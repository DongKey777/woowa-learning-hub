# Java Optional 입문

> 한 줄 요약: Optional은 "값이 있을 수도 없을 수도 있다"는 상태를 타입으로 표현해서, null을 직접 다루다 생기는 NullPointerException을 줄이는 컨테이너다.

**난이도: 🟢 Beginner**

관련 문서:

- [Optional / Stream / 불변 컬렉션 / 메모리 누수 패턴](./optional-stream-immutable-collections-memory-leak-patterns.md)
- [Java 예외 처리 기초](./java-exception-handling-basics.md)
- [language 카테고리 인덱스](../README.md)
- [Java 제네릭 입문](./java-generics-basics.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)

retrieval-anchor-keywords: java optional basics, optional 입문, nullpointerexception 방지, optional orelse beginner, optional ispresent beginner, optional 왜 쓰나요, optional 기초, java optional ifpresent, optional map filter beginner, null 대신 optional, 자바 옵셔널 입문, optional empty of ofnullable, 처음 배우는데 Optional, Optional 큰 그림, Optional 언제 쓰는지, Optional null 차이, Optional of ofNullable 차이, orElse orElseGet 차이, Optional get 쓰면 안 되는 이유, Optional 반환 타입 권장, Optional 필드에 쓰면 안 되는 이유, 값 없음 표현 기초

## 핵심 개념

`Optional<T>`는 값이 있거나 없을 수 있는 컨테이너 클래스다. `null`을 반환하는 대신 `Optional`을 반환하면, 호출한 쪽에서 "값이 없을 수 있다"는 사실을 타입 선언에서 알 수 있다.

입문자가 헷갈리는 지점은 `Optional`이 만능 null 방어책이 아니라는 것이다. 반환 타입으로만 쓰는 것이 의도된 용도이며, 필드나 메서드 파라미터에 쓰면 오히려 코드가 복잡해진다.

## 한눈에 보기

```
// null 직접 반환 방식 (NPE 위험)
String name = findUser(id);    // null일 수 있음
System.out.println(name.length()); // NPE 가능

// Optional 방식 (없음을 타입으로 표현)
Optional<String> name = findUser(id);
name.ifPresent(n -> System.out.println(n.length())); // 있을 때만 실행
```

## 상세 분해

### 생성 방법 세 가지

```java
Optional<String> a = Optional.of("hello");       // 값이 반드시 있을 때
Optional<String> b = Optional.empty();            // 비어 있는 Optional
Optional<String> c = Optional.ofNullable(value);  // null일 수도 있을 때
```

`Optional.of(null)`은 즉시 `NullPointerException`을 던진다. null이 들어올 수 있다면 `ofNullable`을 써야 한다.

### 값 꺼내기 — orElse / orElseGet / orElseThrow

```java
Optional<String> opt = Optional.ofNullable(getName());

String s1 = opt.orElse("기본값");             // 없으면 "기본값" 반환
String s2 = opt.orElseGet(() -> compute());   // 없으면 람다 실행 결과 반환
String s3 = opt.orElseThrow();               // 없으면 NoSuchElementException
```

`orElse`는 Optional이 비어 있든 아니든 인수를 항상 평가한다. 인수 생성 비용이 클 때는 `orElseGet`이 낫다.

### map과 filter로 변환 체인

```java
Optional<String> name = findUser(id)
    .map(User::getName)
    .filter(n -> !n.isBlank());
```

값이 있을 때만 `map`과 `filter`가 적용된다. 없으면 `Optional.empty()`가 그대로 흘러간다.

### ifPresent로 부수 효과 처리

```java
findUser(id).ifPresent(user -> log.info("사용자 접속: {}", user.getName()));
```

값이 있을 때만 람다를 실행한다. `isPresent()` + `get()` 조합보다 간결하고 안전하다.

## 흔한 오해와 함정

**오해 1: `get()`으로 꺼내면 된다**
`get()`은 비어 있으면 `NoSuchElementException`을 던진다. 반드시 `isPresent()` 확인 후 써야 하는데, 그냥 `orElse`나 `ifPresent`를 쓰는 게 더 낫다.

**오해 2: Optional을 필드에 저장해도 된다**
Optional은 직렬화(Serializable)를 구현하지 않는다. 필드에 저장하면 직렬화 오류가 나거나 의도치 않은 null 혼재가 생긴다. 반환 타입으로만 써야 한다.

**오해 3: Optional이 있으면 null 체크가 완전히 필요 없다**
Optional 자체가 null이면 똑같이 NPE가 발생한다. `Optional<T>` 변수에 null을 대입하지 않는 게 전제다.

## 실무에서 쓰는 모습

Repository 계층에서 단건 조회 결과를 Optional로 반환하고, 서비스 계층에서 처리하는 패턴이 가장 흔하다.

1. `Optional<User> userRepo.findById(Long id)` — DB에 없을 수 있음
2. 서비스: `user.orElseThrow(() -> new UserNotFoundException(id))`
3. 컨트롤러: 예외를 받아 404 응답 반환

## 더 깊이 가려면

- 메모리 누수·Stream 연계 패턴: [Optional / Stream / 불변 컬렉션 / 메모리 누수 패턴](./optional-stream-immutable-collections-memory-leak-patterns.md)
- Stream과 함께 쓰는 방법: [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)

## 면접/시니어 질문 미리보기

**Q. `orElse`와 `orElseGet`의 차이는?**
`orElse(T other)`는 항상 `other`를 평가한다. `orElseGet(Supplier<T> supplier)`는 Optional이 비어 있을 때만 Supplier를 호출한다. 인수 생성 비용이 있으면 `orElseGet`이 효율적이다.

**Q. Optional을 파라미터로 받는 메서드가 나쁜 이유는?**
호출자가 `null`이나 `Optional.empty()`를 전달하는 두 가지 방법이 생긴다. 단순히 `@Nullable`을 문서화하거나 메서드를 오버로딩하는 편이 낫다.

**Q. `Optional.flatMap`은 언제 쓰나?**
`map` 함수가 `Optional`을 반환할 때 `flatMap`으로 중첩(`Optional<Optional<T>>`)을 펼친다.

## 한 줄 정리

Optional은 null 대신 "없음"을 타입으로 표현하는 컨테이너이며, 반환 타입으로만 써야 하고 `get()` 대신 `orElse`·`ifPresent`·`map`으로 안전하게 꺼낸다.
