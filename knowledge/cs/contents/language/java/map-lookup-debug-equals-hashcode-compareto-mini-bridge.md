# Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서

> 한 줄 요약: "분명 넣은 key 같은데 왜 못 찾지?"가 나오면, 먼저 `HashMap` 계열인지 `TreeMap` 계열인지 자르고, `HashMap`이면 `equals()`/`hashCode()`, `TreeMap`이면 `compareTo()`/`Comparator`를 확인하는 순서가 초급 디버깅의 가장 안전한 시작점이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: map lookup debug equals hashcode compareto mini bridge basics, map lookup debug equals hashcode compareto mini bridge beginner, map lookup debug equals hashcode compareto mini bridge intro, java basics, beginner java, 처음 배우는데 map lookup debug equals hashcode compareto mini bridge, map lookup debug equals hashcode compareto mini bridge 입문, map lookup debug equals hashcode compareto mini bridge 기초, what is map lookup debug equals hashcode compareto mini bridge, how to map lookup debug equals hashcode compareto mini bridge
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
> - [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
> - [TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator](./treemap-record-containskey-get-name-comparator-drill.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)

> retrieval-anchor-keywords: map lookup debug equals hashCode compareTo mini bridge, containsKey false get null debug flow, hashmap get null equals hashCode checklist, treemap containsKey false compareTo checklist, java map lookup miss beginner, map key lookup debug order, hashmap treemap lookup debugging primer, 자바 map 조회 디버깅, 자바 containsKey false get null 원인, 자바 hashmap equals hashCode 확인 순서, 자바 treemap compareTo 확인 순서, map 조회 실패 초급 체크리스트

## 먼저 잡을 mental model

처음에는 이 한 문장만 기억하면 된다.

> `HashMap`은 "같은 key인가?"를 `equals()`/`hashCode()`로 찾고, `TreeMap`은 `compareTo()`/`Comparator`로 길을 찾는다.

그래서 증상은 비슷해도 확인 순서는 갈린다.

- `HashMap`/`LinkedHashMap`에서 못 찾으면 `equals()`/`hashCode()` 쪽부터 본다
- `TreeMap`에서 못 찾으면 `compareTo()`/`Comparator` 쪽부터 본다

## 10초 분기 표

| 지금 쓰는 Map | 먼저 볼 것 | 흔한 실수 |
|---|---|---|
| `HashMap`, `LinkedHashMap` | `equals()`/`hashCode()` | key 필드 바뀜, `equals()`만 고치고 `hashCode()`는 안 고침 |
| `TreeMap` | `compareTo()` 또는 생성자 `Comparator` | `equals()`만 보고 안심함, `compareTo() == 0` 규칙을 놓침 |

초보자용 디버깅 규칙은 이것이다.

1. `Map` 구현체를 먼저 확인한다.
2. `HashMap` 계열이면 `equals()`/`hashCode()`를 본다.
3. `TreeMap` 계열이면 `compareTo()`/`Comparator`를 본다.
4. 둘 다 key를 `put(...)` 뒤에 바꾸지 않았는지도 확인한다.

## 왜 `containsKey == false`와 `get == null`이 같이 나오나

아래 증상은 보통 같이 보인다.

```java
System.out.println(map.containsKey(key)); // false
System.out.println(map.get(key));         // null
```

이때 초보자가 먼저 헷갈리는 지점은 두 가지다.

- "같은 객체 reference인데 왜 못 찾지?"
- "출력해 보면 map 안에 key가 보이는데 왜 `get()`은 `null`이지?"

핵심은 map이 "현재 key 상태"를 실시간으로 다시 정리하지 않는다는 점이다.

- `HashMap`은 hash 경로가 빗나가면 못 찾을 수 있다
- `TreeMap`은 비교 경로가 빗나가면 못 찾을 수 있다

즉 `containsKey == false`와 `get == null`은 "map이 비었다"보다 "lookup 기준이 어긋났다" 쪽 신호일 때가 많다.

## 1단계: 먼저 Map 종류를 자르기

디버깅 첫 질문은 이것이면 충분하다.

```java
System.out.println(map.getClass().getName());
```

보는 포인트:

- `HashMap`, `LinkedHashMap`이면 `equals()`/`hashCode()` route
- `TreeMap`이면 `compareTo()`/`Comparator` route

여기서 바로 갈라지는데, 초보자는 종종 `equals()`만 붙잡고 오래 헤맨다.
하지만 `TreeMap`에서는 그 순서가 아니다.

## 2단계: `HashMap` 계열이면 `equals()`/`hashCode()`부터

`HashMap` 계열에서는 이 질문 순서가 안전하다.

| 질문 | 왜 보나 |
|---|---|
| key 필드가 `put(...)` 뒤에 바뀌었나? | `hashCode()` 결과가 달라질 수 있다 |
| `equals()`와 `hashCode()`가 같은 필드를 보나? | 계약이 어긋나면 조회가 흔들린다 |
| `equals()`만 구현하고 `hashCode()`를 빠뜨렸나? | `HashMap` 조회가 깨질 수 있다 |

짧은 예제를 보자.

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

final class UserKey {
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
}

Map<UserKey, String> map = new HashMap<>();
UserKey key = new UserKey("mina");
map.put(key, "saved");

key.rename("momo");

System.out.println(map.containsKey(key)); // false
System.out.println(map.get(key));         // null
```

읽는 법은 단순하다.

- `put(...)` 때는 `"mina"` 기준으로 저장됐다
- 지금 lookup은 `"momo"` 기준으로 찾는다
- 그래서 같은 객체여도 못 찾을 수 있다

## 3단계: `TreeMap`이면 `compareTo()`/`Comparator`를 본다

`TreeMap`은 질문 순서가 다르다.

| 질문 | 왜 보나 |
|---|---|
| key가 `Comparable`인가, 아니면 `Comparator`를 넘겼나? | 실제 lookup 규칙 출처를 알아야 한다 |
| `compareTo()`/`compare(...)`가 어떤 필드를 보나? | 조회 경로 자체가 여기로 정해진다 |
| 그 비교 기준 필드가 `put(...)` 뒤에 바뀌었나? | 트리 경로가 달라져 조회가 실패할 수 있다 |

짧은 예제:

```java
import java.util.Map;
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
    public int compareTo(UserKey other) {
        return this.login.compareTo(other.login);
    }
}

Map<UserKey, String> map = new TreeMap<>();
UserKey key = new UserKey("mina");
map.put(key, "saved");

key.rename("momo");

System.out.println(map.containsKey(key)); // false
System.out.println(map.get(key));         // null
```

여기서 핵심은 `equals()`가 아니라 `compareTo()`다.

- `TreeMap`은 `"mina"` 기준 경로에 넣었다
- 지금은 `"momo"` 기준 경로로 찾으려 한다
- 그러면 트리 안에서 다른 길로 들어갈 수 있다

## 4단계: 헷갈리면 이 순서대로 좁히기

| 증상 | 먼저 떠올릴 질문 | 다음 확인 |
|---|---|---|
| `HashMap`에서 `containsKey == false` | key가 바뀌었나? | `equals()`/`hashCode()`가 같은 필드를 보는가 |
| `TreeMap`에서 `containsKey == false` | 비교 기준 필드가 바뀌었나? | `compareTo()`/`Comparator`가 무엇을 보는가 |
| map 출력엔 key가 보이는데 `get == null` | 저장은 됐지만 lookup 경로가 달라졌나? | mutable key 여부 확인 |

## 자주 하는 오해

- "`get() == null`이면 그냥 key가 없는 거다"
  - 아니다. `null` value와 lookup miss를 먼저 구분해야 한다.
- "`equals()`가 맞으니 `TreeMap`도 괜찮다"
  - 아니다. `TreeMap`은 `compareTo()`/`Comparator`를 먼저 본다.
- "같은 객체 reference면 언제나 찾을 수 있다"
  - 아니다. lookup 기준 필드가 바뀌면 같은 객체여도 실패할 수 있다.

## 30초 체크리스트

- 지금 map이 `HashMap` 계열인지 `TreeMap`인지 확인했나?
- `HashMap`이면 `equals()`/`hashCode()`를 같이 봤나?
- `TreeMap`이면 `compareTo()` 또는 `Comparator`를 봤나?
- key의 비교 기준 필드를 `put(...)` 뒤에 바꾸지 않았나?
- 지금 문제는 "key 없음"인지, "기준 어긋남"인지 분리했나?

## 다음 읽기

- `HashMap`/`TreeMap`에 넣은 뒤 key를 바꾸는 전체 사례가 필요하면: [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
- `TreeMap`에서 `compareTo() == 0`이 왜 같은 key 자리인지 다시 잡고 싶으면: [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- `record` key + name-only comparator에서 조회만 따로 손예측해 보고 싶으면: [TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator](./treemap-record-containskey-get-name-comparator-drill.md)
- `get() == null`이 "key 없음"과 "null value" 중 무엇인지부터 구분하고 싶으면: [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)

## 한 줄 정리

`containsKey() == false`나 `get() == null`이 나왔을 때는 메서드 하나만 보지 말고, 먼저 map 종류를 자른 뒤 `HashMap`은 `equals()`/`hashCode()`, `TreeMap`은 `compareTo()`/`Comparator` 순서로 확인하면 초급 디버깅이 훨씬 빨라진다.
