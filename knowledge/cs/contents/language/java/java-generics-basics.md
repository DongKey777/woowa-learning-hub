# Java 제네릭 입문

> 한 줄 요약: 제네릭은 클래스나 메서드가 다룰 타입을 컴파일 시점에 지정해서, 캐스팅 없이 타입 안전성을 보장하는 기능이다.

**난이도: 🟢 Beginner**

관련 문서:

- [generic-type-erasure-workarounds](./generic-type-erasure-workarounds.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [language 카테고리 인덱스](../README.md)
- [Spring IoC 컨테이너와 DI](../../spring/ioc-di-container.md)

retrieval-anchor-keywords: java generics basics, 제네릭 입문, type parameter java beginner, generic class basics, generic method basics, 타입 파라미터 기초, java wildcard basics, bounded type parameter, list string vs list object, 제네릭 왜 쓰나요, unchecked cast warning, java 타입 안전성 입문

## 핵심 개념

제네릭이 없던 Java 5 이전에는 컬렉션에서 값을 꺼낼 때마다 `(String)` 같은 명시적 캐스팅이 필요했고, 타입이 맞지 않으면 런타임에서야 `ClassCastException`이 발생했다.

제네릭은 "이 컨테이너는 `String`만 담는다"고 컴파일 시점에 선언해서, 타입 불일치를 컴파일 오류로 잡는다. 입문자가 헷갈리는 부분은 꺽쇠(`<>`) 문법이 낯선 것이지, 개념 자체는 "타입을 변수처럼 쓴다"로 이해하면 된다.

## 한눈에 보기

```
제네릭 없이                     제네릭 사용
List list = new ArrayList();    List<String> list = new ArrayList<>();
list.add("hello");              list.add("hello");
String s = (String) list.get(0); String s = list.get(0); // 캐스팅 불필요
// 런타임에 ClassCastException 위험     // 컴파일 시점에 타입 오류 감지
```

## 상세 분해

### 제네릭 클래스

```java
public class Box<T> {
    private T value;

    public Box(T value) {
        this.value = value;
    }

    public T getValue() {
        return value;
    }
}

Box<String> strBox = new Box<>("hello");
Box<Integer> intBox = new Box<>(42);
String s = strBox.getValue(); // 캐스팅 없이 String 반환
```

`T`는 타입 파라미터다. `Box<String>`을 만들면 `T`가 `String`으로 치환된다.

### 제네릭 메서드

```java
public static <T> T getFirst(List<T> list) {
    return list.get(0);
}

String first = getFirst(List.of("a", "b")); // 타입 추론으로 T = String
```

메서드에도 타입 파라미터를 붙일 수 있다. 반환 타입 앞에 `<T>`를 선언한다.

### 경계 타입 파라미터

```java
public static double sum(List<? extends Number> numbers) {
    return numbers.stream().mapToDouble(Number::doubleValue).sum();
}

sum(List.of(1, 2, 3));       // Integer는 Number의 하위 타입
sum(List.of(1.5, 2.5));      // Double도 가능
```

`? extends Number`는 "Number 또는 Number의 하위 타입"을 받겠다는 뜻이다.

## 흔한 오해와 함정

**오해 1: `List<Object>`는 모든 리스트를 받을 수 있다**
`List<String>`은 `List<Object>`의 하위 타입이 아니다. 제네릭은 공변(covariant)이 아니다. `List<? extends Object>`나 `List<?>`를 써야 다양한 타입을 받을 수 있다.

**오해 2: 제네릭 타입은 런타임에도 살아있다**
Java는 타입 소거(type erasure)를 사용해 런타임에는 타입 파라미터 정보가 지워진다. `List<String>`과 `List<Integer>`는 런타임에 같은 `List`다. 이것이 `instanceof List<String>`이 안 되는 이유다.

**오해 3: `<>`(다이아몬드 연산자)와 `<?>`(와일드카드)는 같다**
다이아몬드 `<>`는 타입 추론 단축 문법이고, `<?>`는 "모르거나 어떤 타입이든"이라는 와일드카드다.

## 실무에서 쓰는 모습

Spring에서 `ResponseEntity<T>`, `Optional<T>`, `List<UserDto>` 등이 제네릭 없이는 작성이 불가능하다.

1. 서비스 계층에서 `Optional<User> findById(Long id)` 반환
2. 컨트롤러에서 `Optional<User>`를 `ResponseEntity<UserResponse>`로 변환
3. `ResponseEntity.ok(userResponse)` — 타입 파라미터가 컴파일 시점에 맞춰지므로 안전

제네릭을 이해하지 못하면 Spring 코드에서 `unchecked cast` 경고를 이해하거나 `TypeToken` 같은 패턴을 쓰기 어렵다.

## 더 깊이 가려면

- 타입 소거의 한계와 우회 방법은 [generic-type-erasure-workarounds](./generic-type-erasure-workarounds.md)
- Spring DI에서 제네릭 타입이 어떻게 활용되는지는 [Spring IoC 컨테이너와 DI](../../spring/ioc-di-container.md)

## 면접/시니어 질문 미리보기

**Q. `List<String>`과 `List<Object>`의 관계는?**
하위 타입 관계가 없다. `String`이 `Object`의 하위 타입이어도 `List<String>`은 `List<Object>`의 하위 타입이 아니다. 공변을 원하면 `List<? extends Object>`를 쓴다.

**Q. 제네릭 배열 `new T[10]`이 왜 안 되나?**
타입 소거로 런타임에 `T`가 무엇인지 알 수 없어서 JVM이 올바른 배열 타입을 생성할 수 없다. 대신 `(T[]) new Object[10]`으로 우회하거나 `ArrayList<T>`를 쓴다.

**Q. `PECS(Producer Extends, Consumer Super)`가 무엇인가?**
와일드카드 경계 규칙이다. 값을 꺼낼 때(읽기)는 `? extends T`, 값을 넣을 때(쓰기)는 `? super T`를 쓴다.

## 한 줄 정리

제네릭은 타입을 파라미터로 받아 컴파일 시점에 타입 안전성을 보장하고, 불필요한 캐스팅을 제거한다.
