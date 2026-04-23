# Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary

> 한 줄 요약: starter를 추가했다는 사실은 "자동 구성 후보를 classpath에 올렸다"는 뜻일 뿐이고, 실제 bean 생성은 classpath 조건, property, 기존 bean 존재, scan/import 경계가 모두 맞아야 일어난다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 흔한 "starter added but bean not created" 상황을 classpath/property/override/scan boundary로 빠르게 분기하는 **beginner troubleshooting FAQ**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)
> - [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
> - [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)

retrieval-anchor-keywords: starter added but bean missing, starter bean not created, spring starter bean missing, starter added no bean, why starter bean not created, spring boot starter bean missing, classpath condition fail, ConditionalOnClass miss, ConditionalOnProperty false, ConditionalOnMissingBean back off, existing bean found, bean override rule, allow-bean-definition-overriding, @Primary is not override, component scan boundary, scan import boundary, starter configuration not loaded, starter added but bean not created faq

## 이 문서 다음에 보면 좋은 문서

- `@Configuration`과 Boot auto-configuration의 큰 그림이 먼저 필요하면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)로 간다.
- 조건 평가를 실제로 보는 첫 진입점은 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)다.
- "누가 기존 bean으로 간주됐는가"를 더 정확히 보려면 [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)로 이어진다.
- 내 설정 클래스나 shared module 자체가 안 읽힌 것 같으면 [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md), [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)으로 넘어간다.

---

## 핵심 개념

초반에는 아래 네 줄만 잡으면 된다.

- starter는 보통 **의존성과 auto-configuration 후보**를 추가한다.
- bean은 후보가 생겼다고 자동으로 확정되지 않고, **조건이 통과해야** 실제 등록된다.
- Boot 기본 bean은 흔히 `@ConditionalOnMissingBean`이라서 **이미 비슷한 bean이 있으면 물러난다**.
- starter가 붙어도 **내 `@Configuration`/`@Component`는 scan/import 경계 밖이면 여전히 안 읽힌다**.

즉 "`starter`를 넣었다"는 말만으로는 원인을 못 정한다.  
실제 질문은 아래처럼 바뀌어야 한다.

1. auto-configuration이 classpath 조건에서 탈락했나?
2. property나 profile이 기능을 껐나?
3. 기존 bean 때문에 Boot 기본값이 back off 했나?
4. 내가 기대한 설정 클래스가 scan/import 경계 밖에 있나?

---

## starter가 해 주는 일과 해 주지 않는 일

| starter를 넣으면 보통 생기는 일 | starter를 넣어도 보장되지 않는 일 |
|---|---|
| 관련 라이브러리와 auto-configuration 후보가 classpath에 올라간다 | 조건이 안 맞는데 bean이 강제로 생성되지는 않는다 |
| Boot가 `@ConditionalOnClass`, `@ConditionalOnProperty`, `@ConditionalOnMissingBean`를 평가할 기회를 얻는다 | 내 앱의 임의 package를 대신 scan해 주지 않는다 |
| 소비자 앱이 의존성 하나로 기본 설정을 받을 준비를 한다 | 같은 역할의 사용자 bean이 있어도 Boot 기본 bean을 억지로 유지해 주지 않는다 |

여기서 제일 흔한 오해는 이것이다.

```text
starter 추가 = bean 확정
```

실제 의미는 아래에 더 가깝다.

```text
starter 추가 = auto-configuration 후보 등록 + 조건 평가 시작
```

---

## 30초 분기표

| 먼저 묻는 질문 | 보통 뜻하는 것 | 가장 먼저 확인할 증거 | 다음 문서 |
|---|---|---|---|
| target auto-configuration이 아예 negative match인가? | classpath 조건 또는 웹 타입 조건이 안 맞는다 | `--debug`, Actuator `conditions`, `@ConditionalOnClass`, `@ConditionalOnWebApplication` | [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md) |
| auto-configuration은 보이는데 property 조건에서 꺼졌나? | profile/env/property가 기능을 껐다 | `@ConditionalOnProperty`, active profile, env override | [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md) |
| report에 `@ConditionalOnMissingBean` miss나 `existing bean`이 보이나? | 이미 사용자 bean 또는 다른 starter bean이 있어 기본값이 물러났다 | 내 `@Bean`, `@Import`, test config, 다른 starter | [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md) |
| Boot 쪽은 positive match인데 내 설정 클래스나 커스텀 bean만 안 보이나? | scan/import boundary 문제다 | `@SpringBootApplication` package, `scanBasePackages`, `@Import` 여부 | [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md) |

핵심은 "`bean이 없다`"를 한 문장으로 끝내지 말고, **조건 실패 / property off / back-off / scan miss** 중 어디인지 먼저 가르는 것이다.

---

## 자주 묻는 질문

### Q1. starter를 넣었는데 왜 bean이 안 생기나?

가장 흔한 답은 "starter가 틀렸다"가 아니라 **조건이 아직 다 맞지 않았다**다.

- 필요한 클래스가 classpath에 없을 수 있다
- property가 `false`거나 다른 profile에서 꺼졌을 수 있다
- 이미 같은 역할의 bean이 있어서 Boot 기본값이 빠졌을 수 있다
- 기대한 설정 클래스가 scan/import 경계 밖일 수 있다

예를 들어 `spring-boot-starter-web`이 있어도 아래처럼 강제로 non-web 문맥이면 servlet 계열 bean 기대가 깨질 수 있다.

```properties
spring.main.web-application-type=none
```

즉 starter는 기능 후보를 제공하지만, **현재 애플리케이션 문맥이 그 기능을 실제로 켜는지**는 별도다.

### Q2. `@Primary`를 붙였는데 왜 Boot 기본 bean이 다시 안 뜨나?

`@Primary`는 **주입 시점의 우선 선택 규칙**이지, auto-configuration back-off를 되돌리는 스위치가 아니다.

- `@ConditionalOnMissingBean`은 "이미 bean이 존재하는가"를 본다
- `@Primary`는 "여러 bean 중 무엇을 주입할까"를 본다

즉 이미 사용자 bean이 하나라도 존재해서 Boot 기본값이 물러났다면, `@Primary`를 붙여도 "빠진 auto-config bean을 다시 생성"하지는 않는다.

### Q3. `spring.main.allow-bean-definition-overriding=true`를 켜면 해결되나?

대개 아니다.

이 설정은 **같은 bean name 정의 충돌을 허용할지**에 가깝다.  
반면 starter bean 누락의 흔한 원인은 아래 둘이다.

- 조건 실패로 auto-configuration이 애초에 실행되지 않음
- `@ConditionalOnMissingBean`이 기존 bean을 보고 back off 함

즉 override 허용은 **이미 충돌이 난 bean definition**의 문제이고, "`조건이 안 맞아 생성되지 않았다`"와는 별개다.

### Q4. starter를 넣었는데 내 `@Configuration`이 왜 안 읽히나?

starter와 component scan은 다른 경로다.

- starter auto-configuration은 metadata를 통해 import 된다
- 내 앱의 `@Configuration`/`@Component`는 여전히 scan 또는 `@Import`가 필요하다

따라서 shared module에 설정 클래스를 만들어 놓고 "starter를 넣었으니 소비자 앱이 알아서 scan하겠지"라고 기대하면 자주 빗나간다.  
이 경우는 broad scan보다 `@Import` 또는 starter-style auto-configuration 계약이 더 맞을 수 있다.

### Q5. 다른 환경에서는 되는데 테스트나 CI에서만 bean이 사라진다

대개 코드보다 **환경 입력값 차이**를 먼저 의심한다.

- test slice가 전체 auto-configuration을 안 올릴 수 있다
- test property가 feature를 껐을 수 있다
- dependency scope나 optional dependency 차이로 classpath가 달라질 수 있다

즉 "같은 코드인데 다르게 보인다"면 우선 classpath/profile/property diff를 본다.

---

## 가장 흔한 예시 두 개

### 1. 사용자 bean 때문에 Boot 기본값이 물러나는 경우

```java
@Configuration
public class CustomClockConfig {

    @Bean
    public Clock systemClock() {
        return Clock.systemUTC();
    }
}
```

Boot 쪽이 아래처럼 설계돼 있다면:

```java
@Bean
@ConditionalOnMissingBean
public Clock systemClock() {
    return Clock.systemDefaultZone();
}
```

이 상황은 "starter bean 생성 실패"라기보다 **사용자 bean이 이미 존재해서 기본값이 빠진 상태**다.

### 2. starter는 붙었지만 내 설정은 scan 경계 밖인 경우

```text
com.example.bootstrap.Application
com.example.feature.CustomFeatureConfig
com.shared.support.ExternalModuleConfig
```

`Application`이 `com.example.bootstrap` 아래에 있고 `ExternalModuleConfig`가 `com.shared.support`에 있다면, starter 유무와 별개로 그 설정 클래스는 기본 component scan에 잡히지 않을 수 있다.

즉 아래 두 문장을 분리해서 봐야 한다.

- starter auto-configuration 후보는 classpath에 올라왔다
- 내가 기대한 custom config는 scan/import 경계 밖이라 안 읽혔다

---

## 마지막 체크리스트

1. target bean 이름과 auto-configuration 클래스 이름을 먼저 적는다.
2. `--debug` 또는 Actuator `conditions`에서 positive/negative match를 확인한다.
3. negative match면 classpath 조건인지 property 조건인지 한 줄로 적는다.
4. `existing bean` 또는 `@ConditionalOnMissingBean` miss면 내 `@Bean`/`@Import`/다른 starter를 찾는다.
5. Boot 쪽은 positive인데 내 설정만 안 보이면 component scan 또는 `@Import` 경계를 본다.

이 순서로 보면 "`starter 넣었는데 bean이 안 떠요`"를 감으로 푸는 대신, **조건 평가 -> 기존 bean -> scan boundary** 순서로 좁힐 수 있다.
