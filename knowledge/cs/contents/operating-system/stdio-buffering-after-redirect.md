# stdout/stderr Ordering After Redirect

> 한 줄 요약: redirect 뒤에 stdout과 stderr 순서가 바뀌어 보이는 가장 흔한 이유는 "코드 실행 순서"와 "각 stream이 실제로 flush되어 밖으로 나온 순서"가 다르기 때문이다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) 다음에 읽는 beginner bridge다. `dup2()` / `posix_spawn_file_actions_adddup2()`로 stdout/stderr 배선은 맞춘 것 같은데 stderr가 먼저 보이거나, `2>&1`로 합쳤는데도 순서가 어긋나 보일 때, "fd wiring", "stdio buffering", "merge 지점"을 분리해 본다.

**난이도: 🟢 Beginner**

관련 문서:

- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [Shell Redirection Order Primer](./shell-redirection-order-primer.md)
- [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
- [CI Log Merge Behavior Primer](./ci-log-merge-behavior-primer.md)
- [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [HTTP Response Compression, Buffering, Streaming Trade-offs](../network/http-response-compression-buffering-streaming-tradeoffs.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: stdout stderr ordering after redirect, stdout delayed stderr immediate, stderr appears before stdout, redirect output delayed basics, fd wiring vs buffering mental model, stdout stderr merge order, 2>&1 buffering order, ci merged log order, python stdout stderr buffering tty pipe, node stdout stderr tty pipe behavior, redirect 후 순서가 바뀌어요, stdout stderr 순서 왜 바뀜

## 먼저 잡는 멘탈 모델

먼저 그림을 단순하게 잡자.

```text
child 코드
  -> stdout용 stdio buffer -> write(1, ...) -> stdout pipe/file
  -> stderr용 stdio buffer -> write(2, ...) -> stderr pipe/file
  -> parent / terminal / logger가 나중에 화면에 보여 줌
```

`dup2(pipe_write, STDOUT_FILENO)`와 `dup2(err_write, STDERR_FILENO)`는 **fd 1과 fd 2가 어디를 향하는지**를 바꾼다. 하지만 `printf()`와 `fprintf(stderr, ...)`는 "코드 줄을 실행한 즉시 같은 속도로 밖에 보인다"를 보장하지 않는다.

핵심은 세 가지다.

- stdout과 stderr는 **서로 다른 buffer**를 가질 수 있다
- stdout과 stderr는 **서로 다른 fd 경로**로 갈 수 있다
- 둘이 다시 한 화면에 합쳐질 때는 **flush된 시점**이나 **parent merge 정책**이 보이는 순서를 만든다

즉 "코드에서 stdout을 먼저 썼다"와 "밖에서 stdout이 먼저 보였다"는 다른 문장이다.

## 터미널일 때와 pipe/file일 때 달라지는 기본값

많은 C stdio/libc 계열 runtime은 stdout이 터미널인지 아닌지에 따라 버퍼링 방식을 바꾼다. 언어와 런타임마다 세부값은 다르지만 beginner mental model은 아래처럼 잡으면 된다.

| child 출력 대상 | 흔한 buffering 감각 | 보이는 현상 |
|---|---|---|
| stdout -> 터미널(TTY) | line buffered | `\n`이 나오면 바로 보이는 것처럼 느껴진다 |
| stdout -> pipe | full buffered인 경우가 많음 | 여러 줄이 모였다가 나중에 나온다 |
| stdout -> 일반 file | full buffered인 경우가 많음 | 로그 파일에 늦게 쓰이는 것처럼 보인다 |
| stderr | unbuffered 또는 더 자주 flush | stderr는 바로 보이는데 stdout만 늦게 보일 수 있다 |
| `write(2)` 직접 호출 | stdio buffer를 거치지 않음 | syscall이 성공하면 바로 kernel 쪽으로 넘어간다 |

여기서 중요한 차이는 "pipe가 newline을 기다린다"가 아니다. 대부분의 지연은 kernel pipe 앞단의 **프로그램 stdio buffer**에서 생긴다.

## buffering 지연 vs pipe hang 한눈에 비교

같은 "출력이 이상하다"여도 초보자가 먼저 갈라야 하는 축은 아래 둘이다.

| 관찰 | stdio buffering 지연 | pipe backpressure hang |
|---|---|---|
| 대표 증상 | 출력이 늦게 보이거나 몰려 나온다 | child가 출력 중 멈추고 parent `wait()`도 안 끝난다 |
| 실제로 막힌 곳 | child runtime/stdio buffer 앞단 | kernel pipe buffer가 꽉 찬 뒤 `write()` |
| child 상태 | 아직 flush 전이거나, flush가 늦다 | `write(1/2, ...)`에서 sleep/block |
| parent가 해야 할 일 | `flush`, unbuffered 옵션, merge 지점 확인 | stdout/stderr를 실행 중 계속 drain |
| 먼저 볼 문서 | 이 문서 | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) |

한 줄로 요약하면, **"늦게 보인다"는 timing 문제일 수 있지만 "안 끝난다"는 소비 속도 문제일 가능성이 크다.**

## 언어별 기본값 한눈에 보기

runtime wrapper를 만들 때 자주 헷갈리는 지점은 "모든 언어가 C stdio처럼 TTY면 line buffered, pipe면 full buffered일 것"이라고 가정하는 것이다. Python은 이 그림에 꽤 가깝지만, Java와 Node는 기본 표준 stream 계층이 다르다.

| 언어 | stdout -> TTY | stdout -> pipe/file | stderr -> TTY/pipe | runtime-wrapper에서 먼저 떠올릴 것 |
|---|---|---|---|---|
| Python 3.9+ | line buffered | block buffered | line buffered | stdout만 늦고 stderr가 먼저 보이는 전형적 사례가 가장 흔하다 |
| Java (`System.out`, `System.err`) | `println` 기준 자주 flush | `println` 기준 자주 flush | `println` 기준 자주 flush | TTY 여부보다 `println` vs `print`, 직접 만든 `PrintWriter`/logger 설정이 더 중요하다 |
| Node.js (POSIX 기준) | sync write | async write | sync write | classic stdio buffer보다 fd별 write 완료 시점과 parent merge가 더 큰 변수다 |

이 표는 "항상 똑같이 동작한다"는 뜻이 아니라, **초보자가 ordering surprise를 제일 빨리 좁혀 가는 1차 지도**다.

## Python에서 먼저 볼 것

Python 3 문서는 다음 감각을 거의 그대로 준다.

- interactive `stdout`은 line buffered
- non-interactive `stdout`은 block buffered
- `stderr`는 둘 다 line buffered

그래서 wrapper가 `stdout=PIPE`, `stderr=PIPE`로 child를 잡으면 아래 같은 현상이 흔하다.

```python
print("out 1")
sys.stderr.write("err 1\n")
```

코드는 `out 1`이 먼저여도, pipe 환경에서는 `err 1`이 먼저 보일 수 있다.
특히 `print(..., end="")`, 긴 loop, `time.sleep()`, process crash가 끼면 stdout 지연이 더 눈에 띈다.

| Python에서 먼저 볼 것 | 이유 |
|---|---|
| `python -u` / `PYTHONUNBUFFERED=1` 사용 여부 | stdout/stderr를 더 즉시 밀어낸다 |
| `print(..., flush=True)` 여부 | line 단위 timing 의도를 코드에 직접 적는다 |
| Python 버전 | 3.9부터 non-interactive `stderr`도 line buffered라 예전 글보다 덜 헷갈린다 |

즉 Python child라면 runtime wrapper 사용자는 먼저 **"stdout만 block buffered로 늦어진 건가?"**를 의심하는 편이 빠르다.

## Java에서 먼저 볼 것

Java 기본 표준 출력은 `System.out` / `System.err`의 `PrintStream`을 통해 나간다. 여기서 beginner가 잡아야 할 감각은 이것이다.

- 기본 `System.out`과 `System.err`는 보통 `println(...)`에서 자주 flush되는 쪽으로 동작한다
- 그래서 Python처럼 "TTY면 line buffered, pipe면 full buffered" 그림으로 바로 대응되지 않는 경우가 많다
- 대신 `print(...)`로 newline 없이 쓰거나, 직접 만든 `PrintWriter`/logging appender가 별도 버퍼를 가지면 그때 지연이 커진다

빠른 비교는 아래처럼 잡으면 된다.

| Java 코드 모양 | 흔한 관찰 |
|---|---|
| `System.out.println("x")` | TTY든 pipe든 비교적 바로 보이기 쉽다 |
| `System.out.print("x")` | newline/flush 전까지 늦게 보일 수 있다 |
| `BufferedWriter` / `PrintWriter(autoFlush=false)` | TTY 여부와 무관하게 앱 쪽 버퍼가 ordering surprise를 만든다 |
| logging framework async appender | stdout/stderr보다 logger queue flush가 더 큰 원인이 될 수 있다 |

그래서 Java child에서 stderr가 먼저 보여도, 첫 의심점은 "pipe라서 JVM이 full buffered라서"보다 **"우리가 `println`이 아닌 buffered writer/logger를 쓰고 있나?"** 쪽이다.

## Node에서 먼저 볼 것

Node는 Python/C 쪽과 멘탈 모델이 다르다. `process.stdout`과 `process.stderr`는 일반 stdio wrapper보다 **Node stream**에 가깝고, 최신 Node 문서는 POSIX에서 다음 차이를 직접 적는다.

- TTY는 synchronous write
- pipes/sockets는 asynchronous write

초보자용 번역은 이렇다.

| Node 코드/환경 | 흔한 관찰 |
|---|---|
| `console.log()` + TTY | 바로 보이는 것처럼 느껴지기 쉽다 |
| `console.log()` + pipe | write 완료가 event loop / receiving side timing 영향을 더 받는다 |
| `process.stdout.write("x")` 후 즉시 종료 | callback이나 drain을 안 기다리면 timing surprise가 커질 수 있다 |
| stdout/stderr separate pipes | child 안 코드 순서보다 parent merge 순서가 더 크게 보일 수 있다 |

Node에서 ordering surprise를 볼 때는 "line buffered냐 full buffered냐"보다 아래 질문이 더 실용적이다.

- `process.stdout.isTTY`, `process.stderr.isTTY`가 각각 무엇인가
- POSIX pipe라서 stdout/stderr write completion timing이 엇갈린 것 아닌가
- parent가 stdout/stderr를 따로 읽은 뒤 merge하고 있지 않은가

즉 Node child라면 **classic stdio buffering보다 sync/async write와 merge 지점**을 먼저 본다.

## runtime-wrapper 사용자를 위한 10초 판별

| child 언어 | 가장 먼저 확인할 것 | ordering surprise가 잘 생기는 모양 |
|---|---|---|
| Python | `-u`, `flush=True`, stdout이 pipe인지 | stdout은 몰리고 stderr는 먼저 보임 |
| Java | `println`인지, logger/appender가 async인지 | stdout/stderr보다 앱 logger가 늦게 도착 |
| Node | `isTTY`, separate pipes merge, `process.exit()` 타이밍 | pipe에서 stdout/stderr 도착 순서가 흔들림 |

이 표를 기억해 두면 wrapper 사용자가 "왜 Python은 stdout이 늦고, Java는 newline 여부가 중요하고, Node는 pipe에서 더 흔들리지?"를 한 번에 설명하기 쉽다.

## 왜 stdout/stderr 순서가 바뀌어 보이나

가장 흔한 예시는 이것이다.

```c
printf("stdout: start\n");
fprintf(stderr, "stderr: warning\n");
```

코드 순서는 stdout이 먼저다. 그런데 stdout이 pipe/file이라 full buffered 쪽으로 동작하고 stderr는 더 빨리 flush되면, 밖에서는 아래처럼 보일 수 있다.

```text
stderr: warning
stdout: start
```

타임라인으로 보면 이유가 단순해진다.

| 코드에서 한 일 | 실제로 바로 일어나는 일 | 바깥에서 보이는 순서 |
|---|---|---|
| `printf("stdout: start\n")` | stdout buffer에만 잠시 쌓일 수 있다 | 아직 안 보일 수 있다 |
| `fprintf(stderr, "stderr: warning\n")` | stderr 쪽 `write(2, ...)`가 더 빨리 나갈 수 있다 | stderr가 먼저 보인다 |
| `fflush(stdout)` 또는 `exit()` | 이제야 stdout 쪽 `write(1, ...)`가 나간다 | stdout이 나중에 보인다 |

즉 관찰 순서는 "소스 코드 줄 순서"가 아니라 **각 stream이 실제로 밖으로 나온 순서**다.

## fd wiring과 stdio buffering 빠른 비교

| 질문 | fd wiring 문제 | stdio buffering 문제 |
|---|---|---|
| "child stdout/stderr가 어디로 가나?" | `fd 1/2`가 terminal/pipe/file 중 무엇을 가리키는지 | 이미 연결된 목적지로 언제 byte를 밀어낼지 |
| 대표 API | `dup2()`, `adddup2()`, `addopen()`, shell `>` / `2>` | `fflush()`, `setvbuf()`, language unbuffered option |
| 고장 증상 | 출력이 아예 다른 곳으로 가거나 parent가 pipe를 잘못 읽는다 | 종료/flush 전까지 출력이 늦게 보인다 |
| 확인 감각 | `/proc/<pid>/fd/1`, `/proc/<pid>/fd/2`, spawn file actions | newline/flush/exit 후 갑자기 나오고 stderr가 먼저 보일 수 있다 |
| 관련 문서 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) | 이 문서 |

초보자에게 가장 중요한 분리는 이것이다.

> `dup2()`는 "목적지"를 바꾸고, `fflush()`는 "버퍼 안 byte를 지금 목적지로 밀어낸다."

## 합치는 위치가 다르면 보이는 순서도 달라진다

stdout/stderr를 "어디서" 합치느냐도 중요하다.

| 배치 | 무슨 일이 일어나나 | beginner 감각 |
|---|---|---|
| `cmd >out 2>err` | 애초에 파일이 둘이다 | 두 파일 사이의 전체 순서는 자동 보존되지 않는다 |
| `cmd >out 2>&1` | 둘 다 같은 목적지로 간다 | 그래도 stdout/stderr buffer flush 타이밍 차이는 남는다 |
| parent가 `stdout=PIPE`, `stderr=PIPE`로 따로 받고 나중에 합침 | parent가 두 pipe를 읽어 자기 규칙으로 merge한다 | 마지막 순서는 child 코드보다 parent reader timing 영향이 크다 |
| terminal이 stdout/stderr를 각각 받아 화면에 그림 | 화면에서는 한 줄 섞여 보여도 내부 경로는 둘이다 | "한 콘솔에 보인다"가 "하나의 stream이다"를 뜻하지는 않는다 |

특히 CI, IDE, test runner, language wrapper는 stdout/stderr를 별도 pipe로 받은 뒤 reader thread 두 개로 읽는 경우가 많다. 이 구조에서는 **각 pipe 안의 순서**만 비교적 유지되고, stdout과 stderr를 가로지르는 전체 순서는 parent가 어떻게 합쳤는지에 따라 달라질 수 있다.

`cmd >out 2>&1`와 `cmd 2>&1 >out` 자체가 왜 다른지는 buffering보다 shell redirection 적용 순서의 문제다. 그 차이는 [Shell Redirection Order Primer](./shell-redirection-order-primer.md)에서 따로 분리해 본다.

## 빠른 판별표

| 지금 보이는 현상 | 흔한 1차 원인 | 먼저 떠올릴 질문 |
|---|---|---|
| stderr는 바로 나오는데 stdout은 종료 때 몰려 나온다 | stdout만 pipe/file 기준 buffering | "stdout이 TTY가 아니라서 full buffered처럼 동작하나?" |
| `2>&1`로 합쳤는데도 stderr가 먼저 찍힌다 | 같은 목적지라도 stream별 flush 시점이 다름 | "둘이 같은 파일로 가는가"보다 "각 stream이 언제 write했나"를 봤나? |
| CI/IDE 콘솔에서 줄 순서가 매번 조금씩 다르다 | parent가 stdout/stderr를 별도 pipe로 읽고 merge | "child 안에서 합친 건가, parent가 나중에 합친 건가?" |
| 파일 두 개를 나중에 합쳐 봤더니 순서가 어색하다 | 애초에 경로가 둘이라 전역 순서가 없음 | "처음부터 한 stream으로 남겼어야 하나?" |

## 작은 예제

아래처럼 child가 진행 로그는 stdout, 경고는 stderr로 쓴다고 하자.

```c
printf("step 1\n");
fprintf(stderr, "warn: slow path\n");
printf("step 2\n");
```

관찰 결과는 배치에 따라 달라질 수 있다.

| 관찰 환경 | 보일 수 있는 결과 | 이유 |
|---|---|---|
| 터미널에서 직접 실행 | `step 1`, `warn`, `step 2`처럼 자연스럽게 보일 수 있다 | stdout이 line buffered라 newline마다 빨리 flush된다 |
| stdout만 pipe/file로 redirect | `warn`이 먼저 보이고 `step 1`, `step 2`가 나중에 몰릴 수 있다 | stdout buffer가 늦게 flush된다 |
| parent가 stdout/stderr를 따로 받아 merge | `warn`, `step 1`, `step 2` 또는 `step 1`, `warn`, `step 2`가 모두 가능하다 | 두 pipe의 도착 시간과 parent merge 정책이 개입한다 |

중요한 점은 "관찰된 순서가 조금 바뀌었다"가 꼭 scheduler 이상이나 shell bug를 뜻하지는 않는다는 것이다. 대부분은 **buffering 차이 + merge 지점 차이**로 설명된다.

## 어떻게 고칠지 고르는 기준

| 상황 | 먼저 할 일 | 이유 |
|---|---|---|
| 내가 child 코드를 고칠 수 있음 | 진행 로그 뒤 `fflush(stdout)` 또는 line/unbuffered 설정 | output timing 의도를 코드에 명시한다 |
| stdout/stderr의 시간 순서가 중요함 | child에서 line 단위 flush, timestamp, sequence id를 함께 남긴다 | 두 stream을 나중에 합치면 원래 코드 순서를 복원하기 어렵다 |
| stdout/stderr를 분리할 필요가 없음 | 처음부터 한쪽으로 merge하는 정책을 검토 | merge를 늦게 할수록 reorder 해석이 어려워진다 |
| child 코드를 못 고침 | GNU/Linux에서는 `stdbuf -oL` / `stdbuf -o0` 같은 wrapper를 검토 | 프로그램 바깥에서 stdout buffering 정책을 바꿀 수 있다 |
| CLI가 TTY일 때만 즉시 출력함 | pseudo-tty 사용을 검토하되 신중히 적용 | TTY로 보이면 line buffering/색상/progress bar 동작이 함께 바뀔 수 있다. 자세한 차이는 [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md) 참고 |
| 최종 결과만 필요함 | 굳이 unbuffered로 바꾸지 않고 종료까지 읽는다 | 즉시성이 필요 없으면 buffering은 성능에 도움 된다 |
| 출력이 아예 안 오고 EOF도 안 옴 | fd wiring/pipe end close 문제를 먼저 본다 | 이 경우는 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)의 `close()` / `CLOEXEC` 문제일 수 있다 |

언어별 옵션은 다르다. 예를 들어 Python은 `-u`나 `PYTHONUNBUFFERED=1`이 있고, Java는 `PrintWriter`의 auto-flush 여부나 logging framework appender 설정이 영향을 줄 수 있다. 핵심은 옵션 이름이 아니라 **"stdio/runtime buffer를 언제 flush할지"**다.

CI나 test runner처럼 parent가 stdout/stderr를 따로 읽고 나중에 transcript로 합치는 환경에서는, buffering 차이에 더해 **merge timing**까지 순서를 흔들 수 있다. 그 감각은 [CI Log Merge Behavior Primer](./ci-log-merge-behavior-primer.md)에서 이어서 본다.

## 자주 헷갈리는 포인트

### 1. `dup2()`가 늦게 적용된 것 아닌가요?

보통 아니다. `dup2()`나 file actions가 성공했다면 child가 새 프로그램을 시작할 때 fd 1/2는 이미 새 목적지를 향한다. 늦는 것은 fd 연결이 아니라 child의 `write()` 호출이다.

### 2. pipe가 newline을 기다리나요?

아니다. kernel pipe는 byte stream이다. newline을 특별히 기다리지 않는다. newline을 보고 flush할지 말지는 pipe 앞단의 stdio/runtime 정책이다.

### 3. stderr는 바로 보이는데 stdout만 늦는 이유는 뭔가요?

stderr는 에러 메시지를 잃지 않기 위해 unbuffered이거나 더 자주 flush되는 기본값을 쓰는 경우가 많다. 그래서 같은 child process 안에서도 `stderr` 로그가 `stdout` 로그보다 먼저 보일 수 있다.

### 4. `2>&1`로 합쳤는데도 순서가 달라질 수 있나요?

그럴 수 있다. `2>&1`는 stdout과 stderr의 목적지를 같게 만들 뿐, 이미 각 stream이 가진 buffering 차이까지 없애 주지는 않는다. 즉 "같은 파일/pipe로 간다"와 "코드 줄 순서대로 보인다"는 별개다.
`2>&1` 자체의 적용 순서가 왜 결과를 바꾸는지는 [Shell Redirection Order Primer](./shell-redirection-order-primer.md)를 보면 된다.

### 5. stdout/stderr 전체 순서를 정말 보존하려면 어떻게 하나요?

가장 단순한 방법은 **처음부터 한 stream으로 쓰는 것**이다. stdout/stderr를 분리한 채 나중에 합치면, 합치는 쪽은 "각 stream에 언제 도착했는가"만 알 수 있고 child 코드의 원래 실행 순서를 완전히 복원하지 못할 수 있다. 분리가 꼭 필요하면 line 단위 flush와 함께 timestamp나 sequence id를 남기는 편이 안전하다.

### 6. redirect한 파일에 로그가 늦게 생기면 `fsync()` 문제인가요?

먼저 stdio buffer를 봐야 한다. `fsync()`는 이미 kernel에 넘어간 file data를 storage 내구성 관점에서 다룬다. `printf()` 결과가 아직 `write()`로 넘어가지 않았다면 `fsync()` 이전 단계의 문제다. page cache / durability까지 이어서 보고 싶을 때만 [page cache, dirty writeback, fsync](./page-cache-dirty-writeback-fsync.md)로 내려가면 된다.

### 7. process가 비정상 종료하면 buffered stdout이 사라질 수 있나요?

그럴 수 있다. 정상 `exit()`는 보통 stdio buffer를 flush하지만, crash, `SIGKILL`, `_exit()` 같은 경로는 stdio flush를 건너뛸 수 있다. 즉시 필요한 진행 로그나 장애 로그는 stderr, explicit flush, logging framework flush 정책을 명확히 잡는 편이 안전하다.

## beginner 체크리스트

- fd 1/2가 어디로 연결됐는지와 stdout/stderr가 언제 flush되는지를 분리해서 생각한다.
- "stderr가 먼저 보인다"면 scheduler보다 stream별 buffering 차이를 먼저 떠올린다.
- "각각은 맞는데 합친 화면에서 순서가 다르다"면 merge 지점이 어디인지 확인한다.
- "종료할 때 한꺼번에 보인다"면 fd wiring보다 buffering을 먼저 의심한다.
- "아예 EOF가 안 온다"면 buffering보다 누가 pipe write end를 들고 있는지 먼저 본다.
- 파일 durability 문제로 가기 전에 `fflush()`/runtime flush가 있었는지 확인한다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`fd 배선은 맞는데 EOF가 안 오거나 redirect 자체가 헷갈린다"면: [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - "`PTY를 붙였을 때 왜 색상, prompt, progress bar까지 같이 바뀌는지"를 잇고 싶다면: [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
> - "`posix_spawn()` redirection을 child-side checklist로 다시 읽고 싶다면": [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

redirect는 "fd 1/2가 어디를 향하는가"이고 ordering은 "stdout/stderr가 언제 flush되어 어디서 merge됐는가"다. 순서가 바뀌어 보여도 먼저 buffering과 merge 경로를 의심한다.
