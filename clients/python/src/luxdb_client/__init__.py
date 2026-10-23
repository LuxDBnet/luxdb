"""Public SDK entry point. The service is live."""
from .generated import GeneratedOperations
from .transport import ApiError, BaseClient, Request, Response, TransportError, TransportTimeout


class Client(GeneratedOperations, BaseClient):
    """A JSON client; paid credentials require explicit allow_paid=True."""


__all__ = ["Client", "ApiError", "TransportError", "TransportTimeout", "Request", "Response"]
