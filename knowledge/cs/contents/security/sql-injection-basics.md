---
schema_version: 3
title: SQL 인젝션 기초
concept_id: security/sql-injection-basics
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 70
mission_ids: []
review_feedback_tags:
- sql injection basics
- sql 인젝션이 뭐예요
- preparedstatement 왜 써야 해요
- 사용자 입력 쿼리 위험
aliases:
- sql injection basics
- sql 인젝션이 뭐예요
- preparedstatement 왜 써야 해요
- 사용자 입력 쿼리 위험
- 쿼리 조작 공격
- beginner sql injection
- sql injection prevention
- parameterized query
- sql injection example
- database attack beginner
- security readme sql injection primer
- security beginner route
symptoms: []
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/security/sql-injection-beyond-preparedstatement.md
- contents/security/input-validation-basics.md
- contents/security/security-basics-what-and-why.md
- contents/security/idor-bola-patterns-and-fixes.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- SQL 인젝션 기초 핵심 개념을 설명해줘
- sql injection basics가 왜 필요한지 알려줘
- SQL 인젝션 기초 실무 설계 포인트는 뭐야?
- sql injection basics에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 SQL 인젝션 기초를 다루는 primer 문서다. SQL 인젝션은 사용자 입력이 SQL 쿼리의 일부로 해석되는 취약점이고, PreparedStatement로 입력을 값(파라미터)과 구조(쿼리)를 분리하면 막을 수 있다. 검색 질의가 sql injection basics, sql 인젝션이 뭐예요, preparedstatement 왜 써야 해요, 사용자 입력 쿼리 위험처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# SQL 인젝션 기초

> 한 줄 요약: SQL 인젝션은 사용자 입력이 SQL 쿼리의 일부로 해석되는 취약점이고, PreparedStatement로 입력을 값(파라미터)과 구조(쿼리)를 분리하면 막을 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [SQL 인젝션: PreparedStatement를 넘어서](./sql-injection-beyond-preparedstatement.md)
- [입력값 검증 기초](./input-validation-basics.md)
- [보안 기초: 왜 보안이 필요한가](./security-basics-what-and-why.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: sql injection basics, sql 인젝션이 뭐예요, preparedstatement 왜 써야 해요, 사용자 입력 쿼리 위험, 쿼리 조작 공격, beginner sql injection, sql injection prevention, parameterized query, sql injection example, database attack beginner, security readme sql injection primer, security beginner route, security primer next step, return to security readme, 문자열 이어 붙여 쿼리 만들 때

## 이 문서 다음에 보면 좋은 문서

- security 입문 문서 안에서 다른 primer를 다시 고르고 싶으면 [Security README 기본 primer 묶음](./README.md#기본-primer)으로 돌아가면 된다.
- "입력 검증을 했는데도 왜 SQL 인젝션을 따로 막아야 하지?"가 헷갈리면 [입력값 검증 기초](./input-validation-basics.md)를 같이 보면 validation과 파라미터 바인딩의 역할이 분리된다.
- ORM, 동적 정렬, native query처럼 PreparedStatement 바깥의 함정을 더 보려면 [SQL 인젝션: PreparedStatement를 넘어서](./sql-injection-beyond-preparedstatement.md)로 이어 가면 된다.

## 핵심 개념

SQL 인젝션은 서버가 사용자 입력을 SQL 쿼리 문자열에 그대로 이어 붙일 때 발생한다. 공격자가 입력값 안에 SQL 문법을 섞으면, 서버는 그것을 "데이터"가 아니라 "명령"으로 실행한다. 입문자가 헷갈리는 이유는 "그냥 문자열 붙이기"처럼 보이는 코드가 실제로는 쿼리 구조를 바꿀 수 있다는 점을 직관적으로 파악하기 어렵기 때문이다.

## 한눈에 보기

사용자 입력을 SQL 문자열에 직접 이어 붙이면 입력이 "데이터"가 아닌 "명령"으로 실행될 수 있다.

```
[취약한 패턴]
String sql = "SELECT * FROM users WHERE id = '" + userInput + "'";
userInput = "' OR '1'='1"
→ SELECT * FROM users WHERE id = '' OR '1'='1'  (모든 행 반환)
```

PreparedStatement를 사용하면 `?` 자리에 들어오는 값은 항상 데이터로만 처리된다.

```
[안전한 패턴]
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setString(1, userInput);
→ ?는 항상 값으로만 처리됨 (SQL 구조 변경 불가)
```

## 상세 분해

- **문자열 이어 붙이기(String concatenation)**: 쿼리와 입력값을 `+`로 합치면, 입력에 포함된 따옴표·세미콜론·주석(`--`)이 SQL 문법으로 해석된다.
- **PreparedStatement의 역할**: 쿼리 구조(뼈대)를 먼저 DB에 전달하고, 이후 파라미터를 값으로만 바인딩한다. DB는 `?` 자리에 들어온 모든 것을 명령어가 아닌 데이터로 취급한다.
- **ORM을 써도 위험한 경우**: JPA의 `JPQL`이나 MyBatis에서도 `${param}` 방식으로 문자열을 직접 삽입하면 취약하다. `#{param}` 방식(파라미터 바인딩)을 써야 한다.
- **영향 범위**: 데이터 조회(모든 사용자 정보 노출)뿐 아니라 데이터 수정·삭제, 심지어 OS 명령 실행까지 이어질 수 있다.

## 흔한 오해와 함정

- **"입력값을 앞뒤에서 따옴표로 감싸면 괜찮다"** → 공격자는 따옴표를 닫고 그 뒤에 추가 SQL을 붙인다. 이스케이프 처리보다 파라미터 바인딩이 근본 해결책이다.
- **"숫자 타입이라 문자열 문제가 없다"** → 숫자도 형 변환 없이 그대로 이어 붙이면 `1 OR 1=1` 같은 조작이 가능하다.
- **"ORM을 쓰니까 자동으로 안전하다"** → native query나 동적 쿼리 빌더에서 문자열 직접 삽입이 섞이면 여전히 위험하다.

## 실무에서 쓰는 모습

- **Spring JDBC**: `JdbcTemplate`의 `query("... WHERE id = ?", userId)` 형태로 파라미터 바인딩을 항상 사용한다.
- **JPA**: `@Query("SELECT u FROM User u WHERE u.id = :id")` + `@Param("id")`로 JPQL 파라미터 바인딩을 사용한다. 동적 쿼리는 Criteria API나 QueryDSL을 통해 빌드한다. `nativeQuery = true`일 때도 `?1` / `:param` 방식을 쓰고, 절대 문자열 직접 이어 붙이지 않는다.
- **MyBatis**: `#{id}` 방식만 사용하고, 동적 정렬 컬럼 등 구조적 요소가 필요한 경우 허용 목록(allowlist) 방식으로 검증 후 `${}`를 최소 사용한다.

## 더 깊이 가려면

- [SQL 인젝션: PreparedStatement를 넘어서](./sql-injection-beyond-preparedstatement.md) — 2차 인젝션, ORM 취약 패턴, 저장 프로시저 등 심화 내용
- [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md) — 쿼리 조작과 함께 자주 등장하는 수평 권한 상승 패턴

## 면접/시니어 질문 미리보기

- **"PreparedStatement가 SQL 인젝션을 막는 이유를 DB 레벨에서 설명해 보세요."** → DB가 쿼리 구조를 먼저 컴파일/파싱한 뒤 파라미터를 값으로만 바인딩하므로, 파라미터 내용이 SQL 구조에 영향을 줄 수 없다는 점을 설명한다.
- **"JPA를 쓰면 SQL 인젝션이 없다고 볼 수 있나요?"** → native query나 동적 정렬에서 문자열 직접 삽입을 피해야 하고, ORM이 자동으로 모든 입력을 안전하게 만들어 주지 않는다는 점을 설명한다.

## 한 줄 정리

SQL 인젝션은 사용자 입력을 쿼리 구조와 분리하지 않아서 생기며, PreparedStatement/파라미터 바인딩으로 입력을 항상 "값"으로만 처리하는 것이 핵심 방어다.
