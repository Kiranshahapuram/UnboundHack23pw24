"""Pydantic schemas for API."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# Workflow
class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class WorkflowResponse(WorkflowBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Step
class StepBase(BaseModel):
    name: str
    prompt_template: str
    model: str = "kimi-k2p5"
    max_tokens: int = 4096
    temperature: float = 0.7
    retry_limit: int = 3
    context_mode: str = "summary"
    rule_type: str
    rule_value: Optional[str] = None
    llm_judge_enabled: bool = False
    llm_judge_prompt: Optional[str] = None


class StepCreate(StepBase):
    position: int


class StepUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None
    prompt_template: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    retry_limit: Optional[int] = None
    context_mode: Optional[str] = None
    rule_type: Optional[str] = None
    rule_value: Optional[str] = None
    llm_judge_enabled: Optional[bool] = None
    llm_judge_prompt: Optional[str] = None


class StepResponse(StepBase):
    id: str
    workflow_id: str
    position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Workflow Run
class WorkflowRunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    failure_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Step Run
class StepRunResponse(BaseModel):
    id: str
    workflow_run_id: str
    workflow_step_id: str
    position: int
    status: str
    attempt_number: int
    output: Optional[str] = None
    extracted_context: Optional[str] = None
    evaluation_result: Optional[dict] = None
    failure_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# LLM Log
class LLMLogResponse(BaseModel):
    id: str
    step_run_id: str
    call_type: str
    attempt_number: int
    prompt: str
    response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Workflow with steps
class WorkflowDetailResponse(WorkflowResponse):
    steps: list[StepResponse] = []


# Run with step runs
class WorkflowRunDetailResponse(WorkflowRunResponse):
    step_runs: list[StepRunResponse] = []
