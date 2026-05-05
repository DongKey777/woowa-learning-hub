---
schema_version: 3
title: 컨트롤러 미진입 원인 라우터
concept_id: spring/controller-not-hit-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/roomescape
- missions/baseball
- missions/blackjack
review_feedback_tags:
- requestbody-pre-controller-400
- content-type-contract
- security-pre-controller-block
aliases:
- 컨트롤러 전에 요청이 끝나는 이유
- controller 로그 안 찍힘 원인
- 스프링 컨트롤러까지 못 감
- 요청이 컨트롤러 전에 막힘
- requestbody 전에 끊기는 것 같음
- handler 전에 에러가 남
symptoms:
- 컨트롤러 첫 줄 로그가 아예 안 찍혀요
- JSON 요청을 보냈는데 서비스까지 가지도 않고 바로 400이나 415가 떠요
- 브라우저에서는 요청이 나가는데 컨트롤러 breakpoint가 한 번도 안 걸려요
- 로그인은 한 것 같은데 관리자 API가 302나 403으로 먼저 끝나요
intents:
- symptom
- troubleshooting
prerequisites:
- spring/mvc-controller-basics
next_docs:
- spring/requestbody-400-before-controller-primer
- spring/requestbody-415-unsupported-media-type-primer
- spring/valid-400-vs-message-conversion-400-primer
- spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge
linked_paths:
- contents/spring/spring-requestbody-400-before-controller-primer.md
- contents/spring/spring-requestbody-415-unsupported-media-type-primer.md
- contents/spring/spring-valid-400-vs-message-conversion-400-primer.md
- contents/spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md
- contents/spring/spring-mvc-request-lifecycle-basics.md
- contents/spring/spring-modelattribute-vs-requestbody-binding-primer.md
- contents/spring/spring-bindingresult-local-validation-400-primer.md
- contents/spring/spring-admin-302-login-vs-403-beginner-bridge.md
confusable_with:
- spring/requestbody-400-before-controller-primer
- spring/requestbody-415-unsupported-media-type-primer
- spring/valid-400-vs-message-conversion-400-primer
- spring/json-request-400-cause-router
- spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge
forbidden_neighbors: []
expected_queries:
- Spring에서 왜 컨트롤러 브레이크포인트가 안 찍히고 요청이 먼저 끝날까?
- JSON API 호출이 컨트롤러에 닿기 전에 실패할 때 어디부터 나눠서 봐야 해?
- 400, 415, 302, 403이 섞여서 보일 때 컨트롤러 미진입 원인을 어떻게 진단해?
- RequestBody 문제인지 Security 문제인지 처음에 어떤 질문으로 갈라야 해?
- 서비스 로직은 안 탔는데 응답만 바로 돌아오면 스프링 어느 구간을 먼저 의심해?
contextual_chunk_prefix: |
  이 문서는 학습자가 Spring에서 "컨트롤러 첫 줄 로그가 안 찍혀요",
  "JSON 요청인데 바로 400이나 415가 떠요", "브레이크포인트가 안 걸려요",
  "로그인은 한 것 같은데 302나 403으로 먼저 끝나요" 같은 증상을
  RequestBody 변환 전 단계 / Content-Type 계약 / validation 이전 변환 실패 /
  Security 필터 선차단 네 갈래로 나누는 symptom_router다. 컨트롤러 미진입,
  controller 로그 안 찍힘, breakpoint 미진입, 요청이 서비스까지 못 감 같은
  검색을 원인 문서로 보내는 입구로 사용한다.
---

# 컨트롤러 미진입 원인 라우터

> 한 줄 요약: 컨트롤러가 안 탄다는 말은 대개 서비스 버그보다 앞단에서 요청이 끝났다는 뜻이라서, 먼저 `400/415` 바인딩 축인지 `302/403` 보안 축인지부터 갈라야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)
- [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)
- [2단계 `@Valid`는 언제 타고 언제 못 타는가](./spring-valid-400-vs-message-conversion-400-primer.md)
- [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나](./spring-bindingresult-local-validation-400-primer.md)
- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Browser DevTools Waterfall Primer](../network/browser-devtools-waterfall-primer.md)

retrieval-anchor-keywords: controller 로그 안 찍힘, spring controller not hit, requestbody 전에 끊김, 왜 컨트롤러 진입 안 함, 400 before controller basics, 415 unsupported media type 처음, 302 403 before controller, breakpoint 안 걸림, handler 전에 에러, what is pre controller failure

## 핵심 개념

컨트롤러 미진입은 "서비스 코드가 틀렸다"보다 요청이 컨트롤러 앞 단계에서 종료됐다는 신호다. 초급 단계에서는 `Content-Type` 계약 문제, JSON 변환 실패, validation 단계 오해, Security 선차단 네 갈래로 먼저 자르면 된다. 먼저 어디서 끊겼는지 보는 것이 핵심이고, 그다음에 body 내용이나 권한 설정을 본다.

## 한눈에 보기

| 지금 보이는 응답 | 먼저 던질 질문 | 다음 문서 |
| --- | --- | --- |
| `415 Unsupported Media Type` | `Content-Type`과 `consumes`가 맞는가? | [415 primer](./spring-requestbody-415-unsupported-media-type-primer.md) |
| `400` + `JSON parse error` | DTO를 아예 못 만든 건가? | [RequestBody 400 primer](./spring-requestbody-400-before-controller-primer.md) |
| `400` + validation 메시지 | DTO는 만들었고 검증에서 막힌 건가? | [2단계 `@Valid` primer](./spring-valid-400-vs-message-conversion-400-primer.md) |
| `302 /login`, `403 Forbidden` | 보안 필터가 먼저 끝냈는가? | [보안 체인 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md) |

## 빠른 분기

1. `415`면 body 값보다 헤더와 `consumes`부터 본다.
2. `400`인데 `Cannot deserialize`, 날짜 파싱, enum 변환 힌트가 보이면 DTO 생성 전 단계 문제다.
3. `@Valid`, `MethodArgumentNotValidException`, `BindingResult`가 보이면 validation 축이다.
4. `302`, `403`, `/login` 리다이렉트가 보이면 보안 체인이 먼저 처리한 장면이다.
5. 단계가 전혀 감이 안 오면 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)로 돌아가 filter, binding, validation, controller 순서를 다시 세운다.

## 흔한 오해와 함정

- 같은 `400`이라도 DTO를 못 만든 경우와 validation 실패는 수정 위치가 다르다.
- `JSON`을 보냈다고 해서 `Content-Type`도 맞는 것은 아니다. 브라우저 도구나 테스트 코드가 헤더를 다르게 보낼 수 있다.
- 컨트롤러 첫 줄 로그가 안 찍히는데 서비스 로직부터 고치기 시작하면 진단 순서가 뒤집힌다.
- `302`를 인증 성공 신호로만 읽으면 실제로는 로그인 페이지 리다이렉트인 상황을 놓치기 쉽다.

## 다음 행동

- body 변환 실패면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)로 간다.
- media type 계약 문제면 [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)를 본다.
- validation 분기까지 함께 정리하려면 [Spring `@RequestBody 400` vs validation `400` vs business `409` 결정 가이드](./spring-requestbody-400-vs-validation-400-vs-business-409-decision-guide.md)로 이어간다.
- 요청 단계별 타이밍을 눈으로 확인하고 싶으면 [Browser DevTools Waterfall Primer](../network/browser-devtools-waterfall-primer.md)를 같이 본다.

## 한 줄 정리

컨트롤러가 안 타면 서비스 버그부터 의심하지 말고, 요청이 `media type`, DTO 변환, validation, 보안 필터 중 어디서 끝났는지부터 먼저 자르는 편이 빠르다.
