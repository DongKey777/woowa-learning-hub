# Source Priority and Citation

> 한 줄 요약: 질문 유형마다 먼저 볼 문서와 마지막에 인용할 문서를 나눠야 RAG가 덜 흔들린다.

관련 문서:

- [RAG Design](./README.md)
- [RAG Ready Checklist](../RAG-READY.md)
- [Chunking and Metadata](./chunking-and-metadata.md)
- [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
- [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
- [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)
- [Retrieval Failure Modes](./retrieval-failure-modes.md)
- [Security README](../contents/security/README.md)

**난이도: 🟢 Beginner**

retrieval-anchor-keywords: source priority, citation guide, citation policy, evidence ranking, primary source, secondary source, tertiary source, citation trace, response hints citation markdown, pasted reference block, bucket trace, why this citation, queue-governor, duplicate enqueue, same bucket different category, alias-query-overlap, contextual-prefix-format, release-stop, pilot_50_untouched, concept_id_unique, 뭐예요, basics

## 우선순위 원칙

이 저장소는 문서 성격이 뚜렷하다. 따라서 검색 우선순위도 문서 타입별로 나눈다.

### 1차 소스

- `README.md`
- `JUNIOR-BACKEND-ROADMAP.md`
- `ADVANCED-BACKEND-ROADMAP.md`
- `SENIOR-QUESTIONS.md`
- `contents/*/README.md`

이들은 "어디를 봐야 하는지"를 알려준다.

### 2차 소스

- `contents/**/deep dive` 문서
- `contents/**/qa` 섹션
- `contents/**/README.md`의 상세 항목

이들은 "무엇이 맞는지"를 설명한다.

### 3차 소스

- `code/`
- `materials/`
- `img/`

이들은 설명 보강용이다. 답변 본문보다 증거로 쓰는 편이 낫다.
`img/`, `code/`, local HTML `src` / `href` / `srcset`를 증거로 붙일 때는 path 자체가 QA에 안전한지 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)으로 먼저 확인해 두면 이후 reverse-link wave에서 덜 흔들린다.

## 질문별 우선순위

### 학습 순서 질문

1. `README.md`
2. `JUNIOR-BACKEND-ROADMAP.md`
3. `ADVANCED-BACKEND-ROADMAP.md`
4. `contents/*/README.md`

### 개념 설명 질문

1. 해당 카테고리 `README.md`
2. 심화 문서
3. 관련 `SENIOR-QUESTIONS.md` 항목
4. 필요 시 코드/자료

### 비교/트레이드오프 질문

1. 비교 대상 문서 둘 다
2. `SENIOR-QUESTIONS.md`
3. `README.md`의 카테고리 개요

### 운영/장애 질문

1. 심화 문서의 `실전 시나리오`
2. `SENIOR-QUESTIONS.md`
3. 관련 `materials/`
4. 관련 `code/`

### 증상/에러 문자열 질문

1. `rag/retrieval-anchor-keywords.md`
2. 해당 카테고리 `README.md`
3. symptom을 직접 다루는 심화 문서
4. 관련 `SENIOR-QUESTIONS.md`

## 인용 규칙

- 답변에는 가능한 한 원문 경로를 붙인다.
- 한 문단에 여러 출처를 섞지 말고, 주장마다 1차 근거를 둔다.
- 문서 간 중복이 있으면 가장 구체적인 문서를 인용한다.
- `README.md`는 요약 근거로, 심화 문서는 설명 근거로, `materials/`는 보조 근거로 쓴다.
- 증상 질의는 anchor keyword로 후보를 넓힌 뒤, 인용은 가장 구체적인 심화 문서에 고정한다.
- learner-facing `참고:` 블록은 AI가 새로 쓰기보다 `response_hints.citation_markdown`을 그대로 복사하는 것을 기본으로 본다.
- citation path는 맞는데 "왜 이 문서가 붙었는지" 설명이 필요하면 `response_hints.citation_trace[]`의 `path`, `bucket`, `score`를 먼저 보고 retrieval bucket을 확인한다.
- category가 기대한 축과 다르면 먼저 `response_hints.citation_trace[].category`로 cross-category bleed인지 확인한다. 예를 들어 spring 질문인데 `system-design` category가 먼저 나오면 citation wording보다 retrieval route를 먼저 고친다.

## citation trace를 언제 보나

짧은 mental model은 이렇다.

- `response_hints.citation_markdown` = 학습자에게 그대로 보여 줄 `참고:` 블록
- `response_hints.citation_paths` = 실제로 붙은 경로 목록
- `response_hints.citation_trace[]` = 각 경로가 어느 retrieval bucket에서 어떤 점수로 올라왔는지 설명하는 operator용 trace
- `response_hints.tier_downgrade` / `response_hints.fallback_disclaimer` = citation이 비었을 때 "검색 실패인가, corpus-gap downgrade인가"를 가르는 안전장치

특히 아래 질문 모양이면 citation trace를 먼저 보는 편이 빠르다.

| 보이는 증상 | 먼저 볼 필드 | 왜 이게 먼저인가 |
|---|---|---|
| `참고:` 경로는 맞는데 본문 톤이 어색하다 | `response_hints.citation_trace[].bucket` | 같은 path라도 learning-point bucket인지 fallback bucket인지에 따라 붙은 이유가 다르다 |
| spring 질문인데 database/system-design 문서가 먼저 붙는다 | `response_hints.citation_trace[].category` | path가 실존해도 category가 기대 축과 다르면 source priority보다 query routing 문제가 먼저다 |
| 같은 문서가 여러 bucket에서 보였는데 어떤 경로가 채택됐는지 헷갈린다 | `response_hints.citation_trace[].score` | 중복 path는 가장 강한 score/bucket 쪽이 learner-facing citation으로 남는다 |
| citation이 비어 있는데 retrieval은 돌았다고 들었다 | `response_hints.citation_markdown`, `response_hints.citation_paths`, `response_hints.tier_downgrade` | hit 없음인지, tier-0 downgrade인지 먼저 갈라야 corpus repair와 refusal handling을 섞지 않는다 |

## 자주 헷갈리는 지점

초반에 가장 많이 섞는 것은 "학습자에게 보이는 값"과 "operator가 추적하는 값"이다.

| 헷갈리는 쌍 | 먼저 이렇게 생각하면 안전하다 | 왜 자주 헷갈리나 |
|---|---|---|
| `response_hints.citation_markdown` vs `response_hints.citation_paths` | markdown은 그대로 붙일 블록, paths는 그 블록을 구성한 path 목록이다 | 둘 다 citation 결과처럼 보여서 하나만 봐도 된다고 느끼기 쉽다 |
| `response_hints.citation_paths` vs `response_hints.citation_trace[]` | paths는 최종 결과, trace는 왜 그 결과가 남았는지 설명하는 근거다 | path가 같으면 trace도 같을 것처럼 보이지만 bucket/category/score는 다를 수 있다 |
| `response_hints.citation_trace[].category` vs 문서 path 폴더명 | category는 retrieval이 본 분류 축이고, path는 저장 위치다 | helper 문서나 cross-category bridge는 path와 retrieval 축이 항상 1:1이 아니다 |
| `response_hints.tier_downgrade` vs hit miss | downgrade는 "검색했지만 corpus-grounded citation을 붙이지 않기로 결정한 상태"다 | citation이 비어 있으면 단순 miss로 오해하기 쉽다 |

## 30초 예시

예를 들어 학습자가 "`Spring bean` 질문인데 왜 system-design 문서가 참고로 붙었어요?"라고 물었다고 하자.

1. `response_hints.citation_markdown`으로 실제 learner-facing `참고:` path를 먼저 고정한다.
2. `response_hints.citation_paths`에서 그 path가 하나인지 여러 개인지 본다.
3. 같은 path에 대한 `response_hints.citation_trace[]`를 찾아 `bucket -> category -> score`를 읽는다.
4. `category=system-design`이면 citation 문구를 손보기 전에 cross-category bridge나 broad helper query를 먼저 의심한다.
5. path는 맞고 `bucket=fallback`이면 corpus 자체보다 learning-point handoff가 약한지부터 본다.

## citation trace를 30초 안에 읽는 순서

operator가 "`왜 이 path가 붙었지?`"를 짧게 자를 때는 아래 순서가 가장 덜 흔들린다.

1. `response_hints.citation_markdown`이 비었는지 먼저 본다.
2. 비어 있지 않으면 `response_hints.citation_paths`가 learner-facing 결과임을 확인한다.
3. 그다음 `response_hints.citation_trace[]`에서 같은 path의 `bucket -> category -> score` 순서로 이유를 읽는다.
4. `response_hints.citation_markdown`이 비어 있으면 `response_hints.tier_downgrade`를 보고 refusal downgrade인지, 그냥 hit 없음인지 가른다.
5. downgrade였다면 `response_hints.fallback_disclaimer`를 learner-facing 첫 줄로 쓰고, `참고:` 블록은 붙이지 않는다.

짧은 판단표는 이렇게 외우면 된다.

| 먼저 볼 것 | 질문 | 다음 액션 |
|---|---|---|
| `response_hints.citation_markdown` | learner에게 붙일 `참고:`가 실제로 있나 | 없으면 trace 해석보다 downgrade/hit-miss 분기를 먼저 탄다 |
| `response_hints.citation_paths` | 어떤 path가 최종 learner-facing citation으로 채택됐나 | path 집합이 맞으면 wording보다 selection 근거를 본다 |
| `response_hints.citation_trace[].bucket` | learning-point 경유인가 fallback 경유인가 | bucket이 기대와 다르면 query shape 또는 learning-point mapping을 먼저 의심한다 |
| `response_hints.citation_trace[].category` | 질문한 카테고리와 같은 축인가 | 다른 축이면 cross-domain handoff나 helper bleed를 먼저 본다 |
| `response_hints.citation_trace[].score` | 같은 path 후보 중 왜 이 경로가 남았나 | dedupe 이후 최고 score만 남는지 확인한다 |
| `response_hints.tier_downgrade` / `response_hints.fallback_disclaimer` | citation이 없는 이유가 corpus gap인가 | downgrade면 일반 지식 fallback으로 답하고, citation repair와 섞지 않는다 |

## queue-governor 질문은 citation보다 bucket triage가 먼저다

`같은 candidate가 계속 생겨요`, `이거 새 후보로 올려야 해요` 같은 질문은 citation wording보다 queue 분류가 먼저다.
이때는 `response_hints.citation_trace[]`만 길게 읽기보다 아래 순서로 자르는 편이 duplicate enqueue를 덜 만든다.

1. learner-facing failure가 기존 item과 같은지 본다.
2. `response_hints.citation_trace[].category`가 정말 다른 검증 축을 가리키는지 본다.
3. 그래도 다르면 `bucket + category + differentiator`를 적고, differentiator가 비면 새 후보를 만들지 않는다.

짧게 말하면 citation trace는 "왜 이 path가 붙었는가"를 설명하는 도구이고,
queue-governor는 "왜 이 후보를 또 만들 필요가 없는가"를 먼저 설명해야 한다.
그래서 queue wave에서는 [Query Playbook](./query-playbook.md)과 [Retrieval Failure Modes](./retrieval-failure-modes.md)의 canonical bucket 이름을 먼저 고정한 뒤,
정말 다른 category 검증 축일 때만 새 candidate로 승격하는 편이 안전하다.

특히 citation trace를 읽다가 broad label을 새로 만들지 않는 것이 중요하다.
`frontmatter debt`, `metadata issue`처럼 넓은 이름으로 다시 부르면 같은 실패가 다른 후보처럼 재등록되기 쉽다.

| citation / queue에서 먼저 보이는 신호 | 그대로 붙일 canonical bucket | 왜 broad label로 낮추지 않나 |
|---|---|---|
| `aliases`와 `expected_queries`가 같은 문장을 반복한다 | `alias-query-overlap` | alias 확장과 qrel seed repair를 분리하지 않으면 같은 learner-facing 실패가 generic frontmatter debt로 다시 부풀어 오른다 |
| `contextual_chunk_prefix`가 비었거나 질문 모양이 약하다 | `contextual-prefix-format` | prefix 문맥 부족은 path typo와 다른 검색 실패라서 citation wording 문제로 축소하면 안 된다 |
| Pilot source와 `locked_pilot_paths.json`이 어긋난다 | `release-stop` | 이 상태는 `pilot_50_untouched` 판단 자체를 흔들어 partial release나 category split으로 숨기기 어렵다 |
| cross-category `concept_id`가 겹친다 | `release-stop` | `concept_id_unique`는 chunk identity 충돌이라 일부 문서만 떼면 증상만 가리고 원인은 남는다 |

## same bucket 다른 category를 언제 split하나

queue-governor에서 citation trace category가 다르게 보여도, 바로 새 후보를 만드는 쪽이 더 위험할 때가 많다.

| 관측 상태 | enqueue 판단 | safe next step |
|---|---|---|
| 같은 bucket이고 category만 다르지만 검증 축은 같다 | split하지 않는다 | `bucket + multi-category note`로 유지하고 기존 후보 설명만 보강한다 |
| 같은 bucket이지만 category별 확인 contract가 다르다 | 그때만 split한다 | `bucket + category + differentiator`를 모두 적을 수 있을 때만 새 후보를 만든다 |
| `release-stop`인데 category별로 나눠서 빨리 처리하고 싶다 | split하지 않는다 | Pilot lock 또는 `concept_id` source를 먼저 고정하고 wave를 멈춘다 |

짧게 외우면 `same bucket + same validation axis = merge`, `release-stop = stop`이다.

## 추천 인용 문구 패턴

```markdown
이 부분은 [인덱스와 실행 계획] (../contents/database/index-and-explain.md)와
[쿼리 튜닝 체크리스트] (../contents/database/query-tuning-checklist.md)를 같이 보면 된다.
```

## 실전 기준

- 정의를 말할 때는 index/README를 인용한다.
- 원리와 trade-off를 말할 때는 deep dive를 인용한다.
- 장애와 운영을 말할 때는 실전 시나리오와 `SENIOR-QUESTIONS.md`를 인용한다.
- 코드 조각은 설명보다 짧고 정확해야 한다. 길면 보조 링크로 넘긴다.
- repo-local `img/`·`code/`나 local HTML asset form을 근거로 인용할 때는 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md) 기준으로 target 존재 여부와 filename hygiene를 먼저 고정한다.

## 한 줄 정리

먼저 `README`와 로드맵으로 길을 잡고, 답의 핵심은 심화 문서에서 인용하고, 코드와 자료는 마지막 증거로 쓰는 것이 이 repo의 기본 규칙이다.
