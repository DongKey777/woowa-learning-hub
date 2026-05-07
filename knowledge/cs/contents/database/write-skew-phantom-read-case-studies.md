---
schema_version: 3
title: Write Skew and Phantom Read Case Studies
concept_id: database/write-skew-phantom-read-case-studies
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- write-skew
- phantom-read
- range-invariant
- serializable
- guard-row
aliases:
- write skew
- phantom read
- range invariant
- set invariant
- snapshot isolation anomaly
- absence check race
- doctor on call minimum staffing
- capacity oversell
- reservation overlap
- predicate lock
symptoms:
- write skew와 phantom read가 모두 조회 후 판단에서 시작되지만 어떤 점이 다른지 사례로 설명해야 해
- row lock이 있어도 서로 다른 row를 수정해 집합 불변식이 깨지는 이유를 이해해야 해
- empty range나 absence check를 믿고 insert하다 phantom으로 중복 예약, overlap, capacity oversell이 생길 수 있어
intents:
- deep_dive
- comparison
- troubleshooting
prerequisites:
- database/transaction-isolation-locking
- database/read-committed-repeatable-read-anomalies
next_docs:
- database/range-invariant-enforcement-write-skew-phantom
- database/exclusion-constraint-overlap-case-studies
- database/write-skew-detection-compensation-patterns
linked_paths:
- contents/database/transaction-isolation-locking.md
- contents/database/read-committed-vs-repeatable-read-anomalies.md
- contents/database/gap-lock-next-key-lock.md
- contents/database/range-invariant-enforcement-write-skew-phantom.md
- contents/database/exclusion-constraint-overlap-case-studies.md
- contents/database/write-skew-detection-compensation-patterns.md
- contents/database/transaction-retry-serialization-failure-patterns.md
confusable_with:
- database/range-invariant-enforcement-write-skew-phantom
- database/read-committed-repeatable-read-anomalies
- database/write-skew-detection-compensation-patterns
forbidden_neighbors: []
expected_queries:
- write skew와 phantom read는 둘 다 조회 후 판단에서 시작되지만 어떻게 다른 anomaly야?
- doctor on-call minimum staffing 사례에서 서로 다른 row를 수정했는데 전체 불변식이 깨지는 이유를 설명해줘
- absence check race로 예약 overlap이나 capacity oversell이 생기는 phantom 사례를 알려줘
- snapshot isolation은 읽은 값이 안정돼 보여도 set invariant를 안전하게 만들지 못한다는 뜻이 뭐야?
- guard row, exclusion constraint, serializable retry, post-commit compensation 중 어떤 사다리로 대응해?
contextual_chunk_prefix: |
  이 문서는 write skew와 phantom read case studies를 range invariant, set invariant, absence check race, snapshot isolation anomaly 관점으로 설명하는 advanced deep dive다.
  doctor on call, capacity oversell, reservation overlap, predicate lock, guard row 질문이 본 문서에 매핑된다.
---
# Write Skew and Phantom Read Case Studies

> 한 줄 요약: write skew와 phantom은 둘 다 "조회 후 판단"에서 시작되지만, write skew는 서로 다른 row를 갱신해 집합 규칙이 깨지고 phantom은 "없음/범위" 판단 사이로 새 row가 끼어드는 문제라는 점이 다르다.

**난이도: 🔴 Advanced**

관련 문서:

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Read Committed vs Repeatable Read Anomalies](./read-committed-vs-repeatable-read-anomalies.md)
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [Write Skew Detection과 Compensation Patterns](./write-skew-detection-compensation-patterns.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)

retrieval-anchor-keywords: write skew, phantom read, range invariant, set invariant, snapshot isolation anomaly, absence check race, doctor on call minimum staffing, capacity oversell, reservation overlap, exclusion constraint, predicate lock, guard row, serializable retry, overlap invariant

## 핵심 개념

write skew와 phantom은 둘 다 "같은 순간에 본 조회 결과를 믿고 쓰기 결정"을 내릴 때 생긴다.  
차이는 트랜잭션이 무엇을 믿고 있었는가에 있다.

| 구분 | 트랜잭션이 믿는 것 | 흔한 안티패턴 | 실제로 필요한 보호 |
|---|---|---|---|
| phantom | "이 범위에는 아직 row가 없다" | 조회 결과가 비어 있으면 insert | range/predicate를 저장 시점에 막는 구조 |
| write skew | "다른 row 상태가 이러니 내 row만 바꿔도 된다" | count/sum 후 자기 row만 update | 집합 규칙을 대표하는 guard row, constraint, serializable |
| overlap invariant | "겹치는 예약이 없다" | overlap query 후 insert | exclusion constraint, slotization, active predicate 정규화 |

핵심은 둘 다 row 하나의 충돌이 아니라 **부재(absence)와 집합(predicate) 판단이 경쟁 상황에서 깨지는 문제**라는 점이다.

## 깊이 들어가기

### 1. row lock이 있어도 안 막히는 이유

write skew는 서로 다른 row를 수정할 때 잘 드러난다.

- 트랜잭션 A는 의사 A row를 읽고 update한다
- 트랜잭션 B는 의사 B row를 읽고 update한다
- 둘 다 "전체 당직자는 1명 이상"이라는 규칙을 봤지만, write set이 겹치지 않아서 충돌 없이 커밋될 수 있다

즉 row lock은 "같은 row를 누가 만졌는가"에는 강하지만,  
"그 row들을 함께 보면 유지되어야 하는 규칙"까지 자동으로 보호하지는 않는다.

### 2. phantom은 "존재하지 않음"을 믿는 순간 생긴다

phantom은 대개 이런 형태다.

1. `SELECT ... WHERE predicate`
2. 결과가 없다고 믿음
3. 다른 트랜잭션이 같은 predicate 범위에 row를 insert
4. 첫 트랜잭션이 오래된 판단으로 계속 진행

중요한 점은 phantom이 단순히 "두 번째 조회 결과가 바뀌었다"로 끝나지 않는다는 것이다.  
실전에서는 보통 이 변화가 곧바로 **중복 예약, blackout window 충돌, 허용량 초과** 같은 비즈니스 오류로 이어진다.

### 3. snapshot isolation은 "읽은 값이 안 바뀌어 보인다"와 "규칙이 안전하다"를 같게 만들지 않는다

snapshot isolation에서는 각 트랜잭션이 일관된 스냅샷을 보므로 읽기가 안정돼 보인다.  
하지만 다음 상황은 여전히 남는다.

- 각자 같은 "빈 범위"를 보고 insert
- 각자 같은 "충분한 합계"를 보고 다른 row를 update/insert
- 최종적으로는 write-write conflict가 없어서 둘 다 성공

그래서 snapshot isolation이 있다고 해서 "범위 규칙도 안전하다"고 결론 내리면 안 된다.

### 4. 실전에서는 anomaly 이름보다 guardrail 사다리가 중요하다

보통은 아래 순서로 생각하면 된다.

1. 규칙을 constraint나 unique/exclusion semantics로 옮길 수 있는가
2. 안 되면 guard row나 counter row로 쓰기 충돌 지점을 만들 수 있는가
3. 그래도 읽기 기반 판단이 필요하면 serializable + bounded retry를 붙일 수 있는가
4. 분산 경계가 있으면 post-commit validation과 compensation을 어디에 둘 것인가

즉 anomaly를 분류하는 이유는 정답을 맞히기 위해서가 아니라,  
**어떤 지점에 쓰기 충돌을 강제로 만들지 판단하기 위해서**다.

## 실전 시나리오

### 시나리오 1. 당직 의사 최소 1명 규칙

규칙:

- 같은 `shift_id`에서 `on_call = true` 의사는 최소 1명 남아야 한다

깨지는 흐름:

1. 의사 A와 B가 동시에 `SELECT COUNT(*) FROM doctor_shift WHERE shift_id = 7 AND on_call = true`
2. 둘 다 `2`를 본다
3. A는 자기 row를 `on_call = false`로 바꾼다
4. B도 자기 row를 `on_call = false`로 바꾼다
5. 두 트랜잭션은 서로 다른 row만 건드렸으므로 충돌 없이 끝날 수 있다
6. 결과적으로 당직자는 `0`명이 된다

이건 phantom보다는 전형적인 write skew다.  
`COUNT(*)`가 읽기 판단에 쓰였지만, 실제 쓰기는 각자 자기 row에만 일어났기 때문이다.

현실적 guardrail:

- `shift_guard(shift_id, on_call_count)` 같은 대표 row를 두고 `on_call_count > 1`일 때만 감소시킨다
- `doctor_shift`만 잠그지 말고, guard row를 조건부 update하는 경로를 유일한 쓰기 경로로 만든다
- 정말 강한 정합성이 필요하면 `SERIALIZABLE` + `40001` bounded retry를 같이 둔다
- 운영에서는 `on_call_count = 0` 또는 `doctor_shift` 실집계와 guard row 불일치 알람을 따로 둔다

### 시나리오 2. 선착순 쿠폰 / 좌석 capacity 초과

규칙:

- 같은 `campaign_id`의 활성 claim 합계는 `capacity`를 넘으면 안 된다

깨지는 흐름:

1. 요청 A와 B가 동시에 `SELECT COALESCE(SUM(qty), 0) FROM coupon_claim WHERE campaign_id = 99 AND status IN ('HELD', 'CONFIRMED')`
2. 둘 다 현재 합계를 `96`으로 본다
3. 각자 `qty = 5` claim row를 insert한다
4. 두 row는 서로 다른 PK를 가지므로 write conflict가 없다
5. 최종 합계는 `106`이 된다

이건 write skew와 phantom 성격이 둘 다 있다.

- 합계라는 set invariant를 깨뜨린다는 점에서는 write skew
- 새 claim row가 나중에 범위 결과에 나타난다는 점에서는 phantom-like insert race

현실적 guardrail:

- `campaign_guard.reserved_qty`를 두고 `reserved_qty + :delta <= capacity` 조건부 update로 승인한다
- `HELD`, `CONFIRMED`, `EXPIRED` lifecycle을 명확히 정하고, 만료 cleanup 지연이 있어도 guard row 기준과 일치하게 만든다
- retry 경로에는 반드시 idempotency key를 붙여서 같은 요청이 중복 claim을 만들지 않게 한다
- 정기적으로 `SUM(active_claims)`와 `campaign_guard`를 대조하는 reconciliation job을 둔다

### 시나리오 3. 회의실 예약 겹침과 blackout window 충돌

규칙:

- 같은 `room_id`에 대해 `HELD`, `CONFIRMED`, `BLACKOUT` 구간은 겹치면 안 된다

깨지는 흐름:

1. 사용자 예약 요청이 `겹치는 활성 booking 없음`을 조회한다
2. 동시에 운영자가 같은 시간대에 `BLACKOUT` 구간을 추가한다
3. 둘 다 "현재는 비어 있다"고 판단하고 insert한다
4. 나중에 읽으면 예약과 blackout이 함께 존재한다

이건 대표적인 phantom/overlap 문제다.  
조회 시점에는 비어 있었지만, 쓰기 직전과 커밋 사이에 같은 predicate 범위로 row가 들어왔다.

현실적 guardrail:

- `[start_at, end_at)` 반개구간 규칙을 먼저 고정한다
- `HELD`, `CONFIRMED`, `BLACKOUT`처럼 실제로 자원을 막는 상태를 active predicate로 통일한다
- 사용자 API와 운영 도구가 모두 같은 exclusion-style arbitration을 통과하게 한다
- 충돌은 DB 예외로 끝내지 말고 409 계열 도메인 에러로 번역한다

### 시나리오 4. 정책 window 겹침과 멀티 차원 범위

규칙:

- 같은 `tenant_id`, `product_id`, `country_code` 조합에서 `ACTIVE` 가격 정책 window는 겹치면 안 된다

깨지는 흐름:

1. 배치 A가 신규 프로모션 window를 넣기 전에 기존 active window를 조회한다
2. 운영자 B도 다른 화면에서 같은 조합의 정책을 추가한다
3. 둘 다 동일 조건 범위를 비어 있다고 보고 insert한다
4. API는 어떤 가격 규칙이 우선인지 애매해지고, 캐시와 재계산 결과도 서로 달라진다

이 문제는 phantom이면서 동시에 "equality dimension 누락" 버그가 자주 섞인다.  
`tenant_id`나 `country_code` 중 하나라도 check에서 빠지면 제약이 있어도 다른 차원에서 겹침이 새기 쉽다.

현실적 guardrail:

- equality dimension을 쿼리와 constraint 양쪽에서 동일하게 유지한다
- 활성 상태와 유효 기간을 정책 엔진, 관리자 화면, DB에서 같은 기준으로 해석한다
- 배치 경로가 대량 insert를 할 때도 동일한 충돌 해석과 retry 정책을 사용한다

## 현실적 guardrail 체크리스트

- 규칙이 key 중복인지, overlap인지, count/sum인지 먼저 분류한다
- 부재 기반 판단이 있다면 그 판단을 누가 저장 시점에 강제할지 정한다
- active predicate와 range boundary(`[start, end)`)를 문서와 코드에 같이 고정한다
- `40001`, `23P01`, deadlock victim을 "예상 가능한 경쟁 결과"로 보고 retry/도메인 에러 정책을 분리한다
- constraint 추가 전에는 기존 중복/겹침 데이터 정리와 backfill 검증을 먼저 한다
- 실시간 방어만 믿지 말고 reconciliation metric과 수동 복구 경로를 남긴다

## 코드로 보기

```sql
-- 안티패턴: 읽은 합계를 믿고 append row를 추가
SELECT COALESCE(SUM(qty), 0)
FROM coupon_claim
WHERE campaign_id = :campaign_id
  AND status IN ('HELD', 'CONFIRMED');

INSERT INTO coupon_claim(campaign_id, user_id, qty, status)
VALUES (:campaign_id, :user_id, :qty, 'HELD');
```

```sql
-- 더 안전한 패턴: 대표 row에 경쟁을 모은다
UPDATE campaign_guard
SET reserved_qty = reserved_qty + :qty,
    version = version + 1
WHERE campaign_id = :campaign_id
  AND reserved_qty + :qty <= capacity
  AND version = :version;
```

```text
decision pattern
1. exact key 중복인가?
   -> unique / primary key
2. 겹치는 구간 부재를 믿는가?
   -> exclusion constraint / slotization / predicate-safe lock
3. count / sum 규칙인가?
   -> guard row / counter row / conditional update
4. 단일 DB 커밋으로 닫히지 않는가?
   -> validation + idempotent compensation
```

## 트레이드오프

| 대응 | 장점 | 단점 | 사용 시점 |
|---|---|---|---|
| 조회 후 판단 + insert/update | 구현이 빠르다 | phantom/write skew에 가장 취약하다 | 중요도가 낮은 내부 도구, 임시 실험 |
| guard row / counter row | 합계 규칙에 직접적이다 | 대표 row 경합이 생긴다 | capacity, 최소/최대 인원 규칙 |
| exclusion constraint / slotization | overlap 규칙을 저장 시점에 막는다 | 엔진 제약, 모델링 비용이 있다 | 예약, blackout, window 충돌 |
| serializable + retry | 강한 안전망이다 | retry 설계와 성능 비용이 필요하다 | 높은 정합성 경로, 재모델링이 어려울 때 |
| post-commit validation + compensation | 분산 경계에서 현실적이다 | 늦게 발견될 수 있다 | 외부 시스템 포함 workflow |

## 꼬리질문

> Q: write skew와 phantom은 왜 둘 다 "조회 후 판단" 문제라고 하나요?
> 의도: anomaly 이름보다 공통 원인을 잡는지 확인
> 핵심: 둘 다 부재/범위/합계 판단을 읽기 결과에 맡길 때 경쟁 상황에서 무너진다

> Q: snapshot isolation이면 조회가 안정적인데 왜 여전히 위험한가요?
> 의도: 스냅샷 안정성과 불변식 안전성을 구분하는지 확인
> 핵심: 읽기 스냅샷이 안정적이어도 write set이 안 겹치면 집합 규칙은 깨질 수 있다

> Q: overlap 문제를 write skew와 별도로 봐야 하나요?
> 의도: overlap을 phantom 형태의 범위 불변식으로 이해하는지 확인
> 핵심: overlap은 대개 phantom-shaped invariant이지만, guardrail은 exclusion/slotization처럼 더 특화된 도구가 필요하다

## 한 줄 정리

write skew와 phantom을 실전에서 다루려면 anomaly 이름만 구분할 게 아니라, 부재·범위·합계 판단을 constraint, guard row, slotization, serializable retry 같은 저장 시점 guardrail로 옮겨야 한다.
