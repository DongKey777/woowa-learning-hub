# Hibernate Lock SQL Log to Deadlock Triage Bridge

> 한 줄 요약: Hibernate lock SQL 로그는 "피해자 SQL"을 보여 주고, MySQL lock/deadlock 관찰은 "누가 막았는지"를 보여 준다. 초급자는 두 화면을 한 번에 보려 하지 말고 **같은 테이블·같은 key·같은 시각**으로 이어 붙이면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Hibernate SQL Log + EXPLAIN Lock Verification Primer](./hibernate-sql-log-explain-lock-verification-primer.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Deadlock Case Study](./deadlock-case-study.md)
- [Transaction Timeout vs Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: hibernate deadlock triage bridge, hibernate lock sql log blocker query, mysql deadlock blocker query beginner, spring jpa lock wait investigation, hibernate for update log to innodb status, mysql sys innodb_lock_waits beginner, deadlock victim sql to blocker sql, logged sql to blocker query bridge, spring cannotacquirelockexception blocker query, mysql 1213 1205 hibernate triage, 하이버네이트 락 sql 로그 데드락 조사, 하이버네이트 로그로 blocker 쿼리 찾기, mysql 데드락 blocker 쿼리 찾기 초급, spring jpa lock wait 조사 순서, for update 로그에서 deadlock 추적

## 먼저 잡을 그림

초급자 기준으로는 아래 두 줄만 먼저 기억하면 된다.

> 애플리케이션 로그는 "내 요청이 어떤 SQL을 날렸는가"를 보여 준다.
> DB 관찰 화면은 "그 SQL이 누구에게 막혔는가" 또는 "방금 누구와 순환 대기였는가"를 보여 준다.

즉 로그 한 줄만으로 deadlock 원인을 다 알 수는 없고, DB 화면 한 장만으로도 서비스 코드 맥락이 안 보인다.

둘을 연결하는 최소 고리는 보통 이 네 가지다.

- 같은 시각대인가
- 같은 테이블인가
- 같은 key 값인가
- 내 SQL이 `waiter`인지 `victim`인지인가

## 30초 분기표

| 보인 신호 | 지금 뜻하는 것 | 다음 한 걸음 |
|---|---|---|
| MySQL `1205` lock wait timeout | 내 SQL이 오래 기다렸지만 상대는 아직 살아 있을 수 있다 | 현재 blocker를 찾는다 |
| MySQL `1213` deadlock found | 순환 대기가 났고 DB가 희생자를 골랐다 | 가장 최근 deadlock 기록을 본다 |
| Spring `CannotAcquireLockException`만 보임 | timeout과 deadlock이 섞여 있을 수 있다 | root `errno`/`SQLSTATE`를 다시 본다 |

핵심은 `1205`와 `1213`을 같은 "락 에러"로 뭉개지 않는 것이다.

## 예시로 보는 출발점

애플리케이션 로그가 이렇게 찍혔다고 하자.

```text
org.springframework.dao.CannotAcquireLockException: could not execute statement
Caused by: java.sql.SQLException: Deadlock found when trying to get lock; try restarting transaction
SQLState: 40001
ErrorCode: 1213
```

Hibernate SQL 로그는 이렇게 보일 수 있다.

```text
select
    ci1_0.coupon_id,
    ci1_0.member_id,
    ci1_0.status
from coupon_issue ci1_0
where ci1_0.coupon_id=?
  and ci1_0.member_id=?
for update
```

여기서 바로 결론을 내리기보다, 초급자는 먼저 다음만 메모하면 충분하다.

- 테이블: `coupon_issue`
- key 후보: `(coupon_id, member_id)`
- SQL 성격: `FOR UPDATE` locking read
- DB 신호: `1213 deadlock`

이 네 줄이 있으면 이후 DB 화면에서 blocker/victim을 이어 붙이기 쉬워진다.

## 1. 애플리케이션 쪽에서 먼저 챙길 것

DB 화면을 열기 전에, 로그에서 아래 네 줄을 먼저 챙긴다.

| 로그에서 챙길 것 | 왜 필요한가 |
|---|---|
| 실제 SQL shape | 어떤 테이블과 조건을 봐야 하는지 정한다 |
| bind 값 | 같은 row/key를 잡고 있는 blocker를 찾을 때 필요하다 |
| 예외 코드 `1205` vs `1213` | 현재 blocker를 볼지, 최근 deadlock 기록을 볼지 갈린다 |
| 찍힌 시각 | DB 관찰 결과와 대조할 기준점이 된다 |

예를 들어 아래처럼 정리하면 된다.

```text
time=10:14:22
sql=select ... from coupon_issue where coupon_id=? and member_id=? for update
binds=(10, 42)
errno=1213
```

중요한 점은 "완벽한 SQL 복원"보다 **같은 row를 가리키는 단서 확보**다.

## 2. lock wait timeout이면 현재 blocker부터 본다

`1205`는 "기다리다 끝났다"에 가깝다.
즉 상대 트랜잭션이 아직 살아 있을 가능성이 있어서, 현재 blocker를 찾는 흐름이 우선이다.

MySQL 8 계열에서 가장 beginner 친화적인 시작점은 `sys.innodb_lock_waits`다.

```sql
SELECT
    waiting_pid,
    waiting_query,
    blocking_pid,
    blocking_query,
    locked_table,
    locked_index,
    wait_age
FROM sys.innodb_lock_waits;
```

이 화면에서 초급자가 먼저 볼 것은 세 가지다.

- `waiting_query`가 내 Hibernate 로그 SQL shape와 비슷한가
- `blocking_query`가 어떤 쓰기 SQL인지 보이는가
- `locked_table` / `locked_index`가 로그에서 추정한 대상과 맞는가

예를 들어 이렇게 이어 읽는다.

| 화면 | 읽는 법 |
|---|---|
| `waiting_query = select ... for update` | 내 요청이 기다리는 쪽이다 |
| `blocking_query = update coupon_issue ...` | 상대가 같은 row를 먼저 잡고 있다 |
| `locked_table = app/coupon_issue` | 같은 테이블로 연결된다 |

이 단계의 목표는 "정답 설계"가 아니라 **blocker SQL 한 줄 확보**다.

## 3. deadlock이면 현재 blocker보다 최근 deadlock 기록을 본다

`1213`는 이미 deadlock이 끝났다는 뜻이다.
DB가 희생자를 골라 transaction 하나를 끊었기 때문에, "지금 누가 막고 있지?"만 찾으면 늦을 수 있다.

이때는 `SHOW ENGINE INNODB STATUS\G`로 가장 최근 deadlock 기록을 본다.

```sql
SHOW ENGINE INNODB STATUS\G
```

초급자는 출력 전체를 읽으려 하지 말고 `LATEST DETECTED DEADLOCK` 주변만 본다.

거기서 먼저 찾을 항목은 이 정도면 충분하다.

- 두 트랜잭션이 각각 어떤 SQL을 실행했는가
- 어떤 테이블/인덱스를 잡으려 했는가
- 어느 쪽이 victim으로 rollback 되었는가

읽는 순서는 단순하다.

1. 내 Hibernate 로그 SQL과 비슷한 문장을 deadlock 기록에서 찾는다.
2. 그 옆에 나온 다른 SQL을 상대 쿼리 후보로 본다.
3. 두 SQL이 같은 key를 반대 순서로 잡았는지 확인한다.

즉 deadlock에서는 "현재 blocker 찾기"보다 **방금 충돌한 두 SQL 복원**이 더 중요하다.

## 4. 로그 SQL과 blocker SQL을 이어 붙이는 가장 쉬운 방법

초급자가 가장 덜 흔들리는 연결 순서는 아래다.

| 순서 | 확인 질문 | 예시 |
|---|---|---|
| 1 | 같은 테이블인가 | 둘 다 `coupon_issue`를 만지는가 |
| 2 | 같은 key 값인가 | 둘 다 `(10, 42)` 또는 같은 주문 번호를 만지는가 |
| 3 | 읽기 vs 쓰기 역할이 무엇인가 | 나는 `select ... for update`, 상대는 `update`인가 |
| 4 | 순서가 엇갈렸는가 | 한쪽은 `coupon_issue -> coupon`, 다른 쪽은 `coupon -> coupon_issue`인가 |

예를 들어 내 로그가 아래라면:

```text
select ... from coupon_issue
where coupon_id=10 and member_id=42
for update
```

DB 쪽 상대 SQL이 아래처럼 보일 수 있다.

```text
update coupon_issue
set status='ISSUED'
where coupon_id=10 and member_id=42
```

이 경우 초급자 결론은 복잡하지 않다.

- 같은 row를 만지고 있다
- 내 SQL은 lock을 기다리는 locking read다
- 상대 SQL은 이미 같은 row를 잡은 write다

이 정도만 연결해도 "어떤 blocker query를 먼저 읽어야 하나"가 정리된다.

## 5. deadlock과 lock wait를 같은 방식으로 조사하면 헷갈린다

| 항목 | lock wait timeout (`1205`) | deadlock (`1213`) |
|---|---|---|
| 우선 질문 | 지금 누가 막고 있나 | 방금 어떤 두 SQL이 순환 대기였나 |
| 먼저 볼 화면 | `sys.innodb_lock_waits` | `SHOW ENGINE INNODB STATUS\G` |
| 기대 산출물 | 현재 blocker query 1개 | 충돌한 SQL 2개와 lock 순서 |
| 흔한 실수 | timeout인데 무조건 retry만 건다 | deadlock인데 현재 blocker만 찾다가 단서를 놓친다 |

같은 "락 장애"라도 조사 시작점이 다르다는 점만 잡아도 초급자 혼란이 크게 줄어든다.

## 6. 조사 후 팀에 남기면 좋은 최소 메모

아래 다섯 줄이면 보통 다음 사람이 다시 처음부터 헤매지 않는다.

```text
victim_sql=select ... for update on coupon_issue(coupon_id, member_id)
binds=(10,42)
db_signal=1213 deadlock
other_sql=update coupon_issue set status='ISSUED' ...
hypothesis=same row contention or lock ordering mismatch
```

만약 `1205`였다면 `other_sql` 자리에 현재 `blocking_query`를 적으면 된다.

## common confusion

- "Hibernate SQL 로그만 있으면 deadlock 원인이 다 나온다"
  - 아니다. 로그는 보통 내 SQL만 보여 주고, 상대 SQL은 DB 관찰 화면에서 찾아야 한다.
- "`CannotAcquireLockException`이면 전부 deadlock이다"
  - 아니다. MySQL에서는 `1205` lock wait timeout도 이 이름으로 보일 수 있다.
- "deadlock도 blocker query 하나만 찾으면 된다"
  - 아니다. deadlock은 두 SQL의 순환 관계가 핵심이다.
- "`SHOW ENGINE INNODB STATUS`는 항상 현재 상태를 보여 준다"
  - deadlock 구간에서는 보통 "가장 최근 deadlock 기록"을 읽는 용도로 생각하는 편이 맞다.
- "bind 값이 없어도 대충 같은 테이블이면 충분하다"
  - 아니다. 같은 테이블 안에서도 어떤 key가 막혔는지가 중요하다.

## 여기까지 되면 충분하다

초급자 기준 종료 조건은 아래 네 가지다.

1. 내 Hibernate 로그에서 victim/waiter SQL 한 줄을 확보했다.
2. `1205`인지 `1213`인지 분리했다.
3. DB 화면에서 blocker SQL 또는 deadlock 상대 SQL을 하나 이상 확보했다.
4. 둘이 같은 테이블·같은 key·같은 시각대라는 연결고리를 설명할 수 있다.

여기까지 되면 "로그만 봤다"에서 끝나지 않고, 실제 blocker query나 deadlock 상대 SQL까지 따라간 것이다.
그다음의 lock ordering 수정, retry 정책, transaction 축소는 관련 문서로 넘기면 된다.

## 한 줄 정리

Hibernate lock SQL 로그는 "피해자 SQL"을 보여 주고, MySQL lock/deadlock 관찰은 "누가 막았는지"를 보여 준다. 초급자는 두 화면을 한 번에 보려 하지 말고 **같은 테이블·같은 key·같은 시각**으로 이어 붙이면 된다.
