import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import WorkflowList from './pages/WorkflowList';
import WorkflowEditor from './pages/WorkflowEditor';
import RunStatus from './pages/RunStatus';
import ExecutionHistory from './pages/ExecutionHistory';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Workflows</Link>
        <Link to="/workflows/new">New Workflow</Link>
      </nav>
      <Routes>
        <Route path="/" element={<WorkflowList />} />
        <Route path="/workflows/new" element={<WorkflowEditor key="new" />} />
        <Route path="/workflows/:id" element={<WorkflowEditor />} />
        <Route path="/workflows/:workflowId/history" element={<ExecutionHistory />} />
        <Route path="/runs/:runId" element={<RunStatus />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
