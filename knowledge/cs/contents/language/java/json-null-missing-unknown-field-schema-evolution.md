# JSON `null`, Missing Field, Unknown Property, and Schema Evolution

> 한 줄 요약: JSON 경계에서 `null`, 필드 누락, 모르는 새 필드는 서로 다른 의미를 가진다. Java DTO/record가 이 차이를 뭉개면 PATCH semantics, 기본값 적용, backward/forward compatibility, 이벤트 재처리가 조용히 깨진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)
> - [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)
> - [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
> - [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md)
> - [`Instant`, `LocalDateTime`, `OffsetDateTime`, `ZonedDateTime` Boundary Design](./java-time-instant-localdatetime-boundaries.md)
> - [Design Pattern: Event Upcaster Compatibility Patterns](../../design-pattern/event-upcaster-compatibility-patterns.md)
> - [Design Pattern: Projection Rebuild, Backfill, and Cutover Pattern](../../design-pattern/projection-rebuild-backfill-cutover-pattern.md)
> - [System Design: Historical Backfill / Replay Platform](../../system-design/historical-backfill-replay-platform-design.md)

> retrieval-anchor-keywords: JSON null vs missing, unknown property, schema evolution, backward compatibility, forward compatibility, DTO default value, PATCH semantics, record deserialization, unknown field handling, Java JSON mapping, Optional, partial update, replay compatibility, primitive field default, wrapper field null, empty string, blank string

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

JSON 필드에는 최소 세 가지 상태가 있다.

- 값이 있다
- 필드가 명시적으로 `null`이다
- 필드 자체가 없다

그리고 여기에 네 번째 상태가 더해진다.

- 내가 아직 모르는 새 필드가 들어왔다

문제는 많은 Java DTO가 이 차이를 하나의 `null`로 뭉개 버린다는 점이다.  
그러면 다음이 흔들린다.

- PATCH에서 값을 지우려는 것인지, 건드리지 말라는 것인지
- 기본값을 적용해야 하는지
- old consumer가 new producer를 읽을 수 있는지
- 이벤트 replay가 버전 차이를 버틸 수 있는지

## 깊이 들어가기

### 1. `null`과 missing은 같은 뜻이 아니다

예를 들어 사용자 프로필 수정 API에서:

- `"nickname": null` 은 "닉네임을 지워라"일 수 있다
- `nickname` 필드 자체가 없음은 "닉네임은 그대로 둬라"일 수 있다

이 차이를 구분하지 못하면 PATCH semantics가 깨진다.

즉 "값이 없음"은 하나가 아니다.

### 2. unknown field는 forward compatibility 정책 문제다

새 producer가 필드를 추가하면 old consumer는 세 가지 중 하나를 택해야 한다.

- strict fail
- ignore
- raw field를 보존하고 넘긴다

어떤 선택이 맞는지는 경계에 따라 다르다.

- public API contract 검증: strict fail이 맞을 수 있다
- 이벤트 소비/재생성: ignore 또는 preserve가 더 안전할 수 있다

### 3. 기본값 적용 시점이 중요하다

missing field를 만났을 때 언제 default를 넣을지 정해야 한다.

- JSON binding 단계
- DTO -> domain 변환 단계
- domain constructor 단계

너무 이른 기본값 적용은 "필드가 안 왔다"는 정보를 잃게 만들고,  
너무 늦은 적용은 서비스 내부에 미완성 상태를 오래 남긴다.

즉 defaulting은 convenience가 아니라 schema evolution 정책이다.

primitive field를 DTO에 두면 binding 단계에서 default가 너무 일찍 들어가 이 정보가 더 빨리 사라질 수 있다.  
관련해서 [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)을 같이 보면 좋다.

### 4. `Optional` 하나로는 tri-state를 다 표현하지 못한다

많은 경우 `Optional<T>`는 "값 있거나 없음"만 표현한다.  
하지만 JSON PATCH에서는 다음 셋을 구분해야 할 수 있다.

- missing
- explicit null
- present value

그래서 tri-state wrapper나 별도 patch model이 필요할 때가 있다.

### 5. record와 생성자 바인딩은 더 엄격할 수 있다

record는 간결하지만 component가 계약이 되기 쉽다.  
필수 필드 추가나 기본값 없는 component는 old payload와의 호환성을 깨뜨릴 수 있다.

즉 DTO record를 진화시킬 땐:

- 필수/선택 필드 구분
- default 전략
- unknown field 처리

를 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: PATCH가 필드를 의도치 않게 지운다

DTO에서 missing과 `null`이 모두 `null`로 들어왔다.  
서비스는 이를 "clear field"로 해석해 기존 값을 날려버린다.

### 시나리오 2: 새 필드 하나 추가했는데 old consumer가 죽는다

엄격한 unknown-property 실패 정책이 이벤트 소비자에 적용되어 있다.  
롤링 배포 중 old consumer가 new payload를 못 읽고 재시도만 반복한다.

### 시나리오 3: 기본값이 replay semantics를 바꾼다

과거 이벤트에는 필드가 없었는데, 새 코드가 역직렬화 시 기본값을 강제로 넣는다.  
그 결과 재처리 결과가 원래와 달라진다.

### 시나리오 4: record 필수 필드 추가 후 오래된 요청이 깨진다

소스는 깔끔하지만, old client가 아직 그 필드를 보내지 않아 역직렬화 경계가 깨진다.

## 코드로 보기

### 1. tri-state patch 모델 감각

```java
public sealed interface FieldPatch<T> permits Missing, NullValue, Present {}

public record Missing<T>() implements FieldPatch<T> {}

public record NullValue<T>() implements FieldPatch<T> {}

public record Present<T>(T value) implements FieldPatch<T> {}
```

### 2. DTO와 domain apply 분리

```java
public record UserProfilePatch(FieldPatch<String> nickname) {
    public UserProfile applyTo(UserProfile profile) {
        return switch (nickname) {
            case Missing<String> ignored -> profile;
            case NullValue<String> ignored -> profile.clearNickname();
            case Present<String> present -> profile.changeNickname(present.value());
        };
    }
}
```

### 3. unknown field 처리 전략은 boundary마다 다를 수 있다

```java
// public write API는 strict하게,
// event replay consumer는 ignore-or-preserve 전략으로 다르게 볼 수 있다.
```

### 4. record 필수 필드 추가 시 생각할 것

```java
public record PaymentEvent(String id, String type, String region) {}
```

`region`이 새 필수 component라면 old payload와의 호환성 전략을 먼저 정해야 한다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `null`/missing 통합 | 구현이 단순하다 | PATCH와 진화 semantics를 잃는다 |
| tri-state patch 모델 | 의미가 명확하다 | DTO와 변환 코드가 늘어난다 |
| unknown field strict fail | 계약 위반을 빨리 찾는다 | 롤링 배포와 forward compatibility에 취약하다 |
| unknown field ignore/preserve | 진화에 유연하다 | 잘못된 입력을 늦게 발견할 수 있다 |

핵심은 JSON binding을 단순 파싱이 아니라 버전 호환성과 부분 업데이트 계약의 일부로 보는 것이다.

## 꼬리질문

> Q: `null`과 missing을 왜 구분해야 하나요?
> 핵심: 값 삭제와 "건드리지 않음"의 의미가 전혀 다를 수 있기 때문이다.

> Q: unknown field는 무조건 무시하면 되나요?
> 핵심: 경계에 따라 다르다. public write API와 event replay consumer의 정책은 달라질 수 있다.

> Q: `Optional`이면 충분하지 않나요?
> 핵심: missing과 explicit null을 동시에 구분해야 하는 PATCH 모델에는 부족할 수 있다.

> Q: record DTO는 왜 진화에 더 조심해야 하나요?
> 핵심: component 구조가 생성 계약이 되기 쉬워 필수 필드 변경이 바로 호환성 문제로 이어질 수 있기 때문이다.

## 한 줄 정리

JSON 경계에서 `null`, missing, unknown field를 구분하는 것은 파서 취향이 아니라 PATCH semantics와 schema evolution을 지키는 핵심 설계다.
