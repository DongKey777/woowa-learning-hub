---
schema_version: 3
title: Serialization Compatibility and serialVersionUID
concept_id: language/serialization-compatibility-serial-version-uid
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/payment
- missions/spring-roomescape
review_feedback_tags:
- serialization
- compatibility
- serialversionuid
aliases:
- Serialization Compatibility and serialVersionUID
- Java native serialization serialVersionUID
- Serializable ObjectInputStream compatibility
- readObject writeObject readResolve writeReplace
- serialPersistentFields transient invariant
- 자바 serialVersionUID 호환성
symptoms:
- serialVersionUID를 명시하지 않아 작은 필드나 class 구조 변경이 저장 데이터 역직렬화 호환성을 예측하기 어렵게 만들어
- Java native serialization을 단순 DTO 복사처럼 이해해 readObject writeObject readResolve writeReplace transient invariant 복구 경로를 놓쳐
- 장기 저장 포맷으로 native serialization을 쓰면서 schema evolution, null vs missing, classloader memory leak 위험을 함께 검토하지 않아
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/io-nio-serialization
- language/serialization-proxy-pattern-invariant-preservation
- language/value-object-invariants-canonicalization-boundary-design
next_docs:
- language/serialpersistentfields-readobjectnodata-evolution-escape-hatches
- language/record-serialization-evolution
- language/json-null-missing-unknown-field-schema-evolution
linked_paths:
- contents/language/java/io-nio-serialization.md
- contents/language/java/serialization-proxy-pattern-invariant-preservation.md
- contents/language/java/serialpersistentfields-readobjectnodata-evolution-escape-hatches.md
- contents/language/java/record-serialization-evolution.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
- contents/language/java/json-null-missing-unknown-field-schema-evolution.md
- contents/language/java/classloader-memory-leak-playbook.md
- contents/language/java/string-intern-pool-pitfalls.md
- contents/language/java-memory-model-happens-before-volatile-final.md
confusable_with:
- language/serialization-proxy-pattern-invariant-preservation
- language/serialpersistentfields-readobjectnodata-evolution-escape-hatches
- language/record-serialization-evolution
forbidden_neighbors: []
expected_queries:
- Java native serialization에서 serialVersionUID는 역직렬화 compatibility를 어떻게 판단해?
- serialVersionUID를 자동 생성에 맡기면 작은 리팩터링도 저장 데이터 호환성을 깨뜨릴 수 있어?
- readObject writeObject readResolve writeReplace transient는 serialization contract에서 어떤 역할을 해?
- native serialization을 장기 저장 포맷으로 쓰면 schema evolution과 value object invariant를 어떻게 봐야 해?
- serialPersistentFields와 serialization proxy는 serialVersionUID 문제와 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 Java native serialization compatibility와 serialVersionUID, readObject/writeObject hooks, transient invariant, schema evolution risk를 점검하는 advanced playbook이다.
  serialVersionUID, Serializable, ObjectInputStream, compatibility, readObject, serialization evolution 질문이 본 문서에 매핑된다.
---
# Serialization Compatibility and `serialVersionUID`

> 한 줄 요약: Java native serialization은 클래스 구조와 직렬화 계약이 강하게 묶이므로, `serialVersionUID`를 이해하지 못하면 작은 필드 변경도 역직렬화 호환성을 깨뜨릴 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [Serialization Proxy Pattern and Invariant Preservation](./serialization-proxy-pattern-invariant-preservation.md)
> - [`serialPersistentFields`, `readObjectNoData`, and Native Serialization Evolution Escape Hatches](./serialpersistentfields-readobjectnodata-evolution-escape-hatches.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [String Intern and Pool Pitfalls](./string-intern-pool-pitfalls.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)

> retrieval-anchor-keywords: serialization compatibility, `serialVersionUID`, `Serializable`, `ObjectInputStream`, `ObjectOutputStream`, readObject, writeObject, default serialization, schema evolution, backward compatibility, forward compatibility, serial persistent fields, transient, value object invariant, null vs missing field, serialization proxy, writeReplace, readResolve, readObjectNoData, putFields, readFields

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

Java native serialization은 객체의 필드와 타입 정보를 바이트 형태로 저장한다.  
문제는 이 포맷이 "현재 클래스 구현"에 강하게 의존한다는 점이다.

`serialVersionUID`는 역직렬화 시 클래스 버전이 호환되는지 판단하는 식별자다.  
명시적으로 선언하지 않으면 컴파일러와 JVM이 자동 계산한 값에 의존하게 된다.

### 왜 이게 중요한가

- 필드 추가/삭제가 잦으면 호환성이 흔들린다
- 클래스 이름은 같아도 구조가 달라지면 역직렬화가 깨질 수 있다
- 장기 저장 포맷으로는 운영 리스크가 크다

## 깊이 들어가기

### 1. 자동 생성 `serialVersionUID`는 왜 위험한가

`serialVersionUID`를 명시하지 않으면 클래스 내부 변경이 곧 버전 변경으로 이어질 수 있다.

예를 들어 다음은 모두 호환성에 영향을 줄 수 있다.

- 필드 추가
- 필드 타입 변경
- 접근 제어자 변경
- 상속 구조 변경
- `private` helper 추가가 계산 결과에 영향을 주는 경우

작은 리팩터링이 저장 데이터와의 계약을 깨뜨릴 수 있다는 뜻이다.

### 2. 역직렬화는 필드만 복원하는 과정이 아니다

serialization은 단순한 DTO 복사가 아니다.

- `readObject`
- `writeObject`
- `readResolve`
- `writeReplace`
- `serialPersistentFields`

같은 hooks가 개입할 수 있다.  
즉 포맷 호환성은 필드 목록뿐 아니라 클래스의 커스텀 로직에도 달려 있다.

이 중 `serialPersistentFields`, `PutField`/`GetField`, `readObjectNoData()` 같은 escape hatch는 [serialPersistentFields, readObjectNoData, and Native Serialization Evolution Escape Hatches](./serialpersistentfields-readobjectnodata-evolution-escape-hatches.md)에서 더 자세히 다룬다.

### 3. `transient`는 계약의 일부다

`transient` 필드는 직렬화 대상에서 빠진다.  
그 자체는 단순해 보이지만, 복원 후 객체 불변식(invariant)을 다시 세워야 할 수 있다.

이 감각은 value object에서 특히 중요하다.  
정규화와 invariant를 생성 시점에 보장했다면 역직렬화 경로도 같은 의미를 회복해야 한다.

예를 들어 다음 항목은 `transient`로 놓기 쉽다.

- 캐시
- derived field
- 보안 민감 정보
- runtime-only handle

그런데 이 값이 객체 의미에 꼭 필요하면 `readObject`에서 재구성 로직이 필요하다.

### 4. class evolution은 backward와 forward를 나눠 봐야 한다

- backward compatibility: 새 코드가 옛 데이터를 읽을 수 있는가
- forward compatibility: 옛 코드가 새 데이터를 읽을 수 있는가

실무에서는 대개 backward compatibility를 우선한다.  
예전 데이터가 남아 있는 시간이 길기 때문이다.

## 실전 시나리오

### 시나리오 1: 배포 후 오래된 캐시를 못 읽는다

클래스 구조를 바꾸고 나서 예전 파일, 세션, 캐시 데이터를 읽지 못하는 경우다.  
이때 `InvalidClassException`이 대표적인 증상이다.

점검 순서:

1. `serialVersionUID`가 명시돼 있는지 본다
2. 필드 변경 내역을 본다
3. 커스텀 serialization hook이 있는지 본다
4. 저장 포맷을 native serialization에 의존하고 있는지 본다

### 시나리오 2: 필드를 하나 추가했는데 장애가 난다

native serialization은 "호환되는 변경"의 범위가 좁다.  
필드 추가가 항상 안전한 것도 아니고, 삭제가 항상 안전한 것도 아니다.

### 시나리오 3: 클래스명만 같으면 된다고 생각한다

클래스명은 같아도 `serialVersionUID`나 필드 구조가 다르면 호환되지 않을 수 있다.  
이 점 때문에 장기 저장 포맷으로는 JSON이나 명시적 schema를 더 자주 선택한다.

## 코드로 보기

### 1. 명시적 `serialVersionUID`

```java
import java.io.Serializable;

public class UserProfile implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String userId;
    private transient String cachedDisplayName;

    public UserProfile(String userId) {
        this.userId = userId;
    }

    public String userId() {
        return userId;
    }
}
```

### 2. 커스텀 복원 로직

```java
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.Serializable;

public class SessionToken implements Serializable {
    private static final long serialVersionUID = 1L;

    private String tokenValue;
    private transient boolean expired;

    private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
        in.defaultReadObject();
        this.expired = false;
    }
}
```

### 3. 호환성에 안전한 방향으로 바꾸기

```java
// 장기 저장 포맷은 native serialization보다
// 명시적 JSON/schema DTO가 더 예측 가능하다.
```

### 4. 역직렬화 예외를 봐야 하는 지점

```java
try (ObjectInputStream in = new ObjectInputStream(inputStream)) {
    Object value = in.readObject();
}
```

문제가 나면 `InvalidClassException`, `StreamCorruptedException` 같은 예외를 통해 계약 위반을 먼저 의심한다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| native serialization | 구현이 빠르다 | 호환성과 보안 리스크가 크다 |
| 명시적 `serialVersionUID` | 버전 제어가 가능하다 | 변경 규칙을 팀이 지켜야 한다 |
| 커스텀 hooks | 진화 전략을 넣을 수 있다 | 복잡도가 높다 |
| JSON / schema 포맷 | 명시적이고 디버깅이 쉽다 | 코드가 더 필요하다 |

핵심은 "직렬화가 된다"와 "오래 안전하게 유지된다"를 분리해서 보는 것이다.

## 꼬리질문

> Q: `serialVersionUID`를 왜 명시하나요?
> 핵심: 자동 계산에 의존하면 사소한 구현 변경도 호환성 깨짐으로 이어질 수 있기 때문이다.

> Q: `transient` 필드는 왜 위험할 수 있나요?
> 핵심: 직렬화에서 빠진 뒤 복원 시 객체 불변식을 다시 만들어야 하기 때문이다.

> Q: native serialization을 장기 저장에 잘 안 쓰는 이유는 무엇인가요?
> 핵심: 클래스 구조 변화와 보안 문제에 취약하고 진화 규칙이 불명확하기 때문이다.

## 한 줄 정리

`serialVersionUID`는 native serialization의 버전 계약이고, 구조 변화가 잦거나 장기 보관이 필요하면 명시적 포맷으로 바꾸는 게 더 안전하다.
