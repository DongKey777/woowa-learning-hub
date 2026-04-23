# Monotonic Clock, Wall Clock, Timeout and Deadline

> 한 줄 요약: 타임아웃은 "얼마나 기다릴까"이고, 데드라인은 "언제까지 끝나야 하나"이며, 실전 시스템은 `CLOCK_MONOTONIC`으로 측정하고 wall clock은 표시와 외부 연동에만 조심해서 써야 한다.

**난이도: 🔴 Advanced**

## 핵심 개념

시간을 다룰 때 가장 먼저 나눠야 하는 것은 `시간의 표시`와 `시간의 측정`이다.

- `wall clock`: 사람이 읽는 현재 시각이다. `2026-04-09 14:30:00` 같은 값이다.
- `monotonic clock`: 시스템 시작 이후 단조 증가하는 시간이다. 앞으로만 가고, 중간에 뒤로 가지 않는다.

실무에서 중요한 이유는 명확하다.

- 타임아웃은 "몇 초 기다릴지"를 재는 문제라서 시간 역행이 있으면 안 된다.
- 데드라인은 "이 시각 전까지 끝내야 한다"는 약속이라서 NTP나 수동 시계 변경에 흔들리면 안 된다.
- 예약 작업, 재시도 스케줄러, 서킷 브레이커, 배치 잡은 wall clock을 잘못 쓰면 갑자기 빨라지거나 느려지는 버그가 생긴다.

관련 문서:

- [네트워크 타임아웃 타입: connect, read, write](../network/timeout-types-connect-read-write.md)
- [타임아웃, 재시도, 백오프 실전](../network/timeout-retry-backoff-practical.md)
- [Spring Scheduler와 Async 경계](../spring/spring-scheduler-async-boundaries.md)
- [Resilience4j retry, circuit breaker, bulkhead](../spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)
- [Spring Batch chunk, retry, skip](../spring/spring-batch-chunk-retry-skip.md)
- [idempotency, retry, consistency boundaries](../software-engineering/idempotency-retry-consistency-boundaries.md)
- [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
- [Scheduler Fairness, Page Cache, File System Basics](./scheduler-fairness-page-cache.md)

## 깊이 들어가기

### 1. wall clock과 monotonic clock은 쓰임새가 다르다

`wall clock`은 "지금 몇 시인가"를 알려준다.
`monotonic clock`은 "얼마나 시간이 흘렀는가"를 알려준다.

여기서 함정은 wall clock이 바뀔 수 있다는 점이다.

- NTP가 시간을 보정하면 뒤로 점프할 수 있다.
- 운영자가 수동으로 시간을 바꾸면 예약 시각이 흔들린다.
- VM이나 컨테이너 환경에서는 호스트 시간 보정의 영향을 받을 수 있다.

그래서 소요 시간 측정, timeout 계산, retry backoff의 경과 시간 판정은 monotonic clock으로 해야 안전하다.

### 2. timeout과 deadline은 다르다

타임아웃은 "기다리는 최대 시간"이다.
데드라인은 "절대 시각"이다.

예를 들어:

- timeout 2초: 지금부터 2초 기다린다.
- deadline 14:30:05: 지금 시각이 무엇이든 14:30:05 전에 끝내야 한다.

이 둘은 비슷해 보이지만, 분산 시스템에서는 역할이 다르다.

- timeout은 하위 호출 하나의 실패 감지에 좋다.
- deadline은 여러 단계에 걸친 작업의 총 예산을 관리하는 데 좋다.

### 3. NTP clock jump가 버그를 만든다

wall clock으로 timeout을 계산하면 다음 문제가 생긴다.

- 시간이 뒤로 가면 timeout이 영원히 안 끝난 것처럼 보일 수 있다.
- 시간이 앞으로 가면 아직 안 끝난 작업이 갑자기 만료될 수 있다.
- 재시도 스케줄러가 갑자기 몰리거나 비는 현상이 생긴다.

예를 들어 `start = System.currentTimeMillis()`로 저장하고 `now - start >= timeout`을 계산하면, 시계가 뒤로 갔을 때 경과 시간이 음수처럼 보일 수 있다.

### 4. deadline propagation이 없으면 분산 호출이 느려진다

한 요청이 API A -> B -> C로 이어질 때, 각 계층이 자기 timeout만 따로 잡으면 전체 요청 예산이 깨진다.

- A가 1초 기다리고
- B가 1초 기다리고
- C가 1초 기다리면

겉보기에는 각각 짧아도 전체는 3초 이상 늘어질 수 있다.

그래서 실제로는 request deadline을 받아서 남은 시간을 계산해야 한다.

- 남은 시간 = deadline - now
- 각 하위 호출 timeout = `min(남은 시간, 안전 마진)`

이렇게 해야 상위 SLA를 넘기지 않는다.

### 5. retry scheduler는 wall clock보다 monotonic이 안전하다

retry scheduler는 다음 실행 시점을 잡는다.

- `fixed delay`: 실패 후 일정 시간 기다린 뒤 다시 시도
- `fixed rate`: 정해진 간격으로 반복
- `exponential backoff`: 실패할수록 대기 시간을 늘림

이때 wall clock 기반으로 다음 시각을 계산하면, NTP가 시간을 바꾸는 순간 예약이 몰리거나 밀린다.
monotonic clock 기반이면 경과 시간만 보므로 이런 문제를 줄일 수 있다.

## 실전 시나리오

### 시나리오 1: 배포 직후 retry storm

외부 API가 잠깐 느려졌다가 회복되었는데, 여러 워커가 wall clock 기준으로 같은 시점에 다시 재시도하면 트래픽이 한꺼번에 몰린다.

증상:

- p95 latency가 튄다
- 실패 후 복구했는데도 요청이 계속 쏠린다
- 큐가 비었다가 다시 폭주한다

대응:

- exponential backoff + jitter를 넣는다
- monotonic 기준으로 backoff를 계산한다
- deadline이 지난 요청은 더 이상 재시도하지 않는다

### 시나리오 2: 배치 잡이 하루에 한 번씩 이상하게 빨리 돈다

cron이나 스케줄러가 wall clock을 기준으로 동작하면, NTP 보정이나 DST 변경 시 실행 간격이 어긋난다.

대응:

- 실제 실행 간격은 monotonic으로 추적한다
- 예약 시각은 wall clock으로 표현하되, 실행 중 경과 판정은 monotonic으로 한다
- 중요한 배치는 `last_run`, `next_run`, `drift`를 모두 기록한다

### 시나리오 3: 마이크로서비스 체인이 전체 timeout을 넘긴다

상위 서비스가 2초 SLA를 받았는데 하위 서비스가 각자 1초 timeout을 쓰면, 체인 전체는 2초를 넘기기 쉽다.

대응:

- deadline을 헤더로 전달한다
- 하위 서비스는 남은 시간을 계산한다
- 타임아웃 실패와 비즈니스 실패를 구분한다

### 시나리오 4: 테스트는 통과하는데 운영에서만 timeout이 난다

테스트는 빠른 wall clock 가정으로 작성되고, 운영은 NTP 보정이나 컨테이너 스케줄링 영향으로 시간 감각이 다를 수 있다.

대응:

- 시간 의존 코드는 `Clock` 주입으로 테스트한다
- 경과 시간 계산은 monotonic 기준으로 분리한다
- 실제 운영 로그에는 wall clock과 monotonic 기반 경과 시간을 같이 남긴다

## 코드로 보기

### Java에서 wall clock과 monotonic clock 비교

```java
import java.time.Duration;
import java.time.Instant;

public class TimeoutExample {
    public static void main(String[] args) throws InterruptedException {
        long startedAtMillis = System.currentTimeMillis();
        long startedAtNanos = System.nanoTime();

        Thread.sleep(150);

        long elapsedMillisByWallClock = System.currentTimeMillis() - startedAtMillis;
        long elapsedMillisByMonotonicClock = Duration.ofNanos(System.nanoTime() - startedAtNanos).toMillis();

        System.out.println("wall clock elapsed = " + elapsedMillisByWallClock + "ms");
        System.out.println("monotonic elapsed  = " + elapsedMillisByMonotonicClock + "ms");
    }
}
```

`System.currentTimeMillis()`는 시계 변경의 영향을 받지만, `System.nanoTime()`은 경과 시간 측정에 더 적합하다.

### deadline propagation 예시

```java
import java.time.Duration;
import java.time.Instant;

public record Deadline(Instant expiresAt) {
    public Duration remaining(Instant now) {
        Duration remaining = Duration.between(now, expiresAt);
        return remaining.isNegative() ? Duration.ZERO : remaining;
    }
}
```

```java
Deadline deadline = new Deadline(Instant.now().plusMillis(800));
Duration remaining = deadline.remaining(Instant.now());

if (remaining.isZero()) {
    throw new IllegalStateException("deadline exceeded");
}

externalClient.call(remaining.toMillis());
```

### retry backoff를 monotonic 관점으로 이해하기

```java
long start = System.nanoTime();
long delayMillis = 100;

while (true) {
    try {
        doCall();
        break;
    } catch (Exception e) {
        long elapsedMillis = Duration.ofNanos(System.nanoTime() - start).toMillis();
        if (elapsedMillis > 1000) {
            throw e;
        }

        Thread.sleep(delayMillis);
        delayMillis = Math.min(delayMillis * 2, 1000);
    }
}
```

### Linux에서 시간 보정과 현재 시각 확인

```bash
date
timedatectl status
chronyc tracking
chronyc sources -v
```

운영 중에는 "시각이 맞는가"와 "경과 시간을 제대로 재는가"를 분리해서 봐야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| wall clock | 사람이 이해하기 쉽다 | NTP, DST, 수동 변경에 흔들린다 | 표시, 로그 타임스탬프, 외부 약속 |
| monotonic clock | 시간 역행이 없다 | 사람이 읽는 절대 시각이 아니다 | timeout, deadline 계산, 경과 측정 |
| timeout 중심 설계 | 구현이 쉽다 | 체인 전체 예산을 잃기 쉽다 | 단일 호출, 짧은 작업 |
| deadline 중심 설계 | 분산 호출 전체 예산을 지킨다 | 구현이 조금 더 복잡하다 | 여러 서비스가 연결된 요청 |
| fixed delay retry | 단순하다 | 실패가 몰리면 storm이 생길 수 있다 | 저위험 반복 작업 |
| exponential backoff + jitter | 폭주를 줄인다 | 지연이 길어질 수 있다 | 외부 API, 불안정한 하위 시스템 |

## 꼬리질문

> Q: `System.currentTimeMillis()`와 `System.nanoTime()`은 언제 각각 써야 하나요?
> 의도: 시각과 경과 시간의 차이를 아는지 확인한다.
> 핵심: currentTimeMillis는 wall clock, nanoTime은 elapsed time이다.

> Q: timeout과 deadline은 왜 구분해야 하나요?
> 의도: 분산 호출에서 총 예산 관리 감각을 보는 질문이다.
> 핵심: timeout은 개별 대기, deadline은 전체 완료 시각이다.

> Q: NTP가 시간을 바꾸면 어떤 버그가 생기나요?
> 의도: 운영 시간 보정이 시스템에 미치는 영향을 아는지 확인한다.
> 핵심: wall clock 기반 timeout, retry scheduler, 배치 실행 시각이 흔들린다.

> Q: deadline propagation을 안 하면 무엇이 제일 먼저 망가지나요?
> 의도: 마이크로서비스 체인의 예산 관리를 이해하는지 확인한다.
> 핵심: 상위 SLA 초과, 하위 재시도 중첩, tail latency 증가다.

> Q: retry는 왜 monotonic clock과 같이 설계해야 하나요?
> 의도: 재시도 스케줄의 안정성을 보는 질문이다.
> 핵심: 시계 점프가 있어도 경과 시간 기준이면 backoff가 흔들리지 않는다.

## 한 줄 정리

시간을 표시할 때는 wall clock을 쓰고, 기다림과 경과 시간을 계산할 때는 monotonic clock을 써야 한다. timeout은 개별 대기 예산이고 deadline은 전체 완료 시각이며, 재시도와 스케줄러는 deadline propagation과 backoff를 함께 설계해야 안전하다.
