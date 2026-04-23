# MVCC, Replication, Sharding

**난이도: 🔴 Advanced**

> 데이터베이스 확장성과 동시성 관점에서 자주 나오는 개념 정리

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Read Committed vs Repeatable Read Anomalies](./read-committed-vs-repeatable-read-anomalies.md), [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md), [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md), [Replication Failover and Split Brain](./replication-failover-split-brain.md), [Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control](./multi-tenant-tenant-id-index-topology.md)

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [MVCC](#mvcc)
- [Replication](#replication)
- [Sharding](#sharding)
- [자주 헷갈리는 지점](#자주-헷갈리는-지점)
- [샤드 키를 볼 때 던질 질문](#샤드-키를-볼-때-던질-질문)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

> retrieval-anchor-keywords:
> - MVCC
> - multi-version concurrency control
> - replication
> - read replica
> - replication lag
> - sharding
> - shard key
> - horizontal partitioning
> - repeatable read snapshot
> - undo log version chain
> - read after write
> - primary replica failover
> - partitioning vs sharding
> - resharding
> - hot shard
> - shard hotspot
> - 방금 쓴 데이터 안 보임
> - replica lag
> - snapshot isolation

## 이 문서 다음에 보면 좋은 문서

- MVCC를 격리수준, snapshot, phantom read 관점으로 더 정확히 보려면 [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)과 [Read Committed vs Repeatable Read Anomalies](./read-committed-vs-repeatable-read-anomalies.md)를 이어 본다.
- replication을 실제 사용자 증상인 `old data after write`, `read-after-write`, `stale read`로 연결하려면 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)와 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)이 바로 이어진다.
- failover, split-brain, shard hotspot 같은 운영 문제로 확장하려면 [Replication Failover and Split Brain](./replication-failover-split-brain.md)와 [Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control](./multi-tenant-tenant-id-index-topology.md)을 같이 보는 편이 좋다.

## 왜 중요한가

백엔드 면접에서는 단순 CRUD를 넘어

- 동시성에서 읽기/쓰기가 어떻게 공존하는지
- DB를 어떻게 확장하는지

를 묻는 경우가 많다.

---

## MVCC

MVCC(Multi-Version Concurrency Control)는 **동시에 접근하는 트랜잭션들이 서로 덜 막히도록 여러 버전의 데이터를 관리하는 방식**이다.

핵심 감각:

- 읽는 쪽은 특정 시점의 snapshot을 본다
- 쓰는 쪽은 새 버전을 만든다

장점:

- 읽기와 쓰기 충돌을 줄일 수 있다
- 동시성 성능이 좋아질 수 있다

단점:

- 내부 동작을 이해하지 못하면 “왜 최신 값이 바로 안 보이는지” 헷갈릴 수 있다
- undo/version 관리 비용이 있다

---

## Replication

Replication은 **같은 데이터를 여러 DB 서버에 복제하는 것**이다.

대표 목적:

- 읽기 부하 분산
- 장애 대비

예:

- Primary / Replica

주의:

- 복제 지연(replication lag)이 생길 수 있다
- 방금 쓴 데이터가 replica에는 아직 안 보일 수 있다

즉 읽기 확장은 쉬워지지만, 읽기 일관성은 별도로 고민해야 한다.

---

## Sharding

Sharding은 **데이터를 여러 DB에 나눠 저장하는 것**이다.

예:

- 사용자 ID 범위별 분리
- 지역별 분리

Replication이 “같은 데이터 복제”라면,
Sharding은 “데이터 분산 저장”이다.

장점:

- 데이터 크기를 수평으로 확장할 수 있다
- 특정 샤드 단위로 부하를 나눌 수 있다

단점:

- 샤드 키 설계가 어렵다
- 조인, 집계, 재샤딩이 복잡하다

---

## 자주 헷갈리는 지점

### MVCC는 replication이 아니다

MVCC는 한 DB 노드 안에서 동시 읽기/쓰기를 어떻게 공존시킬지의 문제다.  
즉 snapshot을 어떤 시점으로 볼지, undo/version chain을 어떻게 따라갈지가 핵심이다.

반대로 replication은 **커밋된 결과를 다른 노드로 어떻게 전파할지**의 문제다.  
그래서 MVCC를 이해해도 replica lag나 failover consistency가 자동으로 해결되지는 않는다.

### replication은 읽기 확장과 일관성 비용을 같이 만든다

read replica를 붙이면 조회 부하는 분산되지만, 다음 질문이 바로 따라온다.

- 방금 쓴 값이 언제 replica에 보이는가
- failover 직후 어떤 commit까지 안전한가
- 사용자 세션을 primary에 pinning해야 하는가

즉 replication은 단순 복제가 아니라 **read-after-write를 얼마까지 보장할지 정하는 설계 문제**다.

### partitioning과 sharding은 비슷해 보여도 다르다

- partitioning
  - 한 DB 인스턴스 안에서 테이블을 논리적으로 나누는 것
- sharding
  - 여러 DB 인스턴스에 데이터를 물리적으로 나누는 것

partition pruning은 같은 노드 안의 locality 최적화에 가깝고, sharding은 라우팅·재분배·크로스샤드 집계까지 포함하는 더 큰 운영 문제다.

---

## 샤드 키를 볼 때 던질 질문

- 대부분의 조회와 쓰기가 같은 shard key를 기준으로 locality를 얻는가
- 특정 tenant/user가 hot shard를 만들 가능성이 있는가
- cross-shard join이나 aggregate가 핵심 경로에 있는가
- 나중에 resharding할 때 lookup table, dual write, backfill 경로를 감당할 수 있는가
- 샤딩 대신 partitioning이나 read replica만으로도 현재 문제를 풀 수 있는가

샤딩은 “데이터가 많다”는 이유만으로 바로 고르는 카드가 아니다.  
대부분은 access pattern, hotspot, 재분배 비용을 숫자로 확인한 뒤에야 정당화된다.

---

## 추천 공식 자료

- PostgreSQL MVCC:
  - https://www.postgresql.org/docs/current/mvcc-intro.html
- PostgreSQL Replication:
  - https://www.postgresql.org/docs/current/high-availability.html

---

## 면접에서 자주 나오는 질문

### Q. MVCC란 무엇인가요?

- 동시에 실행되는 트랜잭션들이 서로 덜 막히도록 여러 버전의 데이터를 관리하는 방식이다.

### Q. Replication과 Sharding 차이는 무엇인가요?

- Replication은 같은 데이터를 복제하는 것이고,
- Sharding은 데이터를 분산 저장하는 것이다.

### Q. Replica를 쓰면 항상 읽기 성능이 좋아지나요?

- 읽기 분산은 가능하지만 복제 지연과 일관성 문제를 함께 고려해야 한다.
