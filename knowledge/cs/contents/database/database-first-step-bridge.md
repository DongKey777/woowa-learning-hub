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

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: database first step bridge, database beginner bridge, transaction jdbc jpa mybatis index order, backend mission database first read, db 입문 순서, 트랜잭션 jdbc jpa mybatis 인덱스 순서, 백엔드 미션 데이터베이스 첫걸음, database beginner route, beginner database, 처음 배우는데 database first step bridge, spring 다음 database, controller 다음 save sql, request controller database flow, 처음 db 전에 spring, why save sql hidden

## 먼저 큰 그림

초급자에게는 용어 정의보다 "요청 1개가 DB를 다녀오는 실제 흐름"이 먼저다.

```text
요청 도착
  -> 트랜잭션 경계 안에서 SQL 실행 (commit/rollback)
  -> 애플리케이션 계층에서 JDBC/JPA/MyBatis 중 하나로 DB와 통신
  -> SQL이 많아지고 데이터가 커지면 인덱스로 조회 비용을 줄임
요청 완료
```

처음에는 아래 한 줄만 머리에 남겨도 충분하다.

- 트랜잭션은 "같이 성공/실패할 범위"
- JDBC/JPA/MyBatis는 "SQL이 어디서 만들어지고 실행되는지"
- 인덱스는 "왜 조회가 빠르거나 느린지"

오늘 딱 10분만 본다면 아래 순서로 끊어 읽으면 된다.

| 시간 | 먼저 답할 질문 | 열 문서 |
|---|---|---|
| 0~3분 | "실패하면 어디까지 같이 취소돼야 하지?" | [트랜잭션 기초](./transaction-basics.md) |
| 3~6분 | "`save()` 뒤에서 SQL은 누가 만들지?" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| 6~10분 | "느린 이유가 찾는 경로 문제인가?" | [인덱스 기초](./index-basics.md) |

## spring에서 넘어올 때 붙이는 사다리

network나 spring에서 막 내려온 초보자라면 먼저 이 사다리를 고정한다.

| 지금 막힌 말 | 바로 앞 문서 | 이 문서 다음 한 걸음 |
|---|---|---|
| "`브라우저 -> controller -> database` 전체 흐름이 처음이에요" | [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) -> [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [트랜잭션 기초](./transaction-basics.md) |
| "`save()`는 보이는데 SQL은 왜 안 보여요?" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`왜 SQL 전에 controller/service가 보여요?`" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | 이 문서의 `요청 1개를 세 렌즈로 나누기`부터 다시 본다 |

처음 읽을 때는 세 축을 한 번에 깊게 파지 말고, 요청 1개를 아래 세 질문으로만 끊어 읽으면 된다.

| 요청을 읽으며 바로 던질 질문 | 붙는 축 | 바로 이어질 문서 |
|---|---|---|
| "실패하면 어디까지 같이 되돌려야 하지?" | 트랜잭션 | [트랜잭션 기초](./transaction-basics.md) |
| "이 서비스에서 SQL은 어디서 만들어지지?" | 접근 기술 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "이 조회가 느린 이유가 찾는 경로 때문일까?" | 인덱스 | [인덱스 기초](./index-basics.md) |

## 요청 1개를 세 렌즈로 나누기

같은 요청을 세 렌즈로만 나눠 보면 더 덜 추상적이다.

| 같은 "주문 생성" 요청을 볼 때 | 초보자용 첫 질문 | 바로 볼 코드/문서 |
|---|---|---|
| 트랜잭션 렌즈 | "주문 저장과 재고 차감을 같이 rollback해야 하나?" | `@Transactional`, [트랜잭션 기초](./transaction-basics.md) |
| 접근 기술 렌즈 | "`save()` 뒤 SQL은 repository가 만들까, mapper가 만들까?" | `Repository`/`@Mapper`, [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| 인덱스 렌즈 | "`WHERE order_id = ?`가 느린 이유가 찾는 경로 때문일까?" | 조회 조건, [인덱스 기초](./index-basics.md) |

핵심은 같은 기능을 보더라도 질문을 한 번에 하나만 고르는 것이다.

- "같이 실패해야 하나?"를 묻는 순간에는 인덱스 얘기를 잠시 미룬다.
- "SQL이 어디 있지?"를 묻는 순간에는 동시성 용어를 잠시 미룬다.
- "왜 느리지?"를 묻는 순간에는 먼저 조회 조건과 인덱스부터 본다.

처음부터 세 문서를 다 외우려 하지 않아도 된다. 아래처럼 "질문 1개당 문서 1개"로 끊으면 훨씬 덜 헷갈린다.

| 지금 막힌 한 문장 | 먼저 열 문서 |
|---|---|
| "실패하면 어디까지 같이 취소돼야 하지?" | [트랜잭션 기초](./transaction-basics.md) |
| "`save()`는 보이는데 SQL은 어디 있지?" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "조회가 느린데 어디부터 봐야 하지?" | [인덱스 기초](./index-basics.md) |

이 순서를 지키면:

- 트랜잭션을 "실패 단위"로 먼저 이해하고
- JDBC/JPA/MyBatis를 "접근 방식 차이"로 이해하고
- 인덱스를 "성능 도구"로 이해하게 된다

## 이 문서를 펼치는 신호

아래 문장 중 하나가 떠오르면 이 브리지부터 시작하면 된다.

| 지금 드는 말 | 먼저 분리할 축 | 바로 이어질 문서 |
|---|---|---|
| "`@Transactional`은 있는데 왜 여전히 헷갈리지?" | 트랜잭션과 접근 기술이 섞인 상태 | [트랜잭션 기초](./transaction-basics.md), [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`save()`만 보이고 SQL은 안 보여" | 접근 기술 구분이 먼저 필요 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "쿼리 한 줄인데 왜 느린지 모르겠어" | 성능 축을 따로 떼어 봐야 함 | [인덱스 기초](./index-basics.md) |

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

초보자가 실제 리뷰 메모로 바꾸면 보통 이 정도면 충분하다.

- "이 로직은 주문 저장과 재고 차감을 같이 실패시키려는 의도인가요?"
- "이 프로젝트는 `save()` 뒤 SQL을 JPA가 만드는 구조인가요, mapper SQL을 직접 보는 구조인가요?"
- "조회가 느리다면 `order_id` 찾기 경로부터 확인해 볼까요?"

한 줄 점검 순서로 줄이면 이렇다.

1. 실패가 같이 묶여야 하나?
2. SQL이 코드 어디에서 만들어지나?
3. 느리다면 어떤 조건으로 찾고 있나?

## 자주 헷갈리는 지점

- "`@Transactional`을 붙였으니 성능도 자동으로 좋아진다" -> 트랜잭션은 정합성 도구이고, 성능은 쿼리/인덱스와 별개로 봐야 한다.
- "JPA를 쓰면 SQL을 몰라도 된다" -> SQL을 모르면 느린 쿼리와 인덱스 미스 원인을 찾기 어렵다.
- "인덱스는 많을수록 좋다" -> 읽기는 빨라질 수 있지만 쓰기 비용이 늘어난다.
- "순서는 아무거나 괜찮다" -> 초급자 학습에서는 `트랜잭션 -> 접근 기술 -> 인덱스` 순서가 가장 덜 흔들린다.
- "`Repository`라는 이름이 보이니 무조건 JPA다" -> 팀에 따라 JDBC repository, JPA repository, MyBatis mapper가 함께 있을 수 있으니 SQL 위치를 직접 확인한다.

## 안전한 다음 단계

- "`처음`이라 DB 앞단 handoff까지 같이 복습하고 싶으면 -> [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) -> [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) -> 이 문서 순서로 되돌아온다"
- commit/rollback은 이해되는데 동시성 오류가 헷갈리면 -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- JDBC/JPA/MyBatis 용어가 미션 코드에서 섞여 보이면 -> [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- 인덱스 추가 전후를 근거 있게 비교하고 싶으면 -> [인덱스와 실행 계획](./index-and-explain.md)
- 아직 어느 문서를 더 읽어야 할지 모르겠으면 -> 이 문서 맨 위 3단계 표로 돌아가서 "지금 막힌 질문 1개"만 다시 고른다

cross-category bridge:

- Spring `@Transactional` 동작 경계를 코드 레벨에서 확인하려면 [Spring @Transactional 기초](../spring/spring-transactional-basics.md)로 이어서 본다.

## 한 줄 정리

백엔드 미션 초반 DB 학습은 트랜잭션으로 실패 단위를 먼저 고정하고, JDBC/JPA/MyBatis로 코드 경로를 구분한 뒤, 인덱스로 조회 성능을 보는 3단계 순서가 가장 안전하다.
