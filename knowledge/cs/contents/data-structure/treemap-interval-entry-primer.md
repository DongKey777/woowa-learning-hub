# TreeMap Interval Entry Primer

> 한 줄 요약: `TreeMap<start, end>`를 "시작 시각 기준으로 정렬된 예약 줄"로 보면 `floorKey`/`floorEntry`는 왼쪽 예약, `ceilingKey`/`ceilingEntry`는 오른쪽 예약, `subMap`은 시간창 안에서 시작한 예약 묶음을 꺼내는 도구다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: treemap interval entry primer basics, treemap interval entry primer beginner, treemap interval entry primer intro, data structure basics, beginner data structure, 처음 배우는데 treemap interval entry primer, treemap interval entry primer 입문, treemap interval entry primer 기초, what is treemap interval entry primer, how to treemap interval entry primer
> 관련 문서:
> - [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [Neighbor-query 워크시트 바로가기](../language/java/navigablemap-navigableset-mental-model.md#작은-워크시트-timestamp와-score-bucket에서-이웃-질의)
> - [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
> - [Disjoint Interval Set](./disjoint-interval-set.md)
> - [Interval Tree](./interval-tree.md)

> retrieval-anchor-keywords: treemap interval primer, treemap reservation beginner, floorKey ceilingKey subMap interval, floorEntry ceilingEntry booking, lowerEntry floorEntry ceilingEntry higherEntry, lowerKey floorKey ceilingKey higherKey, key return vs entry return treemap, floorEntry ceilingEntry trace table, treemap timestamp trace, calendar booking treemap, ordered map interval beginner, room booking gap check, reservation conflict floorEntry, next reservation ceilingEntry, subMap calendar view, interval neighbor lookup, calendar booking i treemap, tree map gap check, floor ceiling interval entry, neighbor query worksheet, lower floor ceiling higher worksheet, treemap neighbor query beginner, online interval insert, offline interval merge, insert interval vs merge intervals, calendar booking vs merge intervals

## 30초 워밍업

`lower`/`floor`/`ceiling`/`higher` 이름이 아직 바로 안 떠오르면 이 문서를 억지로 읽기보다 먼저 [neighbor-query 워크시트](../language/java/navigablemap-navigableset-mental-model.md#작은-워크시트-timestamp와-score-bucket에서-이웃-질의)로 가는 편이 빠르다.

거기서 `왼쪽 바로 전` / `같거나 바로 왼쪽` / `같거나 바로 오른쪽` / `오른쪽 바로 다음`만 손으로 한 번 구해 보고 돌아오면, 이 문서의 `예약 왼쪽 이웃` / `예약 오른쪽 이웃` 설명이 바로 연결된다.

## 먼저 잡을 mental model

`TreeMap` interval 문제를 처음 볼 때는 key/value를 추상적으로 보지 말고 이렇게 생각하는 편이 쉽다.

> key는 "예약이 시작하는 시각", value는 "그 예약이 끝나는 시각"이다.

즉 `TreeMap<start, end>`는 아래처럼 **시작 시각 기준으로 정렬된 시간표 한 줄**이다.

```text
09:00 -> [09:00, 10:00)
10:30 -> [10:30, 11:00)
13:00 -> [13:00, 14:00)
```

이 줄에서 세 API를 질문으로 바꾸면 감이 빨라진다.

| API | 초보자용 질문 | 보통 쓰는 장면 |
|---|---|---|
| `floorKey(t)` 또는 `floorEntry(t)` | `t`의 왼쪽에서 가장 가까운 예약은? | 새 예약이 왼쪽 예약과 부딪히는지 |
| `ceilingKey(t)` 또는 `ceilingEntry(t)` | `t`의 오른쪽에서 가장 가까운 예약은? | 다음 예약이 언제 시작하는지 |
| `subMap(a, true, b, false)` | `[a, b)` 안에서 시작한 예약은? | 캘린더 시간창 조회 |

실전에서는 end 값도 바로 꺼내야 해서 `floorKey`/`ceilingKey`보다 `floorEntry`/`ceilingEntry`를 더 자주 쓰기도 한다.

헷갈림을 줄이려면 `Key` 계열과 `Entry` 계열을 같이 보면 된다.

| 찾고 싶은 위치 | key만 필요할 때 | start와 end를 같이 볼 때 | exact match 포함 여부 |
|---|---|---|---|
| 기준보다 바로 왼쪽 | `lowerKey(t)` | `lowerEntry(t)` | 제외 |
| 기준과 같거나 바로 왼쪽 | `floorKey(t)` | `floorEntry(t)` | 포함 |
| 기준과 같거나 바로 오른쪽 | `ceilingKey(t)` | `ceilingEntry(t)` | 포함 |
| 기준보다 바로 오른쪽 | `higherKey(t)` | `higherEntry(t)` | 제외 |

초보자 기준으로는 이렇게 기억하면 충분하다.

- `lower/floor/ceiling/higher`는 "어느 방향 이웃을 찾는가"를 정한다.
- `Key` vs `Entry`는 "반환값에 end 정보가 같이 오나"만 다르다.
- 예약 문제에서는 보통 충돌 여부를 보려면 end가 필요하므로 `Entry` 쪽이 더 바로 쓸 수 있다.

예를 들어 같은 시간표에서 `t = 10:30`이면:

- `floorKey(10:30)` -> `10:30`
- `floorEntry(10:30)` -> `10:30 -> [10:30, 11:00)`
- `higherKey(10:30)` -> `13:00`
- `higherEntry(10:30)` -> `13:00 -> [13:00, 14:00)`

## 먼저 잡을 mental model (계속 2)

즉 "`floor`는 exact match를 포함하나?", "`Entry`는 key 말고 value도 같이 주나?" 두 질문만 먼저 분리하면 API 이름이 훨씬 덜 섞인다.

`lower`/`floor`/`ceiling`/`higher` 이름이 아직 손에 안 붙으면, 위의 [neighbor-query 워크시트](../language/java/navigablemap-navigableset-mental-model.md#작은-워크시트-timestamp와-score-bucket에서-이웃-질의)에서 timestamp 예시를 손으로 한 번 따라가고 이 문서로 돌아오면 예약 문제 해석이 훨씬 빨라진다.

## 먼저 끊는 첫 분기: online insert vs offline merge

초보자가 interval 문제에서 가장 많이 섞는 두 문장은 아래 두 개다.

- `새 예약이 지금 들어왔는데 넣어도 되나?`
- `이미 있는 구간 목록을 한 번 쭉 합쳐서 정리하라`

둘 다 interval을 다루지만, **질문 시점**이 다르다.

| online interval insert | offline interval merge |
|---|---|
| 새 구간이 하나씩 들어올 때마다 바로 판단한다 | 구간 목록이 이미 전부 주어진 뒤 한 번에 정리한다 |
| `겹치나?`, `넣어도 되나?`, `다음 빈 시간은?`을 자주 묻는다 | `merge intervals`, `겹치는 구간 합치기`가 핵심이다 |
| 양옆 이웃인 `floorEntry` / `ceilingEntry`가 먼저 나온다 | 보통 시작점 기준 정렬 후 왼쪽에서 오른쪽으로 sweep한다 |
| 대표 구조: `TreeMap`, [Disjoint Interval Set](./disjoint-interval-set.md), [Interval Tree](./interval-tree.md) | 대표 라우트: [구간 / Interval Greedy 패턴](../algorithm/interval-greedy-patterns.md), [정렬 알고리즘](../algorithm/sort.md) |
| 예: `calendar booking`, `online reservation insert` | 예: `merge intervals`, `겹치는 회의 구간 정리` |

한 줄로 줄이면 이렇다.

- online insert: "새 손님이 올 때마다 앞뒤 예약을 본다"
- offline merge: "예약표 전체를 펼쳐 놓고 한 번 정리한다"

이 문서는 왼쪽 열, 즉 `online interval insert` 쪽 입문서다.

## 세 연산이 바로 문제 문장으로 바뀌는 순간

| 문제 문장 | 먼저 보는 API | 왜 이 API가 맞는가 |
|---|---|---|
| `09:30~10:15` 예약을 넣어도 되나? | `floorEntry(start)` + `ceilingEntry(start)` | 새 예약 양옆 이웃을 보면 된다 |
| 지금 이후 가장 가까운 예약은? | `ceilingEntry(now)` | "오른쪽 첫 예약"을 찾는 질문이다 |
| 오전 회의 목록만 보여 줘 | `subMap(09:00, true, 12:00, false)` | 시간창 안에서 시작한 예약 묶음이 필요하다 |
| `11:00~12:00` 빈 구간이 있나? | `floorEntry(start)` + `ceilingEntry(start)` | 왼쪽 예약의 종료 시각과 오른쪽 예약의 시작 시각 사이를 본다 |

여기서 핵심은 `TreeMap`이 interval tree처럼 "겹치는 모든 구간 검색"을 바로 해 주는 구조가 아니라,
**정렬된 이웃과 range view를 빠르게 꺼내는 구조**라는 점이다.

## 같은 캘린더로 한 번에 보기

다음 예약들이 있다고 하자.

```text
09:00 -> [09:00, 10:00)
10:30 -> [10:30, 11:00)
13:00 -> [13:00, 14:00)
```

### 작은 trace table: timestamp별 `floorEntry` / `ceilingEntry`

같은 예약표에서 초급자는 "특정 시각 `t`를 넣으면 양옆 예약이 무엇으로 잡히는가"를 먼저 손으로 확인해 두면 읽기가 빨라진다.

| `t` | `floorEntry(t)` | `ceilingEntry(t)` | 초급자용 해석 |
|---|---|---|---|
| `09:30` | `09:00 -> [09:00, 10:00)` | `10:30 -> [10:30, 11:00)` | `09:30`의 왼쪽 예약은 9시 예약, 오른쪽 첫 예약은 10시 30분 예약 |
| `10:00` | `09:00 -> [09:00, 10:00)` | `10:30 -> [10:30, 11:00)` | exact match가 없으므로 왼쪽은 "가장 가까운 이전 시작", 오른쪽은 "가장 가까운 다음 시작" |
| `10:30` | `10:30 -> [10:30, 11:00)` | `10:30 -> [10:30, 11:00)` | exact match가 있으면 `floorEntry`와 `ceilingEntry`가 둘 다 같은 예약을 가리킨다 |

이 표 하나만 기억해도 아래 예시의 `예약 가능 여부`, `충돌 검사`, `gap check`를 읽을 때 왜 양옆 이웃을 먼저 보는지 훨씬 덜 헷갈린다.

### 1. 예약 가능 여부: `[10:00, 10:30)`은 비어 있나?

- `floorEntry(10:00)` -> `09:00 -> [09:00, 10:00)`
- `ceilingEntry(10:00)` -> `10:30 -> [10:30, 11:00)`

반열린 구간 `[start, end)` 기준이라면:

- 왼쪽 예약의 끝 `10:00`은 새 예약 시작 `10:00`을 넘지 않는다
- 오른쪽 예약의 시작 `10:30`은 새 예약 끝 `10:30`보다 빠르지 않다

그래서 `[10:00, 10:30)`은 들어갈 수 있다.

### 2. 충돌 검사: `[09:30, 10:15)`는 왜 막히나?

- `floorEntry(09:30)` -> `09:00 -> [09:00, 10:00)`

왼쪽 예약의 끝 `10:00`이 새 예약 시작 `09:30`보다 뒤이므로 이미 겹친다.
이런 패턴이 `calendar booking I`류 문제에서 자주 나온다.

### 3. 캘린더 보기: 오전 예약만 꺼내기

- `subMap(09:00, true, 12:00, false)`
- 결과: `09:00`, `10:30`

이건 "오전 안에서 **시작한** 예약"을 보는 질문에 잘 맞는다.

### 4. gap check: `11:00` 이후 첫 빈 시간대는?

## 같은 캘린더로 한 번에 보기 (계속 2)

- `floorEntry(11:00)` -> `10:30 -> [10:30, 11:00)`
- `ceilingEntry(11:00)` -> `13:00 -> [13:00, 14:00)`

그러면 `11:00~13:00`이 바로 다음 빈 gap이다.
초보자 입장에서는 gap도 결국 "왼쪽 종료 시각"과 "오른쪽 시작 시각" 사이를 보는 문제라고 생각하면 된다.

## 왜 예약 문제에서 양옆 이웃만 자주 보나

이 패턴이 깔끔하게 먹히는 전제는 보통 다음과 같다.

- 예약들을 `start` 기준으로 정렬해 저장한다
- 저장된 예약들은 서로 겹치지 않게 유지한다
- 그래서 새 예약이 부딪힌다면 보통 가장 가까운 왼쪽/오른쪽 이웃에서 먼저 드러난다

이 전제에서는 `TreeMap<start, end>`만으로도 다음 문제를 꽤 많이 풀 수 있다.

- 예약 accept/reject
- 바로 다음 예약 찾기
- gap check
- 시간창 예약 보기

이 단계가 익숙해진 뒤에야 `Disjoint Interval Set`이나 `Interval Tree`로 넘어가도 늦지 않다.

## 자주 헷갈리는 지점

- `insert interval`이라는 말을 봤다고 무조건 offline merge로 가면 안 된다.
  문제 문장이 `새 구간이 들어올 때마다`인지, `배열 하나를 입력으로 받고 한 번 합치라`인지 먼저 본다.
- `subMap`은 "범위 안에서 시작한 예약"을 보여 준다.
  `08:50~09:10` 예약처럼 더 일찍 시작했지만 범위 안까지 이어지는 interval은 `subMap(09:00, ...)`만으로는 놓칠 수 있다. 이런 경우 `floorEntry(rangeStart)`를 함께 봐야 한다.
- `floorEntry` 하나만으로 모든 overlap query가 해결되지는 않는다.
  저장된 interval들이 서로 겹칠 수 있는 일반 상황이라면 더 왼쪽 interval이 길게 뻗어 있을 수 있다. 그때는 `Interval Tree` 같은 search 구조가 필요하다.
- `[start, end)`와 `[start, end]`를 섞으면 조건식이 바로 틀어진다.
  예약/캘린더 문제는 반열린 구간 `[start, end)`를 쓰는지 먼저 확인하는 편이 안전하다.

## 어디까지는 `TreeMap`으로 버티고, 언제 넘어가나

| 상황 | 먼저 볼 구조 | 이유 |
|---|---|---|
| 새 예약 하나를 넣을지 말지, gap이 있는지 본다 | `TreeMap` interval entry 패턴 | 양옆 이웃 확인이 핵심이다 |
| 넣을 때마다 merge해서 항상 비겹침 상태를 유지한다 | [Disjoint Interval Set](./disjoint-interval-set.md) | canonical form 유지가 본업이다 |
| 겹치는 interval 전부를 찾거나 stabbing query가 많다 | [Interval Tree](./interval-tree.md) | search workload가 중심이다 |
| interval이 한 번에 전부 주어지고 최대 겹침 수만 센다 | [Sweep Line Overlap Counting](../algorithm/sweep-line-overlap-counting.md) | online structure보다 offline 계산이 맞다 |

## 다음에 어디로 가면 좋은가

- `TreeMap` 자체 선택 이유를 다시 묶어 보고 싶으면 [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
- `lower/floor/ceiling/higher` 이름이 아직 헷갈리면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- 바로 손으로 확인하는 표가 필요하면 [neighbor-query 워크시트](../language/java/navigablemap-navigableset-mental-model.md#작은-워크시트-timestamp와-score-bucket에서-이웃-질의)
- 예약을 넣을 때 merge/reject/gap tracking을 본격적으로 다루려면 [Disjoint Interval Set](./disjoint-interval-set.md)
- 겹치는 interval 전체 탐색으로 넘어가면 [Interval Tree](./interval-tree.md)

## 한 줄 정리

`TreeMap` interval 입문은 어렵게 보면 tree 이야기지만, 초보자에게는 "왼쪽 예약, 오른쪽 예약, 시간창 view" 세 가지 질문으로 바꾸는 순간 훨씬 쉬워진다.
