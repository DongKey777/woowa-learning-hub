# SQL 조인과 쿼리 실행 순서

> 단순 SQL 문법을 넘어, DB가 쿼리를 어떻게 이해하는지 설명하기 위한 문서

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [JOIN의 기본 의미](#join의-기본-의미)
- [INNER / LEFT / RIGHT JOIN](#inner--left--right-join)
- [쿼리 실행 순서 감각](#쿼리-실행-순서-감각)
- [GROUP BY와 HAVING](#group-by와-having)
- [서브쿼리와 JOIN](#서브쿼리와-join)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

## 왜 중요한가

백엔드 개발자는 결국 여러 테이블에서 필요한 데이터를 조합해 읽어야 한다.

그래서 최소한

- JOIN이 왜 필요한지
- WHERE, GROUP BY, HAVING이 어떤 순서로 적용되는지
- 서브쿼리와 JOIN 중 언제 무엇을 더 읽기 좋게 쓸지

정도는 설명할 수 있어야 한다.

---

## JOIN의 기본 의미

JOIN은 **여러 테이블을 논리적으로 연결해서 읽는 것**이다.

예:

- `games`
- `pieces`

가 분리돼 있으면, 특정 게임의 기물 상태를 읽을 때 JOIN이 필요할 수 있다.

즉 JOIN은 단순 문법이 아니라 **분리된 데이터를 관계를 통해 다시 조합하는 과정**이다.

---

## INNER / LEFT / RIGHT JOIN

### INNER JOIN

- 양쪽에 모두 매칭되는 row만 가져온다

### LEFT JOIN

- 왼쪽 테이블 row는 유지하고, 오른쪽이 없으면 `NULL`

### RIGHT JOIN

- 오른쪽 테이블 row는 유지하고, 왼쪽이 없으면 `NULL`

실무에서는 보통 `INNER JOIN`, `LEFT JOIN`이 많이 쓰이고, `RIGHT JOIN`은 상대적으로 덜 자주 쓴다.

---

## 쿼리 실행 순서 감각

SQL을 작성하는 순서와 DB가 처리하는 논리 순서는 다르다.

보통 감각적으로는:

1. `FROM`
2. `JOIN`
3. `WHERE`
4. `GROUP BY`
5. `HAVING`
6. `SELECT`
7. `ORDER BY`
8. `LIMIT`

이 순서로 이해하면 좋다.

즉 `WHERE`는 그룹핑 이전, `HAVING`은 그룹핑 이후 조건이라는 점이 중요하다.

---

## GROUP BY와 HAVING

### `GROUP BY`

- 데이터를 그룹 단위로 묶음

### `HAVING`

- 그룹 결과에 조건을 건다

예를 들어 “팀별 평균 점수가 10 이상인 팀”을 찾고 싶다면 `HAVING`이 필요하다.

---

## 서브쿼리와 JOIN

둘 다 결과를 조합할 수 있지만 관점이 다르다.

### JOIN이 더 자연스러운 경우

- 테이블 간 관계가 명확할 때
- 결과를 한 번에 조합해서 읽고 싶을 때

### 서브쿼리가 더 자연스러운 경우

- 조건 자체를 먼저 계산하고 싶을 때
- 특정 집합을 미리 구해서 필터링하고 싶을 때

중요한 건 “무조건 JOIN이 빠르다”가 아니라 **읽기 쉬움과 실행 계획을 같이 봐야 한다**는 점이다.

---

## 시니어 관점 질문

- `LEFT JOIN` 후 `WHERE` 조건을 잘못 걸면 왜 사실상 `INNER JOIN`처럼 동작할 수 있는가?
- `GROUP BY` 쿼리가 느릴 때 어디부터 의심해야 하는가?
- 서브쿼리와 JOIN 중 무엇이 더 빠른지는 왜 단정할 수 없는가?
- SQL을 읽기 쉽게 쓰는 것과 DB가 실행하기 좋은 것은 항상 같은가?
