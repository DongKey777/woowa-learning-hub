---
schema_version: 3
title: Session vs Process Group Primer
concept_id: operating-system/session-vs-process-group-primer
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 73
review_feedback_tags:
- session-vs-process
- group
- controlling-terminal
- setsid-setpgid
aliases:
- session vs process group
- controlling terminal
- setsid setpgid
- shell job control
- terminal signal job group
- foreground process group
intents:
- definition
- comparison
linked_paths:
- contents/operating-system/posix-spawn-attributes-primer.md
- contents/operating-system/shell-job-control-command-bridge.md
- contents/operating-system/daemonization-checklist-primer.md
- contents/operating-system/signals-process-supervision.md
- contents/operating-system/pty-raw-mode-echo-basics.md
expected_queries:
- session과 process group, controlling terminal은 어떻게 달라?
- terminal signal을 같이 받는 job 묶음은 process group이야?
- setsid와 setpgid는 무엇을 떼거나 묶는 system call이야?
- shell job control에서 foreground process group은 어떤 의미야?
contextual_chunk_prefix: |
  이 문서는 process group을 terminal signal을 함께 받을 job 묶음으로, session을 그런 process group을
  담는 더 큰 runtime/terminal boundary로, controlling terminal을 session에 붙은 keyboard/screen
  entrance로 설명한다.
---
# Session vs Process Group Primer

> 한 줄 요약: process group은 terminal signal을 같이 받을 "job 묶음"이고, session은 그런 process group들을 담는 더 큰 terminal/runtime 경계이며, controlling terminal은 그 session에 붙은 키보드/화면 입구다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md) 다음에 읽는 beginner bridge다. `process group`, `session`, `controlling terminal`, `setsid()`, `setpgid()`가 job-control 문맥에서 한꺼번에 나오며 섞일 때, "무엇을 묶고 무엇을 떼는가"를 먼저 분리해 준다.

**난이도: 🟢 Beginner**

관련 문서:

- [Shell Job-Control Command Bridge](./shell-job-control-command-bridge.md)
- [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Process Spawn API Comparison: `fork()`, `vfork()`, `posix_spawn()`, `exec()`, `clone()`](./process-spawn-api-comparison.md)
- [signals, process supervision](./signals-process-supervision.md)
- [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [operating-system 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: session vs process group primer, session이 뭐예요, process group이 뭐예요, session vs process group 뭐가 달라요, controlling terminal 뭐예요, foreground process group 뭐예요, ctrl-c를 누르면 왜 pipeline 전체가 멈춰요, ctrl-c가 어디로 가요, setpgid와 setsid 차이, setpgid랑 setsid가 헷갈려요, 터미널에서 분리된다는 게 뭐예요, 처음 배우는데 session process group, job control basics, process group job control, what is session vs process group

## 이 문서가 먼저 맞는 질문

아래처럼 "용어를 처음 묻는 질문"이면 shell/job-control deep dive보다 이 문서가 먼저다.

- "`session`이 뭐예요?"
- "`process group`이 뭐예요?"
- "`session`과 `process group`은 뭐가 달라요?"
- "`Ctrl-C`를 누르면 왜 pipeline 전체가 같이 멈춰요?"
- "`setpgid()`와 `setsid()`가 왜 따로 있죠?"
- "terminal에서 분리된다는 말이 정확히 뭐예요?"

반대로 `nohup`, `fg`, `bg`, `disown` 같은 shell 명령 차이나 daemonization checklist가 궁금하면 관련 follow-up 문서로 내려가는 편이 안전하다.

## 먼저 잡는 멘탈 모델

먼저 용어보다 그림을 잡자.

```text
terminal window (/dev/pts/3)
  -> one controlling terminal for a session

session
  -> process group A: shell
  -> process group B: foreground job, 예: vim
  -> process group C: background job, 예: sleep 100 &
```

초보자용 mental model은 이렇게 충분하다.

| 용어 | 무엇을 묶나 | 초보자용 감각 |
|---|---|---|
| process | 실행 중인 프로그램 하나 | PID 하나 |
| process group | signal을 같이 받을 process 묶음 | shell의 "job"에 가까움 |
| session | process group들을 담는 더 큰 실행 경계 | 로그인 shell / terminal 작업판 |
| controlling terminal | session에 붙은 terminal 장치 | `Ctrl-C`, `Ctrl-Z`가 들어오는 입구 |
| foreground process group | terminal 앞자리에 있는 process group | terminal 입력과 job-control signal의 현재 대상 |

가장 중요한 문장은 이것이다.

> `Ctrl-C`는 "부모와 자식 전체"에 가는 것이 아니라, controlling terminal의 **foreground process group**에 간다.

그래서 process tree, process group, session을 같은 그림으로 뭉개면 job-control 설명이 계속 흐려진다.

## 용어를 한 번에 비교하기

| 질문 | 답이 되는 개념 | 예 |
|---|---|---|
| 누가 누구의 자식인가 | parent/child process | shell이 `grep`을 실행했다 |
| `Ctrl-C`를 같이 받을 묶음은 누구인가 | process group | `cat file | grep foo` pipeline 전체 |
| 이 terminal 작업판 안의 job 묶음들은 어디에 속하나 | session | 로그인 shell이 만든 terminal session |
| keyboard input은 지금 누구에게 가나 | foreground process group | 현재 foreground인 `vim` 또는 pipeline |
| terminal과 아예 떨어져 daemon처럼 시작하려면 | `setsid()` | old terminal/session에서 분리 |
| 같은 session 안에서 새 job 묶음을 만들려면 | `setpgid()` | shell이 pipeline children을 같은 PGID로 묶음 |

여기서 parent/child 관계는 **생성 관계**고, process group/session은 **signal과 terminal 제어를 위한 묶음**이다.
같은 부모 밑 child들이라도 서로 다른 process group에 있을 수 있고, 같은 process group 안에 pipeline의 여러 process가 같이 있을 수 있다.

## process group: job-control의 기본 단위

process group은 "같이 signal을 받을 팀"이라고 보면 된다.

대표 예시는 shell pipeline이다.

```sh
cat access.log | grep ERROR | less
```

이 pipeline에는 process가 여러 개 있다.

- `cat`
- `grep`
- `less`

하지만 사용자는 이것을 하나의 foreground job처럼 다룬다.

- `Ctrl-C`를 누르면 pipeline 전체가 멈추길 기대한다
- `Ctrl-Z`를 누르면 pipeline 전체가 suspend되길 기대한다
- `fg`, `bg`, `jobs`도 job 단위로 보이길 기대한다

그래서 shell은 이런 children을 같은 process group에 넣는다.
이때 process group id를 `PGID`라고 부른다.

```text
PGID 4200
  PID 4200 cat
  PID 4201 grep
  PID 4202 less
```

process group의 핵심은 "누가 부모인가"보다 "terminal-origin signal을 누구와 같이 받는가"다.

## session: process group들을 담는 더 큰 경계

session은 process group보다 한 단계 큰 묶음이다.

초보자에게는 보통 이렇게 잡으면 된다.

```text
one login shell or terminal tab
  -> one session
  -> many process groups/jobs inside it
```

session은 다음을 설명할 때 등장한다.

- terminal 하나에 여러 foreground/background job이 매달리는 이유
- daemon이 terminal에서 떨어져 나갈 때 `setsid()`가 나오는 이유
- process group은 같거나 달라질 수 있어도, job-control은 보통 같은 session 안에서 이뤄지는 이유

session id를 `SID`라고 부른다.
처음에는 `SID`를 "이 process가 어느 terminal 작업판에 속하는가" 정도로 읽으면 충분하다.

주의할 점:

- session은 parent/child tree가 아니다
- process group보다 큰 job-control 경계다
- 하나의 session 안에는 여러 process group이 있을 수 있다
- process는 한 번에 하나의 session에만 속한다

## controlling terminal: session에 붙은 terminal 입구

controlling terminal은 session에 연결된 terminal 장치다.

예를 들어 terminal tab에서 shell을 열면, 그 shell session은 `/dev/pts/3` 같은 terminal을 controlling terminal로 가질 수 있다.
그 terminal에는 "지금 foreground인 process group"이 하나 있다.

```text
controlling terminal: /dev/pts/3
foreground process group: PGID 4200
```

terminal driver는 keyboard에서 온 job-control 입력을 foreground process group 쪽으로 보낸다.

| 입력 | 보통 전달되는 signal | 대상 |
|---|---|---|
| `Ctrl-C` | `SIGINT` | foreground process group |
| `Ctrl-\` | `SIGQUIT` | foreground process group |
| `Ctrl-Z` | `SIGTSTP` | foreground process group |
| background job이 terminal에서 read | `SIGTTIN` | 해당 background process group |
| background job이 terminal에 write | `SIGTTOU` 가능 | 설정에 따라 해당 background process group |

즉 controlling terminal은 "process 하나에 붙은 stdin"보다 넓은 개념이다.
terminal에는 session이 붙고, 그 안에서 foreground process group이 바뀐다.

## `setpgid()`: 같은 session 안에서 job 묶음을 조정한다

`setpgid()`는 process의 process group을 정하는 호출이다.

초보자용으로는 이렇게 읽으면 된다.

```text
setpgid() = 이 process를 어떤 job/process-group에 넣을지 정한다
```

대표 사용처는 shell이다.

```text
shell
  -> fork child A
  -> fork child B
  -> setpgid(A, A)      # A를 새 process group leader로 둠
  -> setpgid(B, A)      # B를 A의 process group에 합침
  -> terminal foreground를 PGID A로 바꿈
```

`setpgid()`가 하는 일:

- 새 process group을 만들 수 있다
- child를 기존 process group에 넣을 수 있다
- pipeline을 하나의 job처럼 묶을 수 있다

`setpgid()`가 하지 않는 일:

- 새 session을 만들지 않는다
- terminal에서 자동으로 떨어뜨리지 않는다
- file descriptor를 닫지 않는다
- signal handler나 signal mask를 정리하지 않는다

그래서 `setpgid()`는 "daemon detach"보다 "job 묶기"에 가깝다.

## `setsid()`: 새 session을 만들고 terminal에서 떨어진다

`setsid()`는 훨씬 큰 경계를 바꾸는 호출이다.

초보자용으로는 이렇게 읽으면 된다.

```text
setsid() = 새 session을 만들고, 새 process group leader가 되며,
           기존 controlling terminal과 떨어진 상태로 시작한다
```

주요 효과:

- caller가 새 session의 session leader가 된다
- caller가 새 process group의 process group leader가 된다
- 새 session에는 처음에 controlling terminal이 없다

그래서 daemon화 설명에서 `setsid()`가 자주 나온다.
목적은 "부모 shell의 terminal job-control 영향에서 벗어나 독립 실행 경계를 만들기"다.

주의할 점:

- `setsid()`는 child를 새로 만들지 않는다
- `setsid()`는 fd를 자동으로 닫지 않는다
- `setsid()`는 `SIGTERM`을 무시하게 만들지 않는다
- caller가 이미 process group leader이면 실패할 수 있어, daemon 패턴에서 `fork()` 후 child가 `setsid()`를 호출하는 그림이 자주 나온다

이 마지막 제약은 beginner 단계에서 세부 race까지 외울 필요는 없다.
"`setsid()`는 terminal/session 경계를 새로 만들기 때문에 `setpgid()`보다 더 큰 작업"이라고 기억하면 된다.

## `setpgid()`와 `setsid()` 비교

| 구분 | `setpgid()` | `setsid()` |
|---|---|---|
| 바꾸는 핵심 | process group | session + process group |
| 주된 목적 | job-control 묶음 만들기 | terminal/session에서 분리 |
| 새 session 생성 | 아니다 | 그렇다 |
| controlling terminal 분리 | 아니다 | 기존 terminal과 분리됨 |
| shell pipeline과의 관계 | children을 같은 job으로 묶을 때 사용 | 보통 pipeline 묶음에는 과하다 |
| daemon과의 관계 | 충분하지 않다 | daemon detach 설명에 자주 등장 |
| fd 정리 | 하지 않는다 | 하지 않는다 |
| signal mask/default 정리 | 하지 않는다 | 하지 않는다 |

한 줄로 줄이면 이렇다.

- `setpgid()`: 같은 session 안에서 "이 process는 어느 job인가"를 정한다
- `setsid()`: "새 terminal/session 경계로 나가겠다"를 정한다

## `posix_spawnattr_t`와는 어떻게 이어지나

[posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)에서 본 `POSIX_SPAWN_SETPGROUP`은 이 문서의 `setpgid()` 쪽 감각과 연결된다.

```text
posix_spawn file actions = child fd 배선
posix_spawn attrs        = child process 시작 상태
POSIX_SPAWN_SETPGROUP   = child의 process group 시작 상태
```

하지만 beginner가 조심할 점이 있다.

- process group 설정은 session 생성과 다르다
- process group 설정은 controlling terminal foreground 변경과 다르다
- process group 설정은 signal mask/default 설정과 다르다

예를 들어 shell은 child를 process group으로 묶은 뒤, 필요하면 terminal의 foreground process group을 바꾼다.
그 foreground 전환은 `tcsetpgrp()` 같은 terminal-control 쪽 작업이지, 단순히 process group만 만든다고 자동으로 일어나는 것은 아니다.

즉 `POSIX_SPAWN_SETPGROUP`은 "이 child를 어느 job 묶음에 둘까"에 가깝고, "`setsid()`처럼 terminal에서 완전히 떼어 내라"는 말과는 다르다.

## 작은 예제로 묶어 보기

### 1. foreground pipeline

```text
user runs: cat log | grep ERROR

shell session: SID 1000
controlling terminal: /dev/pts/3

process group 1000
  PID 1000 shell

process group 2100
  PID 2100 cat
  PID 2101 grep
```

foreground 실행 동안 terminal의 foreground process group은 `2100`이다.

```text
Ctrl-C
  -> terminal driver
  -> SIGINT to PGID 2100
  -> cat and grep see SIGINT
  -> shell itself does not have to die
```

이게 "terminal signal은 process tree가 아니라 foreground process group으로 간다"는 말의 실제 의미다.

### 2. background job

```sh
sleep 100 &
```

background job도 process group을 가질 수 있지만, terminal의 foreground process group은 shell 쪽에 남아 있다.

```text
foreground PGID: shell
background PGID: sleep job
```

그래서 background job은 keyboard input의 현재 주인이 아니다.
background process가 terminal input을 읽으려 하면 `SIGTTIN` 같은 job-control signal을 만날 수 있다.

### 3. daemon-style detach

daemon-style detach 그림은 다르다.

```text
parent shell session
  -> fork child
  -> child calls setsid()
  -> child is now in a new session with no controlling terminal
```

여기서는 "같은 terminal 안에서 job을 묶기"가 목적이 아니다.
old terminal/session 영향에서 벗어나 새 실행 경계를 만드는 것이 핵심이다.

## 자주 헷갈리는 포인트

### 1. process group은 부모-자식 관계가 아니다

아니다.

- 부모-자식은 누가 누구를 만들었는가
- process group은 signal/job-control 묶음이 무엇인가

pipeline의 여러 process는 같은 parent에서 나왔을 수 있지만, 중요한 것은 같은 process group으로 묶였다는 점이다.

### 2. 새 process group이면 daemon이 된 것이다

아니다.

새 process group은 job 묶음을 새로 만든 것이다.
daemon처럼 terminal/session에서 떨어지는 감각은 `setsid()` 쪽이 더 직접적이다.

### 3. `setsid()`는 `setpgid(0, 0)`의 긴 이름이다

아니다.

- `setpgid(0, 0)`: process group만 조정
- `setsid()`: 새 session을 만들고 새 process group leader가 되며 controlling terminal이 없는 상태가 됨

크기가 다른 작업이다.

### 4. `exec()`를 하면 session/process group이 초기화된다

아니다.

`exec()`는 프로그램 이미지를 바꾸지만, process group이나 session을 자동으로 새로 만들지는 않는다.
그래서 launch 전에 정한 process group / session 감각이 `exec()` 이후 target program에도 이어질 수 있다.

### 5. signal mask/default와 process group은 같은 문제다

아니다.

- signal mask/default: signal을 받았을 때 이 process가 어떤 상태인가
- process group: terminal이나 `kill(-pgid, sig)`가 signal을 어느 묶음에 보낼 것인가

그래서 `posix_spawnattr_t`에서 process group, signal mask, signal default가 같이 나오더라도 같은 knob로 읽으면 안 된다.

## 관찰할 때 보는 필드

실제 시스템에서 감을 잡을 때는 PID 하나만 보지 말고 아래 필드를 같이 본다.

```bash
ps -o pid,ppid,pgid,sid,tpgid,tty,stat,comm -p <pid>
```

| 필드 | 읽는 의미 |
|---|---|
| `PID` | 이 process 자체 |
| `PPID` | 부모 process |
| `PGID` | 이 process가 속한 process group |
| `SID` | 이 process가 속한 session |
| `TPGID` | terminal의 foreground process group |
| `TTY` | 연결된 terminal |

beginner 디버깅 질문은 보통 이 순서면 충분하다.

1. 이 process의 부모는 누구인가
2. 이 process의 `PGID`는 무엇인가
3. 같은 job이어야 하는 process들이 같은 `PGID`인가
4. 이 process의 `SID`와 `TTY`는 무엇인가
5. terminal의 `TPGID`가 내가 생각한 foreground job과 맞는가

## 꼬리질문

> Q: `Ctrl-C`는 부모 process와 모든 child에게 가나요?
> 핵심: 아니다. controlling terminal의 foreground process group에 전달된다고 먼저 이해해야 한다.

> Q: `setpgid()`와 `setsid()` 중 shell pipeline을 한 job으로 묶는 데 더 직접적인 것은 무엇인가요?
> 핵심: `setpgid()`다. 같은 session 안에서 process group을 조정하는 작업이기 때문이다.

> Q: `setsid()`를 호출하면 fd leak이나 stdout redirect 문제가 자동으로 해결되나요?
> 핵심: 아니다. session/terminal 경계와 fd table 정리는 다른 문제다. fd hygiene는 별도로 봐야 한다.

## Self-check (자가 점검 4문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. parent/child 관계(`PPID`)와 job-control 묶음(`PGID`)이 서로 다른 축임을 예시로 설명할 수 있는가?
   힌트: 부모-자식은 생성 계보이고, process group은 함께 신호를 받는 작업 묶음이라 기준이 다르다.
2. `setpgid()`와 `setsid()` 중 "같은 session 안 job 묶기"와 "terminal에서 떨어진 새 session 시작"을 각각 어디에 쓰는지 구분할 수 있는가?
   힌트: `setpgid()`는 기존 세션 안에서 그룹만 바꾸고, `setsid()`는 터미널에서 떨어진 새 세션을 시작한다.
3. `Ctrl-C` 전달 경로를 "foreground process group(`TPGID`)" 기준으로 설명할 수 있는가?
   힌트: 터미널은 개별 PID가 아니라 현재 foreground process group 전체에 `SIGINT`를 보낸다고 보면 된다.
4. `exec()` 이후에도 session/process group 설정이 그대로 이어질 수 있다는 점을 기억하고 launch 시점 정책을 세울 수 있는가?
   힌트: `exec()`는 프로그램 이미지를 바꿔도 job-control 소속은 보통 유지되므로 시작 전에 구조를 정해야 한다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "같은 그림을 shell 명령 `jobs`/`fg`/`bg`/`nohup`으로 이어 보고 싶으면": [Shell Job-Control Command Bridge](./shell-job-control-command-bridge.md)
> - "`setsid()` 다음에 왜 stdio redirection, `umask`, `chdir()`가 또 필요한지 붙여 보고 싶으면": [Daemonization Checklist Primer](./daemonization-checklist-primer.md)
> - "`POSIX_SPAWN_SETPGROUP`를 launch 시점 knob로 다시 연결하고 싶으면": [posix_spawn Attributes Primer](./posix-spawn-attributes-primer.md)
> - "`SIGHUP`/`SIGTERM`/supervisor까지 signal 운영 감각을 넓히고 싶으면": [signals, process supervision](./signals-process-supervision.md)
> - 운영체제 입문 primer 묶음으로 돌아가려면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

job-control 용어가 섞이면 "parent tree는 생성 관계, process group은 signal을 같이 받을 job 묶음, session은 그 job 묶음들을 담는 terminal/runtime 경계, controlling terminal은 foreground process group에 입력과 terminal signal을 보내는 입구"라는 순서로 다시 나누면 된다.
