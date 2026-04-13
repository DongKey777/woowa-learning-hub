# Multi-Region Active-Active 설계

> 한 줄 요약: 여러 리전에서 동시에 서비스를 제공하면서도 지연, 장애, 충돌을 제어하는 글로벌 아키텍처를 설계한다.

retrieval-anchor-keywords: multi-region active-active, regional failover, write locality, split brain, quorum, replication lag, data residency, conflict resolution, active-passive, rpo rto, global traffic routing

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Multi-tenant SaaS Isolation 설계](./multi-tenant-saas-isolation-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)

## 핵심 개념

Active-active는 "모든 리전이 똑같이 다 한다"가 아니다.  
실무에서는 아래를 동시에 맞춰야 한다.

- 각 리전에서 빠르게 서비스한다
- 장애 시 다른 리전이 흡수한다
- 데이터 충돌을 통제한다
- 지역별 규제와 residency를 지킨다
- 복구 시 RPO/RTO를 만족한다

즉, 글로벌 시스템은 하나의 DB가 아니라 **지역별 책임과 글로벌 규칙의 조합**이다.

## 깊이 들어가기

### 1. 먼저 목표를 숫자로 고정한다

설계 전에 묻는 질문:

- 허용 가능한 RTO는 얼마인가
- 허용 가능한 RPO는 얼마인가
- 읽기와 쓰기를 어디까지 지역 내에서 처리할 수 있는가
- 어떤 데이터는 cross-region으로 나가면 안 되는가

예를 들어:

- 사용자 트래픽 70%는 APAC
- 20%는 US
- 10%는 EU

이 경우 각 리전은 자기 트래픽을 감당할 뿐 아니라, 다른 리전 장애 시 버스트를 흡수할 수 있어야 한다.

### 2. Capacity Estimation

멀티 리전은 총량보다 "리전별 피크"와 "장애 시 피크"를 봐야 한다.

예:

- 정상 시 각 리전 QPS: 5k / 3k / 2k
- 한 리전 장애 시 나머지 두 리전이 10k를 감당해야 함
- replication link는 데이터 변경량과 함께 폭주할 수 있음

즉, 계산 대상은 다음이다.

- 지역별 request rate
- cross-region replication bandwidth
- failover 시 배수 부하
- replication lag

### 3. 아키텍처 토폴로지

일반적인 형태:

- 글로벌 traffic router
- region-local load balancer
- region-local app cluster
- region-local cache
- region-local DB 또는 write leader
- async replication / event stream

중요한 점은 "글로벌"과 "지역 로컬"의 경계를 나누는 것이다.  
로그, 큐, 캐시, DB, 백업, 오브젝트 스토리지가 모두 같은 경계에 있어야 한다.

### 4. 데이터 전략

데이터는 보통 엔티티별로 다르게 다룬다.

| 데이터 유형 | 권장 전략 | 이유 |
|---|---|---|
| 사용자 프로필 | 지역 로컬 우선 | 읽기 지연이 중요 |
| 주문/결제 | 단일 writer 또는 강한 제약 | 정합성이 중요 |
| 이벤트/로그 | 비동기 복제 | 유실 허용 범위가 넓다 |
| 설정/메타데이터 | 글로벌 제어 plane | 전 리전에서 공통 사용 |

모든 데이터에 하나의 정책을 강요하면 active-active는 금방 무너진다.

### 5. 충돌 해결

active-active의 난제는 write conflict다.

대표적 접근:

- entity owner region을 정한다
- last-write-wins를 제한적으로 쓴다
- version number 또는 vector clock을 둔다
- merge 가능한 도메인만 multi-write를 허용한다

예를 들어 프로필 사진은 충돌 허용이 쉽지만, 결제 상태는 그렇지 않다.

### 6. 세션과 캐시

사용자가 한 리전에서 로그인한 뒤 다른 리전으로 튀면 다음 문제가 생긴다.

- read-your-writes가 깨진다
- 세션이 사라진 것처럼 보인다
- cache가 stale해질 수 있다

대응책:

- sticky routing
- session token을 stateless하게 유지
- 중요 write 후에는 동일 리전에서 읽기 유도
- cache invalidation은 regional event로 처리

이 부분은 [Distributed Cache 설계](./distributed-cache-design.md)와 함께 봐야 한다.

### 7. 장애와 split brain

가장 위험한 상황은 둘 다 "내가 쓴다"고 믿는 것이다.

대응:

- quorum 기반 leader election
- write fencing token
- region health check
- traffic draining
- failover drill

완전한 split brain 회피는 어렵기 때문에, write 범위를 좁히는 것이 더 현실적이다.

## 실전 시나리오

### 시나리오 1: 한 리전 전체 장애

문제:

- APAC 리전이 다운된다
- 트래픽이 US/EU로 넘어온다

해결:

- GSLB가 트래픽을 재라우팅한다
- 캐시와 큐가 다른 리전에서 재가동된다
- failover capacity를 미리 예약한다

### 시나리오 2: 네트워크 분리

문제:

- 리전 간 연결이 끊겼다
- replication lag가 커진다

해결:

- write locality를 유지한다
- conflict 가능 엔티티만 제한적으로 multi-write한다
- 나머지는 read-only 또는 degraded mode로 전환한다

### 시나리오 3: 데이터 residency

문제:

- EU 데이터가 EU 밖으로 나가면 안 된다

해결:

- EU tenant는 EU DB, EU cache, EU queue를 사용한다
- 글로벌 control plane만 메타데이터를 가진다

이 부분은 [Multi-tenant SaaS Isolation 설계](./multi-tenant-saas-isolation-design.md)와 같은 원리다.

## 코드로 보기

```text
global-router:
  apac -> apac-region
  us   -> us-region
  eu   -> eu-region

write-policy:
  orders = single-writer-per-entity
  profiles = last-write-wins-with-version
  logs = async-replicated
```

```java
public boolean canWrite(EntityType type) {
    return switch (type) {
        case ORDER, PAYMENT -> region.isOwner();
        case PROFILE -> true;
        case LOG -> true;
    };
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Active-active | 낮은 지역 지연, 높은 가용성 | 충돌과 복제가 어렵다 | 글로벌 서비스 |
| Active-passive | 단순하다 | failover 시 지연이 커진다 | DR 우선 시스템 |
| Strong global consistency | 정합성이 높다 | 지연과 비용이 크다 | 결제, 원장 |
| Region-local consistency | 빠르다 | 전역 충돌 제어가 어렵다 | 프로필, 콘텐츠 |
| Sticky routing | read-your-writes가 쉽다 | 트래픽 편중 가능 | 세션 민감 서비스 |

핵심은 "모든 리전을 똑같이 쓰자"가 아니라 **어떤 데이터는 로컬하게, 어떤 데이터는 전역 규칙으로 다루는가**다.

## 꼬리질문

> Q: active-active와 active-passive의 차이는 무엇인가요?
> 의도: DR 아키텍처 선택 기준 확인
> 핵심: active-active는 양쪽이 동시에 서비스하고, active-passive는 한쪽만 주로 서비스한다.

> Q: split brain을 왜 위험하다고 하나요?
> 의도: 분산 합의와 fencing 이해 확인
> 핵심: 두 리전이 모두 쓰기 주도권을 가지면 충돌과 데이터 분기가 생긴다.

> Q: RPO와 RTO는 어떻게 다르나요?
> 의도: 재해복구 목표 이해 확인
> 핵심: RPO는 잃어도 되는 데이터 양/시간, RTO는 복구까지 걸리는 시간이다.

> Q: 모든 데이터를 multi-write로 만들 수 있나요?
> 의도: 도메인별 정합성 차이를 이해하는지 확인
> 핵심: 결제와 원장처럼 강한 정합성이 필요한 데이터는 제한이 많다.

## 한 줄 정리

Multi-region active-active는 글로벌 지연과 장애 대응을 개선하지만, 충돌 해결과 데이터 경계를 설계하지 않으면 가장 복잡한 분산 시스템이 된다.

