---
schema_version: 3
title: Backup, Restore, Disaster Recovery Drill 설계
concept_id: system-design/backup-restore-disaster-recovery-drill-design
canonical: false
category: system-design
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- backup restore
- disaster recovery
- point in time recovery
- snapshot backup
aliases:
- backup restore
- disaster recovery
- point in time recovery
- snapshot backup
- wal shipping
- restore drill
- rpo rto
- backup catalog
- immutable backup
- integrity verification
- cross-region vault
- resilience validation
symptoms:
- Backup, Restore, Disaster Recovery Drill 설계 관련 장애나 마이그레이션 리스크가 발생해 단계별 대응이 필요하다
intents:
- troubleshooting
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/multi-region-active-active-design.md
- contents/system-design/audit-evidence-vault-design.md
- contents/system-design/object-metadata-service-design.md
- contents/system-design/file-storage-presigned-url-cdn-design.md
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/system-design/service-discovery-health-routing-design.md
- contents/system-design/failure-injection-resilience-validation-platform-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Backup, Restore, Disaster Recovery Drill 설계 장애 대응 순서를 알려줘
- backup restore 복구 설계 체크리스트가 뭐야?
- Backup, Restore, Disaster Recovery Drill 설계에서 blast radius를 어떻게 제한해?
- backup restore 운영 리스크를 줄이는 방법은?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Backup, Restore, Disaster Recovery Drill 설계를 다루는 playbook 문서다. 백업과 복구 설계는 데이터를 저장하는 것보다, 원하는 시점과 우선순위로 실제 복원이 가능한지 반복적으로 검증하는 운영 복구 시스템이다. 검색 질의가 backup restore, disaster recovery, point in time recovery, snapshot backup처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Backup, Restore, Disaster Recovery Drill 설계

> 한 줄 요약: 백업과 복구 설계는 데이터를 저장하는 것보다, 원하는 시점과 우선순위로 실제 복원이 가능한지 반복적으로 검증하는 운영 복구 시스템이다.

retrieval-anchor-keywords: backup restore, disaster recovery, point in time recovery, snapshot backup, wal shipping, restore drill, rpo rto, backup catalog, immutable backup, integrity verification, cross-region vault, resilience validation

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Audit Evidence Vault 설계](./audit-evidence-vault-design.md)
> - [Object Metadata Service 설계](./object-metadata-service-design.md)
> - [File Storage / Presigned URL / CDN 설계](./file-storage-presigned-url-cdn-design.md)
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Failure Injection / Resilience Validation Platform 설계](./failure-injection-resilience-validation-platform-design.md)

## 핵심 개념

백업은 "복사본이 있다"는 사실만으로는 의미가 약하다.
실전에서 중요한 질문은 다음이다.

- 언제 시점으로 복구할 수 있는가
- 복구에 얼마나 걸리는가
- 어떤 시스템부터 우선 복구할 것인가
- control plane이 망가져도 복구를 시작할 수 있는가
- 백업이 실제로 깨지지 않았는가

즉, DR은 저장 정책이 아니라 **복원 경로와 연습 절차를 가진 운영 시스템**이다.

## 깊이 들어가기

### 1. Failover와 restore는 다르다

많은 팀이 멀티 리전 failover를 가지고 있으면 DR이 끝났다고 생각한다.
하지만 둘은 다르다.

- **failover**: 이미 준비된 다른 리전으로 트래픽을 넘긴다
- **restore**: 손상되거나 삭제된 데이터를 특정 시점으로 되살린다

리전은 살아 있지만 논리적 삭제나 잘못된 배치가 전체에 복제되면, failover만으로는 해결되지 않는다.

### 2. Capacity Estimation

예:

- 운영 DB 20 TB
- 하루 변경량 800 GB
- object storage 200 TB
- RPO 15분
- 핵심 서비스 RTO 60분

이때 봐야 할 숫자:

- snapshot 생성 주기
- incremental log 보관량
- restore throughput
- cross-region copy 지연
- drill 성공률
- integrity verification 시간

복구 설계는 저장 비용보다 restore 속도와 검증 시간이 병목이 되는 경우가 많다.

### 3. 백업 계층과 카탈로그

보통 복구 가능한 시스템은 다음 계층을 가진다.

- full snapshot
- incremental log 또는 change stream
- backup catalog
- checksum / manifest
- key material reference

catalog가 없으면 "어떤 백업이 어떤 시점과 어떤 스키마에 대응하는가"를 알 수 없다.
즉, 백업 파일보다 메타데이터 관리가 더 중요할 수 있다.

### 4. Immutable backup과 격리된 신뢰 경계

랜섬웨어나 운영자 실수는 production credential을 이미 가진 상태에서 발생할 수 있다.
그래서 다음 원칙이 중요하다.

- backup vault는 production 계정과 분리한다
- delete는 time lock 또는 별도 승인 경로를 둔다
- encryption key와 data catalog를 같은 계정에 두지 않는다
- backup 읽기와 restore 실행 권한을 분리한다

복구 체계 자체가 production과 같은 blast radius 안에 있으면 위기 때 같이 망가진다.

### 5. 복구는 순서가 핵심이다

모든 시스템을 동시에 복원하려고 하면 길을 잃는다.
보통은 다음 순서를 정한다.

1. identity와 secrets
2. control plane 메타데이터
3. 핵심 transaction store
4. derived index와 cache
5. 비핵심 분석 시스템

검색 인덱스나 캐시는 다시 만들 수 있지만, 원장과 계정 데이터는 그렇지 않다.

### 6. Drill은 게임데이가 아니라 정기 검증이다

백업이 있어도 restore를 한 번도 안 해 보면 의미가 없다.
권장 drill 항목:

- 무작위 시점 PITR 복원
- 샘플 row checksum 비교
- 서비스 부팅 가능 여부
- 애플리케이션 smoke test
- 운영자가 실제 runbook대로 복구 가능한지 확인

핵심은 "복구 스크립트가 있다"가 아니라 "반복 가능한가"다.

### 7. 복원 후 정합성 검증

restore가 끝나도 바로 트래픽을 붙이면 위험하다.

검증 항목:

- row count와 checksum
- 핵심 도메인 invariant
- CDC/queue lag 초기화 상태
- service discovery / routing 재등록 여부
- 최근 이벤트 재적용 범위

특히 derived system은 원본을 restore한 뒤 다시 backfill할지, 복제 로그를 재적용할지 판단해야 한다.

## 실전 시나리오

### 시나리오 1: 운영 배치가 잘못되어 대량 논리 삭제 발생

문제:

- 삭제가 정상 트랜잭션으로 commit되어 다른 리전에도 복제된다

해결:

- 오염 시점을 기준으로 PITR restore 후보를 만든다
- 격리된 복구 환경에서 차이를 비교한다
- 필요한 엔티티만 선택 복구하거나 보정 이벤트를 발행한다

### 시나리오 2: 랜섬웨어로 production control plane 손상

문제:

- 운영 계정과 메타데이터가 동시에 망가졌다

해결:

- 분리된 backup vault와 catalog에서 restore를 시작한다
- service discovery와 secrets를 먼저 복구한다
- production credential과 독립된 break-glass 절차를 사용한다

### 시나리오 3: 리전 손실 후 핵심 DB 복원

문제:

- active-active가 아니거나 일부 데이터는 single-writer였다

해결:

- 핵심 DB를 우선 restore한다
- derived index와 cache는 늦게 재구축한다
- external callback과 webhook은 replay-safe하게 재연결한다

## 코드로 보기

```pseudo
function restore(request):
  backup = catalog.findClosest(request.targetTime)
  env = isolatedEnvironment.create()
  restoreSnapshot(env, backup.snapshot)
  applyLogs(env, backup.logsUntil(request.targetTime))
  verifyChecksums(env)
  if request.promote and verificationPassed():
    cutoverTraffic(env)
```

```java
public RestorePlan plan(Instant targetTime) {
    BackupChain chain = backupCatalog.resolve(targetTime);
    return restorePlanner.build(chain);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Snapshot only | 단순하다 | RPO가 커진다 | 중요도가 낮은 시스템 |
| Snapshot + log shipping | PITR이 가능하다 | 운영 복잡도 증가 | 핵심 DB |
| Cross-region replica | failover가 빠르다 | 논리 손상이 같이 복제될 수 있다 | 고가용성 우선 |
| Immutable backup vault | 안전하다 | 접근 절차가 느려질 수 있다 | 높은 보안 요구 |
| Frequent restore drill | 신뢰도가 높다 | 시간과 비용이 든다 | 중요한 프로덕션 |

핵심은 백업이 저장 정책이 아니라 **복원 가능한 상태를 지속적으로 증명하는 운영 계약**이라는 점이다.

## 꼬리질문

> Q: 멀티 리전 replica가 있으면 백업이 덜 중요하지 않나요?
> 의도: 가용성과 복구 차이 이해 확인
> 핵심: 논리 손상과 운영 실수는 replica에도 복제될 수 있어 별도 backup이 여전히 필요하다.

> Q: RPO와 RTO 중 무엇이 더 중요한가요?
> 의도: 복구 목표 수립 감각 확인
> 핵심: 둘 다 중요하지만 도메인마다 허용 손실량과 허용 중단 시간이 다르므로 함께 숫자로 정해야 한다.

> Q: derived index를 같이 restore해야 하나요?
> 의도: source-of-truth 우선순위 이해 확인
> 핵심: 보통 원본 저장소 복구가 먼저이고, derived system은 재구축으로 대체할 수 있다.

> Q: restore drill은 왜 production과 닮은 격리 환경이 필요한가요?
> 의도: runbook 검증의 현실성 이해 확인
> 핵심: 실제 의존성과 성능 병목이 드러나야 drill 결과가 믿을 만하다.

## 한 줄 정리

Backup, restore, disaster recovery drill 설계는 백업 파일을 쌓는 것이 아니라, 원하는 시점과 우선순위로 실제 복원이 가능한지 반복 검증하는 운영 복구 체계를 만드는 일이다.
