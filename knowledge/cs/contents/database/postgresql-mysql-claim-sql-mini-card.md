# PostgreSQL / MySQL Claim SQL 미니 카드

> 한 줄 요약: 같은 `idempotency_key`를 한 번만 선점하는 목적은 셋 다 같지만, 초보자는 `INSERT`는 **duplicate 예외**, PostgreSQL `ON CONFLICT DO NOTHING`은 **0-row loser 신호**, MySQL `ON DUPLICATE KEY UPDATE`는 **update branch 성공 신호**로 읽는다고 먼저 고정하면 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [UNIQUE Claim + Existing-Row Reuse Primer](./unique-claim-existing-row-reuse-primer.md)
- [PostgreSQL `DO NOTHING` vs `DO UPDATE` Outcome Primer, with MySQL `ON DUPLICATE KEY UPDATE`](./do-nothing-vs-do-update-outcome-primer-postgresql-mysql.md)
- [MySQL `ON DUPLICATE KEY UPDATE` Safety Primer](./mysql-on-duplicate-key-update-safety-primer.md)
- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: postgresql mysql claim sql mini card, insert on conflict do nothing on duplicate key comparison, idempotency claim sql beginner, same idempotency pattern postgres mysql, plain insert duplicate key vs do nothing vs on duplicate key, claim path beginner postgres mysql, on conflict do nothing 0 rows, on duplicate key update affected rows beginner, unique claim syntax comparison, first writer wins sql card, postgresql mysql upsert claim mini card, duplicate exception vs silent loser vs update branch, 멱등성 claim SQL 비교, insert do nothing on duplicate key 차이, postgres mysql claim path one page, beginner claim sql chooser

## 먼저 멘탈모델

초보자는 이 주제를 "같은 번호표를 누가 먼저 잡느냐"로 보면 쉽다.

- `INSERT`: 번호표를 먼저 잡은 사람만 통과하고, 뒤 요청은 duplicate 예외를 본다
- PostgreSQL `ON CONFLICT DO NOTHING`: 뒤 요청이 져도 예외 대신 조용히 비켜서며 `0 rows`를 본다
- MySQL `ON DUPLICATE KEY UPDATE`: 뒤 요청이 지면 update branch로 들어가 statement는 성공처럼 끝난다

핵심은 SQL 이름보다 **loser가 무엇을 보느냐**다.

> 셋 다 "한 줄만 남긴다"는 목적은 비슷하지만, 앱이 받는 신호는 서로 다르다.

## 같은 예시 테이블

```sql
CREATE TABLE payment_request (
  id BIGINT PRIMARY KEY,
  idempotency_key VARCHAR(64) NOT NULL UNIQUE,
  request_hash CHAR(64) NOT NULL,
  status VARCHAR(20) NOT NULL,
  response_body TEXT NULL
);
```

이 테이블에서 서비스가 알고 싶은 질문은 보통 아래 셋이다.

1. 내가 지금 winner인가
2. 이미 있는 row가 같은 요청 재시도인가
3. 같은 key를 다른 payload로 재사용한 conflict인가

## 30초 비교표

| claim SQL | loser가 처음 보는 것 | 초보자 기본 해석 | 다음 행동 |
|---|---|---|---|
| plain `INSERT` | duplicate 예외 (`23505` / `1062`) | 이미 winner row가 있다 | fresh read로 existing row 분류 |
| PostgreSQL `INSERT ... ON CONFLICT DO NOTHING RETURNING ...` | `0 rows` | 이미 winner row가 있다 | fresh read로 existing row 분류 |
| MySQL `INSERT ... ON DUPLICATE KEY UPDATE ...` | update branch 성공, 보통 `affectedRows` 변화 | existing row 경로로 들어갔다 | business 컬럼 overwrite 여부 확인 후 fresh read로 닫기 |

먼저 외울 것:

- `INSERT`는 **패배를 예외로 보여 준다**
- PostgreSQL `DO NOTHING`은 **패배를 0-row로 보여 준다**
- MySQL `ON DUPLICATE KEY UPDATE`는 **패배를 성공한 update 경로처럼 보여 줄 수 있다**

## 1. plain `INSERT`: 가장 직선적인 claim

PostgreSQL과 MySQL 모두 가장 단순한 시작점은 같다.

```sql
INSERT INTO payment_request (
  id,
  idempotency_key,
  request_hash,
  status
) VALUES (
  :id,
  :idempotency_key,
  :request_hash,
  'PENDING'
);
```

이 패턴은 읽기 쉽다.

- 성공: 내가 winner다
- duplicate 예외: 이미 누군가 winner다

초보자에게 좋은 점은 "패배했다"는 신호가 분명하다는 것이다.
그래서 다음 단계도 단순하다.

1. duplicate를 잡는다
2. primary/fresh read로 기존 row를 읽는다
3. `same hash`면 replay 또는 `in-progress`
4. `different hash`면 `conflict`

## 2. PostgreSQL `ON CONFLICT DO NOTHING`: loser를 0-row로 받기

PostgreSQL에서는 같은 흐름을 예외 없이 더 짧게 쓸 수 있다.

```sql
INSERT INTO payment_request (
  id,
  idempotency_key,
  request_hash,
  status
) VALUES (
  :id,
  :idempotency_key,
  :request_hash,
  'PENDING'
)
ON CONFLICT (idempotency_key) DO NOTHING
RETURNING id, idempotency_key, request_hash, status;
```

이 패턴의 핵심은 아주 단순하다.

- `1 row`: 내가 winner다
- `0 rows`: 이미 winner가 있다

즉 `DO NOTHING`은 existing row를 바로 주지 않는다.
패배 사실만 조용히 알려 준다.

초보자 기억법:

> PostgreSQL `DO NOTHING`은 "duplicate 예외를 0-row 신호로 바꾼 claim"에 가깝다.

## 3. MySQL `ON DUPLICATE KEY UPDATE`: loser가 update branch로 들어간다

MySQL에서는 보통 이렇게 쓴다.

```sql
INSERT INTO payment_request (
  id,
  idempotency_key,
  request_hash,
  status
) VALUES (
  ?,
  ?,
  ?,
  'PENDING'
)
ON DUPLICATE KEY UPDATE
  status = status;
```

이 문법도 row를 하나로 유지한다.
다만 loser가 보는 신호가 앞의 두 패턴과 다르다.

- insert winner면 insert path 성공
- duplicate loser면 update branch 성공

여기서 초보자가 가장 자주 하는 오해는 이것이다.

> statement가 성공했으니 내가 새 row를 만들었다

아니다. duplicate loser도 "성공한 statement"처럼 끝날 수 있다.

그래서 MySQL에서는 특히 아래 규칙이 중요하다.

- `ON DUPLICATE KEY UPDATE`를 써도 **business 컬럼을 함부로 덮어쓰지 않는다**
- duplicate path는 no-op 또는 안전한 보조 컬럼 update만 둔다
- 최종 business outcome은 fresh read와 `request_hash` 비교로 닫는다

### `affectedRows`는 어떻게 읽나

초보자용으로는 이 정도만 기억하면 충분하다.

| MySQL 표면 신호 | 의미 |
|---|---|
| `affectedRows = 1` | insert path였을 가능성이 크다 |
| `affectedRows = 2` | duplicate update path였을 가능성이 크다 |
| `affectedRows = 0` | no-op update였을 수 있다 |

단, `CLIENT_FOUND_ROWS` 같은 드라이버 옵션에 따라 숫자 해석이 달라질 수 있으므로, `affectedRows`만으로 `created`를 닫지 않는 편이 안전하다.

## 언제 어떤 시작점을 고르나

| 시작점 | beginner 기본 추천 장면 | 이유 |
|---|---|---|
| plain `INSERT` | duplicate를 예외로 분명히 드러내고 싶을 때 | winner/loser 신호가 가장 직선적이다 |
| PostgreSQL `DO NOTHING` | PostgreSQL에서 loser를 예외 대신 0-row로 받고 싶을 때 | duplicate를 제어 흐름으로 다루기 쉽다 |
| MySQL `ON DUPLICATE KEY UPDATE` | MySQL에서 한 문장 claim을 유지하되 overwrite 정책을 엄격히 통제할 수 있을 때 | duplicate path를 SQL 안에서 흡수할 수 있다 |

초보자 기본값으로는 아래처럼 잡으면 크게 틀리지 않는다.

- PostgreSQL: `INSERT` 또는 `DO NOTHING`
- MySQL: plain `INSERT`부터 이해한 뒤, 필요할 때만 `ON DUPLICATE KEY UPDATE`

## 자주 하는 오해

- "`DO NOTHING`이면 기존 row도 바로 반환된다"
  - 아니다. 보통 loser는 `0 rows`만 본다.
- "`ON DUPLICATE KEY UPDATE`는 멱등성을 자동으로 해결한다"
  - 아니다. 같은 key와 같은 request인지 앱이 따로 확인해야 한다.
- "`affectedRows = 1`이면 무조건 새 row다"
  - 드라이버/statement 모양에 따라 그렇게 단정하면 위험하다.
- "셋 중 어느 문법을 써도 business outcome은 저절로 같다"
  - 아니다. `same hash` / `different hash` 분류와 fresh read가 여전히 필요하다.

## 처음에는 이것만 기억하면 충분하다

1. 세 문법 모두 목적은 "같은 key winner 하나"다.
2. 차이는 loser 신호다: 예외, `0 rows`, update branch.
3. 최종 응답은 SQL 문법이 아니라 fresh read + `request_hash` 비교로 닫는다.
