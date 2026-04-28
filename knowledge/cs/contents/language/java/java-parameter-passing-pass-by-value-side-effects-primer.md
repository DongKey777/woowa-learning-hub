# Java parameter 전달, pass-by-value, side effect 입문

> 한 줄 요약: Java 입문자가 "기본형은 안 바뀌는데 참조형은 왜 바뀌는 것처럼 보이지?"를 pass-by-value, 객체 mutation, parameter 재할당을 한 흐름으로 이해하도록 돕는 primer다.

**난이도: 🟢 Beginner**


관련 문서:

- [Language README](../README.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

retrieval-anchor-keywords: java pass by value, java parameter passing basics, java reference copy, java mutation vs reassignment, java side effect basics, java aliasing basics, 자바 값 전달, 자바는 항상 pass by value, 기본형은 안 바뀌는데 객체는 왜 바뀌나요, 메서드에서 객체 바꾸면 원본도 바뀌는지, 자바 파라미터 전달 큰 그림, mutation reassignment 차이

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 결론: Java는 항상 pass-by-value다](#먼저-결론-java는-항상-pass-by-value다)
- [기본형과 참조형에서 무엇이 복사되는가](#기본형과-참조형에서-무엇이-복사되는가)
- [mutation과 reassignment는 다르다](#mutation과-reassignment는-다르다)
- [손으로 추적하는 작은 연습](#손으로-추적하는-작은-연습)
- [side effect를 읽는 체크리스트](#side-effect를-읽는-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 parameter를 배운 뒤 가장 자주 헷갈리는 질문은 보통 이 셋이다.

- `int`를 넘기면 안 바뀌는데 왜 `Student`를 넘기면 바뀌는 것처럼 보일까?
- 참조형이면 "주소"를 넘기는 것이니 pass-by-reference 아닌가?
- 메서드 안에서 parameter에 새 객체를 넣었는데 왜 호출자 변수는 그대로일까?

핵심은 "Java는 항상 pass-by-value"라는 한 문장을 정확히 이해하는 데 있다.
다만 참조형에서는 **복사되는 값이 객체 자체가 아니라 참조값**이기 때문에, 객체 mutation이 같이 보이면 초보자 눈에는 pass-by-reference처럼 보인다.

이 문서는 그 착시를 작은 예제와 상태 추적으로 끊어 내는 데 목적이 있다.

## 먼저 잡는 멘탈 모델

메서드 호출을 "값이 적힌 메모 한 장을 복사해 건네는 일"로 보면 쉽다.

- 기본형이면 메모에 숫자 같은 값이 적혀 있다.
- 참조형이면 메모에 "어느 객체를 보고 있는지"라는 참조값이 적혀 있다.
- 메서드는 그 메모의 복사본을 받는다. 호출자 변수 자체를 빌려 가지는 것이 아니다.

그래서 참조형에서 보이는 변화는 "변수를 공유해서"가 아니라 "같은 객체를 함께 보고 있어서" 생긴다.

## 먼저 결론: Java는 항상 pass-by-value다

Java 메서드 호출에서 복사되는 것은 항상 **argument의 값**이다.

- 기본형 argument면 값 자체가 복사된다.
- 참조형 argument면 "어떤 객체를 가리키는 참조값"이 복사된다.

그래서 참조형에서도 메서드가 호출자 변수를 직접 붙잡는 것은 아니다.
메서드는 **호출자가 들고 있던 참조값의 복사본**을 자기 parameter에 받는다.

짧게 표로 보면 다음과 같다.

| 전달 대상 | 복사되는 것 | 메서드 안에서 가능한 일 | 호출자가 보게 되는 것 |
|---|---|---|---|
| `int score` | 숫자 값 | local copy 변경 | 원래 변수는 안 바뀜 |
| `Counter counter` | `Counter`를 가리키는 참조값 | 같은 객체를 mutation하거나 local parameter를 다른 객체로 재할당 | mutation은 보이고, 재할당은 안 보임 |
| `int[] numbers` | 배열 객체를 가리키는 참조값 | 배열 원소 mutation, local parameter 재할당 | 원소 mutation은 보이고, 재할당은 안 보임 |

## 기본형과 참조형에서 무엇이 복사되는가

### 기본형: 값 사본만 바뀐다

```java
static void increase(int value) {
    value++;
}

int score = 10;
increase(score);
System.out.println(score); // 10
```

`increase()` 안의 `value`는 `score`의 복사본이다.
따라서 `value++`는 메서드 안의 local 값만 바꾼다.

### 참조형: 참조값 사본이 같은 객체를 가리킨다

```java
final class Counter {
    private int value;

    Counter(int value) {
        this.value = value;
    }

    void add(int amount) {
        value += amount;
    }

    int getValue() {
        return value;
    }
}

static void addBonus(Counter counter) {
    counter.add(10);
}

Counter counter = new Counter(5);
addBonus(counter);
System.out.println(counter.getValue()); // 15
```

여기서 바깥의 `counter` 변수와 메서드 안의 `counter` parameter는 같은 변수가 아니다.
단지 둘 다 **같은 `Counter` 객체를 가리키는 참조값**을 가지게 된 것이다.

그래서 parameter를 통해 객체를 mutation하면, 호출자도 그 같은 객체의 바뀐 상태를 보게 된다.

## mutation과 reassignment는 다르다

초보자가 가장 자주 섞는 것은 아래 두 문장이다.

- `counter.add(10);`
- `counter = new Counter(999);`

둘은 완전히 다른 동작이다.

### 1. mutation: 같은 객체의 상태를 바꾼다

```java
static void addBonus(Counter counter) {
    counter.add(10);
}
```

이 코드는 parameter가 가리키는 **기존 객체의 내부 상태**를 바꾼다.
호출자와 parameter가 같은 객체를 보고 있다면, 바깥에서도 변화가 보인다.

### 2. reassignment: local parameter가 다른 객체를 가리키게 만든다

```java
static void replace(Counter counter) {
    counter = new Counter(999);
}

Counter original = new Counter(5);
replace(original);
System.out.println(original.getValue()); // 5
```

`replace()`는 parameter 변수에 새 객체를 넣었을 뿐이다.
호출자 쪽 변수 `original`이 가진 참조값은 바뀌지 않았으므로, 바깥에서는 여전히 원래 객체를 본다.

같은 내용을 배열로 보면 더 선명하다.

```java
static void touchFirst(int[] numbers) {
    numbers[0] = 99;
}

static void replaceArray(int[] numbers) {
    numbers = new int[] {7, 8, 9};
}

int[] values = {1, 2, 3};
touchFirst(values);
replaceArray(values);

System.out.println(values[0]); // 99
System.out.println(values.length); // 3
```

- `numbers[0] = 99`는 같은 배열 객체를 mutation한다.
- `numbers = new int[] {7, 8, 9}`는 local parameter만 다른 배열을 보게 만든다.

처음 배우는 단계에서는 아래 두 질문으로 잘라 보면 덜 헷갈린다.

| 지금 일어난 일 | 실제로 바뀌는 것 | 호출자에게 보이는가 |
|---|---|---|
| `counter.add(10)` | 같은 객체의 내부 상태 | 보인다 |
| `counter = new Counter(999)` | 메서드 안 parameter가 가리키는 대상 | 안 보인다 |
| `numbers[0] = 99` | 같은 배열의 원소 | 보인다 |
| `numbers = new int[] {7, 8, 9}` | 메서드 안 parameter 변수 | 안 보인다 |

## 손으로 추적하는 작은 연습

### 연습 1. 기본형은 왜 그대로인가

```java
static void grow(int size) {
    size += 3;
}

int size = 2;
grow(size);
```

질문:

- 마지막 줄 뒤에 `size`는 얼마인가?

정답:

- `size = 2`

이유:

- `grow()`는 `2`의 복사본을 받아 `5`로 바꿨지만, 호출자 변수는 그대로다.

### 연습 2. mutation이 보이는 이유는 무엇인가

```java
static void markDone(Todo todo) {
    todo.complete();
}

final class Todo {
    private boolean done;

    void complete() {
        done = true;
    }

    boolean isDone() {
        return done;
    }
}

Todo first = new Todo();
Todo alias = first;
markDone(first);
```

질문:

- `first.isDone()`은 무엇인가?
- `alias.isDone()`은 무엇인가?

정답:

- 둘 다 `true`

이유:

- `first`와 `alias`는 같은 객체를 보고 있다.
- `markDone()`은 parameter를 재할당한 것이 아니라 같은 객체 상태를 mutation했다.

### 연습 3. 새 객체를 넣었는데 왜 안 바뀌는가

```java
static void reset(Counter counter) {
    counter = new Counter(0);
}

Counter saved = new Counter(7);
reset(saved);
```

질문:

- 마지막 줄 뒤에 `saved.getValue()`는 얼마인가?

정답:

- `7`

이유:

- `reset()` 안에서 바뀐 것은 local parameter `counter`뿐이다.
- 호출자 변수 `saved`가 들고 있던 참조값은 바뀌지 않았다.

### 연습 4. mutation과 reassignment를 한 번에 구분해 보기

```java
static void update(Counter counter) {
    counter.add(2);
    counter = new Counter(100);
    counter.add(5);
}

Counter base = new Counter(1);
update(base);
```

질문:

- 마지막 줄 뒤에 `base.getValue()`는 얼마인가?

정답:

- `3`

이유:

## 손으로 추적하는 작은 연습 (계속 2)

1. 처음 `counter.add(2)`는 원래 객체를 mutation하므로 `base`가 보는 값도 `3`이 된다.
2. 그다음 `counter = new Counter(100)`은 local parameter만 새 객체를 보게 만든다.
3. 마지막 `counter.add(5)`는 새로 만든 local 객체를 `105`로 바꾸지만, 호출자 `base`와는 무관하다.

## side effect를 읽는 체크리스트

메서드가 side effect를 만드는지 빠르게 보려면 아래를 보면 된다.

- parameter나 field를 통해 **기존 mutable 객체의 상태**를 바꾸는가
- 배열 원소, 컬렉션 원소, 객체 필드를 수정하는가
- `static` 필드, 외부 I/O, DB, 로그처럼 메서드 바깥에서 관측 가능한 것을 바꾸는가

반대로 아래는 side effect가 아니다.

- primitive parameter local copy 재계산
- parameter 변수 자체를 다른 객체로 재할당
- 새 객체를 만들어 local 변수에만 저장

입문 단계에서는 특히 다음 질문이 가장 유용하다.

- "이 코드는 **같은 객체**를 바꾸는가?"
- "아니면 **parameter 이름만** 다른 객체로 돌리는가?"

이 두 질문으로 대부분의 pass-by-value 혼란을 바로 정리할 수 있다.

## 어떤 문서를 다음에 읽으면 좋은가

- parameter, return type, state change를 메서드 시그니처 관점에서 다시 정리하고 싶다면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- 참조형, 객체, aliasing 감각을 더 넓은 OOP 맥락에서 보고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- 배열 전달과 복사에서 side effect가 어떻게 달라지는지 함께 보려면 [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- 상태를 바꾸지 않는 설계가 왜 side effect를 줄이는지 보고 싶다면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
- `==`, identity, 같은 객체를 본다는 의미가 비교 연산에서 어떻게 나타나는지 보고 싶다면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- 메서드를 인스턴스에 둘지 `static`으로 둘지, `this` 의존성과 side effect 관점으로 이어서 보고 싶다면 [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md)

## 한 줄 정리

Java는 항상 pass-by-value이고, 참조형에서 보이는 변화는 parameter 자체가 호출자 변수를 바꾸는 것이 아니라 복사된 참조값을 통해 같은 객체를 mutation했기 때문에 보이는 것이다.
