# Back-of-Envelope 추정법

> 한 줄 요약: 시스템 설계 면접에서 숫자를 "맞히는" 것이 아니라, 가정과 계산으로 병목과 우선순위를 빠르게 좁히는 방법이다.

retrieval-anchor-keywords: back-of-envelope estimation, DAU, QPS, storage estimate, bandwidth, peak multiplier, headroom, fan-out, retry amplification, hotset, capacity planning

**난이도: 🟢 Basic**

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
