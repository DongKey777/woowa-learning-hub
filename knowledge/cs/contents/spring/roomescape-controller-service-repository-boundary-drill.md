---
schema_version: 3
title: Roomescape Controller / Service / Repository Boundary Drill
concept_id: spring/roomescape-controller-service-repository-boundary-drill
canonical: false
category: spring
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/roomescape
- missions/spring-roomescape
review_feedback_tags:
- roomescape
- layer-boundary
- controller-service-repository
- review-drill
aliases:
- roomescape layer boundary drill
- 룸이스케이프 계층 책임 드릴
- controller service repository boundary drill
- 예약 생성 책임 분리 문제
- Spring Roomescape responsibility drill
symptoms:
- 리뷰에서 controller service repository 책임을 나누라는 말을 받았지만 구체 예시가 필요하다
- reservation 생성 흐름에서 어떤 코드가 어느 계층에 있어야 하는지 헷갈린다
- 테스트를 controller test, service test, repository test 중 어디에 둘지 판단이 느리다
intents:
- drill
- troubleshooting
- design
prerequisites:
- spring/mvc-controller-basics
- software-engineering/roomescape-controller-service-repository-boundary-bridge
next_docs:
- software-engineering/controller-service-domain-responsibility-split-drill
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- software-engineering/repository-dao-boundary-review-drill
linked_paths:
- contents/spring/spring-mvc-controller-basics.md
- contents/software-engineering/roomescape-controller-service-repository-boundary-bridge.md
- contents/software-engineering/controller-service-domain-responsibility-split-drill.md
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
- contents/software-engineering/repository-dao-boundary-review-drill.md
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
confusable_with:
- software-engineering/controller-service-domain-responsibility-split-drill
- software-engineering/roomescape-controller-service-repository-boundary-bridge
- software-engineering/repository-dao-boundary-review-drill
forbidden_neighbors:
- contents/spring/roomescape-admin-reservation-list-fetch-plan-bridge.md
expected_queries:
- roomescape controller service repository 책임 분리를 문제로 연습하고 싶어
- 예약 생성 코드가 어느 계층에 있어야 하는지 예제로 판단해줘
- controller가 repository를 바로 호출하는 코드 리뷰 드릴을 줘
- Spring roomescape에서 서비스 비대화 피드백을 짧은 문제로 풀어줘
contextual_chunk_prefix: |
  이 문서는 Spring Roomescape layer boundary drill이다. controller가
  repository를 직접 호출, service bloat, response DTO assembly, domain rule
  placement, repository contract 같은 리뷰 문장을 짧은 판별 문제로 바꾼다.
---
# Roomescape Controller / Service / Repository Boundary Drill

> 한 줄 요약: 코드를 어느 계층에 둘지 모르면 "HTTP를 아는가, 유스케이스를 조합하는가, 저장소 세부를 아는가"를 먼저 묻는다.

**난이도: Beginner**

## 문제 1

상황:

```text
ReservationController.create()가 ReservationRepository.findByDateAndTime()을 호출해 중복을 검사한다.
```

답:

controller 책임을 넘었다. 중복 예약은 현재 저장 상태를 조회해야 하는 유스케이스 규칙이므로 service에서 repository를 호출해 판단하는 편이 낫다.

## 문제 2

상황:

```text
ReservationRepository.findAllForAdminPage()가 ReservationResponse DTO를 반환한다.
```

답:

목록 조회 전용 query model이면 의도적으로 분리할 수 있지만, 일반 domain repository 계약처럼 두면 API 응답 모양이 저장소 경계로 새어 들어간다. 조회 전용 repository인지 domain repository인지 이름과 위치로 드러내야 한다.

## 문제 3

상황:

```text
ReservationService.create(requestDto)가 requestDto.getDate(), getTimeId(), getThemeId()를 모두 꺼내고 responseDto까지 만든다.
```

답:

처음엔 가능하지만 비대화 신호다. service는 command나 필요한 primitive를 받아 유스케이스를 조합하고, response 조립은 일관된 경계로 분리할 후보가 된다.

## 빠른 체크

| 질문 | 더 가까운 위치 |
|---|---|
| HTTP status, request body binding을 아는가 | controller |
| 예약 생성이라는 유스케이스 순서를 조합하는가 | service |
| 날짜/시간/상태 규칙을 지키는가 | domain |
| SQL, JPA, row mapping을 아는가 | repository / DAO |
