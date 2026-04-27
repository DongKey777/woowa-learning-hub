# Primitive Descending Array Sort Bridge

> 한 줄 요약: `int[]` 같은 primitive 배열은 `Comparator`를 받는 `Arrays.sort(...)` overload가 없어서, "내림차순 comparator를 바로 넘긴다"가 아니라 **오름차순 정렬 후 뒤집기 / 뒤에서부터 읽기 / wrapper 배열로 전환** 중 하나를 고르는 것이 안전하다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: primitive descending array sort bridge basics, primitive descending array sort bridge beginner, primitive descending array sort bridge intro, java basics, beginner java, 처음 배우는데 primitive descending array sort bridge, primitive descending array sort bridge 입문, primitive descending array sort bridge 기초, what is primitive descending array sort bridge, how to primitive descending array sort bridge
> 관련 문서:
> - [Language README](../README.md)
> - [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
> - [Primitive Array Descending Search Primer](./primitive-array-descending-binarysearch-primer.md)
> - [Collection vs Collections vs Arrays 유틸리티 미니 브리지](./collection-vs-collections-vs-arrays-utility-mini-bridge.md)
> - [Comparator Utility Patterns](./java-comparator-utility-patterns.md)

> retrieval-anchor-keywords: language-java-00096, primitive descending array sort bridge, java int array descending sort comparator error, java primitive array descending sort no comparator, java Arrays.sort int[] Comparator.reverseOrder compile error, java primitive array comparator overload missing, java int array reverse order beginner, java primitive descending sort safe alternatives, java sort int array descending then reverse, java keep int array ascending read backwards, java boxed sorted reverseOrder int stream beginner, java intstream boxed reverseorder descending, java Integer[] reverseOrder sort beginner, 자바 int 배열 내림차순 정렬 comparator 안됨, 자바 primitive 배열 comparator 없는 이유, 자바 배열 내림차순 정렬 안전한 방법, 자바 int 배열 sort reverseOrder 에러, 자바 boxed sorted reverseOrder 초보자

## 먼저 잡는 mental model

초보자가 가장 자주 하는 착각은 이것이다.

- `String[]`는 `Arrays.sort(names, Comparator.reverseOrder())`가 되니까
- `int[]`도 `Arrays.sort(numbers, Comparator.reverseOrder())`가 될 것 같아 보인다

하지만 primitive 배열은 다르게 읽어야 한다.

- `int[]`, `long[]`, `double[]`는 **값 자체를 바로 담는 primitive 배열**
- `Comparator`는 **객체끼리 비교 규칙을 넘기는 도구**
- 그래서 primitive 배열용 `Arrays.sort(...)`에는 comparator overload가 없다

한 줄로 기억하면 충분하다.

> primitive 배열은 "comparator로 방향을 바꾸는 정렬"이 아니라, **기본 오름차순 API를 먼저 쓰고 표현 방식을 따로 고른다**.

## 왜 여기서 막히나

아래 코드는 beginner가 자주 시도하는 모양이다.

```java
import java.util.Arrays;
import java.util.Comparator;

int[] numbers = {3, 1, 4, 2};
Arrays.sort(numbers, Comparator.reverseOrder()); // compile error
```

이유는 단순하다.

- `Arrays.sort(T[] a, Comparator<? super T> c)`는 객체 배열용이다
- `int[]`는 `T[]`가 아니다
- 그래서 `Comparator.reverseOrder()`를 넘길 자리가 없다

즉 문제의 핵심은 "`reverseOrder()` 사용법"이 아니라
"primitive 배열과 object 배열 overload가 다르다"는 점이다.

## 안전한 선택 3가지

| 지금 필요한 것 | 가장 안전한 선택 | 왜 beginner-friendly 한가 |
|---|---|---|
| 그냥 내림차순 결과만 한 번 만들고 싶다 | 오름차순 정렬 후 직접 뒤집기 | primitive 배열 그대로 유지된다 |
| 검색도 같이 써야 한다 | 오름차순으로 유지하고 뒤에서부터 읽기 | `binarySearch` 전제를 안 깨뜨린다 |
| comparator 규칙이 꼭 필요하다 | `Integer[]` 같은 wrapper 배열로 전환 | `Comparator.reverseOrder()`를 그대로 쓸 수 있다 |

## 선택지 1. 오름차순 정렬 후 직접 뒤집기

내림차순 실배열이 필요하지만 primitive 배열을 유지하고 싶다면 이 방법이 가장 직선적이다.

```java
import java.util.Arrays;

int[] numbers = {3, 1, 4, 2};
Arrays.sort(numbers); // [1, 2, 3, 4]

for (int left = 0, right = numbers.length - 1; left < right; left++, right--) {
    int temp = numbers[left];
    numbers[left] = numbers[right];
    numbers[right] = temp;
}

System.out.println(Arrays.toString(numbers)); // [4, 3, 2, 1]
```

이 방식은 안전하지만, 검색까지 같이 쓰는 경우에는 주의가 필요하다.

- 배열 모양은 내림차순이 된다
- 하지만 `Arrays.binarySearch(numbers, key)`는 여전히 오름차순 전제를 기대한다

그래서 "정렬만"이 목적일 때 더 잘 맞는다.

## 선택지 2. 오름차순으로 유지하고 뒤에서부터 읽기

검색이나 삽입 위치 해석까지 같이 필요하면 이쪽이 더 안전하다.

```java
import java.util.Arrays;

int[] numbers = {3, 1, 4, 2};
Arrays.sort(numbers); // [1, 2, 3, 4]

for (int i = numbers.length - 1; i >= 0; i--) {
    System.out.print(numbers[i] + " ");
}
// 4 3 2 1
```

이 패턴의 장점은 명확하다.

- 정렬은 표준 primitive API 그대로 쓴다
- 검색도 `Arrays.binarySearch(numbers, key)`를 그대로 쓴다
- 화면이나 출력에서만 내림차순처럼 읽으면 된다

즉 "데이터 저장 순서"와 "보여 주는 순서"를 분리하는 방식이다.

검색까지 얽혀 있으면 자세한 설명은 [Primitive Array Descending Search Primer](./primitive-array-descending-binarysearch-primer.md)로 이어서 보면 된다.

## 선택지 3. `Integer[]`로 바꿔 comparator를 쓴다

정말로 comparator 기반 정렬 규칙이 필요하면 wrapper 배열로 가는 편이 낫다.

```java
import java.util.Arrays;
import java.util.Comparator;

Integer[] numbers = {3, 1, 4, 2};
Arrays.sort(numbers, Comparator.reverseOrder());

System.out.println(Arrays.toString(numbers)); // [4, 3, 2, 1]
```

이 방식은 이런 상황에 어울린다.

- `Comparator.reverseOrder()`를 바로 쓰고 싶다
- 나중에 `null` 정책이나 다른 comparator 규칙도 붙일 수 있어야 한다
- primitive 유지보다 규칙 설명이 더 중요하다

다만 초보자 기준에서는 먼저 기억할 점이 있다.

- `Integer[]`는 `int[]`와 다른 타입이다
- boxing이 들어간다
- "숫자 배열 내림차순 한 번" 정도라면 primitive + 뒤집기가 더 단순할 수 있다

## mini bridge. reverse loop와 `boxed().sorted(reverseOrder())`는 언제 갈리나

초보자가 자주 보는 우회 코드는 이 모양이다.

```java
import java.util.Comparator;
import java.util.stream.IntStream;

int[] numbers = {3, 1, 4, 2};

int[] descending = IntStream.of(numbers)
        .boxed()
        .sorted(Comparator.reverseOrder())
        .mapToInt(Integer::intValue)
        .toArray();
```

결과는 맞게 나오지만, beginner 기준에서는 먼저 "문제 하나를 풀기 위해 타입 왕복이 늘어났나?"를 보면 된다.

| 비교 포인트 | `Arrays.sort(numbers)` 후 reverse loop | `boxed().sorted(reverseOrder())` |
|---|---|---|
| 처음 읽을 때 | "오름차순 정렬 후 거꾸로 읽거나 뒤집는다" | "객체로 감싼 뒤 comparator 정렬하고 다시 primitive로 푼다" |
| mental model | primitive 배열 API 안에서 끝난다 | stream + boxing + comparator + unboxing이 한 번에 들어온다 |
| beginner에게 쉬운 상황 | 배열 정렬과 반복문을 같이 복습할 때 | 이미 stream pipeline을 배우고 있고 새 결과 배열이 필요할 때 |
| beginner에게 헷갈리는 지점 | swap loop 인덱스 실수만 조심하면 된다 | 왜 `boxed()`가 필요한지, 왜 다시 `mapToInt(...)` 하는지 자주 막힌다 |

짧게 판단하면 이렇다.

- **기본 답안**이 필요하면 `int[]`를 오름차순 정렬한 뒤 reverse loop 쪽이 더 단순하다.
- 이미 stream 흐름 안에서 필터링, 매핑, 수집을 같이 하고 있다면 `boxed().sorted(reverseOrder())`가 문맥상 자연스러울 수 있다.
- 단순히 "내림차순 한 번" 때문에 stream detour를 택하면, 초보자에게는 정렬보다 타입 변환 설명이 더 커질 때가 많다.

즉 이 우회는 "불가능한 방법"이 아니라, **stream 문맥이 이미 있을 때는 도움 될 수 있지만 배열 primer의 첫 해답으로는 설명 비용이 더 큰 방법**이라고 보면 된다.

## 초보자가 자주 헷갈리는 지점

- `Collections.reverseOrder()`나 `Comparator.reverseOrder()`는 primitive 배열을 직접 정렬해 주지 않는다.
- `Arrays.sort(int[], comparator)` overload가 없는 것이지, 내가 import를 빠뜨린 것이 아니다.
- `Arrays.sort(numbers)` 뒤 직접 뒤집는 것과, 처음부터 comparator로 정렬하는 것은 같은 API 흐름이 아니다.
- 검색까지 필요하면 배열을 내림차순 실배열로 바꾸는 순간 `Arrays.binarySearch(...)` 사용 감각도 달라진다.
- `stream().boxed().sorted(Comparator.reverseOrder())` 같은 우회 방법도 가능하지만, beginner primer의 기본 답으로는 `int[]` 그대로 유지하는 쪽이 더 단순하다.

## 빠른 선택 체크리스트

- primitive 배열인지 먼저 확인한다: `int[]` / `long[]` / `double[]`
- comparator를 넘기려는 순간 object 배열 overload인지 먼저 의심한다
- 검색이 필요 없으면 `Arrays.sort(...)` 후 뒤집기를 고려한다
- 검색이 필요하면 오름차순 유지 + 뒤에서부터 읽기를 먼저 떠올린다
- comparator 규칙 자체가 중요하면 `Integer[]` 같은 wrapper 배열 전환을 검토한다

## 한 줄 정리

primitive 배열 내림차순 정렬의 핵심은 "`Comparator`를 어디에 넘기지?"가 아니라, **primitive 배열에는 그 overload가 없으므로 오름차순 정렬을 기준으로 뒤집기/역방향 읽기/wrapper 전환 중 하나를 고르는 것**이다.
