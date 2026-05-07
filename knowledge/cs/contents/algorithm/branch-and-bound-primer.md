---
schema_version: 3
title: Branch and Bound Primer
concept_id: algorithm/branch-and-bound-primer
canonical: true
category: algorithm
difficulty: intermediate
doc_role: primer
level: intermediate
language: mixed
source_priority: 78
mission_ids: []
review_feedback_tags:
- branch-and-bound
- pruning
- search-space
- optimization
aliases:
- branch and bound
- branch-and-bound
- bounding function
- pruning search tree
- 분기 한정법
- 가지치기 최적화
symptoms:
- 완전탐색은 가능한데 최적해를 찾기 위해 어떤 가지를 버려도 되는지 모르겠다
- backtracking과 branch and bound가 같은 것처럼 느껴진다
- 현재 partial solution으로는 best보다 좋아질 수 없다는 판단을 어떻게 쓰는지 헷갈린다
intents:
- definition
- comparison
- design
prerequisites:
- algorithm/backtracking-intro
- algorithm/brute-force-intro
next_docs:
- algorithm/dancing-links-dlx
- algorithm/meet-in-the-middle
- algorithm/bitmask-dp
linked_paths:
- contents/algorithm/backtracking-intro.md
- contents/algorithm/brute-force-intro.md
- contents/algorithm/dancing-links-dlx.md
- contents/algorithm/meet-in-the-middle.md
- contents/algorithm/bitmask-dp.md
- contents/algorithm/time-complexity-intro.md
confusable_with:
- algorithm/backtracking-intro
- algorithm/brute-force-intro
- algorithm/meet-in-the-middle
forbidden_neighbors: []
expected_queries:
- branch and bound가 뭐고 backtracking과 어떻게 달라?
- 최적화 문제에서 bound로 가지치기한다는 뜻을 설명해줘
- 현재 선택으로는 best보다 좋아질 수 없을 때 왜 탐색을 멈춰도 돼?
- 완전탐색에 pruning을 붙일 때 lower bound upper bound를 어떻게 생각해?
contextual_chunk_prefix: |
  이 문서는 branch and bound를 완전탐색과 backtracking 다음 단계로 설명하는
  algorithm primer다. best solution, lower bound, upper bound, pruning,
  search tree, optimization 같은 표현을 현재 partial solution이 앞으로
  좋아질 수 있는 한계로 가지를 버리는 판단에 매핑한다.
---
# Branch and Bound Primer

> 한 줄 요약: branch and bound는 탐색을 하되, 지금 가지가 아무리 잘 풀려도 현재 best를 이길 수 없으면 그 아래를 통째로 버리는 최적화 탐색이다.

**난이도: Intermediate**

## backtracking과의 차이

| 방식 | 버리는 이유 |
|---|---|
| backtracking | 제약 조건을 이미 어겼다 |
| branch and bound | 제약은 아직 가능하지만 best를 이길 희망이 없다 |

예를 들어 최소 비용 문제에서 현재 비용이 이미 `best`보다 크고, 앞으로 비용이 더 줄지 않는다면 그 branch는 더 볼 필요가 없다.

## bound의 의미

| 문제 방향 | bound 질문 |
|---|---|
| 최소화 | 이 가지가 앞으로 도달할 수 있는 최소 비용이 현재 best보다 작은가 |
| 최대화 | 이 가지가 앞으로 도달할 수 있는 최대 점수가 현재 best보다 큰가 |

bound가 빡빡할수록 더 많이 버릴 수 있지만, 계산 비용이 너무 크면 오히려 느려질 수 있다.

## 적용 체크

1. 완전탐색 상태를 정의한다.
2. 현재까지의 partial solution 값을 계산한다.
3. 앞으로 아무리 잘해도 가능한 한계 값을 추정한다.
4. 그 한계가 best를 이기지 못하면 branch를 버린다.

정확한 bound가 아니어도 된다.
다만 안전해야 한다. 최소화 문제에서 실제 가능한 최소보다 더 낙관적인 값은 괜찮지만, 더 비관적으로 잡아 최적해 가지를 버리면 안 된다.

