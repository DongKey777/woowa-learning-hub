---
schema_version: 3
title: TreeMap 이웃 조회 마이크로 드릴
concept_id: data-structure/treemap-neighbor-query-micro-drill
canonical: false
category: data-structure
difficulty: beginner
doc_role: drill
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- treemap-neighbor-query
- strict-vs-inclusive-boundary
- treeset-to-treemap-transfer
aliases:
- treemap neighbor query drill
- treemap lowerkey floorkey ceilingkey higherkey
- ordered map exact match beginner
- treemap lower floor ceiling higher
- treemap 바로 이전 같거나 이전
- treemap 같거나 다음 바로 다음
- ordered map neighbor micro drill
symptoms:
- lowerKey와 floorKey가 exact match에서 왜 달라지는지 자꾸 헷갈린다
- TreeSet에서는 알겠는데 TreeMap으로 오면 같은 이름 규칙이 흔들린다
- 예약표에서 바로 이전 시작 시각과 같거나 이전 시작 시각을 구분하지 못한다
intents:
- drill
- comparison
prerequisites:
- data-structure/treeset-exact-match-drill
- data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer
next_docs:
- data-structure/treemap-key-entry-strictness-bridge
- data-structure/treemap-floorentry-ceilingentry-value-read-micro-drill
- data-structure/treemap-interval-entry-primer
linked_paths:
- contents/data-structure/treeset-exact-match-drill.md
- contents/data-structure/treemap-key-entry-strictness-bridge.md
- contents/data-structure/treemap-floorentry-ceilingentry-value-read-micro-drill.md
- contents/data-structure/treemap-interval-entry-primer.md
- contents/data-structure/treemap-string-prefix-range-mini-drill.md
- contents/language/java/navigablemap-navigableset-mental-model.md
confusable_with:
- data-structure/treeset-exact-match-drill
- data-structure/treemap-key-entry-strictness-bridge
- data-structure/treemap-string-prefix-range-mini-drill
forbidden_neighbors:
- contents/data-structure/treeset-exact-match-drill.md
- contents/data-structure/treemap-key-entry-strictness-bridge.md
expected_queries:
- TreeMap에서 lowerKey floorKey ceilingKey higherKey를 손으로 구분하는 짧은 드릴이 필요해
- 왜 lowerKey랑 floorKey가 exact match에서 달라지는지 예약표 예제로 보고 싶어
- TreeSet 감각을 TreeMap ordered map query로 옮기는 초급 연습이 필요해
- ordered map에서 strict와 inclusive 이웃 조회를 처음 배울 때 뭐부터 봐야 해
- 같은 key가 있을 때 higherKey와 ceilingKey가 왜 달라지는지 빠르게 확인하고 싶어
- reservation schedule에서 바로 이전 시작 시각과 같거나 이전 시작 시각을 구분하고 싶어
contextual_chunk_prefix: |
  이 문서는 TreeSet 감각을 TreeMap으로 옮기는 입문자가 lowerKey,
  floorKey, ceilingKey, higherKey의 exact match 차이를 확인
  질문으로 굳히는 drill이다. 바로 앞 시각 찾기, 같은 값도 허용한
  왼쪽 찾기, 같은 key가 있을 때 오른쪽 첫 값, ordered map 경계
  포함 여부, 예약표에서 이전 슬롯 잡기, strict와 inclusive를
  손으로 구분하기 같은 자연어 paraphrase가 본 문서의 이웃 조회
  규칙에 매핑된다.
---
# TreeMap Neighbor-Query Micro Drill

> 한 줄 요약: `TreeSet`에서 `lower/floor/ceiling/higher`를 먼저 익힌 초보자라면, `TreeMap`의 `lowerKey/floorKey/ceilingKey/higherKey`도 exact-match 규칙은 그대로고 `key -> value` 문맥만 추가된 버전이라고 보면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)
- [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [TreeMap 문자열 Prefix vs 사전순 Range Mini Drill](./treemap-string-prefix-range-mini-drill.md)
- [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- [Interval Greedy Patterns](../algorithm/interval-greedy-patterns.md)

retrieval-anchor-keywords: treemap neighbor query drill, treemap floorkey ceilingkey beginner, lower higher floor ceiling beginner, treemap lowerkey higherkey exact match, why lower floor different, exact match inclusive 여부, 왜 lower랑 floor가 달라요, floor ceiling exact match 포함, 같은 key 포함 여부 treemap, ordered map lower floor difference, treeset lower floor ceiling higher, reservation schedule treemap drill, lower higher 헷갈림, treeset to treemap handoff, set only intuition treemap

## 핵심 개념

이 문서는 특히 아래처럼 검색하는 초보자 질문을 바로 받는 entrypoint다.

- `왜 lower랑 floor가 달라요?`
- `floorKey는 exact match를 포함해요?`
- `같은 값이 있으면 ceiling이랑 higher가 왜 달라져요?`

초보자는 `TreeMap<startTime, reservationName>`을 "시작 시각 기준으로 정렬된 예약표"라고 보면 충분하다.

- `lowerKey(t)`: `t`보다 strict하게 왼쪽에 있는 가장 가까운 시작 시각
- `floorKey(t)`: `t`와 같거나 그보다 왼쪽에 있는 가장 가까운 시작 시각
- `ceilingKey(t)`: `t`와 같거나 그보다 오른쪽에 있는 가장 가까운 시작 시각
- `higherKey(t)`: `t`보다 strict하게 오른쪽에 있는 가장 가까운 시작 시각

문자열 key를 다루더라도 질문이 "`app`으로 시작하나?"처럼 prefix/range 구분이라면 이 문서보다 [TreeMap 문자열 Prefix vs 사전순 Range Mini Drill](./treemap-string-prefix-range-mini-drill.md)로 가는 편이 맞다. 여기서는 prefix가 아니라 ordered neighbor 질문만 다룬다.

한 줄로 줄이면 이렇다.

> `lower/floor`는 왼쪽, `ceiling/higher`는 오른쪽이고, `floor/ceiling`만 exact match를 포함한다.

## TreeSet에서 막 넘어왔다면

이 문서는 `TreeSet` drill을 먼저 풀고 "`set에서는 알겠는데 map이 되니까 또 헷갈려요`"라는 상태를 바로 받는 브리지다.
그럴 때는 새 규칙을 외우지 말고, 이미 아는 이름을 그대로 치환하면 된다.

| `TreeSet`에서 익힌 것 | `TreeMap`에서 그대로 읽는 것 | 초보자 메모 |
|---|---|---|
| `lower(x)` | `lowerKey(x)` | strict하게 왼쪽 |
| `floor(x)` | `floorKey(x)` | 같은 key 포함한 왼쪽 |
| `ceiling(x)` | `ceilingKey(x)` | 같은 key 포함한 오른쪽 |
| `higher(x)` | `higherKey(x)` | strict하게 오른쪽 |

여기서 달라지는 것은 딱 하나다.

- `TreeSet`은 값 줄을 읽는다.
- `TreeMap`은 정렬된 key 줄을 읽고, 필요하면 그 key에 붙은 value까지 이어서 본다.

즉 `TreeSet`에서 `floor(30)`을 맞혔다면, `TreeMap`에서 `floorKey(30)`도 같은 이유로 맞혀야 한다.
이 문서의 예제는 그 치환을 예약표 문맥으로 손에 붙이는 단계다.

ordered map query를 처음 붙일 때는 아래처럼 문장을 바로 번역하면 된다.

| 검색하거나 묻는 말 | 첫 번역 |
|---|---|
| `왜 lower랑 floor가 달라요?` | 같은 key가 있을 때 `lower`는 건너뛰고 `floor`는 멈춘다 |
| `exact match 포함 여부가 뭐예요?` | `floor/ceiling`만 같은 key를 포함한다 |
| `ordered map에서 lower/floor 언제 써요?` | 정렬된 key에서 strict/inclusive 이웃 조회를 나누는 질문이다 |

## 먼저 외울 한 장

같은 예약표에서 네 이름을 먼저 이렇게 번역하면 덜 헷갈린다.

| API | 방향 | exact match 포함 여부 | 초보자용 읽는 법 |
|---|---|---|---|
| `lowerKey(t)` | 왼쪽 | 제외 | "바로 이전 예약 시작" |
| `floorKey(t)` | 왼쪽 | 포함 | "같거나 바로 이전 예약 시작" |
| `ceilingKey(t)` | 오른쪽 | 포함 | "같거나 바로 다음 예약 시작" |
| `higherKey(t)` | 오른쪽 | 제외 | "바로 다음 예약 시작" |

핵심은 한 줄이다.

- `lower/higher`는 strict
- `floor/ceiling`은 inclusive

## exact match 포함 여부만 먼저 자르기

입문자가 가장 자주 헷갈리는 지점은 사실 방향보다 `같은 key를 포함하나`다.
이 한 표만 먼저 고정하면 `왜 lower랑 floor가 달라요`가 거의 끝난다.

| 기준 질문 | exact match가 있으면 | exact match가 없으면 |
|---|---|---|
| 왼쪽을 보고 싶다 | `lower`는 한 칸 더 왼쪽, `floor`는 그 자리에 멈춤 | 둘 다 같은 왼쪽 이웃 |
| 오른쪽을 보고 싶다 | `higher`는 한 칸 더 오른쪽, `ceiling`은 그 자리에 멈춤 | 둘 다 같은 오른쪽 이웃 |

짧게 번역하면 이렇게 외우면 된다.

- `floor/ceiling` = `같은 값 있으면 포함`
- `lower/higher` = `같은 값 있어도 제외`

이 규칙은 `ordered map query pack` 관점에서 한 줄로 요약하면 아래와 같다.

| 질문 | 같은 key가 있으면 | learner 메모 |
|---|---|---|
| `lower vs floor` | `lower`는 왼쪽으로 더 간다, `floor`는 그 자리에 선다 | `왜 lower랑 floor가 달라요`의 핵심 |
| `higher vs ceiling` | `higher`는 오른쪽으로 더 간다, `ceiling`은 그 자리에 선다 | `exact match 포함 여부`의 오른쪽 버전 |

## 한눈에 보기

오늘 예약표가 아래처럼 있다고 하자.

```text
09:00 상담
10:30 리뷰
13:00 점검
15:30 배포
```

| 질문 | 먼저 볼 API | 읽는 법 |
|---|---|---|
| `10:30` 바로 이전 예약은? | `lowerKey(10:30)` | exact match는 빼고 왼쪽 |
| `10:30` 예약이 딱 있으면 그 자리도 포함하나? | `floorKey(10:30)` | exact match면 그 자리 포함 |
| `10:30` 예약이 딱 있으면 그 자리도 포함한 오른쪽은? | `ceilingKey(10:30)` | exact match면 그 자리 포함 |
| `10:30`보다 strict하게 다음 예약은? | `higherKey(10:30)` | exact match는 빼고 오른쪽 |

## exact match 한 번에 고정하기

같은 `10:30`을 넣었을 때 네 결과를 한 표로 보면 inclusive/strict 차이가 바로 보인다.

| 호출 | 답 | 왜 이렇게 나오나 |
|---|---|---|
| `lowerKey(10:30)` | `09:00` | `10:30` 자리는 제외 |
| `floorKey(10:30)` | `10:30` | `10:30` 자리 포함 |
| `ceilingKey(10:30)` | `10:30` | `10:30` 자리 포함 |
| `higherKey(10:30)` | `13:00` | `10:30` 자리는 제외 |

초보자는 이 표만 손으로 맞히면 `lower/floor`와 `ceiling/higher`를 거의 분리할 수 있다.
여기서 검색 문장을 다시 붙이면 아래처럼 읽으면 된다.

- `왜 lower랑 floor가 달라요?` -> exact match가 있어서 strict/inclusive 차이가 드러난다
- `exact match 포함 여부가 뭐예요?` -> `floor/ceiling`은 포함, `lower/higher`는 제외다

## 앞쪽 3문제 먼저 풀기

같은 예약표를 계속 쓴다.

```text
09:00 상담
10:30 리뷰
13:00 점검
15:30 배포
```

### 예제 1. exact match가 있는 시각

질문: `10:30`을 넣으면?

| 호출 | 답 |
|---|---|
| `lowerKey(10:30)` | `09:00` |
| `floorKey(10:30)` | `10:30` |
| `ceilingKey(10:30)` | `10:30` |
| `higherKey(10:30)` | `13:00` |

해석: exact match가 있으면 `floor/ceiling`만 그 자리에서 멈추고, `lower/higher`는 strict하게 한 칸 건너뛴다.

### 예제 2. 두 예약 사이 시각

질문: `11:00`을 넣으면?

| 호출 | 답 |
|---|---|
| `lowerKey(11:00)` | `10:30` |
| `floorKey(11:00)` | `10:30` |
| `ceilingKey(11:00)` | `13:00` |
| `higherKey(11:00)` | `13:00` |

해석: `11:00`은 key로 없으므로 strict/inclusive 차이가 사라지고, 왼쪽 둘과 오른쪽 둘이 각각 같은 답으로 모인다.

### 예제 3. 첫 예약보다 더 이른 시각

질문: `08:00`을 넣으면?

| 호출 | 답 |
|---|---|
| `lowerKey(08:00)` | `null` |
| `floorKey(08:00)` | `null` |
| `ceilingKey(08:00)` | `09:00` |
| `higherKey(08:00)` | `09:00` |

해석: 왼쪽에는 예약이 없고, 오른쪽 첫 예약만 잡힌다.

## 뒤쪽 3문제 이어서 풀기

### 예제 4. 마지막 예약보다 더 늦은 시각

질문: `17:00`을 넣으면?

| 호출 | 답 |
|---|---|
| `lowerKey(17:00)` | `15:30` |
| `floorKey(17:00)` | `15:30` |
| `ceilingKey(17:00)` | `null` |
| `higherKey(17:00)` | `null` |

해석: 이번에는 반대로 오른쪽 예약이 없다.

### 예제 5. 막 비어 있는 틈 찾기

질문: `10:00`부터 30분 미팅을 넣고 싶다. 양옆 시작 시각은?

| 호출 | 답 |
|---|---|
| `lowerKey(10:00)` | `09:00` |
| `floorKey(10:00)` | `09:00` |
| `ceilingKey(10:00)` | `10:30` |
| `higherKey(10:00)` | `10:30` |

해석: 초보자에게는 이 단계까지만 맞혀도 충분하다. 바로 다음 단계인 "`key`에서 `entry`로 바꿔 strict/inclusive를 그대로 유지하는 법"은 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)에서 이어지고, `entry`에서 종료 시각을 읽는 연습은 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)에서 붙인 뒤, 충돌 검사와 gap check는 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)에서 확장된다.

### 예제 6. 점심 직후 가장 가까운 예약 찾기

질문: `13:05`를 넣으면?

| 호출 | 답 |
|---|---|
| `lowerKey(13:05)` | `13:00` |
| `floorKey(13:05)` | `13:00` |
| `ceilingKey(13:05)` | `15:30` |
| `higherKey(13:05)` | `15:30` |

해석: 이미 지난 가장 가까운 예약과, 앞으로 올 가장 가까운 예약을 한 번에 읽는 연습이다.

## TreeSet으로 바꾸면 더 쉬운 이유

같은 시간을 value 없이 `TreeSet<LocalTime>`에 넣어도 읽는 감각은 거의 같다.

| `TreeMap`에서 보던 질문 | `TreeSet`에서 대응되는 질문 |
|---|---|
| `floorKey(10:30)` | `floor(10:30)` |
| `lowerKey(10:30)` | `lower(10:30)` |
| `ceilingKey(10:30)` | `ceiling(10:30)` |
| `higherKey(10:30)` | `higher(10:30)` |

즉 "시간 자체만 있으면 되는가"와 "시간에 이름이나 종료 시각 value도 붙여야 하는가"만 다르고, 이웃 조회 멘탈 모델은 그대로 재사용된다.

- 시간 값만 관리하면 `TreeSet`
- `시작 시각 -> 예약 정보`를 같이 들고 가면 `TreeMap`

따라서 초보자에게 가장 안전한 학습 순서는 아래처럼 짧다.

1. `TreeSet`에서 strict/inclusive를 손으로 맞힌다.
2. 같은 표를 `TreeMap`의 `Key` 버전으로 다시 읽는다.
3. 그다음에야 `Entry`로 바꿔 value를 함께 읽는다.

이 순서를 따르면 `map`이라는 단어 때문에 exact-match 규칙까지 새로 외우는 실수를 줄일 수 있다.

## 상세 분해

초보자 기준으로는 아래 네 줄만 고정하면 된다.

1. key는 `예약 시작 시각`이다.
2. `lowerKey`와 `higherKey`는 exact match를 제외한다.
3. `floorKey`와 `ceilingKey`는 exact match를 포함한다.
4. 범위를 벗어나면 없는 쪽은 `null`이다.

이 문서에서는 일부러 `Entry` 대신 `Key`만 썼다.
먼저 "어느 시작 시각이 잡히는가"를 손으로 맞히는 게 목적이기 때문이다.
다음 문서에서는 같은 질문을 `Entry`로 바꿔 `종료 시각 value`까지 읽는 연습을 붙이면 된다.

## 흔한 오해와 함정

- `floorKey`를 "무조건 이전 값"으로 외우면 exact match에서 틀린다. `같은 key`도 포함한다.
- `lowerKey`를 `floorKey`와 같은 의미로 읽으면 exact match에서 틀린다. `lowerKey`는 strict하게 같은 key를 뺀다.
- `ceilingKey`를 "다음 값"으로만 외우면 exact match에서 틀린다. 이것도 `같은 key`를 포함한다.
- `higherKey`는 `ceilingKey`의 strict 버전이다. exact match를 포함하지 않는다.
- `null`이 나오면 에러라고 느끼기 쉽지만, 이웃이 없다는 정상 결과다.
- 예약 충돌 여부까지 한 번에 판단하려 하면 초반에 과부하가 온다. 먼저 `strict/inclusive 왼쪽/오른쪽`만 맞히고, 다음 단계에서 `floorEntry`/`ceilingEntry`로 종료 시각까지 읽는 편이 낫다.
- `ordered map`을 "정렬된 출력 도구" 정도로만 보면 `lower/floor` 질문이 갑자기 뜬금없어 보일 수 있다. 이 문서에서는 `정렬된 key에서 가장 가까운 이웃을 찾는 도구`로 읽어야 한다.
- "`못 찾으면 예외인가 null인가`가 먼저 헷갈리면 [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)에서 빈 컬렉션/경계 바깥 결과를 한 장으로 먼저 보고 오는 편이 안전하다.

## 실무에서 쓰는 모습

예약 시스템에서는 "`지금 이후 첫 예약`", "`이 시각 바로 전 예약`", "`같은 시각이 있으면 포함할까 건너뛸까`" 같은 이웃 조회가 자주 나온다.
이때 `HashMap`은 key를 다시 정렬해야 하지만, `TreeMap`은 `lowerKey`/`floorKey`/`ceilingKey`/`higherKey`로 바로 읽을 수 있다.

그래서 초급자에게는 `TreeMap`을 "정렬된 예약표에서 strict/inclusive 이웃을 찾는 도구"로 먼저 잡아 두는 편이 value-read 드릴과 interval 문서로 넘어갈 때 훨씬 덜 막힌다.

## 더 깊이 가려면

- 시작 시각만 찾는 단계에서 `lower/floor/ceiling/higher`를 `Entry`로 바꾸는 브리지가 먼저 필요하면 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- 시작 시각만 찾는 단계 다음으로 종료 시각 value까지 읽고 싶다면 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- 예약 충돌 검사와 gap check까지 붙이고 싶다면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- 값만 있는 정렬 줄로 exact match부터 다시 붙이고 싶다면 [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- `Set` 선택 기준까지 같이 복습하고 싶다면 [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- `lower`/`higher`까지 포함한 전체 이름표를 한 번에 보고 싶다면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- 한 번 정렬해서 끝나는 구간 문제인지, 계속 insert/query가 들어오는 문제인지 구분하려면 [Interval Greedy Patterns](../algorithm/interval-greedy-patterns.md)

## 한 줄 정리

`TreeMap` 초급 이웃 조회는 "예약 시작 시각 줄에서 `lower/floor/ceiling/higher` 중 exact match를 포함하는 쪽만 구분한다"로 잡으면 `TreeSet`과 interval 문서까지 같은 감각으로 이어진다.
