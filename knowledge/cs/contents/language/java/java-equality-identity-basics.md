# Java Equality and Identity Basics

> 한 줄 요약: Java 입문자가 `==`, `.equals()`, `hashCode()`, 문자열 비교, 기본형과 참조형 비교 차이를 한 흐름으로 이해하도록 정리한 primer다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)
> - [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
> - [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
> - [Java Array Equality Basics](./java-array-equality-basics.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
> - [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
> - [String Intern and Pool Pitfalls](./string-intern-pool-pitfalls.md)
> - [Java Collections 성능 감각](./collections-performance.md)

> retrieval-anchor-keywords: java equality basics, java identity basics, java `==` vs `equals`, java `hashCode` basics, java string comparison basics, java primitive vs reference comparison, java object equality, java reference equality, java beginner equality, java record equality basics, java record equals hashCode, value object equality basics, mutable entity equality hazard, mutable key equals hashCode bug, hashmap mutable key, hashmap key mutation lookup, hashset mutable element bug, mutable hash key beginner, java array equality basics, java array `==` vs `equals`, java `Arrays.equals`, java `Arrays.deepEquals`, `HashMap` `HashSet` equals hashCode, `String` equals vs `==`, `Objects.equals`, java comparable basics, java comparator basics, java compareTo equals consistency, java natural ordering basics, 자바 == equals 차이, 처음 배우는데 == equals hashcode, 자바 문자열 비교 equals, 객체 동일성 동등성 차이, 자바 hashCode 왜 같이 구현, equals만 구현하면 안 되는 이유, 언제 == 쓰고 언제 equals 쓰는지, 자바 비교 연산 큰 그림

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [같은 값과 같은 객체는 다르다](#같은-값과-같은-객체는-다르다)
- [비교 연산의 차이](#비교-연산의-차이)
- [hashCode 기본기](#hashcode-기본기)
- [문자열 비교는 어떻게 해야 하나](#문자열-비교는-어떻게-해야-하나)
- [초보자가 자주 하는 비교 실수](#초보자가-자주-하는-비교-실수)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 비교 연산에서 가장 자주 막히는 지점은 "같다"의 의미가 하나가 아니라는 점이다.

- 숫자 `10`과 `10`은 왜 `==`로 비교해도 될까?
- `String`은 왜 `==`가 아니라 `equals()`를 써야 할까?
- `equals()`를 만들면 왜 `hashCode()`도 같이 만들라고 할까?
- `HashSet`에 넣었는데 중복 제거가 왜 안 될까?

이 문서는 위 질문을 초급 수준에서 한 번에 정리한다.
정렬 계약, `BigDecimal`, JPA 엔티티 같은 심화 설계는 관련 문서로 확장하고, 여기서는 초보자가 먼저 실수하지 않아야 할 최소 규칙을 잡는다.

## 같은 값과 같은 객체는 다르다

Java에서는 "같다"를 두 축으로 나눠서 봐야 한다.

| 관점 | 질문 | 대표 도구 | 예시 |
|---|---|---|---|
| 값의 동등성 equality | 내용이 같은가 | `.equals()` | `"java"`와 `"java"` |
| 객체 동일성 identity | 같은 객체를 보고 있는가 | `==` | 같은 `String` 인스턴스인지 |

기본형과 참조형도 같이 구분해야 한다.

| 구분 | 예시 | `==` 의미 | `.equals()` 사용 가능 여부 |
|---|---|---|---|
| 기본형 | `int`, `long`, `double`, `boolean` | 값 비교 | 불가 |
| 참조형 | `String`, 배열, 클래스, `Integer` | 같은 객체인지 비교 | 가능 |

즉 `==`는 항상 같은 의미가 아니다.

- 기본형에서는 값 비교
- 참조형에서는 객체 identity 비교

이 차이를 놓치면 `String`, wrapper, 컬렉션 key에서 버그가 생긴다.

## 비교 연산의 차이

### 기본형은 `==`로 값을 비교한다

```java
int left = 10;
int right = 10;

System.out.println(left == right); // true
```

기본형은 값 자체를 다루므로 `==`가 곧 값 비교다.

### 참조형에서 `==`는 같은 객체인지 본다

```java
String a = new String("java");
String b = new String("java");

System.out.println(a == b); // false
```

두 문자열의 내용은 같지만 서로 다른 객체이므로 `==`는 `false`다.

### 참조형에서 내용 비교는 보통 `.equals()`로 한다

```java
System.out.println(a.equals(b)); // true
```

`equals()`는 "논리적으로 같은 값인가"를 표현한다.
다만 모든 클래스가 자동으로 값 비교를 해 주는 것은 아니다.

### `Object`의 기본 `equals()`는 사실상 identity 비교다

클래스가 `equals()`를 오버라이드하지 않으면, 기본 구현은 `==`와 비슷하게 동작한다.
그래서 사용자 정의 클래스는 "무엇이 같다고 볼 것인가"를 직접 정해야 할 수 있다.

```java
import java.util.Objects;

public final class Member {
    private final long id;
    private final String name;

    public Member(long id, String name) {
        this.id = id;
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Member member)) return false;
        return id == member.id && Objects.equals(name, member.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name);
    }
}
```

위처럼 구현하면 서로 다른 인스턴스라도 `id`와 `name`이 같을 때 같은 값으로 볼 수 있다.

## hashCode 기본기

`hashCode()`는 해시 기반 컬렉션이 빠르게 위치를 찾기 위해 쓰는 정수다.

- `HashMap`
- `HashSet`
- `ConcurrentHashMap`

핵심 규칙은 하나만 먼저 기억해도 충분하다.

- `equals()`가 `true`면 `hashCode()`도 같아야 한다.

왜냐하면 `HashMap`과 `HashSet`은 대략 다음 순서로 동작하기 때문이다.

1. `hashCode()`로 후보 위치를 찾는다.
2. 그 안에서 `equals()`로 정말 같은지 확인한다.

그래서 `equals()`만 바꾸고 `hashCode()`를 안 바꾸면, "같은 값"인데도 다른 위치에 들어가서 조회나 중복 제거가 깨질 수 있다.

```java
Member first = new Member(1L, "jane");
Member second = new Member(1L, "jane");

System.out.println(first.equals(second)); // true
System.out.println(first.hashCode() == second.hashCode()); // true 여야 한다
```

초보자용 규칙으로는 다음이 가장 안전하다.

- `equals()`를 오버라이드하면 `hashCode()`도 같이 오버라이드한다.
- 둘 다 같은 필드를 기준으로 만든다.
- `HashMap` key나 `HashSet` 원소로 쓸 값은 가능하면 불변으로 둔다.

## 문자열 비교는 어떻게 해야 하나

문자열은 참조형이므로 내용 비교에 `==`를 쓰면 안 된다.

```java
String role = new String("ADMIN");

System.out.println(role == "ADMIN"); // false
System.out.println(role.equals("ADMIN")); // true
```

실무와 학습 코드에서 가장 흔히 쓰는 안전한 형태는 다음 두 가지다.

### null이 아닐 것이 분명하면 `.equals()`

```java
if (role.equals("ADMIN")) {
    // ...
}
```

### null 가능성이 있으면 리터럴을 앞으로

```java
if ("ADMIN".equals(role)) {
    // role이 null이어도 안전
}
```

양쪽 모두 null일 수 있으면 `Objects.equals(a, b)`가 더 편하다.

```java
import java.util.Objects;

System.out.println(Objects.equals(role, inputRole));
```

문자열 리터럴은 intern 때문에 `==`가 우연히 `true`처럼 보일 수 있다.
그래서 초보자가 더 자주 속는다. 이 부분은 [String Intern and Pool Pitfalls](./string-intern-pool-pitfalls.md)에서 더 깊게 이어진다.

## 초보자가 자주 하는 비교 실수

### 1. `String` 내용을 `==`로 비교한다

```java
if (userInput == "yes") {
    // 우연히만 맞을 수 있다
}
```

문자열 내용 비교는 `equals()` 또는 `Objects.equals()`를 쓴다.

### 2. wrapper를 primitive처럼 비교한다

```java
Integer a = 127;
Integer b = 127;
Integer c = 128;
Integer d = 128;

System.out.println(a == b); // true 일 수 있다
System.out.println(c == d); // false 일 수 있다
```

`Integer`, `Long`, `Boolean`은 기본형이 아니라 참조형이다.
cache와 autoboxing 때문에 `==`가 가끔 맞아 보여 더 위험하다.

### 3. null wrapper를 primitive 문맥에서 비교한다

```java
Integer count = null;

if (count == 0) { // NullPointerException
    // ...
}
```

이 비교는 `count`가 자동 unboxing되면서 예외를 낸다.
wrapper와 기본형을 섞을 때는 null 가능성을 먼저 생각해야 한다.

### 4. `equals()`만 만들고 `hashCode()`를 빼먹는다

```java
Set<Member> members = new HashSet<>();
members.add(new Member(1L, "jane"));
members.add(new Member(1L, "jane"));
```

논리적으로 같은 `Member`를 같은 값으로 다루려면 `equals()`와 `hashCode()`가 함께 맞아야 한다.

### 5. "변수 복사"를 "객체 복사"로 오해한다

```java
Member original = new Member(1L, "jane");
Member copied = original;

System.out.println(original == copied); // true
```

참조형 변수 대입은 객체를 새로 만드는 것이 아니라 같은 객체를 함께 가리키게 하는 것이다.

## 코드로 한 번에 보기

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

public class EqualityExample {
    public static void main(String[] args) {
        int x = 10;
        int y = 10;
        System.out.println(x == y); // true

        String s1 = new String("java");
        String s2 = new String("java");
        System.out.println(s1 == s2); // false
        System.out.println(s1.equals(s2)); // true

        System.out.println("ADMIN".equals(s1)); // false
        System.out.println(Objects.equals(s1, s2)); // true

        Member m1 = new Member(1L, "jane");
        Member m2 = new Member(1L, "jane");
        System.out.println(m1 == m2); // false
        System.out.println(m1.equals(m2)); // true

        Set<Member> members = new HashSet<>();
        members.add(m1);
        members.add(m2);
        System.out.println(members.size()); // 1
    }

    private static final class Member {
        private final long id;
        private final String name;

        private Member(long id, String name) {
            this.id = id;
            this.name = name;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof Member member)) return false;
            return id == member.id && Objects.equals(name, member.name);
        }

        @Override
        public int hashCode() {
            return Objects.hash(id, name);
        }
    }
}
```

이 예제에서 확인할 포인트는 네 가지다.

- 기본형은 `==`가 값 비교다.
- 참조형은 `==`가 identity 비교다.
- 문자열 내용 비교는 `equals()`나 `Objects.equals()`다.
- `HashSet` 중복 제거는 `equals()`와 `hashCode()`를 함께 본다.

## 빠른 체크리스트

- 기본형 비교는 `==`
- 참조형 내용 비교는 보통 `equals()`
- 같은 객체인지 묻는 경우에만 참조형 `==`
- 문자열 비교는 보통 `"LITERAL".equals(value)` 또는 `Objects.equals(a, b)`
- `equals()`를 오버라이드하면 `hashCode()`도 같이 구현
- 해시 컬렉션 key는 가능한 불변으로 유지
- `Integer`, `Long`, `Boolean`도 참조형이라는 점을 잊지 않기

## 어떤 문서를 다음에 읽으면 좋은가

- 초급 흐름을 먼저 이어가려면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- 값 객체 관점에서 equality를 확장해 보고 싶다면 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- 배열 비교 함정을 따로 정리해서 보려면 [Java Array Equality Basics](./java-array-equality-basics.md)
- 정렬 기준과 `equals()` 관계까지 이어서 보려면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `equals()`와 `hashCode()` 계약을 더 정확히 보려면 [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
- wrapper 비교 함정을 더 보려면 [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
- 문자열 pool과 `intern()`까지 확장하려면 [String Intern and Pool Pitfalls](./string-intern-pool-pitfalls.md)
- 해시 컬렉션 성능과 연결해 보려면 [Java Collections 성능 감각](./collections-performance.md)

## 한 줄 정리

Java에서 기본형은 `==`로 값을 비교하지만, 참조형은 `==`가 객체 identity를 보고 `equals()`가 논리적 동등성을 보므로, 문자열과 해시 컬렉션에서는 특히 이 차이를 분명히 구분해야 한다.
