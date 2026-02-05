import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';

export default function ExecutionHistory() {
  const { workflowId } = useParams();
  const [runs, setRuns] = useState([]);
  const [workflow, setWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!workflowId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      api.workflows.get(workflowId),
      api.workflows.runs(workflowId),
    ])
      .then(([w, r]) => {
        setWorkflow(w);
        setRuns(r);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [workflowId]);

  if (loading) return <div className="container">Loading...</div>;
  if (error) return <div className="container">Error: {error}</div>;

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link to={`/workflows/${workflowId}`}>← Back to {workflow?.name || 'Workflow'}</Link>
      </div>
      <h1>Execution History</h1>
      {runs.length === 0 ? (
        <div className="card">No runs yet. Run the workflow to see history.</div>
      ) : (
        runs.map((run) => (
          <Link key={run.id} to={`/runs/${run.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span className={`badge ${run.status}`}>{run.status}</span>
                <span style={{ marginLeft: '0.75rem' }}>{new Date(run.created_at).toLocaleString()}</span>
              </div>
              <div>
                {run.failure_reason && (
                  <span style={{ fontSize: '0.85rem', color: '#8b949e' }}>{run.failure_reason.slice(0, 80)}...</span>
                )}
                <span style={{ marginLeft: '0.5rem' }}>→</span>
              </div>
            </div>
          </Link>
        ))
      )}
    </div>
  );
}
