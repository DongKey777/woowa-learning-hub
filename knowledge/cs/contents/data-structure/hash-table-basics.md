---
schema_version: 3
title: 해시 테이블 기초
concept_id: data-structure/hash-table-basics
canonical: true
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids:
- missions/baseball
- missions/lotto
- missions/blackjack
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- hash-table-o1-average-not-always
- collision-load-factor-basics
- hashcode-equals-contract
aliases:
- hash table basics
- 해시 테이블 입문
- hash map basics
- 해시맵이 뭐예요
- hash function basics
- collision basics
- 해시 충돌이란
- chaining open addressing
- key value store basics
- o1 lookup
- load factor rehashing
- hashmap vs treemap beginner
symptoms:
- HashMap은 항상 O(1)이라고 들었는데 충돌이 많으면 왜 느려지는지 모르겠어
- hashCode가 같으면 같은 객체인지 헷갈려
- load factor와 rehashing이 성능에 어떤 영향을 주는지 궁금해
intents:
- definition
- comparison
prerequisites:
- data-structure/backend-data-structure-starter-pack
next_docs:
- data-structure/hashmap-internals
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
- language/java-equals-hashcode-comparable-contracts
- algorithm/time-complexity-intro
linked_paths:
- contents/data-structure/hashmap-internals.md
- contents/data-structure/basic.md
- contents/data-structure/treemap-vs-hashmap-vs-linkedhashmap.md
- contents/algorithm/time-complexity-intro.md
- contents/language/java-equals-hashcode-comparable-contracts.md
confusable_with:
- data-structure/hashmap-internals
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
- language/java-equals-hashcode-comparable-contracts
forbidden_neighbors: []
expected_queries:
- 해시 테이블은 key를 어떻게 O(1)에 가까운 인덱스로 바꿔?
- 해시 충돌이 나면 chaining과 open addressing이 어떻게 달라?
- HashMap이 평균 O(1)이지만 최악에는 왜 O(n)이 될 수 있어?
- hashCode가 같아도 equals가 다르면 왜 다른 key일 수 있어?
- load factor가 높아지면 rehashing과 메모리 사용이 어떻게 바뀌어?
contextual_chunk_prefix: |
  이 문서는 hash table을 key를 hash function으로 bucket index에 매핑해 평균 O(1) lookup을 제공하지만 collision, chaining, open addressing, load factor, rehashing, hashCode/equals contract에 따라 실제 성능과 정확성이 달라지는 자료구조로 설명하는 beginner primer다.
  HashMap은 항상 O(1)인가, hash collision, load factor, rehash, hashCode equals 차이 같은 자연어 질문이 본 문서에 매핑된다.
---
# 해시 테이블 기초 (Hash Table Basics)

> 한 줄 요약: 해시 테이블은 key를 해시 함수로 인덱스로 변환해 O(1) 평균 조회를 만드는 구조로, 충돌이 발생하면 그 처리 방식이 성능을 좌우한다.

**난이도: 🟢 Beginner**

관련 문서:

- [HashMap 내부 구조](./hashmap-internals.md)
- [기본 자료 구조](./basic.md)
- [자료구조 정리](./README.md)
- [시간복잡도 입문](../algorithm/time-complexity-intro.md)

retrieval-anchor-keywords: hash table basics, 해시 테이블 입문, hash map basics, 해시맵이 뭐예요, hash function basics, collision basics, 해시 충돌이란, chaining open addressing, key value store basics, o(1) lookup, 해시 테이블 원리, beginner hash, hash collision handling, hashmap vs treemap beginner, hash table basics basics

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "HashMap이면 조회가 항상 빠른 거 아닌가요?" | lotto 번호 중복 검사, shopping-cart 상품 id 조회, roomescape 예약 시간 lookup에 Map을 쓰는 코드 | 평균 O(1)과 충돌이 심한 최악 상황을 구분한다 |
| "`hashCode`가 같으면 같은 객체라는 뜻인가요?" | 값 객체를 Set/Map key로 넣었는데 중복 판단이 이상한 테스트 | `hashCode` bucket 후보와 `equals` 동등성 판정을 분리한다 |
| "LinkedHashMap이나 TreeMap으로 바꾸라는 리뷰가 왜 나오죠?" | 출력 순서, 정렬 순서, 삽입 순서가 결과 요구사항에 드러나는 미션 | 해시 테이블은 빠른 lookup 기본값이고 순서 계약은 별도 자료구조 문제로 본다 |

## 핵심 개념

해시 테이블은 **key-value 쌍을 저장**하고, key로 value를 빠르게 찾는 자료구조다.
핵심 원리는 **해시 함수(hash function)** 다. 해시 함수는 임의의 key를 고정 크기 배열의 인덱스(버킷)로 변환한다.

입문자가 자주 헷갈리는 부분은 이것이다.

> "해시 테이블은 항상 O(1)이 아닌가요?"

평균적으로 O(1)이지만, **충돌(collision)** 이 많아지면 최악의 경우 O(n)까지 떨어질 수 있다.

## 한눈에 보기

```text
key: "apple"
       ↓
   해시 함수
       ↓
 인덱스: 3
       ↓
버킷 배열:  [0][ ]  [1][ ]  [2][ ]  [3]["apple" → 100]  [4][ ] ...
```

| 연산 | 평균 | 최악 (충돌 심할 때) |
|---|---|---|
| 조회 (get) | O(1) | O(n) |
| 삽입 (put) | O(1) | O(n) |
| 삭제 (remove) | O(1) | O(n) |

## 상세 분해

### 해시 함수

key를 받아 배열 인덱스를 반환하는 함수다. 좋은 해시 함수는 값을 배열 전체에 고르게 분산시킨다. 자바에서는 `hashCode()` 메서드가 이 역할을 한다.

### 충돌 (Collision)

서로 다른 두 key가 같은 인덱스(버킷)로 변환되는 현상이다. 충돌은 피할 수 없어서, 처리 방식이 중요하다.

- **체이닝 (Chaining)**: 같은 버킷에 연결 리스트나 리스트를 붙여 여러 값을 저장한다. Java `HashMap`이 이 방식을 기본으로 쓴다.
- **오픈 어드레싱 (Open Addressing)**: 충돌이 나면 다른 빈 버킷을 찾아 저장한다.

### 로드 팩터 (Load Factor)

저장된 항목 수를 버킷 총 개수로 나눈 값이다. 로드 팩터가 높아질수록 충돌이 잦아진다. Java `HashMap`은 기본 로드 팩터 0.75를 초과하면 배열을 두 배로 늘리고 재해싱(rehashing)한다.

## 흔한 오해와 함정

- **오해: HashMap은 항상 O(1)이다.**
  충돌이 심하면 O(n)까지 떨어진다. Java 8부터는 한 버킷의 리스트 길이가 8을 넘으면 레드-블랙 트리로 전환해 최악 O(log n)으로 제한한다.

- **함정: null 처리.**
  Java `HashMap`은 key로 null을 허용하지만 `Hashtable`은 허용하지 않는다. `ConcurrentHashMap`도 null key를 허용하지 않는다.

- **오해: 같은 hashCode면 같은 객체다.**
  `hashCode()`가 같아도 `equals()`가 다르면 다른 객체다. 두 메서드를 항상 함께 오버라이드해야 한다.

## 실무에서 쓰는 모습

**캐시 조회** — 서비스 레이어에서 DB 조회 결과를 Map에 담아 재사용하는 것이 가장 흔한 패턴이다. key를 ID나 조건으로 잡고, value를 조회 결과로 저장한다.

**중복 제거** — 리스트에서 중복을 없애거나 방문 여부를 체크할 때 `HashSet`(내부는 HashMap)을 쓴다. 배열 전체를 순회해 비교하는 O(n²) 대신 O(n)으로 해결된다.

## 더 깊이 가려면

- Java HashMap의 버킷 내부 구조, 트리 전환, rehashing 비용은 [HashMap 내부 구조](./hashmap-internals.md)
- TreeMap, LinkedHashMap과 비교해 어느 맵을 언제 쓸지는 [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
- 알고리즘 문제에서 해시를 활용한 패턴은 [알고리즘 기본](../algorithm/basic.md)

## 면접/시니어 질문 미리보기

1. **해시 충돌이 발생했을 때 Java HashMap은 어떻게 처리하나요?**
   체이닝 방식을 쓴다. 같은 버킷에 연결 리스트로 이어 붙이고, 리스트 길이가 8을 넘으면 레드-블랙 트리로 전환해 최악을 O(log n)으로 낮춘다.

2. **hashCode와 equals를 같이 오버라이드해야 하는 이유가 무엇인가요?**
   HashMap은 먼저 hashCode로 버킷을 찾고, 같은 버킷 안에서 equals로 동일성을 확인한다. hashCode만 같고 equals가 다르면 같은 키를 다른 키로 판단해 중복 저장된다.

3. **로드 팩터를 낮추면 어떤 트레이드오프가 있나요?**
   충돌 가능성이 줄어 조회가 빨라지지만, 배열이 더 자주 늘어나 메모리를 더 쓰고 rehashing 비용이 증가한다.

## 한 줄 정리

해시 테이블은 key를 인덱스로 변환해 평균 O(1) 조회를 실현하며, 충돌 처리 방식이 실제 성능을 결정한다.
