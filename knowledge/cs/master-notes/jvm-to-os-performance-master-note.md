# JVM to OS Performance Master Note

> 한 줄 요약: most "Java performance" incidents are really JVM, OS, or storage scheduling issues that only appear through the Java process.

**Difficulty: Advanced**

> retrieval-anchor-keywords: safepoint, GC pause, JIT warmup, deoptimization, context switch, run queue, load average, RSS, native memory, direct buffer, NUMA, page fault, off-CPU, perf, strace, cgroup throttle

> related docs:
> - [G1 vs ZGC](../contents/language/java/g1-vs-zgc.md)
> - [JFR / JMC performance playbook](../contents/language/java/jfr-jmc-performance-playbook.md)
> - [Direct Buffer / Off-Heap / Native Memory Troubleshooting](../contents/language/java/direct-buffer-offheap-memory-troubleshooting.md)
> - [Virtual Threads (Project Loom)](../contents/language/java/virtual-threads-project-loom.md)
> - [Executor Sizing / Queue / Rejection Policy](../contents/language/java/executor-sizing-queue-rejection-policy.md)
> - [context switching, deadlock, lock-free](../contents/operating-system/context-switching-deadlock-lockfree.md)
> - [run queue, load average, CPU saturation](../contents/operating-system/run-queue-load-average-cpu-saturation.md)
> - [eBPF, perf, strace production tracing](../contents/operating-system/ebpf-perf-strace-production-tracing.md)
> - [syscall / user-kernel boundary](../contents/operating-system/syscall-user-kernel-boundary.md)
> - [file descriptor, socket, syscall cost](../contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md)
> - [NUMA production debugging](../contents/operating-system/numa-production-debugging.md)
> - [Topic Map](../rag/topic-map.md)
> - [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
> - [Query Playbook](../rag/query-playbook.md)

## 핵심 개념

Java process performance is a stack:

- application code
- JVM runtime
- native memory
- kernel scheduling
- storage and network I/O

If the symptom is latency, throughput, or memory growth, do not stop at the heap.

Typical cross-layer signals:

- high GC pause time
- high context switch rate
- run queue growth
- RSS growth without heap growth
- blocked threads on I/O
- cgroup throttling in containers

## 깊이 들어가기

### 1. The JVM may be fine while the OS is not

Examples:

- JVM heap is stable, but RSS keeps growing because of direct buffers or mmap
- CPU is not 100% busy, but latency is high because the thread is waiting on lock or I/O
- throughput drops because the container is CPU-throttled

Useful links:

- [Direct Buffer / Off-Heap / Native Memory Troubleshooting](../contents/language/java/direct-buffer-offheap-memory-troubleshooting.md)
- [OOM Killer / cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
- [NUMA Production Debugging](../contents/operating-system/numa-production-debugging.md)

### 2. Safepoints and GC are visible only when you measure them

GC pauses and safepoints are latency events.
They are not just memory events.

Correlate:

- allocation rate
- GC pause histogram
- thread state
- p99 latency

### 3. OS scheduling is part of app latency

If threads are runnable but not scheduled, the app is "slow" even if the code is fine.

That is why `load average` alone is not enough.
Compare:

- run queue
- CPU utilization
- blocked time
- context switch rate

### 4. Syscalls are a boundary, not a detail

Every blocking file, socket, or page fault crosses into the kernel.
That boundary matters when many requests do the same thing at once.

Read together:

- [syscall / user-kernel boundary](../contents/operating-system/syscall-user-kernel-boundary.md)
- [file descriptor, socket, syscall cost](../contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md)
- [I/O models and event loop](../contents/operating-system/io-models-and-event-loop.md)

## 실전 시나리오

### 시나리오 1: heap is fine, RSS is exploding

Likely cause:

- direct buffers
- mmap
- native libraries
- page cache or filesystem pressure

### 시나리오 2: more threads made latency worse

Likely cause:

- context switching
- lock contention
- thread pool oversubscription

### 시나리오 3: virtual threads did not magically solve blocking

Likely cause:

- pinned carrier threads
- blocking native calls
- hidden synchronized sections

### 시나리오 4: container latency gets bad at the same traffic level

Likely cause:

- cgroup CPU throttle
- memory pressure
- noisy neighbor interference

## 코드로 보기

### Perf and JFR triage

```bash
jcmd <pid> JFR.start name=perf settings=profile filename=app.jfr duration=60s
perf stat -p <pid>
strace -f -p <pid>
```

### Thread pool sizing sketch

```java
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    16,
    64,
    60, TimeUnit.SECONDS,
    new ArrayBlockingQueue<>(1000),
    new ThreadPoolExecutor.CallerRunsPolicy()
);
```

This is not just "Java code".
It is an OS scheduling decision.

## 트레이드오프

| Choice | Benefit | Cost | When to pick |
|---|---|---|---|
| Platform threads | Easy debugging | Memory and context-switch cost | Normal blocking workloads |
| Virtual threads | High concurrency | Pinning and hidden blocking still matter | I/O-heavy services |
| Direct buffer | Faster I/O paths | Native memory pressure | Network-heavy systems |
| Heap buffer | Easier GC visibility | Copy cost | Simpler services |
| Larger pools | More parallelism | More contention | Short, independent work |

## 꼬리질문

> Q: Why can a JVM be slow even when CPU usage is not maxed?
> Intent: checks scheduling and waiting awareness.
> Core: the process may be blocked, throttled, or waiting on I/O.

> Q: Why is RSS different from heap usage?
> Intent: checks native memory understanding.
> Core: RSS includes off-heap, mmap, stacks, and other native allocations.

> Q: Why does too many threads hurt latency?
> Intent: checks context switching and contention.
> Core: runnable threads compete for CPU and increase scheduling overhead.

> Q: What changes when virtual threads are introduced?
> Intent: checks modern Java/runtime reasoning.
> Core: concurrency gets cheaper, but blocking and pinning still exist.

## 한 줄 정리

Java performance debugging means tracing the request through the JVM into the kernel, because the bottleneck is often below the heap.
