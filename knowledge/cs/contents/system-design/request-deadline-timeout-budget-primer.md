# Request Deadline and Timeout Budget Primer

> 한 줄 요약: client deadline, app budget, cache timeout, DB timeout을 계단처럼 맞춰야 느린 의존성이 partial failure에 머무르고 retry storm로 커지지 않는다.

retrieval-anchor-keywords: request deadline primer, timeout budget primer, end-to-end deadline, client timeout budget, app timeout budget, cache timeout fallback, db timeout budget, partial failure, retry storm prevention, remaining budget, fail-fast ladder, deadline propagation basics, cache slow miss, db statement timeout, request deadline timeout budget primer basics

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [분산 캐시 설계](./distributed-cache-design.md)
- [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- [Proxy Retry Budget Discipline](../network/proxy-retry-budget-discipline.md)

---

## 핵심 개념

완전히 죽은 장애보다 더 위험한 건 "조금씩 느린" partial failure다.

- cache hit는 줄었지만 완전히 down은 아니다
- DB는 응답하지만 pool wait이나 lock wait이 길어진다
- app는 아직 새 요청을 받고 있어서 client가 retry를 시작한다

이때 timeout budget이 없으면 같은 사용자 요청이 겹친다.

- 첫 시도는 아직 cache나 DB에서 기다리는 중이다
- client는 이미 timeout으로 새 시도를 보낸다
- app는 남은 시간을 계산하지 않고 downstream call을 다시 시작한다
- DB는 오래된 query와 새 query를 함께 떠안는다

즉 timeout budget의 목적은 "언제 포기할까"만이 아니라 **이전 시도가 정리되기 전에 다음 시도가 겹치지 않게 하는 것**이다.

대표 request chain은 아래처럼 볼 수 있다.

```text
Client (deadline 1500ms)
  -> App (overall budget 1200ms, response reserve 포함)
      -> Cache (timeout 30ms)
      -> DB (pool acquire 40ms, statement timeout 180ms)
```

핵심 원칙:

- client는 end-to-end 상한을 잡는다
- app은 남은 시간을 읽고 dependency budget을 나눈다
- cache는 optional fast path라서 가장 짧게 끊는다
- DB timeout은 app/client보다 짧아야 zombie query를 줄인다
- retry는 "횟수"보다 먼저 remaining budget을 본다

---

## 깊이 들어가기

### 1. 왜 partial failure가 retry storm로 번지나

가장 흔한 실패는 모든 레이어가 비슷한 timeout을 쓰는 것이다.

예:

- client timeout 1500ms
- app request timeout 1500ms
- cache timeout 400ms
- DB timeout 1200ms
- client retry 1회, app retry 1회

cache가 300ms로 느려지면 app은 거의 꽉 찰 때까지 cache를 기다린다.
그 뒤에 DB call이 시작되면 client는 1500ms에서 포기하고 retry를 보낸다.
그런데 첫 DB query는 아직 끝나지 않았고, app retry까지 붙으면 한 요청이
`client 2회 x app 2회 = 최대 4개의 DB 시도`
로 증폭될 수 있다.

여기서 더 중요한 건 총 횟수보다 **동시에 살아 있는 시도 수**다.
timeout budget은 이 overlap을 줄이는 장치다.

### 2. client deadline은 전체 상한선이다

client는 사용자 체감 시간을 기준으로 end-to-end deadline을 정한다.
이 deadline보다 app timeout이 길면 client는 포기했는데 server는 계속 일한다.

client layer에서 필요한 것:

- 전체 요청 상한선
- cancel/abort signal 전달
- retry 전 remaining budget 확인
- idempotent하지 않은 요청의 blind retry 금지

좋은 감각은 이렇다.

- client는 "몇 초 기다릴까"보다 "언제까지 이 요청이 유효한가"를 정한다
- deadline이 끝났으면 새 시도를 시작하지 않는다
- retry하더라도 backoff, jitter, retry budget을 함께 둔다

### 3. app budget은 coordinator다

app이 흔히 하는 실수는 각 dependency에 독립 timeout을 새로 주는 것이다.
이러면 cache 300ms, DB 500ms, 내부 queue 200ms가 모두 합쳐져 client deadline을 넘어간다.

app이 해야 할 일:

1. inbound deadline에서 남은 시간을 계산한다
2. 응답 serialization과 write를 위한 reserve를 남긴다
3. cache, DB 같은 dependency에 더 작은 sub-budget을 배분한다
4. 의미 있는 시간이 남지 않았으면 새 호출을 시작하지 않고 fail-fast 한다

간단한 감각은 이렇다.

## 깊이 들어가기 (계속 2)

```text
remaining = client_deadline - now
response_reserve = 100ms

cache_budget = min(30ms, remaining - response_reserve)
db_budget = min(180ms, remaining - response_reserve - cache_time_spent)

if remaining <= response_reserve:
  새 downstream call 금지
```

핵심은 app timeout이 client보다 짧아야 한다는 점보다, **app이 client의 남은 시간을 존중해야 한다**는 점이다.

### 4. cache timeout은 "짧은 실패"를 만드는 장치다

cache는 source of truth가 아니라 빠른 지름길이다.
그래서 cache timeout은 보통 DB timeout보다 훨씬 짧아야 한다.

이유:

- cache가 느리면 결국 DB로 fallback할 가능성이 높다
- cache를 오래 기다리면 같은 요청이 `cache wait + DB wait`를 둘 다 먹는다
- 그러면 client timeout 직전에 DB call이 시작되어 overlap이 커진다

좋은 방향:

- cache timeout을 짧게 둔다
- stale 허용 가능한 read는 stale entry를 잠깐 쓴다
- hot key는 single-flight나 request coalescing으로 miss를 묶는다
- cache 장애 때는 miss rate와 timeout rate를 따로 본다

즉 cache timeout은 "cache를 끝까지 믿자"가 아니라 **slow cache를 quick miss로 바꾸는 안전장치**다.

### 5. DB timeout은 capacity guardrail이다

DB partial failure는 완전 outage보다 더 흔하다.

- connection pool acquire가 길어진다
- lock wait이 늘어난다
- statement는 끝나지만 p99가 급격히 뛴다

이때 DB timeout이 app/client보다 길면 문제가 커진다.

- caller는 이미 retry를 시작했다
- old query는 DB에서 계속 CPU, lock, connection을 점유한다
- queue와 pool wait이 더 길어지면서 다음 wave가 더 늦어진다

그래서 DB path에는 보통 여러 상한이 필요하다.

- connection pool acquire timeout
- lock wait timeout
- statement timeout
- transaction timeout

방향성:

- DB timeout은 app deadline보다 짧다
- 최근에 이미 budget을 많이 썼다면 DB call을 새로 시작하지 않는다
- DB retry는 남은 budget과 멱등성이 둘 다 만족될 때만 허용한다

## 깊이 들어가기 (계속 3)

여기서 중요한 감각은 DB timeout이 단순 성능 파라미터가 아니라 **동시성 확산을 막는 보호선**이라는 점이다.

### 6. 좋은 budget ladder는 "위가 길고 아래가 짧다"

대표적인 ladder는 아래 느낌이다.

| 레이어 | 역할 | 너무 길면 생기는 일 | 좋은 방향 |
|---|---|---|---|
| client deadline | end-to-end 상한 | 사용자는 포기했는데 서버는 계속 일함 | 전체 요청의 최종 마감 시각을 둔다 |
| app budget | 남은 시간 배분 | hop마다 timeout이 리셋됨 | reserve를 남기고 dependency budget을 쪼갠다 |
| cache timeout | optional fast path 판단 | cache wait 뒤 DB wait이 겹친다 | quick miss, stale, coalescing을 우선한다 |
| DB timeout | source of truth 보호 | abandoned query, lock wait, pool saturation이 남는다 | pool/lock/statement timeout을 짧게 둔다 |

이 계단이 맞으면 partial failure가 생겨도 old attempt가 빨리 접히고, new attempt와 겹치는 시간이 줄어든다.
반대로 모든 레이어가 비슷한 timeout을 쓰면 "천천히 실패하는 요청"이 전체 시스템에 오래 남는다.

### 7. retry budget은 timeout budget 위에서만 의미가 있다

retry budget이 있어도 timeout budget이 헐거우면 overlap이 줄지 않는다.
반대로 timeout만 짧고 retry 기준이 없으면 작은 흔들림도 과하게 실패로 드러난다.

그래서 보통 둘을 같이 본다.

- timeout budget: 한 시도가 얼마나 오래 살 수 있는가
- retry budget: 몇 번까지 다시 시도할 수 있는가

실전 원칙:

- 같은 요청을 client와 app이 동시에 retry하지 않는다
- remaining budget이 full-cost floor보다 작으면 재시도하지 않는다
- non-critical read는 stale, degrade, shed를 먼저 본다
- write retry는 idempotency key 없이는 보수적으로 다룬다

---

## 실전 시나리오

### 시나리오 1: cache는 조금 느리고 DB는 아직 멀쩡하다

문제:

- cache p99가 5ms에서 120ms로 튄다
- app은 cache를 300ms까지 기다린 뒤 DB로 fallback한다
- client는 1.5s에서 retry를 시작한다

결과:

- 각 요청이 cache wait과 DB wait을 둘 다 먹는다
- DB는 miss traffic뿐 아니라 overlapped retry traffic까지 받는다
- 원래 cache incident가 DB read spike incident로 커진다

해결 방향:

- cache timeout을 짧게 줄인다
- stale read 허용 범위를 명확히 둔다
- hot key는 single-flight로 묶는다
- client/app blind retry를 끊는다

### 시나리오 2: DB가 완전히 죽진 않았지만 lock wait이 길다

문제:

- DB statement timeout 2s
- app deadline 900ms
- client deadline 1.2s
- client는 1회 retry한다

결과:

- client는 포기하고 새 시도를 보낸다
- 이전 query는 lock wait 상태로 계속 남는다
- pool acquire time이 늘고 app thread도 더 오래 묶인다

해결 방향:

- statement, lock, pool timeout을 더 짧게 둔다
- 남은 budget이 작으면 새 DB call 자체를 막는다
- write path는 fail-fast와 idempotency guard를 함께 둔다
- 필요하면 read-only나 degraded mode로 축소 운영한다

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 공격적으로 짧은 timeout | useless work를 빨리 끊는다 | false timeout이 늘 수 있다 | overloaded dependency 보호 우선 |
| 넉넉한 timeout | 일시적 tail spike를 더 흡수한다 | retry overlap과 pool 점유가 길어진다 | batch, background, 중요하지만 비대화형 경로 |
| cache quick miss | request budget을 아낀다 | DB fallback traffic이 늘 수 있다 | cache가 optional fast path일 때 |
| DB fail-fast | lock/pool 확산을 막는다 | 일부 요청은 더 빨리 실패한다 | source of truth 보호가 더 중요할 때 |

핵심은 timeout을 크게 잡아 성공률만 보는 것이 아니라 **시스템 전체 동시성 비용**까지 함께 보는 것이다.

## 꼬리질문

> Q: 왜 cache timeout이 DB timeout보다 짧아야 하나요?
> 핵심: cache는 optional fast path라서 오래 기다리기보다 quick miss로 바꿔 DB fallback이나 stale 경로를 선택하는 편이 낫다.

> Q: app이 client timeout과 같은 값을 쓰면 왜 위험한가요?
> 핵심: app이 응답 write와 정리 시간을 남기지 못해 client가 포기한 뒤에도 downstream work가 계속 남기 쉽다.

> Q: timeout budget과 retry budget은 어떤 관계인가요?
> 핵심: timeout budget이 한 시도의 수명을 제한하고 retry budget이 시도 횟수를 제한한다. 둘 중 하나만 있으면 partial failure 증폭을 막기 어렵다.

## 한 줄 정리

client, app, cache, DB timeout budget을 계단형으로 맞추면 partial failure가 짧은 실패로 정리되고, 맞추지 않으면 느린 요청과 retry가 겹치며 storm로 커진다.
