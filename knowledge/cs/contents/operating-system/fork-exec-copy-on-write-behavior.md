# Fork, Exec, Copy-on-Write Behavior

> 한 줄 요약: fork는 처음엔 싸지만 copy-on-write 때문에 첫 write가 비싸질 수 있고, exec는 새 주소 공간으로 갈아타면서 이전 상태를 버린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [PID Limits, Process Table Exhaustion](./pid-limit-process-table-exhaustion.md)
> - [Linux Process State Machine, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)

> retrieval-anchor-keywords: fork, execve, copy-on-write, COW, vfork, address space, page duplication, child process, first write penalty

## 핵심 개념

`fork()`는 부모 프로세스를 복제해 자식을 만들지만, 실제 페이지는 즉시 전부 복사하지 않는다. 대신 write가 발생할 때 copy-on-write(COW)로 페이지를 분리한다. `execve()`는 그 뒤 프로세스 이미지를 새 프로그램으로 갈아타는 동작이다.

- `fork`: 부모 주소 공간을 복제하는 것처럼 보이지만 COW를 쓴다
- `execve`: 현재 프로세스 이미지를 새 프로그램으로 바꾼다
- `COW`: 쓰기 시에만 실제 복제를 수행한다

왜 중요한가:

- pre-fork 서버는 fork가 빠르다고 느끼지만 첫 write가 비쌀 수 있다
- 큰 heap이나 캐시를 가진 프로세스는 fork 비용이 커진다
- exec는 상태를 갈아엎기 때문에 안정적이지만 초기화 비용이 든다

이 문서는 [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)와 [PID Limits, Process Table Exhaustion](./pid-limit-process-table-exhaustion.md)를 프로세스 생성 관점으로 묶는다.

## 깊이 들어가기

### 1. fork는 page table을 빠르게 복제한다

부모의 메모리를 물리적으로 즉시 전부 복사하는 것이 아니라, page table과 참조 관계를 복제한다.

- 초기 fork는 상대적으로 빠르다
- 자식과 부모가 같은 페이지를 읽는 동안은 싸다
- write가 시작되면 COW가 터진다

### 2. 첫 write는 page fault와 연결된다

자식이 메모리를 쓰는 순간 새 페이지가 필요할 수 있다.

- minor fault가 발생할 수 있다
- 실제 복제가 늦게 일어난다
- fork 직후 write-heavy 경로는 비용이 크다

### 3. exec는 이전 메모리 이미지를 교체한다

`execve()`는 기존 주소 공간을 새 프로그램 이미지로 바꾼다.

- 부모/자식 관계를 유지하되 코드와 메모리 이미지는 갈아탄다
- 초기화 비용은 있지만 상태를 단순하게 만든다
- shell wrapper, init 프로세스, worker exec 패턴에 중요하다

### 4. fork/exec는 서버 설계와 연결된다

- pre-fork worker model
- shell spawning
- script execution
- daemon reload

## 실전 시나리오

### 시나리오 1: fork는 빠른데 자식 첫 요청이 느리다

가능한 원인:

- COW로 첫 write가 비싸다
- 큰 부모 heap을 복제한다
- page fault와 reclaim이 겹친다

진단:

```bash
perf stat -p <pid> -e minor-faults,major-faults,page-faults -- sleep 30
strace -f -ttT -e trace=fork,vfork,clone,execve -p <pid>
```

### 시나리오 2: worker 생성이 많을수록 메모리 압박이 커진다

가능한 원인:

- fork된 자식들이 곧바로 write한다
- COW가 대량 page duplication으로 변한다
- pid limit과 memory pressure가 같이 온다

### 시나리오 3: exec 기반 모델이 느리지만 안정적이다

가능한 원인:

- 새 주소 공간 초기화 비용
- cold start fault
- 그러나 상태 분리가 좋아 장애 격리가 쉬움

## 코드로 보기

### fork 후 write 감각

```c
pid_t pid = fork();
if (pid == 0) {
    // child writes -> COW may trigger
}
```

### exec 모델

```c
execl("/usr/bin/java", "java", "-jar", "app.jar", NULL);
```

### 단순 모델

```text
fork
  -> pages shared read-only
  -> first write duplicates pages
  -> exec replaces entire address space
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| fork + COW | 시작이 빠르다 | 첫 write 비용이 크다 | pre-fork worker |
| exec 기반 | 상태가 단순하다 | 초기화 비용이 든다 | daemon restart |
| vfork | 매우 빠를 수 있다 | 제약이 강하다 | 특수 케이스 |
| thread pool | 주소 공간 공유 | 장애 전파 위험 | 일반 서버 |

## 꼬리질문

> Q: fork가 왜 처음엔 싸나요?
> 핵심: 실제 페이지를 바로 복사하지 않고 COW를 쓰기 때문이다.

> Q: exec는 무엇을 하나요?
> 핵심: 현재 프로세스 이미지를 새 프로그램으로 교체한다.

> Q: COW는 언제 비싸지나요?
> 핵심: 자식이나 부모가 페이지를 실제로 쓰기 시작할 때다.

## 한 줄 정리

fork는 copy-on-write 덕분에 초기에는 싸지만, write-heavy 경로에서는 첫 페이지 복제가 비용이 되어 tail latency를 키울 수 있다.
