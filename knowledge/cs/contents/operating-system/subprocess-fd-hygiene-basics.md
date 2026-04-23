# Subprocess FD Hygiene Basics

> 한 줄 요약: subprocess I/O에서 가장 안전한 기본값은 "pipe/socket은 생성 시점부터 `CLOEXEC`, child는 `dup2()`로 `0/1/2`만 남기고, parent/child 모두 안 쓰는 pipe end를 즉시 닫기"다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md) 다음에 읽는 beginner bridge다. `fork()` / `exec()`는 알겠는데 stdout/stderr redirect, pipe EOF, leaked fd across exec가 자꾸 섞일 때 기본 규칙부터 고정한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
- [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
- [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- [signals, process supervision](./signals-process-supervision.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)

retrieval-anchor-keywords: subprocess fd hygiene basics, subprocess pipe redirection, subprocess stdout redirect, subprocess stdin redirect, pipe redirection basics, dup2 redirect basics, close-on-exec basics, exec fd leak, leaked pipe eof, pipe2 o_cloexec, dup2 stdin stdout stderr, close_fds mental model, fd hygiene 처음 배우는데, 서브프로세스 뭐예요

## 핵심 개념

subprocess를 띄울 때 가장 많이 섞이는 질문은 이것이다.

- child에 **무엇이 의도적으로 남아야 하는가**
- `execve()` 경계에서 **무엇이 사라져야 하는가**

여기서 감각이 흔들리면 stdout/stderr redirect, pipe EOF, leaked listener/socket 문제가 한 번에 헷갈린다.

- `fork()` 뒤 child는 부모의 file descriptor table을 이어받는다
- `execve()` 뒤에도 close-on-exec가 꺼진 fd는 그대로 남는다
- 그래서 stdio redirection은 "남길 fd를 `0/1/2`로 재배치"하는 작업이고, fd hygiene는 "그 외 fd를 child로 넘기지 않는 습관"이다

초보자용으로는 이 문장 하나가 핵심이다.

> **기본값은 `close-on-exec`, 예외는 `stdin/stdout/stderr` 같은 의도적 상속만 `dup2()`로 남긴다.**

## 한눈에 보는 안전한 흐름

```text
parent
  -> pipe2(..., O_CLOEXEC) 로 pipe 생성
  -> fork()
child
  -> dup2(read_end, STDIN_FILENO) / dup2(write_end, STDOUT_FILENO)
  -> 필요하면 STDERR_FILENO도 재배치
  -> 원래 pipe fd 번호들을 전부 close()
  -> execve(...)
parent
  -> child가 쓸 pipe end는 즉시 close()
  -> 남긴 쪽 fd로만 read/write
  -> waitpid()로 종료 회수
```

여기서 중요한 점은 두 가지다.

- `pipe2(O_CLOEXEC)`로 만든 원래 fd 번호는 exec 때 닫혀야 한다
- 하지만 `dup2()`로 만든 `0/1/2`는 새 프로그램의 stdio로 살아남아야 한다

즉 `CLOEXEC`는 "아무것도 상속하지 말자"가 아니라, **"우리가 명시적으로 남긴 것만 상속하자"**는 기본값이다.

## beginner-safe rules: CLOEXEC와 dup2

### 1. pipe/socket/temp fd는 생성 시점부터 `CLOEXEC`를 붙인다

가장 안전한 출발점은 "일단 안 넘긴다"다.

- `open(..., O_CLOEXEC)`
- `pipe2(..., O_CLOEXEC)`
- `socket(..., SOCK_CLOEXEC, ...)`
- `accept4(..., SOCK_CLOEXEC)`
- `dup3(..., O_CLOEXEC)`

이유:

- `open()` 후 `fcntl(FD_CLOEXEC)`를 따로 붙이면 멀티스레드 환경에서 race가 생길 수 있다
- subprocess wrapper가 늘어나도 기본값이 유지된다
- 우발적 listener/socket/pipe leak를 크게 줄인다

### 2. child에 남길 것은 `0/1/2`만 `dup2()`로 명시한다

stdio redirection의 핵심은 child가 새 프로그램으로 갈아타기 전에 fd를 `stdin/stdout/stderr` 위치로 옮기는 것이다.

```c
dup2(stdin_pipe[0], STDIN_FILENO);
dup2(stdout_pipe[1], STDOUT_FILENO);
dup2(stderr_pipe[1], STDERR_FILENO);
```

이 패턴이 safe한 이유:

- 원래 pipe fd는 `CLOEXEC`라서 backup safety net이 된다
- `dup2()` 대상인 `0/1/2`는 새 프로그램이 실제로 써야 하는 stdio다
- 그래서 "무엇을 inherit할지"가 코드에 명시적으로 드러난다

## beginner-safe rules: close와 기본값

### 3. `dup2()`가 끝나면 parent/child 모두 원래 pipe end를 바로 닫는다

`dup2()`는 새 번호를 만들 뿐, 원래 fd를 자동으로 없애지 않는다.

그래서 child에서는:

- `dup2()` 뒤 원래 `stdin_pipe[0]`, `stdout_pipe[1]` 같은 번호를 닫는다
- 쓰지 않는 반대편 end도 함께 닫는다

parent에서는:

- child가 쓸 end를 즉시 닫는다
- 예를 들어 child stdout을 읽는 parent라면 parent의 `stdout_pipe[1]`은 필요 없다

이 규칙을 어기면 가장 흔한 증상이 나온다.

- reader가 EOF를 영원히 못 본다
- helper process가 listener를 계속 잡고 있다
- "분명 child는 끝났는데 왜 pipe가 안 닫히지?" 같은 증상이 생긴다

### 4. `CLOEXEC`는 safety net이고, explicit `close()`는 lifecycle 정리다

초보자가 자주 하는 오해는 "`CLOEXEC`만 붙였으니 close는 대충 해도 된다"는 생각이다. 하지만 둘의 역할은 다르다.

- `CLOEXEC`: exec 경계를 넘는 우발적 상속 방지
- `close()`: 지금 이 프로세스 안에서 더 이상 쓰지 않는 끝을 정리

즉 pipe EOF와 backpressure는 `close()`가 맞추고, exec leak는 `CLOEXEC`가 막는다. 둘 중 하나만으로는 hygiene가 완성되지 않는다.

### 5. 기본값은 "close all, explicit inherit only"로 둔다

언어 런타임이나 subprocess helper를 쓸 때도 mental model은 같다.

- 기본 close policy를 끄지 않는다
- 꼭 넘길 fd만 지정한다
- wrapper가 여러 겹이어도 "무엇이 child에 살아남는가"를 추적할 수 있게 만든다

`close_fds=true` 같은 기본값이 있다면 보통 유지하는 편이 안전하다. 의도적 handoff가 필요할 때만 예외를 문서화한다.

## 코드로 보기

### child stdin/stdout redirect의 안전한 기본형

```c
int to_child[2];
int from_child[2];

pipe2(to_child, O_CLOEXEC);
pipe2(from_child, O_CLOEXEC);

pid_t pid = fork();
if (pid == 0) {
    if (dup2(to_child[0], STDIN_FILENO) == -1) _exit(127);
    if (dup2(from_child[1], STDOUT_FILENO) == -1) _exit(127);

    close(to_child[0]);
    close(to_child[1]);
    close(from_child[0]);
    close(from_child[1]);

    execl("/usr/bin/sort", "sort", (char *)NULL);
    _exit(127);
}

close(to_child[0]);    /* parent는 child stdin read end를 쓰지 않음 */
close(from_child[1]);  /* parent는 child stdout write end를 쓰지 않음 */
```

이 예제에서 기억할 점:

- `pipe2(O_CLOEXEC)`로 만든 원래 fd는 우발적 exec leak를 막는다
- `dup2(..., STDIN_FILENO/STDOUT_FILENO)`는 의도적 stdio 상속이다
- parent가 `from_child[1]`을 닫지 않으면 child가 종료해도 EOF가 늦게 오거나 안 올 수 있다

### 자주 헷갈리는 포인트: `CLOEXEC`인데 왜 stdout은 살아남나?

```text
pipe2(..., O_CLOEXEC)
  -> 원래 pipe fd 번호는 exec 시 닫힘

dup2(pipe_write_end, STDOUT_FILENO)
  -> STDOUT_FILENO(1)는 새 프로그램의 표준 출력으로 남아야 함
  -> 그래서 의도한 redirection은 유지됨
```

즉 "`pipe를 CLOEXEC로 만들면 redirect가 깨진다"는 걱정은 보통 잘못된 mental model이다.

## 실전 시나리오

### 시나리오 1: child는 끝났는데 parent read가 EOF를 못 받는다

가능한 원인:

- parent가 write end를 아직 들고 있다
- sibling/helper process가 write end를 상속했다
- `dup2()` 뒤 원래 fd를 닫지 않았다

먼저 확인할 감각:

- 누가 write end를 들고 있는지 `lsof -p <pid>`나 `/proc/<pid>/fd`로 본다
- `pipe2(O_CLOEXEC)`가 빠졌는지 본다
- parent가 child-side end를 즉시 닫았는지 본다

### 시나리오 2: 재시작했는데 포트가 계속 잡혀 있다

가능한 원인:

- helper subprocess가 listener fd를 상속했다
- `accept4(..., SOCK_CLOEXEC)` / `O_CLOEXEC` 습관이 없다
- "새 프로그램이니 fd도 깨끗하겠지"라고 잘못 가정했다

이 경우는 socket leak이면서 동시에 lifecycle bug다.

### 시나리오 3: 예상치 못한 child가 privileged fd를 쥐고 있다

가능한 원인:

- temp file, admin socket, secret-bearing fd가 exec를 넘어갔다
- 기본 close policy를 꺼 두었다
- wrapper가 여러 겹인데 pass-through fd를 문서화하지 않았다

이 경우는 단순 편의 문제가 아니라 보안 경계 문제로 봐야 한다.

## 자주 섞이는 질문

> Q: `pipe2(O_CLOEXEC)`로 만들면 child의 stdout redirect도 exec 때 닫히나요?
> 핵심: 아니다. 원래 pipe fd 번호는 닫히지만, `dup2()`로 붙인 `STDOUT_FILENO`는 새 프로그램의 stdio로 남도록 의도한 상속이다.

> Q: `CLOEXEC`만 있으면 `close()`를 안 해도 되나요?
> 핵심: 아니다. `CLOEXEC`는 exec leak 방지용이고, EOF/backpressure/lifecycle 정리는 지금 프로세스의 `close()`가 담당한다.

> Q: 왜 parent도 pipe end를 바로 닫아야 하나요?
> 핵심: parent가 write end를 쥐고 있으면 child가 끝나도 reader는 "아직 쓸 사람이 남아 있다"고 판단해 EOF를 못 본다.

> Q: high-level subprocess API에서도 같은 규칙이 적용되나요?
> 핵심: 그렇다. 이름만 다를 뿐 기본값은 "close all, explicit inherit only"가 가장 안전하다.

## 이 문서 다음에 보면 좋은 문서

- `exec()` 경계의 leak를 더 깊게 보려면 [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
- `dup()`와 shared open file description까지 같이 보려면 [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
- local IPC primitive 선택까지 넓히려면 [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- supervision / reaping 흐름을 같이 보려면 [signals, process supervision](./signals-process-supervision.md)

## 한 줄 정리

subprocess FD hygiene의 가장 안전한 기본값은 "`CLOEXEC`로 새는 길을 막고, `dup2()`로 `0/1/2`만 의도적으로 남기고, parent/child 모두 안 쓰는 pipe end를 즉시 닫는다"다.
