# Beginner Symptom-to-Doc Map

> 한 줄 요약: 운영체제에서 처음 막힐 때는 "원인 확정"보다 "증상을 맞는 문서로 라우팅"이 먼저다.

**난이도: 🟢 Beginner**

관련 문서:

- [operating-system 카테고리 인덱스](./README.md)
- [개념 점검용 추천 순서 (self-check 빠른 점검 루트)](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)
- [Beginner Triage Quick-Check Snippet Pack](./beginner-triage-quick-check-snippet-pack.md)
- [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)
- [CPU 스케줄링 기초](./cpu-scheduling-basics.md)
- [메모리 관리 기초](./memory-management-basics.md)
- [`Killed`, `OOMKilled`, `memory.events`를 한 장면으로 읽는 입문 메모](./killed-oomkilled-memory-events-beginner-bridge.md)
- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [인터럽트 기초](./interrupt-basics.md)
- [Timeout, Retry, Idempotency](../network/timeout-retry-idempotency.md)

retrieval-anchor-keywords: beginner symptom map, os symptom triage, beginner symptom routing mental model, beginner triage quick check, command first quick check, slow response first triage, oom first triage, too many open files first triage, interrupt confusion primer, syscall vs context switch confusion, process vs thread confusion, 운영체제 증상 라우팅, 증상별 관찰 명령, 운영체제 빠른 점검 루트 점프, beginner symptom to doc map basics

## 먼저 잡는 멘탈 모델

운영체제 초반 트러블슈팅은 "고장 수리"보다 "병원 접수"에 가깝다.

- 첫 증상으로 진료과(문서 축)를 고른다.
- 그다음 primer에서 용어를 맞춘다.
- 마지막에 deep dive로 원인/복구를 좁힌다.

즉, **처음부터 고급 분석 문서로 뛰어들기보다, 증상 -> primer -> deep dive 순서가 실패율이 낮다.**

## 어디로 바로 점프하면 되나

처음 막힌 지점에 따라 아래처럼 바로 이동하면 왕복이 줄어든다.

| 지금 필요한 것 | 바로 갈 문서 | 왜 여기로 가나 |
|---|---|---|
| "증상은 있는데 무슨 명령부터 볼지 모르겠다" | [Beginner Triage Quick-Check Snippet Pack](./beginner-triage-quick-check-snippet-pack.md) | 증상별로 2~3개 관찰 명령만 먼저 실행해 30초 안에 분기할 수 있다. |
| "서버가 느린데 `load average` 다음에 어디까지 내려가야 할지 모르겠다" | [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md) | `load average`를 CPU 포화/쿼터 쓰로틀링/I/O 대기 3갈래로 나누는 beginner bridge라서 deep dive 진입 전 첫 분기가 선명해진다. |
| "증상은 잡았는데 개념이 자꾸 섞여서 다시 정리하고 싶다" | [개념 점검용 추천 순서 (self-check 빠른 점검 루트)](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트) | primer 4편을 짧게 다시 훑고 각 문서 말미 `Self-check`로 개념 축을 재고정할 수 있다. |
| "카테고리 전체에서 다른 primer를 다시 고르고 싶다" | [operating-system 카테고리 인덱스](./README.md) | symptom entrypoint에서 primer/deep dive catalog 전체로 다시 이동할 수 있다. |

## 왕복 이동이 가장 자주 필요한 경로: "서버가 느려요"

느림 증상은 입문 맵에서 deep dive로 가장 자주 내려가는 대신, 중간에 "이 문서가 너무 깊다"는 느낌이 들면 다시 올라와야 하는 대표 경로다.

| 지금 위치 | 다음 이동 | 언제 다시 돌아오면 좋은가 |
|---|---|---|
| 이 문서에서 "느리다" 증상을 처음 잡았을 때 | [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md) | `load average`, `vmstat r`, PSI가 각각 무엇을 뜻하는지 아직 섞여 있으면 |
| starter guide까지 읽고 "원인 축 3개를 빨리 나누고 싶다"면 | [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md) | triage 문서에서 quota, I/O wait, scheduler 용어가 다시 헷갈리면 |
| triage를 읽다가 "아예 다른 증상 문서로 갈 수도 있나?" 싶으면 | [이 증상 맵으로 다시 돌아오기](./beginner-symptom-to-doc-map.md) | 느림이 아니라 `Killed`, `EMFILE`, 인터럽트 혼동 쪽이 더 가까워 보이면 |

## 증상별 1차 라우팅: 느림 / OOM

| 첫 증상 | 먼저 볼 primer | `command-first` | 다음 deep dive | 지금 당장 확인할 관찰 포인트 |
|---|---|---|---|---|
| 요청이 전반적으로 느리고 응답 지연이 커짐 | [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md), [CPU 스케줄링 기초](./cpu-scheduling-basics.md) | [command-first](./beginner-triage-quick-check-snippet-pack.md#느림-command-first) | [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md), [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md) | 느린 원인이 CPU 포화인지, quota throttling인지, I/O 대기인지 먼저 분리 |
| 프로세스가 죽거나 `Killed` 로그와 함께 메모리 의심 | [메모리 관리 기초](./memory-management-basics.md), [`Killed`, `OOMKilled`, `memory.events`를 한 장면으로 읽는 입문 메모](./killed-oomkilled-memory-events-beginner-bridge.md) | [command-first](./beginner-triage-quick-check-snippet-pack.md#oom-command-first) | [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md), [OOM Killer Scoring and Victim Selection](./oom-killer-scoring-victim-selection.md) | 앱 로그 `Killed`, Kubernetes `OOMKilled`, cgroup `memory.events`를 같은 사건의 다른 표기라고 먼저 묶는다 |

## 증상별 1차 라우팅: fd

| 첫 증상 | 먼저 볼 primer | `command-first` | 다음 deep dive | 지금 당장 확인할 관찰 포인트 |
|---|---|---|---|---|
| `Too many open files`, `EMFILE`, `ENFILE` 에러 | [파일 디스크립터 기초](./file-descriptor-basics.md), [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) | [command-first](./beginner-triage-quick-check-snippet-pack.md#fd-command-first) | [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md), [Container FD Pressure Bridge: `EMFILE`, `ENFILE`, Host vs Container](./container-fd-pressure-emfile-enfile-bridge.md), [RLIMIT_NOFILE, NPROC Governance](./rlimit-nofile-nproc-governance.md) | 프로세스 한도(`EMFILE`)인지 시스템 한도(`ENFILE`)인지부터 구분하고, 컨테이너에서는 호스트 공유 fd pressure도 같이 본다 |

`command-first` 배지는 "지금은 문서보다 명령 2~3개가 먼저"라는 뜻이다. 표에서 막히면 quick-check 문서의 해당 증상 섹션으로 바로 내려가면 된다.

## 증상별 1차 라우팅: 개념 혼동

| 첫 증상 | 먼저 볼 primer | `command-first` | 다음 deep dive | 지금 당장 확인할 관찰 포인트 |
|---|---|---|---|---|
| "`시스템 콜`과 `컨텍스트 스위치`가 같은 말처럼 느껴짐" | [시스템 콜 기초](./syscall-basics.md), [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md) | [command-first](./beginner-triage-quick-check-snippet-pack.md#syscall-vs-context-switch-command-first) | [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md), [Lock Contention, Futex, Off-CPU Debugging](./lock-contention-futex-offcpu-debugging.md) | "`커널에 요청하는 경계`(syscall)와 `누가 CPU를 쓰는지`(스케줄링)를 분리" |
| "`프로세스`와 `스레드` 차이가 계속 섞임" | [프로세스와 스레드 기초](./process-thread-basics.md), [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md) | [command-first](./beginner-triage-quick-check-snippet-pack.md#process-vs-thread-command-first) | [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md), [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) | "격리 단위(프로세스) vs 실행 단위(스레드)"를 먼저 고정 |

## 증상별 1차 라우팅: 개념 혼동 (계속 2)

| 인터럽트/시그널/예외가 섞여서 헷갈림 | [인터럽트 기초](./interrupt-basics.md), [signals, process supervision](./signals-process-supervision.md) | [command-first](./beginner-triage-quick-check-snippet-pack.md#interrupt-command-first) | [softirq, hardirq, latency, server debugging](./softirq-hardirq-latency-server-debugging.md), [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md) | "비동기 인터럽트"와 "동기 예외/트랩"을 먼저 분리 |

## 작은 예시: "서버가 느려요"에서 시작할 때

"CPU 100%"만 보고 바로 코드 최적화로 가면 자주 빗나간다.

1. [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)로 `load average`와 run queue를 먼저 읽는다.
2. [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)로 원인 축을 3개로 나눈다.
3. CPU 포화가 아니라 quota throttling이었다면, compute 최적화보다 cgroup 설정/배치가 먼저다.

중간에 "내가 지금 scheduler 문서를 읽어야 하는지, 메모리/fd 문서를 읽어야 하는지 다시 헷갈린다"면 [이 symptom map](./beginner-symptom-to-doc-map.md)으로 다시 올라와 증상 축부터 재선택하면 된다.

핵심은 "느림"이라는 같은 증상도 원인 축이 다르면 다음 문서가 달라진다는 점이다.

## 짧은 실제 예시: `load`는 비슷한데 원인은 다를 수 있다

같은 "서버가 느리다"라도 `load average` 숫자 하나만 보면 헷갈린다. 아래처럼 `load` + `vmstat` + PSI를 같이 보면 초보자도 첫 분기를 더 안전하게 탈 수 있다.

| 관찰 스냅샷 | CPU 포화 쪽에 가까운 예시 | I/O 대기 쪽에 가까운 예시 |
|---|---|---|
| `uptime` | `load average: 9.8, 9.4, 8.7` | `load average: 10.1, 9.7, 8.9` |
| `vmstat 1` 핵심 | `r=11`, `b=0`, `wa=1` | `r=1`, `b=7`, `wa=38` |
| PSI 핵심 | `cpu.pressure avg10=14.20`, `io.pressure avg10=0.30` | `cpu.pressure avg10=0.80`, `io.pressure avg10=19.40` |
| 초보자 1차 해석 | runnable 일이 코어보다 많아 CPU를 기다리는 그림 | runnable보다는 blocked task가 많고 I/O 쪽 stall이 큰 그림 |
| 다음 문서 | [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md) | [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md), [vmstat Counters, Runtime Pressure](./vmstat-counters-runtime-pressure.md) |

여기서 중요한 포인트는 이것뿐이다.

- `load average`가 둘 다 높아도 `vmstat r`이 높고 `cpu.pressure`가 크면 CPU 포화 쪽이다.
- `load average`가 높아도 `vmstat b`/`wa`와 `io.pressure`가 크면 I/O 대기 쪽이다.
- 즉, `load average`는 경보음이고 판정문은 `vmstat`과 PSI가 보강한다.

## 흔한 혼동 정리

- "느리면 무조건 CPU 문제"가 아니다.
- "`load average`가 높으면 곧바로 CPU 포화"가 아니다. `r`/`b`/`wa`와 `cpu.pressure`/`io.pressure`를 같이 봐야 한다.
- "OOM이면 메모리가 완전히 0이어야 한다"가 아니다.
- "fd 에러는 파일을 많이 열어서만 생긴다"가 아니다. 소켓/파이프 누수도 같은 문제다.
- "시스템 콜 = 컨텍스트 스위치"가 아니다. syscall은 경계 진입이고, 컨텍스트 스위치는 CPU 실행 주체 전환이다.
- "프로세스 = 스레드"가 아니다. 프로세스는 격리 단위, 스레드는 같은 프로세스 안 실행 단위다.
- "인터럽트 = 시그널"이 아니다. 인터럽트는 커널 이벤트 처리 메커니즘이고, 시그널은 유저 공간 전달 인터페이스다.

## 다음으로 어디를 읽을까?

- 증상 자체를 빠르게 분류하고 싶으면 [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md), [메모리 관리 기초](./memory-management-basics.md), [파일 디스크립터 기초](./file-descriptor-basics.md), [인터럽트 기초](./interrupt-basics.md)부터 읽는다.
- `load average` triage까지 내려갔다가 "느림 말고 다른 축이 더 맞는 것 같다"면 [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)으로 다시 올라와 증상 기준으로 재분기한다.
- 분류 후 운영 디버깅으로 내려가려면 [현대 runtime catalog](./README.md#현대-runtime-catalog)에서 bucket별 deep dive로 이동한다.

## Self-check (자가 점검 4문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

답이 자꾸 "`용어는 본 것 같은데 서로 연결이 잘 안 된다`"로 흐르면, 바로 [개념 점검용 추천 순서 (self-check 빠른 점검 루트)](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 올라가서 primer 4편만 다시 훑는 편이 가장 빠르다.

1. "요청이 느리다"는 증상 하나만으로 바로 코드 최적화에 들어가기보다, CPU 포화/쿼터 쓰로틀링/I/O 대기 중 어느 축인지 먼저 나눠 봤는가?
   힌트: "느리다"는 결과만 같고 원인은 다르니, 먼저 어떤 자원이 막혔는지 분류해야 다음 문서가 맞아진다.
2. `Killed` 로그를 봤을 때 "OS 전체 메모리 부족"으로 단정하지 않고 global OOM과 memcg OOM 가능성을 분리해 봤는가?
   힌트: 컨테이너 한도 초과로도 같은 현상이 보일 수 있어 host 전체와 cgroup 범위를 나눠 봐야 한다.
3. `Too many open files`에서 `EMFILE`(프로세스 한도)와 `ENFILE`(시스템 한도)를 구분해 확인할 수 있는가?
   힌트: 내 프로세스만 넘친 것인지 시스템 전체 테이블이 찬 것인지에 따라 원인과 대응이 달라진다.
4. 인터럽트, 예외, 시그널을 같은 단어로 뭉개지 않고 "커널 이벤트 처리"와 "유저 공간 전달 인터페이스"를 분리해서 설명할 수 있는가?
   힌트: 인터럽트·예외는 커널이 먼저 다루는 사건이고, 시그널은 그 결과를 프로세스에 전달하는 별도 인터페이스다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`무슨 명령부터 쳐야 하지?`"가 먼저 막히면: [Beginner Triage Quick-Check Snippet Pack](./beginner-triage-quick-check-snippet-pack.md)
> - "`느리다`를 CPU 포화 / quota throttling / I/O 대기로 더 좁히고 싶다면": [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)
> - "`용어 축이 다시 흐려졌다`"면: [개념 점검용 추천 순서 (self-check 빠른 점검 루트)](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

초급 단계에서 가장 중요한 것은 정확한 root cause 선언이 아니라, 첫 증상을 올바른 primer/deep dive 경로로 보내는 것이다.

개념 축이 흐려졌다면 이 문서 안에서 오래 맴돌기보다 [self-check 빠른 점검 루트](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 바로 점프해 primer 4편을 짧게 재정렬하는 편이 더 빠르다.
