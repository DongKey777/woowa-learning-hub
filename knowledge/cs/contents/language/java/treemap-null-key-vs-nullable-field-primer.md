---
schema_version: 3
title: TreeMap Null Key vs Nullable Field Primer
concept_id: language/treemap-null-key-vs-nullable-field-primer
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 91
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- treemap
- null-handling
- comparator
aliases:
- TreeMap Null Key vs Nullable Field Primer
- Java TreeMap null key nullable field
- TreeMap rejects null key but nullable field okay
- comparator nullsLast TreeMap key object
- boundary null vs null key TreeMap
- 자바 TreeMap null key nullable field
symptoms:
- TreeMap에 null key를 넣는 문제와 key 객체 내부 nullable field를 comparator가 처리하는 문제를 같은 null 문제로 섞어
- floorEntry나 ceilingEntry가 null을 반환하는 boundary result를 null key 허용 정책과 혼동해
- nullable wrapper field를 comparingInt처럼 unboxing하는 unsafe comparator로 TreeMap key 정렬을 하다가 NPE를 만든다
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- language/hashmap-vs-treemap-beginner-selection-bridge
- language/nullable-wrapper-comparator-bridge
- language/java-comparator-utility-patterns
next_docs:
- language/ordered-map-null-safe-practice-drill
- language/comparator-null-reversal-primer
- data-structure/treemap-interval-entry-primer
linked_paths:
- contents/language/java/hashmap-vs-treemap-beginner-selection-bridge.md
- contents/language/java/nullable-wrapper-comparator-bridge.md
- contents/language/java/comparator-null-reversal-primer.md
- contents/language/java/ordered-map-null-safe-practice-drill.md
- contents/data-structure/backend-data-structure-starter-pack.md
confusable_with:
- language/ordered-map-null-safe-practice-drill
- language/nullable-wrapper-comparator-bridge
- language/comparator-null-reversal-primer
forbidden_neighbors: []
expected_queries:
- TreeMap은 null key를 보통 막지만 key 객체 안 nullable field는 comparator로 정렬할 수 있다는 뜻이 뭐야?
- TreeMap null key와 nullable field와 floorEntry 반환 null은 각각 어떻게 달라?
- Comparator.nullsLast로 Student.rank null을 처리하면 TreeMap key 객체는 non-null이라 가능한 이유를 설명해줘
- comparingInt로 nullable Integer field를 unboxing하면 TreeMap comparator에서 왜 NPE가 날 수 있어?
- HashMap null key와 TreeMap null key 정책 차이를 beginner 기준으로 알려줘
contextual_chunk_prefix: |
  이 문서는 TreeMap의 null key, key object 내부 nullable field, ordered lookup boundary null을 분리해 comparator null handling을 설명하는 beginner primer다.
  TreeMap null key, nullable field, Comparator.nullsLast, boundary null, ordered map 질문이 본 문서에 매핑된다.
---
# TreeMap Null Key vs Nullable Field Primer

> 한 줄 요약: `TreeMap`은 key 자체를 정렬해야 하므로 보통 `null` key를 바로 받아들이지 않지만, key 객체가 non-null이고 comparator가 내부 nullable field를 안전하게 처리하면 `null` field가 있어도 정렬할 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [Language README](../README.md)
- [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md)
- [Nullable Wrapper Comparator Bridge](./nullable-wrapper-comparator-bridge.md)
- [Comparator Null Reversal Primer](./comparator-null-reversal-primer.md)
- [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md)

retrieval-anchor-keywords: treemap null key vs nullable field, java treemap null key why, treemap rejects null key but nullable field okay, tree map comparator nullable wrapper field, comparator nullslast treemap key object, tree map null key natural ordering, 자바 treemap null key 왜 안됨, 자바 null key 와 null 필드 차이, 처음 treemap null 헷갈림, what is treemap null key, treemap nullable field beginner, ordered map null key basics

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교 표](#한-장-비교-표)
- [`null` key는 왜 막히나](#null-key는-왜-막히나)
- [예외적으로 `null` key를 받게 만들 수도 있다](#예외적으로-null-key를-받게-만들-수도-있다)
- [nullable field는 왜 정렬할 수 있나](#nullable-field는-왜-정렬할-수-있나)
- [코드로 같이 보기](#코드로-같이-보기)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

초보자는 보통 여기서 헷갈린다.

- "`TreeMap`은 `null` key를 싫어한다면서요?"
- "그런데 왜 `Comparator.nullsLast(...)`로 `rank == null`인 객체는 정렬되나요?"
- "`floorEntry(...)`가 `null`이면 이것도 같은 `null` 문제인가요?"
- "둘 다 `null` 이야기인데 뭐가 다른 거죠?"

핵심은 "`null`이 어디에 있느냐"다.

- `null`이 **key 자체**면 `TreeMap`이 비교를 시작할 대상이 없다
- `null`이 **key 객체 안 field**면 comparator가 그 field를 어떻게 다룰지 직접 정할 수 있다
- `floorEntry(...) == null`처럼 **조회 결과가 비어 있는 것**이면, key 정책이 아니라 "경계 밖이라 이웃이 없음"을 뜻한다

즉 "key가 `null`인 것"과 "key는 있는데 그 안의 field가 `null`인 것"은 완전히 같은 상황이 아니다.
그리고 ordered map API가 돌려주는 boundary-`null`까지 합치면, 초보자가 섞기 쉬운 `null`이 세 종류가 된다.

| `null`이 나온 위치 | 먼저 읽을 뜻 | 따라갈 문서 |
|---|---|---|
| `map.put(null, value)`의 key 자리 | key 자체가 비어 있음 | 이 문서 |
| `new Student("Mina", null)`의 field 자리 | key는 있고 field만 비어 있음 | 이 문서 |
| `floorEntry(...) == null` 같은 반환값 자리 | 경계 밖이라 이웃이 없음 | [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md) |

## 먼저 잡을 mental model

초보자용으로 가장 안전한 한 줄은 이것이다.

> `TreeMap`은 key 객체를 줄 세우고, comparator는 그 key 객체 안의 값을 읽어 줄 세운다.

그래서 질문을 둘로 나누면 된다.

1. key 객체 자체가 있나?
2. key 객체 안의 nullable field를 comparator가 안전하게 처리하나?

이렇게 보면 감각이 단순해진다.

- `TreeMap<Integer, String>`에 `null` key를 넣기
  - key 객체 자체가 없다
- `TreeMap<Student, String>`에서 `new Student("Mina", null)`을 key로 넣기
  - key 객체는 있다
  - 다만 `rank` field가 `null`일 뿐이다

## 한 장 비교 표

| 상황 | `TreeMap`이 실제로 비교하는 대상 | 기본 결과 |
|---|---|---|
| `map.put(null, "x")` in `TreeMap<Integer, String>` | key 자체 | 보통 실패 |
| `map.put(new Student("Mina", null), "x")` with safe comparator | `Student` 객체들 | 가능 |
| `map.put(new Student("Mina", null), "x")` with unsafe comparator like `comparingInt(Student::rank)` | `Student` 객체들, but `rank` unboxing 필요 | 실패 가능 |

여기서 중요한 건 "`TreeMap`은 `null`을 무조건 싫어한다"가 아니라, **정렬 과정에서 무엇을 어떻게 비교할 수 있느냐**다.

## `null` key는 왜 막히나

`TreeMap`은 hash bucket에 넣는 것이 아니라, key 순서대로 tree 안에 자리를 잡는다.

그래서 새 key를 넣을 때는 기존 key와 비교해야 한다.

- 이 key가 더 앞인가?
- 더 뒤인가?
- 같은 자리인가?

그런데 key 자체가 `null`이면, 보통 natural ordering이나 일반 comparator 기준으로는 이 비교를 진행할 수 없다.

```java
import java.util.Map;
import java.util.TreeMap;

Map<Integer, String> scores = new TreeMap<>();
scores.put(null, "absent"); // NullPointerException
```

초보자용으로 줄이면 이 뜻이다.

> `TreeMap`은 "`null`을 값으로 비교해서 어디에 둘지"를 기본적으로 알지 못하므로, 보통 `null` key에서 막힌다.

정확히는 JDK 문서 기준으로, `TreeMap`은 natural ordering을 쓰거나 comparator가 `null` key를 허용하지 않으면 `null` key에서 `NullPointerException`이 난다.
그래서 입문 단계에서는 "`TreeMap`은 보통 `null` key를 받지 않는다"로 기억하면 충분하다.

## 예외적으로 `null` key를 받게 만들 수도 있다

여기서 한 가지 고급 예외만 짧게 알고 넘어가면 충분하다.

> comparator가 key 자체의 `null`도 비교 규칙에 포함하면, `TreeMap`이 의도적으로 `null` key를 받게 만들 수 있다.

예를 들면:

```java
import java.util.Comparator;
import java.util.Map;
import java.util.TreeMap;

Map<Integer, String> scores = new TreeMap<>(
        Comparator.nullsFirst(Comparator.naturalOrder())
);

scores.put(null, "missing");
scores.put(10, "ten");
scores.put(20, "twenty");
```

이 경우 comparator가 "`null`은 가장 앞"이라고 직접 정했기 때문에, `null` key도 정렬 규칙 안에 들어간다.

다만 beginner 기준에서는 이렇게 구분하면 된다.

- 기본 규칙: `TreeMap`은 보통 `null` key를 받지 않는다
- 고급 예외: comparator가 key 자체의 `null`까지 명시적으로 다루면 받을 수 있다
- 현재 문서의 핵심: 그래도 "`null` key"와 "non-null key 안의 `null` field"는 여전히 다른 문제다

## nullable field는 왜 정렬할 수 있나

이번에는 key 자체가 `null`이 아니라고 가정하자.

```java
record Student(String name, Integer rank) {}
```

`new Student("Mina", null)`은 `null`이 아니다.
객체는 있고, 그 안의 `rank`만 비어 있다.

이때 comparator가 이렇게 생겼다면:

```java
Comparator<Student> byRankNullLast =
        Comparator.comparing(
                Student::rank,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).thenComparing(Student::name);
```

정렬은 이런 순서로 진행된다.

1. `TreeMap`은 non-null `Student` key 객체를 comparator에 넘긴다.
2. comparator는 `student.rank()`를 읽는다.
3. `rank`가 `null`이면 `nullsLast(...)` 규칙으로 위치를 정한다.
4. `rank`가 같으면 `name`으로 한 번 더 비교한다.

즉 여기서는 `TreeMap`이 `null` key를 직접 정렬하는 것이 아니다.
**non-null key 객체를 정렬하는데, 그 안의 nullable field 처리 규칙을 comparator가 알고 있는 것**이다.

## 코드로 같이 보기

```java
import java.util.Comparator;
import java.util.Map;
import java.util.TreeMap;

record Student(String name, Integer rank) {}

Map<Student, String> seats = new TreeMap<>(
        Comparator.comparing(
                Student::rank,
                Comparator.nullsLast(Comparator.naturalOrder())
        ).thenComparing(Student::name)
);

seats.put(new Student("Mina", 1), "front");
seats.put(new Student("Ria", null), "middle");
seats.put(new Student("Noah", 2), "back");
```

이 코드는 안전하다.

- key는 모두 `Student` 객체라서 non-null이다
- `rank`가 `null`이어도 comparator가 `nullsLast(...)`로 처리한다
- 그래서 `Ria`도 map에 들어갈 수 있다

반대로 아래 코드는 위험하다.

```java
Map<Student, String> unsafe = new TreeMap<>(
        Comparator.comparingInt(Student::rank)
);
```

왜 위험할까?

- `comparingInt`는 primitive `int` 비교 흐름이다
- `Student::rank`가 `Integer`인데 `null`이면 unboxing이 필요하다
- 그 순간 `NullPointerException`이 날 수 있다

초보자 메모는 이것만 기억하면 된다.

- key 자체 `null` 문제: `TreeMap`이 key 자리를 못 잡는다
- field `null` 문제: comparator가 처리 규칙을 갖고 있으면 된다

## 초보자 혼동 포인트

- "`Comparator.nullsLast(...)`가 있으니 `null` key도 다 받을 수 있겠네"
  - 아니다. 그 comparator가 **key 자체 타입**에 대해 `null`을 허용하도록 만들어졌는지가 별개다.
- "`floorEntry(...) == null`도 결국 `TreeMap`이 `null`을 싫어해서 생긴 거겠네"
  - 아니다. 그건 insert 규칙이 아니라 lookup 결과다. 정렬된 key 줄에서 해당 방향 이웃이 없어서 `null`이 나온 것이다.
- "`new Student(\"Ria\", null)`도 null이니까 key로 못 쓰겠네"
  - 아니다. key 객체는 존재한다. `null`인 것은 field다.
- "`TreeMap`이 field를 직접 정렬하나?"
  - 직접은 아니다. `TreeMap`은 key 객체를 comparator에 넘기고, comparator가 field를 꺼내 정렬한다.
- "`null` field가 있으면 무조건 `TreeMap`에서 못 쓰나?"
  - 아니다. `Comparator.nullsFirst(...)`나 `nullsLast(...)`처럼 field 규칙을 정하면 된다.
- "`TreeMap`은 절대 `null` key를 허용하지 않나?"
  - 초보자 문맥에서는 그렇게 기억해도 되지만, 정확히는 comparator가 key 자체의 `null`을 허용하도록 설계되면 예외가 있다.

## 빠른 체크리스트

- 지금 `null`인 것이 key 자체인지, key 안 field인지 먼저 구분했나?
- 혹시 `floorEntry`/`ceilingEntry` 반환값의 `null`까지 같은 문제로 묶고 있지는 않나?
- key 객체 자체가 `null`이면 `TreeMap` 기본 사용에서는 막힌다고 봐도 되나?
- nullable wrapper field를 정렬한다면 `comparingInt` 대신 `Comparator.comparing(..., Comparator.nullsFirst/Last(...))` 쪽을 먼저 봤나?
- `compare == 0`이 너무 쉽게 나오지 않게 tie-breaker도 붙였나?

## 한 줄 정리

`TreeMap`이 보통 거부하는 것은 "key 자체가 `null`인 경우"이고, comparator로 안전하게 다룰 수 있는 것은 "non-null key 객체 안의 nullable field"이므로, 두 상황을 같은 `null` 문제로 섞지 않는 것이 핵심이다.
