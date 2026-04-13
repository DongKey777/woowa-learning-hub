# Streaming Analytics Pipeline 설계

> 한 줄 요약: streaming analytics pipeline은 이벤트를 실시간으로 흡수해 윈도우 집계, 세션화, 이상 탐지, 근사 통계를 만드는 데이터 처리 시스템이다.

retrieval-anchor-keywords: streaming analytics, event time, watermark, window aggregation, sessionization, approximate count, heavy hitters, count min sketch, hyperloglog, stream processor

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)
> - [Count-Min Sketch](../data-structure/count-min-sketch.md)
> - [HyperLogLog](../data-structure/hyperloglog.md)
> - [Event Bus Control Plane 설계](./event-bus-control-plane-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)

## 핵심 개념

Streaming analytics는 로그를 저장하는 것이 아니라,  
흐르는 이벤트에서 바로 의미를 추출하는 시스템이다.

- 실시간 지표 계산
- 윈도우 기반 집계
- 세션화
- 근사 통계
- 이상치 탐지
- 대시보드/알림 데이터 생성

즉, streaming analytics는 분석용 data plane이다.

## 깊이 들어가기

### 1. event time과 processing time

스트림은 늦게 도착한다.

- event time: 사건이 실제로 일어난 시각
- processing time: 시스템이 받은 시각

이 둘을 구분하지 않으면 집계가 흔들린다.

### 2. Capacity Estimation

예:

- 초당 100만 이벤트
- 이벤트당 200 bytes
- 5분 tumbling window

이 경우 처리량뿐 아니라 late arrival와 backpressure가 핵심이다.

봐야 할 숫자:

- ingest QPS
- watermark lag
- window latency
- late event ratio
- checkpoint duration

### 3. 파이프라인

```text
Event Source
  -> Ingest
  -> Parse / Normalize
  -> Key By
  -> Window / Session
  -> Aggregate
  -> Sink
```

### 4. 윈도우와 세션

일반적인 윈도우:

- tumbling window
- sliding window
- session window

세션화는 사용자 행동 분석에서 중요하다.

### 5. 근사 통계

정확한 집계를 항상 할 필요는 없다.

- Count-Min Sketch: 빈도 근사
- HyperLogLog: distinct count
- Heavy hitter: 상위 항목 추적

이 부분은 [Count-Min Sketch](../data-structure/count-min-sketch.md), [HyperLogLog](../data-structure/hyperloglog.md), [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)와 연결된다.

### 6. exactly-once와 checkpoints

스트림 처리에서 중복은 흔하다.

- at-least-once + idempotent sink
- checkpoints
- replay
- offset management

완전한 exactly-once는 비용이 크다.  
실무에서는 재처리 가능성과 idempotency를 같이 설계한다.

### 7. sinks and serving

스트림 결과는 보통 여러 곳으로 간다.

- real-time dashboard
- alerting
- OLAP warehouse
- feature store

## 실전 시나리오

### 시나리오 1: 실시간 전환율 대시보드

문제:

- 1분 단위 전환율이 필요하다

해결:

- window aggregation
- late event correction

### 시나리오 2: 인기 상품/검색어 탐지

문제:

- 상위 항목이 빨리 바뀐다

해결:

- heavy hitter 추적
- approximate frequency

### 시나리오 3: session 기반 분석

문제:

- 사용자 행동 세션을 끊어야 한다

해결:

- inactivity gap sessionization
- watermark and late event handling

## 코드로 보기

```pseudo
function process(event):
  key = extractKey(event)
  state = stateStore.load(key)
  window = assignWindow(event.time)
  aggregate = update(state, event, window)
  sink.write(aggregate)
```

```java
public void onEvent(StreamEvent event) {
    analyticsEngine.process(event);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Batch analytics | 단순하다 | 지연이 크다 | 오프라인 리포트 |
| Streaming analytics | 반응이 빠르다 | 운영이 복잡하다 | 실시간 대시보드 |
| Exact counting | 정확하다 | 비용이 높다 | 재무/정산 |
| Sketch-based analytics | 메모리 효율적이다 | 근사다 | 고QPS telemetry |
| Stateful processing | 표현력이 높다 | state 관리가 어렵다 | 세션/전환 분석 |

핵심은 streaming analytics가 로그 저장소가 아니라 **이벤트에서 실시간 의미를 계산하는 처리 파이프라인**이라는 점이다.

## 꼬리질문

> Q: event time과 processing time을 왜 구분하나요?
> 의도: late event와 window 정확성 이해 확인
> 핵심: 도착 지연이 있더라도 실제 사건 시간 기준 집계가 필요하기 때문이다.

> Q: checkpoint는 왜 필요한가요?
> 의도: 재처리와 장애 복구 이해 확인
> 핵심: 스트림 장애 후 이어서 처리하기 위해서다.

> Q: 왜 sketch를 쓰나요?
> 의도: 근사 통계의 실무적 가치를 이해하는지 확인
> 핵심: 정확도보다 메모리/처리량이 중요할 때가 많다.

> Q: streaming analytics와 metrics pipeline의 차이는?
> 의도: 분석과 관측성의 차이 이해 확인
> 핵심: metrics는 운영 지표, analytics는 비즈니스/행동 분석이다.

## 한 줄 정리

Streaming analytics pipeline은 실시간 이벤트에서 윈도우 집계와 근사 통계를 계산해 대시보드, 알림, 분석 싱크로 흘려보내는 시스템이다.

