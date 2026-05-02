---
schema_version: 3
title: 'shopping-cart에서 동일 사용자 동시 추가/결제에 rate limit이 필요한 시점'
concept_id: network/shopping-cart-rate-limit-bridge
canonical: false
category: network
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- rate-limit-vs-idempotency
- duplicate-add-checkout
- per-user-throttle
aliases:
- shopping-cart rate limit
- 장바구니 동시 추가
- 결제 중복 방지 throttle
- 사용자별 요청 제한
- 카트 add API rate
intents:
- mission_bridge
- design
prerequisites:
- system-design/rate-limiting-basics
linked_paths:
- contents/network/api-gateway-auth-rate-limit-chain.md
- contents/system-design/rate-limiter-design.md
forbidden_neighbors:
- contents/network/retry-storm-containment-concurrency-limiter-load-shedding.md
expected_queries:
- 장바구니 추가 API에 rate limit이 필요해?
- 결제 버튼 두 번 누르면 두 번 결제되는데 어떻게 막아?
- 동일 사용자 동시 요청을 throttle로 막는 게 맞아?
- shopping-cart에서 멱등성과 rate limit 중 뭘 먼저 적용해?
---

# shopping-cart에서 동일 사용자 동시 추가/결제에 rate limit이 필요한 시점

> 한 줄 요약: shopping-cart에서 *결제 중복*은 *rate limit*이 아니라 *idempotency key (멱등 키)*로 막는 게 정답이다. *rate limit*은 *abusive 트래픽 방어*에 쓴다 — 봇/스크래퍼 / 1초에 100번 클릭 같은 시그니처. 두 도구는 다른 문제를 푼다.

**난이도: 🟡 Intermediate**

**미션 컨텍스트**: shopping-cart (Woowa 트랙) — 결제/장바구니 동시성 단계

관련 문서:

- [API Gateway: Auth + Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md) — gateway 레벨 처리
- [Rate Limiter Design](../system-design/rate-limiter-design.md) — 일반 디자인

## 미션의 어디에 동시 요청 문제가 보이는가

shopping-cart에서 다음 시나리오가 흔하다:

### 시나리오 A — 결제 버튼 더블클릭

```
T1: POST /payments {cartId: 7}  → 결제 진행
T2: POST /payments {cartId: 7}  → (T1 끝나기 전) 또 결제
```

같은 카트가 *두 번 결제*된다. UI가 첫 클릭 후 *버튼을 비활성화*해도 네트워크 지연/재전송이 살아있다.

### 시나리오 B — 봇이 인기 상품을 1초에 100번 카트에 담기

```
T1~T100: POST /carts/items {productId: 999, qty: 1}  (한 사용자가 1초에 100건)
```

재고 1개짜리 상품을 *모두 카트에 담아* 정상 사용자를 막는다. 또는 부하로 서버를 흔든다.

두 시나리오는 *문제 종류가 다르다*. 하나는 *의도하지 않은 중복 (사용자 의도 = 1번)*이고, 다른 하나는 *의도된 abusive 트래픽 (사용자 의도 = 100번)*.

## 두 도구의 분기

### 도구 1 — Idempotency Key (시나리오 A)

```http
POST /payments
Idempotency-Key: a1b2c3d4-...
{ "cartId": 7 }
```

서버가 *같은 키*를 본 적 있으면 *첫 응답을 그대로 돌려준다*. 같은 결제가 *한 번만 실행*된다.

```java
@PostMapping("/payments")
public PaymentResponse pay(
    @RequestHeader("Idempotency-Key") String key,
    @RequestBody PaymentRequest req
) {
    return idempotencyStore.executeOnce(key, () -> paymentService.pay(req));
}
```

핵심:

- 클라이언트가 *키를 생성*해서 같은 요청 재시도에 *같은 키*를 붙인다
- 서버는 *키 → 응답 캐시*를 두고 *재실행을 회피*한다
- TTL은 보통 24시간

이게 *결제 중복 문제의 정답*이다. Rate limit으로는 이 문제를 풀 수 없다 — 사용자가 *다음 날 정당하게 한 번 더 결제*하면 막히면 안 된다.

### 도구 2 — Rate Limit (시나리오 B)

```
GET/POST 요청 → 사용자 ID 또는 IP 기준 → token bucket 검사 → 초과면 429
```

```java
@PostMapping("/carts/items")
@RateLimited(perUser = "60/min", per = "POST /carts/items")
public CartItem addItem(...) { ... }
```

핵심:

- *시간 윈도우 안의 요청 수*를 측정
- *임계치 초과*하면 `429 Too Many Requests`
- *공정성 (fair use)*과 *abuse 방어*가 목적

이 도구는 *정상 사용자의 정당한 한 번*도 *임계치를 넘으면 막는다*. 그래서 *결제 중복 방지*에는 부적절하고 *bulk 추가 abuse*에는 적절.

## shopping-cart에 적용 시 흔한 잘못된 분기

### 잘못 1 — 결제 중복을 rate limit으로

```java
@PostMapping("/payments")
@RateLimited(perUser = "1/10s")   // ❌ 정당한 두 번째 결제도 막힘
public ... pay(...) { ... }
```

10초에 한 번? 사용자가 *진짜로 두 상품을 따로 사고 싶을 때*도 막힌다. *기능적 결함*이 된다.

### 잘못 2 — 카트 추가에 rate limit 없이 멱등 키만

장바구니 *abuse*는 멱등 키가 막지 못한다. *서로 다른 키*로 1초에 100번 추가하면 통과된다. abuse는 *시간 단위 카운팅*이 본질이다.

### 잘못 3 — `synchronized` 메소드로 두 시나리오 모두 처리

```java
public synchronized PaymentResponse pay(...) { ... }   // ❌
```

JVM 락은 *서버 한 대*에서만 작동. *서버 두 대*면 무용. *분산 환경*을 가정하면 도구가 *Redis-backed token bucket*이나 *DB unique 제약 (멱등 키)*이어야 한다.

### 잘못 4 — 카트 추가 API의 rate limit을 IP 기준으로

```yaml
rate_limit:
  key: client_ip
  limit: 60/min
```

*같은 IP*에 *여러 정상 사용자* (NAT, 회사 네트워크)가 있을 수 있다. 카트 추가는 *사용자 ID*가 더 정확한 키.

## 두 도구를 같이 쓰면

shopping-cart는 *둘 다 적용*하는 게 자연스럽다:

- 결제 API: *멱등 키 필수* + 결제 시도 *5회/min* rate limit (악의적 카드 시도 방어)
- 카트 추가: 멱등 키 *선택* + 사용자별 *60건/min* rate limit (abuse 방어)

이 조합이 *학습자 PR에서 자주 빠지는 부분*이다.

## 자가 점검

- [ ] 결제 API에 *Idempotency Key*를 받아 처리하는가?
- [ ] Idempotency Key TTL이 *재시도 윈도우보다 충분히 긴가* (예: 24h)?
- [ ] 카트 추가에 *사용자별 rate limit*이 있는가? IP 기준이 아닌가?
- [ ] rate limit 초과 시 *429 응답*이 표준 형식 (Retry-After 헤더 포함)인가?
- [ ] 분산 환경 가정으로 락 도구가 *Redis/DB 기반*인가? (`synchronized` 금지)

## 다음 문서

- 더 큰 그림: [API Gateway: Auth + Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md)
- Rate Limiter 설계 디테일: [Rate Limiter Design](../system-design/rate-limiter-design.md)
- 알고리즘 상세: [Rate Limiter Algorithms](../algorithm/rate-limiter-algorithms.md)
