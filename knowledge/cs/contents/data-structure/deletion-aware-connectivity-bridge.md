# Deletion-Aware Connectivity Bridge

> 한 줄 요약: 간선 삭제가 끼는 순간 질문은 `합치기`에서 `지운 뒤에도 우회 경로가 남는가`로 바뀌어서, plain union-find 대신 DSU rollback이나 다른 dynamic-connectivity 기법을 떠올려야 한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: deletion aware connectivity bridge basics, deletion aware connectivity bridge beginner, deletion aware connectivity bridge intro, data structure basics, beginner data structure, 처음 배우는데 deletion aware connectivity bridge, deletion aware connectivity bridge 입문, deletion aware connectivity bridge 기초, what is deletion aware connectivity bridge, how to deletion aware connectivity bridge
> 관련 문서:
> - [자료구조 정리](./README.md)
> - [Union-Find Deep Dive](./union-find-deep-dive.md)
> - [DSU Rollback](../algorithm/dsu-rollback.md)
> - [Bridges and Articulation Points](../algorithm/bridges-and-articulation-points.md)
> - [그래프 알고리즘](../algorithm/graph.md)
>
> retrieval-anchor-keywords: deletion-aware connectivity, edge deletion connectivity, union find deletion limit, union find split limitation, dynamic connectivity bridge, dynamic connectivity intro, offline dynamic connectivity, fully dynamic connectivity, dsu rollback handoff, rollback union find intro, bridge edge deletion, cut edge connectivity, edge removal query, temporal connectivity queries, graph connectivity after deletion, 간선 삭제 연결성, 간선 제거 후 연결 여부, 삭제가 있는 유니온 파인드, 유니온 파인드 split 한계, 동적 연결성 입문, 오프라인 동적 연결성, rollback dsu, 브리지 간선 삭제, cut edge 연결성

## 왜 여기서 막히나

Union-Find를 처음 익히면 `연결 여부 질의 = DSU`로 외우기 쉽다.
하지만 그 공식은 **간선이 추가되기만 할 때**만 잘 맞는다.

삭제가 들어오면 질문은 이렇게 바뀐다.

- `이 간선을 지워도 같은 컴포넌트인가?`
- `방금 지운 간선이 bridge였나, 아니면 우회 경로가 남아 있나?`
- `시간 t 시점의 그래프 상태로 되돌아가면 연결성이 어떻게 되나?`

이 순간부터는 `합치기`보다 **삭제 후 상태 복구 / 현재 그래프 재평가**가 핵심이 된다.

## 왜 plain Union-Find가 바로 막히나

Union-Find는 `누가 같은 집합인가`만 압축해서 기억한다.
반대로 아래 정보는 기억하지 않는다.

- 어떤 간선이 그 연결을 만들었는지
- 지운 간선 말고 대체 경로가 남아 있는지
- 이전 시점 상태로 어떻게 되돌아가야 하는지

예를 들어 아래 두 그래프는 삭제 한 번 뒤의 결과가 다르다.

```text
A. cycle
1 - 2
|   |
4 - 3

(2, 3) 삭제 후에도 2 -> 1 -> 4 -> 3 우회 가능
```

```text
B. chain
1 - 2 - 3 - 4

(2, 3) 삭제 후 1-2 와 3-4로 분리
```

둘 다 삭제 전에는 `1`과 `4`가 연결되어 있었지만,
삭제 후 결과는 `지운 간선이 bridge였는지`에 따라 달라진다.

plain Union-Find는 이미 합쳐진 컴포넌트만 알고 있어서
이 차이를 직접 판정하거나 split을 수행할 수 없다.

## 그래서 어떤 다음 도구를 떠올리나

| 상황 | 먼저 떠올릴 다음 선택지 | 이유 |
|---|---|---|
| 삭제 질의가 적고 그래프도 작다 | BFS/DFS 재탐색 | 현재 그래프에서 우회 경로가 있는지 직접 확인하면 된다 |
| 모든 질의를 미리 안다 | [DSU Rollback](../algorithm/dsu-rollback.md) | 시간 축 구간을 나누고 union을 되돌리며 오프라인 동적 연결성을 다룰 수 있다 |
| 삽입/삭제가 온라인으로 계속 들어온다 | fully dynamic connectivity 구조 | rollback만으로는 현재 시점 변화를 모두 감당하기 어렵다 |
| `이 간선이 끊기면 그래프가 분리되나?`가 핵심이다 | [Bridges and Articulation Points](../algorithm/bridges-and-articulation-points.md) | bridge/cut edge 판정이 직접적인 답이 된다 |

여기서 초보자에게 가장 중요한 감각은 하나다.

> 삭제는 `union의 반대 연산 하나 더 추가`가 아니라,
> `우회 경로 존재 여부`와 `시간 축 상태 관리`를 같이 묻는 문제다.

그래서 학습 경로도 보통 이렇게 넘어간다.

- add-only connectivity: [Union-Find Deep Dive](./union-find-deep-dive.md)
- deletion + offline queries: [DSU Rollback](../algorithm/dsu-rollback.md)
- deletion이 현재 그래프 취약 간선 판단으로 읽힌다: [Bridges and Articulation Points](../algorithm/bridges-and-articulation-points.md)

## 한 줄 정리

간선 삭제가 섞이는 순간 연결성 문제는 `합치기`보다 `삭제 후에도 우회 경로가 남는가`가 핵심이 되므로, plain Union-Find에서 DSU rollback이나 더 강한 dynamic connectivity 기법으로 넘어가야 한다.

## 빠른 확인 질문

- 이 문서의 핵심 용어를 한 문장으로 설명할 수 있는가?
- 실제 미션 코드에서 이 문제가 어디에 나타나는가?

## 한 줄 정리

간선 삭제가 섞이면 연결성 문제는 단순 union보다 삭제 후 우회 경로와 시간 축 상태 관리가 핵심이다.
