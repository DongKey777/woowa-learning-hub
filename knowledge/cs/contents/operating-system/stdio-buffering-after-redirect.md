# Stdio Buffering After Redirect

> 한 줄 요약: child stdout을 pipe나 file로 redirect했는데 출력이 늦게 보이는 이유는 fd 연결이 늦어서가 아니라, child 프로그램의 stdio 버퍼가 아직 `write()`를 호출하지 않았기 때문일 수 있다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) 다음에 읽는 beginner bridge다. `dup2()` / `posix_spawn_file_actions_adddup2()`로 stdout 배선은 맞춘 것 같은데 parent가 child 출력을 늦게 받거나 file에 로그가 한꺼번에 쓰이는 현상이 헷갈릴 때, "fd wiring"과 "stdio buffering"을 분리해 본다.

**난이도: 🟢 Beginner**

관련 문서:

- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- [page cache, dirty writeback, fsync](./page-cache-dirty-writeback-fsync.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: stdio buffering after redirect, stdout buffering after pipe redirect, child output delayed pipe, child stdout delayed, subprocess output delayed, redirected stdout buffering, file redirection buffering, pipe redirection buffering, line buffering vs full buffering, fd wiring vs stdio buffering, dup2 works but output delayed, posix_spawn stdout delayed, fflush stdout, setvbuf stdout, stdbuf line buffered, unbuffered stdout, stderr appears before stdout, child log delayed

## 핵심 개념

먼저 그림을 단순하게 잡자.

```text
child 코드의 printf/println
  -> language/runtime stdio buffer
  -> write(1, ...)
  -> fd 1이 가리키는 pipe/file/terminal
  -> parent reader 또는 file
```

`dup2(pipe_write, STDOUT_FILENO)`나 `posix_spawn_file_actions_adddup2(..., STDOUT_FILENO)`는 **fd 1이 어디를 향하는지**를 바꾼다.  
하지만 `printf()` 같은 stdio 함수는 바로 `write(1, ...)`를 호출하지 않고 자기 버퍼에 잠시 모아 둘 수 있다.

그래서 parent 입장에서는 이렇게 보일 수 있다.

- fd wiring은 이미 맞다
- child도 `printf("tick\n")`를 실행했다
- 그런데 child runtime이 아직 `write()`를 안 해서 parent pipe에는 읽을 byte가 없다

즉 "redirect가 안 됐다"가 아니라 **"redirect된 목적지로 아직 flush되지 않았다"**가 원인일 수 있다.

## 터미널일 때와 pipe/file일 때 달라지는 기본값

많은 C stdio/libc 계열 runtime은 stdout이 터미널인지 아닌지에 따라 버퍼링 방식을 바꾼다. 언어와 런타임마다 세부값은 다르지만 beginner mental model은 아래처럼 잡으면 된다.

| child stdout 대상 | 흔한 stdout buffering | 보이는 현상 |
|---|---|---|
| 터미널(TTY) | line buffered | `\n`이 나오면 바로 보이는 것처럼 느껴진다 |
| pipe | full buffered인 경우가 많음 | 여러 줄이 모였다가 buffer가 차거나 flush/exit 때 한꺼번에 보일 수 있다 |
| 일반 file | full buffered인 경우가 많음 | 로그 파일에 늦게 쓰이거나 process 종료 때 몰아서 쓰이는 것처럼 보일 수 있다 |
| stderr | unbuffered 또는 더 짧게 flush되는 경우가 많음 | stderr는 바로 보이는데 stdout만 늦는 것처럼 보일 수 있다 |
| `write(2)` 직접 호출 | stdio buffer를 거치지 않음 | syscall이 성공하면 kernel pipe/file 쪽으로 바로 넘어간다 |

여기서 중요한 차이는 "stdout이 pipe라서 kernel이 줄 단위로 기다린다"가 아니다.  
대부분의 지연은 kernel pipe 앞단의 **프로그램 stdio buffer**에서 생긴다.

## fd wiring과 stdio buffering 빠른 비교

| 질문 | fd wiring 문제 | stdio buffering 문제 |
|---|---|---|
| "child stdout이 어디로 가나?" | `fd 1`이 terminal/pipe/file 중 무엇을 가리키는지 | 이미 연결된 목적지로 언제 byte를 밀어낼지 |
| 대표 API | `dup2()`, `adddup2()`, `addopen()`, shell `>` / `|` | `fflush()`, `setvbuf()`, language unbuffered option |
| 고장 증상 | 출력이 아예 다른 곳으로 가거나 parent가 pipe를 잘못 읽는다 | 종료/flush 전까지 출력이 늦게 보인다 |
| 확인 감각 | `/proc/<pid>/fd/1`, spawn file actions, parent pipe end close | newline/flush/exit 후에 갑자기 나온다, stderr는 먼저 보인다 |
| 관련 문서 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) | 이 문서 |

초보자에게 가장 중요한 분리는 이것이다.

> `dup2()`는 "stdout 목적지"를 바꾸고, `fflush()`는 "stdout 버퍼 안의 byte를 지금 목적지로 밀어낸다."

## 작은 예제

아래처럼 child가 1초마다 한 줄씩 찍는다고 하자.

```c
for (int i = 0; i < 3; i++) {
    printf("tick %d\n", i);
    sleep(1);
}
```

터미널에서 직접 실행하면 보통 이렇게 느껴진다.

```text
tick 0
tick 1
tick 2
```

각 줄이 1초마다 보이는 이유는 stdout이 터미널이라 line buffering이 걸리고, `\n`이 flush 계기가 되기 때문이다.

하지만 parent가 child stdout을 pipe로 redirect해서 읽으면 런타임에 따라 parent가 3초 뒤에 한꺼번에 받을 수 있다.

```text
tick 0
tick 1
tick 2
```

이때 fd 연결이 3초 뒤에 된 것이 아니다.

- child stdout fd는 시작 시점부터 pipe를 가리켰다
- 다만 `printf()` 결과가 child stdio buffer에 모여 있었다
- buffer full, `fflush(stdout)`, 정상 `exit()`, 또는 런타임 정책 때문에 나중에 `write()`가 발생했다

진행 상황 로그처럼 즉시성이 중요하면 child 코드에서 의도를 드러내야 한다.

```c
printf("tick %d\n", i);
fflush(stdout);
```

또는 처음부터 stdout buffering 정책을 바꾼다.

```c
setvbuf(stdout, NULL, _IOLBF, 0); /* line buffered */
```

## 어떻게 고칠지 고르는 기준

| 상황 | 먼저 할 일 | 이유 |
|---|---|---|
| 내가 child 코드를 고칠 수 있음 | 진행 로그 뒤 `fflush(stdout)` 또는 line/unbuffered 설정 | output timing 의도를 코드에 명시한다 |
| child 코드를 못 고침 | GNU/Linux에서는 `stdbuf -oL` / `stdbuf -o0` 같은 wrapper를 검토 | 프로그램 바깥에서 stdout buffering 정책을 바꿀 수 있다 |
| CLI가 TTY일 때만 즉시 출력함 | pseudo-tty 사용을 검토하되 신중히 적용 | TTY로 보이면 line buffering/색상/progress bar 동작이 함께 바뀔 수 있다 |
| 최종 결과만 필요함 | 굳이 unbuffered로 바꾸지 않고 종료까지 읽는다 | 즉시성이 필요 없으면 buffering은 성능에 도움 된다 |
| 출력이 아예 안 오고 EOF도 안 옴 | fd wiring/pipe end close 문제를 먼저 본다 | 이 경우는 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)의 `close()` / `CLOEXEC` 문제일 수 있다 |

언어별 옵션은 다르다. 예를 들어 Python은 `-u`나 `PYTHONUNBUFFERED=1`이 있고, Java는 `PrintWriter`의 auto-flush 여부나 logging framework appender 설정이 영향을 줄 수 있다. 핵심은 옵션 이름이 아니라 **"stdio/runtime buffer를 언제 flush할지"**다.

## 자주 헷갈리는 포인트

### 1. `dup2()`가 늦게 적용된 것 아닌가요?

보통 아니다. `dup2()`나 file actions가 성공했다면 child가 새 프로그램을 시작할 때 fd 1은 이미 pipe/file을 향한다. 늦는 것은 fd 연결이 아니라 child의 `write()` 호출이다.

### 2. pipe가 newline을 기다리나요?

아니다. kernel pipe는 byte stream이다. newline을 특별히 기다리지 않는다. newline을 보고 flush할지 말지는 pipe 앞단의 stdio/runtime 정책이다.

### 3. stderr는 바로 보이는데 stdout만 늦는 이유는 뭔가요?

stderr는 에러 메시지를 잃지 않기 위해 unbuffered이거나 더 자주 flush되는 기본값을 쓰는 경우가 많다. 그래서 같은 child process 안에서도 `stderr` 로그가 `stdout` 로그보다 먼저 보일 수 있다.

### 4. redirect한 파일에 로그가 늦게 생기면 `fsync()` 문제인가요?

먼저 stdio buffer를 봐야 한다. `fsync()`는 이미 kernel에 넘어간 file data를 storage 내구성 관점에서 다룬다. `printf()` 결과가 아직 `write()`로 넘어가지 않았다면 `fsync()` 이전 단계의 문제다. page cache / durability까지 이어서 보고 싶을 때만 [page cache, dirty writeback, fsync](./page-cache-dirty-writeback-fsync.md)로 내려가면 된다.

### 5. process가 비정상 종료하면 buffered stdout이 사라질 수 있나요?

그럴 수 있다. 정상 `exit()`는 보통 stdio buffer를 flush하지만, crash, `SIGKILL`, `_exit()` 같은 경로는 stdio flush를 건너뛸 수 있다. 즉시 필요한 진행 로그나 장애 로그는 stderr, explicit flush, logging framework flush 정책을 명확히 잡는 편이 안전하다.

## beginner 체크리스트

- fd 1이 pipe/file로 연결됐는지와 stdout buffer가 flush됐는지를 분리해서 생각한다.
- "종료할 때 한꺼번에 보인다"면 fd wiring보다 buffering을 먼저 의심한다.
- "아예 EOF가 안 온다"면 buffering보다 누가 pipe write end를 들고 있는지 먼저 본다.
- stderr와 stdout 순서가 섞이면 scheduling보다 buffering 차이를 먼저 떠올린다.
- 파일 durability 문제로 가기 전에 `fflush()`/runtime flush가 있었는지 확인한다.

## 이 문서 다음에 보면 좋은 문서

- child에 어떤 fd를 남기고 닫을지부터 다시 잡으려면 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- `posix_spawn()` redirection을 child-side checklist로 읽고 싶으면 [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
- fd 번호와 fd table 자체가 아직 낯설면 [파일 디스크립터 기초](./file-descriptor-basics.md)
- `dup()` / `fork()` 뒤 shared open file description과 file offset까지 보려면 [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)

## 한 줄 정리

redirect는 "fd 1이 어디를 향하는가"이고 buffering은 "child runtime이 언제 `write(1, ...)`를 호출하는가"다. child 출력이 늦게 보이면 두 층을 섞지 말고, fd wiring 확인 뒤 stdio flush 정책을 따로 확인한다.
