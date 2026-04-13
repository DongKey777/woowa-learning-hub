# Production Readiness Review

> 한 줄 요약: production readiness review는 배포 가능 여부를 보는 회의가 아니라, 운영 중 실패를 견딜 준비가 되었는지 검증하는 관문이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Service Maturity Model](./service-maturity-model.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)

> retrieval-anchor-keywords:
> - production readiness review
> - PRR
> - operational readiness
> - rollback readiness
> - observability readiness
> - support readiness
> - launch checklist
> - go-live gate

## 핵심 개념

PRR은 코드를 배포하기 전에 "운영 가능한가"를 확인하는 절차다.

핵심은 기능 완성 여부가 아니라:

- 소유권이 명확한가
- 모니터링이 있는가
- 롤백이 가능한가
- runbook이 준비됐는가
- support 경로가 있는가

즉 PRR은 **launch gate**이자 **risk review**다.

---

## 깊이 들어가기

### 1. PRR은 출시 전 safety check다

점검 항목:

- owner / on-call
- dashboards / alerts
- rollback plan
- feature flag strategy
- capacity / performance assumption
- contract compatibility

### 2. PRR은 기능별이 아니라 서비스별이어야 한다

큰 기능이 아니라 운영 단위로 봐야 한다.

예:

- 새 결제 플로우
- 새 이벤트 발행 경로
- 새 BFF
- 새 배치 job

### 3. PRR은 체크박스가 아니라 판단 회의다

점검표는 필요하지만, 맥락도 봐야 한다.

예:

- 위험은 낮지만 rollback이 어려운가?
- 관측은 충분한가?
- 소비자 migration이 아직 덜 됐는가?

### 4. PRR은 서비스 maturity와 연결된다

성숙도가 낮은 서비스는 PRR에서 더 많은 조건을 요구해야 한다.

이 문맥은 [Service Maturity Model](./service-maturity-model.md)과 연결된다.

### 5. PRR 결과는 남아야 한다

승인/보류/조건부 승인과 그 이유를 기록해야 한다.
그래야 다음 런칭에서 참고할 수 있다.

---

## 실전 시나리오

### 시나리오 1: 새 API를 외부에 공개한다

PRR에서 contract, support, rollback, communication을 확인한다.

### 시나리오 2: 중요한 배치가 처음 운영된다

운영 시간대, kill switch, 재실행 절차, 알림 기준을 봐야 한다.

### 시나리오 3: rollout은 가능하지만 support가 없다

기능은 준비됐더라도 PRR에서 보류해야 한다.

---

## 코드로 보기

```markdown
PRR checklist:
- Owner assigned
- Dashboards ready
- Alerts tested
- Rollback path validated
- Runbook published
- Consumer communication sent
```

PRR은 배포 전에 실패 비용을 줄이는 마지막 관문이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 생략 | 빠르다 | 사고 위험이 크다 | 작은 실험 |
| 가벼운 PRR | 적당히 안전하다 | 놓칠 수 있다 | 일반 기능 |
| 엄격한 PRR | 안전하다 | 시간이 든다 | 핵심 서비스 |

PRR은 출시를 늦추기 위한 문턱이 아니라, **운영 실패를 막기 위한 최종 확인**이다.

---

## 꼬리질문

- 어떤 변경은 PRR이 필수인가?
- PRR 승인자는 누구인가?
- PRR의 실패 기준은 무엇인가?
- 결과를 다음 출시에서 어떻게 회수할 것인가?

## 한 줄 정리

Production readiness review는 서비스가 실제 운영 실패를 견딜 준비가 되었는지 확인하는 릴리스 전 관문이다.
