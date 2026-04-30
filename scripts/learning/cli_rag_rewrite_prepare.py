"""CLI for query-rewrite-v1 wrapper (plan §P4.2 / §9 element 3).

The wrapper is deterministic: it computes a stable ``prompt_hash`` from
the learner prompt + mode, infers a default mode from token shape if
none provided, writes the input artifact to
``state/cs_rag/query_rewrites/<prompt_hash>.input.json``, and prints
the expected output path on stdout.

The AI session is the *caller* — it runs this wrapper from inside its
own turn, then reads the input artifact, follows the procedure in
``skills/woowa-rag-rewrite/SKILL.md``, and writes the output JSON to
the expected path. ``searcher.search()`` reads the output when present
or falls back to PRF (P4.3).

This file never calls an LLM. It is a pure placeholder factory.

Schema (canonical): ``docs/ai-behavior-contracts.md`` §query-rewrite-v1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_ID_INPUT = "query-rewrite-v1.input"
DEFAULT_OUT_REL = "state/cs_rag/query_rewrites"


# ---------------------------------------------------------------------------
# Mode inference
# ---------------------------------------------------------------------------

# Korean particles + colloquial markers that signal a normalize-friendly query.
_COLLOQUIAL_TOKENS = ("뭐야", "뭐임", "뭔데", "이란", "이란게", "란게", "임", "이야", "야?")
# Compound-question markers (decompose).
_COMPOUND_TOKENS = ("랑", "와", "그리고", "또", " 및 ", " 및\n", "차이", " vs ", "VS")
# Compound markers also include connectives between clauses.
_COMPOUND_PUNCT = re.compile(r"[?？]\s*\S+.*[?？]")


def infer_mode(prompt: str) -> str:
    """Pick a default mode from token shape.

    Order matters — we prefer ``decompose`` for clearly multi-part
    questions, then ``normalize`` for short colloquial queries, and
    fall back to ``hyde`` for everything else (factual, low-token
    queries).
    """
    text = prompt.strip()
    if not text:
        return "hyde"

    # decompose: multiple question marks OR explicit compound connectives
    qmark_count = text.count("?") + text.count("？")
    has_compound_token = any(tok in text for tok in _COMPOUND_TOKENS)
    if qmark_count >= 2 or has_compound_token or _COMPOUND_PUNCT.search(text):
        return "decompose"

    # normalize: short query ending in colloquial marker
    if len(text) <= 30 and any(text.endswith(tok) or tok in text[-6:] for tok in _COLLOQUIAL_TOKENS):
        return "normalize"

    return "hyde"


# ---------------------------------------------------------------------------
# prompt_hash
# ---------------------------------------------------------------------------

def compute_prompt_hash(prompt: str, mode: str) -> str:
    """Deterministic hash for input/output cache key.

    Includes mode so the same prompt under a different mode produces a
    different artifact pair (the rewrites differ).
    """
    norm = prompt.strip()
    payload = f"{mode}\x1f{norm}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


# ---------------------------------------------------------------------------
# learner_context normalization
# ---------------------------------------------------------------------------

def normalize_learner_context(raw: dict | None) -> dict:
    """Return a dict that always satisfies the contract shape.

    Keys with no value default to ``null`` / empty list per the schema in
    ``docs/ai-behavior-contracts.md``.
    """
    if not isinstance(raw, dict):
        raw = {}
    return {
        "experience_level": raw.get("experience_level"),
        "mastered_concepts": list(raw.get("mastered_concepts", [])),
        "uncertain_concepts": list(raw.get("uncertain_concepts", [])),
        "recent_topics": list(raw.get("recent_topics", [])),
    }


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "knowledge" / "cs").exists() and (parent / "scripts").exists():
            return parent
    return here.parents[2]


def write_input_artifact(
    *,
    prompt: str,
    mode: str,
    learner_context: dict,
    out_root: Path,
    now: datetime | None = None,
) -> tuple[Path, Path, str]:
    """Write input artifact and return (input_path, output_path, prompt_hash)."""
    prompt_hash = compute_prompt_hash(prompt, mode)
    out_root.mkdir(parents=True, exist_ok=True)
    input_path = out_root / f"{prompt_hash}.input.json"
    output_path = out_root / f"{prompt_hash}.output.json"
    payload = {
        "schema_id": SCHEMA_ID_INPUT,
        "prompt_hash": prompt_hash,
        "prompt": prompt,
        "learner_context": normalize_learner_context(learner_context),
        "mode": mode,
        "produced_at": (now or datetime.now(timezone.utc)).isoformat(),
    }
    input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return input_path, output_path, prompt_hash


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(
        description=(
            "query-rewrite-v1 wrapper. Writes the input artifact and prints "
            "the expected output path. The AI session is responsible for "
            "filling the output (see skills/woowa-rag-rewrite/SKILL.md)."
        )
    )
    parser.add_argument("prompt", help="Original learner question.")
    parser.add_argument(
        "--mode",
        choices=("hyde", "decompose", "normalize", "auto"),
        default="auto",
        help="Rewrite mode. 'auto' (default) infers from prompt shape.",
    )
    parser.add_argument(
        "--out",
        default=str(repo_root / DEFAULT_OUT_REL),
        help="Storage root (default: state/cs_rag/query_rewrites).",
    )
    parser.add_argument(
        "--learner-context",
        default=None,
        help='Optional JSON string with experience_level / mastered_concepts / uncertain_concepts / recent_topics.',
    )
    args = parser.parse_args(argv)

    if not args.prompt or not args.prompt.strip():
        print("[rag-rewrite-prepare] prompt is empty", file=sys.stderr)
        return 2

    mode = infer_mode(args.prompt) if args.mode == "auto" else args.mode

    learner_context = None
    if args.learner_context:
        try:
            learner_context = json.loads(args.learner_context)
        except json.JSONDecodeError as exc:
            print(f"[rag-rewrite-prepare] --learner-context not valid JSON: {exc}", file=sys.stderr)
            return 2

    input_path, output_path, prompt_hash = write_input_artifact(
        prompt=args.prompt,
        mode=mode,
        learner_context=learner_context or {},
        out_root=Path(args.out),
    )

    print(json.dumps(
        {
            "schema_id": SCHEMA_ID_INPUT,
            "prompt_hash": prompt_hash,
            "mode": mode,
            "input_path": str(input_path),
            "output_path": str(output_path),
        },
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
