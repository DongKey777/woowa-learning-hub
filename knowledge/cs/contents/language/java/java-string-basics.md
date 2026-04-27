# Java String 기초

> 한 줄 요약: String은 불변 객체이므로 `+` 연산마다 새 객체를 만들고, 내용 비교에는 `equals()`를 써야 하며, 반복적인 문자열 조합에는 `StringBuilder`가 훨씬 효율적이다.

**난이도: 🟢 Beginner**

관련 문서:

- [string-intern-pool-pitfalls](./string-intern-pool-pitfalls.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [`equalsIgnoreCase()` vs `CASE_INSENSITIVE_ORDER` Bridge](./equalsignorecase-vs-case-insensitive-order-bridge.md)
- [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
- [language 카테고리 인덱스](../README.md)
- [Java 불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

retrieval-anchor-keywords: java string basics, string 불변성 입문, string equals beginner, string vs stringbuilder, 문자열 비교 방법, java string 입문, string 왜 equals 써야 하나요, string pool beginner, 자바 문자열 기초, string concatenation beginner, stringbuilder 언제 써야 하나, string immutable beginner

## 핵심 개념

Java의 `String`은 한 번 만들어지면 내용이 바뀌지 않는 **불변(immutable)** 객체다. `str = str + "world"` 처럼 보여도 원래 문자열이 바뀌는 게 아니라 새 `String` 객체가 생기고 참조가 교체된다.

입문자가 가장 자주 저지르는 실수 두 가지가 있다. 첫째, `==`로 문자열 내용을 비교하는 것. 둘째, 반복문 안에서 `+`로 문자열을 이어 붙이는 것. 두 실수 모두 결과가 잘못되거나 성능이 나빠진다.

## 한눈에 보기

```
String a = "hello";
String b = "hello";
String c = new String("hello");

a == b        → true  (String Pool에서 같은 객체)
a == c        → false (new로 만든 별도 객체)
a.equals(c)   → true  (내용 비교)

// 반복 연결 성능 차이
String result = "";
for (int i = 0; i < 1000; i++) result += i;  // 객체 1000개 생성

StringBuilder sb = new StringBuilder();
for (int i = 0; i < 1000; i++) sb.append(i); // 객체 1개 재사용
String result = sb.toString();
```

## 상세 분해

### String 불변성

`String` 내부의 `char[]` 배열은 `final`로 선언되어 변경할 수 없다. 메서드(`toUpperCase`, `substring` 등)는 원본을 바꾸지 않고 새 `String`을 반환한다.

```java
String s = "hello";
String upper = s.toUpperCase(); // s는 여전히 "hello"
// upper는 "HELLO"인 새 객체
```

### equals()와 ==

`==`는 참조(주소)를 비교한다. `equals()`는 내용을 비교한다. 문자열 내용이 같은지 확인할 때는 항상 `equals()`를 써야 한다.

```java
String a = new String("hi");
String b = new String("hi");
System.out.println(a == b);       // false (다른 객체)
System.out.println(a.equals(b));  // true  (같은 내용)
```

### StringBuilder vs String

반복 연결에는 `StringBuilder`를 쓴다. `+` 연산은 내부적으로 매번 새 객체를 생성한다.

```java
StringBuilder sb = new StringBuilder();
sb.append("Hello");
sb.append(", ");
sb.append("World");
String result = sb.toString(); // "Hello, World"
```

`StringBuffer`는 `StringBuilder`와 같지만 스레드 안전(thread-safe)하다. 단일 스레드에서는 `StringBuilder`가 빠르다.

## 흔한 오해와 함정

**오해 1: `String`은 기본 타입(primitive)이다**
아니다. `String`은 클래스다. 다만 리터럴 문법(`"hello"`)으로 편하게 만들 수 있어 기본 타입처럼 보인다.

**오해 2: `null.equals("hello")`로 안전하게 비교할 수 있다**
`null`에서 메서드를 호출하면 `NullPointerException`이 발생한다. 안전한 패턴은 `"hello".equals(str)` (리터럴을 앞에) 또는 `Objects.equals(str, "hello")`다.

**오해 3: 컴파일러가 `+`를 자동으로 `StringBuilder`로 바꿔준다**
단순한 한 줄 `+`는 컴파일러가 최적화할 수 있지만, 반복문 안의 `+`는 매 반복마다 새 `StringBuilder`를 만들어 버릴 수 있다. 직접 `StringBuilder`를 쓰는 것이 안전하다.

## 실무에서 쓰는 모습

1. 사용자 입력을 받아서 비교할 때: `input.equals("admin")` (대소문자 무시는 `equalsIgnoreCase`)
2. 여러 필드를 붙여 메시지 생성: `StringBuilder`로 반복 `append`
3. `null` 안전 비교: `Objects.equals(name, "Alice")`
4. 문자열에서 부분 추출: `str.substring(0, 3)`, `str.contains("key")`

## 더 깊이 가려면

- String Pool 내부와 `intern()` 함정: [string-intern-pool-pitfalls](./string-intern-pool-pitfalls.md)
- `==` vs `equals()` 깊이 있는 설명: [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- direct equality와 case-insensitive ordering을 분리해서 보고 싶다면 [`equalsIgnoreCase()` vs `CASE_INSENSITIVE_ORDER` Bridge](./equalsignorecase-vs-case-insensitive-order-bridge.md)
- nullable `String` 정렬에서 `nullsLast`와 case-insensitive comparator를 함께 읽고 싶다면 [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)

## 면접/시니어 질문 미리보기

**Q. `String`이 불변인 이유는?**
보안(해시 키 변경 방지), 스레드 안전성, String Pool 공유 가능성 등이 이유다. 불변이기 때문에 여러 변수가 같은 리터럴을 안전하게 공유할 수 있다.

**Q. `String s = "hello"`와 `String s = new String("hello")`의 차이는?**
리터럴은 String Pool에서 기존 객체를 재사용한다. `new`는 Pool과 무관한 새 객체를 힙에 생성한다. 거의 항상 리터럴 방식이 낫다.

**Q. `StringBuilder`와 `StringBuffer` 차이는?**
`StringBuffer`는 모든 메서드가 `synchronized`라 스레드 안전하지만 느리다. `StringBuilder`는 동기화가 없어 빠르다. 단일 스레드에서는 항상 `StringBuilder`를 쓴다.

## 한 줄 정리

String은 불변이므로 내용 비교는 `equals()`, 반복 연결은 `StringBuilder`를 쓰는 것이 기본 원칙이다.
