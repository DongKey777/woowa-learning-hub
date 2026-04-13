# FD Exhaustion, ulimit, Diagnostics

> 한 줄 요약: fd exhaustion은 "파일이 많다"가 아니라, 프로세스와 시스템이 더 이상 열린 자원을 받지 못해 서버 전체를 흔드는 운영 장애다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)

> retrieval-anchor-keywords: ulimit -n, RLIMIT_NOFILE, EMFILE, ENFILE, file-max, file-nr, lsof, /proc/pid/fd, too many open files

## 핵심 개념

Linux에서 fd는 열린 파일, 소켓, 파이프, 장치 같은 커널 객체를 가리키는 숫자다. fd exhaustion은 이 숫자가 너무 많아져 더 이상 새 fd를 열 수 없는 상태다.

- `EMFILE`: 프로세스 자신의 fd 한도를 넘었다
- `ENFILE`: 시스템 전체 fd 테이블 한도에 걸렸다
- `RLIMIT_NOFILE`: 프로세스별 fd 제한이다
- `fs.file-max`: 시스템 전체 파일 핸들 상한이다

왜 중요한가:

- accept가 실패하면 새 연결을 못 받는다
- 로그를 못 열면 장애 분석이 더 어려워진다
- 작은 leak이 누적되면 시간이 지나서 갑자기 장애가 된다

이 문서는 [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)에서 다룬 fd 개념을, 실제 고갈 진단과 복구 절차로 좁혀서 정리한다.

## 깊이 들어가기

### 1. 프로세스 한도와 시스템 한도는 다르다

fd 고갈에는 두 층이 있다.

- 프로세스가 자기 `ulimit -n`을 넘는 경우
- 시스템 전체가 파일 객체를 더 못 받는 경우

즉 하나의 프로세스만 문제가 될 수도 있고, 노드 전체가 동시에 위험해질 수도 있다.

### 2. fd leak은 메모리 leak보다 늦게 드러난다

fd leak은 종종 천천히 진행된다.

- connection이 닫히지 않는다
- retry path에서 소켓이 남는다
- 파일 close 누락이 있다
- logging handler가 descriptor를 반복 생성한다

그래서 메모리 leak처럼 눈에 띄지 않다가, 어느 순간 `EMFILE`로 터진다.

### 3. fd exhaustion은 accept 장애로 바로 이어진다

서버가 새 연결을 받으려면 새 소켓 fd를 열어야 한다.

- listen 자체는 살아 있다
- 하지만 `accept()`가 새 fd를 못 만들면 연결 수용이 실패한다
- backlog가 차기 전에 fd 고갈이 먼저 터질 수도 있다

이 지점은 [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)와 직접 이어진다.

### 4. 컨테이너 환경에서는 더 헷갈린다

컨테이너 안에서 fd가 부족해도 호스트의 `fs.file-max`는 남아 있을 수 있다.

- 앱은 `EMFILE`을 본다
- 운영자는 "노드는 멀쩡한데?"라고 생각한다
- 실제로는 개별 프로세스나 cgroup에 묶인 워커가 한도를 넘었을 수 있다

이때는 [container, cgroup, namespace](./container-cgroup-namespace.md)와 함께 봐야 한다.

## 실전 시나리오

### 시나리오 1: 갑자기 `Too many open files`가 뜬다

가능한 원인:

- fd leak
- connection spike
- 로그/임시 파일을 닫지 못함
- worker pool의 descriptor 누수

진단:

```bash
ulimit -n
cat /proc/<pid>/limits | grep -i "open files"
ls /proc/<pid>/fd | wc -l
```

### 시나리오 2: 프로세스는 멀쩡한데 새 연결만 안 열린다

가능한 원인:

- `accept()`에서 `EMFILE`
- connection당 fd를 너무 많이 사용한다
- close가 늦어 fd 재활용이 안 된다

진단:

```bash
lsof -p <pid> | head
ss -tanp | head
cat /proc/<pid>/fdinfo/*
```

### 시나리오 3: 노드 전체가 비슷한 시점에 흔들린다

가능한 원인:

- 시스템 전체 `file-max`에 접근한다
- 많은 컨테이너가 같은 호스트에서 fd를 늘린다
- 파일 객체가 해제되지 않아 누적된다

진단:

```bash
cat /proc/sys/fs/file-max
cat /proc/sys/fs/file-nr
```

`file-nr`는 보통 할당/사용/최대치 감각을 주는 데 유용하다. 시스템 전체 포화를 볼 때 가장 먼저 본다.

### 시나리오 4: 배포 후만 fd가 급증한다

가능한 원인:

- 재시도 루프가 소켓을 쌓는다
- 새 버전에서 connection close가 누락됐다
- health check와 일반 트래픽이 합쳐져 누수가 드러난다

이런 경우는 `lsof`를 시간차로 비교하는 것이 유용하다.

## 코드로 보기

### 프로세스별 fd 개수 확인

```bash
ls /proc/<pid>/fd | wc -l
```

### 상한과 현재 상태 확인

```bash
ulimit -n
cat /proc/<pid>/limits | grep -i "Max open files"
cat /proc/sys/fs/file-nr
```

### 열린 객체를 빠르게 훑기

```bash
lsof -p <pid> | awk '{print $5}' | sort | uniq -c
```

이렇게 보면 `IPv4`, `IPv6`, `REG`, `CHR`, `FIFO` 같은 유형별 비중을 대략 읽을 수 있다.

### 설정 예시

```bash
ulimit -n 1048576
```

주의점:

- 한도만 키우면 leak이 늦게 터질 뿐이다
- 반드시 close 누락, idle connection, worker lifetime을 같이 봐야 한다

### accept 실패를 다루는 의사 코드

```c
int c = accept(listen_fd, NULL, NULL);
if (c < 0 && errno == EMFILE) {
    // backpressure, logging, alerting
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `ulimit -n` 상향 | 더 많은 연결을 수용한다 | leak 숨김 효과가 있다 | 대규모 서버 |
| leak 수정 | 근본 원인을 제거한다 | 분석이 필요하다 | 장기 운영 |
| connection cap | 폭주를 막는다 | 유연성이 줄어든다 | 멀티테넌트 서비스 |
| fd pool/reuse | 오픈 비용을 줄인다 | 구현 복잡도 증가 | 고빈도 I/O |

fd exhaustion 대응은 "한도 올리기"보다, **어떤 객체가 왜 닫히지 않는지**를 찾는 게 핵심이다.

## 꼬리질문

> Q: `EMFILE`과 `ENFILE`의 차이는 무엇인가요?
> 핵심: 전자는 프로세스 한도, 후자는 시스템 전체 한도다.

> Q: fd를 많이 열면 왜 서버가 느려지나요?
> 핵심: 관리 비용, poll/epoll 비용, 메모리 사용이 함께 늘기 때문이다.

> Q: 한도만 올리면 해결되나요?
> 핵심: 아니다. 누수와 backpressure를 같이 잡아야 한다.

> Q: 컨테이너에서 fd 문제가 더 헷갈리는 이유는?
> 핵심: 호스트와 컨테이너의 관측 경계가 다르기 때문이다.

## 한 줄 정리

fd exhaustion은 연결, 로그, 파일, 소켓을 한꺼번에 멈추게 만들 수 있으므로, `ulimit`, `/proc/sys/fs/file-nr`, `lsof`, `/proc/<pid>/fd`를 같이 봐야 한다.
