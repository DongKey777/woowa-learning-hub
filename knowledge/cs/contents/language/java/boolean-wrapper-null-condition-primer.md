# `Boolean`이 `null`일 수도 있을 때 조건문을 어떻게 읽을까 beginner bridge

> 한 줄 요약: `Boolean`은 `true`/`false`뿐 아니라 `null`도 담을 수 있어서, 조건문에서는 단순 wrapper 값 비교와 다르게 "지금 이 값이 참인가"와 "아직 상태가 비어 있나"를 분리해서 읽어야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Primitive-wrapper choice primer: `int`/`long`/`boolean` vs `Integer`/`Long`/`Boolean`](./primitive-wrapper-choice-primer.md)
- [Wrapper 값 비교 입문 브리지 (`Integer` / `Long` / `Boolean`)](./wrapper-value-comparison-beginner-bridge.md)
- [Java Optional 입문](./java-optional-basics.md)
- [`Optional<Boolean>`가 왜 자주 어색할까 follow-up card](./optional-boolean-double-absence-follow-up-card.md)
- [Java enum 기초](./java-enum-basics.md)
- [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)
- [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- [Null Object Pattern: null 대신 아무 일도 하지 않는 객체를 넣기](../../design-pattern/null-object-pattern.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: boolean null condition beginner, java boolean null semantics, if flag null npe, boolean true false null, boolean wrapper condition basics, boolean true equals null safe, boolean wrapper equality vs condition, tri state boolean beginner, boolean null 왜 터져요, boolean 조건문 처음, boolean null state enum optional, java boolean wrapper what is, true false null 헷갈림

## 핵심 개념

`boolean`과 `Boolean`은 이름이 비슷하지만, 조건문에서는 질문 자체가 달라진다.

- `boolean`은 항상 `true` 아니면 `false`다
- `Boolean`은 `true`, `false`, `null` 세 상태를 가질 수 있다

그래서 `Boolean approved`를 보면 먼저 두 질문을 나눠야 한다.

1. 지금 하고 싶은 일이 단순 값 비교인가?
2. 아니면 조건문에서 "참일 때만 실행"을 묻는가?

값 비교라면 `Objects.equals(left, right)`나 `Boolean.TRUE.equals(flag)` 같은 비교 규칙이 중심이다.
조건문이라면 `null`을 어떤 상태로 해석할지부터 정해야 한다. 즉 `Boolean`은 "boolean wrapper"이기도 하지만, 초보자 코드에서는 종종 작은 tri-state 상태 모델로도 읽힌다.

## 한눈에 보기

| 지금 코드에서 묻는 것 | 바로 쓰기 쉬운 표현 | 왜 이렇게 읽나 |
|---|---|---|
| `flag`가 `true`인가 | `Boolean.TRUE.equals(flag)` | `null`이어도 안전하게 `false`로 읽힌다 |
| `flag`가 `false`인가 | `Boolean.FALSE.equals(flag)` | "거짓으로 명시됨"과 `null`을 분리한다 |
| `flag`가 비어 있나 | `flag == null` | 아직 값이 안 정해졌다는 뜻을 직접 본다 |
| 두 wrapper 값이 같은가 | `Objects.equals(left, right)` | 값 비교와 조건문 의미를 섞지 않는다 |
| `null`도 하나의 상태인가 | `Optional`, `enum`, 상태 타입 검토 | `true/false`만으로 부족한 의미를 타입으로 올린다 |

짧게 외우면 이렇다.

> `if (flag)`는 "참인가"만 보는 것 같지만, 실제로는 `null` unboxing 가능성까지 같이 끌고 온다.

## 왜 `if (flag)`가 초보자 코드를 자주 흔들까

겉으로는 자연스러워 보이지만, `flag`가 `Boolean`이면 JVM은 안쪽에서 `boolean`으로 꺼내 쓰려고 한다.

```java
Boolean approved = null;

if (approved) {
    sendCoupon();
}
```

이 코드는 "`approved`가 참이면 쿠폰 발급"처럼 읽히지만, 실행 시점에는 `approved.booleanValue()` 같은 unboxing이 필요하다. `approved`가 `null`이면 여기서 `NullPointerException`이 난다.

초보자 기준으로는 아래처럼 생각하면 충분하다.

- `if (primitiveBoolean)`은 괜찮다
- `if (wrapperBoolean)`은 `null` 가능성을 먼저 확인해야 한다
- 그래서 wrapper를 조건문에 바로 넣기보다, "`true`인가", "`false`인가", "아직 없음인가"를 분리해서 쓰는 편이 안전하다

즉 `Boolean`에서 위험한 지점은 equality만이 아니라 조건문 진입 순간의 자동 unboxing이다.

## `true` / `false` / `null`을 각각 어떻게 읽을까

`Boolean`이 정말 필요한 이유는 보통 `null`이 "아직 모름" 또는 "안 왔음" 같은 별도 의미를 가질 때다.

| 값 | beginner 해석 | 흔한 예 |
|---|---|---|
| `Boolean.TRUE` | 명시적으로 참 | 체크박스를 사용자가 켰다 |
| `Boolean.FALSE` | 명시적으로 거짓 | 체크박스를 사용자가 껐다 |
| `null` | 아직 안 정해짐, 안 보냄, 초기 상태 | PATCH 요청에서 필드 미전달 |

예를 들어:

```java
Boolean marketingConsent = request.marketingConsent();

if (Boolean.TRUE.equals(marketingConsent)) {
    subscribe();
}
```

이 코드는 `null`을 "참 아님"으로 처리한다. 이 선택이 맞는 상황도 많다. 하지만 `null`이 정말로 "미입력"이라서 나중에 따로 처리해야 한다면, 아래처럼 분리하는 편이 낫다.

```java
if (marketingConsent == null) {
    askAgain();
} else if (marketingConsent) {
    subscribe();
} else {
    keepOff();
}
```

핵심은 `null`을 그냥 귀찮은 예외 케이스로 밀어내지 말고, 상태 의미가 있는지 먼저 판단하는 것이다.

초보자가 API update 요청에서 가장 많이 만나는 해석 표도 같이 보면 좋다.

| 요청 DTO의 값 | PATCH에서 자주 쓰는 해석 | 주의점 |
|---|---|---|
| `true` | 이 필드를 켜 달라 | 명시적 변경 |
| `false` | 이 필드를 꺼 달라 | 명시적 변경 |
| `null` | 변경 없음, 아직 미응답, 잘못된 요청 중 하나 | 팀 계약 없이는 뜻이 고정되지 않는다 |

즉 `Boolean`의 `null`은 자바 문법 문제가 아니라, update API에서 "이 요청이 기존 상태를 건드리나"라는 계약 문제이기도 하다.

## wrapper 값 비교와 조건문 해석은 다른 문제다

초보자가 자주 섞는 두 질문을 나누면 판단이 쉬워진다.

| 질문 | 중심 표현 | 핵심 포인트 |
|---|---|---|
| "이 두 값이 같은가?" | `Objects.equals(left, right)` | wrapper equality 문제 |
| "이 값이 참인가?" | `Boolean.TRUE.equals(flag)` | null-safe 조건문 문제 |
| "왜 값이 비어 있지?" | `Optional` 또는 상태 타입 | tri-state 의미 문제 |

예를 들어 아래 두 줄은 비슷해 보여도 목적이 다르다.

```java
Objects.equals(leftFlag, rightFlag);
Boolean.TRUE.equals(published);
```

첫 번째는 두 값이 같은지 묻는다. 두 번째는 `published`가 `true`인지 묻는다. `null`을 어떻게 처리하는지도 다르다.

- equality 문제라면 `left`와 `right`를 대칭으로 본다
- 조건문 문제라면 `true`를 기준값으로 두고 `flag`를 해석한다
- 상태 모델 문제라면 아예 `Boolean` 하나로 충분한지 다시 본다

그래서 "wrapper 비교" 문서와 "조건문에서의 `Boolean`" 문서는 붙어 있지만, 같은 질문에 답하는 것은 아니다.

## `null`이 계속 의미를 가지면 `Optional`이나 `enum`으로 올릴 때

`Boolean`이 편한 건 상태가 셋뿐일 때까지다. 아래처럼 설명 문장이 길어지기 시작하면 브리지 하나 더 건너는 편이 좋다.

- `null` = 아직 답변 안 함
- `false` = 명시적으로 거절
- `true` = 명시적으로 동의

이 정도면 `Boolean`으로도 버틸 수 있다. 하지만 아래처럼 되면 `Boolean` 하나가 점점 흐려진다.

- `null` = 초기 상태
- `false` = 비활성
- `true` = 활성
- 추가로 `SUSPENDED`, `EXPIRED`도 필요해질 수 있다

이때는 `enum`이 더 선명하다.

```java
enum ConsentStatus {
    UNANSWERED,
    ACCEPTED,
    REJECTED
}
```

또 "값이 없을 수도 있다"만 중요하면 `Optional<Boolean>`보다 질문을 다시 보는 편이 좋다.

- 정말 단건의 있음/없음인가
- 아니면 `Boolean` 값 자체가 이미 상태를 품고 있는가

초보자 코드에서는 `Optional<Boolean>`가 "없음"과 `Boolean`의 tri-state를 겹쳐서 더 헷갈리게 만들 때가 많다. 이럴 때는 `enum` 또는 상태 포함 타입으로 올리는 편이 더 읽기 쉽다.

## 흔한 오해와 함정

- "`Boolean`도 불린이니까 `if (flag)`면 되겠지"
  `Boolean`은 wrapper라서 `null`일 수 있고, 조건문에서 자동 unboxing이 일어난다.
- "`Boolean.TRUE.equals(flag)`면 모든 설계가 끝난다"
  null-safe 조건문에는 좋지만, `null`이 별도 상태 의미를 가지면 설계 질문은 남아 있다.
- "`Objects.equals(flag, true)`도 같은 것 아닌가"
  결과는 비슷할 수 있지만, `Boolean.TRUE.equals(flag)`가 "참인지 확인"이라는 의도를 더 직접 드러낸다.
- "헷갈리니까 전부 `Optional<Boolean>`로 감싸자"
  단건 존재 여부와 tri-state 의미가 겹치며 오히려 읽기 어려워질 수 있다.

## 실무에서 쓰는 모습

가장 흔한 장면은 DTO나 요청 모델에서 `Boolean`이 들어왔을 때다.

```java
public record UpdateProfileRequest(Boolean marketingConsent) {
}
```

이 필드를 서비스에서 읽을 때는 먼저 정책을 정한다.

1. `null`을 "변경 없음"으로 볼까?
2. `null`을 validation error로 볼까?
3. `true`/`false`/`미응답`을 아예 enum으로 분리할까?

정책이 정해지면 조건문도 달라진다.

- 단순 "참일 때만 실행"이면 `Boolean.TRUE.equals(...)`
- `null`을 따로 처리해야 하면 `if (value == null)` 분기를 먼저 둔다
- 상태가 늘어나면 `enum`이나 값 타입으로 올린다

즉 실무 포인트는 문법 암기가 아니라, 조건문에 넣기 전에 `null`을 어떤 상태로 볼지 먼저 확정하는 것이다.

PATCH 감각으로 짧게 보면 이런 흐름이다.

```java
public void updatePublishState(Post post, Boolean requested) {
    if (requested == null) {
        return; // 이 팀에서는 null을 "변경 없음"으로 해석
    }
    post.changePublished(requested);
}
```

여기서 중요한 것은 "`Boolean`이라서 null-safe 비교를 쓴다"보다도 "`null`의 뜻을 먼저 정해 두고 그 정책에 맞는 분기를 둔다"는 점이다.

만약 `null`이 "아직 리뷰 안 끝남", `false`가 "비공개", `true`가 "공개"처럼 계속 상태 의미를 품으면 `Boolean` 하나가 점점 답답해진다.  
그때는 다음 단계로 `enum`을 검토하면 된다.

```java
enum PublishDecision {
    UNDECIDED,
    HIDDEN,
    PUBLISHED
}
```

## 더 깊이 가려면

- wrapper 값 비교 자체가 먼저 헷갈리면 [Wrapper 값 비교 입문 브리지 (`Integer` / `Long` / `Boolean`)](./wrapper-value-comparison-beginner-bridge.md)
- `Optional<Boolean>`가 왜 자주 어색해지는지 이어서 보려면 [Java Optional 입문](./java-optional-basics.md)과 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- `Optional<Boolean>`만 따로 짧게 정리한 카드가 필요하면 [`Optional<Boolean>`가 왜 자주 어색할까 follow-up card](./optional-boolean-double-absence-follow-up-card.md)
- `null`이 상태 의미를 가지기 시작할 때는 [Java enum 기초](./java-enum-basics.md)와 [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)
- API payload에서 missing / explicit `null` / default가 어떻게 갈리는지는 [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- "아무 일도 하지 않음"이 자연스러운 협력 객체라면 [Null Object Pattern: null 대신 아무 일도 하지 않는 객체를 넣기](../../design-pattern/null-object-pattern.md)

## 한 줄 정리

`Boolean`을 조건문에 넣을 때는 wrapper equality 규칙만 외우지 말고, `true`/`false`/`null` 중 `null`을 어떤 상태로 읽을지 먼저 정한 뒤 `Boolean.TRUE.equals(...)`, 명시적 `null` 분기, `enum` 승격 중 하나를 고르면 된다.
