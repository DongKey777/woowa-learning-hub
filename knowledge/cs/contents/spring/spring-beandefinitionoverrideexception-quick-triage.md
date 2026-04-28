# BeanDefinitionOverrideException Quick Triage: 같은 이름 충돌인지, back-off인지, 후보 선택 문제인지 먼저 가르기

> 한 줄 요약: startup 로그에 override 비슷한 말이 보여도, 실제 원인은 `같은 bean 이름 충돌`, `auto-configuration back-off`, `여러 후보 중 하나를 못 고름` 셋 중 하나인 경우가 많다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `The bean 'x' could not be registered`, `overriding is disabled`, `existing bean`, `found 2`처럼 초보자가 한 덩어리로 오해하기 쉬운 startup 메시지를 `이름 충돌`, `back-off`, `후보 선택 실패`로 먼저 갈라 주는 **beginner startup triage note**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다](./spring-primary-vs-bean-override-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring DI 예외 빠른 판별: bean을 못 찾음 vs 여러 개라 못 고름](./spring-di-exception-quick-triage.md)
- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [트랜잭션 기초](../database/transaction-basics.md)
- [카테고리 README](./README.md)

retrieval-anchor-keywords: beandefinitionoverrideexception quick triage, bean override startup error, the bean could not be registered, bean name collision beginner, overriding is disabled spring boot, conditionalonmissingbean did not match, existing bean found startup, expected single matching bean but found 2, bean override vs primary, bean override vs back off, duplicate bean name fix, spring startup bean conflict, 처음 배우는데 bean override 에러, bean 이름 충돌 뭐예요, startup bean error primer

## 핵심 개념

먼저 이것만 잡으면 된다.

- `BeanDefinitionOverrideException`은 보통 **같은 이름으로 bean을 두 번 등록하려고 했다**는 신호다
- 하지만 startup 로그에 `override`, `existing bean`, `found 2`가 같이 보인다고 해서 전부 같은 문제는 아니다
- 초반 분기는 "등록 충돌", "등록 back-off", "주입 후보 선택" 세 갈래면 충분하다

짧게 번역하면 이렇다.

- name collision: 같은 이름 자리를 두 bean이 같이 차지하려 한다
- back-off: 기존 bean이 있어서 Boot 기본 bean이 아예 안 만들어진다
- candidate selection: bean은 둘 다 등록됐는데 하나를 못 고른다

## 한눈에 보기

| 로그 신호 | 실제 질문 | 보통 첫 해결 방향 |
|---|---|---|
| `The bean 'x' could not be registered` | 같은 이름의 bean definition이 충돌했나? | bean 이름 분리, 중복 등록 경로 정리 |
| `overriding is disabled` | 같은 이름 충돌을 Boot가 막았나? | `allow-bean-definition-overriding`을 켜기 전에 충돌 의도부터 확인 |
| `@ConditionalOnMissingBean did not match`, `existing bean` | 이미 bean이 있어서 기본 bean이 물러났나? | 누가 먼저 bean을 만들었는지 찾고 back-off로 읽기 |
| `expected single matching bean but found 2` | 후보가 둘 이상이라 하나를 못 고르나? | `@Primary`, `@Qualifier`, collection 주입으로 분기 |

핵심 순서는 아래다.

```text
1. 이름 충돌인가?
2. 아니면 Boot 기본 bean이 물러난 것인가?
3. 아니면 둘 다 등록됐는데 주입에서 하나를 못 고르는가?
```

## 메시지 한 줄로 바로 고칠 축 찾기

| 로그/문구 조각 | 이 문서에서 읽는 뜻 | 첫 fix 후보 |
|---|---|---|
| `BeanDefinitionOverrideException` | 같은 이름 등록 충돌 | 같은 이름을 만든 선언 두 군데 찾기 |
| `The bean 'x' could not be registered` | 거의 항상 name collision 분기 | `@Bean` 이름, component scan 이름, rename 잔여 문자열 정리 |
| `overriding is disabled` | 충돌은 있었고 Boot가 막음 | 설정을 켜기 전에 충돌이 의도인지 확인 |
| `@ConditionalOnMissingBean did not match` | override가 아니라 back-off | 기존 bean 출처와 condition report 확인 |
| `existing bean` | 기본 bean이 물러났을 가능성 큼 | 누가 먼저 등록됐는지 찾기 |
| `expected single matching bean but found 2` | 후보 선택 실패 | `@Primary`, `@Qualifier`, collection 주입 중 하나 선택 |

초보자 기준으로는 예외 클래스 전체를 외우기보다, 로그에 보이는 짧은 문구를 위 표에 바로 대입하는 편이 빠르다.

<a id="symptom-name-collision"></a>

## `The bean 'x' could not be registered`가 보이면

이 메시지는 초보자 기준으로 거의 항상 **이름 충돌**부터 의심하면 된다.

자주 나오는 원인은 아래다.

- `@Bean` 메서드명이 같다
- `@Bean("paymentClient")`처럼 명시 이름이 겹친다
- component scan bean 이름과 `@Bean` 이름이 우연히 겹친다
- rename 중 old 이름과 new 이름을 같이 쓰다가 충돌한다

먼저 할 일은 단순하다.

1. 충돌한 bean 이름이 정확히 무엇인지 본다
2. 그 이름을 만드는 선언이 두 군데인지 찾는다
3. 정말 "교체" 의도인지, 그냥 우연한 중복인지 결정한다

우연한 중복이면 보통 **이름을 분리**하는 쪽이 맞다.

빠른 fix 후보는 아래 셋이다.

- `@Bean` 이름을 명시적으로 바꾼다
- 중복 import / 중복 configuration 경로를 끊는다
- rename 중 남은 `@Qualifier("oldName")`, `@Bean("oldName")` 문자열을 정리한다

<a id="symptom-overriding-disabled"></a>

## `overriding is disabled`가 보이면

이건 "같은 이름 충돌이 있었고, Boot가 안전하게 막았다"로 읽으면 된다.

초보자가 자주 하는 오해는 이것이다.

- `spring.main.allow-bean-definition-overriding=true`만 켜면 해결된다고 생각한다

하지만 beginner 기준 첫 질문은 따로 있다.

- 내가 정말 기존 bean을 **의도적으로 교체**하려는가?
- 아니면 이름이 우연히 겹친 것뿐인가?

의도적 교체가 아니라면 설정을 켜기보다 아래를 먼저 본다.

- bean 이름을 명시적으로 분리할 수 있는가
- 테스트용 설정이 운영 설정과 섞여 들어왔는가
- 같은 역할 bean을 top-level 교체 대신 customizer나 조건부 등록으로 풀 수 있는가

즉 이 문구의 beginner용 결론은 "`설정을 켤까?`"보다 "`왜 같은 이름이 됐지?`"가 먼저다.

<a id="symptom-backoff"></a>

## `@ConditionalOnMissingBean did not match`나 `existing bean`이 보이면

이 경우는 보통 override 예외가 아니라 **back-off**다.

즉 Boot 기본 bean이 "충돌 후 패배"한 것이 아니라, 처음부터 아래처럼 판단한 것이다.

```text
이미 같은 역할 bean이 있네?
그럼 내 기본 bean은 만들지 말자.
```

이때 첫 대응은 `@Primary`를 붙이는 것이 아니다.
먼저 아래를 찾는다.

- 어떤 사용자 `@Bean`이 이미 같은 타입/이름 역할을 차지했는가
- 다른 starter나 `@Import`가 먼저 bean을 만들었는가
- conditions report에서 `existing bean`으로 찍힌 대상이 누구인가

즉 back-off는 "등록 충돌을 허용할지"가 아니라 **기본 bean 생성 자체를 멈춘 것**이다.

이 분기에서는 보통 아래 fix가 먼저 나온다.

- 직접 등록한 bean을 유지하고 기본 bean 부재를 정상으로 받아들인다
- 의도하지 않은 선등록 bean이면 import/scan/starter 경로를 정리한다
- 커스터마이징만 필요했다면 bean 교체 대신 customizer 확장 지점을 쓴다

<a id="symptom-found-2"></a>

## `expected single matching bean but found 2`가 보이면

이건 override보다 **후보 선택 문제**다.

여기서는 보통 bean 두 개가 다 살아 있다.
문제는 Spring이 생성자 파라미터 하나에 무엇을 넣어야 할지 모른다는 점이다.

이때는 아래 셋 중 하나로 간다.

- 기본 구현 하나가 필요하다 -> `@Primary`
- 이 주입 지점만 특정 구현체를 원한다 -> `@Qualifier`
- 원래 여러 구현을 다 받아야 한다 -> `List<T>` 또는 `Map<String, T>`

즉 `found 2`는 "등록 실패"보다 **선택 규칙 부재**에 가깝다.

이 메시지에서 bean 이름을 억지로 통일하거나 override 허용 설정을 켜는 것은 보통 잘못된 축이다.

## 자주 섞이는 세 메시지 비교

| 보이는 문구 | 실제 상태 | 왜 헷갈리나 | 먼저 고칠 축 |
|---|---|---|---|
| `BeanDefinitionOverrideException` | 같은 이름 등록 충돌 | bean 관련 문제라서 `@Primary`와 섞어 보기 쉽다 | 이름 충돌 |
| `@ConditionalOnMissingBean did not match` | 기본 bean back-off | "내 bean이 기본 bean을 override했다"처럼 느껴진다 | 조건부 등록 / 기존 bean 출처 |
| `NoUniqueBeanDefinitionException`, `found 2` | 후보 선택 실패 | bean이 여러 개라서 "중복 등록"처럼 보일 수 있다 | candidate selection |

여기서 중요한 한 줄은 이것이다.

```text
같은 이름 충돌과 같은 타입 후보 중복은 다른 문제다.
```

## 실무에서 쓰는 모습

### 예시 1. 이름 충돌

```java
@Configuration
class AConfig {
    @Bean("paymentClient")
    PaymentClient tossPaymentClient() {
        return new TossPaymentClient();
    }
}

@Configuration
class BConfig {
    @Bean("paymentClient")
    PaymentClient kakaoPaymentClient() {
        return new KakaoPaymentClient();
    }
}
```

이 경우는 `paymentClient` 이름 하나를 두 definition이 동시에 차지하려 해서 override 예외 쪽으로 읽는다.

### 예시 2. back-off

```java
@Bean
@ConditionalOnMissingBean(PaymentClient.class)
PaymentClient defaultPaymentClient() {
    return new DefaultPaymentClient();
}
```

이미 앱 쪽에서 `PaymentClient`를 등록했다면 Boot 기본 bean은 아예 안 생길 수 있다.
이건 "졌다"보다 "처음부터 안 만들었다"에 가깝다.

### 예시 3. 후보 선택 실패

```java
@Bean
PaymentClient tossPaymentClient() {
    return new TossPaymentClient();
}

@Bean
PaymentClient kakaoPaymentClient() {
    return new KakaoPaymentClient();
}
```

둘 다 등록된 뒤 `PaymentClient` 하나만 주입하려 하면 `found 2` 경로로 내려간다.

## 흔한 오해와 함정

- `@Primary`를 붙이면 `BeanDefinitionOverrideException`도 해결된다
  - 아니다. `@Primary`는 등록 후 후보 선택 규칙이다.
- `existing bean found`는 override가 성공했다는 뜻이다
  - 아니다. 보통은 `@ConditionalOnMissingBean`이 back off했다는 뜻이다.
- `allow-bean-definition-overriding=true`를 켜면 항상 정답이다
  - 아니다. 테스트용 임시 우회일 수는 있어도, beginner 기본 해법은 충돌 원인 분리다.
- rename 뒤 startup 에러가 났으면 무조건 scan 문제다
  - 아니다. bean 이름 문자열 계약이 깨졌을 수도 있다.

## 더 깊이 가려면

- 이름 충돌과 주입 우선순위를 한 장에서 먼저 분리하고 싶다면 [Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다](./spring-primary-vs-bean-override-primer.md)로 간다.
- Boot 기본 bean back-off를 더 정확히 보고 싶다면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)를 본다.
- bean 이름이 어디서 생기고 rename이 왜 깨지는지 보려면 [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)로 간다.
- 컨테이너 정책 자체를 더 깊게 보려면 [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)로 올라간다.

## 면접/시니어 질문 미리보기

> Q: `BeanDefinitionOverrideException`와 `NoUniqueBeanDefinitionException`의 차이는?
> 의도: 이름 충돌과 후보 선택 실패를 구분하는지 확인
> 핵심: 전자는 같은 이름 definition 충돌, 후자는 여러 후보 중 하나를 못 고르는 주입 문제다.

> Q: `existing bean`이 보이면 override가 일어난 것인가?
> 의도: back-off와 override를 분리하는지 확인
> 핵심: 많은 경우 `@ConditionalOnMissingBean`이 기존 bean을 보고 기본 bean 생성을 멈춘 것이다.

> Q: `allow-bean-definition-overriding=true`는 언제 조심해야 하나?
> 의도: 임시 우회와 의도된 교체를 구분하는지 확인
> 핵심: 테스트나 특수 교체 시나리오가 아니면 우연한 이름 충돌을 가리는 설정이 될 수 있다.

## 한 줄 정리

startup bean 오류에서 `override` 비슷한 말이 보여도, 먼저 `같은 이름 충돌`, `Boot back-off`, `후보 선택 실패` 셋 중 무엇인지 가르면 고칠 축이 바로 보인다.
