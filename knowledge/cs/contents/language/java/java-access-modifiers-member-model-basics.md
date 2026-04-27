# Java 접근 제한자와 멤버 모델 입문

> 한 줄 요약: Java 입문자가 접근 제한자, 인스턴스 vs `static` 멤버, `final`의 의미를 하나의 클래스 모델로 연결해서 이해하도록 정리한 primer다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
> - [Java 패키지 경계 퀵체크 카드](./java-package-boundary-quickcheck-card.md)
> - [접근 제한자 오해 미니 퀴즈: top-level vs member](./java-access-modifier-top-level-member-mini-quiz.md)
> - [Java 접근 제한자 경계 실습](./java-access-modifier-boundary-lab.md) - 아래 `protected` follow-up 예제를 그대로 손으로 확인하는 실습
> - [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
> - [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md)
> - [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
> - [추상 클래스 vs 인터페이스](./abstract-class-vs-interface.md)
> - [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)

> retrieval-anchor-keywords: java access modifier basics, java access modifiers and member model, java modifier decision table, java public private protected package-private, java package private default access, java instance member vs static member, java static field vs instance field, java static method vs instance method, java static utility method basics, java static factory method basics, java final field method class, java beginner class member basics, java private static final constant, java encapsulation basics, access modifier beginner, class member model basics, java member modifier decision flow, java top-level vs member private protected, java top-level member mini quiz bridge, java protected access confusion, protected other package subclass access, protected field this vs parent reference, java protected this field access, java protected base reference compile error, java protected other package baseRef access, java protected child reference access, java protected this childRef parentRef table, java protected same package different package summary table, java protected compile success fail prediction, java protected method call same rule as field access, java protected method vs field same context rule, java access modifier follow-up example, java access modifier lab bridge, java protected lab entrypoint, java protected worksheet, java protected follow-up worksheet, java this protected vs parentRef protected, java this protected vs baseRef protected, java protected 3 question follow-up, java protected wrong answer note, java import does not change access protected, java subpackage same package misconception, java package name similarity protected confusion, java same package subclass non subclass, java package boundary quick card, 자바 protected this baseRef 차이, 자바 protected 워크시트, 자바 접근제한자 후속 문제, 자바 top-level member 구분, 자바 top-level private protected 불가 member 가능, 자바 import 해도 protected 안 보임, 자바 패키지명 비슷해도 다른 패키지, 자바 패키지 경계 퀵체크, java final reference vs immutable

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 보는 3축 모델](#먼저-보는-3축-모델)
- [접근 제한자는 무엇을 막고 무엇을 열어 주나](#접근-제한자는-무엇을-막고-무엇을-열어-주나)
- [멤버 모델: 인스턴스 vs static](#멤버-모델-인스턴스-vs-static)
- [final은 어디에 붙고 무엇을 고정하나](#final은-어디에-붙고-무엇을-고정하나)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [초보자가 자주 하는 실수](#초보자가-자주-하는-실수)
- [protected 빠른 비교표](#protected-빠른-비교표)
- [protected 3문항 follow-up](#protected-3문항-follow-up)
- [워크시트 아래 자주 나오는 오답 이유 3개](#워크시트-아래-자주-나오는-오답-이유-3개)
- [읽고 바로 실습 연결하기](#읽고-바로-실습-연결하기)
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

## 먼저 보는 3축 모델

처음엔 용어를 외우기보다, 멤버를 아래 세 축으로 먼저 분해하면 훨씬 덜 헷갈린다.

| 축 | 질문 | 대표 키워드 |
|---|---|---|
| 공개 범위 | 누가 이 멤버를 볼 수 있나? | `public`, `protected`, package-private, `private` |
| 소유권 | 객체마다 따로 있나, 클래스가 공유하나? | 인스턴스 vs `static` |
| 변경 가능성 | 한 번 정하면 바꿀 수 있나? | `final` |

실무에서 멤버를 추가할 때는 아래 순서가 안전하다.

1. 먼저 `private`로 시작하고, 정말 필요할 때만 공개 범위를 넓힌다.
2. 값이 객체마다 달라야 하면 인스턴스 멤버, 모두가 공유하면 `static`으로 둔다.
3. 생성 후 바뀌면 안 되는 값이면 `final`을 붙인다.

즉 modifier는 문법 암기보다 "설계 의도"를 표시하는 라벨에 가깝다.

### 30초 적용 예시: 새 멤버를 추가할 때

`BankAccount`에 멤버를 하나 추가한다고 가정하면, 아래처럼 3축으로 바로 결정할 수 있다.

| 멤버 후보 | 공개 범위 | 소유권 | 변경 가능성 | 첫 선택 이유 |
|---|---|---|---|---|
| 계좌번호 `accountNumber` | `private` | 인스턴스 | `final` | 객체마다 다르고 생성 후 바뀌지 않음 |
| 생성된 계좌 수 `createdCount` | `private` | `static` | mutable | 클래스 전체가 공유해야 함 |
| 최소 입금액 `MIN_DEPOSIT` | `private` | `static` | `final` | 클래스 공통 상수 |
| 외부 조회용 `getBalance()` | `public` | 인스턴스 메서드 | - | 인스턴스 상태를 안전하게 노출 |

초보자에게 중요한 포인트는 "modifier를 고르는 순서"다.

1. 누가 봐야 하는가(접근 제한자)
2. 누가 소유하는가(인스턴스 vs `static`)
3. 바뀌어도 되는가(`final`)

## 접근 제한자는 무엇을 막고 무엇을 열어 주나

접근 제한자(access modifier)는 "이 클래스나 멤버를 어디까지 공개할 것인가"를 정하는 도구다.
초보자 관점에서는 **정보 은닉과 사용 범위 관리**를 위한 스위치로 이해하면 된다.

### 1. top-level 클래스와 멤버는 허용 범위가 다르다

| 대상 | 가능한 접근 수준 | 설명 |
|---|---|---|
| top-level 클래스 | `public`, package-private | 파일 최상단 클래스는 `private`/`protected`를 쓸 수 없다 |
| 필드, 메서드, 생성자, 중첩 클래스 | `public`, `protected`, package-private, `private` | 멤버는 네 가지 접근 수준을 모두 가질 수 있다 |

여기서 package-private은 별도 키워드가 아니라 **아무 접근 제한자도 쓰지 않은 상태**를 뜻한다.

이 한 표가 아직 손에 안 붙으면 [접근 제한자 오해 미니 퀴즈: top-level vs member](./java-access-modifier-top-level-member-mini-quiz.md)로 먼저 5문항만 예측하고 돌아오면 훨씬 덜 헷갈린다.

### 2. 멤버 접근 범위는 이렇게 기억하면 된다

| modifier | 같은 클래스 | 같은 패키지 | 다른 패키지의 하위 클래스 | 그 밖의 외부 |
|---|---|---|---|---|
| `public` | 가능 | 가능 | 가능 | 가능 |
| `protected` | 가능 | 가능 | 가능 | 불가 |
| package-private | 가능 | 가능 | 불가 | 불가 |
| `private` | 가능 | 불가 | 불가 | 불가 |

same package / subclass / non-subclass를 먼저 빠르게 자르고 싶다면 [Java 패키지 경계 퀵체크 카드](./java-package-boundary-quickcheck-card.md)를 먼저 보고 돌아오면 `protected`가 훨씬 덜 헷갈린다.

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

### `protected`면 "아무 객체에서 접근 가능"하다고 생각한다

다른 패키지에서 `protected`에 접근할 때는 "하위 클래스 문맥"이 필요하다.
즉 `protected`는 무조건 넓은 공개가 아니라, **상속을 전제로 한 제한적 공개**다.

- 메서드 호출이든 필드 참조든 규칙은 같다.
- `this.protectedMethod()`가 되면 보통 `this.points`도 같은 이유로 되고, `baseRef.protectedMethod()`가 안 되면 `baseRef.points`도 같은 이유로 안 된다.
- 즉 `protected`는 "메서드냐 필드냐"보다 "지금 누구 문맥에서, 어떤 참조로 접근하느냐"를 먼저 본다.

처음엔 이렇게 기억하면 된다.

- 상속 설계가 없다면 `protected`보다 `private`/package-private이 보통 더 안전하다.
- "확장 지점"을 실제로 열어야 할 때만 `protected`를 선택한다.

작은 코드로 보면 차이가 더 선명하다.

```java
// 다른 패키지
class Child extends Parent {
    void ok() {
        this.protectedMethod(); // 가능: 하위 클래스 문맥
    }
}

class Other {
    void fail(Child child) {
        // child.protectedMethod(); // 불가: 하위 클래스 문맥이 아님
    }
}
```

필드로 보면 더 자주 헷갈린다. 핵심은 "다른 패키지에서는 하위 클래스 자기 자신(또는 그 하위 클래스 타입) 문맥으로만 접근 가능"이라는 점이다.

```java
// package a
package a;
public class Parent {
    protected int points = 10;
}

// package b
package b;
import a.Parent;

public class Child extends Parent {
    void ok() {
        System.out.println(this.points); // 가능: Child 자신의 inherited protected 멤버 접근
    }

    void fail(Parent baseRef) {
        // System.out.println(baseRef.points); // 컴파일 오류
        // 다른 패키지에서는 "Parent 참조 변수"를 통해 protected에 접근할 수 없다.
    }
}
```

처음엔 이렇게 기억하면 된다.

- `this.points`는 "하위 클래스 내부에서 자기 자신의 protected 멤버 접근"이라 가능
- `baseRef.points`는 "다른 패키지의 부모 타입 참조를 통한 접근"이라 불가

## protected 빠른 비교표

초보자는 `protected`를 볼 때 "누가 상속했는가"보다 먼저 아래 두 질문만 보면 된다.

1. 지금 접근 위치가 같은 패키지인가?
2. 다른 패키지라면, 하위 클래스 내부에서 `this`나 `Child` 타입 참조로 접근하는가?

아래 한 표로 먼저 예측하면 컴파일 성공/실패를 빨리 맞힐 수 있다.

| 패키지 관계 | 접근하는 곳 | 표현식 | 컴파일 | 이유 |
|---|---|---|---|---|
| 같은 패키지 | 일반 클래스 | `parentRef.points` | 성공 | 같은 패키지에서는 `protected`를 패키지 멤버처럼 볼 수 있다 |
| 같은 패키지 | 일반 클래스 | `childRef.points` | 성공 | 같은 패키지라 참조 타입이 `Child`여도 그대로 가능 |
| 다른 패키지 | `Child` 내부 | `this.points` | 성공 | 하위 클래스가 자기에게 상속된 `protected` 멤버를 읽는 경우다 |
| 다른 패키지 | `Child` 내부 | `childRef.points` | 성공 | 다른 패키지라도 `Child` 타입(또는 그 하위 타입) 참조면 허용된다 |
| 다른 패키지 | `Child` 내부 | `parentRef.points` | 실패 | 부모 타입 참조를 통한 접근은 "하위 클래스 자기 멤버 접근"으로 보지 않는다 |
| 다른 패키지 | 하위 클래스가 아닌 일반 클래스 | `childRef.points` | 실패 | 상속 문맥이 아니므로 `protected`가 열리지 않는다 |

짧게 줄이면 이렇게 기억하면 된다.

- 같은 패키지: `protected`는 거의 package-private처럼 접근 가능
- 다른 패키지: `this` 또는 `Child` 쪽 참조만 가능
- 다른 패키지의 `Parent` 참조: 실패

작은 예제로 다시 보면 표와 코드가 바로 연결된다.

```java
// package a
package a;
public class Parent {
    protected int points = 10;
}

// package b
package b;
import a.Parent;

public class Child extends Parent {
    void check(Child childRef, Parent parentRef) {
        System.out.println(this.points);      // OK
        System.out.println(childRef.points);  // OK
        // System.out.println(parentRef.points); // compile error
    }
}
```

여기서 `childRef.points`가 되는 이유는 "현재 코드가 `Child` 내부이고, 접근 대상도 `Child` 계열"이기 때문이다.
반대로 `parentRef.points`는 참조 변수의 타입이 `Parent`라서 같은 `points`여도 규칙이 바뀐다.

## protected 3문항 follow-up

여기서 초보자가 가장 많이 틀리는 지점은 "하위 클래스 안이면 다 되겠지?"라는 생각이다.
아래 3문항은 그 오개념만 빠르게 고치기 위한 최소 워크시트다.

먼저 이 한 줄만 기억하면 된다.

- 다른 패키지의 `protected`는 `this`나 `Child` 계열 참조일 때만 열린다.
- `Parent` 타입 참조(`baseRef`, `parentRef`)로 보면 같은 하위 클래스 안이어도 닫힌다.

```java
// package a
package a;
public class Parent {
    protected int points = 10;
}

// package b
package b;
import a.Parent;

public class Child extends Parent {
    void followUp(Child childRef, Parent baseRef) {
        System.out.println(this.points);      // 1
        System.out.println(childRef.points);  // 2
        System.out.println(baseRef.points);   // 3
    }
}
```

실행 전에 먼저 `성공`/`실패`를 적어 본다.

| 문항 | 표현식 | 예측 | 정답 | 이유 |
|---|---|---|---|---|
| 1 | `this.points` |  | 성공 | 하위 클래스 자기 자신의 inherited `protected` 멤버 접근 |
| 2 | `childRef.points` |  | 성공 | 현재 코드가 `Child` 내부이고, 참조도 `Child` 계열 |
| 3 | `baseRef.points` |  | 실패 | `Parent` 타입 참조를 통한 접근은 허용되지 않음 |

헷갈리면 용어보다 아래 질문 순서로 보면 된다.

1. 지금 코드는 하위 클래스 내부인가?
2. 접근 대상도 `Child` 자기 자신 또는 `Child` 계열 참조인가?
3. 참조 타입이 `Parent`로 내려가면 실패로 본다.

## 워크시트 아래 자주 나오는 오답 이유 3개

워크시트에서 3번을 `성공`으로 적는 초급자 답안은 보통 아래 세 오해 중 하나에 걸린다.

> `import` 오해
>
> "`import a.Parent;`를 했으니 `baseRef.points`도 보이겠지"라고 생각하기 쉽다.
> 하지만 `import`는 이름을 짧게 쓰게 해 줄 뿐이고, `protected` 접근 규칙 자체는 바꾸지 못한다.
> 즉 `import`를 했어도 다른 패키지의 `Parent` 참조로 보는 순간 `baseRef.points`는 여전히 막힌다.
> 먼저 [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)의 "`import`는 이름을 줄여 주지만 접근 권한은 바꾸지 않는다" 구간으로 연결해서 보면 바로 정리된다.

> 패키지명 유사성 오해
>
> `package a;`와 `package a.child;`를 같은 묶음처럼 느껴서 "거의 같은 패키지니까 `protected`가 풀리겠지"라고 오해하기 쉽다.
> Java는 이름이 비슷한지를 보지 않고, package 선언이 **완전히 같은지**만 본다.
> 그래서 `a`와 `a.child`는 다른 패키지고, 다른 패키지 규칙을 그대로 적용해야 한다.
> 이 감각이 약하면 [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)의 "같은 부모를 공유해도 다른 package일 수 있다"와 [Java 패키지 경계 퀵체크 카드](./java-package-boundary-quickcheck-card.md)를 같이 보는 편이 빠르다.

> `protected` 범위 오해
>
> "하위 클래스 안에만 있으면 아무 `Parent` 객체의 `protected` 멤버도 읽을 수 있다"라고 생각하는 경우가 가장 많다.
> 하지만 다른 패키지에서는 `protected`가 "하위 클래스 문맥"만으로 열리지 않고, **`this` 또는 `Child` 계열 참조**일 때만 열린다.

| 표현식 | 초급자 오답 이유 | 실제 판단 |
|---|---|---|
| `this.points` | 하위 클래스 안이니까 된다 | 맞다. 자기 자신에게 상속된 멤버 접근 |
| `childRef.points` | `this`가 아닌데도 되나? | 된다. 현재 코드도 `Child` 내부이고 참조도 `Child` 계열 |
| `baseRef.points` | 하위 클래스 안이니까 이것도 되겠지 | 안 된다. 참조 타입이 `Parent`라서 다른 패키지 규칙에 막힌다 |

이 표에서 막히면 "`누가 상속했나`"보다 "`지금 어떤 참조 타입으로 보고 있나`"를 먼저 체크하면 된다.

## 읽고 바로 실습 연결하기

위 표를 읽고도 손에 안 붙으면, 아래 3줄만 먼저 외운 뒤 바로 [Access Modifier Boundary Lab](./java-access-modifier-boundary-lab.md)로 넘어가면 된다.

| 이 문서의 follow-up 예제 | Lab에서 바로 확인할 위치 | 초보자용 질문 |
|---|---|---|
| 같은 패키지에서는 `protected`가 package-private처럼 보인다 | `SamePackageProbe` + 기본 퀴즈 1번 | "같은 패키지면 왜 `protectedPin`이 바로 보이지?" |
| 다른 패키지 하위 클래스 내부의 `this.points`는 된다 | `BetaSubVault.testInSubclass()` + `protected` follow-up 1번 | "상속받은 자기 멤버라서 되나?" |
| 다른 패키지 하위 클래스 내부의 `childRef.points`도 된다 | `protected` follow-up 2번 | "`this`만 되고 같은 Child 참조는 왜 되지?" |
| 다른 패키지의 `parentRef.points`는 안 된다 | `protected` follow-up 3번 | "하위 클래스 안인데 왜 부모 참조는 안 되지?" |

실습 전에 아래 예제를 한 번 눈으로 예측해 보면 lab 체감이 훨씬 좋아진다.

```java
// package a
package a;
public class Parent {
    protected int points = 10;
}

// package b
package b;
import a.Parent;

public class Child extends Parent {
    void preview(Child childRef, Parent parentRef) {
        System.out.println(this.points);      // OK
        System.out.println(childRef.points);  // OK
        // System.out.println(parentRef.points); // compile error
    }
}
```

핵심은 한 문장이다.

- 다른 패키지의 `protected`는 "하위 클래스 안"이라는 사실만으로 충분하지 않다.
- **하위 클래스 자기 자신(`this`)이나 `Child` 계열 참조로 접근할 때만** 열린다.

즉 이 예제를 읽었다면 다음 단계는 설명을 더 읽는 것보다, lab에서 주석을 하나씩 풀어 보며 "성공/실패를 먼저 맞히는 연습"이다.

## 빠른 체크리스트

- 필드는 기본 `private`로 시작한다.
- 값이 객체마다 다르면 인스턴스 멤버다.
- 값이 클래스 전체에서 하나면 `static` 후보다.
- 바뀌지 않아야 하는 참조나 값을 필드에 담으면 `final`을 검토한다.
- 상수라면 `private static final` 형태를 먼저 떠올린다.
- `final field`와 불변 객체를 같은 뜻으로 혼동하지 않는다.

## 어떤 문서를 다음에 읽으면 좋은가

지금 막힌 포인트 기준으로 다음 문서를 고르면 훨씬 빠르다.

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `protected` 예제를 읽었는데 손으로는 아직 헷갈린다 | [Access Modifier Boundary Lab](./java-access-modifier-boundary-lab.md) |
| package 경계와 접근 제한자가 함께 헷갈린다 | [Java package와 import 경계 입문](./java-package-import-boundary-basics.md) |
| 인스턴스 메서드와 `static` 메서드 선택이 흔들린다 | [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java-instance-static-factory-methods-primer.md) |
| `final` 참조와 불변 객체 차이가 헷갈린다 | [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md) |
| 상속 경계를 언제 열어야 하는지 감이 없다 | [추상 클래스 vs 인터페이스](./abstract-class-vs-interface.md) |

클래스/객체 큰 그림을 다시 보고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md), modern Java 타입 경계까지 확장하려면 [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)을 이어서 보면 된다.

## 한 줄 정리

접근 제한자는 **누가 보게 할지**, 인스턴스/`static`은 **누가 소유하는지**, `final`은 **무엇을 고정할지**를 정하는 규칙이며, 세 개를 함께 봐야 Java 클래스의 기본 멤버 모델이 정리된다.
