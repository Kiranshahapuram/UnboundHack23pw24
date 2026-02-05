-- Agentic Workflow Builder - MySQL Schema
-- Separates definitions (workflows, steps) from execution (runs, step_runs, llm_logs)

CREATE DATABASE IF NOT EXISTS workflow_builder CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE workflow_builder;

-- Workflow definitions (what the user creates)
CREATE TABLE workflows (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_workflows_created (created_at)
);

-- Steps within a workflow (ordered by position)
CREATE TABLE workflow_steps (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    position INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    prompt_template TEXT NOT NULL,
    model VARCHAR(100) DEFAULT 'gpt-4o-mini',
    max_tokens INT DEFAULT 4096,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    retry_limit INT DEFAULT 3,
    context_mode ENUM('full', 'code_only', 'json_only', 'summary') DEFAULT 'summary',
    -- Completion criteria: rule-based (required)
    rule_type ENUM('contains', 'regex', 'json_valid', 'code_block_present') NOT NULL,
    rule_value TEXT,
    -- Optional LLM judge
    llm_judge_enabled BOOLEAN DEFAULT FALSE,
    llm_judge_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE KEY uk_workflow_position (workflow_id, position),
    INDEX idx_steps_workflow (workflow_id)
);

-- Workflow execution instances
CREATE TABLE workflow_runs (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    failure_reason TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    INDEX idx_runs_workflow (workflow_id),
    INDEX idx_runs_status (status),
    INDEX idx_runs_created (created_at)
);

-- Step execution attempts (one per step per run)
CREATE TABLE step_runs (
    id VARCHAR(36) PRIMARY KEY,
    workflow_run_id VARCHAR(36) NOT NULL,
    workflow_step_id VARCHAR(36) NOT NULL,
    position INT NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    attempt_number INT DEFAULT 1,
    input_context TEXT,
    output TEXT,
    extracted_context TEXT,
    evaluation_result JSON,
    failure_reason TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(id) ON DELETE CASCADE,
    INDEX idx_step_runs_run (workflow_run_id),
    INDEX idx_step_runs_step (workflow_step_id)
);

-- LLM call logs (prompt, response, tokens, cost per call)
CREATE TABLE llm_logs (
    id VARCHAR(36) PRIMARY KEY,
    step_run_id VARCHAR(36) NOT NULL,
    call_type ENUM('main', 'retry', 'llm_judge') NOT NULL,
    attempt_number INT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    model VARCHAR(100),
    latency_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (step_run_id) REFERENCES step_runs(id) ON DELETE CASCADE,
    INDEX idx_llm_logs_step_run (step_run_id),
    INDEX idx_llm_logs_created (created_at)
);
