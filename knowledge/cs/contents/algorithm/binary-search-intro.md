# 이분 탐색 입문 (Binary Search Basics)

> 한 줄 요약: 이분 탐색은 정렬된 배열에서 탐색 범위를 매 단계 절반으로 줄여 O(log n)에 답을 찾는 기법이며, "정확한 값 찾기"와 "조건을 만족하는 경계 찾기" 두 가지 패턴을 구분해서 쓴다.

**난이도: 🟢 Beginner**

관련 문서:

- [이분 탐색 패턴](./binary-search-patterns.md)
- [정렬 알고리즘 비교 심화](./sort.md)
- [algorithm 카테고리 인덱스](./README.md)
- [트리 기초](../data-structure/tree-basics.md)

retrieval-anchor-keywords: binary search intro, 이분 탐색 입문, 이진 탐색 기초, binary search beginner, 이분 탐색이 뭐예요, 정렬된 배열 탐색, log n 탐색, lo hi mid, binary search lo hi, lower bound beginner, upper bound beginner, 경계 이분 탐색, off by one binary search, binary search loop condition, binary search intro basics

## 핵심 개념

이분 탐색은 **정렬된 배열**에서 원하는 값을 찾는 방법이다. 매 단계에서 중간값과 목표값을 비교해 오른쪽 절반 또는 왼쪽 절반을 버린다. n개의 배열을 선형 탐색하면 O(n)이지만 이분 탐색을 쓰면 O(log n)으로 줄어든다.

입문자가 가장 많이 틀리는 부분은 **종료 조건과 경계 처리**다. `lo <= hi`와 `lo < hi`는 탐색 패턴에 따라 다르게 쓰이며, 하나만 외우면 다른 패턴에서 off-by-one 오류가 생긴다.

## 한눈에 보기

```
배열: [1, 3, 5, 7, 9, 11], target = 7
lo=0, hi=5, mid=2 → arr[2]=5 < 7 → lo=3
lo=3, hi=5, mid=4 → arr[4]=9 > 7 → hi=3
lo=3, hi=3, mid=3 → arr[3]=7 = 7 → 찾음!
```

| 패턴 | 목적 | 종료 조건 예시 |
|---|---|---|
| 정확한 값 탐색 | target이 존재하는 index 반환 | lo <= hi |
| Lower Bound | target 이상인 첫 번째 위치 | lo < hi |
| Upper Bound | target 초과인 첫 번째 위치 | lo < hi |

## 상세 분해

- **mid 계산**: `mid = (lo + hi) / 2`는 `lo + hi`가 int 최댓값을 초과할 수 있다. `mid = lo + (hi - lo) / 2`가 안전하다.
- **정확한 값 탐색**: `arr[mid] == target`이면 반환, 작으면 `lo = mid + 1`, 크면 `hi = mid - 1`. 루프 종료 후 못 찾으면 -1 반환.
- **Lower Bound**: `arr[mid] < target`이면 `lo = mid + 1`, 아니면 `hi = mid`. 루프 종료 시 `lo`가 첫 번째 target 위치.
- **전제 조건은 정렬**: 배열이 정렬되지 않으면 이분 탐색 결과가 보장되지 않는다.

## 흔한 오해와 함정

- "이분 탐색은 배열에서만 쓴다" → 틀리다. "조건을 만족하는 최솟값/최댓값 찾기" 형태의 문제에도 답의 범위에 이분 탐색을 쓸 수 있다.
- `lo <= hi`를 항상 쓰면 된다고 외우면 Lower Bound 패턴에서 무한 루프가 날 수 있다.
- `hi = mid - 1`과 `hi = mid`를 섞어 쓰면 탐색 범위가 수렴하지 않는다. 패턴을 하나로 통일해야 한다.
- 정수 배열만 해당된다고 생각하는 경우가 있지만, 실수 범위 이분 탐색도 가능하다(오차 범위로 종료).

## 실무에서 쓰는 모습

1. **정렬된 DB 인덱스 탐색**: B-Tree 인덱스의 범위 검색이 이분 탐색 원리로 동작한다. `WHERE age >= 25 AND age < 30` 같은 쿼리는 Lower Bound → Upper Bound 범위다.
2. **결정 문제로 변환**: "용량 C 이하의 배에 화물을 나눠 실을 때 최소 배 수는?"처럼 답 범위가 단조 증가할 때, 배 수 x에 대해 "가능한가"를 O(n) 검사하고 x에 이분 탐색을 걸면 O(n log n)으로 해결된다.

## 더 깊이 가려면

- Lower Bound / Upper Bound 응용 패턴과 결정 문제 이분 탐색은 [이분 탐색 패턴](./binary-search-patterns.md)
- 정렬 후 이분 탐색 파이프라인의 복잡도 분석은 [정렬 알고리즘 비교 심화](./sort.md)

## 면접/시니어 질문 미리보기

- "이분 탐색이 O(log n)인 이유는?" → 매 단계에서 탐색 범위가 절반이 되므로 최대 log₂n번 비교한다.
- "Lower Bound와 Upper Bound의 차이는?" → Lower Bound는 target 이상의 첫 인덱스, Upper Bound는 target 초과의 첫 인덱스. 둘의 차이가 배열 안의 target 개수다.
- "이분 탐색을 쓸 수 없는 경우는?" → 정렬되지 않은 배열, 또는 비교 함수가 단조성을 만족하지 않는 경우.

## 한 줄 정리

이분 탐색은 정렬된 구조에서 O(log n)으로 답을 찾는 기법이며, "정확한 값"과 "경계(Lower/Upper Bound)" 두 패턴의 종료 조건 차이를 구분하는 것이 핵심이다.
