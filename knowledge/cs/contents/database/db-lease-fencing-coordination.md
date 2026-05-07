---
schema_version: 3
title: DB Lease and Fencing Token
concept_id: database/db-lease-fencing-coordination
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- db-lease
- fencing-token
- distributed-lock
- stale-worker
aliases:
- db lease fencing coordination
- DB lease와 fencing token
- lease
- fencing token
- clock skew
- GC pause
- distributed lock
- stale worker
- DB lease fencing
- 분산 작업 lease
symptoms:
- lease 만료 후 새 worker가 소유권을 얻었는데 GC pause에서 돌아온 옛 worker가 뒤늦게 write한다
- Redis lock이나 DB lease를 잡았다는 사실만 믿고 stale write를 막는 fencing token 검증을 두지 않는다
- lease row가 hot spot이 되거나 TTL heartbeat 설정 때문에 장애 감지와 DB 부하가 흔들린다
intents:
- deep_dive
- design
- troubleshooting
prerequisites:
- database/transaction-isolation-locking
- database/deadlock-case-study
- database/replication-failover-split-brain
next_docs:
- database/application-level-fencing-token-propagation
- database/stale-lease-renewal-failure-fencing
- database/ghost-reads-mixed-routing-write-fence-tokens
linked_paths:
- contents/database/transaction-isolation-locking.md
- contents/database/deadlock-case-study.md
- contents/database/replication-failover-split-brain.md
- contents/database/application-level-fencing-token-propagation.md
- contents/database/stale-lease-renewal-failure-fencing.md
- contents/database/ghost-reads-mixed-routing-write-fence-tokens.md
confusable_with:
- database/advisory-locks-vs-row-locks
- database/application-level-fencing-token-propagation
- database/stale-lease-renewal-failure-fencing
- database/replication-failover-split-brain
forbidden_neighbors: []
expected_queries:
- DB lease는 소유권 표시이고 fencing token은 stale write를 막는 장치라는 차이를 설명해줘
- lease만 있으면 GC pause나 network partition 뒤 오래된 worker가 최신 결과를 덮을 수 있는 이유가 뭐야?
- fencing token이 단조 증가하고 더 낮은 token의 write를 거부해야 하는 원리를 SQL 예시로 알려줘
- DB lease row가 hot spot이 되거나 TTL heartbeat가 너무 짧으면 어떤 운영 문제가 생겨?
- Redis lock이나 DB lease에 fencing token이 없으면 분산 cron 중복 실행에서 왜 위험해?
contextual_chunk_prefix: |
  이 문서는 DB Lease and Fencing Token deep dive로, DB를 coordination store로 쓰는 lease가
  worker ownership을 표시하지만 GC pause, clock skew, network delay 뒤 stale worker write를 막으려면
  monotonic fencing token을 모든 write에 검증해야 함을 설명한다.
---
# DB Lease와 Fencing Token

> 한 줄 요약: lease는 “누가 먼저 잡았는가”를 말해 주지만, fencing token만 있어야 “오래된 주체가 아직도 쓰지 못한다”를 막을 수 있다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Deadlock Case Study](./deadlock-case-study.md), [Replication Failover and Split Brain](./replication-failover-split-brain.md)
retrieval-anchor-keywords: lease, fencing token, clock skew, GC pause, distributed lock

## 핵심 개념

DB를 coordinator처럼 써서 분산 작업의 주인을 정하려면 lease가 필요하다.  
하지만 lease만으로는 충분하지 않다.

왜 중요한가:

- cron job이나 배치 worker가 중복 실행될 수 있다
- 네트워크 분할이나 GC pause로 오래된 worker가 다시 살아날 수 있다
- 만료된 lease를 가진 주체가 최신 주체의 데이터를 덮어쓸 수 있다

즉 lease는 **소유권 표시**이고, fencing token은 **stale write 방지 장치**다.

## 깊이 들어가기

### 1. 단순 lease가 왜 위험한가

가장 흔한 패턴은 다음과 같다.

- `expires_at`이 지나면 다른 worker가 lease를 가져간다
- 주기적으로 heartbeat를 갱신한다

문제는 시계와 실행 지연이다.

- clock skew 때문에 아직 만료되지 않은 lease를 만료로 판단할 수 있다
- GC pause나 스레드 정체로 heartbeat가 늦을 수 있다
- 네트워크 순간 장애 후, 원래 주체가 늦게 돌아와도 자기 작업을 계속할 수 있다

### 2. fencing token이 왜 필요한가

lease가 바뀔 때마다 단조 증가하는 token을 발급하면, 오래된 주체의 쓰기를 거를 수 있다.

핵심 규칙:

- 새 lease를 얻을 때 token을 증가시킨다
- 모든 후속 write는 이 token을 함께 보낸다
- 저장소는 더 낮은 token의 write를 거부한다

이렇게 해야 “오래된 worker가 뒤늦게 commit”하는 상황을 막을 수 있다.

### 3. DB lease를 쓸 때의 현실

DB lease는 구현이 쉽지만, 그 자체가 핫 로우가 될 수 있다.

- 한 lease row에 접근이 몰리면 contention이 생긴다
- lease 갱신 주기가 너무 짧으면 DB 부하가 커진다
- TTL이 너무 길면 장애 감지가 늦어진다

즉 lease는 정합성과 가용성의 균형점을 잘 잡아야 한다.

### 4. 언제 DB lease가 적합한가

- 하나의 배치 작업만 실행되면 되는 경우
- 외부 coordinator를 추가하고 싶지 않은 경우
- 락 범위가 작고 단순한 경우

반대로, 강한 분산 coordination이 필요하면 etcd/ZooKeeper 같은 전용 도구가 더 적합할 수 있다.

## 실전 시나리오

### 시나리오 1: 야간 정산 job이 두 번 돈다

한 worker가 이미 정산을 진행하는데, 다른 worker가 lease 만료를 오해하고 같은 job을 다시 시작한다.  
이때 fencing token이 없으면 중복 반영이 발생한다.

### 시나리오 2: 오래 멈춘 worker가 뒤늦게 write한다

GC pause나 네트워크 문제로 기존 worker가 늦게 돌아왔는데, 이미 새 주체가 lease를 얻었다.  
옛 worker가 계속 쓰면 최신 결과를 덮어쓸 수 있다.

### 시나리오 3: 분산 cron의 중복 실행

매 분 실행되는 작업이 여러 인스턴스에서 동시에 시작되면, lease는 “한 명만 뛰게” 만들고 fencing은 “늦게 도착한 사람이 결과를 못 쓰게” 만든다.

## 코드로 보기

```sql
CREATE TABLE distributed_lease (
  name VARCHAR(100) PRIMARY KEY,
  owner_id VARCHAR(100) NOT NULL,
  fencing_token BIGINT NOT NULL,
  expires_at DATETIME NOT NULL
);

-- lease 획득
UPDATE distributed_lease
SET owner_id = 'worker-a',
    fencing_token = fencing_token + 1,
    expires_at = NOW() + INTERVAL 30 SECOND
WHERE name = 'billing-reconciler'
  AND expires_at < NOW();

-- 현재 token 조회
SELECT fencing_token
FROM distributed_lease
WHERE name = 'billing-reconciler';
```

```sql
-- stale write 차단 예시
UPDATE settlement
SET status = 'DONE',
    last_fencing_token = 42
WHERE id = 9001
  AND last_fencing_token < 42;
```

lease는 잡는 것보다, **놓쳤을 때도 옛 주체가 못 쓰게 하는 장치**가 더 중요하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| DB lease | 구현이 쉽다 | 핫 로우가 되기 쉽다 | 단순한 배치/cron |
| DB lease + fencing | stale write를 막는다 | 저장소 설계가 더 필요하다 | 결과 덮어쓰기가 치명적일 때 |
| Redis lock | 빠르다 | fencing 없으면 위험하다 | 가벼운 분산 조정 |
| etcd/ZooKeeper | coordination이 강하다 | 운영 비용이 있다 | 전용 리더 선출이 필요할 때 |

## 꼬리질문

> Q: lease만으로는 왜 충분하지 않나요?
> 의도: 만료 후 stale worker의 write 문제를 아는지 확인
> 핵심: 오래된 주체가 다시 살아나 결과를 덮을 수 있다

> Q: fencing token은 무엇을 막아주나요?
> 의도: stale write 차단 원리 이해 여부 확인
> 핵심: 더 낮은 token의 늦은 쓰기를 거른다

> Q: DB lease가 핫스팟이 될 수 있나요?
> 의도: coordination row 자체의 contention을 아는지 확인
> 핵심: lease row에 접근이 몰리면 또 다른 병목이 된다

## 한 줄 정리

DB lease는 분산 작업의 소유권을 나누는 장치고, fencing token은 만료된 소유자가 뒤늦게 결과를 덮어쓰지 못하게 하는 안전장치다.
