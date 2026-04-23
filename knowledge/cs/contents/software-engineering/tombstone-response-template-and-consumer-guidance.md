# Tombstone Response Template and Consumer Guidance

> 한 줄 요약: tombstone mode는 단순한 실패 응답이 아니라, deprecated path를 호출한 소비자가 왜 막혔는지와 어디로 가야 하는지를 즉시 이해하도록 돕는 controlled failure contract이므로, response template과 guidance를 표준화할 필요가 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)
> - [Deprecation Communication Playbook](./deprecation-communication-playbook.md)
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [Support Contract Request Type Severity Matrix](./support-contract-request-type-severity-matrix.md)
> - [API Lifecycle Stage Model](./api-lifecycle-stage-model.md)

> retrieval-anchor-keywords:
> - tombstone response
> - tombstone template
> - 410 Gone
> - deprecated api response
> - sunset error contract
> - sunset response body
> - error envelope
> - replacement guidance
> - deprecation response body
> - migration docs url
> - support contact
> - traceable error code
> - consumer guidance

## 핵심 개념

tombstone mode는 old path를 막는 마지막 단계다.
이때 plain 404나 vague 410만 주면 support 문의와 consumer 혼란이 커진다.

좋은 tombstone response는 최소한 다음을 준다.

- 무엇이 종료됐는가
- 왜 실패했는가
- 어떤 replacement를 써야 하는가
- 어디서 지원을 받는가
- 이 호출을 추적할 수 있는 code/id

즉 tombstone response는 차단이 아니라 **가이드가 포함된 종료 계약**이다.

---

## Template Insertion Points

tombstone guidance는 응답 body 한 군데에만 넣으면 지원 흐름이 끊긴다. 보통 아래 위치를 같이 맞춘다.

- gateway/application error envelope: `error_code`, `replacement`, `docs_url`, `support_channel`, `trace_id`를 넣는다.
- deprecation docs / migration guide: 같은 replacement id와 sunset date를 반복해 consumer가 연결할 수 있게 한다.
- support runbook / severity matrix: tombstone code가 들어오면 어느 채널로 보내는지 매핑한다.
- observability dashboard / alert annotation: tombstone hit count와 top consumer를 같은 code 기준으로 본다.

즉 tombstone template의 삽입 지점은 **응답, 문서, 지원, 관측** 네 군데가 한 세트여야 한다.

---

## 깊이 들어가기

### 1. tombstone response는 support contract의 일부다

API를 막는 순간 support 부담은 사라지지 않는다.
오히려 마지막 남은 consumer 문의가 집중될 수 있다.

그래서 tombstone response에는 다음이 연결돼야 한다.

- support channel
- documentation URL
- replacement API/service id
- incident/deprecation trace code

### 2. human-readable과 machine-readable을 함께 넣는 편이 좋다

좋은 구조 예:

- machine-readable: error_code, replacement_id, deprecation_stage
- human-readable: summary, next steps, deadline context

이렇게 해야 consumer team과 automation/tooling 둘 다 활용할 수 있다.

### 3. security와 information leakage를 조심해야 한다

내부 시스템이라고 해서 상세한 내부 구조를 모두 응답에 실을 필요는 없다.

응답에는:

- 충분한 next step
- 최소한의 내부 정보
- support traceability

가 균형 있게 들어가야 한다.

### 4. tombstone template는 stage별로 다를 수 있다

warning stage와 allowlist-only stage와 hard tombstone stage는 메시지가 다를 수 있다.

예:

- pre-sunset: deadline 강조
- sunset: replacement mandatory 강조
- post-sunset: replacement only + support cut-off 명시

즉 tombstone도 lifecycle-aware해야 한다.

### 5. template는 운영 지표와 연결돼야 한다

봐야 할 것:

- tombstone hit count
- top remaining consumers
- support ticket volume
- replacement adoption after tombstone

이 데이터가 있어야 template와 guidance를 개선할 수 있다.

---

## 실전 시나리오

### 시나리오 1: 구 endpoint를 호출하자 갑자기 404만 받는다

consumer는 endpoint typo인지 sunset인지 모른다.
tombstone template가 있으면 migration action으로 바로 이어질 수 있다.

### 시나리오 2: allowlist-only 단계에서 일부 팀만 막힌다

response에 replacement path와 support channel이 없다면 운영 혼란이 커진다.

### 시나리오 3: 외부 파트너 API를 종료한다

내부 jargon 없이 파트너가 이해할 수 있는 guidance와 support contract 링크가 더 중요하다.

---

## 코드로 보기

```json
{
  "error_code": "API_SUNSET_410",
  "message": "legacy-order-detail-v1 is no longer supported",
  "replacement": "order-detail-v2",
  "docs_url": "https://internal/docs/order-detail-v2",
  "support_channel": "#order-api-support",
  "trace_id": "sunset-2026-10-01-1234"
}
```

좋은 tombstone은 실패를 더 잘 설명해 support 비용을 줄인다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| plain 404/410 | 단순하다 | 혼란과 문의가 커진다 | 거의 없음 |
| custom tombstone body | 전환 안내가 된다 | 설계가 필요하다 | 일반적인 sunset |
| stage-aware tombstone template | 가장 친절하다 | 운영 관리가 필요하다 | 소비자가 많을 때 |

tombstone response template의 목적은 에러를 예쁘게 꾸미는 것이 아니라, **차단 순간에도 소비자가 스스로 다음 행동을 이해하게 만드는 것**이다.

---

## 꼬리질문

- tombstone response가 replacement path와 support channel을 제공하는가?
- machine-readable field와 human-readable guidance가 같이 있는가?
- lifecycle stage에 따라 메시지가 달라져야 하지 않는가?
- tombstone hit 이후 실제 migration이 진행되는지 측정하고 있는가?

## 한 줄 정리

Tombstone response template and consumer guidance는 sunset된 경로의 실패 응답을 controlled failure contract로 만들어, 차단 순간에도 소비자가 replacement와 지원 경로를 이해하게 하는 표준이다.
