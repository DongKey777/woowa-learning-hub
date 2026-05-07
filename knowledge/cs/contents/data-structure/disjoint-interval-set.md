---
schema_version: 3
title: Disjoint Interval Set
concept_id: data-structure/disjoint-interval-set
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 85
mission_ids:
- missions/roomescape
review_feedback_tags:
- interval-canonicalization
- treemap-interval-bridge
- reservation-window-merge
aliases:
- disjoint interval set
- interval set
- merge intervals online
- non-overlapping ranges
- canonical interval map
- TreeMap intervals
- reservation window merge
symptoms:
- TreeMap으로 양옆 이웃을 읽는 단계와 insert 후 전체 구간을 non-overlapping canonical state로 유지하는 단계를 섞는다
- 예약, allowlist, 점유 시간창을 겹치는 구간 그대로 쌓아 질의마다 여러 조각을 반복 비교한다
- interval tree가 필요한 overlap search 문제와 disjoint interval set으로 충분한 merge/canonicalization 문제를 구분하지 못한다
intents:
- comparison
- design
prerequisites:
- data-structure/treemap-interval-entry-primer
next_docs:
- data-structure/interval-tree
- algorithm/sweep-line-overlap-counting
- algorithm/interval-greedy-patterns
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
linked_paths:
- contents/data-structure/treemap-interval-entry-primer.md
- contents/data-structure/interval-tree.md
- contents/algorithm/sweep-line-overlap-counting.md
- contents/algorithm/interval-greedy-patterns.md
- contents/data-structure/treemap-vs-hashmap-vs-linkedhashmap.md
confusable_with:
- data-structure/interval-tree
- algorithm/sweep-line-overlap-counting
- algorithm/interval-greedy-patterns
- data-structure/treemap-interval-entry-primer
forbidden_neighbors: []
expected_queries:
- Disjoint Interval Set은 TreeMap interval primer 다음에 언제 필요해?
- 예약 구간을 insert할 때마다 겹치는 구간을 merge해 canonical state로 유지하는 방법은?
- interval tree와 disjoint interval set은 overlap query와 merge 유지 기준으로 어떻게 달라?
- non-overlapping ranges를 TreeMap floor ceiling으로 관리하는 감각을 알려줘
- IP allowlist나 예약 시간창을 disjoint interval로 유지하는 이유는?
contextual_chunk_prefix: |
  이 문서는 겹치지 않는 interval들을 정렬된 canonical state로 유지하는
  Disjoint Interval Set chooser다. TreeMap floorEntry/ceilingEntry로 이웃을
  읽는 primer에서 insert 후 merge, gap tracking, 예약 window, allowlist
  range 관리로 넘어가는 기준을 설명한다.
---
# Disjoint Interval Set

> 한 줄 요약: Disjoint Interval Set은 겹치지 않는 구간들을 정렬해 유지하면서 병합, 삭제, 충돌 검사를 빠르게 하도록 설계한 구간 관리 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
> - [Interval Tree](./interval-tree.md)
> - [Sweep Line Overlap Counting](../algorithm/sweep-line-overlap-counting.md)
> - [구간 / Interval Greedy 패턴](../algorithm/interval-greedy-patterns.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)

> retrieval-anchor-keywords: disjoint interval set, interval set, insert interval, merge intervals, online interval merge, non-overlapping ranges, range union, canonical interval map, TreeMap intervals, floorKey ceilingKey, gap tracking, calendar booking i, booking feasibility, neighbor overlap check, reservation windows, interval canonicalization, 실시간 예약 가능 여부, treemap interval primer next, treemap interval after primer, disjoint set beginner bridge, interval canonical state, online interval insert merge

## TreeMap 입문 다음에 이 문서로 오는 순간

`TreeMap Interval Entry Primer`를 막 끝냈다면, 이 문서는 "`floorEntry`/`ceilingEntry`로 양옆 예약을 보는 단계" 다음에 읽으면 된다.

초보자 기준으로는 이렇게 넘기면 된다.

| 아직 TreeMap primer에 머물러도 되는 경우 | 이제 이 문서로 넘어올 때 |
|---|---|
| 새 예약이 들어왔을 때 왼쪽/오른쪽 이웃만 보고 `겹치나?`를 판단하는 연습이 먼저다 | 예약을 넣을 때마다 겹치는 구간을 합쳐서 항상 "안 겹치는 상태"로 유지해야 한다 |
| `floorEntry`, `ceilingEntry`, `subMap`이 아직 낯설다 | `merge`, `gap tracking`, `canonical form`이 문제의 중심어로 보인다 |
| "지금 이 예약을 넣어도 되나?"가 핵심 질문이다 | "넣은 뒤 구조를 어떻게 정리된 상태로 남기나?"가 핵심 질문이다 |

짧게 말하면:

- `TreeMap` primer는 "양옆 이웃을 읽는 법"을 익히는 입문 단계다.
- 이 문서는 "읽은 이웃을 바탕으로 구간들을 합쳐 정리된 상태를 계속 유지하는 법"으로 넘어가는 다리다.

자주 헷갈리는 지점도 하나 있다.

- `TreeMap`을 쓴다고 바로 Disjoint Interval Set이 되는 것은 아니다.
- 핵심 차이는 "`정렬된 이웃을 본다`"가 아니라 "`insert 뒤에도 전체를 비겹침 canonical state로 유지한다`"에 있다.

## 이 문서 다음에 보면 좋은 문서

- 새 interval이 들어올 때마다 "겹치는 게 있는가?"보다 "겹치는 것들을 찾아라"가 더 중요하면 [Interval Tree](./interval-tree.md)가 맞다.
- interval이 한 번에 주어지고 최대 동시성만 세면 된다면 [Sweep Line Overlap Counting](../algorithm/sweep-line-overlap-counting.md)이 더 직접적이다.
- interval을 한 번 정렬한 뒤 어떤 것을 남길지/버릴지가 핵심이면 [구간 / Interval Greedy 패턴](../algorithm/interval-greedy-patterns.md)으로 가야 한다.

## 핵심 개념

Disjoint Interval Set은 서로 겹치지 않는 구간들을 정규화된 상태로 저장한다.
보통 구간이 추가될 때 기존 구간들과 합쳐 하나의 canonical form으로 유지한다.

이 구조의 핵심은 두 가지다.

- 겹치는 구간은 미리 merge한다.
- 질의할 때는 정리된 구간만 보면 된다.

backend에서 자주 만나는 예:

- 예약된 시간대 관리
- 금지 구간/허용 구간 관리
- IP allowlist/denylist 범위
- 점유된 리소스 시간창 관리

핵심은 겹치는 구간들의 **검색 결과를 풍부하게 반환하는 것**보다,
insert가 들어올 때마다 이웃 구간만 보고 canonical form을 유지하는 데 있다.

## 깊이 들어가기

### 1. 왜 disjoint로 유지하나

구간이 겹친 채로 쌓이면 질의마다 여러 조각을 비교해야 한다.

예를 들어 `[1, 3]`, `[2, 6]`, `[8, 10]`을 각각 따로 들고 있으면 overlap 판단이 복잡해진다.
하지만 merge해서 `[1, 6]`, `[8, 10]`으로 유지하면 훨씬 단순해진다.

### 2. merge invariant

구조의 불변식은 다음과 같다.

- 구간은 정렬되어 있다.
- 서로 겹치지 않는다.
- 인접 규칙을 함께 합칠지 정책이 명확하다.

이 불변식이 유지되면 insert, delete, overlap query 모두 쉬워진다.

### 3. TreeMap과 잘 맞는 이유

정렬된 구간을 유지해야 하므로 `TreeMap` 같은 ordered map이 자주 쓰인다.

- 새 구간의 왼쪽/오른쪽 이웃을 찾기 쉽다.
- 합칠 대상만 빠르게 찾을 수 있다.
- range policy를 구현하기 좋다.

### 4. Interval Tree와 어디서 갈리나

둘 다 interval insert/query를 다루지만 관점이 다르다.

- Disjoint Interval Set: merge, reject, gap lookup처럼 **정리된 상태 유지**가 핵심
- Interval Tree: arbitrary overlap search, stabbing query처럼 **검색 질의**가 핵심

그래서 `calendar booking I`, `insert interval`, `merge intervals` 같은 문제는 이 문서가 더 가깝고,
겹치는 구간 전체를 자주 찾거나 복잡한 overlap query가 반복되면 interval tree 쪽이 자연스럽다.

### 5. backend에서 중요한 이유

구간은 실제 서비스에서 시간, 범위, 버전, 권한에 대응한다.

- 배포 배치 시간
- DB maintenance window
- 고객별 요금 적용 구간
- blocked time range

## 실전 시나리오

### 시나리오 1: Calendar Booking I / insert interval

새 예약이 들어올 때 기존 구간과 겹치는지 확인하고, 겹치면 merge 또는 reject 정책을 적용한다.

### 시나리오 2: 허용 범위 정리

여러 차례 추가된 허용 구간을 정리된 형태로 보관하면 조회와 감사가 쉬워진다.

### 시나리오 3: 오판

구간 자체를 많이 분할하는 문제라면 interval tree가 더 잘 맞을 수 있다.
disjoint set은 "겹침 검사"보다 "정리된 상태 유지"가 핵심이다.

### 시나리오 4: gap 분석

정리된 구간 사이의 빈 공간을 보면 사용 가능 시간대를 찾기 쉽다.

## 코드로 보기

```java
import java.util.NavigableMap;
import java.util.TreeMap;

public class DisjointIntervalSet {
    private final NavigableMap<Integer, Integer> intervals = new TreeMap<>();

    public void add(int start, int end) {
        if (start > end) throw new IllegalArgumentException();

        Integer leftKey = intervals.floorKey(start);
        if (leftKey != null && intervals.get(leftKey) + 1 >= start) {
            start = leftKey;
            end = Math.max(end, intervals.get(leftKey));
            intervals.remove(leftKey);
        }

        while (true) {
            Integer key = intervals.ceilingKey(start);
            if (key == null || key > end + 1) break;
            end = Math.max(end, intervals.get(key));
            intervals.remove(key);
        }

        intervals.put(start, end);
    }

    public boolean overlaps(int start, int end) {
        Integer key = intervals.floorKey(end);
        return key != null && intervals.get(key) >= start;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Disjoint Interval Set | 정리된 구간 상태를 유지하고 gap lookup이 쉽다 | 겹침 전체 목록 조회는 약할 수 있다 | merge 중심 구간 관리, booking feasibility |
| Interval Tree | 겹치는 구간 탐색에 강하다 | 구현이 더 복잡하다 | overlap query 중심, dynamic search |
| Sweep Line | 최대 동시성 계산이 직관적이다 | insert/query마다 전체 재계산이 필요하다 | offline overlap count |
| Interval Greedy | 선택/제거 문제에 최적이다 | 정리된 상태 유지에는 맞지 않는다 | interval scheduling, overlap removal |
| 단순 리스트 | 직관적이다 | 구간이 많아지면 느리다 | 데이터가 작을 때 |

## 꼬리질문

> Q: 왜 disjoint invariant가 중요한가?
> 의도: 상태 정규화의 가치를 아는지 확인
> 핵심: 겹치는 구간을 미리 합치면 질의가 단순해진다.

> Q: interval tree와 어떻게 다른가?
> 의도: 목적 차이를 이해하는지 확인
> 핵심: 하나는 정리된 저장, 다른 하나는 충돌 검색이다.

> Q: sweep line과는 어떻게 다른가요?
> 의도: offline batch 계산과 online state 유지 차이 확인
> 핵심: sweep line은 한 번에 전체를 세는 계산이고, disjoint set은 insert마다 canonical state를 갱신한다.

> Q: 왜 TreeMap과 궁합이 좋나?
> 의도: 정렬된 구간 이웃 탐색을 이해하는지 확인
> 핵심: 좌우 경계를 빠르게 찾을 수 있기 때문이다.

## 한 줄 정리

Disjoint Interval Set은 겹치지 않는 구간만 유지해 병합과 충돌 검사를 단순하게 만드는 정리형 구간 자료구조다.
