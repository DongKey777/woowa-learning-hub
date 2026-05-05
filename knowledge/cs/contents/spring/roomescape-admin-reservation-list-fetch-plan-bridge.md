---
schema_version: 3
title: roomescape 관리자 예약 목록 조회 ↔ fetch plan과 N+1 브릿지
concept_id: spring/roomescape-admin-reservation-list-fetch-plan-bridge
canonical: false
category: spring
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- reservation-list-fetch-plan
- n-plus-one
- projection-vs-entity-loading
aliases:
- roomescape 예약 목록 N+1
- roomescape 관리자 예약 조회 fetch join
- roomescape 예약 목록 EntityGraph
- 룸이스케이프 예약 목록 조회 최적화
- 관리자 예약 목록 projection 분리
symptoms:
- roomescape 예약 목록 API만 호출하면 SQL이 예상보다 많이 찍혀요
- 예약 목록 DTO를 만들 때 member나 theme를 꺼내는 순간 쿼리가 계속 추가돼요
- fetch join을 붙였더니 페이지네이션이 이상해졌다는 리뷰를 받았어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/spring-data-jpa-basics
- spring/spring-persistence-transaction-web-service-repository-primer
next_docs:
- database/n-plus-one-query-detection-solutions
- spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card
- software-engineering/query-model-separation-read-heavy-apis
linked_paths:
- contents/database/n-plus-one-query-detection-solutions.md
- contents/spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md
- contents/spring/spring-dto-projection-vs-entity-loading-readonly-response-mini-card.md
- contents/software-engineering/query-model-separation-read-heavy-apis.md
- contents/spring/spring-controller-entity-return-vs-dto-return-primer.md
confusable_with:
- database/n-plus-one-query-detection-solutions
- spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card
- software-engineering/query-model-separation-read-heavy-apis
forbidden_neighbors: []
expected_queries:
- roomescape 관리자 예약 목록에서 member 이름만 붙였는데 왜 쿼리가 여러 번 나가?
- 예약 목록 API를 JPA로 만들 때 fetch join이랑 EntityGraph 중 어디서 시작해야 해?
- 룸이스케이프 목록 조회에 컬렉션 fetch join을 붙이면 페이지네이션이 왜 깨져?
- 리뷰어가 목록 조회는 projection이나 query model을 보라고 한 이유가 뭐야?
- roomescape admin 예약 조회를 엔티티 그대로 읽으면 어떤 fetch plan 문제가 생겨?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 관리자 예약 목록 조회를 만들다가
  learner가 member, theme, reservationTime 같은 연관 값을 DTO로 꺼내는 순간
  SQL이 늘어나거나 fetch join과 pagination이 충돌하는 장면을 Spring fetch plan
  문제로 묶어 설명하는 mission_bridge다. 예약 목록 N+1, EntityGraph를 붙여야
  하는지, projection으로 분리해야 하는지, 목록 API에서 엔티티를 그대로 끌고
  가도 되는지 같은 자연어 질문이 이 문서의 검색 표면이다.
---

# roomescape 관리자 예약 목록 조회 ↔ fetch plan과 N+1 브릿지

## 한 줄 요약

roomescape 관리자 예약 목록은 "예약 한 건 저장"보다 "여러 연관 값을 한 번에 읽기"가 더 중요한 장면이다. 그래서 이 화면에서 받는 `N+1`, `fetch join + pagination`, `projection으로 빼라`는 리뷰는 모두 fetch plan을 목록 유스케이스에 맞게 드러내라는 말에 가깝다.

## 미션 시나리오

roomescape 미션에서 관리자 예약 목록을 만들면 보통 예약자 이름, 테마 이름, 날짜, 시간, 예약 상태를 한 줄에 같이 보여 주고 싶어진다. 처음에는 `Reservation` 엔티티 리스트를 읽고 DTO로 바꾸면서 `reservation.getMember().getName()`이나 `reservation.getTheme().getName()`을 꺼내는 방식이 가장 자연스러워 보인다.

그런데 이 방식은 데이터가 몇 건 없을 때는 조용히 지나가다가, 목록 건수가 늘거나 페이지 조회가 붙는 순간 문제가 드러난다. SQL 로그에는 예약 목록 조회 1번 뒤에 member, theme 조회가 여러 번 따라붙고, 급하게 `fetch join`을 붙이면 이번에는 pagination 경고나 row 부풀림이 나타난다. PR에서 "목록 조회는 fetch plan을 명시하세요", "엔티티 그대로 말고 projection도 고려해 보세요"라는 코멘트가 붙는 이유가 여기 있다.

## CS concept 매핑

roomescape 관리자 예약 목록은 CS 관점에서 "쓰기 모델을 복원하는 문제"보다 "읽기 유스케이스에 맞는 fetch plan을 고르는 문제"에 가깝다. 핵심은 연관 데이터를 언제, 어떤 단위로, 몇 쿼리로 읽을지 미리 정하는 것이다.

| roomescape 장면 | 더 가까운 Spring/JPA 개념 | 왜 그 개념으로 읽나 |
| --- | --- | --- |
| 예약 목록 DTO에서 member, theme 이름을 순회하며 꺼냄 | N+1, lazy loading | 연관 접근 시점에 쿼리가 뒤늦게 터질 수 있다 |
| 목록용 Repository 메서드에 연관 하나둘만 미리 로딩 | `@EntityGraph` | 기본 조회 메서드에 fetch plan을 선언적으로 붙이기 좋다 |
| JPQL로 목록 조건과 정렬을 이미 직접 작성 | fetch join | 쿼리 의미와 로딩 계획을 한 문장에 같이 둔다 |
| 컬렉션 연관까지 한 번에 끌고 와 페이지로 자름 | collection fetch join + pagination 충돌 | DB LIMIT보다 row duplication 문제가 먼저 생긴다 |
| 목록 화면 전용 컬럼이 계속 늘어남 | projection, query model separation | 쓰기 엔티티보다 읽기 모델이 더 큰 압력을 받는다 |

짧게 외우면, roomescape 목록 API에서 중요한 질문은 "`엔티티를 그대로 읽었나`"보다 "`이 화면에 필요한 값을 어떤 fetch plan으로 준비했나`"다. 목록은 도메인 규칙보다 읽기 모양이 먼저 설계를 밀기 때문에, write model을 억지로 늘리는 것보다 조회 경로를 분리하는 편이 더 단순할 수 있다.

## 미션 PR 코멘트 패턴

- "`Reservation`을 순회하며 연관 이름을 꺼내면 목록에서 N+1이 납니다."라는 코멘트는 DTO 변환 시점 lazy access를 fetch plan으로 앞당기라는 뜻이다.
- "목록 조회는 `@EntityGraph`나 fetch join으로 필요한 연관을 명시하세요."라는 코멘트는 로딩 계획을 repository 경계에 드러내라는 뜻이다.
- "컬렉션 fetch join에 pagination을 바로 붙이면 위험합니다."라는 코멘트는 쿼리 수만 줄이지 말고 결과 row 단위를 먼저 보라는 뜻이다.
- "관리자 목록이 계속 비대해지면 projection이나 query model을 분리해도 됩니다."라는 코멘트는 write entity 하나로 모든 읽기 요구를 버티지 말라는 뜻이다.

## 다음 학습

- N+1을 어떻게 탐지하고 fetch join, `@EntityGraph`, `@BatchSize`를 언제 나눠 쓰는지 보려면 `N+1 Query Detection and Solutions`를 본다.
- DTO 읽기에서 fetch join과 `@EntityGraph`를 빠르게 비교하려면 `Fetch Join vs @EntityGraph Mini Card for DTO Reads`를 이어서 본다.
- 목록 응답을 엔티티 로딩으로 유지할지 projection으로 바로 읽을지 고민되면 `Spring DTO Projection vs Entity Loading Read-Only Response Mini Card`를 본다.
- 관리자 목록 요구가 커져 write model보다 읽기 모델이 더 흔들릴 때는 `Query Model Separation for Read-Heavy APIs`로 넘어간다.
