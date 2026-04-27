# 0-1 BFS lexicographic tie mini note

> 한 줄 요약: 최단 거리만 맞으면 되는 기본형과 달리, "사전순으로 더 작은 경로"까지 요구되면 `newDist == dist[next]`일 때도 어떤 부모가 더 앞서는지 비교하는 추가 규칙이 필요하다.

**난이도: 🟢 Beginner**

관련 문서:

- [0-1 BFS parent tie mini note](./zero-one-bfs-parent-tie-mini-note.md)
- [0-1 BFS 전체 경로 사전순 비교 브리지](./zero-one-bfs-full-path-lexicographic-bridge.md)
- [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)
- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 0-1 bfs lexicographic tie, zero one bfs lexicographic path, 0-1 bfs 사전순 경로, 0-1 bfs equal distance lexicographic, 0-1 bfs same distance lexicographic parent, 0-1 bfs parent tie break lexicographic, lexicographically smallest shortest path 0-1 bfs, shortest path lexicographic tie break, 0-1 bfs newdist == dist lexicographic, 0-1 bfs 동점 사전순, 0-1 bfs parent 비교, 0-1 bfs 작은 경로 선택, 0-1 bfs equal cost path order, 0-1 bfs tie break beginner, zero one bfs lexicographic tie mini note basics

## 먼저 감각부터

기본형 `0-1 BFS`는 보통 이렇게 끝난다.

- 최단 거리 구하기
- 그 최단 거리 하나를 만드는 아무 경로 하나 복원하기

하지만 문제 문장이 이렇게 바뀌면 얘기가 달라진다.

> 최단 거리 경로가 여러 개면, 사전순으로 가장 작은 경로를 출력하라.

이제는 "아무 최단 경로"가 아니라
"최단 경로들 중에서도 더 앞서는 경로"를 골라야 한다.

## 기본형과 무엇이 달라지나

| 목표 | `newDist == dist[next]`일 때 |
|---|---|
| 최단 거리만 맞추면 됨 | 보통 그대로 둠 |
| 사전순 tie-break도 필요 | 부모 후보를 추가 비교해야 할 수 있음 |

즉 거리만 보면 동점이지만,
경로 문자열이나 정점 번호 나열로 보면 우열이 생길 수 있다.

## 어느 분기에만 추가 로직이 붙나

초보자 기준으로는 먼저 이 표 하나를 고정하면 된다.

| 분기 | 기본형 동작 | 사전순 tie-break형 동작 |
|---|---|---|
| `newDist < dist[next]` | 무조건 갱신 | 무조건 갱신 |
| `newDist == dist[next]` | 보통 그대로 둠 | **여기서만** 경로 순서 비교 |
| `newDist > dist[next]` | 버림 | 버림 |

즉 "사전순 요구가 생겼다"는 말은
알고리즘 전체를 갈아엎는다는 뜻이 아니라,
보통 `==` 분기에만 작은 비교문 하나가 더 생긴다는 뜻에 가깝다.

## beginner implementation sketch

고급 자료구조 없이도, 일단 읽는 감각은 아래처럼 잡으면 된다.

```python
if new_dist < dist[nxt]:
    dist[nxt] = new_dist
    parent[nxt] = cur
    push_by_edge_weight(nxt, w)   # 0이면 앞, 1이면 뒤
elif new_dist == dist[nxt]:
    if lexicographically_better(cur, parent[nxt]):
        parent[nxt] = cur
```

여기서 핵심은 두 가지다.

- 거리 갱신과 deque 삽입은 여전히 `<` 분기가 중심이다.
- 사전순 비교는 `new_dist == dist[nxt]`일 때만 켠다.

즉 초보자가 먼저 봐야 하는 "추가 path-order logic"의 자리 자체는
`elif new_dist == dist[nxt]:` 바로 그 줄이다.

## 이 스케치에서 당장 알면 되는 것

`lexicographically_better(cur, parent[nxt])`를 보고
"벌써 고급 자료구조를 알아야 하나?"라고 느끼기 쉽다.
이 문서에서는 거기까지 들어가지 않아도 된다.

지금 단계에서 먼저 잡을 것은:

- 기본형은 `==`를 보통 지나친다
- 사전순 요구가 있으면 `==`에서만 부모 후보를 다시 본다
- 비교 대상이 "부모 번호 한 칸"인지 "전체 경로"인지는 문제 정의에 따라 달라진다

즉 이 문서의 beginner bridge는
"비교를 **어떻게 빠르게** 하냐"보다
"비교를 **어느 분기에서 시작**하냐"를 고정하는 데 초점이 있다.

## 작은 예시

```text
정점 번호가 작은 쪽이 사전순으로 앞선다고 하자.

1 -> 2 비용 0
1 -> 3 비용 0
2 -> 4 비용 1
3 -> 4 비용 1
```

`1 -> 2 -> 4`와 `1 -> 3 -> 4`의 총비용은 둘 다 `1`이다.

하지만 경로 나열로 보면:

- `1, 2, 4`
- `1, 3, 4`

사전순으로는 `1, 2, 4`가 더 앞선다.

그래서 이 문제에서는 `dist[4] = 1`만 맞추는 것으로 끝나지 않고,
`parent[4]`를 `2`로 둘지 `3`으로 둘지도 규칙이 필요하다.

## tie 장면 한 페이지 손추적 표

아래 표는 "언제 `dist`는 그대로인데 `parent`만 바뀌는가?"를
deque, 거리표, 부모표를 같이 놓고 한 번에 보여 준다.

```text
정점 번호가 작은 쪽이 사전순으로 앞선다고 하자.

1 -> 2 비용 0
1 -> 3 비용 0
3 -> 4 비용 1
2 -> 4 비용 1
```

핵심은 `4`를 **처음 볼 때**가 아니라,
`4`를 **같은 거리로 다시 볼 때** 사전순 비교가 켜진다는 점이다.

초기 상태는 아래처럼 둔다.

```text
dist[1] = 0
dist[2] = dist[3] = dist[4] = INF
parent[*] = 없음
deque = [1@0]
```

| step | 꺼낸 상태 | 이번 줄에서 본 간선 | deque 상태 (front -> back) | `dist[2]` | `dist[3]` | `dist[4]` | `parent[2]` | `parent[3]` | `parent[4]` |
|---|---|---|---|---:|---:|---:|---|---|---|
| 0 | 시작 전 | `1@0`만 넣고 시작 | `[1@0]` | `INF` | `INF` | `INF` | `-` | `-` | `-` |
| 1 | `1@0` | `1 -> 2 (0)`, `1 -> 3 (0)` | `[3@0, 2@0]` | `0` | `0` | `INF` | `1` | `1` | `-` |
| 2 | `3@0` | `3 -> 4 (1)` | `[2@0, 4@1]` | `0` | `0` | `1` | `1` | `1` | `3` |
| 3 | `2@0` | `2 -> 4 (1)`도 `newDist = 1` | `[4@1]` | `0` | `0` | `1` | `1` | `1` | `2`로 교체 |
| 4 | `4@1` | 더 나가는 간선 없음 | `[]` | `0` | `0` | `1` | `1` | `1` | `2` |

step 3이 이 문서의 핵심이다.

| 항목 | step 2 직후 | step 3 비교 시점 |
|---|---|---|
| 이미 기록된 경로 | `1, 3, 4` | `parent[4] = 3` |
| 새로 들어온 동점 후보 | 없음 | `1, 2, 4` |
| 거리 비교 | `dist[4] = 1` | `newDist = 1`, 즉 동점 |
| 그다음 할 일 | 첫 기록이라 바로 저장 | 사전순 비교 후 더 앞서는 쪽 부모 선택 |

왜 step 1에서 deque가 `[3@0, 2@0]`가 되냐고 묻는다면,
이 예시는 `1 -> 2`를 먼저 읽고 `1 -> 3`을 나중에 읽는 순서를 가정했기 때문이다.
둘 다 비용 `0`이라 `push_front`가 두 번 일어나면 마지막에 넣은 `3`이 앞에 선다.

그래서 실제 흐름은 이렇게 읽으면 된다.

## tie 장면 한 페이지 손추적 표 (계속 2)

```text
step 2:
    3을 먼저 처리해서 4를 처음 기록
    dist[4] = 1, parent[4] = 3

step 3:
    2를 나중에 처리했더니 4에 같은 거리 1로 또 도착
    newDist == dist[4]
    이제서야 "3을 유지할까, 2로 바꿀까?"를 비교
    사전순은 1,2,4가 앞이므로 parent[4]는 2로 교체
```

즉 사전순 비교는 "모든 간선에서 항상" 도는 게 아니라,
보통 **동점 후보가 실제로 생긴 그 순간**에만 의미가 있다.

## 왜 단순히 "번호 작은 부모"만 보면 위험한가

초보자가 자주 하는 단순화는 이것이다.

> "동점이면 그냥 부모 번호가 작은 쪽을 고르자."

이 규칙이 맞는 문제도 있지만, 항상 안전한 것은 아니다.
진짜로 비교해야 하는 대상은 보통 **부모 번호 한 칸**이 아니라 **시작점부터 이어진 전체 경로**다.

| 비교 방식 | 항상 안전한가 |
|---|---|
| 현재 부모 번호만 비교 | 아닐 수 있음 |
| 시작점부터의 전체 경로 기준 비교 | 문제 요구와 더 직접적 |

즉 문제에서 "사전순"이 무엇을 뜻하는지 먼저 확인해야 한다.
더 작은 반례 두 개로 이 차이만 따로 떼어 보고 싶다면 [0-1 BFS 전체 경로 사전순 비교 브리지](./zero-one-bfs-full-path-lexicographic-bridge.md)로 바로 이어지면 된다.

## tiny counterexample card: 부모 번호만 보면 왜 틀리나

아래 예시는 "즉시 부모 번호가 더 작은데도, 전체 경로 사전순은 오히려 뒤지는" 가장 작은 감각용 반례다.

```text
정점 번호가 작은 쪽이 사전순으로 앞선다고 하자.

1 -> 2 비용 0
1 -> 3 비용 0
2 -> 9 비용 0
3 -> 4 비용 0
9 -> 7 비용 1
4 -> 7 비용 1
```

`7`까지 가는 최단 경로 둘은 둘 다 총비용 `1`이다.

| 후보 경로 | 즉시 부모 | 전체 경로 사전순 |
|---|---|---|
| `1, 2, 9, 7` | `9` | 더 앞섬 |
| `1, 3, 4, 7` | `4` | 더 뒤짐 |

여기서 부모 번호만 보면 `4 < 9`라서 `4 -> 7` 쪽을 고를 수 있다.
하지만 전체 경로를 앞에서부터 비교하면 두 번째 칸에서 `2 < 3`이므로, 실제 사전순 최솟값은 `1, 2, 9, 7`이다.

즉 이 문제류에서 물어보는 것은 보통

- "마지막 직전 정점 번호가 더 작은가?"
- 가 아니라 "시작점부터 이어진 전체 경로가 더 앞서는가?"

이다.

한 줄로 줄이면:

```text
부모 번호 비교는 마지막 한 칸 비교다.
사전순 비교는 경로 전체를 앞에서부터 비교한다.
```

그래서 "동점이면 부모 번호가 작은 쪽"은 쉬운 근사 규칙일 뿐이고,
문제 요구가 전체 경로 사전순이면 반례가 바로 생길 수 있다.

## beginner 기준 안전한 해석

초보자에게는 아래 순서가 가장 안전하다.

1. 먼저 기본형 `0-1 BFS`로 최단 거리 조건을 이해한다.
2. 그다음 "동점이면 무엇을 비교하라"는 추가 요구를 따로 읽는다.
3. 그 요구가 있으면 `newDist == dist[next]`도 별도 분기로 본다.

종이에 적으면 보통 이렇게 정리된다.

```text
if newDist < dist[next]:
    더 짧으니 무조건 갱신
elif newDist == dist[next]:
    tie-break 규칙이 있으면 부모 후보 비교
```

여기서 beginner 버전으로는 한 줄만 더 기억하면 충분하다.

```text
추가 path-order logic가 붙는 자리는
대부분 `elif newDist == dist[next]:` 분기다.
```

핵심은 "`==` 분기 자체가 잘못"이 아니라,
**추가 요구가 있을 때만 `==` 분기를 켠다**는 점이다.

## 구현 전에 꼭 분리할 질문

| 질문 | 먼저 답해야 하는 이유 |
|---|---|
| 사전순 기준이 정점 번호 나열인가, 문자열인가 | 비교 대상이 달라진다 |
| 경로 하나만 출력하면 되나, 최소 경로 자체를 강제하나 | 기본형인지 tie-break형인지 갈린다 |
| 동점 시 부모 한 칸 비교로 충분한가 | 충분하지 않으면 더 큰 비교 구조가 필요하다 |

이 문서의 초점은 "기본형에선 보통 `==`를 무시하지만, 사전순 요구가 있으면 예외가 생긴다"까지다.
고급 구현 디테일은 다음 단계 문서로 넘기는 편이 안전하다.

## 자주 하는 혼동

- `newDist == dist[next]`가 나온다고 항상 부모를 갈아끼우는 것은 아니다.
- 반대로 "0-1 BFS는 무조건 `<`만 본다"도 문제 요구가 바뀌면 틀릴 수 있다.
- 사전순 tie-break는 **거리 알고리즘 자체의 기본 규칙**이 아니라 **문제별 추가 조건**에 가깝다.
- 그래서 먼저 최단 거리 로직과 tie-break 로직을 머릿속에서 분리해야 한다.

## 한 줄 정리

기본형 `0-1 BFS`는 동점 부모를 보통 그대로 두지만, "사전순으로 가장 작은 최단 경로"가 요구되면 `newDist == dist[next]`에서도 더 앞서는 경로인지 비교하는 추가 규칙이 필요하다.

## 다음 연결

- 기본형에서 왜 보통 부모를 안 바꾸는지 먼저 고정하려면 [0-1 BFS parent tie mini note](./zero-one-bfs-parent-tie-mini-note.md)
- 부모 번호 비교와 전체 경로 비교가 언제 갈리는지 더 작은 반례 두 개로 보려면 [0-1 BFS 전체 경로 사전순 비교 브리지](./zero-one-bfs-full-path-lexicographic-bridge.md)
- 같은 거리 후보를 왜 보통 재삽입하지 않는지 보려면 [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- deque와 `dist`를 줄 단위로 손으로 따라가는 감각부터 잡으려면 [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)
- `dist`, `parent`, `deque`의 기본 뼈대를 먼저 코드로 보고 싶다면 [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)

## 한 줄 정리

최단 거리만 맞으면 되는 기본형과 달리, "사전순으로 더 작은 경로"까지 요구되면 `newDist == dist[next]`일 때도 어떤 부모가 더 앞서는지 비교하는 추가 규칙이 필요하다.
