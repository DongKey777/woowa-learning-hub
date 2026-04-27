# Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`

> 한 줄 요약: blocked signal은 "지금은 전달을 막아 둔 상태"인 signal mask 문제이고, ignored/default/handler는 "전달되면 무엇을 할지"인 signal disposition 문제다. `fork()`는 둘을 복사하고, `exec()`는 mask는 남기되 caught handler를 기본 동작으로 되돌리며, `posix_spawn()`은 보통 `fork()+exec()`처럼 시작하되 attrs로 초기 mask/default를 덮어쓸 수 있다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)와 [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md) 다음에 읽는 beginner bridge다. "`SIGINT`를 block한 것"과 "`SIGINT`를 ignore한 것"이 왜 다른지, 그리고 그 차이가 process launch 경계에서 어떻게 이어지는지 한 장으로 정리한다.

**난이도: 🟢 Beginner**

관련 문서:

- [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
- [/proc/<pid>/status Signal Fields Debugging Primer](./proc-pid-status-signal-fields-debugging-primer.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [signals, process supervision](./signals-process-supervision.md)
- [SIGCHLD Ignore vs `waitpid()` Bridge](./sigchld-ignore-vs-waitpid-bridge.md)
- [Session vs Process Group Primer](./session-vs-process-group-primer.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [operating-system 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: signal mask vs disposition bridge, signal mask disposition mental model, blocked vs ignored mental model, blocked signal vs ignored signal, signal handler vs default action, signal disposition basics, fork exec signal inheritance, exec preserves signal mask, exec resets handlers, ignored signal preserved across exec, posix_spawn signal inheritance, posix_spawn setsigmask setsigdef, posix_spawn_setsigmask, posix_spawn_setsigdef, beginner signal inheritance primer

## 먼저 잡는 멘탈 모델

먼저 signal에는 서로 다른 두 질문이 있다.

| 질문 | 보는 대상 | 초보자용 감각 |
|---|---|---|
| "지금 당장 이 signal을 받게 둘까?" | signal mask | 문 앞에 잠깐 세워 둔다 |
| "실제로 도착하면 무엇을 할까?" | signal disposition | 기본 동작 / 무시 / handler 중 하나를 고른다 |

그래서 아래 네 단어를 한 줄로 섞으면 안 된다.

| 상태 | 의미 | 흔한 오해 |
|---|---|---|
| blocked | delivery를 미뤄 pending 상태로 둘 수 있다 | "무시한 것"이라고 착각 |
| ignored | 전달돼도 버린다 | "unblock하면 처리될 것"이라고 착각 |
| default | signal별 기본 동작을 쓴다 | "모든 signal이 종료"라고 착각 |
| handler | 프로그램이 등록한 함수를 실행한다 | "`exec()` 뒤에도 남는다"라고 착각 |

엄밀히는 signal mask는 thread별, signal disposition은 process-wide 성질이다.
beginner 단계에서는 "child나 새 프로그램이 어떤 signal 상태로 시작하는가"를 보는 정도로 충분하다.

## API 경계에서 한 번에 보기

| 무엇을 보나 | `fork()` 뒤 child | `exec()` 뒤 같은 PID의 새 프로그램 | `posix_spawn()` child |
|---|---|---|---|
| blocked signals (mask) | `fork()`를 호출한 thread의 mask를 복사한다 | mask가 유지된다 | 기본적으로 이어받고, `POSIX_SPAWN_SETSIGMASK`로 초기 mask를 지정할 수 있다 |
| ignored signals | 부모 disposition을 복사한다 | ignore 상태가 유지된다 | 보통 이어받고, `POSIX_SPAWN_SETSIGDEF`로 default로 되돌릴 수 있다 |
| default actions | default 상태를 복사한다 | default는 default로 남는다 | default로 시작하거나 `SETSIGDEF`로 강제 default 지정 가능 |
| handlers | 부모 handler disposition을 복사한다 | caught handler는 default로 reset된다 | 부모 handler를 넘기지 않는다. target program이 다시 설치해야 한다 |

핵심만 줄이면 이렇다.

- `fork()`는 mask와 disposition을 복사한다.
- `exec()`는 mask와 ignored/default 상태는 남기지만, caught handler는 default로 되돌린다.
- `posix_spawn()`은 새 프로그램 launch API라서 보통 `fork()+exec()`처럼 생각하고, attrs로 initial mask/default를 조정한다.

## 예제 1: blocked는 `exec()` 뒤에도 남는다

상황:

- parent가 잠깐 `SIGINT`를 block한 상태였다.
- 그 상태에서 child를 만들고 바로 `exec("sleep")`했다.
- "새 프로그램이니 signal 상태도 깨끗해졌겠지"라고 생각했다.

실제 mental model:

```text
parent: SIGINT blocked
  -> fork()
child: SIGINT blocked copy
  -> exec("sleep")
new program: still SIGINT blocked
```

그래서 `Ctrl-C`에 바로 반응하지 않는다면 handler 문제가 아니라 **mask를 풀지 않은 문제**일 수 있다.
`posix_spawn()`에서는 child initial mask를 empty set으로 주고 `POSIX_SPAWN_SETSIGMASK`를 켜면 이 혼동을 줄일 수 있다.

## 예제 2: ignored도 `exec()` 뒤에 남을 수 있다

상황:

- parent가 `SIGPIPE`를 `SIG_IGN`으로 바꿔 두었다.
- child가 `exec()`로 다른 프로그램이 됐다.
- 그 프로그램은 `SIGPIPE`의 기본 동작을 기대했다.

하지만 ignore는 handler가 아니라 disposition 정책이다.

```text
SIGPIPE ignored
  -> exec()
still ignored
```

이때는 `mask` 문제가 아니라 **disposition을 default로 돌릴지**의 문제다.
`posix_spawn()`에서는 `spawn_sigdefault`에 해당 signal을 넣고 `POSIX_SPAWN_SETSIGDEF`를 켜는 쪽을 본다.

## 예제 3: handler는 `fork()`까지만 복사되고 `exec()`에서 끊긴다

상황:

- parent가 `SIGTERM` handler를 설치해 종료 전에 로그를 flush한다.
- `fork()` 직후 child는 같은 handler disposition을 복사해 시작한다.
- child가 `exec("worker")`를 하면 handler는 유지되지 않는다.

```text
parent: SIGTERM -> custom handler
  -> fork()
child before exec: same custom handler
  -> exec("worker")
worker after exec: SIGTERM back to default
```

`exec()`는 프로그램 이미지를 갈아끼우므로 예전 프로그램의 handler 함수 주소를 계속 쓸 수 없다.
worker가 custom shutdown을 원하면 worker 코드가 스스로 handler를 다시 설치해야 한다.

## `posix_spawn()`에서 고르는 knob

| 하고 싶은 것 | 보는 attr | 의미 |
|---|---|---|
| child가 어떤 signal을 block한 채 시작할까 | `POSIX_SPAWN_SETSIGMASK` | initial signal mask |
| parent가 ignored하던 signal을 child에서는 default로 돌릴까 | `POSIX_SPAWN_SETSIGDEF` | initial signal default actions |
| parent의 custom handler를 child에 넘길까 | 해당 없음 | 새 프로그램이 직접 handler를 설치해야 한다 |

초보자 체크:

- `SETSIGMASK`는 blocked/unblocked 문제다.
- `SETSIGDEF`는 ignored/default 문제다.
- 둘은 서로 대체제가 아니다.
- `SIGCHLD` ignored 상태는 child reaping 기대치를 바꿀 수 있으므로, default `SIGCHLD`와 명시적 `SIG_IGN`이 왜 다른지 보려면 [SIGCHLD Ignore vs `waitpid()` Bridge](./sigchld-ignore-vs-waitpid-bridge.md)로 이어서 본다.

## 자주 섞이는 오해

- "`exec()`는 새 프로그램이니 signal도 전부 초기화된다"가 아니다. mask와 ignored/default 상태는 남을 수 있고, caught handler만 default로 reset된다.
- "`SIGINT`가 안 먹는다"만 보고 ignore라고 단정하면 안 된다. blocked mask 때문일 수도 있다.
- "`posix_spawn()`이면 parent signal 상태가 안 새어 들어간다"가 아니다. attrs로 덮어쓰지 않으면 `fork()+exec()`처럼 이어진다고 보는 편이 안전하다.
- "`posix_spawn()` attrs로 custom handler를 넣을 수 있다"가 아니다. attrs는 initial mask/default 같은 시작 상태를 정한다.

## 꼬리질문

> Q: blocked signal과 ignored signal의 가장 큰 차이는 무엇인가요?
> 핵심: blocked는 나중에 전달될 수 있지만, ignored는 전달돼도 버린다.

> Q: 왜 `exec()` 뒤에는 parent의 signal handler가 그대로 안 남나요?
> 핵심: 새 프로그램 이미지로 갈아타므로 예전 프로그램의 handler 코드를 계속 신뢰할 수 없어서 caught handler는 default로 reset된다.

> Q: `posix_spawn()`에서 child가 깨끗한 signal 상태로 시작하게 하려면 무엇을 보나요?
> 핵심: blocked/unblocked는 `POSIX_SPAWN_SETSIGMASK`, ignore/default는 `POSIX_SPAWN_SETSIGDEF`를 본다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`/proc/<pid>/status`에서 `SigBlk`/`SigIgn`/`SigCgt`/`SigPnd`를 실제 디버깅 표지판으로 읽고 싶다면": [/proc/<pid>/status Signal Fields Debugging Primer](./proc-pid-status-signal-fields-debugging-primer.md)
> - "`posix_spawnattr_t`에서 process group과 signal knob를 한 장으로 다시 정리"하고 싶다면: [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
> - "`Ctrl-C`가 어느 프로세스들에 가는지"를 session/job-control 그림으로 잇고 싶다면: [Session vs Process Group Primer](./session-vs-process-group-primer.md)
> - "shutdown, reaping, supervision에서 signal을 어떻게 다루는지"를 운영 관점으로 보려면: [signals, process supervision](./signals-process-supervision.md)
> - "`SIGCHLD` 기본 상태와 명시적 `SIG_IGN`이 왜 같은 뜻이 아닌지"를 child reaping 기준으로 묶고 싶다면: [SIGCHLD Ignore vs `waitpid()` Bridge](./sigchld-ignore-vs-waitpid-bridge.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

signal 문제는 먼저 "`막혀 있는가(mask)`"와 "`받으면 무엇을 하는가(disposition)`"를 나눠야 한다. 그다음 `fork()`는 복사, `exec()`는 handler reset, `posix_spawn()`은 attrs로 initial mask/default 조정이라고 기억하면 beginner 단계의 혼란이 크게 줄어든다.
