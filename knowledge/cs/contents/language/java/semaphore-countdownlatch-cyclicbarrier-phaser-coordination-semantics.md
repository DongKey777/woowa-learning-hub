# `Semaphore`, `CountDownLatch`, `CyclicBarrier`, and `Phaser` Coordination Semantics

> 한 줄 요약: 이 도구들은 모두 "스레드를 기다리게 한다"는 공통점이 있지만 의미가 전혀 다르다. permit 제어, one-shot 완료 대기, rendezvous barrier, 다단계 phase 진행을 섞어 쓰면 startup hang, permit leak, broken barrier, 재시도 꼬임이 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [`wait`/`notify`, `Condition`, Spurious Wakeup, and Lost Signal](./wait-notify-condition-spurious-wakeup-lost-signal.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)

> retrieval-anchor-keywords: Semaphore, CountDownLatch, CyclicBarrier, Phaser, permit leak, one-shot latch, barrier break, coordination primitive, acquire release, countdown hang, phased execution, startup gate, bulkhead, interruptible wait

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

네 도구는 목적이 다르다.

- `Semaphore`: 동시에 들어갈 수 있는 수량을 제어한다
- `CountDownLatch`: 어떤 일이 끝날 때까지 한 번 기다린다
- `CyclicBarrier`: 정해진 인원이 모두 도착할 때까지 서로 기다린다
- `Phaser`: 여러 phase를 동적으로 진행한다

즉 "기다림"이 아니라 **무엇을 세고 있는가**를 먼저 봐야 한다.

## 깊이 들어가기

### 1. `Semaphore`는 ownership 없는 permit다

`Semaphore`는 lock과 다르다.

- permit는 특정 thread가 소유하지 않는다
- acquire한 thread와 release하는 thread가 달라도 된다
- resource pool, rate limiting, bulkhead에 자주 쓰인다

장점은 유연성이지만, 그만큼 leak와 double-release 위험이 있다.

즉 `Semaphore`는 mutual exclusion보다 capacity control에 가깝다.

### 2. `CountDownLatch`는 one-shot gate다

`CountDownLatch`는 count가 0이 되면 열린다.  
그리고 다시 닫히지 않는다.

그래서 잘 맞는 곳:

- startup initialization 대기
- fan-out 작업 완료 합류
- 테스트에서 비동기 완료 대기

잘 안 맞는 곳:

- 반복되는 라운드
- reset이 필요한 프로토콜

### 3. `CyclicBarrier`는 rendezvous다

`CyclicBarrier`는 참여자들이 모두 barrier에 도착해야 다음 단계로 넘어간다.  
즉 "한쪽이 끝나길 기다리는 것"이 아니라 "모두 같이 모인다"는 semantics다.

중요한 점:

- 한 참가자가 실패하거나 interrupt되면 barrier가 깨질 수 있다
- broken barrier 상태를 호출자가 이해해야 한다

즉 barrier는 성공 경로만큼 실패 경로 설계가 중요하다.

### 4. `Phaser`는 phase 수명 관리 도구다

`Phaser`는 barrier보다 유연하다.

- phase가 여러 번 진행된다
- 참여자 수를 동적으로 등록/해제할 수 있다
- 큰 배치나 staged workflow에 맞을 수 있다

대신 읽기와 디버깅 난도가 올라간다.  
간단한 문제엔 과한 경우가 많다.

### 5. interruption과 timeout을 무시하면 coordination이 hang으로 바뀐다

이 도구들은 모두 "기다림"을 포함하므로 취소와 timeout 설계가 중요하다.

- count가 영영 0이 안 되는 latch
- release 누락된 semaphore
- broken barrier를 무시한 재시도
- deregister되지 않아 phase가 끝나지 않는 phaser

backend에서는 이런 문제가 보통 startup hang, stuck batch, queue drain 실패로 나타난다.

## 실전 시나리오

### 시나리오 1: 외부 API bulkhead를 만들고 싶다

요청 수를 제한하려는 문제면 `Semaphore`가 더 맞다.  
`CountDownLatch`로는 "동시 허용 수" 개념을 표현하기 어렵다.

### 시나리오 2: 애플리케이션 기동 시 warm-up 완료를 기다린다

여러 초기화 작업이 끝난 뒤 only-once gate를 열고 싶다면 `CountDownLatch`가 자연스럽다.

### 시나리오 3: 병렬 계산 라운드를 여러 번 돈다

각 라운드마다 참여자들이 모두 합류해야 한다면 `CyclicBarrier`나 `Phaser`가 후보다.  
한 번 쓰고 끝나는 latch는 맞지 않는다.

### 시나리오 4: semaphore permit가 회수되지 않는다

예외 경로에서 `release()`가 빠지면 처리량이 서서히 줄고 결국 전체가 멈춘다.  
이 문제는 deadlock처럼 보이지만, 실제로는 capacity leak다.

## 코드로 보기

### 1. bulkhead 용도의 `Semaphore`

```java
import java.util.concurrent.Semaphore;

Semaphore permits = new Semaphore(20);

if (!permits.tryAcquire()) {
    throw new IllegalStateException("too many concurrent calls");
}

try {
    callRemote();
} finally {
    permits.release();
}
```

### 2. startup gate로 `CountDownLatch`

```java
import java.util.concurrent.CountDownLatch;

CountDownLatch ready = new CountDownLatch(3);

// worker들이 준비되면 ready.countDown()
ready.await();
```

### 3. 반복 라운드용 `CyclicBarrier`

```java
import java.util.concurrent.CyclicBarrier;

CyclicBarrier barrier = new CyclicBarrier(4, this::afterRound);
barrier.await();
```

### 4. 동적 참여자용 `Phaser`

```java
import java.util.concurrent.Phaser;

Phaser phaser = new Phaser(1);
phaser.register();
phaser.arriveAndAwaitAdvance();
phaser.arriveAndDeregister();
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `Semaphore` | 동시 허용량 제어가 직관적이다 | permit leak와 fairness 비용을 직접 관리해야 한다 |
| `CountDownLatch` | one-shot 완료 대기에 단순하다 | reset이 안 된다 |
| `CyclicBarrier` | 반복 라운드 합류를 잘 표현한다 | broken barrier와 실패 처리가 까다롭다 |
| `Phaser` | 다단계와 동적 참여자에 유연하다 | 가독성과 디버깅 난도가 높다 |

핵심은 "스레드를 막는다"가 아니라 "무엇을 세고 있으며 언제 다시 열리는가"다.

## 꼬리질문

> Q: `Semaphore`와 lock의 차이는 무엇인가요?
> 핵심: semaphore는 ownership 없는 permit 수량 제어이고, lock은 임계구역 소유에 가깝다.

> Q: `CountDownLatch`를 왜 반복 작업에 쓰면 안 되나요?
> 핵심: one-shot이어서 한 번 열리면 reset되지 않기 때문이다.

> Q: `CyclicBarrier`가 깨진다는 것은 무슨 뜻인가요?
> 핵심: 일부 참가자의 실패나 interrupt로 전체 rendezvous가 성립하지 못한 상태다.

> Q: `Phaser`는 언제 고려하나요?
> 핵심: 여러 phase를 거치고 참여자가 동적으로 늘고 줄어드는 coordination이 필요할 때다.

## 한 줄 정리

`Semaphore`, `CountDownLatch`, `CyclicBarrier`, `Phaser`는 모두 대기 도구가 아니라 서로 다른 coordination contract이므로, 세는 대상과 실패 경로를 먼저 맞춰야 한다.
