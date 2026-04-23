# Rate Limiting 기초 (Rate Limiting Basics)

> 한 줄 요약: Rate Limiting은 단위 시간당 요청 수를 제한해 서비스를 과부하와 남용으로부터 보호하는 기법이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Rate Limiter 설계](./rate-limiter-design.md)
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: rate limiting basics, 속도 제한 입문, rate limit 뭐예요, throttling 기초, 429 too many requests, token bucket 개념, leaky bucket 개념, fixed window rate limit, api 호출 제한, rate limiting beginner, 요청 횟수 제한, ddos 방어 기초, 트래픽 제어 기초

---

## 핵심 개념

Rate Limiting은 "정해진 시간 안에 요청을 몇 번까지 허용할지 제한하는 것"이다.
입문자가 자주 헷갈리는 지점은 **왜 정상 사용자도 막힐 수 있는가**이다.

Rate Limiting이 필요한 이유는 세 가지다:

- **서비스 보호**: 한 사용자나 봇이 초당 수천 요청을 보내면 서비스 전체가 다운될 수 있다.
- **공정한 자원 배분**: 일부 클라이언트가 자원을 독점하지 못하게 한다.
- **비용 통제**: 외부 API를 내부에서 쓸 때 호출 비용이 급증하는 것을 막는다.

---

## 한눈에 보기

대표적인 Rate Limiting 알고리즘 비교:

| 알고리즘 | 원리 | 특징 |
|---|---|---|
| Fixed Window | 1분 창마다 카운터 초기화 | 구현 단순, 경계 구간 집중 취약 |
| Sliding Window | 실제 1분 전 요청만 집계 | 더 정확하지만 메모리 비용 있음 |
| Token Bucket | 토큰을 채워두고 요청마다 소비 | 버스트 허용 가능 |
| Leaky Bucket | 일정 속도로만 처리, 초과는 대기 | 출력률이 고정됨 |

초보자가 가장 먼저 알아두면 좋은 건 **Fixed Window**다.

---

## 상세 분해

### Fixed Window 방식

1분 단위로 카운터를 초기화한다.

- 00:00~01:00 사이에 100번 요청 허용
- 101번째부터 429 응답 반환
- 01:00이 되면 카운터를 0으로 초기화

약점: 00:59에 100번, 01:00에 100번 보내면 2초 안에 200번이 통과된다.

### Token Bucket 방식

버킷에 토큰을 채워두고, 요청마다 토큰을 하나 소비한다.

- 버킷에 토큰이 있으면 요청을 처리한다.
- 토큰이 없으면 429를 반환하거나 대기한다.
- 일정 속도로 토큰이 채워진다.

장점: 갑작스러운 burst를 토큰이 남아 있는 만큼 허용할 수 있다.

### Rate Limit 적용 단위

- IP별: 특정 클라이언트 차단에 적합
- 사용자별: 로그인한 사용자 기준
- API Key별: B2B 서비스에서 고객사별 제한
- 엔드포인트별: 특히 무거운 API만 제한

---

## 흔한 오해와 함정

- **"Rate Limit은 공격자만 막는다"**: 정상 사용자도 프로그래밍 실수로 루프를 돌면 걸린다. 클라이언트 측 retry 로직에 backoff가 없으면 서버를 더 괴롭힐 수 있다.
- **"429가 오면 바로 재시도해야 한다"**: 429는 `Retry-After` 헤더를 따라 기다렸다 재시도해야 한다. 바로 재시도하면 금방 또 막힌다.
- **"하나의 Rate Limit 숫자면 충분하다"**: 전체 초당 1000건이 허용돼도, 한 사용자가 그 전부를 쓰면 다른 사용자에게 영향을 준다. 전역 제한과 사용자별 제한을 함께 쓰는 경우가 많다.

---

## 실무에서 쓰는 모습

가장 흔한 시나리오는 API Gateway나 미들웨어에 Rate Limit을 설정하는 것이다.

1. 클라이언트가 API를 호출한다.
2. Gateway가 Redis에서 해당 API Key의 요청 카운터를 확인한다.
3. 제한 이하면 요청을 통과시키고 카운터를 증가시킨다.
4. 제한을 초과하면 429 응답과 `Retry-After: 30` 헤더를 반환한다.

Spring 등에서는 `spring-cloud-gateway`의 `RequestRateLimiter` 필터나, Redis를 활용한 직접 구현으로 처리한다.

---

## 더 깊이 가려면

- [Rate Limiter 설계](./rate-limiter-design.md) — 분산 환경에서의 Rate Limiting 설계
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md) — Rate Limit 응답을 받았을 때 클라이언트 재시도 전략

---

## 면접/시니어 질문 미리보기

> Q: Fixed Window Rate Limiting의 약점은 무엇인가요?
> 의도: 알고리즘의 트레이드오프를 아는지 확인
> 핵심: 윈도우 경계 구간에 요청이 몰리면 실제 처리량이 두 배가 될 수 있다.

> Q: Rate Limit에 걸렸을 때 클라이언트는 어떻게 해야 하나요?
> 의도: 429 응답에 대한 올바른 대응 방식 이해 확인
> 핵심: Retry-After 헤더를 보고 기다린 뒤 exponential backoff로 재시도해야 한다.

> Q: Rate Limiting을 어느 계층에 두는 것이 좋은가요?
> 의도: API Gateway, 미들웨어, 서비스 내부 중 적합한 위치 판단
> 핵심: 공통 정책은 Gateway나 미들웨어에, 도메인 특화 제한은 서비스 내부에 두는 조합이 많다.

---

## 한 줄 정리

Rate Limiting은 서비스 보호와 자원 공정 배분을 위해 단위 시간당 요청 수를 제한하는 기법이며, Fixed Window가 가장 단순하고 Token Bucket이 burst를 허용하는 유연함을 준다.
