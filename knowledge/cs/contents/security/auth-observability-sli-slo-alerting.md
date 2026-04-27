# Auth Observability: SLI / SLO / Alerting

> 한 줄 요약: 인증과 인가의 운영 품질은 단순 401 카운트가 아니라, login, token issuance, verification, JWKS refresh, revocation, decision logging을 단계별로 계측하고 bucketed failure와 propagation lag를 함께 보는 observability 설계로 결정된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
> - [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)
> - [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)
> - [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
> - [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
> - [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
> - [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)
> - [Security README: Incident / Recovery / Trust](./README.md#incident--recovery--trust)

retrieval-anchor-keywords: auth observability, authentication SLI, authorization telemetry, auth SLO, JWKS metrics, token verification metrics, 401 spike alerting, revocation lag, auth dashboards, security telemetry, decision metrics, identity error budget, shadow evaluation, replay store outage, trust boundary bypass, session store outage, security observability bridge, incident observability bundle, security readme observability bridge, beginner fallback observability, auth observability beginner fallback, observability primer return path, security readme return anchor

## Beginner Fallback

이 문서는 운영 관측 설계를 깊게 다룬다. beginner라면 metric taxonomy를 바로 늘리기 전에 먼저 `signal -> decision -> audit` 3칸 mental model부터 고정하는 편이 안전하다.

- 첫 입구로 되돌아가려면 [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)
- security primer 묶음으로 한 단계 올라가려면 [Security README: 기본 primer](./README.md#기본-primer)
- observability 관련 갈래를 다시 고르려면 [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기), [Security README: 운영 / Incident catalog](./README.md#운영--incident-catalog)

---

## 핵심 개념

인증 장애를 "로그인 안 됨" 한 줄로만 보면 복구가 늦어진다.
인증/인가는 단계가 많고, 각 단계마다 다른 장애 모드와 다른 지표가 필요하다.

대표 단계:

- login / callback
- token issuance / refresh
- JWT verification / introspection
- JWKS fetch / cache refresh
- session revoke / logout propagation
- authorization decision

즉 auth observability의 핵심은 "identity path를 stage별 pipeline으로 나누고, 각 단계의 실패 bucket과 전파 지연을 계측하는 것"이다.

---

## 깊이 들어가기

### 1. audit log와 operational telemetry를 구분해야 한다

둘 다 중요하지만 목적이 다르다.

- audit log: 나중에 누가 무엇을 했는지 증명
- operational telemetry: 지금 어디가 망가졌는지 탐지

audit log가 있다고 해서 운영 대시보드가 되는 것은 아니다.
반대로 metric만 있다고 forensic이 되는 것도 아니다.

### 2. 401 수치 하나로는 아무것도 구분되지 않는다

같은 401이라도 실제 의미는 다르다.

- malformed token
- expired token
- issuer mismatch
- `kid` miss
- JWKS timeout
- claim validation failure
- route misconfiguration

그래서 error taxonomy를 먼저 정하고, metric label은 그 taxonomy를 따라야 한다.

### 3. stage별 핵심 SLI를 따로 둬야 한다

예시:

- login success rate
- callback latency
- token issuance success rate
- refresh success rate
- JWT verification failure rate by bucket
- JWKS refresh latency / error rate
- revocation propagation lag
- authz decision latency
- deny rate by reason code

이렇게 나눠야 "IdP는 살아 있는데 JWKS path만 죽음" 같은 상황이 보인다.

### 4. propagation lag는 availability만큼 중요하다

보안 시스템은 "응답했다"로 끝나지 않는다.

- logout가 몇 초 뒤 반영되는가
- key rotation이 verifier fleet에 몇 분 뒤 반영되는가
- policy 변경이 authz cache에 얼마나 늦게 퍼지는가

이런 freshness SLI가 없으면 revoke/key/policy incident를 늦게 발견한다.

### 5. high-cardinality 설계를 통제해야 한다

auth telemetry는 라벨이 너무 많아지기 쉽다.

- user id
- tenant id
- `jti`
- route
- device id

이걸 metric에 그대로 넣으면 시스템이 감당을 못 한다.

실전 원칙:

- metric에는 bucketed label만 둔다
- 세부 식별자는 structured log나 trace에 둔다
- issuer, client type, route class, failure bucket 정도로 제한한다

### 6. alert는 절대치보다 변화율과 조합이 중요하다

좋은 alert 예:

- `kid_miss_after_refresh` 급증
- 특정 issuer에서만 verification error 급증
- refresh success rate 급락 + reuse detection 급증
- revocation lag p95 급증
- back-channel logout 처리량은 정상인데 local session revoke count가 0

즉 "401이 많다"보다 "어느 failure bucket이 어떤 scope에서 튀는가"가 더 중요하다.

### 7. security signal과 rollout signal을 같이 봐야 오탐을 줄인다

보안 이상으로 보이지만 실제론 배포 문제일 수 있다.

- 새 verifier 버전 rollout 후 only new pods에서 `alg_mismatch`
- app release 직후 device binding mismatch 급증
- region migration 뒤 only one AZ에서 JWKS timeout

그래서 release version, region, cluster, route class 같은 운영 컨텍스트도 auth telemetry에 필요하다.

### 8. dashboard는 질문 단위로 구성하는 편이 좋다

유용한 질문:

- 지금 login 문제인가, verification 문제인가, authorization 문제인가
- 어느 issuer/client class/region이 터졌는가
- revocation과 logout propagation이 늦는가
- misuse signal이 rollout bug인지 실제 compromise인지

그래프를 기술 요소별로 나열하는 것보다, incident 질문에 맞춰 배치하는 편이 낫다.

---

## 실전 시나리오

### 시나리오 1: 401이 급증했는데 로그인도 되고 refresh도 된다

문제:

- verification path만 흔들리는 상황일 수 있다

대응:

- `jwt_verification_failure_bucket`을 본다
- `kid_miss`, `jwks_timeout`, `claim_invalid` 중 무엇이 튀는지 본다
- issuer/region/pod version으로 분리한다

### 시나리오 2: revoke는 호출됐는데 실제 로그아웃 체감이 느리다

문제:

- propagation lag를 계측하지 않았다

대응:

- revoke request 시각과 마지막 accept 시각 차이를 본다
- refresh family revoke, session store invalidation, downstream cache bust를 따로 계측한다

### 시나리오 3: misuse alert가 폭증했는데 실제로는 앱 배포였다

문제:

- auth signal에 release dimension이 없다

대응:

- app version, platform, region 태그를 붙인다
- security anomaly와 release anomaly를 같은 대시보드에서 본다
- auto-revoke는 shadow confidence가 높을 때만 켠다

---

## 코드로 보기

### 1. verification metric 예시

```java
metrics.counter(
        "auth.jwt.verification.failures",
        "issuer", issuer,
        "failure_bucket", failureBucket,
        "route_class", routeClass,
        "verifier_version", verifierVersion
).increment();
```

### 2. propagation lag 측정 개념

```java
Duration lag = Duration.between(revocationRequestedAt, lastAcceptedAt);
metrics.timer("auth.revocation.propagation.lag", "scope", "refresh_family").record(lag);
```

### 3. 최소 대시보드 질문

```text
1. 어느 stage가 실패하는가: login / issue / verify / revoke / authorize
2. 어느 bucket인가: malformed / kid_miss / jwks_timeout / scope_deny / reuse_detected
3. 어느 범위인가: issuer / region / route_class / release_version
4. freshness는 어떤가: key rollout lag / revocation lag / policy propagation lag
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 단순 401/403 카운트 | 구현이 쉽다 | 원인 분류가 거의 안 된다 | 초기 수준, 임시 관측 |
| bucketed auth metrics | 장애 분류가 빨라진다 | taxonomy 관리가 필요하다 | 대부분의 실서비스 |
| 고카디널리티 전부 metric | 세부 분석이 쉬워 보인다 | 비용과 cardinality 폭발이 난다 | 보통 피해야 한다 |
| metric + structured log + trace 조합 | 운영과 forensic을 함께 잡는다 | 설계와 운영이 더 복잡하다 | 중대형 서비스, 보안 요구가 큰 환경 |

판단 기준은 이렇다.

- 인증/인가 장애를 몇 분 안에 bucket 분류해야 하는가
- key rotation, revoke propagation 같은 freshness 요구가 있는가
- misuse detection과 rollout anomaly를 같이 구분해야 하는가
- observability 비용과 cardinality를 통제할 수 있는가

---

## 꼬리질문

> Q: audit log가 있는데 왜 auth observability가 또 필요한가요?
> 의도: 증거 로그와 운영 지표를 구분하는지 확인
> 핵심: audit log는 사후 증명용이고, observability는 실시간 탐지와 복구용이기 때문이다.

> Q: 왜 401 카운트만으로는 부족한가요?
> 의도: failure bucket 분류의 필요를 아는지 확인
> 핵심: malformed token, kid miss, jwks timeout, claim mismatch가 모두 401처럼 보일 수 있기 때문이다.

> Q: propagation lag는 왜 보안 지표인가요?
> 의도: revoke/key/policy freshness를 운영 지표로 보는지 확인
> 핵심: 로그아웃, key rotation, 권한 회수가 늦게 반영되면 보안 창이 길어지기 때문이다.

> Q: auth telemetry에서 cardinality를 왜 조심해야 하나요?
> 의도: observability 시스템의 현실 제약을 이해하는지 확인
> 핵심: user id나 jti를 metric label로 넣으면 비용과 성능 문제가 급증한다.

## 한 줄 정리

Auth observability의 핵심은 401 수치를 세는 것이 아니라, identity path를 stage와 failure bucket으로 나누고 key/revoke/policy 전파 지연까지 함께 측정하는 것이다.
