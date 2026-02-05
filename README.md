#Agentic Workflow Builder

An Agentic Workflow Builder that allows users to create, run, and monitor multi-step AI workflows.
Each step is an LLM task with configurable prompts, models, completion criteria, retries, and explicit context passing.

Built for the Unbound Hackathon with a focus on robust execution, clear observability, and real-world agent design.

##Key Features
- Multi-step AI workflows with sequential execution
- Per-step configuration:
  - Model selection
  - Prompt templates
  - Completion criteria (rule-based + optional AI judge)
  - Retry limits
  - Context passing modes
- Automatic context handoff between steps using {{context}}
- Retry with feedback injection on failure
- Graceful failure when retry budget is exhausted
- Full execution history and logs

##Bonus Challenges Implemented
- Retry budget per step
- Token usage and cost tracking per LLM call
- Live workflow and step execution tracking
- Clear separation of agent failures vs infrastructure failures

##Tech Stack

Backend
- FastAPI
- SQLAlchemy
- MySQL / PostgreSQL
- Unbound API

Frontend
- React (Vite)

##Setup & Run

Backend
cd backend
python -m venv venv
source venv/bin/activate   (Windows: venv\Scripts\activate)
pip install -r requirements.txt
uvicorn main:app --reload

Create a .env file:
UNBOUND_API_KEY=your_key
UNBOUND_BASE_URL=https://api.getunbound.ai/v1
DATABASE_URL=your_db_url

Backend runs at http://localhost:8000

Frontend
cd frontend
npm install
npm run dev

Frontend runs at http://localhost:5173

##API Overview
- Create workflow: POST /workflows
- Add steps: POST /workflows/{workflow_id}/steps
- Run workflow: POST /workflows/{workflow_id}/run
- Check run status: GET /runs/{run_id}
- View logs: GET /runs/{run_id}/logs

##Demo Walkthrough
1. Create a workflow
2. Add multiple AI steps
3. Run the workflow
4. Observe execution, retries, context passing, and cost tracking
5. Inspect execution logs

##Design Notes
- Validation is AI-based but lightweight and stable
- Context passing is explicit, not implicit
- Retries are semantic, not infrastructure-level
- Infrastructure failures fail fast with clear error reporting

Author
S Raghothama Kiran
GitHub: https://github.com/Kiranshahapuram
