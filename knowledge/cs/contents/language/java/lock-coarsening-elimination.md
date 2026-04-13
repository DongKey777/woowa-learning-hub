# Lock Coarsening and Lock Elimination

> 한 줄 요약: HotSpot은 escape analysis와 JIT 최적화를 통해 필요 없는 lock을 제거하거나 여러 lock을 더 큰 임계영역으로 합칠 수 있지만, 이 최적화는 코드 구조와 관찰 가능성에 크게 의존한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Escape Analysis and Scalar Replacement](./escape-analysis-scalar-replacement.md)
> - [Biased Locking Removal and Lock States](./biased-locking-removal-lock-states.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)

> retrieval-anchor-keywords: lock coarsening, lock elimination, escape analysis, synchronized, uncontended lock, monitor optimization, JIT, lock elision, alias analysis, critical section, compilation optimization

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

JIT는 lock을 항상 그대로 두지 않는다.

- lock elimination: 안전하다고 판단되면 lock 자체를 제거
- lock coarsening: 작은 lock 여러 개를 더 큰 lock 하나로 묶음

이런 최적화는 코드가 보기보다 더 빠르게 보이는 이유이기도 하다.

## 깊이 들어가기

### 1. lock elimination은 언제 일어나나

객체가 thread 밖으로 새지 않고, lock이 의미상 보호 대상이 아닌 경우 JIT가 lock을 제거할 수 있다.  
특히 escape analysis와 잘 연결된다.

### 2. lock coarsening은 왜 하나

작은 synchronized 블록이 반복되면 lock enter/exit 비용이 누적된다.  
JIT는 여러 개의 lock을 합쳐 더 큰 임계영역으로 바꿀 수 있다.

### 3. 관찰 가능성이 있으면 최적화가 줄어든다

- synchronization 대상이 외부로 새는 경우
- identityHashCode를 보는 경우
- reflection/agent/monitor 관찰이 있는 경우

이런 요소는 최적화를 더 보수적으로 만들 수 있다.

### 4. coarsening은 항상 좋은 게 아니다

합쳐진 lock이 길어지면 contention이 더 커질 수 있다.  
그래서 JIT 최적화는 코드 구조와 워크로드에 따라 득실이 다르다.

## 실전 시나리오

### 시나리오 1: synchronized가 많은데 성능이 나쁘지 않다

JIT가 lock elimination 또는 coarsening을 적용했을 가능성이 있다.  
그래서 microbenchmark와 실제 워크로드는 다를 수 있다.

### 시나리오 2: lock이 하나로 뭉쳐서 느려진다

coarsening이 과도하게 먹거나, 원래 설계가 너무 큰 shared monitor를 쓰는 경우를 의심한다.

### 시나리오 3: 코드 변경 후 lock 패턴이 바뀐다

작은 리팩터링도 escape 경로를 바꿔 최적화 결과를 달라지게 할 수 있다.  
JIT 관점에서는 충분히 다른 코드다.

## 코드로 보기

### 1. 작은 synchronized가 반복되는 예

```java
public class Builder {
    private final StringBuilder sb = new StringBuilder();

    public void appendLine(String line) {
        synchronized (sb) {
            sb.append(line).append('\n');
        }
    }
}
```

### 2. 제거 후보가 되는 예

```java
public int localWork() {
    Object lock = new Object();
    synchronized (lock) {
        return 1;
    }
}
```

### 3. coarsening을 떠올리게 하는 예

```java
for (int i = 0; i < 100; i++) {
    synchronized (lock) {
        doStep(i);
    }
}
```

### 4. 관측은 JFR/JMH로

```java
// 실제로 lock elimination이 일어나는지는 JMH + JFR로 보는 편이 좋다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| lock elimination | 불필요한 lock 비용을 없앤다 | 코드 구조에 민감하다 |
| lock coarsening | enter/exit overhead를 줄인다 | contention이 커질 수 있다 |
| 명시적 lock 설계 | 의도가 분명하다 | 최적화 여지가 줄 수 있다 |
| lock-free 구조 | 경합이 적을 수 있다 | 설계와 검증이 어렵다 |

핵심은 JIT가 lock을 최적화할 수 있지만, 그 결과는 코드의 escape/alias 구조에 의해 결정된다는 점이다.

## 꼬리질문

> Q: lock elimination은 왜 가능한가요?
> 핵심: 객체와 lock이 thread 밖으로 새지 않으면 실제로 보호할 경쟁 대상이 없다고 판단할 수 있기 때문이다.

> Q: lock coarsening은 왜 생기나요?
> 핵심: 작은 lock을 합쳐 enter/exit 비용을 줄이려는 최적화다.

> Q: 왜 JIT 최적화를 믿기만 하면 안 되나요?
> 핵심: 워크로드와 관찰 가능성에 따라 결과가 달라지기 때문이다.

## 한 줄 정리

lock elimination과 coarsening은 HotSpot의 중요한 최적화지만, escape 분석과 코드 구조에 따라 효과가 달라진다.
