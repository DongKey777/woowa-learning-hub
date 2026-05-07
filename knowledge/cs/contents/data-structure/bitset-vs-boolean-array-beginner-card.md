---
schema_version: 3
title: BitSet vs boolean[] Beginner Card
concept_id: data-structure/bitset-vs-boolean-array-beginner-card
canonical: false
category: data-structure
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- boolean-array-vs-bitset
- set-algebra-signal
- dense-id-representation
aliases:
- bitset vs boolean array beginner
- bitset vs boolean[] basics
- boolean array 뭐예요
- bitset 뭐예요
- bit array 처음
- why not boolean array
- when to use bitset
- beginner bitmap primer
- bitset 헷갈림
- boolean[] 헷갈림
- what is bitset
- basics bit array
- dense integer id basics
- 처음 bitset
- 왜 bitset 써요
symptoms:
- boolean[]으로도 되는데 왜 굳이 BitSet을 쓰는지 모르겠어
- 방문 여부 저장인데 배열처럼 볼지 집합처럼 볼지 헷갈려
- 한 칸씩 읽는 문제와 집합 연산 문제를 구분하기 어렵다
intents:
- comparison
- design
prerequisites:
- data-structure/basic
- data-structure/bitmap-vs-set-dense-integer-id-beginner-bridge
next_docs:
- data-structure/bitset-vs-roaring-bitmap-handoff
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
linked_paths:
- contents/data-structure/bitmap-vs-set-dense-integer-id-beginner-bridge.md
- contents/data-structure/bitset-vs-roaring-bitmap-beginner-handoff.md
- contents/data-structure/map-set-queue-priorityqueue-trie-bitmap-selection-primer.md
- contents/algorithm/bitset-optimization-patterns.md
confusable_with:
- data-structure/bitmap-vs-set-dense-integer-id-beginner-bridge
- data-structure/bitset-vs-roaring-bitmap-handoff
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
forbidden_neighbors: []
expected_queries:
- 체크박스 상태 저장에서 boolean 배열과 BitSet을 어떻게 고를까
- 방문 여부만 저장하는데 BitSet이 필요한 상황이 따로 있어?
- bitset을 집합처럼 이해해야 하는 이유를 입문자 기준으로 설명해줘
- AND OR 같은 집합 연산이 나오면 왜 boolean[]보다 BitSet 쪽으로 기우나
- 정수 id 플래그를 다룰 때 배열 사고와 비트 집합 사고를 어떻게 나눠?
- 작은 상태표면 그냥 boolean[]으로 가도 되는 기준
contextual_chunk_prefix: |
  이 문서는 BitSet vs boolean[] beginner chooser로 정수 인덱스 체크 표면,
  visited flag, boolean array, bit array, dense integer id, AND/OR/NOT 집합 연산을 구분한다.
  한 칸씩 true/false를 읽고 쓰는 문제는 boolean[]에 남기고, 여러 집합을 합치고 뒤집고 스캔하는 문제는 BitSet으로 연결한다.
---
# BitSet vs boolean[] Beginner Card

> 한 줄 요약: `boolean[]`은 칸마다 `true/false`를 직접 담는 가장 단순한 표이고, `BitSet`은 같은 "정수 id 체크 표"를 더 비트 집합답게 다루는 도구다. beginner는 "`한 칸씩 값만 저장하나`"와 "`집합처럼 합치고 뒤집고 스캔하나`"를 먼저 나누면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md)
- [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- [Bitset Optimization Patterns](../algorithm/bitset-optimization-patterns.md)

retrieval-anchor-keywords: bitset vs boolean array beginner, bitset vs boolean[] basics, boolean array 뭐예요, bitset 뭐예요, bit array 처음, why not boolean array, when to use bitset, beginner bitmap primer, bitset 헷갈림, boolean[] 헷갈림, what is bitset, basics bit array, dense integer id basics, 처음 bitset, 왜 bitset 써요

## 핵심 개념

처음에는 둘 다 "`정수 id` 칸에 체크하는 표"라고 이해해도 된다.

- `boolean[]`: 각 칸에 `true/false` 값을 그대로 둔다
- `BitSet`: 비트를 묶어서 다루는 집합 도구다

입문자가 헷갈리는 이유는 둘 다 겉으로는 "`0번은 켜짐, 3번은 꺼짐`"처럼 읽히기 때문이다.
하지만 질문 모양이 달라지면 선택도 달라진다.

- `학생 30명의 출석 여부를 칸마다 저장`처럼 값 저장이 중심이면 `boolean[]`
- `active 집합 AND premium 집합`처럼 집합 연산이 중심이면 `BitSet`

비유로 말하면 둘 다 체크리스트지만, `boolean[]`은 칸을 하나씩 보는 종이에 가깝고 `BitSet`은 여러 칸을 한 번에 합치고 뒤집는 집합 도구에 가깝다.
다만 이 비유는 저장 방식의 감각만 돕는다. 실제 선택은 "`배열처럼 한 칸씩 다루나`"와 "`집합 연산을 하려나`"로 나누는 편이 더 정확하다.

## 한눈에 보기

| 지금 필요한 질문 | 먼저 떠올릴 것 | 이유 |
|---|---|---|
| `index 17`의 방문 여부만 읽고 쓴다 | `boolean[]` | 칸 단위 읽기/쓰기가 가장 직접적이다 |
| `0..9999` 사용자 중 `active ∩ premium`을 계산한다 | `BitSet` | 비트 집합 연산이 문제를 바로 표현한다 |
| 학생 30명의 체크박스를 화면 모델에 담는다 | `boolean[]` | 길이가 작고 각 칸 의미가 명확하다 |
| `visited`, `blocked`, `eligible` 집합을 반복해서 합친다 | `BitSet` | `and/or/andNot` 같은 집합 연산이 자연스럽다 |
| 처음 bit array를 이해하는 중이다 | `boolean[]`에서 시작해도 된다 | 칸 하나가 무엇을 뜻하는지 먼저 잡기 쉽다 |

짧은 결정표로 다시 보면 이렇다.

| 판단 질문 | `boolean[]` 쪽 신호 | `BitSet` 쪽 신호 |
|---|---|---|
| 각 칸을 독립된 값처럼 읽고 쓰나 | 강함 | 약함 |
| 집합 전체 `AND/OR/NOT`를 자주 하나 | 약함 | 강함 |
| 크기가 아주 작고 UI/상태 모델에 가깝나 | 강함 | 약함 |
| dense integer id 집합을 다루나 | 보통 | 강함 |

## boolean[]에서 멈춰도 되는 순간

아래 조건이 맞으면 beginner는 `boolean[]`로 끝내도 충분하다.

1. 문제를 "칸마다 `true/false` 저장"으로 설명할 수 있다
2. 집합 전체를 겹쳐 보는 연산보다 개별 칸 갱신이 더 많다
3. 크기가 작거나 고정돼 있어서 메모리 압박이 아직 핵심이 아니다
4. 코드 독해가 성능 미세조정보다 더 중요하다

예를 들어 `30명 출석표`, `요일별 영업 여부 7칸`, `보드 게임 방문 칸 체크` 같은 장면은 `boolean[]`이 더 곧바로 읽힌다.

```text
seatOpen[12] = true
visited[3] = false
```

이 단계에서 learner가 꼭 잡아야 하는 감각은 "`인덱스 하나가 대상 하나를 가리킨다`"는 점이다.
그 감각이 아직 흐리면 `BitSet`보다 `boolean[]`이 더 좋은 입구가 된다.

## BitSet이 더 자연스러운 순간

`BitSet`은 "`boolean[]`보다 무조건 고급"이 아니라, 비트 집합 연산이 문제의 중심일 때 더 자연스럽다.

아래 신호가 보이면 `BitSet` 쪽으로 기운다.

1. 원소가 `0..n` 정수 id다
2. `"이 집합과 저 집합의 교집합"` 같은 문장이 자주 나온다
3. 켜진 칸만 훑거나 한꺼번에 비우고 뒤집는 일이 많다
4. `clear`, `flip`, `and`, `or`를 집합 의미로 읽는 편이 쉽다

예를 들어 `activeUsers`, `premiumUsers`, `couponEligibleUsers`를 계속 조합하는 장면은
각 칸을 하나씩 보는 배열보다 "`집합 전체를 합친다`"가 더 핵심이다.

| 장면 | `boolean[]`로 보면 | `BitSet`으로 보면 |
|---|---|---|
| 대상자 세그먼트 교집합 | 칸을 전부 직접 비교해야 한다는 생각이 먼저 든다 | `AND` 한 번이 집합 교집합으로 읽힌다 |
| 켜진 id만 순회 | 모든 칸을 도는 그림이 먼저 떠오른다 | 켜진 비트 중심 순회라는 사고가 붙는다 |
| 여러 조건을 반복 조합 | 상태 배열이 늘어난다 | 비트 집합 조합으로 모델링하기 쉽다 |

보통 beginner-safe 분기는 이 한 줄이면 충분하다.

> `칸 값 저장`이면 `boolean[]`, `정수 id 집합 연산`이면 `BitSet`

## 흔한 오해와 함정

- `BitSet`은 그냥 `boolean[]`의 다른 문법인가요?
  아니다. 비트 기반 집합 연산을 더 직접 표현하는 도구라는 차이가 있다.
- `boolean[]`가 더 단순하니 항상 느린 선택인가요?
  아니다. 작은 고정 크기 상태표나 칸 단위 갱신 중심 문제에서는 더 읽기 쉽고 충분하다.
- `BitSet`이면 곧바로 압축 bitmap까지 알아야 하나요?
  아니다. 먼저 `boolean[]`와의 차이, 즉 "값 배열"과 "비트 집합"의 차이만 잡아도 충분하다.
- `BitSet`이 항상 메모리를 아껴 주나요?
  보통 비트를 묶어 다루므로 `boolean[]`보다 유리한 면이 있지만, beginner 단계에서는 "언제 집합 도구로 읽어야 하나"를 먼저 이해하는 편이 안전하다.

## 다음 한 걸음

이 카드는 `BitSet`을 압축 bitmap 전에 이해하기 위한 entrypoint primer다.
다음 단계는 아래 순서가 안전하다.

1. `dense integer id 집합을 set과 어떻게 나누죠?` -> [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
2. `BitSet이면 충분한가요, sparse range면 어떻게 하죠?` -> [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md)
3. 알고리즘 문제에서 비트 기반 사고를 보고 싶다 -> [Bitset Optimization Patterns](../algorithm/bitset-optimization-patterns.md)

즉 beginner의 학습 순서는 `boolean[]`와 `BitSet` 차이 -> `Set`과 `bitmap` 차이 -> `compressed bitmap handoff` 순서로 가는 편이 덜 헷갈린다.

## 한 줄 정리

`boolean[]`은 칸마다 `true/false`를 저장하는 배열이고, `BitSet`은 같은 정수 칸을 집합처럼 합치고 훑는 도구다. 처음엔 "`값 배열`이냐 `비트 집합`이냐"만 분리해도 다음 bitmap 학습이 훨씬 쉬워진다.
