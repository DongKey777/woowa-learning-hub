# Zero-Downtime Schema Migration Platform 설계

> 한 줄 요약: 무중단 스키마 마이그레이션 플랫폼은 애플리케이션 버전 차이, 대규모 backfill, 읽기/쓰기 경로의 호환성 문제를 제어해 서비스 중단 없이 데이터 구조를 바꾸는 운영 시스템이다.
>
> 문서 역할: 이 문서는 migration / replay / cutover cluster 안에서 **호환성 창과 migration control plane**을 설명하는 deep dive다.

retrieval-anchor-keywords: zero downtime schema migration, expand and contract, online ddl, backfill, shadow read, compatibility window, migration control plane, cutover, schema evolution, throttled backfill, dual write, read path cutover, dual read compare, deploy rollback safety, contract phase, cleanup gate, point of no return, database security bridge, backfill verification, cdc gap repair, repair first soak

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Change Data Capture / Outbox Relay 설계](./change-data-capture-outbox-relay-design.md)
> - [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Distributed Scheduler 설계](./distributed-scheduler-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Consistency Repair / Anti-Entropy Platform 설계](./consistency-repair-anti-entropy-platform-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)
> - [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)
> - [Database: CDC Gap Repair, Reconciliation, and Rebuild Boundaries](../database/cdc-gap-repair-reconciliation-playbook.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](../design-pattern/projection-rebuild-backfill-cutover-pattern.md)
> - [Event Upcaster Compatibility Patterns](../design-pattern/event-upcaster-compatibility-patterns.md)

## 이 문서 다음에 보면 좋은 설계

- 실제 데이터 이동은 [Change Data Capture / Outbox Relay 설계](./change-data-capture-outbox-relay-design.md)와 함께 봐야 한다.
- backfill / replay 운영은 [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)로 이어진다.
- 검증 기반 승격은 [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md), [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)로 이어진다.
- database authority 이동이 identity claim/capability rollout과 같이 묶이면 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md), [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md), [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)를 함께 봐야 release gate가 닫힌다.
- old column, old route, compatibility layer를 언제 제거할지는 [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)까지 이어서 봐야 rollback 경계가 선명해진다.

## 핵심 개념

스키마 변경은 `ALTER TABLE` 한 줄로 끝나지 않는다.
실전에서는 다음이 동시에 움직인다.

- DB schema
- 애플리케이션 읽기/쓰기 코드
- 캐시와 검색 인덱스 projection
- CDC payload와 consumer schema
- 운영 중인 오래된 바이너리 버전

그래서 무중단 마이그레이션의 핵심은 DDL 자체보다 **호환성 창을 운영하는 제어 절차**다.

## 깊이 들어가기

### 1. expand and contract가 기본이다

가장 안전한 기본 패턴은 다음과 같다.

1. 새 필드나 새 테이블을 추가한다
2. 애플리케이션이 old/new 둘 다 읽을 수 있게 만든다
3. backfill을 수행한다
4. 새 쓰기 경로를 활성화한다
5. 충분한 검증 후 old 필드를 제거한다

즉, "추가 후 전환 후 제거" 순서를 지키는 것이 중요하다.
바로 rename하거나 타입을 바꾸면 롤백 경로가 사라진다.

### 2. Capacity Estimation

예:

- 20억 row 테이블
- 평균 row 크기 700 bytes
- 정상 트래픽 시 쓰기 QPS 8천
- replica lag 허용치 5초

이때 migration이 보는 숫자는 다음이다.

- backfill rows/sec
- write amplification
- lock hold time
- replica lag
- storage headroom
- cutover 검증 시간

대용량 migration은 성공률보다 "언제 throttling 해야 하는가"가 더 중요하다.

### 3. migration control plane

실전에서는 migration마다 수동 스크립트를 돌리면 실패한다.
보통은 다음 상태를 가진 control plane이 필요하다.

```text
PLANNED
 -> EXPAND_APPLIED
 -> BACKFILL_RUNNING
 -> DUAL_READ_VERIFYING
 -> CUTOVER_READY
 -> CONTRACT_PENDING
 -> DONE
```

이 상태 머신이 있어야 누가 어디까지 했는지, 롤백 시 어디로 돌아가야 하는지 추적할 수 있다.

### 4. Backfill은 별도 제품처럼 다뤄야 한다

DDL보다 더 위험한 것은 데이터 backfill이다.

문제:

- 대량 scan이 primary를 흔든다
- secondary index 유지 비용이 급증한다
- downstream CDC와 indexer가 과부하된다

대응:

- chunk 단위 backfill
- tenant 또는 shard별 rate limit
- replica lag 기반 auto throttle
- checkpoint 저장 후 중단/재개

이 부분은 [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)와 운영 모델이 많이 닮아 있다.

### 5. 호환성 창을 명시해야 한다

무중단 migration은 "새 코드가 배포되면 끝"이 아니다.
현실에는 다음이 같이 존재한다.

- 아직 롤링 업데이트 중인 구버전 인스턴스
- stale cache를 들고 있는 worker
- 오래된 payload를 재처리하는 consumer
- 재시작 전까지 old schema를 기대하는 배치

그래서 설계 문서에 다음을 적어야 한다.

- old write 허용 기간
- dual write 필요 여부
- dual read fallback 규칙
- old column 삭제 가능 시점

가능하다면 dual write 자체를 피하고, 하나의 writer와 projection bridge를 유지하는 편이 운영 리스크가 더 낮다.

### 6. 검증은 shadow read와 집계 비교가 핵심이다

새 구조가 맞는지 확인하는 방법:

- old/new 값을 동시에 읽어 비교
- 샘플링 shadow read
- checksum 또는 aggregate count 비교
- 비즈니스 invariant 검증

예를 들어 금액 합계, 상태 전이 수, 고유 건수 같은 집계가 맞지 않으면 cutover를 미뤄야 한다.
읽기 경로 자체가 크게 바뀌는 migration이라면 shadow read를 넘어 실제 traffic shadowing과 canary cutover를 같이 설계하는 편이 안전하다.
그리고 응답 의미가 복잡한 경우에는 raw compare 대신 semantic dual-read verification 규칙을 따로 가져가는 편이 false positive를 줄인다.

### 7. 롤백은 contract 전까지만 쉽다

많은 팀이 rollback을 "배포만 되돌리면 된다"고 생각한다.
하지만 이미 새 컬럼에만 쓰기 시작했거나 old 필드를 삭제했다면 되돌리기 어렵다.

원칙:

- destructive step은 가장 마지막에 둔다
- delete 대신 tombstone 기간을 둔다
- cutover와 cleanup을 분리한다
- 장애 시 old path로 되돌리는 kill switch를 마련한다

그리고 contract 전에 anti-entropy scan이나 targeted repair로 new path 데이터를 검증할 수 있어야, cleanup 이후의 surprise를 줄일 수 있다.

## 실전 시나리오

### 시나리오 1: nullable 컬럼을 필수 컬럼으로 전환

문제:

- 기존 row에는 값이 없다
- 신규 API는 필수값을 기대한다

해결:

- nullable 컬럼을 먼저 추가한다
- 애플리케이션은 fallback 규칙을 가진다
- backfill 완료 후 validation을 거쳐 not null 제약을 늦게 건다

### 시나리오 2: JSON blob을 정규화 테이블로 분리

문제:

- 기존 payload가 커서 질의가 느리다
- 여러 소비자가 blob 구조에 의존한다

해결:

- 새 정규화 테이블을 추가한다
- dual write 기간을 둔다
- shadow read로 old/new 결과를 비교한다
- 안정화 후 old blob 의존을 제거한다

### 시나리오 3: shard key 전환

문제:

- 기존 shard key가 hot partition을 만든다
- 전체 재배치가 필요하다

해결:

- 새 shard mapping을 control plane에서 버전 관리한다
- background copy와 change capture를 조합한다
- cutover 전후 read routing 규칙을 분리한다

## 코드로 보기

```pseudo
function migrateUsers():
  applyExpandDDL()
  while backfill.hasNextChunk():
    chunk = backfill.nextChunk()
    migrateChunk(chunk)
    if replicaLagTooHigh():
      throttle()
  enableDualReadVerification()
  if verificationPassed():
    switchWritesToNewSchema()
```

```java
public MigrationStep next(MigrationState state) {
    return switch (state) {
        case PLANNED -> MigrationStep.APPLY_EXPAND;
        case EXPAND_APPLIED -> MigrationStep.START_BACKFILL;
        case BACKFILL_RUNNING -> MigrationStep.VERIFY_DUAL_READ;
        default -> MigrationStep.NOOP;
    };
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Big bang migration | 빠르다 | 실패 시 장애 폭이 크다 | 작은 테이블, 내부 시스템 |
| Expand and contract | 안전하다 | 시간이 오래 걸린다 | 대부분의 실서비스 |
| Dual write | cutover가 쉽다 | write path 복잡도 증가 | 구조 전환이 큰 경우 |
| Shadow read verify | 정합성 확인이 좋다 | 추가 read 비용 | 중요한 도메인 데이터 |
| Online DDL tool | 락 위험을 줄인다 | 운영 학습 비용 | 대형 테이블 변경 |

핵심은 schema migration이 DB 작업이 아니라 **애플리케이션, 데이터, 운영 절차를 함께 조율하는 배포 시스템**이라는 점이다.

## 꼬리질문

> Q: rename column을 바로 하면 왜 위험한가요?
> 의도: backward compatibility 창 이해 확인
> 핵심: 구버전 애플리케이션과 재처리 중인 consumer가 즉시 깨질 수 있다.

> Q: backfill이 DDL보다 더 위험할 수 있는 이유는?
> 의도: 운영 부하 감각 확인
> 핵심: 장시간 scan과 write amplification이 실시간 트래픽을 흔들기 때문이다.

> Q: dual read는 언제 필요한가요?
> 의도: cutover 검증 전략 이해 확인
> 핵심: old/new 구조 결과를 비교해 새 경로의 정확성을 확인할 때 유용하다.

> Q: rollback은 어디까지 쉬운가요?
> 의도: destructive step 순서 이해 확인
> 핵심: old path를 유지하는 contract 이전까지가 상대적으로 쉽고, 삭제 후에는 급격히 어려워진다.

## 한 줄 정리

Zero-downtime schema migration 플랫폼은 expand and contract, throttled backfill, compatibility window, 검증 절차를 묶어 서비스 중단 없이 데이터 구조를 바꾸는 운영 제어 체계다.
