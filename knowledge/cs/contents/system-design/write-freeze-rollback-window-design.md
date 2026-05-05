---
schema_version: 3
title: Write-Freeze Rollback Window 설계
concept_id: system-design/write-freeze-rollback-window-design
canonical: true
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- rollback-window-vs-transaction-rollback
- donor-read-only-drain
- reversible-soak-cutover-gate
aliases:
- write freeze rollback window
- reversible soak window
- donor read only drain
- cutover rollback window
- stateful cutover rollback soak
- freeze handoff rollback
- rollback window vs transaction rollback
symptoms:
- migration cutover 뒤에 rollback window를 얼마나 열어 둬야 할지 감이 안 온다
- rollback window와 DB transaction rollback을 같은 뜻으로 이해해서 문서를 잘못 찾고 있다
- donor를 언제 read-only로 남기고 언제 cleanup으로 넘겨도 되는지 헷갈린다
intents:
- design
- deep_dive
- comparison
- troubleshooting
prerequisites:
- system-design/receiver-warmup-cache-prefill-write-freeze-cutover-design
- system-design/traffic-shadowing-progressive-cutover-design
- system-design/cleanup-point-of-no-return-design
next_docs:
- system-design/dedicated-cell-drain-retirement-design
- system-design/config-rollback-safety-design
linked_paths:
- contents/system-design/receiver-warmup-cache-prefill-write-freeze-cutover-design.md
- contents/system-design/cleanup-point-of-no-return-design.md
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
- contents/system-design/stateful-workload-placement-failover-control-plane-design.md
- contents/system-design/shard-rebalancing-partition-relocation-design.md
- contents/system-design/read-after-write-routing-primer.md
- contents/database/transaction-basics.md
confusable_with:
- database/transaction-basics
- system-design/read-after-write-routing-primer
- system-design/cleanup-point-of-no-return-design
forbidden_neighbors: []
expected_queries:
- write freeze rollback window은 무엇이고 cutover 뒤에 왜 따로 필요해?
- rollback window와 transaction rollback은 무엇이 다른가?
- donor를 read-only로 남기는 reversible soak은 언제 끝내야 해?
- stateful cutover 뒤 fast rollback trigger를 어떻게 정하나?
contextual_chunk_prefix: |
  이 문서는 stateful cutover에서 짧은 write freeze 뒤 donor를 바로 지우지 않고
  reversible soak과 donor read-only drain을 얼마나 유지할지 설명하는
  deep_dive다. rollback window가 transaction rollback이랑 뭐가 달라,
  donor를 언제 정리해, cutover 직후 fast rollback trigger를 어떻게 잡아 같은
  질문을 post-cutover 상태 모델과 exit gate로 연결한다.
---
# Write-Freeze Rollback Window 설계

> 한 줄 요약: write-freeze rollback window 설계는 최종 handoff를 위해 잠깐 쓰기를 동결한 뒤 얼마나 오랫동안 빠른 rollback을 허용할지, donor/receiver를 어떤 상태로 유지할지 정하는 stateful cutover 운영 설계다.

retrieval-anchor-keywords: write freeze rollback window, fenced rollback window, handoff rollback, donor drain window, reversible cutover, freeze rollback boundary, stateful rollback soak, short freeze safety, cutover reversibility, donor tombstone delay

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md)
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
> - [Transaction Basics](../database/transaction-basics.md)

## 핵심 개념

짧은 write freeze로 handoff를 끝냈다고 해서 바로 완전히 안전한 것은 아니다.
전환 직후에도 다음 문제가 남는다.

- stale route가 늦게 도착
- receiver hit ratio가 아직 불안정
- donor drain 중 늦은 write가 발견
- rollback 필요 여부가 몇 분 뒤에 보임

그래서 실전에서는 freeze 자체보다 **freeze 이후 얼마 동안 reversible 상태를 유지할 것인가**가 중요하다.

여기서 말하는 rollback window는 **DB transaction의 `commit/rollback` 버튼**이 아니다.
이 문서는 이미 끝난 cutover를 운영적으로 얼마나 오래 되돌릴 수 있게 둘지 다루며,
DB 안의 트랜잭션 경계가 헷갈리면 [Transaction Basics](../database/transaction-basics.md)를 먼저 보는 편이 맞다.
또 "방금 쓴 값이 왜 안 보여?"처럼 read path 신선도 문제가 핵심이면
[Read-After-Write Routing Primer](./read-after-write-routing-primer.md)로 내려가는 편이 빠르다.

## 깊이 들어가기

### 1. 왜 rollback window가 필요한가

최종 handoff 직후 바로 donor를 제거하면 다음 상황에서 곤란하다.

- receiver latency spike
- hidden consistency bug
- cache prefill miss
- routing version drift

즉, final switch는 성공했더라도 "짧은 되돌릴 시간"이 필요하다.

### 2. Capacity Estimation

예:

- final write freeze 300ms
- rollback window 15분
- donor read-only drain 30분
- stale route tail 2분

이때 봐야 할 숫자:

- rollback decision latency
- stale route miss tail
- donor retention cost
- receiver error burst duration
- reversible window success rate

freeze는 짧아야 하지만 rollback window는 너무 짧아도 운영상 무의미할 수 있다.

### 3. Freeze 이후 상태 모델

보통 다음처럼 나눈다.

```text
FREEZE
 -> CUTOVER
 -> REVERSIBLE_SOAK
 -> DONOR_DRAIN
 -> IRREVERSIBLE_CLEANUP
```

핵심은 switch와 irreversible cleanup을 분리하는 것이다.

### 4. Donor state 유지 정책

rollback window 동안 donor를 어떻게 둘지 정해야 한다.

선택지:

- read-only donor
- hidden standby donor
- tombstoned but restorable
- immediate delete 금지

이 정책이 있어야 fast rollback이 가능하다.

### 5. Rollback trigger

대표 trigger:

- receiver error rate spike
- hit ratio collapse
- write verification mismatch
- stale route miss burst
- operator manual abort

즉, rollback window는 시간만의 문제가 아니라 어떤 신호가 오면 되돌릴지의 정책이 필요하다.

### 6. Scope granularity

rollback은 항상 전체일 필요가 없다.

- shard 단위
- tenant 단위
- cell 단위
- region 단위

scope를 좁힐 수 있을수록 donor 유지 비용과 blast radius를 줄일 수 있다.

### 7. Observability

운영자는 다음을 즉시 알아야 한다.

- 지금 reversible soak 구간인가
- rollback window가 몇 분 남았는가
- donor가 어떤 상태로 살아 있는가
- 어떤 trigger가 rollback 후보를 만들고 있는가
- irreversible cleanup이 아직 막혀 있는가

rollback window는 시간보다도 상태를 명확히 보여 주는 것이 중요하다.

## 실전 시나리오

### 시나리오 1: shard handoff 직후 receiver p99 급등

문제:

- write freeze는 성공했지만 receiver가 cold path를 제대로 흡수하지 못한다

해결:

- rollback window 안에서 donor로 되돌린다
- receiver는 debug mode로 격리한다
- prefill / warmup 정책을 보정한 뒤 재시도한다

### 시나리오 2: tenant reassignment 후 hidden stale route

문제:

- 일부 client가 아직 old partition으로 요청을 보낸다

해결:

- donor read-only drain을 유지한다
- stale route miss를 metric으로 본다
- rollback window 중이면 빠르게 되돌릴 수 있게 둔다

### 시나리오 3: cleanup 직전 late inconsistency 발견

문제:

- soak는 지나갔지만 donor purge 직전에 verification mismatch가 보인다

해결:

- irreversible cleanup을 즉시 멈춘다
- rollback boundary가 아직 남아 있으면 donor state를 다시 활성화한다
- 아니면 correction plan으로 전환한다

## 코드로 보기

```pseudo
function afterCutover(scope):
  state.mark(scope, "REVERSIBLE_SOAK")
  donor.setReadOnly(scope)
  startTimer(scope.rollbackWindow)

function maybeRollback(scope):
  if state.isReversible(scope) and rollbackTriggersFired(scope):
    switchBack(scope, donor)
    state.mark(scope, "ROLLED_BACK")
```

```java
public boolean canRollback(ScopeId scopeId) {
    return cutoverState.current(scopeId).isReversible()
        && donorStateRepository.available(scopeId);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| No rollback window | 단순하다 | hidden defect에 취약하다 | very low-risk move |
| Short reversible soak | 안전하다 | donor 비용이 남는다 | 대부분의 stateful cutover |
| Long donor retention | rollback이 쉽다 | 운영 비용과 ambiguity가 커진다 | high-value state |
| Scoped rollback window | 효율이 좋다 | scope metadata가 필요하다 | tenant/shard-aware platform |

핵심은 write-freeze rollback window 설계가 freeze의 부가물 아니라 **final handoff 이후 짧은 되돌림 가능성을 운영적으로 보존하는 상태 전이 설계**라는 점이다.

## 꼬리질문

> Q: freeze가 성공했으면 rollback window는 불필요한가요?
> 의도: handoff와 post-cutover risk 차이 이해 확인
> 핵심: 아니다. final race는 끝났더라도 cold path, stale routing, hidden mismatch는 전환 직후에야 보일 수 있다.

> Q: donor를 read-only로 남기는 이유는?
> 의도: reversible state 유지 확인
> 핵심: 늦은 read와 빠른 rollback 가능성을 보존하면서 new write 오염은 막기 위해서다.

> Q: rollback window를 너무 길게 두면 왜 문제인가요?
> 의도: safety vs ambiguity 균형 확인
> 핵심: donor 비용과 운영 복잡도, old/new ambiguity가 계속 남기 때문이다.

> Q: irreversible cleanup과 어떤 관계가 있나요?
> 의도: rollback boundary와 cleanup 연결 확인
> 핵심: rollback window가 끝나는 순간 cleanup gate를 열 수 있지만, 그 전에는 donor purge와 destructive cleanup을 막아야 한다.

## 한 줄 정리

Write-freeze rollback window 설계는 최종 handoff 후에도 잠시 donor와 rollback trigger를 유지해, stateful cutover의 마지막 숨은 위험을 흡수하는 운영 설계다.
