# Bounded MPMC Queue

> 한 줄 요약: Bounded MPMC Queue는 고정 크기 ring 위에서 per-slot sequence를 세대 표식처럼 사용해, 다중 producer와 다중 consumer의 경쟁을 조율하면서 메모리 상한과 backpressure를 구조적으로 강제하는 concurrent handoff queue다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ring Buffer](./ring-buffer.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
> - [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md)
> - [Michael-Scott Lock-Free Queue](./michael-scott-lock-free-queue.md)
> - [Sequencer-Based Ring Buffer Coordination](./sequencer-based-ring-buffer-coordination.md)
> - [ABA Problem and Tagged Pointers](./aba-problem-and-tagged-pointers.md)
> - [Hazard Pointers vs Epoch-Based Reclamation](./hazard-pointers-vs-epoch-based-reclamation.md)

> retrieval-anchor-keywords: bounded mpmc queue, vyukov queue, mpmc ring buffer, multiple producer multiple consumer ring queue, bounded concurrent queue, sequence based queue, per-slot sequence, slot generation counter, claim publish queue, backpressure queue, lock-free mpmc ring, fixed capacity queue, disruptor style queue, concurrent handoff ring, ring buffer backpressure, bounded worker queue

## 핵심 개념

범용 MPMC queue가 필요해도 linked-list 방식만 있는 것은 아니다.  
메모리 상한이 중요하면 bounded ring 기반 MPMC가 더 적합할 수 있다.

핵심은 이렇다.

- 고정 크기 slot 배열
- producer와 consumer가 slot sequence를 기준으로 경쟁
- enqueue ticket과 dequeue ticket은 slot ownership만 예약
- full이면 명시적 backpressure

즉 unbounded lock-free queue보다 범용성은 줄지만,  
**메모리 예측성과 고정 비용**을 얻는다.

## 깊이 들어가기

### 1. 왜 bounded가 중요한가

event burst가 와도 무한히 node를 할당하고 싶지 않은 경로가 있다.

- telemetry ingest
- internal executor handoff
- network event queue

이런 곳에서 bounded queue는 자료구조이면서 정책이다.

- 가득 차면 drop
- block
- spin
- upstream throttle

즉 queue 선택이 곧 backpressure 모델 선택이 된다.

### 2. slot lifecycle이 실제 알고리즘이다

bounded MPMC ring은 흔히 slot마다 sequence를 둔다.

- 초기 상태: `cell.sequence == slotIndex`
- producer는 `enqueuePos`를 CAS로 가져간 뒤 `cell.sequence == pos`인지 확인
- payload를 쓴 다음 `cell.sequence = pos + 1`로 publish
- consumer는 `cell.sequence == pos + 1`이면 읽을 수 있다고 판단
- 읽고 비운 뒤 `cell.sequence = pos + capacity`로 recycle

이 방식은 head/tail 하나만 보는 단순 ring보다 복잡하지만,  
여러 producer/consumer가 같은 ring을 안전하게 공유하게 해준다.

핵심은 sequence가 단순한 "사용 중 플래그"가 아니라  
**wraparound를 포함한 세대 정보**라는 점이다.  
같은 배열 index를 다시 만나도 sequence가 다르면 이전 회차와 현재 회차를 구분할 수 있다.

### 3. claim과 publish는 다른 단계다

많이 헷갈리는 지점이 여기다.

- `enqueuePos` CAS 성공: "이 slot은 내가 채울 차례"를 예약
- payload store 완료
- `cell.sequence` 갱신: 다른 thread에게 publish

consumer도 비슷하다.

- `dequeuePos` CAS 성공: "이 slot은 내가 비울 차례"를 예약
- payload read
- slot clear
- `cell.sequence`를 다음 세대로 넘겨 producer에게 반환

즉 전역 position은 **ownership 예약**,  
slot-local sequence는 **가시화와 재사용 허가**를 담당한다.

이 분리가 있어야 producer/consumer가 같은 index를 돌아가며 써도  
아직 publish되지 않은 값과 이미 recycle된 값을 헷갈리지 않는다.

### 4. linked MPMC와 어디서 갈리나

Michael-Scott Queue와 비교하면 감각이 다르다.

- MS Queue: unbounded, linked node, allocation 필요
- bounded MPMC: fixed ring, allocation 적음, full 처리 필요

즉 "범용 concurrent handoff"만 보면 linked MPMC가 편하지만,  
"메모리 상한과 tail predictability"까지 보면 bounded ring이 매력적이다.

여기서 메모리 회수 문제의 형태도 달라진다.

- linked MPMC: dequeue마다 node retire/free 문제가 따라온다
- bounded ring: core slot 배열은 재사용되므로 hot path reclamation이 줄어든다

다만 이게 reclamation이 완전히 사라진다는 뜻은 아니다.  
payload가 pooled pointer이거나, side freelist를 쓰거나, 동적 wait node를 붙이면  
ABA와 safe reclamation 문제가 다른 층위에서 다시 등장한다.

### 5. ABA는 줄지만 형태가 바뀐다

bounded ring의 큰 장점 중 하나는  
linked pointer 자체를 CAS로 밀고 당기는 구간이 줄어든다는 점이다.

- slot은 미리 할당돼 있다
- per-slot sequence가 세대 표식 역할을 한다
- index wraparound도 generation으로 구분한다

그래서 core queue만 놓고 보면  
linked stack/queue에서 흔한 pointer ABA가 크게 줄어든다.

하지만 다음 상황은 여전히 위험하다.

- slot payload가 외부 freelist node를 가리킬 때
- descriptor pool을 재사용할 때
- parked producer/consumer 대기 노드를 동적으로 붙일 때

즉 bounded MPMC는 ABA를 없앤다기보다  
**문제를 slot generation과 외부 object lifecycle로 재배치**한다.

### 6. backpressure 정책이 자료구조 의미를 바꾼다

full일 때 무엇을 하느냐는 구현 디테일이 아니라 계약이다.

- fail-fast `offer`: caller가 drop/retry를 직접 결정
- bounded spin 후 `yield`/`park`: 짧은 혼잡은 흡수하고 긴 혼잡은 CPU를 아낀다
- timed wait: latency budget을 넘기면 실패로 처리
- upstream credit/throttle: producer 수나 배치 크기를 줄인다

같은 bounded MPMC여도

- 로그/metric 경로면 drop 허용
- worker handoff면 block 또는 park
- RPC ingress면 caller-side throttle

처럼 시스템 semantics가 달라진다.

즉 queue가 가득 찼다는 사실은 단순한 오류가 아니라  
**상류에 전달해야 하는 pressure signal**이다.

### 7. cache line과 false sharing이 성능을 좌우한다

bounded MPMC는 이론보다 layout이 더 중요하다.

- producer index
- consumer index
- slot sequence
- slot payload

이 필드들의 line 배치가 나쁘면 contention이 폭증한다.  
그래서 실전 구현은 padding과 sequence layout을 매우 신경 쓴다.

추가로 자주 나오는 최적화는 다음과 같다.

- power-of-two capacity와 mask 연산
- producer/consumer별 local cached limit
- batch claim으로 CAS 빈도 감소
- queue sharding으로 단일 ring 경합 완화

### 8. backend에서 어디에 맞나

bounded MPMC는 "절대 무한히 쌓이면 안 되는" 파이프라인에 잘 맞는다.

- internal event bus
- bounded worker queue
- batch ingestion pipeline
- low-latency handoff

반면 queue가 가득 찼을 때의 정책을 결정하지 못하면,  
자료구조만 바꿔도 시스템 semantics가 흔들릴 수 있다.

## 실전 시나리오

### 시나리오 1: telemetry ingest with drop policy

관측 이벤트는 유실 가능하지만 메모리 폭주는 안 된다면  
bounded MPMC가 잘 맞는다.  
full 시 fail-fast로 반환하고 상위에서 sample/drop counter를 올리면 된다.

### 시나리오 2: worker handoff with throttle

producer가 여럿이고 consumer도 여럿이지만  
queue 길이 자체를 명시적으로 통제하고 싶을 때 유용하다.  
짧은 혼잡은 spin으로 버티고, 길어지면 park나 upstream throttle로 넘기는 식이다.

### 시나리오 3: allocation-sensitive hot path

linked node allocation이 GC와 tail latency를 흔든다면  
ring 기반 bounded queue가 더 낫다.  
core queue가 preallocated slot을 재사용하므로 allocator pressure를 줄이기 쉽다.

### 시나리오 4: 부적합한 경우

메모리 상한보다 손실 없는 unbounded 수용이 중요하면  
linked MPMC나 durable queue 계열이 더 맞다.

### 시나리오 5: 느린 consumer 하나가 전체를 막는 경우

capacity가 작고 consumer 편차가 크면  
가장 느린 소비자가 queue 전체 backpressure를 만들 수 있다.  
이때는 queue sharding, stage 분리, 또는 sequencer 기반 topology 재설계가 더 맞을 수 있다.

## 코드로 보기

```java
import java.util.concurrent.atomic.AtomicLong;

public class BoundedMpmcQueue<E> {
    private final Cell<E>[] buffer;
    private final int mask;
    private final AtomicLong enqueuePos = new AtomicLong(0);
    private final AtomicLong dequeuePos = new AtomicLong(0);

    @SuppressWarnings("unchecked")
    public BoundedMpmcQueue(int capacityPowerOfTwo) {
        this.buffer = new Cell[capacityPowerOfTwo];
        this.mask = capacityPowerOfTwo - 1;
        for (int i = 0; i < capacityPowerOfTwo; i++) {
            buffer[i] = new Cell<>(i);
        }
    }

    public boolean offer(E value) {
        while (true) {
            long pos = enqueuePos.get();
            Cell<E> cell = buffer[(int) (pos & mask)];
            long seq = cell.sequence;
            long diff = seq - pos;
            if (diff == 0) {
                if (enqueuePos.compareAndSet(pos, pos + 1)) {
                    cell.value = value;
                    cell.sequence = pos + 1;
                    return true;
                }
            } else if (diff < 0) {
                return false;
            }
        }
    }

    public E poll() {
        while (true) {
            long pos = dequeuePos.get();
            Cell<E> cell = buffer[(int) (pos & mask)];
            long seq = cell.sequence;
            long diff = seq - (pos + 1);
            if (diff == 0) {
                if (dequeuePos.compareAndSet(pos, pos + 1)) {
                    E value = cell.value;
                    cell.value = null;
                    cell.sequence = pos + buffer.length;
                    return value;
                }
            } else if (diff < 0) {
                return null;
            }
        }
    }

    private static final class Cell<E> {
        private volatile long sequence;
        private E value;

        private Cell(long sequence) {
            this.sequence = sequence;
        }
    }
}
```

이 코드는 sequence 기반 bounded MPMC 감각만 보여준다.  
실전 구현은 padding, spin/yield 정책, memory ordering, full-handling semantics가 더 중요하다.

특히 `cell.sequence`는 단순 상태값이 아니라  
slot reuse 세대를 나타내는 version tag처럼 읽는 편이 맞다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Bounded MPMC Queue | 메모리 상한과 backpressure semantics가 명확하고 core allocation을 줄이기 쉽다 | full 처리, sequence layout, slow consumer 병목을 설계해야 한다 | bounded internal handoff, low-latency ring |
| Sequencer-Based Ring Coordination | multi-stage 진행 제어와 fan-out barrier를 세밀하게 표현한다 | 단순 handoff에는 과하고 topology가 복잡하다 | staged event pipeline, bounded bus |
| Michael-Scott Queue | 범용 unbounded MPMC handoff가 쉽다 | allocation과 reclamation 비용이 있다 | generic shared queue |
| Lock-Free MPSC Queue | consumer가 하나면 더 단순하고 빠르다 | 다수 consumer엔 안 맞는다 | mailbox, ingress queue |
| SPSC Ring Buffer | 1:1 경로에 가장 싸다 | 역할 제약이 강하다 | dedicated pipeline |

중요한 질문은 "다수 스레드가 공유하는가"뿐 아니라  
"얼마까지 쌓이게 허용할 것인가", "가득 찼을 때 누가 어떤 pressure를 받을 것인가"다.

## 꼬리질문

> Q: bounded MPMC queue가 linked MPMC보다 나은 순간은 언제인가요?
> 의도: bounded memory와 allocation trade-off를 이해하는지 확인
> 핵심: 메모리 상한과 예측 가능한 tail latency가 더 중요할 때다.

> Q: sequence per slot은 왜 필요한가요?
> 의도: 다중 producer/consumer가 같은 ring을 공유하는 안전성 이해 확인
> 핵심: 각 slot이 지금 enqueue 가능한 상태인지 dequeue 가능한 상태인지, 그리고 몇 번째 reuse 세대인지까지 구분해야 하기 때문이다.

> Q: `enqueuePos` CAS만 성공하면 enqueue가 끝난 것 아닌가요?
> 의도: claim과 publish를 구분하는지 확인
> 핵심: 아니다. position은 ownership 예약이고, 다른 thread가 값을 읽을 수 있게 만드는 publication은 slot sequence 갱신으로 별도 완료된다.

> Q: 왜 full 정책이 자료구조 의미까지 바꾸나요?
> 의도: backpressure를 자료구조 외부 문제로만 보지 않는지 확인
> 핵심: drop/block/throttle 선택에 따라 시스템 semantics와 장애 모드가 달라지기 때문이다.

> Q: bounded ring이면 ABA와 reclamation을 완전히 잊어도 되나요?
> 의도: core slot reuse와 외부 object lifecycle을 구분하는지 확인
> 핵심: 아니다. core slot 배열은 안전해지지만 payload 재사용, freelist, side node에서는 ABA와 safe reclamation이 다시 중요해진다.

## 한 줄 정리

Bounded MPMC Queue는 per-slot sequence를 세대 표식으로 써서 다중 producer/consumer를 고정 크기 ring에서 안전하게 재사용시키고, 메모리 상한과 backpressure를 구조 차원에서 강제하는 concurrent handoff queue다.
