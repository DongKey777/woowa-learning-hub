# Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까

> 한 줄 요약: 도메인에서 `true/false`나 `null`로 상태를 얼버무리기 시작하면 의미가 금방 흐려지므로, "상태 후보가 정해졌는가", "값 묶음 자체가 하나의 의미인가", "생성 시점부터 규칙을 지켜야 하는가"를 기준으로 `enum`, `record`, 값 객체로 올려 주는 편이 초보자도 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java enum 기초](./java-enum-basics.md)
- [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- [Validation Boundary: Input vs Domain Invariant 미니 브리지](../../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)

retrieval-anchor-keywords: domain state type primer, boolean null signaling java, enum vs record vs value object, domain modeling beginner java, boolean flag smell beginner, null state modeling intro, 상태를 boolean으로 두면 왜 헷갈려, null 대신 enum record 값객체, domain state type basics, 자바 도메인 상태 타입 입문, enum record value object 언제 쓰나, beginner domain model state

## 핵심 개념

초보자가 도메인 모델을 만들 때 가장 먼저 나오는 유혹은 "`boolean` 하나면 되겠지", "`null`이면 미입력이겠지"다.

처음엔 빨라 보이지만 곧 이런 질문이 따라온다.

- `true`가 정확히 무엇인가: 승인됨, 공개됨, 완료됨?
- `null`이 왜 비어 있는가: 아직 미입력, 선택 안 함, 정책상 없음?
- 값 둘을 같이 움직여야 하는가: 통화 + 금액, 시작일 + 종료일?

이때 필요한 멘탈 모델은 단순하다.

- **후보가 정해진 상태 이름**이면 `enum`
- **함께 움직이는 값 묶음**이면 `record`
- **규칙까지 품은 도메인 값**이면 값 객체

즉 `boolean`/`null`은 "값이 있다/없다" 정도만 말하고, 도메인 타입은 "그 값이 무슨 의미인지"까지 드러낸다.

## 한눈에 보기

| 지금 코드에서 보이는 신호 | 더 먼저 볼 타입 | 이유 |
|---|---|---|
| `isClosed`, `isPaid`처럼 딱 두 상태만 있고 뜻이 분명하다 | `boolean` 유지 가능 | 상태가 정말 둘뿐이고 추가 가능성이 낮다 |
| `true/false`가 점점 설명이 길어진다 | `enum` | 상태 이름을 코드에 드러내야 한다 |
| `null`이 "없음" 말고 여러 이유를 숨긴다 | `enum` 또는 상태 포함 `record` | 이유를 타입으로 올려야 분기가 읽힌다 |
| 필드 두세 개가 항상 같이 다닌다 | `record` | 하나의 값 묶음으로 읽는 편이 자연스럽다 |
| 생성 시점부터 검증/정규화가 필요하다 | 값 객체 | 불변식과 canonicalization을 타입 안에 둘 수 있다 |

짧게 외우면 이렇다.

> "`boolean`은 예/아니오, `enum`은 상태 이름표, `record`는 값 묶음, 값 객체는 규칙까지 가진 값"이라고 보면 된다.

## 언제 `enum`으로 올리나

`boolean`은 선택지가 정확히 둘일 때만 읽기 쉽다.

하지만 아래처럼 설명이 붙기 시작하면 이미 `enum` 쪽 신호다.

- `isVisible`: 공개, 비공개, 임시저장 중 무엇인가?
- `isDelivered`: 배송 전, 배송 중, 배송 완료, 취소 중 어디인가?
- `deletedAt == null`: 정상, 휴면, soft delete를 어떻게 구분하나?

```java
enum OrderStatus {
    CREATED, PAID, SHIPPED, CANCELLED
}
```

`enum`의 장점은 "가능한 상태 후보"를 코드로 고정한다는 점이다.

- `true/false`보다 이름이 직접 보인다
- 잘못된 상태값 입력을 줄인다
- 나중에 상태 전이 규칙을 붙이기 쉽다

즉 "둘 중 하나"가 아니라 "여러 상태 중 하나"로 읽히는 순간 `enum`이 더 적합하다.

## 언제 `record`가 먼저 맞나

`record`는 상태 이름표보다 **값 묶음**에 강하다.

예를 들어 주소를 `street`, `city`, `zipCode` 세 필드로 여기저기 흩뿌리면 호출자가 항상 "세 개를 같이" 다뤄야 한다.

```java
public record ShippingAddress(String street, String city, String zipCode) {}
```

이런 경우 `record`를 쓰면 좋은 이유는 아래와 같다.

- 값 경계가 한 타입으로 묶인다
- 파라미터 목록이 줄어든다
- `equals()`/`hashCode()`가 값 단위로 자동 정리된다

초보자 기준 판단법은 간단하다.

- "이 필드들이 항상 함께 움직이는가?"
- "이 묶음을 하나의 이름으로 부르는가?"

둘 다 `yes`면 `record`를 먼저 검토해 볼 만하다.
다만 `record`는 **값 묶음**이지 자동으로 "좋은 도메인 모델"이 되는 문법은 아니다. 검증이 더 강하면 값 객체로 한 단계 더 올라간다.

## 언제 값 객체까지 가야 하나

값 객체는 "`record`로도 묶었는데, 여기에 규칙을 더 붙여야 한다"는 순간 등장한다.

예를 들어 할인율이 `null`이거나 `0~100` 밖 숫자일 수 있으면 호출자마다 검증을 반복하게 된다.

```java
public record DiscountRate(int percent) {
    public DiscountRate {
        if (percent < 0 || percent > 100) {
            throw new IllegalArgumentException("discount percent must be 0..100");
        }
    }
}
```

이 타입은 단순 숫자가 아니라 "유효한 할인율"이라는 뜻을 갖는다.

값 객체가 특히 유리한 경우:

- 생성 시점부터 불변식을 지켜야 할 때
- 정규화가 필요할 때 (`trim`, 소문자화, 단위 통일)
- primitive나 `String`만 두면 의미가 빈약할 때

즉 "`null`이 아니기만 하면 된다"를 넘어 "`유효한 값이어야 한다`"가 중요해지는 순간 값 객체가 더 맞다.

## 흔한 오해와 함정

- "`boolean`이 제일 단순하니 항상 좋다"
  단순한 것은 맞지만, 의미가 두 갈래를 넘는 순간 가장 먼저 읽기 어려워진다.
- "`record`면 다 값 객체다"
  아니다. `record`는 값 묶음 문법이고, 불변식 설계까지 자동으로 대신해 주지 않는다.
- "`null` 하나면 미입력/숨김/삭제를 다 표현할 수 있다"
  표현은 되지만 읽는 쪽이 이유를 추측해야 한다. 상태 의미가 중요하면 타입으로 올려야 한다.
- "`enum`만 있으면 상태 모델링이 끝난다"
  `enum`은 후보 목록이고, 실제 전이 규칙은 도메인 메서드가 붙잡아야 한다.

초보자용 빠른 체크는 이것 하나면 된다.

- 설명 주석이 길어질수록 primitive 대신 타입을 올릴 신호다.

## 실무에서 쓰는 모습

아래처럼 바꾸면 감각이 빨리 잡힌다.

| 처음 코드 | 더 나은 첫 변경 | 왜 나은가 |
|---|---|---|
| `boolean isPaid` | `OrderStatus status` | 결제 전/완료/취소를 구분할 여지를 남긴다 |
| `String street, city, zip` 흩어짐 | `ShippingAddress record` | 주소를 한 값으로 전달할 수 있다 |
| `Integer percentOrNull` | `DiscountRate` 값 객체 | null/범위 검증을 호출자마다 반복하지 않는다 |
| `String nicknameOrNull` | `record NicknameInfo(NicknameStatus status, String value)` | 없음의 이유를 타입으로 드러낸다 |

처음부터 완벽하게 고를 필요는 없다.

1. `boolean`이 셋째 의미를 설명하기 시작하면 `enum`
2. 파라미터가 항상 같이 움직이면 `record`
3. 유효성 규칙이 반복되면 값 객체

이 순서로만 올려도 beginner 단계의 도메인 모델은 훨씬 읽기 쉬워진다.

## 더 깊이 가려면

- 상태 후보를 타입으로 고정하는 감각은 [Java enum 기초](./java-enum-basics.md)
- 상태 이름표에서 전이 규칙으로 넘어가는 단계는 [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md)
- `record`가 value object와 어디서 만나고 어디서 갈리는지는 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- request DTO의 raw string을 service 전에 값 객체로 올리는 감각은 [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)
- `Optional`로 끝낼지 상태 타입으로 올릴지 판단은 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- 입력 검증과 도메인 불변식을 어디서 나눌지는 [Validation Boundary: Input vs Domain Invariant 미니 브리지](../../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)

## 한 줄 정리

도메인에서 `boolean`과 `null`이 자꾸 설명을 요구하기 시작하면, 상태 이름은 `enum`, 값 묶음은 `record`, 규칙까지 가진 값은 값 객체로 올리는 쪽이 더 명확하다.
