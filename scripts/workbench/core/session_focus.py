from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .cohort import current_cohort_year
from .comment_classifier import _has_column
from .paths import repo_context_dir
from .schema_validation import validate_payload


def _extract_year(iso_ts: str | None) -> int | None:
    """Pull the YYYY year out of an ISO-8601 timestamp like ``2024-04-12T...``."""
    if not iso_ts or len(iso_ts) < 4:
        return None
    head = iso_ts[:4]
    return int(head) if head.isdigit() else None

GENERIC_ROOTS = frozenset({
    "src/main/java", "src/test/java", "src/main", "src/test",
    "src", "test", "lib", "app", "main", "resources",
})


def _filtered_retrieval_path_hints(hints: list[str]) -> list[str]:
    return [h for h in hints if h.lower() not in GENERIC_ROOTS and len(h.split("/")) >= 3]

ROLE_WEIGHTS = {
    "mentor_original": 1.0,
    "mentor_followup": 0.8,
    "crew_self_reply": 0.3,
    "crew_self_original": 0.2,
    "bot": 0.0,
    "mentor": 1.0,
    "self": 0.2,
}

STOPWORDS = {
    "",
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "what",
    "why",
    "how",
    "review",
    "pr",
    "code",
    "설명",
    "다시",
    "현재",
    "기준",
    "무엇",
    "어떻게",
    "왜",
    "뭐야",
    "정리",
    "질문",
    "다른",
    "했는지",
}

GENERIC_PATHS = {
    "README.md",
    "build.gradle",
    "settings.gradle",
    ".gitignore",
    "gradlew",
    "gradlew.bat",
}

GENERIC_PATH_TOKENS = {
    "src",
    "main",
    "test",
    "java",
    "resources",
    "readme",
    "build",
    "gradle",
    "docs",
    "domain",
}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _slug(value: str) -> str:
    return value.lower().replace("/", "-").replace(" ", "-")


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    lowered = text.lower()
    collapsed = re.sub(r"[^0-9a-z가-힣]+", " ", lowered)
    return " ".join(collapsed.split())


def _normalize_compact(text: str | None) -> str:
    return _normalize_text(text).replace(" ", "")


def _clip(value: str | None, limit: int = 220) -> str:
    if not value:
        return ""
    flattened = " ".join(value.split())
    if len(flattened) <= limit:
        return flattened
    return flattened[: limit - 3].rstrip() + "..."


def _extract_stage_numbers(*values: str | None) -> set[str]:
    patterns = [
        r"사이클\s*(\d+)",
        r"cycle\s*(\d+)",
        r"step\s*(\d+)",
        r"(\d+)\s*단계",
    ]
    numbers: set[str] = set()
    for value in values:
        if not value:
            continue
        for pattern in patterns:
            for match in re.finditer(pattern, value, flags=re.IGNORECASE):
                numbers.add(match.group(1))
    return numbers


def _stage_variants(numbers: set[str]) -> set[str]:
    variants = set()
    for number in numbers:
        variants.update({
            f"사이클{number}",
            f"사이클 {number}",
            f"cycle{number}",
            f"cycle {number}",
            f"step{number}",
            f"step {number}",
            f"{number}단계",
            f"{number} 단계",
        })
    return {_normalize_compact(value) for value in variants if value}


def _tokenize_text(text: str | None) -> list[str]:
    normalized = _normalize_text(text)
    tokens = []
    for token in normalized.split():
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _topic_terms(topic_terms: list[str] | None) -> list[str]:
    terms: list[str] = []
    for term in topic_terms or []:
        lowered = term.lower()
        if lowered and lowered not in terms:
            terms.append(lowered)
    return terms


def _path_signature(paths: list[str]) -> dict:
    exact_paths = []
    directories = set()
    tokens = set()
    for raw_path in paths:
        path = raw_path.strip()
        if not path:
            continue
        exact_paths.append(path)
        pure_path = PurePosixPath(path)
        for index in range(1, len(pure_path.parts)):
            directory = PurePosixPath(*pure_path.parts[:index])
            if len(directory.parts) < 3:
                continue
            directories.add(str(directory))
        normalized = path.lower()
        pieces = (
            normalized.replace("/", " ")
            .replace("-", " ")
            .replace("_", " ")
            .replace(".", " ")
            .split()
        )
        for piece in pieces:
            if len(piece) >= 2 and piece not in STOPWORDS and piece not in GENERIC_PATH_TOKENS:
                tokens.add(piece)
    return {
        "paths": exact_paths,
        "directories": sorted(directories),
        "tokens": sorted(tokens),
    }


def _current_pr_paths(connection: sqlite3.Connection, current_pr_number: int | None) -> list[str]:
    if current_pr_number is None:
        return []
    rows = connection.execute(
        """
        SELECT f.path
        FROM pull_request_files_current f
        JOIN pull_requests_current pr ON pr.id = f.pull_request_id
        WHERE pr.number = ?
          AND pr.is_missing = 0
          AND f.is_missing = 0
          AND f.path IS NOT NULL
        ORDER BY f.path
        """,
        (current_pr_number,),
    ).fetchall()
    return [row["path"] for row in rows]


def _review_maps(connection: sqlite3.Connection) -> tuple[dict[int, list[dict]], dict[int, list[dict]], dict[int, list[dict]]]:
    has_review_role = _has_column(connection, "pull_request_reviews_current", "reviewer_role")
    has_comment_role = _has_column(connection, "pull_request_review_comments_current", "comment_role")
    has_issue_role = _has_column(connection, "pull_request_issue_comments_current", "comment_role")

    review_role_col = ", reviewer_role" if has_review_role else ""
    review_bot_filter = " AND reviewer_role != 'bot'" if has_review_role else ""
    comment_role_col = ", comment_role" if has_comment_role else ""
    comment_bot_filter = " AND comment_role != 'bot'" if has_comment_role else ""
    issue_role_col = ", comment_role" if has_issue_role else ""
    issue_bot_filter = " AND comment_role != 'bot'" if has_issue_role else ""

    review_rows = connection.execute(
        f"""
        SELECT pull_request_id, reviewer_login, state, body, submitted_at{review_role_col}
        FROM pull_request_reviews_current
        WHERE is_missing = 0{review_bot_filter}
        ORDER BY pull_request_id, submitted_at
        """
    ).fetchall()
    comment_rows = connection.execute(
        f"""
        SELECT pull_request_id, user_login, path, line, body, created_at{comment_role_col}
        FROM pull_request_review_comments_current
        WHERE is_missing = 0{comment_bot_filter}
        ORDER BY pull_request_id, created_at
        """
    ).fetchall()
    issue_comment_rows = connection.execute(
        f"""
        SELECT pull_request_id, user_login, body, created_at{issue_role_col}
        FROM pull_request_issue_comments_current
        WHERE is_missing = 0{issue_bot_filter}
        ORDER BY pull_request_id, created_at
        """
    ).fetchall()

    review_map: dict[int, list[dict]] = {}
    comment_map: dict[int, list[dict]] = {}
    issue_comment_map: dict[int, list[dict]] = {}

    for row in review_rows:
        review_map.setdefault(row["pull_request_id"], []).append(dict(row))
    for row in comment_rows:
        comment_map.setdefault(row["pull_request_id"], []).append(dict(row))
    for row in issue_comment_rows:
        issue_comment_map.setdefault(row["pull_request_id"], []).append(dict(row))

    return review_map, comment_map, issue_comment_map


def _candidate_rows(connection: sqlite3.Connection, current_pr_number: int | None) -> list[sqlite3.Row]:
    query = """
        SELECT id, number, title, body, author_login, base_ref_name, head_ref_name, updated_at, created_at
        FROM pull_requests_current
        WHERE is_missing = 0
    """
    params: tuple = ()
    if current_pr_number is not None:
        query += " AND number != ?"
        params = (current_pr_number,)
    query += " ORDER BY updated_at DESC, number DESC"
    return connection.execute(query, params).fetchall()


def _file_map(connection: sqlite3.Connection) -> dict[int, list[str]]:
    rows = connection.execute(
        """
        SELECT pull_request_id, path
        FROM pull_request_files_current
        WHERE is_missing = 0
          AND path IS NOT NULL
        ORDER BY pull_request_id, path
        """
    ).fetchall()
    result: dict[int, list[str]] = {}
    for row in rows:
        result.setdefault(row["pull_request_id"], []).append(row["path"])
    return result


def _extract_focus_excerpt(body: str | None) -> str:
    if not body:
        return ""
    sanitized = re.sub(r"<!--.*?-->", " ", body, flags=re.DOTALL)
    lines = sanitized.splitlines()
    keywords = ["집중", "리뷰", "고민", "궁금", "focus", "question"]
    for index, raw_line in enumerate(lines):
        line = raw_line.strip().lower()
        if not line:
            continue
        if not any(keyword in line for keyword in keywords):
            continue
        collected = []
        for following in lines[index + 1:index + 13]:
            stripped = following.strip()
            if not stripped:
                if collected:
                    break
                continue
            if stripped.startswith("#"):
                break
            if "코드와 관련된 질문이 있다면" in stripped:
                collected = []
                break
            if "adding comments to a pull request" in stripped.lower():
                continue
            if stripped.startswith("<!--") or stripped.startswith("-->"):
                continue
            collected.append(stripped)
        if collected:
            return _clip(" ".join(collected), limit=320)

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
    for paragraph in paragraphs:
        lowered = paragraph.lower()
        if "코드와 관련된 질문이 있다면" in lowered:
            continue
        if "체크 리스트" in paragraph:
            continue
        if "예를 들어" in paragraph:
            continue
        if len(paragraph) < 30:
            continue
        return _clip(paragraph, limit=320)
    return ""


def _stage_score(candidate: dict, title_hint: str | None, branch_hint: str | None, current_pr_title: str | None) -> tuple[int, list[str]]:
    title_compact = _normalize_compact(candidate.get("title"))
    body_compact = _normalize_compact(candidate.get("body"))
    ref_compact = _normalize_compact(f"{candidate.get('base_ref_name') or ''} {candidate.get('head_ref_name') or ''}")
    score = 0
    reasons: list[str] = []

    hint = _normalize_compact(title_hint)
    if hint:
        if hint in title_compact:
            score += 20
            reasons.append(f"title-hint:{title_hint}")
        elif hint in body_compact:
            score += 8
            reasons.append(f"body-hint:{title_hint}")

    for variant in _stage_variants(_extract_stage_numbers(title_hint, branch_hint, current_pr_title)):
        if variant in title_compact:
            score += 18
            reasons.append(f"title-stage:{variant}")
        elif variant in ref_compact:
            score += 12
            reasons.append(f"ref-stage:{variant}")
        elif variant in body_compact:
            score += 6
            reasons.append(f"body-stage:{variant}")
    return score, reasons


def _text_overlap_score(tokens: list[str], title: str, body: str, focus_excerpt: str) -> tuple[int, list[str], list[str]]:
    score = 0
    reasons: list[str] = []
    matched_terms: list[str] = []
    for token in tokens:
        if token in title:
            score += 6
            reasons.append(f"title-term:{token}")
            matched_terms.append(token)
        elif token in focus_excerpt:
            score += 4
            reasons.append(f"focus-term:{token}")
            matched_terms.append(token)
        elif token in body:
            score += 2
            reasons.append(f"body-term:{token}")
            matched_terms.append(token)
    return score, reasons, sorted(set(matched_terms))


def _review_overlap_score(tokens: list[str], reviews: list[dict]) -> tuple[int, list[str], list[dict]]:
    scored_samples: list[dict] = []
    for review in reviews:
        normalized = _normalize_text(review.get("body"))
        if not normalized:
            continue
        matched_terms = [token for token in tokens if token in normalized]
        if not matched_terms:
            continue
        review_score = min(14, 4 + len(matched_terms) * 3)
        role = review.get("reviewer_role") or ""
        role_weight = ROLE_WEIGHTS.get(role, 1.0)
        review_score = int(review_score * role_weight)
        if review_score <= 0:
            continue
        scored_samples.append({
            "reviewer_login": review.get("reviewer_login"),
            "state": review.get("state"),
            "matched_terms": sorted(set(matched_terms)),
            "body_excerpt": _clip(review.get("body"), limit=220),
            "score": review_score,
        })

    scored_samples.sort(key=lambda item: (-item["score"], item.get("reviewer_login") or ""))
    samples = scored_samples[:3]
    score = sum(item["score"] for item in samples)
    reasons: list[str] = []
    for sample in samples:
        for token in sample.get("matched_terms", [])[:3]:
            reasons.append(f"review-body-term:{token}")
    return score, reasons, samples


def _review_comment_overlap_score(tokens: list[str], local_signature: dict, comments: list[dict]) -> tuple[int, list[str], list[dict]]:
    scored_samples: list[dict] = []
    local_exact = set(local_signature["paths"])
    local_dirs = set(local_signature["directories"])
    local_tokens = set(local_signature["tokens"])

    for comment in comments:
        comment_score = 0
        comment_reasons: list[str] = []
        path = comment.get("path") or ""
        body = comment.get("body") or ""
        normalized_body = _normalize_text(body)
        matched_terms = [token for token in tokens if token in normalized_body]

        if path and PurePosixPath(path).name not in GENERIC_PATHS:
            if path in local_exact:
                comment_score += 12
                comment_reasons.append(f"review-path-exact:{path}")
            else:
                candidate_dir = str(PurePosixPath(path).parent)
                if candidate_dir in local_dirs:
                    comment_score += 5
                    comment_reasons.append(f"review-path-dir:{candidate_dir}")

            path_tokens = _path_signature([path])["tokens"]
            shared_tokens = sorted(local_tokens & set(path_tokens))
            for token in shared_tokens[:4]:
                comment_score += 2
                comment_reasons.append(f"review-path-token:{token}")

        if matched_terms:
            comment_score += min(12, 4 + len(matched_terms) * 2)
            for token in matched_terms[:3]:
                comment_reasons.append(f"review-comment-term:{token}")

        if comment_score <= 0:
            continue

        role = comment.get("comment_role") or ""
        role_weight = ROLE_WEIGHTS.get(role, 1.0)
        comment_score = int(comment_score * role_weight)
        if comment_score <= 0:
            continue

        scored_samples.append({
            "user_login": comment.get("user_login"),
            "path": path or None,
            "line": comment.get("line"),
            "matched_terms": sorted(set(matched_terms)),
            "body_excerpt": _clip(body, limit=220),
            "score": comment_score,
            "score_reasons": comment_reasons,
        })

    scored_samples.sort(key=lambda item: (-item["score"], item.get("path") or "", item.get("line") or 0))
    samples = scored_samples[:4]
    score = sum(item["score"] for item in samples)
    reasons: list[str] = []
    for sample in samples:
        reasons.extend(sample.get("score_reasons", [])[:5])
        sample.pop("score_reasons", None)
    return score, reasons, samples


def _issue_comment_overlap_score(tokens: list[str], issue_comments: list[dict]) -> tuple[int, list[str], list[dict]]:
    scored_samples: list[dict] = []
    for comment in issue_comments:
        body = comment.get("body") or ""
        normalized_body = _normalize_text(body)
        matched_terms = [token for token in tokens if token in normalized_body]
        if not matched_terms:
            continue
        item_score = min(10, 3 + len(matched_terms) * 2)
        role = comment.get("comment_role") or ""
        role_weight = ROLE_WEIGHTS.get(role, 1.0)
        item_score = int(item_score * role_weight)
        if item_score <= 0:
            continue
        scored_samples.append({
            "user_login": comment.get("user_login"),
            "matched_terms": sorted(set(matched_terms)),
            "body_excerpt": _clip(body, limit=220),
            "score": item_score,
        })

    scored_samples.sort(key=lambda item: (-item["score"], item.get("user_login") or ""))
    samples = scored_samples[:3]
    score = sum(item["score"] for item in samples)
    reasons: list[str] = []
    for sample in samples:
        for token in sample.get("matched_terms", [])[:3]:
            reasons.append(f"issue-comment-term:{token}")
    return score, reasons, samples


def _path_overlap_score(
    local_signature: dict,
    candidate_paths: list[str],
    retrieval_path_hints: list[str] | None = None,
) -> tuple[int, list[str], list[str]]:
    if not candidate_paths:
        return 0, [], []

    candidate_signature = _path_signature(candidate_paths)
    local_exact = set(local_signature["paths"])
    candidate_exact = set(candidate_signature["paths"])
    local_dirs = set(local_signature["directories"])
    candidate_dirs = set(candidate_signature["directories"])
    local_tokens = set(local_signature["tokens"])
    candidate_tokens = set(candidate_signature["tokens"])

    score = 0
    reasons: list[str] = []
    matched_paths: list[str] = []

    exact_matches = sorted(path for path in (local_exact & candidate_exact) if PurePosixPath(path).name not in GENERIC_PATHS)
    if exact_matches:
        for path in exact_matches[:3]:
            score += 16
            reasons.append(f"path-exact:{path}")
            matched_paths.append(path)

    dir_matches = sorted(local_dirs & candidate_dirs, key=len, reverse=True)
    for directory in dir_matches[:3]:
        score += 5
        reasons.append(f"path-dir:{directory}")

    token_matches = sorted(local_tokens & candidate_tokens)
    for token in token_matches[:5]:
        score += 2
        reasons.append(f"path-token:{token}")

    if retrieval_path_hints:
        hint_bonus = 0
        for hint in retrieval_path_hints[:5]:
            normalized_hint = hint.rstrip("/").lower()
            for candidate_path in candidate_paths:
                if normalized_hint in candidate_path.lower():
                    hint_bonus += 3
                    reasons.append(f"mission-path-hint:{hint}")
                    break
            if hint_bonus >= 6:
                break
        score += hint_bonus

    return score, reasons, matched_paths


def build_session_focus(
    repo_name: str,
    db_path: Path,
    mode: str,
    prompt: str,
    current_pr_number: int | None,
    git_diff_files: list[str],
    title_hint: str | None,
    branch_hint: str | None,
    current_pr_title: str | None,
    topic_terms: list[str] | None,
    retrieval_path_hints: list[str] | None = None,
) -> dict:
    with _connect(db_path) as connection:
        current_pr_paths = _current_pr_paths(connection, current_pr_number)
        local_paths = git_diff_files or current_pr_paths
        local_source = "git_diff" if git_diff_files else ("current_pr_files" if current_pr_paths else "none")
        local_signature = _path_signature(local_paths)
        file_map = _file_map(connection)
        review_map, comment_map, issue_comment_map = _review_maps(connection)
        candidates = []
        prompt_tokens = _tokenize_text(prompt)
        combined_terms = prompt_tokens + [term for term in _topic_terms(topic_terms) if term not in prompt_tokens]
        stage_constrained = bool(_extract_stage_numbers(title_hint, branch_hint, current_pr_title))
        cohort_year = current_cohort_year()

        for row in _candidate_rows(connection, current_pr_number):
            candidate = dict(row)
            candidate_paths = file_map.get(candidate["id"], [])
            review_samples = review_map.get(candidate["id"], [])
            comment_samples = comment_map.get(candidate["id"], [])
            issue_comment_samples = issue_comment_map.get(candidate["id"], [])
            focus_excerpt = _extract_focus_excerpt(candidate.get("body"))
            normalized_title = _normalize_text(candidate.get("title"))
            normalized_body = _normalize_text(candidate.get("body"))
            normalized_focus = _normalize_text(focus_excerpt)

            stage_score, stage_reasons = _stage_score(candidate, title_hint, branch_hint, current_pr_title)
            if stage_constrained and stage_score <= 0:
                continue
            text_score, text_reasons, matched_terms = _text_overlap_score(combined_terms, normalized_title, normalized_body, normalized_focus)
            review_score, review_reasons, matched_review_samples = _review_overlap_score(combined_terms, review_samples)
            comment_score, comment_reasons, matched_comment_samples = _review_comment_overlap_score(combined_terms, local_signature, comment_samples)
            issue_comment_score, issue_comment_reasons, matched_issue_comment_samples = _issue_comment_overlap_score(combined_terms, issue_comment_samples)
            filtered_hints = _filtered_retrieval_path_hints(retrieval_path_hints or [])
            path_score, path_reasons, matched_paths = _path_overlap_score(local_signature, candidate_paths, filtered_hints)
            score = stage_score + text_score + review_score + comment_score + issue_comment_score + path_score
            if score <= 0:
                continue

            created_year = _extract_year(candidate.get("created_at"))
            cohort_caveat = bool(
                created_year is not None and created_year != cohort_year
            )
            freshness_note = (
                f"{created_year}년 자료 — 현재 미션 세부 요구사항과 다를 수 있음"
                if cohort_caveat
                else None
            )
            candidates.append({
                "pr_number": candidate["number"],
                "title": candidate["title"],
                "author_login": candidate["author_login"],
                "updated_at": candidate.get("updated_at"),
                "created_at": candidate.get("created_at"),
                "created_year": created_year,
                "cohort_caveat": cohort_caveat,
                "freshness_note": freshness_note,
                "score": score,
                "reasons": stage_reasons + text_reasons + review_reasons + comment_reasons + issue_comment_reasons + path_reasons,
                "matched_terms": matched_terms,
                "matched_paths": matched_paths[:5],
                "focus_excerpt": focus_excerpt,
                "matched_review_samples": matched_review_samples,
                "matched_comment_samples": matched_comment_samples,
                "matched_issue_comment_samples": matched_issue_comment_samples,
                "path_examples": candidate_paths[:5],
            })

    candidates.sort(key=lambda item: (-item["score"], item.get("updated_at") or "", item["pr_number"]))
    payload = {
        "focus_type": "session_pr_focus",
        "repo": repo_name,
        "mode": mode,
        "generated_at": _timestamp(),
        "current_pr_number": current_pr_number,
        "prompt": prompt,
        "prompt_terms": prompt_tokens,
        "topic_terms": _topic_terms(topic_terms),
        "local_path_signature": {
            "source": local_source,
            "paths": local_paths[:20],
            "tokens": local_signature["tokens"][:20],
            "directories": local_signature["directories"][:20],
        },
        "candidate_count": len(candidates),
        "candidates": candidates[:10],
    }
    validate_payload("session-pr-focus", payload)
    path = repo_context_dir(repo_name) / f"{mode}-focus.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["json_path"] = str(path)
    return payload
