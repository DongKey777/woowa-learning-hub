# Stack vs Heap Escape Intuition

> 한 줄 요약: "스택에 올라간다/힙에 올라간다"는 직관은 편하지만, HotSpot의 실제 최적화는 escape analysis와 allocation elimination으로 훨씬 더 유연하게 동작한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Escape Analysis and Scalar Replacement](./escape-analysis-scalar-replacement.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)

> retrieval-anchor-keywords: stack vs heap, escape analysis, stack allocation, heap allocation, scalar replacement, object lifetime, publication, allocation elimination, JIT, local variable, object identity

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

Java에서 local variable은 스택에 있지만, 그 변수가 참조하는 객체는 대개 heap에 있다.  
이 단순한 그림은 출발점으로는 좋지만, HotSpot 최적화까지 설명하진 못한다.

실제 핵심은 객체가 어디로 "escape"하는가다.

- method 밖으로 나가면 더 조심해야 한다
- thread 밖으로 나가면 더 조심해야 한다
- 안 나가면 JIT가 더 공격적으로 최적화할 수 있다

## 깊이 들어가기

### 1. 스택과 heap은 "생각 도구"다

개발자는 보통 이렇게 외운다.

- primitive local: stack 느낌
- object: heap 느낌

하지만 JVM은 더 똑똑하다.  
객체를 실제로 만들지 않을 수도 있고, 일부 필드는 register/local로 쪼갤 수도 있다.

### 2. escape가 실제 의미하는 것

객체가 escape한다는 것은 그 객체가 더 넓은 범위에서 관찰될 수 있다는 뜻이다.

- 반환값이 된다
- 필드에 저장된다
- 다른 thread로 넘겨진다
- static/global 경로로 보관된다

그 순간 JIT가 "이 객체는 임시로 지워도 안전하다"라고 말하기 어려워진다.

### 3. stack allocation보다 중요한 것은 allocation elimination이다

사람들은 종종 "스택에 넣으면 빠르다"로 이해한다.  
실제로는 객체를 아예 만들지 않는 최적화가 더 중요할 수 있다.

즉 성능 관점에서 핵심은 공간이 아니라 **lifetime과 observability**다.

### 4. identity가 있으면 더 조심해야 한다

객체 identity가 관찰되면 JIT가 마음대로 지우기 어렵다.

- `synchronized(obj)`
- `System.identityHashCode(obj)`
- 객체 참조 비교
- 외부로 새는 reference

이런 것은 escape 분석을 더 보수적으로 만든다.

## 실전 시나리오

### 시나리오 1: 작은 DTO를 많이 만들어도 괜찮다

임시 객체가 좁은 scope 안에서만 쓰이고 밖으로 새지 않으면, HotSpot이 allocation을 줄이거나 없앨 수 있다.

### 시나리오 2: helper 객체를 재사용하려다 오히려 복잡해진다

재사용은 언제나 이득이 아니다.  
상태 오염, 동기화, contention, 테스트 복잡도가 더 커질 수 있다.

### 시나리오 3: "스택 객체"를 직접 기대한다

Java 코드 수준에서 "이 객체는 무조건 stack에 간다"고 생각하는 것은 위험하다.  
JIT가 바꿀 수 있기 때문이다.

## 코드로 보기

### 1. 임시 객체 감각

```java
public int sumPoint(int x, int y) {
    Point p = new Point(x, y);
    return p.x() + p.y();
}

record Point(int x, int y) {}
```

### 2. escape가 커지는 예

```java
public class Holder {
    private Object value;

    public void store(Object next) {
        value = next;
    }
}
```

### 3. identity가 최적화를 막을 수 있다

```java
public int mark(Object obj) {
    return System.identityHashCode(obj);
}
```

### 4. 실무 감각

```java
// 먼저 읽기 쉬운 코드를 쓰고,
// JIT가 불필요한 allocation을 제거할 수 있게 scope를 좁히는 편이 낫다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| 작은 임시 객체 사용 | 코드가 읽기 쉽다 | JIT 최적화에 의존할 수 있다 |
| 객체 재사용 | 할당이 줄어들 수 있다 | 상태와 동시성 관리가 어렵다 |
| primitive 위주 계산 | 빠를 수 있다 | 도메인 표현력이 떨어질 수 있다 |
| identity 기반 설계 | 단순한 경우가 있다 | escape 최적화 여지가 줄 수 있다 |

핵심은 stack/heap 위치보다 "얼마나 넓게 관찰되는가"다.

## 꼬리질문

> Q: Java 객체는 언제 스택에 올라가나요?
> 핵심: 코드 수준에서 고정적으로 보장되는 개념이 아니라, JIT 최적화 결과로 바뀔 수 있다.

> Q: escape analysis가 왜 중요하나요?
> 핵심: allocation elimination과 scalar replacement의 전제가 되기 때문이다.

> Q: 객체 재사용이 항상 좋은가요?
> 핵심: 아니다. 동시성과 수명 관리가 더 복잡해질 수 있다.

## 한 줄 정리

Java 성능을 볼 때는 스택/heap 이분법보다 객체가 어디까지 escape하는지와 JIT가 allocation을 제거할 수 있는지를 먼저 봐야 한다.
