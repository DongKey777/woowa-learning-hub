---
schema_version: 3
title: Guard Row vs Serializable Retry vs Reconciliation for Set Invariants
concept_id: database/guard-row-vs-serializable-vs-reconciliation-set-invariants
canonical: true
category: database
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- set-invariant-enforcement-chooser
- guard-row-vs-serializable
- reconciliation-drift-repair
aliases:
- guard row vs serializable retry vs reconciliation
- set invariant
- count invariant
- sum invariant
- capacity oversell
- minimum staffing
- quota guard
- invariant drift repair
- serializable retry telemetry
- guard row reconciliation
symptoms:
- capacity나 quota 같은 count/sum set invariant를 guard row, serializable retry, reconciliation 중 어디서 막을지 모르겠어
- SELECT COUNT 후 insert 같은 read-then-write 경합으로 write skew가 나고 있어
- guard row가 즉시 차단하지 못한 우회 쓰기나 cleanup lag를 reconciliation으로 잡아야 해
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/range-invariant-enforcement-write-skew-phantom
- database/active-predicate-alignment-capacity-guards
next_docs:
- database/serializable-retry-telemetry-set-invariants
- database/summary-drift-detection-bounded-rebuild
- database/hold-expiration-predicate-drift
- database/hot-row-contention-counter-sharding
linked_paths:
- contents/database/range-invariant-enforcement-write-skew-phantom.md
- contents/database/active-predicate-alignment-capacity-guards.md
- contents/database/hot-row-contention-counter-sharding.md
- contents/database/serializable-retry-telemetry-set-invariants.md
- contents/database/write-skew-phantom-read-case-studies.md
- contents/database/write-skew-detection-compensation-patterns.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/transaction-boundary-isolation-locking-decision-framework.md
- contents/database/summary-drift-detection-bounded-rebuild.md
- contents/database/hold-expiration-predicate-drift.md
confusable_with:
- database/range-invariant-enforcement-write-skew-phantom
- database/active-predicate-alignment-capacity-guards
- database/summary-drift-detection-bounded-rebuild
forbidden_neighbors: []
expected_queries:
- capacity나 quota 같은 set invariant는 guard row, serializable retry, reconciliation 중 무엇으로 막아야 해?
- guard row는 커밋 전 admission control이고 reconciliation은 커밋 후 repair라는 차이를 설명해줘
- serializable retry는 query predicate 기반 write skew를 언제 현실적으로 막아?
- hard invariant에 reconciliation only가 거의 맞지 않는 이유는 뭐야?
- hot aggregate에서 guard row가 병목이면 striped guard row나 ledger로 언제 바꿔야 해?
contextual_chunk_prefix: |
  이 문서는 count/sum 기반 set invariant를 guard row, serializable retry, reconciliation 중 어느 방어선에서 막을지 고르는 advanced chooser다.
  guard row vs serializable retry, set invariant, capacity oversell, reconciliation drift repair 같은 자연어 설계 질문이 본 문서에 매핑된다.
---
# Guard Row vs Serializable Retry vs Reconciliation for Set Invariants

> 한 줄 요약: capacity나 minimum staffing처럼 count/sum으로 정의되는 set invariant는 guard row로 즉시 차단하고, serializable retry는 재모델링이 어려운 조회-판단 경로를 감싸며, reconciliation은 drift와 우회 쓰기를 잡는 복구 루프로 써야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Active Predicate Alignment for Capacity Guards](./active-predicate-alignment-capacity-guards.md)
- [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md)
- [Serializable Retry Telemetry for Set Invariants](./serializable-retry-telemetry-set-invariants.md)
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)
- [Write Skew Detection과 Compensation Patterns](./write-skew-detection-compensation-patterns.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
- [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)
- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)

retrieval-anchor-keywords: guard row, serializable retry, reconciliation, set invariant, count invariant, sum invariant, capacity oversell, minimum staffing, quota guard, bounded retry, invariant drift repair, write skew, active predicate drift, reservation ledger, admission control, guard row hotspot, striped guard row, capacity bucket, expires_at released_at alignment, guard row reconciliation predicate, serializable retry telemetry, retry budget, sqlstate 40001, hot aggregate observability

## 핵심 개념

capacity, quota, minimum staffing 같은 규칙은 row 하나의 값보다 **집합의 count/sum이 안전한가**를 묻는다.  
그래서 `SELECT COUNT(*)`나 `SUM(qty)`를 보고 애플리케이션이 판단한 뒤 각자 다른 row를 쓰면 write skew가 나기 쉽다.

guard row, serializable retry, reconciliation은 비슷해 보여도 막는 위치가 다르다.

| 선택지 | 작동 시점 | 주로 해결하는 것 | 반드시 같이 챙길 것 |
|---|---|---|---|
| guard row | 커밋 전, 같은 트랜잭션 안 | capacity 초과, 최소/최대 인원 위반을 즉시 차단 | 모든 쓰기가 canonical row를 거치게 만들기 |
| serializable retry | 커밋 시 충돌 검출 | query/predicate 기반 의사결정 경합 | bounded retry, 멱등성, 짧은 트랜잭션 |
| reconciliation | 커밋 후, 비동기 검증/복구 | bypass write, cleanup lag, 수동 수정, 분산 경계 drift | source of truth, repair contract, 알람 |

핵심은 셋 중 하나를 "정답"으로 고르는 게 아니라, **이 규칙을 어디서 끊을지**를 정하는 일이다.

## 먼저 판단할 질문

### 1. 이 규칙을 aggregate key 하나의 대표 row로 내릴 수 있는가

예:

- `campaign_id = 42`의 활성 예약 합계는 `capacity` 이하
- `shift_id = 7`의 `on_call_count`는 1 이상

이렇게 aggregate key가 분명하면 guard row가 1순위다.

- 실패를 즉시 돌려줄 수 있다
- 규칙이 SQL 조건으로 드러난다
- 운영자가 어느 row가 canonical source인지 알기 쉽다

반대로 모든 쓰기가 guard row를 거치지 않으면, guard row는 금방 summary 캐시처럼 drift 난다.  
즉 guard row를 쓰려면 "상세 row insert/update"가 아니라 **guard row 조건부 update가 승인 gate**가 되게 만들어야 한다.

### 2. 규칙이 여러 table/predicate에 걸려 guard row로 옮기기 어려운가

예:

- `status IN ('HELD', 'CONFIRMED') AND expires_at > now()` 같은 active predicate
- 휴가, 대체 인력, 예외 스케줄까지 포함한 minimum staffing 계산

이때는 serializable retry가 더 현실적일 수 있다.

- 기존 query 기반 판정을 유지할 수 있다
- 동시 실행이 위험하면 DB가 한쪽을 `40001`류 실패로 밀어낸다
- 애플리케이션은 bounded retry만 잘 설계하면 된다

대신 비용이 명확하다.

- abort/retry율이 올라간다
- 경합이 높을수록 tail latency가 튄다
- 외부 호출이 트랜잭션 안에 있으면 retry가 위험해진다

즉 serializable은 "모델링을 안 해도 된다"가 아니라, **모델을 못 바꾸는 동안 query race를 안전하게 실패시키는 장치**에 가깝다.

### 3. 위반을 절대 즉시 막아야 하는가, 아니면 잠깐의 drift를 복구해도 되는가

reconciliation은 admission control이 아니다.

- 초과 예약을 지금 막아야 하는가 -> reconciliation만으로는 부족하다
- 당직자가 0명이 되는 순간이 있어도 안 되는가 -> reconciliation만으로는 부족하다
- 수동 수정, batch import, 외부 시스템 지연으로 drift가 날 수 있는가 -> reconciliation이 꼭 필요하다

즉 reconciliation은 "나중에 맞춘다"가 아니라, **방어선을 우회한 변경을 찾아내고 다시 맞춘다**는 의미다.

## 실전 선택 가이드

| 상황 | 기본 선택 | 이유 | 보조 장치 |
|---|---|---|---|
| 한 aggregate key의 count/sum만 지키면 됨 | guard row | 가장 직접적이고 explainable하다 | reconciliation |
| query predicate가 복잡하고 재모델링이 당장 어렵다 | serializable retry | read-then-write race를 DB가 밀어낸다 | reconciliation, 멱등성 |
| 외부 시스템/다른 서비스까지 합쳐야 함 | 로컬 guard row + 글로벌 reconciliation | 단일 DB transaction으로 닫히지 않는다 | compensation |
| 일시적 drift 허용, 최종 정산이 더 중요 | reconciliation 중심 | 실시간 실패보다 후속 repair가 중요하다 | cutoff, 알람, bounded rebuild |
| hot aggregate라 guard row 경합이 너무 큼 | shard된 guard row 또는 ledger 재설계 검토 | 대표 row 하나가 병목이 된다 | retry budget, repair scan |

실무 기본값은 보통 아래 둘 중 하나다.

1. 단일 aggregate면 `guard row + reconciliation`
2. query-based set invariant를 당장 바꾸기 어렵다면 `serializable retry + reconciliation`

`reconciliation only`는 hard invariant에는 거의 맞지 않는다.

## 패턴별로 보면

### Guard row가 맞는 경우

guard row는 set invariant를 row 하나의 조건부 update로 내리는 방식이다.

대표 예시:

- `campaign_guard(campaign_id, reserved_qty, capacity)`
- `shift_guard(shift_id, on_call_count)`

장점:

- 승인/거절이 결정적이다
- 위반 이유를 사용자 에러로 바로 번역하기 쉽다
- 모니터링 포인트가 분명하다

주의점:

- 상세 row와 guard row를 같은 트랜잭션에서 갱신해야 한다
- 수동 SQL, 배치, legacy code가 guard row를 우회하지 못하게 해야 한다
- hold expiry나 soft delete가 active predicate를 바꾸면 reconciliation이 필요하다

### Serializable retry가 맞는 경우

serializable은 "같은 predicate를 믿고 동시에 결정한 두 트랜잭션" 중 하나를 밀어낸다.

잘 맞는 상황:

- 여러 row를 읽어 최소 인원/총합을 계산해야 한다
- predicate가 자주 바뀌어 guard row schema가 불안정하다
- 기존 로직을 빠르게 안정화해야 한다

주의점:

- `40001`, serialization failure, deadlock victim을 bounded retry로 다뤄야 한다
- retry마다 같은 side effect가 중복되지 않게 해야 한다
- 경합이 높으면 결국 guard row나 ledger 같은 모델 재설계가 필요하다

### Reconciliation이 맞는 경우

reconciliation은 "실시간 차단"보다 "사후 발견과 복구"가 목적이다.

잘 맞는 상황:

- guard row와 detail row가 수동 수정으로 어긋날 수 있다
- expiry cleanup lag 때문에 active claim 집계가 흔들릴 수 있다
- 외부 시스템 승인/취소와 DB 상태가 비동기로 맞춰진다

주의점:

- 원본 truth가 무엇인지 정해야 한다
- 허용 가능한 drift window를 정해야 한다
- repair가 재실행 가능해야 한다

## 시나리오 1. 최소 당직 인원 규칙

규칙:

- `shift_id`별 `on_call = true` 의사는 최소 1명

권장 선택:

- 기본: `shift_guard.on_call_count > 1` 조건부 감소
- 예외: 당직 가능 여부가 여러 table에 흩어져 있고 빠른 재모델링이 어렵다면 `SERIALIZABLE`로 먼저 안정화
- 항상: 실제 `COUNT(*)`와 `shift_guard.on_call_count`를 대조하는 reconciliation scan

이 규칙은 "한 번이라도 0명이 되면 안 되는가"가 중요하므로, reconciliation 단독 선택은 맞지 않는다.

## 시나리오 2. capacity / quota 초과 방지

규칙:

- `campaign_id`별 활성 claim 합계는 `capacity` 이하

권장 선택:

- 기본: `campaign_guard.reserved_qty + :qty <= capacity` 조건부 update
- predicate가 `HELD`, `CONFIRMED`, `expires_at`, `released_at` 조합으로 복잡하면 ledger 또는 serializable 검토
- 항상: 만료 cleanup 지연, 수동 조정, 재처리 누락을 잡는 reconciliation job

이 규칙에서 흔한 실수는 guard row가 있으니 reconciliation이 필요 없다고 보는 것이다.  
하지만 hold expiry와 manual fix는 guard row를 가장 자주 틀리게 만든다.

## 코드로 보기

```sql
-- 최소 인원 규칙을 guard row로 내리는 예
UPDATE shift_guard
SET on_call_count = on_call_count - 1,
    version = version + 1
WHERE shift_id = :shift_id
  AND on_call_count > 1
  AND version = :version;
```

```sql
-- query 기반 규칙을 serializable로 감싸는 예
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

SELECT COALESCE(SUM(qty), 0) AS active_qty
FROM coupon_claim
WHERE campaign_id = :campaign_id
  AND status IN ('HELD', 'CONFIRMED')
  AND released_at IS NULL;

INSERT INTO coupon_claim(campaign_id, qty, status)
VALUES (:campaign_id, :qty, 'HELD');

COMMIT;
-- serialization failure면 bounded retry
```

```sql
-- guard row와 상세 row가 어긋났는지 보는 reconciliation scan
SELECT g.campaign_id,
       g.reserved_qty AS guard_qty,
       COALESCE(SUM(c.qty), 0) AS actual_qty
FROM campaign_guard g
LEFT JOIN coupon_claim c
  ON c.campaign_id = g.campaign_id
 AND c.status IN ('HELD', 'CONFIRMED')
 AND c.released_at IS NULL
GROUP BY g.campaign_id, g.reserved_qty
HAVING COALESCE(SUM(c.qty), 0) <> g.reserved_qty
    OR COALESCE(SUM(c.qty), 0) > MAX(g.capacity);
```

## 자주 하는 오해

### "Serializable이면 guard row는 필요 없다"

아니다. serializable은 query race를 실패시키지만, 사용자 경험은 retry/abort 중심이 된다.  
aggregate key가 분명하면 guard row가 더 싸고 설명 가능하다.

### "Guard row가 있으면 reconciliation은 사치다"

아니다. 우회 쓰기, manual SQL, backfill, expiry drift는 guard row를 틀리게 만든다.  
guard row를 도입할수록 오히려 "실집계와의 불일치 탐지"가 더 중요해진다.

### "Reconciliation만 있으면 결국 맞춰지니 괜찮다"

capacity oversell, minimum staffing, quota 초과처럼 즉시 위반이 치명적이면 틀린 생각이다.  
reconciliation은 사후 복구이지 admission gate가 아니다.

## 꼬리질문

> Q: count/sum invariant에는 왜 optimistic version check만으로 부족한가요?
> 의도: row version과 set invariant를 구분하는지 확인
> 핵심: 서로 다른 detail row를 수정하면 version 충돌 없이도 총합은 깨질 수 있어서, guard row나 serializable predicate 보호가 필요하다

> Q: guard row와 ledger는 어떻게 다른가요?
> 의도: 대표 row와 append-only claim 모델의 차이를 아는지 확인
> 핵심: guard row는 대표 상태를 직접 수정하고, ledger는 claim row를 쌓되 승인 판단을 별도 aggregate/locking으로 붙인다

> Q: reconciliation 주기는 어떻게 정하나요?
> 의도: repair 비용과 business blast radius를 연결하는지 확인
> 핵심: 허용 가능한 oversell/minimum staffing violation window보다 짧아야 하고, 보통 실시간 차단이 강할수록 reconciliation은 느슨해도 된다

## 한 줄 정리

set invariant에서 guard row는 1차 admission gate, serializable retry는 query race 안전장치, reconciliation은 drift 복구 루프다. hard invariant라면 보통 셋 중 하나가 아니라 둘 이상을 같이 쓴다.
