# CPU 스케줄링 기초

> 한 줄 요약: CPU 스케줄러는 실행 가능한 여러 프로세스 중 다음에 CPU를 줄 프로세스를 선택하는 장치이고, 기준은 공정성·응답 시간·처리량의 균형이다.

**난이도: 🟢 Beginner**

관련 문서:

- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
- [operating-system 카테고리 인덱스](./README.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)

retrieval-anchor-keywords: cpu 스케줄링 기초, cpu scheduling beginner, 스케줄러란, process scheduling basics, round robin 스케줄링, fcfs scheduling, sjf scheduling, preemptive scheduling, 선점형 스케줄링, 비선점형 스케줄링, 타임 슬라이스, time slice basics, 스케줄링 알고리즘

## 핵심 개념

운영체제 면접에서 "CPU 스케줄링이 뭐예요?"라는 질문이 자주 나온다. 핵심은 이것이다.

멀티태스킹 OS에서는 실행할 준비가 된 프로세스(스레드)가 여러 개다. CPU는 한 번에 하나만 실행할 수 있으므로, OS는 "지금 누구를 돌릴지" 결정해야 한다. 이 결정을 내리는 모듈이 **CPU 스케줄러(scheduler)**다.

스케줄러가 고려하는 목표는 크게 세 가지다.

- **CPU 활용률(utilization)**: CPU를 최대한 바쁘게 유지한다.
- **응답 시간(response time)**: 요청 후 첫 응답까지 짧게 유지한다.
- **공정성(fairness)**: 특정 프로세스가 CPU를 독점하지 않도록 한다.

이 세 목표는 동시에 최적화하기 어렵고, 알고리즘마다 트레이드오프가 다르다.

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

## 흔한 오해와 함정

- "SJF가 항상 최선이다" — 실제로 작업 실행 시간을 미리 알기 어렵다. SJF는 이론적 최적 기준으로 쓰인다.
- "우선순위가 높으면 반드시 먼저 실행된다" — 선점형에서는 맞지만, 비선점형에서는 현재 실행 중인 프로세스가 끝나야 한다.
- "문맥 전환은 공짜다" — 문맥 전환은 레지스터·메모리 상태를 저장·복원하는 실제 비용이다. 타임 슬라이스를 너무 짧게 잡으면 문맥 전환 비용이 유용한 실행 시간을 초과할 수 있다.

## 실무에서 쓰는 모습

Linux는 CFS(Completely Fair Scheduler)를 기본 스케줄러로 사용한다. `nice` 값으로 우선순위 가중치를 주되, 모든 프로세스가 CPU를 공정하게 나눠 갖도록 가상 런타임(vruntime)을 기준으로 정렬한다.

백엔드 서버에서 직접 스케줄러 알고리즘을 선택할 일은 드물지만, 스케줄링 원리를 알면 "스레드가 많아지면 왜 응답이 느려지나", "CPU가 포화상태인데 왜 특정 요청만 늦나" 같은 문제를 해석할 수 있다.

## 더 깊이 가려면

- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md) — 스케줄러가 CPU를 넘길 때 내부에서 무슨 일이 일어나는지 본다.
- [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md) — 스케줄 대상인 프로세스·스레드의 상태 모델을 다시 확인한다.

## 면접/시니어 질문 미리보기

1. **Round Robin의 타임 슬라이스를 너무 짧게 잡으면 어떤 문제가 생기나요?**
   의도: 문맥 전환 비용 인식 확인. 핵심 답: "문맥 전환이 너무 자주 발생해 실제 작업 시간보다 전환 비용이 커진다."

2. **선점형과 비선점형 스케줄링의 차이와 현대 OS의 선택 이유는?**
   의도: 응답성 트레이드오프 이해 확인. 핵심 답: "선점형은 우선순위 높은 작업의 응답성을 보장하므로 대화형 시스템에 적합하다."

## 한 줄 정리

CPU 스케줄러는 준비 큐에서 다음 실행 프로세스를 고르는 장치이고, 공정성·응답 시간·처리량 사이의 균형이 알고리즘 선택 기준이다.
