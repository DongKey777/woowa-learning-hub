# PostgreSQL `DO NOTHING` vs `DO UPDATE` Outcome Primer, with MySQL `ON DUPLICATE KEY UPDATE`

> 한 줄 요약: 초보자는 upsert 결과를 "row가 만들어졌나?"보다 "`created` / `existing` / `conflict` / `in-progress`를 서비스가 어떻게 닫나?"로 읽어야 하며, PostgreSQL `DO NOTHING`은 보통 **0-row loser 신호**, PostgreSQL `DO UPDATE`와 MySQL `ON DUPLICATE KEY UPDATE`는 보통 **existing-row merge 신호**로 보는 편이 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [PostgreSQL / MySQL Claim SQL 미니 카드](./postgresql-mysql-claim-sql-mini-card.md)
- [MySQL `ON DUPLICATE KEY UPDATE` Safety Primer](./mysql-on-duplicate-key-update-safety-primer.md)
- [UNIQUE Claim + Existing-Row Reuse Primer](./unique-claim-existing-row-reuse-primer.md)
- [Read-Before-Write Race Timeline Across MySQL and PostgreSQL](./read-before-write-race-timeline-mysql-postgresql.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [Spring Beginner Bridge: 외부 승인 성공 뒤 DB 저장이 실패하면 rollback보다 보상 + 멱등성으로 닫기](../spring/spring-payment-approval-db-failure-compensation-idempotency-primer.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: do nothing vs do update primer, postgres on conflict do nothing returning 0 row, postgres on conflict do update returning row, mysql on duplicate key update affected rows, upsert return value beginner, created existing conflict in progress upsert, do nothing loser signal, do update merge signal, mysql affectedrows 1 2 0, postgresql returning existing row confusion, upsert 뭐예요, do nothing do update 차이 뭐예요, 처음 배우는데 upsert 결과가 헷갈려요, 왜 0 row가 나와요, do nothing 언제 써요

## 먼저 잡을 멘탈모델

이 주제는 "한 문장으로 create-or-reuse를 하고 싶은데, 결과를 앱이 어떻게 읽어야 하나?"로 보면 쉽다.

- PostgreSQL `DO NOTHING`: 같은 key에 졌으면 **조용히 비켜선다**
- PostgreSQL `DO UPDATE`: 같은 key에 졌으면 **기존 row에 합류해서 update 규칙을 적용한다**
- MySQL `ON DUPLICATE KEY UPDATE`: 같은 key에 졌으면 **기존 row update 경로로 들어간다**

초보자에게 중요한 건 SQL 이름보다 **서비스 결과를 어떻게 닫을 수 있느냐**다.

- `created`: 내가 새 row를 만들었다
- `existing`: 이미 있는 winner row를 재사용하면 된다
- `conflict`: 같은 key지만 같은 요청으로 보면 안 된다
- `in-progress`: 이미 있는 row가 아직 끝나지 않았다

핵심 한 줄:

> `DO NOTHING`은 "loser를 0-row로 알려 주는 패턴"에 가깝고, `DO UPDATE`/`ON DUPLICATE KEY UPDATE`는 "기존 row를 어떻게 병합할지 정해야 하는 패턴"에 가깝다.

## 30초 비교표

| 문법 | 앱이 바로 보는 대표 신호 | 초보자 기본 해석 | 서비스 기본 다음 행동 |
|---|---|---|---|
| PostgreSQL `ON CONFLICT ... DO NOTHING RETURNING ...` | `1 row` 또는 `0 rows` | `1 row`면 내가 winner, `0 rows`면 이미 winner가 있다 | `0 rows`면 fresh read로 existing row 확인 |
| PostgreSQL `ON CONFLICT ... DO UPDATE ... RETURNING ...` | 보통 `1 row` | insert든 update든 statement는 성공했다 | returned row만 보고 `created`로 닫지 말고 merge 정책을 확인 |
| MySQL `INSERT ... ON DUPLICATE KEY UPDATE` | 보통 `affectedRows` | `1` insert, `2` existing row update, `0`은 "기존 값과 같음"일 수 있다 | `affectedRows`를 힌트로만 쓰고 canonical 결과는 fresh read로 닫기 |

이 표에서 먼저 외울 것:

- PostgreSQL `DO NOTHING`은 **existing row를 바로 돌려주지 않는다**
- PostgreSQL `DO UPDATE`는 **row를 돌려줘도 그게 곧 `created`는 아니다**
- MySQL `affectedRows`는 **DB 실행 결과 힌트**이지 비즈니스 결과 그 자체가 아니다

## 가장 단순한 서비스 시나리오

결제 요청이나 쿠폰 발급처럼 `idempotency_key`가 있다고 하자.

```sql
CREATE TABLE payment_request (
  id BIGSERIAL PRIMARY KEY,
  idempotency_key VARCHAR(64) NOT NULL UNIQUE,
  request_hash CHAR(64) NOT NULL,
  status VARCHAR(20) NOT NULL,
  response_body TEXT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

이때 서비스가 진짜로 알고 싶은 건 보통 이것이다.

1. 내가 지금 새 row를 만든 winner인가
2. 이미 있던 row가 같은 요청 재시도인가
3. 같은 key를 다른 payload로 재사용한 conflict인가
4. 기존 row가 아직 `PENDING`이라 `in-progress`로 닫아야 하나

DB 반환값은 이 질문의 **재료**일 뿐, 마지막 business outcome 그 자체는 아니다.

## PostgreSQL `DO NOTHING`: winner면 row, loser면 0-row

가장 beginner-friendly한 패턴은 보통 이것이다.

```sql
INSERT INTO payment_request (
  idempotency_key,
  request_hash,
  status,
  updated_at
) VALUES (
  :idempotency_key,
  :request_hash,
  'PENDING',
  NOW()
)
ON CONFLICT (idempotency_key) DO NOTHING
RETURNING id, idempotency_key, request_hash, status;
```

이 SQL은 초보자에게 읽기 쉽다.

- `RETURNING` 결과가 `1 row`면 내가 insert winner다
- `RETURNING` 결과가 `0 rows`면 같은 key winner가 이미 있었다

즉 PostgreSQL `DO NOTHING`은 "기존 row를 반환해 주는 create-or-reuse"가 아니라:

- winner면 새 row를 준다
- loser면 아무 row도 안 준다

그래서 보통 서비스는 이렇게 닫는다.

| PostgreSQL 결과 | 서비스 해석 | 다음 액션 |
|---|---|---|
| `RETURNING 1 row` | `created` 또는 `claimed PENDING` | 후속 작업 진행 |
| `RETURNING 0 rows` | `existing` 후보 | primary/fresh read로 기존 row 조회 |

fresh read 이후에는 보통 이렇게 갈린다.

| 기존 row 상태 | 서비스 결과 |
|---|---|
| 같은 `request_hash` + `SUCCEEDED` | 기존 성공 결과 replay |
| 같은 `request_hash` + `PENDING` | `in-progress` |
| 다른 `request_hash` | `conflict` |

초보자 기억법:

> PostgreSQL `DO NOTHING`은 "패배 사실"은 알려 주지만 "winner row 내용"은 바로 주지 않는다.

## PostgreSQL `DO UPDATE`: row가 돌아와도 `created`라고 단정하지 말기

이번에는 conflict 시 update branch를 타는 패턴이다.

```sql
INSERT INTO payment_request (
  idempotency_key,
  request_hash,
  status,
  updated_at
) VALUES (
  :idempotency_key,
  :request_hash,
  'PENDING',
  NOW()
)
ON CONFLICT (idempotency_key) DO UPDATE
SET updated_at = NOW()
RETURNING id, idempotency_key, request_hash, status, updated_at;
```

이 패턴은 insert path와 update path 모두에서 row가 돌아올 수 있다.

즉 앱 입장에서는:

- row가 돌아왔다 -> statement는 성공했다
- 하지만 그 row가 "방금 새로 만들어진 row"라는 뜻은 아니다

초보자가 여기서 자주 틀리는 문장은 이것이다.

> `RETURNING`으로 row를 받았으니 항상 create 성공이다

아니다. `DO UPDATE`는 같은 key 충돌 시 **기존 row에 update semantics를 적용**한 것이다.

그래서 이 문법은 보통 이런 상황에서만 안전하게 읽는다.

- 같은 key의 기존 row를 일부 갱신해도 정책상 괜찮다
- "최초 값 보존", "허용된 상태 전이", "request_hash 동일 시에만 갱신" 같은 merge 규칙이 이미 있다

반대로 초보자 기본값으로는 아래처럼 읽는 편이 안전하다.

| 보이는 것 | 바로 내리면 안 되는 결론 |
|---|---|
| `RETURNING 1 row` | "무조건 새로 생성됐다" |
| update branch가 성공 | "같은 요청 재시도이므로 무조건 안전하다" |
| SQL 예외가 없었다 | "conflict가 숨겨지지 않았다" |

즉 PostgreSQL `DO UPDATE`는 반환 row가 편하더라도, **정책 없는 overwrite**로 쓰면 안 된다.

## MySQL `ON DUPLICATE KEY UPDATE`: 보통 `affectedRows`를 먼저 본다

MySQL에서 초보자가 자주 접하는 표면 결과는 `RETURNING`보다 `affectedRows`다.

```sql
INSERT INTO payment_request (
  idempotency_key,
  request_hash,
  status,
  updated_at
) VALUES (
  ?,
  ?,
  'PENDING',
  NOW()
)
ON DUPLICATE KEY UPDATE
  updated_at = NOW();
```

MySQL 문서 기준 대표 해석은 이렇다.

| `affectedRows` | 초보자 해석 |
|---|---|
| `1` | 새 row insert |
| `2` | duplicate path에서 기존 row update |
| `0` | duplicate path였지만 결과 값이 현재 값과 같아 실질 변경이 없을 수 있음 |

하지만 여기서 바로 business outcome을 닫으면 안 된다.

### 왜 조심해야 하나

1. `affectedRows = 2`는 "한 existing row가 update branch를 탔다"는 뜻이지, "두 row가 바뀌었다"는 뜻이 아니다.
2. `affectedRows = 0`은 "existing row와 값이 같았다"일 수 있다.
3. MySQL 문서 기준 `CLIENT_FOUND_ROWS` 옵션을 쓰면 위 `0`이 `1`로 보일 수 있다.

즉 MySQL에서는 특히 이 문장을 먼저 고정해야 한다.

> `affectedRows`는 실행 path 힌트이지, `created` / `replay` / `conflict`를 완성해 주는 비즈니스 결과가 아니다.

## beginner 기본 패턴: DB 신호 -> fresh read -> 서비스 결과

PostgreSQL과 MySQL을 함께 놓고 보면 초보자 기본 패턴은 비슷하다.

| 엔진/문법 | DB가 직접 알려 주는 것 | 앱이 추가로 확인할 것 |
|---|---|---|
| PostgreSQL `DO NOTHING` | winner였는지 loser였는지 | loser면 existing row 상태와 hash |
| PostgreSQL `DO UPDATE` | statement가 insert 또는 update로 성공했는지 | 그 update가 replay인지 overwrite인지 |
| MySQL `ON DUPLICATE KEY UPDATE` | insert path인지 duplicate update path인지 대략의 힌트 | existing row 상태, hash, merge 정책 |

초보자용 서비스 pseudo-flow:

```text
1. upsert 실행
2. DB가 "내가 새 row를 만들었는지" 또는 "기존 row branch로 갔는지" 알려준다
3. existing-row 가능성이 있으면 fresh read
4. request_hash / status / response_body로
   - replay
   - in-progress
   - conflict
   를 닫는다
```

이 흐름이 필요한 이유는 `same key`와 `same request`가 같은 말이 아니기 때문이다.

## 반환값을 서비스 결과로 잘못 번역하는 흔한 실수

### 1. PostgreSQL `DO NOTHING`의 `0 rows`를 실패로만 읽기

`0 rows`는 종종 정상 경쟁 결과다.

- "이미 winner가 있다"
- "기존 row를 읽으러 가라"

즉 `0 rows`는 `duplicate key exception`과 비슷한 **loser 신호**로 읽는 편이 맞다.

### 2. PostgreSQL `DO UPDATE RETURNING`의 `1 row`를 `created`로 읽기

이건 단지 insert/update 중 하나가 성공했다는 뜻일 뿐이다.

- created
- replay-safe update
- conflict를 숨긴 overwrite

이 셋은 returned row 한 줄만으로는 자동 구분되지 않는다.

### 3. MySQL `affectedRows = 2`를 "두 건 처리"로 읽기

아니다. duplicate path에서 기존 row 하나를 update했다는 뜻이다.

### 4. MySQL `affectedRows = 0`을 "아무 일도 없었다"로 읽기

duplicate path였지만 이미 같은 값이라 no-op였을 수 있다.
게다가 연결 옵션에 따라 `1`로 보일 수도 있다.

## 언제 어떤 문법이 beginner에게 더 읽기 쉬운가

| 목표 | 초보자 기본 추천 | 이유 |
|---|---|---|
| "없으면 만들고, 있으면 기존 row를 다시 읽어 replay/conflict/in-progress를 나누고 싶다" | PostgreSQL `DO NOTHING` 또는 plain insert + duplicate handling | loser 신호가 단순하다 |
| "같은 key 충돌 시 제한된 merge를 한 문장에 담고 싶다" | PostgreSQL `DO UPDATE`, MySQL `ON DUPLICATE KEY UPDATE` | merge 규칙이 분명할 때만 읽기 쉽다 |
| "같은 요청 재시도와 다른 payload 충돌을 구분하고 싶다" | 어떤 문법이든 `request_hash` + fresh read | SQL branch만으로는 business 의미가 완성되지 않는다 |

핵심은 문법보다 정책이다.

- `DO NOTHING`은 "existing row를 다시 읽어 의미를 닫겠다"는 정책에 잘 맞는다
- `DO UPDATE`와 `ON DUPLICATE KEY UPDATE`는 "충돌 시 병합 규칙이 이미 있다"는 정책에 잘 맞는다

## 자주 묻는 짧은 질문

> Q. PostgreSQL에서 existing row를 한 번에 돌려받고 싶어서 `DO UPDATE`를 써도 되나요?
> 짧은 답: 가능은 하지만, 그 순간부터 "그 update가 정책상 안전한가?"를 책임져야 한다. 단순 반환 편의만 보고 고르면 overwrite 의미가 섞인다.

> Q. MySQL `affectedRows`만으로 `replay`와 `conflict`를 구분할 수 있나요?
> 짧은 답: 보통 어렵다. 같은 key라도 같은 요청인지 다른 payload 충돌인지는 existing row와 `request_hash`를 봐야 한다.

> Q. PostgreSQL `DO NOTHING`은 왜 existing row를 바로 안 주나요?
> 짧은 답: 이 문법의 의미가 "삽입을 건너뛴다"에 가깝기 때문이다. winner row 재사용은 follow-up read 단계에서 닫는 편이 기본이다.

## 한 줄 정리

초보자 기준으로는 PostgreSQL `DO NOTHING`을 "0-row loser 신호 후 fresh read", PostgreSQL `DO UPDATE`와 MySQL `ON DUPLICATE KEY UPDATE`를 "existing-row merge 문법 후 정책 검증"으로 읽으면 서비스 결과와 반환값 패턴이 가장 덜 헷갈린다.
