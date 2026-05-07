---
schema_version: 3
title: Insecure Deserialization / Gadget Chains
concept_id: security/insecure-deserialization-gadget-chains
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- insecure deserialization
- gadget chain
- object injection
- type confusion
aliases:
- insecure deserialization
- gadget chain
- object injection
- type confusion
- polymorphic deserialization
- Java serialization
- YAML payload
- JSON polymorphism
- whitelist
- allowlist
- unsafe parser
- Insecure Deserialization / Gadget Chains
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/sql-injection-beyond-preparedstatement.md
- contents/security/secret-management-rotation-leak-patterns.md
- contents/spring/spring-security-architecture.md
- contents/security/xss-csrf-spring-security.md
- contents/security/jwt-deep-dive.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Insecure Deserialization / Gadget Chains 핵심 개념을 설명해줘
- insecure deserialization가 왜 필요한지 알려줘
- Insecure Deserialization / Gadget Chains 실무 설계 포인트는 뭐야?
- insecure deserialization에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Insecure Deserialization / Gadget Chains를 다루는 deep_dive 문서다. insecure deserialization은 "데이터를 객체로 복원하는 과정"이 신뢰 경계를 넘는 순간 생긴다. 타입 검증만으로 부족하고, 허용 형식과 gadget 표면까지 같이 줄여야 한다. 검색 질의가 insecure deserialization, gadget chain, object injection, type confusion처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Insecure Deserialization / Gadget Chains

> 한 줄 요약: insecure deserialization은 "데이터를 객체로 복원하는 과정"이 신뢰 경계를 넘는 순간 생긴다. 타입 검증만으로 부족하고, 허용 형식과 gadget 표면까지 같이 줄여야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SQL Injection beyond PreparedStatement](./sql-injection-beyond-preparedstatement.md)
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)

retrieval-anchor-keywords: insecure deserialization, gadget chain, object injection, type confusion, polymorphic deserialization, Java serialization, YAML payload, JSON polymorphism, whitelist, allowlist, unsafe parser

---

## 핵심 개념

직렬화(serialization)는 객체를 전송 가능한 형태로 바꾸는 것이고, 역직렬화(deserialization)는 그 반대다.  
문제는 역직렬화가 단순 복원이 아니라, 객체 생성과 초기화 로직을 함께 수행할 수 있다는 점이다.

위험해지는 순간:

- 신뢰되지 않은 입력을 객체로 복원할 때
- 타입 정보를 입력에서 받아들일 때
- 역직렬화 시점에 side effect가 있는 클래스가 섞일 때
- parser가 외부 입력으로 복잡한 객체 그래프를 만든다

이 취약점의 무서운 점은 payload가 "데이터"처럼 보이는데, 실제로는 코드 실행 경로를 타게 만들 수 있다는 데 있다.

---

## 깊이 들어가기

### 1. 왜 deserialization이 위험한가

역직렬화는 보통 다음을 수행한다.

- 바이트 스트림을 읽는다
- 타입을 결정한다
- 객체를 생성한다
- 필드를 채운다
- 경우에 따라 callback, constructor, setter, proxy resolution이 일어난다

이 과정에서 공격자가 원하는 클래스 조합이 있으면 gadget chain이 형성될 수 있다.

### 2. gadget chain은 무엇인가

gadget chain은 직접적인 취약 함수 하나가 아니라, 여러 안전해 보이는 클래스가 연결되어 위험한 동작을 만드는 경로다.

- 한 클래스는 문자열을 바꾼다
- 다른 클래스는 자동으로 lookup을 한다
- 또 다른 클래스는 외부 호출이나 reflection을 유발한다

이걸 이용하면 단순한 데이터 입력이 원치 않는 동작으로 이어질 수 있다.

### 3. Java serialization은 특히 조심해야 한다

Java native serialization은 역사적으로 많은 사고를 낳았다.

- 직렬화된 stream 안에 class metadata가 들어간다
- `readObject` 같은 훅이 호출될 수 있다
- 신뢰되지 않은 입력을 그대로 `ObjectInputStream`으로 읽으면 위험하다

그래서 실무에서는 native serialization을 피하고, 명시적 schema를 가진 형식으로 옮기는 경우가 많다.

### 4. JSON도 안전하다는 뜻은 아니다

JSON은 Java serialization보다 낫지만, 자동 polymorphic binding이 있으면 또 위험해질 수 있다.

- `@type` 같은 필드를 신뢰한다
- base type을 외부 입력이 고른다
- expected class가 아닌 하위 타입이 생성된다

즉 문제는 형식이 아니라 "외부가 타입 결정권을 가지는가"다.

### 5. 안전한 대안은 schema와 allowlist다

방어의 핵심:

- native serialization을 피한다
- 명시적 DTO만 역직렬화한다
- polymorphic typing을 제한한다
- class allowlist를 둔다
- parser 옵션을 보수적으로 설정한다
- 객체 생성 후 추가 검증을 한다

---

## 실전 시나리오

### 시나리오 1: 외부에서 온 serialized blob을 복원함

문제:

- 파일 업로드나 메시지 큐 payload를 바로 객체로 읽는다

대응:

- 신뢰되지 않은 입력에는 native deserialization을 쓰지 않는다
- DTO schema를 고정한다
- size limit과 validation을 먼저 수행한다

### 시나리오 2: JSON polymorphism이 너무 자유로움

문제:

- `@JsonTypeInfo`로 외부가 타입을 고르게 한다

대응:

- allowlist를 설정한다
- base type별로 subtype을 제한한다
- 불필요한 polymorphism을 제거한다

### 시나리오 3: 캐시나 세션 payload를 사람이 읽기 쉽게 바꾸려다 사고가 남

문제:

- 편의를 위해 객체 graph를 그대로 직렬화한다

대응:

- 구조화된 저장 대신 primitive 중심 payload를 쓴다
- 민감 상태는 별도 저장소에서 조회한다

---

## 코드로 보기

### 1. 위험한 native deserialization 예시

```java
public Object decode(byte[] data) throws IOException, ClassNotFoundException {
    try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(data))) {
        return ois.readObject();
    }
}
```

### 2. DTO 기반 안전한 대안

```java
public PaymentEvent decode(String json) throws JsonProcessingException {
    PaymentEvent event = objectMapper.readValue(json, PaymentEvent.class);
    validate(event);
    return event;
}
```

### 3. allowlist 개념

```java
public void validate(Object value) {
    if (!(value instanceof PaymentEvent event)) {
        throw new SecurityException("unexpected type");
    }
    if (event.amount() <= 0) {
        throw new IllegalArgumentException("invalid amount");
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| native serialization | 구현이 빠르다 | 공격 표면이 매우 크다 | 거의 피해야 함 |
| JSON DTO | 명시적이고 안전하다 | 스키마 관리가 필요하다 | 대부분의 서비스 |
| polymorphic JSON | 유연하다 | 타입 주입 위험이 있다 | 제한적으로만 |
| binary schema (Protobuf 등) | schema가 명확하다 | 진화 전략이 필요하다 | 안정적 RPC/메시징 |

판단 기준은 이렇다.

- 입력이 신뢰되지 않는가
- 타입 선택권을 외부가 가지는가
- 객체 생성 시 side effect가 있는가
- schema를 명시적으로 관리할 수 있는가

---

## 꼬리질문

> Q: 왜 deserialization이 취약점이 되나요?
> 의도: 객체 복원 과정이 코드 실행 경로를 탈 수 있다는 점을 아는지 확인
> 핵심: 객체 생성과 초기화가 예상 밖 동작을 유발할 수 있기 때문이다.

> Q: gadget chain은 무엇인가요?
> 의도: 직접 취약 함수가 아니라 체인 문제라는 점을 이해하는지 확인
> 핵심: 안전해 보이는 클래스들이 연결되어 위험한 동작을 만든다.

> Q: JSON도 항상 안전한가요?
> 의도: 형식보다 타입 결정권이 중요함을 아는지 확인
> 핵심: 아니요. polymorphic typing이 자유로우면 위험할 수 있다.

> Q: 가장 좋은 방어는 무엇인가요?
> 의도: 실무형 방어 전략을 아는지 확인
> 핵심: native serialization 회피, DTO schema, allowlist, validation이다.

## 한 줄 정리

insecure deserialization은 입력을 객체로 바꾸는 순간 타입과 동작까지 외부에 넘기는 문제이므로, 안전한 schema와 allowlist로 좁혀야 한다.
