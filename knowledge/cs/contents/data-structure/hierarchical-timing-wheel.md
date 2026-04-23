# Hierarchical Timing Wheel

> 한 줄 요약: Hierarchical Timing Wheel은 미래 시점을 원형 버킷에 나눠 담아, 대량 timeout과 delayed task를 heap보다 더 싸게 관리하려는 스케줄링용 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ring Buffer](./ring-buffer.md)
> - [Heap Variants](./heap-variants.md)
> - [Calendar Queue](./calendar-queue.md)
> - [Timing Wheel Variants and Selection](./timing-wheel-variants-and-selection.md)
> - [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
> - [Distributed Scheduler Design](../system-design/distributed-scheduler-design.md)

> retrieval-anchor-keywords: hierarchical timing wheel, timing wheel, timer wheel, hashed wheel timer, delayed task scheduler, timeout management, deadline bucket, bucket rotation, delay queue alternative, retry scheduler, timer bucket scheduler

## 핵심 개념

timeout이나 delayed job이 매우 많아지면 "가장 빠른 deadline"만 잘 꺼내는 것으로는 부족하다.  
문제는 개별 timer 수가 아니라, **등록/취소/만료 확인이 너무 자주 일어난다**는 점이다.

Timing Wheel은 시간을 균등한 tick으로 잘라 원형 배열에 담는다.

- wheel의 각 slot은 특정 시간 구간을 뜻한다.
- 현재 시각이 한 tick 전진할 때 현재 slot만 확인한다.
- 같은 slot에 들어온 timer들은 연결 리스트나 bucket 안에서 함께 관리한다.

즉 "deadline 전체를 정렬"하기보다, **비슷한 시각의 일들을 같은 bucket으로 묶는 발상**이다.

## 깊이 들어가기

### 1. 왜 binary heap만으로는 버거워지나

priority queue 기반 timer는 직관적이지만, timeout 수가 커질수록 다음 비용이 누적된다.

- `add timer`: `O(log n)`
- `cancel timer`: 임의 원소 제거와 stale entry 정리 비용
- `poll expired`: 만료 직전 원소를 계속 heap top에서 확인

수십만~수백만 idle connection timeout, retry schedule, session expiry를 다루면  
"정렬은 정확하지만 너무 자주 건드려야 하는" 구조가 된다.

Timing Wheel은 tick 단위의 근사 정렬을 받아들이고, 대신 등록과 스캔 비용을 크게 줄인다.

### 2. 단일 wheel은 `slot + round`로 생각하면 쉽다

wheel 크기가 `N`, 현재 tick이 `t`일 때 delay가 `d`인 timer는 보통 이렇게 배치한다.

- `slot = (t + d) % N`
- `round = d / N`

현재 slot을 만났다고 바로 실행하는 것이 아니라, `round == 0`일 때만 만료시킨다.  
아직 먼 미래면 `round`를 하나 줄이고 다음 회전을 기다린다.

이 방식의 장점:

- 삽입이 거의 `O(1)`이다
- 매 tick에서 보는 bucket 수가 고정된다

한계도 분명하다.

- 최대 delay가 매우 크면 `round`가 커진다
- tick granularity보다 더 정밀한 deadline은 표현이 어렵다

### 3. 그래서 계층형 wheel이 나온다

Hierarchical Timing Wheel은 초/분/시간처럼 여러 wheel을 겹쳐 둔다.

- 하위 wheel: 가까운 미래를 세밀하게 관리
- 상위 wheel: 먼 미래를 거칠게 저장
- 하위 wheel이 한 바퀴 돌 때 상위 wheel bucket을 아래로 cascade

이 구조 덕분에 "아주 먼 미래"도 huge round 없이 저장할 수 있다.

대표 감각은 이렇다.

- 1ms wheel 256칸
- 256ms가 넘는 timer는 2단계 wheel로 보냄
- 2단계 bucket이 도래하면 1단계로 다시 내려보냄

즉 등록 시점에는 거칠게 분류하고, 실행 시점이 가까워질수록 더 정밀한 wheel로 이동한다.

### 4. 취소와 lazy deletion이 실무 포인트다

실무 timer는 등록보다 취소가 더 많을 수 있다.

- 요청이 정상 응답되면 timeout timer는 취소된다
- retry가 성공하면 뒤의 재시도 timer는 무효화된다
- 세션이 닫히면 idle timer는 제거된다

bucket 중간에서 연결 리스트 노드를 정확히 제거하려면 handle 관리가 필요하다.  
그래서 흔한 구현은 두 가지다.

- intrusive node를 들고 다니며 즉시 제거
- `cancelled=true` 표시만 하고 만료 tick에 lazy skip

후자는 단순하지만 tombstone이 쌓이면 bucket scan이 무거워진다.  
즉시 제거는 빠르지만 동시성과 handle 수명이 복잡해진다.

### 5. 정확도보다 운영 의미가 중요하다

Timing Wheel은 보통 "정확히 그 시각"보다 "그 근처 tick 안에서 실행"을 허용한다.

그래서 다음 판단이 먼저다.

- timeout 정확도가 몇 ms까지 중요한가
- 대량 timer 등록/취소가 핵심 병목인가
- JVM stop-the-world, event loop stall, clock jump에 어떻게 대응할 것인가

특히 timeout 관리에는 **wall clock이 아니라 monotonic clock**을 써야 한다.  
시계 보정 때문에 시간이 뒤로 가면 bucket 계산이 깨질 수 있다.

## 실전 시나리오

### 시나리오 1: 네트워크 서버의 idle timeout

웹소켓, TCP proxy, RPC 서버는 연결마다 idle timeout을 둔다.  
수백만 connection을 heap으로 관리하면 timer churn이 커질 수 있는데, hashed wheel은 이 패턴에 잘 맞는다.

### 시나리오 2: 지연 재시도 스케줄러

`5초 후`, `30초 후`, `5분 후` 같은 retry를 대량 등록할 때는 deadline 정렬 정확도보다  
대량 삽입과 만료 배치 비용이 더 중요하다.

### 시나리오 3: lease / session expiry

분산 lock lease, session expiry, cache refresh는 보통 tick 단위 근사 만료로 충분하다.  
이 경우 timing wheel은 고정 비용으로 대량 만료를 처리하기 좋다.

### 시나리오 4: 부적합한 경우

정확한 earliest-deadline-first 스케줄링, 매우 작은 timer 수, sub-millisecond 정밀도 요구에는  
heap이나 OS timer가 더 맞을 수 있다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

public class HashedWheelTimer {
    private final List<List<TimerTask>> wheel;
    private final int wheelSize;
    private long currentTick = 0L;

    public HashedWheelTimer(int wheelSize) {
        this.wheelSize = wheelSize;
        this.wheel = new ArrayList<>(wheelSize);
        for (int i = 0; i < wheelSize; i++) {
            wheel.add(new LinkedList<>());
        }
    }

    public TimerHandle schedule(long delayTicks, Runnable task) {
        if (delayTicks < 0) {
            throw new IllegalArgumentException("delayTicks must be >= 0");
        }

        long deadlineTick = currentTick + delayTicks;
        int slot = (int) (deadlineTick % wheelSize);
        long remainingRounds = delayTicks / wheelSize;

        TimerTask timerTask = new TimerTask(task, remainingRounds);
        wheel.get(slot).add(timerTask);
        return () -> timerTask.cancelled = true;
    }

    public void advanceOneTick() {
        int slot = (int) (currentTick % wheelSize);
        List<TimerTask> bucket = wheel.get(slot);
        Iterator<TimerTask> iterator = bucket.iterator();

        while (iterator.hasNext()) {
            TimerTask timerTask = iterator.next();
            if (timerTask.cancelled) {
                iterator.remove();
                continue;
            }

            if (timerTask.remainingRounds > 0) {
                timerTask.remainingRounds--;
                continue;
            }

            iterator.remove();
            timerTask.task.run();
        }

        currentTick++;
    }

    public interface TimerHandle {
        void cancel();
    }

    private static final class TimerTask {
        private final Runnable task;
        private long remainingRounds;
        private boolean cancelled;

        private TimerTask(Runnable task, long remainingRounds) {
            this.task = task;
            this.remainingRounds = remainingRounds;
        }
    }
}
```

이 코드는 single wheel만 보여준다.  
실전의 hierarchical wheel은 상위 bucket에서 하위 wheel로 **cascade**하는 단계가 추가된다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Hierarchical Timing Wheel | 대량 timer 등록/만료 비용이 낮고 bucket 스캔이 예측 가능하다 | tick 단위 근사와 cascade 복잡도가 있다 | idle timeout, retry, session expiry가 많을 때 |
| Binary Heap / Priority Queue | 가장 이른 deadline을 정확히 꺼내기 쉽다 | 삽입/취소 churn이 커지면 비용이 누적된다 | timer 수가 적거나 정확한 ordering이 중요할 때 |
| Delay Queue | 구현이 단순하고 블로킹 모델에 잘 맞는다 | 내부적으로 heap 계열 비용을 피하기 어렵다 | JVM 단일 프로세스 scheduler를 빠르게 만들 때 |
| 주기적 전체 스캔 | 이해가 쉽다 | key 수가 커지면 바로 무너진다 | 규모가 아주 작을 때만 |

핵심은 "시간을 정렬할 것인가"보다 "시간을 bucket으로 묶어도 되는가"다.

## 꼬리질문

> Q: timing wheel이 heap보다 유리한 이유는 무엇인가?
> 의도: 정렬 정확도와 운영 비용의 trade-off 이해 확인
> 핵심: deadline 전체를 매번 정렬하지 않고, 비슷한 시각의 timer를 bucket으로 묶기 때문이다.

> Q: 왜 단일 wheel 대신 계층형 wheel이 필요한가?
> 의도: 먼 미래 timer 처리 감각 확인
> 핵심: 하나의 wheel만 쓰면 큰 delay를 `round`로 오래 들고 있어야 해서 비효율적이기 때문이다.

> Q: cancellation을 lazy하게 처리할 때 주의점은?
> 의도: tombstone과 bucket scan 비용 이해 확인
> 핵심: 취소된 timer가 많이 쌓이면 만료 tick의 스캔 비용이 급증할 수 있다.

## 한 줄 정리

Hierarchical Timing Wheel은 대량 timeout과 delayed task를 tick bucket으로 묶어, deadline 정밀도 일부를 포기하는 대신 훨씬 싼 스케줄링 비용을 얻는 자료구조다.
