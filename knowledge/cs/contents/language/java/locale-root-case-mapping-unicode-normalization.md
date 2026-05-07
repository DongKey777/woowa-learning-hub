---
schema_version: 3
title: Locale.ROOT Case Mapping and Unicode Normalization Pitfalls
concept_id: language/locale-root-case-mapping-unicode-normalization
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 89
mission_ids:
- missions/payment
- missions/racingcar
review_feedback_tags:
- string-normalization
- locale
- unicode
aliases:
- Locale.ROOT case mapping Unicode normalization
- Turkish I toLowerCase pitfall
- Unicode NFC NFD normalization Java
- identifier canonicalization Java
- string equality visually same different code point
- 자바 문자열 정규화 Locale.ROOT
symptoms:
- toLowerCase()를 locale 없이 호출해 운영 서버 default locale 차이로 protocol key, cache key, signature input이 달라지는 문제를 만든다
- 화면상 같은 문자열이 NFC/NFD code point sequence 차이로 equals false나 unique index 중복을 일으키는 상황을 놓쳐
- 모든 문자열을 normalize/lower-case하면 된다고 생각해 password, opaque token, signature payload처럼 바꾸면 안 되는 경계를 손상해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- language/string-intern-pool-pitfalls
- language/java-equality-identity-basics
- language/charset-utf8-bom-malformed-input-decoder-policy
next_docs:
- language/empty-string-blank-null-missing-payload-semantics
- language/record-serialization-evolution
- language/json-null-missing-unknown-field-schema-evolution
linked_paths:
- contents/language/java/string-intern-pool-pitfalls.md
- contents/language/java-equals-hashcode-comparable-contracts.md
- contents/language/java/io-nio-serialization.md
- contents/language/java/empty-string-blank-null-missing-payload-semantics.md
- contents/language/java/charset-utf8-bom-malformed-input-decoder-policy.md
- contents/language/java/record-serialization-evolution.md
- contents/language/java/json-null-missing-unknown-field-schema-evolution.md
confusable_with:
- language/charset-utf8-bom-malformed-input-decoder-policy
- language/empty-string-blank-null-missing-payload-semantics
- language/string-intern-pool-pitfalls
forbidden_neighbors: []
expected_queries:
- Java에서 toLowerCase에 Locale.ROOT를 붙여야 하는 이유와 Turkish I 함정을 설명해줘
- 사람이 보기엔 같은 문자열인데 equals가 false인 Unicode normalization 문제를 예제로 보여줘
- NFC와 NFD normalization을 사용자명 dedup이나 검색 key에 어떻게 적용해야 해?
- signature payload나 token은 왜 함부로 normalize lower-case 하면 안 돼?
- display value와 canonical key를 분리 저장하는 문자열 canonicalization 설계를 알려줘
contextual_chunk_prefix: |
  이 문서는 Java 문자열 canonicalization에서 Locale.ROOT case mapping, Unicode NFC/NFD normalization, original display value와 canonical key 분리를 다루는 advanced playbook이다.
  Locale.ROOT, Turkish I, Unicode normalization, String equals false, identifier canonicalization 질문이 본 문서에 매핑된다.
---
# `Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls

> 한 줄 요약: 문자열은 사람 눈에 같아 보여도 code point가 다를 수 있고, `toLowerCase()`는 locale에 따라 달라질 수 있다. 식별자, 사용자명, 검색 키, 서명 대상 문자열을 다룰 때 normalization과 case policy를 명시하지 않으면 조용한 중복과 검증 실패가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [String Intern and Pool Pitfalls](./string-intern-pool-pitfalls.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md)
> - [Charset, UTF-8 BOM, Malformed Input, and Decoder Policy](./charset-utf8-bom-malformed-input-decoder-policy.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)

> retrieval-anchor-keywords: Locale.ROOT, Unicode normalization, NFC, NFD, case mapping, case folding, Turkish I, Normalizer, canonical representation, identifier normalization, username key, email normalization, UTF-8 boundary, string equality, signature mismatch, blank string, trim policy

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

문자열 동등성에는 층이 있다.

- byte가 같은가
- code point sequence가 같은가
- Unicode canonical equivalence로 같은가
- 비즈니스 규칙상 같은 식별자인가

예를 들어 사람이 보기엔 같은 문자여도 다음은 다를 수 있다.

- composed form
- decomposed form
- 대소문자 변환 결과
- locale-specific mapping 결과

그래서 backend에서는 문자열을 "그냥 `String`"으로만 다루면 부족할 때가 많다.

## 깊이 들어가기

### 1. `toLowerCase()`는 locale에 영향을 받는다

Java의 `String#toLowerCase()`와 `toUpperCase()`는 locale을 받지 않으면 기본 locale 영향을 받을 수 있다.  
프로토콜 키, header 이름, enum-like token, username key를 canonicalize할 때는 보통 `Locale.ROOT`가 더 안전하다.

대표 함정은 Turkish I다.

- 영어권에서 기대한 소문자화 결과
- 터키어 locale에서의 실제 변환 결과

이 차이가 캐시 키, 권한 코드, signature input을 조용히 바꿀 수 있다.

### 2. Unicode normalization을 안 하면 "같아 보이는 다른 문자열"이 남는다

문자 하나가 하나의 code point로 표현될 수도 있고,  
기본 문자 + combining mark로 표현될 수도 있다.

즉 화면상 같은 값이어도 `equals()`는 `false`일 수 있다.

이 문제는 다음에서 자주 나온다.

- 사용자명 dedup
- 검색 키 생성
- 외부 시스템에서 받은 UTF-8 입력 저장
- unique index 전 단계 canonicalization

일반적인 canonical representation이 필요하면 보통 NFC를 먼저 검토한다.

### 3. normalization과 case folding은 같은 작업이 아니다

순서도, 목적도 다르다.

- normalization: 표현을 정규화
- case policy: 대소문자 민감도를 정한다

예를 들어 사용자명 검색 키는 `NFC + Locale.ROOT lower-case`가 맞을 수 있지만,  
비밀번호, opaque token, 서명 원문은 건드리면 안 된다.

즉 모든 문자열을 normalize/lower-case 하는 것은 정답이 아니다.

### 4. 경계에서 한 번만 canonicalize하는 편이 안전하다

입력마다 중간 계층이 제각각 정규화하면 다음이 생긴다.

- DB 저장 값과 캐시 키가 다름
- 로그 재처리 결과가 다름
- 서명/해시 대상 문자열이 다름

그래서 보통은 boundary를 정한다.

- 입력 검증 시 canonical key 생성
- 원본 display value는 별도 보존
- 비교/인덱싱은 canonical key 기준

### 5. compatibility normalization은 더 위험할 수 있다

NFKC/NFKD는 폭넓은 compatibility folding을 해준다.  
하지만 의미를 과하게 접어버릴 수 있어 식별자/보안 경계에 무작정 쓰기 위험하다.

실무 기본값은 보통 이렇다.

- canonical equivalence가 필요하면 NFC 검토
- protocol/identifier case folding은 `Locale.ROOT`
- security-sensitive field는 별도 정책 문서화

## 실전 시나리오

### 시나리오 1: 같은 사용자명이 두 번 가입된다

한 입력은 precomposed, 다른 입력은 decomposed form이다.  
화면에선 같아 보여도 `equals()`와 DB unique key가 다르게 동작할 수 있다.

### 시나리오 2: 운영 서버 locale이 바뀌자 캐시 miss가 늘어난다

키 canonicalization에 `toLowerCase()`만 썼다면,  
default locale 차이로 동일 토큰이 다른 키가 될 수 있다.

### 시나리오 3: 서명 검증이 환경마다 다르게 실패한다

송신자는 원문 그대로 서명했고, 수신자는 normalization 후 서명 검증했다.  
문자열 "의미"는 같아 보여도 byte sequence가 달라져 해시가 바뀐다.

### 시나리오 4: 이메일을 전부 소문자화했더니 예외 케이스가 생긴다

도메인 파트는 보통 case-insensitive로 취급하지만, local-part는 계약상 반드시 그렇다고 볼 수 없다.  
즉 field별 canonicalization 정책을 분리해야 한다.

## 코드로 보기

### 1. identifier key canonicalization

```java
import java.text.Normalizer;
import java.util.Locale;

public final class UserKeyNormalizer {
    public String canonicalize(String raw) {
        String nfc = Normalizer.normalize(raw, Normalizer.Form.NFC);
        return nfc.toLowerCase(Locale.ROOT);
    }
}
```

이 코드는 case-insensitive identifier라는 도메인 정책이 있을 때만 맞다.

### 2. 원본 값과 비교 키 분리

```java
public record Username(String displayValue, String canonicalKey) {
    public static Username from(String raw) {
        String canonical = java.text.Normalizer.normalize(raw, java.text.Normalizer.Form.NFC)
            .toLowerCase(java.util.Locale.ROOT);
        return new Username(raw, canonical);
    }
}
```

### 3. locale를 명시한 case mapping

```java
String protocolToken = input.toLowerCase(java.util.Locale.ROOT);
```

### 4. 서명 대상 문자열은 함부로 바꾸지 않기

```java
byte[] payloadBytes = rawPayload.getBytes(java.nio.charset.StandardCharsets.UTF_8);
```

canonicalization과 signature input canonicalization은 같은 문제가 아닐 수 있다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `Locale.ROOT` 기반 case policy | 환경 의존성을 줄인다 | 언어별 자연스러운 표시 규칙과는 다를 수 있다 |
| NFC normalization | visually same input 중복을 줄인다 | 어디서 적용할지 정책이 필요하다 |
| 원본/정규화 값 분리 저장 | 검색과 표시를 모두 안정적으로 다룬다 | 모델과 저장 필드가 늘어난다 |
| 무조건 compatibility folding | 중복을 더 공격적으로 줄일 수 있다 | 의미 손실과 security risk가 커질 수 있다 |

핵심은 문자열 canonicalization을 구현 디테일이 아니라 도메인 정책으로 다루는 것이다.

## 꼬리질문

> Q: 왜 `toLowerCase()`에 `Locale.ROOT`를 붙이나요?
> 핵심: default locale 의존성을 제거해 identifier canonicalization을 환경에 덜 흔들리게 하기 위해서다.

> Q: Unicode normalization은 언제 필요한가요?
> 핵심: 사람이 보기엔 같은 문자열이 서로 다른 code point sequence로 들어올 수 있는 입력 경계에서 필요하다.

> Q: 모든 문자열을 normalize하고 lower-case하면 되나요?
> 핵심: 아니다. 비밀번호, 토큰, 서명 원문처럼 바꾸면 안 되는 값이 많다.

> Q: display value와 canonical key를 왜 나누나요?
> 핵심: 사용자 경험용 원본 표현과 비교/인덱싱용 표현의 요구가 다르기 때문이다.

## 한 줄 정리

문자열 비교 정책은 `String` API 선택이 아니라 canonicalization 설계이므로, `Locale.ROOT`, Unicode normalization, 원본/비교 키 분리를 경계에서 명시하는 것이 안전하다.
