# CPU 스케줄링 기초

> 한 줄 요약: CPU 스케줄러는 실행 가능한 여러 프로세스 중 다음에 CPU를 줄 프로세스를 선택하는 장치이고, 기준은 공정성·응답 시간·처리량의 균형이다.

**난이도: 🟢 Beginner**

관련 문서:

- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
- [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)
- [operating-system 카테고리 인덱스](./README.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)

retrieval-anchor-keywords: cpu scheduling beginner, cpu 스케줄링 기초, process scheduling basics, round robin basics, fcfs scheduling, preemptive scheduling, time slice basics, ready queue basics, response time vs turnaround time, run queue basics, cpu scheduling self check, 스케줄링 자가 점검

## Self-check Primer Handoff

> **이 문서는 self-check 빠른 점검 루트의 2단계다**
>
> - 언제 읽나: 큰 그림은 기억나는데 "CPU가 누구에게 언제 돌아가느냐"와 ready queue, time slice, 응답 시간 지표가 흐릿할 때 읽는다.
> - 선행 문서: [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)에서 process/thread와 context switch 큰 그림을 먼저 잡고 오면 스케줄링 축이 덜 섞인다.
> - 후행 문서: [메모리 관리 기초](./memory-management-basics.md)에서 CPU 축 다음으로 virtual memory, page fault, RSS/VSZ 혼동을 메모리 관점에서 정리한다.

## 먼저 잡는 멘탈 모델

CPU 코어를 "창구", 실행 가능한 스레드를 "대기 줄"로 보면 쉽다.

- 창구(CPU 코어)는 순간마다 제한되어 있다.
- 대기 줄(ready queue)에는 실행하고 싶은 스레드가 동시에 많이 있다.
- 스케줄러는 매 순간 "누가 먼저 창구를 쓸지" 정한다.

CPU 스케줄링은 결국 **한정된 CPU 시간을 어떤 규칙으로 나눠 줄 것인가**의 문제다.

## 핵심 개념

멀티태스킹 OS에서는 실행할 준비가 된 프로세스(스레드)가 여러 개다. CPU는 한 번에 하나만 실행할 수 있으므로, OS는 "지금 누구를 돌릴지" 결정해야 한다. 이 결정을 내리는 모듈이 **CPU 스케줄러(scheduler)**다.

스케줄러가 고려하는 목표는 크게 세 가지다.

- **CPU 활용률(utilization)**: CPU를 최대한 바쁘게 유지한다.
- **응답 시간(response time)**: 요청 후 첫 응답까지 짧게 유지한다.
- **공정성(fairness)**: 특정 프로세스가 CPU를 독점하지 않도록 한다.

이 세 목표는 동시에 최적화하기 어렵고, 알고리즘마다 트레이드오프가 다르다.

초급자가 먼저 헷갈리는 "시간 지표 3개"를 분리하면 이후 문서 이해가 쉬워진다.

| 지표 | 뜻 | 사용자가 체감하는 질문 |
|------|----|------------------------|
| 응답 시간(Response Time) | 요청 후 "첫 반응"까지 걸린 시간 | "클릭했더니 언제 처음 반응했나?" |
| 대기 시간(Waiting Time) | ready queue에서 CPU를 기다린 시간 합 | "실행 가능했는데 줄에서 얼마나 기다렸나?" |
| 반환 시간(Turnaround Time) | 도착부터 완료까지 전체 시간 | "요청부터 끝까지 총 몇 초 걸렸나?" |

## 한눈에 보기

| 알고리즘 | 핵심 규칙 | 장점 | 단점 |
|----------|-----------|------|------|
| FCFS | 먼저 온 순서대로 처리 | 구현 단순 | 긴 작업 뒤에 짧은 작업이 오래 기다림(convoy effect) |
| SJF | 짧은 작업 먼저 처리 | 평균 대기 시간 최소 | 긴 작업은 계속 밀릴 수 있음(기아) |
| Round Robin | 타임 슬라이스만큼 돌아가며 배분 | 공정성 높음 | 문맥 전환 비용 발생 |
| 우선순위 | 우선순위 높은 것 먼저 | 중요 작업 빠르게 | 낮은 우선순위 기아 문제 |

## 상세 분해

### 선점형 vs 비선점형

- **비선점형(non-preemptive)**: 실행 중인 프로세스가 스스로 CPU를 양보할 때까지 기다린다. FCFS, SJF 기본형이 여기에 속한다.
- **선점형(preemptive)**: OS가 타임 슬라이스 초과 또는 더 높은 우선순위 프로세스 도착 시 강제로 CPU를 빼앗는다. Round Robin이 대표적이다.

현대 OS는 대부분 선점형을 사용한다. 응답성이 훨씬 좋기 때문이다.

### 타임 슬라이스(time slice)

Round Robin에서 각 프로세스에 주어지는 최대 실행 시간이다. 너무 짧으면 문맥 전환이 많아지고, 너무 길면 FCFS와 다를 게 없어진다. 일반적으로 10~100ms 범위를 사용한다.

### 준비 큐(ready queue)

실행 가능 상태의 프로세스들이 대기하는 자료구조다. 스케줄러는 준비 큐에서 다음 실행 대상을 선택한다.

## 아주 작은 예시: FCFS vs Round Robin 체감

세 작업이 동시에 도착했다고 가정하자.

- `P1`: 8ms
- `P2`: 2ms
- `P3`: 2ms

| 방식 | 실행 순서(단순화) | 짧은 작업 첫 응답 시점 | 초급자 체감 |
|------|-------------------|-------------------------|-------------|
| FCFS | `P1 -> P2 -> P3` | `P2=8ms`, `P3=10ms` | 긴 작업 하나가 앞에 있으면 뒤 요청이 오래 기다린다 |
| RR(타임 슬라이스 2ms) | `P1 -> P2 -> P3 -> P1 ...` | `P2=2ms`, `P3=4ms` | 짧은 작업의 첫 응답이 훨씬 빨라진다 |

여기서 핵심은 평균 처리량보다 "사용자가 체감하는 첫 응답"이 스케줄링 정책에 크게 좌우된다는 점이다.

## 흔한 오해와 함정

- "SJF가 항상 최선이다" — 실제로 작업 실행 시간을 미리 알기 어렵다. SJF는 이론적 최적 기준으로 쓰인다.
- "우선순위가 높으면 반드시 먼저 실행된다" — 선점형에서는 맞지만, 비선점형에서는 현재 실행 중인 프로세스가 끝나야 한다.
- "문맥 전환은 공짜다" — 문맥 전환은 레지스터·메모리 상태를 저장·복원하는 실제 비용이다. 타임 슬라이스를 너무 짧게 잡으면 문맥 전환 비용이 유용한 실행 시간을 초과할 수 있다.
- "코어가 여러 개면 스케줄링은 중요하지 않다" — 코어가 늘어도 runnable 스레드가 더 많으면 여전히 대기열과 공정성 문제가 생긴다.
- "CPU 사용률이 100%면 무조건 나쁜 상태다" — 배치 작업에서는 정상일 수 있다. 중요한 건 `run queue` 길이, 지연 시간, SLA 위반 여부를 함께 보는 것이다.

## 다음으로 어디를 읽을까? (초심자 라우팅)

| 지금 막힌 질문 | 다음 문서 | 이유 |
|----------------|-----------|------|
| "CPU는 바쁜데 진짜 포화인지 잘 모르겠다" | [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md) | `run queue`와 `load average`를 함께 읽는 기준을 잡을 수 있다. |
| "문맥 전환이 왜 느린지 감이 안 온다" | [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md) | 스케줄러 결정 이후 실제 전환 비용이 어디서 생기는지 연결된다. |
| "운영 중 지표를 어떤 순서로 보면 되나" | [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md) | `vmstat`, `/proc/<pid>/sched`, `runqlat`를 초급자 순서로 확인할 수 있다. |

## 실무에서 쓰는 모습

Linux는 CFS(Completely Fair Scheduler)를 기본 스케줄러로 사용한다. `nice` 값으로 우선순위 가중치를 주되, 모든 프로세스가 CPU를 공정하게 나눠 갖도록 가상 런타임(vruntime)을 기준으로 정렬한다.

백엔드 서버에서 직접 스케줄러 알고리즘을 선택할 일은 드물지만, 스케줄링 원리를 알면 "스레드가 많아지면 왜 응답이 느려지나", "CPU가 포화상태인데 왜 특정 요청만 늦나" 같은 문제를 해석할 수 있다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "지금 느린 원인이 CPU 포화인지"부터 분리하려면: [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - "운영에서 어떤 순서로 관측할지"가 필요하면: [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)
> - "wakeup 지연/큐잉 병목까지" 들어가려면: [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)

## 더 깊이 가려면

- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md) — 스케줄러가 CPU를 넘길 때 내부에서 무슨 일이 일어나는지 본다.
- [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md) — 스케줄 대상인 프로세스·스레드의 상태 모델을 다시 확인한다.
- [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md) — `load average`, `vmstat r`, `/proc/<pid>/sched`를 초급자 순서로 읽는다.
- [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md) — "느리다"를 run queue 신호로 해석하는 방법을 익힌다.

## 면접/시니어 질문 미리보기

1. **Round Robin의 타임 슬라이스를 너무 짧게 잡으면 어떤 문제가 생기나요?**
   의도: 문맥 전환 비용 인식 확인. 핵심 답: "문맥 전환이 너무 자주 발생해 실제 작업 시간보다 전환 비용이 커진다."

2. **선점형과 비선점형 스케줄링의 차이와 현대 OS의 선택 이유는?**
   의도: 응답성 트레이드오프 이해 확인. 핵심 답: "선점형은 우선순위 높은 작업의 응답성을 보장하므로 대화형 시스템에 적합하다."

## Self-check (자가 점검 4문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. ready queue가 길어진다는 신호가 "CPU가 실제로 바쁘다"는 뜻인지, 아니면 다른 병목 때문인지 추가 분기가 필요하다는 점을 알고 있는가?
   힌트: ready queue 증가는 출발 신호일 뿐이라 CPU 사용률, I/O 대기, quota 제한을 같이 봐야 원인이 좁혀진다.
2. FCFS와 RR 차이를 "평균 처리량"보다 "짧은 작업의 첫 응답" 관점으로 설명할 수 있는가?
   힌트: RR은 짧은 작업에 빨리 첫 CPU 기회를 주기 쉬워 체감 응답을 개선한다.
3. 선점형/비선점형 차이를 실제 사용자 체감(응답성)과 연결해 설명할 수 있는가?
   힌트: 선점형은 긴 작업이 있어도 새 요청이 오래 굶지 않게 해 화면 반응을 지켜 준다.
4. CPU 사용률 숫자 하나만으로 상태를 단정하지 않고 `run queue`와 지연 지표를 함께 보겠다는 체크리스트를 세웠는가?
   힌트: "CPU% + run queue + tail latency" 3개를 같이 보는 습관이 오판을 가장 많이 줄인다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`지금 느린 게 진짜 CPU 포화인가?`"가 궁금하면: [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - "`초보자 기준으로 스케줄러 관측 순서를 어떻게 잡지?`"가 궁금하면: [Scheduler Observation Starter Guide](./scheduler-observation-starter-guide.md)
> - "`wakeup 지연`과 `runqlat`은 어떻게 이어지지?`"가 궁금하면: [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - "`컨텍스트 스위치 비용`과 `lock-free`는 어디서 같이 보지?`"가 궁금하면: [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
> - "`다른 operating-system primer는 어디서 다시 고르지?`"가 궁금하면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

CPU 스케줄러는 준비 큐에서 다음 실행 프로세스를 고르는 장치이고, 공정성·응답 시간·처리량 사이의 균형이 알고리즘 선택 기준이다.
