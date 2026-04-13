# Memory Barriers and VarHandle Fences

> 한 줄 요약: memory barrier는 CPU/JIT가 읽기·쓰기 순서를 바꾸지 못하게 하는 경계이고, `VarHandle` fence 메서드는 그 의도를 Java 코드에서 더 분명하게 드러내는 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
> - [`volatile` `long`/`double` Atomicity and Memory Visibility](./volatile-long-double-atomicity-memory-visibility.md)
> - [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)

> retrieval-anchor-keywords: memory barrier, fence, acquire, release, full fence, load fence, store fence, VarHandle, ordering, reordering, publication, visibility, JMM

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

memory barrier 또는 fence는 읽기/쓰기의 재정렬을 제어한다.  
JMM의 happens-before는 추상 규칙이고, barrier는 그 규칙을 실제 하드웨어와 JIT 수준에서 지키게 하는 장치다.

`VarHandle`은 이런 제어를 더 명시적으로 표현할 수 있게 한다.

- acquire
- release
- opaque
- volatile
- fence 메서드

## 깊이 들어가기

### 1. 왜 barrier가 필요한가

컴파일러와 CPU는 성능을 위해 명령을 재정렬할 수 있다.  
그러면 코드상으로는 먼저 썼다고 생각한 값이 다른 thread에는 나중에 보일 수 있다.

barrier는 이 재정렬에 제약을 건다.

### 2. acquire와 release는 무엇이 다른가

- release write: 이전 쓰기들을 밖으로 내보낼 준비를 강하게 만든다
- acquire read: 이후 읽기들이 너무 일찍 당겨오지 못하게 한다

둘은 대칭처럼 보이지만 쓰임새가 다르다.  
간단한 publication은 release/acquire로 충분한 경우가 많다.

### 3. full fence는 더 강하지만 더 비쌀 수 있다

full fence는 더 넓은 순서 제약을 준다.  
필요할 때만 써야 한다.

실무에서는 "최대한 강한 fence"보다 "딱 필요한 ordering"이 좋다.

### 4. `volatile`은 결국 fence와 연결된다

`volatile` 읽기/쓰기는 JMM 차원에서 happens-before를 제공하고, 구현은 그에 맞는 barrier를 사용한다.  
즉 fence는 `volatile`의 내부 구현 세부이자, 저수준 대안이다.

## 실전 시나리오

### 시나리오 1: flag는 보였는데 데이터가 안 보인다

이건 publication ordering 문제의 전형이다.

```text
data = 42;
ready = true;
```

다른 thread가 `ready`를 먼저 보는데 `data`를 늦게 보면 barrier가 약하거나 없다는 뜻일 수 있다.

### 시나리오 2: lock-free 구조를 만들고 싶다

CAS만으로는 부족할 수 있고, publish/consume 경계의 ordering이 필요하다.  
이때 `VarHandle` access mode와 fence를 검토한다.

### 시나리오 3: over-fencing으로 느려진다

너무 강한 barrier를 자주 넣으면 병렬성이 줄어든다.  
단순 플래그 하나에 full fence를 남발하면 손해가 크다.

## 코드로 보기

### 1. release/acquire 느낌의 publication

```java
public class FlagBox {
    private int data;
    private volatile boolean ready;

    public void publish(int value) {
        data = value;
        ready = true;
    }

    public int read() {
        if (!ready) {
            return -1;
        }
        return data;
    }
}
```

`volatile`만으로도 많은 publication 패턴을 해결할 수 있다.

### 2. VarHandle fence 사용 감각

```java
import java.lang.invoke.VarHandle;

public class FenceExample {
    private int value;

    public void publish(int next) {
        value = next;
        VarHandle.releaseFence();
    }

    public int read() {
        VarHandle.acquireFence();
        return value;
    }
}
```

이 예시는 fence의 의도를 드러내는 학습용 예다.  
실무에서는 `volatile`이나 `VarHandle` access mode가 더 적합한 경우가 많다.

### 3. 배리어를 섞어 쓸 때

```java
// strong ordering이 꼭 필요한 구간만 fence를 두고,
// 나머지는 일반 읽기/쓰기로 둔다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| plain read/write | 가장 빠를 수 있다 | ordering이 없다 |
| `volatile` | 쉬운 visibility 보장 | 과도하면 비용이 생긴다 |
| acquire/release | 더 세밀하다 | 이해와 검증이 필요하다 |
| full fence | 강하다 | 비용이 가장 클 수 있다 |

핵심은 ordering이 필요한 최소 지점에만 barrier를 두는 것이다.

## 꼬리질문

> Q: fence와 `volatile`의 관계는 무엇인가요?
> 핵심: `volatile`은 JMM 규칙이고, fence는 그 규칙을 구현하는 저수준 장치다.

> Q: acquire/release는 언제 유용한가요?
> 핵심: publication이나 consumption의 경계를 표현할 때 과도한 full fence를 피하면서 사용할 수 있다.

> Q: barrier를 너무 많이 두면 왜 느려지나요?
> 핵심: 재정렬 최적화를 막고 캐시/파이프라인 효율을 떨어뜨릴 수 있기 때문이다.

## 한 줄 정리

memory barrier는 ordering을 강제하는 저수준 장치이고, VarHandle fence는 그 목적을 Java 코드에서 명시적으로 표현하는 방법이다.
