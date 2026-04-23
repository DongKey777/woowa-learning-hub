# O_CLOEXEC, FD Inheritance, Exec-Time Leaks

> 한 줄 요약: `execve()`는 주소 공간은 바꾸지만 file descriptor는 기본적으로 유지하므로, `O_CLOEXEC` 습관이 없으면 소켓, 파이프, 임시 파일이 자식 프로세스로 새어 나가기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - [Fork, Exec, Copy-on-Write Behavior](./fork-exec-copy-on-write-behavior.md)
> - [file descriptor, socket, syscall cost](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
> - [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
> - [PIDFD Basics, Race-Free Process Handles](./pidfd-basics-race-free-process-handles.md)
> - [signals, process supervision](./signals-process-supervision.md)
> - [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)

> retrieval-anchor-keywords: O_CLOEXEC, FD_CLOEXEC, close-on-exec, execve descriptor inheritance, leaked socket, leaked pipe, accept4 SOCK_CLOEXEC, pipe2 O_CLOEXEC, dup3 O_CLOEXEC, fork exec race

## 핵심 개념

`fork()` 이후 자식은 부모의 file descriptor table을 이어받고, `execve()` 이후에도 close-on-exec가 설정되지 않은 descriptor는 그대로 남는다. 이 기본 동작을 잊으면 서브프로세스가 의도치 않게 listener, DB socket, pipe, temp file을 계속 쥐고 있게 된다.

- `FD_CLOEXEC`: exec 시 닫히도록 만드는 descriptor flag다
- `O_CLOEXEC`: `open()` 계열에서 생성 시점부터 close-on-exec를 켜는 방식이다
- `SOCK_CLOEXEC`: `socket()`/`accept4()` 계열에서 같은 목적을 가진다
- `pipe2(..., O_CLOEXEC)`, `dup3(..., O_CLOEXEC)`: 파이프와 dup에도 생성 시점 설정을 붙일 수 있다

왜 중요한가:

- listener가 새어 나가면 graceful restart나 port release가 꼬일 수 있다
- pipe의 반대편 fd가 남아 EOF가 안 와서 worker가 영원히 기다릴 수 있다
- privileged file descriptor가 의도치 않은 helper process로 넘어가 보안 경계가 흐려질 수 있다

## 깊이 들어가기

### 1. exec는 메모리를 갈아끼우지만 descriptor는 남길 수 있다

많이 헷갈리는 부분은 이것이다.

- `execve()`는 코드와 주소 공간은 새 프로그램으로 교체한다
- 하지만 close-on-exec가 아닌 file descriptor는 새 이미지에서도 열린 채 남는다
- 그래서 "새 프로세스니까 깨끗하겠지"라는 가정이 자주 틀린다

특히 supervisor, shell-out, helper worker를 자주 띄우는 백엔드에서는 이 차이가 운영 버그로 바로 이어진다.

### 2. 생성 후 `fcntl()`보다 생성 시점 `*_CLOEXEC`가 더 안전하다

멀티스레드 프로그램에서는 `open()` 후 `fcntl(F_SETFD, FD_CLOEXEC)`를 따로 호출하는 방식이 race를 만들 수 있다.

- 한 스레드가 fd를 열었다
- 다른 스레드가 그 사이 `fork()` + `execve()`를 했다
- 아직 `FD_CLOEXEC`가 안 붙은 fd가 자식으로 새어 나간다

그래서 가능하면 `O_CLOEXEC`, `SOCK_CLOEXEC`, `pipe2`, `dup3`처럼 생성 시점에 바로 설정하는 편이 안전하다.

### 3. leak는 "사용하지 않는 fd"가 아니라 "수명 관리가 깨진 fd"다

descriptor leak는 단순히 개수가 늘어나는 문제만이 아니다.

- listener가 살아 있어 port close가 안 된다
- write end가 남아 있어 pipe reader가 EOF를 못 받는다
- temp file이나 mount가 busy 상태로 남는다
- connection pool socket이 helper process에 남아 장애 분석을 헷갈리게 만든다

즉 leak는 자원 누수이면서 동시에 lifecycle bug다.

### 4. 예외는 있다. 다만 의도적으로 남겨야 한다

descriptor 상속이 항상 나쁜 것은 아니다.

- socket activation
- supervisor가 child에 특정 fd를 넘기는 구조
- zero-downtime restart에서 listener handoff

하지만 이런 경우도 "기본값은 close-on-exec, 예외만 명시적으로 상속"이 운영상 훨씬 안전하다.

## 실전 시나리오

### 시나리오 1: 부모를 내렸는데도 포트가 계속 잡혀 있다

가능한 원인:

- helper process가 listener를 상속했다
- `execve()` 이후에도 close-on-exec가 꺼져 있었다
- zero-downtime restart 설계와 우발적 leak가 섞여 있다

진단:

```bash
lsof -iTCP -sTCP:LISTEN -nP
ls -l /proc/<pid>/fd
strace -ff -ttT -e trace=open,openat,accept,accept4,dup,dup2,dup3,fcntl,execve <cmd>
```

### 시나리오 2: subprocess가 끝났는데 pipe reader가 EOF를 못 받는다

가능한 원인:

- 부모나 sibling process가 write end를 여전히 들고 있다
- `pipe()` 뒤 close 정리가 빠졌다
- `pipe2(O_CLOEXEC)` 대신 수동 정리를 믿었다

대응 감각:

- 사용하지 않는 pipe end는 즉시 닫는다
- 파이프 생성은 가능하면 `pipe2(O_CLOEXEC)`를 쓴다
- shell wrapper를 여러 겹 두는 구조라면 inheritance chain을 확인한다

### 시나리오 3: 의도치 않은 자식 프로세스가 privileged fd를 물고 있다

가능한 원인:

- temp credential file, unix domain socket, admin listener가 상속됐다
- shell-out 경로가 많아 추적이 어렵다
- exec 전에 fd hygiene가 표준화되어 있지 않다

이 경우는 성능 문제가 아니라 보안/운영 경계 문제로 봐야 한다.

## 코드로 보기

### 생성 시점 close-on-exec

```c
int fd = open(path, O_RDONLY | O_CLOEXEC);
int p[2];
pipe2(p, O_CLOEXEC);
int client = accept4(listener, NULL, NULL, SOCK_CLOEXEC);
```

### dup가 필요할 때

```c
int newfd = dup3(oldfd, targetfd, O_CLOEXEC);
```

### mental model

```text
fork()
  -> child inherits descriptors
execve()
  -> address space replaced
  -> descriptors stay open unless FD_CLOEXEC is set
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 기본값 `*_CLOEXEC` | leak 가능성을 크게 줄인다 | 의도적 상속 경로는 별도 처리 필요 | 일반 서버/라이브러리 코드 |
| 수동 `fcntl(FD_CLOEXEC)` | 구식 API와 맞출 수 있다 | 멀티스레드 race를 만들 수 있다 | 불가피한 레거시 경로 |
| 명시적 fd 상속 | 재시작/소켓 handoff가 가능하다 | 설계와 문서화가 필요하다 | supervisor, socket activation |
| 무계획 상속 | 구현이 쉬워 보인다 | 장애와 보안 리스크가 커진다 | 피해야 한다 |

## 꼬리질문

> Q: `execve()`를 하면 file descriptor도 다 닫히나요?
> 핵심: 아니다. close-on-exec가 켜진 descriptor만 닫히고, 나머지는 새 프로그램에도 남는다.

> Q: 왜 `open()` 다음 `fcntl()`보다 `O_CLOEXEC`가 더 낫나요?
> 핵심: 멀티스레드 환경에서는 두 호출 사이에 `fork()+exec()`가 끼어들며 leak race가 생길 수 있기 때문이다.

> Q: descriptor 상속은 언제 의도적으로 쓰나요?
> 핵심: socket activation이나 listener handoff처럼 자식에게 일부 fd를 의식적으로 넘길 때다.

## 한 줄 정리

`execve()` 경로의 안정성은 "무엇을 열었는가"보다 "무엇을 닫지 않고 다음 프로세스로 넘겼는가"를 관리하는 데서 갈린다.
