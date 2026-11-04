const API_BASE = import.meta.env.VITE_API_URL ?? '';

class ApiError extends Error {
  constructor(kind, fields = []) {
    super(kind);
    this.kind = kind; // 'rate_limited' | 'invalid' | 'server'
    this.fields = fields;
  }
}

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (response.ok) return response.json();
  if (response.status === 429) throw new ApiError('rate_limited');
  if (response.status === 422) {
    const body = await response.json();
    throw new ApiError('invalid', body.fields);
  }
  throw new ApiError('server');
}

const postJson = (path, body) =>
  request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

export const getOptions = () => request('/api/options');
export const analyzeFarm = (farm) => postJson('/api/analyze', farm);
export const sendChat = (messages, language, farm) =>
  postJson('/api/chat', { messages, language, farm });
