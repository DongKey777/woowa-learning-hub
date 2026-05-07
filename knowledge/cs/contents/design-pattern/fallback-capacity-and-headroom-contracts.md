---
schema_version: 3
title: Fallback Capacity and Headroom Contracts
concept_id: design-pattern/fallback-capacity-and-headroom-contracts
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- fallback-capacity
- strict-path-headroom
- secondary-incident-prevention
aliases:
- fallback capacity contract
- fallback headroom contract
- strict path headroom
- write-side fallback capacity
- old projection fallback capacity
- fallback burst budget
- fallback circuit breaker
- strict fallback saturation policy
- fallback concurrency budget
- pinned chain reserve sizing
symptoms:
- strict fallback path가 있다며 평균 fallback rate만 보고 reserve를 잡아 incident burst에서 write-side나 old projection이 포화된다
- fallback route를 열어 둔 뒤 DB connection, search thread pool, command p99, breaker threshold를 별도 guardrail로 보지 않는다
- page1-only fallback과 pinned-chain continuation reserve를 구분하지 않아 next-page traffic이 fallback source headroom을 잠식한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/strict-read-fallback-contracts
- design-pattern/projection-freshness-slo-pattern
- design-pattern/projection-lag-budgeting-pattern
next_docs:
- design-pattern/strict-fallback-degraded-ux-contracts
- design-pattern/pinned-legacy-chain-risk-budget
- design-pattern/canary-promotion-thresholds-projection-cutover
linked_paths:
- contents/design-pattern/strict-read-fallback-contracts.md
- contents/design-pattern/strict-pagination-fallback-contracts.md
- contents/design-pattern/strict-fallback-degraded-ux-contracts.md
- contents/design-pattern/pinned-legacy-chain-risk-budget.md
- contents/design-pattern/projection-lag-budgeting-pattern.md
- contents/design-pattern/projection-freshness-slo-pattern.md
- contents/design-pattern/read-model-cutover-guardrails.md
- contents/design-pattern/canary-promotion-thresholds-projection-cutover.md
- contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md
- contents/database/replica-lag-observability-routing-slo.md
confusable_with:
- design-pattern/strict-read-fallback-contracts
- design-pattern/strict-pagination-fallback-contracts
- design-pattern/pinned-legacy-chain-risk-budget
- design-pattern/strict-fallback-degraded-ux-contracts
forbidden_neighbors: []
expected_queries:
- Strict fallback path는 spare capacity가 아니라 reserved headroom contract여야 하는 이유가 뭐야?
- fallback capacity를 평균 rate가 아니라 peak_strict_rps, activation_ratio, burst_multiplier로 sizing해야 하는 이유가 뭐야?
- fallback source가 write-side인지 old projection인지에 따라 command p99, replica lag, breaker guardrail이 달라지는 이유가 뭐야?
- fallback saturation은 freshness SLO의 secondary burn signal이고 breaker-open rate와 함께 봐야 하는 이유가 뭐야?
- pinned legacy chain은 active chain과 next-page request 때문에 별도 reserve sizing이 필요한 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Fallback Capacity and Headroom Contracts playbook으로, strict read fallback을
  임시 우회가 아니라 peak strict RPS, activation ratio, burst multiplier, required concurrency,
  reserved headroom, circuit breaker, degraded UX, owner를 가진 capacity contract로 설계하는 방법을 설명한다.
---
# Fallback Capacity and Headroom Contracts

> 한 줄 요약: strict-path fallback은 단순 우회 경로가 아니라 write-side나 old projection에 미리 예약된 용량 계약이어야 하며, activation ratio, burst multiplier, concurrency, circuit breaker, degraded UX를 함께 고정해야 freshness incident가 overload incident로 번지지 않는다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Strict Fallback Degraded UX Contracts](./strict-fallback-degraded-ux-contracts.md)
> - [Pinned Legacy Chain Risk Budget](./pinned-legacy-chain-risk-budget.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Replica Lag Observability와 Routing SLO](../database/replica-lag-observability-routing-slo.md)

retrieval-anchor-keywords: fallback capacity contract, fallback headroom contract, strict path headroom, write-side fallback capacity, old projection fallback capacity, fallback burst budget, fallback circuit breaker, strict fallback saturation policy, fallback concurrency budget, secondary incident prevention, pinned chain reserve sizing, pinned chain capacity reserve

---

## 핵심 개념

[Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)가 `언제`와 `어디로` 우회할지를 고정한다면, Fallback Capacity and Headroom Contracts는 `그 우회가 실제로 버틸 수 있는가`를 고정한다.

실전 사고는 보통 여기서 난다.

- projection lag가 튀자 strict 요청이 한꺼번에 write-side로 몰린다
- old projection fallback을 열었는데 index refresh/replica가 이미 한계라 2차 지연이 난다
- fallback rate는 SLO 안인데 burst가 짧게 몰리며 breaker 없이 timeout 폭증이 난다
- canary 중에만 괜찮다가 full traffic에서 strict cohort가 겹치며 reserve가 증발한다

즉 fallback은 "있다/없다"보다 다음을 계약으로 남겨야 안전하다.

- 얼마까지 fallback을 받아도 되는가
- 어떤 burst shape까지 버텨야 하는가
- 어느 시점에 breaker를 열고 scope를 줄일 것인가
- fallback도 포화되면 어떤 degraded UX로 내려갈 것인가

### Retrieval Anchors

- `fallback capacity contract`
- `fallback headroom contract`
- `strict path headroom`
- `write-side fallback capacity`
- `old projection fallback capacity`
- `fallback burst budget`
- `fallback circuit breaker`
- `fallback concurrency budget`
- `fallback saturation policy`
- `secondary incident prevention`

---

## 깊이 들어가기

### 1. fallback path는 spare capacity가 아니라 예약된 reserve여야 한다

fallback은 평소 거의 안 쓰더라도 incident 때는 한 번에 몰린다.  
그래서 "평소 CPU 20% 남아 있으니 괜찮다"가 아니라, **strict cohort가 동시 활성화될 때 남겨 둔 reserve가 있는가**로 봐야 한다.

특히 다음 둘을 분리해서 적는 편이 좋다.

| 항목 | 의미 | 왜 분리하나 |
|---|---|---|
| baseline load | fallback source가 평소에도 처리하는 부하 | 이미 소모 중인 용량을 착시 없이 보기 위해 |
| reserved fallback headroom | strict fallback 전용으로 비워 둔 안전 여유 | incident/cutover 시 동시 몰림을 버티기 위해 |

fallback source가 write-side면 commands와 lock contention이 baseline이다.  
old projection이면 일반 read traffic, refresh latency, replica lag가 baseline이다.

### 2. 평균 fallback rate가 아니라 상관된 incident burst로 sizing해야 한다

많은 팀이 `평균 strict fallback rate 0.3%`만 보고 fallback 용량을 가늠한다.  
하지만 실제 사고는 평균이 아니라 상관된 burst로 온다.

- 특정 shard backlog
- projector consumer pause
- cutover route misconfiguration
- hot tenant / hot actor 집중

그래서 최소 산정식은 보통 다음처럼 둔다.

`required_fallback_rps = peak_strict_rps x activation_ratio x burst_multiplier`

각 항목의 의미는 이렇다.

| 항목 | 질문 | 예시 |
|---|---|---|
| `peak_strict_rps` | strict path가 피크에 초당 몇 건 들어오는가 | 주문 직후 상세 120 RPS |
| `activation_ratio` | 한 incident에서 strict cohort 중 몇 %가 fallback으로 전환될 수 있는가 | shard 단위면 0.3, global lag면 1.0 |
| `burst_multiplier` | 1초/10초 창에서 피크가 평균보다 얼마나 튀는가 | 2x ~ 4x |

평균 rate는 SLO 해석에는 유용하지만, capacity sizing에는 `activation_ratio`와 `burst_multiplier`가 더 직접적이다.

### 3. RPS만 보면 부족하고 concurrency와 storage cost까지 환산해야 한다

fallback source가 버티는지는 RPS만으로 끝나지 않는다.

최소한 다음 둘도 함께 본다.

`required_concurrency = required_fallback_rps x p99_fallback_latency_seconds`

| 축 | 왜 필요한가 | 흔한 실수 |
|---|---|---|
| RPS | 초당 요청 수 포화 여부 | 평균 QPS만 보고 짧은 burst를 놓침 |
| concurrency | in-flight connection / thread / pool 포화 여부 | DB connection pool이나 search thread pool을 빼먹음 |
| read cost | query fan-out, row scan, index refresh 비용 | old projection lookup이 사실상 full shard fan-out임을 늦게 발견 |
| lock / contention cost | write-side read가 command latency를 잡아먹는지 | fallback read가 command path tail latency를 악화 |

즉 strict fallback route는 "조회 API 하나 더 둠"이 아니라, **별도의 자원 예산**이다.

### 4. write-side fallback과 old projection fallback은 병목이 다르다

같은 fallback이라도 병목이 다르면 보호 장치도 달라진다.

| fallback source | 주 병목 | 먼저 봐야 할 guardrail | fallback 실패 시 기본 대응 |
|---|---|---|---|
| write-side query port | DB connection, row lock contention, command tail latency | command p99, pool utilization, hot aggregate skew | `processing` UX 또는 actor-scope 축소 |
| old projection | replica lag, index refresh, stale cache, dual-stack 운영비 | refresh latency, replica lag, legacy path error rate | old path 유지 범위 축소, page1-only로 downgrade |
| pending / processing UX | polling 폭증, session pinning, repeated refresh | retry-after 준수율, poll amplification | poll backoff 강화, explicit completion message |

따라서 "fallback source를 둘 다 두자"는 제안은 capacity 관점에서는 더 안전한 게 아니라 **병목 두 종류를 동시에 운영하자**는 의미일 수 있다.

### 5. scale 전에 scope를 좁혀야 reserve가 현실적이 된다

fallback capacity는 인프라 증설만으로 해결하기보다 scope 제한과 함께 문서화하는 편이 낫다.

- actor-owned strict path만 허용
- 생성 직후 3~5초 TTL만 허용
- 상세만 허용하고 검색/목록은 제외
- 목록이라면 `page1-only`와 query fingerprint 제한

이렇게 해야 `required_fallback_rps`가 의미 있는 숫자가 된다.  
scope가 넓으면 reserve를 아무리 계산해도 결국 "전체 read traffic의 숨은 dual stack"이 된다.

### 6. circuit breaker는 freshness 보호 장치가 아니라 2차 장애 차단 장치다

fallback source가 포화될 때 그냥 timeout으로 죽게 두면 strict incident가 시스템 incident로 번진다.  
그래서 fallback path에는 별도의 breaker와 shed rule이 필요하다.

| 신호 | 기본 동작 | 이유 |
|---|---|---|
| utilization 70~80% 접근 | warn + low-priority strict cohort 제한 준비 | reserve가 빠르게 줄고 있음을 조기 감지 |
| timeout / queue wait 급증 | new fallback admissions 제한, 짧은 TTL strict만 유지 | tail latency 악화가 command/read 전체로 번지기 전 차단 |
| utilization 90% 초과 또는 command p99 악화 | breaker open, `processing`/`retry-after`로 degrade | fallback source를 보호하고 2차 장애를 막기 위해 |
| error rate / stale mismatch 동반 | canary freeze 또는 rollback | 단순 과부하가 아니라 correctness risk일 수 있음 |

실무에서는 보통 다음 세 가지를 같이 둔다.

- token bucket 또는 rate limit: burst 흡수량 상한
- in-flight concurrency cap: connection/thread 고갈 방지
- fast-fail breaker: saturation 시 pending UX나 재시도로 즉시 전환

### 7. mode별로 다른 envelope를 가져야 한다

normal, canary, rebuild는 fallback contract를 소비하는 방식이 다르다.

| Mode | 허용 headroom 해석 | 기본 정책 예시 |
|---|---|---|
| normal | strict reserve를 steady-state에서 거의 쓰지 않아야 함 | reserved headroom 50% 이상 유지 |
| canary | mismatch/fallback 상승을 실험 비용으로 보되 reserve 소진은 빠르게 차단 | fallback saturation 70% 접근 시 승격 중지 |
| rebuild / backfill | 일시적 fallback 증가는 허용하되 write-side를 태우지 않도록 scope를 더 좁힘 | actor-only + short TTL + page1-only 강제 |

즉 same route라도 모드가 바뀌면 `allowed activation ratio`, `breaker threshold`, `degraded UX`가 달라질 수 있다.

### 8. fallback saturation은 freshness SLO의 secondary burn 신호다

[Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)에서 fallback rate를 secondary SLI로 본다면, 여기서는 한 걸음 더 나가서 **fallback saturation**도 같이 봐야 한다.

- fallback rate는 primary freshness 압박을 말해 준다
- fallback saturation은 우회 경로 reserve가 얼마나 남았는지 말해 준다

둘은 다른 질문이다.

| 지표 | 질문 | 예시 해석 |
|---|---|---|
| fallback rate | primary projection이 strict 약속을 얼마나 자주 못 지키는가 | 1% -> freshness 부채 증가 |
| fallback utilization | fallback source reserve가 얼마나 차고 있는가 | 85% -> 2차 장애 위험 접근 |
| breaker-open rate | degrade로 내려간 strict 요청이 얼마나 되는가 | 0.2% -> reserve 초과 또는 보호 정책 발동 |

cutover admission이나 rollback trigger는 rate만이 아니라 saturation까지 포함해야 한다.

### 9. old projection을 fallback으로 남길 때도 retirement gate가 필요하다

old projection fallback은 심리적으로 편하지만, 유지 기간이 길어질수록 dual-stack 비용이 쌓인다.

그래서 제거 전에는 최소한 다음을 확인한다.

- strict cohort fallback reserve를 new path + degraded UX만으로 감당 가능한가
- legacy path breaker와 observability가 충분히 검증됐는가
- page1-only / actor-only 축소 후에도 UX가 받아들일 만한가
- rollback window 종료 후 old projection을 다시 살릴 필요가 거의 없는가

즉 old projection fallback은 "있으면 안심"이 아니라, **capacity proof가 끝나면 제거해야 하는 임시 reserve**에 가깝다.

### 10. 최소 계약 패킷을 표로 남겨야 팀 간 해석이 같다

| 필드 | 꼭 적어야 하는 질문 | 예시 |
|---|---|---|
| Fallback ID | 어느 strict path / route의 용량 계약인가 | `orders.detail.write-fallback` |
| Source type | write-side인지 old projection인지 | `WRITE_QUERY_PORT` |
| Peak strict RPS | strict 경로 피크는 얼마인가 | 120 RPS |
| Activation ratio | 한 incident에서 얼마나 동시에 fallback되는가 | 0.5 |
| Burst multiplier | 짧은 창에서 몇 배 튀는가 | 3x |
| Required concurrency | p99 latency 기준 in-flight 몇 개를 버텨야 하나 | 90 |
| Reserved headroom | baseline 제외 후 몇 RPS를 비워 두는가 | 180 RPS |
| Breaker threshold | 언제 open할 것인가 | util 90% or command p99 +20% |
| Degrade action | breaker open 시 무엇을 보여주는가 | `processing` + retry-after 2s |
| Owner | 누가 용량/운영을 승인하는가 | orders team + DB/platform on-call |
| Review cadence | 언제 다시 재측정하는가 | cutover 전, 월간 traffic change 20% 초과 시 |

이 패킷이 있어야 "fallback이 있으니 안전하다"를 실제 운영 문장으로 바꿀 수 있다.

### 11. 하지 말아야 할 것

- 평균 fallback rate만 보고 reserve를 산정하지 말 것
- write-side fallback을 열어 두고 command tail latency를 별도 guardrail 없이 방치하지 말 것
- old projection fallback을 남겨 두면서 refresh/replica 비용을 baseline에서 빼먹지 말 것
- breaker 없이 timeout으로만 과부하를 흡수하려 하지 말 것
- cutover stage에서 fallback saturation을 안 보고 mismatch rate만으로 승격하지 말 것

fallback contract의 목적은 "어떤 경우에도 strict path를 억지로 살린다"가 아니라, **strict path를 살리되 시스템 전체를 무너지게 하지 않는다**는 데 있다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 직후 상세를 write-side로 fallback

- peak strict RPS: 80
- activation ratio: 1.0
- burst multiplier: 2.5
- required fallback RPS: 200

여기서 write query port baseline이 이미 150 RPS를 쓰고 safe capacity가 320 RPS라면 reserve가 부족하다.  
이 경우 선택지는 세 가지다.

- actor scope는 유지하되 strict TTL을 5초에서 2초로 축소
- command와 분리된 read replica/query port를 추가
- reserve가 확보될 때까지 canary/cutover를 중지

### 시나리오 2: 검색 cutover 중 old projection page1 fallback

목록 전체 continuity를 old path로 유지하면 reserve가 급격히 커진다.  
그래서 다음처럼 줄이는 편이 안전하다.

- `page1-only`
- actor-owned shortcut만 허용
- cursor verdict는 `REISSUE`
- saturation 80% 접근 시 old projection fallback을 strict cohort 일부만 유지

핵심은 old projection을 "다시 primary처럼" 쓰지 않는 것이다.

### 시나리오 3: breaker-open 후 degraded UX

fallback route가 열려 있어도 DB pool wait와 command p99가 동시에 악화되면 breaker를 연다.

- strict read 일부는 `processing` 상태로 응답
- `retry-after` 2초 부여
- canary traffic 즉시 동결
- on-call은 lag 원인보다 먼저 fallback saturation 완화에 집중

이 흐름이 없으면 팀은 strict UX를 지키려다 write-side 자체를 무너뜨릴 수 있다.
여기서 `processing`과 `retry-after`를 어떤 user-visible guarantee와 함께 내려야 하는지는 [Strict Fallback Degraded UX Contracts](./strict-fallback-degraded-ux-contracts.md)에서 response-side 기준으로 이어서 본다.

---

## 코드로 보기

### fallback capacity contract

```java
public record FallbackCapacityContract(
    String fallbackId,
    int peakStrictRps,
    double activationRatio,
    double burstMultiplier,
    Duration p99FallbackLatency,
    int baselineRps,
    int safeCapacityRps,
    double breakerOpenUtilization
) {
    public int requiredFallbackRps() {
        return (int) Math.ceil(peakStrictRps * activationRatio * burstMultiplier);
    }

    public int reservedHeadroomRps() {
        return safeCapacityRps - baselineRps;
    }

    public int requiredConcurrency() {
        return (int) Math.ceil(requiredFallbackRps()
            * (p99FallbackLatency.toMillis() / 1000.0));
    }

    public boolean hasReserve() {
        return reservedHeadroomRps() >= requiredFallbackRps();
    }
}
```

### breaker decision

```java
public final class FallbackAdmissionController {
    public Decision decide(
        double utilization,
        Duration commandP99,
        Duration commandP99Budget,
        FallbackCapacityContract contract
    ) {
        if (utilization >= contract.breakerOpenUtilization()
            || commandP99.compareTo(commandP99Budget) > 0) {
            return Decision.DEGRADE_TO_PENDING;
        }
        return Decision.ALLOW_FALLBACK;
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| fallback capacity 계약 없이 strict fallback만 둠 | 구현이 빠르다 | 사고 시 2차 과부하 위험이 크다 | 임시 대응 외에는 비추천 |
| write-side fallback reserve 확보 | correctness 해석이 단순하다 | command path contention 관리가 필요하다 | 핵심 단건 strict path |
| old projection fallback reserve 확보 | 구현 전환 비용이 낮다 | dual-stack 유지비와 legacy drift가 쌓인다 | cutover / rollback window |
| breaker + degraded UX 우선 | 시스템 보호가 쉽다 | 사용자 경험이 일부 희생된다 | reserve가 작거나 burst 변동이 큰 서비스 |

판단 기준은 다음과 같다.

- strict route 계약과 capacity 계약을 분리해서 문서화한다
- reserve는 평균이 아니라 correlated burst 기준으로 산정한다
- RPS만 아니라 concurrency와 command/read contention까지 본다
- saturation 시 breaker-open과 degraded UX를 기본 경로로 둔다
- old projection fallback은 임시 reserve로 보고 제거 기준을 같이 둔다

## 꼬리질문

> Q: fallback rate가 낮으면 capacity proof는 끝난 것 아닌가요?
> 의도: rate와 saturation을 같은 지표로 보는지 확인한다.
> 핵심: 아니다. rate가 낮아도 짧은 burst에서 concurrency나 pool이 먼저 포화될 수 있다.

> Q: write-side와 old projection 둘 다 fallback으로 두면 두 배 안전한가요?
> 의도: route 수가 많을수록 안전하다고 오해하는지 본다.
> 핵심: 아니다. 병목과 observability surface가 두 배가 되므로, activation order와 breaker 정책이 없으면 오히려 복잡성만 늘 수 있다.

> Q: breaker가 열리면 strict contract를 깨는 것 아닌가요?
> 의도: degraded UX도 계약 안에 포함되는지 보는 질문이다.
> 핵심: 아니다. reserve를 초과한 뒤 timeout으로 무너지는 것보다, 명시적 `processing`/`retry-after`로 내려가는 편이 더 강한 운영 계약이다.

## 한 줄 정리

Fallback Capacity and Headroom Contracts는 strict fallback route를 "있으면 쓰는 우회"가 아니라 reserve, burst, breaker, degraded UX까지 포함한 용량 계약으로 바꿔서 2차 장애를 막는 패턴이다.
