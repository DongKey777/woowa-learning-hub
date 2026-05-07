---
schema_version: 3
title: CPU Cache, Coherence, Memory Barrier
concept_id: operating-system/cpu-cache-coherence-memory-barrier
canonical: true
category: operating-system
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- coherence-vs-ordering
- memory-barrier-release-acquire
- false-sharing-performance-diagnosis
aliases:
- CPU cache coherence memory barrier
- cache coherence
- memory barrier
- false sharing
- cache line
- MESI basics
- release acquire fence
- visibility ordering
- perf c2c cache line
- 멀티코어 가시성 순서
- CPU cache와 JMM 연결
- cache line ping pong
symptoms:
- 플래그를 봤는데 데이터가 아직 예전 값처럼 보이는 이유가 궁금해
- coherence와 memory ordering 차이가 헷갈려
- 스레드 수를 늘렸는데 cache line 경쟁 때문에 더 느려지는 것 같아
intents:
- deep_dive
- troubleshooting
prerequisites:
- operating-system/process-thread-basics
- language/java-memory-model-happens-before-volatile-final
next_docs:
- operating-system/false-sharing-cache-line
- operating-system/context-switching-deadlock-lockfree
- operating-system/cpu-affinity-irq-affinity-core-locality
- language/java-memory-model-happens-before-volatile-final
linked_paths:
- contents/operating-system/false-sharing-cache-line.md
- contents/operating-system/cpu-affinity-irq-affinity-core-locality.md
- contents/operating-system/cfs-scheduler-nice-cpu-fairness.md
- contents/operating-system/workqueues-kthreads-debugging.md
- contents/operating-system/major-minor-page-faults-runtime-diagnostics.md
- contents/operating-system/context-switching-deadlock-lockfree.md
- contents/language/java-memory-model-happens-before-volatile-final.md
- contents/language/java/volatile-counter-atomicity-cause-router.md
confusable_with:
- operating-system/false-sharing-cache-line
- operating-system/context-switching-deadlock-lockfree
- language/java-memory-model-happens-before-volatile-final
forbidden_neighbors: []
expected_queries:
- cache coherence와 memory ordering은 뭐가 달라?
- memory barrier 없이 ready flag를 보면 왜 data가 아직 안 보일 수 있어?
- false sharing과 cache line ping-pong이 멀티스레드 성능을 어떻게 망쳐?
- Java volatile과 CPU memory barrier가 어떤 관계인지 설명해줘
- perf c2c로 cache line 경쟁을 의심하는 상황을 알고 싶어
contextual_chunk_prefix: |
  이 문서는 멀티코어 CPU에서 cache line, coherence traffic, memory ordering, memory barrier, release/acquire, false sharing이 동시성 성능과 visibility bug에 어떻게 연결되는지 설명하는 advanced deep dive다.
  Java volatile과 JMM 뒤의 하드웨어 감각, 플래그는 봤는데 데이터가 안 보이는 증상, cache line ping-pong, MESI, perf c2c 같은 자연어 질문이 본 문서에 매핑된다.
---
# CPU Cache, Coherence, Memory Barrier

> 한 줄 요약: 멀티코어에서 성능 문제와 동시성 버그는 cache line 경쟁, coherence traffic, memory ordering이 서로 섞여서 나타나며, 먼저 false sharing과 visibility를 구분해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [false sharing, cache line](./false-sharing-cache-line.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [Workqueues, Kthreads, Debugging](./workqueues-kthreads-debugging.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)

> retrieval-anchor-keywords: cache coherence, memory barrier, false sharing, cache line, MESI, release acquire, fence, perf c2c, visibility, ordering

## 핵심 개념

CPU는 DRAM보다 훨씬 가까운 캐시에 데이터를 둔다. 멀티코어 환경에서는 한 코어가 쓴 값이 다른 코어에 언제, 어떤 순서로 보이는지가 성능과 정합성을 좌우한다.

- `cache line`: 캐시가 움직이는 기본 단위다
- `coherence`: 같은 주소의 최신 값을 유지하려는 규칙이다
- `memory barrier`: 명령 재정렬을 제한해 관찰 순서를 맞춘다

왜 중요한가:

- false sharing은 공유하지 않는 데이터인데도 캐시 경쟁을 만든다
- release/acquire 없이 상태를 넘기면 stale read가 생길 수 있다
- 성능 버그와 정합성 버그가 같은 코드에서 함께 보일 수 있다

이 문서는 [false sharing, cache line](./false-sharing-cache-line.md)보다 더 넓게 coherence와 ordering을 함께 본다.

## 깊이 들어가기

### 1. cache line은 성능의 기본 단위다

캐시는 바이트 단위가 아니라 cache line 단위로 움직인다.

- 한 줄을 누가 자주 쓰느냐가 중요하다
- 한 코어의 write가 다른 코어의 line을 무효화할 수 있다
- false sharing이 대표적이다

### 2. coherence와 ordering은 다르다

- coherence: 같은 주소에 최신 값을 맞추는 문제다
- ordering: 서로 다른 주소의 관찰 순서를 맞추는 문제다

같은 값을 본다고 해서 코드 순서가 보장되는 것은 아니다.

### 3. memory barrier는 재정렬을 제한한다

- store barrier: 이전 write가 먼저 보이도록 돕는다
- load barrier: 이후 read가 앞당겨지지 않도록 막는다
- full fence: 둘 다 강하게 제한한다

### 4. release/acquire는 실전에서 자주 보이는 패턴이다

- producer는 `release`로 publish한다
- consumer는 `acquire`로 확인한 뒤 읽는다

## 실전 시나리오

### 시나리오 1: 멀티스레드 카운터를 늘렸는데 느려진다

가능한 원인:

- false sharing
- atomic contention
- cache line ping-pong

진단:

```bash
perf stat -e cache-references,cache-misses,LLC-load-misses,LLC-store-misses -- sleep 10
perf c2c record -p <pid> -- sleep 20
perf c2c report
```

### 시나리오 2: 플래그를 봤는데 데이터가 아직 예전 값이다

가능한 원인:

- ordering이 보장되지 않는다
- barrier가 없다
- release/acquire 패턴이 빠졌다

### 시나리오 3: 워커 수를 늘릴수록 성능이 안 좋아진다

가능한 원인:

- cache line thrash
- coherence traffic 증가
- affinity와 locality가 깨짐

이 경우는 [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)와 같이 본다.

## 코드로 보기

### 잘못된 패턴 예시

```c
data = value;
ready = true;
```

이 순서가 다른 코어에서 그대로 보인다고 가정하면 위험하다.

### 올바른 감각

```c
// producer
store_release(&ready, true);

// consumer
if (load_acquire(&ready)) {
    // safe to read published data
}
```

### false sharing 힌트

```text
different variables
  -> same cache line
  -> writes invalidate each other
  -> performance collapses
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| atomics only | 간단하다 | ordering 실수 위험 | 작은 동기화 |
| mutex/lock | 정합성이 쉽다 | contention 비용이 든다 | 복잡한 공유 상태 |
| padding으로 false sharing 완화 | 성능이 좋아질 수 있다 | 메모리 사용이 늘어난다 | 카운터/통계 |
| release/acquire | 명확하다 | 이해가 필요하다 | lock-free publish |

## 꼬리질문

> Q: coherence와 memory ordering 차이는?
> 핵심: coherence는 최신성, ordering은 관찰 순서다.

> Q: false sharing은 왜 느린가요?
> 핵심: 서로 다른 데이터라도 같은 cache line을 자주 무효화하기 때문이다.

> Q: barrier 없이도 가끔 맞는 이유는?
> 핵심: 우연히 순서가 맞을 수 있지만 보장되지 않기 때문이다.

## 한 줄 정리

cache coherence는 같은 주소의 최신성을 맞추고, memory barrier는 서로 다른 메모리 접근의 관찰 순서를 보장하며, 둘을 구분해야 멀티코어 버그를 제대로 잡을 수 있다.
