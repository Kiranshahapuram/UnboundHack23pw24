# Agentic Workflow Builder

Multi-step AI workflow execution engine for the Unbound Hackathon. Chains LLM tasks with completion criteria, retries, and context passing.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: MySQL
- **Frontend**: React (Vite)
- **LLM**: Unbound API (OpenAI-compatible)

## Setup

### 1. Database

Create MySQL database and run schema:

```bash
mysql -u root -p < database/schema.sql
```

Or create the database manually and let the app create tables via SQLAlchemy `create_all`.

### 2. Backend

**Requires Python 3.11 or 3.12** (Python 3.14 lacks pre-built wheels for pydantic).

```bash
cd backend
cp .env.example .env
# Edit .env: DATABASE_URL, UNBOUND_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend proxies `/api` to `http://localhost:8000`.

## Features

- **Workflow CRUD**: Create, edit, delete workflows
- **Step configuration**: Prompts, models, completion rules (contains, regex, json_valid, code_block_present)
- **Context passing**: full, code_only, json_only, summary
- **Retry logic**: Per-step retry limit with feedback injection
- **Optional LLM judge**: Rule checks first, then LLM judge if enabled
- **Execution**: Background run, poll for status, view logs

## API

- `GET/POST /workflows` - List, create
- `GET/PATCH/DELETE /workflows/{id}` - Get, update, delete
- `POST/GET/PATCH/DELETE /workflows/{id}/steps` - Step CRUD
- `POST /workflows/{id}/run` - Start run (returns run_id)
- `GET /runs/{id}` - Poll run status
- `GET /runs/{id}/logs` - LLM call logs
