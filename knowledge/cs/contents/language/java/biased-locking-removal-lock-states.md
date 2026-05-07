---
schema_version: 3
title: Biased Locking Removal and Lock States
concept_id: language/java-biased-locking-removal-lock-states
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- java-locking
- synchronized-performance
- jvm-version-change
aliases:
- biased locking removal
- JEP 374 biased locking
- Java lock states
- mark word object header
- inflated monitor
- thin lock lightweight lock
- synchronized fast path
symptoms:
- JDK 15 이후 biased locking 기본 비활성화와 JDK 18 제거를 모른 채 예전 synchronized 성능 가정을 그대로 적용해
- synchronized가 항상 무겁거나 항상 공짜라고 단순화하고 uncontended fast path와 monitor inflation을 구분하지 못해
- JDK 업그레이드 후 lock microbenchmark 차이를 JVM 락 상태 변화와 연결해야 해
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- language/java-memory-model-happens-before-volatile-final
- language/varhandle-unsafe-atomics
next_docs:
- language/jfr-jmc-performance-playbook
- language/jit-warmup-deoptimization
- language/escape-analysis-scalar-replacement
- operating-system/cpu-cache-coherence-memory-barrier
linked_paths:
- contents/language/java-memory-model-happens-before-volatile-final.md
- contents/language/java/varhandle-unsafe-atomics.md
- contents/language/java/jfr-jmc-performance-playbook.md
- contents/language/java/jit-warmup-deoptimization.md
- contents/language/java/escape-analysis-scalar-replacement.md
- contents/operating-system/cpu-cache-coherence-memory-barrier.md
confusable_with:
- language/java-memory-model-happens-before-volatile-final
- language/varhandle-unsafe-atomics
- operating-system/cpu-cache-coherence-memory-barrier
forbidden_neighbors: []
expected_queries:
- biased locking이 JDK 15와 JDK 18에서 어떻게 바뀌었는지 설명해줘
- synchronized는 biased locking 제거 이후에도 왜 항상 느리다고 말할 수 없어?
- Java lock state에서 thin lock과 inflated monitor를 어떻게 이해해야 해?
- JDK 업그레이드 후 lock benchmark가 달라졌을 때 무엇을 확인해야 해?
- mark word object header monitor inflation을 synchronized 성능 관점으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 HotSpot biased locking removal과 synchronized lock states를 JEP 374, JDK 15, JDK 18, mark word, lightweight lock, inflated monitor 관점으로 설명하는 advanced deep dive다.
  biased locking, synchronized performance, monitor inflation, uncontended fast path, lock state 질문이 본 문서에 매핑된다.
---
# Biased Locking Removal and Lock States

> 한 줄 요약: biased locking은 JDK 15에서 기본 비활성화되고 JDK 18에서 관련 코드가 제거되었으며, 지금의 `synchronized`는 "bias"보다 "uncontended fast path vs inflated monitor" 관점으로 읽는 편이 맞다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)

> retrieval-anchor-keywords: biased locking, lock states, mark word, object header, thin lock, lightweight locking, inflated monitor, monitor inflation, `synchronized`, revocation, JEP 374, JDK 15, JDK 18

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

HotSpot의 락은 "있다/없다"가 아니라 상태를 가진다.  
그 상태를 읽는 관점이 object header와 mark word다.

- unlocked
- lightweight/thin lock
- inflated monitor

예전에는 biased locking이 여기에 더해져서 "특정 thread에 편향된 빠른 경로"가 있었다.  
하지만 JEP 374로 JDK 15에서 기본 비활성화되었고, 이후 JDK 18에서 관련 코드가 obsolete 처리되었다.

### 왜 지금도 알아야 하나

biased locking이 없어졌다고 `synchronized`가 의미 없어진 것은 아니다.  
오히려 이제는 "bias가 있던 시대의 마이크로벤치마크"와 "현재 JVM의 락 비용"을 구분해야 한다.

## 깊이 들어가기

### 1. biased locking이 왜 있었나

biased locking의 목적은 uncontended lock에서 CAS 비용을 피하는 것이었다.  
같은 thread가 반복해서 같은 monitor를 잡는 경우를 더 싸게 처리하려고 한 것이다.

문제는 시간이 지나면서 다음 부담이 커졌다는 점이다.

- 코드 복잡도
- JVM 내부 상호작용 증가
- 최신 하드웨어와 워크로드에서 얻는 이득 감소

그래서 현재는 유지 비용 대비 효용이 낮다고 본다.

### 2. lock state를 읽는 기본 감각

실무에서 필요한 감각은 복잡한 비트 필드가 아니라 다음이다.

- lock이 비어 있으면 fast path가 있다
- 경쟁이 생기면 monitor가 inflating 될 수 있다
- `synchronized`가 항상 무거운 것은 아니다
- 그렇다고 공짜도 아니다

즉, "락이 있느냐"보다 "얼마나 자주 경합하는가"가 더 중요하다.

### 3. biased locking이 사라졌어도 최적화는 남아 있다

JVM과 JIT는 여전히 다음을 한다.

- lock elision
- lock coarsening
- escape analysis 기반 lock 제거
- uncontended fast path 최적화

그러므로 "bias가 사라졌으니 synchronized는 다 느리다"는 결론은 틀리다.

### 4. 버전 차이를 꼭 기억해야 한다

JDK 업그레이드 후 lock 성능이 달라졌다면 다음을 먼저 떠올려야 한다.

- bias 관련 가정이 사라졌다
- lock inflation 패턴이 달라졌다
- JIT가 인라이닝/EA를 다르게 적용할 수 있다

특히 미세한 차이는 JMH warmup 없이는 제대로 보이지 않는다.

## 실전 시나리오

### 시나리오 1: `synchronized`가 갑자기 느려졌다

가능한 원인:

- thread 수가 늘어 경합이 커졌다
- 같은 객체를 여러 request가 공유한다
- 락 안에서 I/O나 긴 계산을 한다
- JDK 버전이 바뀌어 biased locking 전제가 달라졌다

진단은 "락을 제거할 수 있는가"보다 먼저 "경합 구간이 짧은가"를 본다.

### 시나리오 2: 작은 임계영역인데도 병목이 난다

이 경우는 보통 다음 중 하나다.

- 락 객체가 너무 공유된다
- lock striping이 없다
- `HashMap` 같은 비동시 자료구조를 보호하려고 하나의 큰 락을 쓴다

여기서는 락 자체보다 설계가 문제일 가능성이 높다.

### 시나리오 3: 미세 벤치마크가 JDK 버전마다 달라진다

biased locking이 켜져 있던 시절의 결과를 현재 JDK에 그대로 들이대면 안 된다.  
같은 코드라도 VM의 락 경로가 달라졌기 때문이다.

## 코드로 보기

### 1. 가장 기본적인 `synchronized`

```java
public class Counter {
    private int value;

    public synchronized int increment() {
        return ++value;
    }

    public synchronized int get() {
        return value;
    }
}
```

이 코드는 경합이 낮으면 읽기 쉽고 충분히 빠를 수 있다.  
문제는 락이 길어지거나 공유 범위가 커질 때다.

### 2. 공유 범위를 줄인 예

```java
public class ShardedCounter {
    private final int[] shards = new int[16];

    public void increment(int key) {
        int index = key & (shards.length - 1);
        synchronized (shards) {
            shards[index]++;
        }
    }
}
```

이 예시는 단순화되어 있지만, 실무에서는 lock striping이나 concurrent 자료구조로 바꾸는 쪽이 더 낫다.

### 3. 락 상태를 볼 때 함께 쓰는 명령

```bash
jcmd <pid> Thread.print -l
jfr summary /tmp/app.jfr
```

경합이 있다면 thread dump에 `BLOCKED` 상태와 monitor 소유자가 나타난다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `synchronized` | 단순하고 JVM 최적화가 잘 먹는다 | 경합이 크면 병목이 된다 |
| `ReentrantLock` | 공정성, timed lock, interruptible lock이 가능하다 | 코드가 복잡해진다 |
| striping | 경합을 분산한다 | 설계가 복잡해진다 |
| lock-free | 경합 상황에서 유리할 수 있다 | ABA, CAS 실패, 설계 난이도가 높다 |

핵심은 "bias가 있느냐"가 아니라 "공유와 경합을 어떻게 줄이느냐"다.

## 꼬리질문

> Q: biased locking은 왜 제거됐나요?
> 핵심: uncontended case를 싸게 만들려고 했지만, 복잡도와 유지 비용에 비해 이득이 줄어들었다.

> Q: 지금도 `synchronized`를 써도 되나요?
> 핵심: 된다. 현재 JVM에서도 uncontended fast path는 여전히 중요하고, JIT 최적화도 함께 작동한다.

> Q: lock state를 볼 때 가장 먼저 확인할 것은 무엇인가요?
> 핵심: 공유 객체가 너무 넓게 쓰이는지, 그리고 임계영역이 길어지는지다.

## 한 줄 정리

biased locking은 역사 속 최적화가 되었고, 지금은 lock state와 경합, inflation을 기준으로 `synchronized` 비용을 읽어야 한다.
