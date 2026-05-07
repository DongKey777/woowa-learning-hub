---
schema_version: 3
title: RLIMIT NOFILE NPROC Governance
concept_id: operating-system/rlimit-nofile-nproc-governance
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- rlimit-nofile-nproc
- governance
- rlimit-nofile-rlimit
- nproc
aliases:
- RLIMIT_NOFILE RLIMIT_NPROC
- nofile nproc governance
- fd limit process limit
- ulimit governance
- too many open files
- process spawn limit
intents:
- troubleshooting
- design
- deep_dive
linked_paths:
- contents/operating-system/fd-exhaustion-ulimit-diagnostics.md
- contents/operating-system/pid-limit-process-table-exhaustion.md
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/container-cgroup-namespace.md
symptoms:
- RLIMIT_NOFILE이 낮아 정상 connection workload가 먼저 EMFILE로 막힌다.
- RLIMIT_NPROC나 cgroup pids.max 때문에 worker/thread/process 생성이 실패한다.
- limits를 폭주 방어로 쓰려다 정상 트래픽 headroom까지 잘라 버린다.
expected_queries:
- RLIMIT_NOFILE과 RLIMIT_NPROC는 서버 폭주 방어와 정상 workload headroom을 어떻게 조절해?
- too many open files와 process spawn failure를 limit governance로 어떻게 진단해?
- ulimit, cgroup pids.max, fd exhaustion을 함께 보는 기준은?
- nofile nproc 값을 크게 올리기만 하면 안전한가?
contextual_chunk_prefix: |
  이 문서는 RLIMIT_NOFILE과 RLIMIT_NPROC를 fd와 process/thread count 폭주를 막는 governance로
  보되, 너무 낮으면 정상 workload가 먼저 막힌다는 headroom/trade-off를 다룬다.
---
# RLIMIT NOFILE, NPROC Governance

> 한 줄 요약: `RLIMIT_NOFILE`과 `RLIMIT_NPROC`는 서버가 열 수 있는 fd와 프로세스 수를 제한해 폭주를 막지만, 잘못 잡으면 정상 워크로드도 먼저 막는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)
> - [PID Limits, Process Table Exhaustion](./pid-limit-process-table-exhaustion.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [signals, process supervision](./signals-process-supervision.md)
> - [CFS Bandwidth, Burst Behavior](./cfs-bandwidth-burst-behavior.md)

> retrieval-anchor-keywords: RLIMIT_NOFILE, RLIMIT_NPROC, ulimit -n, ulimit -u, nofile, nproc, soft limit, hard limit, PAM limits

## 핵심 개념

Linux `rlimit`은 프로세스가 사용할 수 있는 자원 상한을 정한다. backend 팀이 가장 자주 보는 건 fd와 process 수다.

- `RLIMIT_NOFILE`: 열린 파일/소켓 수 상한이다
- `RLIMIT_NPROC`: 프로세스 수 상한이다
- `soft limit`: 현재 적용되는 낮은 쪽 한도다
- `hard limit`: soft limit의 상한이다

왜 중요한가:

- connection 많은 서버는 nofile이 낮으면 먼저 죽는다
- worker를 많이 쓰는 서버는 nproc이 낮으면 fork/exec가 막힌다
- 한도를 너무 낮추면 정상 트래픽도 장애로 보인다

이 문서는 [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)와 [PID Limits, Process Table Exhaustion](./pid-limit-process-table-exhaustion.md)을 governance 관점에서 묶는다.

## 깊이 들어가기

### 1. rlimit은 프로세스별 governance다

`rlimit`은 각 프로세스에 개별적으로 적용된다.

- 서비스별로 다르게 줄 수 있다
- 컨테이너와 호스트에서 다르게 보일 수 있다
- soft/hard 구성으로 단계적 제어가 가능하다

### 2. nofile은 연결과 로그를 같이 잡는다

- socket connection
- open file
- pipe
- descriptor-based IPC

모두 `nofile`에 포함된다.

### 3. nproc은 fork/exec 경로를 막는다

- worker spawn
- shell execution
- child process creation

이 단계에서 막히면 회복 경로 자체가 어렵다.

### 4. governance는 단순히 낮추는 일이 아니다

- 너무 높으면 폭주를 허용한다
- 너무 낮으면 정상 부하도 막는다
- 서비스 특성과 재시작 전략이 필요하다

## 실전 시나리오

### 시나리오 1: 연결이 많아지면 `Too many open files`가 뜬다

가능한 원인:

- nofile soft limit이 낮다
- fd leak이 있다
- keep-alive와 worker pool이 커졌다

진단:

```bash
ulimit -n
cat /proc/<pid>/limits | grep -i "open files"
```

### 시나리오 2: worker spawn이 실패한다

가능한 원인:

- nproc limit이 낮다
- zombie가 쌓였다
- container pids limit과 겹친다

진단:

```bash
ulimit -u
cat /proc/<pid>/limits | grep -i processes
cat /sys/fs/cgroup/pids.current
```

### 시나리오 3: 배치 노드와 API 노드의 limit이 같아서 둘 다 불편하다

가능한 원인:

- workloads가 다르다
- 같은 limit이 적절하지 않다
- governance가 분리되지 않았다

## 코드로 보기

### 현재 limit 확인

```bash
ulimit -n
ulimit -u
cat /proc/<pid>/limits
```

### 설정 감각

```bash
ulimit -n 65535
ulimit -u 4096
```

### 단순 모델

```text
soft limit reached
  -> new fd/process creation blocked
hard limit reached
  -> cannot raise without privilege
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 낮은 nofile | 폭주를 막는다 | 정상 연결이 막힐 수 있다 | 소규모 서비스 |
| 높은 nofile | 많은 연결을 수용 | leak 숨김 효과 | 대형 server |
| 낮은 nproc | process explosion 방지 | worker 확장이 막힌다 | container runtime |
| 높은 nproc | spawn 유연성 | 폭주 위험 | fan-out 작업 |

## 꼬리질문

> Q: nofile과 nproc은 무엇을 막나요?
> 핵심: 각각 열린 fd 수와 프로세스 수를 제한한다.

> Q: soft limit과 hard limit의 차이는?
> 핵심: soft는 현재 적용, hard는 상한이다.

> Q: rlimit만 올리면 끝인가요?
> 핵심: 아니다. leak, pids, backpressure까지 봐야 한다.

## 한 줄 정리

`RLIMIT_NOFILE`과 `RLIMIT_NPROC`는 서비스 폭주를 제어하는 기본 장치지만, workload별로 다르게 설계하지 않으면 정상 트래픽도 먼저 막는다.
