# Fenwick Tree vs Segment Tree

> 한 줄 요약: Fenwick Tree는 점 갱신과 누적합에 가볍고, Segment Tree는 더 넓은 범위 연산과 유연성에서 강하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Fenwick Tree (Binary Indexed Tree)](./fenwick-tree.md)
> - [Segment Tree Lazy Propagation](./segment-tree-lazy-propagation.md)
> - [Sparse Table](./sparse-table.md)

> retrieval-anchor-keywords: fenwick tree vs segment tree, bit, range sum, point update, lazy propagation, query tradeoff, static vs dynamic, prefix sum, interval query, backend metrics

## 핵심 개념

두 자료구조는 자주 같이 등장하지만, 전혀 같은 도구는 아니다.

- Fenwick Tree: prefix sum과 point update 중심
- Segment Tree: 더 일반적인 구간 질의/갱신

선택 기준은 "둘 다 빠른가"가 아니라, **내가 필요한 연산이 무엇인가**다.

## 깊이 들어가기

### 1. Fenwick Tree가 강한 경우

Fenwick Tree는 메모리가 적고 구현이 단순하다.

- 점 갱신
- prefix sum
- range sum
- 빈도 카운팅

이 정도면 아주 실용적이다.

### 2. Segment Tree가 강한 경우

Segment Tree는 더 범용적이다.

- 구간 최솟값/최댓값
- 구간 합
- 구간 갱신 with lazy
- 커스텀 병합 함수

즉 "조금 더 복잡하지만 더 많은 표현력"을 가진다.

### 3. backend에서의 선택 감각

대시보드/집계에는 Fenwick Tree가 충분한 경우가 많다.

- 누적 트래픽
- 점수 분포
- 순위 통계

반면 범위 할당이나 여러 종류의 구간 연산이 섞이면 Segment Tree로 가는 편이 낫다.

### 4. 성능만 보지 말아야 한다

세그먼트 트리는 표현력이 높지만, 구현 실수와 메모리 사용량이 늘 수 있다.
Fenwick Tree는 덜 유연하지만, 문제에 맞으면 더 깔끔하다.

## 실전 시나리오

### 시나리오 1: 누적 요청 수

분 단위 요청 누적은 Fenwick Tree가 충분할 수 있다.

### 시나리오 2: 구간 평균/최소/최대

구간 별로 다양한 집계를 해야 하면 Segment Tree가 더 자연스럽다.

### 시나리오 3: 오판

구간 갱신이 없는데도 세그먼트 트리를 먼저 떠올리면 구현이 과해질 수 있다.

### 시나리오 4: 대규모 실시간 서비스

작고 단순한 연산은 Fenwick Tree, 복잡한 범위 정책은 Segment Tree로 나누는 게 좋다.

## 코드로 보기

```java
public class FenwickVsSegmentNotes {
    // 설명용 스케치: 선택 기준을 빠르게 확인하기 위한 비교표가 핵심이다.
    static final String FENWICK = "point update + prefix sum";
    static final String SEGMENT = "range query + lazy propagation";
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Fenwick Tree | 간단하고 메모리가 작다 | 연산 범위가 제한적이다 | 점 갱신/누적합 중심 |
| Segment Tree | 표현력이 넓다 | 구현이 복잡하고 메모리가 더 든다 | 구간 갱신/복합 질의 |
| Sparse Table | 질의가 매우 빠르다 | 업데이트가 불가능하다 | 정적 RMQ |

이 비교는 "무엇이 더 낫나"가 아니라 "무엇이 맞나"를 고르는 문제다.

## 꼬리질문

> Q: Fenwick Tree와 Segment Tree는 완전히 대체 관계인가?
> 의도: 구조의 범위와 한계를 아는지 확인
> 핵심: 아니다. Fenwick은 더 좁고 가벼운 문제에 좋다.

> Q: 구간 갱신이 들어가면 왜 Segment Tree가 유리한가?
> 의도: lazy propagation 필요성을 이해하는지 확인
> 핵심: 중간 구간을 효율적으로 미룰 수 있기 때문이다.

> Q: 실무에서 어떤 기준으로 고르나?
> 의도: 문제 요구사항과 자료구조를 연결하는지 확인
> 핵심: 연산 종류, 업데이트 빈도, 메모리, 구현 복잡도다.

## 한 줄 정리

Fenwick Tree는 단순한 누적 질의에 강하고, Segment Tree는 더 복잡한 구간 연산을 넓게 커버한다.
