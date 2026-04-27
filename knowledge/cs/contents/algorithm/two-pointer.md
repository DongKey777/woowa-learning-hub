# 두 포인터 (two-pointer)

> 한 줄 요약: 두 포인터는 두 인덱스를 이동시키며 관계를 좁혀 가는 상위 패턴이고, pair-relation scan과 contiguous window를 구분해야 오판이 줄어든다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **same-direction / opposite-direction pointer 전략과 pair-relation scan, sliding window, subsequence 최적화의 경계**를 다루는 pattern deep dive다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: two pointer basics, two pointer beginner, two pointer intro, algorithm basics, beginner algorithm, 처음 배우는데 two pointer, two pointer 입문, two pointer 기초, what is two pointer, how to two pointer
> 관련 문서:
> - [정렬 알고리즘](./sort.md)
> - [Sliding Window Patterns](./sliding-window-patterns.md)
> - [Monotonic Queue / Stack](../data-structure/monotonic-queue-and-stack.md)
> - [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [시간복잡도와 공간복잡도](./basic.md#시간복잡도와-공간복잡도)
>
> retrieval-anchor-keywords: two pointer pattern, two-pointer, left right pointers, same direction pointers, opposite direction pointers, pair relation scan, pair scan, sorted array scan, sorted pair sum, two sum sorted, two sum ii, pair difference scan, closest pair scan, palindrome scan, container with most water, left right contraction, pointer sweep, sliding window vs two pointer, pair relation vs contiguous window, subsequence vs two pointer, skip allowed sequence, contiguous subarray, contiguous index range, array interval scan, index interval scan, interval scheduling vs two pointer, meeting rooms not two-pointer, calendar overlap not two-pointer, dual pointer, fixed-size window extrema boundary, sliding window maximum not two-pointer, sliding window minimum not two-pointer, recent k maximum routing, recent k minimum routing, monotonic queue handoff, deque-based window extrema

> 참고 자료:
> - 작성자 권혁진 | [최장증가부분수열 LIS](./materials/최장증가수열.pdf)
> - 작성자 윤가영 | [최장감소부분수열 LDS & 두포인터](./materials/최장감소수열_두포인터.pdf)
> - 구현 예시 | [two_pointer.cpp](./code/two_pointer.cpp)

---

## 이 문서 다음에 보면 좋은 문서

- opposite-direction two-pointer 전에 정렬 전처리가 왜 필요한지는 [정렬 알고리즘](./sort.md)에서 먼저 연결된다.
- 연속 구간을 실제로 유지하는 하위 패턴은 [Sliding Window Patterns](./sliding-window-patterns.md)에서 더 자세히 이어진다.
- `sliding window maximum/minimum`, `최근 k개 최대/최소`처럼 고정 길이 윈도우 극값을 물으면 [Monotonic Queue / Stack](../data-structure/monotonic-queue-and-stack.md)으로 바로 넘어가야 한다.
- `meeting rooms`, `reservation schedule`, `calendar overlap count`처럼 각 원소가 이미 `start/end`를 가진 독립 일정이면 [Interval Greedy Patterns](./interval-greedy-patterns.md)나 [Sweep Line Overlap Counting](./sweep-line-overlap-counting.md)으로 가야 한다.
- 원소를 건너뛰며 순서를 최적화하는 문제라면 [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md)로 라우팅해야 한다.
- `가능/불가능` 경계가 한 번만 바뀌는 문제라면 [Binary Search Patterns](./binary-search-patterns.md)로 넘어가야 한다.
- 복잡도와 포인터 스캔 기본기를 다시 잡고 싶다면 [시간복잡도와 공간복잡도](./basic.md#시간복잡도와-공간복잡도)를 같이 보면 좋다.

## 핵심 개념

두 포인터는 두 개의 인덱스(`left`, `right`)를 움직이며 답 후보를 줄여 가는 패턴이다.
여기서 다루는 구간은 배열/문자열 인덱스 축 위의 연속 범위이지, 각 원소가 `start/end`를 들고 있는 일정 interval 레코드가 아니다.

대표적인 형태는 두 가지다.

1. 같은 방향으로 움직이는 포인터
2. 서로 반대 방향에서 좁혀 오는 포인터

핵심은 "포인터를 한 번 움직였을 때 이전 상태를 버려도 되는 근거"가 있어야 한다는 점이다.

- 연속 구간을 유지해야 하면 sliding window 계열이다.
- 정렬 배열에서 합/차이/순서를 맞추면 opposite-direction two-pointer가 자주 나온다.
- 원소를 자유롭게 건너뛰며 가장 좋은 부분 수열을 고르는 문제라면 two-pointer보다 subsequence/LIS 계열이 먼저다.
- 조건이 `false ... true`처럼 단조적으로 바뀌면 two-pointer보다 이분 탐색이 더 직접적이다.

## 자주 헷갈리는 패턴 구분

| 패턴 | 포인터/상태 | 대표 질문 | 강한 신호 |
|---|---|---|---|
| Two Pointer | 두 위치의 관계를 줄인다 | "합/거리/순서를 맞추며 포인터를 이동할 수 있는가?" | 정렬 배열, 양끝 포인터, pair sum, difference, palindrome, left/right |
| Sliding Window | 연속 구간 `[left, right]`를 유지한다 | "현재 구간을 밀면서 답을 갱신할 수 있는가?" | `subarray`, `substring`, 최근 `k`개, 빈도/합 유지 |
| LIS / Subsequence Optimization | 원소를 건너뛰며 순서를 보존한다 | "몇 개를 skip 하며 가장 좋은 subsequence를 고를 수 있는가?" | `subsequence`, `skip allowed`, `tails`, `lower_bound`, 증가 수열 |
| Binary Search | 정답 후보 공간의 경계를 찾는다 | "`x`가 가능한가?", "처음 참은 어디인가?" | monotonic predicate, answer space, feasibility check |

## 자주 헷갈리는 패턴 구분 (계속 2)

- sliding window는 two-pointer의 한 하위 패턴이다. 모든 sliding window는 two-pointer지만, 모든 two-pointer가 sliding window는 아니다.
- `pair`, `sum`, `difference`, `palindrome`, `left/right`처럼 "두 값의 관계"를 줄이는 표현이 먼저 보이면 contiguous window보다 two-pointer 쪽이 더 정확하다.
- `길이 k`의 모든 구간에서 `max/min`을 묻는다면 포인터 이동 자체보다 극값 후보 만료 관리가 본질이라 [Monotonic Queue / Stack](../data-structure/monotonic-queue-and-stack.md)으로 라우팅해야 한다.
- `meeting`, `schedule`, `reservation`, `calendar overlap`처럼 일정 레코드의 겹침이나 배정을 묻는 표현이 먼저 보이면 two-pointer보다 [Interval Greedy Patterns](./interval-greedy-patterns.md)나 [Sweep Line Overlap Counting](./sweep-line-overlap-counting.md) 쪽이 맞다.
- `subsequence`, `skip allowed`, `order preserving`가 먼저 보이면 현재 두 위치를 맞추는 스캔보다 [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md) 같은 subsequence 라우트가 우선이다.
- `길이 L`이 가능한지 판정하면서 포인터로 구간을 훑는다면, 바깥은 [Binary Search Patterns](./binary-search-patterns.md), 내부 검사는 [Sliding Window Patterns](./sliding-window-patterns.md)일 수 있다.

## 깊이 들어가기

### 1. same-direction two-pointer

`left`, `right`가 모두 오른쪽으로 이동한다.

이 형태는 보통 연속 구간을 유지하므로 sliding window와 거의 겹친다.

예:

- 중복 없는 가장 긴 부분 문자열
- 합이 `S` 이상인 최소 길이 부분 배열
- 최근 `k`개 요청 집계

다만 `최근 k개 최대/최소`, `max/min in every window`처럼 고정 길이 윈도우의 극값을 묻는다면 same-direction pointer만으로는 부족하다.
포인터는 창 경계만 옮기고, 실제 답 후보 관리는 [Monotonic Queue / Stack](../data-structure/monotonic-queue-and-stack.md)의 단조 deque가 맡는다.

### 2. opposite-direction two-pointer

`left`는 왼쪽에서 시작하고 `right`는 오른쪽에서 시작해 서로를 향해 움직인다.

예:

- 정렬 배열에서 `target` 합 찾기
- 회문 문자열 검사
- 물통 문제처럼 양끝 높이를 비교하며 줄여 가는 문제

이 경우는 연속 구간 상태를 유지하지 않아도 되므로 sliding window보다 더 일반적인 "두 위치 관계 조정" 문제다.

### 3. subsequence와 헷갈릴 때는 "skip allowed"를 먼저 본다

두 포인터의 대표 문제는 현재 `left`, `right`가 가리키는 **두 위치 관계**를 줄이는 스캔이다.
반면 LIS류는 "어떤 원소를 건너뛰어도 되는가"와 "그 결과 가장 좋은 subsequence가 무엇인가"가 핵심이다.

- `pair sum`, `pair difference`, `palindrome`, `closest pair`, `container with most water`면 two-pointer 쪽이다.
- `subarray`, `substring`, `minimum window`, `recent k`면 [Sliding Window Patterns](./sliding-window-patterns.md) 쪽이다.
- `subsequence`, `skip allowed`, `증가 부분 수열`, `tails`, `lower_bound`면 [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md) 쪽이다.

주의할 점도 있다. `"s가 t의 subsequence인가?"`처럼 **포함 여부만 확인하는 문제**는 same-direction two-pointer로 풀 수 있다.
여기서 말하는 subsequence 혼동은 LIS처럼 "건너뛰는 선택 자체를 최적화"하는 문제를 뜻한다.

### 4. 정렬 여부가 성능을 바꾼다

정렬된 배열에서 opposite-direction two-pointer는 보통 O(n)이다.
하지만 정렬이 필요하면 전체 시간복잡도는 정렬 비용까지 포함해 O(n log n)이 된다.

## 깊이 들어가기 (계속 2)

즉 "정렬 안 된 배열에서도 two-pointer니까 O(n)"이라고 보면 오판하기 쉽다.

## 실전 시나리오

### 시나리오 1: 정렬 배열에서 pair sum 찾기

합이 너무 작으면 `left`를 늘리고, 너무 크면 `right`를 줄인다.
정렬 덕분에 한 번 버린 후보를 다시 볼 필요가 없다.

### 시나리오 2: sliding window로 착각하는 경우

문제가 `subarray`, `substring`이 아니라 "서로 다른 두 값"의 조합을 묻는다면 같은 구간을 유지할 이유가 없다.
이때는 sliding window보다 opposite-direction two-pointer가 더 정확하다.

### 시나리오 3: subsequence 최적화로 착각하는 경우

문제가 "중간 원소를 건너뛰어도 된다", "가장 긴 증가 subsequence를 구하라"처럼 선택 자체를 최적화한다면 pair-relation scan이 아니다.
이때는 두 위치를 조이기보다 [Longest Increasing Subsequence Patterns](./longest-increasing-subsequence-patterns.md)처럼 subsequence 패턴으로 가야 한다.

### 시나리오 4: binary search로 착각하는 경우

질문이 "최소 가능한 용량"이나 "처음 만족하는 길이"라면 포인터 이동보다 단조 조건 판정이 핵심이다.
이런 문제는 [Binary Search Patterns](./binary-search-patterns.md) 쪽이 더 직접적이다.

## 코드로 보기

```java
public class TwoPointerPatterns {
    public boolean hasPairWithSum(int[] sorted, int target) {
        int left = 0;
        int right = sorted.length - 1;

        while (left < right) {
            int sum = sorted[left] + sorted[right];

            if (sum == target) {
                return true;
            }
            if (sum < target) {
                left++;
            } else {
                right--;
            }
        }
        return false;
    }
}
```

핵심은 "포인터를 어느 쪽으로 움직이면 남은 후보 집합을 안전하게 줄일 수 있는가"다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Same-direction two-pointer | 연속 구간을 선형으로 훑기 좋다 | 사실상 sliding window 설계가 필요하다 | subarray, substring |
| Opposite-direction two-pointer | 정렬 배열의 pair 관계 문제에 강하다 | 정렬이 없으면 전처리 비용이 든다 | pair sum, palindrome, 양끝 비교 |
| LIS / Subsequence Optimization | skip allowed 문제를 직접 다룬다 | pair relation scan에는 맞지 않는다 | LIS, subsequence, order preserving |
| Binary Search | 경계 탐색에 강하다 | 단조 조건이 없으면 못 쓴다 | 최소 가능값, 최대 허용치, first true |
| Hash 기반 탐색 | 정렬 없이도 빠를 수 있다 | 공간이 더 든다 | unsorted two-sum, membership check |

## 꼬리질문

> Q: sliding window와 two-pointer는 같은가?
> 의도: 상위/하위 패턴 관계를 구분하는지 확인
> 핵심: sliding window는 two-pointer의 하위 패턴이다.

> Q: 두 포인터는 정렬이 꼭 필요한가?
> 의도: 적용 조건 감각 확인
> 핵심: opposite-direction은 정렬이 자주 필요하지만, same-direction window는 연속 구간만 있으면 가능하다.

> Q: pair sum 문제를 왜 binary search보다 two-pointer로 푸나요?
> 의도: 패턴 선택 이유 확인
> 핵심: 정렬 배열에서는 한 번의 선형 스캔으로 후보를 줄일 수 있기 때문이다.

> Q: `subsequence`가 보이면 무조건 two-pointer인가?
> 의도: subsequence membership와 LIS 최적화를 구분하는지 확인
> 핵심: 단순 포함 검사면 same-direction two-pointer가 가능하지만, skip을 최적화하는 LIS류는 다른 문제다.

## 한 줄 정리

두 포인터는 두 인덱스의 관계를 조정해 후보를 줄이는 상위 패턴이고, 연속 구간이면 sliding window, skip allowed 최적화면 subsequence/LIS, 단조 경계면 binary search로 갈라진다.
