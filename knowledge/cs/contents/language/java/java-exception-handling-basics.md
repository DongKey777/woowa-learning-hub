# Java 예외 처리 기초

> 한 줄 요약: 예외는 프로그램 실행 중 발생하는 비정상 상황을 표현하는 객체이고, try-catch-finally로 잡거나 throws로 위로 넘기는 두 가지 대응 방식이 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [try-with-resources와 Suppressed Exception](./try-with-resources-suppressed-exceptions.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [language 카테고리 인덱스](../README.md)
- [Spring MVC 요청 생명주기](../../spring/README.md)

retrieval-anchor-keywords: java exception basics, try catch finally beginner, checked unchecked exception, throws throw beginner, exception handling intro, java 예외처리 입문, nullpointerexception beginner, runtimeexception beginner, exception hierarchy java, what is exception java, 예외 종류 입문, java exception class hierarchy

## 핵심 개념

예외(Exception)는 프로그램이 실행되다가 의도하지 않은 상황이 발생했음을 알리는 객체다. 예를 들어 배열 범위를 벗어난 접근, null인 참조 변수의 메서드 호출, 파일을 찾지 못하는 경우 등이 이에 해당한다.

입문자가 자주 헷갈리는 지점은 "예외를 던진다(throw)"와 "예외를 잡는다(catch)"를 섞어 이해하는 것이다. 던지는 쪽은 문제를 발견한 코드이고, 잡는 쪽은 그 문제를 처리하는 코드다.

## 한눈에 보기

```
Throwable
├── Error          (JVM 수준 심각한 문제, 잡지 않아도 됨)
└── Exception
    ├── RuntimeException  (Unchecked - 컴파일러가 강제하지 않음)
    │   ├── NullPointerException
    │   ├── ArrayIndexOutOfBoundsException
    │   └── IllegalArgumentException
    └── IOException       (Checked - 반드시 처리해야 함)
        └── FileNotFoundException
```

- **Checked 예외**: 컴파일러가 `try-catch` 또는 `throws` 선언을 강제한다.
- **Unchecked 예외**: `RuntimeException` 하위. 처리 강제 없음.

## 상세 분해

### try-catch-finally

```java
try {
    int result = 10 / 0; // ArithmeticException 발생
} catch (ArithmeticException e) {
    System.out.println("0으로 나눌 수 없음: " + e.getMessage());
} finally {
    System.out.println("항상 실행됨");
}
```

- `try` 블록: 예외가 발생할 수 있는 코드
- `catch` 블록: 해당 예외를 잡아 처리
- `finally` 블록: 예외 여부 관계없이 항상 실행 (자원 정리에 사용)

### throws로 예외 위임

```java
public void readFile(String path) throws IOException {
    // 직접 처리 대신 호출자에게 넘김
}
```

메서드가 예외를 직접 처리하지 않고 호출한 쪽으로 책임을 위임할 때 `throws`를 사용한다.

### throw로 직접 던지기

```java
if (age < 0) {
    throw new IllegalArgumentException("나이는 음수일 수 없음: " + age);
}
```

조건 검증 실패 등 특정 상황에서 직접 예외를 만들어 던진다.

## 흔한 오해와 함정

**오해 1: `finally`는 return이 있어도 실행된다**
`try` 안에서 `return`을 해도 `finally`는 실행된다. 다만 `finally` 안에서 `return`을 하면 `try`의 반환값을 덮어쓰므로 `finally`에 `return`은 피해야 한다.

**오해 2: 모든 예외를 catch해야 한다**
`RuntimeException`은 잡지 않아도 컴파일 오류가 없다. 오히려 의미 없이 모든 예외를 잡으면 버그를 숨기게 된다.

**오해 3: `throws`는 예외를 처리한다**
`throws`는 처리가 아니라 위임이다. 결국 어딘가에서 잡거나 프로그램이 종료된다.

## 실무에서 쓰는 모습

가장 흔한 패턴은 서비스 계층에서 도메인 예외를 던지고, 컨트롤러 또는 글로벌 핸들러에서 응답 형태로 변환하는 흐름이다.

1. 도메인 로직에서 `throw new IllegalArgumentException("...")` 발생
2. Spring의 `@ExceptionHandler`나 `@ControllerAdvice`가 이를 잡아 HTTP 응답 코드와 메시지로 변환
3. 클라이언트는 400 Bad Request 등을 받음

이 흐름을 이해하려면 예외가 call stack을 타고 올라가는 원리를 먼저 잡아야 한다.

## 더 깊이 가려면

- 자원 자동 반납 패턴은 [try-with-resources와 Suppressed Exception](./try-with-resources-suppressed-exceptions.md)
- Spring에서 예외가 응답으로 변환되는 과정은 [Spring README](../../spring/README.md)

## 면접/시니어 질문 미리보기

**Q. Checked와 Unchecked 예외의 차이는?**
컴파일러가 처리를 강제하느냐의 차이다. Checked는 `IOException`처럼 외부 자원과 상호작용할 때 쓰고, Unchecked는 프로그래밍 오류(`NullPointerException` 등)에 쓴다.

**Q. `catch (Exception e) {}`처럼 모든 예외를 잡아도 되나?**
기술적으로는 가능하지만 나쁜 습관이다. 어떤 예외가 발생했는지 모르는 채로 넘어가면 버그를 숨기게 된다.

**Q. finally가 항상 실행된다고 했는데 예외는?**
`System.exit()` 호출이나 JVM 비정상 종료 시에는 실행되지 않을 수 있다.

## 한 줄 정리

예외는 실행 중 비정상 상황을 알리는 객체이며, try-catch로 잡거나 throws로 위임하고, Checked/Unchecked 구분이 "컴파일러 강제 여부"다.
