# Technology Radar and Adoption Governance

> 한 줄 요약: technology radar는 기술 선택을 유행이나 개인 취향으로 결정하지 않고, assess-trial-adopt-hold-retire 같은 상태와 책임을 붙여 조직의 채택과 퇴출을 관리하는 운영 장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)
> - [Service Bootstrap Governance](./service-bootstrap-governance.md)
> - [Golden Path Escape Hatch Policy](./golden-path-escape-hatch-policy.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Dependency Update Strategy and Blast Radius Management](./dependency-update-blast-radius-management.md)

> retrieval-anchor-keywords:
> - technology radar
> - tech radar
> - assess trial adopt hold retire
> - stack governance
> - technology standard
> - framework approval
> - deprecate technology
> - adoption governance

## 핵심 개념

조직이 커질수록 기술 선택은 "좋아 보여서"로 결정하면 안 된다.
어떤 기술은 시험해도 되고, 어떤 기술은 공식 채택하고, 어떤 기술은 더 이상 늘리면 안 된다.

technology radar는 이 상태를 명시한다.

예:

- assess: 조사 중
- trial: 제한된 범위에서 사용
- adopt: 기본 선택지
- hold: 신규 사용 지양
- retire: 퇴출 진행

즉 radar는 기술 목록이 아니라 **채택과 퇴출의 정책 언어**다.

---

## 깊이 들어가기

### 1. radar는 추천 목록이 아니라 lifecycle이다

많은 팀이 radar를 "좋은 기술 리스트"처럼 운영한다.
하지만 실제로 중요한 건 현재 상태와 다음 상태로 가는 조건이다.

예:

- trial -> adopt: 운영 지표와 레퍼런스 서비스 필요
- adopt -> hold: 유지 비용 증가, 인력 감소, 보안 이슈
- hold -> retire: migration path와 종료 일정 확보

상태 전이가 정의되지 않으면 radar는 위키 페이지로 끝난다.

### 2. 채택에는 owner와 기준이 함께 있어야 한다

새 기술을 도입할 때 가장 흔한 실패는 "누가 계속 볼지"가 없는 것이다.

채택 기준 예:

- 어떤 문제를 해결하는가
- 기존 대안보다 무엇이 나은가
- 운영 책임은 누가 지는가
- paved road나 bootstrap에 어떻게 녹일 것인가
- 실패하면 어떻게 철수할 것인가

기술은 도입 순간보다 **유지되는 시간**이 훨씬 길다.

### 3. 표준화와 escape hatch는 같이 설계해야 한다

모든 팀에 단일 스택만 강제하면 우회 경로가 생긴다.
반대로 표준이 약하면 조직 전체가 조각난다.

좋은 운영 방식은 보통 다음과 같다.

- 기본 경로는 adopt 기술로 제공
- 예외는 ADR과 기간을 붙여 허용
- 예외가 반복되면 radar 재평가

즉 radar는 금지 규칙만이 아니라 **예외를 학습하는 장치**여야 한다.

### 4. deprecation은 공지보다 migration이 먼저다

hold나 retire로 바꾸는 것만으로는 실제 퇴출이 일어나지 않는다.

필요한 것:

- 영향 받는 서비스 목록
- 대체 기술
- migration funding
- 지원 종료 날짜
- 보안/운영 리스크 설명

퇴출 경로가 없으면 조직은 계속 낡은 기술을 끌고 간다.

### 5. radar는 문서가 아니라 실행 경로에 연결돼야 한다

radar가 유효하려면 다음과 연결돼야 한다.

- 서비스 템플릿
- dependency policy
- architecture review
- bootstrap defaults
- 기술 부채 정리 계획

즉 radar는 아키텍처 토론의 결과물이 아니라, **새 프로젝트와 변경 흐름에 반영되는 운영 규칙**이다.

---

## 실전 시나리오

### 시나리오 1: 새 workflow engine을 검토한다

바로 전사 표준으로 두지 않고, 한두 서비스에서 trial로 운영한다.
운영 복잡도와 장애 패턴이 검증되면 adopt 여부를 결정한다.

### 시나리오 2: 오래된 tracing 라이브러리를 퇴출한다

hold만 선언하면 아무도 안 움직인다.
instrumentation migration 가이드와 sunset date를 함께 둬야 한다.

### 시나리오 3: 특정 팀이 표준 밖 프레임워크를 원한다

예외를 막연히 금지하지 말고, 왜 기본 경로가 맞지 않는지 기록한다.
그 예외가 반복되면 paved road나 radar가 현실을 못 따라가는 신호다.

---

## 코드로 보기

```yaml
technology_radar:
  - name: workflow-engine-x
    state: trial
    owner: platform-architecture
    exit_criteria:
      - two_services_in_production
      - incident_review_complete
      - migration_path_documented
  - name: tracing-lib-v1
    state: hold
    sunset_date: 2026-12-31
    replacement: tracing-lib-v2
```

좋은 radar는 상태와 책임과 다음 행동이 같이 적혀 있어야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 팀별 자율 선택 | 빠르고 유연하다 | 스택이 파편화된다 | 작은 조직 |
| 엄격한 radar | 일관성이 높다 | 예외가 답답할 수 있다 | 규모가 커지고 운영 비용이 커질 때 |
| radar + escape hatch | 균형이 좋다 | 운영 규칙 설계가 필요하다 | 성장 조직 |

technology radar의 목적은 기술 취향을 통제하는 것이 아니라, **채택 비용과 퇴출 비용을 조직이 감당 가능하게 만드는 것**이다.

---

## 꼬리질문

- trial에서 adopt로 올리는 기준은 무엇인가?
- hold 기술을 언제까지 허용할 것인가?
- 예외 요청이 많다면 radar가 틀린 것인가, paved road가 약한 것인가?
- retire 대상 기술의 migration 비용은 누가 부담하는가?

## 한 줄 정리

Technology radar and adoption governance는 기술을 선택하는 표가 아니라, 채택과 퇴출과 예외를 상태 기반으로 관리해 스택 파편화를 줄이는 운영 장치다.
