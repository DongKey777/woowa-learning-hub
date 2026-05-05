# RAG Ready Checklist

> 한 줄 요약: 이 저장소를 RAG에 넣을 때는 문서 구조, chunk 기준, 우선순위, citation 규칙뿐 아니라 `cs-index-build` 이후 stale index와 readiness smoke를 어디서 복구할지도 미리 고정돼 있어야 한다.

**난이도: 🟢 Beginner**

retrieval-anchor-keywords: rag ready checklist, retrieval readiness, rag index smoke, migration v3 readiness, cs-index-build checklist, 왜 새 문서가 안 잡혀요, helper 문서만 나와요, 뭐예요, frontmatter release gate, missing qrel seed, concept_id 중복, concept_id unique, queue governor dedupe, pilot lock drift, cross-category split, cohort eval gate, real qrels drift, baseline 94.0, regression baseline, verify real qrels, refusal threshold calibration

관련 문서:

- [RAG README](./rag/README.md)
- [Chunking and Metadata](./rag/chunking-and-metadata.md)
- [Source Priority and Citation](./rag/source-priority-and-citation.md)
- [Topic Map](./rag/topic-map.md)
- [Query Playbook](./rag/query-playbook.md)
- [Retrieval Anchor Keywords](./rag/retrieval-anchor-keywords.md)
- [Cross-Domain Bridge Map](./rag/cross-domain-bridge-map.md)
- [Retrieval Failure Modes](./rag/retrieval-failure-modes.md)
- [Dual-Read Comparison / Verification Platform 설계](../cs/contents/system-design/dual-read-comparison-verification-platform-design.md)
- [Master Notes](./MASTER-NOTES.md)

## 운영 규칙

1. 질문이 들어오면 카테고리를 먼저 고른다.
2. 넓거나 교차 도메인 질문이면 `master-notes/`를 먼저 붙인다.
3. `README`와 로드맵으로 범위를 정한다.
4. `topic-map`과 `cross-domain-bridge-map`으로 교차 영역을 확인한다.
5. 심화 문서의 `H2` 섹션을 우선 검색한다.
6. 증상/에러 문자열 질문이면 `retrieval-anchor-keywords`로 alias를 먼저 확장한다.
7. 코드와 `materials/`는 보강용으로만 쓴다.
8. 답변에는 원문 경로를 붙인다.
9. direct question은 `definition / mechanism / policy / troubleshooting / design`으로 먼저 분해한다.
10. `rag/*`, `RAG-READY.md`, 루트 가이드 같은 메타 문서는 기본 검색에서 우선 제외하고, RAG 자체를 묻는 질문일 때만 다시 포함한다.
11. `cs-index-build` 이후에도 helper 문서만 계속 잡히거나 새 문서가 안 보이면, chunking 오류보다 먼저 stale index / readiness smoke를 의심한다.

## 금지

- 문서 전체를 무작정 같은 가중치로 검색하지 않는다.
- `materials/`를 심화 문서보다 먼저 인용하지 않는다.
- `README`의 요약과 깊이 문서의 세부 원리를 섞어 말하지 않는다.
- 동일한 개념을 여러 문서에서 중복 인용하지 않는다.
- 에러 문자열이나 운영 증상을 일반 개념어 하나로 뭉개서 검색하지 않는다.

## 체크 포인트

- 문서 제목이 검색 가능한가
- H2 기준 chunk가 의미 단위인가
- alias/증상 문서를 위한 `retrieval-anchor-keywords`가 들어 있는가
- linked paths가 남아 있는가
- code/materials가 보조 소스인지 구분되는가
- root guide에서 카테고리로 잘 내려갈 수 있는가
- 넓은 질문을 받아줄 `master-notes/` 상위 레이어가 있는가

## 인덱스 readiness smoke에서 먼저 확인할 것

RAG 운영 질문은 "문서가 왜 안 잡히지?"처럼 broad하게 들어오기 쉽다.
이때 learner가 바로 deep dive 원인을 추측하기보다, 아래 순서로 증상을 고정하면 복구가 빨라진다.

| 보이는 증상 | 먼저 의심할 것 | safe next step |
|---|---|---|
| `cs-index-build`를 돌렸는데 새 문서가 안 잡힌다 | stale index, build 대상 누락, helper 문서 과노출 | [Chunking and Metadata](./rag/chunking-and-metadata.md), [Retrieval Failure Modes](./rag/retrieval-failure-modes.md) |
| migration branch에서 문서를 고쳤는데 learner 환경 `cs-index-build`는 `already_current`만 나온다 | corpus repair와 publish/release handoff를 같은 단계로 보고 있는지 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md), [Query Playbook](./rag/query-playbook.md) |
| 질문이 계속 `README`, `RAG-READY.md` 같은 helper 문서로만 간다 | route label은 맞지만 concept 본문 handoff가 실패함 | [Topic Map](./rag/topic-map.md), [Query Playbook](./rag/query-playbook.md) |
| citation은 붙는데 본문이 옛 설명처럼 보인다 | stale retrieval 또는 source priority 역전 | [Source Priority and Citation](./rag/source-priority-and-citation.md), [Retrieval Failure Modes](./rag/retrieval-failure-modes.md) |
| `참고:`는 붙는데 왜 이 path가 붙었는지 모르겠다 | learner-facing citation과 operator trace를 섞어 보고 있음 | [Source Priority and Citation](./rag/source-priority-and-citation.md), [Retrieval Failure Modes](./rag/retrieval-failure-modes.md) |

처음 보는 learner에게는 "`문서가 왜 안 잡히지?`"를 곧바로 chunking 문제로 번역하지 말고,
먼저 "stale index인지", "helper 문서 과노출인지", "citation trace로 bucket을 봐야 하는지"를
질문으로 나눠 보는 편이 안전하다.

## release handoff smoke에서 먼저 확인할 것

release 쪽 질문은 "`문서를 고쳤다`"와 "`학습자에게 새 artifact가 내려갔다`"를 같은 단계로
착각할 때 길어진다. 아래 표처럼 failure bucket 이름을 먼저 붙이면 다음 wave가 짧아진다.

| 보이는 증상 | 먼저 의심할 것 | safe next step |
|---|---|---|
| migration wave에서 frontmatter는 붙였는데 release gate에서 막힌다 | `aliases`/`expected_queries` 역할 중복, `linked_paths` path contract 위반, 빈 `contextual_chunk_prefix` override, cross-category `concept_id` 중복 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md), [Query Playbook](./rag/query-playbook.md) |
| migration branch에서는 문서를 고쳤는데 learner 환경 `cs-index-build`는 `already_current`만 나온다 | release tag가 아직 안 바뀌었거나, local `manifest.json`은 이전 release를 가리키고 있고, RunPod rebuild/publish가 아직 안 끝남 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md) |
| migration wave에서 `batch release`로 묶을지 `cherry-pick`으로 뺄지 헷갈린다 | 같은 failure bucket 반복인지, isolated typo/prefix fix인지, Pilot lock/`concept_id` 충돌인지 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md), [Query Playbook](./rag/query-playbook.md) |
| Pilot source 목록과 `locked_pilot_paths.json`이 서로 안 맞는 것 같다 | lock manifest mismatch인지, strict gate 숫자가 lock drift를 반영하는지 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md), [Query Playbook](./rag/query-playbook.md) |
| strict v3 blocker 숫자가 왜 갑자기 커졌는지 헷갈린다 | 파일 수보다 `path-normalization`/`missing-qrel-seed` bucket이 먼저 커졌는지, 같은 category에 몰렸는지 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md), [Query Playbook](./rag/query-playbook.md) |

## cohort eval gate에서 먼저 확인할 것

cohort eval 질문은 "`문서가 좋아졌는데 왜 점수는 떨어졌지?`"처럼 들어오기 쉽다.
이때는 corpus repair, qrels fixture drift, baseline snapshot 갱신을 같은 원인으로 뭉개지 않는 편이 안전하다.

| 보이는 증상 | 먼저 의심할 것 | safe next step |
|---|---|---|
| `strict v3 blocker`는 줄었는데 cohort baseline이 `94.0` 아래로 떨어진다 | corpus 품질 후퇴인지, qrels fixture/seed drift인지 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md), [Query Playbook](./rag/query-playbook.md) |
| `expected_queries`를 채웠는데 real qrels 검증이 다시 막힌다 | alias 보강과 eval seed를 같은 문장으로 넣었는지, canonical path가 바뀌었는지 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md), [Chunking and Metadata](./rag/chunking-and-metadata.md) |
| refusal threshold calibration report만 바뀌었는데 전체 retrieval regression처럼 보인다 | retrieval recall 저하인지, threshold tuning snapshot 변화인지 | [Retrieval Failure Modes](./rag/retrieval-failure-modes.md), [Source Priority and Citation](./rag/source-priority-and-citation.md) |
| learner 질문은 그대로인데 paraphrase/symptom cohort만 흔들린다 | query reformulation alias가 약해졌는지, helper 문서가 다시 과노출되는지 | [Query Playbook](./rag/query-playbook.md), [RAG README](./rag/README.md) |

짧게 기억하면 아래 세 갈래다.

1. corpus doc repair
2. qrels / expected_queries seed 정합성
3. baseline / calibration snapshot 변화

cohort eval gate에서 "`94.0 아래로 떨어졌다`"는 문장은 원인 이름이 아니라 결과다.
그래서 바로 "`문서가 나빠졌다`"로 번역하지 말고, 먼저 "seed drift인가", "query alias가 흔들렸나",
"threshold snapshot만 달라졌나"를 자르는 편이 learner-facing 품질 복구에 더 안전하다.

## index rebuild trigger를 세 surface로 나눠 보기

`문서는 바뀌었는데 왜 learner는 그대로예요`라는 질문은 한 줄처럼 들리지만,
실제로는 아래 세 surface가 분리돼 있다.

| surface | 여기서 보는 truth | 여기서 막히면 어떤 착각이 생기나 |
|---|---|---|
| source corpus | `knowledge/cs/**` 실제 문서 집합과 현재 corpus hash | 문서를 고쳤으니 learner도 바로 새 내용을 본다고 착각하기 쉽다 |
| local index state | `state/cs_rag/manifest.json`과 `r3_lexical_sidecar.json`이 가리키는 현재 로컬 artifact | 이미 내려받은 artifact와 source corpus를 같은 것으로 착각하기 쉽다 |
| release lock | `config/rag_models.json`의 `release.tag` / `archive_sha256` | release tag가 안 바뀌었는데도 publish가 끝났다고 착각하기 쉽다 |

짧게 기억하면 이렇다.

1. source corpus가 바뀌는 것은 migration wave 일이다.
2. local index state가 바뀌는 것은 rebuild / fetch 결과다.
3. learner에게 새 artifact가 내려가는 것은 release lock이 바뀐 뒤다.

즉 `already_current`는 "source corpus와 완전히 같다"가 아니라,
대개 "현재 learner가 들고 있는 local artifact가 아직 같은 release lock을 가리킨다"에 가깝다.
그래서 rebuild trigger 질문에서는 문서 diff보다 먼저 "지금 보고 있는 것이 source corpus인지, local manifest인지, release lock인지"를 구분해야 한다.

## target query shape를 먼저 고정하기

target query shape는 대체로 아래 셋이다.

- `cs-index-build 했는데 왜 새 문서가 안 잡혀요`
- `rag index stale 인가요 helper 문서만 나와요`
- `retrieval readiness smoke에서 뭐부터 확인해요`
- `참고는 붙는데 왜 이 path예요 citation trace가 뭐예요`
- `frontmatter는 붙였는데 왜 release gate에서 다시 막혀요`
- `문서는 고쳤는데 왜 cs-index-build는 already_current예요`
- `manifest corpus hash랑 지금 corpus hash가 왜 달라요`
- `release tag는 그대로인데 문서는 바뀌었어요`
- `이 blocker는 batch release로 묶어야 해요 아니면 cherry-pick 해요`
- `pilot lock drift인가요 locked_pilot_paths mismatch인가요`
- `strict v3 blocker가 왜 늘었어요 path-normalization 때문인가요`
- `cohort eval baseline이 왜 94.0 아래로 떨어졌어요`
- `real qrels drift인가요 expected_queries가 잘못된 건가요`
- `refusal threshold calibration만 바뀌었는데 retrieval regression인가요`

2026-05-05 strict v3 corpus lint 스냅샷처럼 blocker 숫자가 한 번 커져 보여도,
queue-governor는 그 숫자 자체보다 "같은 bucket이 같은 category 안에서 반복되느냐"를 먼저 본다.
즉 snapshot count는 상황 설명일 뿐이고, enqueue 이름은 계속 `path-normalization`,
`missing-qrel-seed` 같은 canonical bucket으로 유지하는 편이 안전하다.

## frontmatter release gate를 30초 안에 자르는 기준

readiness 질문이 "`frontmatter는 붙였는데 왜 또 gate에서 막히죠?`"로 들어오면,
학습자는 migration 전체를 의심하기 쉽다. 하지만 실제로는 아래 세 갈래 중 하나로
바로 줄어드는 경우가 많다.

| 보이는 실패 | 먼저 고정할 질문 | 왜 이 질문이 먼저인가 |
|---|---|---|
| `aliases`와 `expected_queries`가 둘 다 비슷한 문장이다 | alias인가, qrel seed인가 | 같은 표현을 두 군데에 넣으면 retrieval과 eval 역할이 겹쳐서 release gate가 다시 막힌다 |
| `linked_paths`가 `./spring-x.md`처럼 들어 있다 | corpus path contract를 지켰나 | release gate는 사람이 읽기 좋은 상대경로보다 `contents/...` 정규 경로를 먼저 본다 |
| `contextual_chunk_prefix`를 비워 두었거나 한 줄 메모처럼만 적었다 | dense 검색용 문맥 프리픽스가 실제 질문을 받나 | prefix가 빈 override면 doc body는 좋아도 chunk 입구가 약해진다 |
| `concept_id`가 다른 category 문서와 겹친다 | typo 하나인가, chunk identity 자체가 충돌하는가 | duplicate `concept_id`는 retrieval 선택과 strict lint를 같이 흔들어서 isolated typo처럼 cherry-pick하면 증상을 가리기 쉽다 |

짧게 말하면 아래 순서로 자르면 된다.

1. `aliases ⊥ expected_queries`를 먼저 본다.
2. 그다음 `linked_paths=contents/...` 정규화 여부를 본다.
3. `concept_id`가 category를 넘어 중복되지 않는지 본다.
4. 마지막으로 `contextual_chunk_prefix`가 비어 있지 않고, 학습자 자연어 paraphrase를 받는지 본다.

`expected_queries`가 비었다면 "frontmatter는 있는데 release gate가 막힌다"가 아니라
"qrel seed가 없어 readiness smoke가 비어 보인다"로 이름을 붙이는 편이 안전하다.
queue-governor에서도 이 경우는 파일명보다 `missing-qrel-seed` bucket으로 먼저 묶어야
같은 누락을 새 candidate로 다시 증식시키지 않는다.

이 네 줄은 [Query Playbook](./rag/query-playbook.md)의 `pilot 50 untouched -> aliases ⊥ expected_queries -> linked_paths=contents/... -> concept_id unique -> contextual_chunk_prefix format` 순서를
학습자 질문 기준으로 다시 풀어쓴 것이다. 즉 "`release gate가 막혔다`"는 말만으로는 broad하니,
먼저 "역할 중복", "path contract", "chunk identity 충돌", "prefix 문맥 부족" 중 어디인지 이름을 붙이면 다음 wave가 훨씬 짧아진다.

## 배치 판단을 짧게 고정하기

index rebuild trigger나 release handoff를 묻는 질문은 "문서를 고쳤다"와 "학습자에게 새 artifact가 내려간다"를 같은 단계로 착각하기 쉽다.
이럴 때는 아래 두 줄만 먼저 고정하면 drift를 줄이기 쉽다.

- migration wave: 문서 repair와 queue 정리는 여기서 끝난다.
- publish window: RunPod rebuild, verify/import, release tag 갱신은 여기서만 한다.

queue-governor triage에서는 파일명보다 canonical bucket 이름을 먼저 고정해야 duplicate enqueue를 줄이기 쉽다.

| 보이는 blocker | canonical bucket | 왜 먼저 이름을 고정하나 |
|---|---|---|
| 같은 category에서 `linked_paths` path contract 위반이 반복된다 | `path-normalization` | 파일별 candidate로 쪼개면 같은 경로 정규화 이슈가 다시 증식하기 쉽다 |
| `expected_queries`가 비었거나 누락됐다 | `missing-qrel-seed` | frontmatter migration과 qrel seed repair를 다른 wave로 분리할 수 있다 |
| `aliases`와 `expected_queries`가 같은 문장을 반복한다 | `alias-query-overlap` | retrieval alias와 eval seed 역할이 섞인 후보를 broad한 frontmatter debt로 다시 부풀리지 않게 막는다 |
| `contextual_chunk_prefix`가 비었거나 질문 모양이 약하다 | `contextual-prefix-format` | prefix 문맥 부족을 typo나 path repair와 분리해야 learner query handoff 실패를 따로 설명할 수 있다 |
| chooser의 `confusable_with`가 부족하다 | `chooser-compare-gap` | 새 chooser 작성보다 기존 비교축 보강이 먼저라는 신호를 준다 |
| playbook의 `symptoms`가 비었다 | `playbook-symptom-gap` | 새 playbook 확장보다 learner symptom handoff repair를 우선시한다 |
| `doc_role` enum 표기 한 건이 틀렸다 | `enum-typo` | isolated typo를 large batch처럼 부풀리지 않게 막는다 |
| Pilot lock 또는 cross-category `concept_id` 충돌이다 | `release-stop` | `concept_id_unique` 위반은 일부 문서만 빼서는 chunk identity 판단이 안 서므로 partial release보다 wave 중단과 source 재조정이 먼저다 |

질문이 `duplicate enqueue`, `runaway candidate`, `queue wave triage` 쪽이면 위 bucket 이름으로 먼저 재질의한 뒤 [Retrieval Failure Modes](./rag/retrieval-failure-modes.md)로 내려가면 된다.

## release-stop을 섣불리 cherry-pick으로 낮추지 않기

운영 질문에서 흔한 오판은 "`문서 몇 개만 어긋났으니 cherry-pick이면 된다`"라고 빨리 결론내리는 것이다.
하지만 아래 둘은 파일 수와 무관하게 release-stop으로 유지하는 편이 안전하다.

| 보이는 신호 | 왜 cherry-pick으로 낮추면 안 되나 | safe next step |
|---|---|---|
| Pilot source 목록과 `locked_pilot_paths.json`이 서로 다른 집합을 가리킨다 | baseline 보호 범위 자체가 흔들려서 일부 문서만 떼어도 `pilot_50_untouched` 판단이 계속 어긋날 수 있다 | source 목록과 lock manifest를 먼저 맞추고, 그전까지는 wave를 멈춘 채 [Retrieval Failure Modes](./rag/retrieval-failure-modes.md)의 `release stop` 기준으로 본다 |
| cross-category `concept_id` 중복이 보여서 한 category만 먼저 빼고 싶다 | duplicate chunk identity는 retrieval 선택과 lint 결과를 같이 흔들어서 partial release가 증상을 가릴 수 있다 | duplicate 쌍을 먼저 고정하고, batch를 다시 자를지 나중에 판단한다 |

즉 `release-stop`은 "파일이 많다"가 아니라 "일부만 내보내면 baseline이나 chunk identity 판단이 더 흐려진다"는 뜻이다.

## next candidate를 바로 늘리지 않는 기준

queue-governor에서 가장 흔한 실수는 같은 실패를 파일명만 바꿔 여러 candidate로 다시 올리는 것이다.
초보 운영자도 아래 세 줄만 먼저 보면 runaway candidate를 많이 줄일 수 있다.

| 보이는 상태 | 먼저 할 질문 | enqueue 판단 |
|---|---|---|
| 새 후보 제목이 파일명만 다르고 설명은 거의 같다 | 기존 bucket과 learner-facing failure가 같은가 | 같으면 새 item을 만들지 말고 기존 bucket item에 묶는다 |
| blocker 숫자는 줄었는데 `next_candidates`가 계속 늘어난다 | 품질 debt가 남은 건가, 이름만 다른 재등록인가 | canonical bucket + category + 차별 포인트가 모두 없으면 enqueue하지 않는다 |
| 같은 bucket인데 category만 다르다 | release/repair 단위가 category별 검증이 필요한가 | category 검증 축이 다를 때만 분리하고, 아니면 batch 이름 하나로 유지한다 |

짧게 기억하면 `bucket -> category -> differentiator` 순서로만 새 후보를 만든다.
이 세 칸 중 하나라도 비어 있으면 queue를 늘리기보다 기존 wave 설명을 먼저 고친다.

## queue wave dedupe를 15초 안에 자르는 기준

queue-governor wave에서는 "문서를 더 만들까"보다 "같은 learner-facing 실패를 또 enqueue하는가"를 먼저 본다.
아래 표처럼 `bucket + category + differentiator`를 한 번에 확인하면 duplicate candidate를 많이 줄일 수 있다.

| 지금 보이는 상태 | 바로 붙일 질문 | enqueue 판단 |
|---|---|---|
| 후보 제목만 파일명이나 category 표현만 바뀌고 설명은 거의 같다 | learner-facing failure가 정말 다른가 | 다르지 않으면 기존 bucket item 설명만 보강하고 새 후보는 만들지 않는다 |
| 같은 `path-normalization`인데 spring과 design-pattern이 같이 보인다 | category 검증 축이 서로 다른가 | 검증 축이 다를 때만 분리하고, 아니면 bucket 1개로 유지한다 |
| `next_candidates`가 늘었는데 differentiator를 한 줄로 못 적겠다 | bucket 이름만 바꾼 재등록 아닌가 | differentiator를 못 적으면 enqueue 대신 기존 wave summary를 고친다 |

운영자가 짧게 기억할 문장은 하나면 충분하다.

- 새 후보는 `bucket`, `category`, `differentiator`가 모두 있을 때만 만든다.
- 셋 중 하나라도 비면 queue를 늘리지 말고 기존 bucket 설명을 먼저 정리한다.
- learner가 겪는 질문이 같다면 파일명이 달라도 같은 후보로 본다.

## RAG 적용 대상

- 학습 경로 추천
- 개념 설명
- 비교 질문
- 장애/운영 질문
- 코드 예시가 필요한 질문

## 한 줄 정리

이 저장소의 RAG는 `README -> category README -> master-notes(필요 시) -> deep dive -> code/materials` 순으로 내려가고, chunk는 `H2` 중심, 인용은 가장 구체적인 원문 중심으로 해야 한다.
