# migration_v3_60 Runbook — Phase 8 코퍼스 v3 마이그레이션 (60-worker, ChatGPT Pro)

> 이 문서는 사용자가 codex CLI에서 `migration_v3_60 시작해`처럼 한국어
> 의도를 던졌을 때 AI 세션이 따라가는 절차다. 학습자 production은
> 영향받지 않는 무중단 흐름.

## 목적

post-9.3 cohort_eval (2026-05-05) 결과에서 가장 약한 cohort 3개를 직접
공략한다.

| Cohort | post-9.3 pass | 전략 | 워커 수 |
|---|---:|---|---:|
| mission_bridge | 83.3% | 5 미션별 mission_bridge 신규 doc 작성 | 5 |
| confusable_pairs | 90.0% | 3 카테고리별 chooser doc 작성 | 3 |
| symptom_to_cause | 93.3% | 3 카테고리별 symptom_router doc 작성 | 3 |

이 11개 Wave C writer + 11 Wave A frontmatter + 11 Wave B prefix +
13 QA + 8 RAG + 4 ops + 2 curriculum = **60 워커**.

## 사전 조건

| 항목 | 요구 |
|---|---|
| 구독 | ChatGPT Pro 이상 (Plus는 quota 한계로 30-worker 변형 추천) |
| 환경 | macOS / Linux. `python -m pytest`, `git`, `gh` 동작 |
| Python | `.venv` 활성, `pip install -e .` 완료 |
| 인덱스 | `state/cs_rag/manifest.json` 있음 (cohort_eval baseline용) |
| 디스크 | 최소 5GB 여유 (worker 출력 로그 + git diff 누적) |

## 한 줄 시작 (사용자 인터페이스)

사용자가 codex CLI에서:

> *"migration_v3_60 시작해"* 또는 *"v3 마이그레이션 60워커 시작"*

→ AI 세션이 다음 명령 자동 호출:

```bash
bin/migration-v3-60-start
```

이 wrapper가 4단계를 자동 처리:

1. **branch 격리** — `migration_v3_60-cycle-<UTCYYYYMMDDTHHMMSSZ>` 생성, `origin/main`에서 분기. main 그대로 보전.
2. **preflight 회귀** — topology + prompt rendering + Pilot lock + workers_topology 4 테스트.
3. **baseline cohort_eval** — 시작점 OVERALL 기록 (현재 측정 95.5% / 9.3 active 후 94.0%).
4. **fleet-start** — `bin/orchestrator fleet-start --profile migration_v3_60` 호출.

## 워커 토폴로지

```
60 워커
├─ 2 curriculum
│  ├─ pilot-lock-guard         (Pilot 69 docs lock 감시)
│  └─ batch-planner            (큐 enqueue, batch manifest)
├─ 11 Wave A — frontmatter authoring (1 per category)
│  └─ migration-v3-60-frontmatter-{algorithm,...,system-design}
├─ 11 Wave B — contextual_chunk_prefix authoring (1 per category)
│  └─ migration-v3-60-prefix-{...}
├─ 11 Wave C — new doc authoring (cohort 약점 직격)
│  ├─ 5 mission_bridge   (roomescape / baseball / lotto / shopping-cart / blackjack)
│  ├─ 3 chooser          (spring / database / design-pattern)
│  └─ 3 symptom_router   (database / spring / network)
├─ 13 QA — v3-specific invariant 검증
│  ├─ frontmatter-lint, pilot-lock-guard, concept-id-uniqueness
│  ├─ prefix-format, aliases-eq-disjoint, linked-paths-integrity
│  ├─ forbidden-bidirectional, doc-role-coverage, symptom-completeness
│  ├─ mission-id-coverage, confusable-pair-symmetry
│  └─ prerequisite-graph, next-doc-graph
├─ 8 RAG — eval gate + recalibration
│  ├─ cohort-eval-gate (singleton, 94.0% baseline 가드)
│  ├─ golden-mutator, signal-rules-mutator (singleton)
│  ├─ refusal-threshold-recalibrate, citation-trace-validate
│  └─ index-smoke, paraphrase-robustness, confusable-disambiguation
└─ 4 ops
   ├─ batch-release, index-rebuild-trigger
   └─ queue-governor, rollback-handler
```

## 동작 원리

### 워커 prompt — v3-aware

`scripts/workbench/core/orchestrator_workers.py:_worker_prompt`는 mode가
`migrate_v0_to_v3` / `migrate_prefix` / `migrate_new_doc` 일 때 legacy
expansion prompt 대신 `_build_migration_v3_prompt()`로 분기한다. 이
prompt는 명시적으로:

- `docs/worklogs/rag-r3-corpus-v3-contract.md`의 18-field 계약 인용
- `config/migration_v3/locked_pilot_paths.json` Pilot lock 강제
- `corpus_lint --strict --strict-v3` 통과 요구
- `aliases ⊥ expected_queries` 불변
- doc_role별 작성 톤 가이드 (Wave B prefix 모드에서)
- 신규 doc 3가지 doc_role 구조 (Wave C 모드에서)

회귀 테스트 `tests/unit/test_migration_v3_prompt_rendering.py`가 prompt
가 v3 키워드를 가지고 legacy lint 호출이 안 들어 있음을 검증한다.

### 무중단 — 학습자 production 영향 0

```
사용자가 migration_v3_60 작업 중:
  branch:        migration_v3_60-cycle-...   ← worker 작업 여기
  main:          그대로                       ← 학습자 production
  state/cs_rag:  그대로                       ← 학습자 인덱스 (gitignored)
  config/rag_models.json (release tag): 그대로 ← bin/cs-index-build already_current
```

- 학습자가 `bin/rag-ask`로 질문 → main의 `state/cs_rag` 그대로 사용 →
  답변 영향 0.
- 학습자가 `bin/cs-index-build` 호출 → release tag sha256 비교 →
  `already_current` → 다운로드 ❌.
- migration이 끝나고 사용자가 main에 merge하면 *코드*는 들어오지만
  *인덱스*는 release publish 전엔 갱신 안 됨.

→ 학습자가 새 corpus를 받으려면 **release publish가 명시적으로 일어나야** 함
(다음 §6 참조).

### Pilot lock — 95.5%/94.0% baseline 보호

`config/migration_v3/locked_pilot_paths.json`에 69 v3 docs (Pilot 50 +
Phase 4 wave) 등록됨. 워커가 이 docs를 changed_files에 포함시키면
`_run_completion_gates`가 fail-fast — subprocess 안 띄우고 즉시
backlog 복귀.

테스트 `tests/unit/test_migration_v3_pilot_lock.py`가 이 동작을 가드.

## 모니터링

```bash
# 활성 워커 + 대기 큐
bin/orchestrator fleet-status --profile migration_v3_60

# 큐 상세
bin/orchestrator queue --profile migration_v3_60

# 워커별 로그
ls state/orchestrator/workers/migration-v3-60-*/log.jsonl
```

워커 log entry에 `token_usage`가 기록됨 — Pro quota 소진율 추적용.

## Wave 진행 권장 순서

각 wave 끝에 cohort_eval 회귀 검사. OVERALL이 94.0% - 1pp = 93.0%
이하로 떨어지면 **즉시 fleet-stop + 진단**.

```
Wave A — frontmatter (deterministic baseline + LLM authorial fields)
  algorithm (85 docs)         ← 가장 작은 카테고리, 1번 시범
  data-structure (193)
  ... 11 카테고리
  Wave A 끝나고 cohort_eval
        ↓
Wave B — contextual_chunk_prefix (LLM authoring)
  같은 순서
  Wave B 끝나고 cohort_eval (큰 향상 기대 — Pilot 41 prefix가 +35.5pp 만들었음)
        ↓
Wave C — 신규 doc (cohort 약점 직격, 토큰 가장 많이 듦)
  mission_bridge × 5 → mission_bridge cohort 회복
  chooser × 3 → confusable_pairs cohort 회복
  symptom_router × 3 → symptom_to_cause cohort 회복
  Wave C 끝나고 최종 cohort_eval
```

## 중단 / 회수

```bash
# graceful — 진행 중인 worker는 끝까지 가고, 새 claim 안 함
bin/orchestrator fleet-stop --profile migration_v3_60

# 강제 종료 — kill -9
bin/orchestrator fleet-stop --profile migration_v3_60 --force

# 작업 초기화 — branch 자체 폐기
git checkout main
git branch -D migration_v3_60-cycle-<날짜>
```

## §6 — Release publish (wave 완료 후)

cohort_eval이 안정화되면 인덱스 재빌드 + release 갱신:

```bash
# 1. main에 merge
git checkout main
git merge --no-ff migration_v3_60-cycle-<날짜>

# 2. RunPod에서 인덱스 재빌드 (5-10분 + 모델 다운로드)
.venv/bin/python -m scripts.remote.runpod_rag_full_build \
    --corpus-root knowledge/cs/contents \
    --output state/cs_rag

# 3. tar.zst 압축 + sha256 + upload
.venv/bin/python -m scripts.remote.publish_index_release \
    --tag "index-v1.0.0-corpus@$(git rev-parse --short HEAD)"

# 4. config/rag_models.json의 release 블록 갱신 (자동)
# 5. config 커밋 + push
git add config/rag_models.json
git commit -m "release: index-v1.0.0-corpus@<sha>"
git push origin main

# → 학습자 다음 bin/cs-index-build 호출에서 새 release 다운로드 (자동, ~30초)
```

## 비상 — fleet 시작 전 점검

```bash
# 사전 회귀 (wrapper가 자동 호출하지만 수동 검증 가능)
.venv/bin/python -m pytest \
    tests/unit/test_migration_v3_60_topology.py \
    tests/unit/test_migration_v3_prompt_rendering.py \
    tests/unit/test_migration_v3_workers_topology.py \
    tests/unit/test_migration_v3_pilot_lock.py \
    tests/unit/test_create_v3_frontmatter.py \
    tests/unit/test_synthesize_chunk_prefix.py -q

# Pilot lock 무결성
jq '.locked_count, (.locked_paths | length)' config/migration_v3/locked_pilot_paths.json
# 두 숫자 같아야 함
```

## 참고

- 코드: `scripts/workbench/core/orchestrator_migration_workers.py:MIGRATION_V3_60_FLEET`
- prompt: `scripts/workbench/core/orchestrator_workers.py:_build_migration_v3_prompt`
- v3 contract spec: `docs/worklogs/rag-r3-corpus-v3-contract.md`
- baseline 측정: `reports/rag_eval/post_phase_9_3_active.json`
- Pilot lock: `config/migration_v3/locked_pilot_paths.json`
