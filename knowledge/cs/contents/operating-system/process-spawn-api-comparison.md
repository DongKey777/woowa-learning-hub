---
schema_version: 3
title: Process Spawn API Comparison fork vfork posix_spawn exec clone
concept_id: operating-system/process-spawn-api-comparison
canonical: true
category: operating-system
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 77
review_feedback_tags:
- process-spawn-api
- comparison
- fork-vfork-posix
- spawn-exec-clone
aliases:
- fork vfork posix_spawn exec clone comparison
- process spawn API
- exec does not create new process
- posix_spawn high level API
- clone flags low level primitive
- vfork exec path
intents:
- comparison
- definition
linked_paths:
- contents/operating-system/process-lifecycle-and-ipc-basics.md
- contents/operating-system/fork-exec-copy-on-write-behavior.md
- contents/operating-system/posix-spawn-file-actions-primer.md
- contents/operating-system/posix-spawn-attributes-primer.md
- contents/operating-system/clone-flags-thread-like-process-like-namespace-isolated.md
confusable_with:
- operating-system/fork-exec-copy-on-write-behavior
- operating-system/posix-spawn-file-actions-primer
- operating-system/clone-flags-thread-like-process-like-namespace-isolated
expected_queries:
- fork vfork posix_spawn exec clone은 무엇이 새로 생기고 무엇이 교체되는지 어떻게 달라?
- exec는 새 process를 만드는 게 아니라 current process image를 갈아끼우는 거야?
- posix_spawn은 fork/exec보다 어떤 high-level request로 보면 돼?
- clone은 Linux에서 thread-like process-like namespace child를 직접 고르는 primitive야?
contextual_chunk_prefix: |
  이 문서는 fork, vfork, posix_spawn, exec, clone을 비교해 무엇이 새로 생기고 무엇이 기존
  process image를 교체하는지 분리한다. subprocess API 이름이 섞일 때 읽는 beginner chooser다.
---
# Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`

> 한 줄 요약: `fork()`는 부모를 하나 더 갈라 만드는 기본 모델이고, `vfork()`는 `exec()` 직전까지 부모를 잠깐 멈추는 특수 경로이며, `posix_spawn()`은 "새 프로그램 하나 실행"을 요청하는 고수준 API이고, `exec()`는 새 프로세스를 만드는 게 아니라 현재 프로세스를 갈아끼우고, `clone()`은 Linux에서 공유 범위를 직접 고르는 저수준 생성 primitive다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md) 다음에 읽는 beginner follow-up이다. subprocess를 띄울 때 API 이름은 아는데 머릿속 그림이 섞일 때, "무엇이 새로 생기고 무엇이 교체되는가"를 먼저 분리해 준다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)


retrieval-anchor-keywords: fork exec 차이, fork와 exec 뭐가 달라요, exec는 새 프로세스인가요, posix_spawn 뭐예요, vfork 뭐예요, clone 뭐예요, subprocess 실행 큰 그림, 새 프로세스 생성 vs 교체, process spawn mental model, process launch basics, 처음 배우는데 fork exec 헷갈려요, 프로세스 실행 api 큰 그림, child process 생성 기초, beginner operating system, operating system primer
> 관련 문서:
> - [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
> - [Fork, Exec, Copy-on-Write Behavior](./fork-exec-copy-on-write-behavior.md)
> - [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
> - [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
> - [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md)
> - [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
> - [`clone()` Flags Mental Model: Thread-Like, Process-Like, Namespace-Isolated](./clone-flags-thread-like-process-like-namespace-isolated.md)
> - [pidfd Basics: Race-Free Process Handles](./pidfd-basics-race-free-process-handles.md)
> - [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)

> retrieval-anchor-keywords: process spawn api comparison, process spawn comparison, spawn api mental model, subprocess mental model, child creation api, process launch basics, fork vs vfork, fork vs posix_spawn, fork vs exec, exec vs fork, exec is not spawn, posix_spawn basics, posix_spawn mental model, vfork basics, vfork mental model, clone basics, clone mental model, clone vs fork, clone flags mental model, clone thread-like process-like, clone namespace isolated, new pid or not, process image replacement, spawn api fd hygiene, posix_spawn fd inheritance basics, fork exec signal inheritance, fork exec 뭐예요, exec가 프로세스를 새로 만들어요, 처음 subprocess를 띄울 때, beginner handoff box, primer handoff box, process spawn comparison 다음 문서, subprocess api 다음 단계

## 먼저 잡는 멘탈 모델

이 다섯 이름이 자주 섞이는 이유는 모두 "프로그램을 띄우는 것처럼 보이는" 주변에 있기 때문이다.
하지만 mental model은 먼저 두 질문으로 자르는 편이 훨씬 쉽다.

1. **새 child/task가 생기는가**
2. **현재 프로세스의 프로그램 이미지가 교체되는가**

이 기준으로 보면 감각이 바로 갈린다.

| 호출 | 새 child/task 생성 | 현재 프로세스 이미지 교체 | 부모 실행 | 초보자용 한 줄 감각 |
|---|---|---|---|---|
| `fork()` | 그렇다 | 아니다 | 계속 간다 | 부모를 하나 더 갈라 child를 만든다 |
| `vfork()` | 그렇다 | 아니다 | child가 `exec()` 또는 `_exit()` 할 때까지 멈춘다 | child가 부모 실행 공간을 잠깐 빌려 `exec()` 쪽으로 뛰어간다 |
| `posix_spawn()` | 그렇다 | child 쪽에서 곧바로 target program으로 간다 | 계속 간다 | "다른 프로그램 하나 실행"을 요청하는 고수준 API다 |
| `exec()` | 아니다 | 그렇다 | 해당 없음 | 새 child 없이 현재 프로세스가 다른 프로그램이 된다 |
| `clone()` | 그렇다 | 아니다 | 계속 가는 경우가 일반적이다 | Linux가 공유 범위를 직접 고르게 하는 저수준 생성 도구다 |

핵심은 이것이다.

- `fork()` / `vfork()` / `posix_spawn()` / `clone()`은 **무언가를 새로 만든다**
- `exec()`는 **새로 만들지 않고 현재 것을 바꾼다**

## 1. `exec()`는 spawn이 아니라 "교체"다

초보자가 가장 먼저 바로잡아야 하는 오해가 이것이다.

- `exec()`는 새 프로세스를 추가하지 않는다
- 현재 PID가 같은 채로 코드/데이터/힙/스택 같은 프로그램 이미지가 바뀐다
- 그래서 `exec()`만 호출하면 프로세스 수는 늘지 않는다

가장 흔한 그림은 shell이다.

```text
shell process
  -> fork() 로 child 생성
  -> child가 exec("/usr/bin/python", ...)
  -> child는 더 이상 shell 코드가 아니라 python 프로그램이 된다
```

즉 "새 child를 만든다"는 일은 `fork()` 쪽이 하고,
"그 child를 다른 프로그램으로 바꾼다"는 일은 `exec()` 쪽이 한다.

이 차이를 놓치면 아래 API들도 다 흐려진다.

- `posix_spawn()`이 왜 `exec()`와 다른지
- `vfork()`가 왜 `exec()` 직전 fast path처럼 설명되는지
- `O_CLOEXEC`가 왜 exec 경계에서 중요해지는지

여기에 더해 "`blocked signal`과 `ignored signal`도 `exec()` 뒤에 같은 방식으로 남나?"가 다음 혼동 포인트라면 [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md)에서 mask와 disposition을 분리해 이어서 보는 편이 안전하다.

## 2. `fork()`: 가장 직관적인 기본 모델

`fork()`는 "부모 실행 흐름이 두 갈래로 갈라진다"는 감각으로 이해하면 된다.

- 부모와 child가 둘 다 `fork()` 다음 줄부터 실행을 이어 간다
- child는 새 PID를 가진다
- 메모리는 처음부터 전부 복사하는 게 아니라 보통 copy-on-write로 시작한다
- child는 `exec()` 전에 fd 정리, 작업 디렉터리 변경, 환경 변수 조정 같은 준비를 직접 할 수 있다

그래서 `fork()`는 **가장 이해하기 쉬운 범용 기본값**이다.

```c
pid_t pid = fork();
if (pid == 0) {
    execl("/usr/bin/python3", "python3", "worker.py", NULL);
}
```

초보자용 감각:

- "먼저 child를 하나 만들고"
- "child 쪽에서 필요한 준비를 한 뒤"
- "원하면 `exec()`로 새 프로그램으로 갈아탄다"

단, 성능과 메모리 비용은 별도 문제다. 그 부분은 [Fork, Exec, Copy-on-Write Behavior](./fork-exec-copy-on-write-behavior.md)가 더 직접적이다.

## 3. `vfork()`: 일반 child라기보다 `exec()` 전용 대기실에 가깝다

`vfork()`를 그냥 "더 빠른 `fork()`"라고 외우면 바로 헷갈린다.
beginner mental model은 이쪽이 더 안전하다.

- child는 생긴다
- 하지만 부모는 child가 `exec()` 또는 `_exit()`를 할 때까지 멈춘다
- child는 부모의 주소 공간을 잠깐 빌려 쓰는 것처럼 봐야 한다
- 그래서 child가 마음대로 메모리를 건드리거나 일반 함수 흐름을 오래 타는 모델로 이해하면 안 된다

즉 `vfork()`는 "새 child를 만든 뒤 마음껏 child 코드를 실행"하는 API가 아니라,
**"곧바로 `exec()`로 넘어갈 child를 아주 짧게 준비시키는 특수 경로"**에 가깝다.

초보자가 `strace`에서 `vfork()`를 봤을 때는 이렇게 읽으면 충분하다.

```text
부모가 잠깐 멈춤
  -> child가 빨리 exec() 하거나 _exit()
  -> 그다음 부모가 다시 진행
```

그래서 직접 쓰는 애플리케이션 코드보다, libc나 런타임이 내부 최적화로 쓰는 경우가 더 자연스럽다.

## 4. `posix_spawn()`: "다른 프로그램 하나 실행"이라는 고수준 계약

`posix_spawn()`은 mental model을 이렇게 잡으면 된다.

- 새 child를 만든다
- 그 child는 보통 곧바로 target program으로 들어간다
- 호출자는 child 쪽에서 할 수 있는 준비를 제한된 방식으로 전달한다
- 목적은 "외부 프로그램 실행"이지 "child 안에서 임의의 코드를 길게 수행"하는 것이 아니다

즉 `posix_spawn()`은 `fork()`와 `exec()`를 각각 따로 생각하기보다,
**"새 프로그램 launch를 요청하는 고수준 API"**로 보는 편이 정확하다.

중요한 점은 구현 세부사항과 계약을 분리하는 것이다.

- libc는 내부적으로 `fork()`, `vfork()`, `clone()` 계열을 선택할 수 있다
- 하지만 호출자 mental model은 "새 프로그램을 안전하게 실행해 달라"에 두는 편이 낫다
- under-the-hood가 무엇인지를 전제로 로직을 짜면 이식성과 해석이 약해진다

그래서 초보자 관점에서는 아래처럼 고르면 된다.

- child 안에서 복잡한 사용자 코드를 직접 돌려야 한다면 `fork()` + `exec()`
- "프로그램 실행"이 목적이고 설정도 file actions/attrs 정도면 `posix_spawn()`

여기서 stdin/stdout redirect, `O_CLOEXEC`, `pipe EOF`, leaked fd 같은 감각이 바로 이어지지 않는다면 [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)로 내려가서 "무엇을 남기고 무엇을 닫는가"를 같은 축으로 다시 보는 편이 좋다.
`dup2()` 감각은 있는데 `posix_spawn_file_actions_adddup2()` / `addopen()` / `addclose()` 이름이 추상적으로 느껴지면 [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)에서 redirection 패턴만 따로 잡고 돌아오면 된다.
반대로 redirect는 이해했는데 `posix_spawnattr_t`, process group, signal mask가 추상적으로 느껴지면 [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)에서 `attrs`를 process 시작 조건으로 따로 읽고 돌아오면 된다.

## 5. `clone()`: Linux가 "얼마나 공유할지" 직접 정하게 하는 primitive

`clone()`은 `fork()`보다 어려운 이유가 이름 때문이 아니라, **공유 범위를 호출자가 직접 정하기 때문**이다.

- 메모리를 공유할지
- file descriptor table을 공유할지
- signal handler를 공유할지
- thread처럼 보이게 할지
- namespace를 분리할지

이런 성질이 flag로 결정된다.

어떤 flag 묶음을 thread-like child, process-like child, namespace-isolated child로 읽을지는 [`clone()` Flags Mental Model: Thread-Like, Process-Like, Namespace-Isolated](./clone-flags-thread-like-process-like-namespace-isolated.md)에서 이어서 보면 된다.

그래서 `clone()`의 beginner mental model은 이렇다.

```text
fork()  = 친절한 기본 프리셋
clone() = 공유 범위를 직접 조립하는 저수준 생성 도구
```

이 차이 때문에 `clone()`은 보통 다음과 연결된다.

- thread library 구현
- container / namespace runtime
- 프로세스처럼도, thread처럼도 보일 수 있는 Linux task 모델

즉 초보자가 `clone()`을 읽을 때는 "이게 곧 일반 subprocess API"라고 보기보다,
**Linux 내부 모델과 런타임 구현을 이해하기 위한 lower-level primitive**로 보는 편이 맞다.

## 6. 상황별로 무엇을 먼저 떠올리면 좋은가

| 상황 | 먼저 떠올릴 모델 | 이유 |
|---|---|---|
| 다른 프로그램 하나를 실행하고 싶다 | `posix_spawn()` | 호출 의도가 "launch target program"에 가장 가깝다 |
| child 쪽에서 fd 재배치, 세션 분리, 추가 준비를 직접 하고 싶다 | `fork()` + `exec()` | child가 `exec()` 전 코드를 직접 실행할 수 있다 |
| 이미 child 안에 있고, 이제 target program으로 갈아타고 싶다 | `exec()` | 새 child를 만들지 않고 현재 이미지만 바꾸면 된다 |
| trace에서 `vfork()`가 보인다 | "`exec()` 직전 특수 fast path" | 일반 child 실행 모델로 과해석하지 않는 편이 안전하다 |
| thread / container / namespace 같은 Linux runtime 내부를 본다 | `clone()` | 공유 범위를 낮은 수준에서 고르는 문제다 |

실무에서는 런타임이나 라이브러리가 이들을 섞어서 쓸 수 있다.
그래도 해석 순서는 단순하다.

1. 새 child/task가 생겼는가
2. 누가 `exec()`를 하는가
3. 부모가 멈추는가
4. 공유 범위를 누가 얼마나 제어하는가

## 7. 자주 섞이는 오해

### "`exec()`가 새 프로세스를 만든다"

아니다. 새 프로세스를 만드는 쪽은 `fork()` / `posix_spawn()` / `clone()`류고, `exec()`는 현재 프로세스 이미지를 교체한다.

### "`vfork()`는 그냥 빠른 `fork()`다"

너무 단순한 설명이다. 초보자는 "부모를 잠깐 멈추고 child를 거의 `exec()` 전용으로 다루는 특수 경로"라고 이해하는 편이 안전하다.

### "`posix_spawn()`은 그냥 `fork()`의 다른 이름이다"

아니다. mental model이 다르다. `posix_spawn()`은 호출자에게 "새 프로그램 실행" 계약을 주는 고수준 API고, 내부 구현은 libc가 정할 수 있다.

### "`clone()`은 이름만 다른 process 생성 API다"

아니다. `clone()`은 Linux task의 공유 성질을 세밀하게 고르는 primitive라서, thread/runtime/container 이해와 더 가깝다.

## 꼬리질문

> Q: subprocess를 띄울 때 가장 먼저 무엇부터 구분해야 하나요?
> 핵심: 새 child를 만드는 문제인지, 현재 프로세스를 `exec()`로 교체하는 문제인지부터 나눠야 한다.

> Q: `posix_spawn()`과 `exec()`의 가장 큰 차이는 뭔가요?
> 핵심: `posix_spawn()`은 새 child를 만들어 target program을 실행하고, `exec()`는 현재 프로세스를 target program으로 바꾼다.

> Q: `clone()`이 trace에 보이면 무조건 새 프로세스인가요?
> 핵심: 아니다. 어떤 공유 flag를 썼는지에 따라 thread처럼 보일 수도 있고, process-like task처럼 보일 수도 있다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`posix_spawn()`에서 fd redirect가 child 쪽에서 어떻게 적용되는지"를 바로 잇고 싶다면: [posix_spawn File Actions Primer](./posix-spawn-file-actions-primer.md)
> - "`blocked signal`과 `ignored signal`이 launch 경계에서 왜 다르게 남는지"가 궁금하면: [Signal Mask vs Disposition Bridge: `fork()`, `exec()`, `posix_spawn()`](./signal-mask-vs-disposition-fork-exec-posix-spawn.md)
> - "`clone()`이 thread처럼도 process처럼도 보이는 이유"를 더 또렷하게 보려면: [`clone()` Flags Mental Model: Thread-Like, Process-Like, Namespace-Isolated](./clone-flags-thread-like-process-like-namespace-isolated.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

`fork()` / `vfork()` / `posix_spawn()` / `clone()`은 "무엇을 새로 만들까"의 차이고, `exec()`는 "현재 것을 무엇으로 바꿀까"의 문제라는 축만 먼저 고정하면 subprocess API 이름이 훨씬 덜 헷갈린다.
