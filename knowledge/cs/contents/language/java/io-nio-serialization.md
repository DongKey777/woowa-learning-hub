# Java IO, NIO, Serialization, JSON Mapping

**난이도: 🔴 Advanced**

> 파일/네트워크 입출력과 객체 변환을 실전에서 읽고 판단하기 위한 정리

> 관련 문서:
> - [Serialization Compatibility and `serialVersionUID`](./serialization-compatibility-serial-version-uid.md)
> - [`serialPersistentFields`, `readObjectNoData`, and Native Serialization Evolution Escape Hatches](./serialpersistentfields-readobjectnodata-evolution-escape-hatches.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)
> - [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
> - [BigDecimal `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md)
> - [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)
> - [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
> - [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)
> - [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
> - [`Instant`, `LocalDateTime`, `OffsetDateTime`, `ZonedDateTime` Boundary Design](./java-time-instant-localdatetime-boundaries.md)
> - [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./locale-root-case-mapping-unicode-normalization.md)
> - [Charset, UTF-8 BOM, Malformed Input, and Decoder Policy](./charset-utf8-bom-malformed-input-decoder-policy.md)
> - [Direct Buffer, Off-Heap, Native Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)

> retrieval-anchor-keywords: Java IO, NIO, ByteBuffer, FileChannel, SocketChannel, blocking IO, non-blocking IO, serialization, native serialization, JSON mapping, Jackson, ObjectInputStream, ObjectOutputStream, BigDecimal JSON, canonical representation, precision loss, schema evolution, OffsetDateTime JSON, Unicode normalization, UTF-8 boundary, enum JSON mapping, unknown enum, NaN JSON, null vs missing field, primitive field default, serialPersistentFields, charset, BOM, malformed input

<details>
<summary>Table of Contents</summary>

- [왜 이 주제를 알아야 하는가](#왜-이-주제를-알아야-하는가)
- [IO와 NIO의 차이](#io와-nio의-차이)
- [버퍼와 채널](#버퍼와-채널)
- [ByteBuffer를 읽는 감각](#bytebuffer를-읽는-감각)
- [Blocking과 Non-blocking](#blocking과-non-blocking)
- [Serialization의 의미와 위험](#serialization의-의미와-위험)
- [Serialization 피해야 하는 이유](#serialization-피해야-하는-이유)
- [JSON Mapping이 더 자주 쓰이는 이유](#json-mapping이-더-자주-쓰이는-이유)
- [실전 선택 기준](#실전-선택-기준)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 주제를 알아야 하는가

백엔드에서는

- 파일을 읽고 쓰고
- 네트워크로 데이터를 주고받고
- 객체를 직렬화하거나 JSON으로 바꾸는

일이 반복된다.

이때 중요한 것은 "API 이름"보다 **어떤 비용과 제약이 생기는가**다.

---

## IO와 NIO의 차이

### IO

- 전통적인 스트림 기반 API
- 바이트 또는 문자 단위로 읽고 쓴다
- 코드가 단순하다

예:

```java
InputStream in = new FileInputStream("a.txt");
OutputStream out = new FileOutputStream("b.txt");
```

### NIO

- 버퍼, 채널, 선택자(selector) 중심
- 더 많은 제어가 가능하다
- 대규모 동시 연결이나 고성능 처리에서 자주 언급된다

예:

```java
Path path = Path.of("a.txt");
byte[] bytes = Files.readAllBytes(path);
```

### 감각적으로 보면

- IO는 "흐르는 물을 그대로 받는 느낌"
- NIO는 "버퍼에 담아 효율적으로 처리하는 느낌"

---

## 버퍼와 채널

### Buffer

- 데이터를 잠시 담아두는 저장 공간
- 읽기/쓰기 단위를 관리하기 쉽다

### Channel

- 데이터가 오가는 통로
- Stream보다 더 명시적으로 입출력을 다룬다

### 중요한 차이

- Stream은 보통 순차 처리 중심
- Channel은 더 유연한 제어가 가능하다

즉 큰 파일 처리나 네트워크 이벤트 처리에서 NIO가 자주 고려된다.

### 자주 보는 채널

- `FileChannel`
- `SocketChannel`
- `ServerSocketChannel`

채널은 기본적으로 버퍼와 함께 사용한다.  
즉 "채널에서 바로 바이트를 하나씩 읽는 느낌"이 아니라, **버퍼에 담아 옮기는 느낌**이 더 가깝다.

---

## ByteBuffer를 읽는 감각

`ByteBuffer`는 NIO를 이해할 때 핵심이다.

### 상태

버퍼는 보통 아래 상태 전이를 기억하면 된다.

- `clear()`: 쓰기 준비
- `flip()`: 읽기 준비
- `compact()`: 남은 데이터를 앞으로 당김

### 핵심 필드

- `position`
- `limit`
- `capacity`

이 셋의 관계를 이해하면, 왜 읽고 쓴 뒤에 `flip()`이 필요한지 바로 보인다.

### 예시 흐름

```java
ByteBuffer buffer = ByteBuffer.allocate(1024);
int read = channel.read(buffer);
buffer.flip();
channel.write(buffer);
```

`read()` 후에는 버퍼가 "쓴 상태"이므로, 그대로 쓰기 작업에 넘기려면 `flip()`이 필요하다.

### 실전 포인트

- 버퍼를 잘못 넘기면 읽은 데이터가 비어 보이거나, 쓰기 위치가 꼬인다
- 대용량 처리에서는 버퍼 크기와 반복 횟수도 성능에 영향을 준다
- direct buffer는 JVM 힙 밖 자원을 활용할 수 있어 상황에 따라 고려된다

---

## Blocking과 Non-blocking

### Blocking

- 작업이 끝날 때까지 호출 스레드가 기다린다

### Non-blocking

- 바로 반환하고, 나중에 다시 처리한다

### 언제 중요한가

- 연결 수가 많을 때
- 한 스레드가 오래 대기하는 비용이 클 때
- 서버 자원을 효율적으로 쓰고 싶을 때

실전에서는 "무조건 non-blocking이 더 좋다"가 아니라,
구조와 복잡도를 감당할 수 있는지까지 같이 봐야 한다.

---

## Serialization의 의미와 위험

Serialization은 **객체 상태를 바이트 형태로 저장하거나 전송 가능한 형태로 바꾸는 것**이다.

### 쓰는 이유

- 캐시 저장
- 파일 저장
- 네트워크 전송

### 위험

- 클래스 구조가 바뀌면 호환성 문제가 생길 수 있다
- 내부 구현이 노출되기 쉽다
- 보안 이슈가 생길 수 있다

### 실전 감각

- Java native serialization은 편하지만 주의가 필요하다
- 장기 저장 형식으로는 신중해야 한다

---

## Serialization 피해야 하는 이유

Java native serialization은 "작동은 쉽지만 운영 리스크가 큰 방식"으로 보는 편이 안전하다.

### 호환성 문제

- 필드 추가/삭제가 잦으면 역직렬화가 깨질 수 있다
- `serialVersionUID`를 의식해야 한다

### 캡슐화 약화

- 직렬화 대상이 곧 외부 포맷이 되므로 내부 설계를 바꾸기 어려워진다
- private 구현 세부가 포맷 안정성에 영향을 준다

### 보안 문제

- 신뢰할 수 없는 입력을 역직렬화하는 것은 위험하다
- 객체 생성 과정에서 예상치 못한 코드 실행 경로가 열릴 수 있다

### 객체 생명주기 문제

- `transient` 필드는 직렬화되지 않는다
- `readObject`, `writeObject`를 쓰면 규칙을 더 세심하게 관리해야 한다

즉 Java native serialization은 "간단한 데모"에는 편할 수 있지만, 장기 유지보수 포맷으로는 부담이 크다.

---

## JSON Mapping이 더 자주 쓰이는 이유

실무에서는 객체를 그대로 바이트로 저장하기보다 JSON으로 바꾸는 경우가 많다.

### 이유

- 사람이 읽기 쉽다
- 언어 간 호환이 좋다
- API 응답/요청 형식으로 널리 쓰인다

### Trade-off

- 문자열 기반이라 바이트 직렬화보다 크기가 커질 수 있다
- 파싱 비용이 있다
- 스키마를 강하게 보장하지 않는다
- 숫자/날짜/널 처리 규칙을 팀이 따로 합의해야 한다

### 자주 보는 도구

- Jackson
- Gson
- Spring에서의 HTTP message converter

### 실전 감각

- API 경계에서는 JSON이 디버깅과 운영에 유리한 경우가 많다
- 내부 고속 통신이나 저장 포맷은 binary protocol을 별도로 설계하는 경우도 있다
- "JSON이 무조건 좋다"가 아니라, 관찰 가능성과 호환성 측면에서 자주 선택된다고 보는 것이 정확하다

---

## 실전 선택 기준

### 파일 처리

- 단순한 순차 읽기/쓰기라면 IO로도 충분한 경우가 많다
- 대용량 파일이나 더 세밀한 제어가 필요하면 NIO를 고려한다
- 버퍼 상태 전이가 중요한 코드라면 `ByteBuffer`의 `position`, `limit`, `flip()` 동작을 먼저 확인한다

### 서비스 간 통신

- 대체로 JSON mapping이 더 흔하다
- 디버깅과 운영 편의성이 좋기 때문이다

### 저장 포맷

- 빠른 내부 저장이 중요하면 binary serialization을 검토할 수 있다
- 장기 유지보수와 호환성이 중요하면 JSON/명시적 포맷이 더 안전하다
- 신뢰할 수 없는 입력을 받는다면 native serialization은 피하는 쪽이 낫다

---

## 면접에서 자주 나오는 질문

### Q. IO와 NIO의 차이는 무엇인가요?

- IO는 스트림 중심이고, NIO는 버퍼/채널 중심이다.

### Q. Non-blocking이 항상 더 좋은가요?

- 아니다. 복잡도와 운영 난이도가 올라간다.

### Q. Java native serialization을 조심해야 하는 이유는 무엇인가요?

- 호환성, 보안, 유지보수 측면에서 부담이 크기 때문이다.

### Q. `ByteBuffer.flip()`은 왜 필요한가요?

- 읽기와 쓰기의 기준점이 다르기 때문이다.
- `flip()`은 "방금 쓴 데이터를 읽기 위한 상태"로 바꿔준다.

### Q. 실무에서 JSON mapping을 많이 쓰는 이유는 무엇인가요?

- 가독성, 호환성, 디버깅 편의성이 좋기 때문이다.
