# container, cgroup, namespace

> 한 줄 요약: 컨테이너는 "가벼운 VM"이 아니라, namespace로 보이는 세계를 나누고 cgroup으로 자원을 제한하는 리눅스 기능의 조합이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - [PID 1, SIGTERM, and Container Reaping Basics](./container-pid-1-sigterm-zombie-reaping-basics.md)
> - [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)
> - [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
> - [file descriptor, socket, syscall cost](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [OverlayFS Copy-up, Container Layering, Runtime Debugging](./overlayfs-copy-up-container-layering-debugging.md)
> - [tmpfs, shmem, /dev/shm, Cgroup Memory Accounting](./tmpfs-shmem-cgroup-memory-accounting.md)
> - [Virtual Threads(Project Loom)](../language/java/virtual-threads-project-loom.md)
> - [Spring Boot 자동 구성](../spring/spring-boot-autoconfiguration.md)

> retrieval-anchor-keywords: container, cgroup, namespace, pid namespace, mount namespace, network namespace, capability, cgroup v2, PID 1, container isolation, overlayfs, tmpfs

---

## 핵심 개념

컨테이너는 프로세스를 격리하는 리눅스 기능 조합이다.

- `namespace`: 프로세스가 보는 이름공간을 분리한다. PID, mount, network, UTS, IPC, user 등을 나눌 수 있다.
- `cgroup`: CPU, memory, pids, I/O 같은 자원 사용량을 제한하고 계측한다.
- `capability`: root 전체 권한이 아니라 필요한 권한만 부분적으로 준다.

왜 중요한가:

- 서버가 여러 개의 워크로드를 한 호스트에서 안전하게 돌려야 한다.
- "내 프로세스만 죽었는데 왜 전체 노드가 흔들렸지?" 같은 장애를 막으려면 격리와 제한을 이해해야 한다.

---

## 깊이 들어가기

### 1. namespace는 "보이는 세계"를 나눈다

대표적인 namespace:

- PID namespace: 같은 프로세스도 각 컨테이너에서 다른 PID로 보인다
- mount namespace: 파일 시스템 마운트가 분리된다
- network namespace: 인터페이스, 라우팅 테이블, 포트가 분리된다
- UTS namespace: hostname 분리
- IPC namespace: shared memory, semaphore 분리
- user namespace: root 권한을 호스트와 분리해서 매핑

실제 런타임에서는 이 mount view가 OverlayFS 기반 image layer와 결합되는 경우가 많아서, "컨테이너 파일 시스템도 결국 일반 디렉터리"라고 보면 write path를 과소평가하기 쉽다.

핵심은 프로세스가 커널 자원 전체를 보는 것이 아니라, **자기 namespace 안의 일부만 보는 것처럼 느끼게 하는 것**이다.

### 2. cgroup은 "얼마나 쓸 수 있는지"를 제한한다

cgroup은 CPU와 메모리 같은 자원을 계측하고 제한한다.

운영에서 자주 보는 항목:

- CPU quota / period
- memory limit
- pids limit
- blkio / io weight

즉 컨테이너는 "가상 머신처럼 보이지만", 실제로는 **같은 커널 위에서 프로세스를 제어하는 방식**이다.

### 3. PID 1이 중요한 이유

컨테이너 내부의 PID 1은 일반 리눅스의 init처럼 좀비 reaping 책임을 져야 한다.

- PID 1이 `SIGCHLD`를 처리하지 않으면 zombie가 누적될 수 있다
- 종료 시그널을 제대로 전달하지 않으면 graceful shutdown이 깨질 수 있다

이 부분은 [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)와 직접 연결된다.

### 4. namespace와 cgroup은 역할이 다르다

- namespace: "보이는 것"을 나눈다
- cgroup: "쓸 수 있는 것"을 제한한다

이 둘을 혼동하면 컨테이너 격리를 잘못 이해하게 된다.

---

## 실전 시나리오

### 시나리오 1: 컨테이너가 OOMKilled 되었는데 호스트는 멀쩡함

설명:

- 컨테이너 메모리 limit을 넘으면 cgroup이 프로세스를 kill할 수 있다
- 호스트 전체 메모리가 부족한 것이 아닐 수 있다

진단:

```bash
docker inspect <container> | jq '.[0].State'
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.current
```

### 시나리오 2: 컨테이너 안에서 `ps`를 봤더니 PID가 이상함

설명:

- PID namespace 때문에 호스트와 컨테이너의 PID가 다르다
- 호스트에서 보이는 PID와 컨테이너 내부 PID를 헷갈리면 운영 진단이 꼬인다

진단:

```bash
lsns
nsenter --target <host-pid> --pid --mount --uts --net sh
cat /proc/1/status
```

### 시나리오 3: CPU가 100%가 아닌데 응답이 느림

원인 후보:

- cgroup CPU quota로 throttling이 걸림
- 노드 전체는 여유가 있어도 컨테이너 단위로 실행이 제한됨

진단:

```bash
cat /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/cpu.stat
```

### 시나리오 4: 포트 충돌, hostname 충돌, tmp 파일 충돌

원인:

- network namespace, UTS namespace, mount namespace를 제대로 이해하지 못함

즉 컨테이너는 파일 시스템만 분리하는 것이 아니라, **프로세스와 네트워크와 이름 공간을 함께 분리**한다.

---

## 코드로 보기

### 컨테이너 격리 감각을 보는 기본 명령

```bash
docker run --rm -it --name demo alpine sh
ps -ef
cat /proc/1/status
mount | head
ip addr
```

### PID namespace와 좀비 회수

```c
// 의사 코드: PID 1 역할을 하는 프로세스는 자식 종료를 회수해야 한다
for (;;) {
    pid = waitpid(-1, &status, WNOHANG);
    if (pid > 0) {
        // child reap
    }
    handle_signals();
}
```

### cgroup 관찰 감각

```bash
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/pids.current
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| Namespace | 격리와 단순한 mental model | 자원 제한은 안 된다 | 프로세스/네트워크 분리 |
| cgroup | 자원 제어와 계측이 된다 | 잘못 잡으면 throttling/OOM | 운영 안정성 필요 |
| Capability | root 권한을 쪼갤 수 있다 | 설정 실수 시 위험 | 최소 권한 운영 |
| VM | 커널 자체가 분리된다 | 무겁다 | 강한 격리/다양한 OS 필요 |
| Container | 가볍고 빠르다 | 같은 커널을 공유한다 | 빠른 배포와 밀집 운영 |

컨테이너는 VM의 대체물이 아니라, **더 가볍게 격리와 자원 관리를 하고 싶을 때의 선택**이다.

---

## 꼬리질문

> Q: namespace와 cgroup의 차이는?
> 의도: 컨테이너를 표면적으로만 아는지 확인
> 핵심: namespace는 보이는 세계를 분리하고, cgroup은 쓸 수 있는 자원을 제한한다.

> Q: 컨테이너에서 PID 1이 왜 중요한가요?
> 의도: zombie reaping과 graceful shutdown 이해 확인
> 핵심: PID 1은 자식 프로세스를 회수하고 signal을 잘 받아야 한다.

> Q: 컨테이너와 VM의 가장 큰 차이는?
> 의도: 격리 수준과 운영 비용 균형을 아는지 확인
> 핵심: VM은 커널까지 분리하고, 컨테이너는 같은 커널 위에서 namespace/cgroup으로 격리한다.

---

## 한 줄 정리

컨테이너는 리눅스 프로세스를 namespace로 나누고 cgroup으로 제한하는 기술이며, 운영 문제는 대부분 이 둘의 경계를 잘못 이해할 때 터진다.
