# Middleware Pattern Language: 요청과 응답 사이에 끼는 공통 관심사

> 한 줄 요약: Middleware는 요청/응답 파이프라인 중간에 들어가 공통 관심사를 조합하는 패턴 언어다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
> - [Pipeline vs Chain of Responsibility](./pipeline-vs-chain-of-responsibility.md)
> - [Retry Policy vs Decorator Chain](./retry-policy-vs-decorator-chain.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Middleware는 웹 프레임워크에서 흔히 보지만, 더 넓게 보면 **요청 흐름을 조작하는 중간 계층**이다.

- auth
- logging
- tracing
- rate limit
- error translation

### Retrieval Anchors

- `middleware pattern`
- `request response pipeline`
- `cross-cutting concern`
- `middleware stack`
- `before after hooks`

---

## 깊이 들어가기

### 1. middleware는 조합의 언어다

각 middleware는 작은 책임만 가진다.  
순서와 조합이 전체 행동을 만든다.

### 2. Chain보다 더 프레임워크적이다

Chain of Responsibility는 객체 설계 관점이 강하고, Middleware는 요청 처리 스택 관점이 강하다.

### 3. 순서가 곧 정책이다

middleware는 등록 순서가 결과를 바꾼다.

- auth 먼저
- logging 나중
- error translation은 가장 바깥

---

## 실전 시나리오

### 시나리오 1: HTTP 요청 처리

인증, 추적 id, 에러 핸들링을 middleware로 분리한다.

### 시나리오 2: 배치 job 실행

실행 전후 공통 훅을 조합할 때도 유용하다.

### 시나리오 3: 메시지 처리

소비 전후 공통 로직을 middleware처럼 붙일 수 있다.

---

## 코드로 보기

### Middleware interface

```java
public interface Middleware {
    Response handle(Request request, Next next);
}
```

### Example

```java
public class AuthMiddleware implements Middleware {
    @Override
    public Response handle(Request request, Next next) {
        if (!request.isAuthorized()) {
            return Response.unauthorized();
        }
        return next.run(request);
    }
}
```

### Stack

```java
// middleware1 -> middleware2 -> handler
```

Middleware는 공통 관심사를 조합하기 좋은 패턴 언어다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 전/후처리 | 단순하다 | 중복이 늘어난다 | 소규모 |
| Middleware stack | 조합이 쉽다 | 순서 추적이 필요하다 | 공통 관심사가 많을 때 |
| Chain of Responsibility | 책임 분리가 명확하다 | 흐름이 숨겨질 수 있다 | 차단/위임 |

판단 기준은 다음과 같다.

- 요청 흐름 공통 기능이면 middleware
- 중단과 위임이 중요하면 chain
- 순서가 정책이므로 문서화해야 한다

---

## 꼬리질문

> Q: middleware와 chain of responsibility는 같은 건가요?
> 의도: 스타일과 구조를 구분하는지 확인한다.
> 핵심: 비슷하지만 middleware는 요청 스택에 더 가깝다.

> Q: middleware 순서가 왜 중요한가요?
> 의도: 조합과 정책의 관계를 아는지 확인한다.
> 핵심: 앞뒤 순서가 결과를 바꾸기 때문이다.

> Q: middleware를 너무 많이 쓰면 어떤가요?
> 의도: 추적 가능성의 한계를 아는지 확인한다.
> 핵심: 실행 경로가 복잡해진다.

## 한 줄 정리

Middleware는 요청과 응답 사이에 공통 관심사를 끼워 넣는 조합형 패턴 언어다.

