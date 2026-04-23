# Circular Queue vs Ring Buffer Primer

> 한 줄 요약: `circular queue`와 `ring buffer`는 같은 원형 배열 아이디어를 공유하지만, 전자는 면접식 큐 설계 용어이고 후자는 시스템 버퍼링 용어로 더 자주 쓰인다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [기본 자료 구조](./basic.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md)
> - [Ring Buffer](./ring-buffer.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
> - [응용 자료 구조 개요](./applied-data-structures-overview.md)
>
> retrieval-anchor-keywords: circular queue vs ring buffer, circular queue, ring buffer, circular buffer, circular queue interview, design circular queue, queue array implementation, front rear, head tail, wraparound queue, modulo queue, bounded queue, overwrite policy, reject policy, blocking queue policy, backpressure, full queue policy, producer consumer, latest n buffer, systems ring buffer, fifo vs overwrite, 원형 큐, 링 버퍼, circular queue primer, ring buffer primer

## 먼저 결론

둘은 완전히 다른 구조라기보다, **같은 뼈대를 어디에 강조하느냐**가 다르다.

| 구분 | Circular Queue | Ring Buffer |
|---|---|---|
| 자주 나오는 맥락 | 자료구조 수업, 면접 구현 문제 | 시스템, 런타임, 스트리밍, 저지연 처리 |
| 먼저 보는 것 | `enQueue`, `deQueue`, `Front`, `Rear`, `isFull` | producer/consumer, overwrite, backpressure, latency |
| 기본 의미 | "원형 배열로 구현한 FIFO queue" | "고정 크기 원형 버퍼" |
| 꽉 찼을 때 질문 | full/empty를 어떻게 구분하지? | 버릴까, 막을까, 늦출까? |
| 동시성 관심 | 보통 낮다 | 자주 높다 |

짧게 말하면:

- `circular queue`는 **큐 인터페이스를 원형 배열로 구현하는 법**에 가깝다.
- `ring buffer`는 **고정 크기 버퍼를 운영 제약 안에서 쓰는 법**에 가깝다.

## 공통 뼈대는 같다

두 용어 모두 보통 아래 구조를 떠올린다.

- 고정 크기 배열
- 끝까지 가면 처음으로 돌아오는 wraparound
- 읽는 위치와 쓰는 위치를 나타내는 포인터
- full / empty 구분 규칙

예를 들어 capacity가 `5`라면 인덱스는 보통 이렇게 돈다.

```text
0 -> 1 -> 2 -> 3 -> 4 -> 0 -> ...
```

그래서 초보자가 느끼는 "이거 결국 같은 거 아닌가?"라는 감각 자체는 맞다.  
실제로 **같은 구현 아이디어를 다른 문맥에서 부르는 경우가 많다.**

## 어디서 갈라지나

### 1. Circular Queue: 면접형 "큐 설계" 용어

`circular queue`라는 표현은 보통 이런 질문에서 나온다.

- `Design Circular Queue`
- `Front/Rear를 O(1)에 구하라`
- `배열로 queue를 구현하되 공간 낭비를 줄여라`

이때 핵심은 **FIFO queue가 깨지지 않게 구현하는 것**이다.

- `enQueue`
- `deQueue`
- `Front`
- `Rear`
- `isEmpty`
- `isFull`

즉 관심사는 보통 이것들이다.

- 원형 인덱스를 어떻게 감쌀까
- full과 empty를 어떻게 구분할까
- `rear`를 마지막 원소로 볼까, 다음 삽입 위치로 볼까

동시성, cache line, publication order 같은 얘기는 보통 여기서 주제가 아니다.

### 2. Ring Buffer: 시스템형 "버퍼 운영" 용어

`ring buffer`는 보통 이런 문맥에서 나온다.

- 로그/event를 고정 크기 메모리에 담고 싶다
- producer/consumer 파이프라인을 싸게 연결하고 싶다
- 최신 `N`개만 유지하고 싶다
- overwrite, reject, blocking, backpressure 중 정책을 골라야 한다

이때 핵심은 단순한 queue API보다 **운영 정책과 성능 특성**이다.

- 메모리 상한이 고정되어 있는가
- 꽉 찼을 때 어떤 정책을 쓸 것인가
- producer와 consumer가 몇 개인가
- tail latency와 allocation 비용이 중요한가

즉 ring buffer는 "`queue`를 구현했다"보다 "`bounded buffer`를 어떤 정책으로 굴린다"에 더 가깝다.
`reject`, `overwrite`, `blocking`, `backpressure`를 초보자 기준으로 따로 비교하고 싶다면 [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md)를 이어서 보면 흐름이 자연스럽다.

## 용어가 헷갈리는 지점

같은 포인터를 가리켜도 설명 방식이 다를 수 있다.

| 자주 보는 표현 | Circular Queue 쪽 뉘앙스 | Ring Buffer 쪽 뉘앙스 |
|---|---|---|
| `front` / `rear` | 현재 맨 앞 원소, 현재 맨 뒤 원소 | 잘 안 쓰거나, `head` / `tail`로 바꿔 말한다 |
| `head` / `tail` | 구현 세부 용어일 수 있다 | 거의 기본 용어다 |
| `enqueue` / `dequeue` | 대표 연산 이름 | `offer` / `poll`, `publish` / `consume` 같은 이름도 흔하다 |
| `isFull` / `isEmpty` | 면접 문제 핵심 포인트 | 정책 판단의 일부일 뿐이다 |
| `size` | 남은 칸 계산용 상태 | lag, capacity, sequence 차이로 더 자주 본다 |

특히 많이 헷갈리는 한 가지:

> 원형 큐 문제의 `rear`는 "마지막 원소 위치"로 설명되는 경우가 많고,  
> ring buffer의 `tail`은 "다음에 쓸 위치"로 설명되는 경우가 많다.

둘 다 맞는 모델이지만, **문서마다 정의가 조금씩 다를 수 있으니 먼저 정의를 확인**해야 한다.

## 문제에서 무엇을 먼저 떠올릴까

| 문제에서 보이는 표현 | 먼저 떠올릴 용어 | 이유 |
|---|---|---|
| `Front()`, `Rear()`, `isFull()`, `원형 배열로 queue 구현` | Circular Queue | 인터페이스와 구현 정확성이 중심이다 |
| `producer/consumer`, `latest N`, `overwrite`, `backpressure` | Ring Buffer | 버퍼 운영 정책과 성능이 중심이다 |
| `audio buffer`, `log buffer`, `event buffer`, `telemetry buffer` | Ring Buffer | 시스템 파이프라인 용어가 더 자연스럽다 |
| `BFS용 queue를 배열로 구현` | Circular Queue 또는 일반 Queue 구현 | 핵심은 FIFO 구현이지 시스템 버퍼링이 아니다 |

## 자주 하는 오해

1. `ring buffer = circular queue`라고 외우고 끝내면 문맥을 놓친다.  
구현 뼈대는 비슷하지만, 질문이 묻는 포인트가 다르다.

2. ring buffer는 항상 overwrite한다고 오해한다.  
아니다. reject, blocking, backpressure처럼 다른 정책도 많다.

3. circular queue가 더 "기초적"이고 ring buffer가 완전히 다른 고급 구조라고 생각한다.  
실제로는 같은 원형 배열 아이디어를 다른 문제 축에서 설명하는 경우가 많다.

4. ring buffer도 무조건 strict FIFO queue라고 생각한다.  
최신값 유지용 overwrite 정책을 쓰면, "가장 오래된 것을 반드시 보존한다"는 queue 감각은 약해질 수 있다.

## 다음 문서로 어떻게 이어질까

- `queue`, `deque`, `priority queue`를 먼저 갈라야 한다면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- 꽉 찬 bounded buffer에서 어떤 full policy를 쓸지 먼저 보고 싶다면 [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md)
- 시스템 쪽 ring buffer 활용과 정책을 더 보고 싶다면 [Ring Buffer](./ring-buffer.md)
- producer 1개 / consumer 1개 저지연 경로까지 보고 싶다면 [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)

## 한 줄 정리

`circular queue`는 **원형 배열 기반 FIFO 큐 구현**에 초점이 있고,  
`ring buffer`는 **고정 크기 원형 버퍼를 시스템 제약 안에서 운영하는 방법**에 더 가깝다.
