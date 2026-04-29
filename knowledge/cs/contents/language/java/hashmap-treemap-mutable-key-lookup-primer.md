# Mutable Keys in HashMap and TreeMap

> 한 줄 요약: `HashMap`/`TreeMap`에 넣은 뒤 key의 `equals()`/`hashCode()`/`compareTo()` 기준 필드를 바꾸면, map은 key를 자동으로 옮겨 주지 않아서 `get`/`containsKey`/`remove`가 실패할 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: hashmap mutable key beginner, treemap mutable key beginner, hashmap get null 왜, hashmap containskey false 왜, treemap get null 왜, treemap key 바꿨더니 조회가 안 돼요, map에 넣은 key 바꿨더니 get null, map에 넣은 key 바꿨더니 containskey false, 같은 객체인데 containskey false, hashmap key 변경 왜 안 돼요, treemap key 수정 왜 안 돼요, 처음 배우는데 map key 왜 불변이어야 하나요, map key mutation primer, immutable key beginner, java map key mutation basics
> 관련 문서:
> - [Language README](../README.md)
> - [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md)
> - [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
> - [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Stable ID as Map Key Primer](./stable-id-map-key-primer.md)
> - [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
> - [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
> - [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

> retrieval-anchor-keywords: language-java-00074, mutable keys in maps primer, hashmap mutable key lookup bug, treemap mutable key lookup bug, mutate key after put hashmap, mutate key after put treemap, java equals hashCode compareTo mutation, hashmap get null after key mutation, hashmap containsKey false after mutation, hashmap remove fails after key mutation, treemap get null after key mutation, treemap containsKey false after mutation, treemap remove fails after key mutation, mutable key equals hashCode bug, mutable key compareTo bug, same object lookup still fails hashmap, same object lookup still fails treemap, immutable key beginner, java map key mutation primer, map lookup debug equals hashCode compareTo

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 요약 표](#한-장-요약-표)
- [예제에 쓸 mutable key](#예제에-쓸-mutable-key)
- [`HashMap`: 서랍 번호가 바뀌면 조회가 빗나간다](#hashmap-서랍-번호가-바뀌면-조회가-빗나간다)
- [`TreeMap`: 갈림길 기준이 바뀌면 조회가 길을 잃는다](#treemap-갈림길-기준이-바뀌면-조회가-길을-잃는다)
- [무엇을 절대 바꾸면 안 되나](#무엇을-절대-바꾸면-안-되나)
- [안전한 기본 패턴](#안전한-기본-패턴)
- [초보자가 자주 헷갈리는 지점](#초보자가-자주-헷갈리는-지점)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Map을 처음 배울 때는 보통 이렇게 이해한다.

- `HashMap`은 빠르게 찾는 map
- `TreeMap`은 정렬되는 map
- key 객체를 수정해도 map 안의 그 객체가 같이 바뀌었으니 조회도 될 것 같다

하지만 실제로는 아래 같은 surprise가 나온다.

- `HashMap`에 분명 key가 보이는데 `get(...)`이 `null`이다
- 같은 key 객체 reference를 넘겼는데도 `containsKey(key)`가 `false`다
- `TreeMap`에서 key를 바꾼 뒤 `get(...)`이 실패한다
- `TreeMap.firstKey()`가 현재 값 기준으로 가장 앞 key처럼 보이지 않는다

첫 질문이 `"HashMap get이 왜 null이에요?"`, `"같은 객체인데 containsKey가 왜 false예요?"`, `"TreeMap key 바꿨더니 조회가 왜 안 돼요?"`라면 깊은 구현 문서보다 이 primer가 먼저 잡히는 것이 목표다.

핵심은 하나다.

> map은 key의 현재 상태를 계속 감시해서 다시 배치하지 않는다.

`put(...)`할 때 계산했던 lookup 경로와, 나중에 key가 바뀐 뒤의 lookup 경로가 달라지면 조회가 깨질 수 있다.

## 먼저 잡을 mental model

초보자용 기억법은 map 종류마다 하나씩 잡으면 된다.

- `HashMap`
  - `hashCode()`로 "어느 서랍으로 갈지"를 고른다
  - `equals()`로 "그 서랍 안에서 정말 같은 key인지"를 확인한다
- `TreeMap`
  - `compareTo()`나 `Comparator`로 "왼쪽/오른쪽 어느 갈림길로 갈지"를 고른다

여기서 중요한 점은 둘 다 같다.

- `put(...)`할 때 계산한 자리나 경로는 map 안에 남는다
- key 필드가 바뀌어도 map이 그 key를 꺼내서 재배치하지는 않는다
- 그래서 "현재 key 값"과 "map 안의 저장 위치"가 서로 다른 이야기를 하게 된다

비유하면 이렇다.

- `HashMap`은 서랍장이다. 서랍 번호표를 바꾸면 검색자가 다른 서랍을 열 수 있다
- `TreeMap`은 갈림길이 많은 복도다. 방향 표지판을 바꾸면 검색자가 다른 길로 들어설 수 있다

## 한 장 요약 표

| Map | lookup이 의존하는 것 | `put(...)` 뒤에 안정적으로 유지해야 하는 것 | mutation 뒤 흔한 증상 |
|---|---|---|---|
| `HashMap` | `hashCode()` -> `equals()` | key의 `equals()`/`hashCode()` 기준 필드 | `get`/`containsKey`/`remove`가 `null` 또는 `false` |
| `TreeMap` | `compareTo()` 또는 `Comparator` | key의 정렬 기준 필드 | `get`/`containsKey`/`remove` 실패, 정렬 순서가 이상해 보임 |

필드 기준으로 보면 더 단순하다.

| mutable 필드가 참여하는 계약 | 왜 위험한가 |
|---|---|
| `hashCode()` | lookup이 다른 bucket으로 향할 수 있다 |
| `equals()` | bucket 안까지 갔더라도 "같은 key" 판정이 바뀔 수 있다 |
| `compareTo()` / `Comparator` | lookup이 다른 branch로 향할 수 있다 |

초보자용 안전 규칙은 이 한 줄이면 충분하다.

> map key의 identity를 정하는 필드는 map 안에 들어간 동안 바꾸지 않는다.

## 예제에 쓸 mutable key

아래 `MemberKey`는 일부러 나쁜 예제로 만든 key다.
`login`이 mutable인데도 `equals()`/`hashCode()`/`compareTo()`에 모두 참여한다.

```java
import java.util.Objects;

final class MemberKey implements Comparable<MemberKey> {
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
    public int compareTo(MemberKey other) {
        int loginResult = this.login.compareTo(other.login);
        if (loginResult != 0) {
            return loginResult;
        }
        return Long.compare(this.id, other.id);
    }

    @Override
    public String toString() {
        return "MemberKey{id=" + id + ", login=" + login + "}";
    }
}
```

실무에서는 이런 key를 피하는 것이 정답이다.
하지만 왜 위험한지 감각을 잡기에는 좋은 예제다.

## `HashMap`: 서랍 번호가 바뀌면 조회가 빗나간다

먼저 `HashMap`에 key를 넣는다.

```java
import java.util.HashMap;
import java.util.Map;

Map<MemberKey, String> teamByMember = new HashMap<>();

MemberKey key = new MemberKey(1L, "mina");
teamByMember.put(key, "backend");

System.out.println(teamByMember.get(new MemberKey(1L, "mina")));
System.out.println(teamByMember.containsKey(key));
```

처음에는 자연스럽다.

```text
backend
true
```

이제 map 안에 들어간 `key`의 `login`을 바꾼다.

```java
key.renameLogin("momo");

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
false
null
{MemberKey{id=1, login=momo}=backend}
```

초보자 눈에는 특히 두 가지가 이상하다.

- map 출력에는 key가 보이는데 `get(...)`이 `null`이다
- 같은 객체 reference인 `key`를 넣었는데도 `containsKey(key)`가 `false`다

이유는 간단하다.

1. `put(...)`할 때 `HashMap`은 `"mina"` 기준 `hashCode()`로 bucket을 정했다.
2. 나중에 `login`이 `"momo"`로 바뀌어도 entry는 옛 bucket에 그대로 남아 있다.
3. 이제 lookup은 `"mina"`든 `"momo"`든 현재 계산한 hash를 따라 다른 bucket으로 갈 수 있다.
4. `HashMap`은 모든 bucket을 끝까지 뒤져서 복구해 주지 않는다.

즉 `HashMap`은 "key object가 같은가"보다 먼저 "지금 이 key는 어느 bucket에 있어야 하나"를 본다.
그 bucket 계산이 달라지면 같은 객체 reference로도 못 찾을 수 있다.

## `TreeMap`: 갈림길 기준이 바뀌면 조회가 길을 잃는다

`TreeMap`에서는 bucket 대신 정렬 경로가 문제다.

```java
import java.util.NavigableMap;
import java.util.TreeMap;

NavigableMap<MemberKey, String> teamByMember = new TreeMap<>();

MemberKey middle = new MemberKey(2L, "mina");
MemberKey left = new MemberKey(1L, "anna");
MemberKey right = new MemberKey(3L, "zoe");

teamByMember.put(middle, "backend");
teamByMember.put(left, "platform");
teamByMember.put(right, "search");

System.out.println(teamByMember.get(new MemberKey(1L, "anna")));
```

처음에는 왼쪽 key를 잘 찾는다.

```text
platform
```

이제 `left`의 `login`을 바꾼다.

```java
left.renameLogin("yuri");

System.out.println(teamByMember.get(new MemberKey(1L, "anna")));
System.out.println(teamByMember.get(new MemberKey(1L, "yuri")));
System.out.println(teamByMember.containsKey(left));
System.out.println(teamByMember.firstKey());
System.out.println(teamByMember);
```

출력은 이렇게 보일 수 있다.

```text
null
null
false
MemberKey{id=1, login=yuri}
{MemberKey{id=1, login=yuri}=platform, MemberKey{id=2, login=mina}=backend, MemberKey{id=3, login=zoe}=search}
```

왜 이런 일이 생길까?

1. `put(left, ...)` 당시에는 `"anna"`가 `"mina"`보다 앞이므로 왼쪽 branch로 들어갔다.
2. 나중에 `"anna"`를 `"yuri"`로 바꾸면 현재 정렬 기준상 이 key는 `"mina"`보다 뒤로 가야 한다.
3. 하지만 `TreeMap`은 이미 들어간 node를 새 위치로 자동 이동하지 않는다.
4. 이제 `get(new MemberKey(1L, "yuri"))`는 현재 비교 결과를 따라 오른쪽으로 내려가지만, 실제 node는 예전 왼쪽 쪽에 남아 있어서 못 찾을 수 있다.

그래서 `TreeMap`에서는 두 종류의 이상 현상이 같이 보인다.

- lookup이 실패한다
- iteration이나 `firstKey()` 결과가 현재 필드 값 기준 정렬처럼 보이지 않을 수 있다

## `TreeMap`: 갈림길 기준이 바뀌면 조회가 길을 잃는다 (계속 2)

이 원리는 `compareTo()`를 쓰는 natural ordering뿐 아니라, `new TreeMap<>(comparator)`처럼 custom `Comparator`를 넘긴 경우에도 똑같다.

## 무엇을 절대 바꾸면 안 되나

여기서 기준을 collection별로 외우면 헷갈리기 쉽다.
더 쉬운 방법은 "lookup이 보는 필드"만 기억하는 것이다.

| 상황 | map 안에 들어간 뒤 바꾸면 안 되는 것 |
|---|---|
| `HashMap` key | `equals()`/`hashCode()`가 보는 필드 |
| `TreeMap` key with natural ordering | `compareTo()`가 보는 필드 |
| `TreeMap` key with custom comparator | 그 `Comparator`가 보는 필드 |
| map value | 보통 괜찮다. lookup은 value가 아니라 key를 본다 |

특히 `HashMap` key는 보통 이렇게 설계하는 것이 가장 안전하다.

- `equals()`와 `hashCode()`가 같은 stable identity 필드를 본다
- 그 identity 필드는 `final`이거나 사실상 immutable하다

## 안전한 기본 패턴

### 1. 가장 좋은 방법은 immutable key다

```java
record MemberId(long value) {}

Map<MemberId, Member> members = new HashMap<>();
```

변해야 하는 정보는 `Member` value 쪽에 두고, key는 변하지 않는 ID로 둔다.

### 2. key 자체를 바꿔야 한다면 remove -> mutate -> put 순서를 지킨다

```java
String team = teamByMember.remove(oldKey);
oldKey.renameLogin("new-login");
teamByMember.put(oldKey, team);
```

중요한 점은 "map 안에 들어 있는 상태로 바꾸지 않는다"는 것이다.

### 3. mutable entity 전체를 key로 쓰지 말고 stable identifier만 key로 쓴다

- `Map<MemberId, Member>`
- `Map<String, Order>`
- `Map<Long, Session>`

초보자 단계에서는 이 패턴이 가장 사고가 적다.

## 초보자 혼동 포인트

### 1. "map 출력에 보이는데 왜 조회가 안 되죠?"

iteration은 저장된 entry를 순회한다.
하지만 `get`/`containsKey`/`remove`는 해시나 비교 규칙으로 lookup 경로를 다시 계산한다.
두 경로가 달라졌기 때문이다.

### 2. "같은 객체 reference를 넘기면 찾을 수 있어야 하지 않나요?"

`HashMap`도 `TreeMap`도 lookup 전에 현재 `hashCode()`나 `compareTo()` 경로를 먼저 계산한다.
같은 reference인지부터 확인하지 않는다.

### 3. "그럼 mutable value도 안 되나요?"

보통 문제는 key mutation이다.
value는 lookup 경로를 정하지 않으므로, value 내부 상태 변경은 별개의 문제다.

### 4. "`equals()`만 바뀌고 `hashCode()`는 그대로면 괜찮나요?"

여전히 위험하다.
`HashMap`은 bucket 안에서 마지막으로 `equals()`를 본다.
같은 bucket까지 갔더라도 equality 판정이 달라지면 조회가 어긋날 수 있다.

초보자용 안전 규칙은 복잡하게 나누지 말고 다음처럼 외우면 된다.

> `HashMap` key의 정체성을 설명하는 필드는 전부 immutable하게 둔다.

## 빠른 체크리스트

- 이 객체를 map key로 쓰는가?
- 그렇다면 `equals()`/`hashCode()`/`compareTo()` 또는 `Comparator`가 어떤 필드를 보는지 먼저 적어 봤는가?
- 그 필드가 map 안에 들어간 뒤 바뀔 수 있는가?
- 바뀔 수 있다면 key가 아니라 stable ID를 써야 하는가?
- 정말 key를 바꿔야 한다면 map 밖에서 `remove -> change -> put`로 처리하는가?

## 어떤 문서를 다음에 읽으면 좋은가

- `HashMap` key 계약과 equality 감각을 먼저 다지려면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- mutable entity를 key 대신 value로 두는 기본 패턴부터 잡으려면 [Stable ID as Map Key Primer](./stable-id-map-key-primer.md)
- `compareTo()`와 `Comparator` 기본기를 같이 보려면 [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- `TreeMap`/`TreeSet`에서 natural ordering의 `compareTo() == 0`이 어떤 의미인지 보려면 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- sorted collection 안에서 mutable 비교 필드가 왜 더 위험한지 이어서 보려면 [Mutable Fields Inside Sorted Collections](./treeset-treemap-mutable-comparator-fields-primer.md)
- key를 애초에 불변으로 설계하는 감각을 잡으려면 [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

## 한 줄 정리

`HashMap`은 key의 해시와 동등성으로, `TreeMap`은 key의 비교 결과로 길을 찾기 때문에, 그 기준이 되는 mutable 필드를 `put(...)` 뒤에 바꾸면 map lookup이 깨질 수 있다.
