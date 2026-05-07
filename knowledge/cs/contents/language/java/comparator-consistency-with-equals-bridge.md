---
schema_version: 3
title: Comparator Consistency With equals Bridge
concept_id: language/comparator-consistency-with-equals-bridge
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- comparator-contract
- tree-collection
- equality-ordering
aliases:
- Comparator consistency with equals
- compare zero equals mismatch
- TreeSet comparator zero
- TreeMap comparator key equality
- HashSet vs TreeSet equality
- 자바 comparator equals 일관성
symptoms:
- compare(...) == 0을 단순 정렬 동점으로만 보고 TreeSet/TreeMap에서 같은 원소나 key 자리로 취급된다는 점을 놓쳐
- record equals는 false인데 comparator가 이름만 봐서 0을 반환하면 sorted collection 결과가 hash collection과 달라지는 이유를 설명하지 못해
- comparator tie-breaker를 충분히 붙이지 않아 다른 객체가 TreeSet에서 하나로 합쳐지거나 TreeMap value가 덮어써져
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- language/java-comparable-comparator-basics
- language/collections-equality-mutable-state-foundations
next_docs:
- language/treeset-treemap-comparator-tie-breaker-basics
- language/hashset-vs-treeset-duplicate-semantics
- language/record-value-object-equality-basics
linked_paths:
- contents/language/java/hashset-vs-treeset-duplicate-semantics.md
- contents/language/java/treeset-treemap-comparator-tie-breaker-basics.md
- contents/language/java/record-value-object-equality-basics.md
- contents/language/java/map-lookup-debug-equals-hashcode-compareto-mini-bridge.md
confusable_with:
- language/hashset-vs-treeset-duplicate-semantics
- language/treeset-treemap-comparator-tie-breaker-basics
- language/record-value-object-equality-basics
forbidden_neighbors: []
expected_queries:
- Comparator compare zero와 equals false가 TreeSet TreeMap에서 어떤 문제를 만드는지 설명해줘
- HashSet은 두 개가 들어가는데 TreeSet은 하나만 남는 comparator mismatch 예제를 보여줘
- TreeMap에서 comparator가 이름만 보면 다른 id 학생 value가 덮어써지는 이유가 뭐야?
- Comparator tie breaker를 언제 붙여 equals와 더 일관되게 만들어야 해?
- compareTo 또는 comparator consistency with equals를 초보자 기준으로 알려줘
contextual_chunk_prefix: |
  이 문서는 Comparator consistency with equals를 HashSet equals/hashCode와 TreeSet/TreeMap compare == 0 기준 차이로 설명하는 beginner primer다.
  compare zero equals mismatch, TreeSet duplicate, TreeMap overwrite, record comparator mismatch, comparator tie-breaker 질문이 본 문서에 매핑된다.
---
# Comparator Consistency With `equals()` Bridge

> 한 줄 요약: `HashSet`은 `equals()`/`hashCode()`를, `TreeSet`/`TreeMap`은 `compare(...) == 0`을 더 직접적으로 보므로, comparator가 `equals()`와 어긋나면 같은 `record` 예제도 컬렉션마다 다르게 보일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)

retrieval-anchor-keywords: comparator consistency with equals, compare zero equals mismatch, treeset treemap comparator zero, hashset vs treeset equality, java record comparator mismatch, 자바 comparator equals 일관성, 처음 배우는데 comparator consistency, why treeset removes duplicate, how compare zero works, sorted collection equality mismatch, comparator tie breaker beginner, compare zero same key

## 먼저 잡을 mental model

가장 안전한 beginner 기억법은 이 두 줄이다.

- `HashSet`은 `equals()`/`hashCode()` 기준으로 같은 원소를 판단한다.
- `TreeSet`/`TreeMap`은 `compare(...) == 0`이면 같은 자리로 본다.

즉 comparator에서 `0`이 나온다는 말은 sorted collection 안에서는 단순 동점이 아니라 "같은 원소 칸" 또는 "같은 key 칸"에 더 가깝다.

## 한 화면 비교 예제

```java
record Student(long id, String name) {}

Comparator<Student> byNameOnly =
        Comparator.comparing(Student::name);

Student first = new Student(1L, "Mina");
Student second = new Student(2L, "Mina");
```

이 예제에서 기준은 갈라진다.

- `first.equals(second)`는 `false`
- `byNameOnly.compare(first, second)`는 `0`

즉 equality 기준과 ordering 기준이 서로 다른 상태다.

## 컬렉션별로 왜 결과가 갈리나

| 컬렉션 | 먼저 보는 기준 | 결과 |
|---|---|---|
| `HashSet<Student>` | `equals()`/`hashCode()` | 2개 다 들어간다 |
| `TreeSet<Student>` + `byNameOnly` | `compare(...) == 0` | 1개만 남는다 |
| `TreeMap<Student, String>` + `byNameOnly` | `compare(...) == 0` | 같은 key 자리라 값이 덮어써진다 |

핵심은 컬렉션이 이상한 것이 아니라 각 컬렉션이 자기 규칙대로 움직인다는 점이다.

## `TreeMap`이 특히 헷갈리는 이유

```java
Map<Student, String> map = new TreeMap<>(byNameOnly);
map.put(first, "front");
map.put(second, "back");

System.out.println(map.size()); // 1
System.out.println(map.get(new Student(99L, "Mina"))); // back
```

초보자는 `new Student(99L, "Mina")`가 전혀 다른 객체인데도 조회가 되는 장면에서 많이 막힌다.

이유는 단순하다.

1. `TreeMap`은 key reference보다 comparator 기준을 먼저 본다.
2. 이름만 비교하면 `"Mina"`는 모두 같은 key 자리다.
3. 그래서 두 번째 `put`이 value를 덮어쓰고, 조회도 같은 이름이면 같은 자리로 찾는다.

## 언제 tie-breaker가 필요한가

이름이 같아도 `id`가 다르면 다른 학생으로 남겨야 한다면 comparator를 끝까지 나눠야 한다.

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);
```

이제는 다음이 같이 맞춰진다.

- `compare(first, second) != 0`
- `equals()`도 `false`

즉 "다른 객체면 sorted collection에서도 다른 자리"라는 기대와 더 잘 맞는다.

## 초보자 공통 혼동

- `compare(...) == 0`을 단순 정렬 동점으로만 이해하기 쉽다.
- `record`가 `equals()`를 자동 생성하니 `TreeSet`도 같은 기준일 거라고 기대하기 쉽다.
- `HashSet`에서 잘 되면 `TreeSet`/`TreeMap`도 같을 거라고 생각하기 쉽다.

빠른 점검 질문은 세 가지면 충분하다.

1. 지금 컬렉션이 `HashSet`인가, `TreeSet`/`TreeMap`인가?
2. comparator가 보는 필드와 `equals()`가 보는 필드가 같은가?
3. `compare(...) == 0`이어도 정말 같은 원소나 같은 key로 합쳐도 되는가?

## 다음에 어디로 이어서 읽을까

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `TreeSet` comparator를 어떻게 설계하지? | [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md) |
| hash 계열과 sorted 계열 차이를 더 짧게 보고 싶다 | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |
| value object equality 기준부터 다시 잡고 싶다 | [Record and Value Object Equality](./record-value-object-equality-basics.md) |

## 한 줄 정리

`HashSet`은 `equals()` 기준으로, `TreeSet`/`TreeMap`은 `compare(...) == 0` 기준으로 같은 자리를 판단하므로, comparator가 `equals()`와 어긋나면 같은 `record` 예제도 컬렉션마다 전혀 다르게 보일 수 있다.
