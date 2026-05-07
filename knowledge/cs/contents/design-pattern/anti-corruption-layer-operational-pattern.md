---
schema_version: 3
title: Anti-Corruption Layer Operational Pattern
concept_id: design-pattern/anti-corruption-layer-operational-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- anti-corruption-operational-pattern
- acl-drift-detection
- translation-quarantine
aliases:
- anti corruption operational pattern
- ACL operational pattern
- acl drift detection
- integration contract drift
- translation quarantine
- boundary fallback
- provider model change detection
- external contract drift
- 안티 코럽션 운영 패턴
symptoms:
- ACL을 adapter와 translator 코드 구조로만 만들고 unknown code, schema mismatch, semantic drift를 관측하지 않는다
- provider timeout과 malformed payload와 unknown enum을 모두 같은 연동 실패로 보고 retry 정책을 섞는다
- 외부 계약 drift가 생겼을 때 rollback, degraded flow, quarantine queue 같은 축소 운영 경로가 없다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/anti-corruption-adapter-layering
- design-pattern/anti-corruption-translation-map-pattern
- design-pattern/tolerant-reader-event-contract-pattern
next_docs:
- design-pattern/anti-corruption-contract-test-pattern
- design-pattern/anti-corruption-rollout-provider-sandbox-pattern
- design-pattern/facade-anti-corruption-seam
linked_paths:
- contents/design-pattern/anti-corruption-adapter-layering.md
- contents/design-pattern/anti-corruption-translation-map-pattern.md
- contents/design-pattern/anti-corruption-contract-test-pattern.md
- contents/design-pattern/anti-corruption-rollout-provider-sandbox-pattern.md
- contents/design-pattern/facade-anti-corruption-seam.md
- contents/design-pattern/bounded-context-relationship-patterns.md
confusable_with:
- design-pattern/anti-corruption-adapter-layering
- design-pattern/anti-corruption-contract-test-pattern
- design-pattern/anti-corruption-translation-map-pattern
- design-pattern/tolerant-reader-event-contract-pattern
forbidden_neighbors: []
expected_queries:
- ACL은 번역 코드뿐 아니라 provider drift detection과 quarantine 운영 패턴까지 왜 필요해?
- provider timeout과 malformed payload와 unknown enum은 retry와 quarantine 관점에서 어떻게 나눠?
- unknown status code mapping count나 translator fallback rate를 ACL metric으로 봐야 하는 이유가 뭐야?
- 외부 계약 drift가 발생했을 때 mapping rollback, degraded flow, provider 기능 차단은 어떻게 설계해?
- Anti-Corruption Layer에서 semantic mismatch를 내부 도메인으로 흘리지 않으려면 어떤 운영 신호가 필요해?
contextual_chunk_prefix: |
  이 문서는 Anti-Corruption Layer Operational Pattern playbook으로, ACL을
  단순 translator 코드가 아니라 provider contract drift를 감지하고 unknown code,
  schema mismatch, semantic anomaly를 metric, quarantine, degrade, rollback path로
  격리하는 운영 패턴으로 설명한다.
---
# Anti-Corruption Layer Operational Pattern

> 한 줄 요약: Anti-Corruption Layer는 번역 코드만 두는 구조가 아니라, 외부 계약 drift를 감지하고 격리하고 롤포워드하는 운영 패턴까지 함께 가져야 실제 경계 보호가 유지된다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Anti-Corruption Translation Map Pattern](./anti-corruption-translation-map-pattern.md)
> - [Anti-Corruption Contract Test Pattern](./anti-corruption-contract-test-pattern.md)
> - [Anti-Corruption Rollout and Provider Sandbox Pattern](./anti-corruption-rollout-provider-sandbox-pattern.md)
> - [Facade as Anti-Corruption Seam](./facade-anti-corruption-seam.md)
> - [Bounded Context Relationship Patterns](./bounded-context-relationship-patterns.md)
> - [Tolerant Reader for Event Contracts](./tolerant-reader-event-contract-pattern.md)

---

## 핵심 개념

많은 팀이 ACL을 "코드 구조"로만 이해한다.

- adapter
- translator
- facade
- port

하지만 실제 운영에서는 외부 계약이 계속 흔들린다.

- 필드 추가/삭제
- enum 값 확장
- 에러 코드 의미 변경
- pagination/정렬 semantics 변경

그래서 ACL은 단순 번역 계층이 아니라 **drift detection + graceful degradation + rollback path**를 가진 운영 패턴이어야 한다.

### Retrieval Anchors

- `anti corruption operational pattern`
- `acl drift detection`
- `integration contract drift`
- `translation quarantine`
- `boundary fallback`
- `external model change detection`
- `acl contract test`

---

## 깊이 들어가기

### 1. ACL의 진짜 적은 외부 계약 drift다

처음 붙일 때보다 운영 중이 더 어렵다.

- 외부 provider가 문서 없이 필드를 추가
- 기존 의미를 subtly 바꿈
- 응답 shape는 같지만 status 의미가 달라짐

ACL은 이런 drift를 내부로 흘려보내지 않기 위한 방화벽이다.

### 2. 운영 가능한 ACL은 unknown을 격리할 수 있어야 한다

외부 응답이 예상과 다를 때 선택지는 보통 세 가지다.

- 즉시 실패
- 안전한 degraded result 반환
- quarantine/dead-letter로 격리 후 수동 확인

문제는 이 정책이 코드 안에만 숨어 있으면 운영자가 상황을 설명하기 어렵다는 점이다.

### 3. translation 실패와 provider 실패를 구분해야 한다

같은 "연동 실패"처럼 보여도 다르다.

- provider timeout
- malformed payload
- unknown enum
- semantic mismatch

이걸 구분하지 않으면 재시도 정책도 잘못 붙는다.

### 4. ACL 운영은 metrics와 샘플링 없이는 blind spot이 된다

다음 신호가 최소한 필요하다.

- unknown code mapping count
- translator fallback rate
- schema mismatch count
- provider version/channel별 오류율

그래야 "외부가 바뀌었다"를 구조적으로 감지할 수 있다.

### 5. ACL은 코드만 아니라 rollback surface도 설계해야 한다

drift가 감지됐을 때 대응 전략이 있어야 한다.

- 이전 mapping table로 즉시 rollback
- 특정 provider 기능만 차단
- degraded flow로 전환
- quarantine queue로 격리

즉 ACL은 boundary design이면서 동시에 integration incident control plane이다.

---

## 실전 시나리오

### 시나리오 1: PG 상태 코드 확장

기존에 없던 `PARTIAL_CAPTURED`가 들어오면, 내부 모델로 곧바로 침투시키지 말고 `UNKNOWN_CAPTURE_STATE`로 격리하고 알람을 올릴 수 있어야 한다.

### 시나리오 2: 물류 응답 필드 shape 변경

필수 필드 누락이 반복되면 retry가 아니라 translation quarantine가 더 맞다.

### 시나리오 3: 외부 ERP 의미 변경

코드는 통과하지만 금액 의미가 바뀌면 더 위험하다.  
semantic anomaly detection이 필요하다.

---

## 코드로 보기

### translation result 분리

```java
public sealed interface TranslationResult<T>
    permits TranslationResult.Success, TranslationResult.Quarantined, TranslationResult.Degraded {

    record Success<T>(T value) implements TranslationResult<T> {}
    record Quarantined<T>(String reason) implements TranslationResult<T> {}
    record Degraded<T>(T fallbackValue, String reason) implements TranslationResult<T> {}
}
```

### unknown code metric

```java
public PaymentStatus translate(String externalCode) {
    PaymentStatus status = MAP.get(externalCode);
    if (status == null) {
        metrics.increment("pg.translation.unknown_status");
        return PaymentStatus.UNKNOWN;
    }
    return status;
}
```

### quarantine path

```java
if (payloadMissingCriticalField(response)) {
    quarantineStore.save(response.rawBody());
    throw new IllegalStateException("translation quarantined");
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단순 ACL 코드만 유지 | 구현이 빠르다 | drift 감지가 늦고 대응이 약하다 | 아주 단순한 내부 연동 |
| 운영 가능한 ACL | drift를 빨리 감지하고 격리할 수 있다 | metrics/quarantine/fallback 설계가 필요하다 | 외부 provider 의존도가 높은 시스템 |
| provider model 직접 수용 | 속도가 빠르다 | 도메인 오염과 운영 blast radius가 크다 | 보통 피하는 편이 좋다 |

판단 기준은 다음과 같다.

- provider drift 가능성이 있으면 ACL 운영 신호를 같이 둔다
- unknown/semantic mismatch를 retry로만 처리하지 않는다
- rollback/degrade/quarantine path를 미리 만든다

---

## 꼬리질문

> Q: ACL이 있으면 외부 계약 변경을 자동으로 흡수하나요?
> 의도: 구조 분리와 운영 대응을 혼동하지 않는지 본다.
> 핵심: 아니다. drift를 감지하고 격리하는 운영 설계가 추가로 필요하다.

> Q: unknown 값을 그냥 UNKNOWN으로만 두면 충분한가요?
> 의도: silent degradation을 경계하는지 본다.
> 핵심: 아니다. metrics, sampling, quarantine 같은 관측성과 함께 가야 한다.

> Q: retry와 quarantine은 어떻게 나누나요?
> 의도: transport failure와 semantic failure를 구분하는지 본다.
> 핵심: 네트워크/일시 장애는 retry, payload/semantic mismatch는 quarantine가 더 맞다.

## 한 줄 정리

Anti-Corruption Layer는 번역 코드를 넘어서, 외부 계약 drift를 감지하고 격리하고 안전하게 축소 운영하는 운영 패턴까지 가져야 진짜 경계 보호가 된다.
