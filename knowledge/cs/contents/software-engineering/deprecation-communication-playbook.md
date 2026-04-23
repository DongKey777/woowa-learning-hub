# Deprecation Communication Playbook

> 한 줄 요약: deprecation communication은 기능을 지우겠다는 공지가 아니라, 소비자가 언제 무엇을 바꿔야 하는지 혼란 없이 이해하도록 돕는 운영 커뮤니케이션이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [RFC vs ADR Decision Flow](./rfc-vs-adr-decision-flow.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)
> - [Tombstone Response Template and Consumer Guidance](./tombstone-response-template-and-consumer-guidance.md)

> retrieval-anchor-keywords:
> - deprecation communication
> - sunset notice
> - consumer notice
> - migration timeline
> - communication plan
> - change announcement
> - stakeholder update
> - support channel

## 핵심 개념

기술 종료는 기술만의 문제가 아니다.
소비자와 운영자, 지원팀이 모두 알아야 한다.

deprecation communication playbook은 무엇을 공지할지, 누구에게 언제 알릴지, 어떤 문구로 혼동을 줄일지 정한다.

---

## 깊이 들어가기

### 1. 공지는 "알림"이 아니라 "행동 유도"다

좋은 공지는 다음을 명확히 해야 한다.

- 무엇이 deprecated 되었는가
- 언제까지 쓸 수 있는가
- 무엇으로 바꿔야 하는가
- 누가 영향받는가
- 어디에 문의하는가

### 2. 공지 대상은 여러 층위다

대상:

- 직접 소비자
- 내부 지원팀
- 운영/온콜
- 제품/프로젝트 오너
- 외부 파트너

각각 필요한 정보와 톤이 다르다.

### 3. 일정은 기술 준비보다 먼저 합의해야 한다

공지는 늦으면 migration window가 부족해진다.

보통 필요한 일정:

- 최초 공지
- reminder
- final warning
- sunset day
- post-sunset support policy

### 4. channel strategy가 중요하다

한 채널만 쓰면 놓칠 수 있다.

예:

- 이메일
- 릴리스 노트
- Slack/Teams
- service catalog notice
- dashboard banner

### 5. 공지와 실제 차단은 분리해야 한다

공지 후에도 일정 기간은 기존 경로를 유지해야 한다.
바로 끊으면 공지 자체의 신뢰가 깨진다.

---

## 실전 시나리오

### 시나리오 1: 구 API를 종료한다

초기 공지 후, 소비자별 책임자에게 반복적으로 알리고, 종료일 직전 final warning을 보낸다.

### 시나리오 2: 이벤트 topic을 바꾼다

구 topic 소비자를 파악하고, 새 topic adoption 가이드를 함께 배포한다.

### 시나리오 3: 내부 기능을 플랫폼으로 넘긴다

제품 팀과 플랫폼 팀 모두 같은 종료 문구가 아니라, 각자의 책임 문구를 받아야 한다.

---

## 코드로 보기

```markdown
Announcement template:
- What is changing
- Why it is changing
- Deadline
- Replacement
- Impacted consumers
- Support channel
```

공지 템플릿이 있어야 메시지 품질이 일정해진다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단발성 공지 | 빠르다 | 놓치기 쉽다 | 영향이 작을 때 |
| 다단계 공지 | 안전하다 | 운영 비용이 든다 | 큰 종료 작업 |
| 채널 분산 공지 | 도달률이 좋다 | 관리가 복잡하다 | 소비자가 많을 때 |

deprecation communication은 종료를 알리는 일이 아니라 **소비자가 바꿀 시간을 보장하는 일**이다.

---

## 꼬리질문

- 누구에게 어떤 순서로 공지할 것인가?
- reminder cadence는 충분한가?
- support 채널은 실제로 응답 가능한가?
- 종료일과 migration window는 현실적인가?

## 한 줄 정리

Deprecation communication playbook은 종료 일정과 대체 경로를 명확히 전달해 소비자 혼란을 줄이고 migration을 촉진하는 커뮤니케이션 설계다.
