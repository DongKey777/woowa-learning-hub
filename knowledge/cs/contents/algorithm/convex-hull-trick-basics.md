---
schema_version: 3
title: Convex Hull Trick Basics
concept_id: algorithm/convex-hull-trick-basics
canonical: false
category: algorithm
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- linear-dp-modeling
- line-container-choice
aliases:
- convex hull trick
- cht
- line container
- dp optimization
- lower envelope
- monotonic slopes
- query optimization
- linear dp
- optimization trick
- line intersection
symptoms:
- DP 식은 있는데 왜 갑자기 직선 집합으로 바꾸는지 연결이 안 돼
- deque CHT와 Li Chao tree를 언제 갈라야 하는지 모르겠어
- 기울기 정렬이나 질의 순서 조건이 깨지면 CHT를 써도 되는지 헷갈려
intents:
- deep_dive
prerequisites:
- algorithm/dp-intro
- algorithm/binary-search-patterns
next_docs:
- algorithm/divide-and-conquer-dp-optimization
- algorithm/topological-dp
- algorithm/monotone-queue-dp
linked_paths:
- contents/algorithm/dp-intro.md
- contents/algorithm/binary-search-patterns.md
- contents/algorithm/topological-dp.md
- contents/algorithm/divide-and-conquer-dp-optimization.md
- contents/algorithm/monotone-queue-dp.md
confusable_with:
- algorithm/divide-and-conquer-dp-optimization
- algorithm/monotone-queue-dp
forbidden_neighbors: []
expected_queries:
- DP 점화식을 직선 최소값 질의로 바꾸는 Convex Hull Trick 감각을 설명해줘
- 기울기 순서가 정렬된 경우와 아닌 경우에 CHT 구현 선택이 어떻게 달라져?
- lower envelope를 본다는 말이 선형 비용 DP에서 무슨 뜻이야
- deque CHT를 써도 되는 조건과 Li Chao tree로 넘어가는 경계를 알고 싶어
- 직선 교점 기준으로 최적 후보를 버리는 이유를 beginner 이후 단계에서 이해하고 싶어
contextual_chunk_prefix: |
  이 문서는 알고리즘 학습자가 DP 식이 왜 직선 집합 비교로 바뀌는지, 특정 x에서
  가장 유리한 선만 빠르게 찾는 lower envelope 감각과 구현 조건을 깊이 잡는
  deep_dive다. 선 여러 개 중 최솟값 찾기, 비용식을 직선으로 바꾸기, 직선 후보
  버리기 기준, 기울기 순서 활용, 질의 x 순서 조건 같은 자연어 paraphrase가 본
  문서의 Convex Hull Trick 핵심에 매핑된다.
---
# Convex Hull Trick Basics

> 한 줄 요약: Convex Hull Trick은 여러 직선 중 특정 x에서 최적값을 빠르게 찾기 위해 선들을 정리해 두는 DP 최적화 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [동적 계획법](./basic.md#동적-계획법-dynamic-programming)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [Topological DP](./topological-dp.md)

> retrieval-anchor-keywords: convex hull trick, cht, line container, dp optimization, lower envelope, monotonic slopes, query optimization, linear dp, optimization trick, line intersection

## 핵심 개념

Convex Hull Trick(CHT)은 `y = mx + b` 형태의 직선들 중에서 특정 `x`에서 최소/최대값을 빠르게 찾는 기법이다.

DP 식이 직선의 최솟값으로 바뀌는 순간, 이 최적화가 등장한다.

대표적으로 다음 느낌이다.

- `dp[i] = min(dp[j] + cost(j, i))`
- cost가 선형식으로 정리됨

## 깊이 들어가기

### 1. 왜 직선이 나오나

많은 DP 최적화는 전개해 보면 `x`에 대한 선형식으로 바뀐다.

이때 이전 상태 하나하나를 전부 비교하지 않고, 직선 집합으로 바꿔 처리한다.

### 2. lower envelope 감각

최솟값을 찾는다면 직선들의 아래쪽 경계만 보면 된다.

직선이 많아져도 "어떤 x에서 누가 이기는가"가 정리되면 빠르게 조회할 수 있다.

### 3. monotonic slope / monotonic query

삽입되는 직선의 기울기나 질의 x가 정렬돼 있으면 구현이 훨씬 쉬워진다.

- 기울기 정렬: deque 방식
- arbitrary query: balanced structure

### 4. backend에서의 감각

직선 자체보다 "비용 함수가 선형으로 정리되는가"를 보는 게 중요하다.

- 배치 비용 최적화
- 구간 비용 누적
- 생산성/처리량 trade-off

## 실전 시나리오

### 시나리오 1: DP 비용 최적화

이전 상태의 선형 비용을 최소화하는 문제에서 CHT가 등장한다.

### 시나리오 2: 오판

비용이 선형이 아니거나 구간 정리가 안 되면 CHT를 억지로 쓰면 안 된다.

### 시나리오 3: 질의가 많을 때

직선을 많이 추가하고 질의도 많이 할 때, 전체 스캔보다 훨씬 이득이다.

## 코드로 보기

```java
import java.util.ArrayDeque;
import java.util.Deque;

public class ConvexHullTrickBasics {
    static final class Line {
        long m, b;
        Line(long m, long b) { this.m = m; this.b = b; }
        long value(long x) { return m * x + b; }
    }

    private final Deque<Line> hull = new ArrayDeque<>();

    public void addLine(long m, long b) {
        hull.addLast(new Line(m, b));
    }

    public long query(long x) {
        long best = Long.MAX_VALUE;
        for (Line line : hull) {
            best = Math.min(best, line.value(x));
        }
        return best;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Convex Hull Trick | 선형 DP 최적화가 매우 빠르다 | 조건이 맞아야 한다 | linear cost DP |
| Brute Force | 구현이 쉽다 | 너무 느리다 | 작은 입력 |
| Segment Tree of Lines | 질의 유연성이 높다 | 구현이 복잡하다 | 비정형 삽입/질의 |

## 꼬리질문

> Q: CHT는 어떤 문제에서 나오나?
> 의도: DP 최적화 패턴을 인식하는지 확인
> 핵심: 선형 비용이 섞인 DP다.

> Q: 왜 직선 아래쪽 경계가 중요한가?
> 의도: 최솟값/최댓값 구조 이해 확인
> 핵심: 특정 x에서 가장 좋은 선만 보면 되기 때문이다.

> Q: 언제 쓰면 안 되나?
> 의도: 조건 검증 습관 확인
> 핵심: 비용이 선형으로 정리되지 않을 때다.

## 한 줄 정리

Convex Hull Trick은 선형 DP 비용을 직선 집합의 최적 질의로 바꿔 빠르게 푸는 최적화 기법이다.
