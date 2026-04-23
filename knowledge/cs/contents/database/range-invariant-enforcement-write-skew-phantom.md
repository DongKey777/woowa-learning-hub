# Range Invariant Enforcement for Write Skew and Phantom Anomalies

> 한 줄 요약: write skew와 phantom은 row 하나가 아니라 범위·집합 규칙이 흔들릴 때 생기므로, 조회 후 판단보다 constraint, slotization, guard row 같은 저장 시점 enforcement로 옮겨야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)
- [Guard Row vs Serializable Retry vs Reconciliation for Set Invariants](./guard-row-vs-serializable-vs-reconciliation-set-invariants.md)
- [Write Skew Detection과 Compensation Patterns](./write-skew-detection-compensation-patterns.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)

retrieval-anchor-keywords: range invariant, set invariant, predicate lock, serializable snapshot isolation, write skew prevention, phantom-safe constraint, overlap invariant, capacity guard row, slotization, reservation ledger, temporal overlap protection, engine fallback, PostgreSQL vs MySQL overlap, guard row vs serializable, reconciliation loop

## 핵심 개념

Write skew와 phantom을 같이 보면 공통점이 있다. 둘 다 "한 row가 충돌했는가"보다 **범위나 집합 규칙이 유지되는가**가 핵심이다.

- `unique(email)`처럼 한 row 또는 정확한 key를 보호하는 문제는 point invariant에 가깝다.
- "같은 회의실에 겹치는 시간대 예약 금지"는 overlap/range invariant다.
- "당직자는 최소 1명 남아야 한다", "전체 예약 합계는 capacity를 넘지 않아야 한다"는 set/capacity invariant다.

문제가 되는 이유는 애플리케이션이 자주 다음 패턴으로 구현하기 때문이다.

1. 조회한다.
2. 조건이 만족된다고 판단한다.
3. insert/update 한다.

이 구조는 동시에 두 트랜잭션이 같은 "없음" 또는 "여유 있음"을 관찰하면 쉽게 새어 버린다.

## 깊이 들어가기

### 1. row lock으로는 범위 규칙을 다 못 막는다

row lock은 이미 존재하는 row 충돌에는 강하다. 하지만 아래 문제는 다르다.

- 아직 존재하지 않는 row의 삽입이 금지되어야 하는 경우
- 여러 row의 합계나 개수가 규칙을 만족해야 하는 경우
- 서로 다른 row를 수정해도 전체 규칙이 깨지는 경우

즉 "누가 같은 row를 건드렸는가"가 아니라 "트랜잭션이 어떤 predicate를 믿고 있었는가"가 중요하다.

### 2. invariant 모양에 따라 enforcement 방식도 달라진다

| invariant 유형 | 예시 | 우선 검토할 enforcement |
|---|---|---|
| point uniqueness | 이메일 중복 금지, `(seat_id, slot_id)` 중복 금지 | `UNIQUE`, PK, upsert arbitration |
| overlap / range | 시간 구간 예약 겹침 금지 | exclusion-style constraint, slotization, predicate-safe locking |
| set / count / sum | 당직 최소 1명, 총 예약 수량 <= capacity | guard row, ledger/counter row, serializable, atomic conditional update |
| distributed boundary | 여러 서비스 합산 quota, 외부 시스템 포함 예약 | reservation ledger, post-commit validation, compensation |

핵심은 격리수준 이름을 외우는 것이 아니라, **불변식이 어떤 모양인지 먼저 분류하는 것**이다.

### 3. overlap invariant는 "겹침 금지"를 저장 규칙으로 내려야 한다

회의실 예약을 예로 들면:

- 나쁜 모델: `겹치는 예약이 없으면 insert`
- 더 나은 모델: 겹침 금지를 constraint semantics나 discrete slot row로 표현

연속 구간이면 overlap 판단이 필요하므로 exclusion-style constraint가 맞을 수 있다.  
시간 단위가 15분, 30분처럼 bucket으로 잘리면 slot row + unique key가 더 단순할 수 있다.

즉 overlap 문제는 "조회 결과가 비어 있는가"보다 "저장 시점에 겹침을 거부할 수 있는가"로 옮겨야 한다.

### 4. capacity invariant는 guard row나 ledger를 별도로 세워야 한다

합계/개수 제약은 row 여러 개를 보고 판단하면 write skew가 잘 생긴다.

예:

- 예약 총합이 `capacity`를 넘지 않아야 함
- 잔여 좌석 수가 음수가 되면 안 됨
- 당직 의사가 최소 1명은 남아야 함

이런 문제는 다음 패턴이 더 안전하다.

- capacity를 대표하는 guard row를 한 곳에 두고 조건부 update
- reservation ledger에 claim을 먼저 남기고 합계를 원자적으로 판정
- 가능한 경우 serializable이나 predicate-safe locking 사용

중요한 점은 "합계를 계산하는 질의"와 "승인 결정을 기록하는 쓰기"가 분리되면 다시 새기 쉽다는 것이다.

### 5. 격리수준은 도움을 주지만 모델링을 대신하지는 않는다

Serializable이나 next-key/predicate 계열 보호는 도움이 된다. 하지만 다음 한계가 남는다.

- 엔진별 동작 차이가 크다
- 성능 비용이 커질 수 있다
- 애플리케이션이 규칙을 정확히 표현하지 못하면 여전히 새는 구간이 생긴다

즉 격리수준은 최종 안전망일 수는 있어도, 잘못된 모델을 마법처럼 고쳐 주지는 않는다.

### 6. 완전 차단이 어렵다면 검증과 보상을 붙인다

외부 시스템이나 다중 서비스가 걸리면 모든 규칙을 단일 트랜잭션으로 막기 어렵다.

이때는:

- 가능한 한 로컬에서는 constraint/guard row로 먼저 줄이고
- 커밋 후 validation으로 위반 여부를 감지하고
- 보상 작업을 idempotent하게 설계한다

이 흐름이 [Write Skew Detection과 Compensation Patterns](./write-skew-detection-compensation-patterns.md)와 연결된다.

## 실전 시나리오

### 시나리오 1. 당직 의사 최소 1명 규칙

두 의사가 동시에 자기 row만 off로 바꾸면 row 충돌은 없어도 규칙은 깨질 수 있다.  
이 문제는 단순 row lock보다 `on_call_count` guard row나 serializable 판정이 더 직접적이다.

### 시나리오 2. 회의실 시간 구간 예약

겹치는 예약이 없는지 먼저 조회하고 insert하면 phantom이 난다.  
연속 구간이면 exclusion-style constraint, discrete slot이면 slot row + unique key가 더 안전하다.

### 시나리오 3. 재고/좌석 capacity 초과

여러 주문이 동시에 "아직 남아 있다"고 보고 각각 감소시키면 합계가 음수가 될 수 있다.  
capacity row에 조건부 update를 걸거나 reservation ledger를 통해 승인 순서를 만들 필요가 있다.

## 코드로 보기

```sql
-- discrete slot으로 환원 가능한 경우
CREATE UNIQUE INDEX uq_room_slot
ON room_slot_reservation(room_id, slot_id);
```

```sql
-- guard row를 두고 조건부로 승인 수량을 올리는 패턴
UPDATE inventory_guard
SET reserved = reserved + :delta,
    version = version + 1
WHERE sku_id = :sku_id
  AND reserved + :delta <= capacity
  AND version = :version;
```

```text
decision pattern
1. exact key 충돌인가?
   -> unique / primary key
2. overlap 금지인가?
   -> exclusion-style constraint or slotization
3. 합계 / 개수 / 최소치 규칙인가?
   -> guard row / ledger / conditional update
4. 단일 트랜잭션으로 닫히지 않는가?
   -> validation + idempotent compensation
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 조회 후 판단 + insert/update | 구현이 빠르다 | phantom/write skew에 취약하다 | 중요도가 낮거나 임시 실험 |
| unique / check / exclusion-style constraint | 규칙을 저장 시점에 강제한다 | 엔진/모델 제약이 있다 | DB가 규칙을 직접 표현할 수 있을 때 |
| slotization | 설명 가능하고 테스트하기 쉽다 | row 수가 늘어난다 | 시간이 discrete bucket으로 나뉠 때 |
| guard row / ledger | 합계 불변식에 강하다 | 추가 모델링이 필요하다 | capacity/count 규칙이 핵심일 때 |
| serializable / predicate-safe locking | 강한 보호를 준다 | 비용이 크고 운영 튜닝이 필요하다 | 높은 정합성이 우선일 때 |
| post-commit validation + compensation | 분산 경계에 현실적이다 | 늦게 발견될 수 있다 | 완전한 사전 차단이 어려울 때 |

## 꼬리질문

> Q: write skew를 막으려면 무조건 serializable이면 되나요?
> 의도: 격리수준과 모델링 책임을 구분하는지 확인
> 핵심: 강한 보호는 되지만 비용이 크고, guard row/constraint로 더 직접적으로 표현할 수 있으면 그 편이 낫다

> Q: overlap invariant와 capacity invariant는 왜 다른가요?
> 의도: 불변식의 모양에 따라 enforcement가 달라진다는 점을 이해하는지 확인
> 핵심: overlap은 구간 관계, capacity는 합계/개수 규칙이라 같은 도구가 항상 맞지 않는다

> Q: slotization은 언제 exclusion-style constraint보다 낫나요?
> 의도: 문법보다 모델 단순화를 우선할 수 있는지 확인
> 핵심: 시간이나 자원이 discrete bucket으로 자연스럽게 나뉘는 경우다

## 한 줄 정리

Write skew와 phantom을 줄이려면, 범위·집합 불변식을 조회 결과에 맡기지 말고 constraint, slotization, guard row, validation/compensation 같은 저장 시점 enforcement로 내려야 한다.
