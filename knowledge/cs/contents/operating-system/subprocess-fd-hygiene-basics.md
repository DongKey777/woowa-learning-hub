---
schema_version: 3
title: Subprocess FD Hygiene Basics
concept_id: operating-system/subprocess-fd-hygiene-basics
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- fd-inheritance-across-exec
- pipe-close-ordering
- stdio-vs-fd-hygiene
aliases:
- subprocess fd hygiene basics
- fd inheritance across exec
- subprocess eof wait
- pipe eof after child exit
- close_fds pass_fds cloexec mental model
- cloexec 뭐예요
- dup2 redirect basics
- subprocess stdout stderr redirect
- subprocess stdin stdout mapping
- shell helper fd leak
- listener inherited across exec
- parent pipe end not closed
- pipe mapping parent child
- close-on-exec basics
- child pipe end still open
- pipe close ordering basics
symptoms:
- child는 끝난 것 같은데 parent read가 EOF를 못 받아요
- shell helper를 붙였더니 listener나 socket이 계속 살아 있어요
- close_fds, pass_fds, CLOEXEC, dup2가 한 그림으로 안 잡혀요
intents:
- definition
prerequisites:
- operating-system/process-lifecycle-and-ipc-basics
- operating-system/process-spawn-api-comparison
next_docs:
- operating-system/subprocess-pipe-backpressure-primer
- operating-system/stdio-buffering-after-redirect
- operating-system/o-cloexec-fd-inheritance-exec-leaks
- operating-system/subprocess-bidirectional-pipe-deadlock-primer
linked_paths:
- contents/operating-system/subprocess-symptom-first-branch-guide.md
- contents/operating-system/process-lifecycle-and-ipc-basics.md
- contents/operating-system/process-spawn-api-comparison.md
- contents/operating-system/popen-runtime-wrapper-mapping.md
- contents/operating-system/shell-wrapper-boundary-primer.md
- contents/operating-system/stdio-buffering-after-redirect.md
- contents/operating-system/posix-spawn-file-actions-primer.md
- contents/operating-system/posix-spawn-attributes-primer.md
- contents/operating-system/o-cloexec-fd-inheritance-exec-leaks.md
- contents/operating-system/open-file-description-dup-fork-shared-offsets.md
- contents/operating-system/pipe-socketpair-eventfd-memfd-ipc-selection.md
- contents/operating-system/signals-process-supervision.md
- contents/language/java/java-thread-basics.md
confusable_with:
- operating-system/stdio-buffering-after-redirect
- operating-system/subprocess-pipe-backpressure-primer
- operating-system/o-cloexec-fd-inheritance-exec-leaks
forbidden_neighbors:
- contents/operating-system/stdio-buffering-after-redirect.md
expected_queries:
- subprocess에서 EOF가 왜 안 와요?
- close_fds pass_fds CLOEXEC 차이를 어떻게 이해하면 돼요?
- child가 끝났는데 pipe가 안 닫히는 이유가 뭐예요?
- subprocess stdout redirect에서 fd leak를 어떻게 막아요?
- fork/exec 경계에서 어떤 fd를 닫고 어떤 fd를 남겨야 해?
contextual_chunk_prefix: |
  이 문서는 subprocess 입문자가 stdout/stderr redirect와 pipe EOF 문제를 볼 때 child에 남길 fd와 exec 경계에서 사라질 fd를 어떻게 구분하는지 기초를 잡는 primer다. 자식 종료 뒤 read가 안 끝남, 실행 후 소켓이 계속 남음, 표준입출력 배선, 실행 경계 핸들 정리, 헬퍼 프로세스가 fd를 물고 감 같은 자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다.
---
# Subprocess FD Hygiene Basics

> 한 줄 요약: subprocess I/O에서 spawn API 모양이 달라도 가장 안전한 기본값은 "pipe/socket은 생성 시점부터 `CLOEXEC`, child에 남길 것은 `0/1/2`만 명시하고, parent/child 모두 안 쓰는 pipe end를 즉시 닫기"다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md) 다음에 읽는 beginner bridge다. `fork()` / `exec()` / `posix_spawn()` 이름은 아는데 stdout/stderr redirect, pipe EOF, leaked fd across `exec()`가 자꾸 섞일 때 "어느 API를 쓰든 무엇을 남기고 무엇을 닫아야 하는가"부터 고정한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Subprocess Symptom First-Branch Guide](./subprocess-symptom-first-branch-guide.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)
- [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
- [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
- [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
- [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
- [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- [signals, process supervision](./signals-process-supervision.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)

retrieval-anchor-keywords: subprocess fd hygiene basics, fd leak across exec, eof가 왜 안 와요, child finished but pipe not closed, close_fds pass_fds mental model, cloexec 뭐예요, dup2 redirect basics, subprocess stdout redirect, subprocess stdin redirect, shell helper fd leak, listener inherited by child, parent forgot pipe close, subprocess pipe mapping, close-on-exec basics, subprocess basics

## 이 문서가 먼저 맞는 질문

- child는 끝난 것 같은데 parent `read()`가 EOF를 못 받아 계속 기다릴 때
- `close_fds`, `pass_fds`, `CLOEXEC`, `dup2()`가 이름만 다르고 머릿속에서 같은 그림으로 안 묶일 때
- shell wrapper나 helper를 끼운 뒤에만 socket/listener가 안 닫히는 것처럼 보일 때
- "`stdio buffering` 문제인가 `fd 상속` 문제인가"를 먼저 갈라야 할 때

## Subprocess Primer Handoff

> **이 문서는 subprocess 입문 흐름의 1단계다**
>
> - 출발점: [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)에서 parent/child, `pipe`, `waitpid()` 그림을 먼저 잡는다
> - 지금 문서의 질문: "child에 남길 fd와 바로 닫을 fd를 어떻게 구분하지?"
> - 다음 문서: [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)에서 "배선은 맞는데 왜 child가 출력하다 멈추지?"를 잇는다

## 먼저 잡는 멘탈 모델

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

## spawn API 선택이 바꾸는 것: hygiene를 어디에 적는가

초보자가 자주 헷갈리는 지점은 "`fork()`를 쓰느냐 `posix_spawn()`을 쓰느냐에 따라 규칙 자체가 달라지나?"다.
결론부터 말하면 **규칙은 거의 같고, 그 규칙을 코드 어디에 적는지만 달라진다.**

| launch 모양 | stdio / fd 정리를 적는 위치 | beginner-safe 기본값 | 자주 나는 실수 |
|---|---|---|---|
| `fork()` + `exec()` | child가 `fork()` 뒤 `exec()` 전 구간에서 `dup2()` / `close()` 수행 | `pipe2(O_CLOEXEC)`로 만들고 `0/1/2`만 남긴다 | parent나 child가 원래 pipe end 하나를 안 닫아 EOF가 안 온다 |
| `posix_spawn()` | `posix_spawn_file_actions_*()` 같은 file actions에 명시 | parent가 만드는 fd 자체를 먼저 `O_CLOEXEC`로 두고, file actions로 survivor만 지정한다 | "`posix_spawn()`이 알아서 깨끗하게 정리하겠지"라고 가정한다 |
| high-level subprocess API ([`popen()`, language runtime wrapper](./popen-runtime-wrapper-mapping.md)) | `stdin/stdout/stderr`, `close_fds`, `pass_fds` 같은 옵션으로 표현 | 기본 close policy를 유지하고 필요한 fd만 예외로 넘긴다 | 편의를 위해 `close_fds=false`를 켜거나 shell wrapper를 여러 겹 둔다 |
| 이미 child 안에서 `exec()`만 호출 | 현재 프로세스가 바로 새 프로그램으로 바뀐다 | `exec()` 전에 원치 않는 fd를 닫거나 `CLOEXEC`로 막아 둔다 | "`exec()`면 새 프로그램이니 fd도 자동 정리된다"라고 오해한다 |

핵심은 이것이다.

- spawn API가 달라도 pipe EOF는 "지금 write end를 누가 들고 있나"가 결정한다
- `CLOEXEC`는 그 write end가 **추가 `exec()`를 거친 helper**까지 새는 것을 막는다
- `close()`는 parent/child가 **현재 시점에 쥔 불필요한 끝**을 정리한다

즉 API 선택은 표현 방식의 차이이고, hygiene 기본 원칙은 같다.

다만 `shell=True`, `sh -c`, shell script wrapper처럼 shell이 한 겹 끼면 "fd가 target에 직접 가는가, shell에도 먼저 보이는가"라는 boundary가 추가된다. 이 감각은 [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)에서 따로 떼어 읽는 편이 쉽다.

## spawn API 선택이 바꾸는 것: hygiene를 어디에 적는가 (계속 2)

stdout/stderr redirect 배선은 맞는데 parent가 출력을 늦게 받는다면 fd 문제가 아니라 child stdio buffering일 수 있다. 이 차이는 [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)에서 따로 분리해 읽는 편이 안전하다.

`popen()`, `PIPE`, `close_fds`, `pass_fds` 같은 runtime wrapper 옵션 이름이 OS 그림과 잘 연결되지 않는다면 [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)에서 pipe와 fd table 작업으로 먼저 번역해 보면 된다.
`fork()` 쪽 `dup2()` 감각은 잡혔는데 `posix_spawn()` 행만 유독 추상적으로 느껴진다면 [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)에서 `adddup2()` / `addopen()` / `addclose()`를 child-side 체크리스트로 번역해 놓은 버전을 먼저 보는 편이 쉽다.
redirect는 이해했는데 process group, signal mask, signal default가 왜 별도 설정으로 나뉘는지가 남는다면 [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)로 이어서 읽으면 `attrs`가 fd hygiene와 다른 종류의 문제를 푼다는 점이 정리된다.

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

## 왜 pipe EOF 버그와 exec leak가 같이 보이나

초보자에게 가장 혼란스러운 부분은 "EOF가 안 오는 문제"와 "descriptor leak"가 따로 노는 버그처럼 보인다는 점이다. 실제로는 같은 줄기에서 만나는 경우가 많다.

```text
parent가 write end를 안 닫음
  -> reader는 EOF를 못 봄

helper process가 leaked write end를 exec 뒤에도 들고 있음
  -> reader는 역시 EOF를 못 봄
```

reader 입장에서는 둘 다 똑같이 보인다.

- "아직 누군가 write end를 들고 있다"
- 그래서 EOF를 보내지 못한다

차이는 원인 위치다.

- 현재 parent/child의 정리 실수면 `close()` 문제다
- 예상 밖 helper/subprocess까지 write end가 갔다면 `CLOEXEC` / close policy 문제다

그래서 EOF가 안 오면 "`close()`만 보면 된다"도 틀리고 "`CLOEXEC`만 보면 된다"도 틀리다.
둘을 같이 봐야 한다.

## 흔한 실수 빠른 비교

| 실수 | 보이는 증상 | 먼저 고칠 기본값 |
|---|---|---|
| `pipe()`로 만든 뒤 나중에 `fcntl(FD_CLOEXEC)`를 붙인다 | 멀티스레드 spawn 경로에서 가끔 helper가 pipe/socket을 상속한다 | `pipe2(O_CLOEXEC)`, `open(..., O_CLOEXEC)`처럼 생성 시점 flag로 바꾼다 |
| `dup2()` 뒤 원래 pipe fd를 닫지 않는다 | child 종료 뒤에도 parent read가 EOF를 못 보거나 backpressure가 꼬인다 | parent/child 모두 remap 후 원래 번호를 즉시 닫는다 |
| `close_fds=false` 또는 broad shell wrapper를 습관처럼 쓴다 | listener, admin socket, temp fd가 예상 밖 subprocess까지 퍼진다 | 기본 close policy를 유지하고 의도적 handoff만 `pass_fds`/file actions로 문서화한다 |

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

작게 읽는 표:

| `lsof` 표시 | subprocess 문맥에서 먼저 떠올릴 뜻 |
|---|---|
| `FIFO` | parent-child 사이 pipe일 가능성이 크다. EOF가 안 오면 누가 반대쪽 end를 아직 들고 있는지 본다. |
| `REG` | redirect 대상 일반 파일이다. stdout/stderr가 파일로 빠지는지 확인할 때 본다. |
| `IPv4` | child가 네트워크 socket도 함께 상속했을 수 있다. 원치 않는 listener/socket leak 여부를 의심한다. |
| `(deleted)` | 지워진 파일이지만 fd는 아직 살아 있다. log file reopen 누락이나 temp file 정리 실패를 떠올린다. |

흔한 오해:

- `FIFO`가 보인다고 named pipe만 뜻하는 것은 아니다. 초보자 관찰에서는 "pipe 계열 연결선"으로 먼저 읽으면 충분하다.
- `(deleted)`는 "곧 정리될 것"이 아니라 "아직 열린 참조가 남아 있다"는 경고에 가깝다.

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

> Q: `fork()+exec()` 대신 `posix_spawn()`을 쓰면 `CLOEXEC`를 신경 안 써도 되나요?
> 핵심: 아니다. API가 바뀌어도 원치 않는 fd를 기본적으로 넘기지 않는 원칙은 같고, 생성 시점 `O_CLOEXEC`가 여전히 가장 안전한 출발점이다.

## Self-check (자가 점검 4문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. `CLOEXEC`가 막는 문제(`exec` 경계 leak)와 `close()`가 푸는 문제(EOF/lifecycle 정리)를 말로 분리해 설명할 수 있는가?
   힌트: `CLOEXEC`는 새 프로그램으로 fd가 새는 일을 막고, `close()`는 현재 파이프 생명주기를 끝내는 동작이다.
2. "`기본값은 close all, 필요한 것만 명시 inherit`" 원칙을 `fork()+exec()`와 `posix_spawn()` 둘 다에 적용해 볼 수 있는가?
   힌트: 어떤 생성 API를 쓰든 기본은 최소 상속이고, 필요한 fd만 의도적으로 남긴다는 사고가 안전하다.
3. child redirect에서 `dup2()` 뒤 원래 pipe end를 parent/child가 각각 왜 닫아야 하는지 설명할 수 있는가?
   힌트: 새 표준 입출력 자리에 복제한 뒤 원본까지 들고 있으면 EOF 판정과 자원 정리가 꼬이기 쉽다.
4. "child는 종료됐는데 parent read가 EOF를 못 받는 상황"에서 먼저 확인할 주체(누가 write end를 들고 있는지)를 떠올릴 수 있는가?
   힌트: 누군가 write end 복사본을 아직 열어 두면 커널은 아직 쓰는 쪽이 남았다고 판단한다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`stdout=PIPE`인데 왜 child가 `write()`에서 멈추지?"가 남으면: [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
> - "`popen()` / `PIPE` / `close_fds` 옵션이 실제 fd table에서 어떻게 보이지?"를 보고 싶으면: [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
> - "`exec()` 뒤에도 fd leak를 왜 계속 신경 써야 하지?"를 더 파려면: [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

subprocess FD hygiene의 가장 안전한 기본값은 "`CLOEXEC`로 새는 길을 막고, `dup2()`로 `0/1/2`만 의도적으로 남기고, parent/child 모두 안 쓰는 pipe end를 즉시 닫는다"다.
