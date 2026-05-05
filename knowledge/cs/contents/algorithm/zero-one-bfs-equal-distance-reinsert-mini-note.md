---
schema_version: 3
title: 0-1 BFS equal-distance reinsert mini note
concept_id: algorithm/zero-one-bfs-equal-distance-reinsert-mini-note
canonical: false
category: algorithm
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 75
mission_ids: []
review_feedback_tags:
- equal-distance-reinsert
- strict-less-than-relax
aliases:
- 0-1 bfs equal distance
- zero one bfs equal distance
- 0-1 bfs equal-distance reinsert
- zero one bfs reinsert same distance
- 0-1 bfs newdist equals dist
- 0-1 bfs newdist == dist
- 0-1 bfs strict less than
- 0-1 bfs duplicate equal cost
- 0-1 bfs tie update
- 0-1 bfs same distance no requeue
- 0-1 bfs same distance no reinsert
- deque shortest path equal distance
- binary weight shortest path equal distance
- 0-1 bfs beginner equality case
- zero one bfs equal distance reinsert mini note basics
symptoms:
- 같은 거리 후보가 또 나오면 덱에 다시 넣어야 하는지 헷갈려
- newDist == dist[next]인 경우를 왜 그냥 넘겨도 되는지 감이 안 와
- 0-1 BFS에서 중복 후보를 다 넣으면 뭐가 문제인지 확인하고 싶어
intents:
- troubleshooting
- drill
prerequisites:
- algorithm/zero-one-bfs-grid-conversion-primer
- algorithm/zero-one-bfs-dist-vs-visited-counterexamples
next_docs:
- algorithm/zero-one-bfs-parent-tie-mini-note
- algorithm/zero-one-bfs-lexicographic-tie-mini-note
- algorithm/zero-one-bfs-implementation-mistake-check-template
linked_paths:
- contents/algorithm/zero-one-bfs-dist-vs-visited-counterexamples.md
- contents/algorithm/zero-one-bfs-parent-tie-mini-note.md
- contents/algorithm/zero-one-bfs-lexicographic-tie-mini-note.md
- contents/algorithm/zero-one-bfs-stale-entry-mini-card.md
- contents/algorithm/zero-one-bfs-hand-calculation-worksheet.md
- contents/algorithm/zero-one-bfs-implementation-mistake-check-template.md
confusable_with:
- algorithm/zero-one-bfs-parent-tie-mini-note
- algorithm/zero-one-bfs-stale-entry-mini-card
forbidden_neighbors:
- contents/algorithm/zero-one-bfs-full-path-lexicographic-bridge.md
expected_queries:
- 0-1 BFS에서 같은 비용으로 다시 도착했을 때 왜 보통 다시 안 넣는지 설명해줘
- newDist와 기존 거리값이 같으면 relax를 생략해도 되는 이유를 짧게 알고 싶어
- 최단 거리값은 안 변하는데 덱에 중복으로 넣는 코드를 줄여도 되는지 확인하고 싶어
- 동일 거리 후보를 또 봤을 때 beginner 구현이 어떤 기준으로 멈추는지 궁금해
- 0비용 간선이 있어도 같은 거리 재삽입을 기본형에서 생략하는 근거가 뭐야
contextual_chunk_prefix: |
  이 문서는 0-1 BFS beginner 구현에서 같은 거리 후보를 다시 덱에 넣어야
  하는지 헷갈릴 때, newDist == dist[next]는 보통 새 최단 정보가 아니라는
  drill이다. 같은 비용 재삽입, strict less-than relax, 중복 후보를
  그냥 넘겨도 되는 이유 같은 자연어 질문이 이 문서의 판단 규칙으로
  매핑된다.
---
# 0-1 BFS equal-distance reinsert mini note

> 한 줄 요약: 초보자용 `0-1 BFS`에서 `newDist == dist[next]`라면 보통 "더 좋아진 것"이 아니므로 덱에 다시 넣지 않고 `newDist < dist[next]`만 잡아도 충분하다.

**난이도: 🟢 Beginner**

관련 문서:

- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [0-1 BFS parent tie mini note](./zero-one-bfs-parent-tie-mini-note.md)
- [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)
- [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 0-1 bfs equal distance, zero one bfs equal distance, 0-1 bfs equal-distance reinsert, zero one bfs reinsert same distance, 0-1 bfs newdist equals dist, 0-1 bfs newdist == dist, 0-1 bfs strict less than, 0-1 bfs duplicate equal cost, 0-1 bfs tie update, 0-1 bfs same distance no requeue, 0-1 bfs same distance no reinsert, deque shortest path equal distance, binary weight shortest path equal distance, 0-1 bfs beginner equality case, zero one bfs equal distance reinsert mini note basics

## 먼저 감각부터

초보자 기준으로는 `dist[next]`를 "최저가 표"라고 보면 쉽다.

- `newDist < dist[next]`: 더 싼 표를 찾았다
- `newDist == dist[next]`: 같은 가격 표를 하나 더 봤다

같은 가격 표를 또 봤다면, **최저가 자체는 안 바뀐다.**
그래서 보통은 덱에 다시 넣지 않아도 된다.

## 왜 `<`만으로 충분한가

초보 구현의 목표가 보통 이것이기 때문이다.

1. 시작점에서 각 정점까지의 **최단 거리값** 구하기
2. 그 최단 거리 하나를 만드는 **아무 경로 하나** 구하기

이 목적이라면 `newDist == dist[next]`는 개선이 아니다.

| 비교 결과 | 의미 | 보통 동작 |
|---|---|---|
| `newDist < dist[next]` | 더 좋은 후보 발견 | `dist` 갱신 후 덱에 삽입 |
| `newDist == dist[next]` | 같은 품질 후보를 하나 더 봄 | 보통 아무것도 하지 않음 |

즉 초보자용 기본형은 아래 한 줄로 충분하다.

```python
if new_dist < dist[nxt]:
    dist[nxt] = new_dist
```

경로 복원까지 한다면 `parent[nxt]`도 같은 규칙으로 보면 된다.

- `new_dist < dist[nxt]`일 때만 `parent[nxt]`를 같이 갱신
- `new_dist == dist[nxt]`면 beginner 기본형은 보통 그대로 유지

이 parent 쪽 동점 감각만 따로 짧게 떼어 보면 [0-1 BFS parent tie mini note](./zero-one-bfs-parent-tie-mini-note.md)가 바로 이어진다.

## 작은 예시

```text
S -> A 비용 0
S -> B 비용 0
A -> T 비용 1
B -> T 비용 1
```

여기서 `T`로 가는 비용은 두 경로 모두 `1`이다.

- `S -> A -> T`를 먼저 보면 `dist[T] = 1`
- 나중에 `S -> B -> T`를 봐도 `newDist = 1`
- 이미 `dist[T] = 1`이므로 최단 거리값은 그대로다

따라서 `T`를 다시 덱에 넣어도 거리표는 달라지지 않는다.
초보 구현에서는 이 재삽입이 새 정보를 만들지 못한다.

## 자주 하는 혼동

많이 헷갈리는 장면은 이것이다.

- `A@1`처럼 오래된 더 나쁜 후보가 남아 있는 경우
- 같은 `1`을 또 만드는 동점 후보가 들어오는 경우

둘은 다르다.

| 상황 | 핵심 판단 |
|---|---|
| 예전 후보가 남아 있음 | [stale-entry](./zero-one-bfs-stale-entry-mini-card.md)처럼 나중에 꺼내도 `dist` 기준으로 보면 된다 |
| 같은 최단 거리 후보를 하나 더 찾음 | 거리값이 안 줄었으니 초보 기본형은 재삽입 없이 지나가도 된다 |

즉 "`같은 정점이 덱에 두 번 들어갈 수 있나?`"와
"`동일 거리일 때도 꼭 다시 넣어야 하나?`"는 다른 질문이다.

## 언제 예외를 생각하나

아래 목표가 붙으면 동점 처리를 별도로 설계할 수 있다.

- 최단 경로 개수 세기
- 모든 최단 부모 저장하기
- 사전순 같은 추가 tie-break 규칙 강제하기

하지만 beginner primer에서는 중심이 아니다.
먼저는 **`<`로만 relax하는 기본형**을 안정적으로 익히는 편이 좋다.

## 한 줄 정리

초보자용 `0-1 BFS`에서 `newDist == dist[next]`는 "더 짧아졌다"가 아니라 "같은 거리 후보를 하나 더 봤다"에 가깝기 때문에, 보통은 덱에 다시 넣지 않고 넘어가도 된다.

## 다음 연결

- 오래된 더 나쁜 후보가 왜 남아 있어도 되는지 보려면 [0-1 BFS stale-entry mini card](./zero-one-bfs-stale-entry-mini-card.md)
- 초보 구현에서 `dist`, `deque`, `parent` 순서를 같이 보려면 [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- `visited` 대신 `dist` 비교가 필요한 이유를 반례로 먼저 보려면 [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- 같은 거리 후보에서 `parent[next]`를 왜 보통 안 바꾸는지 보려면 [0-1 BFS parent tie mini note](./zero-one-bfs-parent-tie-mini-note.md)

## 한 줄 정리

초보자용 `0-1 BFS`에서 `newDist == dist[next]`라면 보통 "더 좋아진 것"이 아니므로 덱에 다시 넣지 않고 `newDist < dist[next]`만 잡아도 충분하다.
