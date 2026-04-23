# Lost Update vs Write Skew vs Phantom Timeline Guide

> 한 줄 요약: lost update는 같은 row를 덮어쓰는 문제이고, write skew는 서로 다른 row를 바꿔 집합 규칙을 깨는 문제이며, phantom은 없다고 믿은 범위에 새 row가 끼어드는 문제다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Lost Update Detection Patterns](./lost-update-detection-patterns.md)
- [Read Committed와 Repeatable Read의 이상 현상 비교](./read-committed-vs-repeatable-read-anomalies.md)
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)

retrieval-anchor-keywords: lost update vs write skew vs phantom, anomaly timeline guide, concurrency anomaly decision map, same row overwrite, different row invariant break, new row predicate race, beginner transaction anomaly, lost update write skew phantom difference, read modify write race, minimum staffing write skew, overlap check phantom, absence check insert race, version check, guard row, predicate lock

## 핵심 개념

세 anomaly는 모두 "읽고 나서 판단하고 쓴다"는 흐름에서 시작되지만, 망가지는 지점이 다르다.

| 이상 현상 | 트랜잭션이 믿는 것 | 실제 쓰기 모양 | 깨지는 것 | 첫 기억법 |
|---|---|---|---|---|
| lost update | "내가 읽은 row 값이 아직 유효하다" | 같은 row를 둘 다 최종 저장 | 앞선 변경이 덮여 사라짐 | 같은 row |
| write skew | "다른 row 상태를 보면 내 row만 바꿔도 된다" | 서로 다른 existing row를 각자 수정 | count/sum/minimum 같은 집합 규칙 | 다른 row |
| phantom | "이 범위에는 아직 row가 없다" | predicate 범위에 새 row가 insert | 부재/범위 판단이 깨짐 | 새 row |

초보자에게는 일단 `같은 row / 다른 row / 새 row`로 기억하면 구분이 빨라진다.  
다만 실전에서는 capacity oversell처럼 write skew와 phantom-like insert race가 섞일 수 있으므로, 마지막에는 **어떤 불변식을 보호해야 하는지**로 다시 정리해야 한다.

## 하나의 공유 시나리오

하나의 `야간 진료 예약 시스템`을 생각해 보자. 같은 제품 안에 아래 세 테이블이 있다.

- `shift_capacity(shift_id, remaining_slots, version)`: 이번 교대의 남은 예약 가능 수량
- `doctor_shift(shift_id, doctor_id, on_call)`: 의사별 당직 여부
- `appointment(room_id, start_at, end_at, status)`: 실제 진료실 예약

같은 서비스 안에서도 어떤 테이블과 규칙을 건드리느냐에 따라 anomaly 이름이 달라진다.

## 타임라인 1. Lost Update

상황: 남은 슬롯을 나타내는 `shift_capacity.remaining_slots`는 `10`이다. 두 예약 요청이 동시에 한 칸씩 차감한다.

| 시점 | 트랜잭션 A | 트랜잭션 B | 의미 |
|---|---|---|---|
| t1 | `remaining_slots = 10` 조회 |  | 둘 다 같은 시작값을 볼 수 있다 |
| t2 |  | `remaining_slots = 10` 조회 | 아직 서로의 변경을 모른다 |
| t3 | `10 -> 9`로 저장 |  | A의 예약 1건 반영 |
| t4 |  | `10 -> 9`로 저장 | B가 A의 결과를 덮어쓴다 |
| 결과 |  |  | 최종값은 `9`, 실제로는 `8`이어야 한다 |

판단 포인트:

- 두 트랜잭션은 **같은 row**를 최종 저장했다
- 뒤늦은 저장이 앞선 저장을 **덮어썼다**
- 그래서 앞선 변경이 조용히 사라졌다

처음 떠올릴 대응:

- 원자적 `UPDATE remaining_slots = remaining_slots - 1`
- `version` column CAS
- `SELECT ... FOR UPDATE`

## 타임라인 2. Write Skew

상황: 같은 교대에는 의사 A와 B 두 명이 당직 중이고, 규칙은 "최소 1명은 on-call이어야 한다"다.

| 시점 | 트랜잭션 A | 트랜잭션 B | 의미 |
|---|---|---|---|
| t1 | `on_call = true` 인원 수가 `2`인지 조회 |  | 규칙이 아직 만족된다고 본다 |
| t2 |  | `on_call = true` 인원 수가 `2`인지 조회 | B도 같은 판단을 한다 |
| t3 | 자기 row를 `on_call = false`로 수정 |  | A는 자기 row만 바꾼다 |
| t4 |  | 자기 row를 `on_call = false`로 수정 | B도 자기 row만 바꾼다 |
| 결과 |  |  | 최종 인원 수는 `0`이 된다 |

판단 포인트:

- 두 트랜잭션은 **서로 다른 existing row**를 수정했다
- 누구도 상대 row를 덮어쓰지 않았다
- 그런데 합쳐 보면 "최소 1명"이라는 **집합 규칙**이 깨졌다

처음 떠올릴 대응:

- `shift_guard` 같은 대표 row에 `on_call_count`를 모으기
- 조건부 update로 감소 승인
- `SERIALIZABLE` + bounded retry

## 타임라인 3. Phantom

상황: 같은 진료실 `room_id = 7`에 `22:00 ~ 22:30` 예약이 비어 있는지 확인한 뒤 예약을 넣는다.

| 시점 | 트랜잭션 A | 트랜잭션 B | 의미 |
|---|---|---|---|
| t1 | 겹치는 예약이 없는지 `SELECT` |  | 결과가 비어 있다 |
| t2 |  | 같은 범위를 다시 `SELECT` | B도 비어 있다고 본다 |
| t3 | 새 예약 row를 `INSERT` |  | A의 예약이 생긴다 |
| t4 |  | 겹치는 새 예약 row를 `INSERT` | B가 predicate 사이로 끼어든다 |
| 결과 |  |  | 이제 같은 범위에 두 row가 함께 존재한다 |

판단 포인트:

- 문제의 핵심은 기존 row 덮어쓰기보다 **부재(absence) 판단**이다
- 처음 조회할 때는 없었지만, 나중에 **새 row**가 범위 안으로 들어왔다
- "비어 있음"을 믿고 진행한 결정이 깨졌다

처음 떠올릴 대응:

- `UNIQUE`로 환원 가능하면 discrete slot table + unique key
- 연속 구간이면 exclusion-style constraint
- predicate-safe locking, next-key/gap lock, slotization

## 왜 자주 헷갈리나

### 1. lost update와 write skew는 둘 다 stale read처럼 보인다

둘 다 "옛값을 보고 결정했다"는 느낌이 있다.  
하지만 lost update는 **같은 row의 최종 저장이 충돌**하고, write skew는 **서로 다른 row는 멀쩡히 저장되는데 전체 규칙이 깨진다**.

### 2. write skew와 phantom은 둘 다 조회 후 판단 문제다

둘 다 read-then-decide 안티패턴에서 나온다.  
차이는 write skew가 주로 **existing row들의 조합 규칙**을 깨고, phantom은 **없다고 본 predicate 범위에 새 row가 생긴다**는 점이다.

### 3. 실전 버그는 이름이 섞여 보일 수 있다

예를 들어 claim row를 append해서 capacity를 넘기는 문제는:

- 새 row가 들어온다는 점에서는 phantom-like insert race이고
- 합계 규칙이 깨진다는 점에서는 write skew 성격도 있다

그래서 이름만 맞히기보다 "무엇을 저장 시점에 강제해야 하는가"를 먼저 잡는 편이 낫다.

## 결정 맵

```text
1. 같은 physical row를 둘 다 최종 write했는가?
   - yes -> lost update를 먼저 의심한다

2. 아니면 서로 다른 existing row를 write했는데
   count / sum / minimum / maximum 규칙이 깨졌는가?
   - yes -> write skew를 먼저 의심한다

3. 아니면 earlier query에는 없던 row가 later insert되어
   "없음" 또는 "이 범위는 안전함" 판단을 깨뜨렸는가?
   - yes -> phantom을 먼저 의심한다

4. 분류가 섞여 보이면 이름 싸움보다 불변식 모양을 다시 본다
   - same row overwrite -> atomic update / version check
   - set invariant -> guard row / conditional update / serializable
   - range absence invariant -> unique / exclusion / slotization / predicate-safe lock
```

한 줄 기억법:

- **같은 row**가 사라지면 lost update
- **다른 row**를 각각 바꿨는데 규칙이 깨지면 write skew
- **새 row**가 끼어들어 비어 있음 판단이 깨지면 phantom

## 대응 선택 빠른 표

| 이상 현상 | 보통 먼저 검토할 장치 | 이유 |
|---|---|---|
| lost update | version CAS, atomic update, pessimistic row lock | 같은 row overwrite를 저장 시점에 바로 막기 쉽다 |
| write skew | guard row, counter row, serializable retry | 집합 규칙을 대표하는 충돌 지점을 만들어야 한다 |
| phantom | unique/exclusion constraint, slotization, predicate-safe locking | 부재/범위 판단을 조회가 아니라 저장 시점으로 내려야 한다 |

## 꼬리질문

> Q: phantom과 non-repeatable read는 뭐가 다른가요?
> 의도: row 값 변화와 row 집합 변화를 구분하는지 확인
> 핵심: non-repeatable read는 같은 row 값이 바뀌는 것이고, phantom은 같은 조건의 결과 집합에 row가 생기거나 사라지는 것이다

> Q: write skew도 결국 lost update 아닌가요?
> 의도: 같은-row overwrite와 집합 규칙 위반을 구분하는지 확인
> 핵심: 아니다. write skew는 서로 다른 row가 각각 정상 저장되어도 전체 규칙이 깨질 수 있다

> Q: 이름이 애매하면 무엇부터 결정해야 하나요?
> 의도: anomaly 라벨보다 guardrail 선택을 우선하는지 확인
> 핵심: 보호해야 하는 것이 same row overwrite인지, set invariant인지, range absence인지부터 정한다

## 한 줄 정리

헷갈릴 때는 `같은 row / 다른 row / 새 row`로 먼저 나누고, 마지막에는 overwrite인지 set invariant인지 range absence인지에 맞춰 guardrail을 고르면 된다.
