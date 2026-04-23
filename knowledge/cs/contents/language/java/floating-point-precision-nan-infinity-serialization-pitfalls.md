# Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls

> 한 줄 요약: `double`과 `float`는 빠른 근사값 타입이지 "실수 일반"이 아니다. 이 특성을 잊으면 `0.1 + 0.2`, `NaN`, signed zero, JSON 숫자 직렬화, 캐시 키, 정렬에서 조용한 오류가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [`BigDecimal` Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
> - [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [JMH Benchmarking Pitfalls](./jmh-benchmarking-pitfalls.md)

> retrieval-anchor-keywords: floating point precision, IEEE 754, double, float, NaN, Infinity, signed zero, rounding error, epsilon comparison, Double.compare, JSON number, BigDecimal.valueOf, numeric serialization, precision loss, cache key, exact arithmetic, integer overflow

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

`double`과 `float`는 대부분의 십진수를 정확히 저장하지 못한다.  
이건 Java 버그가 아니라 IEEE 754 binary floating-point의 성질이다.

그래서 다음을 같이 생각해야 한다.

- 값이 근사치여도 되는가
- `NaN`과 `Infinity`를 허용할 것인가
- equality를 어떻게 정의할 것인가
- JSON/DB 경계에서 어떤 숫자 표현을 계약으로 삼을 것인가

핵심 오해는 "`double`이 정밀한 숫자"라는 기대다.  
정확한 표현, 안정된 동등성, 재현 가능한 직렬화가 필요하면 다른 모델이 낫다.

## 깊이 들어가기

### 1. 십진수와 이진 부동소수점은 표현 방식이 다르다

`0.1`, `0.2`, `0.3` 같은 값은 binary floating-point에서 정확히 표현되지 않는 경우가 많다.  
그래서 연산 결과가 사람이 기대하는 십진수와 조금 다를 수 있다.

이 특성은 다음에서 문제를 만든다.

- 누적 합
- 비율 계산
- 경계값 비교
- 문자열 직렬화 후 재파싱

즉 부동소수점의 첫 번째 질문은 "얼마나 정확한가"가 아니라 "근사 오차를 허용해도 되는가"다.

### 2. `NaN`, `Infinity`, signed zero는 일반 숫자처럼 행동하지 않는다

부동소수점은 특수값을 가진다.

- `NaN`
- `Infinity`
- `-Infinity`
- `-0.0`

이 값들은 business rule과 컬렉션 semantics를 흔들 수 있다.

- primitive 레벨에서는 `NaN == NaN`이 `false`
- `Double.isNaN()`으로 따로 확인해야 한다
- `-0.0`과 `0.0`은 산술적으로는 비슷해 보여도 비교/직렬화/해시에서 다르게 취급될 수 있다

즉 "숫자인데 같지 않다" 같은 순간이 생긴다.

### 3. equality는 연산 용도와 저장 용도가 다르다

부동소수점 비교에는 보통 두 축이 있다.

- 계산 결과가 충분히 가까운가
- 저장/캐시/서명 대상 문자열이 정확히 같은가

이 둘을 섞으면 안 된다.

- 수치 알고리즘: epsilon 기반 비교를 쓸 수 있다
- 캐시 키/직렬화 계약: canonical representation이 필요하다

`double`을 그대로 key나 signature input에 쓰기 전에 이 경계를 먼저 정해야 한다.

### 4. 직렬화 경계는 숫자 의미를 더 자주 깨뜨린다

JSON, 로그, 메시지, DB를 거치면 다음이 생길 수 있다.

- 다른 언어가 `double`로 파싱하며 오차가 달라짐
- `NaN`/`Infinity`가 JSON 표준 밖이라 직렬화 실패 또는 비표준 토큰이 생김
- scientific notation과 plain string이 섞임
- `-0.0`이 문자열 레벨에서 구분됨

즉 부동소수점 문제는 산술보다 wire contract에서 더 자주 아프다.

### 5. 타입 선택은 문제 정의를 드러내야 한다

실무 기본 감각은 대체로 이렇다.

- 센서값, 통계, 비율, 그래픽: `double`
- 돈, 세율, 정산: `BigDecimal` 또는 minor unit `long`
- 카운터: 정수 타입

문제는 "일단 `double`로 계산하고 마지막에만 `BigDecimal`로 바꾼다"는 습관이다.  
이미 들어간 오차는 나중에 복구되지 않는다.

## 실전 시나리오

### 시나리오 1: 합계 비교가 가끔 실패한다

`total == expected` 비교가 운영에서만 드물게 깨진다.  
개별 연산은 맞아 보여도 누적 오차가 경계값에서 드러난다.

### 시나리오 2: 비율 계산 결과가 `NaN`으로 퍼진다

분모가 0이 되어 `0.0 / 0.0`이 나오면 `NaN`이 생길 수 있다.  
이 값이 metrics, 캐시, JSON 응답으로 퍼지면 장애가 커진다.

### 시나리오 3: JSON 응답 직렬화가 특정 데이터에서만 깨진다

평소엔 숫자 응답이 잘 나가다가, overflow나 잘못된 계산으로 `Infinity`가 생긴다.  
JSON serializer는 표준 JSON이 아니라며 거부하거나 비표준 값을 내보낼 수 있다.

### 시나리오 4: `-0.0`과 `0.0`이 캐시 키를 흔든다

화면상으론 같은 값처럼 보여도, 문자열과 wrapper equality는 달리 움직일 수 있다.  
정규화가 없는 key 생성 로직은 재현하기 어려운 버그를 만든다.

## 코드로 보기

### 1. 근사 오차 예시

```java
double value = 0.1d + 0.2d;
System.out.println(value); // 0.30000000000000004
```

### 2. `NaN`은 따로 검사한다

```java
double ratio = 0.0d / 0.0d;
if (Double.isNaN(ratio)) {
    throw new IllegalStateException("ratio is not a number");
}
```

### 3. `BigDecimal`로 바꿀 땐 문자열이나 `valueOf`를 쓴다

```java
import java.math.BigDecimal;

BigDecimal a = new BigDecimal("0.1");
BigDecimal b = BigDecimal.valueOf(0.1d);
```

`valueOf`는 `new BigDecimal(double)`보다 예측 가능하지만,  
애초에 경계를 어떤 숫자 타입으로 받을지부터 설계하는 편이 더 중요하다.

### 4. 계산 비교와 저장 비교를 분리한다

```java
double diff = Math.abs(actual - expected);
boolean closeEnough = diff < 1e-9;
```

이 패턴은 수치 비교에는 의미가 있어도, 캐시 키나 직렬화 계약에는 그대로 쓰면 안 된다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `double` | 빠르고 하드웨어 친화적이다 | 근사 오차와 특수값 semantics를 이해해야 한다 |
| `BigDecimal` | 십진 표현과 반올림을 통제하기 쉽다 | 느리고 정책 결정이 더 많이 필요하다 |
| minor unit `long` | 저장과 비교가 단순하다 | 스케일과 통화 규칙을 별도 관리해야 한다 |
| epsilon 비교 | 수치 계산에 실용적이다 | equality contract나 wire format에는 쓸 수 없다 |

핵심은 숫자 타입 선택이 성능 문제가 아니라 도메인 의미와 직렬화 계약 문제라는 점이다.

## 꼬리질문

> Q: 왜 `0.1 + 0.2`가 `0.3`이 아니게 나오나요?
> 핵심: binary floating-point에서 해당 십진수를 정확히 표현하지 못하기 때문이다.

> Q: `NaN`은 왜 조심해야 하나요?
> 핵심: 일반 숫자처럼 비교되지 않고 연산 결과를 조용히 오염시킬 수 있기 때문이다.

> Q: 부동소수점 비교는 항상 epsilon으로 해야 하나요?
> 핵심: 수치 계산에는 도움이 되지만, 저장/캐시/서명 같은 계약 비교에는 별도 canonicalization이 필요하다.

> Q: 돈 계산은 왜 `double`보다 `BigDecimal`이나 minor unit가 낫나요?
> 핵심: 정확한 십진 표현과 반올림 정책 제어가 필요하기 때문이다.

## 한 줄 정리

부동소수점은 빠른 근사 계산 도구이므로, `NaN`/`Infinity`/signed zero와 직렬화 경계를 이해하지 않고 equality나 계약 값으로 쓰면 운영 버그가 생기기 쉽다.
