# Hibernate SQL Log + EXPLAIN Lock Verification Primer

> 한 줄 요약: Spring/Hibernate의 locking repository 메서드를 믿기 전에, **실제로 찍힌 SQL**을 Hibernate 로그에서 확인하고 그 SQL을 MySQL `EXPLAIN`에 붙여 intended index path가 유지되는지 보는 beginner primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring/JPA Exact-Key Lock Mapping Guide](./spring-jpa-exact-key-lock-mapping-guide.md)
- [Hibernate Lock SQL Log to Deadlock Triage Bridge](./hibernate-lock-sql-log-to-deadlock-triage-bridge.md)
- [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: hibernate sql log explain primer, spring jpa lock verification explain, mysql explain for update beginner, hibernate sql log index path verification, locking repository method explain check, spring data jpa for update explain checklist, hibernate logged sql mysql explain, pessimistic lock index path drift, for update repository method verification, beginner hibernate explain primer, 하이버네이트 sql 로그 explain 검증, 락킹 repository 메서드 explain 확인, mysql for update 인덱스 경로 검증, jpa 비관적 락 explain 보는 법, logged sql explain beginner

## 먼저 잡을 그림

초급자 기준으로는 이 문장을 먼저 기억하면 된다.

> repository 메서드는 "락을 걸고 싶다"는 의도를 담고, Hibernate SQL 로그는 "실제로 어떤 SQL이 나갔는지"를 보여 주고, MySQL `EXPLAIN`은 "그 SQL이 어떤 인덱스 길을 탔는지"를 보여 준다.

즉 "`@Lock(PESSIMISTIC_WRITE)`를 붙였다"만으로는 검증이 끝나지 않는다.

- Hibernate 로그로 실제 `FOR UPDATE`/`FOR SHARE` SQL이 나갔는지 본다
- MySQL `EXPLAIN`으로 그 SQL이 intended index path를 탔는지 본다
- 마지막 correctness는 여전히 `UNIQUE`나 business constraint가 맡는다

이 세 층을 분리하면 beginner가 가장 많이 헷갈리는 "락을 걸었는데 왜 검증이 더 필요하지?"가 정리된다.

## 한눈에 보는 검증 흐름

| 단계 | 지금 확인하는 것 | 기대하는 질문 |
|---|---|---|
| 1. repository 메서드 확인 | 어떤 조건으로 잠그려는가 | full key equality인가, join/정렬이 붙었나 |
| 2. Hibernate SQL 로그 확인 | 실제로 어떤 SQL이 실행됐는가 | `FOR UPDATE`/`FOR SHARE`가 붙었나, 조건이 바뀌지 않았나 |
| 3. MySQL `EXPLAIN` 실행 | 어떤 index path를 탔는가 | intended index를 `key`로 잡았나, `rows`가 작나 |
| 4. 해석 정리 | lock intention과 access path가 맞나 | "의도한 같은 인덱스 칸"을 읽는다고 말할 수 있나 |

핵심은 "코드 -> SQL -> plan" 순서를 끊지 않는 것이다.

## 예시로 보는 가장 단순한 장면

예를 들어 coupon 중복 발급 pre-check를 아래처럼 만들었다고 하자.

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("""
    select ci
    from CouponIssue ci
    where ci.couponId = :couponId
      and ci.memberId = :memberId
    """)
Optional<CouponIssue> findByCouponIdAndMemberIdForUpdate(Long couponId, Long memberId);
```

그리고 인덱스가 아래라고 하자.

```sql
UNIQUE KEY uq_coupon_member (coupon_id, member_id)
```

beginner 기준 기대 그림은 이렇다.

1. Hibernate 로그에서 `where coupon_id = ? and member_id = ? for update` 비슷한 SQL이 보여야 한다.
2. 그 SQL을 값으로 치환해 MySQL `EXPLAIN`을 돌렸을 때 `key = uq_coupon_member`가 보여야 한다.
3. `rows`도 대개 `1` 근처여야 한다.

이 세 줄이 맞아야 "의도한 locking repository 메서드가 아직 같은 index path를 탄다"라고 말하기 쉽다.

## 1. Hibernate SQL 로그에서 먼저 보는 것

먼저 해야 할 일은 "내가 상상한 SQL"이 아니라 "실제로 찍힌 SQL"을 보는 것이다.

예시 설정은 보통 이 정도면 충분하다.

```properties
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.orm.jdbc.bind=TRACE
```

환경에 따라 바인드 로그 카테고리는 다를 수 있지만, beginner 관점에서는 아래 두 질문이 더 중요하다.

- 실제 SQL 끝에 `FOR UPDATE` 또는 `FOR SHARE`가 붙었는가
- `WHERE` shape가 repository 메서드 의도와 같은가

예를 들면 이런 로그를 기대한다.

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

여기서 beginner가 바로 체크할 포인트는 세 개다.

- 조건이 full key equality 그대로인가
- 불필요한 `order by`, `join`, 함수가 끼지 않았는가
- 정말 locking clause가 붙었는가

로그 단계에서 이미 query drift가 보이면 `EXPLAIN`까지 가기 전에 repository 메서드를 다시 보는 편이 빠르다.

## 2. 로그에 찍힌 SQL을 EXPLAIN용으로 옮기는 법

`EXPLAIN`은 애플리케이션 로그의 `?`를 그대로 이해하지 못하므로, 실제 값으로 치환한 SQL이 필요하다.

예시는 이렇게 만든다.

```sql
EXPLAIN
SELECT coupon_id, member_id, status
FROM coupon_issue
WHERE coupon_id = 10
  AND member_id = 42
FOR UPDATE;
```

여기서 중요한 점은 "비슷한 SQL"이 아니라 **로그에 찍힌 SQL과 최대한 같은 shape**를 유지하는 것이다.

- `FOR UPDATE`를 빼지 않는다
- `ORDER BY`, `LIMIT`, join이 로그에 있으면 그대로 둔다
- 컬럼/테이블 alias도 가능하면 같은 모양으로 둔다

왜냐하면 beginner가 가장 자주 하는 실수가 "단순화한 다른 SQL"을 `EXPLAIN`해 놓고 원래 repository 메서드도 같다고 믿는 것이기 때문이다.

## 3. MySQL EXPLAIN에서 무엇을 읽어야 하나

이 primer에서는 `EXPLAIN` 전체를 깊게 읽기보다, lock verification에 필요한 최소 항목만 본다.

| 항목 | 기대하는 모습 | 초보자 해석 |
|---|---|---|
| `key` | intended index 이름 | 원하던 책꽂이를 실제로 골랐다 |
| `type` | `const`, `ref`, `eq_ref`처럼 좁은 접근 | 거의 한 칸만 확인한다 |
| `rows` | 아주 작다. 보통 `1` 근처 | 넓은 범위를 훑는 계획이 아니다 |
| `Extra` | 정렬/임시/과한 후처리 신호가 크지 않다 | lookup 중심 query shape다 |

가장 먼저 볼 것은 역시 `key`다.

예를 들면 이런 결과가 beginner 기준 good sign이다.

| id | table | type | key | rows | Extra |
|---|---|---|---|---|---|
| 1 | coupon_issue | ref | uq_coupon_member | 1 | Using index |

반대로 아래 신호는 바로 멈춰야 한다.

| 보이는 신호 | 왜 조심해야 하나 |
|---|---|
| `key = NULL` | 인덱스 path가 아니다 |
| `key = idx_coupon_id` | full unique key 대신 prefix 쪽을 탔을 수 있다 |
| `rows`가 크다 | exact-key probe보다 넓은 range/scan일 가능성이 크다 |
| `Extra`에 정렬/임시 처리 신호가 크다 | locking pre-check 전용 query에서 drift가 났을 수 있다 |

## 4. 자주 보는 "겉으로는 같은 메서드, 실제로는 다른 길" 사례

### case 1. full key를 일부만 쓰기 시작했다

원래는:

```sql
where coupon_id = ? and member_id = ? for update
```

바뀐 뒤:

```sql
where coupon_id = ? for update
```

business 문장상 비슷해 보여도, `(coupon_id, member_id)` 전체 key를 찌르던 query가 prefix range 쪽으로 흔들릴 수 있다.

### case 2. 화면용 정렬이 슬며시 섞였다

```sql
where coupon_id = ? and member_id = ?
order by created_at desc
for update
```

`FOR UPDATE`는 남아 있어도 optimizer가 다른 path를 고를 여지가 커진다.

### case 3. 함수가 index path를 흐렸다

```sql
where lower(email) = lower(?)
for update
```

메서드 이름은 여전히 "email로 잠금 조회"처럼 들리지만, plain equality index probe와는 다른 문제가 된다.

이 문서의 목적은 "이 경우마다 정답 설계"를 고르는 것이 아니라, **로그와 `EXPLAIN`을 같이 보면 drift를 빨리 잡을 수 있다**는 감각을 만드는 것이다.

## 5. beginner용 1분 검증 템플릿

실무 메모나 PR 설명에 아래 네 줄을 남기면 덜 흔들린다.

```text
Locking repository method: findByCouponIdAndMemberIdForUpdate
Logged SQL: ... where coupon_id=? and member_id=? for update
EXPLAIN: key=uq_coupon_member, type=ref, rows=1
Correctness backstop: UNIQUE(coupon_id, member_id)
```

이 메모의 장점은 세 층을 한 번에 남긴다는 점이다.

- application 의도: 어떤 repository 메서드인가
- SQL 관찰: 실제로 어떤 locking SQL이 나갔나
- DB 근거: 그 SQL이 어떤 index path를 탔나

## common confusion

- "`FOR UPDATE`가 로그에 보였으니 검증 끝이다"
  - 아니다. lock clause와 chosen index path는 다른 층이다.
- "메서드 이름이 그대로니 plan도 같을 것이다"
  - 아니다. JPQL, derived query, 정렬, 함수 추가만으로도 SQL shape가 달라진다.
- "`EXPLAIN`에서 인덱스를 썼으니 충분하다"
  - 아니다. intended index인지, full key path인지까지 봐야 한다.
- "`rows = 1`이면 correctness도 확보됐다"
  - 아니다. 마지막 중복 방지는 여전히 `UNIQUE` 같은 write-time constraint가 맡는다.
- "`EXPLAIN`이 lock 자체를 보여 준다"
  - 아니다. `EXPLAIN`은 access path를 보여 주고, lock verification은 그 path를 통해 간접 확인하는 것이다.

## 어디까지 확인하면 충분한가

beginner 기준 종료 조건은 생각보다 단순하다.

1. Hibernate 로그에서 내가 기대한 locking SQL이 실제로 찍혔다.
2. MySQL `EXPLAIN`에서 intended index path가 유지됐다.
3. correctness backstop이 `UNIQUE`나 다른 명시적 constraint로 분리돼 있다.

이 셋이 맞으면 "이 repository 메서드는 적어도 지금은 의도한 locking path로 보인다"라고 말할 수 있다.

그 이상인 deadlock 순서, range lock 해석, empty-result gap semantics는 다음 문서로 넘겨도 된다.

운영에서 실제 blocker query나 deadlock 상대 SQL까지 따라가야 한다면, 다음 단계는 [Hibernate Lock SQL Log to Deadlock Triage Bridge](./hibernate-lock-sql-log-to-deadlock-triage-bridge.md)다.

## 다음에 어디로 가면 좋은가

- `EXPLAIN`의 `key/type/rows`를 더 짧은 체크리스트로 보고 싶으면 [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- Spring/JPA의 `@Lock`과 MySQL locking read가 어떻게 이어지는지 보고 싶으면 [Spring/JPA Exact-Key Lock Mapping Guide](./spring-jpa-exact-key-lock-mapping-guide.md)
- exact-key가 아니라 range/empty-result 쪽이 궁금하면 [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md), [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- `EXPLAIN` 컬럼 자체가 아직 낯설면 [인덱스와 실행 계획](./index-and-explain.md)

## 한 줄 정리

locking repository 메서드를 검증할 때는 "`@Lock`을 붙였나"보다 "Hibernate 로그의 실제 SQL이 무엇이었고, 그 SQL을 MySQL `EXPLAIN`에 넣었을 때 intended index path가 유지되나"를 같이 보는 편이 beginner에게 가장 안전하다.
