---
schema_version: 3
title: Record Comparator 60 Second Mini Drill
concept_id: language/record-comparator-60-second-mini-drill
canonical: true
category: language
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 91
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- record
- comparator
- equality-ordering
aliases:
- Record Comparator 60 second mini drill
- record equals comparator mismatch practice
- Java record TreeSet TreeMap surprise
- record name only comparator worksheet
- HashSet TreeSet TreeMap record prediction
- 자바 record comparator 연습
symptoms:
- record의 자동 equals는 모든 component를 보는데 TreeSet TreeMap comparator는 name만 보도록 만들어 중복 기준이 갈리는 점을 놓쳐
- HashSet은 equals/hashCode 기준이고 TreeSet TreeMap은 compare==0 기준이라는 차이를 record 예제로 예측하지 못해
- comparator tie-breaker를 빼면 같은 name을 같은 자리로 collapse하고 thenComparingLong id를 넣으면 분리된다는 감각이 없어
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- language/record-value-object-equality-basics
- language/equality-vs-ordering-beginner-drill-sheet
- language/hashset-vs-treeset-duplicate-semantics
next_docs:
- language/treemap-record-containskey-get-name-comparator-drill
- language/treeset-treemap-comparator-tie-breaker-basics
- language/java-comparable-comparator-basics
linked_paths:
- contents/language/java/record-value-object-equality-basics.md
- contents/language/java/equality-vs-ordering-beginner-drill-sheet.md
- contents/language/java/hashset-vs-treeset-duplicate-semantics.md
- contents/language/java/treeset-treemap-comparator-tie-breaker-basics.md
- contents/language/java/treemap-record-containskey-get-name-comparator-drill.md
- contents/language/java/java-comparable-comparator-basics.md
confusable_with:
- language/equality-vs-ordering-beginner-drill-sheet
- language/hashset-vs-treeset-duplicate-semantics
- language/treemap-record-containskey-get-name-comparator-drill
forbidden_neighbors: []
expected_queries:
- record 자동 equals와 name-only Comparator가 다를 때 HashSet TreeSet TreeMap 결과를 예측하는 드릴을 해보고 싶어
- record Student id name에서 HashSet은 둘 다 남고 TreeSet은 하나로 합쳐질 수 있는 이유가 뭐야?
- TreeMap comparator가 name만 보면 new Student(99, Mina)로 get이 되는 이유를 설명해줘
- comparator에 thenComparingLong id tie-breaker를 넣으면 collapse가 separation으로 바뀌는 이유가 뭐야?
- equality와 ordering 기준이 다르면 sorted collection에서 어떤 surprise가 생겨?
contextual_chunk_prefix: |
  이 문서는 record 자동 equals/hashCode와 name-only Comparator가 다른 기준을 쓸 때 HashSet, TreeSet, TreeMap 결과를 예측하는 beginner drill이다.
  record comparator, equality vs ordering, TreeSet duplicate, TreeMap get, thenComparing tie-breaker 질문이 본 문서에 매핑된다.
---
# Record-Comparator 60초 미니 드릴

> 한 줄 요약: `record`의 자동 `equals()`와 name-only `Comparator`가 서로 다른 기준을 쓰면, 같은 두 객체를 넣어도 `HashSet`/`TreeSet`/`TreeMap` 결과가 갈릴 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: record comparator 60 second mini drill basics, record comparator 60 second mini drill beginner, record comparator 60 second mini drill intro, java basics, beginner java, 처음 배우는데 record comparator 60 second mini drill, record comparator 60 second mini drill 입문, record comparator 60 second mini drill 기초, what is record comparator 60 second mini drill, how to record comparator 60 second mini drill
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)
> - [Beginner Drill Sheet: Equality vs Ordering](./equality-vs-ordering-beginner-drill-sheet.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator](./treemap-record-containskey-get-name-comparator-drill.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)

> retrieval-anchor-keywords: record comparator mini drill, record comparator 60 second worksheet, java record treeset treemap surprise, record equals comparator mismatch practice, hashset treeset treemap record example, record name only comparator worksheet, compare zero same slot record, record hashset treeset treemap prediction, java beginner equality ordering worksheet, java thenComparingLong id tie breaker, comparator collapse to separation, treeset treemap tie breaker worksheet, record comparator separation example, 자바 record comparator 연습, 자바 record treeset treemap 결과 예측, 자바 hashset treeset treemap record 워크시트, record 자동 equals comparator 충돌, thenComparingLong id 브리지, comparator tie breaker 분리 예제

## 먼저 잡을 mental model

처음엔 아래 3줄만 기억하면 된다.

- `record`의 자동 `equals()`는 선언한 component 전체를 본다
- `HashSet`은 `equals()/hashCode()` 기준으로 중복을 판단한다
- `TreeSet`/`TreeMap`은 `compare(...) == 0` 기준으로 같은 자리인지 판단한다

이번 드릴에서는 이 기준이 일부러 갈리게 만든다.

- `record Student(long id, String name)` -> `id`와 `name`을 둘 다 본다
- `Comparator.comparing(Student::name)` -> `name`만 본다

## 15초 비교표

| 컬렉션 | 이번 드릴의 중복 기준 | `new Student(1, "Mina")`, `new Student(2, "Mina")` |
|---|---|---|
| `HashSet<Student>` | `equals()/hashCode()` | 둘 다 남을 수 있음 |
| `TreeSet<Student>` | `compare(...) == 0` | 하나로 합쳐질 수 있음 |
| `TreeMap<Student, V>` | key `compare(...) == 0` | 같은 key 자리로 보고 값이 덮어써질 수 있음 |

## 1페이지 미니 드릴

### 드릴 코드

```java
import java.util.Comparator;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

record Student(long id, String name) {}

Student a = new Student(1L, "Mina");
Student b = new Student(2L, "Mina");

Comparator<Student> byNameOnly =
        Comparator.comparing(Student::name);

Set<Student> hash = new HashSet<>();
hash.add(a);
hash.add(b);

Set<Student> tree = new TreeSet<>(byNameOnly);
tree.add(a);
tree.add(b);

TreeMap<Student, String> seat = new TreeMap<>(byNameOnly);
String prev1 = seat.put(a, "front");
String prev2 = seat.put(b, "back");

System.out.println(hash.size());
System.out.println(tree.size());
System.out.println(prev1);
System.out.println(prev2);
System.out.println(seat.size());
System.out.println(seat.get(new Student(99L, "Mina")));
```

### 실행 전 워크시트

| 질문 | 내 답(실행 전) |
|---|---|
| `hash.size()` |  |
| `tree.size()` |  |
| `prev1` |  |
| `prev2` |  |
| `seat.size()` |  |
| `seat.get(new Student(99L, "Mina"))` |  |

### 정답

- `hash.size()` -> `2`
- `tree.size()` -> `1`
- `prev1` -> `null`
- `prev2` -> `"front"`
- `seat.size()` -> `1`
- `seat.get(new Student(99L, "Mina"))` -> `"back"`

## 같은 워크시트, tie-breaker 하나만 더하면

이번에는 같은 `Student a`, `Student b`를 그대로 두고 comparator만 바꿔 본다.

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);
```

mental model은 짧다.

- 전에는 `name`만 봐서 `a`와 `b`가 같은 칸으로 collapse됐다
- 지금은 `name`이 같아도 `id`를 한 번 더 봐서 서로 다른 칸으로 separation된다

### 결과가 어떻게 바뀌나

| 질문 | name-only comparator | `thenComparingLong(Student::id)` 추가 후 |
|---|---|---|
| `hash.size()` | `2` | `2` |
| `tree.size()` | `1` | `2` |
| `prev1` | `null` | `null` |
| `prev2` | `"front"` | `null` |
| `seat.size()` | `1` | `2` |
| `seat.get(new Student(99L, "Mina"))` | `"back"` | `null` |

왜 이렇게 바뀔까?

- `HashSet`은 원래 comparator를 안 보므로 그대로 `2`다
- `TreeSet`은 이제 `name`이 같아도 `id`가 다르면 `compare(...) != 0`이라 둘 다 남는다
- `TreeMap`도 같은 key 자리로 보지 않으므로 두 번째 `put`이 덮어쓰지 않고 `null`을 반환한다
- 조회도 `new Student(99L, "Mina")`가 더는 같은 자리로 잡히지 않으므로 `null`이 나온다

## 왜 이렇게 나오나

### `HashSet`

- `record Student(long id, String name)`의 `equals()`는 `id`와 `name`을 둘 다 본다
- `a`와 `b`는 `id`가 다르므로 `equals()`가 `false`다
- 그래서 `HashSet`에는 둘 다 남는다

### `TreeSet`

- comparator가 `name`만 보므로 `a`와 `b`를 비교하면 `0`이 나온다
- `TreeSet`은 `compare(...) == 0`이면 같은 원소 자리로 본다
- 그래서 하나만 남는다

### `TreeMap`

- key 비교도 같은 comparator를 쓴다
- 두 번째 `put`은 "다른 객체"를 넣는 것처럼 보여도, map 입장에서는 같은 key 자리다
- 그래서 기존 `"front"`를 반환하고, 최종 값은 `"back"`으로 바뀐다
- `new Student(99L, "Mina")`로 조회해도 `name`만 같으면 같은 key 자리로 본다

## 초보자가 자주 헷갈리는 포인트

- `record`니까 모든 컬렉션이 같은 기준으로 중복을 판단할 거라고 생각하기 쉽다
- `TreeSet`에서 원소가 "사라졌다"고 느끼기 쉽지만, 실제로는 comparator가 둘을 구분하지 못한 것이다
- `TreeMap.get(new Student(99L, "Mina"))`가 되는 이유를 "record는 이름만 비교하나 보다"로 오해하기 쉽다

안전한 습관:

- `record`를 보면 먼저 "`equals()`가 어떤 필드를 보나?"를 적는다
- sorted 컬렉션을 보면 "`compare == 0`이 되는 조건이 뭔가?"를 따로 적는다
- 같은 워크시트에서 collapse를 separation으로 바꾸고 싶다면 `thenComparingLong(Student::id)` 같은 tie-breaker를 넣는다

## 다음 읽기

- 조회만 따로 다시 손예측하려면: [TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator](./treemap-record-containskey-get-name-comparator-drill.md)
- 개념 먼저 다시 묶기: [Record and Value Object Equality](./record-value-object-equality-basics.md)
- 워크시트 확장판: [Beginner Drill Sheet: Equality vs Ordering](./equality-vs-ordering-beginner-drill-sheet.md)
- 컬렉션별 중복 규칙: [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- tie-breaker 감각 확장: [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

## 한 줄 정리

`record`의 자동 `equals()`와 name-only `Comparator`가 서로 다른 기준을 쓰면, 같은 두 객체를 넣어도 `HashSet`/`TreeSet`/`TreeMap` 결과가 갈릴 수 있다.
