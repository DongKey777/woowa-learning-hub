# JDBC · JPA · MyBatis 기초

> 한 줄 요약: JDBC는 SQL을 직접 실행하는 저수준 API이고, JPA는 객체와 테이블을 매핑하는 ORM 표준이며, MyBatis는 둘 사이 어딘가에서 SQL을 XML/어노테이션으로 관리하는 SQL 매퍼다.

**난이도: 🟢 Beginner**

관련 문서:

- [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md)
- [database 카테고리 인덱스](./README.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)

retrieval-anchor-keywords: jdbc jpa mybatis beginner, jdbc 기초, jpa 입문, mybatis 처음 배우는데, orm 기초, sql mapper 기초, jdbc vs jpa 차이, jpa가 뭐예요, mybatis 설명, java db 연결 입문

## 핵심 개념

자바 애플리케이션이 데이터베이스와 통신할 때는 세 가지 접근 방식이 자주 등장한다.

- **JDBC(Java Database Connectivity)** — 자바 표준 저수준 API. SQL 문자열을 직접 작성하고 `Connection → Statement → ResultSet` 순서로 처리한다.
- **JPA(Jakarta Persistence API)** — 자바 ORM 표준 인터페이스. 테이블 대신 자바 객체(Entity)를 중심으로 생각하고, 실제 SQL은 구현체(Hibernate 등)가 생성한다.
- **MyBatis** — SQL을 XML 또는 어노테이션으로 직접 작성하되, `ResultSet` 처리·커넥션 관리 같은 반복 코드를 프레임워크가 대신한다.

입문자가 자주 혼동하는 점:

- JPA는 인터페이스(표준)이고, Hibernate는 그 구현체다 — "Spring Data JPA"는 그 위의 편의 레이어다
- MyBatis는 ORM이 아니다 — SQL을 직접 쓰기 때문에 매핑 대상이 객체가 아닌 결과 집합(ResultSet)이다
- JDBC는 직접 쓸 일이 드물지만, JPA와 MyBatis 모두 내부적으로 JDBC를 사용한다

## 한눈에 보기

| 항목 | JDBC | JPA (Hibernate) | MyBatis |
|---|---|---|---|
| SQL 작성 주체 | 개발자 | ORM 자동 생성 | 개발자 (XML/어노테이션) |
| 객체-테이블 매핑 | 없음 | 자동 | 수동 ResultMap |
| 복잡한 동적 SQL | 문자열 조합 필요 | JPQL/Criteria | XML `<if>` 태그 |
| 학습 곡선 | 낮음 | 높음 | 중간 |
| 주요 사용 환경 | Spring JDBC | Spring Boot + JPA | 복잡한 SQL 조회 중심 서비스 |

## 상세 분해

**JDBC 사용 흐름 (개요)**:

1. `DriverManager.getConnection(url, user, pw)` 으로 커넥션 획득
2. `Connection.prepareStatement(sql)` 으로 PreparedStatement 생성
3. 파라미터 바인딩 후 `executeQuery()` 또는 `executeUpdate()` 실행
4. `ResultSet` 에서 컬럼값 직접 꺼내기
5. `close()` 로 자원 반납

이 과정이 반복되기 때문에 스프링이 `JdbcTemplate` 으로 상용구를 줄여 준다.

**JPA 핵심 흐름**:

1. `@Entity` 클래스와 테이블을 매핑 선언
2. `EntityManager` 또는 Spring Data `Repository` 인터페이스로 조회/저장
3. 트랜잭션 내 변경 감지(Dirty Checking) → commit 시 자동 `UPDATE`

**MyBatis 핵심 흐름**:

1. `Mapper` 인터페이스 메서드와 XML `<select>/<insert>` 를 1:1 대응
2. MyBatis가 `PreparedStatement` 생성·실행·ResultSet→객체 변환을 담당
3. 동적 SQL은 XML 안 `<if>`, `<foreach>` 태그로 작성

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "JPA 쓰면 SQL 몰라도 된다" | JPA가 생성하는 SQL을 이해하지 못하면 N+1 문제, 인덱스 미사용 등의 성능 문제를 해결하기 어렵다 | JPA를 쓸 때도 실행 SQL을 로그에서 확인하는 습관을 유지한다 |
| "MyBatis는 구식이다" | 복잡한 조회 쿼리가 많은 서비스에서는 동적 SQL 표현력이 뛰어나 지금도 널리 쓰인다 | 비즈니스 특성(쓰기 중심 vs 조회 중심)에 맞게 선택한다 |
| "JDBC는 직접 쓰면 안 된다" | 단순 배치나 성능 임계점에서 `JdbcTemplate`/JDBC는 여전히 유효하다 | 레이어 추상화 비용이 없어야 할 상황인지 먼저 확인한다 |

## 실무에서 쓰는 모습

**(1) 신규 Spring Boot 서비스** — 대부분 Spring Data JPA를 기본으로 시작한다. `Repository` 인터페이스의 메서드 이름 규칙(`findByName`)만으로 단순 쿼리는 자동 완성된다.

**(2) 대용량 통계/보고서 쿼리** — GROUP BY, 서브쿼리, 여러 테이블 조인이 복잡하게 섞이는 경우 MyBatis XML로 SQL을 명시하거나, JPA + `@Query`(JPQL) 또는 QueryDSL로 복잡도를 관리한다.

## 더 깊이 가려면

- JPA N+1 문제, 연관관계 매핑, 영속성 컨텍스트 상세 → [JDBC, JPA, MyBatis 심화](./jdbc-jpa-mybatis.md)

cross-category bridge:

- Repository·DAO·Entity 계층 설계 원칙 → [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)

## 면접/시니어 질문 미리보기

> Q: JPA와 MyBatis 중 어떤 상황에서 어떤 것을 선택하나요?
> 의도: 기술 선택의 근거를 말할 수 있는지 확인
> 핵심: 도메인 모델 중심의 복잡한 비즈니스 로직은 JPA, 복잡한 조회 SQL이 핵심인 서비스는 MyBatis가 더 편하다. 두 가지를 한 프로젝트에서 혼용하기도 한다.

> Q: JPA의 N+1 문제가 무엇인가요?
> 의도: ORM 사용 시 발생하는 가장 흔한 성능 문제를 아는지 확인
> 핵심: 연관 엔티티를 lazy 로딩할 때 부모 N개를 조회하면 자식 조회 SQL이 N번 추가로 발생한다. `fetch join` 또는 `EntityGraph`로 해결한다.

## 한 줄 정리

JDBC는 SQL 직접 실행 저수준 API, JPA는 객체-테이블 자동 매핑 ORM 표준, MyBatis는 SQL을 직접 작성하되 반복 처리 코드를 줄여 주는 SQL 매퍼다.
