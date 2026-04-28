from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .git_context import read_current_pr, read_git_context
from .paths import repo_analysis_dir
from .schema_validation import validate_payload
from .shell import run_capture

LANGUAGE_EXTENSIONS = {
    ".java": "java",
    ".kt": "kotlin",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".py": "python",
    ".rb": "ruby",
    ".go": "go",
}

BUILD_FILES = {
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "settings.gradle": "gradle",
    "settings.gradle.kts": "gradle",
    "pom.xml": "maven",
    "package.json": "npm",
    "pnpm-lock.yaml": "node",
    "yarn.lock": "node",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "Gemfile": "ruby",
}

LAYER_RULES = {
    "domain": ["domain", "model", "entity", "aggregate"],
    "application": ["application", "usecase", "service"],
    "infrastructure": ["infra", "infrastructure", "adapter", "persistence"],
    "persistence": ["repository", "dao", "jdbc", "database", "db", "jpa", "mongo", "sqlite"],
    "presentation": ["controller", "handler", "view", "ui", "screen", "page", "component"],
    "parsing": ["parser", "parse", "input", "output", "validation", "validator", "request", "response", "dto"],
    "testing": ["test", "fixture", "stub", "mock"],
}

CONCERN_RULES = [
    {
        "id": "persistence",
        "label": "Persistence",
        "keywords": ["repository", "dao", "jdbc", "sqlite", "database", "db", "jpa", "mongo", "sql"],
        "fallback_query": "repository",
    },
    {
        "id": "transaction",
        "label": "Transaction",
        "keywords": ["transaction", "rollback", "commit", "connection", "datasource"],
        "fallback_query": "transaction",
    },
    {
        "id": "layering",
        "label": "Layering",
        "keywords": ["service", "controller", "application", "infra", "view", "usecase"],
        "fallback_query": "service",
    },
    {
        "id": "domain_modeling",
        "label": "Domain",
        "keywords": ["domain", "model", "entity", "aggregate", "object"],
        "fallback_query": "domain",
    },
    {
        "id": "parsing_validation",
        "label": "Validation",
        "keywords": ["parser", "parse", "validation", "validator", "input", "request", "response", "dto"],
        "fallback_query": "validation",
    },
    {
        "id": "testing",
        "label": "Test",
        "keywords": ["test", "junit", "assertj", "jest", "pytest", "cypress", "fixture"],
        "fallback_query": "test",
    },
    {
        "id": "ui_flow",
        "label": "UI",
        "keywords": ["view", "ui", "component", "screen", "page", "render", "input", "output"],
        "fallback_query": "view",
    },
    {
        "id": "state_management",
        "label": "State",
        "keywords": ["state", "store", "session", "context", "cache", "reducer"],
        "fallback_query": "state",
    },
]

TOKEN_STOPWORDS = {
    "",
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "your",
    "java",
    "kotlin",
    "javascript",
    "typescript",
    "python",
    "woowacourse",
    "mission",
    "repo",
    "project",
    "main",
    "test",
    "src",
    "readme",
    "gradle",
    "build",
    "docs",
    "file",
    "files",
    "step",
    "cycle",
    "단계",
    "사이클",
    "요구사항",
    "기능",
    "학습",
    "목표",
}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clip(value: str | None, limit: int = 160) -> str | None:
    if not value:
        return None
    flattened = " ".join(str(value).split())
    if len(flattened) <= limit:
        return flattened
    return flattened[: limit - 3].rstrip() + "..."


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    lowered = text.lower()
    collapsed = re.sub(r"[^0-9a-z가-힣]+", " ", lowered)
    return " ".join(collapsed.split())


def _tokenize(text: str | None) -> list[str]:
    tokens = []
    for token in _normalize_text(text).split():
        if len(token) < 2:
            continue
        if token in TOKEN_STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _repo_files(repo_path: Path) -> list[Path]:
    files: set[Path] = set()

    # Tracked files (existing behavior)
    tracked = run_capture(["git", "ls-files"], cwd=repo_path)
    if tracked.returncode == 0:
        for line in tracked.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                files.add(repo_path / stripped)

    # Untracked files, respecting .gitignore — required so mid-implementation
    # work (controller/, domain/ before first commit) is visible to layer detection.
    untracked = run_capture(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo_path)
    if untracked.returncode == 0:
        for line in untracked.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                files.add(repo_path / stripped)

    ignored = {".git", ".gradle", "build", "dist", "target", "node_modules", ".idea", ".next"}

    if not files:
        # Last-resort fallback: rglob (when git is unavailable or returns nothing).
        for path in repo_path.rglob("*"):
            if not path.is_file():
                continue
            try:
                rel_parts = path.relative_to(repo_path).parts
            except ValueError:
                continue
            if any(part in ignored for part in rel_parts):
                continue
            files.add(path)
        return list(files)

    # Defense-in-depth: even if `--exclude-standard` lets something through,
    # filter against the ignored set on repo-relative parts (not absolute parts —
    # repo path may itself contain a token like "build" and trigger false rejects).
    safe_files: list[Path] = []
    for path in files:
        if not path.is_file():
            continue
        try:
            rel_parts = path.relative_to(repo_path).parts
        except ValueError:
            continue
        if any(part in ignored for part in rel_parts):
            continue
        safe_files.append(path)
    return safe_files


def _build_files(repo_path: Path) -> list[Path]:
    files = []
    for name in BUILD_FILES:
        path = repo_path / name
        if path.exists():
            files.append(path)
    return files


def _primary_build_tool(build_files: list[Path]) -> str | None:
    counts = Counter(BUILD_FILES[path.name] for path in build_files if path.name in BUILD_FILES)
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def _language_counts(files: list[Path]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for path in files:
        language = LANGUAGE_EXTENSIONS.get(path.suffix.lower())
        if language:
            counts[language] += 1
    return dict(counts)


def _source_and_test_roots(repo_path: Path, files: list[Path]) -> tuple[list[str], list[str]]:
    source_roots = set()
    test_roots = set()
    for path in files:
        rel = path.relative_to(repo_path).as_posix()
        lower = rel.lower()
        if lower.startswith("src/test/"):
            parts = lower.split("/")
            test_roots.add("/".join(parts[:3]) if len(parts) >= 3 else lower)
            continue
        if lower.startswith("src/"):
            parts = lower.split("/")
            source_roots.add("/".join(parts[:3]) if len(parts) >= 3 else lower)
            continue
    return sorted(source_roots)[:8], sorted(test_roots)[:8]


def _package_roots(repo_path: Path, files: list[Path]) -> list[str]:
    packages: Counter[str] = Counter()
    for path in files:
        suffix = path.suffix.lower()
        if suffix not in {".java", ".kt"}:
            continue
        text = _read_text(path)
        match = re.search(r"^\s*package\s+([a-zA-Z0-9_.]+)\s*;", text, flags=re.MULTILINE)
        if not match:
            continue
        package_name = match.group(1)
        parts = package_name.split(".")
        package_root = ".".join(parts[: min(3, len(parts))])
        packages[package_root] += 1
    return [name for name, _ in packages.most_common(8)]


def _top_level_entries(repo_path: Path, files: list[Path]) -> list[str]:
    counts: Counter[str] = Counter()
    for path in files:
        rel = path.relative_to(repo_path)
        if not rel.parts:
            continue
        top = rel.parts[0]
        counts[top] += 1
    return [name for name, _ in counts.most_common(8)]


def _dependency_signals(repo_path: Path, build_files: list[Path]) -> list[str]:
    signals: Counter[str] = Counter()
    for path in build_files:
        text = _read_text(path)
        if path.name in {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"}:
            for artifact in re.findall(r"['\"]([a-zA-Z0-9_.-]+:[a-zA-Z0-9_.-]+)(?::[a-zA-Z0-9_.-]+)?['\"]", text):
                signals[artifact.split(":")[1].lower()] += 1
        elif path.name == "pom.xml":
            for artifact in re.findall(r"<artifactId>([^<]+)</artifactId>", text):
                signals[artifact.lower()] += 1
        elif path.name == "package.json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = {}
            for key in payload.get("dependencies", {}):
                signals[key.lower()] += 1
            for key in payload.get("devDependencies", {}):
                signals[key.lower()] += 1
        elif path.name in {"pyproject.toml", "requirements.txt"}:
            for line in text.splitlines():
                cleaned = line.strip().split("==")[0].split(">=")[0].split("<=")[0]
                if cleaned and cleaned[0].isalpha():
                    signals[cleaned.lower()] += 1
    return [name for name, _ in signals.most_common(12)]


def _readme_path(repo_path: Path) -> Path | None:
    candidates = [
        repo_path / "README.md",
        repo_path / "readme.md",
        repo_path / "README.MD",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _readme_analysis(repo_path: Path) -> dict:
    path = _readme_path(repo_path)
    if path is None:
        return {
            "path": None,
            "title": None,
            "headings": [],
            "summary_lines": [],
            "requirement_lines": [],
            "keywords": [],
        }

    text = _read_text(path)
    lines = text.splitlines()
    in_code_block = False
    headings = []
    summary_lines = []
    requirement_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not stripped:
            continue
        if stripped.startswith("#"):
            headings.append(stripped.lstrip("#").strip())
            continue
        if re.match(r"^(-|\*|\d+\.)\s+", stripped) or any(keyword in stripped for keyword in ["요구사항", "기능", "학습 목표", "목표"]):
            requirement_lines.append(_clip(stripped, limit=180))
        if len(summary_lines) < 8 and len(stripped) <= 180:
            summary_lines.append(stripped)

    keyword_counter: Counter[str] = Counter()
    for line in headings + requirement_lines + summary_lines:
        for token in _tokenize(line):
            keyword_counter[token] += 1

    return {
        "path": str(path),
        "title": headings[0] if headings else path.name,
        "headings": headings[:8],
        "summary_lines": summary_lines[:8],
        "requirement_lines": [line for line in requirement_lines[:10] if line],
        "keywords": [token for token, _ in keyword_counter.most_common(12)],
    }


def _layer_paths(repo_path: Path, files: list[Path]) -> dict[str, list[str]]:
    buckets: dict[str, Counter[str]] = {layer: Counter() for layer in LAYER_RULES}
    for path in files:
        rel = path.relative_to(repo_path).as_posix()
        lowered = rel.lower()
        for layer, keywords in LAYER_RULES.items():
            if any(f"/{keyword}/" in f"/{lowered}/" or lowered.endswith(f"/{keyword}") or keyword in lowered.split("/") for keyword in keywords):
                buckets[layer][rel] += 1

    return {
        layer: [path for path, _ in counter.most_common(6)]
        for layer, counter in buckets.items()
        if counter
    }


def _entry_points(repo_path: Path, files: list[Path]) -> list[str]:
    entries = []
    for path in files:
        rel = path.relative_to(repo_path).as_posix()
        name = path.name.lower()
        if name in {"app.tsx", "main.ts", "main.tsx", "index.tsx"}:
            entries.append(rel)
            continue
        if name.endswith("application.java") or name == "application.java":
            entries.append(rel)
            continue
        if path.suffix.lower() in {".java", ".kt"}:
            text = _read_text(path)
            if "public static void main" in text or "@springbootapplication" in text.lower():
                entries.append(rel)
                continue
    return entries[:8]


def _file_counts(files: list[Path]) -> dict:
    source_files = 0
    test_files = 0
    docs_files = 0
    for path in files:
        lower = path.as_posix().lower()
        if "/src/test/" in lower:
            test_files += 1
        elif "/src/" in lower:
            source_files += 1
        if path.suffix.lower() in {".md", ".adoc"}:
            docs_files += 1
    return {
        "tracked_files": len(files),
        "source_files": source_files,
        "test_files": test_files,
        "docs_files": docs_files,
    }


def _mission_kind(build_tool: str | None, dependency_signals: list[str], layer_paths: dict[str, list[str]]) -> str:
    deps = set(dependency_signals)
    if any(dep in deps for dep in {"react", "next", "vite"}):
        return "frontend"
    if build_tool in {"gradle", "maven"}:
        if "presentation" in layer_paths and any("controller" in path.lower() for path in layer_paths.get("presentation", [])):
            if any(dep in deps for dep in {"spring-boot-starter-web", "spring-web"}):
                return "backend-web"
            return "backend-console"
        return "backend"
    if build_tool == "npm":
        return "frontend"
    if build_tool == "python":
        return "python-app"
    return "unknown"


def _concern_candidates(
    readme_keywords: list[str],
    layer_paths: dict[str, list[str]],
    dependency_signals: list[str],
    diff_files: list[str],
) -> list[dict]:
    layer_text = " ".join(path.lower() for paths in layer_paths.values() for path in paths)
    diff_text = " ".join(diff_files).lower()
    readme_text = " ".join(readme_keywords)
    dependency_text = " ".join(dependency_signals)
    candidates = []

    for rule in CONCERN_RULES:
        score = 0
        reasons = []
        matched_keywords = []
        for keyword in rule["keywords"]:
            matched = False
            if keyword in readme_text:
                score += 3
                reasons.append(f"readme:{keyword}")
                matched = True
            if keyword in layer_text:
                score += 4
                reasons.append(f"path:{keyword}")
                matched = True
            if keyword in dependency_text:
                score += 2
                reasons.append(f"dependency:{keyword}")
                matched = True
            if keyword in diff_text:
                score += 2
                reasons.append(f"diff:{keyword}")
                matched = True
            if matched and keyword not in matched_keywords:
                matched_keywords.append(keyword)
        if score <= 0:
            continue
        query = matched_keywords[0] if matched_keywords else rule["fallback_query"]
        candidates.append({
            "id": rule["id"],
            "topic": rule["label"],
            "query": query,
            "keywords": matched_keywords[:6] or [rule["fallback_query"]],
            "score": score,
            "reasons": reasons[:8],
        })

    candidates.sort(key=lambda item: (-item["score"], item["topic"]))
    return candidates


def _retrieval_terms(repo: dict, readme_keywords: list[str], concern_candidates: list[dict]) -> list[str]:
    counter: Counter[str] = Counter()
    for raw in [repo.get("name"), repo.get("mission"), repo.get("title_contains"), repo.get("branch_hint")]:
        for token in _tokenize(raw):
            counter[token] += 3
    for token in readme_keywords:
        counter[token] += 2
    for candidate in concern_candidates:
        for keyword in candidate.get("keywords", []):
            counter[keyword] += 2
        query = candidate.get("query")
        if query:
            counter[query] += 2
    return [token for token, _ in counter.most_common(16)]


def _retrieval_path_hints(layer_paths: dict[str, list[str]], source_roots: list[str], test_roots: list[str]) -> list[str]:
    hints = []
    for paths in layer_paths.values():
        hints.extend(paths[:2])
    hints.extend(source_roots[:3])
    hints.extend(test_roots[:2])
    unique = []
    seen = set()
    for hint in hints:
        if hint in seen:
            continue
        seen.add(hint)
        unique.append(hint)
    return unique[:12]


def _compact_summary(mission_kind: str, build_tool: str | None, primary_language: str | None, concern_candidates: list[dict], readme_analysis: dict) -> list[str]:
    summary = []
    if mission_kind != "unknown":
        summary.append(f"mission kind: {mission_kind}")
    if build_tool or primary_language:
        summary.append(f"build={build_tool or 'unknown'}, language={primary_language or 'unknown'}")
    if concern_candidates:
        summary.append("primary concerns: " + ", ".join(candidate["topic"] for candidate in concern_candidates[:3]))
    if readme_analysis.get("title"):
        summary.append(f"readme: {readme_analysis['title']}")
    if readme_analysis.get("requirement_lines"):
        summary.append(f"requirement hint: {readme_analysis['requirement_lines'][0]}")
    return summary[:5]


def _relative_paths(repo_path: Path, files: list[Path], limit: int = 8) -> list[str]:
    return [path.relative_to(repo_path).as_posix() for path in files[:limit]]


def build_mission_map(repo: dict) -> dict:
    repo_name = repo["name"]
    repo_path = Path(repo["path"]).resolve()
    files = sorted(_repo_files(repo_path))
    build_files = _build_files(repo_path)
    build_tool = _primary_build_tool(build_files)
    language_counts = _language_counts(files)
    primary_language = Counter(language_counts).most_common(1)[0][0] if language_counts else None
    source_roots, test_roots = _source_and_test_roots(repo_path, files)
    package_roots = _package_roots(repo_path, files)
    readme_analysis = _readme_analysis(repo_path)
    layer_paths = _layer_paths(repo_path, files)
    dependency_signals = _dependency_signals(repo_path, build_files)
    git_context = read_git_context(repo_path)
    current_pr = read_current_pr(repo_path)
    concern_candidates = _concern_candidates(
        readme_analysis["keywords"],
        layer_paths,
        dependency_signals,
        git_context["diff_files"],
    )
    mission_kind = _mission_kind(build_tool, dependency_signals, layer_paths)
    retrieval_terms = _retrieval_terms(repo, readme_analysis["keywords"], concern_candidates)
    retrieval_path_hints = _retrieval_path_hints(layer_paths, source_roots, test_roots)

    payload = {
        "report_type": "mission_map",
        "repo": repo_name,
        "repo_path": str(repo_path),
        "generated_at": _timestamp(),
        "mission_hints": {
            "upstream": repo.get("upstream"),
            "track": repo.get("track"),
            "mission": repo.get("mission"),
            "title_contains": repo.get("title_contains"),
            "branch_hint": repo.get("branch_hint"),
            "current_pr_title": repo.get("current_pr_title"),
        },
        "repo_fingerprint": {
            "build_files": _relative_paths(repo_path, build_files, limit=6),
            "build_tool": build_tool,
            "primary_language": primary_language,
            "language_counts": language_counts,
            "source_roots": source_roots,
            "test_roots": test_roots,
            "package_roots": package_roots,
            "top_level_entries": _top_level_entries(repo_path, files),
            "file_counts": _file_counts(files),
            "entry_points": _entry_points(repo_path, files),
        },
        "readme_analysis": readme_analysis,
        "codebase_analysis": {
            "layer_paths": layer_paths,
            "dependency_signals": dependency_signals,
            "current_branch": git_context.get("branch"),
            "current_pr": current_pr,
            "current_diff_files": git_context.get("diff_files", [])[:12],
            "status_lines": git_context.get("status_lines", [])[:12],
        },
        "analysis": {
            "mission_kind": mission_kind,
            "primary_concerns": [item["topic"] for item in concern_candidates[:4]],
            "secondary_concerns": [item["topic"] for item in concern_candidates[4:8]],
            "likely_review_topics": concern_candidates[:6],
            "retrieval_terms": retrieval_terms,
            "retrieval_path_hints": retrieval_path_hints,
            "coaching_notes": [
                "Start from mission-map before opening large packets when this repo is newly onboarded.",
                "Use likely_review_topics as fallback topic candidates when prompt-only inference is weak.",
                "Prefer retrieval_path_hints over generic top-level paths when mapping evidence back to code.",
            ],
        },
        "summary": _compact_summary(mission_kind, build_tool, primary_language, concern_candidates, readme_analysis),
    }
    validate_payload("mission-map", payload)
    return payload


def write_mission_map(repo: dict) -> dict:
    payload = build_mission_map(repo)
    path = repo_analysis_dir(repo["name"]) / "mission-map.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["json_path"] = str(path)
    return payload
