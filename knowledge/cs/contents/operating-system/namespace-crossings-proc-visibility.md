---
schema_version: 3
title: Namespace Crossings proc Visibility
concept_id: operating-system/namespace-crossings-proc-visibility
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- namespace-crossings-proc
- visibility
- namespace-crossing-proc
- container-proc-view
aliases:
- namespace crossing proc visibility
- container proc view
- PID namespace visibility
- host vs container proc
- nsenter diagnostics
- process identity namespace
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/container-cgroup-namespace.md
- contents/operating-system/pid-namespace-init-semantics.md
- contents/operating-system/pid-limit-process-table-exhaustion.md
- contents/operating-system/fd-exhaustion-ulimit-diagnostics.md
- contents/operating-system/signals-process-supervision.md
- contents/operating-system/container-pid-1-sigterm-zombie-reaping-basics.md
symptoms:
- host와 container 안에서 같은 process의 PID나 /proc path가 다르게 보인다.
- nsenter나 kubectl exec 위치에 따라 fd, signal, process visibility가 달라진다.
- 진단 명령을 어디서 실행했는지 고정하지 않아 서로 다른 관측을 섞는다.
expected_queries:
- namespace를 넘나들면 /proc visibility와 PID가 왜 다르게 보여?
- container 안과 host에서 같은 process를 진단할 때 무엇을 먼저 고정해야 해?
- nsenter로 들어간 namespace에 따라 fd, signal, process table이 어떻게 달라져?
- PID namespace와 /proc visibility를 runtime debugging에서 어떻게 해석해?
contextual_chunk_prefix: |
  이 문서는 namespace crossing 상황에서 같은 process와 /proc path가 host, container,
  target namespace에 따라 다르게 보일 수 있으므로 진단의 첫 질문은 어디서 보고 있는가를
  고정하는 것이라고 설명한다.
---
# Namespace Crossings, /proc Visibility

> 한 줄 요약: namespace를 넘나들면 같은 프로세스와 /proc 경로가 다르게 보이므로, 진단은 "어디서 보고 있나"를 먼저 고정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [PID Namespace, Init Semantics](./pid-namespace-init-semantics.md)
> - [PID Limits, Process Table Exhaustion](./pid-limit-process-table-exhaustion.md)
> - [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)
> - [signals, process supervision](./signals-process-supervision.md)

> retrieval-anchor-keywords: namespace crossing, /proc visibility, /proc/PID/ns, /proc/PID/root, nsenter, mount namespace, pid namespace, procfs

## 핵심 개념

namespace는 프로세스가 보는 세계를 나눈다. `/proc`은 현재 namespace 기준으로 보이는 정보를 제공하므로, namespace를 넘어서면 같은 대상도 다르게 보일 수 있다.

- `procfs`: 프로세스 정보를 보여주는 가상 파일 시스템이다
- `/proc/<pid>/ns`: 프로세스 namespace 링크를 보여준다
- `/proc/<pid>/root`: 그 프로세스가 보는 루트다

왜 중요한가:

- host와 container에서 보이는 PID가 다르다
- mount namespace를 넘으면 파일 경로가 달라진다
- 진단 위치를 잘못 잡으면 사실과 다르게 해석할 수 있다

이 문서는 [container, cgroup, namespace](./container-cgroup-namespace.md)와 [PID Namespace, Init Semantics](./pid-namespace-init-semantics.md)를 `/proc` 시점에서 묶는다.

## 깊이 들어가기

### 1. /proc은 현재 시야의 산물이다

같은 PID라도 namespace가 다르면 다르게 보인다.

- host와 container의 `/proc`은 같지 않다
- 진단 대상 프로세스의 namespace를 맞춰야 한다
- `nsenter`가 중요하다

### 2. namespace crossing은 경로와 권한을 바꾼다

- mount namespace: 파일 경로가 달라진다
- pid namespace: PID 숫자가 달라진다
- network namespace: 인터페이스/포트가 달라진다

### 3. /proc visibility는 디버깅의 출발점이다

진단 전에 다음을 먼저 확인한다.

- 지금 host namespace인지
- target process namespace인지
- `/proc/<pid>/root`가 어디를 가리키는지

### 4. 경계를 넘나들면 같은 명령도 다르게 동작한다

예를 들어 `ps`, `ls`, `cat /proc/1/status`는 namespace에 따라 전혀 다른 세계를 보여준다.

## 실전 시나리오

### 시나리오 1: 컨테이너 안에서는 PID가 다르게 보인다

가능한 원인:

- PID namespace가 분리됐다
- host PID와 container PID를 혼동했다

진단:

```bash
ls -l /proc/<pid>/ns
nsenter --target <host-pid> --pid --mount --uts --net sh
```

### 시나리오 2: 파일이 있는데 컨테이너 안에서 안 보인다

가능한 원인:

- mount namespace가 다르다
- `/proc/<pid>/root`가 다른 루트를 가리킨다

### 시나리오 3: 진단 스크립트가 host에서는 되는데 container에서는 다르다

가능한 원인:

- proc visibility 차이
- capability나 permission 차이
- namespace crossing 미고려

## 코드로 보기

### namespace 링크 확인

```bash
ls -l /proc/<pid>/ns
ls -l /proc/<pid>/root
```

### namespace 진입

```bash
nsenter --target <host-pid> --pid --mount --uts --net sh
```

### 단순 모델

```text
same process
  -> different namespace
  -> different /proc view
  -> different diagnosis if context is wrong
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| host에서 진단 | 전체를 본다 | container context를 놓칠 수 있다 | 노드 장애 |
| namespace 안에서 진단 | 대상과 일치한다 | host와 차이를 이해해야 한다 | 컨테이너 장애 |
| nsenter 활용 | 정확한 시야를 얻는다 | 사용이 복잡하다 | 심화 분석 |

## 꼬리질문

> Q: /proc은 왜 namespace마다 다르게 보이나요?
> 핵심: 현재 프로세스의 namespace 시야를 반영하기 때문이다.

> Q: `/proc/<pid>/root`는 무엇을 보여주나요?
> 핵심: 그 프로세스가 보는 루트 디렉터리다.

> Q: namespace crossing 진단의 첫 단계는?
> 핵심: 지금 어디 시야에서 보고 있는지 고정하는 것이다.

## 한 줄 정리

namespace crossing에서는 /proc의 관측 시야가 바뀌므로, host와 container의 PID, root, network를 같은 맥락에서 맞춰 봐야 한다.
