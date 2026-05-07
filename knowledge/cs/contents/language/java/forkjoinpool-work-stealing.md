---
schema_version: 3
title: ForkJoinPool Work-Stealing
concept_id: language/forkjoinpool-work-stealing
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- forkjoinpool
- common-pool
- work-stealing
aliases:
- ForkJoinPool work stealing
- Java commonPool
- RecursiveTask RecursiveAction
- ManagedBlocker
- parallelStream common pool
- work stealing deque
- ForkJoinPool starvation
symptoms:
- ForkJoinPool을 일반 ExecutorService와 같은 queue worker 모델로 보고 worker deque와 work-stealing의 의미를 놓쳐
- parallelStream이나 CompletableFuture commonPool에 blocking IO, lock wait, 긴 임계영역을 섞어 starvation을 만든다
- fork join task granularity를 너무 작거나 크게 잡아 scheduling overhead나 낮은 parallelism을 만든다
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- language/executor-sizing-queue-rejection-policy
next_docs:
- language/completablefuture-execution-model-common-pool-pitfalls
- language/virtual-threads-project-loom
- language/jfr-jmc-performance-playbook
linked_paths:
- contents/language/java/executor-sizing-queue-rejection-policy.md
- contents/language/java/virtual-threads-project-loom.md
- contents/language/java/jfr-jmc-performance-playbook.md
- contents/language/java-memory-model-happens-before-volatile-final.md
- contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md
confusable_with:
- language/executor-sizing-queue-rejection-policy
- language/completablefuture-execution-model-common-pool-pitfalls
- language/virtual-threads-project-loom
forbidden_neighbors: []
expected_queries:
- ForkJoinPool work stealing이 worker deque와 steal count로 동작하는 방식을 설명해줘
- parallelStream이나 CompletableFuture commonPool에 blocking IO를 넣으면 왜 starvation이 생길 수 있어?
- ForkJoinPool RecursiveTask에서 fork join task granularity를 어떻게 생각해야 해?
- ManagedBlocker는 ForkJoinPool blocking 문제를 어떻게 완화하는 도구야?
- work-stealing pool과 일반 fixed thread pool을 언제 구분해서 써야 해?
contextual_chunk_prefix: |
  이 문서는 ForkJoinPool을 worker deque, work-stealing, commonPool, RecursiveTask/RecursiveAction, ManagedBlocker, blocking I/O starvation 관점으로 설명하는 advanced deep dive다.
  ForkJoinPool, work stealing, commonPool, parallelStream, ManagedBlocker, starvation 질문이 본 문서에 매핑된다.
---
# ForkJoinPool Work-Stealing

> 한 줄 요약: `ForkJoinPool`은 worker deque를 활용한 work-stealing으로 작은 작업을 효율적으로 분산하지만, blocking I/O나 긴 임계영역이 섞이면 오히려 starvation을 만들 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)

> retrieval-anchor-keywords: ForkJoinPool, work-stealing, deque, steal count, commonPool, RecursiveTask, RecursiveAction, ManagedBlocker, join, fork, parallelism, blocking I/O, asyncMode

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

`ForkJoinPool`은 다른 `ExecutorService`와 달리 work-stealing을 핵심으로 둔다.  
각 worker는 자기 작업을 주로 자기 deque의 한쪽 끝에서 처리하고, 일이 없으면 다른 worker의 작업을 훔친다.

이 모델이 잘 맞는 경우:

- 분할 정복
- 작은 작업의 대량 처리
- 재귀적으로 subtasks를 만드는 경우

이 모델이 잘 맞지 않는 경우:

- 오래 블로킹되는 I/O
- 외부 lock 대기
- 큰 단일 작업만 있는 경우

## 깊이 들어가기

### 1. 왜 work-stealing이 빠른가

worker가 자기 작업을 자기 deque에서 먼저 처리하면 캐시 지역성이 좋다.  
남는 worker가 다른 deque에서 steal하면 CPU가 놀지 않게 만든다.

즉, 핵심은 "공평하게 나누기"보다 "busy worker를 최대한 유지하기"다.

### 2. common pool이 편하지만 항상 안전하지는 않다

`ForkJoinPool.commonPool()`은 많은 곳에서 기본값처럼 쓰인다.

- `CompletableFuture`
- parallel stream
- 일부 라이브러리 내부 병렬 처리

문제는 여러 기능이 같은 common pool을 공유하면 하나의 병목이 전체에 번질 수 있다는 점이다.  
특히 blocking call이 섞이면 더 위험하다.

### 3. blocking이 왜 문제인가

work-stealing은 "짧게 끝나는 작업이 많이 쌓이는 상황"에 강하다.  
worker가 외부 I/O, DB wait, lock wait에 오래 묶이면 stealing이 의미를 잃기 쉽다.

이때는 다음을 고려한다.

- 별도 executor 사용
- `ManagedBlocker`
- 작업을 더 잘게 쪼개지 않기
- 아예 virtual threads로 실행 모델을 바꾸기

### 4. 조인과 분할의 균형이 중요하다

task를 너무 잘게 쪼개면 scheduling 비용이 커진다.  
task를 너무 크게 만들면 parallelism을 못 쓴다.

그래서 `fork()`와 `join()`의 경계는 성능 설계의 핵심이다.

## 실전 시나리오

### 시나리오 1: recursive 계산이 잘 맞는다

예:

- 범위 합산
- 트리 순회
- 배열 분할 처리

이런 일은 분할 정복과 잘 맞는다.

### 시나리오 2: `parallelStream()`이 느리거나 불안정하다

`parallelStream()`은 내부적으로 common pool을 사용할 수 있다.  
그래서 같은 JVM에서 다른 비동기 작업과 경쟁할 수 있다.

원인 후보:

- common pool 공유
- 작은 작업이 너무 많음
- 중간에 blocking call 있음
- downstream에서 lock contention 발생

### 시나리오 3: pool이 멈춘 것처럼 보인다

대부분의 경우 실제로는 worker들이 모두 기다리고 있다.

- join 대기
- 외부 lock 대기
- blocking I/O
- 다른 작업에 의한 starvation

JFR과 thread dump를 함께 보면 어느 worker가 무엇에 막혔는지 보인다.

## 코드로 보기

### 1. 분할 정복 `RecursiveTask`

```java
import java.util.concurrent.RecursiveTask;

public class SumTask extends RecursiveTask<Long> {
    private static final int THRESHOLD = 10_000;
    private final int[] data;
    private final int lo;
    private final int hi;

    public SumTask(int[] data, int lo, int hi) {
        this.data = data;
        this.lo = lo;
        this.hi = hi;
    }

    @Override
    protected Long compute() {
        if (hi - lo <= THRESHOLD) {
            long sum = 0;
            for (int i = lo; i < hi; i++) {
                sum += data[i];
            }
            return sum;
        }

        int mid = (lo + hi) >>> 1;
        SumTask left = new SumTask(data, lo, mid);
        SumTask right = new SumTask(data, mid, hi);
        left.fork();
        long rightSum = right.compute();
        long leftSum = left.join();
        return leftSum + rightSum;
    }
}
```

### 2. pool 상태를 읽는 예

```java
import java.util.concurrent.ForkJoinPool;

ForkJoinPool pool = new ForkJoinPool();
System.out.println(pool);
System.out.println("steals=" + pool.getStealCount());
System.out.println("queued=" + pool.getQueuedTaskCount());
```

### 3. blocking 작업은 조심해야 한다

```java
pool.submit(() -> {
    // 오래 걸리는 I/O나 DB 호출은 common pool에서 직접 돌리지 않는 편이 안전하다.
});
```

이런 작업은 custom executor나 virtual thread로 분리하는 편이 낫다.

### 4. blocking을 꼭 섞어야 한다면

```java
ForkJoinPool.managedBlock(new ForkJoinPool.ManagedBlocker() {
    private boolean done;

    @Override
    public boolean block() throws InterruptedException {
        if (!done) {
            // blocking work
            done = true;
        }
        return true;
    }

    @Override
    public boolean isReleasable() {
        return done;
    }
});
```

이 API는 fork/join이 blocking을 조금 더 잘 견디도록 돕지만, 근본적으로 blocking 자체를 없애는 것은 아니다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| work-stealing | 작은 task를 효율적으로 분산한다 | 설계가 blocking 친화적이지 않다 |
| common pool | 설정이 간단하다 | 여러 기능이 섞여 경쟁할 수 있다 |
| custom FJP | 격리가 된다 | 운영과 튜닝 부담이 생긴다 |
| virtual threads | blocking 코드를 유지하기 쉽다 | work-stealing과 목적이 다르다 |

핵심은 "병렬성"과 "블로킹"을 같은 도구로 해결하려 하지 않는 것이다.

## 꼬리질문

> Q: ForkJoinPool이 일반 thread pool보다 유리한 이유는 무엇인가요?
> 핵심: worker deque와 work-stealing으로 작은 task를 효율적으로 분산하고 캐시 지역성을 살릴 수 있다.

> Q: blocking I/O를 ForkJoinPool에 넣으면 왜 위험한가요?
> 핵심: worker가 오래 묶이면 steal할 여지가 줄어들고, 전체 pool이 starvation에 가까워질 수 있다.

> Q: parallel stream이 항상 좋은가요?
> 핵심: 아니다. common pool 공유, task 크기, blocking 여부를 함께 봐야 한다.

## 한 줄 정리

`ForkJoinPool`은 work-stealing에 강하지만 blocking이 섞이면 강점이 약해지므로, 분할 정복에는 쓰되 I/O와 긴 대기는 다른 실행 모델로 분리하는 게 좋다.
