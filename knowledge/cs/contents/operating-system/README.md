# Operating System (운영체제)

> 한 줄 요약: 이 README는 운영체제 카테고리에서 beginner가 `무엇부터 읽지?`, `왜 느리지?`, `oomkilled 뭐예요?` 같은 첫 질문을 안전한 primer와 follow-up으로 분기시키는 category navigator다.

**난이도: 🟢 Beginner**

관련 문서:

- [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)
- [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../network/network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [CS 루트 README: 카테고리 전체 Quick Routes](../../README.md#quick-routes)

retrieval-anchor-keywords: operating system readme, os navigator, operating system primer, os beginner route, process thread basics, memory basics, too many open files, oomkilled 뭐예요, subprocess hang why, wait에서 안 끝나요, stdin eof 안 와요, stdout pipe full, operating system 처음, what is operating system, beginner triage

## 빠른 탐색

이 카테고리는 크게 두 층으로 읽으면 된다.

| 지금 상태 | 먼저 읽을 층 | 첫 클릭 |
| --- | --- | --- |
| 운영체제를 처음 묶어 보고 싶다 | beginner primer | [입문 primer](#입문-primer) |
| 증상은 있는데 어디서 잘라야 할지 모르겠다 | symptom router | [증상별 빠른 분기](#증상별-빠른-분기) |
| 이미 개념은 있고 Linux runtime을 깊게 보고 싶다 | deep dive shelf | [현대 runtime shelf](#현대-runtime-shelf) |

초보자라면 deep dive 문서부터 열지 말고 `primer -> symptom bridge -> deep dive` 순서를 지키는 편이 안전하다. 이 비유는 entrypoint에서만 유효하다. 실제 운영에서는 scheduler, memory, fd, network가 동시에 얽히므로 follow-up 문서에서 경계를 다시 세분화해야 한다.

## 추천 학습 흐름

운영체제를 처음 다시 잡는다면 아래 순서가 가장 덜 끊긴다.

1. [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)로 용어 축을 먼저 묶는다.
2. [CPU 스케줄링 기초](./cpu-scheduling-basics.md), [메모리 관리 기초](./memory-management-basics.md), [시스템 콜 기초](./syscall-basics.md)로 CPU/메모리/커널 경계를 각각 분리한다.
3. 증상이 보이면 [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)에서 `slow`, `oom`, `fd`, `subprocess` 중 어느 축인지 먼저 자른다.
4. 그다음에만 runtime deep dive나 playbook으로 내려간다.

학습 시간이 짧다면 1번 문서 하나만 먼저 읽어도 된다. `process vs thread`, `syscall vs context switch`, `rss vs vsz` 세 축이 잡히면 나머지 문서가 훨씬 덜 섞인다.

## 입문 primer

처음 읽는 독자에게 가장 안전한 출발점은 아래 5개다.

- [프로세스와 스레드 기초](./process-thread-basics.md): 실행 주체와 공유/격리 감각을 먼저 잡는다.
- [CPU 스케줄링 기초](./cpu-scheduling-basics.md): ready queue와 time slice를 응답시간 관점으로 묶는다.
- [메모리 관리 기초](./memory-management-basics.md): virtual memory, page fault, RSS/VSZ를 한 장면으로 본다.
- [시스템 콜 기초](./syscall-basics.md): 앱이 커널과 만나는 경계를 잡는다.
- [파일 디스크립터 기초](./file-descriptor-basics.md): fd, socket, redirect, `Too many open files` 첫 질문을 받는다.

`뭐예요`, `처음`, `헷갈려요`에 가까운 질문은 위 primer에서 시작하고, primer 말미의 handoff box를 따라 다음 문서로 이동하면 된다.

## 증상별 빠른 분기

증상이 먼저 보일 때는 아래처럼 자르면 된다.

| 보이는 증상 | 먼저 볼 문서 | 왜 여기서 시작하나 |
| --- | --- | --- |
| CPU는 낮은데 응답이 느리다 | [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md) | CPU, throttling, I/O wait를 바로 분리한다 |
| `oomkilled`, `Killed`, `memory.events`가 보인다 | [Killed, OOMKilled, memory.events Beginner Bridge](./killed-oomkilled-memory-events-beginner-bridge.md) | 같은 종료 사건의 서로 다른 표지판을 묶는다 |
| `Too many open files`가 보인다 | [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md) | `EMFILE`과 `ENFILE`을 먼저 구분한다 |
| 출력이 많을 때만 subprocess가 멈춘다 | [Subprocess Pipe Backpressure Primer](./subprocess-pipe-backpressure-primer.md) | buffering 지연과 pipe backpressure hang를 분리한다 |
| child는 끝난 것 같은데 parent가 EOF를 못 받는다 | [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) | 누가 write end를 아직 쥐고 있는지 먼저 본다 |
| `stdin=PIPE`와 `stdout=PIPE`를 같이 쓸 때 `cat`, `sort`에서 멈춘다 | [Bidirectional Pipe Deadlock Primer](./subprocess-bidirectional-pipe-deadlock-primer.md) | read, write, close 순서와 EOF 전달 문제를 함께 본다 |
| backlog, `ListenOverflows`, accept 지연이 보인다 | [Accept Overload Observability Playbook](./accept-overload-observability-playbook.md) | listener queue와 user-space drain 병목을 같이 본다 |

subprocess 질문은 하나로 뭉뚱그리지 말고 `출력이 많을 때만 멈춤`, `EOF가 안 옴`, `stdin/stdout 둘 다 pipe` 중 어느 쪽인지 먼저 고르면 다음 문서가 훨씬 정확해진다.

질문이 "`왜 느려요?`"처럼 너무 넓으면 먼저 [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)으로 돌아가서 분기를 다시 고른다.

## 현대 runtime shelf

아래 문서들은 beginner primer 다음 단계의 follow-up shelf다.

- scheduler/lock 축: [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md), [Lock Contention, Futex Wait, Off-CPU Debugging](./lock-contention-futex-offcpu-debugging.md)
- event loop / io_uring 축: [I/O Models and Event Loop](./io-models-and-event-loop.md), [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
- memory / page cache 축: [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md), [page cache, dirty writeback, fsync](./page-cache-dirty-writeback-fsync.md)
- container / pressure 축: [container, cgroup, namespace](./container-cgroup-namespace.md), [PSI Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

이 shelf는 "정의"보다 "운영 관찰"을 다룬다. 따라서 beginner가 여기부터 읽으면 개념보다 증상 이름만 늘 수 있다. 먼저 primer에서 기준 좌표를 세운 뒤 필요한 축 하나만 내려가는 편이 낫다.

## 연결해서 보면 좋은 문서

운영체제 질문은 다른 카테고리와 자주 붙는다.

- request lifetime과 timeout/disconnect를 같이 보려면 [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../network/network-spring-request-lifecycle-timeout-disconnect-bridge.md)로 넘어간다.
- 애플리케이션 스레드/프레임워크 경계를 같이 보려면 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)를 잇는다.
- page cache와 durability를 DB 관점까지 확장하려면 [Redo Log Write Amplification](../database/redo-log-write-amplification.md), [Doublewrite Buffer, Torn-Page Protection](../database/doublewrite-buffer-torn-page-protection.md)를 본다.
- JVM/thread 관찰로 이어 가려면 [JVM to OS Performance Master Note](../../master-notes/jvm-to-os-performance-master-note.md), [JFR, JMC Performance Playbook](../language/java/jfr-jmc-performance-playbook.md)을 따라간다.

cross-category bridge는 "지금 보이는 현상이 OS만의 문제인가?"를 확인할 때 쓰는 안전한 다음 걸음이다. 원인을 아직 못 좁혔다면 다시 symptom router로 돌아오는 편이 낫다.

## 한 줄 정리

운영체제 카테고리는 `primer로 좌표를 세우고`, `증상으로 분기한 뒤`, `필요한 deep dive 하나만 내려간다`는 순서로 읽을 때 가장 덜 헷갈린다.
