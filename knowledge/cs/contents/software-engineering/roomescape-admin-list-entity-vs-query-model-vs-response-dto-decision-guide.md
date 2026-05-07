---
schema_version: 3
title: roomescape 관리자 예약 목록 Entity vs Query Model vs Response DTO 결정 가이드
concept_id: software-engineering/roomescape-admin-list-entity-vs-query-model-vs-response-dto-decision-guide
canonical: false
category: software-engineering
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/roomescape
review_feedback_tags:
- admin-list-read-model
- query-model-separation
- response-dto-boundary
aliases:
- roomescape 관리자 예약 목록 read model 결정
- roomescape admin list query model
- roomescape 예약 목록 entity response dto 구분
- 룸이스케이프 관리자 목록 조회 모델 분기표
- roomescape admin row view response 분리
symptoms:
- roomescape 관리자 예약 목록을 만들 때 엔티티를 그대로 읽을지 조회 전용 모델을 둘지 응답 DTO만 만들지 기준이 헷갈려요
- 리뷰어가 projection이나 query model을 보라고 했는데 response DTO만 나누면 안 되는지 모르겠어요
- roomescape 예약 목록 코드에서 Entity, RowView, Response가 다 비슷해 보여 무엇을 남길지 판단이 안 돼요
intents:
- comparison
- design
- mission_bridge
prerequisites:
- software-engineering/dto-vo-entity-basics
- software-engineering/query-model-separation-read-heavy
next_docs:
- spring/roomescape-admin-reservation-list-fetch-plan-bridge
- software-engineering/query-model-separation-read-heavy
- software-engineering/command-dto-vs-query-view-naming-checklist
- spring/controller-entity-return-vs-dto-return-primer
linked_paths:
- contents/spring/roomescape-admin-reservation-list-fetch-plan-bridge.md
- contents/software-engineering/query-model-separation-read-heavy-apis.md
- contents/software-engineering/command-dto-vs-query-view-naming-checklist.md
- contents/spring/spring-controller-entity-return-vs-dto-return-primer.md
confusable_with:
- spring/roomescape-admin-reservation-list-fetch-plan-bridge
- software-engineering/query-model-separation-read-heavy
- software-engineering/command-dto-vs-query-view-naming-checklist
- spring/controller-entity-return-vs-dto-return-primer
forbidden_neighbors: []
expected_queries:
- roomescape 관리자 예약 목록에서 Reservation 엔티티를 그대로 반환하지 말라는 리뷰는 어떤 선택을 하라는 뜻이야?
- roomescape 목록 조회는 response dto만 분리하면 충분한지 query model까지 가야 하는지 한 표로 보고 싶어
- 관리자 예약 목록에서 row view, response, entity를 각각 언제 쓰는지 기준을 알려줘
- roomescape admin 목록 API를 만들 때 fetch plan 문제와 응답 계약 문제를 어디서 갈라야 해?
- 예약 목록 조회 코드에서 projection으로 바로 읽을지 엔티티를 읽고 응답으로 바꿀지 어떻게 판단해?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 관리자 예약 목록 API를 만들며
  Reservation 엔티티, 조회 전용 RowView 또는 Query Model, 최종 Response DTO를
  어디서 나눌지 헷갈리는 학습자를 위한 chooser다. roomescape admin list query
  model, 엔티티 그대로 반환해도 되는지, projection과 response dto 차이, fetch
  plan 문제와 API 계약 문제를 어떻게 분리하는지 같은 자연어 질문을 목록 조회
  설계 분기표로 연결한다.
---
# roomescape 관리자 예약 목록 Entity vs Query Model vs Response DTO 결정 가이드

## 한 줄 요약

> roomescape 관리자 예약 목록에서 `Entity`는 규칙을 지키는 저장 모델, `Query Model`은 목록이 읽기 좋은 모양, `Response DTO`는 밖으로 약속한 JSON 계약이므로 "비슷하게 생겼다"가 아니라 "왜 바뀌는가"로 나눠야 한다.

## 결정 매트릭스

| 지금 부딪힌 장면 | 먼저 잡을 모델 | 왜 그 모델이 맞나 |
| --- | --- | --- |
| 목록 화면에 필요한 필드와 조인 구조가 계속 바뀐다 | Query Model | 예약자 이름, 테마명, 상태 라벨처럼 읽기 요구가 저장 규칙보다 먼저 설계를 밀고 있다 |
| API 응답 필드명, null 정책, 외부 계약을 고정해야 한다 | Response DTO | 클라이언트와의 약속은 SQL shape나 엔티티 필드와 분리하는 편이 안전하다 |
| 예약 취소 가능 여부, 상태 전이, 불변식이 중심이다 | Entity | 이 축은 목록 표시보다 쓰기 규칙과 일관성이 핵심이다 |
| N+1, fetch join, projection 이야기가 PR에서 계속 나온다 | Query Model + fetch plan | 지금 문제는 규칙보다 읽기 경로 최적화이므로 목록 전용 읽기 모델을 의심해야 한다 |
| 엔티티를 그대로 내보내면 당장은 편하지만 화면 요구와 API 계약이 함께 흔들린다 | Response DTO 분리부터 | 처음 단계에서는 응답 계약을 먼저 끊고, 목록 요구가 커지면 Query Model까지 분리한다 |

짧게 외우면 `Entity`는 "지켜야 할 규칙", `Query Model`은 "읽기 좋은 모양", `Response DTO`는 "보여 주는 약속"이다.

## 흔한 오선택

`Entity`를 그대로 응답으로 내보내면 목록 화면 요구가 저장 모델을 끌고 다니기 시작한다.
roomescape 관리자 목록은 예약자 이름, 테마명, 상태 텍스트처럼 읽기 편의가 계속 늘어나기 쉬워서, write model에 조회 전용 관심사가 새기 쉽다.

반대로 `Response DTO`만 만들고 내부 읽기 경로는 그대로 `Entity` 순회에 기대면, 외부 계약은 분리됐어도 N+1과 fetch plan 문제는 남는다.
리뷰에서 "projection으로 빼라", "목록은 query model이 더 자연스럽다"는 말은 JSON 클래스 이름을 바꾸라는 뜻이 아니라 읽기 경로 자체를 따로 세우라는 뜻일 때가 많다.

또 `Query Model`과 `Response DTO`를 완전히 같은 것으로 보는 실수도 흔하다.
둘 다 필드 몇 개 가진 타입처럼 보여도, 전자는 조회 SQL과 화면 조합 압력 때문에 바뀌고 후자는 API 계약 때문에 바뀌므로 변경 이유가 다르다.

## 다음 학습

- 목록 조회에서 왜 fetch plan이 먼저 문제 되는지 roomescape 장면으로 다시 묶으려면 [roomescape 관리자 예약 목록 조회 ↔ fetch plan과 N+1 브릿지](../spring/roomescape-admin-reservation-list-fetch-plan-bridge.md)를 본다.
- 같은 DB 안에서 query repository를 언제 꺼내는지 더 일반화해서 보려면 [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)를 읽는다.
- `RowView`, `Response`, `Command` 같은 이름 경계를 정리하려면 [Command DTO Vs Query View Naming Checklist](./command-dto-vs-query-view-naming-checklist.md)로 이어간다.
- controller가 엔티티를 그대로 반환하면 왜 위험한지 Spring 응답 관점에서 보고 싶다면 [Controller Entity Return Vs DTO Return Primer](../spring/spring-controller-entity-return-vs-dto-return-primer.md)를 본다.
