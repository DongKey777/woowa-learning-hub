# Decision Revalidation and Supersession Lifecycle

> 한 줄 요약: 좋은 architecture decision flow는 ADR을 작성하는 순간 끝나지 않고, 어떤 신호가 오면 결정을 다시 검토하며, supersede/retire/exception 중 어떤 경로로 바꿀지까지 포함하는 lifecycle이어야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Decision Revalidation and Supersession Lifecycle](./README.md#decision-revalidation-and-supersession-lifecycle)
> - [RFC vs ADR Decision Flow](./rfc-vs-adr-decision-flow.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Architecture Exception Process](./architecture-exception-process.md)
> - [Technology Radar and Adoption Governance](./technology-radar-adoption-governance.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)

> retrieval-anchor-keywords:
> - decision revalidation
> - superseded ADR
> - decision lifecycle
> - assumption expiry
> - decision revisit
> - architecture re-review
> - revalidation trigger
> - decision sunset

## 핵심 개념

아키텍처 결정은 만들어지는 순간부터 낡기 시작한다.
당시에는 맞았던 판단도 팀 구조, 트래픽, 비용, 기술 표준, 장애 패턴이 바뀌면 더 이상 맞지 않을 수 있다.

그래서 decision flow는 보통 다음까지 포함해야 한다.

- 처음 결정하는 흐름
- 다시 볼 신호
- 바꾸지 않을 근거
- supersede / retire / exception 처리

즉 decision governance의 핵심은 "한 번 잘 정하자"가 아니라 **언제 다시 볼지 미리 정해 두는 것**이다.

---

## 깊이 들어가기

### 1. 결정은 영구 사실이 아니라 당시 제약의 산물이다

많은 ADR이 실패하는 이유는 결정 자체보다 제약이 바뀌었다는 사실을 문서가 따라가지 못하기 때문이다.

예:

- 팀이 둘에서 여섯으로 늘어남
- 트래픽 규모가 10배 증가
- 표준 스택이 hold/retire 상태로 바뀜
- 비용 구조가 달라짐

이 경우 옛 결정은 틀렸다기보다 **전제 조건이 만료된 것**이다.

### 2. revalidation trigger를 명시해야 한다

좋은 lifecycle은 언제 다시 볼지 미리 정한다.

대표 trigger:

- 반복 incident
- budget/SLO 위반
- 기술 radar 상태 변경
- 조직 구조 변경
- 예외가 반복 연장됨
- migration 또는 deprecation 시작

trigger가 없으면 문서는 쌓이지만 실제 결정은 자동으로 재평가되지 않는다.

### 3. 변경 경로는 amend보다 supersede가 더 명확할 때가 많다

예전 ADR을 계속 수정하면 히스토리가 흐려질 수 있다.
이럴 때는 새 결정으로 supersede하는 편이 낫다.

보통 선택지:

- keep: 아직 유효함
- amend: 작은 사실 보정
- supersede: 핵심 전제 변경
- retire: 더 이상 관련 없음
- exception: 원칙은 유지하되 제한적 예외 허용

즉 revalidation의 결과도 몇 가지 상태로 명확히 표현해야 한다.

### 4. decision lifecycle은 구현과 gate까지 닫혀야 한다

새 ADR만 쓰고 정책/코드가 안 바뀌면 아무 일도 안 일어난다.

연결 대상 예:

- policy as code
- service template
- PRR checklist
- rollout gate
- technology radar entry

decision lifecycle은 문서 체계가 아니라 **실행 체계의 메타 레이어**다.

### 5. revalidation은 blame가 아니라 learning loop여야 한다

과거 결정이 지금은 맞지 않다는 사실은 실패가 아니다.
오히려 조직이 성장하며 판단 기준이 바뀌었다는 신호다.

좋은 질문:

- 당시 어떤 제약 때문에 이 결정을 했는가?
- 지금 무엇이 달라졌는가?
- 전환 비용을 감당할 가치가 있는가?

이 질문이 없으면 팀은 오래된 결정을 비판만 하거나, 반대로 신성불가침처럼 다룬다.

---

## 실전 시나리오

### 시나리오 1: shared library 전략이 한계에 도달한다

처음엔 빠른 재사용을 위해 맞았지만, 팀과 서비스가 늘면서 version drift와 배포 결합이 커졌다.
이때는 platform service 방향으로 supersede할지 다시 검토해야 한다.

### 시나리오 2: 예외가 계속 연장된다

특정 아키텍처 예외가 세 번 연장됐다면, 원칙이 현실과 안 맞거나 migration 계획이 실패한 것이다.
exception을 계속 늘리기보다 ADR 재검토가 필요하다.

### 시나리오 3: 기술 표준이 hold 상태가 된다

technology radar에서 hold가 되면 새 사용만 막는 것으로 끝내지 말고, 관련 ADR의 전제도 다시 봐야 한다.

---

## 코드로 보기

```yaml
decision_record:
  id: ADR-021
  status: accepted
  revalidation_triggers:
    - repeated_incident
    - slo_breach_for_2_weeks
    - technology_radar_state_change
  review_by: 2026-11-01
  superseded_by: null
```

좋은 decision record는 과거 이유뿐 아니라 다시 볼 신호도 남긴다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 결정 후 방치 | 빠르다 | 오래될수록 위험하다 | 거의 없음 |
| 정기 재검토 | 낡은 전제를 빨리 찾는다 | 관리 비용이 든다 | 핵심 구조 결정 |
| trigger-based revalidation | 현실적이다 | 신호 설계가 필요하다 | 성숙한 조직 |

decision revalidation의 목적은 결정을 자주 뒤집는 것이 아니라, **더 이상 맞지 않는 전제를 조용히 방치하지 않는 것**이다.

---

## 꼬리질문

- 이 결정이 다시 검토돼야 할 신호는 무엇인가?
- 작은 amendment와 supersede를 어떤 기준으로 나눌 것인가?
- repeated exception이 decision flaw의 신호는 아닌가?
- revalidation 결과가 실제 policy와 template와 gate에 반영되는가?

## 한 줄 정리

Decision revalidation and supersession lifecycle은 아키텍처 결정을 일회성 합의가 아니라, 전제 변화와 운영 신호에 따라 다시 평가되고 계승되는 수명주기로 다루는 방식이다.
