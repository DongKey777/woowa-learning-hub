# Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다

> 한 줄 요약: `@SpringBootApplication(scanBasePackages = ...)`로 component scan 범위를 넓혀도 JPA entity scan과 repository scan은 자동으로 따라오지 않으므로, multi-module에서 `@EntityScan`과 `@EnableJpaRepositories` 경계를 따로 맞추지 않으면 `Not a managed type`나 repository bean 누락이 바로 난다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 **JPA startup boundary troubleshooting primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)
- [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)

> 관련 문서:
> - [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
> - [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
> - [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)

retrieval-anchor-keywords: jpa scan boundary, entityscan, enablejparepositories, @entityscan 뭐예요, @enablejparepositories 뭐예요, entityscan enablejparepositories 차이, component scan vs entity scan, component scan이랑 entity scan 차이 헷갈려요, repository scan이 뭐예요, spring jpa scan 큰 그림, jpa scan 처음 배우는데, scanbasepackages no effect entity scan, not a managed type, repository bean not found, 처음 jpa scan 설정할 때 뭐부터 봐요

## 이 문서가 먼저 맞는 질문

아래처럼 "개념은 아직 큰 그림이 필요하고, 증상은 이미 보인다" 같은 첫 질문이면 이 문서가 먼저 맞다.

- "`@EntityScan`이 뭐예요?"
- "`@EnableJpaRepositories`는 언제 써요?"
- "`component scan`이랑 뭐가 달라요? 헷갈려요"
- "`scanBasePackages`를 넓혔는데 왜 `Not a managed type`가 나요?"
- "처음 배우는데 repository bean은 뜨는데 entity만 안 잡혀요"

반대로 "`JPA`가 뭐예요?", "`repository`가 왜 필요한가요?"처럼 더 앞단 개념이 먼저 막히면 [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)에서 접근 기술의 큰 그림을 먼저 잡고 돌아오는 편이 덜 헷갈린다.

## 이 문서 다음에 보면 좋은 문서

- stereotype bean 탐색 경계부터 다시 잡으려면 [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)으로 이어진다.
- shared module을 scan으로 붙일지 `@Import`나 auto-configuration으로 붙일지 판단하려면 [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)을 같이 본다.
- Boot가 기본 패키지와 auto-configuration을 어떻게 엮는지는 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)과 연결된다.
- startup은 통과했지만 영속성 컨텍스트 경계가 헷갈리면 [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)로 넘어간다.
- `@DataJpaTest`에서 JPA 경계 착시까지 보고 싶다면 [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)을 본다.

---

## 핵심 개념

초보자가 가장 자주 하는 오해는 이것이다.

- component scan
- entity scan
- repository scan

이 셋을 모두 "Spring이 알아서 찾는 한 번의 scan"으로 생각한다.

실제로는 서로 다른 탐색 경계다.

| 경계 | 찾는 대상 | 대표 설정 | 대표 증상 |
|---|---|---|---|
| component scan | `@Component`, `@Service`, `@Controller`, `@Configuration` 같은 stereotype bean | `@SpringBootApplication`, `@ComponentScan` | service/controller bean 누락, `NoSuchBeanDefinitionException` |
| entity scan | `@Entity`, `@Embeddable`, `@MappedSuperclass` | Boot 기본 패키지, `@EntityScan` | `Not a managed type`, entity metadata build 실패 |
| repository scan | `JpaRepository` 같은 Spring Data repository interface | Boot 기본 패키지, `@EnableJpaRepositories` | repository bean 누락, repository 주입 실패 |

즉 질문은 "`scanBasePackages`를 넓혔는데 왜 JPA가 안 되지?"가 아니라, **지금 깨진 것이 bean 발견인지, entity 등록인지, repository 등록인지 먼저 나누는 것**이다.

### 가장 중요한 함정 하나

`@SpringBootApplication(scanBasePackages = "...")`는 component scan alias일 뿐이다.

즉 아래를 자동으로 해 주지 않는다.

- `@Entity` 경계 확장
- Spring Data JPA repository 경계 확장

그래서 multi-module에서 흔히 이런 일이 생긴다.

1. controller/service는 잘 뜬다
2. 그런데 repository bean이 없다
3. 또는 repository는 떴는데 entity가 managed type이 아니다

이건 "scan이 절반만 맞은 상태"다.

---

## 먼저 이 그림으로 나눈다

```text
@SpringBootApplication / @ComponentScan
  -> stereotype bean 탐색

@EntityScan
  -> JPA entity 탐색

@EnableJpaRepositories
  -> Spring Data repository interface 탐색
```

셋 다 package 기반이지만, **같은 knob로 움직이지 않는다.**

Boot 기본값만 쓸 때는 메인 애플리케이션 클래스 package를 기준으로 비슷하게 보일 수 있다.
하지만 한 축만 커스터마이즈하는 순간 경계가 쉽게 어긋난다.

---

## 가장 흔한 실패 패턴

### 1. `scanBasePackages`만 넓히고 JPA도 같이 넓어진다고 생각한다

예를 들어 애플리케이션 클래스가 너무 깊은 package에 있다.

```text
com.example.app
  └── ApiApplication

com.example.order
  ├── application
  │   └── OrderQueryService
  └── persistence
      ├── entity
      │   └── OrderEntity
      └── repository
          └── OrderJpaRepository
```

이를 고치겠다고 아래처럼 component scan만 넓힌다.

```java
@SpringBootApplication(scanBasePackages = "com.example")
public class ApiApplication {
}
```

이러면 `OrderQueryService`는 잡힐 수 있다.
하지만 `OrderEntity`와 `OrderJpaRepository`는 여전히 별도 경계다.

대표 증상:

- `OrderJpaRepository` 주입 실패
- repository는 떴는데 `Not a managed type: class ...OrderEntity`

즉 **service가 잡힌 것과 JPA가 준비된 것은 다른 문제**다.

### 2. `@EntityScan`만 추가하고 repository도 같이 해결됐다고 생각한다

```java
@SpringBootApplication
@EntityScan(basePackageClasses = OrderEntityMarker.class)
public class ApiApplication {
}
```

이 설정은 entity scan만 고친다.

해결되는 것:

- `OrderEntity`가 managed type으로 등록됨

여전히 남는 것:

- repository interface discovery

즉 repository package가 기본 경계 밖이면 `@EnableJpaRepositories`를 따로 맞춰야 한다.

### 3. `@EnableJpaRepositories`만 추가하고 entity도 같이 따라온다고 생각한다

```java
@SpringBootApplication
@EnableJpaRepositories(basePackageClasses = OrderRepositoryMarker.class)
public class ApiApplication {
}
```

이 설정은 repository bean 등록만 고친다.

해결되는 것:

- `OrderJpaRepository` bean 생성

여전히 남는 것:

- repository가 참조하는 entity가 managed type인지 여부

즉 repository bean이 살아도 `EntityManagerFactory`가 해당 entity를 모르면 JPA는 여전히 깨진다.

## 가장 흔한 실패 패턴 (계속 2)

### 4. 별도 `JpaConfig`에 annotation을 옮기고, package 지정 없이 기본값에 기대 버린다

이 함정은 생각보다 많다.

```text
com.example.app
  ├── ApiApplication
  └── config.jpa
      └── JpaConfig

com.example.order.persistence.entity
com.example.order.persistence.repository
```

```java
@Configuration
@EntityScan
@EnableJpaRepositories
public class JpaConfig {
}
```

겉보기엔 "JPA 설정 전용 클래스로 분리했다"처럼 보인다.
하지만 package를 명시하지 않으면 annotation이 붙은 **그 설정 클래스 package** 기준으로 좁게 잡힐 수 있다.

즉 `com.example.app.config.jpa` 아래엔 entity/repository가 없어서, 오히려 기본값보다 더 좁아질 수 있다.

### 5. `@Entity`를 Spring bean처럼 생각한다

beginner가 자주 섞는 오해다.

- `@Entity`는 stereotype bean annotation이 아니다
- component scan이 `@Entity`를 service bean처럼 등록해 주지 않는다
- `@EntityScan`도 entity를 일반 Spring bean으로 등록하는 기능이 아니다

즉 entity는 **JPA 메타데이터 대상**이지, 보통 constructor injection 대상으로 쓰는 Spring bean이 아니다.

---

## 예외로 빠르게 분기하기

| 증상 | 먼저 의심할 경계 | 흔한 원인 |
|---|---|---|
| `NoSuchBeanDefinitionException: ...OrderService` | component scan | stereotype bean이 base package 밖에 있음 |
| `NoSuchBeanDefinitionException: ...OrderJpaRepository` | repository scan | repository interface가 기본 경계 밖에 있거나 `@EnableJpaRepositories`가 잘못 잡힘 |
| `Not a managed type: class ...OrderEntity` | entity scan | entity package가 기본 경계 밖에 있거나 `@EntityScan`이 잘못 잡힘 |
| startup은 되지만 entity class를 bean처럼 주입하려다 실패 | 개념 혼동 | `@Entity`를 component로 오해함 |

핵심은 exception 이름만 봐도 **bean 누락인지, JPA 메타데이터 누락인지**를 먼저 나눌 수 있다는 점이다.

---

## 왜 multi-module에서 특히 잘 터지나

multi-module은 module dependency와 package boundary가 자주 어긋난다.

- Gradle/Maven dependency가 있다
- classpath에는 클래스가 있다
- 그래서 "Spring도 다 찾겠지"라고 생각한다

하지만 Spring은 classpath 전체를 의미 기반으로 자동 분류하지 않는다.
각 scan 메커니즘이 **자기 package 경계 안에서만** 후보를 찾는다.

즉 multi-module의 핵심 오해는 다음 한 줄로 줄일 수 있다.

> 의존성 추가는 classpath 문제를 해결할 뿐이고, scan boundary 문제를 해결하지는 않는다.

---

## 고칠 때의 우선순위

### 1. 가능하면 package root부터 정리한다

애플리케이션 내부 모듈이라면 가장 단순한 해법은 메인 클래스와 JPA 관련 package가 공통 root 아래에 오게 만드는 것이다.

```text
com.example
  ├── ApiApplication
  └── order
      ├── application
      └── persistence
```

이 구조면 Boot 기본값만으로 끝나는 경우가 많다.

### 2. 공통 root를 맞추기 어렵다면 세 경계를 따로 선언한다

```java
@SpringBootApplication(scanBasePackageClasses = {
        ApiApplication.class,
        OrderApplicationMarker.class
})
@EntityScan(basePackageClasses = OrderEntityMarker.class)
@EnableJpaRepositories(basePackageClasses = OrderRepositoryMarker.class)
public class ApiApplication {
}
```

중요한 점:

- component scan marker
- entity marker
- repository marker

를 **같은 것으로 뭉뚱그리지 말고**, 실제 package ownership에 맞게 나누는 편이 안전하다.

### 3. string package보다 marker class를 우선한다

`basePackages = "com.example.order.persistence.entity"`보다 `basePackageClasses = OrderEntityMarker.class`가 refactor에 안전하다.

이유:

- package rename에 덜 취약하다
- 왜 이 package를 열었는지 코드에 남는다
- component/entity/repository 경계를 각각 분리해 두기 쉽다

### 4. JPA 설정을 분리하더라도 package를 명시적으로 적는다

전용 `JpaConfig`를 두는 것은 괜찮다.
하지만 아래처럼 **기본값에 기대는 분리**는 위험하다.

```java
@Configuration
@EntityScan
@EnableJpaRepositories
public class JpaConfig {
}
```

분리할수록 오히려 marker class나 base package를 더 명시하는 쪽이 안전하다.

---

## 추천 mental model

JPA multi-module startup 문제를 볼 때는 "scan이 왜 안 되지?" 대신 아래처럼 생각하면 덜 헷갈린다.

1. 이 클래스는 stereotype bean인가?
2. 이 클래스는 JPA entity metadata 대상인가?
3. 이 인터페이스는 Spring Data repository 후보인가?

셋은 서로 다른 질문이다.

그래서 아래 셋도 서로 다른 대답을 가진다.

- `@ComponentScan`
- `@EntityScan`
- `@EnableJpaRepositories`

한 annotation으로 셋을 동시에 해결하려고 하면 거의 항상 경계가 흐려진다.

## 꼬리질문

> Q: `@SpringBootApplication(scanBasePackages = "com.example")`를 추가했는데 왜 `Not a managed type`가 계속 날 수 있는가?
> 의도: component scan과 entity scan 분리 이해 확인
> 핵심: `scanBasePackages`는 stereotype bean 탐색만 넓히고 entity scan 경계는 바꾸지 않기 때문이다.

> Q: `@EntityScan`을 추가했는데 repository bean이 여전히 없는 이유는 무엇인가?
> 의도: entity scan과 repository scan 분리 이해 확인
> 핵심: repository interface discovery는 `@EnableJpaRepositories` 또는 Boot의 repository 기본 경계를 따르기 때문이다.

> Q: `JpaConfig`에 `@EntityScan`, `@EnableJpaRepositories`만 붙여 두고 package를 지정하지 않으면 왜 더 좁아질 수 있는가?
> 의도: annotation 기본 package 이해 확인
> 핵심: explicit package를 주지 않으면 annotation이 붙은 설정 클래스 package 기준으로 탐색할 수 있기 때문이다.

> Q: `@Entity`는 왜 component scan으로 바로 bean이 되지 않는가?
> 의도: entity와 bean 역할 분리 확인
> 핵심: `@Entity`는 JPA 메타데이터 annotation이지 stereotype bean annotation이 아니기 때문이다.

## 한 줄 정리

multi-module Spring Boot에서 JPA startup을 안정적으로 맞추려면 component scan, entity scan, repository scan을 하나의 "scan"으로 뭉개지 말고 세 개의 독립 경계로 나눠서 설정해야 한다.
