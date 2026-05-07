---
schema_version: 3
title: '로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나'
concept_id: security/log-masking-basics
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 70
mission_ids: []
review_feedback_tags:
- log masking basics
- authorization header masking
- bearer token masking
- error log masking
aliases:
- log masking basics
- authorization header masking
- bearer token masking
- error log masking
- log redaction primer
- before after masking example
- authorization header before after
- exception log redaction
- credential leak in logs
- beginner security logging
- token redaction
- secret redaction
symptoms: []
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/security/secrets-management-basics.md
- contents/security/api-key-basics.md
- contents/security/secret-scanning-credential-leak-response.md
- contents/security/audit-logging-auth-authz-traceability.md
- contents/security/auth-observability-primer-bridge.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- '로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나 핵심 개념을 설명해줘'
- log masking basics가 왜 필요한지 알려줘
- '로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나 실무 설계 포인트는 뭐야?'
- log masking basics에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: '이 문서는 security 카테고리에서 로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나를 다루는 primer 문서다. 로그 마스킹의 핵심은 "문제 재현에 필요한 최소 정보만 남기고, 재사용 가능한 비밀은 남기지 않는 것"이다. 검색 질의가 log masking basics, authorization header masking, bearer token masking, error log masking처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.'
---
# 로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나

> 한 줄 요약: 로그 마스킹의 핵심은 "문제 재현에 필요한 최소 정보만 남기고, 재사용 가능한 비밀은 남기지 않는 것"이다.

**난이도: 🟢 Beginner**

관련 문서:

- [시크릿 관리 기초: API 키와 비밀번호를 코드에 넣으면 안 되는 이유](./secrets-management-basics.md)
- [API 키 기초](./api-key-basics.md)
- [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md)
- [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
- [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)
- [Security 카테고리 README](./README.md#기본-primer)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: log masking basics, authorization header masking, bearer token masking, error log masking, log redaction primer, before after masking example, authorization header before after, exception log redaction, credential leak in logs, beginner security logging, token redaction, secret redaction, log sanitization, log masking beginner, 로그를 남길 때 어디까지 가려야 하나

## 핵심 개념

초보자가 로그 마스킹을 어려워하는 이유는 보통 둘 중 하나다.

- "디버깅하려면 많이 남겨야 하는 것 아닌가?"
- "전부 지우면 원인 분석이 안 되는 것 아닌가?"

먼저 이 기준만 고정하면 된다.

> 로그는 `문제 원인`을 남기는 곳이지, `로그인 증명`이나 `비밀 원문`을 보관하는 곳이 아니다.

즉 남겨야 하는 것은 대개 이런 정보다.

- 어떤 요청이었는가
- 어느 사용자/세션/요청 ID였는가
- 어떤 엔드포인트에서 실패했는가
- 결과가 `401`인지 `403`인지 `500`인지

반대로 남기면 안 되는 것은 이런 정보다.

- `Authorization` header 원문
- access token / refresh token 원문
- API key 원문
- 비밀번호, secret, cookie 원문

## 30초 판단표

| 로그 값 | 그대로 남겨도 되나 | 왜 위험한가 | 대신 남길 것 |
|---|---|---|---|
| `Authorization: Bearer <token>` 전체 | 아니오 | 토큰 재사용이 가능할 수 있다 | scheme, 일부 prefix, token hash/jti |
| `Cookie`, `Set-Cookie` 전체 | 아니오 | 세션 탈취로 이어질 수 있다 | cookie 이름, 존재 여부, 속성 일부 |
| 에러 메시지 안의 API key / password / DSN | 아니오 | 운영 로그가 곧 유출 경로가 된다 | 필드 이름, 실패 이유, request id |
| 요청 경로, status code, request id | 보통 예 | 재사용 가능한 비밀이 아니다 | 그대로 남겨도 된다 |

## 먼저 머리에 넣을 한 장

같은 장애를 로그로 남기더라도 목표는 두 개를 동시에 만족하는 것이다.

| 목표 | 남겨야 하는 것 | 지워야 하는 것 |
|---|---|---|
| 원인 파악 | `status`, `path`, `request_id`, `error_code` | 토큰 원문, 비밀번호 원문, 쿠키 원문 |
| 반복 여부 추적 | `token_fingerprint`, `upstream_request_id`, `user_id` | 다시 쓸 수 있는 credential 전체 문자열 |

초보자 기준으로는 이 한 줄만 기억하면 된다.

> 로그는 "무슨 요청이 왜 실패했는가"를 남기는 곳이지, "다시 로그인할 수 있는 비밀"을 백업하는 곳이 아니다.

## Before / After 카드

### 1. Authorization 헤더

잘못된 로그:

```text
request failed
method=GET path=/api/orders/42
Authorization=Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
status=401
```

권장 로그:

```text
request failed
method=GET path=/api/orders/42
authorization_scheme=Bearer
authorization_present=true
token_fingerprint=sha256:8f3c2d1a
status=401 request_id=req-13f2
```

핵심은 `토큰 원문`이 아니라 `토큰이 있었는지`, `어떤 종류였는지`, `같은 토큰이 반복되는지`만 남기는 것이다.

한눈 비교:

| 보고 싶은 것 | 잘못 남긴 값 | 안전하게 남길 값 |
|---|---|---|
| 토큰이 있었나 | `Authorization=Bearer eyJ...` | `authorization_present=true` |
| 어떤 방식이었나 | `Bearer eyJ...` | `authorization_scheme=Bearer` |
| 같은 토큰이 반복되나 | 토큰 원문 전체 비교 | `token_fingerprint=sha256:8f3c2d1a` |

### 2. 에러 로그

잘못된 로그:

```text
ExternalApiException: 401 Unauthorized
request headers={Authorization=Bearer sk_live_abcd1234, X-Client-Id=billing-batch}
response body={"error":"invalid token","token":"sk_live_abcd1234"}
```

권장 로그:

```text
ExternalApiException: 401 Unauthorized
upstream=billing-api
auth_header_present=true
auth_header_masked=Bearer ****
response_error_code=invalid_token
request_id=req-77aa upstream_request_id=up-91d0
```

핵심은 "무엇이 틀렸는가"를 남기고, "다시 쓸 수 있는 값"은 지우는 것이다.

같은 에러를 더 안전하게 옮기면 보통 이렇게 바뀐다.

## Before / After 카드 (계속 2)

| 로그 목적 | before | after |
|---|---|---|
| 인증 헤더 존재 확인 | `Authorization=Bearer sk_live_abcd1234` | `auth_header_present=true` |
| 어떤 upstream 호출이었나 | headers/raw body 전체 | `upstream=billing-api` |
| 실패 이유 확인 | 응답 body 전체 dump | `response_error_code=invalid_token` |
| 운영 추적 | 없음 | `request_id`, `upstream_request_id` |

### 3. "이 정도면 충분한가?" 빠른 예시 카드

| 상황 | before | after |
|---|---|---|
| 브라우저 API `401` | `Authorization=Bearer eyJ...` | `authorization_present=true status=401 request_id=req-1004` |
| 외부 결제 API 실패 | `response body={\"token\":\"sk_live_...\"}` | `response_error_code=invalid_token upstream_request_id=up-91d0` |
| DB 연결 실패 | `jdbc:mysql://...:password=secret123` | `db_connect_failed datasource=orders-main reason=auth_failed` |

이 표의 의도는 "무조건 짧게 남기라"가 아니다. `원인 파악용 필드`와 `재사용 가능한 비밀`을 분리해 보라는 뜻이다.

## 자주 헷갈리는 포인트

### "앞 4글자 정도는 남겨도 되나요?"

원문 대부분을 남기면 안 된다. 다만 운영에서 같은 credential 반복 여부를 보려면 아래 정도는 허용할 수 있다.

- scheme 이름(`Bearer`, `Basic`)
- 존재 여부(`authorization_present=true`)
- 짧은 fingerprint/hash
- 정말 필요하면 매우 짧은 prefix

prefix를 남기더라도 "원문 복원에 도움이 되지 않는 수준"이어야 한다.

초보자라면 prefix보다 fingerprint를 먼저 고르는 편이 안전하다. prefix는 습관처럼 길어지기 쉽지만, fingerprint는 원문 복원 가능성을 훨씬 낮춘다.

### "에러 stack trace는 원래 길게 찍는 것 아닌가요?"

stack trace 자체보다 위험한 것은 예외 메시지 안에 민감값이 섞여 들어오는 경우다.

예를 들면 이런 값이 흔히 섞인다.

- 외부 API 호출용 URL query string의 `token`
- DB 연결 문자열의 password
- upstream 응답 body 안의 API key

그래서 `예외를 로깅하기 전에 메시지를 sanitize`하는 단계가 필요하다.

### "마스킹하면 디버깅이 너무 어려워지지 않나요?"

그래서 보통 `원문` 대신 `join 가능한 식별자`를 남긴다.

- `request_id`
- `user_id` 또는 `tenant_id`
- `token_fingerprint`
- `upstream_request_id`
- `status`, `error_code`

이 정도면 초보자도 "무슨 요청에서 왜 실패했는지"는 볼 수 있고, 비밀 원문까지 로그에 남기지 않아도 된다.

반대로 아래 값은 디버깅용처럼 보여도 실제로는 위험하다.

- `Authorization` 전체 문자열
- 외부 API 응답 body 전체 dump
- DB 연결 문자열 전체
- `Cookie` / `Set-Cookie` 전체

## 실무 체크리스트

1. `Authorization`, `Cookie`, `Set-Cookie`, `password`, `secret`, `token` 필드는 기본 마스킹 대상으로 둔다.
2. 예외 메시지와 외부 API 응답 body를 그대로 로그에 붙이지 않는다.
3. 원문 대신 `request_id`, `status`, `error_code`, `token_fingerprint` 같은 join key를 남긴다.
4. "개발 환경이라서 괜찮다"는 예외를 오래 두지 않는다.

## 작은 코드 예시

```java
public String maskAuthorization(String authorizationHeader) {
    if (authorizationHeader == null || authorizationHeader.isBlank()) {
        return "absent";
    }
    String[] parts = authorizationHeader.split(" ", 2);
    String scheme = parts[0];
    return scheme + " ****";
}
```

이 함수의 목적은 "로그에 안전한 요약"을 만드는 것이지, 원문 일부를 예쁘게 보여 주는 것이 아니다.

## 더 깊이 가려면

- 로그 설계와 audit evidence를 더 보려면 [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
- 유출 이후 회전/폐기 대응까지 보려면 [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md)
- auth signal / decision / audit 구분부터 다시 잡으려면 [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)

## 면접/시니어 질문 미리보기

> Q: Authorization 헤더를 왜 그대로 남기면 안 되나요?
> 의도: bearer token이 사실상 비밀번호처럼 재사용될 수 있다는 점을 이해하는지 확인
> 핵심: 로그 유출만으로도 토큰 재사용 공격이 가능해질 수 있기 때문이다.

> Q: 마스킹하면 디버깅 정보가 부족해지지 않나요?
> 의도: 원문과 진단 정보의 차이를 구분하는지 확인
> 핵심: 원문 대신 request id, status, error code, fingerprint를 남기면 된다.

## 한 줄 정리

로그 마스킹은 "아무것도 남기지 않는 것"이 아니라, 원인 분석에 필요한 식별자만 남기고 재사용 가능한 비밀 원문은 버리는 습관이다.
