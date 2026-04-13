# Ring Buffer

> 한 줄 요약: Ring Buffer는 고정 크기 배열을 원형으로 써서, 큐 연산을 빠르고 예측 가능하게 만드는 자료구조다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Queue (큐)](./basic.md#queue-큐)
> - [Monotonic Queue and Stack](./monotonic-queue-and-stack.md)
> - [Amortized Analysis Pitfalls](../algorithm/amortized-analysis-pitfalls.md)

> retrieval-anchor-keywords: ring buffer, circular buffer, head tail, wraparound, producer consumer, bounded queue, log buffer, event queue, overwrite policy, backpressure

## 핵심 개념

Ring Buffer는 배열의 끝에 도달하면 다시 처음으로 돌아가서 쓰는 **원형 큐**다.

핵심 아이디어는 간단하다.

- 배열 크기는 고정한다.
- `head`는 읽을 위치, `tail`은 쓸 위치를 가리킨다.
- 인덱스는 `% capacity` 또는 조건 분기로 감싼다.

이 구조는 다음 상황에서 특히 좋다.

- 메모리 사용량을 예측해야 할 때
- 할당/해제를 줄이고 싶을 때
- producer/consumer 흐름이 많을 때

## 깊이 들어가기

### 1. head / tail을 어떻게 해석할까

Ring Buffer는 보통 `head`와 `tail`만으로 상태를 표현한다.

대표적인 두 방식이 있다.

- 하나를 비워 두는 방식: empty와 full을 쉽게 구분
- `size`를 따로 두는 방식: 공간 활용이 더 좋음

실무에서는 "가득 찼는지" 판별이 중요하므로, 정책을 명확히 정해야 한다.

### 2. overwrite vs reject

버퍼가 꽉 찼을 때의 정책도 중요하다.

- reject: 새 데이터를 버린다
- overwrite: 가장 오래된 데이터를 덮어쓴다

로그나 센서 스트림처럼 최신값이 더 중요하면 overwrite가 맞고,  
결제 이벤트처럼 유실이 치명적이면 reject나 backpressure가 맞다.

### 3. 왜 예측 가능성이 중요한가

Ring Buffer는 보통 동적 resize가 없다.

- 평균적으로 빠른 것이 아니라
- 매 연산이 거의 일정한 비용이라는 점이 강점이다

그래서 tail latency가 중요한 경로에서 좋다.

### 4. backend에서의 활용 감각

Ring Buffer는 큐 이상의 의미가 있다.

- 로그 수집 버퍼
- Kafka-like producer/consumer 내부 큐
- 이벤트 루프 작업 목록
- 고정 크기 샘플링 윈도우

## 실전 시나리오

### 시나리오 1: 로그 버퍼

짧은 시간 동안 로그를 모아서 배치 전송할 때, ring buffer는 메모리 할당을 줄이고 throughput을 안정화한다.

### 시나리오 2: 실시간 이벤트 큐

웹소켓 서버나 게임 서버처럼 이벤트가 많이 오가는 곳에서는, 고정 크기 버퍼가 GC 압박을 줄여준다.

### 시나리오 3: 최신 N개만 유지

최근 요청, 최근 상태 변화, 최근 알림만 보관하고 싶다면 overwrite 정책의 ring buffer가 잘 맞는다.

### 시나리오 4: backpressure 필요

버퍼가 꽉 차면 생산 속도를 늦추거나 거절해야 할 수 있다.  
이때 ring buffer는 "얼마나 쌓였는지"를 직접 보여줘서 제어 로직을 붙이기 쉽다.

## 코드로 보기

```java
import java.util.NoSuchElementException;

public class RingBuffer<T> {
    private final Object[] data;
    private int head = 0;
    private int tail = 0;
    private int size = 0;

    public RingBuffer(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        this.data = new Object[capacity];
    }

    public boolean offer(T value) {
        if (size == data.length) {
            return false;
        }
        data[tail] = value;
        tail = (tail + 1) % data.length;
        size++;
        return true;
    }

    public T poll() {
        if (size == 0) {
            return null;
        }
        @SuppressWarnings("unchecked")
        T value = (T) data[head];
        data[head] = null;
        head = (head + 1) % data.length;
        size--;
        return value;
    }

    public T peek() {
        if (size == 0) throw new NoSuchElementException();
        @SuppressWarnings("unchecked")
        T value = (T) data[head];
        return value;
    }

    public int size() {
        return size;
    }

    public boolean isEmpty() {
        return size == 0;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Ring Buffer | 고정 비용과 예측 가능성이 좋다 | 크기를 늘리기 어렵다 | 지연시간과 메모리 예측성이 중요할 때 |
| 동적 Queue | 유연하다 | resize와 GC 비용이 생긴다 | 입력량이 자주 바뀔 때 |
| Deque | 앞뒤 삽입이 편하다 | 큐 의미가 흐려질 수 있다 | 양방향 처리도 필요할 때 |

Ring Buffer는 "무조건 큐"가 아니라, **bounded queue**라는 점이 핵심이다.

## 꼬리질문

> Q: empty와 full을 어떻게 구분하나?
> 의도: 원형 인덱스 판별 이해 확인
> 핵심: size를 두거나, 한 칸을 비워 두는 방식으로 구분한다.

> Q: 왜 tail latency에 유리한가?
> 의도: 상수 비용과 할당 회피 감각 확인
> 핵심: resize가 없고, 연산이 단순해서 비용 예측이 쉽다.

> Q: overwrite가 항상 좋은가?
> 의도: 데이터 유실 정책 이해 확인
> 핵심: 아니다. 최신성보다 무결성이 중요하면 overwrite는 위험하다.

## 한 줄 정리

Ring Buffer는 고정 크기 원형 배열로 큐를 구현해, 예측 가능한 성능과 낮은 할당 비용을 얻는 자료구조다.
