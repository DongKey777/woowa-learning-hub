# Spring/JPA Exact-Key Lock Mapping Guide

> 한 줄 요약: Spring/JPA의 `PESSIMISTIC_WRITE`와 `PESSIMISTIC_READ`는 대체로 MySQL `FOR UPDATE`와 `FOR SHARE`로 내려가지만, RR next-key가 exact-key queue처럼 보이는 장면은 **락 모드**보다 **chosen index path**가 유지될 때만 성립한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Hibernate SQL Log + EXPLAIN Lock Verification Primer](./hibernate-sql-log-explain-lock-verification-primer.md)
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)
- [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md)
- [Spring 트랜잭션 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring jpa exact key lock, spring data jpa for update mysql exact key, jpa pessimistic write mysql next key, hibernate for share mysql, exact key probe spring repository, why jpa lock lost index path, derived query lock mysql beginner, jpa lower email for update problem, same repository method different sql path, spring duplicate check rr next key, jpa exact key basics, 왜 jpa 락인데 중복이 생겨요, spring jpa exact key lock mapping guide basics, spring jpa exact key lock mapping guide beginner, spring jpa exact key lock mapping guide intro

## 핵심 개념

이 주제는 세 층을 분리해서 보면 덜 헷갈린다.

- Spring/JPA는 "`이 조회를 locking read로 보내라`"는 **락 모드**를 고른다
- Hibernate/MySQL dialect는 그 요청을 대체로 `FOR UPDATE`나 `FOR SHARE` 같은 **SQL 모양**으로 바꾼다
- InnoDB는 그 SQL이 실제로 탄 **인덱스 경로**를 따라 record/gap/next-key를 잠근다

즉 `@Lock(PESSIMISTIC_WRITE)`는 "이 business 조건 전체를 잠가라"는 계약이 아니다.
입문자용 기억법은 한 줄이면 된다.

> JPA는 lock clause를 고르고, MySQL은 access path를 고른다.

그래서 RR에서 exact-key queue처럼 보이던 장면도, repository 코드가 살짝 바뀌어 chosen index path가 흔들리면 바로 깨질 수 있다.

## 한눈에 보기

| Spring/JPA에서 보이는 것 | MySQL에서 대략 내려가는 SQL | exact-key probe처럼 읽기 쉬운 장면 | 조용히 흔들리는 지점 |
|---|---|---|---|
| `@Lock(PESSIMISTIC_WRITE)` + entity 조회 | `... FOR UPDATE` | full-key equality + matching `UNIQUE`/composite index + RR | 함수, join, 정렬, 다른 인덱스 선택 |
| `@Lock(PESSIMISTIC_READ)` + entity 조회 | `... FOR SHARE` 또는 구버전 `LOCK IN SHARE MODE` | exact-key duplicate pre-check를 reader 쪽에서 좁게 볼 때 | `FOR UPDATE`보다 약해서가 아니라 path가 달라져서 깨짐 |
| `entityManager.find(..., PESSIMISTIC_WRITE)` | `where pk = ? for update` | PK exact-key lock | business key duplicate check와는 다른 surface |
| 같은 repository 이름, 다른 JPQL/derived query | lock clause는 남을 수 있음 | 겉보기엔 "같은 락"처럼 보임 | 실제로는 다른 slot/range/table을 더듬고 있을 수 있음 |

핵심은 "`락 모드 이름`"보다 "`정말로 어떤 인덱스 칸을 읽었는가`"다.

## exact-key로 맞는 경우

### 1. 가장 좁게 exact-key가 맞는 경우

아래처럼 full key를 그대로 조회하면 Spring/JPA의 의도와 MySQL의 exact-key 장면이 가장 잘 맞는다.

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

dialect가 지원하면 SQL은 대략 이렇게 내려간다.

```sql
select coupon_id, member_id, status
  from coupon_issue
 where coupon_id = ?
   and member_id = ?
 for update;
```

`UNIQUE(coupon_id, member_id)`가 있고 MySQL `REPEATABLE READ`라면, 이 조회는 absent key 주변 slot을 exact-key probe처럼 건드릴 수 있다.
다만 correctness backstop은 여전히 `UNIQUE`다. `FOR UPDATE`가 uniqueness를 대신하지는 않는다.

### 2. `PESSIMISTIC_READ`도 "다른 버튼"이지 "다른 길"은 아니다

reader 쪽 잠금은 보통 아래처럼 보인다.

```java
@Lock(LockModeType.PESSIMISTIC_READ)
Optional<CouponIssue> findByCouponIdAndMemberId(Long couponId, Long memberId);
```

MySQL 8 계열에서는 대략 `FOR SHARE`, 더 오래된 표현으로는 `LOCK IN SHARE MODE`가 붙는다.

중요한 점은 empty-result exact-key 장면에서 `FOR UPDATE`와 `FOR SHARE`의 차이를 과장하지 않는 것이다.

- 둘 다 locking read다
- 둘 다 chosen index path를 따라 잠금이 남는다
- `0 row`일 때는 "강한 락 버튼"보다 "같은 key slot을 정말 탔는가"가 더 중요하다

즉 `PESSIMISTIC_WRITE`로 바꾸면 자동으로 predicate-safe해진다고 보면 틀리기 쉽다.

## ORM에서 흔들리는 경우

### 3. ORM 층에서 exact-key 가정을 잃는 흔한 패턴

겉보기 business 문장은 비슷해도 아래 변화가 생기면 exact-key 직관이 흔들린다.

- 함수가 끼어든다: `lower(ci.email) = lower(:email)`은 plain exact-key index probe와 다르다
- full key를 덜 쓴다: `(coupon_id, member_id)` 인덱스인데 `coupon_id`만 조건에 쓰면 range에 가까워진다
- join/정렬이 붙는다: `join member`, `order by createdAt desc`, `findTop1...OrderBy...`는 optimizer가 다른 길을 고르기 쉽다
- shared method가 커진다: 원래는 duplicate pre-check 전용이던 repository 메서드가 화면 조회와 공용화되면 query shape가 달라진다

이때 코드 리뷰에서는 "`@Lock`이 있으니 같은 lock"처럼 보이지만, InnoDB 입장에서는 아예 다른 index path일 수 있다.

## 흔한 오해와 함정

- "`@Lock(PESSIMISTIC_WRITE)`면 조건 전체가 잠긴다"
  - 아니다. 보통은 `FOR UPDATE`가 붙은 조회가 실제로 읽은 경로만 잠근다.
- "repository 메서드 이름이 비슷하면 exact-key 가정도 유지된다"
  - 아니다. JPQL 함수, join, `order by`, derived query 변경만으로도 path가 달라질 수 있다.
- "`FOR UPDATE`가 `FOR SHARE`보다 무조건 더 안전하다"
  - empty-result exact-key에서는 락 세기보다 matching index path가 더 중요하다.
- "RR 테스트에서 한 번 대기열이 보였으니 앞으로도 계속 그렇다"
  - 아니다. RC 전환, 인덱스 변경, optimizer plan drift, query refactor가 오면 바로 깨질 수 있다.

## 실무에서 쓰는 모습

Spring/JPA에서 exact duplicate path를 다룰 때는 보통 이 순서가 가장 덜 흔들린다.

1. `UNIQUE`로 correctness를 먼저 닫는다.
2. exact-key pre-check가 필요하면 **전용 repository 메서드**를 둔다.
3. 그 메서드는 full-key equality, 불필요한 함수/정렬/조인을 피한 짧은 query shape로 유지한다.
4. query를 고쳤다면 Hibernate SQL 로그와 `EXPLAIN`을 같이 본다.
5. 애플리케이션에서는 `duplicate key`와 `lock timeout/deadlock`을 다른 failure로 분리한다.

짧게 말해, exact-key pre-check는 "`보조 queue`"로 두고, 진짜 중복 차단은 `UNIQUE`, 진짜 검증은 SQL/plan 확인으로 가져가는 편이 안전하다.

## 더 깊이 가려면

- RR exact-key slot 직관부터 먼저 잡으려면 [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- Hibernate 로그에서 실제 SQL을 뽑아 `EXPLAIN`으로 이어 붙이는 beginner 절차가 필요하면 [Hibernate SQL Log + EXPLAIN Lock Verification Primer](./hibernate-sql-log-explain-lock-verification-primer.md)
- `EXPLAIN`에서 intended full unique-key path를 정말 탔는지 30초 체크로 보고 싶다면 [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- Spring service/retry 경계까지 같이 보려면 [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)
- `0 row FOR UPDATE`가 왜 predicate lock이 아닌지 보려면 [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md)
- Spring annotation과 transaction 경계 primer가 필요하면 [Spring 트랜잭션 기초](../spring/spring-transactional-basics.md)

## 면접/시니어 질문 미리보기

> Q. `@Lock(PESSIMISTIC_WRITE)`를 붙였는데 왜 exact-key safe라고 단정하면 안 되나요?
> 의도: lock mode와 chosen index path를 분리해서 설명하는지 확인
> 핵심: JPA는 `FOR UPDATE` 같은 lock clause를 만들 뿐이고, InnoDB가 실제로 잠그는 표면은 optimizer가 고른 index path이기 때문이다.

> Q. RR에서 잘 버티던 duplicate pre-check가 query refactor 뒤 왜 흔들릴 수 있나요?
> 의도: ORM 코드 변화가 physical probe shape를 바꾼다는 점을 아는지 확인
> 핵심: 함수, join, `order by`, incomplete key 조건이 들어오면 exact-key slot 대신 다른 range/scan path를 탈 수 있기 때문이다.

> Q. 그러면 Spring/JPA exact-key path의 마지막 안전장치는 뭔가요?
> 의도: queueing과 correctness backstop을 구분하는지 확인
> 핵심: 대기열처럼 보이는 RR next-key가 아니라 `UNIQUE` 같은 write-time constraint다.

## 한 줄 정리

Spring/JPA의 pessimistic lock은 MySQL locking read로 내려가지만, RR exact-key 효과는 "`락 버튼`"이 아니라 "`같은 인덱스 칸을 읽는 query shape`"가 유지될 때만 살아남고, 최종 중복 안전성은 결국 `UNIQUE`가 책임진다.
