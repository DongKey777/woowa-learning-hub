# Monotonic Queue and Stack

> 한 줄 요약: 단조 스택/큐는 "현재까지 본 값 중 의미 없는 값을 버리는" 방식으로 최적 후보를 빠르게 유지하는 자료구조다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [자료구조 정리](./README.md)
> - [Sliding Window 패턴](../algorithm/sliding-window-patterns.md)
> - [Deque](./advanced.md)

## 핵심 개념

단조 스택(monotonic stack)과 단조 큐(monotonic queue)는 원소를 **오름차순 또는 내림차순으로 유지**하면서, 매 시점마다 최댓값/최솟값 후보만 남기는 구조다.

- 단조 증가 스택: 스택 top부터 아래로 갈수록 값이 증가하거나 감소하는 형태를 유지한다.
- 단조 큐: 슬라이딩 윈도우에서 구간의 최댓값/최솟값을 O(1)에 가까운 비용으로 얻기 위해 사용한다.

핵심은 "들어온 원소보다 쓸모없는 원소는 뒤에서 제거한다"는 점이다.  
이렇게 하면 각 원소는 최대 한 번 들어오고 한 번 나가므로 전체 시간복잡도는 보통 O(n)이다.

## 깊이 들어가기

### 1. 왜 필요한가

정렬된 후보만 유지하면 다음 두 작업이 쉬워진다.

- 현재까지의 최댓값 또는 최솟값을 즉시 얻는다.
- 오래된 원소나 더 나쁜 후보를 빠르게 버린다.

이 구조는 다음 문제군에 자주 나온다.

- 슬라이딩 윈도우 최댓값/최솟값
- 다음 큰 수 / 이전 큰 수
- 히스토그램 최대 직사각형
- 주가, 온도, 점수처럼 "최근 구간의 극값"이 필요한 경우

### 2. 스택과 큐의 차이

단조 스택은 보통 "다음 큰 수"처럼 한 번 훑는 문제에 맞고,  
단조 큐는 "고정 길이 구간"을 이동시키는 슬라이딩 윈도우에 맞다.

큐는 front에서만 오래된 원소를 제거하고,  
스택은 top에서만 후보를 제거한다.

### 3. 시간복잡도 감각

겉보기에는 while pop이 여러 번 일어나서 느려 보이지만, 각 원소는 한 번만 push되고 한 번만 pop된다.

즉 상각 분석으로 보면 O(n)이다.

이 점은 [상각 분석과 복잡도 함정](../algorithm/amortized-analysis-pitfalls.md)과 같이 보면 더 잘 보인다.

## 실전 시나리오

### 시나리오 1: 슬라이딩 윈도우 최대값

길이 k의 윈도우를 한 칸씩 밀면서 최대값을 구해야 한다면, 매번 O(k)로 훑는 방식은 O(nk)로 너무 느리다.

단조 큐는 아래 규칙을 쓴다.

1. 새 값이 들어오면 뒤에서 자신보다 작은 값들을 제거한다.
2. 윈도우 밖으로 나간 값이 front에 있으면 제거한다.
3. front가 현재 윈도우의 최댓값이다.

### 시나리오 2: 다음 큰 수

배열을 왼쪽에서 오른쪽으로 보면서, 현재 값보다 작은 값은 앞으로도 답이 될 수 없다.  
이때 단조 스택은 작은 후보를 밀어내고, 다음 더 큰 값이 등장했을 때 바로 답을 확정한다.

## 코드로 보기

### 슬라이딩 윈도우 최대값

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.ArrayList;
import java.util.List;

public class SlidingWindowMax {
    public List<Integer> maxSlidingWindow(int[] nums, int k) {
        Deque<Integer> deque = new ArrayDeque<>(); // index 저장
        List<Integer> result = new ArrayList<>();

        for (int i = 0; i < nums.length; i++) {
            while (!deque.isEmpty() && nums[deque.peekLast()] <= nums[i]) {
                deque.pollLast();
            }
            deque.offerLast(i);

            if (deque.peekFirst() <= i - k) {
                deque.pollFirst();
            }

            if (i >= k - 1) {
                result.add(nums[deque.peekFirst()]);
            }
        }
        return result;
    }
}
```

### 다음 큰 수

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Arrays;

public class NextGreaterElement {
    public int[] solve(int[] arr) {
        int[] answer = new int[arr.length];
        Arrays.fill(answer, -1);
        Deque<Integer> stack = new ArrayDeque<>(); // index 저장

        for (int i = 0; i < arr.length; i++) {
            while (!stack.isEmpty() && arr[stack.peek()] < arr[i]) {
                answer[stack.pop()] = arr[i];
            }
            stack.push(i);
        }
        return answer;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단조 스택 | 구현이 단순하고 다음/이전 원소 문제에 강함 | 윈도우 만료 처리에는 부적합 | 다음 큰 수, 히스토그램 |
| 단조 큐 | 슬라이딩 윈도우 극값에 강함 | 인덱스 만료 처리를 신경써야 함 | 구간 최대/최소 |
| 우선순위 큐 | 구현이 쉽고 최대/최소 추출이 직관적 | 오래된 원소 제거가 번거롭고 O(log n) | 윈도우가 크고 구현 우선 |

## 꼬리질문

> Q: 단조 큐와 우선순위 큐 중 무엇이 더 좋은가?
> 의도: 문제의 구조를 보고 자료구조를 선택할 수 있는지 확인
> 핵심: 삭제가 "오래된 원소" 중심이면 단조 큐가 유리하고, 단순 추출이면 우선순위 큐도 가능하다.

> Q: 왜 while pop이 많은데도 O(n)인가?
> 의도: 상각 분석 이해 여부 확인
> 핵심: 각 원소는 한 번만 삽입되고 한 번만 제거되기 때문이다.

## 한 줄 정리

단조 스택/큐는 "쓸모없는 후보를 미리 제거"해서 극값이나 다음 후보를 빠르게 찾는 O(n) 상각 구조다.
