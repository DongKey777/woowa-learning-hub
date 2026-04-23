# Config Distribution System 설계

> 한 줄 요약: config distribution system은 서비스 설정을 빠르게 전파하고, 버전 관리와 안전한 롤백을 보장하는 중앙 제어 시스템이다.

retrieval-anchor-keywords: config distribution, push pull hybrid, versioned config, snapshot, rollout, checksum, config cache, propagation delay, last known good, control plane, endpoint routing, bootstrap config, control plane data plane separation, config rollback safety

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)
> - [Config Rollback Safety 설계](./config-rollback-safety-design.md)

## 핵심 개념

Config는 코드에 박아두기 어려운 운영 파라미터다.  
실전에서는 다음을 동시에 만족해야 한다.

- 빠른 전파
- 버전 일관성
- 안전한 롤백
- 환경별 분리
- tenant/region override
- 서비스별 스키마 진화

즉, config distribution은 배포와 운영 사이의 제어 평면이다.

## 깊이 들어가기

### 1. 어떤 config를 다루는가

보통 아래를 포함한다.

- connection timeout
- retry policy
- feature toggles
- endpoint routing
- quota thresholds
- region affinity

코드 상수와 config를 구분하지 않으면 운영 중 변경이 불가능해진다.
특히 endpoint routing과 regional failover 규칙은 service discovery 정책과 어긋나지 않도록 같은 버전 경계에서 관리하는 편이 안전하다.

### 2. Capacity Estimation

예:

- 2,000개 서비스 인스턴스
- 인스턴스당 1분마다 refresh
- 수천 개 config key

이때 중요한 것은 전체 키 수보다 배포 fan-out과 propagation delay다.  
전체 인스턴스가 동시에 pull하면 control plane이 흔들린다.

### 3. Push / pull / hybrid

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| Pull | 단순하다 | 반영 지연이 생긴다 | 초기에 좋다 |
| Push | 빠르다 | 연결 관리가 어렵다 | 긴급 변경 |
| Hybrid | 균형이 좋다 | 구현이 복잡하다 | 실서비스 |

실무에서는 control plane이 변경 이벤트를 푸시하고, data plane은 주기적으로 snapshot을 pull하는 혼합형이 많다.

### 4. Versioning

config는 항상 버전을 가져야 한다.

- current version
- effective version
- rollback version
- last-known-good version

버전이 없으면 장애 시 무엇으로 되돌릴지 알 수 없다.

### 5. Validation

bad config는 배포보다 위험하다.

검증:

- schema validation
- type check
- range check
- dependency check
- canary test

config가 잘못되면 앱 전체가 망가질 수 있으므로, 저장 전에 검증하고 배포 후에도 안전장치가 필요하다.

### 6. 환경 분리

일반적으로 다음을 분리한다.

- dev
- staging
- prod
- region
- tenant override

이 부분은 [멀티 테넌트 SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)와 연결된다.

### 7. Failure mode

가장 중요한 원칙은 "config 시스템이 죽어도 서비스는 돌아야 한다"다.

대응:

- local snapshot
- default config
- fail-open / fail-close 정책
- checksum 검증

## 실전 시나리오

### 시나리오 1: 긴급 timeout 조정

문제:

- 외부 API가 느려졌다

해결:

- timeout config를 control plane에서 조정
- 모든 인스턴스가 새 snapshot을 받음

### 시나리오 2: 잘못된 config 배포

문제:

- 값 하나가 잘못되어 장애가 났다

해결:

- last-known-good로 롤백
- 변경 이력을 audit에 남김

### 시나리오 3: tenant별 override

문제:

- 대형 tenant만 별도 제한이 필요하다

해결:

- tenant override layer를 둔다
- 우선순위 merge 규칙을 명시한다

## 코드로 보기

```pseudo
function resolveConfig(service, tenant, region):
  base = load("global")
  env = load("prod")
  regionOverride = load(region)
  tenantOverride = loadTenant(tenant)
  return merge(base, env, regionOverride, tenantOverride)
```

```java
public ConfigSnapshot current() {
    return snapshotCache.loadOrFallback();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Static config | 단순하다 | 변경이 느리다 | 매우 작은 시스템 |
| Pull-based snapshot | 안정적이다 | propagation 지연 | 기본 선택 |
| Push-based update | 빠르다 | fan-out 복잡도 | 긴급 조정 |
| Hierarchical merge | 유연하다 | 우선순위 실수 가능 | multi-env/tenant |
| Local fallback | 장애에 강하다 | stale risk | 필수 안전장치 |

핵심은 config가 "설정값 저장소"가 아니라 **서비스 동작을 안전하게 바꾸는 배포 인프라**라는 점이다.

## 꼬리질문

> Q: config와 feature flag는 어떻게 다른가요?
> 의도: 운영 설정과 정책/실험 구분 확인
> 핵심: config는 시스템 동작, flag는 기능 노출과 실험이 중심이다.

> Q: 잘못된 config를 어떻게 막나요?
> 의도: validation과 rollback 감각 확인
> 핵심: schema validation, canary, last-known-good가 필요하다.

> Q: push와 pull을 같이 쓰는 이유는 무엇인가요?
> 의도: 전파 지연과 안정성 trade-off 이해 확인
> 핵심: 빠른 반영과 안정적인 fallback을 함께 얻기 위해서다.

> Q: 서비스가 config 서버 없이 살아남아야 하는 이유는 무엇인가요?
> 의도: fail-safe 설계 이해 확인
> 핵심: control plane 장애가 data plane 장애로 번지면 안 되기 때문이다.

## 한 줄 정리

Config distribution system은 안전한 버전 관리와 빠른 전파, 로컬 fallback을 통해 서비스 설정을 운영 가능한 형태로 유지하는 제어 평면이다.
