---
schema_version: 3
title: '401 / 403 / 404 / CORS 응답 분기 마이크로 드릴'
concept_id: security/auth-response-code-triage-micro-drill
canonical: false
category: security
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 72
mission_ids: []
review_feedback_tags:
- auth-response-code
- cors-vs-auth-failure
- concealment-404
aliases:
- 401 403 404 CORS drill
- 인증 인가 응답 코드 분기
- CORS인지 401인지
- forbidden not found concealment
- auth failure micro drill
symptoms:
- 브라우저 콘솔에는 CORS가 보이는데 실제 서버 응답은 401인지 403인지 모르겠다
- 로그인 안 됨과 권한 없음과 존재 숨김 404를 구분하지 못한다
- API 에러 코드를 보안 정책과 사용자 메시지로 연결하지 못한다
intents:
- drill
- troubleshooting
prerequisites:
- security/auth-failure-response-401-403-404
- security/cors-basics
next_docs:
- security/cookie-cors-auth-anonymous-symptom-router
- security/browser-401-vs-302-login-redirect-guide
- security/concealment-404-entry-cues
linked_paths:
- contents/security/auth-failure-response-401-403-404.md
- contents/security/cors-basics.md
- contents/security/cors-samesite-preflight.md
- contents/security/cookie-cors-auth-anonymous-symptom-router.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/security/concealment-404-entry-cues.md
- contents/spring/spring-api-401-vs-browser-302-beginner-bridge.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- 401 403 404 CORS를 짧은 문제로 구분 연습하고 싶어
- 브라우저에는 CORS라고 뜨는데 실제 auth 실패인지 어떻게 봐?
- 권한 없는 리소스를 403으로 줄지 404로 숨길지 판단하는 연습이 필요해
- 로그인 안 됨과 권한 없음 응답을 초급자 관점에서 드릴로 풀어줘
contextual_chunk_prefix: |
  이 문서는 401, 403, concealment 404, CORS 브라우저 차단을 짧은 문제로
  구분하는 security drill이다. CORS처럼 보이는 auth failure, 로그인 안 됨,
  권한 없음, 리소스 존재 숨김, browser redirect 같은 질의를 응답 코드와
  보안 정책 분기 연습으로 연결한다.
---
# 401 / 403 / 404 / CORS 응답 분기 마이크로 드릴

> 한 줄 요약: 401은 "누구인지 모름", 403은 "누구인지는 알지만 허용 안 됨", concealment 404는 "존재 자체를 숨김", CORS는 브라우저가 응답을 JS에 못 넘기는 전송 정책 문제다.

**난이도: 🟢 Beginner**

## 문제 1

상황:

```text
Authorization 헤더가 없다.
API는 로그인 필요 endpoint다.
```

답:

`401 Unauthorized`가 자연스럽다. 인증이 없다.

## 문제 2

상황:

```text
로그인은 되어 있다.
USER role인데 ADMIN API를 호출했다.
```

답:

`403 Forbidden`이 자연스럽다. 인증은 됐지만 권한이 없다.

## 문제 3

상황:

```text
다른 사용자의 비공개 주문 id를 추측해서 호출했다.
서비스 정책상 존재 여부를 숨기고 싶다.
```

답:

`404 Not Found` concealment를 고려한다. 단, 내부 audit log에는 deny reason을 남겨야 한다.

## 문제 4

상황:

```text
서버는 401을 보냈지만 브라우저 콘솔에는 CORS error만 보인다.
```

답:

서버 auth 실패와 브라우저 CORS 노출 실패를 분리한다. Network 탭에서 실제 status, preflight, CORS response headers를 확인한다.

## 빠른 체크

```text
1. Network 탭에 실제 HTTP status가 보이는가
2. preflight OPTIONS가 실패했는가 actual request가 실패했는가
3. credential/cookie가 필요한 요청인가
4. 인증 없음인가 권한 없음인가 존재 숨김인가
```

## 한 줄 정리

브라우저 메시지만 보지 말고 실제 HTTP status와 인증/인가 상태를 함께 봐야 401, 403, 404, CORS가 갈린다.
