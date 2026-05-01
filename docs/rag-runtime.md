# RAG Runtime Notes

대화형 학습 세션에서 CS RAG 코퍼스를 호출할 때 알아야 할 운영 사실들. 라우터 설계는 `interactive_rag_router.py`, 호출 wrapper는 `bin/rag-ask`.

## HF_HUB_OFFLINE

Full 모드(Tier 2) 첫 호출이 느린 이유는 LanceDB v3 production runtime이
BGE-M3 query encoder와 cross-encoder reranker를 로드하고, HuggingFace Hub에
모델 메타데이터 요청을 보낼 수 있기 때문이다. 모델 weights가 로컬 캐시에
있으면 다음 환경 변수로 네트워크 확인을 차단할 수 있다:

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
| R3 full, local daemon | 2.4-2.7s | first daemon request 15-24s | first daemon request 18-25s |

cheap 모드는 ML 의존성을 안 타므로 (FTS BM25만) 네트워크/캐시 상태와 무관.

full 모드는 첫 호출 시 BGE-M3 query encoder + cross-encoder reranker를
로드한다. 이후 같은 프로세스 안에서는 module-level cache로 재사용한다.

## R3 Local Daemon

R3 full 모드는 `BAAI/bge-m3` query encoder와
`BAAI/bge-reranker-v2-m3` cross-encoder를 모두 쓰므로, 매번 새 Python
프로세스로 `bin/rag-ask`를 실행하면 모델 로드가 반복된다. R3 실사용
프로파일은 장기 프로세스를 기준으로 봐야 한다.

```bash
bin/rag-daemon start
bin/rag-ask "RAG로 깊게 latency가 뭐야?" --rag-backend r3 --via-daemon
bin/rag-daemon stop
```

2026-05-01 R3 프로파일:

- one-shot full: 23.34s wall, `hits.meta.latency_ms=22162`
- same-process warm full with 50-pair rerank: 6.1-6.9s
- daemon full with 50-pair rerank: first request 18.9s, warm requests 6.2-6.9s
- local M5 window profile: 20-pair rerank warmed at about 3.4-3.8s on the
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

Therefore R3 local default rerank window is 20 pairs. 50-pair local reranking
is still available through `WOOWA_RAG_R3_LOCAL_RERANK_INPUT_WINDOW=50`, but it
is an explicit profiling/quality mode rather than the local default.

R3 remote artifacts must include `r3_lexical_sidecar.json`. The sidecar is
metadata-only by default because full-body JSON sidecars took about 60s to
cold-load locally. Body lexical recall stays on Lance FTS/query prefetch;
sidecar candidates use `lexical_sidecar:*` provenance and lower fusion weights
so corpus metadata can add recall without replacing richer body-bearing
candidates before reranking.

Production default runtime modalities are `fts,dense,sparse`. Sparse is
default-on after the 2026-05-01 decision; the next gate is explicit sparse
bottleneck/effect analysis before any category-gated sparse or weight
reduction.

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
