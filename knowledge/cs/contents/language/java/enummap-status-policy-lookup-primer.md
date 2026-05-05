---
schema_version: 3
title: Enum 키라면 언제 `HashMap`에서 `EnumMap`으로 옮길까
concept_id: language/enummap-status-policy-lookup-primer
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- enum-key-map-choice
- status-policy-table
aliases:
- enummap vs hashmap enum key
- enum key map choice beginner
- when to use enummap
- enum map mental model
- hashmap to enummap
- enum status lookup table
- enum key why not hashmap
- 처음 배우는데 enummap
- enum 키면 언제 enummap
- 상태별 정책 테이블
- what is enummap
- java enum map basics
symptoms:
- enum 키만 쓰는데 왜 그냥 HashMap을 쓰는지 설명이 안 돼
- 상태별 라벨이나 정책을 저장할 때 EnumMap을 언제 떠올려야 할지 모르겠어
- switch가 반복되는데 map으로 옮길지 enum 메서드로 갈지 감이 안 와
intents:
- definition
prerequisites:
- language/java-enum-basics
- language/java-collections-basics
next_docs:
- language/enum-to-state-transition-beginner-bridge
- language/map-implementation-selection-mini-drill
- software-engineering/oop-design-basics
linked_paths:
- contents/language/java/java-enum-basics.md
- contents/language/java/map-implementation-selection-mini-drill.md
- contents/language/java/java-collections-basics.md
- contents/language/java/enum-to-state-transition-beginner-bridge.md
- contents/software-engineering/oop-design-basics.md
confusable_with:
- language/map-implementation-selection-mini-drill
- language/enum-to-state-transition-beginner-bridge
forbidden_neighbors:
- contents/language/java/java-collections-basics.md
expected_queries:
- Enum 키만 쓰는 맵이면 HashMap 말고 EnumMap을 왜 고려해야 해?
- 상태별 정책 테이블을 만들 때 EnumMap이 잘 맞는 경우를 초보자 기준으로 알려줘
- 주문 상태 라벨 저장 예제로 EnumMap 입문 설명해줘
- enum 전용 lookup 표와 일반 HashMap 차이를 처음 배우는 사람 관점에서 보고 싶어
- key가 enum으로 닫혔다는 말이 map 선택에 왜 중요해?
- switch가 늘어나기 시작할 때 EnumMap으로 옮기는 신호가 뭔지 궁금해
contextual_chunk_prefix: |
  이 문서는 Java 학습자가 enum만 key로 쓰는 상태표에서 범용 map 대신 EnumMap을 언제 떠올려야 하는지, 작은 라벨표와 정책표 선택 기준을 처음 잡는 primer다. enum 전용 칸막이 표, 상태별 lookup 표, switch가 늘어날 때 map 선택, key 후보가 이미 닫힘, 주문 상태 라벨표, 범용 서랍보다 전용 표가 나은 순간 같은 자연어 paraphrase가 본 문서의 핵심 판단에 매핑된다.
---
# Enum 키라면 언제 `HashMap`에서 `EnumMap`으로 옮길까

> 한 줄 요약: key 후보가 enum으로 이미 고정됐다면 `HashMap`은 범용 서랍이고 `EnumMap`은 enum 전용 칸막이 표라고 생각하면 된다. 상태별 작은 값을 붙일 때는 `EnumMap`이 의도를 더 또렷하게 드러낸다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java enum 기초](./java-enum-basics.md)
- [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md)
- [객체지향 설계 기초](../../software-engineering/oop-design-basics.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: enummap vs hashmap enum key, enum key map choice beginner, when to use enummap, enum map mental model, hashmap to enummap, enum status lookup table, enum key why not hashmap, 처음 배우는데 enummap, enum 키면 언제 enummap, 상태별 정책 테이블, what is enummap, java enum map basics

## 핵심 개념

먼저 아주 작게 잡으면 된다.

- `HashMap`은 "아무 key나 넣을 수 있는 범용 서랍"이다.
- `EnumMap`은 "이 enum 전용으로 미리 이름표가 붙은 칸막이 표"다.

즉 key 후보가 이미 `OrderStatus`, `DeliveryStatus` 같은 enum으로 고정됐다면, 그 순간부터는 범용 서랍보다 전용 칸막이 쪽이 코드 의도를 더 잘 보여 준다.

초보자 기준 핵심 질문은 하나다.

> "이 map의 key가 앞으로도 이 enum밖에 없나?"

답이 `yes`라면 `EnumMap`을 먼저 떠올리면 된다.

## 한눈에 보기

| 질문 | `HashMap`에 더 가까운 경우 | `EnumMap`에 더 가까운 경우 |
|---|---|---|
| key 종류가 계속 바뀌나 | `String`, `Long`, 여러 타입을 두루 쓴다 | 같은 enum 타입만 쓴다 |
| map이 표현하는 의미가 뭔가 | 범용 lookup 저장소 | 상태표, 정책표, 라벨표 |
| 읽는 사람이 코드에서 바로 알아야 하나 | "그냥 map"이어도 된다 | "enum 전용 표"라는 의도가 중요하다 |
| beginner 첫 선택 | 아직 key 정책이 열려 있다 | key 후보가 enum으로 닫혀 있다 |

짧게 외우면 이렇다.

> `HashMap`은 "아직 열려 있는 map", `EnumMap`은 "enum으로 닫힌 map"이다.

## `HashMap`에서 `EnumMap`으로 옮길 신호

아래 세 가지가 보이면 옮길 타이밍으로 보면 된다.

1. key가 항상 같은 enum이다.
2. 상태마다 붙는 값이 라벨, 요금, 허용 여부처럼 "작은 lookup 값"이다.
3. 같은 enum으로 `switch`나 `if`가 여러 군데 반복되기 시작한다.

예를 들면 이런 순간이다.

- `Map<OrderStatus, String>`로 상태별 배지 문구를 저장한다.
- `Map<OrderStatus, Integer>`로 상태별 수수료를 저장한다.
- `Map<OrderStatus, Boolean>`로 상태별 취소 가능 여부를 저장한다.

이때 `HashMap`도 동작은 하지만, `EnumMap`으로 바꾸면 "이건 주문 상태표"라는 메시지가 타입 선언에서 바로 보인다.

반대로 아직 key가 enum으로 확정되지 않았다면 굳이 옮길 이유가 없다.

- 오늘은 enum이지만 내일 `String` 코드값도 같이 섞일 수 있다.
- 외부 입력을 그대로 key로 쓰는 임시 집계 맵이다.

이런 경우는 범용 map인 `HashMap` 쪽이 자연스럽다.

## 실무에서 쓰는 모습

주문 상태 배지 문구를 붙이는 아주 흔한 예로 보자.

### 처음엔 `HashMap`으로 시작할 수 있다

```java
import java.util.HashMap;
import java.util.Map;

enum OrderStatus {
    CREATED, PAID, CANCELED
}

Map<OrderStatus, String> badgeLabels = new HashMap<>();
badgeLabels.put(OrderStatus.CREATED, "주문 생성");
badgeLabels.put(OrderStatus.PAID, "결제 완료");
badgeLabels.put(OrderStatus.CANCELED, "주문 취소");
```

이 코드도 틀리지는 않는다.  
하지만 읽는 사람 입장에서는 "그냥 map이구나"까지만 보인다.

### key가 enum으로 고정됐다면 `EnumMap`이 더 직접적이다

```java
import java.util.EnumMap;
import java.util.Map;

enum OrderStatus {
    CREATED, PAID, CANCELED
}

Map<OrderStatus, String> badgeLabels = new EnumMap<>(OrderStatus.class);
badgeLabels.put(OrderStatus.CREATED, "주문 생성");
badgeLabels.put(OrderStatus.PAID, "결제 완료");
badgeLabels.put(OrderStatus.CANCELED, "주문 취소");
```

바뀐 것은 생성 부분 한 줄이지만 읽히는 의미는 달라진다.

- `HashMap` 버전: "범용 map 하나를 만들었다"
- `EnumMap` 버전: "주문 상태 enum 전용 표를 만들었다"

beginner에게는 이 차이가 중요하다.  
나중에 상태별 수수료, 상태별 버튼 노출 여부가 붙어도 같은 패턴으로 확장할 수 있기 때문이다.

## 자주 헷갈리는 포인트

- `EnumMap`은 "enum 전용 map"이지 "상태 전이 규칙 엔진"이 아니다. `PAID`에서 `CANCELED`로 갈 수 있는지는 여전히 도메인 규칙이 결정한다.
- "성능이 더 빠르다더라"보다 먼저 봐야 할 포인트는 의도 표현이다. 초보 단계에서는 미세한 성능보다 "왜 이 map을 골랐는지"가 더 중요하다.
- 상태마다 큰 행동이 갈리면 `EnumMap`보다 enum 메서드나 도메인 메서드가 더 잘 맞을 수 있다.
- `ordinal()`로 배열 인덱스를 직접 맞추는 방식보다 `EnumMap`이 훨씬 읽기 쉽다. 초보자에게는 "몇 번째 칸인가"보다 "어떤 상태인가"가 더 중요하다.

## 무엇을 기준으로 고르면 되나

| 상황 | 먼저 떠올릴 선택 |
|---|---|
| key 후보가 아직 열려 있다 | `HashMap` |
| key가 같은 enum 타입으로 고정됐다 | `EnumMap` |
| 상태마다 작은 값 표가 필요하다 | `EnumMap` |
| 상태마다 큰 행동 규칙이 다르다 | enum 메서드 또는 도메인 메서드 |

판단 문장 하나로 정리하면 이렇다.

> "enum으로 닫힌 작은 lookup table"가 보이면 `HashMap`에서 `EnumMap`으로 옮긴다.

## 한 줄 정리

enum key만 쓰는 상태표, 라벨표, 정책표라면 `HashMap`보다 `EnumMap`이 더 정확한 이름표이며, 초보자에게도 "언제 범용 map을 멈추고 전용 map으로 바꾸는지"를 분명하게 보여 준다.
