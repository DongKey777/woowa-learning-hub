# Java 스트림과 람다 입문

> 한 줄 요약: 람다는 익명 함수를 간결하게 쓰는 문법이고, 스트림은 컬렉션을 filter/map/reduce 파이프라인으로 처리하는 선언적 API다.

**난이도: 🟢 Beginner**

관련 문서:

- [executor-sizing-queue-rejection-policy](./executor-sizing-queue-rejection-policy.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- [language 카테고리 인덱스](../README.md)
- [Spring IoC 컨테이너와 DI](../../spring/ioc-di-container.md)

retrieval-anchor-keywords: java stream basics, java lambda basics, 스트림 입문, 람다 입문, functional interface basics, java filter map reduce, stream pipeline beginner, java stream sorted comparator, stream sorted comparator chain, java list sort vs stream sorted, java sorted stream original list unchanged, method reference basics, java 8 stream beginner, 스트림 어떻게 쓰나요, java lambda syntax, 람다식 처음, collector basics

## 핵심 개념

Java 8 이전에는 리스트에서 특정 조건의 요소를 추출하려면 for 루프, if 조건, 임시 리스트를 모두 직접 작성해야 했다. 스트림 API는 이를 `filter`, `map`, `collect` 한 줄 파이프라인으로 표현하게 해준다.

람다는 스트림에서 "조건"이나 "변환 함수"를 간결하게 전달하는 문법이다. `(x) -> x > 0` 같은 표현식이 람다다.

입문자가 어렵게 느끼는 이유는 함수형 프로그래밍 개념이 낯설기 때문이다. "메서드를 값처럼 넘긴다"는 감각을 잡으면 나머지는 따라온다.

## 한눈에 보기

```
for 루프 방식:
List<String> result = new ArrayList<>();
for (String name : names) {
    if (name.startsWith("김")) {
        result.add(name.toUpperCase());
    }
}

스트림 방식:
List<String> result = names.stream()
    .filter(name -> name.startsWith("김"))
    .map(String::toUpperCase)
    .collect(Collectors.toList());
```

두 코드는 결과가 같다. 스트림은 "무엇을"에 집중하고, for 루프는 "어떻게"에 집중한다.

## 상세 분해

### 람다 문법

```java
// 파라미터 하나, 반환 있음
Function<String, Integer> length = s -> s.length();

// 파라미터 둘, 반환 있음
BinaryOperator<Integer> add = (a, b) -> a + b;

// 블록 본문 (여러 줄)
Function<String, String> process = s -> {
    String trimmed = s.trim();
    return trimmed.toUpperCase();
};
```

`->` 왼쪽은 파라미터, 오른쪽은 본문이다.

### 스트림 파이프라인 세 단계

1. **소스**: `list.stream()`, `Arrays.stream(arr)`
2. **중간 연산** (게으른 연산): `filter`, `map`, `sorted`, `distinct`
3. **최종 연산** (실제 실행 트리거): `collect`, `forEach`, `count`, `findFirst`

```java
long count = employees.stream()
    .filter(e -> e.getSalary() > 3000)   // 중간
    .map(Employee::getName)               // 중간
    .distinct()                           // 중간
    .count();                             // 최종 (여기서 실행됨)
```

### 메서드 참조

람다가 기존 메서드를 그대로 호출하는 경우 더 짧게 쓸 수 있다.

```java
// 람다            → 메서드 참조
s -> s.toUpperCase()   → String::toUpperCase
s -> System.out.println(s) → System.out::println
```

## 흔한 오해와 함정

**오해 1: 스트림은 항상 for 루프보다 빠르다**
단순 단일 루프에서는 for 루프가 더 빠를 수 있다. 스트림의 장점은 가독성과 병렬 처리 전환(`parallelStream()`)이지 무조건적인 성능 우위가 아니다.

**오해 2: 스트림을 여러 번 쓸 수 있다**
스트림은 한 번 최종 연산이 실행되면 소비된다. 재사용하려면 다시 `stream()`을 호출해야 한다.

**오해 3: 람다 안에서 바깥 변수를 마음대로 바꿀 수 있다**
람다가 캡처하는 외부 변수는 effectively final이어야 한다. 즉 람다가 사용하는 지역 변수는 이후에 값을 바꾸면 컴파일 오류가 난다.

## 실무에서 쓰는 모습

Spring 프로젝트에서 DTO 변환, 필터링, 집계를 스트림으로 처리하는 것이 일반적이다.

1. JPA로 조회한 `List<User>`를 스트림으로 변환
2. `filter`로 활성 사용자만 추리고
3. `map`으로 `UserDto`로 변환
4. `collect(Collectors.toList())`로 결과 수집

이 흐름이 읽히지 않으면 PR 리뷰에서 스트림 코드를 분석하기 어렵다.

## 더 깊이 가려면

- `List.sort(...)`와 `stream.sorted(...)`에 같은 comparator chain을 재사용하는 감각은 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- `Comparator.comparingInt`, `thenComparing`, `reversed` 조립법은 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- 스트림과 스레드 풀의 관계, `parallelStream` 위험은 [executor-sizing-queue-rejection-policy](./executor-sizing-queue-rejection-policy.md)
- 스트림에서 자주 쓰이는 Optional 패턴은 [language README](../README.md)

## 면접/시니어 질문 미리보기

**Q. 스트림 중간 연산이 게으르다(lazy)는 게 무슨 뜻인가?**
최종 연산이 호출되기 전까지 중간 연산은 실행되지 않는다. `filter`와 `map`을 체인해도 `collect` 없이는 아무것도 처리되지 않는다.

**Q. `collect(Collectors.toList())`와 `toList()`(Java 16+)의 차이는?**
Java 16+의 `Stream.toList()`는 불변 리스트를 반환한다. `Collectors.toList()`는 수정 가능한 리스트를 반환한다.

**Q. 람다와 익명 클래스의 차이는?**
람다는 `@FunctionalInterface` 하나를 구현할 때만 쓸 수 있다. `this`가 바깥 클래스를 가리킨다는 점도 다르다. 람다는 클래스를 새로 만들지 않아 가볍다.

## 한 줄 정리

람다는 함수를 값처럼 전달하는 문법이고, 스트림은 그 람다를 활용해 컬렉션을 선언적 파이프라인으로 처리하는 API다.
