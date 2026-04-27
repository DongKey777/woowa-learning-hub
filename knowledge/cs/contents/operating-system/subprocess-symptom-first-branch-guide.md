# Subprocess Symptom First-Branch Guide

> 한 줄 요약: subprocess가 "멈춘다"처럼 보여도 원인은 `fd 누수`, `출력 pipe backpressure`, `양방향 read/write 순서`로 갈리므로, 먼저 증상 모양으로 문서를 고르면 초반 분기가 빨라진다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md) 다음에 읽는 beginner bridge다. [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md), [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md), [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md), [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md) 중 어디부터 읽어야 할지 첫 분기 기준을 한 표로 묶는다.

**난이도: 🟢 Beginner**

관련 문서:

- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
- [Broken Pipe and `SIGPIPE` Bridge](./broken-pipe-sigpipe-bridge.md)
- [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)
- [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)
- [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: subprocess symptom first branch guide, subprocess symptom mental model, subprocess hang mental model, subprocess comparison table, fd hygiene vs backpressure vs bidirectional deadlock, subprocess first doc to read, subprocess hang triage primer, stdout pipe full vs eof hang, stdin pipe stdout pipe deadlock, child waits for stdin eof, parent forgot stdin close, subprocess stdin eof branch, subprocess symptom map, subprocess branch guide, subprocess beginner guide, 서브프로세스 멈춤 멘탈 모델, 서브프로세스 분기 멘탈 모델, pipe eof 안 옴, wait 먼저 read 나중 멈춤, stdin pipe stdout pipe 같이 쓰면 멈춤, stdin 안 닫아서 멈춤, subprocess 어디부터 읽지, primer handoff box, beginner handoff box

## 먼저 잡는 멘탈 모델

subprocess 멈춤은 한 종류가 아니다. 초보자는 먼저 아래 셋을 다른 문제로 나눠 보면 된다.

- **fd hygiene**: "누가 pipe end나 socket fd를 아직 쥐고 있지?"
- **backpressure**: "parent가 출력을 제때 안 읽어서 pipe가 꽉 찼나?"
- **bidirectional deadlock**: "입력 쓰기, 출력 읽기, stdin close 순서가 서로 물리나?"

같이 "hang"처럼 보여도 첫 질문이 다르다.
문서 선택도 그 첫 질문에 맞추면 된다.

## 한눈에 고르는 비교표

| 겉으로 보이는 증상 | 먼저 던질 질문 | 먼저 볼 문서 | 이유 |
|---|---|---|---|
| child는 이미 끝난 것 같은데 parent `read()`가 EOF를 못 받는다 | write end를 parent/helper/shell wrapper 중 누가 아직 들고 있나 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) | EOF 문제는 대개 "fd가 아직 열려 있음"에서 시작한다 |
| `wait()`를 먼저 했더니 child가 안 끝난다 | stdout/stderr pipe를 실행 중에 누가 drain하나 | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) | parent가 안 읽으면 child가 `write()`에서 멈출 수 있다 |
| `stdin=PIPE`, `stdout=PIPE`를 같이 쓸 때 큰 입력이나 특정 명령(`cat`, `sort`)에서 멈춘다 | 입력 쓰기, 출력 읽기, stdin close 순서가 맞나 | [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md) | 양방향 pipe는 queue 두 개와 EOF 순서를 함께 맞춰야 한다 |
| stdout은 잘 읽는데 실패할 때만 가끔 멈춘다 | stderr도 같이 drain하고 있나 | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) | 장애 경로에서 stderr가 먼저 꽉 차는 경우가 흔하다 |
| `stdin.write()` 후 `flush()`까지 했는데 결과가 안 온다 | child가 EOF를 받아야 결과를 내는 타입인가 | [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md) | `flush()`는 EOF가 아니고, 일부 child는 `close(stdin)` 뒤에만 반응한다 |
| parent가 read end를 먼저 닫은 뒤 child가 갑자기 죽거나 `BrokenPipeError`/`EPIPE`가 보인다 | reader가 사라진 뒤 writer가 계속 쓰고 있나 | [Broken Pipe and `SIGPIPE` Bridge](./broken-pipe-sigpipe-bridge.md) | pipe full이 아니라 "더 받을 쪽이 없음"이므로 `SIGPIPE`/`EPIPE`로 surface가 바뀐다 |
| shell wrapper나 helper를 끼운 뒤에만 EOF/리스너 누수가 이상해진다 | 원치 않는 fd가 `exec()` 경계를 넘어갔나 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) | `CLOEXEC`, `close_fds`, `pass_fds` 축을 먼저 봐야 한다 |

## 30초 분기 규칙

| 먼저 관찰한 사실 | 초보자용 첫 분기 |
|---|---|
| child가 "출력을 많이 낼 때만" 멈춘다 | backpressure부터 본다 |
| child가 이미 끝났는데도 EOF가 안 온다 | fd hygiene부터 본다 |
| `stdin=PIPE`와 `stdout=PIPE`를 둘 다 잡았다 | bidirectional deadlock부터 본다 |
| 입력은 다 보낸 것 같은데 child가 계속 기다린다 | stdin EOF부터 본다 |
| 출력은 늦게 보이지만 결국 다 나온다 | 위 3개보다 [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)를 먼저 본다 |

핵심은 이것이다.

- **EOF가 안 온다**: 누가 fd를 쥐고 있는지부터 본다
- **출력이 많을 때 멈춘다**: pipe를 누가 비우는지부터 본다
- **입출력을 둘 다 한다**: read/write/close 순서를 먼저 본다
- **입력을 다 보냈는데도 child가 안 넘어간다**: EOF를 누가 막고 있는지부터 본다

## 자주 헷갈리는 포인트

- "`wait()`에서 멈췄으니 process lifecycle 문제겠지"라고 바로 가지 않는다.
  `stdout=PIPE` / `stderr=PIPE`가 있으면 backpressure일 수 있다.
- "`flush()` 했는데 왜 결과가 안 오지?"는 buffering만의 문제가 아니다.
  child가 EOF를 기다리는 타입이면 `stdin.close()`가 빠졌을 수 있다.
- "`CLOEXEC`만 켜면 hang가 다 해결된다"도 아니다.
  `CLOEXEC`는 fd 누수를 줄이지만, parent가 stdout/stderr를 안 읽으면 pipe는 여전히 찬다.

## 작은 예시로 고르기

| 코드 패턴 | 가장 먼저 의심할 문서 |
|---|---|
| `p.wait(); out = p.stdout.read()` | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) |
| `p.stdin.write(big_data); p.stdin.close(); out = p.stdout.read()`에서 큰 입력만 멈춤 | [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md) |
| `p.stdin.write(data); p.stdin.flush(); out = p.stdout.read()` | [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md) |
| child 종료 뒤에도 `read()`가 끝나지 않고 shell/helper를 거친다 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) |

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`EOF가 왜 안 오지, 누가 fd를 들고 있지?`"를 보면: [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - "`wait()` 먼저 했더니 왜 child가 안 끝나지?"를 보면: [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
> - "`stdin=PIPE`와 `stdout=PIPE`를 같이 쓰면 왜 순서가 중요하지?"를 보면: [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)
> - "`입력을 다 보낸 것 같은데 왜 child가 stdin EOF를 못 받지?`"를 보면: [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)
