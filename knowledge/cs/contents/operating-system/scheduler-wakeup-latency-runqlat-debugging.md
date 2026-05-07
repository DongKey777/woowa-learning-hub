---
schema_version: 3
title: Scheduler Wakeup Latency runqlat Queueing Debugging
concept_id: operating-system/scheduler-wakeup-latency-runqlat-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- scheduler-wakeup-latency
- runqlat
- wakeup-to-run
- latency
aliases:
- scheduler wakeup latency
- runqlat debugging
- wakeup-to-run latency
- runnable queueing delay
- event loop p99 scheduler
- lock handoff scheduler delay
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/run-queue-load-average-cpu-saturation.md
- contents/operating-system/scheduler-observation-starter-guide.md
- contents/operating-system/schedstat-proc-sched-runtime-debugging.md
- contents/operating-system/lock-contention-futex-offcpu-debugging.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
- contents/operating-system/ebpf-perf-strace-production-tracing.md
symptoms:
- CPU 평균 사용률은 낮지만 runnable task가 wakeup 후 실제 CPU를 받기까지 밀린다.
- event loop, lock handoff, request dispatch p99가 scheduler wakeup-to-run delay로 무너진다.
- runqlat tail과 per-task schedstat를 연결해 원인을 좁혀야 한다.
expected_queries:
- runqlat은 runnable task가 wakeup된 뒤 CPU를 받기까지의 latency를 어떻게 보여줘?
- CPU 평균 사용률이 낮아도 scheduler wakeup latency 때문에 p99가 무너질 수 있어?
- event loop나 lock handoff 지연을 wakeup-to-run tail로 어떻게 확인해?
- runqlat과 schedstat, PSI를 함께 보는 scheduler debugging flow는?
contextual_chunk_prefix: |
  이 문서는 CPU average utilization이 낮아도 runnable task가 wakeup된 뒤 실제 CPU를 받기까지
  queueing되면 event loop, lock handoff, request dispatch p99가 무너질 수 있다는 scheduler
  wakeup latency playbook이다.
---
# Scheduler Wakeup Latency, runqlat, Queueing Debugging

> 한 줄 요약: CPU 평균 사용률이 낮아도 runnable 태스크가 wakeup된 뒤 실제로 CPU를 받기까지 밀리면 event loop, lock handoff, request dispatch의 p99는 쉽게 무너진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: runqlat, wakeup latency, runnable latency, sched_wakeup, sched_switch, run queue delay, queueing delay, wakeup-to-run, CPU wait time, scheduler latency

## 핵심 개념

태스크가 깨어났다고 해서 바로 실행되는 것은 아니다. `epoll_wait`, `futex`, softirq completion, timer expiry 같은 이벤트가 태스크를 runnable 상태로 바꿔도, 실제 CPU를 받기까지는 run queue에서 다시 기다릴 수 있다. 이 gap이 wakeup latency이며 `runqlat` 같은 도구가 보는 대상이다.

- `wakeup`: 태스크가 sleeping에서 runnable 후보로 돌아오는 순간이다
- `run queue`: runnable 태스크가 CPU를 기다리는 큐다
- `wakeup-to-run latency`: 깨어난 시점부터 실제 실행 시점까지의 지연이다
- `runqlat`: 이 지연 분포를 보는 운영 도구/관점이다

왜 중요한가:

- 요청 스레드는 이미 깨어났는데 핸들러가 늦게 실행될 수 있다
- 락이 풀렸는데 next owner가 CPU를 못 받아 convoy가 길어질 수 있다
- 평균 CPU 사용률은 정상처럼 보여도 p99만 나빠지는 이유를 설명할 수 있다

## 깊이 들어가기

### 1. wakeup latency는 "CPU가 없어서"만 생기지 않는다

가장 단순한 원인은 runnable 태스크가 많아 run queue가 길어진 경우다. 하지만 현실에서는 더 많은 요인이 섞인다.

- 같은 코어에 runnable 태스크가 몰렸다
- 높은 우선순위 태스크나 RT 태스크가 먼저 실행된다
- cgroup quota/throttling으로 runnable인데도 못 뛴다
- CPU affinity/cpuset 제한 때문에 비어 있는 코어가 있어도 못 간다
- softirq, interrupt, kernel worker가 짧게 끊어 먹는다

즉 "CPU%가 낮다"만으로 스케줄러 대기를 배제하면 안 된다.

### 2. event loop와 lock handoff는 wakeup latency에 민감하다

다음 구조는 특히 wakeup-to-run 지연의 영향을 크게 받는다.

- single-threaded event loop
- accept loop와 worker handoff
- mutex unlock 뒤 기다리던 owner handoff
- timerfd/signalfd/eventfd 기반 control plane

이 구조들은 실제 작업 시간보다 "깨웠는데 언제부터 움직였는가"가 p99에 더 큰 영향을 주기도 한다.

### 3. load average보다 분포가 중요하다

짧은 burst에서는 1분 load average가 거의 안 움직일 수 있다. 하지만 runqlat 히스토그램은 바로 흔들린다.

- 평균 부하는 정상처럼 보인다
- p50은 안정적이다
- 특정 시간대 p95/p99만 치솟는다

그래서 wakeup latency는 평균 지표보다 분포형 지표로 보는 것이 훨씬 유용하다.

### 4. queueing은 계층을 타고 전염된다

run queue에서 한 번 밀리면 그 지연이 다른 대기로 이어진다.

- lock owner가 늦게 실행된다
- 대기 중인 다른 스레드가 더 오래 잔다
- socket read/write가 늦어져 peer latency가 는다
- timeout과 retry가 겹치며 전체 queueing이 커진다

즉 wakeup latency는 scheduler 내부 문제가 아니라 요청 경로 전체의 queueing 증폭점이다.

## 실전 시나리오

### 시나리오 1: `epoll_wait`에서 깬 뒤 handler 실행이 수 ms 늦다

가능한 원인:

- accept/worker 수가 너무 많아 run queue가 길다
- softirq, kworker, batch가 같은 코어를 흔든다
- cpuset이나 affinity 때문에 실제 사용할 CPU가 적다

진단:

```bash
sudo runqlat-bpfcc -p <pid> 30
sudo perf sched timehist -p <pid> -- sleep 15
vmstat 1
cat /proc/pressure/cpu
```

판단 포인트:

- runqlat 히스토그램 tail이 burst 때만 두꺼워지는가
- `r` 값과 cpu PSI `some`이 같이 오르는가
- CPU 평균보다 wakeup-to-run 지연이 먼저 튀는가

### 시나리오 2: 락은 짧게 잡는데도 요청이 길게 밀린다

가능한 원인:

- 락 owner가 unlock 후 곧바로 next owner가 스케줄되지 않는다
- lock hold time보다 scheduler queueing delay가 길다
- convoy가 생겨 대기열이 꼬리를 문다

이 경우는 락 구현보다 scheduler queueing이 더 큰 병목일 수 있다.

### 시나리오 3: 노드 CPU는 남는데 특정 컨테이너만 느리다

가능한 원인:

- `cpu.max` throttling
- `cpuset.cpus` 제한
- 같은 cgroup 내부 burst가 특정 코어에 몰림

이때는 global run queue 감각보다 cgroup/affinity 경계를 같이 봐야 한다.

## 코드로 보기

### run queue delay 보기

```bash
sudo runqlat-bpfcc -p <pid> 30
sudo perf sched timehist -p <pid> -- sleep 15
```

### `/proc/<pid>/sched` 감각

```bash
cat /proc/<pid>/sched
```

볼 때의 감각:

- 실행 시간만이 아니라 대기 시간, migration, scheduling 통계가 같이 보인다
- 절대값보다 spike 시간대 비교가 중요하다

### mental model

```text
event arrives
  -> task wakes up
  -> task enters run queue
  -> waits behind runnable work
  -> finally runs handler

tail latency = wakeup source latency + run queue delay + actual handler time
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 워커 수 축소 | run queue churn을 줄인다 | 순간 병렬성이 줄 수 있다 | herd/queueing이 심할 때 |
| affinity/cpuset 조정 | locality와 예측성이 좋아진다 | 잘못 잡으면 더 막힌다 | noisy neighbor 분리 |
| quota 완화 | runnable delay를 줄일 수 있다 | 멀티테넌트 공정성이 약해진다 | cgroup burst 문제 |
| event loop/worker 분리 | 제어 경로를 단순화한다 | 구조가 복잡해질 수 있다 | mixed workload |

## 꼬리질문

> Q: CPU 사용률이 낮은데도 wakeup latency가 높을 수 있나요?
> 핵심: 그렇다. affinity, throttling, burst queueing, 높은 우선순위 태스크 때문에 runnable 상태에서 오래 밀릴 수 있다.

> Q: runqlat는 무엇을 보여 주나요?
> 핵심: 태스크가 runnable이 된 뒤 실제로 스케줄되기까지의 지연 분포를 보여 준다.

> Q: lock contention처럼 보이는 문제도 scheduler 문제일 수 있나요?
> 핵심: 그렇다. lock hold time이 짧아도 next owner가 늦게 실행되면 체감은 긴 lock wait처럼 보일 수 있다.

## 한 줄 정리

wakeup latency는 "깨웠다"와 "실제로 돌았다" 사이의 보이지 않는 큐잉 비용이며, runqlat를 보면 평균 CPU로는 안 보이던 p99 scheduler 병목이 드러난다.
