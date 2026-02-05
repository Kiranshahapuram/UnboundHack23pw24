"""SQLAlchemy models matching the schema."""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DECIMAL, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = relationship("WorkflowStep", back_populates="workflow", order_by="WorkflowStep.position")
    runs = relationship("WorkflowRun", back_populates="workflow")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    prompt_template = Column(Text, nullable=False)
    model = Column(String(100), default="kimi-k2p5")
    max_tokens = Column(Integer, default=4096)
    temperature = Column(DECIMAL(3, 2), default=0.7)
    retry_limit = Column(Integer, default=3)
    context_mode = Column(String(50), default="summary")
    rule_type = Column(String(50), nullable=False)
    rule_value = Column(Text)
    llm_judge_enabled = Column(Boolean, default=False)
    llm_judge_prompt = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="steps")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending")
    failure_reason = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="runs")
    step_runs = relationship("StepRun", back_populates="workflow_run", order_by="StepRun.position")


class StepRun(Base):
    __tablename__ = "step_runs"

    id = Column(String(36), primary_key=True)
    workflow_run_id = Column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    workflow_step_id = Column(String(36), ForeignKey("workflow_steps.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")
    attempt_number = Column(Integer, default=1)
    input_context = Column(Text)
    output = Column(Text)
    extracted_context = Column(Text)
    evaluation_result = Column(JSON)
    failure_reason = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow_run = relationship("WorkflowRun", back_populates="step_runs")
    llm_logs = relationship("LLMLog", back_populates="step_run")


class LLMLog(Base):
    __tablename__ = "llm_logs"

    id = Column(String(36), primary_key=True)
    step_run_id = Column(String(36), ForeignKey("step_runs.id", ondelete="CASCADE"), nullable=False)
    call_type = Column(String(50), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(DECIMAL(10, 6), default=0)
    model = Column(String(100))
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    step_run = relationship("StepRun", back_populates="llm_logs")
