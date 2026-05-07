---
schema_version: 3
title: Back-of-Envelope 추정법
concept_id: system-design/back-of-envelope-estimation
canonical: true
category: system-design
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- capacity-estimation-before-component-choice
- unit-sanity-check
- qps-hotset-headroom-routing
aliases:
- back-of-envelope estimation
- capacity estimation basics
- beginner capacity estimation
- dau qps storage bandwidth estimate
- order of magnitude estimate
- peak qps headroom hotset
- system design 숫자 추정
- 대략적인 QPS 계산
- 저장량 대역폭 추정
- 설계 면접 숫자 감각
- unit sanity check
- 피크 트래픽 계산
symptoms:
- 시스템 설계에서 DAU를 QPS로 바꾸는 계산이 헷갈려
- 숫자 추정을 왜 하는지 모르겠고 그냥 컴포넌트부터 고르게 돼
- 저장량과 대역폭과 hotset을 어떤 단위로 계산해야 할지 막혀
intents:
- definition
- design
prerequisites:
- system-design/system-design-foundations
next_docs:
- system-design/system-design-framework
- system-design/caching-vs-read-replica-primer
- system-design/job-queue-design
- system-design/database-scaling-primer
- system-design/retry-amplification-and-backpressure-primer
linked_paths:
- contents/system-design/system-design-framework.md
- contents/system-design/system-design-foundations.md
- contents/system-design/caching-vs-read-replica-primer.md
- contents/system-design/job-queue-design.md
- contents/system-design/database-scaling-primer.md
- contents/system-design/retry-amplification-and-backpressure-primer.md
- contents/database/index-and-explain.md
- contents/database/query-tuning-checklist.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/cache-control-practical.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
confusable_with:
- system-design/system-design-framework
- system-design/database-scaling-primer
- system-design/caching-vs-read-replica-primer
forbidden_neighbors: []
expected_queries:
- DAU와 하루 요청 수를 QPS로 바꾸는 back-of-envelope 계산을 알려줘
- system design 면접에서 숫자 추정을 왜 먼저 하는지 설명해줘
- peak QPS, bandwidth, storage, hotset을 어떤 순서로 계산해야 해?
- capacity estimation에서 단위 실수를 어떻게 줄일 수 있어?
- QPS 계산 후 cache, replica, queue 중 무엇을 볼지 어떻게 정해?
contextual_chunk_prefix: |
  이 문서는 system design에서 DAU, 요청 수, peak QPS, 응답 크기, 저장량, bandwidth, hotset, headroom을 빠르게 추정해 병목 후보와 다음 설계 질문을 좁히는 beginner primer다.
  숫자를 정확히 맞히는 일이 아니라 단위 sanity check와 order-of-magnitude 계산으로 cache, replica, queue, index, sharding 같은 선택지를 고르는 자연어 paraphrase가 본 문서에 매핑된다.
---
# Back-of-Envelope 추정법

> 한 줄 요약: 시스템 설계 면접에서 숫자를 "맞히는" 것이 아니라, 가정과 계산으로 병목과 우선순위를 빠르게 좁히는 방법이다.

retrieval-anchor-keywords: back-of-envelope estimation, dau, qps, storage estimate, bandwidth, peak multiplier, headroom, fan-out, retry amplification, hotset, capacity planning, unit sanity check, order of magnitude estimate, beginner capacity estimation, beginner estimation routing

**난이도: 🟢 Beginner**

관련 문서:

- [시스템 설계 면접 프레임워크](./system-design-framework.md)
- [인덱스와 실행 계획](../database/index-and-explain.md)
- [쿼리 튜닝 체크리스트](../database/query-tuning-checklist.md)
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
- [Cache-Control 실전](../network/cache-control-practical.md)
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)

---

## 핵심 개념

Back-of-envelope 추정은 말 그대로 "종이 뒷면에 적을 수 있을 정도의 빠른 계산"이다.
시스템 설계 면접에서는 정확한 수치보다 다음이 더 중요하다.

- 요구사항의 크기를 감으로가 아니라 숫자로 바꿀 수 있는가
- 어떤 자원이 먼저 병목이 되는지 추론할 수 있는가
- 캐시, 샤딩, 인덱스, 큐잉이 왜 필요한지 설명할 수 있는가

추정의 목적은 정답을 내는 것이 아니다.

- 설계 범위를 줄이고
- 위험한 가정을 드러내고
- 질문을 더 잘 하기 위한 기준선을 만드는 것이다

## 먼저 잡는 mental model: 계산을 "다음 설계 질문"으로 번역하기

Back-of-envelope 결과는 최종 답이 아니라 다음 설계 질문을 고르는 라우팅 표다.
초보자라면 숫자를 낸 뒤 바로 아래 표로 연결하면 된다.

| 계산에서 먼저 튀는 신호 | 바로 던질 설계 질문 | 다음 문서 |
|---|---|---|
| 피크 QPS가 예상보다 높다 | read 부하를 cache/replica/queue 중 어디서 먼저 흡수할까 | [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md) |
| 응답 전송량(`MB/s`)이 높다 | 네트워크/직렬화/keep-alive 중 어디가 먼저 병목일까 | [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md) |
| write fan-out/retry 배수가 크다 | 비동기 큐잉과 재시도 경계를 어떻게 잡아 증폭을 막을까 | [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md), [Job Queue 설계](./job-queue-design.md) |
| 저장량보다 hotset 변동이 크다 | 캐시 용량과 eviction 기준을 무엇으로 잡을까 | [Cache-Control 실전](../network/cache-control-practical.md) |

## 첫 회독 5분 루트: 숫자 3개만 먼저 고정하기

처음 읽을 때 모든 공식을 다 붙잡기보다 아래 3개 숫자만 정확히 적으면 된다.

| 먼저 고정할 숫자 | 왜 먼저 보나 | 초보자 기본값(불명확할 때) |
|---|---|---|
| `peak QPS` | 병목 후보를 가장 빨리 좁힌다 | 평균 QPS에 `x5~x10` 임시 배수 |
| `응답 전송량(MB/s)` | DB가 아니라 네트워크가 먼저 막히는지 본다 | 평균 응답 크기 `4~16KB`로 범위 계산 |
| `hotset 메모리(GB)` | 캐시가 현실적인지 바로 판단한다 | 전체의 `1~10%`를 hotset 가정 |

정확한 값이 없으면 단일 숫자 대신 범위(최소~최대)로 적고, 설계 판단은 보수적인 상한 기준으로 시작한다.

## 초보자 4단계 계산 루틴

처음에는 공식을 많이 외우기보다 아래 순서를 고정하면 된다.

| 단계 | 먼저 적을 것 | 바로 확인할 질문 |
|---|---|---|
| 1 | `하루 요청 수` | 읽기/쓰기 중 어디가 먼저 병목이 될까 |
| 2 | `평균/피크 QPS` | 평균이 아니라 피크에서도 버틸 수 있나 |
| 3 | `응답 크기/저장 크기` | 병목이 DB인지 네트워크인지 어디인가 |
| 4 | `headroom (2x~3x)` | retry, 배치, 장애 복구까지 포함하면 안전한가 |

이 루틴의 목적은 정밀 계산이 아니라 **병목 후보를 1~2개로 좁히는 것**이다.

## 30초 sanity check: 단위 실수 먼저 잡기

초보자가 가장 자주 틀리는 지점은 공식보다 단위다.
아래 표처럼 "입력 단위 -> 중간 단위 -> 최종 단위"를 한 번만 적어도 큰 실수를 많이 줄일 수 있다.

| 계산 항목 | 입력 단위 | 중간 단위 | 최종 단위 |
|---|---|---|---|
| 요청량 | `req/day` | `/86,400` | `req/sec (QPS)` |
| 응답 전송량 | `QPS`, `KB/resp` | `QPS x KB` | `KB/s` 또는 `MB/s` |
| 저장 용량 | `records`, `KB/record` | `records x KB` | `GB/TB` |
| 캐시 메모리 | `hot items`, `KB/item` | `items x KB` | `GB` |

한 줄 규칙:

- `day` 단위를 `sec`로 바꾸지 않았으면 QPS 계산이 거의 항상 과대/과소된다.
- 용량은 `base data` 뒤에 인덱스/메타 오버헤드를 더한 값을 따로 적는다.

## 30초 예시: 댓글 API 트래픽 감 잡기

가정:

- DAU `20만`
- 1인당 댓글 조회 `12회/일`
- 피크 계수 `6`
- 응답 크기 `6KB`

```text
하루 요청 수 = 200,000 x 12 = 2,400,000 req/day
평균 QPS = 2,400,000 / 86,400 ≈ 28
피크 QPS = 28 x 6 ≈ 168
초당 전송량 = 168 x 6KB ≈ 1MB/s
```

이 계산 하나로도 첫 설계 질문이 바로 정리된다.

- 이 구간은 DB보다 캐시 hit/miss 패턴이 먼저 중요할 가능성이 크다.
- 네트워크는 즉시 위험 구간은 아니지만 응답 크기가 커지면 빠르게 역전될 수 있다.

---

## 깊이 들어가기

### 1. 먼저 잡아야 할 숫자

면접에서 자주 쓰는 시작점은 아래 네 가지다.

- `DAU` 또는 `MAU`
- 사용자당 평균 행동 수
- 평균 데이터 크기
- 피크 시간대 배수

대부분의 시스템은 평균보다 피크가 중요하다.
평균 QPS만 보면 여유 있어 보여도, 출퇴근 시간이나 이벤트 직후에는 실제 트래픽이 몇 배로 뛸 수 있다.

### 2. 자주 쓰는 기본 공식

```text
평균 QPS = 하루 요청 수 / 86,400
피크 QPS = 평균 QPS x 피크 계수

저장 용량 = 레코드 수 x 레코드 크기 x (1 + 인덱스/메타데이터 오버헤드)

대역폭 = QPS x 평균 응답 크기

메모리 요구량 = 캐시에 올릴 핫 데이터 수 x 항목 크기 x 오버헤드
```

여기서 중요한 점은 "정확한 상수"가 아니라 "단위가 맞는지"다.

예를 들어:

- 요청 수는 `req/day`
- QPS는 `req/sec`
- 용량은 `bytes`, `MB`, `GB`
- 대역폭은 `bytes/sec` 또는 `Mbps`

단위를 혼동하면 계산이 그럴듯해 보여도 완전히 틀린 결론이 나온다.

### 3. headroom은 반드시 남긴다

실제 시스템은 추정값 그대로 돌지 않는다.

- 스파이크가 있다
- 재시도가 있다
- 배치가 같이 돈다
- 캐시 미스가 있다
- 장애 복구 중 트래픽이 몰린다

그래서 설계 단계에서는 보통 `2x~3x` 정도의 headroom을 고려한다.
이 숫자는 절대 법칙이 아니라, "여유 없이 딱 맞게" 잡는 설계가 위험하다는 뜻이다.

### 4. 트래픽 패턴을 같이 읽어야 한다

같은 QPS라도 패턴이 다르면 설계가 달라진다.

- 읽기 많은 서비스: 캐시와 CDN이 효과적이다
- 쓰기 많은 서비스: 배치, 큐, 로그 적재, 인덱스 비용을 먼저 봐야 한다
- 버스트성 트래픽: 레이트 리미팅과 버퍼링이 중요하다
- 주기성 트래픽: 캐시 TTL과 프리워밍 전략이 중요하다

이 단계에서 자주 연결되는 문서가 [인덱스와 실행 계획](../database/index-and-explain.md)과 [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)이다.

### 5. 캐시와 메모리는 "핫셋"을 먼저 본다

캐시는 전체 데이터를 올리는 곳이 아니라, 자주 쓰는 데이터만 올리는 곳이다.

따라서 메모리 추정은 다음 순서가 실용적이다.

1. 전체 데이터 크기를 계산한다
2. 그중 자주 접근되는 비율을 잡는다
3. 캐시 항목당 오버헤드를 더한다
4. TTL, eviction, replication 비용을 고려한다

예를 들어 핫 데이터가 전체의 5%라면, 전체 데이터를 기준으로 메모리를 잡으면 과하게 잡을 가능성이 크다.
반대로 핫셋을 너무 작게 잡으면 캐시 적중률이 낮아져 DB가 다시 병목이 된다.

### 6. 네트워크는 응답 크기까지 같이 봐야 한다

QPS만 계산하고 끝내면 절반만 본 것이다.

## 깊이 들어가기 (계속 2)

- 작은 JSON 1개와
- 이미지/첨부를 포함한 응답 1개는

같은 QPS라도 네트워크 비용이 전혀 다르다.

대역폭은 보통 아래처럼 본다.

```text
초당 전송량 = 피크 QPS x 평균 응답 크기
```

응답이 커질수록 로드밸런서, 프록시, TLS, keep-alive 전략까지 영향을 받는다.
이 부분은 [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)와 함께 보는 것이 좋다.

### 7. 추정이 자주 틀리는 지점

숫자 자체는 맞는데 설계가 틀어지는 경우가 많다. 보통 아래를 빼먹는다.

- fan-out 배수
- retry amplification
- reindex / backfill 비용
- cache warmup과 cold start
- multi-region failover 시 트래픽 배수
- batch job의 주기적 몰림
- human review나 manual ops의 처리량

이 함정은 다음 문서와 직접 연결된다.

- [Job Queue 설계](./job-queue-design.md)
- [Distributed Scheduler 설계](./distributed-scheduler-design.md)
- [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)
- [Webhook Consumer Platform 설계](./webhook-consumer-platform-design.md)
- [Email Delivery Platform 설계](./email-delivery-platform-design.md)
- [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)
- [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)
- [Billing / Usage Metering System 설계](./billing-usage-metering-system-design.md)

---

## 실전 시나리오

### 예시: 게시글 조회 서비스

가정:

- DAU 100만 명
- 사용자 1명당 하루 평균 조회 20회
- 전체 요청 중 90%가 조회
- 피크는 평균의 10배
- 응답 크기 평균 8KB
- 한 레코드 평균 1KB, 인덱스 오버헤드 30%

계산:

```text
하루 총 요청 수 = 1,000,000 x 20 = 20,000,000 req/day
평균 QPS = 20,000,000 / 86,400 ≈ 231 QPS
피크 QPS = 231 x 10 ≈ 2,310 QPS

초당 응답 전송량 = 2,310 x 8KB ≈ 18MB/s
```

이 숫자가 주는 의미:

- 평균만 보면 작아 보이지만 피크에서는 꽤 무겁다
- 조회 비율이 높으니 캐시가 효과적일 가능성이 크다
- 응답 크기가 크면 DB보다 네트워크와 직렬화가 먼저 병목이 될 수 있다

저장 용량도 같이 본다.

```text
게시글 1,000만 개 x 1KB = 10GB
인덱스/메타데이터 포함 x 1.3 = 13GB
```

여기서 면접 답변은 "13GB다"로 끝나면 안 된다.

- 단일 DB에 넣을지
- 파티셔닝이 필요한지
- 캐시 워밍이 필요한지
- 백업/복구 시간이 허용되는지

까지 이어져야 한다.

### 예시: 알림 시스템

알림은 보통 조회보다 쓰기와 fan-out이 문제다.

- 한 이벤트가 여러 사용자에게 전파된다
- 피크 순간에 burst가 발생한다
- 중복 전송 방지가 필요하다

이 경우 추정은 단순 QPS보다 다음을 먼저 본다.

- 이벤트 1건당 수신자 수
- 평균 fan-out 비율
- 재시도 시 중복 가능성
- 큐 적체 허용 시간

이런 시스템은 [시스템 설계 면접 프레임워크](./system-design-framework.md)에서 요구사항을 나눈 뒤, QPS보다 먼저 fan-out 비용을 계산하는 편이 더 정확하다.

### 예시: 실시간 분석과 관측성

가정:

- 초당 이벤트 100만 개
- 이벤트당 200 bytes
- 5분 윈도우 집계
- distinct count와 heavy hitter도 필요

이 경우 단순 저장량보다 다음이 중요하다.

- ingest lag
- watermark delay
- checkpoint 비용
- hot key와 cardinality

이런 경우는 [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md), [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md), [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md), [HyperLogLog](../data-structure/hyperloglog.md), [Count-Min Sketch](../data-structure/count-min-sketch.md)와 함께 봐야 한다.

### 예시: 플랫폼 제어 평면

가정:

## 실전 시나리오 (계속 2)

- 2,000개 인스턴스
- 1분마다 config refresh
- flag와 rate limit policy도 함께 전파

이 경우 핵심은 저장량이 아니라 propagation delay와 rollback time이다.

관련 문서:

- [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
- [Config Distribution System 설계](./config-distribution-system-design.md)
- [Rate Limit Config Service 설계](./rate-limit-config-service-design.md)

---

## 코드로 보기

아래는 면접장에서 바로 써먹을 수 있는 아주 단순한 추정 템플릿이다.

```python
def estimate_system(
    dau: int,
    actions_per_user_per_day: int,
    peak_multiplier: float,
    response_kb: float,
    record_kb: float,
    index_overhead: float = 0.3,
    hot_ratio: float = 0.05,
):
    daily_requests = dau * actions_per_user_per_day
    avg_qps = daily_requests / 86400
    peak_qps = avg_qps * peak_multiplier

    bandwidth_mb_s = peak_qps * response_kb / 1024
    total_storage_gb = daily_requests * record_kb * (1 + index_overhead) / 1024 / 1024
    hot_cache_gb = total_storage_gb * hot_ratio

    return {
        "avg_qps": round(avg_qps, 2),
        "peak_qps": round(peak_qps, 2),
        "bandwidth_mb_s": round(bandwidth_mb_s, 2),
        "storage_gb": round(total_storage_gb, 2),
        "hot_cache_gb": round(hot_cache_gb, 2),
    }
```

이런 함수의 목적은 계산 자동화가 아니다.

- 어떤 입력값이 중요한지 보이게 하고
- 가정이 바뀌면 결과가 얼마나 달라지는지 보여주고
- 면접관과 같은 숫자판을 보게 만드는 데 있다

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 대충 크게 잡기 | 빠르고 안전해 보임 | 비용 과다, 설계 판단이 흐려짐 | 아주 초반 브레인스토밍 |
| 과하게 정밀하게 잡기 | 숫자가 그럴듯함 | 면접 시간 낭비, 가정이 복잡해짐 | 거의 비추천 |
| 핵심 숫자만 잡기 | 빠르고 설계 판단에 충분함 | 일부 오차는 감수해야 함 | 시스템 설계 면접의 기본 |

추정의 목표는 정확도 자체가 아니다.
**"무엇이 병목인지 설명 가능한 수준"**이면 충분하다.

---

## 흔한 혼동

- 숫자를 소수점까지 정확히 맞히는 시험이라고 오해하기 쉽다. beginner 단계에서는 order-of-magnitude와 병목 방향이 맞는지가 우선이다.
- `DAU`를 트래픽으로 바로 쓰면 안 된다. 사용자당 행동 수를 곱해 `req/day`로 바꿔야 한다.
- 평균 QPS가 낮다고 안전한 것은 아니다. 피크 계수를 빼면 병목을 늦게 발견한다.
- 저장 용량 추정에서 인덱스/메타데이터를 빼면 실제 디스크 요구량을 과소평가한다.
- 캐시 메모리를 전체 데이터 기준으로 잡으면 과하게 큰 숫자가 나온다. 핫셋 비율부터 정해야 한다.
- 계산 결과 하나만 말하면 설계 근거가 약하다. 어떤 가정이 결과를 크게 바꾸는지도 같이 말해야 한다.
- 숫자를 계산한 뒤 바로 아키텍처를 고정하면 위험하다. 초보자 단계에서는 "가장 큰 병목 후보 1~2개"만 먼저 결정하고, 나머지는 다음 문서에서 좁힌다.

---

## 다음으로 이어 읽기

초보자용으로는 "지금 막힌 질문" 기준으로 다음 문서를 고르면 된다.

| 지금 막힌 지점 | 다음 문서 | 이유 |
|---|---|---|
| 면접 답변 구조가 흩어진다 | [시스템 설계 면접 프레임워크](./system-design-framework.md) | 추정 결과를 요구사항/컴포넌트/트레이드오프로 연결하기 쉽다 |
| 읽기 병목에서 cache와 replica 중 선택이 어렵다 | [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md) | 지연, 비용, stale 허용치 기준으로 분기할 수 있다 |
| retry/timeout 배수 때문에 계산이 자꾸 흔들린다 | [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md) | 증폭 계수와 상한을 함께 계산하는 방법을 본다 |
| fan-out 비동기 처리량 추정이 어렵다 | [Job Queue 설계](./job-queue-design.md) | enqueue/dequeue/worker 처리량으로 분해해 계산하기 쉽다 |

---

## 꼬리질문

> Q: 왜 평균 QPS가 아니라 피크 QPS를 먼저 봐야 하나요?
> 의도: 트래픽 분포와 용량 계획 감각을 보는 질문
> 핵심: 평균은 평시 기준이고, 장애와 확장은 피크 기준으로 결정된다

> Q: 저장 용량 계산에서 인덱스 오버헤드를 왜 더하나요?
> 의도: DB 저장 구조와 인덱스 비용을 이해했는지 확인
> 핵심: 실제 저장소는 데이터만 있는 것이 아니라 인덱스, 메타데이터, 로그가 함께 쌓인다

> Q: 캐시 용량은 전체 데이터 크기와 같아야 하나요?
> 의도: 캐시를 저장소 복제본처럼 보는지 확인
> 핵심: 캐시는 핫셋 중심으로 잡고, hit ratio와 eviction 정책을 같이 봐야 한다

> Q: 추정값이 크게 틀리면 어떻게 하나요?
> 의도: 숫자 정확도보다 의사결정 과정을 보는 질문
> 핵심: 가정을 다시 밝히고, 민감한 변수부터 재계산한다

> Q: 면접에서 계산 실수를 줄이려면 어떻게 하나요?
> 의도: 커뮤니케이션과 계산 습관을 확인
> 핵심: 단위를 먼저 적고, 중간값을 말로 설명하고, 최종값은 반올림해서 제시한다

> Q: fan-out이나 retry를 왜 별도로 더해야 하나요?
> 의도: 계산에 숨은 배수를 아는지 확인
> 핵심: 한 번의 요청이 여러 작업으로 퍼지거나 다시 시도되면 실제 부하가 곱으로 커진다

---

## 한 줄 정리

Back-of-envelope 추정은 "정답 숫자 맞히기"가 아니라, 가정과 계산으로 QPS, 저장, 대역폭, 메모리의 병목을 빠르게 드러내는 면접용 도구다.
