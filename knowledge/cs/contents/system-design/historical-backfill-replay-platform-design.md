# Historical Backfill / Replay Platform 설계

> 한 줄 요약: historical backfill과 replay 플랫폼은 과거 데이터를 대규모로 다시 처리하되, live traffic을 보호하고 중복 side effect를 억제하면서 결과를 검증 가능한 형태로 재생성하는 운영 실행 시스템이다.

retrieval-anchor-keywords: historical backfill, replay platform, reprocessing, bootstrap, replay cursor, watermark, side effect suppression, derived data rebuild, shadow backfill, throttled replay, checkpoint resume, repair replay, correction rebuild, replay campaign

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Change Data Capture / Outbox Relay 설계](./change-data-capture-outbox-relay-design.md)
> - [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
> - [Streaming Analytics Pipeline 설계](./streaming-analytics-pipeline-design.md)
> - [Distributed Scheduler 설계](./distributed-scheduler-design.md)
> - [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
> - [Event Bus Control Plane 설계](./event-bus-control-plane-design.md)
> - [Consistency Repair / Anti-Entropy Platform 설계](./consistency-repair-anti-entropy-platform-design.md)
> - [Stateful Stream Processor State Store / Checkpoint Recovery 설계](./stateful-stream-processor-state-store-checkpoint-recovery-design.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](../design-pattern/projection-rebuild-backfill-cutover-pattern.md)
> - [Event Upcaster Compatibility Patterns](../design-pattern/event-upcaster-compatibility-patterns.md)
> - [Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)
> - [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](../language/java/json-null-missing-unknown-field-schema-evolution.md)

## 핵심 개념

실전 시스템은 시간이 지나면 반드시 "다시 돌려야 하는" 순간이 온다.

- 검색 인덱스를 새 스키마로 다시 구성
- 과금 규칙을 바꾼 뒤 지난 사용량 재계산
- 버그 수정 후 derived projection 재생성
- 분석 파이프라인 지연 구간 재처리

이때 backfill과 replay를 평소 데이터 경로와 같은 방식으로 실행하면 live traffic이 무너지거나, side effect가 중복 발생한다.
그래서 별도 플랫폼이 필요하다.

## 깊이 들어가기

### 1. backfill, replay, bootstrap은 다르다

비슷해 보이지만 목적이 다르다.

- **bootstrap**: 새 consumer나 새 저장소를 처음 채움
- **backfill**: 과거 전체 또는 일부 데이터를 다시 계산
- **replay**: 기존 이벤트를 같은 순서/규칙으로 재적용

이 차이를 무시하면 checkpoint, 순서 보장, side effect 처리 규칙이 꼬인다.

### 2. Capacity Estimation

예:

- 원본 이벤트 500억 건
- 평균 이벤트 800 bytes
- 재처리 목표 24시간
- live 트래픽과 같은 cluster를 공유

이때 봐야 할 숫자:

- replay throughput
- source scan QPS
- checkpoint 저장 간격
- target write amplification
- live traffic 보호 한도
- 검증 샘플링 시간

평상시 처리량보다 "얼마나 천천히 돌려도 운영을 망치지 않는가"가 더 중요한 경우가 많다.

### 3. Control plane과 execution plane 분리

좋은 replay 시스템은 다음을 분리한다.

- 어떤 범위를 재처리할지 결정하는 control plane
- 실제 worker가 읽고 쓰는 execution plane

control plane이 관리해야 할 것:

- source 범위
- tenant 또는 shard 대상
- target sink
- dry-run 여부
- rate limit
- checkpoint와 resume 정책

이런 메타데이터가 없으면 운영자가 셸 히스토리로 replay를 관리하게 된다.

### 4. Side effect suppression

가장 위험한 부분이다.
재처리 작업이 원래 운영 side effect를 다시 발생시키면 안 된다.

예:

- 과거 주문 이벤트 replay가 고객에게 알림을 다시 보냄
- 결제 event backfill이 외부 PG에 재호출됨
- webhook redrive가 상대 시스템에 중복 요청을 날림

대응:

- replay mode를 명시한다
- side effect sink를 stub 또는 noop 처리한다
- idempotency key namespace를 분리한다
- derived projection만 갱신하는 별도 consumer를 둔다

### 5. Checkpoint와 watermark

대규모 backfill은 한 번에 끝나지 않는다.
그래서 다음이 필요하다.

- source cursor 또는 primary key checkpoint
- 대상별 watermark
- chunk 단위 성공/실패 기록
- 재시작 시 resume 전략

이 구조가 있어야 멈췄다가 다시 시작해도 어디부터 이어갈지 알 수 있다.

### 6. Validation과 cutover

재처리 결과는 만들기보다 검증이 더 어렵다.

검증 방식:

- row count / aggregate count 비교
- 샘플링 diff
- checksum
- shadow query
- old/new 결과 동시 조회

검증이 끝나기 전까지는 old 결과와 new 결과를 동시에 유지하는 편이 안전하다.
그리고 drift를 고치는 것이 목적이라면 full replay 대신 suspect 범위만 targeted repair로 처리하는 편이 blast radius가 더 작을 수 있다.

### 7. Live traffic 보호

backfill worker는 보통 "더 빨리" 돌리고 싶어진다.
하지만 운영 시스템은 다음 이유로 throttling이 더 중요하다.

- DB scan이 primary를 압박
- 검색 색인이 merge cost로 흔들림
- queue backlog가 실시간 작업을 밀어냄
- cache churn이 발생

그래서 replay 플랫폼은 자체 rate limit, tenant fairness, pause/resume 기능을 갖는 편이 좋다.

## 실전 시나리오

### 시나리오 1: 검색 인덱스 재구축

문제:

- analyzer 변경으로 전체 문서를 다시 색인해야 한다

해결:

- 새 index version을 만든다
- backfill worker는 tenant shard 단위로 천천히 재색인한다
- live indexing은 기존 경로로 계속 받고, 경계 구간은 dedup한다

### 시나리오 2: 과금 규칙 변경 후 지난 사용량 재계산

문제:

- 이미 청구된 사용량 기록과 새로운 계산 규칙을 비교해야 한다

해결:

- dry-run replay로 차이를 계산한다
- ledger correction event만 별도 생성한다
- 외부 청구나 고객 알림은 재실행하지 않는다

### 시나리오 3: 스트리밍 분석 파이프라인 복구

문제:

- 특정 기간 checkpoint 손상으로 집계가 틀어졌다

해결:

- 영향 구간만 replay 범위로 잡는다
- live window와 겹치는 구간은 watermark 기준으로 합친다
- old/new aggregate를 샘플링 비교한다

## 코드로 보기

```pseudo
function runReplay(job):
  cursor = checkpoint.load(job.id) or job.startCursor
  while cursor < job.endCursor:
    batch = source.read(cursor, limit=job.batchSize)
    transformed = transform(batch, mode=job.mode)
    sink.write(transformed)
    checkpoint.save(job.id, batch.lastCursor)
    throttleIfNeeded()

function transform(batch, mode):
  if mode == "DERIVED_ONLY":
    disableExternalSideEffects()
  return projector.apply(batch)
```

```java
public void execute(ReplayJob job) {
    ReplayCursor cursor = checkpointRepository.loadOrStart(job.id());
    replayWorker.run(job, cursor);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Ad-hoc script | 빠르다 | 재현성과 검증이 약하다 | 작은 일회성 작업 |
| Dedicated replay platform | 운영 안전성이 높다 | 구축 비용이 든다 | 재처리가 잦은 플랫폼 |
| Full replay | 정확하다 | 비용과 시간이 크다 | 규칙 전면 변경 |
| Partial backfill | 빠르다 | 영향 범위 판단이 어렵다 | 구간이나 tenant 한정 오류 |
| Dry-run comparison | 안전하다 | 두 경로를 유지해야 한다 | 금전/정산/권한 관련 변경 |

핵심은 backfill과 replay가 배치 작업이 아니라 **과거 데이터를 다시 흘려도 운영 사고를 만들지 않도록 통제하는 실행 플랫폼**이라는 점이다.

## 꼬리질문

> Q: replay와 retry는 어떻게 다른가요?
> 의도: 재처리 스코프 차이 이해 확인
> 핵심: retry는 개별 실패 처리이고, replay는 과거 범위를 다시 흘리는 운영 작업이다.

> Q: 왜 side effect suppression이 중요하나요?
> 의도: 재처리 시 외부 영향 이해 확인
> 핵심: 과거 이벤트를 다시 계산하는 것과 외부 세상에 다시 반영하는 것은 다르기 때문이다.

> Q: live traffic과 backfill worker를 왜 분리하나요?
> 의도: 운영 보호 감각 확인
> 핵심: 재처리 부하가 실시간 사용자 경로를 압박하지 않도록 경계가 필요하다.

> Q: replay 결과를 어떻게 믿을 수 있나요?
> 의도: 검증 전략 이해 확인
> 핵심: checksum, aggregate diff, shadow query 같은 비교 절차가 있어야 한다.

## 한 줄 정리

Historical backfill과 replay 플랫폼은 과거 데이터를 다시 처리하면서도 live 시스템과 외부 side effect를 보호하고, checkpoint와 검증 절차로 결과를 신뢰할 수 있게 만드는 운영 실행 체계다.
