# Sketch and Filter Selection Playbook

> 한 줄 요약: sketch/filter 선택은 "무슨 이름이 유명한가"가 아니라 membership, frequency, cardinality, heavy hitters, percentile 중 어떤 질문에 답해야 하는지로 갈린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bloom Filter vs Cuckoo Filter](./bloom-filter-vs-cuckoo-filter.md)
> - [Count-Min Sketch vs HyperLogLog](./count-min-vs-hyperloglog.md)
> - [DDSketch](./ddsketch.md)
> - [Space-Saving Heavy Hitters](./space-saving-heavy-hitters.md)

> retrieval-anchor-keywords: sketch filter selection, bloom vs cuckoo vs xor vs quotient, count-min vs hyperloglog, ddsketch vs kll vs t-digest, heavy hitter structure, approximate data structure decision guide, telemetry sketch choice, probabilistic filter choice, backend observability structure

## 핵심 개념

근사 자료구조는 서로 대체재처럼 보이지만, 실제로는 질문이 다르다.

- membership: 있나 없나
- frequency: 얼마나 자주 나왔나
- cardinality: 서로 다른 개수가 몇 개인가
- heavy hitters: 가장 시끄러운 상위 key가 누구인가
- percentile: 분위수가 얼마인가

즉 "메모리를 적게 쓰는 구조"라는 공통점만으로 고르면 거의 항상 틀린다.

## 질문별 선택

### 1. membership filter

질문:

- 없는 key를 빨리 걸러내고 싶은가
- 집합이 동적인가
- 삭제가 필요한가

대체로:

- [Bloom Filter](./bloom-filter.md): 가장 단순한 기본값
- [Cuckoo Filter](./cuckoo-filter.md): 삭제/동적 운영
- [Xor Filter](./xor-filter.md): 정적 집합, 매우 compact
- [Quotient Filter](./quotient-filter.md): locality와 compactness를 같이 볼 때

### 2. frequency / hot key

질문:

- 임의 key 빈도를 묻는가
- top offender 자체를 알고 싶은가

대체로:

- [Count-Min Sketch](./count-min-sketch.md): point query frequency
- [Space-Saving Heavy Hitters](./space-saving-heavy-hitters.md): top-k heavy hitter 후보

둘은 경쟁이라기보다 보완 관계인 경우가 많다.

### 3. distinct count

질문:

- 고유 사용자/고유 tenant 수를 대략 알고 싶은가

대체로:

- [HyperLogLog](./hyperloglog.md): cardinality 추정의 기본 선택지

### 4. percentile / latency distribution

질문:

- histogram이 필요한가
- 상대 오차가 중요한가
- tail percentile을 특히 잘 보고 싶은가
- rank error 관점으로 봐도 되는가

대체로:

- [HDR Histogram](./hdr-histogram.md): bucket histogram + percentile
- [DDSketch](./ddsketch.md): relative value error 설명이 쉬움
- [KLL Sketch](./kll-sketch.md): compact rank-summary
- [t-Digest](./t-digest.md): tail percentile 표현에 강함

## 선택 프레임

| 운영 질문 | 유력 후보 |
|---|---|
| "이 key는 아예 없나?" | Bloom / Cuckoo / Xor / Quotient |
| "이 key가 얼마나 자주 보였나?" | Count-Min Sketch |
| "지금 가장 noisy한 key는 누구인가?" | Space-Saving |
| "고유 개수는 몇 개인가?" | HyperLogLog |
| "p99는 얼마인가?" | HDR / DDSketch / KLL / t-Digest |

## 자주 하는 실수

### 1. Bloom Filter로 cardinality를 구하려고 함

Bloom은 membership filter다.  
고유 개수 추정은 HLL 계열이 더 맞다.

### 2. Count-Min Sketch로 top offender를 바로 뽑으려 함

CMS는 임의 key point query에는 강하지만,  
상위 ranking은 Space-Saving 같은 후보 구조가 더 직접적이다.

### 3. percentile 요구에 HLL이나 CMS를 들이댐

cardinality와 frequency는 percentile 문제가 아니다.  
latency distribution은 quantile sketch/histogram이 필요하다.

### 4. 정적 집합에 Bloom만 씀

정적 immutable segment prefilter라면  
Xor Filter가 더 compact할 수 있다.

## 운영 시나리오

### 시나리오 1: rate limiting + observability

- suspicious key 추정: Count-Min Sketch
- top noisy key 대시보드: Space-Saving
- exact enforcement: Redis/exact counter

### 시나리오 2: large segment lookup

- negative lookup prefilter: Xor/Bloom
- block selection: sparse index/fence pointer

### 시나리오 3: latency telemetry

- histogram dashboard: HDR
- relative error percentile: DDSketch
- tail percentile 집중: t-Digest
- compact summary merge: KLL

## 꼬리질문

> Q: 근사 자료구조 선택에서 가장 먼저 확인할 질문은 무엇인가요?
> 의도: 이름이 아니라 질의 유형으로 고르는지 확인
> 핵심: membership, frequency, cardinality, heavy hitter, percentile 중 무엇을 묻는지다.

> Q: 왜 Count-Min과 Space-Saving을 같이 쓸 수 있나요?
> 의도: point query와 ranking 문제를 분리하는지 확인
> 핵심: 하나는 임의 key 빈도 추정, 다른 하나는 상위 후보 유지에 강하기 때문이다.

> Q: percentile 구조를 고를 때 무엇을 더 따져야 하나요?
> 의도: quantile sketch 사이의 차이를 운영 요구와 연결하는지 확인
> 핵심: histogram 필요 여부, tail 강조 여부, 상대 오차/순위 오차 중 무엇을 설명할지다.

## 한 줄 정리

sketch/filter 선택은 구조 이름 암기가 아니라, backend가 지금 어떤 질의를 빠르고 싸게 해야 하는지부터 분해하는 문제다.
