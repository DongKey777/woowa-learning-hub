# popen and Runtime Wrapper Mapping

> 한 줄 요약: `popen()`이나 Python `subprocess.Popen()` 같은 런타임 wrapper는 새로운 OS 개념이 아니라, pipe를 만들고 child의 `stdin/stdout/stderr` fd에 붙인 뒤 어떤 fd를 상속할지 정하는 작업을 옵션 이름으로 감싼 것이다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) 다음에 읽는 beginner bridge다. `popen()`, `stdin=PIPE`, `stdout=PIPE`, `close_fds`, `pass_fds` 같은 API 옵션을 OS-level `pipe`, `dup2()`, `close()`, `CLOEXEC`, `posix_spawn file actions` mental model로 다시 매핑한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Runtime Shell Option Matrix](./runtime-shell-option-matrix.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
- [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)
- [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)
- [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)
- [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
- [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: popen runtime wrapper mapping, popen pipe fd mapping, subprocess pipe mapping, communicate drain wait policy, capture_output mental model, stderr stdout merge, close_fds pass_fds mental model, pass_fds fd inheritance, shell true fd inheritance, child waits for stdin eof, flush is not eof, runtime wrapper file actions, high-level subprocess os mental model, popen 처음 배우는데, close_fds 뭐예요

## Subprocess Primer Handoff

> **이 문서는 subprocess 입문 흐름의 4단계다**
>
> - 바로 앞 문서: [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)에서 양방향 pipe ordering을 먼저 잡는다
> - 지금 문서의 질문: "`PIPE`, `close_fds`, `pass_fds`, `shell=True`가 OS 그림으로는 각각 뭘 뜻하지?"
> - 다음 문서: [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)에서 shell이 한 겹 끼는 순간 parser/process/fd 경계가 어떻게 늘어나는지 잇는다

## 먼저 잡는 멘탈 모델

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
`shell=True`가 만드는 extra parser/process boundary를 따로 떼어 보고 싶다면 [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)를 바로 이어서 보면 된다.

## wrapper 옵션을 OS 작업으로 번역하기

언어별 이름은 다르지만 대부분 아래 표로 해석할 수 있다.

| wrapper 옵션 | OS-level mental model | 초보자가 기억할 말 |
|---|---|---|
| `stdin=PIPE` | parent -> child 방향 pipe를 만들고 child fd `0`에 read end를 붙인다 | parent가 child에게 입력을 쓴다 |
| `stdout=PIPE` | child -> parent 방향 pipe를 만들고 child fd `1`에 write end를 붙인다 | parent가 child 출력을 읽는다 |
| `stderr=PIPE` | 별도 pipe를 만들고 child fd `2`에 write end를 붙인다 | stderr를 stdout과 따로 읽는다 |
| `capture_output=True` | `stdout=PIPE`, `stderr=PIPE`를 한 번에 켠 shorthand다 | 결과를 모아 받되 둘 다 drain 책임이 생긴다 |
| `stderr=STDOUT` | child fd `2`를 fd `1`과 같은 대상으로 붙인다 | 에러도 stdout 쪽으로 합친다 |
| `stdout=file` | child fd `1`을 파일 fd로 `dup2()`하거나 spawn file action으로 연다 | child 출력이 파일로 간다 |
| `DEVNULL` | `/dev/null`을 열어 child fd `0/1/2` 중 하나에 붙인다 | 입력은 빈값처럼, 출력은 버림처럼 다룬다 |
| `close_fds=True` | child에 의도하지 않은 fd를 남기지 않는다 | 기본값은 "닫고, 예외만 남긴다" |
| `close_fds=False` | close-on-exec가 꺼진 fd가 child까지 남을 수 있다 | 편해 보이지만 leak 위험이 커진다 |
| `pass_fds=(fd,)` | `0/1/2` 외에 특정 fd를 명시적으로 child에 남긴다 | fd handoff다. 데이터 복사가 아니다 |
| `communicate()` | parent가 stdout/stderr drain, optional stdin write, `wait()`를 한 흐름으로 묶는다 | "다 쓴 뒤 읽고 마지막에 기다림" 순서를 wrapper가 대신 조율한다 |
| `shell=True` | target program 앞에 shell parser/process가 한 겹 생긴다 | fd 정책은 shell에도 먼저 적용되고 quoting 규칙도 shell 기준이 된다 |

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

그래서 `stdin=PIPE`와 `stdout=PIPE`를 동시에 줬다면 이제 남는 질문은 "parent가 언제 쓰고, 언제 읽고, 언제 닫는가"다. 그 순서가 틀리면 pipe capacity나 EOF 대기 때문에 멈출 수 있다. 전체 ordering은 [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)에서, "입력을 다 보냈는데 write end가 안 닫혀 child가 EOF를 못 보는 경우"는 [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)에서 따로 다룬다.

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

## 증상별로 wrapper 옵션 먼저 고르기

runtime wrapper 문서에 처음 들어올 때는 옵션 이름보다 "지금 무엇을 줄이려는가"로 붙는 편이 쉽다.

| 지금 보이는 증상/목표 | 먼저 떠올릴 옵션/호출 | 이 옵션이 하는 일 | 그래도 이어서 볼 문서 |
|---|---|---|---|
| `wait()`나 `run()`이 가끔 안 끝나고 stdout/stderr를 둘 다 모아야 한다 | `communicate()` | 두 pipe를 실행 중에 drain하고 마지막 wait까지 한 흐름으로 묶는다 | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) |
| "결과만 한 번에 받고 싶다"가 목표라 `capture_output=True`를 쓰려 한다 | `capture_output=True` | 사실상 `stdout=PIPE`, `stderr=PIPE` shorthand라 둘 다 pipe backpressure 규칙을 그대로 가진다 | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) |
| stderr는 따로 안 봐도 되고 실패 로그 때문에 가끔 멈추는 것만 줄이고 싶다 | `stderr=STDOUT` | stderr를 stdout 쪽으로 합쳐 한 stream만 drain하면 되게 만든다 | [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md) |
| child가 parent의 listener/socket/temp fd를 괜히 들고 가는 것 같다 | `close_fds=True` | `0/1/2`와 명시한 예외 외에는 child 상속을 막는다 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) |
| 반대로 child가 control socket 하나는 꼭 받아야 한다 | `pass_fds=(fd,)` | 닫는 기본 정책은 유지하면서 필요한 fd만 예외로 남긴다 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) |

자주 쓰는 한 줄 기억법:

- `communicate()`: 읽기와 기다리기를 같이 묶는다
- `capture_output=True`: 편한 축약형이지만 실제로는 stdout/stderr 둘 다 pipe다
- `stderr=STDOUT`: stderr를 stdout 쪽 한 줄기로 합친다
- `close_fds=True`: 기본은 닫고, 예외만 남긴다
- `pass_fds=(fd,)`: 기본은 닫되, 이 fd만 넘긴다

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

보통 반대다. shell process가 한 겹 더 생기므로 fd가 shell에도 먼저 보일 수 있다. 기본 close policy를 더 명확히 해야 한다. quoting boundary와 extra process 감각은 [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)에서 따로 분리해 볼 수 있다.

### 5. 출력이 늦게 보이면 `close_fds` 문제인가요?

항상 그렇지는 않다. EOF가 안 오면 fd leak나 pipe end close를 먼저 보고, 줄 단위 출력이 늦게 보이면 [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)의 stdio buffering을 따로 본다.

## 지금 증상으로 다음 문서 고르기

wrapper 옵션 이름은 이해했는데 실제 증상과 아직 잘 안 붙는다면 아래처럼 고르면 된다.

| 지금 막힌 질문 | 먼저 갈 문서 | 이유 |
|---|---|---|
| "`capture_output=True`나 `communicate()`를 써도 왜 결국 pipe 규칙을 알아야 하지?" | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) | 편한 API 이름이 붙어도 kernel pipe를 drain해야 한다는 사실은 그대로다 |
| "`close_fds`, `pass_fds`가 실제로 어디를 닫고 어디를 남기지?" | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) | wrapper 옵션을 "누가 어떤 fd를 계속 들고 있나" 관점으로 다시 고정한다 |
| "`stdout=PIPE`만 걸었는데 왜 child가 안 끝나지?" | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) | pipe가 작은 대기열이라 parent가 제때 안 읽으면 child `write()`가 막힐 수 있음을 보여 준다 |
| "`stdin=PIPE`와 `stdout=PIPE`를 같이 썼더니 왜 순서가 꼬이지?" | [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md) | 쓰기, 읽기, stdin close 순서가 두 방향 pipe와 EOF 대기를 어떻게 꼬이게 하는지 분리해 준다 |
| "`flush()`까지 했는데 왜 child가 입력 종료를 모른 채 기다리지?" | [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md) | `write()`/`flush()`와 `close()`가 child에 주는 신호가 다르다는 점을 분리해 준다 |
| "`shell=True`가 왜 갑자기 quoting/fd 문제를 늘리지?" | [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md) | wrapper 앞에 shell이라는 추가 경계가 하나 더 생긴다는 점을 따로 잡아 준다 |

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`close_fds` / `pass_fds`가 결국 누가 어떤 fd를 계속 들고 있느냐의 문제라는 점"을 다시 잡으려면: [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - "Python `shell=True`, Java `ProcessBuilder`, Node `exec()`/`spawn({ shell: true })`를 같은 OS 그림으로 맞추고 싶다면": [Runtime Shell Option Matrix](./runtime-shell-option-matrix.md)
> - "`stdout=PIPE`, `stderr=PIPE`인데 왜 child가 `write()`에서 멈추지?"를 먼저 풀려면: [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
> - "`stdin=PIPE`와 `stdout=PIPE`를 같이 잡으면 왜 순서가 더 중요하지?"를 이어서 보려면: [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)
> - "`flush()`는 했는데 왜 child가 EOF를 못 받아 계속 읽기 대기하지?"를 떼어 보려면: [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)
> - "`shell=True`가 extra process boundary를 어떻게 추가하지?"를 떼어 보려면: [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

`popen()`과 language-level subprocess option은 "pipe를 만들고, child fd table을 원하는 모양으로 만들고, 상속할 fd만 남긴다"는 OS 작업을 더 편한 API 이름으로 적는 방식이다.
