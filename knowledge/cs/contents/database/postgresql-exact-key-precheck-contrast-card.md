# PostgreSQL Exact-Key Pre-Check Contrast Card

> 한 줄 요약: PostgreSQL에서 `EXPLAIN`이 exact-key unique index probe처럼 보여도, 그것만으로 MySQL `REPEATABLE READ`의 gap/next-key queue 직관까지 따라온다고 읽으면 안 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: postgresql exact key precheck contrast, same explain not same lock behavior, explain confidence postgresql vs mysql, postgresql exact key no gap lock, postgres exact key pre check beginner, mysql next key vs postgres row lock, exact key explain portability, exact key probe portability card, why postgres explain is not mysql gap lock, postgresql unique probe no next key, empty result exact key postgres, exact key pre-check contrast card, explain good but no queue postgres, same explain different locking engine, postgresql absence check exact key

## 먼저 잡을 그림

초보자 기준으로는 아래 두 줄만 먼저 고정하면 된다.

- `EXPLAIN`은 "어느 인덱스 길로 갔는가"를 보여 준다.
- gap/next-key는 "그 길을 가면서 없는 자리 주변까지 잠그는가"를 말한다.

즉 `EXPLAIN` confidence와 lock behavior는 같은 층이 아니다.

> PostgreSQL에서 exact-key unique index probe가 보여도, 그것만으로 "같은 missing key insert를 줄 세운다"까지 결론 내리면 과장이다.

## 한눈에 비교

| 질문 | MySQL `REPEATABLE READ` exact-key probe | PostgreSQL exact-key probe |
|---|---|---|
| `EXPLAIN`에서 full unique-key path가 보이나 | 볼 수 있다 | 볼 수 있다 |
| 그 의미 | 같은 key slot을 실제로 찾고 있다는 강한 힌트 | 같은 unique index path를 탔다는 강한 힌트 |
| empty-result에서 같은 key insert를 앞단에서 잠깐 줄 세울 수 있나 | 때때로 그렇다. gap/next-key가 보조할 수 있다 | 보통 아니다. missing row 자체를 MySQL 식 next-key로 잠근다고 보면 안 된다 |
| final correctness backstop | `UNIQUE` | `UNIQUE` |
| absence/predicate까지 직렬화가 필요하면 | RR 보너스에 기대지 말고 별도 설계도 본다 | `SERIALIZABLE` + retry, constraint, guard surface를 먼저 본다 |

핵심 기억법:

- MySQL RR: "`좋은 EXPLAIN` + exact-key path"가 queueing 보조로 이어질 수 있다
- PostgreSQL: "`좋은 EXPLAIN`"은 path confidence일 뿐, MySQL식 gap/next-key 보조까지 뜻하지는 않는다

## 같은 `EXPLAIN`이어도 결론이 달라지는 이유

예를 들어 두 엔진 모두 아래 query가 있다고 하자.

```sql
SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR UPDATE;
```

그리고 둘 다 아래 인덱스를 가진다고 하자.

```sql
UNIQUE (coupon_id, member_id)
```

`EXPLAIN` 결과가 "정말 exact-key unique index probe를 탄다"는 confidence를 줄 수는 있다.
하지만 그 다음 해석은 엔진별로 갈린다.

- MySQL RR: 같은 ordered key slot 주변 gap/next-key가 보조적으로 남을 수 있다
- PostgreSQL: chosen unique index path를 탔더라도, `0 row`이면 잠근 row가 없다고 읽는 편이 안전하다

즉 둘 다 "`맞는 책꽂이의 같은 칸`"을 찾으러 갔다는 뜻일 수는 있어도,
"빈 칸 앞에서 뒤 사람을 세워 두는가"는 같은 답이 아니다.

## 초보자용 30초 판정 카드

| 지금 확인한 것 | PostgreSQL에서 바로 해도 되는 말 | PostgreSQL에서 아직 하면 안 되는 말 |
|---|---|---|
| `EXPLAIN`의 `key`가 intended unique index다 | "query path는 exact-key 쪽이다" | "그러니 MySQL RR처럼 missing key insert도 줄 선다" |
| `rows`가 `1` 근처다 | "넓은 range scan보다 한 칸 lookup에 가깝다" | "absence check가 잠금으로 보호된다" |
| `SELECT ... FOR UPDATE`가 `0 row`다 | "지금 잠글 existing row가 없을 수 있다" | "없는 key 자리를 예약했다" |
| PostgreSQL `SERIALIZABLE`을 쓴다 | "충돌 시 retry로 직렬화될 수 있다" | "`FOR UPDATE` empty result가 gap lock처럼 바뀐다" |

## 흔한 오해

- "`EXPLAIN`이 좋으니 PostgreSQL도 MySQL RR exact-key probe처럼 안전하다"
  - 아니다. `EXPLAIN`은 access path 근거이고, MySQL식 gap/next-key 동작 근거는 아니다.
- "`FOR UPDATE`인데 unique index도 탔으니 없는 row도 예약됐다"
  - PostgreSQL에서는 보통 이렇게 읽지 않는다.
- "그럼 `EXPLAIN`은 PostgreSQL에서 의미가 없나"
  - 아니다. exact-key path drift를 잡는 데는 여전히 중요하다. 다만 queueing 의미까지 덧붙이면 안 된다.
- "PostgreSQL에서 absence safety가 필요하면 `FOR UPDATE`만 더 세게 쓰면 되나"
  - 보통 아니다. `UNIQUE`, exclusion constraint, guard surface, `SERIALIZABLE` retry를 먼저 검토한다.

## 실무 메모 템플릿

PR이나 학습 메모에 아래처럼 적어 두면 초보자가 덜 헷갈린다.

```text
EXPLAIN confirms the exact-key unique-index path.
This does not imply MySQL-style gap/next-key queueing in PostgreSQL.
Correctness backstop: UNIQUE.
If absence itself must serialize, use PostgreSQL SERIALIZABLE + whole-transaction retry or another guard surface.
```

## 바로 이어서 볼 문서

- `EXPLAIN`을 어떤 선까지 믿어야 하는지 먼저 고정하려면 [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- MySQL RR에서 왜 같은 장면이 queue처럼 보이는지 비교하려면 [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- `0 row FOR UPDATE` 직관 자체를 엔진별로 나눠 보고 싶으면 [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- PostgreSQL에서 absence를 정말 직렬화해야 할 때의 기본 해법을 보려면 [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)

## 한 줄 정리

PostgreSQL에서 good `EXPLAIN`은 "exact-key path를 탔다"는 근거이지, MySQL `REPEATABLE READ`의 gap/next-key처럼 missing key insert를 앞단에서 줄 세운다는 근거는 아니다.
