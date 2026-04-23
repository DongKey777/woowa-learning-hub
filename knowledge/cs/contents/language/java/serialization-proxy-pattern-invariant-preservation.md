# Serialization Proxy Pattern and Invariant Preservation

> 한 줄 요약: Java native serialization에서 내부 표현을 직접 직렬화하면 필드 구조와 불변식이 외부 계약이 된다. serialization proxy pattern은 `writeReplace`/`readResolve`로 안정된 proxy를 직렬화해 value object 불변식과 진화 여지를 더 잘 지키게 해준다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Serialization Compatibility and `serialVersionUID`](./serialization-compatibility-serial-version-uid.md)
> - [`serialPersistentFields`, `readObjectNoData`, and Native Serialization Evolution Escape Hatches](./serialpersistentfields-readobjectnodata-evolution-escape-hatches.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)

> retrieval-anchor-keywords: serialization proxy pattern, writeReplace, readResolve, InvalidObjectException, invariant preservation, native serialization, serialization evolution, stable proxy schema, value object serialization, Effective Java, serial proxy, readObject guard, serialPersistentFields

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

기본 Java serialization은 객체의 내부 필드 구조를 그대로 바깥으로 드러내기 쉽다.  
그러면 내부 표현이 곧 직렬화 계약이 된다.

serialization proxy pattern은 이 문제를 줄인다.

- 실제 객체 대신 proxy 객체를 직렬화한다
- 역직렬화는 proxy가 원본 객체를 다시 생성한다
- 원본 객체는 직접 역직렬화되지 않게 막는다

즉 "객체 상태 덤프"가 아니라 "안정된 재구성 계약"으로 직렬화를 바꾸는 패턴이다.

## 깊이 들어가기

### 1. 왜 기본 직렬화가 value object에 거칠 수 있나

value object는 보통 생성 시점에 invariant를 잠근다.

- 정규화
- 범위 검사
- canonical form 강제
- 필드 간 상호 제약

그런데 기본 직렬화는 내부 필드 값을 그대로 복원하기 때문에,  
생성자 규칙이 우회되기 쉽다.

즉 정상 생성 경로와 역직렬화 경로가 다른 의미를 가질 수 있다.

### 2. proxy는 "재구성에 필요한 최소 계약"만 노출한다

proxy 클래스에는 보통 외부 계약으로 유지하고 싶은 최소 필드만 둔다.

- 공개 의미에 필요한 값
- 안정적으로 진화시킬 수 있는 표현
- 원본 객체를 다시 만들 수 있는 정보

즉 내부 캐시, 파생 필드, 구현 세부는 원본 객체에 남기고  
직렬화 계약은 proxy가 담당한다.

### 3. `writeReplace`와 `readResolve`가 흐름의 핵심이다

전형적인 흐름:

- 원본 객체가 `writeReplace()`로 proxy를 반환
- proxy가 직렬화된다
- proxy가 `readResolve()`로 원본 객체를 재구성한다

그리고 원본 객체의 `readObject()`는 보통 직접 역직렬화를 막기 위해 실패시킨다.

이렇게 해야 "항상 proxy 경유" 규칙이 강제된다.

### 4. proxy도 versioned contract다

serialization proxy를 쓴다고 evolution 문제가 사라지는 것은 아니다.  
다만 어떤 필드를 계약으로 삼을지 더 의식적으로 고를 수 있다.

즉 proxy 패턴의 장점은 마법이 아니라 boundary control이다.

### 5. 모든 타입에 과한 것은 아니다

단순 DTO나 short-lived cache object에는 과할 수 있다.  
하지만 다음에는 가치가 크다.

- value object
- 불변식이 중요한 타입
- 내부 표현을 숨기고 싶은 타입
- 장기 저장 또는 서로 다른 버전 간 호환성이 중요한 타입

## 실전 시나리오

### 시나리오 1: 역직렬화 후 invalid object가 생긴다

생성자에서는 음수 금액을 막는데,  
역직렬화는 내부 필드만 복원해서 invalid state가 들어온다.

proxy를 쓰면 재구성 경로를 생성자/팩토리로 통일할 수 있다.

### 시나리오 2: 내부 표현을 바꿨더니 오래된 데이터가 깨진다

원래는 `BigDecimal` 하나였는데 이후 `currency + minorUnit long`으로 바꿨다.  
기본 직렬화라면 내부 구조 변화가 바로 호환성 문제로 번진다.

proxy라면 이전 계약을 유지하며 내부 표현을 교체할 여지가 생긴다.

### 시나리오 3: 파생 필드와 캐시 필드가 계약에 섞인다

성능 때문에 넣은 derived field가 직렬화 포맷에 섞이면,  
구현 최적화가 external contract가 되어버린다.

## 코드로 보기

### 1. 원본 객체는 proxy를 내보낸다

```java
import java.io.InvalidObjectException;
import java.io.ObjectInputStream;
import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;

public final class Percent implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    private final BigDecimal value;

    public Percent(BigDecimal value) {
        if (value.signum() < 0 || value.compareTo(new BigDecimal("100")) > 0) {
            throw new IllegalArgumentException("percent out of range");
        }
        this.value = value.stripTrailingZeros();
    }

    @Serial
    private Object writeReplace() {
        return new SerializationProxy(value.toPlainString());
    }

    @Serial
    private void readObject(ObjectInputStream in) throws InvalidObjectException {
        throw new InvalidObjectException("proxy required");
    }

    private static final class SerializationProxy implements Serializable {
        @Serial
        private static final long serialVersionUID = 1L;

        private final String decimal;

        private SerializationProxy(String decimal) {
            this.decimal = decimal;
        }

        @Serial
        private Object readResolve() {
            return new Percent(new BigDecimal(decimal));
        }
    }
}
```

### 2. 핵심 감각

```java
// 직렬화 계약은 proxy가 가진다.
// 원본 객체는 항상 생성자 규칙을 통과해서만 복원된다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| 기본 직렬화 | 구현이 단순하다 | 내부 표현과 invariant가 외부 계약에 노출되기 쉽다 |
| serialization proxy | 경계를 통제하고 invariant를 재적용하기 쉽다 | 보일러플레이트와 진화 설계가 필요하다 |
| JSON/schema DTO | 명시성과 상호운용성이 높다 | native serialization보다 코드가 더 필요하다 |

핵심은 직렬화가 "현재 필드를 덤프하는가" 아니면 "의미를 재구성하는가"를 선택하는 것이다.

## 꼬리질문

> Q: serialization proxy pattern은 왜 쓰나요?
> 핵심: 내부 표현 대신 안정된 proxy 계약만 직렬화해 invariant와 진화 여지를 지키기 위해서다.

> Q: `readObject()`를 왜 막나요?
> 핵심: 원본 객체가 proxy를 우회해 직접 역직렬화되는 경로를 차단하기 위해서다.

> Q: proxy를 쓰면 호환성 문제가 사라지나요?
> 핵심: 아니지만, 어떤 필드를 계약으로 유지할지 더 의식적으로 통제할 수 있다.

> Q: 모든 `Serializable` 타입에 필요한가요?
> 핵심: 아니다. value object나 invariants가 중요한 타입에서 특히 가치가 크다.

## 한 줄 정리

serialization proxy pattern은 native serialization에서도 생성자 규칙과 불변식을 다시 중심에 놓게 해주는 boundary-control 패턴이다.
