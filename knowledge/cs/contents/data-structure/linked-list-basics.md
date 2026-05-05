---
schema_version: 3
title: 연결 리스트 기초 (Linked List Basics)
concept_id: data-structure/linked-list-basics
canonical: true
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- pointer-update-basics
- null-tail-guard
- linkedlist-vs-arraylist
aliases:
- linked list basics
- 연결 리스트 입문
- singly linked list
- doubly linked list
- 단방향 연결 리스트
- 양방향 연결 리스트
- node pointer
- linked list structure
- 연결 리스트 구조
- 연결 리스트가 뭐예요
- linked list insert delete
- head tail pointer beginner
- null pointer linked list
- linked list basics basics
- linked list basics beginner
symptoms:
- 연결 리스트가 노드랑 포인터라는 말까진 알겠는데 그림이 안 그려져
- 삽입 삭제가 빠르다면서 왜 위치 찾기 비용까지 같이 보라고 하는지 헷갈려
- 단방향이랑 양방향 연결 리스트를 언제 구분해서 써야 하는지 모르겠어
intents:
- definition
prerequisites:
- data-structure/basic
next_docs:
- data-structure/array-vs-linked-list
- data-structure/lru-cache-basics
linked_paths:
- contents/data-structure/basic.md
- contents/data-structure/lru-cache-basics.md
- contents/data-structure/arraydeque-vs-linkedlist-queue-choice-card.md
- contents/algorithm/two-pointer-intro.md
confusable_with:
- data-structure/array-vs-linked-list
- data-structure/basic
forbidden_neighbors:
- contents/data-structure/array-vs-linked-list.md
expected_queries:
- 연결 리스트 동작 방식을 그림 없이도 이해하고 싶어
- 노드와 포인터로 이어진 구조를 처음 배울 때 볼 설명
- 단일 연결 리스트와 이중 연결 리스트 차이 입문
- 연결 리스트가 임의 접근에 약한 이유를 쉽게 설명해줘
- head tail null 처리를 왜 자꾸 강조하는지 알고 싶어
- LRU 전에 연결 리스트 기본기를 먼저 정리하고 싶어
- ArrayList 대신 LinkedList를 언제 떠올려야 하는지 입문 기준이 필요해
- 연결 리스트 순회랑 삽입 비용을 같이 봐야 하는 이유가 궁금해
contextual_chunk_prefix: |
  이 문서는 자료구조 입문자가 노드와 포인터로 이어진 연결 리스트가 왜
  삽입과 삭제에는 강하고 임의 접근에는 약한지 기초를 잡는 primer다.
  노드 체인 그림, head tail null 처리, 단방향과 양방향 차이, 위치를
  알아야 O(1) 삽입, 배열과 반대 특성 같은 자연어 paraphrase가 본
  문서의 핵심 개념에 매핑된다.
---
# 연결 리스트 기초 (Linked List Basics)

> 한 줄 요약: 연결 리스트는 노드들이 포인터로 이어진 구조로, 삽입·삭제가 빠르지만 임의 접근이 느리다는 점에서 배열과 정반대 강점을 가진다.

**난이도: 🟢 Beginner**

관련 문서:

- [기본 자료 구조](./basic.md)
- [LRU 캐시 설계 입문](./lru-cache-basics.md)
- [자료구조 정리](./README.md)
- [두 포인터 입문](../algorithm/two-pointer-intro.md)

retrieval-anchor-keywords: linked list basics, 연결 리스트 입문, singly linked list, doubly linked list, 단방향 연결 리스트, 양방향 연결 리스트, node pointer, array vs linked list, 배열과 연결 리스트 차이, 연결 리스트가 뭐예요, linked list insert delete, head tail pointer beginner, null pointer linked list, linked list basics basics, linked list basics beginner

## 핵심 개념

연결 리스트는 **노드(node)** 라는 단위를 포인터로 이어 붙인 자료구조다.
각 노드는 값(data)과 다음 노드를 가리키는 포인터(next)로 이루어진다.

배열과 가장 많이 비교되는 이유가 있다.

- 배열은 메모리가 **연속**으로 붙어 있어 인덱스로 바로 접근할 수 있다.
- 연결 리스트는 노드들이 메모리 곳곳에 흩어져 있어 인덱스 접근이 느리지만, 중간에 노드를 끼워 넣거나 뺄 때 포인터만 수정하면 된다.

이 차이가 자료구조 선택의 핵심이다.

## 한눈에 보기

| 연산 | 배열 | 연결 리스트 |
|---|---|---|
| 임의 접근 (index) | O(1) | O(n) |
| 앞/중간 삽입 | O(n) | O(1) (위치 알 때) |
| 앞/중간 삭제 | O(n) | O(1) (위치 알 때) |
| 끝에 삽입 | O(1) (amortized) | O(1) (tail 포인터 있을 때) |
| 메모리 | 연속 블록 | 노드별 분산 |

## 상세 분해

### 단방향 연결 리스트 (Singly Linked List)

각 노드가 다음 노드만 가리킨다. 순방향 순회는 쉽지만 역방향은 한 번에 안 된다.

```text
[head] → [1] → [2] → [3] → null
```

### 양방향 연결 리스트 (Doubly Linked List)

각 노드가 이전(prev)과 다음(next) 모두를 가리킨다. 양방향 순회가 필요하거나 특정 노드 앞에 삽입할 때 유리하다. Java의 `LinkedList`가 이 구조다.

```text
null ← [1] ↔ [2] ↔ [3] → null
```

### 원형 연결 리스트 (Circular Linked List)

마지막 노드가 첫 노드(head)를 가리켜 순환 구조를 만든다. 순환 큐나 라운드 로빈 스케줄러에서 볼 수 있다.

## 흔한 오해와 함정

- **오해: 연결 리스트가 배열보다 항상 좋다.**
  삽입·삭제 위치를 이미 알고 있을 때만 O(1)이다. 위치를 먼저 찾아야 한다면 순회(O(n))가 선행된다.

- **함정: NullPointerException.**
  마지막 노드의 next는 null이다. 순회할 때 null 체크를 빠뜨리면 NPE가 발생한다.

- **오해: Java ArrayList와 LinkedList 중 LinkedList가 삽입에서 항상 빠르다.**
  리스트 중간에 반복 삽입·삭제가 많을 때는 맞지만, 대부분의 일반적인 순차 작업에서는 캐시 친화적인 ArrayList가 실제로 더 빠른 경우가 많다.

## 실무에서 쓰는 모습

**LRU 캐시** — 가장 최근에 접근한 항목을 앞으로 이동시켜야 할 때, 양방향 연결 리스트와 해시맵을 함께 쓰면 삭제-재삽입이 O(1)로 된다.

**Queue 구현** — 연결 리스트로 큐를 만들면 head에서 dequeue, tail에 enqueue하는 동작이 O(1)이다. 배열 기반 큐보다 크기 제약이 없다.

## 더 깊이 가려면

- LRU 캐시 설계에서 연결 리스트가 왜 쓰이는지는 [LRU 캐시 설계 입문](./lru-cache-basics.md)
- 배열, 스택, 큐를 함께 비교하고 싶으면 [기본 자료 구조](./basic.md)
- 알고리즘 문제에서의 연결 리스트 패턴은 [알고리즘 기본](../algorithm/basic.md)

## 면접/시니어 질문 미리보기

1. **배열과 연결 리스트의 차이가 무엇인가요?**
   배열은 연속 메모리로 인덱스 접근이 O(1)이지만 중간 삽입·삭제가 O(n)이다. 연결 리스트는 포인터로 연결되어 중간 삽입·삭제가 O(1)이지만 임의 접근이 O(n)이다.

2. **연결 리스트에서 사이클을 어떻게 감지하나요?**
   플로이드 사이클 탐지 알고리즘(Floyd's Cycle Detection)을 쓴다. 빠른 포인터(2칸씩)와 느린 포인터(1칸씩)를 동시에 이동시키면, 사이클이 있을 때 둘이 만난다.

3. **Java LinkedList를 언제 사용하고 언제 ArrayList를 사용하나요?**
   리스트 중간에 잦은 삽입·삭제가 있고 순차 접근이 주라면 LinkedList, 인덱스 기반 임의 접근이 빈번하면 ArrayList가 적합하다. 대부분 실무에서는 ArrayList가 기본값이다.

## 한 줄 정리

연결 리스트는 포인터로 이어진 노드 체인으로, 삽입·삭제는 강하고 임의 접근은 느리다는 배열의 정반대 강점을 가진다.
