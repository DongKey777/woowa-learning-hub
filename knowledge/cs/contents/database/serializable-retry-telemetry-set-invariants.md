---
schema_version: 3
title: Serializable Retry Telemetry for Set Invariants
concept_id: database/serializable-retry-telemetry-set-invariants
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- serializable
- retry-telemetry
- set-invariant
- sqlstate
- observability
aliases:
- serializable retry telemetry
- serializable observability
- retry budget
- retry exhaustion
- sqlstate 40001
- sqlstate 40P01
- set invariant observability
- hot aggregate telemetry
- retry depth histogram
- invariant safety vs availability
symptoms:
- minimum staffing, quota, capacity 같은 set invariant를 SERIALIZABLE로 보호할 때 retry telemetry를 설계해야 해
- 40001 총합만 보고 정상 경합인지 retry storm인지 구분하지 못하고 있어
- safety breach와 availability degradation, contention shape를 서로 다른 panel로 나눠야 해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- database/guard-row-vs-serializable-vs-reconciliation-set-invariants
- database/transaction-retry-serialization-failure-patterns
next_docs:
- database/postgresql-serializable-retry-playbook
- database/range-invariant-enforcement-write-skew-phantom
- database/lock-wait-deadlock-latch-triage-playbook
linked_paths:
- contents/database/guard-row-vs-serializable-vs-reconciliation-set-invariants.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/postgresql-serializable-retry-playbook.md
- contents/database/write-skew-phantom-read-case-studies.md
- contents/database/range-invariant-enforcement-write-skew-phantom.md
- contents/database/hot-row-contention-counter-sharding.md
- contents/database/lock-wait-deadlock-latch-triage-playbook.md
confusable_with:
- database/transaction-retry-serialization-failure-patterns
- database/postgresql-serializable-retry-playbook
- database/guard-row-vs-serializable-vs-reconciliation-set-invariants
forbidden_neighbors: []
expected_queries:
- SERIALIZABLE로 quota나 minimum staffing set invariant를 보호할 때 어떤 retry telemetry를 남겨야 해?
- SQLSTATE 40001이 보인다고 바로 사고가 아니라 안전한 abort일 수도 있다는 말을 어떻게 해석해?
- retry exhausted와 invariant breach를 같은 알람에 섞지 말고 safety와 availability를 나눠야 하는 이유가 뭐야?
- 40001, 40P01, 55P03, lock timeout, unique violation을 retry budget에서 어떻게 분류해?
- top hot key, retry depth histogram, success after retry 지표로 serializable contention을 어떻게 읽어?
contextual_chunk_prefix: |
  이 문서는 serializable retry telemetry를 SQLSTATE 40001/40P01, retry budget, retry exhaustion, safety vs availability, set invariant observability로 다루는 advanced playbook이다.
  minimum staffing, quota contention, retry depth histogram, hot aggregate telemetry 질문이 본 문서에 매핑된다.
---
# Serializable Retry Telemetry for Set Invariants

> 한 줄 요약: minimum staffing이나 quota를 `SERIALIZABLE`로 보호할 때는 `40001` 자체보다, 어떤 SQLSTATE가 retry budget을 태우는지와 언제 안전한 경합이 운영 사고로 바뀌는지를 따로 관측해야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [Guard Row vs Serializable Retry vs Reconciliation for Set Invariants](./guard-row-vs-serializable-vs-reconciliation-set-invariants.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [Write Skew and Phantom Read Case Studies](./write-skew-phantom-read-case-studies.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)

retrieval-anchor-keywords: serializable retry telemetry, serializable observability, retry budget, retry exhaustion, sqlstate 40001, sqlstate 40P01, sqlstate 55P03, lock wait timeout classification, minimum staffing retry alert, quota contention alert, set invariant observability, hot aggregate telemetry, retry depth histogram, conflict ratio, success after retry, deadlock vs serialization failure, invariant safety vs availability

## 핵심 개념

minimum staffing, quota, capacity 같은 set invariant를 `SERIALIZABLE`로 보호하면 DB는 "규칙이 깨질 뻔한 경쟁"을 보통 **abort + retry 신호**로 바꿔 준다.

이때 운영자가 구분해야 하는 건 세 가지다.

1. **안전 신호**: `40001`처럼 DB가 write skew를 막아 준 결과
2. **가용성 신호**: retry budget 소진, tail latency 상승, 사용자 실패율 증가
3. **실제 안전 사고**: `on_call_count = 0`, `actual_qty > capacity` 같은 invariant breach

즉 `40001`이 보인다고 바로 사고가 아니다.  
반대로 `40001`만 보고 "정상 경합이네"라고 넘기면 retry storm, hot aggregate, lock ordering bug를 놓칠 수 있다.

serializable 경로에서는 "실패 건수"보다 아래 질문에 답할 수 있어야 한다.

- 어떤 SQLSTATE가 retryable conflict이고, 어떤 것은 timeout/bug/domain reject인가
- 한 요청이 몇 번까지 다시 시도해도 되는가
- 어느 aggregate key가 retry budget을 대부분 태우는가
- retry는 성공하지만 이미 운영 SLO를 망가뜨리고 있지는 않은가
- 실제 invariant breach는 정말 0건인가

## 먼저 분리할 두 축: safety vs availability

| 축 | 대표 신호 | 해석 |
|---|---|---|
| safety | `actual_qty > capacity`, `on_call_count = 0`, reconciliation mismatch | serializable 보호가 새거나 우회 write가 있다는 뜻이다. 즉시 조사 대상이다 |
| availability | retry depth 증가, retry exhausted, latency p95 상승 | 규칙은 지켰지만 서비스 품질이 악화되고 있다는 뜻이다 |
| contention shape | `40001`, `40P01`, hot key concentration | 왜 budget이 소모되는지 설명해 주는 원인 축이다 |

운영 대시보드와 알람도 이 축을 섞지 않는 편이 좋다.

- safety panel: 실제 invariant breach, reconciliation drift
- availability panel: retry exhausted, user-visible failure, p95/p99 latency
- contention panel: SQLSTATE ratio, top hot key, deadlock vs serialization split

`retry exhausted = 0`이어도 `actual_qty > capacity`가 나오면 safety incident다.  
반대로 `40001`이 1% 있어도 retry 1회 안에 거의 모두 성공하고 latency가 안정적이면 건강한 보호일 수 있다.

## 텔레메트리 계약

serializable 보호 경로는 최소한 attempt 단위로 아래 필드를 남기는 편이 좋다.

- `rule_name`: `minimum_staffing`, `campaign_quota`, `seat_capacity`
- `resource_key_hash`: `shift_id`, `campaign_id` 같은 aggregate key의 raw 값 대신 hash/bucket
- `transaction_name`: admission path 이름
- `db_engine`, `isolation_level`
- `attempt_index`, `max_attempts`
- `sqlstate`, `vendor_code`, `exception_class`
- `retryable`: `true/false`
- `backoff_ms`, `txn_elapsed_ms`, `end_to_end_elapsed_ms`
- `outcome`: `success_initial`, `success_after_retry`, `retry_exhausted`, `domain_reject`, `timeout`, `unknown_commit`

예시:

```json
{
  "event": "serializable_retry",
  "rule_name": "campaign_quota",
  "resource_key_hash": "campaign:5f2a",
  "transaction_name": "claim_coupon",
  "db_engine": "postgresql",
  "isolation_level": "serializable",
  "attempt_index": 2,
  "max_attempts": 3,
  "sqlstate": "40001",
  "vendor_code": null,
  "retryable": true,
  "backoff_ms": 27,
  "txn_elapsed_ms": 41,
  "end_to_end_elapsed_ms": 86,
  "outcome": "retrying"
}
```

핵심은 `40001` 총합만 세지 않는 것이다. 아래 지표를 같이 봐야 운영 해석이 가능하다.

- `attempts_total`
- `retryable_conflicts_total`
- `retry_exhausted_total`
- `success_after_retry_total`
- `retry_depth_histogram`
- `latency_seconds{outcome=...}`
- `top_hot_keys` 또는 log-based top-N aggregate
- `invariant_breach_total`

## SQLSTATE 분류 표

serializable set invariant 경로에서는 "retry 가능한 실패"와 "budget을 늘려도 해결되지 않는 실패"를 섞지 않아야 한다.

| SQLSTATE / 코드 | 대표 엔진 surface | 기본 분류 | retry budget에 포함? | 운영 해석 |
|---|---|---|---|---|
| `40001` | PostgreSQL serialization failure, MySQL deadlock victim(`1213`)이 `40001`로 노출되는 경우 | retryable conflict | 포함 | serializable이 경합을 안전하게 거부한 것이다. 비율과 hot key를 본다 |
| `40P01` | PostgreSQL deadlock detected | retryable but separate | 포함하되 별도 bucket | retry는 가능하지만 lock ordering 문제일 수 있다. `40001`와 합치지 말고 본다 |
| `55P03` | PostgreSQL `NOWAIT`/lock-not-available | conditional retry | 보통 별도 budget | 의도된 non-blocking probe면 정상일 수 있다. 아니면 saturation 신호다 |
| `57014` | PostgreSQL statement timeout / cancel | non-blind-retry | 미포함 | 이미 latency budget을 다 쓴 경우가 많다. blocking/timeout 원인 분석이 우선이다 |
| `HY000` + `1205` | MySQL lock wait timeout | non-blind-retry | 미포함 | serializable conflict라기보다 blocking/saturation에 가깝다 |
| class `23` (`23505`, `23P01`, `23000`) | unique/exclusion/integrity violation | domain or modeling rejection | 미포함 | quota/full/overlap을 constraint로 표현한 결과일 수 있다. retry보다 에러 번역이 중요하다 |
| class `08` | connection exception, commit outcome unknown | idempotent recovery only | 미포함 | blind retry 금지. 결과 조회나 idempotency key 확인이 필요하다 |

운영 팁:

- MySQL 계열은 SQLSTATE보다 vendor errno가 더 설명력이 큰 경우가 많다. `sqlstate`와 `vendor_code`를 같이 저장한다.
- PostgreSQL은 `40001`과 `40P01`를 분리해야 한다. 둘 다 재시도 대상일 수 있지만, 대응 액션이 다르다.
- class `23`을 retry budget에 섞으면 "quota가 찬 정상 거절"과 "serializable 경합"이 같은 알람에 묻힌다.

## Retry budget 설계

retry budget은 횟수만이 아니라 **허용할 지연과 최종 실패율**까지 포함하는 계약이다.

### 1. 동기 admission 경로

예: 당직 해제 버튼, 선착순 쿠폰 claim, 좌석 hold 생성

- 권장: `max_attempts = 3` (초기 1회 + retry 2회)
- backoff: `10ms -> 40ms` 수준의 exponential + jitter
- 추가 지연 budget: 대개 `150~250ms` 안쪽
- 초과 시 outcome: `retry_exhausted`

이 경로는 사용자가 기다리고 있으므로, success rate를 위해 무작정 5~7회까지 늘리면 tail latency가 먼저 망가진다.

### 2. 비동기 job / queue worker

예: quota reclaim, staffing rebalance, periodic recompute

- 권장: `max_attempts = 5`
- backoff: `25ms -> 400ms` 수준의 exponential + jitter
- wall-clock budget: 대개 `2~5s` 이내

비동기라고 budget을 무한대로 두면 worker가 hot key 하나에 매달려 backlog를 만든다.  
job budget도 결국 queue latency budget과 연결된다.

### 3. 운영 해석용 budget 지표

아래 세 수치가 함께 보여야 한다.

| 지표 | 권장 해석 |
|---|---|
| `conflict_ratio = retryable_conflicts_total / attempts_total` | serializable 보호가 얼마나 자주 발동하는가 |
| `success_after_retry_ratio` | 경합은 있었지만 budget 안에서 대부분 회복되는가 |
| `retry_exhausted_ratio` | 실제 사용자/worker 실패로 번지는가 |

실전에서는 아래 식으로 보는 편이 이해하기 쉽다.

- `conflict_ratio`가 높아도 `retry_exhausted_ratio`가 낮고 latency가 안정적이면 아직 건강한 보호
- `conflict_ratio`가 낮아도 특정 hot key가 대부분을 차지하면 곧 폭발할 수 있는 국소 병목
- `retry_exhausted_ratio`가 오르면 budget을 늘릴지보다 트랜잭션 길이, lock order, aggregate model을 먼저 본다

## 권장 알람 임계치

아래 값은 set invariant admission path에 두는 보수적인 시작점이다. 실제 SLO에 맞춰 조정하되, **safety alert와 contention alert를 따로** 건다.

| 신호 | Warning | Critical | 이유 |
|---|---|---|---|
| `conflict_ratio` (`40001` + `40P01`) | 10분 평균 `> 2%` | 10분 평균 `> 5%` | retry budget과 p95 latency가 빠르게 올라가기 시작하는 구간 |
| `retry_exhausted_ratio` on sync path | 5분 평균 `> 0.3%` | 5분 평균 `> 1%` | 사용자 실패가 보이기 시작한다 |
| `retry_exhausted_ratio` on low-QPS staffing admin path | 15분 동안 `>= 3건` | 15분 동안 `>= 10건` 또는 연속 5분 발생 | 원래 경합이 낮아야 하는 경로라 적은 건수도 이상하다 |
| deadlock share (`40P01 / retryable_conflicts`) | `> 20%` | `> 40%` | serializable 충돌보다 lock ordering bug 가능성이 크다 |
| timeout share (`55P03`, `57014`, `1205`) | 5분 평균 `> 0.2%` | 5분 평균 `> 0.5%` | retry가 아니라 blocking/saturation 조치가 필요하다 |
| hot key concentration | 상위 key 1개가 retryable conflict의 `> 25%` | `> 40%` | 모델 재설계나 sharding 후보다 |
| actual invariant breach | 즉시 조사 | 즉시 page | serializable 보호가 실제로 새었거나 우회 write가 있다는 뜻이다 |

권장 해석:

- quota/flash sale처럼 원래 경쟁이 높은 경로는 `conflict_ratio` 자체보다 `retry_exhausted_ratio`와 hot key concentration이 더 중요하다
- minimum staffing 같은 낮은 QPS 경로는 `40001` 몇 건만 반복돼도 배포/락 순서 회귀를 의심할 만하다
- `actual invariant breach`는 volume과 무관하게 별도 critical이다

## 상황별 운영 해석

### 1. `40001`은 많은데 대부분 1회 retry 안에 성공

의미:

- serializable 보호는 정상 동작 중
- 다만 특정 시간대나 aggregate에서 경합이 올라가고 있을 수 있음

운영 액션:

1. top hot key를 본다
2. retry depth p95가 1을 넘는지 본다
3. latency p95가 baseline 대비 2배 이상 뛰면 admission path 분리나 guard row 재모델링을 검토한다

### 2. `40P01` 비중이 높다

의미:

- 단순 serializable 경합보다 lock ordering 문제일 가능성이 크다

운영 액션:

1. path별 statement order를 비교한다
2. 같은 aggregate를 읽는 순서가 path마다 다른지 본다
3. budget 상향보다 canonical lock ordering을 먼저 고친다

### 3. `1205`/`57014`가 늘어난다

의미:

- retry budget을 늘려도 잘 낫지 않는 blocking/saturation 경로

운영 액션:

1. lock wait / statement timeout 원인을 분리한다
2. 오래 잡는 트랜잭션, 외부 호출, 불필요한 read fan-out을 줄인다
3. timeout을 `40001`과 같은 버킷으로 보고 있지 않은지 확인한다

### 4. hot key 하나가 conflict 대부분을 먹는다

의미:

- shift 하나, campaign 하나가 arbitration hotspot이 된 상태

운영 액션:

1. minimum staffing이면 guard row로 내릴 수 있는지 본다
2. quota면 striped guard row, counter shard, ledger projection을 검토한다
3. retry budget 상향은 임시 완화일 뿐이라고 가정한다

## 최소 대시보드 구성

serializable set invariant 운영 대시보드는 아래 네 줄이면 된다.

1. `attempts_total` 대비 `40001`, `40P01`, timeout, class `23` 비율
2. `retry_depth_histogram`과 `success_after_retry_ratio`
3. `retry_exhausted_ratio` + path latency p95/p99
4. `actual invariant breach` + reconciliation mismatch + top hot keys

이 네 줄이 같이 보여야 "정상 보호", "성능 악화", "실제 안전 사고"를 구분할 수 있다.

## 자주 하는 실수

### "`40001`은 모두 정상이라 알람이 필요 없다"

틀리다. `40001`은 safety guard가 작동한 결과일 수 있지만, rate와 retry depth가 올라가면 곧 availability incident가 된다.

### "deadlock도 재시도되니 `40001`과 같은 bucket으로 보면 된다"

틀리다. 둘 다 retry는 가능하지만 `40P01` 증가는 lock ordering bug나 statement mix 회귀를 시사한다.

### "retry exhausted가 없으면 안전도 괜찮다"

틀리다. 우회 write, manual SQL, reconciliation 누락이 있으면 retry 통계와 별개로 실제 invariant breach가 날 수 있다.

### "quota full과 serializable conflict를 같은 실패율로 보면 된다"

틀리다. class `23`/business reject는 정상 정책 결과일 수 있지만, `40001`은 경합 비용이다. 운영 의미가 다르다.

## 꼬리질문

> Q: minimum staffing 경로에서 `40001`이 5분 동안 4건만 나와도 왜 신경 써야 하나요?
> 의도: low-QPS invariant path와 high-QPS quota path의 운영 해석을 구분하는지 확인
> 핵심: 원래 경합이 적어야 하는 경로라면 적은 건수도 lock ordering 회귀나 새 hotspot의 신호일 수 있다

> Q: 왜 `retry_exhausted_ratio`보다 `actual invariant breach`를 더 높은 우선순위로 보나요?
> 의도: 안전 신호와 가용성 신호를 분리하는지 확인
> 핵심: exhausted는 실패-안전일 수 있지만, invariant breach는 실제로 보호가 새었다는 뜻이기 때문이다

> Q: hot key concentration이 높으면 왜 budget을 늘리기보다 모델 재설계를 먼저 보나요?
> 의도: retry와 모델링의 관계를 이해하는지 확인
> 핵심: 한 aggregate가 arbitration surface를 독점하면 retry는 시간을 사는 것뿐이고 근본 병목은 그대로 남기 때문이다

## 한 줄 정리

serializable set invariant 운영의 핵심은 `40001` 자체가 아니라, SQLSTATE를 retryable conflict / timeout / domain reject로 분리하고, retry budget 소모와 실제 invariant breach를 별도 알람으로 보는 것이다.
