# Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다

> 한 줄 요약: `@ConditionalOnMissingBean`은 "Boot 기본 bean을 등록할까?"를 묻고, `@Primary`는 "이미 등록된 후보 중 기본으로 무엇을 주입할까?"를 묻는다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 auto-configuration back-off와 bean candidate selection을 섞어 이해하는 오해를 빠르게 분리하는 **beginner comparison primer**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
> - [Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다](./spring-primary-vs-bean-override-primer.md)
> - [Spring `@ConditionalOnBean` 경계 노트: activation과 DI 후보 선택은 다르다](./spring-conditionalonbean-activation-vs-di-candidate-selection-primer.md)
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
> - [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)

retrieval-anchor-keywords: @ConditionalOnMissingBean vs @Primary, ConditionalOnMissingBean primary confusion, primary is not auto configuration override, primary does not restore boot bean, auto-configuration back-off vs bean selection, bean registration vs dependency injection, boot default bean skipped existing bean, user bean wins boot default, ConditionalOnMissingBean back off, existing bean found primary ignored, spring boot default bean missing primary, bean candidate selection vs conditional bean registration, beginner spring boot bean choice, @Primary injection priority, @ConditionalOnMissingBean miss

## 먼저 mental model

두 annotation은 같은 "bean 문제"처럼 보이지만 질문하는 시간이 다르다.

```text
1. bean 등록 단계
   Boot: "이미 이 역할의 bean이 있나?"
   없으면 기본 bean 등록, 있으면 back off
   -> @ConditionalOnMissingBean

2. bean 주입 단계
   Spring: "등록된 후보 중 이 생성자 파라미터에 무엇을 넣을까?"
   여러 후보면 @Qualifier, @Primary, 이름 등을 보고 하나 선택
   -> @Primary
```

초보자용 한 줄 감각은 이렇다.

- `@ConditionalOnMissingBean`: **만들지 말지**를 정한다
- `@Primary`: **이미 만들어진 것 중 무엇을 넣을지**를 정한다

그래서 `@Primary`를 붙였는데 Boot 기본 bean이 "다시 생기지 않는" 것은 정상이다.
`@Primary`는 등록 여부가 아니라 주입 우선순위만 바꾼다.

여기에 "같은 bean 이름 충돌"까지 같이 섞여 있다면 [Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다](./spring-primary-vs-bean-override-primer.md)에서 override/name collision 축을 먼저 분리하는 편이 빠르다.

같은 시간축 분리를 `@ConditionalOnBean`까지 확장하고 싶다면 [Spring `@ConditionalOnBean` 경계 노트: activation과 DI 후보 선택은 다르다](./spring-conditionalonbean-activation-vs-di-candidate-selection-primer.md)를 바로 이어서 보면 된다.

---

## 한눈에 비교

| 구분 | `@ConditionalOnMissingBean` | `@Primary` |
|---|---|---|
| 핵심 질문 | "이미 bean이 있으면 Boot 기본값을 만들지 말까?" | "여러 bean이 있으면 기본으로 무엇을 주입할까?" |
| 동작 시점 | auto-configuration이 bean definition을 등록할 때 | 의존성 주입 지점에서 후보를 고를 때 |
| 주로 붙는 곳 | Boot auto-configuration의 `@Bean` | 사용자가 만든 `@Component`나 `@Bean` |
| 보는 대상 | 기존 bean 존재 여부 | 이미 등록된 후보 목록 |
| 해결하는 문제 | Boot 기본값과 사용자 설정의 중복 등록 방지 | `NoUniqueBeanDefinitionException` 같은 단일 주입 후보 선택 |
| 하지 않는 일 | 후보 중 하나를 주입 대상으로 고르지 않는다 | skipped auto-configuration bean을 다시 등록하지 않는다 |

핵심은 순서다.

```text
등록되지 않은 bean은 @Primary 후보가 될 수 없다.
```

---

## 예제 1. 사용자 bean 때문에 Boot 기본값이 물러난다

Boot auto-configuration이 이런 기본 bean을 제공한다고 가정한다.

```java
@AutoConfiguration
public class MailAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean(MailSender.class)
    public MailSender defaultMailSender() {
        return new SmtpMailSender();
    }
}
```

그런데 애플리케이션에서 이미 같은 타입의 bean을 등록했다.

```java
@Configuration
public class AppMailConfig {

    @Bean
    @Primary
    public MailSender customMailSender() {
        return new SesMailSender();
    }
}
```

이때 결과는 이렇게 읽어야 한다.

1. `customMailSender`가 먼저 bean 후보로 보인다.
2. Boot가 `@ConditionalOnMissingBean(MailSender.class)`를 평가한다.
3. 이미 `MailSender` bean이 있으므로 `defaultMailSender`는 등록되지 않는다.
4. `@Primary`는 `customMailSender`가 등록된 뒤의 주입 우선순위일 뿐이다.

즉 이 상황에서 `@Primary`는 "Boot 기본값과 내 bean 중 내 bean을 고른다"가 아니다.
Boot 기본값은 애초에 back off되어 후보 목록에 없다.

---

## 예제 2. `@Primary`는 후보가 둘 이상 있을 때 의미가 생긴다

아래처럼 실제로 같은 타입 bean이 둘 다 등록되어 있다면 이야기가 다르다.

```java
@Configuration
public class MultiMailConfig {

    @Bean
    public MailSender smtpMailSender() {
        return new SmtpMailSender();
    }

    @Bean
    @Primary
    public MailSender sesMailSender() {
        return new SesMailSender();
    }
}
```

그리고 서비스가 타입만 보고 하나를 주입받는다.

```java
@Service
public class NoticeService {

    public NoticeService(MailSender mailSender) {
    }
}
```

이때는 `smtpMailSender`와 `sesMailSender`가 모두 등록되어 있으므로, Spring이 단일 후보를 골라야 한다.
그래서 `@Primary`가 붙은 `sesMailSender`가 기본으로 선택된다.

여기서의 질문은 auto-configuration back-off가 아니라 **주입 후보 선택**이다.

---

## 가장 흔한 오해

| 헷갈리는 말 | 맞는 해석 |
|---|---|
| "`@Primary`를 붙이면 `@ConditionalOnMissingBean`이 무시된다" | 아니다. primary bean도 여전히 "존재하는 bean"이다. missing 조건은 존재 여부를 본다. |
| "Boot 기본 bean과 내 bean이 둘 다 생기고 `@Primary`가 이긴다" | 많은 Boot 기본 bean은 `@ConditionalOnMissingBean` 때문에 내 bean이 있으면 아예 등록되지 않는다. |
| "`@ConditionalOnMissingBean`이 있으면 후보 중복 문제가 사라진다" | 아니다. 사용자 bean이나 다른 library bean이 여러 개면 주입 단계에서 여전히 애매할 수 있다. |
| "Boot bean이 안 뜨니 `@Primary`를 붙이면 된다" | 아니다. 조건 평가에서 빠진 문제면 `conditions` report에서 어떤 조건이 실패했는지 봐야 한다. |

초반에는 아래처럼 증상별로 갈라 보면 된다.

| 보이는 증상 | 먼저 볼 문제 | 다음 행동 |
|---|---|---|
| `@ConditionalOnMissingBean` miss, `existing bean` | auto-configuration back-off | 누가 같은 타입/역할 bean을 등록했는지 찾는다 |
| `expected single matching bean but found 2` | bean 후보 선택 | `@Primary`, `@Qualifier`, collection 주입 중 맞는 전략을 고른다 |
| starter를 넣었는데 bean 자체가 안 보임 | 조건 실패 또는 scan/import 경계 | `--debug`, Actuator `conditions`, starter FAQ로 분기한다 |

---

## 언제 무엇을 쓰나

| 원하는 것 | 적절한 선택 |
|---|---|
| 우리 앱의 기본 구현을 Boot 기본값 대신 쓰고 싶다 | 같은 타입의 사용자 `@Bean`을 등록한다. Boot가 `@ConditionalOnMissingBean`이면 보통 back off한다. |
| 같은 타입 구현체가 여러 개이고 보통 쓸 기본 후보가 필요하다 | 기본 후보에 `@Primary`를 붙인다. |
| 특정 주입 지점은 반드시 다른 구현체여야 한다 | 그 주입 지점에 `@Qualifier`를 붙인다. |
| Boot 기본 설정 전체를 갈아엎고 싶지는 않고 일부 설정만 바꾸고 싶다 | top-level bean 교체보다 Boot가 제공하는 customizer bean이 있는지 먼저 찾는다. |

마지막 줄은 `ObjectMapper`, `WebClient.Builder`, MVC 설정에서 자주 중요하다.
전체 bean을 교체하면 `@ConditionalOnMissingBean` 때문에 Boot 기본 구성 묶음이 빠질 수 있으니, 단순 옵션 변경인지 전체 교체인지 먼저 나눈다.

---

## 디버깅 순서

1. 내가 찾는 bean 타입과 이름을 적는다.
2. 같은 타입 bean이 실제로 몇 개인지 본다.
3. `--debug`나 Actuator `conditions`에서 target auto-configuration이 positive인지 negative인지 확인한다.
4. `@ConditionalOnMissingBean` miss면 기존 bean 등록 출처를 찾는다.
5. 후보가 여러 개인 주입 오류면 `@Primary`/`@Qualifier` 문제로 내려온다.

이 순서가 중요한 이유는 간단하다.

```text
조건 평가 문제를 주입 우선순위로 고칠 수 없고,
주입 후보 문제를 auto-configuration 조건만 보고 해결할 수도 없다.
```

---

## 꼬리질문

> Q: `@ConditionalOnMissingBean`과 `@Primary`를 한 줄로 나누면?
> 의도: 등록 단계와 주입 단계를 구분하는지 확인
> 핵심: `@ConditionalOnMissingBean`은 bean 등록 back-off 조건이고, `@Primary`는 등록된 후보 중 단일 주입 기본값이다.

> Q: 사용자 `MailSender` bean에 `@Primary`를 붙이면 Boot의 `defaultMailSender`가 다시 생기는가?
> 의도: primary가 auto-configuration 조건에 영향을 주지 않음을 확인
> 핵심: 아니다. 이미 `MailSender`가 존재하면 `@ConditionalOnMissingBean(MailSender.class)` 조건은 실패할 수 있고, `@Primary`는 그 bean을 다시 만들지 않는다.

> Q: `expected single matching bean but found 2`면 먼저 무엇을 봐야 하는가?
> 의도: 후보 중복 오류와 back-off 디버깅을 분리
> 핵심: 실제 후보가 둘 이상 등록된 상태이므로 `@Primary`, `@Qualifier`, collection 주입 중 요구사항에 맞는 선택 규칙을 고른다.

## 한 줄 정리

`@ConditionalOnMissingBean`은 "Boot 기본 bean을 만들지 말지"의 조건이고, `@Primary`는 "이미 있는 bean 중 기본으로 무엇을 넣을지"의 우선순위다. 둘을 시간 순서로 나누면 auto-configuration back-off와 bean 선택 오해가 대부분 정리된다.
