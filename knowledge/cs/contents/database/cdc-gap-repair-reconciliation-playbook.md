# CDC Gap Repair, Reconciliation, and Rebuild Boundaries

> 한 줄 요약: CDC 장애 뒤의 핵심은 connector를 다시 켜는 것이 아니라, 어느 구간이 비었는지 확인하고 replay·backfill·recompute 중 어떤 수리 경계를 택할지 빠르게 결정하는 것이다.

**난이도: 🔴 Advanced**

관련 문서:

- [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)
- [CDC Backpressure, Binlog/WAL Retention, and Replay Safety](./cdc-backpressure-binlog-retention-replay.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)
- [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)
- [Read Repair와 Failover Reconciliation](./read-repair-reconciliation-after-failover.md)
- [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md)
- [Projection Rebuild, Backfill, and Cutover Pattern](../design-pattern/projection-rebuild-backfill-cutover-pattern.md)
- [Event Upcaster Compatibility Patterns](../design-pattern/event-upcaster-compatibility-patterns.md)
- [Historical Backfill / Replay Platform 설계](../system-design/historical-backfill-replay-platform-design.md)
- [Replay / Repair Orchestration Control Plane 설계](../system-design/replay-repair-orchestration-control-plane-design.md)
- [Reconciliation Window / Cutoff Control 설계](../system-design/reconciliation-window-cutoff-control-design.md)

retrieval-anchor-keywords: cdc gap repair, cdc reconciliation, replay boundary, bounded repair fence, replay cutoff, connector outage recovery, binlog gap, wal gap, rebuild boundary, projection repair, replay verification, checksum repair, repair manifest

## 핵심 개념

CDC 파이프라인이 멈추거나 로그를 놓치면 다음 질문이 바로 생긴다.

- gap이 실제로 생겼는가
- 생겼다면 어느 시점부터 어느 projection이 틀렸는가
- replay로 메울 수 있는가
- source scan/backfill이 필요한가
- 그냥 전체 rebuild가 더 빠른가

운영에서 중요한 것은 "수리한다"는 말 자체가 너무 넓다는 점이다.  
CDC repair는 보통 다음 세 단계로 나뉜다.

1. gap boundary 확인
2. 손상 범위(scope) 확인
3. repair fence와 cutoff 결정
4. repair 방식 선택

즉 recovery는 connector restart보다 **repair boundary selection**에 더 가깝다.

## 깊이 들어가기

### 1. 먼저 "지연"과 "실제 gap"을 구분해야 한다

lag가 커도 로그가 아직 남아 있고 offset이 이어지면 gap은 아닐 수 있다.  
반대로 connector가 살아 있어도 offset 점프, schema mismatch, DLQ 누락 때문에 실제 gap이 생길 수 있다.

구분 질문:

- source offset이 연속적인가
- sink checkpoint가 source history와 이어지는가
- 특정 테이블/tenant만 누락됐는가
- consumer dedup 테이블과 checkpoint가 서로 일치하는가

즉 repair는 "늦었다"가 아니라 **"무엇이 빠졌는가"를 증명**하는 것부터 시작한다.

### 2. repair boundary는 시간보다 도메인 범위로 자르는 편이 낫다

장애가 14:00~14:30에 있었다고 해서 항상 그 시간대 전체를 다시 흘리면 되는 것은 아니다.

더 좋은 경계:

- 특정 tenant
- 특정 aggregate type
- 특정 bucket/day
- 특정 event sequence 범위

이렇게 잘라야:

- blast radius가 줄고
- 검증이 쉬워지며
- 중복 처리 비용도 줄어든다

즉 시간 구간은 힌트일 뿐, repair unit은 보통 **도메인 단위 또는 projection 단위**가 된다.

### 3. bounded repair는 lower/upper fence를 명시해야 한다

repair 범위를 잘랐더라도 "어디까지가 이번 수리의 세계인가"를 닫지 않으면 검증이 흔들린다.

보통 필요한 것:

- lower fence: 처음 suspect한 offset, timestamp, bucket
- upper fence: repair 시작 시점에 고정한 high watermark
- live write policy: repair 중 계속 흘릴지, stale read로 돌릴지, correction queue로 뺄지
- closed window policy: 마감된 기간이면 silent overwrite 대신 correction-only로 보낼지

즉 repair boundary는 시작점만이 아니라 **끝점과 우회 정책까지 포함한 bounded repair contract**여야 한다.

### 4. replay, backfill, recompute는 서로 다른 수리 방식이다

대표적인 세 가지 repair 방식:

- replay
  - 로그나 DLQ에서 동일 이벤트를 다시 흘린다
  - 이벤트 dedup이 잘 돼 있을 때 강하다
- source backfill
  - 원본 테이블을 읽어 projection을 다시 맞춘다
  - CDC gap이 길거나 로그 손실이 있을 때 필요하다
- recompute
  - summary/read model을 아예 재계산한다
  - 집계형 projection에는 더 단순하고 안전할 수 있다

실무에서는 "뭐가 더 정교한가"보다 **projection 성격에 맞는 repair primitive**를 고르는 게 중요하다.

### 5. summary projection은 이벤트 replay보다 bucket rebuild가 나을 때가 많다

예를 들어 일별 집계가 틀렸다면 모든 이벤트를 다시 replay하는 것보다:

- 영향받은 날짜 bucket을 invalidation 하고
- source of truth에서 다시 계산하는 편이
- 더 빠르고 검증 가능할 수 있다

반대로 search index나 read model처럼 row-level projection은 bounded replay가 더 자연스러울 수 있다.

즉 CDC repair는 파이프라인 하나가 아니라, **projection 유형별 repair 전략 모음**으로 봐야 한다.

### 6. repair 전에 freeze할 것과 계속 흘릴 것을 나눠야 한다

장애 뒤 즉시 모든 flow를 다시 돌리면 오히려 진실원이 흐려질 수 있다.

구분해야 할 것:

- 새 이벤트는 계속 받아도 되는가
- 손상된 projection만 잠시 stale 표시할 것인가
- repair 중 사용자 read를 fallback source로 보낼 것인가
- repair queue와 live queue를 분리할 것인가

이 결정이 없으면 repair 작업이 실시간 traffic과 섞이며 tail latency와 중복 side effect를 키운다.

### 7. 검증 없는 repair는 또 다른 drift를 만든다

repair 뒤에 꼭 남겨야 할 검증:

- source count vs projection count
- sample diff
- aggregate checksum
- tenant/bucket 단위 completeness check

특히 "이벤트를 다시 넣었으니 맞겠지"는 위험하다.  
repair는 write이기도 하므로, 결과 검증 없이는 drift를 더 키울 수 있다.

## 실전 시나리오

### 시나리오 1. Debezium connector가 40분 멈췄다가 재시작

binlog/WAL retention 안이면 replay가 가능할 수 있다.

우선순위:

- gap boundary 확인
- source offset 연속성 확인
- search/read model sink의 dedup 안전성 확인
- upper fence 고정과 live write 분리
- bounded replay 실행

### 시나리오 2. retention을 넘겨 일부 로그가 유실됨

이 경우는 replay만으로는 복구가 안 된다.

대응:

- 영향을 받은 aggregate/tenant 범위 계산
- source backfill 또는 projection rebuild
- repair 중 stale 표시와 freshness 메타데이터 노출
- close된 window는 correction-only 정책 검토

### 시나리오 3. 집계 대시보드만 틀리고 상세 데이터는 맞음

이때는 전체 CDC를 건드리기보다:

- 영향 bucket invalidation
- summary recompute
- summary drift 검증

이 더 안전하다.

## 코드로 보기

```sql
CREATE TABLE cdc_repair_job (
  job_id BIGINT PRIMARY KEY,
  projection_name VARCHAR(100) NOT NULL,
  repair_mode VARCHAR(30) NOT NULL,
  scope_start VARCHAR(255) NOT NULL,
  scope_end VARCHAR(255) NOT NULL,
  source_low_watermark VARCHAR(255) NOT NULL,
  source_high_watermark VARCHAR(255) NOT NULL,
  cutoff_policy VARCHAR(30) NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

```sql
CREATE TABLE projection_repair_checkpoint (
  projection_name VARCHAR(100) PRIMARY KEY,
  last_verified_source_position VARCHAR(255) NOT NULL,
  last_repaired_at TIMESTAMP NOT NULL
);
```

```java
switch (repairMode) {
    case REPLAY -> replayEvents(scope);
    case BACKFILL -> backfillFromSource(scope);
    case RECOMPUTE -> recomputeProjection(scope);
}
verifyProjection(scope);
```

핵심은 repair 코드를 하나 만드는 것이 아니라, 어떤 projection이 어떤 repair mode를 지원하는지 미리 정해 두는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| bounded replay | 가장 자연스럽고 빠를 수 있다 | dedup과 로그 보존에 의존한다 | 로그가 남아 있고 sink가 replay-safe할 때 |
| bounded replay + correction-only | 마감된 window를 안전하게 다룬다 | correction 경로를 따로 설계해야 한다 | billing, settlement, summary close 이후 |
| source backfill | 로그 손실에도 복구 가능하다 | source scan 부하가 크다 | gap이 길거나 retention을 놓쳤을 때 |
| bucket recompute | 집계 수리에 강하다 | 세밀한 row-level projection엔 안 맞는다 | summary/dashboard drift |
| full rebuild | 상태를 명확히 다시 맞춘다 | 비용과 시간이 크다 | projection이 단순하고 데이터량이 감당될 때 |

## 꼬리질문

> Q: CDC repair에서 가장 먼저 해야 할 일은 무엇인가요?
> 의도: restart보다 gap boundary 파악을 우선하는지 확인
> 핵심: 지연인지 실제 누락인지 구분하고 repair 범위를 먼저 증명해야 한다

> Q: 왜 모든 경우에 replay가 정답이 아닌가요?
> 의도: projection 유형별 repair 차이를 아는지 확인
> 핵심: 로그 유실, dedup 부재, summary 성격에 따라 backfill이나 recompute가 더 안전할 수 있다

> Q: repair 후 무엇을 검증해야 하나요?
> 의도: 운영 수리의 마감 조건을 아는지 확인
> 핵심: count, checksum, sample diff, scope completeness 같은 source-to-projection 검증이 필요하다

## 한 줄 정리

CDC gap repair의 본질은 connector 복구가 아니라, 손상 범위를 도메인 단위로 자르고 projection 성격에 맞는 replay·backfill·recompute 경계를 선택해 검증까지 끝내는 것이다.
