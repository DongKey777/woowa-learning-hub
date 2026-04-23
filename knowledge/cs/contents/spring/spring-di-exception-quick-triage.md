# Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`

> 한 줄 요약: `NoSuchBeanDefinitionException`는 "조건에 맞는 bean 후보가 0개", `NoUniqueBeanDefinitionException`는 "후보는 있지만 2개 이상이라 하나로 못 고름"이다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 DI startup 오류를 scan 누락과 후보 중복으로 먼저 가르는 **beginner troubleshooting note**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
> - [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
> - [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
> - [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
> - [Spring Startup / Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)

retrieval-anchor-keywords: spring di exception quick triage, NoSuchBeanDefinitionException vs NoUniqueBeanDefinitionException, missing bean vs ambiguous bean, bean not found vs bean duplication, scan miss vs duplicate candidate, component scan omission, qualifier mismatch, @Primary @Qualifier beginner, @Primary vs @Qualifier vs collection injection, expected single matching bean but found 2, no qualifying bean of type available

## 핵심 개념

초보자 기준으로는 아래 두 줄만 먼저 잡으면 된다.

- `NoSuchBeanDefinitionException`: **주입하려는 조건에 맞는 bean이 0개**
- `NoUniqueBeanDefinitionException`: **타입은 맞는 bean이 여러 개라 하나를 못 고름**

즉 DI 예외를 볼 때 첫 질문은 "없어서 실패했나, 많아서 실패했나"다.

여기서 beginner가 자주 헷갈리는 포인트가 하나 더 있다.

- `NoUniqueBeanDefinitionException`는 Spring 타입 계층상 `NoSuchBeanDefinitionException`의 하위 예외다
- 그래서 로그 일부만 보면 둘 다 비슷하게 "No qualifying bean"처럼 보일 수 있다
- **반드시 예외 클래스 이름과 메시지 끝부분의 `found 2`, `found 3` 같은 표현까지 같이 본다**

---

## 예외 이름만 보고 5초 분기

| 보인 예외/문구 | 실제 뜻 | 먼저 볼 것 | beginner용 첫 대응 |
|---|---|---|---|
| `NoSuchBeanDefinitionException` | 조건에 맞는 후보가 0개다 | scan 범위, stereotype annotation, `@Bean`, profile/condition, qualifier mismatch | Bean이 왜 등록되지 않았는지부터 본다 |
| `NoUniqueBeanDefinitionException` | 타입은 맞는데 후보가 2개 이상이다 | 구현체 개수, 같은 반환 타입 `@Bean`, `@Primary`, `@Qualifier` | "기본 후보를 둘지, 명시적으로 찍을지"를 정한다 |
| `expected single matching bean but found 2` | 거의 항상 후보 중복이다 | 후보 목록 이름 | `@Primary`, `@Qualifier`, collection 주입 중 맞는 전략을 고른다 |
| `expected at least 1 bean which qualifies as autowire candidate` | 거의 항상 후보 0개다 | 등록 누락 or 조건 불일치 | component scan / explicit registration부터 본다 |

실전에서는 표 전체보다 아래 한 줄이 더 중요하다.

```text
0개면 등록/scan 문제, 2개 이상이면 선택/우선순위 문제
```

---

## 1. `NoSuchBeanDefinitionException`를 보면 먼저 scan/등록 누락부터 본다

대표 상황은 아래다.

1. `@SpringBootApplication` package 바깥이라 component scan에서 빠졌다
2. `@Service`, `@Repository`, `@Component` 같은 stereotype annotation이 없다
3. 외부 클래스인데 `@Bean`으로 등록하지 않았다
4. `@Qualifier`를 붙였는데 그 이름이나 역할에 맞는 bean이 없다
5. profile/conditional 설정 때문에 현재 실행 조건에서 bean이 안 떴다

beginner의 빠른 확인 순서는 이렇다.

1. 주입하려는 concrete class가 진짜 Spring Bean인지 본다
2. `Application` package 하위인지 본다
3. stereotype annotation 또는 `@Bean` 등록이 있는지 본다
4. `@Qualifier`를 썼다면 이름/역할이 실제 bean과 맞는지 본다

가장 흔한 예시는 component scan 누락이다.

```java
package com.example.order;

@Service
public class OrderService {
}
```

```java
package com.example.bootstrap.app;

@SpringBootApplication
public class Application {
}
```

이 경우 `OrderService`는 `Application`의 sibling package에 있어서 기본 scan에 안 잡힐 수 있다.

즉 `NoSuchBeanDefinitionException`에서 beginner가 제일 먼저 의심할 것은 "Spring이 못 찾았다"가 아니라, **내가 scan/등록 규칙 바깥에 둔 것은 아닌가**다.

---

## 2. `NoUniqueBeanDefinitionException`를 보면 후보 중복부터 본다

대표 상황은 아래다.

1. 같은 인터페이스 구현체가 둘 이상 있다
2. 같은 타입을 반환하는 `@Bean` 메서드가 여러 개 있다
3. `@Primary`도 없고 `@Qualifier`도 없는데 단일 타입 주입을 시도했다

예를 들어:

```java
public interface PaymentClient {
    void pay();
}

@Component
public class TossPaymentClient implements PaymentClient {
}

@Component
public class KakaoPaymentClient implements PaymentClient {
}

@Service
public class CheckoutService {
    public CheckoutService(PaymentClient paymentClient) {
    }
}
```

`PaymentClient` 후보는 둘인데 주입 지점은 하나를 원하므로 Spring은 자동으로 못 고른다.

이때 선택지는 세 갈래다.

1. 보통 기본값 하나가 있으면 `@Primary`
2. 이번 주입에서 특정 후보를 찍어야 하면 `@Qualifier`
3. 원래 여러 개를 다 받아야 하는 문제면 `List<PaymentClient>`나 `Map<String, PaymentClient>`

즉 `NoUniqueBeanDefinitionException`는 "bean 등록이 실패했다"보다, **등록은 됐는데 단일 선택 규칙이 없다**에 가깝다.

---

## 3. 예외 메시지 읽는 법

초보자에게는 예외 클래스보다 메시지 패턴이 더 빨리 눈에 들어온다.

| 메시지 패턴 | 해석 | 바로 가야 할 문서 |
|---|---|---|
| `No qualifying bean of type ... available` | 조건에 맞는 후보가 없다 | [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md) |
| `expected single matching bean but found 2` | 후보가 둘 이상이라 애매하다 | [Spring Bean과 DI 기초](./spring-bean-di-basics.md), [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md), [Spring 커스텀 `@Qualifier` 입문](./spring-custom-qualifier-primer.md) |
| `UnsatisfiedDependencyException` 바깥 예외만 보인다 | wrapper일 수 있다 | 안쪽 root cause를 끝까지 읽는다 |

특히 아래 메시지는 자주 착시를 만든다.

```text
No qualifying bean of type '...PaymentClient' available: expected single matching bean but found 2: tossPaymentClient,kakaoPaymentClient
```

앞부분만 보면 "bean이 없다"처럼 읽히지만, 진짜 핵심은 뒤의 `found 2`다.  
이 경우는 missing bean이 아니라 ambiguous bean이다.

---

## 4. 초급자용 빠른 결정 트리

```text
1. root cause가 무엇인지 본다
2. 메시지에 found 2 / found 3 이 보이면 -> 후보 중복 경로
3. 그런 숫자 없이 no qualifying bean / expected at least 1 bean 이면 -> 후보 0개 경로
4. 후보 0개 경로면 -> scan 범위, annotation, @Bean, qualifier mismatch 확인
5. 후보 중복 경로면 -> @Primary, @Qualifier, collection 주입 중 맞는 해법 선택
```

beginner 기준으로는 이 결정 트리만 따라도 "component scan 문서를 봐야 하는지, qualifier 문서를 봐야 하는지"가 빨리 갈린다.

---

## 자주 하는 오해

### 1. `NoSuchBeanDefinitionException`이면 무조건 component scan 문제다

그렇지 않다. beginner quick path는 scan부터 보는 것이 맞지만, qualifier mismatch나 profile mismatch도 후보 0개로 보일 수 있다.

### 2. `NoUniqueBeanDefinitionException`이면 bean 하나를 지워야 한다

항상 그렇지는 않다. 애초에 여러 구현체가 필요한 설계일 수 있다.  
그 경우에는 `@Primary`, `@Qualifier`, collection 주입처럼 **선택 규칙을 추가**하는 쪽이 맞다.

### 3. 예외를 `UnsatisfiedDependencyException`까지만 읽어도 된다

아니다. 그건 wrapper인 경우가 많다.  
항상 안쪽 cause가 `NoSuchBeanDefinitionException`인지, `NoUniqueBeanDefinitionException`인지 확인해야 한다.

---

## 꼬리질문

> Q: `NoSuchBeanDefinitionException`와 `NoUniqueBeanDefinitionException`를 한 줄로 구분하면?
> 의도: 후보 0개 vs 후보 2개 이상 구분 확인
> 핵심: 전자는 등록/조건 누락, 후자는 선택 규칙 부재다.

> Q: `NoUniqueBeanDefinitionException`에서도 `No qualifying bean` 문구가 보일 수 있는 이유는 무엇인가?
> 의도: 메시지 패턴 착시 확인
> 핵심: 이 예외가 `NoSuchBeanDefinitionException` 계층 아래라서 앞부분만 보면 비슷하게 보일 수 있다.

> Q: `NoSuchBeanDefinitionException`를 봤을 때 beginner가 제일 먼저 확인할 것은 무엇인가?
> 의도: scan 누락 기본 루트 확인
> 핵심: `Application` package 경계, stereotype annotation, `@Bean` 등록이다.

> Q: 같은 타입 구현체가 둘인데 둘 다 필요하면 어떻게 해야 하는가?
> 의도: 후보 제거 대신 collection 주입 감각 확인
> 핵심: `List<T>`나 `Map<String, T>`로 여러 후보를 받는 편이 더 맞을 수 있다.

---

## 한 줄 정리

`NoSuchBeanDefinitionException`는 "못 찾음", `NoUniqueBeanDefinitionException`는 "못 고름"으로 먼저 나누면 DI 디버깅 초반 속도가 확 올라간다.
