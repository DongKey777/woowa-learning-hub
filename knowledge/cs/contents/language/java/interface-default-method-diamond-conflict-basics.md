# Java `default method` diamond conflict 기초

> 한 줄 요약: 처음 배우는데 다중 인터페이스에서 같은 `default method`가 부딪히면, Java는 "자동으로 아무거나 고르지 않고" 구현 클래스가 직접 정하라고 요구한다. 큰 그림은 `클래스 메서드 우선 -> 더 구체적인 인터페이스 우선 -> 그래도 동률이면 내가 override` 순서로 잡으면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- [인터페이스 `default method` vs `static` method 프라이머](./interface-default-vs-static-method-primer.md)
- [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)

retrieval-anchor-keywords: java default method diamond conflict, java two interfaces same default method, java default method override conflict, java class inherits unrelated defaults, java duplicate default method compile error, class wins over interface default, more specific interface wins, interfacename.super syntax, 같은 default method 두 개, 인터페이스 default method 충돌 해결, implements 두 개 했더니 컴파일 에러, 처음 배우는데 default method 충돌 큰 그림, default method 충돌 뭐예요, interface default method diamond conflict basics basics, interface default method diamond conflict basics beginner

<details>
<summary>Table of Contents</summary>

- [처음 배우는데 왜 헷갈리나](#처음-배우는데-왜-헷갈리나)
- [큰 그림 규칙 3개](#큰-그림-규칙-3개)
- [가장 흔한 충돌 예제](#가장-흔한-충돌-예제)
- [충돌을 직접 푸는 방법](#충돌을-직접-푸는-방법)
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

### `default method` 충돌을 피하려고 무조건 추상 클래스로 가는 것은 아니다

이 문제는 "다중 인터페이스에서 기본 구현 선택" 문제다. 공통 상태와 긴 공통 로직이 필요할 때만 추상 클래스를 다시 검토하면 된다.

### `InterfaceName.super.method()`는 아무 데서나 쓰는 문법이 아니다

충돌을 푸는 구현 클래스의 override 안에서, 특정 인터페이스의 `default method`를 고를 때 쓴다.

## 다음에 읽을 문서

- `default method` 자체가 왜 생겼는지 큰 그림부터 보고 싶다면 [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- 인터페이스 안의 `default`와 `static`을 먼저 구분하고 싶다면 [인터페이스 `default method` vs `static` method 프라이머](./interface-default-vs-static-method-primer.md)
- 인터페이스와 추상 클래스를 언제 나누는지 더 넓게 보고 싶다면 [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)

## 한 줄 정리

다중 인터페이스에서 같은 `default method`가 부딪히면 Java는 자동으로 하나를 고르지 않는다. 처음 배우는데는 `클래스 메서드 우선 -> 더 구체적인 인터페이스 우선 -> 그래도 동률이면 구현 클래스가 override` 순서로 기억하면 가장 덜 헷갈린다.
