# Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`

> 한 줄 요약: self-invocation 문제는 `@Transactional` 하나의 예외가 아니라, 프록시 기반 애노테이션 전반에서 같은 원리로 반복되는 함정이므로 "어떤 애노테이션이 왜 내부 호출에서 빠지는지"를 한 번에 묶어 보는 편이 실전적이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
> - [Spring Method Validation Proxy Pitfalls](./spring-method-validation-proxy-pitfalls.md)
> - [Spring Security Method Security Deep Dive](./spring-security-method-security-deep-dive.md)
> - [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)

retrieval-anchor-keywords: self invocation, proxy trap, internal call bypass proxy, transactional self invocation, async self invocation, cacheable self invocation, validated self invocation, preauthorize self invocation, AopContext

## 핵심 개념

Spring에서 self-invocation 문제를 처음 배울 때 보통 `@Transactional` 예제로 접한다.

하지만 실제로는 같은 원리가 여러 애노테이션에 반복된다.

- `@Transactional`
- `@Async`
- `@Cacheable`
- `@Validated`
- `@PreAuthorize`

공통 원리는 단순하다.

- 외부에서 프록시를 통해 들어오면 interception이 된다
- 같은 객체 내부에서 `this.method()`로 부르면 프록시를 우회한다

즉 self-invocation은 특정 애노테이션 버그가 아니라, **프록시 기반 기능 전체에 공통인 구조적 함정**이다.

## 깊이 들어가기

### 1. 문제의 본질은 애노테이션이 아니라 호출 경로다

같은 코드를 봐도 중요한 질문은 "무슨 애노테이션이 붙었나?"보다 "누가 누구를 어떻게 호출하나?"다.

```java
public void outer() {
    this.inner(); // proxy bypass
}
```

여기서 `inner()`에 어떤 프록시 기반 애노테이션이 붙든, 원칙적으로는 비슷한 위험이 생긴다.

즉 self-invocation은 기능별 예외 목록이 아니라, **호출 경로 모델**로 이해해야 한다.

### 2. annotation별로 깨지는 증상은 다르게 보인다

같은 구조지만 현상은 다르게 체감된다.

| 애노테이션 | self-invocation 시 흔한 증상 |
|---|---|
| `@Transactional` | 트랜잭션이 안 열리거나 전파/롤백 기대가 깨짐 |
| `@Async` | 비동기 실행이 안 되고 같은 스레드에서 바로 실행됨 |
| `@Cacheable` | 캐시를 안 타고 매번 실제 메서드 실행 |
| `@Validated` | 메서드 파라미터/리턴값 검증이 조용히 빠짐 |
| `@PreAuthorize` | 메서드 보안 검사가 안 걸림 |

즉 "작동 안 함"은 같지만, **무엇이 빠졌는지는 기능마다 다르게 보인다**.

### 3. 복합 애노테이션일수록 더 헷갈린다

한 메서드에 여러 프록시 기반 기능이 같이 붙으면 self-invocation은 더 위험하다.

예:

- `@Transactional` + `@CacheEvict`
- `@Async` + `@Transactional`
- `@PreAuthorize` + `@Validated`

이 경우 일부만 빠지고 일부는 다른 경로에서 살아 있는 것처럼 보여, 디버깅이 더 어려워진다.

즉 self-invocation 문제는 단일 기능보다, **애노테이션 조합이 많을수록 더 운영적으로 헷갈린다**.

### 4. 해결은 프록시를 억지로 끌어오는 것보다 경계를 나누는 편이 낫다

보통 더 좋은 방향은 아래다.

- 메서드를 다른 빈으로 분리
- orchestration service와 worker service 분리
- 내부 helper는 프록시 기대 없이 순수 로직으로 유지

`AopContext.currentProxy()`나 self injection은 가능할 수 있다.

하지만 이런 우회는 대개 다음 대가가 있다.

- 구조가 프록시 구현에 묶인다
- 테스트가 지저분해진다
- 팀원이 읽기 어렵다

즉 해결의 기본은 마법이 아니라, **호출 경계를 프록시가 탈 수 있는 방향으로 다시 그리는 것**이다.

### 5. "같은 클래스에 있으니 자연스럽다"는 감각이 오히려 위험하다

서비스 메서드를 잘게 나누다 보면 내부 호출이 자연스러워 보인다.

하지만 프록시 기반 기능이 붙는 순간, 같은 클래스 배치는 단순한 리팩터링 취향이 아니라 실행 의미를 바꾼다.

즉 메서드 위치는 코드 스타일이 아니라, **interception 가능 여부를 결정하는 구조 요소**가 된다.

### 6. 디버깅은 기능별 현상보다 공통 원리를 먼저 보는 것이 빠르다

문제가 보이면 먼저 묻는다.

- 이 메서드는 외부 빈에서 프록시를 통해 불렸는가
- 아니면 같은 객체 내부에서 직접 호출됐는가

이 질문 하나로 트랜잭션, 캐시, 보안, 검증, 비동기 문제 상당수가 동시에 좁혀진다.

## 실전 시나리오

### 시나리오 1: `@Async`가 붙었는데 로그가 같은 스레드에서 찍힌다

내부 호출로 프록시를 우회했을 수 있다.

### 시나리오 2: 캐시가 붙은 조회 메서드가 내부 호출에서는 매번 DB를 친다

`@Cacheable`도 같은 프록시 구조를 쓰므로 self-invocation 영향을 받는다.

### 시나리오 3: `@PreAuthorize`가 서비스 내부 호출에서는 무력화된다

보안 문제처럼 보여도 본질은 method-security proxy bypass일 수 있다.

### 시나리오 4: `@Validated`가 붙었는데 내부 helper 경로에선 검증이 안 된다

validation도 interception 기반이면 같은 구조 문제를 가진다.

## 코드로 보기

### 위험한 구조

```java
@Service
public class OrderService {

    public void place() {
        save(); // self-invocation
    }

    @Transactional
    public void save() {
    }
}
```

### 더 나은 분리

```java
@Service
public class OrderFacade {

    private final OrderWriter orderWriter;

    public void place() {
        orderWriter.save();
    }
}
```

### 최후 수단

```java
((OrderService) AopContext.currentProxy()).save();
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 내부 호출 유지 | 코드가 한 곳에 모인다 | 프록시 기반 기능이 조용히 빠질 수 있다 | 프록시 기능이 없는 순수 로직 |
| 별도 빈 분리 | 실행 의미가 명확하다 | 클래스 수가 늘어난다 | 트랜잭션/보안/캐시/비동기 경계 |
| self injection / `AopContext` | 빠른 우회가 가능하다 | 구조가 불투명해진다 | 정말 제한적으로 |
| AspectJ 등 다른 접근 | self-invocation 제약을 줄일 수 있다 | 복잡도와 운영 부담이 있다 | 매우 특수한 경우 |

핵심은 self-invocation을 `@Transactional` 특수 사례로 보지 않고, **프록시 기반 annotation 전체의 공통 위험 모델**로 보는 것이다.

## 꼬리질문

> Q: self-invocation 문제가 여러 애노테이션에서 반복되는 이유는 무엇인가?
> 의도: 공통 구조 원리 이해 확인
> 핵심: 모두 프록시를 통한 interception에 의존하기 때문이다.

> Q: `@Async` self-invocation은 어떤 식으로 보일 수 있는가?
> 의도: 현상 차이 이해 확인
> 핵심: 비동기화가 안 되고 같은 스레드에서 즉시 실행될 수 있다.

> Q: 가장 기본적인 해결은 무엇인가?
> 의도: 구조적 해결 우선순위 확인
> 핵심: 프록시를 탈 수 있도록 메서드를 다른 빈/경계로 분리하는 것이다.

> Q: 왜 `AopContext.currentProxy()`는 최후 수단인가?
> 의도: 우회책의 비용 인식 확인
> 핵심: 코드 구조가 프록시 구현 세부사항에 강하게 묶이기 때문이다.

## 한 줄 정리

self-invocation은 `@Transactional`만의 함정이 아니라, 프록시 기반 annotation 전체에서 반복되는 공통 구조 문제다.
