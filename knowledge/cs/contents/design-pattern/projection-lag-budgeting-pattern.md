# Projection Lag Budgeting Pattern

> 한 줄 요약: projection lag는 없앨 대상이 아니라 관리할 예산이므로, 유스케이스별 freshness budget과 consumer backlog 예산, 모드별 headroom, degrade 정책을 함께 두어 read model 운영을 설계해야 한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Replica Lag Observability와 Routing SLO](../database/replica-lag-observability-routing-slo.md)
> - [Consistency Repair / Anti-Entropy Platform 설계](../system-design/consistency-repair-anti-entropy-platform-design.md)

retrieval-anchor-keywords: projection lag budget, freshness budget decomposition, consumer backlog budget, watermark headroom, mode specific lag budget, projection budget burn, cutover lag reserve, fallback headroom contract, fallback reserve sizing
retrieval-anchor-keywords: consumer backlog budget, freshness budget 나누기, projection lag budget 나누기, projection lag budget consumer backlog freshness budget, projection lag reserve, lag budget decomposition, projection freshness budget

---

## 핵심 개념

read model 팀이 자주 빠지는 함정은 projection lag를 "무조건 0으로 만들어야 하는 문제"로 보는 것이다.

하지만 실제로는:

- 화면마다 허용 지연이 다르고
- consumer 처리량 예산이 다르고
- backfill/cutover 때 일시적 lag가 커질 수 있다

그래서 더 현실적인 접근은 lag budgeting이다.

- 어떤 화면은 2초 허용
- 어떤 workflow는 30초까지 허용
- 어떤 결정 경로는 stale read 금지

projection lag를 운영 SLO처럼 예산화하면, 아키텍처 결정과 사용자 기대를 함께 맞출 수 있다.

### Retrieval Anchors

- `projection lag budget`
- `freshness budget`
- `read model slo`
- `consumer backlog budget`
- `staleness tier`
- `lag degrade policy`
- `freshness sli`
- `projection budget burn`
- `cutover lag reserve`

---

## 깊이 들어가기

### 1. lag는 절대값보다 tier가 중요하다

예를 들어:

- Tier A: 결제 직후 사용자 확인 화면, 1-2초 이내
- Tier B: 운영 목록, 수 초 허용
- Tier C: 통계 대시보드, 수 분 허용

이렇게 나누지 않으면 모든 read model을 같은 기준으로 평가하게 된다.

### 2. lag budget은 consumer throughput만의 문제가 아니라 end-to-end slice의 합이다

lag는 여러 층의 합이다.

- outbox relay 지연
- broker 지연
- consumer backlog
- projector 처리 시간
- DB/검색 인덱스 반영 시간

그래서 end-to-end freshness budget으로 보는 편이 더 맞다.

| Budget slice | 대표 질문 | 흔한 guardrail |
|---|---|---|
| relay budget | outbox -> broker 전달이 얼마나 늦어도 되는가 | relay p95, max retry queue |
| backlog budget | consumer가 몇 초/분 backlog를 먹어도 되는가 | watermark gap, backlog age |
| projector budget | projection code가 한 건 처리에 얼마나 써도 되는가 | handler latency, hot shard 감지 |
| storage budget | DB/index 반영이 얼마나 늦어도 되는가 | flush/refresh latency |
| fallback reserve | strict screen 우회로가 얼마나 버틸 수 있는가 | fallback rate, write model QPS headroom |

이 slice를 적어 두면 "lag가 크다"를 "relay가 문제인지 projector가 문제인지"로 빨리 분해할 수 있다.

특히 `fallback reserve` slice는 [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)처럼 RPS, concurrency, burst, breaker 기준까지 내려가야 실제 incident 대비가 된다.

### 3. backlog는 메시지 개수보다 시간으로 환산해야 판단이 선다

메시지 backlog 10만 건은 숫자만으로는 의미가 약하다.

- 초당 5만 건 처리 시스템이면 잠깐의 파도일 수 있다
- 초당 100건 처리 시스템이면 이미 budget 초과일 수 있다

그래서 운영 문서에는 보통 다음 둘을 함께 적는다.

- backlog size
- backlog age 또는 target watermark 대비 시간 gap

cutover readiness와 SLO incident는 거의 항상 "몇 건 밀렸나"보다 "몇 초/분 늦었나"로 의사결정된다.

### 4. 예산을 넘기면 degrade 정책이 필요하다

lag가 budget을 넘었을 때 선택지가 있어야 한다.

- write-through fallback
- stale badge 표시
- 일부 화면 기능 비활성화
- read API 503 / maintenance message

예산 없이 운영하면 lag가 커졌을 때 모두가 즉흥 대응하게 된다.

### 5. backfill과 cutover는 일시적으로 budget을 재협상하는 작업이다

projection rebuild 중에는 평소보다 lag가 커질 수 있다.  
이때는 operational mode를 분리하는 게 좋다.

- normal mode freshness
- rebuild mode freshness
- cutover mode fallback

예를 들어 strict path budget이 2초여도, backfill 동안에는 10초까지 허용하되 fallback rate 상한을 더 낮게 둘 수 있다.  
중요한 건 모드가 바뀌었을 때 어떤 budget이 임시로 유효한지 미리 승인돼 있어야 한다는 점이다.

### 6. lag budget에는 남겨둬야 하는 안전 여유가 포함돼야 한다

cutover 전환이나 장애 복구는 budget을 쓰는 작업이다.  
따라서 normal mode에서 budget을 빡빡하게 다 써버리면 전환 실험을 할 여유가 없다.

보통은 다음과 같은 reserve를 둔다.

- strict tier는 평시 budget의 일부만 사용하도록 headroom 확보
- canary 전에는 backlog age가 normal budget의 일정 비율 이하인지 확인
- monthly error budget이 이미 많이 소진됐으면 cutover 연기

즉 lag budget은 현재 허용치이면서 동시에 미래 전환을 위한 reserve다.

### 7. budget은 숫자만이 아니라 승인된 trade-off 문서여야 한다

예를 들어:

- 이 화면은 5초 stale 허용
- 대신 결제 확정 판단은 write model 조회
- 30초 넘으면 degraded mode

이런 합의가 있어야 read/write coordination이 흔들리지 않는다.

### 운영 체크포인트

| 항목 | 꼭 적어야 하는 질문 | 예시 |
|---|---|---|
| Tier | 어느 경로가 strict한가 | 주문 상세 vs 운영 목록 |
| Slice budget | 어디서 지연을 쓸 수 있는가 | relay 500ms, backlog 1s, storage 500ms |
| Reserve | cutover를 위해 얼마를 남길 것인가 | strict path는 50% headroom 유지 |
| Mode budget | rebuild/cutover 때 임시 허용치는 무엇인가 | rebuild mode p95 10초 |
| Degrade | budget 초과 시 무엇을 끌 것인가 | stale badge, fallback, canary freeze |
| Ownership | 누가 slice별 원인을 본다 | platform, consumer owner, search owner |

---

## 실전 시나리오

### 시나리오 1: 주문 목록과 주문 상세

상세는 Tier A, 목록은 Tier B로 둘 수 있다.  
둘 다 같은 projection을 써도 fallback 정책은 다를 수 있다.

### 시나리오 2: 대시보드 집계

대시보드는 늦어도 괜찮지만, lag 지표는 보여줘야 한다.  
숫자가 최신이 아님을 운영자가 알 수 있어야 한다.

### 시나리오 3: relay 지연과 projector 지연 구분

같은 8초 lag라도 relay가 느린 것과 projector가 hot shard에 걸린 것은 대응이 다르다.  
slice budget이 없으면 팀은 backlog만 보고 원인을 혼동하기 쉽다.

### 시나리오 4: 대규모 backfill

backfill 동안 평소 budget을 유지할 수 없다면, cutover 전까지 특정 화면을 processing mode로 두는 편이 더 현실적이다.

---

## 코드로 보기

### freshness tier

```java
public enum FreshnessTier {
    STRICT,
    NORMAL,
    RELAXED
}
```

### lag budget slice

```java
public record ProjectionLagBudget(
    Duration relayBudget,
    Duration backlogBudget,
    Duration projectorBudget,
    Duration storageBudget,
    Duration reserveForCutover,
    FreshnessTier tier
) {}
```

### budget status

```java
public record ProjectionLagStatus(
    Duration currentLag,
    Duration backlogAge,
    double remainingBudgetRatio
) {
    public boolean shouldFallback() {
        return remainingBudgetRatio < 0.2;
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| lag 0 지향 | 직관적이다 | 비용이 커지고 모든 read path가 복잡해진다 | 아주 작은 핵심 경로 |
| end-to-end 숫자 하나만 보는 lag budget | 단순하다 | 병목 위치와 reserve가 가려진다 | 초기 관찰 단계 |
| slice + mode까지 포함한 lag budget 운영 | 현실적인 trade-off가 가능하다 | SLO/모니터링 합의가 필요하다 | 대부분의 projection 시스템 |
| stale 허용 무제한 | 구조가 단순하다 | UX와 비즈니스 오해가 커질 수 있다 | 중요도 낮은 내부 통계 |

판단 기준은 다음과 같다.

- 유스케이스별 freshness tier를 먼저 나눈다
- backlog를 건수보다 시간 gap으로 본다
- lag를 relay/backlog/projector/storage slice로 분해한다
- budget 초과 시 fallback/degrade 정책을 함께 둔다
- rebuild/cutover 모드에서는 임시 budget을 별도로 둔다

---

## 꼬리질문

> Q: projection lag는 줄이면 줄일수록 좋은 것 아닌가요?
> 의도: 절대 최적화 대신 budget trade-off를 보는지 본다.
> 핵심: 아니다. 모든 경로를 초저지연으로 만들 비용과 복잡도가 다르다.

> Q: budget은 누가 정하나요?
> 의도: 기술 수치가 아니라 사용자 기대와 비즈니스 중요도가 개입된다는 점을 아는지 본다.
> 핵심: product/ops/backend가 함께 정하는 운영 계약에 가깝다.

> Q: backlog 건수만 보면 충분하지 않나요?
> 의도: workload 특성에 따라 같은 건수가 전혀 다른 지연을 뜻할 수 있음을 아는지 본다.
> 핵심: 아니다. backlog age나 watermark gap처럼 시간으로 환산해야 cutover/SLO 판단에 쓸 수 있다.

> Q: budget을 넘으면 무조건 fallback해야 하나요?
> 의도: degrade 정책 다양성을 보는지 본다.
> 핵심: 아니다. badge, partial disable, processing mode 등 여러 선택지가 있다.

## 한 줄 정리

Projection lag budgeting은 read model freshness를 감이 아니라 slice별 예산, reserve, degrade 정책으로 다루게 해, SLO 운영과 cutover 판단을 더 설명 가능하고 안정적으로 만든다.
