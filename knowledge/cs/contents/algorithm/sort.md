# 정렬 알고리즘의 종류와 개념

> 작성자 : [장주섭](https://github.com/wntjq68), [이세명](https://github.com/3people)

> 한 줄 요약: 정렬은 단순히 "순서를 맞추는 작업"이 아니라, 검색, 순위, 중복 제거, 범위 질의의 전처리 기반이 되는 핵심 패턴이다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **대표 정렬 알고리즘 비교와 stable / unstable, comparison / non-comparison 구분**을 빠르게 잡는 primer다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [시간복잡도와 공간복잡도](./basic.md#시간복잡도와-공간복잡도)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [두 포인터 (two-pointer)](./two-pointer.md)
> - [Interval Greedy Patterns](./interval-greedy-patterns.md)
> - [Sweep Line Overlap Counting](./sweep-line-overlap-counting.md)
> - [Disjoint Interval Set](../data-structure/disjoint-interval-set.md)
> - [Interval Tree](../data-structure/interval-tree.md)
> - [Heap Variants](../data-structure/heap-variants.md)
>
> retrieval-anchor-keywords: sorting algorithm comparison, insertion sort, selection sort, bubble sort, merge sort, quick sort, heap sort, counting sort, radix sort, stable sort, unstable sort, in-place sort, comparison sort, non-comparison sort, merge sort vs quick sort, sorting as preprocessing, sorted array preprocessing, binary search preprocessing, start time sort, end time sort, interval preprocessing, interval comparator, merge intervals, insert interval, interval merge, batch interval merge, offline interval merge, event sort boundary

<details>
<summary>Table of Contents</summary>

- [Insertion Sort (삽입정렬)](#insertion-sort-삽입정렬)
- [Selection Sort (선택정렬)](#selection-sort-선택정렬)
- [Bubble Sort (거품정렬)](#bubble-sort-거품정렬)
- [Merge Sort (합병정렬)](#merge-sort-합병정렬)
- [Quick Sort (퀵정렬)](#quick-sort-퀵정렬)
- [Quick Sort vs Merge Sort](#quick-sort-vs-merge-sort)
- [Heap, Radix, Counting Sort](#heap-radix-counting-sort)

</details>

---

## 이 문서 다음에 보면 좋은 문서

- 정렬된 배열에서 경계 탐색으로 이어지는 흐름은 [Binary Search Patterns](./binary-search-patterns.md)이 가장 가깝다.
- 정렬 후 양끝 포인터나 pair 관계를 줄이는 문제는 [두 포인터 (two-pointer)](./two-pointer.md)와 함께 보면 연결이 선명해진다.
- `merge intervals`, `insert interval`, `구간 병합`처럼 정렬 후 한 번 훑어 붙이는 문제는 아래 [정렬 전처리로 구간 문제 읽기](#정렬-전처리로-구간-문제-읽기)와 [Interval Greedy Patterns](./interval-greedy-patterns.md)을 같이 보면 경계가 빨리 잡힌다.
- "무엇으로 정렬해야 최적이 되는가"가 핵심인 문제는 [Interval Greedy Patterns](./interval-greedy-patterns.md)로 이어진다.
- heap sort를 우선순위 큐 관점에서 다시 보고 싶다면 [Heap Variants](../data-structure/heap-variants.md)가 좋다.

정렬은 코딩테스트에서 가장 먼저 배우지만, 실무에서는 의외로 "정렬 그 자체"보다 "정렬을 왜 해야 하는가"가 더 중요하다.

- 검색 결과를 순서대로 보여주기 위해
- 순위표를 만들기 위해
- 중복을 제거하고 그룹화하기 위해
- 구간 질의를 쉽게 하기 위해

즉 정렬은 단순한 알고리즘이 아니라, 더 큰 문제를 풀기 위한 전처리 단계다.  
관련해서 [Binary Search Patterns](./binary-search-patterns.md), [Interval Greedy Patterns](./interval-greedy-patterns.md), [Topological Sort Patterns](./topological-sort-patterns.md)도 함께 보면 좋다.

---

## 정렬 전처리로 구간 문제 읽기

구간 문제는 전부 "일단 정렬"처럼 보이지만, **무엇을 기준으로 정렬한 뒤 어떤 상태를 유지하느냐**에 따라 라우트가 완전히 달라진다.

| 질문 표현 | 정렬 / 유지 상태 | 먼저 볼 문서 | 왜 여기서 갈리나 |
|---|---|---|---|
| `merge intervals`, `insert interval`, `구간 병합` | 시작점 기준 정렬 + 현재 merge tail | [Interval Greedy Patterns](./interval-greedy-patterns.md), [Disjoint Interval Set](../data-structure/disjoint-interval-set.md) | 비겹침 선택이 아니라 겹치는 구간을 합친다. 한 번만 처리하면 sort pass고, 계속 들어오면 disjoint set 쪽이다 |
| `activity selection`, `erase overlap intervals`, `meeting rooms I` | 끝점 기준 정렬 + 마지막 선택 end | [Interval Greedy Patterns](./interval-greedy-patterns.md) | 미래 선택 공간을 최대화해야 해서 earliest-finish 기준이 핵심이다 |
| `meeting rooms II`, `minimum meeting rooms`, `max concurrency` | 시작/끝 이벤트 정렬 + active count | [Sweep Line Overlap Counting](./sweep-line-overlap-counting.md) | 어떤 interval을 남길지가 아니라 동시에 몇 개가 겹치는지를 센다 |
| `calendar booking`, `online reservation insert`, `insert interval then query` | 정렬 결과를 매번 다시 만들지 않고 insert/query 상태 유지 | [Disjoint Interval Set](../data-structure/disjoint-interval-set.md), [Interval Tree](../data-structure/interval-tree.md) | 정적 batch가 아니라 동적 workload라서 "정렬 후 한 번 스캔"으로 끝나지 않는다 |

- LeetCode식 `insert interval`처럼 새 구간 하나를 기존 목록에 넣고 **이번 입력에서만** merge하면 batch merge 쪽으로 읽는다.
- 예약 API처럼 새 구간이 계속 들어오고 매번 `겹치나?`, `넣어도 되나?`를 물으면 정렬 문제가 아니라 자료구조 라우트로 넘긴다.

---

## Insertion Sort (삽입정렬)

삽입정렬은 앞에서부터 보면서 현재 원소를 이미 정렬된 부분에 끼워 넣는 방식이다.  
작은 데이터, 거의 정렬된 데이터, 온라인 입력에 강하다.

### Example

> 28 13 23 25 19 : 초기 배열
>
> 28 **13** 23 25 19 : 13을 왼쪽 정렬 구간에 삽입
>
> 13 28 **23** 25 19 : 23을 올바른 위치에 삽입
>
> 13 23 28 **25** 19 : 25를 삽입
>
> 13 23 25 28 **19** : 19를 삽입
>
> 13 19 23 25 28 : 정렬 완료

### 시간복잡도

- Best: O(n)
- Average: O(n^2)
- Worst: O(n^2)

### Source Code

```java
void insertionSort(int[] arr) {
    for (int index = 1; index < arr.length; index++) {
        int temp = arr[index];
        int aux = index - 1;

        while (aux >= 0 && arr[aux] > temp) {
            arr[aux + 1] = arr[aux];
            aux--;
        }
        arr[aux + 1] = temp;
    }
}
```

### 실전 감각

- 거의 정렬된 배열에서 매우 빠르다.
- 작은 배치에서 오버헤드가 적다.
- 온라인으로 들어오는 데이터의 유지 정렬에 자주 쓰인다.

### 장점

- 구현이 쉽다.
- 안정 정렬이다.
- 부분 정렬 상태에서 효율적이다.

### 단점

- 데이터가 많고 무작위면 느리다.

---

## Selection Sort (선택정렬)

선택정렬은 매번 최솟값을 골라 앞에 두는 방식이다.  
단순하지만 비교 횟수가 많아 실전에서는 잘 안 쓴다.

### Example

> 28 13 23 25 19 : 초기 배열
>
> 13 28 23 25 19 : 최솟값 13을 앞으로
>
> 13 19 23 25 28 : 다음 최솟값 19를 앞으로
>
> 13 19 23 25 28 : 정렬 완료

### 시간복잡도

- Best: O(n^2)
- Average: O(n^2)
- Worst: O(n^2)

### Source Code

```java
void selectionSort(int[] list) {
    int indexMin, temp;

    for (int i = 0; i < list.length - 1; i++) {
        indexMin = i;
        for (int j = i + 1; j < list.length; j++) {
            if (list[j] < list[indexMin]) {
                indexMin = j;
            }
        }
        temp = list[indexMin];
        list[indexMin] = list[i];
        list[i] = temp;
    }
}
```

### 실전 감각

- swap 횟수를 줄이고 싶을 때 설명용으로 좋다.
- 비교는 많지만 교환은 적다.
- 배치 작업에서 "최솟값 선택" 사고방식을 익힐 때 유용하다.

### 장점

- 교환 횟수가 적다.
- 구현이 단순하다.

### 단점

- 항상 비효율적이다.
- 안정 정렬이 아니다.

---

## Bubble Sort (거품정렬)

거품정렬은 인접한 두 원소를 계속 비교해 큰 값을 뒤로 보내는 방식이다.  
가장 교육적인 정렬이지만, 실무에서는 거의 사용하지 않는다.

### Example

> 28 13 23 25 19 : 시작
>
> 13 23 25 19 28 : 첫 pass 후 최대값이 뒤로 감
>
> 13 23 19 25 28 : 다음 pass
>
> 13 19 23 25 28 : 완료

### 시간복잡도

- Best: O(n) with early stop
- Average: O(n^2)
- Worst: O(n^2)

### Source Code

```java
void bubbleSort(int[] arr) {
    for (int i = 0; i < arr.length; i++) {
        boolean swapped = false;
        for (int j = 1; j < arr.length - i; j++) {
            if (arr[j] < arr[j - 1]) {
                int temp = arr[j - 1];
                arr[j - 1] = arr[j];
                arr[j] = temp;
                swapped = true;
            }
        }
        if (!swapped) break;
    }
}
```

### 실전 감각

- 교육용으로는 좋다.
- 이미 정렬된 상태를 감지하는 early stop 아이디어를 보여준다.

### 장점

- 이해하기 쉽다.
- swap이 적으면 빠르게 끝날 수 있다.

### 단점

- 너무 느리다.
- 실무에서 쓸 이유가 거의 없다.

---

## Merge Sort (합병정렬)

합병정렬은 분할 정복의 대표격이다.  
항상 `O(n log n)`을 보장하고 안정 정렬이 가능하다는 점이 강점이다.

### Example

큰 배열을 절반으로 나누고, 다시 나누고, 각 부분을 정렬한 뒤 합친다.

### 시간복잡도

- Average: O(n log n)
- Worst: O(n log n)

### Source Code

```java
void mergeSort(int[] arr, int start, int end) {
    if (start < end) {
        int mid = (start + end) / 2;
        mergeSort(arr, start, mid);
        mergeSort(arr, mid + 1, end);
        merge(arr, start, mid, end);
    }
}

void merge(int[] arr, int start, int mid, int end) {
    int i = start;
    int j = mid + 1;
    int k = 0;

    int[] temp = new int[end - start + 1];
    while (i <= mid && j <= end) {
        if (arr[i] < arr[j]) {
            temp[k++] = arr[i++];
        } else {
            temp[k++] = arr[j++];
        }
    }

    while (i <= mid) temp[k++] = arr[i++];
    while (j <= end) temp[k++] = arr[j++];

    for (int idx = 0; idx < temp.length; idx++) {
        arr[start + idx] = temp[idx];
    }
}
```

### 장점

- 안정 정렬이다.
- 최악에도 성능이 일정하다.
- 외부 정렬, linked list 정렬, 병렬 처리와 잘 맞는다.

### 단점

- 추가 메모리가 필요하다.
- 작은 배열에서는 오버헤드가 크다.

### backend angle

대규모 로그를 정렬하거나, 외부 저장소에서 chunk를 병합할 때 merge sort의 사고방식이 그대로 쓰인다.  
결국 "나누고, 정렬하고, 합친다"는 구조는 분산 처리에도 잘 맞는다.

---

## Quick Sort (퀵정렬)

퀵정렬은 pivot을 기준으로 작은 값과 큰 값을 나누며 재귀적으로 정렬하는 방식이다.  
평균적으로 매우 빠르고, in-place라서 실무 구현에서도 자주 본다.

### Example

> 3 7 6 5 1 4 2 : 초기 배열
>
> pivot = 3
>
> 1 2 **3** 5 6 4 7 : pivot 기준 분할
>
> ... recursive ...

### 시간복잡도

- Average: O(n log n)
- Worst: O(n^2)

### Source Code

```java
void quickSort(int[] arr, int start, int end) {
    if (start < end) {
        int p = partition(arr, start, end);
        quickSort(arr, start, p - 1);
        quickSort(arr, p + 1, end);
    }
}

int partition(int[] arr, int start, int end) {
    int low = start + 1;
    int high = end;
    int pivot = arr[start];

    while (low <= high) {
        while (low <= end && arr[low] < pivot) low++;
        while (high >= start && arr[high] > pivot) high--;
        if (low < high) swap(arr, low, high);
    }
    swap(arr, start, high);
    return high;
}

void swap(int[] arr, int i, int j) {
    int temp = arr[j];
    arr[j] = arr[i];
    arr[i] = temp;
}
```

### 장점

- 평균적으로 매우 빠르다.
- 추가 메모리가 거의 필요 없다.
- 캐시 친화적일 수 있다.

### 단점

- pivot 선택이 나쁘면 최악의 성능이 나온다.
- 안정 정렬이 아니다.

### backend angle

정렬 라이브러리나 데이터 프레임의 내부 구현에서 quicksort류의 partition 사고방식은 매우 중요하다.  
실무에서는 median-of-three, random pivot, introsort처럼 최악 케이스 완화 전략을 같이 고려한다.

---

## Quick Sort vs Merge Sort

두 알고리즘 모두 평균 `O(n log n)`이지만, 선택 기준은 시간복잡도 표기만으로 끝나지 않는다.

| 관점 | Quick Sort | Merge Sort |
|---|---|---|
| 평균 속도 | 빠른 편 | 안정적 |
| 최악 시간 | O(n^2) | O(n log n) |
| 메모리 | 적음 | 추가 배열 필요 |
| 안정성 | 보통 아님 | 안정적 |
| 실전 적합성 | in-place 정렬에 좋음 | 대량 병합/외부 정렬에 좋음 |

### 실전 판단

- 메모리가 빡빡하면 quick sort 계열을 본다.
- 안정성이 중요하면 merge sort를 본다.
- 이미 거의 정렬되어 있으면 pivot 전략을 신경 써야 한다.

### backend angle

실무에서 중요한 건 "이론상 최악"뿐 아니라 "데이터 분포"다.  
로그처럼 거의 정렬된 입력, 랜덤 입력, 중복이 많은 입력에 따라 성능 체감이 달라진다.

---

## Heap, Radix, Counting Sort

정렬은 비교만으로 끝나지 않는다.  
데이터 성질에 따라 비교하지 않고 더 빨리 정렬하는 방법도 있다.

- [Heap Sort](../data-structure/heap-variants.md) 개념은 우선순위 큐와 연결된다.
- Radix Sort는 자리수 기반 정렬이다.
- Counting Sort는 값의 범위가 작을 때 매우 빠르다.

### 비교 기준

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Heap Sort | in-place, worst-case 안정 | 상수 비용이 크다 | 메모리 절약 필요 |
| Radix Sort | 비교를 줄일 수 있다 | 키 형식 제약이 있다 | 정수/문자열 키 |
| Counting Sort | 매우 빠르다 | 범위가 작아야 한다 | 제한된 값 범위 |
| Comparison Sort | 범용적이다 | `O(n log n)` 한계 | 일반적인 정렬 |

### backend angle

실무에서는 "정렬 알고리즘"보다 "정렬의 전제 조건"을 먼저 본다.

- 값 범위가 작나?
- 안정성이 필요하나?
- 메모리가 제한적인가?
- 전체 정렬이 필요한가, top-k만 필요한가?

이 질문에 답하면 sort 선택이 훨씬 쉬워진다.

---

## 한 줄 정리

정렬은 알고리즘의 끝이 아니라 전처리의 시작이며, 데이터 성질과 시스템 제약에 따라 알맞은 정렬 방식을 고르는 것이 핵심이다.
