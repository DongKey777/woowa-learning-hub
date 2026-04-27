# 0-1 BFS parent tie mini note

> 한 줄 요약: beginner 기본형 `0-1 BFS`에서는 `newDist == dist[next]`인 동점 후보가 나와도 보통 `parent[next]`를 다시 바꾸지 않고, `newDist < dist[next]`일 때만 `parent[next]`를 함께 갱신하면 충분하다.

**난이도: 🟢 Beginner**

관련 문서:

- [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- [0-1 BFS lexicographic tie mini note](./zero-one-bfs-lexicographic-tie-mini-note.md)
- [0-1 BFS 전체 경로 사전순 비교 브리지](./zero-one-bfs-full-path-lexicographic-bridge.md)
- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)
- [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 0-1 bfs parent tie, zero one bfs parent tie, 0-1 bfs equal distance parent, zero one bfs same distance parent update, 0-1 bfs parent[next] tie, 0-1 bfs equal cost parent update, 0-1 bfs predecessor tie, 0-1 bfs same shortest path parent, 0-1 bfs parent overwrite equal distance, 0-1 bfs parent do not update tie, 0-1 bfs parent update only on relax, 0-1 bfs beginner parent tie, 0-1 bfs 동점 부모 갱신, 0-1 bfs 같은 거리 parent, 0-1 bfs parent[next] 언제 바꾸나

## 먼저 감각부터

초보자 기준으로 `parent[next]`는
"현재 최단 거리표를 만든 직전 정점 메모"라고 보면 쉽다.

그래서 거리표가 안 바뀌면, 그 메모도 보통 안 바꾼다.

- `newDist < dist[next]`: 더 짧아졌으니 `dist`와 `parent`를 같이 갱신
- `newDist == dist[next]`: 같은 길이 후보를 하나 더 본 것이므로 beginner 기본형은 보통 그대로 둠

## 왜 보통 안 바꾸나

초보자용 기본 목표는 대개 이것이다.

1. 최단 거리값 구하기
2. 그 최단 거리 하나를 만드는 아무 경로 하나 복원하기

이 목표라면 동점 후보는 "틀린 경로"가 아니라 "다른 정답 후보"다.
이미 하나의 최단 부모가 기록돼 있다면 그것만 써도 충분하다.

| 상황 | `dist[next]` | `parent[next]` |
|---|---|---|
| 더 짧은 후보 발견 | 갱신 | 같이 갱신 |
| 같은 거리 후보 발견 | 유지 | 보통 유지 |

## 작은 예시

```text
S -> A 비용 0
S -> B 비용 0
A -> T 비용 1
B -> T 비용 1
```

`A`를 먼저 통해 `T`를 보면:

- `dist[T] = 1`
- `parent[T] = A`

나중에 `B`를 통해 다시 `T`를 봐도:

- `newDist = 1`
- 이미 `dist[T] = 1`

즉 `B -> T`는 더 짧은 경로가 아니라 **같은 길이의 다른 최단 경로**다.
beginner 기본형에서는 `parent[T]`를 `A` 그대로 둬도 문제가 없다.

## 언제 바꿔야 하나

아래처럼 "어떤 최단 경로를 고를지"가 추가 요구사항이면 동점 규칙을 따로 정해야 한다.

- 사전순으로 가장 작은 경로를 강제
- 모든 최단 부모를 저장
- 최단 경로 개수를 세기

이 경우에는 `newDist == dist[next]`일 때도
"지금 부모보다 이 부모가 더 우선인가?"를 따로 비교할 수 있다.

특히 사전순 tie-break를 beginner 관점에서 따로 떼어 보면 [0-1 BFS lexicographic tie mini note](./zero-one-bfs-lexicographic-tie-mini-note.md)로 바로 이어진다.
그때 "부모 번호 비교"와 "전체 경로 사전순 비교"가 왜 다른지도 같이 막히면 [0-1 BFS 전체 경로 사전순 비교 브리지](./zero-one-bfs-full-path-lexicographic-bridge.md)를 바로 붙여 읽으면 된다.

하지만 beginner primer의 기본형은 아니다.
먼저는 "`dist`가 줄어들 때만 `parent`도 같이 바뀐다"를 고정하는 편이 안전하다.

## 헷갈리기 쉬운 두 질문

| 질문 | 기본 답 |
|---|---|
| 같은 거리 후보면 `next`를 다시 덱에 넣어야 하나? | 보통 아니오 |
| 같은 거리 후보면 `parent[next]`를 다시 바꿔야 하나? | 보통 아니오 |

둘 다 추가 tie-break 요구가 없으면 보통 유지가 기본형이다.

## 한 줄 정리

beginner 기본형 `0-1 BFS`에서는 `newDist == dist[next]`가 나오면 "다른 최단 경로 하나를 더 본 것"에 가깝기 때문에, 보통 `parent[next]`를 다시 바꾸지 않고 기존 최단 부모를 그대로 둔다.

## 다음 연결

- 같은 거리에서 왜 보통 재삽입하지 않는지 먼저 보려면 [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- 사전순으로 더 작은 최단 경로를 고르는 예외 규칙만 따로 보려면 [0-1 BFS lexicographic tie mini note](./zero-one-bfs-lexicographic-tie-mini-note.md)
- `dist`, `parent`, `deque`가 실제 코드에서 어디서 같이 움직이는지 보려면 [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- BFS / 0-1 BFS / Dijkstra의 경로 복원 감각 차이를 한 번에 보려면 [Shortest Path Reconstruction Bridge](./shortest-path-reconstruction-bridge.md)

## 한 줄 정리

beginner 기본형 `0-1 BFS`에서는 `newDist == dist[next]`인 동점 후보가 나와도 보통 `parent[next]`를 다시 바꾸지 않고, `newDist < dist[next]`일 때만 `parent[next]`를 함께 갱신하면 충분하다.
