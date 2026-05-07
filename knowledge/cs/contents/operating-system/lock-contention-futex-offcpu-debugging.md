---
schema_version: 3
title: Lock Contention Futex Wait Off CPU Debugging
concept_id: operating-system/lock-contention-futex-offcpu-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- lock-contention-futex
- offcpu
- off-cpu
- perf-lock-futex
aliases:
- lock contention futex off CPU
- off-CPU debugging
- perf lock futex wait
- lock wait p99
- blocked thread latency
- futex contention stack
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/futex-mutex-semaphore-spinlock.md
- contents/operating-system/futex-requeue-priority-inheritance-convoy-debugging.md
- contents/operating-system/ebpf-perf-strace-production-tracing.md
- contents/operating-system/scheduler-wakeup-latency-runqlat-debugging.md
- contents/operating-system/cpu-cache-coherence-memory-barrier.md
- contents/operating-system/context-switching-deadlock-lockfree.md
symptoms:
- CPU를 많이 쓰지 않는데 thread가 lock wait로 오래 못 움직여 request latency가 커진다.
- futex wait, off-CPU stack, perf lock 지표를 어떻게 같이 봐야 할지 모른다.
- lock owner scheduling delay와 actual critical section length가 섞여 보인다.
expected_queries:
- lock contention은 CPU busy보다 off-CPU wait로 보일 수 있어?
- futex wait와 perf lock, off-CPU stack을 함께 보는 디버깅 흐름은?
- lock owner가 runnable인데 scheduling되지 않아 convoy가 생길 수 있어?
- p99 latency에서 lock wait와 CPU saturation을 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 lock contention을 CPU를 많이 쓰는 문제가 아니라 thread가 얼마나 오래 못 움직였는가의
  off-CPU wait 문제로 본다. futex, perf lock, off-CPU stack, scheduler wakeup latency를 연결한다.
---
# Lock Contention, Futex Wait, Off-CPU Debugging

> 한 줄 요약: 락 경합은 CPU를 많이 쓰는 문제보다 "스레드가 얼마나 오래 못 움직였는가"의 문제로 드러나는 경우가 많고, `futex`, off-CPU stack, `perf lock`을 같이 봐야 정체가 보인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Futex, Mutex, Semaphore, Spinlock](./futex-mutex-semaphore-spinlock.md)
> - [Futex Requeue, Priority Inheritance, Convoy Debugging](./futex-requeue-priority-inheritance-convoy-debugging.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [CPU Cache, Coherence, Memory Barrier](./cpu-cache-coherence-memory-barrier.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)

> retrieval-anchor-keywords: lock contention, futex, off-CPU, perf lock, mutex convoy, rwlock contention, blocked threads, lock handoff, futex_wait, futex_wake, contention debugging

## 핵심 개념

락 문제는 흔히 "CPU가 높다"로 상상되지만, 실제 장애에서는 대기 시간이 더 큰 특징으로 나타난다. 경합이 커지면 스레드는 `futex` wait에 잠들고, lock owner가 다시 실행될 때까지 off-CPU 상태로 밀린다. 그래서 락 디버깅은 CPU hot path와 별개로 "누가, 어떤 락 때문에, 얼마나 오래 못 뛰었는가"를 봐야 한다.

- `lock contention`: 동시에 같은 임계 구간을 원해 기다림이 생기는 상태다
- `futex`: user-space 락이 경쟁 시 커널의 sleep/wake 경로를 빌리는 메커니즘이다
- `off-CPU`: 스레드가 실행 중이 아니라 잠들어 있거나 기다리는 시간이다
- `perf lock`: lock 대기/획득 이벤트를 보는 도구다
- `convoy`: 한 락이 풀릴 때마다 대기열이 길게 이어지는 현상이다

왜 중요한가:

- 락 경합은 p99를 무너뜨리지만 CPU 사용률만으로는 잘 안 보인다
- 경합이 심하면 실제 병목은 critical section 길이보다 handoff와 wakeup 지연일 수 있다
- 애플리케이션 락, 라이브러리 락, 런타임 락이 다 비슷한 증상으로 보일 수 있다

## 깊이 들어가기

### 1. lock hold time과 lock wait time은 다르다

많은 팀이 락을 오래 잡는 코드만 찾지만, 실제 대기는 그보다 더 크다.

- owner가 lock을 푼다
- waiter가 깨워진다
- 하지만 즉시 CPU를 못 받아 다시 기다린다
- 그 사이 큐 전체가 convoy가 된다

즉 critical section이 짧아도 scheduler queueing과 wakeup cost 때문에 체감 wait는 길어질 수 있다.

### 2. futex는 "경합이 생겼다"를 보여 주는 힌트다

Linux user-space 락은 경쟁이 없을 때 user-space fast path로 끝난다. `futex_wait`/`futex_wake`가 자주 보이기 시작하면 이미 경합이 운영 문제로 표면화된 것이다.

- `futex_wait`: 락을 못 얻고 잠든다
- `futex_wake`: owner나 runtime이 waiter를 깨운다
- wait가 길다고 해서 owner가 계속 CPU를 쓰는 것은 아니다

그래서 `strace -e futex`는 "락 대기가 있다"는 신호는 주지만, root cause는 off-CPU와 scheduler까지 봐야 나온다.

### 3. rwlock과 조건 변수는 더 교묘하게 꼬일 수 있다

reader/writer 구조나 condition variable은 단순 mutex보다 현상이 복잡하다.

- reader가 많아 writer가 오래 굶는다
- broadcast wakeup이 herd를 만든다
- queue 자체는 짧아도 특정 writer만 tail에서 계속 밀린다

이때는 단순 평균 lock wait보다 분포와 wakeup 패턴이 중요하다.

### 4. cache line bouncing도 락 체감에 섞인다

락 변수 하나에 많은 코어가 접근하면 단순 wait 외에도 cache line 이동 비용이 붙는다.

- 스핀 구간이 길어진다
- CAS retry가 늘어난다
- 실질 lock hold time보다 CPU side overhead가 커진다

그래서 lock contention은 스케줄링 문제이면서 캐시 일관성 문제이기도 하다.

## 실전 시나리오

### 시나리오 1: CPU는 40%인데 요청은 계속 timeout 난다

가능한 원인:

- 다수 스레드가 `futex_wait`에 잠들어 있다
- critical section보다 wakeup/handoff가 느리다
- owner thread가 run queue에서 밀린다

진단:

```bash
sudo strace -ff -ttT -p <pid> -e trace=futex
sudo offcputime-bpfcc -p <pid> 20
sudo perf sched timehist -p <pid> -- sleep 15
```

판단 포인트:

- `futex_wait` 시간이 긴가
- off-CPU stack 상단에 lock wait 계열이 많은가
- owner handoff가 scheduler delay와 같이 보이는가

### 시나리오 2: `perf`로는 CPU hotspot이 안 보이는데 p99만 무너진다

가능한 원인:

- 대부분 시간이 기다림이라 CPU 샘플에 잘 안 잡힌다
- lock convoy로 인해 소수 스레드만 잠깐 일하고 다수는 잔다
- 사용률이 아니라 blocked time이 핵심이다

대응 감각:

- CPU flame graph만으로 결론내리지 않는다
- off-CPU와 lock report를 같이 본다
- wait distribution을 요청 지연과 맞춘다

### 시나리오 3: read-heavy라서 rwlock이 안전할 줄 알았는데 writer가 굶는다

가능한 원인:

- reader가 계속 들어오며 writer handoff가 밀린다
- wakeup 정책과 scheduling이 writer tail을 악화시킨다
- 배치성 read burst가 writer starvation을 만든다

이 경우는 "read 비율이 높다"는 이유만으로 rwlock을 정답으로 보면 안 된다는 좋은 예다.

## 코드로 보기

### futex 경합을 직접 보기

```bash
sudo strace -ff -ttT -p <pid> -e trace=futex
```

### lock report

```bash
sudo perf lock record -p <pid> -- sleep 20
sudo perf lock report
```

### off-CPU stack

```bash
sudo offcputime-bpfcc -p <pid> 20
```

### mental model

```text
many threads want the same lock
  -> some spin or sleep
  -> owner releases
  -> waiter wakes
  -> waiter may still wait in run queue
  -> convoy extends tail latency
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 단순 mutex | 이해가 쉽다 | hotspot 한 곳에 경합이 몰리면 tail이 커진다 | 기본 선택지 |
| rwlock | read 비중이 높으면 유리할 수 있다 | writer starvation과 handoff cost가 생길 수 있다 | truly read-mostly |
| sharding/striping | 경합 지점을 나눈다 | 구현 복잡도가 오른다 | key-local workload |
| lock-free/CAS | 낮은 경쟁에서는 빠르다 | 높은 경쟁에서는 retry와 cache bouncing이 커진다 | 짧은 원자 연산 |

## 꼬리질문

> Q: lock contention이 왜 CPU flame graph에는 잘 안 보일 수 있나요?
> 핵심: 대부분 시간이 off-CPU waiting에 쓰이면 CPU 샘플링에는 덜 잡히기 때문이다.

> Q: `futex_wait`가 길면 무조건 critical section이 긴 건가요?
> 핵심: 아니다. owner handoff 지연, scheduler queueing, convoy가 wait를 더 길게 만들 수 있다.

> Q: rwlock은 read-heavy면 항상 좋은가요?
> 핵심: 아니다. writer starvation과 broadcast wakeup 비용이 오히려 tail을 악화시킬 수 있다.

## 한 줄 정리

락 문제는 "누가 락을 오래 잡았나"보다 "누가 락 때문에 얼마나 오래 off-CPU로 밀렸나"를 봐야 풀리는 경우가 많다.
