# SIGCHLD Ignore vs `waitpid()` Bridge

> 한 줄 요약: `SIGCHLD`의 기본 상태는 "자식 종료를 자동 회수한다"가 아니고, 자식을 직접 `waitpid()`로 회수해야 zombie가 사라진다. 반대로 `SIG_IGN`이나 `SA_NOCLDWAIT`를 명시하면 "나중에 `waitpid()`로 회수할 종료 상태" 자체를 남기지 않는 쪽으로 읽는 편이 beginner에게 안전하다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md), [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md) 다음에 읽는 beginner bridge다. "`SIGCHLD` 기본 동작이 ignore라는데 왜 zombie가 생기지?"라는 혼란을 `default` vs `SIG_IGN` vs `SA_NOCLDWAIT` vs `waitpid()` 기대치로 한 장에서 정리한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md)
- [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
- [signals, process supervision](./signals-process-supervision.md)
- [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)
- [pidfd Basics: Race-Free Process Handles](./pidfd-basics-race-free-process-handles.md)

retrieval-anchor-keywords: sigchld ignore vs waitpid, sigchld default vs sig_ign, sigchld default behavior, sigchld zombie basics, sigchld ignore zombie, sa_nocldwait basics, waitpid expectation sigchld, explicit sig_ign vs default sigchld, child auto reap basics, child reap mental model, process supervision beginner, zombie reap beginner bridge, sigchld 기본 동작, sigchld 무시, sig_ign 좀비, sa_nocldwait, waitpid 기대치, child reaping basics, beginner handoff box, primer handoff box

## 먼저 잡는 멘탈 모델

초보자가 가장 먼저 분리해야 할 질문은 두 개다.

1. 자식이 종료했을 때 **좀비 기록을 남길 것인가**
2. 부모가 나중에 **`waitpid()`로 종료 상태를 읽을 수 있어야 하는가**

이 기준으로 보면 `SIGCHLD` 주변 선택지가 정리된다.

| 설정 | zombie가 잠깐 남을 수 있나 | 나중에 `waitpid()`로 종료 상태를 읽나 | beginner용 감각 |
|---|---|---|---|
| 기본 상태 (`SIG_DFL`) | 그렇다 | 그렇다 | "자식 종료를 부모가 직접 수거해라" |
| `SIGCHLD = SIG_IGN` 명시 | 보통 남기지 않는다 | 보통 기대하면 안 된다 | "종료 상태를 버리고 자동 정리 쪽으로 간다" |
| `SA_NOCLDWAIT` | 남기지 않는다 | 보통 기대하면 안 된다 | "좀비를 만들지 말라"를 명시한다 |
| handler 설치 + `waitpid()` | 남을 수 있지만 곧 회수 | 그렇다 | "알림은 signal, 실제 수거는 `waitpid()`" |

이 문서에서는 Linux/POSIX 실무 감각에 맞춰 다음처럼 기억하는 편을 권한다.

- `SIGCHLD` 기본 상태는 "아무것도 안 해도 자동 회수"가 아니다.
- `SIGCHLD`를 **명시적으로** `SIG_IGN`으로 두거나 `SA_NOCLDWAIT`를 쓰면 "나중에 내가 회수할 종료 상태"를 남기지 않는 쪽으로 동작한다고 보는 편이 안전하다.
- 따라서 `waitpid()`를 써서 exit status를 읽고 싶다면 `SIG_IGN`/`SA_NOCLDWAIT`와 섞지 않는 편이 beginner에게 명확하다.

## 왜 "`SIGCHLD` 기본 동작은 ignore"라는 말이 함정인가

문서나 표를 읽다 보면 "`SIGCHLD`의 default action은 ignore"라는 표현을 자주 본다.
그런데 초보자가 이 문장을 그대로 "`명시적 `SIG_IGN``과 똑같다"로 이해하면 거의 반드시 헷갈린다.

beginner용으로는 아래처럼 끊어 읽는 편이 낫다.

- **기본 상태 (`SIG_DFL`)**: handler를 따로 설치하지 않은 상태
- **명시적 `SIG_IGN`**: 프로그래머가 "이 signal은 무시"라고 직접 설정한 상태

`SIGCHLD`에서는 이 둘을 같은 의미로 취급하면 안 된다.

| 무엇을 비교하나 | 기본 상태 (`SIG_DFL`) | 명시적 `SIG_IGN` |
|---|---|---|
| 자식 종료 알림을 handler로 받나 | handler 없으면 직접 코드는 안 돈다 | handler도 안 돈다 |
| zombie가 생길 수 있나 | 그렇다 | 보통 생기지 않게 한다 |
| `waitpid()`로 나중에 회수할 수 있나 | 그렇다 | 보통 기대하지 않는다 |
| 초보자용 해석 | "부모가 직접 `waitpid()` 해야 한다" | "커널에 종료 상태를 버리라고 맡긴다" |

핵심은 이것이다.

> `SIGCHLD`에서 "default action이 ignore처럼 적혀 있다"는 말과 "내가 `SIG_IGN`을 명시했다"는 말은 beginner 관점에서 같은 뜻이 아니다.

## 타임라인으로 보면 더 덜 헷갈린다

### 경우 1: 기본 상태 + 부모가 `waitpid()` 호출

```text
child exits
  -> child becomes zombie
  -> parent calls waitpid()
  -> exit status read
  -> zombie removed
```

이게 가장 기본적인 그림이다.

- zombie는 "회수 전의 잠깐 남는 기록"이다
- 문제가 되는 것은 zombie가 생긴다는 사실 자체보다, **계속 안 치워지는 것**이다

### 경우 2: `SIGCHLD = SIG_IGN`

```text
parent sets SIGCHLD to SIG_IGN
  -> child exits
  -> kernel does not keep a waitable zombie record
  -> later waitpid() usually has nothing to reap
```

여기서는 beginner가 이렇게 기억하면 된다.

- zombie를 없애는 대신
- 나중에 부모가 "`exit code`를 읽겠다"는 선택지도 같이 약해진다

### 경우 3: `SA_NOCLDWAIT`

```text
parent installs SIGCHLD disposition with SA_NOCLDWAIT
  -> child exits
  -> child is not left as a zombie
  -> later waitpid() usually has no exited child to collect
```

`SA_NOCLDWAIT`는 이름 그대로 "child가 죽어도 wait가 필요한 상태를 남기지 말라"에 가깝다.

## `waitpid()` 기대치는 언제 성립하나

초보자 혼란의 대부분은 "`자식이 죽었으니 나중에 `waitpid()` 하면 되겠지`"라는 기대가 항상 맞는 줄 아는 데서 나온다.

하지만 그 기대는 **종료 상태를 남겨 두는 정책**일 때만 성립한다.

| 내가 원하는 것 | 추천 mental model | `waitpid()` 기대치 |
|---|---|---|
| 자식 종료 코드를 읽고 분기하고 싶다 | 기본 상태 또는 handler + `waitpid()` | 기대해도 된다 |
| zombie를 직접 회수할 준비가 돼 있다 | `SIGCHLD` 알림 뒤 `waitpid(WNOHANG)` 루프 | 기대해도 된다 |
| 종료 코드는 안 중요하고 zombie도 만들고 싶지 않다 | `SIG_IGN` 또는 `SA_NOCLDWAIT` | 나중 회수는 기대하지 말자 |
| supervisor처럼 종료 여부와 code를 모두 관리해야 한다 | 명시적 reap 설계 | 반드시 `waitpid()` 경로를 가진다 |

실무적으로는 이렇게 정리하면 안전하다.

- `exit status`가 중요하다면 `waitpid()` 경로를 설계한다.
- `waitpid()` 경로를 설계했다면 `SIGCHLD`를 `SIG_IGN`으로 두지 않는다.
- `SIG_IGN`/`SA_NOCLDWAIT`는 "코드를 단순화하는 마법"이 아니라 "`waitpid()` 기반 회수 모델을 포기하는 선택"에 가깝다.

## handler를 써도 `waitpid()`는 여전히 필요하다

`SIGCHLD` handler를 설치한 뒤 beginner가 자주 하는 착각은 이것이다.

- "handler가 돌았으니 회수까지 끝났겠지"

하지만 signal은 알림일 뿐이다.

```c
static void on_sigchld(int signo) {
    (void)signo;
    while (waitpid(-1, NULL, WNOHANG) > 0) {
        /* exited children reaped here */
    }
}
```

핵심은 handler 등록이 아니라 그 안의 `waitpid()`다.

- signal은 "자식이 끝났다"를 알려 준다
- `waitpid()`는 종료 상태를 읽고 zombie를 치운다

그래서 "`SIGCHLD`를 처리한다"와 "`자식을 회수한다`"는 같은 말이 아니다.

## 어떤 선택을 먼저 떠올리면 되나

### 1. child exit code가 필요한가

필요하면:

- 기본 상태 또는 `SIGCHLD` handler
- `waitpid()` 또는 `waitpid(WNOHANG)` 루프

이 조합을 먼저 본다.

### 2. exit code는 안 중요하고 zombie만 피하고 싶은가

그렇다면:

- `SIGCHLD = SIG_IGN`
- 또는 `SA_NOCLDWAIT`

이쪽이 후보가 된다.

단, 이 경우에는 나중에 "`그 child가 왜 죽었지? exit code는 몇이었지?`"를 `waitpid()`로 수습하려 들면 이미 늦을 수 있다.

## 자주 섞이는 오해

- "`SIGCHLD` 기본 동작이 ignore라니까 `waitpid()` 안 해도 된다"가 아니다. 기본 상태에서는 zombie가 남을 수 있다.
- "`SIG_IGN`은 signal handler가 없는 기본 상태와 비슷하다"가 아니다. `SIGCHLD`에서는 zombie/wait 의미가 달라질 수 있다.
- "`SIGCHLD` handler만 등록하면 회수까지 자동이다"가 아니다. 보통 `waitpid()` 루프가 있어야 한다.
- "`SA_NOCLDWAIT`는 `waitpid()`를 더 편하게 만들어 준다"가 아니다. 오히려 나중에 회수할 종료 상태를 남기지 않는 쪽으로 읽어야 한다.

## 꼬리질문

> Q: 왜 child가 끝났는데도 `ps`에 잠깐 남아 있나요?
> 핵심: 부모가 `waitpid()`로 종료 상태를 읽기 전까지 zombie 기록이 남을 수 있기 때문이다.

> Q: `SIGCHLD`를 `SIG_IGN`으로 두면 편한 것 아닌가요?
> 핵심: zombie를 줄일 수는 있지만, 나중에 `waitpid()`로 exit status를 읽는 모델과는 잘 맞지 않는다.

> Q: `SA_NOCLDWAIT`와 `SIG_IGN`은 무엇이 공통인가요?
> 핵심: 둘 다 beginner 관점에서는 "좀비를 남기지 않는 대신 나중 회수를 기대하지 않는 설정"으로 보면 된다.

## 여기까지 이해했으면 다음으로

> **Beginner handoff box**
>
> - zombie/orphan 상태 자체를 더 넓게 보고 싶다면: [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - `fork()` / `exec()` / `waitpid()` 전체 흐름으로 다시 묶고 싶다면: [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
> - blocked signal과 ignored signal 차이를 launch 경계에서 다시 보고 싶다면: [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md)
> - container PID 1이 왜 직접 reaping 책임을 지는지 잇고 싶다면: [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)

## 한 줄 정리

`SIGCHLD`에서는 "기본 상태"와 "명시적 `SIG_IGN`"을 같은 뜻으로 읽지 않는 것이 핵심이다. exit status를 나중에 `waitpid()`로 읽고 싶다면 직접 회수 모델을 유지하고, zombie를 자동으로 남기지 않게 할 생각이라면 그만큼 `waitpid()` 기대치도 내려놓아야 한다.
