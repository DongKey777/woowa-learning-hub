# `/proc/<pid>/status` Signal Fields Debugging Primer

> 한 줄 요약: `/proc/<pid>/status`의 `SigBlk`, `SigIgn`, `SigCgt`, `SigPnd`는 "이 프로세스가 signal을 막고 있는지, 무시하는지, handler를 잡았는지, 아직 처리되지 않은 signal이 있는지"를 한 번에 좁혀 주는 1차 현장 디버깅 표지판이다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md) 다음에 읽는 beginner bridge다. "`SIGINT`가 안 먹는데 block인가 ignore인가?" 같은 질문을 `/proc` 출력으로 바로 분기하는 입문용 가이드다.

**난이도: 🟢 Beginner**

관련 문서:

- [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md)
- [signals, process supervision](./signals-process-supervision.md)
- [Broken Pipe and `SIGPIPE` Bridge](./broken-pipe-sigpipe-bridge.md)
- [SIGCHLD Ignore vs `waitpid()` Bridge](./sigchld-ignore-vs-waitpid-bridge.md)
- [Session vs Process Group Primer](./session-vs-process-group-primer.md)
- [container PID 1, SIGTERM, zombie reaping basics](./container-pid-1-sigterm-zombie-reaping-basics.md)
- [operating-system 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: operating-system-00065, /proc pid status signal fields primer, /proc/<pid>/status signal debug, SigBlk SigIgn SigCgt SigPnd, blocked vs ignored signal debug, procfs signal mask disposition, signal fields beginner, signal triage primer, SigBlk meaning, SigIgn meaning, SigCgt meaning, SigPnd meaning, signal pending bitmap, blocked signal pending, ignored signal proc status, custom handler proc status, grep SigBlk SigIgn SigCgt SigPnd, proc status signal diagnosis, /proc status 시그널 필드, 시그널 block ignore 구분, 시그널 pending 진단, beginner handoff box, primer handoff box

## 먼저 잡는 멘탈 모델

signal이 이상하게 보일 때 초보자는 먼저 질문을 네 개로 나누면 된다.

| 질문 | `/proc/<pid>/status` 필드 | 초보자용 감각 |
|---|---|---|
| 지금 막아 둔 signal이 있나 | `SigBlk` | 문 앞에 잠깐 세워 둠 |
| 아예 무시하는 signal이 있나 | `SigIgn` | 와도 버림 |
| custom handler를 잡은 signal이 있나 | `SigCgt` | 오면 프로그램 코드가 받음 |
| 이미 왔는데 아직 처리 안 된 signal이 있나 | `SigPnd` | 문 앞 대기열 |

핵심은 이것이다.

- `SigBlk`는 blocked mask다.
- `SigIgn`는 ignored disposition이다.
- `SigCgt`는 caught disposition, 즉 handler 설치 여부다.
- `SigPnd`는 pending 상태다.

그래서 "`signal이 안 먹는다`"는 한 문장만으로는 부족하다.
안 먹는 이유가 block인지, ignore인지, handler 동작인지, pending 대기인지 나눠 봐야 한다.

## 가장 먼저 보는 명령

```bash
grep -E 'SigPnd|ShdPnd|SigBlk|SigIgn|SigCgt' /proc/<pid>/status
```

예시 출력:

```text
SigPnd: 0000000000000000
ShdPnd: 0000000000000000
SigBlk: 0000000000000002
SigIgn: 0000000000001000
SigCgt: 0000000000004000
```

이 값들은 보통 hex bitmap이다.
"어느 bit가 어느 signal인가"까지 바로 외울 필요는 없다. beginner 단계에서는 먼저 **같은 signal이 여러 칸에 동시에 보이는가**를 본다.

## 필드별로 아주 짧게 보기

| 필드 | 뜻 | 디버깅에서 바로 읽는 질문 |
|---|---|---|
| `SigBlk` | 현재 blocked된 signal mask | "지금 delivery를 막았나?" |
| `SigIgn` | ignore disposition인 signal | "받아도 그냥 버리나?" |
| `SigCgt` | user handler가 잡은 signal | "기본 동작 대신 프로그램 코드가 받나?" |
| `SigPnd` | 이 thread에 pending인 signal | "이미 왔는데 아직 못 처리했나?" |

보너스로 같이 보이는 `ShdPnd`는 process-wide pending 쪽이다.
beginner는 우선 `SigPnd`와 `ShdPnd`를 묶어서 "pending이 있나 없나"를 본 뒤, 필요할 때만 thread/process 차이로 내려가면 충분하다.

## 예제 1: `Ctrl-C`가 안 먹을 때 block인지 ignore인지 가르기

상황:

- foreground process가 `Ctrl-C`에 바로 안 죽는다.
- 초보자는 "`SIGINT`를 무시하나 보다"라고 생각하기 쉽다.

먼저 `/proc/<pid>/status`를 본다.

### 경우 A: `SigBlk`에 `SIGINT` bit가 있다

```text
SigPnd: 0000000000000002
SigBlk: 0000000000000002
SigIgn: 0000000000000000
SigCgt: 0000000000000000
```

읽는 법:

- `SIGINT`가 blocked돼 있다
- 이미 들어온 `SIGINT`가 pending으로 쌓였을 수 있다
- ignore는 아니다

초보자용 해석:

> "신호를 못 받은 게 아니라, 받지 못하게 막아 둔 상태다."

이 경우 unblock되면 나중에 처리될 수 있다.

### 경우 B: `SigIgn`에 `SIGINT` bit가 있다

```text
SigPnd: 0000000000000000
SigBlk: 0000000000000000
SigIgn: 0000000000000002
SigCgt: 0000000000000000
```

읽는 법:

- block은 아니다
- `SIGINT`를 ignore disposition으로 두고 있다
- pending으로 쌓이지 않는 쪽으로 보는 게 맞다

초보자용 해석:

> "문을 잠근 게 아니라, 벨이 와도 아예 무시한다."

이 경우 unblock으로 해결되지 않는다. disposition을 바꿔야 한다.

## 예제 2: `SIGTERM`이 안 죽고 대기만 하는 것처럼 보일 때

상황:

- 서비스에 `kill -TERM <pid>`를 보냈다
- 바로 종료되지 않는다

다음처럼 보일 수 있다.

```text
SigPnd: 0000000000004000
SigBlk: 0000000000004000
SigIgn: 0000000000000000
SigCgt: 0000000000000000
```

이 조합은 beginner에게 아주 중요하다.

- 같은 signal이 `SigBlk`와 `SigPnd`에 같이 보인다
- 즉 "왔다" + "그런데 지금은 막혀 있다"는 뜻이다

이때는 "`kill`이 안 갔다"가 아니라 **갔는데 delivery가 미뤄진 상태**를 먼저 의심해야 한다.

## 예제 3: `SIGPIPE`는 왜 조용히 사라지나

상황:

- pipe/socket 쓰기에서 상대가 끊겼다
- 보통은 `SIGPIPE`를 떠올리는데 프로세스가 죽지 않는다

`/proc/<pid>/status`가 다음처럼 보일 수 있다.

```text
SigPnd: 0000000000000000
SigBlk: 0000000000000000
SigIgn: 0000000000001000
SigCgt: 0000000000000000
```

이 경우 beginner 해석은 간단하다.

- `SIGPIPE`를 ignore하고 있다
- 그래서 기본 종료 동작이 안 일어난다
- 대신 write 쪽에서 `EPIPE` 같은 에러 경로를 보게 될 가능성이 크다

즉 signal 문제처럼 보였지만, 실제 애플리케이션 증상은 "조용한 write 실패"로 나타날 수 있다.

## 예제 4: handler가 있어서 안 죽는 것처럼 보일 때

상황:

- `SIGTERM`을 보내도 즉시 종료되지 않는다
- block도 ignore도 아닌 것 같다

```text
SigPnd: 0000000000000000
SigBlk: 0000000000000000
SigIgn: 0000000000000000
SigCgt: 0000000000004000
```

이 조합은 보통 이렇게 읽는다.

- 그 signal에 custom handler가 설치돼 있다
- 기본 종료 대신 프로그램 코드가 먼저 실행된다

초보자용 감각:

> "신호를 못 받은 게 아니라, 받았을 때 할 일을 프로그램이 바꿔 놓았다."

이 경우는 graceful shutdown, cleanup, log flush 같은 정상 설계일 수 있다.

## 가장 자주 하는 오해

- `SigBlk`가 켜져 있으면 ignore라고 단정하면 안 된다. block은 "지금만 보류"이고 ignore는 "와도 버림"이다.
- `SigPnd`만 보고 "signal handler가 이미 돌았다"라고 생각하면 안 된다. pending은 아직 처리 안 된 상태다.
- `SigCgt`가 있으면 반드시 종료가 안 되는 것은 아니다. handler 안에서 결국 종료할 수도 있다.
- `SigIgn`가 있으면 unblock으로 해결되지 않는다. disposition을 바꾸는 문제다.
- `SigPnd`가 0이어도 signal 문제가 없다는 뜻은 아니다. 이미 처리됐거나, ignore되어 쌓이지 않았거나, 다른 thread/process 쪽 pending일 수 있다.

## 빠른 분기표

| 보이는 조합 | 먼저 드는 해석 | 다음 질문 |
|---|---|---|
| `SigBlk`만 켜짐 | 막아 둠 | 언제 unblock되나 |
| `SigIgn`만 켜짐 | 무시함 | 왜 ignore로 설정했나 |
| `SigCgt`만 켜짐 | handler 있음 | handler가 무엇을 하나 |
| `SigBlk` + `SigPnd` | 왔지만 막혀 대기 | 왜 unblock이 안 되나 |
| `SigIgn` + 증상 지속 | signal보다 앱 에러 경로 가능성 | `EINTR`, `EPIPE`, 종료 정책을 보나 |

## bit를 실제 signal 이름으로 잇는 최소 팁

초보자는 먼저 "관심 있는 signal 하나"만 확인하면 된다.

- `SIGINT`가 궁금하면 `Ctrl-C` 문제로 본다
- `SIGTERM`이 궁금하면 graceful shutdown 문제로 본다
- `SIGPIPE`가 궁금하면 pipe/socket write 실패 문제로 본다
- `SIGCHLD`가 궁금하면 child reaping 문제로 본다

정확한 번호 매핑이 필요하면 다음처럼 현재 시스템 signal 목록을 같이 본다.

```bash
kill -l
```

다만 이 문서의 핵심은 bit 전체 해독이 아니라, **`SigBlk`/`SigIgn`/`SigCgt`/`SigPnd`의 역할을 먼저 분리하는 것**이다.

## 꼬리질문

> Q: `SigBlk`와 `SigIgn`는 무엇이 가장 다른가요?
> 핵심: `SigBlk`는 나중에 처리될 수 있지만, `SigIgn`는 전달돼도 버린다.

> Q: `SigBlk`와 `SigPnd`에 같은 signal이 같이 보이면 무슨 뜻인가요?
> 핵심: signal은 이미 왔지만 지금은 막혀 있어서 대기 중이라는 뜻이다.

> Q: `SigCgt`가 보이면 무조건 버그인가요?
> 핵심: 아니다. graceful shutdown처럼 의도된 handler일 수 있다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - blocked와 ignored 차이를 `fork()`/`exec()` 경계까지 이어서 보고 싶다면: [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md)
> - `SIGCHLD`를 ignore한 것과 `waitpid()` 기반 회수가 왜 다른지 보려면: [SIGCHLD Ignore vs `waitpid()` Bridge](./sigchld-ignore-vs-waitpid-bridge.md)
> - supervisor와 graceful shutdown 문맥으로 signal을 넓히고 싶다면: [signals, process supervision](./signals-process-supervision.md)
> - foreground process group과 `Ctrl-C` 전달 경로를 같이 보고 싶다면: [Session vs Process Group Primer](./session-vs-process-group-primer.md)
> - 운영체제 입문 primer 묶음으로 돌아가려면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

`/proc/<pid>/status`의 signal 필드는 "안 먹는 signal" 문제를 block, ignore, handler, pending 네 갈래로 바로 나누게 해 주는 1차 분기표다. 초보자는 먼저 `SigBlk`, `SigIgn`, `SigCgt`, `SigPnd`를 분리해서 읽는 습관만 잡아도 디버깅이 훨씬 빨라진다.
