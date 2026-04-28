# Deletion-Aware Connectivity Bridge

> 한 줄 요약: union-find는 `합치기만 계속되는 연결 여부`에는 강하지만, 간선을 지운 뒤에도 아직 이어져 있는지를 바로 판정하거나 쪼개는 일은 못해서 삭제가 보이면 DSU rollback 같은 다음 도구로 넘어가야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 README](./README.md)
- [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md)
- [Union-Find Deep Dive](./union-find-deep-dive.md)
- [DSU Rollback](../algorithm/dsu-rollback.md)
- [Bridges and Articulation Points](../algorithm/bridges-and-articulation-points.md)

retrieval-anchor-keywords: deletion aware connectivity, edge deletion connectivity, union find deletion limit, union find split limitation, connectivity after edge removal, why union find cannot delete, dsu rollback intro, offline dynamic connectivity beginner, graph connectivity deletion beginner, 간선 삭제 연결성, 간선 제거 후 연결 여부, 유니온 파인드 삭제 한계

## 핵심 개념

처음 union-find를 배우면 `연결 여부 = union-find`처럼 외우기 쉽다.
이 공식은 반만 맞다.

정확히는 **간선이 추가되기만 하고**, 질문도 **둘이 같은 그룹인지 yes/no만 묻는 상황**에서 아주 강하다.
문제는 간선을 지우는 순간 시작된다.

삭제가 들어오면 질문이 `한 번 합쳤던 둘을 다시 나눌 수 있나?`로 바뀌지 않는다.
실제로는 `이 간선을 지워도 다른 우회 길이 남아 있나?`, `삭제 전 상태로 잠깐 돌아가야 하나?` 같은 질문이 붙는다.
그래서 삭제가 있는 연결성은 plain union-find의 연장선이라기보다, **다른 문제로 읽는 첫 감각**이 중요하다.

## 한눈에 보기

| 상황 | plain union-find | 왜 막히나 | 다음 첫 선택지 |
|---|---|---|---|
| 간선 추가만 있다 | 잘 맞는다 | 합치기만 하면 된다 | union-find |
| 간선을 하나 지운 뒤 still connected인지 묻는다 | 바로 답 못 한다 | 대체 경로가 남는지 저장하지 않는다 | BFS/DFS 재탐색 |
| 삭제/복구 질의를 여러 번 미리 안다 | 그대로는 못 푼다 | 과거 상태로 돌아갈 수 없다 | [DSU Rollback](../algorithm/dsu-rollback.md) |
| `이 간선이 끊기면 그래프가 둘로 갈리나?`가 핵심이다 | 직접 판정이 약하다 | bridge 여부가 핵심이다 | [Bridges and Articulation Points](../algorithm/bridges-and-articulation-points.md) |

짧게 외우면 이렇다.

- union-find는 `합치기`에는 강하다
- 삭제는 `쪼개기`보다 `우회 경로 판단`이 핵심이다
- 그래서 삭제가 보이면 바로 다음 도구를 떠올려야 한다

## 왜 삭제가 plain union-find를 깨뜨리나

union-find가 기억하는 것은 `누가 같은 그룹인가`다.
반대로 아래 정보는 기본적으로 기억하지 않는다.

- 어떤 간선이 그 연결을 만들었는지
- 지금 지우려는 간선 말고 다른 우회 경로가 남는지
- 이전 시점으로 어떻게 되돌아가야 하는지

예를 들어 아래 두 그래프를 보자.

```text
A. cycle
1 - 2
|   |
4 - 3

(2,3)을 지워도 2 -> 1 -> 4 -> 3으로 돌아갈 수 있다
```

```text
B. chain
1 - 2 - 3 - 4

(2,3)을 지우면 1-2와 3-4로 갈라진다
```

삭제 전에는 두 그래프 모두 `1`과 `4`가 연결되어 있다.
하지만 `(2,3)`을 지운 뒤 결과는 다르다.
첫 번째는 여전히 연결, 두 번째는 분리다.

plain union-find는 삭제 전의 `같은 그룹` 정보만 강하게 들고 있고, 그 연결이 **어떤 모양으로 유지되었는지**는 들고 있지 않다.
그래서 `지운 뒤에도 still connected인가?`를 단독으로 판정하지 못한다.

## 처음 떠올릴 다음 도구

삭제가 보였다고 무조건 어려운 자료구조부터 가면 초반에 더 헷갈린다.
문제 문장을 먼저 이렇게 번역하면 된다.

| 문제 문장 | 먼저 할 생각 | 이유 |
|---|---|---|
| `이 간선을 지워도 아직 갈 수 있어?` | 현재 그래프에서 BFS/DFS 재탐색 | 우회 경로가 남는지 직접 보면 된다 |
| `삭제와 복구 질의를 한꺼번에 처리해` | [DSU Rollback](../algorithm/dsu-rollback.md) | union 결과를 되돌리며 시간 축을 오프라인으로 다룬다 |
| `이 간선이 끊기면 치명적인가?` | [Bridges and Articulation Points](../algorithm/bridges-and-articulation-points.md) | bridge 판정이 문제의 중심이다 |
| `삽입/삭제가 실시간으로 계속 온다` | fully dynamic connectivity 계열 | rollback만으로는 온라인 변화를 다 받기 어렵다 |

초급자 기준에서는 여기서 fully dynamic connectivity를 깊게 파지 않아도 된다.
핵심은 `삭제가 들어오면 plain union-find 한 장으로 끝나지 않는다`는 감각을 먼저 고정하는 것이다.

## 흔한 오해와 함정

- `삭제는 union의 반대니까 split만 있으면 되지 않나요?`
  union-find는 애초에 split을 직접 지원하는 구조가 아니다.
- `parent를 거꾸로 고치면 지울 수 있지 않나요?`
  이미 여러 union이 겹친 뒤에는 어떤 간선 때문에 붙었는지 정보가 충분하지 않다.
- `연결 여부만 묻는데 왜 BFS/DFS가 다시 나오나요?`
  삭제 뒤의 연결 여부는 현재 그래프의 실제 우회 경로를 봐야 할 수 있기 때문이다.
- `DSU rollback이면 모든 동적 그래프를 다 해결하나요?`
  아니다. 보통은 오프라인 질의에 강하고, 완전 온라인 삭제/삽입 문제는 더 어려운 범주다.

## 실무에서 쓰는 모습

코딩 테스트나 학습 문제에서 자주 만나는 장면은 보통 세 가지다.

1. 친구 관계나 네트워크 연결이 추가되기만 한다.
   이때는 union-find가 첫 선택지다.
2. 특정 간선을 제거했을 때도 같은 컴포넌트인지 묻는다.
   이때는 현재 그래프에서 BFS/DFS로 확인하거나, 문제 크기에 따라 더 강한 기법으로 간다.
3. `시간 t에는 간선이 있었고, 시간 t+1에는 사라졌다` 같은 질의가 여러 개 묶여 있다.
   이때는 [DSU Rollback](../algorithm/dsu-rollback.md)처럼 되돌릴 수 있는 방식이 필요해진다.

즉 삭제가 들어오는 순간의 첫 분기는 `이걸 다시 탐색으로 볼까, 시간 축 문제로 볼까`다.
이 분기만 정확해도 초급 단계에서 불필요하게 어려운 자료구조로 점프하는 일을 많이 줄일 수 있다.

## 더 깊이 가려면

- add-only 연결성의 첫 관문부터 다시 고정하려면 [Union-Find Standalone Beginner Primer](./union-find-standalone-beginner-primer.md)
- path compression, union by size/rank까지 구조적으로 정리하려면 [Union-Find Deep Dive](./union-find-deep-dive.md)
- 삭제와 복구를 오프라인으로 다루는 첫 고급 기법은 [DSU Rollback](../algorithm/dsu-rollback.md)
- `지운 간선이 bridge였나?`가 핵심이면 [Bridges and Articulation Points](../algorithm/bridges-and-articulation-points.md)

## 면접/시니어 질문 미리보기

| 질문 | 의도 | 짧은 답 방향 |
|---|---|---|
| `왜 plain union-find는 삭제를 바로 못 다루나요?` | 저장 정보의 한계 확인 | 같은 그룹 정보는 강하지만 대체 경로나 과거 상태를 기억하지 않기 때문이다 |
| `삭제 뒤 연결 여부를 가장 직관적으로 확인하는 방법은?` | 문제 분기 감각 확인 | 현재 그래프에서 BFS/DFS로 우회 경로를 직접 확인하는 것이다 |
| `DSU rollback은 언제 떠올리나요?` | handoff 타이밍 확인 | 삭제/복구가 시간 축으로 여러 번 나오고, 질의를 오프라인으로 처리할 수 있을 때다 |

## 한 줄 정리

간선 삭제가 보이는 순간 연결성 문제는 `합쳐졌나`보다 `지운 뒤에도 우회 경로가 남나`가 핵심이 되므로, plain union-find에서 BFS/DFS 재탐색이나 DSU rollback 같은 다음 도구로 넘어가야 한다.
