# Java 스트림과 람다 입문

> 한 줄 요약: 람다는 익명 함수를 간결하게 쓰는 문법이고, 스트림은 컬렉션을 filter/map/reduce 파이프라인으로 처리하는 선언적 API다.

**난이도: 🟢 Beginner**

관련 문서:

- [executor-sizing-queue-rejection-policy](./executor-sizing-queue-rejection-policy.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [`filter` vs `map` 결정 미니 카드](./stream-filter-vs-map-decision-mini-card.md)
- [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)
- [`Collectors.toMap(...)` Duplicate Key Primer](./collectors-tomap-duplicate-key-primer.md)
- [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- [language 카테고리 인덱스](../README.md)
- [Spring IoC 컨테이너와 DI](../../spring/ioc-di-container.md)

retrieval-anchor-keywords: java stream basics, java lambda basics, 스트림 입문, 람다 입문, functional interface basics, java filter map reduce, stream pipeline beginner, java stream sorted comparator, stream sorted comparator chain, java list sort vs stream sorted, java sorted stream original list unchanged, stream toList vs collectors toList, java Stream.toList beginner, java Collectors.toList mutability, stream result mutability bridge, method reference basics, java 8 stream beginner, 스트림 어떻게 쓰나요, java lambda syntax, 람다식 처음, collector basics, 자바 스트림 람다 기초, 스트림 람다 처음 배우는데, 스트림 람다 큰 그림, filter map 언제 쓰는지, for문 대신 stream 언제 쓰는지, 람다식 언제 쓰는지 기초, 메서드 참조 언제 쓰는지, stream 파이프라인 기초, for to stream migration, loop to stream migration, for문 stream 변환 예제, for문을 stream으로 바꾸기, 같은 문제 for stream 비교, stream으로 옮길 때 기준, beginner stream next step, stream으로 바꾸면 뭐가 좋아요, stream 장점 뭐예요, loop vs stream beginner, 반복문 대신 스트림 기준, for문이 더 나은 경우, stream 써도 되는 시점

## 핵심 개념

Java 8 이전에는 리스트에서 특정 조건의 요소를 추출하려면 for 루프, if 조건, 임시 리스트를 모두 직접 작성해야 했다. 스트림 API는 이를 `filter`, `map`, `collect` 한 줄 파이프라인으로 표현하게 해준다.

람다는 스트림에서 "조건"이나 "변환 함수"를 간결하게 전달하는 문법이다. `(x) -> x > 0` 같은 표현식이 람다다.

입문자가 어렵게 느끼는 이유는 함수형 프로그래밍 개념이 낯설기 때문이다. "메서드를 값처럼 넘긴다"는 감각을 잡으면 나머지는 따라온다.

## 먼저 잡을 감각

스트림은 "반복을 없애는 마법"이 아니라, **반복의 뼈대는 맡기고 내가 고를 조건과 변환만 적는 방식**이다.

- `for`는 "한 칸씩 어떻게 돈다"를 직접 적는다.
- `stream`은 "무엇을 걸러서 무엇으로 바꿀지"를 순서대로 적는다.

처음에는 `for`가 더 읽기 쉬워도 괜찮다. 같은 문제를 두 방식으로 나란히 읽으면서 `filter -> map -> collect`가 `if -> add -> 결과 모으기`와 대응된다는 감각을 잡는 것이 먼저다.

## 한눈에 보기

| 보고 싶은 것 | `for` 루프 | `stream` |
| --- | --- | --- |
| 반복 흐름 | 내가 직접 인덱스/요소를 돈다 | 컬렉션이 흐름을 제공한다 |
| 조건 걸러내기 | `if (...)` | `filter(...)` |
| 값 바꾸기 | 새 값을 계산해서 `add(...)` | `map(...)` |
| 결과 모으기 | 임시 리스트를 직접 만든다 | `collect(...)` / `toList()` |
| 초보자용 읽는 순서 | "어떻게 돌지"부터 본다 | "무엇을 남길지"부터 본다 |

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

## 같은 문제를 `for`에서 `stream`으로 옮겨 보기

문제:
"주문 목록에서 `PAID` 상태만 골라서, 고객 이름을 대문자로 바꾼 새 리스트를 만든다."

### 1. `for`로 먼저 풀기

```java
List<String> customerNames = new ArrayList<>();
for (Order order : orders) {
    if (order.getStatus() == OrderStatus.PAID) {
        customerNames.add(order.getCustomerName().toUpperCase());
    }
}
```

### 2. 같은 흐름을 `stream`으로 옮기기

```java
List<String> customerNames = orders.stream()
    .filter(order -> order.getStatus() == OrderStatus.PAID)
    .map(order -> order.getCustomerName().toUpperCase())
    .toList();
```

### 3. 한 줄씩 대응시키기

| `for`에서 하던 일 | `stream`에서 대응되는 자리 |
| --- | --- |
| `for (Order order : orders)` | `orders.stream()` |
| `if (order.getStatus() == PAID)` | `.filter(order -> order.getStatus() == OrderStatus.PAID)` |
| `customerNames.add(...)`에 넣을 값 계산 | `.map(order -> order.getCustomerName().toUpperCase())` |
| 결과 리스트에 모으기 | `.toList()` |

처음 바꿀 때는 "한 줄짜리 stream을 새로 생각한다"보다, **기존 `for` 코드에서 조건은 `filter`, 변환은 `map`, 결과 모으기는 `toList()`로 옮긴다**고 보면 덜 헷갈린다.

## `for`문 말고 `stream`은 언제 쓸까

먼저 mental model을 한 줄로 잡으면 이렇다.

> `for`는 "반복을 직접 조종"할 때, `stream`은 "조건/변환/수집을 문장처럼 나열"할 때 유리하다.

질문을 바꾸면 더 쉽다.

- "`몇 번째를 언제 멈출지`가 중요하다" -> `for`
- "`무엇을 걸러서 어떤 결과로 만들지`가 중요하다" -> `stream`

| 상황 | 먼저 떠올릴 선택 | 이유 |
| --- | --- | --- |
| `break`, `continue`, 인덱스 제어가 핵심 | `for` | 반복 흐름 자체를 직접 읽고 바꿔야 한다 |
| `filter -> map -> toList()`처럼 한 방향 변환이 핵심 | `stream` | 조건, 변환, 수집이 한 줄 흐름으로 드러난다 |
| 합계, 개수, 그룹핑처럼 "결과를 모으는 작업"이 중심 | `stream` | collector와 terminal operation으로 의도가 잘 보인다 |
| 상태값 여러 개를 동시에 갱신하거나 예외 분기가 많음 | `for` | 중간 상태와 분기 처리가 더 직접적으로 보인다 |

초보자 기준으로 `stream`으로 바꾸면 보통 좋아지는 점은 세 가지다.

- 임시 리스트를 직접 만들고 `add(...)`하는 보일러플레이트가 줄어든다.
- "무엇을 고르고 어떻게 바꾸는지"가 코드 위에서 바로 읽힌다.
- 같은 패턴을 `filter`, `map`, `sorted`, `groupingBy`로 재사용하기 쉬워진다.

반대로 아래처럼 읽히면 아직은 `for`가 더 안전하다.

- 중간에 특정 시점에서 바로 끊어야 한다.
- 루프 안에서 여러 변수 상태를 같이 추적해야 한다.
- stream 문법보다 문제 자체가 아직 더 낯설다.

반복문 자체가 아직 흔들리면 [Java 반복문과 스코프 follow-up 입문](./java-loop-control-scope-follow-up-primer.md)에서 `break`/`continue`/scope 감각을 먼저 고정한 뒤 다시 돌아오는 편이 빠르다.

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

**오해 4: stream을 쓰면 원본 리스트가 자동으로 바뀐다**
`map(...)`, `filter(...)`, `toList()`는 새 결과를 만드는 흐름이다. 원본 `orders` 자체를 바꾸는 것이 아니다. "정렬해서 원본을 바꾸고 싶다" 같은 문제는 `stream`보다 `List.sort(...)` 문서로 가는 편이 안전하다.

**오해 5: `for`를 다 stream으로 바꿔야 더 좋은 코드다**
아니다. 중간에 `break`, 복잡한 예외 처리, 여러 상태값을 한꺼번에 누적하는 로직은 `for`가 더 읽기 쉬울 수 있다. 초보자라면 "짧은 `filter`/`map`/`collect`"부터 stream으로 옮기고, 나머지는 무리해서 바꾸지 않는 편이 낫다.

**오해 6: stream으로 바꾸면 무조건 더 현대적이고 더 좋은 코드다**
아니다. stream의 장점은 "짧은 변환 파이프라인을 읽기 좋게 만든다"는 데 있다. 그래서 코드가 더 짧아졌더라도 `break`를 흉내 내려고 우회 로직이 늘거나, 람다가 너무 길어지면 오히려 beginner에게는 `for`보다 읽기 어려워질 수 있다.

## 실무에서 쓰는 모습

Spring 프로젝트에서 DTO 변환, 필터링, 집계를 스트림으로 처리하는 것이 일반적이다.

1. JPA로 조회한 `List<User>`를 스트림으로 변환
2. `filter`로 활성 사용자만 추리고
3. `map`으로 `UserDto`로 변환
4. `collect(Collectors.toList())`로 결과 수집

이 흐름이 읽히지 않으면 PR 리뷰에서 스트림 코드를 분석하기 어렵다.

## 더 깊이 가려면

- 지금도 `filter`와 `map`이 문장 단위로 헷갈리면 [`filter` vs `map` 결정 미니 카드](./stream-filter-vs-map-decision-mini-card.md)부터 짧게 보고 돌아오는 편이 가장 빠르다.
- 아직 "`for`와 `stream` 중 언제 뭘 고를지"가 더 헷갈리면 [Java 반복문과 스코프 follow-up 입문](./java-loop-control-scope-follow-up-primer.md)에서 반복 제어 감각을 먼저 고정하고 다시 돌아온다.
- 지금도 `filter`와 `map` 역할이 헷갈리면 이 문서의 `for -> stream` 미니 예제를 다시 본 뒤, 컬렉션 자체가 낯설면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)으로 먼저 돌아간다.
- `List.sort(...)`와 `stream.sorted(...)`에 같은 comparator chain을 재사용하는 감각은 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- `sorted(...)` 다음에 `toList()`와 `Collectors.toList()` 중 무엇을 고를지, 그리고 결과 리스트를 수정해도 되는지 헷갈리면 [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)
- `collect(Collectors.toMap(...))`가 왜 duplicate key에서 실패하는지, merge function을 언제 붙여야 하는지 헷갈리면 [`Collectors.toMap(...)` Duplicate Key Primer](./collectors-tomap-duplicate-key-primer.md)
- `Comparator.comparingInt`, `thenComparing`, `reversed` 조립법은 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- `null` 처리와 "값이 없을 수도 있음"이 같이 섞여 stream이 갑자기 어려워지면 [Java Optional 입문](./java-optional-basics.md)으로 넘어가는 편이 안전하다.
- 스트림과 스레드 풀의 관계, `parallelStream` 위험은 [executor-sizing-queue-rejection-policy](./executor-sizing-queue-rejection-policy.md)
- 스트림에서 자주 쓰이는 Optional 패턴은 [language README](../README.md)

## 면접/시니어 질문 미리보기

**Q. 스트림 중간 연산이 게으르다(lazy)는 게 무슨 뜻인가?**
최종 연산이 호출되기 전까지 중간 연산은 실행되지 않는다. `filter`와 `map`을 체인해도 `collect` 없이는 아무것도 처리되지 않는다.

**Q. `collect(Collectors.toList())`와 `toList()`(Java 16+)의 차이는?**
`Stream.toList()`는 수정 불가 결과 리스트를 준다. 반면 `Collectors.toList()`는 그냥 `List`로 모은다는 뜻이라 구현 타입과 수정 가능 여부가 명세상 보장되지 않는다. 나중에 결과를 꼭 수정해야 한다면 `Collectors.toCollection(ArrayList::new)`나 `new ArrayList<>(stream.toList())`처럼 의도를 명시하는 편이 안전하다.

**Q. 람다와 익명 클래스의 차이는?**
람다는 `@FunctionalInterface` 하나를 구현할 때만 쓸 수 있다. `this`가 바깥 클래스를 가리킨다는 점도 다르다. 람다는 클래스를 새로 만들지 않아 가볍다.

## 한 줄 정리

람다는 함수를 값처럼 전달하는 문법이고, 스트림은 그 람다를 활용해 컬렉션을 선언적 파이프라인으로 처리하는 API다.
