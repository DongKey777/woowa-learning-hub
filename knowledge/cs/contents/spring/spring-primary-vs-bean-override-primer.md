---
schema_version: 3
title: 'Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다'
concept_id: spring/spring-primary-vs-bean-override-primer
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/lotto
- missions/shopping-cart
review_feedback_tags:
- primary-vs-override
- bean-candidate-vs-name-collision
aliases:
- '@primary vs bean override'
- primary default candidate
- bean override basics
- bean override toggle
- same type bean injection
- same name bean collision
- bean name collision vs bean candidate
- nouniquebeandefinitionexception vs beandefinitionoverrideexception
- 주입 단계 등록 단계 차이
- primary not bean override
- overriding disabled spring boot
- spring bean candidate selection beginner
- 빈 이름 충돌 구분
- primary qualifier ordering
symptoms:
- 같은 타입 bean이 여러 개인 문제와 같은 이름 bean 충돌을 같은 문제로 보고 있어요
- '@Primary를 붙이면 bean 이름 충돌도 같이 풀릴 거라고 생각해요'
- NoUniqueBeanDefinitionException과 BeanDefinitionOverrideException을 같은 축으로 읽고 있어요
intents:
- definition
prerequisites:
- spring/bean-di-basics
- spring/primary-qualifier-collection-injection
next_docs:
- spring/primary-qualifier-collection-injection
- spring/spring-custom-qualifier-primer
- spring/ioc-container-internals
linked_paths:
- contents/spring/spring-primary-qualifier-collection-injection-decision-guide.md
- contents/spring/spring-beandefinitionoverrideexception-quick-triage.md
- contents/spring/spring-allow-bean-definition-overriding-test-boundaries-primer.md
- contents/spring/spring-bean-definition-overriding-semantics.md
- contents/spring/spring-bean-naming-qualifier-rename-pitfalls-primer.md
- contents/spring/spring-conditionalonmissingbean-vs-primary-primer.md
- contents/spring/spring-di-exception-quick-triage.md
- contents/spring/spring-custom-qualifier-primer.md
- contents/spring/ioc-di-container.md
- contents/database/transaction-basics.md
confusable_with:
- spring/primary-conditionalonmissingbean-bean-override-decision-guide
- spring/spring-conditionalonmissingbean-vs-primary-primer
- spring/conditionalonsinglecandidate-vs-primary-primer
- spring/primary-qualifier-collection-injection
- spring/same-type-bean-injection-failure-cause-router
forbidden_neighbors:
- contents/spring/spring-same-type-bean-injection-failure-cause-router.md
- contents/spring/spring-same-name-bean-collision-cause-router.md
expected_queries:
- "'@Primary가 뭐예요?'"
- bean override가 뭐예요?
- "'@Primary는 언제 써요?'"
- bean override는 언제 켜요?
- 같은 타입 빈이 여러 개면 뭐가 주입돼요?
- primary랑 qualifier 중 뭐부터 봐야 해?
- 빈 이름 충돌이랑 같은 타입 후보 문제를 왜 따로 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Spring 초심자가 같은 타입 후보 여러 개 문제와 같은 bean
  이름 충돌 문제를 시간축으로 분리해 `@Primary`와 bean override를 처음
  잡는 primer다. 기본으로 꽂힐 대상을 정하기, 등록 단계에서 이름이
  부딪힘, 왜 앱 시작 전에 깨지지, 주입 규칙과 등록 규칙 차이, found 2와
  이름 충돌 메시지 구분 같은 자연어 paraphrase가 본 문서의 핵심 비교에
  매핑된다.
---
# Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다

> 한 줄 요약: `@Primary`는 이미 등록된 여러 후보 중 기본 주입 대상을 고르는 규칙이고, bean override는 같은 이름의 bean definition이 충돌할 때 등록 자체를 어떻게 처리할지의 문제다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 "같은 타입 후보가 여러 개"와 "같은 bean 이름이 겹침"을 초보자 눈높이로 먼저 분리해 주는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [BeanDefinitionOverrideException Quick Triage: 같은 이름 충돌인지, back-off인지, 후보 선택 문제인지 먼저 가르기](./spring-beandefinitionoverrideexception-quick-triage.md)
- [Spring `spring.main.allow-bean-definition-overriding` Boundaries Primer: 테스트에서는 언제 괜찮고, 운영 기본값으로는 왜 위험한가](./spring-allow-bean-definition-overriding-test-boundaries-primer.md)
- [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)
- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [트랜잭션 기초](../database/transaction-basics.md)

retrieval-anchor-keywords: @primary 뭐예요, bean override 뭐예요, @primary vs bean override, @primary 언제 써요, bean override 언제 켜요, 같은 타입 빈 여러 개 뭐가 주입돼요, 같은 이름 bean 이 겹치면 어떻게 돼요, bean name collision vs bean candidate, nouniquebeandefinitionexception vs beandefinitionoverrideexception, 주입 단계 등록 단계 차이, primary not bean override, overriding disabled spring boot, spring bean candidate selection beginner, 빈 이름 충돌 헷갈려요, primary qualifier 전에 뭐부터 봐요

## 이 문서가 먼저 잡는 질문

이 문서는 아래처럼 **`@Primary`와 bean override를 처음 같이 헷갈리는 질문**에서 primer로 먼저 걸리도록 조정했다.

| 학습자 질문 모양 | 이 문서에서 먼저 주는 답 |
|---|---|
| "`@Primary`가 뭐예요?" | 이미 등록된 후보 중 기본 주입 대상을 고르는 규칙이라고 먼저 자른다 |
| "bean override가 뭐예요?" | 같은 이름 bean definition 충돌을 등록 단계 문제로 먼저 자른다 |
| "`@Primary` 붙이면 충돌 해결돼요?" | 아니다. 이름 충돌은 주입 단계 전에 먼저 터질 수 있다고 답한다 |
| "같은 타입이 여러 개인 거랑 같은 이름 충돌이 왜 달라요?" | 타입 후보 선택과 이름 등록 충돌을 시간축으로 분리해 준다 |

## 먼저 mental model

Spring bean 문제는 초반에 아래 두 단계로 나누면 덜 헷갈린다.

```text
1. 등록 단계
   "이 이름으로 bean을 컨테이너에 올릴 수 있나?"
   -> 같은 이름이 겹치면 bean override / name collision 문제

2. 주입 단계
   "이미 등록된 후보 중 이 타입 파라미터에 무엇을 넣을까?"
   -> 같은 타입 후보가 여러 개면 @Primary / @Qualifier 문제
```

초보자용으로는 아래 두 줄만 먼저 잡으면 된다.

- bean override: **이 bean 이름을 등록할 수 있는가**
- `@Primary`: **등록된 후보 중 기본으로 무엇을 꽂을까**

즉, 둘 다 "bean 관련"이지만 보는 축이 다르다.

- override는 **이름 충돌**
- `@Primary`는 **타입 후보 선택**

---

## 한눈에 비교

| 구분 | `@Primary` | Bean override / name collision |
|---|---|---|
| 핵심 질문 | "같은 타입 후보가 여러 개면 기본으로 무엇을 주입할까?" | "같은 이름의 bean definition이 둘이면 등록을 허용할까?" |
| 보는 대상 | 타입이 맞는 후보 목록 | bean 이름과 definition 등록 |
| 동작 시점 | 의존성 주입 시점 | bean definition 등록 시점 |
| 흔한 증상 | `expected single matching bean but found 2` | `The bean 'x' could not be registered...` 같은 이름 충돌 메시지 |
| 먼저 떠올릴 해결책 | `@Primary`, `@Qualifier`, collection 주입 | 이름 분리, 조건부 등록, 의도된 교체 정책 확인 |
| 하지 않는 일 | bean 이름 충돌을 허용하지 않는다 | 여러 후보 중 기본 주입 대상을 고르지 않는다 |

가장 중요한 차이는 이것이다.

```text
이름 충돌이 해결되어야 bean이 등록되고,
bean이 등록되어야 @Primary로 후보 선택을 할 수 있다.
```

---

## 예제 1. 이름은 다르고 타입만 같다: `@Primary` 문제

아래처럼 `PaymentClient` 구현체가 둘 다 등록되어 있다고 가정한다.

```java
public interface PaymentClient {
    void pay();
}

@Configuration
public class PaymentConfig {

    @Bean
    public PaymentClient tossPaymentClient() {
        return new TossPaymentClient();
    }

    @Bean
    @Primary
    public PaymentClient kakaoPaymentClient() {
        return new KakaoPaymentClient();
    }
}
```

여기서는 bean 이름이 다르다.

- `tossPaymentClient`
- `kakaoPaymentClient`

즉 등록 단계에서는 충돌이 없다.
문제는 주입 단계다.

```java
@Service
public class CheckoutService {

    public CheckoutService(PaymentClient paymentClient) {
    }
}
```

`CheckoutService`는 `PaymentClient` 하나만 원하므로 Spring이 둘 중 하나를 골라야 한다.
그래서 `@Primary`가 붙은 `kakaoPaymentClient`가 기본 후보가 된다.

이 상황은 **override 문제가 아니라 후보 선택 문제**다.

---

## 예제 2. 이름이 같다: bean override / name collision 문제

이번에는 bean 이름이 같은 경우를 보자.

```java
@Configuration
public class PaymentConfigA {

    @Bean("paymentClient")
    public PaymentClient tossPaymentClient() {
        return new TossPaymentClient();
    }
}

@Configuration
public class PaymentConfigB {

    @Bean("paymentClient")
    @Primary
    public PaymentClient kakaoPaymentClient() {
        return new KakaoPaymentClient();
    }
}
```

여기서는 둘 다 bean 이름이 `paymentClient`다.
이 경우 Spring은 먼저 "이 이름으로 bean을 두 번 등록해도 되는가?"를 판단해야 한다.

초보자 기준 핵심은 아래다.

- 이 시점의 핵심 문제는 `@Primary`가 아니다
- 먼저 **같은 이름 충돌**이 발생한다
- override가 허용되지 않으면 애플리케이션이 시작 단계에서 실패할 수 있다

즉 `@Primary`를 붙였다고 해서 이름 충돌이 해결되지는 않는다.
충돌이 나면 주입 단계까지 가지 못할 수 있기 때문이다.

---

## 가장 자주 섞이는 두 상황

| 실제 상황 | 무엇이 다른가 | 먼저 생각할 도구 |
|---|---|---|
| 같은 타입 bean이 여러 개, 이름은 각각 다름 | 후보가 많아서 하나를 못 고른다 | `@Primary`, `@Qualifier`, `List<T>` |
| 같은 bean 이름이 두 번 등록됨 | 후보 선택 전부터 등록 충돌이 난다 | 이름 변경, alias 대신 명시 이름 정리, 조건부 등록 |

여기서 `alias`도 같이 조심하면 좋다.

- alias는 **같은 bean에 여러 이름을 붙이는 것**이다
- override는 **서로 다른 definition이 같은 이름을 차지하려는 것**이다

비슷해 보여도 완전히 다른 문제다. alias를 만들었다고 override가 된 것이 아니다.

---

## 자주 나오는 오해

### 1. `@Primary`를 붙이면 이름 충돌도 이긴다고 생각한다

아니다. `@Primary`는 주입 우선순위일 뿐이다.
bean 이름 충돌은 등록 단계 문제라서 `@Primary`보다 먼저 터질 수 있다.

### 2. override를 허용하면 `@Primary`와 비슷하다고 생각한다

아니다. override가 일어나면 보통 "어느 definition이 남느냐"의 문제다.
`@Primary`처럼 "둘 다 등록된 상태에서 기본 후보를 고른다"와는 다르다.

### 3. 같은 타입 bean 2개와 같은 이름 bean 2개를 같은 오류로 본다

둘은 출발점이 다르다.

- 같은 타입 bean 2개 -> 주입 후보 선택
- 같은 이름 bean 2개 -> 등록 충돌

로그와 예외도 다르게 읽어야 한다.

### 4. Boot 기본 bean이 안 보이면 무조건 override 문제라고 생각한다

이 경우는 override보다 [`@ConditionalOnMissingBean` back-off](./spring-conditionalonmissingbean-vs-primary-primer.md)일 수도 있다.
"이름이 겹쳤는가", "같은 타입 기존 bean이 있어서 기본 bean이 물러났는가"를 분리해서 본다.

---

## 증상으로 빠르게 분기하기

| 보이는 증상 | 먼저 볼 축 | 보통 다음 액션 |
|---|---|---|
| `NoUniqueBeanDefinitionException` | 후보 선택 | `@Primary`, `@Qualifier`, collection 주입 중 요구사항에 맞게 고른다 |
| `The bean 'x' could not be registered` | 이름 충돌 / override 정책 | bean 이름이 왜 겹쳤는지 찾고, 정말 교체 의도인지 확인한다 |
| "`@Primary`를 붙였는데도 Boot 기본 bean이 안 뜬다" | auto-configuration back-off | `@ConditionalOnMissingBean` miss인지 conditions report로 본다 |

이 표만 기억해도 "무엇부터 고쳐야 하는가"가 훨씬 빨라진다.

startup 로그에서 `BeanDefinitionOverrideException`, `overriding is disabled`, `existing bean`, `found 2`가 섞여 보여 30초 안에 분기가 안 되면 [BeanDefinitionOverrideException Quick Triage: 같은 이름 충돌인지, back-off인지, 후보 선택 문제인지 먼저 가르기](./spring-beandefinitionoverrideexception-quick-triage.md)부터 열어 증상 기준으로 가르는 편이 빠르다.

---

## 초보자 기준 정리

문제가 생겼을 때는 먼저 아래 질문을 순서대로 던진다.

1. bean 이름이 겹친 것인가?
2. 아니면 이름은 다른데 같은 타입 후보가 여러 개인가?
3. Boot가 기본 bean 생성을 물러난 것인가?

이 순서로 나누면 대응도 자연스럽게 갈린다.

- 이름 충돌이면 bean 이름과 등록 정책을 본다
- 타입 후보 중복이면 `@Primary`/`@Qualifier`를 본다
- Boot 기본값이 사라졌으면 `@ConditionalOnMissingBean`을 본다

---

## 이 문서 다음에 보면 좋은 문서

- "`@Primary`와 `@Qualifier` 중 무엇을 써야 하지?"가 다음 질문이면 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)로 이어진다.
- startup 오류 메시지 한 줄만 들고 빠르게 갈라 타고 싶다면 [BeanDefinitionOverrideException Quick Triage: 같은 이름 충돌인지, back-off인지, 후보 선택 문제인지 먼저 가르기](./spring-beandefinitionoverrideexception-quick-triage.md)로 먼저 간다.
- 이름 충돌과 override 정책을 더 정확하게 보고 싶다면 [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)로 이어진다.
- bean 이름이 어디서 오고 rename 때 왜 깨지는지 보고 싶다면 [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)로 이어진다.
- Boot 기본 bean이 왜 안 뜨는지가 섞이면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)로 이어진다.

## 꼬리질문

> Q: `@Primary`와 bean override를 한 줄로 나누면?
> 의도: 후보 선택과 등록 충돌을 분리하는지 확인
> 핵심: `@Primary`는 등록된 후보 중 기본 주입 대상을 고르고, bean override는 같은 이름 definition 충돌을 어떻게 처리할지의 문제다.

> Q: `@Primary`를 붙였는데 왜 "bean could not be registered"가 날 수 있는가?
> 의도: 등록 단계와 주입 단계를 구분하는지 확인
> 핵심: 이름 충돌이 등록 단계에서 먼저 터지기 때문이다. `@Primary`는 그 이후의 주입 규칙이다.

> Q: override를 허용하면 `@Primary`와 같은 효과인가?
> 의도: replacement와 preference를 구분하는지 확인
> 핵심: 아니다. override는 definition 교체 정책이고, `@Primary`는 여러 후보가 함께 등록된 상태에서의 기본 선택 규칙이다.

## 한 줄 정리

`@Primary`는 "등록된 여러 후보 중 기본 하나", bean override는 "같은 이름 등록 충돌을 어떻게 처리할까"다. 이름 충돌과 후보 선택을 따로 보면 Spring bean 문제를 훨씬 덜 섞어 보게 된다.
