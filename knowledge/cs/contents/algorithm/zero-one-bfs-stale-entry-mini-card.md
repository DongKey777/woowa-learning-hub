# 0-1 BFS stale-entry mini card

> 한 줄 요약: deque 안에 `A@1`이 남아 있어도 이미 `A@0`으로 `dist[A]`가 줄었다면, 오래된 항목은 "틀린 답"이 아니라 그냥 건너뛰면 되는 옛 예약표다.

**난이도: 🟢 Beginner**

관련 문서:

- [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)
- [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)
- [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)
- [State-space visited vs dist starter card](./zero-one-bfs-state-visited-vs-dist-starter-card.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 0-1 bfs stale entry, zero one bfs stale entry, stale deque entry, outdated deque item, old deque entry harmless, a@1 a@0 zero one bfs, deque duplicate vertex 0-1 bfs, stale pop skip 0-1 bfs, stale distance entry, old reservation ticket analogy, 0-1 bfs duplicate deque safe, 0-1 bfs outdated node card, 0-1 bfs beginner stale entry, 0-1 bfs deque old entry, 0-1 bfs 왜 a@1 남아도 되나

## 먼저 그림부터

초보자 기준으로는 deque를 "처리 예약표"라고 보면 쉽다.

- `A@1`: "A를 비용 1 후보로 나중에 한 번 보자"
- `A@0`: "A를 비용 0 후보로 더 먼저 보자"

중요한 것은 deque 안의 메모보다 **현재 `dist[A]`** 다.

즉 `A@1`이 먼저 예약되어 있었더라도, 나중에 `A@0`이 나오면서 `dist[A] = 0`으로 줄면 최신 진실은 이미 바뀐 것이다.

## 딱 이 장면만 보기

```text
1) S -> A 비용 1
   dist[A] = 1
   deque = [A@1]

2) S -> B 비용 0, B -> A 비용 0
   dist[A] = 0으로 갱신
   deque = [A@0, A@1]
```

여기서 많은 초보자가 묻는다.

> "deque 안에 아직 `A@1`이 남아 있는데, 이거 잘못된 것 아닌가?"

답은 `아니다`다.

- `A@0`은 최신 후보
- `A@1`은 예전 후보
- 최종 판단은 `dist[A]`가 들고 있다

## 왜 harmless한가

`A@1`을 나중에 꺼내더라도, 이미 `dist[A] = 0`이다.

그래서 해석은 이렇게 하면 된다.

| 꺼낸 항목 | 현재 `dist[A]` | 의미 |
|---|---:|---|
| `A@0` | `0` | 최신 예약이 맞다. 이 기준으로 이웃을 본다 |
| `A@1` | `0` | 예전 예약이다. 이미 더 싼 값이 있으니 새 정보가 아니다 |

핵심은:

> 오래된 항목이 deque에 남아 있어도, `dist`가 더 작아졌다면 그 항목은 답을 망치지 못한다.

왜냐하면 relax 조건이 `newDist < dist[next]`이기 때문이다.
예전 항목에서 출발하면 보통 더 좋은 `newDist`를 만들지 못한다.

## 비유로 기억하기

`A@1`은 오래된 택배 송장처럼 보면 된다.

- 처음에는 배송 예정 시간이 `1`이었다
- 더 빠른 특송이 잡혀서 실제 예정 시간이 `0`으로 바뀌었다
- 예전 송장이 시스템에 남아 있어도 최신 예정 시간은 바뀌지 않는다

deque 안의 예전 항목은 남을 수 있지만, 거리표는 최신 값만 유지한다.

## 코드에서 어디를 보면 되나

보통은 pop 직후 아래 한 줄로 감각을 정리한다.

```text
꺼낸 값이 예전 후보여도 relax는 항상 현재 dist 기준으로 본다
```

실제로 많은 구현은 deque에 정점만 넣고, pop한 뒤 이 한 줄로 stale 감각을 처리한다.

```python
cur = dq.popleft()

for nxt, cost in graph[cur]:
    new_dist = dist[cur] + cost
    if new_dist < dist[nxt]:
        ...
```

즉 "deque에 적힌 옛 거리"를 믿는 게 아니라, **배열에 저장된 최신 `dist[cur]`** 로 계속 계산한다.

## 자주 하는 오해

- deque에 같은 정점이 두 번 들어가면 바로 버그라고 생각하기 쉽다.
- 하지만 `0-1 BFS`에서는 더 싼 재도착이 가능하므로 예전 후보가 남을 수 있다.
- 중요한 것은 "중복이 있나?"보다 "`dist`가 최신값을 들고 있나?"다.
- 같은 거리 후보를 또 봤을 때 왜 보통 재삽입하지 않는지는 [0-1 BFS equal-distance reinsert mini note](./zero-one-bfs-equal-distance-reinsert-mini-note.md)에서 따로 분리해 보면 덜 헷갈린다.

## 한 줄 정리

`A@1`이 남아 있어도 `A@0`이 이미 `dist[A]`를 갱신했다면, 오래된 deque 항목은 그냥 늦게 도착한 옛 예약일 뿐이라서 harmless하다.

## 다음 연결

- 같은 예시를 step 표로 다시 보고 싶으면 [0-1 BFS 손계산 워크시트](./zero-one-bfs-hand-calculation-worksheet.md)
- 왜 첫 방문 고정이 아니라 `dist` 비교가 핵심인지 보려면 [0-1 BFS dist vs visited 미니 반례 카드](./zero-one-bfs-dist-vs-visited-counterexamples.md)
- 실제 코드에서 `dist`, `deque`, `parent`가 어디서 같이 움직이는지 보려면 [0-1 BFS 구현 실수 체크 템플릿](./zero-one-bfs-implementation-mistake-check-template.md)

## 한 줄 정리

deque 안에 `A@1`이 남아 있어도 이미 `A@0`으로 `dist[A]`가 줄었다면, 오래된 항목은 "틀린 답"이 아니라 그냥 건너뛰면 되는 옛 예약표다.
