# 시스템 설계 면접 프레임워크

> 한 줄 요약: 모호한 요구사항을 숫자와 트레이드오프로 구체화해, 설계 선택의 이유를 설명하는 방법을 정리한다.

retrieval-anchor-keywords: system design interview, requirements, capacity estimation, tradeoffs, bottleneck, failure modes, control plane, data plane, rollback, hot key

**난이도: 🔴 Advanced**

---

## 핵심 개념

시스템 설계 면접은 "정답"을 맞히는 자리가 아니다.  
문제의 범위를 정하고, 병목을 예측하고, 선택지를 비교하면서, 왜 그 설계를 택했는지 설명하는 자리다.

이 문서를 읽을 때의 기준은 네 가지다.

1. 요구사항을 명확히 다시 말할 수 있는가
2. 트래픽과 저장량을 대략 계산할 수 있는가
3. 핵심 구성요소를 이유 있게 배치할 수 있는가
4. 더 좋은 대안이 있어도 왜 지금은 이 선택을 하는지 말할 수 있는가

면접 흐름은 보통 아래 순서로 간다.

| 단계 | 질문 | 목표 |
|---|---|---|
| 1 | 요구사항이 무엇인가? | 범위 고정 |
| 2 | 얼마나 큰 시스템인가? | 숫자 감각 확보 |
| 3 | 어떤 컴포넌트가 필요한가? | 큰 그림 설계 |
| 4 | 어디가 병목인가? | 리스크 식별 |
| 5 | 어떻게 실패를 다룰 것인가? | 운영성 확보 |
| 6 | 왜 이 선택을 했는가? | 트레이드오프 설명 |

> 관련 개념은 [Database](../database/README.md), [Network](../network/README.md), [Operating System](../operating-system/README.md) 문서와 함께 보면 연결이 더 잘 보인다.

---

## 깊이 들어가기

### 1. 요구사항 정리

설계는 기능 목록부터 시작하지 않는다.  
먼저 **무엇을 만들지, 무엇을 안 만들지**를 정해야 한다.

면접 초반에 확인할 것:

- 핵심 사용자 행동은 무엇인가
- 읽기/쓰기 비율은 어떤가
- 실시간성이 필요한가
- 정합성이 중요한가, 가용성이 더 중요한가
- 운영자는 어떤 지표를 봐야 하는가
- 지금 범위에 포함되지 않는 것은 무엇인가

예를 들어 "채팅 시스템"이라고 해도 범위가 달라진다.

- 1:1 채팅인지, 그룹 채팅인지
- 읽음 표시가 필요한지
- 메시지 순서 보장이 필요한지
- 첨부 파일 업로드가 포함되는지
- 오프라인 푸시까지 필요한지

이 단계에서 질문을 잘못하면 뒤 설계가 전부 흔들린다.  
면접관이 원하는 것은 기능 나열이 아니라, **문제를 잘 정의하는 능력**이다.

### 2. Capacity Estimation

숫자 추정은 정밀 계산이 아니라 **규모 감각을 보여주는 도구**다.

자주 쓰는 순서:

1. DAU/MAU를 가정한다
2. 1인당 요청 수를 잡는다
3. 평균 payload 크기를 잡는다
4. 읽기/쓰기 비율을 나눈다
5. 초당 트래픽, 저장량, 대역폭을 계산한다

간단한 예시:

- DAU 100만
- 사용자당 하루 30회 요청
- 평균 응답 크기 10 KB
- 쓰기 비율 5%

그러면 대략:

- 일일 요청 수: 3,000만
- 평균 QPS: 약 347
- 쓰기 QPS: 약 17
- 읽기 QPS: 약 330
- 일일 전송량: 약 300 GB 수준

이 숫자는 정확도가 핵심이 아니다.  
중요한 것은 **어떤 지점이 먼저 터질지**를 추정하는 것이다.

### 3. High-Level Design

큰 그림은 보통 아래 요소로 시작한다.

- Client
- Load Balancer
- API Server
- Cache
- Primary DB / Replica DB
- Queue / Stream
- Object Storage
- Search Index
- Monitoring / Logging / Alerting

설계할 때는 "무조건 많이 넣기"보다 "왜 필요한지"를 먼저 답해야 한다.

- 캐시는 읽기 병목을 줄인다
- 큐는 비동기 처리와 버퍼 역할을 한다
- replica는 읽기 확장을 돕는다
- object storage는 대용량 바이너리를 분리한다
- search index는 조회 패턴을 바꾼다

여기서 중요한 실전 포인트는, 각 컴포넌트가 **어떤 실패를 흡수하는지**까지 같이 말하는 것이다.

### 4. Data Model

데이터 모델은 보통 설계의 중심이다.  
요청 API를 먼저 그린 뒤, 실제 저장 형태를 함께 맞춰야 한다.

점검할 것:

- 어떤 엔티티가 핵심 도메인인가
- 강한 일관성이 필요한 필드는 무엇인가
- 조회 패턴에 맞는 인덱스가 있는가
- 데이터가 한 테이블에 너무 몰리지 않는가
- 조인 비용이 커질 수 있는가
- 시간 순서가 중요한 데이터인가

예를 들어 타임라인, 알림, 피드처럼 시간 정렬 조회가 많은 시스템은  
[인덱스와 실행 계획](../database/index-and-explain.md)과 [MVCC / Replication / Sharding](../database/mvcc-replication-sharding.md) 관점이 중요하다.

### 5. Bottleneck Review

설계의 수준을 가르는 부분은 병목을 먼저 보는 습관이다.

대표적인 병목:

- DB 단일 인스턴스
- hot key
- 대형 트래픽 burst
- 네트워크 대역폭
- 동기 API 체인
- 파일 업로드/다운로드
- 락 경합
- 캐시 미스 폭증

병목을 볼 때는 아래 질문을 던진다.

1. 읽기와 쓰기 중 무엇이 먼저 한계에 닿는가
2. 저장소가 한계인가, 네트워크가 한계인가, 애플리케이션 스레드가 한계인가
3. 캐시가 깨졌을 때도 시스템이 버티는가
4. 특정 사용자나 키에 부하가 쏠리면 어떻게 되는가

운영 관점에서는 [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md), [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md) 같은 네트워크 설계가 병목 완화에 직접 연결된다.

### 6. Reliability and Security

대규모 시스템은 "잘 되는 날"보다 "망가지는 날"에 더 강해야 한다.

기본 체크리스트:

- retry는 안전한가
- idempotency가 보장되는가
- partial failure를 감출 수 있는가
- rate limit이 필요한가
- 인증과 인가가 분리되어 있는가
- 민감 정보가 로그에 남지 않는가
- 데이터 유실 가능성을 어디까지 허용하는가

가용성을 위해 자주 쓰는 전략:

- timeout 설정
- 재시도와 backoff
- circuit breaker
- bulkhead
- queue 기반 비동기화
- replica failover

보안 측면에서는 [Spring Security 아키텍처](../spring/spring-security-architecture.md)와 함께 생각하면 좋다.  
인증 정보, 세션, 토큰, 권한 체크는 설계 초반부터 포함해야 한다.

### 운영 실패를 먼저 상상하기

면접 답변이 강해지는 지점은 "잘 될 때"가 아니라 "망가질 때"를 먼저 보여줄 때다.

- rollout이 잘못되면 어떻게 rollback할 것인가
- cache stampede가 나면 DB를 어떻게 보호할 것인가
- authz policy가 stale하면 어떤 경로를 fail-close 할 것인가
- queue backlog가 폭증하면 어떤 작업을 버릴 것인가
- multi-region 장애 시 읽기와 쓰기를 어떻게 분리할 것인가

이 질문들은 아래 문서로 이어진다.

- [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
- [Config Distribution System 설계](./config-distribution-system-design.md)
- [Distributed Cache 설계](./distributed-cache-design.md)
- [Rate Limit Config Service 설계](./rate-limit-config-service-design.md)
- [Edge Authorization Service 설계](./edge-authorization-service-design.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
- [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)

### 7. 트레이드오프 설명

설계 면접에서 가장 중요한 말은 "A가 좋다"가 아니라  
"이 문제에서는 A를 선택하지만, B의 장단점도 안다"이다.

자주 비교하는 축:

| 선택지 | 장점 | 단점 | 선택 기준 |
|---|---|---|---|
| Cache | 빠른 읽기 | 일관성 관리 어려움 | 읽기 비중이 높을 때 |
| Queue | 버퍼링, 비동기 | 지연 증가 | 즉시 응답이 필요 없을 때 |
| SQL | 정합성, 조인 | 확장 복잡도 | 관계가 명확할 때 |
| NoSQL | 수평 확장 | 쿼리 제약 | 단순 조회 패턴일 때 |
| Sync | 단순성 | 느린 경로 전파 | 강한 즉시 응답이 필요할 때 |
| Async | 탄력성 | 복잡도 증가 | 처리량과 복원력이 중요할 때 |

면접에서 이 비교를 말할 때는 "왜 지금 이 선택이 맞는지"를 한 문장으로 끝내야 한다.

### 실전 연결 맵

이 프레임워크의 각 축은 별도 주제로 계속 확장된다.

- 제어 평면: [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md), [Config Distribution System 설계](./config-distribution-system-design.md), [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
- 캐시와 일관성: [Distributed Cache 설계](./distributed-cache-design.md), [Session Store Design at Scale](./session-store-design-at-scale.md), [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md)
- 비동기 흐름: [Job Queue 설계](./job-queue-design.md), [Distributed Scheduler 설계](./distributed-scheduler-design.md), [Event Bus Control Plane 설계](./event-bus-control-plane-design.md)
- 관측과 분석: [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md), [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md), [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
- 보안과 정책: [Edge Authorization Service 설계](./edge-authorization-service-design.md), [Secrets Distribution System 설계](./secrets-distribution-system-design.md), [API Key Management Platform 설계](./api-key-management-platform-design.md)

---

## 실전 시나리오

### 시나리오 1: URL 단축기

질문 초점:

- 짧은 키를 어떻게 생성할 것인가
- 충돌은 어떻게 처리할 것인가
- 리다이렉트는 얼마나 빨라야 하는가
- 클릭 로그는 실시간으로 필요한가

면접 답변 흐름:

1. 짧은 URL 생성 API 정의
2. key 생성 방식 결정
3. 원본 URL 저장 방식 설계
4. redirect path 최적화
5. analytics 비동기화

이 주제는 [URL 단축기 설계](./url-shortener-design.md)로 확장해 볼 수 있다.

### 시나리오 2: 뉴스피드

질문 초점:

- fan-out on write와 fan-out on read 중 무엇을 고를 것인가
- 피드 정렬 기준은 무엇인가
- 팔로우 관계가 많아져도 버틸 수 있는가

여기서는 읽기/쓰기 비율과 캐시 전략이 핵심이다.  
큰 계정이 등장했을 때 hot path가 어디로 몰리는지 말할 수 있어야 한다.

### 시나리오 3: 채팅 시스템

질문 초점:

- 메시지 순서를 어떻게 보장할 것인가
- 실시간 연결은 WebSocket으로 할 것인가
- 오프라인 메시지는 어디에 저장할 것인가
- 중복 전송과 재시도는 어떻게 처리할 것인가

실시간 전송은 [SSE, WebSocket, Polling](../network/sse-websocket-polling.md)과 연결해서 설명하면 좋다.

### 시나리오 4: 알림 시스템

질문 초점:

- push와 pull 중 무엇을 선택할 것인가
- 우선순위가 다른 알림을 어떻게 나눌 것인가
- 중복 알림을 어떻게 막을 것인가

알림은 단순한 메시지 전달이 아니라, 재시도와 순서, 중복 제거가 모두 걸린다.

### 시나리오 5: 플랫폼 제어 평면

질문 초점:

- flag, config, policy를 어떻게 분리할 것인가
- stale snapshot과 rollback을 어떻게 다룰 것인가
- 누가 언제 정책을 바꿀 수 있는가

이 범위는 [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md), [Config Distribution System 설계](./config-distribution-system-design.md), [Rate Limit Config Service 설계](./rate-limit-config-service-design.md)와 연결된다.

### 시나리오 6: 관측과 실시간 분석

질문 초점:

- metrics와 analytics를 어떻게 나눌 것인가
- heavy hitter, cardinality, window lag를 어떻게 볼 것인가
- 대시보드와 알람의 책임은 어디까지인가

이 범위는 [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md), [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md), [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)와 잘 맞는다.

---

## 코드로 보기

### 설계 면접용 응답 템플릿

```text
1. 요구사항 확인
   - 무엇을 포함하고 제외할지 정한다.

2. 규모 추정
   - DAU, QPS, 저장량, 대역폭을 대략 계산한다.

3. API와 데이터 모델 정의
   - 핵심 엔티티와 주요 endpoint를 잡는다.

4. 아키텍처 스케치
   - cache, db, queue, storage, search를 배치한다.

5. 병목과 실패 대응
   - hot key, failover, retry, timeout을 점검한다.

6. 트레이드오프 요약
   - 선택 이유와 대안을 짧게 정리한다.
```

### 간단한 pseudo architecture

```yaml
client:
  web:
  mobile:

edge:
  load_balancer:
  cdn:

app:
  api_server:
  cache:
  worker:
  auth_service:

storage:
  primary_db:
  replica_db:
  object_storage:
  queue:

observability:
  metrics:
  logs:
  tracing:
```

### 계산 예시

```text
daily_active_users = 1,000,000
requests_per_user = 30
avg_request_size_kb = 10

daily_requests = daily_active_users * requests_per_user
average_qps = daily_requests / 86,400
daily_traffic_gb = daily_requests * avg_request_size_kb / 1024 / 1024
```

이런 계산은 정답을 맞히려는 게 아니라,  
어떤 자원이 먼저 부족해질지 빠르게 추론하기 위한 것이다.

---

## 트레이드오프

| 주제 | 선택 A | 선택 B | 판단 기준 |
|---|---|---|---|
| API 응답 방식 | 동기 응답 | 비동기 처리 | 사용자 대기 허용 여부 |
| 저장 구조 | 정규화 중심 | 조회 최적화 중심 | 쓰기 빈도와 조인 비용 |
| 확장 방식 | scale-up | scale-out | 비용과 운영 복잡도 |
| 실시간 전달 | WebSocket | Polling | 연결 수와 즉시성 |
| 일관성 | 강한 일관성 | eventual consistency | 도메인 중요도 |

면접에서는 "둘 다 가능하다"보다 "이 상황에서는 왜 하나를 먼저 고르는가"가 더 중요하다.

---

## 꼬리질문

> Q: 요구사항이 모호할 때 가장 먼저 무엇을 확인하나요?
> 의도: 문제 정의 능력과 범위 통제 능력 확인
> 핵심: 기능 목록보다 사용자 행동, 제약, 우선순위를 먼저 정리한다.

> Q: capacity estimation은 왜 정확할 필요가 없나요?
> 의도: 숫자를 외우는지, 감각으로 구조를 읽는지 확인
> 핵심: 정밀 계산보다 병목 추정과 의사결정이 목적이다.

> Q: cache를 넣으면 항상 좋은가요?
> 의도: 캐시의 장점만 외우지 않았는지 확인
> 핵심: 일관성, 무효화, stale read, 복잡도 비용을 함께 봐야 한다.

> Q: 트레이드오프를 말할 때 자주 하는 실수는 무엇인가요?
> 의도: 면접 답변의 성숙도 확인
> 핵심: 장점만 말하거나, 선택 기준 없이 나열만 하는 것이다.

> Q: 병목을 찾을 때 어디부터 보나요?
> 의도: 시스템 사고 방식 확인
> 핵심: QPS, latency, DB, cache hit ratio, network, thread pool 순으로 본다.

---

## 한 줄 정리

대규모 시스템 설계 면접은 기능을 많이 아는 시험이 아니라, 요구사항을 좁히고 숫자로 규모를 가늠한 뒤, 병목과 실패를 고려해 설계 선택의 이유를 설득하는 연습이다.
