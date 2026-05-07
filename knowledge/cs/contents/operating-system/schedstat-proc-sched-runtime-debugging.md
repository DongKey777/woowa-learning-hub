---
schema_version: 3
title: schedstat proc sched Runtime Debugging
concept_id: operating-system/schedstat-proc-sched-runtime-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- schedstat-proc-sched
- schedstat-proc-pid
- sched
- scheduler
aliases:
- schedstat proc pid sched
- scheduler runtime debugging
- per task scheduler stats
- runqlat follow up
- CPU scheduling delay attribution
- scheduler queueing diagnostics
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/scheduler-observation-starter-guide.md
- contents/operating-system/scheduler-wakeup-latency-runqlat-debugging.md
- contents/operating-system/run-queue-load-average-cpu-saturation.md
- contents/operating-system/cpu-migration-load-balancing-locality-debugging.md
- contents/operating-system/ebpf-perf-strace-production-tracing.md
symptoms:
- runqlat으로 tail은 보였지만 어떤 task와 CPU에서 scheduler delay가 누적되는지 더 좁혀야 한다.
- /proc/<pid>/sched와 /proc/schedstat 해석을 섞어 per-task와 per-CPU 관점을 구분하지 못한다.
- CPU 쏠림과 wakeup latency를 연결해야 한다.
expected_queries:
- runqlat 다음에 schedstat와 /proc/<pid>/sched로 무엇을 더 확인해?
- scheduler delay가 어떤 task와 CPU에서 누적되는지 어떻게 좁혀?
- /proc/pid/sched와 /proc/schedstat는 어떤 관측창이 달라?
- CPU migration이나 load balancing 문제를 scheduler stats로 어떻게 확인해?
contextual_chunk_prefix: |
  이 문서는 runqlat이 wakeup-to-run latency distribution을 보여준 뒤, schedstat와
  /proc/<pid>/sched가 그 지연이 어떤 task와 CPU에서 누적되는지 좁혀 주는 runtime debugging
  관측창이라는 점을 설명한다.
---
# schedstat, /proc/<pid>/sched, Runtime Debugging

> 한 줄 요약: `runqlat`가 지연 분포를 보여 준다면, `schedstat`와 `/proc/<pid>/sched`는 그 지연이 어떤 태스크와 어떤 CPU에서 누적되고 있는지 더 가까이에서 보여 주는 관측창이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [Scheduler Classes, nice, RT Trade-offs](./scheduler-classes-nice-rt-tradeoffs.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: schedstat, /proc/PID/sched, proc pid sched, /proc/schedstat starter, schedstat beginner, when to move from /proc/<pid>/sched to /proc/schedstat, per-CPU imbalance safe reading, cpu hotspot delta reading, schedstat delta comparison, se.vruntime, sum_exec_runtime, nr_switches, run_delay, wait_sum, perf sched, scheduler counters, task scheduling stats

## 핵심 개념

스케줄러 병목을 볼 때 `top`이나 CPU%만으로는 부족하다. "누가 CPU를 많이 썼는가"보다 "누가 얼마나 오래 기다렸는가", "어디서 migration이 잦은가", "switch가 어떤 형태로 쌓였는가"가 더 중요할 때가 많다. 이때 자주 보는 인터페이스가 `/proc/<pid>/sched`, `/proc/schedstat`, `perf sched`다.

- `/proc/<pid>/sched`: 특정 태스크의 scheduler 관점 상태를 보여 주는 스냅샷이다
- `/proc/schedstat`: per-CPU 및 scheduler 도메인 관점의 누적 통계를 보여 준다
- `perf sched timehist`: sleep, wakeup, run, migration의 시간축을 보여 준다
- `runqlat`: runnable이 된 뒤 실행되기까지의 지연 분포를 보여 준다

왜 중요한가:

- 같은 p99 spike라도 lock handoff 문제인지, wakeup delay인지, migration churn인지 나눌 수 있다
- event loop 한 스레드만 밀리는지, CPU 전체가 흔들리는지 구분할 수 있다
- "CPU는 남는다"는 체감과 "특정 태스크는 계속 늦다"는 현상을 함께 설명할 수 있다

## 깊이 들어가기

### 1. `/proc/<pid>/sched`는 per-task scheduler 현미경이다

이 파일에는 태스크별 scheduler 상태와 누적 통계가 담긴다. 필드 이름과 형식은 커널 버전/빌드 옵션에 따라 조금 달라질 수 있지만, 운영에서 자주 보는 축은 비슷하다.

- `vruntime` 계열: 공정성 관점에서 얼마나 실행됐는지
- `sum_exec_runtime` 계열: 실제 실행 시간 누적
- `nr_switches`, voluntary/involuntary switch 계열: 얼마나 자주 전환됐는지
- wait/run delay 계열: runnable 또는 scheduling delay가 얼마나 쌓였는지

핵심은 절대값 암기가 아니라, spike 전후 delta 비교다.

### 2. `/proc/schedstat`는 "이 CPU 쪽 world에서 무슨 일이 있었나"를 본다

per-task 파일이 현미경이라면 `/proc/schedstat`는 CPU 단위의 망원경에 가깝다.

- 특정 CPU만 이상하게 바쁜가
- load balancing이 과도한가
- 한 코어에 burst가 집중되는가

특히 affinity, cpuset, IRQ locality가 얽힌 문제는 태스크 하나만 보는 것보다 CPU별 누적치가 더 빨리 힌트를 준다.

주의:

- 포맷은 커널 버전에 따라 달라질 수 있다
- 절대 의미보다 "이상한 CPU 하나가 튀는가" 같은 비교 관점이 더 중요하다

#### beginner follow-up: 언제 `/proc/<pid>/sched`에서 `/proc/schedstat`로 넓히나

처음 읽는 순서는 보통 [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)의 흐름이 안전하다. 즉 `load average`/`r` -> `/proc/<pid>/sched` -> 필요할 때만 `/proc/schedstat` 순서다.

`/proc/schedstat`로 넘어갈 만한 신호:

- suspect TID는 찾았는데 "왜 하필 이 CPU 쪽에서 밀리는가"가 안 보인다
- 여러 TID가 같이 delay를 보이는데 단일 hot thread 하나로 설명되지 않는다
- affinity, cpuset, IRQ locality, housekeeping CPU 같은 배치 문제를 의심한다
- `ps -eLo pid,tid,psr,comm`나 `mpstat -P ALL`에서 특정 CPU 집합으로 실행이 몰리는 것처럼 보인다

#### per-CPU imbalance를 안전하게 읽는 최소 규칙

- `/proc/schedstat`는 누적 counter라서 절대값 하나보다 짧은 간격 delta가 중요하다
- 같은 호스트, 같은 시간 구간의 형제 CPU끼리 먼저 비교한다. 다른 커널 버전이나 다른 서버와 숫자를 바로 맞대지 않는다
- `taskset`, cpuset, isolated/housekeeping CPU, IRQ/ksoftirqd 배치 때문에 원래 한 CPU가 뜨거운 경우를 먼저 뺀다
- 한 CPU의 delta가 형제 CPU보다 반복해서 더 빨리 늘고, 그 CPU에 문제 thread나 IRQ가 실제로 몰릴 때만 imbalance 후보로 본다. 모든 CPU가 함께 오르면 전체 load일 가능성이 크다

### 3. `perf sched timehist`가 타임라인을 채운다

`/proc` 파일은 스냅샷이지만, 운영 장애는 시간축 위에서 벌어진다. `perf sched timehist`는 다음을 붙여 준다.

- 언제 sleep했는가
- 언제 wakeup됐는가
- 실제 run까지 얼마나 걸렸는가
- 어떤 CPU로 migration됐는가

그래서 `/proc/<pid>/sched`로 suspect를 좁히고, `perf sched`로 타임라인을 맞추면 해석이 쉬워진다.

### 4. counter 하나로 결론내리면 쉽게 틀린다

예를 들어 `nr_switches`가 많아도 문제는 전환 횟수가 아니라 그 이유일 수 있다.

- voluntary switch가 많다: I/O wait나 lock wait일 수 있다
- involuntary switch가 많다: timeslice 경쟁이 심할 수 있다
- run delay가 크다: runnable queueing이 심할 수 있다
- migration이 잦다: locality 손실이 클 수 있다

즉 counter는 답이 아니라 질문 생성기다.

## 실전 시나리오

### 시나리오 1: event loop 하나만 자꾸 p99를 만든다

가능한 원인:

- 해당 TID의 run delay가 유독 높다
- switch는 많지 않은데 wakeup-to-run 지연이 누적된다
- migration이 잦아 cache locality가 깨진다

진단:

```bash
cat /proc/<tid>/sched
sudo runqlat-bpfcc -p <pid> 20
sudo perf sched timehist -p <pid> -- sleep 10
```

판단 포인트:

- 문제 TID만 scheduler delay 계열이 튀는가
- 전체 CPU 문제가 아니라 단일 hot thread 문제인가
- wakeup과 실제 run 사이 gap이 큰가

### 시나리오 2: CPU는 남는데 특정 코어만 이상하게 흔들린다

가능한 원인:

- affinity/cpuset/IRQ locality가 한쪽으로 쏠렸다
- 특정 CPU의 scheduler 누적 통계가 비정상적이다
- batch, kworker, softirq가 같은 코어를 흔든다

진단:

```bash
cat /proc/schedstat
mpstat -P ALL 1
ps -eLo pid,tid,psr,comm | head
```

### 시나리오 3: 락 문제처럼 보였는데 실제로는 owner thread가 늦다

가능한 원인:

- lock hold time보다 owner의 scheduling delay가 길다
- waiters는 `futex_wait`로 보이지만 root cause는 run queue 지연이다
- `perf sched`에서 unlock 뒤 next owner run까지 gap이 보인다

이 경우는 lock 디버깅과 scheduler 디버깅을 분리하면 안 된다.

## 코드로 보기

### per-task sched 보기

```bash
cat /proc/<pid>/sched
cat /proc/<tid>/sched
```

### per-CPU scheduler 통계

```bash
cat /proc/schedstat
```

### 타임라인으로 확인

```bash
sudo perf sched timehist -p <pid> -- sleep 10
```

### 해석 감각

```text
runqlat says: runnable delay exists
  -> /proc/<tid>/sched says: which thread accumulates it
  -> /proc/schedstat says: which CPU domain looks odd
  -> perf sched says: when and after what event it happened
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `/proc/<pid>/sched` | 빠르고 per-task로 좁히기 쉽다 | 필드 해석이 커널 버전에 따라 다를 수 있다 | suspect thread 확인 |
| `/proc/schedstat` | CPU별 이상 징후를 보기 쉽다 | 포맷이 덜 친절하다 | affinity/load-balance 문제 |
| `perf sched timehist` | 시간축 해석이 강하다 | 짧게 캡처하며 해석해야 한다 | wakeup/migration 분석 |
| `runqlat` | 지연 분포를 바로 본다 | 원인 구분은 추가 도구가 필요하다 | scheduler tail triage |

## 꼬리질문

> Q: `/proc/<pid>/sched`에서 무엇을 먼저 봐야 하나요?
> 핵심: 절대값 암기보다 run delay, switch 패턴, runtime delta를 spike 전후로 비교하는 것이 더 중요하다.

> Q: `/proc/schedstat`는 왜 보나요?
> 핵심: 문제를 특정 태스크 하나가 아니라 CPU/domain imbalance 관점으로 넓혀 보기 위해서다.

> Q: `runqlat`가 있으면 `/proc/<pid>/sched`는 필요 없나요?
> 핵심: 아니다. 전자는 분포, 후자는 어떤 태스크가 그 분포를 만드는지 좁히는 용도다.

## 한 줄 정리

`schedstat`와 `/proc/<pid>/sched`는 scheduler 병목을 "CPU가 바쁘다"가 아니라 "누가 어느 CPU에서 어떤 형태로 밀리고 있는가"로 바꿔 읽게 해 준다.
