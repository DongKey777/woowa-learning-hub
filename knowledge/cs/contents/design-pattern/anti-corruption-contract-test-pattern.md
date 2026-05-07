---
schema_version: 3
title: Anti-Corruption Contract Test Pattern
concept_id: design-pattern/anti-corruption-contract-test-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- anti-corruption-contract-test
- provider-drift-regression
- translator-fixture-test
aliases:
- anti corruption contract test
- ACL contract test
- translator contract fixture
- external payload snapshot test
- provider drift regression
- acl compatibility test
- fixture based contract test
- provider sandbox gap
- 외부 계약 drift 테스트
symptoms:
- ACL 구조는 있지만 provider payload shape drift를 production 장애 이후에야 발견한다
- live sandbox integration test가 있으니 fixture 기반 regression test는 필요 없다고 생각한다
- unknown enum, optional field 추가, 필수 field 누락 같은 translation 정책을 테스트로 고정하지 않는다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/anti-corruption-layer-operational-pattern
- design-pattern/anti-corruption-adapter-layering
- design-pattern/tolerant-reader-event-contract-pattern
next_docs:
- design-pattern/anti-corruption-rollout-provider-sandbox-pattern
- design-pattern/domain-event-translation-pipeline
- design-pattern/anti-corruption-translation-map-pattern
linked_paths:
- contents/design-pattern/anti-corruption-layer-operational-pattern.md
- contents/design-pattern/anti-corruption-rollout-provider-sandbox-pattern.md
- contents/design-pattern/anti-corruption-adapter-layering.md
- contents/design-pattern/anti-corruption-translation-map-pattern.md
- contents/design-pattern/tolerant-reader-event-contract-pattern.md
- contents/design-pattern/domain-event-translation-pipeline.md
confusable_with:
- design-pattern/anti-corruption-layer-operational-pattern
- design-pattern/anti-corruption-rollout-provider-sandbox-pattern
- design-pattern/tolerant-reader-event-contract-pattern
- design-pattern/domain-event-translation-pipeline
forbidden_neighbors: []
expected_queries:
- ACL contract test는 provider API 전체 테스트가 아니라 translator semantics를 어떻게 고정해?
- 외부 payload fixture에 unknown enum, missing required, optional field 추가 케이스를 넣는 이유가 뭐야?
- sandbox 연동 테스트만으로 provider drift regression을 막기 어려운 이유는 뭐야?
- tolerant reader 정책을 contract test로 어디까지 허용하고 quarantine할지 어떻게 고정해?
- incident payload를 ACL regression fixture로 남기면 어떤 drift를 빨리 잡을 수 있어?
contextual_chunk_prefix: |
  이 문서는 Anti-Corruption Contract Test Pattern playbook으로, ACL translator와
  facade가 기대하는 provider payload shape와 translation semantics를 fixture 기반
  contract test로 고정해 provider drift regression을 production 전에 잡는 방법을 설명한다.
---
# Anti-Corruption Contract Test Pattern

> 한 줄 요약: ACL이 외부 계약 drift를 막으려면 운영 신호만으로는 부족하고, translator와 facade가 기대하는 외부 shape를 fixture 기반 contract test로 계속 검증해야 한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Anti-Corruption Layer Operational Pattern](./anti-corruption-layer-operational-pattern.md)
> - [Anti-Corruption Rollout and Provider Sandbox Pattern](./anti-corruption-rollout-provider-sandbox-pattern.md)
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Anti-Corruption Translation Map Pattern](./anti-corruption-translation-map-pattern.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)

---

## 핵심 개념

ACL이 있어도 외부 계약이 바뀌면 결국 번역 코드는 깨질 수 있다.  
운영 알람은 문제를 늦게 알려주고, 실제 장애는 production에서 먼저 터질 수 있다.

그래서 ACL에는 코드 구조와 운영 신호 외에 **계약 테스트 층**이 필요하다.

- provider payload fixture
- translator expected mapping
- facade degraded/quarantine behavior
- unknown field/enum compatibility expectation

핵심은 "외부가 이렇게 오면 우리는 이렇게 번역한다"를 테스트 자산으로 고정하는 것이다.

### Retrieval Anchors

- `anti corruption contract test`
- `translator contract fixture`
- `integration mapping test`
- `external payload snapshot test`
- `acl compatibility test`
- `provider drift regression`
- `provider sandbox gap`

---

## 깊이 들어가기

### 1. ACL contract test는 provider API 전체 테스트가 아니다

이 테스트의 목적은 provider가 살아있는지 확인하는 게 아니다.

- shape를 우리가 어떻게 해석하는지
- unknown/optional field를 어떻게 처리하는지
- quarantine 조건이 무엇인지

즉 boundary translation semantics를 고정하는 테스트다.

### 2. fixture는 happy path만 있으면 안 된다

최소한 다음 케이스를 같이 본다.

- 정상 payload
- optional field 추가
- unknown enum 값
- 필수 field 누락
- semantic anomaly 예시

그래야 drift가 "정상 응답에서만" 가려지지 않는다.

### 3. contract test는 tolerant reader 정책과 짝을 이뤄야 한다

consumer가 tolerant reader를 쓰더라도, 어디까지 tolerant한지는 명시돼야 한다.

- extra field는 허용
- unknown enum은 `UNKNOWN`
- 필수 field 누락은 quarantine

이 정책을 테스트로 굳혀야 팀 내 해석이 흔들리지 않는다.

### 4. translation map 변경은 fixture diff로 검토하는 편이 좋다

mapping table을 바꾸는 순간 의미가 달라질 수 있다.

- `AUTH_OK` -> `AUTHORIZED`
- `PARTIAL_CAPTURED` -> `UNKNOWN`

이런 변경은 코드 diff보다 fixture 결과 diff가 더 설명력이 높다.

### 5. 운영 incident 이후에는 회귀 fixture를 추가해야 한다

실제 provider drift incident가 있었다면, 그 payload는 가장 가치 높은 fixture가 된다.

- prod raw payload redaction
- regression fixture 등록
- quarantine/degrade expectation 고정

즉 incident learning이 ACL test corpus로 쌓여야 한다.

---

## 실전 시나리오

### 시나리오 1: PG status 확장

새 status가 들어온 incident 후, 그 raw payload를 fixture로 남기고 `UNKNOWN_CAPTURE_STATE`로 매핑되는지 테스트할 수 있다.

### 시나리오 2: 물류 필수 field 누락

필수 tracking field가 빠지면 retry가 아니라 quarantine 되는지 contract test로 고정할 수 있다.

### 시나리오 3: ERP 응답 의미 변경

shape는 같지만 금액 의미가 바뀐 경우, translation result가 degraded로 가는지 fixture 기반으로 확인할 수 있다.

---

## 코드로 보기

### fixture-driven translator test

```java
@Test
void unknown_status_is_mapped_to_unknown_and_metric_is_recorded() {
    PgResponseFixture fixture = fixtureLoader.load("pg_unknown_partial_captured.json");

    PaymentStatus status = translator.translate(fixture.status());

    assertThat(status).isEqualTo(PaymentStatus.UNKNOWN);
}
```

### quarantine expectation

```java
@Test
void missing_required_field_is_quarantined() {
    LegacyResponse fixture = fixtureLoader.load("erp_missing_required_amount.json");

    TranslationResult<OrderSyncCommand> result = translator.translate(fixture);

    assertThat(result).isInstanceOf(TranslationResult.Quarantined.class);
}
```

### fixture set

```java
// happy/
// unknown-enum/
// missing-required/
// degraded/
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 운영 모니터링만 사용 | 구현이 단순하다 | 장애 후에야 drift를 알기 쉽다 | 중요도 낮은 내부 연동 |
| ACL contract tests | drift regression을 빨리 잡는다 | fixture 관리 비용이 든다 | 외부 provider 의존이 큰 시스템 |
| live sandbox integration test만 의존 | 실제와 가깝다 | 재현성과 corner case 고정이 약하다 | 보조 신호로는 유용 |

판단 기준은 다음과 같다.

- translator/facade 기대 semantics를 fixture로 고정한다
- unknown/optional/missing-required 케이스를 포함한다
- incident payload를 regression fixture로 축적한다

---

## 꼬리질문

> Q: sandbox 연동 테스트가 있으면 contract test는 필요 없나요?
> 의도: live dependency와 deterministic regression test를 구분하는지 본다.
> 핵심: 아니다. sandbox는 보조 신호이고, drift 회귀 방지는 fixture 기반 contract test가 더 강하다.

> Q: unknown field를 허용하는데 왜 테스트가 필요한가요?
> 의도: tolerant policy도 명시돼야 함을 보는 질문이다.
> 핵심: 어디까지 허용하고 언제 quarantine하는지 팀 합의를 코드로 고정해야 하기 때문이다.

> Q: fixture가 너무 많아지면 어떻게 하나요?
> 의도: 테스트 자산 관리 감각을 보는 질문이다.
> 핵심: happy, degraded, quarantine, incident regression처럼 목적별로 묶는 편이 좋다.

## 한 줄 정리

Anti-Corruption Contract Test는 ACL이 기대하는 번역 의미를 fixture 기반으로 고정해, 외부 계약 drift가 production 장애로 먼저 드러나는 일을 줄여 준다.
