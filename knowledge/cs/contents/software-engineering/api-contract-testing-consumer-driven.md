---
schema_version: 3
title: API Contract Testing Consumer Driven
concept_id: software-engineering/api-contract-testing
canonical: true
category: software-engineering
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 89
mission_ids:
- missions/payment
review_feedback_tags:
- contract-testing
- consumer-driven-contract
- api-compatibility
aliases:
- API Contract Testing Consumer Driven
- consumer-driven contract testing
- Pact contract test
- Spring Cloud Contract
- provider verification
- consumer expectation test
- 컨슈머 주도 계약 테스트
symptoms:
- provider 내부 테스트가 통과했으니 실제 consumer가 기대하는 필드와 enum 의미도 안전하다고 가정해
- API 응답 스냅샷이나 통합 테스트만으로 소비자 호환성 깨짐을 배포 전 잡을 수 있다고 생각해
- 계약 파일이 늘어나도 owner, broker, verification scope, breaking change policy 없이 운영해 유지비가 폭증해
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- software-engineering/api-versioning-contracts-acl
- software-engineering/backward-compatibility-gates
next_docs:
- software-engineering/contract-registry-governance
- software-engineering/consumer-exception-model
- software-engineering/compatibility-waiver-governance
linked_paths:
- contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md
- contents/software-engineering/backward-compatibility-test-gates.md
- contents/software-engineering/contract-registry-governance.md
- contents/software-engineering/consumer-exception-operating-model.md
- contents/software-engineering/backward-compatibility-waiver-consumer-exception-governance.md
- contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md
- contents/software-engineering/repository-dao-entity.md
confusable_with:
- software-engineering/backward-compatibility-gates
- software-engineering/contract-registry-governance
- software-engineering/api-lifecycle-stage
forbidden_neighbors: []
expected_queries:
- consumer-driven contract testing은 provider test나 integration test와 무엇이 달라?
- Pact나 Spring Cloud Contract는 소비자가 기대하는 필드와 provider verification을 어떻게 연결해?
- API enum 삭제나 의미 변경 같은 breaking change를 계약 테스트로 어떻게 먼저 잡아?
- 계약 테스트가 너무 많아질 때 contract broker owner verification scope를 어떻게 관리해야 해?
- API versioning과 backward compatibility gate, consumer contract test를 함께 운영하는 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 consumer-driven API contract testing을 consumer expectations, Pact/Spring Cloud Contract, provider verification, contract broker, backward compatibility gate 관점에서 설명하는 advanced deep dive다.
---
# API Contract Testing, Consumer-Driven

> 한 줄 요약: 계약 테스트는 "응답이 나온다"가 아니라, 소비자와 제공자 사이의 깨지기 쉬운 약속을 자동으로 지키게 하는 장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Deployment, Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)

> retrieval-anchor-keywords:
> - API contract testing
> - consumer-driven contracts
> - CDC test
> - Pact
> - Spring Cloud Contract
> - provider verification
> - consumer expectations
> - contract broker
> - 컨슈머 주도 계약

## 핵심 개념

Contract testing은 API의 구조와 의미를 테스트로 고정하는 방식이다.
Consumer-driven contract testing은 그중에서도 **소비자가 필요로 하는 계약을 먼저 정의하고, 제공자가 이를 만족하는지 검증**하는 방식이다.

이 접근이 필요한 이유는 명확하다.

- 문서만 믿으면 실제 클라이언트가 기대하는 필드가 빠질 수 있다
- 통합 테스트만으로는 버전 호환성 깨짐을 늦게 발견한다
- 마이크로서비스가 늘수록 "내가 바꾼 응답"이 누굴 깨는지 보이지 않는다

즉, 계약 테스트는 단순히 API를 테스트하는 게 아니라 **배포의 안전장치**를 만드는 것이다.

## 깊이 들어가기

### 1. Provider test와 Consumer test는 다르다

Provider test는 제공자 내부 기준으로 계약을 확인한다.
Consumer-driven contract test는 소비자 관점에서 필요한 필드를 남기고 나머지를 제거한다.

```text
Consumer -> Pact/contract -> Provider verification
```

이 차이가 중요한 이유는, 제공자 기준 테스트는 "내가 생각한 API"만 통과시킬 수 있기 때문이다.

### 2. 과도한 계약 테스트도 문제다

모든 엔드포인트에 계약 테스트를 다 걸면:

- 테스트 유지비가 급증한다
- 소비자 수가 많아질수록 검증 작업이 길어진다
- 단일 서비스 변경인데도 여러 계약 파일을 갱신해야 한다

그래서 계약 테스트는 **변경이 자주 깨지는 경계**에 집중해야 한다.

### 3. 버전 관리와 계약 테스트의 관계

API versioning이 계약의 수명을 늘려주지만, 버전을 늘리는 것만으로 호환성이 생기지는 않는다.

- 새 필드는 대체로 안전하다
- 삭제와 의미 변경은 위험하다
- enum 확장도 클라이언트 파싱에 따라 깨질 수 있다

계약 테스트는 이런 변화가 실제 소비자에 어떤 영향을 주는지 먼저 잡아낸다.

## 실전 시나리오

### 시나리오 1: 주문 서비스 응답 필드 삭제

결제 팀은 `orderStatus` 필드를 더 이상 쓰지 않는다고 생각해서 제거했다.
하지만 배송 팀 대시보드는 여전히 그 필드를 기준으로 상태를 계산하고 있었다.

문서만 있었으면 배포 후에야 깨진다.
계약 테스트가 있으면 소비자 검증 단계에서 멈춘다.

### 시나리오 2: enum 의미 변경

`READY_FOR_SHIPPING`을 `READY`로 줄인 변경은 내부에서는 사소해 보이지만, 소비자 파서는 문자열 매칭에 의존하고 있을 수 있다.

이런 변경은 통합 테스트보다 계약 테스트에서 먼저 드러난다.

### 시나리오 3: anti-corruption layer와 계약 테스트

외부 시스템과 직접 붙으면 계약이 흘러들어와 도메인을 오염시킨다.
ACL을 두면 외부 계약 변경과 내부 도메인 변경을 분리할 수 있다.

계약 테스트는 ACL 앞단에서 "외부와의 약속"을 고정하는 데 특히 유용하다.

## 코드로 보기

### 소비자 계약 예시

```json
{
  "consumer": "delivery-service",
  "provider": "order-service",
  "request": {
    "method": "GET",
    "path": "/orders/123"
  },
  "response": {
    "status": 200,
    "body": {
      "id": 123,
      "status": "PAID",
      "totalAmount": 45000
    }
  }
}
```

### 검증 포인트

```java
// 제공자 검증 시 핵심은 "소비자가 요구한 필드가 모두 있는가"다.
assertThat(response.body())
    .containsKey("id")
    .containsKey("status")
    .containsKey("totalAmount");
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| 통합 테스트만 | 이해하기 쉽다 | 깨짐을 늦게 발견한다 | 작은 서비스 |
| 스냅샷 테스트 | 빠르게 확인 가능 | 의미보다 형태에 취약하다 | UI/JSON이 거의 고정일 때 |
| Consumer-driven contract | 소비자 호환성을 정확히 잡는다 | 유지비가 높다 | 팀 간 API 변경이 잦을 때 |
| 양방향 contract | 제공/소비를 함께 맞춘다 | 복잡도가 크다 | API 플랫폼 운영 시 |

## 꼬리질문

- 계약 테스트와 스냅샷 테스트의 차이를 실무 장애 기준으로 설명할 수 있는가?
- provider 기준 테스트만으로는 왜 소비자 호환성을 보장하지 못하는가?
- 계약 파일이 너무 많아질 때 운영 정책은 어떻게 가져갈 것인가?
- API 버전 업과 계약 테스트를 함께 운영할 때 무엇을 먼저 깨야 하는가?

## 한 줄 정리

Consumer-driven contract testing은 배포 전에 소비자 호환성을 깨지 않도록 API 경계를 테스트로 고정하는 방법이다.
