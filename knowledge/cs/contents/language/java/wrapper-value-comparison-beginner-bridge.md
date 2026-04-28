# Wrapper 값 비교 입문 브리지 (`Integer` / `Long` / `Boolean`)

> 한 줄 요약: `Integer`, `Long`, `Boolean`은 숫자나 불린처럼 보여도 객체이므로 `==`를 기본값으로 두지 말고, 값 비교라면 `equals()`나 `Objects.equals(...)`를 먼저 떠올리는 편이 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Primitive-wrapper choice primer: `int`/`long`/`boolean` vs `Integer`/`Long`/`Boolean`](./primitive-wrapper-choice-primer.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [`Boolean`이 `null`일 수도 있을 때 조건문을 어떻게 읽을까 beginner bridge](./boolean-wrapper-null-condition-primer.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [Java Optional 입문](./java-optional-basics.md)
- [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
- [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- [객체지향 설계 기초](../../software-engineering/oop-design-basics.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: java wrapper comparison basics, integer long boolean equals beginner, wrapper == vs equals, integer 비교 뭐 써요, long 비교 왜 이상해요, boolean wrapper equals, java autoboxing beginner bridge, wrapper value comparison intro, wrapper comparison 처음, wrapper comparison 헷갈려요, objects.equals wrapper, what is wrapper value comparison

## 핵심 개념

초보자 눈에는 `Integer`, `Long`, `Boolean`이 `int`, `long`, `boolean`과 거의 같아 보인다. 이름도 비슷하고, 출력값도 똑같이 보이기 때문이다.

하지만 비교 규칙은 다르다.

- `int`, `long`, `boolean`은 기본형이라 `==`가 값 비교다
- `Integer`, `Long`, `Boolean`은 객체라 `==`가 같은 객체인지 보는 쪽에 가깝다
- 그래서 wrapper 값 비교는 `equals()`나 `Objects.equals(...)`를 기본 선택지로 두는 편이 안전하다

이 문서의 목표는 cache나 boxing 내부 동작을 먼저 설명하는 게 아니다. 입문자가 "지금 이 줄에서 무엇을 비교해야 하나"를 바로 고를 수 있게 만드는 것이다.

## 한눈에 보기

| 지금 가진 값 | 질문 | 초보자 기본 선택 | 이유 |
|---|---|---|---|
| `int`, `long`, `boolean` | 값이 같은가 | `==` | 기본형은 `==`가 값 비교다 |
| `Integer`, `Long`, `Boolean` | 값이 같은가 | `equals()` | wrapper는 객체라 값 비교를 `==`에 맡기지 않는다 |
| `Integer`, `Long`, `Boolean` | 둘 중 하나가 `null`일 수 있는가 | `Objects.equals(a, b)` | null-safe하게 값 비교할 수 있다 |
| `Boolean flag` | `true`인지 확인하고 싶은가 | `Boolean.TRUE.equals(flag)` | `flag`가 `null`이어도 안전하다 |
| wrapper 둘 | 정말 같은 객체를 가리키는가 | `==` | value가 아니라 identity를 볼 때만 쓴다 |

먼저 외울 규칙은 짧다.

- primitive 값 비교면 `==`
- wrapper 값 비교면 `equals()`
- wrapper가 `null`일 수도 있으면 `Objects.equals(...)`

## 왜 wrapper에서 `==`가 헷갈릴까

헷갈리는 이유는 코드가 너무 primitive처럼 보이기 때문이다.

```java
Integer left = 10;
Integer right = 10;
```

여기서 숫자 `10`만 보면 "숫자끼리 비교하니까 `==`겠지"라고 생각하기 쉽다. 하지만 실제 타입은 숫자 자체가 아니라 숫자를 담은 객체다.

초보자 mental model은 이렇게 두면 충분하다.

1. wrapper는 숫자나 불린을 담은 상자다.
2. `==`는 상자 두 개가 같은 상자인지 묻기 쉽다.
3. `equals()`는 상자 안 값이 같은지 묻는 쪽이다.

즉 wrapper 비교에서 먼저 답해야 할 질문은 "`값`이 같은가?"인지, "`같은 객체`인가?"인지다. 입문 코드 대부분은 첫 번째 질문이므로 `equals()` 쪽이 기본값이 된다.

## `Integer` / `Long` / `Boolean` 비교 예시

가장 흔한 세 타입만 따로 보면 패턴이 거의 같다.

```java
Integer ageA = 20;
Integer ageB = 20;

Long idA = 1L;
Long idB = 1L;

Boolean enabledA = Boolean.TRUE;
Boolean enabledB = Boolean.TRUE;

System.out.println(ageA.equals(ageB));         // true
System.out.println(idA.equals(idB));           // true
System.out.println(enabledA.equals(enabledB)); // true
```

입문 단계에서는 아래처럼 읽으면 된다.

| 타입 | 값 비교 기본 규칙 | null 가능성이 있으면 |
|---|---|---|
| `Integer` | `left.equals(right)` | `Objects.equals(left, right)` |
| `Long` | `left.equals(right)` | `Objects.equals(left, right)` |
| `Boolean` | `left.equals(right)` | `Objects.equals(left, right)` 또는 `Boolean.TRUE.equals(flag)` |

`Boolean`은 조건문에서 특히 자주 헷갈린다.

```java
Boolean approved = null;

if (Boolean.TRUE.equals(approved)) {
    approve();
}
```

이 패턴은 "`approved`가 true인가?"를 묻는 데 집중하고, `null`도 안전하게 처리한다.

## 흔한 오해와 함정

### 1. "wrapper도 숫자처럼 보이니 `==`면 되겠지"

가장 흔한 첫 실수다. wrapper는 숫자 모양을 한 객체라서, 값 비교 기본값을 primitive와 같게 두면 안 된다.

### 2. "`equals()`만 기억하면 항상 끝난다"

거의 맞지만 한 가지를 더 붙이면 좋다. 값이 `null`일 수 있으면 `left.equals(right)` 자체가 예외를 낼 수 있으니 `Objects.equals(left, right)`가 더 안전하다.

### 3. "`if (flag)`도 되지 않나"

`flag`가 `Boolean`이면 `null`이 들어올 수 있다. 초보자 코드에서 의미가 "참인가?"라면 `Boolean.TRUE.equals(flag)`가 더 안전하다.

여기서 한 번 더 구분해야 한다.

- "이 값이 다른 `Boolean`과 같은가?"는 wrapper 값 비교 질문이다
- "이 값을 조건문에 넣어도 되나?"는 `true`/`false`/`null` 해석 질문이다

둘이 계속 섞이면 [`Boolean`이 `null`일 수도 있을 때 조건문을 어떻게 읽을까 beginner bridge](./boolean-wrapper-null-condition-primer.md)에서 tri-state 감각만 따로 보는 편이 더 빠르다.

### 4. "primitive와 wrapper를 섞어도 감각은 같다"

감각이 비슷해 보여도 null 가능성과 비교 규칙이 달라진다. 값이 반드시 있어야 하고 비교도 단순하면 primitive가 더 직선적이고, 값이 비어 있을 수 있으면 wrapper를 선택할 이유가 생긴다.

## 실무에서 쓰는 모습

가장 흔한 장면은 세 가지다.

1. ID나 카운트를 DTO나 컬렉션에서 wrapper로 들고 있으면서 값 비교가 필요할 때
2. `Boolean` 플래그가 null일 수 있는 입력을 읽을 때
3. 서비스 로직에서 primitive와 wrapper가 섞여 있어 "왜 어떤 비교는 되고 어떤 비교는 이상하지?"가 나올 때

예를 들면 이런 식이다.

```java
Long ownerId = request.ownerId();

if (Objects.equals(ownerId, loginUserId)) {
    allowEdit();
}
```

여기서 핵심은 "숫자니까 `==`"가 아니라 "wrapper라서 값 비교를 명시한다"는 의도를 코드에 드러내는 것이다.

## 더 깊이 가려면

- `==`, `equals()`, `hashCode()` 전체 그림을 먼저 다시 붙이고 싶다면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- 왜 어떤 값에서는 `==`가 맞아 보이기도 하는지, autoboxing과 cache까지 보려면 [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
- wrapper를 쓰는 이유가 nullability인지 API 바인딩인지 더 따지고 싶다면 [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- `Boolean` 대신 더 명시적인 상태 모델이 필요한지 고민하고 싶다면 [객체지향 설계 기초](../../software-engineering/oop-design-basics.md)

## 면접/시니어 질문 미리보기

Q. wrapper 비교에서 왜 `==`를 피하나요?  
A. 보통 값이 아니라 같은 객체인지 보는 쪽으로 읽히기 때문이다.

Q. `Objects.equals(...)`는 언제 쓰나요?  
A. wrapper가 `null`일 수도 있을 때 안전한 값 비교 기본값으로 쓴다.

Q. `Boolean.TRUE.equals(flag)`는 왜 자주 보이나요?  
A. `flag`가 `null`이어도 "`true`인가?"라는 질문을 예외 없이 표현할 수 있기 때문이다.

Q. 그럼 `Boolean`은 값 비교와 조건문 해석이 같은 문제인가요?  
A. 아니다. 값 비교는 `equals()`/`Objects.equals(...)` 쪽이고, 조건문 해석은 `null`을 어떤 상태로 볼지 정하는 문제다.

## 한 줄 정리

`Integer`, `Long`, `Boolean`은 primitive처럼 보여도 객체이므로, beginner 기본 규칙은 "`==`보다 `equals()`, null 가능성이 있으면 `Objects.equals(...)`"이다.
