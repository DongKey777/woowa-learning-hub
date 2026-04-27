# `clone()` Flags Mental Model: Thread-Like, Process-Like, Namespace-Isolated

> 한 줄 요약: `clone()`은 항상 새 Linux task를 만들지만, `CLONE_THREAD`/`CLONE_VM` 축으로 가면 thread-like해지고, 공유 flag를 빼면 process-like해지며, `CLONE_NEW*`를 얹으면 namespace-isolated child로 읽는 편이 가장 덜 헷갈린다.
>
> 문서 역할: 이 문서는 [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md) 다음에 읽는 intermediate follow-up이다. `clone()` trace를 봤을 때 "이 child가 thread인지 process인지, 아니면 container 쪽 namespace child인지"를 flag 조합으로 빠르게 분류하게 해 준다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)


retrieval-anchor-keywords: clone flags thread like process like namespace isolated basics, clone flags thread like process like namespace isolated beginner, clone flags thread like process like namespace isolated intro, operating system basics, beginner operating system, 처음 배우는데 clone flags thread like process like namespace isolated, clone flags thread like process like namespace isolated 입문, clone flags thread like process like namespace isolated 기초, what is clone flags thread like process like namespace isolated, how to clone flags thread like process like namespace isolated
> 관련 문서:
> - [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
> - [프로세스와 스레드 기초](./process-thread-basics.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [PID Namespace, Init Semantics](./pid-namespace-init-semantics.md)
> - [Namespace Crossings, /proc Visibility](./namespace-crossings-proc-visibility.md)
> - [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)

> retrieval-anchor-keywords: clone flags mental model, clone flag combinations, clone thread-like, clone process-like, clone namespace-isolated, clone namespace isolated, CLONE_VM, CLONE_FILES, CLONE_FS, CLONE_SIGHAND, CLONE_THREAD, CLONE_VFORK, CLONE_NEWPID, CLONE_NEWNS, CLONE_NEWUSER, CLONE_NEWNET, CLONE_NEWIPC, CLONE_NEWUTS, CLONE_NEWCGROUP, CLONE_NEWTIME, TGID vs TID, clone thread group, clone child classification, clone vs fork mental model, namespace child creation

## 핵심 개념

`clone()`을 볼 때는 "flag가 많다"보다 먼저, **새 task가 부모와 무엇을 공유하는지**를 봐야 한다.

가장 먼저 자르는 질문은 세 가지다.

1. 주소 공간, fd table, filesystem state, signal handler를 **공유하는가**
2. 새 task가 **같은 thread group**에 들어가는가
3. 새 task가 **새 namespace**에서 시작하는가

이 세 축만 잡으면 `clone()` flag 묶음은 보통 아래 셋 중 하나로 읽힌다.

| mental model | 대표 조합 | 무엇으로 읽으면 되는가 |
|---|---|---|
| process-like | `SIGCHLD` | `fork()`와 비슷한 새 child 프로세스 |
| thread-like | `CLONE_VM | CLONE_SIGHAND | CLONE_THREAD` + 보통 `CLONE_FILES | CLONE_FS` | 같은 process 안의 새 thread |
| namespace-isolated | `SIGCHLD` + 하나 이상 `CLONE_NEW*` | 새 view를 가진 child process, container/runtime 쪽 child |

아래 예시는 `clone()` 표기 습관대로 `SIGCHLD`를 함께 적는다. `clone3()`에서는 같은 의미가 `exit_signal = SIGCHLD`로 분리된다고 생각하면 된다.

## 먼저 기억할 핵심 flag

| flag | 바꾸는 것 | set이면 | unset이면 |
|---|---|---|---|
| `CLONE_VM` | 주소 공간 | 부모와 child가 같은 메모리 공간을 본다 | child는 별도 메모리 공간을 가진다 |
| `CLONE_FILES` | fd table | `close()`, `dup()`, `fcntl(F_SETFD)` 같은 table 조작이 서로에게 보인다 | fd table은 복사되고 이후 조작은 분리된다 |
| `CLONE_FS` | root/cwd/umask | 파일시스템 관련 process state를 같이 쓴다 | root/cwd/umask는 분리된다 |
| `CLONE_SIGHAND` | signal disposition | `sigaction()` 변경이 서로에게 같이 적용된다 | signal handler table은 복사된다 |
| `CLONE_THREAD` | thread group | 같은 TGID를 공유하는 thread가 된다 | 새 thread group leader가 된다 |
| `CLONE_NEW*` | namespace view | PID/mount/net/user 같은 시야를 새로 만든다 | 부모와 같은 namespace를 본다 |
| `CLONE_VFORK` | 부모 대기 방식 | parent가 child `execve()`/`_exit()`까지 멈춘다 | parent는 바로 계속 간다 |

`CLONE_VFORK`는 **정체성**이 아니라 **부모를 얼마나 멈추는가**를 바꾸는 modifier다.
즉 `CLONE_VFORK`가 있다고 해서 thread-like가 되지는 않는다.

## 1. 가장 process-like한 조합: `SIGCHLD`

가장 단순한 mental model은 이것이다.

```text
flags = SIGCHLD
```

이 조합은 `clone()`을 `fork()`에 가장 가깝게 읽는 출발점이다.

- child는 새 thread group leader가 된다
- parent는 보통 `waitpid()`로 종료를 회수할 수 있다
- child 종료 시 parent는 `SIGCHLD`를 받는다
- 주소 공간, fd table, filesystem state, signal handler table은 live-sharing이 아니라 copy 쪽으로 간다

즉 "새로 생긴 건 분명 child process"이고, namespace도 추가로 안 바꾸면 **부모와 같은 세계를 보는 일반 child**다.

다만 fd table이 복사된다고 해서 열린 파일의 모든 의미가 완전히 끊기는 것은 아니다. `fork()`처럼 **상속된 fd가 같은 open file description을 가리키는 효과**는 여전히 남을 수 있으므로, file offset 공유 같은 현상은 별도 문맥으로 봐야 한다.

## 2. thread-like로 바뀌는 기준점: `CLONE_THREAD`

`clone()` 조합을 thread-like로 읽는 가장 중요한 기준점은 `CLONE_THREAD`다.

```text
flags = CLONE_VM | CLONE_SIGHAND | CLONE_THREAD
```

여기서 중요한 제약이 함께 따라온다.

- `CLONE_SIGHAND`는 `CLONE_VM` 없이 쓸 수 없다
- `CLONE_THREAD`는 `CLONE_SIGHAND` 없이 쓸 수 없다
- 따라서 `CLONE_THREAD`를 보는 순간, 사실상 `CLONE_VM` 축까지 같이 보게 된다

이 조합이 뜻하는 바는 다음과 같다.

- 새 task는 **같은 thread group**에 들어간다
- `getpid()`는 같은 TGID를 보게 되고, 각 task는 `gettid()`로 구분된다
- 각 thread는 자기 스택, 레지스터, signal mask는 따로 가진다
- 하지만 주소 공간과 signal disposition은 process-wide 성질로 움직인다

실제 pthread/NPTL 스타일 구현에서는 보통 여기에 아래가 더 붙는다.

```text
CLONE_FS | CLONE_FILES | CLONE_SYSVSEM
```

그리고 런타임 bookkeeping 용도로 아래도 자주 같이 붙는다.

- `CLONE_SETTLS`
- `CLONE_PARENT_SETTID`
- `CLONE_CHILD_CLEARTID`

하지만 mental model 기준으로 정말 중요한 것은 다음이다.

- `CLONE_THREAD`가 있으면: 같은 process 안의 thread로 읽는다
- `CLONE_THREAD`가 없으면: 아무리 몇 개를 공유해도 기본은 process-like 쪽으로 읽는다

## 3. `CLONE_VM`만 있다고 thread는 아니다

초보자가 가장 자주 헷갈리는 함정이 이것이다.

```text
flags = CLONE_VM | SIGCHLD
```

이 조합은 주소 공간은 공유하지만, **같은 thread group은 아니다**.

즉 이런 child는:

- 메모리는 부모와 공유할 수 있다
- 하지만 여전히 새 TGID를 가진다
- `waitpid()` 대상인 process-like child다
- `CLONE_THREAD`가 만드는 pthread-style thread와는 다르다

같은 식으로 아래도 모두 "hybrid process" 쪽이다.

- `CLONE_FILES | SIGCHLD`: fd table만 공유하는 child
- `CLONE_FS | SIGCHLD`: cwd/root/umask만 공유하는 child
- `CLONE_VM | CLONE_VFORK | SIGCHLD`: parent를 잠깐 멈추는 `vfork()`-like child

즉 `clone()`은 thread/process 둘 중 하나만 만드는 API가 아니라, **중간 hybrid를 만들 수 있는 low-level primitive**다.
그래도 실전 mental model은 `CLONE_THREAD` 유무를 첫 기준으로 두면 대부분 빠르게 정리된다.

## 4. namespace-isolated child는 "새 process + 새 시야"로 읽는다

`CLONE_NEW*`가 붙기 시작하면 생각을 thread 쪽이 아니라 **격리된 process** 쪽으로 옮기는 편이 맞다.

대표적인 container/runtime 쪽 출발점은 이런 형태다.

```text
flags = SIGCHLD | CLONE_NEWUSER | CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET | CLONE_NEWIPC | CLONE_NEWUTS
```

여기서 읽는 순서는 단순하다.

- 기본 바닥은 `SIGCHLD` 기반의 process-like child다
- 그 위에 PID, mount, network, IPC, UTS, user namespace를 새로 얹는다
- 그래서 child는 "부모와 다른 view를 가진 새 process"가 된다

특히 `CLONE_NEWPID`는 해석 포인트가 분명하다.

- 새 child는 새 PID namespace에서 시작한다
- 그 namespace 안에서 첫 프로세스라면 PID 1 역할을 맡는다
- 그래서 signal/reaping 의미가 container init semantics와 바로 연결된다

또한 `CLONE_NEWNS`와 `CLONE_NEWPID`를 같이 쓰면 `/proc`을 새 mount namespace에서 다시 마운트해야 `ps`, `/proc/self`, `kill` 감각이 덜 꼬인다.

즉 namespace child는 이렇게 읽으면 된다.

```text
namespace child
  = thread처럼 부모 안에 들어간 것
  이 아니라
  = 부모와 다른 시야를 가진 새 process
```

## 5. 조합 제약을 같이 외워 두면 덜 헤맨다

실무에서 자주 걸리는 제약만 추리면 이 정도다.

| 조합 | 왜 문제인가 |
|---|---|
| `CLONE_SIGHAND` without `CLONE_VM` | signal disposition 공유는 주소 공간 공유를 전제로 한다 |
| `CLONE_THREAD` without `CLONE_SIGHAND` | 같은 thread group은 signal handler 공유를 전제로 한다 |
| `CLONE_NEWPID` with `CLONE_THREAD` | PID namespace를 새로 만들면서 같은 thread group에 남을 수 없다 |
| `CLONE_NEWUSER` with `CLONE_THREAD` | user namespace 격리 child는 thread-like 조합과 같이 갈 수 없다 |
| `CLONE_NEWNS` with `CLONE_FS` | 새 mount namespace를 만들면서 root/cwd/umask를 같은 FS state로 묶을 수 없다 |
| `CLONE_NEWUSER` with `CLONE_FS` | user namespace 생성과 FS state 공유를 같이 둘 수 없다 |
| `CLONE_NEWIPC` with `CLONE_SYSVSEM` | 새 IPC namespace와 SysV semaphore undo 공유는 충돌한다 |

이 표를 "조합 암기"보다 **정신 모델의 안전장치**로 쓰는 편이 좋다.
즉 namespace isolation과 thread grouping은 보통 서로 반대 방향의 설계라는 뜻이다.

## 6. trace에서 5초 만에 읽는 shortcut

`strace`나 runtime 로그에서 `clone()`을 보면 순서를 이렇게 두면 된다.

1. `CLONE_THREAD`가 보이는가
2. `CLONE_NEW*`가 보이는가
3. `CLONE_VM`/`CLONE_FILES`/`CLONE_FS`가 얼마나 붙는가
4. `CLONE_VFORK`가 parent wait semantics만 바꾸는지 본다

빠른 해석 표:

| trace에서 보이는 묶음 | 바로 떠올릴 말 |
|---|---|
| `CLONE_VM | CLONE_SIGHAND | CLONE_THREAD` | "새 thread" |
| `SIGCHLD` 중심, `CLONE_THREAD` 없음 | "새 process-like child" |
| `SIGCHLD` + `CLONE_NEW*` | "container/runtime 쪽 namespace child" |
| `CLONE_VM | SIGCHLD` | "메모리만 공유하는 hybrid child, thread는 아님" |
| `CLONE_VM | CLONE_VFORK | SIGCHLD` | "`vfork()`-like fast path" |

## 꼬리질문

> Q: `clone()`에서 thread-like로 읽는 진짜 스위치는 무엇인가요?
> 핵심: `CLONE_THREAD`다. 그리고 그 뒤에는 `CLONE_SIGHAND`, `CLONE_VM` 제약이 따라온다.

> Q: `CLONE_VM`만 있으면 같은 thread 아닌가요?
> 핵심: 아니다. 메모리만 공유할 뿐, `CLONE_THREAD`가 없으면 새 thread group의 process-like child다.

> Q: `CLONE_NEWPID`가 붙으면 더 process-like해지나요, thread-like해지나요?
> 핵심: process-like 쪽이다. `CLONE_NEWPID`는 새 PID namespace를 만드는 격리 flag이고 `CLONE_THREAD`와 함께 갈 수 없다.

> Q: `CLONE_VFORK`가 붙으면 thread라고 보면 되나요?
> 핵심: 아니다. parent를 잠깐 멈추는 modifier일 뿐, thread group 정체성을 바꾸는 flag는 아니다.

## 이 문서 다음에 보면 좋은 문서

- `clone()`이 spawn/fork/exec 축에서 어디에 놓이는지 다시 정리하려면 [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- process/thread 기초로 다시 내려가려면 [프로세스와 스레드 기초](./process-thread-basics.md)
- namespace child가 container runtime에서 어떤 의미를 가지는지 보려면 [container, cgroup, namespace](./container-cgroup-namespace.md)
- `CLONE_NEWPID` 뒤의 PID 1 의미를 더 깊게 보려면 [PID Namespace, Init Semantics](./pid-namespace-init-semantics.md)
- namespace를 건넌 뒤 `/proc`이 왜 달라 보이는지 보려면 [Namespace Crossings, /proc Visibility](./namespace-crossings-proc-visibility.md)

## 한 줄 정리

`clone()`은 "새 task를 만든다"까지는 같지만, `CLONE_THREAD`가 붙으면 thread-like, 공유 flag 없이 `SIGCHLD`만 남기면 process-like, `CLONE_NEW*`를 얹으면 namespace-isolated child로 읽는 것이 가장 실전적이다.
