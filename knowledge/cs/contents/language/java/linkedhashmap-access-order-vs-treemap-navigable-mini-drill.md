# LinkedHashMap access-order vs TreeMap navigable API 미니 드릴

> 한 줄 요약: "`get()`만 했는데 순서가 바뀐다"면 `LinkedHashMap(access-order=true)` 쪽이고, "`x` 이하에서 가장 가까운 key`"나 "`20` 이상 `40` 미만만 자르고 싶다`"면 `TreeMap`의 `floorKey`/`subMap` 쪽이라는 감각을 증상부터 빠르게 고정하는 beginner drill이다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [LinkedHashMap access-order에서 cache/LRU로 넘어가는 브리지](./linkedhashmap-access-order-cache-behavior-bridge.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](../../data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md)

retrieval-anchor-keywords: linkedhashmap access order vs treemap navigable api, linkedhashmap get changes order, treemap floorkey submap beginner, linkedhashmap insertion order vs access order drill, treemap range query symptom first, 조회만 했는데 순서가 바뀐다, floorkey 언제 써요, submap 언제 써요, 정렬된 key 범위 조회 map, insertion order access order 헷갈림, linkedhashmap vs treemap 언제, what is access order map, why map order changed after get, beginner ordered map symptom drill, 처음 배우는 treemap navigable basics

## 먼저 잡는 멘탈 모델

이번 드릴은 "둘 다 순서가 있는 map"이라고 묶지 않는 연습이다.

- `LinkedHashMap(access-order=true)`는 최근에 **만진 순서**를 기록한다.
- `TreeMap`은 key를 **정렬한 줄** 위에서 이웃과 범위를 찾는다.

짧게 외우면 이 두 문장이다.

> "조회만 했는데 뒤로 밀리면 access-order"  
> "`이 key 근처`, `이 구간만`이 나오면 TreeMap navigable API"

초보자가 많이 섞는 이유는 둘 다 "순서"라는 말을 쓰기 때문이다.
하지만 여기서 말하는 순서는 전혀 다르다.

- access-order: 최근 접근 기록
- `floorKey`/`subMap`: 정렬된 key 좌표계

## 10초 선택 표

| 보인 증상 또는 요구 | 첫 선택 | 왜 |
|---|---|---|
| `get(A)`만 했는데 출력 순서가 `B, C, A`로 바뀐다 | `LinkedHashMap(access-order=true)` | 조회가 최근 접근으로 기록된다 |
| 최근에 본 항목을 남기고 오래 안 본 항목을 밀어내고 싶다 | `LinkedHashMap(access-order=true)` | access-order가 LRU 감각과 연결된다 |
| `87` 이하에서 가장 가까운 key를 찾고 싶다 | `TreeMap.floorKey(87)` | 정렬된 key 줄에서 왼쪽 이웃을 찾는다 |
| `20` 이상 `40` 미만 entry만 보고 싶다 | `TreeMap.subMap(20, 40)` | 정렬된 key 범위를 자른다 |
| 등록한 순서 그대로 보여 주기만 하면 된다 | 기본 `LinkedHashMap` | 삽입 순서면 충분하다 |

핵심은 "`순서 보장`"이라는 말만 보고 `TreeMap`과 `LinkedHashMap`을 같은 칸에 두지 않는 것이다.

## 작은 예제로 먼저 보기

같은 key 세 개가 있어도 질문이 다르면 구현체가 갈린다.

| 장면 | 읽는 법 | 더 맞는 쪽 |
|---|---|---|
| `A, B, C`를 넣고 `get(A)`를 했더니 `B, C, A`가 됨 | 최근에 만진 것을 뒤로 보냄 | `LinkedHashMap(access-order=true)` |
| key가 `10, 20, 30, 40`일 때 `25`의 왼쪽 이웃을 찾음 | 정렬된 줄에서 가장 가까운 작은 key 찾기 | `TreeMap.floorKey(25)` |
| key가 `10, 20, 30, 40`일 때 `20`부터 `40` 전까지만 보고 싶음 | 정렬된 줄에서 구간 자르기 | `TreeMap.subMap(20, 40)` |

이 표를 한 번 붙이고 나면 증상을 이렇게 번역할 수 있다.

- "조회 후 순서 이동" -> access-order 문제
- "가까운 key / 범위 조회" -> navigable API 문제

## 미니 드릴: 증상 보고 고르기

아래 문장을 읽고 가장 먼저 떠올릴 답을 적어 보자.

| 번호 | 증상 또는 요구 | 내 답 |
|---|---|---|
| 1 | 테스트에서 `A, B, C`를 넣고 `get(B)`를 한 뒤 다시 순회했더니 `A, C, B`가 됐다. |  |
| 2 | 점수 기준표가 key로 저장돼 있고, `87`점일 때 적용할 바로 이전 기준 key를 찾고 싶다. |  |
| 3 | 예약 시각 key 중에서 `10:00` 이상 `12:00` 미만만 잘라서 보고 싶다. |  |
| 4 | 사용자가 북마크한 순서를 그대로 보여 주기만 하면 되고, 조회했다고 순서가 바뀌면 안 된다. |  |
| 5 | "왜 `get()`만 했는데 다음 eviction 대상이 `B`로 바뀌지?"라는 캐시 증상이 보인다. |  |
| 6 | "`30` 이하에서 가장 가까운 key"와 "`30` 이상 key들만`"을 같이 써야 한다. |  |

## 정답과 이유

| 번호 | 정답 | 이유 |
|---|---|---|
| 1 | `LinkedHashMap(access-order=true)` | `get(B)` 뒤에 `B`가 뒤로 갔다는 단서가 핵심이다 |
| 2 | `TreeMap.floorKey(87)` | exact match가 없어도 왼쪽에서 가장 가까운 key를 찾는 질문이다 |
| 3 | `TreeMap.subMap(10:00, 12:00)` | 삽입 순서가 아니라 정렬된 key 범위가 필요하다 |
| 4 | 기본 `LinkedHashMap` | 삽입 순서는 필요하지만 access-order는 오히려 방해가 된다 |
| 5 | `LinkedHashMap(access-order=true)` | 조회가 순서를 바꿔 eldest 후보를 밀었기 때문이다 |
| 6 | `TreeMap` + `floorKey`/`tailMap` 또는 `subMap` | 이웃 조회와 범위 조회를 모두 쓰는 ordered key 문제다 |

여기서 초보자에게 가장 중요한 한 줄은 이것이다.

- `TreeMap`은 "정렬된 key를 읽는 API"
- `LinkedHashMap(access-order=true)`는 "최근 접근 순서를 기록하는 API"

## 흔한 오해와 함정

- "`LinkedHashMap`도 순서가 있으니 `floorKey` 비슷한 걸 할 수 있겠지"라고 생각하기 쉽다.
- "`TreeMap`도 순서가 있으니 `get()` 한 번 하면 맨 뒤로 밀릴 수도 있겠지"라고 읽기 쉽다.
- 기본 `LinkedHashMap`과 `LinkedHashMap(access-order=true)`를 같은 것으로 읽어서 "`조회만 했는데 순서가 바뀐다`" 증상을 놓치기 쉽다.
- `subMap(20, 40)`을 "`20`부터 `40`까지 전부"로 읽어서 끝 경계 `40`도 포함한다고 착각하기 쉽다.

안전한 읽기 순서는 아래처럼 잡으면 된다.

1. 지금 질문이 "최근에 만진 순서"인지 본다.
2. 아니면 "정렬된 key 줄에서 이웃/범위"인지 본다.
3. 범위라면 `subMap(from, to)`는 기본이 `[from, to)`라고 다시 읽는다.

## 다음에 어디로 이어서 읽을까

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`get()`이 왜 eviction 결과를 바꾸지?" | [LinkedHashMap access-order에서 cache/LRU로 넘어가는 브리지](./linkedhashmap-access-order-cache-behavior-bridge.md) |
| "`floor`/`ceiling`/`lower`가 같이 헷갈린다" | [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md) |
| "`subMap` 경계 포함/제외가 헷갈린다" | [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md) |
| "삽입 순서 map, access-order map, 정렬 map을 한 장으로 다시 보고 싶다" | [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md) |

## 한 줄 정리

"조회만 했는데 순서가 바뀐다"면 `LinkedHashMap(access-order=true)`를 먼저 보고, "`가까운 key`나 `범위 조회`"가 필요하면 `TreeMap.floorKey`/`subMap`을 먼저 보는 습관이 beginner 실수를 가장 빠르게 줄인다.
