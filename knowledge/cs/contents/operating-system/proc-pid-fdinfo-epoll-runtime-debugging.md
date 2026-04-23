# /proc/<pid>/fdinfo, Epoll Runtime Debugging

> 한 줄 요약: `/proc/<pid>/fdinfo`는 "이 프로세스가 무슨 fd를 열었나"를 넘어서, file offset, flags, epoll watch 상태 같은 런타임 fd 메타데이터를 보여 주는 저비용 현장 디버깅 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
> - [epoll Level-Triggered, Edge-Triggered, ONESHOT Wakeup Semantics](./epoll-level-edge-oneshot-wakeup-semantics.md)
> - [deleted-but-open files, log rotation, space leak debugging](./deleted-open-file-space-leak-log-rotation.md)
> - [eventfd, signalfd, Epoll Control-Plane Integration](./eventfd-signalfd-epoll-control-plane-integration.md)

> retrieval-anchor-keywords: /proc/pid/fdinfo, fdinfo, epoll fdinfo, file offset debug, fd flags debug, mount id, epoll watched fds, proc fd runtime state, pos flags

## 핵심 개념

`/proc/<pid>/fd`가 "어떤 경로/객체를 열고 있는가"를 보여 준다면, `/proc/<pid>/fdinfo/<fd>`는 그 fd의 런타임 상태를 더 자세히 보여 준다. 이 정보는 숨은 offset 공유, epoll 등록 상태, deleted-open file, descriptor flags 문제를 실제 프로세스 상태로 확인할 때 유용하다.

- `/proc/<pid>/fd/<fd>`: 해당 fd가 가리키는 객체 링크다
- `/proc/<pid>/fdinfo/<fd>`: 해당 fd의 offset, flags, mount id, 일부 객체별 추가 정보를 보여 준다
- `epoll fdinfo`: 어떤 target fd들이 어떤 event mask로 등록됐는지 힌트를 줄 수 있다

왜 중요한가:

- 코드 없이도 "이 프로세스가 지금 어떤 fd 상태인가"를 좁힐 수 있다
- shared offset 문제를 런타임에 검증할 수 있다
- event loop가 어떤 fd를 어떻게 감시 중인지 확인하는 현장 디버깅이 가능하다

## 깊이 들어가기

### 1. `fdinfo`는 pathname보다 상태를 보여 준다

같은 파일 path를 열고 있어도 상태는 다를 수 있다.

- 현재 file offset
- flags
- mount id
- 객체 종류별 추가 메타데이터

그래서 `readlink /proc/<pid>/fd/<fd>`만으로는 안 보이는 문제가 `fdinfo`에는 드러난다.

### 2. shared offset 디버깅에 특히 유용하다

`dup()` 또는 `fork()` 공유 때문에 cursor가 꼬인다고 의심될 때, `fdinfo`의 offset 변화는 좋은 힌트가 된다.

- 두 fd가 같은 path를 가리킨다
- offset이 같이 움직이는 것처럼 보인다
- 예상과 달리 read cursor가 분리되어 있지 않다

이때 `fdinfo`는 "정말 같은 열린 객체를 공유 중인지"를 추론하는 단서가 된다.

### 3. epoll fd도 런타임 관측이 가능하다

event loop 장애에서는 "지금 이 epoll fd가 무엇을 감시하고 있는가"가 궁금할 때가 있다. `fdinfo`는 epoll target과 event mask 정보를 보여 주는 힌트를 제공할 수 있다.

- 어떤 target fd가 등록됐는가
- 어떤 event mask를 기대하는가
- rearm 누락처럼 보이는 문제를 간접 확인할 수 있다

즉 `/proc`만으로도 event loop ownership bug를 꽤 좁힐 수 있다.

### 4. deleted-open과 log rotation도 같이 본다

deleted-open file 문제는 path만 보면 숨는다. 하지만 `fd` 링크와 `fdinfo`를 함께 보면 다음이 보인다.

- `(deleted)` target
- 여전히 살아 있는 fd 번호
- offset이 계속 증가하는지 여부

그래서 "누가 계속 쓰고 있나"를 매우 빠르게 잡을 수 있다.

## 실전 시나리오

### 시나리오 1: 두 worker의 file read cursor가 이상하게 꼬인다

진단:

```bash
ls -l /proc/<pid>/fd
cat /proc/<pid>/fdinfo/<fd>
```

판단 포인트:

- 두 fd의 path는 같지만 offset도 함께 움직이는가
- `dup`/`fork` 공유 경로인지 의심할 만한가

### 시나리오 2: epoll loop가 뭔가 등록을 놓친 것 같다

진단:

```bash
ls -l /proc/<pid>/fd
cat /proc/<pid>/fdinfo/<epoll-fd>
```

판단 포인트:

- target fd가 실제로 epoll에 들어가 있는가
- 기대한 event mask가 보이는가
- `EPOLLONESHOT` 재arm bug처럼 보이는가

### 시나리오 3: disk usage가 안 줄어드는데 누가 deleted file을 잡고 있는지 모르겠다

진단:

```bash
lsof +L1
ls -l /proc/<pid>/fd | rg deleted
cat /proc/<pid>/fdinfo/<fd>
```

## 코드로 보기

### 가장 기본 확인

```bash
ls -l /proc/<pid>/fd
cat /proc/<pid>/fdinfo/<fd>
```

### mental model

```text
/proc/<pid>/fd
  -> what object/path does this fd point to?

/proc/<pid>/fdinfo
  -> what runtime state does this fd currently have?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `fd` 링크만 보기 | 빠르다 | 상태는 잘 안 보인다 | 1차 확인 |
| `fdinfo`까지 보기 | offset/flags/epoll 상태를 더 본다 | 해석에 객체별 차이가 있다 | 런타임 fd 디버깅 |
| `strace` 사용 | syscall 경로를 직접 본다 | 붙이는 비용이 있다 | 행동 원인 추적 |
| 코드 로그 추가 | 맥락이 풍부하다 | 장애 이후엔 늦을 수 있다 | 재현 가능한 버그 |

## 꼬리질문

> Q: `/proc/<pid>/fd`와 `/proc/<pid>/fdinfo`의 차이는?
> 핵심: 전자는 대상 객체 링크, 후자는 해당 fd의 런타임 상태 정보다.

> Q: `fdinfo`로 epoll 상태도 볼 수 있나요?
> 핵심: 객체 유형에 따라 추가 정보가 보일 수 있어서 event loop 디버깅에 유용하다.

> Q: deleted-open file 문제에도 도움이 되나요?
> 핵심: 그렇다. 어떤 fd가 숨은 inode를 잡고 있고 offset이 계속 움직이는지 볼 때 유용하다.

## 한 줄 정리

`/proc/<pid>/fdinfo`는 fd 문제를 "무엇을 열었나"에서 "지금 어떤 상태로 열려 있나"로 바꿔 보는 현장용 디버깅 도구다.
