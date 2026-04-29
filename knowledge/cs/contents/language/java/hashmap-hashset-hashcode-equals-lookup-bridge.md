# `HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까

> 한 줄 요약: Java 입문자가 `equals()`/`hashCode()` 기초 다음 단계에서 `HashMap`/`HashSet`이 실제로는 "`hashCode()`로 후보를 찾고 `equals()`로 마지막 확인을 한다"는 lookup 흐름을 한 장으로 연결하도록 만든 beginner bridge다.

**난이도: 🟢 Beginner**

관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)

retrieval-anchor-keywords: hashmap hashset hashcode equals lookup bridge, hashcode then equals lookup flow, hash collection lookup beginner, hashmap get hashcode equals order, hashset contains hashcode equals order, same hash not duplicate beginner, equals hashcode why both in hash map set, hashmap put get containskey lookup flow, hashset add contains duplicate flow, 자바 hashmap hashcode equals 조회 흐름, 자바 hashset hashcode equals 중복 판단 흐름, hashcode 다음 equals 왜 보나, hash bucket equals lookup 기초, contains false get null hashcode equals, hash collision duplicate 아님
> 관련 문서:
> - [Language README](../README.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [`new`/별칭에서 `HashSet`/`HashMap#get`까지: Equality Lookup Bridge Drill](./new-aliasing-equality-hashset-hashmap-get-bridge-drill.md)
> - [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
> - [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
> - [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)
> - [Java Collections 성능 감각](./collections-performance.md)

## 먼저 잡을 mental model

처음에는 이 두 줄만 기억하면 된다.

- `HashMap`과 `HashSet`은 먼저 `hashCode()`로 후보 bucket을 찾는다.
- 그 bucket 안에서 `equals()`로 정말 같은 key/원소인지 마지막 확인을 한다.

즉 `hashCode()`가 "후보 좁히기", `equals()`가 "최종 판정"이다.

## 왜 `hashCode()` 하나로 끝나지 않나

초보자는 종종 이렇게 오해한다.

- "`hashCode()`가 같으면 같은 값 아닌가?"
- "`equals()`가 같으면 왜 `hashCode()`도 신경 써야 하지?"

핵심은 역할이 다르기 때문이다.

| 메서드 | 역할 | 초보자 메모 |
|---|---|---|
| `hashCode()` | 먼저 어느 bucket을 볼지 정한다 | 빠르게 후보를 좁히는 단계 |
| `equals()` | bucket 안에서 정말 같은지 확인한다 | 마지막 판정 단계 |

그래서 둘 중 하나만 맞아도 충분한 것이 아니라, 해시 컬렉션에서는 둘이 같이 맞아야 한다.

## `HashSet`은 중복을 어떻게 보나

`HashSet.add(element)`를 아주 단순화하면 흐름은 이렇다.

1. `element.hashCode()`로 후보 bucket을 찾는다.
2. 그 bucket 안의 기존 원소들과 `equals()`를 비교한다.
3. `equals()`가 `true`인 원소가 있으면 중복으로 보고 넣지 않는다.
4. 없으면 새 원소를 넣는다.

`contains(element)`도 거의 같은 lookup 흐름을 탄다.

1. `hashCode()`로 bucket을 찾는다.
2. 그 안에서 `equals()`가 `true`인 원소를 찾는다.

짧은 예제:

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

final class User {
    private final long id;

    User(long id) {
        this.id = id;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User other)) return false;
        return id == other.id;
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}

Set<User> users = new HashSet<>();
users.add(new User(1L));
users.add(new User(1L));

System.out.println(users.size()); // 1
```

여기서 `HashSet`이 1개만 남기는 이유는 "`hashCode()`도 같고, 같은 bucket 안에서 `equals()`도 `true`"이기 때문이다.

## `HashMap`은 key를 어떻게 찾나

`HashMap.get(key)`도 큰 그림은 같다.

1. `key.hashCode()`로 후보 bucket을 찾는다.
2. 그 bucket 안에서 `equals()`가 `true`인 key를 찾는다.
3. 찾으면 그 key에 연결된 value를 돌려준다.

`put(key, value)`도 마찬가지다.

- 같은 bucket 안에 `equals()`가 `true`인 key가 있으면 value를 덮어쓴다.
- 없으면 새 entry를 추가한다.

짧은 예제:

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

final class UserKey {
    private final long id;

    UserKey(long id) {
        this.id = id;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UserKey other)) return false;
        return id == other.id;
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}

Map<UserKey, String> names = new HashMap<>();
names.put(new UserKey(1L), "mina");
names.put(new UserKey(1L), "momo");

System.out.println(names.size()); // 1
System.out.println(names.get(new UserKey(1L))); // momo
```

초보자용 읽는 법:

- 두 key는 다른 객체여도 `equals()`가 `true`다
- `HashMap`은 같은 key 자리라고 보고 value를 덮어쓴다

## 같은 `hashCode()`라고 바로 같은 값은 아니다

이 부분이 특히 중요하다.

> 같은 `hashCode()`는 "같은 bucket 후보"일 뿐, "같은 key/원소 확정"이 아니다.

즉 이런 장면이 가능하다.

- `hashCode()`는 같다
- 하지만 `equals()`는 `false`다
- 그러면 `HashSet`에는 둘 다 들어갈 수 있다
- `HashMap`에서도 서로 다른 key로 공존할 수 있다

초보자는 "`hash 충돌 = 중복`"으로 외우기 쉬운데, 실제 마지막 판정자는 `equals()`다.

## 그래서 `equals()`와 `hashCode()`를 같이 구현하라고 한다

이제 계약 문장이 왜 필요한지 흐름으로 이해할 수 있다.

- `equals()`가 `true`인데 `hashCode()`가 다르면 lookup 시작 bucket부터 어긋날 수 있다
- `equals()`와 `hashCode()`가 서로 다른 필드를 보면 중복 제거와 조회가 흔들릴 수 있다

처음 배우는 단계에서는 아래 규칙만 먼저 고정하면 된다.

1. `equals()`를 오버라이드하면 `hashCode()`도 같이 오버라이드한다.
2. 두 메서드는 같은 의미의 필드를 기준으로 만든다.
3. `HashMap` key와 `HashSet` 원소는 가능한 불변으로 둔다.

## 자주 하는 오해

- "`hashCode()`가 같으면 중복이다"
  - 아니다. `equals()`가 마지막 확인을 한다.
- "`equals()`만 맞으면 `HashMap`/`HashSet`도 괜찮다"
  - 아니다. lookup 시작점이 `hashCode()`라서 둘이 같이 맞아야 한다.
- "같은 객체 reference면 언제나 찾을 수 있다"
  - 아니다. mutable key/원소면 lookup 흐름이 어긋날 수 있다.

## 20초 체크리스트

- 지금 문제를 `HashMap`/`HashSet` 관점으로 보고 있는가?
- `hashCode()`를 후보 bucket 찾기라고 이해했는가?
- `equals()`를 최종 판정이라고 이해했는가?
- `equals()`와 `hashCode()`가 같은 필드를 보는가?
- key/원소의 기준 필드를 넣은 뒤 바꾸지 않았는가?

## 다음 읽기

- `equals()`/`hashCode()` 기초를 먼저 다시 다지고 싶으면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- aliasing에서 hash lookup까지 한 번에 묶어 예측하는 연습이 필요하면 [`new`/별칭에서 `HashSet`/`HashMap#get`까지: Equality Lookup Bridge Drill](./new-aliasing-equality-hashset-hashmap-get-bridge-drill.md)
- `HashMap` 조회 실패 증상을 바로 디버깅 순서로 연결하고 싶으면 [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
- mutable key 때문에 lookup이 깨지는 사례를 보고 싶으면 [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
- `TreeSet`/`TreeMap`은 왜 다른 규칙을 쓰는지 비교하고 싶으면 [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)

## 한 줄 정리

`HashMap`과 `HashSet`은 `hashCode()`로 후보를 찾고 `equals()`로 마지막 확인을 하므로, 해시 컬렉션에서 "같다"를 안전하게 다루려면 두 메서드를 한 흐름으로 같이 이해해야 한다.
