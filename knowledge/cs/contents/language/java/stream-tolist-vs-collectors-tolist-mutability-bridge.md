# `Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge

> 한 줄 요약: `sorted(...)`는 순서를 정하고, `toList()`/`Collectors.toList()`는 결과 리스트 계약을 정한다. 초보자 기준으로는 `Stream.toList()`를 "읽기 전용 결과", 수정 가능한 결과가 필요할 때는 `toCollection(ArrayList::new)`를 명시하는 식으로 구분하면 가장 덜 헷갈린다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: stream tolist vs collectors tolist mutability bridge basics, stream tolist vs collectors tolist mutability bridge beginner, stream tolist vs collectors tolist mutability bridge intro, java basics, beginner java, 처음 배우는데 stream tolist vs collectors tolist mutability bridge, stream tolist vs collectors tolist mutability bridge 입문, stream tolist vs collectors tolist mutability bridge 기초, what is stream tolist vs collectors tolist mutability bridge, how to stream tolist vs collectors tolist mutability bridge
> 관련 문서:
> - [Language README](../README.md)
> - [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
> - [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
> - [`List.copyOf(...)` vs `stream.toList()` 읽기 전용 스냅샷 브리지](./list-copyof-vs-stream-tolist-readonly-snapshot-bridge.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

> retrieval-anchor-keywords: language-java-00070, stream result mutability bridge, java Stream.toList beginner, java Collectors.toList beginner, stream toList vs collectors toList, java stream toList unmodifiable, java collectors toList mutability, collectors toList no guarantees, stream sorted toList unsupportedoperationexception, beginner sorting pipeline result list, java sorted stream result mutability, collect toCollection ArrayList, new ArrayList stream toList, stream toList vs toCollection ArrayList, java stream read only list, java stream mutable result list, toList collectors toList ArrayList choice table, stream result collection decision table, java stream list collection choice beginner

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [먼저 이 표로 고르기](#먼저-이-표로-고르기)
- [정렬과 결과 리스트는 다른 문제다](#정렬과-결과-리스트는-다른-문제다)
- [가장 흔한 beginner sorting pipeline](#가장-흔한-beginner-sorting-pipeline)
- [`Stream.toList()`: 읽기 전용 결과로 받기](#streamtolist-읽기-전용-결과로-받기)
- [`Collectors.toList()`: 그냥 List로 모으기](#collectorstolist-그냥-list로-모으기)
- [정말 수정 가능한 결과가 필요하면](#정말-수정-가능한-결과가-필요하면)
- [한 장 비교 표](#한-장-비교-표)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 잡을 mental model

초보자가 가장 많이 섞어 생각하는 두 질문은 사실 서로 다르다.

- `sorted(...)`는 "어떤 순서로 줄 세울까?"를 정한다.
- `toList()`나 `collect(...)`는 "그 결과를 어떤 리스트 계약으로 받을까?"를 정한다.

즉 아래 두 코드는 정렬 규칙은 같지만, **결과 리스트를 어떻게 다룰 수 있는지**가 다를 수 있다.

```java
students.stream()
        .sorted(byScoreDesc)
        .toList();

students.stream()
        .sorted(byScoreDesc)
        .collect(Collectors.toList());
```

정렬과 결과 컨테이너를 분리해서 보면 갑자기 훨씬 단순해진다.

> `sorted(...)`는 순서 문제이고, `toList()` vs `Collectors.toList()`는 결과 리스트 계약 문제다.

## 먼저 이 표로 고르기

초보자라면 세 API를 길게 비교하기 전에, 아래 표를 기본 선택표로 잡아도 충분하다.

| 지금 필요한 것 | 먼저 떠올릴 선택 | 이유 |
|---|---|---|
| "정렬/필터 결과를 읽기만 할 것 같다" | `toList()` | 읽기 전용 결과라는 의도가 가장 바로 보인다 |
| "기존 코드가 이미 `collect(...)` 스타일로 통일돼 있다" | `Collectors.toList()` | collector 흐름을 맞출 수 있다. 다만 수정 가능 여부는 기대하지 않는다 |
| "결과에 `add/remove/sort`를 할 것이다" | `Collectors.toCollection(ArrayList::new)` | 수정 가능한 `ArrayList`가 필요하다는 의도를 코드에 직접 쓴다 |

한 줄 브리지로 줄이면 이렇다.

> 기본값은 `toList()`, collector 스타일 유지가 목적이면 `Collectors.toList()`, 수정 가능성이 목적이면 `toCollection(ArrayList::new)`.

## 정렬과 결과 리스트는 다른 문제다

예를 들어 점수 높은 순으로 학생 목록을 보고 싶다고 하자.

```java
import java.util.Comparator;

record Student(String name, int score) {}

Comparator<Student> byScoreDesc =
        Comparator.comparingInt(Student::score).reversed();
```

이제 고민할 질문은 두 개다.

1. 점수 내림차순으로 정렬할까?
2. 정렬된 결과를 나중에 수정할 수 있어야 할까?

첫 번째 질문은 `sorted(byScoreDesc)`가 답한다.
두 번째 질문은 `toList()`인지, `Collectors.toList()`인지, 아니면 `toCollection(ArrayList::new)`인지가 답한다.

## 가장 흔한 beginner sorting pipeline

처음 배우는 단계에서는 보통 아래 세 모양이 자주 나온다.

```java
List<Student> ranking1 = students.stream()
        .sorted(byScoreDesc)
        .toList();

List<Student> ranking2 = students.stream()
        .sorted(byScoreDesc)
        .collect(Collectors.toList());

List<Student> ranking3 = students.stream()
        .sorted(byScoreDesc)
        .collect(Collectors.toCollection(ArrayList::new));
```

세 코드 모두 "정렬된 결과를 리스트로 받는다"는 점은 같다.
차이는 **그 리스트를 나중에 수정해도 되는지, 그리고 그 약속이 명확한지**에 있다.

## `Stream.toList()`: 읽기 전용 결과로 받기

`Stream.toList()`는 초보자가 읽을 때 의도가 가장 잘 드러나는 경우가 많다.

```java
List<Student> ranking = students.stream()
        .sorted(byScoreDesc)
        .toList();
```

이 코드를 읽는 기본 감각은 다음과 같다.

- stream pipeline 결과를 리스트로 받는다
- 그 결과 리스트는 구조를 바꾸는 연산을 지원하지 않는다
- 즉 `add`, `remove`, `sort` 같은 mutator를 호출하면 `UnsupportedOperationException`이 날 수 있다

예를 들어:

```java
List<Student> ranking = students.stream()
        .sorted(byScoreDesc)
        .toList();

ranking.add(new Student("Late", 0)); // 예외
```

초보자 기준으로는 이렇게 기억해 두면 충분하다.

> `Stream.toList()`는 "정렬된 결과를 읽기 전용 snapshot처럼 받겠다"는 쪽에 가깝다.

그래서 아래 같은 상황에 특히 잘 맞는다.

- 컨트롤러/서비스에서 정렬 결과를 바로 반환할 때
- 화면에 보여 줄 read-only 목록이 필요할 때
- 후속 코드가 결과 리스트를 수정하면 안 되는 쪽이 더 안전할 때

## `Collectors.toList()`: 그냥 List로 모으기

`Collectors.toList()`는 이름만 보면 "수정 가능한 리스트를 만든다"처럼 느껴질 수 있다.
하지만 초보자에게 더 안전한 mental model은 이쪽이다.

> `Collectors.toList()`는 "List로 모은다"는 뜻이지, "반드시 수정 가능한 ArrayList를 준다"는 약속이 아니다.

```java
List<Student> ranking = students.stream()
        .sorted(byScoreDesc)
        .collect(Collectors.toList());
```

이 코드를 읽을 때 중요한 포인트는 다음과 같다.

- 결과는 `List`다
- 구현 타입이 꼭 `ArrayList`라고 보장되지 않는다
- 수정 가능 여부도 명세상 보장되지 않는다

실전에서는 수정 가능한 리스트처럼 동작하는 구현을 자주 보게 되더라도, beginner primer에서는 그 사실을 "규칙"으로 외우는 게 오히려 위험하다.
나중에 코드 리뷰에서 "왜 여기서 수정 가능한 줄 알았지?"라는 confusion이 생기기 쉽기 때문이다.

그래서 초보자 관점의 안전한 결론은 이렇다.

- 단순히 결과를 읽기만 할 거면 `toList()`가 더 의도가 잘 보인다
- 결과를 수정할 계획이 있으면 `Collectors.toList()`에 기대지 말고 더 명시적인 방법을 쓴다

## 정말 수정 가능한 결과가 필요하면

정렬 결과에 항목을 더 붙이거나, 일부를 제거하거나, 후속 단계에서 다시 `sort(...)`해야 할 수도 있다.
그럴 때는 "수정 가능한 리스트가 필요하다"는 의도를 코드에 직접 써 주는 편이 좋다.

가장 읽기 쉬운 선택지는 보통 둘 중 하나다.

```java
List<Student> editableRanking = students.stream()
        .sorted(byScoreDesc)
        .collect(Collectors.toCollection(ArrayList::new));
```

```java
List<Student> editableRanking = new ArrayList<>(
        students.stream()
                .sorted(byScoreDesc)
                .toList()
);
```

둘 다 "결과를 수정할 것이다"라는 의도가 분명하다.

초보자용 판단 기준은 이렇게 두면 된다.

- 읽기 전용 결과면 `toList()`
- 수정 가능한 결과면 `toCollection(ArrayList::new)` 또는 `new ArrayList<>(...)`
- `Collectors.toList()`를 "mutable 버전"으로 외우지 않는다

## 한 장 비교 표

| 코드 | 초보자 mental model | mutability 계약 | 언제 자연스러운가 |
|---|---|---|---|
| `stream.sorted(...).toList()` | 정렬된 결과를 읽기 전용 리스트로 받기 | 수정 불가 | 반환용 결과, read-only view, 후속 수정이 필요 없음 |
| `stream.sorted(...).collect(Collectors.toList())` | 정렬된 결과를 그냥 `List`로 모으기 | 명세상 구체 타입/수정 가능 여부 보장 없음 | 기존 코드가 collector 스타일을 통일해서 쓸 때 |
| `stream.sorted(...).collect(Collectors.toCollection(ArrayList::new))` | 정렬된 결과를 수정 가능한 `ArrayList`로 받기 | `ArrayList`를 명시했으므로 의도 선명 | 나중에 `add/remove/sort`를 해야 할 때 |
| `new ArrayList<>(stream.sorted(...).toList())` | 읽기 전용 결과를 한 번 받은 뒤 mutable copy 만들기 | 바깥쪽 `ArrayList`는 수정 가능 | `toList()` 가독성을 유지하면서 후속 수정도 필요할 때 |

## 초보자가 자주 헷갈리는 지점

- `sorted(...)`가 원본 `students` 리스트를 바꾸는 것은 아니다. stream pipeline 안에서 정렬된 결과를 만드는 것이다.
- `toList()`가 리스트 구조를 수정 불가로 만들더라도, 안에 들어 있는 요소 객체 자체가 immutable이 되는 것은 아니다.
- 이미 있는 컬렉션을 읽기 전용 snapshot으로 고정하는 문제는 `stream.toList()`보다 `List.copyOf(...)` 쪽 질문에 가깝다.
- `Collectors.toList()`는 "가운데 선택지"처럼 보여도, 초보자 기준에서는 "mutable 보장도, read-only 보장도 하지 않는 선택"이라고 이해하는 편이 안전하다.
- `Collectors.toList()`는 `Collectors.toUnmodifiableList()`와 다르다. 이름이 비슷해 보여도 계약이 다르다.
- `Collectors.toList()`를 "항상 mutable"이라고 외우면 나중에 잘못된 일반화를 하게 된다. 수정 가능한 결과가 필요하면 `toCollection(ArrayList::new)`처럼 목적을 명시하는 편이 안전하다.
- Java 16 이전에는 `Stream.toList()`가 없으므로 예전 코드에서 `collect(...)` 패턴을 더 자주 보게 된다. 하지만 최신 코드에서 읽기 전용 결과를 표현하고 싶다면 `toList()`가 더 직관적일 수 있다.
- 이미 mutable `List` 자체를 직접 정렬하고 싶다면 stream 수집 방식보다 `List.sort(...)`가 더 자연스럽다.

## 어떤 문서를 다음에 읽으면 좋은가

- stream pipeline 자체가 아직 낯설다면 [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- 같은 comparator를 `List.sort(...)`와 `stream.sorted(...)`에 재사용하는 감각을 먼저 잡고 싶다면 [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- `List`, `Set`, `Map`의 mutability와 인터페이스 감각을 같이 정리하고 싶다면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- "읽기 전용 리스트"와 "요소 자체의 불변성"이 왜 다른지까지 이어서 보려면 [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

## 한 줄 정리

정렬 beginner pipeline에서는 `sorted(...)`가 순서를 정하고, `toList()`/`Collectors.toList()`가 결과 리스트 계약을 정한다. 기본값은 `toList()`를 읽기 전용 결과로 이해하고, 수정 가능한 결과가 필요할 때만 `toCollection(ArrayList::new)` 같은 명시적 선택으로 넘어가면 된다.
