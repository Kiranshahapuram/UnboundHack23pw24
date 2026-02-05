"""
Workflow execution engine - core logic.
Sequential step execution, retry with feedback injection, completion evaluation, context passing.
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from models import Workflow, WorkflowStep, WorkflowRun, StepRun, LLMLog
from llm_client import call_llm
from evaluation import evaluate_completion
from context_extractor import extract_context_async


RETRY_FEEDBACK_TEMPLATE = """
---
Previous attempt failed. Feedback:
{feedback}

Please address the above and try again. Your revised response:
"""


def _build_messages(prompt_template: str, context: str | None, retry_feedback: str | None) -> list[dict]:
    """
    Build messages for LLM call.
    Inject context directly into prompt (Option A).
    """

    prompt = prompt_template.replace("{{context}}", context or "")

    if "{{context}}" in prompt:
        raise RuntimeError("Context placeholder '{{context}}' was not replaced")

    system_content = ""
    if retry_feedback:
        system_content = RETRY_FEEDBACK_TEMPLATE.format(feedback=retry_feedback)

    messages = []
    if system_content:
        messages.append({"role": "system", "content": system_content})

    messages.append({"role": "user", "content": prompt})
    return messages


async def _execute_single_step(
    db: Session,
    step: WorkflowStep,
    step_run: StepRun,
    input_context: str | None,
    retry_feedback: str | None,
) -> tuple[str, str, bool, dict]:
    """
    Execute one step attempt.
    Returns (output, extracted_context, passed, eval_result).
    """

    messages = _build_messages(
        step.prompt_template,
        input_context,
        retry_feedback,
    )

    content, in_tok, out_tok, cost, latency = await call_llm(
        messages=messages,
        model=step.model,
        max_tokens=step.max_tokens,
        temperature=float(step.temperature),
    )

    llm_log = LLMLog(
        id=str(uuid.uuid4()),
        step_run_id=step_run.id,
        call_type="retry" if retry_feedback else "main",
        attempt_number=step_run.attempt_number,
        prompt=str(messages),
        response=content,
        input_tokens=in_tok,
        output_tokens=out_tok,
        total_tokens=in_tok + out_tok,
        cost_usd=cost,
        model=step.model,
        latency_ms=latency,
    )
    db.add(llm_log)
    db.commit()

    passed, eval_result = await evaluate_completion(
        output=content,
        rule_type=step.rule_type,
        rule_value=step.rule_value,
        llm_judge_enabled=step.llm_judge_enabled,
        llm_judge_prompt=step.llm_judge_prompt,
        model=step.model,
    )

    extracted = await extract_context_async(
        content,
        step.context_mode,
        step.model,
    )
    
    if step.context_mode != "full" and not extracted.strip():
        extracted = content.strip()

    if not extracted.strip():
        raise RuntimeError(
            f"Context extraction failed for step '{step.name}' "
            f"(mode={step.context_mode})"
        )

    return content, extracted, passed, eval_result


async def run_workflow(db: Session, workflow_run_id: str) -> None:
    """
    Main execution loop. Runs workflow asynchronously, updates DB.
    """

    run = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_run_id).first()
    if not run or run.status != "pending":
        return

    run.status = "running"
    run.started_at = datetime.utcnow()
    db.commit()

    workflow = db.query(Workflow).filter(Workflow.id == run.workflow_id).first()
    steps = sorted(workflow.steps, key=lambda s: s.position)

    accumulated_context: str | None = None

    try:
        for step in steps:
            step_run = StepRun(
                id=str(uuid.uuid4()),
                workflow_run_id=run.id,
                workflow_step_id=step.id,
                position=step.position,
                status="running",
                input_context=accumulated_context,
                started_at=datetime.utcnow(),
            )
            db.add(step_run)
            db.commit()

            retry_count = 0
            passed = False
            failure_reason = ""

            while retry_count <= step.retry_limit:
                step_run.attempt_number = retry_count + 1

                retry_feedback = (
                    f"Attempt {retry_count} failed. Reason: {failure_reason}"
                    if retry_count > 0
                    else None
                )

                try:
                    output, extracted, passed, eval_result = await _execute_single_step(
                        db=db,
                        step=step,
                        step_run=step_run,
                        input_context=accumulated_context,
                        retry_feedback=retry_feedback,
                    )
                except Exception as e:
                    passed = False
                    eval_result = {"error": str(e)}
                    failure_reason = str(e)

                if passed:
                    step_run.status = "completed"
                    step_run.output = output
                    step_run.extracted_context = extracted
                    step_run.evaluation_result = eval_result
                    step_run.completed_at = datetime.utcnow()
                    db.commit()

                    accumulated_context = extracted
                    break

                step_run.evaluation_result = eval_result
                failure_reason = eval_result.get("reason") or str(eval_result)
                retry_count += 1

            if not passed:
                step_run.status = "failed"
                step_run.failure_reason = failure_reason
                step_run.completed_at = datetime.utcnow()
                db.commit()

                run.status = "failed"
                run.failure_reason = (
                    f"Step '{step.name}' failed after {step.retry_limit} retries: "
                    f"{failure_reason}"
                )
                run.completed_at = datetime.utcnow()
                db.commit()
                return

        run.status = "completed"
        run.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        run.status = "failed"
        run.failure_reason = str(e)
        run.completed_at = datetime.utcnow()
        db.commit()
        raise
