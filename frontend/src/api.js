const BASE = '/api';
const TIMEOUT_MS = 15000;

async function req(method, path, body) {
  const opts = { method, headers: {} };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  opts.signal = controller.signal;
  try {
    const r = await fetch(`${BASE}${path}`, opts);
    clearTimeout(timeout);
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      const msg = Array.isArray(err.detail) ? err.detail.map((e) => e.msg || e).join(', ') : (err.detail || JSON.stringify(err));
      throw new Error(msg);
    }
    return r.json();
  } catch (e) {
    clearTimeout(timeout);
    if (e.name === 'AbortError') throw new Error('Request timed out. Is the backend running?');
    throw e;
  }
}

export const api = {
  workflows: {
    list: () => req('GET', '/workflows'),
    get: (id) => req('GET', `/workflows/${id}`),
    create: (data) => req('POST', '/workflows', data),
    update: (id, data) => req('PATCH', `/workflows/${id}`, data),
    delete: (id) => req('DELETE', `/workflows/${id}`),
    run: (id) => req('POST', `/workflows/${id}/run`),
    runs: (id) => req('GET', `/workflows/${id}/runs`),
  },
  steps: {
    create: (workflowId, data) => req('POST', `/workflows/${workflowId}/steps`, data),
    update: (workflowId, stepId, data) => req('PATCH', `/workflows/${workflowId}/steps/${stepId}`, data),
    delete: (workflowId, stepId) => req('DELETE', `/workflows/${workflowId}/steps/${stepId}`),
  },
  runs: {
    get: (id) => req('GET', `/runs/${id}`),
    logs: (id) => req('GET', `/runs/${id}/logs`),
  },
};
