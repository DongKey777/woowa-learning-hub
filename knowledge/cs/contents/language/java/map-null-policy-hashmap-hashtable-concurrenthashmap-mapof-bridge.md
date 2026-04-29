# Map null 허용 여부 구현체 브리지: `HashMap` vs `Hashtable` vs `ConcurrentHashMap` vs `Map.of`

> 한 줄 요약: 초보자 기준으로는 `HashMap`은 `null` key/value를 허용할 수 있고, `Hashtable`·`ConcurrentHashMap`·`Map.of(...)`는 `null`을 허용하지 않는다고 먼저 나누면 가장 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md)
- [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md)

retrieval-anchor-keywords: hashmap null key null value, hashtable null not allowed, concurrenthashmap null key value, map.of null exception, java map null policy beginner, 자바 hashmap null 허용, 자바 concurrenthashmap null 왜 안돼, 자바 map.of null 안됨, map implementation null difference, map null safety bridge, null key value 비교표, beginner map null primer

## 먼저 잡는 멘탈 모델

`Map`의 `null` 정책은 공통 규칙이 아니라 구현체 규칙이다.

- `HashMap`: `null` key 1개, `null` value 여러 개 가능
- `Hashtable`: `null` key/value 둘 다 불가
- `ConcurrentHashMap`: `null` key/value 둘 다 불가
- `Map.of(...)`: `null` key/value 둘 다 불가

초보자 기준에서는 먼저 이렇게 읽으면 된다.

> "`get() == null` 해석까지 할 일이 있으면 보통 `HashMap` 계열, 애초에 `null` 자체를 막아 두면 `ConcurrentHashMap`이나 `Map.of(...)` 쪽"

## 10초 비교표

| 구현체 | `null` key | `null` value | 초보자용 한 줄 해석 |
|---|---|---|---|
| `HashMap` | 허용 | 허용 | `null`을 넣을 수 있어서 `get() == null` 해석이 애매할 수 있다 |
| `Hashtable` | 불가 | 불가 | 예전 동기화 map, `null`은 바로 막는다 |
| `ConcurrentHashMap` | 불가 | 불가 | 동시성 map이라 `null`을 금지해 조회 의미를 분명하게 둔다 |
| `Map.of(...)` | 불가 | 불가 | 읽기 전용 상수 map이라 `null` 없이 바로 만든다 |

실무에서 초보자가 가장 자주 마주치는 혼동은 이것이다.

- "`Map`이면 다 `null` 넣을 수 있겠지?" -> 아니다
- "`get() == null`이면 언제나 key가 없다는 뜻이겠지?" -> `HashMap`에서는 아니다

## 같은 코드라도 결과가 다르다

```java
Map<String, String> hashMap = new HashMap<>();
hashMap.put(null, "ok");
hashMap.put("A", null);   // 둘 다 가능

Map<String, String> table = new Hashtable<>();
table.put(null, "boom");  // NullPointerException

Map<String, String> concurrent = new ConcurrentHashMap<>();
concurrent.put("A", null); // NullPointerException

Map<String, String> fixed = Map.of("A", "apple");
Map<String, String> broken = Map.of("B", null); // NullPointerException
```

핵심은 "문법이 아니라 구현체 계약"이다.
`Map` 인터페이스만 보고 `null` 정책을 추측하면 틀리기 쉽다.

## 왜 `ConcurrentHashMap`은 `null`을 막을까

초보자용으로는 복잡한 동시성 내부 구현보다 이 한 줄이 중요하다.

> 여러 스레드가 동시에 볼 때는 "`get()` 결과가 `null`"이면 "key 없음"으로 바로 읽히는 편이 안전하다.

만약 `null` value까지 허용하면 아래 두 상황이 같은 결과로 보인다.

- 진짜로 key가 없음
- key는 있는데 value가 `null`

`ConcurrentHashMap`은 이 모호함을 아예 막으려고 `null`을 금지한다.
그래서 beginner 첫 읽기에서는 "`동시성 map은 null 없이 읽는 쪽`"까지만 기억하면 충분하다.
복합 연산이나 hot-key contention 같은 운영형 주제는 여기서 파지 말고 follow-up 문서로 넘긴다.

## `Map.of(...)`는 왜 `null`을 막을까

`Map.of(...)`는 초보자 기준으로 "바로 만드는 읽기 전용 상수 map"이다.
이때 `null`까지 받아 버리면 실수한 입력을 늦게 발견하기 쉽다.

그래서 `Map.of(...)`는 만드는 순간 `null`을 거절해, 상수 데이터가 더 단순하게 읽히도록 둔다.

- 설정값, 테스트 데이터, 코드 상수처럼 "비어 있지 않은 값"을 명확히 적고 싶을 때 잘 맞는다
- "`값이 아직 없음`" 같은 상태를 담아야 하면 `Map.of(...)`보다 다른 표현이 나을 수 있다

## 자주 헷갈리는 질문

### `HashMap`에서만 `containsKey()`를 더 자주 떠올리는 이유가 있나요?

있다. `HashMap`은 `null` value를 허용하므로 `get() == null`만으로는 "없는 key"와 "null value"를 구분 못 한다.
그래서 존재 여부가 중요하면 `containsKey()`가 더 안전하다.

### `ConcurrentHashMap`이면 `get() == null`은 key 없음으로 봐도 되나요?

보통 그렇다. `null` value를 저장할 수 없으므로 `get() == null`이면 "현재 key가 없다"로 읽기 쉽다.

### `Hashtable`도 지금 새 코드에서 배워야 하나요?

비교표 수준으로만 알면 충분하다.
초보자 첫 기준은 "`예전 동기화 map이고, `null`을 허용하지 않는다`" 정도면 된다.

## 빠른 선택 체크리스트

- `null` key/value를 저장해야 한다면 먼저 `HashMap` 쪽인지 확인한다
- `get() == null` 해석이 애매하면 `containsKey()`를 함께 본다
- 동시성 map이 필요하면 `ConcurrentHashMap`은 `null`을 금지한다고 기억한다
- 상수 map을 만들면 `Map.of(...)`는 `null`을 받지 않는다고 기억한다
- "`Map`이면 다 비슷하다"라고 묶지 말고 구현체 계약까지 같이 본다

## 다음 읽기

| 지금 더 막히는 질문 | 다음 문서 |
|---|---|
| "`get() == null`이 왜 애매한지부터 다시 보고 싶다" | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) |
| "`Map.of(...)`와 `Map.copyOf(...)`는 읽기 전용에서 뭐가 다르지?" | [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md) |
| "아예 어떤 map 구현체를 먼저 골라야 할지 헷갈린다" | [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md) |
| "반복 순서까지 같이 비교하고 싶다" | [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md) |
| "`ConcurrentHashMap`을 실무에서 더 깊게 봐야 한다" | [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md) |

## 한 줄 정리

`HashMap`은 `null`을 받을 수 있지만 `Hashtable`, `ConcurrentHashMap`, `Map.of(...)`는 `null`을 막으므로, `Map`의 `null` 정책은 인터페이스가 아니라 구현체 계약으로 읽어야 한다.
