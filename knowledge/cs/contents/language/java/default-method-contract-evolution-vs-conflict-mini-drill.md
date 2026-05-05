---
schema_version: 3
title: Default Method 계약 진화 vs 충돌 해결 미니 드릴
concept_id: language/default-method-contract-evolution-vs-conflict-mini-drill
canonical: false
category: language
difficulty: beginner
doc_role: drill
level: beginner
language: ko
source_priority: 75
mission_ids: []
review_feedback_tags:
- default-method-evolution
- diamond-conflict-resolution
- interface-contract-evolution
aliases:
- default method contract evolution vs conflict
- interface default method mini drill
- default method 언제 추가하고 언제 override
- default method conflict resolution beginner
- default method diamond conflict quick check
- contract evolution vs conflict resolution java
- 같은 default method 두 개 언제 충돌
- 처음 배우는데 default method drill
- default method 왜 false 기본값
- interface default method evolution basics
- what is default method conflict drill
- default method override rule practice
symptoms:
- default method를 볼 때 계약 진화용 기본값인지 충돌 해결 문제인지 바로 구분이 안 돼
- 같은 이름의 메서드가 둘이면 무조건 충돌이라고 착각해
- 글로는 이해했는데 짧은 코드 예제로 보면 evolution과 conflict가 다시 섞여 보여
intents:
- drill
- comparison
prerequisites:
- language/interface-default-method-contract-evolution-primer
- language/interface-default-method-diamond-conflict-basics
- language/interface-default-vs-static-method-primer
next_docs:
- language/abstract-class-vs-interface
- software-engineering/repository-interface-contract
- language/java-abstract-class-vs-interface-basics
linked_paths:
- contents/language/java/interface-default-method-contract-evolution-primer.md
- contents/language/java/interface-default-method-diamond-conflict-basics.md
- contents/language/java/interface-default-vs-static-method-primer.md
- contents/language/java/abstract-class-vs-interface.md
- contents/language/java/java-abstract-class-vs-interface-basics.md
- contents/software-engineering/repository-interface-contract-primer.md
confusable_with:
- language/interface-default-method-contract-evolution-primer
- language/interface-default-method-diamond-conflict-basics
- language/interface-default-vs-static-method-primer
forbidden_neighbors: []
expected_queries:
- default method 문제를 볼 때 계약 진화와 diamond conflict를 빠르게 판별하는 연습 문제가 필요해
- 같은 시그니처 두 개가 만나는 경우와 그냥 기본값 추가인 경우를 짧게 구분해 보고 싶어
- interface default method에서 evolution인지 conflict resolution인지 손으로 확인하는 미니 드릴이 있어?
- 이름은 같은데 파라미터가 다를 때 충돌이 아닌 이유를 예제로 연습하고 싶어
- default method override 규칙을 초보자용 quick check 형태로 정리한 문서를 찾고 있어
contextual_chunk_prefix: |
  이 문서는 Java 학습자가 default method를 볼 때 계약을 넓히는 기본값과
  같은 시그니처 충돌 해결을 확인 질문으로 굳히는 drill이다. 예전 구현체를
  덜 깨뜨리며 메서드를 늘리는 경우, 인터페이스 둘이 만났을 때 직접
  선택해야 하는 경우, 이름은 같아도 overload라서 공존하는 경우, override가
  왜 마지막 결정인지 같은 자연어 표현이 본 문서의 quick check 판단에
  매핑된다.
---
# Default Method 계약 진화 vs 충돌 해결 미니 드릴

> 한 줄 요약: `default method`를 볼 때 먼저 "기존 구현체를 덜 깨뜨리며 계약을 넓히는가"와 "같은 시그니처 두 개가 만나서 누구 걸 쓸지 정해야 하는가"를 나누면 beginner 혼란이 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [인터페이스 `default method` 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- [Java `default method` diamond conflict 기초](./interface-default-method-diamond-conflict-basics.md)
- [인터페이스 `default method` vs `static` method 프라이머](./interface-default-vs-static-method-primer.md)
- [Repository Interface Contract Primer](../../software-engineering/repository-interface-contract-primer.md)

retrieval-anchor-keywords: default method contract evolution vs conflict, interface default method mini drill, default method 언제 추가하고 언제 override, default method conflict resolution beginner, default method diamond conflict quick check, contract evolution vs conflict resolution java, 같은 default method 두 개 언제 충돌, 처음 배우는데 default method drill, default method 왜 false 기본값, interface default method evolution basics, what is default method conflict drill, default method override rule practice

## 핵심 개념

이 드릴의 핵심 질문은 두 개뿐이다.

- 이 `default method`가 **기존 구현체를 살리면서 인터페이스를 조금 넓히는 기본값**인가?
- 아니면 **서로 다른 인터페이스의 같은 시그니처가 만나서 구현 클래스가 직접 선택해야 하는 상황**인가?

첫 번째면 계약 진화(evolution) 쪽이고, 두 번째면 충돌 해결(conflict resolution) 쪽이다. beginner가 자주 섞는 이유는 둘 다 `default method` 문법을 쓰기 때문이다. 하지만 질문 자체가 다르다.

- evolution: "새 메서드를 추가해도 예전 구현체가 바로 깨지지 않게 할 수 있나?"
- conflict: "같은 메서드가 둘이라서 누구 걸 쓸지 지금 정해야 하나?"

## 15초 구분 카드

| 먼저 보는 힌트 | 어디에 가깝나 | 왜 그렇게 읽나 |
|---|---|---|
| 기존 구현체가 이미 많고, 새 능력을 안전한 기본값으로 붙인다 | 계약 진화 | `default`가 완충 장치 역할을 한다 |
| `supportsX()`, `isX()`, `sendAll()`처럼 기본값이나 편의 메서드가 있다 | 계약 진화 | 핵심 계약 위에 얇게 얹는 경우가 많다 |
| 구현 클래스가 인터페이스 두 개를 `implements`한다 | 충돌 후보 | 같은 시그니처가 겹칠 수 있다 |
| 두 인터페이스 모두 `default void start()`를 가진다 | 충돌 해결 | 자동 선택이 아니라 직접 override가 필요하다 |
| 이름은 같지만 파라미터가 다르다 | 충돌 아님 | overload라서 둘 다 함께 존재할 수 있다 |

짧게 외우면 이렇다.

- **새 메서드를 덧붙여 예전 구현체를 살리는 질문이면 evolution**
- **같은 시그니처 두 개 중 누구 걸 쓸지 고르는 질문이면 conflict**

## quick check 1-2

### 1. 이건 계약 진화일까

```java
interface PaymentClient {
    void pay(int amount);

    default boolean supportsCancel() {
        return false;
    }
}
```

정답: **계약 진화**

왜:
- 기존 구현체는 `pay(...)`만 구현해도 계속 동작한다
- 새 메서드 `supportsCancel()`에 안전한 기본값 `false`가 있다
- 질문의 중심이 "누구 기본 구현을 고를까?"가 아니라 "예전 구현체를 덜 깨뜨리며 표면을 넓힐 수 있나?"다

### 2. 이건 왜 충돌이 아닌가

```java
interface Printer {
    default void print() {
        System.out.println("print");
    }
}

interface Scanner {
    default void print(String mode) {
        System.out.println(mode);
    }
}

class OfficeMachine implements Printer, Scanner {
}
```

정답: **충돌 아님**

왜:
- 이름은 같아도 `print()`와 `print(String)`은 시그니처가 다르다
- 이 경우는 conflict resolution이 아니라 overload로 읽는다
- beginner 기준으로는 "이름보다 괄호 안 모양이 먼저"라고 기억하면 된다

## quick check 3-4

### 3. 이건 왜 충돌 해결 규칙이 필요한가

```java
interface Camera {
    default void start() {
        System.out.println("camera");
    }
}

interface Recorder {
    default void start() {
        System.out.println("recorder");
    }
}

class SmartDevice implements Camera, Recorder {
}
```

정답: **충돌 해결**

왜:
- `start()` 시그니처가 완전히 같다
- `SmartDevice`는 어떤 기본 구현을 쓸지 자동으로 정해지지 않는다
- 그래서 구현 클래스가 직접 override해서 의도를 적어야 한다

### 4. 어떻게 풀어야 하나

```java
class SmartDevice implements Camera, Recorder {
    @Override
    public void start() {
        Camera.super.start();
    }
}
```

정답 포인트:
- `override`가 최종 결정이다
- `Camera.super.start()`는 선택한 인터페이스 기본 구현 호출이다
- 이것은 "계약 진화용 기본값 추가"가 아니라 "겹친 기본 구현 중 하나를 고르는 행동"이다

## 흔한 오해와 함정

- `default method`가 보이면 전부 conflict라고 오해하기 쉽다. 하지만 대부분은 먼저 "기존 계약을 덜 깨뜨리며 넓히는 기본값인가?"를 봐야 한다.
- 반대로 `default method`면 무조건 evolution 도구라고만 보면 안 된다. 다중 인터페이스에서 같은 시그니처가 만나면 충돌 해결 규칙으로 넘어간다.
- 이름만 같으면 충돌이라고 착각하기 쉽다. 충돌 판단의 첫 기준은 시그니처다.
- `default method`의 기본값이 있다고 해서 항상 좋은 설계는 아니다. 의미 없는 기본값이면 컴파일은 살아도 계약 설명이 흐려진다.

## 더 깊이 가려면

- evolution 쪽 기준을 먼저 다시 잡고 싶다면 [인터페이스 `default method` 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- diamond conflict 규칙을 예제와 함께 더 보고 싶다면 [Java `default method` diamond conflict 기초](./interface-default-method-diamond-conflict-basics.md)
- `default`와 `static`의 역할 분리를 같이 정리하고 싶다면 [인터페이스 `default method` vs `static` method 프라이머](./interface-default-vs-static-method-primer.md)
- 인터페이스를 정말 계약 중심으로 읽는 감각을 보강하려면 [Repository Interface Contract Primer](../../software-engineering/repository-interface-contract-primer.md)

## 한 줄 정리

`default method`를 봤을 때 "기존 구현체를 살리며 인터페이스를 넓히는가"를 묻는 순간은 evolution이고, "같은 시그니처 두 개 중 누구 걸 쓸지 정하는가"를 묻는 순간은 conflict resolution이다.
