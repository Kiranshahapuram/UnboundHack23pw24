import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';

const POLL_INTERVAL = 2000;

export default function RunStatus() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!runId) return;
    let cancelled = false;
    const fetchRun = () => {
      api.runs.get(runId)
        .then((r) => {
          if (!cancelled) setRun(r);
          return r;
        })
        .catch((e) => { if (!cancelled) setError(e.message); });
    };
    fetchRun();
    const id = setInterval(fetchRun, POLL_INTERVAL);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [runId]);

  useEffect(() => {
    if (!runId || !run) return;
    api.runs.logs(runId)
      .then(setLogs)
      .catch(() => setLogs([]));
  }, [runId, run?.status]);

  useEffect(() => {
    setLoading(false);
  }, [run]);

  if (error) return <div className="container">Error: {error}</div>;
  if (!runId) return <div className="container">Invalid run ID</div>;
  if (loading && !run) return <div className="container">Loading...</div>;
  if (!run) return <div className="container">Run not found</div>;

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link to={`/workflows/${run.workflow_id}`}>← Back to Workflow</Link>
      </div>
      <h1>Run Status</h1>
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <span>
            Status: <span className={`badge ${run.status}`}>{run.status}</span>
          </span>
          {run.started_at && <span>Started: {new Date(run.started_at).toLocaleString()}</span>}
          {run.completed_at && <span>Completed: {new Date(run.completed_at).toLocaleString()}</span>}
        </div>
        {run.failure_reason && (
          <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#21262d', borderRadius: 6, color: '#f85149' }}>
            {run.failure_reason}
          </div>
        )}
      </div>

      <h2>Step Runs</h2>
      {run.step_runs?.map((sr, i) => (
        <div key={sr.id} className="card" style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span>Step {i + 1} — Attempt {sr.attempt_number}</span>
            <span className={`badge ${sr.status}`}>{sr.status}</span>
          </div>
          {sr.failure_reason && (
            <div style={{ fontSize: '0.85rem', color: '#f85149', marginBottom: '0.5rem' }}>{sr.failure_reason}</div>
          )}
          {sr.output && (
            <details style={{ marginTop: '0.5rem' }}>
              <summary>Output</summary>
              <pre style={{ background: '#0d1117', padding: '0.75rem', borderRadius: 6, overflow: 'auto', maxHeight: 200, fontSize: '0.8rem' }}>
                {sr.output}
              </pre>
            </details>
          )}
        </div>
      ))}

      <h2>LLM Logs</h2>
      {logs.length === 0 ? (
        <div className="card">No logs yet.</div>
      ) : (
        logs.map((log) => (
          <div key={log.id} className="card" style={{ marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
              <span className={`badge ${log.call_type}`}>{log.call_type}</span>
              <span>Tokens: {log.total_tokens} | Cost: ${log.cost_usd?.toFixed(6)}</span>
              {log.latency_ms && <span>Latency: {log.latency_ms}ms</span>}
            </div>
            <details>
              <summary>Prompt / Response</summary>
              <pre style={{ background: '#0d1117', padding: '0.5rem', borderRadius: 4, overflow: 'auto', maxHeight: 150, fontSize: '0.75rem' }}>
                {log.prompt?.slice(0, 500)}... / {log.response?.slice(0, 500)}...
              </pre>
            </details>
          </div>
        ))
      )}
    </div>
  );
}
