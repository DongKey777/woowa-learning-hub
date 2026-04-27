# Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정

> 한 줄 요약: component scan은 "프로젝트 전체 검색"이 아니라 `@SpringBootApplication`이나 `@ComponentScan`이 정한 base package 아래에서 stereotype 후보만 찾는 과정이므로, 패키지 위치 하나만 어긋나도 `NoSuchBeanDefinitionException`이 난다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 **component scan boundary troubleshooting primer**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)
- [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)
- [Spring Startup / Bean Graph Debugging](./spring-startup-bean-graph-debugging-playbook.md)
- [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)

retrieval-anchor-keywords: spring component scan failure, component scan boundary, springbootapplication package, scanbasepackages, scanbasepackageclasses, multi module component scan, missing stereotype annotation, nosuchbeandefinitionexception, profile conditional bean missing, condition evaluation report, starter bean missing faq, 처음 배우는데 bean 안 떠요, spring bean basics, component scan basics

## 이 문서 다음에 보면 좋은 문서

- Bean 등록과 DI의 큰 그림은 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)로 이어진다.
- `@SpringBootApplication` 안에서 `@ComponentScan`과 auto-configuration이 어떻게 갈리는지는 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)과 연결된다.
- shared module을 scan으로 붙일지 `@Import`/auto-configuration으로 붙일지 판단하려면 [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)을 같이 본다.
- service는 뜨는데 repository나 entity에서만 깨지면 [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)로 넘어가서 JPA 전용 경계를 따로 본다.
- package와 stereotype annotation은 멀쩡한데 특정 profile/test/CI에서만 bean이 사라지면 component scan보다 `@Profile`/conditional 탈락일 수 있으니 [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md), [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 먼저 분기한다.
- 증상이 startup failure 전체로 번졌다면 [Spring Startup / Bean Graph Debugging](./spring-startup-bean-graph-debugging-playbook.md)으로 이어서 본다.
- `NoSuchBeanDefinitionException`와 `NoUniqueBeanDefinitionException`를 먼저 가르고 싶다면 [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)에서 빠른 분기표를 먼저 본다.

---

## 먼저 10초 역분기

`bean이 안 떴다 = 무조건 scan 실패`로 보면 초반에 자주 헤맨다. 먼저 아래 둘 중 어디에 가까운지 가른다.

| 먼저 보는 질문 | component scan 쪽 | `@Profile`/conditional 쪽 |
|---|---|---|
| 언제 깨지는가? | 로컬, 테스트, 운영 어디서나 비슷하게 깨진다 | 특정 profile, 특정 테스트 슬라이스, CI/운영에서만 깨진다 |
| 코드에서 먼저 볼 것 | `@SpringBootApplication` 위치, `scanBasePackages`, stereotype annotation | `@Profile`, `@ConditionalOnProperty`, `@ConditionalOnClass`, `@ConditionalOnBean` |
| 바로 이어갈 문서 | 이 문서 | [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md), [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md), [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ](./spring-starter-added-but-bean-missing-faq.md) |

짧게 말하면 이렇다.

- package 구조나 annotation이 처음부터 어긋나 있으면 scan 누락일 가능성이 크다.
- package와 annotation은 멀쩡한데 환경마다 결과가 달라지면 scan보다 실행 조건 탈락을 먼저 의심한다.

예를 들어 `dev`에서는 뜨는데 `prod`에서만 안 뜨는 bean은, beginner가 가장 많이 scan 문제로 오해하는 케이스다. 이런 경우는 이 문서를 끝까지 읽기보다 condition 문서로 먼저 넘어가는 편이 더 빠르다.

## 핵심 개념

component scan 실패는 대개 "Spring이 이상하다"가 아니라 아래 셋 중 하나다.

1. **scan 시작점이 잘못됐다**
   `@SpringBootApplication`이 놓인 패키지가 너무 깊거나, custom scan 설정이 너무 좁다.
2. **scan 대상이 아니다**
   클래스가 classpath에 있어도 stereotype annotation이 없으면 Bean 후보가 아니다.
3. **module 경계와 package 경계를 혼동했다**
   Gradle/Maven module dependency가 있다고 해서 자동으로 scan 범위에 들어오지 않는다.

즉 component scan은 "모든 코드를 훑는 기능"이 아니라, **정해진 package boundary 안에서 Bean 후보를 수집하는 규칙**이다.

## 헷갈리기 쉬운 첫 분기

여기서 초보자가 먼저 잡아야 할 분기는 하나다.

- `NoSuchBeanDefinitionException`면 이 문서처럼 **후보 0개 경로**를 먼저 본다
- `NoUniqueBeanDefinitionException`면 scan 문제가 아니라 **후보 중복 경로**일 가능성이 더 크다

즉 예외 이름이 "못 찾음"인지 "못 고름"인지 먼저 나누면 component scan 문서로 와야 할지 더 빨리 결정된다.

여기서 하나만 더 붙이면 초보자 시행착오가 크게 줄어든다.

- package와 annotation이 틀렸으면 component scan 쪽이다
- package와 annotation은 맞는데 특정 환경에서만 bean이 사라지면 `@Profile`/conditional 쪽일 가능성이 더 크다

즉 `NoSuchBeanDefinitionException`라고 해서 항상 이 문서의 범위는 아니다.
scan 경계가 멀쩡해 보이면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md)나 [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ](./spring-starter-added-but-bean-missing-faq.md)로 바로 넘어가는 편이 빠르다.

## 먼저 이 오해부터 버린다

| 흔한 오해 | 실제 동작 |
|---|---|
| 의존 모듈에 클래스가 있으니 Bean으로 잡힌다 | package boundary 안에 있고 stereotype 또는 explicit registration이 있어야 한다 |
| `@SpringBootApplication`은 프로젝트 전체를 scan한다 | 해당 클래스 패키지와 하위 패키지를 기본으로 scan한다 |
| 클래스 이름이 `Service`, `Repository`면 알아서 등록된다 | `@Service`, `@Repository`, `@Component` 같은 annotation이 필요하다 |
| multi-module이면 scanBasePackages를 크게 열어 두는 게 정답이다 | app 소유 코드인지 library-style module인지 구분해서 root package, `@Import`, auto-configuration 중 하나를 선택해야 한다 |

위 마지막 분기가 이 문서의 바깥으로 커지면, 선택 기준 자체는 [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)으로 이어서 보는 편이 빠르다.

여기서 한 번 더 중요한 분기가 있다.

- service/controller bean이 안 잡히면 component scan 문제일 가능성이 크다
- repository bean이나 `Not a managed type`가 뜨면 component scan이 아니라 JPA 전용 경계 문제일 수 있다

즉 `@SpringBootApplication(scanBasePackages = ...)`를 손봤다고 JPA entity/repository discovery까지 함께 고쳐진다고 보면 안 된다. 이 분기는 [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)에서 따로 정리한다.

---

## 1. `@SpringBootApplication`이 너무 깊은 패키지에 있다

가장 흔한 실수다.

```text
com.example
  ├── order
  │   └── OrderService
  └── bootstrap
      └── app
          └── Application
```

`Application`이 `com.example.bootstrap.app`에 있으면 기본 scan 범위는 그 하위 패키지다.
즉 `com.example.order.OrderService`는 sibling package라서 잡히지 않는다.

대표 증상:

- `NoSuchBeanDefinitionException`
- `UnsatisfiedDependencyException`
- controller mapping이 안 잡혀서 endpoint가 없는 것처럼 보임

가장 좋은 수정은 보통 **메인 클래스를 공통 root package로 올리는 것**이다.

```text
com.example
  ├── Application
  ├── order
  │   └── OrderService
  └── member
      └── MemberController
```

`scanBasePackages`로 임시 봉합할 수는 있지만, 애플리케이션 전체가 하나의 package root를 공유한다면 구조를 바로잡는 편이 더 단순하다.

## 2. custom `scanBasePackages`가 기본 범위를 더 좁혀 버렸다

처음엔 잘 동작했는데, 특정 설정을 추가한 뒤 일부 Bean만 사라지는 경우가 있다.

```java
@SpringBootApplication(scanBasePackages = "com.example.api")
public class Application {
}
```

이 설정은 "api만 보고 싶다"는 뜻에 가깝다.
`com.example.service`, `com.example.infra`가 sibling이면 scan에서 빠진다.

문제가 되는 이유:

- 팀은 여전히 "`Application`이 `com.example` 아래 있으니 다 잡히겠지"라고 생각한다
- 실제 설정은 더 좁은 package만 보도록 바뀌어 있다

안전한 선택 순서:

1. 정말 custom scan이 필요한지 먼저 의심한다
2. 필요하다면 string literal보다 `scanBasePackageClasses`를 우선 고려한다
3. scan을 넓히는 대신 `@Import`가 더 맞는 module인지 구분한다

예를 들면 marker class 기반 구성이 refactor에 더 안전하다.

```java
@SpringBootApplication(scanBasePackageClasses = {
        Application.class,
        CoreModuleMarker.class
})
public class Application {
}
```

## 3. multi-module 구조인데 package root가 서로 달라 scan이 끊긴다

multi-module에서 자주 나오는 오해는 "dependency를 추가했으니 component scan도 넘어간다"는 생각이다.

```text
app module   -> com.example.app.Application
core module  -> com.example.core.OrderService
infra module -> com.example.infra.JpaOrderRepository
```

`Application`이 `com.example.app`에 있으면 기본 scan은 `com.example.app..*`이다.
`com.example.core`, `com.example.infra`는 sibling이라서 자동으로 잡히지 않는다.

여기서 선택지는 세 갈래다.

| 상황 | 우선 선택 | 이유 |
|---|---|---|
| 한 애플리케이션의 내부 모듈들이다 | 공통 root package 재정렬 | 구조가 가장 읽기 쉽다 |
| 별도 module을 제한적으로 붙인다 | `scanBasePackageClasses` | package 문자열보다 안전하다 |
| 재사용 library-style module이다 | `@Import` 또는 auto-configuration | broad scan보다 계약이 명확하다 |

즉 multi-module의 핵심은 "scan을 더 크게 열기"가 아니라, **이 module을 app 내부 코드처럼 볼지, library처럼 가져올지 먼저 결정하는 것**이다.

## 4. stereotype annotation이 빠져 있어서 scan 후보가 아니다

패키지 위치는 맞는데도 Bean이 안 잡히면, 다음으로 볼 것은 annotation이다.

```java
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }
}
```

이 클래스는 package 안에 있어도 Bean 후보가 아니다.
아래 둘 중 하나가 필요하다.

```java
@Service
public class OrderService {
}
```

또는

```java
@Configuration
public class OrderConfig {

    @Bean
    public OrderService orderService(OrderRepository orderRepository) {
        return new OrderService(orderRepository);
    }
}
```

특히 아래 실수가 beginner에게 많다.

- 구현체에는 annotation이 없고 interface만 존재한다
- utility/helper 클래스를 그냥 주입하려고 한다
- 외부 라이브러리 클래스를 stereotype 없이 직접 주입하려고 한다

원칙은 단순하다.

- **내 concrete class면** stereotype annotation
- **외부 객체거나 생성 로직이 중요하면** `@Bean`

## 5. default package를 쓰거나 package 선언이 제각각이다

package 선언 없이 `Application`을 default package에 두는 것은 피해야 한다.

```java
// package 선언 없음
@SpringBootApplication
public class Application {
}
```

이 경우 scan이 지나치게 넓어지거나 예측하기 어려워진다.
Spring Boot 문맥에서도 default package는 권장되지 않는다.

이 패턴의 문제:

- 어떤 코드가 scan 대상인지 추론이 어렵다
- startup 시간이 늘거나 원치 않는 classpath scan이 섞일 수 있다
- 팀원이 package 구조만 보고 경계를 이해하기 어렵다

실무 기준으로는 **반드시 명시적인 root package를 선언**하는 편이 안전하다.

---

## 빠른 점검 체크리스트

문제를 보면 아래 순서로 확인하면 된다.

1. `Application` 클래스의 package는 어디인가?
2. 문제가 난 Bean 클래스는 그 package의 하위인가, sibling인가?
3. `scanBasePackages` 또는 `scanBasePackageClasses`를 직접 건드렸는가?
4. 대상 클래스에 `@Component`, `@Service`, `@Repository`, `@Controller` 또는 `@Bean`이 있는가?
5. multi-module이라면 이 코드를 scan 대상으로 둘지, `@Import`/auto-configuration으로 가져올지 결정했는가?

이 다섯 개를 보면 component scan 문제의 대부분은 빠르게 좁혀진다.

## 고칠 때의 우선순위

실전에서는 아래 우선순위가 덜 꼬인다.

1. 메인 클래스를 공통 root package로 옮길 수 있으면 먼저 그렇게 한다.
2. root package를 공유하기 어렵다면 string package보다 `scanBasePackageClasses`를 쓴다.
3. 재사용 module이면 broad scan 대신 `@Import`나 auto-configuration으로 계약을 명시한다.
4. plain class 주입 문제는 stereotype annotation 또는 `@Bean` 등록으로 해결한다.

핵심은 "어떻게든 scan되게 만들기"보다, **왜 이 Bean이 이 애플리케이션에서 관리되어야 하는지 구조를 드러내는 것**이다.

## 꼬리질문

> Q: `@SpringBootApplication`이 붙어 있는데도 왜 다른 module의 Bean이 안 잡히는가?
> 의도: package boundary와 module boundary를 분리해서 이해하는지 확인
> 핵심: dependency가 있어도 기본 scan은 `Application` package와 하위만 본다.

> Q: multi-module이면 `scanBasePackages`를 크게 열어 두는 것이 항상 좋은가?
> 의도: broad scan과 explicit import의 trade-off 확인
> 핵심: reusable module은 `@Import`/auto-configuration이 더 명확할 수 있다.

> Q: class가 같은 package에 있는데도 주입이 안 되는 가장 흔한 이유는 무엇인가?
> 의도: stereotype annotation 누락 확인
> 핵심: package 안에 있어도 Bean 후보 annotation이나 `@Bean` 등록이 없으면 scan되지 않는다.

## 한 줄 정리

component scan 문서는 `package 경계와 annotation이 틀린 경우`를 다루고, package/annotation은 맞는데 환경마다 bean이 사라지면 `@Profile`/conditional 분기 문서로 먼저 넘어가는 것이 빠르다.
