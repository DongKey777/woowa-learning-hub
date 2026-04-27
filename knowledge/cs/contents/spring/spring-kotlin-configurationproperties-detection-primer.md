# Kotlin `@ConfigurationProperties` 탐지 보조 노트: data class와 등록 포인트를 같이 찾는 법

> 한 줄 요약: Kotlin에서는 `data class`와 생성자 바인딩 문법 때문에 "`@ConfigurationProperties` 타입 정의"와 "실제 Bean 등록 포인트"가 떨어져 보이기 쉬우므로, 둘을 한 세트로 찾아야 한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)
> - [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
> - [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)

retrieval-anchor-keywords: kotlin configurationproperties detection primer, kotlin configurationproperties data class, kotlin constructor binding detection, configurationproperties registration point, configurationpropertiesscan enableconfigurationproperties kotlin, bean missing configurationproperties kotlin, grep configurationproperties kotlin, data class properties scan, constructor binding grep miss, beginner configurationproperties registration note, spring kotlin configurationproperties detection primer basics, spring kotlin configurationproperties detection primer beginner, spring kotlin configurationproperties detection primer intro, spring basics, beginner spring

## 먼저 mental model 한 줄

`@ConfigurationProperties`는 "설정 값을 담는 타입"이고, 별도로 **Spring이 그 타입을 Bean으로 등록하는 길**이 있어야 실제 주입이 된다.

초급자가 리뷰에서 놓치기 쉬운 이유는 이 두 정보가 Kotlin에서 자주 **다른 파일**에 나오기 때문이다.

## 먼저 찾을 두 가지

1. 설정 타입 정의
2. 그 타입을 Spring이 등록하는 포인트

이 둘 중 하나만 보면 "분명 annotation은 있는데 왜 주입이 안 되지?"라는 오해가 생긴다.

## 30초 비교표

| 보고 싶은 것 | Java에서 자주 보이는 모양 | Kotlin에서 grep이 놓치기 쉬운 모양 |
|---|---|---|
| 설정 타입 | `class ClientProperties { setter... }` | `data class ClientProperties(val baseUrl: URI)` |
| 생성자 바인딩 힌트 | `@ConstructorBinding`가 눈에 띔 | Boot 3에서는 single constructor면 annotation이 없어도 됨 |
| 등록 포인트 | `@EnableConfigurationProperties(X.class)` | `@EnableConfigurationProperties(X::class)` 또는 `@ConfigurationPropertiesScan` |
| Bean 방식 등록 | `@Bean @ConfigurationProperties ...` | `fun clientProperties() = ClientProperties(...)`와 헷갈리기 쉬움 |

핵심은 "`@ConstructorBinding`이 안 보이면 아닌가?"가 아니라, **"이 타입이 어디에서 등록되나?"**를 보는 것이다.

## Kotlin에서 자주 나오는 모양

### 1. 타입 정의는 data class인데 등록은 다른 곳에 있다

```kotlin
@ConfigurationProperties("app.client")
data class ClientProperties(
    val baseUrl: URI,
    val timeout: Duration,
)
```

이 코드만 보면 "설정 타입은 있다"까지는 알 수 있다.
하지만 이것만으로 Bean 등록이 끝난 것은 아니다.

등록 포인트는 보통 아래 둘 중 하나다.

```kotlin
@ConfigurationPropertiesScan
@SpringBootApplication
class Application
```

```kotlin
@Configuration
@EnableConfigurationProperties(ClientProperties::class)
class ClientConfig
```

## beginner 체크표: 무엇을 찾았으면 무엇을 더 봐야 하나

| 먼저 보인 것 | 다음에 바로 볼 것 | 흔한 오해 |
|---|---|---|
| `@ConfigurationProperties` data class | `@ConfigurationPropertiesScan` 또는 `@EnableConfigurationProperties` | annotation만 있으면 자동 등록된다고 생각함 |
| `@ConfigurationPropertiesScan` | 실제 prefix를 가진 타입이 같은 모듈/패키지 아래 있는지 | scan이 있는데도 타입 위치를 안 봄 |
| `@EnableConfigurationProperties(Foo::class)` | `Foo`가 진짜 `@ConfigurationProperties` 타입인지 | 그냥 일반 class도 등록된다고 착각함 |
| `@Bean @ConfigurationProperties` 메서드 | 반환 타입이 mutable인지, setter/var가 필요한지 | data class constructor binding과 같은 방식이라고 착각함 |

## grep이 놓치기 쉬운 포인트

### 1. `@ConstructorBinding`만 찾으면 Boot 3 Kotlin data class를 놓친다

예전 자료만 기억하고 아래만 찾으면:

```bash
rg -n --glob '*.{java,kt}' '@ConstructorBinding'
```

요즘 Kotlin 코드의 많은 경우를 놓친다.
single constructor `data class`는 annotation 없이도 constructor binding처럼 읽히기 때문이다.

그래서 첫 검색은 이렇게 넓게 시작하는 편이 안전하다.

```bash
rg -n --glob '*.kt' '@ConfigurationProperties'
```

그다음 등록 포인트를 따로 찾는다.

```bash
rg -n --glob '*.kt' '@ConfigurationPropertiesScan|@EnableConfigurationProperties'
```

### 2. setter나 `var`를 찾으면 immutable data class를 놓친다

Java mutable properties 습관으로 setter, `var`, no-arg 생성자만 찾으면 아래 같은 타입을 거의 다 빠뜨린다.

```kotlin
@ConfigurationProperties("app.mail")
data class MailProperties(
    val host: String,
    val port: Int,
)
```

이 타입은 `val`만 있어도 정상적인 바인딩 후보일 수 있다.

### 3. 타입 정의와 등록 포인트가 분리돼 있어 한 파일 grep으로 끝내기 어렵다

예를 들어 아래 둘은 같이 봐야 의미가 완성된다.

```kotlin
// properties/ClientProperties.kt
@ConfigurationProperties("app.client")
data class ClientProperties(
    val baseUrl: URI,
)
```

```kotlin
// Application.kt
@ConfigurationPropertiesScan
@SpringBootApplication
class Application
```

한 파일만 읽고 "등록이 안 보인다"라고 결론 내리면 오진하기 쉽다.

## 등록 포인트 3종을 먼저 구분하자

### 1. scan 방식

```kotlin
@ConfigurationPropertiesScan
@SpringBootApplication
class Application
```

- 초급자 해석: "이 패키지 아래의 `@ConfigurationProperties` 타입을 찾아 등록하라"
- 리뷰 포인트: 타입 위치가 scan 범위 안인가

### 2. 명시 등록 방식

```kotlin
@Configuration
@EnableConfigurationProperties(ClientProperties::class)
class ClientConfig
```

- 초급자 해석: "이 타입을 직접 등록하라"
- 리뷰 포인트: scan이 없어도 이 줄이 있으면 등록 근거가 있다

### 3. `@Bean` 메서드 방식

```kotlin
@Configuration
class MailConfig {

    @Bean
    @ConfigurationProperties("app.mail")
    fun mailProperties(): MailMutableProperties = MailMutableProperties()
}
```

- 초급자 해석: "메서드가 반환한 객체에 프로퍼티를 바인딩한다"
- 리뷰 포인트: 이 방식은 data class constructor binding mental model과 다를 수 있다

## 가장 흔한 혼동 4개

- `@ConfigurationProperties`가 타입에 붙어 있으면 자동으로 주입 가능하다고 생각한다.
- `@ConstructorBinding` annotation이 없으면 constructor binding이 아니라고 생각한다.
- Kotlin `data class`면 무조건 scan 없이도 등록된다고 생각한다.
- `@Bean @ConfigurationProperties`와 data class constructor binding을 같은 방식으로 이해한다.

## 리뷰에서 바로 쓰는 짧은 순서

1. `@ConfigurationProperties` 타입을 찾는다.
2. 그다음 `@ConfigurationPropertiesScan` / `@EnableConfigurationProperties` / `@Bean @ConfigurationProperties` 셋 중 무엇으로 등록되는지 찾는다.
3. Kotlin이면 `data class`와 `val`만 보고 "setter가 없어서 실패"라고 단정하지 않는다.
4. `@ConstructorBinding`이 없어도 Boot 버전과 single constructor 여부를 같이 본다.

## 한 줄 정리

Kotlin `@ConfigurationProperties`는 "`data class` 정의"만 찾으면 반만 본 것이다. 초급자 기준으로는 항상 **타입 정의 + 등록 포인트**를 한 세트로 찾는 것이 가장 안전하다.
