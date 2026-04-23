# Subprocess Pipe Backpressure Primer

> 한 줄 요약: child stdout/stderr를 pipe로 받으면 pipe는 작은 대기열이 되고, parent가 제때 읽지 않으면 대기열이 차서 child가 `write()` 안에서 멈출 수 있다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) 다음에 읽는 beginner bridge다. `stdout=PIPE`, `stderr=PIPE`, `popen()`, `ProcessBuilder`처럼 child 출력을 parent가 받는 구조에서 "왜 wait만 했는데 child가 안 끝나지?"를 pipe backpressure 관점으로 설명한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- [동기/비동기와 블로킹/논블로킹 기초](./sync-async-blocking-nonblocking-basics.md)
- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [signals, process supervision](./signals-process-supervision.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: operating-system-00055, subprocess pipe backpressure primer, subprocess pipe backpressure, child blocks writing stdout pipe, child process blocked stdout stderr, parent does not drain pipe, parent wait before read deadlock, subprocess wait deadlock, subprocess communicate pipe drain, stdout pipe full, stderr pipe full, pipe buffer full, pipe capacity finite, drain stdout stderr promptly, child stuck in write syscall, write blocks when pipe full, popen read deadlock, ProcessBuilder pipe deadlock, Python subprocess PIPE deadlock, pipe backpressure 처음 배우는데, stdout stderr 안 읽으면 멈춤

## 핵심 개념

먼저 pipe를 "작은 물통"처럼 생각하면 된다.

```text
child stdout/stderr
  -> kernel pipe buffer 라는 작은 대기열
  -> parent가 read()로 비움
```

child가 출력 byte를 계속 넣는데 parent가 비우지 않으면 pipe buffer가 찬다.  
pipe buffer가 가득 찬 상태에서 child가 blocking fd에 `write(1, ...)` 또는 `write(2, ...)`를 호출하면, kernel은 "공간이 생길 때까지" child를 재운다.

그래서 겉으로는 이렇게 보인다.

- child가 CPU를 쓰지 않는다
- parent는 child 종료를 기다린다
- 로그는 더 이상 늘지 않는다
- 하지만 child는 죽은 것이 아니라 `write()`에서 막혀 있다

이 흐름이 **pipe backpressure**다. 받는 쪽이 느리거나 멈추면 보내는 쪽도 결국 멈춘다.

## 어디에서 막히나

출력 한 줄은 대략 아래 경로를 지난다.

```text
child printf/logging
  -> child runtime buffer
  -> write(1 or 2, bytes)
  -> kernel pipe buffer
  -> parent read()
```

이 문서가 다루는 지점은 `write()` 뒤의 **kernel pipe buffer**다.

| 층 | 질문 | 막히면 보이는 현상 | 이어서 볼 문서 |
|---|---|---|---|
| child stdio/runtime buffer | child가 아직 `write()`를 호출했나 | 출력이 늦게 보이다가 한꺼번에 나온다 | [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md) |
| kernel pipe buffer | parent가 pipe를 제때 비우나 | child가 `write()`에서 멈춰 종료하지 못한다 | 이 문서 |
| fd lifecycle | write end가 아직 열려 있나 | child가 끝났는데 EOF가 안 온다 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) |
| process lifecycle | 종료한 child를 회수했나 | zombie가 남거나 exit status를 못 읽는다 | [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md) |

초보자에게 중요한 구분은 이것이다.

> "출력이 늦게 보임"은 buffering일 수 있고, "출력이 많을 때 child가 안 끝남"은 pipe backpressure일 수 있다.

## 가장 흔한 deadlock: 먼저 `wait()`, 나중에 `read()`

가장 위험한 패턴은 parent가 child 출력을 pipe로 연결해 놓고, pipe를 읽기 전에 child 종료만 기다리는 것이다.

```python
p = subprocess.Popen(
    ["some-command"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

p.wait()          # child가 끝나기를 먼저 기다림
out = p.stdout.read()
err = p.stderr.read()
```

작은 출력에서는 우연히 통과할 수 있다. 하지만 child가 많이 출력하면 흐름이 이렇게 바뀐다.

```text
parent: wait()에서 child 종료를 기다림
child : stdout pipe에 계속 write()
pipe  : parent가 안 읽어서 가득 참
child : write(1, ...)에서 block
parent: child가 종료하지 않아서 계속 wait()
```

서로 기다리므로 deadlock처럼 보인다.

안전한 기본형은 "기다리는 동안 출력도 같이 비우는 것"이다.

```python
p = subprocess.Popen(
    ["some-command"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

out, err = p.communicate()
```

`communicate()`의 핵심은 API 이름이 아니라 정책이다.

- child가 실행되는 동안 stdout/stderr를 drain한다
- child 종료도 기다린다
- pipe가 차서 child가 멈추는 경로를 줄인다

직접 구현한다면 parent는 별도 thread, event loop, nonblocking I/O, 또는 selector로 stdout/stderr를 계속 읽어야 한다.

## stdout과 stderr는 따로 찬다

child에 `stdout=PIPE`, `stderr=PIPE`를 둘 다 걸면 pipe가 두 개 생긴다.

```text
child fd 1(stdout) -> stdout pipe -> parent reader A
child fd 2(stderr) -> stderr pipe -> parent reader B
```

여기서 stdout만 열심히 읽고 stderr를 방치하면 stderr pipe가 찰 수 있다. 그러면 child는 `write(2, ...)`에서 멈춘다. 반대도 가능하다.

| parent 동작 | 위험 |
|---|---|
| stdout만 읽고 stderr는 나중에 읽음 | stderr가 많이 나오면 child가 멈춘다 |
| stderr만 읽고 stdout은 나중에 읽음 | stdout이 많이 나오면 child가 멈춘다 |
| stdout/stderr를 같은 pipe로 합침 | deadlock 위험은 줄지만 stream 구분이 사라진다 |
| 둘 다 동시에 drain | 가장 명확한 capture 패턴이다 |
| 한쪽을 파일이나 `/dev/null`로 보냄 | parent가 읽을 필요는 줄지만 저장/폐기 정책을 명확히 해야 한다 |

따라서 "stdout만 필요하다"는 말과 "stderr를 안 읽어도 된다"는 말은 다르다. stderr를 버릴 거면 pipe로 만들지 말고 명시적으로 버리거나 파일로 보내는 편이 낫다.

## pipe capacity에 의존하지 않는다

pipe buffer 크기는 운영체제, 커널 설정, 런타임 상황에 따라 달라질 수 있다. 중요한 점은 정확한 숫자가 아니다.

초보자용 규칙은 단순하다.

- pipe는 무한 큐가 아니다
- 출력량이 pipe capacity보다 커질 수 있으면 parent가 실행 중에 읽어야 한다
- 테스트에서 작은 로그로 통과해도 운영에서 큰 stderr가 나오면 멈출 수 있다

그래서 "내 로컬에서는 됐다"가 안전 근거가 되지 않는다. 출력량이 커지는 순간 같은 코드가 막힐 수 있다.

## beginner-safe 선택지

| 상황 | 추천 기본값 | 이유 |
|---|---|---|
| stdout/stderr 전체가 필요함 | runtime의 `communicate()` 계열을 사용 | drain과 wait를 한 흐름으로 묶는다 |
| 긴 실행 중 실시간 로그가 필요함 | stdout/stderr를 별도 reader thread나 event loop로 계속 drain | child 실행 중 pipe가 차지 않게 한다 |
| stderr 내용은 필요 없음 | `stderr`를 `/dev/null` 또는 파일로 명시 redirect | 읽지 않을 pipe를 만들지 않는다 |
| stdout/stderr 구분이 필요 없음 | `stderr=STDOUT` 같은 merge를 검토 | 하나의 stream만 drain하면 된다 |
| 출력이 매우 클 수 있음 | pipe 대신 temp file, log file, bounded capture 사용 | parent 메모리와 pipe pressure를 같이 줄인다 |
| child stdin도 pipe임 | 입력을 다 쓴 뒤 parent write end를 닫음 | child가 EOF를 받아 다음 단계로 갈 수 있다 |

핵심은 parent가 "언젠가 읽겠다"가 아니라 **child가 쓰는 동안 읽는다**는 점이다.

## 흔한 오해

### 1. child가 멈춘 것은 scheduler 문제인가요?

대부분 아니다. child가 `write()`에서 block되면 scheduler는 그 프로세스를 runnable로 보지 않을 수 있다. CPU starvation이 아니라 pipe 공간을 기다리는 상태다.

### 2. newline을 찍으면 pipe가 자동으로 비워지나요?

아니다. newline은 kernel pipe를 비우지 않는다. newline 때문에 child runtime이 flush할 수는 있지만, flush 뒤 pipe가 가득 차 있으면 `write()`가 막힐 수 있다.

### 3. `CLOEXEC`나 fd close만 잘하면 backpressure가 사라지나요?

아니다. `CLOEXEC`와 `close()`는 fd leak와 EOF 문제를 줄인다. 하지만 parent가 살아 있는 동안 stdout/stderr pipe를 안 읽으면 pipe buffer는 여전히 찰 수 있다.

### 4. nonblocking으로 만들면 해결인가요?

자동 해결은 아니다. nonblocking fd에서는 pipe가 차면 `write()`가 `EAGAIN`으로 실패할 수 있다. 그러면 child나 parent가 retry, polling, buffering 정책을 직접 가져야 한다. beginner subprocess capture에서는 보통 parent가 drain 구조를 제대로 잡는 것이 먼저다.

### 5. stderr는 양이 작으니 나중에 읽어도 되나요?

장애 상황에서는 stderr가 가장 많이 나올 수 있다. stack trace, warning loop, verbose error log가 stderr pipe를 먼저 채우는 경우가 흔하다.

## 빠른 진단 감각

subprocess가 "가끔 안 끝난다"면 아래 순서로 보면 좋다.

1. `stdout=PIPE` 또는 `stderr=PIPE`를 만들고도 실행 중 읽지 않는가
2. parent가 `wait()`를 먼저 호출하고 `read()`를 나중에 하는가
3. stdout은 drain하지만 stderr는 방치하는가
4. child가 많은 로그를 쓰는 실패 경로에서만 멈추는가
5. `strace` 같은 도구에서 child가 `write(1, ...)` 또는 `write(2, ...)`에 오래 머무는가

반대로 child가 이미 끝났는데 parent read가 EOF를 못 받는다면 backpressure보다 "누가 write end를 아직 들고 있는가"가 먼저다. 그 경우는 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)의 pipe end close 문제로 돌아가면 된다.

## 이 문서 다음에 보면 좋은 문서

- wrapper 옵션 이름을 OS pipe/fd 그림으로 번역하려면 [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- 출력이 늦게 보이는 이유가 pipe full인지 stdio flush인지 분리하려면 [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- EOF가 안 오는 문제와 fd leak를 잡으려면 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- pipe와 socketpair/eventfd/memfd 중 무엇을 쓸지 고르려면 [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)

## 한 줄 정리

subprocess output pipe는 무한 로그 저장소가 아니라 작은 kernel buffer다. parent가 child 실행 중 stdout/stderr를 drain하지 않으면 child는 출력하다가 `write()`에서 멈출 수 있으므로, capture 코드는 "read와 wait를 함께 설계"해야 한다.
