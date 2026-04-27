# Marker Interface vs Capability Method 브리지

> 한 줄 요약: 처음 배우는데 `Serializable` 같은 marker interface와 `supportsRetry()` 같은 capability-style method가 비슷해 보인다면, marker는 "이 타입은 이 분류에 속한다"를 타입 자체에 붙이는 표지이고, capability method는 "지금 이 객체가 이 기능을 지원하나"를 런타임에 묻는 답변창이라고 먼저 나누면 된다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)
> - [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
> - [인터페이스 `default method` vs `static` method 프라이머](./interface-default-vs-static-method-primer.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)
> - [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)

> retrieval-anchor-keywords: marker interface vs capability method, marker interface beginner, capability method beginner, supportsX method design, supportsRetry design, marker interface 언제 쓰는지, capability method 언제 쓰는지, marker interface와 supports 차이, marker interface vs supports method, serializable marker interface meaning, marker interface type tag beginner, capability-style method primer, interface 설계 기초, 인터페이스 설계 첫 진입점, 인터페이스 설계 큰 그림, 처음 배우는데 marker interface, 처음 배우는데 supportsX, 처음 배우는데 interface 설계, can-do method vs type marker, runtime capability check beginner, 타입 표지 vs 런타임 질문, marker interface can-do confusion, marker interface 남용, capability method 남용

## 먼저 잡을 mental model

처음 배우는데 이 둘이 같이 나오면 둘 다 "기능을 나타내는 인터페이스"처럼 보여서 헷갈린다.

하지만 초급 기준에서는 질문을 둘로 자르면 된다.

- **marker interface**: "이 타입은 이 특별한 분류에 속하나?"
- **capability method**: "이 객체는 지금 이 기능을 지원하나?"

짧게 외우면 이렇다.

> marker는 **타입 표지**, capability method는 **런타임 답변**이다.

## 한 장 비교 표

| 질문 | marker interface | capability-style method |
|---|---|---|
| 대표 모양 | `interface Cacheable {}` | `boolean supportsRetry()` |
| 핵심 답 | "이 타입은 이 그룹에 속한다" | "지금 이 객체는 이 기능을 지원한다/안 한다" |
| 판단 시점 | 타입 선언 시점에 거의 고정 | 호출 시점에 확인 |
| 값의 성격 | 보통 예/아니오가 타입에 붙음 | 구현체/설정/상태에 따라 달라질 수 있음 |
| 잘 맞는 질문 | 분류, 제약, 프레임워크 훅 | 옵션 기능, 지원 여부, 정책 차이 |
| 초급 기억법 | 배지 붙이기 | 물어보고 대답받기 |

## 언제 marker interface를 먼저 떠올리나

다음 질문이면 marker 쪽이 더 자연스럽다.

- "이 타입이 특정 그룹 소속인지 타입 수준에서 구분해야 하나?"
- "프레임워크나 공통 로직이 `instanceof`나 제네릭 bound로 이 그룹을 한 번에 다루나?"
- "객체 상태가 바뀌어도 이 분류 자체는 흔들리지 않나?"

예를 들어 `Serializable`은 "이 객체가 지금 기분 좋으면 직렬화 가능"이 아니라, **이 타입은 직렬화 대상으로 취급해도 된다**는 표지에 가깝다.

```java
interface Exportable {}

final class Report implements Exportable {}
final class DashboardWidget {}
```

```java
void enqueueForExport(Object target) {
    if (target instanceof Exportable) {
        System.out.println("내보내기 큐에 추가");
    }
}
```

이 코드는 "내보내기 기능을 수행한다"보다 "내보내기 대상 그룹에 속한다"를 구분하는 쪽에 가깝다.

## 언제 capability method를 먼저 떠올리나

다음 질문이면 `supportsX()` 같은 capability method가 더 자연스럽다.

- "지원 여부가 구현체마다 다를 수 있나?"
- "같은 타입 계열이라도 설정, 환경, 정책에 따라 답이 달라질 수 있나?"
- "호출자가 행동 전에 '가능한지'를 물어보는 흐름이 자연스러운가?"

```java
interface AlarmSender {
    void send(String message);

    default boolean supportsRetry() {
        return false;
    }
}

final class SmsAlarmSender implements AlarmSender {
}

final class KafkaAlarmSender implements AlarmSender {
    @Override
    public boolean supportsRetry() {
        return true;
    }
}
```

여기서 `supportsRetry()`는 "이 타입은 Retryable 그룹이다"보다, **이 구현체는 재시도 기능을 제공하나**를 묻는 질문에 가깝다.

즉 capability method는 "배지"보다 "질문-응답" 문장에 더 잘 맞는다.

## 처음 설계할 때 20초 판단 순서

처음 배우는데 interface 설계가 막히면 아래 순서로 보면 된다.

1. 내가 붙이려는 것이 **분류**인지 **행동/지원 여부**인지 먼저 자른다.
2. 타입에 한 번 붙으면 거의 안 바뀌는 분류면 marker를 검토한다.
3. 구현체나 상황에 따라 달라질 수 있는 답이면 capability method를 검토한다.
4. "지원 여부"를 물은 뒤 실제 동작까지 이어질 거라면, capability method와 실제 행동 메서드를 같이 설계한다.

짧게 쓰면:

- **고정된 타입 표지**면 marker
- **실행 전 물어볼 기능 지원 여부**면 `supportsX()`

## 같은 주제를 두 방식으로 보면 차이가 더 잘 보인다

### 1. "이 타입은 감사 대상인가?"

이 질문은 타입 분류에 가깝다.

```java
interface Auditable {}

final class Order implements Auditable {}
final class Product {}
```

감사 로직은 `Auditable` 그룹 전체를 다루면 된다.

### 2. "이 저장소는 지금 batch insert를 지원하나?"

이 질문은 지원 여부에 가깝다.

```java
interface UserRepository {
    void save(User user);

    default boolean supportsBatchInsert() {
        return false;
    }
}
```

이 경우 호출자는 동작 전에 선택지를 나눌 수 있다.

```java
if (repository.supportsBatchInsert()) {
    System.out.println("batch path");
} else {
    System.out.println("single insert path");
}
```

이 코드는 "저장소라는 타입 분류"보다 "현재 구현체가 어느 기능까지 제공하나"를 묻는다.

## 자주 하는 오해

### marker interface가 보이면 무조건 옛날 방식이라고 보면 안 된다

현대 Java에서는 annotation이나 명시적 메서드가 더 읽기 쉬운 경우가 많다. 그래도 **타입 자체를 특정 그룹으로 묶는 목적**이라면 marker interface가 여전히 설명력이 있을 수 있다.

### capability method가 있으면 marker가 필요 없다고 단정하면 안 된다

둘은 질문 층위가 다르다.
`Auditable`처럼 그룹을 묶는 표지와 `supportsBatchInsert()` 같은 지원 여부 질문은 같은 문제를 풀지 않는다.

### `supportsX()`가 있으면 실제 동작 메서드도 같이 생각해야 한다

`supportsRetry()`만 있고 retry 관련 행동이 어디에 붙는지 불분명하면 API가 흐려진다. 초급 설계에서는 "지원 여부 질문"과 "실제 행동"이 어떤 흐름으로 이어지는지 같이 보는 편이 좋다.

### marker를 너무 많이 만들면 타입 이름만 늘어나고 의미는 약해질 수 있다

빈 인터페이스를 많이 추가했는데 공통 처리, 제약, 분류 이점이 없다면 beginner 관점에서는 "배지만 많고 규칙은 없는 상태"가 되기 쉽다.

## 큰 그림에서 어디와 연결되나

- "인터페이스냐 추상 클래스냐"가 먼저 헷갈리면 [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)
- `supportsRetry()` 같은 메서드가 왜 `default method` 예시로 자주 나오는지 궁금하면 [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- 결국 상속보다 역할 인터페이스 + 조합으로 가는 이유를 더 넓게 보려면 [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)

## 한 줄 정리

처음 배우는데 marker interface와 `supportsX()`가 둘 다 "기능 표시"처럼 보이면, marker는 타입에 붙이는 고정 배지, capability method는 객체에게 지금 가능한지 묻는 런타임 질문이라고 나누면 interface 설계의 첫 진입점이 훨씬 선명해진다.
