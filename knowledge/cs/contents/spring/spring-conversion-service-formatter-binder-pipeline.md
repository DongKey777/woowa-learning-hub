# Spring ConversionService, Formatter, and Binder Pipeline

> 한 줄 요약: Spring의 타입 변환은 `ConversionService`, `Formatter`, `WebDataBinder`가 이어지는 파이프라인이며, 바인딩 오류의 원인을 정확히 나누려면 이 세 층을 구분해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)

retrieval-anchor-keywords: ConversionService, Formatter, WebDataBinder, type conversion, binding pipeline, PropertyEditor, data binding, format annotation, conversion error

## 핵심 개념

Spring MVC에서 문자열은 자바 객체로 바로 들어오지 않는다.

먼저 변환이 있고, 그 다음 바인딩이 있다.

- ConversionService: 타입 간 변환 엔진
- Formatter: 문자열 표현과 객체 표현 변환
- WebDataBinder: 웹 요청 데이터를 객체에 바인딩

이 세 단계가 섞이면 "왜 400이 났는지"가 흐려진다.

## 깊이 들어가기

### 1. ConversionService는 타입 변환의 중심이다

`String -> Integer`, `String -> LocalDate`, `String -> Enum` 같은 변환이 여기서 이뤄진다.

```java
@Component
public class StringToMoneyConverter implements Converter<String, Money> {
    @Override
    public Money convert(String source) {
        return Money.parse(source);
    }
}
```

이건 단순 문자열 포맷이 아니라 타입 변환 계약이다.

### 2. Formatter는 사용자 친화적 표기를 다룬다

Formatter는 주로 표시용 문자열과 객체 간 왕복 변환에 맞는다.

```java
public class LocalDateFormatter implements Formatter<LocalDate> {
    @Override
    public LocalDate parse(String text, Locale locale) {
        return LocalDate.parse(text);
    }

    @Override
    public String print(LocalDate object, Locale locale) {
        return object.toString();
    }
}
```

표시 형식과 입력 형식이 같은 경우에 특히 유용하다.

### 3. WebDataBinder가 요청 바인딩을 담당한다

웹 요청의 query string, form data, path variable을 객체 필드에 묶는다.

```java
@InitBinder
public void initBinder(WebDataBinder binder) {
    binder.addCustomFormatter(new LocalDateFormatter());
}
```

이 단계에서 필드명, 타입, format이 맞지 않으면 binding error가 난다.

### 4. PropertyEditor는 오래된 경로다

예전 방식의 변환 경로도 있지만, 지금은 `Converter`/`Formatter`를 중심으로 보는 것이 낫다.

레거시와 호환할 때만 의미가 커진다.

### 5. 바인딩 실패와 validation 실패는 다르다

- 바인딩 실패: 타입/형식이 안 맞음
- validation 실패: 변환은 됐지만 규칙을 어김

이 구분이 흐리면 에러 응답을 잘못 설계한다.

## 실전 시나리오

### 시나리오 1: 날짜 포맷 때문에 400이 난다

```java
@GetMapping("/orders")
public List<OrderResponse> search(@RequestParam LocalDate from) {
    ...
}
```

이 경우 `ConversionService`가 날짜 문자열을 못 바꾸면 binding error가 난다.

### 시나리오 2: `@DateTimeFormat`은 먹는데 JSON에서는 다르게 보인다

웹 요청 바인딩과 JSON 직렬화는 서로 다른 계층일 수 있다.

- form/query binding
- HttpMessageConverter
- Jackson serialization

### 시나리오 3: 커스텀 타입을 도입했더니 여기저기에서 깨진다

이럴 때는 Converter를 등록하고, 가능하면 공통 format policy를 둬야 한다.

### 시나리오 4: 컨트롤러 파라미터는 바뀌었는데 검증 에러만 나온다

바인딩과 검증 중 어느 단계에서 실패했는지 먼저 봐야 한다.

## 코드로 보기

### Converter

```java
@Component
public class StringToUserIdConverter implements Converter<String, UserId> {
    @Override
    public UserId convert(String source) {
        return new UserId(Long.parseLong(source));
    }
}
```

### Formatter

```java
@Component
public class MoneyFormatter implements Formatter<Money> {
    @Override
    public Money parse(String text, Locale locale) {
        return Money.parse(text);
    }

    @Override
    public String print(Money object, Locale locale) {
        return object.toString();
    }
}
```

### binder 등록

```java
@ControllerAdvice
public class GlobalBindingConfig {

    @InitBinder
    public void configure(WebDataBinder binder) {
        binder.addCustomFormatter(new MoneyFormatter());
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `Converter` | 타입 변환이 명확하다 | 표시 형식 표현은 약하다 | DTO/도메인 타입 변환 |
| `Formatter` | 사람 친화적 포맷에 좋다 | 타입 계약이 흐려질 수 있다 | 날짜/금액/표시 문자열 |
| `WebDataBinder` | 요청 바인딩에 자연스럽다 | 잘못 쓰면 전역 영향이 크다 | MVC 입력 처리 |
| `PropertyEditor` | 레거시 호환이 된다 | 현대적 대안보다 무겁다 | 오래된 코드 유지보수 |

핵심은 "어디서 변환하는가"보다 **어떤 의미의 변환인지**다.

## 꼬리질문

> Q: `ConversionService`와 `Formatter`의 차이는 무엇인가?
> 의도: 타입 변환과 사용자 포맷 구분 확인
> 핵심: ConversionService는 일반 변환, Formatter는 문자열 표현 중심이다.

> Q: 바인딩 오류와 validation 오류는 어떻게 다른가?
> 의도: 파이프라인 구분 확인
> 핵심: 바인딩은 변환 실패, validation은 규칙 위반이다.

> Q: `WebDataBinder`는 언제 쓰이는가?
> 의도: MVC 입력 경로 이해 확인
> 핵심: 웹 요청 데이터를 객체에 묶을 때 사용한다.

> Q: 커스텀 타입이 여러 엔드포인트에서 깨질 때 먼저 볼 것은 무엇인가?
> 의도: 변환 경로 진단 확인
> 핵심: Converter/Formatter 등록과 적용 범위를 먼저 본다.

## 한 줄 정리

Spring의 입력 변환은 ConversionService, Formatter, WebDataBinder가 이어진 파이프라인이므로 변환과 바인딩 실패를 분리해서 봐야 한다.
