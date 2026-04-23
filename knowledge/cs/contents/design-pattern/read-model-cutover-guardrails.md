# Read Model Cutover Guardrails

> 한 줄 요약: read-model cutover는 단순 스위치 전환이 아니라 parity check, fallback, canary, rollback window, freshness/error-budget guardrail을 갖춘 운영 절차여야 안전하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Projection Rebuild Evidence Packet](./projection-rebuild-evidence-packet.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Rollback Window Exit Criteria](./projection-rollback-window-exit-criteria.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Search Normalization and Query Pattern](./search-normalization-query-pattern.md)
> - [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Dual-Read Comparison / Verification Platform 설계](../system-design/dual-read-comparison-verification-platform-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](../system-design/traffic-shadowing-progressive-cutover-design.md)
> - [Replica Lag Observability와 Routing SLO](../database/replica-lag-observability-routing-slo.md)

retrieval-anchor-keywords: read model cutover guardrails, dual read parity, cutover assumption checklist, normalized query parity, pagination cutover, cursor invalidation, next-page parity, stable sort parity, rollback window, rollback window exit criteria, old projection decommission, rollback command verification, freshness guardrail, strict read fallback contract, error budget admission gate, cutover budget burn, canary promotion threshold, canary dwell time, projection rebuild evidence packet, cutover approval packet, rollback proof packet

---

## 핵심 개념

projection rebuild 자체보다 더 위험한 순간은 cutover다.

- old projection에서 new projection으로 트래픽 전환
- 일부 화면만 새 projection 사용
- fallback 경로가 제대로 작동하는지 확인

이 순간 guardrail이 없으면:

- partial stale read
- parity mismatch unnoticed
- rollback 불가
- read-your-writes regression

Read Model Cutover Guardrails는 전환 자체를 안전하게 만드는 운영 패턴이다.

### Retrieval Anchors

- `read model cutover guardrails`
- `projection canary`
- `dual read parity`
- `rollback window`
- `cutover fallback`
- `strict read fallback contract`
- `freshness guardrail`
- `canary rollback threshold`
- `error budget admission gate`
- `cutover budget burn`

---

## 깊이 들어가기

### 1. cutover는 on/off 스위치보다 단계적 전환이 안전하다

다음 식의 단계가 흔하다.

- shadow read
- sampled dual read compare
- canary traffic
- full cutover
- rollback window 유지

이렇게 해야 "새 projection을 쓰기 시작했다"와 "안전하게 굳혔다"를 구분할 수 있다.

### 2. parity guardrail은 단순 count 비교로 부족하다

최소한 다음 차원을 봐야 한다.

- row count
- key 존재 여부
- 중요한 상태 필드
- 정렬 결과
- 최신 version/watermark

겉으로는 row 수가 같아도 사용자 경험은 달라질 수 있다.

### 3. read-your-writes regression은 cutover에서 자주 터진다

새 projection이 아직 더 느리거나 watermark 반영이 늦으면, 기존에 되던 직후 조회가 깨질 수 있다.

그래서 cutover guardrail에는 다음이 필요하다.

- strict screen list
- fallback read path
- freshness threshold check

### 4. rollback window를 너무 빨리 닫으면 위험하다

full cutover 직후 old projection을 바로 제거하면:

- parity issue 재현이 어려워지고
- 사용자 제보가 와도 즉시 rollback이 어렵다

일정 기간 old projection을 읽기 가능한 상태로 유지하는 편이 낫다.
그리고 그 기간을 언제 닫을지는 [Rollback Window Exit Criteria](./projection-rollback-window-exit-criteria.md)처럼 audit cadence, latent-bug sweep, rollback command verification이 포함된 별도 exit gate로 고정하는 편이 안전하다.

### 5. cutover guardrail은 장애 기준도 포함해야 한다

예를 들어:

- parity mismatch > 0.1%
- freshness budget 초과
- canary error rate 증가
- strict screen fallback rate 급증

이 기준을 넘으면 자동 또는 수동 rollback을 트리거할 수 있어야 한다.

### 6. cutover는 남은 error budget으로 실험을 감당할 수 있는지까지 확인해야 한다

parity가 맞고 fallback도 있어 보여도, 남은 error budget이 거의 없다면 cutover는 시작하면 안 된다.

특히 다음 신호는 admission gate에 들어가는 편이 좋다.

- 최근 1시간/6시간 burn rate가 이미 높음
- strict screen fallback rate가 평시보다 상승
- canary 동안 예상되는 lag reserve가 부족
- 월간 budget 잔여량이 rollback window를 버티지 못함

즉 cutover approval은 "정합성 pass"와 "예산 여유 있음"을 모두 만족해야 한다.

실제 승격 회의에서 이 신호들을 어떤 artifact와 verdict vocabulary로 묶을지는 [Projection Rebuild Evidence Packet](./projection-rebuild-evidence-packet.md)처럼 approval packet 형식으로 고정해 두는 편이 안전하다.

### 7. cutover는 같은 입력을 같은 의미로 해석한다는 가정부터 검증해야 한다

많은 팀이 old/new 결과 row만 비교하지만, 그 전에 먼저 고정돼야 할 게 있다.

- blank keyword를 어떻게 처리하는지
- unknown filter를 drop할지 reject할지
- 기본 sort가 무엇인지
- page size cap이 같은지

즉 dual-read parity는 데이터 비교 이전에 **입력 해석 parity**가 있어야 한다.  
이게 다르면 mismatch는 projection 오류가 아니라 query contract drift일 수 있다.

### 8. 목록 endpoint cutover는 cursor 정책 없이는 반쪽짜리다

상세 조회 cutover는 단건 parity로 설명할 수 있지만, 목록은 다르다.

- 첫 페이지 결과 집합
- 정렬 순서
- 다음 cursor 발급 방식
- 예전 cursor 재사용 여부

이 네 가지가 모두 계약이다.  
특히 old projection에서 발급한 cursor를 new projection이 그대로 받아야 하는지부터 명확해야 한다.

보통 안전한 기본값은 다음 중 하나다.

- cutover 시 cursor 전면 무효화
- schema version을 올려 old cursor 거절
- dual-read로 첫 페이지와 다음 페이지를 함께 검증한 뒤 제한적으로 허용

목록 endpoint 전환만 따로 좁혀 보면 [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)처럼 legacy cursor verdict, stable sort audit, `page 1 -> page 2` continuity를 별도 gate로 빼 두는 편이 안전하다.

### 9. parity 기준은 같은 row 수보다 같은 사용자 경험에 가까워야 한다

실전에서 row count가 같아도 cutover 실패인 경우가 있다.

- tie-breaker가 빠져 ordering이 달라짐
- null ordering 차이로 상단 결과가 바뀜
- collation 차이로 검색 결과 순서가 달라짐
- strict screen에서 read-your-writes 보장이 약해짐

따라서 cutover assumption 문서에는 최소한 다음이 있어야 한다.

- normalized request contract
- stable sort + tie-breaker
- cursor versioning / invalidation 정책
- strict screen fallback 규칙
- rollback threshold와 유지 기간

### 10. fallback은 old read model로 되돌린다보다 더 구체적이어야 한다

fallback은 경로가 있는지보다, **어떤 화면에서 어떤 조건으로 fallback하는지**가 중요하다.

- strict screen만 old projection fallback
- freshness threshold 초과 시에만 fallback
- pagination endpoint는 첫 페이지에만 fallback 허용
- cutover compare 중 mismatch 샘플은 강제로 shadow path 저장

이렇게 해야 rollback과 degrade가 섞이지 않는다.  
모든 요청을 old로 되돌리는 것과, 일부 유스케이스에만 안전장치를 두는 것은 운영 의미가 다르다.

즉 cutover 문서에는 strict screen별 fallback ownership, routing, rate 상한이 별도 계약으로 붙어 있어야 한다.  
이 부분은 [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)와 함께 보면 cutover guardrail을 더 명확히 해석할 수 있다.

### 11. 단계별 진입 조건과 중지 조건을 표로 고정해 두면 운영 해석이 빨라진다

| 단계 | 진입 조건 | 중지 / rollback 조건 |
|---|---|---|
| SHADOW | parity 샘플 수집 시작, normalization 계약 고정 | mismatch 해석 불가, input drift 발견 |
| CANARY | parity 허용 범위 통과, lag reserve 확보, 잔여 budget 충분 | fallback rate 급증, burn rate 상승, strict path regression |
| PRIMARY | canary 안정화, rollback path 살아 있음 | freshness breach 지속, projected budget burn 과다 |
| ROLLBACK WINDOW | old path 유지, latency/quality 재관찰 | latent bug 발견 시 즉시 rollback |

이 표가 없으면 "지금 canary를 멈춰야 하나"를 사람마다 다르게 판단하게 된다.

여기서 stage 이름만 고정해 두고 sample size, dwell time, rollback threshold를 비워 두면 운영 해석이 다시 흐려진다.  
실제 승격 계약은 [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)처럼 stage별 수치 패킷으로 붙여 두는 편이 안전하다.

### 12. cutover assumption checklist를 미리 고정하면 비교 결과 해석이 빨라진다

전환 전에 다음 질문에 답이 있어야 한다.

1. old/new가 같은 normalization 규칙을 쓰는가
2. supported sort set과 기본 sort가 같은가
3. tie-breaker와 null ordering이 같은가
4. 기존 cursor를 재사용할 수 있는가, 아니면 버전업으로 끊는가
5. strict screen의 read-your-writes fallback은 어느 쪽이 책임지는가
6. mismatch, fallback, freshness 초과 시 rollback 기준은 무엇인가
7. 남은 error budget이 어느 정도여야 canary/full cutover를 허용하는가

이 체크리스트가 없으면 cutover 중 발견된 차이를 매번 ad-hoc으로 해석하게 된다.

---

## 실전 시나리오

### 시나리오 1: 주문 검색 projection 교체

새 검색 인덱스를 shadow mode로 돌리고 샘플 비교 후 canary를 연다.  
full cutover 후에도 며칠은 old index를 rollback 가능 상태로 둔다.

### 시나리오 2: 사용자 주문 상세 projection 변경

직후 조회가 중요한 화면이라면 cutover 초기에 strict screen은 old/new dual read와 fallback을 함께 둬야 한다.

### 시나리오 3: 대규모 backfill 후 전환

backfill 완료만 보고 전환하지 말고, tail catch-up과 lag guardrail을 함께 본 뒤 cutover해야 한다.

### 시나리오 4: 검색 목록 projection 교체

새 검색 인덱스로 cutover할 때는 first-page parity만 보면 부족하다.

- normalized query가 old/new에서 같은지
- 동일 tie-breaker로 다음 페이지가 이어지는지
- 기존 cursor를 거절할지 버전업할지
- mismatch가 나면 어느 화면을 old path로 fallback할지

이 가정이 선행돼야 "결과가 다르다"는 사실을 운영적으로 해석할 수 있다.

### 시나리오 5: parity는 통과했지만 budget이 거의 소진된 상태

새 projection이 dual-read에서는 맞아 보여도, 최근 몇 시간 동안 strict fallback이 계속 늘고 있다면 cutover를 미루는 편이 맞다.  
전환은 budget을 먹는 작업이므로, 남은 error budget 없이 강행하면 rollback window를 버티지 못한다.

---

## 코드로 보기

### cutover mode

```java
public enum CutoverMode {
    SHADOW,
    CANARY,
    PRIMARY,
    ROLLBACK
}
```

### parity gate

```java
public record CutoverGuardrail(
    double maxParityMismatchRate,
    Duration maxFreshnessLag,
    double maxFallbackRate,
    double minRemainingBudgetRatio,
    double maxHourlyBudgetBurnRate,
    boolean invalidateLegacyCursor
) {}
```

### dual read compare

```java
public class OrderReadCutoverService {
    public OrderPage read(OrderSearchCriteria rawCriteria, OrderCursor cursor) {
        OrderSearchCriteria normalized = rawCriteria.normalized();
        if (cursor != null && !cursor.matches(normalized)) {
            throw new InvalidCursorException();
        }

        OrderPage oldView = oldRepo.search(normalized, cursor);
        OrderPage newView = newRepo.search(normalized, cursor);
        parityMeter.compare(normalized, oldView, newView);
        return routeByCutoverMode(oldView, newView);
    }
}
```

### admission decision

```java
public boolean canPromoteToCanary(
    CutoverGuardrail guardrail,
    double remainingBudgetRatio,
    double hourlyBudgetBurnRate
) {
    return remainingBudgetRatio >= guardrail.minRemainingBudgetRatio()
        && hourlyBudgetBurnRate <= guardrail.maxHourlyBudgetBurnRate();
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 전환 | 빠르다 | parity/fallback 문제를 놓치기 쉽다 | 매우 작은 내부 전환 |
| parity만 보고 전환 | 구현이 단순하다 | budget burn과 latent freshness 문제를 놓친다 | low-risk 내부 전환 |
| canary + dual read + rollback window + budget gate | 안전하다 | 운영 복잡도와 비용이 든다 | 사용자 영향이 큰 read model |
| 장기 병행 운영 | 안정성이 높다 | 비용이 크고 정리 지점이 흐려질 수 있다 | 전환 리스크가 매우 클 때 |

판단 기준은 다음과 같다.

- strict screen에는 stronger guardrail을 둔다
- parity와 freshness를 같이 본다
- cutover admission에 error budget 잔여량과 burn rate를 넣는다
- rollback window를 미리 정의한다
- query normalization과 pagination 계약도 cutover 가정에 포함한다

---

## 꼬리질문

> Q: backfill이 끝났으면 바로 cutover해도 되지 않나요?
> 의도: rebuild 완료와 운영 guardrail을 구분하는지 본다.
> 핵심: 아니다. parity, freshness, fallback readiness를 같이 봐야 한다.

> Q: row count만 같으면 안전한가요?
> 의도: parity를 다차원으로 보는지 본다.
> 핵심: 아니다. 상태 필드, 정렬, 최신성까지 봐야 한다.

> Q: parity가 통과하면 budget은 안 봐도 되나요?
> 의도: 정합성과 운영 여유를 분리해서 생각하는지 본다.
> 핵심: 아니다. 남은 error budget이 부족하면 cutover 실험 자체를 감당하지 못한다.

> Q: rollback window를 왜 남겨야 하나요?
> 의도: full cutover 후 발견되는 latent issue를 생각하는지 본다.
> 핵심: 늦게 발견되는 문제에 즉시 되돌릴 수 있어야 하기 때문이다.

## 한 줄 정리

Read-model cutover guardrail은 새 projection 전환을 parity, freshness, error-budget gate, fallback, rollback window가 있는 운영 절차로 바꿔 주는 패턴이다.
