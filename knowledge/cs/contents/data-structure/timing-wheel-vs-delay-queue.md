# Timing Wheel vs Delay Queue

> 한 줄 요약: Timing Wheel은 대량 timer churn을 bucket으로 싸게 처리하려는 구조이고, Delay Queue는 heap 기반 정밀 deadline 처리를 단순한 blocking 모델로 제공하는 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md)
> - [Timing Wheel Variants and Selection](./timing-wheel-variants-and-selection.md)
> - [Heap Variants](./heap-variants.md)
> - [Calendar Queue](./calendar-queue.md)
> - [Radix Heap](./radix-heap.md)
> - [Concurrent Skip List Internals](./concurrent-skiplist-internals.md)

> retrieval-anchor-keywords: timing wheel vs delay queue, hashed wheel timer vs delay queue, heap timer queue, delayed task scheduler, timeout churn, timer precision, blocking scheduler queue, timer structure comparison, deadline queue, scheduler tradeoff, ordered workload, concurrent ordered scheduler, delay queue vs skip list, deadline index, cancellation heavy scheduler

## 핵심 개념

둘 다 미래 시점 작업을 다루지만 운영 감각이 다르다.

- Timing Wheel: bucket 기반, churn 최적화
- Delay Queue: heap 기반, 정확한 earliest deadline + blocking model

즉 "둘 다 delayed task queue"라고 뭉뚱그리면  
등록/취소 비용, 정밀도, 구현 모델 차이를 놓치기 쉽다.

## 깊이 들어가기

### 1. Delay Queue는 보통 heap 사고다

Delay Queue는 보통 다음 성질을 가진다.

- 가장 이른 deadline을 heap top으로 유지
- consumer는 다음 만료까지 block 가능
- 정밀 ordering이 상대적으로 자연스럽다

장점:

- 구현 모델이 직관적
- 정확한 deadline ordering에 유리
- timer 수가 아주 크지 않을 때 단순하다

단점:

- `offer`/`poll`이 heap 비용을 낸다
- 취소가 많으면 stale entry 정리 비용이 붙는다

### 2. Timing Wheel은 timer churn에 특화된다

Timing Wheel은 deadline 전체를 정렬하기보다  
비슷한 시각의 작업을 같은 bucket으로 묶는다.

장점:

- 대량 등록/취소가 싸다
- idle timeout/lease expiry에 강하다
- bucket scan 비용이 예측 가능하다

단점:

- tick 기반 근사
- cascade/tombstone 관리
- exact earliest ordering은 약하다

### 3. ordered workload를 먼저 분해해야 한다

"시간순으로 처리한다"는 말만으로는 구조를 고르기 어렵다.  
ordered workload는 보통 아래 넷 중 어디에 가까운지 먼저 갈라진다.

- earliest-only dequeue: 언제나 가장 빠른 deadline 하나만 뽑으면 된다
- coarse expiry batch: 같은 시간대 만료 작업을 한꺼번에 처리해도 된다
- ordered neighborhood/range: `ceiling(deadline)`, `[now, now + Δ]` 범위 스캔, tenant별 다음 작업 탐색이 필요하다
- monotone dequeue: 새로 들어오는 deadline이 현재 최소값보다 더 앞서지 않는다

이 구분을 해두면 자료구조 이름보다 역할이 먼저 보인다.

- Delay Queue는 `earliest-only dequeue`에 가장 자연스럽다
- Timing Wheel은 `coarse expiry batch`와 cancellation-heavy timeout에 강하다
- Concurrent Skip List는 `ordered neighborhood/range`가 있는 concurrent scheduler index에 가깝다
- Radix Heap이나 Calendar Queue는 monotone 또는 분포 가정이 맞을 때 검토한다

즉 Timing Wheel과 Delay Queue를 비교할 때도, 사실은 "우리 시스템이 어떤 ordered semantics를 요구하는가"를 먼저 물어야 한다.

### 4. blocking consumer 모델이 필요한가도 차이점이다

Delay Queue는 thread가 "다음 작업 시각까지 잠들었다가" 깨어나는 모델과 잘 맞는다.  
반면 timing wheel은 event loop나 scheduler tick과 더 잘 어울린다.

즉 구조 차이뿐 아니라 runtime model도 다르다.

- dedicated blocking thread
- event loop tick
- poll-based scheduler

### 5. cancellation이 많을수록 차이가 커진다

실무 timer는 취소가 매우 많다.

- 응답이 오면 timeout 취소
- retry 성공 시 재시도 취소
- 세션 종료 시 idle timer 취소

Delay Queue는 heap/stale entry 관리가 부담이 될 수 있고,  
Timing Wheel은 lazy cancellation tombstone이 쌓일 수 있다.

즉 취소 자체가 병목인지도 봐야 한다.

### 6. Concurrent Skip List는 timer queue보다 ordered index에 가깝다

동시성 scheduler를 설명할 때 skip list가 자주 같이 언급되지만, 역할은 다르다.

- Delay Queue는 "다음 하나를 정확히 뽑는" 우선순위 큐다
- Timing Wheel은 "비슷한 시각의 만료를 싸게 처리하는" bucket scheduler다
- Concurrent Skip List는 "정렬된 작업 집합을 여러 스레드가 range/neighbor 질의와 함께 다루는" ordered index다

그래서 아래 기능이 필요하면 skip list가 후보로 올라온다.

- `pollFirstEntry`뿐 아니라 `ceilingEntry`, `higherEntry`가 필요하다
- `[now, now + 100ms]` 같은 윈도우 스캔이 필요하다
- tenant/shard별로 다음 작업을 공정하게 번갈아 훑어야 한다
- 만료 작업을 batch claim하면서도 전체 순서를 유지해야 한다

반대로 아래 패턴이면 skip list를 바로 고르기 어렵다.

- earliest deadline 하나만 필요하다
- 수백만 timeout을 tick 근사로 흘려도 된다
- cancellation churn이 매우 커서 포인터 chasing 자체가 부담이다

즉 skip list는 "Delay Queue의 빠른 대체재"라기보다,  
delay queue로는 부족한 ordered query를 가진 concurrent scheduler용 자료구조다.

### 7. backend에서 고르는 기준

Delay Queue가 잘 맞는 경우:

- timer 수가 중간 규모
- 정확한 ordering이 중요
- dedicated blocking thread 모델

Timing Wheel이 잘 맞는 경우:

- timer 수가 매우 큼
- 취소 churn이 많음
- tick 근사 허용

Concurrent Skip List가 잘 맞는 경우:

- 여러 스레드가 ordered set/map를 동시에 갱신한다
- `ceiling`/`higher`/range scan 같은 ordered API가 필요하다
- 단일 `take()`보다 "다음 작업 구간"을 탐색하는 일이 많다

빠르게 정리하면 아래 표로 보는 편이 쉽다.

| workload 질문 | 자연스러운 기본값 | 이유 |
|---|---|---|
| blocking consumer가 다음 deadline 하나만 기다리면 되는가 | Delay Queue | exact earliest deadline을 단순하게 구현할 수 있다 |
| 취소가 매우 많고 tick 근사 expiry를 허용하는가 | Timing Wheel | bucket 기반으로 churn 비용을 눌러준다 |
| ordered iteration/range scan을 여러 스레드가 함께 써야 하는가 | Concurrent Skip List | concurrent ordered index semantics를 제공한다 |
| workload 분포 가정이 약하고 안전한 baseline이 필요한가 | Heap / Delay Queue | 구현과 운영 리스크가 가장 낮다 |

## 실전 시나리오

### 시나리오 1: RPC timeout 관리

수십만 연결과 timeout 취소가 몰리면  
timing wheel 쪽이 더 자연스러울 수 있다.

### 시나리오 2: 단일 JVM delayed task executor

스레드 하나가 다음 작업까지 block하고 깨는 모델이면  
Delay Queue가 단순하고 실용적이다.

### 시나리오 3: retry scheduler

작업 수와 분포가 작으면 Delay Queue,  
대량 retry churn이면 timing wheel을 더 검토할 만하다.

### 시나리오 4: multi-tenant delayed job index

단순히 "가장 빠른 작업 하나"보다  
tenant별 다음 작업, 특정 시간대 batch scan, 재배치가 중요하면 concurrent skip list 같은 ordered index가 더 잘 맞는다.

### 시나리오 5: 부적합한 경우

둘 다 가정이 안 맞고 workload 분포도 불확실하면  
heap 기반 baseline부터 시작하는 편이 안전하다.

## 꼬리질문

> Q: Timing Wheel이 Delay Queue보다 유리한 순간은 언제인가요?
> 의도: churn 최적화와 정밀 ordering trade-off 이해 확인
> 핵심: timer 수와 취소 churn이 매우 크고 tick 근사를 받아들일 수 있을 때다.

> Q: Delay Queue가 더 단순한 이유는 무엇인가요?
> 의도: blocking heap model 감각 확인
> 핵심: 가장 이른 deadline 하나만 잘 유지하면 되고, consumer가 그 시각까지 block하는 모델과 잘 맞기 때문이다.

> Q: 둘 중 무엇을 택할지 정할 때 가장 먼저 볼 것은 무엇인가요?
> 의도: 자료구조 이름보다 workload 계약을 먼저 보는지 확인
> 핵심: timer 수, 취소 빈도, 정밀도 요구, runtime model이다.

> Q: concurrent skip list는 왜 delay queue의 드롭인 대체재가 아닌가요?
> 의도: timer queue와 ordered index 역할을 구분하는지 확인
> 핵심: skip list는 ordered range/neighbor 질의를 위한 구조이고, block-until-next-deadline semantics를 바로 제공하지 않기 때문이다.

## 한 줄 정리

Timing Wheel과 Delay Queue의 차이는 단순한 구현 취향이 아니라, ordered workload의 종류와 timer churn 규모, blocking model, deadline 정밀도 요구가 다른 데서 나온다.
