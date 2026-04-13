# API Lifecycle Stage Model

> 한 줄 요약: API는 생성과 버전만 관리하면 끝나는 것이 아니라, draft부터 retired까지 어떤 단계에 있는지 명확히 정의해야 소비자와 운영이 같은 언어로 움직인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [Deprecation Communication Playbook](./deprecation-communication-playbook.md)
> - [Backward Compatibility Test Gates](./backward-compatibility-test-gates.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)

> retrieval-anchor-keywords:
> - API lifecycle
> - draft
> - active
> - deprecated
> - sunset
> - retired
> - lifecycle stage model
> - contract governance

## 핵심 개념

API lifecycle stage model은 API의 "버전 번호"와 "운영 상태"를 분리해서 보는 틀이다.

버전은 무엇이 바뀌었는지를 말하고, stage는 지금 그 API를 어떻게 다뤄야 하는지를 말한다.

예:

- draft: 아직 외부 소비자에게 약속하지 않음
- active: 공식 계약으로 운영 중
- deprecated: 새 소비자 유입 중단
- sunset: 종료 예정, migration 진행 중
- retired: 더 이상 지원하지 않음

이 구분이 없으면, 같은 v1이라도 운영 정책이 혼란스러워진다.

---

## 깊이 들어가기

### 1. version과 stage는 서로 다른 축이다

version은 payload 또는 behavior의 변경 단위를 나타낸다.
stage는 지원 정책을 나타낸다.

즉:

- v1 active
- v1 deprecated
- v2 active

가 동시에 가능하다.

### 2. stage는 소비자 커뮤니케이션과 연결되어야 한다

stage가 바뀌면 다음도 바뀌어야 한다.

- 공지 문구
- contract registry 상태
- release gate
- support 정책

stage만 바뀌고 주변 시스템이 따라오지 않으면 운영이 흔들린다.

### 3. stage transition에는 조건이 필요하다

stage는 마음대로 오르내리면 안 된다.

대표 조건:

- deprecated로 바꿀 때: 새 대체 API가 존재해야 한다
- sunset으로 바꿀 때: 주요 consumer migration이 시작돼야 한다
- retired로 바꿀 때: 소비자 호출이 사실상 0이어야 한다

### 4. stage model은 registry와 결합해야 한다

API가 많아질수록 stage를 문서로만 유지할 수 없다.

필요한 메타데이터:

- owner
- consumer list
- stage
- deprecation date
- sunset date
- replacement API

이 정보는 [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)와도 연결된다.

### 5. stage model은 test gate와 함께 가야 한다

active API는 backward compatibility gate를 통과해야 하고, deprecated API는 새 consumer를 받지 않도록 막아야 한다.

즉 stage는 선언이 아니라 **실제 정책 상태**여야 한다.

---

## 실전 시나리오

### 시나리오 1: 새로운 API를 공개한다

처음엔 draft로 두고 내부 consumer만 시험한 뒤 active로 전환한다.

### 시나리오 2: 구 API를 종료한다

deprecated -> sunset -> retired로 단계적 전환을 거친다.

### 시나리오 3: 같은 버전인데 정책이 다르다

v1이라도 stage가 deprecated면 신규 연동은 허용하지 않아야 한다.

---

## 코드로 보기

```yaml
api:
  name: order-detail
  version: v2
  stage: active
  replacement: order-detail-v3
```

stage는 설명이 아니라 실행 규칙에 반영돼야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| version만 관리 | 단순하다 | 지원 정책이 흐려진다 | 아주 작은 시스템 |
| stage만 관리 | 운영은 쉬워진다 | 형식 변화가 보이지 않는다 | 내부 도구 |
| version + stage | 가장 명확하다 | 메타데이터가 늘어난다 | 외부 소비자가 많을 때 |

API lifecycle stage model은 기능 분류가 아니라 **지원 정책을 명시하는 운영 체계**다.

---

## 꼬리질문

- version과 stage를 누가 각각 소유하는가?
- draft에서 active로 갈 때 무엇이 검증되어야 하는가?
- deprecated stage의 신규 consumer를 어떻게 막을 것인가?
- retired 전환 조건을 어떤 지표로 판단할 것인가?

## 한 줄 정리

API lifecycle stage model은 버전과 지원 상태를 분리해, API를 어떻게 다뤄야 하는지 조직 전체가 같은 규칙으로 보게 만드는 체계다.
