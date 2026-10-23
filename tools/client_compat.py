"""Explicit client-only compatibility for nullable values in the live API.

The canonical contract bytes are never changed. Remove these relaxations only
when the supplied contract and the service agree, with a reviewed regeneration.
"""
import copy


def client_view(spec):
    result = copy.deepcopy(spec)
    schemas = result['components']['schemas']
    fields = [schemas['SearchRow']['properties']['price_usd_band']]
    dimensions = schemas['Article']['properties']['dimensions']['properties']
    fields += [dimensions['height_cm'], dimensions['height_in']]
    for obj in fields:
        kind = obj.get('type')
        if isinstance(kind, str):
            obj['type'] = [kind, 'null']
        elif isinstance(kind, list) and 'null' not in kind:
            obj['type'] = kind + ['null']
    return result
