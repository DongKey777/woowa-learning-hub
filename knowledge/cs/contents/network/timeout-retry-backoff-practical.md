# Timeout, Retry, Backoff 실전

**난이도: 🟡 Intermediate**

> 실무에서 요청 실패를 “운 좋게 한번 더 보내면 되겠지”로 처리하지 않기 위한 정리
>
> 문서 역할: 이 문서는 network 운영 cluster 안에서 **timeout / retry / backoff의 기본 의사결정**을 담당하는 survey형 deep dive다.

> 관련 문서:
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
> - [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
> - [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)

retrieval-anchor-keywords: timeout retry backoff, exponential backoff, jitter, retry storm, request timeout, connect timeout, deadline budget, retry budget, transient failure, fail-fast

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 중요한가](#왜-이-주제가-중요한가)
- [Timeout](#timeout)
- [Retry](#retry)
- [Backoff](#backoff)
- [실전 조합](#실전-조합)
- [하면 안 되는 것](#하면-안-되는-것)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 이 문서 다음에 보면 좋은 문서

- 시간 분해 관측은 [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)로 이어진다.
- hop별 남은 시간 전달은 [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)에서 더 깊게 다룬다.
- proxy 자체 retry 정책은 [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)에서 이어서 본다.

## 왜 이 주제가 중요한가

네트워크 요청은 생각보다 자주 실패한다.

- 서버가 느리다
- 중간 프록시가 끊긴다
- DNS나 연결 수립에서 지연이 생긴다
- 순간적인 트래픽 폭주로 응답이 밀린다

이때 중요한 건 "재시도하면 된다"가 아니라,
**언제 끊고, 언제 다시 보내고, 얼마나 기다릴지**를 정하는 것이다.

### Retrieval Anchors

- `timeout retry backoff`
- `exponential backoff`
- `jitter`
- `retry storm`
- `request timeout`
- `deadline budget`
- `retry budget`
- `fail-fast`

---

## Timeout

Timeout은 **응답을 무한정 기다리지 않기 위한 상한선**이다.

대표적으로 다음 단계마다 따로 생각해야 한다.

- DNS lookup timeout
- TCP connect timeout
- TLS handshake timeout
- request timeout
- read timeout

### 왜 나눠서 봐야 하나

“전체 요청 3초”만 두면 원인 파악이 어렵다.

- 연결 자체가 안 되는지
- 서버가 응답을 안 주는지
- 응답은 왔는데 너무 느린지

를 구분하기 힘들다.

### 실무 감각

- 짧은 timeout은 장애를 빨리 드러내지만 오탐도 늘린다
- 긴 timeout은 사용자 경험을 망치고 쓰레드/커넥션을 오래 잡아먹는다
- 외부 의존성일수록 내부보다 timeout을 더 보수적으로 잡는 편이 낫다

---

## Retry

Retry는 **일시적 실패를 다시 시도하는 전략**이다.

모든 실패를 retry하면 안 된다.

### retry해도 되는 실패

- 일시적인 네트워크 단절
- 502, 503, 504 같은 임시 장애
- 서버가 잠깐 과부하인 경우

### retry하면 안 되는 실패

- 잘못된 요청
- 인증 실패
- 권한 부족
- 이미 처리된 요청인데 부작용이 있는 경우

### 중요한 원칙

- 무조건 retry하지 않는다
- retry 횟수는 제한한다
- retry 전에도 timeout이 있어야 한다
- 요청이 멱등적인지 먼저 확인한다

특히 `POST`는 중복 처리 위험이 있으므로 그냥 재시도하면 안 된다.

---

## Backoff

Backoff는 **retry 간격을 점점 늘리는 전략**이다.

단순히 즉시 다시 보내면 장애가 더 악화될 수 있다.

### 이유

- 실패한 서버에 트래픽이 몰린다
- 재시도 폭풍이 생긴다
- 장애 복구 시간을 더 방해한다

### 대표 방식

- Fixed backoff: 매번 같은 시간 대기
- Exponential backoff: 1초, 2초, 4초처럼 점점 증가
- Jitter: 대기 시간에 랜덤성을 섞어 동시 재시도 폭주를 줄임

실무에서는 보통 **exponential backoff + jitter** 조합을 많이 쓴다.

---

## 실전 조합

실무에서 가장 흔한 형태는 아래와 같다.

1. 짧고 명확한 timeout을 건다
2. 실패 원인을 구분한다
3. 재시도 가능한 오류만 retry한다
4. retry는 제한된 횟수만 허용한다
5. backoff와 jitter를 넣는다
6. 최종 실패 시에는 호출자에게 빨리 실패를 반환한다

### 많이 쓰는 추가 장치

- circuit breaker
  - 장애가 지속되면 아예 호출을 잠시 중단한다
- bulkhead
  - 의존성별 자원을 분리해 연쇄 장애를 줄인다
- idempotency key
  - 중복 요청을 안전하게 처리한다

---

## 하면 안 되는 것

- timeout 없이 retry만 넣기
- 모든 에러를 retry하기
- backoff 없이 짧은 간격으로 무한 재시도하기
- 멱등하지 않은 요청을 아무 보호 없이 다시 보내기
- 장애가 난 외부 API를 계속 두드려서 더 악화시키기

이 패턴은 장애를 고치는 게 아니라,
**장애를 증폭시키는 코드**가 되기 쉽다.

---

## 면접에서 자주 나오는 질문

### Q. timeout과 retry는 왜 같이 봐야 하나요?

- timeout이 있어야 실패를 감지할 수 있고, retry가 있어야 일시적 실패를 흡수할 수 있기 때문이다.

### Q. 왜 backoff가 필요한가요?

- 실패 직후 바로 재시도하면 장애 서버에 트래픽이 몰려 상황이 더 나빠질 수 있기 때문이다.

### Q. 멱등성이 왜 중요한가요?

- retry 시 같은 요청이 여러 번 실행되어도 최종 상태가 안전한지 판단하는 기준이 되기 때문이다.

### Q. retry는 항상 좋은가요?

- 아니다. 잘못된 요청이나 부작용이 있는 요청에 retry를 넣으면 중복 처리와 장애 확산을 만들 수 있다.
