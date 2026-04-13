# Event Bus Control Plane 설계

> 한 줄 요약: event bus control plane은 토픽, 권한, 보존 정책, 라우팅, 재처리 규칙을 중앙에서 관리하는 이벤트 인프라 제어 시스템이다.

retrieval-anchor-keywords: event bus control plane, topic management, schema registry, retention policy, routing rule, consumer group, replay, dead letter queue, event governance, partition assignment

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Job Queue 설계](./job-queue-design.md)
> - [Distributed Scheduler 설계](./distributed-scheduler-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)

## 핵심 개념

Event bus control plane은 메시지를 흘리는 시스템이 아니라,  
이벤트 생태계를 운영하는 정책 시스템이다.

- topic 생성/삭제
- schema registry
- retention / compaction
- ACL / producer policy
- consumer group governance
- replay / backfill rules

즉, 제어 평면은 이벤트 흐름의 질서와 안전성을 관리한다.

## 깊이 들어가기

### 1. 왜 control plane이 필요한가

event bus가 커지면 단순 publish/subscribe로는 부족하다.

- 누가 어떤 topic에 쓸 수 있는가
- 어떤 schema가 허용되는가
- 얼마나 오래 보관하는가
- replay가 가능한가
- 어떤 consumer가 느려도 전체를 막지 않는가

### 2. Capacity Estimation

예:

- 수천 topic
- 수만 consumer group
- 초당 수백만 event

여기서 control plane 트래픽은 상대적으로 낮지만, 잘못된 policy가 data plane 전체를 망칠 수 있다.

봐야 할 숫자:

- topic count
- partition count
- consumer lag
- schema update rate
- routing rule propagation delay

### 3. Topic governance

topic마다 정책이 달라질 수 있다.

- retention days
- compaction 여부
- ordering guarantee
- encryption policy
- tenant ownership

topic은 무한정 늘어날 수 있으므로 naming convention과 lifecycle 관리가 필요하다.

### 4. Schema registry

이벤트는 스키마가 바뀐다.

- backward compatible
- forward compatible
- versioned schema
- validation on publish

schema drift를 막지 않으면 consumer가 깨진다.

### 5. Routing and replay

이벤트는 다른 bus나 topic으로 복제될 수 있다.

- fan-out routing
- tenant partitioning
- archived replay
- DLQ redrive

replay는 강력하지만, 잘못 쓰면 duplicate storm이 된다.

### 6. Partition assignment

consumer group 운영도 control plane의 일부다.

- static assignment
- rebalancing
- hot partition mitigation
- tenant-aware partitioning

이 부분은 [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)과 연결된다.

### 7. Failure mode

control plane이 장애여도 data plane은 계속 돌아야 한다.

- local cached policies
- last-known-good configs
- default retention/routing

## 실전 시나리오

### 시나리오 1: 새 topic 생성

문제:

- 서비스가 새 이벤트 토픽이 필요하다

해결:

- control plane에서 topic template 적용
- schema 등록
- ACL 생성

### 시나리오 2: schema 변경

문제:

- 이벤트 필드를 추가해야 한다

해결:

- registry에 버전 추가
- backward compatibility 검사

### 시나리오 3: lag 증가

문제:

- consumer lag이 급증한다

해결:

- partition 재배치
- hot partition 분리
- DLQ 점검

## 코드로 보기

```pseudo
function publish(event, topic):
  schema = registry.validate(topic, event.schemaVersion)
  if !policy.allowed(topic, event.producer):
    reject()
  bus.publish(topic, event)
```

```java
public void createTopic(TopicSpec spec) {
    topicPolicyService.validate(spec);
    topicRepository.create(spec);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Open publish bus | 유연하다 | governance가 약하다 | 초기 플랫폼 |
| Strong governance plane | 안전하다 | 운영 복잡도 증가 | 대규모 이벤트 플랫폼 |
| Schema registry | 호환성 관리가 쉽다 | 버전 관리가 필요하다 | 실서비스 |
| Replay-enabled bus | 복구가 강하다 | duplicate risk | event-sourced workloads |
| Tenant-aware partitions | 격리가 좋다 | assignment가 복잡하다 | 멀티테넌트 |

핵심은 event bus가 메시지 통로가 아니라 **이벤트 거버넌스를 수행하는 플랫폼**이라는 점이다.

## 꼬리질문

> Q: event bus control plane과 data plane은 어떻게 다르나요?
> 의도: 정책과 전달 분리 이해 확인
> 핵심: control plane은 규칙, data plane은 전달을 맡는다.

> Q: schema registry는 왜 필요한가요?
> 의도: 이벤트 호환성 이해 확인
> 핵심: producer/consumer 진화를 안정적으로 관리하기 위해서다.

> Q: replay가 왜 위험할 수 있나요?
> 의도: 중복과 부작용 이해 확인
> 핵심: 같은 이벤트가 다시 처리되어 duplicate side effect가 날 수 있다.

> Q: hot partition은 어떻게 다루나요?
> 의도: 부하 분산 이해 확인
> 핵심: partition key 설계와 재배치가 필요하다.

## 한 줄 정리

Event bus control plane은 topic, schema, retention, ACL, replay를 중앙에서 관리해 이벤트 플랫폼의 질서와 안전을 유지한다.

