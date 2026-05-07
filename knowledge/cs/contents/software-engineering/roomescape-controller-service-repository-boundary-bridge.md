---
schema_version: 3
title: Roomescape Controller / Service / Repository Boundary Bridge
concept_id: software-engineering/roomescape-controller-service-repository-boundary-bridge
canonical: false
category: software-engineering
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 78
mission_ids:
- missions/roomescape
- missions/spring-roomescape
review_feedback_tags:
- roomescape
- layer-boundary
- controller-service-repository
- responsibility-placement
aliases:
- roomescape controller service repository boundary
- roomescape 계층 책임 분리
- 룸이스케이프 컨트롤러 서비스 저장소 경계
- 예약 생성 로직 어느 계층
- controller service repository review bridge
symptoms:
- roomescape 예약 생성 코드가 controller, service, repository에 어떻게 나뉘어야 하는지 모르겠다
- controller에서 repository를 직접 호출해도 되는지 리뷰에서 막혔다
- service가 DTO 변환, 검증, DB 조회, 응답 조립을 모두 들고 있어서 비대해졌다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
next_docs:
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- software-engineering/roomescape-dao-vs-repository-bridge
- spring/roomescape-reservation-request-validation-binding-bridge
linked_paths:
- contents/software-engineering/layered-architecture-basics.md
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
- contents/software-engineering/controller-service-domain-responsibility-split-drill.md
- contents/spring/roomescape-reservation-request-validation-binding-bridge.md
confusable_with:
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- software-engineering/roomescape-dao-vs-repository-bridge
- software-engineering/controller-service-domain-responsibility-split-drill
forbidden_neighbors:
- contents/spring/roomescape-admin-reservation-list-fetch-plan-bridge.md
expected_queries:
- roomescape 예약 생성에서 controller service repository 책임을 어떻게 나눠?
- 컨트롤러가 repository를 직접 호출하지 말라는 리뷰를 CS 개념으로 설명해줘
- 룸이스케이프 서비스가 비대해졌을 때 어디를 먼저 분리해야 해?
- 예약 생성 flow에서 DTO 변환과 도메인 규칙과 DB 접근 경계를 나눠줘
contextual_chunk_prefix: |
  이 문서는 roomescape 예약 생성과 관리자 API를 controller, service,
  repository boundary로 연결하는 mission_bridge다. controller direct
  repository call, service bloat, DTO conversion, domain rule placement,
  persistence boundary, layer responsibility 같은 리뷰 문장을 Spring
  Roomescape 미션의 계층 책임 분리 질문으로 매핑한다.
---
# Roomescape Controller / Service / Repository Boundary Bridge

> 한 줄 요약: roomescape에서 controller는 HTTP 입구, service는 유스케이스 조합, repository는 저장소 접근 계약으로 읽어야 한다.

**난이도: Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "예약 생성 코드가 controller, service, repository에 어떻게 나뉘어야 할지 모르겠어요" | roomescape 예약 생성 flow 첫 레이어 분리 | HTTP 입구, 유스케이스 조합, 저장소 계약을 따로 둔다 |
| "controller에서 repository를 직접 호출하면 왜 리뷰에서 막히나요?" | 얇은 controller와 service 책임 피드백 | controller가 persistence adapter를 직접 잡지 않게 use case 경계를 세운다 |
| "service가 DTO 변환, 검증, DB 조회, 응답 조립을 모두 들고 있어요" | 비대한 service 리팩토링 | domain rule, orchestration, response assembly를 나눠 읽는다 |

## CS concept 매핑

| roomescape 장면 | 더 가까운 계층 질문 |
|---|---|
| `ReservationController`가 `reservationRepository.save()`를 직접 호출 | HTTP adapter가 persistence adapter를 바로 잡고 있다 |
| service가 request DTO를 받아 모든 필드를 직접 꺼내 검증 | 입구 DTO와 도메인 command 경계가 흐리다 |
| repository가 `ReservationResponse`를 바로 반환 | 저장소 계약과 API 응답 모양이 섞인다 |
| controller가 중복 예약을 직접 조회 | use case rule이 controller로 올라왔다 |
| domain 객체가 JPA query method 이름을 안다 | domain이 persistence detail을 안다 |

## 리뷰 신호

- "컨트롤러는 요청을 받고 서비스에 위임하세요"는 얇은 controller를 만들라는 말이다.
- "서비스가 너무 많은 일을 합니다"는 유스케이스 orchestration과 domain rule, DTO 조립을 구분하라는 말이다.
- "Repository가 response DTO를 반환하는 게 맞나요?"는 저장 계약과 화면 응답 계약을 분리하라는 말이다.
- "DAO와 Repository 이름만 바꾸지 마세요"는 역할 경계를 먼저 설명하라는 말이다.

## 분리 순서

1. Controller는 path/body/query를 읽고 service method를 호출한다.
2. Service는 예약 생성 유스케이스를 시작하고 필요한 저장소를 조합한다.
3. Domain은 날짜, 시간, 상태 같은 비즈니스 규칙을 표현한다.
4. Repository는 domain이 필요한 저장/조회 계약을 제공한다.
5. Response DTO 조립은 controller/service 경계에서 일관되게 한 곳으로 정한다.

이렇게 나누면 roomescape 코드 리뷰에서 "어디에 둘지" 논쟁이 줄고, 테스트도 controller contract, service rule, repository mapping으로 나눠진다.
