# Chunking and Metadata

> 한 줄 요약: `CS-study`는 파일 단위가 아니라, 제목과 섹션 단위로 잘라야 검색 품질이 안정적이다.

**난이도: 🔴 Advanced**
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [RAG Ready Checklist](../RAG-READY.md)
> - [Source Priority and Citation](./source-priority-and-citation.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)

> retrieval-anchor-keywords: chunking metadata, section chunking, retrieval metadata guide, linked_paths metadata, asset qa linked paths, auxiliary asset filename audit, html asset path metadata, reverse-link maintenance route, cs-index-build 했는데 새 문서가 안 잡혀요, helper 문서만 나와요, already_current but docs changed, manifest corpus hash mismatch, release tag unchanged, frontmatter는 붙였는데 gate에서 막혀요, alias query overlap, concept id duplicate, contextual chunk prefix format

## 기본 원칙

이 저장소의 문서는 대체로 다음 구조를 따른다.

- 제목
- 한 줄 요약
- 핵심 개념
- 깊이 들어가기
- 실전 시나리오
- 코드로 보기
- 트레이드오프
- 꼬리질문
- 한 줄 정리

RAG에서는 이 구조를 그대로 활용하는 편이 좋다.

### 자르는 기준

- `H1`는 문서 정체성이다. 문서 전체의 상위 메타데이터로 남긴다.
- `H2`는 기본 chunk 경계다. 대부분의 문서는 `H2` 단위로 자른다.
- `H3`는 길이가 길 때만 보조 chunk 경계로 쓴다.
- 표, 코드블록, SQL, 명령어는 중간에 끊지 않는다.
- `README.md`와 로드맵은 짧아도 통째로 유지하는 편이 낫다.

### 예외

- `materials/*.pdf` 추출본은 문단이 깨질 수 있으니, 문단 기준으로 다시 재분할한다.
- `code/` 아래 예시는 파일 경로를 메타데이터에 남기고, 설명 텍스트와 분리한다.
- 표가 핵심인 문서는 표를 분리 chunk로 유지한다.

## 권장 메타데이터

각 chunk에는 최소한 아래 메타데이터를 붙인다.

```json
{
  "path": "contents/database/index-and-explain.md",
  "title": "인덱스와 실행 계획",
  "category": "database",
  "doc_type": "deep_dive",
  "level": "advanced",
  "chunk_type": "section",
  "section": "실전 시나리오",
  "language": "ko",
  "contains_code": true,
  "contains_table": true,
  "retrieval_anchor_keywords": [
    "redo log",
    "checkpoint",
    "crash recovery"
  ],
  "linked_paths": [
    "contents/database/transaction-isolation-locking.md",
    "contents/database/mvcc-replication-sharding.md"
  ],
  "source_priority": 80
}
```

### 추천 필드

- `path`: 원본 파일 절대 경로 또는 repo-relative path
- `title`: 문서 제목
- `category`: `database`, `network`, `spring` 같은 상위 분류
- `doc_type`: `root`, `roadmap`, `index`, `deep_dive`, `qa`, `material`, `code`
- `level`: `basic`, `intermediate`, `advanced`
- `section`: chunk의 섹션명
- `language`: `ko`, `en`, `mixed`
- `contains_code`: 코드/쿼리 포함 여부
- `contains_table`: 표 포함 여부
- `retrieval_anchor_keywords`: 동의어, 약어, 증상, 에러 문자열, 도구 이름
- `linked_paths`: 같은 질문에서 자주 같이 읽는 파일. repo-local `img/`·`code/`나 local HTML asset form이 들어간 chunk라면 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)도 같이 남겨 후속 filename/reverse-link QA route를 보존한다.
- `source_priority`: 검색 우선순위 점수

## migration v3 release smoke에서 먼저 볼 메타데이터

`cs-index-build` 이후에도 새 문서가 안 잡히거나, frontmatter를 붙였는데 release gate에서 다시 막히는 질문은 대개 chunking 자체보다 메타데이터 contract가 먼저 흔들린 경우다.
이때 learner가 "문서를 다시 쪼개야 하나?"부터 의심하면 복구가 느려진다.

먼저 아래 네 항목만 짧게 자르는 편이 안전하다.

| 보이는 증상 | 먼저 확인할 필드 | 왜 먼저 보나 |
|---|---|---|
| `frontmatter는 붙였는데 gate에서 막혀요` | `expected_queries` | 비어 있으면 qrel seed를 못 만들고, release gate에서 "붙였지만 아직 못 씀" 상태가 된다. |
| `aliases랑 expected_queries가 거의 같아요` | `aliases`, `expected_queries` | alias는 검색어 확장, expected query는 eval seed라 역할이 다르다. 둘이 겹치면 `no_alias_query_overlap` gate에 걸린다. |
| `linked_paths`가 있는데도 handoff가 이상해요 | `linked_paths` | `contents/<category>/<file>.md` 형식이 아니면 retrieval 재탐색 힌트가 끊긴다. |
| prefix를 override했는데 검색 tone이 더 흐려졌어요 | `contextual_chunk_prefix`, `concept_id` | 빈 prefix나 중복 `concept_id`는 chunk identity를 흐리게 만들어 `contextual_prefix_format`, `concept_id_unique` gate를 같이 흔든다. |

실무에서는 아래 순서로 보면 충분하다.

1. Pilot cohort 문서를 건드린 건 아닌지 확인한다.
2. `expected_queries`가 비어 있지 않은지 본다.
3. `aliases`와 `expected_queries`가 같은 문장을 반복하지 않는지 본다.
4. `linked_paths`, `concept_id`, `contextual_chunk_prefix` 형식을 확인한다.

이 분기는 [Retrieval Failure Modes](./retrieval-failure-modes.md)의 release blocker 설명과 같은 순서로 유지하는 편이 좋다.

## chunking 문제로 오진하지 않기

index-smoke 질문은 겉으로는 모두 "검색이 이상하다"로 들리지만, 아래 셋은 chunking보다 다른 surface를 먼저 보는 편이 안전하다.

| 보이는 증상 | chunking보다 먼저 볼 것 | 왜 먼저 여기서 자르나 | safe next step |
|---|---|---|---|
| migration branch에서 문서를 고쳤는데 learner 환경 `cs-index-build`는 `already_current`만 나온다 | release lock, local manifest | 이 경우는 chunk boundary보다 learner가 아직 이전 artifact를 들고 있는지 확인하는 편이 빠르다 | [Retrieval Failure Modes](./retrieval-failure-modes.md) |
| `README`, `RAG-READY.md` 같은 helper 문서만 계속 잡힌다 | query shape, helper 제외 규칙 | metadata가 맞아도 broad helper query면 concept 본문 handoff가 계속 밀릴 수 있다 | [Query Playbook](./query-playbook.md), [RAG Design](./README.md) |
| `manifest.json`의 corpus hash와 지금 `knowledge/cs/**` corpus hash가 다르다 | source corpus vs local artifact drift | source doc repair와 local artifact 상태를 같은 것으로 보면 rebuild 판단이 꼬인다 | [Retrieval Failure Modes](./retrieval-failure-modes.md), [RAG Ready Checklist](../RAG-READY.md) |

짧게 기억하면 이렇다.

1. `expected_queries`, `aliases`, `linked_paths`, `concept_id`, `contextual_chunk_prefix`는 metadata contract 문제다.
2. `already_current`, `manifest hash mismatch`, `release tag unchanged`는 release/local-state 문제다.
3. helper 문서 과노출은 chunking보다 query shape와 source-priority 분기를 먼저 확인한다.

## RAG에 맞는 청크 우선순위

1. root/roadmap 질문이면 `README.md`, `JUNIOR-BACKEND-ROADMAP.md`, `ADVANCED-BACKEND-ROADMAP.md`, `SENIOR-QUESTIONS.md`
2. 개념 질문이면 `contents/*/README.md`
3. 구현/실전 질문이면 `contents/**/deep dive` 문서
4. 예시 코드 질문이면 `code/` 또는 문서 내 `코드로 보기`
5. 마지막 보강으로 `materials/`

## 실전 팁

- chunk 크기는 "토큰 수"만 보지 말고, 섹션 의미가 끊기는지 먼저 본다.
- 같은 개념이 여러 문서에 반복되면, 인용할 원문은 하나만 남기고 나머지는 링크 관계로 처리한다.
- 문서 내부 링크는 chunk metadata의 `linked_paths`에 넣어 재탐색 힌트로 쓴다.
- `retrieval-anchor-keywords` 줄이 있으면 metadata에 그대로 올려서 alias 확장에 쓴다.
- release smoke가 걸린 wave에서는 chunk 크기보다 `expected_queries`, `aliases`, `linked_paths`, `concept_id`, `contextual_chunk_prefix` 계약을 먼저 본다.
- repo-local `img/`·`code/` path나 local HTML asset form을 설명하는 chunk는 `linked_paths`에서 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)로 한 번 더 이어 두면 다음 link-maintenance wave가 adjacent QA note를 놓치지 않는다.
- README는 개념의 정의보다 위치 안내 역할을 하므로 짧은 chunk로 유지한다.

## 한 줄 정리

`CS-study`는 "파일"이 아니라 "섹션"을 검색 단위로 봐야 하고, 메타데이터는 `path`, `category`, `doc_type`, `level`, `section`, `linked_paths`가 핵심이다.
