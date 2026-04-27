# 뮤텍스와 교착상태 기초

> 한 줄 요약: 뮤텍스는 공유 자원을 한 번에 하나의 스레드만 사용하도록 잠그는 장치이고, 교착상태는 서로 다른 자원을 쥐고 상대방의 자원을 기다릴 때 발생한다.

**난이도: 🟢 Beginner**

관련 문서:

- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [Futex, Mutex, Semaphore, Spinlock](./futex-mutex-semaphore-spinlock.md)
- [operating-system 카테고리 인덱스](./README.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)

retrieval-anchor-keywords: 뮤텍스란, 교착상태란, mutex beginner, deadlock beginner, 데드락이란, mutex lock unlock, critical section basics, race condition basics, 임계구역, deadlock conditions, 교착상태 발생 조건, 스레드 동기화 기초, mutex deadlock basics basics, mutex deadlock basics beginner, mutex deadlock basics intro

## 먼저 잡는 멘탈 모델

멀티스레드 환경에서 두 스레드가 같은 변수를 동시에 쓰면 어떻게 될까? 예를 들어 두 스레드가 `count++`를 동시에 실행하면, 실제로는 `읽기 → 증가 → 쓰기` 세 단계가 겹쳐서 증가가 한 번만 반영될 수 있다. 이런 상황을 **경쟁 조건(race condition)**이라 한다.

이를 막으려면 한 스레드가 실행하는 동안 다른 스레드가 접근하지 못하도록 **임계 구역(critical section)**을 보호해야 한다. 가장 흔한 도구가 **뮤텍스(mutex, mutual exclusion)**다.

뮤텍스는 자물쇠와 같다. 잠그면(`lock`) 다른 스레드는 기다려야 하고, 해제하면(`unlock`) 대기 중인 스레드가 들어갈 수 있다.

## 한눈에 보기

뮤텍스는 "잠금 → 사용 → 해제" 순서를 강제해 임계 구역을 한 번에 하나의 스레드만 진입하도록 만든다.

스레드 A와 B가 같은 뮤텍스를 경쟁하는 흐름:

```text
스레드 A                          스레드 B
mutex.lock()  ---[잠김]-->
  공유 자원 사용                  mutex.lock() 시도 -> 대기
mutex.unlock() -[잠금 해제]-->
                                  mutex.lock() 획득
                                    공유 자원 사용
                                  mutex.unlock()
```

뮤텍스는 항상 잠근 스레드가 직접 해제해야 한다. 이 소유권 규칙이 세마포어와 다른 핵심 특징이다.

핵심 속성 비교:

| 속성 | 뮤텍스 | 이진 세마포어 |
|------|--------|---------------|
| 소유권 | 잠근 스레드만 해제 가능 | 누구든 signal 가능 |
| 용도 | 임계 구역 1개 보호 | 자원 1개 제어 |
| 재귀 획득 | 구현에 따라 지원 | 보통 안 됨 |

## 상세 분해

### 교착상태(Deadlock) 4가지 조건

교착상태는 아래 네 조건이 동시에 성립할 때 발생한다. 하나라도 깨면 교착상태가 일어나지 않는다.

1. **상호 배제(mutual exclusion)**: 자원은 한 번에 하나의 스레드만 사용 가능하다.
2. **점유와 대기(hold and wait)**: 자원을 쥔 채로 다른 자원을 기다린다.
3. **비선점(no preemption)**: 자원을 강제로 빼앗을 수 없다.
4. **순환 대기(circular wait)**: A가 B를 기다리고, B가 A를 기다리는 원형 구조가 생긴다.

### 교착상태 예시

```text
스레드 A: lock(자원1) → lock(자원2) 시도 → 대기
스레드 B: lock(자원2) → lock(자원1) 시도 → 대기
```

두 스레드가 서로 상대방이 쥔 자원을 기다려 영원히 진행되지 않는다.

### 기본 예방법

- **순서 일관성**: 모든 스레드가 동일한 순서로 자원에 잠금을 건다. 위 예시라면 항상 자원1 → 자원2 순서로 잠근다.
- **타임아웃**: 잠금 시도에 시간 제한을 두고, 초과 시 이미 쥔 자원을 놓고 재시도한다.

## 흔한 오해와 함정

- "synchronized 블록은 무조건 안전하다" — 두 잠금을 다른 순서로 획득하면 synchronized 안에서도 교착상태가 생긴다.
- "뮤텍스를 많이 쓸수록 안전하다" — 잠금이 늘어날수록 교착상태 가능성도 올라간다. 임계 구역을 좁게 잡는 것이 기본 원칙이다.
- "교착상태는 드문 버그다" — 스레드 수가 많아질수록, 잠금 순서가 복잡해질수록 재현 빈도가 크게 높아진다.

## 실무에서 쓰는 모습

Java에서는 `synchronized` 키워드나 `ReentrantLock`으로 임계 구역을 보호한다.

```java
// 간단한 synchronized 예시
synchronized (this) {
    count++;
}
```

실제 서버에서 교착상태가 발생하면 스레드가 영원히 응답을 못 해 타임아웃이 쌓이는 증상이 나타난다. `jstack` 명령어나 Java 프로파일러로 스레드 덤프를 확인하면 `BLOCKED` 상태의 스레드와 대기 중인 자원을 볼 수 있다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "락 도구들 차이를 OS 레벨에서 정리"하려면: [Futex, Mutex, Semaphore, Spinlock](./futex-mutex-semaphore-spinlock.md)
> - "운영 중 락 경합 때문에 느린지"를 확인하려면: [Lock Contention, Futex Wait, Off-CPU Debugging](./lock-contention-futex-offcpu-debugging.md)
> - "교착상태/우선순위 역전까지" 확장하려면: [Futex Requeue, Priority Inheritance, Convoy Debugging](./futex-requeue-priority-inheritance-convoy-debugging.md)

## 더 깊이 가려면

- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md) — 교착상태를 더 깊게 다루고 lock-free 대안까지 연결한다.
- [Futex, Mutex, Semaphore, Spinlock](./futex-mutex-semaphore-spinlock.md) — 뮤텍스 구현 내부와 세마포어 차이를 OS 수준에서 본다.

## 면접/시니어 질문 미리보기

1. **교착상태가 발생하는 4가지 조건을 설명하고, 하나를 깨는 방법은?**
   의도: 교착상태 원리를 이해했는지 확인. 핵심 답: "순환 대기를 깨는 가장 쉬운 방법은 잠금 획득 순서를 전역적으로 통일하는 것이다."

2. **뮤텍스와 세마포어는 어떻게 다른가요?**
   의도: 동기화 도구 차이 인식 확인. 핵심 답: "뮤텍스는 잠근 스레드만 해제할 수 있고 1개 자원 보호에 쓰이며, 세마포어는 카운터로 N개 자원 동시 접근을 제어한다."

## 한 줄 정리

뮤텍스는 임계 구역을 하나의 스레드만 진입하도록 잠그는 도구이고, 교착상태는 여러 잠금을 서로 다른 순서로 획득할 때 순환 대기가 생겨 발생한다.
