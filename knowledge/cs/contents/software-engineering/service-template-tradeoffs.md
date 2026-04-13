# Service Template Trade-offs

> 한 줄 요약: service template은 새 서비스를 빠르게 시작하게 하지만, 너무 강한 템플릿은 설계 다양성과 팀의 자율성을 갉아먹을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Service Maturity Model](./service-maturity-model.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)

> retrieval-anchor-keywords:
> - service template
> - scaffold
> - starter kit
> - boilerplate
> - opinionated template
> - template drift
> - developer experience
> - platform scaffolding

## 핵심 개념

서비스 템플릿은 새 서비스 시작을 빠르게 해 주는 scaffold다.

좋은 템플릿은:

- 모니터링
- 로깅
- 배포 설정
- health check
- 기본 정책

을 자동으로 제공한다.

하지만 너무 많은 것을 미리 고정하면, 템플릿이 팀의 문제를 해결하는 대신 **문제를 숨기는 틀**이 된다.

---

## 깊이 들어가기

### 1. 템플릿의 목적은 복제가 아니라 출발 가속이다

템플릿은 모든 서비스를 같게 만들기 위한 것이 아니다.

목표:

- 새 서비스 생성 시간 단축
- 기본 운영 품질 확보
- 실수 방지

### 2. opinionated template는 장단이 뚜렷하다

장점:

- 빠르게 표준화 가능
- 운영 일관성 확보

단점:

- 특수 요구에 맞지 않을 수 있다
- 우회 경로가 생길 수 있다
- template drift가 생긴다

### 3. template drift를 감시해야 한다

처음엔 템플릿을 따르다가 시간이 지나면 수정된 서비스가 늘어난다.

점검:

- 템플릿과 실제 서비스의 차이
- outdated dependencies
- 달라진 observability setup
- 수동 수정 항목

### 4. 템플릿과 policy as code를 같이 써야 한다

서비스 템플릿만으로는 규칙 강제가 어렵다.

그래서:

- 템플릿 = 시작점
- policy as code = 경계
- fitness function = 지속 검증

### 5. 템플릿은 서비스 maturity를 높이는 도구다

기본적인 운영 품질을 자동화해, 새 서비스가 낮은 maturity에서 시작하지 않게 만든다.

---

## 실전 시나리오

### 시나리오 1: 새 서비스가 자주 생긴다

템플릿으로 시작 시간을 줄이고, 공통 운영 품질을 보장한다.

### 시나리오 2: 특수한 배포가 필요한 서비스다

템플릿은 기본으로 두되, 예외 경로를 명시적으로 허용한다.

### 시나리오 3: 템플릿을 따라도 실제 운영이 다르다

template drift를 측정하고 템플릿을 개선한다.

---

## 코드로 보기

```yaml
service_template:
  logging: default
  metrics: default
  deployment: standard
  exceptions: adr_required
```

템플릿은 빠른 시작을 위한 출발점이지, 모든 팀을 묶는 족쇄가 아니다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 최소 템플릿 | 유연하다 | 품질이 들쭉날쭉하다 | 작은 조직 |
| 강한 템플릿 | 표준화가 쉽다 | 우회가 생긴다 | 플랫폼이 성숙할 때 |
| 템플릿 + policy | 출발과 통제를 같이 잡는다 | 관리가 필요하다 | 여러 팀이 동시에 만들 때 |

service template trade-offs는 새 서비스를 빨리 만드는 것과, 각 팀의 요구를 존중하는 것 사이의 균형 문제다.

---

## 꼬리질문

- 템플릿이 강제하는 것은 무엇이고, 허용하는 예외는 무엇인가?
- template drift를 어떻게 감시할 것인가?
- 템플릿을 누가 유지보수하는가?
- 서비스 maturity와 템플릿 정책을 어떻게 연결할 것인가?

## 한 줄 정리

Service template trade-offs는 새 서비스의 시작을 가속하는 표준화와, 팀별 필요를 존중하는 유연성 사이의 균형을 설계하는 문제다.
