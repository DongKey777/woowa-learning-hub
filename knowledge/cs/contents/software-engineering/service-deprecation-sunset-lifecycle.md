---
schema_version: 3
title: Service Deprecation and Sunset Lifecycle
concept_id: software-engineering/service-deprecation-sunset-lifecycle
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- deprecation
- sunset
- service-lifecycle
- consumer-migration
aliases:
- service deprecation sunset lifecycle
- service sunset governance
- tombstone lifecycle
- replacement service migration
- deprecation extension governance
- 서비스 종료 수명주기
symptoms:
- service deprecation을 코드 삭제로만 처리해 남은 consumer, batch job, event topic, dashboard, alert rule을 관측하지 못해
- deprecation notice, migration window, tombstone, hard delete 조건 없이 endpoint를 제거해 소비자 충격이 발생해
- sunset extension과 allowlist가 공식 exception backlog가 아니라 DM이나 개인 시트로 관리돼 retire/absorb 판단이 흐려져
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/api-versioning-contracts-acl
- software-engineering/service-ownership-catalog-boundaries
next_docs:
- software-engineering/deprecation-enforcement-tombstone-guardrails
- software-engineering/compatibility-waiver-governance
- software-engineering/service-portfolio-lifecycle-governance
linked_paths:
- contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
- contents/software-engineering/service-ownership-catalog-boundaries.md
- contents/software-engineering/adr-decision-records-at-scale.md
- contents/software-engineering/incident-review-learning-loop-architecture.md
- contents/software-engineering/service-portfolio-lifecycle-governance.md
- contents/software-engineering/deprecation-enforcement-tombstone-guardrails.md
- contents/software-engineering/backward-compatibility-waiver-consumer-exception-governance.md
- contents/software-engineering/consumer-exception-operating-model.md
- contents/software-engineering/shadow-process-officialization-absorption-criteria.md
confusable_with:
- software-engineering/deprecation-enforcement-tombstone-guardrails
- software-engineering/consumer-exception-model
- software-engineering/service-portfolio-lifecycle-governance
forbidden_neighbors: []
expected_queries:
- service deprecation을 단순 삭제가 아니라 consumer migration과 관측 가능한 sunset lifecycle로 설계하려면 어떻게 해야 해?
- deprecation notice, 신규 사용 차단, tombstone, hard delete를 어떤 순서로 진행해야 안전해?
- endpoint를 내리기 전에 마지막 호출 시각, consumer 식별, dashboard migration을 왜 확인해야 해?
- sunset extension request를 consumer exception backlog와 연결해 retire 또는 absorb 판단하는 기준을 설명해줘
- API는 지웠지만 batch job과 event consumer가 남아 있을 때 service sunset에서 무엇을 더 점검해야 해?
contextual_chunk_prefix: |
  이 문서는 서비스 deprecation을 공지, consumer migration, tombstone, 관측 유지, hard delete 조건으로 관리하는 advanced sunset lifecycle playbook이다.
---
# Service Deprecation and Sunset Lifecycle

> 한 줄 요약: 서비스 deprecation은 오래된 API를 지우는 일이 아니라, 대체 경로와 관측 가능성을 유지한 채 소비자를 안전하게 이동시키는 수명 종료 관리다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)
> - [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)
> - [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)
> - [Consumer Exception Operating Model](./consumer-exception-operating-model.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)

> retrieval-anchor-keywords:
> - service deprecation
> - sunset lifecycle
> - replacement service
> - tombstone
> - migration window
> - consumer notice
> - hard delete
> - backward compatibility
> - retire vs absorb
> - sunset exception path
> - deprecation extension governance
> - sunset allowlist absorb

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Service Deprecation and Sunset Lifecycle](./README.md#service-deprecation-and-sunset-lifecycle)
> - 다음 단계: [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)

## 핵심 개념

서비스 deprecation은 "없애자"가 아니다.
정확히는 **소비자들이 안전하게 떠날 수 있는 종료 절차를 설계하는 것**이다.

대부분의 서비스는 다음 이유로 바로 지우면 안 된다.

- 아직 쓰는 소비자가 있다
- 계약과 데이터가 뒤섞여 있다
- 호출 빈도는 낮아도 중요한 배치가 남아 있다
- 운영 대시보드와 알림이 아직 참조 중이다

즉 sunset은 기능 삭제가 아니라 **책임 있는 철수**다.

---

## 깊이 들어가기

### 1. deprecation은 공지부터 시작한다

좋은 종료는 먼저 알려야 한다.

필요한 것:

- 종료 예정일
- 대체 서비스/경로
- 남은 migration window
- 영향받는 소비자 목록
- 연락 채널

공지 없이 지우면 기술적으로는 깔끔해 보여도, 운영적으로는 사고다.

### 2. sunset은 단계적으로 진행해야 한다

보통 순서는 이렇다.

1. deprecation 공지
2. 신규 사용 차단
3. 기존 소비자 migration
4. read-only 또는 tombstone 모드
5. 최종 종료
6. 데이터/리소스 정리

이 순서는 소비자에게 준비 시간을 주고, 내부 관측을 유지한다.

### 3. deprecated path 주변의 예외 경로는 retire할지 absorb할지 먼저 정해야 한다

서비스 자체는 sunset 대상이어도, 그 주변의 exception path는 두 종류로 나뉜다.

- 이미 exception registry, waiver review, tombstone policy가 있는데 사람들이 slack DM이나 개인 시트로 마감 연장을 처리한다면: 그 bypass는 **retire** 대상이다
- 서비스별 allowlist, extension count, replacement readiness, tombstone reason code를 매번 같은 형태로 따로 적고 있다면: 그 반복 데이터는 **absorb** 대상이다

핵심 질문은 단순하다.

- 공식 경로가 이미 있는데 사람들이 우회하는가 -> retire
- 반복되는 structured data가 공식 registry/gateway에 못 들어가고 있는가 -> absorb

이 기준을 [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)와 같은 언어로 써 두면, sunset governance와 consumer exception review가 서로 다른 말로 같은 문제를 설명하지 않게 된다.
특히 deprecation 연장 request는 [Consumer Exception Operating Model](./consumer-exception-operating-model.md)과 [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)에서 관리하는 exception backlog와 연결해 보는 편이 안전하다.

### 4. 관측 가능성을 먼저 줄이지 말아야 한다

서비스를 내리기 전에 다음을 남겨야 한다.

- 에러 로그
- 호출 통계
- 소비자 식별
- 마지막 요청 시각

이게 없으면 누가 아직 쓰는지 알 수 없다.

### 5. hard delete는 가장 마지막이다

API endpoint를 내리는 것과, backing data를 지우는 것은 다르다.

특히 다음은 더 늦게 지워야 한다.

- 이벤트 토픽
- DB 테이블
- 배치 job
- 대시보드
- 알림 rule

서비스는 코드보다 주변 의존성이 더 오래 남을 수 있다.

### 6. 종료는 ADR과 연결되어야 한다

왜 종료하는지, 무엇이 대체인지, 어떤 조건이 충족되면 지우는지 남겨야 한다.
이 문맥은 [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)와 직접 연결된다.

---

## 실전 시나리오

### 시나리오 1: 낡은 조회 API를 종료한다

조회 API를 새 BFF와 새 contract로 옮겼다면:

- 구 API에 deprecation header를 붙인다
- 소비자 목록을 추적한다
- 일정 기간 후 read-only로 전환한다
- 마지막에 endpoint를 제거한다

### 시나리오 2: 내부 서비스가 더 이상 필요 없다

같은 기능을 제공하는 새 서비스가 안정화되면, 옛 서비스는 tombstone 상태로 바꾸고 호출 차단을 걸 수 있다.
하지만 바로 제거하지 말고 로그와 관측을 남긴다.

### 시나리오 3: 배치와 이벤트가 남아 있다

API는 지웠는데, 배치 job과 이벤트 consumer가 옛 서비스 이름을 바라보는 경우가 많다.
그래서 deprecation은 코드 삭제보다 dependencies cleanup이 더 오래 걸린다.

---

## 코드로 보기

```yaml
deprecation_plan:
  announce: 2026-05-01
  stop_new_consumers: true
  tombstone_after: 30d
  delete_after:
    - consumer_count == 0
    - last_access < 14d
    - dashboards_migrated: true
```

종료 조건이 명시되어야 sunset이 감정이 아닌 절차가 된다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 삭제 | 단순하다 | 소비자 충격이 크다 | 외부 노출이 없고 안전할 때 |
| tombstone 후 삭제 | 안전하다 | 종료가 길어진다 | 소비자가 남아 있을 때 |
| 장기 sunset | 리스크가 낮다 | 유지비가 든다 | 중요한 서비스일 때 |

deprecation은 지우는 속도가 아니라 **안전하게 떠나게 하는 능력**으로 평가해야 한다.

---

## 꼬리질문

- 누가 종료 결정을 승인하는가?
- 소비자 migration이 끝났는지 어떻게 확인하는가?
- 읽기/쓰기 경로는 언제 분리할 것인가?
- tombstone 상태를 운영 도구가 이해하는가?
- 남은 sunset side path는 retire 대상인가, absorb 대상인가?

## 한 줄 정리

서비스 deprecation은 서비스 삭제가 아니라, 소비자 migration과 관측 가능성을 유지한 채 수명을 정리하는 lifecycle 관리다.
