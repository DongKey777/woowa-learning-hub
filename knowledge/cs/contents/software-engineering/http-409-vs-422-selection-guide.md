---
schema_version: 3
title: 409 vs 422 선택 기준 짧은 가이드
concept_id: software-engineering/http-409-vs-422-selection-guide
canonical: false
category: software-engineering
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- status-code-semantics
- conflict-vs-validation
- api-error-contract
aliases:
- 409 vs 422
- http 409 conflict
- http 422 unprocessable content
- business rule violation status code
- beginner status code guide
- 업무 규칙 위반 상태 코드
- 409 422 차이
- conflict vs unprocessable content
- duplicate reservation 409
- invalid state transition 409
- domain validation 422
- semantic validation error
- 상태 충돌 vs 의미 오류
- 초심자 decision table
- beginner error handling primer
symptoms:
- 중복 예약이 409인지 422인지 리뷰 때마다 헷갈려요
- 형식은 맞는데 business rule에 걸리면 무슨 상태 코드를 줘야 할지 모르겠어요
- 상태 코드보다 error code를 먼저 고정하라는 피드백이 왜 나오는지 이해가 안 돼요
intents:
- comparison
- design
prerequisites:
- software-engineering/api-design-error-handling
- software-engineering/exception-handling-basics
- software-engineering/domain-invariants-as-contracts
next_docs:
- software-engineering/roomescape-validation-vs-domain-rule-bridge
- spring/spring-roomescape-validation-400-vs-business-conflict-409-primer
- software-engineering/api-design-error-handling
linked_paths:
- contents/software-engineering/api-design-error-handling.md
- contents/software-engineering/exception-handling-basics.md
- contents/software-engineering/domain-invariants-as-contracts.md
- contents/software-engineering/roomescape-validation-vs-domain-rule-bridge.md
- contents/spring/spring-roomescape-validation-400-vs-business-conflict-409-primer.md
confusable_with:
- software-engineering/roomescape-validation-vs-domain-rule-bridge
- software-engineering/api-design-error-handling
- spring/valid-400-vs-message-conversion-400-primer
forbidden_neighbors:
- contents/software-engineering/api-design-error-handling.md
- contents/software-engineering/exception-handling-basics.md
expected_queries:
- 중복 리소스나 상태 충돌은 언제 409로 보는 게 자연스러워?
- 요청 형식은 맞는데 값 의미가 틀리면 422를 써도 되는 거야?
- 예약 API에서 슬롯 선점과 시간 범위 오류를 다른 상태 코드로 나누는 기준이 뭐야?
- 업무 규칙 위반을 전부 Conflict로 보내지 말라는 말을 어떻게 이해해야 해?
- 400이랑 409랑 422를 초심자 기준으로 빨리 구분하는 방법이 있어?
contextual_chunk_prefix: |
  이 문서는 API 실패 응답을 설계할 때 요청이 현재 상태와 충돌한 것인지,
  요청 내용 자체를 고쳐야 하는 것인지 헷갈리는 학습자에게 409와 422를 가르는
  기준을 결정하게 하는 chooser다. 이미 누가 선점한 건가, 값 형식은 맞는데
  규칙이 깨졌나, 다시 보내면 성공할 수 있나, 400하고는 어디서 갈리나, 중복
  예약은 왜 conflict로 보나 같은 자연어 paraphrase가 본 문서의 상태 코드
  판단에 매핑된다.
---
# 409 vs 422 선택 기준 짧은 가이드

> 한 줄 요약: **같은 요청을 "상태만 바꿔서" 다시 보내면 성공할 수 있으면 `409`, 요청 내용 자체를 고쳐야 하면 `422`**로 먼저 생각하면 초심자 혼동이 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [Software Engineering README: 409 vs 422 선택 기준 짧은 가이드](./README.md#409-vs-422-선택-기준-짧은-가이드)
- [API 설계와 예외 처리](./api-design-error-handling.md)
- [예외 처리 기초](./exception-handling-basics.md)
- [Domain Invariants as Contracts](./domain-invariants-as-contracts.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 409 vs 422, http 409 conflict, http 422 unprocessable content, business rule violation status code, beginner status code guide, 업무 규칙 위반 상태 코드, 409 422 차이, conflict vs unprocessable content, duplicate reservation 409, invalid state transition 409, domain validation 422, semantic validation error, 상태 충돌 vs 의미 오류, 초심자 decision table, beginner error handling primer

## 먼저 잡는 한 줄 멘탈 모델

- `409 Conflict`: **요청 뜻은 이해했지만, 서버의 현재 상태와 충돌한다.**
- `422 Unprocessable Content`: **요청 JSON 모양은 맞지만, 그 내용 자체로는 처리할 수 없다.**

초심자용 첫 질문은 이것 하나면 된다.

`이 요청은 서버 상태가 바뀌면 그대로 다시 시도할 수 있는가?`

## decision table

| 질문 | 더 가까운 코드 | 왜 그렇게 보나 |
|---|---|---|
| 같은 본문으로 나중에 다시 보내면 성공할 수 있나? | `409 Conflict` | 현재 상태 충돌이 핵심이다. |
| 요청 값 자체를 바꿔야만 성공하나? | `422 Unprocessable Content` | 내용 의미가 규칙을 못 맞춘다. |
| 형식부터 틀렸나? | `400 Bad Request` | `409`/`422` 전에 입력 모양 오류다. |

## 자주 만나는 예시

| 상황 | 추천 | 이유 |
|---|---|---|
| 이미 배송된 주문을 취소하려고 함 | `409` | 주문의 현재 상태가 `SHIPPED`라서 충돌한다. |
| 이미 사용한 쿠폰을 다시 사용하려고 함 | `409` | 같은 요청이라도 쿠폰 상태가 문제다. |
| 종료일이 시작일보다 빠른 일정 생성 요청 | `422` | JSON 형식은 맞지만 값 조합이 의미상 잘못됐다. |
| 비밀번호 확인값이 비밀번호와 다름 | `422` | 요청 필드들의 의미 관계가 맞지 않는다. |
| 이메일 형식이 아예 틀림 | `400` | 의미 이전에 형식 검증 단계에서 걸린다. |

## 같은 예시로 보는 before / after

상황: 예약 생성 API

| 상태 | 판단 | 결과 |
|---|---|---|
| before | "업무 규칙 위반은 전부 `409`" | 날짜 범위 오류와 슬롯 선점 충돌이 한 코드에 섞여 호출자가 수정 방향을 읽기 어렵다. |
| after | "상태 충돌인지, 값 의미 오류인지 먼저 분리" | `이미 예약된 시간`은 `409`, `종료 시간이 시작보다 빠름`은 `422`로 갈라져 응답 의도가 선명해진다. |

```http
POST /reservations
Content-Type: application/json

{
  "startAt": "2026-04-27T15:00:00",
  "endAt": "2026-04-27T14:00:00",
  "seatId": 12
}
```

이 요청은 시간 형식은 맞지만 `endAt < startAt`이라서 값 의미가 틀렸다. 이런 경우는 `422`가 더 자연스럽다.

반대로 아래는 값 형태가 아니라 **현재 좌석 상태**가 문제다.

```http
POST /reservations
Content-Type: application/json

{
  "startAt": "2026-04-27T15:00:00",
  "endAt": "2026-04-27T16:00:00",
  "seatId": 12
}
```

이미 같은 시간대에 `seatId=12`가 선점되어 있다면 이 경우는 `409`로 보는 편이 읽기 쉽다.

## 흔한 오해와 함정

- "`422`는 거의 안 쓰니까 전부 `409`로 보내도 된다"라고 생각하기 쉽다.
  - 보정: 팀이 단순화를 위해 `409` 하나로 통일할 수는 있지만, 그때도 "상태 충돌"과 "내용 의미 오류"를 에러 코드나 문서에서 분리해 둬야 호출자가 덜 헷갈린다.
- "`422`는 `@Valid` 실패용이다"라고 오해하기 쉽다.
  - 보정: 초심자 문맥에서는 형식 검증 실패는 보통 `400`으로 먼저 배우는 편이 안전하다. `422`는 **형식은 맞지만 의미가 틀린 값**에 더 가깝다.
- "`중복 이메일`은 무조건 `422`다"라고 단정하기 쉽다.
  - 보정: 이미 존재하는 리소스 상태와 충돌한다고 보면 `409`가 더 자연스럽다. 이 케이스는 팀 기준이 갈릴 수 있으니 API 문서의 예시를 고정해 두는 편이 중요하다.

## 팀 기준을 빠르게 정하는 최소 규칙

1. 형식 오류는 `400`으로 먼저 고정한다.
2. 현재 서버 상태와 부딪히는 규칙은 `409`로 둔다.
3. 값 조합이나 의미 해석이 틀린 규칙은 `422`로 둔다.
4. 애매한 케이스는 상태 코드보다 `error.code`를 먼저 안정적으로 고정한다.

## 다음에 이어서 볼 문서

- [API 설계와 예외 처리](./api-design-error-handling.md) - `@Valid`, `400`, `409` 분리와 에러 응답 포맷을 더 넓게 본다.
- [Domain Invariants as Contracts](./domain-invariants-as-contracts.md) - "업무 규칙"을 상태 코드 이전에 어떤 계약으로 표현할지 이어서 본다.

## 한 줄 정리

**같은 요청을 "상태만 바꿔서" 다시 보내면 성공할 수 있으면 `409`, 요청 내용 자체를 고쳐야 하면 `422`**로 먼저 생각하면 초심자 혼동이 크게 줄어든다.
