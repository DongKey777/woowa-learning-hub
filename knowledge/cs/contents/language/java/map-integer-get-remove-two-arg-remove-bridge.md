# `Map<Integer, V>`에서 `get(1)`은 쉬운데 `remove(1)`은 왜 다르게 읽을까

> 한 줄 요약: `Map<Integer, V>`에서는 `get(1)`과 `remove(1)` 모두 index가 아니라 key `1` lookup으로 읽는다. 헷갈림은 `List.remove(1)` 같은 overload가 아니라, `remove(key)`가 "삭제된 value 반환"인지 `remove(key, value)`가 "지금 그 value일 때만 삭제"인지에서 갈린다.

**난이도: 🟡 Intermediate**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java Deep Dive Catalog](./README.md)
- [`List<Integer>.remove()` 오버로드 예측 드릴](./list-integer-remove-overload-practice-drill.md)
- [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [Map 조회/갱신 API 미니 브리지: `put()` vs `putIfAbsent()` vs `computeIfAbsent()` vs `merge()`](./map-put-putifabsent-computeifabsent-merge-overwrite-bridge.md)
- [Map vs Set Requirement Bridge](../../data-structure/map-vs-set-requirement-bridge.md)

retrieval-anchor-keywords: map integer get remove bridge, map integer get(1) remove(1) why, hashmap integer key remove confusion, map remove key value overload, map remove(key,value) when to use, map integer lookup update misconception, list remove(1) vs map remove(1), 왜 map remove(1) 은 index 가 아니에요, map get 1 remove 1 헷갈려요, map remove returns value or boolean, integer key lookup basics, what is map remove key value, map integer key overwrite why, remove key value compare and delete

## 핵심 개념

이 문서는 `List<Integer>.remove(1)` 드릴 다음 칸이다.

여기서 먼저 고정할 문장은 하나다.

- `Map<Integer, V>.get(1)`은 key `1` 조회다.
- `Map<Integer, V>.remove(1)`도 key `1` 삭제다.
- `List.remove(1)`처럼 "1번 위치"라는 질문은 `Map`에 없다.

즉 `Map<Integer, V>`에서 숫자 `1`이 보일 때 첫 함정은 index가 아니라 key lookup과 update 해석이다. `Map`은 줄 서 있는 목록이 아니라 key-value 사전이기 때문이다.

## 한눈에 보기

| 코드 | 먼저 읽는 질문 | 반환값/결과 |
|---|---|---|
| `map.get(1)` | key `1`의 현재 value가 있나 | value 또는 `null` |
| `map.remove(1)` | key `1`을 지우면 무엇이 빠지나 | 삭제된 value 또는 `null` |
| `map.remove(1, "OPEN")` | key `1`이 지금 `"OPEN"`일 때만 지울까 | `true` 또는 `false` |
| `map.put(1, "DONE")` | key `1` 자리를 새 value로 바꿀까 | 이전 value 또는 `null` |

짧은 멘탈 모델은 이렇다.

- `get`은 현재 상태를 읽는다.
- `put`은 key `1` 자리의 값을 바꾼다.
- `remove(key)`는 지워진 값을 돌려준다.
- `remove(key, value)`는 compare-and-delete처럼 "둘 다 맞을 때만 지운다"로 읽는다.

## 왜 `get(1)`은 쉬운데 `remove(1)`에서 멈추나

`get(1)`은 보통 질문이 하나라서 덜 흔들린다.

- key `1`이 있나
- 있으면 지금 value가 뭐지

반면 `remove`는 이름이 같아도 읽는 축이 둘이다.

- `remove(1)`은 key `1`을 지우고 삭제된 value를 돌려준다.
- `remove(1, "OPEN")`은 key와 value가 둘 다 맞을 때만 지우고 `boolean`을 돌려준다.

즉 `Map`의 `remove`에서 다른 점은 overload 자체보다 "삭제 후 무엇을 돌려주느냐"와 "현재 value까지 같이 확인하느냐"다. `List`처럼 `1`이 index인지 값인지 따지는 장면이 아니다.

## `Map<Integer, V>`에서 자주 섞이는 세 장면

```java
Map<Integer, String> statusById = new HashMap<>();
statusById.put(1, "OPEN");

System.out.println(statusById.get(1));              // OPEN
System.out.println(statusById.remove(1));           // OPEN
System.out.println(statusById.remove(1, "OPEN"));   // false
```

읽는 순서는 이렇게 자르면 안전하다.

1. `get(1)`은 key `1`의 현재 value 조회다.
2. `remove(1)`은 key `1`을 이미 지워서 `"OPEN"`을 반환한다.
3. 그다음 `remove(1, "OPEN")`은 key `1`이 더 이상 없으니 `false`다.

이 장면에서 learner가 자주 하는 오해는 "`remove(1)`도 성공 여부를 `boolean`으로 주겠지" 또는 "`remove(1, value)`는 그냥 더 자세한 조회인가"이다. 둘 다 아니다.

## 흔한 오해와 함정

| 오해 | 왜 위험한가 | 더 안전한 질문 |
|---|---|---|
| "`Map.remove(1)`도 `List.remove(1)`처럼 index 1 삭제죠?" | `Map`에는 index 개념이 없다 | 지금 `1`은 key인가 |
| "`remove(1)` 성공 여부를 알고 싶어요" | 1-arg `remove`는 value를 돌려준다 | 삭제된 값이 필요한가, 성공/실패만 필요한가 |
| "`remove(1, \"OPEN\")`은 key 1의 value를 읽는 거죠?" | 2-arg `remove`는 조건부 삭제다 | key와 현재 value가 둘 다 맞을 때만 지우고 싶은가 |
| "`put(1, \"DONE\")`은 key 1을 하나 더 추가하죠?" | `Map`은 같은 key를 중복 저장하지 않고 덮어쓴다 | 같은 key 자리의 value를 갱신하는가 |
| "`get(1) == null`이면 key 1이 없네요" | `null` value를 허용하면 단정이 어렵다 | key 없음인가, value가 `null`인가 |

비유로 보면 `Map<Integer, V>`는 좌석 번호표보다 사물함 번호에 가깝다. 다만 이 비유는 "조건부 삭제"까지 자동으로 설명하지 못하므로, `remove(key, value)`는 결국 API 계약으로 다시 읽어야 한다.

## 언제 `remove(key, value)`를 떠올리면 좋은가

`remove(key, value)`는 "지워도 되는 상태인지"를 같이 확인할 때 맞다.

```java
Map<Integer, String> statusById = new HashMap<>();
statusById.put(1, "OPEN");

boolean removed = statusById.remove(1, "OPEN");   // true
boolean skipped = statusById.remove(1, "DONE");   // false
```

이 패턴은 "key 1이 존재하기만 하면 지운다"보다 더 좁다.

- `remove(1)`은 key만 맞으면 지운다.
- `remove(1, "OPEN")`은 key와 현재 value가 모두 기대와 같을 때만 지운다.

그래서 update 오해와도 연결된다.

- key `1`을 새 상태로 바꾸고 싶으면 `put`, `replace`, `compute` 계열을 본다.
- key `1`이 특정 상태일 때만 없애고 싶으면 `remove(key, value)`를 본다.

## 더 깊이 가려면

- `List.remove(1)` 함정을 먼저 끊고 `Map`으로 넘어오고 싶으면 [`List<Integer>.remove()` 오버로드 예측 드릴](./list-integer-remove-overload-practice-drill.md)
- `Map` 메서드 반환값을 표로 다시 잡고 싶으면 [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md)
- `get(1) == null` 해석이 아직 흔들리면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- key `1` 자리 갱신과 "없을 때만 넣기"를 더 세분화하고 싶으면 [Map 조회/갱신 API 미니 브리지: `put()` vs `putIfAbsent()` vs `computeIfAbsent()` vs `merge()`](./map-put-putifabsent-computeifabsent-merge-overwrite-bridge.md)
- `Map`과 `Set` 요구 해석을 자료구조 관점에서 다시 묶고 싶으면 [Map vs Set Requirement Bridge](../../data-structure/map-vs-set-requirement-bridge.md)

## 한 줄 정리

`Map<Integer, V>`에서 `get(1)`과 `remove(1)`은 둘 다 key `1` lookup으로 읽고, 진짜 분기점은 `remove(key)`의 반환값 해석과 `remove(key, value)`의 조건부 삭제 의미를 구분하는 데 있다.
