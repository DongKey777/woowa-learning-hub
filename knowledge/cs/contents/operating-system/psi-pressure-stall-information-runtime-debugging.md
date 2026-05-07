---
schema_version: 3
title: PSI Pressure Stall Information Runtime Debugging
concept_id: operating-system/psi-pressure-stall-information-runtime-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 90
review_feedback_tags:
- psi-pressure-stall
- information
- cpu-memory-io
- stall
aliases:
- PSI pressure stall information
- CPU memory IO stall
- pressure runtime debugging
- process cannot move
- resource busy vs stalled
- some full PSI
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/run-queue-load-average-cpu-saturation.md
- contents/operating-system/scheduler-wakeup-latency-runqlat-debugging.md
- contents/operating-system/kswapd-vs-direct-reclaim-latency.md
- contents/operating-system/dirty-throttling-balance-dirty-pages-writeback-stalls.md
- contents/operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md
symptoms:
- 자원이 얼마나 busy인지보다 process가 얼마나 오래 움직이지 못했는지 알고 싶다.
- CPU, memory, I/O pressure가 request p99로 어떻게 드러나는지 분리해야 한다.
- load average나 utilization만으로는 stall 시간을 설명하지 못한다.
expected_queries:
- PSI는 resource가 얼마나 busy한가보다 process가 얼마나 오래 못 움직였는지를 보여줘?
- CPU memory IO some full pressure를 runtime debugging에서 어떻게 해석해?
- load average나 utilization보다 PSI가 p99 latency에 더 직접적인 이유는?
- memory reclaim, dirty throttling, CPU saturation을 PSI로 어떻게 비교해?
contextual_chunk_prefix: |
  이 문서는 PSI를 자원이 얼마나 바쁜가가 아니라 runnable 또는 blocked process가 CPU, memory,
  I/O resource를 기다리느라 얼마나 오래 움직이지 못했는지를 보여주는 runtime debugging signal로
  설명한다.
---
# PSI, Pressure Stall Information, Runtime Debugging

> 한 줄 요약: PSI는 "자원이 얼마나 바쁜가"보다 "프로세스가 얼마나 오래 못 움직였는가"를 보여주는 지표다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: PSI, pressure stall information, cpu.pressure, memory.pressure, io.pressure, some full, cgroup pressure, stall time

## 핵심 개념

PSI(`Pressure Stall Information`)는 Linux가 CPU, memory, I/O 압박 때문에 태스크가 실제로 얼마나 오래 지연됐는지 보여주는 인터페이스다. 단순히 사용률을 보는 것이 아니라, **실행하고 싶었는데 못 했던 시간**을 관찰한다.

- `cpu.pressure`: runnable이었지만 CPU를 못 받은 시간을 본다
- `memory.pressure`: 메모리 회수, reclaim, page fault 때문에 멈춘 시간을 본다
- `io.pressure`: 블록 I/O 대기 때문에 멈춘 시간을 본다
- `some`: 일부 태스크가 막힌 시간이다
- `full`: 모든 태스크가 막혀 시스템이 사실상 멈춘 시간이다

왜 중요한가:

- CPU 100%가 아니어도 심한 압박이 있을 수 있다
- OOM은 최종 결과일 뿐, PSI는 그 전에 보이는 조기 신호다
- container/cgroup 환경에서는 노드 전체가 아니라 워크로드 단위 압력을 읽을 수 있다

이 문서는 [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)에서 말한 pressure를, 실제 운영 관측값으로 어떻게 읽을지에 초점을 둔다.

## 깊이 들어가기

### 1. PSI는 "대기 시간"을 측정한다

CPU 사용률은 "CPU가 일하고 있나"만 보여준다. PSI는 "그 자원을 기다리느라 못 움직인 시간이 얼마나 되나"를 본다.

- runnable인데 CPU를 못 받으면 cpu pressure
- 메모리를 못 얻어 reclaim이 길어지면 memory pressure
- 디스크나 네트워크 저장 경로가 밀리면 io pressure

즉 PSI는 자원의 절대량보다 **대기열의 체감 압력**에 가깝다.

### 2. `some`과 `full`의 차이를 같이 봐야 한다

- `some`: 적어도 일부 태스크가 막혔다
- `full`: 시스템에 남은 태스크가 사실상 없다, 전체가 멈췄다

운영에서는 `some`이 자주 먼저 튄다. `full`은 더 심한 상태다.

따라서 PSI는 "문제가 있는가"보다 "문제가 어느 정도 퍼졌는가"를 분리해준다.

### 3. cgroup PSI는 워크로드 단위로 해석할 수 있다

노드 전체 PSI와 cgroup PSI는 다르다.

- 노드 PSI가 낮아도 특정 cgroup은 압박받을 수 있다
- 컨테이너 CPU quota가 부족하면 cpu PSI가 높아질 수 있다
- memory.high나 memory.max 근처에서 memory PSI가 먼저 튄다

이 지점은 [container, cgroup, namespace](./container-cgroup-namespace.md)와 직접 연결된다.

### 4. PSI는 OOM보다 먼저 나온다

메모리 압박은 보통 다음 흐름으로 악화된다.

reclaim 증가 -> stall 증가 -> page fault/IO 대기 증가 -> throughput 저하 -> OOM 또는 심각한 latency

즉 PSI는 "아직 안 죽었지만 이미 느린 상태"를 보여준다.

## 실전 시나리오

### 시나리오 1: CPU 사용률은 50%인데 p99가 튄다

가능한 원인:

- runnable 태스크가 많지만 quota 때문에 실제 실행이 밀린다
- lock 경쟁이나 간헐적인 scheduler pressure가 있다
- 배치와 API가 같은 cgroup을 공유한다

진단:

```bash
cat /proc/pressure/cpu
cat /sys/fs/cgroup/cpu.pressure
vmstat 1
top -H
```

판단 포인트:

- `cpu.pressure`의 `some`이 지속적으로 높아지는가
- `full`이 튀는가
- run queue와 함께 악화되는가

### 시나리오 2: 메모리 여유가 있는데도 응답이 느려진다

가능한 원인:

- reclaim이 자주 발생한다
- direct reclaim이나 page fault가 길어진다
- page cache가 밀리면서 I/O까지 같이 느려진다

진단:

```bash
cat /proc/pressure/memory
cat /sys/fs/cgroup/memory.pressure
grep -E 'pgfault|pgmajfault' /proc/vmstat
```

### 시나리오 3: 로그 flush나 배치 쓰기 후에 latency가 길어진다

가능한 원인:

- dirty writeback이 몰린다
- 저장장치 큐가 밀린다
- I/O PSI가 먼저 경고를 준다

진단:

```bash
cat /proc/pressure/io
iostat -x 1
pidstat -d 1
```

### 시나리오 4: 컨테이너만 느리고 노드는 멀쩡하다

가능한 원인:

- cgroup quota/throttling
- memory.high 근접으로 pressure 증가
- 특정 IO class가 병목

진단:

```bash
cat /sys/fs/cgroup/cpu.stat
cat /sys/fs/cgroup/cpu.pressure
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.pressure
```

## 코드로 보기

### PSI를 가장 직접적으로 보는 명령

```bash
watch -n 1 'cat /proc/pressure/cpu; echo; cat /proc/pressure/memory; echo; cat /proc/pressure/io'
```

### cgroup 단위로 확인

```bash
cat /sys/fs/cgroup/cpu.pressure
cat /sys/fs/cgroup/memory.pressure
cat /sys/fs/cgroup/io.pressure
```

### 아주 단순한 해석 감각

```text
PSI가 높다
  -> 자원 경합 또는 reclaim이 길다
  -> runnable / alloc / IO wait이 늘어난다
  -> tail latency가 먼저 흔들린다
```

### pressure를 줄이기 위한 제어 예

```bash
# 메모리 압박을 느리게 만들고 싶다면 limit 근처를 완화하거나 작업을 분리한다
echo 8589934592 > /sys/fs/cgroup/memory.max
```

실무에서는 단순히 limit을 키우기보다, 작업 분리와 병목 자원 파악이 먼저다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| PSI 상시 관측 | 조기 경보가 된다 | 지표를 해석해야 한다 | 운영 대시보드 |
| quota 완화 | pressure를 낮출 수 있다 | 노드 공정성이 떨어질 수 있다 | burst 완화 필요 |
| 작업 분리 | pressure 원인을 나눌 수 있다 | 배포/운영 복잡도 증가 | API와 배치 혼재 |
| memory.high 활용 | OOM 전에 완충한다 | latency가 오히려 늘 수 있다 | 컨테이너 메모리 관리 |

PSI는 "무슨 자원이 꽉 찼나"보다 "무엇이 실제로 기다리게 만들었나"를 보기 위한 도구다.

## 꼬리질문

> Q: PSI가 load average보다 나은 점은 무엇인가요?
> 핵심: load average는 큐 압력을, PSI는 실제 stall 시간을 보여준다.

> Q: `some`과 `full`을 왜 구분하나요?
> 핵심: 일부만 막힌 압박과 시스템 전체 정지를 구분해야 하기 때문이다.

> Q: PSI가 높으면 항상 OOM인가요?
> 핵심: 아니다. OOM은 한 결과일 뿐이고, CPU/I/O pressure만 높을 수도 있다.

> Q: cgroup PSI와 node PSI가 다른 이유는?
> 핵심: 자원 경합이 워크로드 경계 안에서만 집중될 수 있기 때문이다.

## 한 줄 정리

PSI는 자원 사용률이 아니라 stall 시간을 보여주므로, OOM과 latency 폭주를 늦기 전에 잡는 데 가장 유용한 운영 신호다.
