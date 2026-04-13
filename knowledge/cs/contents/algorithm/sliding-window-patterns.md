# Sliding Window Patterns

> 한 줄 요약: 연속 구간을 유지하면서 조건을 만족하는 답을 찾는 문제를 푸는 대표 패턴이다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [두 포인터 (two-pointer)](./two-pointer.md)
> - [시간복잡도와 공간복잡도](./basic.md#시간복잡도와-공간복잡도)

## 핵심 개념

슬라이딩 윈도우는 연속된 구간 `[left, right]`를 유지하면서 조건을 만족하도록 창을 밀어가는 방식이다.

주로 다음 문제에서 나온다.

- 최대/최소 길이의 부분 문자열
- 합/개수 조건을 만족하는 구간
- 중복 문자를 피하는 구간
- 고정 길이 평균/최대값

핵심은 매번 처음부터 다시 보지 않고, 이전 상태를 재사용하는 것이다.

## 깊이 들어가기

### 1. 고정 크기 윈도우

윈도우 크기가 정해져 있으면 추가되는 원소와 빠지는 원소만 갱신하면 된다.

예:

- 길이 K인 구간 합
- 길이 K인 구간 최대 빈도

### 2. 가변 크기 윈도우

조건이 만족되지 않으면 `left`를 당겨서 윈도우를 줄이고, 만족하면 `right`를 늘린다.

예:

- 합이 S 이상인 최소 길이 구간
- 중복 없는 가장 긴 부분 문자열

### 3. 카운트/빈도 배열이 자주 쓰이는 이유

윈도우 안의 상태를 빠르게 갱신하려면

- `Set`
- `Map`
- `int[] freq`

중 하나가 필요하다.

문자열 문제는 보통 `freq` 배열이 가장 빠르다.

---

## 실전 시나리오

### 시나리오 1: 중복 없는 가장 긴 부분 문자열

문자 하나씩만 보면서 `left`를 조정하면 O(n)으로 풀 수 있다.
매번 전체 구간을 다시 검사하면 O(n^2)가 된다.

### 시나리오 2: 최근 요청 집계

최근 5분 동안의 요청 수 같은 실시간 통계는 고정 크기 윈도우로 풀기 좋다.

---

## 코드로 보기

```java
import java.util.HashMap;
import java.util.Map;

public class SlidingWindow {
    public int lengthOfLongestSubstring(String s) {
        Map<Character, Integer> lastSeen = new HashMap<>();
        int left = 0;
        int answer = 0;

        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            if (lastSeen.containsKey(c)) {
                left = Math.max(left, lastSeen.get(c) + 1);
            }
            lastSeen.put(c, right);
            answer = Math.max(answer, right - left + 1);
        }
        return answer;
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Sliding Window | 연속 구간을 O(n)으로 처리 가능 | 조건 설계가 익숙하지 않으면 실수하기 쉽다 | substring, subarray, interval 문제 |
| Prefix Sum | 구간 합 계산이 쉽다 | 조건에 따라 윈도우처럼 못 쓸 수 있다 | 합 기반의 빠른 질의 |
| Brute Force | 구현이 쉽다 | 거의 항상 느리다 | 검증용 |
| Deque | 윈도우 최대/최소에 강하다 | 개념이 더 복잡하다 | monotonic queue 문제 |

핵심 판단 기준은 "연속 구간을 유지하면서 점진적으로 갱신할 수 있는가"다.

---

## 꼬리질문

> Q: 언제 sliding window를 쓰면 안 되는가?
> 의도: 패턴 남용 여부 확인
> 핵심: 조건이 단조롭지 않거나 연속 구간이 아닌 경우다.

> Q: two-pointer와 sliding window는 같은가?
> 의도: 패턴의 미묘한 차이를 보는가
> 핵심: two-pointer는 더 넓은 개념이고 sliding window는 그 하위 패턴이다.

> Q: 왜 문자열 문제에서 자주 등장하는가?
> 의도: 패턴 인식 능력 확인
> 핵심: 연속성, 중복 제어, 길이 최적화가 자주 함께 나오기 때문이다.

## 한 줄 정리

Sliding window는 연속 구간 상태를 재사용해서, 부분 문자열/부분 배열 문제를 선형 시간에 푸는 패턴이다.
