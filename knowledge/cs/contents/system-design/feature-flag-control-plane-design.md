# Feature Flag Control Plane 설계

> 한 줄 요약: feature flag control plane은 기능 노출을 동적으로 제어하고, 점진 배포와 실험, 장애 격리를 안전하게 운영하는 정책 시스템이다.

retrieval-anchor-keywords: feature flag control plane, rollout, kill switch, targeting, evaluation, bucketing, experimentation, flag cache, approval workflow, config sync, progressive delivery, canary guardrail, automated canary

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Entitlement / Quota 설계](./entitlement-quota-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)

## 핵심 개념

feature flag는 단순한 `if` 문이 아니다.  
실전에서는 다음을 동시에 제어해야 한다.

- 점진적 롤아웃
- kill switch
- 실험 버킷 분배
- tenant/user/region targeting
- 승격 승인과 감사 로그
- SDK와 서버의 일관된 평가

즉, control plane은 정책을 관리하고, data plane은 정책을 빠르게 평가한다.

## 깊이 들어가기

### 1. 무엇을 제어할 것인가

flag는 보통 아래 용도로 나뉜다.

- release flag
- experiment flag
- ops flag
- permission flag

각 flag는 수명과 위험도가 다르다.  
release flag는 짧고, permission flag는 오래 가며, ops flag는 즉시 꺼져야 한다.

### 2. Capacity Estimation

예:

- 10만 DAU
- 요청당 flag 20개 평가
- 초당 5만 evaluation

이때 control plane의 쓰기보다 evaluation path가 훨씬 중요하다.  
그래서 대부분은 local cache와 snapshot 기반 평가를 쓴다.

봐야 할 숫자:

- evaluation QPS
- config sync latency
- cache hit ratio
- rollout propagation delay
- override rate

### 3. Control plane / data plane 분리

```text
Admin UI / API
  -> Flag Store
  -> Audit Log
  -> Config Publisher
  -> CDN / Snapshot Store
  -> SDK / Gateway Evaluator
```

control plane은 변경, 승인, 이력, 롤백을 담당한다.  
data plane은 현재 시점의 flag를 빠르게 판정한다.

### 4. Targeting과 bucketing

대부분의 롤아웃은 아래 조건을 조합한다.

- userId
- tenantId
- region
- device
- plan
- percentage

stable bucketing이 중요하다.  
같은 사용자는 항상 같은 bucket에 들어가야 실험이 흔들리지 않는다.

### 5. Rollout 전략

일반적인 단계:

1. internal only
2. 1%
3. 10%
4. 50%
5. 100%

롤아웃을 할 때는 오류율, latency, business metric을 같이 본다.  
기능 자체가 좋아 보여도 p95가 망가지면 바로 되돌릴 수 있어야 한다.
즉, flag는 "누구를 새 경로로 보낼지"를 정하는 도구이고, 실제 승격 안전성은 shadowing, tracing, canary guardrail과 함께 봐야 한다.

### 6. 승인과 감사

flag는 제품 기능이자 운영 권한이다.

- 누가 켰는지
- 어떤 범위로 켰는지
- 언제 롤백했는지
- 승인자가 누구인지

이력은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)와 연결된다.

### 7. Failure mode

flag 시스템이 죽으면 두 가지 위험이 있다.

- 새 기능을 켤 수 없다
- 이미 켜진 기능의 평가가 느려진다

대응:

- last-known-good snapshot
- safe default
- local fallback evaluator

## 실전 시나리오

### 시나리오 1: 점진 배포

문제:

- 새 API를 전체 사용자에게 바로 열 수 없다

해결:

- 내부 사용자부터 시작
- 퍼센트 롤아웃
- 에러율 기준 자동 rollback

### 시나리오 2: 장애 차단

문제:

- 특정 백엔드 기능이 장애를 일으킨다

해결:

- kill switch를 즉시 전파
- evaluator는 local fallback으로 안전하게 off를 유지

### 시나리오 3: A/B 테스트

문제:

- 실험군과 대조군을 안정적으로 나눠야 한다

해결:

- stable bucketing
- experiment versioning
- metric guardrail

## 코드로 보기

```pseudo
function evaluateFlag(user, flag):
  snapshot = cache.get("flags:snapshot")
  if snapshot == null:
    snapshot = loadLastKnownGood()
  return snapshot.evaluate(user, flag)
```

```java
public boolean isEnabled(UserContext ctx, String flagKey) {
    FlagSnapshot snapshot = snapshotCache.current();
    return snapshot.evaluate(ctx, flagKey);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Client-side evaluation | 빠르다 | 정책 노출 가능 | 단순 실험 |
| Server-side evaluation | 통제가 쉽다 | 서버 비용 증가 | 보안/정책 중요 |
| Snapshot cache | 안정적이다 | propagation 지연 | 대부분의 서비스 |
| Push-based sync | 반영이 빠르다 | 운영 복잡도 | 빠른 롤아웃 |
| Pull-based refresh | 단순하다 | stale 가능성 | 초기 시스템 |

핵심은 flag가 설정값이 아니라 **운영 정책과 실험 계약**이라는 점이다.

## 꼬리질문

> Q: feature flag와 config는 어떻게 다른가요?
> 의도: 동적 정책과 정적 설정 구분 확인
> 핵심: flag는 의사결정과 실험이 중심이고, config는 시스템 동작 파라미터가 중심이다.

> Q: stable bucketing이 왜 중요한가요?
> 의도: 실험 일관성 이해 확인
> 핵심: 사용자가 매 요청마다 다른 그룹에 들어가면 실험이 깨진다.

> Q: flag 시스템이 장애나면 어떻게 하나요?
> 의도: control plane 실패 대응 확인
> 핵심: last-known-good snapshot과 safe default가 필요하다.

> Q: kill switch는 왜 별도로 강조하나요?
> 의도: 운영 대응 감각 확인
> 핵심: 장애 확산을 빠르게 끊는 최후 방어선이기 때문이다.

## 한 줄 정리

Feature flag control plane은 변경 가능한 정책을 안전하게 배포하고 빠르게 평가해, 롤아웃과 실험, 장애 대응을 통합하는 시스템이다.
