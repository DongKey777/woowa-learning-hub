# BigDecimal API 출력 입문: canonicalization 뒤 `toString()` vs `toPlainString()`

> 한 줄 요약: 초급자 기준으로는 "`같은 값으로 한 번 정규화`한 뒤, API 바깥으로 사람이 읽는 문자열을 내보낼 때는 `toPlainString()`을 먼저 검토"하면 `1E+3` 같은 surprise를 크게 줄일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md)
- [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md)
- [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)
- [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
- [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
- [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)

retrieval-anchor-keywords: bigdecimal tostring vs toplainstring beginner, bigdecimal api boundary canonicalization, bigdecimal output policy beginner, bigdecimal scientific notation log json ui, bigdecimal plain string display policy, bigdecimal striptrailingzeros tostring, bigdecimal serialization display bridge, java bigdecimal 출력 정책, 자바 bigdecimal tostring toplainstring 차이, 자바 bigdecimal 정규화 후 출력, bigdecimal 지수표기 방지, bigdecimal plain string 출력

## 핵심 개념

초급자 기준으로는 이 한 줄이 제일 중요하다.

> `BigDecimal`은 "같은 값으로 맞추는 정책"과 "어떻게 보여 줄지 정책"이 다르다.

- `stripTrailingZeros()` 같은 canonicalization은 "같은 값을 같은 내부 표현으로 모을까?"에 가깝다.
- `toString()`과 `toPlainString()`은 "그 값을 바깥에 어떤 문자열로 보여 줄까?"에 가깝다.
- 그래서 "같은 값으로 정리했다"와 "사람이 읽기 좋은 문자열이 된다"를 같은 말로 보면 헷갈린다.

API boundary에서는 아래처럼 두 단계를 분리하면 초급자에게 가장 안전하다.

1. 내부에서 같은 값으로 맞춘다.
2. 바깥으로 내보낼 문자열 정책을 따로 고른다.

## 한눈에 보기

| 질문 | 먼저 보는 것 | 초급자용 첫 선택 |
|---|---|---|
| `1.0`, `1.00`, `1`을 같은 값으로 모을까 | canonicalization 정책 | 입력 경계에서 한 번 정규화 |
| 정규화한 값을 로그/UI/문자열 API로 보낼까 | 문자열 출력 정책 | `toPlainString()` 먼저 검토 |
| 숫자 JSON으로 보낼까 | serializer 계약 | `toString()`/`toPlainString()`보다 라이브러리 설정 먼저 확인 |
| 내부 디버깅에서 기본 표현 자체가 궁금한가 | 기본 표현 확인 | `toString()`도 충분할 수 있음 |

초급 단계에서는 아래 한 줄이면 충분하다.

> "같은 값으로 한 번 맞춘 다음, 사람이 읽는 경계에서는 `toPlainString()`, 숫자 JSON은 serializer 계약"으로 나눈다.

## 상세 분해

### 1. 정규화와 출력은 다른 문제다

예를 들어 API 입구에서 `stripTrailingZeros()`로 값을 맞췄다고 하자.

- 이 단계의 목적은 `1.0`과 `1.00`을 같은 값으로 모으는 것이다.
- 아직 "어떤 문자열로 내보낼지"는 결정하지 않았다.
- 그래서 정규화가 끝났어도 `toString()`과 `toPlainString()` 선택은 여전히 남아 있다.

### 2. 왜 canonicalization 뒤에 더 헷갈리나

정규화 전에는 `1000.00`처럼 보이던 값이 정규화 뒤에는 scale이 줄어들 수 있다.
이때 `toString()`은 기본 표현을 택하고, 어떤 값에서는 지수 표기로 보일 수 있다.

초급자가 자주 겪는 혼동은 이렇다.

- "정규화했더니 값이 바뀐 건가?"
- "왜 API 응답에서 갑자기 `1E+3`이 나와?"
- "로그와 UI가 서로 다른 숫자를 보내는 건가?"

대부분은 값이 바뀐 게 아니라 문자열 표현 정책이 안 정해진 경우다.

### 3. 차이를 가장 짧게 보면

```java
import java.math.BigDecimal;

BigDecimal raw = new BigDecimal("1000.00");
BigDecimal normalized = raw.stripTrailingZeros();

System.out.println(raw.toPlainString());        // 1000.00
System.out.println(normalized.toString());      // 1E+3 형태가 나올 수 있음
System.out.println(normalized.toPlainString()); // 1000
```

초급자에게 중요한 포인트는 이것이다.

- 정규화는 내부 값을 같은 쪽으로 모으는 일이다.
- `toString()`은 그 정규화된 값을 기본 방식으로 보여 준다.
- `toPlainString()`은 사람이 읽기 쉽게 지수 표기 없이 펼쳐 준다.

### 4. `toString()`과 `toPlainString()`을 고르는 10초 비교표

| 메서드 | 초급자용 해석 | 주의할 점 |
|---|---|---|
| `toString()` | `BigDecimal`의 기본 문자열 표현 | 경우에 따라 지수 표기가 나올 수 있다 |
| `toPlainString()` | 지수 표기 없이 풀어서 보여 주는 문자열 | 사람이 읽기엔 편하지만, 출력 길이가 길어질 수 있다 |

## 흔한 오해와 함정

- `stripTrailingZeros()`를 했으니 출력도 자동으로 "보기 좋게" 정리된다고 생각하기 쉽다.
- `toPlainString()`을 쓰면 반올림, 소수 자리 고정, 통화 포맷까지 해결된다고 생각하기 쉽다.
- JSON 숫자 직렬화도 자바 코드에서 `toPlainString()`만 호출하면 끝난다고 생각하기 쉽다.
- `toString()`에 지수 표기가 나오면 값이 바뀌었다고 오해하기 쉽다.
- 내부 key canonicalization과 외부 API 문자열 계약을 같은 정책으로 취급하기 쉽다.

## 실무에서 쓰는 모습

### 1. 로그

운영 로그에서 사람이 직접 읽고 금액/비율을 확인해야 한다면 `toPlainString()`이 보통 더 안전하다.

```java
log.info("amount={}", amount.toPlainString());
```

이유는 단순하다.

- `1E+3`보다 `1000`이 초급자에게 더 바로 읽힌다.
- `1E-6`를 보면 "값이 깨졌나?"라고 오해하기 쉽다.

반대로, 내부 디버깅에서 기본 표현을 그대로 보고 싶으면 `toString()`도 나쁘지 않다.

핵심은 팀 로그 정책을 섞지 않는 것이다.

### 2. UI 표시

UI는 대부분 사람이 읽는 표면이므로 `toPlainString()` 쪽이 출발점으로 더 자연스럽다.

```java
String display = amount.toPlainString();
```

다만 UI는 여기서 끝나지 않는다.

- 천 단위 구분
- 통화 기호
- 고정 소수점 자리수

이런 문제는 `toPlainString()` 하나로 해결되지 않는다.
그래도 "지수 표기 없이 먼저 안전하게 문자열로 만들기"라는 첫 단계에서는 유용하다.

## API/직렬화 경계에서 보기

### 1. JSON

여기서 가장 많이 헷갈리는 점은 이것이다.

> JSON은 `toString()` vs `toPlainString()` 싸움이 아니라, "숫자로 보낼지 문자열로 보낼지" 계약 문제가 먼저다.

예를 들면:

```json
{ "amount": 1000 }
```

```json
{ "amount": "1000" }
```

초급자용 판단 기준은 아래처럼 단순하게 잡는 편이 좋다.

| JSON 계약 | 먼저 볼 것 | 초급자용 메모 |
|---|---|---|
| 숫자(`number`) | JSON serializer 설정 | Java 코드에서 직접 `toPlainString()` 호출이 안 보일 수 있다 |
| 문자열(`string`) | `toPlainString()` 같은 출력 정책 | 사람이 읽는 계약을 고정하기 쉽다 |

- 숫자로 보내면 소비자 언어와 serializer 설정 영향도 함께 본다.
- 문자열로 보내면 표현을 직접 통제하기 쉽지만, validation 책임이 늘어난다.

즉 JSON에서는 "문자열로 보낼 때 `toPlainString()`이 자주 유용하다"가 핵심이지, 모든 JSON이 무조건 문자열이어야 한다는 뜻은 아니다.

### 2. API boundary 예시: canonicalization 뒤 어떤 문자열을 보낼까

```java
import java.math.BigDecimal;

record AmountResponse(String amount) {
    static AmountResponse from(BigDecimal raw) {
        BigDecimal canonical = raw.stripTrailingZeros();
        return new AmountResponse(canonical.toPlainString());
    }
}
```

이 예시에서 읽어야 할 순서는 이렇다.

1. `stripTrailingZeros()`는 내부 canonical value를 만든다.
2. `toPlainString()`은 API 바깥으로 보낼 문자열을 만든다.
3. "같은 값으로 모으기"와 "사람이 읽게 보내기"를 한 메서드에 섞지 않고, 코드에서 두 단계가 보이게 둔다.

초급자라면 특히 아래 표처럼 고르면 된다.

| API 바깥 계약 | 첫 선택 | 이유 |
|---|---|---|
| 사람이 읽는 문자열 응답 | `toPlainString()` | `1E+3` surprise를 줄이기 쉽다 |
| 숫자 JSON 응답 | serializer 설정 점검 | 문자열 메서드보다 직렬화 계약이 먼저다 |
| 내부 디버깅용 문자열 | `toString()` 또는 둘 다 출력 | 기본 표현과 표시 표현을 비교하기 쉽다 |

## 더 깊이 가려면

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| API 입구에서 `1.0`, `1.00`, `1`을 언제 한 번 맞출지 먼저 정하고 싶다 | [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md) |
| key canonicalization과 출력 정책을 같이 점검하고 싶다 | [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md) |
| 입력 생성부터 흔들리지 않게 고르고 싶다 | [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md) |
| 돈, 반올림, 직렬화 계약까지 한 번에 보고 싶다 | [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md) |
| JSON/직렬화 일반 경계를 더 넓게 보고 싶다 | [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md) |

## 면접/시니어 질문 미리보기

> Q. 왜 canonicalization 뒤에도 `toString()`과 `toPlainString()`을 따로 골라야 하나요?
> 핵심: 정규화는 내부 값 표현 통일이고, 두 메서드는 외부 문자열 계약을 고르는 문제이기 때문이다.

> Q. API가 숫자 JSON을 내려주면 `toPlainString()`은 필요 없나요?
> 핵심: 숫자 JSON은 serializer 계약이 우선이지만, 로그/UI/문자열 응답에는 여전히 출력 정책이 필요하다.

> Q. `toPlainString()`이면 출력 정책이 끝난 건가요?
> 핵심: 아니다. 천 단위, 통화, 고정 소수점, locale은 별도 포맷 정책이다.

## 한 줄 정리

초급자 기준 `BigDecimal` API 출력은 "입력 경계에서 같은 값으로 한 번 맞추고, 사람이 읽는 문자열 경계에서는 `toPlainString()`, 숫자 JSON은 serializer 계약"으로 나누어 이해하면 된다.
