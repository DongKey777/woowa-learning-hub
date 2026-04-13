# Change Ownership Handoff Boundaries

> 한 줄 요약: change ownership handoff는 업무를 넘기는 것이 아니라, 설계·운영·온콜 책임을 어떤 경계에서 누구에게 넘길지 명확히 정하는 절차다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)

> retrieval-anchor-keywords:
> - change ownership
> - handoff
> - responsibility transfer
> - operator handoff
> - service stewardship
> - release ownership
> - support boundary
> - transition checklist

## 핵심 개념

기능이나 서비스가 바뀔 때, 일을 "넘긴다"는 표현은 너무 넓다.

실제로는 다음 책임이 따로 움직인다.

- 코드 소유
- 배포 소유
- 운영 소유
- 온콜 소유
- 문서 소유
- 고객 커뮤니케이션 소유

change ownership handoff는 이 책임 경계를 안전하게 이동시키는 일이다.

---

## 깊이 들어가기

### 1. handoff는 단일 이벤트가 아니라 단계다

좋은 handoff에는 보통 다음이 있다.

- 사전 공지
- 공동 운영 기간
- 권한/접근 이관
- runbook 업데이트
- 모니터링 확인
- 최종 승인

즉 갑작스러운 책임 이동은 사고 확률을 높인다.

### 2. ownership은 코드보다 먼저 합의되어야 한다

새 팀이 코드만 받고 운영은 옛 팀이 계속 맡으면 경계가 깨진다.

모든 handoff는 다음 질문에 답해야 한다.

- 누가 배포를 승인하는가?
- 누가 장애를 받는가?
- 누가 보정 작업을 수행하는가?
- 누가 고객과 소통하는가?

### 3. handoff 전에 observability를 확인해야 한다

책임을 넘길 때는 상대 팀이 시스템을 읽을 수 있어야 한다.

필수:

- 대시보드
- 알림 채널
- runbook
- 서비스 카탈로그
- ADR 또는 변경 설명

관측이 없으면 책임만 넘겨지고 대응은 못 한다.

### 4. transition period는 안전망이다

공동 운영 기간이 있어야 새 owner가 실제로 문제를 경험하고 학습한다.

이 기간 동안:

- 옛 owner가 backup 역할
- 새 owner가 primary 역할
- 장애 대응을 함께 수행

이렇게 해야 handoff가 문서상 변경이 아니라 실제 운영 전환이 된다.

### 5. handoff 후에도 피드백 루프가 필요하다

이관 후에는 다음을 확인해야 한다.

- 문서가 충분했는가
- runbook이 실제로 쓸모 있었는가
- 온콜 경계가 명확했는가
- 책임이 중복되거나 비어 있지 않은가

이 피드백은 다음 handoff를 개선한다.

---

## 실전 시나리오

### 시나리오 1: 기능이 플랫폼 팀으로 넘어간다

제품 팀에서 운영 공통 기능을 플랫폼 팀으로 이관할 때는, 코드만 넘기지 말고 알림, 배포, runbook, 온콜까지 함께 넘겨야 한다.

### 시나리오 2: 서비스가 다른 팀으로 편입된다

합병 후 소유권이 바뀌면 API 사용처, SLA, 교대표까지 다시 정리해야 한다.

### 시나리오 3: 긴급 장애 대응 후 영구 책임을 재조정한다

임시 대응으로 다른 팀이 대신 맡던 기능을, 사고가 지나면 원래 소유 또는 새 소유로 명확히 돌려놔야 한다.

---

## 코드로 보기

```markdown
Handoff checklist:
- Owner change announced
- Runbook updated
- Alerts transferred
- Dashboards verified
- Primary on-call switched
- Backup shadow period completed
```

handoff는 체크리스트가 없으면 쉽게 누락된다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 이관 | 빠르다 | 누락이 많다 | 작은 변경 |
| 공동 운영 후 이관 | 안전하다 | 시간이 든다 | 핵심 서비스 |
| 단계적 이관 | 균형이 좋다 | 관리 포인트가 많다 | 조직이 큰 경우 |

ownership handoff의 본질은 책임을 옮기는 것이 아니라 **책임이 실제로 수행 가능하게 만드는 것**이다.

---

## 꼬리질문

- 소유권 이관 후 누가 장애를 받는가?
- runbook과 대시보드는 언제 업데이트되는가?
- 공동 운영 기간은 얼마나 둘 것인가?
- 임시 책임과 영구 책임을 어떻게 구분할 것인가?

## 한 줄 정리

Change ownership handoff는 업무 전달이 아니라, 운영 책임과 의사결정 권한을 안전하게 넘기는 전환 절차다.
