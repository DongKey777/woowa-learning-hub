# `Optional<Boolean>`가 왜 자주 어색할까 follow-up card

> 한 줄 요약: `Optional<Boolean>`는 바깥 `Optional`의 "없음"과 안쪽 `Boolean`이 끌고 오는 상태 해석이 겹치기 쉬워서, absence만 말하는지 아니면 상태 이름까지 필요한지 먼저 자른 뒤 `enum`이나 상태 타입으로 올리는 편이 초보자에게 더 읽기 쉽다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java Optional 입문](./java-optional-basics.md)
- [`Boolean`이 `null`일 수도 있을 때 조건문을 어떻게 읽을까 beginner bridge](./boolean-wrapper-null-condition-primer.md)
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- [Java enum 기초](./java-enum-basics.md)
- [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)
- [Validation Boundary: Input vs Domain Invariant 미니 브리지](../../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: optional boolean beginner, optional boolean why bad, optional boolean double absence, optional boolean enum state, optional boolean 왜 헷갈려, optional boolean 언제 쓰나, optional boolean 뭐가 낫나, tri-state boolean optional beginner, boolean null optional 차이, optional boolean state type basics, optional boolean why awkward, beginner optional boolean card

## 핵심 개념

초보자가 `Optional<Boolean>`를 처음 보면 보통 이렇게 생각한다.

- `Optional`이니까 "없을 수도 있음"을 표현한다
- `Boolean`이니까 `true`/`false`를 표현한다

문제는 이 둘을 합치면 질문이 너무 많아진다는 점이다.

- `Optional.empty()`는 아직 값이 안 왔다는 뜻인가
- `Optional.of(false)`는 명시적 거절인가
- "미응답", "변경 없음", "비공개"처럼 이유가 더 있나

즉 `Optional<Boolean>`는 "단건의 없음"과 "불린 상태 해석"을 한 칸에 같이 밀어 넣기 쉽다. 그래서 beginner 단계에서는 타입이 짧아 보여도 읽는 비용이 금방 올라간다.

## 한눈에 보기

| 지금 표현하려는 것 | 첫 선택 | 왜 이쪽이 더 읽기 쉬운가 |
|---|---|---|
| 값이 있나 없나만 중요하다 | `Optional<T>` | absence 하나만 말하면 된다 |
| `yes` / `no` 두 답만 있으면 충분하다 | `boolean` 또는 `Boolean` 정책 명시 | 상태가 둘뿐이면 굳이 바깥 상자를 하나 더 두지 않아도 된다 |
| `미응답` / `동의` / `거절`처럼 이름이 셋 이상이다 | `enum` | 상태 이름을 타입으로 드러낼 수 있다 |
| 상태 이유와 실제 값이 같이 움직인다 | 상태 포함 `record` / 값 객체 | "왜 비어 있는지"와 값을 한 묶음으로 설명할 수 있다 |

짧게 외우면 이렇다.

> `Optional<Boolean>`를 보면 먼저 "없음이 하나인지, 상태 이름이 필요한지"부터 자른다.

## 왜 `Optional<Boolean>`가 뜻을 두 겹으로 만들까

예를 들어 마케팅 수신 동의를 이렇게 표현했다고 하자.

```java
Optional<Boolean> marketingConsent
```

겉으로는 세 경우처럼 보인다.

- `empty`: 응답 없음
- `true`: 동의
- `false`: 거절

하지만 실제 서비스 코드에서는 금방 질문이 더 붙는다.

- `empty`가 "아직 안 물어봄"인가, "PATCH에서 필드 미전달"인가
- `false`가 "명시적 거절"인가, "기본값 false"인가
- 나중에 `EXPIRED`, `REVOKED` 같은 상태가 생기면 어디에 넣을까

즉 바깥 `Optional`이 absence를 말하는데, 안쪽 `Boolean`도 사실상 작은 상태 모델처럼 읽히기 시작한다. 그래서 "없음"과 "상태 이름"이 한 칸에서 서로 밀치게 된다.

## 언제 `enum`이나 상태 타입으로 바꾸나

상태 이름을 문장으로 설명해야 하면 이미 `enum` 신호다.

```java
enum ConsentStatus {
    UNANSWERED,
    ACCEPTED,
    REJECTED
}
```

이쪽이 더 좋은 이유는 아래와 같다.

- `empty`의 뜻을 추측하지 않아도 된다
- `false`가 무엇을 의미하는지 주석으로 보강하지 않아도 된다
- 상태가 늘어나도 switch나 분기에서 이름으로 읽힌다

값까지 같이 보여 줘야 하면 상태 타입으로 한 칸 더 올리면 된다.

```java
record ConsentInfo(ConsentStatus status, String source) {
}
```

초보자용 빠른 기준은 단순하다.

1. `Optional<Boolean>`를 설명하는 한국어 문장이 한 줄을 넘기면 상태 타입을 의심한다.
2. `empty`와 `false`를 서로 다른 업무 의미로 읽고 있으면 `enum`을 먼저 본다.
3. 상태 이유와 추가 데이터가 같이 다니면 `record`나 값 객체를 본다.

## 흔한 오해와 함정

- "`Optional<Boolean>`면 딱 3상태라서 깔끔하다"
  3상태가 깔끔한 것이 아니라, 각 상태 이름이 분명해야 깔끔하다.
- "`false`가 있으니 `empty`는 그냥 null-safe 버전이다"
  실제로는 `false`와 `empty`를 다른 업무 의미로 쓰기 시작해 해석 비용이 커진다.
- "헷갈리면 `Boolean` 대신 `Optional<Boolean>`로 감싸면 된다"
  absence와 상태 이름을 동시에 표현하려 해서 오히려 질문이 늘 수 있다.
- "항상 enum으로 바꾸는 게 정답이다"
  아니다. 정말로 "필드가 전달됐는가"와 "전달된 값이 true/false인가"만 보는 어댑터 경계라면 짧게 지나갈 수도 있다. 다만 도메인 안으로 들어오면 상태 이름을 올리는 편이 안전하다.

## 다음 한 칸

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`Optional`이 어디까지 맞는지 다시 큰 그림으로 보고 싶다" | [Java Optional 입문](./java-optional-basics.md) |
| "`Boolean`의 `true` / `false` / `null` 해석이 먼저 헷갈린다" | [`Boolean`이 `null`일 수도 있을 때 조건문을 어떻게 읽을까 beginner bridge](./boolean-wrapper-null-condition-primer.md) |
| "없음의 이유를 상태 이름으로 올리는 감각이 약하다" | [Java enum 기초](./java-enum-basics.md) |
| "enum 말고 record/value object까지 언제 가는지 보고 싶다" | [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md) |

## 한 줄 정리

`Optional<Boolean>`는 "없음"과 "불린 상태 해석"을 한 칸에 겹치기 쉬우므로, absence만 필요한지 아니면 `UNANSWERED` 같은 상태 이름이 필요한지 먼저 나눈 뒤 `enum`이나 상태 타입으로 올리면 더 명확하다.
