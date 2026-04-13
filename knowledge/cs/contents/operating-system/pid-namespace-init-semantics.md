# PID Namespace, Init Semantics

> 한 줄 요약: PID namespace에서 init은 단순 첫 프로세스가 아니라, 자식 회수와 signal 전달 책임을 지는 컨테이너의 사실상 운영자다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - [signals, process supervision](./signals-process-supervision.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [PID Limits, Process Table Exhaustion](./pid-limit-process-table-exhaustion.md)
> - [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)

> retrieval-anchor-keywords: PID namespace, PID 1, init semantics, subreaper, zombie reaping, signal forwarding, container init, orphan adoption

## 핵심 개념

PID namespace는 프로세스에게 다른 PID 시야를 제공한다. 그 안에서 PID 1은 일반 프로세스보다 더 특별한 의미를 가진다.

- `PID 1`: namespace 안의 첫 프로세스다
- `init semantics`: 자식 회수와 signal 처리 책임이 강한 성질이다
- `subreaper`: 자식의 자식을 대신 회수할 수 있는 주체다

왜 중요한가:

- container에서 PID 1이 signal을 무시하면 graceful shutdown이 깨질 수 있다
- zombie가 쌓이면 PID와 process table을 소모한다
- init 역할을 이해하지 못하면 restart와 termination이 꼬인다

이 문서는 [container, cgroup, namespace](./container-cgroup-namespace.md)와 [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)를 PID namespace 내부 시점으로 다시 본다.

## 깊이 들어가기

### 1. PID namespace는 "보이는 PID"를 바꾼다

호스트와 컨테이너는 같은 프로세스를 다른 PID로 볼 수 있다.

- 운영자는 PID 매핑을 헷갈릴 수 있다
- 진단은 namespace 경계를 따라가야 한다
- `nsenter`가 유용하다

### 2. PID 1은 reaping을 책임진다

컨테이너에서 PID 1은 자식이 종료되었을 때 반드시 수거해야 한다.

- `wait()`/`waitpid()`가 중요하다
- `SIGCHLD`를 제대로 받아야 한다
- 회수 실패 시 zombie가 쌓인다

### 3. signal forwarding이 누락되면 shutdown이 꼬인다

PID 1이 wrapper로만 존재하고 signal을 앱에 전달하지 않으면 종료가 지연될 수 있다.

- `SIGTERM`이 앱에 안 닿을 수 있다
- 종료가 타임아웃으로 바뀔 수 있다
- cleanup이 안 끝날 수 있다

### 4. subreaper는 중간 회수자다

컨테이너 내부에서 더 복잡한 프로세스 트리를 다루면 subreaper가 필요할 수 있다.

## 실전 시나리오

### 시나리오 1: 컨테이너가 종료되지 않고 hang처럼 보인다

가능한 원인:

- PID 1이 signal을 전달하지 않는다
- 자식 프로세스가 회수되지 않는다
- wrapper shell이 init 역할을 대신 못한다

진단:

```bash
ps -o pid,ppid,stat,comm -p 1
pstree -ap <container-pid>
cat /proc/1/status
```

### 시나리오 2: zombie가 계속 늘어난다

가능한 원인:

- PID 1이 wait를 안 한다
- child process tree가 복잡하다
- supervisor가 잘못 구성됐다

### 시나리오 3: 컨테이너 안 PID와 호스트 PID가 헷갈린다

가능한 원인:

- namespace 경계를 무시했다
- 호스트 PID를 컨테이너 PID로 오해했다
- 진단 대상이 틀렸다

## 코드로 보기

### PID 1 관찰

```bash
ps -p 1 -o pid,ppid,comm,stat
```

### namespace 진입 힌트

```bash
nsenter --target <host-pid> --pid --mount --uts --net sh
```

### init 의미의 간단한 의사 코드

```c
for (;;) {
    pid = waitpid(-1, &status, WNOHANG);
    if (pid > 0) {
        // reap child
    }
    forward_signals();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 앱을 직접 PID 1로 실행 | 단순하다 | reaping/signal 책임이 커진다 | 매우 단순한 서비스 |
| init wrapper 사용 | 종료와 회수가 안정적이다 | 레이어가 하나 늘어난다 | 일반 container |
| subreaper 도입 | 복잡한 트리를 관리한다 | 운영 복잡도 증가 | supervisor 구조 |

## 꼬리질문

> Q: PID namespace에서 PID 1이 왜 특별한가요?
> 핵심: 자식 회수와 signal 처리 책임이 있기 때문이다.

> Q: zombie는 왜 문제인가요?
> 핵심: PID 슬롯과 process table을 잠식하기 때문이다.

> Q: wrapper shell이 왜 위험할 수 있나요?
> 핵심: signal forwarding과 reaping을 제대로 안 하면 종료가 꼬인다.

## 한 줄 정리

PID namespace의 init은 컨테이너 내부의 수거 책임자이므로, signal forwarding과 reaping이 안 되면 종료와 회수가 모두 흔들린다.
