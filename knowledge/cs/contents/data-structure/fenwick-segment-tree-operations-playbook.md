# Fenwick and Segment Tree Operations Playbook

> 한 줄 요약: Fenwick Tree와 Segment Tree는 알고리즘 문제용 구조가 아니라, prefix/range aggregation과 quota window 운영을 싸게 만들 수 있는 backend용 집계 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Fenwick Tree](./fenwick-tree.md)
> - [Segment Tree Lazy Propagation](./segment-tree-lazy-propagation.md)
> - [Fenwick Tree vs Segment Tree](./fenwick-vs-segment-tree.md)
> - [Coordinate Compression Patterns](./coordinate-compression-patterns.md)

> retrieval-anchor-keywords: fenwick segment tree operations, quota window aggregation, prefix counter, range counter, sliding bucket updates, backend metrics tree, rate limit bucket tree, sparse timeline aggregation, operational data structure playbook, range update query

## 핵심 개념

Fenwick Tree와 Segment Tree는 "구간 합" 문제용으로만 끝내면 아깝다.  
운영 시스템에서는 다음 질문이 반복된다.

- 특정 시점까지 누적 합은 얼마인가
- 이 기간 전체에 공통 보정을 걸고 싶다
- sparse한 시각/좌표를 압축해서 빠르게 집계하고 싶다

즉 둘 다 본질적으로는 **시간축이나 bucket 축 위의 집계 구조**다.

## 깊이 들어가기

### 1. Fenwick은 prefix 누적 센서에 가깝다

Fenwick Tree는 다음 상황에서 특히 간결하다.

- point update
- prefix sum
- 누적 분포 역추적

예:

- 분 단위 요청 수 누적
- 점수 histogram의 누적 비율
- 특정 임계값 이하 카운트
- shard별 offset 누적치

운영적으로는 "한 점은 자주 바뀌고, prefix는 자주 본다"는 패턴에 잘 맞는다.

### 2. Segment Tree는 range 정책 엔진에 가깝다

Segment Tree는 Fenwick보다 무겁지만 표현력이 넓다.

- range add
- range assign
- range min/max/sum
- lazy propagation

그래서 다음 같은 정책형 집계에 잘 맞는다.

- 기간 전체에 quota 보정
- 스케줄 윈도우 활성/비활성 플래그
- 여러 bucket 구간에 일괄 패널티 적용
- 구간별 최대 부하 감시

즉 Fenwick이 "누적 집계기"라면, Segment Tree는 "구간 상태 관리기"에 더 가깝다.

### 3. 운영 시스템에서는 좌표 압축이 같이 붙는다

실제 서비스의 시간축과 key 공간은 촘촘하지 않을 수 있다.

- 이벤트가 특정 시각에만 생김
- bucket이 sparse함
- tenant별 유효 구간만 존재

이때 좌표 압축 없이 tree를 만들면 공간 낭비가 크다.  
그래서 실무에서는 대개 다음이 같이 온다.

- coordinate compression
- bucketized time axis
- sparse index mapping

즉 tree 자체보다 **어떤 축으로 투영할지**가 먼저다.

### 4. rate limiting / quota 운영에서 어떻게 쓰나

많은 rate limiter는 exact sliding log보다 bucketized counter를 쓴다.  
여기서 tree 구조가 필요한 경우가 생긴다.

- 최근 N bucket 누적치 조회
- 특정 구간 전체에 보정치 적용
- threshold 이하/이상 경계 빠른 탐색

Fenwick은 최근 구간 합과 누적량 질의에 잘 맞고,  
Segment Tree는 일괄 보정이나 range max/min 감시에 유리하다.

### 5. 온콜 관점에서 자주 틀리는 선택

실무에서 흔한 오해:

- 모든 range 문제는 Segment Tree다
- 모든 prefix 문제는 SQL sum으로 충분하다

하지만 판단 기준은 더 구체적이다.

- update가 점인가, 구간인가
- query가 prefix인가, arbitrary range인가
- 값이 sparse해서 압축이 필요한가
- tail latency와 메모리 예산이 어떤가

Fenwick이 더 맞는 문제에 Segment Tree를 쓰면 구현과 디버깅이 과도해지고,  
Segment Tree가 필요한 문제에 Fenwick을 쓰면 patchwork가 늘어난다.

## 실전 시나리오

### 시나리오 1: 분 단위 API 호출 누적

minute bucket counter를 계속 더하고  
`0..t` 또는 `t-k..t` 누적 합을 자주 본다면 Fenwick이 자연스럽다.

### 시나리오 2: 운영자가 특정 기간 전체 quota를 일괄 조정

광고 예산, 노출 quota, 예약 윈도우 전체에 조정치를 얹고  
구간 합/최대치를 봐야 한다면 lazy segment tree가 더 맞다.

### 시나리오 3: sparse한 예약 시간대 집계

예약 가능한 시각이 일부만 존재한다면  
좌표 압축 후 Fenwick/Segment Tree를 얹는 편이 공간 효율적이다.

### 시나리오 4: 부적합한 경우

bucket 수가 작고 쿼리도 단순하면  
plain array prefix sum이 더 단순하고 빠를 수 있다.

## 선택 프레임

| 질문 | 더 자연스러운 선택 |
|---|---|
| point update + prefix/range sum 위주인가 | Fenwick Tree |
| range update가 핵심인가 | Segment Tree + lazy |
| min/max 같은 다른 monoid도 필요한가 | Segment Tree |
| sparse axis를 압축해야 하는가 | 둘 다 가능, coordinate compression 먼저 |
| 운영 복잡도를 최소화해야 하는가 | 가능한 한 Fenwick/array 쪽이 단순 |

## 꼬리질문

> Q: 운영 시스템에서 Fenwick Tree가 생각보다 자주 맞는 이유는 무엇인가요?
> 의도: prefix aggregation 문제를 range tree 전체로 과하게 일반화하지 않는지 확인
> 핵심: 많은 운영 지표는 결국 point update + prefix/range sum 형태이기 때문이다.

> Q: Segment Tree가 필요한 신호는 무엇인가요?
> 의도: lazy propagation이 필요한 상황을 구분하는지 확인
> 핵심: 구간 전체에 공통 보정/상태를 자주 적용해야 할 때다.

> Q: 좌표 압축이 왜 같이 나오나요?
> 의도: 자료구조와 입력 표현을 함께 설계하는 감각 확인
> 핵심: 시간축이나 값축이 sparse하면 tree보다 축 설계가 먼저 병목이 되기 때문이다.

## 한 줄 정리

Fenwick과 Segment Tree의 실무 선택은 "누가 더 고급인가"가 아니라, point/prefix 중심 운영 집계인지 range 정책 엔진인지에 따라 갈린다.
