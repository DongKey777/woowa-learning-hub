# Database (데이터베이스)

> 한 줄 요약: 이 README는 database를 처음 고를 때 쓰는 `category navigator`다. 처음에는 `Database First-Step Bridge -> 트랜잭션 기초 -> JDBC · JPA · MyBatis 기초 -> 인덱스 기초`까지만 잡고, `deadlock`/`failover`/`cdc` 같은 운영 문서는 실제 증상이 붙을 때만 관련 문서로 내려간다.

**난이도: 🟢 Beginner**

관련 문서:

- [Database First-Step Bridge](./database-first-step-bridge.md)
- [트랜잭션 기초](./transaction-basics.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [인덱스 기초](./index-basics.md)
- [Language README의 빠른 탐색](../language/README.md#빠른-탐색)
- [루트 README](../../README.md)

retrieval-anchor-keywords: database readme, database navigator, database beginner route, database basics, database what is first, database 처음 뭐부터, db 처음 어디부터, save 보이는데 sql 안 보여요, transactional save entity 헷갈려요, explain 처음 뭐부터, key null 뭐예요, deadlock 은 나중에, cdc cutover follow-up, spring database bridge

## 빠른 탐색

처음 5분은 아래 한 줄만 기억하면 충분하다.

`Database First-Step Bridge -> 트랜잭션 기초 -> JDBC · JPA · MyBatis 기초 -> 인덱스 기초`

| 지금 막힌 말 | 먼저 열 문서 | 왜 여기서 시작하나 |
|---|---|---|
| "DB를 어디부터 읽어야 할지 모르겠어요" | [Database First-Step Bridge](./database-first-step-bridge.md) | 질문 축을 `트랜잭션 / SQL 위치 / 인덱스`로 먼저 자른다 |
| "`commit`은 했는데 왜 마지막 재고가 또 팔려요?" | [트랜잭션 기초](./transaction-basics.md) | commit/rollback과 동시성 충돌을 먼저 분리한다 |
| "`save()`는 보이는데 SQL이 안 보여요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | repository, entity, mapper 역할을 먼저 구분한다 |
| "`Repository`, `Entity`라는 말부터 헷갈려요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 저장 시작점과 저장 대상이라는 최소 뜻부터 잡는다 |
| "WHERE 조건 하나인데 왜 느려요?" | [인덱스 기초](./index-basics.md) | 조회 경로 문제를 따로 떼어 봐야 한다 |

## beginner route에서 멈추는 기준

처음 읽기에서는 아래 네 문서 바깥으로 바로 점프하지 않는다.

`Database First-Step Bridge -> 트랜잭션 기초 -> JDBC · JPA · MyBatis 기초 -> 인덱스 기초`

| 먼저 보인 단어 | 지금 이 README에서 할 일 | 바로 갈 관련 문서 |
|---|---|---|
| `deadlock`, `lock wait`, `retry` | "동시성/충돌 follow-up"이라는 것만 확인하고 primer route를 끝낸다 | [락 기초](./lock-basics.md), [Deadlock vs Lock Wait Timeout 입문 프라이머](./deadlock-vs-lock-wait-timeout-primer.md) |
| `flush`, lazy loading, OSIV | "JPA 내부 동작 follow-up"이라는 것만 확인한다 | [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md), [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| `pool timeout`, `failover`, `replica lag` | 입문 route가 아니라 운영/배포 축이라는 것만 확인한다 | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md), [Replica Lag와 Read-after-Write](./replica-lag-read-after-write-strategies.md) |
| `cdc`, `backfill`, `cutover` | 데이터 이동/마이그레이션 축이라는 것만 확인한다 | [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md) |

## 읽고 돌아오는 안전 루프

primer 한 장을 읽은 뒤에는 deep dive를 연달아 고르기보다, "다음 한 칸"과 "돌아올 자리"를 같이 고정해 두는 편이 안전하다.

각 database primer 상단의 `database 카테고리 인덱스` 링크는 다시 이 README로 돌아오는 safe return path다. primer에서 질문이 풀리지 않으면 deep dive로 더 내려가기보다, 먼저 이 README의 [빠른 탐색](#빠른-탐색)으로 복귀해 `트랜잭션 / SQL 위치 / 인덱스` 중 어떤 축이 남았는지 다시 고른다.

| 방금 읽은 primer | 바로 다음 한 칸 | 여기서 더 안 내려가고 돌아올 자리 |
|---|---|---|
| [Database First-Step Bridge](./database-first-step-bridge.md) | [트랜잭션 기초](./transaction-basics.md) 또는 [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| [트랜잭션 기초](./transaction-basics.md) | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) 또는 [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| [인덱스 기초](./index-basics.md) | [인덱스와 실행 계획](./index-and-explain.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| database를 읽다가 질문이 다시 `new`, `equals()`, `HashMap#get(...)`, `Optional` 축으로 줄어듦 | [Language README의 빠른 탐색](../language/README.md#빠른-탐색) | 이 README의 [빠른 탐색](#빠른-탐색) |

초보자용 복귀 문장은 이 한 줄이면 충분하다.

`이 README의 빠른 탐색 -> primer 1장 -> 다음 한 칸 1장 -> 막히면 다시 이 README의 빠른 탐색`

## 한 화면에 같이 보일 때

`@Transactional`, `save()`, `@Entity`가 같이 보이면 아래처럼 쪼개 읽는다.

| 먼저 보이는 단서 | 초보자용 첫 해석 | 다음 문서 |
|---|---|---|
| `@Transactional` | 어디까지 같이 commit/rollback할지 정하는 경계다 | [트랜잭션 기초](./transaction-basics.md) |
| `save()` / `Repository` / `Mapper` | 저장이나 조회를 시작하는 창구다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `@Entity` | 무엇을 저장하는지 보여 주는 매핑 단서다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `key = NULL`, `Using filesort` | 조회 경로를 다시 읽어야 한다는 신호다 | [인덱스와 실행 계획](./index-and-explain.md) |

처음엔 `@Transactional`, `Repository`, `Entity`를 한 문장으로 읽지 않는 편이 안전하다.

- `@Transactional`은 "어디까지 같이 실패하나"를 보는 단서다.
- `Repository`는 "어디서 저장을 시작하나"를 보는 단서다.
- `Entity`는 "무엇을 저장하나"를 보는 단서다.

이 세 줄이 분리되면, 초보자용 첫 독해는 이미 절반 이상 끝난 상태다.

## 처음 보는 저장 흐름 예시

처음엔 "한 메서드 안에 뜻이 너무 많다"는 느낌이 가장 흔하다. 아래 예시는 한 줄마다 질문 축이 다르다는 점만 잡으면 된다.

```java
@Transactional
public void register(String email) {
    Member member = new Member(email);
    memberRepository.save(member);
}
```

| 코드 한 줄 | 지금 붙일 첫 뜻 | 먼저 갈 문서 |
|---|---|---|
| `@Transactional` | 어디까지 같이 commit/rollback할지 정하는 경계다 | [트랜잭션 기초](./transaction-basics.md) |
| `new Member(email)` | 저장할 객체를 만드는 중이다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| `memberRepository.save(member)` | 저장 요청이 시작되는 entrypoint다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |

이 예시에서 아직 답하지 않는 질문도 있다.

- "`왜 update SQL이 나가요?`", "`flush`가 뭐예요?" -> [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)
- "`왜 마지막 재고가 또 팔려요?`" -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- "`Repository`와 `Entity`가 이름만 봐선 헷갈려요" -> [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)

이 예시에서 더 안전한 다음 한 칸도 같이 고르면 route가 덜 끊긴다.

| 지금 예시를 읽고 남은 질문 | safe next step |
|---|---|
| "`save()`는 알겠는데 insert/update 구분이 안 돼요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)의 `save()` 설명 구간 |
| "`Repository`와 `Entity` 단어 자체가 계속 섞여요" | [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md) |
| "`왜 같이 rollback돼요?`가 더 먼저 궁금해요" | [트랜잭션 기초](./transaction-basics.md) |

## Spring -> Database handoff

`controller -> service -> repository`까지는 보이는데 database에서 어디부터 읽어야 할지 막히면 이 순서로만 간다.

| 지금 막힌 말 | primer 1장 | safe next step 1장 |
|---|---|---|
| "`spring` 다음에 DB는 뭐부터예요?" | [Database First-Step Bridge](./database-first-step-bridge.md) | [트랜잭션 기초](./transaction-basics.md) 또는 [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`save()`는 보이는데 SQL이 안 보여요" | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| "`왜 같이 rollback돼요?`" | [트랜잭션 기초](./transaction-basics.md) | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |

질문이 browser/network 쪽으로 다시 올라가면 [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)과 [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)로 한 칸 복귀한다.

database primer를 한 장 읽고도 질문이 여전히 "`new`가 뭘 만들죠?", "`같은 객체`와 `같은 값`이 뭐가 달라요?", "`HashMap#get(...)`이 왜 `null`이죠?"라면 database 안에서 더 내려가지 말고 [Language README의 빠른 탐색](../language/README.md#빠른-탐색)으로 바로 복귀한다.

반대로 Spring이나 Language에서 이 README로 건너온 경우에도, `트랜잭션 기초` 또는 `JDBC · JPA · MyBatis 기초`까지만 읽고 길이 다시 퍼지면 이 README의 [빠른 탐색](#빠른-탐색)으로 먼저 되돌아온다. `격리 수준`, `flush`, `pool timeout` 같은 follow-up은 "남은 질문 1개"가 분명해졌을 때만 다음 한 칸으로 붙인다.

## DB인지 Java인지 헷갈릴 때

처음 보는 에러 문장에 `save()`, `@Transactional`, `Repository`가 있어도 실제로는 database보다 Java 문법 축을 먼저 복구해야 할 때가 있다.

| 지금 더 먼저 막히는 말 | 여기서 더 내려가기보다 먼저 갈 문서 | 왜 이쪽이 먼저인가 |
|---|---|---|
| "`save()`보다 `HashMap#get(...)`이 왜 `null`인지가 더 헷갈려요" | [Language README의 빠른 탐색](../language/README.md#빠른-탐색) | key 조회와 value `null` 해석을 먼저 자르면 DB와 Java 질문이 덜 섞인다 |
| "`rollback`보다 `new` 했는데 뭐가 생기는지가 더 헷갈려요" | [Java 실행 모델과 객체 메모리 mental model 입문](../language/java/java-execution-object-memory-mental-model-primer.md) | 객체 생성과 참조 공유가 안 잡히면 repository 흐름도 같이 흐려진다 |
| "`Repository`는 보이는데 `같은 객체`와 `같은 값` 차이부터 흔들려요" | [Java Equality and Identity Basics](../language/java/java-equality-identity-basics.md) | `Set`/`Map` 동작과 엔티티 비교 오해를 먼저 분리해야 한다 |
| "`한 명 없음`과 `0개`가 왜 다른지 모르겠어요" | [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](../language/java/optional-collections-domain-null-handling-bridge.md) | 단건의 없음과 컬렉션 0개를 먼저 나누면 DB 결과 해석이 쉬워진다 |

이 표에서 language 쪽 primer를 한 장 읽고 나면, 다시 DB 질문이 남았을 때만 이 README의 [빠른 탐색](#빠른-탐색)으로 돌아와 `트랜잭션 / SQL 위치 / 인덱스` 중 한 축만 다시 고르면 된다.

## 자주 섞이는 오해

초보자 질문에서 가장 자주 섞이는 오해는 아래 3개다.

| 헷갈린 문장 | 바로 끊어야 할 구분 | 먼저 갈 문서 |
|---|---|---|
| "`@Transactional`이 있으니 JPA 아닌가요?" | 트랜잭션 경계와 DB 접근 기술은 다른 축이다 | [트랜잭션 기초](./transaction-basics.md), [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`Entity`가 있으니 insert SQL도 여기 있겠죠?" | `Entity`는 매핑 단서이고 저장 시작점은 repository/mapper/DAO다 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`save()`만 보이니 DB가 자동으로 다 되는 거죠?" | 저장 요청 시작점과 실제 동시성 안전성은 다르다 | [트랜잭션 기초](./transaction-basics.md), [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |

## beginner route 뒤에 붙는 4번째 문서

처음부터 deep dive로 내려가지 말고, beginner route를 끝낸 뒤 "남은 질문 1개" 기준으로 4번째 문서만 붙인다.

| beginner route 뒤에 남은 질문 | 4번째 문서 |
|---|---|
| "`@Transactional`인데 왜 중복 판매가 나요?" | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |
| "`JpaRepository` 구현체가 안 보여요" | [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md) |
| "`save()`는 보이는데 pool timeout도 보여요" | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) |
| "`EXPLAIN`에 `key = NULL`이 보여요" | [인덱스와 실행 계획](./index-and-explain.md) |
| "`EXPLAIN`에 `Using temporary`가 보여요" | [EXPLAIN 첫 판독 미니카드](./explain-first-read-timeout-mini-card.md) |
| "`cdc replay`, `cutover`가 같이 궁금해요" | [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md) |

## 추천 학습 흐름 (category-local survey)

이 survey는 "긴 catalog를 정독"하라는 뜻이 아니다. 각 줄의 앞 2~3개 primer만 먼저 읽고, 실제 증상이 생겼을 때만 follow-up으로 내려간다. 아래 표의 `replica / consistency`, `cdc / cutover`는 beginner route가 아니라 관련 질문이 직접 붙었을 때만 연다.

| 질문 축 | beginner first route | follow-up 신호 |
|---|---|---|
| transaction / lock | [Database First-Step Bridge](./database-first-step-bridge.md) -> [트랜잭션 기초](./transaction-basics.md) -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) | `deadlock`, `retry`, `FOR UPDATE`, oversell |
| SQL 위치 / JPA | [Database First-Step Bridge](./database-first-step-bridge.md) -> [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | `JpaRepository`, `flush`, lazy loading, pool timeout |
| index / explain | [인덱스 기초](./index-basics.md) -> [인덱스와 실행 계획](./index-and-explain.md) -> [EXPLAIN 첫 판독 미니카드](./explain-first-read-timeout-mini-card.md) | `Using filesort`, `Using temporary`, `actual rows`, histogram |
| postgresql storage / write churn | [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md) -> [PostgreSQL `HOT update`는 뭐예요?](./postgresql-hot-update-beginner-bridge.md) | `fillfactor`, `HOT update`, heap page 여유 공간, update churn |
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

## Bridge Entrypoints

이 아래 4개 anchor는 cross-category README와 bridge map이 beginner-safe entrypoint로 공통 참조하는 구간이다. 처음에는 각 anchor에서 `primer 1장 -> follow-up 1장`까지만 고정하고, incident나 operator 문서는 마지막 열에 적힌 cue가 생길 때만 붙인다.

<a id="database-bridge-request-entry-to-sql"></a>
## Request -> Controller -> `save()` -> SQL handoff

브라우저 요청이 controller를 지나 repository와 SQL로 내려가는 장면이 한 문장처럼 섞일 때 쓰는 beginner bridge다. mental model은 "`어디로 들어오나 -> 누가 연결했나 -> 무엇이 저장되나 -> 어떤 기술이 SQL을 만들까`" 순서로만 자르는 것이다.

| 지금 막힌 말 | primer | safe next step | 아직 안 가는 편이 좋은 문서 |
|---|---|---|---|
| "`브라우저 요청이 controller를 지나 DB까지 어떻게 와요?`" | [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) -> [Database First-Step Bridge](./database-first-step-bridge.md) | deadlock, failover, cdc replay |
| "`controller` 다음 `save()`와 SQL은 어디서 봐요?`" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | JPA flush 심화, lock incident |
| "`왜 네트워크나 Spring을 안 보고 DB 문서부터 보면 헷갈려요?`" | [Database First-Step Bridge](./database-first-step-bridge.md) | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) | schema migration, replay cutover |

- 공통 오해:
  - `save()`가 보인다고 바로 SQL 문서부터 열면 `request entry`, bean wiring, 저장 기술이 한 번에 섞인다.
  - `404`, `400`, `415`가 먼저 보이면 DB보다 network/spring entrypoint를 먼저 복구하는 편이 안전하다.

<a id="database-bridge-transaction-app"></a>
## 트랜잭션 경계 / 애플리케이션 브리지

`@Transactional`, rollback, 격리 수준, Spring proxy가 같이 보여도 beginner 첫 목표는 "`무엇을 한 번에 commit/rollback하나`"만 고정하는 것이다. 그다음에야 DB anomaly와 Spring proxy 규칙을 분리한다.

| 지금 막힌 말 | primer | safe next step | deep dive cue |
|---|---|---|---|
| "`왜 같이 rollback돼요?`" | [트랜잭션 기초](./transaction-basics.md) | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) | `lost update`, `deadlock`, `FOR UPDATE` |
| "`@Transactional`이 안 먹는 것 같아요" | [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md) | [트랜잭션 기초](./transaction-basics.md) | self-invocation, rollback-only, propagation |
| "`service`에서 묶었는데 왜 DB 결과가 기대와 달라요?`" | [트랜잭션 기초](./transaction-basics.md) | [Cross-Domain Bridge Map: Transaction Isolation / `@Transactional` / Rollback Debugging](../../rag/cross-domain-bridge-map.md#bridge-database-spring-transaction-cluster) | routing datasource, readOnly, checked exception commit |

- common confusion:
  - `@Transactional`은 DB 접근 기술 이름이 아니라 경계 선언이다.
  - 격리 수준과 propagation은 둘 다 "트랜잭션"이지만 같은 질문이 아니다. 처음에는 commit/rollback 경계부터 본다.

<a id="database-bridge-retry-replay"></a>
## Retry / Idempotency / Replay 브리지

`중복 제출`, `retry`, `replay`, `cutover`가 한 덩어리처럼 들려도 초보자에게는 먼저 "같은 요청이 다시 왔나"와 "데이터를 다시 흘려 보내나"를 분리하는 것이 안전하다.

| 지금 막힌 말 | primer | safe next step | 나중에만 볼 문서 |
|---|---|---|---|
| "`새로고침했더니 주문이 두 번 될까 봐 무서워요`" | [Post/Redirect/Get(PRG) 패턴 입문](../network/post-redirect-get-prg-beginner-primer.md) | [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md) | replay runbook, cutover gate |
| "`retry`와 `중복 방지`가 뭐가 달라요?`" | [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md) | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) | saga, bulk recovery |
| "`cdc replay`, `backfill`, `cutover`가 같이 보여요`" | [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md) | [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md) | operator cleanup, incident recovery |

- symptom phrase anchors:
  - `처음 replay가 뭐예요`, `왜 retry와 replay를 같은 말로 쓰면 안 되죠?`, `중복 제출 basics`, `backfill what is`

<a id="database-bridge-identity-authority"></a>
## Identity / Authority Transfer 브리지

SCIM, deprovision, authority transfer 질문은 먼저 `row parity`와 `access tail`로 나눈다.

| 지금 막힌 말 | primer | safe next step | deeper handoff |
|---|---|---|---|
| "`SCIM disable은 끝났는데 왜 아직 접근돼요?`" | [Identity Lifecycle / Provisioning Primer](../security/identity-lifecycle-provisioning-primer.md) | [Role Change and Session Freshness Basics](../security/role-change-session-freshness-basics.md) -> [Claim Freshness After Permission Changes](../security/claim-freshness-after-permission-changes.md) | [Security lifecycle bridge](../security/README.md#security-bridge-identity-delegation-lifecycle) |
| "`backfill is green but access tail remains`" | [Authority Transfer vs Revoke Lag Primer Bridge](../security/authority-transfer-vs-revoke-lag-primer-bridge.md) | [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md) | [System Design: Database / Security Authority Bridge](../system-design/README.md#system-design-database-security-authority-bridge) |
| "`decision parity`, `auth shadow divergence`가 뭐부터예요?`" | [Authority Transfer vs Revoke Lag Primer Bridge](../security/authority-transfer-vs-revoke-lag-primer-bridge.md) | [Security lifecycle bridge](../security/README.md#security-bridge-identity-delegation-lifecycle) | [System Design: Verification / Shadowing / Authority Bridge](../system-design/README.md#system-design-verification-shadowing-authority-bridge) |

## Identity 브리지에서 여기로 다시 돌아오는 기준

- common confusion: row/backfill 검증이 green이어도 세션, claim, authz cache tail은 남을 수 있다.
- security primer를 한 장 읽고도 질문이 다시 `트랜잭션`, `backfill`, `row parity` 쪽이면 system-design deep dive로 더 내려가기보다 이 README의 [빠른 탐색](#빠른-탐색)으로 먼저 돌아와 database 축이 아직 남았는지 다시 고른다.

## 권한 tail 메모

- beginner 첫 클릭은 operator cleanup이 아니라 primer -> bridge 사다리다.

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
