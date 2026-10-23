"""Conservative JavaScript literal inspection, never evaluation of candidate code.

This is not a full JS parser. Executable sources are also pinned by reviewed
content hashes; unreviewed changes are blocked even outside this lexical subset.
"""
import ast
import re
from content_policy import normalise, SECRET_FIELDS, placeholder

TOKENS = re.compile(r'''//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`''')


def inspect_javascript(text):
    categories, strings, literals = set(), [], []
    last, joined = None, ''
    for match in TOKENS.finditer(text):
        literal = match[0]
        if literal.startswith(('//', '/*')):
            continue
        if literal.startswith('`'):
            if '${' in literal:
                categories.add('javascript-dynamic-template')
            literal = repr(literal[1:-1])
        try:
            decoded = ast.literal_eval(literal)
        except (ValueError, SyntaxError):
            categories.add('javascript-unanalysable-literal')
            continue
        if not isinstance(decoded, str):
            continue
        decoded = re.sub(r'\\u\{([0-9a-fA-F]{1,6})\}', lambda m: chr(int(m[1], 16)) if int(m[1],16) <= 1114111 else '?', decoded)
        strings.append(decoded)
        if last is not None and text[last:match.start()].strip() == '+':
            joined += decoded
            strings.append(joined)
        else:
            joined = decoded
        last = match.end()
        literals.append((match.start(), match.end(), decoded))
    # Credential names with a literal assignment, including quoted object keys.
    for start, end, decoded in literals:
        prefix = text[max(0, start-100):start]
        key = re.search(r'''(?:["']?)([A-Za-z_-]+)(?:["']?)\s*[:=]\s*$''', prefix)
        if key and normalise(key[1]).lower() in SECRET_FIELDS and not placeholder(decoded):
            categories.add('credential-literal')
    # JSON strings are handled by the shared recursive record/decoder policy.
    # JS object literals carrying a non-empty numeric/string price are refused too.
    if re.search(r'''(?:["']?)(?:price|price_local|price_usd|usd_ref|media_url|image_url)(?:["']?)\s*:\s*(?:[0-9]|["'][^"'])''', text):
        categories.add('javascript-record-literal')
    if re.search(r'\b(?:eval|Function|atob)\s*\(|\bString\s*\.\s*fromCharCode\s*\(', text):
        categories.add('javascript-obfuscated-source')
    return categories, strings
