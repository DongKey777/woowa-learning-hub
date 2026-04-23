# Configuration Governance and Runtime Safety

> 한 줄 요약: 설정 변경은 코드 배포보다 가볍게 보이기 쉽지만, 실제로는 더 넓은 blast radius를 만들 수 있으므로 configuration governance는 config를 운영 변경으로 취급하고 검증과 점진 배포를 붙이는 방식이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Kill Switch Fast-Fail Ops](./kill-switch-fast-fail-ops.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)

> retrieval-anchor-keywords:
> - configuration governance
> - config as code
> - runtime safety
> - config blast radius
> - configuration rollout
> - config validation
> - dynamic config
> - config drift

## 핵심 개념

운영 사고 중 상당수는 코드가 아니라 설정 변경에서 시작된다.
timeout, retry, rate limit, endpoint, feature exposure, credential rotation 모두 config로 바뀔 수 있다.

문제는 config가 가벼워 보여서 review와 검증을 건너뛰기 쉽다는 점이다.

configuration governance는 다음을 요구한다.

- 누가 바꾸는가
- 무엇을 검증하는가
- 어디까지 퍼지게 하는가
- 잘못되면 어떻게 되돌리는가

즉 config는 파일이 아니라 **운영 중인 시스템의 제어면(control plane)**이다.

---

## 깊이 들어가기

### 1. 모든 config가 같은 위험도를 갖지 않는다

config는 유형별로 나눠 봐야 한다.

예:

- cosmetic: 문구, 색상
- behavioral: timeout, retry, rate limit
- side-effect: 결제, 알림, 쓰기 허용 여부
- secret/security: 키, endpoint, issuer

같은 "설정 변경"이라도 blast radius와 rollback 난이도가 완전히 다르다.

### 2. schema와 validation이 없으면 config는 런타임 코드가 된다

좋은 config 시스템은 단순 key-value 저장소가 아니다.

필요한 것:

- 타입 검증
- 허용 범위 검증
- 필수값 확인
- 환경별 기본값
- deprecated key 경고

즉 config도 compile 단계는 없지만 **입력 계약**은 있어야 한다.

### 3. config rollout도 점진적으로 해야 한다

코드 배포만 canary를 하는 팀이 많다.
하지만 config도 다음처럼 단계적으로 풀어야 한다.

- 특정 환경
- 특정 서비스
- 특정 사용자군
- 특정 트래픽 비율

특히 retry, timeout, write enable 같은 값은 한 번에 전체 반영하면 사고가 커진다.

### 4. emergency override와 audit trail이 필요하다

운영 사고 중에는 빠른 수정이 중요하다.
하지만 빠르게 바꾸는 것과 무기록으로 바꾸는 것은 다르다.

필요한 요소:

- change reason
- operator identity
- change scope
- before/after value
- expiry 또는 재검토 시점

config는 쉽게 바뀌어야 하지만, **쉽게 잊히면 안 된다**.

### 5. config governance는 flag, kill switch, secret rotation과 이어진다

config는 혼자 존재하지 않는다.

- flag는 노출 제어
- kill switch는 긴급 차단
- secret rotation은 보안 운영
- release policy는 변경 허용 범위 제어

이 흐름이 분리되면 운영자는 무엇을 어디서 바꿔야 하는지 헷갈리게 된다.

---

## 실전 시나리오

### 시나리오 1: 결제 timeout을 늘린다

사소해 보이지만 downstream 정체와 thread 고갈로 이어질 수 있다.
이런 변경은 canary와 모니터링 없이 전체 반영하면 위험하다.

### 시나리오 2: 알림 rate limit 값을 바꾼다

너무 느슨하면 외부 연동 폭주가 날 수 있고, 너무 엄격하면 중요한 알림이 누락된다.
값 검증과 rollback 경로가 필요하다.

### 시나리오 3: 잘못된 endpoint로 설정이 바뀐다

코드가 멀쩡해도 전 서비스가 잘못된 외부 시스템을 치게 된다.
config validation과 environment guard가 없으면 피해가 크다.

---

## 코드로 보기

```yaml
config_policy:
  key: payment.retry.max_attempts
  risk_tier: high
  validate:
    min: 0
    max: 3
  rollout:
    strategy: canary
    scope: 10_percent
  rollback: previous_value
```

좋은 config는 값만 저장하지 않고, 위험도와 배포 규칙까지 같이 가진다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 자유 수정 | 빠르다 | 사고가 커지기 쉽다 | 매우 작은 실험 |
| config review + validation | 안전하다 | 속도가 조금 느려진다 | 일반 운영 |
| tiered governance + staged rollout | 가장 안전하다 | 시스템 설계가 필요하다 | 고위험 서비스 |

configuration governance의 목적은 운영자를 느리게 만드는 것이 아니라, **가벼워 보이는 변경이 큰 장애로 번지는 것을 막는 것**이다.

---

## 꼬리질문

- 어떤 config는 즉시 적용 가능하고, 어떤 config는 PRR 수준 검토가 필요한가?
- 설정 변경도 canary 대상인가?
- 잘못된 값을 누가 얼마나 빨리 되돌릴 수 있는가?
- flag, kill switch, secret rotation은 하나의 운영 모델로 보이고 있는가?

## 한 줄 정리

Configuration governance and runtime safety는 설정 변경을 운영 변경으로 보고, 검증과 감사와 점진 배포를 붙여 config로 인한 대형 사고를 줄이는 방식이다.
