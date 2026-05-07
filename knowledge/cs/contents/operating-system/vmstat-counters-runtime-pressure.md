---
schema_version: 3
title: vmstat Counters Runtime Pressure
concept_id: operating-system/vmstat-counters-runtime-pressure
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- vmstat-counters-pressure
- vmstat-r-b
- si-so-cs
- us-sy-wa
aliases:
- vmstat counters runtime pressure
- vmstat r b si so cs us sy wa
- CPU run queue swap IO context switch
- runtime pressure summary
- vmstat beginner to advanced
- system pressure counters
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/run-queue-load-average-cpu-saturation.md
- contents/operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md
- contents/operating-system/dirty-throttling-balance-dirty-pages-writeback-stalls.md
- contents/operating-system/kswapd-vs-direct-reclaim-latency.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
- contents/operating-system/context-switching-deadlock-lockfree.md
symptoms:
- vmstat 숫자는 보이지만 r, b, si, so, cs, us, sy, wa 중 어떤 조합이 신호인지 모른다.
- CPU, run queue, swap, I/O, context switch pressure를 빠르게 요약해야 한다.
- load average나 PSI를 보기 전에 1차 pressure snapshot이 필요하다.
expected_queries:
- vmstat counters로 CPU, run queue, swap, I/O, context switch pressure를 어떻게 빠르게 읽어?
- vmstat r b si so cs us sy wa는 각각 어떤 runtime pressure 신호야?
- load average와 PSI 보기 전에 vmstat로 어떤 noise와 signal을 가를 수 있어?
- dirty writeback이나 reclaim stall이 vmstat에 어떻게 보일 수 있어?
contextual_chunk_prefix: |
  이 문서는 vmstat를 CPU, run queue, swap, I/O, context switch를 한 번에 보는 빠른 pressure summary로
  설명한다. counter 의미를 알아야 noise가 아닌 signal을 읽을 수 있다.
---
# vmstat Counters, Runtime Pressure

> 한 줄 요약: `vmstat`는 CPU, run queue, swap, I/O, context switch를 한 번에 보는 가장 빠른 압력 요약이며, 숫자의 의미를 알아야 노이즈가 아닌 신호를 읽을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)

> retrieval-anchor-keywords: vmstat, r, b, si, so, bi, bo, us, sy, id, wa, st, cs, free pages, runnable, swap in, swap out, load average triage, vmstat r b wa triage

## 핵심 개념

`vmstat`는 시스템 압력을 한 줄로 보여준다. 각 컬럼은 단순 숫자가 아니라 현재 병목의 방향을 알려준다.

- `r`: runnable task 수다
- `b`: uninterruptible sleep task 수다
- `si`/`so`: swap in/out이다
- `bi`/`bo`: block I/O다
- `us`/`sy`/`id`/`wa`/`st`: CPU 시간 분포다
- `cs`: context switch 수다

왜 중요한가:

- CPU인지 메모리인지 I/O인지 빠르게 감을 잡을 수 있다
- 높은 `load average`가 saturation인지 blocked wait인지 1차 분리를 할 수 있다
- `vmstat`은 가장 빠른 1차 triage 도구다
- PSI, perf, iostat로 넘어가기 전에 방향을 잡을 수 있다

이 문서는 [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)와 [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)를 숫자 해석 관점에서 묶는다.

## 깊이 들어가기

### 1. `r`은 runnable pressure다

`r`이 높으면 CPU를 기다리는 태스크가 많다는 뜻이다.

- run queue pressure를 시사한다
- CPU saturation과 관련이 있다
- throttling과 함께 보면 더 좋다

### 2. `b`는 막혀 있는 태스크다

`b`가 올라가면 I/O나 reclaim 같은 uninterruptible wait을 의심한다.

- disk I/O
- page reclaim
- filesystem wait

### 3. `si`/`so`는 swap pressure다

swap in/out이 지속되면 memory pressure와 latency가 함께 커진다.

### 4. `cs`는 스위칭 과부하를 보여준다

context switch가 많으면 스레드가 너무 많거나 경합이 심할 수 있다.

## 실전 시나리오

### 시나리오 1: CPU는 낮은데 서버가 느리다

가능한 원인:

- `b`가 높다
- `wa`가 높다
- reclaim이나 I/O 대기가 길다

진단:

```bash
vmstat 1
```

### 시나리오 2: CPU는 높은데 처리량은 낮다

가능한 원인:

- `r`이 높다
- `cs`가 많다
- run queue와 context switch가 병목이다

### 시나리오 3: 메모리 압박이 보인다

가능한 원인:

- `si`/`so`가 늘어난다
- reclaim이 진행된다
- swap이 시작되었다

이때는 [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)와 같이 본다.

## 코드로 보기

### 기본 triage

```bash
vmstat 1
```

### 한 줄 해석 감각

```text
r high -> CPU runnable pressure
b high -> blocked tasks
si/so high -> swap pressure
wa high -> IO wait
cs high -> scheduler churn
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| vmstat 중심 | 빠르게 방향을 잡는다 | 세부 원인은 못 준다 | 1차 triage |
| PSI 병행 | stall 시간을 더 정확히 본다 | 해석이 더 필요하다 | 운영 관측 |
| perf/iostat 전환 | 원인 추적이 깊다 | 비용과 복잡도 증가 | 상세 분석 |

## 꼬리질문

> Q: `r`과 `b`의 차이는?
> 핵심: `r`은 CPU를 기다리는 runnable, `b`는 I/O나 reclaim으로 막힌 태스크다.

> Q: `si`/`so`가 늘면 무엇을 의심하나요?
> 핵심: swap pressure와 memory pressure를 의심한다.

> Q: `vmstat`만으로 충분한가요?
> 핵심: 아니다. 방향을 잡고 PSI나 perf로 넘어가는 용도다.

## 한 줄 정리

vmstat는 시스템 압력의 첫 신호를 읽는 도구이며, `r`, `b`, `si/so`, `wa`, `cs`를 연결해 보면 병목 방향을 빠르게 잡을 수 있다.
