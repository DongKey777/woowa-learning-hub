# Timing Wheel Variants and Selection

> 한 줄 요약: timing wheel 계열은 timer churn을 싸게 처리하려고 시간을 bucket으로 바꾸는 구조들이며, single wheel, hierarchical wheel, calendar queue, radix heap은 각각 workload 가정이 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md)
> - [Calendar Queue](./calendar-queue.md)
> - [Radix Heap](./radix-heap.md)
> - [Heap Variants](./heap-variants.md)

> retrieval-anchor-keywords: timing wheel variants, hashed wheel timer, single timing wheel, hierarchical timing wheel, calendar queue, radix heap, timer queue selection, delayed task scheduler, timeout wheel, scheduler data structure choice

## 핵심 개념

timer 구조를 고를 때 흔히 "heap vs timing wheel"만 떠올리지만, 실전 선택지는 더 세분화된다.

- single hashed wheel
- hierarchical timing wheel
- calendar queue
- radix heap
- binary heap / delay queue

이 구조들은 모두 "미래 작업을 정렬한다"는 공통 목적을 가지지만,  
최적화하려는 전제가 다르다.

- tick 기반 근사 만료
- deadline 분포의 균일성
- monotone integer key
- exact earliest-deadline-first

즉 timer queue 선택은 자료구조 그 자체보다 **작업 분포 계약**을 먼저 보는 문제다.

## 깊이 들어가기

### 1. single hashed wheel은 가장 싸지만 가정도 강하다

single wheel은 가장 단순하다.

- `slot = deadline % N`
- `round = deadline / N`
- 현재 tick bucket만 본다

장점:

- 삽입이 거의 `O(1)`
- 취소/만료 경로가 예측 가능
- 대량 idle timeout에 강함

한계:

- 최대 delay가 길어질수록 `round`가 커짐
- tick granularity보다 더 정확한 ordering이 어려움
- delay 분포가 넓으면 bucket 편차가 커짐

즉 "가까운 미래 timeout이 많고 대략 tick 정밀도면 충분"할 때 좋다.

### 2. hierarchical wheel은 먼 미래까지 관리하려는 확장형이다

single wheel의 `round` 문제를 해결하려고 상위 wheel을 쌓는다.

- 가까운 미래는 세밀한 하위 wheel
- 먼 미래는 거친 상위 wheel
- 시점이 가까워질수록 cascade

그래서:

- 대량 timeout
- 긴 delay 범위
- 일정 수준 근사 허용

이라는 세 조건이 함께 있을 때 매우 강하다.

반면 구현은 더 복잡해진다.

- cascade 비용
- cancellation tombstone
- wheel 간 tick 정렬

### 3. calendar queue는 "버킷형 priority queue"에 가깝다

calendar queue도 시간을 bucket으로 나누지만,  
timing wheel처럼 tick/round 중심으로 생각하기보다 deadline 분포 중심으로 본다.

장점:

- deadline 분포가 bucket width와 맞으면 평균 비용이 좋다
- priority queue 대체로 쓸 수 있다

한계:

- bucket width tuning이 필요하다
- burst/skew에 약하다
- 동일 시각 집중이 심하면 bucket 내부 정렬 비용이 커진다

즉 timeout churn보다 **event time distribution**이 더 중요할 때 맞는다.

### 4. radix heap은 monotone scheduler에서 강하다

radix heap은 timer 구조처럼 보이진 않지만,  
deadline이 절대 뒤로 가지 않는 monotone queue라면 강력하다.

- 현재 시각 이후 task만 enqueue
- dequeue되는 최소 deadline은 nondecreasing

이 전제가 맞으면 일반 binary heap보다 더 적은 일반성 비용으로 처리할 수 있다.

즉 다음처럼 쓸 수 있다.

- replay scheduler
- monotone deadline queue
- integer time priority queue

하지만 더 이른 deadline이 나중에 들어올 수 있으면 계약이 깨진다.

### 5. binary heap은 여전히 baseline이다

결국 많은 시스템이 binary heap으로 끝나는 이유는 단순하다.

- 구현이 쉽다
- exact earliest ordering이 된다
- workload 가정이 약하다

timer 수가 아주 많지 않거나,  
deadline 분포를 확신할 수 없으면 heap이 여전히 현실적인 기본값이다.

## 실전 시나리오

### 시나리오 1: 대규모 idle timeout

연결 수가 매우 많고 timeout 등록/취소가 빈번하다면  
hierarchical timing wheel 쪽이 대체로 더 자연스럽다.

### 시나리오 2: discrete event simulation / event time scheduler

deadline 분포가 비교적 고르게 퍼져 있고 tuning 여지가 있다면  
calendar queue를 검토할 수 있다.

### 시나리오 3: monotone replay scheduler

시퀀스나 deadline이 절대 뒤로 가지 않는 작업 재생이면  
radix heap이 잘 맞는다.

### 시나리오 4: 불확실한 범용 scheduler

작업 수가 중간 규모고 분포 가정이 불분명하면  
binary heap이 운영 리스크가 가장 낮다.

## 선택 프레임

| 질문 | yes일 때 유력 후보 | 이유 |
|---|---|---|
| tick 단위 근사 만료를 허용하는가 | single / hierarchical timing wheel | churn 비용이 매우 낮다 |
| 아주 먼 미래 delay가 많은가 | hierarchical timing wheel | round 폭증을 피할 수 있다 |
| deadline 분포가 비교적 균일한가 | calendar queue | bucket width tuning이 먹힐 수 있다 |
| key가 monotone nondecreasing인가 | radix heap | monotone integer queue 최적화가 가능하다 |
| 위 가정을 확신할 수 없는가 | binary heap | 범용성이 가장 높다 |

## 꼬리질문

> Q: timing wheel과 calendar queue의 가장 큰 차이는 무엇인가요?
> 의도: 둘 다 bucket 구조라는 공통점 너머의 차이를 이해하는지 확인
> 핵심: timing wheel은 tick/round 기반 timeout 관리이고, calendar queue는 deadline 분포를 전제로 한 bucket형 priority queue다.

> Q: radix heap을 timer queue처럼 쓸 수 있는 조건은 무엇인가요?
> 의도: monotone priority queue 조건 이해 확인
> 핵심: 새로 들어오는 deadline이 현재 최소값보다 작지 않아야 한다.

> Q: 왜 heap이 여전히 기본 선택인가요?
> 의도: 평균 최적화와 운영 단순성 균형 감각 확인
> 핵심: workload 가정이 약하고 exact ordering을 보장하며 구현/운영 리스크가 낮기 때문이다.

## 한 줄 정리

timing wheel 계열 선택은 "어떤 구조가 더 빠른가"보다 "우리 timer workload가 어떤 계약을 만족하는가"를 먼저 보는 문제다.
