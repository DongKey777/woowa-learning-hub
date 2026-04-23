# Enum Persistence, JSON, and Unknown Value Evolution

> 한 줄 요약: enum은 코드 안에서는 닫힌 집합처럼 보이지만, DB/JSON/메시지 경계를 넘는 순간 이름과 저장 방식이 곧 외부 계약이 된다. `ordinal()`에 기대거나 `Enum.valueOf()`만 믿으면 배포 순서와 스키마 진화에 취약해진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)
> - [Java Binary Compatibility and Runtime Linkage Errors](./java-binary-compatibility-linkage-errors.md)
> - [Sealed Interfaces and Exhaustive Switch Design](./sealed-interfaces-exhaustive-switch-design.md)

> retrieval-anchor-keywords: enum evolution, Enum.ordinal, Enum.name, Enum.valueOf, unknown enum value, EnumType.STRING, JSON enum, database enum persistence, wire contract, backward compatibility, forward compatibility, schema evolution, code mapping, switch exhaustiveness

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

enum은 코드 안에선 안전해 보인다.

- 가능한 값 집합이 명확하다
- `switch`가 읽기 쉽다
- equality와 hash가 안정적이다

하지만 외부 경계에서는 다른 질문이 생긴다.

- DB에 무엇을 저장할 것인가
- JSON에는 어떤 문자열을 내보낼 것인가
- 아직 모르는 새 값이 들어오면 어떻게 할 것인가
- constant 이름을 바꿔도 되는가

즉 enum은 문법 설탕이 아니라 wire contract 후보로 봐야 한다.

## 깊이 들어가기

### 1. `ordinal()`은 저장 형식으로 거의 항상 위험하다

`ordinal()`은 선언 순서다.  
비즈니스 의미가 아니라 소스 코드 위치에 의존한다.

그래서 다음이 모두 위험하다.

- enum 상수 순서 재배치
- 중간 상수 추가
- 일부 상수 삭제

DB나 메시지에 ordinal을 저장하면, 코드 리팩터링이 데이터 오염으로 번질 수 있다.

### 2. `name()`은 `ordinal()`보다 낫지만, 여전히 계약이다

`name()` 기반 저장은 사람이 읽기 쉽고 상수 재배치에도 안전하다.  
그래서 JPA에서도 보통 `EnumType.STRING`이 더 안전한 기본값이다.

하지만 이것도 완전한 자유는 아니다.

- 상수 rename은 breaking change다
- producer가 새 enum을 보내면 old consumer는 모를 수 있다
- 대소문자와 spelling이 외부 계약이 된다

즉 `STRING`은 "리팩터링 자유"가 아니라 "의미를 이름에 고정한다"는 선택이다.

### 3. 외부 입력은 닫힌 집합이 아닐 수 있다

코드 안의 enum 집합은 닫혀 있어도, 외부 시스템은 더 빨리 진화할 수 있다.

예를 들어 partner API가 새 상태 `PARTIALLY_REFUNDED`를 추가하면:

- old consumer의 `Enum.valueOf()`는 `IllegalArgumentException`을 던질 수 있다
- JSON binder는 역직렬화 실패로 요청 전체를 버릴 수 있다
- analytics/replay pipeline은 과거 이벤트 재처리에서 깨질 수 있다

그래서 external enum은 unknown handling 전략이 필요하다.

### 4. unknown handling은 도메인 정책이다

선택지는 보통 셋이다.

- strict fail: 모르는 값이면 바로 실패
- sentinel fallback: `UNKNOWN`으로 흡수
- raw value 보존: 원문 문자열을 별도 필드로 저장

어느 것이 맞는지는 맥락에 달려 있다.

- 결제 상태처럼 보수적으로 막아야 하는가
- 알림 타입처럼 일부 기능만 건너뛰면 되는가
- 저장 후 나중에 재처리할 수 있어야 하는가

즉 unknown enum은 파서 문제가 아니라 compatibility 정책 문제다.

### 5. 때로는 enum보다 명시적 코드 값 객체가 낫다

값 집합이 외부 시스템 소유이거나 자주 진화하면 enum이 오히려 경직될 수 있다.

이때 고려할 것:

- `enum + code` 필드
- `String` 기반 value object
- sealed hierarchy + unknown variant

즉 "닫힌 집합"이라는 전제가 약하면 enum 하나로 버티기보다 모델을 분리하는 편이 낫다.

## 실전 시나리오

### 시나리오 1: JPA에서 `ORDINAL`을 썼다가 상수 순서를 바꿨다

운영 DB의 숫자 `2`가 어제는 `SHIPPED`였는데 오늘은 `CANCELED`로 읽힌다.  
이건 마이그레이션 누락이 아니라 저장 계약을 잘못 고른 문제다.

### 시나리오 2: 새 producer가 새 enum 값을 보냈다

이벤트 consumer는 enum 역직렬화에 실패해 메시지를 계속 재시도한다.  
dead letter queue가 쌓이고, old consumer가 새 producer rollout을 막는다.

### 시나리오 3: enum 이름을 예쁘게 바꿨다

`PAYMENT_WAITING`을 `PENDING_PAYMENT`로 rename했다.  
코드 검색은 좋아졌지만 기존 JSON, DB 값, 캐시 키, 로그 재생성, BI 파이프라인이 모두 흔들릴 수 있다.

### 시나리오 4: `switch`가 exhaustive라서 안심했다

내부 도메인 enum이라면 장점이지만, 외부 입력을 그대로 enum으로 받는다면 새 값 도입 시 런타임 실패로 이어질 수 있다.  
closed world와 external contract를 구분해야 한다.

## 코드로 보기

### 1. ordinal 저장은 피하기

```java
public enum OrderStatus {
    CREATED,
    PAID,
    SHIPPED
}
```

이 enum의 `ordinal()`은 저장 계약으로 쓰기엔 너무 취약하다.

### 2. 명시적 wire code를 가진 enum

```java
public enum OrderStatus {
    CREATED("created"),
    PAID("paid"),
    SHIPPED("shipped"),
    UNKNOWN("unknown");

    private final String code;

    OrderStatus(String code) {
        this.code = code;
    }

    public String code() {
        return code;
    }

    public static OrderStatus fromCode(String raw) {
        for (OrderStatus status : values()) {
            if (status.code.equals(raw)) {
                return status;
            }
        }
        return UNKNOWN;
    }
}
```

### 3. 원문 보존까지 같이 하기

```java
public record ParsedStatus(OrderStatus status, String rawCode) {
    public static ParsedStatus parse(String raw) {
        return new ParsedStatus(OrderStatus.fromCode(raw), raw);
    }
}
```

### 4. switch boundary 분리

```java
switch (parsedStatus.status()) {
    case CREATED -> startFlow();
    case PAID -> settle();
    case SHIPPED -> notifyCustomer();
    case UNKNOWN -> storeForReview(parsedStatus.rawCode());
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `ordinal()` 저장 | 공간이 작다 | 순서 변경에 매우 취약하다 |
| `name()`/`EnumType.STRING` 저장 | 읽기 쉽고 재배치에 안전하다 | rename이 breaking change가 된다 |
| 명시적 wire code | 내부 이름과 외부 계약을 분리할 수 있다 | 변환 코드와 문서화가 필요하다 |
| unknown fallback | forward compatibility를 높인다 | 잘못 쓰면 오류를 조용히 숨길 수 있다 |

핵심은 enum 상수 집합보다 "경계를 넘을 때 어떤 문자열이나 숫자를 계약으로 고정할 것인가"다.

## 꼬리질문

> Q: JPA에서 왜 `EnumType.ORDINAL`보다 `STRING`이 보통 낫나요?
> 핵심: ordinal은 선언 순서에 묶여 리팩터링과 상수 추가에 매우 취약하기 때문이다.

> Q: `Enum.valueOf()`만 쓰면 왜 위험한가요?
> 핵심: 모르는 새 값이 들어오면 역직렬화 전체가 실패할 수 있어서다.

> Q: enum 이름을 바꾸는 건 단순 리팩터링 아닌가요?
> 핵심: DB/JSON/메시지에 이름이 노출됐다면 rename은 외부 계약 변경이다.

> Q: unknown 값을 `UNKNOWN`으로 다 흡수하면 안전한가요?
> 핵심: forward compatibility에는 도움 되지만, 중요한 새 상태를 숨길 수 있어 도메인별 정책이 필요하다.

## 한 줄 정리

enum은 코드 안의 닫힌 집합이지만 외부 경계에선 storage/wire contract이므로, `ordinal()`을 피하고 explicit code와 unknown handling 정책을 함께 설계하는 것이 안전하다.
