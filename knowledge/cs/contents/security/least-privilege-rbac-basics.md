# 최소 권한 원칙과 RBAC 기초

> 한 줄 요약: 최소 권한 원칙은 "필요한 권한만 줘라"이고, RBAC는 "역할을 묶어서 권한을 관리해라"다. 둘을 함께 쓰면 권한이 과도하게 퍼지는 사고를 예방한다.

**난이도: 🟢 Beginner**

관련 문서:

- [인증과 인가의 차이](./authentication-vs-authorization.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [Spring Security 기초](../spring/spring-security-basics.md)
- [Security 카테고리 README](./README.md)

retrieval-anchor-keywords: least privilege basics, rbac 기초, 역할 기반 접근 제어, 최소 권한 원칙이란, role based access control beginner, 권한 관리 입문, admin 권한 남용, 역할이란 뭔가요, rbac 왜 써요, permission vs role, spring security role, 권한 분리 기초, 권한을 나눠 주려면 어떻게 시작하나

## 빠른 복귀 링크

- security 전체 beginner 분기에서 다시 고르려면 [Security 카테고리 README](./README.md)로 돌아가면 된다.
- `인증은 됐는데 왜 403인가`까지 바로 이어서 보려면 다음 단계는 [인증과 인가의 차이](./authentication-vs-authorization.md)다.

## 핵심 개념

최소 권한 원칙(Principle of Least Privilege)은 단순하다. 어떤 사용자든 서비스든 "지금 하는 작업에 필요한 권한만" 가져야 한다. 이 원칙을 어기면 계정 하나가 털렸을 때 피해가 예상보다 훨씬 커진다.

예를 들어 게시글 목록을 조회하는 서비스가 DB 테이블 전체 삭제 권한을 가질 이유가 없다. 버그나 보안 허점이 생겼을 때 권한 범위가 넓을수록 피해가 크다.

RBAC(Role-Based Access Control)는 이 원칙을 실무에서 구현하는 가장 흔한 방법이다. 개별 사용자에게 권한을 하나하나 붙이는 대신, **역할(Role)**을 먼저 정의하고 역할에 권한을 묶은 뒤 사용자에게 역할을 부여한다.

## 한눈에 보기

**직접 권한 부여 방식 (관리하기 어려움)**

- 사용자 A → 게시글 읽기, 게시글 쓰기, 댓글 쓰기
- 사용자 B → 게시글 읽기, 게시글 쓰기, 댓글 쓰기, 댓글 삭제

**RBAC 방식 (역할 정의만 바꾸면 전체 적용)**

- 역할 "일반회원" → 게시글 읽기, 게시글 쓰기, 댓글 쓰기
- 역할 "관리자" → 일반회원 권한 + 댓글 삭제, 회원 관리
- 사용자 A → 역할 "일반회원" 부여
- 사용자 B → 역할 "관리자" 부여

## 상세 분해

### 역할(Role)이란

역할은 "이런 일을 하는 사람"이라는 그룹 레이블이다. `ROLE_USER`, `ROLE_ADMIN`, `ROLE_MANAGER` 같은 형태로 정의한다. 권한 변경이 필요할 때 역할 정의만 수정하면 그 역할을 가진 모든 사용자에게 적용된다.

### 권한(Permission / Authority)이란

특정 행동을 할 수 있는지의 단위다. `articles:read`, `articles:write`, `comments:delete` 같은 세분화된 형태다. RBAC에서는 역할이 여러 권한을 묶는다.

### 최소 권한 원칙을 서비스 계정에 적용하기

사람 사용자뿐 아니라 서비스 계정(DB 접속 계정, 외부 API 키)에도 최소 권한 원칙이 적용된다. 읽기만 하는 마이크로서비스의 DB 계정에 `DROP TABLE` 권한이 있을 필요가 없다. DB 사용자를 용도별로 분리하고 각각 최소 권한만 준다.

### 권한 에스컬레이션 주의

낮은 권한의 사용자가 높은 권한을 얻는 방법이 코드 안에 숨어 있으면 안 된다. 예를 들어 `userId`를 URL 파라미터로 받아서 그 사용자의 권한으로 행동하는 코드가 검증 없이 노출되면 안 된다.

## 흔한 오해와 함정

### "관리자 계정 하나로 모든 걸 처리하면 편하다"

개발 편의를 위해 모든 서비스가 관리자 계정을 공유하면, 하나의 서비스가 침해됐을 때 전체 시스템에 영향이 간다. 서비스별로 최소 권한의 계정을 분리하는 것이 원칙이다.

### "Spring Security에서 `ROLE_ADMIN`이면 모든 게 가능하다"

`ROLE_ADMIN`이 어떤 권한을 포함하는지는 코드에서 명시적으로 정의해야 한다. 역할 이름이 크다고 자동으로 모든 권한이 생기지 않는다. 역할과 권한의 매핑을 명확하게 문서화해야 한다.

### "권한 체크는 프론트엔드에서도 하고 있으니 괜찮다"

프론트엔드의 권한 체크는 UI 편의를 위한 것이고, 보안은 서버 사이드에서 검증해야 한다. 공격자는 브라우저를 우회해 API를 직접 호출할 수 있다.

## 실무에서 쓰는 모습

Spring Security에서 RBAC를 적용하는 기본 패턴은 두 가지다.

첫 번째는 URL 레벨 설정이다. `HttpSecurity`에서 특정 경로에 역할을 지정한다.

```java
.requestMatchers("/admin/**").hasRole("ADMIN")
.requestMatchers("/api/**").hasRole("USER")
```

두 번째는 메서드 레벨 설정이다. `@PreAuthorize`로 서비스 레이어에서 권한을 확인한다.

```java
@PreAuthorize("hasRole('ADMIN')")
public void deleteUser(Long userId) { ... }
```

자원 소유자 확인도 필요하다. 로그인한 사용자가 `userId=1`인데 `/users/2` 자원에 접근하려 하면 역할 외에도 소유권 체크가 필요하다.

## 이 문서 다음에 보면 좋은 문서

- 로그인 성공과 권한 허용을 먼저 분리하고 싶으면 [인증과 인가의 차이](./authentication-vs-authorization.md)로 이어 가면 된다.
- `role`만으로 안 끝나고 `scope`, `ownership`까지 같이 봐야 하는 beginner bridge가 필요하면 [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)를 보면 된다.
- security 카테고리 안에서 다른 auth primer나 authz symptom route를 다시 고르려면 [Security 카테고리 README](./README.md)로 돌아가면 된다.

## 면접/시니어 질문 미리보기

> Q: 최소 권한 원칙이란 무엇이고, 왜 중요한가요?
> 의도: 권한 설계의 기본 원칙을 이해하는지 확인
> 핵심: 필요한 권한만 부여해서 침해 발생 시 피해 범위를 최소화한다. 사용자뿐 아니라 서비스 계정과 DB 계정에도 적용한다.

> Q: 개별 사용자에게 권한을 직접 부여하는 방식과 RBAC의 차이는 무엇인가요?
> 의도: RBAC의 관리 이점을 이해하는지 확인
> 핵심: RBAC는 역할 정의를 바꾸면 그 역할을 가진 모든 사용자에게 일괄 반영되어 관리가 쉽다. 직접 부여 방식은 사용자가 많아질수록 관리 비용이 급증한다.

## 한 줄 정리

최소 권한 원칙은 필요한 것만 주는 것이고, RBAC는 역할로 묶어서 관리하는 것이며, 서버 사이드 권한 체크 없이 프론트엔드 체크만으로는 보안이 되지 않는다.
