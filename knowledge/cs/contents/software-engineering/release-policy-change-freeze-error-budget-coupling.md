# Release Policy, Change Freeze, and Error Budget Coupling

> 한 줄 요약: change freeze는 무조건 멈추는 규칙이 아니라, progressive rollout과 error budget을 함께 보고 언제 멈추고 언제 밀어붙일지 정하는 release policy다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Kill Switch Fast-Fail Ops](./kill-switch-fast-fail-ops.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [Feature Flag Cleanup and Expiration](./feature-flag-cleanup-expiration.md)
> - [Lead Time, Change Failure, and Recovery Loop](./lead-time-change-failure-recovery-loop.md)
> - [Configuration Governance and Runtime Safety](./configuration-governance-runtime-safety.md)
> - [Operational Readiness Drills and Change Safety](./operational-readiness-drills-and-change-safety.md)
> - [Rollout Guardrail Profiles, Auto-Pause, and Manual Resume](./rollout-guardrail-profiles-auto-pause-resume.md)

> retrieval-anchor-keywords:
> - change freeze
> - progressive rollout
> - error budget
> - release policy
> - release gate
> - rollout pause
> - SLO burn rate
> - launch window

## 핵심 개념

Change freeze는 전통적으로 "지금은 바꾸지 말자"는 운영 규칙처럼 보인다.
하지만 실무에서는 freeze가 정답이 아니라 **어떤 변경을 언제까지 허용할지 결정하는 정책**이다.

특히 다음을 같이 봐야 한다.

- 현재 장애 추세
- SLO/에러 예산 소진 속도
- 배포 위험도
- 롤백 가능성
- 사용자 영향 창구

즉 release policy는 freeze vs rollout의 이분법이 아니라, **위험 허용치를 기준으로 한 동적 제어**다.

---

## 깊이 들어가기

### 1. change freeze는 무조건 멈춤이 아니다

Freeze는 보통 다음 이유로 걸린다.

- 연말/성수기
- 장애 다발 구간
- 데이터 마이그레이션 직후
- 운영 인력이 부족한 기간

하지만 모든 변경을 막으면 오히려 긴급 패치도 못 넣는다.
그래서 freeze에는 예외 규칙이 필요하다.

- hotfix 허용
- security patch 허용
- kill switch 관련 변경 허용
- low-risk config만 허용

### 2. progressive rollout은 freeze의 반대가 아니라 보완이다

롤아웃을 점진적으로 하면, 변경 자체는 계속 흘리되 위험을 작은 단위로 제한할 수 있다.

즉 정책은 보통 이렇게 된다.

- error budget이 충분하면 progressive rollout
- error budget이 빠르게 소진되면 rollout pause
- 사고가 커지면 freeze 또는 kill switch

### 3. error budget은 출시 속도에 대한 제약 조건이다

에러 예산은 단순 SLO 숫자가 아니라, 출시 정책을 바꾸는 신호다.

예를 들어:

- 에러 예산이 충분하면 새 기능을 더 빨리 풀 수 있다
- 에러 예산이 급격히 줄면 launch window를 닫는다
- 예산이 바닥나면 안정화 작업이 우선이다

즉 출시 정책은 제품 팀의 의지보다 **운영 신뢰도**를 반영해야 한다.

### 4. release gate는 지표만이 아니라 맥락도 본다

게이트 조건 예:

- 최근 24시간 5xx 비율
- p95/p99 latency
- 주요 전환율
- 알림 수
- 재시도 증가
- 최근 change failure rate

하지만 수치만 보면 안 되는 경우도 있다.

- 비정상 트래픽이 짧게 몰린 경우
- 외부 의존성 장애가 원인인 경우
- 특정 고객군만 영향받는 경우

그래서 게이트는 수치와 상황을 함께 본다.

### 5. freeze와 rollback은 같은 것이 아니다

Freeze는 앞으로의 변경을 제한하는 것이고, rollback은 이미 들어간 변경을 되돌리는 것이다.

두 정책을 섞으면 사고 대응이 느려진다.

좋은 정책은:

- freeze: 추가 배포 중단
- rollback: 문제 버전 되돌림
- kill switch: 피해 확산 차단
- incident review: 재발 방지

---

## 실전 시나리오

### 시나리오 1: 연말 성수기 freeze

연말에는 신규 기능을 막되, 다음은 허용한다.

- 보안 패치
- 데이터 정합성 보정
- 장애 복구용 hotfix

### 시나리오 2: 에러 예산이 빠르게 소진된다

새 기능 rollout 비율을 높이려 했지만, 최근 장애로 예산이 거의 남지 않았다.

이때는 rollout을 멈추고, 안정화와 관측성 개선이 우선이다.

### 시나리오 3: 작은 설정 변경이지만 배포를 멈춰야 한다

설정 변경이라도 인증, 결제, 데이터 쓰기 경로와 연결되면 freeze 대상이 된다.
즉 코드 양보다 blast radius가 중요하다.

---

## 코드로 보기

```yaml
release_gate:
  require:
    - error_budget_remaining > 20%
    - 5xx_rate < baseline * 1.2
    - rollback_plan: present
  pause_if:
    - burn_rate > 2x
    - incident_open: true
```

release policy는 선언이 아니라 실행 가능한 규칙이어야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| strict freeze | 안정적이다 | 너무 경직될 수 있다 | 대형 이벤트/성수기 |
| progressive rollout | 위험을 분산한다 | 관측 체계가 필요하다 | 일반 릴리스 |
| policy-driven gate | 유연하고 명시적이다 | 운영 규칙이 복잡해진다 | 성숙한 팀 |

release policy는 "배포 가능/불가"를 넘어서 **운영 상태를 반영하는 제어판**이 되어야 한다.

---

## 꼬리질문

- 어떤 지표가 freeze를 트리거해야 하는가?
- error budget은 누가 관리하고 누가 소진 판단을 하는가?
- hotfix 예외는 어떻게 남용을 막을 것인가?
- rollout pause와 incident response는 어떻게 연결되는가?

## 한 줄 정리

change freeze와 progressive rollout은 반대 개념이 아니라, 에러 예산과 운영 신호를 바탕으로 배포 속도를 조절하는 같은 release policy의 두 모드다.
