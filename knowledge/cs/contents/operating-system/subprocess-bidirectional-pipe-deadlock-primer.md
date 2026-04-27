# Bidirectional Pipe Deadlock Primer

> 한 줄 요약: `stdin=PIPE`와 `stdout=PIPE`를 함께 쓰면 parent와 child 사이에 작은 대기열이 두 개 생기고, parent의 read/write 순서가 어긋나면 서로 상대방을 기다리며 멈출 수 있다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) 다음에 읽는 beginner bridge다. `stdin=PIPE` + `stdout=PIPE` 조합에서 왜 "입력을 다 쓰고 나서 읽자" 또는 "출력을 먼저 읽자"가 막힐 수 있는지, pipe capacity와 EOF, `communicate()`-style API 정책으로 연결해 설명한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Subprocess Symptom First-Branch Guide](./subprocess-symptom-first-branch-guide.md)
- [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)
- [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
- [operating-system 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: operating-system-00060, subprocess symptom first branch guide, subprocess comparison table, bidirectional pipe deadlock primer, subprocess bidirectional pipe deadlock, bidirectional pipe mental model, two-queue eof mental model, stdin=pipe stdout=pipe deadlock, subprocess stdin stdout deadlock, two way pipe deadlock, parent write then read deadlock, parent read before close stdin deadlock, child blocked writing stdout stops reading stdin, beginner handoff box, subprocess bidirectional pipe deadlock primer basics

## Subprocess Primer Handoff

> **이 문서는 subprocess 입문 흐름의 3단계다**
>
> - 바로 앞 문서: [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md)에서 stdout/stderr drain 문제를 먼저 분리한다
> - 지금 문서의 질문: "`stdin=PIPE`까지 같이 쓰면 왜 read/write/close 순서가 엉키지?"
> - 다음 문서: [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)에서 이 ordering 감각을 `PIPE`, `close_fds`, `pass_fds` 옵션 이름으로 다시 번역한다

## 먼저 잡는 멘탈 모델

먼저 이것을 "작은 큐 두 개 + EOF 신호 하나"로 보면 된다.

```text
parent write()
  -> stdin pipe  -> child -> stdout pipe -> parent read()
parent close(stdin)
  -> EOF 전달     -> child가 입력 종료를 안다
```

여기서 중요한 점은 세 가지다.

- `stdin` pipe도, `stdout` pipe도 **무한하지 않다**
- child는 `stdout`에 막히면 더 이상 `stdin`을 읽지 못할 수 있다
- 어떤 child는 **EOF를 받아야** 비로소 출력을 내보낸다

즉 양방향 pipe에서는 "누가 언제 읽고, 누가 언제 쓰고, 누가 언제 닫는가"가 같이 맞아야 한다.
EOF 축만 따로 떼어 보고 싶다면 [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)에서 "write end가 열려 있어서 child가 계속 읽기 대기하는 경우"를 분리해 볼 수 있다.

## 두 가지 막힘을 먼저 분리한다

`stdin=PIPE` + `stdout=PIPE`에서 초보자가 자주 섞는 문제는 사실 두 종류다.

| child 성격 | parent가 잘못하기 쉬운 순서 | 왜 막히나 | 대표 예시 |
|---|---|---|---|
| 읽으면서 바로 쓰는 streaming/filter형 | 입력을 끝까지 다 쓴 뒤에야 stdout을 읽음 | child stdout pipe가 차면 child가 write에서 멈추고, 그 순간 child는 stdin도 덜 읽게 된다 | `cat`, `tr`, 압축/변환 filter |
| EOF를 받아야 결과를 내는 batch형 | stdout을 먼저 읽고 stdin close를 늦춤 | child는 "입력이 아직 안 끝났다"고 생각해 결과를 안 내고, parent는 출력이 오길 기다린다 | `sort`, 전체 입력을 모아 처리하는 parser |

핵심은 "pipe capacity"와 "EOF 필요 여부"가 동시에 있다는 점이다.

## deadlock 1. 입력을 다 쓰고 나서 읽으려는 패턴

아래 패턴은 작은 데이터에서는 우연히 통과할 수 있다.

```python
p = subprocess.Popen(
    ["cat"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
)

p.stdin.write(big_data)   # 여기서 막힐 수 있음
p.stdin.close()
out = p.stdout.read()
```

왜 막히는지 타임라인으로 보면 단순하다.

| 시점 | parent | child | 두 pipe 상태 |
|---|---|---|---|
| 1 | stdin pipe에 계속 쓴다 | stdin에서 읽고 stdout에 다시 쓴다 | 둘 다 조금씩 찬다 |
| 2 | 아직 stdout은 읽지 않는다 | stdout pipe에 계속 쓴다 | stdout pipe가 점점 찬다 |
| 3 | 여전히 stdin에 더 쓰려 한다 | stdout pipe가 가득 차 `write(stdout)`에서 block된다 | child가 더 이상 stdin을 읽지 못한다 |
| 4 | child가 stdin을 안 읽으니 parent `write(stdin)`도 block된다 | 이미 stdout write에서 block 중이다 | 서로 진행이 멈춘다 |

이 상황은 "child가 느리다"가 아니라 **양쪽 pipe가 모두 유한해서 생기는 순서 문제**다.

## deadlock 2. stdout을 먼저 읽고 stdin close를 미루는 패턴

이번에는 child가 EOF를 받아야 결과를 내는 경우다.

```python
p = subprocess.Popen(
    ["sort"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
)

p.stdin.write("b\na\n")
p.stdin.flush()
out = p.stdout.read()     # 여기서 기다릴 수 있음
p.stdin.close()
```

`sort` 같은 프로그램은 보통 "입력이 끝났다"는 신호, 즉 stdin EOF를 받아야 정렬 결과를 내보낸다.

```text
parent: stdout.read()로 결과를 먼저 기다림
child : 아직 stdin EOF를 못 받아서 계속 입력 대기
parent: p.stdin.close()까지 못 감
```

이번에는 pipe capacity가 아니라 **EOF 전달 순서**가 막힌다.

즉 양방향 pipe 문제는 항상 "버퍼가 찼다"만이 아니라, 어떤 child는 "입력이 끝났는지"까지 기다린다는 점을 같이 봐야 한다.

## 왜 `stdin=PIPE` + `stdout=PIPE`가 특히 위험한가

한 방향 pipe만 있으면 보통 parent가 "읽기만" 또는 "쓰기만" 하면 된다.
하지만 두 방향 pipe를 동시에 만들면 parent는 아래 세 가지를 한 흐름으로 묶어야 한다.

1. child stdin에 입력 쓰기
2. child stdout을 실행 중에 비우기
3. 입력을 다 썼다면 stdin을 닫아 EOF 전달하기

이 셋 중 하나라도 늦어지면 다른 둘이 기다릴 수 있다.

| parent가 놓치는 것 | child 입장에서 보이는 현상 |
|---|---|
| stdout을 안 읽음 | stdout pipe가 차서 `write()`에서 멈춘다 |
| stdin을 안 닫음 | EOF가 오지 않아 결과 생성 단계로 못 간다 |
| stdin만 쓰고 stdout은 나중에 읽음 | child가 stdout에 막히며 stdin 소비도 멈출 수 있다 |
| stdout만 읽고 stdin 쓰기/닫기를 안 함 | child가 "아직 입력이 덜 왔다"고 보고 결과를 안 낼 수 있다 |

## `communicate()`-style API가 하는 일

`communicate()`의 핵심은 "편한 함수 하나"가 아니라 **안전한 I/O 정책 묶음**이다.

- parent가 child 실행 중 stdout/stderr를 drain한다
- 입력이 있으면 child stdin으로 보내고, 다 보내면 닫는다
- 입출력 정리가 끝난 뒤 child 종료를 기다린다

즉 `communicate(input=data)`는 보통 아래 순서를 runtime이 대신 안전하게 잡아 준다.

```text
입력 보내기
  + 출력 drain하기
  + 입력 종료 시 stdin close
  + child exit wait
```

그래서 beginner-safe 기본값은 대개 이렇다.

```python
completed = subprocess.run(
    ["sort"],
    input=b"b\na\n",
    capture_output=True,
)
```

또는

```python
out, err = p.communicate(input=big_data)
```

API 이름은 언어마다 달라도, 안전한 정책은 비슷하다.

## parent read/write ordering 빠른 선택표

| 원하는 것 | 나쁜 기본형 | beginner-safe 기본형 |
|---|---|---|
| one-shot 입력을 보내고 결과 전체를 받기 | `write()`를 끝까지 한 뒤 `read()` | `communicate(input=...)` 또는 동등한 wrapper |
| child가 stdout을 많이 낼 수 있음 | stdin만 밀어 넣고 stdout은 마지막에 읽기 | 입력과 출력 drain을 동시에 처리 |
| child가 EOF 뒤에만 결과를 냄 | `read()` 먼저 호출하고 stdin close를 늦춤 | 입력 완료 즉시 stdin close, 또는 `communicate()` 사용 |
| 실시간 request/response 대화형 프로토콜 | blocking `write()`와 `read()`를 한 thread에서 순진하게 교대로 호출 | reader/writer를 분리한 thread, selector, event loop, socketpair 등으로 설계 |
| stdout이 필요 없음 | 습관적으로 `stdout=PIPE` | 파일, `/dev/null`, 상위 logger 등으로 명시 redirect |

## 언제 pipe capacity를 먼저 떠올리나

아래 증상이라면 pipe capacity와 ordering을 먼저 떠올리는 편이 좋다.

- 입력이 작을 때는 되는데 큰 payload에서만 멈춘다
- child가 filter처럼 입력을 읽으며 출력을 계속 낸다
- parent stack trace를 보면 `write()` 쪽에서 멈춰 있다
- child를 보면 `write(stdout)` 쪽에서 잠든 것처럼 보인다

반대로 아래라면 EOF 문제를 먼저 떠올린다.

- 작은 입력인데도 결과가 안 나온다
- child가 batch 처리형이라 입력 종료 뒤에만 결과를 낸다
- parent가 stdin을 아직 닫지 않았다

## 흔한 오해

### 1. pipe 크기를 키우면 해결되나요?

근본 해결은 아니다. 더 큰 pipe는 막히기 전 시간을 조금 벌어 줄 뿐이다. parent ordering이 틀리면 결국 다시 찬다.

### 2. newline을 보내면 child가 결과를 주지 않나요?

newline은 EOF가 아니다. 어떤 child는 줄 단위로 처리하지만, 어떤 child는 stdin close까지 기다린다.

### 3. `stdin.write()` 후 `flush()`만 하면 충분한가요?

아니다. `flush()`는 parent 쪽 runtime buffer를 pipe로 밀어내는 일이고, child에게 "입력이 끝났다"를 알리는 것은 `close()`다.

### 4. `stdout=PIPE`만 조심하면 되나요?

아니다. `stdin=PIPE`와 같이 쓰면 "읽지 않아서 생기는 backpressure"와 "닫지 않아서 생기는 EOF 대기"가 함께 들어온다.

### 5. `stderr=PIPE`까지 같이 잡으면 어떤가요?

그때는 queue가 하나 더 늘어난다. `communicate()`-style API가 더 유리한 이유가 여기에 있다. stdout만 읽고 stderr를 방치해도 다시 비슷한 막힘이 생길 수 있다.

## Self-check (자가 점검 4문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. 양방향 pipe에서 "쓰기 막힘(backpressure)"과 "EOF 대기"를 서로 다른 deadlock 축으로 구분해 설명할 수 있는가?
   힌트: 하나는 버퍼가 꽉 차서 못 쓰는 문제고, 다른 하나는 상대가 끝났다는 신호가 안 와서 계속 기다리는 문제다.
2. child가 EOF 뒤에만 응답하는 타입일 때 parent가 반드시 해야 할 동작(`stdin` close)을 떠올릴 수 있는가?
   힌트: 데이터를 다 보냈다면 write end를 닫아 "이제 입력 끝"이라는 신호를 child에 줘야 한다.
3. one-shot request/response에서는 수동 순서 제어보다 `communicate()`-style API가 왜 안전한지 말할 수 있는가?
   힌트: 쓰기와 읽기, 필요하면 종료 대기까지 한 묶음으로 처리해 파이프 가득 참과 순서 실수를 줄여 준다.
4. `stderr=PIPE`를 함께 사용할 때 drain 대상이 늘어나며 ordering 위험이 커진다는 점을 설명할 수 있는가?
   힌트: stdout만 보던 코드가 stderr까지 따로 막힐 수 있어, 두 스트림을 함께 비우는 전략이 필요하다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`stdin=PIPE`, `stdout=PIPE`, `stderr=PIPE` 옵션이 실제로 뭘 만드는지"를 보고 싶으면: [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
> - "`flush()`까지 했는데 왜 child가 EOF를 못 받아서 계속 기다리지?"를 따로 떼어 보려면: [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)
> - "막힘이 deadlock이 아니라 buffering 착시인가?"를 구분하려면: [Stdio Buffering After Redirect](./stdio-buffering-after-redirect.md)
> - "EOF가 왜 안 오지, 누가 fd를 아직 들고 있지?"를 다시 잡으려면: [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - 운영체제 입문 primer 묶음으로 돌아가려면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

`stdin=PIPE` + `stdout=PIPE`는 "두 방향으로 무한히 대화할 수 있다"가 아니라 "작은 큐 두 개와 EOF 신호를 조심해서 다뤄야 한다"는 뜻이다. 입력 쓰기, 출력 읽기, stdin close를 한 정책으로 묶는 것이 핵심이다.
