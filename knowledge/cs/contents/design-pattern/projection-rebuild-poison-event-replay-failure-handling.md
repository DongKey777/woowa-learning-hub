# Poison Event and Replay Failure Handling in Projection Rebuilds

> 한 줄 요약: projection rebuild 중 poison event나 partial replay failure가 나오면, 무한 재시도보다 분류, 격리, 검증된 체크포인트 재개, sign-off 규칙을 먼저 고정해야 backfill 진행과 cutover 판단을 동시에 지킬 수 있다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Projection Replay Observability and Alerting Pattern](./projection-replay-observability-alerting-pattern.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)
> - [Event Upcaster Compatibility Patterns](./event-upcaster-compatibility-patterns.md)
> - [Event Contract Drift Triage for Rebuilds](./event-contract-drift-triage-rebuilds.md)
> - [Checkpoint / Snapshot Pattern](./checkpoint-snapshot-pattern.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [System Design: Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md)
> - [System Design: Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: projection poison event, replay failure quarantine, projection rebuild retry policy, partial replay failure, replay checkpoint recovery, projection replay signoff, quarantine ledger, poison event retry matrix, rebuild shard recovery, replay gap closure, quarantine growth alert, last verified watermark drift, replay retry budget burn, event contract drift triage, upcaster gap classification, semantic incompatibility replay

---

## 핵심 개념

projection rebuild는 실패가 나면 보통 두 갈래로 갈린다.

- 잠깐 실패했지만 다시 시도하면 되는 경우
- 같은 입력을 다시 먹여도 계속 터지는 경우

여기서 둘을 구분하지 못하면 운영은 둘 다 망가진다.

- transient failure를 너무 빨리 dead-letter로 보내서 진행이 늦어짐
- poison event를 무한 재시도해서 backlog 전체가 멈춤
- 일부 shard만 적용되고 checkpoint가 어정쩡하게 남아 replay gap이 숨겨짐
- "한 번 재시작해서 초록색"만 보고 cutover sign-off를 해 버림

그래서 projection rebuild에서는 **retry 정책**, **quarantine 정책**, **partial failure 복구 규칙**, **sign-off 문장**이 한 묶음이어야 한다.

### Retrieval Anchors

- `projection poison event`
- `projection replay failure`
- `replay quarantine ledger`
- `partial replay failure`
- `last verified watermark`
- `replay retry matrix`
- `projection replay signoff`
- `rebuild gap closure`
- `shard replay recovery`
- `cutover blocked by poison event`

---

## 깊이 들어가기

### 1. retry 전에 failure class를 먼저 고정해야 한다

rebuild 중 실패를 한 종류로 다루면 판단이 흐려진다.

| Failure class | 전형적 예시 | 기본 대응 | cutover 영향 |
|---|---|---|---|
| Transient infra | DB timeout, broker reset, temporary storage throttle | bounded auto-retry + backoff | 장기화되지 않으면 직접 영향 없음 |
| Deterministic code/data bug | 같은 event에서 deserialize 실패, upcaster 누락, unknown enum | 즉시 해당 단위 중지, 원인 분류, fix 후 재개 | open 상태면 readiness red |
| Poison semantic event | 원본 이벤트 의미가 현재 projection 계약으로 해석 불가 | quarantine + owner 지정 + disposition 문서화 | skip 허용 규칙 없으면 cutover 불가 |
| Partial apply / ambiguous checkpoint | row upsert는 일부 반영됐는데 checkpoint 기록 실패 | last verified checkpoint 기준으로 검증 후 재개 | gap 해소 전 sign-off 금지 |

여기서 핵심은 "실패했다"가 아니라 **같은 입력을 다시 넣었을 때 의미가 바뀌는가**다.  
같은 입력, 같은 stack trace, 같은 watermark에서 반복되면 retry보다 분류가 먼저다.

특히 deterministic failure 안에서도 legacy schema drift, upcaster coverage gap, semantic incompatibility는 재개 조건이 다르다.  
이 세분화 기준은 [Event Contract Drift Triage for Rebuilds](./event-contract-drift-triage-rebuilds.md)에서 별도로 본다.

### 2. quarantine는 버리는 작업이 아니라 blast radius를 제한하는 작업이다

poison event를 quarantine할 때는 단순히 dead-letter 큐에 넣고 끝내면 안 된다.  
최소한 다음 필드는 남겨야 한다.

- `rebuild_run_id`
- `projection_name`
- `partition_or_shard`
- `event_id` / `aggregate_id` / `event_type`
- `event_watermark`
- `failure_class`
- `first_seen_at`, `last_seen_at`, `attempt_count`
- `disposition_owner`
- `replay_policy_after_fix` (`retry`, `skip-with-signoff`, `manual-patch-then-replay`)

이 정보가 없으면 나중에 "어떤 이벤트를 왜 건너뛰었는지"를 아무도 설명하지 못한다.

quarantine 단위도 고정해야 한다.

- 단일 event만 고립 가능하면 event 단위 quarantine
- 특정 shard 전체가 깨졌으면 shard 단위 pause
- 이벤트 범위를 특정하기 전이면 range quarantine 후 drill-down

즉 quarantine의 목적은 backlog를 영구 방치하는 게 아니라, **문제가 난 단위를 분리해 나머지 backfill을 계속 밀 수 있게 하는 것**이다.

### 3. retry는 횟수보다 종료 조건이 더 중요하다

retry 정책은 보통 "몇 번까지"만 적는데, rebuild 운영에서는 **언제 자동 retry를 그만둘지**가 더 중요하다.

| 상황 | 권장 정책 | 멈추는 조건 |
|---|---|---|
| 일시적 네트워크/스토리지 오류 | 지수 backoff, 짧은 auto-retry | 동일 shard에서 retry budget 소진 또는 lag reserve 붕괴 |
| deserialize/upcaster 오류 | auto-retry 금지, 즉시 quarantine 후보로 분류 | 첫 재현 시 즉시 중지 |
| projector bug 의심 | code fix 전까지 같은 입력 재시도 금지 | stack trace/fingerprint 확정 시 |
| checkpoint write 실패 | 재시작 전에 last verified watermark 확인 | applied rows와 checkpoint 차이가 설명되지 않을 때 |

운영 기본값은 다음처럼 잡는 편이 안전하다.

- auto-retry는 transient class에만 허용
- deterministic failure는 동일 fingerprint 2회면 auto-retry 중지
- `last_attempted_watermark`와 `last_verified_watermark`를 분리 기록
- ambiguous 상태에서는 "아마 적용됐을 것"으로 checkpoint를 전진시키지 않음

### 4. partial replay failure는 skip보다 gap closure 순서로 다뤄야 한다

가장 위험한 경우는 전체 잡이 죽는 경우보다, **일부만 반영되고 겉으로는 진행된 것처럼 보이는 경우**다.

대표적인 예시는 다음과 같다.

- shard A는 `105000`까지 반영됐는데 shard B는 `104200`에서 멈춤
- row upsert는 성공했지만 checkpoint commit이 실패해 재시작 시 중복/누락 판단이 모호함
- batch 1,000건 중 997건만 저장되고 3건이 실패했는데 진행률은 100%처럼 집계됨

이때 복구 순서는 보통 다음이 더 안전하다.

1. 영향 shard/range를 즉시 freeze한다.
2. `last_verified_watermark`를 읽어 재개 기준점을 되돌린다.
3. 그 이후 구간의 applied row와 dedup ledger를 샘플 검증한다.
4. 누락/중복이 확인되면 gap을 메운 뒤 다시 checkpoint를 전진시킨다.
5. gap list가 0이 되기 전까지 `history backfill complete`를 선언하지 않는다.

핵심은 `last_attempted_watermark`가 아니라 `last_verified_watermark`를 sign-off 기준으로 삼는 것이다.  
시도한 위치와 증명된 위치를 섞으면 partial failure가 readiness 문서에서 사라진다.

### 5. sign-off는 세 종류로 분리해야 해석이 안 흔들린다

실무에서는 sign-off를 하나로 적어 두는 경우가 많지만, rebuild 운영에서는 세 갈래가 더 현실적이다.

| Sign-off 종류 | 질문 | 최소 근거 |
|---|---|---|
| Retry sign-off | fix 후 어디서부터 다시 돌릴 것인가 | failure class, code/data fix 링크, restart watermark, idempotency 확인 |
| Quarantine sign-off | 이 이벤트를 당장 처리하지 않고 넘어가도 되는가 | skip 허용 정책, 영향 범위, compensating path, owner/ETA |
| Cutover sign-off | 이 rebuild 결과로 트래픽을 전환해도 되는가 | quarantine ledger 정리, partial gap 0, parity 재검증, rollback/fallback green |

특히 cutover sign-off는 아래 조건 중 하나라도 남아 있으면 보류하는 편이 맞다.

- unresolved poison event가 있는데 skip 허용 정책이 문서화되지 않음
- partial replay gap이 남아 있는데 blast radius가 미상임
- quarantine 이벤트가 핵심 상태 전이를 포함해 parity 의미를 흔듦
- 재가동 후 parity를 다시 돌리지 않았음

즉 "재시작 후 에러가 안 난다"는 sign-off 근거로 약하다.  
**무엇을 격리했고, 무엇을 다시 돌렸고, 무엇이 아직 미해결인지**가 함께 있어야 한다.

### 6. skip-with-signoff는 예외 경로이지 기본값이 아니다

가끔 poison event를 바로 수정할 수 없어 건너뛰고 싶은 순간이 있다.  
이때도 무조건 금지가 아니라, 허용 조건을 아주 좁게 적는 편이 좋다.

예를 들면 다음 정도다.

- 이벤트가 deprecated feature에만 영향
- downstream에서 누락을 보정하는 별도 reconciliation이 있음
- 해당 aggregate가 cutover parity 샘플에서 명시적으로 제외되고 owner가 승인함

반대로 아래 경우는 보통 skip-with-signoff를 허용하면 안 된다.

- 주문 상태, 결제 상태, 재고 수량처럼 핵심 읽기 의미를 바꾸는 이벤트
- strict screen이 직접 의존하는 projection 필드
- 왜 실패했는지 아직 분류조차 안 된 이벤트

즉 quarantine는 허용될 수 있어도, **skip은 훨씬 더 강한 승인 행위**다.

### 7. readiness 문서에는 open issue 수보다 disposition 상태가 들어가야 한다

단순히 "오픈 이슈 3건"이라고 쓰면 운영 판단에 도움이 약하다.  
rebuild sign-off packet에는 최소한 아래가 같이 보여야 한다.

- `target_watermark`와 `last_verified_watermark`
- shard별 replay gap count
- quarantine event 수와 failure class 분포
- `retrying`, `quarantined`, `fixed-awaiting-rerun`, `accepted-skip` 건수
- parity 재실행 시각과 결과
- strict path fallback rate / backlog reserve / remaining budget
- 최종 승인자와 승인 시각

이렇게 해야 "진행률 99%" 같은 요약 대신 **운영적으로 남은 리스크가 무엇인지**가 보인다.

---

## 운영 의사결정 매트릭스

| 관찰 신호 | 흔한 원인 | 즉시 행동 | sign-off 전 확인 |
|---|---|---|---|
| 같은 event가 3번 연속 deserialize 실패 | upcaster 누락, schema drift | 해당 event quarantine 후보로 분류, shard 진행 중지 | fix 후 fixture replay 성공 여부 |
| 일부 shard만 watermark가 뒤처짐 | shard hotspot, checkpoint write 누락 | lagging shard freeze, gap 범위 계산 | gap 0, shard parity 재확인 |
| batch 완료율은 100%인데 row count가 부족 | partial batch commit, silent skip | batch range 재검증, missing key 샘플링 | missing row 해소, duplicate 여부 점검 |
| 재시작 후 에러는 사라졌지만 fallback rate 상승 | latent data skew, semantic mismatch | cutover 보류, parity 재수집 | strict path 의미 차이 해소 |
| quarantine 건수는 적지만 핵심 상태 이벤트 포함 | business critical event skip | cutover red 유지 | compensating path와 explicit owner 승인 없이는 불가 |

---

## 실전 시나리오

### 시나리오 1: upcaster 누락으로 특정 legacy event가 계속 실패

`OrderPlacedV1`의 오래된 payload에서 새 필수 필드가 없어 deserialize가 계속 실패한다고 해 보자.

- auto-retry로는 해결되지 않는다
- 해당 event는 poison 후보로 quarantine ledger에 기록한다
- upcaster를 보완한 뒤 fixture replay로 재현을 닫는다
- fix 후 `last_verified_watermark`부터 다시 재개한다

여기서 중요한 건 "재시도 횟수"가 아니라 **legacy contract fix가 sign-off packet에 붙었는가**다.

### 시나리오 2: row upsert는 끝났는데 checkpoint commit이 실패

잡은 재시작되지만, 이미 반영된 row 범위를 정확히 모른다면 바로 다음 watermark로 넘기면 안 된다.

- `last_verified_watermark`로 되돌아간다
- 해당 range를 idempotent projector 전제로 재적용한다
- dedup ledger 또는 row version으로 중복 반영이 없는지 확인한다

이 경우 sign-off 포인트는 "에러가 사라졌다"가 아니라 **중복과 누락 둘 다 설명됐다**는 점이다.

### 시나리오 3: 32개 shard 중 1개만 partial replay failure

31개 shard가 녹색이어도 global readiness는 아직 녹색이 아니다.

- shard-local quarantine와 replay gap은 허용될 수 있다
- 하지만 cutover sign-off는 전체 projection 의미를 본다
- lagging shard가 strict path나 상위 query fingerprint에 영향 주면 바로 red다

즉 부분 성공은 운영 진행에는 도움이 되지만, **전환 승인 근거와는 별개**다.

---

## 코드로 보기

### replay failure disposition

```java
public record ReplayFailureDisposition(
    String rebuildRunId,
    String projectionName,
    String shardId,
    long lastVerifiedWatermark,
    long failedWatermark,
    FailureClass failureClass,
    String eventId,
    String owner,
    Disposition disposition
) {}
```

### classifier

```java
public final class ReplayFailureClassifier {
    public FailureClass classify(Throwable error, int repeatedFingerprintCount) {
        if (error instanceof SocketTimeoutException) {
            return FailureClass.TRANSIENT_INFRA;
        }
        if (error instanceof DeserializationException || repeatedFingerprintCount >= 2) {
            return FailureClass.DETERMINISTIC_POISON;
        }
        return FailureClass.AMBIGUOUS_PARTIAL_APPLY;
    }
}
```

### sign-off gate

```java
public boolean readyForCutover(ReplayRunStatus status) {
    return status.openReplayGaps() == 0
        && status.unclassifiedFailures() == 0
        && status.unapprovedSkips() == 0
        && status.parityGreen()
        && status.fallbackReady()
        && status.rollbackReady();
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 무한 재시도 중심 운영 | 구현이 단순하다 | poison event가 전체 backlog를 막는다 | 거의 권장하지 않음 |
| quarantine + bounded retry | blast radius를 줄이고 backfill을 계속 밀 수 있다 | ledger, owner, runbook 관리가 필요하다 | event replay를 자주 하는 read model |
| skip-with-signoff 허용 | 운영 중단을 줄일 수 있다 | 잘못 쓰면 의미 손실을 승인하게 된다 | 영향 범위가 매우 좁고 보정 경로가 명확할 때만 |

판단 기준은 다음과 같다.

- transient와 poison을 같은 retry loop에 넣지 않는다
- checkpoint는 attempted가 아니라 verified 기준으로 전진시킨다
- unresolved quarantine와 partial gap이 있으면 cutover sign-off를 막는다

---

## 꼬리질문

> Q: poison event가 한 건뿐이면 그냥 건너뛰고 cutover해도 되나요?
> 의도: 이벤트 수와 의미 영향도를 구분하는지 본다.
> 핵심: 아니다. 한 건이어도 핵심 상태 전이면 skip은 강한 승인 행위다.

> Q: 재시작 후 에러가 없어졌으면 partial replay failure는 해소된 것 아닌가요?
> 의도: 시도 성공과 검증 완료를 구분하는지 본다.
> 핵심: 아니다. gap closure와 parity 재검증이 있어야 verified 상태다.

> Q: quarantine가 있으면 cutover는 항상 불가능한가요?
> 의도: 절대 금지와 예외 승인 차이를 보는 질문이다.
> 핵심: 기본값은 보류지만, 영향 범위와 compensating path가 명시적으로 승인된 좁은 예외는 가능하다.

## 한 줄 정리

Projection rebuild에서 poison event와 partial replay failure는 "재시작하면 언젠가 된다"로 다루지 말고, failure class 분류, quarantine ledger, verified checkpoint 재개, cutover sign-off 규칙까지 묶어 운영해야 한다.
