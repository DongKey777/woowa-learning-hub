---
schema_version: 3
title: Primitive vs Wrapper Fields in JSON Payload Semantics
concept_id: language/primitive-vs-wrapper-fields-json-payload-semantics
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/spring-roomescape
- missions/payment
review_feedback_tags:
- dto
- json
- primitive-wrapper
aliases:
- Primitive vs Wrapper Fields in JSON Payload Semantics
- int vs Integer JSON payload semantics
- boolean vs Boolean missing explicit null
- primitive wrapper DTO defaulting
- API payload binding tri-state
- 자바 DTO primitive wrapper JSON 의미
symptoms:
- DTO primitive field를 쓰면서 missing field와 explicit null이 default false나 0으로 뭉개질 수 있는 payload contract 차이를 놓쳐
- Integer Boolean wrapper를 쓰면 tri-state 표현 공간은 생기지만 null 의미가 자동으로 정해지는 것은 아니라는 점을 문서화하지 않아
- create API, PATCH API, event replay, backward compatibility 경계에서 primitive와 wrapper 선택을 취향이나 style 문제로만 처리해
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/java-autoboxing-integercache-null-unboxing-pitfalls
- language/json-null-missing-unknown-field-schema-evolution
- language/empty-string-blank-null-missing-payload-semantics
next_docs:
- language/patch-tri-state-field-primer
- language/optional-vs-fieldpatch-patch-tri-state-bridge
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
linked_paths:
- contents/language/java/autoboxing-integercache-null-unboxing-pitfalls.md
- contents/language/java/json-null-missing-unknown-field-schema-evolution.md
- contents/language/java/empty-string-blank-null-missing-payload-semantics.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
- contents/language/java/io-nio-serialization.md
confusable_with:
- language/json-null-missing-unknown-field-schema-evolution
- language/patch-tri-state-field-primer
- language/optional-vs-fieldpatch-patch-tri-state-bridge
forbidden_neighbors: []
expected_queries:
- JSON DTO에서 int와 Integer, boolean과 Boolean 선택은 payload contract로 어떻게 달라?
- primitive field를 쓰면 missing과 explicit null이 default value로 뭉개질 수 있다는 뜻을 설명해줘
- wrapper field는 tri-state를 열어주지만 null 의미를 자동으로 정하지 않는다는 게 무슨 말이야?
- create API와 PATCH API에서 primitive wrapper 선택 기준이 왜 달라질 수 있어?
- backward compatibility와 event replay에서 DTO defaulting이 위험해지는 사례를 알려줘
contextual_chunk_prefix: |
  이 문서는 JSON payload DTO에서 primitive vs wrapper field 선택이 missing, explicit null, default value, PATCH tri-state, API compatibility에 미치는 의미를 점검하는 advanced playbook이다.
  primitive vs wrapper, int Integer, boolean Boolean, JSON missing null, DTO defaulting 질문이 본 문서에 매핑된다.
---
# Primitive vs Wrapper Fields in JSON Payload Semantics

> 한 줄 요약: API DTO에서 `int`/`Integer`, `boolean`/`Boolean` 선택은 취향이 아니라 payload contract다. primitive를 쓰면 missing과 explicit `null`이 기본값으로 뭉개질 수 있고, wrapper를 쓰면 tri-state가 생기므로 PATCH, defaulting, backward compatibility가 달라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
> - [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
> - [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)

> retrieval-anchor-keywords: primitive vs wrapper field, JSON payload semantics, int vs Integer, boolean vs Boolean, default value binding, absent field, explicit null, DTO defaulting, PATCH semantics, tri-state boolean, API compatibility, payload binding, empty string, blank string

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

JSON payload를 Java DTO로 받을 때 field 타입은 곧 의미 선택이다.

- primitive field: null이 없고 기본값이 있다
- wrapper field: null이 가능하고 "값 없음"을 담을 수 있다

그래서 다음 세 상태를 구분할 수 있는지가 달라진다.

- 값이 명시적으로 왔다
- 필드가 아예 안 왔다
- 필드가 `null`로 왔다

이 차이는 PATCH, create API, event replay, old client compatibility에서 크게 드러난다.

## 깊이 들어가기

### 1. primitive는 바인딩 후 의미를 잃기 쉽다

`int`, `long`, `boolean`은 바인딩이 끝난 시점에 항상 값이 있다.  
문제는 그 값이 "실제 payload 값"인지 "기본값"인지 분간하기 어려워진다는 점이다.

예:

- `boolean enabled`는 `false`가 왔는지
- 아예 안 왔는데 default `false`가 들어간 건지

를 DTO만 보고 구분하기 어렵다.

즉 primitive field는 create command처럼 "필수이며 항상 값이 있어야 하는" 경우엔 잘 맞지만,  
partial update나 backward compatibility 경계엔 쉽게 위험해진다.

### 2. wrapper는 tri-state를 만들지만, 그 자체로 정책은 아니다

`Integer`, `Boolean`, `Long`을 쓰면 `null`을 담을 수 있다.  
그래서 다음이 가능해진다.

- `true`
- `false`
- `null`

하지만 `null`이 무엇을 뜻하는지는 여전히 따로 정해야 한다.

- missing과 같은가
- explicit null과 같은가
- "아직 모름"인가

즉 wrapper는 표현 공간을 열어줄 뿐, 의미를 자동으로 정해주지는 않는다.

### 3. create API와 PATCH API는 다른 모델이 필요할 수 있다

create command에서는 다음이 자연스럽다.

- 필수 필드: primitive 또는 non-null value object
- 선택 필드: wrapper/value object nullable

반면 PATCH는 보통 tri-state가 필요하다.

- 바꾸지 않음
- 명시적으로 비움
- 새 값으로 바꿈

이때 primitive field는 표현력이 부족할 수 있다.

### 4. Boolean flag는 특히 오해가 많다

`boolean active`는 간단해 보이지만 payload semantics가 붙으면 복잡해진다.

- 가입 시 기본값이 `true`인가
- 요청에서 안 보내면 서버 default를 넣는가
- PATCH에서 `false`와 missing을 구분해야 하는가

즉 boolean은 binary value지만, API contract는 종종 binary가 아니다.

### 5. DTO 기본값과 도메인 기본값은 다를 수 있다

바인딩 단계에서 기본값을 일찍 넣어버리면 "클라이언트가 안 보냈다"는 정보가 사라진다.  
그래서 서버가 진짜 default policy를 적용할 기회를 잃는다.

이 때문에 많은 시스템은:

- DTO는 raw intent를 보존
- domain command 변환 시 default 정책 적용

방식을 택한다.

## 실전 시나리오

### 시나리오 1: PATCH 요청이 의도치 않게 `false`를 넣는다

DTO에 `boolean marketingOptIn`이 있다.  
클라이언트가 필드를 안 보냈는데 바인딩 후 `false`가 들어가서 기존 동의값을 덮어쓴다.

### 시나리오 2: old client가 새 필드를 안 보내도 의미가 바뀐다

새 필드 `int retryLimit`을 추가했는데 primitive default `0`이 들어간다.  
old client는 그냥 모르는 필드를 안 보낸 것뿐인데, 서버는 이를 명시적 0으로 해석한다.

### 시나리오 3: `Boolean`을 썼더니 서비스 내부 NPE가 생긴다

payload 단계에선 tri-state가 유용했지만,  
도메인 코드에서 곧바로 `if (enabled)` 같은 unboxing을 해버리면 runtime bug가 난다.

### 시나리오 4: record DTO가 너무 단순해 보여 함정이 숨어든다

record component에 primitive를 쓰면 compact constructor에 들어왔을 때 이미 기본값이 들어가 있을 수 있다.  
즉 "payload에 없었다"는 정보를 record constructor가 알기 어렵다.

## 코드로 보기

### 1. create command 감각

```java
public record CreateUserRequest(
    String email,
    boolean marketingOptIn
) {}
```

이 모델은 `marketingOptIn`이 항상 payload에 있어야 하는 계약일 때만 자연스럽다.

### 2. PATCH 모델 감각

```java
public record UpdateUserRequest(
    FieldPatch<Boolean> marketingOptIn
) {}
```

partial update라면 primitive보다 tri-state 모델이 더 잘 맞을 수 있다.

### 3. wrapper를 domain으로 바로 넘기지 않기

```java
public record RetryPolicy(Integer retryLimit) {
    public int normalizedRetryLimit() {
        return retryLimit == null ? 3 : retryLimit;
    }
}
```

default 정책 적용 지점을 명시하는 편이 안전하다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| primitive field | 단순하고 null이 없다 | missing과 default를 구분하기 어렵다 |
| wrapper field | payload intent를 더 많이 보존한다 | tri-state 의미와 null 처리 정책이 필요하다 |
| tri-state patch model | PATCH semantics가 명확하다 | DTO와 변환 코드가 늘어난다 |
| domain default later | 클라이언트 intent를 덜 잃는다 | 변환 계층 설계가 필요하다 |

핵심은 DTO field 타입이 구현 편의가 아니라 payload meaning을 결정한다는 점이다.

## 꼬리질문

> Q: DTO에서 primitive를 쓰면 왜 위험할 수 있나요?
> 핵심: 바인딩 후 default 값이 들어가며 missing과 explicit value를 구분하기 어려워질 수 있기 때문이다.

> Q: wrapper를 쓰면 항상 더 좋은가요?
> 핵심: 아니다. tri-state를 열어주지만 null semantics를 따로 설계해야 한다.

> Q: PATCH에 boolean field 하나만 있으면 충분한가요?
> 핵심: 보통은 부족하다. unchanged, clear, set을 구분해야 할 수 있다.

> Q: DTO default와 domain default를 왜 나누나요?
> 핵심: 너무 이른 defaulting은 클라이언트가 실제로 보낸 intent를 잃게 만들 수 있기 때문이다.

## 한 줄 정리

API DTO에서 primitive와 wrapper 선택은 단순 타입 선택이 아니라 missing, null, default, partial update 의미를 어디까지 보존할지 정하는 계약이다.
