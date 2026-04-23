# Device / Session Graph Revocation Design

> 한 줄 요약: 실제 사용자 세션은 선형 체인이 아니라 device, browser session, refresh family, step-up grant, downstream token이 연결된 그래프에 가깝기 때문에, revoke 범위와 recovery UX도 그래프 단위로 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Device Binding Caveats](./device-binding-caveats.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
> - [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: device session graph, session graph revocation, refresh family graph, device session lineage, logout all devices graph, step-up grant graph, session inventory, revocation scope graph, device token graph, session inventory UX, operator revoke preview, delegated session graph

---

## 핵심 개념

세션을 보통 "로그인 1회"처럼 생각하지만, 실제 운영 객체는 더 많다.

- device registration
- browser session
- refresh token family
- access token lineage
- elevated/step-up grant
- downstream exchanged token

즉 실제 session model은 리스트보다 그래프에 가깝다.

---

## 깊이 들어가기

### 1. revoke 범위는 그래프의 어떤 절단면을 끊을지 정하는 일이다

예:

- current tab only
- current device only
- current refresh family
- all devices for one account
- all sessions for one tenant admin

이건 결국 그래프에서 어느 노드/엣지를 끊을지의 문제다.

### 2. device와 session은 1:1이 아닐 수 있다

- 한 device에 여러 browser session
- 한 account에 여러 device
- 한 session에서 여러 downstream token

그래서 "모든 기기 로그아웃"은 단순 row delete가 아니라 fan-out 작업이 된다.

### 3. graph를 명시적으로 모델링하면 misuse containment가 쉬워진다

예:

- 한 refresh family만 quarantine
- 특정 device 노드만 disable
- elevated grant만 회수

이렇게 세밀한 대응이 가능하다.

### 4. step-up grant도 session graph의 일부다

민감 작업용 elevated grant는 보통 base session 위에 매달린다.

그래서:

- base session revoke 시 함께 제거
- device mismatch 시 elevated 노드만 먼저 제거
- quarantine 시 base는 유지하되 elevated만 끊기

같은 정책이 자연스럽다.

### 5. downstream exchanged token은 tail 노드처럼 남을 수 있다

특히 BFF/internal exchange 구조에서는:

- base session은 끊겼는데
- 일부 downstream audience token이 짧게 살아 남는다

그래서 graph에서 root만 끊는다고 즉시 모든 tail이 사라지는 것은 아니다.

### 6. session inventory UX도 graph를 반영해야 한다

사용자 UI에서 흔한 오해:

- "기기" 목록만 보여 줌
- 실제론 같은 기기에 여러 세션/브라우저가 있음

더 좋은 UX:

- device + recent session + region + auth time
- current device와 family 분리
- revoke 범위를 명확히 설명

scope naming과 inventory row 설계는 [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)에서 더 구체적으로 이어진다.

operator tooling도 같은 graph를 보더라도 `현재 세션`, `이 기기`, `모든 기기`를 다른 friction으로 노출해야 하며, 이 safety rail은 [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)에서 이어 볼 수 있다.

### 7. audit는 graph traversal이 가능해야 한다

유용한 질의:

- 이 refresh family에 연결된 device는 무엇인가
- 이 step-up grant는 어떤 base session에 매달렸는가
- revoke 이후 어떤 tail token이 마지막으로 accept됐는가

이게 가능해야 incident 대응이 빨라진다.

### 8. graph model은 운영 비용이 있지만 고위험 시스템에 유용하다

필요한 시스템:

- 큰 consumer platform
- multi-device login
- high-risk admin or financial actions
- device binding / step-up / token exchange를 함께 쓰는 구조

---

## 실전 시나리오

### 시나리오 1: "이 기기만 로그아웃"을 눌렀는데 다른 브라우저 탭도 같이 죽는다

문제:

- device와 browser session을 구분하지 않았다

대응:

- device node와 session node를 분리 모델링한다
- UX에서도 범위를 명확히 보여 준다

### 시나리오 2: refresh family를 revoke했는데 일부 API 호출은 잠깐 계속 된다

문제:

- downstream exchanged token tail이 남아 있다

대응:

- root revoke와 tail acceptance를 분리 계측한다
- high-risk route는 direct check나 quarantine를 둔다

### 시나리오 3: risk signal은 한 device에서만 발생했는데 계정 전체가 끊긴다

문제:

- graph 범위보다 상위 수준 revoke만 가능하다

대응:

- device node quarantine를 도입한다
- 강한 compromise가 아닐 땐 family/user-wide revoke를 늦춘다

---

## 코드로 보기

### 1. 간단한 graph 개념

```text
user
 ├─ device A
 │   ├─ browser session 1
 │   │   ├─ refresh family F1
 │   │   └─ step-up grant S1
 │   └─ browser session 2
 └─ device B
     └─ app session 3
```

### 2. 운영 체크리스트

```text
1. device, session, refresh family, step-up grant를 구분하는가
2. revoke 범위를 graph 절단면처럼 설명할 수 있는가
3. root revoke 이후 tail token acceptance를 따로 계측하는가
4. 사용자 UI와 내부 audit가 같은 범위 모델을 공유하는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| flat session list | 구현이 단순하다 | revoke 범위가 거칠다 | 단순 서비스 |
| device + session model | UX와 보안이 좋아진다 | 모델이 복잡해진다 | multi-device consumer app |
| graph-based model | 세밀한 revoke/quarantine 가능 | 저장/쿼리 비용이 높다 | 고위험, 대규모 플랫폼 |
| user-wide revoke only | 구현이 쉽다 | 오탐 비용이 크다 | 제한적 긴급 대응 |

판단 기준은 이렇다.

- multi-device와 step-up grant를 함께 운영하는가
- revoke/quarantine 범위를 세밀하게 제어해야 하는가
- session inventory UX가 중요한가
- incident 대응에서 tail token 추적이 필요한가

---

## 꼬리질문

> Q: session graph라는 표현을 왜 쓰나요?
> 의도: 실제 세션 객체가 여러 계층임을 이해하는지 확인
> 핵심: device, session, family, elevated grant, downstream token이 연결된 구조이기 때문이다.

> Q: refresh family revoke가 왜 모든 것을 즉시 끊지 못할 수 있나요?
> 의도: tail token 문제를 이해하는지 확인
> 핵심: 이미 발급된 access/exchanged token이 잠깐 더 살아 있을 수 있기 때문이다.

> Q: device-only quarantine가 왜 유용한가요?
> 의도: 세밀한 containment 가치를 이해하는지 확인
> 핵심: 한 device의 이상 신호를 계정 전체 revoke 없이 좁게 격리할 수 있기 때문이다.

> Q: UI도 graph 모델을 반영해야 하나요?
> 의도: 사용자 이해와 내부 모델 일치를 보는지 확인
> 핵심: 그렇다. revoke 범위를 사용자가 오해하면 지원 비용과 보안 오해가 커진다.

## 한 줄 정리

고위험 세션 운영의 핵심은 세션을 단일 row로 보는 것이 아니라 device, family, elevated grant, downstream token이 연결된 그래프로 보고 revoke/quarantine 범위를 설계하는 것이다.
