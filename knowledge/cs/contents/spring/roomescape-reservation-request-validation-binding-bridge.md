---
schema_version: 3
title: roomescape 예약 생성 요청 검증 ↔ Spring MVC 바인딩/Bean Validation 브릿지
concept_id: spring/roomescape-reservation-request-validation-binding-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- request-binding
- bean-validation
- controller-vs-service-boundary
aliases:
- roomescape 예약 요청 DTO 검증
- roomescape RequestBody 바인딩
- roomescape Bean Validation
- 룸이스케이프 예약 생성 요청 검증
- 관리자 예약 API 입력 바인딩
symptoms:
- roomescape 예약 생성에서 @Valid를 어디에 붙여야 할지 모르겠어요
- 예약 생성 API가 controller에 오기 전에 400으로 떨어져서 어디를 봐야 할지 헷갈려요
- RequestBody 검증과 service 규칙 검증이 뒤섞여 PR에서 지적받았어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/mvc-controller-basics
- software-engineering/service-layer-basics
next_docs:
- spring/mvc-controller-basics
- spring/roomescape-transactional-boundary-bridge
- software-engineering/roomescape-validation-vs-domain-rule-bridge
linked_paths:
- contents/spring/spring-mvc-controller-basics.md
- contents/spring/spring-roomescape-validation-400-vs-business-conflict-409-primer.md
- contents/spring/spring-valid-400-vs-message-conversion-400-primer.md
- contents/software-engineering/roomescape-validation-vs-domain-rule-bridge.md
confusable_with:
- software-engineering/roomescape-validation-vs-domain-rule-bridge
- spring/mvc-controller-basics
forbidden_neighbors:
- contents/software-engineering/roomescape-validation-vs-domain-rule-bridge.md
- contents/spring/roomescape-transactional-boundary-bridge.md
expected_queries:
- roomescape 예약 생성 컨트롤러에서 DTO 바인딩과 검증을 어떻게 나눠야 해?
- 예약 생성 API가 컨트롤러 진입 전에 400이면 Spring MVC 어디부터 봐야 해?
- 룸이스케이프에서 RequestBody 검증은 하고 중복 예약 검사는 왜 따로 둬?
- 리뷰어가 controller는 형식만 검사하라고 했는데 roomescape에서는 무슨 뜻이야?
- create reservation 요청 DTO에 어떤 제약을 두고 서비스에는 무엇을 남겨야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 관리자 예약 생성 API를 만들 때
  learner가 RequestBody 바인딩, Bean Validation, controller 진입 전 400,
  service 규칙 검증의 경계를 한 번에 헷갈리는 상황을 풀어주는
  mission_bridge다. 예약 생성 DTO, @Valid 위치, RequestBody 바인딩 실패,
  controller에서는 형식만 보고 service가 정책을 판단해야 한다는 리뷰
  맥락이 이 문서의 핵심 검색 표면이다.
---

# roomescape 예약 생성 요청 검증 ↔ Spring MVC 바인딩/Bean Validation 브릿지

## 한 줄 요약

> roomescape 예약 생성 API에서 Spring MVC는 요청 JSON을 DTO로 바인딩하고 `@Valid`로 입구 규칙을 먼저 거른다. 그 뒤에야 service가 "이미 같은 슬롯이 찼는가" 같은 저장 상태 규칙을 판단한다.

## 미션 시나리오

roomescape 관리자 예약 생성 API를 만들면 학습자는 `ReservationCreateRequest` 같은 DTO에 어디까지 책임을 둘지부터 흔들린다. `name` 공백, 날짜 형식 오류, 인원 수 0 같은 값은 쉽게 DTO 제약으로 보이지만, 중복 예약도 같이 막고 싶어지기 때문이다.

이때 PR에서 자주 나오는 지적은 "controller는 요청을 DTO로 바꾸고 형식 제약만 검사하라"는 말이다. 멘토가 보는 핵심은 검증 자체의 유무가 아니라 검증이 필요한 정보의 종류다. 요청 본문만 보면 알 수 있는 규칙과 repository 조회가 있어야 알 수 있는 규칙을 같은 층에 두면 컨트롤러가 금방 비대해진다.

또 한 가지 흔한 장면은 요청이 service까지 오지도 못하고 `400`으로 끝나는 경우다. 이때 learner는 service의 `if` 문을 먼저 뒤지지만, 실제 출발점은 JSON 형식, 필드명, `@RequestBody`, `@Valid`, DTO 제약 선언인 경우가 많다. roomescape 문맥에서는 이 첫 분기를 잡는 것이 MVC 감각을 만드는 지름길이다.

## CS concept 매핑

| roomescape 장면 | Spring MVC에서 먼저 일어나는 일 | 더 가까운 CS 개념 | 보통 책임 위치 |
| --- | --- | --- | --- |
| JSON 필드명이 DTO와 안 맞음 | 바인딩 실패 또는 변환 실패 | request binding, message conversion | controller 진입 전후 |
| `name`이 비어 있거나 인원 수가 0 | Bean Validation 실패 | input validation | request DTO |
| 같은 날짜와 시간 슬롯이 이미 존재 | 상태 조회 후 충돌 판정 | business rule, domain conflict | service |
| 예외를 어떤 HTTP 상태로 돌릴지 결정 | 실패 의미 번역 | exception mapping, API contract | advice / controller layer |

짧게 외우면 "HTTP 본문을 자바 객체로 옮기는 단계"와 "그 객체로 비즈니스 판단을 하는 단계"를 끊어 읽으면 된다. 전자는 Spring MVC 바인딩과 validation이고, 후자는 service가 담당하는 정책 판단이다.

그래서 `@RequestBody`와 `@Valid`는 roomescape에서 컨트롤러가 해야 할 최소 입구 작업으로 읽는다. 반대로 "이 예약 시간이 이미 찼는가", "취소된 슬롯은 다시 허용하는가" 같은 질문은 저장 상태를 봐야 하므로 service 메소드에 남겨 두는 편이 자연스럽다.

## 미션 PR 코멘트 패턴

- "`@Valid`는 DTO 형식 검증에 쓰고, 중복 예약은 service에서 판단해 보세요."라는 코멘트는 request DTO와 정책 검증의 경계를 나누라는 뜻이다.
- "`400`이 controller에 오기 전 바인딩 단계에서 날 수도 있으니 service부터 의심하지 마세요."라는 코멘트는 Spring MVC 파이프라인을 먼저 보라는 뜻이다.
- "`RequestBody`를 받은 컨트롤러가 repository를 직접 조회하지 말고 service에 위임하세요."라는 코멘트는 HTTP 입구와 도메인 규칙을 분리하라는 뜻이다.
- "`409`로 번역할 충돌과 `400`으로 끝낼 형식 오류를 섞지 마세요."라는 코멘트는 실패 원인을 API 계약에 반영하라는 뜻이다.

## 다음 학습

- Spring MVC 입구 흐름 자체를 복습하려면 [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)을 본다.
- roomescape 예시로 `400`과 `409`를 더 직접 비교하려면 [Spring RoomEscape validation `400` vs business conflict `409` 분리 primer](./spring-roomescape-validation-400-vs-business-conflict-409-primer.md)를 본다.
- 바인딩 전후 `400` 분기를 더 세밀하게 보고 싶으면 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)를 본다.
- 입력 검증과 서비스 규칙 경계를 일반 설계 관점으로 다시 묶으려면 [roomescape 예약 생성 실패 응답 ↔ 입력 검증과 도메인 규칙 경계 브릿지](../software-engineering/roomescape-validation-vs-domain-rule-bridge.md)를 본다.
