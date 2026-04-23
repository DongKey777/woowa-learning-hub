# Thread Dump State Interpretation

> 한 줄 요약: thread dump의 `RUNNABLE`, `BLOCKED`, `WAITING`, `TIMED_WAITING`, `in native` 같은 상태는 "지금 무엇을 기다리는가"를 보여주며, 진짜 병목은 상태 이름보다 그 상태에 들어간 이유와 소유자다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)
> - [JFR Event Interpretation](./jfr-event-interpretation.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)
> - [`wait`/`notify`, `Condition`, Spurious Wakeup, and Lost Signal](./wait-notify-condition-spurious-wakeup-lost-signal.md)
> - [`LockSupport.park`/`unpark` Permit Semantics and Coordination Pitfalls](./locksupport-park-unpark-permit-semantics.md)
> - [JNI Native Call Overhead](./jni-native-call-overhead.md)

> retrieval-anchor-keywords: thread dump, RUNNABLE, BLOCKED, WAITING, TIMED_WAITING, in native, monitor owner, lock contention, parked thread, native blocked, native waiting, thread state interpretation, wait notify, Condition, lost signal, LockSupport, park, unpark, blocker

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

thread dump는 JVM thread의 순간 스냅샷이다.  
상태 이름만 보고 단정하면 안 되고, stack trace와 lock owner를 같이 읽어야 한다.

대표 상태:

- `RUNNABLE`
- `BLOCKED`
- `WAITING`
- `TIMED_WAITING`
- `in native`

## 깊이 들어가기

### 1. RUNNABLE이 항상 "잘 도는 중"은 아니다

RUNNABLE은 OS 관점에서 실행 가능 상태라는 뜻이지, CPU를 실제로 계속 먹고 있다는 뜻은 아니다.  
busy loop, native spin, hot lock loop가 다 RUNNABLE로 보일 수 있다.

### 2. BLOCKED는 monitor 경쟁의 신호다

`BLOCKED`는 synchronized monitor 진입을 못 하고 있는 경우가 많다.  
이때 가장 먼저 봐야 할 것은 lock owner와 lock을 오래 쥐는 코드다.

### 3. WAITING과 TIMED_WAITING은 자발적 대기다

- `WAITING`: `Object.wait()`, `LockSupport.park()` 같은 무기한 대기
- `TIMED_WAITING`: sleep, timed park, timed wait

대기 자체는 정상일 수 있다.  
중요한 것은 "왜 여기서 멈춰 있는가"다.

특히 `Object.wait()`나 `Condition.await()`가 보이면 predicate loop와 signal 규약이 맞는지 [wait/notify, Condition, Spurious Wakeup, and Lost Signal](./wait-notify-condition-spurious-wakeup-lost-signal.md)을 같이 보는 편이 좋다.
`LockSupport.park()`가 보이면 permit가 남아 있었는지, blocker가 무엇인지, interrupt로 깼는지도 함께 봐야 한다.

### 4. in native는 JVM 밖 구간일 수 있다

native method, JNI, JVM 내부 작업이 섞이면 `in native`로 보일 수 있다.  
이 상태만으로는 좋고 나쁨을 판단할 수 없다.

### 5. thread dump는 pause를 유발할 수 있다

thread dump를 뜨는 순간 모든 thread를 잠깐 멈춰야 하므로, 관측 자체가 짧은 pause를 만들 수 있다.  
그래서 thread dump는 증거로 쓰되 과도하게 남발하지 않는 것이 좋다.

## 실전 시나리오

### 시나리오 1: BLOCKED가 몰려 있다

공유 lock, 거대한 synchronized 블록, 싱글 워커, 혹은 잘못된 resource serialization을 의심한다.

### 시나리오 2: WAITING이 많다

생산자/소비자 구조, queue backpressure, `join()`, `park()` 등을 본다.  
정상적인 대기인지, 교착에 가까운 대기인지 구분해야 한다.

### 시나리오 3: RUNNABLE인데 CPU는 낮다

native wait, spin, lock contention, scheduler 문제, I/O 경합을 의심한다.  
JFR이나 OS-level profiling과 같이 봐야 한다.

## 코드로 보기

### 1. monitor contention 예

```java
public class SharedCounter {
    private int value;

    public synchronized int increment() {
        return ++value;
    }
}
```

### 2. wait/notify 예

```java
synchronized (lock) {
    while (!ready) {
        lock.wait();
    }
}
```

### 3. park/wait 감각

```java
java.util.concurrent.locks.LockSupport.parkNanos(1_000_000L);
```

### 4. thread dump를 읽는 감각

```text
Thread-1 BLOCKED on monitor owned by Thread-7
Thread-2 WAITING on condition queue
Thread-3 in native
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| thread dump | 즉시 상태를 볼 수 있다 | 관측 순간 pause가 생긴다 |
| JFR | 시간축과 상태를 함께 본다 | 해석에 시간이 든다 |
| OS profiler | CPU/lock 진단이 강하다 | JVM 내부 맥락은 약할 수 있다 |
| 단순 로그 | 구현이 쉽다 | 상태의 실제 원인을 놓치기 쉽다 |

핵심은 thread dump를 상태표가 아니라 원인 탐색의 출발점으로 쓰는 것이다.

## 꼬리질문

> Q: RUNNABLE인데 왜 느릴 수 있나요?
> 핵심: busy spin, native 구간, lock 경합, scheduler 영향이 있을 수 있다.

> Q: BLOCKED와 WAITING 차이는 무엇인가요?
> 핵심: BLOCKED는 monitor 진입 대기이고, WAITING은 wait/park 같은 자발적 대기다.

> Q: thread dump만으로 원인을 확정할 수 있나요?
> 핵심: 보통은 안 된다. lock owner, stack trace, JFR 같은 보조 증거가 필요하다.

## 한 줄 정리

thread dump 상태는 증상 힌트일 뿐이고, 진짜 병목은 상태를 만든 lock owner, wait reason, native 구간, 그리고 시간축 맥락을 함께 봐야 드러난다.
