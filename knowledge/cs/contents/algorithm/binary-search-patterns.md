# Binary Search Patterns

> 한 줄 요약: 이분 탐색은 "정렬된 배열에서 값 찾기"가 아니라, `조건이 처음 참이 되는 지점`을 빠르게 찾는 패턴이다.

**난이도: 🟡 Intermediate**

> 관련 문서: [알고리즘 기본](./basic.md)

---

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

