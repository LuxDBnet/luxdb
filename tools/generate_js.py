"""Deterministic ESM operation metadata and TypeScript declarations; no dependencies."""
import hashlib
import json
from pathlib import Path

JS_OUTPUT = 'clients/js/generated.js'
TYPES_OUTPUT = 'clients/js/index.d.ts'


def expression(obj):
    if '$ref' in obj:
        return obj['$ref'].split('/')[-1]
    if 'const' in obj:
        return json.dumps(obj['const'], ensure_ascii=False)
    if 'enum' in obj:
        return ' | '.join(json.dumps(v, ensure_ascii=False) for v in obj['enum'])
    for key, joiner in [('oneOf', ' | '), ('anyOf', ' | '), ('allOf', ' & ')]:
        if key in obj:
            return '(' + joiner.join(expression(v) for v in obj[key]) + ')'
    kind = obj.get('type')
    if isinstance(kind, list):
        return '(' + ' | '.join(expression({**obj, 'type': k, 'nullable': False}) for k in kind) + ')'
    if kind == 'object':
        if 'properties' in obj:
            required = set(obj.get('required', []))
            value = '{ ' + '; '.join(json.dumps(k) + ('' if k in required else '?') + ': ' + expression(v)
                                    for k, v in obj['properties'].items()) + ' }'
        else:
            extra = obj.get('additionalProperties')
            value = 'Record<string, ' + (expression(extra) if isinstance(extra, dict) else 'unknown') + '>'
    elif kind == 'array':
        value = 'Array<' + expression(obj.get('items', {})) + '>'
    else:
        value = {'string': 'string', 'integer': 'number', 'number': 'number', 'boolean': 'boolean', 'null': 'null'}.get(kind, 'unknown')
    return '(' + value + ' | null)' if obj.get('nullable') and value != 'null' else value


def outputs(root):
    from generate_clients import METHOD_NAMES, UNSUPPORTED_HEADERS, operation_name, title
    raw = (root / 'openapi/openapi.json').read_bytes()
    from client_compat import client_view
    spec = client_view(json.loads(raw))
    digest = hashlib.sha256(raw).hexdigest()
    operations = {}
    types = ['// Generated from the public contract; do not edit.']
    for name, schema in spec['components']['schemas'].items():
        types.append('export type ' + name + ' = ' + expression(schema) + ';')
    methods = []
    for path, value in spec['paths'].items():
        op = value['get']
        name = operation_name(path, op)
        parameters = []
        for p in op.get('parameters', []):
            if p['in'] == 'header':
                if p['name'] not in UNSUPPORTED_HEADERS.get(path, ()):
                    raise ValueError('new header needs client review')
                continue
            if p['in'] not in {'query', 'path'} or p['schema'].get('type') != 'string':
                raise ValueError('new parameter needs client review')
            parameters.append({k: p[k] for k in ('name', 'in', 'required') if k in p} | {'schema': p['schema']})
        operations[name] = {'path': path, 'authenticated': op.get('security') != [], 'parameters': parameters}
        response = title(name) + 'Response'
        types.append('export type ' + response + ' = ' + expression(op['responses']['200']['content']['application/json']['schema']) + ';')
        option = '{ ' + '; '.join(json.dumps(p['name']) + ('' if p.get('required') else '?') + ': string' for p in parameters) + ' }' if parameters else 'Record<string, never>'
        methods.append('  ' + name + '(params' + ('' if any(p.get('required') for p in parameters) else '?') + ': ' + option + '): Promise<' + response + '>;')
    js = '// Generated from the public contract; do not edit.\n// Public spec SHA256: ' + digest + '\n'
    js += 'export const API_BASE_URL = ' + json.dumps(spec['servers'][0]['url']) + ';\n'
    for name, value in [('ERROR_CODES', spec['components']['schemas']['Error']['properties']['code']['enum']),
                        ('ERROR_MODES', spec['components']['schemas']['Error']['properties'].get('mode', {}).get('enum', [])), ('OPERATIONS', operations)]:
        js += 'export const ' + name + ' = ' + json.dumps(value, ensure_ascii=False, indent=2) + ';\n'
    types += ['export interface ClientOptions { apiKey?: string; allowPaid?: boolean; timeoutMs?: number; fetch?: typeof globalThis.fetch; }',
              'export class Client {', '  constructor(options?: ClientOptions);', *methods, '}',
              'export class ApiError extends globalThis.Error { readonly status: number; readonly code: string; readonly mode: string | null; readonly retryAfterSeconds: number | null; readonly details: Record<string, unknown>; }',
              'export class TransportError extends globalThis.Error {}']
    return {JS_OUTPUT: js, TYPES_OUTPUT: '\n'.join(types) + '\n'}
