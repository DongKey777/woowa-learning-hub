# RAG Runtime Notes

대화형 학습 세션에서 CS RAG 코퍼스를 호출할 때 알아야 할 운영 사실들. 라우터 설계는 `interactive_rag_router.py`, 호출 wrapper는 `bin/rag-ask`.

## HF_HUB_OFFLINE

Full 모드(Tier 2) 첫 호출이 느린 이유는 R3 production runtime이 BGE-M3
query encoder, dense/sparse sidecar metadata, 그리고 정책상 필요할 때
cross-encoder reranker를 로드하고, HuggingFace Hub에 모델 메타데이터 요청을
보낼 수 있기 때문이다. 모델 weights가 로컬 캐시에 있으면 다음 환경 변수로
네트워크 확인을 차단할 수 있다:

```bash
export HF_HUB_OFFLINE=1
```

2026-05-01 sparse-default smoke에서 `HF_HUB_OFFLINE=1` 기준 cold start는
약 10.0초였고, warm P95는 약 524ms였다. 오프라인 모드에서는 네트워크 확인
지연이 사라진다.

세션 시작 시 한 번 export하거나 `~/.zshrc` / `~/.bashrc`에 영구 등록 권장. 모델 업데이트가 필요할 때만 일시적으로 unset.

## Latency 가정

| Mode | Warm | Cold (offline=1) | Cold (online) |
|------|------|------------------|---------------|
| cheap | 50-200ms | 50-200ms | 50-200ms |
| Lance full | 500ms-2s | 2-8s | 10-25s |
| R3 full, one-shot CLI | 2.3-3.0s after OS cache | 15-24s | 18-25s |
| R3 full, local daemon, auto sidecar default | about 1.2s on current artifact | first daemon request 18-20s | first daemon request 18-25s |
| R3 full, forced BGE reranker direct | about 25s one-shot on current artifact | first daemon request 15-24s | first daemon request 18-25s |

cheap 모드는 ML 의존성을 안 타므로 (FTS BM25만) 네트워크/캐시 상태와 무관.

full 모드는 첫 호출 시 BGE-M3 query encoder와 R3 sidecar를 로드한다. BGE
reranker는 `WOOWA_RAG_R3_RERANK_POLICY=always`이거나 `auto` 정책이 sidecar
skip 조건을 만족하지 못할 때 로드된다. 이후 같은 프로세스 안에서는
module-level cache로 재사용한다.

## R3 Local Daemon

R3 full 모드는 `BAAI/bge-m3` query encoder, dense/sparse/lexical candidate
discovery, metadata lexical sidecar를 쓴다. `BAAI/bge-reranker-v2-m3`
cross-encoder는 R3의 기본 품질 reranker로 유지하지만, 로컬 interactive
기본값은 검증된 lexical sidecar가 있을 때 reranker를 자동으로 건너뛰는
`auto` 정책이다. 매번 새 Python 프로세스로 `bin/rag-ask`를 실행하면 모델
로드가 반복되므로 R3 실사용 프로파일은 장기 프로세스를 기준으로 봐야 한다.

```bash
bin/rag-daemon start
bin/rag-ask "RAG로 깊게 latency가 뭐야?" --via-daemon
bin/rag-daemon stop
```

`bin/rag-ask`의 default daemon path는 startup `runtime_fingerprint`를 검사한다.
fingerprint에는 현재 git HEAD와 RAG runtime source/config hash가 들어가며,
`state/rag-daemon.json`과 `/health` 응답에 같이 기록된다. wrapper의 ensure
단계는 현재 checkout fingerprint와 running daemon fingerprint가 다르면 daemon을
자동 stop/start한다. 따라서 PR merge, local source edit, wrapper env contract
변경 뒤에도 healthy-but-stale Python process가 낡은 response contract를 계속
내보내지 못한다.

디버그/CI에서 daemon을 끄려면 wrapper opt-out을 쓴다:

```bash
WOOWA_RAG_NO_DAEMON=1 bin/rag-ask "Gradle 설정 어떻게 해?"
```

As of the 2026-05-02 R3 cutover, `auto` selects the R3 runtime when
`state/cs_rag` contains a valid `r3_lexical_sidecar.json` whose
`corpus_hash`, `row_count`, and `document_count` match the index manifest.
Use `--rag-backend lance` only for a controlled rollback comparison.

Rerank policy:

| Policy | Meaning |
|---|---|
| `WOOWA_RAG_R3_RERANK_POLICY=auto` | default. Use BGE reranker unless the verified metadata lexical sidecar is loaded; with sidecar, skip cross-encoder reranking for local interactive latency. |
| `WOOWA_RAG_R3_RERANK_POLICY=always` | force `BAAI/bge-reranker-v2-m3` for quality experiments or suspected ranking failures. |
| `WOOWA_RAG_R3_RERANK_POLICY=off` | disable reranking for controlled candidate-discovery or latency-only runs. |

2026-05-01 R3 프로파일:

- one-shot full: 23.34s wall, `hits.meta.latency_ms=22162`
- same-process warm full with 50-pair rerank: 6.1-6.9s
- daemon full with 50-pair rerank: first request 18.9s, warm requests 6.2-6.9s
- local M4 window profile: 20-pair rerank warmed at about 3.4-3.8s on the
  three mixed Korean/English smoke prompts
- 100q Corpus v2 gate with 20-pair local rerank preserved
  `final_hit_relevant@5=1.0`, `forbidden_rate@5=0`, and
  `lost_top20_rate=0`
- 2026-05-01 sparse retriever cache profile: daemon warm full latency improved
  to `hits.meta.latency_ms=2401-2605` on the two post-warm mixed prompts;
  `r3_stage_ms` now reports query encoding, candidate retrieval, fusion, and
  reranker timing.
- 2026-05-01 lexical sidecar gate: remote-prebuilt metadata lexical sidecar
  (`title`, `section`, `aliases`; no body terms) is 26,966,603 bytes for
  27,170 chunks. Cold local load was about 4.25s; warm sidecar load is
  effectively cached. The 100q window-20 reranker gate stayed green:
  `final_hit_relevant@5=1.0`, Korean-only `=1.0`, mixed Korean/English `=1.0`,
  `forbidden_rate@5=0`, `lost_top20_rate=0`.
- 2026-05-01 daemon sidecar smoke: first sidecar-enabled daemon request was
  18.33s; warm requests were 2.65-2.68s. Warm sidecar load was under 0.2ms;
  the dominant warm stage remained cross-encoder reranking at about 2.0s.
- 2026-05-01 auto rerank policy gate: with `use_reranker=null`, policy `auto`,
  and the metadata lexical sidecar present, all 100 qrels used
  `policy_auto_sidecar_first_stage_gate`, no rerank stage ran, and
  `final_hit_relevant@5=1.0` overall, Korean-only, and mixed Korean/English.
  The learner-facing daemon smoke showed 12.30s for the first request and
  476ms for the warm request, with runtime JSON exposing policy, skip reason,
  sidecar presence, and stage timing.
- 2026-05-02 final R3 selection:
  `r3-61216f2-2026-05-02T0937` is the selected remote-built index artifact:
  remote-built on RunPod, imported into local `state/cs_rag`, `row_count=27158`,
  `corpus_hash=c002a92b2b97033d5ff3f0a9c94d3c952586107337e3a07cd66e9c943643cacb`,
  and strict R3 verified with `--verify-import`. The runtime commit
  `788ee99e67b7131e647684592d53bd268eef93f0` serves this index with fusion v2.
  The final 208q production gate
  `reports/rag_eval/r3_backend_compare_208q_production_r3_auto_20260502T1052Z.summary.json`
  reports candidate and final primary/relevant hit/recall at 5/20/50/100 as
  `1.0` overall, Korean, and mixed, with `forbidden_rate@5=0`. Local smoke
  `reports/rag_eval/r3_61216f2_runtime_788ee99_local_smoke_20260502T1059Z.json`
  returned 1020ms for the second warm daemon full request. A forced direct
  `BAAI/bge-reranker-v2-m3` run verified the quality path, with 28067ms total
  latency and 6304.254ms rerank time for 20 pairs.
- 2026-05-02 rollback refresh:
  `state/cs_rag_archive/v2_current_20260502T1101Z` is the current-corpus legacy
  v2 MiniLM + SQLite/NPZ rollback index. Smoke report
  `reports/rag_eval/r3_legacy_rollback_current_corpus_smoke_20260502T1104Z.json`
  shows `indexer.is_ready()` as `ready`. The older
  `state/cs_rag_archive/v2_20260501T063445Z` remains preserved for historical
  comparison but is stale against the expanded corpus.

Therefore R3 local default rerank policy is `auto`; the local default rerank
window remains 20 pairs when reranking is forced or when the sidecar is absent.
50-pair local reranking is still available through
`WOOWA_RAG_R3_LOCAL_RERANK_INPUT_WINDOW=50`, but it is an explicit
profiling/quality mode rather than the local default.

R3 remote artifacts must include `r3_lexical_sidecar.json`. The sidecar is
metadata-only by default because full-body JSON sidecars took about 60s to
cold-load locally. Body lexical recall stays on Lance FTS/query prefetch;
sidecar candidates use `lexical_sidecar:*` provenance and lower fusion weights
so corpus metadata can add recall without replacing richer body-bearing
candidates before reranking.

Production default backend is R3 over the LanceDB v3 storage artifact, with
runtime modalities `fts,dense,sparse`. Sparse is a first-stage R3 signal when
full mode encodes BGE-M3 query sparse terms; cheap mode stays lexical-only.

## Index Manifest

`state/cs_rag/manifest.json` 필드:

| 필드 | 의미 |
|------|------|
| `index_version` | 인덱스 schema 버전 (현재 3). v2는 legacy archive 전용 |
| `corpus_hash` | corpus 파일 변경 감지용 해시 |
| `row_count` | chunk 개수 |
| `encoder.model_id` | 임베딩 모델 이름 (`BAAI/bge-m3`) |
| `encoder.model_version` | pinned model revision |
| `modalities` | index에 저장된 modality (`fts,dense,sparse`) |
| `lancedb.indices` | LanceDB dense/FTS/ColBERT index metadata |
| `corpus_root` | 코퍼스 루트 절대경로 |

**주의**: `schema_version`은 잘못된 표기다. 실제 필드명은 `index_version`.
Legacy v2 archive는 `state/cs_rag_archive/v2_20260501T063445Z`에 보존되어
있고 rollback 전용이다.

## bin/rag-ask 사용

```bash
# 단순 질문 — Tier 0/1/2 자동 라우팅
bin/rag-ask "Spring Bean이 뭐야?"

# 코칭 모드 시도 — repo 명시 필요
bin/rag-ask "내 PR 리뷰해줘" --repo spring-roomescape-admin
```

출력은 한 줄 JSON:

```json
{
  "decision": {"tier": 1, "mode": "cheap", "reason": "domain + definition signal",
               "experience_level": "beginner", "override_active": false, "blocked": false},
  "hits": { "by_fallback_key": {...}, "meta": {"latency_ms": 111} },
  "next_command": null
}
```

- `decision.tier` 0/1/2/3 (각각 skip/cheap/full/coach-run)
- `decision.blocked=true`면 코칭 요청이 repo/PR 부재로 실행 불가
- `hits`는 Tier 1/2일 때만 채워짐
- `next_command`는 Tier 3 ready일 때만 채워짐 (`bin/coach-run` 호출 명령)
- `--reformulated-query`는 검색 품질뿐 아니라 routing rescue에도 사용됨.
  raw prompt의 override/tool-only/coach 판단은 유지하되, domain/depth/definition
  감지는 raw prompt와 reformulated query를 함께 본다.

## Tier 분류 빠른 참조

| 입력 패턴 | 예시 | Tier | 호출 |
|-----------|------|------|------|
| 도구/빌드 키워드 | "Gradle 멀티 프로젝트 어떻게?" | 0 | (없음) |
| CS/학습 도메인 + 정의 시그널 | "Spring Bean이 뭐야?" | 1 | `augment(cheap)` |
| CS/학습 도메인 + 깊이 시그널 | "DI vs Service Locator 차이" | 2 | `augment(full)` |
| 코칭 요청 (multi-word) + repo ready | "내 PR 리뷰해줘" + onboarded | 3 | `bin/coach-run` |
| 도메인 매치 없음 | "오늘 점심 왜 없어?" | 0 | (없음) |

## Override 키워드

학습자가 라우터 결정을 강제할 때 프롬프트에 다음 표현 포함:

| 표현 | 효과 |
|------|------|
| `RAG로 깊게`, `심도 있게` | Tier 2 강제 |
| `RAG로 답해`, `근거 보여줘` | 최소 Tier 1 강제 |
| `그냥 답해`, `RAG 빼고` | Tier 0 강제 |
| `코치 모드` | Tier 3 시도 (repo/PR 미준비면 blocked) |

## 인덱스 stale 감지

`bin/rag-ask` 호출 시 `corpus_hash` 자동 비교. 코퍼스 변경 시
`cs_readiness.state != "ready"`가 되며, CS-only 요청은 AI 세션이
`bin/cs-index-build`를 자동 실행한 뒤 다시 호출한다. R2 cutover 이후
`bin/cs-index-build` 기본 backend는 LanceDB v3이다. Legacy는 rollback
검증 때만 명시적으로 사용한다:

```bash
bin/cs-index-build
bin/cs-index-build --backend legacy --mode full  # rollback/manual v2 only
```

Lance full rebuild는 로컬 CPU에서 오래 걸릴 수 있으므로 큰 코퍼스 재빌드는
remote GPU runbook을 우선 사용한다. 출력 끝 라인의 `corpus_hash`가
manifest와 일치하면 정상.
