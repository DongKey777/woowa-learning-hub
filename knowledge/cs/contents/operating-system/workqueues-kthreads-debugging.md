---
schema_version: 3
title: Workqueues Kthreads Debugging
concept_id: operating-system/workqueues-kthreads-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- workqueues-kthreads
- kernel-worker-overload
- deferred-work-queue
- kthread-backlog
aliases:
- workqueues kthreads debugging
- kernel worker overload
- deferred work queue
- kthread backlog
- workqueue saturation
- hidden kernel worker
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/kworker-saturation-runtime-diagnostics.md
- contents/operating-system/softirq-hardirq-latency-server-debugging.md
- contents/operating-system/ebpf-perf-strace-production-tracing.md
- contents/operating-system/cpu-affinity-irq-affinity-core-locality.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
symptoms:
- user request path에서 떼어낸 kernel deferred work가 workqueue/kthread backlog로 밀린다.
- kworker saturation을 봤지만 어떤 kernel work가 쌓였는지 더 좁혀야 한다.
- softirq follow-up이나 reclaim work가 hidden worker overload로 나타난다.
expected_queries:
- workqueue와 kthread는 kernel이 오래 걸리는 일을 user path에서 떼어내는 실행 단위야?
- kworker saturation을 workqueues와 kthreads debugging으로 어떻게 좁혀?
- deferred work backlog가 application p99 latency를 만들 수 있어?
- eBPF perf로 kernel worker overload를 어떻게 관측해?
contextual_chunk_prefix: |
  이 문서는 workqueue와 kthread를 kernel이 오래 걸리는 work를 user/request path에서 떼어내 처리하는
  execution units로 설명한다. bottleneck이 생기면 hidden kernel worker overload로 드러난다.
---
# Workqueues, Kthreads, Debugging

> 한 줄 요약: workqueue와 kthread는 커널이 오래 걸리는 일을 유저 경로에서 떼어내기 위해 쓰는 실행 단위이고, 병목이 생기면 커널 내부의 숨은 worker 과부하가 드러난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Softirq, Hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)

> retrieval-anchor-keywords: workqueue, kthread, kernel worker, kworker, unbound workqueue, flush_work, delayed_work, /proc/workqueue, hidden worker

## 핵심 개념

커널은 즉시 처리하지 않아도 되는 작업을 workqueue나 kthread로 넘긴다. 이들은 커널 내부 worker처럼 움직이며, 병목이나 폭주가 생기면 latency와 CPU 사용이 예상과 다르게 보일 수 있다.

- `workqueue`: 커널이 비동기 작업을 보내는 큐다
- `kthread`: 커널 스레드다
- `kworker`: workqueue를 실제로 실행하는 worker다

왜 중요한가:

- I/O completion, reclaim, filesystem maintenance 같은 작업이 worker로 밀릴 수 있다
- 유저 스레드가 아니라 커널 worker가 병목일 수 있다
- "CPU는 낮은데 왜 늦지?"의 답이 될 수 있다

이 문서는 [softirq, hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)와 [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)를 커널 worker 관점으로 연결한다.

## 깊이 들어가기

### 1. workqueue는 커널의 백그라운드 작업대다

커널은 긴 일을 바로 하지 않고 work item으로 넘긴다.

- filesystem flush
- reclaim 보조 작업
- deferred maintenance
- I/O 후속 처리

### 2. kthread는 커널 전용 실행 흐름이다

일부 작업은 커널 스레드로 따로 돈다.

- kswapd 같은 메모리 관련 스레드
- 특정 driver worker
- daemon-like kernel activity

### 3. worker가 막히면 유저도 영향을 받는다

커널 worker가 밀리면 다음이 늦어진다.

- completion
- reclaim
- filesystem housekeeping
- deferred flush

즉 유저 스레드가 멀쩡해도 시스템은 느려질 수 있다.

### 4. unbound workqueue는 유연하지만 예측이 어렵다

- 특정 CPU에 묶이지 않는다
- load balance가 좋을 수 있다
- 하지만 locality와 병목 추적이 어려울 수 있다

## 실전 시나리오

### 시나리오 1: I/O 완료가 늦는데 user-space는 한가하다

가능한 원인:

- worker가 backlog를 쌓고 있다
- workqueue가 밀린다
- softirq 이후 후속 작업이 늦는다

진단:

```bash
ps -eLo pid,tid,cls,rtprio,pri,psr,comm | grep kworker | head
cat /proc/workqueue/* 2>/dev/null | head
```

### 시나리오 2: reclaim이 늦고 메모리 압박이 길다

가능한 원인:

- kswapd가 busy하다
- shrinker/worker가 따라잡지 못한다
- workqueue 폭주가 섞인다

### 시나리오 3: 특정 커널 이벤트 후 전체 지연이 튄다

가능한 원인:

- deferred work가 한꺼번에 실행된다
- worker가 CPU affinity와 안 맞는다
- hot core에서 커널 worker가 몰린다

이 경우는 [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)와 같이 본다.

## 코드로 보기

### kworker 확인

```bash
ps -eLo pid,tid,comm | grep kworker | head
```

### workqueue 관찰 힌트

```bash
ls /sys/kernel/debug/workqueue 2>/dev/null
```

### 단순 모델

```text
kernel event
  -> deferred to workqueue/kthread
  -> worker backlog grows
  -> completion/reclaim latency increases
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| workqueue 사용 | 즉시 경로를 짧게 한다 | backlog 관리가 필요하다 | deferred work |
| kthread 전용화 | 제어가 분명하다 | 고정 비용이 든다 | 장기 작업 |
| unbound worker | 유연하다 | 추적이 어려울 수 있다 | 일반 커널 백그라운드 |
| affinity 고정 | locality가 좋다 | hot spot 위험 | latency-sensitive kernel work |

## 꼬리질문

> Q: workqueue는 왜 필요한가요?
> 핵심: 오래 걸리는 일을 즉시 경로에서 떼어내기 위해서다.

> Q: kworker가 보이면 문제인가요?
> 핵심: 아니다. 다만 backlog나 지연이 커지면 병목 신호가 된다.

> Q: user-space가 느린데 workqueue를 왜 보나요?
> 핵심: completion과 reclaim 같은 커널 후속 작업이 영향을 줄 수 있기 때문이다.

## 한 줄 정리

workqueue와 kthread는 커널의 deferred execution 경로이며, backlog가 쌓이면 유저 경로가 아닌 커널 worker가 성능 병목이 될 수 있다.
