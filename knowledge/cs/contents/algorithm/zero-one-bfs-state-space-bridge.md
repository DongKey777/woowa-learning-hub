# 0-1 BFS State-Space Bridge

> 한 줄 요약: 격자 최단 경로에서 같은 칸이라도 "열쇠 보유", "벽을 몇 번 부쉈는가", "현재 바라보는 방향"이 다르면 서로 다른 정점으로 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [0-1 BFS grid-conversion primer](./zero-one-bfs-grid-conversion-primer.md)
- [State-space visited vs dist starter card](./zero-one-bfs-state-visited-vs-dist-starter-card.md)
- [DFS와 BFS 입문](./dfs-bfs-intro.md)
- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 0-1 bfs state space bridge, zero one bfs state modeling, grid state space bfs, r c state modeling, row col state shortest path, key door bfs state, wall break count bfs state, facing direction bfs state, stateful grid shortest path, 3d visited bfs, 3d dist bfs, 0-1 bfs beginner state, 격자 상태 공간, r c state 모델링, zero one bfs state space bridge basics

## 먼저 잡을 생각

초보자가 가장 많이 하는 실수는 `(r, c)`만 방문 처리하는 것이다.

하지만 아래 질문에 `예`가 하나라도 나오면, 칸만으로는 부족할 수 있다.

- 같은 칸이어도 **가지고 있는 것**이 다르면 이후 이동 가능성이 달라지나?
- 같은 칸이어도 **이미 쓴 기회 수**가 다르면 이후 선택지가 달라지나?
- 같은 칸이어도 **현재 방향**이 다르면 다음 이동 비용이 달라지나?

답이 `예`라면 정점은 보통 `(r, c, state)`가 된다.

즉 핵심은 "지금 어디 있나?"만이 아니라,
"지금 어떤 조건을 들고 그 칸에 있나?"까지 같이 저장하는 것이다.

## 왜 같은 칸인데 다른 정점인가

`(2, 3)` 칸에 도착했다고 해도 다음처럼 상황이 다를 수 있다.

| 도착 상태 | 다음에 할 수 있는 일 |
|---|---|
| 열쇠 없음 | 문 통과 불가 |
| 빨간 열쇠 보유 | 빨간 문 통과 가능 |
| 벽 1번 이미 부숨 | 남은 벽 부수기 기회 0 |
| 동쪽을 바라봄 | 직진 비용 0, 회전 비용 1 |

좌표는 같아도 **미래가 다르면 같은 정점이 아니다.**

초보자 기준으로는 이렇게 기억하면 된다.

> "그 칸에 다시 와도, 들고 있는 상태가 다르면 다음 간선 집합이 달라진다."

간선 집합이 달라지면 그래프의 정점도 분리해야 한다.

## 칸만 쓰는 모델 vs 상태를 붙이는 모델

| 질문 | 칸만으로 충분 | `(r, c, state)`가 필요 |
|---|---|---|
| 이동 가능 여부가 좌표만으로 결정되나 | O | X |
| 다음 비용이 좌표만으로 결정되나 | O | X |
| 같은 칸 재방문 의미가 항상 같나 | O | X |
| `visited[r][c]` 한 장으로 충분한가 | O | X |

간단히 말해:

- "이 칸이면 언제 와도 똑같다"면 `(r, c)`
- "이 칸이어도 조건에 따라 다르다"면 `(r, c, state)`

## 예제 1: 열쇠와 문

문제 말:

> `a` 열쇠를 주우면 `A` 문을 통과할 수 있다.

이때 `(r, c)`만 방문 처리하면 왜 틀리기 쉬울까?

같은 문 앞 칸에 와도:

- 아직 `a`를 못 주운 상태
- 이미 `a`를 주운 상태

이 둘은 완전히 다르기 때문이다.

| 상태 표현 | 의미 |
|---|---|
| `(r, c, keyMask)` | 현재 칸과 보유 열쇠 집합 |

예를 들어 `keyMask = 0b001`이면 빨간 열쇠만 가진 상태처럼 볼 수 있다.

초보자용 핵심만 남기면:

- 좌표만 같아도 열쇠 집합이 다르면 다른 정점
- 그래서 `visited[r][c][keyMask]` 또는 `dist[r][c][keyMask]`가 필요

## 예제 2: 벽을 몇 번 부쉈는가

문제 말:

> 벽을 최대 `K`번까지 부술 수 있다.

이 문제도 `(r, c)`만으로는 부족하다.

같은 칸에 도착해도:

- 아직 벽을 0번 부순 상태
- 이미 벽을 2번 부순 상태

는 남은 선택지가 다르다.

| 상태 표현 | 의미 |
|---|---|
| `(r, c, broken)` | 현재 칸과 지금까지 부순 벽 수 |

이때 초보자가 자주 놓치는 감각은 이것이다.

> 더 늦게 도착했더라도 `broken`이 더 작으면 더 좋은 상태일 수 있다.

즉 `(r, c)`만 보고 "이미 방문했으니 끝"이라고 하면,
남은 기회가 더 많은 경로를 잘라 버릴 수 있다.

## 예제 3: 현재 바라보는 방향

문제 말:

> 직진은 비용 `0`, 방향 전환은 비용 `1`

이 경우 같은 칸이어도 방향이 다르면 다음 비용이 달라진다.

| 상태 표현 | 의미 |
|---|---|
| `(r, c, dir)` | 현재 칸과 바라보는 방향 |

예를 들어 `(2, 4, east)`와 `(2, 4, north)`는 좌표는 같지만:

- 동쪽으로 한 칸 더 가는 비용
- 북쪽으로 꺾는 비용

이 서로 다를 수 있다.

그래서 이런 문제는 보통 `dist[r][c][dir]`로 둔다.

## 0-1 BFS와 상태 모델링은 서로 다른 질문이다

여기서 헷갈리기 쉬운 포인트를 분리해야 한다.

1. 정점을 무엇으로 잡을까?
2. 간선 비용이 `0`/`1`인가?

첫 번째 질문은 **상태 모델링**이고,
두 번째 질문은 **알고리즘 선택**이다.

예를 들어:

| 문제 해석 | 정점 | 간선 비용 | 선택 후보 |
|---|---|---|---|
| 열쇠/문 + 모든 이동 비용 1 | `(r, c, keyMask)` | 전부 `1` | BFS |
| 방향 유지 0, 회전 1 | `(r, c, dir)` | `0` 또는 `1` | 0-1 BFS |
| 벽 부수기 비용 2, 걷기 비용 1 | `(r, c, broken)` | `1`, `2` | Dijkstra |

즉 상태를 붙였다고 자동으로 `0-1 BFS`가 되는 것도 아니고,
`0-1 BFS`라고 해서 정점이 항상 `(r, c)`인 것도 아니다.

여기서 한 번 더 분리하면:

- 상태를 몇 차원으로 잡을지는 `visited[r][c][state]` 관점의 질문
- 같은 상태를 더 싸게 다시 갈 수 있는지는 `dist[r][c][state]` 관점의 질문

이 둘을 한 장으로 비교해 보고 싶으면 [State-space visited vs dist starter card](./zero-one-bfs-state-visited-vs-dist-starter-card.md)로 이어가면 된다.

## 초보자용 판별 루틴

문제를 읽고 아래 순서대로 적으면 실수가 많이 줄어든다.

1. 좌표 말고도 미래를 바꾸는 정보가 있나?
2. 그 정보는 `state`로 붙여야 하나?
3. 그래서 정점이 `(r, c)`인가, `(r, c, state)`인가?
4. 그다음 각 이동 비용이 `0`/`1`인가?

종이에 이렇게 적으면 충분하다.

```text
정점 = (r, c, ?)
state = ?
0 비용 이동 = ?
1 비용 이동 = ?
```

`state` 칸이 비어 있는데 문제에 열쇠, 방향, 사용 횟수 제한이 나오면
모델링을 다시 봐야 한다.

## 자주 하는 오해

- "격자니까 `visited[r][c]`면 되겠지"라고 바로 가면 위험하다.
- "같은 칸이면 같은 정점"은 상태가 없을 때만 맞다.
- 열쇠 문제에서 열쇠를 주운 뒤 같은 칸을 다시 방문하는 것은 **중복**이 아니라 **새 상태**일 수 있다.
- 벽 부수기 문제에서 더 빠른 경로보다 "남은 벽 부수기 기회가 많은 경로"가 이후에는 더 유리할 수 있다.
- 방향 비용 문제는 좌표 BFS가 아니라, 사실상 "방향이 붙은 그래프"를 푸는 것에 가깝다.

## 한 줄 정리

격자 문제에서 "좌표는 같지만 미래가 달라지는가?"가 보이면,
정점을 칸 하나가 아니라 `(r, c, state)`로 키워서 봐야 한다.

## 다음 연결

- 격자 문제를 먼저 `0/1 비용` 관점으로 번역하는 감각은 [0-1 BFS grid-conversion primer](./zero-one-bfs-grid-conversion-primer.md)
- `dist`와 `deque` 갱신 위치까지 이어서 보려면 [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- `visited` 고정 습관이 왜 위험한지 짧은 반례로 보려면 [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)

## 한 줄 정리

격자 최단 경로에서 같은 칸이라도 "열쇠 보유", "벽을 몇 번 부쉈는가", "현재 바라보는 방향"이 다르면 서로 다른 정점으로 봐야 한다.
