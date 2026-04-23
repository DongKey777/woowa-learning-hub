# Charset, UTF-8 BOM, Malformed Input, and Decoder Policy

> 한 줄 요약: 문자열은 `String`으로 다 같아 보여도, 경계에서는 bytes와 charset policy가 먼저다. UTF-8 BOM, 잘못된 decoder 기본값, replacement 문자 허용, default charset 의존을 놓치면 로그, CSV, 메시지, 서명, payload parsing이 환경마다 다르게 깨진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./locale-root-case-mapping-unicode-normalization.md)
> - [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md)
> - [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)

> retrieval-anchor-keywords: charset, UTF-8, BOM, Byte Order Mark, malformed input, unmappable character, CharsetDecoder, CodingErrorAction, replacement character, default charset, mojibake, byte to string, string to byte, signature mismatch, CSV encoding

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

문자열 경계의 첫 질문은 "무슨 문자셋인가"다.

- 바이트를 어떤 charset으로 해석할 것인가
- 잘못된 입력을 예외로 볼지 replacement로 볼지
- BOM을 허용할지 제거할지
- 시스템 default charset에 기대도 되는가

이걸 명시하지 않으면 "가끔 깨지는 문자열"이 생긴다.

## 깊이 들어가기

### 1. default charset은 운영 계약이 아니다

`new String(bytes)`나 `string.getBytes()`는 기본 charset에 기대는 코드가 될 수 있다.  
이 값은 OS, locale, JVM 설정에 따라 달라질 수 있다.

즉 개발환경에서 맞던 코드가:

- 배포 환경
- 배치 서버
- CSV import worker

에서 다르게 동작할 수 있다.

### 2. malformed input을 replacement로 삼킬지 예외로 볼지 결정해야 한다

decoder는 잘못된 입력을 만났을 때 대개 둘 중 하나를 택한다.

- 예외로 실패
- replacement character로 대체

문제는 replacement가 조용한 데이터 손실을 만들 수 있다는 점이다.

- 사용자 이름 일부가 `�`로 바뀐다
- 서명/해시 원문이 달라진다
- CSV key가 깨진 채 저장된다

즉 편의 fallback이 correctness bug를 숨길 수 있다.

### 3. UTF-8 BOM은 "문자 하나"처럼 끼어들 수 있다

UTF-8 BOM은 파일/stream 시작에 붙을 수 있다.  
지원 라이브러리나 파서가 이를 자동 제거하지 않으면:

- 첫 컬럼 이름 앞에 숨은 문자
- 헤더 mismatch
- JSON/CSV parsing 이상

같은 문제가 생긴다.

즉 BOM은 encoding metadata처럼 보이지만 payload 일부로 읽힐 수 있다.

### 4. boundary마다 policy가 다를 수 있다

모든 문자열 경계가 같은 정책을 쓰는 것은 아니다.

- user-facing import: 에러 위치를 자세히 보여주며 fail-fast
- tolerant log ingest: replacement 허용 가능
- signature/verification path: byte-for-byte strict

즉 charset policy는 기능이 아니라 boundary contract다.

### 5. canonicalization보다 먼저 decode correctness가 필요하다

`Locale.ROOT`, NFC normalization 같은 정책도 중요하지만,  
그 전에 바이트가 올바르게 문자열로 해석되어야 한다.

잘못 decode한 문자열은 그 다음 정규화로도 복구되지 않는다.

## 실전 시나리오

### 시나리오 1: CSV 첫 헤더가 매번 안 맞는다

파일 앞 BOM이 헤더 이름 앞에 숨어 있었다.  
사람 눈에는 같아 보여도 첫 컬럼 키가 달랐다.

### 시나리오 2: 운영에서만 한글이 깨진다

로컬은 UTF-8 기본 charset, 운영은 다른 default charset이었다.  
코드가 charset을 명시하지 않아 mojibake가 생겼다.

### 시나리오 3: webhook 서명 검증이 가끔 실패한다

원문 bytes를 검증해야 하는데 먼저 `String`으로 decode한 뒤 재인코딩했다.  
charset이나 malformed input handling 차이로 원문이 바뀌었다.

### 시나리오 4: 잘못된 입력이 조용히 저장된다

decoder가 replacement를 허용해 `�`를 넣고 넘어갔다.  
장애는 안 났지만 데이터 정합성이 깨졌다.

## 코드로 보기

### 1. charset 명시

```java
byte[] bytes = payload.getBytes(java.nio.charset.StandardCharsets.UTF_8);
String text = new String(bytes, java.nio.charset.StandardCharsets.UTF_8);
```

### 2. strict decoder 정책

```java
java.nio.charset.CharsetDecoder decoder =
    java.nio.charset.StandardCharsets.UTF_8
        .newDecoder()
        .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
        .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT);
```

### 3. BOM 감각

```java
// parser 진입 전 BOM 존재 여부를 의식해야 한다.
```

### 4. 서명 경계는 bytes 기준

```java
byte[] raw = requestBodyBytes;
```

이 경계는 decode 후 재인코딩보다 raw byte 보존이 더 중요할 수 있다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| default charset 의존 | 코드가 짧다 | 환경 차이로 조용히 깨질 수 있다 |
| UTF-8 명시 | 예측 가능성이 높다 | 외부 입력의 실제 charset mismatch를 따로 처리해야 한다 |
| replacement 허용 | ingestion이 덜 자주 실패한다 | 데이터 손실과 서명 mismatch를 숨길 수 있다 |
| strict decoder | 데이터 품질이 높다 | 잘못된 입력을 명시적으로 처리해야 한다 |

핵심은 charset을 I/O 세부가 아니라 payload correctness의 일부로 보는 것이다.

## 꼬리질문

> Q: 왜 charset을 항상 명시하나요?
> 핵심: default charset은 환경 의존적이라 운영 계약으로 보기 어렵기 때문이다.

> Q: replacement character를 허용하면 안 되나요?
> 핵심: 상황에 따라 가능하지만, 조용한 데이터 손실을 만들 수 있어 boundary별 정책이 필요하다.

> Q: UTF-8 BOM은 왜 문제인가요?
> 핵심: 자동 제거되지 않으면 payload 앞의 숨은 문자처럼 동작해 헤더나 첫 필드를 깨뜨릴 수 있다.

> Q: 서명 검증은 왜 문자열보다 bytes가 중요하나요?
> 핵심: decode/encode 과정에서 원문이 바뀌면 서명 대상 자체가 달라지기 때문이다.

## 한 줄 정리

문자열 boundary의 correctness는 `String` API보다 charset/decoder policy가 먼저이며, UTF-8 명시와 malformed input 처리 전략을 계약으로 가져가야 한다.
