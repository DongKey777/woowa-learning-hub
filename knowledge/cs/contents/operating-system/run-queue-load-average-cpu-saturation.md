---
schema_version: 3
title: Run Queue Load Average CPU Saturation
concept_id: operating-system/run-queue-load-average-cpu-saturation
canonical: true
category: operating-system
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
review_feedback_tags:
- run-queue-load
- average-cpu-saturation
- runnable-tasks-backlog
- cpu-saturation-diagnostics
aliases:
- run queue load average CPU saturation
- runnable tasks backlog
- CPU saturation diagnostics
- load average interpretation
- scheduler contention
- vmstat r
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/operating-system/context-switching-deadlock-lockfree.md
- contents/operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md
- contents/operating-system/scheduler-observation-starter-guide.md
- contents/operating-system/scheduler-wakeup-latency-runqlat-debugging.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
- contents/operating-system/cgroup-cpu-throttling-quota-runtime-debugging.md
expected_queries:
- run queue, load average, CPU saturation을 어떻게 구분해?
- CPU가 바쁜지 runnable task가 쌓였는지 thread가 blocked인지 어떻게 봐?
- vmstat r과 load average로 scheduler contention을 해석하는 법은?
- cgroup throttling과 I/O wait 때문에 load average가 높은 경우를 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 CPU가 바쁜지, runnable task가 run queue에 쌓였는지, thread가 I/O나 lock에서
  blocked인지 구분해야 latency 원인을 정확히 잡을 수 있다는 scheduler deep dive다.
---
# Run Queue, Load Average, CPU Saturation

> 한 줄 요약: CPU가 바쁜지, 스레드가 막혔는지, 아니면 runnable 태스크가 쌓였는지를 구분해야 지연의 원인을 정확히 잡을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
> - [I/O 모델과 이벤트 루프](./io-models-and-event-loop.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)

> retrieval-anchor-keywords: run queue, load average, cpu saturation, runnable tasks, queueing delay, runqlat, context switch, CPU pressure, runnable latency, load average false positive, cpu saturation vs throttling

## 핵심 개념

`run queue`는 지금 CPU를 기다리는 runnable 태스크의 대기열이다.  
`load average`는 단순 CPU 사용률이 아니라, 일정 시간 동안 CPU를 기다리거나 I/O 상태에 있던 태스크의 평균적인 부담을 보여주는 지표다.

왜 중요한가:

- CPU 사용률 100%는 이미 너무 늦은 신호일 수 있다.
- runnable 태스크가 많아도 CPU가 부족하면 처리량보다 대기만 늘어난다.
- 반대로 load average가 높아도 I/O 대기 때문에 CPU는 놀 수 있다.

`CPU saturation`은 CPU가 더 이상 추가 작업을 빨리 처리하지 못하는 상태다.  
이때는 평균 응답 시간보다 `p95/p99`가 먼저 무너진다.

## 깊이 들어가기

### 1. load average가 의미하는 것

Linux의 load average는 보통 `1m / 5m / 15m` 기준으로 관찰한다.  
여기서 중요한 건 "CPU 점유율"이 아니라 "대기 중인 태스크의 압력"이다.

- runnable 태스크
- uninterruptible sleep 상태의 태스크
- 스케줄러가 실행할 후보

이 부담이 높아지면 CPU 코어 수보다 runnable 태스크 수가 많아지고, 스케줄링 지연이 늘어난다.

### 2. run queue와 saturation의 관계

각 CPU 코어는 자기 run queue를 가진다.  
태스크가 많아질수록 다음이 일어난다.

- 태스크가 더 오래 runnable 상태로 대기한다
- context switch가 늘어난다
- 캐시 locality가 깨진다
- tail latency가 커진다

이 상태를 더 직접적으로 보면 wakeup 이후 실제 실행까지의 지연, 즉 `runqlat` 분포가 두꺼워진다.

즉 saturation은 CPU를 "더 쓰는" 문제가 아니라, 이미 쓰는 CPU를 더 잘게 나눠 쓰면서 생기는 병목이다.

### 3. I/O wait, throttling, CPU saturation을 구분해야 한다

load average가 높아도 원인이 다를 수 있다.

- CPU saturation: runnable 태스크가 많음
- cgroup throttling: 태스크는 더 일하고 싶지만 quota/runtime 예산이 먼저 바닥남
- I/O saturation: 디스크/네트워크 대기 태스크가 많음

즉 high load average를 "scheduler contention" 하나로 뭉개면 쉽게 틀린다.

- saturation인데 스레드를 늘리면 run queue와 context switch가 더 늘 수 있다
- throttling인데 nice만 조정하면 quota 제한은 그대로 남는다
- I/O wait인데 CPU를 먼저 늘리면 blocked task만 더 쌓일 수 있다

세 갈래를 빠르게 나누는 초보자용 기준은 [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)에 따로 정리했다.

## 실전 시나리오

### 시나리오 1: 스레드를 늘렸더니 latency가 악화됨

Tomcat worker를 늘렸지만 p99가 더 나빠진 경우다.  
원인은 보통 다음 중 하나다.

- run queue가 코어 수를 크게 초과함
- context switch와 cache miss가 늘어남
- DB나 외부 API 대기가 CPU를 잠식함

진단:

```bash
uptime
top -H
vmstat 1
mpstat -P ALL 1
```

확인 포인트:

- `load average`가 코어 수보다 유의미하게 큰가
- `r` 값이 지속적으로 높아지는가
- `cs`(context switch)가 폭증하는가

### 시나리오 2: CPU는 60%인데도 서버가 느림

이 경우는 saturation이 아니라 대기 구조 문제일 수 있다.

- lock 경합
- page cache miss
- blocking I/O
- GC stop-the-world

CPU 사용률만 보면 정상처럼 보이지만 runnable 태스크는 밀릴 수 있다.

## 코드로 보기

### 운영 진단용 커맨드

```bash
# load average와 runnable 대기 확인
uptime
vmstat 1

# CPU별 사용률과 steal/iowait 확인
mpstat -P ALL 1

# 프로세스/스레드 단위 보기
top -H -p <pid>
```

### 아주 단순한 saturation 감각 모델

```text
effective throughput ≈ min(CPU 코어 수, runnable task 처리 속도)

queueing delay ≈ runnable task 수 / CPU 서비스율
```

실제로는 lock, cache, I/O가 섞이지만, 첫 진단은 이 단순 모델로 충분하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 스레드 수 증가 | 처리량이 잠시 올라갈 수 있음 | saturation과 context switch 악화 | I/O-bound가 확실할 때 |
| CPU 증설 | 단순하고 직접적 | 병목이 CPU가 아닐 수 있음 | runnable 태스크가 실제로 코어를 압도할 때 |
| 비동기/이벤트 루프 | runnable 대기 감소 | 코드 복잡도 증가 | I/O 대기가 지배적일 때 |
| 작업 분리/큐잉 | burst 흡수 | 지연 증가 | 피크가 크고 즉시 처리 불필요할 때 |

## 꼬리질문

> Q: load average가 높으면 무조건 CPU가 바쁜가?
> 의도: load average와 CPU 사용률의 차이 이해 여부 확인
> 핵심: runnable 태스크와 I/O 대기 태스크를 구분할 수 있어야 한다.

> Q: run queue가 길어지면 왜 p99가 먼저 무너지는가?
> 의도: queueing delay와 tail latency 이해 여부 확인
> 핵심: 평균이 아니라 대기열 분포가 지연을 만든다.

> Q: 스레드를 늘렸는데 왜 처리량이 줄 수 있는가?
> 의도: saturation과 context switch 비용 이해 여부 확인
> 핵심: runnable 태스크가 너무 많으면 CPU가 일보다 전환에 더 시간을 쓴다.

## 한 줄 정리

load average는 CPU 사용률이 아니라 대기 압력의 신호이고, run queue가 길어지면 서버는 보통 먼저 tail latency부터 무너진다.
