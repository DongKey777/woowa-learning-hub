# Linux Process State Machine, Zombie, Orphan

> 한 줄 요약: 리눅스에서 프로세스가 어떻게 종료되고 회수되는지 알아야 좀비 프로세스, 고아 프로세스, 자식 회수 누락 장애를 설명할 수 있다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)


retrieval-anchor-keywords: linux process state zombie orphan basics, linux process state zombie orphan beginner, ready vs runnable vs sleeping linux, linux r s d state meaning, ready runnable sleeping difference, process state ready runnable sleeping 헷갈려요, sleeping blocked waiting difference, ps state r s d z what is, operating system basics, beginner operating system, 처음 배우는데 linux process state zombie orphan, linux process state zombie orphan 입문, linux process state zombie orphan 기초, what is linux process state zombie orphan, how to linux process state zombie orphan
> 관련 문서:
> - [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
> - [프로세스와 스레드](./README.md#프로세스와-스레드)
> - [프로세스 스케줄링](./README.md#프로세스-스케줄링)
> - [컨텍스트 스위칭, 데드락, Lock-free](./context-switching-deadlock-lockfree.md)
> - [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)

## 핵심 개념

리눅스 프로세스는 실행 중에 여러 상태를 오간다.

- `R` running or runnable
- `S` interruptible sleep
- `D` uninterruptible sleep
- `T` stopped or traced
- `Z` zombie

이 중 실무에서 자주 헷갈리는 것이 `zombie`와 `orphan`이다.

그 전에 beginner 문서에서 더 자주 섞이는 축을 먼저 분리하자.

## 용어 먼저 정리: `ready` vs `runnable` vs `sleeping`

운영체제 입문 자료를 읽다 보면 어떤 문서는 `ready`, 어떤 문서는 `runnable`, 또 어떤 문서는 `sleeping`이라고 써서 같은 상태처럼 보일 수 있다. 완전히 같은 말은 아니지만, beginner 단계에서는 아래처럼 정리하면 대부분의 질문이 풀린다.

| 용어 | beginner에서 먼저 읽는 뜻 | Linux 관찰에서 붙는 주의점 |
|------|--------------------------|----------------------------|
| `running` | 지금 CPU에서 실제로 실행 중 | `ps`의 `R`은 running만이 아니라 runnable까지 넓게 묶어 보일 수 있다 |
| `ready` | 실행 준비는 끝났고 CPU만 기다리는 상태 | beginner 설명용 표현이다 |
| `runnable` | `ready`와 거의 같은 뜻으로 많이 쓴다 | Linux에서는 "실행 중이거나 곧 실행 가능"처럼 더 넓게 읽힐 수 있다 |
| `sleeping` | CPU를 기다리는 게 아니라 외부 이벤트를 기다리는 상태 | Linux에서는 보통 `S`(interruptible sleep), `D`(uninterruptible sleep)처럼 다시 나뉜다 |

짧게 말하면 이렇다.

- 입문 문서에서는 `ready`와 `runnable`을 거의 동의어로 봐도 된다.
- `sleeping`은 대개 `blocked`/`waiting` 쪽이지, ready queue에 서 있는 상태가 아니다.
- Linux 상태 문자를 읽을 때는 `R`, `S`, `D`, `Z`처럼 좀 더 운영체제 관찰 친화적인 표기를 만난다.

예를 들어 웹 요청 worker가 DB 응답을 기다리면 beginner 설명으로는 `blocked` 또는 `sleeping` 쪽이고, DB 응답을 받은 뒤 CPU 차례만 기다리면 `ready/runnable` 쪽이다. "`sleeping`이면 그냥 쉬는 거예요?"라는 질문에는 "아니고, 보통은 I/O나 락이 풀리길 기다리는 중"이라고 답하는 편이 안전하다.

- `Zombie`는 **이미 종료됐지만 부모가 `wait()` 계열 호출로 회수하지 않은 자식 프로세스**
- `Orphan`은 **부모가 먼저 종료되어 부모를 잃은 자식 프로세스**

둘은 다르다.

- 좀비는 죽었는데 기록이 남아 있다
- 고아는 살아 있는데 보호자가 바뀐다

리눅스에서는 프로세스가 종료될 때 커널이 즉시 흔적을 완전히 지우지 않는다.
부모 프로세스가 자식의 종료 상태를 읽을 기회를 주기 위해, 최소한의 종료 정보는 잠시 남겨 둔다. 그게 좀비다.

고아 프로세스는 보통 `init` 또는 `systemd` 같은 1번 프로세스가 입양한다.
그래서 고아 자체는 보통 문제라기보다, 부모 종료 타이밍과 정리 책임이 꼬였다는 신호로 본다.

## 깊이 들어가기

### 1. 프로세스 상태 전이

전형적인 흐름은 이렇다.

```text
fork() -> ready/runnable -> running -> sleeping(blocked) <-> ready/runnable -> exit() -> zombie -> wait() -> fully reaped
```

여기서 `sleeping(blocked)`는 "CPU를 못 받아서 기다리는 상태"가 아니라 "외부 이벤트가 끝나야 다시 runnable이 될 수 있는 상태"다.

부모와 자식의 관계는 커널이 추적한다.

- 자식이 종료하면 커널은 `exit status`, `resource usage` 같은 최소 정보를 남긴다
- 부모는 `wait()`, `waitpid()`로 이를 회수한다
- 부모가 회수하지 않으면 자식은 좀비로 남는다

### 2. 왜 좀비가 생기는가

좀비는 메모리를 계속 차지하는 프로세스가 아니다.
대신 커널의 프로세스 테이블 엔트리와 PID를 점유한다.

즉 좀비가 많아지면 생기는 문제는 다음과 같다.

- PID 고갈 위험
- 프로세스 목록 오염
- 부모 프로세스가 자식 종료를 제대로 처리하지 못한다는 신호

좀비는 "CPU를 먹는 프로세스"가 아니라 "수거되지 않은 종료 기록"에 가깝다.

### 3. 왜 고아가 생기는가

부모가 먼저 종료되면 자식은 고아가 된다.

이때 커널은 고아를 방치하지 않고 1번 프로세스에게 재부모(reparent)한다.

```text
parent exits
  -> child becomes orphan
  -> init/systemd adopts child
```

그래서 고아 자체는 정상적인 커널 동작이다.
문제는 고아가 의도치 않게 생기는 구조, 즉 부모-자식 생명주기 설계가 불안정하다는 점이다.

### 4. backend 개발자가 알아야 하는 이유

실무에서 이 주제가 터지는 지점은 대개 다음과 같다.

- 웹 서버가 자식 프로세스를 띄우고 `wait()`를 안 해서 좀비가 쌓임
- 배치가 외부 명령을 실행하고 종료 회수 로직을 빠뜨림
- 컨테이너 안에서 PID 1이 시그널과 자식 회수를 제대로 처리하지 않음
- 프로세스 풀을 직접 관리하다가 종료 누락이 발생함

특히 Java/Spring 백엔드에서는 직접 `fork()`를 자주 쓰지 않아도,
빌드 툴, 이미지 처리, ffmpeg, Python helper, shell script 같은 외부 프로세스를 띄우는 순간 같은 문제가 생길 수 있다.

### 5. wait/reaping의 역할

부모는 자식이 종료되면 `wait()` 또는 `waitpid()`로 종료 상태를 읽어야 한다.

이 과정을 `reaping`이라고 부른다.

```c
pid_t pid = fork();
if (pid == 0) {
    _exit(0);
}

int status;
waitpid(pid, &status, 0);
```

`wait()`를 호출하지 않으면 자식은 좀비로 남는다.
반대로 부모가 비정상 종료하면 자식은 고아가 되고, 커널이 재부모한다.

### 6. PID 1의 의미

컨테이너 환경에서 특히 중요한 점은 PID 1이다.

## 깊이 들어가기 (계속 2)

- PID 1은 자식 회수 책임이 더 크다
- PID 1이 시그널 처리를 제대로 안 하면 종료가 비정상적으로 느려질 수 있다
- shell wrapper가 PID 1이 되면 `SIGTERM` 전달과 reaping이 꼬일 수 있다

그래서 경량 컨테이너에는 `tini`, `dumb-init` 같은 init 역할 도구를 두기도 한다.

## 실전 시나리오

### 시나리오 1: 좀비 프로세스가 쌓인다

증상:

- `ps`에서 `Z` 상태가 계속 보임
- PID 수가 예상보다 빠르게 증가함
- 프로세스는 죽었는데 목록에서 안 사라짐

진단:

```bash
ps -eo pid,ppid,stat,cmd | grep ' Z '
```

```bash
cat /proc/<pid>/status | grep -E 'State|PPid|Pid'
```

의심 포인트:

- 부모 프로세스가 `wait()`를 호출하지 않는다
- `SIGCHLD`를 무시하거나 잘못 처리한다
- 자식 종료 후에 수거 루프가 없다

### 시나리오 2: 부모가 죽고 자식만 남는다

증상:

- 부모 프로세스가 재시작되거나 종료됨
- 자식 프로세스는 계속 동작함
- 로그상으로는 부모-자식 관계가 끊겨 보임

확인:

```bash
pstree -ap <pid>
ps -o pid,ppid,stat,cmd -p <child_pid>
```

해석:

- `PPid`가 `1` 또는 `systemd` PID로 바뀌면 고아가 재부모된 것이다
- 의도된 백그라운드 워커일 수도 있지만, 보통은 종료 정책을 다시 봐야 한다

### 시나리오 3: 컨테이너가 종료되지 않는다

원인 중 하나는 PID 1이 자식 프로세스를 회수하지 않는 경우다.

```text
app shell(pid 1)
  -> worker child
  -> worker exits
  -> parent never wait()
  -> zombie remains
```

이 경우 `docker stop`이나 `SIGTERM` 이후에도 프로세스가 깔끔하게 안 끝날 수 있다.

## 코드로 보기

### 자식 회수 예시

```c
#include <sys/wait.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    pid_t pid = fork();

    if (pid == 0) {
        printf("child exits\n");
        _exit(42);
    }

    int status = 0;
    pid_t waited = waitpid(pid, &status, 0);
    if (waited < 0) {
        perror("waitpid");
        return 1;
    }

    if (WIFEXITED(status)) {
        printf("child exit code = %d\n", WEXITSTATUS(status));
    }

    return 0;
}
```

핵심은 부모가 종료 상태를 읽는다는 점이다.

### `SIGCHLD` 처리 예시

```c
#include <signal.h>
#include <sys/wait.h>

void on_sigchld(int signo) {
    (void)signo;
    while (waitpid(-1, NULL, WNOHANG) > 0) {
        // 종료된 자식을 모두 회수
    }
}
```

이 패턴은 자식이 여러 개인 서버나 데몬에서 자주 쓴다.

### 관찰 명령

```bash
# 상태와 부모 확인
ps -eo pid,ppid,stat,cmd | head

# 프로세스 트리 확인
pstree -ap <pid>

# 특정 프로세스 세부 상태 확인
cat /proc/<pid>/status

# 열린 파일과 현재 작업 디렉토리 확인
ls -l /proc/<pid>/fd
readlink /proc/<pid>/cwd
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 부모가 `wait()`로 직접 회수 | 명시적이고 안전하다 | 구현 누락 시 좀비 발생 | 일반적인 fork/worker 구조 |
| `SIGCHLD` 기반 비동기 회수 | 부모가 다른 일을 해도 된다 | 시그널 처리 난이도가 높다 | 데몬, 멀티 자식 서버 |
| reaper 프로세스 사용 | 책임 분리가 된다 | 구조가 복잡해진다 | 장기 실행 워커 풀 |
| PID 1 init 도구 사용 | 컨테이너 종료와 회수가 안정적이다 | 추가 바이너리/레이어 필요 | 컨테이너 환경 |

판단 기준은 단순하다.

- 자식 수가 적고 구조가 단순하면 `wait()`로 충분하다
- 자식 수가 많거나 오래 실행되면 `SIGCHLD`/reaper가 필요하다
- 컨테이너라면 PID 1 문제를 반드시 고려해야 한다

## 꼬리질문

### 🟢 Basic

**Q. 좀비 프로세스는 왜 메모리를 계속 먹지 않나요?**
- 의도: 좀비의 본질을 이해하는지 확인
- 핵심: 실행 코드는 끝났고, 커널이 PID와 종료 정보를 잠깐만 보관한다

**Q. 고아 프로세스는 무조건 문제인가요?**
- 의도: orphan과 zombie를 구분하는지 확인
- 핵심: 고아는 커널이 재부모하므로 정상 동작일 수 있다

### 🟡 Intermediate

**Q. 부모 프로세스가 `wait()`를 안 하면 왜 문제가 되나요?**
- 의도: reaping의 필요성 이해
- 핵심: 종료한 자식이 좀비로 남아 PID와 커널 엔트리를 점유한다

**Q. `ps`와 `/proc`로 어떤 정보를 먼저 봐야 하나요?**
- 의도: 실전 진단 순서 확인
- 핵심: `STAT`, `PPid`, `cmd`, `status`의 `State`와 `PPid`를 먼저 본다

### 🔴 Advanced

**Q. 컨테이너에서 PID 1이 특별한 이유는 무엇인가요?**
- 의도: 운영 환경에서 process lifecycle을 이해하는지 확인
- 핵심: 시그널 전달과 자식 회수 책임이 크고, init 역할이 없으면 좀비와 종료 지연이 생긴다

**Q. `SIGCHLD`를 쓰는 것과 주기적으로 `waitpid(WNOHANG)`를 도는 것의 차이는?**
- 의도: 종료 회수 전략의 trade-off 이해
- 핵심: 시그널은 즉시성, 폴링은 단순성이 있다. 다만 시그널 핸들러는 재진입성과 구현 복잡도가 문제다

## 한 줄 정리

리눅스에서 좀비는 "죽었지만 부모가 수거하지 않은 자식"이고, 고아는 "부모가 먼저 죽어 재부모된 자식"이다. 백엔드에서는 `wait()`/`SIGCHLD`/PID 1 처리 누락이 운영 장애로 이어질 수 있으니 `ps`, `/proc`, `pstree`로 빠르게 확인해야 한다.
