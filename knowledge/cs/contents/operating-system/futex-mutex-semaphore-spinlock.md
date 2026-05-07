---
schema_version: 3
title: Futex Mutex Semaphore Spinlock
concept_id: operating-system/futex-mutex-semaphore-spinlock
canonical: true
category: operating-system
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- lock-contention-runtime-cost
- mutex-semaphore-spinlock-choice
- futex-user-kernel-boundary
aliases:
- futex mutex semaphore spinlock
- futex wait wake
- mutex vs semaphore
- spinlock busy wait
- sleeping lock vs spinning lock
- lock contention
- critical section wait strategy
- Java synchronized futex
symptoms:
- mutex, semaphore, spinlock을 모두 같은 락으로 이해하고 있어
- spinlock이 CPU를 태우는 이유와 sleep 기반 lock이 context switch를 만드는 이유를 섞고 있어
- futex가 항상 커널 락이 아니라 user-space fast path와 kernel sleep/wake의 조합이라는 점을 놓치고 있어
intents:
- comparison
- deep_dive
- troubleshooting
prerequisites:
- operating-system/mutex-deadlock-basics
- operating-system/context-switching-deadlock-lockfree
- operating-system/cpu-cache-coherence-memory-barrier
next_docs:
- operating-system/lock-contention-futex-offcpu-debugging
- operating-system/futex-requeue-priority-inheritance-convoy-debugging
- operating-system/semaphore-monitor-basics
- language/java-thread-basics
linked_paths:
- contents/operating-system/context-switching-deadlock-lockfree.md
- contents/operating-system/cpu-cache-coherence-memory-barrier.md
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
- contents/operating-system/lock-contention-futex-offcpu-debugging.md
- contents/operating-system/futex-requeue-priority-inheritance-convoy-debugging.md
confusable_with:
- operating-system/mutex-deadlock-basics
- operating-system/semaphore-monitor-basics
- operating-system/context-switching-deadlock-lockfree
- language/java-thread-basics
forbidden_neighbors: []
expected_queries:
- mutex와 semaphore와 spinlock은 기다리는 방식이 어떻게 달라?
- futex는 user space fast path와 kernel sleep wake를 어떻게 조합해?
- spinlock은 왜 짧은 임계 구간에서는 빠르지만 오래 잡히면 CPU를 낭비해?
- Java synchronized나 ReentrantLock의 락 경합을 OS futex 관점으로 어떻게 볼 수 있어?
- DB connection pool 동시성 제한은 mutex보다 semaphore 감각이 맞는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 lock primitive bridge로, mutex, semaphore, spinlock, futex를 waiting strategy 관점에서 비교한다.
  mutex vs semaphore, spinlock busy wait, futex wait wake, lock contention, Java synchronized 대기 비용 같은 자연어 질문이 본 문서에 매핑된다.
---
# Futex, Mutex, Semaphore, Spinlock

> 한 줄 요약: 락은 모두 기다림을 다르게 처리한다. 짧게 끝나면 spin, 오래 기다리면 sleep이 기본 감각이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
> - [CPU 캐시, 코히어런시, 메모리 배리어](./cpu-cache-coherence-memory-barrier.md)
> - [file descriptor, socket, syscall cost](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [Lock Contention, Futex Wait, Off-CPU Debugging](./lock-contention-futex-offcpu-debugging.md)
> - [Futex Requeue, Priority Inheritance, Convoy Debugging](./futex-requeue-priority-inheritance-convoy-debugging.md)

> retrieval-anchor-keywords: futex, mutex, semaphore, spinlock, futex_wait, futex_wake, futex requeue, priority inheritance, lock contention, spin wait, sleeping lock, critical section

---

## 핵심 개념

동시성 제어는 결국 "누가 자원을 얼마나 기다릴 것인가"의 문제다.

- `mutex`: 상호 배제를 위한 기본 락
- `semaphore`: 허용 개수를 세는 동기화 도구
- `spinlock`: 잠들지 않고 바쁘게 확인하는 락
- `futex`: 사용자 공간에서 빠르게 처리하고, 필요할 때만 커널이 개입하는 Linux 메커니즘

왜 중요한가:

- 서버는 항상 락을 쓴다
- 락을 잘못 고르면 CPU 낭비, latency 증가, starvation이 생긴다
- Java `synchronized`, `ReentrantLock` 같은 도구의 배경에도 같은 감각이 있다

---

## 깊이 들어가기

### 1. mutex

mutex는 한 번에 한 스레드만 들어가게 한다.

- 임계 구간이 길면 안전하다
- 대기가 길어지면 sleep 기반이 유리하다

실무에서는 보통 "기본 선택지"다.

### 2. semaphore

semaphore는 자원의 개수를 관리한다.

- DB connection permit 수 제한
- worker 동시 실행 수 제한
- 외부 API rate-limiting 보조 수단

락과 달리 "하나만 들어가게"가 아니라 "몇 개까지 허용할지"를 다룬다.

### 3. spinlock

spinlock은 잠들지 않고 계속 확인한다.

장점:

- 매우 짧은 임계 구간에서는 sleep/wakeup 오버헤드를 피할 수 있다

단점:

- 오래 잡히면 CPU를 태운다
- 컨텍스트 스위칭보다 더 비쌀 수 있다

### 4. futex

futex는 user space fast path를 먼저 시도하고, 경쟁이 생기면 커널이 sleep/wake를 돕는다.

핵심 감각:

- uncontended일 때는 빠르다
- contended일 때만 커널 개입이 늘어난다

즉 "항상 커널로 들어가는 락"이 아니라, **대부분은 사용자 공간에서 끝내고 필요할 때만 커널을 부르는 구조**다.

---

## 실전 시나리오

### 시나리오 1: 락 경합으로 p99가 늘어남

임계 구간이 길어지면 mutex 대기가 늘고, 워커가 묶인다.

진단:

```bash
strace -e futex -p <pid>
perf top
jstack <pid>
pidstat -w -p <pid> 1
```

### 시나리오 2: spinlock이 CPU 100%를 먹음

임계 구간이 길거나 경쟁이 높으면 spin이 오히려 손해다.

이럴 때는:

- critical section을 줄이고
- sleep 기반 락으로 바꾸고
- 동시성 자체를 제한해야 한다

### 시나리오 3: DB connection pool을 semaphore로 감싼다

허용 개수를 넘기면 더 기다리게 해야 한다.  
이때 semaphore 감각이 맞다.

### 시나리오 4: JVM에서 모니터 경합이 늘어난다

Java의 락도 결국 대기와 깨우기 문제가 핵심이다.  
락 구현은 언어 문법이 아니라 스케줄링/대기 비용과 연결된다.

---

## 코드로 보기

### semaphore로 동시성 제한

```java
Semaphore permits = new Semaphore(10);

public void handle() throws InterruptedException {
    permits.acquire();
    try {
        // 최대 10개만 동시에 실행
    } finally {
        permits.release();
    }
}
```

### spin의 개념

```c
while (!try_lock()) {
    // busy wait
}
```

짧게 끝나면 유리할 수 있지만, 길어지면 CPU를 낭비한다.

### futex 감각 보기

```bash
strace -e futex -p <pid>
# FUTEX_WAIT, FUTEX_WAKE가 보이면 대기/깨우기 경로를 탄다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| mutex | 단순하고 안전하다 | 경합 시 대기 비용 | 일반 임계 구간 |
| semaphore | 개수 제한에 적합 | 사용 실수 시 논리 깨짐 | 동시 실행 제한 |
| spinlock | 매우 짧으면 빠르다 | CPU를 태운다 | 커널/극단적으로 짧은 구간 |
| futex | uncontended fast path가 빠르다 | 구현 감각이 어렵다 | Linux user-space 락 |

---

## 꼬리질문

> Q: spinlock은 왜 위험한가요?
> 의도: 기다림 방식의 차이를 아는지 확인
> 핵심: 잠들지 않아서 CPU를 지속적으로 소모한다.

> Q: semaphore와 mutex의 차이는?
> 의도: 개수 제어와 상호 배제를 구분하는지 확인
> 핵심: mutex는 1명만, semaphore는 N명까지 허용한다.

> Q: futex는 왜 필요한가요?
> 의도: 사용자 공간 fast path 개념 이해 확인
> 핵심: 경쟁이 없을 때 커널 진입을 피하고, 필요할 때만 sleep/wake를 한다.

---

## 한 줄 정리

락은 모두 기다림을 다르게 처리한다. 짧은 구간이면 spinning, 길어지면 sleeping, 운영에서는 경쟁 패턴에 맞는 선택이 중요하다.
