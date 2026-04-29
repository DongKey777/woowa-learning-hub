# Java Optional 입문

> 한 줄 요약: Optional은 "값이 있을 수도 없을 수도 있다"는 상태를 타입으로 표현해서, null을 직접 다루다 생기는 NullPointerException을 줄이는 컨테이너다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- [`Optional<List<T>>` vs 빈 컬렉션 증상 카드](./optional-list-empty-collection-symptom-card.md)
- [`Optional<Boolean>`가 왜 자주 어색할까 follow-up card](./optional-boolean-double-absence-follow-up-card.md)
- [`Optional` vs `FieldPatch`: PATCH tri-state에서 왜 갈라지나](./optional-vs-fieldpatch-patch-tri-state-bridge.md)
- [Java enum 기초](./java-enum-basics.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [`Optional` 필드/파라미터 anti-pattern 30초 카드](./optional-field-parameter-antipattern-card.md)
- [`Optional.empty()` 비교와 값 꺼내기 전 equality 판단 프라이머](./optional-empty-equals-before-unwrapping-primer.md)
- [Java 예외 처리 기초](./java-exception-handling-basics.md)
- [Java 제네릭 입문](./java-generics-basics.md)
- [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)

retrieval-anchor-keywords: java optional basics, optional 입문, nullpointerexception 방지, optional orelse beginner, optional why use, null 대신 optional, 자바 옵셔널 입문, optional empty ofnullable, 처음 optional, optional 큰 그림, optional 언제 쓰는지, optional vs empty list, optional vs enum, map get null optional 헷갈림, optional과 enum 차이 뭐예요

## 핵심 개념

`Optional<T>`는 값이 있거나 없을 수 있는 컨테이너 클래스다. `null`을 반환하는 대신 `Optional`을 반환하면, 호출한 쪽에서 "값이 없을 수 있다"는 사실을 타입 선언에서 알 수 있다.

입문자가 헷갈리는 지점은 `Optional`이 만능 null 방어책이 아니라는 것이다. 반환 타입으로만 쓰는 것이 의도된 용도이며, 필드나 메서드 파라미터에 쓰면 오히려 코드가 복잡해진다.

## 10초 결정표: `Optional`만 보면 되는가

`Optional`은 "단건의 있음/없음"을 표현할 때 가장 잘 맞는다. 초보자가 자주 섞는 다른 선택지와 같이 보면 기준이 더 선명해진다.

| 지금 표현하려는 것 | 첫 선택 | 왜 이렇게 읽나 |
|---|---|---|
| 회원 한 명을 찾았더니 없을 수도 있다 | `Optional<User>` | 단건 결과의 있음/없음만 말하면 충분하다 |
| 주문 항목이 0개일 수 있다 | `List<OrderLine>` + 빈 리스트 | 여러 건 자료의 0개는 컬렉션이 이미 표현한다 |
| 상태가 없음 / 비공개 / 미입력처럼 이유까지 중요하다 | `enum` 또는 상태 타입 | 단순 empty보다 "왜 없는지"가 더 중요하다 |
| `Map#get(...)` 결과가 비어 보인다 | `Map` 해석 문서로 분기 | key 없음과 value가 `null`인 상황이 겹칠 수 있다 |

한 줄로 줄이면 이렇다. `Optional`은 "한 칸짜리 상자", 컬렉션은 "여러 칸짜리 상자", 상태 타입은 "없음의 이유까지 이름 붙인 상자"다.

같은 흐름을 객체 언어로 다시 붙이면 더 덜 헷갈린다.

- `field`: 객체 안에 저장된 칸
- `object state`: 그 field 값들이 모인 현재 상태
- `behavior`: 그 상태를 읽거나 바꾸는 메서드

`Optional`은 보통 "지금 한 칸 값이 비어 있을 수 있는가"를 설명하고, enum 상태는 "그 칸이 비어 있는 이유나 상태 이름이 무엇인가"를 설명한다.

## 처음 `Optional`이 헷갈릴 때 먼저 자를 3가지 질문

`왜 Optional이 필요하지?`, `빈 리스트랑 뭐가 다르지?`, `enum으로 안 되나?`가 한꺼번에 섞이면 아래 순서로 먼저 자르면 된다.

1. 지금 결과가 한 건인가, 여러 건인가?
2. 없음만 중요할까, 없음의 이유도 중요할까?
3. `Map#get(...)`처럼 `null` 하나에 두 의미가 겹친 상황인가?

빠르게 번역하면 이렇다.

- 한 건의 있음/없음이면 `Optional`
- 여러 건의 0개면 빈 컬렉션
- 이유가 중요하면 enum 상태 또는 상태 타입
- 조회 결과의 `null` 해석이 문제면 `Map` 문서로 분기

## 한 예제로 같이 보기: `Optional` / 빈 리스트 / enum 상태

초보자가 가장 많이 헷갈리는 질문은 이거다. "없을 수 있으면 전부 `Optional`로 감싸면 되는 것 아닌가요?"
아니다. 같은 "없음"이라도 질문 자체가 다르다.

| 지금 코드가 말하려는 것 | 첫 선택 | 왜 이쪽이 더 자연스러운가 |
|---|---|---|
| 회원 한 명을 찾았는데 없을 수도 있다 | `Optional<User>` | 단건 결과의 있음/없음만 표현하면 된다 |
| 장바구니 상품이 하나도 없을 수 있다 | `List<CartItem>` + 빈 리스트 | 여러 건 자료의 0개는 컬렉션 자체가 표현한다 |
| 닉네임이 없는 이유가 미입력/비공개로 갈린다 | `enum` 포함 타입 | "왜 없는지"까지 상태 이름으로 드러낼 수 있다 |
| `Map#get(...)`가 `null`이다 | `Map` 해석 규칙 확인 | key 없음과 value `null`을 분리해서 읽어야 한다 |

```java
Optional<User> owner = userRepository.findById(ownerId);
List<CartItem> items = cart.findItems();

enum NicknameStatus {
    PRESENT, NOT_ENTERED, PRIVATE
}
```

이 예제에서 핵심은 "없음의 모양"이 서로 다르다는 점이다.

- `Optional<User>`는 한 명이 있나 없나를 묻는다
- `List<CartItem>`는 0개인가 1개 이상인가를 묻는다
- `NicknameStatus`는 왜 비어 있는지까지 이름을 붙인다
- `Map#get(...)`는 `null` 하나에 두 의미가 겹칠 수 있다

여기서 enum 쪽을 객체 관점으로 다시 읽으면 `NicknameStatus`가 `NicknameInfo`의 field 의미를 더 선명하게 만든다. 즉 "`없음`을 Optional로 표현할까?"와 "`그 field의 object state를 enum 이름으로 드러낼까?"는 같은 설계 흐름 안의 분기다.

처음 배우는 단계에서는 "`없을 수 있다`"는 말만 듣고 전부 `Optional`로 감싸기 쉽다. 하지만 컬렉션과 상태 타입이 이미 더 정확한 의미를 주는 순간에는 `Optional`이 아니라 그 타입을 그대로 쓰는 편이 읽기 쉽다.

## 한눈에 보기

- `java optional basics`의 첫 기준은 정의, 사용 시점, 흔한 오해를 분리해서 읽는 것이다.
- 코드 예시는 바로 아래 섹션에서 보고, 여기서는 판단 기준만 먼저 잡는다.
- 입문 단계에서는 API 이름보다 어떤 문제를 줄이는지부터 확인한다.

## 코드로 보는 예시

```java
// null 직접 반환 방식 (NPE 위험)
String name = findUser(id);    // null일 수 있음
System.out.println(name.length()); // NPE 가능

// Optional 방식 (없음을 타입으로 표현)
Optional<String> name = findUser(id);
name.ifPresent(n -> System.out.println(n.length())); // 있을 때만 실행
```

## 상세 분해

### 생성 방법 세 가지

```java
Optional<String> a = Optional.of("hello");       // 값이 반드시 있을 때
Optional<String> b = Optional.empty();            // 비어 있는 Optional
Optional<String> c = Optional.ofNullable(value);  // null일 수도 있을 때
```

`Optional.of(null)`은 즉시 `NullPointerException`을 던진다. null이 들어올 수 있다면 `ofNullable`을 써야 한다.

### 값 꺼내기 — orElse / orElseGet / orElseThrow

```java
Optional<String> opt = Optional.ofNullable(getName());

String s1 = opt.orElse("기본값");             // 없으면 "기본값" 반환
String s2 = opt.orElseGet(() -> compute());   // 없으면 람다 실행 결과 반환
String s3 = opt.orElseThrow();               // 없으면 NoSuchElementException
```

`orElse`는 Optional이 비어 있든 아니든 인수를 항상 평가한다. 인수 생성 비용이 클 때는 `orElseGet`이 낫다.

### map과 filter로 변환 체인

```java
Optional<String> name = findUser(id)
    .map(User::getName)
    .filter(n -> !n.isBlank());
```

값이 있을 때만 `map`과 `filter`가 적용된다. 없으면 `Optional.empty()`가 그대로 흘러간다.

### ifPresent로 부수 효과 처리

```java
findUser(id).ifPresent(user -> log.info("사용자 접속: {}", user.getName()));
```

값이 있을 때만 람다를 실행한다. `isPresent()` + `get()` 조합보다 간결하고 안전하다.

## 흔한 오해와 함정

**오해 1: `get()`으로 꺼내면 된다**
`get()`은 비어 있으면 `NoSuchElementException`을 던진다. 반드시 `isPresent()` 확인 후 써야 하는데, 그냥 `orElse`나 `ifPresent`를 쓰는 게 더 낫다.

값 꺼내기 전에 "empty인가?" 또는 "같은 값을 감싼 `Optional`인가?"를 판단하는 감각이 약하면 [`Optional.empty()` 비교와 값 꺼내기 전 equality 판단 프라이머](./optional-empty-equals-before-unwrapping-primer.md)를 같이 보면 좋다.

**오해 2: Optional을 필드에 저장해도 된다**
Optional은 직렬화(Serializable)를 구현하지 않는다. 필드에 저장하면 직렬화 오류가 나거나 의도치 않은 null 혼재가 생긴다. 반환 타입으로만 써야 한다.

**오해 3: Optional이 있으면 null 체크가 완전히 필요 없다**
Optional 자체가 null이면 똑같이 NPE가 발생한다. `Optional<T>` 변수에 null을 대입하지 않는 게 전제다.

**오해 4: 빈 리스트, enum 상태, `Map.get()`의 `null`도 전부 Optional로 감싸면 끝난다**
아니다. "0개"는 빈 컬렉션이 더 자연스럽고, "왜 없는지"가 중요하면 상태 타입이 더 설명력이 좋다. `Map.get()`의 `null`은 key 없음과 `null` value를 구분해야 해서 `Optional`로만 바로 치환하면 오히려 상황을 가릴 수 있다.

초보자 기준 빠른 기억법은 한 줄이면 된다.

- "`한 명 없음`은 `Optional`, `여러 개 없음`은 빈 컬렉션, `없음의 이유`는 enum 상태"

## 다음 한 칸

처음 읽기에서는 "어디에 써야 하느냐"보다 "어디까지 쓰지 말아야 하느냐"를 같이 잡는 편이 안전하다.

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`Optional<List<T>>`와 빈 리스트를 언제 갈라야 할지 짧게 다시 보고 싶다" | [`Optional<List<T>>` vs 빈 컬렉션 증상 카드](./optional-list-empty-collection-symptom-card.md) |
| "`Optional<List<T>>`가 왜 어색한지 더 확인하고 싶다" | [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md) |
| "`PATCH`에서 `Optional`로도 될 것 같은데 왜 `FieldPatch`를 또 두죠?" | [`Optional` vs `FieldPatch`: PATCH tri-state에서 왜 갈라지나](./optional-vs-fieldpatch-patch-tri-state-bridge.md) |
| "`Map.get()`의 `null`과 `Optional.empty()`가 계속 섞인다" | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) |
| "필드/파라미터에 두지 말라는 이유를 짧게 다시 보고 싶다" | [`Optional` 필드/파라미터 anti-pattern 30초 카드](./optional-field-parameter-antipattern-card.md) |
| "`Optional<Boolean>`가 왜 의미를 두 겹으로 만들기 쉬운지 짧게 보고 싶다" | [`Optional<Boolean>`가 왜 자주 어색할까 follow-up card](./optional-boolean-double-absence-follow-up-card.md) |
| "`get()` 없이 비교하고 비어 있음 판단하는 감각이 약하다" | [`Optional.empty()` 비교와 값 꺼내기 전 equality 판단 프라이머](./optional-empty-equals-before-unwrapping-primer.md) |
| "Stream과 같이 쓸 때 읽기 규칙이 헷갈린다" | [Java 스트림과 람다 입문](./java-stream-lambda-basics.md) |

## 더 깊이 가려면

- `Optional.empty()` 비교, `Optional.equals(...)`, `get()` 없이 특정 값과 비교하는 패턴은 [`Optional.empty()` 비교와 값 꺼내기 전 equality 판단 프라이머](./optional-empty-equals-before-unwrapping-primer.md)
- 필드/파라미터에 왜 보통 두지 않는지와 대안 선택은 [`Optional` 필드/파라미터 anti-pattern 30초 카드](./optional-field-parameter-antipattern-card.md)
- PATCH tri-state에서 `Optional`과 `FieldPatch`를 어디서 가르는지는 [`Optional` vs `FieldPatch`: PATCH tri-state에서 왜 갈라지나](./optional-vs-fieldpatch-patch-tri-state-bridge.md)
- `Optional<List<T>>`를 빈 컬렉션과 어떻게 나눌지 한 장으로 다시 보려면 [`Optional<List<T>>` vs 빈 컬렉션 증상 카드](./optional-list-empty-collection-symptom-card.md)
- `Optional<List<T>>` 대신 빈 컬렉션이나 상태 타입을 언제 고를지: [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- Stream과 함께 쓰는 방법: [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- 빈 컬렉션, `Map.get()`의 `null`, 상태 타입까지 같이 보고 싶다면 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)와 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- Stream 연계나 메모리 누수처럼 운영 냄새가 나는 follow-up은 [Optional / Stream / 불변 컬렉션 / 메모리 누수 패턴](./optional-stream-immutable-collections-memory-leak-patterns.md)

## 한 줄 정리

Optional은 null 대신 "없음"을 타입으로 표현하는 컨테이너이며, 반환 타입으로만 써야 하고 `get()` 대신 `orElse`·`ifPresent`·`map`으로 안전하게 꺼낸다.
