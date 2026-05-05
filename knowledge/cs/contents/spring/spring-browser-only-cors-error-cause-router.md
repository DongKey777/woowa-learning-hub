---
schema_version: 3
title: 브라우저에서만 CORS 에러가 나요 원인 라우터
concept_id: spring/browser-only-cors-error-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- cors-preflight-vs-auth
- cors-owner-mismatch
- credentials-wildcard-confusion
aliases:
- 브라우저에서만 cors 에러
- preflight options 막힘
- postman 은 되는데 브라우저만 실패
- access control allow origin 없음
- fetch cors blocked spring
- cors 설정했는데 계속 막힘
- options 403 spring
symptoms:
- Postman이나 curl은 되는데 브라우저 fetch만 CORS 에러로 막혀요
- preflight OPTIONS가 401이나 403으로 끝나고 실제 POST는 아예 안 나가요
- 응답은 200 같은데 브라우저 콘솔에는 Access-Control-Allow-Origin 관련 에러만 보여요
- 로그인 페이지로 리다이렉트된 것 같은데 화면에서는 그냥 CORS 에러처럼 보여요
intents:
- symptom
- troubleshooting
prerequisites:
- spring/spring-security-basics
next_docs:
- spring/cors-security-vs-mvc-ownership
- spring/spring-security-filter-chain-ordering
- security/browser-401-vs-302-login-redirect-guide
- spring/controller-not-hit-cause-router
linked_paths:
- contents/spring/spring-cors-security-vs-mvc-ownership.md
- contents/spring/spring-security-filter-chain-ordering.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/security/spring-security-options-primer.md
- contents/spring/spring-controller-not-hit-cause-router.md
- contents/spring/spring-api-401-vs-browser-302-beginner-bridge.md
confusable_with:
- spring/cors-security-vs-mvc-ownership
- spring/controller-not-hit-cause-router
- security/browser-401-vs-302-login-redirect-guide
forbidden_neighbors: []
expected_queries:
- Spring에서 브라우저 fetch만 막히고 Postman은 되면 CORS를 어떤 갈래로 먼저 나눠 봐야 해?
- preflight 요청이 401이나 403으로 끝날 때 인증 실패인지 CORS 처리 위치 문제인지 어떻게 구분해?
- Access-Control-Allow-Origin 헤더가 없다는 콘솔 에러가 뜨는데 실제로는 로그인 리다이렉트인지 어떻게 확인해?
- allowCredentials를 켰는데 origin을 와일드카드로 둔 상황이 왜 브라우저에서만 실패로 보이는지 설명해줘
- 컨트롤러는 멀쩡한 것 같은데 브라우저만 cross-origin 에러가 날 때 다음으로 읽을 Spring 문서는 뭐야?
contextual_chunk_prefix: |
  이 문서는 Spring에서 "Postman은 되는데 브라우저 fetch만 CORS 에러예요",
  "preflight OPTIONS가 401이나 403으로 끝나요", "Access-Control-Allow-Origin
  헤더가 없대요", "로그인 페이지로 튄 것 같은데 콘솔에는 CORS 에러만 보여요"
  같은 증상을 preflight 차단 / CORS owner 중복 / credentials 와일드카드
  조합 / login redirect 오인 네 갈래로 나누는 symptom_router다. 브라우저만
  막힘, fetch만 실패, cross-origin 에러, options 막힘 같은 검색을 다음
  원인 문서로 보내는 입구로 사용한다.
---
# 브라우저에서만 CORS 에러가 나요 원인 라우터

## 한 줄 요약

> 브라우저 전용 CORS 에러는 서버 전체 고장보다 preflight가 앞에서 막혔는지, 응답 헤더 책임이 꼬였는지, 아니면 login redirect를 CORS로 오인했는지를 먼저 가르는 편이 빠르다.

## 가능한 원인

1. **preflight `OPTIONS`가 Security 앞단에서 막혔다.** actual `POST`는 보내기도 전에 `OPTIONS 401/403`으로 끝나면 인증 규칙과 CORS 연결 위치를 먼저 봐야 한다. 이 갈래는 [Spring Security OPTIONS Primer](../security/spring-security-options-primer.md)와 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)으로 이어진다.
2. **CORS 정책 주인이 Security와 MVC 사이에서 겹치거나 비어 있다.** 한쪽에만 설정했다고 생각했는데 실제 응답 헤더는 다른 레이어가 결정하면 `Access-Control-Allow-Origin`이 빠진다. 이 경우는 [Spring CORS: Security vs MVC Ownership](./spring-cors-security-vs-mvc-ownership.md)로 내려가 owner를 고정한다.
3. **`allowCredentials=true`인데 origin을 `*`처럼 다뤘다.** Postman은 통과해도 브라우저는 자격 증명 요청에서 더 엄격하게 막으므로 "브라우저만 실패"처럼 보이기 쉽다. 이때도 [Spring CORS: Security vs MVC Ownership](./spring-cors-security-vs-mvc-ownership.md)에서 credentials와 응답 헤더 조합을 다시 본다.
4. **사실은 CORS가 아니라 login redirect나 HTML 응답 오인이다.** `/api/**`가 `302 /login`이나 login HTML을 받아도 콘솔에는 cross-origin 실패처럼만 보일 수 있다. 이 갈래는 [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)와 [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md)로 간다.
5. **컨트롤러까지 도달하기 전에 다른 앞단에서 응답했다.** CORS처럼 보이지만 실제로는 filter, proxy, gateway가 먼저 끊어 컨트롤러 로그가 비는 경우도 있다. 이 경우는 [컨트롤러 미진입 원인 라우터](./spring-controller-not-hit-cause-router.md)로 올라가 입구를 다시 자른다.

## 빠른 자기 진단

1. Network 탭에서 actual 요청보다 `OPTIONS`가 먼저 있는지, 그 상태 코드가 `401/403/302`인지 확인한다. preflight가 실패하면 컨트롤러 코드를 먼저 볼 이유가 줄어든다.
2. 실패 응답 헤더에 `Access-Control-Allow-Origin`과 `Access-Control-Allow-Credentials`가 실제로 있는지 본다. 없으면 owner 누락이나 헤더 조합 문제가 더 가깝다.
3. `Location: /login`, login HTML, redirect chain이 보이면 CORS 자체보다 인증 진입점 오인부터 분리한다.
4. Postman만 되고 브라우저만 안 되면 `credentials: "include"` 사용 여부와 origin 고정값을 같이 본다. 브라우저는 이 조합에서 더 엄격하다.
5. 컨트롤러 로그가 전혀 없으면 Spring MVC 안쪽보다 filter chain, proxy, gateway 같은 앞단 분기로 먼저 이동한다.

## 다음 학습

- preflight `OPTIONS`가 막히는 장면부터 잡으려면 [Spring Security OPTIONS Primer](../security/spring-security-options-primer.md)와 [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)을 본다.
- CORS 설정 주인이 Security인지 MVC인지 헷갈리면 [Spring CORS: Security vs MVC Ownership](./spring-cors-security-vs-mvc-ownership.md)으로 내려간다.
- login redirect를 CORS로 오해한 것 같으면 [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)와 [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md)를 잇는다.
- 컨트롤러 미진입 자체가 더 큰 질문이면 [컨트롤러 미진입 원인 라우터](./spring-controller-not-hit-cause-router.md)로 올라가 전체 입구를 다시 자른다.
