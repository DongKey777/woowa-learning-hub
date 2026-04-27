# Map `put()`이 `null`을 돌려줄 때: 새 key vs 기존 `null` value 구분 브리지

> 한 줄 요약: `put(key, value)`가 `null`을 돌려줘도 "새 key였다"와 "기존 value가 null이었다"를 바로 구분할 수는 없다. 이때는 `containsKey(key)`를 덮어쓰기 전에 같이 봐야 뜻이 분명해진다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./treemap-put-return-value-overwrite-bridge.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)

retrieval-anchor-keywords: java map put null containsKey difference, hashmap put null previous value beginner, map put returns null but key exists, map put null distinguish containsKey, map previous value null vs missing key, treemap put null containsKey beginner, 자바 map put null 의미, 자바 hashmap put 반환값 null 구분, 자바 containsKey put 패턴, 맵 put null 기존 null 값 새 key 차이, map put previous value null missing key bridge

## 먼저 잡는 멘탈 모델

`put()`은 "넣고 끝"이 아니라 "넣기 전 상태를 한 번 알려 주기"까지 같이 한다.

- 비어 있던 칸에 처음 넣으면 이전 값이 없으니 `null`
- 이미 있던 칸의 값이 `null`이었어도 이전 값은 역시 `null`

즉 `put()`의 `null`은 한 가지 뜻이 아니라 두 가지 가능성을 같이 품는다.

## 10초 비교표

| `put()` 호출 전 상태 | `put()` 반환값 | `containsKey(key)` | 무슨 일인가 |
|---|---|---|---|
| key 없음 | `null` | `false` | 새 key 추가 |
| key 있음, 이전 value가 `null` | `null` | `true` | 기존 key 덮어쓰기 |
| key 있음, 이전 value가 `"A"` | `"A"` | `true` | 기존 key 덮어쓰기 |

초보자 기준 핵심 문장은 이것 하나면 된다.

> `put() == null`만으로는 "새 key"라고 단정하지 말고, 필요하면 `containsKey()`를 먼저 본다.

## 가장 흔한 혼동 예제

```java
Map<String, String> statusByUser = new HashMap<>();
statusByUser.put("alice", null);

String previous = statusByUser.put("alice", "ONLINE");
System.out.println(previous); // null
```

여기서 `previous`가 `null`이라고 해서 `"alice"`가 새 key였던 것은 아니다.

- `"alice"` key는 이미 있었다
- 다만 이전 value가 `null`이었을 뿐이다

반대로 아래도 반환값은 똑같이 `null`이다.

```java
Map<String, String> statusByUser = new HashMap<>();

String previous = statusByUser.put("alice", "ONLINE");
System.out.println(previous); // null
```

이번에는 정말 새 key 추가다.

즉 두 코드 모두 `put()` 반환값은 `null`인데, 실제 상황은 다르다.

## 먼저 보는 정답 패턴 vs 오답 패턴

| 하고 싶은 말 | 오해하기 쉬운 코드 | beginner 기준 권장 코드 |
|---|---|---|
| "새 key인지 알고 싶다" | `if (map.put(k, v) == null)` | `boolean existed = map.containsKey(k); map.put(k, v);` |
| "이전 value도 같이 알고 싶다" | `String prev = map.put(k, v);`만 보고 해석 | `boolean existed = map.containsKey(k); String prev = map.put(k, v);` |

짧게 외우면 이렇다.

- `put()`만 보면 "이전 value"까지만 안다
- `containsKey()`를 먼저 보면 "원래 key가 있었는지"까지 안다

## 구분이 필요할 때 쓰는 패턴

가장 읽기 쉬운 초급 패턴은 "먼저 존재 여부를 확인하고, 그다음 `put()`"이다.

```java
boolean existed = statusByUser.containsKey("alice");
String previous = statusByUser.put("alice", "ONLINE");

if (!existed) {
    System.out.println("새 key 추가");
} else if (previous == null) {
    System.out.println("기존 key였고, 이전 value는 null");
} else {
    System.out.println("기존 key였고, 이전 value는 " + previous);
}
```

읽는 순서는 3단계다.

1. `containsKey()`로 key 존재 여부를 먼저 본다
2. `put()`으로 실제 저장을 수행한다
3. `previous` 값으로 덮어쓰기 전 value를 해석한다

실무 표현으로 바꾸면 아래처럼 읽으면 된다.

- `!existed` -> 이번 `put()`은 새 key 추가
- `existed && previous == null` -> 기존 key였고 이전 value만 `null`
- `existed && previous != null` -> 기존 key를 일반 덮어쓰기

## 왜 `containsKey()`를 "나중"이 아니라 "먼저" 보나

`put()`을 한 뒤에 `containsKey()`를 보면 이미 key가 들어간 뒤라 구분에 도움이 안 된다.

```java
Map<String, String> statusByUser = new HashMap<>();

String previous = statusByUser.put("alice", "ONLINE");
System.out.println(previous); // null
System.out.println(statusByUser.containsKey("alice")); // true
```

이 `true`는 두 경우를 모두 포함한다.

- 원래 없었는데 방금 추가한 경우
- 원래 있었고 값만 바꾼 경우

그래서 구분이 목적이면 `containsKey()`를 `put()` 전에 읽어야 한다.

## 자주 하는 오해

- "`put() == null`이면 무조건 새 key다"
  아니다. 기존 value가 `null`이었을 수도 있다.
- "`containsKey()`는 `put()` 뒤에 봐도 된다"
  아니다. 구분이 목적이면 덮어쓰기 전에 봐야 한다.
- "`get(key) == null`로 대신 확인하면 되지 않나요?"
  `null` value를 허용하는 `Map`에서는 이것도 애매하다.
- "`containsKey()`를 먼저 보면 `put()` 반환값은 필요 없나요?"
  아니다. 존재 여부와 이전 value는 다른 정보라서 둘 다 필요할 수 있다.
- "`TreeMap`이면 다르게 해석하나요?"
  `put()`의 이전 값 반환 규칙은 같다. 다만 key 같은 자리 판단 기준이 comparator일 수 있다.

## 빠른 선택 체크리스트

- "그냥 저장만 하면 된다" -> `put()`만 써도 된다
- "새 key였는지 기존 key 덮어쓰기인지 구분해야 한다" -> `containsKey()`를 먼저 본다
- "`null` value를 허용하지 않는 설계"라면 `put() == null`을 새 key 신호로 읽기 쉽다
- "`null` value를 허용하는 설계"라면 `put() == null` 단독 해석을 피한다

## 다음에 어디로 이어 읽으면 좋은가

| 지금 더 궁금한 질문 | 다음 문서 |
|---|---|
| "`Map` 메서드 반환값 전체를 한 번에 묶어 보고 싶다" | [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md) |
| "`get()`의 `null`과 `containsKey()` 차이도 같이 헷갈린다" | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) |
| "`TreeMap.put()`도 같은 규칙인가요?" | [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./treemap-put-return-value-overwrite-bridge.md) |

## 한 줄 정리

`put()`이 `null`을 돌려줘도 새 key 추가인지 기존 `null` value 덮어쓰기인지는 바로 알 수 없으므로, 그 차이가 중요할 때는 `containsKey()`를 저장 전에 함께 보는 습관이 가장 안전하다.
