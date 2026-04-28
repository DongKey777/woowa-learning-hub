# Junior Backend CS Roadmap

> 신입 백엔드 개발자 기준으로 CS-study를 어떤 순서로 공부할지 정리한 가이드

> retrieval-anchor-keywords: junior backend roadmap, 신입 백엔드 로드맵, beginner backend study order, backend learning path, cs study sequence, foundational curriculum, backend starter guide, roadmap, survey, backend mission prerequisite, 우테코 백엔드 미션 선행지식, backend mission first reading, woowacourse backend learning ladder, 우테코 백엔드 안전 사다리, java http mvc jdbc transaction di aop system design 순서, backend beginner safe next step

## 목표

이 문서는 CS-study의 범위가 넓어서 무엇부터 봐야 할지 막막할 때,

- 어떤 주제를 먼저 봐야 하는지
- 어느 정도 깊이까지 공부해야 하는지
- 어떤 문서를 같이 읽으면 좋은지

를 빠르게 정리하기 위해 만들었다.

미션 기준으로 "어디까지 먼저 알아야 시작할 수 있지?"가 막막하면
[우테코 백엔드 미션 선행 개념 입문](./contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md)부터 보고,
이 로드맵을 따라가면 된다.

## 우테코 백엔드 안전 사다리 동기화

우테코 백엔드 입문자는 아래 6단계를 먼저 고정한 뒤, 그 다음에 운영체제/알고리즘/심화 트랙으로 확장하는 편이 안전하다.
이 섹션은 category README 사이 점프를 줄이기 위한 `primer -> follow-up -> deep dive` 최소 사다리다.

| 단계 | primer | 안전한 다음 한 걸음 | deep dive는 나중에 |
|---|---|---|---|
| 1. Java basics | [자바 언어의 구조와 기본 문법](./contents/language/java/java-language-basics.md) | [Java 타입, 클래스, 객체, OOP 입문](./contents/language/java/java-types-class-object-oop-basics.md) | language runtime/concurrency catalog |
| 2. HTTP / web basics | [HTTP 요청-응답 기본 흐름](./contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [HTTP 메서드와 REST 멱등성 입문](./contents/network/http-methods-rest-idempotency-basics.md) | proxy timeout, 499, coalescing deep dive |
| 3. MVC | [Spring 요청 파이프라인과 Bean Container 기초](./contents/spring/spring-request-pipeline-bean-container-foundations-primer.md) | [Spring MVC 컨트롤러 기초](./contents/spring/spring-mvc-controller-basics.md) | HandlerMethod resolver, async lifecycle |
| 4. JDBC / transactions | [Database First-Step Bridge](./contents/database/database-first-step-bridge.md) | [JDBC · JPA · MyBatis 기초](./contents/database/jdbc-jpa-mybatis-basics.md) -> [트랜잭션 기초](./contents/database/transaction-basics.md) | isolation anomaly / lock 심화 |
| 5. DI / AOP | [IoC와 DI 기초](./contents/spring/spring-ioc-di-basics.md) | [AOP 기초](./contents/spring/spring-aop-basics.md) -> [@Transactional 기초](./contents/spring/spring-transactional-basics.md) | rollback-only, propagation, self-invocation 트랩 |
| 6. System design | [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./contents/system-design/stateless-backend-cache-database-queue-starter-pack.md) | [System Design Foundations](./contents/system-design/system-design-foundations.md) | cutover/control-plane incident 설계 |

짧게 외우면 `Java -> HTTP/web -> MVC -> JDBC/transactions -> DI/AOP -> system design`이다.

## 1단계. 자바 언어 감각 잡기

추천 순서:

1. [자바 언어의 구조와 기본 문법](./contents/language/java/java-language-basics.md)
2. [객체지향 핵심 원리](./contents/language/java/object-oriented-core-principles.md)
3. [불변 객체와 방어적 복사](./contents/language/java/immutable-objects-and-defensive-copying.md)
4. [추상 클래스 vs 인터페이스](./contents/language/java/abstract-class-vs-interface.md)

이 단계 목표:

- 객체/클래스/인스턴스 설명 가능
- 상속/다형성/추상화 설명 가능
- 불변 객체, 방어적 복사, 얕은/깊은 복사 구분 가능

## 2단계. 운영체제와 네트워크 기초

추천 순서:

1. [Operating System](./contents/operating-system/README.md)
2. [Network](./contents/network/README.md)
3. [HTTP 메서드, REST, 멱등성](./contents/network/http-methods-rest-idempotency.md)
4. [HTTP의 무상태성과 쿠키, 세션, 캐시](./contents/network/http-state-session-cache.md)

이 단계 목표:

- 프로세스와 스레드 차이 설명 가능
- 동기/비동기, blocking/non-blocking 차이 설명 가능
- TCP/UDP 차이 설명 가능
- HTTP 요청/응답 흐름 설명 가능
- 세션, 쿠키, 캐시 차이 설명 가능
- REST와 멱등성 설명 가능

## 3단계. 데이터베이스 기본기

추천 순서:

1. [Database](./contents/database/README.md)
2. [JDBC, JPA, MyBatis](./contents/database/jdbc-jpa-mybatis.md)
3. [트랜잭션 격리수준과 락](./contents/database/transaction-isolation-locking.md)
4. [인덱스와 실행 계획](./contents/database/index-and-explain.md)
5. [MVCC, Replication, Sharding](./contents/database/mvcc-replication-sharding.md)
6. [트랜잭션 실전 시나리오](./contents/database/transaction-case-studies.md)
7. [JDBC 실전 코드 패턴](./contents/database/jdbc-code-patterns.md)
8. [SQL 조인과 쿼리 실행 순서](./contents/database/sql-joins-and-query-order.md)
9. [Schema Migration, Partitioning, CDC, CQRS](./contents/database/schema-migration-partitioning-cdc-cqrs.md)

이 단계 목표:

- 정규화/반정규화 설명 가능
- 인덱스, 트랜잭션, NoSQL 기본 개념 설명 가능
- JDBC / JPA / MyBatis 차이 설명 가능
- SQLite / H2 / MySQL 차이 설명 가능
- 락, 격리수준, MVCC 차이 설명 가능
- 실행 계획을 통해 인덱스 사용 여부를 해석할 수 있음

## 4단계. 소프트웨어 공학과 저장 계층 설계

추천 순서:

1. [Software Engineering](./contents/software-engineering/README.md)
2. [Repository, DAO, Entity](./contents/software-engineering/repository-dao-entity.md)
3. [Design Pattern](./contents/design-pattern/README.md)
4. [API 설계와 예외 처리](./contents/software-engineering/api-design-error-handling.md)
5. [캐시, 메시징, 관측성](./contents/software-engineering/cache-message-observability.md)

이 단계 목표:

- SOLID를 말로 설명 가능
- Repository / DAO / Entity 구분 가능
- 어떤 경우에 패턴이 과한지 판단 가능
- 객체지향 설계를 왜 이렇게 나눴는지 설명 가능
- 예외를 어디서 던지고 잡을지 설명 가능
- 캐시 / 메시징 / 관측성의 기본 역할을 설명 가능

## 5단계. Spring 기본기 연결

추천 순서:

1. [Spring Framework](./contents/spring/README.md)
2. [IoC 컨테이너와 DI](./contents/spring/ioc-di-container.md)
3. [AOP와 프록시 메커니즘](./contents/spring/aop-proxy-mechanism.md)
4. [Spring MVC 요청 생명주기](./contents/spring/spring-mvc-request-lifecycle.md)
5. [Spring Boot 자동 구성](./contents/spring/spring-boot-autoconfiguration.md)

이 단계 목표:

- Spring이 객체를 직접 `new` 하지 않고 관리하는 이유를 설명 가능
- 요청이 `DispatcherServlet`을 지나 컨트롤러까지 도달하는 흐름을 설명 가능
- Spring Boot가 자동으로 설정해주는 것과 개발자가 명시적으로 제어해야 하는 것을 구분 가능
- 프록시 기반 기능이 왜 동작하고 어디서 한계가 생기는지 감을 잡음

`@Transactional`과 Spring Security 같은 주제는 이 단계에서 가볍게 존재만 알고, 실제 설계 제약과 운영 포인트는 심화 로드맵에서 다루는 편이 좋다.

## 6단계. 알고리즘 / 자료구조 병행

추천 순서:

- [Data Structure](./contents/data-structure/README.md)
- [Algorithm](./contents/algorithm/README.md)

이 단계 목표:

- 기본 자료구조 특성 설명 가능
- 시간복잡도 감각 잡기
- DFS/BFS, 정렬, 그래프, DP 기본 문제 풀이 가능

## 7단계. JVM / 동시성 심화

추천 순서:

1. [JVM, GC, JMM](./contents/language/java/jvm-gc-jmm-overview.md)
2. [Java 동시성 유틸리티](./contents/language/java/java-concurrency-utilities.md)
3. [ClassLoader, Exception 경계, 객체 계약](./contents/language/java/classloader-exception-boundaries-object-contracts.md)
4. [컨텍스트 스위칭, 데드락, lock-free](./contents/operating-system/context-switching-deadlock-lockfree.md)
5. [I/O 모델과 이벤트 루프](./contents/operating-system/io-models-and-event-loop.md)
6. [Reflection, Generics, Annotations](./contents/language/java/reflection-generics-annotations.md)

이 단계 목표:

- JVM 메모리 구조와 GC를 설명 가능
- JMM과 `volatile`, `synchronized` 차이를 설명 가능
- `ExecutorService`, `Future`, `CompletableFuture`를 구분 가능
- 데드락 / 스타베이션 / lock-free를 설명 가능
- blocking/non-blocking과 이벤트 루프를 설명 가능

## 공부할 때 기준

각 주제를 공부할 때 아래 4가지를 항상 같이 가져가면 좋다.

1. 정의를 한 문장으로 설명할 수 있는가
2. 왜 필요한지 말할 수 있는가
3. 코드나 시스템에서 어디 쓰이는지 말할 수 있는가
4. 면접에서 30초 안에 답할 수 있는가

## 한 단계 더 깊게 가는 방법

기본 정리가 끝나면 아래 문서를 같이 보자.

- [Senior-Level CS Questions](./SENIOR-QUESTIONS.md)
- [System Design](./contents/system-design/README.md)

이 문서는 정의 확인용이 아니라

- 트레이드오프
- 장애 시나리오
- 대안 비교
- 설계 선택 이유
- 요구사항을 시스템 구조로 바꾸는 방식

를 묻는 질문 모음이다.

즉 “외웠다” 수준에서 “설명하고 판단할 수 있다” 수준으로 올리기 위한 보조 문서다.

## 핵심

이 저장소를 공부하면서 가장 중요한 건 “많이 읽는 것”이 아니라,

**읽은 개념을 코드와 연결해서 설명할 수 있게 만드는 것**

이다.
