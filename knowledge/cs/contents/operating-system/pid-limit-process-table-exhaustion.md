---
schema_version: 3
title: PID Limits Process Table Exhaustion
concept_id: operating-system/pid-limit-process-table-exhaustion
canonical: true
category: operating-system
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- pid-limit-process
- table-exhaustion
- pids-max
- fork-resource-temporarily
aliases:
- PID limit process table exhaustion
- pids.max
- fork resource temporarily unavailable
- process table full
- cgroup PID exhaustion
- cannot create new process
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/linux-process-state-zombie-orphan.md
- contents/operating-system/container-cgroup-namespace.md
- contents/operating-system/signals-process-supervision.md
- contents/operating-system/fd-exhaustion-ulimit-diagnostics.md
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/container-pid-1-sigterm-zombie-reaping-basics.md
symptoms:
- fork나 process spawn이 실패하고 resource temporarily unavailable이 난다.
- cgroup pids.max 또는 system process table exhaustion 때문에 새 실행 단위를 만들 수 없다.
- zombie process reaping 실패와 PID exhaustion이 연결되어 server가 멈춘다.
expected_queries:
- PID limit과 process table exhaustion은 단순 fork 실패 숫자가 아니야?
- cgroup pids.max 때문에 container가 새 process나 thread를 못 만들 수 있어?
- zombie reaping 실패가 PID exhaustion으로 이어지는지 어떻게 확인해?
- fork resource temporarily unavailable을 FD exhaustion이나 OOM과 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 PID limit이 단순 fork를 막는 숫자가 아니라 process/thread 같은 새 execution unit을
  만들 수 없게 해 server를 멈추게 할 수 있다는 symptom router다. cgroup pids.max,
  process table, zombie reaping, FD/OOM과 구분한다.
---
# PID Limits, Process Table Exhaustion

> 한 줄 요약: PID limits는 단순히 fork를 막는 숫자가 아니라, 프로세스와 cgroup이 더 이상 새 실행 단위를 만들지 못하게 해서 서버를 멈추게 할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [signals, process supervision](./signals-process-supervision.md)
> - [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)

> retrieval-anchor-keywords: pids.max, pids.current, process table, fork failure, EAGAIN, pid exhaustion, zombie accumulation, process limit

## 핵심 개념

Linux는 무한히 많은 프로세스를 만들 수 없다. PID와 process table은 제한이 있고, cgroup pids controller도 프로세스 수를 제한할 수 있다.

- `pids.max`: cgroup에서 허용하는 프로세스 수 상한이다
- `pids.current`: 현재 프로세스 수다
- `fork failure`: 새 프로세스를 못 만들 때 발생하는 실패다
- `zombie`: 종료됐지만 회수되지 않은 프로세스다

왜 중요한가:

- fork/clone 실패는 갑자기 애플리케이션을 멈추게 할 수 있다
- zombie가 쌓이면 PID를 잠식한다
- 컨테이너에서는 호스트와 다른 한도 때문에 더 헷갈린다

이 문서는 [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)와 [container, cgroup, namespace](./container-cgroup-namespace.md)를 PID 상한 관점에서 연결한다.

## 깊이 들어가기

### 1. PID exhaustion은 단순 프로세스 수 증가가 아니다

프로세스가 많다고 무조건 문제가 되는 것은 아니다. 문제는 사용 가능한 PID와 controller limit을 넘는 순간이다.

- zombie가 많이 쌓여도 PID를 소비한다
- fork-bomb 같은 폭주가 빠르게 한계를 치게 할 수 있다
- cgroup pids limit이 낮으면 더 빨리 실패한다

### 2. fork 실패는 보통 `EAGAIN` 형태로 보인다

새 프로세스를 만들 수 없으면 실패가 돌아온다.

- 부모 프로세스는 자식 생성 실패를 보게 된다
- 워커 풀 확장이 멈출 수 있다
- 재시도 루프가 더 큰 문제를 만들 수 있다

### 3. zombie는 PID를 묶어둔다

zombie는 메모리를 크게 쓰지 않아 보여도 PID 슬롯을 차지한다.

- PID 1이나 부모 프로세스가 회수해야 한다
- 누적되면 새 프로세스 생성에 영향을 준다
- container PID namespace에서는 더 혼란스럽다

### 4. process table exhaustion은 서비스 슈퍼비전과 연결된다

프로세스 supervisor가 failover를 시도하려고 새 프로세스를 만들려다 막힐 수 있다. 그럼 recovery 자체가 지연된다.

## 실전 시나리오

### 시나리오 1: 배포 후 워커가 더 이상 늘지 않는다

가능한 원인:

- `pids.max`에 걸렸다
- zombie가 쌓였다
- supervisor가 재기동을 못 한다

진단:

```bash
cat /sys/fs/cgroup/pids.current
cat /sys/fs/cgroup/pids.max
ps -eo stat,pid,ppid,comm | grep Z
```

### 시나리오 2: fork 실패가 간헐적으로 발생한다

가능한 원인:

- burst traffic 동안 worker 생성이 몰린다
- child 회수가 지연된다
- cgroup limit이 과도하게 낮다

### 시나리오 3: 컨테이너 안에서는 멀쩡해 보이는데 호스트에서 이상하다

가능한 원인:

- PID namespace 차이
- 호스트/컨테이너 pids limit 혼동
- supervisor가 다른 namespace에서 돌고 있다

## 코드로 보기

### PID 수 확인

```bash
ps -e --no-headers | wc -l
cat /sys/fs/cgroup/pids.current
```

### zombie 확인

```bash
ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/ {print}'
```

### limit 예시

```bash
echo 1024 > /sys/fs/cgroup/pids.max
```

### fork 실패를 다루는 의사 코드

```c
pid_t pid = fork();
if (pid < 0) {
    // backpressure and alert
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| pids limit 엄격화 | 폭주를 막는다 | 워커 확장에 제약 | 멀티테넌트 |
| limit 완화 | burst 흡수 | process explosion 위험 | 높은 fan-out |
| zombie 회수 개선 | PID 누수를 막는다 | supervisor 설계 필요 | daemon, container |
| worker pool 고정 | 예측 가능하다 | 탄력성이 낮다 | 안정성 우선 |

## 꼬리질문

> Q: PID가 부족하면 왜 위험한가요?
> 핵심: 새 워커, 재기동, recovery가 모두 실패할 수 있기 때문이다.

> Q: zombie는 왜 문제인가요?
> 핵심: 메모리보다 PID 슬롯을 잠식하기 때문이다.

> Q: cgroup pids limit과 시스템 PID limit은 다른가요?
> 핵심: 그렇다. 범위와 적용 층이 다르다.

## 한 줄 정리

PID limits와 process table exhaustion은 새 프로세스 생성 자체를 막아 recovery를 방해할 수 있으므로, zombie 회수와 cgroup pids 설정을 같이 봐야 한다.
