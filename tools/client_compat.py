"""Return an independent, unchanged client view of the canonical contract.

Nullable fields are defined by the contract itself; no type overrides are applied.
"""
import copy


def client_view(spec):
    return copy.deepcopy(spec)
