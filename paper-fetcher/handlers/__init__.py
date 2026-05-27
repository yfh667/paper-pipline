"""Publisher handlers: one class per publisher.

Each handler:
  - Implements fetch_one(job) -> Path (saves PDF, returns path)
  - Manages its own session/driver lifecycle via setup() / teardown()
  - Has its own gap_seconds for polite pacing between sequential fetches
"""
from .base import PublisherHandler, Job
from .ieee import IeeeHandler
from .acm import AcmHandler
from .elsevier import ElsevierHandler
from .optica import OpticaHandler

# Tag (as it appears in [tag] in the input list) -> handler class.
REGISTRY: dict[str, type[PublisherHandler]] = {
    "ieee": IeeeHandler,
    "acm": AcmHandler,
    "elsevier": ElsevierHandler,
    "optica": OpticaHandler,
}

__all__ = ["PublisherHandler", "Job", "REGISTRY",
           "IeeeHandler", "AcmHandler", "ElsevierHandler", "OpticaHandler"]
