# Software Engineering (소프트웨어 공학)

> 한 줄 요약: 초심자는 이 README를 용어 백과사전이 아니라, "지금 막힌 질문에 맞는 primer를 고르는 시작 지도"로 읽으면 된다.

**난이도: 🔴 Advanced**

> 작성자 : [장주섭](https://github.com/wntjq68), [이세명](https://github.com/3people)

관련 문서:

- [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md)
- [Junior Backend Roadmap](../../JUNIOR-BACKEND-ROADMAP.md)
- [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md)

<details>
<summary>Table of Contents</summary>

- [빠른 탐색](#빠른-탐색)
- [초심자 오해 FAQ 미니 블록](#초심자-오해-faq-미니-블록)
- [테스트 용어 한 줄 비교](#테스트-용어-한-줄-비교)
- [같은 예시로 보는 `첫 테스트 선택 -> seam 분리`](#같은-예시로-보는-첫-테스트-선택---seam-분리)
- [Beginner 30-Minute Entry Subset](#beginner-30-minute-entry-subset)
- [Beginner 10-Minute Follow-up Branches](#beginner-10-minute-follow-up-branches)
- [Backend Delivery and Observability Foundations Primer](#backend-delivery-and-observability-foundations-primer)
- [10분 분기 고르기 미니 self-check](#10분-분기-고르기-미니-self-check)
- [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge)
- [입문 이후: catalog로 넘어가는 기준](#입문-이후-catalog로-넘어가는-기준)
- [레거시 primer](#레거시-primer)
- [최신 설계 / 거버넌스 catalog](#최신-설계--거버넌스-catalog)
- [보조 primer](#보조-primer)
- [명령형 프로그래밍 vs 선언형 프로그래밍](#명령형-프로그래밍-vs-선언형-프로그래밍)
- [함수형 프로그래밍](#함수형-프로그래밍)
- [객체지향 프로그래밍](#객체지향-프로그래밍)
- [SOLID Failure Patterns](#solid-failure-patterns)
- [우테코 백엔드 미션 선행 개념 입문](#우테코-백엔드-미션-선행-개념-입문)
- [Mission Review Vocabulary Primer](#mission-review-vocabulary-primer)
- [Common-Confusion Wayfinding Notes](#common-confusion-wayfinding-notes)
- [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](#읽기-좋은-코드-레이어-분리-테스트-피드백-루프-입문)
- [계층형 아키텍처 기초](#계층형-아키텍처-기초)
- [Service 계층 기초](#service-계층-기초)
- [테스트 전략 기초](#테스트-전략-기초)
- [SOLID 원칙 기초](#solid-원칙-기초)
- [DTO, VO, Entity 기초](#dto-vo-entity-기초)
- [예외 처리 기초](#예외-처리-기초)
- [Architecture and Layering Fundamentals](#architecture-and-layering-fundamentals)
- [Ports and Adapters Beginner Primer](#ports-and-adapters-beginner-primer)
- [Message-Driven Adapter Example](#message-driven-adapter-example)
- [Batch Job Scope In Hexagonal Architecture](#batch-job-scope-in-hexagonal-architecture)
- [Batch Partial Failure Policies Primer](#batch-partial-failure-policies-primer)
- [Batch Run Result Modeling Examples](#batch-run-result-modeling-examples)
- [Batch Idempotency Key Boundaries](#batch-idempotency-key-boundaries)
- [Bulk Idempotency Keys For Named Contracts](#bulk-idempotency-keys-for-named-contracts)
- [Batch Recovery Runbook Bridge](#batch-recovery-runbook-bridge)
- [Bulk Port vs Per-Item Use Case Tradeoffs](#bulk-port-vs-per-item-use-case-tradeoffs)
- [saveAll/sendAll Port Smells and Safer Alternatives](#saveallsendall-port-smells-and-safer-alternatives)
- [True Bulk Contracts and Partial Failure Results](#true-bulk-contracts-and-partial-failure-results)
- [Adapter Bulk Optimization Without Port Leakage](#adapter-bulk-optimization-without-port-leakage)
- [Testing Named Bulk Contracts](#testing-named-bulk-contracts)
- [HTTP Coalescing Failure Mapping](#http-coalescing-failure-mapping)
- [Webhook and Broker Boundary Primer](#webhook-and-broker-boundary-primer)
- [Hexagonal Testing Seams Primer](#hexagonal-testing-seams-primer)
- [Inbound Adapter Test Slices Primer](#inbound-adapter-test-slices-primer)
- [Inbound Adapter Testing Matrix](#inbound-adapter-testing-matrix)
- [Outbox and Message Adapter Test Matrix](#outbox-and-message-adapter-test-matrix)
- [Repository Interface Contract Primer](#repository-interface-contract-primer)
- [Persistence Follow-up Question Guide](#persistence-follow-up-question-guide)
- [Repository Naming Smells Primer](#repository-naming-smells-primer)
- [Repository, DAO, Entity](#repository-dao-entity)
- [DAO vs Query Model Entrypoint](#dao-vs-query-model-entrypoint)
- [Persistence Adapter Mapping Checklist](#persistence-adapter-mapping-checklist)
- [DataJpaTest DB 차이 가이드](#datajpatest-db-차이-가이드)
- [JPA Batch Config Pitfalls](#jpa-batch-config-pitfalls)
- [Repository Fake Design Guide](#repository-fake-design-guide)
- [Aggregate Persistence Mapping Pitfalls](#aggregate-persistence-mapping-pitfalls)
- [Persistence Model Leakage Anti-Patterns](#persistence-model-leakage-anti-patterns)
- [JPA Lazy Loading and N+1 Boundary Smells](#jpa-lazy-loading-and-n1-boundary-smells)
- [Query Model Separation for Read-Heavy APIs](#query-model-separation-for-read-heavy-apis)
- [Same-DB Query Repository Vs Separate Read Store](#same-db-query-repository-vs-separate-read-store)
- [Bulk Helper Ports vs Query Model Separation](#bulk-helper-ports-vs-query-model-separation)
- [Helper Snapshot Bloat Vs Response DTO Separation](#helper-snapshot-bloat-vs-response-dto-separation)
- [API 설계와 예외 처리](#api-설계와-예외-처리)
- [409 vs 422 선택 기준 짧은 가이드](#409-vs-422-선택-기준-짧은-가이드)
- [테스트 전략과 테스트 더블](#테스트-전략과-테스트-더블)
- [캐시, 메시징, 관측성](#캐시-메시징-관측성)
- [DDD, Hexagonal Architecture, Consistency Boundary](#ddd-hexagonal-architecture-consistency-boundary)
- [DDD Bounded Context Failure Patterns](#ddd-bounded-context-failure-patterns)
- [Event Sourcing, CQRS Adoption Criteria](#event-sourcing-cqrs-adoption-criteria)
- [Domain Event, Outbox, Inbox](#domain-event-outbox-inbox)
- [Clean Architecture vs Layered Architecture, Modular Monolith](#clean-architecture-vs-layered-architecture-modular-monolith)
- [Monolith to MSA Failure Patterns](#monolith-to-msa-failure-patterns)
- [Technical Debt Refactoring Timing](#technical-debt-refactoring-timing)
- [Feature Flags, Rollout, Dependency Management](#feature-flags-rollout-dependency-management)
- [Deployment Rollout, Rollback, Canary, Blue-Green](#deployment-rollout-rollback-canary-blue-green)
- [Strangler Fig Migration, Contract, Cutover](#strangler-fig-migration-contract-cutover)
- [API Versioning, Contract Testing, Anti-Corruption Layer](#api-versioning-contract-testing-anti-corruption-layer)
- [Anti-Corruption Layer Integration Patterns](#anti-corruption-layer-integration-patterns)
- [API Contract Testing, Consumer-Driven](#api-contract-testing-consumer-driven)
- [Contract Drift Detection and Rollout Governance](#contract-drift-detection-and-rollout-governance)
- [Modular Monolith Boundary Enforcement](#modular-monolith-boundary-enforcement)
- [Module API DTO Patterns](#module-api-dto-patterns)
- [ArchUnit Brownfield Rollout Playbook](#archunit-brownfield-rollout-playbook)
- [Shared Module Guardrails](#shared-module-guardrails)
- [Feature Flag Cleanup and Expiration](#feature-flag-cleanup-and-expiration)
- [Idempotency, Retry, Consistency Boundaries](#idempotency-retry-consistency-boundaries)
- [Branch by Abstraction, Feature Flag, Strangler Fig](#branch-by-abstraction-feature-flag-strangler-fig)
- [Technology Radar and Adoption Governance](#technology-radar-and-adoption-governance)
- [Build vs Buy, Exit Cost, Integration Governance](#build-vs-buy-exit-cost-integration-governance)
- [Configuration Governance and Runtime Safety](#configuration-governance-and-runtime-safety)
- [Service Template Trade-offs](#service-template-trade-offs)
- [Service Bootstrap Governance](#service-bootstrap-governance)
- [Lead Time, Change Failure, and Recovery Loop](#lead-time-change-failure-and-recovery-loop)
- [Data Migration Rehearsal, Reconciliation, Cutover](#data-migration-rehearsal-reconciliation-cutover)
- [Team Cognitive Load and Boundary Design](#team-cognitive-load-and-boundary-design)
- [Non-Functional Requirements as Budgets](#non-functional-requirements-as-budgets)
- [Prototype, Spike, and Productionization Boundaries](#prototype-spike-and-productionization-boundaries)
- [Migration Wave Governance and Decision Rights](#migration-wave-governance-and-decision-rights)
- [Cross-Service NFR Budget Negotiation](#cross-service-nfr-budget-negotiation)
- [Decision Revalidation and Supersession Lifecycle](#decision-revalidation-and-supersession-lifecycle)
- [Operational Readiness Drills and Change Safety](#operational-readiness-drills-and-change-safety)
- [Architectural Governance Operating Model](#architectural-governance-operating-model)
- [Migration Carrying Cost and Cost of Delay](#migration-carrying-cost-and-cost-of-delay)
- [Platform Control Plane and Delegation Boundaries](#platform-control-plane-and-delegation-boundaries)
- [Platform Scorecards](#platform-scorecards)
- [Service Portfolio Lifecycle Governance](#service-portfolio-lifecycle-governance)
- [Architecture Council and Domain Stewardship Cadence](#architecture-council-and-domain-stewardship-cadence)
- [Migration Stop-Loss and Scope Reduction Governance](#migration-stop-loss-and-scope-reduction-governance)
- [Platform Policy Ownership and Override Governance](#platform-policy-ownership-and-override-governance)
- [Service Split, Merge, and Absorb Evolution Framework](#service-split-merge-and-absorb-evolution-framework)
- [Team APIs and Interaction Modes in Architecture](#team-apis-and-interaction-modes-in-architecture)
- [Change Ownership Handoff Boundaries](#change-ownership-handoff-boundaries)
- [Service Criticality Tiering and Control Intensity](#service-criticality-tiering-and-control-intensity)
- [Service Deprecation and Sunset Lifecycle](#service-deprecation-and-sunset-lifecycle)
- [Backward Compatibility Waivers and Consumer Exception Governance](#backward-compatibility-waivers-and-consumer-exception-governance)
- [Consumer Exception Registry Templates](#consumer-exception-registry-templates)
- [Consumer Exception Operating Model](#consumer-exception-operating-model)
- [Deprecation Enforcement, Tombstone, and Sunset Guardrails](#deprecation-enforcement-tombstone-and-sunset-guardrails)
- [Rollout Guardrail Profiles, Auto-Pause, and Manual Resume](#rollout-guardrail-profiles-auto-pause-and-manual-resume)
- [Incident Feedback to Policy and Ownership Closure](#incident-feedback-to-policy-and-ownership-closure)
- [Policy as Code Adoption Order and Sequencing](#policy-as-code-adoption-order-and-sequencing)
- [Policy as Code Rollout and Adoption Stages](#policy-as-code-rollout-and-adoption-stages)
- [Override Burn-Down and Exemption Debt](#override-burn-down-and-exemption-debt)
- [Support SLA and Escalation Contracts](#support-sla-and-escalation-contracts)
- [Shadow Process Detection Signals](#shadow-process-detection-signals)
- [Shadow Process Catalog and Retirement](#shadow-process-catalog-and-retirement)
- [Shadow Process Catalog Entry Schema](#shadow-process-catalog-entry-schema)
- [Shadow Review Packet Template](#shadow-review-packet-template)
- [Shadow Packet Automation Mapping](#shadow-packet-automation-mapping)
- [Shadow Review Outcome Template](#shadow-review-outcome-template)
- [Shadow Forum Escalation Rules](#shadow-forum-escalation-rules)
- [Shadow Catalog Lifecycle States](#shadow-catalog-lifecycle-states)
- [Shadow Catalog Review Cadence Profiles](#shadow-catalog-review-cadence-profiles)
- [Shadow Lifecycle Scorecard Metrics](#shadow-lifecycle-scorecard-metrics)
- [Temporary Hold Exit Criteria](#temporary-hold-exit-criteria)
- [Manual Path Ratio Instrumentation](#manual-path-ratio-instrumentation)
- [Mirror Lag SLA Calibration](#mirror-lag-sla-calibration)
- [Shadow Candidate Promotion Thresholds](#shadow-candidate-promotion-thresholds)
- [Threshold Override Governance](#threshold-override-governance)
- [Shadow Promotion Snapshot Schema Fields](#shadow-promotion-snapshot-schema-fields)
- [Break-Glass Path Segmentation](#break-glass-path-segmentation)
- [Emergency Misclassification Signals](#emergency-misclassification-signals)
- [Break-Glass Reentry Governance](#break-glass-reentry-governance)
- [Shadow Retirement Proof Metrics](#shadow-retirement-proof-metrics)
- [Shadow Retirement Scorecard Schema](#shadow-retirement-scorecard-schema)
- [Shadow Catalog Reopen and Successor Rules](#shadow-catalog-reopen-and-successor-rules)
- [Tombstone Response Template and Consumer Guidance](#tombstone-response-template-and-consumer-guidance)
- [Policy Candidate Backlog Scoring and Priority](#policy-candidate-backlog-scoring-and-priority)
- [Consumer Exception State Machine and Review Cadence](#consumer-exception-state-machine-and-review-cadence)
- [Override Burn-Down Review Cadence and Scorecards](#override-burn-down-review-cadence-and-scorecards)
- [Support Operating Models: Self-Service, Office Hours, On-Call](#support-operating-models-self-service-office-hours-on-call)
- [Shadow Process Officialization and Absorption Criteria](#shadow-process-officialization-and-absorption-criteria)
- [Consumer Exception Registry Quality and Automation](#consumer-exception-registry-quality-and-automation)
- [애자일 개발 프로세스](#애자일-개발-프로세스)

</details>

## 질의응답: 요구사항/검증

## 한 줄 정리

초심자는 이 README에서 막힌 질문 문구를 그대로 검색해 첫 primer 1개를 고르고, 그 문서의 다음 한 걸음 링크로만 확장하면 된다.

## 한 줄 정리

초심자는 이 README에서 막힌 질문 문구를 그대로 검색해 첫 primer 1개를 고르고, 그 문서의 다음 한 걸음 링크로만 확장하면 된다.

---

retrieval-anchor-keywords: software engineering readme, 처음 백엔드 미션 뭐부터, 코드리뷰 용어 정리, 가독성 이슈 분기, controller/service/repository 구조, 서비스 레이어 뭐하는 곳, dto vs vo vs entity 차이, 예외 어디서 잡나요, 첫 테스트 선택표, 어디부터 읽어야 하나, 레이어 설계, 운영/배포 감각, beginner software engineering path, question based starter table

## 빠른 탐색

이 `README`는 프로그래밍 패러다임 primer와 아키텍처/거버넌스 deep dive를 함께 모아 둔 **navigator 문서**다.

처음에는 용어를 많이 외우기보다, "한 변경을 어디서 설명하고 어디서 검증할지"를 먼저 잡는 편이 훨씬 쉽다.

아래 `필수`/`선택` 배지는 문서 자체의 절대 난이도보다, **초심자가 지금 바로 알아야 하는 용어 부담**을 먼저 표시한다.

| 배지 | 뜻 | 언제 읽으면 좋나 |
|---|---|---|
| `필수` | 초심자가 초반 PR/미션에서 반복해서 만나는 용어 | 첫 30~60분 안에 먼저 읽는다. |
| `선택` | 지금 막힌 질문이 있을 때 여는 확장 용어 | `필수`를 훑은 뒤 필요한 것만 고른다. |

계층형/Service 입문 경로는 `계층형 아키텍처 기초 -> Service 계층 기초`로 한 번 훑고, 각 문서 안에서는 `before/after -> 흔한 오해와 함정` 순서로 왕복하며 읽으면 첫 구현 동선이 더 빨리 잡힌다.

## Beginner Starter Quick Path

| 60분 starter step | 먼저 답할 질문 | 문서 |
|---|---|---|
| 1 | "가독성 이슈 분기: 코드가 읽히지 않을 때 어디부터 고치지?" | [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md) `필수` |
| 2 | "Controller/Service/Repository 구조는 어떻게 나누지?" (같은 주문 생성 예시로 before/after + 문서 상단 10초 기준 + 검증/트랜잭션 self-check + Service vs Domain 규칙 위치 짧은 before/after + `existsBy...` 같은 Repository 조회 검증 안티패턴 before/after + 각 문서에서는 `before/after -> 흔한 오해와 함정` 순서로 읽게 하는 왕복 힌트 + `Service를 바꿨으면 무조건 @SpringBootTest인가?`를 끊어 주는 FAQ + Service를 읽은 직후 바로 `첫 테스트 선택표`로 넘어가게 돕는 "읽고 바로 다음 한 걸음" 브리지) | [계층형 아키텍처 기초](./layered-architecture-basics.md) `필수` → [Service 계층 기초](./service-layer-basics.md) `필수` → [테스트 전략 기초](./test-strategy-basics.md#첫-테스트-선택표-변경-1건-기준) |
| 3 | "첫 테스트 선택표: 이번 변경의 첫 테스트는 무엇부터 쓰면 되지?" (`Service 계층 기초`에서 넘어온 초심자를 위해 문서 상단에 `Service에서 바뀐 것 -> 같은 이름의 선택표 행` 브리지를 먼저 두고, 그다음 5문항 Yes/No 체크리스트와 본문 선택표를 같은 용어로 1:1 연결) | [테스트 전략 기초](./test-strategy-basics.md) `필수` (문서 상단 5문항 Yes/No 체크리스트를 본문 선택표 앞 5개 행과 같은 용어로 1:1 맞춰 30초 자가진단 후 바로 같은 라벨을 다시 찾게 돕고, `보안 규칙 자체가 변경인가?` 분기로 MVC 계약 테스트와 security-focused 테스트를 초반에 가르고, `@WebMvcTest`/`@DataJpaTest` 최소 템플릿, 외부 API 재시도 분기를 이름만으로 읽는 Given-When-Then 네이밍 예시, `401/403` 혼동을 줄이는 `addFilters=false`/테스트 전용 보안 설정 입문 패턴, before/after 사례, "실패 먼저 재현 -> 최소 테스트 1개" 미니 시나리오 2개, `@WebMvcTest` 검증 실패 응답의 `field/message` assertion 복붙 예시까지 바로 연결) |
| 4 | "DTO vs VO vs Entity 차이, 예외 어디서 잡나요?" | [DTO, VO, Entity 기초](./dto-vo-entity-basics.md) `필수` (문서 상단의 `request DTO -> service command -> entity 저장` 1분 표로 첫 구현 흐름을 먼저 잡고 읽기 시작), [예외 처리 기초](./exception-handling-basics.md) `필수` |

## Beginner Starter Manifest

- 🟢 Beginner 입문 문서 (Junior 로드맵 starter):
  - 아래 10개 링크 목록은 README 안의 canonical starter manifest다. beginner 점검 스크립트는 이 블록만 파싱하면 되도록 유지한다.
  - <!-- beginner-starter-manifest:start -->
  - [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md) `필수` - root/roadmap에서 내려온 뒤 `Java -> HTTP -> MVC -> 저장 경계` 4레인으로 먼저 고정하는 entry bridge
  - [Mission Review Vocabulary Primer](./mission-review-vocabulary-primer.md) `필수`
  - [Common-Confusion Wayfinding Notes](./common-confusion-wayfinding-notes.md) `선택`
  - [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md) `필수`
  - [계층형 아키텍처 기초](./layered-architecture-basics.md) `필수`
  - [Service 계층 기초](./service-layer-basics.md) `필수` - Service 로직 변경이 곧바로 `@SpringBootTest`를 뜻하지 않는다는 beginner FAQ와 첫 테스트 연결 포함
  - [테스트 전략 기초](./test-strategy-basics.md) `필수` - `Service 계층 기초`를 읽은 직후 같은 주문 생성 흐름을 `첫 테스트 선택표`로 바로 잇는 다음 문서
  - [SOLID 원칙 기초](./solid-principles-basics.md) `선택`
  - [DTO, VO, Entity 기초](./dto-vo-entity-basics.md) `필수`
  - [예외 처리 기초](./exception-handling-basics.md) `필수`
  - <!-- beginner-starter-manifest:end -->

## Beginner Starter QA Gates

- Beginner starter 공통 형식 점검 기준 (`qa-content-software-engineering-00012`):
  - 한 줄 멘탈 모델 -> before/after 비교 -> 흔한 오해와 함정 순으로 첫 읽기 동선을 맞춘다.
  - 운영/심화 내용은 starter 본문 중심이 아니라 관련 문서 링크로 확장한다.
  - `필수`만 먼저 읽어도 첫 PR 용어는 따라갈 수 있게 두고, `선택`은 막힌 질문이 생겼을 때만 펼친다.

- Beginner starter 공통 형식 자동 점검 (`qa-content-software-engineering-00028`):
  - 대상: 위 `beginner-starter-manifest` 블록의 10개 문서
  - 점검 항목: 멘탈 모델 섹션, 비교 섹션(`before/after`, `비교표`, `한눈 비교` 같은 동등 표현 허용), 오해/혼동 정리 섹션(`흔한 오해`, `오해 교정`, `혼동 FAQ` 같은 변형 허용)
  - 실행: `python3 knowledge/cs/contents/software-engineering/check_beginner_starter_sections.py`
  - 목적: README starter 목록을 단일 manifest로 유지해 하드코딩 목록 없이도 초심자용 primer의 "개념 한 줄 -> 비교 -> 오해 교정" 동선 회귀를 PR 전에 잡는다.

- Beginner ladder 링크 스모크 테스트 (`qa-bridge-00084`):
  - 대상: 루트 `README`, `JUNIOR-BACKEND-ROADMAP`, [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md)
  - 점검 항목: beginner-safe `primer -> 다음 한 걸음` 링크와 root/roadmap reverse-link anchor
  - 실행: `python3 knowledge/cs/rag/check_beginner_ladder_links.py`
  - 목적: safe-next-step 링크 드리프트로 초심자 entry ladder가 어긋나는 회귀를 PR 전에 잡는다.

## Beginner Persistence Quick Path

- Beginner 경계/영속성 질문형 빠른 경로 (문서 이름보다 질문 중심으로 읽기):
  - [1) Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md) `필수` — "`Repository Interface Contract Primer`부터 `Persistence Model Leakage Anti-Patterns`까지를 한 질문형 결정표로 묶어, 지금 막힌 지점이 계약/이름/조회 분리/매핑/누수 중 무엇인지부터 고르게 돕는다."
  - [2) Module API DTO Patterns](./module-api-dto-patterns.md) `선택` — "모듈 경계를 넘는 DTO는 어디까지 공개할까?"
  - [3) Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) `선택` — "JPA/ORM 세부가 서비스 코드로 새고 있지 않은가?"
  - [4) Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) `선택` — "도메인 모델과 영속 모델 매핑이 어디서 끝나는가?"
  - [5) Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md) `선택` — "성능 최적화가 유스케이스 계약까지 오염시키지 않았는가?"

## 초심자 오해 FAQ 미니 블록

먼저 용어부터 외우기보다, **"이 코드는 요청을 받는가, 일을 조립하는가, 저장하는가?"**를 먼저 묻는 편이 덜 헷갈린다.

| 자주 헷갈리는 질문 | 먼저 잡을 짧은 답 |
|---|---|
| `Layered Architecture`와 `Service Layer`는 같은 말인가? | 아니다. 전자는 구조 지도, 후자는 그 지도 안의 한 칸이다. |
| Controller는 얇은데 Service가 너무 비대해 보이면 어디부터 읽나? | 먼저 [계층형 아키텍처 기초](./layered-architecture-basics.md)로 Controller/Service/Repository 경계를 잡고, 이어서 [Service 계층 기초](./service-layer-basics.md)로 Service가 규칙 조합과 트랜잭션 orchestration까지만 맡는 기준을 본다. |
| DTO와 Entity는 왜 나누나? | API 계약과 DB 저장 구조가 서로 같이 흔들리지 않게 하려고 나눈다. |
| VO와 Entity는 뭐가 다르나? | VO는 "값이 같으면 같은 것", Entity는 "ID가 같으면 같은 것"이다. |
| Repository와 DAO는 같은가? | 비슷해 보여도, Repository는 도메인 관점 계약이고 DAO는 저장 기술 접근에 더 가깝다. |
| 검증은 Controller에서 할까 Service에서 할까? | HTTP 형식 검사는 Controller, 여러 진입점에서 공통인 업무 규칙은 Service/Domain이 기본이다. |

## 테스트 용어 한 줄 비교

테스트 용어도 먼저 정의를 외우기보다, **"이번 변경에서 어디까지 연결해 확인하나?"** 로 보면 덜 헷갈린다.

| 용어 | 초심자용 한 줄 뜻 | 보통 언제 먼저 고르나 |
|---|---|---|
| `unit test` | 한 클래스나 한 규칙을 주변 기술 없이 가장 작게 확인하는 테스트 | 계산 규칙, 조건 분기, 도메인 규칙이 바뀌었을 때 |
| `slice test` | 웹/영속성처럼 한 조각의 프레임워크 경계만 얇게 연결해 보는 테스트 | 컨트롤러 요청/응답, JPA 쿼리처럼 특정 층의 wiring을 보고 싶을 때 |
| `integration test` | 여러 조각을 실제에 가깝게 함께 붙여 흐름이 이어지는지 보는 테스트 | 트랜잭션, DB, 보안, 메시지, 외부 연동이 실제로 맞물리는지 볼 때 |
| `seam` | 테스트를 어디서 끊을지 정하는 경계선 | "여기까지는 fake/mock, 여기부터는 실제 연결"을 나눌 때 |

- 흔한 오해 1: `slice test`는 작은 `integration test`가 아니라, "특정 층만 집중해서 보는 경계 선택"에 가깝다.
- 흔한 오해 2: `seam`은 테스트 종류 이름이 아니라, unit/slice/integration을 나누게 해 주는 "끊는 기준"이다.
- 빠른 예시: 할인 금액 계산식 변경이면 `unit test`, `@WebMvcTest`로 요청 검증을 확인하면 `slice test`, 주문 저장과 재고 차감이 같은 트랜잭션으로 묶이는지 보면 `integration test`다.
- 다음 문서 연결: 첫 테스트를 고르는 기준은 [테스트 전략 기초](./test-strategy-basics.md), 경계(seam)를 어디에 둘지 더 보고 싶으면 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md), controller/message handler 같은 조각별 예시는 [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)로 이어가면 된다.

## 같은 예시로 보는 `첫 테스트 선택 -> seam 분리`

초심자에게는 "무슨 테스트를 먼저 쓸까?"와 "그 테스트를 어디서 끊을까?"를 분리해서 보는 편이 훨씬 쉽다.

같은 예시로 `쿠폰 만료 배치`를 잡으면 흐름은 아래처럼 단순하다.

| 단계 | 먼저 할 판단 | 이번 예시의 선택 | 다음 문서 |
|---|---|---|---|
| 1 | 첫 테스트를 무엇으로 시작할까? | 만료 시각이 지나면 `ACTIVE -> EXPIRED`가 되는지 `unit test`로 시작 | [테스트 전략 기초](./test-strategy-basics.md) |
| 2 | 그 테스트를 어디까지 검증할까? | fake repository로 유스케이스 규칙까지만 확인 | [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md) |
| 3 | DB 조건/매핑이 진짜 걱정되는가? | 걱정될 때만 `@DataJpaTest`를 별도 추가 | [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md), [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md) |

한 줄로 줄이면, [테스트 전략 기초](./test-strategy-basics.md)는 `첫 삽`을 고르게 해 주고 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)는 그 삽을 `어디 경계까지만 팔지`를 정하게 해 준다.

같은 beginner-safe 예시는 [Common-Confusion Wayfinding Notes](./common-confusion-wayfinding-notes.md#같은-예시로-보는-첫-테스트-선택---seam-분리)에도 다시 정리해 두었다. 문서 선택이 먼저 막히면 그 wayfinding 문서부터 보고 돌아오면 된다.

## 자주 헷갈리는 구조/타입 질문

- `Q. Layered Architecture` vs `Service Layer`
  - 멘탈 모델: `Layered Architecture`는 "도시 지도", `Service Layer`는 그 지도 안의 "업무 처리 구역"이다.
  - 초심자 기준으로는 [계층형 아키텍처 기초](./layered-architecture-basics.md)에서 Controller-Service-Repository 3칸과 주문 생성 before/after를 먼저 보고, 그다음 [Service 계층 기초](./service-layer-basics.md)에서 같은 주문 생성 시나리오로 Service가 트랜잭션과 유스케이스 조립을 어디까지 맡는지 좁혀 읽으면 된다.
  - 한 줄 구분: 구조를 묻는 질문이면 `Layered`, 서비스 책임 범위를 묻는 질문이면 `Service Layer`다.

- `Q. DTO` vs `Entity`
  - 멘탈 모델: DTO는 "밖과 약속하는 택배 상자", Entity는 "시스템 안에서 추적하는 실제 물건"이다.
  - `OrderEntity`를 그대로 응답으로 내보내면 DB 컬럼 변화가 API 응답 변화로 번지기 쉽다. 그래서 요청/응답은 DTO로, 저장 추적은 Entity로 분리한다.
  - 처음 구현 감각이 아직 없으면 [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)의 `request DTO -> service command -> entity 저장` 1분 표부터 보고, 그 다음 본문을 읽는 편이 빠르다.
  - 먼저 [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)를 보고, 경계 누수가 걱정되면 [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)로 이어가면 된다.

- `Q. VO` vs `Entity`
  - 멘탈 모델: `Money(1000원)`은 값이 같으면 같은 것이고, `Order#123`은 금액이 바뀌어도 같은 주문이다.
  - 그래서 VO는 보통 불변으로 다루고, Entity는 식별자와 생명주기를 중심으로 본다.
  - DTO/VO/Entity 셋이 한 번에 섞여 보이면 [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)의 "전달 계약 / 값 의미 / 식별자 추적" 구분부터 다시 잡는 것이 가장 빠르다.

## 저장/검증 질문

- `Q. Repository` vs `DAO`
  - 멘탈 모델: Repository는 "도메인이 원하는 창구", DAO는 "DB와 대화하는 손발"에 가깝다.
  - 초심자는 둘 다 저장소처럼 보여 헷갈리기 쉽지만, 도메인 언어를 유지하는 계약인지, SQL/ORM 세부에 가까운 구현인지로 보면 구분이 쉬워진다.
  - 빠르게 감을 잡으려면 [Repository, DAO, Entity](./repository-dao-entity.md)부터 보고, "인터페이스를 왜 나누지?"가 남으면 [Repository Interface Contract Primer](./repository-interface-contract-primer.md), "메서드 이름만 봐도 repository와 DAO를 구분하고 싶다"가 남으면 [Repository Naming Smells Primer](./repository-naming-smells-primer.md)로 이어가면 된다.

- `Q. 검증/트랜잭션은 Controller` vs `Service` 어디에 둘까?
  - 멘탈 모델: "입력 형식 확인"은 창구 일이고, "업무 규칙과 같이 성공/실패해야 하는 흐름"은 서비스 일이다.
  - 예를 들어 `@Valid`로 요청 필수값을 확인하는 것은 Controller 쪽이 자연스럽고, "수량은 1 이상", "주문 저장과 재고 차감은 같이 성공" 같은 규칙은 Service/Domain 쪽이 기본 위치다.
  - 같은 주문 결제 예시로 `paymentMethod` 빈값과 `CANCELLED 주문 재결제`를 한 표에서 바로 비교하고 싶으면 [Validation Boundary Mini Bridge](./validation-boundary-input-vs-domain-invariant-mini-bridge.md)를 먼저 보면 된다.
  - 바로 적용할 self-check는 [계층형 아키텍처 기초](./layered-architecture-basics.md)의 `Controller 검증/트랜잭션 경계 self-check`를 먼저 보면 된다.

## Beginner 30-Minute Entry Subset

처음 방문자는 "모든 개념을 다 이해"보다, `변경 단위`를 어디서 설명/검증하는지 30분 안에 한 바퀴 도는 게 목표다.

| 30분 질문 | 지금 읽을 1개 문서 | 왜 지금 읽나 |
|---|---|---|
| "처음 백엔드 미션 뭐부터?" | [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md) `필수` | 입문 용어를 한 번에 정리해 첫 문서 선택 시간을 줄인다. |
| "코드리뷰 용어 정리: `domain rule`, `DTO`, `transaction`" | [Mission Review Vocabulary Primer](./mission-review-vocabulary-primer.md) `필수` | 리뷰 용어를 책임 경계 언어로 번역해 첫 피드백 반영 속도를 높인다. |
| "가독성 이슈 분기: 코드가 읽히지 않을 때 어디부터 고치지?" | [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md) `필수` | 리팩터링 시작점을 `가독성-레이어-테스트` 순으로 잡아준다. |
| "Controller/Service/Repository 구조는 어떻게 나누지?" | [계층형 아키텍처 기초](./layered-architecture-basics.md) `필수` | 책임 분리와 검증/트랜잭션 경계 self-check로 초반 오해를 줄인다. |
| "서비스 레이어 뭐하는 곳?" | [Service 계층 기초](./service-layer-basics.md) `필수` | 업무 규칙 orchestration과 단순 위임을 구분하고, `Controller는 얇은데 Service가 저장 세부를 다 안다` 같은 흔한 오해를 before/after로 바로 끊어 준다. |
| "DTO vs VO vs Entity 차이" | [DTO, VO, Entity 기초](./dto-vo-entity-basics.md) `필수` | `request DTO -> service command -> entity 저장` 1분 표로 첫 흐름 감각을 잡고, 경계 타입을 섞어 쓰는 초반 실수를 줄인다. |
| "첫 테스트 선택표: 무엇부터 쓰면 되지?" | [테스트 전략 기초](./test-strategy-basics.md) `필수` | 5문항 체크리스트와 선택표를 같은 용어로 맞춰 첫 failing test를 빠르게 고르게 돕고, 보안 규칙 변경을 MVC 계약 변경과 초반에 분리해 `401/403` 혼동을 줄이며, `@WebMvcTest`/`@DataJpaTest` 시작 템플릿과 대표 반례를 바로 이어 준다. |

## Beginner 10-Minute Follow-up Branches

30분 subset을 끝냈다면, 다음 10분은 "내가 당장 개선하고 싶은 목표" 하나만 고르고 문서 1개만 더 읽는 방식이 가장 덜 헷갈린다.

| 지금 목표 (10분) | 바로 읽을 1개 문서 | 연결 이유 |
|---|---|---|
| 코드리딩: 어디부터 읽어야 하나 | [Common-Confusion Wayfinding Notes](./common-confusion-wayfinding-notes.md) `선택` | PR에서 섞인 용어와 책임 오해를 빠르게 분리해, 무엇을 먼저 고칠지 바로 정하게 돕는다. |
| 레이어 설계 | [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) `선택` | Controller-Service-Repository 다음 단계에서 inbound/outbound 경계를 어디서 끊을지 감각을 붙인다. |
| 테스트 | [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md) `선택` | 첫 테스트 종류를 고른 뒤, unit/adapter/contract 중 어디 경계에 둘지 seam 기준으로 좁혀 테스트 과잉을 줄인다. |
| Spring 웹 입구 큰 그림 | [Servlet Filter vs MVC Interceptor Beginner Bridge](./servlet-filter-vs-mvc-interceptor-beginner-bridge.md) `선택` | 처음 배우는데 `filter`와 `interceptor`가 비슷해 보여 controller/security 문서 선택이 막힐 때, 서블릿 입구와 MVC 경계를 먼저 나눠 준다. |
| 운영/배포 감각 | [Backend Delivery and Observability Foundations Primer](./backend-delivery-observability-foundations-primer.md) `선택` | logs, metrics, feature flag, rollout, rollback을 한 흐름으로 묶어 운영 용어를 따로 외우지 않게 돕는다. |

## 10분 분기 고르기 미니 self-check

문서 제목보다 **"지금 막힌 증상"** 으로 고르면 선택 실패가 줄어든다. 아래 4개 분기 중 `YES`가 2개 이상인 문서 1개만 먼저 열면 된다.

| 분기 | 이런 증상일 때 연다 | 바로 읽을 문서 |
|---|---|---|
| 코드리딩: 어디부터 읽어야 하나 | 용어가 섞여서 리뷰 코멘트의 뜻이 안 잡힌다 | [Common-Confusion Wayfinding Notes](./common-confusion-wayfinding-notes.md) |
| 레이어 설계 | 책임이 어디까지인지 몰라 파일을 옮겨도 계속 헷갈린다 | [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) |
| 테스트 | 테스트를 썼는데도 "어디가 깨진 건지" 설명이 안 된다 | [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md) |
| 운영/배포 감각 | 로그/지표/롤백 용어가 따로 놀아 "무엇으로 보고 어떻게 줄일지"가 안 잡힌다 | [Backend Delivery and Observability Foundations Primer](./backend-delivery-observability-foundations-primer.md) |

## 실제 PR 상황 예시

| 실제 PR 상황 | 먼저 고를 10분 분기 | 왜 이 분기부터 보나 |
|---|---|---|
| 가독성 이슈: 메서드 이름은 단순한데 검증, 조회, 저장, 응답 조립이 다 섞여 있다 | 코드리딩 | 네이밍 문제처럼 보여도 실제로는 어떤 일이 섞였는지 번역부터 해야 다음 수정이 흔들리지 않는다. |
| 레이어 혼합: Service에서 외부 API 세부, Repository 호출, 이벤트 발행까지 한 번에 처리한다 | 레이어 설계 | 파일 이동보다 먼저 안/밖 경계를 설명할 수 있어야 책임 분리가 된다. |
| 테스트 과잉: 규칙 하나 바꿨는데 `@SpringBootTest`와 무거운 fixture만 늘어난다 | 테스트 | 테스트 개수보다 질문보다 큰 테스트를 먼저 골랐는지 점검하는 것이 빠르다. |
| 운영 질문: "로그는 남기는데 무엇을 지표로 보고, 문제면 flag를 끌지 rollback할지"가 잘 안 잡힌다 | 운영/배포 감각 | delivery와 observability를 한 흐름으로 먼저 묶어야 운영 용어가 따로 놀지 않는다. |

## 분기별 self-check

- 코드리딩 self-check
  - `domain/service/repository/DTO` 같은 단어가 리뷰 코멘트마다 다르게 들려서, 무엇을 먼저 고쳐야 할지 멈춘다.
  - 같은 클래스를 봐도 "이건 구조 문제인가, 네이밍 문제인가, 책임 문제인가"가 바로 분리되지 않는다.
  - [Mission Review Vocabulary Primer](./mission-review-vocabulary-primer.md)까지 읽었는데도 코드 냄새 이름과 수정 방향이 연결되지 않는다.

- 레이어 설계 self-check
  - Controller에서 Service로 옮겼는데도 "이 로직이 아직도 여기 있어도 되나?"가 계속 남는다.
  - Repository, 외부 API client, 메시지 발행 코드가 Service 안에서 한 덩어리로 보여 경계선을 어디에 그을지 모르겠다.
  - [계층형 아키텍처 기초](./layered-architecture-basics.md)의 3칸 구조는 이해했지만, inbound/outbound처럼 "밖과 안의 경계" 이름이 아직 손에 안 잡힌다.

- 테스트 self-check
  - [테스트 전략 기초](./test-strategy-basics.md)에서 unit/`@WebMvcTest`/`@DataJpaTest`/`@SpringBootTest` 첫 선택은 했는데, 그 다음 "어느 경계까지 검증할지"가 흐리다.
  - 테스트가 초록이어도 adapter wiring, port contract, fake 경계 중 어디를 놓쳤는지 설명하기 어렵다.
  - Controller 테스트와 Service 테스트가 비슷한 시나리오를 중복해서 다루며, 무엇을 어느 층에서 검증해야 하는지 다시 정리하고 싶다.

- 운영/배포 감각 self-check
  - `log`, `metric`, `feature flag`, `rollout`, `rollback`이 각각 뭘 푸는 장치인지 자꾸 섞인다.
  - 배포 후 이상 징후가 보이면 `flag off`와 `rollback` 중 무엇을 먼저 고를지 감이 안 잡힌다.
  - 장애 회고 문서를 읽어도 "그래서 다음 배포에서 무엇을 바꾸라는 뜻이지?"가 바로 연결되지 않는다.

## 빠른 규칙과 흔한 오해

- 빠른 고르기 규칙:
  - `YES` 2개 이상이면 그 분기 문서부터 10분만 읽는다.
  - 두 분기가 동시에 걸리면 `코드리딩 -> 레이어 설계 -> 테스트 -> 운영/배포 감각` 순으로 하나씩만 연다.
  - 아무 분기도 2개가 안 걸리면, 이미 30분 subset 안에서 해결 가능한 질문일 가능성이 크니 위 `필수` 문서로 돌아간다.

- 흔한 오해:
  - "10분 추가면 세 문서를 다 읽어야 하나?"가 아니다. 지금 막힌 목표 1개에 해당하는 문서 1개만 읽으면 된다.
  - "`선택`이면 중요하지 않은 문서인가?"가 아니다. 지금 문제를 푸는 데 바로 안 막히면 잠시 미뤄도 된다는 뜻이다.
  - "Ports and Adapters는 고급 설계라 나중에 봐도 된다"가 아니다. beginner primer는 경계 이름을 외우는 문서가 아니라 책임을 섞지 않는 최소 규칙을 잡는 문서다.
  - "테스트 확장은 바로 E2E로 가야 한다"가 아니다. 먼저 seam(경계) 위치를 잡고 unit/slice/contract를 나누는 것이 10분 후속의 핵심이다.
  - "운영 문서는 나중에만 본다"가 아니다. project-stage 백엔드에서 feature flag, rollout, rollback 용어가 리뷰나 회고에 바로 나오면 최소 mental model은 일찍 잡아 두는 편이 덜 흔들린다.

- 자주 헷갈리는 포인트:
  - `Layered Architecture`는 구조 설명이고, `Service Layer`는 그 구조 안에서 서비스 책임을 더 구체화한 문서다.
  - `DTO/VO/Entity`를 먼저 분리하면 이후 예외 처리와 테스트 전략 문서가 훨씬 읽기 쉬워진다.
  - 고급 운영/장애 문서는 지금 건너뛰고, 아래 `기초 survey` 또는 `연결해서 보면 좋은 문서`에서 필요할 때만 확장한다.

## 기초 survey 입구

- 기초 survey부터 읽고 싶다면:
  - 추천 읽기 순서: `코드 읽기 감각` → `설계/경계` → `테스트/영속성`
  - [명령형 프로그래밍 vs 선언형 프로그래밍](#명령형-프로그래밍-vs-선언형-프로그래밍)
  - [함수형 프로그래밍](#함수형-프로그래밍)
  - [객체지향 프로그래밍](#객체지향-프로그래밍)
  - [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md) `필수`
  - [Mission Review Vocabulary Primer](./mission-review-vocabulary-primer.md) `필수`
  - [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md) `필수`
  - [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md) `선택`
  - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) `선택`
  - [Message-Driven Adapter Example](./message-driven-adapter-example.md) `선택`

## batch/persistence survey 입구

  - [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md) `선택`
  - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md) `선택`
  - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md) `선택`
  - [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md) `선택`
  - [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md) `선택`
  - [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md) `선택`
  - [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md) `선택`
  - [saveAll/sendAll Port Smells and Safer Alternatives](./saveall-sendall-port-smells-safer-alternatives.md) `선택`
  - [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md) `선택`
  - [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md) `선택`
  - [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md) `선택`
  - [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md) `선택`
  - [Webhook and Broker Boundary Primer](./webhook-and-broker-boundary-primer.md) `선택`
  - [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md) `선택`
  - [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md) `선택`
  - [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md) `선택`
  - [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md) `선택`

## repository/persistence survey 입구

  - [Repository Interface Contract Primer](./repository-interface-contract-primer.md) `선택`
  - [Repository Naming Smells Primer](./repository-naming-smells-primer.md) `선택`
  - [Repository, DAO, Entity](./repository-dao-entity.md) `선택`
  - [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) `선택`
  - [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md) `선택`
  - [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md) `선택`
  - [Repository Fake Design Guide](./repository-fake-design-guide.md) `선택`
  - [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md) `선택`
  - [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) `선택`
  - [JPA Lazy Loading and N+1 Boundary Smells](./jpa-lazy-loading-n-plus-one-boundary-smells.md) `선택`

## query/api survey 입구

  - [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md) `선택`
  - [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md) `선택`
  - [Bulk Helper Ports vs Query Model Separation](./bulk-helper-ports-vs-query-model-separation.md) `선택`
  - [Helper Snapshot Bloat Vs Response DTO Separation](./helper-snapshot-bloat-vs-response-dto-separation.md) `선택`
  - [API 설계와 예외 처리](./api-design-error-handling.md) `선택` - `MethodArgumentNotValidException`의 `400` 응답에서 `message`와 필드별 `errors[]`를 어떻게 읽는지까지 같이 볼 때

## deep dive 바로가기

- 설계/경계 deep dive로 바로 들어가려면:
  - `DDD, Hexagonal Architecture, Consistency Boundary`
  - `Batch Job Scope In Hexagonal Architecture`
  - `Batch Partial Failure Policies Primer`
  - `Batch Run Result Modeling Examples`
  - `Batch Idempotency Key Boundaries`
  - `Bulk Idempotency Keys For Named Contracts`
  - `Batch Recovery Runbook Bridge`
  - `Bulk Port vs Per-Item Use Case Tradeoffs`
  - `saveAll/sendAll Port Smells and Safer Alternatives`
  - `True Bulk Contracts and Partial Failure Results`
  - `Adapter Bulk Optimization Without Port Leakage`
  - `Testing Named Bulk Contracts`
  - `HTTP Coalescing Failure Mapping`
  - `DDD Bounded Context Failure Patterns`
  - `Clean Architecture vs Layered Architecture, Modular Monolith`
  - `Modular Monolith Boundary Enforcement`
  - `Module API DTO Patterns`
  - `ArchUnit Brownfield Rollout Playbook`
  - `Shared Module Guardrails`
  - `Domain Event, Outbox, Inbox`
  - `Outbox and Message Adapter Test Matrix`
  - `Idempotency, Retry, Consistency Boundaries`
  - `API Versioning, Contract Testing, Anti-Corruption Layer`
  - `Anti-Corruption Layer Integration Patterns`

## 거버넌스/운영 deep dive 바로가기

- 거버넌스/운영 모델 문서로 바로 들어가려면:
  - `Technology Radar and Adoption Governance`
  - `Build vs Buy, Exit Cost, Integration Governance`
  - `Architectural Governance Operating Model`
  - `Platform Scorecards`
  - `Consumer Exception Operating Model`
  - `Service Deprecation and Sunset Lifecycle`
  - `Shadow Process Detection Signals`
  - `Shadow Process Catalog and Retirement`
  - `Shadow Process Catalog Entry Schema`
  - `Shadow Review Packet Template`
  - `Shadow Review Outcome Template`
  - `Shadow Forum Escalation Rules`
  - `Shadow Catalog Lifecycle States`
  - `Shadow Catalog Review Cadence Profiles`
  - `Temporary Hold Exit Criteria`
  - `Manual Path Ratio Instrumentation`
  - `Mirror Lag SLA Calibration`
  - `Shadow Candidate Promotion Thresholds`
  - `Threshold Override Governance`
  - `Shadow Promotion Snapshot Schema Fields`
  - `Emergency Misclassification Signals`
  - `Break-Glass Reentry Governance`
  - `Shadow Retirement Proof Metrics`
  - `Shadow Retirement Scorecard Schema`
  - `Shadow Catalog Reopen and Successor Rules`
  - `Shadow Process Officialization and Absorption Criteria`
  - `Override Burn-Down and Exemption Debt`
  - `Override Burn-Down Review Cadence and Scorecards`
  - `Service Portfolio Lifecycle Governance`
  - `Operational Readiness Drills and Change Safety`
  - `Change Ownership Handoff Boundaries`
  - `Support SLA and Escalation Contracts`
  - `Support Operating Models: Self-Service, Office Hours, On-Call`

## governance deep dive 메모

- cross-category bridge로 확장하려면:
  - [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge)
- 보조 primer는 맨 아래 `애자일 개발 프로세스` 구간만 별도로 보면 된다.

## 연결해서 보면 좋은 문서 (cross-category bridge)

빠른 탐색에서는 software-engineering 내부 primer entrypoint만 남기고, adjacent-category handoff는 이 섹션에만 모아 둔다.

- 구조 primer를 디자인 패턴 언어와 runtime plane으로 이어 읽으려면 [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md), [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) 다음에 [Design Pattern: Ports and Adapters vs GoF 패턴](../design-pattern/ports-and-adapters-vs-classic-patterns.md), [Design Pattern: Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](../design-pattern/hexagonal-ports-pattern-language.md), [System Design: Control Plane / Data Plane Separation 설계](../system-design/control-plane-data-plane-separation-design.md)를 같이 보면 `layer`, `port`, `plane`이 서로 다른 질문에 답한다는 감각이 빨리 잡힌다.
- 처음 배우는데 `템플릿 메소드 vs 전략`이 궁금하면 smell 문서부터 가지 말고 [Design Pattern: 템플릿 메소드 첫 질문 라우터](../design-pattern/template-method-query-router-beginner.md) -> [Design Pattern: 템플릿 메소드 패턴 기초](../design-pattern/template-method-basics.md) -> [Design Pattern: 템플릿 메소드 vs 전략](../design-pattern/template-method-vs-strategy.md) 순서로 먼저 큰 그림을 잡는다. `hook method`, `abstract step`, `부모가 흐름을 쥔다 vs 호출자가 전략을 고른다` 같은 검색도 이 같은 beginner entry route로 묶는다. [Design Pattern: Template Hook Smells](../design-pattern/template-hook-smells.md)는 `beforeX`/`afterX`/`cleanup`이 이미 불어나서 "hook 하나 더 둘지, 구조를 갈아야 할지"를 점검하는 늦은 follow-up 문서로 보는 편이 안전하다.

## inbound/runtime bridge

- 채널별 inbound adapter를 command lifecycle과 테스트 경계까지 함께 잡으려면 [Message-Driven Adapter Example](./message-driven-adapter-example.md), [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md), [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md), [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md), [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md), [Webhook and Broker Boundary Primer](./webhook-and-broker-boundary-primer.md), [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md), [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md), [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md) 다음에 [Design Pattern: Command Handler Pattern](../design-pattern/command-handler-pattern.md), [Design Pattern: Process Manager Deadlines and Timeouts](../design-pattern/process-manager-deadlines-timeouts.md), [System Design: Job Queue 설계](../system-design/job-queue-design.md), [System Design: 분산 스케줄러 설계](../system-design/distributed-scheduler-design.md), [System Design: Workflow Orchestration + Saga 설계](../system-design/workflow-orchestration-saga-design.md)를 이어서 본다.

## persistence bridge

- persistence primer를 read-model boundary와 migration/cutover handoff로 확장하려면 [Repository, DAO, Entity](./repository-dao-entity.md), [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md), [Repository Fake Design Guide](./repository-fake-design-guide.md), [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md) 다음에 [Design Pattern: Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md), [Design Pattern: Anti-Corruption Adapter Layering](../design-pattern/anti-corruption-adapter-layering.md), [System Design: Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md), [System Design: Zero-Downtime Schema Migration Platform 설계](../system-design/zero-downtime-schema-migration-platform-design.md)를 붙이면 aggregate 경계와 relay/cutover 경계가 한 줄로 연결된다.

## 입문 이후: catalog로 넘어가는 기준

입문 구간을 읽은 다음에는, **"용어를 익히는 단계"에서 "설계 선택지를 비교하는 단계"로 넘어간다**고 생각하면 된다. 이 지점부터의 catalog는 `정답 암기`보다 `왜 이 경계를 택했는지 설명하는 문서`에 가깝다.

| 아직 beginner 구간에 머물 때 | catalog로 넘어갈 때 |
|---|---|
| `Service`, `Repository`, `DTO` 같은 단어 뜻이 아직 자주 흔들린다 | 같은 단어 뜻은 아는데 "이 경우엔 어떤 경계 선택이 맞나?"를 비교하고 싶다 |
| "이 로직을 어디로 옮기지?"가 먼저 막힌다 | "batch 전용 유스케이스를 따로 둘까?", "read model을 분리할까?"처럼 선택지 비교가 막힌다 |
| 한 문서에서 before/after 예시가 더 필요하다 | trade-off, rollout, governance 문서가 더 필요하다 |

- catalog로 넘어가기 전에 최소로 확인할 문서:
  - [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md)
  - [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md)
  - [계층형 아키텍처 기초](./layered-architecture-basics.md)
  - [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)

- catalog 첫 진입 추천:
  - 경계 설계가 궁금하면 [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) 다음에 `DDD, Hexagonal Architecture, Consistency Boundary` 구간으로 간다.
  - 테스트/영속성 경계가 궁금하면 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md), [Repository Interface Contract Primer](./repository-interface-contract-primer.md) 다음에 persistence/query-model catalog로 간다.
  - 운영/거버넌스 문서는 `입문 이후`에도 바로 첫 선택이 아니다. 코드 경계가 먼저 잡힌 뒤 `rollout`, `governance`, `ownership` 질문이 생길 때만 연다.

- 자주 하는 착각:
  - "`catalog`에 있으면 지금 당장 다 읽어야 하나?"가 아니다. 지금 질문과 같은 키워드가 보이는 묶음 1개만 고르면 된다.
  - "beginner 문서를 끝냈으니 장애/운영 문서부터 봐야 하나?"가 아니다. 초반에는 설계 경계 catalog가 우선이고, 운영 문서는 필요 시 링크로 확장하면 충분하다.

## 레거시 primer

아래 구간은 소프트웨어 공학 입문과 패러다임 복습용 primer다.

## 프로그래밍 패러다임

## 명령형 프로그래밍 vs 선언형 프로그래밍

 함수형 프로그래밍은 선언형 프로그래밍이다.

- **명령형 프로그래밍** :

   명령형 프로그래밍은 **어떻게(HOW)** 목적을 달성 할 지에 초점이 맞추어져 있고 프로그래밍의 상태와 그것을 변경시키는 구문의 관점에서 연산을 설명하는 프로그래밍 패러다임이다. 그래서 프로그래밍에 사용된 알고리즘에 대해서는 명시되어 있고 목표에 대해서는 명시되어 있지 않다. 일반적으로 컴퓨터가 수행할 명령들을 순서대로 써내려가는데 일반적인 예시로는 C, C++, Java, Paskal, Ruby 등 우리가 아는 웬만한 절차형, 객체지향 언어들은 명령형 프로그래밍 언어이다.

- **선언형 프로그래밍** :

  선언형 프로그래밍은 일반적으로 두 가지 정의로 나뉜다.

  1. 선언형 프로그래밍은 **무엇을(WHAT)** 할지에 초점이 맞추어져 있는 프로그래밍 패러다임이다. 알고리즘은 명시하지 않고 목표에 대해서만 명시 한다. 예를들어 HTML 과 같이 무엇을 웹에 나타낼지에 대해 고민하는 것이지 어떤 방법으로 나타낼지를 고민 하는 것이 아니다.
  2. 함수형, 논리형, 제한형 프로그래밍 언어로 쓰인 경우 선언형 프로그래밍이라고 한다. 명령형 언어와 대비되는 프로그래밍 언어들을 선언형으로 통칭한다. 하지만 이 중 논리형, 제한형 프로그래밍 언어 같은 경우 명백히 알고리즘을 설명할 수 있고 구현도 가능하기 때문에 첫번째 정의를 따르는 엄밀한 의미의 선언형 프로그래밍은 아니다.

## 함수형 프로그래밍

## 함수형 프로그래밍을 배워야 하는 이유

  "일반적인 프로그래밍은 그냥 생각하면 되는 것이고, 함수형 프로그래밍은 기존과 다르게 생각하는 방법을 알려줄 것이다. 그러므로 당신은 아마도 예전 방식으로 절대 돌아가지 않을 것이다."

   함수형 프로그래밍은 프로그래밍 언어나 방식을 배우는 것이 아니라 함수로 프로그래밍 하는 사고를 배우는 것이다. 즉 기존의 사고방식을 전환하여 사고를 유연하게 문제 해결에 접근 하는 것이다.

## 함수형 프로그래밍이란?

   함수형 프로그래밍이란 자료처리를 수학적 함수의 계산으로 취급하고 상태와 가변 데이터를 멀리하는 프로그래밍 패러다임의 하나이다. 명령형 프로그래밍에서 상태를 바꾸는 것을 강조하는 것과는 달리 함수형프로그래밍은 함수의 응용을 강조한다. 따라서 프로그래밍이 식이나 선언으로 수행되는 선언형 프로그래밍 패러다임을 따르고 있다.

- 명령형 프로그래밍의 함수와 수학적 함수의 차이

    **명령형 프로그래밍의 함수** : 프로그램의 상태의 값을 바꿀 수 있다. 이 때문에 참조 투명성이 없고 같은 코드라 해도 실행되는 프로그램의 상태에 따라 다른 결과값을 낼 수 있다.

    **함수형 프로그래밍 (수학적) 함수** : 이 함수의 출력값은 함수에 입력된 인수에만 의존하므로 인수 x에 대해 함수 f 를 호출 하면 f(x) 라는 결과가 나온다. 이것은 프로그램의 동작을 예측하기 훨씬 쉬워진다. (함수형 프로그래밍 개발 핵심 동기)

   함수형 프로그래밍은 **순수함수(pure function)** 을 조합하고 **공유상태(shared state)**, **변경 가능한 데이터(mutable data)** 및 **부작용(side-effects)** 을 피하여 소프트웨어를 만드는 프로세스이다.

## 함수형 프로그래밍 주요 개념

  1. 순수 함수(pure function) : 무조건 같은 입력이 주어지면 같은 출력을 반환한다. 또한 부작용이 없는 함수 이다.
  2. 합성 함수(function composition) : 새로운 함수를 만들기 위해 둘 이상의 함수를 조합하는 과정이다. f(g(x))로 이해하면 된다. 합성 함수는 함수형 프로그래밍을 이용하여 소프트웨어를 구성하는 중요한 방법이다.
  3. 공유 상태(shared state) : 공유 범위(shared scope) 내에 있는 변수, 객체 또는 메모리 공간이거나 범위 간에 전달되는 객체의 속성입니다.
  4. 불변성(Immutability) : 변경할 수 없는 객체란 생성한 후에 수정할 수 없는 객체이다. 불변성은 함수형 프로그래밍의 핵심 개념이다. 불변성을 빼면 프로그램의 데이터 흐름이 손실되기 때문이다.
  5. 부작용(side effects) : 반환값 이외에 호출된 함수 외부에 영향을 끼치지는 것이다. 따라서 부작용이 없는 순수한 함수는 스레드 측면에서 안전하고 병렬적인 계산이 가능하다.
     - 외부 변수 또는 객체 속성 수정
     - 콘솔에서 로깅
     - 화면에 쓰기 작업
     - 파일에 쓰기 작업
     - 네트워크에 쓰기 작업
     - 외부 프로세스를 트리거
     - 부작용을 동반한 다른 함수 호출
  6. 고차함수(high order function) : 함수를 인수로 취급하거나, 함수를 반환하거나 또는 둘 다인 함수이다.
     - 콜백 함수, 프로미스, 모나드 등을 사용하여 액션, 효과 또는 비동기 흐름을 추상화하거나 분리
     - 다양한 데이터 타입에 대해 동작할 수 있는 유틸리티 만듬
     - 합성 함수나 재사용의 목적으로 커링 함수를 만들거나 인수를 함수에 부분적으로 적용
     - 함수 목록을 가져오고, 입력 함수의 합성을 반환

## 객체지향 프로그래밍

## 객체지향 프로그래밍 이전 패러다임

  1. 순차적, 비구조적 프로그래밍 : 말그대로 순차적으로 코딩해 나가는 것, 필요한 것이 있으면 순서를 추가해가면서 구현하는 방식이다. 직관적이지만 goto문을 활용하므로서 규모가 매우 커지게 되고 나중엔 코드가 어떻게 연결되었는지 구분하기 매우 어렵다.
  2. 절차적, 구조적 프로그래밍 : 위 프로그래밍 방식을 개선하기 위해 나온 패러다임이다. 반복될 가능성이 높은 함수(프로시저)들을 따로 만들어 사용하는 방식이다. 하나의 큰기능을 처리하기 위해 작은 단위의 기능들으로 나누어 처리하고 비교적 작은 규모의 작업을 수행하는 함수를 생성한다. 하지만 이러한 절차적, 구조적 프로그래밍은 함수(논리적 단위)는 표현이 되지만 실제 데이터에 대한 변수 나 상수(물리적 단위)의 표현에는 어려움이 있다. 이러한 단점은 프로그램을 비효율적으로 코딩하게 되고 결국은 유지보수와 디버깅에 어려움을 가져온다. 즉  큰 규모의 작업으로 갈 수 록 더 효율적인 모듈화와 데이터 관리가 필요하다 그렇기에 나온게 데이터와 함수를 동시에 관리 할 수 있는 객체지향 프로그래밍이 각광받게 된다.

## 객체 지향 프로그래밍이란

   객체 지향 프로그래밍은 특정한 개념의 함수와 자료형을 함께 묶어서 관리하기 위해 탄생한 것이다. 즉 객체 내부에 자료형(필드)와 함수(메소드) 가 같이 존재 한다. 객체지향 프로그래밍을 하면 객체간의 독립성이 생기고 중복코드의 양이 줄어드는 장점이 있다. 또한 독립성이 확립되면서 유지보수에도 큰 도움을 주게 된다.

   또한 이러한 객체들 끼리 서로 상호작용하면서 어떠한 문제를 해결해 나가는 것이 객체지향 프로그램이다.

## 객체 지향 프로그래밍의 특성

  1. 추상화(Abstraction)

     어떤 영역에서 필요로 하는 속성이나 행동을 추출하는 작업 , 즉 모델화

     - 사물들의 공통된 특징, 즉 추상적 특징을 파악해 인식의 대상으로 삼는 행위
     - 구체적인 사물들의 공통적인 특징을 파악해서 이를 하나의 개념(집합)으로 다루는 수단

     >구체적인 개념에 의존
     >
     >```java
     >switch(동물의 종류){
     >  case 사자 : //somthing
     >  case 호랑이 : // something
     >  case 토끼 : // someting
     >}
     >```
     >
     >새로운 종이 추가 되면 코드를 새로 추가 해야함
     >
     >
     >
     >추상적인 개념에 의존
     >
     >```java
     >void something(Animal a){
     >  a.something();
     >}
     >```
     >
     >새로운 종이 나와도 코드를 변경 할 필요가 없다. 뒤에서 다형성에 의한 오버라이드로 처리

  2. 캡슐화(Encapsulation)

      높은 응집도(Cohesion) 과 낮은 결합도(Coupling) 를 유지해야 요구사항에 맞춰 유연하게 대처 할 수 있다.

     - 응집도 : 모듈(클래서) 내에서 요소들이 얼마나 밀접하게 관련이 있는지, 응집도는 정보 은닉을 통해 높일 수 있다. 즉, 내부에서만 사용하는 정보는 외부에서 접근하지 못하도록 제한하는 것이다. Ex) private
     - 결합도 : 어떠한 기능을 수행하는데 다른 모듈(클래스)에 얼마나 의존적인지

  3. 일반화(Generalization) : 상속

     이미 정의된 상위클래스의 모든 속성과 연산을 하위클래스가 물려 받는 것을 의미한다.

     - 일반화를 이용 하면 상위 클래스로 부터 상속받은 하위 클래스는 모든 속성(필드)과 연산(메소드)을 다시 정의하지 않고 자신의 것으로 사용 할 수있다.
     - 상속받은 속성과 연산 외에 새로운 속성과 연산을 추가하여 사용 가능하다.
     - 클래스를 재사용 하므로서 소프트웨어 재사용성을 증대시키는 중요한 개념이다.

  4. 다형성(Polymorphism)

     1. Pure Polymorphism : 서로 다른 클래스의 객체가 같은 메세지를 받았을때 각자의 방식으로 동작하는 능력이다.
        - 일반화와 함께 프로그램을 변화에 유연하게 만든다.
        - 다형성을 사용할 경우 어떤 클래스가 참조 되었는지 무관하게 프로그래밍 할 수 있다.

     2. Ad hoc polymorphism : Overridng & Overloading

     3. Generics (parameter type) : T (type parameter, 어떤 타입이 와도 무관)

## 객체지향 설계 원칙 SOLID

1. SRP(단일 책임의 원칙 : Single Responsibility Principle) : 작성된 클래스는 하나의 기능만 가지며 클래스가 제공하는 모든 서비스는 그 하나의 책임을 수행하는데 집중되어 있어야 한다는 원칙

2. OCP(개방폐쇄의 원칙 : Open Close Principle) : 소프트웨어의 구성요소는 확장에는 열려있고, 변경에는 닫혀있어야 한다는 원칙. 변경은 최소화 하고 확장을 최대화

3. LSP(리스코브 치환의 원칙 : The Liskov Substitution Principle) : 서브타입은 언제나 기반 타입으로 교체할 수 있어야 한다는 원칙, 즉 항상 하위 클래스는 상위 클래스를 대신할 수 있다. 상위클래스가 할 수 있는 일들에 대해선 하위클래스는 당연히 할 수 있다는 원칙이다.

4. ISP(인터페이스 분리의 원칙 : Interface Segregation Principle) : 인터페이스 분리 원칙은 클라이언트가 자신이 이용하지 않는 메서드에 의존하지 않아야 한다는 원칙이다. 인터페이스 분리 원칙은 큰 덩어리의 인터페이스들을 구체적이고 작은 단위들로 분리시킴으로써 클라이언트들이 꼭 필요한 메서드들만 이용할 수 있게 한다. SRP 는 클래스의 단일 책임이라면 ISP는 인터페이스의 단일 책임을 강조하는 것이다.

5. DIP(의존성 역전의 원칙 : Dependency Inversion Principle) : 자주 변화하는 구체적인 클래스 보다는 변화하기 어려운 인터페이스나 상위(추상) 클래스와 관계를 맺으라는 원칙

## 최신 설계 / 거버넌스 catalog

아래 구간은 최신 설계 선택지, 경계 설계, rollout, governance 문서를 모아 둔 catalog다.

`입문 이후` 기준으로는, 이 구간을 "beginner primer 다음 단계"로 보면 된다. 아직 `Service/Repository/DTO` 기본 역할이 자주 흔들리면 위 beginner 구간으로 돌아가고, 기본 역할은 설명할 수 있지만 `trade-off`, `boundary`, `rollout`, `governance` 비교가 필요할 때만 아래 catalog를 연다.

## SOLID Failure Patterns

- [SOLID Failure Patterns](./solid-failure-patterns.md)

> 원칙을 외우는 대신, 각 원칙이 무너질 때 어떤 실패가 생기는지와 과하게 적용했을 때 어떤 비용이 생기는지 정리한 문서

## 우테코 백엔드 미션 선행 개념 입문

- [우테코 백엔드 미션 선행 개념 입문](./woowacourse-backend-mission-prerequisite-primer.md)

> 우테코 백엔드 미션 전에 무엇을 완벽히 알아야 하는지보다, 입력 -> 규칙 -> 조립 -> 저장/응답 흐름과 `Service`/`Repository`/`DTO`/`Entity` 역할을 먼저 잡게 돕는 beginner entrypoint
>
> 막힌 질문별로 Java/OOP, layer, DTO/VO/Entity, JDBC/JPA, HTTP/Spring primer로 안전하게 내려가는 첫 라우트
>
> beginner-safe ladder: `Java basics -> HTTP/web basics -> MVC -> JDBC/transactions -> DI/AOP -> system design`를 고정하고, 각 단계는 primer 하나 + follow-up 하나를 끝낸 뒤 다음 단계로 넘어간다.
>
> 관련 cross-category bridge: [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md), [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md), [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md), [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md), [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](../spring/spring-ioc-di-basics.md), [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](../system-design/stateless-backend-cache-database-queue-starter-pack.md)

## Mission Review Vocabulary Primer

- [Mission Review Vocabulary Primer](./mission-review-vocabulary-primer.md)

> PR 리뷰에서 자주 나오는 `domain rule`, `DTO`, `entity`, `repository`, `service`, `validation`, `transaction`을 "어디에 둬야 하는 책임인가" 관점으로 번역해 주는 초심자용 bridge primer

## Common-Confusion Wayfinding Notes

- [Common-Confusion Wayfinding Notes](./common-confusion-wayfinding-notes.md)

> `batch/헥사고날`, `영속성/JPA`, `테스트`, `controller-service-repository 책임` 중 어디부터 읽을지 헷갈릴 때, 막힌 질문을 `유스케이스 경계`, `영속성 구현`, `첫 테스트 선택`, `계층 경계`로 나눠 시작 문서를 고르게 돕는 beginner wayfinding bridge
> 이번 QA 보강으로 `saveAll` 오해가 보이면 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)로, Controller는 얇은데 Service가 비대해 보이면 [계층형 아키텍처 기초](./layered-architecture-basics.md)와 [Service 계층 기초](./service-layer-basics.md)로 바로 이어지는 분기를 더 선명하게 적었다.

## 읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문

- [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md)

> 읽기 좋은 메서드/클래스, controller-service-repository 책임 분리, unit vs integration test, 테스트를 곁들인 작은 리팩토링 루프를 우테코 코드 리뷰 문맥으로 한 번에 묶어 주는 beginner bridge primer

## 계층형 아키텍처 기초

- [계층형 아키텍처 기초](./layered-architecture-basics.md)

> Controller / Service / Repository를 "창구-업무-창고" 3칸으로 나눠 보고, 형식 검증과 업무 규칙, 트랜잭션을 어디에 둘지 첫 기준을 잡게 돕는 beginner primer

## Service 계층 기초

- [Service 계층 기초](./service-layer-basics.md)

> Service가 모든 걸 아는 만능 계층이 아니라, 유스케이스 순서와 트랜잭션 경계를 조립하는 곳이라는 기준을 짧은 before/after와 첫 테스트 연결로 묶어 둔 beginner primer

## 테스트 전략 기초

- [테스트 전략 기초](./test-strategy-basics.md)

> unit test, `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest` 중 이번 변경의 첫 테스트 1개를 어떻게 고를지 4문항 체크리스트와 반례로 안내하는 beginner primer

## SOLID 원칙 기초

- [SOLID 원칙 기초](./solid-principles-basics.md)

> SOLID 다섯 원칙을 암기 목록이 아니라 "왜 이 구조가 바꾸기 쉽게 만드는가" 관점으로 풀어 주고, 더 깊은 실패 패턴 문서로 넘어가기 전 안전한 첫 기준을 주는 primer

## DTO, VO, Entity 기초

- [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)

> `request DTO -> service command -> entity 저장` 흐름으로 전달 계약, 값 의미, 식별자 추적을 분리해 초심자의 경계 타입 혼동을 줄여 주는 beginner primer

## 예외 처리 기초

- [예외 처리 기초](./exception-handling-basics.md)

> 비즈니스 예외와 시스템 예외를 구분하고, 어디서 던지고 어디서 HTTP 응답으로 바꿀지 첫 경계선을 잡게 하는 beginner primer

## Architecture and Layering Fundamentals

- [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)

> layered / clean / modular monolith / DDD boundary / repository-entity separation을 한 번에 연결해 주는 입문 브리지 문서

## Ports and Adapters Beginner Primer

- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)

> hexagonal ports/adapters를 입문자 눈높이에서 풀고, inbound/outbound port와 간단한 폴더 구조를 clean architecture와 연결해 설명하는 후속 primer

## Message-Driven Adapter Example

- [Message-Driven Adapter Example](./message-driven-adapter-example.md)

> HTTP controller, message consumer, scheduled job를 같은 hexagonal 모델 안의 inbound adapter로 비교하고, 채널별 차이는 응답/재시도/배치 처리 같은 adapter 관심사에 있다는 점을 짧게 정리한 primer

## Batch Job Scope In Hexagonal Architecture

- [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)

> scheduled job가 기존 유스케이스를 per-item loop로 재사용해도 되는 경우와, batch window/chunk/checkpoint/failure policy가 application 의미가 되는 순간 dedicated batch-oriented application service로 올려야 하는 기준을 정리한 follow-up

## Batch Partial Failure Policies Primer

- [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)

> batch가 단순 per-item retry를 넘어서 chunk summary, retry queue, checkpoint를 언제 별도 정책으로 가져가야 하는지, run 재개와 실패 backlog를 beginner 눈높이에서 구분해 설명한 primer

## Batch Run Result Modeling Examples

- [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)

> `RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint`를 framework-specific 구현체가 아니라 batch 실패/재개를 설명하는 네 가지 결과 모델로 나누어 초심자 예시와 비교표로 정리한 bridge primer

## Batch Idempotency Key Boundaries

- [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)

> item-level, chunk-level, run-level idempotency key를 "같은 일을 다시 요청했는가"라는 질문으로 나누어, batch retry/resume이 중복 부작용 없이 복구되도록 설명한 beginner bridge primer

## Bulk Idempotency Keys For Named Contracts

- [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md)

> `run`, `file`, `chunk`, `item` 같은 named contract를 먼저 고정한 뒤, rerun/re-upload/retry 장면마다 어떤 idempotency key scope를 재사용하고 언제 새 key로 바꿔야 하는지 초심자용 선택 기준으로 연결한 bridge primer

## Batch Recovery Runbook Bridge

- [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)

> batch failure policy를 operator runbook 언어로 옮겨, 무엇을 먼저 확인하고 언제 멈추며 어떤 증거가 있어야 safe rerun할 수 있는지 초심자 기준으로 연결한 beginner operations bridge

## Bulk Port vs Per-Item Use Case Tradeoffs

- [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)

> 처리량 문제를 보고 곧바로 `saveAll`/`sendAll` 같은 bulk port를 노출하기보다, strict per-item execution을 유지할지, per-item 유스케이스는 둔 채 bulk helper port만 둘지, 아니면 bulk 자체를 application 계약으로 올릴지를 초심자 기준으로 비교한 primer

## saveAll/sendAll Port Smells and Safer Alternatives

- [saveAll/sendAll Port Smells and Safer Alternatives](./saveall-sendall-port-smells-safer-alternatives.md)

> `saveAll`/`sendAll`를 outbound port로 바로 노출할 때 왜 item 단위 불변식과 실패 정책이 숨어 버리는지 설명하고, 단건 port 유지, bulk helper port, named batch contract로 나누는 더 안전한 beginner primer
> 이번 QA 보강으로 "`saveAll`이면 JPA batch도 자동으로 맞는가?"라는 오해가 보일 때 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)로 즉시 넘어가도록 링크 문구를 보강했다.

## True Bulk Contracts and Partial Failure Results

- [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)

> bulk가 실제 업무 단위가 되었을 때 `List<T>`와 단순 count 대신 run/chunk/file 입력 계약과 partial failure result 타입을 어떻게 이름 붙여야 하는지 beginner 눈높이에서 정리한 follow-up primer

## Adapter Bulk Optimization Without Port Leakage

- [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)

> JPA `saveAll`, JDBC batch, HTTP bulk endpoint를 adapter 내부 최적화로 유지하면서 application port는 per-item, domain-shaped 계약으로 남기는 기준을 초심자용 mental model, 3건 예시, 적용 3단계로 정리한 bridge primer

## Testing Named Bulk Contracts

- [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)

> named bulk adapter 테스트에서 `SettlementChunk`, `ItemFailure`, `receiptId`를 중심으로 chunk invariant, item-failure mapping, receipt correlation을 어떤 assertion으로 고정해야 하는지 초심자용 체크리스트와 예시로 정리한 compact primer

## HTTP Coalescing Failure Mapping

- [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md)

> HTTP adapter가 bulk endpoint 응답을 받을 때 `batch receipt`, `per-item receipt`, `retry decision`으로 다시 펼쳐서 부분 성공과 누락 item을 안전하게 다루는 기준을 초심자용 예시로 정리한 focused primer

## Webhook and Broker Boundary Primer

> 이 문서를 읽기 전 필요한 선행 개념: [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)에서 inbound adapter가 "바깥 입력을 유스케이스 호출로 번역하는 자리"라는 감각만 먼저 잡고 오면 된다.

- [Webhook and Broker Boundary Primer](./webhook-and-broker-boundary-primer.md)

> webhook endpoint와 broker consumer를 같은 inbound adapter 축에 두고, 차이는 transport 종류보다 retry 주도권, idempotency key, acknowledgment semantics에서 갈린다는 점을 정리한 follow-up primer

## Hexagonal Testing Seams Primer

> 이 문서를 읽기 전 필요한 선행 개념: [테스트 전략 기초](./test-strategy-basics.md)에서 unit/slice/integration 차이를 먼저 익히고, [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)에서 inbound/outbound port 이름만 구분할 수 있으면 충분하다. 문서 상단에는 "지금 필요한 게 seam 설명인지, 아니면 첫 테스트 종류 선택인지"를 가르는 3문항 브리지 질문도 추가해 두었다.

- [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)

> hexagonal 경계를 테스트 seam으로 읽어, 유스케이스 unit test는 fake outbound port로 빠르게 검증하고 adapter integration test는 언제 필요한지 분리해 설명하는 후속 primer

## Inbound Adapter Test Slices Primer

- [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)

> controller/message handler 같은 inbound adapter test에서 port 경계까지만 보는 slice test와 실제 transaction, broker, security wiring까지 보는 full integration test를 언제 나눌지 설명하는 후속 primer

## Inbound Adapter Testing Matrix

- [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)

> controller, message consumer, scheduled job를 같은 hexagonal inbound adapter로 두되 controller는 slice-heavy, consumer는 integration/contract-heavy, scheduler는 clock/lock-heavy portfolio가 필요하다는 follow-up matrix

## Outbox and Message Adapter Test Matrix

- [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md)

> outbox/inbox와 message-driven adapter를 한 흐름으로 놓고, unit test는 결정 로직, integration test는 transaction/broker/dedup wiring, contract test는 event schema와 consumer 약속을 맡도록 분리하는 실전 매트릭스

## Repository Interface Contract Primer

- [Repository Interface Contract Primer](./repository-interface-contract-primer.md)

> 처음 배우는데 `Repository`를 왜 인터페이스로 두는지, 구현체 교체 계약과 DAO/helper 구현 세부를 어디서 나눠 읽어야 하는지 큰 그림부터 잡는 beginner entrypoint primer

## Persistence Follow-up Question Guide

- [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)

> `Repository Interface Contract Primer`부터 `Persistence Model Leakage Anti-Patterns`까지를 하나의 질문형 결정표와 짧은 코드 예시로 묶어, 초심자가 지금 막힌 지점이 계약/이름/조회 분리/매핑/누수 중 어디인지 먼저 고르게 돕는 beginner bridge primer

## Repository Naming Smells Primer

- [Repository Naming Smells Primer](./repository-naming-smells-primer.md)

> 처음 배우는데 메서드 이름만 보고도 domain-language repository 계약과 table/SQL-shaped DAO API를 구분할 수 있게, `save/find` vs `insert/select/update` 말투와 query-model 분기 신호를 짧은 표와 예시로 정리한 beginner primer

## Repository, DAO, Entity

- [Repository, DAO, Entity](./repository-dao-entity.md)

> 초심자가 저장 계층 용어를 glossary처럼 외우지 않고도 `Repository=유스케이스 저장 창구`, `DAO=테이블/SQL 도구`, `Entity=저장용 모양`, `Mapper=번역기`로 한 표에서 먼저 구분한 뒤, 작은 주문 저장 예시와 흔한 혼동 bullets로 첫 동선을 잡게 돕는 persistence primer
> 같은 주문 생성 시나리오를 [계층형 아키텍처 기초](./layered-architecture-basics.md)와 이어 읽을 수 있게, `Service -> Repository -> DAO -> Entity` 책임 이동을 가볍게 다시 보여 주는 연결 문서

## DAO vs Query Model Entrypoint

- [DAO vs Query Model Entrypoint](./dao-vs-query-model-entrypoint-primer.md)

> 처음 배우는데 DAO로 충분한 경우와 dedicated query repository/read model이 더 나은 경우를 "정해진 대상 조회" vs "읽기 화면 설계"라는 큰 그림으로 빠르게 나눠 주는 beginner bridge primer

## Persistence Adapter Mapping Checklist

- [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)

> repository port는 도메인 언어를 유지하고, JPA entity 매핑과 fetch/cascade 같은 ORM 세부는 persistence adapter 안에 묶어 두는 기준을 1분 멘탈모델, before/after, 헷갈림 방지 체크로 정리한 실전 문서

## DataJpaTest DB 차이 가이드

- [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)

> `@DataJpaTest`에서 H2로 충분한 경우와 Testcontainers로 실제 DB를 붙여야 하는 경우를 초심자 기준으로 먼저 나누고, DB 전용 쿼리를 옮길 최소 판단 기준과 시작 템플릿까지 바로 연결해 주는 beginner bridge guide
> 이번 QA 보강으로 Flyway/Liquibase 기반 운영 스키마와 테스트 `ddl-auto` 자동 생성 스키마가 왜 어긋나는지 4문항 체크리스트로 바로 확인할 수 있게 다듬었다.

## JPA Batch Config Pitfalls

- [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)

> `hibernate.jdbc.batch_size`, `flush()`/`clear()` 주기, `GenerationType.IDENTITY`가 왜 insert batching을 흔들고 왜 여전히 persistence adapter concern인지, 그리고 `saveAll`을 성급히 port로 승격하면 왜 계약 오해가 생기는지 before/after 예시로 정리한 beginner primer
> 이번 QA 보강으로 `IDENTITY` vs `SEQUENCE`를 "먼저 넣고 번호를 받는가 / 번호를 받고 넣는가"라는 3건 insert 표로 바로 비교할 수 있게 다듬었다.
> 이번 QA 보강으로 SQL 로그나 Hibernate statistics에서 batch 실행 흔적을 읽는 가장 짧은 확인 예시도 함께 붙였다.

## Repository Fake Design Guide

- [Repository Fake Design Guide](./repository-fake-design-guide.md)

> repository fake를 in-memory JPA clone이 아니라 outbound port semantics를 재현하는 test adapter로 설계하고, `save()`/중복/조회 계약만 남겨 use case test로 persistence 세부가 새지 않게 하는 가이드

## Aggregate Persistence Mapping Pitfalls

- [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md)

> 양방향 연관관계, `cascade`, `orphanRemoval`을 aggregate 규칙으로 오해할 때 생기는 초심자용 mapping 함정과 도메인 누수 신호를 정리한 primer

## Persistence Model Leakage Anti-Patterns

- [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)

> JPA `@Entity`가 API 응답, 애플리케이션 흐름, 도메인 규칙까지 침범할 때 생기는 leakage anti-pattern을 증상별 첫 처방과 common confusion까지 포함해 beginner 관점에서 정리한 문서

## JPA Lazy Loading and N+1 Boundary Smells

- [JPA Lazy Loading and N+1 Boundary Smells](./jpa-lazy-loading-n-plus-one-boundary-smells.md)

> lazy loading 자체보다 엔티티가 API 경계를 넘어갈 때 왜 `LazyInitializationException`, 숨은 N+1, fetch join 남발이 한 묶음으로 나타나는지 beginner 예시로 설명한 primer

## Query Model Separation for Read-Heavy APIs

- [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)

> 목록/상세 화면 때문에 write entity와 aggregate를 계속 늘리는 대신, 같은 DB 위에서도 query repository와 response model을 분리하는 CQRS-lite 도입 시점을 정리한 beginner primer

## Same-DB Query Repository Vs Separate Read Store

- [Same-DB Query Repository Vs Separate Read Store](./same-db-query-repository-vs-separate-read-store.md)

> 같은 DB query repository에서 멈춰도 되는 시점과, 같은 DB projection/view를 거쳐 진짜 separate read store로 올라가야 하는 시점을 초심자용 escalation ladder로 정리한 bridge primer

## Bulk Helper Ports vs Query Model Separation

- [Bulk Helper Ports vs Query Model Separation](./bulk-helper-ports-vs-query-model-separation.md)

> `findByIds` 같은 helper port가 command 보조 조회로 충분한 경우와, helper snapshot이 화면/query 책임을 빨아들이기 시작할 때 dedicated query repository/read model로 넘어가는 기준을 초심자 눈높이에서 비교한 bridge primer

## Helper Snapshot Bloat Vs Response DTO Separation

- [Helper Snapshot Bloat Vs Response DTO Separation](./helper-snapshot-bloat-vs-response-dto-separation.md)

> helper snapshot이 언제 command 지원 모델이 아니라 screen DTO처럼 비대해지는지, 그리고 command-support data와 API response DTO를 가장 작은 단계로 분리하는 방법을 초심자용 예시로 설명한 primer

## API 설계와 예외 처리

- [API 설계와 예외 처리](./api-design-error-handling.md)

> `@Valid` 같은 입력 형식 검증과 서비스/도메인 업무 규칙 검증을 왜 분리하는지, `400`과 `409`가 어떻게 갈리는지, `MethodArgumentNotValidException`의 필드별 `errors[]` 응답을 어떻게 읽는지 회원 가입·주문·예약 예시로 설명한 primer

## 409 vs 422 선택 기준 짧은 가이드

- [409 vs 422 선택 기준 짧은 가이드](./http-409-vs-422-selection-guide.md)

> 업무 규칙 위반 응답에서 `409 Conflict`와 `422 Unprocessable Content`를 어떻게 가를지, "서버 상태 충돌인지 요청 의미 오류인지"를 초심자용 decision table과 예약 예시로 짧게 정리한 bridge primer

## 테스트 전략과 테스트 더블

- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)

## 캐시, 메시징, 관측성

- [캐시, 메시징, 관측성](./cache-message-observability.md)

## Backend Delivery and Observability Foundations Primer

- [Backend Delivery and Observability Foundations Primer](./backend-delivery-observability-foundations-primer.md)

> project-stage 백엔드에서 logs, metrics, feature flag, rollout, rollback, incident response를 `변경을 내보내고 관찰하고 줄이는 한 흐름`으로 먼저 묶어 주는 beginner entrypoint primer

## DDD, Hexagonal Architecture, Consistency Boundary

- [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)

## DDD Bounded Context Failure Patterns

- [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)

## Event Sourcing, CQRS Adoption Criteria

- [Event Sourcing, CQRS Adoption Criteria](./event-sourcing-cqrs-adoption-criteria.md)

## Domain Event, Outbox, Inbox

- [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)

## Clean Architecture vs Layered Architecture, Modular Monolith

- [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)

## Monolith to MSA Failure Patterns

- [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)

## Technical Debt Refactoring Timing

- [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)

## Feature Flags, Rollout, Dependency Management

- [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)

## Deployment Rollout, Rollback, Canary, Blue-Green

- [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)

## Strangler Fig Migration, Contract, Cutover

- [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)

## API Versioning, Contract Testing, Anti-Corruption Layer

- [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)

## Anti-Corruption Layer Integration Patterns

- [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)

## API Contract Testing, Consumer-Driven

- [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)

## Contract Drift Detection and Rollout Governance

- [Contract Drift Detection and Rollout Governance](./contract-drift-detection-rollout-governance.md)

## Modular Monolith Boundary Enforcement

- [Modular Monolith Boundary Enforcement](./modular-monolith-boundary-enforcement.md)

> `api` 패키지 공개 범위, `internal` 은닉 규칙, 가벼운 ArchUnit 테스트로 모듈 경계를 실전에서 강제하는 starter guide

## Module API DTO Patterns

- [Module API DTO Patterns](./module-api-dto-patterns.md)

> 모듈 경계에서 command/query/result DTO와 domain object를 어떻게 구분할지, 30초 결정 흐름과 자주 헷갈리는 지점까지 포함해 주문-결제 예시로 설명하는 practical guide

## ArchUnit Brownfield Rollout Playbook

- [ArchUnit Brownfield Rollout Playbook](./archunit-brownfield-rollout-playbook.md)

> legacy 위반이 이미 많은 모놀리스에서 ArchUnit을 `baseline freeze -> fail-new-only -> ratchet -> hard fail` 순서로 도입하고 allowlist/예외 부채를 관리하는 playbook


## Shared Module Guardrails

- [Shared Module Guardrails](./shared-module-guardrails.md)

> `shared/common`을 기술적 공통 관심사와 명시적 shared kernel로만 좁히고, ownership, 입장 규칙, architecture lint로 도메인 덤프 공간을 막는 focused guide

## Feature Flag Cleanup and Expiration

- [Feature Flag Cleanup and Expiration](./feature-flag-cleanup-expiration.md)

## Idempotency, Retry, Consistency Boundaries

- [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)

## Branch by Abstraction, Feature Flag, Strangler Fig

- [Branch by Abstraction, Feature Flag, Strangler Fig](./branch-by-abstraction-vs-feature-flag-vs-strangler.md)

## Technology Radar and Adoption Governance

- [Technology Radar and Adoption Governance](./technology-radar-adoption-governance.md)

## Build vs Buy, Exit Cost, Integration Governance

- [Build vs Buy, Exit Cost, Integration Governance](./build-vs-buy-exit-cost-governance.md)

## Configuration Governance and Runtime Safety

- [Configuration Governance and Runtime Safety](./configuration-governance-runtime-safety.md)

## Service Template Trade-offs

- [Service Template Trade-offs](./service-template-tradeoffs.md)

> scaffold default, escape hatch, template drift를 어떤 운영 기록과 검증 지점에 같이 꽂아야 하는지 정리한 문서

## Service Bootstrap Governance

- [Service Bootstrap Governance](./service-bootstrap-governance.md)

> bootstrap command, catalog registration, PRR gate까지 초기 생성 시점의 삽입 지점을 묶어 보는 문서

## Lead Time, Change Failure, and Recovery Loop

- [Lead Time, Change Failure, and Recovery Loop](./lead-time-change-failure-recovery-loop.md)

## Data Migration Rehearsal, Reconciliation, Cutover

- [Data Migration Rehearsal, Reconciliation, Cutover](./data-migration-rehearsal-reconciliation-cutover.md)

## Team Cognitive Load and Boundary Design

- [Team Cognitive Load and Boundary Design](./team-cognitive-load-boundary-design.md)

## Non-Functional Requirements as Budgets

- [Non-Functional Requirements as Budgets](./non-functional-requirements-budgeting.md)

## Prototype, Spike, and Productionization Boundaries

- [Prototype, Spike, and Productionization Boundaries](./prototype-spike-productionization-boundaries.md)

## Migration Wave Governance and Decision Rights

- [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md)

## Cross-Service NFR Budget Negotiation

- [Cross-Service NFR Budget Negotiation](./cross-service-nfr-budget-negotiation.md)

## Decision Revalidation and Supersession Lifecycle

- [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)

## Operational Readiness Drills and Change Safety

- [Operational Readiness Drills and Change Safety](./operational-readiness-drills-and-change-safety.md)

## Architectural Governance Operating Model

- [Architectural Governance Operating Model](./architectural-governance-operating-model.md)

## Migration Carrying Cost and Cost of Delay

- [Migration Carrying Cost and Cost of Delay](./migration-carrying-cost-cost-of-delay.md)

## Platform Control Plane and Delegation Boundaries

- [Platform Control Plane and Delegation Boundaries](./platform-control-plane-delegation-boundaries.md)

## Platform Scorecards

- [Platform Scorecards](./platform-scorecards.md)

> platform 채택률만 보는 표가 아니라 `normal_path_health`, `break_glass_visibility`, `governance_spillover`를 나란히 둬 panel별 owner와 drilldown을 분리하는 문서

## Service Portfolio Lifecycle Governance

- [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)

## Architecture Council and Domain Stewardship Cadence

- [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)

## Migration Stop-Loss and Scope Reduction Governance

- [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md)

## Platform Policy Ownership and Override Governance

- [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)

## Service Split, Merge, and Absorb Evolution Framework

- [Service Split, Merge, and Absorb Evolution Framework](./service-split-merge-absorb-evolution-framework.md)

## Team APIs and Interaction Modes in Architecture

- [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)

## Change Ownership Handoff Boundaries

- [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)

> ownership 이전을 코드 전달이 아니라 support/on-call/runbook과 함께 넘기는 staged handoff와 anti-pattern 중심으로 정리한 문서

## Service Criticality Tiering and Control Intensity

- [Service Criticality Tiering and Control Intensity](./service-criticality-tiering-control-intensity.md)

## Service Deprecation and Sunset Lifecycle

- [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)

> deprecation을 단순 삭제가 아니라 consumer migration과 sunset exception의 retire-vs-absorb 판정까지 포함한 lifecycle로 정리한 문서

## Backward Compatibility Waivers and Consumer Exception Governance

- [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)

> compatibility waiver를 expiry/compensating control뿐 아니라 repeated waiver side path의 retire-vs-absorb 판정과 연결한 문서

## Consumer Exception Registry Templates

- [Consumer Exception Registry Templates](./consumer-exception-registry-templates.md)

> registry row, waiver request, review packet, support guidance에 같은 필드를 재사용하는 template insertion point를 정리한 문서

## Consumer Exception Operating Model

- [Consumer Exception Operating Model](./consumer-exception-operating-model.md)

> consumer exception을 registry, state machine, review cadence, automation quality gate로 묶고, repeated exception path를 retire할지 absorb할지 같은 언어로 판정하게 만드는 통합 operating model 문서

## Deprecation Enforcement, Tombstone, and Sunset Guardrails

- [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)

> warning, allowlist, tombstone guardrail을 waiver path와 묶고 sunset bypass를 retire할지 structured data를 absorb할지 구분하는 enforcement 문서

## Rollout Guardrail Profiles, Auto-Pause, and Manual Resume

- [Rollout Guardrail Profiles, Auto-Pause, and Manual Resume](./rollout-guardrail-profiles-auto-pause-resume.md)

## Incident Feedback to Policy and Ownership Closure

- [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)

## Policy as Code Adoption Order and Sequencing

- [Policy as Code Adoption Order and Sequencing](./policy-as-code-adoption-order-and-sequencing.md)

> policy-as-code를 어떤 순서로 넓혀야 하는지, low-friction baseline에서 lifecycle and business guardrail로 넘어가는 adoption wave를 정리한 문서

## Policy as Code Rollout and Adoption Stages

- [Policy as Code Rollout and Adoption Stages](./policy-as-code-rollout-adoption-stages.md)

## Override Burn-Down and Exemption Debt

- [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)

> override debt를 age와 repeated owner만이 아니라 exit condition, policy scope drift, governance health 관점으로 읽는 문서

## Support SLA and Escalation Contracts

- [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)

> support contract를 단일 응답 시간 표기가 아니라 first response, ownership acceptance, escalation ladder, handoff clock까지 포함한 운영 계약으로 설명한 문서

## Shadow Process Detection Signals

- [Shadow Process Detection Signals](./shadow-process-detection-signals.md)

> repeated override, 사람 의존 승인, off-plane data store 같은 signal을 confidence와 intake 기준까지 포함해 shadow catalog 후보로 올리는 문서

## Shadow Process Catalog and Retirement

- [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)

> detection signal에서 catalog intake, retire/officialize/absorb 판정, override scorecard 연결까지 shadow retirement pipeline을 설명하는 문서

## Shadow Process Catalog Entry Schema

- [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)

> signal evidence, target state, review forum, retirement tracking을 같은 catalog entry로 묶어 detection에서 종료까지 끊기지 않게 만드는 schema 문서

## Shadow Review Packet Template

- [Shadow Review Packet Template](./shadow-review-packet-template.md)

> shadow catalog entry review에 필요한 최소 packet field와 `decision / execution-risk / verification` agenda section을 고정해 forum별 판단 흔들림을 줄이는 문서

## Shadow Packet Automation Mapping

- [Shadow Packet Automation Mapping](./shadow-packet-automation-mapping.md)

> shadow catalog entry field를 review-packet row로 자동 투영할 때 section routing, required/optional fallback, quality gate를 고정하는 문서

## Shadow Review Outcome Template

- [Shadow Review Outcome Template](./shadow-review-outcome-template.md)

> shadow review forum 결과를 `source_packet_ref`, `from_state -> to_state`, `field_updates`, `decision_owner`, `next_review_at`로 남겨 packet 입력과 state-transition 출력을 같은 계약으로 닫는 문서

## Shadow Forum Escalation Rules

- [Shadow Forum Escalation Rules](./shadow-forum-escalation-rules.md)

> blocked shadow entry와 high-blast shared workaround를 local stewardship forum에 계속 둘지 architecture council로 올릴지 `blocked_duration`, `impacted_domains`, `affected_teams`, shared gate change threshold로 고정하는 문서

## Shadow Catalog Lifecycle States

- [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)

> detected, decision_pending, temporary_hold, blocked, verification_pending, retired를 분리해 shadow entry가 어디서 멈췄는지와 언제 진짜 종료되는지 보이게 만드는 state machine 문서

## Shadow Catalog Review Cadence Profiles

- [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)

> `detected`, `temporary_hold`, `blocked`, `verification_pending` 상태별 기본 review frequency, owner expectation, escalation SLA를 묶어 shadow backlog 정체와 가짜 close를 줄이게 하는 운영 프로파일 문서

## Shadow Lifecycle Scorecard Metrics

- [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)

> `lifecycle_state` aging, `blocked_duration`, hold expiry risk, retirement verification health를 같은 dashboard 언어로 묶어 shadow backlog 정체와 가짜 retirement를 같이 보이게 하는 문서

## Temporary Hold Exit Criteria

- [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)

> `temporary_hold`가 언제 만료돼 resume_state로 복귀해야 하는지, 언제 bounded extension이 정당한지, repeated hold가 언제 absorb/officialize escalation 신호로 바뀌는지 concrete example로 정리한 문서

## Manual Path Ratio Instrumentation

- [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)

> DM 승인, spreadsheet 상태 저장, off-plane artifact 사용을 request 단위 fact로 정규화해 manual_path_ratio와 shadow_candidate_count를 실제로 계산 가능하게 만드는 계측 문서

## Mirror Lag SLA Calibration

- [Mirror Lag SLA Calibration](./mirror-lag-sla-calibration.md)

> approval, sheet, off-plane artifact별 `mirror_lag` band와 공통 breach class를 고정해 manual breach 분류를 팀 간 비교 가능한 scorecard 언어로 맞추는 문서

## Shadow Candidate Promotion Thresholds

- [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)

> repeated manual-path bundle을 `observe / watchlist / promote / fast_track` tier와 confidence cap으로 나눠 shadow catalog intake 승격 시점을 고정하는 문서

## Threshold Override Governance

- [Threshold Override Governance](./threshold-override-governance.md)

> `shadow_candidate` / `fast_track` / `mirror_breach` 같은 공통 threshold를 언제 workflow별로 덮어쓸 수 있는지, 누가 승인하고 `expires_at`, renewal cap, scorecard review로 어떻게 되돌리는지 정리한 문서

## Shadow Promotion Snapshot Schema Fields

- [Shadow Promotion Snapshot Schema Fields](./shadow-promotion-snapshot-schema-fields.md)

> shadow catalog entry와 review packet에 `promotion_snapshot`, `promotion_tier`, `promotion_threshold_summary` 같은 최소 필드를 고정해 tier/confidence 판단 근거를 replay 가능하게 남기는 문서

## Break-Glass Path Segmentation

- [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)

> emergency와 break-glass workflow를 scorecard에서 계속 보이게 하면서도 normal manual_path_ratio와 shadow retirement proof hard-gate denominator를 오염시키지 않도록 path segment, denominator scope, fallback visibility sidecar를 분리하는 문서

## Emergency Misclassification Signals

- [Emergency Misclassification Signals](./emergency-misclassification-signals.md)

> repeated emergency path가 hidden workflow인지, time-box를 놓친 override debt인지 signal rule로 갈라 shadow backlog와 override backlog로 재분류하는 문서

## Break-Glass Reentry Governance

- [Break-Glass Reentry Governance](./break-glass-reentry-governance.md)

> authorized break-glass 이후 `reentry_slo`, ownership handoff, closeout audit field를 어떻게 강제해야 emergency mode가 semi-permanent override로 굳지 않는지 정리한 문서

## Shadow Retirement Proof Metrics

- [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)

> `closed`와 `retired`를 분리하고, manual_path_ratio, exception burndown, audit-log coverage, recurrence, authoritative off-plane artifact 같은 hard gate를 어떤 threshold와 verification window로 봐야 하는지 정리한 문서

## Shadow Retirement Scorecard Schema

- [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)

> shadow retirement hard gate, `verification_window`, `verdict_record`를 canonical YAML/JSON field set으로 고정해 proof 문서, catalog entry, lifecycle dashboard, review outcome example이 같은 key를 재사용하게 만드는 문서

## Shadow Catalog Reopen and Successor Rules

- [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)

> recurrence triage를 same-path/same-replacement/same-proof continuity로 가르고, active-state recurrence는 same-row rollback을 먼저 보며, successor가 필요할 때는 새 baseline과 adjacency-preserving predecessor/successor 링크를 append-only로 남기는 문서

## Tombstone Response Template and Consumer Guidance

- [Tombstone Response Template and Consumer Guidance](./tombstone-response-template-and-consumer-guidance.md)

> error envelope, migration docs, support runbook, dashboard annotation에 tombstone contract를 어디에 꽂을지 정리한 문서

## Policy Candidate Backlog Scoring and Priority

- [Policy Candidate Backlog Scoring and Priority](./policy-candidate-backlog-scoring-and-priority.md)

> policy 후보를 impact, readiness, friction, dependency unlock 기준으로 점수화해 adoption queue와 rollout next action을 정리하는 문서

## Consumer Exception State Machine and Review Cadence

- [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md)

## Override Burn-Down Review Cadence and Scorecards

- [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)

> age bucket과 repeated owner뿐 아니라 manual path ratio, shadow candidate count까지 포함해 burn-down과 구조 개선을 같이 읽는 문서

## Support Operating Models: Self-Service, Office Hours, On-Call

- [Support Operating Models: Self-Service, Office Hours, On-Call](./support-operating-models-self-service-office-hours-oncall.md)

> self-service, office hours, business-hours, on-call을 lane으로 나누고 cutover surge profile과 lane handoff 규칙까지 다루는 운영 모델 문서

## Shadow Process Officialization and Absorption Criteria

- [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)

> officialize, absorb, retire, hold를 적합성 테스트와 guardrail 기준으로 나누고 rollout/deprecation/migration worked example까지 붙여 판정 감각을 보강하는 문서

## Consumer Exception Registry Quality and Automation

- [Consumer Exception Registry Quality and Automation](./consumer-exception-registry-quality-automation.md)

---

## 보조 primer

아래 구간은 최신 catalog와 별개로 남아 있는 보조 primer 성격의 학습 자료다.

## 애자일 개발 프로세스

아래의 자료에서 자세한 설명과 코드를 볼 수 있다.

- 작성자 이세명 | [Agile Software Development](./materials/CS_Agile.pdf)
- 작성자 정희재 | [eXtreme Programming(XP)](./eXtremeProgramming.md)

---

## 질의응답

_질문에 대한 답을 말해보며 공부한 내용을 점검할 수 있으며, 클릭하면 답변 내용을 확인할 수 있습니다._

<!-- 애자일, 요구사항, 프로젝트 관리 -->

<details>
<summary>애자일처럼 소프트웨어 공학에서의 개발 프로세스를 적용하여 프로젝트를 진행한 경험이 있으신가요? 어떻게 진행했나요?</summary>
<p>

지원자의 경험을 스크럼, XP, 폭포수 모델 개발 방법 등의 진행 과정을 설명하면 됩니다. 아래는 답안의 한 예시로 참조하시면 되겠습니다.

매일매일 짧게라도 회의를 진행하여 계획하고, 리팩토링을 두려워하지않고 프로토타입을 만드는 것을 먼저 생각했다.
사용할 기능에 대한 우선순위를 두어 개발 주기마다 적용할 기능의 목록을 만들어보았고 적용시킨 후 팀원들의 리뷰를 통하여 제품을 학습하고 이해하였다. 이 후 또 다음 백로그를 준비하는 스크럼 방법을 사용했다.

</p>
</details>
<details>
<summary>애자일 개발 방법이 생겨나게 된 배경에 대해서 설명 해주실 수 있나요?</summary>
<p>

전통적인 프로그램 개발 방법론에서는 대규모 프로젝트를 진행할 때 개발보다는 문서화, 회의, 설계 등의 업무에 더 많은 시간을 소비했다.
또한 전통적인 개발 방법론은 소비자의 요구사항이 변동되었을 때 그에 대해 빠르게 대응하지 못하는 단점이 있었다.
애자일은 이러한 전통적인 방법론보다 더 나은 방법을 찾고자 하는 데에서 시작되었다.

</p>
</details>

## 질의응답: 프로젝트/테스트

<details>
<summary>요즘 많은 기업들이 애자일 프로세스를 따르고 있습니다. 왜 그럴까요?</summary>
<p>

- 변화에 대해 신속하고 능동적인 대응이 가능합니다.
- 이해관계자들과 효과적인 소통이 가능합니다.
- 개발자들이 개발에 좀 더 집중할 수 있습니다.

</p>
</details>

<details>
<summary>개발 단계를 기획-설계-구현-테스트 이렇게 네 가지 단계로 분류한다고 했을 때 본인이 생각하기에 가장 시간과 비용이 많이 요구되는 단계는 어디라고 생각 하시나요? 그 이유와 함께 답변 부탁드립니다.</summary>
<p>

2021년 현재 소프트웨어 생명 주기 단계 중 시간과 비용이 가장 많이 요구되는 단계는 '테스트' 단계입니다.
이해하기 쉽게 예시를 들어 설명하겠습니다.

자동차에 관한 소프트웨어라면 처음부터 안전을 우선순위로 설계하여 구현함에도 실제 테스트단계에서 일어나는 예외사항에 많은 시간과 비용이 들어갑니다. 이상이 일어날 시에 불가피한 리팩토링은 많은 시간과 비용을 사용하여야 합니다. 또한 자동차 뿐만 아니라 스마트폰 및 게임에서도 테스트가 시간과 비용이 가장 많이 요구되었습니다.

</p>
</details>
<details>
<summary>Validation과 Verification 이라는게 있습니다. 한국어로 풀이하면 둘다 검증, 확인이라는 뜻으로 똑같이 해석이 되는데 소프트웨어공학의 입장에서 보면 이 두 단어는 서로 비슷하지만 다른 뜻을 가지고 있습니다. 이 둘의 차이점에 대해서 설명해주실 수 있나요?</summary>
<p>

- Validation : 소프트웨어의 기능과 목적이 요구사항을 반영하는가, 일치하는가, 누락된 요구사항은 없는가
- Verification : 소프트웨어의 입력에 대해 출력 값이 요구사항에서 원하는 바와 일치하는가 즉, 버그가 없는가

</p>

</details>

## 한 줄 정리

README starter 질문 문구를 그대로 검색해 첫 primer 1개를 고르고, 그 문서의 다음 한 걸음 링크로만 확장하면 된다.

## 한 줄 정리

README starter 질문 문구를 그대로 검색해 첫 primer 1개를 고르고, 그 문서의 다음 한 걸음 링크로만 확장하면 된다.

<details>
<summary>요구사항 명세서란 무엇인가요? 왜 필요한가요?</summary>
<p>

개발할 소프트웨어의 기능적, 비기능적 요구사항을 서술해 놓은 것을 의미합니다. 이해 관계자와 소프트웨어 개발자들의 의사소통 도구로 사용됩니다.
- 제품의 기능에 대한 기본적인 합의를 수월하게 도출해낼 수 있습니다.
- 각 기능을 개발하기 위한 비용과 스케줄을 예측할 수 있는 지표가 되기도 합니다.
- 효율적인 개발 계획을 세울 수 있고 제품 테스트, 검증을 위한 베이스를 제공해줍니다.
- 제품의 성능 향상을 위한 기반이 되는 자료 입니다.

</p>

</details>
