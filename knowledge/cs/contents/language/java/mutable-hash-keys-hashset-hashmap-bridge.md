# Mutable Hash Keys Bridge

> 한 줄 요약: `HashSet` 원소나 `HashMap` key의 `equals()`/`hashCode()` 기준 필드를 넣은 뒤 바꾸면, 같은 객체가 안 보이거나 삭제가 실패하는 초보자 함정을 `hash 컬렉션` 관점만 좁혀 설명하는 bridge다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
> - [Mutable Elements in HashSet and TreeSet Primer](./mutable-elements-hashset-treeset-primer.md)
> - [HashSet Mutable Element Removal Drill](./hashset-mutable-element-removal-drill.md)
> - [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
> - [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

> retrieval-anchor-keywords: language-java-00079, mutable hash keys bridge, mutable hash key beginner, hashset mutable element bug, hashmap mutable key bug, mutate field used by equals hashCode, hashset contains false after mutation, hashset remove false after mutation, hashmap get null after key mutation, hashmap containsKey false after key mutation, hashmap remove null after key mutation, same object still not found hashmap, same object still not found hashset, equals hashCode mutable field beginner, java hash collection mutation trap, java mutable key bridge, java beginner hash key mutation, 자바 hashset 원소 변경 함정, 자바 hashmap key 변경 함정, equals hashCode 필드 변경 버그, hash 컬렉션 가변 키 기초

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 요약 표](#한-장-요약-표)
- [예제에 쓸 mutable key](#예제에-쓸-mutable-key)
- [`HashSet`: 분명 넣었는데 `contains()`가 깨진다](#hashset-분명-넣었는데-contains가-깨진다)
- [`HashMap`: 분명 보이는데 `get()`이 `null`이다](#hashmap-분명-보이는데-get이-null이다)
- [왜 같은 객체 reference인데도 못 찾나](#왜-같은-객체-reference인데도-못-찾나)
- [안전한 기본 패턴](#안전한-기본-패턴)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [다음에 읽으면 좋은 문서](#다음에-읽으면-좋은-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

초보자는 보통 이렇게 기대한다.

- `HashSet`에 넣은 객체를 나중에 조금 바꿔도 여전히 그 원소일 것이다
- `HashMap` key 객체를 바꿔도 같은 객체 reference니까 조회될 것이다

하지만 실제로는 이런 surprise가 나온다.

- `HashSet.contains(element)`가 `false`다
- `HashSet.remove(element)`가 실패한다
- `HashMap.get(key)`가 `null`이다
- `HashMap.containsKey(key)`가 `false`다
- 컬렉션을 출력하면 객체가 보이는데 조회는 안 된다

핵심은 하나다.

> `HashSet`과 `HashMap`은 객체를 넣을 때 계산한 hash 경로를 자동으로 다시 맞춰 주지 않는다.

그래서 `equals()`/`hashCode()` 기준 필드를 넣은 뒤 바꾸면,
"객체의 현재 상태"와 "컬렉션이 기억하는 자리"가 서로 어긋날 수 있다.

## 먼저 잡을 mental model

초보자용 기억법은 이 한 줄이면 충분하다.

> hash 컬렉션은 객체를 넣을 때 `hashCode()`로 서랍을 정하고, 그 뒤 필드 변화는 감시하지 않는다.

조금 더 풀면 이렇게 이해하면 된다.

- `hashCode()`는 먼저 어느 서랍(bucket)으로 갈지 정한다
- `equals()`는 그 서랍 안에서 정말 같은 원소인지 확인한다
- 넣은 뒤 key/원소의 기준 필드가 바뀌어도 컬렉션은 그 객체를 다시 재배치하지 않는다

즉 "같은 객체를 들고 있다"와 "같은 서랍으로 다시 찾아간다"는 다른 문제다.

## 한 장 요약 표

| 컬렉션 | 안정적으로 유지해야 하는 필드 | mutation 뒤 흔한 증상 |
|---|---|---|
| `HashSet` 원소 | `equals()`/`hashCode()`가 보는 필드 | `contains`, `remove` 실패 |
| `HashMap` key | `equals()`/`hashCode()`가 보는 필드 | `get`, `containsKey`, `remove` 실패 |

| 바꾼 필드가 어디에 쓰이나 | 왜 위험한가 |
|---|---|
| `hashCode()`에만 참여 | 다른 bucket으로 찾아갈 수 있다 |
| `equals()`에만 참여 | bucket 안에서 같은 원소 판정이 달라질 수 있다 |
| `equals()`와 `hashCode()` 둘 다 참여 | 조회와 삭제가 가장 쉽게 깨진다 |

초보자용 안전 규칙은 아래 한 줄이다.

> `HashSet` 원소와 `HashMap` key의 identity 필드는 컬렉션 안에 있는 동안 바꾸지 않는다.

## 예제에 쓸 mutable key

아래 `MemberKey`는 일부러 위험한 예제다.
`login`이 mutable인데 `equals()`와 `hashCode()`에 모두 참여한다.

```java
import java.util.Objects;

final class MemberKey {
    private final long id;
    private String login;

    MemberKey(long id, String login) {
        this.id = id;
        this.login = login;
    }

    void renameLogin(String login) {
        this.login = login;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof MemberKey other)) return false;
        return id == other.id && Objects.equals(login, other.login);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, login);
    }

    @Override
    public String toString() {
        return "MemberKey{id=" + id + ", login=" + login + "}";
    }
}
```

실무 기본값은 이런 key를 피하는 것이다.
하지만 초보자 함정을 이해하기에는 좋은 예제다.

## `HashSet`: 분명 넣었는데 `contains()`가 깨진다

```java
import java.util.HashSet;
import java.util.Set;

Set<MemberKey> members = new HashSet<>();

MemberKey key = new MemberKey(1L, "mina");
members.add(key);

System.out.println(members.contains(key));
System.out.println(members.contains(new MemberKey(1L, "mina")));
```

처음에는 자연스럽다.

```text
true
true
```

이제 `HashSet` 안에 들어간 객체를 바꾼다.

```java
key.renameLogin("momo");

System.out.println(members.contains(key));
System.out.println(members.contains(new MemberKey(1L, "mina")));
System.out.println(members.contains(new MemberKey(1L, "momo")));
System.out.println(members.remove(key));
System.out.println(members);
```

출력은 이렇게 보일 수 있다.

```text
false
false
false
false
[MemberKey{id=1, login=momo}]
```

이상하게 보이지만 이유는 단순하다.

1. `add(...)`할 때는 `"mina"` 기준 hash로 bucket을 정했다.
2. 원소는 그 bucket 안에 그대로 남아 있다.
3. 지금 `contains(...)`와 `remove(...)`는 `"momo"` 기준 hash로 다른 bucket을 찾을 수 있다.
4. 그래서 같은 객체 reference를 넘겨도 못 찾을 수 있다.

## `HashMap`: 분명 보이는데 `get()`이 `null`이다

`HashMap`도 같은 원리다.

```java
import java.util.HashMap;
import java.util.Map;

Map<MemberKey, String> teamByMember = new HashMap<>();

MemberKey key = new MemberKey(1L, "mina");
teamByMember.put(key, "backend");

System.out.println(teamByMember.get(key));
System.out.println(teamByMember.get(new MemberKey(1L, "mina")));
```

처음에는 잘 찾는다.

```text
backend
backend
```

이제 key 객체를 바꾼다.

```java
key.renameLogin("momo");

System.out.println(teamByMember.get(key));
System.out.println(teamByMember.get(new MemberKey(1L, "mina")));
System.out.println(teamByMember.get(new MemberKey(1L, "momo")));
System.out.println(teamByMember.containsKey(key));
System.out.println(teamByMember.remove(key));
System.out.println(teamByMember);
```

출력은 이렇게 보일 수 있다.

```text
null
null
null
false
null
{MemberKey{id=1, login=momo}=backend}
```

초보자가 꼭 잡아야 할 포인트는 둘이다.

- map 출력에 key가 보인다고 `get()`이 되는 것은 아니다
- 같은 key 객체 reference라고 `containsKey(key)`가 되는 것도 아니다

## 왜 같은 객체 reference인데도 못 찾나

`HashSet`과 `HashMap`은 "객체 identity"로 바로 찾지 않는다.
항상 먼저 현재 `hashCode()`로 bucket을 계산한다.

즉 lookup 순서는 대략 이렇다.

1. 지금 넘긴 객체의 현재 `hashCode()`를 계산한다
2. 그 hash에 맞는 bucket으로 간다
3. 그 bucket 안에서 `equals()`로 같은지 확인한다

문제는 entry나 원소가 옛 bucket에 남아 있다는 점이다.

- 컬렉션 안 객체의 상태는 `"momo"`로 바뀌었다
- 하지만 삽입 당시 bucket은 `"mina"` 기준으로 정해졌다
- 현재 lookup은 `"momo"` 기준 bucket으로 간다
- 그래서 bucket 자체를 잘못 찾아갈 수 있다

즉 "같은 객체 reference"라는 사실은 hash 경로가 맞아야 의미가 있다.

## 안전한 기본 패턴

가장 안전한 기본값은 두 가지다.

1. key/원소를 불변으로 만든다
2. 꼭 바꿔야 하면 컬렉션에서 제거한 뒤 새 상태로 다시 넣는다

불변 설계 예시는 아래처럼 생각하면 된다.

```java
record MemberKey(long id, String login) {}
```

상태가 바뀌면 기존 객체를 고치지 말고 새 객체를 만든다.

```java
MemberKey before = new MemberKey(1L, "mina");
MemberKey after = new MemberKey(1L, "momo");
```

mutable 객체를 꼭 써야 한다면, 적어도 아래 패턴은 지킨다.

- `HashSet` 원소를 바꾸기 전에 `remove(...)`
- 필드 수정
- 다시 `add(...)`

- `HashMap` key를 바꾸지 말고
- old key로 `remove(...)`한 뒤
- new key 객체로 `put(...)`

## 초보자가 자주 헷갈리는 지점

- `HashSet`은 원소를 객체 identity로 찾는다고 생각한다
- `HashMap`은 key reference만 같으면 항상 조회된다고 생각한다
- `toString()` 출력에 보이면 `contains()`나 `get()`도 될 거라고 생각한다
- `equals()`만 맞으면 되고 `hashCode()`는 덜 중요하다고 생각한다
- "조금만 바꿨으니 같은 key"라는 사람 기준과 컬렉션 기준이 같다고 생각한다

## 빠른 체크리스트

- 이 객체가 `HashSet` 원소인가
- 이 객체가 `HashMap` key인가
- 바꾸려는 필드가 `equals()`/`hashCode()`에 들어가나
- 들어간다면 컬렉션 안에 있는 동안 바꾸지 않는가
- 꼭 바꿔야 한다면 제거 후 재삽입 패턴으로 처리했는가
- 가능하면 애초에 불변 객체로 설계했는가

## 다음에 읽으면 좋은 문서

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`HashSet.contains()`와 `remove()`가 왜 같이 실패하는지 짧게 먼저 연습하고 싶다" | [HashSet Mutable Element Removal Drill](./hashset-mutable-element-removal-drill.md) |
| "`==`와 `equals()`부터 다시 잡고 싶다" | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| "`HashMap`뿐 아니라 `TreeMap`까지 같이 보고 싶다" | [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md) |
| "정렬 컬렉션에서 비슷한 문제가 어떻게 생기지?" | [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md) |
| "왜 `HashSet`과 `TreeSet` 중복 규칙이 다르지?" | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |
| "애초에 가변 상태를 줄이는 설계가 왜 중요하지?" | [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md) |

## 한 줄 정리

`HashSet` 원소와 `HashMap` key는 넣는 순간의 `equals()`/`hashCode()` 기준으로 자리를 잡으므로, 그 기준 필드를 나중에 바꾸면 "분명 들어 있는데 못 찾는" 초보자 함정이 생긴다.
