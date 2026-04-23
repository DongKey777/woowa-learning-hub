# pidfd Basics, Race-Free Process Handles

> 한 줄 요약: pidfd는 PID 재사용 문제를 피하면서 프로세스를 안정적으로 가리키는 커널 핸들이라, 종료 감시와 signal 전달을 더 안전하게 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [PID Limits, Process Table Exhaustion](./pid-limit-process-table-exhaustion.md)
> - [PID Namespace, Init Semantics](./pid-namespace-init-semantics.md)
> - [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - [signals, process supervision](./signals-process-supervision.md)
> - [UNIX Domain Socket, FD Passing, Credentials](./unix-domain-socket-fd-passing-credentials.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)

> retrieval-anchor-keywords: pidfd, pidfd_open, pidfd_send_signal, PID reuse, race-free handle, process handle, pollable process, waitid

## 핵심 개념

PID는 숫자라 재사용될 수 있다. pidfd는 이 숫자 대신 프로세스를 안정적으로 가리키는 파일 디스크립터다.

- `pidfd_open`: PID를 pidfd로 연다
- `pidfd_send_signal`: pidfd를 통해 signal을 보낸다
- `race-free`: PID 재사용으로 인한 착오를 줄인다

왜 중요한가:

- supervisor가 잘못된 PID에 signal을 보낼 위험을 줄인다
- process lifecycle 관찰이 안정적이다
- container와 namespace 환경에서 유용하다

이 문서는 [PID Limits, Process Table Exhaustion](./pid-limit-process-table-exhaustion.md)와 [PID Namespace, Init Semantics](./pid-namespace-init-semantics.md)를 더 안전한 process handle 관점에서 본다.

## 깊이 들어가기

### 1. PID는 재사용될 수 있다

프로세스가 끝난 뒤 같은 숫자가 다른 프로세스에 할당될 수 있다.

- `kill(pid)`만으로는 race가 생길 수 있다
- supervisor는 잘못된 대상에 signal을 보낼 가능성이 있다
- pidfd는 이런 문제를 줄인다

### 2. pidfd는 파일 디스크립터처럼 다룬다

- poll/epoll과 함께 다룰 수 있다
- 프로세스 종료를 안정적으로 관찰할 수 있다
- FD 기반 관리 모델에 잘 맞는다

### 3. container/supervision과 궁합이 좋다

- PID namespace 안팎에서 더 안전하다
- daemon manager가 child를 안정적으로 제어할 수 있다
- lifecycle race를 줄인다

### 4. pidfd는 만능이 아니라 도구다

- 모든 코드가 pidfd를 쓰는 것은 아니다
- 기존 supervisor와 통합이 필요하다
- 커널/배포판 지원을 확인해야 한다

## 실전 시나리오

### 시나리오 1: supervisor가 가끔 잘못된 프로세스에 signal을 보낸다

가능한 원인:

- PID 재사용 race
- 오래된 PID 캐시
- 프로세스 확인 시점과 signal 시점의 간극

진단 방향:

- pidfd 기반으로 교체 검토
- `waitid`와 process lifecycle 관찰 강화

### 시나리오 2: 종료 감시가 안정적이지 않다

가능한 원인:

- child reaping과 signal 전달이 분리되어 있다
- wrapper가 PID를 잘못 다룬다
- namespace 경계를 오해한다

### 시나리오 3: 컨테이너 운영에서 PID 관리가 자주 꼬인다

가능한 원인:

- namespace별 PID가 다르다
- host PID와 container PID를 혼동한다
- zombie/exit 감시가 분산돼 있다

## 코드로 보기

### pidfd 개념 감각

```text
open pidfd for process
  -> keep stable handle
  -> signal or poll on handle
  -> avoid PID reuse race
```

### 핵심 API 이름

```c
pidfd_open(pid, 0);
pidfd_send_signal(pidfd, SIGTERM, NULL, 0);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| pidfd 사용 | race를 줄인다 | 코드와 환경이 더 복잡하다 | supervisor |
| pid 숫자만 사용 | 단순하다 | 재사용 race가 있다 | 작은 도구 |
| pidfd + poll | 종료 관찰이 쉽다 | 호환성 확인 필요 | runtime manager |

## 꼬리질문

> Q: pidfd는 왜 필요한가요?
> 핵심: PID 재사용으로 인한 race를 줄이기 위해서다.

> Q: pidfd와 kill(pid)의 차이는?
> 핵심: pidfd는 안정적인 핸들, kill은 숫자 PID를 직접 쓴다.

> Q: pidfd는 어디에 유용한가요?
> 핵심: supervisor, container runtime, lifecycle 관리다.

## 한 줄 정리

pidfd는 PID 재사용 race를 줄이는 안정적인 process handle이라서, supervisor와 container runtime에 특히 유용하다.
