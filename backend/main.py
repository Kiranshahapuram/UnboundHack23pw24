"""
FastAPI application - Agentic Workflow Builder.
APIs: Workflow CRUD, Step config, Run workflow, Poll status, Execution logs.
"""
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base, Workflow, WorkflowStep, WorkflowRun, StepRun, LLMLog
from schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowDetailResponse,
    StepCreate,
    StepUpdate,
    StepResponse,
    WorkflowRunResponse,
    WorkflowRunDetailResponse,
    StepRunResponse,
    LLMLogResponse,
)
from executor import run_workflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    # shutdown


app = FastAPI(title="Agentic Workflow Builder", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message ":"Connection Successful"}

# --- Workflow CRUD ---
@app.get("/workflows", response_model=list[WorkflowResponse])
def list_workflows(db: Session = Depends(get_db)):
    return db.query(Workflow).order_by(Workflow.created_at.desc()).all()


@app.post("/workflows", response_model=WorkflowResponse)
def create_workflow(data: WorkflowCreate, db: Session = Depends(get_db)):
    w = Workflow(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


@app.get("/workflows/{workflow_id}", response_model=WorkflowDetailResponse)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    w = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(404, "Workflow not found")
    return w


@app.patch("/workflows/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: str, data: WorkflowUpdate, db: Session = Depends(get_db)):
    w = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(404, "Workflow not found")
    if data.name is not None:
        w.name = data.name
    if data.description is not None:
        w.description = data.description
    db.commit()
    db.refresh(w)
    return w


@app.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    w = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(404, "Workflow not found")
    db.delete(w)
    db.commit()
    return {"ok": True}


# --- Step CRUD ---
@app.post("/workflows/{workflow_id}/steps", response_model=StepResponse)
def create_step(workflow_id: str, data: StepCreate, db: Session = Depends(get_db)):
    w = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(404, "Workflow not found")
    s = WorkflowStep(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        position=data.position,
        name=data.name,
        prompt_template=data.prompt_template,
        model=data.model,
        max_tokens=data.max_tokens,
        temperature=data.temperature,
        retry_limit=data.retry_limit,
        context_mode=data.context_mode,
        rule_type=data.rule_type,
        rule_value=data.rule_value,
        llm_judge_enabled=data.llm_judge_enabled,
        llm_judge_prompt=data.llm_judge_prompt,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@app.patch("/workflows/{workflow_id}/steps/{step_id}", response_model=StepResponse)
def update_step(
    workflow_id: str, step_id: str, data: StepUpdate, db: Session = Depends(get_db)
):
    s = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.id == step_id, WorkflowStep.workflow_id == workflow_id)
        .first()
    )
    if not s:
        raise HTTPException(404, "Step not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


@app.delete("/workflows/{workflow_id}/steps/{step_id}")
def delete_step(workflow_id: str, step_id: str, db: Session = Depends(get_db)):
    s = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.id == step_id, WorkflowStep.workflow_id == workflow_id)
        .first()
    )
    if not s:
        raise HTTPException(404, "Step not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


# --- Run workflow ---
@app.post("/workflows/{workflow_id}/run", response_model=WorkflowRunResponse)
def trigger_run(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    w = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(404, "Workflow not found")
    if not w.steps:
        raise HTTPException(400, "Workflow has no steps")

    run = WorkflowRun(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    async def _run():
        from database import SessionLocal
        session = SessionLocal()
        try:
            await run_workflow(session, run.id)
        finally:
            session.close()

    background_tasks.add_task(_run)
    return run


# --- Poll workflow status ---
@app.get("/runs/{run_id}", response_model=WorkflowRunDetailResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@app.get("/workflows/{workflow_id}/runs", response_model=list[WorkflowRunResponse])
def list_runs(workflow_id: str, db: Session = Depends(get_db)):
    return (
        db.query(WorkflowRun)
        .filter(WorkflowRun.workflow_id == workflow_id)
        .order_by(WorkflowRun.created_at.desc())
        .all()
    )


# --- Execution logs ---
@app.get("/runs/{run_id}/logs", response_model=list[LLMLogResponse])
def get_run_logs(run_id: str, db: Session = Depends(get_db)):
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")
    step_run_ids = [sr.id for sr in run.step_runs]
    logs = db.query(LLMLog).filter(LLMLog.step_run_id.in_(step_run_ids)).order_by(LLMLog.created_at).all()
    return logs


@app.get("/runs/{run_id}/steps/{step_run_id}/logs", response_model=list[LLMLogResponse])
def get_step_run_logs(run_id: str, step_run_id: str, db: Session = Depends(get_db)):
    step_run = (
        db.query(StepRun)
        .filter(StepRun.id == step_run_id, StepRun.workflow_run_id == run_id)
        .first()
    )
    if not step_run:
        raise HTTPException(404, "Step run not found")
    return db.query(LLMLog).filter(LLMLog.step_run_id == step_run_id).order_by(LLMLog.created_at).all()
