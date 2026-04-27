# Result-row Explosion Debugging Checklist

> 한 줄 요약: JOIN 뒤 결과 row가 예상보다 많아졌다면, 먼저 "버그가 생겼다"보다 **어느 관계에서 몇 배가 붙는지, 지금 필요한 결과가 상세 row인지 요약 row인지, 유일하다고 믿은 값이 실제로도 유일한지**를 순서대로 확인해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [SQL 조인 기초](./sql-join-basics.md)
- [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md)
- [기본 키와 외래 키 기초](./primary-foreign-key-basics.md)
- [조인 테이블과 복합 키 기초](./join-table-composite-key-basics.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: result row explosion, duplicated rows after join, join duplicates checklist, sql duplicate rows debugging, join cardinality debugging, group by intent checklist, uniqueness assumption broken, one-to-many join duplicate, many-to-many row explosion, why join returns duplicates, sql row count suddenly increased, beginner join debugging, duplicate rows after left join, row multiplication after join, join result too many rows

## 핵심 개념

가장 먼저 잡아야 할 mental model은 이것이다. **JOIN은 row를 "합치는" 연산이 아니라, 조건에 맞는 row를 "붙이는" 연산이다.**

그래서 왼쪽 row 하나에 오른쪽 row가 3개 매칭되면, 결과는 "한 줄"이 아니라 **3줄**이 된다. 이건 DB가 틀린 것이 아니라 관계 cardinality를 그대로 보여준 것이다.

초급자가 디버깅할 때는 아래 세 질문을 먼저 던지면 된다.

- 이 JOIN은 원래 1:1이라고 생각했나, 실제로는 1:N인가?
- 지금 내가 원하는 결과는 상세 row인가, 아니면 회원별/주문별 같은 요약 row인가?
- "이 값은 유일할 것"이라고 믿었는데, DB 제약이나 실제 데이터가 그 믿음을 보장하나?

## 한눈에 보는 3단계 체크리스트

| 확인할 것 | 왜 보나 | 바로 하는 질문 |
|---|---|---|
| 1. cardinality | 어느 JOIN에서 row가 몇 배 늘었는지 찾기 위해 | "왼쪽 1개에 오른쪽 몇 개가 붙을 수 있지?" |
| 2. grouping intent | 상세 목록이 필요한데 요약을 기대했는지, 반대인지 구분하기 위해 | "결과 한 줄의 단위가 회원 1명인가, 주문 1건인가?" |
| 3. uniqueness assumption | email, code, status 같은 값이 실제 유일하지 않을 수 있어서 | "DB에 `PRIMARY KEY`/`UNIQUE`가 있나? 중복 데이터가 이미 있나?" |

## 예시로 먼저 보기

```sql
SELECT c.name, o.id, oi.product_id
FROM customer c
JOIN orders o ON o.customer_id = c.id
JOIN order_item oi ON oi.order_id = o.id
WHERE c.id = 10;
```

이 쿼리에서 `customer` 1명은 `orders` 여러 건을 가질 수 있고, 주문 1건은 `order_item` 여러 건을 가질 수 있다.

즉 row 증가는 자연스럽다.

- `customer -> orders` 에서 1:N
- `orders -> order_item` 에서 1:N
- 따라서 고객 1명의 결과가 `주문 수 x 주문별 상품 수`만큼 늘 수 있다

여기서 "고객이 한 줄만 나와야 하는데 중복됐다"고 느꼈다면, 사실은 중복이 아니라 **상세 row를 펼쳐 본 결과**일 가능성이 크다.

## 1. cardinality부터 확인한다

가장 흔한 원인은 잘못된 문법보다 **관계 cardinality를 잘못 가정한 것**이다.

| 관계 | JOIN 뒤 row 느낌 | 흔한 착각 |
|---|---|---|
| 1:1 | 거의 그대로 유지 | "항상 이럴 줄 알았다" |
| 1:N | 왼쪽 row가 자식 수만큼 반복 | "부모가 중복됐다" |
| N:M | 연결 테이블을 거치며 더 크게 늘 수 있음 | "JOIN이 이상하게 폭발했다" |

빠르게 확인하는 방법:

```sql
SELECT customer_id, COUNT(*)
FROM orders
GROUP BY customer_id
HAVING COUNT(*) > 1;
```

이런 식으로 "한 고객에 주문이 실제로 여러 개 있나?"를 먼저 본다.
생각은 1:1인데 데이터는 이미 1:N이면, JOIN 결과가 늘어나는 것은 정상이다.

조인 조건 자체가 약한 경우도 있다.

```sql
SELECT *
FROM orders o
JOIN payment p ON p.order_id = o.id;
```

이때 주문당 결제가 여러 row일 수 있다면 주문 row는 반복된다.
`payment` 쪽에서 "최신 결제 1건만" 붙이고 싶은데 그런 조건이 빠졌다면, JOIN은 가능한 모든 결제를 붙인다.

## 2. grouping intent를 분리한다

다음으로 확인할 것은 "무슨 단위의 결과를 원했는가"다.

- 주문 상세 목록이 필요하면 여러 row가 맞다
- 고객별 주문 수가 필요하면 여러 row를 다시 고객 단위로 묶어야 한다

예를 들어 고객별 주문 수를 원한다면 아래처럼 `GROUP BY`가 필요하다.

```sql
SELECT c.id, c.name, COUNT(o.id) AS order_count
FROM customer c
LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.name;
```

반대로 상세 주문 목록이 필요한데 `GROUP BY`로 억지로 줄이면 정보가 사라진다.
그래서 디버깅 때는 먼저 이렇게 말로 정리하는 것이 좋다.

- "결과 한 줄은 고객 1명인가?"
- "결과 한 줄은 주문 1건인가?"
- "결과 한 줄은 고객-주문-상품 조합 1건인가?"

이 단위가 정해지면 `GROUP BY`, `DISTINCT`, 서브쿼리, 집계 중 무엇이 맞는지도 훨씬 쉬워진다.

## 3. missing uniqueness assumption을 의심한다

초급자가 놓치기 쉬운 부분은 "내가 유일하다고 믿은 값"이 실제로는 유일하지 않을 수 있다는 점이다.

예를 들어 아래 JOIN은 겉보기엔 자연스럽다.

```sql
SELECT u.id, u.name, p.nickname
FROM users u
JOIN profiles p ON p.email = u.email;
```

하지만 `email`이 두 테이블에서 모두 진짜 유일하다는 보장이 없다면:

- 같은 `email` row가 여러 개 붙을 수 있고
- 결과 row가 예상보다 많아지며
- 문제 원인을 `GROUP BY`로 덮어 버리기 쉽다

먼저 확인할 것:

- 조인 키가 PK/FK인가?
- 아니면 단지 "중복이 없을 것 같은" 일반 컬럼인가?
- 그 컬럼에 `UNIQUE` 제약이 실제로 있나?
- 기존 데이터에 이미 중복 row가 들어간 적은 없나?

빠른 확인 예시:

```sql
SELECT email, COUNT(*)
FROM profiles
GROUP BY email
HAVING COUNT(*) > 1;
```

이 결과가 나오면 JOIN 버그라기보다 **모델링 또는 데이터 품질 문제**일 수 있다.

## 디버깅 순서 템플릿

1. 시작 테이블 기준으로 "원래 몇 row가 나와야 하는지" 먼저 센다.
2. JOIN을 하나씩 추가하며 어느 단계에서 row 수가 늘어나는지 본다.
3. 늘어난 JOIN에서 관계가 1:1인지 1:N인지 다시 확인한다.
4. 결과 단위가 상세인지 요약인지 정하고, 요약이면 `GROUP BY` 또는 사전 집계를 검토한다.
5. 조인 키가 PK/FK/UNIQUE로 보장되는지 확인한다.
6. 중복 데이터가 있으면 `DISTINCT`로 가리기 전에 제약과 데이터 정합성을 먼저 본다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "JOIN이 row를 중복 생성했다" | 대개는 1:N 관계를 펼쳐 보여준 것이다 | 먼저 cardinality를 본다 |
| "`DISTINCT` 붙이면 해결됐다" | 증상만 숨기고 왜 중복됐는지 놓칠 수 있다 | 왜 여러 row가 생겼는지 먼저 설명한다 |
| "`GROUP BY id` 하면 한 줄로 줄일 수 있다" | 나머지 컬럼 의미가 깨지거나 비결정적 결과가 될 수 있다 | 결과 한 줄의 단위를 먼저 정의한다 |
| "email로 JOIN해도 되겠지" | UNIQUE 제약이 없으면 같은 email 여러 row가 붙을 수 있다 | PK/FK 또는 실제 유일 제약 여부를 확인한다 |

## 자주 쓰는 대응 방식

| 상황 | 더 맞는 대응 |
|---|---|
| 부모 1건당 자식 최신 1건만 필요 | 자식 테이블을 먼저 최신 1건으로 줄인 뒤 JOIN |
| 고객별 주문 수처럼 요약 결과가 필요 | `GROUP BY`로 결과 단위를 명시 |
| 같은 연결 자체가 중복 저장됨 | `PRIMARY KEY`/`UNIQUE` 제약을 점검 |
| 원인 파악 전 임시로 결과만 줄이고 싶음 | `DISTINCT`는 임시 확인용으로만 보고, 근본 원인을 따로 찾기 |

## 더 깊이 가려면

- JOIN 종류와 1:N에서 row가 왜 늘어나는지 다시 정리하려면 → [SQL 조인 기초](./sql-join-basics.md)
- `GROUP BY`, `HAVING`, 결과 단위 요약을 다시 보려면 → [SQL 집계 함수와 GROUP BY 기초](./sql-aggregate-groupby-basics.md)
- PK/FK, 관계 cardinality, 모델링 읽기 흐름을 먼저 잡으려면 → [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md)
- 조인 키 유일성, PK/FK 기본기를 다시 보려면 → [기본 키와 외래 키 기초](./primary-foreign-key-basics.md)
- N:M 연결 테이블에서 중복 연결을 어떻게 막는지 보려면 → [조인 테이블과 복합 키 기초](./join-table-composite-key-basics.md)

## 면접/시니어 질문 미리보기

> Q: JOIN 뒤 row 수가 예상보다 많아졌을 때 가장 먼저 무엇을 확인하시겠어요?
> 의도: 증상과 관계 cardinality를 연결해서 설명할 수 있는지 확인
> 핵심: 어느 JOIN에서 1:N 또는 N:M이 생겼는지, 즉 row가 몇 배로 늘 수 있는 구조인지 먼저 본다.

> Q: `DISTINCT`로 줄어들면 문제 해결 아닌가요?
> 의도: 증상 완화와 원인 해결을 구분하는지 확인
> 핵심: `DISTINCT`는 보여 주는 결과만 줄일 수 있다. 잘못된 조인 키, 빠진 유일성 제약, 잘못된 결과 단위는 그대로 남는다.

> Q: "중복 row"와 "상세 row가 여러 줄인 정상 결과"는 어떻게 구분하나요?
> 의도: grouping intent를 설명할 수 있는지 확인
> 핵심: 결과 한 줄의 단위를 먼저 정한다. 고객 1명 단위 요약을 기대했는데 고객-주문-상품 상세를 펼쳐 놓았다면 중복이 아니라 결과 단위가 다른 것이다.

## 한 줄 정리

JOIN 뒤 row가 폭발하면, 먼저 cardinality로 "왜 여러 줄이 붙는지"를 설명하고, 다음에 grouping intent로 "원하는 한 줄의 단위"를 정한 뒤, 마지막으로 조인 키의 실제 유일성 보장을 확인하는 순서로 디버깅하면 된다.
