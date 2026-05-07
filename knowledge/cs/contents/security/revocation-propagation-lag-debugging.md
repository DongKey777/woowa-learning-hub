---
schema_version: 3
title: Revocation Propagation Lag / Debugging
concept_id: security/revocation-propagation-lag-debugging
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- revocation lag
- logout propagation lag
- revoke debugging
- session invalidation delay
aliases:
- revocation lag
- logout propagation lag
- revoke debugging
- session invalidation delay
- refresh family revoke lag
- token revocation delay
- last accepted after revoke
- logout inconsistency
- revoke fan-out debugging
- revocation propagation status
- requested in progress fully blocked confirmed
- fully blocked confirmed meaning
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/session-revocation-at-scale.md
- contents/security/oidc-backchannel-logout-session-coherence.md
- contents/security/revocation-propagation-status-contract.md
- contents/security/auth-observability-sli-slo-alerting.md
- contents/security/session-quarantine-partial-lockdown-patterns.md
- contents/security/auth-incident-triage-blast-radius-recovery-matrix.md
- contents/security/browser-bff-token-boundary-session-translation.md
- contents/security/bff-session-store-outage-degradation-recovery.md
- contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
- contents/spring/spring-security-logout-handler-success-boundaries.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Revocation Propagation Lag / Debugging 핵심 개념을 설명해줘
- revocation lag가 왜 필요한지 알려줘
- Revocation Propagation Lag / Debugging 실무 설계 포인트는 뭐야?
- revocation lag에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Revocation Propagation Lag / Debugging를 다루는 deep_dive 문서다. logout, password reset, admin disable, family revoke는 "호출됐다"로 끝나지 않고 언제 마지막으로 수용됐는지까지 봐야 하며, revocation lag는 저장소, cache, token TTL, route class, region fan-out을 나눠 디버깅해야 한다. 검색 질의가 revocation lag, logout propagation lag, revoke debugging, session invalidation delay처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Revocation Propagation Lag / Debugging

> 한 줄 요약: logout, password reset, admin disable, family revoke는 "호출됐다"로 끝나지 않고 언제 마지막으로 수용됐는지까지 봐야 하며, revocation lag는 저장소, cache, token TTL, route class, region fan-out을 나눠 디버깅해야 한다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **revocation incident의 지연 분석과 debugging**을 맡는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
> - [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
> - [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](../spring/spring-security-logout-handler-success-boundaries.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: revocation lag, logout propagation lag, revoke debugging, session invalidation delay, refresh family revoke lag, token revocation delay, last accepted after revoke, logout inconsistency, revoke fan-out debugging, revocation propagation status, requested in progress fully blocked confirmed, fully blocked confirmed meaning, revoke status payload, logout still works, logout but still works, logout tail, revocation tail, logout all devices still works, old session still works after logout

## 이 문서 다음에 보면 좋은 문서

- `logout still works`, `logout tail`, `revocation tail`, `last accepted after revoke`처럼 tail symptom 자체를 설명해야 하면 기본 revocation 모델을 [Session Revocation at Scale](./session-revocation-at-scale.md)로 되돌아가면 좋다.
- federated logout 전파는 [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)와 연결된다.
- operator-triggered revoke의 status payload와 blocked-confirmation 의미는 [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)에서 이어진다.
- 브라우저 local logout cleanup과 실제 revoke plane을 나눠 보고 싶으면 [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](../spring/spring-security-logout-handler-success-boundaries.md)를 같이 본다.
- `login loop`, `hidden session mismatch`, `cookie는 남았는데 session missing`처럼 translation 계층 문제로 보이면 [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md), [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) 쪽으로 갈아타는 편이 맞다.
- 운영 지표와 incident framing은 [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md), [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)로 이어진다.

---

## 핵심 개념

세션 revoke에서 자주 하는 착각은 이렇다.

- revoke API가 성공했다
- 그러니 세션은 끝났다

실제로는 그 뒤가 더 중요하다.

- 어떤 route는 이미 끊겼는가
- 어떤 region은 아직 받아 주는가
- access token TTL 때문에 얼마 동안 살아 있는가
- cache나 stale session이 아직 예전 상태를 보는가

즉 revocation incident의 핵심은 revoke 요청 자체가 아니라 propagation lag를 측정하고 설명하는 것이다.

그래서 operator tooling이나 status page는 `requested`, `in_progress`, `fully_blocked_confirmed`를 같은 상태로 뭉개면 안 된다.  
lag debugging은 왜 아직 `in_progress`인지 설명하는 근거를 만들고, `fully_blocked_confirmed`가 언제 정당한지 증명하는 축이다.

---

## 깊이 들어가기

### 1. revoke는 하나의 이벤트가 아니라 전파 파이프라인이다

보통 단계는 이렇다.

1. revoke intent 생성
2. session/version/family store 갱신
3. cache invalidation fan-out
4. verifier/resource server 반영
5. 마지막 수용 종료

어느 단계가 느린지 모르면 대응이 틀린다.

### 2. 토큰 종류마다 기대 가능한 즉시성이 다르다

- browser session cookie: 보통 빠르게 끊을 수 있다
- refresh family: store 갱신 후 비교적 빠르게 끊을 수 있다
- self-contained access token: TTL이 남는 동안 일부 route에서 계속 살 수 있다
- exchanged downstream token: 별도 audience cache 때문에 더 늦을 수 있다

즉 "logout 후 즉시 반영"은 토큰 종류별로 실제 의미가 다르다.

### 3. lag는 평균보다 마지막 accept 시각이 중요하다

운영에서 의미 있는 지표:

- revoke requested at
- last accepted at
- last refresh success after revoke
- region with longest tail

이게 있어야 "대부분 빨랐다"가 아니라 "언제 완전히 끊겼는가"를 말할 수 있다.

### 4. lag 원인은 보통 네 갈래다

- TTL: access token 자체가 아직 유효
- cache: session/authz cache가 stale
- fan-out: pub/sub invalidation이 느림
- route inconsistency: 어떤 서비스는 revoke check를 안 함

이 네 가지를 분리하지 않으면, 무조건 TTL만 줄이거나 무조건 cache만 비우는 잘못된 대응으로 간다.

### 5. route class별로 기대치를 다르게 둬야 한다

예:

- payment/admin/security settings: revoke lag 거의 없어야 함
- 일반 personalized read: 약간의 tail 허용 가능
- audit export/download: 더 보수적 정책 필요

즉 propagation lag SLO는 모든 route에 같지 않아도 된다.

### 6. quarantine가 revoke 대기 상태를 메워 줄 수 있다

즉시 revoke가 어려운 route가 있더라도 중간 대응은 가능하다.

- 민감 write 즉시 차단
- refresh freeze
- read-only quarantine

이렇게 하면 propagation lag tail을 줄이지 못해도 위험을 줄일 수 있다.

### 7. federated logout와 local revoke의 lag는 따로 봐야 한다

외부 IdP에서 logout token이 왔더라도:

- local session store 반영
- refresh family revoke
- downstream access token acceptance 종료

는 따로 늦을 수 있다.

그래서 "OP logout success"와 "우리 앱에서 완전 종료"는 다른 지표다.

### 8. debugging은 경로별 acceptance evidence를 모아야 한다

유용한 evidence:

- revoke 이후 allow된 request id
- 어떤 verifier/pod/region이 수용했는지
- 어떤 token type이었는지
- cache hit 여부

이게 없으면 사용자 제보 외에는 tail을 재현하기 어렵다.

---

## 실전 시나리오

### 시나리오 1: logout all devices 후에도 한 모바일 기기만 계속 살아 있다

문제:

- refresh family는 끊겼지만 mobile access token TTL과 local cache가 남았다

대응:

- token type과 device cohort를 분리해 본다
- last accepted after revoke를 device별로 수집한다
- 고위험 route는 quarantine/fail-closed를 적용한다

### 시나리오 2: admin disable은 즉시 반영돼야 하는데 일부 region에서 수 분간 허용된다

문제:

- invalidation fan-out이 regional tail을 만든다

대응:

- region별 lag histogram을 본다
- fan-out 경로와 stale cache를 분리해 본다
- admin route는 stronger direct check를 둔다

### 시나리오 3: 사용자는 logout했다고 하는데 사실은 federated logout만 되고 local token cache가 남아 있다

문제:

- OP logout와 local revoke가 같은 상태로 취급돼 `logout still works`처럼 보인다

대응:

- issuer logout event와 local revoke completed를 별도 metric으로 둔다
- session mapping과 token cache invalidation을 같이 본다

---

## 코드로 보기

### 1. propagation lag 측정 예시

```java
public void recordLastAcceptedAfterRevoke(String subject, Instant revokedAt, Instant acceptedAt) {
    if (acceptedAt.isAfter(revokedAt)) {
        metrics.timer("auth.revocation.last_accept_lag").record(Duration.between(revokedAt, acceptedAt));
    }
}
```

### 2. 운영 체크리스트

```text
1. revoke requested 시각과 last accepted 시각을 같이 보는가
2. token type별 기대 즉시성을 분리하는가
3. cache/fan-out/TTL/route inconsistency를 별도 원인으로 보는가
4. high-risk route는 propagation lag 중에도 quarantine 또는 direct check가 가능한가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 짧은 access token TTL | revoke tail을 줄인다 | issuance/refresh 부담이 늘어난다 | 민감 API |
| 중앙 direct check | 즉시성이 강하다 | latency와 dependency가 늘어난다 | admin, payment, security route |
| cache fan-out invalidation | 확장성이 좋다 | tail과 regional skew가 생길 수 있다 | 대부분의 분산 시스템 |
| quarantine로 위험 완화 | revoke tail 중간 방어가 가능하다 | 상태 모델이 복잡하다 | 회색 구간 대응 |

판단 기준은 이렇다.

- 어떤 route가 거의 즉시 revoke를 요구하는가
- token type이 self-contained인지 stateful인지
- regional fan-out tail을 관측할 수 있는가
- direct check 또는 quarantine 같은 보조 제어가 있는가

---

## 꼬리질문

> Q: revoke API가 성공했는데 왜 세션이 즉시 안 끝날 수 있나요?
> 의도: revoke intent와 propagation completion을 구분하는지 확인
> 핵심: cache, fan-out, token TTL, route inconsistency 때문에 마지막 수용 시각이 뒤로 밀릴 수 있기 때문이다.

> Q: propagation lag에서 가장 중요한 지표는 무엇인가요?
> 의도: 평균보다 tail을 보는지 확인
> 핵심: revoke 이후 마지막으로 accept된 시각, 즉 last accepted after revoke다.

> Q: 모든 route에 같은 revoke 즉시성이 필요하나요?
> 의도: route risk 기반 운영을 이해하는지 확인
> 핵심: 아니다. admin/payment/security route는 더 강한 즉시성이 필요할 수 있다.

> Q: revocation lag를 줄이기 어려우면 어떤 중간 대안이 있나요?
> 의도: quarantine의 역할을 이해하는지 확인
> 핵심: 민감 write 차단, refresh freeze, read-only quarantine 같은 중간 제어가 있다.

## 한 줄 정리

Revocation incident를 잘 다루려면 revoke API 성공 여부보다, 어떤 token과 어떤 route가 언제까지 accept됐는지를 propagation lag 관점으로 추적해야 한다.
