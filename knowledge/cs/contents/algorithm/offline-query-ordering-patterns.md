# Offline Query Ordering Patterns

> 한 줄 요약: Offline query ordering은 질문 순서를 바꿔 상태 이동 비용을 줄이는 방식으로, Mo's algorithm 같은 기법의 공통 감각이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Mo's Algorithm Basics](./mo-algorithm-basics.md)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [Sliding Window Patterns](./sliding-window-patterns.md)

> retrieval-anchor-keywords: offline query ordering, query reordering, batch queries, state movement cost, mo ordering, sqrt decomposition, answer preprocessing, range queries

## 핵심 개념

오프라인 질의는 모든 질문을 먼저 모은 뒤, 더 싸게 처리되도록 순서를 바꾸는 발상이다.

핵심은 "질의 순서를 바꾸어도 정답이 변하지 않는가"다.

- 가능하면 순서를 재조정한다.
- 불가능하면 online 구조가 필요하다.

## 깊이 들어가기

### 1. 왜 ordering이 중요한가

상태를 조금씩 바꾸며 질의를 처리할 때, 다음 질의가 이전 질의와 가까울수록 싸다.

이 감각이 Mo's algorithm, sweep 기반 처리, offline DP 최적화와 연결된다.

### 2. 어떤 질문이 offline인가

- 미리 모든 질의를 알고 있다
- 질의 순서가 결과에 영향을 주지 않는다
- 상태 유지 비용이 크다

### 3. backend에서의 감각

대량 분석 작업은 종종 batch로 처리된다.

- 로그 분석
- 리포트 집계
- 구간 통계

이때 offline ordering은 처리량을 크게 개선할 수 있다.

## 실전 시나리오

### 시나리오 1: range statistics

구간별 빈도나 distinct count 같은 질의에서 쓸 수 있다.

### 시나리오 2: 오판

실시간 응답이 필요한 API에는 적용할 수 없다.

### 시나리오 3: query clustering

비슷한 질의를 가까이 묶으면 add/remove 비용이 줄어든다.

## 코드로 보기

```java
public class OfflineQueryOrderingNotes {
    // 설명용 노트: 실제 구현은 query 비용을 줄이도록 정렬 기준을 설계한다.
    static final class Query {
        int l, r;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Offline ordering | 상태 이동 비용을 줄인다 | 결과를 즉시 못 준다 | batch query |
| Online processing | 즉시 응답 가능 | 상태 이동이 비쌀 수 있다 | 실시간 API |
| Precompute | 질의가 매우 빠르다 | 전처리가 무겁다 | 고정 데이터 |

## 꼬리질문

> Q: 왜 질의 순서를 바꾸나?
> 의도: 상태 이동 비용 감각 확인
> 핵심: 비싼 상태 갱신을 덜 하기 위해서다.

> Q: 온라인 질의와 차이는 무엇인가?
> 의도: 시간적 제약 이해 확인
> 핵심: 온라인은 즉시, 오프라인은 배치 후 처리다.

> Q: 어떤 문제와 잘 맞나?
> 의도: Mo's algorithm 연결 확인
> 핵심: 구간 질의, batch 분석, 상태 재사용 문제다.

## 한 줄 정리

Offline query ordering은 질의 순서를 재배치해 상태 이동 비용을 줄이는 배치 처리 패턴이다.
