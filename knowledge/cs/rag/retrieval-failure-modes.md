# Retrieval Failure Modes

> 한 줄 요약: RAG가 틀리는 방식부터 알아야 검색 품질을 복구할 수 있다.

**난이도: 🟡 Intermediate**

관련 문서:

- [RAG Design](./README.md)
- [Query Playbook](./query-playbook.md)
- [Chunking and Metadata](./chunking-and-metadata.md)
- [Source Priority and Citation](./source-priority-and-citation.md)
- [Topic Map](./topic-map.md)
- [Dual-Read Comparison / Verification Platform 설계](../contents/system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: retrieval failure modes, rag failure modes, cs-index-build stale index, helper 문서만 잡힘, citation path right but content stale, frontmatter는 붙였는데 gate에서 막혀요, 왜 새 문서가 안 잡혀요, 뭐예요, release blocker, alias query overlap, linked_paths path contract, pilot lock drift, locked_pilot_paths mismatch, release stop, queue governor dedupe

## 왜 필요한가

검색 시스템은 보통 "찾는 것"보다 "잘못 찾는 것"이 더 문제다.
이 저장소는 같은 개념이 여러 폴더에 반복되기 때문에, 잘못된 문서를 고르는 순간 답변이 흔들린다.

## 대표 실패 모드

### 1. 개념은 맞는데 층이 틀림

예:

- `Spring` 질문인데 `Java` runtime 문서만 잡는 경우
- `DB` 질문인데 `System Design`의 개략 설계만 잡는 경우

대응:

- 먼저 `contents/*/README.md`를 찾는다.
- 다음에 deep dive를 붙인다.

### 2. README만 잡고 실전 문서를 놓침

README는 길 안내다.
정답이 필요한 질문에서 README만 보면 정의는 맞아도 운영 포인트가 빠진다.

대응:

- 정의 질문: README
- 장애/운영 질문: deep dive
- 비교 질문: deep dive 2개

### 3. 여러 문서에서 같은 말을 반복하는데 서로 다른 시각임

예:

- `cache`는 `network`, `database`, `system-design`, `software-engineering`에 다 나온다.

대응:

- 문서의 시각을 메타데이터에 남긴다.
- 답변에는 시각을 섞지 않는다.

### 4. chunk가 너무 크거나 너무 작음

- 너무 크면 검색은 되는데 답변이 둔해진다.
- 너무 작으면 문맥이 사라진다.

대응:

- 기본은 `H2`
- 표/코드/SQL은 분리
- README는 짧게 유지

### 5. 파일명은 맞는데 링크가 끊김

이 repo는 상대 링크가 많아서 구조가 조금만 어긋나도 검색이 깨진다.

대응:

- 경로 기반 검증을 한다.
- 파일명 변경 시 관련 README와 rag 문서도 같이 본다.

### 6. 질문 분해가 안 됨

예:

`Spring에서 왜 느리죠?`

이 질문은 너무 넓다.

대응:

- `Spring MVC`인지 `WebFlux`인지
- `transaction`인지 `test slice`인지
- `cache`인지 `AOP`인지

로 다시 쪼갠다.

## 인덱스는 다시 만들었는데 retrieval이 여전히 옛 경로를 탐

예:

- `cs-index-build` 직후인데 새 문서가 검색 결과에 안 보이는 경우
- helper 문서만 계속 잡히고 `contents/**` handoff가 안 되는 경우
- citation 경로는 맞는데 설명 톤이 예전 구조에 묶여 보이는 경우

대응:

- 먼저 stale index인지, build 대상이 빠졌는지, helper 문서가 과노출됐는지 분리한다.
- broad helper query면 [RAG Design](./README.md)으로 돌아가 메타 문서 제외 규칙을 다시 확인한다.
- route는 맞는데 handoff가 안 되면 [Query Playbook](./query-playbook.md)과 [Topic Map](./topic-map.md)으로 query shape를 고정한다.

index smoke는 아래 셋만 먼저 가른다.

| 보이는 증상 | 먼저 고정할 분기 | safe next step |
|---|---|---|
| `cs-index-build`를 했는데 새 문서가 안 나온다 | stale index인지, build 대상 자체가 빠졌는지 | [Chunking and Metadata](./chunking-and-metadata.md) |
| 결과가 계속 `README`, `RAG-READY.md` 같은 helper로만 간다 | helper query가 broad한지, helper 제외 규칙이 깨졌는지 | [RAG Design](./README.md), [Query Playbook](./query-playbook.md) |
| citation path는 맞는데 설명이 옛 구조처럼 보인다 | source priority 역전인지, query shape가 옛 alias에 묶였는지 | [Source Priority and Citation](./source-priority-and-citation.md), [Topic Map](./topic-map.md) |

## citation trace가 붙었는데 이유가 설명되지 않음

citation mismatch를 더 짧게 자르려면 `response_hints`를 아래처럼 읽는다.

| 지금 보이는 현상 | 먼저 볼 trace | 다음 판단 |
|---|---|---|
| `참고:`에는 path가 붙었는데 "왜 이 bucket이었는지" 설명이 안 된다 | `response_hints.citation_trace[].bucket` | learning-point 유도인지 fallback 유도인지 갈라서 query shape 문제인지 corpus 분류 문제인지 먼저 자른다 |
| 질문은 spring인데 citation이 system-design/network 쪽으로 새어 보인다 | `response_hints.citation_trace[].category` | cross-category bleed인지, broad helper query인지 먼저 갈라서 source priority와 routing을 섞지 않는다 |
| 같은 path가 여러 번 검색됐는데 최종 citation은 하나만 남았다 | `response_hints.citation_trace[].score` | dedupe 자체는 정상일 수 있으니, 낮은 score bucket이 탈락한 것인지 먼저 본다 |
| citation이 비었는데 retrieval 실패인지 tier downgrade인지 헷갈린다 | `response_hints.citation_markdown`, `response_hints.tier_downgrade`, `response_hints.fallback_disclaimer` | 빈 hit인지 refusal downgrade인지 분리한 뒤 corpus repair와 fallback 응답 점검을 나눈다 |

`citation_trace`를 볼 때는 "trace가 많다"보다 "같은 path가 왜 learner-facing citation으로 남았는가"를 먼저 자르는 편이 안전하다.
즉 `bucket -> category -> score` 순서로 보면 operator 질문이 빨리 줄어든다.

## citation trace를 읽는 순서

| 읽는 순서 | 왜 이 순서가 안전한가 |
|---|---|
| `citation_markdown` / `citation_paths` | learner에게 실제로 무엇이 붙었는지부터 고정해야 trace 해석이 과잉이 되지 않는다 |
| `citation_trace[].bucket` | learning-point / fallback 어느 경로에서 붙었는지 알아야 query shape 문제와 corpus 분류 문제를 분리할 수 있다 |
| `citation_trace[].category` | 질문 축과 다른 category가 먼저 붙으면 wording보다 route가 먼저 문제다 |
| `citation_trace[].score` | dedupe 이후 최고 score가 남는 것이 정상인지 확인할 수 있다 |
| `fallback_disclaimer` | downgrade였다면 learner-facing 첫 줄이 이미 정해져 있으므로 citation repair와 응답 톤 문제를 섞지 않는다 |

`fallback_disclaimer`가 채워졌다면 그 turn은 "citation이 빠진 버그"가 아니라
"코퍼스에 신뢰할 만한 근거가 없어 일반 지식 fallback으로 내려간 turn"으로 먼저 해석하는 편이 안전하다.

## cohort eval regression을 corpus 문제로 바로 번역함

예:

- strict frontmatter blocker는 줄었는데 cohort baseline만 `94.0` 아래로 떨어진다.
- 새 doc repair는 거의 없는데 real qrels 검증 결과만 흔들린다.
- refusal threshold calibration report가 바뀌었는데 retrieval recall 회귀처럼 읽힌다.

대응:

- 먼저 `corpus doc quality`, `qrels fixture / expected_queries seed`, `baseline or calibration snapshot`을 분리한다.
- paraphrase cohort만 흔들리면 broad alias나 reformulation 축을 먼저 의심하고, 전체 corpus 품질 후퇴로 바로 확대하지 않는다.
- symptom cohort만 흔들리면 helper 문서 과노출, `retrieval-anchor-keywords`, safe-next-step handoff 약화를 먼저 본다.
- calibration report 변화는 retrieval hit 품질과 refusal cutoff 조정이 섞여 보일 수 있으니, "못 찾음"과 "찾았지만 downgrade"를 분리해서 읽는다.

cohort eval triage는 아래 세 줄로 먼저 자르면 된다.

| 보이는 현상 | 먼저 붙일 라벨 | 왜 이 라벨이 먼저인가 |
|---|---|---|
| baseline이 `94.0` 아래로 떨어졌다 | `cohort-baseline regression` | 결과 수치만으로는 corpus 문제인지 fixture drift인지 구분되지 않는다 |
| real qrels 검증만 다시 막힌다 | `qrels-seed drift` | retrieval field와 eval field가 섞였는지 먼저 봐야 같은 문서를 또 broad frontmatter debt로 묶지 않는다 |
| calibration report 변화 후 citation이 줄어 보인다 | `threshold-vs-retrieval split` | hit 부재와 downgrade 증가는 learner-facing 현상이 비슷해도 복구 축이 다르다 |

## v3 frontmatter가 "이관된 것처럼" 보이는데 release 직전에 다시 막힘

예:

- `schema_version: 3`는 붙었는데 `expected_queries`가 비어 있어서 qrel seed를 못 만든다.
- `aliases`와 `expected_queries`가 같은 문장을 반복해서 alias/query overlap gate에 걸린다.
- `linked_paths`가 `spring-foo.md` 같은 상대 경로라 corpus path contract(`contents/...`)를 못 맞춘다.
- Pilot 50 기준 문서를 건드려서 baseline 비교군이 오염된다.

대응:

- release 전에는 "frontmatter가 있느냐"보다 "eval-only field와 retrieval field가 분리됐느냐"를 먼저 본다.
- `expected_queries`는 빈 배열 금지, `aliases`와 문장 중복 금지, `linked_paths`는 `contents/<category>/<file>.md` 형식만 허용으로 본다.
- `contextual_chunk_prefix`를 override한 문서는 빈 문자열보다 문서 역할과 학습자 질문 모양이 보이는 한두 문장으로 고정한다.
- pilot cohort 문서는 migration 실험군이 아니면 수정하지 않고, non-pilot doc부터 batch로 묶는다.
- migration branch에서 corpus만 바뀐 상태라면 learner 쪽 `bin/cs-index-build`가 `already_current`를 반환해도 이상이 아니다. release tag와 `config/rag_models.json`는 publish 시점까지 그대로 두고, RunPod rebuild -> artifact verify/import -> release publish 순서가 끝나야 새 corpus가 내려간다.
- Pilot source 목록과 `locked_pilot_paths.json`이 서로 안 맞으면 "Pilot 문서를 수정했는가" 이전에 baseline 보호 범위 정의가 흔들린 상태다. 이 경우는 doc 하나를 빼는 cherry-pick보다 lock source를 먼저 다시 맞추는 편이 안전하다.

## release 직전 preflight

release 직전 preflight를 짧게 확인하려면 이 순서가 안전하다.

1. `pilot 50 untouched`인지 먼저 본다.
2. `aliases`와 `expected_queries`가 서로 다른 역할을 유지하는지 본다.
3. `linked_paths`, `concept_id`, `contextual_chunk_prefix`가 형식 계약을 지키는지 본다.
4. 그다음에야 검색 품질 자체를 의심한다.

짧은 release 체크는 아래 네 줄이면 충분하다.

```text
1. pilot 50 untouched?
2. aliases ⊥ expected_queries?
3. expected_queries / linked_paths / concept_id 형식이 비어 있거나 느슨하지 않은가?
4. contextual prefix override가 비어 있으면 이번 wave에서 채울지, auto-generation에 맡길지 명시했는가?
```

## release handoff 분기

release handoff에서는 "RunPod rebuild가 끝났는가"와 "release lock이 바뀌었는가"를 같은 질문으로 섞지 않는 편이 안전하다.

| 보이는 증상 | 먼저 확인할 것 | safe next step |
|---|---|---|
| corpus doc는 고쳤는데 learner 환경 `cs-index-build`가 `already_current`만 반환한다 | release tag가 아직 이전 artifact를 가리키는지, RunPod rebuild/publish가 아직 안 끝났는지 | migration wave에서는 문서/queue 수선만 계속하고, publish window에서만 release tag를 갱신한다 |
| RunPod build는 끝났는데 warm runtime 품질이 이상하다 | artifact에 `r3_lexical_sidecar.json`이 포함돼 있는지, verify-import가 통과했는지 | rebuild artifact contract를 다시 확인하고 publish 전에 strict import 검증을 다시 돈다 |

## hash mismatch triage

release handoff에서 특히 자주 놓치는 것은 "지금 어느 hash를 보고 있나"다.
문서 diff와 artifact 상태를 한 줄로 합치지 말고 아래처럼 나눠 보면 재빌드 트리거 판단이 빨라진다.

| 지금 비교하는 값 | 뜻 | mismatch일 때 먼저 붙일 라벨 |
|---|---|---|
| 현재 `knowledge/cs/**` 기준 corpus hash vs `state/cs_rag/manifest.json.corpus_hash` | source corpus와 local artifact가 다른지 | `source-vs-local drift` |
| `manifest.json.corpus_hash` vs `r3_lexical_sidecar.json.corpus_hash` | local artifact 내부 sidecar contract가 맞는지 | `artifact-contract drift` |
| `config/rag_models.json.release.tag` / `archive_sha256` vs learner local manifest release 정보 | learner가 여전히 이전 publish를 보고 있는지 | `release-lock unchanged` |

`already_current`는 대개 세 번째 줄이 그대로라는 뜻이지,
첫 번째 줄까지 자동으로 일치한다는 뜻은 아니다.
그래서 migration wave 중에는 `source-vs-local drift`가 보여도 바로 release bug로 번역하지 않고,
publish window가 열렸는지부터 확인하는 편이 안전하다.

## index rebuild trigger truth table

ops wave에서 가장 자주 흔들리는 질문은 "`지금 rebuild를 눌러야 하나, release tag를 바꿔야 하나`"다.
이때는 broad한 "index가 stale하다" 대신 아래 조합으로 surface를 고정하는 편이 안전하다.

| source corpus vs local artifact | release lock | 우선 판단 | 왜 이 판단이 안전한가 |
|---|---|---|---|
| 다르다 | unchanged | rebuild pending, publish 아직 아님 | `knowledge/cs/**` 변경이 local manifest나 learner release에 자동 전파되지는 않는다. RunPod rebuild와 verify/import가 먼저다. |
| 같다 | unchanged | rebuild 불필요, learner는 현재 release를 보고 있음 | 이 경우 `already_current`는 정상일 수 있고, 새 문서가 안 보이면 query shape나 helper 과노출을 먼저 본다. |
| 같다 | changed | release handoff 검증 | publish는 됐지만 warm runtime이나 import contract가 어긋났을 수 있다. `r3_lexical_sidecar.json`과 release metadata를 같이 본다. |
| 다르다 | changed | release claim 재검증 | release tag가 이미 바뀌었는데 source/local이 다시 어긋나면 artifact verify/import 누락이나 잘못된 release cut일 수 있다. |

짧은 operator 문장으로는 이렇게 자르면 된다.

- `source-vs-local drift + release-lock unchanged`면 rebuild queue 질문이다.
- `artifact-contract drift + release-lock changed`면 import/verify 질문이다.
- `release-lock changed`만 보고 publish 완료라고 말하지 않는다.

## batch release와 cherry-pick을 가르는 기준

release gate를 막는 원인이 보여도, 서로 다른 계약 위반을 한 번에 태우면 queue가 다시 꼬인다.
ops wave에서는 "몇 파일이냐"보다 "같은 failure bucket이냐"를 먼저 본다.

| 지금 보이는 blocker | release cut 판단 | 이유 |
|---|---|---|
| 같은 category에서 `linked_paths=contents/...` 정규화가 여러 문서에 반복된다 | batch release | path-normalization bucket이라 한 번에 검증하고 handoff 문구도 통일하는 편이 안전하다 |
| `expected_queries` 누락, chooser `confusable_with` 부족처럼 같은 schema 누락이 묶여 있다 | batch release | eval field를 같은 축으로 채워야 qrel seed와 qa 설명이 같이 맞는다 |
| `aliases`와 `expected_queries`가 한 문서에서만 겹치거나 `doc_role` enum typo가 1건이다 | cherry-pick | isolated fix라 queue를 크게 흔들지 않고 preflight 확인도 짧다 |
| `contextual_chunk_prefix`가 비어 있거나 질문 모양이 약한 문서가 1~2개다 | cherry-pick 또는 very small batch | retrieval quality 확인 범위가 좁아서 원인 추적이 쉽다 |
| Pilot 50 문서를 건드렸거나 `concept_id` 충돌이 카테고리를 넘는다 | release stop | partial cherry-pick으로 가리기보다 source doc를 재조정하고 다시 wave를 자르는 편이 안전하다 |
| Pilot source 목록과 `locked_pilot_paths.json`이 서로 다른 집합을 가리킨다 | release stop | lock drift 상태에서는 어떤 문서가 "Pilot untouched"인지 판정 자체가 흔들려 partial release가 baseline 오염을 숨길 수 있다 |

짧게 자르면 아래처럼 본다.

1. pilot lock / cross-category `concept_id` 충돌이면 release를 자르지 말고 wave를 멈춘다.
2. 같은 bucket이 2건 이상 반복되면 batch release 후보로 본다.
3. 한 문서 typo, prefix, alias 분리처럼 고립된 fix면 cherry-pick 후보로 본다.
4. batch release라도 `linked_paths`, `expected_queries`, `contextual_chunk_prefix`처럼 검증 축이 다른 수정은 한 commit에 섞지 않는다.

release-stop을 더 짧게 기억하려면 이렇게 보면 된다.

- Pilot lock drift = 보호 대상 집합 정의가 흔들린 상태라서 release cut 이전에 source/manifest 정합성이 먼저다.
- cross-category `concept_id` duplicate = chunk identity가 흔들린 상태라서 category 하나만 떼어도 회복되지 않을 수 있다.

## citation trace 질문을 release gate 질문과 섞지 않기

`참고:` path가 어색한데 동시에 frontmatter gate도 막혀 있으면, 둘을 한 원인으로 묶기 쉽다.
하지만 operator triage에서는 아래처럼 먼저 분리하는 편이 안전하다.

| 먼저 보이는 신호 | 우선 분류 | 이유 |
|---|---|---|
| learner-facing `참고:` path 선택 이유가 궁금하다 | citation-trace 문제 | 이미 검색 결과는 나왔고, 지금 필요한 것은 bucket/category/score 설명이다 |
| `aliases`, `expected_queries`, `linked_paths`, `contextual_chunk_prefix`가 strict gate에서 막힌다 | frontmatter contract 문제 | 검색 결과가 보이더라도 release publish 전에 막아야 하는 schema/lint 축이다 |
| citation도 비고 gate도 막혔다 | 두 갈래로 분리 | downgrade/hit-miss와 release gate를 한 wave 원인으로 섞으면 queue candidate가 broad해진다 |

## queue-governor는 "파일"보다 "실패 bucket"으로 먼저 자른다

2026-05-05 기준 strict v3 corpus lint 스냅샷에서는 release gate를 막는 `corpus_v3_frontmatter`가 78건이었다.
하지만 queue-governor에서는 count 자체보다 "같은 learner-facing 실패가 같은 bucket으로 반복되느냐"가 더 중요하다.
즉 이 표는 snapshot 참고치이고, 새 candidate 이름은 계속 아래 canonical bucket으로 고정하는 편이 안전하다.

| 현재 bucket | 관측된 위반 수 | 지금 새 후보를 늘리기보다 먼저 할 일 |
|---|---:|---|
| `linked_paths`가 `contents/...` 형식을 못 맞춤 | 59 | 같은 category의 v3 doc들을 path-normalization 묶음으로 처리하고, release gate 설명도 이 bucket 이름으로 통일한다 |
| `expected_queries` 누락 또는 빈 배열 | 18 | qrel seed가 없는 doc를 우선 repair 대상으로 묶고, 단순 frontmatter 추가 wave와 구분한다 |
| `aliases`와 `expected_queries`가 같은 문장을 반복함 | snapshot마다 변동 | alias/query overlap을 isolated frontmatter bucket으로 고정해 broad candidate 재증식을 막는다 |
| `contextual_chunk_prefix`가 비었거나 질문 모양이 약함 | snapshot마다 변동 | prefix format 미비를 typo/path repair와 섞지 않고 learner query handoff 실패로 따로 본다 |
| chooser의 `confusable_with`가 2개 미만 | 1 | 새 chooser 추가보다 기존 chooser의 비교 축을 먼저 완성한다 |

## snapshot count보다 bucket/category 조합을 먼저 본다

strict gate가 특정 날짜에 몇 파일, 몇 카테고리에 몰리는지는 계속 바뀔 수 있다.
그래서 queue-governor는 파일 목록을 backlog 제목으로 승격하지 않고, 아래 두 축만 먼저 고정한다.

1. canonical bucket이 무엇인가
2. category 검증 축이 정말 다른가

예를 들어 spring과 design-pattern에서 모두 `path-normalization`이 보이더라도,
설명 제목은 파일명 대신 `path-normalization + category` 조합으로 남기는 편이 duplicate enqueue를 줄인다.

## queue wave에서 canonical bucket 이름을 고정한다

queue wave를 실제로 굴릴 때는 아래처럼 "지금 뭐부터 자를지"를 먼저 고정하면 duplicate enqueue를 더 줄일 수 있다.
이때 lane마다 bucket 이름이 달라지면 같은 실패가 다른 후보처럼 다시 올라오므로, 아래 이름을 canonical label로 고정해 두는 편이 안전하다.

| 보이는 상태 | mental model | 먼저 내릴 판단 | safe next step |
|---|---|---|---|
| 같은 category에서 `linked_paths` 위반이 여러 파일에 반복된다 | 파일별 문제가 아니라 path-normalization 묶음이다 | writer lane 새 item을 파일별로 늘릴지, bucket 1개로 묶을지 | bucket 이름을 `path-normalization`으로 통일하고 category 단위 repair wave만 남긴다 |
| `expected_queries`가 비어 있는 문서가 드문드문 섞여 있다 | retrieval field는 있어도 eval seed가 없는 상태다 | frontmatter-complete wave로 보낼지, qrel-seed repair로 분리할지 | `missing-qrel-seed` bucket으로 분리하고 frontmatter typo batch와 섞지 않는다 |

## queue wave에서 overlap/prefix bucket을 분리한다

같은 frontmatter 계열 위반이라도 qrel seed 누락과 query overlap, prefix 약화는 learner-facing 실패가 다르다.
그래서 path/path-seed 묶음을 끝낸 뒤에는 overlap/prefix를 별도 bucket으로 보는 편이 안전하다.

| 보이는 상태 | mental model | 먼저 내릴 판단 | safe next step |
|---|---|---|---|
| `aliases`와 `expected_queries`가 비슷한 문장을 반복한다 | alias와 qrel seed 역할이 섞인 상태다 | path나 typo 문제와 한 배치로 묶을지, overlap repair로 따로 자를지 | `alias-query-overlap` bucket으로 고정하고 같은 wave에서 query seed 설명만 정리한다 |
| `contextual_chunk_prefix`가 비었거나 너무 짧다 | chunk 입구 문맥이 약해서 learner 자연어를 못 받는 상태다 | retrieval wording repair인지, schema typo인지부터 자를지 | `contextual-prefix-format` bucket으로 분리하고 prefix 보강 소규모 wave만 남긴다 |

## queue wave canonical bucket 예시

| 보이는 상태 | mental model | 먼저 내릴 판단 | safe next step |
|---|---|---|---|
| chooser/playbook 쪽 미세 위반이 1~2건 남아 있다 | 새 콘텐츠 부족이 아니라 비교 축 누락이다 | 새 chooser/playbook 후보를 추가할지, 기존 문서만 보강할지 | chooser는 `chooser-compare-gap`, playbook은 `playbook-symptom-gap`으로 분리하고 기존 문서 repair 1건만 남긴다 |
| `doc_role` enum 오탈자처럼 단일 schema typo가 남아 있다 | batch 품질 debt가 아니라 isolated typo다 | 새 lane을 열지, 개별 수선으로 끝낼지 | `enum-typo` bucket으로 고정하고 cherry-pick 1건만 남긴다 |
| cross-category `concept_id`가 겹치거나 Pilot lock source가 흔들린다 | partial release로 숨길 수 없는 chunk identity / baseline 문제다 | category split으로 버틸지, stop 신호로 올릴지 | `release-stop`으로 유지하고 `concept_id_unique` 또는 pilot lock source를 먼저 고정한다 |
| strict gate 숫자는 작아졌는데 next candidate가 계속 늘어난다 | queue가 품질 debt보다 생성 속도가 빨라진 상태다 | 새 candidate가 진짜 다른 bucket인지, 같은 실패를 이름만 바꿔 재등록한 것인지 | `next_candidates`에 canonical bucket 이름과 차별 포인트를 같이 적고, 같으면 enqueue하지 않는다 |

## queue candidate 생성 전 질문

새 candidate를 만들기 전에는 아래 세 질문을 먼저 고정한다.

1. learner-facing failure가 기존 item과 같은가
2. category 검증 축이 기존 item과 다른가
3. differentiator를 한 줄로 못 적으면 사실상 같은 후보가 아닌가

세 질문 중 하나라도 애매하면 새 후보를 추가하지 말고 기존 bucket 설명을 먼저 보강한다.
이 분기 자체를 learner-facing checklist로 짧게 다시 보고 싶으면 [RAG Ready Checklist](../RAG-READY.md)의 queue wave dedupe section으로 올라가면 된다.

## queue-governor에서 enqueue 대신 summary만 고칠 때

duplicate enqueue를 줄이려면 "새 후보를 만들지 않는 경우"를 먼저 고정하는 편이 안전하다.
아래 표는 queue wave에서 가장 자주 나오는 보류 패턴만 짧게 묶은 것이다.

| 지금 보이는 상태 | 새 item을 만들지 않는 이유 | 대신 할 일 |
|---|---|---|
| 제목만 파일명이나 category 표현만 바뀌고 learner-facing failure는 같다 | bucket이 이미 같고 differentiator가 없다 | 기존 candidate summary를 `bucket + category + differentiator` 형식으로 다시 쓴다 |
| 같은 `path-normalization`인데 파일만 여러 개 늘어났다 | 파일 수 증가는 queue 근거가 아니라 검증 범위 변화일 뿐이다 | 새 후보 대신 existing wave description에 affected category/paths만 덧붙인다 |
| `next_candidates`가 늘었지만 "왜 기존 item으로 안 묶는지" 한 줄 설명을 못 적겠다 | split 이유가 설명되지 않으면 broad 재등록일 가능성이 크다 | enqueue를 보류하고 split 근거가 생길 때까지 canonical bucket 1개로 유지한다 |
| Pilot lock drift나 cross-category `concept_id` 충돌이 섞여 있다 | 이 경우는 split 후보가 아니라 stop 신호다 | 새 후보 생성 대신 `release-stop`으로 올리고 source 정합성부터 복구한다 |

짧게 기억하면 queue-governor의 기본값은 "추가"가 아니라 "보류 후 기존 wave 설명 보강"이다.

## 같은 bucket인데 category가 다를 때 정말 분리해야 하나

queue-governor에서 가장 흔한 오판은 category가 둘 이상 보인다는 이유만으로 새 후보를 늘리는 것이다.
하지만 learner-facing failure와 validation axis가 그대로면, file split이나 category split이 아니라 기존 bucket 설명 보강으로 끝나는 경우가 많다.

| 관측 상태 | learner-facing failure | enqueue 판단 | 이유 |
|---|---|---|---|
| 같은 `path-normalization`이고 같은 category 안에서 파일명만 다르다 | 같다 | 분리하지 않는다 | 파일별 backlog로 자르면 같은 경로 계약 위반을 다시 증식시킨다 |
| 같은 bucket이고 category는 다르지만 둘 다 같은 path contract만 고치면 된다 | 거의 같다 | 기본은 1개로 유지한다 | 검증 축이 같으면 `bucket + multi-category note`가 더 안전하다 |
| 같은 bucket이지만 category별로 확인해야 할 contract나 비교축이 다르다 | 다르다 | 그때만 분리한다 | 예를 들어 chooser와 playbook은 둘 다 "보강"처럼 보여도 검증 기준이 다르다 |
| `release-stop` 성격의 Pilot lock drift나 cross-category `concept_id` 충돌이다 | batch 전체가 흔들린다 | 분리하지 말고 wave를 멈춘다 | 일부만 떼어내면 baseline 보호나 chunk identity 판단이 더 흐려진다 |

짧게 기억하면 이렇다.

- same bucket + same validation axis = 기존 후보에 묶는다.
- same bucket + different validation axis = 그때만 category split을 검토한다.
- `release-stop`은 split 후보가 아니라 stop 신호다.

## 초보 운영자를 위한 bucket 해석

초보 운영자 관점에서는 아래처럼 보면 된다.

- `path-normalization`: "링크 경로 형식이 틀려서 release gate가 막힌다"는 한 가지 질문에 답하는 repair 묶음이다.
- `missing-qrel-seed`: "검색은 될 수 있는데 eval seed가 없어서 품질 측정을 못 한다"는 다른 질문에 답하는 묶음이다.
- `chooser-compare-gap` / `playbook-symptom-gap`: 새 문서를 더 쓰는 문제가 아니라 기존 문서가 learner query를 제대로 받는지 보강하는 묶음이다.
- `enum-typo`: `deep-dive` vs `deep_dive`처럼 schema 표기 한 건이 release를 멈추는 경우를 분리하는 묶음이다.

즉, queue-governor의 첫 질문은 "어느 파일을 고칠까?"가 아니라 "이 실패가 어떤 learner-facing 검색 실패를 만들까?"여야 한다.
그래야 같은 `linked_paths` 오류를 lane마다 다시 candidate로 만들지 않고, 학습자가 실제로 겪는 "문서는 있는데 검색이 못 붙는다" 문제를 더 빨리 줄일 수 있다.

## bucket 이름을 next candidate에 그대로 쓴다

짧게 말하면:

- queue-governor는 같은 `linked_paths` 오류를 파일마다 새 item으로 복제하지 않는다.
- 먼저 `path-normalization`, `missing-qrel-seed`, `chooser-compare-gap`, `playbook-symptom-gap`, `enum-typo` 같은 canonical bucket 이름으로 묶는다.
- writer/qa lane의 next candidate도 이 bucket 이름을 그대로 써야 중복 enqueue를 줄일 수 있다.

## 빠른 triage 카드

운영자가 30초 안에 다음 분기를 고르려면 아래 표면 충분하다.

| 질문 모양 | 먼저 확인할 것 | safe next step |
|---|---|---|
| `새 문서가 왜 안 잡혀요` | stale index / helper 과노출 | [RAG Design](./README.md) |
| `참고:`는 붙는데 왜 이 문서인지 모르겠어요 | `response_hints.citation_trace` | [Source Priority and Citation](./source-priority-and-citation.md) |
| `frontmatter는 붙였는데 gate에서 막혀요` | `expected_queries`, `aliases`, `linked_paths`, `concept_id` | [Chunking and Metadata](./chunking-and-metadata.md) |
| `같은 종류 candidate가 계속 생겨요` | failure bucket 이름이 중복인지 | 이 문서의 queue-governor section |

## 복구 전략

1. 질문을 `domain`과 `intent`로 쪼갠다.
2. `README`와 `RAG-READY.md`를 먼저 찾는다.
3. `topic-map.md`로 교차 도메인을 고른다.
4. `source-priority-and-citation.md` 순서대로 인용한다.
5. 답변이 애매하면 `question-decomposition-examples.md` 패턴으로 다시 분해한다.
6. migration wave면 Pilot lock, alias/query 분리, corpus path 형식을 먼저 검증하고 나서 batch release를 자른다.

## 한 줄 정리

RAG의 품질은 "무엇을 찾았는가"보다 "무엇을 잘못 찾는가"를 얼마나 빨리 복구하느냐에 달려 있다.
