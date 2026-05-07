---
schema_version: 3
title: Primary Switch and Write Fencing
concept_id: database/primary-switch-write-fencing
canonical: true
category: database
difficulty: intermediate
doc_role: playbook
level: intermediate
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- failover
- write-fencing
- fencing-epoch
- primary-switch
aliases:
- primary switch
- write fencing
- fencing epoch
- stale primary
- promotion cutover
- visibility window
- commit horizon
- primary switch write fencing
- 옛 primary write 차단
- failover write fence
symptoms:
- primary switch 후 read route만 바꾸고 old primary의 stale write를 fencing하지 않아 split brain write corruption 위험이 있어
- DNS TTL, pool, worker cache 때문에 일부 writer가 옛 endpoint로 write를 보낼 수 있어 epoch 검증이 필요해
- failover cutover에서 promotion, route switch, write fence, commit horizon verification 순서를 잡아야 해
intents:
- troubleshooting
- design
prerequisites:
- database/replication-failover-split-brain
- database/failover-promotion-read-divergence
next_docs:
- database/ghost-reads-mixed-routing-write-fence-tokens
- database/failover-visibility-window-topology-cache-playbook
- database/commit-horizon-after-failover-verification
linked_paths:
- contents/database/replication-failover-split-brain.md
- contents/database/failover-promotion-read-divergence.md
- contents/database/ghost-reads-mixed-routing-write-fence-tokens.md
- contents/database/failover-visibility-window-topology-cache-playbook.md
- contents/database/commit-horizon-after-failover-verification.md
- contents/spring/spring-persistence-transaction-web-service-repository-primer.md
confusable_with:
- database/replication-failover-split-brain
- database/ghost-reads-mixed-routing-write-fence-tokens
- database/commit-horizon-after-failover-verification
forbidden_neighbors: []
expected_queries:
- primary switch에서 read routing보다 write fencing이 더 중요한 이유가 뭐야?
- failover 후 옛 primary의 늦은 write를 fencing epoch로 어떻게 막아?
- DNS TTL이나 connection pool에 남은 stale writer를 어떻게 거절해야 해?
- primary promotion cutover에서 bump epoch, fence old primary, switch write route 순서를 설명해줘
- commit horizon verification 없이 primary switch를 마치면 어떤 write corruption 위험이 있어?
contextual_chunk_prefix: |
  이 문서는 primary switch와 failover cutover에서 old primary stale write를 fencing epoch, write fence token, commit horizon verification으로 막는 intermediate playbook이다.
  primary switch write fencing, stale primary, 옛 primary write 차단 질문이 본 문서에 매핑된다.
---
# Primary Switch와 Write Fencing

> 한 줄 요약: primary가 바뀌는 순간에는 읽기 라우팅보다 write fencing이 더 중요하고, 옛 primary의 늦은 write를 반드시 막아야 한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-persistence-transaction-web-service-repository-primer.md)

관련 문서: [Replication Failover and Split Brain](./replication-failover-split-brain.md), [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md), [Ghost Reads와 Mixed Routing Write Fence Tokens](./ghost-reads-mixed-routing-write-fence-tokens.md), [Failover Visibility Window, Topology Cache, and Freshness Playbook](./failover-visibility-window-topology-cache-playbook.md), [Commit Horizon After Failover, Loss Boundaries, and Verification](./commit-horizon-after-failover-verification.md)
retrieval-anchor-keywords: primary switch, write fencing, fencing epoch, stale primary, promotion cutover, visibility window, commit horizon, primary switch write fencing basics, primary switch write fencing beginner, primary switch write fencing intro, database basics, beginner database, 처음 배우는데 primary switch write fencing, primary switch write fencing 입문, primary switch write fencing 기초

## 핵심 개념

Primary switch는 기존 primary를 내리고 새 primary를 올리는 과정이다.
이때 가장 위험한 것은 옛 primary가 늦게 살아나서 최신 write를 덮는 것이다.

왜 중요한가:

- failover 이후에도 옛 primary가 write를 받아버릴 수 있다
- 읽기 divergence보다 write corruption이 훨씬 치명적이다
- fencing 없이는 split brain이 잠깐만 있어도 데이터가 갈라질 수 있다

즉 primary switch는 “새 노드 선택”이 아니라 **옛 주체의 write 권한 회수**다.

## 깊이 들어가기

### 1. cutover의 핵심

cutover가 안전하려면 새 primary를 올리는 것과 동시에 옛 primary를 확실히 막아야 한다.

- read-only 강제
- 네트워크 차단
- fencing epoch 증가
- application route 전환

이 네 가지가 함께 가야 한다.

### 2. 왜 write fencing이 먼저인가

옛 primary는 늦은 요청을 계속 받을 수 있다.

- connection pool에 남아 있을 수 있다
- DNS TTL이 남아 있을 수 있다
- 일부 worker가 옛 endpoint를 쓰고 있을 수 있다

write fencing이 없으면 마지막 write가 최신 상태를 망가뜨린다.

### 3. fencing epoch

새 primary로 넘어갈 때마다 epoch를 올리고, 모든 write에 epoch를 붙인다.

- 새 epoch만 허용
- 낮은 epoch는 거절
- stale writer는 결과를 못 쓴다

이렇게 해야 primary switch가 데이터 경계로 작동한다.

### 4. 읽기와 쓰기를 같이 보면 안 되는 이유

read routing이 늦어도 문제지만, write fencing이 늦으면 더 큰 문제다.
읽기는 다소 stale해도 회복할 수 있지만, 잘못된 write는 복구가 어렵다.

## 실전 시나리오

### 시나리오 1: failover 직후 옛 primary가 살아남

쓰기 endpoint가 아직 옛 primary를 가리키면 최신 상태를 덮을 수 있다.
fencing이 필수다.

### 시나리오 2: promotion은 끝났는데 일부 worker가 옛 노드 사용

라우팅이 완전히 바뀌지 않았고, stale worker가 write를 보낸다.
epoch 검증이 없으면 사고가 난다.

### 시나리오 3: 네트워크 분할 후 다시 합류

split brain이 잠깐이라도 있었으면, primary switch 이후에도 write conflict를 검사해야 한다.

## 코드로 보기

```sql
CREATE TABLE primary_epoch (
  cluster_name VARCHAR(100) PRIMARY KEY,
  epoch BIGINT NOT NULL
);

UPDATE account_state
SET balance = balance - 1000,
    epoch = 42
WHERE id = 1
  AND epoch < 42;
```

```text
switch:
  promote new primary
  bump epoch
  fence old primary
  switch write route
```

primary switch의 핵심은 새 primary를 세우는 것이 아니라, **옛 primary의 write를 거절하는 것**이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| route only switch | 빠르다 | stale write 위험 | 거의 없음 |
| fencing epoch switch | 안전하다 | 구현이 필요하다 | 일반적 해법 |
| hard shutdown old primary | 확실하다 | 복구 비용이 있다 | 고위험 시스템 |
| read-only only | 일부 보호 | write는 막지 못할 수 있다 | 임시 조치 |

## 꼬리질문

> Q: primary switch에서 왜 write fencing이 중요한가요?
> 의도: stale primary의 늦은 write 위험을 아는지 확인
> 핵심: 읽기보다 쓰기 corruption이 더 치명적이기 때문이다

> Q: epoch는 왜 올려야 하나요?
> 의도: 단조 증가하는 주체 버전을 이해하는지 확인
> 핵심: 옛 주체의 write를 거절하기 위해서다

> Q: read routing만 바꾸면 충분한가요?
> 의도: 읽기와 쓰기 보호를 분리하는지 확인
> 핵심: 아니다, write fence가 같이 필요하다

## 한 줄 정리

Primary switch는 새 primary를 세우는 일이 아니라, 옛 primary의 늦은 write를 fencing epoch로 차단하는 일이다.
