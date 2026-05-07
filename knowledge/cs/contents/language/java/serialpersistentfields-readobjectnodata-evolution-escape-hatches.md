---
schema_version: 3
title: serialPersistentFields readObjectNoData Evolution Escape Hatches
concept_id: language/serialpersistentfields-readobjectnodata-evolution-escape-hatches
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 85
mission_ids:
- missions/payment
- missions/spring-roomescape
review_feedback_tags:
- serialization
- compatibility
- evolution
aliases:
- serialPersistentFields readObjectNoData evolution escape hatches
- Java serialPersistentFields PutField GetField
- readObjectNoData native serialization
- persistent field schema evolution
- native serialization escape hatch
- 자바 serialPersistentFields readObjectNoData
symptoms:
- native serialization이 현재 non-transient field에 끌려가는 기본 동작만 알고 serialPersistentFields로 저장 계약을 분리할 수 있는 경우를 놓쳐
- putFields readFields mapping 코드를 migration layer로 다루지 않고 serializer hook 정도로만 생각해 compatibility reasoning이 불투명해져
- readObjectNoData가 hierarchy evolution 같은 edge case의 safety net이지 일반 복구 로직이 아니라는 점을 구분하지 못해
intents:
- deep_dive
- design
- comparison
prerequisites:
- language/serialization-compatibility-serial-version-uid
- language/serialization-proxy-pattern-invariant-preservation
- language/record-serialization-evolution
next_docs:
- language/value-object-invariants-canonicalization-boundary-design
- language/json-null-missing-unknown-field-schema-evolution
- language/io-nio-serialization
linked_paths:
- contents/language/java/serialization-compatibility-serial-version-uid.md
- contents/language/java/serialization-proxy-pattern-invariant-preservation.md
- contents/language/java/record-serialization-evolution.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
confusable_with:
- language/serialization-proxy-pattern-invariant-preservation
- language/serialization-compatibility-serial-version-uid
- language/record-serialization-evolution
forbidden_neighbors: []
expected_queries:
- serialPersistentFields는 실제 클래스 필드와 별개로 persistent field schema를 어떻게 통제해?
- ObjectOutputStream PutField와 ObjectInputStream GetField는 serialization migration layer처럼 쓰이는 이유가 뭐야?
- readObjectNoData는 class hierarchy evolution에서 언제 호출될 수 있는 escape hatch야?
- serialPersistentFields는 serialization proxy보다 경계를 덜 분리하지만 언제 유용할 수 있어?
- native serialization evolution escape hatch는 강력하지만 왜 reasoning 비용이 커져?
contextual_chunk_prefix: |
  이 문서는 Java native serialization에서 serialPersistentFields, PutField/GetField, readObjectNoData를 field schema evolution escape hatch로 설명하는 advanced deep dive다.
  serialPersistentFields, readObjectNoData, PutField, GetField, serialization evolution 질문이 본 문서에 매핑된다.
---
# `serialPersistentFields`, `readObjectNoData`, and Native Serialization Evolution Escape Hatches

> 한 줄 요약: Java native serialization은 기본적으로 현재 필드 구조에 끌려가지만, `serialPersistentFields`와 `readObjectNoData()`는 그 계약을 부분적으로 통제할 수 있는 escape hatch다. 다만 강력한 대신 더 쉽게 불투명한 호환성 코드를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Serialization Compatibility and `serialVersionUID`](./serialization-compatibility-serial-version-uid.md)
> - [Serialization Proxy Pattern and Invariant Preservation](./serialization-proxy-pattern-invariant-preservation.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)

> retrieval-anchor-keywords: serialPersistentFields, readObjectNoData, putFields, readFields, native serialization evolution, persistent field schema, hierarchy change, InvalidObjectException, serialization hook, backward compatibility, forward compatibility

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

기본 native serialization은 "현재 non-transient 필드"를 중심으로 움직인다.  
하지만 실제 운영에서는 저장 계약을 조금 더 의식적으로 통제하고 싶을 때가 있다.

그때 등장하는 도구가:

- `serialPersistentFields`
- `ObjectOutputStream.PutField` / `ObjectInputStream.GetField`
- `readObjectNoData()`

이다.

즉 이 기능들은 serialization proxy만큼 경계를 완전히 분리하진 못하지만,  
기본 직렬화보다 더 명시적인 field contract를 만들게 해준다.

## 깊이 들어가기

### 1. `serialPersistentFields`는 "저장할 필드 목록"을 직접 적는 방식이다

이 기능을 쓰면 실제 클래스 필드와 별개로  
"직렬화 포맷에 포함할 persistent field 목록"을 명시할 수 있다.

즉 다음 같은 용도에 쓸 수 있다.

- 내부 필드는 바꿨지만 저장 계약은 유지하고 싶다
- derived field를 저장에서 빼고 싶다
- 필드 이름/구성을 더 안정적으로 유지하고 싶다

하지만 그만큼 기본 직렬화의 단순함을 버린다.

### 2. `putFields`/`readFields`는 명시적 mapping 레이어다

이 방식은 사실상 "작은 schema mapping"을 직접 쓰는 것이다.

- 어떤 이름으로 저장할지
- 없는 필드를 어떻게 기본값 처리할지
- 읽은 뒤 어떻게 현재 객체 상태로 옮길지

즉 이 코드는 serializer hook이면서 migration code다.

### 3. `readObjectNoData()`는 hierarchy 변화 같은 edge case를 다룬다

이 메서드는 stream에 해당 클래스 데이터가 없을 때 호출될 수 있다.  
예를 들어 class hierarchy가 바뀌었거나 예상과 다른 형태의 stream을 읽을 때 의미가 생긴다.

일반 서비스 코드에서 자주 쓰이진 않지만,  
오래된 직렬화 데이터와 class evolution이 복잡하게 얽힌 경우엔 마지막 safety net 역할을 할 수 있다.

### 4. 이 escape hatch들은 복잡도를 줄이지 않는다

중요한 점은:

- 호환성 통제는 좋아질 수 있다
- 하지만 reasoning 비용은 크게 증가한다

즉 이 기능들은 "쉽게 만드는 도구"가 아니라  
"어쩔 수 없이 기본 직렬화 위에서 계약을 더 명시하는 도구"에 가깝다.

### 5. value object와 장기 저장 포맷에서는 proxy나 schema DTO가 더 자주 낫다

`serialPersistentFields`가 쓸모 없다는 뜻은 아니다.  
다만 value object invariant와 장기 포맷 진화까지 생각하면,

- serialization proxy
- 명시적 JSON/schema DTO

가 더 읽기 쉽고 운영하기 쉬운 경우가 많다.

## 실전 시나리오

### 시나리오 1: 내부 필드 구조를 바꾸고도 저장 포맷은 유지하고 싶다

이전엔 `firstName`, `lastName`을 저장했는데,  
현재 객체는 `displayName` 하나만 가진다.

기본 직렬화만 믿으면 깨지기 쉽지만, persistent field mapping을 두면 완충이 가능하다.

### 시나리오 2: 클래스 계층 변화 후 오래된 데이터가 애매하게 읽힌다

stream에는 특정 superclass 데이터가 없는데 현재 클래스 계층에는 생겼다.  
이런 edge case에서 `readObjectNoData()`를 통해 안전한 기본 상태를 강제할 수 있다.

### 시나리오 3: 호환성 코드는 늘었는데 아무도 이해 못 한다

escape hatch를 과하게 쓰면 "돌아가긴 하는데 왜 그런지 모르는" serialization layer가 된다.  
이 경우는 차라리 proxy나 명시적 schema로 갈아타는 편이 낫다.

## 코드로 보기

### 1. persistent field 목록 명시

```java
import java.io.ObjectStreamField;
import java.io.Serializable;

public final class LegacyUser implements Serializable {
    private static final ObjectStreamField[] serialPersistentFields = {
        new ObjectStreamField("userId", String.class),
        new ObjectStreamField("displayName", String.class)
    };

    private final String userId;
    private final String displayName;

    public LegacyUser(String userId, String displayName) {
        this.userId = userId;
        this.displayName = displayName;
    }
}
```

### 2. 명시적 write/read mapping

```java
private void writeObject(java.io.ObjectOutputStream out) throws java.io.IOException {
    java.io.ObjectOutputStream.PutField fields = out.putFields();
    fields.put("userId", userId);
    fields.put("displayName", displayName);
    out.writeFields();
}

private void readObject(java.io.ObjectInputStream in) throws java.io.IOException, ClassNotFoundException {
    java.io.ObjectInputStream.GetField fields = in.readFields();
    String restoredUserId = (String) fields.get("userId", null);
    String restoredDisplayName = (String) fields.get("displayName", "");
    if (restoredUserId == null) {
        throw new java.io.InvalidObjectException("userId missing");
    }
}
```

### 3. no data edge case

```java
private void readObjectNoData() throws java.io.ObjectStreamException {
    throw new java.io.InvalidObjectException("required serialized data missing");
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| 기본 직렬화 | 단순하다 | field 구조 변화에 끌려가고 계약 통제가 약하다 |
| `serialPersistentFields` + mapping | 필드 계약을 더 명시할 수 있다 | hook 코드와 migration complexity가 커진다 |
| serialization proxy | invariant와 boundary control이 더 명확하다 | 보일러플레이트가 늘어난다 |
| JSON/schema DTO | 상호운용성과 가독성이 높다 | 별도 DTO와 변환 계층이 필요하다 |

핵심은 이 기능들을 편의 기능이 아니라 "기본 직렬화의 부족함을 메우는 escape hatch"로 보는 것이다.

## 꼬리질문

> Q: `serialPersistentFields`는 언제 의미가 있나요?
> 핵심: 실제 클래스 필드와 저장 계약을 약간 분리해 유지하고 싶을 때 의미가 있다.

> Q: `readObjectNoData()`는 왜 존재하나요?
> 핵심: hierarchy 변화나 예상치 못한 stream 형태에서 해당 클래스 데이터가 없을 때 안전한 기본 동작을 정의하기 위해서다.

> Q: 이 기능들을 쓰면 native serialization이 안전해지나요?
> 핵심: 더 통제할 수는 있지만, 복잡도와 reasoning 비용도 크게 늘어난다.

> Q: 언제 proxy나 DTO가 더 낫나요?
> 핵심: invariant가 중요하고 장기 진화가 필요한 대부분의 서비스 코드에선 더 읽기 쉽고 운영하기 좋다.

## 한 줄 정리

`serialPersistentFields`와 `readObjectNoData()`는 native serialization 위에서 계약을 더 명시하는 탈출구이지만, 강한 만큼 복잡도도 커서 정말 필요한 곳에만 써야 한다.
