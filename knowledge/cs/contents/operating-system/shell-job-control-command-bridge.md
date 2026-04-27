# Shell Job-Control Command Bridge

> 한 줄 요약: `jobs`, `fg`, `bg`는 shell의 job table과 terminal foreground를 다루는 명령이고, `nohup`, `disown`는 "shell이 끝날 때 이 job을 어떻게 남길까" 쪽을 건드린다. 초보자는 `PGID`, `SID`, `TPGID`, `TTY` 네 칸만 같이 보면 shell job-control이 magic처럼 보이지 않는다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Session vs Process Group Primer](./session-vs-process-group-primer.md) 바로 다음에 읽는 beginner follow-up이다. shell에서 자주 치는 `jobs`, `fg`, `bg`, `nohup`, `disown`를 `PGID` / `SID` / `TTY` 변화와 연결해 "무엇이 shell bookkeeping이고, 무엇이 kernel-visible 구조인가"를 분리해 준다.

**난이도: 🟢 Beginner**

관련 문서:

- [Session vs Process Group Primer](./session-vs-process-group-primer.md)
- [signals, process supervision](./signals-process-supervision.md)
- [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [operating-system 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: operating-system-00061, shell job-control command bridge, shell job control commands, shell job control mental model, shell job table mental model, jobs fg bg nohup disown basics, jobs builtin vs ps, jobs -l pgid, fg bg tpgid, foreground process group shell command, background job controlling terminal, nohup vs disown, nohup not setsid, disown not detach, shell job table basics

## 먼저 잡는 멘탈 모델

먼저 command 이름보다 층을 나누면 훨씬 덜 헷갈린다.

| 층 | 대표 명령/필드 | 초보자용 질문 |
|---|---|---|
| shell job table | `jobs`, `fg`, `bg`, `disown` | "내 shell이 이 job을 지금 어떻게 기억하나?" |
| kernel-visible 구조 | `PGID`, `SID`, `TPGID`, `TTY` | "이 process는 어느 job/session/terminal에 붙어 있나?" |
| hangup 정책 | `nohup`, 일부 shell의 `disown -h` | "shell이 끝날 때 `SIGHUP`을 어떻게 보낼까?" |

핵심 문장은 이것이다.

> `jobs`에 보인다고 해서 커널 구조가 바뀐 것은 아니고, `nohup`을 쓴다고 해서 새 session이 생긴 것도 아니다.

즉 shell job-control 명령은 모두 "detach"가 아니다. 어떤 것은 shell의 메모를 바꾸고, 어떤 것은 foreground ownership을 바꾸고, 어떤 것은 hangup 정책만 바꾼다.

## 먼저 보는 네 칸

초보자가 직접 확인할 때는 아래 한 줄이 가장 효율적이다.

```bash
ps -o pid,ppid,pgid,sid,tpgid,tty,stat,cmd -p $$ -p <job-pid>
```

필드 감각은 이 정도면 충분하다.

| 필드 | 무엇을 뜻하나 | 초보자용 해석 |
|---|---|---|
| `PGID` | process group ID | 같은 job인가 |
| `SID` | session ID | 같은 terminal 작업판 안인가 |
| `TPGID` | terminal foreground process group ID | 지금 keyboard 입력의 주인이 누구인가 |
| `TTY` | 연결된 terminal | 아직 terminal에 붙어 있는가 |

같이 보면 좋은 shell 쪽 관찰 도구는 이것이다.

```bash
jobs -l
```

`jobs -l`은 shell의 job 번호와 PID를 보여 준다.
반면 `ps`는 커널이 보는 `PGID` / `SID` / `TTY` 구조를 보여 준다.

## 명령별로 무엇이 바뀌나

| 명령 | shell이 하는 일 | 초보자가 `ps`/`jobs`에서 보게 되는 변화 | 보통 그대로인 것 |
|---|---|---|---|
| `jobs` | 현재 shell의 job table을 읽어 보여 준다 | `jobs -l` 출력만 생긴다 | `PGID`, `SID`, `TPGID`, `TTY`는 그대로다 |
| `bg %1` | stopped job에 `SIGCONT`를 보내고 background로 둔다 | `STAT`가 `T`에서 `S`/`R` 쪽으로 바뀔 수 있다. `TPGID`는 보통 shell 쪽에 남는다 | 같은 `PGID`, 같은 `SID`, 같은 `TTY` |
| `fg %1` | 그 job의 `PGID`를 foreground로 올리고 shell은 기다린다 | 실행 중에는 `TPGID == job의 PGID`가 된다 | 같은 `PGID`, 같은 `SID`, 같은 `TTY` |
| `nohup cmd ...` | command가 `SIGHUP`을 무시하도록 시작하고, 필요하면 출력을 `nohup.out` 등으로 돌린다 | output redirection이 생길 수 있다. process가 shell 종료 후에도 남기 쉬워진다 | 새 `SID`가 생기지 않는 경우가 많고, `TTY`도 바로 `?`로 바뀌지 않는다 |
| `disown %1` | shell job table에서 그 job을 지운다 | `jobs`에서는 사라지지만 `ps`에서는 process가 그대로 보인다 | 같은 `PGID`, 같은 `SID`, 같은 `TTY` |

여기서 초보자가 꼭 기억할 포인트:

- `fg` / `bg`의 핵심 변화는 대개 `TPGID`와 실행 상태(`STAT`)다.
- `nohup`의 핵심 변화는 대개 `SIGHUP` 처리와 output redirection이다.
- `disown`의 핵심 변화는 shell job table이다.
- `PGID`와 `SID`는 위 명령들 때문에 자주 바뀌지 않는다.

## 작은 그림으로 보면

예를 들어 terminal 한 탭에서 shell이 아래 상태라고 하자.

```text
shell: PID=5000 PGID=5000 SID=5000 TTY=pts/3
job  : PID=6200 PGID=6200 SID=5000 TTY=pts/3
```

여기서 중요한 감각은:

- shell과 job은 **같은 `SID`**에 있다
- job은 shell과 **다른 `PGID`**를 가질 수 있다
- foreground owner는 `TPGID`가 가리킨다

### 1. `Ctrl-Z` 후 `jobs`

foreground에서 돌던 job을 `Ctrl-Z`로 멈추면 보통 이런 그림이 된다.

```text
job STAT  -> T (stopped)
TPGID     -> shell의 PGID로 돌아감
jobs -l   -> [1]+ 6200 Stopped ...
```

이 시점의 핵심은 job이 "없어진 것"이 아니라, **같은 session / 같은 TTY 안에서 멈춘 background candidate**가 되었다는 점이다.

### 2. `bg %1`

`bg %1`는 그 stopped job을 다시 돌리지만 foreground로 올리지는 않는다.

```text
job STAT  -> T 에서 S/R 쪽으로 바뀔 수 있음
TPGID     -> 여전히 shell의 PGID
PGID/SID  -> 그대로
```

즉 `bg`는 "새로운 job을 만드는 것"보다 **기존 job을 다시 돌리되 keyboard ownership은 shell에 남겨 두는 것**에 가깝다.

### 3. `fg %1`

`fg %1`는 그 job을 다시 foreground owner로 만든다.

```text
TPGID -> job의 PGID
```

실행 중에는 terminal-generated signal인 `Ctrl-C`, `Ctrl-Z`가 다시 그 job의 process group으로 간다.
즉 `fg`의 본질은 "job을 새로 만드는 것"이 아니라 **terminal foreground token을 job 쪽으로 넘기는 것**이다.

### 4. `nohup cmd &`

초보자가 가장 많이 오해하는 부분이다.

```text
nohup sleep 300 &
```

이 명령은 보통:

- shell의 background job처럼 시작될 수 있고
- `SIGHUP`에는 덜 민감해지며
- stdout/stderr가 `nohup.out`으로 빠질 수 있다

하지만 자주 **안 바뀌는 것**도 있다.

- 새 `SID`가 생기지 않을 수 있다
- `TTY`가 그대로일 수 있다
- background job이 terminal input을 읽으려 하면 여전히 job-control signal을 만날 수 있다

즉 `nohup`은 "진짜 detach"라기보다 **hangup survival 정책**에 더 가깝다.

### 5. `disown %1`

`disown`은 bash/zsh에서 자주 보는 shell builtin이다.

## 작은 그림으로 보면 (계속 2)

```text
disown %1
jobs      -> 그 job이 사라짐
ps        -> process는 여전히 존재
```

초보자 관점에서 가장 중요한 사실은 이것이다.

> `disown`은 대개 shell이 그 job을 기억하는 방식을 바꾸고, 커널이 본 `PGID` / `SID` / `TTY`를 새로 만들지는 않는다.

그래서 `disown` 뒤에 `jobs`만 보면 "없어졌네?"라고 느낄 수 있지만, `ps`로 보면 같은 process가 계속 살아 있다.

## `nohup`과 `disown`을 헷갈리지 않는 법

| 질문 | `nohup` | `disown` |
|---|---|---|
| 주 타깃 | process의 `SIGHUP` 반응 | shell의 job table |
| `jobs` 출력 | 보일 수 있다 | 보통 사라진다 |
| 새 session 생성 | 아니다 | 아니다 |
| `TTY=?` 보장 | 아니다 | 아니다 |
| "shell 종료 후 남게 만들기"에 도움 | 그렇다 | shell/옵션에 따라 일부 도움 |

한 줄로 줄이면:

- `nohup`은 "죽지 말라" 쪽
- `disown`은 "shell이 이 job을 놓아 주자" 쪽

둘 다 흔히 **`setsid()`의 대체제가 아니다**.

## 자주 헷갈리는 포인트

- "`jobs`에 안 보이면 process도 끝난 것이다" -> 아니다. `jobs`는 현재 shell의 job table이고, `ps`는 시스템의 process view다.
- "`nohup`을 쓰면 terminal과 완전히 끊긴다" -> 보통 아니다. `SID`와 `TTY`가 그대로일 수 있다.
- "`disown`을 하면 새 session이 생긴다" -> 아니다. shell bookkeeping이 주로 바뀐다.
- "`bg`는 process를 다른 group으로 옮긴다" -> 보통 아니다. 같은 `PGID`를 background 상태로 다시 돌릴 뿐이다.
- "`fg`는 PID나 PGID를 새로 만든다" -> 아니다. foreground ownership(`TPGID`)이 핵심이다.
- "`disown`은 모든 shell에서 같다" -> 아니다. 특히 option 의미는 shell마다 다를 수 있다. beginner는 먼저 "job table에서 지운다"는 공통 감각부터 잡는 편이 안전하다.

## Self-check (자가 점검 4문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. `jobs` 결과와 `ps` 결과가 왜 다를 수 있는지(shell job table vs 시스템 process view) 설명할 수 있는가?
   힌트: `jobs`는 현재 shell이 추적하는 작업만 보여 주고, `ps`는 시스템 전체 프로세스 관점이라 범위가 다르다.
2. `fg`/`bg`의 핵심 변화가 새 PID 생성이 아니라 foreground ownership(`TPGID`) 전환이라는 점을 말할 수 있는가?
   힌트: `fg`/`bg`는 기존 작업을 앞이나 뒤로 보내는 것이지 새 프로세스를 만드는 명령이 아니다.
3. `nohup`과 `disown`을 "SIGHUP 반응 정책"과 "shell bookkeeping"으로 분리해 설명할 수 있는가?
   힌트: `nohup`은 종료 신호 반응을 바꾸고, `disown`은 shell이 그 작업을 목록에서 관리할지 말지를 바꾼다.
4. terminal에서 완전히 분리된 실행이 필요할 때 `nohup`/`disown`만으로 충분하지 않을 수 있다는 점을 이해하고 `setsid()` 계열 후속 문서를 찾을 수 있는가?
   힌트: hangup 처리만 바꿔도 controlling terminal 관계가 남을 수 있으니 session 분리까지 생각해야 할 때가 있다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`jobs`/`fg`/`bg` 뒤의 `PGID`/`SID`/foreground process group 그림을 다시 고정하고 싶으면": [Session vs Process Group Primer](./session-vs-process-group-primer.md)
> - "`setsid()`까지는 알겠는데 그다음 daemonization 체크리스트가 왜 붙는지 보고 싶으면": [Daemonization Checklist Primer](./daemonization-checklist-primer.md)
> - "shell 명령 말고 launch 시점 `POSIX_SPAWN_SETPGROUP`/signal mask로 연결하고 싶으면": [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
> - "`SIGHUP`/`SIGTERM`/supervisor까지 확장해서 보고 싶으면": [signals, process supervision](./signals-process-supervision.md)
> - "`terminal에 붙어 있음`이 출력 모드와 prompt에 주는 차이를 알고 싶으면": [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

`jobs` / `fg` / `bg` / `nohup` / `disown`를 한 덩어리로 외우지 말고, "shell job table 변화인가, `TPGID` foreground 변화인가, `SIGHUP` survival 정책인가"로 먼저 나누면 `PGID` / `SID` / `TTY` 그림이 훨씬 또렷해진다.
