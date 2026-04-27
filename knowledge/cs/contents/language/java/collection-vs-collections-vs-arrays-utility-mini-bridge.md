# Collection vs Collections vs Arrays 유틸리티 미니 브리지

> 한 줄 요약: `Collection`은 데이터를 "담고 조작하는 인터페이스"이고, `Collections`와 `Arrays`는 각각 "컬렉션"과 "배열"을 도와주는 static 유틸리티 클래스다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)

retrieval-anchor-keywords: collection vs collections vs arrays, java collection collections arrays 차이, Collection 인터페이스 Collections 유틸 Arrays 유틸, java beginner collection api vs utility class, Arrays.asList Collections.sort 차이, java list set map collection hierarchy basics, java arrays sort binarySearch basics, Arrays.asList fixed size list, Arrays.asList add remove unsupportedoperationexception, Arrays.asList vs List.of, Arrays.asList vs new ArrayList, 자바 Collection Collections Arrays 차이, 자바 컬렉션 유틸리티 클래스 차이, 처음 배우는데 Collection Collections Arrays, 자바 Arrays.asList 함정, Arrays.asList 고정 크기 리스트

## 먼저 잡는 멘탈 모델

먼저 이름부터 끊어 보면 덜 헷갈린다.

- `Collection`: **인터페이스**. `add`, `remove`, `contains`처럼 "데이터를 직접 다루는 API"
- `Collections`: **유틸리티 클래스**. `sort`, `reverse`, `frequency`처럼 "컬렉션을 도와주는 static 메서드"
- `Arrays`: **유틸리티 클래스**. 배열(`T[]`, `int[]`)을 도와주는 static 메서드

기억법 한 줄:

- 끝에 `-s`가 붙은 `Collections`, `Arrays`는 "도구함"
- `Collection`은 "계약(인터페이스)"

## 5가지 자주 하는 작업으로 바로 비교

| 자주 하는 작업 | 먼저 떠올릴 대상 | 예시 |
|---|---|---|
| 1. 데이터 추가/삭제/존재 확인 | `Collection` API | `list.add("kim")`, `set.contains("ADMIN")` |
| 2. 컬렉션 정렬/뒤집기 | `Collections` | `Collections.sort(list)`, `Collections.reverse(list)` |
| 3. 배열 정렬/검색 | `Arrays` | `Arrays.sort(nums)`, `Arrays.binarySearch(nums, 42)` |
| 4. 배열을 리스트처럼 빠르게 보기 | `Arrays` | `Arrays.asList("a", "b")` |
| 5. 컬렉션 빈도/최댓값 계산 | `Collections` | `Collections.frequency(list, "A")`, `Collections.max(list)` |

## 작은 예제로 한 번에 보기

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

Collection<String> tags = new ArrayList<>();
tags.add("java");
tags.add("backend");
boolean hasJava = tags.contains("java"); // Collection API

List<Integer> scores = new ArrayList<>(List.of(80, 95, 90));
Collections.sort(scores);    // Collections 유틸: 컬렉션 정렬
Collections.reverse(scores); // Collections 유틸: 뒤집기

int[] ids = {30, 10, 20};
Arrays.sort(ids);                          // Arrays 유틸: 배열 정렬
int idx = Arrays.binarySearch(ids, 20);    // Arrays 유틸: 배열 검색

List<String> names = Arrays.asList("kim", "lee", "park");
```

## 초보자가 자주 헷갈리는 지점

- "`Collection.sort(...)`는 왜 없나요?"
  `Collection`은 인터페이스라 구현 도움 메서드를 거의 담지 않는다. 정렬은 `Collections.sort(list)` 또는 `List.sort(comparator)`를 쓴다.
- "`Arrays.sort(list)` 해도 되나요?"
  안 된다. `Arrays`는 배열 전용이다. `List`는 `Collections` 또는 `List.sort(...)`를 쓴다.
- "`Arrays.asList(...)` 결과는 보통 `ArrayList`인가요?"
  아니다. 고정 크기 리스트 뷰라 `add/remove`는 실패한다. 이 함정을 따로 정리한 체크리스트는 [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md).
- "`Map`도 `Collection`인가요?"
  아니다. `Map`은 별도 계층이다. (반복이 필요하면 `entrySet()`으로 본다.)

## 빠른 선택 체크리스트

- 데이터를 담고 바꾸는 동작이면 `Collection`/`List`/`Set` API
- "이미 있는 컬렉션"을 도와주는 작업이면 `Collections`
- "배열"을 다루는 작업이면 `Arrays`
- `List` 정렬은 `Collections.sort(list)` 또는 `list.sort(...)`
- 배열 정렬/검색은 `Arrays.sort(...)` + `Arrays.binarySearch(...)`

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "List/Set/Map을 언제 고르죠?" | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |
| "`Arrays.asList(...)`에서 왜 `add/remove`가 실패하죠?" | [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md) |
| "Iterable/Collection/Map 계층이 헷갈려요" | [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md) |
| "배열 정렬/검색 규칙을 더 정확히 보고 싶어요" | [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md) |

## 한 줄 정리

`Collection`은 "데이터를 다루는 계약", `Collections`는 "컬렉션 도구", `Arrays`는 "배열 도구"로 구분하면 첫 선택이 거의 틀리지 않는다.
