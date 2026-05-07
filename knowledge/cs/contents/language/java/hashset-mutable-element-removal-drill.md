---
schema_version: 3
title: HashSet Mutable Element Removal Drill
concept_id: language/hashset-mutable-element-removal-drill
canonical: true
category: language
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- hashset-mutation
- equals-hashcode
- removal-debug
aliases:
- HashSet mutable element removal drill
- HashSet contains remove fail
- mutable hashCode field HashSet
- same object remove false
- HashSet remove false after mutation
- 자바 HashSet remove 실패
symptoms:
- HashSet에 넣은 원소의 equals/hashCode 기준 필드를 바꿨는데 같은 객체이니 contains/remove가 될 거라고 기대해
- contains와 remove가 둘 다 현재 hashCode로 bucket을 찾는 lookup 경로라 같은 이유로 실패할 수 있다는 점을 놓쳐
- 출력에는 원소가 보이지만 bucket lookup으로는 못 찾는 차이를 이해하지 못해
intents:
- drill
- troubleshooting
- definition
prerequisites:
- language/mutable-hash-keys-hashset-hashmap-bridge
next_docs:
- language/mutable-elements-hashset-treeset-primer
- language/hashset-vs-treeset-duplicate-semantics
- language/java-immutable-object-basics
linked_paths:
- contents/language/java/mutable-hash-keys-hashset-hashmap-bridge.md
- contents/language/java/mutable-elements-hashset-treeset-primer.md
- contents/language/java/java-equality-identity-basics.md
- contents/language/java/hashset-vs-treeset-duplicate-semantics.md
confusable_with:
- language/mutable-hash-keys-hashset-hashmap-bridge
- language/mutable-elements-hashset-treeset-primer
- language/hashmap-treemap-mutable-key-lookup-primer
forbidden_neighbors: []
expected_queries:
- HashSet에 넣은 원소 필드를 바꿨더니 같은 객체인데 contains와 remove가 false인 이유를 알려줘
- HashSet remove가 실패하는 mutable hashCode field 드릴을 풀고 싶어
- 출력에는 원소가 보이는데 HashSet remove가 안 되는 bucket lookup 차이를 설명해줘
- HashSet 원소의 equals hashCode 기준 필드를 바꾸면 왜 옛 bucket에 남는지 알려줘
- HashSet mutable element는 빼고 바꾸고 다시 넣는 패턴이 왜 필요한지 설명해줘
contextual_chunk_prefix: |
  이 문서는 HashSet에 넣은 mutable element의 equals/hashCode 기준 필드가 바뀌면 contains/remove lookup이 실패할 수 있음을 손예측하는 beginner drill이다.
  HashSet mutable element, remove false, contains false, hashCode changed, same object lookup 질문이 본 문서에 매핑된다.
---
# HashSet Mutable Element Removal Drill

> 한 줄 요약: `HashSet`에 넣은 원소의 `equals()`/`hashCode()` 기준 필드를 바꾸면, `contains()`와 `remove()`가 둘 다 같은 lookup 이유로 실패할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
- [Mutable Elements in HashSet and TreeSet Primer](./mutable-elements-hashset-treeset-primer.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)

retrieval-anchor-keywords: hashset mutable element removal, hashset contains remove fail, mutable hashcode field hashset, java hashset remove false after mutation, 자바 hashset remove 실패, 자바 hashset contains false, 처음 배우는데 hashset remove, hashset 왜 remove false 인가요, how hashset bucket works, equals hashcode mutation beginner, same object remove false, hashset mutable element drill

## 먼저 잡을 mental model

이번 드릴은 이 두 줄이면 충분하다.

- `HashSet`은 현재 `hashCode()`로 bucket을 찾고, 그 안에서 `equals()`를 본다.
- 원소를 넣은 뒤 필드가 바뀌어도 `HashSet`은 그 원소를 새 bucket으로 옮겨 주지 않는다.

그래서 초보자용 결론은 한 줄이다.

> `contains()`가 현재 bucket을 못 찾으면 `remove()`도 같은 이유로 같이 실패하기 쉽다.

## 10초 예측표

| 상황 | 결과 예측 |
|---|---|
| `add(user)` 직후 `contains(user)` | `true` |
| `login` 변경 후 `contains(user)` | `false` 가능 |
| 같은 상태에서 `remove(user)` | `false` 가능 |

## 드릴 코드

```java
final class User {
    private String login;

    User(String login) {
        this.login = login;
    }

    void rename(String login) {
        this.login = login;
    }

    @Override
    public boolean equals(Object o) { ... login 기준 ... }

    @Override
    public int hashCode() { ... login 기준 ... }
}

Set<User> users = new HashSet<>();
User user = new User("mina");
users.add(user);

user.rename("momo");

System.out.println(users.contains(user));
System.out.println(users.remove(user));
System.out.println(users.size());
```

정답은 보통 이렇게 읽는다.

- `users.contains(user)` -> `false`
- `users.remove(user)` -> `false`
- `users.size()` -> `1`

## 왜 둘 다 같은 이유로 실패하나

순서는 짧게 이렇게 보면 된다.

1. `add(user)` 할 때는 `"mina"` 기준 `hashCode()`로 bucket이 정해진다.
2. `rename("momo")` 뒤에도 원소는 옛 bucket에 그대로 남아 있다.
3. 이제 `contains(user)`는 `"momo"` 기준 bucket을 찾는다.
4. `remove(user)`도 거의 같은 lookup 경로를 따라간다.
5. 그래서 둘 다 원소를 못 찾고 `false`가 된다.

핵심은 reference가 같다는 사실만으로는 충분하지 않다는 점이다.

## 눈으로 바로 보는 장면

| 시점 | `login` 값 | `HashSet`이 찾는 bucket 기준 |
|---|---|---|
| 삽입 직후 | `"mina"` | `"mina"` hash |
| 변경 직후 | `"momo"` | `"momo"` hash |

원소는 옛 bucket에 남아 있는데 lookup은 새 bucket으로 가니 어긋난다.

이 장면 때문에 출력에 원소가 보여도 `remove()`가 실패할 수 있다.

## 초보자 공통 혼동

- "`contains()`만 조회라서 실패하고 `remove()`는 지울 수 있지 않나?" -> 둘 다 같은 lookup 규칙을 쓴다.
- "같은 객체를 넘겼는데 왜 못 찾지?" -> `HashSet`은 reference보다 현재 `hashCode()` 경로를 먼저 본다.
- "출력에 보이는데 왜 없는 것처럼 굴지?" -> 순회해서 보이는 것과 bucket으로 찾는 것은 다른 과정이다.

처음 배우는 단계에서는 이 규칙만 먼저 고정하면 된다.

- `HashSet`/`HashMap` key로 쓰는 필드는 가능하면 불변으로 둔다.
- 꼭 바꿔야 하는 필드라면 컬렉션에 넣기 전후 경계를 다시 설계한다.

## 바로 쓸 안전한 수정 패턴

가변 필드를 꼭 바꿔야 한다면 "빼고, 바꾸고, 다시 넣기" 순서를 먼저 떠올리면 된다.

```java
users.remove(user);
user.rename("momo");
users.add(user);
```

이 패턴은 증상 응급처치로는 쓸 수 있지만, 초급자 기준 더 좋은 기본 해법은 `equals()`/`hashCode()` 기준 필드를 불변으로 두는 쪽이다.

## 다음에 어디로 이어서 읽을까

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| 같은 문제를 `HashMap` key까지 넓혀 보고 싶다 | [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md) |
| `TreeSet`의 가변 원소 문제와 같이 비교하고 싶다 | [Mutable Elements in HashSet and TreeSet Primer](./mutable-elements-hashset-treeset-primer.md) |
| equality 기준부터 다시 잡고 싶다 | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |

## 한 줄 정리

`HashSet`에 들어간 뒤 `equals()`/`hashCode()` 기준 필드를 바꾸면, `contains()`와 `remove()`는 둘 다 현재 bucket을 잘못 찾아 함께 실패할 수 있다.
