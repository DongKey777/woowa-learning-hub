# Database (데이터베이스)

> 한 줄 요약: 이 README는 database를 처음 고를 때 쓰는 `category navigator`다. 처음에는 `Database First-Step Bridge -> 트랜잭션 기초 -> JDBC · JPA · MyBatis 기초 -> 인덱스 기초`까지만 잡고, 운영/incident 문서는 실제 증상이 붙을 때만 follow-up으로 내려간다.

**난이도: 🟢 Beginner**

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [트랜잭션 기초](./transaction-basics.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [인덱스 기초](./index-basics.md)
- [루트 README](../../README.md)

retrieval-anchor-keywords: database readme, database navigator, database beginner route, database 처음 뭐부터, db 처음 어디부터, save 보이는데 sql 안 보여요, transactional save entity 헷갈려요, explain 처음 뭐부터, key null 뭐예요, deadlock 은 나중에, cdc cutover follow-up, spring database bridge

## 빠른 탐색

처음 5분은 아래 한 줄만 기억하면 충분하다.

`Database First-Step Bridge -> 트랜잭션 기초 -> JDBC · JPA · MyBatis 기초 -> 인덱스 기초`

| 지금 막힌 말 | 먼저 열 문서 | 왜 여기서 시작하나 |
|---|---|---|
| "DB를 어디부터 읽어야 할지 모르겠어요" | [Database First-Step Bridge](./database-first-step-bridge.md) | 질문 축을 `트랜잭션 / SQL 위치 / 인덱스`로 먼저 자른다 |
| "`commit`은 했는데 왜 마지막 재고가 또 팔려요?" | [트랜잭션 기초](./transaction-basics.md) | commit/rollback과 동시성 충돌을 먼저 분리한다 |
| "`save()`는 보이는데 SQL이 안 보여요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | repository, entity, mapper 역할을 먼저 구분한다 |
| "WHERE 조건 하나인데 왜 느려요?" | [인덱스 기초](./index-basics.md) | 조회 경로 문제를 따로 떼어 봐야 한다 |

## 한 화면에 같이 보일 때

`@Transactional`, `save()`, `@Entity`가 같이 보이면 아래처럼 쪼개 읽는다.

| 먼저 보이는 단서 | 초보자용 첫 해석 | 다음 문서 |
|---|---|---|
| `@Transactional` | 어디까지 같이 commit/rollback할지 정하는 경계다 | [트랜잭션 기초](./transaction-basics.md) |
| `save()` / `Repository` / `Mapper` | 저장이나 조회를 시작하는 창구다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `@Entity` | 무엇을 저장하는지 보여 주는 매핑 단서다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `key = NULL`, `Using filesort` | 조회 경로를 다시 읽어야 한다는 신호다 | [인덱스와 실행 계획](./index-and-explain.md) |

## Spring -> Database handoff

`controller -> service -> repository`까지는 보이는데 database에서 어디부터 읽어야 할지 막히면 이 순서로만 간다.

| 지금 막힌 말 | primer 1장 | safe next step 1장 |
|---|---|---|
| "`spring` 다음에 DB는 뭐부터예요?" | [Database First-Step Bridge](./database-first-step-bridge.md) | [트랜잭션 기초](./transaction-basics.md) 또는 [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`save()`는 보이는데 SQL이 안 보여요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| "`왜 같이 rollback돼요?`" | [트랜잭션 기초](./transaction-basics.md) | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |

질문이 browser/network 쪽으로 다시 올라가면 [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)과 [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)로 한 칸 복귀한다.

## beginner route 뒤에 붙는 4번째 문서

처음부터 deep dive로 내려가지 말고, 아래처럼 "남은 질문 1개" 기준으로 4번째 문서만 붙인다.

| beginner route 뒤에 남은 질문 | 4번째 문서 |
|---|---|
| "`@Transactional`인데 왜 중복 판매가 나요?" | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| "`JpaRepository` 구현체가 안 보여요" | [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| "`save()`는 보이는데 pool timeout도 보여요" | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |
| "`EXPLAIN`에 `key = NULL`이 보여요" | [인덱스와 실행 계획](./index-and-explain.md) |
| "`cdc replay`, `cutover`가 같이 궁금해요" | [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md) |

## 추천 학습 흐름 (category-local survey)

이 survey는 "긴 catalog를 정독"하라는 뜻이 아니다. 각 줄의 앞 2~3개 primer만 먼저 읽고, 실제 증상이 생겼을 때만 follow-up으로 내려간다.

| 질문 축 | beginner first route | follow-up 신호 |
|---|---|---|
| transaction / lock | [Database First-Step Bridge](./database-first-step-bridge.md) -> [트랜잭션 기초](./transaction-basics.md) -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) | `deadlock`, `retry`, `FOR UPDATE`, oversell |
| SQL 위치 / JPA | [Database First-Step Bridge](./database-first-step-bridge.md) -> [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | `JpaRepository`, `flush`, lazy loading, pool timeout |
| index / explain | [인덱스 기초](./index-basics.md) -> [인덱스와 실행 계획](./index-and-explain.md) | `Using filesort`, `actual rows`, histogram |
| replica / consistency | [MVCC, Replication, Sharding](./mvcc-replication-sharding.md) -> [Replica Lag와 Read-after-Write](./replica-lag-read-after-write-strategies.md) | `stale read`, failover, session guarantee |
| cdc / cutover | primer route 아님 | `cdc`, `replay`, `backfill`, `cutover`가 질문에 직접 등장할 때만 |

## 연결해서 보면 좋은 문서 (cross-category bridge)

| 경계 | 먼저 열 문서 | 다음 1걸음 |
|---|---|---|
| network -> spring -> db | [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) -> [Database First-Step Bridge](./database-first-step-bridge.md) |
| repository / DAO / entity 이름 구분 | [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md) | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| Spring Data JPA 구현체/메서드 이름 | [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) | [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md) |
| cdc / replay가 system design 질문으로 커짐 | [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md) | [Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md) |
| authority / security로 번짐 | [Authority Transfer vs Revoke Lag Primer Bridge](../security/authority-transfer-vs-revoke-lag-primer-bridge.md) | [Permission Model Bridge: Authn -> Role -> Scope -> Ownership](../security/permission-model-bridge-authn-to-role-scope-ownership.md) |

## follow-up 묶음

README에서는 "내 질문이 어느 follow-up 묶음으로 커졌는가"만 확인하고, 해당 문서로 바로 건너가면 된다.

| 묶음 | 바로 갈 문서 |
|---|---|
| lock incident | [락 기초](./lock-basics.md), [Deadlock vs Lock Wait Timeout 입문 프라이머](./deadlock-vs-lock-wait-timeout-primer.md), [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |
| explain deeper | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md), [PostgreSQL `EXPLAIN ANALYZE`에서 `actual rows`, `buffers`, `heap fetches`를 같이 읽는 법](./postgresql-explain-analyze-terms-mini-bridge.md), [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) |
| migration / cdc | [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md), [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md), [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md) |
| replica / failover | [Replica Lag와 Read-after-Write](./replica-lag-read-after-write-strategies.md), [Client Consistency Tokens](./client-consistency-tokens.md), [Failover Promotion, Visibility Window, and Read Divergence](./failover-promotion-read-divergence.md) |
| lifecycle / cleanup | [Soft Delete와 Data Lifecycle](./soft-delete-uniqueness-indexing-lifecycle.md), [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md), [Summary Maintenance and Drift Repair](./summary-drift-detection-bounded-rebuild.md) |

## 한 줄 정리

이 README는 database 전체 catalog를 처음부터 읽는 문서가 아니라, 초보자가 `트랜잭션 / SQL 위치 / 인덱스` 중 지금 막힌 질문 하나를 골라 첫 primer로 안전하게 보내는 라우터다.
