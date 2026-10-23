/** LuxDB: one fetch per call, explicit paid opt-in, no retries or redirects. */
import {API_BASE_URL, ERROR_CODES, ERROR_MODES, OPERATIONS} from './generated.js';
const MAX_BYTES = 8 * 1024 * 1024;
const KEYS = new WeakMap();
export class TransportError extends Error {
  constructor(message = 'HTTP transport failed') { super(message); this.name = 'TransportError'; }
}
export class ApiError extends Error {
  constructor(status, code, retryAfterSeconds, mode, details = {}) {
    const safe = ERROR_CODES.includes(code) ? code : 'http_error';
    super('HTTP ' + status + ': ' + safe);
    Object.defineProperty(this, 'details', {value: details, enumerable: false});
    this.name = 'ApiError'; this.status = status; this.code = safe;
    this.retryAfterSeconds = retryAfterSeconds;
    this.mode = ERROR_MODES.includes(mode) ? mode : null;
  }
}
function seconds(value) {
  if (typeof value === 'number' && Number.isSafeInteger(value) && value >= 0) return value;
  return typeof value === 'string' && /^[0-9]{1,9}$/.test(value) ? Number(value) : null;
}
async function payload(response) {
  if (!response.body || typeof response.body.getReader !== 'function') throw new TransportError('Invalid service response');
  const reader = response.body.getReader();
  const chunks = []; let size = 0;
  try {
    for (;;) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.byteLength;
      if (size > MAX_BYTES) { await reader.cancel(); throw new TransportError('Response exceeds the client byte limit'); }
      chunks.push(part.value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  try { return JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes)); } catch { return null; }
}
export class Client {
  constructor({apiKey = 'demo', allowPaid = false, timeoutMs = 20000, fetch: transport = globalThis.fetch} = {}) {
    if (typeof apiKey !== 'string' || !/^[\x21-\x7e]+$/.test(apiKey)) throw new TypeError('Invalid API key');
    if (apiKey !== 'demo' && allowPaid !== true) throw new TypeError('A paid key requires allowPaid: true');
    if (typeof timeoutMs !== 'number' || !Number.isFinite(timeoutMs) || timeoutMs <= 0 || timeoutMs > 2147483647) throw new TypeError('Invalid timeoutMs');
    if (typeof transport !== 'function') throw new TypeError('A fetch implementation is required');
    KEYS.set(this, {key: apiKey, timeoutMs, transport});
  }
  async _call(name, params = {}) {
    const op = OPERATIONS[name];
    if (!op || !params || typeof params !== 'object' || Array.isArray(params)) throw new TypeError('Invalid parameters');
    const known = new Set(op.parameters.map(p => p.name));
    for (const key of Object.keys(params)) if (!known.has(key)) throw new TypeError('Unknown parameter');
    let path = op.path; const query = new URLSearchParams();
    for (const p of op.parameters) {
      const value = params[p.name];
      if (value === undefined) { if (p.required) throw new TypeError('Required parameter missing'); continue; }
      if (typeof value !== 'string' || (p.required && !value.trim())) throw new TypeError('Invalid parameter');
      if (p.schema.pattern && !(new RegExp(p.schema.pattern)).test(value)) throw new TypeError('Invalid parameter format');
      if (p.in === 'path') path = path.replace('{' + p.name + '}', encodeURIComponent(value));
      else query.set(p.name, value);
    }
    if (name === 'article' && (params.codes.split(',').length > 20 || params.codes.split(',').some(p => !p.trim()))) throw new TypeError('Expected 1 to 20 codes');
    const {key, timeoutMs, transport} = KEYS.get(this);
    const headers = {Accept: 'application/json'};
    if (op.authenticated) headers['X-API-Key'] = key;
    const url = API_BASE_URL + path + (query.size ? '?' + query.toString() : '');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await transport(url, {method: 'GET', headers, redirect: 'error', credentials: 'omit', cache: 'no-store', signal: controller.signal});
      // Also reject a redirect returned by an injected transport.
      if (response.redirected || (response.status >= 300 && response.status < 400)) throw new TransportError('Redirect refused');
      const body = await payload(response);
      if (response.status < 200 || response.status >= 300) {
        const obj = body && typeof body === 'object' && !Array.isArray(body) ? body : {};
        const wait = seconds(response.headers.get('retry-after')) ?? seconds(obj.retry_after_seconds);
        throw new ApiError(response.status, obj.code, wait, response.status === 503 ? obj.mode : null, obj);
      }
      if (!body || typeof body !== 'object' || Array.isArray(body)) throw new TransportError('Expected a JSON object response');
      return body;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      // Never copy a transport message, cause, key, query or response body.
      throw new TransportError();
    } finally { clearTimeout(timer); }
  }
}
for (const name of Object.keys(OPERATIONS)) {
  Object.defineProperty(Client.prototype, name, {value: function (params) { return this._call(name, params); }});
}
