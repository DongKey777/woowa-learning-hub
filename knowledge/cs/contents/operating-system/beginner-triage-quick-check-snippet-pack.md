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
- [Timeout, Retry, Idempotency](../network/timeout-retry-idempotency.md)

retrieval-anchor-keywords: beginner triage quick check, os quick check snippet pack, symptom first routing, slow response first check, oom first check, too many open files first check, interrupt signal first check, beginner self-check route, primer review route, quick observation mental model, what to check first, basics triage route, beginner triage quick check snippet pack basics, beginner triage quick check snippet pack beginner, beginner triage quick check snippet pack intro

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

## fd quick-check 다음에 바로 보는 20초 handoff

멘탈 모델은 이것만 먼저 고정하면 된다. `Too many open files`가 뜨면 "파일을 너무 많이 열었나?"보다 "어느 번호표 상자가 찼나?"를 먼저 묻는다.

| quick-check 결과 | 첫 해석 | 바로 이어서 볼 문서 |
|---|---|---|
| `ls /proc/$PID/fd | wc -l` 값이 `ulimit -n`에 바짝 붙음 | 지금 이 프로세스의 번호표 상자가 거의 찼다. `EMFILE` 쪽 first-read triage로 이어진다. | [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md) 의 `Quick-check 다음 1분 판독표` |
| `cat /proc/sys/fs/file-nr` 첫 값이 크고 노드 전체가 흔들림 | 특정 프로세스보다 시스템 전체 번호표 풀이 차는 `ENFILE` 쪽을 먼저 본다. | [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md) 의 `Quick-check 다음 1분 판독표` |
| 둘 다 애매하거나 PID 하나만 봐서는 감이 안 옴 | 아직 원인 확정 단계가 아니다. 한도 위치를 다시 나눠 읽어야 한다. 바로 deep dive로 밀지 말고 fd primer부터 다시 고정한다. | [파일 디스크립터 기초](./file-descriptor-basics.md), [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md), [README self-check 빠른 점검 루트](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트) |

짧게만 기억하면 된다.

- `EMFILE`: 내 프로세스 상자가 먼저 찬 경우
- `ENFILE`: 시스템 전체 상자가 먼저 찬 경우
- 다음 단계는 새 명령을 더 많이 치는 것이 아니라, 위 관찰값을 들고 decision table로 내려가는 것이다

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

## `dmesg`가 안 열릴 때 OOM은 무엇을 먼저 보나

멘탈 모델은 단순하다. `dmesg`는 "커널이 남긴 이유 설명"이고, 막혀 있으면 먼저 `cgroup`과 현재 메모리 상태에서 "누가 한도를 넘었는지"를 본다.

| 상황 | 먼저 볼 것 | 짧은 해석 |
|---|---|---|
| 컨테이너 안에서 `dmesg: read kernel buffer failed: Operation not permitted` | `cat /sys/fs/cgroup/memory.current`<br>`cat /sys/fs/cgroup/memory.max`<br>`cat /sys/fs/cgroup/memory.events` | `memory.current`가 `memory.max` 근처이고 `memory.events`의 `oom`/`oom_kill`이 늘면 cgroup OOM 쪽이 더 유력하다. |
| 커널 로그 권한이 막혀도 "정말 메모리 부족이었나?"가 궁금함 | `free -h`<br>`cat /proc/meminfo | egrep 'MemAvailable|SwapFree'` | 호스트 여유 메모리와 swap 여지를 먼저 본다. 호스트는 여유가 있는데 프로세스/컨테이너만 죽었으면 global OOM보다 cgroup limit 쪽이 흔하다. |
| 재시작 뒤라 현재 값만으로 헷갈림 | 애플리케이션 로그의 `Killed` 흔적<br>오케스트레이터 상태의 `OOMKilled` 여부<br>`memory.events`의 누적 카운터 | 지금 메모리가 내려가 있어도 누적 이벤트는 남을 수 있다. "현재 사용량"과 "직전 OOM 흔적"을 분리해서 읽는다. |

여기까지 보고도 메모리 개념 축이 흔들리면 [README self-check 빠른 점검 루트](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 돌아가 1번, 3번 primer를 먼저 다시 본다.

## OOM 종료 흔적 읽기

종료 해석은 "강제 종료"와 "OOM 문맥"을 분리해서 보면 된다.

| 보이는 종료 흔적 | 초보자 1차 해석 | OOM 쪽으로 더 기우는 추가 단서 |
|---|---|---|
| `Exited` 또는 종료 코드 `0` | 프로그램이 스스로 끝난 정상 종료일 가능성이 높다 | 보통 없음 |
| `Terminated`, `SIGTERM`, 종료 코드 `143` | 사용자나 supervisor가 종료를 요청한 흔적일 가능성이 높다 | 보통 없음 |
| `Killed`, 종료 코드 `137` | 강한 종료가 있었던 것은 맞지만 이유는 아직 모른다 | `OOMKilled`, `memory.events`의 `oom_kill` 증가, 메모리 limit 근접 |

이 표에서 초보자가 꼭 기억할 한 줄은 이것이다.

- 종료 코드 `137` 하나만으로 OOM을 확정하지 않는다.
- OOM은 "강제 종료"라는 결과에 `OOMKilled`나 `memory.events` 같은 메모리 문맥이 더 붙어야 한다.

권한 제한 환경에서의 초급자용 분기만 기억하면 된다.

- `dmesg`가 막혔다 = OOM 분석 불가가 아니다.
- 컨테이너/권한 제한 환경에서는 `memory.events`가 가장 먼저 보는 대체 관찰점이다.
- `free -h`는 호스트 상태, `memory.current`/`memory.max`는 cgroup 상태다. 둘은 같은 숫자가 아니다.

## cgroup 파일 이름 호환성 메모

호환성 메모는 파일 이름보다 역할을 맞추는 데 목적이 있다.

| 보고 싶은 역할 | cgroup v2 파일 | cgroup v1에서 자주 보이는 이름 |
|---|---|---|
| 현재 사용량 | `memory.current` | `memory.usage_in_bytes` |
| 제한값 | `memory.max` | `memory.limit_in_bytes` |
| OOM 흔적 | `memory.events` | `memory.oom_control`와 로그를 함께 확인 |

- 핵심은 파일 이름이 아니라 역할이다. "현재 사용량 / 제한값 / OOM 흔적" 3가지만 같은 자리에서 찾으면 된다.
- 오래된 환경이나 일부 컨테이너 이미지는 `memory.current` 대신 `memory.usage_in_bytes`만 보일 수 있다.

더 깊게 들어가야 하면 아래 문서로 이동한다.

- [`Killed`, `OOMKilled`, `memory.events`를 한 장면으로 읽는 입문 메모](./killed-oomkilled-memory-events-beginner-bridge.md)
- [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
- [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
- [OOM Killer Scoring, Victim Selection](./oom-killer-scoring-victim-selection.md)

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
