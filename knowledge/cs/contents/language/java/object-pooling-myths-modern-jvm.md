# Object Pooling Myths in the Modern JVM

> 한 줄 요약: 현대 JVM에서는 무조건적인 object pooling이 성능을 올린다는 믿음이 자주 틀리며, JIT, escape analysis, GC, allocation rate 때문에 오히려 단순 생성이 더 나을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Escape Analysis and Scalar Replacement](./escape-analysis-scalar-replacement.md)
> - [Stack vs Heap Escape Intuition](./stack-vs-heap-escape-intuition.md)
> - [JMH Benchmarking Pitfalls](./jmh-benchmarking-pitfalls.md)
> - [Cleaner vs `finalize()` Deprecation](./cleaner-vs-finalize-deprecation.md)

> retrieval-anchor-keywords: object pooling, pooling myth, allocation rate, GC, escape analysis, scalar replacement, reuse, contention, cache locality, modern JVM, premature optimization, object lifecycle

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로 보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

예전에는 객체 생성이 비싸다고 생각해 pooling을 많이 썼다.  
하지만 현대 JVM은 allocation을 매우 빠르게 처리하고, JIT가 임시 객체를 제거할 수도 있다.

그래서 object pooling은 기본값이 아니라 예외적 설계가 되어야 한다.

## 깊이 들어가기

### 1. 왜 pooling이 항상 이득이 아닌가

pooling은 다음 비용을 가져올 수 있다.

- 관리 코드 증가
- contention
- stale state 위험
- reset 누락 버그
- cache locality 악화

즉 할당 비용을 줄이는 대신 다른 비용을 만든다.

### 2. 현대 JVM은 allocation을 잘한다

escape analysis와 scalar replacement가 먹히면, 생각보다 allocation 비용이 작아질 수 있다.  
임시 객체는 JIT가 없애 버릴 수도 있다.

### 3. pool이 필요한 경우도 있다

모든 pooling이 나쁜 것은 아니다.  
대형 버퍼, 비싼 네이티브 리소스, 극도로 제한된 객체 수명에서는 reuse가 합리적일 수 있다.

### 4. benchmark 없이는 믿지 말아야 한다

pooling은 직관적으로 좋아 보이기 쉽다.  
하지만 실제로는 GC와 JIT가 더 잘하는 경우가 많으므로 JMH로 비교해야 한다.

## 실전 시나리오

### 시나리오 1: 작은 DTO를 pool에 넣고 싶다

대부분은 필요 없다.  
오히려 코드 복잡도와 버그 가능성이 올라간다.

### 시나리오 2: 큰 버퍼를 반복해서 쓴다

이 경우는 pooling/재사용이 합리적일 수 있다.  
특히 off-heap이나 direct buffer는 더 신중해야 한다.

### 시나리오 3: 객체 pool이 병목이 된다

pool 자체가 shared lock과 contention point가 될 수 있다.  
이때는 pooling이 성능 병목을 옮겨 놓은 것일 수 있다.

## 코드로 보기

### 1. 단순 생성이 더 나을 수 있는 예

```java
public String format(String a, String b) {
    return new StringBuilder().append(a).append(b).toString();
}
```

### 2. pool이 위험해지는 예

```java
// borrowed object를 reset하지 않으면 stale state가 남을 수 있다.
```

### 3. 큰 리소스의 재사용

```java
// 대형 버퍼나 expensive native resource는 예외적으로 reuse를 고려할 수 있다.
```

### 4. benchmark로 판단

```java
// pooling vs fresh allocation은 직관이 아니라 측정으로 판단한다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| fresh allocation | 단순하고 안전하다 | 극단적 재사용 비용을 못 줄일 수 있다 |
| pooling | 재사용으로 비용을 줄일 수 있다 | contention과 stale state 위험이 있다 |
| object reuse | 메모리 churn을 줄인다 | lifecycle 관리가 어렵다 |
| JIT 최적화에 맡김 | 코드를 단순하게 유지한다 | 특정 워크로드에선 이득이 제한될 수 있다 |

핵심은 object pooling을 기본 성능 최적화로 보지 않는 것이다.

## 꼬리질문

> Q: 현대 JVM에서 pooling이 덜 필요한 이유는 무엇인가요?
> 핵심: allocation이 빠르고 escape analysis가 임시 객체를 지울 수 있기 때문이다.

> Q: pooling이 위험한 이유는 무엇인가요?
> 핵심: contention, stale state, reset 누락, 코드 복잡도 때문이다.

> Q: 언제 pooling을 고려해야 하나요?
> 핵심: 대형 버퍼나 비싼 native resource 같이 재사용 이득이 명확한 경우다.

## 한 줄 정리

현대 JVM에서는 object pooling이 기본 정답이 아니며, 단순 allocation이 더 싸고 안전할 수 있으므로 반드시 측정으로 판단해야 한다.
