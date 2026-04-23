# Reclamation Cost Trade-offs

> 한 줄 요약: lock-free 구조의 실전 비용은 CAS 알고리즘 자체보다 retire queue, scan, stalled thread, 메모리 회수 지연 같은 reclamation 비용에서 크게 갈린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Hazard Pointers vs Epoch-Based Reclamation](./hazard-pointers-vs-epoch-based-reclamation.md)
> - [Michael-Scott Lock-Free Queue](./michael-scott-lock-free-queue.md)
> - [ABA Problem and Tagged Pointers](./aba-problem-and-tagged-pointers.md)
> - [Concurrent Skip List Internals](./concurrent-skiplist-internals.md)

> retrieval-anchor-keywords: reclamation cost tradeoffs, hazard pointer cost, epoch reclamation cost, retire list growth, stalled thread memory retention, lock-free reclamation overhead, memory reclamation performance, concurrent memory management cost, scan overhead, reclamation latency

## 핵심 개념

safe reclamation은 correctness 문제이면서 동시에 성능 문제다.  
실무에서는 "무엇이 안전한가" 다음으로 "무엇이 얼마나 비싼가"가 중요하다.

대표 비용 축:

- fast path publish 비용
- retire list 길이
- global scan 비용
- stalled thread가 잡고 있는 메모리
- batch free latency

즉 reclamation 전략은 correctness addon이 아니라  
**lock-free 자료구조의 총비용 모델** 일부다.

## 깊이 들어가기

### 1. Hazard Pointer 비용

Hazard Pointer는 정밀하지만 비용이 눈에 잘 보인다.

- 읽기 전에 pointer publish
- recheck/retry
- retire 시 hazard slot scan

즉 read-heavy path에서는 publish/retry 오버헤드가 체감될 수 있다.  
대신 stalled thread 하나가 전체 메모리 회수를 오래 막는 문제는 상대적으로 덜하다.

### 2. EBR 비용

EBR은 fast path가 가볍지만 비용이 다른 곳으로 간다.

- 오래된 epoch retire list 누적
- 느린 thread 때문에 free 지연
- burst retire 시 메모리 사용량 급증

즉 throughput은 잘 나올 수 있지만,  
메모리 footprint와 tail reclaim latency는 더 나빠질 수 있다.

### 3. 비용은 queue/list마다 다르게 체감된다

같은 reclamation 전략도 구조마다 체감 포인트가 다르다.

- queue: node retire 폭이 일정할 수 있음
- skip list: level별 node/link 구조 때문에 retire 복잡도가 큼
- stack/list: ABA와 reuse 패턴이 더 민감할 수 있음

즉 reclamation 비용은 알고리즘과 독립된 숫자가 아니다.

### 4. 운영에서는 메모리 지연이 장애로 보일 수 있다

reclaim가 늦어지면 correctness는 멀쩡해도 다음처럼 보일 수 있다.

- RSS가 계속 증가
- allocator pressure
- page cache 잠식
- GC/native fragmentation 증가

즉 "안전하니까 괜찮다"가 아니라,  
회수 지연 자체가 운영 장애 모드가 될 수 있다.

### 5. 선택 기준은 throughput 하나가 아니다

다음을 같이 봐야 한다.

- fast path latency
- reclaim burst latency
- worst-case memory retention
- thread lifecycle 제어 가능성
- native vs GC runtime

실무에선 이 다섯 가지가 종종 trade-off를 만든다.

## 실전 시나리오

### 시나리오 1: high-throughput fixed worker queue

worker 수가 고정되고 thread가 안정적이면  
EBR이 throughput 면에서 매력적일 수 있다.

### 시나리오 2: long-lived reader / preemption-heavy runtime

느린 thread 하나가 계속 epoch를 붙잡을 수 있다면  
EBR은 memory retention이 심해질 수 있다.

### 시나리오 3: memory budget tight service

fast path가 조금 느려도 reclaim 지연을 더 작게 통제해야 한다면  
Hazard Pointer 쪽이 더 안전할 수 있다.

### 시나리오 4: 부적합한 이해

"CAS가 빠르니 전체 구조도 빠르다"는 판단이 가장 위험하다.  
retire/free 비용을 빼고 보면 production 성능을 놓치기 쉽다.

## 비교 질문

| 질문 | 더 민감한 구조 |
|---|---|
| stalled thread가 회수를 오래 막아도 되는가 | EBR |
| fast path publish 비용을 감수할 수 있는가 | Hazard Pointer |
| 메모리 footprint 증가가 더 위험한가 | EBR 쪽 위험 증가 |
| reader retry 비용이 더 위험한가 | Hazard Pointer 쪽 비용 증가 |

## 꼬리질문

> Q: 왜 reclamation 비용을 알고리즘 밖 문제로 보면 안 되나요?
> 의도: correctness와 performance가 분리되지 않는다는 점 이해 확인
> 핵심: safe reclamation 방식에 따라 fast path latency와 memory retention이 크게 달라지기 때문이다.

> Q: EBR이 throughput이 좋아 보여도 운영 리스크가 생기는 이유는 무엇인가요?
> 의도: 메모리 회수 지연을 성능 문제로 이해하는지 확인
> 핵심: 느린 thread 하나가 오래된 retire list 해제를 막아 메모리 사용량과 reclaim tail을 키울 수 있기 때문이다.

> Q: Hazard Pointer가 더 정밀한 대신 치르는 대표 비용은 무엇인가요?
> 의도: precision과 overhead trade-off 이해 확인
> 핵심: hazard publish/retry와 retire scan 비용이다.

## 한 줄 정리

lock-free 구조의 실전 비용은 CAS 성공률만으로 설명되지 않고, 어떤 reclamation 전략이 retire latency와 memory retention을 어떻게 만드는지까지 함께 봐야 한다.
