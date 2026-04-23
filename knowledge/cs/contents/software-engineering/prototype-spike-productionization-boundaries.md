# Prototype, Spike, and Productionization Boundaries

> 한 줄 요약: spike와 prototype은 학습을 위한 산출물이고 productionization은 별도의 작업인데, 이 경계를 흐리게 두면 임시 코드가 운영 책임과 규제를 떠안는 시스템으로 조용히 굳어 버린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Prototype, Spike, and Productionization Boundaries](./README.md#prototype-spike-and-productionization-boundaries)
> - [Golden Path Escape Hatch Policy](./golden-path-escape-hatch-policy.md)
> - [Service Bootstrap Governance](./service-bootstrap-governance.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Technology Radar and Adoption Governance](./technology-radar-adoption-governance.md)
> - [Architecture Runway and Refactoring Window](./architecture-runway-refactoring-window.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)

> retrieval-anchor-keywords:
> - prototype
> - spike
> - productionization
> - experiment to production
> - proof of concept
> - temporary system
> - graduation criteria
> - hardening path
> - endless pilot

## 핵심 개념

spike, prototype, PoC는 모두 가치가 있다.
문제는 이 산출물이 목적을 다한 뒤에도 "일단 돌아가니까"라는 이유로 운영 경로에 남는 경우다.

구분은 다음처럼 보는 편이 좋다.

- spike: 기술 불확실성을 줄이기 위한 짧은 탐색
- prototype: 사용자 흐름이나 운영 가설을 빠르게 검증
- productionization: 운영 가능성, 보안, 관측성, 소유권을 붙이는 단계

즉 prototype이 성공했다고 해서 바로 production-ready인 것은 아니다.

---

## 깊이 들어가기

### 1. spike의 산출물은 학습이지 자산이 아니다

spike는 빠르게 버릴 수 있어야 한다.

보통 의도:

- 기술 선택 검증
- 성능 가능성 확인
- 라이브러리/프레임워크 적합성 확인

따라서 spike 코드에 장기 구조를 요구하면 속도가 죽고, 반대로 spike 코드를 그대로 남기면 운영 부채가 쌓인다.

### 2. prototype은 사용자 가치를 보지만 운영 책임은 보장하지 않는다

prototype이 검증하는 것:

- 이 흐름이 유용한가
- 이 UX가 통하는가
- 이 연동이 가능한가

prototype이 보장하지 않는 것:

- 보안 검토
- on-call readiness
- rollback
- auditability
- lifecycle management

그래서 prototype 성공 이후에는 productionization backlog가 필요하다.

### 3. productionization은 별도 예산과 일정이 필요하다

많은 팀이 prototype 이후 바로 고객에게 노출하고, hardening을 "나중에" 하려 한다.
하지만 실제로는 이 단계가 가장 비싸다.

보통 필요한 작업:

- ownership 지정
- observability 추가
- config/secret 관리
- failure mode 정리
- PRR와 runbook
- 정책/컴플라이언스 반영

즉 productionization은 포장 작업이 아니라 **운영 가능성 확보 프로젝트**다.

### 4. escape hatch와 expiry를 붙여야 임시가 영구가 되지 않는다

실험 시스템이 운영 경로에 들어가는 것을 완전히 막을 수는 없다.
하지만 통제는 가능하다.

예:

- 실험용 경로에 명시적 label
- 만료 날짜
- 제한된 사용자군
- 예외 승인
- sunset review

이 장치가 없으면 prototype은 조용히 핵심 의존성이 된다.

### 5. graduation criteria가 있어야 경계가 선다

"좀 안정화되면 옮기자"는 보통 실행되지 않는다.

좋은 기준 예:

- service owner 지정
- SLO 초안 작성
- observability minimum 확보
- security review 완료
- rollout/rollback path 확인

즉 prototype에서 production으로 가는 문턱은 취향이 아니라 **체크 가능한 기준**이어야 한다.

---

## 실전 시나리오

### 시나리오 1: 배치 스크립트가 점점 중요해진다

처음엔 운영자가 수동 실행하던 스크립트가 매일 돌고 있다면, 이제는 productionization 대상으로 봐야 한다.

### 시나리오 2: AI 추천 prototype이 바로 서비스에 붙는다

데모는 잘 됐지만 model drift, fallback, cost guardrail이 없으면 운영 서비스로 보기 어렵다.

### 시나리오 3: admin 도구가 핵심 장애 대응 도구가 된다

이 경우 권한, 감사 로그, 가용성까지 붙여야 한다.
"내부 도구니까 괜찮다"는 말로 끝나지 않는다.

---

## 코드로 보기

```yaml
prototype_path:
  owner: growth-team
  user_scope: beta_users
  expires_at: 2026-08-01
  graduation_requirements:
    - observability_minimum
    - service_owner_assigned
    - rollback_plan
    - security_review
```

임시 산출물이 살아남아도 되지만, 그때는 임시가 아니라 운영 시스템으로 다뤄야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| spike 유지 금지 | 깔끔하다 | 학습 결과 재활용이 어렵다 | 리스크가 큰 환경 |
| prototype 빠른 출시 | 시장 검증이 빠르다 | 운영 부채가 쌓인다 | 제한된 실험 |
| explicit productionization stage | 안전하다 | 일정과 예산이 더 든다 | 실험이 실제 서비스로 이어질 때 |

prototype과 productionization의 경계를 세우면 실험 속도가 느려지는 것이 아니라, **임시 코드가 핵심 시스템이 되는 순간을 통제할 수 있게 된다**.

---

## 꼬리질문

- 이 산출물은 학습을 위한 것인가, 운영을 위한 것인가?
- 언제부터 productionization budget이 필요해지는가?
- prototype이 운영 경로에 들어갈 때 만료와 범위 제한이 있는가?
- graduation criteria 없이 "일단 운영"이 되고 있지 않은가?

## 한 줄 정리

Prototype, spike, and productionization boundaries는 탐색용 산출물과 운영 시스템의 경계를 분리해, 임시 코드가 무심코 핵심 운영 자산으로 굳는 것을 막는 관점이다.
