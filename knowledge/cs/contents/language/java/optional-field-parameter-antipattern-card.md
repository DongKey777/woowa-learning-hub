# `Optional` 필드/파라미터 anti-pattern 30초 카드

> 한 줄 요약: `Optional`은 보통 "반환값에서 없음 여부를 드러내는 상자"로 가장 잘 맞고, 필드나 파라미터에 넣기 시작하면 상태가 두 겹으로 늘고 API 읽기가 더 어려워진다.

**난이도: 🟢 Beginner**

관련 문서:

- [`Optional<List<T>>` vs 빈 컬렉션 증상 카드](./optional-list-empty-collection-symptom-card.md)
- [Java Optional 입문](./java-optional-basics.md)
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
- [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: optional field parameter anti pattern, java optional field beginner, java optional parameter beginner, optional 필드 왜 안 쓰나, optional 파라미터 왜 안 되나, optional field anti pattern java, optional parameter anti pattern java, return optional not field, return optional not parameter, optional 대신 뭘 쓰나, 처음 배우는데 optional 필드, optional null 이중 상태, beginner optional api design, optional list vs empty list, optional list field 어색함

## 먼저 잡는 멘탈 모델

`Optional`은 보통 "돌려줄 때 쓰는 상자"다.
메서드가 값을 **반환**할 때는 "없을 수도 있음"을 호출자에게 분명히 알려 준다.

반대로 필드나 파라미터에 넣으면 질문이 두 겹이 된다.

- 이 값이 없는가?
- `Optional` 자체도 `null`일 수 있는가?

즉 초보자 기준으로는 `Optional`을 저장하거나 전달하는 상자로 보기보다, **반환 시점에만 잠깐 꺼내 드는 표시판**으로 생각하는 편이 덜 헷갈린다.

## 10초 판단 표

| 지금 위치 | `Optional`을 바로 두기보다 먼저 볼 것 | 이유 |
|---|---|---|
| 메서드 반환값 | `Optional<T>` | "없을 수 있음"을 타입으로 드러내기 좋다 |
| 필수 필드 | 그냥 `T` + 생성자 검증 | 빠지면 안 되는 값은 비어 있는 상자가 아니라 불변식 문제다 |
| 선택 필드 | private nullable field + 반환 메서드에서 `Optional.ofNullable(...)` 또는 상태 타입 | 저장은 단순하게 두고, 바깥 노출만 분명하게 만들 수 있다 |
| 0개 이상 데이터 | 빈 `List`/`Set`/`Map` | `Optional<List<T>>`보다 읽기 쉽다 |
| 선택 파라미터 1개 | 메서드 오버로딩 또는 의미가 다른 별도 메서드 | 호출자가 `Optional.empty()`를 만들어 넘길 이유가 줄어든다 |
| 선택 파라미터 여러 개 | parameter object / request command / builder | 파라미터 나열보다 의도가 잘 보인다 |

## 왜 필드에 두면 어색한가

필드는 "객체가 지금 어떤 상태인가"를 저장하는 자리다.
그런데 `Optional<String> nickname`처럼 두면, 실제 상태보다 포장 상태가 먼저 눈에 들어온다.

특히 아래 문제가 자주 같이 온다.

- `Optional` 필드 자체에 `null`이 들어가면 `null`과 `Optional.empty()`가 동시에 생긴다
- 직렬화/바인딩/ORM 경계에서 예상보다 잘 안 맞는다
- getter에서 다시 `Optional`을 꺼내고, 사용하는 쪽도 또 `isPresent()`를 보게 되어 읽기 비용이 늘어난다

짧게 말하면 필드는 데이터를 저장해야 하는데, `Optional` 필드는 데이터와 포장을 같이 저장해 버린다.

```java
class UserProfile {
    private String nickname;

    public Optional<String> nickname() {
        return Optional.ofNullable(nickname);
    }
}
```

이쪽이 더 단순한 이유는 내부 저장은 평범하게 두고, 바깥에 보여 줄 때만 `Optional`로 의미를 드러내기 때문이다.

## 왜 파라미터에 두면 어색한가

파라미터는 "호출자가 지금 무엇을 넘겨야 하는가"를 읽는 자리다.
그런데 `changeNickname(Optional<String> nickname)`처럼 만들면 호출자가 값 전달보다 포장 규칙부터 신경 써야 한다.

게다가 아래처럼 호출 방식이 불필요하게 늘어난다.

- `changeNickname(Optional.of("neo"))`
- `changeNickname(Optional.empty())`
- 잘못하면 `changeNickname(null)`

즉 "값이 필요한가, 비우고 싶은가, 아예 호출을 안 해야 하는가"가 한 메서드에 섞인다.

보통은 아래처럼 의미를 나누는 편이 더 읽기 쉽다.

```java
class UserProfile {
    public void changeNickname(String nickname) { ... }

    public void clearNickname() { ... }
}
```

또는 선택 입력이 많아지면 메서드 오버로딩보다 command 객체나 builder가 더 낫다.

## 대신 무엇을 쓰면 좋나

초보자 기준으로는 아래 순서로 고르면 된다.

1. 꼭 있어야 하는 값이면 그냥 `T`로 받고 생성자/메서드 안에서 검증한다.
2. "비운다"가 별도 행동이면 `clearXxx()` 같은 메서드로 분리한다.
3. 선택 입력이 많으면 parameter object, request DTO, command 객체로 묶는다.
4. 0개 이상 데이터면 빈 컬렉션을 쓴다.
5. 없음의 이유가 중요하면 `enum`, `record`, value object 같은 상태 타입으로 올린다.

핵심은 "`Optional`을 everywhere"가 아니라, **없음의 의미를 어디서 드러내는 게 가장 읽기 쉬운가**다.

## 흔한 오해와 함정

- "`Optional`이면 무조건 null-safe다"
  `Optional` 필드 자체가 `null`이면 그대로 깨진다.
- "선택 파라미터를 표현하려면 `Optional`이 가장 정직하다"
  호출자는 값보다 포장 방식을 먼저 읽게 된다. 오버로딩이나 별도 메서드가 더 직접적일 때가 많다.
- "필드도 `Optional`이면 getter가 깔끔하다"
  저장, 직렬화, 바인딩까지 함께 보면 오히려 경계가 복잡해지기 쉽다.
- "`Optional<List<T>>`가 더 안전하다"
  다건 데이터의 `0개`는 빈 컬렉션이 이미 잘 표현한다.

## 더 이어서 보면 좋은 문서

- `Optional` 자체의 기본 API는 [Java Optional 입문](./java-optional-basics.md)
- 단건/다건/상태 타입 선택은 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- DTO/JSON 경계에서 `null`과 missing을 어떻게 볼지는 [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
- 경계별 타입 역할 분리는 [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)

## 한 줄 정리

`Optional`은 보통 반환값에서 "없을 수 있음"을 드러낼 때 가장 자연스럽고, 필드나 파라미터에서는 plain 값, 빈 컬렉션, 별도 메서드, 상태 타입으로 의미를 나누는 편이 더 읽기 쉽다.
