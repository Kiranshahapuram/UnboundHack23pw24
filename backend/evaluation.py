"""
Completion criteria evaluation - hybrid rule-based + optional LLM judge.
Evaluation order: Rule checks -> LLM judge (if enabled) -> final decision.
"""

import re
import json
from typing import Optional, Tuple, Dict, Any
from llm_client import call_llm


# ---------------- Rule handlers ---------------- #

def _rule_contains(text: str, value: str) -> bool:
    return bool(value and text and value in text)


def _rule_regex(text: str, pattern: str) -> bool:
    if not text or not pattern:
        return False
    try:
        return bool(re.search(pattern, text, re.DOTALL))
    except re.error:
        return False


def _rule_json_valid(text: str, _: Optional[str]) -> bool:
    if not text:
        return False
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def _rule_code_block_present(text: str, _: Optional[str]) -> bool:
    return bool(text and "```" in text)


RULE_HANDLERS = {
    "contains": _rule_contains,
    "regex": _rule_regex,
    "json_valid": _rule_json_valid,
    "code_block_present": _rule_code_block_present,
}


def evaluate_rule(rule_type: str, rule_value: Optional[str], output: str) -> Tuple[bool, str]:
    handler = RULE_HANDLERS.get(rule_type)
    if not handler:
        return False, f"Unknown rule type: {rule_type}"

    passed = handler(output or "", rule_value or "")
    reason = f"Rule '{rule_type}' {'passed' if passed else 'failed'}"
    return passed, reason


# ---------------- LLM Judge ---------------- #

async def evaluate_llm_judge(
    output: str,
    judge_prompt: Optional[str],
    model: str = "kimi-k2p5",
) -> Tuple[bool, str]:

    default_prompt = (
        "Evaluate if the following output meets the expected quality and completeness. "
        "Respond ONLY in JSON: {\"pass\": true/false, \"reason\": \"...\"}"
    )

    prompt = judge_prompt or default_prompt
    full_prompt = f"{prompt}\n\n---\nOutput:\n{output}"

    messages = [{"role": "user", "content": full_prompt}]

    content, *_ = await call_llm(messages, model=model, max_tokens=512)

    try:
        data = json.loads(content)
        return bool(data.get("pass", False)), data.get("reason", "No reason provided")
    except Exception:
        passed = "true" in content.lower()
        return passed, content.strip()


# ---------------- Main evaluator ---------------- #

async def evaluate_completion(
    output: str,
    rule_type: str,
    rule_value: Optional[str],
    llm_judge_enabled: bool = False,
    llm_judge_prompt: Optional[str] = None,
    model: str = "kimi-k2p5",
) -> Tuple[bool, Dict[str, Any]]:

    try:
        if not output or not output.strip():
            return False, {
                "passed": False,
                "reason": "LLM output was empty",
                "details": {},
                "error": None,
            }

        details = {
            "rule_passed": None,
            "rule_reason": None,
            "llm_judge_passed": None,
            "llm_judge_reason": None,
        }

        # ---- Rule evaluation ----
        rule_passed, rule_reason = evaluate_rule(rule_type, rule_value, output)
        details["rule_passed"] = rule_passed
        details["rule_reason"] = rule_reason

        if not rule_passed:
            return False, {
                "passed": False,
                "reason": rule_reason,
                "details": details,
                "error": None,  # ✅ FIX
            }

        # ---- Optional LLM judge ----
        if llm_judge_enabled:
            llm_passed, llm_reason = await evaluate_llm_judge(
                output, llm_judge_prompt, model
            )
            details["llm_judge_passed"] = llm_passed
            details["llm_judge_reason"] = llm_reason

            if not llm_passed:
                return False, {
                    "passed": False,
                    "reason": llm_reason,
                    "details": details,
                    "error": None,  
                }

        # ---- Success ----
        return True, {
            "passed": True,
            "details": details,
            "error": None,  # ✅ FIX
        }

    except Exception as e:
        # HARD failure: evaluator bug or infra issue
        return False, {
            "error": repr(e),
        }
