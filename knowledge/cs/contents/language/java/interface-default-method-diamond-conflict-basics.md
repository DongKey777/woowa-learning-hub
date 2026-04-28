# Java `default method` diamond conflict 기초

> 한 줄 요약: 처음 배우는데 다중 인터페이스에서 같은 `default method`가 부딪히면, Java는 "자동으로 아무거나 고르지 않고" 구현 클래스가 직접 정하라고 요구한다. 큰 그림은 `클래스 메서드 우선 -> 더 구체적인 인터페이스 우선 -> 그래도 동률이면 내가 override` 순서로 잡으면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md)
- [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- [Default Method 계약 진화 vs 충돌 해결 미니 드릴](./default-method-contract-evolution-vs-conflict-mini-drill.md)
- [인터페이스 `default method` vs `static` method 프라이머](./interface-default-vs-static-method-primer.md)
- [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)

retrieval-anchor-keywords: java default method diamond conflict, java two interfaces same default method, java duplicate default method compile error, interfacename.super 어디서 쓰나, interface super call not allowed here, 같은 default method 두 개, implements 두 개 했더니 컴파일 에러, default method 충돌 뭐예요, 처음 배우는데 default method 충돌, default method override vs overload, 같은 이름인데 충돌인가 오버로딩인가, 파라미터 다르면 충돌 아님, default method 시그니처 기준

<details>
<summary>Table of Contents</summary>

- [처음 배우는데 왜 헷갈리나](#처음-배우는데-왜-헷갈리나)
- [큰 그림 규칙 3개](#큰-그림-규칙-3개)
- [가장 흔한 충돌 예제](#가장-흔한-충돌-예제)
- [충돌인지 오버로딩인지 먼저 자르기](#충돌인지-오버로딩인지-먼저-자르기)
- [Default Method Override vs Overload 미니 드릴](#default-method-override-vs-overload-미니-드릴)
- [충돌을 직접 푸는 방법](#충돌을-직접-푸는-방법)
- [어디서 쓸 수 있고 어디서는 못 쓰나](#어디서-쓸-수-있고-어디서는-못-쓰나)
- [자동으로 풀리는 두 경우](#자동으로-풀리는-두-경우)
- [자주 하는 오해](#자주-하는-오해)
- [다음에 읽을 문서](#다음에-읽을-문서)
- [한-줄-정리](#한-줄-정리)

</details>

## 처음 배우는데 왜 헷갈리나

처음 배우는데 `default method`를 보면 보통 여기서 막힌다.

- 인터페이스도 메서드 몸체를 가질 수 있다
- 구현 클래스는 인터페이스를 여러 개 `implements`할 수 있다
- 그럼 같은 이름의 `default method`가 둘 다 있으면 누구 걸 쓰는가

여기서 Java는 "둘 다 default니까 적당히 하나 고르자"라고 하지 않는다.

- 애매하면 컴파일 단계에서 멈춘다
- 구현 클래스가 의도를 직접 적게 만든다

즉 beginner 관점의 큰 그림은 단순하다.

- Java는 **조용히 추측하지 않는다**
- 충돌이 분명하면 **네가 골라서 override하라**고 한다

처음 검색할 때 아래 같은 증상 문장으로 들어와도 같은 문제다.

- `implements` 두 개 했더니 같은 `default method` 때문에 컴파일이 안 된다
- 인터페이스 둘 다 `start()` 기본 구현이 있는데 누구 것이 선택되는지 모르겠다
- `interfaceName.super`를 왜 쓰는지 감이 안 잡힌다

먼저 한 번 더 자르고 싶다면 이렇게 묻는다.

- 지금 질문이 "기존 구현체를 살리며 메서드를 추가할 수 있나?"면 conflict보다 evolution 쪽이다
- 지금 질문이 "같은 시그니처 두 개 중 누구 걸 골라야 하나?"면 이 문서의 conflict 규칙으로 들어오면 된다

## 큰 그림 규칙 3개

처음에는 아래 표만 기억해도 대부분의 검색 혼선이 줄어든다.

| 상황 | 누가 이기나 | beginner용 기억법 |
|---|---|---|
| 클래스/상위 클래스에 같은 메서드가 이미 있음 | 클래스 메서드 | "class가 interface보다 우선" |
| 인터페이스끼리 상속 관계가 있고 더 구체적인 쪽이 있음 | 더 구체적인 인터페이스 | "child interface가 parent보다 우선" |
| 서로 다른 인터페이스가 같은 `default method`를 각각 제공 | 자동 선택 없음, 구현 클래스가 override | "동률이면 내가 결정" |

이 순서만 머리에 넣으면 된다.

1. 클래스 메서드가 있나
2. 더 구체적인 인터페이스가 있나
3. 둘 다 아니면 직접 override하나

## 가장 흔한 충돌 예제

아래가 beginner가 검색으로 가장 자주 만나는 "diamond conflict" 모양이다.

```java
interface Camera {
    default void start() {
        System.out.println("camera start");
    }
}

interface Recorder {
    default void start() {
        System.out.println("recorder start");
    }
}

class SmartDevice implements Camera, Recorder {
}
```

이 코드는 컴파일되지 않는다. 이유는 `SmartDevice` 입장에서 `start()`가 두 개라서 무엇을 상속해야 할지 애매하기 때문이다.

여기서 중요한 포인트는:

- 둘 다 `default method`여도 자동 병합되지 않는다
- 이름과 파라미터가 같은 시그니처 충돌이면 구현 클래스가 정해야 한다
- 이것이 beginner가 말하는 `diamond problem`의 핵심 감각이다

## 충돌인지 오버로딩인지 먼저 자르기

처음 배우는데 가장 많이 헷갈리는 지점은 "`start`라는 이름이 같으니 무조건 충돌인가?"이다.

큰 그림은 이것 하나면 된다.

- **이름이 아니라 시그니처를 본다**
- parameter 목록까지 같으면 충돌 후보다
- parameter 목록이 다르면 충돌이 아니라 overload다

| 모양 | 어떻게 읽나 | 결과 |
|---|---|---|
| `start()` vs `start()` | 같은 시그니처 | 충돌 가능, 구현 클래스가 override해야 할 수 있음 |
| `start()` vs `start(String mode)` | 다른 시그니처 | 충돌 아님, overload |
| `start(String)` vs `start(String)` | 같은 시그니처 | 충돌 가능 |

## Default Method Override vs Overload 미니 드릴

### 미니 드릴 1. 충돌일까 overload일까

```java
interface Printer {
    default void print() {
        System.out.println("printer");
    }
}

interface Scanner {
    default void print(String mode) {
        System.out.println("scanner " + mode);
    }
}

class OfficeMachine implements Printer, Scanner {
}
```

정답: 충돌이 아니라 overload다.

- `print()`와 `print(String)`은 이름은 같아도 parameter 목록이 다르다
- 그래서 `OfficeMachine`은 두 메서드를 함께 가진다
- 초급자 기준 기억법은 "`같은 이름`보다 `괄호 안 모양`이 먼저"다

### 미니 드릴 2. 왜 이번에는 충돌인가

```java
interface Alarm {
    default void ring(String level) {
        System.out.println("alarm " + level);
    }
}

interface Bell {
    default void ring(String level) {
        System.out.println("bell " + level);
    }
}

class SmartBell implements Alarm, Bell {
}
```

정답: 이번에는 충돌이다.

- 둘 다 `ring(String)`으로 시그니처가 완전히 같다
- return type이나 메서드 몸체가 아니라 **parameter 목록이 같은지**가 첫 기준이다
- 그래서 `SmartBell`은 직접 override해야 한다

### 미니 드릴 3. override와 overload가 같이 들어갈 수도 있다

```java
interface Alarm {
    default void ring() {
        System.out.println("alarm");
    }
}

class SmartAlarm implements Alarm {
    @Override
    public void ring() {
        System.out.println("smart alarm");
    }

    public void ring(int times) {
        for (int i = 0; i < times; i++) {
            ring();
        }
    }
}
```

여기서는 둘이 동시에 있다.

- `ring()`은 부모 인터페이스의 같은 시그니처를 다시 쓰므로 override
- `ring(int)`는 parameter 목록을 늘린 새 메서드이므로 overload

즉 beginner용 한 줄 판단은 이것이다.

- **부모와 시그니처가 같으면 override**
- **이름은 같지만 parameter 목록이 다르면 overload**

## 충돌을 직접 푸는 방법

가장 기본 해법은 구현 클래스에서 직접 override하는 것이다.

```java
class SmartDevice implements Camera, Recorder {
    @Override
    public void start() {
        Camera.super.start();
    }
}
```

이제 `SmartDevice`는 "나는 `Camera` 쪽 기본 동작을 선택하겠다"라고 명시한다.

둘을 섞어서 새 동작을 만들 수도 있다.

```java
class SmartDevice implements Camera, Recorder {
    @Override
    public void start() {
        Camera.super.start();
        Recorder.super.start();
        System.out.println("smart device ready");
    }
}
```

여기서 `InterfaceName.super.method()` 문법은 "그 인터페이스가 가진 default 구현을 직접 가져다 쓰기"라고 이해하면 된다.

처음 배우는데는 이렇게 기억하면 충분하다.

- override는 **충돌을 없애는 최종 결정**
- `Camera.super.start()`는 **선택한 인터페이스 기본 구현 호출**

## 어디서 쓸 수 있고 어디서는 못 쓰나

초급자가 가장 빨리 헷갈리는 지점은 문법 자체보다 **호출 위치 제한**이다. 큰 그림은 한 줄이다.

- `InterfaceName.super.method()`는 **그 인터페이스를 직접 구현한 클래스의 인스턴스 메서드 본문 안**에서만 쓴다

아래 표로 먼저 자르면 검색 혼선이 줄어든다.

| 위치 | 가능 여부 | 왜 그런가 |
|---|---|---|
| 구현 클래스의 `override` 메서드 안 | 가능 | "어느 인터페이스 기본 구현을 고를지" 지금 이 클래스가 결정하는 자리라서 |
| 구현 클래스의 다른 인스턴스 메서드 안 | 가능 | 같은 클래스가 그 인터페이스를 직접 `implements`하고 있기 때문 |
| `static` 메서드 안 | 불가 | 인스턴스 문맥이 아니라서 |
| 인터페이스를 구현하지 않은 하위 헬퍼 클래스 안 | 불가 | 그 클래스는 그 default 구현의 직접 상속 주체가 아니라서 |
| 그냥 `main` 같은 바깥 호출 코드 | 불가 | call-site에서 임의로 특정 인터페이스 기본 구현을 집어 고르는 문법이 아니어서 |

### 되는 예제

```java
interface Camera {
    default void start() {
        System.out.println("camera start");
    }
}

class SmartDevice implements Camera {
    public void boot() {
        Camera.super.start(); // 컴파일 OK
    }
}
```

핵심은 `boot()`가 `SmartDevice`의 인스턴스 메서드이고, `SmartDevice`가 `Camera`를 직접 구현한다는 점이다.

### 안 되는 예제 1. 바깥 call-site에서 바로 고르기

```java
class App {
    public static void main(String[] args) {
        SmartDevice device = new SmartDevice();
        Camera.super.start(); // 컴파일 에러
    }
}
```

여기서는 `App`이 `Camera`를 구현하지도 않고, 지금 위치가 `SmartDevice`의 인스턴스 본문도 아니다. 즉 "어느 default를 고를지" 결정할 자리가 아니다.

### 안 되는 예제 2. `static` 문맥에서 호출하기

```java
class SmartDevice implements Camera {
    public static void bootAll() {
        Camera.super.start(); // 컴파일 에러
    }
}
```

`Camera.super.start()`는 `this`와 연결된 인스턴스 쪽 선택 문법이라 `static` 메서드에서는 못 쓴다.

처음 배우는데는 아래처럼 외우면 충분하다.

- **구현 클래스 안**이라고 다 되는 것은 아니다
- **인스턴스 문맥 + 직접 implements한 인터페이스**여야 된다
- 이 문법은 "호출하는 쪽이 고르는 call-site 문법"이 아니라 **구현 클래스가 상속 충돌을 정리하는 문법**이다

## 자동으로 풀리는 두 경우

### 1. 클래스 메서드가 이미 있으면 클래스가 이긴다

```java
class BaseDevice {
    public void start() {
        System.out.println("base device start");
    }
}

interface Camera {
    default void start() {
        System.out.println("camera start");
    }
}

class SmartDevice extends BaseDevice implements Camera {
}
```

이 경우 `SmartDevice`는 `BaseDevice`의 `start()`를 쓴다.

즉 `default method`는 클래스 계층 메서드를 덮어쓰는 우선권이 아니다. beginner용 한 문장으로 줄이면:

- **클래스 메서드가 보이면 인터페이스 default보다 먼저 본다**

### 2. 더 구체적인 인터페이스가 있으면 그쪽이 이긴다

```java
interface Animal {
    default void move() {
        System.out.println("animal move");
    }
}

interface Bird extends Animal {
    @Override
    default void move() {
        System.out.println("bird move");
    }
}

class Sparrow implements Bird {
}
```

`Sparrow`는 `Bird`의 `move()`를 쓴다. `Bird`가 `Animal`보다 더 구체적인 인터페이스이기 때문이다.

이 경우는 sibling 두 개가 싸우는 것이 아니라 parent-child 관계가 있으므로 Java가 방향을 알고 있다.

## 자주 하는 오해

### 둘 다 `default`면 Java가 하나를 랜덤으로 고르지는 않는다

아니다. 애매하면 컴파일 오류로 막는다. 런타임에서 몰래 고르는 문제가 아니다.

### 이름만 같다고 항상 충돌하는 것은 아니다

파라미터 목록까지 같은 시그니처일 때 문제다. 이름이 같아도 오버로딩 모양이면 다른 메서드일 수 있다.

즉 `default method`에서도 질문 순서는 같다.

1. 같은 이름인가
2. 같은 parameter 목록인가
3. 같다면 충돌 후보, 다르면 overload

### `default method` 충돌을 피하려고 무조건 추상 클래스로 가는 것은 아니다

이 문제는 "다중 인터페이스에서 기본 구현 선택" 문제다. 공통 상태와 긴 공통 로직이 필요할 때만 추상 클래스를 다시 검토하면 된다.

### `InterfaceName.super.method()`는 아무 데서나 쓰는 문법이 아니다

충돌을 푸는 구현 클래스의 override 안에서, 특정 인터페이스의 `default method`를 고를 때 쓴다.

## 다음에 읽을 문서

- `default method` 자체가 왜 생겼는지 큰 그림부터 보고 싶다면 [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- 워크시트처럼 "이건 충돌인가, 그냥 계약 진화인가"를 먼저 자르고 싶다면 [Default Method 계약 진화 vs 충돌 해결 미니 드릴](./default-method-contract-evolution-vs-conflict-mini-drill.md)
- 같은 이름 메서드를 시그니처 기준으로 자르는 감각을 더 기초부터 보고 싶다면 [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md)
- 인터페이스 안의 `default`와 `static`을 먼저 구분하고 싶다면 [인터페이스 `default method` vs `static` method 프라이머](./interface-default-vs-static-method-primer.md)
- 인터페이스와 추상 클래스를 언제 나누는지 더 넓게 보고 싶다면 [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)

## 한 줄 정리

다중 인터페이스에서 같은 `default method`가 부딪히면 Java는 자동으로 하나를 고르지 않는다. 처음 배우는데는 `클래스 메서드 우선 -> 더 구체적인 인터페이스 우선 -> 그래도 동률이면 구현 클래스가 override` 순서로 기억하면 가장 덜 헷갈린다.
