# Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`

> 한 줄 요약: `NoSuchBeanDefinitionException`는 "조건에 맞는 bean 후보가 0개", `NoUniqueBeanDefinitionException`는 "후보는 있지만 2개 이상이라 하나로 못 고름"이다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 DI startup 오류를 scan 누락, `@Profile`/conditional 탈락, 후보 중복으로 먼저 가르는 **beginner troubleshooting note**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [추상 클래스 vs 인터페이스와 DI 브리지: 상속 선택과 주입 선택을 섞지 않기](../design-pattern/abstract-class-vs-interface-injection-bridge.md)

retrieval-anchor-keywords: spring di exception quick triage, spring di exception 뭐예요, nosuchbeandefinitionexception vs nouniquebeandefinitionexception, expected single matching bean but found 2, expected at least 1 bean which qualifies as autowire candidate, no qualifying bean of type available, found 2 selection rule problem, nouniquebeandefinitionexception log one line, primary qualifier collection checklist, rename qualifier string problem, 처음 배우는데 spring di 예외, bean not found vs bean duplication, scan miss vs profile mismatch, primary qualifier collection guide, spring di exception quick triage basics

## rename 의심이면 여기서 바로 갈라 타기

이 문서는 먼저 `0개냐`, `2개 이상이냐`를 가르는 입구다.
그런데 초보자는 rename 직후 `NoSuchBeanDefinitionException`가 뜨면 scan 문제와 이름 계약 문제를 자주 섞어 본다.

아래 두 줄만 먼저 기억하면 된다.

- 클래스명, `@Bean` 메서드명, `@Qualifier("...")` 문자열을 방금 바꿨다면 -> [Spring Bean 이름 규칙과 rename 함정 입문](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)으로 먼저 간다.
- rename은 안 했고 package, annotation, profile, starter 설정을 건드렸다면 -> 이 문서 표대로 scan/조건/후보 중복을 먼저 가른다.

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
| `NoSuchBeanDefinitionException` + rename 직후 | bean이 아예 없는지보다 **이름 계약이 끊겼을 수 있다** | 클래스명, `@Bean` 메서드명, `@Qualifier("oldName")` 문자열 | [Spring Bean 이름 규칙과 rename 함정 입문](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)으로 먼저 간다 |
| `NoSuchBeanDefinitionException` | 조건에 맞는 후보가 0개다 | scan 범위, stereotype annotation, `@Bean`, profile/condition, qualifier mismatch | Bean이 왜 등록되지 않았는지부터 본다 |
| `NoUniqueBeanDefinitionException` | 타입은 맞는데 후보가 2개 이상이다 | 구현체 개수, 같은 반환 타입 `@Bean`, `@Primary`, `@Qualifier` | "기본 후보를 둘지, 명시적으로 찍을지"를 정한다 |
| `expected single matching bean but found 2` | 거의 항상 후보 중복이다 | 후보 목록 이름 | `@Primary`, `@Qualifier`, collection 주입 중 맞는 전략을 고른다 |
| `expected at least 1 bean which qualifies as autowire candidate` | 거의 항상 후보 0개다 | 등록 누락 or 조건 불일치 | component scan / explicit registration부터 본다 |

실전에서는 표 전체보다 아래 한 줄이 더 중요하다.

```text
0개면 등록/scan 문제, 2개 이상이면 선택/우선순위 문제
```

---

<a id="missing-bean-path"></a>

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
4. package와 annotation이 멀쩡한데 특정 profile/test/CI에서만 깨지면 `@Profile`/`@Conditional...`을 본다
5. `@Qualifier`를 썼다면 이름/역할이 실제 bean과 맞는지 본다

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

## 1-1. scan 누락 vs `@Profile`/conditional 탈락 30초 분기

`NoSuchBeanDefinitionException`를 봤다고 해서 바로 component scan만 의심하면 반만 맞는다.
아래 표처럼 **package/annotation 문제인지, 실행 조건 문제인지**를 먼저 나누면 훨씬 빠르다.

| 먼저 보는 단서 | scan 누락 쪽 신호 | `@Profile`/conditional 탈락 쪽 신호 |
|---|---|---|
| package와 annotation | `Application` root 바깥, stereotype 누락, `@Bean` 등록 누락 | package와 annotation은 멀쩡하다 |
| 재현 범위 | 로컬/테스트/CI 어디서나 계속 깨진다 | 특정 profile, 테스트, CI, 운영에서만 깨진다 |
| 코드에 보이는 힌트 | `@SpringBootApplication`, `scanBasePackages`, package 구조가 수상하다 | `@Profile`, `@ConditionalOnProperty`, `@ConditionalOnClass`, `@ConditionalOnBean`이 붙어 있다 |
| 먼저 열 문서 | [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md) | [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md), [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ](./spring-starter-added-but-bean-missing-faq.md) |

예를 들어 아래 코드는 scan 범위 안에 있어도 profile이 안 맞으면 bean이 안 뜬다.

```java
package com.example.payment;

@Service
@Profile("prod")
public class PaymentGatewayClient {
}
```

`Application`이 `com.example` 아래에 있고 `@Service`도 붙어 있어도, active profile이 `local`이면 이 bean은 후보 0개다.
즉 이 경우는 scan 실패가 아니라 **profile 탈락**이다.

---

## 1-2. property/classpath 조건이면 scan보다 실행 조건을 먼저 본다

아래처럼 property 조건으로 빠지는 경우도 같다.

```java
@Configuration
public class SmsConfig {

    @Bean
    @ConditionalOnProperty(name = "app.sms.enabled", havingValue = "true")
    public SmsSender smsSender() {
        return new SmsSender();
    }
}
```

`app.sms.enabled=true`가 없으면 `SmsSender`는 등록되지 않는다.
이때 beginner 질문은 "`왜 scan을 못 했지?`"가 아니라 **"`지금 profile/property/classpath가 이 bean을 켜고 있나?`"**여야 한다.

조건 탈락 쪽 힌트는 네 개만 먼저 보면 충분하다.

- package 위치와 stereotype annotation이 이미 맞다
- 로컬에서는 되는데 test/CI/prod 같은 특정 환경에서만 깨진다
- bean 클래스나 설정 클래스에 `@Profile`, `@Conditional...`이 직접 붙어 있다
- starter bean 문제라서 `--debug`나 Actuator `conditions`로 negative match를 바로 볼 수 있다

---

<a id="ambiguous-bean-path"></a>

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
| `No qualifying bean of type ... available` | 조건에 맞는 후보가 없다 | [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md), [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md) |
| `expected single matching bean but found 2` | 후보가 둘 이상이라 애매하다 | [Spring Bean과 DI 기초](./spring-bean-di-basics.md), [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md), [Spring 커스텀 `@Qualifier` 입문](./spring-custom-qualifier-primer.md) |
| `UnsatisfiedDependencyException` 바깥 예외만 보인다 | wrapper일 수 있다 | 안쪽 root cause를 끝까지 읽는다 |

특히 아래 메시지는 자주 착시를 만든다.

```text
No qualifying bean of type '...PaymentClient' available: expected single matching bean but found 2: tossPaymentClient,kakaoPaymentClient
```

앞부분만 보면 "bean이 없다"처럼 읽히지만, 진짜 핵심은 뒤의 `found 2`다.
이 경우는 missing bean이 아니라 ambiguous bean이다.

초보자 기준으로는 아래 두 문장으로 먼저 갈라 타면 된다.

- `found 2`, `found 3`가 보이면 -> **선택 규칙 문제**로 보고 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)로 간다.
- rename 뒤 `@Qualifier("oldName")` 같은 문자열이 흔들리면 -> **문자열 이름 계약 문제**로 보고 [Spring Bean 이름 규칙과 rename 함정 입문](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)으로 간다.

---

## 3-0. `NoUniqueBeanDefinitionException` 로그 한 줄 미니 체크리스트

실전에서는 긴 stack trace를 다 읽기 전에 아래 한 줄부터 본다.

```text
No qualifying bean of type '...PaymentClient' available: expected single matching bean but found 2: tossPaymentClient,kakaoPaymentClient
```

이 한 줄은 아래처럼 끊어 읽으면 된다.

| 로그 조각 | 뜻 | 바로 고를 분기 |
|---|---|---|
| `PaymentClient` | 지금 충돌한 기준 타입 | 어떤 인터페이스/부모 타입 후보가 여러 개인지 본다 |
| `found 2` | 후보 0개가 아니라 2개 이상 | 등록 문제가 아니라 선택 규칙 문제로 본다 |
| `tossPaymentClient,kakaoPaymentClient` | Spring이 본 실제 후보 목록 | 기본값 하나가 필요한지, 특정 후보를 찍어야 하는지, 둘 다 필요한지 정한다 |

이제 분기는 세 갈래면 충분하다.

1. "대부분 한 구현체를 기본값으로 쓰면 된다" -> `@Primary`
2. "이 주입 지점만 특정 구현체여야 한다" -> `@Qualifier`
3. "둘 다 받아서 직접 고르거나 순회해야 한다" -> `List<T>`/`Map<String, T>`

즉 `found 2` 로그를 보면 먼저 "왜 bean이 없지?"가 아니라 **"하나를 기본으로 둘까, 이번만 찍을까, 아예 다 받을까?"**를 묻는 편이 빠르다.

## 3-1. `found 2`와 rename 문자열 문제를 따로 본다

`found 2`를 봤다면 beginner quick path는 세 줄이면 충분하다.

1. 먼저 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)에서 "기본 후보/명시 선택/다중 수집" 중 무엇이 맞는지 정한다.
2. 문자열 이름 기반 `@Qualifier`가 자주 흔들리면 [Spring 커스텀 `@Qualifier` 입문](./spring-custom-qualifier-primer.md)으로 역할 기반 선택으로 고정한다.
3. 이름 바꾸기(rename)로 우회하기보다, 주입 지점의 선택 규칙을 코드에 명시해 재발을 막는다.

## 3-2. 30초 로그 판독 예시: `found 2` vs `expected at least 1 bean`

실전에서는 아래 두 로그를 거의 반사적으로 갈라 읽으면 된다.

```text
org.springframework.beans.factory.NoUniqueBeanDefinitionException: No qualifying bean of type 'com.example.pay.PaymentClient' available: expected single matching bean but found 2: tossPaymentClient,kakaoPaymentClient
```

| 로그에서 바로 집을 조각 | 초급자 해석 | 첫 행동 |
|---|---|---|
| `found 2` | 후보가 없다는 뜻이 아니라 둘 다 보여서 못 고른다 | `@Primary`, `@Qualifier`, `List<T>` 중 무엇이 요구사항에 맞는지 고른다 |
| `tossPaymentClient,kakaoPaymentClient` | Spring이 실제로 본 후보 이름 목록이다 | 둘 중 기본값 1개가 필요한지, 둘 다 필요한지 결정한다 |

```text
org.springframework.beans.factory.NoSuchBeanDefinitionException: No qualifying bean of type 'com.example.pay.PaymentClient' available: expected at least 1 bean which qualifies as autowire candidate. Dependency annotations: {}
```

| 로그에서 바로 집을 조각 | 초급자 해석 | 첫 행동 |
|---|---|---|
| `expected at least 1 bean` | 최소 1개는 있어야 하는데 지금은 0개다 | package 경계, stereotype annotation, `@Bean` 등록 누락부터 본다 |
| `qualifies as autowire candidate` | 아무 bean이나 1개가 아니라 주입 조건에 맞는 후보가 없다는 뜻이다 | `@Profile`, `@Conditional...`, `@Qualifier` mismatch까지 이어서 본다 |

두 로그 모두 앞부분에 `No qualifying bean`이 있어 비슷해 보이지만, 초급자 기준 핵심은 딱 두 단어다.

- `found 2`면: 선택 문제
- `expected at least 1 bean`이면: 등록 또는 조건 문제

---

## 4. 초급자용 빠른 결정 트리

```text
1. root cause가 무엇인지 본다
2. 메시지에 found 2 / found 3 이 보이면 -> 후보 중복 경로
3. 그런 숫자 없이 no qualifying bean / expected at least 1 bean 이면 -> 후보 0개 경로
4. 후보 0개 경로면 -> package 경계, annotation, `@Bean` 등록부터 확인
5. package와 annotation이 멀쩡한데 환경별로 다르면 -> `@Profile`/`@Conditional...` 경로 확인
6. 그래도 아니면 -> `@Qualifier` mismatch 확인
7. 후보 중복 경로면 -> `@Primary`, `@Qualifier`, collection 주입 중 맞는 해법 선택
```

beginner 기준으로는 이 결정 트리만 따라도 "component scan 문서를 봐야 하는지, qualifier 문서를 봐야 하는지"가 빨리 갈린다.

---

## 자주 하는 오해

먼저 "용어 설명"보다 아래 체크를 그대로 따라가면 beginner가 덜 헷갈린다.

| 자주 하는 오해 | 이렇게 행동으로 확인 |
|---|---|
| "`NoSuchBeanDefinitionException`이면 무조건 component scan 문제다" | package 경계와 stereotype annotation을 먼저 보되, 둘 다 멀쩡하면 바로 `@Profile`, `@ConditionalOnProperty`, `@ConditionalOnClass`를 확인한다. 환경별로만 깨지면 scan보다 조건 탈락 쪽을 먼저 의심한다. |
| "`NoUniqueBeanDefinitionException`이면 bean 하나를 지워야 한다" | 후보를 지우기 전에 "정말 하나만 필요했나?"를 먼저 묻는다. 기본값 1개면 `@Primary`, 특정 1개면 `@Qualifier`, 여러 개가 다 필요하면 `List<T>`/`Map<String, T>`로 바꾼다. |
| "`UnsatisfiedDependencyException`만 봐도 충분하다" | wrapper 예외에서 멈추지 말고 root cause까지 내려간다. 메시지 끝에 `found 2`, `found 3`이 있으면 선택 문제, `expected at least 1 bean`이면 등록/조건 문제로 다시 분기한다. |

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

> Q: package와 annotation이 맞는데 테스트에서만 bean이 없으면 무엇을 먼저 봐야 하는가?
> 의도: scan miss와 조건 탈락 분기 확인
> 핵심: active profile, `@Profile`, `@ConditionalOnProperty` 같은 실행 조건이다.

> Q: 같은 타입 구현체가 둘인데 둘 다 필요하면 어떻게 해야 하는가?
> 의도: 후보 제거 대신 collection 주입 감각 확인
> 핵심: `List<T>`나 `Map<String, T>`로 여러 후보를 받는 편이 더 맞을 수 있다.

---

## 한 줄 정리

`NoSuchBeanDefinitionException`는 "못 찾음", `NoUniqueBeanDefinitionException`는 "못 고름"으로 먼저 나누면 DI 디버깅 초반 속도가 확 올라간다.
