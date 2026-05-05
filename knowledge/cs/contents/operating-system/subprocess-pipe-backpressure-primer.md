---
schema_version: 3
title: Subprocess Pipe Backpressure Primer
concept_id: operating-system/subprocess-pipe-backpressure-primer
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- subprocess-wait-before-read
- stdout-stderr-drain-order
aliases:
- subprocess pipe backpressure primer
- subprocess pipe backpressure
- pipe backpressure mental model
- child blocks writing stdout pipe
- parent wait before read deadlock
- sequential stdout stderr read deadlock
- stdout pipe full
- stderr pipe full
- child stuck in write syscall
- write blocks when pipe full
- pipe backpressure 처음 배우는데
- stdout stderr 안 읽으면 멈춤
- subprocess pipe hang basics
- subprocess pipe backpressure primer basics
- subprocess pipe backpressure primer beginner
symptoms:
- 출력이 많을 때만 subprocess가 안 끝나요
- wait는 끝나지 않는데 child 로그도 안 늘어요
- stdout stderr를 나중에 읽으면 왜 멈추죠
intents:
- definition
- troubleshooting
prerequisites:
- operating-system/process-lifecycle-and-ipc-basics
- operating-system/subprocess-fd-hygiene-basics
next_docs:
- operating-system/subprocess-bidirectional-pipe-deadlock-primer
- operating-system/popen-runtime-wrapper-mapping
linked_paths:
- contents/operating-system/subprocess-symptom-first-branch-guide.md
- contents/operating-system/subprocess-fd-hygiene-basics.md
- contents/operating-system/broken-pipe-sigpipe-bridge.md
- contents/operating-system/subprocess-bidirectional-pipe-deadlock-primer.md
- contents/operating-system/stdio-buffering-after-redirect.md
- contents/operating-system/process-lifecycle-and-ipc-basics.md
- contents/operating-system/pipe-socketpair-eventfd-memfd-ipc-selection.md
- contents/network/http-response-compression-buffering-streaming-tradeoffs.md
confusable_with:
- operating-system/subprocess-bidirectional-pipe-deadlock-primer
- operating-system/subprocess-stdin-eof-primer
forbidden_neighbors:
- contents/operating-system/subprocess-bidirectional-pipe-deadlock-primer.md
- contents/operating-system/subprocess-stdin-eof-primer.md
- contents/operating-system/stdio-buffering-after-redirect.md
expected_queries:
- subprocess 출력이 많을 때만 멈추는 이유가 뭐야?
- wait만 했는데 child가 안 끝나요
- stdout pipe가 차면 왜 write에서 막혀?
- stderr를 따로 읽다가 hang 나는 구조를 처음 설명해줘
- subprocess 로그가 안 늘고 종료도 안 되면 어디부터 봐?
contextual_chunk_prefix: |
  이 문서는 subprocess 출력을 pipe로 받는 순간 왜 작은 대기열이 생기고
  parent가 제때 비우지 않으면 child가 write 안에서 멈추는지 처음 잡는
  primer다. 출력이 많을 때만 멈춤, wait만 하고 read를 안 함, child 로그는
  멈췄는데 프로세스가 안 끝남, stdout stderr를 순서대로 읽다가 hang, 출력
  통로가 막혀 child가 더 못 내보냄 같은 자연어 표현이 본 문서의
  backpressure 원인에 매핑된다.
---

# Subprocess Pipe Backpressure Primer

> 한 줄 요약: child stdout/stderr를 pipe로 받으면 pipe는 작은 대기열이 되고, parent가 제때 읽지 않으면 대기열이 차서 child가 `write()` 안에서 멈출 수 있다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) 다음에 읽는 beginner bridge다. `stdout=PIPE`, `stderr=PIPE`, `popen()`, `ProcessBuilder`처럼 child 출력을 parent가 받는 구조에서 "왜 wait만 했는데 child가 안 끝나지?"를 pipe backpressure 관점으로 설명한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Subprocess Symptom First-Branch Guide](./subprocess-symptom-first-branch-guide.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [Broken Pipe and `SIGPIPE` Bridge](./broken-pipe-sigpipe-bridge.md)
- [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- [동기/비동기와 블로킹/논블로킹 기초](./sync-async-blocking-nonblocking-basics.md)
- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [signals, process supervision](./signals-process-supervision.md)
- [HTTP Response Compression, Buffering, Streaming Trade-offs](../network/http-response-compression-buffering-streaming-tradeoffs.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: subprocess pipe backpressure primer, subprocess pipe backpressure, pipe backpressure mental model, child blocks writing stdout pipe, parent wait before read deadlock, sequential stdout stderr read deadlock, stdout pipe full, stderr pipe full, child stuck in write syscall, write blocks when pipe full, pipe backpressure 처음 배우는데, stdout stderr 안 읽으면 멈춤, subprocess pipe hang basics, subprocess pipe backpressure primer basics, subprocess pipe backpressure primer beginner

## Subprocess Primer Handoff

> **이 문서는 subprocess 입문 흐름의 2단계다**
>
> - 바로 앞 문서: [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)에서 "무엇을 남기고 무엇을 닫는가"를 먼저 고정한다
> - 지금 문서의 질문: "배선은 맞는데 왜 child가 `write()`에서 멈추지?"
> - 다음 문서: [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)에서 `stdin=PIPE`까지 붙을 때 read/write/close 순서 문제를 잇는다
> - 옆가지 문서: [Broken Pipe and `SIGPIPE` Bridge](./broken-pipe-sigpipe-bridge.md)에서 "reader가 너무 느린 것"이 아니라 "reader가 먼저 사라진 것"일 때 writer가 어떻게 실패하는지 따로 본다

## 먼저 잡는 멘탈 모델

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

## 출력 지연 vs 실제 hang 빠른 비교

| 관찰 | stdio buffering 지연 | pipe backpressure hang |
|---|---|---|
| 눈에 보이는 증상 | 로그가 늦게 나오거나 종료 때 몰린다 | 로그가 늘지 않고 `wait()`도 끝나지 않는다 |
| child가 있는 위치 | 아직 stdio/runtime buffer 앞단 | kernel pipe가 꽉 차서 `write()` 안 |
| parent가 지금 안 하는 일 | merge timing을 구분하지 않음 | stdout/stderr drain을 실행 중 하지 않음 |
| 먼저 시도할 것 | `flush`, unbuffered 옵션, TTY 여부 확인 | `communicate()`나 동시 drain으로 구조 변경 |
| 이어서 볼 문서 | [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md) | 이 문서 |

## 10초 타임라인: parent가 늦게 읽으면 어디서 멈추나

| 시점 | child | kernel pipe buffer | parent |
|---|---|---|---|
| 1 | 로그를 조금 `write()`한다 | 아직 빈 공간이 있다 | 아직 다른 일을 하거나 종료만 기다린다 |
| 2 | 계속 로그를 쓴다 | 점점 찬다 | 여전히 읽지 않는다 |
| 3 | 다시 `write()`를 호출한다 | 이미 가득 차 있다 | 아직 `read()`를 하지 않는다 |
| 4 | kernel이 child를 잠재우고 공간이 날 때까지 기다리게 한다 | parent가 읽어야만 다시 비워진다 | `wait()`만 하고 있으면 진전이 없다 |

여기서 pipe capacity는 "조금 늦게 읽어도 되는 짧은 시간 예산"에 가깝다.
잠깐의 속도 차는 흡수하지만, parent가 계속 안 읽는 설계를 안전하게 만들어 주지는 않는다.

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

## parent 설계를 한 줄로 고르면

| parent 목표 | 흔한 나쁜 패턴 | beginner-safe 기본형 |
|---|---|---|
| stdout/stderr 둘 다 캡처 | `wait()` 후 `read()` | `communicate()` 또는 동시 drain |
| stdout만 중요 | `stdout=PIPE`, `stderr=PIPE` 후 stderr 방치 | `stderr=STDOUT`, 파일, `/dev/null` 중 하나로 명시 |
| 긴 실행 중 실시간 로그 | 종료 후 한꺼번에 읽기 | reader thread / event loop로 실행 중 drain |
| 출력이 매우 큼 | pipe에만 쌓아 두고 마지막에 수집 | 파일 redirect, bounded capture, rolling log |

핵심은 API 이름보다 parent의 소비 정책이다.
**"child가 쓰는 속도보다 늦지 않게 읽을 것"**이 지켜지지 않으면 wrapper가 달라도 같은 종류의 멈춤이 생긴다.

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

## 순차 drain anti-pattern: `stdout`을 끝까지 읽고 나서 `stderr`를 읽는 경우

여기서 초보자가 자주 놓치는 점이 하나 더 있다.
`wait()`를 먼저 안 해도, 아래처럼 **한 stream을 EOF까지 다 읽고 나서 다른 stream을 읽는 코드**는 멈출 수 있다.

```python
p = subprocess.Popen(
    ["some-command"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

out = p.stdout.read()   # stdout EOF를 끝까지 기다림
err = p.stderr.read()   # stderr는 그 다음에야 읽음
```

겉으로 보면 "그래도 읽고 있잖아"라고 생각하기 쉽다.
하지만 실제로는 `stdout`만 읽는 동안 `stderr`는 전혀 비우지 않는다.

```text
parent: stdout EOF가 올 때까지 p.stdout.read()에서 대기
child : stdout도 쓰고 stderr도 씀
stderr pipe: parent가 안 읽어서 점점 참
child : write(2, ...)에서 block
child : 막혔으니 stdout close/exit까지 못 감
parent: stdout EOF가 안 와서 계속 p.stdout.read()에 머묾
```

핵심은 이것이다.

- parent는 `stdout`을 읽고 있지만 `stderr`는 안 읽는다
- child는 `stderr`가 막히는 순간 더 진행하지 못한다
- child가 더 진행하지 못하면 `stdout`도 닫히지 않는다
- 그래서 parent의 `stdout.read()`가 끝나지 않는다

즉 이 패턴은 "`wait()`를 먼저 해서 생긴 문제"가 아니라, **두 pipe를 동시에 drain하지 못해서 생긴 문제**다.

| 패턴 | 왜 초보자가 안전해 보인다고 느끼나 | 실제 막히는 이유 |
|---|---|---|
| `wait()` 후 `stdout.read()`, `stderr.read()` | "프로세스만 끝나면 읽으면 되겠지" | child가 pipe full 때문에 끝나지 못한다 |
| `stdout.read()` 후 `stderr.read()` | "그래도 지금 읽고 있으니 wait-first보단 낫겠지" | 읽는 동안 다른 pipe가 차서 child가 멈추고, 첫 번째 `read()`도 EOF를 못 본다 |
| stdout/stderr 동시 drain | 두 stream을 번갈아 비워 준다 | child가 한쪽 pipe full로 멈출 가능성을 줄인다 |

그래서 beginner-safe 기본 규칙은 둘 중 하나다.

- stdout/stderr를 함께 수집해야 하면 `communicate()` 같은 동시 drain API를 쓴다
- 한쪽이 정말 필요 없으면 애초에 그쪽을 `PIPE`로 만들지 않는다

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

`stdin=PIPE`와 `stdout=PIPE`를 함께 잡은 양방향 통신에서는 여기에 "언제 stdin을 닫아 EOF를 줄 것인가"가 추가된다. 그 ordering 문제는 [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)에서 따로 분리해 볼 수 있다.

## 흔한 오해

### 1. child가 멈춘 것은 scheduler 문제인가요?

대부분 아니다. child가 `write()`에서 block되면 scheduler는 그 프로세스를 runnable로 보지 않을 수 있다. CPU starvation이 아니라 pipe 공간을 기다리는 상태다.

### 2. newline을 찍으면 pipe가 자동으로 비워지나요?

아니다. newline은 kernel pipe를 비우지 않는다. newline 때문에 child runtime이 flush할 수는 있지만, flush 뒤 pipe가 가득 차 있으면 `write()`가 막힐 수 있다.

### 3. `CLOEXEC`나 fd close만 잘하면 backpressure가 사라지나요?

아니다. `CLOEXEC`와 `close()`는 fd leak와 EOF 문제를 줄인다. 하지만 parent가 살아 있는 동안 stdout/stderr pipe를 안 읽으면 pipe buffer는 여전히 찰 수 있다.

### 4. nonblocking으로 만들면 해결인가요?

자동 해결은 아니다. nonblocking fd에서는 pipe가 차면 `write()`가 `EAGAIN`으로 실패할 수 있다. 그러면 child나 parent가 retry, polling, buffering 정책을 직접 가져야 한다. beginner subprocess capture에서는 보통 parent가 drain 구조를 제대로 잡는 것이 먼저다.

### 5. pipe 크기를 키우면 해결인가요?

근본 해결은 아니다. 더 큰 pipe는 parent가 늦게 읽을 수 있는 시간을 조금 늘릴 뿐이다. parent가 계속 안 읽거나 한쪽 stream만 읽는 설계라면 언젠가는 다시 찰 수 있다.

### 6. stderr는 양이 작으니 나중에 읽어도 되나요?

장애 상황에서는 stderr가 가장 많이 나올 수 있다. stack trace, warning loop, verbose error log가 stderr pipe를 먼저 채우는 경우가 흔하다.

## 빠른 진단 감각

subprocess가 "가끔 안 끝난다"면 아래 순서로 보면 좋다.

1. `stdout=PIPE` 또는 `stderr=PIPE`를 만들고도 실행 중 읽지 않는가
2. parent가 `wait()`를 먼저 호출하고 `read()`를 나중에 하는가
3. stdout은 drain하지만 stderr는 방치하는가
4. child가 많은 로그를 쓰는 실패 경로에서만 멈추는가
5. `strace` 같은 도구에서 child가 `write(1, ...)` 또는 `write(2, ...)`에 오래 머무는가

반대로 child가 이미 끝났는데 parent read가 EOF를 못 받는다면 backpressure보다 "누가 write end를 아직 들고 있는가"가 먼저다. 그 경우는 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)의 pipe end close 문제로 돌아가면 된다.

## Self-check (자가 점검 4문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. "`wait()` 먼저, `read()` 나중" 패턴이 왜 deadlock을 만들 수 있는지 pipe capacity 관점으로 설명할 수 있는가?
   힌트: child 출력 버퍼가 가득 차면 child는 쓰기에서 멈추고, parent는 종료만 기다리며 서로 막힐 수 있다.
2. stdout/stderr를 둘 다 `PIPE`로 잡았을 때 "한쪽만 읽는 코드"가 왜 막힘을 만들 수 있는지 말할 수 있는가?
   힌트: 읽지 않는 다른 파이프가 먼저 꽉 차면 child 전체가 진행을 못 해 한쪽만 drain해도 부족하다.
3. `CLOEXEC`/`close()` 정리와 backpressure 해결이 서로 다른 축이라는 점을 구분할 수 있는가?
   힌트: 전자는 누가 fd를 쥐고 있는지 문제고, 후자는 pipe 용량과 소비 속도 문제라 원인이 다르다.
4. "실시간 로그가 필요한 경우"와 "최종 결과만 필요한 경우"에 parent drain 전략을 다르게 고를 수 있는가?
   힌트: 실시간이면 계속 읽는 루프가 필요하고, 최종 결과만 보면 되면 `communicate()` 같은 일괄 API가 단순하다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`stdin=PIPE`까지 같이 쓰면 왜 더 쉽게 막히지?"가 궁금하면: [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md)
> - "reader가 없어졌을 때는 왜 block이 아니라 `SIGPIPE`/`broken pipe`가 나오지?"를 보려면: [Broken Pipe and `SIGPIPE` Bridge](./broken-pipe-sigpipe-bridge.md)
> - "wrapper 옵션이 실제 fd/pipe 작업으로 어떻게 번역되지?"를 보고 싶으면: [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
> - "출력이 늦는 이유가 pipe full이 아니라 buffering인가?"를 구분하려면: [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
> - 운영체제 입문 primer 묶음으로 돌아가려면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

subprocess output pipe는 무한 로그 저장소가 아니라 작은 kernel buffer다. parent가 child 실행 중 stdout/stderr를 drain하지 않으면 child는 출력하다가 `write()`에서 멈출 수 있으므로, capture 코드는 "read와 wait를 함께 설계"해야 한다.
