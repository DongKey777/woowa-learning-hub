# Spring Boot 설정 3단계 입문: properties -> customizer -> bean replacement

> 한 줄 요약: Boot 설정을 바꿀 때는 먼저 `application.yml` 같은 **properties knob**를 찾고, 그다음 **customizer bean**으로 덧칠하고, 마지막에만 **top-level bean 교체**로 올라가면 된다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 Boot customization을 **세 단계 사다리**로 정리해, properties와 customizer와 full bean replacement를 초급자용 decision guide로 연결한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)
- [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `RestClient.Builder`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)
- [Spring `RestClient.Builder` 입문 브리지: `RestClientCustomizer`, 전용 `RestClient` bean, builder 교체는 언제 고르나](./spring-restclient-builder-customizer-vs-dedicated-client-vs-builder-replacement-primer.md)
- [Spring MVC Customizer Ladder 입문: `WebMvcConfigurer`로 덧붙이고, core MVC bean 교체는 마지막에 둔다](./spring-mvc-customizer-ladder-webmvcconfigurer-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring `@Value` vs `@ConfigurationProperties` 환경값 읽기 가이드](./spring-value-vs-configurationproperties-env-guide.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: spring boot properties vs customizer vs bean replacement, boot customization ladder beginner, application yml vs customizer vs replace bean, spring boot customization levels, properties first customizer second replacement last, boot config knob beginner, application properties vs bean customization, objectmapper property vs customizer vs replacement, restclientcustomizer vs property vs bean replacement, webmvcconfigurer vs property vs replace bean, conditionalonmissingbean back off customization ladder, beginner boot settings decision guide, boot override escalation, 언제 properties 쓰고 언제 customizer 쓰나요, 언제 bean replacement 하나요

## 먼저 mental model

처음에는 Boot customization을 아래 3단계로 보면 된다.

```text
1. Boot가 이미 열어둔 설정 손잡이(knob)가 있는가?
   -> properties

2. knob는 없지만, Boot가 만든 기본 조립은 유지한 채 한 조각만 덧칠하면 되는가?
   -> customizer bean / 좁은 확장 포인트

3. 기본 조립 owner 자체를 내가 가져와야 하는가?
   -> top-level bean replacement
```

짧게 말하면 이렇다.

- properties: **Boot가 준비한 메뉴판 안에서 값만 고른다**
- customizer: **Boot가 만든 기본 조립은 유지하고 규칙 한 조각을 덧붙인다**
- bean replacement: **기본 조립을 내려놓고 내가 직접 만든다**

초급자 기준 기본 규칙은 한 줄이면 충분하다.

**값만 바꾸면 되면 properties, 훅 하나면 customizer, owner를 바꾸면 replacement**다.

## 한눈에 결정표

| 지금 하고 싶은 일 | 먼저 고를 것 | 왜 이 단계가 먼저인가 |
|---|---|---|
| 파일 업로드 최대 크기, 포트, 기본 timeout 같은 Boot 공개 설정값 조정 | properties | Boot가 이미 안전한 knob를 열어뒀다 |
| `ObjectMapper` feature 하나, 공용 HTTP 헤더 하나, MVC interceptor 하나 추가 | customizer bean / 확장 포인트 | 기본 조립은 유지하고 필요한 부분만 덧칠한다 |
| Boot 기본 builder/bean 생성 책임 자체를 직접 통제 | top-level bean replacement | 더 이상 값 조정이나 훅 추가가 아니라 owner 변경이다 |

이 표를 볼 때 중요한 점은 "무조건 세 단계가 모두 존재한다"가 아니라는 것이다.

- 어떤 기능은 properties까지만 있기도 한다
- 어떤 기능은 properties는 없고 customizer부터 시작한다
- replacement는 거의 항상 마지막 단계다

## 1. 먼저 properties를 찾는다

Boot는 자주 쓰는 조정 지점을 properties로 먼저 열어둔다.

예를 들어 이런 장면은 대개 bean 교체가 아니라 properties 문제다.

```yaml
server:
  port: 8081
  compression:
    enabled: true

spring:
  servlet:
    multipart:
      max-file-size: 10MB
  mvc:
    async:
      request-timeout: 3s
```

이 단계는 이렇게 읽으면 된다.

- Boot가 이미 "여긴 자주 바꾸는 값"이라고 공개해 둔 영역이다
- 개발자는 조립 코드를 새로 쓰지 않고 값만 선택한다
- framework upgrade나 기본 조립 변화와도 충돌할 가능성이 가장 낮다

즉 **같은 결과를 properties로 낼 수 있다면 보통 그 경로가 가장 싸고 안전하다.**

## 2. properties가 없으면 customizer를 본다

원하는 knob가 없더라도, 기본 조립 자체를 버릴 필요는 없는 경우가 많다.

예를 들어 JSON unknown field를 무시하고 싶다면 `ObjectMapper`를 직접 새로 만들기보다 customizer가 더 잘 맞는다.

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

모든 outbound 호출에 공통 헤더를 넣고 싶을 때도 비슷하다.

```java
@Configuration
public class OutboundConfig {

    @Bean
    public RestClientCustomizer outboundDefaults() {
        return builder -> builder.defaultHeader("X-App-Name", "order-api");
    }
}
```

MVC에서 인터셉터 하나를 추가하는 것도 같은 축이다.

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoggingInterceptor());
    }
}
```

이 단계의 공통점은 같다.

- Boot의 기본 bean/기본 파이프라인은 유지한다
- 원하는 동작 한 조각만 덧붙인다
- replacement보다 변경 책임이 작고 의도가 더 선명하다

## 3. bean replacement는 정말 owner를 가져갈 때만 쓴다

아래처럼 top-level bean을 직접 등록하면 의미가 커진다.

```java
@Configuration
public class HttpClientConfig {

    @Bean
    public RestClient.Builder restClientBuilder() {
        return RestClient.builder()
            .defaultHeader("X-App-Name", "order-api");
    }
}
```

겉으로는 "헤더 하나 추가"처럼 보여도 실제 의미는 다르다.

- Boot가 준비하던 shared builder 조립이 back off될 수 있다
- 기본 생성 책임과 이후 유지보수 책임이 내 코드로 올라온다
- 다른 사람은 "공용 기본값만 추가한 줄" 알고 있다가 더 큰 변경으로 오해할 수 있다

그래서 replacement는 아래 질문에 `예`일 때만 올라간다.

1. Boot가 제공하는 properties와 customizer로는 의도를 표현할 수 없는가?
2. 기본 조립 owner를 내가 직접 가져와야 하는가?
3. 그에 따른 테스트/업그레이드 책임도 감수할 것인가?

셋 중 앞의 두 질문이 모호하면 아직 replacement 단계가 아닐 가능성이 크다.

## 자주 헷갈리는 장면

| 장면 | 더 맞는 선택 | 이유 |
|---|---|---|
| 업로드 최대 크기만 바꾸고 싶다 | properties | 이미 공개된 Boot knob다 |
| JSON 직렬화/역직렬화 feature 몇 개만 바꾸고 싶다 | `Jackson2ObjectMapperBuilderCustomizer` | `ObjectMapper` owner 교체까지 갈 필요가 없다 |
| 모든 HTTP 호출에 공통 헤더/timeout baseline을 추가하고 싶다 | `RestClientCustomizer` 또는 `WebClientCustomizer` | 공용 builder는 유지하고 기본값만 덧칠하면 된다 |
| MVC 요청 전후에 공통 로깅을 넣고 싶다 | `WebMvcConfigurer` | 요청 엔진 교체가 아니라 파이프라인 훅 추가다 |
| Boot 기본 builder 생성 방식 자체를 사내 규칙으로 통제하고 싶다 | top-level bean replacement | 이제는 owner 변경 문제다 |

## 흔한 오해 4개

- "`application.yml`로 못 찾겠으니 바로 bean을 새로 만들자"는 점프가 자주 나온다. 보통은 properties 다음에 customizer를 한 번 더 본다.
- "customizer는 약하고 bean replacement가 진짜 커스터마이징이다"라고 생각하기 쉽다. 초급자 기준으로는 customizer가 더 안전한 기본 경로다.
- "bean 하나 등록했을 뿐"이라고 느끼기 쉽지만, top-level replacement는 `@ConditionalOnMissingBean` 때문에 Boot 기본 조립을 물러나게 만들 수 있다.
- 모든 기능에 properties, customizer, replacement가 다 있는 것은 아니다. 중요한 것은 **항상 가장 낮은 단계부터 확인하는 습관**이다.

## 30초 결정 질문

1. Boot가 이미 property로 열어둔 값인가?
2. 아니라면 기본 조립은 유지하고 옵션 한 조각만 덧붙이면 되는가?
3. 정말로 생성 책임과 기본 계약 자체를 바꿔야 하는가?

이 순서대로만 보면 과한 bean replacement를 많이 피할 수 있다.

## 다음에 어디로 이어지면 좋은가

- customizer와 bean replacement의 경계가 더 궁금하면 [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `RestClient.Builder`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)로 이어진다.
- HTTP 클라이언트 예시를 더 구체적으로 보고 싶다면 [Spring `RestClient.Builder` 입문 브리지: `RestClientCustomizer`, 전용 `RestClient` bean, builder 교체는 언제 고르나](./spring-restclient-builder-customizer-vs-dedicated-client-vs-builder-replacement-primer.md)를 본다.
- MVC 쪽 사다리를 보고 싶다면 [Spring MVC Customizer Ladder 입문: `WebMvcConfigurer`로 덧붙이고, core MVC bean 교체는 마지막에 둔다](./spring-mvc-customizer-ladder-webmvcconfigurer-primer.md)로 간다.

## 한 줄 정리

Boot customization은 "먼저 properties, 다음 customizer, 마지막 replacement" 순서로 올라가면 된다. 초보자에게 중요한 건 더 강한 방법을 빨리 쓰는 것이 아니라, **의도에 비해 가장 작은 책임의 도구를 고르는 것**이다.
