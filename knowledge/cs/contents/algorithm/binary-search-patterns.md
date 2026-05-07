---
schema_version: 3
title: Binary Search Patterns
concept_id: algorithm/binary-search-patterns
canonical: true
category: algorithm
difficulty: intermediate
doc_role: bridge
level: intermediate
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- binary-search-boundary-pattern
- monotonic-predicate-design
- parametric-search-feasibility
aliases:
- binary search patterns
- answer space binary search
- first true boundary
- last false boundary
- monotonic predicate
- lower bound upper bound
- parametric search
- boundary search
- 이분 탐색 패턴
- 답의 범위 이분 탐색
- 처음 참 경계 찾기
- 단조 조건 판정
symptoms:
- 정렬 배열에서 값 하나 찾는 코드만 외워서 가능한 최소값이나 최대 허용치 문제를 이분 탐색으로 못 바꿔
- lower_bound와 upper_bound를 exact match 탐색과 섞어서 중복 값이나 경계 조건에서 자주 틀려
- 판정 함수가 단조적인지 확인하지 않고 mid만 줄여서 답이 우연히 맞는 코드가 나온다
intents:
- comparison
- deep_dive
- troubleshooting
prerequisites:
- algorithm/binary-search-intro
- algorithm/sort-to-binary-search-bridge
next_docs:
- algorithm/longest-increasing-subsequence-patterns
- algorithm/sliding-window-patterns
- algorithm/two-pointer
- algorithm/problem-signal-to-pattern-router-beginner
linked_paths:
- contents/algorithm/binary-search-intro.md
- contents/algorithm/sort-to-binary-search-bridge.md
- contents/algorithm/longest-increasing-subsequence-patterns.md
- contents/algorithm/sliding-window-patterns.md
- contents/algorithm/two-pointer.md
- contents/algorithm/problem-signal-to-pattern-router-beginner.md
confusable_with:
- algorithm/sliding-window-patterns
- algorithm/two-pointer
- algorithm/longest-increasing-subsequence-patterns
forbidden_neighbors: []
expected_queries:
- 이분 탐색을 정렬된 배열 검색 말고 답의 범위에서 처음 참이 되는 경계 찾기로 쓰는 법을 설명해줘
- lower bound와 upper bound가 exact match 탐색과 어떻게 다른지 중복 값 예시로 알려줘
- parametric search에서 가능한지 판정하는 함수가 왜 단조적이어야 하는지 알고 싶어
- 길이 L의 연속 구간이 가능한지 확인하는 문제에서 이분 탐색과 슬라이딩 윈도우가 어떻게 같이 쓰이는지 비교해줘
- LIS에서 binary search가 서브루틴으로 쓰일 때와 문제 자체가 이분 탐색인 경우를 구분해줘
contextual_chunk_prefix: |
  이 문서는 이분 탐색을 단순 값 검색이 아니라 단조 조건의 경계 탐색으로 확장하는 bridge다.
  lower_bound, upper_bound, first true, last false, answer space binary search, parametric search, feasibility check, LIS의 binary search 서브루틴, sliding window 판정 함수와의 조합을 구분한다.
---
# Binary Search Patterns

> 한 줄 요약: 이분 탐색은 "정렬된 배열에서 값 찾기"가 아니라, `조건이 처음 참이 되는 지점`을 빠르게 찾는 패턴이다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **단조 조건과 경계 탐색 설계**를 다루는 pattern deep dive다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: binary search patterns basics, binary search patterns beginner, binary search patterns intro, algorithm basics, beginner algorithm, 처음 배우는데 binary search patterns, binary search patterns 입문, binary search patterns 기초, what is binary search patterns, how to binary search patterns
> 관련 문서:
> - [시간복잡도와 공간복잡도](./basic.md#시간복잡도와-공간복잡도)
> - [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md)
> - [Sliding Window Patterns](./sliding-window-patterns.md)
> - [두 포인터 (two-pointer)](./two-pointer.md)
>
> retrieval-anchor-keywords: binary search, lower bound, upper bound, first true, last false, parametric search, decision problem, monotonic predicate, monotone decision, feasibility check, answer space search, boundary search, lis lower_bound, lower_bound on tails, subsequence vs subarray, contiguous window feasibility, length feasibility check

---

## 이 문서 다음에 보면 좋은 문서

- `lower_bound`가 실제로 어디에 쓰이는지 이어서 보려면 [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md)이 가장 가깝다.
- `subsequence`처럼 연속성이 없고 순서만 보존하면 되는 문제라면 [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md)로 먼저 가는 편이 덜 헷갈린다.
- 연속 구간을 점진적으로 줄이고 늘리는 문제라면 [Sliding Window Patterns](./sliding-window-patterns.md)과의 경계를 비교해 보면 좋다.
- 정렬 배열의 양끝이나 서로 다른 두 위치를 좁혀 가는 문제라면 [두 포인터 (two-pointer)](./two-pointer.md)가 더 직접적이다.
- 복잡도 감각과 Big-O 기준부터 다시 잡고 싶다면 [시간복잡도와 공간복잡도](./basic.md#시간복잡도와-공간복잡도)로 되돌아가면 된다.

## 핵심 개념

이분 탐색은 보통 다음 두 가지로 나뉜다.

1. 정렬된 배열에서 특정 값을 찾는 탐색
2. 답의 범위를 잡고 조건을 만족하는 최소/최대 값을 찾는 탐색

실무와 코딩테스트에서는 2번이 더 자주 나온다.

- 최소 작업 시간
- 최소 용량
- 최대 허용치
- 조건을 만족하는 첫 위치

이분 탐색의 핵심은 `정답 후보가 연속된 구간으로 정리된다`는 점이다.
이 구간 성질이 깨지면 이분 탐색을 쓰면 안 된다.

## 자주 헷갈리는 패턴 구분

| 패턴 | 탐색 대상 | 질문 형태 | 강한 신호 |
|---|---|---|---|
| Binary Search | 값의 범위, 인덱스 경계, 정답 후보 공간 | "`x`가 가능한가?", "처음 참은 어디인가?" | 판정 결과가 `false ... true`처럼 한 번만 바뀐다 |
| LIS | 순서를 유지한 부분 수열 최적화 | "건너뛰며 가장 긴 증가 수열을 만들 수 있는가?" | `subsequence`, `tails`, 증가 추세, 연속 조건이 없다 |
| Sliding Window | 연속된 부분 배열 / 부분 문자열 | "현재 구간을 한 칸 밀며 갱신할 수 있는가?" | `subarray`, `substring`, 길이/합/빈도 조건이 같이 나온다 |
| Two Pointer | 두 인덱스 사이의 관계 | "두 값을 비교하며 포인터를 줄이거나 늘릴 수 있는가?" | 정렬 배열, 양끝 포인터, pair sum, palindrome 같은 표현이 나온다 |

- LIS의 `tails + binary search`는 이분 탐색을 "서브루틴"으로 쓰는 대표 예시다. 하지만 질문이 `subsequence`를 묻는다면 1차 라우팅은 [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md)여야 한다.
- `길이 L의 연속 구간 중 조건을 만족하는 것이 있는가?`처럼 보이면 바깥 패턴은 이분 탐색이고, 내부 판정 함수는 [Sliding Window Patterns](./sliding-window-patterns.md)일 수 있다.
- 연속 구간 자체를 유지할 필요 없이 정렬 배열의 양끝에서 합이나 차이를 맞추는 문제면 [두 포인터 (two-pointer)](./two-pointer.md)가 더 자연스럽다.

---

## 깊이 들어가기

### 1. lower_bound / upper_bound

`lower_bound`는 "처음으로 조건 이상이 되는 위치"를 찾는다.
`upper_bound`는 "처음으로 조건 초과가 되는 위치"를 찾는다.

이 두 패턴은 정렬된 배열에서 중복 원소의 경계를 찾을 때 가장 많이 쓴다.

```java
public static int lowerBound(int[] arr, int target) {
    int left = 0;
    int right = arr.length;

    while (left < right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] >= target) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}
```

### 2. 답의 범위 이분 탐색

정렬되지 않은 문제도 조건이 단조성을 가지면 이분 탐색이 가능하다.

예:

- `x`분 안에 작업을 끝낼 수 있는가
- `m`개의 서버로 처리 가능한가
- `capacity`가 충분한가

이런 문제는 `true/false`가 한 번 바뀌면 다시 돌아오지 않아야 한다.

즉,

```text
false false false true true true
```

같은 형태여야 한다.

### 3. 파라메트릭 서치

답을 직접 찾는 대신, 가능한 값 하나를 가정하고 조건을 검사한다.
그 후 조건을 만족하는 최소/최대 값을 이분 탐색으로 좁힌다.

이때 구현 실수는 대부분 아래에서 나온다.

- `left`, `right` 경계 포함/제외를 혼동함
- `mid` 갱신 시 무한 루프가 생김
- 조건 함수가 단조적이지 않은데 억지로 사용함

---

## 실전 시나리오

### 시나리오 1: 가장 작은 허용값 찾기

`N`개 작업을 `k`개의 그룹으로 나눠서 최대 비용을 최소화해야 한다.

이럴 때는 "비용이 `limit` 이하로 가능한가"를 검사하는 함수가 필요하다.
그 함수가 단조적이면 이분 탐색을 적용할 수 있다.

### 시나리오 2: 중복 원소 경계 찾기

검색 결과에서 특정 키워드가 여러 번 등장하는 경우,
`lower_bound`와 `upper_bound`로 시작/끝 지점을 빠르게 찾을 수 있다.

### 시나리오 3: 단조성 없는 문제에 억지 적용

정렬되지 않은 배열에서 조건이 중간에 다시 바뀌는데도 이분 탐색을 쓰면,
정답이 아니라 "우연히 맞는 값"이 나올 수 있다.

이 경우는 BFS/DFS/DP를 먼저 생각해야 한다.

---

## 코드로 보기

```java
public class ParametricSearch {

    public static long minCapacity(long[] jobs, long days) {
        long left = 1;
        long right = 0;
        for (long job : jobs) right += job;

        while (left < right) {
            long mid = left + (right - left) / 2;
            if (canFinish(jobs, days, mid)) {
                right = mid;
            } else {
                left = mid + 1;
            }
        }
        return left;
    }

    private static boolean canFinish(long[] jobs, long days, long capacity) {
        long usedDays = 1;
        long sum = 0;

        for (long job : jobs) {
            if (job > capacity) return false;
            if (sum + job > capacity) {
                usedDays++;
                sum = 0;
            }
            sum += job;
        }
        return usedDays <= days;
    }
}
```

이 패턴은 "정답 찾기"보다 "검사 함수 설계"가 더 중요하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 선형 탐색 | 구현이 쉽다 | 느리다 | 데이터가 작을 때 |
| 이분 탐색 | 빠르다 | 조건 설계가 필요하다 | 단조성이 있을 때 |
| 투 포인터 | 연속 구간에 강하다 | 적용 범위가 좁다 | 합/길이 조건일 때 |
| DP | 안정적이다 | 상태가 많아질 수 있다 | 최적화 구조가 있을 때 |

핵심 판단 기준은 "이분 탐색을 할 수 있는가"가 아니라,
"조건이 단조적인가"다.

---

## 꼬리질문

> Q: `lower_bound`와 `upper_bound`를 왜 따로 배워야 하나요?
> 의도: 경계 탐색과 중복 처리에 대한 감각 확인
> 핵심: 값 찾기와 경계 찾기는 다른 문제다

> Q: 답의 범위 이분 탐색에서 조건 함수가 왜 중요한가요?
> 의도: 파라메트릭 서치 이해 여부 확인
> 핵심: 이분 탐색 자체보다 단조 조건이 핵심이다

> Q: 이분 탐색을 쓰면 항상 `O(logN)`인가요?
> 의도: 반복당 비용과 전체 복잡도 구분 여부 확인
> 핵심: 검사 함수가 `O(N)`이면 전체는 `O(NlogN)`이 될 수 있다

---

## 한 줄 정리

이분 탐색은 정렬 배열만 보는 기술이 아니라, 단조성을 가진 조건에서 "처음 참이 되는 지점"을 빠르게 찾는 패턴이다.
