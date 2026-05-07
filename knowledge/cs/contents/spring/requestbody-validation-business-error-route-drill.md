---
schema_version: 3
title: RequestBody Validation Business Error Route Drill
concept_id: spring/requestbody-validation-business-error-route-drill
canonical: false
category: spring
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/baseball
- missions/blackjack
- missions/lotto
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
review_feedback_tags:
- requestbody-400
- validation-400
- business-409
- route-drill
aliases:
- requestbody validation business error drill
- request body 400 validation 400 business 409 drill
- Spring 400 409 경로 드릴
- @RequestBody @Valid BindingResult drill
- controller before validation error route
symptoms:
- JSON parse 실패, Bean Validation 실패, business conflict를 모두 같은 400으로 처리한다
- '@RequestBody'가 DTO를 만들기 전에 실패한 상황을 service/domain validation 문제로 본다
- 이미 끝난 게임이나 이미 예약된 시간 같은 현재 상태 충돌을 입력 형식 오류와 섞는다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- spring/valid-400-vs-message-conversion-400-primer
- spring/requestbody-400-vs-validation-400-vs-business-409-decision-guide
next_docs:
- spring/bindingresult-local-validation-400-primer
- spring/requestbody-400-before-controller-primer
- software-engineering/backend-api-error-contract-drill
linked_paths:
- contents/spring/spring-valid-400-vs-message-conversion-400-primer.md
- contents/spring/spring-requestbody-400-vs-validation-400-vs-business-409-decision-guide.md
- contents/spring/spring-bindingresult-local-validation-400-primer.md
- contents/spring/spring-requestbody-400-before-controller-primer.md
- contents/software-engineering/backend-api-error-contract-drill.md
- contents/network/http-status-codes-basics.md
confusable_with:
- spring/valid-400-vs-message-conversion-400-primer
- spring/requestbody-400-vs-validation-400-vs-business-409-decision-guide
- software-engineering/backend-api-error-contract-drill
forbidden_neighbors:
- contents/spring/spring-mvc-controller-basics.md
expected_queries:
- Spring에서 RequestBody 400, validation 400, business 409를 드릴로 연습하고 싶어
- JSON parse 실패와 @Valid 실패와 이미 예약됨을 어떻게 구분해?
- 컨트롤러 전에 끝나는 400과 service에서 나는 conflict를 문제로 풀어줘
- BindingResult가 잡는 오류와 못 잡는 오류를 미션 예제로 알려줘
contextual_chunk_prefix: |
  이 문서는 RequestBody validation business error route drill이다. JSON parse
  400, message conversion, @Valid Bean Validation, BindingResult local branch,
  business conflict 409, already finished game, already reserved slot 같은
  질문을 Spring MVC error route 판별 문제로 매핑한다.
---
# RequestBody Validation Business Error Route Drill

> 한 줄 요약: Spring API 오류는 "DTO가 만들어졌는가", "Bean Validation이 실패했는가", "현재 도메인 상태와 충돌했는가" 순서로 보면 400과 409를 덜 섞는다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "JSON 문법 오류도 `@Valid`가 잡나요?" | request body가 DTO로 변환되기 전에 message conversion에서 실패하는 요청 | DTO 생성 전 400과 validation 400을 분리한다 |
| "이미 예약된 시간도 validation error인가요?" | roomescape 예약 생성 DTO는 유효하지만 현재 DB 상태와 충돌하는 상황 | 입력 형식 오류와 business conflict를 나눈다 |
| "끝난 baseball game에 guess를 보내면 400인가요 409인가요?" | request body는 정상인데 game state가 더 이상 guess를 받을 수 없는 흐름 | 현재 resource state conflict로 볼 수 있는지 판단한다 |

**난이도: Beginner**

## 문제 1

상황:

```text
POST /reservations body가 {"date": "2026-05-07", "timeId": } 처럼 JSON 문법이 깨져 있다.
```

답:

message conversion 400이다. DTO가 만들어지기 전이라 `@Valid`나 domain rule까지 도달하지 않는다.

## 문제 2

상황:

```text
body는 JSON이고 DTO도 만들어졌지만 `timeId`가 null이다.
```

답:

Bean Validation 400 후보가 강하다. `@Valid`와 constraint annotation이 이 입력 shape를 검사한다.

## 문제 3

상황:

```text
date/time/theme가 모두 형식상 유효하지만 이미 같은 시간 예약이 존재한다.
```

답:

business conflict 후보가 강하다. 호출자는 다른 시간을 골라야 하므로 409와 안정적인 error code가 더 읽기 좋다.

## 빠른 체크

| 어디서 실패했나 | 후보 |
|---|---|
| JSON parse/type conversion 전 | 400 message conversion |
| DTO 생성 후 constraint 위반 | 400 validation |
| 현재 상태와 충돌 | 409 conflict |
| 권한/로그인 문제 | 401/403 분리 |
