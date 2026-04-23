# Isolation Anomaly Cheat Sheet

> 한 줄 요약: dirty read, non-repeatable read, lost update, write skew, phantom은 "무엇을 다시 읽었는가"보다 "무엇을 믿고 썼는가"와 함께 봐야 isolation과 guardrail을 헷갈리지 않는다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Read Committed와 Repeatable Read의 이상 현상 비교](./read-committed-vs-repeatable-read-anomalies.md)
- [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md)
- [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md)
- [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)

retrieval-anchor-keywords: isolation anomaly cheat sheet, dirty read matrix, non-repeatable read matrix, lost update matrix, write skew matrix, phantom matrix, dirty read non-repeatable read lost update write skew phantom, beginner isolation anomaly table, isolation level guardrail confusion, repeatable read write skew, version column lost update, select for update phantom, unique constraint overlap, guard row write skew

## 핵심 개념

이 표를 볼 때 먼저 구분해야 할 것은 두 가지다.

- isolation level은 **무엇을 관측할 때 흔들리는가**를 줄여 준다
- guardrail은 **무엇을 저장할 때 막아야 하는가**를 강제한다

초보자가 자주 틀리는 이유는 `REPEATABLE READ` 같은 이름 하나로 row 재조회, 같은 row 덮어쓰기, 집합 규칙, 부재 기반 범위 판단을 전부 해결했다고 느끼기 때문이다.

## 먼저 보는 compact matrix

표 읽는 법:

- `가능`: 그 isolation만으로는 구멍이 남는다
- `엔진/패턴 의존`: PostgreSQL vs MySQL, plain `SELECT` vs locking read, read-modify-write vs atomic SQL에 따라 달라진다
- `대체로 차단`: DB가 막거나 abort시키지만, retry/짧은 트랜잭션/모델링은 여전히 필요하다
- 아래 표의 판단은 **isolation만 올렸을 때**를 기준으로 읽고, CAS, `FOR UPDATE`, `UNIQUE`, guard row 같은 별도 guardrail은 마지막 열에서 따로 본다

| 이상 현상 | 깨지는 것 | `READ UNCOMMITTED` | `READ COMMITTED` | `REPEATABLE READ` | `SERIALIZABLE` | 먼저 볼 guardrail |
|---|---|---|---|---|---|---|
| dirty read | commit 전 값을 읽음 | 가능 | 차단 | 차단 | 차단 | 보통 `READ COMMITTED` 이상이면 충분 |
| non-repeatable read | 같은 row를 다시 읽었더니 값이 달라짐 | 가능 | 가능 | 대체로 차단 | 차단 | transaction snapshot, `REPEATABLE READ` |
| lost update | 같은 row 최종 write가 앞선 write를 덮어씀 | 가능 | 가능 | 엔진/패턴 의존 | 대체로 차단 | atomic `UPDATE`, version CAS, row lock |
| write skew | 서로 다른 row는 각각 성공했지만 count/sum/minimum 규칙이 깨짐 | 가능 | 가능 | 가능 | 대체로 차단 | guard row, counter row, conditional update, serializable retry |
| phantom | "없다"고 본 범위에 새 row가 끼어들거나 결과 집합이 달라짐 | 가능 | 가능 | 엔진/패턴 의존 | 대체로 차단 | `UNIQUE`/exclusion, slotization, predicate-safe locking |

이 표는 beginner용 portable mental model이다.  
실제 `READ UNCOMMITTED`, `REPEATABLE READ`, `SERIALIZABLE` 체감은 엔진마다 다르므로, PostgreSQL과 MySQL 차이는 [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md)로 이어서 확인한다.

핵심 해석:

- dirty read와 non-repeatable read는 주로 **읽기 관측** 문제다
- lost update는 **같은 row overwrite** 문제다
- write skew와 phantom은 **집합/범위 불변식** 문제다

즉 뒤로 갈수록 isolation 이름보다 **충돌 지점을 어디에 만들 것인가**가 더 중요해진다.

## 초보자가 가장 많이 헷갈리는 guardrail

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "`REPEATABLE READ`면 동시성 버그는 거의 끝난다" | row 재조회 안정성과 set/range invariant 보호는 다르다 | same-row면 CAS/atomic update, set/range면 guard row나 constraint부터 본다 |
| "`SELECT ... FOR UPDATE`를 했으니 빈 결과도 잠겼다" | empty result 전체를 predicate lock처럼 다뤄 주는 것은 portable한 보장이 아니다 | overlap/absence는 unique, exclusion, slot row, serializable retry를 먼저 검토한다 |
| "`@Version`만 넣으면 phantom이나 write skew도 막힌다" | version column은 같은 row overwrite 감지에는 좋지만, 서로 다른 row 조합 규칙까지 보호하지 않는다 | shared counter row, guard row, ledger 같은 공통 충돌 surface를 만든다 |
| "`UNIQUE` 하나면 capacity나 minimum staffing도 해결된다" | unique는 discrete key 충돌에는 강하지만 count/sum/minimum 규칙 전체를 표현하지 못할 수 있다 | conditional decrement, aggregated guard row, reconciliation을 함께 설계한다 |
| "`SERIALIZABLE`이면 앱은 바꿀 게 없다" | PostgreSQL은 abort/retry, MySQL은 blocking/deadlock surface가 커질 수 있다 | idempotent retry, 짧은 transaction, telemetry를 같이 둔다 |

## 빠른 분류 기억법

| 질문 | 먼저 의심할 anomaly | 보통 먼저 검토할 장치 |
|---|---|---|
| 같은 row를 둘 다 읽고 각자 저장했나? | lost update | atomic SQL, version CAS, `FOR UPDATE` |
| 서로 다른 row를 바꿨는데 총합/최소 인원이 깨졌나? | write skew | guard row, counter row, serializable retry |
| 없다고 본 범위에 새 row가 들어왔나? | phantom | unique/exclusion, slotization, predicate-safe locking |
| 그냥 같은 row를 두 번 읽었더니 값이 달라졌나? | non-repeatable read | `REPEATABLE READ`, snapshot semantics |
| commit 전 값을 읽었나? | dirty read | `READ COMMITTED` 이상 |

## 어디로 이어서 읽으면 좋은가

- dirty read, non-repeatable read, `READ COMMITTED` vs `REPEATABLE READ`는 [Read Committed와 Repeatable Read의 이상 현상 비교](./read-committed-vs-repeatable-read-anomalies.md)
- 엔진별 `REPEATABLE READ`/`SERIALIZABLE` 감각 차이는 [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md)
- lost update, write skew, phantom을 `same row / different row / new row`로 나누려면 [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md)
- same-row overwrite를 실제 SQL 패턴으로 막는 법은 [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md)
- set/range invariant를 저장 시점 enforcement로 내리는 법은 [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)

## 꼬리질문

> Q: lost update는 non-repeatable read랑 같은 말인가요?
> 의도: 읽기 관측 문제와 최종 write overwrite를 분리하는지 확인
> 핵심: 아니다. non-repeatable read는 같은 row를 다시 읽었더니 값이 달라진 것이고, lost update는 최종 저장이 앞선 저장을 지워 버리는 것이다

> Q: phantom은 `REPEATABLE READ`면 항상 사라지나요?
> 의도: 엔진 차이와 predicate 보호의 한계를 아는지 확인
> 핵심: 아니다. repeated plain `SELECT`가 안정적이어도 absence-check나 range invariant는 엔진/locking path에 따라 여전히 구멍이 남을 수 있다

> Q: write skew를 막으려면 왜 row lock만으로 부족한가요?
> 의도: 집합 규칙 위반이 서로 다른 row 조합에서 난다는 점을 이해하는지 확인
> 핵심: 각자 다른 row만 잠그고 써도 count/sum/minimum 규칙은 깨질 수 있으므로, 공유 counter나 guard row 같은 공통 충돌 지점이 필요하다

## 한 줄 정리

dirty read와 non-repeatable read는 읽기 흔들림을 보는 이름이고, lost update, write skew, phantom은 쓰기 충돌 surface를 보는 이름이므로 isolation level과 guardrail을 항상 같이 선택해야 한다.
