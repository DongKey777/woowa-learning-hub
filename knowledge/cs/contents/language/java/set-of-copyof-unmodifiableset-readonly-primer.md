# `Set.of(...)` vs `Set.copyOf(...)` vs `Collections.unmodifiableSet(...)` 미니 프라이머

> 한 줄 요약: 초보자 기준으로는 `Set.of(...)`를 "처음부터 읽기 전용으로 만든 상수 집합", `Set.copyOf(...)`를 "그 순간 따로 떠 놓은 읽기 전용 복사본", `Collections.unmodifiableSet(...)`를 "원본을 비추는 읽기 전용 창문"으로 기억하면 가장 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)
- [`List.copyOf(...)` vs `Collections.unmodifiableList(...)` vs `List.of(...)` beginner bridge](./list-copyof-listof-unmodifiablelist-beginner-bridge.md)
- [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md)
- [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md)

retrieval-anchor-keywords: set.of vs set.copyof vs collections.unmodifiableset, java readonly set beginner, java immutable set factory, unmodifiableset vs copyof, set.of duplicate exception beginner, set.copyof snapshot beginner, read-only view vs immutable set java, 처음 배우는데 읽기 전용 set, 자바 set.of 차이, 자바 불변 set, 자바 set 중복 제거 상수, what is set.of, set of copyof unmodifiableset readonly primer basics, set of copyof unmodifiableset readonly primer beginner, set of copyof unmodifiableset readonly primer intro

## 먼저 잡는 멘탈 모델

셋 다 "수정 못 하는 `Set`"처럼 보여도, 초보자 기준으로는 원본과의 관계를 먼저 나누는 편이 안전하다.

- `Collections.unmodifiableSet(source)`: 원본 집합을 비추는 창문
- `Set.copyOf(source)`: 지금 상태를 따로 떠 둔 읽기 전용 복사본
- `Set.of("a", "b")`: 처음부터 봉인해서 만든 상수 집합

핵심 질문은 두 개다.

- 원본 `Set`이 따로 남아 있나?
- 원본이 나중에 바뀌면 결과도 같이 바뀌어야 하나?

## 한눈에 보는 비교 표

| 코드 | 초보자용 해석 | 원본과 분리됨? | 원본이 바뀌면 같이 달라지나? | 중복 값 허용? |
|---|---|---|---|---|
| `Set.of("a", "b")` | 읽기 전용 상수 집합 | 예 | 원본 자체가 없다 | 아니오 |
| `Set.copyOf(source)` | 읽기 전용 복사본 | 예 | 아니오 | 원본 중복을 자동으로 하나로 본다 |
| `Collections.unmodifiableSet(source)` | 읽기 전용 뷰 | 아니오 | 예 | 원본 규칙을 그대로 따른다 |

`Set`에서는 "원본과 연결돼 있는가"에 더해 "중복을 어떻게 다루는가"도 같이 봐야 덜 헷갈린다.

## 짧은 예제로 바로 구분하기

```java
Set<String> source = new LinkedHashSet<>();
source.add("apple");

Set<String> view = Collections.unmodifiableSet(source);
Set<String> snapshot = Set.copyOf(source);
Set<String> literal = Set.of("apple", "banana");

source.add("banana");

System.out.println(view);     // [apple, banana]
System.out.println(snapshot); // [apple]
System.out.println(literal);  // [apple, banana]
```

이 예제에서 볼 포인트는 단순하다.

- `view`는 원본 변경이 보인다
- `snapshot`은 원본과 분리돼 그대로다
- `literal`은 애초에 원본 없이 바로 만든다

## `Set`에서 특히 자주 헷갈리는 점

리스트와 달리 `Set`은 중복을 허용하지 않는다. 그래서 factory를 고를 때 "읽기 전용인가"만 보면 절반만 본 것이다.

- `Set.of("a", "a")`는 중복 때문에 예외가 난다
- `Set.copyOf(listSource)`는 중복이 있으면 하나로 합쳐진 결과를 만든다
- `Collections.unmodifiableSet(source)`는 원본 `Set`이 이미 어떻게 중복을 다루는지 그대로 따른다

즉 `Set.of(...)`는 "상수 집합을 바로 적기", `Set.copyOf(...)`는 "기존 데이터를 집합 규칙으로 읽기 전용 snapshot 만들기"에 더 가깝다.

## 언제 무엇을 고르면 쉬운가

| 지금 상황 | 추천 | 이유 |
|---|---|---|
| 고정 태그, 권한 이름처럼 상수 집합을 바로 만들고 싶다 | `Set.of(...)` | 의도가 가장 짧게 드러난다 |
| 외부에서 받은 컬렉션을 읽기 전용 `Set`으로 끊어 두고 싶다 | `Set.copyOf(...)` | 원본과 분리되고 `Set` 규칙으로 정리된다 |
| 내부 `Set`을 잠깐 읽기 전용으로만 노출하고 싶다 | `Collections.unmodifiableSet(...)` | view 목적에는 맞지만 원본 보호까지 하지는 않는다 |

## 흔한 오해와 함정

- "`Collections.unmodifiableSet(...)`면 원본도 안전하게 안 바뀐다"

아니다. 읽기 전용으로 보이게 감싼 것뿐이라서, 원본 `Set`을 다른 코드가 바꾸면 결과에도 그대로 보일 수 있다.

- "`Set.copyOf(...)`는 중복이 있으면 예외가 난다"

초보자가 여기서 `Set.of(...)`와 자주 섞는다. `Set.copyOf(...)`는 이미 가진 데이터에서 `Set`을 만드는 쪽이라 중복 원소가 있으면 하나만 남긴 결과를 만든다.

- "`final Set`이면 불변이다"

이것도 아니다. `final`은 참조 재할당만 막는다. 그 안의 자료가 view인지 복사본인지, mutable한지는 따로 봐야 한다.

## 더 이어서 읽기 좋은 문서

| 지금 더 헷갈리는 질문 | 다음 문서 |
|---|---|
| "`List.of(...)`와도 같은 기준으로 보고 싶다" | [`List.copyOf(...)` vs `Collections.unmodifiableList(...)` vs `List.of(...)` beginner bridge](./list-copyof-listof-unmodifiablelist-beginner-bridge.md) |
| "`Map.of(...)`는 또 어떻게 다르지?" | [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md) |
| "`Set` 자체를 언제 쓰는지부터 다시 잡고 싶다" | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |
| "중복 제거와 순서 유지가 같이 필요하면?" | [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md) |
| "읽기 전용 컬렉션과 방어적 복사를 더 넓게 묶어 보고 싶다" | [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md) |

## 한 줄 정리

`Set.of(...)`는 상수 집합, `Set.copyOf(...)`는 읽기 전용 복사본, `Collections.unmodifiableSet(...)`는 원본 위의 읽기 전용 뷰로 기억하면 초보자도 `Set`의 immutable factory를 일관되게 고를 수 있다.
