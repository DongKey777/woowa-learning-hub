# popen and Runtime Wrapper Mapping

> 한 줄 요약: `popen()`이나 Python `subprocess.Popen()` 같은 런타임 wrapper는 새로운 OS 개념이 아니라, pipe를 만들고 child의 `stdin/stdout/stderr` fd에 붙인 뒤 어떤 fd를 상속할지 정하는 작업을 옵션 이름으로 감싼 것이다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) 다음에 읽는 beginner bridge다. `popen()`, `stdin=PIPE`, `stdout=PIPE`, `close_fds`, `pass_fds` 같은 API 옵션을 OS-level `pipe`, `dup2()`, `close()`, `CLOEXEC`, `posix_spawn file actions` mental model로 다시 매핑한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
- [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: popen runtime wrapper mapping, popen mental model, popen pipe fd mapping, popen stdout pipe, popen stdin pipe, language subprocess options, subprocess PIPE mapping, Python subprocess close_fds, close_fds pass_fds mental model, pass_fds fd inheritance, child fd inheritance wrapper, shell true fd inheritance, runtime wrapper file actions, high-level subprocess OS mental model, popen 처음 배우는데, close_fds 뭐예요, pass_fds 뭐예요

## 핵심 개념

먼저 용어보다 그림을 잡자.

```text
runtime wrapper option
  -> pipe/file/devnull 같은 fd를 준비
  -> child가 시작되기 직전에 fd 0/1/2를 원하는 곳으로 연결
  -> child에 남길 fd만 명시
  -> target program exec
```

`popen()`, Python `subprocess.Popen()`, Java `ProcessBuilder`, Node `child_process.spawn()`은 모양이 다르지만 beginner mental model은 같다.

> wrapper 옵션은 "child fd table을 어떻게 만들까"를 더 읽기 쉬운 이름으로 표현한 것이다.

즉 `stdout=PIPE`는 "마법의 문자열 버퍼"가 아니다. OS pipe를 만들고, child의 fd `1`을 pipe write end로 향하게 만드는 요청이다.

## `popen()`은 pipe 하나를 붙인 subprocess다

`popen()`을 처음 볼 때는 "프로세스 실행 + pipe 한쪽을 FILE처럼 돌려줌"으로 읽으면 된다.

| 호출 모양 | parent가 받는 것 | child 쪽 연결 | OS-level 그림 |
|---|---|---|---|
| `popen(cmd, "r")` | parent가 읽을 수 있는 `FILE *` | child `stdout`이 pipe write end로 감 | `pipe()` + child fd `1` redirect |
| `popen(cmd, "w")` | parent가 쓸 수 있는 `FILE *` | child `stdin`이 pipe read end에서 옴 | `pipe()` + child fd `0` redirect |

그래서 `popen(cmd, "r")`의 흐름은 대략 이렇게 보인다.

```text
parent
  -> pipe 생성
  -> child 생성
child
  -> dup2(pipe_write_end, STDOUT_FILENO)
  -> exec command
parent
  -> pipe_write_end를 닫음
  -> pipe_read_end를 FILE *로 감싸서 읽음
```

중요한 점:

- `popen()`은 보통 command string을 shell로 실행한다
- parent가 받는 `FILE *`에는 parent 쪽 stdio buffering도 있을 수 있다
- stdout과 stderr를 따로 세밀하게 다루려면 `popen()`보다 풍부한 subprocess API가 필요하다

shell quoting, command injection, process group 같은 주제는 중요하지만 이 문서의 중심은 아니다. 여기서는 "pipe와 fd 연결을 wrapper가 대신 적어 준다"는 감각만 고정한다.

## wrapper 옵션을 OS 작업으로 번역하기

언어별 이름은 다르지만 대부분 아래 표로 해석할 수 있다.

| wrapper 옵션 | OS-level mental model | 초보자가 기억할 말 |
|---|---|---|
| `stdin=PIPE` | parent -> child 방향 pipe를 만들고 child fd `0`에 read end를 붙인다 | parent가 child에게 입력을 쓴다 |
| `stdout=PIPE` | child -> parent 방향 pipe를 만들고 child fd `1`에 write end를 붙인다 | parent가 child 출력을 읽는다 |
| `stderr=PIPE` | 별도 pipe를 만들고 child fd `2`에 write end를 붙인다 | stderr를 stdout과 따로 읽는다 |
| `stderr=STDOUT` | child fd `2`를 fd `1`과 같은 대상으로 붙인다 | 에러도 stdout 쪽으로 합친다 |
| `stdout=file` | child fd `1`을 파일 fd로 `dup2()`하거나 spawn file action으로 연다 | child 출력이 파일로 간다 |
| `DEVNULL` | `/dev/null`을 열어 child fd `0/1/2` 중 하나에 붙인다 | 입력은 빈값처럼, 출력은 버림처럼 다룬다 |
| `close_fds=True` | child에 의도하지 않은 fd를 남기지 않는다 | 기본값은 "닫고, 예외만 남긴다" |
| `close_fds=False` | close-on-exec가 꺼진 fd가 child까지 남을 수 있다 | 편해 보이지만 leak 위험이 커진다 |
| `pass_fds=(fd,)` | `0/1/2` 외에 특정 fd를 명시적으로 child에 남긴다 | fd handoff다. 데이터 복사가 아니다 |
| `shell=True` | target program 앞에 shell process가 한 겹 생긴다 | fd 정책은 shell에도 먼저 적용된다 |

핵심은 `PIPE` 계열과 fd 상속 옵션을 섞지 않는 것이다.

- `stdin/stdout/stderr=PIPE`: 통신 channel을 새로 만드는 옵션
- `close_fds/pass_fds`: 어떤 기존 fd가 child에 살아남을지 정하는 옵션

둘 다 fd table을 다루지만 질문이 다르다.

## Python 예제를 OS 그림으로 읽기

아래 코드를 보자.

```python
p = subprocess.Popen(
    ["sort"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    close_fds=True,
)
```

OS-level로는 이렇게 번역하면 된다.

```text
parent
  -> stdin용 pipe 생성
  -> stdout용 pipe 생성
  -> stderr용 pipe 생성
child 시작 직전
  -> dup2(stdin_pipe_read, 0)
  -> dup2(stdout_pipe_write, 1)
  -> dup2(stderr_pipe_write, 2)
  -> 그 외 fd는 닫거나 exec 때 닫히도록 정리
  -> exec "sort"
parent
  -> child가 쓰는 pipe end를 닫음
  -> 남은 pipe end를 Python file object로 감싸서 p.stdin/p.stdout/p.stderr로 노출
```

Python 객체가 먼저 보이지만 실제 boundary는 OS fd다.

- `p.stdin.write(...)`는 parent가 pipe write end에 쓰는 것이다
- `p.stdout.read(...)`는 parent가 pipe read end에서 읽는 것이다
- child는 Python 객체를 보는 것이 아니라 fd `0/1/2`를 본다

## `close_fds`와 `pass_fds`를 같이 읽기

초보자에게 가장 안전한 기본값은 이것이다.

```text
child에는 stdin/stdout/stderr와 명시한 fd만 남긴다
```

이 감각을 옵션으로 쓰면 보통 이렇게 된다.

```python
subprocess.Popen(
    ["worker"],
    pass_fds=(control_fd,),
    close_fds=True,
)
```

이 예제의 뜻:

- `control_fd`는 child가 꼭 받아야 하는 기존 fd다
- 그래서 `pass_fds`로 예외를 만든다
- 그 외 listener, temp file, admin socket은 child로 새지 않게 막는다

`pass_fds`는 데이터를 복사해 주는 옵션이 아니다. child도 같은 열린 파일, socket, pipe endpoint를 가리키는 fd를 받는 것이다. 그래서 offset, socket state, pipe EOF 같은 lifecycle 감각이 같이 따라온다.

## `popen()`과 runtime wrapper가 숨기는 것

wrapper는 편하지만 아래 네 가지를 없애지는 않는다.

| 숨겨진 작업 | 왜 계속 중요하나 |
|---|---|
| pipe 생성 | pipe write end가 남아 있으면 EOF가 안 온다 |
| child fd 재배치 | fd `0/1/2`가 어디를 향하는지가 child I/O를 결정한다 |
| close policy | 의도하지 않은 fd가 child나 shell helper로 새면 lifecycle bug가 된다 |
| buffering | fd 연결이 맞아도 child runtime이 flush하지 않으면 출력이 늦게 보인다 |

즉 wrapper를 쓴다고 `close()`, `CLOEXEC`, `dup2()` mental model이 사라지는 것은 아니다. 단지 직접 호출하지 않을 뿐이다.

## 자주 헷갈리는 포인트

### 1. `PIPE`는 언어 런타임 안의 큐인가요?

아니다. 보통 OS pipe fd를 런타임 객체로 감싼 것이다. parent는 객체 메서드를 호출하지만 kernel 입장에서는 pipe read/write다.

### 2. `close_fds=True`면 parent의 fd도 닫히나요?

아니다. child에게 무엇을 상속하지 않을지 정하는 옵션이다. parent가 들고 있는 fd lifecycle은 parent가 계속 관리한다.

### 3. `pass_fds`는 stdout capture와 같은 건가요?

아니다. stdout capture는 새 pipe를 만들어 child fd `1`에 붙이는 일이다. `pass_fds`는 이미 존재하는 fd를 child에게 의도적으로 남기는 일이다.

### 4. `shell=True`면 fd 문제가 단순해지나요?

보통 반대다. shell process가 한 겹 더 생기므로 fd가 shell에도 먼저 보일 수 있다. 기본 close policy를 더 명확히 해야 한다.

### 5. 출력이 늦게 보이면 `close_fds` 문제인가요?

항상 그렇지는 않다. EOF가 안 오면 fd leak나 pipe end close를 먼저 보고, 줄 단위 출력이 늦게 보이면 [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)의 stdio buffering을 따로 본다.

## 이 문서 다음에 보면 좋은 문서

- child에 남길 fd와 닫을 fd의 기본 규칙을 더 잡으려면 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- `posix_spawn()`이 `dup2()` / `close()`를 file actions로 표현하는 방식을 보려면 [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
- fd 연결은 맞는데 child 출력이 늦게 보이면 [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- `exec()` 경계에서 fd leak가 왜 생기는지 더 깊게 보려면 [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)

## 한 줄 정리

`popen()`과 language-level subprocess option은 "pipe를 만들고, child fd table을 원하는 모양으로 만들고, 상속할 fd만 남긴다"는 OS 작업을 더 편한 API 이름으로 적는 방식이다.
