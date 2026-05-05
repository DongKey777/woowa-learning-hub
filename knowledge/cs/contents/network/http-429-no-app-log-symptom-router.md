---
schema_version: 3
title: 429 Too Many Requests인데 앱 로그는 없음 원인 라우터
concept_id: network/http-429-no-app-log-symptom-router
canonical: false
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- edge-local-rate-limit-owner
- quota-key-ip-vs-user
- retry-amplifies-429
aliases:
- 429만 떠요
- too many requests인데 왜 막혀요
- 429인데 앱 로그가 없어요
- rate limit인데 서버 로그가 없어요
- 같은 사무실에서만 429가 떠요
- 재시도할수록 429가 더 떠요
- gateway 429 app log missing
symptoms:
- 브라우저나 API 클라이언트에서는 `429 Too Many Requests`가 반복되는데 애플리케이션 로그에는 같은 요청이 거의 보이지 않아 어디서 막혔는지 헷갈린다
- 어떤 사용자만이 아니라 같은 사무실, 같은 NAT, 같은 테스트 계정 묶음에서만 갑자기 `429`가 많이 떠서 사용자별 제한인지 IP 기반 제한인지 구분이 안 된다
- 실패하자마자 재시도했더니 오히려 `429` 비율이 더 올라가 첫 실패가 원인인지 재시도가 quota를 더 태운 건지 모르겠다
- 응답 body는 HTML 차단 페이지처럼 보이는데 팀에서는 비즈니스 로직의 rate limit인지 edge 정책인지 서로 다르게 말한다
intents:
- symptom
- troubleshooting
prerequisites:
- network/http-status-codes-basics
next_docs:
- network/shopping-cart-rate-limit-bridge
- network/json-expected-but-html-response-symptom-router
- network/same-url-request-twice-symptom-router
linked_paths:
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
- contents/network/api-gateway-auth-rate-limit-chain.md
- contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md
- contents/network/retry-storm-containment-concurrency-limiter-load-shedding.md
- contents/network/cdn-error-html-vs-app-json-decision-card.md
- contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md
- contents/network/browser-devtools-gateway-error-header-clue-card.md
- contents/network/shopping-cart-rate-limit-bridge.md
confusable_with:
- network/json-expected-but-html-response-symptom-router
- network/same-url-request-twice-symptom-router
- network/browser-504-app-200-symptom-router
forbidden_neighbors:
- contents/network/shopping-cart-rate-limit-bridge.md
expected_queries:
- 브라우저에서는 429가 뜨는데 앱 로그가 거의 없으면 어디서 막힌 거야?
- Too Many Requests가 나오는데 gateway 차단인지 서비스 코드인지 어떻게 먼저 가려?
- 같은 회사 IP에서만 429가 많이 뜰 때 무엇부터 확인해야 해?
- 재시도할수록 429가 늘어나면 rate limit 키와 retry를 어떻게 읽어야 해?
- 429 응답이 HTML 차단 페이지처럼 보일 때 origin 앱보다 앞단을 먼저 봐야 하나?
contextual_chunk_prefix: |
  이 문서는 학습자가 `429 Too Many Requests`를 봤지만 애플리케이션 로그가
  거의 없거나, 같은 사무실 사용자만 함께 막히거나, 재시도할수록 더 빨리
  `429`가 쌓일 때 원인을 gateway local rate limit, IP 기준 quota, retry
  amplification, edge HTML 차단 페이지 쪽으로 가르는 network symptom_router다.
  429만 떠요, rate limit인데 서버 로그가 없어요, 같은 회사 IP에서만 막혀요,
  재시도할수록 429가 더 떠요 같은 자연어 표현이 본 문서의 분기와 다음 학습
  문서 추천으로 매핑된다.
---

# 429 Too Many Requests인데 앱 로그는 없음 원인 라우터

> 한 줄 요약: `429`가 보인다고 곧바로 app 비즈니스 로직을 의심하면 자주 틀린다. 먼저 응답 owner가 edge/gateway인지, 어떤 key로 quota를 셌는지, retry가 quota를 더 태웠는지부터 가른다.

**난이도: 🟢 Beginner**

retrieval-anchor-keywords: 429 too many requests, 429인데 앱 로그가 없어요, rate limit basics, gateway local reply, app log missing, same office ip 429, retry makes 429 worse, why no app log, html block page 429, shopping-cart rate limit, nat shared quota

관련 문서:

- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [API Gateway Auth Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md)
- [JSON 기대했는데 HTML 응답이 옴 원인 라우터](./json-expected-but-html-response-symptom-router.md)
- [shopping-cart에서 동일 사용자 동시 추가/결제에 rate limit이 필요한 시점](./shopping-cart-rate-limit-bridge.md)
- [shopping-cart 결제 성공인데 재고가 두 번 줄어듦 ↔ 멱등성/중복 처리 브릿지](../database/shopping-cart-payment-idempotency-stock-bridge.md)

## 가능한 원인

1. CDN, WAF, gateway가 upstream에 보내기 전에 local rate limit으로 막았을 수 있다. 이때는 app 로그가 거의 없고 `Server`, `Via`, vendor header, local rate limit counter가 먼저 단서가 된다. 다음 문서: [CDN Error HTML vs App Error JSON Decision Card](./cdn-error-html-vs-app-json-decision-card.md), [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
2. 사용자 기준이 아니라 IP, NAT, tenant, API key 같은 공유 key로 quota를 세고 있을 수 있다. 같은 사무실 사용자만 함께 막히거나 테스트 계정 묶음이 같이 `429`를 맞으면 trust boundary와 quota key 설계부터 봐야 한다. 다음 문서: [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md), [API Gateway Auth Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md)
3. 첫 실패 뒤 자동 재시도나 버튼 재클릭이 quota를 더 태웠을 수 있다. 이 경우 "원래 요청이 많아서 `429`"라기보다 "retry가 같은 bucket을 더 빨리 비움"이 핵심이다. 다음 문서: [같은 URL 요청이 두 번 보임 원인 라우터](./같은-url-요청이-두-번-보임-원인-라우터.md), [Retry Storm Containment, Concurrency Limiter, Load Shedding](./retry-storm-containment-concurrency-limiter-load-shedding.md)
4. 실제로는 app가 직접 `429`를 반환하지만 로그 상관관계가 약해 놓쳤을 수도 있다. 사용자별 quota, 결제 보호, abuse 방어처럼 비즈니스 정책이라면 trace ID나 principal key로 app 로그를 다시 맞춰 봐야 한다. 다음 문서: [shopping-cart에서 동일 사용자 동시 추가/결제에 rate limit이 필요한 시점](./shopping-cart-rate-limit-bridge.md)
5. `429` 자체보다 응답 body owner를 잘못 읽었을 수 있다. branded HTML, CAPTCHA, edge block 문구가 보이면 origin JSON 에러보다 앞단 보호 페이지 해석이 먼저다. 다음 문서: [JSON 기대했는데 HTML 응답이 옴 원인 라우터](./json-expected-but-html-response-symptom-router.md), [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)

## 빠른 자기 진단

1. 응답 헤더의 `Server`, `Via`, vendor header와 body 첫 줄을 같이 본다. branded HTML이나 edge header가 보이면 app보다 앞단 owner 가능성이 높다.
2. 같은 시각의 gateway rate limit counter, WAF policy hit, app trace를 나란히 놓는다. `429`는 많은데 app trace가 거의 없으면 local reply 갈래가 먼저다.
3. 어떤 key로 제한하는지 적어 본다. user ID인지, IP인지, tenant인지 모르면 "특정 사용자 문제"와 "공유 출구 문제"를 계속 헷갈린다.
4. 같은 URL이 짧은 간격으로 여러 번 보이는지 확인한다. retry, auto refresh, 버튼 재클릭이 있으면 첫 실패 원인과 quota 소진 원인을 따로 봐야 한다.
5. 쓰기 요청이면 재시도 전에 side effect부터 확인한다. `429`가 보여도 일부 요청은 이미 처리됐을 수 있어 중복 제출 판단을 rate limit 숫자만으로 끝내면 위험하다.

## 왜 shopping-cart 미션과 연결되나

shopping-cart 미션에서는 장바구니 담기, 쿠폰 적용, 결제 같은 쓰기 요청이 짧은 시간에
반복될 수 있다. 이때 `429`가 보이면 learner는 흔히 "내 서비스가 rate limit을 잘못
걸었나?"부터 의심하지만, 실제로는 API gateway의 사용자별 quota, NAT 공유 IP 제한,
브라우저 재시도, 중복 클릭이 먼저 원인일 수 있다. 그래서 이 문서에
`missions/shopping-cart`를 연결해 두면 "shopping-cart에서 429인데 앱 로그가
없어요" 같은 질의가 generic network 라우터와 미션 브릿지 둘 다 잡히게 된다.

비유로 보면 shopping-cart는 "결제를 지키기 위한 문" 앞에서 막힌 것처럼 보일 수
있다. 하지만 그 문이 애플리케이션 안쪽 비즈니스 검증인지, gateway 바깥쪽 속도 제한
인지는 다르다. 이 비유는 입구가 여러 겹이라는 점까지만 유효하고, 실제 판정은 응답
헤더와 quota key, retry 흔적을 보고 해야 한다.

## 다음 학습

- 응답 owner가 gateway인지 app인지 더 또렷하게 가르려면 [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- `429`가 branded HTML로 보이는 장면을 다시 자르려면 [JSON 기대했는데 HTML 응답이 옴 원인 라우터](./json-expected-but-html-response-symptom-router.md)
- retry가 quota를 더 태우는 trace를 읽으려면 [같은 URL 요청이 두 번 보임 원인 라우터](./같은-url-요청이-두-번-보임-원인-라우터.md)
- 미션 맥락에서 rate limit과 멱등성을 헷갈렸다면 [shopping-cart에서 동일 사용자 동시 추가/결제에 rate limit이 필요한 시점](./shopping-cart-rate-limit-bridge.md)

## 한 줄 정리

`429`와 app 로그 부재가 같이 보이면 먼저 edge/gateway local reply 가능성을 열고,
그다음 quota key와 retry, 마지막으로 미션의 실제 쓰기 멱등성 문제를 분리해서 본다.
