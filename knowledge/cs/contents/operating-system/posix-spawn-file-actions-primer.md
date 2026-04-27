# posix_spawn File Actions Primer

> 한 줄 요약: `posix_spawn_file_actions_*()`는 "`exec()` 직전 child가 할 `dup2()` / `close()` / `open()` 체크리스트를 미리 적어 둔 것"이라고 생각하면 stdout/stderr redirect를 거의 같은 mental model로 읽을 수 있다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)와 [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md) 다음에 읽는 beginner bridge다. `dup2()` 기반 redirect는 어렴풋이 아는데 `posix_spawn_file_actions_adddup2()` / `addopen()` / `addclose()`가 추상적으로 느껴질 때, "child 쪽에서 무슨 일이 일어나는가"를 같은 그림으로 다시 고정해 준다.

**난이도: 🟢 Beginner**

관련 문서:

- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
- [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: posix_spawn file actions basics, posix_spawn redirect basics, posix_spawn stdin redirect, posix_spawn stdout redirect, posix_spawn stderr redirect, posix_spawn dup2 mental model, posix_spawn_file_actions_adddup2, posix_spawn_file_actions_addopen, posix_spawn_file_actions_addclose, posix_spawn pipe redirection, posix_spawn cloexec basics, spawn file actions beginner, posix_spawn file actions self-check, beginner handoff box, primer handoff box

## 먼저 잡는 멘탈 모델

가장 먼저 잡아 둘 mental model은 이것이다.

```text
fork() + exec() 경로
  -> child가 직접 dup2(), close(), open() 호출
  -> exec()

posix_spawn() 경로
  -> parent가 "child가 곧 할 일"을 file actions에 적어 둠
  -> spawn 시 child 쪽에 그 순서대로 적용
  -> target program 시작
```

즉 `posix_spawn_file_actions_t`는 "지금 parent가 실행하는 코드"가 아니라,
**"새 child가 프로그램을 시작하기 직전에 처리할 fd 작업 목록"** 이다.

초보자에게는 이 문장이 제일 중요하다.

> `posix_spawn_file_actions_adddup2(&fa, a, b)`는 "`dup2(a, b)`를 child 시작 직전에 해 둬"라고 메모하는 것에 가깝다.

이 감각만 고정되면 이름이 길어도 겁먹을 필요가 없다.

- `adddup2`는 child 쪽 `dup2()` 메모다
- `addclose`는 child 쪽 `close()` 메모다
- `addopen`은 child 쪽 "`open()`해서 이 fd 번호에 붙여 둬"라는 메모다

## `dup2()` mental model로 바로 번역하기

`fork()` 뒤 child에서 직접 정리하는 코드를 안다고 가정하면, `posix_spawn_file_actions_*()`는 거의 1:1로 번역된다.

| child 쪽에서 직접 쓴다면 | file actions로 적는다면 | beginner용 해석 |
|---|---|---|
| `dup2(pipe_in[0], STDIN_FILENO);` | `posix_spawn_file_actions_adddup2(&fa, pipe_in[0], STDIN_FILENO);` | child stdin을 `pipe_in[0]`으로 바꾼다 |
| `dup2(pipe_out[1], STDOUT_FILENO);` | `posix_spawn_file_actions_adddup2(&fa, pipe_out[1], STDOUT_FILENO);` | child stdout을 파이프 write end로 보낸다 |
| `dup2(pipe_out[1], STDERR_FILENO);` | `posix_spawn_file_actions_adddup2(&fa, pipe_out[1], STDERR_FILENO);` | child stderr도 같은 대상으로 보낸다 |
| `close(pipe_in[1]);` | `posix_spawn_file_actions_addclose(&fa, pipe_in[1]);` | child에 필요 없는 반대쪽 pipe end를 닫는다 |
| `open("err.log", ...); dup2(logfd, STDERR_FILENO);` | `posix_spawn_file_actions_addopen(&fa, STDERR_FILENO, "err.log", ...);` | child의 fd `2`를 파일로 열어 둔다 |

여기서 `addopen`이 처음엔 가장 낯설다.
하지만 beginner mental model은 단순하게 잡아도 된다.

- `addopen(..., STDERR_FILENO, "err.log", ...)`
- 즉 "child가 시작될 때 fd `2`가 `err.log`를 보게 만들어 둔다"

parent가 미리 log fd를 `open()`해서 들고 있어야 한다는 뜻이 아니다.

## 가장 흔한 redirection 패턴

처음에는 "stdio 세 개를 어디에 연결할까"만 보면 충분하다.

| 하고 싶은 일 | file actions 패턴 | 기억할 포인트 |
|---|---|---|
| child stdin을 pipe read end에 연결 | `adddup2(pipe_in[0], STDIN_FILENO)` | parent는 보통 `pipe_in[1]`로 child에게 입력을 쓴다 |
| child stdout을 pipe write end에 연결 | `adddup2(pipe_out[1], STDOUT_FILENO)` | parent는 `pipe_out[0]`에서 child 출력을 읽는다 |
| child stderr를 파일로 보냄 | `addopen(STDERR_FILENO, "err.log", O_WRONLY | O_CREAT | O_TRUNC, 0644)` | stderr 전용 파일이면 `addopen`이 가장 직관적이다 |
| stdout과 stderr를 같은 pipe/file로 모음 | 먼저 stdout을 붙이고, 그 다음 stderr를 같은 대상으로 `adddup2` | file actions는 **추가한 순서대로** 적용된다고 생각하면 덜 헷갈린다 |
| child에 필요 없는 fd를 닫음 | `addclose(unused_fd)` | child 쪽 정리다. parent 자신의 `close()`까지 대신해 주지는 않는다 |

특히 마지막 두 줄이 자주 헷갈린다.

- file actions는 **추가한 순서대로 적용된다**
- 그래서 "`stdout`을 먼저 만들고 `stderr`를 그 stdout에 붙인다" 같은 순서도 그대로 표현할 수 있다

## 코드로 보는 작은 예제

아래 예제는 `sort`를 띄우면서 child의 stdin/stdout만 pipe로 연결하는 가장 흔한 형태다.

```c
int in_pipe[2];
int out_pipe[2];
pipe2(in_pipe, O_CLOEXEC);
pipe2(out_pipe, O_CLOEXEC);

posix_spawn_file_actions_t actions;
posix_spawn_file_actions_init(&actions);

posix_spawn_file_actions_adddup2(&actions, in_pipe[0], STDIN_FILENO);
posix_spawn_file_actions_adddup2(&actions, out_pipe[1], STDOUT_FILENO);

posix_spawn_file_actions_addclose(&actions, in_pipe[1]);
posix_spawn_file_actions_addclose(&actions, out_pipe[0]);

/* dup2 뒤에는 원래 번호를 닫아도 STDIN/STDOUT은 남는다. */
posix_spawn_file_actions_addclose(&actions, in_pipe[0]);
posix_spawn_file_actions_addclose(&actions, out_pipe[1]);

char *argv[] = {"sort", NULL};
pid_t pid;
posix_spawnp(&pid, "sort", &actions, NULL, argv, environ);

posix_spawn_file_actions_destroy(&actions);

close(in_pipe[0]);   /* parent는 child stdin read end를 안 씀 */
close(out_pipe[1]);  /* parent는 child stdout write end를 안 씀 */
```

이 코드에서 꼭 읽어야 할 흐름은 이것이다.

1. parent는 `pipe2(O_CLOEXEC)`로 안전한 fd를 만든다.
2. file actions에 "`child stdin/stdout을 어디에 붙일지`"를 적는다.
3. 필요한 `dup2` 메모를 넣은 뒤에는 child가 더 이상 필요 없는 원래 번호를 `addclose`로 닫는다.
4. spawn이 끝나면 parent도 자기 쪽에서 안 쓰는 끝을 `close()`한다.

즉 `fork()` + `dup2()` 예제와 다르게 보이는 부분은 "실행 시점"뿐이고,
fd를 남기고 닫는 규칙은 거의 같다.

## 자주 헷갈리는 포인트

### 1. `adddup2`를 호출했다고 parent fd가 바로 바뀌는 것은 아니다

아니다. file actions는 parent의 현재 fd table을 즉시 바꾸지 않는다.

- parent stdout이 갑자기 파이프로 바뀌지 않는다
- spawn이 일어날 때 child 쪽에만 적용된다
- 그래서 "왜 지금 출력 방향이 안 바뀌지?"라는 혼란이 생길 수 있다

### 2. `addclose`는 child 쪽 정리이고, parent `close()`를 대신하지 않는다

이것도 흔한 실수다.

- `posix_spawn_file_actions_addclose(&fa, out_pipe[1])`
- 이건 "child 안에서는 그 번호를 닫아 둬"라는 뜻이다
- parent가 계속 `out_pipe[1]`을 들고 있으면 EOF 문제는 여전히 생길 수 있다

즉 spawn 뒤 parent 정리는 parent가 직접 해야 한다.

### 3. `addopen`은 "parent가 미리 열어 둔 fd를 넘긴다"와 다르다

둘은 다르다.

- parent가 이미 연 fd를 child의 `1`이나 `2`로 붙이고 싶으면 `adddup2`
- child가 시작될 때 특정 경로를 바로 `1`이나 `2`로 열고 싶으면 `addopen`

그래서 "`stderr`를 파일 하나로 보낸다" 같은 경우는 `addopen`이 더 짧고 자연스러울 때가 많다.

### 4. `CLOEXEC` 기본값은 여전히 중요하다

`posix_spawn()`을 쓴다고 해서 fd hygiene가 자동으로 해결되는 것은 아니다.

- parent가 만든 pipe/socket/temp fd는 여전히 생성 시점 `O_CLOEXEC`가 안전하다
- file actions는 "예외적으로 child에 남길 fd"를 적는 곳에 가깝다
- `posix_spawn()`으로 바꿔도 leaked fd, pipe EOF 문제의 기본 원칙은 그대로다

반대로 "redirect는 이해했는데 process group, signal mask, signal default는 왜 따로 있지?"가 남는다면 [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)로 이어서 가는 편이 좋다. `file actions`와 `attrs`가 서로 다른 문제를 푼다는 점을 beginner 관점에서 분리해 준다.

## Self-check (자가 점검 4문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. `posix_spawn_file_actions_*()`를 "`exec()` 직전 child가 할 `dup2()`/`close()`/`open()` 메모"로 번역해 설명할 수 있는가?
   힌트: parent가 지금 바로 fd를 바꾸는 API가 아니라, child 시작 직전에 적용할 작업 목록을 적어 두는 개념이다.
2. `adddup2`/`addclose`가 parent fd table을 즉시 바꾸지 않는다는 점(적용 시점은 spawn 시점)을 말할 수 있는가?
   힌트: setter 호출 시점엔 "예약"만 되고 실제 fd 배선은 child 생성 시점에 한 번에 실행된다.
3. child 쪽 `addclose`와 parent 쪽 `close()`가 서로 대체 관계가 아니라는 점을 이해하고 EOF 누락 시 parent fd를 의심할 수 있는가?
   힌트: child 안에서 닫는 일과 parent가 자기 복사본을 닫는 일은 별개라 EOF는 parent 쪽 누락 때문에 자주 막힌다.
4. `addopen`과 "parent가 미리 연 fd를 넘기는 방식(`adddup2`)"의 차이를 상황별로 고를 수 있는가?
   힌트: child가 직접 파일을 열게 할지, parent가 준비한 fd를 넘길지는 권한·에러 처리·재사용 필요에 따라 달라진다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`file actions` 다음에 `attrs`는 왜 또 따로 있지?"가 남으면: [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
> - "`posix_spawn()` 말고 `fork()`/`exec()`/`clone()`은 어디가 다른가?"를 비교하려면: [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
> - "`execve()` 뒤 fd leak은 왜 계속 신경 써야 하지?"를 더 파려면: [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
> - 운영체제 입문 primer 묶음으로 돌아가려면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

`posix_spawn_file_actions_*()`를 "`fork()` 뒤 child가 하던 `dup2()` / `close()` / `open()`를 미리 적어 두는 체크리스트"로 읽으면 `posix_spawn()` redirection도 낯선 새 개념보다 익숙한 fd 정리 패턴으로 보인다.
