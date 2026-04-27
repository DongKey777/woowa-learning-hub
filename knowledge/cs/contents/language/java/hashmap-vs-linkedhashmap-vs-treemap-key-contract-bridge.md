# HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge

> 한 줄 요약: `HashMap`과 `LinkedHashMap`은 `equals()`/`hashCode()`로 key를 찾고, `TreeMap`은 `compareTo()`/`Comparator`로 key를 찾으며, 세 구현체 모두 key 기준 필드는 map 안에 있는 동안 안정적이어야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
- [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
- [Stable ID as Map Key Primer](./stable-id-map-key-primer.md)
- [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)

retrieval-anchor-keywords: language-java-00110, hashmap vs linkedhashmap vs treemap key contract bridge, hashmap linkedhashmap treemap comparison beginner, hashmap linkedhashmap treemap lookup rule, hashmap linkedhashmap treemap iteration order, hashmap linkedhashmap treemap immutable key, linkedhashmap lookup equals hashcode, treemap lookup compareto comparator, map implementation key contract bridge, java map key contract beginner, java map iteration order comparison, java hashmap linkedhashmap treemap 차이, 자바 hashmap linkedhashmap treemap 비교, 자바 map 조회 규칙, 자바 map 반복 순서 차이, 자바 map immutable key, 자바 treemap compareto comparator key, 자바 linkedhashmap insertion order lookup, 자바 map key는 왜 불변이어야 하나, beginner map key contract primer

## 먼저 잡는 멘탈 모델

처음에는 map마다 아래 세 질문만 같이 보면 된다.

1. key를 **어떤 규칙으로 찾는가**
2. key를 **어떤 순서로 꺼내 보는가**
3. key가 map 안에 있는 동안 **무엇이 바뀌면 안 되는가**

초보자용 결론은 이 표 한 장으로 충분하다.

| 구현체 | key를 찾는 규칙 | 반복 순서 | key가 안정적으로 유지해야 하는 것 |
|---|---|---|---|
| `HashMap` | `hashCode()` -> `equals()` | 보장 없음 | `equals()`/`hashCode()`가 보는 필드 |
| `LinkedHashMap` | `hashCode()` -> `equals()` | 기본은 삽입 순서 | `equals()`/`hashCode()`가 보는 필드 |
| `TreeMap` | `compareTo()` 또는 `Comparator` | key 정렬 순서 | `compareTo()`/`Comparator`가 보는 필드 |

짧게 외우면 이렇게 정리된다.

- `HashMap`: "순서는 안 믿고, hash/equality로 찾는다"
- `LinkedHashMap`: "찾는 규칙은 `HashMap`과 같고, 보는 순서만 유지한다"
- `TreeMap`: "정렬 규칙으로 찾고, 정렬 순서로 본다"

## `LinkedHashMap`은 `HashMap`의 "순서 버전"이지 "다른 조회 규칙"이 아니다

입문자가 자주 놓치는 포인트는 이것이다.

- `HashMap`과 `LinkedHashMap`은 key lookup 규칙이 같다
- 둘의 차이는 주로 **iteration order**
- 그래서 mutable key 문제도 둘이 거의 같은 방향으로 터진다

즉 `LinkedHashMap`을 쓴다고 해서 "순서가 있으니 key 조회도 더 안전해진다"는 뜻은 아니다.
순서가 달라질 뿐, key를 찾는 계약은 여전히 `equals()`/`hashCode()` 쪽이다.

## 한 화면 비교표

| 질문 | `HashMap` | `LinkedHashMap` | `TreeMap` |
|---|---|---|---|
| `put/get/containsKey`가 의존하는 것 | `equals()`/`hashCode()` | `equals()`/`hashCode()` | `compareTo()` 또는 `Comparator` |
| 반복할 때 순서를 기대해도 되나 | 아니오 | 예, 기본은 삽입 순서 | 예, 정렬 순서 |
| key 필드를 바꿨을 때 흔한 증상 | `get()`이 `null`, `containsKey()`가 `false` | `HashMap`과 같은 조회 실패 + 순서는 그대로 보일 수 있음 | `get()` 실패, 정렬/탐색 경로 어긋남 |
| 첫 선택 상황 | 순서보다 일반 조회가 중요 | 넣은 순서대로 보여 줘야 함 | 정렬된 key 탐색이 중요 |

## 같은 데이터로 바로 보기

```java
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.TreeMap;

Map<String, Integer> hashMap = new HashMap<>();
Map<String, Integer> linkedHashMap = new LinkedHashMap<>();
Map<String, Integer> treeMap = new TreeMap<>();

hashMap.put("banana", 2);
hashMap.put("apple", 1);
hashMap.put("carrot", 3);

linkedHashMap.put("banana", 2);
linkedHashMap.put("apple", 1);
linkedHashMap.put("carrot", 3);

treeMap.put("banana", 2);
treeMap.put("apple", 1);
treeMap.put("carrot", 3);

System.out.println(linkedHashMap.get("apple")); // 1
System.out.println(treeMap.get("apple"));       // 1

System.out.println(linkedHashMap.keySet());     // [banana, apple, carrot]
System.out.println(treeMap.keySet());           // [apple, banana, carrot]
System.out.println(hashMap.keySet());           // 순서를 기대하면 안 됨
```

여기서 읽는 포인트는 두 축이다.

- lookup: 세 map 모두 `get("apple")`은 정상 동작한다
- iteration: 꺼내 보는 순서는 구현체마다 다르다

즉 "조회 규칙"과 "반복 순서"는 같은 질문이 아니다.

## 왜 immutable key가 세 구현체 모두에서 중요할까

`Map`이 key를 찾는 방식은 구현체마다 다르지만, 공통점도 하나 있다.

> map은 key 객체 안의 기준 필드가 바뀌었다고 해서 entry를 자동으로 다시 배치하지 않는다.

그래서 아래처럼 생각하면 안전하다.

- `HashMap`/`LinkedHashMap`: key의 `equals()`/`hashCode()` 기준 필드는 넣은 뒤 바꾸지 않는다
- `TreeMap`: key의 `compareTo()`/`Comparator` 기준 필드는 넣은 뒤 바꾸지 않는다

비유하면 이렇다.

- `HashMap`/`LinkedHashMap`은 "서랍 번호표"를 보고 찾는다
- `TreeMap`은 "정렬된 복도의 갈림길 표지판"을 보고 찾는다
- 표지판만 바꾸고 물건 위치를 안 옮기면 검색자가 길을 잃는다

## 작은 예제로 보는 key contract 차이

```java
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

final class UserKey implements Comparable<UserKey> {
    private String login;

    UserKey(String login) {
        this.login = login;
    }

    void rename(String login) {
        this.login = login;
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof UserKey other)) return false;
        return Objects.equals(login, other.login);
    }

    @Override
    public int hashCode() {
        return Objects.hash(login);
    }

    @Override
    public int compareTo(UserKey other) {
        return this.login.compareTo(other.login);
    }
}

UserKey key = new UserKey("mina");

Map<UserKey, String> hashMap = new HashMap<>();
Map<UserKey, String> linkedHashMap = new LinkedHashMap<>();
Map<UserKey, String> treeMap = new TreeMap<>();

hashMap.put(key, "saved");
linkedHashMap.put(key, "saved");
treeMap.put(key, "saved");

key.rename("momo");

System.out.println(hashMap.containsKey(key));       // false가 될 수 있다
System.out.println(linkedHashMap.containsKey(key)); // false가 될 수 있다
System.out.println(treeMap.containsKey(key));       // false가 될 수 있다
```

셋 다 이유는 조금씩 다르다.

- `HashMap`: 바뀐 `hashCode()`/`equals()` 기준으로 다른 bucket을 찾을 수 있다
- `LinkedHashMap`: 내부 조회 규칙이 같아서 같은 문제가 난다
- `TreeMap`: 바뀐 `compareTo()` 기준으로 다른 경로를 찾을 수 있다

즉 "순서를 유지하는 map"이라고 해서 mutable key 문제를 피하는 것은 아니다.

## 어떤 요구에 어떤 구현체를 먼저 고를까

| 요구사항 한 줄 | 첫 선택 | 이유 |
|---|---|---|
| "순서는 상관없고 key로 조회가 중심이다" | `HashMap` | 가장 기본적인 일반 목적 map |
| "입력한 순서대로 보여 줘야 한다" | `LinkedHashMap` | lookup은 그대로 두고 반복 순서만 안정화 |
| "이름순/번호순으로 key를 탐색해야 한다" | `TreeMap` | 정렬된 key 순서와 탐색 API가 강점 |

그리고 세 구현체 모두에서 초보자 기본값은 이 문장이다.

> key에는 변하지 않는 값, 가능하면 immutable 객체나 stable ID를 둔다.

## 자주 하는 혼동

- "`LinkedHashMap`은 `TreeMap`처럼 정렬도 해 주나요?"
  - 아니다. 기본은 삽입 순서 유지다.
- "`LinkedHashMap`은 순서가 있으니 lookup도 순서 기준인가요?"
  - 아니다. lookup 규칙은 `HashMap`과 같다.
- "`TreeMap`도 `equals()`만 맞으면 찾을 수 있나요?"
  - 아니다. 실제 경로는 `compareTo()`/`Comparator`가 정한다.
- "같은 객체 reference를 key로 넣었으니 나중에도 찾을 수 있지 않나요?"
  - 아니다. 비교 기준 필드가 바뀌면 같은 객체여도 실패할 수 있다.

## 20초 체크리스트

- 지금 필요한 것이 "조회"인지, "반복 순서"인지, "정렬 탐색"인지 먼저 구분했나?
- `LinkedHashMap`과 `HashMap`의 lookup 규칙이 같다는 점을 구분했나?
- `TreeMap`은 `compareTo()`/`Comparator` 계약을 먼저 본다는 점을 기억했나?
- key로 쓰는 필드가 map 안에 있는 동안 바뀌지 않는가?
- 헷갈리면 `Map<StableId, Value>` 구조로 단순화할 수 있는가?

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "반복 순서 차이만 더 짧게 보고 싶다" | [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md) |
| "`containsKey()`/`get()`이 왜 실패하는지 디버깅 순서가 필요하다" | [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md) |
| "mutable key 버그를 더 자세히 보고 싶다" | [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md) |
| "entity 대신 stable ID를 key로 두는 설계 감각이 필요하다" | [Stable ID as Map Key Primer](./stable-id-map-key-primer.md) |

## 한 줄 정리

`HashMap`/`LinkedHashMap`은 hash+equality로 찾고 `TreeMap`은 ordering으로 찾으며, 반복 순서는 다르더라도 세 구현체 모두 key 기준 필드는 map 안에서 안정적으로 유지해야 조회가 흔들리지 않는다.
