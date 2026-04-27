# Database First-Step Bridge

> 한 줄 요약: 백엔드 미션 초반 DB 학습은 `트랜잭션 기본 감각 -> JDBC/JPA/MyBatis 역할 구분 -> 인덱스 기본 감각` 순서로 잡아야, 코드와 SQL을 같이 볼 때 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [미션 코드 독해용 DB 체크리스트](./mission-code-reading-db-checklist.md)
- [트랜잭션 기초](./transaction-basics.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [인덱스 기초](./index-basics.md)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: database first step bridge, database beginner bridge, transaction jdbc jpa mybatis index order, backend mission database first read, db 입문 순서, 트랜잭션 jdbc jpa mybatis 인덱스 순서, 백엔드 미션 데이터베이스 첫걸음, database starter route, database beginner route

## 먼저 큰 그림

초급자에게는 용어 정의보다 "요청 1개가 DB를 다녀오는 실제 흐름"이 먼저다.

```text
요청 도착
  -> 트랜잭션 경계 안에서 SQL 실행 (commit/rollback)
  -> 애플리케이션 계층에서 JDBC/JPA/MyBatis 중 하나로 DB와 통신
  -> SQL이 많아지고 데이터가 커지면 인덱스로 조회 비용을 줄임
요청 완료
```

이 순서를 지키면:

- 트랜잭션을 "실패 단위"로 먼저 이해하고
- JDBC/JPA/MyBatis를 "접근 방식 차이"로 이해하고
- 인덱스를 "성능 도구"로 이해하게 된다

## 백엔드 미션용 3단계 순서

| 순서 | 먼저 답할 질문 | 우선 문서 | 바로 다음 한 걸음 |
|---|---|---|---|
| 1. 트랜잭션 기본 | 무엇을 같이 성공/실패시킬까? | [트랜잭션 기초](./transaction-basics.md) | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| 2. 접근 기술 기본 | 지금 코드가 JDBC/JPA/MyBatis 중 무엇을 쓰고 있나? | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 현재 미션 코드에서 repository/mapper가 어느 경로인지 확인 |
| 3. 인덱스 기본 | 왜 특정 조회가 느리고 어떤 컬럼을 먼저 볼까? | [인덱스 기초](./index-basics.md) | [인덱스와 실행 계획](./index-and-explain.md)에서 `EXPLAIN` 시작 |

핵심은 "1단계를 건너뛰고 2~3단계로 바로 가지 않는다"다.

리뷰 직전 5분 점검이 먼저 필요하면:

- [미션 코드 독해용 DB 체크리스트](./mission-code-reading-db-checklist.md)에서 `트랜잭션 경계 -> 접근 기술 -> 인덱스` 3축만 먼저 고정한다.

## 짧은 예시: 주문 생성 미션에서의 적용

상황: `주문 저장 + 재고 차감 + 주문 조회 API`가 한 미션에 같이 있다.

1. 트랜잭션 관점:
`주문 저장`과 `재고 차감`은 보통 함께 commit/rollback되어야 한다.

2. 접근 기술 관점:
팀 코드가 JPA라면 repository 메서드 기준으로 경계를 보고, MyBatis라면 mapper SQL 기준으로 경계를 본다.

3. 인덱스 관점:
`주문 상세 조회(order_id)`가 느리면 먼저 `order_id` 인덱스 유무와 실행 계획을 본다.

이렇게 보면 "왜 rollback됐는지", "어느 계층 코드를 봐야 하는지", "왜 느린지"를 한 번에 분리할 수 있다.

## 자주 헷갈리는 지점

- "`@Transactional`을 붙였으니 성능도 자동으로 좋아진다" -> 트랜잭션은 정합성 도구이고, 성능은 쿼리/인덱스와 별개로 봐야 한다.
- "JPA를 쓰면 SQL을 몰라도 된다" -> SQL을 모르면 느린 쿼리와 인덱스 미스 원인을 찾기 어렵다.
- "인덱스는 많을수록 좋다" -> 읽기는 빨라질 수 있지만 쓰기 비용이 늘어난다.
- "순서는 아무거나 괜찮다" -> 초급자 학습에서는 `트랜잭션 -> 접근 기술 -> 인덱스` 순서가 가장 덜 흔들린다.

## 안전한 다음 단계

- commit/rollback은 이해되는데 동시성 오류가 헷갈리면 -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- JDBC/JPA/MyBatis 용어가 미션 코드에서 섞여 보이면 -> [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- 인덱스 추가 전후를 근거 있게 비교하고 싶으면 -> [인덱스와 실행 계획](./index-and-explain.md)

cross-category bridge:

- Spring `@Transactional` 동작 경계를 코드 레벨에서 확인하려면 [Spring @Transactional 기초](../spring/spring-transactional-basics.md)로 이어서 본다.

## 한 줄 정리

백엔드 미션 초반 DB 학습은 트랜잭션으로 실패 단위를 먼저 고정하고, JDBC/JPA/MyBatis로 코드 경로를 구분한 뒤, 인덱스로 조회 성능을 보는 3단계 순서가 가장 안전하다.
