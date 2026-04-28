# Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머

> 한 줄 요약: `Map.get(key)`가 `null`을 돌려주면 "key가 없음"일 수도 있고 "value가 정말 null임"일 수도 있다. 그래서 "존재 여부가 중요하면 `containsKey()`", "없을 때 대신 쓸 기본값이 필요하면 `getOrDefault()`"로 나눠 읽는 편이 초보자에게 가장 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Map null 허용 여부 구현체 브리지: `HashMap` vs `Hashtable` vs `ConcurrentHashMap` vs `Map.of`](./map-null-policy-hashmap-hashtable-concurrenthashmap-mapof-bridge.md)
- [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md)
- [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)
- [Java Optional 입문](./java-optional-basics.md)
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)

retrieval-anchor-keywords: java map get null containskey getordefault difference, map get returns null missing key null value, hashmap null value beginner, map containskey 언제 쓰나, map getordefault 언제 쓰나, key 없음 null 값 차이, 자바 map get null 의미, 자바 map containskey getordefault 차이, 자바 hashmap null 처리 기초, map null safety beginner, keyset get null confusion, map iteration null beginner, map null vs missing semantics, optional to map null handling bridge, map get null beginner intro

## 먼저 잡는 멘탈 모델

`Map`을 사물함으로 보면 쉽다.

- key: 사물함 번호
- value: 사물함 안 내용물

이때 `get(key)`는 "그 번호 사물함에서 내용물을 꺼내 줘"에 가깝다.

문제는 꺼낸 결과가 `null`일 때다.

- 사물함 자체가 없어서 아무것도 못 꺼낸 것일 수 있다
- 사물함은 있는데 안에 `null`을 넣어 둔 것일 수 있다

즉 `get()`의 `null`만 보고는 둘을 구분할 수 없다.

단, 이 애매함은 주로 `HashMap`처럼 `null` value를 허용하는 구현체에서 생긴다.
`ConcurrentHashMap`이나 `Map.of(...)`처럼 `null`을 금지하는 쪽은 계약이 다르다.

## `Optional`과 빈 컬렉션 다음에 왜 여기서 다시 막히나

초보자는 보통 아래 순서로 null 감각을 익힌다.

- 단건 조회의 없음: `Optional<T>`
- 여러 건의 없음: 빈 `List`/`Set`
- key 기반 조회의 없음: `Map<K, V>`

앞의 두 단계는 비교적 단순하다.

- `Optional.empty()`는 "값 없음"
- 빈 리스트는 "원소 0개"

하지만 `Map.get(key)`는 `null` 하나에 두 의미가 겹칠 수 있다.

- key가 없다
- key는 있는데 value가 `null`이다

그래서 `Map`은 컬렉션이면서도, `Optional`처럼 "없음 해석"을 다시 조심해야 하는 구조다.

| 타입 | 초보자용 질문 | 보통 보는 API |
|---|---|---|
| `Optional<User>` | 사용자가 있나? | `orElse`, `orElseThrow` |
| `List<OrderLine>` | 주문 항목이 0개인가? | `isEmpty()` |
| `Map<Long, String>` | 이 id가 없나, 상태값이 `null`인가? | `containsKey()`, `get()`, `getOrDefault()` |

이 표를 기억하면 "`Optional`은 이해했는데 `Map.get()`에서 다시 헷갈린다"는 지점을 한 번에 연결하기 쉽다.

## 제일 먼저 보는 10초 표

| 지금 알고 싶은 것 | 추천 API | 이유 |
|---|---|---|
| "이 key가 있나?" | `containsKey(key)` | 존재 여부를 직접 묻는다 |
| "값을 꺼내고 싶다" | `get(key)` | 실제 value를 가져온다 |
| "없으면 이 기본값을 쓰자" | `getOrDefault(key, defaultValue)` | 없을 때 대체값을 바로 정한다 |

초보자 기준 핵심 문장은 이것 하나다.

`get()`은 값 조회이고, `containsKey()`는 존재 확인이다.

## 왜 `get() == null`이 애매한가

```java
Map<String, String> nicknames = new HashMap<>();
nicknames.put("alice", null);

System.out.println(nicknames.get("alice")); // null
System.out.println(nicknames.get("bob"));   // null
```

둘 다 `null`이지만 의미는 다르다.

| 코드 | 실제 의미 |
|---|---|
| `nicknames.get("alice")` | key는 존재하지만 저장된 value가 `null` |
| `nicknames.get("bob")` | key 자체가 없음 |

그래서 아래 코드는 초보자가 자주 오해하는 패턴이다.

```java
if (nicknames.get("alice") == null) {
    System.out.println("alice가 없다");
}
```

이 코드는 "없다"를 정확히 말하지 못한다.
그냥 "꺼낸 값이 null이다"만 확인한 것이다.

## 한 세트로 연결해서 보는 3가지 예제

같은 "없음"이라도 타입이 바뀌면 읽는 법이 달라진다.

| 상황 | 타입 | 읽는 법 |
|---|---|---|
| 회원 단건 조회 | `Optional<User>` | 값이 없으면 `empty` |
| 회원의 쿠폰 목록 | `List<Coupon>` | 값이 없으면 빈 리스트 |
| 회원 id별 상태 조회 | `Map<Long, String>` | `get()`의 `null`만으로는 부족할 수 있음 |

```java
Optional<User> user = userRepository.findById(1L);
List<Coupon> coupons = couponService.findCoupons(1L);

Map<Long, String> statusByUser = new HashMap<>();
statusByUser.put(1L, null);
```

이제 각각 질문을 던져 보자.

- `user`는 없으면 `Optional.empty()`다
- `coupons`는 없으면 보통 `[]`다
- `statusByUser.get(1L)`와 `statusByUser.get(2L)`는 둘 다 `null`일 수 있다

즉 `Map`에서는 "없음"을 읽을 때 한 단계 더 질문해야 한다.
"key가 없나?" 아니면 "저장된 값이 `null`인가?"

그래서 beginner route를 짧게 묶으면 이렇게 된다.

1. 단건의 없음은 `Optional`
2. 다건의 0개는 빈 컬렉션
3. key 조회의 애매한 `null`은 `containsKey()`로 분리

## `containsKey()`를 쓰는 순간

존재 여부가 진짜 궁금하면 `containsKey()`가 맞다.

```java
if (nicknames.containsKey("alice")) {
    System.out.println("alice key는 존재한다");
}

if (!nicknames.containsKey("bob")) {
    System.out.println("bob key는 없다");
}
```

이 코드는 `null` value를 허용하는 `Map`에서도 뜻이 분명하다.

## `getOrDefault()`를 쓰는 순간

"없으면 기본값으로 처리하자"가 목적이면 `getOrDefault()`가 읽기 쉽다.

```java
Map<String, Integer> scoreByUser = new HashMap<>();
scoreByUser.put("alice", 95);

int aliceScore = scoreByUser.getOrDefault("alice", 0); // 95
int bobScore = scoreByUser.getOrDefault("bob", 0);     // 0
```

이 패턴은 "없는 key면 0점으로 보자", "없는 설정이면 기본 문자열을 쓰자"처럼 기본값 정책이 분명할 때 잘 맞는다.

다만 초보자 기준에서 한 가지는 꼭 기억해야 한다.

```java
Map<String, Integer> scoreByUser = new HashMap<>();
scoreByUser.put("alice", null);

System.out.println(scoreByUser.getOrDefault("alice", 0)); // null
```

`getOrDefault()`는 "key가 없을 때"만 기본값을 쓴다.
key는 있는데 value가 `null`이면 기본값으로 바꿔 주지 않는다.

## 세 API를 한 예제로 같이 보기

```java
Map<String, String> statusByUser = new HashMap<>();
statusByUser.put("alice", "ONLINE");
statusByUser.put("bob", null);

System.out.println(statusByUser.get("alice"));                 // ONLINE
System.out.println(statusByUser.get("bob"));                   // null
System.out.println(statusByUser.get("charlie"));               // null

System.out.println(statusByUser.containsKey("bob"));           // true
System.out.println(statusByUser.containsKey("charlie"));       // false

System.out.println(statusByUser.getOrDefault("alice", "OFF"));   // ONLINE
System.out.println(statusByUser.getOrDefault("charlie", "OFF")); // OFF
System.out.println(statusByUser.getOrDefault("bob", "OFF"));     // null
```

이 예제에서 읽어야 할 포인트는 3개다.

- `get("bob")`와 `get("charlie")`는 둘 다 `null`
- `containsKey("bob")`만 보면 bob key는 실제로 존재함
- `getOrDefault("bob", "OFF")`는 bob key가 있으므로 기본값 `"OFF"`를 쓰지 않음

## 초보자 혼동 포인트

초보자가 자주 쓰는 패턴:

```java
for (String user : statusByUser.keySet()) {
    String status = statusByUser.get(user);
    System.out.println(user + " -> " + status);
}
```

이 코드가 항상 틀린 건 아니다.
하지만 key와 value를 둘 다 볼 때는 `entrySet()` 쪽이 더 직접적이다.

```java
for (Map.Entry<String, String> entry : statusByUser.entrySet()) {
    System.out.println(entry.getKey() + " -> " + entry.getValue());
}
```

이렇게 쓰면 "순회 중 다시 `get()`해서 `null` 의미를 따로 해석해야 하나?"라는 혼동이 줄어든다.
반복 자체가 목적이면 `entrySet()`으로 pair를 바로 읽는 편이 초보자에게 덜 헷갈린다.

## 자주 하는 선택 실수

- "key가 있는지 보고 싶은데 `get() == null`로 확인한다"
  `null` value를 넣을 수 있는 `Map`에서는 부정확하다.
- "없는 key면 기본값이 필요해서 `containsKey()` + `get()`를 길게 쓴다"
  기본값 정책이 분명하면 `getOrDefault()`가 더 짧고 읽기 쉽다.
- "`getOrDefault()`면 `null` value도 기본값으로 바뀐다"고 생각한다
  아니다. key가 있을 때는 저장된 `null`을 그대로 돌려줄 수 있다.
- "모든 `Map` 구현체가 `null`을 똑같이 다룬다"
  아니다. `HashMap`, `ConcurrentHashMap`, `Map.of(...)`는 `null` 정책이 다르다.
- "순회 중 key/value가 둘 다 필요한데 `keySet()` + `get()`을 기본 패턴으로 잡는다"
  이때는 `entrySet()`이 보통 더 직접적이다.

## 빠른 선택 체크리스트

- 존재 여부가 핵심이면 `containsKey()`
- 실제 value가 필요하면 `get()`
- 없는 key에 대한 기본값 정책이 있으면 `getOrDefault()`
- `Map`이 `null` value를 허용하면 `get() == null`만으로 "없다"를 단정하지 않는다
- 순회에서 key/value를 함께 쓸 때는 `entrySet()`부터 떠올린다

## 다음에 어디로 이어 읽으면 좋은가

| 지금 더 헷갈리는 질문 | 다음 문서 |
|---|---|
| "`put()`/`get()`/`remove()`/`containsKey()` 반환값을 한 번에 외우고 싶다" | [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md) |
| "`Map` 반복에서 `entrySet()`/`keySet()`/`values()`를 언제 고르죠?" | [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md) |
| "`Map` 자체가 `Collection`이 아니라는 말부터 다시 잡고 싶다" | [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md) |
| "`null` 대신 `Optional`은 언제 쓰죠?" | [Java Optional 입문](./java-optional-basics.md) |
| "`Optional`/빈 컬렉션/도메인 타입에서 `Map`으로 넘어오는 기준이 헷갈린다" | [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md) |
| "`List`/`Set`/`Map` 선택부터 다시 정리하고 싶다" | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |
| "`HashMap`/`ConcurrentHashMap`/`Map.of(...)`가 `null`을 왜 다르게 다루지?" | [Map null 허용 여부 구현체 브리지: `HashMap` vs `Hashtable` vs `ConcurrentHashMap` vs `Map.of`](./map-null-policy-hashmap-hashtable-concurrenthashmap-mapof-bridge.md) |

## 한 줄 정리

`Map.get()`의 `null`은 "없음"과 "값이 null"을 구분하지 못하므로, 존재 여부는 `containsKey()`, 없는 key의 기본값 정책은 `getOrDefault()`로 분리해서 생각하면 초보자 실수를 크게 줄일 수 있다.
