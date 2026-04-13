#!/usr/bin/env python3
"""Mission relevance scoring for pull request collection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


STOPWORDS = {
    "java",
    "kotlin",
    "javascript",
    "js",
    "react",
    "spring",
    "android",
    "backend",
    "frontend",
    "mission",
    "woowacourse",
}


@dataclass(frozen=True)
class MissionSignals:
    repo_name: str | None = None
    mission_name: str | None = None
    title_hint: str | None = None
    branch_hint: str | None = None
    current_pr_title: str | None = None
    mission_keywords: tuple[str, ...] = ()


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    lowered = text.lower()
    collapsed = re.sub(r"[^0-9a-z가-힣]+", " ", lowered)
    return " ".join(collapsed.split())


def _normalize_compact(text: str | None) -> str:
    return _normalize_text(text).replace(" ", "")


def _extract_stage_numbers(text: str | None) -> set[str]:
    if not text:
        return set()
    patterns = [
        r"사이클\s*(\d+)",
        r"cycle\s*(\d+)",
        r"step\s*(\d+)",
        r"(\d+)\s*단계",
    ]
    numbers: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            numbers.add(match.group(1))
    return numbers


def _stage_variants(stage_numbers: set[str]) -> set[str]:
    variants: set[str] = set()
    for number in stage_numbers:
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


def _exact_hints(signals: MissionSignals) -> set[str]:
    hints = {
        _normalize_compact(signals.title_hint),
    }
    return {hint for hint in hints if hint}


def _mission_tokens(signals: MissionSignals) -> set[str]:
    raw_values = [signals.repo_name or "", signals.mission_name or ""]
    tokens: set[str] = set()
    for raw in raw_values:
        for token in re.split(r"[^0-9a-zA-Z가-힣]+", raw.lower()):
            cleaned = token.strip()
            if len(cleaned) < 3:
                continue
            if cleaned in STOPWORDS:
                continue
            tokens.add(cleaned)
    return tokens


def _focus_terms(signals: MissionSignals) -> set[str]:
    text = signals.current_pr_title or ""
    normalized = _normalize_text(text)
    if not normalized:
        return set()

    terms: set[str] = set()
    for fragment in re.findall(r"\(([^)]+)\)", text):
        for token in re.split(r"[^0-9a-zA-Z가-힣]+", fragment.lower()):
            cleaned = token.strip()
            if len(cleaned) >= 2 and cleaned not in STOPWORDS:
                terms.add(cleaned)
    return terms


def build_mission_signals(
    *,
    repo_name: str | None,
    mission_name: str | None,
    title_hint: str | None,
    branch_hint: str | None,
    current_pr_title: str | None,
    mission_keywords: list[str] | None = None,
) -> MissionSignals:
    return MissionSignals(
        repo_name=repo_name,
        mission_name=mission_name,
        title_hint=title_hint,
        branch_hint=branch_hint,
        current_pr_title=current_pr_title,
        mission_keywords=tuple(mission_keywords or []),
    )


def score_pull_request_relevance(pr: dict[str, Any], signals: MissionSignals) -> dict[str, Any]:
    title_text = _normalize_text(pr.get("title"))
    title_compact = _normalize_compact(pr.get("title"))
    body_text = _normalize_text(pr.get("body"))
    body_compact = body_text.replace(" ", "")
    ref_text = _normalize_text(
        " ".join(
            part
            for part in [
                (pr.get("base") or {}).get("ref"),
                (pr.get("head") or {}).get("ref"),
                ((pr.get("head") or {}).get("repo") or {}).get("full_name"),
            ]
            if part
        )
    )
    ref_compact = ref_text.replace(" ", "")

    stage_numbers = set()
    stage_numbers.update(_extract_stage_numbers(signals.title_hint))
    stage_numbers.update(_extract_stage_numbers(signals.branch_hint))
    stage_numbers.update(_extract_stage_numbers(signals.current_pr_title))

    score = 0
    reasons: list[str] = []

    for hint in _exact_hints(signals):
        if hint in title_compact:
            score += 20
            reasons.append(f"title-hint:{signals.title_hint}")
        elif hint in body_compact:
            score += 8
            reasons.append(f"body-hint:{signals.title_hint}")

    for variant in _stage_variants(stage_numbers):
        if variant in title_compact:
            score += 18
            reasons.append(f"title-stage:{variant}")
        elif variant in ref_compact:
            score += 12
            reasons.append(f"ref-stage:{variant}")
        elif variant in body_compact:
            score += 6
            reasons.append(f"body-stage:{variant}")

    for token in _mission_tokens(signals):
        if token in title_text:
            score += 3
            reasons.append(f"title-token:{token}")
        elif token in body_text:
            score += 1
            reasons.append(f"body-token:{token}")

    for token in _focus_terms(signals):
        if token in title_text:
            score += 4
            reasons.append(f"title-focus:{token}")
        elif token in body_text:
            score += 2
            reasons.append(f"body-focus:{token}")

    for token in signals.mission_keywords:
        normalized = _normalize_text(token)
        if not normalized or normalized in STOPWORDS:
            continue
        if normalized in title_text:
            score += 5
            reasons.append(f"title-mission-keyword:{normalized}")
        elif normalized in body_text:
            score += 2
            reasons.append(f"body-mission-keyword:{normalized}")

    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "score": score,
        "reasons": reasons,
    }


def filter_relevant_pull_requests(
    pull_requests: list[dict[str, Any]],
    signals: MissionSignals,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored = [score_pull_request_relevance(pr, signals) for pr in pull_requests]
    stage_constrained = bool(
        _extract_stage_numbers(signals.title_hint)
        or _extract_stage_numbers(signals.branch_hint)
        or _extract_stage_numbers(signals.current_pr_title)
    )
    threshold = 10 if stage_constrained else 1

    selected_numbers = {
        item["number"]
        for item in scored
        if item["score"] >= threshold
    }
    if not stage_constrained and not any(item["score"] > 0 for item in scored):
        selected_numbers = {pr["number"] for pr in pull_requests}
        threshold = 0

    matched = [pr for pr in pull_requests if pr.get("number") in selected_numbers]
    matched_count = len(matched)
    matched.sort(
        key=lambda pull_request: (
            pull_request.get("updated_at") or "",
            pull_request.get("number") or 0,
        ),
        reverse=True,
    )
    selected = matched
    if limit is not None:
        selected = selected[:limit]
    selected.sort(key=lambda pull_request: pull_request["number"])

    top_matches = sorted(scored, key=lambda item: (-item["score"], item["number"]))[:10]
    return selected, {
        "stage_constrained": stage_constrained,
        "threshold": threshold,
        "matched_count": matched_count,
        "selected_count": len(selected),
        "candidate_count": len(pull_requests),
        "top_matches": top_matches,
    }
