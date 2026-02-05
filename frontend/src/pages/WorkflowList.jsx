import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

export default function WorkflowList() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.workflows
      .list()
      .then(setWorkflows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id, ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    if (!confirm('Delete this workflow?')) return;
    try {
      await api.workflows.delete(id);
      setWorkflows((w) => w.filter((x) => x.id !== id));
    } catch (e) {
      alert(e.message);
    }
  };

  if (loading) return <div className="container">Loading...</div>;
  if (error) return <div className="container"><p>Error: {error}</p><p style={{ fontSize: '0.9rem', color: '#8b949e' }}>Ensure the backend is running on port 8000.</p></div>;

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1>Workflows</h1>
        <Link to="/workflows/new">
          <button className="primary">+ New Workflow</button>
        </Link>
      </div>
      {workflows.length === 0 ? (
        <div className="card">
          <p>No workflows yet. Create one to get started.</p>
          <Link to="/workflows/new">
            <button className="primary" style={{ marginTop: '0.5rem' }}>Create Workflow</button>
          </Link>
        </div>
      ) : (
        workflows.map((w) => (
          <Link key={w.id} to={`/workflows/${w.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: '0 0 0.25rem 0' }}>{w.name}</h3>
                {w.description && <p style={{ margin: 0, fontSize: '0.9rem', color: '#8b949e' }}>{w.description}</p>}
              </div>
              <div>
                <Link to={`/workflows/${w.id}`}>
                  <button className="secondary" onClick={(e) => e.preventDefault()}>Edit</button>
                </Link>
                <button className="danger" style={{ marginLeft: '0.5rem' }} onClick={(ev) => handleDelete(w.id, ev)}>
                  Delete
                </button>
              </div>
            </div>
          </Link>
        ))
      )}
    </div>
  );
}
