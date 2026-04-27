# LEFT JOIN 필터 위치 입문서 (LEFT JOIN Filter Placement Primer)

> 한 줄 요약: `LEFT JOIN`에서 오른쪽 테이블 조건을 `WHERE`에 두면 `NULL` 행이 제거되어 결과가 `INNER JOIN`처럼 좁아질 수 있고, "오른쪽에서 어떤 행을 붙일지" 조건은 보통 `ON`에 두는 편이 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [SQL 조인 기초](./sql-join-basics.md)
- [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md)
- [기본 키와 외래 키 기초](./primary-foreign-key-basics.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: left join where on 차이, left join filter placement, left join inner join처럼 동작, right table predicate where clause, on clause vs where clause, left join null filter, sql left join beginner, outer join collapsed to inner join, 조인 필터 위치, 오른쪽 테이블 조건 어디에 쓰나, left join filter placement primer basics, left join filter placement primer beginner, left join filter placement primer intro, database basics, beginner database

## 핵심 개념

초보자에게 가장 쉬운 mental model은 이것이다.

- `ON`은 "오른쪽 테이블에서 **어떤 행을 붙일지**" 정한다.
- `WHERE`는 JOIN이 끝난 뒤 "**최종 결과에서 어떤 행을 남길지**" 정한다.

`LEFT JOIN`은 원래 왼쪽 테이블 행을 모두 남긴다. 그런데 오른쪽 테이블 조건을 `WHERE`에 두면, 오른쪽이 없어서 `NULL`인 행까지 같이 탈락할 수 있다. 그래서 결과가 체감상 `INNER JOIN`처럼 보인다.

## 먼저 그림으로 보기

```
customer
id | name
1  | Alice
2  | Bob
3  | Carol

orders
id | customer_id | status
10 | 1           | PAID
11 | 1           | CANCELED
12 | 2           | CANCELED
```

"모든 고객을 보여 주되, 주문이 있다면 `PAID` 주문만 붙이고 싶다"는 상황을 생각해 보자.

| 의도 | 안전한 위치 | 이유 |
|---|---|---|
| 오른쪽에서 어떤 주문을 붙일지 정한다 | `ON` | `LEFT JOIN`의 "왼쪽 유지" 성질을 보존한다 |
| 최종 결과에서 어떤 고객 자체를 제거할지 정한다 | `WHERE` | JOIN이 끝난 뒤 전체 결과를 거른다 |

## 예제 1. `WHERE`에 두면 왜 좁아지나

아래 쿼리는 많은 입문자가 처음에 쓰는 형태다.

```sql
SELECT c.id, c.name, o.id AS order_id, o.status
FROM customer c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'PAID';
```

겉보기 의도는 "`PAID` 주문만 보고 싶다"지만, 실제 결과는 더 좁다.

| customer | JOIN 직후 상태 | `WHERE o.status = 'PAID'` 이후 |
|---|---|---|
| Alice | `PAID`, `CANCELED` 두 row | `PAID` row만 남음 |
| Bob | `CANCELED` 한 row | 탈락 |
| Carol | 오른쪽이 없어 `NULL` 한 row | 탈락 |

결과적으로 Carol처럼 주문이 아예 없는 고객도 사라진다. `LEFT JOIN`을 썼지만 **오른쪽 조건을 `WHERE`가 다시 걸러 버렸기 때문**이다.

## 예제 2. `ON`에 두면 왼쪽 행이 유지된다

같은 의도를 `ON`에 옮기면 결과가 달라진다.

```sql
SELECT c.id, c.name, o.id AS order_id, o.status
FROM customer c
LEFT JOIN orders o
  ON o.customer_id = c.id
 AND o.status = 'PAID';
```

이 쿼리는 먼저 "`customer_id`가 맞고, 그중에서도 `PAID`인 주문만 오른쪽에서 붙여라"라고 말한다. 그래서 결과는 대략 이렇게 읽힌다.

| customer | 결과 |
|---|---|
| Alice | `PAID` 주문이 붙음 |
| Bob | 붙일 `PAID` 주문이 없으므로 오른쪽이 `NULL` |
| Carol | 원래 주문이 없으므로 오른쪽이 `NULL` |

이번에는 Bob과 Carol이 남아 있다. 이것이 `LEFT JOIN`을 기대한 초보자의 머릿속 결과와 더 가깝다.

## `ON`과 `WHERE`를 이렇게 구분하면 덜 헷갈린다

| 질문 | 주로 둘 위치 |
|---|---|
| "오른쪽 테이블에서 어떤 행을 매칭할까?" | `ON` |
| "JOIN이 끝난 최종 결과에서 어떤 행을 버릴까?" | `WHERE` |
| "오른쪽이 없는 왼쪽 행도 꼭 남겨야 하나?" | 그렇다면 오른쪽 조건을 먼저 `ON`부터 의심 |

짧게 기억하면 이렇다.

- 오른쪽 테이블 조건인데 왼쪽 행을 유지하고 싶다 → 먼저 `ON`
- 결과 전체를 줄이고 싶다 → `WHERE`

## 흔한 혼동 1. `LEFT JOIN`인데 왜 `INNER JOIN`처럼 보이나요?

`WHERE o.status = 'PAID'` 같은 조건은 `o.status`가 `NULL`인 row를 통과시키지 못한다. 주문이 없어서 `NULL`인 row, 또는 붙은 주문이 조건과 맞지 않는 row가 모두 탈락한다.

즉 문제는 DB가 `LEFT JOIN`을 `INNER JOIN`으로 바꿨다기보다, **JOIN 뒤의 필터가 결과를 INNER JOIN처럼 보이게 만든 것**에 가깝다.

## 흔한 혼동 2. 그럼 `WHERE`에 오른쪽 컬럼을 절대 쓰면 안 되나요?

그건 아니다. 아래처럼 **의도적으로** 오른쪽이 없는 행만 찾을 때는 `WHERE`가 맞다.

```sql
SELECT c.id, c.name
FROM customer c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.id IS NULL;
```

이 쿼리의 목적은 "주문이 없는 고객만 남기기"이므로, `WHERE`가 최종 필터 역할을 하는 것이 정확하다.

핵심은 "`WHERE`에 오른쪽 컬럼을 쓰면 안 된다"가 아니라, **그 조건이 왼쪽 행까지 탈락시켜도 되는지 먼저 생각해야 한다**는 점이다.

## 실무에서 자주 만나는 패턴

**패턴 1. 모든 부모를 보여 주되, 특정 조건의 자식만 붙이기**

```sql
SELECT m.id, m.name, p.id AS payment_id
FROM member m
LEFT JOIN payment p
  ON p.member_id = m.id
 AND p.status = 'COMPLETED';
```

멤버는 모두 보이되, 완료 결제만 붙인다.

**패턴 2. 자식이 있는 부모만 최종 결과에 남기기**

```sql
SELECT DISTINCT m.id, m.name
FROM member m
LEFT JOIN payment p ON p.member_id = m.id
WHERE p.status = 'COMPLETED';
```

이 경우는 실제로 "완료 결제가 있는 멤버만" 보고 싶은 것이므로, 결과가 `INNER JOIN`처럼 좁아져도 의도와 맞을 수 있다.

## 흔한 오해와 첫 대응

| 자주 하는 말 | 왜 헷갈리나 | 더 맞는 첫 대응 |
|---|---|---|
| "`LEFT JOIN`이면 왼쪽 row는 무조건 다 나온다" | 뒤에 `WHERE`가 다시 줄일 수 있다 | JOIN 뒤 필터까지 함께 읽는다 |
| "오른쪽 조건은 어디에 써도 비슷하다" | `ON`은 매칭 기준, `WHERE`는 최종 필터라 역할이 다르다 | 의도가 "붙일 자식 고르기"인지 먼저 말로 풀어 본다 |
| "결과가 줄었으니 옵티마이저가 JOIN을 바꿨다" | 대부분은 SQL 의미 자체가 그렇게 적혀 있다 | 먼저 `NULL` row가 `WHERE`에서 탈락했는지 본다 |

## 더 깊이 가려면

- JOIN 종류와 `NULL` 포함 범위를 먼저 다지려면 → [SQL 조인 기초](./sql-join-basics.md)
- `FROM` → `JOIN` → `WHERE` 순서 감각을 더 분명히 하려면 → [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)
- PK/FK와 1:N 관계 때문에 row가 왜 늘어나는지 함께 보려면 → [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md)

## 면접/시니어 질문 미리보기

> Q: `LEFT JOIN` 뒤에 오른쪽 테이블 조건을 `WHERE`에 두면 왜 결과가 줄어드나요?
> 의도: outer join의 의미와 필터 적용 지점을 구분하는지 확인
> 핵심: JOIN 후 생성된 `NULL` row까지 `WHERE`가 제거할 수 있어서, 왼쪽 전체 유지 효과가 사라질 수 있다.

> Q: 오른쪽 조건을 `ON`에 둘지 `WHERE`에 둘지 어떻게 판단하나요?
> 의도: 문법 암기가 아니라 의도 중심으로 설명할 수 있는지 확인
> 핵심: 오른쪽에서 어떤 행을 붙일지 정하는 조건은 `ON`, 최종 결과 자체를 걸러도 되는 조건은 `WHERE`가 기본 출발점이다.

## 한 줄 정리

`LEFT JOIN`에서 오른쪽 조건을 `WHERE`에 두면 `NULL` 행이 탈락해 결과가 좁아질 수 있다. "붙일 오른쪽 행 선택"은 `ON`, "최종 결과 필터"는 `WHERE`라고 먼저 나눠 생각하면 실수가 줄어든다.
