# 미션 코드 독해용 DB 체크리스트

> 한 줄 요약: 리뷰 전에 5분만 써서 `트랜잭션 경계`, `접근 기술`, `인덱스` 3가지를 먼저 고정하면, DB 관련 PR 코멘트가 훨씬 덜 흔들린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [인덱스 기초](./index-basics.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: mission code reading db checklist, backend mission db review checklist, transaction boundary access technology index checklist, 미션 코드 독해 db 체크리스트, 리뷰 전 db 점검표, 트랜잭션 경계 접근기술 인덱스 5분, jpa jdbc mybatis 확인 순서, 초급 db 코드리뷰 체크리스트, repository mapper entity manager 확인, explain before review, transactional repository index beginner, mission code reading db checklist basics, mission code reading db checklist beginner, mission code reading db checklist intro, database basics

## 먼저 큰 그림

초급자 기준으로는 용어보다 이 순서가 먼저다.

```text
1. 이 기능은 어디까지 같이 commit/rollback되어야 하지?
2. 이 프로젝트는 DB에 어떤 방식으로 접근하지?
3. 자주 읽는 조건에 맞는 인덱스가 보이나?
```

코드리뷰 직전에는 이 3문항만 답해도 "트랜잭션 문제인지", "기술 스택 오해인지", "조회 성능 문제인지"를 크게 분리할 수 있다.

## 5분 체크 순서

| 시간 | 먼저 볼 곳 | 확인 질문 | 바로 남길 수 있는 리뷰 메모 |
|---|---|---|---|
| 1분 | service 메서드 | 이 작업은 어디까지 한 번에 성공/실패해야 하나? | `주문 저장`과 `재고 차감`이 한 경계인지 먼저 확인 필요 |
| 2분 | repository / mapper / SQL 호출부 | JPA, JDBC, MyBatis 중 무엇으로 DB에 접근하나? | 이 코드는 `JpaRepository` 기준으로 읽어야 함 / mapper SQL을 직접 봐야 함 |
| 2분 | 조회 조건과 schema/index | `WHERE`, `JOIN`, `ORDER BY`에 맞는 인덱스가 보이나? | `member_id + created_at` 축 인덱스 유무 확인 필요 |

핵심은 "모든 SQL을 해석"하는 게 아니라, **트랜잭션 경계 -> 접근 기술 -> 인덱스 축**으로 먼저 분류하는 것이다.

## 1. 트랜잭션 경계: 먼저 실패 단위를 본다

트랜잭션은 "이 변경들을 같이 성공시키고, 같이 되돌릴 범위"다.

처음 읽을 때는 `@Transactional` 유무만 보지 말고 아래 두 가지를 같이 본다.

- 어떤 service 메서드가 실제 진입점인가
- 그 안에서 DB write와 외부 I/O가 섞이는가

### 30초 질문

| 질문 | 예면 의미 | 첫 대응 |
|---|---|---|
| `save`, `update`, `delete`가 한 service 메서드 안에 몰려 있나 | 하나의 commit 경계일 가능성이 크다 | 그 묶음이 정말 같이 실패해야 하는지 본다 |
| `@Transactional` 안에서 HTTP, Redis, 메시지 발행을 기다리나 | 트랜잭션이 불필요하게 길어질 수 있다 | 외부 I/O 분리 가능성을 먼저 본다 |
| 같은 기능인데 service 둘 이상을 왔다 갔다 하나 | 실제 경계가 어디인지 흐릴 수 있다 | "최종 commit 소유자"가 누구인지 메모한다 |

### 작은 예시

```java
@Transactional
public void placeOrder(OrderCommand command) {
    orderRepository.save(order);
    stockRepository.decrease(command.productId(), command.quantity());
}
```

이 코드는 초급자 기준으로 이렇게 읽으면 충분하다.

- `주문 저장`과 `재고 차감`은 같이 commit/rollback될 가능성이 크다.
- 그래서 리뷰 포인트는 "이 둘을 왜 같이 묶었나"이지, `@Transactional` 문법 암기가 아니다.

반대로 아래는 바로 질문할 후보다.

```java
@Transactional
public void placeOrder(OrderCommand command) {
    orderRepository.save(order);
    paymentClient.approve(command.paymentKey());
    orderRepository.markPaid(order.getId());
}
```

- DB write 사이에 외부 호출 대기가 끼어 있다.
- 초급자 리뷰 메모는 "외부 I/O를 트랜잭션 밖으로 뺄 수 있는지" 정도면 충분하다.

이 축이 더 헷갈리면 [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md), [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md)로 이어서 보면 된다.

## 2. 접근 기술: 지금 무엇을 읽고 있는지 먼저 고정한다

같은 `Repository`라는 이름이 보여도 실제 접근 방식은 다를 수 있다.

| 보이는 단서 | 보통 의미 | 읽는 초점 |
|---|---|---|
| `JpaRepository`, `@Entity`, `findBy...` | JPA / Spring Data JPA | 메서드 이름, 엔티티 매핑, 지연 로딩 가능성 |
| `@Mapper`, XML mapper, `select ...` | MyBatis | 실제 SQL과 파라미터 바인딩 |
| `JdbcTemplate`, `NamedParameterJdbcTemplate` | JDBC 계열 | SQL 문자열과 row mapping |

초급자에게 중요한 것은 "어느 기술이 더 좋다"가 아니다.

- JPA면 엔티티와 repository 메서드를 먼저 본다.
- MyBatis면 mapper SQL을 먼저 본다.
- JDBC면 SQL과 파라미터 바인딩을 먼저 본다.

### 빠른 비교

| 질문 | JPA 쪽에서 먼저 볼 것 | MyBatis/JDBC 쪽에서 먼저 볼 것 |
|---|---|---|
| 조회 조건이 무엇인가 | repository 메서드명, `@Query` | SQL `WHERE` 절 |
| 어떤 테이블을 읽나 | 엔티티 매핑 | SQL `FROM` / `JOIN` |
| 성능 코멘트를 어디에 남기나 | 메서드 설계 + 생성 SQL 추정 | SQL 자체와 인덱스 축 |

### 흔한 오해

- "`Repository`면 다 JPA다" -> MyBatis mapper도 팀에 따라 repository처럼 부를 수 있다.
- "JPA니까 SQL은 안 봐도 된다" -> 성능이나 인덱스 얘기를 하려면 결국 SQL 축을 봐야 한다.
- "SQL이 보이니 무조건 JDBC다" -> MyBatis도 SQL을 직접 쓴다.

이 축이 아직 헷갈리면 [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)부터 다시 짧게 보고 오면 된다.

## 3. 인덱스: 조회 조건과 정렬 축이 맞는지만 본다

리뷰 전 2분 안에 인덱스를 완벽히 판단하려고 하면 오히려 흔들린다. 초급자는 아래 세 줄만 본다.

- 자주 보이는 `WHERE` 컬럼이 무엇인가
- `JOIN` 키가 무엇인가
- `ORDER BY`가 함께 붙는가

### 30초 질문

| 질문 | 예면 의미 | 첫 대응 |
|---|---|---|
| `findByMemberIdOrderByCreatedAtDesc` 같은 조회가 반복되나 | `member_id`, `created_at` 축 인덱스 후보 | 단일 인덱스 여러 개보다 복합 인덱스 순서를 먼저 떠올린다 |
| SQL에 `WHERE status = ? ORDER BY created_at DESC`가 보이나 | 필터와 정렬이 같이 있다 | 정렬까지 같이 받는 인덱스인지 확인한다 |
| PK 조회가 아닌데 테이블 전체를 뒤질 것처럼 보이나 | 풀스캔 가능성이 있다 | `EXPLAIN`이 필요하다는 메모를 남긴다 |

### 작은 예시

```sql
SELECT *
FROM orders
WHERE member_id = ?
ORDER BY created_at DESC
LIMIT 20;
```

이 쿼리를 처음 보면 초급자도 여기까지는 말할 수 있다.

- `member_id`로 먼저 좁히고
- 그 안에서 `created_at` 정렬이 붙는다
- 그래서 `member_id + created_at` 순서를 먼저 의심해 볼 수 있다

여기서 중요한 건 "정답 인덱스를 단정"하는 것이 아니라,
"리뷰 코멘트의 초점을 `이 조회 축에 맞는 인덱스가 있는지`로 좁히는 것"이다.

인덱스 감각을 더 보강하려면 [인덱스 기초](./index-basics.md), 실제 근거 확인은 [인덱스와 실행 계획](./index-and-explain.md)로 이어진다.

## 미션 코드에서 바로 쓰는 한 장 점검표

| 축 | 지금 바로 체크할 것 | 초급자용 한 줄 판단 |
|---|---|---|
| 트랜잭션 경계 | 어떤 service 메서드가 commit 소유자인가 | "무엇을 같이 실패시키나?" |
| 접근 기술 | JPA / MyBatis / JDBC 중 무엇인가 | "어느 파일을 기준으로 읽어야 하나?" |
| 인덱스 | `WHERE`, `JOIN`, `ORDER BY` 핵심 컬럼 | "이 조회 축에 맞는 인덱스가 보이나?" |

리뷰 문장을 짧게 쓰면 보통 이 정도면 된다.

- "이 로직의 실제 트랜잭션 경계가 어디인지 먼저 확인하고 싶습니다."
- "현재 JPA repository 기준으로 읽어야 하는지, mapper SQL 기준으로 읽어야 하는지 확인 부탁드립니다."
- "이 조회는 `member_id + created_at` 축 인덱스 유무를 같이 봐야 할 것 같습니다."

## common confusion

- "`@Transactional`만 보이면 DB 리뷰를 다 한 것 같다" -> 경계는 시작일 뿐이고, 실제 접근 기술과 조회 축을 같이 봐야 한다.
- "JPA면 인덱스 얘기는 나중 문제다" -> JPA도 결국 SQL과 인덱스 영향을 받는다.
- "인덱스는 DBA나 운영자가 나중에 보면 된다" -> 미션 코드 독해 단계에서도 `WHERE/JOIN/ORDER BY` 축 확인은 충분히 할 수 있다.
- "정답을 확신할 수 없으면 리뷰 코멘트를 못 남긴다" -> 초급자 리뷰는 단정보다 "어떤 축을 같이 확인해야 하는지"를 정확히 짚는 것이 더 중요하다.

## 안전한 다음 단계

- 트랜잭션 안 외부 I/O가 바로 보이면 -> [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md)
- `@Transactional` 동작 자체가 헷갈리면 -> [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md)
- JPA / JDBC / MyBatis 구분이 흐리면 -> [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- 인덱스 후보를 근거 있게 확인하고 싶으면 -> [인덱스와 실행 계획](./index-and-explain.md)

## 한 줄 정리

미션 코드 DB 리뷰의 첫 5분은 "`무엇을 같이 실패시키는가 -> 어떤 방식으로 DB에 접근하는가 -> 어떤 조회 축을 인덱스로 받는가`" 순서로 보면 가장 덜 흔들린다.
