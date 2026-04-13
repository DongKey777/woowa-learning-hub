# Longest Increasing Subsequence Patterns

> 한 줄 요약: LIS는 단순 길이 계산을 넘어서, 최적 부분구조와 이분 탐색을 결합해 순서 최적화 문제를 푸는 대표 패턴이다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [알고리즘 기본](./basic.md)
> - [Rolling Hash / Rabin-Karp](./rolling-hash-rabin-karp.md)

> retrieval-anchor-keywords: lis, longest increasing subsequence, patience sorting, binary search lis, subsequence dp, sequence optimization, increasing order, tails array, backtracking, variant patterns

## 핵심 개념

LIS는 증가하는 부분 수열 중 가장 긴 것을 찾는 문제다.

대표 풀이 방식은 두 가지다.

- O(n^2) DP
- O(n log n) tails + binary search

실전에서는 길이만 묻는지, 실제 수열 복원이 필요한지에 따라 접근이 갈린다.

## 깊이 들어가기

### 1. O(n^2) DP 감각

각 원소를 끝점으로 하는 LIS 길이를 구한다.

- 앞의 원소들 중 자신보다 작은 것들을 본다
- 그중 최댓값에 1을 더한다

직관적이고 복원이 쉽다.

### 2. tails 배열

O(n log n) 방식은 각 길이에 대해 가능한 가장 작은 tail 값을 유지한다.

- tail이 작을수록 다음 원소를 붙이기 쉽다
- 이분 탐색으로 위치를 찾는다

이 구조가 성능을 끌어올린다.

### 3. backend에서의 감각

LIS는 직접 서비스 로직보다도 "순서 최적화" 사고에 자주 나타난다.

- 점수 상승 추세
- 상태 전이 최적화
- 무작위 순서에서 안정적 경향 찾기

### 4. 변형이 많다

LIS는 여러 응용이 있다.

- 가장 긴 감소 수열
- 비내림차순 수열
- 가중 LIS
- 복원 가능한 LIS

## 실전 시나리오

### 시나리오 1: 성장 추세 분석

시간 순으로 정렬된 지표에서 증가 추세의 길이를 보고 싶을 때 쓴다.

### 시나리오 2: 배치 최적화

순서를 바꿀 수 없고 선택만 할 수 있는 문제에서 자주 등장한다.

### 시나리오 3: 오판

연속 구간이 아니라 부분 수열이라는 점을 놓치면 슬라이딩 윈도우로 풀 수 있다고 착각하기 쉽다.

### 시나리오 4: 복원 필요

길이뿐 아니라 실제 수열이 필요하면 predecessor를 저장해야 한다.

## 코드로 보기

```java
import java.util.Arrays;

public class LisPatterns {
    public int lengthOfLIS(int[] nums) {
        int[] tails = new int[nums.length];
        int size = 0;
        for (int x : nums) {
            int l = 0, r = size;
            while (l < r) {
                int m = (l + r) >>> 1;
                if (tails[m] < x) l = m + 1;
                else r = m;
            }
            tails[l] = x;
            if (l == size) size++;
        }
        return size;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| O(n^2) DP | 복원이 쉽고 직관적이다 | 느리다 | 작은 n |
| O(n log n) tails | 빠르다 | 복원이 까다롭다 | 큰 n |
| Brute force | 이해가 쉽다 | 비현실적으로 느리다 | 검증용 |

## 꼬리질문

> Q: tails 배열은 무엇을 의미하나?
> 의도: 최적 부분구조 이해 확인
> 핵심: 길이별 최소 가능한 끝값이다.

> Q: 왜 이분 탐색이 들어가나?
> 의도: LIS와 binary search 연결 확인
> 핵심: tails가 정렬된 상태를 유지하기 때문이다.

> Q: 부분 수열과 부분 배열은 같은가?
> 의도: 패턴 오해 방지
> 핵심: 다르다. LIS는 부분 수열이다.

## 한 줄 정리

LIS는 증가 부분 수열 최적화를 다루는 대표 패턴이고, tails + 이분 탐색으로 O(n log n)에 풀 수 있다.
