---
schema_version: 3
title: New Aliasing Equality HashSet HashMap Get Bridge Drill
concept_id: language/new-aliasing-equality-hashset-hashmap-get-bridge-drill
canonical: true
category: language
difficulty: intermediate
doc_role: drill
level: intermediate
language: ko
source_priority: 91
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- equality
- aliasing
- hash-lookup
aliases:
- new aliasing equality HashSet HashMap get bridge drill
- Java new aliasing equals hash lookup
- identity equality hash collection prediction
- HashSet HashMap get equality drill
- same object same value lookup drill
- 자바 new aliasing equality 드릴
symptoms:
- new를 몇 번 호출했는지와 단순 대입 aliasing 여부를 세지 않고 ==와 equals 결과를 바로 추측해
- equals와 hashCode가 같은 값 규칙을 제공하면 HashSet 중복 제거와 HashMap get lookup으로 이어진다는 흐름을 끊어서 외워
- 같은 값 객체 두 개와 같은 객체 별칭을 구분하지 못해 identity, equality, hash lookup 결과를 섞어 예측해
intents:
- drill
- comparison
- definition
prerequisites:
- language/java-parameter-passing-pass-by-value-side-effects-primer
- language/java-equality-identity-basics
- language/hashmap-hashset-hashcode-equals-lookup-bridge
next_docs:
- language/mutable-hash-keys-hashset-hashmap-bridge
- language/record-value-object-equality-basics
- language/collections-equality-mutable-state-foundations
linked_paths:
- contents/language/java/java-parameter-passing-pass-by-value-side-effects-primer.md
- contents/language/java/java-equality-identity-basics.md
- contents/language/java/hashmap-hashset-hashcode-equals-lookup-bridge.md
- contents/language/java/collections-equality-mutable-state-foundations.md
- contents/data-structure/backend-data-structure-starter-pack.md
confusable_with:
- language/java-equality-identity-basics
- language/hashmap-hashset-hashcode-equals-lookup-bridge
- language/mutable-hash-keys-hashset-hashmap-bridge
forbidden_neighbors: []
expected_queries:
- Java에서 new와 aliasing을 먼저 세고 == equals HashSet HashMap get 결과를 예측하는 드릴을 해보고 싶어
- 같은 객체 alias와 같은 값 copy는 ==와 equals와 HashSet 결과가 어떻게 달라?
- equals hashCode가 구현된 값 객체를 HashMap key로 넣으면 copy로 get이 되는 이유를 설명해줘
- 객체 수에서 identity equality hash lookup으로 이어지는 순서를 beginner에서 intermediate로 연습하고 싶어
- HashSet은 하나로 보이는데 HashMap get도 되는지 한 흐름으로 예측하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 new 호출 수, aliasing, ==, equals, HashSet, HashMap#get을 한 흐름으로 예측하는 intermediate bridge drill이다.
  Java aliasing, identity equality, HashSet duplicate, HashMap get, equals hashCode lookup 질문이 본 문서에 매핑된다.
---
# `new`/별칭에서 `HashSet`/`HashMap#get`까지: Equality Lookup Bridge Drill

> 한 줄 요약: `new`를 몇 번 했는지와 별칭(aliasing) 여부부터 세고, 그다음 `==`, `equals()`, `HashSet`, `HashMap#get` 결과를 한 흐름으로 예측하게 만드는 intermediate practice drill이다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Language README](../README.md)
- [Java parameter 전달, pass-by-value, side effect 입문](./java-parameter-passing-pass-by-value-side-effects-primer.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md)

retrieval-anchor-keywords: java equality lookup bridge drill, java new aliasing equals hashset hashmap get, java == equals hashset hashmap practice, java aliasing to hash collection flow, java same object same value lookup drill, hashset hashmap get prediction exercise, new 두번 alias 한줄 흐름, 자바 == equals hashset hashmap get 연습, 자바 new aliasing hashset hashmap 흐름, 왜 hashset 은 하나인데 hashmap get 은 되나요, 처음 헷갈리는 equality lookup, what is aliasing equals hash lookup

## 핵심 개념

이 드릴의 핵심은 "`==`, `equals()`, `HashSet`, `HashMap#get`을 따로 외우지 말고, 한 장면을 네 번 다른 질문으로 읽는다"이다.

순서는 늘 같다.

1. `new`를 몇 번 했는지 센다.
2. 대입만 있었는지 보고 별칭인지 본다.
3. `==`는 같은 객체 질문으로 읽는다.
4. `equals()`는 같은 값 질문으로 읽는다.
5. `HashSet`과 `HashMap#get`은 그 값 규칙이 조회 규칙으로 이어지는지 본다.

초급 문서가 규칙 소개라면, 이 문서는 그 규칙을 한 번에 연결해서 예측하는 연습용 브리지다.

## 한눈에 보기

| 코드 장면 | 먼저 보는 것 | 예측 기준 |
|---|---|---|
| `Member alias = first;` | 새 객체 생성이 있었나 | 아니면 같은 객체 별칭 가능성이 크다 |
| `new Member(1L, "jane")`를 두 번 | 객체가 몇 개 생겼나 | 보통 서로 다른 객체 둘이다 |
| `first == copy` | 같은 객체인가 | identity 질문 |
| `first.equals(copy)` | 같은 값으로 설계했나 | equality 질문 |
| `seen.add(first); seen.add(copy)` | `equals()`/`hashCode()`가 같은 기준인가 | 같으면 `HashSet`은 1개로 볼 수 있다 |
| `labels.get(copy)` | 같은 key로 다시 찾을 수 있나 | 같으면 `HashMap#get`이 값을 찾을 수 있다 |

짧게 말하면 `객체 수 -> 별칭 여부 -> identity -> equality -> 해시 조회` 순서다.

## 드릴 1: 한 흐름으로 먼저 예측하기

아래 코드를 실행하기 전에 표를 먼저 채워 보자.

```java
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

final class Member {
    private final long id;
    private final String name;

    Member(long id, String name) {
        this.id = id;
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Member other)) return false;
        return id == other.id && Objects.equals(name, other.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name);
    }
}

Member first = new Member(1L, "jane");
Member alias = first;
Member copy = new Member(1L, "jane");

Set<Member> seen = new HashSet<>();
seen.add(first);
seen.add(copy);

Map<Member, String> labels = new HashMap<>();
labels.put(first, "owner");

System.out.println(first == alias);
System.out.println(first == copy);
System.out.println(first.equals(copy));
System.out.println(seen.size());
System.out.println(labels.get(copy));
```

| 질문 | 실행 전 내 답 |
|---|---|
| `first == alias` |  |
| `first == copy` |  |
| `first.equals(copy)` |  |
| `seen.size()` |  |
| `labels.get(copy)` |  |

## 드릴 1 해설

정답은 보통 아래처럼 읽는다.

- `first == alias` -> `true`
- `first == copy` -> `false`
- `first.equals(copy)` -> `true`
- `seen.size()` -> `1`
- `labels.get(copy)` -> `"owner"`

핵심 해설은 한 줄씩 붙이면 된다.

| 결과 | 왜 이렇게 읽는가 |
|---|---|
| `first == alias`가 `true` | `alias = first`는 새 객체 생성이 아니라 같은 객체를 하나 더 가리키는 대입이다 |
| `first == copy`가 `false` | `new Member(...)`가 두 번 나와 객체가 둘이다 |
| `first.equals(copy)`가 `true` | 이 타입은 `id`, `name`이 같으면 같은 값으로 보게 설계했다 |
| `seen.size()`가 `1` | `HashSet`은 같은 객체 수가 아니라 `equals()`/`hashCode()` 기준 같은 값을 본다 |
| `labels.get(copy)`가 `"owner"` | `HashMap#get`도 같은 key 규칙이면 다른 객체여도 값을 다시 찾을 수 있다 |

이 장면에서 중요한 것은 "`copy`는 다른 객체인데도, 값 규칙이 같으면 해시 컬렉션에서는 같은 원소/같은 key처럼 동작할 수 있다"는 점이다.

## 드릴 2: `equals()`만 맞고 `hashCode()`가 어긋나면 어디서 깨질까

이번에는 비교 기준이 해시 조회까지 정말 이어지는지 확인한다.

```java
final class BrokenMember {
    private final long id;
    private final String name;

    BrokenMember(long id, String name) {
        this.id = id;
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof BrokenMember other)) return false;
        return id == other.id && Objects.equals(name, other.name);
    }

    @Override
    public int hashCode() {
        return Long.hashCode(id);
    }
}
```

이 예시는 일부러 잘못된 계약을 만들려는 코드가 아니다. 여기서 말하고 싶은 요지는 "해시 컬렉션은 `equals()`만 알아서는 예측이 끝나지 않는다"는 점이다. `equals()`와 `hashCode()`가 같은 의미의 필드를 봐야 lookup 설명이 자연스럽게 이어진다.

실무에서는 "두 객체가 같은 값인데 `contains`, `get`, `remove`가 이상하다"는 증상이 보이면 `equals()`와 `hashCode()`가 정말 같은 기준을 보는지부터 확인한다.

## 흔한 오해와 함정

| 흔한 말 | 바로잡는 질문 | 더 안전한 해석 |
|---|---|---|
| "`copy`는 다른 객체니까 `HashSet`에도 두 개여야 하지 않나요?" | 컬렉션이 identity를 쓰나 equality를 쓰나 | `HashSet`은 보통 equality 기준을 쓴다 |
| "`get(copy)`가 되면 같은 객체라는 뜻 아닌가요?" | 조회가 같은 객체를 요구하나 같은 key를 요구하나 | `HashMap#get`은 같은 key 규칙이면 된다 |
| "`==`가 false면 `equals()`도 false 아닌가요?" | 지금 질문이 identity인가 value인가 | 다른 객체여도 같은 값일 수 있다 |
| "`alias`와 `copy`가 다 같은 것처럼 보이는데요" | 대입과 `new`를 구분했나 | 별칭은 같은 객체, `copy`는 다른 객체다 |

비유로 보면 `alias`는 같은 사물에 붙은 다른 메모이고, `copy`는 같은 내용을 가진 다른 사물에 가깝다. 다만 이 비유는 해시 bucket이나 실제 메서드 계약까지 설명하지는 못하므로, 컬렉션 동작은 결국 `equals()`/`hashCode()` 규칙으로 다시 읽어야 한다.

## 실무에서 쓰는 모습

PR 리뷰에서 자주 보이는 장면은 아래 둘이다.

1. 테스트에서 `first == copy`를 기대해 놓고 실제로는 값 비교를 하고 싶었던 경우
2. 도메인 객체를 `HashSet`/`HashMap`에 넣고, "다른 객체로 조회했는데 왜 되지?" 또는 "왜 안 되지?"를 설명하지 못하는 경우

이때 안전한 점검 순서는 짧다.

1. `new`가 몇 번 있었는지 본다.
2. `=`만 있었는지 보고 aliasing을 본다.
3. `equals()`가 어떤 필드를 기준으로 같은 값을 정의하는지 본다.
4. `hashCode()`가 그 기준과 같은 의미를 보는지 본다.
5. 그다음에야 `HashSet` 크기와 `HashMap#get` 결과를 예측한다.

이 순서를 거꾸로 보면 "`왜 결과가 이상하지?`"만 남고, 왜 그런지 설명이 흔들린다.

## 더 깊이 가려면

- 별칭과 side effect 감각부터 다시 다지고 싶으면 [Java parameter 전달, pass-by-value, side effect 입문](./java-parameter-passing-pass-by-value-side-effects-primer.md)
- `==`와 `equals()`를 beginner 관점에서 다시 정리하고 싶으면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- 해시 조회가 실제로 `hashCode()` 다음 `equals()`를 보는 흐름을 따로 복습하고 싶으면 [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md)
- mutable key까지 넓혀서 "처음엔 됐는데 나중엔 왜 안 되지?"를 보고 싶으면 [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- 컬렉션 선택 자체가 아직 흐리면 [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md)

## 면접/시니어 질문 미리보기

- "`HashMap#get(copy)`가 성공했다고 `first == copy`도 `true`인가요?"
  - 아니다. 같은 객체와 같은 key는 다른 질문이다.
- "`equals()`만 맞으면 `HashSet` 예측이 끝나나요?"
  - 아니다. 해시 컬렉션은 `hashCode()`와 같이 봐야 한다.
- "왜 이 드릴을 `TreeMap`까지 바로 넓히지 않았나요?"
  - 이 문서는 identity에서 hash lookup으로 넘어가는 한 흐름에 집중한다. 정렬 기준까지 섞으면 다른 혼동 축이 추가된다.

## 한 줄 정리

`new`와 aliasing으로 객체 수를 먼저 세고, 그다음 `==`, `equals()`, `HashSet`, `HashMap#get`을 같은 장면에 차례로 덧씌우면 equality와 lookup 규칙이 한 번에 정리된다.
