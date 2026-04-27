# `LinkedHashSet` 순서+중복 제거 미니 브리지

> 한 줄 요약: "중복은 제거해야 하는데, 처음 들어온 순서도 유지하고 싶다"면 `List`와 `Set` 사이에서 고민을 오래 끌기보다 `LinkedHashSet`을 먼저 떠올리면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)

retrieval-anchor-keywords: linkedhashset beginner, java linkedhashset 언제 쓰나, linkedhashset order dedup, java 중복 제거 순서 유지, list set linkedhashset 차이, linkedhashset insertion order beginner, list vs set order dedup requirement, java ordered set beginner, linkedhashset mental model, 처음 배우는데 linkedhashset, 자바 linkedhashset 기초, 자바 중복 제거하면서 순서 유지, 순서 유지 중복 제거 컬렉션, list set linkedhashset 선택 기준

## 먼저 잡는 멘탈 모델

먼저 요구를 짧게 번역해 보자.

- `List`: 들어온 **순서**를 그대로 들고 간다. 대신 중복도 그대로 남는다.
- `Set`: **중복 제거**가 된다. 대신 기본 `HashSet`은 순서를 믿으면 안 된다.
- `LinkedHashSet`: **중복 제거 + 넣은 순서 유지**를 같이 잡는다.

초급 기준 기억 문장은 이것 하나면 충분하다.

> "순서도 남기고, 같은 값은 한 번만 남긴다" -> `LinkedHashSet`

## 10초 비교표

| 지금 필요한 것 | 첫 선택 | 왜 이렇게 고르나 |
|---|---|---|
| 순서만 중요하고 중복은 허용 | `List` | 화면/입력 순서를 그대로 보여 줘야 함 |
| 중복 제거만 중요하고 순서는 안 중요 | `HashSet` | 같은 값이 한 번만 있으면 충분 |
| 중복 제거와 입력 순서가 둘 다 중요 | `LinkedHashSet` | 중복을 막으면서 처음 들어온 순서를 유지 |

## 작은 예제로 보기

사용자가 태그를 아래 순서로 눌렀다고 하자.

`java`, `backend`, `java`, `spring`

원하는 결과가

- 같은 태그는 한 번만 남고
- 처음 누른 순서는 유지되는 것

이라면 `LinkedHashSet`이 가장 바로 맞는다.

```java
import java.util.LinkedHashSet;
import java.util.Set;

Set<String> tags = new LinkedHashSet<>();
tags.add("java");
tags.add("backend");
tags.add("java");
tags.add("spring");

System.out.println(tags); // [java, backend, spring]
```

읽는 포인트는 두 가지다.

- 두 번째 `"java"`는 중복이라 추가되지 않는다.
- 결과 순서는 정렬이 아니라 **처음 들어온 순서**다.

## 왜 `List` 하나로 끝내면 안 되나

`List`도 순서는 잘 지킨다.
하지만 중복 제거를 자동으로 해 주지 않는다.

```java
import java.util.ArrayList;
import java.util.List;

List<String> tags = new ArrayList<>();
tags.add("java");
tags.add("backend");
tags.add("java");

System.out.println(tags); // [java, backend, java]
```

즉 `List`는 "순서 보관함"에 가깝고,
`LinkedHashSet`은 "중복 없는 순서 보관함"에 가깝다.

## 초보자가 자주 헷갈리는 포인트

- `LinkedHashSet`은 **정렬**해 주는 컬렉션이 아니다. 넣은 순서를 유지할 뿐이다. 정렬 순서가 필요하면 `TreeSet` 쪽 질문이다.
- `Set`이므로 인덱스로 `get(0)`처럼 접근하지 않는다. 순회가 중심이다.
- 화면이나 API에 `List`가 필요하면 `new ArrayList<>(linkedHashSet)`처럼 마지막에 변환하면 된다.
- "중복도 남겨야 하는데, 순서만 유지"라면 `LinkedHashSet`이 아니라 `List`가 맞다.

## 빠른 선택 체크

- "중복 없이 태그 목록을 입력 순서대로 보여 준다" -> `LinkedHashSet`
- "최근 방문 기록처럼 같은 값도 다시 보여 줘야 한다" -> `List`
- "정렬된 순서가 필요하다" -> `TreeSet` 방향으로 생각

## 한 줄 정리

`List`와 `Set` 중 하나만 억지로 고르기보다, "중복 제거 + 입력 순서 유지"가 같이 나오면 beginner 기준 첫 후보는 `LinkedHashSet`이다.
