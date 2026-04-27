# Java 메서드와 생성자 실전 입문

> 한 줄 요약: Java 입문자가 parameter, return type, overloading, constructor, object state change를 따로 외우지 않고 하나의 클래스 흐름으로 묶어 이해하도록 돕는 짧은 practice primer다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java methods constructors practice primer basics, java methods constructors practice primer beginner, java methods constructors practice primer intro, java basics, beginner java, 처음 배우는데 java methods constructors practice primer, java methods constructors practice primer 입문, java methods constructors practice primer 기초, what is java methods constructors practice primer, how to java methods constructors practice primer
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [Java parameter 전달, pass-by-value, side effect 입문](./java-parameter-passing-pass-by-value-side-effects-primer.md)
> - [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md)
> - [Java 생성자와 초기화 순서 입문](./java-constructors-initialization-order-basics.md)
> - [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
> - [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

> retrieval-anchor-keywords: java methods and constructors basics, java method constructor primer, java parameter return type basics, java method overloading basics, java constructor overloading basics, java object state change, java method practice, java constructor practice, java beginner method signature, java void vs return type, java class state update, java field state change, java instance vs static methods, java static utility method basics, java simple factory method basics, 자바 메서드 생성자 기초, 자바 메서드 생성자 차이 기초, 처음 배우는데 메서드 생성자 차이, 처음 배우는데 메서드 큰 그림, 메서드 언제 쓰는지 기초, 생성자 언제 쓰는지 기초, 자바 파라미터 리턴타입 기초, parameter return type 차이 기초, 자바 메서드 시그니처 기초, 자바 메서드 오버로딩 기초, 자바 생성자 오버로딩 기초, this super 초기화 흐름 기초, 객체 상태 변경 메서드 기초

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡아야 하는 다섯 질문](#먼저-잡아야-하는-다섯-질문)
- [한 클래스에서 한 번에 보기](#한-클래스에서-한-번에-보기)
- [손으로 추적하는 연습](#손으로-추적하는-연습)
- [초보자가 자주 틀리는 포인트](#초보자가-자주-틀리는-포인트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문 구간에서 메서드와 생성자는 보통 따로 배운다.
하지만 실제 코드에서는 다음 질문이 한 번에 묶여 나온다.

- 이 객체는 어떤 값으로 시작해야 하지?
- 이 동작은 무엇을 입력받지?
- 실행 결과를 밖으로 돌려줘야 하나?
- 이름은 같은데 인자가 다른 메서드를 여러 개 둬도 되나?
- 이 호출이 객체 상태를 바꾸는가, 아니면 읽기만 하는가?

이 문서는 위 다섯 질문을 한 클래스 안에서 같이 보게 만드는 짧은 primer다.

## 먼저 잡아야 하는 다섯 질문

| 개념 | 초보자 질문 | 핵심 규칙 |
|---|---|---|
| parameter | "메서드가 일을 하려면 무엇이 필요하지?" | parameter는 호출자가 넘겨 주는 입력이다 |
| return type | "실행 결과를 밖으로 돌려줘야 하나?" | 돌려줄 값이 없으면 `void`, 있으면 그 타입을 쓴다 |
| constructor | "객체는 어떤 상태로 태어나야 하지?" | constructor는 객체의 시작 상태를 정한다. return type을 쓰지 않는다 |
| overloading | "비슷한 일을 하는 메서드를 여러 형태로 만들 수 있나?" | 이름은 같아도 parameter 목록이 다르면 가능하다 |
| object state change | "이 호출 뒤에 필드 값이 바뀌는가?" | 필드를 수정하면 state change, 읽기만 하면 query에 가깝다 |

이 다섯 개를 따로 외우기보다 "`객체를 만들고`, `입력을 받아`, `필요하면 값을 돌려주고`, `상태를 바꾸거나 읽는다`"는 한 흐름으로 묶는 편이 훨씬 잘 남는다.

## 한 클래스에서 한 번에 보기

아래 예시는 constructor overloading, method overloading, state change, query method를 모두 담은 최소 예시다.

```java
public class BankAccount {
    private final String owner;
    private int balance;
    private int transactionCount;

    public BankAccount(String owner) {
        this(owner, 0);
    }

    public BankAccount(String owner, int initialBalance) {
        if (initialBalance < 0) {
            throw new IllegalArgumentException("initialBalance must be >= 0");
        }
        this.owner = owner;
        this.balance = initialBalance;
        this.transactionCount = 0;
    }

    public void deposit(int amount) {
        deposit(amount, 0);
    }

    public void deposit(int amount, int bonus) {
        int total = amount + bonus;
        if (total <= 0) {
            throw new IllegalArgumentException("deposit must be positive");
        }
        balance += total;
        transactionCount++;
    }

    public boolean withdraw(int amount) {
        if (amount <= 0 || amount > balance) {
            return false;
        }
        balance -= amount;
        transactionCount++;
        return true;
    }

    public int getBalance() {
        return balance;
    }

    public String summary() {
        return owner + " balance=" + balance + ", tx=" + transactionCount;
    }
}
```

### 이 코드에서 무엇을 보면 되는가

## 한 클래스에서 한 번에 보기 (계속 2)

| 멤버 | parameter | return type | state change 여부 | 포인트 |
|---|---|---|---|---|
| `BankAccount(String owner)` | `owner` | 없음 | 시작 상태를 정함 | constructor는 클래스 이름과 같고 return type이 없다 |
| `BankAccount(String owner, int initialBalance)` | `owner`, `initialBalance` | 없음 | 시작 상태를 정함 | constructor overloading 예시 |
| `deposit(int amount)` | `amount` | `void` | 있음 | 입금만 하고 호출자에게 별도 값을 돌려주지 않는다 |
| `deposit(int amount, int bonus)` | `amount`, `bonus` | `void` | 있음 | method overloading 예시 |
| `withdraw(int amount)` | `amount` | `boolean` | 성공 시 있음 | 출금 성공 여부를 알려 주기 위해 `boolean`을 반환한다 |
| `getBalance()` | 없음 | `int` | 없음 | 상태를 읽는 query method다 |
| `summary()` | 없음 | `String` | 없음 | 객체 상태를 문자열로 요약해 돌려준다 |

여기서 객체 상태는 `owner`, `balance`, `transactionCount` 같은 필드다.

- constructor는 객체가 처음 태어날 때 이 필드를 채운다.
- `deposit()`와 `withdraw()`는 필드를 바꾸므로 state change가 있다.
- `getBalance()`와 `summary()`는 읽기만 하므로 state change가 없다.

### overloading은 무엇이 다를 때 성립하나

overloading은 **이름이 같고 parameter 목록이 다를 때** 성립한다.

- `deposit(int amount)`
- `deposit(int amount, int bonus)`

반대로 return type만 바꿔서는 overloading이 되지 않는다.

```java
// 컴파일 에러
public int getBalance() { ... }
public String getBalance() { ... }
```

호출하는 쪽에서는 보통 method name과 argument 목록으로 대상을 고르기 때문이다.

## 손으로 추적하는 연습

### 연습 1. 실행 뒤 상태를 적어 보기

```java
BankAccount account = new BankAccount("Mina", 1000);
account.deposit(300);
account.deposit(200, 50);
boolean success = account.withdraw(1700);
```

직접 먼저 적어 보자.

- `balance`는 얼마인가?
- `transactionCount`는 얼마인가?
- `success`는 `true`인가 `false`인가?

정답은 다음과 같다.

- `balance = 1550`
- `transactionCount = 2`
- `success = false`

이유는 다음 순서다.

1. 시작 상태는 `balance = 1000`
2. `deposit(300)` 후 `balance = 1300`, `transactionCount = 1`
3. `deposit(200, 50)` 후 `balance = 1550`, `transactionCount = 2`
4. `withdraw(1700)`은 잔액 부족이라 실패하고 `false`를 반환한다

즉 "return value가 있다"와 "항상 state change가 있다"는 같은 뜻이 아니다.
`withdraw()`는 `boolean`을 반환하지만, 실패하면 상태를 바꾸지 않을 수 있다.

### 연습 2. 요구사항을 시그니처로 바꿔 보기

다음 요구사항을 보면 어떤 constructor/method 시그니처가 자연스러운지 먼저 적어 보자.

- 이름만 받아서 `Counter`를 만든다
- 이름과 시작값을 받아서 `Counter`를 만든다
- 값을 1 증가시킨다
- 값을 원하는 만큼 증가시킨다
- 현재 값을 읽는다

한 가지 자연스러운 답은 아래와 같다.

```java
public Counter(String name)
public Counter(String name, int initialValue)
public void increase()
public void increase(int amount)
public int getValue()
```

이 연습의 핵심은 문법 암기가 아니라, 요구사항을 보고 다음을 바로 결정하는 데 있다.

- 시작 상태가 필요하면 constructor가 들어간다
- 입력이 필요하면 parameter가 붙는다
- 결과를 돌려줘야 하면 return type이 생긴다
- 같은 의도를 다른 입력 형태로 받고 싶으면 overloading을 검토한다

## 초보자가 자주 틀리는 포인트

### constructor에도 return type을 써야 한다고 생각한다

constructor는 method처럼 보여도 선언 방식이 다르다.
클래스 이름과 같고 return type을 쓰지 않는다. `void`도 쓰지 않는다.

### return type만 다르면 overloading이라고 생각한다

아니다. Java는 parameter 목록으로 overloading을 구분한다.

### 상태를 바꾸는 메서드와 읽기 메서드를 구분하지 않는다

`deposit()` 같은 command 성격 메서드와 `getBalance()` 같은 query 성격 메서드를 구분해서 읽는 습관이 필요하다.
그래야 호출 뒤에 객체가 달라졌는지 예측할 수 있다.

### parameter와 field를 같은 것으로 느낀다

parameter는 호출 시 잠깐 들어오는 입력이고, field는 객체가 계속 들고 있는 상태다.
constructor나 method는 parameter를 받아 field를 바꿀 수 있다.

## 어떤 문서를 다음에 읽으면 좋은가

- 클래스, 객체, 인터페이스, 추상 클래스까지 입문 흐름을 더 넓게 보고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- parameter 복사, 참조형 mutation, 재할당 차이를 손으로 추적해 보고 싶다면 [Java parameter 전달, pass-by-value, side effect 입문](./java-parameter-passing-pass-by-value-side-effects-primer.md)
- method overloading과 method overriding이 어디서 갈리는지 한 예제로 분리해서 보고 싶다면 [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md)
- `this()`/`super()`, field initializer, `static`/instance 초기화 블록까지 생성자 흐름을 더 정확히 보고 싶다면 [Java 생성자와 초기화 순서 입문](./java-constructors-initialization-order-basics.md)
- `private`, `static`, `final`이 메서드와 필드에 어떤 의미를 만드는지 보고 싶다면 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 메서드를 객체에 붙일지 `static` helper로 둘지, 생성용 `of()`/`from()`으로 만들지 구분하는 연습을 하고 싶다면 [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md)
- 캡슐화와 메시지 전달 관점에서 메서드를 다시 보고 싶다면 [객체지향 핵심 원리](./object-oriented-core-principles.md)
- 상태를 쉽게 바꾸지 않는 객체 설계까지 이어서 보고 싶다면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

## 한 줄 정리

constructor는 객체의 시작 상태를 만들고, method는 parameter를 받아 상태를 바꾸거나 읽고, return type은 결과를 밖으로 내보내며, overloading은 같은 의도를 다른 입력 형태로 열어 주는 장치다.
