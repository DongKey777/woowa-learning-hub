---
schema_version: 3
title: System Call Basics
concept_id: operating-system/syscall-basics
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 74
review_feedback_tags:
- syscall
- system-call
- kernel-privileged-operation
- user-program-requests
aliases:
- system call basics
- syscall basics
- kernel privileged operation
- user program requests OS
- file read write process creation syscall
intents:
- definition
- deep_dive
linked_paths:
- contents/operating-system/syscall-user-kernel-boundary.md
- contents/operating-system/file-descriptor-basics.md
- contents/operating-system/process-lifecycle-and-ipc-basics.md
- contents/operating-system/interrupt-basics.md
- contents/operating-system/ebpf-perf-strace-production-tracing.md
expected_queries:
- system call은 program이 OS kernel에게 특권 작업을 요청하는 정식 경로야?
- file read write process creation 같은 작업은 왜 syscall을 거쳐야 해?
- user program과 kernel이 만나는 초급 mental model을 설명해줘
- syscall basics 다음에 user-kernel boundary를 어떻게 이어서 보면 돼?
contextual_chunk_prefix: |
  이 문서는 system call을 application이 file I/O, socket I/O, process creation, memory mapping 같은
  privileged operation을 OS kernel에 요청하는 formal entrypoint로 설명하는 beginner primer다.
---
# 시스템 콜 기초

> 한 줄 요약: 시스템 콜은 프로그램이 OS 커널에게 파일 읽기·쓰기·프로세스 생성 같은 특권 작업을 요청하는 유일한 정식 경로다.

**난이도: 🟢 Beginner**

관련 문서:

- [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
- [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [operating-system 카테고리 인덱스](./README.md)
- [TCP/UDP Basics](../network/tcp-udp-basics.md)

retrieval-anchor-keywords: syscall beginner, system call basics, user space kernel space, kernel mode user mode, read write syscall, os api basics, 시스템 콜이란, 시스템 콜 예시, syscall vs context switch, system call context switch difference, 시스템 콜 컨텍스트 스위치 차이, syscall self check, 시스템 콜 자가 점검, syscall concept check, syscall next doc

## Self-check Primer Handoff

> **이 문서는 self-check 빠른 점검 루트의 4단계다**
>
> - 언제 읽나: process/thread, scheduler, memory 큰 그림은 다시 잡았는데 "앱이 커널에 요청한다"는 경계 설명이 아직 추상적일 때 읽는다.
> - 선행 문서: [메모리 관리 기초](./memory-management-basics.md)까지 읽고 오면 page fault 같은 메모리 사건과 syscall 같은 커널 진입 요청을 덜 섞는다.
> - 후행 문서: [Operating System README - 개념 점검용 추천 순서](./README.md#개념-점검용-추천-순서-self-check-빠른-점검-루트)로 돌아가 self-check를 마무리하고, 막힌 축에 따라 다음 primer나 bridge를 고른다.

## 먼저 잡는 멘탈 모델

- 프로그램은 "내가 직접 하드웨어를 만지는 주체"가 아니라, 커널에게 요청하는 클라이언트다.
- 시스템 콜은 함수 이름 암기가 아니라, **유저 공간 -> 커널 공간으로 넘어가는 요청 게이트**다.
- 성능 관점의 핵심은 "시스템 콜 개수"보다 **불필요한 왕복이 반복되는 구조인지**를 먼저 보는 것이다.

## 핵심 개념

일반 프로그램은 하드웨어에 직접 접근할 수 없다. 디스크에서 파일을 읽거나, 네트워크 소켓을 열거나, 새 프로세스를 만드는 일은 모두 **커널(kernel)**만 할 수 있다.

프로그램이 이런 작업을 요청하는 방법이 **시스템 콜(system call)**이다. 프로그램은 "나 대신 이 작업을 해달라"고 OS에 요청하고, OS는 작업을 수행한 뒤 결과를 돌려준다.

이 구분이 중요한 이유는 안전성이다. 모든 프로그램이 하드웨어에 직접 접근할 수 있으면 악의적 코드나 버그가 다른 프로세스의 메모리를 덮어쓰거나 하드웨어를 망가뜨릴 수 있다. 시스템 콜 경계가 이를 막는다.

## 한눈에 보기

프로그램은 유저 모드에서 실행되고, 시스템 콜을 통해서만 커널 모드로 진입할 수 있다. 이 경계 전환이 시스템 콜의 핵심이다.

```text
프로그램 코드              OS 커널
(User Mode)               (Kernel Mode)
    │
    │  System Call
    │ ─────────────▶  작업 수행
    │                 (파일 읽기, 소켓 열기 등)
    │ ◀─────────────  결과 반환
    │
    ▼
다음 코드 실행
```

유저 모드와 커널 모드 전환 자체도 비용이 있다. 시스템 콜이 많아지면 이 전환 비용이 누적된다.

자주 쓰이는 시스템 콜 분류:

| 분류 | 예시 | 설명 |
|------|------|------|
| 파일 I/O | `read`, `write`, `open`, `close` | 파일 읽기·쓰기 |
| 프로세스 | `fork`, `exec`, `exit` | 프로세스 생성·종료 |
| 네트워크 | `socket`, `connect`, `accept` | 소켓 통신 |
| 메모리 | `mmap`, `brk` | 메모리 매핑 |

## 아주 작은 예시: 파일 4KB 읽기 한 번의 왕복

1. 애플리케이션이 `read(fd, buf, 4096)`을 호출한다.
2. CPU가 유저 모드에서 커널 모드로 전환된다.
3. 커널이 fd 유효성, 권한, 버퍼 위치를 확인하고 데이터를 복사한다.
4. 바이트 수(또는 오류 코드)를 반환하고 유저 모드로 돌아온다.

포인트: 개발자가 보는 건 함수 한 줄이지만, OS 관점에서는 "경계 왕복 + 검증 + 복사 + 반환"이 한 묶음으로 일어난다.

## 자주 섞이는 개념: 시스템 콜 vs 컨텍스트 스위치

> **짧은 비교 박스**
>
> 시스템 콜은 "지금 실행 중인 스레드가 커널에게 요청하는 입구"이고, 컨텍스트 스위치는 "CPU가 다른 실행 흐름으로 넘어가는 전환"이다. 시스템 콜이 있어도 같은 스레드로 바로 돌아오면 컨텍스트 스위치가 아닐 수 있다.

| 질문 | 시스템 콜 | 컨텍스트 스위치 |
|------|-----------|------------------|
| 무엇이 바뀌나 | 유저 모드 -> 커널 모드 -> 유저 모드 | 실행 중인 태스크/스레드 |
| 항상 다른 스레드로 넘어가나 | 아니다 | 보통 그렇다 |
| 쉬운 예시 | `read()` 호출 | `read()` 대기 중 현재 스레드가 잠들고 다른 스레드 실행 |

작은 예시로 보면 더 쉽다.

- `getpid()`처럼 짧게 끝나는 시스템 콜은 커널에 잠깐 들어갔다가 **같은 스레드로 바로 돌아올 수 있다.**
- 반대로 `read()`가 디스크나 소켓 데이터를 기다리며 block되면, 그 순간 스케줄러가 다른 runnable 스레드를 선택하면서 **컨텍스트 스위치가 이어질 수 있다.**
- 즉, **시스템 콜이 컨텍스트 스위치를 "부를 수는" 있지만, 시스템 콜 자체가 곧 컨텍스트 스위치는 아니다.**

이 구분이 아직 흐리다면 먼저 [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)의 비교표를 보고 오면 훨씬 덜 섞인다.

## 상세 분해

### 유저 모드와 커널 모드

CPU는 두 가지 실행 모드를 가진다.

- **유저 모드(user mode)**: 일반 프로그램이 실행되는 모드. 하드웨어 직접 접근, 다른 프로세스 메모리 접근 등이 금지된다.
- **커널 모드(kernel mode)**: OS가 실행되는 모드. 모든 하드웨어 접근이 허용된다.

시스템 콜이 호출되면 CPU가 유저 모드에서 커널 모드로 전환한다. 완료되면 다시 유저 모드로 돌아온다.

### 자주 쓰이는 시스템 콜 예시

| 분류 | 시스템 콜 | 역할 |
|------|-----------|------|
| 파일 I/O | `read`, `write`, `open`, `close` | 파일 읽기·쓰기·열기·닫기 |
| 프로세스 | `fork`, `exec`, `waitpid`, `exit` | 프로세스 생성·대체·종료·회수 |
| 메모리 | `mmap`, `brk` | 메모리 매핑 및 힙 크기 조절 |
| 네트워크 | `socket`, `connect`, `accept` | 소켓 생성 및 연결 |
| 시그널 | `kill`, `signal` | 시그널 전달 및 처리 등록 |

### 표준 라이브러리와의 관계

`printf()`, `fopen()` 같은 C 표준 라이브러리 함수는 시스템 콜이 아니다. 내부적으로 `write()`, `open()` 같은 시스템 콜을 감싸는 래퍼(wrapper)다. Java의 파일 I/O도 결국 JVM이 OS 시스템 콜을 호출하는 구조다.

## 흔한 오해와 함정

- "라이브러리 함수 호출 = 시스템 콜" — 라이브러리 함수는 유저 모드에서 실행되고, 필요할 때만 시스템 콜을 부른다. 모든 함수 호출이 커널 전환을 일으키지 않는다.
- "시스템 콜은 느리다" — 커널 전환 비용이 있지만, 현대 OS는 이를 최소화하도록 최적화했다. 불필요한 반복 호출이 아니라면 병목이 되지 않는다.
- "Java 개발자는 시스템 콜을 몰라도 된다" — 파일·소켓·스레드 관련 성능 문제를 분석할 때 시스템 콜 관점이 없으면 병목 원인을 찾기 어렵다.
- "시스템 콜 = 컨텍스트 스위치" — 다르다. 시스템 콜은 모드 전환이고, 컨텍스트 스위치는 실행 주체(스레드/프로세스) 전환이다. 바로 위 비교 박스와 [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)를 같이 보면 구분이 빨라진다.

## 다음으로 어디를 읽을까? (초심자 라우팅)

- `read()/write()` 호출이 왜 막히는지부터 보고 싶다면: [동기/비동기와 블로킹/논블로킹 기초](./sync-async-blocking-nonblocking-basics.md)
- `시스템 콜`과 `컨텍스트 스위치`가 자꾸 같은 말처럼 들린다면: [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
- `fork()/exec()/waitpid()` 같은 프로세스 계열 시스템 콜 흐름이 헷갈린다면: [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- 시스템 콜 경계 비용과 보안 필터링까지 확장하고 싶다면: [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)

## 실무에서 쓰는 모습

백엔드 서버에서 성능 문제를 분석할 때 `strace`(Linux) 명령어로 프로세스가 어떤 시스템 콜을 얼마나 부르는지 확인한다.

```
strace -c java -jar myapp.jar
```

이 명령은 시스템 콜 종류별 호출 수와 시간을 요약해 준다. 파일 I/O 시스템 콜이 예상보다 많거나, 특정 시스템 콜에서 시간이 오래 걸리는 패턴을 발견할 수 있다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`시스템 콜`과 `컨텍스트 스위치`를 먼저 분리해 보고 싶다"면: [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
> - "유저/커널 경계를 더 정확히" 보려면: [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)
> - "운영에서 시스템 콜 병목을 추적"하려면: [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)
> - "허용/차단 정책까지" 확장하려면: [seccomp 기초 (백엔드 팀용)](./seccomp-basics-backend-teams.md)

## 더 깊이 가려면

- [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md) — 전환 비용, vDSO, seccomp 같은 심화 주제로 내려간다.
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md) — `fork()`, `exec()`, `waitpid()` 등 프로세스 관련 시스템 콜의 실제 흐름을 본다.

## 면접/시니어 질문 미리보기

1. **유저 모드와 커널 모드를 나누는 이유는 무엇인가요?**
   의도: 보안·격리 목적 이해 확인. 핵심 답: "프로그램이 하드웨어에 직접 접근하지 못하게 막아 다른 프로세스와 시스템 자체를 보호한다."

2. **라이브러리 함수와 시스템 콜의 차이는?**
   의도: 추상화 계층 이해 확인. 핵심 답: "라이브러리 함수는 유저 모드에서 실행되는 래퍼이고, 시스템 콜은 커널에 직접 요청하는 인터페이스다."

## Self-check (자가 점검 5문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. `printf()`가 항상 시스템 콜을 즉시 일으키는가?
   힌트: 보통 아니다. 표준 출력 버퍼링 때문에 나중에 `write()`로 묶여 내려갈 수 있다.
2. 시스템 콜과 컨텍스트 스위치가 같은 개념인가?
   힌트: 아니다. 시스템 콜은 모드 전환이고, 컨텍스트 스위치는 실행 주체 교체까지 포함하는 더 넓은 개념이다.
3. 시스템 콜이 많은 코드에서 먼저 의심할 것은 "개수 자체"인가, "왕복 구조"인가?
   힌트: 먼저 왕복 구조를 본다. 잘못된 반복 설계가 같은 콜을 과도하게 부르는 경우가 많다.
4. `fork()/exec()` 계열이 헷갈릴 때 다음 문서로 어디를 가야 하는가?
   힌트: 프로세스 생성/대체 흐름은 [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)로 바로 이어 보면 된다.
5. 내 질문이 "커널에 어떤 요청을 보내는가"인지, 아니면 "프로세스와 스레드를 어떻게 나누는가"인지 먼저 분기할 수 있는가?
   힌트: `read`, `write`, `accept`, `fork`, `exec`처럼 커널 호출 경계가 핵심이면 시스템 콜 branch다. 메모리 공유, 격리, 실행 단위 비교가 핵심이면 [프로세스와 스레드 기초](./process-thread-basics.md)로 가고, 호출 경계 비용과 의미가 핵심이면 [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)로 이어지면 된다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`시스템 콜`과 `컨텍스트 스위치`가 왜 다른지 한 장으로 다시 보고 싶다"면: [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
> - "`시스템 콜`은 실제로 어떤 경계 비용을 만들지?`"가 궁금하면: [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)
> - "`운영에서 syscall 병목은 어떤 도구로 추적하지?`"가 궁금하면: [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)
> - "`fork()`, `exec()`, `waitpid()`는 호출 흐름에서 어떻게 이어지지?`"가 궁금하면: [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
> - "`허용/차단 정책`까지 같이 보면 무엇이 달라지지?`"가 궁금하면: [seccomp 기초 (백엔드 팀용)](./seccomp-basics-backend-teams.md)
> - "`다른 operating-system primer는 어디서 다시 고르지?`"가 궁금하면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

시스템 콜은 유저 모드 프로그램이 OS 커널의 특권 기능을 안전하게 빌려 쓰는 유일한 정식 창구다.
