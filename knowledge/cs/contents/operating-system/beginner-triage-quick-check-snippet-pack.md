---
schema_version: 3
title: Beginner Triage Quick Check Snippet Pack
concept_id: operating-system/beginner-triage-quick-check-snippet-pack
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 74
review_feedback_tags:
- triage-check-snippet
- pack
- os-triage-snippets
- check-command-pack
aliases:
- OS beginner triage snippets
- quick check command pack
- symptom to doc triage
- first observation commands
- 30 second OS triage
intents:
- definition
- troubleshooting
- drill
linked_paths:
- contents/operating-system/beginner-symptom-to-doc-map.md
- contents/operating-system/scheduler-observation-starter-guide.md
- contents/operating-system/memory-management-basics.md
- contents/operating-system/file-descriptor-basics.md
- contents/operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
expected_queries:
- 운영체제 증상을 처음 볼 때 30초 안에 어떤 명령으로 triage해?
- CPU memory IO file descriptor 문제를 quick check하는 snippet을 알려줘
- 증상에서 primer와 deep dive 문서로 넘어가는 첫 관찰 흐름이 필요해
- OS beginner triage에서 2~3개 관찰 명령만 먼저 보고 싶어
contextual_chunk_prefix: |
  이 문서는 OS 초급자가 첫 증상을 보고 30초 안에 2~3개 관찰 명령으로 CPU, memory,
  I/O, file descriptor, scheduler pressure를 1차 라우팅한 뒤 primer/deep dive로 이동하게
  돕는 quick-check snippet pack이다.
---
# Beginner Triage Quick-Check Snippet Pack

> 한 줄 요약: 첫 증상이 보이면 30초 안에 `2~3개 관찰 명령`으로 1차 라우팅하고, 그다음 primer/deep dive로 이동한다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)과 같은 `증상 -> primer -> deep dive` 흐름을, 실제 관찰 명령 기준으로 바로 실행하게 돕는 beginner triage primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)
- [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)
- [메모리 관리 기초](./memory-management-basics.md)
- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [인터럽트 기초](./interrupt-basics.md)
- [Subprocess Symptom First-Branch Guide](./subprocess-symptom-first-branch-guide.md)
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)

retrieval-anchor-keywords: beginner triage quick check, os quick check snippet pack, 처음 운영체제 점검, 뭐부터 봐요, 왜 느려요, 왜 killed, too many open files first check, subprocess hang what to check first, stdout read hang first check, symptom first routing, quick observation mental model, what to check first, basics triage route, 헷갈릴 때 보는 문서, beginner primer route

## 먼저 잡는 멘탈 모델

이 문서는 "원인 확정" 문서가 아니다.

- 목표: 첫 증상을 **맞는 문서 축으로 1차 라우팅**하기
- 방법: 각 증상에서 **관찰 명령 2~3개만** 실행하기
- 다음 단계: 분류 결과를 들고 primer/deep dive로 이동하기
- 개념이 흐리면: 이 문서 안에서 오래 버티지 말고 [README의 self-check 빠른 점검 루트](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 돌아가 primer 축부터 다시 세운다.

즉, 초급자에게는 "많이 보는 것"보다 "먼저 맞는 것을 보는 것"이 더 중요하다.

## 이 문서와 symptom map의 역할 차이

같은 beginner entrypoint지만, 두 문서는 시작점이 조금 다르다.

| 문서 | 먼저 하는 일 | 이 문서가 맞는 순간 |
|---|---|---|
| [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md) | 증상을 primer/deep dive 경로로 1차 라우팅 | "무슨 주제 문서로 가야 하는지"부터 정하고 싶을 때 |
| Beginner Triage Quick-Check Snippet Pack | 증상별 `2~3개 관찰 명령`으로 1차 라우팅을 바로 실행 | "무슨 명령부터 쳐야 하는지"가 먼저 막힐 때 |

즉, 둘 다 `증상 -> primer -> deep dive` 흐름을 쓰지만, symptom map은 "문서 경로 선택", snippet pack은 "관찰 명령 시작"에 더 가깝다.

## 증상별 1차 라우팅용 30초 quick-check

느림과 OOM처럼 초보자가 가장 먼저 많이 보는 두 증상부터 나눈다.

### 느림 command-first

| 증상 | 최소 관찰 명령 (2~3개) | 지금 보는 포인트 | 다음 문서 | 개념이 흐리면 바로 돌아갈 곳 |
|---|---|---|---|---|
| 요청이 전반적으로 느림 | `uptime`<br>`vmstat 1 5`<br>`cat /proc/pressure/cpu /proc/pressure/io` | load 숫자만 보지 말고 `r`(run queue), `wa`(I/O wait), `cpu.pressure`, `io.pressure`를 함께 본다. | [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md) | `load average`와 scheduler 기초가 섞이면 [README self-check 빠른 점검 루트](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 돌아가 1~2번 primer부터 다시 본다. |

### OOM command-first

| 증상 | 최소 관찰 명령 (2~3개) | 지금 보는 포인트 | 다음 문서 | 개념이 흐리면 바로 돌아갈 곳 |
|---|---|---|---|---|
| `Killed` 로그/메모리 의심 | `free -h`<br>`cat /proc/meminfo | egrep 'MemAvailable|SwapFree'`<br>`dmesg -T | rg -i 'out of memory|killed process'` | 남은 메모리와 OOM 흔적을 같이 본다. `dmesg`가 막히면 바로 아래 대체 표로 내려가 cgroup 경로부터 확인한다. | [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md) | `RSS`/page fault/OOM 축이 흐리면 [README self-check 빠른 점검 루트](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 돌아가 1번, 3번 primer를 먼저 다시 본다. |

## fd command-first

fd와 interrupt는 "명령은 알겠는데 개념 축이 흔들리는" 경우가 많아서 역링크를 더 직접적으로 둔다.

| 증상 | 최소 관찰 명령 (2~3개) | 지금 보는 포인트 | 다음 문서 | 개념이 흐리면 바로 돌아갈 곳 |
|---|---|---|---|---|
| `Too many open files` (`EMFILE`/`ENFILE`) | `ulimit -n`<br>`ls /proc/$PID/fd | wc -l`<br>`cat /proc/sys/fs/file-nr` | 프로세스 한도(`EMFILE`)인지 시스템 전체 한도(`ENFILE`)인지 먼저 가른다. | [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md) | fd 번호표 감각이 흐리면 바로 [파일 디스크립터 기초](./file-descriptor-basics.md)를 보고, 축 전체가 흐리면 [README self-check 빠른 점검 루트](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 돌아간다. |

## subprocess hang command-first

`Popen`/`ProcessBuilder`/`Runtime.exec()`가 "그냥 멈춘다"는 말은 너무 넓다. 초보자에게는 `wait()` 정지, `stdout.read()` 정지, `stdin close` 누락을 먼저 분리하는 편이 안전하다.

| 증상 | 최소 관찰 명령 (2~3개) | 지금 보는 포인트 | 다음 문서 | 개념이 흐리면 바로 돌아갈 곳 |
|---|---|---|---|---|
| subprocess가 끝나지 않음 | `ps -o pid,ppid,stat,wchan:24,cmd -p $PID`<br>`ls -l /proc/$PID/fd`<br>`strace -p $PID -e read,write,wait4 -tt` | `wait4`에 오래 서 있으면 parent wait 축, pipe fd가 많이 열려 있거나 `read`/`write`에 멈추면 stdin/stdout ordering 축부터 본다. | [Subprocess Symptom First-Branch Guide](./subprocess-symptom-first-branch-guide.md) | `pipe`, `fork`, `waitpid()` 그림이 흐리면 [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)로 돌아가고, fd 감각이 약하면 [파일 디스크립터 기초](./file-descriptor-basics.md)를 먼저 본다. |

여기서 중요한 것은 "명령 하나로 원인을 확정"하려는 태도를 버리는 것이다.

- `wait4`에 멈추면 "자식 종료 대기" 축을 먼저 본다.
- child 쪽 `stdout`/`stderr` pipe가 열려 있으면 "출력을 안 비워서 막힌 것 아닌가"를 먼저 의심한다.
- `stdin` write end가 계속 열려 있으면 "EOF를 못 보내서 child가 기다리는 것 아닌가"를 바로 분리한다.

즉 초급 triage에서는 "`왜 멈췄지?`"를 "`wait` 축인가, pipe 축인가, EOF 축인가?`"로 다시 번역하는 것이 먼저다.

## syscall vs context switch command-first

| 개념 혼동 | 먼저 볼 quick-check | 지금 보는 포인트 | 다음 문서 |
|---|---|---|---|
| "`시스템 콜`과 `컨텍스트 스위치`가 같은 말처럼 느껴짐" | `strace -c -p $PID`<br>`vmstat 1 5` | syscall은 "커널에 무엇을 요청했는지", context switch는 "CPU 실행 주체가 얼마나 자주 바뀌는지"라는 서로 다른 관찰 축이다. | [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md), [Lock Contention, Futex, Off-CPU Debugging](./lock-contention-futex-offcpu-debugging.md) |

## process vs thread command-first

| 개념 혼동 | 먼저 볼 quick-check | 지금 보는 포인트 | 다음 문서 |
|---|---|---|---|
| "`프로세스`와 `스레드` 차이가 계속 섞임" | `ps -eLf | head`<br>`ps -o pid,ppid,comm -p $PID` | 같은 PID 아래 여러 LWP/TID가 보이면 "하나의 프로세스 안 실행 단위"를 먼저 그림으로 잡을 수 있다. | [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md), [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) |

## interrupt command-first

| 증상 | 최소 관찰 명령 (2~3개) | 지금 보는 포인트 | 다음 문서 | 개념이 흐리면 바로 돌아갈 곳 |
|---|---|---|---|---|
| 인터럽트/시그널/예외가 헷갈림 | `cat /proc/interrupts`<br>`ps -e -o pid,ppid,stat,comm,wchan:24`<br>`kill -l` | 하드웨어 인터럽트 관찰(`/proc/interrupts`)과 프로세스 signal 상태(`ps`, `kill -l`)를 같은 개념으로 섞지 않는다. | [softirq, hardirq, latency, server debugging](./softirq-hardirq-latency-server-debugging.md) | interrupt와 process 흐름이 같이 흐리면 [README self-check 빠른 점검 루트](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 돌아가 1번, 4번 primer를 다시 본다. |

## 20초 handoff 표만 기억하면 된다

이 문서는 여기서 더 파고들지 않는다. `fd`, `느림`, `oom`은 **증상 이름만 잡고 바로 다음 문서로 넘기는 것**이 목적이다.

| quick-check 뒤 바로 내릴 말 | 첫 해석 | 바로 이어서 볼 문서 |
|---|---|---|
| "`fd` 수가 `ulimit -n`에 가깝다" | 내 프로세스 상자가 먼저 찬 `emfile` 쪽이다. | [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md), [파일 디스크립터 기초](./file-descriptor-basics.md) |
| "`file-nr` 쪽이 크다" | 시스템 전체 상자가 흔들리는 `enfile` 쪽이다. | [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md) |
| "`killed`는 봤는데 원인은 아직 모르겠다" | 종료 결과만 본 상태다. OOM 여부는 다음 beginner bridge에서 다시 가른다. | [`Killed`, `OOMKilled`, `memory.events`를 한 장면으로 읽는 입문 메모](./killed-oomkilled-memory-events-beginner-bridge.md), [메모리 관리 기초](./memory-management-basics.md) |
| "`느리다`인데 CPU인지 I/O인지 모르겠다" | 지금은 원인 확정이 아니라 분기 단계다. | [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md), [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md) |

## 작은 예시: "너무 느려요"일 때

아래 3개만 먼저 본다.

```bash
uptime
vmstat 1 5
cat /proc/pressure/cpu /proc/pressure/io
```

- `uptime`의 load가 높아도 바로 CPU 포화라고 단정하지 않는다.
- `vmstat`에서 `r`이 크고 `cpu.pressure`가 같이 오르면 CPU가 runnable 작업을 못 받아 주는 쪽으로 먼저 읽는다.
- `vmstat`에서 `wa`가 크고 `io.pressure`가 같이 오르면 디스크/스토리지 대기 쪽으로 먼저 읽는다.
- `cpu.pressure`는 높은데 `wa`는 낮으면 "CPU 대기", `io.pressure`는 높은데 `r`은 낮으면 "I/O 대기" 쪽에 더 가깝다.

초보자용 최소 규칙은 아래 2줄이면 충분하다.

| 같이 볼 값 | 초보자 1차 해석 |
|---|---|
| `vmstat r`가 크고 `cpu.pressure`도 뚜렷하게 오름 | "할 일은 있는데 CPU를 못 받는 줄"이 길다. CPU 포화/스케줄링 축부터 본다. |
| `vmstat wa` 또는 `b`가 크고 `io.pressure`도 뚜렷하게 오름 | "일하다가 I/O 때문에 멈춘 줄"이 길다. 디스크/파일시스템 대기 축부터 본다. |

이 표는 확정 판정표가 아니라 첫 분기표다. 둘 다 같이 오르면 CPU와 I/O가 엮인 상태일 수 있으니 아래 deep dive 문서로 내려가서 좁힌다.

이렇게 30초 분류를 하고 나서 [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)로 내려가면 실패율이 낮다.

더 자세한 숫자 해석이 필요하면 아래 두 문서를 바로 이어서 보면 된다.

- [vmstat Counters, Runtime Pressure](./vmstat-counters-runtime-pressure.md)
- [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

## OOM은 여기서 확정하지 말고 한 번 더 넘긴다

`Killed`, `137`, `OOMKilled`, `memory.events`는 초급자에게 비슷하게 보여도 같은 말이 아니다. 이 문서에서는 아래 한 줄만 먼저 고정하면 충분하다.

- `Killed`나 `137`만으로 OOM을 확정하지 않는다.
- `OOMKilled`나 `memory.events`가 붙는지 보고 다음 문서에서 다시 가른다.
- 권한 때문에 `dmesg`가 막혀도 OOM 학습 경로가 끝난 것은 아니다.

더 깊은 운영 디테일은 이 문서에서 계속 다루지 않는다. 아래 순서로 넘기면 된다.

| 지금 보이는 말 | 여기서의 안전한 다음 단계 |
|---|---|
| "`killed`가 떠서 왜 죽었는지 모르겠다" | [`Killed`, `OOMKilled`, `memory.events`를 한 장면으로 읽는 입문 메모](./killed-oomkilled-memory-events-beginner-bridge.md)로 이동해 종료 흔적과 OOM 문맥을 분리한다. |
| "`memory.events`가 뭔지 처음 본다" | [메모리 관리 기초](./memory-management-basics.md)로 돌아가 메모리 범위부터 다시 잡는다. |
| "컨테이너/cgroup까지 내려가니 갑자기 어렵다" | [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)으로 돌아가 primer 축을 다시 고른다. |

## 흔한 혼동

- load average가 높으면 항상 CPU 병목이라는 오해
- `Killed` 로그를 보면 항상 "서버 전체 메모리 0"이라고 보는 오해
- `Too many open files`를 파일만의 문제로 보는 오해 (소켓/파이프도 fd)
- 인터럽트와 시그널을 같은 계층의 이벤트로 보는 오해

## 사용 팁 (Beginner)

- 먼저 2~3개만 실행하고 캡처한다. 처음부터 10개 이상 명령을 돌리지 않는다.
- 증상 분류가 끝나면 [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)에서 다음 primer/deep dive를 고른다.
- `dmesg` 접근이 제한된 환경이면 OOM 행은 `free -h`, `memory.current`, `memory.max`, `memory.events`부터 본다.
- 파일이 없으면 바로 포기하지 말고 같은 역할의 v1 이름(`memory.usage_in_bytes`, `memory.limit_in_bytes`, `memory.oom_control`)을 찾는다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`증상은 알겠는데 어떤 문서 축으로 갈지`"를 다시 고르려면: [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)
> - "`load average`를 1분 안에 더 정확히 나누고 싶다면": [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)
> - "`Killed` / `OOMKilled` / `memory.events`를 같은 장면으로 묶어 읽고 싶다면": [`Killed`, `OOMKilled`, `memory.events`를 한 장면으로 읽는 입문 메모](./killed-oomkilled-memory-events-beginner-bridge.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

초급 triage에서는 "정밀 분석"보다 "증상 축을 틀리지 않는 30초 관찰"이 먼저다.
