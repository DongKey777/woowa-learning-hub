---
schema_version: 3
title: Backend API Error Contract Drill
concept_id: software-engineering/backend-api-error-contract-drill
canonical: false
category: software-engineering
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
- missions/backend
review_feedback_tags:
- api-error-contract
- status-code
- validation-vs-business-rule
- problem-detail
aliases:
- backend API error contract drill
- API error response status code drill
- 400 409 422 backend drill
- validation business rule error drill
- 백엔드 API 예외 계약 드릴
symptoms:
- 400, 401, 403, 404, 409, 422를 controller 예외 이름 기준으로 고른다
- @Valid 입력 오류와 service/domain 업무 규칙 실패를 같은 error response로 처리한다
- API 실패 응답에 호출자가 재시도, 수정, 충돌 해결 중 무엇을 해야 하는지 드러나지 않는다
intents:
- drill
- comparison
- design
prerequisites:
- software-engineering/api-design-error-handling
- network/http-status-codes-basics
next_docs:
- spring/problemdetail-error-response-design
- software-engineering/api-contract-testing
- security/authentication-authorization-session-foundations
linked_paths:
- contents/software-engineering/api-design-error-handling.md
- contents/network/http-status-codes-basics.md
- contents/spring/spring-problemdetail-error-response-design.md
- contents/software-engineering/api-contract-testing-consumer-driven.md
- contents/security/authentication-authorization-session-foundations.md
confusable_with:
- software-engineering/api-design-error-handling
- spring/problemdetail-error-response-design
- network/http-status-codes-basics
forbidden_neighbors:
- contents/software-engineering/service-layer-basics.md
expected_queries:
- backend API error contract를 400 409 422 문제로 연습하고 싶어
- @Valid 오류와 domain business rule 실패를 status code로 어떻게 나눠?
- duplicate submit과 validation error를 같은 400으로 내려도 되는지 드릴해줘
- API 실패 응답에 error code와 message를 어떻게 남겨야 해?
- spring-roomescape 예외 처리를 problem detail contract로 연습해줘
contextual_chunk_prefix: |
  이 문서는 backend API error contract drill이다. 400 vs 409 vs 422,
  validation vs business rule, ProblemDetail, error code taxonomy, retryable
  vs conflict 같은 미션 리뷰 문장을 API 계약 판별 문제로 매핑한다.
---
# Backend API Error Contract Drill

> 한 줄 요약: API error contract는 "어떤 예외가 났나"보다 호출자가 "입력을 고칠지, 로그인할지, 권한을 받을지, 충돌을 해결할지"를 알게 만드는 계약이다.

**난이도: Beginner**

## 문제 1

상황:

```text
필수 필드가 빠진 요청과 이미 예약된 시간 선택이 모두 400으로 내려간다.
```

답:

필수 필드 누락은 입력 형식/validation 문제이고, 이미 예약됨은 현재 자원 상태와 충돌한 business rule일 수 있다.
후자는 보통 409 conflict 후보로 분리해 호출자가 다른 시간 선택을 하도록 알려야 한다.

## 문제 2

상황:

```text
로그인하지 않은 사용자와 로그인했지만 관리자 권한이 없는 사용자가 같은 403을 받는다.
```

답:

인증 실패와 인가 실패가 섞였다. principal이 없으면 401, principal은 있지만 권한이 없으면 403을 먼저 고려한다.
존재 숨김 정책이 있으면 404 concealment는 별도로 문서화한다.

## 문제 3

상황:

```text
같은 idempotency key인데 request body hash가 다르다.
```

답:

단순 validation error가 아니라 같은 key로 다른 요청을 보낸 conflict다.
409와 stable error code를 주고, 새 key를 쓰거나 기존 요청 body를 맞추라는 의미를 드러낸다.

## 빠른 체크

| 실패 | 후보 응답 |
|---|---|
| JSON shape, type, required field | 400 |
| unauthenticated | 401 |
| authenticated but forbidden | 403 |
| duplicate/current state conflict | 409 |
| syntactically valid but domain semantic invalid | 422 후보 |
