# Greedy Algorithm

> 한 줄 요약: greedy는 매 단계에서 가장 좋아 보이는 선택을 하되, 그 국소 선택이 전체 최적해로 이어진다는 근거가 있을 때만 안전한 설계 기법이다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **generic greedy landing page + proof vocabulary primer** 역할을 한다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [탐욕 알고리즘 (기본 primer)](./basic.md#탐욕-알고리즘-greedy)
> - [구간 / Interval Greedy 패턴](./interval-greedy-patterns.md)
> - [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)
> - [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)
> - [Sweep Line Overlap Counting](./sweep-line-overlap-counting.md)
> - [정렬 알고리즘](./sort.md)
> - [동적 계획법](./basic.md#동적-계획법-dynamic-programming)
>
> retrieval-anchor-keywords: greedy algorithm, greedy algorithm overview, greedy overview, greedy primer, greedy proof, greedy criteria, greedy basic primer, when greedy works, when greedy fails, greedy counterexample, greedy choice property, optimal substructure, local optimum, global optimum, exchange argument, stays ahead proof, cut property, activity selection, interval greedy, interval scheduling, earliest finish time, non-overlapping intervals, erase overlap intervals, meeting rooms i, minimum arrows, coin change greedy, canonical coin system, fractional knapsack, fractional knapsack vs 0-1 knapsack, minimum spanning tree, prim, kruskal, dijkstra, huffman coding, tsp counterexample, 0-1 knapsack counterexample, 탐욕 알고리즘, 그리디 알고리즘, 탐욕 알고리즘 개요, 그리디 알고리즘 개요, 탐욕 개요, 그리디 개요, 탐욕 증명, 탐욕 선택 속성, 최적 부분 구조, 국소 최적, 전역 최적, 교환 논증, 활동 선택 문제, 구간 스케줄링, 구간 그리디, 회의실 1, 거스름돈 문제, 정렬 후 선택 기준, 분할 가능한 배낭, 최소 신장 트리, 프림, 크루스칼, 다익스트라, 허프만 코딩, 외판원 순회 문제, 0-1 배낭 문제

## 이 문서 다음에 보면 좋은 문서

- 회의 배정, 구간 겹침 제거처럼 정렬 기준이 핵심인 greedy 문제는 [구간 / Interval Greedy 패턴](./interval-greedy-patterns.md)으로 바로 이어진다.
- greedy가 그래프 문제에서 어떻게 쓰이는지 보려면 [Minimum Spanning Tree: Prim vs Kruskal](./minimum-spanning-tree-prim-vs-kruskal.md)과 [Dijkstra, Bellman-Ford, Floyd-Warshall](./dijkstra-bellman-ford-floyd-warshall.md)을 같이 보면 좋다.
- `meeting rooms II`, `최소 몇 개 방 필요`, `최대 동시성`처럼 겹침 수 자체를 세는 문제는 [Sweep Line Overlap Counting](./sweep-line-overlap-counting.md)으로 바로 갈라진다.
- greedy가 왜 실패하는지, 언제 DP로 넘어가야 하는지 감을 잡으려면 [동적 계획법](./basic.md#동적-계획법-dynamic-programming)을 함께 보는 편이 정확하다.

---

## Greedy Entry Router

| 질문 phrasing | 먼저 볼 선택 | 왜 그렇게 가는가 |
|---|---|---|
| `greedy choice property`, `exchange argument`, `그리디가 왜 맞나`, `언제 greedy를 써도 되나` | 이 문서 | generic greedy 판단 기준과 증명 어휘를 먼저 잡아야 한다 |
| `activity selection`, `non-overlapping intervals`, `erase overlap intervals`, `meeting rooms I`, `minimum arrows` | [구간 / Interval Greedy 패턴](./interval-greedy-patterns.md) | 끝점 정렬과 비겹침 선택이 핵심인 greedy 변형이다 |
| `meeting rooms II`, `minimum meeting rooms`, `max concurrency`, `calendar overlap count` | [Sweep Line Overlap Counting](./sweep-line-overlap-counting.md) | interval을 고르는 문제가 아니라 동시성 계수를 세는 문제다 |
| `calendar booking`, `online reservation insert`, `insert interval then query overlap` | [Interval Tree](../data-structure/interval-tree.md) / [Disjoint Interval Set](../data-structure/disjoint-interval-set.md) | batch greedy가 아니라 online insert/query workload다 |
| `0-1 knapsack`, `TSP`, `지금 이득이 미래 선택을 망친다` | [동적 계획법](./basic.md#동적-계획법-dynamic-programming) | greedy가 깨지는 대표 반례 구간이다 |

## Greedy 알고리즘이란?

**그리디 알고리즘**(욕심쟁이 알고리즘, Greedy Algorithm)은 매 선택 순간에 가장 좋아 보이는 답을 고정해 나가는 알고리즘 설계 기법이다.

핵심은 "지금 최선"과 "전체 최적"이 항상 같은 것은 아니라는 점이다.
따라서 greedy는 감으로 쓰는 기법이 아니라, **지금의 선택을 확정해도 전체 최적해가 깨지지 않는다는 증명**이 있을 때만 안전하다.

## Greedy 알고리즘 예제

예를 들어 1번 도시에서 5번 도시까지 이동하는데, 매번 현재 도시에서 가장 비용이 낮은 간선만 선택한다고 가정해 보자.

이 방식은 각 단계에서는 그럴듯하지만, 전체 경로 합이 최소가 된다는 보장은 없다.

- 현재 선택 경로: `1 - 1 - 1 - 100`
- 다른 선택 경로: `1 - 1 - 10 - 10`

앞의 세 단계만 보면 첫 번째 선택이 더 좋아 보이지만, 마지막까지 합치면 두 번째 경로가 더 낫다.
즉 **국소 최적(local optimum)** 이 자동으로 **전역 최적(global optimum)** 이 되지는 않는다.

## Greedy 알고리즘은 언제 사용할 수 있는가?

다음 두 속성을 만족할 때 greedy를 적용할 수 있다.

- **탐욕 선택 속성(greedy choice property)**: 지금의 greedy한 선택을 먼저 해도 최적해를 잃지 않는다.
- **최적 부분 구조(optimal substructure)**: 현재 문제의 최적해가 부분 문제들의 최적해로부터 구성된다.

실전에서는 보통 다음 질문으로 빠르게 점검한다.

- 지금 선택을 확정한 뒤 다시 되돌릴 필요가 없는가?
- 더 나중 선택을 위해 현재 선택을 일부러 손해 보며 미뤄야 하지는 않는가?
- 정렬 기준이나 우선순위 기준을 한 번 고르면 끝까지 일관되게 밀 수 있는가?

증명은 보통 교환 논증(exchange argument), cut property, 혹은 "더 나쁜 선택으로 바꿔도 손해가 없다"는 식으로 진행된다.

## 자주 쓰는 정당화 패턴

- **교환 논증(exchange argument)**: 어떤 최적해가 greedy 선택으로 시작하지 않더라도, 첫 선택을 greedy 선택으로 바꿔도 손해가 없음을 보인다. interval scheduling이 대표적이다.
- **stays ahead**: greedy가 각 단계에서 다른 어떤 후보해보다 뒤처지지 않음을 보인다. prefix 비교나 누적 기준 비교에서 자주 쓴다.
- **cut property**: 구조를 둘로 나눴을 때 그 경계를 가로지르는 안전한 최소 선택이 있음을 보인다. Prim, Kruskal 같은 MST 계열에서 핵심이다.

## 대표적인 Greedy 알고리즘 예시

- 활동 선택 문제(Activity Selection Problem)
- 구간 스케줄링과 회의 배정
- 거스름돈 문제(화폐 체계 조건이 맞을 때)
- 최소 신장 트리(Minimum Spanning Tree)의 Prim, Kruskal
- 다익스트라 알고리즘
- 허프만 코딩(Huffman Coding)
- Fractional Knapsack

## Greedy로 최적해를 보장할 수 없는 대표 문제

- 외판원 순회 문제(TSP, Traveling Salesperson Problem)
- 0-1 배낭 문제(0-1 Knapsack Problem)
- 화폐 단위가 일반적이지 않은 거스름돈 변형 문제

이런 문제는 "당장 가장 이득인 선택"이 이후 선택 공간을 망가뜨릴 수 있어서 greedy만으로는 정답 보장이 어렵다.
그래서 DP, 완전 탐색, 백트래킹, branch and bound 같은 다른 접근이 필요해진다.

## 한 줄 정리

greedy는 빠르고 구현이 단순하지만, **탐욕 선택 속성 + 최적 부분 구조**가 증명되지 않으면 오답을 빠르게 만드는 기법이 될 수 있다.

**Reference** [나무위키(그리디 알고리즘)](https://namu.wiki/w/%EA%B7%B8%EB%A6%AC%EB%94%94%20%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98)
