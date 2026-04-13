# SQL Injection beyond PreparedStatement

> 한 줄 요약: PreparedStatement는 값 바인딩을 안전하게 해주지만, SQL 구조 자체를 안전하게 만들지는 못한다. 식별자, 정렬, 동적 조건, 2차 저장값이 남는 구멍을 같이 막아야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [비밀번호 저장: bcrypt / scrypt / argon2](./password-storage-bcrypt-scrypt-argon2.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [MySQL 온라인 스키마 변경 전략](../database/online-schema-change-strategies.md)
> - [슬로우 쿼리 분석 플레이북](../database/slow-query-analysis-playbook.md)

---

## 핵심 개념

PreparedStatement는 `WHERE name = ?`처럼 **값**을 안전하게 바인딩하는 데 강하다.  
하지만 SQL 문장의 구조를 만들 때는 여전히 취약할 수 있다.

대표적인 취약 지점:

- 컬럼명, 테이블명, 정렬 방향 같은 식별자
- `ORDER BY`, `LIMIT`, `OFFSET`
- 동적 `IN (...)`
- `LIKE` 패턴 조합
- 저장된 값이 나중에 다시 SQL로 합쳐지는 2차 인젝션

즉, "PreparedStatement를 썼다"는 이유만으로 안전하다고 말하면 안 된다.

---

## 깊이 들어가기

### 1. PreparedStatement가 막는 것과 못 막는 것

잘 막는 것:

- 문자열 값 주입
- 따옴표 탈출
- 기본적인 `' OR 1=1 --` 형태 공격

못 막는 것:

- 식별자 주입
- SQL 문법 구조 조작
- 쿼리 조각 문자열 연결

### 2. 식별자 인젝션

```java
String sql = "SELECT * FROM users ORDER BY " + sort + " " + direction;
```

`sort`와 `direction`은 바인딩할 수 없다.  
이런 값은 allowlist로만 받아야 한다.

### 3. 2차 SQL Injection

한 번 저장된 값이 나중에 SQL로 다시 합쳐지는 경우가 있다.

- 관리자 메모
- 배치 작업 메타데이터
- 검색 조건 빌더

입력 시점에는 무해해 보여도, 출력 시점에 SQL 조각이 되면 터진다.

### 4. ORM과 동적 쿼리

ORM을 써도 안전이 자동 보장되는 것은 아니다.

- JPQL 문자열을 이어 붙이면 취약해진다
- Native SQL을 조합하면 동일하게 위험하다
- Criteria API나 Query DSL도 구조 검증을 무시하면 안전하지 않다

---

## 실전 시나리오

### 시나리오 1: 정렬 파라미터가 주입 경로가 됨

```java
String sql = "SELECT id, email FROM users ORDER BY " + sort + " " + direction;
```

공격자는 `sort=id; DROP TABLE users; --` 같은 값을 노린다.  
드라이버 설정에 따라 방어가 덜 된 환경이면 바로 사고로 이어질 수 있다.

해결은 allowlist다.

### 시나리오 2: 동적 IN 절을 문자열로 붙임

```java
String sql = "SELECT * FROM orders WHERE id IN (" + idsCsv + ")";
```

CSV 문자열을 직접 합치면 숫자만 들어가야 한다는 가정이 깨진다.  
항목 수에 맞는 placeholder를 만들어 바인딩해야 한다.

### 시나리오 3: 검색 화면의 LIKE 조건이 깨짐

사용자 검색어에 `%`와 `_`가 섞이면 의도치 않은 광범위 조회가 된다.  
SQL injection은 아니더라도 데이터 노출/부하 이슈가 된다.

### 시나리오 4: 관리자 리포트용 필터가 배치에서 터짐

UI에서만 쓰는 정렬/필터 값을 배치 작업에서도 재사용하다가 입력 검증이 약해진다.  
실제 사고는 이런 "재사용" 경로에서 많이 난다.

---

## 코드로 보기

### 1. 위험한 방식

```java
public List<User> search(String sort, String direction) {
    String sql = "SELECT id, email FROM users ORDER BY " + sort + " " + direction;
    return jdbcTemplate.query(sql, userRowMapper);
}
```

### 2. allowlist 기반 방어

```java
public List<User> search(String sort, String direction) {
    String safeSort = switch (sort) {
        case "createdAt" -> "created_at";
        case "email" -> "email";
        default -> throw new IllegalArgumentException("invalid sort");
    };

    String safeDirection = "desc".equalsIgnoreCase(direction) ? "DESC" : "ASC";
    String sql = "SELECT id, email FROM users ORDER BY " + safeSort + " " + safeDirection;
    return jdbcTemplate.query(sql, userRowMapper);
}
```

### 3. 동적 IN 절은 placeholder로 처리

```java
public List<Order> findByIds(List<Long> ids) {
    String placeholders = ids.stream().map(id -> "?").collect(java.util.stream.Collectors.joining(","));
    String sql = "SELECT * FROM orders WHERE id IN (" + placeholders + ")";
    return jdbcTemplate.query(sql, ids.toArray(), orderRowMapper);
}
```

핵심은 값은 바인딩하고, 구조는 allowlist로 제한하는 것이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| PreparedStatement | 값 바인딩을 안전하게 해준다 | 구조 인젝션은 못 막는다 | 기본값 |
| ORM + 파라미터 바인딩 | 생산성이 높다 | 동적 문자열 조합이 남는다 | 일반 CRUD |
| allowlist 기반 구조 생성 | 식별자 인젝션을 줄인다 | 코드가 길어진다 | 정렬/필터/동적 리포트 |
| SQL 직접 조합 | 유연하다 | 사고 나기 쉽다 | 거의 안 쓰는 편이 낫다 |

핵심 판단 기준은 다음이다.

- 이 입력이 값인가, 구조인가
- 구조라면 allowlist로 제한 가능한가
- 저장된 값이 나중에 SQL 조각이 되지 않는가

---

## 꼬리질문

> Q: PreparedStatement를 쓰면 SQL Injection이 끝난다고 말할 수 없는 이유는?
> 의도: 값 바인딩과 SQL 구조 안전성을 구분하는지 확인
> 핵심: 식별자와 SQL 조각은 여전히 위험하다.

> Q: `ORDER BY`는 왜 자주 취약점이 되는가?
> 의도: 바인딩 가능한 값과 아닌 값을 구분하는지 확인
> 핵심: 컬럼명과 정렬 방향은 placeholder로 처리되지 않는다.

> Q: 2차 SQL Injection은 왜 발견이 늦는가?
> 의도: 입력 시점과 실행 시점의 분리를 이해하는지 확인
> 핵심: 저장 시점에는 정상처럼 보이기 때문이다.

## 한 줄 정리

PreparedStatement는 값 주입만 막아주므로, SQL 구조는 allowlist와 동적 쿼리 검증까지 포함해서 방어해야 한다.
