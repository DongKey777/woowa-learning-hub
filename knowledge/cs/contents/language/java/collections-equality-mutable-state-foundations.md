# Collections, Equality, and Mutable-State Foundations

> 한 줄 요약: Java 미션 코드에서 `List`/`Set`/`Map`을 고르는 첫 기준, `equals()`/`hashCode()`/`Comparable`이 컬렉션 동작에 미치는 영향, mutable key와 순회 중 수정 함정을 한 번에 묶어 주는 beginner primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
- [Stable ID as Map Key Primer](./stable-id-map-key-primer.md)
- [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md)
- [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
- [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
- [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)
- [Collection Update Strategy Primer](./collection-update-strategy-primer.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

retrieval-anchor-keywords: language-java-00109, collections equality mutable state foundations, java collections equality primer, java mutable key beginner, mutable hash key beginner, java map iteration update primer, java list set map equals hashcode comparable, beginner collection equality contract, java collection mission code primer, woowacourse backend collections primer, list set map choice equals hashcode compareto, java set duplicate rule beginner, java map key mutation bug beginner, hashset mutable element bug, list contains false after mutation java

## 먼저 잡는 멘탈 모델

컬렉션 문제를 읽을 때는 "자료구조 이름"보다 아래 3가지를 먼저 본다.

1. 데이터를 어떤 모양으로 보관할까
2. 어떤 경우를 "같다"라고 볼까
3. 보관한 뒤 상태를 바꿔도 안전할까

이 3축이 같이 맞아야 컬렉션 코드가 덜 흔들린다.

- `List`: 순서가 핵심인 목록
- `Set`: 중복 판단 규칙이 핵심인 집합
- `Map`: key로 찾는 조회 규칙이 핵심인 사전

즉 컬렉션 선택은 자료를 담는 통만 고르는 일이 아니라,
"이 값의 동등성/정렬/변경 가능성"까지 같이 정하는 일이다.

## 한 장으로 보는 첫 판단표

| 질문 | 먼저 볼 것 | 보통의 첫 선택 |
|---|---|---|
| 순서/인덱스가 중요한가? | `List` | `ArrayList` |
| 중복을 자동으로 막아야 하나? | `Set` | `HashSet` |
| key로 바로 찾아야 하나? | `Map` | `HashMap` |
| 정렬된 순서가 핵심인가? | `Comparable`/`Comparator` + sorted collection | `TreeSet`, `TreeMap` |
| 해시 컬렉션에서 중복/조회가 이상한가? | `equals()`/`hashCode()` | 관련 필드 불변화 |
| sorted collection에서 중복/조회가 이상한가? | `compareTo()`/`Comparator` | tie-breaker, 정렬 기준 점검 |
| 순회 중 삭제/추가가 필요한가? | 안전한 수정 통로 | `Iterator.remove()`, `removeIf(...)` |

## 컬렉션 선택과 비교 규칙은 붙어 있다

초보자는 보통 `List`/`Set`/`Map`만 고르면 끝났다고 생각하기 쉽다.
하지만 실제 동작은 "무엇을 같은 값으로 보느냐"에 따라 바로 달라진다.

| 컬렉션 | 무엇이 핵심 규칙인가 | 초보자 실수 |
|---|---|---|
| `List` | 순서와 위치 | 중복 제거가 자동일 거라고 기대 |
| `HashSet` / `HashMap` | `equals()` + `hashCode()` | `equals()`만 바꾸고 `hashCode()`를 안 맞춤 |
| `TreeSet` / `TreeMap` | `compareTo()` 또는 `Comparator` | `compare == 0`이면 같은 자리라는 점을 놓침 |

예를 들어 `Set`이라고 해도 전부 같은 방식으로 중복을 판단하지 않는다.

- `HashSet`: `equals()`와 `hashCode()` 기준
- `TreeSet`: `compareTo()` 또는 `Comparator.compare(...) == 0` 기준

그래서 "둘 다 `Set`인데 왜 하나는 남고 하나는 사라지지?"라는 surprise가 생긴다.

## 미션 코드에서 자주 나오는 4가지 선택

| 요구 문장 | 먼저 떠올릴 타입 | 같이 점검할 것 |
|---|---|---|
| 방문 순서대로 출력해야 한다 | `List` | 인덱스/순서만 중요하면 중복 허용 여부를 명시 |
| 이미 본 id는 다시 처리하면 안 된다 | `Set` | id 클래스의 `equals()`/`hashCode()` |
| id로 객체를 바로 찾는다 | `Map` | key 필드가 mutable인지 |
| 이름순으로 보여 준다 | `TreeSet`/`TreeMap` 또는 정렬된 `List` | `compareTo()`/`Comparator`와 tie-breaker |

중요한 포인트는 마지막 줄이다.
"정렬해서 보여 준다"는 요구는 단순히 컬렉션 종류만의 문제가 아니라,
정렬 기준을 어디에 둘지까지 같이 결정해야 한다.

## `equals()` / `hashCode()` / `Comparable`을 언제 같이 보나

### 1. `HashSet`, `HashMap`을 쓸 때

해시 컬렉션은 대략 이렇게 동작한다.

1. `hashCode()`로 후보 위치를 찾는다
2. `equals()`로 정말 같은지 확인한다

그래서 초보자용 기본 규칙은 아래 한 줄이다.

- `equals()`를 오버라이드하면 `hashCode()`도 같은 필드로 같이 맞춘다

### 2. `TreeSet`, `TreeMap`을 쓸 때

sorted collection은 정렬 기준으로 위치를 찾는다.

- `compareTo()` 또는 `Comparator`가 `0`이면 같은 자리로 본다

즉 여기서는 `equals()`만 보고 있으면 반쪽짜리다.

### 3. `List`를 정렬할 때

`List`는 중복 판단을 정렬 기준으로 하지는 않지만,
정렬 결과를 이해하려면 `Comparable`/`Comparator` 감각이 필요하다.

- 클래스의 대표 순서가 있으면 `Comparable`
- 상황별 순서가 여러 개면 `Comparator`

## 아주 작은 예제로 한 번에 보기

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;

final class MemberKey implements Comparable<MemberKey> {
    private final long id;
    private String name;

    MemberKey(long id, String name) {
        this.id = id;
        this.name = name;
    }

    void rename(String name) {
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof MemberKey other)) return false;
        return id == other.id && Objects.equals(name, other.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name);
    }

    @Override
    public int compareTo(MemberKey other) {
        int byName = name.compareTo(other.name);
        if (byName != 0) {
            return byName;
        }
        return Long.compare(id, other.id);
    }
}

Map<MemberKey, String> teamByMember = new HashMap<>();
MemberKey key = new MemberKey(1L, "mina");
teamByMember.put(key, "backend");

Set<MemberKey> ordered = new TreeSet<>();
ordered.add(new MemberKey(1L, "mina"));
ordered.add(new MemberKey(2L, "mina"));

key.rename("momo");

System.out.println(teamByMember.containsKey(key)); // false가 될 수 있다
System.out.println(ordered.size()); // 2
```

이 예제에서 봐야 할 포인트는 둘이다.

- `HashMap` 조회는 mutable key 때문에 깨질 수 있다
- `TreeSet` 중복 판단은 `equals()`가 아니라 `compareTo()` 결과에 달려 있다

## mutable key가 왜 특히 위험한가

멘탈 모델만 잡으면 어렵지 않다.

- `HashMap`은 key를 넣을 때 계산한 bucket을 기억한다
- `TreeMap`은 key를 넣을 때 계산한 정렬 경로 위에 놓는다
- key 필드가 바뀌어도 컬렉션이 자동으로 재배치하지는 않는다

그래서 아래 패턴은 피하는 편이 안전하다.

| 상황 | 왜 위험한가 |
|---|---|
| `HashMap` key의 `equals()`/`hashCode()` 기준 필드를 변경 | 조회 bucket 계산이 달라진다 |
| `TreeMap` key의 `compareTo()` 기준 필드를 변경 | 탐색 경로가 달라진다 |
| `HashSet` 원소의 `equals()`/`hashCode()` 기준 필드를 변경 | 포함 여부 확인과 제거가 흔들린다 |
| `TreeSet` 원소의 정렬 기준 필드를 변경 | 정렬/조회/중복 판단이 흔들린다 |

초보자 기본값은 단순하다.

- key와 set 원소는 가능하면 불변으로 둔다
- 바꿔야 한다면 컬렉션 밖에서 새 객체를 만들고 다시 넣는 쪽이 안전하다

## 순회하면서 수정할 때의 기본 선택

컬렉션을 순회할 때는 "지금 보고 있는 목록"과 "구조를 바꾸는 통로"를 분리해서 생각해야 한다.

| 하고 싶은 일 | 더 안전한 선택 | 피할 것 |
|---|---|---|
| `Map`을 돌며 조건에 맞는 항목 삭제 | `entrySet().removeIf(...)` | `for-each` 안에서 `map.remove(...)` |
| while 순회 중 한 칸씩 삭제 | `Iterator.remove()` | 외부 컬렉션에 직접 `remove(...)` |
| 값만 바꾸기 | `entry.setValue(...)` 또는 명시적 갱신 | 구조 변경과 같은 감각으로 섞어 이해 |

특히 초보자가 자주 헷갈리는 지점은 이거다.

- `ConcurrentModificationException`은 멀티스레드에서만 나는 예외가 아니다
- 같은 스레드에서도 순회 중 구조를 바꾸면 터질 수 있다

## 자주 하는 오해 6가지

- `Set`이면 전부 같은 방식으로 중복을 판단한다고 생각한다
- `equals()`만 구현하면 `HashSet`/`HashMap`이 잘 동작할 거라고 생각한다
- `compareTo() == 0`과 `equals() == true`를 같은 말로 생각한다
- map 안에 들어간 key 객체를 바꿔도 같은 reference니까 조회될 거라고 생각한다
- `HashMap` 출력에 key가 보이면 `get()`도 반드시 될 거라고 생각한다
- `for-each` 안의 `remove(...)`를 단순한 문법 차이 정도로 본다

## 30초 점검표

- 순서가 핵심이면 `List`
- 중복 제거가 핵심이면 `Set`
- key 조회가 핵심이면 `Map`
- 해시 컬렉션이면 `equals()`와 `hashCode()`를 같이 본다
- sorted collection이면 `compareTo()`/`Comparator`를 같이 본다
- key/원소의 비교 기준 필드는 넣은 뒤 바꾸지 않는다
- 순회 중 삭제는 `Iterator.remove()`나 `removeIf(...)`로 한다

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`List`/`Set`/`Map` 자체가 아직 헷갈린다" | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |
| "요구 문장을 타입으로 번역하는 연습이 더 필요하다" | [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md) |
| "`==`/`equals()`/`hashCode()` 감각이 약하다" | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| "`compareTo()`와 `Comparator`를 언제 나누지?" | [Comparable and Comparator Basics](./java-comparable-comparator-basics.md) |
| "mutable key 조회 실패를 더 자세히 보고 싶다" | [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md) |
| "순회 중 수정 패턴만 따로 익히고 싶다" | [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md) |

## 한 줄 정리

Java 컬렉션 첫 읽기에서는 `List`/`Set`/`Map` 선택, `equals()`/`hashCode()`/`compareTo()` 계약, mutable key 금지, 순회 중 안전한 수정 통로를 따로 떼지 말고 한 세트로 이해하는 편이 실수를 가장 빨리 줄인다.
