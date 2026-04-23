# Spring Security Method Security Deep Dive

> 한 줄 요약: Method security는 URL 차단보다 더 가까운 곳에서 권한을 강제하지만, 프록시 경계와 표현식, 호출 흐름을 이해하지 못하면 쉽게 빠져나간다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)

retrieval-anchor-keywords: method security, @PreAuthorize, @PostAuthorize, @Secured, @RolesAllowed, authorization expression, proxy boundary, security context, permission evaluator

## 핵심 개념

Method security는 "이 URL에 들어오면 막는다"가 아니라, "이 메서드를 호출할 수 있는가"를 본다.

- URL security: 요청 레벨 차단
- Method security: 서비스 메서드 레벨 차단

이 차이는 중요하다.

- URL은 컨트롤러 진입 전에 막을 수 있다
- method security는 더 세밀한 도메인 규칙을 걸 수 있다
- 동일한 서비스가 여러 진입점에서 호출돼도 규칙을 유지할 수 있다

즉, method security는 권한을 비즈니스 로직에 더 가깝게 붙이는 장치다.

## 깊이 들어가기

### 1. method security는 proxy 기반이다

```java
@Service
public class PaymentService {

    @PreAuthorize("hasRole('ADMIN')")
    public void cancelAll() {
        ...
    }
}
```

이 어노테이션은 AOP proxy를 통해 실행 전후에 권한 검사를 건다.

그래서 다음 함정이 생긴다.

- 내부 self-invocation은 프록시를 안 탈 수 있다
- final/private 메서드는 제약이 있다
- 빈 밖에서 new로 만든 객체에는 적용되지 않는다

이 문맥은 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)과 같이 봐야 한다.

### 2. `@PreAuthorize`와 `@PostAuthorize`는 시점이 다르다

- `@PreAuthorize`: 실행 전에 검사
- `@PostAuthorize`: 실행 후 결과를 보고 검사

```java
@PreAuthorize("hasRole('ADMIN')")
public void deleteUser(Long id) {
    ...
}

@PostAuthorize("returnObject.owner == authentication.name")
public DocumentDto getDocument(Long id) {
    ...
}
```

`@PostAuthorize`는 결과를 봐야 할 때 유용하지만, 이미 메서드가 실행된 뒤라 비용이 크다.

### 3. `@Secured`와 `@RolesAllowed`는 더 단순한 표현이다

이 두 방식은 표현식 기반보다 단순하지만, 복잡한 도메인 조건에는 약하다.

- `@Secured`: 역할 목록 중심
- `@RolesAllowed`: JSR-250 스타일
- `@PreAuthorize`: SpEL 기반의 유연한 표현

실무에서는 대부분 `@PreAuthorize`가 가장 유연하다.

### 4. `PermissionEvaluator`는 도메인 권한의 탈출구다

권한이 "관리자냐 아니냐" 수준을 넘으면 도메인 대상별 권한 검사가 필요하다.

```java
@PreAuthorize("hasPermission(#documentId, 'Document', 'WRITE')")
public void edit(Long documentId) {
    ...
}
```

이때 `PermissionEvaluator`를 붙이면 객체/소유자/상태 기반 권한을 처리할 수 있다.

### 5. method security는 호출 경로가 아니라 계약을 보장한다

컨트롤러에서 한 번 검사했다고 서비스 안에서 안심하면 안 된다.

- 다른 컨트롤러
- 배치
- 메시지 소비자
- 내부 서비스 호출

이런 경로가 모두 같은 권한 계약을 공유해야 할 수 있다.

## 실전 시나리오

### 시나리오 1: 컨트롤러에서는 막혔는데 서비스는 직접 호출됐다

컨트롤러 보안만으로는 내부 호출 경로를 막지 못한다.

- 배치 작업
- 이벤트 리스너
- 다른 서비스 계층

같은 서비스 메서드를 호출할 수 있다.

### 시나리오 2: `@PreAuthorize`가 있는데도 self-invocation으로 빠졌다

같은 클래스 내부 호출은 프록시를 안 거칠 수 있다.

이 문제는 AOP 기반 method security의 전형적인 함정이다.

### 시나리오 3: 권한 표현식이 길어져서 읽기 어려워졌다

SpEL은 유연하지만, 너무 많은 비즈니스 규칙을 넣으면 가독성이 떨어진다.

이 경우는 커스텀 `PermissionEvaluator`나 도메인 서비스로 옮기는 게 낫다.

### 시나리오 4: `@PostAuthorize`가 느리다

결과를 만든 뒤 검사하므로 비싼 조회 뒤에 거절될 수 있다.

가능하면 `@PreAuthorize`로 앞에서 잘라내는 편이 효율적이다.

## 코드로 보기

### pre authorize

```java
@Service
public class OrderAdminService {

    @PreAuthorize("hasRole('ADMIN')")
    public void cancelAllOrders() {
        ...
    }
}
```

### post authorize

```java
@PostAuthorize("returnObject.owner == authentication.name")
public OrderDto findOrder(Long id) {
    return orderQueryService.find(id);
}
```

### permission evaluator

```java
@PreAuthorize("hasPermission(#documentId, 'Document', 'WRITE')")
public void editDocument(Long documentId) {
    documentService.edit(documentId);
}
```

### method security enablement

```java
@Configuration
@EnableMethodSecurity
public class MethodSecurityConfig {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| URL security | 요청을 일찍 막는다 | 도메인 단위 제어는 약하다 | 공통 경로 보안 |
| Method security | 서비스 경계에 가깝다 | 프록시/호출 경로 함정이 있다 | 세밀한 권한 강제 |
| `@PreAuthorize` | 가장 유연하다 | 표현식이 길어질 수 있다 | 복합 조건 |
| `@PostAuthorize` | 결과 기반 검사가 가능하다 | 늦게 막아서 비용이 든다 | 소유권/결과 의존 판단 |

핵심은 URL과 method security를 대체 관계로 보지 말고, **서로 다른 깊이의 안전망**으로 보는 것이다.

## 꼬리질문

> Q: method security와 URL security의 차이는 무엇인가?
> 의도: 보안 계층 구분 확인
> 핵심: URL은 요청 단위, method security는 서비스 메서드 단위다.

> Q: `@PreAuthorize`가 self-invocation에서 깨질 수 있는 이유는 무엇인가?
> 의도: 프록시 경계 이해 확인
> 핵심: AOP proxy를 거쳐야 실행되기 때문이다.

> Q: `@PostAuthorize`는 언제 써야 하는가?
> 의도: 실행 전/후 권한 검사 구분 확인
> 핵심: 결과 객체를 보고 판단해야 할 때다.

> Q: `PermissionEvaluator`는 왜 필요한가?
> 의도: 객체/소유자 기반 권한 이해 확인
> 핵심: 단순 role 체크를 넘어 도메인 대상별 권한을 다루기 위해서다.

## 한 줄 정리

Method security는 서비스 경계에서 권한을 강제하는 강한 도구지만, proxy 기반이므로 호출 경로와 표현식 복잡도를 같이 관리해야 한다.
