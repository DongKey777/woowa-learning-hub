# 인터페이스 `default method` vs `static` method 프라이머

> 한 줄 요약: 처음 배우는데 인터페이스 메서드 몸체가 둘 다 보여 헷갈린다면, `default method`는 "구현체에게도 보이는 기본 동작", interface `static` method는 "인터페이스 이름으로만 부르는 도우미"라고 먼저 나누면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md)
- [Collection vs Collections vs Arrays 유틸리티 미니 브리지](./collection-vs-collections-vs-arrays-utility-mini-bridge.md)
- [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)

retrieval-anchor-keywords: interface default vs static method, default method vs static method beginner, default method 언제 쓰는지, interface static method 언제 쓰는지, interface static method vs utility class, interface static method utility class 차이, 인터페이스 static 메서드 vs 유틸리티 클래스, 인터페이스 static 메서드 언제 쓰는지, utility class 언제 쓰는지, 정적 메서드 어디에 두나, interface 안에 둘지 utility class로 뺄지, interface private helper method, interface private method 언제 쓰는지, 처음 배우는데 default method와 static method 차이

<details>
<summary>Table of Contents</summary>

- [처음 배우는데 왜 헷갈리나](#처음-배우는데-왜-헷갈리나)
- [큰 그림 한 장으로 구분하기](#큰-그림-한-장으로-구분하기)
- [코드로 보는 `default`와 `static`](#코드로-보는-default와-static)
- [interface `private` helper는 어디에 끼나](#interface-private-helper는-어디에-끼나)
- [언제 쓰는지 빠른 기준](#언제-쓰는지-빠른-기준)
- [interface `static` method와 별도 utility class는 언제 나누나](#interface-static-method와-별도-utility-class는-언제-나누나)
- [자주 하는 오해](#자주-하는-오해)
- [다음에 읽을 문서](#다음에-읽을-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 처음 배우는데 왜 헷갈리나

처음 배우는데 인터페이스를 보면 보통 이렇게 기억한다.

- 인터페이스는 계약이다
- 구현체가 `implements`해서 메서드를 채운다

그런데 Java 8 이후 인터페이스 안에 이런 메서드가 같이 보인다.

- `default void log() { ... }`
- `static boolean isBlank(...) { ... }`

둘 다 몸체가 있으니 같은 종류처럼 보이지만, beginner 단계에서는 역할을 먼저 자르는 편이 덜 헷갈린다.

- `default method`: 구현체 인스턴스가 바로 물려받는 기본 동작
- interface `static` method: 인터페이스 이름으로만 부르는 도우미

즉 둘 다 "몸체가 있는 메서드"라는 공통점은 있지만, 호출 위치와 책임이 다르다.

## 큰 그림 한 장으로 구분하기

| 질문 | `default method` | interface `static` method |
|---|---|---|
| 누가 바로 쓰나 | 구현체 인스턴스 | 인터페이스 이름 |
| 호출 모양 | `sender.sendAll(...)` | `AlarmSender.isRetryableMessage(...)` |
| override 가능한가 | 예 | 아니오 |
| 핵심 역할 | 기존 계약 위에 기본 동작/편의 메서드 추가 | 인터페이스와 가까운 헬퍼 규칙 묶기 |
| 구현체 상태/다른 추상 메서드 활용 | 가능 | 인스턴스 상태 없음 |
| beginner용 한 문장 | "구현체 쪽에 내려가는 기본 기능" | "인터페이스 옆에 둔 유틸리티" |

처음 배우는데는 아래 두 문장만 먼저 기억해도 충분하다.

- `default method`는 **구현체가 상속받는 기본 동작**이다.
- interface `static` method는 **구현체가 물려받지 않는 정적 도우미**다.

## 코드로 보는 `default`와 `static`

### 1. `default method`는 구현체가 바로 쓴다

```java
public interface AlarmSender {
    void send(String message);

    default void sendAll(List<String> messages) {
        for (String message : messages) {
            send(message);
        }
    }
}
```

```java
AlarmSender sender = new SmsAlarmSender();
sender.sendAll(List.of("a", "b"));
```

여기서 `sendAll(...)`은 구현체가 따로 만들지 않아도 인스턴스 호출이 된다. 이유는 이 메서드가 "구현체에게 기본으로 내려가는 동작"이기 때문이다.

또한 `default method`는 이미 있는 추상 메서드 `send(...)`를 조합해 편의 기능을 만들 수 있다.

### 2. interface `static` method는 인터페이스 이름으로만 부른다

```java
public interface AlarmSender {
    void send(String message);

    static boolean isRetryableMessage(String message) {
        return message != null && !message.isBlank();
    }
}
```

```java
boolean retryable = AlarmSender.isRetryableMessage(message);
```

이 메서드는 `SmsAlarmSender` 객체가 물려받지 않는다.

```java
AlarmSender sender = new SmsAlarmSender();
sender.isRetryableMessage("hello"); // 컴파일 에러
```

- `default method`는 "구현체 인스턴스에 붙는 메서드"
- interface `static` method는 "인터페이스 이름으로 직접 부르는 메서드"

### 3. 둘을 나란히 두면 역할이 더 잘 보인다

```java
public interface AlarmSender {
    void send(String message);

    default void sendIfValid(String message) {
        if (isSendableMessage(message)) {
            send(message);
        }
    }

    static boolean isSendableMessage(String message) {
        return message != null && !message.isBlank();
    }
}
```

- `sendIfValid(...)`: 구현체가 바로 쓰는 기본 동작
- `isSendableMessage(...)`: 그 동작을 돕는 정적 규칙

즉 `default method`는 "행동 entrypoint", `static` method는 "옆에서 돕는 규칙/헬퍼"로 보면 이해가 빠르다.

## interface `private` helper는 어디에 끼나

Java에서는 interface 안에 `private` 메서드도 둘 수 있다. 처음 배우는데는 이것을 "세 번째 entrypoint"로 보면 안 되고, **interface 내부에서만 재사용하는 helper**로 보면 된다.

| 질문 | `default method` | interface `static` method | interface `private` method |
|---|---|---|---|
| 누가 호출하나 | 구현체 인스턴스 | 인터페이스 이름 | interface 안의 다른 메서드 |
| 바깥에서 직접 호출 가능? | 가능 | 가능 | 불가 |
| 구현체가 상속하나 | 예 | 아니오 | 아니오 |
| override 가능한가 | 예 | 아니오 | 아니오 |
| beginner용 한 문장 | 기본 동작 | 정적 도우미 | 내부 중복 제거용 숨은 helper |

짧게 외우면 이렇게 구분된다.

- `default`: 구현체에게 내려가는 기본 동작
- `static`: 인터페이스 이름으로 부르는 공개 헬퍼
- `private`: interface 안에서만 쓰는 비공개 helper

```java
public interface AlarmSender {
    void send(String message);

    default void sendIfValid(String message) {
        if (isSendable(message)) {
            send(message);
        }
    }

    private boolean isSendable(String message) {
        return message != null && !message.isBlank();
    }
}
```

이 예시에서 `isSendable(...)`은 구현체도, 호출자도 직접 못 쓴다. 역할은 하나다. `default method`나 `static method` 안에 반복되는 검사를 interface 내부에서만 숨겨 두는 것이다.

그래서 beginner 기준 첫 구분은 "밖에서 부르나, 안에서만 쓰나"다.

- 밖에서 인스턴스로 부르면 `default`
- 밖에서 interface 이름으로 부르면 `static`
- 밖에서 못 부르고 interface 안에서만 쓰면 `private`

## 언제 쓰는지 빠른 기준

### 이런 질문이면 `default method` 쪽이다

- "구현체가 공통으로 바로 쓸 동작인가?"
- "이미 있는 추상 메서드를 묶어 편의 메서드를 만들고 싶은가?"
- "기존 구현체를 덜 깨뜨리며 작은 기능을 추가하고 싶은가?"

예:

- `sendAll(...)`
- `isEmpty()`를 다른 추상 메서드 조합으로 제공
- `supportsRetry()` 같은 기본값 제공

### 이런 질문이면 interface `static` method 쪽이다

- "이 규칙이 특정 구현체 인스턴스 없이도 설명되는가?"
- "인터페이스 옆에 두면 의미상 가깝지만, 구현체가 물려받을 필요는 없는가?"
- "검사/파싱/보조 규칙 같은 helper인가?"

예:

- `ofCode(int code)` 같은 간단한 lookup 보조
- `isValidFormat(String raw)` 같은 검사
- `normalize(String raw)` 같은 정적 정리 함수

## interface `static` method와 별도 utility class는 언제 나누나

처음 배우는데 이 지점에서 자주 막힌다.

- "`static`이면 그냥 interface 안에 두면 되나?"
- "왜 어떤 건 `Collections` 같은 utility class로 빠지지?"

큰 그림은 짧다.

- **이 규칙이 그 인터페이스를 읽는 사람에게 거의 붙어 있어야 하면** interface `static` method
- **여러 타입이 같이 쓰는 범용 규칙이면** 별도 utility class

| 질문 | interface `static` method | 별도 utility class |
|---|---|---|
| 어디에 두면 읽는 흐름이 자연스러운가 | 해당 인터페이스 바로 옆 | 여러 타입이 공유하는 공용 도구함 |
| 누구를 중심으로 읽나 | "이 계약 주변 규칙" | "이 타입 저 타입이 같이 쓰는 일반 규칙" |
| 대표 예 | `AlarmSender.isValidFormat(raw)` | `MessageFormats.normalize(raw)` |
| beginner용 한 문장 | 인터페이스 가까이에 둔 정적 helper | 인터페이스 밖으로 뺀 범용 정적 helper |

짧은 판단 기준은 세 가지면 충분하다.

1. 그 메서드 이름을 봤을 때 바로 특정 인터페이스가 떠오르면 interface `static` method 쪽이 자연스럽다.
2. 같은 규칙을 다른 인터페이스나 클래스에서도 반복해서 쓸 것 같으면 utility class 쪽이 안전하다.
3. 메서드가 늘어나며 "계약 설명"보다 "문자열 정리, 포맷 변환, 범용 검사"가 중심이 되면 utility class로 빼는 편이 읽기 쉽다.

예를 들어 아래 둘은 결이 다르다.

```java
public interface AlarmSender {
    void send(String message);

    static boolean isValidMessage(String message) {
        return message != null && !message.isBlank();
    }
}
```

이 경우 `isValidMessage(...)`는 `AlarmSender` 문맥을 읽는 사람이 같이 봐도 어색하지 않다.

반면 아래는 공용 규칙으로 커질 가능성이 더 크다.

```java
public final class MessageTextUtils {
    private MessageTextUtils() {
    }

    public static String normalize(String raw) {
        return raw.trim().replace("\r\n", "\n");
    }
}
```

이 `normalize(...)`는 `AlarmSender`만의 규칙이라기보다 다른 메시지 처리 코드도 같이 쓸 수 있는 일반 도구에 가깝다.

처음 배우는 단계에서는 이렇게 외우면 충분하다.

- **계약 옆에 붙는 작은 정적 규칙이면 interface `static`**
- **인터페이스 밖에서도 재사용할 공용 정리 도구면 utility class**

## 초보자 혼동 포인트

### 몸체가 있으니 둘 다 같은 역할이라고 보면 안 된다

초보자는 "둘 다 구현이 있네"로 묶기 쉽다. 하지만 실제 구분은 몸체 유무가 아니라 **누가 호출하고, 어디에 내려가느냐**다.

### interface `static` method는 override되지 않는다

구현체에 같은 이름의 `static` 메서드를 만들어도 그것은 별개다. `default method`처럼 다형적으로 교체되는 자리가 아니다.

### `default method`는 구현체 상태를 간접적으로 쓸 수 있지만, interface `static` method는 아니다

`default method`는 다른 추상 메서드를 호출해 구현체 동작을 이어 붙일 수 있다. 반면 interface `static` method는 인스턴스가 없으니 그런 흐름에 직접 올라타지 않는다.

### helper가 있다고 무조건 interface `static` method에 둘 필요는 없다

범용 유틸리티라면 별도 유틸 클래스가 더 자연스러울 수 있다. "이 규칙이 정말 이 인터페이스와 강하게 묶여 있는가?"를 먼저 보면 된다.

### interface `private` method는 구현체를 위한 새 기능이 아니다

`private` 메서드는 `default`처럼 구현체에게 내려가지도 않고, `static`처럼 바깥 API도 아니다. `default`/`static` 안에서 중복 코드를 줄이는 내부 정리 도구에 가깝다.

## 다음에 읽을 문서

- `default method`의 역할을 더 깊게 보려면 [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- `static` 메서드를 인스턴스 메서드, 팩터리 메서드와 더 넓게 비교하려면 [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md)
- 인터페이스와 추상 클래스의 큰 그림으로 돌아가려면 [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)

## 한 줄 정리

처음 배우는데 인터페이스의 `default method`와 `static` method가 같이 보여 헷갈린다면, `default method`는 "구현체가 물려받는 기본 동작", interface `static` method는 "인터페이스 이름으로만 부르는 도우미"라고 나누면 빠르게 정리된다.
