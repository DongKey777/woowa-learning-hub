---
schema_version: 3
title: Roomescape Admin List Fetch Plan Drill
concept_id: spring/roomescape-admin-list-fetch-plan-drill
canonical: false
category: spring
difficulty: intermediate
doc_role: drill
level: intermediate
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
review_feedback_tags:
- roomescape
- n-plus-one
- fetch-plan
- admin-list
aliases:
- roomescape admin list fetch plan drill
- 룸이스케이프 관리자 목록 N+1 드릴
- reservation list entitygraph fetch join drill
- admin reservation DTO projection drill
- fetch plan review practice
symptoms:
- roomescape 관리자 예약 목록에서 DTO 변환 중 SQL이 여러 번 나간다
- fetch join을 붙였더니 pagination warning이나 row duplication이 걱정된다
- EntityGraph, fetch join, projection 중 무엇을 골라야 할지 리뷰에서 막혔다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- spring/roomescape-admin-reservation-list-fetch-plan-bridge
- spring/spring-data-jpa-basics
next_docs:
- database/n-plus-one-query-detection-solutions
- spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card
- software-engineering/roomescape-admin-list-entity-vs-query-model-vs-response-dto-decision-guide
linked_paths:
- contents/spring/roomescape-admin-reservation-list-fetch-plan-bridge.md
- contents/database/n-plus-one-query-detection-solutions.md
- contents/spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md
- contents/spring/spring-dto-projection-vs-entity-loading-readonly-response-mini-card.md
- contents/software-engineering/roomescape-admin-list-entity-vs-query-model-vs-response-dto-decision-guide.md
- contents/software-engineering/query-model-separation-read-heavy-apis.md
confusable_with:
- spring/roomescape-admin-reservation-list-fetch-plan-bridge
- spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card
- software-engineering/roomescape-admin-list-entity-vs-query-model-vs-response-dto-decision-guide
forbidden_neighbors:
- contents/spring/roomescape-reservation-create-transaction-boundary-drill.md
expected_queries:
- roomescape 관리자 예약 목록 N+1을 문제로 연습하고 싶어
- fetch join EntityGraph projection 중 어떤 선택인지 드릴로 판단해줘
- 예약 목록 DTO 변환에서 쿼리가 늘어나는 코드를 어떻게 고쳐?
- roomescape admin list pagination과 fetch plan을 짧게 점검해줘
contextual_chunk_prefix: |
  이 문서는 Spring Roomescape admin reservation list fetch plan drill이다.
  N+1, lazy loading during DTO mapping, fetch join, EntityGraph, projection,
  pagination warning, row duplication 같은 목록 조회 리뷰 문장을 짧은
  선택 문제로 매핑한다.
---
# Roomescape Admin List Fetch Plan Drill

> 한 줄 요약: 목록 조회는 "몇 건을 보여줄지"와 "연관 값을 언제 읽을지"를 같이 결정해야 한다.

**난이도: Intermediate**

## 문제 1

상황:

```text
reservationRepository.findAll() 뒤 DTO 변환에서 reservation.getMember().getName()을 호출한다.
```

답:

N+1 후보가 맞다. 목록 row마다 lazy association을 건드리면 추가 SELECT가 반복될 수 있으므로 fetch plan을 repository query에 드러내야 한다.

## 문제 2

상황:

```text
예약 목록은 reservation -> member, theme 같은 단일 연관만 필요하고 page size도 작다.
```

답:

`@EntityGraph`나 fetch join 후보가 된다. 단일 연관을 미리 로딩해 DTO 변환 중 추가 쿼리를 막는 목적이면 자연스럽다.

## 문제 3

상황:

```text
관리자 목록에 결제 내역, 쿠폰, 좌석 목록 같은 컬렉션까지 한 번에 보여주려고 한다.
```

답:

컬렉션 fetch join과 pagination 충돌을 먼저 의심한다. 이때는 projection, 2-step query, query model 분리 후보로 넘어가는 편이 안전하다.

## 빠른 체크

| 신호 | 먼저 볼 선택 |
|---|---|
| 단일 연관 이름 몇 개만 필요 | `@EntityGraph` / fetch join |
| 컬렉션을 같이 가져오며 page를 자름 | 2-step query 또는 projection |
| 화면 전용 컬럼이 계속 늘어남 | query model separation |
| DTO 변환 중 SQL이 반복됨 | lazy access 위치와 fetch plan |
