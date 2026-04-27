# Spring `@ConditionalOnBean` 경계 노트: activation과 DI 후보 선택은 다르다

> 한 줄 요약: `@ConditionalOnBean`은 "이 자동 구성/bean을 켤까?"를 묻고, DI candidate selection은 "이미 켜진 뒤 어떤 bean을 주입할까?"를 묻는다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `@ConditionalOnBean` 활성화 조건과 `@Primary`/`@Qualifier` 기반 주입 후보 선택을 섞어 이해하는 오해를 빠르게 분리하는 **beginner companion primer**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
> - [Spring `@ConditionalOnSingleCandidate` vs `@Primary` Primer: activation 조건과 주입 우선순위는 다르다](./spring-conditionalonsinglecandidate-vs-primary-primer.md)
> - [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
> - [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)

retrieval-anchor-keywords: @ConditionalOnBean activation vs DI candidate selection, ConditionalOnBean does not choose bean, ConditionalOnBean vs @Primary, ConditionalOnBean vs @Qualifier, condition passes but autowire ambiguous, ConditionalOnBean name does not inject named bean, conditional bean activation vs dependency injection, spring condition positive but NoUniqueBeanDefinitionException, existing prerequisite bean required not bean choice, auto-configuration activation vs bean injection, ConditionalOnBean positive match ambiguous dependency, beginner ConditionalOnBean primer, spring conditional activation boundary, ConditionalOnBean debug output, ConditionalOnBean actuator conditions, ConditionalOnBean positive match negative match

## 먼저 mental model

초보자 기준으로는 아래 두 줄만 먼저 잡으면 된다.

- `@ConditionalOnBean`: **켜도 되는지**를 본다
- `@Primary` / `@Qualifier` / collection 주입: **무엇을 넣을지**를 본다

시간 순서로 보면 더 덜 헷갈린다.

```text
1. 조건 평가 단계
   "선행 bean이 하나라도 있나?"
   -> 있으면 이 auto-configuration / @Bean 등록 진행
   -> @ConditionalOnBean

2. bean 생성 / 주입 단계
   "이 파라미터에는 어떤 bean을 넣지?"
   -> @Primary, @Qualifier, 이름, collection 규칙 적용
```

즉 `@ConditionalOnBean`이 통과했다고 해서, 그 타입의 bean 하나가 자동으로 골라졌다는 뜻은 아니다.

---

## 한눈에 비교

| 구분 | `@ConditionalOnBean` | DI candidate selection |
|---|---|---|
| 핵심 질문 | "이 bean/config를 활성화해도 되나?" | "주입 지점에 어떤 bean을 넣나?" |
| 동작 시점 | 조건 평가, bean definition 등록 전후 | 실제 bean 생성자/`@Bean` 파라미터 주입 시점 |
| 보는 대상 | 선행 bean의 존재 여부 | 이미 등록된 후보 목록 |
| 대표 도구 | `@ConditionalOnBean(type/name/annotation)` | `@Primary`, `@Qualifier`, parameter name, `List<T>`, `Map<String, T>` |
| 하는 일 | 조건이 맞으면 등록 경로를 연다 | 단일 후보를 고르거나 전체 후보를 받는다 |
| 하지 않는 일 | 여러 후보 중 하나를 대신 골라 주지 않는다 | 꺼져 있던 auto-configuration을 켜지 않는다 |

핵심은 이 한 줄이다.

```text
활성화 조건이 통과해도, 주입 후보 선택은 여전히 별도 문제다.
```

---

## 예제 1. 조건은 통과하지만 주입은 실패할 수 있다

자동 구성이 아래처럼 생겼다고 가정하자.

```java
@AutoConfiguration
public class PaymentReporterAutoConfiguration {

    @Bean
    @ConditionalOnBean(PaymentClient.class)
    public PaymentReporter paymentReporter(PaymentClient paymentClient) {
        return new PaymentReporter(paymentClient);
    }
}
```

애플리케이션 쪽에는 `PaymentClient`가 두 개 있다.

```java
@Configuration
public class PaymentClientConfig {

    @Bean
    public PaymentClient tossPaymentClient() {
        return new TossPaymentClient();
    }

    @Bean
    public PaymentClient kakaoPaymentClient() {
        return new KakaoPaymentClient();
    }
}
```

이때 흐름은 이렇게 읽어야 한다.

1. `PaymentClient`가 하나 이상 있으므로 `@ConditionalOnBean(PaymentClient.class)`는 통과한다.
2. 그래서 `paymentReporter` bean 등록 경로가 열린다.
3. 하지만 `paymentReporter(PaymentClient paymentClient)`를 만들려는 순간 후보가 둘이라 애매하다.
4. 이 단계에서는 `NoUniqueBeanDefinitionException`가 날 수 있다.

즉 여기서 막히는 이유는 "`@ConditionalOnBean`이 틀렸다"가 아니라, **조건은 맞았지만 주입 후보 선택 규칙이 없기 때문**이다.

---

## 예제 2. `name` 조건도 주입 대상을 대신 고르지 않는다

이 오해도 자주 나온다.

```java
@Bean("mainDataSource")
public DataSource mainDataSource() {
    return buildMain();
}

@Bean("auditDataSource")
public DataSource auditDataSource() {
    return buildAudit();
}
```

```java
@AutoConfiguration
public class AuditAutoConfiguration {

    @Bean
    @ConditionalOnBean(name = "mainDataSource")
    public AuditReader auditReader(DataSource dataSource) {
        return new AuditReader(dataSource);
    }
}
```

초보자가 흔히 이렇게 생각한다.

```text
name = "mainDataSource"니까 auditReader에도 그 bean이 들어가겠지?
```

아니다. 여기서 `name = "mainDataSource"`는 **활성화 조건**일 뿐이다.

- 조건 의미: `"mainDataSource"`라는 이름의 bean이 있으면 `AuditReader`를 만들 수 있다
- 주입 의미: `DataSource dataSource` 파라미터에는 어떤 `DataSource`를 넣을지 별도로 결정해야 한다

지금은 `DataSource`가 둘이므로 그대로 두면 여전히 애매할 수 있다.
정말 특정 bean을 넣고 싶다면 주입 지점도 명시해야 한다.

```java
@Bean
@ConditionalOnBean(name = "mainDataSource")
public AuditReader auditReader(@Qualifier("mainDataSource") DataSource dataSource) {
    return new AuditReader(dataSource);
}
```

---

## 가장 흔한 오해

| 헷갈리는 말 | 맞는 해석 |
|---|---|
| "`@ConditionalOnBean(Foo.class)`가 있으니 `Foo`가 자동으로 하나 골라진다" | 아니다. 조건은 존재 여부만 본다. 어떤 `Foo`를 주입할지는 별도 규칙이다. |
| "`name = \"foo\"`면 그 이름의 bean이 파라미터에도 들어간다" | 아니다. 이름 조건은 activation gate다. 정확한 주입은 `@Qualifier(\"foo\")` 같은 주입 규칙이 맡는다. |
| "condition report에서 positive match면 생성도 안전하다" | 아니다. 조건 통과 뒤에 constructor/`@Bean` 파라미터 주입이 또 실패할 수 있다. |
| "`NoUniqueBeanDefinitionException`가 났으니 `@ConditionalOnBean`이 miss한 것이다" | 오히려 반대일 수 있다. 조건은 통과했지만, 주입 단계에서 후보가 많아 실패한 것일 수 있다. |

---

## 증상별로 이렇게 가른다

| 보이는 증상 | 먼저 볼 문제 | 다음 행동 |
|---|---|---|
| condition report에서 `@ConditionalOnBean` negative match | 선행 bean 자체가 없다 | prerequisite bean 등록/scan/profile/property를 찾는다 |
| condition report는 positive match인데 bean creation에서 `found 2` | 후보 선택 문제다 | `@Primary`, `@Qualifier`, collection 주입 중 맞는 전략을 고른다 |
| 특정 이름의 bean이 있어 조건은 통과하지만 다른 bean이 주입된다 | activation과 injection이 섞였다 | 조건과 주입 지점을 각각 분리해서 본다 |

초반 디버깅 질문은 이렇게 바꾸면 된다.

- "`이 auto-configuration이 왜 안 켜졌지?`" -> 조건 문제
- "`켜지긴 했는데 왜 생성자 주입에서 터지지?`" -> 후보 선택 문제

---

## `--debug`와 Actuator `conditions`에서는 이렇게 보인다

초보자 기준으로는 **positive/negative match 문장을 한 줄씩 읽는 것**만으로도 충분하다.

| 어디서 보나 | positive일 때 읽는 뜻 | negative일 때 읽는 뜻 |
|---|---|---|
| `--debug` Condition Evaluation Report | "`PaymentClient`가 있어서 등록 경로를 열었다" | "`PaymentClient`가 없어서 등록 경로를 닫았다" |
| Actuator `/actuator/conditions` | 지금 떠 있는 앱에서도 같은 조건이 통과 중이다 | 지금 떠 있는 앱에서도 같은 조건이 실패 중이다 |

예를 들어 `@ConditionalOnBean(PaymentClient.class)`라면 `--debug` 로그에서는 보통 이런 식의 positive match를 보게 된다.

```text
PaymentReporterAutoConfiguration matched:
   - @ConditionalOnBean (types: com.example.PaymentClient; SearchStrategy: all) found bean 'tossPaymentClient' (OnBeanCondition)
```

이 문장에서 읽어야 할 핵심은 하나다.

- `found bean 'tossPaymentClient'` -> **조건은 통과했다**

반대로 prerequisite bean이 없으면 negative match는 보통 이런 식이다.

```text
PaymentReporterAutoConfiguration:
   Did not match:
      - @ConditionalOnBean (types: com.example.PaymentClient; SearchStrategy: all) did not find any beans of type com.example.PaymentClient (OnBeanCondition)
```

이때 핵심 해석은 이것이다.

- `did not find any beans` -> **아직 등록 경로도 안 열렸다**

Actuator `conditions`도 읽는 법은 같다. 형식은 JSON이지만 초보자는 `positiveMatches` / `negativeMatches`와 메시지 한 줄만 보면 된다.

```json
{
  "contexts": {
    "application": {
      "positiveMatches": {
        "PaymentReporterAutoConfiguration": [
          {
            "condition": "OnBeanCondition",
            "message": "@ConditionalOnBean (types: com.example.PaymentClient; SearchStrategy: all) found bean 'tossPaymentClient'"
          }
        ]
      }
    }
  }
}
```

```json
{
  "contexts": {
    "application": {
      "negativeMatches": {
        "PaymentReporterAutoConfiguration": {
          "notMatched": [
            {
              "condition": "OnBeanCondition",
              "message": "@ConditionalOnBean (types: com.example.PaymentClient; SearchStrategy: all) did not find any beans of type com.example.PaymentClient"
            }
          ]
        }
      }
    }
  }
}
```

즉, `--debug`든 Actuator든 `@ConditionalOnBean`에서 먼저 읽을 문장은 같다.

- `found bean ...`이면 activation은 통과했다
- `did not find any beans ...`이면 activation에서 멈췄다
- activation이 통과한 뒤 `found 2`, `expected single matching bean`이 나오면 그때부터는 DI 후보 선택 문제다

조건 report를 어디서 여는지부터 헷갈리면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 바로 이어서 본다.

---

## 언제 무엇을 써야 하나

| 원하는 것 | 적절한 선택 |
|---|---|
| 어떤 인프라 bean이 있을 때만 보조 bean을 켜고 싶다 | `@ConditionalOnBean` |
| 같은 타입 후보가 여러 개지만 보통 쓸 기본 후보 하나가 필요하다 | `@Primary` |
| 이번 주입 지점만 특정 bean이어야 한다 | `@Qualifier` |
| 여러 구현체를 전부 받아 직접 순회하거나 라우팅하고 싶다 | `List<T>` / `Map<String, T>` |

즉 `@ConditionalOnBean`은 "전제 조건이 만족될 때만 등록"이고,
`@Primary`/`@Qualifier`는 "등록된 뒤 어떤 후보를 쓸지 결정"이다.

---

## 디버깅 순서

1. condition report에서 target bean/auto-configuration이 positive인지 negative인지 먼저 본다.
2. negative면 prerequisite bean이 정말 없는지, profile/property/classpath 때문에 빠졌는지 본다.
3. positive인데 bean creation이 실패하면 생성자나 `@Bean` 메서드 파라미터의 후보 개수를 본다.
4. `found 2`, `expected single matching bean`이면 `@ConditionalOnBean`이 아니라 주입 선택 규칙 문제로 내려온다.
5. exact bean이 필요하면 `@Qualifier`, 여러 개가 필요하면 collection 주입으로 바꾼다.

핵심은 이 순서다.

```text
조건 통과 여부와 주입 후보 선택 여부를 같은 질문으로 다루면 계속 헷갈린다.
```

---

## 꼬리질문

> Q: `@ConditionalOnBean(Foo.class)`를 한 줄로 설명하면?
> 의도: activation gate로 이해하는지 확인
> 핵심: `Foo` bean이 이미 있을 때만 이 bean/auto-configuration을 활성화하는 조건이다.

> Q: `@ConditionalOnBean(Foo.class)`가 통과했는데 왜 `Foo foo` 파라미터에서 `found 2`가 날 수 있나?
> 의도: activation과 injection을 분리하는지 확인
> 핵심: 조건은 "하나 이상 존재"만 보고, 실제 주입은 여러 후보 중 하나를 따로 골라야 하기 때문이다.

> Q: `@ConditionalOnBean(name = "mainDataSource")`면 `mainDataSource`가 자동 주입되나?
> 의도: name 조건과 qualifier를 구분하는지 확인
> 핵심: 아니다. name 조건은 활성화 여부만 정한다. 정확한 주입은 `@Qualifier("mainDataSource")` 같은 규칙으로 따로 지정한다.

## 한 줄 정리

`@ConditionalOnBean`은 "이 bean을 켤 전제가 있나?"를 보는 activation 조건이고, DI candidate selection은 "이미 켜진 뒤 어떤 bean을 넣을까?"를 고르는 단계다. 둘을 시간 순서로 나누면 condition-related 오해가 크게 줄어든다.
