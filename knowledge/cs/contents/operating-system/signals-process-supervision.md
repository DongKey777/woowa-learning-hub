# Signals, Process Supervision

> 한 줄 요약: 프로세스는 스스로 잘 죽고 잘 회수돼야 하며, signals와 supervisor를 모르면 운영 중 좀비와 유실이 늘어난다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
> - [Linux 프로세스 상태 머신, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [eventfd, signalfd, Epoll Control-Plane Integration](./eventfd-signalfd-epoll-control-plane-integration.md)
> - [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)

> retrieval-anchor-keywords: signals, SIGTERM, SIGKILL, SIGCHLD, graceful shutdown, process supervision, PID 1, zombie reaping, signalfd, supervisor

## 핵심 개념

`signal`은 프로세스에 전달되는 비동기 알림이다.  
`process supervision`은 프로세스가 죽었을 때 다시 띄우거나, 정상 종료를 감시하는 운영 방식이다.

왜 중요한가:

- 장애가 났을 때 프로세스가 멈추지 않고 "조용히 죽는" 경우가 많다.
- PID 1이 signals를 제대로 처리하지 못하면 container 안에서 문제가 누적된다.
- graceful shutdown을 안 하면 요청 유실과 자원 누수가 생긴다.

## 깊이 들어가기

### 1. signal의 의미

대표적인 signal:

- `SIGTERM`: 정상 종료 요청
- `SIGKILL`: 강제 종료
- `SIGINT`: 인터럽트
- `SIGHUP`: 설정 재읽기/세션 종료 신호
- `SIGCHLD`: 자식 프로세스 종료 알림

signal은 즉시 실행이 아니라, 적절한 시점에 handler가 호출되는 비동기 이벤트다.
event loop 기반 서버에서는 이런 signal을 `signalfd`로 루프 안에서 처리하는 설계도 가능하다.

### 2. graceful shutdown

서버는 보통 `SIGTERM`을 받으면 아래를 해야 한다.

- 새 요청 수락 중단
- 기존 요청 마무리
- 커넥션 닫기
- 자식 프로세스 회수

이걸 안 하면 load balancer에서 빼기 전까지 새 요청이 계속 들어오거나, 종료 중 요청이 끊길 수 있다.

### 3. supervisor가 필요한 이유

단일 프로세스가 죽으면 서비스도 같이 죽는다.  
그래서 시스템은 보통 supervisor가 필요하다.

- `systemd`
- `s6`
- `supervisord`
- `Kubernetes`의 restart policy

supervisor는 프로세스 생명주기를 외부에서 통제한다.

### 4. PID 1 문제

container 내부의 PID 1은 특별하다.

- signal을 제대로 전달받아야 한다
- zombie를 reap해야 한다
- 일반 init처럼 child process 정리를 해야 한다

앱 프로세스를 PID 1로 직접 올리면 이 책임을 놓치기 쉽다.

## 실전 시나리오

### 시나리오 1: deployment 중 요청이 유실된다

`SIGTERM`을 받고 바로 종료하면 in-flight request가 끊긴다.  
해결은 graceful shutdown timeout과 readiness drain이다.

### 시나리오 2: container 안에 zombie가 쌓인다

자식 프로세스가 종료됐는데 부모가 `wait()`를 안 하면 zombie가 남는다.  
PID 1이 이를 회수하지 못하면 zombie가 누적된다.

진단:

```bash
ps -eo pid,ppid,stat,cmd | grep Z
pstree -ap <pid>
cat /proc/<pid>/status | grep -E 'State|PPid'
```

### 시나리오 3: supervisor가 재시작을 반복한다

프로세스가 에러를 내고 죽는데, supervisor가 무한 재시작하면 원인보다 증상이 더 커진다.  
이때는 backoff, exit code 정책, crash loop 제한이 필요하다.

## 코드로 보기

### Java 스타일 graceful shutdown

```java
Runtime.getRuntime().addShutdownHook(new Thread(() -> {
    // stop accepting new work
    // finish in-flight requests
    // flush metrics / logs
}));
```

### Shell에서 signal 보내기

```bash
kill -TERM <pid>
kill -KILL <pid>
```

### zombie 관찰

```bash
ps -eo pid,ppid,stat,cmd | awk '$3 ~ /Z/ { print }'
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 직접 프로세스 운영 | 단순 | 재시작/회수가 약함 | 아주 작은 배치 |
| supervisor 사용 | 재시작/모니터링 쉬움 | 운영 요소 증가 | 서버/daemon |
| container + orchestrator | 표준화 | signal/healthcheck 이해 필요 | 현대 서버 운영 |
| PID 1 직접 앱 실행 | 이미지 단순 | zombie/reaping 문제 | 거의 피하는 편이 좋음 |

## 꼬리질문

> Q: SIGTERM과 SIGKILL의 차이는 무엇인가?
> 의도: graceful shutdown과 강제 종료 차이 이해 여부 확인
> 핵심: SIGTERM은 협상, SIGKILL은 즉시 종료다.

> Q: zombie 프로세스는 왜 생기나?
> 의도: wait/reap 의미 이해 여부 확인
> 핵심: 자식 종료를 부모가 회수하지 않았기 때문이다.

> Q: PID 1이 특별한 이유는 무엇인가?
> 의도: container init 역할 이해 여부 확인
> 핵심: signal 처리와 child reaping 책임이 있다.

## 한 줄 정리

프로세스 운영은 실행만이 아니라 종료와 회수가 반이고, signals와 supervisor를 제대로 다뤄야 container와 서버가 깔끔하게 살아남는다.
