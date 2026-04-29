# Primitive-wrapper choice primer: `int`/`long`/`boolean` vs `Integer`/`Long`/`Boolean`

> 한 줄 요약: "`int`와 `Integer` 차이가 뭐예요?"라는 질문은 결국 "이 값이 항상 있어야 하나, 아니면 `null`도 상태인가?"를 묻는 것이고, 값이 반드시 있어야 하면 primitive를 먼저 보고 "비어 있음", "미입력", "선택값" 같은 상태를 표현해야 하면 wrapper를 검토하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- [Wrapper 값 비교 입문 브리지 (`Integer` / `Long` / `Boolean`)](./wrapper-value-comparison-beginner-bridge.md)
- [`Boolean`이 `null`일 수도 있을 때 조건문을 어떻게 읽을까 beginner bridge](./boolean-wrapper-null-condition-primer.md)
- [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)
- [Validation Boundary: Input vs Domain Invariant 미니 브리지](../../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: int integer 차이, 자바 int integer 차이, int integer 차이 뭐예요, int vs integer beginner, int 대신 integer 왜, integer null 왜 필요해요, int integer null 차이, primitive vs wrapper choice, primitive wrapper 언제 써요, wrapper 왜 써요, java 기본형 wrapper 처음, what is primitive wrapper, field parameter return type java, java field type basics

## `int` / `Integer` 차이로 바로 들어왔다면

이 문서는 "`int Integer 차이`", "`왜 `int` 대신 `Integer` 써요?`", "`primitive랑 wrapper 뭐가 달라요?`" 같은 검색 질문에 바로 답하는 beginner entrypoint다.

먼저 아래 세 줄만 잡으면 검색 의도 대부분이 풀린다.

| 검색에서 실제로 묻는 것 | 먼저 붙일 한 문장 | 바로 다음 문서 |
|---|---|---|
| "`int`와 `Integer`가 뭐가 달라요?" | primitive는 값이 항상 있고, wrapper는 `null`도 상태로 담을 수 있다 | 이 문서의 [한눈에 보기](#한눈에-보기) |
| "`왜 `Integer`를 써요?" | 미입력, 선택값, PATCH 같은 경계에서 `null` 의미를 보존하려고 쓴다 | [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md) |
| "`비교는 뭐가 달라요?" | 타입 선택 질문과 `==`/`equals()` 질문은 분리해서 본다 | [Wrapper 값 비교 입문 브리지 (`Integer` / `Long` / `Boolean`)](./wrapper-value-comparison-beginner-bridge.md) |

처음 고를 때는 "primitive가 더 저수준이고 wrapper가 더 객체지향적이다"처럼 어렵게 볼 필요가 없다.

학습자가 실제로는 이렇게 많이 묻는다.

- "`int`와 `Integer` 차이가 뭐예요?"
- "왜 `int` 대신 `Integer`를 써요?"
- "`Boolean`은 왜 `null`이 될 수 있어요?"

이 세 질문은 전부 같은 축으로 정리된다.
값이 항상 있어야 하면 primitive, 값이 비어 있을 수도 있으면 wrapper다.

먼저 질문을 하나만 던지면 된다.

- 이 값은 **반드시 있어야 하나?**
- 아니면 **없음/null/미입력**도 하나의 상태인가?

여기서 출발하면 대부분 정리된다.

- `int`, `long`, `boolean`은 값이 항상 있다
- `Integer`, `Long`, `Boolean`은 값이 없어서 `null`일 수도 있다

즉 beginner 기준 기본 규칙은 이렇다.

> "없을 수 없는 값"이면 primitive를 먼저, "없음도 의미"면 wrapper를 검토한다.

## 한눈에 보기

| 지금 만드는 자리 | 먼저 떠올릴 선택 | 왜 이렇게 고르나 |
|---|---|---|
| 도메인 필드가 항상 값이 있어야 함 | primitive | `null` 방어 없이 바로 읽고 계산하기 쉽다 |
| 요청 DTO 필드가 미입력일 수 있음 | wrapper | `null`로 "안 왔음"을 표현할 수 있다 |
| 메서드 파라미터가 필수 입력 | primitive | 호출자가 값을 꼭 넘겨야 한다는 의도가 선명하다 |
| 메서드 파라미터가 선택 입력 | wrapper 또는 별도 타입 | "값 없음"을 호출 경계에서 표현해야 한다 |
| 반환값이 항상 계산 가능 | primitive | 호출자가 바로 써도 된다 |
| 반환값이 없을 수도 있음 | wrapper보다 `Optional`/별도 타입 먼저 검토 | "없음" 의미를 더 직접 드러낼 수 있다 |

짧게 외우면 이렇다.

- 필수값이면 primitive 쪽이 기본값
- 선택값이면 wrapper 가능
- 반환값의 "없음"은 wrapper 하나로 밀기보다 `Optional`이나 상태 타입도 같이 본다

초보자가 update API에서 특히 헷갈리는 지점은 `Boolean` 요청 필드다.

| 요청 DTO의 `Boolean marketingConsent` | 초보자 해석 | 서버에서 먼저 정할 질문 |
|---|---|---|
| `true` | 동의로 바꿔 달라 | 바로 `true`로 반영할까 |
| `false` | 비동의로 바꿔 달라 | 바로 `false`로 반영할까 |
| `null` | 안 보냈다, 비웠다, 아직 모름 중 하나일 수 있다 | `변경 없음`인지, `명시적 비움`인지, 검증 에러인지 |

즉 wrapper를 쓰는 순간 "값이 없을 수 있다"에서 끝나지 않고, 그 없음이 update 계약에서 무슨 뜻인지까지 같이 정해야 한다.

## 필드에서 어떻게 고를까

필드에서는 "이 객체가 살아 있는 동안 값이 항상 있어야 하나?"를 먼저 본다.

즉 "`int` 대신 `Integer`를 왜 쓰나요?"라는 질문을 필드 문맥으로 바꾸면 아래 한 줄이 된다.

> 이 필드는 비어 있으면 안 되는가, 아니면 비어 있음 자체가 의미인가?

```java
public class Attendance {
    private final long sessionId;
    private boolean late;
}
```

이런 필드는 값이 비어 있으면 오히려 객체가 덜 완성된 느낌이다. `sessionId`, `late`가 항상 있어야 한다면 primitive가 더 자연스럽다.

반대로 입력 경계에서는 상황이 달라진다.

```java
public record UpdateAttendanceRequest(
    Long sessionId,
    Boolean late
) {}
```

여기서 wrapper를 쓸 이유는 "도메인에서 wrapper가 멋져서"가 아니다. 요청에 값이 안 들어올 수도 있기 때문이다.

초보자용 판단 기준은 아래 두 줄이면 충분하다.

- **도메인 내부에서 항상 존재해야 하는 필드**: primitive 우선
- **입력 경계에서 비어 있을 수 있는 필드**: wrapper 검토

PATCH나 부분 수정 API에서는 이 차이가 더 직접적으로 드러난다.

```java
public record UpdateNotificationRequest(Boolean enabled) {
}
```

이 DTO에서 `enabled`가 `Boolean`인 이유는 대개 "필드가 안 올 수도 있다"를 열어 두기 위해서다.
그래서 beginner가 보는 "`Boolean`은 왜 `null`이 되죠?"라는 질문도 사실은 "이 요청에서 미전달 상태를 살려야 하나?"라는 질문과 거의 같다.
하지만 beginner가 여기서 바로 자주 헷갈리는 질문은 이것이다.

- `null`이면 기존 값을 유지하나?
- `null`이면 기본값 `false`를 넣나?
- `null` 자체를 잘못된 요청으로 보나?

즉 wrapper를 DTO에 두는 일과, `null` 정책을 정하는 일은 같은 작업의 앞뒤다.

## 메서드 시그니처에서는 어떻게 고를까

메서드 파라미터와 반환값은 "호출자에게 어떤 약속을 주는가"를 보여 준다.

예를 들어:

```java
void changeLimit(int limit)
```

이 시그니처는 "`limit`는 꼭 있어야 한다"는 약속에 가깝다.

반면:

```java
void changeLimit(Integer limit)
```

이 시그니처는 호출자에게 "`null`도 넘길 수 있다"는 문을 열어 준다. 그러면 메서드 안에서는 `null`을 어떻게 읽을지 정책이 필요하다.

- 변경 안 함인가
- 기본값 사용인가
- 에러인가

반환값도 비슷하다.

```java
int size()
Long findManagerId()
```

`size()`는 항상 숫자가 있으니 primitive가 자연스럽다.
`findManagerId()`처럼 결과가 없을 수도 있는 질문은 wrapper가 가능하지만, beginner 단계에서도 "`없음`을 돌려준다"는 뜻이 중요하면 `Optional<Long>`이나 별도 결과 타입이 더 또렷할 수 있다.

즉 메서드 시그니처에서 wrapper를 쓰는 순간, 그 메서드는 `null` 의미까지 계약에 포함한다.

## 흔한 오해와 함정

- "wrapper가 객체니까 무조건 더 좋다"
  더 좋은 게 아니라 `null` 상태를 추가로 여는 선택이다.
- "primitive는 옛날 방식이고 wrapper가 최신 방식이다"
  아니다. 값이 항상 있어야 하는 자리에서는 primitive가 더 단순하고 선명하다.
- "반환값이 없을 수도 있으면 무조건 wrapper"
  가능은 하지만, 호출자에게 `null` 체크를 떠넘길 수 있다. `Optional`이나 상태 타입이 더 읽기 쉬운 경우가 많다.
- "`Boolean`도 불린이니까 `if (flag)`면 되겠지"
  `Boolean`은 `null`일 수 있어서 조건문에서 바로 쓰면 흔들린다.
- "DTO에서 wrapper를 썼으니 도메인 필드도 그대로 wrapper"
  입력 경계에서의 필요와 도메인 내부 모델의 필요는 다를 수 있다.

## 실무에서 쓰는 모습

가장 흔한 흐름은 "경계에서는 wrapper, 내부에서는 primitive나 더 명시적인 타입"이다.

```java
public record CreateCouponRequest(Boolean autoPublish) {
}

public final class Coupon {
    private final boolean autoPublish;

    public Coupon(Boolean autoPublish) {
        this.autoPublish = Boolean.TRUE.equals(autoPublish);
    }
}
```

이 예시에서 중요한 포인트는 세 가지다.

1. 요청에서는 `Boolean`으로 미입력을 받을 수 있다
2. 내부 필드에서는 정책을 정한 뒤 `boolean`으로 굳힌다
3. `null` 의미가 더 복잡해지면 `enum`이나 별도 타입으로 올린다

즉 "어디서 wrapper를 허용하고, 어디서 primitive로 확정할지" 경계를 나누는 감각이 중요하다.

update API만 떼어 놓고 보면 아래 순서로 읽으면 덜 흔들린다.

1. 요청 DTO의 `Boolean`은 우선 raw intent를 보존한다
2. 서비스에서 `null`을 `변경 없음`인지 `검증 에러`인지 먼저 정한다
3. 정책이 정해진 뒤에만 도메인 `boolean`이나 더 명시적인 상태 타입으로 바꾼다

예를 들어 "필드를 안 보내면 기존 값 유지" 계약이라면 이런 식으로 읽을 수 있다.

```java
public void updateMarketingConsent(User user, Boolean requested) {
    if (requested == null) {
        return;
    }
    user.changeMarketingConsent(requested);
}
```

반대로 `null`이 "아직 선택 안 함" 같은 별도 상태를 계속 품으면 `boolean`으로 바로 내리지 말고 `enum` 쪽으로 올리는 편이 더 선명하다.

## 더 깊이 가려면

- wrapper 값 비교가 먼저 헷갈리면 [Wrapper 값 비교 입문 브리지 (`Integer` / `Long` / `Boolean`)](./wrapper-value-comparison-beginner-bridge.md)
- `Boolean`의 `null` 조건문이 불안하면 [`Boolean`이 `null`일 수도 있을 때 조건문을 어떻게 읽을까 beginner bridge](./boolean-wrapper-null-condition-primer.md)
- DTO에서 missing / `null` / default가 어떻게 갈리는지 보려면 [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- `boolean`/`null`만으로 상태 설명이 길어지면 [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)
- 입력 검증과 도메인 규칙을 어디서 나눌지 보려면 [Validation Boundary: Input vs Domain Invariant 미니 브리지](../../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)

## 면접/시니어 질문 미리보기

Q. 필드에서 primitive를 기본값으로 두는 이유는 뭔가요?
A. 값이 항상 있어야 하는 모델이라면 `null` 상태를 열지 않고 더 단순한 계약을 만들 수 있기 때문이다.

Q. 그럼 wrapper는 언제 쓰나요?
A. 미입력, 선택값, nullable 경계를 표현해야 할 때 쓴다.

Q. 메서드 반환값이 없을 수도 있으면 wrapper면 충분한가요?
A. 충분할 때도 있지만, "없음" 의미를 분명히 드러내려면 `Optional`이나 별도 타입이 더 읽기 쉬울 수 있다.

Q. DTO와 도메인 필드 타입이 꼭 같아야 하나요?
A. 아니다. DTO는 입력 의도를 보존하고, 도메인은 내부 규칙에 맞게 더 단순하거나 더 명시적인 타입으로 바꿀 수 있다.

## 한 줄 정리

`int`/`long`/`boolean`은 "값이 반드시 있다"는 계약에, `Integer`/`Long`/`Boolean`은 "`null`도 상태다"라는 계약에 가깝기 때문에 필드와 메서드 시그니처에서 먼저 그 질문부터 정하면 된다.
