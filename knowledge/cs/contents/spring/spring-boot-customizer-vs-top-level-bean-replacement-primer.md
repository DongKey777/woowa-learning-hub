# Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `RestClient.Builder`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까

> 한 줄 요약: Boot가 이미 조립해 주는 상위 bean은 "옵션 몇 개 추가"면 customizer bean으로 다루고, 생성 책임과 기본 계약 자체를 바꾸려 할 때만 top-level bean 교체로 올라간다. 이 규칙은 `RestClient.Builder`와 `WebClient.Builder`에 거의 같은 모양으로 적용된다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `ObjectMapper`, `RestClient.Builder`, `WebClient.Builder` 같은 Boot 상위 bean을 건드릴 때 customizer와 bean 교체를 섞어 쓰는 오해를 분리하는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:
- [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)
- [Spring Boot 설정 3단계 입문: properties -> customizer -> bean replacement](./spring-boot-properties-vs-customizer-vs-bean-replacement-primer.md)
- [Spring `RestClient.Builder` 입문 브리지: `RestClientCustomizer`, 전용 `RestClient` bean, builder 교체는 언제 고르나](./spring-restclient-builder-customizer-vs-dedicated-client-vs-builder-replacement-primer.md)
- [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
- [Timeout types: connect/read/write](../network/timeout-types-connect-read-write.md)

retrieval-anchor-keywords: boot customizer vs replace, builder vs template, resttemplatebuilder vs webclient builder, 언제 커스터마이징하는지, 처음 배우는데 webclient builder, webclient builder customizer, restclient builder customizer, customizer keeps boot defaults, top-level bean replacement ownership, shared builder owner, 공용 baseline vs 전용 client, 헤더 하나만 추가하고 싶어요

## 먼저 mental model

초반에는 Boot가 만드는 상위 bean을 이렇게 보면 된다.

- customizer bean: **Boot가 만든 기본 조립은 유지하고 옵션만 덧칠한다**
- top-level bean 교체: **Boot 기본 조립을 내려놓고 내가 직접 만들 책임을 가진다**

즉, 질문은 "`ObjectMapper`를 바꾸고 싶다"가 아니라 아래 순서가 된다.

```text
1. 기본 조립은 그대로 두고 옵션만 조금 바꾸고 싶은가?
   -> customizer bean

2. 공용 기본값은 유지하고 특정 클라이언트 하나만 다르게 만들고 싶은가?
   -> Boot가 준 builder를 받아 별도 client bean 생성

3. 생성 방식, 기본 구현, connector, lifecycle까지 내가 직접 책임질 건가?
   -> top-level bean 교체
```

이 순서를 놓치면 "옵션 하나 바꾸려다 Boot 기본값 전체를 잃는" 일이 생긴다.

특히 HTTP 클라이언트는 아래처럼 한 묶음으로 보면 덜 헷갈린다.

| 보는 대상 | 먼저 떠올릴 질문 | 보통의 첫 선택 |
|---|---|---|
| `RestClient.Builder` | 동기 HTTP 호출의 공용 기본값만 얹는가? | `RestClientCustomizer` |
| `WebClient.Builder` | 비동기/reactive HTTP 호출의 공용 기본값만 얹는가? | `WebClientCustomizer` |
| 둘 다 공통 | 특정 downstream 하나만 별도 인증/base URL이 필요한가? | Boot-managed builder를 주입받아 전용 client bean 생성 |

즉 `RestClient.Builder`는 "`WebClient.Builder`의 동기 버전 cousin"처럼 보면 된다. 실행 모델은 다르지만, **"공용 baseline은 customizer, 특정 client는 builder로 개별 생성, owner 교체는 마지막"** 이라는 선택 규칙은 거의 같다.

---

## 왜 customizer가 더 안전한지 30초 체감

아래 before/after를 먼저 보면 감각이 빨리 온다.

| 보고 싶은 변화 | before: top-level bean 교체 | after: customizer | 왜 after가 더 안전한가 |
|---|---|---|---|
| JSON에서 unknown field 무시 | `@Bean ObjectMapper` 직접 생성 | `Jackson2ObjectMapperBuilderCustomizer` | Boot의 기본 JSON 조립 흐름을 유지한 채 옵션만 얹는다 |
| 모든 outbound HTTP 호출에 공통 헤더 추가 | `@Bean WebClient.Builder` 직접 생성 | `WebClientCustomizer` | shared builder owner를 바꾸지 않고 공용 baseline만 추가한다 |

핵심은 "after가 더 많은 일을 한다"가 아니라 **"after가 덜 건드린다"**는 점이다.

- before: Boot가 해주던 기본 조립을 내가 이어받아야 한다
- after: Boot 기본 조립은 그대로 두고, 내가 바꾸려는 한 조각만 올린다

### before / after 1: `ObjectMapper`

before 쪽은 `FAIL_ON_UNKNOWN_PROPERTIES` 하나만 바꾸는 것처럼 보여도, 실제로는 `ObjectMapper` owner를 통째로 가져온다.

```java
// before: 옵션 하나를 위해 ObjectMapper 생성 책임까지 가져온다
@Configuration
public class JsonConfig {

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper()
            .findAndRegisterModules()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    }
}
```

```java
// after: Boot가 만들 흐름은 유지하고 옵션만 추가한다
@Configuration
public class JsonConfig {

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jsonCustomizer() {
        return builder -> builder.featuresToDisable(
            DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES
        );
    }
}
```

초보자 기준으로 after가 안전한 이유는 단순하다.

- 바꾸려는 의도는 "역직렬화 옵션 하나 조정"이다
- 그런데 before는 "JSON 기본 조립 owner 변경"까지 같이 해버린다
- after는 의도와 변경 범위가 더 잘 맞는다

## builder에서 바로 보는 before / after
공통 헤더 하나를 추가하려는 장면도 구조는 같다.

```java
// before: 헤더 하나를 위해 shared builder owner를 교체한다
@Configuration
public class HttpClientConfig {

    @Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder()
            .defaultHeader("X-App-Name", "order-api");
    }
}
```

```java
// after: shared builder는 유지하고 공용 기본 헤더만 추가한다
@Configuration
public class HttpClientConfig {

    @Bean
    public WebClientCustomizer outboundDefaults() {
        return builder -> builder.defaultHeader("X-App-Name", "order-api");
    }
}
```

여기서도 after가 더 안전한 이유는 같다.

- 하고 싶은 일: 앱 공용 헤더 하나 추가
- before가 실제로 하는 일: shared builder 생성 책임 교체
- after가 실제로 하는 일: shared builder에 공용 옵션 추가

처음 읽을 때는 이 문장 하나만 기억해도 충분하다.

**"원하는 변화보다 더 큰 책임이 따라오면 before, 원하는 변화 크기와 책임이 맞으면 after"**

---

## 한눈에 결정표

| 상황 | 먼저 고를 것 | 이유 |
|---|---|---|
| JSON feature, naming, module 등록 같은 전역 기본값 미세 조정 | `Jackson2ObjectMapperBuilderCustomizer` | Boot가 조립한 `ObjectMapper` 흐름을 유지한다 |
| 공용 `RestClient` 기본 헤더, interceptor, timeout baseline 추가 | `RestClientCustomizer` | Boot가 준비한 shared `RestClient.Builder`를 유지한다 |
| 공용 `WebClient` 기본 헤더, filter, timeout baseline 추가 | `WebClientCustomizer` | Boot가 준비한 shared `WebClient.Builder`를 유지한다 |
| 특정 downstream 하나만 다른 base URL, auth, interceptor가 필요 | Boot-managed `RestClient.Builder`를 주입받아 별도 `RestClient` bean 생성 | 동기 client 하나만 따로 조립하고 공용 builder는 유지한다 |
| 특정 downstream 하나만 다른 base URL, auth, filter가 필요 | Boot-managed `WebClient.Builder`를 주입받아 별도 `WebClient` bean 생성 | 전역 builder를 불필요하게 갈아끼우지 않는다 |
| Boot 기본 조립을 버리고 생성 책임 전체를 직접 가져가겠다 | top-level bean 직접 등록 | back-off 이후의 기본 계약을 내가 책임진다 |

초보자용 규칙은 간단하다.

**"옵션 추가"면 customizer, "생성 책임 인수"면 교체**다.

---

## 1. `ObjectMapper`: 옵션 한두 개면 customizer가 먼저다

아래 코드는 얼핏 보면 JSON 옵션 하나만 바꾸는 것처럼 보인다.

```java
@Configuration
public class JsonConfig {

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper()
            .findAndRegisterModules()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    }
}
```

하지만 의미는 "옵션 추가"보다 크다.

- `ObjectMapper` 생성 책임을 내가 가져온다
- Boot auto-configuration의 기본 `ObjectMapper`는 back off될 수 있다
- 나중에 붙는 Boot/Jackson customizer 흐름과 멀어질 수 있다

여기서 말하는 back-off는 [자동 구성 기초](./spring-boot-autoconfiguration-basics.md)에서 본 `@ConditionalOnMissingBean`의 그대로다. 즉 "이미 같은 타입 bean이 있으면 Boot 기본 조립이 물러난다"가 `ObjectMapper` 교체 장면에 나타난 것이다.

그래서 원하는 것이 "Boot 기본 JSON 조립은 유지하고 feature 몇 개만 바꾸기"라면 보통 customizer가 더 맞다.

```java
@Configuration
public class JsonConfig {

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jsonCustomizer() {
        return builder -> builder.featuresToDisable(
            DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES
        );
    }
}
```

이 코드는 이렇게 읽으면 된다.

- `ObjectMapper`는 여전히 Boot 쪽 생성 흐름이 만든다
- 나는 builder 옵션 한두 개만 추가한다
- 그래서 기본 module/설정 조립을 유지하기 쉽다

### 언제 `ObjectMapper` 직접 교체가 맞나

아래처럼 **기본 조립 자체를 바꾸려는 의도**가 분명할 때다.

- 앱 전역 JSON baseline을 Boot 기본값이 아니라 내 순수 `ObjectMapper` 규칙으로 통일하겠다
- 서로 다른 목적의 `ObjectMapper`를 여러 개 두고 `@Qualifier`로 명시적으로 나누겠다
- 특정 라이브러리 요구 때문에 Boot 기본 조립을 일부러 피하겠다

핵심은 "`ObjectMapper`를 하나 만든다"가 아니라 **"Boot 기본 조립의 owner를 내가 가져간다"**는 점이다.

---

## 2. `RestClient.Builder`: `WebClient.Builder`와 같은 규칙을 동기 호출에도 적용한다

초급자가 `WebClient.Builder` 쪽 mental model은 잡았는데 `RestClient.Builder`에서 다시 흔들리는 이유는 "동기라서 규칙도 다를 것 같다"는 착각 때문이다.

하지만 Boot customization 선택 규칙은 거의 같다.

```java
@Configuration
public class SyncHttpClientConfig {

    @Bean
    public RestClientCustomizer restClientDefaults() {
        return builder -> builder.defaultHeader("X-App-Name", "order-api");
    }
}
```

이 코드는 이렇게 읽으면 된다.

- Boot가 만드는 shared `RestClient.Builder`는 그대로 둔다
- 나는 공용 헤더, interceptor, timeout 같은 baseline만 덧칠한다
- 그래서 다른 동기 outbound client도 같은 공용 규칙을 자연스럽게 공유한다

### 특정 downstream 하나만 다르게 만들고 싶다면

이때도 shared builder를 교체하지 않고 전용 client bean을 만든다.

```java
@Configuration
public class BillingApiConfig {

    @Bean
    public RestClient billingApiRestClient(RestClient.Builder builder) {
        return builder
            .baseUrl("https://billing.example.com")
            .defaultHeader("Authorization", "Bearer sample-token")
            .build();
    }
}
```

초보자 기준으로 중요한 구분은 아래다.

- **앱 공용 baseline 변경**: `RestClientCustomizer`
- **특정 파트너 API 하나만 별도 설정**: `RestClient.Builder`를 주입받아 전용 `RestClient` 생성
- **공용 builder 자체를 새로 설계**: top-level `RestClient.Builder` 교체

## restclient와 webclient builder를 같은 축으로 보는 이유

| 질문 | `RestClient.Builder` | `WebClient.Builder` |
|---|---|---|
| 공용 기본 헤더/인증/filter류를 얹고 싶은가? | `RestClientCustomizer` | `WebClientCustomizer` |
| 특정 client 하나만 따로 만들고 싶은가? | 주입받은 builder로 전용 `RestClient` 생성 | 주입받은 builder로 전용 `WebClient` 생성 |
| shared builder owner를 바꾸는가? | top-level `RestClient.Builder` 직접 등록 | top-level `WebClient.Builder` 직접 등록 |

차이는 builder 선택 규칙보다 **실행 모델**에 있다.

- `RestClient`: 동기 호출, interceptor 중심 사고가 자연스럽다
- `WebClient`: reactive 호출, filter/reactor context까지 함께 본다

즉 customization 입문에서는 둘을 먼저 같은 축으로 묶고, lifecycle 차이는 관련 문서로 넘기는 편이 beginner에게 더 안전하다.

---

## 3. `WebClient.Builder`: 공용 기본값이면 customizer, 특정 클라이언트면 별도 bean

아래도 초보자가 자주 하는 전역 교체다.

```java
@Configuration
public class HttpClientConfig {

    @Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder()
            .defaultHeader("X-App-Name", "order-api");
    }
}
```

이 코드의 실제 의미는 "헤더 하나 추가"가 아니라 공용 builder owner를 바꾸는 것이다.

- Boot가 준비하던 shared `WebClient.Builder`가 back off될 수 있다
- 공용 builder에 붙던 customizer/관측/기본 설정 흐름을 내가 직접 챙겨야 할 수 있다
- 앱 안의 다른 outbound client까지 예상보다 넓게 영향을 줄 수 있다

전역 기본 헤더나 filter를 추가하는 정도면 보통 `WebClientCustomizer`가 더 맞다.

```java
@Configuration
public class HttpClientConfig {

    @Bean
    public WebClientCustomizer outboundDefaults() {
        return builder -> builder.defaultHeader("X-App-Name", "order-api");
    }
}
```

### 특정 downstream 하나만 다르게 만들고 싶다면

이때는 shared builder를 교체하지 말고, Boot가 준 builder를 받아 전용 client를 만든다.

```java
@Configuration
public class PartnerApiConfig {

    @Bean
    public WebClient partnerApiWebClient(WebClient.Builder builder) {
        return builder
            .baseUrl("https://partner.example.com")
            .defaultHeader("Authorization", "Bearer sample-token")
            .build();
    }
}
```

초보자 기준으로 이 분기가 중요하다.

- **앱 공용 baseline 변경**: `WebClientCustomizer`
- **특정 파트너 API 하나만 별도 설정**: `WebClient.Builder`를 주입받아 전용 `WebClient` 생성
- **공용 builder 자체를 새로 설계**: top-level `WebClient.Builder` 교체

---

## 4. 자주 헷갈리는 오해

| 헷갈리는 말 | 맞는 해석 |
|---|---|
| "`@Primary ObjectMapper`를 만들면 Boot 기본 `ObjectMapper`도 살아 있고 내 것만 우선 선택된다" | 많은 경우 Boot 기본 bean은 `@ConditionalOnMissingBean` 때문에 먼저 back off될 수 있다. `@Primary`는 등록 후 후보 선택 문제다. |
| "`RestClient.Builder` bean 하나 만들면 timeout만 하나 더 붙는 거다" | 아니다. 공용 builder owner를 바꾸는 것이다. timeout 하나를 얹고 싶다면 먼저 `RestClientCustomizer`를 본다. |
| "`WebClient.Builder` bean 하나 만들면 헤더만 하나 더 붙는 거다" | 아니다. 공용 builder owner를 바꾸는 것이고, 전역 영향 범위가 더 크다. |
| "customizer는 약하고 bean 교체가 진짜 커스터마이징이다" | 아니다. Boot 환경에서는 customizer가 오히려 "기본 조립 유지 + 의도된 옵션 추가"라는 더 안전한 기본 경로다. |
| "`RestClient`와 `WebClient`는 실행 모델이 다르니 customizer 선택 규칙도 완전히 다를 것이다" | 아니다. builder customization의 초반 의사결정은 거의 같다. 차이는 요청 실행과 관측 방식에서 커진다. |
| "한 서비스만 다르게 쓰고 싶으면 shared builder를 바꿔야 한다" | 아니다. shared builder를 주입받아 전용 `RestClient` 또는 `WebClient` bean을 만들면 된다. |

### 초보자가 자주 놓치는 한 줄 판별

- "헤더 하나만"이라고 말하지만 `@Bean WebClient.Builder`를 만들었다면 실제로는 shared builder owner를 교체한 것이다
- "옵션 하나만"이라고 말하지만 `@Bean ObjectMapper`를 만들었다면 실제로는 Boot JSON 조립 owner를 교체한 것이다
- 말로 설명한 의도보다 코드가 더 큰 책임을 지면, customizer로 한 단계 내려오는 편이 보통 안전하다

---

## 5. 빠른 체크 질문 세 개

아래 질문에 답하면 대부분 방향이 정리된다.

1. Boot 기본 조립을 유지하고 싶은가?
2. 변경 범위가 앱 공용 기본값인가, 특정 client 하나인가?
3. 생성 책임과 기본 계약까지 내가 직접 유지보수할 준비가 되었는가?

짧게 매핑하면 이렇다.

- 1번이 `예`면 customizer부터 본다
- 2번이 "특정 client 하나"면 Boot-managed builder로 전용 bean을 만든다
- 3번까지 `예`면 그때 top-level bean 교체를 고려한다

---

## 꼬리질문

> Q: `ObjectMapper` 설정 하나만 바꾸고 싶은데 `@Bean ObjectMapper`를 바로 만들면 안 되는가?
> 의도: 옵션 변경과 생성 책임 교체를 구분하는지 확인
> 핵심: 가능은 하지만 의미가 더 크다. Boot 기본 조립을 유지하고 싶다면 보통 `Jackson2ObjectMapperBuilderCustomizer`가 먼저다.

> Q: `WebClient.Builder`를 앱 하나에서 공용으로 조금만 바꾸고 싶다면?
> 의도: 공용 baseline 변경과 builder 교체를 구분하는지 확인
> 핵심: 보통 `WebClientCustomizer`가 먼저다. shared builder 전체를 새로 만들 필요는 없다.

> Q: `RestClient.Builder`도 `WebClient.Builder`와 같은 감각으로 보면 되는가?
> 의도: 동기/비동기 HTTP 클라이언트 customization의 공통 mental model을 잡는지 확인
> 핵심: 그렇다. 공용 baseline이면 customizer, 특정 client 하나면 builder 주입 후 개별 생성, owner 교체는 마지막이다.

> Q: 파트너 API 하나만 다른 base URL과 auth header가 필요하면?
> 의도: 공용 builder 교체와 전용 client 생성을 분리하는지 확인
> 핵심: Boot가 준 `RestClient.Builder` 또는 `WebClient.Builder`를 주입받아 전용 client bean을 만든다.

## 한 줄 정리

Spring Boot에서 `ObjectMapper`, `RestClient.Builder`, `WebClient.Builder` 같은 상위 bean은 "기본 조립 위에 옵션 추가"면 customizer로 끝내고, Boot 기본 계약의 owner가 되려 할 때만 top-level bean 교체로 올라가면 된다.
