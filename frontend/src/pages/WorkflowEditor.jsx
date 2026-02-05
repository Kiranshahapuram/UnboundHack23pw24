import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { api } from '../api';

const RULE_TYPES = ['contains', 'regex', 'json_valid', 'code_block_present'];
const CONTEXT_MODES = ['full', 'code_only', 'json_only', 'summary'];
const AVAILABLE_MODELS = ['kimi-k2p5', 'kimi-k2-instruct-0905'];

export default function WorkflowEditor() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const isNew = id === 'new' || location.pathname === '/workflows/new';
  const [workflow, setWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isNew) {
      setWorkflow({ name: '', description: '', steps: [] });
      setLoading(false);
      setError(null);
      return;
    }
    if (!id) return;
    setLoading(true);
    setError(null);
    api.workflows.get(id)
      .then(setWorkflow)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const workflowId = id || workflow?.id;

  const saveWorkflow = async () => {
    if (!workflow) return;
    setSaving(true);
    try {
      if (isNew) {
        const created = await api.workflows.create({ name: workflow.name, description: workflow.description });
        setWorkflow((w) => ({ ...w, id: created.id, ...created }));
        navigate(`/workflows/${created.id}`);
      } else {
        await api.workflows.update(id, { name: workflow.name, description: workflow.description });
      }
    } catch (e) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  const addStep = async () => {
    if (!workflowId) return;
    const pos = (workflow.steps?.length || 0) + 1;
    const step = {
      position: pos,
      name: `Step ${pos}`,
      prompt_template: 'Your task: ...',
      model: 'kimi-k2p5',
      max_tokens: 4096,
      temperature: 0.7,
      retry_limit: 3,
      context_mode: 'summary',
      rule_type: 'code_block_present',
      rule_value: '',
      llm_judge_enabled: false,
      llm_judge_prompt: '',
    };
    try {
      const created = await api.steps.create(workflowId, step);
      setWorkflow((w) => ({ ...w, steps: [...(w.steps || []), created] }));
    } catch (e) {
      alert(e.message);
    }
  };

  const updateStep = async (stepId, data) => {
    if (!workflowId) return;
    try {
      const updated = await api.steps.update(workflowId, stepId, data);
      setWorkflow((w) => ({
        ...w,
        steps: w.steps.map((s) => (s.id === stepId ? updated : s)),
      }));
    } catch (e) {
      alert(e.message);
    }
  };

  const deleteStep = async (stepId) => {
    if (!workflowId || !confirm('Delete this step?')) return;
    try {
      await api.steps.delete(workflowId, stepId);
      setWorkflow((w) => ({ ...w, steps: w.steps.filter((s) => s.id !== stepId) }));
    } catch (e) {
      alert(e.message);
    }
  };

  const runWorkflow = async () => {
    if (!workflowId || !workflow.steps?.length) {
      alert('Add at least one step before running.');
      return;
    }
    try {
      const run = await api.workflows.run(workflowId);
      navigate(`/runs/${run.id}`);
    } catch (e) {
      alert(e.message);
    }
  };

  if (error) return <div className="container">Error: {error}</div>;
  if (loading || !workflow) return <div className="container">Loading...</div>;

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1>{isNew ? 'New Workflow' : workflow.name}</h1>
        <div>
          <button className="secondary" onClick={saveWorkflow} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </button>
          {!isNew && (
          <>
            <Link to={`/workflows/${workflowId}/history`}>
              <button className="secondary" style={{ marginLeft: '0.5rem' }}>History</button>
            </Link>
            <button className="primary" style={{ marginLeft: '0.5rem' }} onClick={runWorkflow}>
              Run Workflow
            </button>
          </>
        )}
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem' }}>Name</label>
        <input
          value={workflow.name}
          onChange={(e) => setWorkflow((w) => ({ ...w, name: e.target.value }))}
          style={{ width: '100%', maxWidth: '400px' }}
          placeholder="Workflow name"
        />
        <label style={{ display: 'block', marginTop: '1rem', marginBottom: '0.5rem' }}>Description</label>
        <textarea
          value={workflow.description || ''}
          onChange={(e) => setWorkflow((w) => ({ ...w, description: e.target.value }))}
          style={{ width: '100%', maxWidth: '600px' }}
          placeholder="Optional description"
        />
      </div>

      <h2>Steps</h2>
      {workflow.steps?.map((step, i) => (
        <div key={step.id} className="card" style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <h3 style={{ margin: 0 }}>Step {i + 1}: {step.name}</h3>
            <button className="danger" onClick={() => deleteStep(step.id)}>Delete</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label>Name</label>
              <input
                value={step.name}
                onChange={(e) => updateStep(step.id, { name: e.target.value })}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label>Model</label>
              <select
                value={AVAILABLE_MODELS.includes(step.model) ? step.model : AVAILABLE_MODELS[0]}
                onChange={(e) => updateStep(step.id, { model: e.target.value })}
                style={{ width: '100%' }}
              >
                {AVAILABLE_MODELS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ marginTop: '1rem' }}>
            <label>Prompt Template</label>
            <textarea
              value={step.prompt_template}
              onChange={(e) => updateStep(step.id, { prompt_template: e.target.value })}
              style={{ width: '100%', minHeight: '120px' }}
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
            <div>
              <label>Rule Type</label>
              <select
                value={step.rule_type}
                onChange={(e) => updateStep(step.id, { rule_type: e.target.value })}
                style={{ width: '100%' }}
              >
                {RULE_TYPES.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
            <div>
              <label>Rule Value (for contains/regex)</label>
              <input
                value={step.rule_value || ''}
                onChange={(e) => updateStep(step.id, { rule_value: e.target.value })}
                style={{ width: '100%' }}
                placeholder="e.g. ``` or pattern"
              />
            </div>
            <div>
              <label>Context Mode</label>
              <select
                value={step.context_mode}
                onChange={(e) => updateStep(step.id, { context_mode: e.target.value })}
                style={{ width: '100%' }}
              >
                {CONTEXT_MODES.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <label>
              <input
                type="checkbox"
                checked={step.llm_judge_enabled}
                onChange={(e) => updateStep(step.id, { llm_judge_enabled: e.target.checked })}
              />
              {' '}LLM Judge
            </label>
            <span>Retry limit: </span>
            <input
              type="number"
              value={step.retry_limit}
              onChange={(e) => updateStep(step.id, { retry_limit: parseInt(e.target.value) || 3 })}
              style={{ width: '60px' }}
            />
          </div>
        </div>
      ))}

      <button className="primary" onClick={addStep} disabled={!workflowId}>
        + Add Step
      </button>
      {isNew && !workflowId && <span style={{ marginLeft: '0.5rem', color: '#8b949e' }}>Save workflow first to add steps</span>}
    </div>
  );
}
