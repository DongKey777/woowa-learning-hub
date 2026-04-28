# PostgreSQL `23P01` Handling Note

> 한 줄 요약: PostgreSQL `23P01`은 "이번 시도를 다시 해 보라"보다 "이미 다른 예약/구간이 먼저 자리를 차지했다"에 가까운 신호라서, 초보자는 generic retryable failure가 아니라 **제품의 conflict/이미 점유됨 오류**로 먼저 번역해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring/JPA 예외 래퍼에서 `SQLSTATE 23P01` 꺼내는 브리지](./spring-jpa-sqlstate-23p01-bridge.md)
- [PostgreSQL `23P01` vs `23505` Product Language Card](./postgresql-23p01-vs-23505-product-language-card.md)
- [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [DB 입문 오류 신호 미니카드](./db-error-signal-beginner-result-language-mini-card.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: postgresql 23p01 handling note, sqlstate 23p01 beginner, exclusion constraint error mapping, exclusion violation not retryable, postgres overlap conflict product error, already booked 23p01, exclusion constraint conflict translation, 23p01 conflict response, postgresql booking overlap error handling, overlap already exists not retry, exclusion constraint domain error, postgres 23p01 user message, beginner exclusion constraint retry confusion, 23p01 vs 40001 vs 40p01, postgres reservation overlap conflict

## 먼저 멘탈모델

`23P01`은 보통 "DB가 이상해졌다"보다 아래 문장에 가깝다.

> "지금 넣으려는 구간이 이미 다른 활성 구간과 겹친다."

즉 exclusion constraint가 지켜 주는 business rule이 정상적으로 작동해서,
겹치는 요청을 저장 시점에 거절한 것이다.

초보자 기본 번역:

- DB 언어: `23P01` exclusion constraint violation
- 제품 언어: `이미 점유된 시간입니다`, `겹치는 예약이 있습니다`, `같은 정책 window가 이미 활성입니다`

여기서 중요한 점은 `23P01`이 보통 **winner가 이미 있는 conflict**라는 것이다.
같은 입력을 그대로 다시 보내도 결과가 갑자기 좋아질 가능성은 낮다.

## 30초 구분표

| 신호 | 초급자 해석 | 기본 제품 번역 | 기본 동작 |
|---|---|---|---|
| `23P01` | 겹치는 활성 구간이 이미 있다 | `conflict`, `already booked`, `overlapping window` | 사용자/호출자에게 충돌을 설명 |
| `40001` | 이번 snapshot 판단이 무효가 됐다 | 내부 `retryable` | 새 트랜잭션으로 전체 재시도 |
| `40P01` | 이번 시도끼리 잠금 순서가 꼬였다 | 내부 `retryable` | 새 트랜잭션으로 전체 재시도 |
| `55P03` / lock timeout 계열 | 아직 결론을 못 봤다 | `busy` | 짧은 제한 retry 또는 혼잡 응답 |

한 줄 기억법:

- `23P01` -> 이미 겹친다
- `40001`, `40P01` -> 이번 시도만 다시
- timeout 계열 -> 지금은 막힘

## 왜 generic retryable로 보면 안 되나

`23P01`을 `40001`처럼 다루면 제품 의미가 흐려진다.

- `40001`은 새 snapshot에서 다시 계산하면 성공할 수도 있다
- `40P01`은 잠금 순서가 바뀌면 성공할 수도 있다
- `23P01`은 같은 business input이 여전히 겹치면 다시 실패한다

즉 `23P01`은 "경쟁 때문에 이번 시도가 우연히 깨졌다"가 아니라,
**도메인 규칙상 지금 요청을 받아 줄 수 없다는 신호**에 더 가깝다.

예약 예시:

- 기존 예약: 회의실 A, `10:00~11:00`
- 새 요청: 회의실 A, `10:30~11:30`
- 결과: exclusion constraint가 `23P01`로 거절

이 장면에서 blind retry를 해도 기존 예약이 사라지지 않으면 계속 충돌한다.

## 제품 오류로 번역하는 가장 단순한 방법

### 1. 먼저 사용자 문장으로 바꾼다

raw DB 메시지 대신, 도메인 문장으로 닫는 편이 좋다.

| 도메인 | 제품 문장 예시 |
|---|---|
| 회의실/숙소 예약 | `이미 같은 시간대에 예약이 있습니다.` |
| 장비 대여 | `선택한 시간대에 이미 다른 대여가 잡혀 있습니다.` |
| 가격 정책 window | `같은 상품에 겹치는 활성 정책이 이미 있습니다.` |

### 2. 내부 분류에서는 `retryable`이 아니라 `conflict` 쪽에 둔다

서비스 결과 enum이 있다면 보통 아래처럼 두는 편이 덜 흔들린다.

- `ALREADY_EXISTS`
- `CONFLICT`
- `BUSY`
- `RETRYABLE`

이때 `23P01`은 보통 `CONFLICT`다.
exact-key 중복인 `23505`가 `ALREADY_EXISTS`라면, `23P01`은 "겹침 conflict"로 옆 칸에 두면 구분이 쉽다.

### 3. API 응답도 같은 뜻으로 맞춘다

예:

- `409 Conflict`
- 에러 코드: `BOOKING_OVERLAP`
- 메시지: `이미 같은 시간대에 예약이 있습니다.`

핵심은 SQLSTATE를 밖으로 노출하는 게 아니라,
**사용자가 바꿀 수 있는 행동**을 알려 주는 것이다.

## 작은 비교: `23505`와 `23P01`

이 둘을 제품 문장 기준으로 한 장에서 더 짧게 붙여 보고 싶다면 [PostgreSQL `23P01` vs `23505` Product Language Card](./postgresql-23p01-vs-23505-product-language-card.md)로 바로 이어서 보면 된다.

둘 다 class `23` 제약 위반이라 헷갈리기 쉽다.

| SQLSTATE | 보통 뜻 | 초급자 제품 언어 |
|---|---|---|
| `23505` | exact key 중복 | `이미 같은 키/항목이 있습니다` |
| `23P01` | overlap 같은 exclusion 충돌 | `겹치는 구간/정책이 이미 있습니다` |

둘 다 흔히 generic retryable보다 **정상적인 business reject**에 가깝다.

## 자주 하는 실수

- "`23P01`도 동시성 중 하나니까 일단 retry"
  - 아니다. overlap 입력이 그대로면 같은 충돌이 반복되기 쉽다.
- "`23P01`이면 DB 장애"
  - 아니다. exclusion constraint가 규칙을 잘 지킨 결과일 수 있다.
- "`23P01`과 `40001`은 둘 다 PostgreSQL 재시도 대상"
  - 아니다. `40001`은 retryable, `23P01`은 보통 conflict다.
- "사용자에게 `exclusion constraint violated`를 그대로 보여 준다"
  - 제품 문장으로 번역하는 편이 훨씬 낫다.

## 최소 구현 예시

```java
String sqlState = SqlStateExtractor.find(ex);

if ("23P01".equals(sqlState)) {
    throw new ProductConflictException(
        "BOOKING_OVERLAP",
        "이미 같은 시간대에 예약이 있습니다."
    );
}

if ("40001".equals(sqlState) || "40P01".equals(sqlState)) {
    throw new RetryableTransactionException(ex);
}
```

포인트는 단순하다.

- `23P01`은 사용자/호출자에게 설명 가능한 conflict로 닫는다
- `40001`, `40P01`만 whole-transaction retry 경로로 보낸다

## 다음에 이어서 볼 문서

- exclusion constraint 자체가 언제 맞는 모델인지 먼저 고르고 싶으면 [Exclusion Constraint vs Slot Row 빠른 선택 가이드](./exclusion-constraint-vs-slot-row-quick-chooser.md)
- active predicate, 반개구간, 운영 함정까지 같이 보고 싶으면 [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- `40001` retry envelope와 혼동이 남아 있으면 [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)

## 한 줄 정리

PostgreSQL `23P01`은 "이번 시도를 다시 해 보라"보다 "이미 다른 예약/구간이 먼저 자리를 차지했다"에 가까운 신호라서, 초보자는 generic retryable failure가 아니라 **제품의 conflict/이미 점유됨 오류**로 먼저 번역해야 한다.
