---
schema_version: 3
title: '`List.copyOf(...)` vs `Collections.unmodifiableList(...)` vs `List.of(...)` beginner bridge'
concept_id: language/list-copyof-listof-unmodifiablelist-beginner-bridge
canonical: false
category: language
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- readonly-list-view-vs-snapshot
- defensive-copy-return-boundary
- list-copyof-vs-unmodifiablelist
aliases:
- list.copyof vs list.of vs collections.unmodifiablelist
- java readonly list beginner
- java list snapshot vs view
- java immutable list factory
- java defensive copy list
- java list.of list.copyof difference
- java readonly list basics
- 처음 배우는데 읽기 전용 리스트
- 자바 읽기 전용 리스트 차이
- 자바 unmodifiablelist 차이
- 자바 리스트 뷰와 복사본
- 자바 상수 리스트
- list copyof listof unmodifiablelist beginner bridge basics
- list copyof listof unmodifiablelist beginner bridge beginner
- list copyof listof unmodifiablelist beginner bridge intro
symptoms:
- 읽기 전용 리스트인데 원본 바꾸니 같이 바뀌어요
- copyOf랑 unmodifiableList를 같은 걸로 써도 되나요
- 상수 리스트를 만들고 싶은데 뭘 써야 할지 모르겠어요
intents:
- comparison
prerequisites:
- language/java-collections-basics
- language/java-immutable-object-basics
next_docs:
- language/list-copyof-vs-stream-tolist-readonly-snapshot-bridge
- language/mutable-element-pitfalls-list-set-primer
- language/set-of-copyof-unmodifiableset-readonly-primer
linked_paths:
- contents/language/java/java-collections-basics.md
- contents/language/java/mutable-element-pitfalls-list-set-primer.md
- contents/language/java/arrays-aslist-fixed-size-list-checklist.md
- contents/language/java/set-of-copyof-unmodifiableset-readonly-primer.md
- contents/language/java/map-of-copyof-unmodifiablemap-readonly-bridge.md
- contents/language/java/list-copyof-vs-stream-tolist-readonly-snapshot-bridge.md
- contents/language/java/java-immutable-object-basics.md
confusable_with:
- language/list-copyof-vs-stream-tolist-readonly-snapshot-bridge
- language/arrays-aslist-fixed-size-list-checklist
- language/map-of-copyof-unmodifiablemap-readonly-bridge
forbidden_neighbors: []
expected_queries:
- unmodifiableList는 복사본이 아니라 뷰라는 게 무슨 뜻이야
- List.copyOf와 List.of는 언제 다르게 써야 해?
- 읽기 전용 리스트를 반환하려면 copyOf가 맞아 unmodifiableList가 맞아
- 원본 리스트가 바뀌어도 안 따라오게 하려면 뭐 써야 해
- Java에서 상수 리스트와 snapshot 리스트를 구분하는 법
- null 요소가 있으면 어떤 팩토리가 깨져?
contextual_chunk_prefix: |
  이 문서는 Java 초보 학습자가 읽기 전용 리스트를 만들 때 `Collections.unmodifiableList(...)`, `List.copyOf(...)`, `List.of(...)`를 같은 것으로 섞지 않도록, 원본을 비추는 뷰와 분리된 스냅샷과 처음부터 봉인된 상수 목록을 연결해 구분하는 bridge다. 원본 바뀌면 같이 보이나, 복사본인지 창문인지, 반환 전에 방어적으로 끊기, 수정 못 하는데 안쪽 객체는 왜 변해, 상수 목록은 무엇으로 만들지 같은 자연어 paraphrase가 본 문서의 선택 기준에 매핑된다.
---
# `List.copyOf(...)` vs `Collections.unmodifiableList(...)` vs `List.of(...)` beginner bridge

> 한 줄 요약: 초보자 기준으로는 `Collections.unmodifiableList(...)`를 "원본을 비추는 읽기 전용 창문", `List.copyOf(...)`를 "그 순간 따로 떠 놓은 읽기 전용 복사본", `List.of(...)`를 "처음부터 읽기 전용으로 만든 상수 목록"으로 기억하면 가장 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md)
- [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md)
- [`Set.of(...)` vs `Set.copyOf(...)` vs `Collections.unmodifiableSet(...)` 미니 프라이머](./set-of-copyof-unmodifiableset-readonly-primer.md)
- [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md)
- [`List.copyOf(...)` vs `stream.toList()` 읽기 전용 스냅샷 브리지](./list-copyof-vs-stream-tolist-readonly-snapshot-bridge.md)
- [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

retrieval-anchor-keywords: list.copyof vs list.of vs collections.unmodifiablelist, java readonly list beginner, java list snapshot vs view, java immutable list factory, java defensive copy list, java list.of list.copyof difference, java readonly list basics, 처음 배우는데 읽기 전용 리스트, 자바 읽기 전용 리스트 차이, 자바 unmodifiablelist 차이, 자바 리스트 뷰와 복사본, 자바 상수 리스트, list copyof listof unmodifiablelist beginner bridge basics, list copyof listof unmodifiablelist beginner bridge beginner, list copyof listof unmodifiablelist beginner bridge intro

## 먼저 잡는 멘탈 모델

세 코드를 다 "수정 못 하는 리스트"로만 외우면 초반에 꼭 섞인다.

초보자 기준으로는 같은 목록을 건네는 방식이 셋 다 다르다고 읽는 편이 안전하다.

- `Collections.unmodifiableList(source)`: 원본 선반을 보는 창문
- `List.copyOf(source)`: 지금 선반 상태를 찍어 둔 사진
- `List.of("a", "b")`: 처음부터 봉인해서 만든 상수 카드 묶음

핵심 질문은 두 개면 충분하다.

- 원본 리스트가 따로 있나?
- 그 원본이 나중에 바뀌면 결과도 같이 바뀌어야 하나?

## 작은 계약 표

| 코드 | 초보자용 해석 | 원본 필요? | 원본이 나중에 바뀌면 결과도 바뀌나? | `null` 요소 허용? |
|---|---|---|---|---|
| `Collections.unmodifiableList(source)` | 읽기 전용 뷰 | 예 | 예 | 원본이 들고 있으면 보일 수 있음 |
| `List.copyOf(source)` | 읽기 전용 복사본 | 예 | 아니오 | 아니오 |
| `List.of("a", "b")` | 읽기 전용 상수 목록 | 아니오 | 원본 자체가 없음 | 아니오 |

이 표에서 제일 중요한 칸은 `원본이 나중에 바뀌면`이다. 여기서 `view`와 `copy`가 갈린다.

## 한 번에 보이는 예제

```java
List<String> source = new ArrayList<>();
source.add("apple");

List<String> view = Collections.unmodifiableList(source);
List<String> snapshot = List.copyOf(source);
List<String> literal = List.of("apple");

source.add("banana");

System.out.println(view);     // [apple, banana]
System.out.println(snapshot); // [apple]
System.out.println(literal);  // [apple]
```

이 예제에서 봐야 할 것은 하나다.

- `view`는 원본을 같이 본다
- `snapshot`은 원본과 분리됐다
- `literal`은 애초에 원본 없이 바로 만든다

## 읽기 전용 리스트여도 안쪽 객체는 바뀔 수 있다

여기서 초보자가 한 번 더 헷갈리는 지점이 있다.

`List.copyOf(...)`나 `Collections.unmodifiableList(...)`는 리스트 구조를 read-only로 만들 수 있다.
하지만 안에 든 value 객체가 mutable이면 그 객체 상태는 여전히 바뀔 수 있다.

```java
final class Point {
    private int x;

    Point(int x) {
        this.x = x;
    }

    void moveTo(int x) {
        this.x = x;
    }

    @Override
    public String toString() {
        return "Point{x=" + x + "}";
    }
}

Point point = new Point(1);
List<Point> snapshot = List.copyOf(List.of(point));

point.moveTo(99);

System.out.println(snapshot); // [Point{x=99}]
snapshot.add(new Point(2));   // 예외
```

이 예제에서는 두 층을 분리해서 봐야 한다.

- 리스트 구조: `add`, `remove`는 막힌다
- 요소 객체 상태: 같은 `Point`를 같이 보고 있으면 값 변경은 보일 수 있다

즉 read-only 컬렉션은 "통을 못 바꾸게 하는 것"에 가깝다.
"안의 물건까지 절대 안 바뀐다"는 뜻은 아니다.

## 언제 무엇을 고르면 쉬운가

| 지금 상황 | 추천 | 이유 |
|---|---|---|
| 상수 데이터, 테스트 데이터, 고정 메뉴를 바로 만들고 싶다 | `List.of(...)` | "처음부터 읽기 전용" 의도가 가장 잘 보인다 |
| 생성자나 반환값에서 외부 리스트와 연결을 끊고 싶다 | `List.copyOf(...)` | 읽기 전용 복사본이라 원본 변경이 새어 나오지 않는다 |
| 내부 리스트를 잠깐 읽기 전용으로만 노출하고 싶다 | `Collections.unmodifiableList(...)` | view 목적에는 맞지만 원본 보호까지 하지는 않는다 |

## 가장 많이 생기는 오해

- "`unmodifiableList`면 원본도 안전하게 안 바뀐다"

아니다. `Collections.unmodifiableList(...)`는 복사본이 아니라 wrapper다.
원본 `source`를 다른 코드가 계속 바꾸면, 그 변화가 `view`에도 보일 수 있다.

- "`List.copyOf(...)`면 요소 객체까지 깊게 복사된다"

이것도 아니다. 바뀌지 않는 것은 리스트 구조다.
요소 객체 자체가 mutable이면 그 내부 상태는 여전히 바뀔 수 있다.

- "`List.of(...)`와 `List.copyOf(...)`는 완전히 같은 역할이다"

비슷한 점은 둘 다 읽기 전용이라는 것이다.
하지만 `List.of(...)`는 값을 바로 적어 넣는 factory이고, `List.copyOf(...)`는 이미 가진 컬렉션에서 snapshot을 뜨는 도구다.

## 초보자 체크포인트

- 원본 변경이 보이면 안 되면 `Collections.unmodifiableList(...)`만으로는 부족하다
- 반환 경계 보호라면 `List.copyOf(...)`가 더 안전하다
- 상수 목록을 바로 적는 상황이면 `List.of(...)`가 가장 읽기 쉽다
- `List.of(...)`와 `List.copyOf(...)`는 `null` 요소를 허용하지 않는다
- 읽기 전용 리스트여도 안의 요소 객체까지 자동으로 불변이 되는 것은 아니다

## 한 줄 정리

`Collections.unmodifiableList(...)`는 창문, `List.copyOf(...)`는 복사본, `List.of(...)`는 상수 목록으로 기억하면 read-only view와 immutable copy와 literal factory 차이를 초보자도 빠르게 구분할 수 있다.
