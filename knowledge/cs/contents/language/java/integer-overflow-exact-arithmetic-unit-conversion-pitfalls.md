# Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls

> 한 줄 요약: Java 정수 연산은 기본적으로 silent wraparound다. counter, timeout, money minor unit, epoch conversion, batch size 계산에서 overflow를 놓치면 예외가 아니라 조용한 음수값과 잘못된 비교가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)
> - [`BigInteger`, Unsigned Parsing, and Numeric Boundary Semantics](./biginteger-unsigned-parsing-boundaries.md)
> - [Parser Overflow Boundaries: `parseInt`, `parseLong`, and `toIntExact`](./parser-overflow-boundaries-parseint-parselong-tointexact.md)
> - [Saturating Arithmetic, Clamping, and Domain Contracts](./saturating-arithmetic-clamping-domain-contracts.md)
> - [`BigDecimal` Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
> - [`Instant`, `LocalDateTime`, `OffsetDateTime`, `ZonedDateTime` Boundary Design](./java-time-instant-localdatetime-boundaries.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)

> retrieval-anchor-keywords: integer overflow, exact arithmetic, Math.addExact, Math.multiplyExact, wraparound, epoch conversion, milliseconds to nanoseconds, unit conversion overflow, minor unit money, counter overflow, long vs int, signed overflow, BigInteger, saturating arithmetic

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

Java의 `int`와 `long`은 overflow가 나도 기본적으로 예외를 던지지 않는다.  
값이 표현 범위를 넘으면 2의 보수 wraparound가 일어난다.

즉 다음이 문제다.

- 계산이 틀려도 바로 티가 안 난다
- 음수가 안 나와야 할 곳에 음수가 생긴다
- 비교와 정렬이 조용히 망가진다

정수 연산은 "정확하다"가 아니라 **범위 안에서만 정확하다**고 읽어야 한다.

## 깊이 들어가기

### 1. overflow는 correctness bug이지 계산기 문제만이 아니다

overflow는 단순한 수학 오차가 아니다.

- rate limit 남은 토큰
- 재고 합계
- retry backoff
- delay queue deadline
- minor unit money

같은 backend state machine에서 직접 상태 전이를 잘못 만들 수 있다.

### 2. unit conversion이 생각보다 자주 터진다

특히 시간과 크기 단위 변환이 위험하다.

- milliseconds -> nanoseconds
- seconds -> milliseconds
- MB -> bytes
- records * chunkSize

이 연산은 개별 값이 작아 보여도 곱셈 순간 범위를 넘을 수 있다.

즉 "원래 값은 안전해 보였다"는 것이 안전 증거가 아니다.

### 3. `Math.addExact` 계열은 boundary assertion 도구다

정수 overflow를 놓치기 싫다면 `Math.addExact`, `subtractExact`, `multiplyExact`, `toIntExact`가 유용하다.

이 메서드들은 overflow 시 예외를 던진다.  
즉 overflow를 값으로 숨기지 않고 contract violation으로 드러낸다.

특히 다음에 잘 맞는다.

- domain invariant가 중요한 연산
- payload를 받는 boundary
- unit conversion
- long -> int 축소 변환

### 4. `int`와 `long` 선택은 현재 값이 아니라 최대 수명을 봐야 한다

처음엔 `int`로 충분해 보이는 값도 누적되면 다르다.

- 요청 수
- sequence number
- uptime 기준 tick
- tenant별 event offset

즉 타입 선택은 "오늘 값이 얼마인가"가 아니라  
"운영 수명 동안 어디까지 커질 수 있는가"를 기준으로 해야 한다.

### 5. 돈과 시간은 단위 혼동이 overflow를 더 숨긴다

예:

- 돈을 minor unit `long`으로 저장하면서 곱셈에 `int`를 섞음
- `Duration.toMillis()` 결과를 다시 나노초로 바꾸며 overflow
- DB bigint를 앱에서 `int`로 잘라 받음

이 문제는 number type bug이면서 unit bug다.  
즉 value object로 단위를 닫는 편이 더 안전하다.

## 실전 시나리오

### 시나리오 1: delay 계산이 음수가 된다

`seconds * 1000 * 1000 * 1000` 식으로 나노초를 만들다 overflow가 났다.  
결과는 예외가 아니라 이상한 음수 delay다.

### 시나리오 2: batch size * row size 계산이 음수가 된다

메모리 사용량 계산이나 buffer allocation 전에 곱셈 overflow가 나면,  
validation이 통과했는데 실제로는 잘못된 크기 판단이 생긴다.

### 시나리오 3: `long` ID를 `int` API로 넘기며 잘린다

초기엔 값이 작아 괜찮다가, 운영 시간이 지나며 `toIntExact` 없이 캐스팅한 부분이 깨진다.

### 시나리오 4: minor unit money 합산이 한계를 넘는다

`long`으로 cents를 저장하는 모델은 좋을 수 있지만,  
대량 집계나 환율 곱셈에선 overflow 경계를 여전히 검토해야 한다.

## 코드로 보기

### 1. silent wraparound

```java
int max = Integer.MAX_VALUE;
int next = max + 1;
System.out.println(next); // 음수
```

### 2. exact arithmetic

```java
long nanos = Math.multiplyExact(seconds, 1_000_000_000L);
```

### 3. 축소 변환 검증

```java
int pageSize = Math.toIntExact(dbValue);
```

### 4. 단위 닫기

```java
public record RetryDelayMillis(long value) {
    public RetryDelayMillis {
        if (value < 0) {
            throw new IllegalArgumentException("negative delay");
        }
    }
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| 기본 정수 연산 | 빠르고 간단하다 | overflow가 조용히 숨는다 |
| `Math.*Exact` | contract violation을 빨리 드러낸다 | 예외 처리와 boundary 검증이 필요하다 |
| `long` 우선 | `int`보다 안전 여유가 크다 | 무한하지는 않다 |
| 단위 value object | 단위 혼동과 잘못된 축소 변환을 줄인다 | 타입 수와 변환 코드가 늘어난다 |

핵심은 overflow를 성능 세부가 아니라 domain correctness 문제로 보는 것이다.

## 꼬리질문

> Q: Java 정수 overflow는 왜 위험한가요?
> 핵심: 기본적으로 예외 없이 wraparound되어 조용한 잘못된 값이 생기기 때문이다.

> Q: `Math.addExact`는 언제 쓰나요?
> 핵심: overflow를 값으로 숨기고 싶지 않은 domain 계산과 unit conversion 경계에서 유용하다.

> Q: `long`이면 충분한가요?
> 핵심: 더 넓지만 무한하지 않다. 누적량과 수명까지 같이 봐야 한다.

> Q: 왜 단위 변환이 특히 위험한가요?
> 핵심: 곱셈이 자주 들어가고 값의 의미가 달라져 overflow가 더 늦게 드러나기 때문이다.

## 한 줄 정리

정수 연산은 범위를 넘는 순간 조용히 wrap되므로, timeout, size, money, ID 계산처럼 의미가 중요한 곳에선 exact arithmetic와 단위 모델링이 필요하다.
