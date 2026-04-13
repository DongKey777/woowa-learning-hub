# Sparse Table

> 한 줄 요약: Sparse Table은 변경이 없는 배열에서 idempotent 구간 질의를 O(1)로 처리하기 위해 미리 2^k 길이 결과를 쌓아두는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Segment Tree Lazy Propagation](./segment-tree-lazy-propagation.md)
> - [Fenwick Tree (Binary Indexed Tree)](./fenwick-tree.md)
> - [Binary Search Patterns](../algorithm/binary-search-patterns.md)

> retrieval-anchor-keywords: sparse table, rmq, range minimum query, static query, idempotent operation, rmq preprocessing, query o1, binary lifting style table, static array, min/max/gcd

## 핵심 개념

Sparse Table은 배열이 바뀌지 않는 조건에서, 구간 질의를 빠르게 처리하기 위한 전처리 구조다.

특히 다음처럼 **idempotent** 연산에 잘 맞는다.

- min
- max
- gcd

idempotent는 `f(x, x) = x`가 성립하는 연산이다.  
이 성질 덕분에 같은 구간을 겹쳐서 보더라도 결과가 깨지지 않는다.

## 깊이 들어가기

### 1. 왜 static 전용인가

Sparse Table은 전처리가 무겁지만, 질의는 아주 빠르다.

- build: `O(n log n)`
- query: `O(1)`

대신 값이 바뀌면 다시 쌓아야 한다.  
즉 자주 갱신되는 배열에는 맞지 않는다.

### 2. 2^k 구간을 쌓는 이유

`st[k][i]`는 `i`에서 시작하는 길이 `2^k` 구간의 답을 저장한다.

- `st[0][i]`: 길이 1
- `st[1][i]`: 길이 2
- `st[2][i]`: 길이 4

이렇게 하면 구간을 두 개의 겹치는 블록으로 덮어 질의를 빠르게 계산할 수 있다.

### 3. 왜 O(1) 질의가 가능한가

`[l, r]` 구간 길이를 `2^k` 두 개로 덮는다.

- 왼쪽 블록: `st[k][l]`
- 오른쪽 블록: `st[k][r - 2^k + 1]`

idempotent 연산은 겹쳐도 괜찮으므로 두 결과를 합치면 된다.

### 4. backend에서의 활용

Sparse Table은 실시간 업데이트보다 읽기 중심 환경에서 좋다.

- 기준 데이터셋의 구간 최소/최대
- 설정값 히스토리의 정적 조회
- 통계 리포트용 read-heavy 분석

## 실전 시나리오

### 시나리오 1: RMQ

구간 최솟값을 많이 묻는다면 sparse table이 매우 강하다.

### 시나리오 2: GCD range

서버별 샘플이나 주기 데이터에서 구간 gcd를 반복 조회할 때 유용하다.

### 시나리오 3: 오판

업데이트가 자주 있으면 sparse table은 부적합하다.  
이때는 세그먼트 트리나 펜윅 트리를 생각해야 한다.

### 시나리오 4: binary lifting과 닮은 점

둘 다 2^k 단위 전처리를 쌓지만, 목적이 다르다.

- Binary lifting: 트리 상 점프
- Sparse table: 배열 구간 질의

## 코드로 보기

```java
public class SparseTable {
    private final int[][] st;
    private final int[] log;

    public SparseTable(int[] arr) {
        int n = arr.length;
        this.log = new int[n + 1];
        for (int i = 2; i <= n; i++) {
            log[i] = log[i / 2] + 1;
        }

        int k = log[n] + 1;
        this.st = new int[k][n];
        System.arraycopy(arr, 0, st[0], 0, n);

        for (int j = 1; j < k; j++) {
            for (int i = 0; i + (1 << j) <= n; i++) {
                st[j][i] = Math.min(st[j - 1][i], st[j - 1][i + (1 << (j - 1))]);
            }
        }
    }

    public int rangeMin(int l, int r) {
        int j = log[r - l + 1];
        return Math.min(st[j][l], st[j][r - (1 << j) + 1]);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Sparse Table | 질의가 O(1)이라 매우 빠르다 | 업데이트가 비싸다 | 정적 구간 질의 |
| Segment Tree | 업데이트와 질의를 모두 지원한다 | 구현이 더 복잡하다 | 동적 배열 |
| Fenwick Tree | 메모리가 작고 간단하다 | idempotent 범위 질의에는 덜 일반적이다 | 누적합/빈도 중심 |

Sparse Table은 "읽기 전용 구간 질의의 고속 캐시"로 보면 이해가 쉽다.

## 꼬리질문

> Q: 왜 min/max/gcd에 잘 맞나?
> 의도: idempotent 성질 이해 확인
> 핵심: 구간을 겹쳐 덮어도 결과가 변하지 않기 때문이다.

> Q: 업데이트가 있으면 왜 안 되나?
> 의도: static 전용 구조 이해 확인
> 핵심: 전처리를 다시 해야 하므로 이점이 사라진다.

> Q: binary lifting과 뭐가 다른가?
> 의도: 2^k 전처리의 맥락 구분 확인
> 핵심: 하나는 트리 점프, 다른 하나는 배열 구간 질의다.

## 한 줄 정리

Sparse Table은 변경 없는 배열에서 idempotent 구간 질의를 O(1)로 처리하는 정적 전처리 자료구조다.
