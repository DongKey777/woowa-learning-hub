# Read Model Staleness and Read-Your-Writes

> 한 줄 요약: CQRS나 projection 기반 read model을 쓰면 staleness는 피할 수 없는 운영 성질이 되고, 사용자 경험과 정합성 기대치에 맞는 read-your-writes 전략을 따로 설계해야 한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Database: Replica Lag와 Read-after-Write](../database/replica-lag-read-after-write-strategies.md)
> - [Database: Incremental Summary Table Refresh and Watermark Discipline](../database/incremental-summary-table-refresh-watermark.md)
> - [Database: Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
> - [Database: Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)
> - [System Design: Change Data Capture / Outbox Relay](../system-design/change-data-capture-outbox-relay-design.md)
> - [System Design: Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)
> - [System Design: Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md)
> - [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

retrieval-anchor-keywords: read model staleness, read your writes, projection lag, freshness budget, eventual consistency UX, projection watermark, projection rebuild, read model cutover, projection lag budget, summary table refresh, session pinning, strict screen fallback, fallback ownership, fallback routing, fallback rate contract, dual read verification, dual read parity, projection freshness slo, old data after write, saved but still old data, write succeeded but old data

---

## 핵심 개념

read model을 분리하면 조회는 빨라지고 화면 조합은 쉬워진다.  
대신 이제 팀은 새로운 질문을 받아야 한다.

- command는 성공했는데 왜 바로 조회에 안 보이나
- 사용자는 방금 만든 주문을 언제 볼 수 있나
- projection lag가 길어지면 어디까지 허용할 건가

이 문제는 단순한 성능 문제가 아니라 **정합성 기대치와 UX 계약의 문제**다.
사용자 문장으로는 `old data after write`, `저장했는데 옛값이 보인다`처럼 들어오는 경우가 많다.

read model staleness는 projection 기반 시스템의 기본 성질이고, read-your-writes는 그 위에서 선택하는 보장 수준이다.

### Retrieval Anchors

- `read model staleness`
- `read your writes`
- `old data after write`
- `projection lag`
- `freshness budget`
- `eventual consistency UX`
- `projection watermark`
- `projection rebuild`
- `read model cutover`
- `projection lag budget`
- `summary table refresh`
- `session pinning`
- `strict screen fallback`
- `fallback ownership`
- `fallback routing`
- `fallback rate contract`
- `dual read verification`
- `dual read parity`
- `projection freshness slo`

---

## 깊이 들어가기

### 1. read model은 빠르지만 항상 최신일 필요는 없다

많은 read model은 다음 흐름으로 갱신된다.

- command 성공
- domain/integration event 기록
- relay/publisher 전송
- projection consumer 반영

이 사이에는 자연스럽게 지연이 생긴다.

- 브로커 지연
- consumer backlog
- projection 실패 재시도
- 배치성 materialization

즉 read model은 "최신 상태 저장소"가 아니라 **최신 상태를 따라가는 뷰**에 더 가깝다.

### 2. 모든 화면이 read-your-writes를 요구하지는 않는다

중요한 건 "stale read가 가능한가"보다 "어디서 stale read가 위험한가"다.

- 관리자 대시보드: 몇 초 지연 허용 가능
- 주문 직후 상세 화면: 방금 만든 주문이 안 보이면 UX가 크게 깨짐
- 한도/재고 확인: stale read가 곧 잘못된 결정으로 이어질 수 있음

그래서 freshness는 시스템 전체의 절대값이 아니라 **유스케이스별 budget**으로 보는 편이 맞다.

### 3. read-your-writes는 여러 방식으로 구현할 수 있다

가장 흔한 선택지는 다음과 같다.

- command 응답에 write model 결과를 직접 포함
- redirect 직후 한 번은 write model/query port로 읽기
- projection version/watermark가 따라올 때까지 짧게 대기
- 화면에 `processing` 상태를 노출하고 eventual consistency를 드러내기

중요한 건 이걸 우연에 맡기지 않는 것이다.

즉 strict screen fallback은 "필요하면 write model도 한 번 보자" 수준의 암묵 규칙으로 두면 안 된다.

- 어느 화면이 strict인지
- 어떤 신호에서 fallback하는지
- fallback rate를 freshness 문제로 어떻게 해석할지

이 셋을 문서화한 운영 계약이 있어야 read-your-writes 보장이 유지된다.  
이 부분은 [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)에서 ownership, routing, rate contract 중심으로 이어서 볼 수 있다.

### 4. staleness를 숨기려다 경계가 무너질 수 있다

projection lag가 싫다고 해서 every query를 write model join으로 돌리기 시작하면 CQRS 분리 이점이 사라진다.

- command model이 조회 요구에 끌려감
- aggregate repository가 화면 조립 책임까지 떠안음
- read model을 따로 둔 이유가 사라짐

즉 freshness 문제를 해결한다며 repository boundary를 다시 무너뜨리면 안 된다.

### 5. 운영 관점에서는 lag를 측정 가능한 신호로 만들어야 한다

read model staleness는 느낌으로 관리하면 안 된다.

- 마지막 processed event offset
- projection updated at
- command version vs projection version 차이
- consumer backlog size

이런 신호가 있어야 freshness budget을 운영적으로 다룰 수 있다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 직후 상세 페이지

주문 생성 command는 성공했지만 read model projection이 아직 안 끝났을 수 있다.  
이때 바로 read model만 조회하면 "주문이 없다"가 뜰 수 있다.

더 나은 선택지는 다음이다.

- 응답에 생성된 orderId와 기본 상태를 포함
- 첫 상세 조회는 write-through query fallback 허용
- 혹은 `processing` 상태를 보여주고 polling

### 시나리오 2: 관리자 통계 화면

통계는 몇 초 늦어도 큰 문제가 없다.  
이 경우 read-your-writes 보장을 억지로 넣기보다 projection lag 모니터링과 운영 알람이 더 중요하다.

### 시나리오 3: 재고 노출

재고 수량을 read model에서만 보여주면 stale 상태에서 과판매 오해가 생길 수 있다.  
노출용 read model과 실제 예약/확정 command 판단 경계를 분리해야 한다.

---

## 코드로 보기

### command 응답에 최소 write result 포함

```java
public record PlaceOrderResult(
    String orderId,
    String status,
    long aggregateVersion
) {}
```

### projection watermark 확인

```java
public interface OrderProjectionWatermark {
    long currentVersion(String orderId);
}
```

```java
public OrderDetailView readAfterWrite(String orderId, long expectedVersion) {
    if (watermark.currentVersion(orderId) >= expectedVersion) {
        return orderReadRepository.findById(orderId).orElseThrow();
    }
    return orderWriteSideQueryPort.findFreshDetail(orderId);
}
```

### UX로 지연을 드러내기

```java
public record PendingOrderView(
    String orderId,
    String message
) {}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| read model만 즉시 조회 | 구조가 단순하다 | projection lag에 취약하다 | 지연 허용이 큰 화면 |
| write fallback / read-your-writes 보장 | UX가 안정적이다 | 경계 설계와 추가 코드가 필요하다 | 생성 직후 상세, 사용자 확인 화면 |
| processing 상태 노출 | eventual consistency를 솔직하게 다룬다 | UX 설계가 필요하다 | 비동기 반영이 자연스러운 흐름 |

판단 기준은 다음과 같다.

- stale read가 비즈니스 오류인지 UX 불편인지 먼저 구분한다
- read-your-writes가 필요한 화면만 선별한다
- lag는 측정 가능한 운영 지표로 관리한다

---

## 꼬리질문

> Q: CQRS를 쓰면 read-your-writes를 포기해야 하나요?
> 의도: eventual consistency를 절대 규칙처럼 외우지 않는지 본다.
> 핵심: 아니다. 특정 유스케이스에 한해 fallback, watermark, processing UX로 보강할 수 있다.

> Q: projection lag를 없애려면 그냥 동기 업데이트하면 되지 않나요?
> 의도: 성능/경계/복잡도 trade-off를 보는 질문이다.
> 핵심: 가능하지만 read model 분리 이점과 실패 면적이 달라진다.

> Q: stale read가 왜 위험한가요?
> 의도: 유스케이스별 freshness budget을 생각하는지 본다.
> 핵심: 어떤 화면은 괜찮지만, 직후 확인 흐름이나 한도 판단은 사용자 신뢰와 비즈니스 오류로 이어질 수 있다.

## 한 줄 정리

read model staleness는 projection 시스템의 기본 성질이고, read-your-writes는 그 위에서 유스케이스별로 의식적으로 설계해야 하는 보장이다.
