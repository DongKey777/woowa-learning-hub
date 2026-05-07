---
schema_version: 3
title: Scheduler Signals Example Walkthrough
concept_id: operating-system/scheduler-signals-example-walkthrough
canonical: true
category: operating-system
difficulty: advanced
doc_role: drill
level: advanced
language: mixed
source_priority: 82
review_feedback_tags:
- scheduler-signals-walkthrough
- vmstat-load-average
- proc-sched-runqlat
- cpu-saturation-io
aliases:
- scheduler signals walkthrough
- vmstat load average proc sched runqlat
- CPU saturation IO false positive
- scheduler example drill
- load average false positive
intents:
- drill
- troubleshooting
linked_paths:
- contents/operating-system/run-queue-load-average-cpu-saturation.md
- contents/operating-system/scheduler-observation-starter-guide.md
- contents/operating-system/scheduler-wakeup-latency-runqlat-debugging.md
- contents/operating-system/schedstat-proc-sched-runtime-debugging.md
- contents/operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md
expected_queries:
- vmstat, load average, /proc/pid/sched, runqlat를 옆으로 붙여 scheduler signal을 읽는 예제가 필요해
- load average만 보면 CPU saturation과 I/O false positive를 왜 헷갈려?
- scheduler observation을 실제 walkthrough로 연습하고 싶어
- runnable queue와 wakeup latency를 한 사례로 비교해줘
contextual_chunk_prefix: |
  이 문서는 load average만 보면 쉽게 틀리므로 vmstat, /proc/<pid>/sched, schedstat, runqlat를
  나란히 읽어 CPU saturation과 I/O false positive, scheduler wait를 가르는 walkthrough drill이다.
---
# Scheduler Signals Example Walkthrough: `vmstat`, Load Average, `/proc/<pid>/sched`, `runqlat`

> 한 줄 요약: `load average`만 보면 쉽게 틀리고, `vmstat`, `/proc/<pid>/sched`, `runqlat`를 옆으로 붙여 읽어야 진짜 CPU saturation과 I/O false positive를 가를 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [vmstat Counters, Runtime Pressure](./vmstat-counters-runtime-pressure.md)
> - [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)

> retrieval-anchor-keywords: scheduler signals walkthrough, vmstat load average proc sched runqlat example, cpu saturation example, load average false positive, io wait high load average, runnable latency example, vmstat r b wa interpretation, proc pid sched wait_sum iowait_sum, runqlat histogram example, scheduler observability sample output

## 핵심 개념

이 문서는 "load average가 높다"라는 한 줄 경보를 네 개 신호로 분해해 읽는 예제다.  
샘플은 16 vCPU Linux 호스트를 가정하며, `/proc/<pid>/sched` 필드 이름과 단위는 커널 버전에 따라 조금 달라질 수 있다.

읽는 순서:

1. `load average`: 압력이 있다는 사실만 먼저 확인한다.
2. `vmstat`: 그 압력이 runnable(`r`)인지 blocked(`b`)인지 구분한다.
3. `/proc/<pid>/sched`: 문제 태스크가 CPU를 기다리는지, 아니면 자주 잠들었다 깨는지 본다.
4. `runqlat`: wakeup 이후 실제 run까지의 tail이 두꺼운지 확인한다.

핵심은 지표 하나로 결론내리지 않는 것이다.  
특히 `load average`는 runnable task와 uninterruptible sleep task를 함께 올릴 수 있어서 "CPU saturation 같다"는 false positive를 자주 만든다.

## 시나리오 1: 진짜 CPU saturation

상황: 점심 트래픽 burst 때 16 vCPU API 서버의 p99가 40ms에서 280ms로 뛰었다. worker 수는 최근 16개에서 48개로 늘었다.

### 샘플 출력

#### `load average`

```bash
$ uptime
14:32:11 up 6 days,  2:41,  3 users,  load average: 22.4, 21.9, 20.7
```

#### `vmstat 1`

```bash
$ vmstat 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in     cs us sy id wa st
21  0      0 812384  91244 6220016   0    0     1     6 3589 182945 76 21  3  0  0
19  0      0 805912  91244 6219984   0    0     0     0 3471 176228 74 22  4  0  0
```

#### `/proc/<pid>/sched`

```bash
$ cat /proc/8421/sched
api-worker-8421 (8421, #threads: 1)
se.sum_exec_runtime                      : 4182.551000
nr_switches                             : 28641
nr_voluntary_switches                   : 413
nr_involuntary_switches                 : 28228
se.statistics.wait_sum                  : 35890.442000
se.statistics.wait_count                : 27311
se.statistics.iowait_sum                : 0.000000
```

#### `runqlat`

```bash
$ sudo runqlat-bpfcc -m -p 8421 10
msecs               : count    distribution
0 -> 1              : 87       |****
1 -> 2              : 311      |**************
2 -> 4              : 844      |************************************
4 -> 8              : 420      |******************
8 -> 16             : 96       |****
16 -> 32            : 12       |
```

### 어떻게 읽는가

- `load average 22.x`는 16 vCPU보다 높아서 압력이 있다는 사실만 보여 준다. 이것만으로는 CPU인지 I/O인지 아직 모른다.
- `vmstat`에서 `r`이 19~21로 높고 `b=0`, `wa=0`이라서 대기열의 성격이 blocked I/O가 아니라 runnable backlog에 가깝다.
- `us+sy`가 95% 안팎이고 `cs`가 초당 17만~18만대로 높다. 스레드를 늘린 뒤 context-switch churn이 같이 커졌다는 힌트다.
- `/proc/<pid>/sched`에서 `nr_involuntary_switches`가 압도적이고 `wait_sum`이 runtime보다 훨씬 크게 누적된다. 태스크가 자발적으로 자는 것보다 CPU를 못 받아 밀리는 시간이 더 길다는 뜻이다.
- `se.statistics.iowait_sum`이 사실상 0이어서 "load average가 높지만 디스크가 원인"이라는 설명과 맞지 않는다.
- `runqlat` 히스토그램 tail이 수 ms까지 두꺼워졌다. wakeup 이후 실제 run까지 스케줄러 queueing이 생기고 있다는 직접 증거다.

판정: 이 케이스는 진짜 CPU saturation이다.  
우선순위는 thread 수 재평가, affinity/cpuset 제약 확인, cgroup quota 확인, hot path CPU cost 축소다.

## 시나리오 2: CPU saturation처럼 보이지만 false positive인 경우

상황: 같은 16 vCPU 호스트에서 batch importer가 느려지고 `load average`가 18 근처까지 올랐다. 하지만 API latency는 거의 그대로고 디스크 대기 경고가 함께 올라왔다.

### 샘플 출력

#### `load average`

```bash
$ uptime
15:08:44 up 6 days,  3:17,  3 users,  load average: 17.8, 18.0, 16.9
```

#### `vmstat 1`

```bash
$ vmstat 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi     bo   in    cs us sy id wa st
 1 11      0 795620  90584 6204120   0    0   184 145328 2180 48762  9  5 28 58  0
 2 10      0 790144  90584 6201088   0    0   172 138904 2104 47318 10  4 29 57  0
```

#### `/proc/<pid>/sched`

```bash
$ cat /proc/9133/sched
import-worker-9133 (9133, #threads: 1)
se.sum_exec_runtime                      : 612.143000
nr_switches                             : 19422
nr_voluntary_switches                   : 18803
nr_involuntary_switches                 : 619
se.statistics.wait_sum                  : 942.771000
se.statistics.wait_count                : 18807
se.statistics.iowait_sum                : 18422.116000
```

#### `runqlat`

```bash
$ sudo runqlat-bpfcc -p 9133 10
usecs               : count    distribution
0 -> 2              : 33       |**
2 -> 4              : 214      |*************
4 -> 8              : 671      |**************************************
8 -> 16             : 291      |****************
16 -> 32            : 58       |***
32 -> 64            : 7        |
```

### 어떻게 읽는가

- `load average 17~18`만 보면 CPU가 꽉 찬 것처럼 보이지만, 이 숫자는 uninterruptible sleep도 같이 올린다.
- `vmstat`에서 `r`은 1~2로 낮고 `b`는 10~11, `wa`는 57~58%다. 이 패턴은 runnable pressure보다 blocked I/O pressure에 가깝다.
- `bo`가 매우 크고 `us+sy`는 14% 정도뿐이라 CPU는 대부분 놀거나 I/O completion을 기다린다.
- `/proc/<pid>/sched`에서 `nr_voluntary_switches`가 대부분이고 `iowait_sum`이 매우 크다. 태스크가 CPU 경쟁으로 쫓겨난 것이 아니라 스스로 잠들며 I/O 완료를 기다렸다는 뜻이다.
- `wait_sum`은 조금 있지만 `runqlat` tail이 수십 us 범위에 머문다. 깨어난 뒤 CPU를 받는 것은 빠르다.

판정: 이 케이스는 "높은 load average = CPU saturation"이라는 false positive다.  
다음 액션은 스토리지/NFS 대기, writeback, queue depth, filesystem stall 쪽을 파는 것이다.

## 두 시나리오를 옆으로 붙여 읽기

| 신호 | 진짜 CPU saturation | false positive |
|---|---|---|
| `load average` | 16 vCPU보다 높은 22.x. 압력은 분명하지만 원인 분리는 아직 안 된다 | 역시 17~18로 높다. 이 값만 보면 CPU saturation처럼 오해하기 쉽다 |
| `vmstat` | `r`이 코어 수 근처까지 올라가고 `b=0`, `wa=0` | `r`은 낮고 `b`, `wa`, `bo`가 높다 |
| `/proc/<pid>/sched` | `nr_involuntary_switches`와 `wait_sum`이 크고 `iowait_sum`은 거의 0 | `nr_voluntary_switches`와 `iowait_sum`이 지배적이다 |
| `runqlat` | 히스토그램 tail이 ms대로 두꺼워진다 | 대부분 us 구간에 몰려 있다 |
| 결론 | runnable queueing이 p99를 만든다 | blocked I/O가 load average를 부풀린다 |

## 실전 판정 규칙

- `load average`가 높아도 `vmstat r`이 낮고 `b`/`wa`가 높으면 먼저 CPU가 아니라 I/O wait을 의심한다.
- `/proc/<pid>/sched`에서 `nr_involuntary_switches`와 `wait_sum`이 빠르게 늘고 `runqlat` tail이 두꺼우면 scheduler queueing 가능성이 높다.
- `/proc/<pid>/sched`에 `iowait_sum`이 없으면 `nr_voluntary_switches`, `vmstat b/wa`, `iostat`나 storage playbook으로 보강한다.
- `load average`는 방향만 알려 주고, 최종 판정은 `vmstat`와 `runqlat`가 만든다.

## 꼬리질문

> Q: `load average`가 코어 수보다 높으면 바로 CPU 증설을 결정해도 되나요?
> 핵심: 아니다. 먼저 `vmstat r/b`, `wa`, `runqlat`, `/proc/<pid>/sched`를 같이 봐서 runnable backlog인지 blocked I/O인지 갈라야 한다.

> Q: `runqlat`가 얇은데 `load average`만 높은 경우는 무엇을 의심하나요?
> 핵심: CPU가 아니라 I/O wait, reclaim, filesystem stall 같은 false positive 가능성을 먼저 본다.

> Q: `/proc/<pid>/sched`에서 무엇이 CPU saturation 쪽 힌트가 되나요?
> 핵심: involuntary switch 우세, 큰 `wait_sum`, 낮은 `iowait_sum`, 그리고 `runqlat` tail 동반 여부다.

## 한 줄 정리

`load average`는 압력의 존재만 말하고, 진짜 CPU saturation인지 여부는 `vmstat`, `/proc/<pid>/sched`, `runqlat`를 옆으로 붙여 읽을 때만 보인다.
