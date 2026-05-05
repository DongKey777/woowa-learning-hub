---
schema_version: 3
title: '`List.contains()` vs `Set.contains()` 증상 카드'
concept_id: language/list-contains-vs-set-contains-symptom-card
canonical: false
category: language
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- equals-hashcode-lookup
- collection-mental-model
- mutable-element-set-lookup
aliases:
- list contains vs set contains
- java contains difference beginner
- list contains equals only
- set contains mental model
- hashset contains hashcode equals
- contains looks same but acts different
- why set contains false java
- why list contains true but set contains false
- contains 헷갈려요 list set
- 자바 contains 왜 다르게 느껴지지
- 처음 배우는데 list set contains 차이
- contains 같은 메서드인데 왜 결과가 달라요
- equals만 바꿨는데 왜 set contains false
- what is list contains vs set contains
- set contains equality rule basics
symptoms:
- List.contains는 되는데 HashSet.contains는 기대와 다르게 나와서 어디부터 봐야 할지 모르겠어
- 같은 contains인데 List와 Set이 왜 다르게 느껴지는지 설명이 필요해
- equals를 손봤는데도 Set.contains 결과가 이상해서 hashCode까지 봐야 하는지 헷갈려
intents:
- symptom
- troubleshooting
prerequisites:
- language/java-collections-basics
- language/java-equality-identity-basics
- language/collections-equality-mutable-state-foundations
next_docs:
- language/list-indexof-remove-vs-set-remove-symptom-bridge
- language/hashmap-hashset-hashcode-equals-lookup-bridge
- language/mutable-element-pitfalls-list-set-primer
linked_paths:
- contents/language/java/java-collections-basics.md
- contents/language/java/collections-equality-mutable-state-foundations.md
- contents/language/java/list-indexof-remove-vs-set-remove-symptom-bridge.md
- contents/language/java/hashmap-hashset-hashcode-equals-lookup-bridge.md
- contents/language/java/mutable-element-pitfalls-list-set-primer.md
- contents/language/java/java-equality-identity-basics.md
- contents/data-structure/map-vs-set-requirement-bridge.md
confusable_with:
- language/list-indexof-remove-vs-set-remove-symptom-bridge
- language/collections-equality-mutable-state-foundations
- data-structure/map-vs-set-requirement-bridge
forbidden_neighbors: []
expected_queries:
- List.contains는 되는데 HashSet.contains는 왜 다르게 실패하는지 먼저 분기해줘
- 같은 contains 메서드인데 List와 Set이 왜 다른 질문을 하는지 증상 기준으로 알고 싶어
- equals만 보면 되는지 hashCode까지 같이 봐야 하는지 컬렉션별로 갈라 설명해줘
- Set.contains가 이상할 때 List 문제인지 집합 규칙 문제인지 빠르게 판단하고 싶어
- TreeSet.contains까지 섞여 헷갈릴 때 어떤 기준으로 다음 문서를 골라야 해?
contextual_chunk_prefix: |
  이 문서는 Java 입문자가 contains가 같은 이름인데도 List에서는 맞고
  Set에서는 어긋나는 상황을 증상에서 원인으로 잇는 symptom_router다.
  목록 검색은 되는데 집합 조회가 빗나감, 눈에 보이는 원소를 못 찾음, 값
  비교만 손봤는데 여전히 실패함, 해시 규칙과 정렬 규칙 중 무엇을 봐야 할지
  막힘 같은 자연어 표현이 본 문서의 첫 분기 판단에 매핑된다.
---
# `List.contains()` vs `Set.contains()` 증상 카드

> 한 줄 요약: `contains()`라는 메서드 이름은 같아 보여도 `List`는 "목록 안에 같은 값이 있나"를, `Set`은 "이 집합 규칙으로 같은 원소가 있나"를 묻기 때문에 초보자는 코드 모양보다 컬렉션의 질문부터 분리해서 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [`List.indexOf()` / `List.remove()` vs `Set.remove()` 증상 브리지](./list-indexof-remove-vs-set-remove-symptom-bridge.md)
- [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md)
- [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md)
- [Map vs Set Requirement Bridge](../../data-structure/map-vs-set-requirement-bridge.md)

retrieval-anchor-keywords: list contains vs set contains, java contains difference beginner, list contains equals only, set contains mental model, hashset contains hashcode equals, contains looks same but acts different, why set contains false java, why list contains true but set contains false, contains 헷갈려요 list set, 자바 contains 왜 다르게 느껴지지, 처음 배우는데 list set contains 차이, contains 같은 메서드인데 왜 결과가 달라요, list contains set contains symptom card, what is list contains vs set contains, set contains equality rule basics

## 핵심 증상

초보자가 자주 하는 말은 비슷하다.

- "`contains()`인데 왜 `List`에서는 이해되는데 `Set`에서는 갑자기 헷갈리지?"
- "둘 다 같은 값 찾기 아닌가요?"
- "`List.contains(...)`는 되는데 `HashSet.contains(...)`는 왜 기대와 다르지?"

이때 바로 구현체 이름을 더 외우기보다, 먼저 질문을 나누는 편이 빠르다.

- `List.contains(...)`: 목록 안에 같은 값이 있나
- `Set.contains(...)`: 이 집합의 중복 규칙으로 같은 원소가 있나

즉 메서드 이름은 같아도, `List`는 "검색" 느낌이 더 강하고 `Set`은 "집합 규칙 확인" 느낌이 더 강하다.

## 먼저 잡는 멘탈 모델

초보자용으로는 아래 두 줄이면 충분하다.

- `List`는 순서가 있는 줄에서 `equals()`로 같은 값을 찾는다.
- `HashSet` 같은 `Set`은 중복을 막는 규칙으로 원소를 관리하고, 해시 집합이면 `hashCode()` 다음 `equals()`로 찾는다.

그래서 `contains()`를 읽는 질문도 달라진다.

- `List`에서의 `contains()`는 "이 값이 목록에 있나?"
- `Set`에서의 `contains()`는 "집합이 이 값을 이미 같은 원소로 보나?"

한 줄로 줄이면 이렇다.

> `List.contains()`는 검색 감각으로, `Set.contains()`는 중복 판단 규칙 감각으로 읽는 편이 안전하다.

## 한눈에 보기

| 컬렉션 | `contains()`가 실제로 묻는 것 | beginner 첫 체크 포인트 |
|---|---|---|
| `List` | 목록 안에 같은 값이 있나 | `equals()`가 같은 값을 제대로 정의했는가 |
| `HashSet` | 같은 원소가 이미 집합 안에 있나 | `equals()`와 `hashCode()`가 같이 맞는가 |
| `TreeSet` | 정렬 기준상 같은 자리에 오는 원소가 있나 | `compareTo()`/`Comparator` 기준이 무엇인가 |

같은 `contains()`라도 초보자 디버깅 시작점은 이렇게 다르다.

| 지금 보이는 증상 | 먼저 의심할 것 |
|---|---|
| `List.contains(new User("mina"))`가 `false`다 | `equals()` 기준이 내가 생각한 "같은 값"과 맞는가 |
| `HashSet.contains(user)`가 같은 객체인데도 이상하다 | 넣은 뒤 `hashCode()`/`equals()` 기준 필드를 바꾸지 않았는가 |
| `TreeSet.contains(user)` 결과가 더 낯설다 | equality가 아니라 ordering 규칙으로 찾는 상황인가 |

## 왜 비슷해 보여도 질문이 다를까

`List`는 순서대로 줄 세운 컬렉션이다.
그래서 `contains()`를 호출하면 "이 줄 어딘가에 같은 값이 있나?"를 묻는 감각으로 읽으면 된다.

반면 `Set`은 애초에 "같은 원소는 하나만 남긴다"는 규칙이 핵심이다.
그래서 `contains()`도 단순 검색이라기보다 "집합 규칙상 이미 같은 원소로 보고 있나?"에 가깝다.

이 차이 때문에 초보자가 자주 놓치는 점은 두 가지다.

- `List.contains(...)`가 된다고 해서 `Set.contains(...)`도 똑같은 멘탈 모델로 읽으면 안 된다.
- 특히 `HashSet.contains(...)`는 `equals()`만이 아니라 `hashCode()` 흐름까지 같이 맞아야 디버깅이 쉽다.

즉 같은 메서드 이름을 보고 같은 사고법으로 밀어붙이면, `Set` 쪽에서 갑자기 "보이는데 못 찾는" 느낌이 생긴다.

## 같은 `Member` 예제로 비교하기

```java
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

final class Member {
    private final long id;

    Member(long id) {
        this.id = id;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Member other)) return false;
        return id == other.id;
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}

List<Member> members = new ArrayList<>();
members.add(new Member(1L));

Set<Member> memberSet = new HashSet<>();
memberSet.add(new Member(1L));

System.out.println(members.contains(new Member(1L)));   // true
System.out.println(memberSet.contains(new Member(1L))); // true
```

여기까지만 보면 정말 비슷해 보인다.
둘 다 결국 "같은 값"을 찾는 것처럼 느껴진다.

하지만 내부에서 초보자가 붙여야 할 설명은 다르다.

- `List.contains(...)`: `equals()`로 같은 값을 순서 목록 안에서 찾는다
- `HashSet.contains(...)`: `hashCode()`로 후보를 찾고 `equals()`로 같은 원소인지 확인한다

즉 결과가 같아 보여도, 문제를 해석하는 멘탈 모델은 이미 다르다.

## 흔한 오해와 첫 디버깅 순서

- "`contains()`니까 둘 다 그냥 같은 값 찾기다"
  - 반만 맞다. `List`는 그 감각이 가깝지만, `Set`은 집합 규칙과 lookup 규칙을 함께 봐야 한다.
- "`Set.contains(...)`도 결국 `equals()`만 맞으면 된다"
  - `HashSet`이라면 `hashCode()`도 같이 봐야 한다.
- "`List`와 `Set` 모두 원소가 보이면 `contains()`도 당연히 된다"
  - mutable 원소를 바꾼 뒤라면 `Set`이 더 쉽게 깨진다.

처음 디버깅할 때는 아래 순서가 안전하다.

1. 지금 컬렉션이 `List`인지 `Set`인지 먼저 고른다.
2. `List`면 `equals()`가 같은 값을 제대로 정의했는지 본다.
3. `HashSet`이면 `equals()`와 `hashCode()`를 같이 본다.
4. 정렬된 `Set`이면 equality보다 ordering 규칙 문서로 넘긴다.

## 더 깊이 가려면

- `contains()` 다음으로 `indexOf()`/`remove()`까지 묶어서 헷갈린다면 [`List.indexOf()` / `List.remove()` vs `Set.remove()` 증상 브리지](./list-indexof-remove-vs-set-remove-symptom-bridge.md)
- `HashSet.contains(...)`가 왜 `hashCode()`까지 보는지 바로 이어서 읽으려면 [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md)
- `contains()`가 mutable 상태 때문에 깨지는 장면을 보려면 [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md)
- `List`/`Set`/`Map`을 아예 처음 다시 고르고 싶으면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- `Set`과 `Map`의 요구 자체가 섞여 있으면 [Map vs Set Requirement Bridge](../../data-structure/map-vs-set-requirement-bridge.md)

## 한 줄 정리

`contains()`라는 이름은 같아도 `List`는 "목록 검색", `Set`은 "집합 규칙 확인"으로 읽어야 덜 헷갈린다.
