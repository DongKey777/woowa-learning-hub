# PostgreSQL `23P01` vs `23505` Product Language Card

> 한 줄 요약: `23505`는 보통 "같은 키가 이미 있다"이고, `23P01`은 보통 "같은 자원/시간대에 겹치는 점유가 이미 있다"라서 제품 문장도 `already exists`와 `conflict`로 나눠 말하는 편이 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Booking Error Language Card](./booking-error-language-card.md)
- [PostgreSQL `23P01` Handling Note](./postgresql-23p01-handling-note.md)
- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [DB 신호 -> 서비스 결과 enum -> HTTP 응답 브리지](./db-signal-service-result-http-bridge.md)
- [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: postgresql 23p01 vs 23505 card, exclusion violation vs unique violation beginner, overlap conflict vs exact duplicate, postgres product error language, 23p01 already booked, 23505 already exists, sqlstate 23p01 23505 mapping, beginner product wording duplicate overlap, exclusion conflict message, unique duplicate message, 예약 겹침 오류 문구, exact key 중복 vs overlap conflict, postgres 23p01 23505 차이, beginner sqlstate language card, product language mapping duplicate overlap

## 먼저 멘탈모델

초보자는 SQLSTATE 번호보다 아래 두 문장을 먼저 분리하면 된다.

- `23505`: **같은 키** 자리는 이미 누가 차지했다
- `23P01`: **겹치는 구간/정책** 자리는 이미 누가 차지했다

짧게 외우면:

> `23505` = exact-key duplicate
> `23P01` = overlap conflict

둘 다 제약 위반 class `23`이라 겉모습은 비슷하지만, 제품에서 설명하는 문장은 다르게 가는 편이 좋다.

## 한 장 비교표

| SQLSTATE | DB가 말하는 것 | 초보자 제품 언어 | 서비스 라벨 기본값 | 사용자에게 보일 문장 예시 |
|---|---|---|---|---|
| `23505` | unique key가 이미 있다 | `already exists` | `ALREADY_EXISTS` 중심 | `이미 같은 신청이 있습니다.`, `이미 같은 키가 사용 중입니다.` |
| `23P01` | exclusion rule상 겹치는 row가 이미 있다 | `conflict` | `CONFLICT` 중심 | `선택한 시간대에 이미 예약이 있습니다.`, `겹치는 활성 정책이 이미 있습니다.` |

핵심 차이:

- `23505`는 보통 **같은 키가 한 자리만 허용**된다는 뜻이다.
- `23P01`은 보통 **다른 키여도 겹치면 안 되는 규칙**이라는 뜻이다.

## 가장 쉬운 예시

### 1. `23505`: exact-key duplicate

예:

```sql
UNIQUE (idempotency_key)
```

- 기존 row: `idempotency_key = pay-123`
- 새 요청: `idempotency_key = pay-123`
- 결과: `23505`

이때 제품 문장은 보통 아래에 가깝다.

- `이미 처리된 요청입니다.`
- `이미 같은 키가 등록되어 있습니다.`

즉 질문은 "같은 키를 또 넣었나?"다.

### 2. `23P01`: overlap conflict

예:

```sql
EXCLUDE USING gist (
  room_id WITH =,
  tstzrange(start_at, end_at, '[)') WITH &&
)
```

- 기존 예약: `room_id=A`, `10:00~11:00`
- 새 요청: `room_id=A`, `10:30~11:30`
- 결과: `23P01`

이때 제품 문장은 보통 아래에 가깝다.

- `선택한 시간대에 이미 예약이 있습니다.`
- `겹치는 점유 구간이 있어 저장할 수 없습니다.`

즉 질문은 "같은 키인가?"보다 **"겹치는가?"**다.

## 왜 제품 문장을 나눠야 하나

`23505`와 `23P01`을 둘 다 "중복입니다"로만 말하면 초보자가 중요한 차이를 놓치기 쉽다.

| 신호 | "중복"이라고만 하면 놓치는 것 | 더 정확한 제품 문장 |
|---|---|---|
| `23505` | exact key 재전송, idem replay, same key 재사용 여부 | `이미 같은 키가 있습니다` |
| `23P01` | 시간대/구간/정책의 겹침 규칙 | `겹치는 예약/정책이 있습니다` |

특히 예약 도메인에서는 `23P01`을 "`예약번호 중복`"처럼 말하면 오해가 커진다.
문제는 예약번호가 아니라 **시간대 충돌**이기 때문이다.

## 제품 언어 빠른 선택

| 지금 본 신호 | 먼저 떠올릴 제품 문장 | 보통 피할 문장 |
|---|---|---|
| `23505` | `이미 같은 항목이 있습니다` | `시간대가 겹칩니다` |
| `23P01` | `이미 겹치는 시간대가 있습니다` | `같은 키가 중복됐습니다` |

한 줄 기억법:

- key가 문제면 `already exists`
- overlap이 문제면 `conflict`

## 자주 헷갈리는 지점

- `23P01`도 class `23`이니 `23505`와 같은 duplicate다
  - 아니다. 둘 다 제약 위반이지만 `23P01`은 overlap 규칙 위반 쪽이다.
- `23P01`은 key가 달라도 날 수 있다
  - 맞다. 시작 시각과 종료 시각이 달라도 구간이 겹치면 날 수 있다.
- `23505`는 항상 바로 `409`다
  - 꼭 아니다. 같은 멱등 요청 재전송이면 fresh read 뒤 replay가 더 자연스러울 수 있다.
- `23P01`도 일단 retry하면 된다
  - 보통 아니다. 같은 구간이 계속 겹치면 같은 충돌이 반복된다.

## 초급자용 최소 분류 규칙

1. `23505`를 보면 먼저 "same key winner가 이미 있나?"를 생각한다.
2. `23P01`을 보면 먼저 "겹치는 active row가 이미 있나?"를 생각한다.
3. `23505`는 `already exists` 축, `23P01`은 `conflict` 축에 두면 제품 문장이 덜 흔들린다.

## 다음에 이어서 볼 문서

- 예약 제품 문장으로 `duplicate key` / `23P01` / `lock timeout` / `deadlock`을 한 장에서 묶어 보려면 [Booking Error Language Card](./booking-error-language-card.md)
- `23505` 뒤 winner row를 어떻게 다시 읽는지 보려면 [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- `23P01`을 왜 retryable보다 conflict로 닫는지 더 보려면 [PostgreSQL `23P01` Handling Note](./postgresql-23p01-handling-note.md)
- overlap 자체를 exact-key와 다른 모델로 이해하려면 [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)

## 한 줄 정리

`23505`는 보통 "같은 키가 이미 있다"이고, `23P01`은 보통 "같은 자원/시간대에 겹치는 점유가 이미 있다"라서 제품 문장도 `already exists`와 `conflict`로 나눠 말하는 편이 안전하다.
