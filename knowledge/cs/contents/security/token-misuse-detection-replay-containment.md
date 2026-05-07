---
schema_version: 3
title: Token Misuse Detection / Replay Containment
concept_id: security/token-misuse-detection-replay-containment
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- token misuse detection
- token theft
- replay containment
- stolen bearer token
aliases:
- token misuse detection
- token theft
- replay containment
- stolen bearer token
- session hijack detection
- refresh token reuse
- impossible travel
- device binding mismatch
- token anomaly detection
- jti replay
- auth anomaly signals
- session quarantine
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/jwt-deep-dive.md
- contents/security/refresh-token-rotation-reuse-detection.md
- contents/security/session-revocation-at-scale.md
- contents/security/step-up-session-coherence-auth-assurance.md
- contents/security/session-quarantine-partial-lockdown-patterns.md
- contents/security/dpop-token-binding-basics.md
- contents/security/device-binding-caveats.md
- contents/security/audit-logging-auth-authz-traceability.md
- contents/security/auth-observability-sli-slo-alerting.md
- contents/security/replay-store-outage-degradation-recovery.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Token Misuse Detection / Replay Containment 핵심 개념을 설명해줘
- token misuse detection가 왜 필요한지 알려줘
- Token Misuse Detection / Replay Containment 실무 설계 포인트는 뭐야?
- token misuse detection에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Token Misuse Detection / Replay Containment를 다루는 deep_dive 문서다. 토큰 탈취 사고는 서명 검증 실패보다 "정상처럼 보이는 남용 패턴"으로 드러나는 경우가 많아서, refresh reuse, device/context drift, geo/ASN anomaly, binding mismatch를 묶어 token misuse를 탐지하고 단계별로 격리해야 한다. 검색 질의가 token misuse detection, token theft, replay containment, stolen bearer token처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Token Misuse Detection / Replay Containment

> 한 줄 요약: 토큰 탈취 사고는 서명 검증 실패보다 "정상처럼 보이는 남용 패턴"으로 드러나는 경우가 많아서, refresh reuse, device/context drift, geo/ASN anomaly, binding mismatch를 묶어 token misuse를 탐지하고 단계별로 격리해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [Refresh Token Rotation / Reuse Detection](./refresh-token-rotation-reuse-detection.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
> - [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
> - [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)
> - [Device Binding Caveats](./device-binding-caveats.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
> - [Database: 멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
> - [System Design: Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)

retrieval-anchor-keywords: token misuse detection, token theft, replay containment, stolen bearer token, session hijack detection, refresh token reuse, impossible travel, device binding mismatch, token anomaly detection, jti replay, auth anomaly signals, session quarantine, elevated step-up, partial lockdown

---

## 핵심 개념

보안팀이 실제로 많이 보는 토큰 사고는 "signature invalid"보다 아래에 가깝다.

- 같은 refresh token이 두 번 온다
- 짧은 시간에 대륙이 바뀐다
- 평소 브라우저 세션인데 갑자기 headless client가 access token을 쓴다
- DPoP key나 device binding 정보가 갑자기 달라진다

즉 토큰 misuse는 "토큰이 위조되었는가"보다 "정상처럼 보이는 토큰이 원래 의도와 다른 방식으로 쓰이고 있는가"의 문제다.

이 문서는 토큰 자체 구조보다, misuse signal을 어떻게 모으고 replay containment를 어떻게 단계화할지에 초점을 둔다.

---

## 깊이 들어가기

### 1. misuse와 invalid token은 다르다

invalid token은 비교적 명확하다.

- 만료됨
- 서명 불일치
- issuer/audience mismatch
- 형식 오류

misuse token은 더 어렵다.

- 서명도 맞고 만료도 안 됐다
- 그런데 사용 패턴이 이상하다
- 탈취된 bearer credential일 수 있다

따라서 misuse 탐지는 validation pipeline 바깥의 문맥이 필요하다.

### 2. signal은 단일 지표보다 묶음이 중요하다

강한 단일 신호:

- refresh token reuse
- DPoP `jti` replay
- 같은 `sid`에서 impossible concurrency

약하지만 유용한 보조 신호:

- ASN 급변
- user-agent family 급변
- browser 세션이 갑자기 server-to-server 패턴으로 바뀜
- device binding key mismatch
- 동일 `jti`가 짧은 시간에 여러 region에서 관찰됨

보통은 강한 신호 하나 + 약한 신호 몇 개를 묶어 대응 수준을 올린다.

### 3. correlation key를 미리 남겨야 misuse를 본다

필요한 필드:

- `jti`
- `sid`
- subject
- client id
- issuer
- tenant id
- device id 또는 binding key thumbprint
- IP / ASN / geo bucket
- user agent family
- request time

토큰 원문을 다 남길 필요는 없지만, reuse와 replay를 묶을 식별자는 있어야 한다.

### 4. replay는 종류가 다르다

토큰 재사용이라 해도 같은 방어로 끝나지 않는다.

- refresh token replay: family revoke가 핵심
- access token replay: 짧은 TTL, step-up, session quarantine
- DPoP proof replay: `jti` store와 request binding
- webhook/HMAC replay: nonce/timestamp window

즉 replay defense는 토큰 종류와 채널에 따라 containment 방법이 달라진다.

### 5. containment는 단계별이어야 한다

모든 이상 신호에 즉시 global logout을 걸면 false positive에 취약하다.

현실적인 대응 단계:

1. shadow detect: 알람만 올림
2. friction add: step-up auth, reauthentication
3. session quarantine: refresh 차단, 민감 작업 차단
4. family revoke: 장기 세션 계열 폐기
5. account-wide revoke: 강한 compromise 의심 시 전 device 무효화

강한 신호가 있거나 결제/관리자 세션이면 빠르게 상위 단계로 올린다.

### 6. device binding과 proof-of-possession도 만능은 아니다

DPoP나 device binding이 있으면 misuse 탐지가 쉬워지지만 끝은 아니다.

- 키 자체가 탈취될 수 있다
- shared device면 신호가 흐려진다
- binding mismatch는 구현 버그와도 구분해야 한다

즉 binding은 "재사용을 줄이는 장치"이지, 관측과 containment를 대체하지는 않는다.

### 7. browser/server boundary도 misuse signal에 포함해야 한다

예를 들어 원래는 BFF가 downstream token을 들고 있어야 하는데,  
어느 시점부터 브라우저에서 직접 resource API를 치기 시작하면 구조 위반 자체가 신호다.

즉 "이 토큰이 어디에서 사용되는 것이 정상인가"를 정의하지 않으면 misuse를 잡을 수 없다.

### 8. false positive budget를 정하지 않으면 탐지 시스템이 곧 무시된다

보안 감지 시스템이 매일 정상 사용자를 끊으면 우회가 시작된다.

그래서 필요하다.

- risk tier 별 정책
- support override 절차
- user-visible recovery UX
- alert precision 점검

탐지는 강할수록 좋다가 아니라, 신뢰할 수 있어야 쓸모가 있다.

---

## 실전 시나리오

### 시나리오 1: refresh token reuse가 잡혔는데 어떤 세션을 끊을지 애매하다

문제:

- rotation은 했지만 family 모델이 없다

대응:

- refresh family id를 기준으로 lineage를 관리한다
- reuse 감지 시 family revoke와 session quarantine를 함께 실행한다
- 같은 계정 전체 revoke는 risk tier를 보고 올린다

### 시나리오 2: access token은 정상인데 사용 위치가 갑자기 달라진다

문제:

- 원래 browser+BFF 경로에서만 쓰이던 토큰이 headless client 패턴으로 관찰된다

대응:

- 정상 사용 채널을 baseline으로 정의한다
- channel anomaly를 misuse signal에 포함한다
- 해당 세션에 step-up 또는 refresh 차단을 건다

### 시나리오 3: device binding mismatch가 대량으로 터졌는데 실제로는 앱 배포 버그다

문제:

- 탐지 시스템이 compromise와 rollout bug를 구분하지 못한다

대응:

- app version, region, release train을 같이 태깅한다
- shadow mode에서 먼저 rollout anomaly를 확인한다
- 강한 revoke는 build/regional scope를 확인한 뒤 실행한다

---

## 코드로 보기

### 1. misuse risk scoring 개념

```java
public MisuseLevel evaluate(TokenEvent event) {
    int score = 0;

    if (event.refreshReuseDetected()) score += 100;
    if (event.dpopReplayDetected()) score += 100;
    if (event.deviceBindingMismatch()) score += 40;
    if (event.asnChangedAbruptly()) score += 20;
    if (event.userAgentFamilyChanged()) score += 10;
    if (event.channelBoundaryViolation()) score += 50;

    if (score >= 100) return MisuseLevel.COMPROMISE;
    if (score >= 50) return MisuseLevel.SUSPICIOUS;
    return MisuseLevel.NORMAL;
}
```

### 2. 단계별 containment 예시

```text
NORMAL -> allow
SUSPICIOUS -> step-up auth + alert
COMPROMISE -> revoke refresh family + quarantine session + incident event
```

### 3. 최소 event schema

```text
subject, sid, jti, client_id, issuer, device_key_thumbprint, asn, ua_family, tenant_id, route_class, event_time
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 강한 단일 신호 위주 | 오탐이 적다 | 탐지 coverage가 좁다 | 초기 단계, 고신뢰 대응 |
| 다중 약한 신호 조합 | 탈취 패턴을 빨리 잡는다 | tuning이 어렵다 | 대규모 consumer auth |
| 즉시 전계정 revoke | 피해 확산을 빠르게 막는다 | 오탐 시 UX 피해가 크다 | 관리자, 결제, 고위험 계정 |
| step-up 후 quarantine | UX와 보안을 균형 있게 잡는다 | 공격자가 일부 계속 움직일 수 있다 | 일반 사용자 세션, 회색 신호 |

판단 기준은 이렇다.

- token 종류가 access인지 refresh인지 proof인지
- false positive를 감당할 수 있는 사용자군인지
- 정상 사용 채널 baseline이 정의돼 있는지
- containment 후 recovery UX가 준비돼 있는지

---

## 꼬리질문

> Q: 토큰 misuse는 왜 서명 검증만으로 못 잡나요?
> 의도: invalid token과 stolen valid token을 구분하는지 확인
> 핵심: 탈취된 토큰은 서명도 맞고 만료도 안 됐지만 사용 문맥이 이상할 수 있기 때문이다.

> Q: 가장 강한 misuse signal은 무엇인가요?
> 의도: 약한 anomaly와 강한 compromise signal을 구분하는지 확인
> 핵심: refresh token reuse, DPoP proof replay처럼 재사용이 명확히 드러나는 신호가 강하다.

> Q: 왜 모든 이상 신호에 바로 global logout을 걸면 안 되나요?
> 의도: false positive 비용을 이해하는지 확인
> 핵심: 오탐이 많아지면 시스템 신뢰가 무너지고 우회가 생기기 때문이다.

> Q: browser/server boundary 위반도 misuse signal이 될 수 있나요?
> 의도: 구조 위반 자체를 관측 대상으로 보는지 확인
> 핵심: 그렇다. 원래 브라우저가 보지 않아야 할 토큰이 브라우저 경로에서 쓰이면 강한 이상 신호다.

## 한 줄 정리

Token misuse 방어의 핵심은 만료와 서명만 보는 것이 아니라, refresh reuse, replay, channel drift, device/context mismatch를 묶어 세션을 단계적으로 격리하고 회수하는 것이다.
