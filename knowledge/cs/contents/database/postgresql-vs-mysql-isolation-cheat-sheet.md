# PostgreSQL vs MySQL Isolation Cheat Sheet

> 한 줄 요약: `READ COMMITTED`, `REPEATABLE READ`, `SERIALIZABLE`은 이름이 같아도 PostgreSQL과 MySQL(InnoDB)이 안전성을 만드는 방식이 달라서, 한 엔진에서 통하던 동시성 직관을 다른 엔진에 그대로 옮기면 쉽게 틀린다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Read Committed와 Repeatable Read의 이상 현상 비교](./read-committed-vs-repeatable-read-anomalies.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)

retrieval-anchor-keywords: postgresql vs mysql isolation, postgres vs mysql isolation, postgresql read committed, postgresql repeatable read, postgresql serializable, postgresql serializable retry playbook, sqlstate 40001, mysql read committed, mysql repeatable read, mysql serializable, snapshot isolation vs next-key lock, postgresql serializable ssi, mysql serializable locking read, engine-specific isolation cheat sheet, beginner isolation comparison, read committed engine difference, repeatable read engine difference, serializable retry vs blocking

## 핵심 개념

같은 isolation level 이름을 봤을 때 초보자가 먼저 물어야 하는 질문은 세 가지다.

1. plain `SELECT`가 statement마다 새 snapshot을 보나, transaction 전체에서 같은 snapshot을 보나?
2. "없음"이나 범위를 믿고 쓰는 경로를 row lock이 아니라 **predicate 자체**까지 보호해 주나?
3. `SERIALIZABLE`이 주로 **retry를 요구하는 optimistic 계열**인가, 아니면 **더 많은 잠금과 대기**를 만드는 lock-heavy 계열인가?

이 질문에 대한 답이 PostgreSQL과 MySQL에서 다르다.  
그래서 "우리 DB에서 `REPEATABLE READ`면 괜찮았다"는 말은 엔진 이름이 빠지면 불완전한 설명이다.

## 먼저 보는 치트 시트

| 격리수준 | PostgreSQL | MySQL InnoDB | 초보자 기억법 |
|---|---|---|---|
| `READ COMMITTED` | plain `SELECT`마다 새 snapshot을 본다. 같은 transaction 안에서도 재조회 결과가 달라질 수 있다. | consistent read도 statement마다 새 snapshot을 본다. locking read는 보통 record lock만 잡고 gap lock은 FK/duplicate-key 검사 쪽에만 남아 phantom이 다시 열릴 수 있다. | 이름은 비슷하지만, MySQL은 `READ COMMITTED`에서 gap locking 기대가 특히 빨리 깨진다. |
| `REPEATABLE READ` | transaction 시작 시점 기준 snapshot을 계속 본다. repeated plain `SELECT`에서는 non-repeatable read와 phantom을 보지 않지만, write skew나 predicate invariant 위반까지 자동으로 막아 주지는 않는다. | plain `SELECT`는 transaction snapshot을 유지한다. 하지만 locking read/range scan은 next-key/gap lock으로 scanned range insert를 막을 수 있어, 일부 부재 체크가 "엔진 구현 덕분에" 안전해 보일 수 있다. | 둘 다 재조회는 안정적이지만, PostgreSQL RR은 snapshot isolation 쪽이고 MySQL RR은 next-key locking 체감이 더 강하다. |
| `SERIALIZABLE` | SSI(Serializable Snapshot Isolation)로 동작한다. 읽기가 무조건 락으로 바뀌기보다, 위험한 rw-dependency cycle을 감지해 한쪽을 abort시키므로 retry 계약이 중요하다. | `REPEATABLE READ`보다 lock-heavy하다. autocommit이 꺼진 plain `SELECT`는 사실상 `FOR SHARE`처럼 취급되어 더 많은 대기와 deadlock 가능성을 만든다. | 같은 `SERIALIZABLE`이어도 PostgreSQL은 "retry 중심", MySQL은 "locking 중심"으로 느껴진다. |

## 격리수준별로 왜 다르게 느껴지나

### 1. `READ COMMITTED`: 둘 다 statement snapshot이지만, MySQL은 range absence-check가 더 쉽게 깨진다

공통점:

- 같은 transaction 안에서도 plain `SELECT`를 다시 하면 최신 committed 값이 보일 수 있다
- non-repeatable read와 phantom을 막는 수준은 아니다

차이점:

- PostgreSQL에서는 "이 statement가 본 snapshot"이 매번 새로 잡힌다고 이해하면 된다
- MySQL InnoDB에서도 consistent read는 매 statement fresh snapshot이지만, `FOR UPDATE`/`FOR SHARE` 같은 locking read에서 **gap lock이 대부분 빠진다**

그래서 MySQL에서 특히 자주 터지는 오해는 이거다.

> `SELECT ... FOR UPDATE`를 했으니 "없음"도 잠겼겠지?

`READ COMMITTED`의 InnoDB에서는 이 가정이 틀릴 수 있다.  
기존 row는 잠가도, 아직 없는 row가 들어올 gap은 막지 못해 overlap check나 "비어 있으면 insert" 경로가 phantom에 취약해진다.

### 2. `REPEATABLE READ`: PostgreSQL은 snapshot 쪽, MySQL은 next-key locking 체감이 더 강하다

### PostgreSQL `REPEATABLE READ`

- transaction 전체가 같은 snapshot을 본다
- repeated plain `SELECT`는 안정적이다
- SQL 표준 표처럼 "phantom이 남을 수 있다"라고 단순 암기하면 PostgreSQL에서는 오답이 된다
- 하지만 이것이 곧 "predicate 불변식까지 안전"을 뜻하지는 않는다

중요한 함정:

- 두 transaction이 같은 집합 규칙을 각자 snapshot에서 읽고
- 서로 다른 row를 수정하거나 새 row를 넣는 방식으로
- write skew / absence-check 위반을 만들 수 있다

즉 PostgreSQL RR은 "관측 그림"은 고정하지만, 그 그림만으로 비즈니스 invariant를 자동 직렬화하지는 않는다.

### MySQL `REPEATABLE READ`

- plain `SELECT`도 같은 snapshot을 본다
- 하지만 locking read와 range scan은 next-key/gap lock을 사용해 scanned index range에 대한 insert를 막을 수 있다
- 그래서 어떤 absence-check가 MySQL RR에서는 꽤 잘 버티는 것처럼 보일 수 있다

중요한 함정:

- 이 안전성은 "추상적인 predicate 전체"가 아니라 **실제로 스캔한 index range**에 묶인다
- 인덱스 prefix, access path, mixed write path가 달라지면 같은 논리 규칙도 깨질 수 있다
- 따라서 "MySQL RR에서 괜찮았으니 PostgreSQL RR로 옮겨도 괜찮다"는 추론은 특히 위험하다

한 줄로 줄이면 이렇다.

- PostgreSQL RR: **snapshot consistency가 핵심**
- MySQL RR: **snapshot + next-key locking 체감이 같이 따라온다**

### 3. `SERIALIZABLE`: 같은 이름이지만 비용 모델이 가장 다르다

### PostgreSQL `SERIALIZABLE`

- 내부적으로 SSI를 사용한다
- 읽기 트랜잭션을 전부 강한 lock으로 바꾸는 방식이 아니다
- 대신 동시에 실행된 transaction들이 serial order로 설명되지 않는 패턴이 생기면 한쪽을 abort한다

초보자가 기억할 점:

- "더 강한 lock"만 생각하지 말고 `retry`를 계약으로 같이 둬야 한다
- 애플리케이션은 serialization failure를 정상 경로로 다뤄야 한다

### MySQL `SERIALIZABLE`

- InnoDB의 `REPEATABLE READ` 위에 더 강한 locking behavior를 얹는 쪽에 가깝다
- autocommit이 꺼진 plain `SELECT`도 shared locking read처럼 동작해 대기가 늘 수 있다

초보자가 기억할 점:

- PostgreSQL처럼 "읽기는 가볍고, 충돌 시 abort"라고 기대하면 안 된다
- 긴 조회를 transaction 안에 넣으면 lock wait과 deadlock surface가 더 빨리 커진다

## 엔진을 바꿀 때 가장 위험한 오해

### 오해 1. "`REPEATABLE READ`면 phantom 걱정은 끝난다"

틀리다.

- PostgreSQL RR은 repeated plain `SELECT`에서 phantom을 보지 않더라도 predicate invariant를 자동 직렬화하지 않는다
- MySQL RR은 next-key locking이 도움을 줄 수 있지만, 그것도 같은 인덱스 경로와 같은 locking protocol을 지킬 때만 그렇다

즉 둘 다 "범위 규칙을 무조건 보장한다"는 뜻은 아니다.

### 오해 2. "MySQL에서 쓰던 `SELECT ... FOR UPDATE` absence-check를 PostgreSQL로 그대로 옮기면 된다"

위험하다.

- MySQL RR에서는 next-key/gap lock 덕분에 일부 insert phantom이 막혔을 수 있다
- PostgreSQL RR에서는 같은 이름의 isolation level이더라도 그 보호가 자동으로 따라오지 않는다

포팅 시에는 아래 대안을 먼저 본다.

- exclusion constraint
- slot row + unique key
- guard row
- PostgreSQL `SERIALIZABLE` + retry

### 오해 3. "`SERIALIZABLE`은 어디서나 그냥 더 느린 `REPEATABLE READ`다"

틀리다.

- PostgreSQL은 retry/abort surface가 핵심이다
- MySQL은 blocking/locking surface가 더 직접적으로 보인다

같은 이름인데도 운영 지표가 달라진다.

- PostgreSQL: serialization failure, retry count
- MySQL: lock wait, deadlock, transaction duration

## 실전 시나리오

### 시나리오 1. 예약 overlap check를 PostgreSQL로 옮길 때

기존 MySQL RR 구현:

1. `SELECT ... FOR UPDATE`로 겹치는 예약이 없는지 확인
2. 결과가 없으면 insert

이 패턴이 MySQL에서 버텼다면, 실제로는 RR의 next-key locking과 인덱스 경로 덕을 봤을 가능성이 있다.  
같은 코드를 PostgreSQL RR로 옮기면 "repeated read는 안정적"이어도 absence-check 자체는 자동으로 잠기지 않는다.

즉 포팅 포인트는 SQL 문법이 아니라 **arbitration surface를 무엇으로 만들지**다.

### 시나리오 2. 보고서/관리자 화면에서 최신성이 더 중요할 때

- PostgreSQL RC, MySQL RC 모두 statement마다 최신 committed view를 보는 감각이 맞다
- 같은 transaction 안에서 값이 바뀌어도 이상이 아니라 격리수준의 성질이다

이런 화면에서 꼭 필요한 건 RR보다도 다음인 경우가 많다.

- 짧은 transaction
- read replica consistency 정책
- "현재 시각 기준"이라는 제품 의미의 명확화

### 시나리오 3. 정합성이 가장 중요한 정산/배치에서 `SERIALIZABLE`을 검토할 때

PostgreSQL이면:

- retry budget과 idempotency를 먼저 설계한다

MySQL이면:

- 긴 read transaction을 줄이고 lock wait surface를 먼저 본다

같은 `SERIALIZABLE`인데도 장애 징후가 다르게 올라오기 때문이다.

## 빠른 선택 기준

| 내가 원하는 것 | PostgreSQL 쪽 기억법 | MySQL 쪽 기억법 |
|---|---|---|
| 매 statement 최신 committed 값을 보고 싶다 | `READ COMMITTED` | `READ COMMITTED` |
| 같은 transaction 안의 plain 재조회는 흔들리지 않았으면 좋겠다 | `REPEATABLE READ` | `REPEATABLE READ` |
| "없음"이나 범위 규칙까지 안전해야 한다 | constraint, guard row, `SERIALIZABLE`을 먼저 검토 | unique/slot/guard row를 먼저 보고, RR next-key locking은 보조로만 본다 |
| 완전한 직렬화 의미가 필요하다 | `SERIALIZABLE` + retry | `SERIALIZABLE` + 짧은 transaction/lock 관찰 |

핵심은 isolation level 이름만 고르지 말고, **어떤 엔진이 어떤 메커니즘으로 그 이름을 구현하는지**까지 같이 보는 것이다.

## 꼬리질문

> Q: PostgreSQL `REPEATABLE READ`가 SQL 표준표보다 강하게 느껴지는 이유는 무엇인가요?
> 의도: PostgreSQL RR이 snapshot isolation처럼 동작한다는 점을 이해하는지 확인
> 핵심: transaction 전체 snapshot을 유지해 repeated plain `SELECT`에서 phantom까지 보이지 않기 때문이다

> Q: MySQL `REPEATABLE READ`가 PostgreSQL `REPEATABLE READ`와 다른 체감의 이유는 무엇인가요?
> 의도: snapshot과 next-key locking을 분리해 설명할 수 있는지 확인
> 핵심: MySQL은 locking read/range scan에서 next-key/gap lock이 개입해 일부 absence-check가 "잠금 기반으로" 안전해 보일 수 있기 때문이다

> Q: PostgreSQL `SERIALIZABLE`과 MySQL `SERIALIZABLE`을 같은 운영 전략으로 다루면 왜 위험한가요?
> 의도: abort/retry 중심과 blocking 중심의 차이를 아는지 확인
> 핵심: PostgreSQL은 SSI로 retry surface가 핵심이고, MySQL은 shared/next-key locking이 늘어 lock wait surface가 더 직접적으로 커지기 때문이다

## 한 줄 정리

PostgreSQL과 MySQL은 isolation level 이름은 같아도 안전성을 만드는 메커니즘이 다르므로, 특히 `REPEATABLE READ`와 `SERIALIZABLE`은 엔진 이름까지 붙여서 기억해야 한다.
