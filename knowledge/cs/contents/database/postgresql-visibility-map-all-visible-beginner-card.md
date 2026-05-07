---
schema_version: 3
title: PostgreSQL Visibility Map and All-Visible Beginner Card
concept_id: database/postgresql-visibility-map-all-visible-beginner-card
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- postgresql
- visibility-map
- index-only-scan
- autovacuum
aliases:
- postgresql visibility map basics
- all-visible meaning
- visibility map what is
- page visibility vs tuple visibility
- row mvcc visibility beginner
- why heap fetches remain
- vacuum all visible basics
- visibility map 처음
- all visible 뭐예요
- tuple visibility 뭐예요
symptoms:
- PostgreSQL visibility map을 row 단위 visible 여부 저장소로 오해하고 page-level all-visible hint를 놓치고 있어
- Index Only Scan인데 Heap Fetches가 남는 이유를 visibility map과 all-visible page 상태로 연결해야 해
- autovacuum가 visibility map을 회복시켜 heap 재확인을 줄이는 흐름을 이해해야 해
intents:
- definition
- troubleshooting
prerequisites:
- database/postgresql-index-only-scan-heap-fetches-beginner-card
- database/mvcc-replication-sharding
next_docs:
- database/postgresql-buffers-hit-read-dirtied-written-mini-card
- database/vacuum-purge-debt-forensics-symptom-map
- database/covering-index-vs-index-only-scan
linked_paths:
- contents/database/postgresql-index-only-scan-heap-fetches-beginner-card.md
- contents/database/covering-index-vs-index-only-scan.md
- contents/database/vacuum-purge-debt-forensics-symptom-map.md
- contents/data-structure/hybrid-top-index-leaf-layouts.md
- contents/database/postgresql-explain-analyze-terms-mini-bridge.md
confusable_with:
- database/postgresql-index-only-scan-heap-fetches-beginner-card
- database/vacuum-purge-debt-forensics-symptom-map
- database/covering-index-vs-index-only-scan
forbidden_neighbors: []
expected_queries:
- PostgreSQL visibility map과 all-visible은 무엇이고 Heap Fetches와 어떻게 연결돼?
- all-visible이 tuple visibility와 같은 말이 아닌 이유를 page-level hint로 설명해줘
- Index Only Scan에서 page가 all-visible이 아니면 왜 heap을 다시 확인해?
- autovacuum이 visibility map을 갱신하면 heap fetches가 줄 수 있는 이유가 뭐야?
- visibility map은 row별 메모인지 page별 메모인지 초보자용으로 알려줘
contextual_chunk_prefix: |
  이 문서는 PostgreSQL visibility map과 all-visible page-level hint가 Index Only Scan의 Heap Fetches를 줄이거나 남기는 이유를 설명하는 beginner primer다.
  visibility map 처음, all visible 뭐예요, tuple visibility와 page visibility 차이 질문이 본 문서에 매핑된다.
---
# PostgreSQL `visibility map`과 `all-visible`은 뭐예요?

> 한 줄 요약: `visibility map`은 PostgreSQL이 "이 heap page는 지금 heap 본문을 다시 안 봐도 될 가능성이 높다"라고 빠르게 표시해 두는 메모이고, `all-visible`은 그 page의 tuple들이 현재 모든 스냅샷에서 보일 수 있다고 정리된 상태를 뜻한다.

**난이도: 🟢 Beginner**

관련 문서:

- [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)
- [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: postgresql visibility map basics, all-visible meaning, visibility map what is, page visibility vs tuple visibility, row mvcc visibility beginner, why heap fetches remain, vacuum all visible basics, postgresql page visibility, index only scan follow up, visibility map 처음, all visible 뭐예요, tuple visibility 뭐예요, 왜 page visibility랑 헷갈려요, beginner visibility map

## 핵심 개념

`Heap Fetches` 설명을 읽고도 막히는 지점은 보통 여기다.
"그래서 visibility map이 정확히 뭐고, all-visible은 무슨 체크인가?"

초급에서는 먼저 층을 둘로 나누면 덜 헷갈린다.

- heap page: row 본문이 들어 있는 페이지
- tuple visibility: "이 row 버전이 내 현재 snapshot에서 보여도 되나?"를 따지는 MVCC 규칙
- `visibility map`: "이 페이지는 지금 tuple visibility를 row마다 다시 안 봐도 될 가능성이 큰가?"를 빠르게 적어 둔 메모
- `all-visible`: 그 page의 tuple들이 현재 모든 transaction에 대해 visible하다고 page 단위로 정리된 상태

즉 `all-visible`은 tuple 하나하나의 판정 결과를 대신 저장한 영구 딱지가 아니라,
**이 page는 지금 row-level MVCC 검사를 생략해도 될 가능성이 크다**는 page-level 힌트에 가깝다.

## 한눈에 보기

| 층 | 무엇을 판단하나 | 초보자용 멘탈모델 | 실행 계획에서 체감되는 변화 |
| --- | --- | --- | --- |
| tuple visibility | 개별 row 버전이 내 snapshot에 보이는가 | row마다 붙는 MVCC 질문 | 필요하면 heap에서 직접 확인한다 |
| `visibility map` | 이 page는 row별 확인을 생략해도 될 가능성이 큰가 | heap 옆의 page 메모 | heap 재확인이 줄 수 있다 |
| page가 `all-visible` | 이 page의 tuple들이 현재 모두 visible한가 | "이 page는 이번엔 다시 안 열어봐도 될 가능성이 높다" | `Heap Fetches`가 줄기 쉽다 |
| page가 `all-visible` 아님 | 어떤 tuple은 직접 확인이 필요할 수 있는가 | "이 page는 조심해야 하니 heap으로 내려간다" | heap 방문이 다시 붙기 쉽다 |

```text
안전한 순서
1. index가 후보 row를 찾는다
2. postgres가 visibility map으로 "이 page는 통과 가능한가?"를 본다
3. all-visible이 아니면 heap에서 tuple visibility를 다시 확인한다
```

## 상세 분해

`visibility map`은 row마다 붙는 메모가 아니라 **page 단위 메모**다.
그래서 어떤 row 하나만 보고 "이 row는 보여요"라고 적는 게 아니라,
"이 page 전체는 지금 all-visible로 취급할 수 있나?"를 본다.

여기서 가장 많이 섞이는 두 질문을 따로 떼면 아래와 같다.

| 질문 | 판단 단위 | 누가 주로 보나 | 의미 |
| --- | --- | --- | --- |
| "이 row 버전이 내 transaction에서 보여도 되나?" | tuple | MVCC visibility check | row-level 판정 |
| "이 page는 row별 판정을 다시 안 해도 되나?" | page | visibility map / `all-visible` bit | page-level 힌트 |

여기서 `all-visible`은 "누구에게나 영원히 보인다"가 아니다.
최근 `UPDATE`나 `DELETE`가 생기면 그 page는 다시 조심해야 하므로,
이 표식이 깨지고 heap 재확인이 다시 필요해질 수 있다.

비유로는 `all-visible`을 "이 서랍은 오늘은 통째로 검사 통과" 메모처럼 볼 수 있다.
다만 이 비유는 **page를 한 번에 스킵할 수 있다**는 감각까지만 맞고,
실제 row가 어떤 transaction에 보이는지는 여전히 MVCC 규칙이 결정한다.

초급자가 붙잡아야 할 핵심은 하나다.

> index가 필요한 컬럼을 갖고 있어도, page가 all-visible이 아니면 PostgreSQL은 heap에 내려가 tuple visibility를 다시 확인할 수 있다.

## 흔한 오해와 함정

- "`all-visible`이면 row가 아예 고정됐다" -> 아니다. 나중에 쓰기가 생기면 상태가 다시 바뀔 수 있다.
- "`visibility map`은 row 하나하나의 visible 여부를 적어 둔다" -> 아니다. page 단위 메모다.
- "`all-visible`과 tuple visibility는 같은 말이다" -> 아니다. `all-visible`은 page-level 요약이고, tuple visibility는 row-level MVCC 판정이다.
- "`all-visible`이면 MVCC를 안 쓴다" -> 아니다. MVCC 규칙은 그대로고, 재확인을 줄이는 힌트가 생긴 것뿐이다.
- "`Heap Fetches`가 있으면 visibility map이 고장 났다" -> 꼭 그렇지 않다. 최근 쓰기나 vacuum 타이밍 때문에 자연스럽게 생길 수 있다.

## 실무에서 쓰는 모습

예를 들어 `EXPLAIN ANALYZE`에서 아래처럼 보였다고 하자.

```text
Index Only Scan using idx_orders_status_created_at on orders
Heap Fetches: 37
```

이때 첫 해석은 "인덱스가 틀렸다"가 아니라 아래 쪽이 더 안전하다.

| 관찰 | 초급 해석 | 바로 이어질 질문 |
| --- | --- | --- |
| `Index Only Scan` | 인덱스만으로 끝내는 경로를 우선 탔다 | 필요한 컬럼은 인덱스에 다 있었나? |
| `Heap Fetches: 37` | 일부 page는 all-visible이 아니라 tuple visibility 재확인이 붙었다 | 최근 쓰기 churn이나 vacuum 지연이 있었나? |

그래서 follow-up은 보통 "인덱스를 다시 만들까?"보다
"이 테이블이 최근에 많이 바뀌었나, vacuum이 따라오고 있나?"를 먼저 보는 쪽이 맞다.

## autovacuum와 왜 연결되나요?

visibility map은 시간이 지나도 자동으로 항상 완벽하게 유지되는 메모가 아니다.
`UPDATE`나 `DELETE`가 생기면 어떤 page는 다시 조심해야 해서 `all-visible` 표식이 깨질 수 있고,
그 뒤 autovacuum나 `VACUUM`이 지나가며 정리해야 다시 heap 재확인을 덜 하게 된다.

초급에서는 아래 흐름만 기억하면 충분하다.

| 상황 | visibility map 쪽 변화 | `Index Only Scan`에 보이는 변화 |
| --- | --- | --- |
| 쓰기가 잦아짐 | `all-visible` page가 줄 수 있다 | `Heap Fetches`가 다시 늘 수 있다 |
| autovacuum가 제때 따라옴 | 정리된 page가 다시 늘 수 있다 | heap 재확인이 줄어 더 빨라질 수 있다 |
| autovacuum가 밀림 | 오래 `all-visible`로 못 돌아온 page가 남는다 | 같은 쿼리도 시간이 지나며 느려진 것처럼 보일 수 있다 |

즉 autovacuum는 "백그라운드 청소"라는 운영 용어로만 외우기보다,
**visibility map을 회복시켜 index-only scan이 다시 index 쪽에서 끝나게 도와주는 작업**으로 연결해서 보는 편이 이해가 빠르다.

## 흔한 질문 한 번에 정리

입문자가 많이 섞는 문장을 짧게 정리하면 아래와 같다.

| learner 질문 | 짧은 답 |
| --- | --- |
| "`all-visible`이면 모든 row가 영원히 보인다는 뜻인가요?" | 아니다. 지금 시점의 page-level 상태일 뿐이고, 쓰기가 생기면 다시 바뀔 수 있다. |
| "tuple visibility를 visibility map이 대신 계산하나요?" | 아니다. visibility map은 "이 page는 row별 재검사를 생략해도 될까?"를 돕는 힌트다. |
| "왜 page 얘기랑 row 얘기를 따로 봐야 하나요?" | `all-visible`은 page 단위, MVCC visibility는 row 단위라서 판단 층이 다르기 때문이다. |
| "언제 heap으로 다시 내려가나요?" | page가 all-visible이 아니어서 row-level 확인이 필요할 때다. |

## 더 깊이 가려면

- `Heap Fetches` 숫자를 plan에서 읽는 연습은 [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- MySQL `Using index`와 PostgreSQL `Index Only Scan`을 헷갈린다면 [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- dead tuple, autovacuum, heap fetch 회귀까지 같이 보고 싶다면 [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)

## 한 줄 정리

`visibility map`은 PostgreSQL이 heap page를 다시 열어볼 필요가 적은지 빠르게 판단하려고 쓰는 메모이고, `all-visible`은 그 page가 지금은 heap 재확인 없이 지나갈 가능성이 큰 상태라고 이해하면 된다.
