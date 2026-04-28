# Map 조회/갱신 API 미니 브리지: `put()` vs `putIfAbsent()` vs `computeIfAbsent()` vs `merge()`

> 한 줄 요약: `HashMap.put`, `TreeMap.put`, `putIfAbsent()`를 한 카드에 놓고 보면 "구현체 선택"과 "덮어쓰기 정책 선택"이 다른 축이라는 점이 보이고, 그다음에 `computeIfAbsent()`와 `merge()`를 붙이면 `Map` 갱신 API 전체가 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md)
- [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md)
- [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./treemap-put-return-value-overwrite-bridge.md)
- [Map `put()`이 `null`을 돌려줄 때: 새 key vs 기존 `null` value 구분 브리지](./map-put-null-containskey-distinction-bridge.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [Map Value-Shape Drill](./map-value-shape-drill.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Hash Table Basics](../../data-structure/hash-table-basics.md)

retrieval-anchor-keywords: java map put vs putifabsent vs computeifabsent vs merge, hashmap put vs treemap put vs putifabsent, hashmap overwrite rules beginner, treemap overwrite rules beginner, map value overwrite when, putifabsent 언제 써, computeifabsent 뭐가 달라, merge 덮어쓰기 규칙, map k list v accumulation beginner, computeifabsent list add pattern, same key multiple values java map, 자바 map 값 있으면 덮어쓰나, 자바 map 없을 때만 넣기, hashmap treemap put 차이 헷갈, 처음 map overwrite policy

## 핵심 개념

이 네 API는 모두 "key에 값을 넣는다"는 공통점이 있다. 하지만 초보자가 먼저 봐야 할 축은 **기존 값이 있을 때 어떻게 행동하나**다.

- `put()`은 기존 값이 있어도 새 값으로 바로 덮어쓴다
- `putIfAbsent()`는 비어 있을 때만 넣고, 값이 있으면 그대로 둔다
- `computeIfAbsent()`는 비어 있을 때만 계산해서 넣는다
- `merge()`는 기존 값이 있으면 "기존 값 + 새 값"을 합친 뒤 다시 저장한다

짧게 외우면 이렇다.

> 항상 교체면 `put()`, 비어 있을 때만 채우면 `putIfAbsent()`/`computeIfAbsent()`, 누적이면 `merge()`.

## `HashMap.put` vs `TreeMap.put` vs `putIfAbsent()` 빠른 비교 카드

초보자가 자주 섞는 두 질문은 사실 축이 다르다.

- `HashMap` vs `TreeMap`은 "어떤 구현체를 쓰나?"라는 질문이다.
- `put()` vs `putIfAbsent()`는 "기존 값이 있을 때 덮어쓸 건가?"라는 질문이다.

즉 `TreeMap`을 골랐다고 자동으로 "안 덮어쓴다"가 되지 않는다. `TreeMap.put(...)`도 같은 key 자리면 그대로 덮어쓴다.

| 비교 대상 | key가 비어 있으면 | 기존 값이 있으면 | 초보자용 한 줄 |
|---|---|---|---|
| `HashMap.put(k, v)` | 저장 | 새 값으로 덮어쓴다 | 구현체는 `HashMap`, 정책은 "항상 교체" |
| `TreeMap.put(k, v)` | 저장 | 같은 key 자리면 새 값으로 덮어쓴다 | 구현체는 `TreeMap`, 정책은 여전히 "항상 교체" |
| `putIfAbsent(k, v)` | 저장 | 기존 값을 유지한다 | 구현체와 별개로 정책만 "비어 있을 때만 저장" |

여기서 `TreeMap.put(...)`의 "같은 key 자리"는 `equals()`가 아니라 comparator 또는 `compareTo() == 0`으로 정해진다. 그래서 초보자용 멘탈 모델은 이렇게 잡으면 된다.

> `HashMap`/`TreeMap`은 key를 찾는 방식의 선택이고, `put`/`putIfAbsent`는 overwrite 정책의 선택이다.

짧은 예제로 보면 더 분명하다.

```java
Map<String, Integer> scores = new HashMap<>();
scores.put("alice", 10);
scores.put("alice", 20);            // 20으로 덮어쓰기
scores.putIfAbsent("alice", 30);    // 그대로 20

TreeMap<String, Integer> sortedScores = new TreeMap<>();
sortedScores.put("alice", 10);
sortedScores.put("alice", 20);      // 여기서도 20으로 덮어쓰기
```

핵심은 마지막 줄이다. `TreeMap`은 정렬 map일 뿐, `put()`의 기본 정책 자체를 바꾸지는 않는다.

## 한눈에 보기

| API | key가 없을 때 | key에 값이 있을 때 | 초보자용 한 줄 |
|---|---|---|---|
| `put(k, v)` | `v` 저장 | 무조건 `v`로 덮어쓰기 | 그냥 새 값으로 교체 |
| `putIfAbsent(k, v)` | `v` 저장 | 기존 값 유지 | 비어 있을 때만 넣기 |
| `computeIfAbsent(k, f)` | `f`로 값 계산 후 저장 | 기존 값 유지 | 필요할 때만 계산해서 넣기 |
| `merge(k, v, f)` | `v` 저장 | `f(기존값, 새값)` 결과로 덮어쓰기 | 기존 값과 새 값을 합치기 |

`putIfAbsent()`와 `computeIfAbsent()`는 둘 다 "없을 때만 넣기" 쪽이다. 차이는 넣을 값을 **이미 갖고 있나**, 아니면 **그때 계산해야 하나**다.

## "덮어써지나?"만 먼저 보면

초보자가 가장 많이 하는 질문을 그대로 표로 줄이면 이렇다.

| 지금 map 상태 | `put()` | `putIfAbsent()` | `computeIfAbsent()` | `merge()` |
|---|---|---|---|---|
| key가 아예 없음 | 넣는다 | 넣는다 | 계산해서 넣는다 | 넣는다 |
| key에 기존 값이 있음 | 새 값으로 덮어쓴다 | 안 바꾼다 | 안 바꾼다 | 합친 결과로 덮어쓴다 |
| key는 있는데 값이 `null`임 | 새 값으로 덮어쓴다 | 새 값으로 채운다 | 계산해서 채운다 | 새 값으로 채운다 |

`null`이 들어갈 수 있는 `Map`에서는 "key는 있는데 값이 비어 있는 상태"도 따로 생각해야 덜 헷갈린다. 이 표만 기억해도 `putIfAbsent()`와 `computeIfAbsent()`를 `put()`처럼 잘못 쓰는 일이 줄어든다.

## 작은 예제로 같이 보기

```java
Map<String, Integer> scores = new HashMap<>();

scores.put("alice", 10);                         // alice = 10
scores.put("alice", 20);                         // alice = 20

scores.putIfAbsent("alice", 30);                 // 그대로 20
scores.putIfAbsent("bob", 30);                   // bob = 30

scores.computeIfAbsent("alice", k -> 40);        // 그대로 20
scores.computeIfAbsent("charlie", k -> 40);      // charlie = 40

scores.merge("alice", 5, Integer::sum);          // 20 + 5 = 25
scores.merge("daisy", 5, Integer::sum);          // daisy = 5
```

읽는 포인트는 네 줄이면 충분하다.

- `put()`은 `"alice"`를 10에서 20으로 바로 바꿨다
- `putIfAbsent()`는 `"alice"`를 건드리지 않았다
- `computeIfAbsent()`도 `"alice"`를 건드리지 않았다
- `merge()`는 `"alice"`를 유지하는 대신 20과 5를 합쳐 25로 갱신했다

## 언제 어떤 API를 고르나

### `put()`

이미 있는 값이 있어도 상관없이 최신 값으로 바꿀 때 쓴다.

- 설정값을 통째로 교체
- 마지막 상태를 그대로 저장
- "예전 값은 중요하지 않다"는 상황

### `putIfAbsent()`

기본값을 한 번만 넣고 싶을 때 쓴다.

- 최초 방문 사용자에만 기본 점수 부여
- 이미 값이 있으면 건드리면 안 되는 경우

### `computeIfAbsent()`

값을 미리 만들지 말고, 정말 필요할 때만 계산하고 싶을 때 쓴다.

- key가 없을 때만 리스트 생성
- key가 없을 때만 캐시 로딩

```java
ordersByUser.computeIfAbsent(userId, id -> new ArrayList<>()).add(order);
```

초보자 기준 핵심은 "`putIfAbsent()`의 지연 계산 버전"으로 읽는 것이다.

## 같은 key에 값을 여러 개 쌓을 때는 이렇게 본다

초보자가 많이 부딪히는 follow-up은 이것이다.

- `Map<String, Order>`에 같은 사용자 주문을 계속 `put()`하면 마지막 주문만 남는다
- 그런데 요구사항은 "사용자별 주문 여러 개"라서 사실 `Map<String, List<Order>>`가 필요하다

즉 문제는 `Map` API보다 먼저 **value 모양**에 있다. key마다 값이 여러 개면 `V` 하나가 아니라 `List<V>`를 둬야 하고, 그 리스트를 안전하게 꺼내는 첫 패턴이 `computeIfAbsent()`다.

```java
Map<String, List<String>> ordersByUser = new HashMap<>();

ordersByUser.computeIfAbsent("alice", key -> new ArrayList<>()).add("order-1");
ordersByUser.computeIfAbsent("alice", key -> new ArrayList<>()).add("order-2");
ordersByUser.computeIfAbsent("bob", key -> new ArrayList<>()).add("order-3");
```

이 코드는 이렇게 읽으면 된다.

- `"alice"`가 처음 나오면 빈 리스트를 한 번 만들고 `"order-1"`을 넣는다
- `"alice"`가 다시 나오면 기존 리스트를 그대로 꺼내 `"order-2"`만 추가한다
- 그래서 `"alice"` 아래 값이 덮어써지지 않고 `["order-1", "order-2"]`처럼 쌓인다

한 줄 멘탈 모델:

> `computeIfAbsent(...).add(...)`는 "리스트가 없으면 만들고, 있으면 그 리스트에 이어 붙이기"다.

## 왜 `put(new ArrayList(...))`가 덮어쓰기가 되나

아래 코드는 초보자가 자주 쓰는 실수다.

```java
ordersByUser.put("alice", new ArrayList<>(List.of("order-1")));
ordersByUser.put("alice", new ArrayList<>(List.of("order-2")));
```

두 번째 줄은 첫 리스트에 `"order-2"`를 추가하는 것이 아니라, `"alice"`에 연결된 값을 아예 새 리스트로 교체한다. 그래서 결과는 `["order-2"]`만 남는다.

같은 요구사항을 안전하게 쓰려면 비교를 이렇게 잡으면 된다.

| 하고 싶은 일 | 더 맞는 코드 |
|---|---|
| 마지막 값 하나만 남겨도 된다 | `put(key, value)` |
| key마다 여러 값을 계속 쌓아야 한다 | `computeIfAbsent(key, k -> new ArrayList<>()).add(value)` |

처음부터 "같은 key에 값이 여러 개 붙나?"를 확인하면 `put()`으로 실수하는 횟수가 크게 줄어든다.

### `merge()`

기존 값에 새 값을 더하거나 이어 붙일 때 쓴다.

```java
counts.merge(word, 1, Integer::sum);
```

이 코드는 "없으면 1로 넣고, 있으면 기존 값에 1을 더해 다시 저장"으로 읽으면 된다.

## 흔한 오해와 바로잡기

- "`putIfAbsent()`는 key만 없을 때 동작한다"고 외우고 끝내기 쉽다.
  `HashMap`처럼 `null` value를 허용하면 현재 값이 `null`일 때도 새 값으로 채운다.
- "`TreeMap`은 정렬 map이니까 `put()`도 기존 값을 보존할 것"이라고 느끼기 쉽다.
  아니다. `TreeMap.put()`도 같은 key 자리면 덮어쓴다. 구현체 선택과 overwrite 정책 선택을 분리해서 봐야 한다.
- "`computeIfAbsent()`는 그냥 `putIfAbsent()`의 복잡한 버전"이라고 보기 쉽다.
  차이는 값을 미리 만들지 않고, 정말 필요할 때만 함수로 계산한다는 점이다.
- "`computeIfAbsent(...).add(...)`는 결국 매번 새 리스트를 넣는 것 아닌가?"라고 느끼기 쉽다.
  key가 이미 있으면 새 리스트를 만들지 않고, 기존 리스트를 그대로 돌려준 뒤 그 리스트에 `add(...)`하는 흐름이다.
- "`merge()`도 결국 덮어쓰기니까 `put()`과 같다"고 보기 쉽다.
  `merge()`는 기존 값을 버리지 않고 합친 결과로 덮어쓴다.
- "조회 후 `if (map.get(k) == null) put(...)`로 직접 짜도 같다"고 생각하기 쉽다.
  의도는 보이지만, "없을 때만 넣기"라는 말을 API 이름으로 바로 드러내는 쪽이 읽기 쉽다.
- "`merge()`는 카운팅 전용 API다"라고 좁게 이해하기 쉽다.
  숫자 합산뿐 아니라 문자열 이어 붙이기, 목록 누적 같은 "기존 값과 새 값을 합치기" 전반에 쓴다.

## 헷갈릴 때 10초 선택표

| 지금 하고 싶은 일 | 먼저 떠올릴 API |
|---|---|
| 기존 값이 있어도 최신 값으로 바꾼다 | `put()` |
| 비어 있을 때만 기본값을 넣는다 | `putIfAbsent()` |
| 비어 있을 때만 값을 계산해서 넣는다 | `computeIfAbsent()` |
| 기존 값과 새 값을 합쳐 다시 넣는다 | `merge()` |

한 문장 멘탈 모델도 같이 기억하면 좋다.

- `put()` = 교체
- `putIfAbsent()` = 빈칸 채우기
- `computeIfAbsent()` = 필요할 때만 만들어 채우기
- `merge()` = 합쳐서 갱신

증상 문장으로도 바로 연결할 수 있다.

- "값이 있어도 그냥 최신 값으로 바꿀래"면 `put()`
- "없을 때만 넣고 싶어"면 `putIfAbsent()`
- "없을 때만 만들고 싶어"면 `computeIfAbsent()`
- "기존 값에 새 값을 더하고 싶어"면 `merge()`

## 더 깊이 가려면

- `null`이 섞이면 `putIfAbsent()`와 `computeIfAbsent()` 해석이 더 헷갈릴 수 있다. 먼저 [Map `put()`이 `null`을 돌려줄 때: 새 key vs 기존 `null` value 구분 브리지](./map-put-null-containskey-distinction-bridge.md)를 같이 보면 좋다.
- `Map<K, List<V>>`처럼 value 모양 자체가 왜 달라져야 하는지부터 약하면 [Map Value-Shape Drill](./map-value-shape-drill.md)을 먼저 보고 돌아오면 좋다.
- 조회 결과 `null`의 뜻부터 불분명하다면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)로 먼저 돌아간다.
- "왜 `TreeMap.put()`도 덮어쓰지?"가 아직 남아 있으면 [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./treemap-put-return-value-overwrite-bridge.md)로 바로 이어서 보면 좋다.
- "그럼 `HashMap`과 `TreeMap`은 대체 언제 고르지?"가 더 궁금하면 [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md)에서 구현체 선택 축만 따로 정리할 수 있다.
- `Map`이 왜 이런 식으로 key를 찾는지 큰 그림이 필요하면 [Hash Table Basics](../../data-structure/hash-table-basics.md)로 넘어가면 된다.

## 한 줄 정리

`put()`은 무조건 교체, `putIfAbsent()`와 `computeIfAbsent()`는 비어 있을 때만 채우기, `merge()`는 기존 값과 새 값을 합쳐 갱신한다고 기억하면 `Map` 갱신 API 선택이 훨씬 쉬워진다.
