# Config Rollback Safety 설계

> 한 줄 요약: config rollback safety 설계는 설정 변경이 코드 버전, 스키마, 라우팅 정책과 어느 범위까지 호환되는지 관리해 잘못된 config 배포 시 빠르게 last-known-good 상태로 복귀할 수 있게 만드는 운영 설계다.

retrieval-anchor-keywords: config rollback safety, last known good config, config compatibility, staged config rollout, config schema evolution, rollback key removal, config freeze, config blast radius, config version skew, safe config deploy, tenant scoped config recovery

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Service Mesh Control Plane 설계](./service-mesh-control-plane-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Failure Injection / Resilience Validation Platform 설계](./failure-injection-resilience-validation-platform-design.md)
> - [Tenant-Scoped Config Incident Recovery 설계](./tenant-scoped-config-incident-recovery-design.md)

## 핵심 개념

많은 장애는 코드가 아니라 config에서 시작된다.
하지만 config는 "텍스트 몇 줄"처럼 보이기 때문에 위험이 과소평가되기 쉽다.

실전에서는 다음이 문제다.

- old binary가 new config shape를 읽지 못함
- key 삭제가 생각보다 rollback을 막음
- policy fan-out이 너무 빨라 blast radius가 큼
- config 자체는 맞아도 dependency readiness와 안 맞음

즉, config rollback safety는 last-known-good만 저장하는 것이 아니라 **어떤 config가 어떤 버전과 호환되는지의 경계를 운영하는 문제**다.

## 깊이 들어가기

### 1. 왜 config rollback이 어려운가

코드 rollback은 artifact 교체로 끝날 수 있지만 config는 runtime에 즉시 퍼진다.
그래서 다음이 문제다.

- 새 key는 추가됐는데 old binary는 모름
- enum 값이 늘었는데 old parser는 crash
- mandatory field로 바뀌어 old client는 해석 실패
- 삭제된 key를 rollback 시 다시 복구해야 함

즉, config는 "실시간 배포된 API"처럼 다뤄야 한다.

### 2. Capacity Estimation

예:

- config consumer 2만 인스턴스
- 주요 policy key 수천 개
- propagation p95 10초
- rollback 목표 1분

이때 봐야 할 숫자:

- convergence time
- stale node ratio
- incompatible parse failure ratio
- rollback completion time
- blast radius per config group

config rollback safety는 validation보다 convergence tail이 더 중요할 때가 많다.

### 3. Compatibility rules

보통 다음을 문서화해야 한다.

- additive change인가
- default 값으로 old binary가 무시 가능한가
- enum / shape 확장이 safe한가
- key removal이 safe한가
- mixed-version fleet에서 읽을 수 있는가

즉, config에도 backward/forward compatibility 표가 필요하다.

### 4. Staged config rollout

안전한 config 배포는 보통 다음 단계다.

1. validation
2. dry-run parse
3. canary consumer subset
4. broad rollout
5. cleanup / removal

코드 없이 config만 바꿔도 canary와 rollback이 필요한 이유가 여기에 있다.

### 5. Last-known-good는 snapshot 하나로 끝나지 않는다

필요한 것:

- per-scope last-known-good
- dependency-aware fallback
- rollback version pin
- frozen override

예를 들어 tenant override가 잘못됐다고 global snapshot까지 되돌릴 필요는 없을 수 있다.

### 6. Dangerous operations

특히 주의할 것:

- key 삭제
- semantic meaning 변경
- retry/timeout 배수 변경
- route target 변경
- authz default 변경

이런 변경은 syntactic validation만 통과해도 운영적으로는 매우 위험할 수 있다.

### 7. Operator ergonomics

운영자는 다음을 즉시 알아야 한다.

- 어떤 config change가 지금 활성화됐는가
- 어느 consumer group이 아직 old version인가
- rollback 가능한가
- 어떤 key removal이 point-of-no-return에 가까운가
- kill switch로 임시 완화 가능한가

즉, config rollback은 "버전 선택" 이상의 운영 UI/UX 문제다.

## 실전 시나리오

### 시나리오 1: mesh retry policy 오배포

문제:

- retry budget을 과도하게 올려 retry storm이 난다

해결:

- mesh policy canary를 먼저 적용한다
- rollback version pin으로 즉시 last-known-good로 되돌린다
- cleanup 전에 키 삭제는 금지한다

### 시나리오 2: new config schema rollout

문제:

- 새 binary는 nested config를 기대하지만 old binary는 flat key만 읽는다

해결:

- additive compatibility window를 만든다
- old/new 둘 다 읽을 수 있는 형태로 일정 기간 유지한다
- old fleet가 사라진 뒤에만 flat key를 제거한다

### 시나리오 3: tenant override 실수

문제:

- 대형 tenant override 하나가 SLA를 망친다

해결:

- scope-local rollback을 지원한다
- global config는 유지한 채 tenant override만 되돌린다
- audit log와 diff를 남긴다

## 코드로 보기

```pseudo
function publishConfig(change):
  validateSyntax(change)
  validateCompatibility(change, activeBinaryVersions())
  rollout.canary(change)
  if canaryHealthy(change):
    rollout.global(change)

function rollback(scope):
  snapshot = lastKnownGood(scope)
  publisher.publish(snapshot)
```

```java
public ConfigRollbackDecision decide(ConfigChange change) {
    CompatibilityCheck check = compatibilityChecker.check(change, fleetVersions.current());
    return rollbackPolicy.decide(check);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Direct global config push | 빠르다 | blast radius가 크다 | low-risk config |
| Staged config rollout | 안전하다 | 절차가 길어진다 | 중요 policy |
| Single last-known-good | 단순하다 | scope-specific rollback이 약하다 | 작은 시스템 |
| Scoped rollback | 유연하다 | metadata 관리가 필요하다 | multi-tenant/platform config |

핵심은 config rollback safety가 rollback 버튼이 아니라 **config shape, version skew, rollout scope, key removal 경계를 함께 관리하는 운영 설계**라는 점이다.

## 꼬리질문

> Q: config는 코드보다 빨리 바꿀 수 있으니 더 안전한 것 아닌가요?
> 의도: runtime config risk 이해 확인
> 핵심: 아니다. 즉시 fan-out되기 때문에 오히려 blast radius가 더 클 수 있다.

> Q: last-known-good만 있으면 충분한가요?
> 의도: scope-aware rollback 이해 확인
> 핵심: 전체 snapshot fallback은 중요하지만, tenant/region/policy 단위 rollback도 필요한 경우가 많다.

> Q: key removal이 왜 위험한가요?
> 의도: rollback boundary 감각 확인
> 핵심: old binary나 old policy가 그 key를 여전히 기대하면 removal이 rollback을 막아 버릴 수 있기 때문이다.

> Q: config도 canary가 필요한가요?
> 의도: config를 release artifact로 보는지 확인
> 핵심: 네. 특히 retry, timeout, route, authz 같은 policy는 코드만큼 위험해 canary가 필요하다.

## 한 줄 정리

Config rollback safety 설계는 설정 변경을 runtime API처럼 다뤄, 호환성 경계와 last-known-good, staged rollout, key removal 정책으로 안전한 되돌리기를 보장하는 운영 설계다.
