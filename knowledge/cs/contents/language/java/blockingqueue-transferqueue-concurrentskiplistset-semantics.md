# `BlockingQueue`, `TransferQueue`, and `ConcurrentSkipListSet` Semantics

> 한 줄 요약: `BlockingQueue`, `TransferQueue`, `ConcurrentSkipListSet`은 모두 concurrent collection이지만, 실제로는 "얼마나 버퍼링할 것인가", "소비자가 실제로 받았는가", "정렬된 membership를 어떤 일관성으로 볼 것인가"라는 서로 다른 계약을 표현한다. 이를 섞어 쓰면 queue saturation 오해, 가짜 backpressure, comparator 기반 dedupe 버그가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [`ConcurrentSkipListMap`, `ConcurrentLinkedQueue`, and `CopyOnWriteArraySet` Trade-offs](./concurrentskiplistmap-concurrentlinkedqueue-copyonwritearrayset-tradeoffs.md)
> - [`wait`/`notify`, `Condition`, Spurious Wakeup, and Lost Signal](./wait-notify-condition-spurious-wakeup-lost-signal.md)
> - [Java Collections 성능 감각](./collections-performance.md)

> retrieval-anchor-keywords: BlockingQueue, ArrayBlockingQueue, LinkedBlockingQueue, SynchronousQueue, TransferQueue, LinkedTransferQueue, ConcurrentSkipListSet, backpressure semantics, bounded queue, queue saturation, producer throttling, put vs offer, transfer vs put, tryTransfer, direct handoff, weakly consistent iterator, sorted concurrent set, comparator consistency, range view, queue depth, latency debt

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [빠른 비교](#빠른-비교)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

핵심 질문은 "thread-safe한가"가 아니라 **부하와 관측을 어떤 계약으로 표현하느냐**다.

- `BlockingQueue`: producer와 consumer 사이에 버퍼와 대기 정책을 둔다.
- `TransferQueue`: element를 큐에 넣는 것과 소비자에게 직접 넘기는 것을 구분한다.
- `ConcurrentSkipListSet`: 정렬된 membership와 range view를 concurrent하게 유지한다.

즉 queueing, handoff, sorted membership는 서로 다른 문제다.

## 빠른 비교

| 구조 | 중심 계약 | backpressure가 생기는 지점 | 자주 하는 오해 |
|---|---|---|---|
| `BlockingQueue` | 버퍼 + 대기/실패 정책 | bounded capacity와 `put`/`offer(timeout)`/실패 처리 | queue 타입만 바꾸면 overload가 해결된다고 생각함 |
| `TransferQueue` | 소비자 수신 여부를 연산 수준에서 표현 | `transfer`/`tryTransfer(timeout)` 같은 직접 handoff 연산 | `LinkedTransferQueue`면 항상 backpressure가 있다고 생각함 |
| `ConcurrentSkipListSet` | 정렬된 concurrent membership | backpressure가 아니라 ordering/iteration semantics 문제 | 정렬되어 있으니 snapshot처럼 정확하다고 생각함 |

## 깊이 들어가기

### 1. `BlockingQueue`는 "가득 찼을 때 무엇을 할지"가 본질이다

`BlockingQueue`를 고를 때는 구현체 이름보다 메서드 의미를 먼저 봐야 한다.

| 생산자 연산 | queue가 가득 찼을 때 | 보통의 의미 |
|---|---|---|
| `add(e)` | 예외 발생 | full이 애플리케이션 버그일 때 |
| `offer(e)` | `false` 반환 | 빠른 실패와 명시적 shedding |
| `offer(e, timeout, unit)` | 일정 시간 대기 후 실패 | soft backpressure |
| `put(e)` | 공간이 날 때까지 대기 | cooperative throttling |

소비자 쪽도 비슷하다.

- `take()`는 element가 올 때까지 기다린다.
- `poll()`은 없으면 바로 `null`을 준다.
- `poll(timeout, unit)`은 bounded wait를 표현한다.

중요한 점은 `put`과 `take`가 interruptible blocking이라는 점이다.  
shutdown이나 cancellation 경로를 설계하지 않으면 queue는 편한 API가 아니라 hang 지점이 된다.

### 2. backpressure는 boundedness에서 시작하지만, 호출자 처리까지 가야 완성된다

`BlockingQueue`가 있다고 해서 backpressure가 자동으로 생기지는 않는다.

- `ArrayBlockingQueue`: 고정 크기 배열 기반이라 메모리 상한이 명확하고, fairness 옵션은 순서를 더 예측 가능하게 하지만 throughput 비용이 있다.
- `LinkedBlockingQueue`: capacity를 주지 않으면 사실상 매우 큰 버퍼를 택한 셈이다.
- `SynchronousQueue`: capacity가 0이라 저장 없이 handoff만 허용한다.

즉 "queue를 쓴다"와 "압력을 제어한다"는 다르다.

대표적인 함정은 다음과 같다.

- unbounded 또는 사실상 큰 queue에 계속 `put`해서 latency debt를 숨긴다.
- `offer`가 `false`를 반환해도 재시도 루프로 즉시 밀어 넣어 backpressure 신호를 무시한다.
- `size()`를 admission control 기준으로 써서 TOCTOU race를 만든다.

`size()`와 `remainingCapacity()`는 관측용 힌트로는 쓸 수 있어도,  
"지금 안전하니 넣어도 된다"는 정확한 승인 토큰이 아니다.

### 3. `TransferQueue`의 핵심은 queue type이 아니라 연산 semantics다

`TransferQueue`는 `BlockingQueue`를 확장하지만, 의미가 완전히 같다 생각하면 안 된다.  
대표 구현인 `LinkedTransferQueue`는 기본적으로 unbounded라서, 타입 이름만 보고 bounded backpressure를 기대하면 틀린다.

`LinkedTransferQueue`에서 중요한 차이는 다음이다.

- `put(e)` / `offer(e)`: 일반 enqueue처럼 동작할 수 있다.
- `transfer(e)`: 어떤 consumer가 실제로 받아 갈 때까지 대기한다.
- `tryTransfer(e)`: 대기 중인 consumer가 있을 때만 즉시 넘기고, 아니면 실패한다.
- `tryTransfer(e, timeout, unit)`: 직접 handoff를 일정 시간까지 기다린다.

즉 `LinkedTransferQueue`는 "항상 backpressure가 있는 queue"가 아니다.  
`put`을 쓰면 그냥 잘 쌓일 수 있고, `transfer`를 써야 소비자 준비 상태와 producer 진행이 직접 묶인다.

이 차이는 `SynchronousQueue`와 비교하면 더 선명하다.

- `SynchronousQueue`: 저장 공간이 없어 모든 성공이 direct handoff다.
- `LinkedTransferQueue`: enqueue도 가능하고 direct handoff도 가능하다.

따라서 "consumer가 받기 전에는 다음 단계로 못 간다"가 요구사항이면  
구조 이름보다 `transfer` 계열 메서드를 실제로 쓰고 있는지 확인해야 한다.

또한 `hasWaitingConsumer()`와 `getWaitingConsumerCount()` 같은 값은 관측용 힌트로는 쓸 수 있지만,  
동시 변경 중 정확한 protocol gate로 쓰기엔 약하다.

### 4. `ConcurrentSkipListSet`은 정렬된 snapshot이 아니라 정렬된 live view다

`ConcurrentSkipListSet`은 다음이 본질이다.

- 정렬된 순서 유지
- concurrent add/remove/search
- weakly consistent iteration
- range view(`headSet`, `tailSet`, `subSet`)

여기서 자주 놓치는 점이 두 가지다.

첫째, iterator와 range view는 snapshot이 아니다.  
순회 중 concurrent update가 일어나도 `ConcurrentModificationException` 없이 진행되지만,  
보는 내용이 "어느 한 시점의 완전한 사진"이라고 보장되지는 않는다.

둘째, set의 중복 판정은 `equals`보다 ordering에 더 가깝다.  
natural ordering이나 comparator가 `0`을 반환하면 같은 원소로 취급된다.

예를 들어 deadline만 비교하는 comparator를 쓰면:

- 같은 deadline을 가진 서로 다른 작업이 하나로 합쳐질 수 있다.
- membership bug처럼 보이지만 실제 원인은 comparator contract다.

즉 `ConcurrentSkipListSet`은 "thread-safe한 TreeSet"이 아니라  
**ordering이 곧 identity 일부가 되는 concurrent set**으로 이해해야 한다.

### 5. queue depth와 membership count는 제어 신호가 아니라 결과 지표에 가깝다

실무에서 흔한 오해는 숫자를 control plane처럼 쓰는 것이다.

- `BlockingQueue#size()`를 보고 "100 미만이니 안전"하다고 판단
- `LinkedTransferQueue#getWaitingConsumerCount()`를 보고 handoff 가능 여부를 확정
- `ConcurrentSkipListSet#size()`를 exact online user 수처럼 사용

이 값들은 관측과 대시보드에는 유용하지만, concurrent mutation이 계속되는 동안  
정확한 admission, exact billing, one-shot decision gate로 쓰기에는 약하다.

제어는 보통 다음으로 표현하는 편이 낫다.

- bounded capacity
- timed offer / timed transfer
- explicit rejection
- 별도 동기화된 snapshot 또는 counter

## 실전 시나리오

### 시나리오 1: API worker queue가 느려질 때 producer를 같이 늦추고 싶다

`ConcurrentLinkedQueue`나 사실상 무한 `LinkedBlockingQueue`는 backlog를 숨기기 쉽다.  
이 경우는 bounded `BlockingQueue`와 `offer(timeout)` 또는 rejection policy가 더 직접적이다.

### 시나리오 2: "받는 스레드가 실제로 가져갔는지"가 중요하다

단순히 큐에 넣었다는 사실로 충분하지 않다면 `LinkedTransferQueue#transfer`가 후보가 된다.  
반대로 burst buffering도 허용된다면 `put`/`offer`와 `transfer`를 어떤 경로에 쓸지 분리해야 한다.

### 시나리오 3: deadline 순 active job 집합을 유지하고 싶다

정렬과 range lookup이 필요하면 `ConcurrentSkipListSet`이 맞다.  
다만 comparator가 deadline만 비교하면 같은 시각의 다른 job이 dedupe될 수 있다.

### 시나리오 4: 모니터링 숫자를 제어 조건으로 오용한다

`queue.size() < 100`이면 안전하다고 판단하거나,  
`getWaitingConsumerCount() > 0`이면 무조건 transfer가 된다고 가정하면 race가 생긴다.

## 코드로 보기

### 1. bounded `BlockingQueue`로 soft backpressure 표현

```java
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;

BlockingQueue<Job> queue = new ArrayBlockingQueue<>(1000, true);

boolean accepted = queue.offer(job, 50, TimeUnit.MILLISECONDS);
if (!accepted) {
    throw new TooBusyException("worker queue saturated");
}
```

여기서 핵심은 queue 존재가 아니라:

- capacity가 bounded인지
- timeout 후 어떤 실패를 낼지
- interrupt를 어떻게 처리할지

까지가 정책이라는 점이다.

### 2. `TransferQueue`에서 `put`과 `transfer`는 의미가 다르다

```java
import java.util.concurrent.LinkedTransferQueue;
import java.util.concurrent.TransferQueue;

TransferQueue<Event> queue = new LinkedTransferQueue<>();

queue.put(event);      // enqueue가 가능하다
queue.transfer(event); // consumer가 실제로 받을 때까지 대기한다
```

같은 자료구조여도 호출 메서드가 handoff 계약을 바꾼다.

### 3. `ConcurrentSkipListSet`에서는 comparator가 dedupe 규칙이다

```java
import java.time.Instant;
import java.util.Comparator;
import java.util.concurrent.ConcurrentSkipListSet;

record ScheduledJob(long id, Instant deadline) {}

ConcurrentSkipListSet<ScheduledJob> jobs =
    new ConcurrentSkipListSet<>(
        Comparator.comparing(ScheduledJob::deadline)
                  .thenComparingLong(ScheduledJob::id)
    );
```

`thenComparingLong(ScheduledJob::id)`를 빼면  
같은 deadline의 다른 job이 한 원소처럼 취급될 수 있다.

## 트레이드오프

| 선택 | 장점 | 비용 | 언제 맞는가 |
|---|---|---|---|
| bounded `BlockingQueue` | 메모리 상한과 producer throttling을 표현하기 쉽다 | block, timeout, rejection을 운영적으로 설계해야 한다 | worker queue, bounded buffer, overload control |
| `LinkedTransferQueue` + `transfer` | 소비자 수신과 producer 진행을 직접 묶을 수 있다 | 잘못 쓰면 일반 enqueue와 섞여 semantics가 흐려진다 | direct handoff, rendezvous성 전달 |
| `ConcurrentSkipListSet` | 정렬된 membership와 range view가 가능하다 | comparator contract와 weakly consistent iteration을 이해해야 한다 | ordered active set, deadline/index view |

핵심은 concurrent collection 선택을 thread safety가 아니라  
**buffering, handoff, ordering, observability contract 선택**으로 보는 것이다.

## 꼬리질문

> Q: `LinkedTransferQueue`를 쓰면 왜 자동으로 backpressure가 생기지 않나요?
> 핵심: 자료구조가 아니라 어떤 연산을 쓰는지가 중요하다. `put`은 enqueue일 수 있고, `transfer`만이 소비자 수신과 producer를 직접 묶는다.

> Q: `put`과 `offer(timeout)` 중 무엇을 고르나요?
> 핵심: producer를 무기한 기다리게 해도 되는지에 달렸다. shutdown/cancellation이 중요하면 bounded wait가 더 운영 친화적일 때가 많다.

> Q: `ConcurrentSkipListSet`은 왜 원소를 "잃어버린 것처럼" 보일 수 있나요?
> 핵심: comparator가 `0`을 반환하면 같은 원소로 취급되기 때문이다. ordering contract가 dedupe 규칙이다.

> Q: `size()`나 `getWaitingConsumerCount()`를 제어 조건으로 쓰면 왜 위험한가요?
> 핵심: concurrent 상태는 읽는 즉시 바뀔 수 있어서, 관측 지표를 correctness gate로 쓰면 race가 생긴다.

## 한 줄 정리

`BlockingQueue`, `TransferQueue`, `ConcurrentSkipListSet`은 모두 concurrent container가 아니라, 각각 buffering/backpressure, direct handoff, ordered live membership를 표현하는 서로 다른 계약이다.
