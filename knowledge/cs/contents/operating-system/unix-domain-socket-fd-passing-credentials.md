# UNIX Domain Socket, FD Passing, Credentials

> 한 줄 요약: UNIX domain socket은 단순 로컬 소켓이 아니라, FD 전달과 peer credential 확인까지 가능한 control-plane IPC라서 supervisor, sidecar, local broker 설계에서 특별한 의미를 가진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
> - [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
> - [pidfd Basics, Race-Free Process Handles](./pidfd-basics-race-free-process-handles.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [eventfd, signalfd, Epoll Control-Plane Integration](./eventfd-signalfd-epoll-control-plane-integration.md)

> retrieval-anchor-keywords: UNIX domain socket, unix socket, SCM_RIGHTS, SO_PEERCRED, credential passing, FD passing, ancillary data, sendmsg recvmsg, local control plane, supervisor IPC

## 핵심 개념

UNIX domain socket은 로컬 IPC에 쓰는 소켓이지만, TCP의 로컬 버전 정도로만 보면 반만 이해한 것이다. 이 채널은 file descriptor 전달과 peer identity 확인 같은 OS 특유 기능 때문에, 로컬 control-plane과 runtime handoff에 매우 강력하다.

- `AF_UNIX`: 로컬 커널 내부 IPC 주소 체계다
- `SCM_RIGHTS`: 열린 fd를 다른 프로세스에 전달하는 ancillary data 메커니즘이다
- `SO_PEERCRED` 계열: peer 프로세스 identity를 확인하는 데 쓰인다
- `sendmsg`/`recvmsg`: 데이터와 ancillary data를 함께 실어 나르는 API다

왜 중요한가:

- listener handoff, local broker, privilege separation 설계가 가능하다
- path 이름만이 아니라 peer process identity와 fd ownership을 함께 다룰 수 있다
- pipe로는 어려운 "제어 메시지 + 실제 fd handoff"를 한 채널에서 처리할 수 있다

## 깊이 들어가기

### 1. UDS는 바이트 전달보다 control-plane에 강하다

TCP처럼 payload만 주고받는 용도로도 쓸 수 있지만, 진짜 강점은 control semantics다.

- process A가 열린 socket/file fd를 process B에 넘긴다
- privilege가 다른 helper process 사이에서 handoff가 가능하다
- supervisor가 child에게 pre-opened resource를 전달할 수 있다

이 지점에서 UDS는 단순 stream이 아니라 "커널 객체 handoff bus"가 된다.

### 2. FD passing은 "경로를 넘기는 것"이 아니라 "열린 객체를 넘기는 것"이다

`SCM_RIGHTS`로 넘기는 것은 path string이 아니다.

- 이미 열린 listener socket
- memfd payload
- pre-opened config/data file
- eventfd/pidfd 같은 다른 fd

그래서 receiver는 다시 `open()`하지 않고도 같은 커널 객체를 이어받을 수 있다.

### 3. credential 확인은 로컬 trust boundary를 만든다

같은 머신 안에서도 모든 프로세스를 동일하게 믿을 수는 없다. UDS는 peer credential 확인으로 local trust boundary를 만들 수 있다.

- 누가 연결했는지 확인한다
- 특정 uid/gid/pid만 허용할 수 있다
- sidecar, agent, supervisor 통신에서 유용하다

즉 "로컬이니까 안전하다"가 아니라 "누가 로컬 peer인가"를 커널에서 확인할 수 있다는 점이 중요하다.

### 4. FD handoff 뒤에는 lifecycle 관리가 다시 중요해진다

descriptor를 넘겼다고 끝이 아니다.

- sender가 언제 닫을지
- receiver가 언제 ownership을 가진다고 볼지
- close-on-exec를 어떻게 유지할지
- receiver failure 시 누가 cleanup할지

FD passing은 매우 강력하지만, 설계가 흐리면 숨은 leak와 ownership race를 만들 수 있다.

## 실전 시나리오

### 시나리오 1: supervisor가 worker에 listener를 넘겨 zero-downtime handoff를 한다

가능한 이유:

- worker가 직접 bind/listen하지 않아도 된다
- privilege separation이 쉬워진다
- reload 시 새 worker가 기존 listener를 이어받을 수 있다

주의:

- handoff 시점 ownership을 명확히 정한다
- old worker가 listener를 언제 닫는지 합의한다

### 시나리오 2: local broker가 큰 payload는 memfd로, 제어는 UDS로 보낸다

가능한 이유:

- UDS는 control message와 fd handoff에 강하다
- 큰 blob은 memfd로 별도 전달한다
- wakeup은 eventfd 또는 control message로 분리할 수 있다

### 시나리오 3: 로컬 소켓인데도 잘못된 프로세스가 붙는다

가능한 원인:

- 파일 권한만 믿었다
- peer credential 확인이 없다
- namespace/container 경계를 과신했다

이 경우는 UDS path permission만으로 충분하다고 생각하면 안 된다.

## 코드로 보기

### mental model

```text
control message over AF_UNIX
  + optional ancillary data
  + optional fd handoff via SCM_RIGHTS
  + peer credential check
```

### 핵심 API 감각

```c
socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
sendmsg(...);   // data + ancillary data
recvmsg(...);   // receive data + passed fd
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| pipe | 단순하다 | fd passing과 peer credential 모델이 약하다 | simple stream |
| socketpair/UDS | control-plane과 fd handoff에 강하다 | ancillary data 처리 복잡도가 있다 | supervisor, broker, local RPC |
| eventfd | pure wakeup에 좋다 | payload/credential/fd handoff는 못 한다 | notification only |
| inherited fd only | 단순하다 | dynamic handoff가 어렵다 | fixed startup handoff |

## 꼬리질문

> Q: `SCM_RIGHTS`는 path를 보내는 건가요?
> 핵심: 아니다. 이미 열린 커널 객체에 대한 fd를 전달하는 것이다.

> Q: UNIX domain socket이 pipe보다 좋은 경우는 언제인가요?
> 핵심: 양방향 control, peer credential 확인, fd passing이 필요할 때다.

> Q: 로컬 소켓이면 무조건 신뢰해도 되나요?
> 핵심: 아니다. peer credential과 ownership 설계를 같이 봐야 한다.

## 한 줄 정리

UNIX domain socket은 로컬 바이트 채널이 아니라, fd handoff와 peer identity까지 다루는 backend control-plane IPC 도구다.
