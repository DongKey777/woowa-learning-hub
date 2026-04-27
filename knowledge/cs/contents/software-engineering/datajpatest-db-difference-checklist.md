# DataJpaTest DB 차이 가이드

> 한 줄 요약: `@DataJpaTest`에서 H2로는 통과해도 실제 DB 전용 쿼리에서는 흔들릴 수 있으니, **언제 H2로 충분하고 언제 Testcontainers로 실제 엔진을 붙여야 하는지**를 먼저 나누면 초반 시행착오를 크게 줄일 수 있다.

**난이도: 🟢 Beginner**

`repository` 테스트를 처음 잡는 학습자라면 이 문서를 "H2를 버릴까?"가 아니라 "**이 쿼리는 어느 DB에서 판정해야 맞는가?**"를 정하는 입구로 읽으면 된다.

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 멘탈 모델](#먼저-잡는-멘탈-모델)
- [언제 H2로 충분하고 언제 Testcontainers로 가나](#언제-h2로-충분하고-언제-testcontainers로-가나)
- [30초 판단 체크리스트](#30초-판단-체크리스트)
- [Flyway/Liquibase 테스트 스키마 정렬 체크리스트](#flywayliquibase-테스트-스키마-정렬-체크리스트)
- [Testcontainers 시작 템플릿](#testcontainers-시작-템플릿)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

관련 문서:

- [Software Engineering README: DataJpaTest DB 차이 가이드](./README.md#datajpatest-db-차이-가이드)
- [테스트 전략 기초](./test-strategy-basics.md)
- [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
- [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
- [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- [Repository Fake Design Guide](./repository-fake-design-guide.md)
- [Spring Testcontainers Boundary Strategy](../spring/spring-testcontainers-boundary-strategy.md)

retrieval-anchor-keywords: datajpatest db 차이, h2 postgres mismatch, h2 mysql mismatch, native query real db test, testcontainers jpa beginner, postgres function h2 error, flyway liquibase test schema mismatch, ddl auto migration mismatch, jsonb h2 mismatch, 처음 배우는데 h2로 충분한가, 언제 testcontainers로 옮기나, datajpatest db difference checklist basics, datajpatest db difference checklist beginner, datajpatest db difference checklist intro, software engineering basics

## 먼저 잡는 멘탈 모델

`@DataJpaTest`는 "JPA 계층을 빠르게 좁혀 보는 테스트"다.
H2는 그 테스트를 빨리 돌리게 도와주지만, 운영 DB를 그대로 복제해 주지는 않는다.

초심자 기준으로는 이렇게 나누면 된다.

- H2는 "매핑, 기본 CRUD, 단순 JPQL"을 빠르게 확인하는 1차 안전망이다.
- 실제 DB는 "DB 전용 문법, 함수, 타입, 정렬 규칙"을 최종 판정하는 심판이다.
- 그래서 실패 원인을 볼 때도 "JPA가 틀렸나?"보다 "이 쿼리를 H2가 판정해도 되는가?"를 먼저 묻는 편이 빠르다.

## 언제 H2로 충분하고 언제 Testcontainers로 가나

| 상황 | 먼저 선택 | 이유 |
|---|---|---|
| 기본 CRUD, 단순 JPQL, 연관관계 매핑 확인 | H2 + `@DataJpaTest` | 문법 차이가 적고 피드백이 빠르다 |
| `nativeQuery`, `ILIKE`, `JSONB`, DB 함수 사용 | Testcontainers + 실제 DB | 쿼리 의미가 엔진 규칙에 묶여 있다 |
| Flyway/Liquibase 스키마와 테스트 스키마가 자주 엇갈림 | Testcontainers + 실제 마이그레이션 | "테스트만 통과" 착시를 줄인다 |
| 정렬/페이지/시간대 결과가 운영 DB와 다름 | Testcontainers로 한 번 재판정 | NULL 정렬, collation, timezone 차이가 숨어 있을 수 있다 |

최소 판단 기준은 단순하다.

1. `nativeQuery = true`면 실제 DB 테스트를 먼저 떠올린다.
2. DB 함수나 타입 이름이 쿼리에 보이면 H2 단독 판정에 기대지 않는다.
3. "결과 건수는 맞는데 순서만 다르다"면 정렬 규칙 차이를 의심한다.

## 30초 판단 체크리스트

아래 네 질문 중 하나라도 `yes`면 H2만으로 끝내지 말고 Testcontainers 후보로 올리면 된다.

| 질문 | `yes`면 |
|---|---|
| 운영 DB 전용 문법이나 함수가 보이나? | 실제 DB 컨테이너에서 쿼리를 검증한다 |
| `jsonb`, enum, timezone, quoted identifier 차이가 있나? | 타입/식별자 차이를 실제 엔진에서 본다 |
| 운영은 Flyway/Liquibase인데 테스트는 `ddl-auto`에 기대나? | 테스트도 같은 마이그레이션 경로로 맞춘다 |
| 페이지/정렬 테스트가 H2와 운영 DB에서 다르게 보이나? | tie-breaker와 NULL 정렬을 실제 DB에서 다시 본다 |

짧은 예시도 이 기준으로 읽으면 된다.
`customer_name ilike ...` 같은 PostgreSQL 쿼리는 repository가 틀렸다기보다, **H2가 심판으로 부적절한 경우**일 가능성이 더 크다.

## Flyway/Liquibase 테스트 스키마 정렬 체크리스트

여기서 초심자가 가장 많이 헷갈리는 지점은 "`운영은 Flyway/Liquibase인데 테스트는 왜 그냥 떠도 되지?`"다.
짧게 말하면, 운영은 "마이그레이션 기록을 따라 만든 스키마"이고 테스트 자동 생성은 "지금 엔티티를 보고 바로 만든 스키마"라서 출발점이 다르다.

| 확인 질문 | 왜 보나 | 바로 할 일 |
|---|---|---|
| 운영 DB는 Flyway/Liquibase를 쓰는데 테스트는 `ddl-auto=create`인가? | 같은 앱이어도 만들어지는 테이블 shape가 달라질 수 있다 | DB 전용 쿼리 테스트는 마이그레이션 기반으로 돌린다 |
| 컬럼명, index, unique constraint를 migration에서 따로 만졌나? | 엔티티만 보고는 빠지는 제약이 있을 수 있다 | "테스트만 초록"이면 migration SQL부터 다시 본다 |
| baseline 이후 수동 SQL patch가 있었나? | 자동 생성 스키마는 그 patch를 모른다 | 테스트 스키마도 같은 patch 경로를 타게 맞춘다 |
| 실패가 `table/column not found`보다 "결과는 나오는데 운영과 다름"에 가까운가? | 스키마 shape 차이가 숨어 있을 수 있다 | H2보다 실제 DB + migration 조합으로 재판정한다 |

처음에는 네 줄만 기억하면 된다.

1. 엔티티 자동 생성은 "현재 코드 snapshot" 기준이다.
2. Flyway/Liquibase는 "변경 이력" 기준이다.
3. 둘이 다르면 repository보다 스키마 준비 방식이 먼저 문제일 수 있다.
4. 특히 `nativeQuery`, index 의존 정렬, constraint 검증은 migration 기준 테스트가 더 안전하다.

## Testcontainers 시작 템플릿

처음에는 큰 구조보다 "실제 DB를 붙인 `@DataJpaTest` 한 개"만 만들어도 충분하다.

```java
@Testcontainers
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class OrderRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void override(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

이 템플릿에서 초심자가 기억할 건 세 가지다.

- `replace = NONE`이 있어야 H2로 다시 바뀌지 않는다.
- 운영 DB가 PostgreSQL이면 테스트도 PostgreSQL 컨테이너로 맞춘다.
- 처음부터 모든 repository를 옮기지 말고, **DB 전용 쿼리 1개**만 실제 엔진으로 옮겨 시작한다.

## 자주 하는 오해

- "`@DataJpaTest`가 통과했으니 운영 DB도 안전하다"
  - 아니다. H2 통과는 빠른 1차 확인이지 최종 판정이 아니다.
- "그럼 이제 모든 repository 테스트를 Testcontainers로 바꿔야 하나"
  - 아니다. DB 전용 쿼리, 정렬 차이, 스키마 차이가 드러나는 곳만 먼저 옮기면 된다.
- "H2에서 깨졌으니 엔티티 매핑부터 다 뜯어야 하나"
  - 아니다. native query, 함수, 타입, 마이그레이션 경로 차이를 먼저 본다.
- "Testcontainers는 무거우니 초심자는 쓰면 안 되나"
  - 아니다. 무겁더라도 **틀린 심판보다 맞는 심판**이 더 중요할 때가 있다.

## 한 줄 정리

- H2는 빠른 1차 확인용, Testcontainers는 실제 DB 판정용이라고 나누면 된다.
- `nativeQuery`, DB 함수, 타입 차이, 정렬/시간대 차이가 보이면 실제 엔진 테스트로 옮긴다.
- 처음에는 모든 테스트를 바꾸지 말고, 가장 헷갈리는 DB 전용 쿼리 1개부터 시작하면 된다.
