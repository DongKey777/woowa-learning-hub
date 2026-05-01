"""R3 evaluation contracts."""

from .metrics import RerankerComparison, reranker_demotion_summary
from .qrels import R3QueryJudgement, R3Qrel, load_qrels
from .trace import R3Trace, read_jsonl, write_jsonl

__all__ = [
    "RerankerComparison",
    "reranker_demotion_summary",
    "R3Qrel",
    "R3QueryJudgement",
    "load_qrels",
    "R3Trace",
    "read_jsonl",
    "write_jsonl",
]
