# Database (데이터베이스)

> 한 줄 요약: 이 README는 database를 처음 고를 때 쓰는 `category navigator`다. 처음에는 primer 3편만 읽고, `playbook`·`runbook`·`cutover`는 실제 증상이나 운영 과제가 붙을 때만 내려간다.

**난이도: 🔴 Advanced**

> 작성자 : [박재용](https://github.com/ggjae), [서그림](https://github.com/Seogeurim), [윤가영](https://github.com/yoongoing), [이세명](https://github.com/3people), [장주섭](https://github.com/wntjq68), [정희재](https://github.com/Hee-Jae)

> retrieval-anchor-keywords: database readme, database navigator, database primer, database survey, database catalog, database deep dive, database playbook, database runbook, database routing, database index guide, database quick start, database quick-start, database bridge entrypoint, database system design bridge entrypoint, database + system design route, database authority bridge entrypoint, identity / delegation / lifecycle route, database / security authority bridge, verification / shadowing / authority bridge, authority route parity, database + security + system design route, schema migration, cdc cqrs, read model, projection rebuild, dual read verification, historical backfill, replay safety, idempotency, replica lag, stale read, read-after-write, projection lag, old data after write, freshness cluster, failover freshness, promotion stale read, post failover stale read, topology cache stale, visibility window, old primary still serving reads, some pods old some new, session consistency, session guarantee, monotonic read, causal consistency, consistency token, session watermark, saw newer then older, same session sees older data, multi-tab stale read, cause before effect, system design bridge, projection freshness slo, read model cutover guardrail, overlap enforcement, PostgreSQL vs MySQL overlap, PostgreSQL vs MySQL isolation, postgres vs mysql isolation, postgresql repeatable read snapshot isolation, postgresql serializable ssi, postgresql serializable retry playbook, postgres serializable beginner, serializable snapshot isolation retry, ssi retry envelope, could not serialize access, mysql serializable locking read, isolation cheat sheet, isolation anomaly cheat sheet, dirty read non-repeatable read lost update write skew phantom, beginner isolation matrix, lost update guardrail, write skew guardrail, phantom guardrail, phantom-safe booking primer, booking overlap pattern primer, unique slot vs exclusion constraint vs guard row, unique-slot booking, exclusion-constraint booking, guard-row booking, overlap probe composite index, booking overlap index, interval predicate scan axis, composite index lock footprint, hold expiration predicate drift, reservation arbitration predicate drift, held confirmed expired lifecycle, booking blackout cleanup alignment, active overlap flag, expired unreleased drift runbook, deadline passed still blocking, release lag slo, post-expiry conflict, cleanup lag, active predicate lifecycle, active predicate alignment, capacity guard drift, admission check guard row reconciliation, active hold table split, live archive split, deleted_at blocking truth, expiry worker race, confirm expire race, row-lock finalization, version-column finalization, optimistic lock failure, version conflict, objectoptimisticlockingfailureexception, rollback only optimistic lock, 409 conflict optimistic lock, claim-path finalization, opportunistic release, guard row, ordered guard row upsert, pre-seeded guard row, guard creation deadlock, PostgreSQL on conflict guard row, MySQL on duplicate key guard row, serializable retry, serializable retry telemetry, sqlstate 40001, sqlstate 40P01, serializable whole transaction retry, retry budget, hot aggregate observability, reconciliation, minimum staffing, capacity invariant, multi-day booking, guard-row granularity, canonical lock ordering, booking deadlock, hot row contention, striped guard row, counter sharding, reservation ledger, room-type inventory, shared pool inventory, room_type_day guard, later unit assignment, pooled inventory ledger, room assignment after booking, assignment horizon, sell from pool assign later, hot path slot arbitration, booking arbitration choice, slot unique key, unique slot claim, resource-day guard row, hybrid fencing booking, reservation-local fence, booking ingress fence, slot unique vs guard row, authority transfer, decision parity, auth shadow divergence, deprovision tail, database security bridge, identity cutover, auth shadow evaluation, SCIM deprovision, SCIM disable but still access, backfill is green but access tail remains, backfill verification, slotization migration, interval-to-slot cutover, slot table backfill, double-booking migration, slotization precheck, legacy interval overlap query, slot rounding collision, rounded slot collapse, DST boundary precheck, ambiguous local time fold, nonexistent local time gap, slot calendar dimension, slot delta reschedule semantics, slot claim tombstone cleanup, slot release watermark, reschedule union lock slot claim, cleanup evidence, retirement evidence, decision log join key, audit evidence bundle
> retrieval-anchor-keywords: scim disable했는데 아직 접근돼요, deprovision 끝났는데 access tail이 남아요, 비활성화했는데 특정 pod만 아직 허용해요, backfill은 끝났는데 왜 old authority가 남아요, row parity 다음에 뭘 확인해요, authority transfer beginner route, deprovision tail beginner route, access tail beginner route, decision parity beginner route, cleanup evidence beginner route

<details>
<summary>Table of Contents</summary>

- [빠른 탐색](#빠른-탐색)
- [역할별 라우팅 요약](#역할별-라우팅-요약)
- [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey)
- [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge)
- [트랜잭션 경계 / 애플리케이션 브리지](#database-bridge-transaction-app)
- [CDC / Outbox / Read Model Cutover 브리지](#database-bridge-cdc-cutover)
- [Identity / Authority Transfer 브리지](#database-bridge-identity-authority)
- [Retry / Idempotency / Replay 브리지](#database-bridge-retry-replay)
- [현대 catalog](#현대-catalog)
- [데이터베이스](#데이터베이스)
- [JDBC, JPA, MyBatis](#jdbc-jpa-mybatis)
- [트랜잭션 격리수준과 락](#트랜잭션-격리수준과-락)
- [인덱스와 실행 계획](#인덱스와-실행-계획)
- [B+Tree vs LSM-Tree](#btree-vs-lsm-tree)
- [MySQL Optimizer Hints and Index Merge](#mysql-optimizer-hints-and-index-merge)
- [MVCC, Replication, Sharding](#mvcc-replication-sharding)
- [트랜잭션 실전 시나리오](#트랜잭션-실전-시나리오)
- [Outbox, Saga, Eventual Consistency](#outbox-saga-eventual-consistency)
- [Deadlock Case Study](#deadlock-case-study)
- [JDBC 실전 코드 패턴](#jdbc-실전-코드-패턴)
- [Connection Pool, Transaction Propagation, Bulk Write](#connection-pool-transaction-propagation-bulk-write)
- [HikariCP 튜닝](#hikaricp-튜닝)
- [멱등성 키와 중복 방지](#멱등성-키와-중복-방지)
- [쿼리 튜닝 체크리스트](#쿼리-튜닝-체크리스트)
- [SQL 조인과 쿼리 실행 순서](#sql-조인과-쿼리-실행-순서)
- [Schema Migration, Partitioning, CDC, CQRS](#schema-migration-partitioning-cdc-cqrs)
- [Multi-Tenant Table Design](#multi-tenant-table-design)
- [온라인 스키마 변경 전략](#온라인-스키마-변경-전략)
- [Authority Transfer / Security Bridge](#authority-transfer--security-bridge)
- [느린 쿼리 분석 플레이북](#느린-쿼리-분석-플레이북)
- [Redo Log, Undo Log, Checkpoint, Crash Recovery](#redo-log-undo-log-checkpoint-crash-recovery)
- [Index Condition Pushdown, Filesort, Temporary Table](#index-condition-pushdown-filesort-temporary-table)
- [Statistics, Histograms, and Cardinality Estimation](#statistics-histograms-and-cardinality-estimation)
- [Replica Lag와 Read-after-Write](#replica-lag와-read-after-write)
- [CDC, Debezium, Outbox, Binlog](#cdc-debezium-outbox-binlog)
- [Queue / Claim Patterns](#queue--claim-patterns)
- [Offset vs Seek Pagination](#offset-vs-seek-pagination)
- [Write Skew와 Phantom Read 사례](#write-skew와-phantom-read-사례)
- [Vacuum / Purge Debt](#vacuum--purge-debt)
- [레거시 primer / reference](#레거시-primer--reference)
- [정규화](#정규화)
- [반정규화](#반정규화)
- [정규화와 반정규화 트레이드오프](#정규화와-반정규화-트레이드오프)
- [Summary Maintenance and Drift Repair](#summary-maintenance-and-drift-repair)
- [Soft Delete와 Data Lifecycle](#soft-delete와-data-lifecycle)
- [인덱스 (Index)](#인덱스-index)
- [트랜잭션(Transaction)과 교착상태](#트랜잭션transaction과-교착상태)
- [NoSQL](#nosql)

</details>

---

## 빠른 탐색

이 README는 입문자가 처음부터 끝까지 읽는 본문이라기보다, **지금 막힌 질문에 맞는 첫 문서 1개를 고르는 라우터**로 쓰는 편이 안전하다.
처음부터 `playbook`, `runbook`, `case study`, `cutover`로 내려가지 말고, 아래 입문 3편에서 mental model만 먼저 고정한 뒤 증상이 붙을 때만 follow-up으로 이동한다.

| 지금 필요한 역할 | 먼저 여는 곳 | 아직 미루는 것 |
|---|---|---|
| 입문 순서 잡기 | [Database First-Step Bridge](./database-first-step-bridge.md), [트랜잭션 기초](./transaction-basics.md), [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | `playbook`, `runbook`, `cutover`, 엔진별 비교 |
| category 안에서 다음 문서 고르기 | [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey) | 긴 catalog를 처음부터 끝까지 정독하기 |
| 실제 증상 대응 | primer를 먼저 읽고 난 뒤 관련 `[playbook]`, `[runbook]` | primer 없이 `deadlock`, `failover`, `cdc replay`부터 읽기 |

처음인데 "`브라우저 요청이 controller를 지나 DB까지 어떻게 와요?`", "`왜 네트워크나 Spring을 안 보고 DB 문서부터 보면 헷갈려요?`", "`save()`는 보이는데 그 전에 무슨 일이 있었죠?`"처럼 앞단 handoff가 같이 막히면 아래 cross-category 사다리부터 본다.

| 지금 막힌 beginner 질문 | 먼저 볼 문서 | 바로 다음 1걸음 | deep dive로 내려가지 않는 이유 |
|---|---|---|---|
| "브라우저 요청이 서버에 어떻게 들어와요?" | [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | DB locking보다 먼저 요청 진입과 객체 연결을 분리해야 한다 |
| "controller 다음에 DB 코드는 어디서 시작돼요?" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [Database First-Step Bridge](./database-first-step-bridge.md) | `DispatcherServlet`, DI, `@Transactional`을 모르면 SQL 위치 판단이 흔들린다 |
| "`save()`는 보이는데 SQL이 왜 안 보여요?" | [Database First-Step Bridge](./database-first-step-bridge.md) | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 아직 접근 기술 구분 단계이므로 MVCC, failover, replay로 건너뛰지 않는다 |

### 🟢 Beginner 입문 3편

처음 DB를 공부하는 경우 아래 3편만 먼저 읽고 멈춘다. `PreparedStatement`, `deadlock`, `failover` 같은 단어가 먼저 보여도 본문에서 다 해결하려 하지 말고 관련 follow-up으로 넘긴다.

- [Database First-Step Bridge](./database-first-step-bridge.md) — 전체 순서를 먼저 잡는 입구
- [트랜잭션 기초](./transaction-basics.md) — "같이 성공/실패" mental model
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) — "이 코드에서 SQL이 어디서 만들어지는가" mental model

가장 안전한 첫 15분 경로는 아래 한 줄이다.

`Database First-Step Bridge -> 트랜잭션 기초 -> JDBC · JPA · MyBatis 기초`

`commit` 뒤 동시성, oversell, `lock` 같은 말이 붙으면 4번째로 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)를 붙인다. `마지막 재고가 두 번 팔렸어요`, `중복 insert 같아요`처럼 증상 구분부터 막히면 [Lost Update vs Oversell vs Duplicate Insert Beginner Bridge](./lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge.md)를 4번째로 끼운다. 조회가 느리다는 말이 같이 붙을 때만 [인덱스 기초](./index-basics.md)를 4번째로 붙인다.

입문자가 `@Transactional`, `save()`, `@Entity`를 한 화면에서 같이 보면 아래 pass cycle 4칸만 먼저 떠올리면 된다.

| 지금 보인 것 | 초보자용 첫 해석 | 바로 열 문서 |
|---|---|---|
| controller/service | 요청을 어떤 묶음으로 처리할지 정하는 곳일 수 있다 | [Database First-Step Bridge](./database-first-step-bridge.md) |
| `@Transactional` | 같이 commit/rollback할 경계 단서다 | [트랜잭션 기초](./transaction-basics.md) |
| `save()` / `Repository` / `Mapper` | SQL 진입점은 보이지만 SQL 위치는 아직 다를 수 있다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `@Entity` / SQL 문자열 / `mapper.xml` | SQL 생성 위치를 더 좁히는 흔적이다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |

| 지금 처음 막힌 말 | primer에서 멈출지 | 다음 1걸음 |
|---|---|---|
| "`@Transactional`은 있는데 왜 마지막 재고가 또 팔려요?" | primer에서 멈추지 않는다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| "`EXPLAIN`부터 봐야 하나요?" | 먼저 [인덱스 기초](./index-basics.md)에서 멈춘다 | 그다음 [인덱스와 실행 계획](./index-and-explain.md) |
| "`save()`는 보이는데 deadlock 예외 이름도 같이 보여요" | 접근 기술 구분부터 끝낸다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) 후 관련 follow-up |

`EXPLAIN` entrypoint는 아래 한 칸만 더 기억하면 충분하다.

| 지금 보이는 증상 | 먼저 멈출 문서 | 그다음 1걸음 |
|---|---|---|
| "WHERE 조건 하나인데 왜 느려요?" | [인덱스 기초](./index-basics.md) | [인덱스와 실행 계획](./index-and-explain.md) |
| "`key = NULL`이 뭐예요?" | [인덱스와 실행 계획](./index-and-explain.md) | [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md) 또는 [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| "`Using filesort`가 왜 보여요?" | [인덱스와 실행 계획](./index-and-explain.md) | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) |
| "느린 게 DB 때문인지 앱 때문인지 모르겠어요" | [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |

위 primer들을 읽다가 길을 잃으면 각 문서 상단의 `database 카테고리 인덱스` 링크로 다시 이 README에 돌아온다. 돌아와서는 `같이 실패할 범위`, `SQL이 숨어 있는 위치`, `조회 경로가 느린가` 중 지금 질문 하나만 다시 고르면 된다.

인덱스 쪽은 처음부터 [인덱스와 실행 계획](./index-and-explain.md)으로 바로 뛰지 않는 편이 안전하다.

`인덱스 기초 -> 인덱스와 실행 계획`

- [인덱스 기초](./index-basics.md)는 "인덱스가 뭐예요?", "왜 full scan이 나와요?"를 푸는 첫 primer다.
- [인덱스와 실행 계획](./index-and-explain.md)는 "`EXPLAIN`을 어떤 순서로 읽죠?", "`Using filesort`가 왜 보이죠?" 같은 두 번째 질문을 푸는 bridge다.

길을 잃으면 [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey)으로 돌아가고, DB 밖 next step이 필요하면 [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge)에서 다시 갈라진다.

| 지금 막힌 한 문장 | 먼저 열 문서 | 왜 여기서 시작하나 |
|---|---|---|
| "DB를 어디부터 공부해야 할지 모르겠어" | [Database First-Step Bridge](./database-first-step-bridge.md) | 입문 순서를 먼저 고정한다 |
| "주문 저장과 재고 차감이 같이 취소돼야 하나?" | [트랜잭션 기초](./transaction-basics.md) | 실패 범위를 먼저 고정해야 한다 |
| "`save()`는 보이는데 SQL이 어디 있는지 모르겠어" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 접근 기술을 먼저 구분해야 코드 읽기가 풀린다 |
| "`Repository`랑 `Entity`가 같이 보이는데 각각 뭐 하는지 헷갈려" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 이름보다 SQL 위치와 매핑 역할을 먼저 분리해야 한다 |
| "`@Transactional`, `save()`, `@Entity`가 한 화면에 같이 보여서 뭐부터 봐야 할지 모르겠어" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 30초 판별 카드로 역할을 먼저 쪼개야 트랜잭션과 접근 기술을 안 섞는다 |
| "`commit`은 했는데 왜 마지막 재고가 또 팔리지?" | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) | commit 성공과 동시성 제어를 분리해야 한다 |
| "WHERE 조건 하나인데 왜 느린지 모르겠어" | [인덱스 기초](./index-basics.md) | 조회 경로 문제를 따로 떼어 봐야 한다 |

`Repository`, `Entity`, `@Transactional`이 한 화면에 같이 보일 때는 아래 1분 루트로 자르면 안전하다.

| 먼저 보이는 단서 | 첫 해석 | 바로 열 문서 |
|---|---|---|
| `new Order(...)`, `@Entity` | 테이블과 연결된 객체를 만드는 중일 수 있다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `orderRepository.save(order)` | 저장 진입점은 보이지만 SQL 위치는 숨겨져 있을 수 있다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `@Transactional` | 같이 commit/rollback할 범위를 정하는 중이다 | [트랜잭션 기초](./transaction-basics.md) |

입문자 공통 혼동은 아래 세 줄로 먼저 끊으면 된다.

| 자주 섞는 말 | 바로 고칠 한 문장 | 첫 문서 |
|---|---|---|
| "`@Transactional`이 있으니 JPA겠지?" | 트랜잭션 경계와 DB 접근 기술은 다른 축이다 | [트랜잭션 기초](./transaction-basics.md), [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`save()`만 보이는데 insert SQL이 안 보여" | repository 뒤에서 ORM이 SQL을 만들 수 있다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`Entity`가 있으니 repository도 자동으로 다 되는 거 아닌가?" | entity는 매핑 정보이고, 실제 SQL 경로는 repository/mapper/DAO에서 다시 확인한다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md), [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md) |
| "`DAO`면 레거시니까 지금 안 봐도 되지?" | 이름보다 `JdbcTemplate`, `PreparedStatement`, SQL 문자열이 있는지부터 본다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`commit`은 했는데 마지막 재고가 두 번 팔렸어" | commit과 동시성 제어는 다른 질문이다 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |

질문이 2개 이상 섞여 있으면 순서를 아래처럼 고정하면 덜 흔들린다.

| 먼저 분리할 질문 | 첫 문서 | 그다음 문서 |
|---|---|---|
| "무엇을 같이 실패 처리할까?" | [트랜잭션 기초](./transaction-basics.md) | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| "SQL은 코드 어디에 숨어 있나?" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md) |
| "왜 느리거나 lock이 오래 걸리지?" | [인덱스 기초](./index-basics.md) 또는 [락 기초](./lock-basics.md) | [인덱스와 실행 계획](./index-and-explain.md) 또는 [트랜잭션 격리수준과 락](./transaction-isolation-locking.md) |

### 입문 3편 뒤에만 붙일 follow-up

| 이런 단어가 먼저 보이면 | primer 본문에서 어디까지만 잡고 넘길지 |
|---|---|
| `PreparedStatement`, `commit`, `close()` | "SQL이 코드 어디 있나"까지만 잡고 [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)으로 넘긴다 |
| `deadlock`, `lock timeout`, `waiting for lock` | "동시성 충돌이 있다"까지만 잡고 [락 기초](./lock-basics.md) 또는 [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) 뒤에 [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)으로 넘긴다 |
| `retry`, `40001`, `could not serialize access` | "격리 수준만으로 끝나지 않는다"까지만 잡고 [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)으로 넘긴다 |
| `failover`, `stale read`, `replica lag` | "트랜잭션 입문"과 별도 freshness 질문으로 분리하고 [Replica Lag와 Read-after-Write](./replica-lag-read-after-write-strategies.md), [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md)로 넘긴다 |
| `cdc replay`, `projection lag`, `read model` | "입문 primer 범위 밖"으로 끊고 [CDC / Outbox / Read Model Cutover 브리지](#database-bridge-cdc-cutover), [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)로 넘긴다 |

운영/심화 문서와 입문 문서를 구분하는 빠른 규칙은 아래처럼 보면 된다.

| 제목에 보이는 표현 | 초보자용 첫 해석 | 읽는 타이밍 |
|---|---|---|
| `기초`, `first-step`, `bridge`, `basics` | mental model을 잡는 입구 | 처음 읽기 |
| `playbook`, `runbook`, `triage`, `case study`, `cutover` | 증상 대응과 운영 검증 문서 | 실제 증상이 생겼을 때 |
| `postgresql vs mysql`, `retry`, `gap lock`, `failover` | 엔진 차이와 follow-up 비교 문서 | 입문 3편 뒤 |

cross-category bridge와 문서 역할 설명은 아래 섹션으로 바로 내려가면 된다.

## 역할별 라우팅 요약

| 지금 필요한 것 | 문서 역할 | 먼저 갈 곳 |
|---|---|---|
| DB 입문 순서와 현재 질문별 첫 문서 | `beginner bridge` | [Database First-Step Bridge](./database-first-step-bridge.md), [트랜잭션 기초](./transaction-basics.md), [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| database 전체 흐름과 추천 순서 | `survey` | [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey), [루트 README](../../README.md) |
| 트랜잭션 / 인덱스 / MVCC 기초 축 | `primer` | [트랜잭션 기초](./transaction-basics.md) -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md), [인덱스 기초](./index-basics.md) -> [인덱스와 실행 계획](./index-and-explain.md), [MVCC, Replication, Sharding](./mvcc-replication-sharding.md) |
| 문제 축별로 다음 문서를 고르기 | `catalog / navigator` | [현대 catalog](#현대-catalog) 아래 각 섹션 |
| 장애 대응 순서나 검증 절차가 먼저 필요함 | `playbook` / `runbook` | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md), [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md), [Vacuum / Purge / Freeze Risk Triage and Runbook Routing](./vacuum-purge-freeze-risk-runbook-routing.md) |
| 역할 라벨이나 검색 alias가 헷갈림 | `taxonomy` / `routing helper` | [Navigation Taxonomy](../../rag/navigation-taxonomy.md), [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md) |

beginner 기준 빠른 규칙:

- `기초`, `bridge`, `first-step`가 보이면 첫 읽기 후보로 본다.
- `처음 배우는데`, `뭐예요`, `basics`, `헷갈려`처럼 개념 질문이면 `survey`보다 `beginner bridge`나 `primer`부터 연다.
- `[playbook]`, `[runbook]`, `case study`, `cutover`, `triage`가 보이면 막힌 증상이 생겼을 때만 연다.
- `postgresql vs mysql`, `retry`, `gap lock`, `failover`, `cdc replay`가 보이면 심화 follow-up일 가능성이 높다.

| 질문 표현 | beginner-safe 첫 역할 | 바로 열 문서 |
|---|---|---|
| "처음 배우는데 DB를 어디부터 봐요?" | `beginner bridge` | [Database First-Step Bridge](./database-first-step-bridge.md) |
| "트랜잭션이 뭐예요?" | `primer` | [트랜잭션 기초](./transaction-basics.md) |
| "`save()` 뒤 SQL이 왜 안 보여요?" | `primer` | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`deadlock`이 나요" | `playbook` follow-up | [락 기초](./lock-basics.md) 뒤에 [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |

## 추천 학습 흐름 (category-local survey)

아래 흐름은 database 내부에서 `primer -> deep dive -> playbook`을 잇는 category-local survey다. 처음 읽는 학습자는 각 줄을 끝까지 따라가기보다, 각 줄의 앞 2~3개 primer만 먼저 고르면 된다.

초보자용 안전 규칙은 간단하다.

- `beginner first route`만 먼저 읽는다.
- `증상이 실제로 생겼을 때만 이어서` 아래로 내려간다.
- `[playbook]`, `[runbook]`, `cutover`, `case study`가 보이면 entrypoint가 아니라 follow-up으로 읽는다.

### 1. Transaction / Locking / Invariant

beginner first route:
[Database First-Step Bridge](./database-first-step-bridge.md) -> [트랜잭션 기초](./transaction-basics.md) -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)

증상이 실제로 생겼을 때만 이어서:

[Database First-Step Bridge](./database-first-step-bridge.md) -> [트랜잭션 기초](./transaction-basics.md) -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) -> [Lost Update vs Oversell vs Duplicate Insert Beginner Bridge](./lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge.md) ->
[트랜잭션 격리수준과 락](./transaction-isolation-locking.md) -> [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md) -> [Read Committed와 Repeatable Read의 이상 현상 비교](./read-committed-vs-repeatable-read-anomalies.md) -> [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md) -> `[playbook]` [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md) -> [MVCC Snapshot vs Locking Read Portability Note](./mvcc-snapshot-vs-locking-read-portability-note.md) -> [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md) -> [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md) -> [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md) -> [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md) -> [MySQL RC Duplicate-Check Pitfall Note](./mysql-rc-duplicate-check-pitfall-note.md) -> [MySQL REPEATABLE READ Safe-Range Checklist](./mysql-repeatable-read-safe-range-checklist.md) -> [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md) -> [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md) -> [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md) -> [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md) -> [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md) -> [Hot-Path Slot Arbitration Choices](./hot-path-slot-arbitration-choices.md) -> [Reservation Reschedule and Cancellation Transition Patterns](./reservation-reschedule-cancellation-transition-patterns.md) -> [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md) -> [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md) -> [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md) -> `[playbook]` [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)

### 2. Query Plan / Index / Write Path

beginner first route:
[인덱스 기초](./index-basics.md) -> [인덱스와 실행 계획](./index-and-explain.md)

증상이 실제로 생겼을 때만 이어서:

[인덱스 기초](./index-basics.md) -> [인덱스와 실행 계획](./index-and-explain.md) -> [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) -> [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md) -> [Covering Index Width, Leaf Fanout, and Write Amplification](./covering-index-width-fanout-write-amplification.md) -> [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md) -> [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) -> [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) -> [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md) -> [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md) -> [Hot Updates, Secondary Index Churn, and Write-Path Contention](./hot-update-secondary-index-churn.md) -> `[playbook]` [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

### 3. Schema Migration / CDC / Replay

이 줄은 beginner 첫 클릭이 아니다. `cdc`, `cutover`, `replay`, `backfill`이 실제로 질문에 등장할 때만 내려간다.

[Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md) -> [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md) -> [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md) -> [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md) -> [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md) -> `[runbook]` [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md) -> [Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md)

### 4. Replica / Failover / Freshness

beginner first route:
[MVCC, Replication, Sharding](./mvcc-replication-sharding.md) -> [Replica Lag와 Read-after-Write](./replica-lag-read-after-write-strategies.md)

증상이 실제로 생겼을 때만 이어서:

[MVCC, Replication, Sharding](./mvcc-replication-sharding.md) -> [Replica Lag와 Read-after-Write](./replica-lag-read-after-write-strategies.md) -> [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md) -> [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md) -> [Monotonic Reads와 Session Guarantees](./monotonic-reads-session-guarantees.md) -> [Client Consistency Tokens](./client-consistency-tokens.md) -> [Causal Consistency Intuition](./causal-consistency-intuition.md) -> [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md) -> `[playbook]` [Replication Lag Forensics and Root-Cause Playbook](./replication-lag-forensics-root-cause-playbook.md) -> [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md) -> `[playbook]` [Failover Visibility Window, Topology Cache, and Freshness Playbook](./failover-visibility-window-topology-cache-playbook.md) -> [Commit Horizon After Failover, Loss Boundaries, and Verification](./commit-horizon-after-failover-verification.md)

### 5. Lifecycle / Cleanup / Drift

이 줄도 운영형 follow-up이다. `expired unreleased`, `cleanup lag`, `vacuum`, `purge` 같은 증상이 없으면 첫 읽기에서 미룬다.

[Soft Delete, Uniqueness, and Data Lifecycle Design](./soft-delete-uniqueness-indexing-lifecycle.md) -> [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md) -> [Active Predicate Drift in Reservation Arbitration](./active-predicate-drift-reservation-arbitration.md) -> [Active Predicate Alignment for Capacity Guards](./active-predicate-alignment-capacity-guards.md) -> [Expiry Worker Race Patterns](./expiry-worker-race-patterns.md) -> `[runbook]` [Expired-Unreleased Drift Runbook](./expired-unreleased-drift-runbook.md) -> [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md) -> [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md) -> `[runbook]` [Vacuum / Purge / Freeze Risk Triage and Runbook Routing](./vacuum-purge-freeze-risk-runbook-routing.md) -> `[playbook]` [Purge Backlog Remediation, Throttling, and Recovery Playbook](./purge-backlog-remediation-throttle-playbook.md)

## 연결해서 보면 좋은 문서 (cross-category bridge)

빠른 탐색에서는 이 구간의 subsection anchor로만 진입하고, 실제 외부 bridge 문서는 여기서 고른다.

<a id="database-bridge-transaction-app"></a>
### 트랜잭션 경계 / 애플리케이션 브리지

- `dirty read`, `lost update`, `write skew`, `phantom` 같은 DB anomaly vocabulary에서 `@Transactional`, `rollback`, `self-invocation`, `REQUIRES_NEW` 쪽으로 올라갈 때 쓰는 beginner bridge다.
- 가장 덜 흔들리는 기본 ladder는 [트랜잭션 격리수준과 락](./transaction-isolation-locking.md) -> [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md) -> [Database to Spring Transaction Master Note](../../master-notes/database-to-spring-transaction-master-note.md) -> [@Transactional 깊이 파기](../spring/transactional-deep-dive.md) -> [Spring Service Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md) -> [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md) -> `[playbook]` [Spring Transaction Debugging Playbook](../spring/spring-transaction-debugging-playbook.md) 순이다.
- `조회성 검증은 예외인가`, `draft 저장 후 승인 대기를 어디까지 허용하나`, `브로커 발행을 outbox로 넘겨야 하나`처럼 코드리뷰 판단 문장이 바로 필요하면 [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md)를 먼저 본다.
- 그다음 질문이 `느려지면 timeout부터 늘려야 하나`라면 [타임아웃 튜닝 순서 체크리스트 카드](./timeout-tuning-order-checklist-card.md)로 바로 이어 본다. 초보자용 연결 문장은 `외부 지연 -> 긴 tx -> lock wait -> pool timeout`이다.
- `readOnly`, isolation, read replica, routing datasource confusion까지 같이 보이면 [Spring Transaction Isolation / ReadOnly Pitfalls](../spring/spring-transaction-isolation-readonly-pitfalls.md), [Spring Routing Datasource: Read/Write Transaction Boundaries](../spring/spring-routing-datasource-read-write-transaction-boundaries.md)를 이어 붙인다.
- 증상이 lock wait / deadlock / pool starvation이면 Spring annotation만 보지 말고 [Deadlock Case Study](./deadlock-case-study.md), `[playbook]` [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md), [Connection Pool / Transaction Propagation / Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)로 옆 갈래를 먼저 탄다.

<a id="database-bridge-cdc-cutover"></a>
### CDC / Outbox / Read Model Cutover 브리지

- `stale read`, `read-after-write`, `projection lag`, `old data after write` alias cluster가 topic-map 없이 곧바로 database README로 들어왔을 때 붙일 category-local bridge다.
- CDC / outbox / read model cutover를 설계 언어로 확장하려면 [Read Model Cutover Guardrails](../design-pattern/read-model-cutover-guardrails.md), [Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md), [Change Data Capture / Outbox Relay](../system-design/change-data-capture-outbox-relay-design.md), [Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)을 같이 본다.

<a id="database-bridge-identity-authority"></a>
### Identity / Authority Transfer 브리지

- `authority transfer`, `SCIM deprovision`, `SCIM disable but still access`, `decision parity`, `auth shadow divergence` alias cluster의 database-side entrypoint다. security README에서는 같은 route를 `Identity / Delegation / Lifecycle`, system-design README에서는 `Database / Security Authority Bridge` -> `Verification / Shadowing / Authority Bridge`로 이어서 부른다.
- 초보자용 mental model: 이 route는 "DB row backfill이 끝났나"만 보는 곳이 아니라, "새 identity source가 같은 allow/deny 결정을 내리고 old authority path를 지워도 되는가"를 확인하는 handoff다.
- 초보자가 `SCIM disable했는데 아직 접근돼요`, `deprovision 끝났는데 access tail이 남아요`, `backfill은 끝났는데 왜 old authority가 남아요`처럼 묻는다면 database README는 `row parity` 질문을 먼저 받는 입구라고 보면 된다.

| README label | 초보자가 먼저 확인할 질문 |
|---|---|
| Database: `Identity / Authority Transfer 브리지` | row/backfill parity가 auth 결정 근거로 쓸 만큼 맞는가 |
| Security: `Identity / Delegation / Lifecycle` | session, claim, SCIM, authz cache에 old authority tail이 남는가 |
| System Design: `Database / Security Authority Bridge` | mixed-version cutover와 capability rollout을 어떻게 운영할 것인가 |
| System Design: `Verification / Shadowing / Authority Bridge` | shadow parity, decision log, audit evidence로 cleanup gate를 닫아도 되는가 |

- authority transfer route를 category README bridge 기준으로 맞추려면 [Security: Identity / Delegation / Lifecycle](../security/README.md#identity--delegation--lifecycle), [System Design: Database / Security Authority Bridge](../system-design/README.md#system-design-database-security-authority-bridge), [System Design: Verification / Shadowing / Authority Bridge](../system-design/README.md#system-design-verification-shadowing-authority-bridge)를 함께 열어 둔다. database row parity -> security authority parity -> system-design retirement gate 순서의 handoff를 고정하는 entrypoint다.
- authority transfer cutover를 database row parity 바깥까지 확장하려면 [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md), [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md), [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md), [Security: SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md)를 같이 본다.

<a id="database-bridge-retry-replay"></a>
### Retry / Idempotency / Replay 브리지

- retry / idempotency / replay 안전성을 한 축으로 묶으려면 [Retry, Timeout, Idempotency Master Note](../../master-notes/retry-timeout-idempotency-master-note.md), [Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md), `[runbook]` [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md)을 이어 읽는 편이 좋다.
- PostgreSQL `SERIALIZABLE`에서 `40001`을 service-layer whole-transaction retry로 어떻게 감싸야 하는지부터 보면 [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)가 가장 빠르다.
- Spring `CannotAcquireLockException`이나 PostgreSQL `40001`을 보고 "왜 SQL 한 줄이 아니라 트랜잭션 전체를 다시 하죠?"가 먼저 막히면 [`CannotAcquireLockException` / `40001` 혼동 FAQ](./cannotacquirelockexception-40001-insert-if-absent-faq.md)에서 `busy` / `retryable` / whole-transaction retry를 먼저 분리한다.
- 코드 리뷰에서 `retry 가능`과 `duplicate write 안전`을 바로 분리해 묻고 싶다면 [Idempotency 리뷰 문장 카드](./idempotency-review-sentence-card.md)를 먼저 붙이면 whole-transaction retry, idempotency key, outbox 질문을 짧게 복사해 쓸 수 있다.

## 현대 catalog

아래 구간은 순서대로 읽는 `survey`가 아니라 문제 축별 `deep dive catalog`다. mixed catalog에서 `[playbook]`, `[runbook]` 라벨은 step-oriented 운영 문서라는 뜻이고, 라벨이 없는 항목은 trade-off / failure-mode 중심 `deep dive`다.

## 데이터베이스

### 입문 시작점

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [트랜잭션 기초](./transaction-basics.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)

### 심화 / 운영 follow-up

이 구간은 beginner 첫 문서가 아니라, 입문 3편을 읽은 뒤 특정 증상이 붙었을 때 여는 follow-up이다.

- 동시성 증상이 붙으면 -> [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- 중복 요청 / 재시도 경계가 막히면 -> [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- 엔진 reference가 필요할 때만 -> [Real MySQL 8.0 레퍼런스](./real-mysql-8.0-reference.md)

### JDBC, JPA, MyBatis

처음 읽기는 `SQL이 어디에 보이느냐`만 분리하면 충분하다. `flush`, 예외 번역, retry boundary, pool 점유 시간은 이 섹션에서 한꺼번에 해결하려 하지 말고 "기술 구분이 끝난 뒤" follow-up으로 넘긴다.

처음 30초 판단은 아래처럼 하면 된다.

- `save()` + `@Entity`가 먼저 보이면 JPA 흔적부터 확인
- `mapper.xml`이나 `@Mapper`가 먼저 보이면 MyBatis 흔적부터 확인
- SQL 문자열이나 `PreparedStatement`가 먼저 보이면 JDBC 흔적부터 확인

| 지금 보인 단서 | beginner 첫 문서 | 바로 다음 follow-up |
|---|---|---|
| `save()`, `@Entity`, `JpaRepository` | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md) |
| `PreparedStatement`, `JdbcTemplate`, SQL 문자열 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | [JDBC 실전 코드 패턴](./jdbc-code-patterns.md) |
| `DAO`, `jdbcTemplate`, SQL 문자열 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | [JDBC 실전 코드 패턴](./jdbc-code-patterns.md) |
| "`@Transactional`도 보이고 mapper도 보여요" | [트랜잭션 기초](./transaction-basics.md) + [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md) |

- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md): `repository`, `mapper`, `entity`, `sql log` 단서로 지금 코드가 어느 접근 기술인지 먼저 잡는 beginner entrypoint
- [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md): beginner 기초에서 "SQL 위치"를 구분한 뒤 `flush`, `persistence context`, `OSIV`, self-invocation, pool 점유 시간처럼 "왜 런타임에서 이렇게 보이지?"를 설명해 주는 follow-up
- [JDBC 실전 코드 패턴](./jdbc-code-patterns.md): `PreparedStatement`, `ResultSet`, `commit/rollback`, `close()` 흐름이 직접 보일 때 여는 raw JDBC follow-up
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md): `repository`, `dao`, `entity` 용어가 기술 이름처럼 섞여 들릴 때 역할 구분부터 다시 잡는 cross-category bridge

운영/incident 계열 질문은 여기서 한꺼번에 나열하지 않는다. 아래처럼 증상 문장으로 필요한 갈래만 연다.

- "`@Transactional`도 보이고 retry도 꼬여요" -> [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md)
- "`save()`는 되는데 lock timeout/deadlock 예외 이름이 너무 많아요" -> [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- "`PESSIMISTIC_WRITE`를 걸었는데 범위 경쟁이 안 막혀요" -> [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md)
- 중복 요청 / 재시도 / outbox까지 같이 얽히면 -> [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md), [Idempotency 리뷰 문장 카드](./idempotency-review-sentence-card.md)

### 트랜잭션 격리수준과 락

처음 읽기는 `트랜잭션 기초 -> 트랜잭션 격리 수준 기초 -> 락 기초`까지만 잡아도 충분하다. 엔진 차이, retry, empty-result locking, playbook은 증상이 붙을 때만 아래 follow-up으로 내려간다.
초보자 기준 빠른 규칙은 하나다. `commit/rollback`이 막히면 primer로, `deadlock`/`40001`/`FOR UPDATE 0 row`가 막히면 follow-up으로 간다.

- [트랜잭션 기초](./transaction-basics.md): `commit`/`rollback` 범위를 먼저 잡는 beginner primer
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md): dirty read, 같은 row 재조회, 범위 재조회가 왜 다른 질문인지 분리하는 beginner primer
- [락 기초](./lock-basics.md): plain `SELECT`와 locking read, optimistic/pessimistic lock을 처음 나누는 beginner primer
- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md): beginner primer 다음에 ACID, `@Transactional isolation`, `SELECT ... FOR UPDATE`, JPA/JDBC 연결을 한 번에 훑는 심화 entry
- [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md): dirty read, non-repeatable read, lost update, write skew, phantom을 isolation level과 guardrail confusion 축으로 한 장에 정리한 beginner entry
- [Read Committed와 Repeatable Read의 이상 현상 비교](./read-committed-vs-repeatable-read-anomalies.md): `READ COMMITTED`와 `REPEATABLE READ`가 관측 일관성에 어떤 차이를 만드는지 비교
- [PostgreSQL vs MySQL Isolation Cheat Sheet](./postgresql-vs-mysql-isolation-cheat-sheet.md): `READ COMMITTED`, `REPEATABLE READ`, `SERIALIZABLE`이 PostgreSQL과 MySQL에서 왜 같은 이름인데도 다른 직관을 만드는지 비교
- [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md): `0 row FOR UPDATE`가 왜 absence check를 보호하지 못하는지, PostgreSQL과 MySQL 차이를 exact duplicate / overlap 예제로 설명하는 beginner entry
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md): exact duplicate check에서 RR next-key가 언제 same-key insert를 막아 주는지, RC 전환이나 chosen index path 변화에서 왜 직관이 깨지는지 보여주는 beginner bridge
- [MySQL RC Duplicate-Check Pitfall Note](./mysql-rc-duplicate-check-pitfall-note.md): RR에서 안전해 보이던 exact-key duplicate pre-check가 RC 전환 뒤 duplicate race와 duplicate-key error를 더 많이 드러내는 이유를 설명하는 beginner note
- `[playbook]` [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md): PostgreSQL SSI에서 `40001`이 왜 정상 경쟁 결과인지, retry loop를 왜 `@Transactional` 바깥에 두어야 하는지 beginner 기준으로 정리
- [MVCC Snapshot vs Locking Read Portability Note](./mvcc-snapshot-vs-locking-read-portability-note.md): plain `SELECT`, locking read, `UPDATE`/`DELETE`가 PostgreSQL과 MySQL에서 같은 visibility 규칙을 따르지 않는다는 점을 portability 관점에서 정리
- [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md): `same row / different row / new row` 기준으로 세 anomaly를 beginner 관점에서 한 번에 분리
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md): InnoDB가 phantom을 줄이기 위해 row 바깥의 gap까지 어떻게 잠그는지 설명
- [MySQL REPEATABLE READ Safe-Range Checklist](./mysql-repeatable-read-safe-range-checklist.md): absence check, overlap probe, index-path assumption이 언제 RR next-key에 기대도 되는지 검증하는 checklist
- [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md): optimistic/pessimistic locking을 충돌 빈도와 retry 비용 기준으로 고르는 법
- [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md): version column flush SQL, `SELECT ... FOR UPDATE` 매핑, retry boundary를 Spring facade/transactional service 기준으로 정리
- [JPA `PESSIMISTIC_WRITE`의 범위 잠금 한계와 전환 기준](./range-locking-limits-jpa.md): empty-result locking 착시, overlap query의 predicate 누수, capacity invariant에서 detail-row lock 대신 constraint/guard row로 옮기는 기준을 정리
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md): deadlock과 lock timeout이 MyBatis/JDBC, Hibernate/JPA, Spring DAO 예외에서 서로 다르게 surface되는 이유와 `SQLSTATE/errno` 기준 bounded retry 분류를 정리
- [Version Column Retry Walkthrough](./version-column-retry-walkthrough.md): `@Version` 충돌이 `UPDATE ... WHERE version = ?` 실패에서 rollback-only transaction, `409 Conflict`, 사용자 안내문까지 어떻게 전파되는지 beginner 기준으로 단계별 설명
- [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md): `@Retryable`이 fresh transaction per attempt를 보장하는 조건, self-invocation으로 advice가 사라지는 경우, `REQUIRES_NEW`가 retry 복구가 아니라 별도 commit이 되는 함정을 정리
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [MySQL Empty-Result Locking Reads](./mysql-empty-result-locking-reads.md): `FOR UPDATE` / `FOR SHARE`가 `0 row`를 돌려줄 때 남는 보호가 logical nonexistence 전체가 아니라 scanned gap/next-key라는 점을 정리
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md): pre-seeded guard row와 ordered upsert-plus-lock을 비교하고, exact-PK lock 재획득이 왜 필요한지 정리
- [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md): `room_type_id + stay_day` pooled inventory에서 sell-time day guard, ledger, later unit assignment를 어떤 invariant로 나눌지 정리
- [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md): hot aggregate row를 striped guard row, counter shard, ledger projection으로 분산하는 판단 기준
- [Hot-Path Slot Arbitration Choices](./hot-path-slot-arbitration-choices.md): slot unique key, `resource-day` guard row, hybrid fencing이 high-contention booking에서 각각 어떤 queue shape를 만드는지 비교
- [Foreign Key Cascade Lock Surprises](./foreign-key-cascade-lock-surprises.md)
- `[playbook]` [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Savepoint Rollback, Lock Retention, and Escalation Edge Cases](./savepoint-lock-retention-edge-cases.md)
- [Savepoint + Lock Retention Incident Scenarios and Recovery Patterns](./savepoint-lock-retention-incident-scenarios.md)
- [Aggregate Boundary vs Transaction Boundary](../design-pattern/aggregate-boundary-vs-transaction-boundary.md)

### 인덱스와 실행 계획

- [인덱스 기초](./index-basics.md): `인덱스가 뭐예요`, `왜 인덱스 안 타요`, `full table scan` 같은 첫 질문을 푸는 beginner primer
- [인덱스와 실행 계획](./index-and-explain.md): `EXPLAIN key/rows/Extra/type`, `type = ALL`, `key = NULL`, `Using filesort` 같은 두 번째 해석 순서를 잡고 "인덱스 부재 vs 정렬 미스 vs 통계 흔들림"을 가르는 bridge
- [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md): InnoDB clustered-index 직관이 왜 PostgreSQL heap + index 저장 구조와 1:1로 대응하지 않는지, PostgreSQL `CLUSTER`가 one-time reorder 도구일 뿐 InnoDB 기본 저장 모델과 같지 않다는 점까지 초급 눈높이로 이어 주는 bridge
- [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md): `Using index`, `Using filesort`, `ORDER BY ... LIMIT`, left-prefix 같은 index shape 질문을 다루는 entry
- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md): MySQL `Using index`와 PostgreSQL `Index Only Scan`, `Heap Fetches`, visibility map처럼 "커버링 설계"와 "실제 heap/table 생략 실행"을 분리하는 entry
- [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md): `Extra` 컬럼에 찍히는 `Using filesort`, `Using temporary`, `ICP`를 symptom 중심으로 해석하고, `type = ALL` / `key = NULL`이면 primer·checklist로 되돌리는 entry
- [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md): `rows` 추정치 흔들림, `EXPLAIN ANALYZE` actual rows mismatch, stale stats 기반 plan drift를 읽고 `Using filesort` / `key = NULL` 주증상이면 다른 entry로 되돌리는 entry
- [Optimizer Trace Reading](./optimizer-trace-reading.md): `EXPLAIN` 결과는 읽었는데 왜 full scan, `key = NULL`, `Using filesort` 같은 선택이 나왔는지 optimizer 내부 cost 판단으로 drill-down하는 entry
- [Sort Buffer, Temporary Table, and Spill Behavior](./sort-buffer-temp-table-spill.md): `Using filesort`, `Using temporary`가 실제로 memory에서 끝나는지 disk spill로 번졌는지, `Created_tmp_disk_tables` / `Sort_merge_passes`로 보는 follow-up entry
- [Temporary Table Engine Choice and Spill Behavior](./temp-table-engine-choice-spill-behavior.md): `Using temporary` 이후 internal temp table 경로와 disk fallback 조건을 분리하는 follow-up entry
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md): booking overlap probe에서 composite index shape가 scan axis와 lock footprint를 어떻게 바꾸는지 정리
- [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md)
- [Covering Index Width, Leaf Fanout, and Write Amplification](./covering-index-width-fanout-write-amplification.md): `Using index`는 보이는데도 느리다, covering 때문에 index가 너무 넓어졌다, write amplification이나 buffer pool pressure가 커졌다는 follow-up을 다루는 entry
- [Hot Updates, Secondary Index Churn, and Write-Path Contention](./hot-update-secondary-index-churn.md)

### B+Tree vs LSM-Tree

- [B+Tree vs LSM-Tree](./bptree-vs-lsm-tree.md)

### MySQL Optimizer Hints and Index Merge

- [MySQL Optimizer Hints and Index Merge](./mysql-optimizer-hints-index-merge.md)

### MVCC, Replication, Sharding

- [MVCC, Replication, Sharding](./mvcc-replication-sharding.md): `snapshot`, `replica lag`, `partitioning vs sharding`, `hot shard`처럼 자주 섞이는 용어를 primer로 먼저 푼다

### 트랜잭션 실전 시나리오

- [트랜잭션 실전 시나리오](./transaction-case-studies.md)
- [Lost Update vs Oversell vs Duplicate Insert Beginner Bridge](./lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge.md): `마지막 재고`, `중복 insert`, `duplicate key` 같은 증상을 anomaly 이름보다 먼저 분리하는 beginner entry
- [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md): shared scenario와 결정 맵으로 lost update, write skew, phantom을 먼저 분리하는 entry
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)
- [Deadlock Case Study](./deadlock-case-study.md)

### Outbox, Saga, Eventual Consistency

- [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)

### Deadlock Case Study

- [Deadlock Case Study](./deadlock-case-study.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md): multi-day / multi-resource 예약에서 canonical lock ordering, union lock, retry 분리를 어떻게 설계할지 정리
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md): guard row를 미리 심는 경우와 런타임 생성하는 경우의 deadlock surface 차이를 비교

### JDBC 실전 코드 패턴

- [JDBC 실전 코드 패턴](./jdbc-code-patterns.md): `PreparedStatement`, `ResultSet`, `setAutoCommit(false)`, `commit/rollback`, `getConnection` / `close`를 "connection을 빌리고 반납하는 순서"로 읽게 해 주는 raw JDBC follow-up. `PreparedStatement`는 보이는데 흐름이 안 잡힐 때만 연다

### Connection Pool, Transaction Propagation, Bulk Write

- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md): `@Transactional propagation`, `REQUIRED vs REQUIRES_NEW`, `hikaricp pool exhausted`, `jpa long transaction`, `external call in transaction`, `connection borrow/return`, `close returns to pool`, `batch chunk commit` 같은 JDBC/JPA 운영 경계 entry

### HikariCP 튜닝

- [HikariCP 튜닝](./hikari-connection-pool-tuning.md): `maximumPoolSize`, `connectionTimeout is not query timeout`, `getConnection` / borrow timeout, `Connection is not available`, `leakDetectionThreshold`, `connection leak detection triggered`, `apparent connection leak detected`, `pool exhaustion`, `threads awaiting connection` 같은 Hikari 운영 alias를 설정값/증상/오탐 구분으로 묶는 entry

### 멱등성 키와 중복 방지

- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md): `duplicate key` / `lock timeout` / `deadlock` / `40001`을 `already exists` / `busy` / `retryable`로 먼저 번역해, "왜 결과가 매번 다르죠?" 같은 초보자 질문을 한 장에서 정리하는 entry
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md): single-key dedup, slot claim, 대표 guard queue 중 어디에 insert-if-absent 충돌을 모을지 고르는 beginner entry
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md): `ON CONFLICT` / `ON DUPLICATE KEY UPDATE`를 guard creation과 canonical lock ordering 관점에서 비교
- `[runbook]` [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [Token Misuse Detection / Replay Containment](../security/token-misuse-detection-replay-containment.md)

### 쿼리 튜닝 체크리스트

- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md): `type = ALL` vs `Using filesort` vs `rows` mismatch vs app bottleneck을 한 순서로 분리하는 triage entry

### SQL 조인과 쿼리 실행 순서

- [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)

### Schema Migration, Partitioning, CDC, CQRS

- [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
- [Projection Rebuild, Backfill, and Cutover Pattern](../design-pattern/projection-rebuild-backfill-cutover-pattern.md)
- [Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)
- [Event Upcaster Compatibility Patterns](../design-pattern/event-upcaster-compatibility-patterns.md)
- [Change Data Capture / Outbox Relay](../system-design/change-data-capture-outbox-relay-design.md)
- [Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md)
- [Zero-Downtime Schema Migration Platform](../system-design/zero-downtime-schema-migration-platform-design.md)
- [Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)
- [Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- `[playbook]` [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md)
- `[playbook]` [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md)
- [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md): slot claim table에서 create/cancel/reschedule delta, union lock, tombstone cleanup watermark를 어떻게 맞출지 정리
- [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)
- `[playbook]` [CDC Schema Evolution, Event Compatibility, and Expand-Contract Playbook](./cdc-schema-evolution-compatibility-playbook.md)
- [Destructive Schema Cleanup, Column Retirement, and Contract-Phase Safety](./destructive-schema-cleanup-column-retirement.md)

### Multi-Tenant Table Design

- [Multi-Tenant Table Design, Tenant-First Indexing, and Hotspot Control](./multi-tenant-tenant-id-index-topology.md)
- [Multi-Tenant Statistics Skew, Plan Drift, and Query Isolation](./multi-tenant-stats-skew-plan-isolation.md)
- `[playbook]` [Hot Tenant Split-Out, Routing, and Cutover Playbook](./tenant-split-out-routing-cutover-playbook.md)

### 온라인 스키마 변경 전략

- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- `[runbook]` [gh-ost / pt-online-schema-change Cutover Precheck Runbook](./gh-ost-pt-osc-cutover-precheck-runbook.md)
- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)
- `[playbook]` [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md)
- `[playbook]` [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md)
- `[playbook]` [Index Maintenance Window, Rollout, and Fallback Playbook](./index-maintenance-window-rollout-playbook.md)
- `[runbook]` [Metadata Lock Outage Triage, Cancel, and Recovery Runbook](./metadata-lock-outage-triage-cancel-recovery.md)

### Authority Transfer / Security Bridge

`authority transfer`, `SCIM deprovision`, `SCIM disable but still access`, `decision parity`, `auth shadow divergence`, `deprovision tail`이 같이 보이면 schema migration이 identity/session/authz authority 이전과 엮인 상황이다.
row parity만으로는 승격을 닫을 수 없다.
이 section은 `deep dive` 본문이 아니라 category-local bridge다. 세부 원인은 아래 개별 문서로 내려가고, route label은 위 `Identity / Authority Transfer 브리지`와 같은 축으로 읽는다.
읽는 순서를 README bridge entrypoint 기준으로 맞추려면 위 [Identity / Authority Transfer 브리지](#database-bridge-identity-authority), [Security: Identity / Delegation / Lifecycle](../security/README.md#identity--delegation--lifecycle), [System Design: Database / Security Authority Bridge](../system-design/README.md#system-design-database-security-authority-bridge), [System Design: Verification / Shadowing / Authority Bridge](../system-design/README.md#system-design-verification-shadowing-authority-bridge)를 같이 본다.

- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)
- [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md)
- [Security: SCIM Drift / Reconciliation](../security/scim-drift-reconciliation.md)
- [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
- [Security: SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md)
- [System Design: Session Store / Claim-Version Cutover 설계](../system-design/session-store-claim-version-cutover-design.md)
- [Security: AuthZ Decision Logging Design](../security/authz-decision-logging-design.md)
- [Security: Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)

### 느린 쿼리 분석 플레이북

- `[playbook]` [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

### Redo Log, Undo Log, Checkpoint, Crash Recovery

- [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)

### Index Condition Pushdown, Filesort, Temporary Table

- [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md): `Using filesort`, `Using temporary`, `ICP`, `index exists but order by slow` 같은 EXPLAIN symptom을 맡고, `type = ALL` / `key = NULL`이면 [인덱스와 실행 계획](./index-and-explain.md)·[쿼리 튜닝 체크리스트](./query-tuning-checklist.md)로 다시 보내는 entry

### Statistics, Histograms, and Cardinality Estimation

- [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md): `rows estimate wrong`, `EXPLAIN ANALYZE actual rows mismatch`, `plan drift after deploy`, `stale statistics`, `histogram skew` 같은 통계 symptom을 맡고, `Using filesort` / `Using temporary` / `key = NULL` 주증상이면 primer·checklist·`Extra` entry로 다시 보내는 entry

### Replica Lag와 Read-after-Write

- `stale read`, `read-after-write`, `projection lag`, `old data after write`, `save succeeded but old value returned` 같은 freshness alias를 database 내부 read path로 먼저 좁히는 subsection이다.
- [Replica Lag와 Read-after-Write](./replica-lag-read-after-write-strategies.md): `write succeeded read is stale`, `생성 직후 데이터 안 보임`, `replica delay after write`처럼 write 직후 freshness budget이 먼저 문제일 때 시작점
- [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md): `cache miss stale replica`, `cache invalidation vs replica lag`, `목록과 상세가 서로 다른 상태`처럼 stale source 분리부터 해야 할 때
- [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md): `내가 바꾼 값이 안 보임`, `refresh after edit shows old value`, `recent write primary fallback`처럼 세션 단위 최신성 보장이 핵심일 때
- [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md): `sometimes old sometimes new`, `retry changed result`, `pagination duplicates across replicas`처럼 replica selection 흔들림을 먼저 의심할 때
- [Monotonic Reads와 Session Guarantees](./monotonic-reads-session-guarantees.md): `saw newer then older`, `same session sees older data`, `read goes backward`처럼 freshness 다음 단계의 session-consistency 회귀를 설명할 때
- [Client Consistency Tokens](./client-consistency-tokens.md): `multi-tab stale read`, `same account different device old data`, `X-Consistency-Token`처럼 서버 세션 밖으로 최신선을 운반해야 할 때
- [Causal Consistency Intuition](./causal-consistency-intuition.md): `comment visible before post`, `payment visible before order`, `cause before effect`처럼 인과 순서까지 맞춰야 할 때
- [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md): `freshness alert threshold`, `lag metric은 있는데 언제 primary fallback해야 하나`, `failover 전 lag routing 기준`처럼 steady-state 관측과 정책 경계가 핵심일 때
- `[playbook]` [Replication Lag Forensics and Root-Cause Playbook](./replication-lag-forensics-root-cause-playbook.md)
- [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md): `failover는 끝났는데 화면마다 값이 다름`, `old primary still serving reads`, `promotion 후 일부 요청만 옛 endpoint`처럼 승격 직후 read authority split을 설명할 때
- `[playbook]` [Failover Visibility Window, Topology Cache, and Freshness Playbook](./failover-visibility-window-topology-cache-playbook.md): `some pods old some new`, `topology cache stale`, `DNS TTL after promotion`, `failover cache bust`처럼 invalidation / pinning / telemetry 액션이 바로 필요할 때
- [Commit Horizon After Failover, Loss Boundaries, and Verification](./commit-horizon-after-failover-verification.md): `새 primary에 실제로 최근 write가 없는지`, `write loss vs stale read`를 가를 때

### CDC, Debezium, Outbox, Binlog

- [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)
- `[playbook]` [CDC Schema Evolution, Event Compatibility, and Expand-Contract Playbook](./cdc-schema-evolution-compatibility-playbook.md)
- [CDC Backpressure, Binlog/WAL Retention, and Replay Safety](./cdc-backpressure-binlog-retention-replay.md)
- `[playbook]` [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)
- `[runbook]` [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md)
- [Replay / Repair Orchestration Control Plane](../system-design/replay-repair-orchestration-control-plane-design.md)
- [Reconciliation Window / Cutoff Control](../system-design/reconciliation-window-cutoff-control-design.md)

### Queue / Claim Patterns

- [Queue Consumer Transaction Boundaries](./queue-consumer-transaction-boundaries.md)
- [Queue Claim with `SKIP LOCKED`, Fairness, and Starvation Trade-offs](./queue-claim-skip-locked-fairness.md)
- [Transactional Claim-Check와 Job Leasing](./transactional-claim-check-job-leasing.md)
- [Expiry Worker Race Patterns](./expiry-worker-race-patterns.md): confirm callback, expiry worker, next claim path가 같은 hold를 finalize할 때 row lock, version column, claim-path finalization을 어떻게 조합할지 비교

### Offset vs Seek Pagination

- [Offset vs Seek Pagination](./pagination-offset-vs-seek.md)

### Write Skew와 Phantom Read 사례

- [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md): lost update까지 함께 놓고 `same row / different row / new row`로 anomaly 구분을 먼저 잡는 beginner entry
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md): 부재 기반 판단이 어떻게 minimum staffing, capacity, overlap race로 이어지는지 사례 중심으로 정리
- [Write Skew Detection과 Compensation Patterns](./write-skew-detection-compensation-patterns.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md): guard row, slotization, ledger로 range/set invariant를 저장 시점에 강제하는 패턴
- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md): exact key, discrete slot, 대표 guard queue 중 어느 충돌 surface가 맞는지 빠르게 고르는 beginner primer
- [Phantom-Safe Booking Patterns Primer](./phantom-safe-booking-patterns-primer.md): `unique-slot`, exclusion constraint, guard row를 booking overlap의 시간 모델, 엔진 제약, queue shape 기준으로 비교하는 빠른 entry
- [Guard Row vs Serializable Retry vs Reconciliation for Set Invariants](./guard-row-vs-serializable-vs-reconciliation-set-invariants.md): count/sum invariant에서 guard row, bounded retry, reconciliation을 언제 조합할지 결정하는 가이드
- `[playbook]` [Serializable Retry Telemetry for Set Invariants](./serializable-retry-telemetry-set-invariants.md): serializable 보호를 쓰는 minimum staffing, quota path에서 retry budget, SQLSTATE 분류, hot key 알람을 어떻게 잡을지 정리
- [Active Predicate Alignment for Capacity Guards](./active-predicate-alignment-capacity-guards.md): expirable hold가 있는 capacity path에서 `expires_at`, `released_at`, `deleted_at` 해석을 admission check, guard row, reconciliation scan에 똑같이 맞추는 contract
- [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md): guard row 하나가 hotspot이 된 capacity path에서 striped budget, shard counter, ledger fallback을 어떻게 고를지 정리
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md): `(resource)` vs `(resource, day)` guard scope, old/new scope union lock, multi-resource canonical ordering을 비교
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md): bounded key space에서 pre-seed를 택할지, sparse key space에서 ordered upsert-plus-lock을 택할지 비교
- [Hot-Path Slot Arbitration Choices](./hot-path-slot-arbitration-choices.md): slot unique key, `resource-day` guard row, hybrid fencing이 high-contention booking path에서 패배 요청을 어떻게 처리하는지 비교
- [Reservation Reschedule and Cancellation Transition Patterns](./reservation-reschedule-cancellation-transition-patterns.md): extend, shorten, move, cancel, expiry cleanup, admin override를 reservation-local fence, `scope_delta`, union lock으로 묶는 전이 contract
- [Slot Delta Reschedule Semantics](./slot-delta-reschedule-semantics.md): slot claim table로 내려갔을 때 `scope_delta`를 create/cancel/reschedule delta, slot guard union lock, tombstone cleanup으로 어떻게 구체화할지 정리
- [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md): room-type pooled inventory를 sell-time day guard, replay ledger, later `room_id + stay_day` assignment로 어떻게 분리할지 정리
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md): overlap probe에서 equality prefix, `start_at`/`end_at` scan axis, active prefix가 lock footprint를 어떻게 바꾸는지 비교
- [MySQL REPEATABLE READ Safe-Range Checklist](./mysql-repeatable-read-safe-range-checklist.md): absence check, overlap probe, index-path assumption을 one-page checklist로 묶어 RR next-key 가정을 검증한다
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md): `FOR UPDATE` overlap probe가 왜 RC에서 empty-result phantom을 다시 허용하는지 설명
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md): equality dimension, range boundary, active predicate, `23P01` 대응까지 포함한 overlap guardrail
- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md): hold expiry, `released_at`, soft delete lag가 active predicate drift로 번지는 경로를 정리
- [Active Predicate Drift in Reservation Arbitration](./active-predicate-drift-reservation-arbitration.md): `HELD`/`CONFIRMED`/`BLACKOUT`/`EXPIRED`를 booking, blackout, cleanup path가 같은 overlap conflict set으로 해석하게 만드는 contract
- `[runbook]` [Expired-Unreleased Drift Runbook](./expired-unreleased-drift-runbook.md): deadline이 지난 expirable blocker를 count, lag bucket, false blocker scope, bounded batch repair로 운영 복구하는 절차
- [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md): active row 존재 여부를 blocking truth로 만들고 종료 row는 history로 보내는 split 기준과 transition contract를 정리
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md): PostgreSQL은 exclusion constraint, MySQL은 slot row/next-key locking/guard row로 규칙을 어떻게 번역할지 정리
- `[playbook]` [Slotization Precheck Queries for Overlaps, Rounding Collisions, and DST Boundaries](./slotization-precheck-overlap-rounding-dst.md): cutover 전 overlap pair, rounding-only collision, DST fold/gap을 어떤 쿼리와 slot calendar로 가를지 정리
- `[playbook]` [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md): interval predicate 기반 예약 모델을 slot claim table로 옮길 때 split-brain writer, catch-up lag, reschedule union lock을 어떻게 통제할지 정리

### Vacuum / Purge Debt

- `[runbook]` [Vacuum / Purge / Freeze Risk Triage and Runbook Routing](./vacuum-purge-freeze-risk-runbook-routing.md)
- [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)
- `[playbook]` [Autovacuum Freeze Debt, XID Age, and Wraparound Playbook](./autovacuum-freeze-debt-wraparound-playbook.md)
- `[playbook]` [Purge Backlog Remediation, Throttling, and Recovery Playbook](./purge-backlog-remediation-throttle-playbook.md)

### 정규화와 반정규화 트레이드오프

- [정규화와 반정규화 트레이드오프](./normalization-denormalization-tradeoffs.md)

### Summary Maintenance and Drift Repair

- [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)
- [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)

### Soft Delete와 Data Lifecycle

- [Soft Delete, Uniqueness, and Data Lifecycle Design](./soft-delete-uniqueness-indexing-lifecycle.md)
- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md): `deleted_at`과 `released_at`을 분리해 expiry cleanup lag가 active set 판단을 오염시키지 않게 하는 방법
- [Active Predicate Drift in Reservation Arbitration](./active-predicate-drift-reservation-arbitration.md): `HELD`/`CONFIRMED`/`BLACKOUT`/`EXPIRED` lifecycle drift가 overlap arbitration까지 번지지 않게 booking, blackout, cleanup path를 같은 canonical blocker predicate로 맞추는 방법
- [Active Predicate Alignment for Capacity Guards](./active-predicate-alignment-capacity-guards.md): capacity guard가 `expires_at`, `released_at`, soft-delete를 서로 다른 active predicate로 해석하지 않게 맞추는 admission/reconciliation contract
- `[runbook]` [Expired-Unreleased Drift Runbook](./expired-unreleased-drift-runbook.md): deadline이 지난 row가 reads/constraints를 계속 막을 때 detection query, release-lag SLO, chunked repair 순서를 정리
- [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md): active hold와 archive/history를 분리해 `deleted_at` 없이 live uniqueness와 overlap truth를 유지하는 패턴

## 레거시 primer / reference

아래 구간은 전통적인 DB primer와 면접/교재형 reference 성격이 강한 본문이다.

### 데이터베이스 용어 정리

#### 긍정적 단어 😃

- **독립성 (Data Independence)**
    - 논리적 독립성 : 응용 프로그램과 데이터베이스를 독립시킴으로써, 데이터의 논리적 구조를 변경시키더라도 응용 프로그램은 변경되지 않는다.
    - 물리적 독립성 : 응용 프로그램과 보조기억장치 같은 물리적 장치를 독립시킴으로써, 데이터베이스 시스템의 성능 향상을 위해 새로운 디스크를 도입하더라도 응용 프로그램에는 영향을 주지 않고 데이터의 물리적 구조만을 변경한다.
- **무결성 (Data Integrity)** : 삽입, 삭제, 갱신 등의 연산 후에도 데이터베이스에 저장된 데이터가 정해진 제약 조건을 항상 만족해야 한다.
- **일관성 (Data Consistency)** : 데이터베이스에 저장된 데이터와 특정 질의에 대한 응답이 변함 없이 일정해야 한다.

#### 부정적 단어 🙁

- **종속성 (Data Dependency)** : (⇔ 독립성) 응용 프로그램의 구조가 데이터의 구조에 영향을 받는다.
- **중복성 (Data Redundancy)** : 같은 데이터가 중복되어 저장되는 것으로, 데이터 수정/삭제 시 연결된 모든 데이터를 수정/삭제해줘야 하는 문제점이 있다.
- **비일관성 (Data Inconsistency)** : 동일한 데이터의 여러 사본이 서로 다른 값을 보유하고 있는 상태로, 데이터 중복성에 이어서 발생할 수 있다.

### 데이터베이스 시스템의 목적

데이터베이스 시스템이 등장하기 전까지는 운영체제의 의해 지원되는 파일 시스템을 통해 데이터를 관리하였다. 이 때 여러가지 문제점이 존재하는데, 데이터베이스 시스템의 목적은 이 문제점을 해결하기 위하는 데 있다. **파일 시스템을 사용했을 때의 주요 문제점**은 다음과 같다.

- 데이터의 중복과 비일관성
- 데이터 접근 시 필요한 데이터를 편리하고 효율적으로 검색하기 힘들다.
- 데이터가 여러 파일에 흩어져 있고 파일 형식이 서로 다를 수 있다.
- 데이터 동시 접근 시 데이터가 잘못 업데이트될 수 있다.
- 무결성 문제
- 보안 문제

데이터베이스는 여러 사람들이 공유하여 사용할 목적으로 체계화해 통합, 관리하는 데이터의 집합을 말한다. DBMS를 통해 요구를 처리하고, SQL을 사용해 데이터에 접근한다. **데이터베이스**는 다음의 **장점**을 가진다.

- 데이터의 논리적, 물리적 독립성, 일관성, 무결성, 보안성 보장
- 데이터 중복 최소화
- 저장된 자료를 공동으로 이용할 수 있다.
- 데이터를 통합하여 관리할 수 있다.
- 데이터의 실시간 처리가 가능하다.

한편 **단점**도 존재한다.

- 전산화 비용이 증가한다.
- 대용량 디스크로의 집중적인 Access로 과부하(Overhead)가 발생할 수 있다.

### 관계형 데이터베이스 시스템 (RDBMS)

RDBMS는 테이블 기반(Table based) DBMS로, 테이블들의 집합으로 데이터들의 관계를 표현한다.

- 데이터를 테이블 단위로 관리
- 중복 데이터 최소화 (정규화)
- 여러 테이블에 분산되어 있는 데이터를 검색 시 테이블 간의 관계(join)를 이용해 필요한 데이터를 검색

### 데이터베이스 언어

#### DDL (Data Definition Language) : 데이터 정의어

- CREATE, ALTER, DROP, RENAME
- 데이터베이스 객체(table, view, index...)의 구조를 정의 (생성, 변경, 제거)

#### DML (Data Manipulation Language) : 데이터 조작어

- INSERT, SELECT, UPDATE, DELETE
- 데이터베이스 테이블의 레코드를 CRUD (Create, Read, Update, Delete)

#### DCL (Data Control Language) : 데이터 제어어

- GRANT, REVOKE
- 데이터베이스와 그 구조에 대한 접근 권한을 제공하거나 제거

#### TCL (Transaction Control Language) : 트랜잭션 제어어

- COMMIT, ROLLBACK, Savepoint
- DML 명령문으로 수행한 변경을 관리 (트랜잭션 관리)

---

## 정규화

정규화란 **함수의 종속성 이론**을 통해 데이터의 중복성을 최소화하고 일관성 등을 보장하여 데이터베이스의 품질과 성능을 향상키시는 과정이다. 정규화 수준이 높을수록 유연한 데이터 구축이 가능하고 데이터의 정확성이 높아지는 반면, 물리적 접근이 복잡하고 너무 많은 조인으로 인해 조회 성능이 저하된다는 특징이 있다

### 정규화의 목적

- 데이터 구조의 안정성과 무결성을 유지한다
- 데이터 모형의 단순화가 가능하다
- 효과적인 검색 알고리즘을 생성할 수 있다
- 데이터 중복을 배제하여 `이상(Anomaly)` 발생을 방지하고 저장 공간을 최소화한다

### 이상(Anomaly)의 개념 및 종류

정규화를 거치지 않으면 **데이터베이스 내에 데이터들이 불필요하게 중복**되어 릴레이션 조작 시 문제가 생기는데, 이를 이상이라고 하며
삽입 이상, 삭제 이상, 갱신 이상이 있다

- **삽입 이상** (Insertion Anomaly) : 데이터를 삽입할 때 원하지 않은 값들도 함께 삽입되는 현상
- **갱신 이상** (Update Anomaly) : 데이터를 수정할 때 일부 튜플의 정보만 갱신되어 정보에 모순이 생기는 현상
- **삭제 이상** (Deletion Anomaly) : 데이터를 삭제할 때 의도와는 상관 없는 값들도 함께 삭제되는 현상

### 정규화 과정

#### 1NF(제 1 정규형)

릴레이션에 속한 모든 도메인이 원자값만으로 되어있는 정규형이다

#### 2NF(제 2 정규형)

1NF를 만족하고, 부분 함수적 종속을 제거하여 기본키가 아닌 모든 속성이 기본키에 대하여 완전 함수적 종속을 만족하는 정규형이다

```bash
완전 함수적 종속 : 만약 (속성 A, 속성 B) -> 속성 C 일때, A->C, B->C 모두 성립될때 완전 함수적 종속이라 한다
부분 함수적 종속 : 만약 (속성 A, 속성 B) -> 속성 C 일때, A->C, B->C 중 하나만 성립될때(모두 성립 x) 부분 함수적 종속이라 한다
```

#### 3NF(제 3 정규형)

2NF를 만족하고, 이행적 함수 종속을 제거하는 정규형이다

```bash
이행적 종속 : A -> B, B -> C 의 종속관계에서 A -> C를 만족하는 관계를 의미한다
```

#### BCNF(Boyce-Codd 정규형)

결정자가 모두 후보키인 정규형이다.(후보키가 아닌 결정자를 제거하는 정규형이다)
</br>

[BCNF의 제약 조건]
- 키가 아닌 모든 속성은 각 키에 대하여 완전 종속해야 한다
- 키가 아닌 모든 속성은 그 자신이 부분적으로 들어가 있지 않은 모든 키에 대해 완전 종속해야 한다
- 어떤 속성도 키가 아닌 속성에 대해서는 완전 종속 할 수 없다

```bash
결정자 : 다른 속성을 고유하게 결정하는 하나 이상의 속성 (속성 간의 종속성을 규명할 때 기준이 되는 값)
종속자 : 결정자의 값에 의해 정해지는 값
후보키 : 테이블에서 각 행을 유일하게 식별할 수 있는 최소한의 속성들의 집합  
```

#### 4NF(제 4 정규형)

다치 종속을 제거하는 정규형이다.

```bash
다치 종속 : 속성 A -> (속성 B, 속성 C) 일때, A->B를 만족하고, **B와 C가 무관**할때 B는 A에 다치종속 관계라고 하며, A->>B 라고 한다. 

다치종속을 제거하지 않으면 A->>B 상황에서 C값이 중복될수 있다.
예를들어,

(회원번호)-> (이름, 주문번호) 인 테이블에서
(회원번호 ->> 주문번호) 일때,

흐쟈미란 고객이 책을 두번 주문하면 흐쟈미 이름이 불필요하게 두번 중복된다.
이를 해결하기 위해서는 (회원번호->이름), (회원번호->주문번호)로 쪼개주는것이 제 4정규형이다.
```

#### 5NF (제 5 정규형)

릴레이션 R의 모든 조인종속이 R의 후보키를 통해서만 성립되는 정규형이다.

```bash
한 테이블을 분해했다가 분해된 결과들을 다시 조인하면 당연히 원래의 테이블로 복원된다고 기대하지만 그렇지 못한 경우가 있다.
다시 조인하면 예상하지 못했던 튜플들이 생성되는 경우가 발생한다.

조인 종속 :  테이블을 분해한 결과를 다시 조인했을 때 원래의 테이블과 동일하게 복원되는 제약조건이다.
```

<details>
<summary>5NF를 실시하는 이유 예시로 보기</summary>  
<p>

> "다시 조인하면 예상하지 못했던 튜플들이 생성되는 경우"

릴레이션 R이 다음과 같을때,

|A|B|C|
|---|---|---|
|s1|p1|c2|
|s1|p2|c1|
|s2|p1|c1|
|s1|p1|c1|

[A,B], [B,C], [A,C]로 쪼개봅시다.

|A|B|
|---|---|
|s1|p1|
|s1|p2|
|s2|p1|

|B|C|
|---|---|
|p1|c2|
|p2|c1|
|p1|c1|

|A|C|
|---|---|
|s1|c2|
|s1|c1|
|s2|c1|

다시 합치면

|A|B|C|
|---|---|---|
|s1|p1|c2|
|s1|p2|c1|
|s2|p1|c1|
|s1|p1|c1|
|**s2**|**p1**|**c2**| 

===> 마지막 튜플에서 이상값 발견!!!!

이런 상황을 방지하기 위해 제 5정규형을 시행합니다.

</p>
</details>

---

## 반정규화

### 반정규화 개념

반정규화란 시스템의 성능 향상, 개발 및 운영의 편의성 등을 위해 정규화된 데이터 모델을 통합, 중복, 분리하는 과정으로 의도적으로 정규화 원칙을 위배하는 행위이다.

* 반정규화를 수행하면 시스템의 성능이 향상되고 관리 효율성은 증가하지만, 데이터의 일관성과 정합성은 저하될 수 있다.
* 과도한 반정규화는 성능을 저하시킨다.
* 반정규화를 위해서는 사전에 **데이터의 일관성과 무결성을 우선으로 할지, 데이터베이스의 성능과 단순화를 우선으로 할지** 생각한다.
* 반정규화 방법에는 테이블 통합, 테이블 분할, 중복 테이블 추가, 중복 속성 추가 등이 있다.

### 테이블 통합

두 개의 테이블이 조인되는 경우가 많아 하나의 테이블로 합쳐 사용하는 것이 성능 향상에 도움이 될 경우 수행한다.
`두 개의 테이블에서 발생하는 프로세스가 동일하게 자주 처리되는 경우`, `두 개의 테이블을 이용하여 항상 조회를 수행하는 경우` 테이블 통합을 고려한다.

#### 테이블 통합 시 고려사항

* 검색은 간편하지만, 레코드 증가로 인해 처리량이 증가한다.
* 테이블 통합으로 인해 입력, 수정, 삭제 규칙이 복잡해질 수 있다.

### 테이블 분할

테이블을 수직 또는 수평으로 분할하는 것이다.

1. **수평 분할** : 레코드를 기준으로 테이블을 분할한다.
2. **수직 분할** : 하나의 테이블에 속성이 너무 많을 경우 속성을 기준으로 테이블을 분할한다.
    * `갱신위주의 속성 분할` : 데이터 갱신 시 레코드 잠금으로 인해 다른 작업을 수행 할 수 없으므로 갱신이 자주 일어나는 속성들을 수직 분할하여 사용한다.
    * `자주 조회되는 속성 분할` : 테이블에서 자주 조회되는 속성이 극히 일부일 경우 자주 사용되는 속성들을 수직분할하여 사용한다.
    * `크기가 큰 속성 분할` : 이미지, 2GB 이상 저장될 수 있는 텍스트 형식으로 된 속성들을 수직분할하여 사용한다.
    * `보안을 적용해야 하는 속성 분할` : 테이블 내의 특정 속성에 대해 보안을 적용할 수 없으므로 보안을 적용해야 하는 속성들을 수직분할 하여 사용한다.

#### 테이블 분할 시 고려사항

* 기본키의 유일성 관리가 어려워진다.
* 데이터 양이 적거나 사용 빈도가 낮은 경우 테이블 분할이 필요한 지를 고려해야한다.
* 분할된 테이블로 인해 수행 속도가 느려질 수 있다.
* 검색에 중점을 두어 테이블 분할 여부를 결정해야 한다.

### 중복 테이블 추가

여러 테이블에서 데이터를 추출해서 사용해야 하거나 다른 서버에 저장된 테이블을 이용해야 하는 경우 중복 테이블을 추가하여 작업의 효율성을 향상시킬 수 있다.

1. 중복 테이블을 추가하는 경우
    * 정규화로 인해 수행 속도가 느려지는 경우
    * 많은 범위의 데이터를 자주 처리해야하는 경우
    * 특정 범위의 데이터만 자주 처리해야 하는 경우
    * 처리 범위를 줄이지 않고는 수행 속도를 개선할 수 없는 경우

2. 중복 테이블을 추가하는 방법
    * `집계 테이블의 추가` : 집계 데이터를 위한 테이블을 생성하고, 각 원본 테이블에 트리거를 설정하여 사용하는 것으로, 트리거의 오버헤드에 유의한다.
    * `진행 테이블의 추가` : 이력 관리 등의 목적으로 추가하는 테이블로, 적절한 데이터 양의 유지와 활용도를 높이기 위해 기본키를 적절히 설정한다.
    * `특정 부분만을 포함하는 테이블의 추가` : 데이터가 많은 테이블의 특정 부분만을 사용하는 경우 해당 부분만으로 새로운 테이블을 생성한다.

### 중복 속성 추가

조인해서 데이터를 처리할 때 데이터를 조회하는 경로를 단축하기 위해 자주 사용하는 속성을 하나 더 추가하는 것이다.

> 중복 속성을 추가하면 데이터의 무결성 확보가 어렵고, 디스크 공간이 추가로 필요하다.

1. 중복 속성을 추가하는 경우
    * 조인이 자주 발생하는 속성인 경우
    * 접근 경로가 복잡한 속성인 경우
    * 액세스 조건으로 자주 사용되는 속성인 경우
    * 기본키의 형태가 적절하지 않거나 여러 개의 속성으로 구성된 경우

2. 중복 속성 추가 시 고려 사항
    * 테이블 중복과 속성의 중복을 고려한다.
    * 데이터 일관성 및 무결성에 유의해야 한다.
    * 저장공간의 지나친 낭비를 고려한다.

---

## 인덱스 (Index)

아래의 자료에서 자세한 설명을 볼 수 있다.

- 작성자 윤가영 | [데이터베이스와 Index](./materials/윤가영_database_index.pdf)

---

## 트랜잭션(Transaction)과 교착상태

트랜잭션이란? 데이터베이스의 상태를 변화시키기 위해 수행되는 작업의 논리적 단위이다.

### ACID

- Atomicity(원자성) : 트랜잭션에 해당하는 작업 내용이 (모두 성공했을 시) 모두 반영되거나, (하나라도 실패했을 시) 모두 반영되지 않아야 한다.
- Consistency(일관성) : 트랜잭션 처리 결과는 항상 데이터의 일관성을 보장해야 한다.
- Isolation(고립성) : 둘 이상의 트랜잭션이 동시에 실행되고 있을 때, 각 트랜잭션은 서로 간섭 없이 독립적으로 수행되어야 한다.
- Durability(지속성) : 트랜잭션이 성공적으로 완료된다면, 그 결과가 데이터베이스에 영구적으로 반영되어야 한다.

#### 주의사항

Isolation(고립성)을 보장하기 위해 무차별적으로 Lock을 걸다보면 대기시간이 매우 길어지므로 트랜잭션은 최소한으로 사용해야한다.

### 트랜잭션 상태

![image](https://user-images.githubusercontent.com/22047374/125165837-a951ee00-e1d3-11eb-9b0b-486cc5eff6b2.png)

- Active : 트랜잭션이 실행중인 상태(SQL 실행)
- Parital Commit : 트랜잭션의 마지막 연산까지 실행했지만, commit 연산이 실행되기 직전의 상태
- Commited : 트랜잭션이 성공적으로 종료되고 commit 연산까지 실행 완료된 상태
- Failed : 트랜잭션 실행에 오류가 발생한 상태
- Aborted: 트랜잭션이 비정상적으로 종료되어 Rollback 연산을 수행한 상태

1. Commit  :  데이터베이스 내의 연산이 성공적으로 종료되어 연산에 의한 수정 내용을 지속적으로 유지하기 위한 명령어이다.
2. Rollback  : 데이터베이스 내의 연산이 비정상적으로 종료되거나 정상적으로 수행이 되었다 하더라도 수행되기 이전의 상태로 되돌리기 위해 연산 내용을 취소할 때 사용하는 명령어이다.

### 트랜잭션에서 발생할 수 있는 문제들

#### Dirty Read Problem

한 트랜잭션 진행 중에 변경한 값을 다른 트랜잭션에서 읽을 때 발생한다.
커밋되지 않은 상태의 트랜잭션을 다른 트랜잭션에서 읽을 수 있을 때 발생하는 문제이다.

#### Non-repeatable Read Problem

한 트랜잭션에서 같은 값을 두 번 이상 읽었을 때 그 값이 다른 경우를 말한다.
한 트랜잭션 도중 다른 트랜잭션이 커밋되면 발생할 수 있는 문제이다.

#### Phantom Read Problem

한 트랜잭션에서 같은 쿼리문을 두 번 이상 실행했을 때 새로운 데이터가 조회되는 경우를 말한다.
A 트랜잭션 도중 B 트랜잭션에서 update 쿼리를 수행하고 커밋하더라도 A 트랜잭션에서 그 결과는 볼 수 없지만, 
A 트랜잭션 도중 B 트랜잭션에서 insert 쿼리를 수행할 경우 A 트랜잭션에서 처음에 안 보였던 새로운 데이터가 조회될 수 있다.

---

## NoSQL

아래의 자료에서 자세한 설명을 볼 수 있다.

- 작성자 이세명 | [NoSQL](./materials/이세명_database_NoSQL.pdf)

---

## 질의응답

_질문에 대한 답을 말해보며 공부한 내용을 점검할 수 있으며, 클릭하면 답변 내용을 확인할 수 있습니다._

<!-- 데이터베이스 개요 -->

<details>
<summary> 데이터베이스는 왜 사용하나요? </summary>  
<p>

기존에는 파일 시스템을 사용해 데이터를 관리했습니다. 그러나 파일 시스템에는 '데이터 중복', '데이터 불일치', '데이터 보안문제' 등 다양한 문제점을 가지고 있습니다. 데이터베이스를 사용하면 이러한 문제들을 어느 정도 해소할 수 있습니다.

</p>
</details>

<details>
<summary> 데이터베이스의 성능을 좋아지게 하려면 어떤 방법들이 있을까요? </summary>  
<p>

DB설계 튜닝
- 테이블 분해, 통합
- 테이블 정규화
- 적절한 데이터 타입 설정

DBMS 튜닝
- I/O 최소화
- Commit 주기 조정
- Middleware 기능과 연동

SQL 튜닝
- Join 방식 조정
- Index 활용

</p>
</details>

---

<!-- 정규화 -->

<details>
<summary>관계형 데이터베이스 설계의 목표는 무엇일까요?</summary>  
<p>

모든 각각의 릴레이션이 3NF와 BCNF를 이행하도록 하는 것

</p>
</details>

<details>
<summary> 정규화는 왜 할까요? </summary>  
<p>

데이터 생성, 수정, 삭제시 데이터 중복, 불일치 등 갱신 이상을 없애기 위해서 합니다. 데이터베이스의 성능을 높이기 위한 이유도 있습니다. (테이블을 분해해서 중복되는 열을 제거하기 때문에 메모리를 절약할수 있음)

</p>
</details>

<details>
<summary> 제1 정규형은 데이터베이스 정규화에서 사용하는 최소 정규형입니다. 제1 정규형에서 어떤 정규화 과정을 진행하는지 예시를 들어 설명할 수 있나요?</summary>  
<p>

ex1) 핸드폰 번호, 전화 번호를 동일한 칼럼에 중복되어 받는 경우(: 555-403-1659, 02-2651-4656)를 제거합니다.  
ex2) ex1에 대한 중복을 제거하기 위한 여러개의 전화번호 행을 두는 것(동일한 도메인과 의미를 두는 것은 최소 정규형에 위배)을 제거합니다.  
위와 같은 정규화 과정을 거쳐 제1 정규형이 됩니다.

</p>
</details>
   
<details>
<summary>제3 정규형을 '추이 종속' or '함수적 이행 종속' 단어를 사용하여 설명할 수 있나요?</summary>  
<p>

테이블이 제2 정규형을 만족하며 모든 속성이 기본 키에만 의존하여 다른 키에 의존하지 않는 정규형을 제3 정규형이라고 합니다.  
만약 의존한다면 함수적 이행 종속이 일어나서 A->B->C 순환적으로 모든 클래스가 의존하게 되는 문제가 일어날 수 있습니다.

</p>
</details>

<details>
<summary><strong>개인정보</strong>에 관한 데이터베이스에서 수정 이상이 일어나 select로 정확한 정보 파악이 되지 않아 정규화를 진행했습니다.  
하지만 이전보다 훨씬 느려졌다고 가정해봅시다. 지원자는 반정규화를 진행할것입니까?
</summary>
<p>

반정규화는 진행하면 안됩니다. 개인정보에 관한 데이터베이스로서 데이터의 무결성과 보안이 제일 중요합니다.   
만약 반정규화로 인해 '삽입, 삭제, 수정 이상'이 발생하는 경우에는 데이터의 무결성이 깨질 수 있고 더군다나 개인정보라서 데이터의 무결성이 깨지면 복원에 큰 어려움이 있습니다. 따라서 반정규화가 아닌 데이터베이스 튜닝, 재구성이 필요해 보입니다.
   
</p>
</details>

<details>
<summary> 정규화 작업 이후, 알맞게 정규화를 했는지 검증하고 싶을땐 어떻게 할까요? </summary>  
<p>

테이블 분해 이후 무손실 조인을 검사해봅니다.  
테이블 분해 이후 함수의 종속성이 보존되는지 확인합니다.

</p>
</details>

---

<!-- Index -->

<details>
<summary>Index가 무엇인지 설명해주세요.</summary>  
<p>

데이터 레코드를 빠르게 접근하기 위해 <키 값, 포인터> 쌍으로 구성되는 데이터 구조.

</p>
</details>

<details>
<summary>Index의 특징에 대해 아는대로 말해보세요.</summary>  
<p>

1. 인덱스는 데이터가 저장된 물리적 구조와 밀접한 관계에 있다.
2. 인덱스는 레코드가 저장된 물리적 구조에 접근방법을 제공한다.
3. 파일의 레코드에 대한 액세스를 빠르게 수행한다.
4. 레코드의 삽입과 삭제가 수시로 일어나는 경우, 인덱스의 개수를 최소로 하는것이 효율적이다.
5. 인덱스가 없으면 특정한 값을 찾기 위해 모든 데이터 페이지를 확인하는 TABLE SCAN이 발생한다.
6. 기본키를 위한 인덱스를 기본 인덱스라 하고, 기본 인덱스가 아닌 인덱스를 보조 인덱스라 한다.
7. 레코드의 물리적 순서가 인덱스의 엔트리 순서와 일치하게 유지되도록 구성되는 인덱스를 클러스터드 인덱스라고 한다.

</p>
</details>

<details>
<summary>Index 테이블 선정 기준에 대해 말해주세요</summary>  
<p>

랜덤 액세스가 빈번하거나, 다른 테이블과 순차적 조인이 발생되는 테이블 혹은 트겆ㅇ 범위나 순서로 데이터 조회가 필요한 테이블에 인덱스를 적용한다.

</p>
</details>

<details>
<summary>Index를 구현하는 자료구조에 대해서 말씀해주세요</summary>  
<p>

Index는 대표적으로 `해시 테이블`, `B+ 트리` 등으로 구현할 수 있다.  

1. 해시 테이블

해시테이블로 구현할 경우 검색에 대하여 시간복잡도 `O(1)`을 갖는다. 즉, 빠른 검색이 가능하다.  
하지만 해시는 등호(=) 연산자에 적합하고 실제 데이터베이스에서 자주 일어나는 부등호(<, >) 연산에는 적합하지 않다.
> 해시가 눈사태 효과(avalanche effect) 를 갖고 있기 때문이다. 


2. B+ 트리

![스크린샷 2021-05-16 오후 5 32 45](https://user-images.githubusercontent.com/22493971/118390940-bc7d8d00-b66c-11eb-9210-fc42db7de0da.png)  
_출처: https://blog.jcole.us/2013/01/10/btree-index-structures-in-innodb/_

리프 노드에만 데이터를 담아둠으로 더 많은 key 값을 저장할 수 있는 구조이다.  
나머지 노드들은 원하는 리프로 갈 수 있도록 안내하는 인덱스만 제공한다.

같은 레벨의 노드들은 `이중 연결리스트`로 연결되어 있기 때문에 부등호를 사용한 `순차검색`에 최적화 되어있다. 
원하는 데이터를 얻기 위해 리프노드까지 가야만한다는 단점이 있지만, 해시 인덱스에 비하여 인덱싱에 더 알맞은 자료구조로 여겨진다.

검색에 있어 시간복잡도 `O(log2 n)` 을 갖는다.

</p>
</details>

<details>
<summary>MULTI BLOCK READ가 무엇이며, 인덱스 테이블 선정기준과 연관지어 설명해보세요.</summary>  
<p>

테이블 액세스시 메모리에 한번에 읽어 들일 수 있는 블록의 수를 MULTI BLOCK READ라고 하며, MULTI BLOCK READ수에 따라 판단하여 인덱스를 사용할지 정한다. 예를들어 MULTI BLOCK READ가 16이면, 테이블의 크기가 16블록 이상일 경우 인덱스가 필요하다.

</p>
</details>

<details>
<summary>인덱스 컬럼 선정 기준에 대해 아는대로 말해보세요.</summary>  
<p>

가능한 한 수정이 빈번하지 않고, ORDER BY/ GROUP BY/ UNION이 빈번한 컬럼을 선정한다. 혹은 분포도가 10% ~ 15% 이내인 컬럼을 선정한다.

</p>
</details>

<details>
<summary>인덱스 설계시, 인덱스와 테이블 데이터의 저장공간이 분리되도록 설계하는 이유에 대해 설명하시오.</summary>  
<p>

데이터 저장시 인덱스의 영향을 받지 않아 빠르기 때문에 저장공간을 분리하여 설계한다.

</p>
</details>

<details>
<summary>비트맵 인덱스의 장점은 무엇인가요?</summary>  
<p>

데이터가 Bit로 구성되어 있어 효율적인 논리연산이 가능하고 저장공간이 작다.

</p>
</details>


---

<!-- NoSQL -->

<details>
<summary>NoSQL의 장점은 무엇인가?</summary>  
<p>

JOIN 처리가 없기 때문에 스케일 아웃을 통한 노드확장이 용이하다. 또한 가변적인 데이터 구조로 데이터를 저장할 수 있어 유연성이 높다.

</p>
</details>

<details>
<summary>어떤 상황에서 NoSQL을 사용하는것이 적합한가?</summary>  
<p>

비정형 데이터 혹은 많은 양의 로그를 수집해야할 때 적합하다.

</p>
</details>

<details>
<summary>NoSQL에서 정규화가 필요할까?</summary>  
<p>

NoSQL에서는 정규화 과정이 필요하지 않다.  
RDB와 달리 NoSQL에서는 `쿼리의 효율성`을 극대화하기 위해 오히려 비정규화한다.  

정규화는 중복을 줄이지만 그만큼 다수의 `JOIN` 을 요구하는 등 성능에 악영향을 미칠수도 있다.  
NoSQL에서는 의도적으로 중복을 허용하여 성능적인 이점을 얻는다.

</p>
</details>

---

<!-- Transaction -->

<details>
<summary>트랜잭션이란 무엇이며 왜 사용해야 하는지 말씀해주세요.</summary>  
<p>

- 키워드 1: 완전성을 보장해 주는 것
- 키워드 2: 작업의 논리적 단위

트랜잭션이란 데이터베이스의 상태 변화에 대한 작업의 논리적 단위를 말합니다. 사용 이유는 데이터의 완전성을 보장하기 위해서입니다. 트랜잭션을 통해 여러 쿼리 중 하나라도 실패했을 때 데이터베이스의 상태를 일관성을 유지한 상태로 원상복귀시킬 수 있고, 이를 통해 오류가 발생하더라도 언제나 데이터의 상태를 신뢰할 수 있습니다.

</p>
</details>

<details>
<summary>트랜잭션은 ACID라는 4가지 특성을 만족해야 합니다. 이 4가지 특성에 대해 자세히 말씀해주세요.</summary>  
<p>

- A : 원자성 (Atomicity) | 트랜잭션에 해당하는 작업 내용이 (모두 성공했을 시) 모두 반영되거나, (하나라도 실패했을 시) 모두 반영되지 않아야 한다.
- C : 일관성 (Consistency) | 트랜잭션 처리 결과는 항상 데이터의 일관성을 보장해야 한다.
- I : 고립성 (Isolation) | 둘 이상의 트랜잭션이 동시에 실행되고 있을 때, 각 트랜잭션은 서로 간섭 없이 독립적으로 수행되어야 한다.
- D : 지속성 (Durability) | 트랜잭션이 성공적으로 완료된다면, 그 결과가 데이터베이스에 영구적으로 반영되어야 한다.

</p>
</details>

<details>
<summary>A 계좌에서 B계좌로 일정 금액을 이체하는 작업에 대해 생각해봅시다. 이 때 트랜잭션은 어떻게 정의할 수 있을까요?</summary>  
<p>

(예시) A 계좌의 잔액 확인 SELECT문 + A 계좌의 금액 차감 UPDATE문 + B 계좌의 금액 추가 UPDATE문으로 정의할 수 있습니다.

</p>
</details>

<details>
<summary>(위 질문과 연결) 방금 말씀해주신 쿼리문에 대해서 Commit 연산과 Rollback 연산이 일어나는 경우는 각각 어떤 상황일까요?</summary>  
<p>

Commit 연산은 한 트랜잭션 단위에 포함된 모든 쿼리문이 성공적으로 완료되었을 경우 수행됩니다. 하나의 트랜잭션이 성공적으로 끝났고, 데이터베이스가 일관성이 있는 상태라는 것을 알려주기 위해 사용되는 연산입니다.
Rollback 연산은 트랜잭션에 포함된 쿼리 중 하나라도 실패하면 수행되며 모든 쿼리문을 취소하고 이전 상태로 돌려놓습니다. Rollback 연산을 통해 트랜잭션 처리가 실패하여 데이터베이스의 일관성을 깨뜨렸을 때, 트랜잭션의 원자성을 구현할 수 있습니다.

</p>
</details>

<details>
<summary>트랜잭션의 Commit 연산에 대해서 트랜잭션의 상태를 통해 설명해주세요.</summary>  
<p>

트랜잭션이 시작되면 활동(Active) 상태가 됩니다. 그리고 트랜잭션에 포함된 모든 연산이 실행되면 부분 완료(Partially Commited) 상태가 됩니다. 그리고 Commit 연산을 실행한 후, 완료(Commited) 상태가 되어 트랜잭션이 성공적으로 종료되게 됩니다.

</p>
</details>

<details>
<summary>트랜잭션의 Rollback 연산에 대해서 트랜잭션의 상태를 통해 설명해주세요.</summary>  
<p>

트랜잭션이 시작되면 활동(Active) 상태가 됩니다. 그리고 트랜잭션 중 오류가 발생하여 중단되면 실패(Failed) 상태가 됩니다. 그리고 Rollback 연산을 수행한 후, 철회(Aborted) 상태가 되어 트랜잭션이 종료되고 트랜잭션 실행 이전 데이터 상태로 돌아가게 됩니다.

</p>
</details>

<details>
<summary>Partial Commited 상태에서 Commited 상태가 되는 과정에 대해 자세히 설명해주세요.</summary>  
<p>

Commit 요청이 들어오면 Partial Commited 상태가 되는데, 이 때 Commit 연산을 문제 없이 수행하면 Commited 상태가 됩니다. 하지만 Commit 연산 수행 중 오류가 발생하면 Failed 상태로 돌아가게 됩니다.

</p>
</details>

<details>
<summary>트랜잭션 격리 수준(transaction isolation level)이란 무엇이며, 왜 필요한가요?</summary>  
<p>

트랜잭션에서 일관성이 없는 데이터를 허용하도록 하는 수준을 말합니다. 이것이 필요한 이유는 효율적인 Locking 방법이 필요하기 때문입니다. Locking 범위를 높인다면 동시에 수행되는 많은 트랜잭션들을 순차적으로 처리할 것이고, 이는 DB의 성능을 떨어뜨리게 됩니다. 반면 범위를 줄인다면 응답성은 높아지겠지만 잘못된 값이 처리될 수 있습니다. 따라서 트랜잭션 격리 수준을 두어 Locking 수준을 관리합니다.

</p>
</details>

<details>
<summary>Isolation level의 종류 중 한 가지를 설명해주시고, 이 때 발생할 수 있는 현상도 함께 설명해주세요.</summary>  
<p>

- Read Uncommited : Dirty Read, Non-Repeatable Read, Phantom Read
- Read Committed : Non-Repeatable Read, Phantom Read
- Repeatable Read : Phantom Read
- Serializable : 완벽한 일관성 보장

</p>
</details>

---

<details>
<summary>
트랜잭션을 병행 제어없이 병행으로 DB에 동시에 접근 할 경우 발생하는 문제점이 무엇인가요?</summary>  
<p>

1. 갱신 분실 : 같은 데이터를 공유하여 갱신 할 때 갱신 결과의 일부가 사라짐

2. 모순성 : 동시에 같은 데이터를 갱신할 때, 데이터의 상호 불일치 발생

3. 연쇄 복귀 : 트랜잭션 하나에 문제가 발생하여 롤백시 나머지 트랜잭션도 다같이 롤백됨

</p>
</details>

<details>
<summary>
교착상태가 일어나기위한 네가지 조건을 설명해주세요</summary>  
<p>

1. Mutual Exclusion : 자원을 공유하지 않음, 자원을 공유한다면 서로 기다릴 필요가 없음.

2. Hold & Wait : 자원을 소유하고 있으면서 다른 자원도 기다리는 상태

3. No Preemption : 자원을 한번 얻으면 완전 종료까지 자원을 놓지 못함, (상대방이 가로채갈 수 없음)

4. Circular Wait : 원형의 형태로 자원을 기다림
![circularwait](https://user-images.githubusercontent.com/22339356/119250905-3ae2ad80-bbde-11eb-9031-64cfeb36bc43.jpeg)

</p>
</details>

<details>
<summary>
Deadlock Prevention 과 Avoidance 의 차이는 무엇인가요?</summary>  
<p>

1. Prevention : 네가지 조건 중 한가지를 막아 Deadlock이 일어나지 않게 하는 것(사전 차단)

2. Avoidance : Deadlock의 가능성이 없는 경우에만 (safe state) 에만 자원을 할당

+그렇다면 Unsafe state == Deadlock 인가?
NO, Unsafe state는 Deadlock이 일어 날 수 도 있는 상태를 의미함

</p>
</details>

<details>
<summary>
Deadlock Prevention , Avoidance 그리고 Ignorance 세가지 방법중에 실제 일반적인 OS에서 가장 많이 사용하는 방식은 무엇이라 생각하시나요?</summary>  
<p>

1. Ignorance

    이유: Deadlock Prevention, Avoidance를 위해서는 많은 비용이 필요함. 따라서 일반적으로 사용하는 OS에서는 Deadlock을 사전에 차단하지 않고 Deadlock발생 시 수동으로 해소시키는 방법을 사용.

2. 로켓 발사나 비행기 운전 시스템과 같이 Deadlock 절대 걸려서는 안되는 정밀하고 중요한 시스템 OS에서만 Prevention이나 Avoidance를 사용함


</p>
</details>

---

## Reference

> - Database System Concepts - 6th edition
> - 시나공 정보처리기사 필기
