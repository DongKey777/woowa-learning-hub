# Distributed Lock 설계

> 한 줄 요약: 분산 환경에서 단일 실행권을 보장하려면, 락 자체보다 "언제 안전하게 풀 수 있는가"와 "누가 진짜 소유자인가"를 먼저 설계해야 한다.

retrieval-anchor-keywords: distributed lock, lease, fencing token, ownership, leader election, stale owner, compare and delete, coordination, failover control, placement fencing, consensus reconfiguration

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [분산 캐시 설계](./distributed-cache-design.md)
> - [Deadlock Case Study](../database/deadlock-case-study.md)
> - [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
> - [Transaction Debugging Playbook](../spring/spring-transaction-debugging-playbook.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Consensus Membership Reconfiguration 설계](./consensus-membership-reconfiguration-design.md)

---

## 핵심 개념

분산 락은 "여러 서버가 동시에 같은 일을 하지 못하게 막는 장치"다.  
하지만 실무에서 진짜 문제는 락을 잡는 것이 아니라, 아래 세 가지다.

- 누가 현재 소유자인가
- 락이 죽은 세션에 남지 않았는가
- 락이 만료된 뒤에도 이전 소유자가 작업을 계속하지 않는가

그래서 분산 락은 단순히 `SET NX PX`로 끝나지 않는다.  
락의 유효기간, 재연장, 해제 검증, fencing token까지 같이 설계해야 한다.

### 언제 쓰는가

- 같은 배치가 중복 실행되면 안 될 때
- 크론 잡이 여러 인스턴스에서 동시에 뜰 때
- 동일 자원에 대한 쓰기 경합이 매우 클 때
- 외부 시스템과의 상호작용을 한 번만 수행해야 할 때

### 언제 쓰지 않는가

- DB 트랜잭션이나 유니크 키로 충분할 때
- 큐를 단일 소비자로 돌리면 되는 경우
- idempotency key로 중복 방지가 가능한 경우

---

## 깊이 들어가기

### 1. 락의 정체성

분산 락은 보통 아래 속성을 가진다.

- `lock key`: 어떤 자원을 잠그는가
- `owner token`: 누가 잡았는가
- `ttl`: 얼마나 오래 유효한가
- `renewal`: 작업이 길어질 때 연장할 수 있는가
- `fencing token`: 오래된 소유자를 어떻게 거를 것인가

`ttl`만 두면 "죽은 락"은 줄지만, "만료된 뒤에도 이전 소유자가 쓰기하는 문제"는 남는다.  
그래서 진짜 중요한 건 fencing token이다.

### 2. Redis 기반 분산 락

가장 흔한 형태는 다음이다.

```text
SET lock:order:123 <uuid> NX PX 30000
```

성공하면 락을 잡는다. 해제할 때는 `uuid`를 다시 확인하고 삭제해야 한다.

문제는 다음과 같다.

- 네트워크 지연으로 TTL이 먼저 만료될 수 있다.
- 오래 걸리는 작업이 락을 잃었는데도 계속 실행될 수 있다.
- 락 해제 스크립트가 원자적이지 않으면 남의 락을 풀 수 있다.

그래서 실무에서는 Lua 스크립트로 compare-and-delete를 만든다.

```lua
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
end
return 0
```

### 3. Fencing Token

락이 오래 걸려 만료되면, 이전 소유자가 여전히 작업을 이어갈 수 있다.  
이 문제를 막는 방식이 fencing token이다.

개념은 단순하다.

1. 락을 잡을 때 monotonically increasing token을 받는다.
2. downstream 저장소는 더 큰 token만 허용한다.
3. 오래된 소유자는 락이 만료돼도 최신 상태를 덮어쓰지 못한다.

이 방식은 분산 락보다 "쓰기 순서 제어"에 더 가깝다.

### 4. ZooKeeper/etcd 스타일

Redis는 빠르지만, 강한 조정(consensus)보다는 캐시 성격이 강하다.  
반면 ZooKeeper/etcd는 클러스터 조정에 더 적합하다.

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| Redis 락 | 빠르고 구현이 쉽다 | split-brain과 TTL 문제를 직접 다뤄야 한다 | 일반적인 배치/단기 락 |
| ZooKeeper/etcd | 소유권과 세션 관리가 강하다 | 운영 복잡도가 높다 | 조정이 중요한 인프라 작업 |
| DB row lock | 이미 있는 자원을 쓴다 | DB 병목이 된다 | 작은 규모, 강한 정합성 필요 |

### 5. 분산 락의 진짜 병목

분산 락은 성능 문제보다 가용성 문제를 먼저 만든다.

- 락 서버가 느려지면 전체 작업이 대기한다.
- TTL이 짧으면 중복 실행이 생긴다.
- TTL이 길면 장애 복구가 느려진다.
- 락 재시도가 많으면 오히려 stampede가 생긴다.

즉, 락은 병목을 제거하는 도구가 아니라 **병목을 하나로 모아 조정하는 도구**다.

---

## 실전 시나리오

### 시나리오 1: 스케줄러 중복 실행

배치 서버가 3대인데 cron이 각 서버에서 동시에 돈다.

대응:

- 시작 시 분산 락 획득
- 작업이 길면 TTL 연장
- 종료 시 compare-and-delete

### 시나리오 2: 재고 차감

동시에 주문이 몰리면 같은 상품 재고를 여러 서버가 건드린다.

선택지:

- DB row lock
- 낙관적 락 + 재시도
- 분산 락 + fencing token

재고처럼 정합성이 매우 중요하면, 분산 락보다 DB 레벨 제어가 더 단순한 경우가 많다.

### 시나리오 3: 외부 API 호출

한 번만 호출해야 하는 결제 승인/정산 작업이 중복되면 비용이 크게 난다.

이 경우 락만 믿지 말고 다음을 같이 넣는다.

- idempotency key
- dedup store
- 재시도 정책

---

## 코드로 보기

```pseudo
function acquireLock(key, owner, ttlMs):
    return redis.set(key, owner, NX=true, PX=ttlMs)

function releaseLock(key, owner):
    luaCompareAndDelete(key, owner)

function executeOnce(jobId):
    token = uuid()
    if !acquireLock("lock:job:" + jobId, token, 30000):
        return "busy"

    try:
        runJob()
    finally:
        releaseLock("lock:job:" + jobId, token)
```

### fencing token 예시

```java
public void updateInventory(long productId, long token, int delta) {
    Inventory inventory = inventoryRepository.find(productId);
    if (inventory.getFencingToken() > token) {
        return; // stale owner
    }
    inventory.apply(delta, token);
    inventoryRepository.save(inventory);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Redis 락 | 빠르고 익숙하다 | TTL/재연장/중복 실행에 취약 | 일반적인 작업 중복 방지 |
| ZooKeeper/etcd | 소유권 모델이 강하다 | 운영 복잡도가 높다 | 조정이 중요한 인프라 |
| DB lock | 단순하다 | DB 병목이 된다 | 정합성이 최우선일 때 |
| 락 없이 idempotency | 가장 안전한 경우가 많다 | 설계가 더 필요하다 | API 재시도가 가능한 경우 |

핵심 판단 기준은 "잠금이 필요한가"가 아니라 **락으로 해결하려는 문제를 더 단순한 제어로 풀 수 있는가**다.

---

## 꼬리질문

> Q: 분산 락만 있으면 중복 실행이 완전히 막히나요?
> 의도: TTL 만료와 stale owner 문제를 아는가 확인
> 핵심: 아니다. fencing token과 idempotency가 같이 필요할 수 있다.

> Q: Redis 락과 DB row lock은 언제 각각 선택하나요?
> 의도: 저장소별 제어 경계 이해
> 핵심: 강한 정합성은 DB, 넓은 작업 조정은 분산 락이 유리하다.

## 한 줄 정리

분산 락은 "한 번만 실행"을 보장하는 마법이 아니라, 만료와 stale owner까지 포함해 소유권을 관리하는 조정 장치다.
