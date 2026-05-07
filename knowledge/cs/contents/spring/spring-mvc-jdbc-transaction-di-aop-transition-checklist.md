---
schema_version: 3
title: Spring MVC to JDBC Transaction DI AOP Transition Checklist
concept_id: spring/mvc-jdbc-transaction-di-aop-transition-checklist
canonical: true
category: spring
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 76
review_feedback_tags:
- mvc-jdbc-transaction
- di-aop-transition
- controller-service-repository
- mental-model
aliases:
- MVC JDBC transaction DI AOP transition
- controller service repository mental model
- request is not transaction
- service owns transaction boundary
- Spring proxy before deep dive
- 초급 Spring 전환 체크리스트
intents:
- definition
- design
- mission_bridge
linked_paths:
- contents/spring/spring-request-pipeline-bean-container-foundations-primer.md
- contents/spring/spring-mvc-controller-basics.md
- contents/database/database-first-step-bridge.md
- contents/database/jdbc-jpa-mybatis-basics.md
- contents/database/transaction-basics.md
- contents/database/transaction-isolation-basics.md
- contents/spring/spring-ioc-di-basics.md
- contents/spring/spring-aop-basics.md
- contents/spring/spring-transactional-basics.md
- contents/spring/spring-self-invocation-transactional-only-misconception-primer.md
mission_ids:
- missions/roomescape
- missions/shopping-cart
confusable_with:
- spring/request-pipeline-bean-container
- spring/mvc-controller-basics
- database/database-first-step-bridge
- database/jdbc-jpa-mybatis-basics
- spring/ioc-di-basics
expected_queries:
- Spring MVC에서 JDBC 트랜잭션 DI AOP로 넘어갈 때 무엇부터 봐야 해?
- 요청 처리와 트랜잭션 경계는 어떻게 분리해서 이해해야 해?
- controller service repository 구조에서 DB 작업 책임은 어디에 둬야 해?
- @Transactional 프록시 deep dive 전에 알아야 할 초급 체크리스트는?
contextual_chunk_prefix: |
  이 문서는 Spring 초급자가 MVC 요청 처리, JDBC/트랜잭션, DI/AOP 프록시를 한 번에
  섞어 오진하는 상황을 줄이기 위한 bridge다. 컨트롤러는 HTTP 변환, 서비스는 유스케이스와
  트랜잭션 경계, 리포지토리는 DB 접근 책임이라는 분리 기준을 설명한다.
---
# Spring MVC -> JDBC/트랜잭션 -> DI/AOP 전환 오해 체크리스트

> 한 줄 요약: MVC에서 JDBC/트랜잭션으로, 다시 DI/AOP로 넘어갈 때는 "요청 처리", "DB 작업", "경계", "프록시"를 한 칸씩 분리해서 봐야 초반 deep dive 오진입을 줄일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network -> Spring handoff](../network/README.md#network---spring-handoff)
- [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md)
- [Database First-Step Bridge](../database/database-first-step-bridge.md)
- [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)
- [트랜잭션 기초](../database/transaction-basics.md)
- [트랜잭션 격리 수준 기초](../database/transaction-isolation-basics.md)
- [IoC와 DI 기초](./spring-ioc-di-basics.md)
- [AOP 기초](./spring-aop-basics.md)
- [@Transactional 기초](./spring-transactional-basics.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)
- [spring 카테고리 인덱스](./README.md)
- [spring primer 되돌아가기](./README.md#spring-primer-되돌아가기)

retrieval-anchor-keywords: mvc jdbc transaction di aop transition checklist, mvc jdbc di aop beginner bridge, mvc to jdbc confusion checklist, jdbc to di aop confusion checklist, controller service repository mental model, @transactional is aop beginner, transaction is not jdbc call, request is not transaction, service owns transaction boundary beginner, proxy before deep dive, beginner spring ladder transition, mvc jdbc transaction di aop ladder, beginner handoff ladder, 처음 spring jdbc transaction, 왜 service 에서 transaction

## 먼저 한 줄 mental model

지금 이 전환은 "새 기능이 계속 추가된다"가 아니라, **서로 다른 질문을 단계별로 분리해서 배우는 과정**이다.

- MVC: 요청이 어디로 들어오나
- JDBC/Repository: DB에 어떻게 말 거나
- Transaction: 어디까지 한 덩어리로 성공/실패하나
- DI/AOP: 객체를 누가 연결하고, 호출 사이에 누가 끼어드나

## beginner-safe 사다리

이 체크리스트는 `network primer -> spring bridge -> database bridge` 뒤에 붙는 정리용 bridge다. 처음에는 아래 한 칸 사다리만 유지하고, deep dive 단어는 링크만 저장한다.

| 지금 막힌 beginner 문장 | primer | follow-up 한 칸 | deeper는 나중에 |
|---|---|---|---|
| "`HTTP 다음에 Spring은 뭐부터 봐요?`" | [Network -> Spring handoff](../network/README.md#network---spring-handoff) | [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md) | filter ordering, async timeout |
| "`controller` 다음 `save()`와 SQL은 어디서 봐요?" | [Database First-Step Bridge](../database/database-first-step-bridge.md) | [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) | ORM flush, failover, replay |
| "`왜 service에서 transaction을 봐요?`" | [트랜잭션 기초](../database/transaction-basics.md) | [@Transactional 기초](./spring-transactional-basics.md) | propagation, self-invocation, rollback-only |
| "`Bean`, `주입`, `프록시`가 한꺼번에 섞여 보여요" | [IoC와 DI 기초](./spring-ioc-di-basics.md) | [AOP 기초](./spring-aop-basics.md) | proxy internals |

짧게 외우면 `요청 처리 -> DB 호출 -> 트랜잭션 경계 -> 프록시` 순서다.

## mental model 4칸

처음에는 용어보다 아래 4칸만 고정하면 된다.

| 칸 | 지금 보는 역할 | 한 줄 기억 |
|---|---|---|
| MVC | HTTP 요청을 받아 controller/service로 넘긴다 | "웹 요청을 어디로 보낼지"를 다룬다 |
| JDBC / Repository | DB에 SQL을 보내고 결과를 받는다 | "데이터를 어떻게 읽고 쓰는지"를 다룬다 |
| Transaction | 여러 DB 작업을 한 덩어리로 묶는다 | "어디까지 같이 commit/rollback할지"를 다룬다 |
| DI / AOP | 객체를 연결하고, 필요한 기능을 바깥에서 감싼다 | "누가 누구를 주입받고, 누가 중간에 끼어드는지"를 다룬다 |

## 30초 체크: 지금 어느 칸에서 막혔나

| 지금 드는 생각 | 실제로 먼저 봐야 하는 칸 |
|---|---|
| "`Controller`에서 DB까지 바로 한 번에 이어지는 것 같다" | MVC vs Service/Repository 분리 |
| SQL 한 번 실행했으니 트랜잭션도 끝난 것 같다 | JDBC 호출 vs Transaction 경계 분리 |
| `@Transactional`은 DB 기능 같고 Spring은 부가 기능 같다 | Transaction 개념 vs AOP 적용 방식 분리 |
| annotation만 붙였는데 왜 안 먹지 싶다 | DI/AOP 프록시 경로 |

## 잘못된 점프부터 막기

초급자에게 자주 나오는 위험한 점프는 아래 3가지다.

| 바로 내려가고 싶은 주제 | 지금 멈추고 먼저 확인할 것 |
|---|---|
| `REQUIRES_NEW`, propagation | "애초에 transaction boundary를 service 기준으로 보고 있는가?" |
| isolation / lock / deadlock | "지금 막힌 게 SQL 실행 자체인지, commit/rollback 경계인지?" |
| self-invocation / proxy internals | "`@Transactional`이 DB 옵션이 아니라 proxy 적용 결과라는 점을 이미 분리했는가?" |

## 전환 1: MVC -> JDBC/트랜잭션에서 자주 헷갈리는 것

먼저 이렇게 기억하면 된다.

- controller는 "요청을 받는 입구"다.
- repository/JDBC는 "DB에 말 거는 손"이다.
- transaction은 "여기서부터 여기까지 같이 성공/실패"라는 경계다.

즉, **HTTP 요청 1개 = 트랜잭션 1개**가 자동으로 성립하는 것이 아니다.

| 흔한 오해 | 왜 초급자가 그렇게 느끼나 | 먼저 고칠 문장 |
|---|---|---|
| 요청 하나가 오면 트랜잭션도 자동으로 하나 열린다 | request와 business use case가 한 덩어리처럼 보이기 때문 | 트랜잭션은 request가 아니라 "트랜잭션 경계가 붙은 service 호출" 기준으로 본다 |
| JDBC `executeUpdate()`를 한 번 호출했으니 전체 작업이 끝난다 | SQL 실행과 commit을 같은 순간으로 느끼기 때문 | SQL 실행과 commit은 다를 수 있고, 같은 트랜잭션 안에서 여러 SQL이 묶일 수 있다 |
| controller에서 예외가 나면 무조건 rollback된다 | 화면에서 "실패"가 보이면 DB도 다 취소됐다고 느끼기 때문 | rollback은 트랜잭션이 실제로 열렸는지와 예외 규칙을 같이 봐야 한다 |
| repository 메서드 하나가 곧 비즈니스 경계다 | DB 호출이 코드상 가장 눈에 띄기 때문 | 비즈니스 경계는 보통 service가 소유하고 repository는 DB 작업 한 조각을 맡는다 |

### 아주 짧은 그림

```text
HTTP 요청
  -> Controller
    -> Service (@Transactional 가능)
      -> Repository/JDBC
        -> DB
```

초급자용 해석:

- controller는 "무슨 요청인지"를 받는다.
- service는 "이 유스케이스를 어디까지 하나로 묶을지"를 정한다.
- repository/JDBC는 "실제 SQL"을 실행한다.

### 초급자용 비교 한 줄

| 보이는 코드 | 바로 같은 뜻이 아닌 것 |
|---|---|
| `@GetMapping`, `@PostMapping` | transaction 시작점 |
| `repository.save()`, `jdbcTemplate.update()` | commit 완료 |
| controller에서 예외 발생 | 항상 rollback |

## 전환 2: JDBC/트랜잭션 -> DI/AOP에서 자주 헷갈리는 것

여기서 제일 많이 생기는 오해는 이것이다.

`@Transactional`을 배우면 DB 기능처럼 보이지만, Spring에서는 **프록시가 메서드 호출을 감싸서 트랜잭션을 붙인다.**

| 흔한 오해 | 왜 틀리기 쉬운가 | 먼저 고칠 문장 |
|---|---|---|
| `@Transactional`은 JDBC 위에 바로 붙는 DB 옵션이다 | SQL과 트랜잭션을 한 층으로 보기 쉽다 | Spring에서는 보통 Bean 메서드 호출을 프록시가 감싸서 트랜잭션을 시작한다 |
| DI와 AOP는 둘 다 "Spring이 알아서 해줌"이라서 같은 개념이다 | 둘 다 자동처럼 보이기 때문 | DI는 객체를 연결하는 일이고, AOP는 호출 앞뒤에 기능을 끼워 넣는 일이다 |
| 같은 클래스 안에서 `this.save()`를 불러도 `@Transactional`이 적용된다 | 메서드에 annotation이 붙어 있으니 어디서 불러도 될 것처럼 보이기 때문 | 프록시를 안 지나면 annotation 기반 기능이 빠질 수 있다 |
| `new OrderService()`로 만들어도 `@Transactional`이 되겠지 | 자바 객체만 있으면 된다고 느끼기 때문 | Spring Bean이어야 프록시가 붙고, 보통 DI로 주입받아야 한다 |

### 한 줄 비교

| 개념 | 초급자용 질문 |
|---|---|
| DI | "이 객체를 누가 만들어서 넣어 주나?" |
| AOP | "이 메서드 호출 앞뒤에 누가 끼어드나?" |
| `@Transactional` | "그 끼어드는 기능 중 하나가 트랜잭션인가?" |

### 한 번 더 짧게 구분

| 보이는 현상 | 먼저 붙일 이름 |
|---|---|
| `new OrderService()`로 만든 객체에는 annotation 효과가 없다 | DI 바깥 객체 |
| 같은 클래스 안의 `this.save()`에서 annotation 효과가 빠진다 | 프록시 우회 |
| bean은 잘 주입되는데 `@Transactional`만 안 먹는 것 같다 | AOP 적용 경로 확인 |

## 한 페이지 체크리스트

아래 6문항만 먼저 답하면 deep dive로 너무 빨리 내려갈 일이 많이 줄어든다.

1. 지금 헷갈리는 대상이 `요청 처리(MVC)`인지 `DB 호출(JDBC)`인지 `경계(Transaction)`인지 `연결/프록시(DI/AOP)`인지 먼저 이름 붙였는가?
2. controller가 비즈니스 경계를 소유한다고 생각하고 있지 않은가?
3. SQL 한 번 실행된 사실과 commit/rollback 경계를 같은 것으로 보고 있지 않은가?
4. `@Transactional`을 "DB 자체 기능"으로만 이해하고, Spring 프록시 경로를 빼먹고 있지 않은가?
5. annotation이 붙은 메서드가 Spring Bean 바깥 호출인지, 같은 클래스 내부 호출인지 확인했는가?
6. `REQUIRES_NEW`, isolation, self-invocation deep dive로 내려가기 전에 기초 primer 한 칸을 아직 건너뛰지 않았는가?

## 오해별 안전한 다음 한 걸음

항상 `primer -> follow-up -> deep dive` 순서로만 내려간다.

| 지금 막히는 지점 | 먼저 볼 primer | 그다음 한 걸음 | deep dive는 나중에 |
|---|---|---|---|
| MVC와 service/repository 경계가 흐리다 | [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md) | [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md) | MVC request lifecycle 전체 |
| JDBC 호출과 트랜잭션 경계를 같은 것으로 느낀다 | [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) | [트랜잭션 기초](../database/transaction-basics.md) | isolation / locking / propagation |
| `commit`과 `rollback`이 어느 service 범위에서 묶이는지 헷갈린다 | [트랜잭션 기초](../database/transaction-basics.md) | [@Transactional 기초](./spring-transactional-basics.md) | propagation / rollback-only / self-invocation |
| `Bean`, `주입`, `프록시`가 한꺼번에 섞인다 | [IoC와 DI 기초](./spring-ioc-di-basics.md) | [AOP 기초](./spring-aop-basics.md) | AOP proxy mechanism 세부 |
| `@Transactional`이 왜 안 먹는지 모르겠다 | [@Transactional 기초](./spring-transactional-basics.md) | [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md) | self-invocation matrix / propagation |

## 길을 잃었을 때 복귀점

같은 요청에서 `302`, `controller`, `save()`, `commit/rollback`이 한 번에 떠오르면 이 문서를 더 깊게 읽기보다 아래 복귀점으로 질문을 다시 하나만 고른다.

| 지금 다시 막힌 말 | 돌아갈 문서 | 왜 이 복귀점이 안전한가 |
|---|---|---|
| "`302`, `304`, `cookie`가 먼저 헷갈려요" | [Network -> Spring handoff](../network/README.md#network---spring-handoff) | browser/network 질문을 먼저 떼어 낸다 |
| "`controller -> service -> repository`까지만 다시 보고 싶어요" | [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md) | 요청 처리와 객체 준비를 다시 분리한다 |
| "`save()`와 `commit/rollback`만 다시 정리하고 싶어요" | [Database First-Step Bridge](../database/database-first-step-bridge.md) | DB 입구 3축으로 돌아가 질문을 다시 고른다 |
| "문서가 많아서 Spring beginner 입구로 돌아가고 싶어요" | [spring primer 되돌아가기](./README.md#spring-primer-되돌아가기) | 같은 category에서 primer 한 칸만 다시 고르게 한다 |

## 3개만 기억하고 끝내기

- controller는 요청의 입구지, transaction 경계 그 자체가 아니다.
- JDBC 호출은 SQL 실행이고, transaction은 commit/rollback 경계다.
- `@Transactional`은 annotation 한 줄이 아니라, 보통 Spring Bean + proxy 경로까지 포함해서 봐야 한다.

## 초급자용 마지막 한 줄

막히는 지점이 보여도 바로 `REQUIRES_NEW`, isolation level, proxy internals로 내려가지 말고, 먼저 **"요청 처리냐, DB 호출이냐, 트랜잭션 경계냐, 프록시 적용이냐"**를 구분하면 사다리 전환에서 덜 흔들린다.

## 한 줄 정리

MVC에서 JDBC/트랜잭션으로, 다시 DI/AOP로 넘어갈 때는 "요청 처리", "DB 작업", "경계", "프록시"를 한 칸씩 분리해서 봐야 초반 deep dive 오진입을 줄일 수 있다.
