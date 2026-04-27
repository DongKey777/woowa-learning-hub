# Scheduler Observation Starter Guide

> 한 줄 요약: scheduler basics를 막 읽은 직후에는 `load average`와 `vmstat r`로 전체 압력을 보고, `/proc/<pid>/sched`로 누가 밀리는지 좁힌 뒤, 그 한 태스크 시야가 부족할 때만 `/proc/schedstat`로 CPU 쏠림을 확인하고, 마지막에 `runqlat`로 wakeup-to-run tail을 검증하는 순서가 가장 안전하다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)


retrieval-anchor-keywords: scheduler observation starter guide basics, scheduler observation starter guide beginner, scheduler observation starter guide intro, operating system basics, beginner operating system, 처음 배우는데 scheduler observation starter guide, scheduler observation starter guide 입문, scheduler observation starter guide 기초, what is scheduler observation starter guide, how to scheduler observation starter guide
> 관련 문서:
> - [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md)
> - [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [Cgroup CPU Throttling, Quota, Runtime Debugging](./cgroup-cpu-throttling-quota-runtime-debugging.md)

> retrieval-anchor-keywords: scheduler observation starter guide, scheduler observability beginner, run queue reading, load average reading, vmstat r meaning, proc pid sched reading, /proc/PID/sched starter, /proc/schedstat starter, schedstat beginner, when to move to /proc/schedstat, per-CPU imbalance beginner, per-CPU imbalance safe reading, cpu hotspot safe reading, runqlat starter, wakeup to run latency, scheduler triage, runnable backlog, cpu saturation checklist, scheduler debugging first five minutes, beginner handoff box, primer handoff box, scheduler observation 다음 문서

## 먼저 잡는 멘탈 모델

scheduler basics를 읽고 나면 가장 먼저 막히는 지점은 "그래서 운영에서는 뭘 보면 되나요?"다.
이때 다섯 가지 관측창을 한 묶음으로 보면 된다.

| 관측창 | 먼저 답하는 질문 | 초보자가 자주 헷갈리는 지점 |
|---|---|---|
| `uptime`의 `load average` | 최근 1/5/15분 동안 시스템 압력이 컸는가 | CPU 사용률과 같은 값이 아니다 |
| `vmstat 1`의 `r` | 지금 이 순간 runnable 태스크가 쌓였는가 | per-CPU run queue 전체를 그대로 보여 주는 숫자는 아니다 |
| `/proc/<pid>/sched` | 어떤 PID/TID가 실제로 많이 기다렸는가 | 필드 이름보다 spike 전후 delta 비교가 중요하다 |
| `/proc/schedstat` | 한 태스크 시야를 넘어 CPU별 쏠림이 있는가 | 포맷 암기보다 짧은 간격 delta와 CPU 간 비교가 더 중요하다 |
| `runqlat` | 깨어난 뒤 실제 실행되기까지 tail이 두꺼운가 | 분포를 보여 줄 뿐 root cause를 단독으로 증명하진 않는다 |

핵심은 CPU%만 보지 않는 것이다.

- `load average`는 "압력이 있었는가"를 보여 준다
- `r`은 "지금 runnable 대기가 있는가"를 보여 준다
- `/proc/<pid>/sched`는 "누가 밀리는가"를 보여 준다
- `/proc/schedstat`는 "어느 CPU 쪽이 이상한가"를 보여 준다
- `runqlat`는 "그 대기가 tail latency로 드러나는가"를 보여 준다

## 1. 먼저 run queue와 load average를 넓게 본다

입문 단계에서는 정교한 scheduler 내부 구조보다 "시스템이 전체적으로 CPU 경쟁 상태인가"를 먼저 판단하는 편이 안전하다.

```bash
uptime
vmstat 1
```

읽는 감각:

- `load average`가 코어 수보다 오래 높게 유지되면 압력이 지속된 것이다
- `vmstat`의 `r`이 반복해서 높으면 runnable 태스크가 지금도 CPU를 기다린다
- `r`은 순간치이고 `load average`는 완만한 평균이므로, burst성 문제는 `r`이 먼저 반응할 수 있다

주의:

- `load average`가 높다고 무조건 CPU saturation은 아니다
- Linux load average에는 runnable뿐 아니라 uninterruptible sleep 계열 부담도 섞일 수 있다
- 그래서 `load average`만 보고 "CPU가 부족하다"로 단정하면 쉽게 틀린다

초보자용 첫 판단은 이 정도면 충분하다.

- `load average`도 높고 `r`도 계속 높다: scheduler queueing을 의심한다
- `load average`는 높은데 `r`은 낮다: I/O wait, reclaim, throttling 같은 다른 축도 본다
- 둘 다 조용한데 latency만 높다: scheduler보다 lock, GC, downstream I/O가 더 유력하다

## 2. 그다음 `/proc/<pid>/sched`로 "누가" 밀리는지 좁힌다

전체 압력이 보여도 실제로는 특정 event loop thread, accept loop, worker 하나만 유독 늦을 수 있다. 이때는 `/proc/<pid>/sched` 또는 `/proc/<tid>/sched`가 유용하다.

```bash
cat /proc/<pid>/sched
cat /proc/<tid>/sched
```

읽는 감각:

- `sum_exec_runtime` 계열은 실제로 얼마나 실행됐는지 감을 준다
- `nr_switches` 계열은 전환이 잦은지 보여 준다
- wait/run delay 계열은 runnable 대기가 누적되는지 보여 준다
- PID보다 TID가 더 유용할 때가 많다. event loop나 hot worker는 보통 thread 하나가 문제를 만든다

여기서 중요한 것은 필드 암기가 아니라 비교다.

- 정상 시간대 `/proc/<tid>/sched`
- 느린 시간대 `/proc/<tid>/sched`

이 두 스냅샷을 비교해 delay와 switch 패턴이 어떻게 달라졌는지를 본다. 절대값 하나만 읽고 결론내리면 커널 버전 차이와 워크로드 특성에 쉽게 속는다.

## 3. `/proc/schedstat`는 per-task 시야가 부족할 때만 꺼낸다

`/proc/<pid>/sched`로 suspect TID를 찾았는데도 "왜 하필 이 CPU 쪽에서 밀리는가"가 안 보이면 그때 `/proc/schedstat`로 시야를 CPU 쪽으로 넓힌다. 초보자가 처음부터 `/proc/schedstat`부터 읽으면 포맷 차이와 누적 counter 때문에 쉽게 길을 잃는다.

이 파일로 넘어갈 신호:

- 여러 TID가 같이 delay를 보이는데 단일 hot thread 하나로 설명되지 않는다
- `ps -eLo pid,tid,psr,comm`에서 특정 `PSR`이나 CPU 집합으로 실행이 자꾸 몰린다
- affinity, cpuset, IRQ locality, housekeeping CPU 같은 배치 문제를 의심한다
- `/proc/<pid>/sched`는 이상한데 "왜 그 CPU가 뜨거운가"라는 질문이 남는다

```bash
cat /proc/schedstat
sleep 2
cat /proc/schedstat
mpstat -P ALL 1 3
ps -eLo pid,tid,psr,comm | head
```

안전하게 읽는 규칙:

- `/proc/schedstat`는 부팅 이후 누적치다. 절대값 하나보다 짧은 간격 두 스냅샷의 delta를 본다
- CPU 간 비교를 먼저 한다. 다른 서버, 다른 커널 버전, 다른 부하 구간과 숫자를 직접 비교하지 않는다
- `taskset`, cpuset, isolated/housekeeping CPU, IRQ/ksoftirqd 배치처럼 원래 한 코어가 뜨거워질 이유가 있는지 먼저 뺀다
- 한 CPU의 delta가 같은 구간의 형제 CPU보다 반복해서 더 빨리 늘고, 그 CPU에 문제 thread나 IRQ가 실제로 몰릴 때만 imbalance 후보로 본다. 모든 CPU가 함께 오르면 그냥 전체 load다

## 4. 마지막으로 `runqlat`로 wakeup-to-run 분포를 확인한다

`load average`와 `vmstat r`는 넓은 힌트고, `/proc/<pid>/sched`는 태스크 단위 현미경이다. 여기에 `/proc/schedstat`가 CPU별 쏠림 여부를 보태 준다. 그래도 "정말 scheduler tail이 요청 지연을 만들었는가"는 분포를 봐야 더 분명해진다. 그때 `runqlat`를 쓴다.

```bash
sudo runqlat-bpfcc -p <pid> 15
```

읽는 감각:

- 히스토그램 tail이 두꺼워지면 runnable 이후 실제 실행까지 오래 밀린다는 뜻이다
- 평소에는 얇은데 spike 구간만 튀면 burst성 queueing일 수 있다
- 평균 CPU 사용률이 낮아도 `runqlat` tail은 두꺼워질 수 있다

`runqlat`가 특히 잘 드러내는 경우:

- `epoll_wait`에서 깬 뒤 handler 실행이 늦다
- lock owner가 깨어났는데 next handoff가 늦다
- worker 수를 늘린 뒤 p99만 나빠졌다

반대로 `runqlat`가 조용한데 latency가 높다면, scheduler는 1차 원인이 아닐 가능성이 크다.

## 5. 이 다섯 관측창을 읽는 가장 단순한 순서

운영에서 초보자가 바로 따라 하기 좋은 순서는 아래다.

1. `uptime`로 `load average`를 본다.
2. `vmstat 1`로 지금 runnable backlog가 반복되는지 본다.
3. 의심 PID/TID를 정해 `/proc/<pid>/sched` 또는 `/proc/<tid>/sched`를 본다.
4. per-task 시야만으로 설명이 안 되면 `/proc/schedstat`, `mpstat`, `PSR`를 같이 본다.
5. `runqlat`로 wakeup-to-run 분포가 실제로 흔들리는지 확인한다.
6. 다섯 관측이 모두 scheduler 쪽을 가리킬 때만 더 깊은 문서로 내려간다.

짧은 의사결정표로 보면 이렇다.

## 5. 이 다섯 관측창을 읽는 가장 단순한 순서 (계속 2)

| 관측 조합 | 더 그럴듯한 해석 | 다음 문서 |
|---|---|---|
| `load average` 높음 + `r` 높음 + `runqlat` tail 두꺼움 | runnable backlog 또는 CPU saturation | [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md) |
| `r`은 높지 않은데 `/proc/<tid>/sched` delay와 `runqlat` tail이 특정 thread에서만 튐 | hot thread, affinity, cpuset, quota 같은 국소 문제 | [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md), [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md) |
| 여러 TID의 `/proc/<tid>/sched` delay가 같이 늘고 `/proc/schedstat` delta가 특정 CPU 쪽에서 더 빨리 쌓임 | per-CPU imbalance, affinity/cpuset/IRQ locality 문제 | [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md), [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md) |
| `load average` 높음 + `runqlat`는 평범함 | I/O wait, reclaim, throttling이 더 유력 | [Cgroup CPU Throttling, Quota, Runtime Debugging](./cgroup-cpu-throttling-quota-runtime-debugging.md) |
| `runqlat` tail 두꺼움 + worker 수 증가 직후 악화 | 과도한 병렬화, context switch, cache locality 손실 | [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md) |

## 6. 자주 나오는 오해

### "`load average`가 높으면 CPU가 100%라는 뜻이다"

아니다. `load average`는 압력 신호다. CPU saturation일 수도 있지만 I/O wait나 reclaim이 섞였을 수도 있다.

### "`vmstat r`만 보면 run queue를 다 안다"

아니다. `r`은 빠른 힌트다. per-CPU 불균형, 특정 TID 문제, burst tail은 다른 관측이 필요하다.

### "`/proc/<pid>/sched` 필드 뜻을 다 외워야 한다"

아니다. 초보 단계에서는 "정상 시간대와 느린 시간대를 비교했을 때 delay/switch/runtime 축이 어떻게 달라졌는가"만 잡아도 충분하다.

### "`/proc/schedstat`에서 숫자 하나가 큰 CPU가 곧 문제 CPU다"

아니다. 누적치라서 오래 켜 둔 서버에서는 원래 숫자가 크다. 같은 구간 delta, 형제 CPU 비교, 의도된 pinning 여부를 같이 봐야 한다.

### "`runqlat`가 높으면 무조건 코어를 늘리면 된다"

아니다. worker 과다, affinity, cgroup quota, noisy neighbor, lock handoff 문제일 수도 있다. `runqlat`는 분포를 보여 줄 뿐 해법을 바로 주지는 않는다.

## 꼬리질문

> Q: scheduler를 볼 때 CPU 사용률만으로 왜 부족한가요?
> 핵심: CPU%는 "얼마나 바빴는가"만 보여 주고, runnable 대기와 wakeup-to-run tail은 숨길 수 있기 때문이다.

> Q: `/proc/<pid>/sched`는 PID로 볼까요, TID로 볼까요?
> 핵심: 전체 프로세스 압력은 PID, 실제 hot loop나 event loop 문제는 TID가 더 직접적일 때가 많다.

> Q: 언제 `/proc/<pid>/sched`에서 `/proc/schedstat`로 넘어가나요?
> 핵심: suspect thread는 보이는데 "왜 이 CPU 쪽이 문제인가"가 안 풀릴 때, 여러 TID가 같이 흔들릴 때, affinity/cpuset/IRQ locality가 의심될 때 넘어간다.

> Q: `runqlat`를 먼저 보는 게 좋지 않나요?
> 핵심: 분포는 강력하지만 범위를 좁히기 어렵다. 초보자는 `load average`와 `r`로 넓게 보고, `/proc/<pid>/sched`로 대상을 좁히고, 필요할 때만 `/proc/schedstat`로 CPU 쏠림을 확인한 뒤 `runqlat`를 보는 편이 해석 실수가 적다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`load average`가 높을 때 CPU saturation, throttling, I/O wait를 먼저 가르자"면: [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)
> - "`/proc/<pid>/sched`와 `/proc/schedstat`를 더 실제 필드로 읽고 싶다면": [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md)
> - "`runqlat` histogram이 tail latency와 어떻게 이어지는지" 보려면: [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)

## 한 줄 정리

scheduler 입문 다음 단계에서는 `load average`와 `vmstat r`로 전체 압력을 잡고, `/proc/<pid>/sched`로 밀리는 태스크를 좁힌 뒤, 필요할 때만 `/proc/schedstat`로 CPU 쏠림을 확인하고, 마지막에 `runqlat`로 wakeup-to-run tail을 검증하는 습관을 먼저 만드는 것이 가장 실용적이다.
