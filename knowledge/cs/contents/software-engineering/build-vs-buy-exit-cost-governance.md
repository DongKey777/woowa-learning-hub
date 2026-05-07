---
schema_version: 3
title: Build vs Buy Exit Cost Integration Governance
concept_id: software-engineering/build-vs-buy-governance
canonical: true
category: software-engineering
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- build-vs-buy
- vendor-lock-in
- integration-governance
aliases:
- Build vs Buy Exit Cost Integration Governance
- build vs buy
- exit cost governance
- vendor lock-in decision
- managed service adoption
- buy decision integration review
symptoms:
- build vs buy를 초기 구현 비용 비교로만 보고 운영 책임, 데이터 소유권, 보안/규제, exit cost를 함께 계산하지 않아
- 외부 솔루션 SDK와 proprietary API를 내부 도메인 전역에 퍼뜨려 나중에 교체 비용과 vendor lock-in을 키워
- 핵심 도메인 정책을 솔루션 설정값이나 workflow DSL 안에 묻어 domain decision ownership을 외부화해
intents:
- comparison
- design
- deep_dive
prerequisites:
- software-engineering/dependency-governance-sbom
- software-engineering/architecture-review-anti-patterns
next_docs:
- software-engineering/shared-library-vs-platform-service
- software-engineering/platform-paved-road
- software-engineering/migration-funding-model
linked_paths:
- contents/software-engineering/shared-library-vs-platform-service-tradeoffs.md
- contents/software-engineering/dependency-governance-sbom-policy.md
- contents/software-engineering/architecture-review-anti-patterns.md
- contents/software-engineering/migration-funding-model.md
- contents/software-engineering/platform-paved-road-tradeoffs.md
- contents/software-engineering/anti-corruption-layer-integration-patterns.md
confusable_with:
- software-engineering/shared-library-vs-platform-service
- software-engineering/dependency-governance-sbom
- software-engineering/platform-paved-road
forbidden_neighbors: []
expected_queries:
- build vs buy 판단에서 초기 개발 비용보다 integration cost, operational responsibility, exit cost를 같이 봐야 하는 이유가 뭐야?
- 외부 SaaS나 managed service를 도입할 때 data portability와 offboarding plan을 왜 초기 decision record에 넣어야 해?
- vendor SDK를 내부 코드 곳곳에 퍼뜨리지 않고 ACL 뒤에 두면 exit cost가 어떻게 줄어?
- buy 결정에서도 결제 승인 정책, 회원 상태 전이 같은 domain decision을 외부화하면 왜 위험해?
- build buy hybrid 선택을 domain differentiation, integration surface, lock-in 기준으로 비교해줘
contextual_chunk_prefix: |
  이 문서는 build vs buy 결정을 initial implementation cost가 아니라 integration governance, vendor lock-in, data portability, operating responsibility, exit cost까지 포함해 비교하는 advanced chooser다.
---
# Build vs Buy, Exit Cost, Integration Governance

> 한 줄 요약: build vs buy 판단은 구현 비용 비교가 아니라, 통합 복잡도와 운영 책임, 그리고 언젠가 떠나야 할 때의 exit cost까지 같이 보는 의사결정이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shared Library vs Platform Service Trade-offs](./shared-library-vs-platform-service-tradeoffs.md)
> - [Dependency Governance and SBOM Policy](./dependency-governance-sbom-policy.md)
> - [Architecture Review Anti-Patterns](./architecture-review-anti-patterns.md)
> - [Migration Funding Model](./migration-funding-model.md)
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)

> retrieval-anchor-keywords:
> - build vs buy
> - exit cost
> - vendor lock-in
> - managed service adoption
> - integration governance
> - buy decision
> - data portability
> - replacement cost

## 핵심 개념

외부 솔루션을 도입하면 개발 속도는 빨라질 수 있다.
하지만 코드를 안 쓴다고 책임이 사라지는 것은 아니다.

build vs buy에서 같이 봐야 하는 것:

- 초기 구현 시간
- 운영 책임
- 보안/규제 적합성
- 데이터 이동 가능성
- 계약 종료 후 대체 비용

즉 buy는 "만들지 않는다"가 아니라, **다른 형태의 결합을 선택한다**는 뜻이다.

---

## 깊이 들어가기

### 1. buy는 개발 비용을 줄여도 통합 비용은 남는다

구매 솔루션은 기능을 빨리 주지만, 실제 시스템에 붙이는 순간 복잡도가 생긴다.

예:

- 인증 모델이 우리 도메인과 안 맞음
- 이벤트 모델이 우리 계약과 다름
- 장애 대응 방식이 내부 runbook과 다름
- 과금 단위가 예상보다 불리함

따라서 build vs buy는 제품 기능 비교표보다 **integration design review**에 가깝다.

### 2. exit cost를 같이 보지 않으면 판단이 왜곡된다

도입은 쉽지만 철수가 어려운 솔루션이 많다.

exit cost를 키우는 요소:

- 데이터 export 제약
- proprietary API
- 강한 SDK 종속
- 계약 구조상 장기 락인
- 운영 절차가 공급자에 맞춰진 경우

즉 buy의 진짜 가격은 onboarding 비용이 아니라 **offboarding 비용까지 포함한 총비용**이다.

### 3. buy해도 domain decision은 외주화되면 안 된다

외부 솔루션이 잘하는 부분은 위임해도 되지만, 핵심 정책까지 맡기면 위험하다.

예:

- 결제 승인 정책
- 회원 상태 전이 규칙
- 내부 정산 기준
- 알림 발송 우선순위

도메인 판단이 솔루션 설정값 안에 묻히면 나중에 교체가 훨씬 어려워진다.

### 4. 계약과 데이터 소유권을 초기에 정리해야 한다

buy 결정 시 꼭 봐야 할 질문:

- 데이터 원본은 누구인가
- export format은 무엇인가
- audit log를 확보할 수 있는가
- 장애 시 수동 운영이 가능한가
- replacement plan 없이 critical path에 올려도 되는가

외부 솔루션은 코드가 아니라 **운영 경계**를 추가하는 것이다.

### 5. 좋은 buy 결정에는 sunset 조건이 있다

아무도 솔루션을 도입할 때 떠날 계획을 세우고 싶어 하지 않는다.
하지만 그 계획이 있어야 락인을 줄일 수 있다.

예:

- 1년 뒤 재평가
- 특정 비용/성능 기준 초과 시 대체 검토
- 핵심 데이터는 내부 canonical schema로 복제
- 연동은 anti-corruption layer 뒤에 둠

즉 build vs buy는 단발성 구매가 아니라 **수명주기 관리**다.

---

## 실전 시나리오

### 시나리오 1: 검색 기능을 외부 서비스로 산다

색인 품질과 운영 편의는 좋아지지만, 검색 이벤트와 도메인 스키마 변환 비용이 계속 든다.
anti-corruption layer 없이 SDK를 퍼뜨리면 exit cost가 커진다.

### 시나리오 2: 인증 솔루션을 도입한다

로그인 자체는 빨라지지만, 회원 상태와 권한 모델을 외부에 끌려가면 제품 정책 변경이 느려진다.

### 시나리오 3: 워크플로 엔진을 구매한다

초기 생산성은 높지만, 핵심 승인 로직이 엔진 DSL 안에 잠기면 나중에 옮기기 어렵다.

---

## 코드로 보기

```yaml
buy_decision:
  problem: "search relevance and indexing"
  owner: commerce-platform
  integration_surface:
    - product_catalog_sync
    - search_event_pipeline
    - admin_console
  exit_plan:
    data_export: daily_snapshot
    abstraction: anti_corruption_layer
    review_at: 2026-10-01
```

좋은 buy 결정은 도입 이유뿐 아니라 철수 경로도 같이 적는다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| build | 통제가 높다 | 초기 비용이 크다 | 도메인 차별성이 클 때 |
| buy | 빠르다 | 락인과 통합 비용이 있다 | 비핵심 기능을 빨리 붙일 때 |
| hybrid | 속도와 통제를 섞을 수 있다 | 경계 설계가 어렵다 | 핵심 정책은 내부에 두고 실행만 외부화할 때 |

build vs buy의 핵심은 속도 비교가 아니라, **누가 어떤 책임과 결합을 떠안는지 명확히 보는 것**이다.

---

## 꼬리질문

- 이 솔루션을 빼고도 1년 뒤 살아남을 수 있는가?
- 핵심 도메인 규칙이 공급자 설정에 묻히지 않는가?
- 데이터 export와 audit는 정말 가능한가?
- integration surface가 예상보다 넓지 않은가?

## 한 줄 정리

Build vs buy, exit cost, integration governance는 외부 솔루션 도입을 기능 비교가 아니라 결합, 데이터, 철수 비용까지 포함한 수명주기 선택으로 보는 관점이다.
