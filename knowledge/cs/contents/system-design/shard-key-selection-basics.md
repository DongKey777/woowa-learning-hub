# Shard Key Selection Basics

> 한 줄 요약: partition key와 shard key는 "무슨 엔티티 이름을 고를까"가 아니라, 어떤 읽기/쓰기 경로를 함께 묶고 시간이 지나도 얼마나 고르게 퍼질지를 정하는 설계 선택이다.

retrieval-anchor-keywords: shard key selection basics, partition key basics, choosing shard key, choosing partition key, hot partition detection, hot shard early warning, tenant_id sharding pitfall, user_id sharding pitfall, access pattern first, key skew, scatter gather basics, resharding cost, beginner sharding, shard key selection basics basics, shard key selection basics beginner

**난이도: 🟢 Beginner**

관련 문서:

- [Database Scaling Primer](./database-scaling-primer.md)
- [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)
- [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md)
- [Tenant Partition Strategy / Reassignment](./tenant-partition-strategy-reassignment-design.md)
- [분산 ID 생성 설계](./distributed-id-generation-design.md)
- [Job Queue 설계](./job-queue-design.md)
- [MVCC, Replication, Sharding](../database/mvcc-replication-sharding.md)
- [Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)

---

## 핵심 개념

좋은 partition key나 shard key는 보통 세 질문에 동시에 답한다.

- 어떤 읽기/쓰기 경로를 같은 파티션 안에 남길 것인가
- 지금뿐 아니라 6개월 뒤에도 트래픽이 고르게 퍼질 것인가
- skew가 커졌을 때 split, move, promote 같은 탈출 경로가 있는가

초보자가 자주 하는 실수는 `tenant_id`, `user_id`, `created_at`처럼 눈에 잘 띄는 필드를 바로 key로 고르는 것이다.
하지만 key는 "식별자가 유명한가"보다 **access pattern, skew, 운영 탈출 경로**를 먼저 봐야 한다.

---

## 깊이 들어가기: Key 선택 기준과 일반적 실수

### 1. Partition key와 shard key는 비슷하지만 변경 비용이 다르다

| 개념 | 주 목적 | 잘못 고르면 생기는 일 |
|---|---|---|
| Partition key | pruning, ordering, local processing | hot partition, cross-partition scan |
| Shard key | write/storage scale, blast radius 분리 | hot shard, scatter-gather, 비싼 resharding |

shard key는 "지금 편한 필드"보다 "나중에 바꾸기 어려운 필드"라는 감각으로 봐야 한다.

### 2. 후보는 엔티티 이름이 아니라 access pattern으로 좁힌다

먼저 아래 네 가지를 적어 두는 편이 안전하다.

1. 가장 뜨거운 write 경로는 무엇인가
2. 반드시 한 파티션 안에서 끝나야 하는 read는 무엇인가
3. scatter-gather를 허용할 read는 무엇인가
4. retention이나 archive 때문에 시간 축 분리가 필요한가

| 자주 있는 경로 | 먼저 떠올릴 key | 바로 확정하면 안 되는 이유 |
|---|---|---|
| 사용자 자신의 주문/세션/장바구니 조회 | `user_id` | 운영자 화면, 정산은 scatter될 수 있다 |
| tenant 단위 admin, billing 작업 | `tenant_id` | 상위 몇 개 tenant가 전체 부하를 흔들 수 있다 |
| 이벤트 로그, 시계열 retention | `created_at` 또는 time bucket | 최신 bucket 하나에 write가 몰리기 쉽다 |

### 3. `tenant_id`, `user_id`가 자주 틀리는 이유

`tenant_id`와 `user_id` 자체가 나쁜 것은 아니다. 문제는 **너무 빨리 기본값처럼 채택하는 것**이다.

- 상위 1% tenant나 user가 전체 트래픽에서 얼마나 큰 비중을 가지는가
- hot tenant나 power user가 생기면 따로 떼어낼 수 있는가

multi-tenant SaaS에서 `tenant_id`를 shard key로 잡는 것은 나쁘지 않다.
하지만 "큰 tenant를 dedicated shard나 cell로 승격하는 경로"가 없으면, 가장 큰 고객 한 명이 전체 배치를 결정하게 된다.

---

## 깊이 들어가기: Hot Partition 조기 감지와 탈출 경로

### 4. Hot partition은 장애 전에 조기 신호가 먼저 보인다

| 조기 신호 | 흔한 원인 |
|---|---|
| hottest partition의 QPS나 bytes가 median보다 지속적으로 몇 배 높다 | natural key 편중, 최신 bucket 집중 |
| 상위 tenant/user의 비중이 계속 올라간다 | premature tenant/user key |
| 특정 partition만 lag, compaction, lock wait가 길다 | append hotspot, skewed write |
| scatter-gather 비율이 커진다 | 잘못된 locality 가정 |
| 재배치를 해도 같은 partition이 다시 뜨거워진다 | structural hot key |

평균만 보고 있으면 이미 늦다. per-partition QPS, top N tenant/user concentration, scatter-gather ratio를 partition 단위로 추적해야 한다.

### 5. 좋은 key는 운영 탈출 경로까지 포함해서 고른다

안전한 결정 흐름:

1. hottest read/write 세 경로를 적는다
2. 후보 key마다 local로 끝나는 경로와 scatter되는 경로를 적는다
3. cardinality보다도 top-N skew를 먼저 본다
4. hot tenant나 hot user가 생기면 split, promote, remap 중 무엇이 가능한지 정한다

- "cardinality가 높다"는 이유만으로 안전하지 않다
- "rebalance하면 되겠지"는 key 선택의 대체재가 아니다
- shard key는 **잘못 골라도 당장은 돌아가고, 나중에야 크게 비싸진다**

---

## 실전 시나리오

### 시나리오 1: B2B SaaS 주문 시스템

문제:

- 대부분의 admin API가 tenant 기준이다
- 하지만 상위 몇 개 enterprise tenant가 전체 write의 대부분을 만든다

판단:

- `tenant_id`는 운영 설명과 recovery에는 잘 맞는다
- 대신 hot tenant 승격 경로가 없으면 큰 고객 하나가 hot shard가 된다

실전 감각:

- `tenant_id`를 아예 버리기보다
- placement directory와 premium tenant split-out 경로를 같이 설계하는 편이 현실적이다

### 시나리오 2: 소비자 서비스 주문 내역

문제:

- 사용자 본인의 최근 주문 조회가 가장 많다
- 운영자와 정산 배치는 store/merchant 단위로 본다

판단:

- `user_id`는 user-facing read path에는 자연스럽다
- 하지만 merchant/tenant 운영 path는 scatter될 수 있다

실전 감각:

- primary write locality와 운영 조회 path를 분리해서 생각한다
- shard key 하나로 모든 조회를 만족시키려 하지 말고 secondary index나 read model을 같이 둔다

### 시나리오 3: 이벤트 로그 저장소

문제:

- retention 때문에 시간 기반 partitioning이 필요하다
- ingest는 항상 "지금"에 몰린다

판단:

- time bucket은 partition pruning에는 좋다
- 하지만 time만으로 shard routing까지 하면 newest shard가 계속 뜨거워질 수 있다

실전 감각:

- "시간축 partitioning"과 "shard 분산"을 같은 문제로 보지 않는다
- hash + time partition처럼 역할을 분리하는 편이 안전하다

---

## 코드로 보기

```pseudo
function evaluateKey(candidate):
  locality = hotPathCoverage(candidate)
  skew = topNShare(candidate)
  scatter = scatterGatherRate(candidate)
  escape = canSplitOrPromoteHeavyOwner(candidate)

  return chooseHigh(locality)
       and chooseLow(skew, scatter)
       and require(escape)
```

이 pseudo code의 핵심은 "가장 유명한 ID"를 고르는 것이 아니라,
`locality`, `skew`, `escape hatch`를 같이 본다는 점이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 맞는가 |
|---|---|---|---|
| `tenant_id` 중심 | 운영 설명과 격리가 쉽다 | 큰 tenant skew에 약하다 | tenant-scoped workload가 지배적일 때 |
| `user_id` 중심 | 사용자 단위 locality가 좋다 | 운영/집계 조회가 scatter될 수 있다 | user-centric product일 때 |
| 시간 bucket 중심 | pruning과 retention이 쉽다 | newest partition이 뜨거워진다 | 시계열 데이터 정리용 partitioning |
| hash 또는 composite key | 분산이 좋아진다 | 사람이 reasoning하기 어렵고 lookup이 복잡해진다 | locality보다 spread가 더 중요할 때 |
| directory + 승격 가능한 hybrid | hot owner 탈출 경로가 좋다 | control plane이 필요하다 | tenant/user skew가 큰 성장형 시스템 |

## 꼬리질문

> Q: multi-tenant면 shard key는 항상 `tenant_id`가 맞나요?
> 의도: 자연스러운 business key와 실제 skew를 구분하는지 확인
> 핵심: 아니다. tenant workload 비중, 상위 tenant skew, 승격 경로를 같이 봐야 한다.

> Q: `user_id` cardinality가 높으면 안전한 것 아닌가요?
> 의도: cardinality와 skew 차이 이해 확인
> 핵심: 아니다. 상위 user 집중, 운영 조회 scatter, background path를 같이 봐야 한다.

> Q: hot partition은 rebalancing으로만 해결하면 되나요?
> 의도: placement 문제와 key 설계 문제를 구분하는지 확인
> 핵심: 아니다. 같은 partition이 반복해서 뜨거워지면 key 자체가 잘못됐을 수 있다.

## 한 줄 정리

좋은 shard key는 "눈에 띄는 식별자"가 아니라, **핫한 경로를 local하게 묶고도 시간이 지나며 한쪽으로 몰리지 않게 하며, 몰릴 때 탈출 경로까지 설명할 수 있는 key**다.
