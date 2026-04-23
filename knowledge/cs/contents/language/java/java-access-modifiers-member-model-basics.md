# Java 접근 제한자와 멤버 모델 입문

> 한 줄 요약: Java 입문자가 접근 제한자, 인스턴스 vs `static` 멤버, `final`의 의미를 하나의 클래스 모델로 연결해서 이해하도록 정리한 primer다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
> - [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
> - [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
> - [추상 클래스 vs 인터페이스](./abstract-class-vs-interface.md)
> - [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)

> retrieval-anchor-keywords: java access modifier basics, java access modifiers and member model, java public private protected package-private, java package private default access, java instance member vs static member, java static field vs instance field, java static method vs instance method, java static utility method basics, java static factory method basics, java final field method class, java beginner class member basics, java private static final constant, java encapsulation basics, access modifier beginner, class member model basics

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [접근 제한자는 무엇을 막고 무엇을 열어 주나](#접근-제한자는-무엇을-막고-무엇을-열어-주나)
- [멤버 모델: 인스턴스 vs static](#멤버-모델-인스턴스-vs-static)
- [final은 어디에 붙고 무엇을 고정하나](#final은-어디에-붙고-무엇을-고정하나)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [초보자가 자주 하는 실수](#초보자가-자주-하는-실수)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 초보자는 클래스를 배우기 시작하면 비슷해 보이는 modifier를 한꺼번에 만나게 된다.

- 필드는 왜 대부분 `private`일까?
- 어떤 값은 객체마다 다르고, 어떤 값은 `static`으로 함께 쓰는 걸까?
- `final`은 "상수"라는 뜻인가, "상속 금지"라는 뜻인가?

이 문서의 핵심은 modifier를 따로 외우지 않고 **"이 멤버가 누구 소유인가, 누가 접근해야 하는가, 앞으로 바뀔 수 있는가"** 라는 세 질문으로 연결해서 보는 데 있다.

## 접근 제한자는 무엇을 막고 무엇을 열어 주나

접근 제한자(access modifier)는 "이 클래스나 멤버를 어디까지 공개할 것인가"를 정하는 도구다.  
초보자 관점에서는 **정보 은닉과 사용 범위 관리**를 위한 스위치로 이해하면 된다.

### 1. top-level 클래스와 멤버는 허용 범위가 다르다

| 대상 | 가능한 접근 수준 | 설명 |
|---|---|---|
| top-level 클래스 | `public`, package-private | 파일 최상단 클래스는 `private`/`protected`를 쓸 수 없다 |
| 필드, 메서드, 생성자, 중첩 클래스 | `public`, `protected`, package-private, `private` | 멤버는 네 가지 접근 수준을 모두 가질 수 있다 |

여기서 package-private은 별도 키워드가 아니라 **아무 접근 제한자도 쓰지 않은 상태**를 뜻한다.

### 2. 멤버 접근 범위는 이렇게 기억하면 된다

| modifier | 같은 클래스 | 같은 패키지 | 다른 패키지의 하위 클래스 | 그 밖의 외부 |
|---|---|---|---|---|
| `public` | 가능 | 가능 | 가능 | 가능 |
| `protected` | 가능 | 가능 | 가능 | 불가 |
| package-private | 가능 | 가능 | 불가 | 불가 |
| `private` | 가능 | 불가 | 불가 | 불가 |

### 3. 초보자용 기본 선택 기준

- 필드는 기본적으로 `private`로 시작한다.
- 외부에 꼭 보여야 하는 메서드만 `public`으로 연다.
- 같은 패키지 안에서만 쓰는 헬퍼라면 package-private도 괜찮다.
- `protected`는 상속 설계가 분명할 때만 쓴다. 초보자 단계에서는 남용하기 쉽다.

즉 "일단 모두 열어 두고 필요하면 닫는 것"보다, **"일단 최소한만 열고 필요할 때 넓히는 것"** 이 안전하다.

## 멤버 모델: 인스턴스 vs static

멤버를 이해할 때 가장 중요한 축은 **객체 소속인지, 클래스 소속인지**다.

| 구분 | 누구 소유인가 | 접근 방식 | 언제 쓰나 |
|---|---|---|---|
| 인스턴스 멤버 | 객체 하나하나 | `account.deposit()` | 객체마다 다른 상태/동작 |
| `static` 멤버 | 클래스 전체 | `BankAccount.getCreatedCount()` | 모든 객체가 공유하는 값/동작 |

### 인스턴스 필드는 객체마다 따로 가진다

```java
public class BankAccount {
    private final String accountNumber;
    private int balance;

    public BankAccount(String accountNumber) {
        this.accountNumber = accountNumber;
    }
}
```

`accountNumber`, `balance`는 계좌 객체마다 다르다.  
`BankAccount`를 두 개 만들면 두 객체는 각자 자기 `balance`를 가진다.

### static 필드는 모든 객체가 함께 본다

```java
public class BankAccount {
    private static int createdCount = 0;

    public BankAccount(String accountNumber) {
        createdCount++;
    }

    public static int getCreatedCount() {
        return createdCount;
    }
}
```

`createdCount`는 특정 계좌 하나의 상태가 아니라 **클래스 전체가 공유하는 상태**다.  
새 계좌를 만들 때마다 하나의 값이 같이 증가한다.

### static 메서드는 클래스 관점의 동작이다

`static` 메서드는 객체 없이 호출할 수 있다.

```java
int created = BankAccount.getCreatedCount();
```

이런 메서드는 보통 다음 용도로 쓴다.

- 공용 규칙 검사
- 팩터리 메서드
- 공유 상태 조회
- 객체 상태와 무관한 유틸리티 동작

반대로 현재 객체의 `balance`처럼 인스턴스 상태를 다뤄야 한다면 인스턴스 메서드가 자연스럽다.

### static 메서드는 인스턴스 멤버를 직접 다룰 수 없다

`static` 메서드에는 `this`가 없다.  
그래서 객체가 있어야만 의미가 생기는 인스턴스 필드/메서드를 직접 사용할 수 없다.

```java
public static void printBalance() {
    // System.out.println(balance); // 컴파일 에러
}
```

이 규칙을 기억하면 "`static`은 클래스 소속"이라는 개념이 더 선명해진다.

## final은 어디에 붙고 무엇을 고정하나

`final`은 "더 이상 바꾸지 못하게 하겠다"는 의도를 나타내지만, **무엇을 고정하는지는 붙는 위치에 따라 달라진다**.

### 1. final field

```java
public class BankAccount {
    private final String accountNumber;
    private int balance;

    public BankAccount(String accountNumber) {
        this.accountNumber = accountNumber;
    }
}
```

`final` 필드는 한 번만 대입할 수 있다.  
보통 생성자에서 초기화하고, 그 뒤에는 다른 값을 다시 넣을 수 없다.

다만 참조형에서는 중요한 주의점이 있다.

```java
private final List<String> tags = new ArrayList<>();
```

이 코드는 `tags` 참조를 다른 리스트로 바꾸지는 못하게 하지만, 리스트 내부 요소 수정까지 막아 주지는 않는다.  
즉 **`final` 참조와 불변 객체는 같은 뜻이 아니다.**

### 2. final method

```java
public class Member {
    public final String role() {
        return "member";
    }
}
```

`final` 메서드는 하위 클래스가 오버라이드할 수 없다.  
즉 "이 동작은 상속받더라도 바꾸지 말라"는 뜻이다.

- 오버라이드는 금지된다.
- 오버로딩은 별개의 시그니처이므로 가능하다.

### 3. final class

```java
public final class FixedDiscountPolicy {
}
```

`final` 클래스는 상속할 수 없다.  
즉 타입 확장 자체를 막는다.

이 선택은 보통 다음 상황에서 쓴다.

- 불변 규칙을 깨는 하위 타입 생성을 막고 싶을 때
- 값 객체처럼 확장보다 안정성이 중요할 때
- 설계상 subtype 확장을 열어 둘 이유가 없을 때

### 4. 자주 보는 조합: private static final

```java
private static final int MIN_DEPOSIT = 1_000;
```

이 조합은 초보자가 가장 자주 만나게 되는 형태다.

- `private`: 클래스 밖에 공개하지 않음
- `static`: 객체마다 따로 두지 않고 클래스 전체가 공유
- `final`: 한 번 정해진 뒤 바뀌지 않음

즉 **클래스 내부 상수**를 표현하는 전형적인 형태다.

## 코드로 한 번에 보기

```java
public final class BankAccount {
    private static final int MIN_DEPOSIT = 1_000; // shared constant
    private static int createdCount = 0;          // shared mutable state

    private final String accountNumber;           // per-instance, assigned once
    private int balance;                          // per-instance, mutable

    public BankAccount(String accountNumber) {
        this.accountNumber = accountNumber;
        createdCount++;
    }

    public void deposit(int amount) {
        if (amount < MIN_DEPOSIT) {
            throw new IllegalArgumentException("amount too small");
        }
        balance += amount;
    }

    public final String getAccountNumber() {
        return accountNumber;
    }

    public int getBalance() {
        return balance;
    }

    public static int getCreatedCount() {
        return createdCount;
    }
}
```

이 코드를 읽을 때 초보자는 다음만 정확히 보이면 된다.

- `BankAccount`는 `final class`이므로 상속할 수 없다.
- `MIN_DEPOSIT`는 `private static final`이라 클래스 내부 상수다.
- `createdCount`는 `static`이라 모든 계좌 객체가 함께 공유한다.
- `accountNumber`는 `final` 인스턴스 필드라 객체마다 하나씩 있고 다시 대입할 수 없다.
- `deposit()`과 `getBalance()`는 인스턴스 상태를 다루므로 인스턴스 메서드다.
- `getCreatedCount()`는 클래스 전체 상태를 다루므로 `static` 메서드다.
- `getAccountNumber()`는 하위 클래스가 바꾸지 못하도록 `final` 메서드다.

## 초보자가 자주 하는 실수

### `final`이면 객체가 완전히 안 바뀐다고 생각한다

`final List<String> names`는 참조 재대입만 막는다.  
리스트 내부를 수정할 수 있는지는 별도의 문제다.

### 인스턴스 상태를 습관적으로 `static`으로 만든다

객체마다 달라야 하는 값을 `static`으로 두면 모든 객체가 같은 값을 공유해 버린다.  
`balance`, `name`, `age` 같은 값은 대부분 인스턴스 필드다.

### 필드를 곧바로 `public`으로 연다

초보자 코드에서 가장 흔한 실수다.  
필드를 열어 버리면 객체가 자기 규칙을 지키기 어려워진다. 보통은 `private` 필드 + 메서드 조합이 더 안전하다.

### package-private을 "modifier를 빼먹은 실수"로만 본다

명시적으로 패키지 안에서만 공개하고 싶을 때는 괜찮은 선택이다.  
다만 초보자 단계에서는 의도를 모르고 쓰기 쉬우니, 왜 열어 두는지 설명할 수 있어야 한다.

### `protected`를 "public보다 조금 덜 공개" 정도로 생각한다

`protected`는 단순 중간 단계가 아니라 **같은 패키지 + 하위 클래스**라는 상속 중심 규칙이다.  
상속 설계가 없다면 보통 `private`이나 package-private이 더 명확하다.

## 빠른 체크리스트

- 필드는 기본 `private`로 시작한다.
- 값이 객체마다 다르면 인스턴스 멤버다.
- 값이 클래스 전체에서 하나면 `static` 후보다.
- 바뀌지 않아야 하는 참조나 값을 필드에 담으면 `final`을 검토한다.
- 상수라면 `private static final` 형태를 먼저 떠올린다.
- `final field`와 불변 객체를 같은 뜻으로 혼동하지 않는다.

## 어떤 문서를 다음에 읽으면 좋은가

- 클래스/객체/인터페이스/추상 클래스까지 한 흐름으로 다시 정리하고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- package와 import가 package-private 경계와 어떻게 연결되는지 먼저 잡고 싶다면 [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
- 생성자와 메서드 시그니처를 객체 상태 변화와 함께 연습하고 싶다면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- 인스턴스 메서드와 `static` 메서드가 실제 설계에서 어떻게 갈리고, `of()`/`from()` 같은 팩터리 메서드는 언제 자연스러운지 이어서 보고 싶다면 [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md)
- 캡슐화, 정보 은닉, 상속, 다형성을 조금 더 길게 읽고 싶다면 [객체지향 핵심 원리](./object-oriented-core-principles.md)
- `final` 참조와 진짜 불변 객체의 차이를 더 정확히 보고 싶다면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
- 상속 경계를 언제 열고 닫을지 더 깊게 보고 싶다면 [추상 클래스 vs 인터페이스](./abstract-class-vs-interface.md)
- `final class` 이후 modern Java의 sealed 계열까지 이어 보고 싶다면 [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)

## 한 줄 정리

접근 제한자는 **누가 보게 할지**, 인스턴스/`static`은 **누가 소유하는지**, `final`은 **무엇을 고정할지**를 정하는 규칙이며, 세 개를 함께 봐야 Java 클래스의 기본 멤버 모델이 정리된다.
