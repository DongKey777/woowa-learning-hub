# Binary Lifting vs Heavy-Light Decomposition

> 한 줄 요약: Binary Lifting은 조상 점프에 강하고, Heavy-Light Decomposition은 경로 질의에 강하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Binary Lifting](./binary-lifting.md)
> - [Heavy-Light Decomposition](../data-structure/heavy-light-decomposition.md)
> - [Rerooting DP](./rerooting-dp.md)

> retrieval-anchor-keywords: binary lifting vs heavy light decomposition, tree query comparison, lca, path query, ancestor query, tree decomposition, segment tree on tree

## 핵심 개념

둘 다 트리 질의를 빠르게 하지만, 질문이 다르다.

- Binary Lifting: k번째 조상, LCA, 점프
- HLD: 경로 합, 경로 최댓값, 경로 업데이트

즉 하나는 "위로 뛰기", 다른 하나는 "경로를 잘라 배열로 보기"다.

## 깊이 들어가기

### 1. Binary Lifting이 잘 맞는 경우

- 조상 질의가 많다
- LCA가 핵심이다
- 경로 전체보다 점프가 중요하다

### 2. HLD가 잘 맞는 경우

- 경로 위의 값을 합치거나 갱신한다
- 트리 경로를 segment tree로 처리하고 싶다
- 서브트리와 경로 질의를 같이 다룬다

### 3. backend에서의 감각

조직도, 권한 전파, 계층형 비용 계산에서는 두 구조가 서로 다른 질문을 해결한다.

### 4. 같이 쓰는 경우

실전에서는 binary lifting으로 LCA를 구하고, HLD로 경로 집계를 한다.

## 실전 시나리오

### 시나리오 1: kth ancestor

Binary lifting이 자연스럽다.

### 시나리오 2: path sum

HLD가 더 강하다.

### 시나리오 3: 오판

경로 질의에 binary lifting만 쓰면 집계가 부족할 수 있다.

## 코드로 보기

```java
public class TreeQuerySelector {
    public static String choose(boolean ancestorQuery, boolean pathQuery) {
        if (ancestorQuery) return "Binary Lifting";
        if (pathQuery) return "Heavy-Light Decomposition";
        return "Need a different tool";
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Binary Lifting | 구현이 안정적이고 점프가 빠르다 | 경로 집계는 약하다 | LCA, kth ancestor |
| Heavy-Light Decomposition | 경로 질의에 강하다 | 구현이 복잡하다 | path query |
| Rerooting DP | 모든 루트 결과를 다룬다 | 목적이 다르다 | all-roots tree DP |

## 꼬리질문

> Q: 둘의 가장 큰 차이는 무엇인가요?
> 의도: 문제 유형 구분 확인
> 핵심: binary lifting은 조상 점프, HLD는 경로 집계다.

> Q: 같이 쓸 수도 있나요?
> 의도: 조합 전략 이해 확인
> 핵심: LCA는 binary lifting, 경로 질의는 HLD로 나눠 쓸 수 있다.

> Q: 어떤 상황에서 HLD가 과한가요?
> 의도: 구조 선택 감각 확인
> 핵심: 조상 질의만 필요한 경우다.

## 한 줄 정리

Binary Lifting은 조상 점프와 LCA에, HLD는 경로 집계와 업데이트에 더 잘 맞는다.
