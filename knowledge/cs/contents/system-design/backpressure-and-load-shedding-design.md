# Backpressure and Load Shedding 설계

> 한 줄 요약: backpressure and load shedding은 시스템이 감당할 수 있는 것만 받아들이고, 넘치는 부하는 우선순위에 따라 버리거나 늦추는 생존성 설계다.

retrieval-anchor-keywords: backpressure, load shedding, graceful degradation, admission control, queue depth, saturation, bulkhead, overload protection, shed low priority, fail fast

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)

## 핵심 개념

부하 제어는 단순 rate limit이 아니다.  
실전에서는 다음을 동시에 다뤄야 한다.

- 시스템이 포화되기 전에 신호를 읽는다
- 중요하지 않은 작업을 먼저 버린다
- 핵심 경로는 유지한다
- 큐와 워커의 backlog를 관리한다
- 장애가 연쇄로 번지지 않게 막는다

즉, backpressure는 downstream이 무너지기 전에 upstream이 스스로 속도를 조절하게 만드는 메커니즘이다.

## 깊이 들어가기

### 1. backpressure와 load shedding의 차이

- backpressure: 더 넣지 말고 천천히 처리하라는 신호
- load shedding: 이미 넘친 부하를 일부 버리는 정책

둘은 같이 쓰는 경우가 많다.  
백프레셔로 속도를 줄이고, 그래도 안 되면 low-priority를 버린다.

### 2. Capacity Estimation

예:

- 초당 요청 20만
- p95 latency가 2배로 상승
- queue depth가 10배로 증가

이 숫자가 보이면 이미 늦었을 수 있다.  
핵심은 절대 수치보다 saturation signal이다.

봐야 할 숫자:

- queue depth
- in-flight request
- worker utilization
- p95/p99 latency
- retry rate

### 3. admission control

모든 요청을 받아서 처리할 필요는 없다.

- low priority drop
- bounded queue
- request deadline
- timeout budget

문제가 되는 경로는 보통 부가 기능이다.

- analytics
- email/push
- report export
- thumbnail generation
- expensive ranking

### 4. shed strategy

보통 다음 순서로 버린다.

1. 가장 늦게 도착한 저우선 작업
2. 재시도 가능한 작업
3. 비용이 큰 보조 작업
4. 사용자 체감이 낮은 작업

핵심은 "아무거나 버린다"가 아니라, **무엇을 희생해 핵심 경로를 살릴지**다.

### 5. bulkhead and isolation

한 경로의 폭주가 전체를 무너뜨리지 않게 해야 한다.

- tenant별 queue
- endpoint별 worker pool
- priority lane
- circuit breaker

이 부분은 [Job Queue 설계](./job-queue-design.md), [Rate Limit Config Service 설계](./rate-limit-config-service-design.md), [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)와 연결된다.

### 6. fallback and degraded mode

늘 완전한 기능을 줄 필요는 없다.

- 검색 결과 일부만 제공
- 오래된 cache를 잠깐 허용
- 비핵심 telemetry를 드롭
- preview와 export를 비동기로 전환

### 7. observability

load shedding은 은밀해야 하지만, 관측은 명확해야 한다.

- shed rate
- reject rate
- queue lag
- downstream saturation
- circuit breaker open ratio

이 데이터는 [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)와 [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)로 흘러갈 수 있다.

## 실전 시나리오

### 시나리오 1: 대량 export 폭주

문제:

- CSV export가 동시에 몰린다

해결:

- export queue를 분리
- low-priority shed
- deadline 설정

### 시나리오 2: webhook/notification 적체

문제:

- 외부 연동이 느려져 backlog가 쌓인다

해결:

- provider별 bulkhead
- fail-fast + retry budget
- DLQ

### 시나리오 3: 실시간 분석 폭주

문제:

- 집계 파이프라인이 메모리 압박을 받는다

해결:

- low-value event drop
- sketch 기반 근사
- priority window

## 코드로 보기

```pseudo
function accept(request):
  if isOverloaded():
    if request.priority == LOW:
      return 503
    if queue.depth > HIGH_WATERMARK:
      return 429
  enqueue(request)
  return 202
```

```java
public boolean shouldShed(Request req) {
    return overloadDetector.isOverloaded() && req.priority() == Priority.LOW;
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Fail fast | 빠르게 회복한다 | 사용자는 실패를 본다 | 과부하 방어 |
| Queue everything | 단순하다 | backlog 폭증 | 작은 시스템 |
| Shed low priority | 핵심 경로를 살린다 | 기능 일부가 사라진다 | 실서비스 |
| Bulkhead isolation | 연쇄 장애를 막는다 | 운영 복잡도 | 멀티테넌트/멀티워크로드 |
| Degraded mode | UX를 유지한다 | 기능이 줄어든다 | 부분 장애 |

핵심은 backpressure and load shedding이 단순 차단이 아니라 **시스템 생존성을 위한 우선순위 조절**이라는 점이다.

## 꼬리질문

> Q: backpressure와 rate limit은 어떻게 다른가요?
> 의도: 보호 목적과 흐름 제어를 구분하는지 확인
> 핵심: rate limit은 규칙, backpressure는 포화 상태 대응이다.

> Q: load shedding에서 무엇을 먼저 버리나요?
> 의도: 우선순위 감각 확인
> 핵심: 재시도 가능하고 사용자 체감이 낮은 작업부터다.

> Q: 왜 bulkhead가 중요한가요?
> 의도: 연쇄 장애와 격리 이해 확인
> 핵심: 한 경로의 폭주가 전체를 죽이지 않게 하기 위해서다.

> Q: degraded mode는 언제 유용한가요?
> 의도: 완전 장애 대신 부분 기능 유지 이해 확인
> 핵심: 핵심 경로는 살리고 비핵심 기능만 줄일 때 좋다.

## 한 줄 정리

Backpressure and load shedding은 포화 신호를 읽고 저우선 부하를 줄여 핵심 경로와 시스템 생존성을 지키는 설계다.

