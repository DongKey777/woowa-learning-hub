# Java 패키지 경계 퀵체크 카드

> 한 줄 요약: Java 입문자가 `same package / subclass / non-subclass`를 10초 안에 구분해서 `public`/`protected`/package-private 접근 가능 여부를 빠르게 판단하도록 돕는 beginner quick card다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
> - [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
> - [Access Modifier Boundary Lab](./java-access-modifier-boundary-lab.md)
> - [Java Top-level 타입 접근 제한자 브리지](./top-level-type-access-modifier-bridge.md)

> retrieval-anchor-keywords: java package boundary quickcheck card, java package boundary quick check, same package subclass non subclass, java protected quick check, java package private quick check, java access boundary card, java same package different package subclass rule, java protected same package subclass non subclass table, java protected access quick card, java package import boundary follow-up, 자바 패키지 경계 체크 카드, 자바 same package subclass non-subclass, 자바 protected 빠른 판단, 자바 package-private 빠른 판단, 자바 접근 경계 퀵체크

## 먼저 잡는 멘탈 모델

복잡하게 외우기보다 아래 순서로만 보면 된다.

1. **같은 package인가?**
2. 아니면 **다른 package의 subclass인가?**
3. 둘 다 아니면 **non-subclass 외부 코드**다.

이 세 칸으로 나누면 초보자가 자주 헷갈리는 `protected`와 package-private을 빨리 정리할 수 있다.

## 10초 판단표

| 접근하는 코드 위치 | `public` | `protected` | package-private | `private` |
|---|---|---|---|---|
| same package | 가능 | 가능 | 가능 | 불가 |
| different package + subclass | 가능 | 가능 | 불가 | 불가 |
| different package + non-subclass | 가능 | 불가 | 불가 | 불가 |

초보자용 한 줄 기억법:

- **same package면** `private`만 빼고 대부분 된다.
- **subclass면** 다른 package여도 `protected`까지는 볼 수 있다.
- **non-subclass 외부 코드면** 사실상 `public`만 본다.

## 먼저 보는 체크리스트 카드

코드를 볼 때 아래 세 질문만 순서대로 답하면 된다.

1. 지금 접근하는 쪽과 선언된 타입이 **정확히 같은 package 선언**인가?
2. 같지 않다면, 지금 코드는 그 타입을 **상속한 subclass 내부**인가?
3. 둘 다 아니라면 `public`이 아니면 안 된다고 보면 된다.

여기서 중요한 점:

- `com.example.order`와 `com.example.order.internal`은 이름이 비슷해도 **same package가 아니다**.
- `import`는 이름을 줄여 줄 뿐, 위 표를 바꾸지 못한다.
- top-level 타입은 `public` 아니면 package-private만 가능하므로 `protected class` 같은 top-level 선언은 불가다.

## 작은 예시로 바로 확인

```java
// package a
package a;

public class Parent {
    public int open = 1;
    protected int extendOnly = 2;
    int packageOnly = 3;
    private int secret = 4;
}
```

```java
// package a
package a;

public class SamePackageUser {
    void read(Parent parent) {
        System.out.println(parent.open);       // 가능
        System.out.println(parent.extendOnly); // 가능
        System.out.println(parent.packageOnly);// 가능
        // System.out.println(parent.secret);  // 불가
    }
}
```

```java
// package b
package b;

import a.Parent;

public class Child extends Parent {
    void read() {
        System.out.println(this.open);         // 가능
        System.out.println(this.extendOnly);   // 가능
        // System.out.println(this.packageOnly); // 불가
    }
}
```

```java
// package b
package b;

import a.Parent;

public class OutsideUser {
    void read(Parent parent) {
        System.out.println(parent.open);       // 가능
        // System.out.println(parent.extendOnly); // 불가
        // System.out.println(parent.packageOnly);// 불가
    }
}
```

## 자주 틀리는 포인트 3개

### `protected`를 "같은 package 아니면 다 불가"로 외운다

다른 package여도 subclass 내부라면 `protected`는 가능하다.
그래서 `protected`는 package 규칙만이 아니라 **상속 규칙까지 같이 보는 칸**이다.

### `protected`를 "상속만 했으면 어디서나 가능"으로 외운다

subclass 관계가 있어도, 접근 위치가 subclass 내부 문맥이 아니면 바로 단순 외부 코드처럼 본다.
더 자세한 `this`/`childRef`/`baseRef` 차이는 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md#protected-빠른-비교표)에서 이어 보면 된다.

### import를 권한처럼 생각한다

`import a.Parent;`를 해도 `packageOnly`나 `protected` 규칙은 그대로다.
즉 import는 "보이게 만드는 마법"이 아니라 "이름을 짧게 쓰는 문법"이다.

## 어디로 이어서 읽으면 좋은가

- `package`와 `import`를 왜 먼저 보는지 큰 그림부터 다시 잡고 싶다면 [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
- `protected`의 더 까다로운 참조 규칙까지 보려면 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 직접 컴파일 성공/실패를 손으로 확인하려면 [Access Modifier Boundary Lab](./java-access-modifier-boundary-lab.md)

## 한 줄 정리

Java 접근 경계는 먼저 `same package인가`, 아니면 `different package의 subclass인가`, 그것도 아니면 `non-subclass 외부 코드인가` 세 칸으로 나누면 가장 빠르게 판단된다.
