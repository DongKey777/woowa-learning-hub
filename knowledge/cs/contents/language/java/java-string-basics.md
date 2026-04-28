# Java String 기초

> 한 줄 요약: String은 불변 객체라서 값이 같아 보여도 `==`는 객체 비교가 되고, 문자열 내용 비교는 `equals()`로 해야 하며, 반복 연결에는 `StringBuilder`가 기본 선택이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [string-intern-pool-pitfalls](./string-intern-pool-pitfalls.md)
- [`equalsIgnoreCase()` vs `CASE_INSENSITIVE_ORDER` Bridge](./equalsignorecase-vs-case-insensitive-order-bridge.md)
- [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
- [Hash Table Basics](../data-structure/hash-table-basics.md)
- [language 카테고리 인덱스](../README.md)
- [Java 불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

retrieval-anchor-keywords: java string basics, java string == vs equals, string comparison beginner, string equals beginner, 문자열 비교 방법, 문자열 비교 == equals 차이, 자바 문자열 비교 equals, string 왜 equals 써야 하나요, string == 왜 false, string 같은데 == false, 문자열 같은데 왜 false, 문자열 비교 왜 안돼요, 문자열 equals 뭐예요, string comparison what is, 자바 문자열 기초

## 핵심 개념

Java의 `String`은 한 번 만들어지면 내용이 바뀌지 않는 **불변(immutable)** 객체다. `str = str + "world"` 처럼 보여도 원래 문자열이 바뀌는 게 아니라 새 `String` 객체가 생기고 참조가 교체된다.

입문자가 가장 자주 저지르는 실수 두 가지가 있다. 첫째, `"왜 문자열이 같은데 `==`는 false지?"` 상태에서 문자열 내용을 `==`로 비교하는 것. 둘째, 반복문 안에서 `+`로 문자열을 이어 붙이는 것. 첫 번째는 결과가 틀리고, 두 번째는 성능이 나빠진다.

질문을 더 넓게 보면 이 문서는 `String` 버전의 `==` vs `equals()` 입문 문서다. "`문자열 비교가 왜 안 돼요`", "`String equals가 뭐예요`", "`같아 보이는데 왜 false예요`"처럼 들어오면 먼저 여기서 문자열 증상을 자르고, 그다음 [Java Equality and Identity Basics](./java-equality-identity-basics.md)로 넘어가서 문자열 밖의 객체 비교까지 같은 규칙으로 확장하면 된다.

## 한눈에 보기

| 지금 묻는 질문 | 먼저 쓸 도구 | 이유 |
|---|---|---|
| 문자열 내용이 같은가 | `equals()` | `String`은 참조형이라 내용 비교를 `==`가 보장하지 않는다 |
| 정말 같은 `String` 객체인가 | `==` | identity 질문일 때만 맞는 도구다 |
| 대소문자 무시하고 같은가 | `equalsIgnoreCase()` | `"abc"`와 `"ABC"`를 같은 입력으로 볼 때 쓴다 |
| 문자열을 반복해서 이어 붙이는가 | `StringBuilder` | `+`는 반복문에서 새 `String`을 계속 만든다 |

입문 단계에서는 `"같은 문자열인가"`와 `"같은 객체인가"`를 먼저 분리하면 대부분의 첫 비교 버그를 바로 자를 수 있다.

문장을 더 직접적으로 바꾸면 아래처럼 읽으면 된다.

| 학습자 발화 | 바로 떠올릴 규칙 | 다음 다리 |
|---|---|---|
| `"문자열 비교가 왜 안 돼요"` | 내용 비교면 `equals()` | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| `"String 같은데 왜 false예요"` | `==`가 객체 비교인지 먼저 본다 | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| `"String equals가 뭐예요"` | 문자열 값 비교 기본 도구다 | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |

이 세 문장은 [Java Equality and Identity Basics](./java-equality-identity-basics.md)의 문자열 증상 표에서도 같은 표현으로 다시 이어진다. 여기서 `String` 로컬 규칙을 먼저 자르고, equality primer에서 참조형 일반 규칙으로 넓히는 양방향 브리지라고 생각하면 된다.

## 코드로 보는 예시

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

위 예시에서 초보자가 먼저 가져갈 한 줄은 이것이다.

- `a == c`가 `false`여도 `"hello"`라는 **내용**은 같다.
- `a == b`가 우연히 `true`여도, 문자열 비교를 `==`로 해도 된다는 뜻은 아니다.
- 문자열 비교 버그를 줄이는 기본값은 항상 `equals()`다.

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

이 문장을 더 실전적으로 바꾸면 아래처럼 기억하면 된다.

- `"문자열이 같은가?"`를 묻는다 -> `equals()`
- `"정말 같은 객체를 같이 보고 있나?"`를 묻는다 -> `==`
- `==`가 가끔 `true`라고 해서 문자열 비교 기본값이 바뀌는 것은 아니다

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

**오해 0: 문자열 비교는 `==`로 해도 가끔 되니까 써도 된다**
리터럴은 String Pool 덕분에 `==`가 `true`로 보일 수 있다. 하지만 `new String(...)`, 외부 입력, 메서드 반환값이 섞이면 바로 깨진다. 문자열 내용 비교의 기본값은 `equals()`다.

**오해 1: `String`은 기본 타입(primitive)이다**
아니다. `String`은 클래스다. 다만 리터럴 문법(`"hello"`)으로 편하게 만들 수 있어 기본 타입처럼 보인다.

**오해 2: `null.equals("hello")`로 안전하게 비교할 수 있다**
`null`에서 메서드를 호출하면 `NullPointerException`이 발생한다. 안전한 패턴은 `"hello".equals(str)` (리터럴을 앞에) 또는 `Objects.equals(str, "hello")`다.

**오해 3: 컴파일러가 `+`를 자동으로 `StringBuilder`로 바꿔준다**
단순한 한 줄 `+`는 컴파일러가 최적화할 수 있지만, 반복문 안의 `+`는 매 반복마다 새 `StringBuilder`를 만들어 버릴 수 있다. 직접 `StringBuilder`를 쓰는 것이 안전하다.

## 실무에서 쓰는 모습

1. 사용자 입력을 받아서 비교할 때: `"admin".equals(input)` 또는 `Objects.equals(input, "admin")`
2. 여러 필드를 붙여 메시지 생성: `StringBuilder`로 반복 `append`
3. `null` 안전 비교: `Objects.equals(name, "Alice")`
4. 문자열에서 부분 추출: `str.substring(0, 3)`, `str.contains("key")`

## 더 깊이 가려면

- String Pool 내부와 `intern()` 함정: [string-intern-pool-pitfalls](./string-intern-pool-pitfalls.md)
- `==` vs `equals()`를 문자열 밖의 객체 비교까지 넓혀 보고 싶다면: [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- "`문자열 비교가 왜 안 돼요`"에서 "`그럼 객체 비교 전체 규칙은 뭐예요`"로 확장하고 싶다면: [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- direct equality와 case-insensitive ordering을 분리해서 보고 싶다면 [`equalsIgnoreCase()` vs `CASE_INSENSITIVE_ORDER` Bridge](./equalsignorecase-vs-case-insensitive-order-bridge.md)
- nullable `String` 정렬에서 `nullsLast`와 case-insensitive comparator를 함께 읽고 싶다면 [Nullable String Comparator Bridge](./nullable-string-comparator-bridge.md)
- `"문자열도 결국 hash 기반 컬렉션에서 어떻게 비교되나?"`가 궁금하면: [Hash Table Basics](../data-structure/hash-table-basics.md)

## 면접/시니어 질문 미리보기

**Q. `String`이 불변인 이유는?**
보안(해시 키 변경 방지), 스레드 안전성, String Pool 공유 가능성 등이 이유다. 불변이기 때문에 여러 변수가 같은 리터럴을 안전하게 공유할 수 있다.

**Q. `String s = "hello"`와 `String s = new String("hello")`의 차이는?**
리터럴은 String Pool에서 기존 객체를 재사용한다. `new`는 Pool과 무관한 새 객체를 힙에 생성한다. 거의 항상 리터럴 방식이 낫다.

**Q. `StringBuilder`와 `StringBuffer` 차이는?**
`StringBuffer`는 모든 메서드가 `synchronized`라 스레드 안전하지만 느리다. `StringBuilder`는 동기화가 없어 빠르다. 단일 스레드에서는 항상 `StringBuilder`를 쓴다.

## 한 줄 정리

String은 불변 객체이므로 `"문자열이 같은가?"`는 `equals()`, `"같은 객체인가?"`는 `==`, 반복 연결은 `StringBuilder`로 읽는 것이 기본 원칙이다.
