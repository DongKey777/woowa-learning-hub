"""R3 retrieval fabric scaffolding.

R3 is intentionally isolated from the production legacy/Lance paths until its
diagnostic gates pass.  Public runtime entrypoints should route here only when
the caller explicitly selects the experimental R3 backend.
"""

from .config import R3Config
from .query_plan import QueryPlan, build_query_plan

__all__ = ["R3Config", "QueryPlan", "build_query_plan"]
