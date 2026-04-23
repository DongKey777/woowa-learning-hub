# AOP 기초: 관점 지향 프로그래밍이 왜 필요한가

> 한 줄 요약: AOP는 로깅·트랜잭션·보안처럼 여러 곳에 반복되는 "횡단 관심사"를 비즈니스 로직과 분리해 한 곳에서 관리하는 프로그래밍 기법이다.

**난이도: 🟢 Beginner**

관련 문서:

- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- [IoC와 DI 기초](./spring-ioc-di-basics.md)
- [software-engineering API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: aop basics, 스프링 aop 처음, aspect 뭐예요, 횡단 관심사 입문, cross-cutting concern beginner, pointcut 뭐예요, advice 뭐예요, joinpoint 입문, spring aop 왜 써요, proxy aop beginner, 로깅 aop 입문, before after around advice

## 핵심 개념

`OrderService`에 트랜잭션 로그를 추가하고 싶다고 해보자. `OrderService`, `PaymentService`, `MemberService` … 모든 서비스마다 같은 로그 코드를 복붙한다면? 로그 형식이 바뀌면 50개 클래스를 전부 수정해야 한다.

AOP(Aspect-Oriented Programming, 관점 지향 프로그래밍)는 이 반복 코드를 "관점(Aspect)"으로 분리해 **한 곳에서 정의하고, 여러 곳에 자동으로 적용**한다. Spring은 이를 프록시 객체를 통해 런타임에 끼워 넣는 방식으로 구현한다.

## 한눈에 보기

```text
[호출자]
   ↓
[프록시(Aspect 적용)]  ← 로깅, 트랜잭션 등 횡단 관심사
   ↓
[실제 서비스 메서드]   ← 순수 비즈니스 로직
```

| 용어 | 의미 |
|---|---|
| Aspect | 횡단 관심사를 담은 모듈 (예: 로깅 Aspect) |
| Advice | 언제 어떤 코드를 실행할지 (Before / After / Around) |
| Pointcut | 어떤 메서드에 Advice를 적용할지 선택 표현식 |
| JoinPoint | Advice가 실제로 끼어드는 실행 지점 (메서드 호출 시점) |

## 상세 분해

- **Before Advice**: 메서드 실행 전에 동작. 예: 입력값 로깅, 권한 확인.
- **After Advice**: 메서드 실행 후에 동작(예외 여부 무관). 예: 실행 완료 기록.
- **Around Advice**: 메서드 실행 전후를 감쌈. `proceed()`를 직접 호출해야 원래 메서드가 실행됨. 가장 강력하지만 실수하면 메서드가 아예 안 불린다.
- **Pointcut 표현식**: `execution(* com.example.service.*.*(..))` 같은 형태로 패키지·클래스·메서드 이름 패턴을 지정한다.
- **@Transactional도 AOP**: Spring의 `@Transactional`은 Around Advice로 트랜잭션을 열고 닫는다. AOP 없이는 선언적 트랜잭션이 불가능하다.

## 흔한 오해와 함정

**오해 1: AOP는 복잡하니 쓸 일이 없다**
로그, 트랜잭션, 보안 검사 등 이미 매일 쓰는 Spring 기능이 AOP 위에 구현돼 있다. 원리를 모르면 `@Transactional`이 왜 내부 호출에서 안 먹히는지 이해하기 어렵다.

**오해 2: Around Advice에서 `proceed()`를 안 불러도 된다**
`proceed()`를 빠뜨리면 원래 메서드가 실행되지 않고 Advice만 실행된다. 항상 `return joinPoint.proceed()`를 반환해야 한다.

**오해 3: AOP는 어떤 메서드에도 다 적용된다**
Spring AOP는 **Spring Bean의 public 메서드**에만 적용된다. 같은 클래스 내부 메서드 호출(self-invocation)에는 프록시가 끼어들지 못한다. 이것이 `@Transactional` 내부 호출 함정과 동일한 원인이다.

## 실무에서 쓰는 모습

실행 시간을 측정하는 간단한 Aspect 예시:

```java
@Aspect
@Component
public class TimingAspect {

    @Around("execution(* com.example.service.*.*(..))")
    public Object measureTime(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed(); // 원래 메서드 실행
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(joinPoint.getSignature() + " took " + elapsed + "ms");
        return result;
    }
}
```

`@Aspect` + `@Component`를 붙이고, `@Around`에 Pointcut 표현식을 지정하면 된다.

## 더 깊이 가려면

- 프록시 생성 방식(JDK 동적 프록시 vs CGLIB), self-invocation 한계, `@EnableAspectJAutoProxy` 동작은 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)에서 이어서 본다.
- `@Transactional`이 AOP로 어떻게 구현되는지는 [Spring @Transactional 기초](./spring-transactional-basics.md)와 함께 보면 연결이 명확해진다.

## 면접/시니어 질문 미리보기

> Q: AOP의 횡단 관심사를 예로 들어 설명하면?
> 의도: AOP 필요성 이해 확인
> 핵심: 로깅, 트랜잭션, 보안 검사 등 여러 모듈에 동일하게 적용되는 기능이 횡단 관심사다.

> Q: Spring AOP에서 self-invocation이 문제가 되는 이유는?
> 의도: 프록시 동작 원리 이해 확인
> 핵심: Spring AOP는 외부 호출 시 프록시를 거치지만, 같은 빈 내부 메서드 호출은 프록시를 우회해 Advice가 적용되지 않는다.

> Q: Around Advice와 Before/After Advice의 차이는?
> 의도: Advice 종류 구분 확인
> 핵심: Around는 메서드 호출을 직접 제어할 수 있고 `proceed()`로 원래 메서드를 실행한다. Before/After는 실행 전/후 시점만 가로챈다.

## 한 줄 정리

AOP는 로깅·트랜잭션처럼 여러 곳에 반복되는 횡단 관심사를 Aspect로 분리해 비즈니스 로직과 섞이지 않게 하는 기법이고, Spring은 프록시를 통해 이를 투명하게 적용한다.
