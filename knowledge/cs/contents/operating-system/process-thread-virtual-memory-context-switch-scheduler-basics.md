# Process, Thread, Virtual Memory, Context Switch, Scheduler Basics

> 한 줄 요약: 프로세스는 자원과 보호 경계이고, 스레드는 그 안에서 CPU에 스케줄되는 실행 흐름이며, 가상 메모리와 스케줄러가 둘을 실제로 움직이게 만든다.

**난이도: 🟢 Beginner**

관련 문서:

- [프로세스와 스레드](./README.md#프로세스와-스레드)
- [프로세스 스케줄링](./README.md#프로세스-스케줄링)
- [가상 메모리](./README.md#가상-메모리)
- [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)
- [Fork, Exec, Copy-on-Write Behavior](./fork-exec-copy-on-write-behavior.md)
- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
- [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
- [Page Table Overhead, Memory Footprint](./page-table-overhead-memory-footprint.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)

retrieval-anchor-keywords: process vs thread, thread vs process, virtual memory basics, stack vs heap, context switch basics, scheduler basics, scheduler observability beginner, address space, process memory layout, ready running waiting, run queue, time slice, page fault, 프로세스 스레드 처음 배우는데, 컨텍스트 스위치 뭐예요

## 핵심 개념

운영체제 기초에서 가장 많이 섞이는 질문은 사실 하나로 묶인다.

- 프로세스와 스레드는 무엇이 다른가
- 메모리는 왜 코드/데이터/힙/스택으로 나누어 말하는가
- 가상 메모리는 왜 필요한가
- context switch는 무엇을 바꾸는가
- scheduler는 어떤 기준으로 다음 실행 대상을 고르는가

이 문서는 이 다섯 질문을 한 흐름으로 묶어 입문 감각을 만든다.

## 한눈에 보기

| 개념 | 무엇인가 | 꼭 기억할 점 |
|------|----------|--------------|
| 프로세스 | 실행 중인 프로그램의 자원 묶음 | 주소 공간과 보호 경계를 가진다 |
| 스레드 | CPU 위에서 실행되는 흐름 | 같은 프로세스의 코드/데이터/힙을 공유한다 |
| 가상 메모리 | 각 프로세스에 보이는 논리 주소 공간 | 실제 물리 메모리와 분리되어 있다 |
| 스택 | 함수 호출과 지역 상태를 담는 메모리 | 스레드마다 따로 가진다 |
| 힙 | 동적 할당 객체가 머무는 메모리 | 같은 프로세스의 스레드가 함께 본다 |
| scheduler | 다음에 돌릴 runnable 태스크를 고르는 장치 | latency, throughput, fairness를 같이 본다 |
| context switch | 현재 실행 상태를 저장하고 다른 태스크 상태를 복원하는 일 | 전환 자체는 유용한 일을 하지 않는 비용이다 |

## 1. 프로세스와 스레드: 무엇을 나누고 무엇을 공유하나

프로세스는 "실행 단위"라기보다 **자원과 보호 경계**에 가깝다.  
스레드는 그 프로세스 안에서 실제로 CPU 명령을 실행하는 **흐름**이다.

- 프로세스는 자신의 가상 주소 공간, 열린 파일, 시그널 상태, 계정 정보 같은 운영체제 자원을 가진다
- 스레드는 프로그램 카운터, 레지스터, 스택처럼 "지금 어디까지 실행했는가"를 표현하는 상태를 가진다
- 같은 프로세스의 스레드는 코드/데이터/힙을 공유한다
- 다른 프로세스는 기본적으로 주소 공간을 공유하지 않는다

### 프로세스 vs 스레드 비교

| 항목 | 프로세스끼리 | 같은 프로세스의 스레드끼리 |
|------|---------------|----------------------------|
| 가상 주소 공간 | 분리됨 | 공유됨 |
| 코드/전역 데이터/힙 | 기본적으로 분리됨 | 공유됨 |
| 스택 | 각 프로세스의 각 스레드가 따로 가짐 | 스레드마다 따로 가짐 |
| 장애 영향 범위 | 상대적으로 격리됨 | 한 스레드의 메모리 오염이 전체 프로세스에 영향 줄 수 있음 |
| 생성/전환 비용 | 더 큼 | 보통 더 작음 |
| 통신 방식 | IPC 필요 | 공유 메모리 접근이 쉬움 |

입문에서는 "CPU가 프로세스를 스케줄한다"고 말해도 큰 틀에서는 맞지만, Linux 관점에서는 실제로 **thread/task 단위가 스케줄 대상**이라는 감각을 같이 가져가면 좋다.

## 2. 가상 메모리: 각 프로세스가 자기 메모리를 가진 것처럼 보이는 이유

가상 메모리는 프로세스마다 **독립적인 논리 주소 공간**을 제공한다.  
즉, 프로그램은 `0x...` 같은 가상 주소를 사용하고, 운영체제와 하드웨어가 이를 실제 물리 메모리에 연결한다.

핵심은 다음 세 가지다.

- **격리**: 프로세스 A가 프로세스 B의 메모리를 함부로 읽거나 쓰지 못하게 한다
- **단순화**: 프로그램은 "연속된 큰 메모리"가 있는 것처럼 코드를 짤 수 있다
- **효율화**: 필요한 페이지를 필요한 시점에만 메모리에 올리는 demand paging이 가능하다

이 연결 정보는 page table 같은 자료구조에 담긴다.

```text
프로세스가 보는 주소
  -> 가상 주소
  -> page table 조회
  -> 물리 메모리 프레임 또는 파일-backed 페이지와 연결
```

중요한 포인트:

- 프로세스마다 page table이 다르다
- 같은 프로세스의 스레드는 같은 주소 공간을 공유하므로 같은 page table을 본다
- 필요한 페이지가 아직 준비되지 않았다면 page fault가 발생하고, 커널이 페이지를 준비한 뒤 실행을 이어 간다

## 3. 코드 / 데이터 / 힙 / 스택: 주소 공간 안은 어떻게 나뉘는가

입문 설명에서 자주 쓰는 메모리 그림은 "전형적인 감각"을 잡기 위한 것이다. 실제 배치는 OS, 아키텍처, ASLR, 런타임에 따라 달라질 수 있지만 아래 틀이 이해의 출발점이 된다.

```text
높은 주소
+---------------------------+
| thread B stack            |
| thread A stack            |
| mmap 영역 / 공유 라이브러리 |
| heap                      |
| data / bss                |
| code / text               |
+---------------------------+
낮은 주소
```

- **code/text**: 실행 명령어가 놓이는 영역이다. 보통 읽기 전용이다
- **data/bss**: 전역 변수, static 변수 같은 장수명 데이터가 놓인다
- **heap**: `malloc`, `new` 같은 동적 할당 결과가 놓인다
- **stack**: 함수 호출 프레임, 매개변수, 복귀 주소, 지역 상태가 놓인다

이 구분을 이해하면 "어떤 메모리가 누구의 소유인가"가 보인다.

## 4. stack vs heap: 둘 다 메모리지만 성질이 다르다

stack과 heap은 모두 프로세스 주소 공간 안에 있지만, **소유권과 수명 관리 방식**이 다르다.

| 항목 | stack | heap |
|------|-------|------|
| 주 소유자 | 각 스레드 | 프로세스 전체 |
| 주 용도 | 함수 호출 상태, 지역 변수 | 동적 생성 객체 |
| 수명 | 함수/스코프 종료와 함께 사라지는 경우가 많다 | 명시적 해제, GC, 참조 해제 등 런타임 정책에 따름 |
| 크기 특성 | 보통 작고 제한이 엄격하다 | 더 유연하지만 무한하지 않다 |
| 흔한 문제 | stack overflow, 너무 깊은 재귀 | memory leak, fragmentation, use-after-free |

초보자가 헷갈리기 쉬운 지점:

- 스레드는 **각자 stack을 가진다**
- 같은 프로세스의 스레드는 **heap을 공유한다**
- 그래서 지역 변수는 보통 스레드 간 자동 격리가 되지만, heap 객체는 동기화 없이 함께 만지면 경쟁 조건이 생긴다

예를 들어 웹 서버 worker 스레드 두 개가 같은 캐시 객체를 수정한다면, 그 객체는 heap에 있으므로 동기화가 필요할 수 있다.

## 5. context switch: CPU가 실행 흐름을 바꿀 때 일어나는 일

CPU 코어 하나는 한 순간에 하나의 실행 흐름만 실제로 돌릴 수 있다.  
그래서 멀티태스킹을 하려면 현재 태스크 상태를 저장하고 다른 태스크 상태를 복원해야 한다. 그 작업이 context switch다.

보통 다음 정보가 전환 대상에 들어간다.

- 프로그램 카운터(다음에 실행할 명령 위치)
- 스택 포인터
- 일반 레지스터
- 스케줄링 상태
- 경우에 따라 주소 공간 관련 정보

### 언제 context switch가 일어나는가

- time slice를 다 써서 선점될 때
- I/O 대기로 block될 때
- sleep, wait, futex 대기처럼 스스로 CPU를 놓을 때
- 더 급한 태스크가 runnable 상태가 되었을 때

### 왜 비용이 드는가

- 저장/복원 자체가 필요하다
- 커널이 개입한다
- 캐시 locality가 깨질 수 있다
- 프로세스 전환이면 주소 공간 전환 영향까지 생길 수 있다

그래서 "스레드가 더 가볍다"는 말은 맞지만, **스레드도 공짜가 아니다**. runnable 스레드를 너무 많이 만들면 context switch 비용이 누적된다.

## 6. scheduler basics: 다음에 누가 CPU를 받는가

scheduler는 runnable 상태의 태스크 중에서 **다음에 CPU를 받을 대상을 고른다**.

입문에서는 상태를 이렇게 단순화하면 충분하다.

- **running**: 지금 CPU에서 실행 중
- **ready/runnable**: 실행할 준비는 됐지만 CPU를 기다리는 중
- **waiting/blocked**: I/O나 이벤트를 기다리는 중이라 지금은 당장 실행할 수 없음

핵심 감각은 다음과 같다.

- waiting 태스크는 run queue 경쟁 대상이 아니다
- runnable 태스크가 많아질수록 run queue가 길어진다
- run queue가 길어지면 응답 지연과 context switch가 늘어난다

### scheduler가 동시에 보는 목표

- **latency**: 너무 오래 기다리지 않게 하기
- **throughput**: 전체 처리량을 높이기
- **fairness**: 특정 태스크만 계속 굶지 않게 하기

이 세 목표는 항상 완전히 일치하지 않는다.  
예를 들어 짧은 인터랙티브 요청 latency를 줄이려면, 긴 배치 작업의 CPU 점유를 어느 정도 희생해야 할 수도 있다.

### time slice와 선점

현대 OS는 보통 선점형 스케줄링을 사용한다.

- 한 태스크가 영원히 CPU를 붙잡지 못하게 한다
- 일정 시간(time slice)이나 정책 기준이 지나면 다른 태스크에 기회를 준다
- 너무 짧게 자르면 응답성은 좋아질 수 있지만 context switch가 많아진다

즉 scheduler는 "누가 먼저인가"만 정하는 것이 아니라 **CPU를 얼마나 잘게 나눌 것인가**도 관리한다.

### scheduler basics 다음에 바로 붙는 관측 노트

여기까지 이해했다면 다음 단계는 scheduler 내부 알고리즘보다 **관측 순서**를 익히는 것이다.

- 먼저 `load average`와 `vmstat r`로 runnable 압력이 실제로 있는지 본다
- 그다음 `/proc/<pid>/sched` 또는 `/proc/<tid>/sched`로 어떤 태스크가 밀리는지 좁힌다
- 마지막으로 `runqlat`로 wakeup-to-run tail이 실제로 두꺼운지 확인한다

이 흐름은 별도 문서인 [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)에서 한 번에 정리해 둔다. 이 문서를 읽고 나서 [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md), [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md), [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md)로 내려가면 훨씬 덜 헷갈린다.

## 7. 이 개념들이 실제 요청 처리에서 어떻게 연결되는가

웹 요청 하나를 단순화하면 다음 흐름으로 볼 수 있다.

```text
1. worker thread가 CPU를 받는다
2. 자기 stack 위에서 함수 호출을 진행한다
3. heap에 있는 공유 객체를 읽거나 수정한다
4. DB/socket I/O를 기다리며 blocked 상태가 된다
5. scheduler가 다른 runnable thread로 context switch한다
6. I/O 완료 후 원래 thread가 다시 runnable 상태가 된다
7. 다시 CPU를 받아 이어서 실행한다
```

이 흐름을 보면 개념이 하나로 이어진다.

- 프로세스는 주소 공간과 자원을 제공한다
- 스레드는 그 안에서 실행된다
- stack은 각 스레드의 "현재 실행 위치"를 붙잡는다
- heap은 여러 스레드가 같이 보는 데이터 저장소다
- 가상 메모리는 이 전체 공간을 안전하게 조직한다
- scheduler와 context switch는 CPU 시간을 번갈아 나눈다

## 8. 자주 나오는 오해

### "스레드는 프로세스보다 무조건 좋다"

아니다. 스레드는 공유가 쉬워 빠를 수 있지만, 동기화와 장애 전파 비용이 생긴다.

### "stack은 빠르고 heap은 느리다"

입문 감각으로는 맞는 말처럼 들리지만, 절대 법칙은 아니다. 핵심 차이는 속도보다 **할당/수명/공유 방식**이다.

### "CPU 사용률만 보면 scheduler 상태를 알 수 있다"

아니다. CPU 사용률이 높지 않아도 runnable 태스크가 길게 대기하면 latency는 나빠질 수 있다. 이때는 run queue와 wakeup latency를 같이 봐야 한다.

### "가상 메모리는 메모리가 부족할 때만 쓰는 기술이다"

아니다. 가상 메모리는 부족할 때 버티는 장치이기도 하지만, 본질적으로는 **격리와 주소 추상화**를 제공하는 기본 구조다.

## 꼬리질문

> Q: 프로세스와 스레드의 가장 큰 차이는 무엇인가요?
> 핵심: 프로세스는 자원과 보호 경계, 스레드는 그 안에서 실행되는 흐름이다.

> Q: 왜 스레드마다 stack이 따로 필요한가요?
> 핵심: 각 스레드는 함수 호출 위치, 지역 상태, 복귀 주소가 서로 다르기 때문이다.

> Q: heap을 공유하면 왜 동기화 문제가 생기나요?
> 핵심: 여러 스레드가 같은 객체를 동시에 읽고 쓸 수 있기 때문이다.

> Q: context switch가 많아지면 왜 느려지나요?
> 핵심: 전환하는 동안은 실제 비즈니스 작업을 하지 않고, 캐시 locality도 깨질 수 있기 때문이다.

> Q: scheduler는 waiting 태스크와 runnable 태스크를 어떻게 다르게 보나요?
> 핵심: waiting 태스크는 아직 실행할 준비가 안 되었고, runnable 태스크만 CPU 경쟁 대상이 된다.

## 한 줄 정리

프로세스는 주소 공간과 자원, 스레드는 실행 흐름, 가상 메모리는 그 공간의 추상화, stack/heap은 그 안의 수명 규칙, scheduler와 context switch는 CPU 시간을 나누는 장치라고 묶어 이해하면 운영체제 기초 축이 정리된다.
