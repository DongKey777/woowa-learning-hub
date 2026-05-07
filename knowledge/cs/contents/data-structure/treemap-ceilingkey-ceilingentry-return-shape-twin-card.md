---
schema_version: 3
title: TreeMap ceilingKey vs ceilingEntry Return-Shape Twin Card
concept_id: data-structure/treemap-ceilingkey-ceilingentry-return-shape-twin-card
canonical: false
category: data-structure
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- treemap-return-shape
- ceilingkey-ceilingentry
- navigablemap-beginner
aliases:
- TreeMap ceilingKey vs ceilingEntry
- ceilingKey ceilingEntry 차이
- ceilingKey returns key
- ceilingEntry returns entry
- right side lookup TreeMap
- key entry return shape
- ceiling exact match 포함
symptoms:
- ceilingKey와 ceilingEntry가 같은 오른쪽 후보를 찾지만 반환 shape만 key vs entry로 다르다는 점을 놓친다
- ceilingEntry가 value를 준다는 이유로 ceilingKey보다 더 멀리 찾는다고 오해한다
- 오른쪽 후보가 없을 때 ceilingKey와 ceilingEntry가 모두 null일 수 있다는 경계 처리를 빠뜨린다
intents:
- definition
- troubleshooting
prerequisites:
- data-structure/treemap-key-entry-strictness-bridge
next_docs:
- data-structure/treemap-ceilingkey-higherkey-exact-match-choice-card
- data-structure/treemap-floorentry-ceilingentry-value-read-micro-drill
- data-structure/treeset-treemap-null-boundary-quick-reference
linked_paths:
- contents/data-structure/treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card.md
- contents/data-structure/treemap-key-entry-strictness-bridge.md
- contents/data-structure/treemap-floorentry-ceilingentry-value-read-micro-drill.md
- contents/data-structure/treeset-treemap-null-boundary-quick-reference.md
- contents/language/java/navigablemap-navigableset-mental-model.md
confusable_with:
- data-structure/treemap-ceilingkey-higherkey-exact-match-choice-card
- data-structure/treemap-key-entry-strictness-bridge
- data-structure/treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card
- data-structure/treeset-treemap-null-boundary-quick-reference
forbidden_neighbors: []
expected_queries:
- TreeMap ceilingKey와 ceilingEntry는 같은 후보를 찾는데 반환값이 어떻게 달라?
- ceilingEntry는 key와 value를 같이 주고 ceilingKey는 key만 준다는 걸 예시로 설명해줘
- ceilingKey와 ceilingEntry는 exact match를 포함하고 오른쪽 후보 없으면 null인가?
- 다음 예약 시작만 필요할 때와 다음 예약 end value까지 필요할 때 어떤 메서드를 써?
- TreeMap 오른쪽 후보 lookup에서 key return shape와 entry return shape를 구분해줘
contextual_chunk_prefix: |
  이 문서는 TreeMap ceilingKey와 ceilingEntry를 같은 right-side inclusive candidate
  lookup이지만 반환 shape가 key-only와 key-plus-value Entry로 다르다고 설명하는
  beginner bridge다. exact match 포함과 null boundary를 함께 다룬다.
---
# TreeMap `ceilingKey` vs `ceilingEntry` Return-Shape Twin Card

> 한 줄 요약: `ceilingKey(x)`와 `ceilingEntry(x)`는 둘 다 `x`와 같거나 바로 다음인 오른쪽 후보를 찾지만, 전자는 key만 돌려주고 후자는 key+value를 함께 돌려준다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeMap `firstKey` vs `firstEntry`, `floorKey` vs `floorEntry` Return-Shape Card](./treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card.md)
- [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: treemap ceilingkey ceilingentry beginner, ceilingkey ceilingentry 차이, ceilingkey vs ceilingentry return shape, treemap right side lookup basics, ordered map 다음 예약 뭐예요, ceilingentry null 왜, ceilingkey ceilingentry 헷갈려요, key entry 반환 shape, treemap exact match 포함 basics, ceilingkey value 같이 반환, 처음 treemap ceiling query, what is ceilingentry

## 핵심 개념

이 카드는 오른쪽 이웃을 읽을 때만 따로 헷갈리는 beginner를 위한 짧은 브리지다.

질문을 먼저 두 축으로 자르면 된다.

- "`x`와 같거나 바로 다음 key"만 필요하나
- 그 후보의 value까지 같이 필요하나

초보자 번역은 한 줄이면 충분하다.

> `ceilingKey(x)`는 오른쪽 후보의 key만, `ceilingEntry(x)`는 그 후보의 key와 value를 같이 준다.

여기서 중요한 점은 "찾는 자리"는 같다는 것이다.

- 둘 다 `ceiling`이라서 exact match를 포함한다.
- 둘 다 오른쪽 후보가 없으면 `null`이다.
- 차이는 `Entry` 쪽만 value를 바로 읽을 수 있다는 점이다.

즉 이 문서는 strict/inclusive 전체를 다시 푸는 글이 아니라, "`오른쪽 포함 검색`에서 key만 볼지 entry까지 볼지"를 한 장으로 붙이는 twin card다.

## 한눈에 보기

`TreeMap<start, end>` 예약표가 아래처럼 있다고 하자.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
15:30 -> 16:00
```

| 질문 | 호출 | 결과 모양 | 값 예시 |
|---|---|---|---|
| `11:00`과 같거나 바로 다음 시작 시각만 보고 싶다 | `ceilingKey(11:00)` | `K` | `13:00` |
| `11:00`과 같거나 바로 다음 예약 전체를 보고 싶다 | `ceilingEntry(11:00)` | `Map.Entry<K, V>` | `13:00 -> 14:00` |
| exact match인 `13:00`이 있으면 그 key만 보고 싶다 | `ceilingKey(13:00)` | `K` | `13:00` |
| exact match인 `13:00` 예약의 시작/끝을 같이 보고 싶다 | `ceilingEntry(13:00)` | `Map.Entry<K, V>` | `13:00 -> 14:00` |

핵심은 "`같은 줄`을 찾더라도 반환 shape가 다르다"는 점이다.

- `ceilingKey(13:00)`와 `ceilingEntry(13:00)`는 둘 다 exact match인 `13:00` 줄에 멈춘다.
- `ceilingKey(11:00)`와 `ceilingEntry(11:00)`도 둘 다 `13:00` 줄을 가리킨다.
- 차이는 `Entry` 쪽만 그 줄의 종료 시각까지 바로 읽는다는 것이다.

## 같은 자리인데 무엇이 달라지나

입문자가 실제로 던지는 질문을 표로 고정하면 아래처럼 읽으면 된다.

| 헷갈리는 질문 | 먼저 떠올릴 pair | 초보자 번역 |
|---|---|---|
| `다음 예약 시작 시각만 필요해요?` | `ceilingKey(x)` | 오른쪽 줄 번호만 보기 |
| `다음 예약 끝 시각도 같이 봐야 해요?` | `ceilingEntry(x)` | 오른쪽 줄 전체 보기 |
| `exact match면 ceilingEntry도 그 자리예요?` | `ceilingKey(x)` vs `ceilingEntry(x)` | 둘 다 `ceiling`이라서 포함 |
| `왜 ceilingKey도 null이고 ceilingEntry도 null이죠?` | `ceiling` pair | 오른쪽 후보 자체가 없기 때문이다 |

이 네 줄만 먼저 붙이면 된다.

- `ceilingKey(x)` -> key만
- `ceilingEntry(x)` -> entry
- 둘 다 exact match를 포함한다
- 둘 다 오른쪽 후보가 없으면 `null`

## 오른쪽 후보가 없을 때는 어떻게 읽나

beginner가 자주 놓치는 포인트는 `ceilingKey`와 `ceilingEntry`가 "실패 방식"까지 같은 계열이라는 점이다.

| 호출 | `17:00` 기준 결과 | 읽는 법 |
|---|---|---|
| `ceilingKey(17:00)` | `null` | 마지막 key보다 더 오른쪽 후보가 없다 |
| `ceilingEntry(17:00)` | `null` | 마지막 entry보다 더 오른쪽 후보가 없다 |
| `ceilingKey(13:00)` | `13:00` | exact match 포함 |
| `ceilingEntry(13:00)` | `13:00 -> 14:00` | exact match 포함 + value까지 읽음 |

그래서 초보자 기준으로는 아래 순서가 안전하다.

1. "`오른쪽 후보가 있나?`"를 먼저 본다.
2. 있으면 key만 필요한지, value도 필요한지 고른다.
3. `Entry`를 받았다면 `null` 확인 뒤 `getKey()`와 `getValue()`를 읽는다.

이 순서로 보면 "`왜 ceilingEntry는 예외가 아니라 null이죠?`" 같은 혼동이 줄어든다. `ceiling` 계열은 후보가 없을 때 `null`로 읽는 쪽이라고 붙이면 된다.

## 실무에서 쓰는 모습

새 예약 시작 시각이 `11:00`일 때 오른쪽 이웃을 보는 코드는 보통 이 정도부터 시작한다.

```java
LocalTime nextStart = reservations.ceilingKey(start);
Map.Entry<LocalTime, LocalTime> nextSlot = reservations.ceilingEntry(start);
```

이 두 줄은 같은 예약 줄을 가리킬 수 있다.
차이는 아래뿐이다.

- `nextStart`는 `13:00`만 받는다.
- `nextSlot`은 `13:00 -> 14:00` 전체를 받는다.

그래서 질문이 "`다음 예약이 몇 시에 시작하지?`"면 `ceilingKey()`로 끝난다.
질문이 "`그 다음 예약은 몇 시에 끝나지?`"까지 커지면 `ceilingEntry()`가 바로 필요해진다.

비유하면 `ceilingKey()`는 "다음 줄 번호"를 보는 것이고 `ceilingEntry()`는 "다음 줄 전체"를 보는 것이다. 다만 실제 `TreeMap`은 줄을 스캔하는 구조가 아니라 정렬된 key 기준으로 후보를 찾는다는 점에서, 이 비유는 "반환 모양"을 설명하는 데까지만 맞다.

## 흔한 오해와 함정

- `ceilingEntry(x)`가 `ceilingKey(x)`보다 더 멀리 찾는 것은 아니다. 둘 다 같은 오른쪽 후보를 찾고 value를 같이 줄 뿐이다.
- `Entry`를 받았다고 해서 non-null이 보장되지는 않는다. 마지막 key보다 더 오른쪽을 찾으면 `ceilingEntry(x)`도 `null`이다.
- `ceilingEntry(x)`가 value까지 준다고 해서 "다음 빈 시간"이 바로 계산되는 것은 아니다. gap 판단은 보통 왼쪽 `floorEntry(start)`도 함께 봐야 한다.
- `ceilingKey(x)`와 `higherKey(x)`를 섞으면 exact match에서 틀린다. `ceiling`은 포함, `higher`는 제외다.

## 더 깊이 가려면

- 왼쪽 lookup 카드와 짝으로 보고 싶다면 [TreeMap `firstKey` vs `firstEntry`, `floorKey` vs `floorEntry` Return-Shape Card](./treemap-firstkey-firstentry-floorkey-floorentry-return-shape-card.md)
- `lower/floor/ceiling/higher` 네 쌍 전체의 strict/inclusive 감각까지 같이 붙이고 싶다면 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- `ceilingEntry()`에서 `getValue()`를 꺼내 다음 예약 종료 시각까지 읽는 연습을 하려면 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- broader한 null 경계표가 먼저 필요하면 [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)

## 한 줄 정리

`ceilingKey`는 오른쪽 후보 key만, `ceilingEntry`는 그 후보의 key+value를 주며, 초보자는 여기에 "둘 다 exact match 포함, 오른쪽 후보가 없으면 둘 다 `null`"이라는 실패 방식까지 같이 묶어 기억하면 된다.
