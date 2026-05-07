---
schema_version: 3
title: TreeMap Record containsKey get Name Comparator Drill
concept_id: language/treemap-record-containskey-get-name-comparator-drill
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
- treemap
- record
- comparator
aliases:
- TreeMap record containsKey get name comparator drill
- record key name only comparator containsKey get
- compare zero same key lookup drill
- TreeMap get different record same name
- record equals comparator mismatch lookup
- 자바 TreeMap record 조회 드릴
symptoms:
- TreeMap.containsKey와 get이 record equals가 아니라 comparator compare==0으로 key slot을 찾는다는 점을 놓쳐
- name-only comparator로 저장한 TreeMap에서 id가 다른 record key도 같은 name이면 같은 key 자리로 조회될 수 있음을 예측하지 못해
- HashMap lookup의 equals/hashCode 감각을 TreeMap lookup에 그대로 적용해 comparator path를 디버깅하지 않아
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- language/record-comparator-60-second-mini-drill
- language/treeset-treemap-comparator-tie-breaker-basics
- language/map-lookup-debug-equals-hashcode-compareto-mini-bridge
next_docs:
- language/treemap-put-return-value-overwrite-bridge
- language/record-value-object-equality-basics
- language/equality-vs-ordering-beginner-drill-sheet
linked_paths:
- contents/language/java/record-comparator-60-second-mini-drill.md
- contents/language/java/treeset-treemap-comparator-tie-breaker-basics.md
- contents/language/java/map-lookup-debug-equals-hashcode-compareto-mini-bridge.md
- contents/language/java/record-value-object-equality-basics.md
confusable_with:
- language/record-comparator-60-second-mini-drill
- language/treeset-treemap-comparator-tie-breaker-basics
- language/map-lookup-debug-equals-hashcode-compareto-mini-bridge
forbidden_neighbors: []
expected_queries:
- TreeMap containsKey와 get은 record equals가 아니라 comparator compare==0 기준으로 조회한다는 드릴을 해보고 싶어
- name-only comparator를 쓰면 new Student(99, Mina)로도 기존 Mina key 값을 찾을 수 있어?
- TreeMap record key 조회에서 id가 달라도 name이 같으면 containsKey가 true가 되는 이유가 뭐야?
- HashMap lookup과 TreeMap lookup은 equals hashCode vs comparator path가 어떻게 달라?
- record comparator mismatch lookup surprise를 beginner worksheet로 예측하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 record key와 name-only Comparator를 쓰는 TreeMap에서 containsKey/get이 compare==0 기준으로 lookup되는 결과를 예측하는 beginner drill이다.
  TreeMap containsKey, TreeMap get, record key, name comparator, compare zero lookup 질문이 본 문서에 매핑된다.
---
# TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator

> 한 줄 요약: `TreeMap`이 `record` key를 찾을 때는 `equals()`가 아니라 comparator의 `compare(...) == 0` 기준으로 같은 key 자리를 찾기 때문에, `id`가 달라도 `name`만 같으면 `containsKey()`와 `get()`이 예상과 다르게 동작할 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: treemap record containskey get name comparator drill basics, treemap record containskey get name comparator drill beginner, treemap record containskey get name comparator drill intro, java basics, beginner java, 처음 배우는데 treemap record containskey get name comparator drill, treemap record containskey get name comparator drill 입문, treemap record containskey get name comparator drill 기초, what is treemap record containskey get name comparator drill, how to treemap record containskey get name comparator drill
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Record-Comparator 60초 미니 드릴](./record-comparator-60-second-mini-drill.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)

> retrieval-anchor-keywords: treemap record containskey get drill, treemap record comparator lookup worksheet, record key name only comparator containsKey get, java treemap containsKey get surprise record, compare zero same key lookup drill, record equals comparator mismatch lookup, treemap get different record same name, treemap containskey different id same name, java beginner treemap record key worksheet, 자바 treemap record 조회 워크시트, 자바 containsKey get comparator surprise, 자바 record key name comparator 조회, 자바 treemap 같은 key 자리 compare zero

## 먼저 잡을 mental model

이번 문서는 저장보다 조회만 본다.

- `record`의 자동 `equals()`는 component 전체를 본다
- 하지만 `TreeMap` 조회는 comparator가 만든 길을 따라간다
- 그래서 `TreeMap`에서는 "`equals()`가 같은가?"보다 "`compare(...) == 0`인가?"가 더 직접적인 조회 기준이 된다

초보자용으로 줄이면 이 문장 하나면 된다.

> `TreeMap.containsKey()`와 `get()`은 "같은 객체인가?"보다 "comparator가 같은 key 자리라고 보나?"를 먼저 본다.

## 15초 비교표

`record Student(long id, String name)`와 `Comparator.comparing(Student::name)`를 같이 쓸 때:

| 조회 키 | record `equals()` 관점 | `TreeMap` 조회 관점 |
|---|---|---|
| `new Student(1, "Mina")` | 원래 key와 같을 수 있음 | 찾음 |
| `new Student(99, "Mina")` | 원래 key와 다름 | 그래도 찾을 수 있음 |
| `new Student(1, "Ria")` | 원래 key와 다름 | 못 찾음 |

핵심은 `TreeMap`이 `id`가 아니라 `name`만 보고 길을 찾는다는 점이다.

## 드릴 코드

```java
import java.util.Comparator;
import java.util.Map;
import java.util.TreeMap;

record Student(long id, String name) {}

Comparator<Student> byNameOnly =
        Comparator.comparing(Student::name);

Map<Student, String> seat = new TreeMap<>(byNameOnly);
seat.put(new Student(1L, "Mina"), "front");

System.out.println(seat.containsKey(new Student(1L, "Mina")));
System.out.println(seat.containsKey(new Student(99L, "Mina")));
System.out.println(seat.containsKey(new Student(1L, "Ria")));

System.out.println(seat.get(new Student(1L, "Mina")));
System.out.println(seat.get(new Student(99L, "Mina")));
System.out.println(seat.get(new Student(1L, "Ria")));
```

## 실행 전 워크시트

| 질문 | 내 답 |
|---|---|
| `containsKey(new Student(1L, "Mina"))` |  |
| `containsKey(new Student(99L, "Mina"))` |  |
| `containsKey(new Student(1L, "Ria"))` |  |
| `get(new Student(1L, "Mina"))` |  |
| `get(new Student(99L, "Mina"))` |  |
| `get(new Student(1L, "Ria"))` |  |

## 정답

- `containsKey(new Student(1L, "Mina"))` -> `true`
- `containsKey(new Student(99L, "Mina"))` -> `true`
- `containsKey(new Student(1L, "Ria"))` -> `false`
- `get(new Student(1L, "Mina"))` -> `"front"`
- `get(new Student(99L, "Mina"))` -> `"front"`
- `get(new Student(1L, "Ria"))` -> `null`

## 왜 이렇게 나오나

### 1. `record` 기준으로는 다른 객체다

- `Student(1, "Mina")`와 `Student(99, "Mina")`는 `id`가 다르다
- 그래서 record의 자동 `equals()` 기준으로는 서로 다르다

여기까지만 보면 초보자는 `containsKey(...)`가 `false`일 거라고 예상하기 쉽다.

### 2. 그런데 `TreeMap`은 comparator로 조회한다

- 지금 comparator는 `name`만 본다
- `"Mina"`와 `"Mina"`를 비교하면 `compare(...) == 0`이다
- `TreeMap`은 이 둘을 같은 key 자리로 본다

그래서 `new Student(99L, "Mina")`로도 조회가 된다.

### 3. 이름이 달라지면 길이 달라진다

- `"Mina"`와 `"Ria"`는 `compare(...) == 0`이 아니다
- 그래서 `TreeMap`은 같은 key 자리가 아니라고 판단한다
- 그 결과 `containsKey(...)`는 `false`, `get(...)`은 `null`이 된다

## 자주 하는 오해

- "`record`니까 조회도 자동 `equals()`로 하겠지"
  - `HashMap` 계열에서는 더 가깝지만, `TreeMap`은 comparator가 더 직접적이다.
- "`containsKey(new Student(99, \"Mina\")) == true`면 record가 이름만 비교하나 보다"
  - 아니다. record `equals()`는 그대로 전체 component를 본다. 조회 기준만 comparator가 바꾼 것이다.
- "`get(...)`이 값을 주면 원래 key 객체와 완전히 같은 것이다"
  - 아니다. 여기서는 "같은 key 자리로 판정됐다"가 더 정확하다.

## 20초 체크리스트

- `TreeMap` key 조회 기준이 `equals()`인지 `Comparator`인지 먼저 적었나?
- comparator가 `name`만 보는지, `id`까지 보는지 확인했나?
- "같은 객체"와 "같은 key 자리"를 같은 말로 섞어 쓰고 있지 않나?

서로 다른 학생을 모두 따로 구분하고 싶다면:

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);
```

이렇게 tie-breaker를 넣어 `compare(...) == 0`이 더 쉽게 나오지 않게 해야 한다.

## 다음 읽기

- 저장까지 같이 보고 싶으면: [Record-Comparator 60초 미니 드릴](./record-comparator-60-second-mini-drill.md)
- `compare == 0`이 왜 같은 key 자리인지 다시 잡고 싶으면: [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- 조회 실패 디버깅 순서를 더 넓게 보려면: [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)

## 한 줄 정리

`TreeMap`에서 `record` key 조회가 헷갈릴 때는 "`equals()`가 같은가?"보다 "이 comparator가 `compare(...) == 0`으로 같은 key 자리를 만들었는가?"를 먼저 보면 된다.
