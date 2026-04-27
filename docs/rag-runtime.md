# RAG Runtime Notes

대화형 학습 세션에서 CS RAG 코퍼스를 호출할 때 알아야 할 운영 사실들. 라우터 설계는 `interactive_rag_router.py`, 호출 wrapper는 `bin/rag-ask`.

## HF_HUB_OFFLINE

Full 모드(Tier 2) 첫 호출이 5–10초 걸리는 이유는 sentence-transformers가 HuggingFace Hub에 모델 메타데이터 HEAD 요청을 보내고, 네트워크 응답이 늦으면 재시도하기 때문이다. 모델 weights는 이미 `~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/`에 캐시돼 있으므로 다음 환경 변수로 네트워크 호출을 차단할 수 있다:

```bash
export HF_HUB_OFFLINE=1
```

설정 후 cold path latency: ~7초 → ~500ms.

세션 시작 시 한 번 export하거나 `~/.zshrc` / `~/.bashrc`에 영구 등록 권장. 모델 업데이트가 필요할 때만 일시적으로 unset.

## Latency 가정

| Mode  | Warm     | Cold (offline=1) | Cold (online) |
|-------|----------|------------------|---------------|
| cheap | 50–200ms | 50–200ms         | 50–200ms      |
| full  | 500ms–2s | 800ms–2s         | 5–10s         |

cheap 모드는 ML 의존성을 안 타므로 (FTS BM25만) 네트워크/캐시 상태와 무관.

full 모드는 첫 호출 시 sentence-transformer + cross-encoder 두 모델을 로드. 이후 같은 프로세스 안에서는 모듈-level 캐시(`_QUERY_EMBEDDER`)로 재사용.

## Index Manifest

`state/cs_rag/manifest.json` 필드:

| 필드 | 의미 |
|------|------|
| `index_version` | 인덱스 schema 버전 (현재 2). 마이그레이션 트리거 |
| `corpus_hash` | corpus 파일 변경 감지용 해시 |
| `row_count` | chunk 개수 |
| `embed_model` | 임베딩 모델 이름 |
| `embed_dim` | 벡터 차원 (384) |
| `corpus_root` | 코퍼스 루트 절대경로 |

**주의**: `schema_version`은 잘못된 표기다. 실제 필드명은 `index_version`.

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

`bin/rag-ask` 호출 시 `corpus_hash` 자동 비교. 코퍼스 변경됐으면 별도 로그 없이 augment가 호출되지만 retrieval 품질 저하 가능. 정기 재빌드:

```bash
bin/cs-index-build
```

87초 정도 소요 (cold). 출력 끝 라인의 `corpus_hash`가 manifest와 일치하면 정상.
