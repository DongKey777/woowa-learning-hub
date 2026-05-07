---
schema_version: 3
title: Record Serialization Evolution
concept_id: language/record-serialization-evolution
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
- record
- serialization
- compatibility
aliases:
- Record Serialization Evolution
- record serialization canonical constructor
- record component change compatibility
- serialization proxy record invariant
- record serialVersionUID evolution
- 자바 record 직렬화 진화
symptoms:
- record 선언이 간결하다는 이유로 component 목록과 canonical constructor가 serialization contract가 된다는 점을 놓쳐
- record component 추가나 타입 변경을 단순 refactor로 보고 old serialized data와 JSON payload compatibility 영향을 고려하지 않아
- compact constructor normalization이나 validation 변경이 과거 데이터 역직렬화 의미를 바꿀 수 있다는 점을 놓쳐
intents:
- deep_dive
- design
- comparison
prerequisites:
- language/serialization-compatibility-serial-version-uid
- language/serialization-proxy-pattern-invariant-preservation
- language/records-sealed-pattern-matching
next_docs:
- language/record-sealed-hierarchy-evolution-pattern-matching-compatibility
- language/enum-persistence-json-unknown-value-evolution
- language/value-object-invariants-canonicalization-boundary-design
linked_paths:
- contents/language/java/serialization-compatibility-serial-version-uid.md
- contents/language/java/serialization-proxy-pattern-invariant-preservation.md
- contents/language/java/records-sealed-pattern-matching.md
- contents/language/java/record-sealed-hierarchy-evolution-pattern-matching-compatibility.md
- contents/language/java/io-nio-serialization.md
- contents/language/java/enum-persistence-json-unknown-value-evolution.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
- contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md
- contents/language/java/class-initialization-ordering.md
confusable_with:
- language/serialization-compatibility-serial-version-uid
- language/serialization-proxy-pattern-invariant-preservation
- language/record-sealed-hierarchy-evolution-pattern-matching-compatibility
forbidden_neighbors: []
expected_queries:
- record serialization에서 component와 canonical constructor가 compatibility contract가 되는 이유가 뭐야?
- record component를 추가하면 old serialized data나 JSON payload compatibility가 어떻게 깨질 수 있어?
- compact constructor의 validation이나 normalization 변경이 과거 데이터 복원에 어떤 영향을 줘?
- record를 장기 저장 포맷으로 쓸 때 serialization proxy가 더 안전할 수 있는 이유가 뭐야?
- record와 serialVersionUID, readResolve, value object invariant를 함께 고려하는 방법을 설명해줘
contextual_chunk_prefix: |
  이 문서는 Java record를 serialization format으로 쓸 때 component evolution, canonical constructor, compact constructor, serialization proxy, invariant compatibility를 다루는 advanced deep dive다.
  record serialization, canonical constructor, component evolution, serialization proxy, compatibility 질문이 본 문서에 매핑된다.
---
# Record Serialization Evolution

> 한 줄 요약: record는 선언이 간결하지만 serialization 계약은 여전히 타입/필드 진화 규칙을 따른다. record를 직렬화 포맷으로 쓸 때는 canonical constructor와 필드 변경이 호환성에 미치는 영향을 꼭 따져야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Serialization Compatibility and `serialVersionUID`](./serialization-compatibility-serial-version-uid.md)
> - [Serialization Proxy Pattern and Invariant Preservation](./serialization-proxy-pattern-invariant-preservation.md)
> - [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)
> - [Record/Sealed Hierarchy Evolution and Pattern Matching Compatibility](./record-sealed-hierarchy-evolution-pattern-matching-compatibility.md)
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
> - [Class Initialization Ordering](./class-initialization-ordering.md)

> retrieval-anchor-keywords: record serialization, canonical constructor, serialization evolution, `serialVersionUID`, compact constructor, component change, serialization proxy, `readResolve`, immutability, schema compatibility, canonicalization, value object normalization, enum evolution, value object invariant, sealed hierarchy evolution

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

record는 값 객체를 간결하게 표현하는 방식이다.  
하지만 serialization 관점에서는 결국 component 목록과 canonical constructor가 포맷 계약이 된다.

즉 "record니까 안전할 것"이 아니라,  
record도 포맷 변화와 호환성 문제에서 자유롭지 않다.

## 깊이 들어가기

### 1. record의 직렬화는 component 중심으로 읽어야 한다

record의 각 component는 사실상 데이터 계약이다.  
component를 추가, 제거, 타입 변경하면 역직렬화 호환성에 영향을 줄 수 있다.

### 2. canonical constructor가 의미하는 것

record는 canonical constructor를 통해 컴포넌트를 완성한다.  
직렬화 복원 시 이 생성 경로가 중요하다.

즉 validation 규칙을 넣을 수 있지만, 그만큼 이전 데이터가 새 규칙을 만족하지 못할 위험도 있다.

### 3. compact constructor는 편하지만 진화 규칙이 필요하다

compact constructor에서 정규화(normalization)를 넣을 수 있다.  
그렇지만 이 로직이 바뀌면 과거 직렬화 데이터의 의미도 달라질 수 있다.

### 4. serialization proxy가 더 안전할 수 있다

record 자체를 포맷으로 바로 노출하기보다, serialization proxy를 두어 내부 구조 변화와 포맷을 분리하는 편이 안전할 수 있다.
이 패턴은 [Serialization Proxy Pattern and Invariant Preservation](./serialization-proxy-pattern-invariant-preservation.md)에서 더 자세히 다룬다.

## 실전 시나리오

### 시나리오 1: record component를 추가하고 오래된 데이터를 읽어야 한다

포맷이 깨질 수 있으므로, 먼저 호환성을 고려해야 한다.  
필드 추가가 항상 무해하지 않다.

### 시나리오 2: validation이 더 엄격해졌다

새 canonical constructor가 이전 데이터를 거부할 수 있다.  
이 경우 마이그레이션이나 proxy 전략이 필요하다.

### 시나리오 3: record를 장기 저장 포맷으로 쓰고 있다

그렇다면 native serialization에 기록된 데이터의 수명과 class evolution 정책을 명확히 해야 한다.  
가능하면 명시적 schema 포맷을 검토하는 편이 낫다.

## 코드로 보기

### 1. record 직렬화 감각

```java
import java.io.Serializable;

public record UserSnapshot(String id, String name) implements Serializable {}
```

### 2. component 정규화

```java
public record Email(String value) {
    public Email {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("blank");
        }
    }
}
```

### 3. evolution 위험

```java
// record component를 바꾸는 것은 API 변경이자 serialization 계약 변경이다.
```

### 4. proxy로 포맷 분리

```java
// 내부 record를 외부 포맷과 직접 묶지 말고
// proxy DTO를 두는 방식도 고려할 수 있다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| record 직렬화 직접 사용 | 구현이 단순하다 | 진화 규칙이 민감하다 |
| proxy 사용 | 포맷을 분리할 수 있다 | 코드가 늘어난다 |
| JSON/schema | 호환성 관리가 쉽다 | 직렬화 코드가 더 필요하다 |
| native serialization 유지 | 기존 호환을 계속 쓸 수 있다 | 장기 유지보수 위험이 있다 |

핵심은 record의 선언적 장점과 serialization의 진화 규칙을 분리해서 보는 것이다.

## 꼬리질문

> Q: record는 serialization에 더 안전한가요?
> 핵심: 간결하지만 안전성이 자동으로 생기지는 않고 component 변경에 여전히 민감하다.

> Q: canonical constructor는 왜 중요한가요?
> 핵심: record 복원과 validation의 핵심 경로이기 때문이다.

> Q: record를 장기 포맷으로 써도 되나요?
> 핵심: 가능은 하지만 호환성 관리가 필요하고, proxy나 schema 포맷이 더 안전할 수 있다.

## 한 줄 정리

record는 직렬화에 편리하지만, component와 canonical constructor가 곧 포맷 계약이므로 진화 규칙을 별도로 설계해야 한다.
