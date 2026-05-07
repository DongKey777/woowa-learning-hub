---
schema_version: 3
title: Map Integer containsKey get getOrDefault Bridge
concept_id: language/map-integer-containskey-get-getordefault-bridge
canonical: true
category: language
difficulty: intermediate
doc_role: primer
level: intermediate
language: mixed
source_priority: 90
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- map-null
- integer-key
- getordefault
aliases:
- Map<Integer,V> containsKey get getOrDefault bridge
- map integer key lookup null default
- containsKey(1) get(1) getOrDefault(1)
- Map getOrDefault null value not default
- Integer key lookup semantics
- 자바 Map<Integer> key 조회 차이
symptoms:
- Map<Integer,V>에서 숫자 1을 List index처럼 읽어 key lookup이라는 점보다 위치 감각을 먼저 적용해
- containsKey, get, getOrDefault가 모두 key 1에 대해 같은 질문을 한다고 생각해 존재 여부, 현재 value, fallback 정책을 구분하지 못해
- getOrDefault가 key는 있지만 value가 null인 경우에도 default를 반환한다고 오해해 nullable value 정책을 잘못 읽어
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- language/map-get-null-containskey-getordefault-primer
- language/map-integer-get-remove-two-arg-remove-bridge
- language/map-put-get-remove-containskey-return-cheat-sheet
next_docs:
- language/map-null-policy-hashmap-hashtable-concurrenthashmap-mapof-bridge
- data-structure/map-vs-set-requirement-bridge
- language/list-integer-remove-overload-practice-drill
linked_paths:
- contents/language/java/map-get-null-containskey-getordefault-primer.md
- contents/language/java/map-integer-get-remove-two-arg-remove-bridge.md
- contents/language/java/map-put-get-remove-containskey-return-cheat-sheet.md
- contents/data-structure/map-vs-set-requirement-bridge.md
- contents/language/java/list-integer-remove-overload-practice-drill.md
- contents/language/java/map-null-policy-hashmap-hashtable-concurrenthashmap-mapof-bridge.md
confusable_with:
- language/map-get-null-containskey-getordefault-primer
- language/map-integer-get-remove-two-arg-remove-bridge
- language/list-integer-remove-overload-practice-drill
forbidden_neighbors: []
expected_queries:
- Map<Integer,V>에서 containsKey(1), get(1), getOrDefault(1, x)는 각각 무엇을 묻는 API야?
- Map<Integer>의 1은 index가 아니라 key라는 점을 List와 비교해서 설명해줘
- getOrDefault는 key가 있는데 value가 null이면 default를 반환하지 않는 이유가 뭐야?
- containsKey 후 get으로 missing key와 null value를 분리하는 예제를 보여줘
- Map<Integer> key lookup과 List<Integer>.remove(1) overload 혼동을 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 Map<Integer,V>에서 containsKey(1), get(1), getOrDefault(1, default)의 존재 확인, 현재 value 조회, key 부재 fallback 의미를 구분하는 intermediate primer다.
  Map Integer key, containsKey get getOrDefault, null value, missing key, index confusion 질문이 본 문서에 매핑된다.
---
# `Map<Integer, V>`에서 `containsKey(1)` / `get(1)` / `getOrDefault(1, ...)`를 언제 갈라 읽을까

> 한 줄 요약: `Map<Integer, V>`에서 `1`은 index가 아니라 key이고, `containsKey(1)`은 "존재 여부", `get(1)`은 "저장된 현재 값", `getOrDefault(1, ...)`는 "key가 없을 때만 대체값"을 묻는다. `null` value를 허용하면 이 셋을 같은 질문으로 읽으면 오해가 생긴다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Java Deep Dive Catalog](./README.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [`Map<Integer, V>`에서 `get(1)`은 쉬운데 `remove(1)`은 왜 다르게 읽을까](./map-integer-get-remove-two-arg-remove-bridge.md)
- [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md)
- [Map vs Set Requirement Bridge](../../data-structure/map-vs-set-requirement-bridge.md)

retrieval-anchor-keywords: map integer containskey get getordefault bridge, map integer key lookup null default difference, containskey(1) get(1) getordefault(1) 언제, map integer missing key null value fallback, hashmap integer key default value bridge, map getordefault null value not default, 자바 map integer key 조회 헷갈려요, 자바 containskey get getordefault 차이, 왜 get(1) 이 null 인데 key 가 있나요, map integer key beginner follow up, what is map integer key lookup, integer key lookup semantics bridge

## 핵심 개념

이 문서는 beginner primer 다음 칸이다.

이미 "`get()`이 `null`일 수 있다"는 사실은 알지만, `Map<Integer, V>`에서 `1`이 보이면 `List`의 index 감각과 "없으면 기본값" 감각이 한꺼번에 섞이기 쉽다.

여기서 먼저 고정할 문장은 세 개다.

- `containsKey(1)`은 key `1`이 존재하는지 묻는다.
- `get(1)`은 key `1`에 저장된 현재 value를 꺼낸다.
- `getOrDefault(1, x)`는 key `1`이 없을 때만 `x`를 대신 쓴다.

즉 분기점은 "`1`이 무엇이냐"보다 "`지금 어떤 질문을 하고 있느냐`"다. `Map<Integer, V>`의 `1`은 세 API 모두에서 key다.

## 한눈에 보기

| 코드 | 먼저 읽는 질문 | key `1`이 없을 때 | key `1`은 있고 value가 `null`일 때 |
|---|---|---|---|
| `scores.containsKey(1)` | key `1`이 존재하나 | `false` | `true` |
| `scores.get(1)` | key `1`의 현재 value가 뭐지 | `null` | `null` |
| `scores.getOrDefault(1, 0)` | key `1`이 없으면 `0`을 대신 쓸까 | `0` | `null` |

짧게 줄이면 아래처럼 읽으면 된다.

- 존재 여부가 필요하면 `containsKey`
- 실제 저장값이 필요하면 `get`
- key 부재에 대한 fallback 정책이 필요하면 `getOrDefault`

`get()`과 `getOrDefault()`가 둘 다 값을 돌려준다고 해서 같은 질문은 아니다. `getOrDefault()`는 "현재 값 조회"에 "없을 때만 대체값"이라는 정책이 추가된 API다.

## 왜 `Map<Integer, V>`에서 더 자주 헷갈리나

숫자 `1`이 보이면 초보자는 보통 두 가지를 같이 떠올린다.

- `List.get(1)`처럼 "두 번째 칸"인가?
- `null`이면 "없으니까 기본값"으로 읽어도 되나?

하지만 `Map<Integer, V>`에서는 둘 다 바로 단정하면 흔들린다.

- `1`은 위치가 아니라 key다.
- `null`은 key 없음일 수도 있고, 저장된 value가 `null`일 수도 있다.

그래서 `Map<Integer, V>`에서는 "`1`을 어떻게 읽을까"보다 "`부재를 어떻게 해석할까`"가 더 큰 함정이다. 이 지점이 `List<Integer>.remove(1)` 오버로드 혼동과 닮아 보여도 실제 분기 축은 다르다.

## 같은 예제를 세 API로 나눠 읽기

```java
Map<Integer, String> statusById = new HashMap<>();
statusById.put(1, null);
statusById.put(2, "READY");
```

이제 세 줄을 비교해 보자.

```java
System.out.println(statusById.containsKey(1));          // true
System.out.println(statusById.get(1));                  // null
System.out.println(statusById.getOrDefault(1, "NEW"));  // null
```

여기서 읽어야 할 포인트는 이렇다.

1. `containsKey(1)`이 `true`이므로 key `1`은 실제로 있다.
2. `get(1)`이 `null`인 이유는 "없어서"가 아니라 "저장된 value가 null이라서"일 수 있다.
3. `getOrDefault(1, "NEW")`도 key `1`이 있으므로 기본값 `"NEW"`를 쓰지 않는다.

반대로 key `3`은 없다고 해 보자.

```java
System.out.println(statusById.containsKey(3));          // false
System.out.println(statusById.get(3));                  // null
System.out.println(statusById.getOrDefault(3, "NEW"));  // NEW
```

이번에는 `get(3)`의 `null`이 key 부재 쪽이고, `getOrDefault(3, "NEW")`는 그 부재를 fallback 정책으로 덮는다.

## 언제 어떤 API를 먼저 떠올리면 안전한가

| 지금 하려는 말 | 첫 API | 이유 |
|---|---|---|
| "id 1이 등록돼 있나?" | `containsKey(1)` | 존재 여부를 직접 말한다 |
| "id 1의 현재 상태값이 뭐지?" | `get(1)` | 저장된 현재 value를 그대로 본다 |
| "id 1이 없으면 임시 기본 상태를 쓰자" | `getOrDefault(1, "NEW")` | key 부재에 대한 fallback을 바로 적는다 |
| "id 1이 없나, 아니면 상태가 아직 null인가?" | `containsKey(1)` 후 `get(1)` | 부재와 null value를 분리해야 한다 |

실무에서 가장 흔한 오독은 이것이다.

```java
if (statusById.get(1) == null) {
    return "NEW";
}
```

이 코드는 "id 1이 없다"와 "id 1은 있는데 값이 null이다"를 같은 분기로 뭉갠다. 그게 의도라면 괜찮지만, 의도가 아니라면 너무 이른 defaulting이다.

## 흔한 오해와 함정

| 오해 | 왜 틀어지나 | 더 안전한 질문 |
|---|---|---|
| "`get(1) == null`이면 key 1이 없다" | `null` value 허용 시 둘을 구분 못 한다 | key가 없는가, value가 `null`인가 |
| "`getOrDefault(1, x)`면 `null`도 `x`로 바뀐다" | 기본값은 key가 없을 때만 쓴다 | key가 있는데 value가 `null`인 경우도 있나 |
| "`Map<Integer, V>`의 `1`은 위치 1 같다" | `Map`에는 index 개념이 없다 | 지금 `1`은 key인가 |
| "`containsKey(1)`는 `get(1) != null`의 다른 표현이다" | `null` value 허용 시 동치가 아니다 | 존재 여부만 묻는가 |

비유로 보면 `Map<Integer, V>`는 좌석 줄이 아니라 번호표가 붙은 보관함이다. 다만 이 비유는 "기본값 정책"까지 자동으로 설명하지 못하므로, `getOrDefault()`는 결국 "보관함이 없을 때만 임시 물건을 대신 준다"는 API 계약으로 다시 읽어야 한다.

## 더 깊이 가려면

- `get()`의 `null` 의미를 beginner 관점에서 먼저 다시 잡고 싶으면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- 숫자 key에서 `remove(1)`과 `remove(1, value)`가 왜 또 다른 분기인지 붙여 보고 싶으면 [`Map<Integer, V>`에서 `get(1)`은 쉬운데 `remove(1)`은 왜 다르게 읽을까](./map-integer-get-remove-two-arg-remove-bridge.md)
- `put()`까지 포함해 반환값 전체를 한 장으로 다시 정리하고 싶으면 [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md)
- `Map`과 `Set` 요구를 자료구조 관점에서 다시 자르고 싶으면 [Map vs Set Requirement Bridge](../../data-structure/map-vs-set-requirement-bridge.md)

## 면접/시니어 질문 미리보기

- "`getOrDefault()`면 `null` value도 default로 바뀌나요?"
  - 보통 아니다. key가 존재하면 저장된 value를 그대로 돌려준다.
- "`containsKey()` 뒤에 `get()`을 바로 부르면 중복 조회 아닌가요?"
  - 맞다. 하지만 초반 학습에서는 의미를 분리해 읽는 연습이 먼저다. 성능이나 원자성 판단은 구현체와 맥락을 따로 봐야 한다.
- "`null` value를 아예 금지하면 이 혼동이 사라지나요?"
  - 일부는 줄어든다. 다만 구현체 계약과 도메인 의미를 함께 설계해야 한다.

## 한 줄 정리

`Map<Integer, V>`에서 `containsKey(1)`은 존재 여부, `get(1)`은 현재 값, `getOrDefault(1, ...)`는 key 부재 fallback이므로, missing key와 `null` value를 섞지 않으려면 셋을 같은 질문으로 읽지 않는 습관이 중요하다.
