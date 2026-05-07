---
schema_version: 3
title: Spring scanBasePackages vs Import vs AutoConfiguration Selection
concept_id: spring/scanbasepackages-vs-import-autoconfiguration-selection
canonical: true
category: spring
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 78
review_feedback_tags:
- scanbasepackages-vs-import
- autoconfiguration-selection
- vs-auto-configuration
- shared-module-bean
aliases:
- scanBasePackages vs @Import vs auto-configuration
- shared module bean registration
- component scan boundary
- Spring Boot auto configuration selection
- explicit configuration import
intents:
- comparison
- design
linked_paths:
- contents/spring/spring-bean-registration-path-decision-guide.md
- contents/spring/spring-scanbasepackages-import-autoconfiguration-decision-guide.md
- contents/spring/spring-boot-autoconfiguration-basics.md
- contents/spring/spring-configuration-vs-autoconfiguration-primer.md
- contents/spring/spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md
- contents/spring/spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md
confusable_with:
- spring/bean-registration-path-decision-guide
- spring/scanbasepackages-import-autoconfiguration-decision-guide
- spring/spring-configuration-vs-autoconfiguration-primer
expected_queries:
- Spring에서 scanBasePackages @Import auto-configuration 중 무엇을 골라야 해?
- shared module bean registration은 component scan보다 auto-configuration이 나아?
- 작은 설정을 명시적으로 가져올 때 @Import가 맞는 경우는?
- 여러 애플리케이션에 배포되는 모듈은 Boot auto-configuration으로 빼야 해?
contextual_chunk_prefix: |
  이 문서는 Spring shared module의 bean registration 방식을 scanBasePackages, @Import,
  Boot auto-configuration으로 나누는 chooser다. 같은 앱이 함께 소유하는 코드, 작은 명시적 설정,
  여러 앱에 배포되는 재사용 모듈이라는 ownership 기준으로 선택한다.
---
# Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준

> 한 줄 요약: 같은 애플리케이션이 함께 소유하는 코드라면 component scan 범위를 넓히거나 package root를 정리하고, 가져올 설정이 작고 명시적이어야 한다면 `@Import`, 여러 애플리케이션에 배포되는 shared module이라면 Boot auto-configuration을 우선 본다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 **shared module bean registration decision guide**를 담당한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
> - [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring BeanDefinitionRegistryPostProcessor and ImportBeanDefinitionRegistrar](./spring-bean-definition-registry-postprocessor-import-registrar.md)
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)

retrieval-anchor-keywords: scanbasepackages vs @import, scanbasepackageclasses vs @import, component scan shared module, spring shared module registration, multi module spring boot, shared config module, explicit import config, boot auto-configuration decision, spring starter decision, library module bean registration, internal module component scan, app-owned module scan, shared infra module import, spring scanbasepackages vs import autoconfiguration selection basics, spring scanbasepackages vs import autoconfiguration selection beginner

## 이 문서 다음에 보면 좋은 문서

- component scan 자체의 실패 패턴은 [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)으로 이어진다.
- component scan을 넓혔는데 JPA entity/repository는 여전히 안 보이는 경우는 [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)에서 따로 본다.
- Boot 기본값 제공 구조를 더 깊게 보려면 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)를 본다.
- `@Configuration`, `@Bean`, `proxyBeanMethods`의 입문 mental model은 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)와 연결된다.
- registry 단계 확장이 왜 마지막 수단인지 보려면 [Spring BeanDefinitionRegistryPostProcessor and ImportBeanDefinitionRegistrar](./spring-bean-definition-registry-postprocessor-import-registrar.md)를 같이 본다.

---

## 핵심 개념

이 선택은 "어떻게든 Bean을 보이게 만든다"가 아니라, **이 module을 애플리케이션 내부 코드로 볼지, 명시적으로 붙이는 설정 묶음으로 볼지, starter-style shared library로 볼지**를 정하는 일이다.

- component scan 확장: "이 코드는 우리 앱의 일부다. 같은 애플리케이션 경계 안에서 함께 발견되면 된다."
- `@Import`: "이 설정 묶음을 이 앱이 의도적으로 가져오겠다."
- Boot auto-configuration: "classpath와 property 조건이 맞으면 기본값을 제공하되, 앱이 필요하면 override할 수 있어야 한다."

즉 질문은 "`scanBasePackages`를 더 크게 열까?"가 아니라, **이 module의 소유권과 활성화 방식이 무엇인가**다.

여기서 JPA만 예외처럼 보이는 이유도 같이 기억해야 한다.

- `scanBasePackages`는 component scan alias다
- `@EntityScan`은 entity metadata 경계다
- `@EnableJpaRepositories`는 repository interface 경계다

즉 shared module을 붙이는 문제와 JPA startup boundary 문제는 겹치지만, **같은 annotation 하나로 같이 움직이지는 않는다**.

---

## 먼저 결론부터 보는 선택표

| 상황 | 우선 선택 | 이유 |
|---|---|---|
| 같은 애플리케이션을 쪼갠 내부 module이고, 함께 배포/리팩터링된다 | package root 정리 또는 제한적 component scan 확장 | 앱 소유 코드라면 "발견" 모델이 자연스럽다 |
| shared module에서 필요한 Bean이 몇 개 안 되고, 앱이 opt-in 여부를 직접 드러내야 한다 | `@Import` | 의존이 코드에 드러나고 scan 오염을 막는다 |
| 여러 서비스가 쓰는 공통 starter이고, classpath/property/기존 Bean에 따라 조건부로 켜져야 한다 | Boot auto-configuration | starter 계약, 기본값 제공, override 지점 설계에 맞다 |
| module 하나 때문에 `com.company` 전체를 scan하고 싶다 | 피한다 | scan 경계가 앱 의도보다 넓어지고 예측성이 떨어진다 |

짧게 말하면 이렇다.

- **app-owned module**이면 scan 쪽
- **explicit feature opt-in**이면 `@Import`
- **reusable shared default**면 auto-configuration

---

## 1. component scan을 넓혀도 되는 경우

component scan 확장은 "한 앱 안의 같은 bounded context"를 자연스럽게 묶을 때만 편하다.

대표 조건:

- 같은 애플리케이션 저장소/배포 단위 안에서 함께 움직인다
- package root를 공유하거나 marker class로 좁게 지정할 수 있다
- `@Service`, `@Repository`, `@Controller`처럼 stereotype 기반 발견이 자연스럽다
- 이 module이 다른 앱에 독립 라이브러리처럼 배포되지는 않는다

예를 들면:

```text
com.example
  ├── app
  │   └── Application
  ├── order
  │   └── OrderService
  └── member
      └── MemberRepository
```

이 경우엔 보통 `Application` 위치를 `com.example`로 올리거나, marker class 기반으로 scan 범위를 맞추는 편이 단순하다.

```java
@SpringBootApplication(scanBasePackageClasses = {
        Application.class,
        OrderModuleMarker.class,
        MemberModuleMarker.class
})
public class Application {
}
```

### 언제 `scanBasePackages`보다 `scanBasePackageClasses`를 우선하나

`scanBasePackages` string literal은 refactor에 약하다.

- package rename 시 조용히 깨질 수 있다
- IDE rename 안전성이 낮다
- "왜 이 package를 열었는지" 코드에서 덜 드러난다

따라서 scan 확장이 필요하더라도 보통은 `scanBasePackageClasses` 쪽이 낫다.

### 이 선택이 맞지 않는 신호

아래 중 하나면 scan 확장을 멈추고 `@Import`/auto-configuration을 다시 본다.

- 특정 shared module 하나 때문에 회사 공통 package 전체를 열고 있다
- library module의 내부 helper까지 소비자 앱 scan에 섞인다
- 앱마다 켜야 하는 Bean이 다르다
- classpath 조건, property 조건, 사용자 override가 필요하다

---

## 2. `@Import`가 더 맞는 경우

`@Import`는 "이 설정 묶음을 내가 명시적으로 채택한다"는 계약이다.

대표 조건:

- shared module이 제공하는 설정이 작고 경계가 명확하다
- 앱이 의도적으로 opt-in 해야 한다
- component scan으로 library 내부 stereotype를 전부 노출하고 싶지 않다
- auto-configuration까지 갈 정도로 조건부/범용 starter 설계가 필요하지 않다

예를 들면 공통 HTTP client 설정, 공통 `Clock`, 특정 feature toggle용 config처럼 **몇 개의 supporting bean**만 가져오면 되는 경우다.

```java
@Configuration
@Import(CommonHttpClientConfig.class)
public class ExternalApiModuleConfig {
}
```

이 방식의 장점:

- import 지점이 코드에 남아서 의존이 보인다
- consumer package scan을 넓히지 않는다
- library가 stereotype annotation으로 앱 전체에 새어 들어오지 않는다

### `@Import`가 scan보다 나은 전형적인 사례

```text
app
shared-http-client
shared-json-config
```

이런 module은 "우리 앱의 service/repository/controller 계층"이라기보다 **지원 설정 번들**에 가깝다.
이때 `scanBasePackages = "com.company"`처럼 여는 것은 지나치게 넓고, `@Import`가 의도를 더 정확하게 드러낸다.

### `@Import`도 과하면 생기는 문제

- import 수가 계속 늘어 설정 조립 파일이 비대해진다
- 앱마다 똑같은 import 세트를 반복한다
- 조건부 활성화와 기본값 override가 필요해진다

이 시점부터는 starter-style auto-configuration이 더 자연스럽다.

---

## 3. Boot auto-configuration이 맞는 경우

shared module이 여러 애플리케이션에서 재사용되고, "있으면 기본값을 넣되 앱이 덮어쓸 수 있어야" 한다면 Boot auto-configuration으로 가는 편이 맞다.

대표 조건:

- 여러 앱이 공통 infra/client/observability 설정을 재사용한다
- classpath 유무, property 값, 기존 Bean 존재 여부에 따라 켜고 꺼야 한다
- 소비자는 starter 의존성 추가 정도만 하고 싶다
- 사용자 Bean override와 기본값 제공 정책이 필요하다

예를 들면:

- 사내 공통 `RestClient`/`WebClient` starter
- 공통 tracing/metrics starter
- 특정 외부 시스템 SDK wrapper starter

전형적인 형태는 이렇다.

```java
@AutoConfiguration
@ConditionalOnClass(RestClient.class)
public class CompanyHttpClientAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public CompanyHttpClient companyHttpClient(RestClient.Builder builder) {
        return new CompanyHttpClient(builder.build());
    }
}
```

이 선택의 핵심은 component scan이 아니라 **조건부 기본값 제공 계약**이다.

### auto-configuration을 과하게 쓰지 말아야 하는 경우

아래라면 auto-configuration은 오버엔지니어링일 수 있다.

- 이 앱 하나에서만 쓰는 내부 module이다
- 앱이 항상 명시적으로 붙여야 하는 config 몇 개뿐이다
- classpath/property/override 조건이 거의 없다

이 경우엔 `@Import`나 단순 수동 설정이 더 읽기 쉽다.

---

## 4. shared module에서 자주 나오는 잘못된 선택

### 안티패턴 1. shared module 하나 때문에 broad scan을 연다

```java
@SpringBootApplication(scanBasePackages = "com.company")
public class Application {
}
```

문제:

- 앱이 소유하지 않는 stereotype가 섞인다
- 같은 회사 package 아래의 다른 모듈까지 scan 후보가 된다
- Bean 충돌과 예측 불가능한 등록이 늘어난다

shared module을 붙이려는 목적이라면 보통 `@Import`나 starter가 더 적절하다.

### 안티패턴 2. library module이 `@Component` 투성이가 된다

library 내부 구현체를 전부 stereotype로 열어 두면 소비자 앱이 scan 경계를 넓혀야만 사용할 수 있게 된다.

이 구조는 보통 두 문제를 만든다.

- 구현 디테일까지 소비자 컨텍스트로 새어 나온다
- 어떤 Bean이 공개 API인지 감춰진다

shared module은 가능한 한 `@Configuration` + `@Bean`, 필요하면 auto-configuration으로 **공개 계약만 노출**하는 편이 낫다.

### 안티패턴 3. auto-configuration이 필요한데 매 앱마다 같은 `@Import`를 반복한다

여러 앱이 다음 import 세트를 복붙하기 시작하면, 이미 starter 후보일 가능성이 크다.

```java
@Import({
        CompanyMetricsConfig.class,
        CompanyTracingConfig.class,
        CompanyHttpClientConfig.class
})
```

반복이 늘수록 "공통 기본값 + 조건부 활성화"로 승격할 타이밍이다.

---

## 5. 빠른 판단 질문

아래 네 질문으로 대부분 정리된다.

1. 이 module은 **같은 앱 소유 코드**인가, 아니면 **여러 앱이 쓰는 shared library**인가?
2. 소비자가 이 module을 붙인 사실을 **코드에서 명시적으로 보여야** 하는가?
3. classpath/property/기존 Bean에 따른 **조건부 활성화**가 필요한가?
4. consumer 앱이 library 내부 stereotype까지 **발견 기반으로 노출받아도** 괜찮은가?

판단 규칙은 이렇게 줄일 수 있다.

- 1번이 "같은 앱 소유 코드"이고 2~4번 부담이 작으면 scan
- 2번이 "예"이고 3번이 "아니오"에 가깝다면 `@Import`
- 3번이 "예"면 Boot auto-configuration

---

## 6. 실전 시나리오

### 시나리오 1. app/core/infra로 나뉜 단일 애플리케이션

```text
app module   -> com.example.app
core module  -> com.example.core
infra module -> com.example.infra
```

세 module이 한 애플리케이션의 내부 계층이라면, 우선 package root를 정리하거나 marker class 기반 scan으로 맞춘다.
이건 shared library 통합보다 **앱 내부 구조 정렬** 문제에 가깝다.

### 시나리오 2. 공통 외부 API client 설정 모듈

`shared-payment-client`가 `WebClient`, retry 정책, auth header injector 몇 개만 제공한다면 `@Import(PaymentClientConfig.class)`가 보통 충분하다.
모든 소비자 앱이 scan 경계를 넓힐 이유는 없다.

### 시나리오 3. 조직 공통 observability starter

metrics/tracing/log correlation이 여러 앱에서 공통으로 쓰이고, 일부 Bean은 사용자 정의가 이겨야 한다면 auto-configuration이 맞다.
starter 의존성 + `@ConditionalOnMissingBean` + property toggle이 정석이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| component scan 확장 | 앱 내부 구조와 잘 맞으면 가장 자연스럽다 | 경계를 넓히기 쉬워 shared module 통합에는 둔감하다 | 같은 앱 소유 module |
| `@Import` | 의존이 명시적이고 scan 오염이 적다 | import 세트가 커지면 반복과 비대화가 생긴다 | 작고 명확한 shared config 묶음 |
| Boot auto-configuration | 재사용성, 조건부 활성화, override 정책이 좋다 | 초기 설계 비용이 가장 크다 | 여러 앱이 쓰는 starter-style shared module |

핵심은 "더 자동화된 쪽이 더 좋다"가 아니다.
**module의 배포 단위와 공개 계약에 맞는 쪽이 좋은 선택**이다.

---

## 꼬리질문

> Q: multi-module이면 `scanBasePackages`를 크게 열어 두는 게 항상 빠른 해결책 아닌가?
> 의도: broad scan과 module 계약을 구분하는지 확인
> 핵심: 앱 내부 module이면 가능하지만, shared module 통합이라면 `@Import`/auto-configuration이 더 명시적이다.

> Q: `@Import`와 component scan의 가장 큰 차이는 무엇인가?
> 의도: 발견 기반과 명시적 opt-in 차이를 확인
> 핵심: scan은 package 아래 stereotype를 발견하고, `@Import`는 설정 묶음을 명시적으로 채택한다.

> Q: Boot auto-configuration은 언제 `@Import`보다 낫나?
> 의도: starter 설계 시점을 구분하는지 확인
> 핵심: 여러 앱 재사용, 조건부 활성화, 사용자 override가 필요할 때다.

> Q: shared module도 모두 `@Component`로 두면 안 되나?
> 의도: library 공개 계약과 구현 노출 차이를 확인
> 핵심: 소비자 앱이 broad scan에 의존하게 되고, 구현 detail이 컨텍스트에 새어 나온다.

---

## 한 줄 정리

`scanBasePackages`를 넓히는 선택은 앱 내부 코드 경계를 정리할 때만 쓰고, shared module은 작고 명시적이면 `@Import`, 여러 앱에 기본값을 배포해야 하면 Boot auto-configuration으로 가져가는 편이 구조를 더 잘 드러낸다.
