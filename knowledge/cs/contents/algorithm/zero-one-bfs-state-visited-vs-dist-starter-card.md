---
schema_version: 3
title: State-space visited vs dist starter card
concept_id: algorithm/zero-one-bfs-state-visited-vs-dist-starter-card
canonical: false
category: algorithm
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- visited-vs-dist-choice
- zero-cost-revisit
aliases:
- state space visited vs dist
- visited r c state vs dist r c state
- 3d visited vs 3d dist
- zero one bfs state dist
- stateful shortest path visited dist
- 0-1 bfs visited dist state card
- 0-1 bfs beginner visited or dist
- grid state visited enough
- grid state dist safer
- visited r c state enough
- dist r c state safer
- key door bfs visited
- wall break bfs dist
- direction state 0-1 bfs dist
- zero one bfs state visited vs dist starter card basics
symptoms:
- visited만 썼는데 반례가 나와서 왜 틀렸는지 모르겠어
- 같은 상태에 더 싼 비용으로 다시 와도 되는지 감이 안 와
- 0 비용 이동이 섞이면 dist 배열로 바꿔야 하는지 헷갈려
intents:
- comparison
- design
prerequisites:
- algorithm/zero-one-bfs-grid-conversion-primer
- algorithm/zero-one-bfs-state-space-bridge
next_docs:
- algorithm/zero-one-bfs-dist-vs-visited-counterexamples
- algorithm/zero-one-bfs-implementation-mistake-check-template
- algorithm/shortest-path-reconstruction-bridge
linked_paths:
- contents/algorithm/zero-one-bfs-state-space-bridge.md
- contents/algorithm/zero-one-bfs-grid-conversion-primer.md
- contents/algorithm/zero-one-bfs-dist-vs-visited-counterexamples.md
- contents/algorithm/zero-one-bfs-implementation-mistake-check-template.md
- contents/algorithm/zero-one-bfs-hand-calculation-worksheet.md
- contents/algorithm/shortest-path-reconstruction-bridge.md
- contents/algorithm/dfs-bfs-intro.md
confusable_with:
- algorithm/zero-one-bfs-dist-vs-visited-counterexamples
- algorithm/zero-one-bfs-state-space-bridge
- algorithm/zero-one-bfs-grid-conversion-primer
forbidden_neighbors:
- contents/algorithm/dfs-bfs-intro.md
- contents/algorithm/zero-one-bfs-grid-conversion-primer.md
expected_queries:
- 0 1 가중치가 섞인 상태 공간에서 visited로 막아도 되는지 궁금해
- 같은 상태를 더 싸게 다시 방문할 수 있으면 배열을 어떻게 둬야 해
- 3차원 상태 배열을 만들었는데 visited로 끝낼지 dist까지 둬야 할지 판단이 안 서
- key door 문제는 visited면 되고 teleport 문제는 dist가 필요한 이유를 설명해줘
- 0-1 BFS에서 처음 방문했다고 끝내면 안 되는 경우를 알고 싶어
- state shortest path에서 비용 비교 배열을 언제 도입해야 해
- visited와 dist 중 무엇을 고를지 빠르게 판단하는 체크포인트가 필요해
contextual_chunk_prefix: |
  이 문서는 상태 공간 최단 경로에서 visited로 막아도 되는 경우와 dist로 더 싼 재도착을 열어야 하는 경우를 골라주는 chooser다. 처음 방문이면 끝인지 판단, 같은 상태 재도착 허용, 비용 비교 배열이 왜 필요한지, 0 비용 이동 섞일 때 처리, 방문 체크와 거리표 선택 같은 자연어 paraphrase가 본 문서의 결정 기준에 매핑된다.
---
# State-space visited vs dist starter card

> 한 줄 요약: 상태 공간이 보여도 간선 비용이 모두 같으면 `visited[r][c][state]`로 충분한 경우가 많고, `0/1` 비용이 섞이면 "처음 방문"보다 "더 싼 재도착"을 허용하는 `dist[r][c][state]`가 더 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [0-1 BFS State-Space Bridge](./zero-one-bfs-state-space-bridge.md)
- [0-1 BFS grid-conversion primer](./zero-one-bfs-grid-conversion-primer.md)
- [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [DFS와 BFS 입문](./dfs-bfs-intro.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: state space visited vs dist, visited r c state vs dist r c state, 3d visited vs 3d dist, zero one bfs state dist, stateful shortest path visited dist, 0-1 bfs visited dist state card, 0-1 bfs beginner visited or dist, grid state visited enough, grid state dist safer, visited r c state enough, dist r c state safer, key door bfs visited, wall break bfs dist, direction state 0-1 bfs dist, zero one bfs state visited vs dist starter card basics

## 먼저 감각부터

초보자 기준으로는 아래 한 줄로 먼저 자르면 된다.

- 모든 이동 비용이 같으면: `visited[r][c][state]` 쪽이 자연스럽다
- `0` 비용과 `1` 비용이 섞이면: `dist[r][c][state]` 쪽이 더 안전하다

이유는 간단하다.

- 일반 BFS는 "처음 도착한 순간"이 곧 최단 거리인 경우가 많다
- `0-1 BFS`는 같은 상태에 **더 싼 비용으로 다시 도착**할 수 있다

즉 상태가 있다는 사실과 `dist`가 필요하다는 사실은 같은 말이 아니다.

## 둘은 무엇이 다른가

| 배열 | 주로 언제 쓰나 | 핵심 질문 |
|---|---|---|
| `visited[r][c][state]` | BFS처럼 간선 비용이 모두 같을 때 | "이 상태를 이미 처리했나?" |
| `dist[r][c][state]` | `0-1 BFS`나 가중치 최단 경로일 때 | "이 상태를 더 싸게 갈 수 있나?" |

짧게 외우면:

> `visited`는 중복 차단용, `dist`는 비용 비교용이다.

## `visited[r][c][state]`만으로 충분한 경우

아래 두 조건이 같이 맞으면 보통 충분하다.

1. 정점이 `(r, c, state)`로 나뉜다
2. 모든 간선 비용이 사실상 같다

예를 들어:

> 한 칸 이동마다 1초, 벽은 최대 1번만 부술 수 있다.

이 문제는 같은 칸이어도 `벽을 이미 부쉈는가`가 다르면 상태를 나눠야 한다.
하지만 모든 이동 비용이 `1`이라면 보통은 레벨 BFS 감각이 그대로 유지된다.

| 상태 | 의미 |
|---|---|
| `(r, c, 0)` | 아직 벽을 안 부숨 |
| `(r, c, 1)` | 이미 벽을 부숨 |

이런 경우는 `visited[r][c][broken]`로도 많이 푼다.

핵심은 "같은 상태를 다시 만나도 더 싼 비용이 나올 일이 거의 없다"는 점이다.

## `dist[r][c][state]`가 더 안전한 경우

아래 둘 중 하나라도 보이면 `dist`부터 의심하는 편이 안전하다.

1. `0` 비용 이동과 `1` 비용 이동이 섞인다
2. 같은 `(r, c, state)`에 더 낮은 비용으로 다시 들어올 수 있다

예를 들어:

> `(r, c, dir)` 상태에서 직진은 비용 `0`, 회전은 비용 `1`

이 문제는 상태도 있고 비용도 섞여 있다.

| 상태 | 다음 이동 |
|---|---|
| `(r, c, east)` | 동쪽 직진 `0`, 다른 방향 전환 `1` |
| `(r, c, north)` | 북쪽 직진 `0`, 다른 방향 전환 `1` |

여기서는 `visited[r][c][dir] = true`로 첫 방문을 고정하면,
나중에 같은 방향 상태로 더 싸게 들어오는 경로를 막을 수 있다.

그래서 보통 이렇게 본다.

```text
if (newDist < dist[nr][nc][nextState]) {
    dist[nr][nc][nextState] = newDist;
}
```

## 가장 쉬운 비교

| 문제 느낌 | 추천 기본값 | 이유 |
|---|---|---|
| 열쇠/벽횟수 같은 상태가 있지만 이동 비용은 전부 `1` | `visited[r][c][state]` | BFS 레벨 순서가 곧 최단 거리다 |
| 방향 유지 `0`, 방향 전환 `1` | `dist[r][c][state]` | 같은 상태에 더 싼 재도착이 가능하다 |
| 포털 이동 `0`, 걷기 `1`, 그리고 열쇠 상태도 있음 | `dist[r][c][state]` | 상태 공간 + `0/1` 비용이 함께 있다 |

## 자주 하는 착각

- 상태가 3차원이라고 해서 무조건 `dist`가 필요한 것은 아니다.
- 반대로 상태가 있으니 `visited`만 쓰면 된다고 보면 `0-1 BFS`에서 자주 틀린다.
- 판단 기준은 배열 차원이 아니라 "같은 상태에 비용이 더 줄어들 수 있나"다.

## 초보자용 판별 질문 3개

1. 정점이 `(r, c)`인가, `(r, c, state)`인가?
2. 모든 이동 비용이 같은가?
3. 같은 상태에 더 싸게 다시 도착할 수 있는가?

판별 결과를 이렇게 적으면 된다.

```text
정점 = (r, c, state)
간선 비용 = 전부 1 / 0과 1 섞임
배열 = visited / dist
```

## 한 줄 정리

상태 공간 문제에서 `visited[r][c][state]`는 "같은 비용 세계"에 잘 맞고,
`0-1 BFS`처럼 `0/1` 비용이 섞이는 순간에는 `dist[r][c][state]`가 더 안전한 출발점이다.

## 다음 연결

- 상태를 왜 `(r, c, state)`로 키워야 하는지 먼저 잡으려면 [0-1 BFS State-Space Bridge](./zero-one-bfs-state-space-bridge.md)
- `0/1` 비용으로 번역하는 감각이 먼저 필요하면 [0-1 BFS grid-conversion primer](./zero-one-bfs-grid-conversion-primer.md)
- 첫 방문 고정이 왜 깨지는지 짧은 반례부터 보려면 [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)

## 한 줄 정리

상태 공간이 보여도 간선 비용이 모두 같으면 `visited[r][c][state]`로 충분한 경우가 많고, `0/1` 비용이 섞이면 "처음 방문"보다 "더 싼 재도착"을 허용하는 `dist[r][c][state]`가 더 안전하다.
