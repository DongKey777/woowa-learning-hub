# Sequencer-Based Ring Buffer Coordination

> 한 줄 요약: sequencer 기반 ring buffer는 claim sequence, publish cursor, gating sequence를 분리해 bounded ring의 capacity를 credit처럼 관리하고, multi-stage consumer의 진행 순서를 coordination plane에서 통제하는 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ring Buffer](./ring-buffer.md)
> - [Bounded MPMC Queue](./bounded-mpmc-queue.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
> - [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md)
> - [ABA Problem and Tagged Pointers](./aba-problem-and-tagged-pointers.md)
> - [Hazard Pointers vs Epoch-Based Reclamation](./hazard-pointers-vs-epoch-based-reclamation.md)

> retrieval-anchor-keywords: sequencer ring buffer, sequence barrier, gating sequence, publish cursor, claim sequence, disruptor sequencer, bounded ring coordination, mpmc ring coordination, ring buffer sequencing, producer consumer sequence, slot sequence protocol, bounded queue coordination, wait strategy, slow consumer gating, credit based backpressure

## 핵심 개념

bounded ring queue의 어려움은 배열 자체보다 "누가 어느 slot을 쓸 차례인가"를 정하는 데 있다.

sequencer 패턴은 이 문제를 풀기 위해:

- claim sequence
- global publish cursor
- consumer progress sequence
- slot-local sequence

를 분리해서 관리한다.

즉 ring buffer는 저장소이고,  
sequencer는 **그 저장소를 안전하게 공유하게 만드는 진행 규약**이다.

## 깊이 들어가기

### 1. 왜 head/tail만으로는 부족한가

SPSC에선 head/tail만으로 충분한 경우가 많다.  
하지만 producer/consumer가 여러 명이면 같은 질문이 겹친다.

- 이 slot이 아직 비워지지 않았나
- 어떤 producer가 이미 claim만 하고 publish는 아직 안 했나
- 내가 지금 publish해도 되나
- 어떤 consumer가 가장 느린가

단순 head/tail만으로는 이런 상태를 분리하기 어렵다.

### 2. claim, fill, publish는 서로 다른 단계다

sequencer 구조에서는 보통 다음을 분리한다.

- claim: producer가 sequence 번호를 예약
- fill: 해당 slot에 payload 작성
- publish: consumer가 볼 수 있게 cursor 전진
- consume: stage가 해당 sequence를 처리
- advance gating: 가장 느린 dependent consumer 기준 갱신

여기서 중요한 점은 claim과 publish가 같지 않다는 것이다.

- producer A가 `100`을 claim
- producer B가 `101`을 claim
- B가 더 빨리 채워도 `100`이 publish되지 않았다면 cursor는 `101`로 건너뛰지 못할 수 있다

즉 sequencer는 단순한 인덱스 증가기가 아니라  
**연속 구간으로 무엇이 소비 가능해졌는지 판정하는 장치**다.

### 3. gating sequence는 capacity credit 모델이다

producer 입장에서 bounded ring의 빈 공간은  
`capacity - (claimSequence - minGatingSequence)`로 해석할 수 있다.

즉 producer는 "배열이 남아 있는가"가 아니라  
"가장 느린 dependent consumer가 몇 칸의 credit를 돌려줬는가"를 본다.

이게 sequencer에서 backpressure가 생기는 방식이다.

- wrap point가 gating sequence를 추월하면 claim 중단
- wait strategy에 따라 spin/yield/park/fail
- consumer가 advance해야만 credit가 복원

bounded MPMC queue에선 full/empty 판단으로 보이던 것이  
sequencer에선 **credit exhaustion**으로 더 명시적으로 드러난다.

### 4. Disruptor 스타일 coordination이 왜 따로 거론되나

일부 ring buffer는 단순 queue를 넘어서 fan-out pipeline을 만든다.

- producer 1개 또는 여러 개
- consumer stage 여러 개
- 각 stage마다 progress sequence

이 경우 queue가 아니라  
**sequence graph 기반 파이프라인 coordination**이 된다.

즉 같은 ring buffer라도

- 단일 handoff queue
- staged event pipeline

은 내부 규약이 꽤 다르다.

예를 들어 `decode -> validate -> enrich -> persist`처럼  
각 stage가 선행 stage sequence를 barrier로 기다리는 구조에서는  
queue보다 dependency graph를 보는 편이 정확하다.

### 5. backpressure와 latency가 sequence 모델에서 갈린다

가장 느린 consumer가 gating point가 되면  
ring 전체 publish가 멈출 수 있다.

장점:

- bounded memory 보장
- overwrite 방지

단점:

- slow consumer가 전체 latency를 끌어올림
- gating topology를 잘못 잡으면 병목이 심해짐

즉 queue의 병목은 CAS만이 아니라  
**누구를 기준으로 진행을 멈추게 하느냐**에서 생긴다.

여기서 wait strategy가 운영 성격을 바꾼다.

- busy spin: 최저 latency, 최고 CPU 사용
- yield/spin hybrid: 짧은 혼잡 흡수
- park/block: CPU 절약, 깨어나는 비용 증가
- timeout/fail-fast: bounded latency budget 유지

즉 sequencer는 자료구조이면서  
**backpressure와 wait 전략의 제어판** 역할을 한다.

### 6. ABA와 reclamation 문제는 어디로 갔나

core ring이 preallocated slot을 재사용한다는 점은 bounded MPMC와 같다.

- slot reuse는 sequence가 세대 표식처럼 관리
- linked node retire/free hot path는 줄어듦

하지만 다음은 여전히 별도 문제다.

- payload가 외부 object pool을 가리킬 때
- parked waiter node나 dependency registration이 동적으로 생성될 때
- off-heap/native descriptor를 stage 사이에 재사용할 때

즉 sequencer는 coordination 문제를 푸는 것이지  
object lifetime 전체를 자동으로 안전하게 만들어주지는 않는다.

### 7. backend에서 어디에 맞나

sequencer 기반 ring은 다음에서 자주 거론된다.

- low-latency event pipeline
- telemetry batching stage
- market data / streaming engine
- bounded internal bus

단순 mailbox보다 더 구조화된 파이프라인일수록  
queue보다 sequence graph 사고가 중요해진다.

## 실전 시나리오

### 시나리오 1: single producer, multiple consumer stages

decode -> enrich -> persist 같은 staged pipeline은  
sequence barrier 모델이 더 자연스러울 수 있다.  
각 stage는 upstream cursor와 선행 stage sequence를 둘 다 본다.

### 시나리오 2: bounded event bus

메모리 상한은 절대 넘기면 안 되지만  
여러 consumer가 서로 다른 속도로 읽는 구조에 잘 맞는다.  
가장 느린 consumer를 gating 기준으로 삼아 overwrite를 막는다.

### 시나리오 3: slow consumer 병목

가장 느린 consumer가 gating이 되면  
ring은 비어 있어도 producer가 못 쓰는 시간이 생길 수 있다.

이 문제를 풀려면 queue 용량 증설보다

- consumer 분리
- 별도 ring으로 fan-out
- 느린 stage 비동기 격리

같은 topology 조정이 더 효과적일 수 있다.

### 시나리오 4: 부적합한 경우

그냥 mailbox handoff만 필요하다면  
sequencer graph는 과하고 MPSC/MPMC queue가 더 단순하다.

## 코드로 보기

```java
import java.util.concurrent.atomic.AtomicLong;

public class SequencerSketch {
    private final AtomicLong nextToClaim = new AtomicLong(0);
    private final AtomicLong cursor = new AtomicLong(-1);
    private final AtomicLong gatingSequence = new AtomicLong(-1);

    public long claimNext(int capacity) {
        while (true) {
            long next = nextToClaim.get();
            long wrapPoint = next - capacity;
            if (wrapPoint > gatingSequence.get()) {
                return -1;
            }
            if (nextToClaim.compareAndSet(next, next + 1)) {
                return next;
            }
        }
    }

    public void publish(long sequence) {
        cursor.set(sequence);
    }

    public void markConsumed(long sequence) {
        gatingSequence.set(sequence);
    }
}
```

이 코드는 sequencing 감각만 보여준다.  
실제 구현은 slot-local sequence, contiguous publish 보장, multiple gating consumer, memory ordering이 핵심이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Sequencer-Based Ring Coordination | bounded ring 위에서 producer/consumer 진행과 multi-stage dependency를 세밀하게 제어할 수 있다 | slow consumer와 topology 설계가 병목이 된다 | staged event pipeline, bounded bus |
| Bounded MPMC Queue | handoff queue로 이해가 더 쉽고 구현 계층이 더 얕다 | fan-out stage coordination엔 덜 직접적이다 | generic bounded queue |
| Lock-Free MPSC Queue | ingress fan-in엔 단순하고 빠르다 | multi-stage bounded coordination은 약하다 | mailbox, submit queue |
| SPSC Ring Buffer | 1:1 파이프에 가장 싸다 | 다단계/다소비자에 안 맞는다 | dedicated low-latency stage |

중요한 질문은 "ring을 공유하나"가 아니라  
"그 위에서 진행 순서를 누가 어떻게 판정하나", "capacity credit를 누가 언제 돌려주나"다.

## 꼬리질문

> Q: bounded MPMC queue와 sequencer 기반 ring은 무엇이 다른가요?
> 의도: 단순 handoff queue와 staged coordination을 구분하는지 확인
> 핵심: 전자는 queue 의미가 강하고, 후자는 sequence graph로 여러 stage를 제어하는 의미가 더 크다.

> Q: claim과 publish를 왜 분리하나요?
> 의도: 예약과 가시화를 같은 것으로 오해하지 않는지 확인
> 핵심: producer가 slot을 예약했다고 해서 payload가 이미 안전하게 공개된 것은 아니기 때문이다.

> Q: gating sequence가 왜 병목이 될 수 있나요?
> 의도: 가장 느린 consumer가 전체 진행을 결정한다는 점 이해 확인
> 핵심: bounded memory를 지키려면 producer가 가장 뒤처진 consumer를 기준으로 멈춰야 하기 때문이다.

> Q: sequencer에서 backpressure는 어떻게 보이나요?
> 의도: bounded capacity를 credit 모델로 이해하는지 확인
> 핵심: producer가 wrap point를 더 이상 밀 수 없을 때, 즉 느린 consumer가 credit를 반환하지 않아 claim이 막힐 때 드러난다.

> Q: 언제 이런 구조가 과한가요?
> 의도: 복잡한 coordination을 남용하지 않는지 확인
> 핵심: 단순 handoff만 필요하면 MPSC/MPMC queue로 충분할 때다.

## 한 줄 정리

sequencer 기반 ring coordination은 bounded ring의 capacity를 gating credit로 관리하면서, claim/publish/consume 단계를 분리해 multi-stage event pipeline의 진행 순서를 제어하는 규약이다.
