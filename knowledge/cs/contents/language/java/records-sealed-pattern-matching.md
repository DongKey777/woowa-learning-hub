# Records, Sealed Classes, Pattern Matching

> 한 줄 요약: Modern Java 문법은 단순 문법 당근이 아니라, 도메인 모델을 덜 지저분하게 표현하기 위한 도구다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)
> - [Sealed Interfaces and Exhaustive Switch Design](./sealed-interfaces-exhaustive-switch-design.md)
> - [Record/Sealed Hierarchy Evolution and Pattern Matching Compatibility](./record-sealed-hierarchy-evolution-pattern-matching-compatibility.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)

> retrieval-anchor-keywords: record, sealed class, pattern matching, DTO, value object, permits, exhaustive switch, hierarchy evolution, variant compatibility, record equals hashCode, record component equality, record shallow immutability

## 핵심 개념

`record`, `sealed class`, `pattern matching`은 서로 연결된 현대 Java 기능이다.

왜 중요한가:

- DTO와 값 객체를 덜 장황하게 표현할 수 있다
- 상속 구조를 통제할 수 있다
- 조건 분기 코드를 더 읽기 쉽게 만들 수 있다

## 깊이 들어가기

### 1. record

record는 데이터 전달용 불변 객체를 짧게 선언하는 방식이다.

### 2. sealed class

sealed class는 상속 가능한 타입을 제한한다.  
도메인 상태가 제한적일 때 유용하다.

### 3. pattern matching

타입 체크와 캐스팅을 줄여 분기 코드를 단순화한다.

## 실전 시나리오

### 시나리오 1: 이벤트 타입이 몇 개로 고정돼 있다

sealed class로 타입 폭발을 막을 수 있다.

### 시나리오 2: 단순 DTO가 너무 장황하다

record로 생성자/getter/equals/hashCode를 덜 쓸 수 있다.

## 코드로 보기

```java
public sealed interface PaymentResult permits Success, Failure {}

public record Success(String transactionId) implements PaymentResult {}
public record Failure(String reason) implements PaymentResult {}
```

```java
switch (result) {
    case Success s -> handleSuccess(s.transactionId());
    case Failure f -> handleFailure(f.reason());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| record | 짧고 명확 | mutable 모델엔 부적합 | 값 객체/DTO |
| sealed | 타입 안전 | 구조 변경 비용 | 상태가 제한적일 때 |
| pattern matching | 가독성 좋음 | 버전/문법 의존 | 분기 로직 단순화 |

## 꼬리질문

> Q: record는 언제 쓰면 안 되는가?
> 의도: 불변성과 도메인 모델 구분 여부 확인
> 핵심: mutable aggregate에는 부적절하다.

> Q: sealed class가 왜 유용한가?
> 의도: 상속 통제의 의미 이해 여부 확인
> 핵심: 허용된 하위 타입만 관리할 수 있다.

## 한 줄 정리

record, sealed, pattern matching은 Java를 더 짧게 쓰게 하는 기능이 아니라, 도메인 타입을 더 안전하게 표현하게 해주는 기능이다.
