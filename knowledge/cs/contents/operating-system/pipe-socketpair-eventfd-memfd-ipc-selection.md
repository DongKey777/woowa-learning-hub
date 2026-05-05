---
schema_version: 3
title: pipe, socketpair, eventfd, memfd IPC Selection
concept_id: operating-system/pipe-socketpair-eventfd-memfd-ipc-selection
canonical: false
category: operating-system
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- ipc-primitive-selection
- control-plane-vs-data-plane
- pipe-vs-socketpair-boundary
aliases:
- pipe socketpair eventfd memfd chooser
- local ipc primitive selection
- pipe vs socketpair
- eventfd wakeup fd basics
- memfd local payload handoff
- local control plane ipc
- backend runtime ipc chooser
- 로컬 ipc primitive 비교
- wakeup fd 선택 기준
- control plane data plane 분리
symptoms:
- 로컬 IPC가 다 fd처럼 보여서 pipe와 socketpair를 언제 갈라야 할지 모르겠어요
- wakeup만 필요할 때도 pipe를 써서 eventfd가 왜 따로 있는지 감이 안 와요
- 큰 payload 전달, 제어 메시지, stdout capture를 한 기준으로 분리하지 못하겠어요
intents:
- comparison
- design
prerequisites:
- operating-system/process-lifecycle-and-ipc-basics
- operating-system/subprocess-fd-hygiene-basics
next_docs:
- operating-system/eventfd-signalfd-epoll-control-plane-integration
- operating-system/unix-domain-socket-fd-passing-credentials
- operating-system/tmpfs-shmem-cgroup-memory-accounting
linked_paths:
- contents/operating-system/process-lifecycle-and-ipc-basics.md
- contents/operating-system/eventfd-signalfd-epoll-control-plane-integration.md
- contents/operating-system/unix-domain-socket-fd-passing-credentials.md
- contents/operating-system/tmpfs-shmem-cgroup-memory-accounting.md
- contents/operating-system/o-cloexec-fd-inheritance-exec-leaks.md
- contents/operating-system/signals-process-supervision.md
- contents/operating-system/io-models-and-event-loop.md
confusable_with:
- operating-system/process-lifecycle-and-ipc-basics
- operating-system/eventfd-signalfd-epoll-control-plane-integration
- operating-system/unix-domain-socket-fd-passing-credentials
forbidden_neighbors:
- contents/operating-system/eventfd-signalfd-epoll-control-plane-integration.md
- contents/operating-system/unix-domain-socket-fd-passing-credentials.md
expected_queries:
- 부모 자식 프로세스 통신에서 pipe, socketpair, eventfd, memfd를 어떤 질문으로 골라야 해?
- stdout 캡처, 제어 메시지, wakeup 신호, 큰 payload 전달을 IPC primitive 기준으로 나눠서 설명해줘
- eventfd는 언제 pipe보다 맞고 memfd는 왜 데이터 전달 도구로 따로 보나?
- 로컬 IPC 설계에서 socketpair와 pipe를 헷갈리지 않게 선택 기준을 알려줘
- fd처럼 보이는 IPC 도구들을 control plane과 data plane 관점으로 비교해줘
contextual_chunk_prefix: |
  이 문서는 운영체제 학습자가 로컬 IPC에서 pipe, socketpair, eventfd,
  memfd를 어떤 역할로 나눌지 결정하게 돕는 chooser다. 한쪽으로 흘리는
  바이트 통로, 서로 주고받는 제어 채널, 깨우기 전용 신호, 큰 payload
  handoff, control plane과 data plane 분리, EOF와 shutdown 차이,
  출력 가로채기와 제어 메시지 구분 같은 자연어 paraphrase가 본 문서의
  선택 기준에 매핑된다.
---
# pipe, socketpair, eventfd, memfd IPC Selection

> 한 줄 요약: 로컬 IPC primitive는 모두 fd처럼 보이지만 payload 모델, backpressure, epoll 적합성, lifecycle이 달라서 backend 런타임의 wakeup 경로와 데이터 전달 경로를 완전히 다르게 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
> - [eventfd, signalfd, Epoll Control-Plane Integration](./eventfd-signalfd-epoll-control-plane-integration.md)
> - [UNIX Domain Socket, FD Passing, Credentials](./unix-domain-socket-fd-passing-credentials.md)
> - [tmpfs, shmem, /dev/shm, Cgroup Memory Accounting](./tmpfs-shmem-cgroup-memory-accounting.md)
> - [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
> - [signals, process supervision](./signals-process-supervision.md)
> - [I/O Models and Event Loop](./io-models-and-event-loop.md)

> retrieval-anchor-keywords: pipe, socketpair, eventfd, memfd, local IPC, UNIX domain socket, FD passing, SCM_RIGHTS, pipe2, socketpair IPC, memfd_create, wakeup fd

## 핵심 개념

백엔드 런타임이 로컬 프로세스/스레드 사이에서 통신할 때 `pipe`, `socketpair`, `eventfd`, `memfd`는 자주 비슷하게 취급된다. 하지만 실제로는 "바이트 스트림이 필요한가", "순수 wakeup만 필요한가", "큰 payload를 zero-copy에 가깝게 넘길 것인가", "epoll에 넣어 제어 경로를 통합할 것인가"에 따라 정답이 달라진다.

- `pipe`: 단방향 byte stream이다
- `socketpair`: 양방향으로 연결된 local socket pair다
- `eventfd`: counter 기반 notification fd다
- `memfd_create`: tmpfs 기반의 anonymous file fd를 만든다

왜 중요한가:

- pure wakeup인데 pipe를 쓰면 payload 없는 바이트 관리가 오히려 복잡해진다
- request/response 제어 채널인데 eventfd를 쓰면 메시지 표현력이 부족하다
- 큰 payload를 pipe로 밀면 copy와 buffer pressure가 커질 수 있다
- primitive 선택이 곧 EOF, shutdown, `epoll`, `CLOEXEC`, fd passing 전략을 결정한다

## 깊이 들어가기

### 1. `pipe`는 가장 단순하지만 방향이 분명하다

`pipe`는 한쪽이 쓰고 다른 쪽이 읽는 단방향 data channel이다.

- stdout/stderr capture
- parent -> child 또는 child -> parent 스트리밍
- EOF 의미가 분명하다

좋은 점:

- 단순하고 폭넓게 쓰인다
- backpressure와 close semantics가 직관적이다

주의할 점:

- 양방향이면 보통 두 개가 필요하다
- payload framing은 직접 해야 한다
- write end 정리가 어긋나면 reader가 EOF를 못 본다

### 2. `socketpair`는 control channel에 더 잘 맞는다

`socketpair(AF_UNIX, ...)`는 unnamed pair of connected sockets다. 두 소켓은 대칭적이고, 양방향 통신이 가능하다.

- parent/child supervisor control channel
- local request/response
- fd passing이 필요한 control plane

좋은 점:

- 양방향이다
- `sendmsg`/`recvmsg` 기반 ancillary data를 붙이기 쉽다
- `SOCK_CLOEXEC`, `SOCK_NONBLOCK`로 생성 시점 hygiene를 맞추기 좋다

주의할 점:

- pipe보다 단순하지는 않다
- stream/message 경계를 어떻게 다룰지 정해야 한다

### 3. `eventfd`는 payload가 아니라 wakeup을 위한 도구다

`eventfd`는 "일이 생겼다"는 신호를 저비용으로 전달하는 데 적합하다.

- queue push 후 event loop wakeup
- reactor thread notification
- lightweight control wakeup

좋은 점:

- `epoll`과 잘 맞는다
- byte payload framing이 필요 없다
- counter semantics라 coalescing이 쉽다

주의할 점:

- 메시지 자체를 실어 나르는 용도는 아니다
- 결국 별도의 shared queue나 state와 같이 써야 한다

즉 `eventfd`는 data plane이 아니라 control plane primitive다.

### 4. `memfd`는 "큰 데이터를 fd처럼 공유"할 때 강하다

`memfd_create()`는 tmpfs 기반 anonymous file을 만든다. `ftruncate`, `mmap`, sealing과 결합하면 local large payload handoff에 유용하다.

- 큰 config blob, rendered artifact, serialized snapshot
- local zero-copy에 가까운 handoff
- producer가 만든 메모리성 파일을 consumer에 전달

좋은 점:

- 파일처럼 다룰 수 있고 `mmap` 가능하다
- tmpfs/shmem 기반이라 local memory path와 잘 맞는다
- sealing으로 "이제 수정 금지" 같은 계약을 만들 수 있다

주의할 점:

- 결국 tmpfs/shmem 메모리를 먹는다
- 보통 `socketpair`나 inherited fd로 descriptor 전달이 같이 필요하다
- wakeup 도구는 아니므로 control 채널과 분리하는 편이 낫다

## 실전 시나리오

### 시나리오 1: 다른 스레드가 event loop를 깨우기만 하면 된다

권장 감각:

- payload는 lock-free queue나 별도 구조체에 둔다
- wakeup만 `eventfd`로 보낸다
- pure notification에 pipe를 남용하지 않는다

### 시나리오 2: parent와 child가 제어 메시지를 주고받아야 한다

권장 감각:

- 양방향 channel이 필요하면 `socketpair`가 자연스럽다
- 향후 fd passing 가능성까지 있으면 더 유리하다
- close-on-exec와 nonblocking을 생성 시점에 맞춘다

### 시나리오 3: 큰 payload를 여러 번 복사하지 않고 넘기고 싶다

권장 감각:

- `memfd_create`로 payload를 만든다
- `ftruncate` + `mmap`으로 채운다
- `socketpair` 또는 다른 FD 경로로 descriptor를 넘긴다
- wakeup은 `eventfd`나 control message로 따로 준다

### 시나리오 4: 로그/출력 스트림을 부모가 받아야 한다

권장 감각:

- 단순 stdout/stderr capture는 `pipe`가 맞다
- EOF를 정확히 만들려면 불필요한 write end를 즉시 닫는다
- exec 경로에서는 `pipe2(O_CLOEXEC)`를 기본값으로 둔다

## 코드로 보기

### pipe

```c
int p[2];
pipe2(p, O_CLOEXEC | O_NONBLOCK);
```

### socketpair

```c
int sv[2];
socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0, sv);
```

### eventfd

```c
int efd = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK);
```

### memfd

```c
int mfd = memfd_create("payload", MFD_CLOEXEC | MFD_ALLOW_SEALING);
ftruncate(mfd, size);
```

### mental model

```text
need stream bytes?
  -> pipe
need bidirectional control and maybe fd passing?
  -> socketpair
need pure wakeup?
  -> eventfd
need large shared payload as fd/mmap object?
  -> memfd
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| pipe | 단순하고 EOF semantics가 좋다 | 단방향이고 framing이 필요하다 | stdout/stderr, simple streams |
| socketpair | 양방향 control channel에 좋다 | pipe보다 무겁고 설계 선택이 많다 | supervisor, local RPC |
| eventfd | wakeup에 매우 적합하다 | payload channel은 아니다 | reactor/control wakeup |
| memfd | 큰 local payload handoff에 좋다 | tmpfs memory와 fd 전달 설계가 필요하다 | blobs, snapshots, mmap sharing |

## 꼬리질문

> Q: event loop wakeup에 왜 pipe 대신 `eventfd`를 쓰나요?
> 핵심: pure notification에는 byte stream보다 counter-based wakeup이 더 단순하고 의미가 분명하기 때문이다.

> Q: `socketpair`가 pipe보다 나은 경우는 언제인가요?
> 핵심: 양방향 control, fd passing, local RPC 같은 대칭 channel이 필요할 때다.

> Q: `memfd`는 shared memory와 같은가요?
> 핵심: tmpfs 기반 anonymous file을 fd로 다루는 방식이라 mmap/shared-memory 패턴에 잘 맞지만, lifecycle과 fd 전달까지 같이 설계해야 한다.

## 한 줄 정리

local IPC primitive 선택은 API 취향 문제가 아니라, "stream/control/wakeup/large payload" 중 무엇이 핵심인지에 따라 backend runtime의 디버깅성과 안정성을 바꾸는 설계 선택이다.
