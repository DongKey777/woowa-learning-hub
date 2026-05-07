---
schema_version: 3
title: Auth Incident Triage / Blast-Radius Recovery Matrix
concept_id: security/auth-incident-triage-blast-radius-recovery-matrix
canonical: false
category: security
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- auth incident triage
- authentication incident recovery
- blast radius matrix
- auth outage classification
aliases:
- auth incident triage
- authentication incident recovery
- blast radius matrix
- auth outage classification
- login incident
- verification outage
- revocation lag incident
- replay outage
- authz bug recovery
- identity incident runbook
- control plane auth incident
- incident close gate
symptoms:
- Auth Incident Triage / Blast-Radius Recovery Matrix 관련 운영 사고나 보안 이상 징후가 발생해 대응 순서가 필요하다
intents:
- troubleshooting
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/jwt-signature-verification-failure-playbook.md
- contents/security/jwt-jwks-outage-recovery-failover-drills.md
- contents/security/auth-observability-sli-slo-alerting.md
- contents/security/authorization-runtime-signals-shadow-evaluation.md
- contents/security/replay-store-outage-degradation-recovery.md
- contents/security/authz-kill-switch-break-glass-governance.md
- contents/security/incident-close-break-glass-gate.md
- contents/security/token-misuse-detection-replay-containment.md
- contents/system-design/control-plane-data-plane-separation-design.md
- contents/system-design/service-discovery-health-routing-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Auth Incident Triage / Blast-Radius Recovery Matrix 장애가 나면 복구 순서는?
- auth incident triage 운영 대응 체크리스트가 뭐야?
- Auth Incident Triage / Blast-Radius Recovery Matrix에서 blast radius를 어떻게 줄여?
- auth incident triage 사고 후 어떤 증거를 남겨야 해?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Auth Incident Triage / Blast-Radius Recovery Matrix를 다루는 playbook 문서다. 인증 장애는 로그인, 검증, revocation, authz, replay defense가 각기 다른 방식으로 망가지므로, incident 초기에 stage, blast radius, integrity risk, 가능한 완화 레버를 매트릭스로 분류해야 잘못된 복구를 줄일 수 있다. 검색 질의가 auth incident triage, authentication incident recovery, blast radius matrix, auth outage classification처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Auth Incident Triage / Blast-Radius Recovery Matrix

> 한 줄 요약: 인증 장애는 로그인, 검증, revocation, authz, replay defense가 각기 다른 방식으로 망가지므로, incident 초기에 stage, blast radius, integrity risk, 가능한 완화 레버를 매트릭스로 분류해야 잘못된 복구를 줄일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
> - [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [System Design: Control Plane / Data Plane Separation](../system-design/control-plane-data-plane-separation-design.md)
> - [System Design: Service Discovery / Health Routing](../system-design/service-discovery-health-routing-design.md)
> - [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)
> - [System Design: Global Traffic Failover Control Plane](../system-design/global-traffic-failover-control-plane-design.md)
> - [Security README: Incident / Recovery / Trust](./README.md#incident--recovery--trust)

retrieval-anchor-keywords: auth incident triage, authentication incident recovery, blast radius matrix, auth outage classification, login incident, verification outage, revocation lag incident, replay outage, authz bug recovery, identity incident runbook, control plane auth incident, incident close gate, break glass closure blocker, global failover auth, session store degraded mode, blast radius containment, unable to find jwk, unable to find JWK, invalid signature spike, security incident bridge, incident recovery trust bundle, security readme incident bridge

---

## 핵심 개념

auth incident에서 가장 비싼 실수는 "로그인 안 됨" 또는 "403 많음" 같은 사용자 증상만 보고 바로 복구 레버를 당기는 것이다.

같은 증상도 내부 원인은 전혀 다를 수 있다.

- login redirect/callback 문제
- token issuance/refresh 문제
- JWT verification/JWKS 문제
- revocation propagation 문제
- authz rollout bug
- replay defense dependency 문제

즉 incident 초기에 필요한 것은 만능 해결책이 아니라, 어떤 stage가 어떤 integrity risk와 blast radius를 가지는지 분류하는 triage matrix다.

---

## 깊이 들어가기

### 1. 먼저 stage를 고정해야 한다

유용한 1차 분류:

- login / federation
- token issue / refresh
- token verify / introspection
- session revoke / logout propagation
- authorization decision
- replay defense / one-time token consume

이 분류가 필요한 이유는 복구 레버가 완전히 다르기 때문이다.

- verify outage에 authz kill switch는 답이 아니다
- authz rollout bug에 JWKS cache refresh는 답이 아니다
- replay store outage에 timestamp window만 여는 것은 부족하다

### 2. blast radius는 actor, route, tenant, region 네 축으로 본다

최소한 다음을 본다.

- 모든 사용자 vs 특정 client class
- 특정 admin route만 vs 전 API
- 특정 tenant cohort vs 전체 tenant
- 특정 region/pod version vs 전역

blast radius를 좁혀야 recovery도 scoped하게 할 수 있다.

### 3. integrity risk와 availability pressure를 같이 봐야 한다

일부 incident는 "서비스가 막힘"보다 "잘못 허용될 위험"이 더 크다.

예:

- authz rollout bug로 old deny -> new allow
- replay store outage로 signed request replay 차단 상실
- duplicate `kid` ambiguity

이 경우 availability 압박이 있어도 완화 레버를 보수적으로 써야 한다.

반대로:

- login callback 일시 장애
- 특정 IdP network issue

같은 경우는 사용자 영향 완화가 더 중요할 수 있다.

### 4. stage별 기본 질문을 runbook처럼 고정해 두는 편이 좋다

예:

- login: redirect, callback, cookie/session, IdP 상태 중 어디인가
- verify: issuer binding, `kid`, `unable to find JWK`, alg, claim, dependency 중 어디인가
- revoke: 요청 실패인가, propagation lag인가, stale session acceptance인가
- authz: deny spike인가, silent allow drift인가, rollout bug인가
- replay: store outage인가, partial write failure인가, one-time token race인가

이 질문이 고정돼 있어야 on-call이 패닉 상태에서 잘못된 레버를 안 당긴다.

### 5. recovery lever inventory가 미리 있어야 한다

유용한 레버 예:

- signer freeze / rollback
- old policy evaluator kill switch
- scoped break-glass grant
- session quarantine
- refresh freeze
- replay route fail-closed
- low-risk degraded mode

핵심은 "있는 레버"와 "절대 쓰면 안 되는 레버"를 문서화하는 것이다.

### 6. incident는 단일 장애보다 연쇄 장애로 보는 편이 맞다

실제 현장에서는 종종 이렇게 이어진다.

- token misuse alert 급증
- support가 강제로 logout all devices
- revocation propagation lag가 튀어 UX 악화
- authz override가 임시로 켜짐

즉 incident state는 하나가 아니라 여러 control plane가 엮인 연쇄 상태다.

### 7. timeline과 decision log를 남겨야 postmortem이 된다

최소한 남길 것:

- 최초 감지 시각
- stage 분류 변경 이력
- blast radius 판단 근거
- 어떤 recovery lever를 언제 켰는지
- override/quarantine/rollback 종료 시각

이게 없으면 incident 후 같은 실수를 반복한다.
특히 break-glass를 쓴 incident라면 종료 이후 leftover grant와 active override를 어떤 hard blocker로 막을지는 [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)까지 이어서 봐야 한다.

### 8. triage matrix는 문서가 아니라 훈련 대상이어야 한다

드릴 없이 문서만 있으면 실제 incident에서 안 써진다.

훈련 질문 예:

- "현재 401 급증인데 login과 refresh는 정상"이면 어느 stage인가
- "403은 늘지 않았는데 cross-tenant allow 의심"이면 어떤 risk인가
- "nonce store partial outage"면 어떤 route를 닫을 것인가

즉 matrix는 on-call muscle memory가 되어야 한다.

---

## 실전 시나리오

### 시나리오 1: 401이 급증해 모두가 로그인 장애라고 생각한다

문제:

- 실제론 verify/JWKS path만 깨졌고 로그에는 `unable to find JWK`만 남았을 수 있다

대응:

- login success와 verification bucket을 분리한다
- stage를 verify로 분류한 뒤 signer freeze와 refresh collapse를 검토한다

### 시나리오 2: support가 403 급증을 막으려다 global break-glass를 켠다

문제:

- blast radius를 확인하기 전 과도한 완화를 실행했다

대응:

- tenant/route/release 범위를 먼저 좁힌다
- old evaluator kill switch나 scoped break-glass부터 검토한다

### 시나리오 3: replay store outage인데 low-risk degraded mode가 전 route로 퍼진다

문제:

- route class별 fail policy inventory가 없다

대응:

- replay-sensitive route를 fail-closed로 고정한다
- degraded mode는 route-scoped, time-boxed로 제한한다
- bypass count를 추적한다

---

## 코드로 보기

### 1. 간단한 triage matrix 예시

```text
stage=verify + integrity_high -> signer freeze, fail-closed on sensitive routes
stage=authz + deny_spike + rollout_recent -> old policy kill switch, shadow diff review
stage=replay + store_outage -> route-tiered fail policy, bounded degraded mode
stage=session + propagation_lag -> quarantine or short TTL, revocation lag investigation
```

### 2. incident event 스키마 예시

```java
public record AuthIncidentEvent(
        String incidentId,
        String stage,
        String blastRadius,
        String integrityRisk,
        String recoveryLever,
        Instant recordedAt
) {
}
```

### 3. 운영 체크리스트

```text
1. incident를 login/issue/verify/revoke/authz/replay stage로 먼저 분류하는가
2. blast radius를 actor, route, tenant, region으로 좁히는가
3. integrity-high 상황에서 금지된 완화 레버가 정의돼 있는가
4. recovery lever 사용 시각과 종료 시각을 기록하는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| symptom-based 대응 | 빠르게 움직일 수 있다 | 잘못된 레버를 당기기 쉽다 | 피해야 한다 |
| stage-first triage | 복구 방향이 선명해진다 | 초기 분류 훈련이 필요하다 | 대부분의 auth incident |
| aggressive availability recovery | 사용자 영향은 줄일 수 있다 | integrity risk가 커질 수 있다 | integrity가 낮은 stage에서만 |
| scoped recovery matrix | blast radius를 줄인다 | control plane 준비가 필요하다 | 성숙한 운영 환경 |

판단 기준은 이렇다.

- 증상이 아니라 어느 stage가 깨졌는지 분류됐는가
- availability보다 integrity가 더 중요한 사건인가
- scoped recovery lever inventory가 준비돼 있는가
- incident timeline을 남길 수 있는가

---

## 꼬리질문

> Q: auth incident에서 제일 먼저 해야 할 일은 무엇인가요?
> 의도: 증상보다 stage 분류를 먼저 하는지 확인
> 핵심: login/issue/verify/revoke/authz/replay 중 어느 stage 문제인지 고정해야 한다.

> Q: 왜 blast radius를 actor/route/tenant/region으로 보나요?
> 의도: 범위 축소의 중요성을 이해하는지 확인
> 핵심: recovery lever를 전역으로 열지 않고 scoped하게 적용하기 위해서다.

> Q: integrity-high incident에서 위험한 실수는 무엇인가요?
> 의도: availability 압박 속에서도 금지 레버를 기억하는지 확인
> 핵심: global allow, unknown key acceptance, replay bypass 확대처럼 trust boundary를 푸는 것이다.

> Q: triage matrix는 왜 드릴해야 하나요?
> 의도: runbook 실행 가능성을 현실적으로 보는지 확인
> 핵심: 실제 incident에서는 문서보다 muscle memory가 더 많이 작동하기 때문이다.

## 한 줄 정리

Auth incident 대응의 핵심은 사용자 증상에 반응하는 것이 아니라, stage와 blast radius를 먼저 고정한 뒤 integrity risk에 맞는 recovery lever만 제한적으로 쓰는 것이다.
