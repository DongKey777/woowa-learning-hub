# Service Ownership and Catalog Boundaries

> 한 줄 요약: 서비스 카탈로그는 서비스 목록이 아니라, 누가 무엇을 소유하고 어떤 경계로 책임지는지 즉시 찾게 해 주는 운영 메타데이터다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [BFF Boundaries and Client-Specific Aggregation](./bff-boundaries-client-specific-aggregation.md)

> retrieval-anchor-keywords:
> - service ownership
> - service catalog
> - ownership boundary
> - domain steward
> - operational metadata
> - on-call ownership
> - dependency map
> - service registry

## 핵심 개념

서비스가 많아질수록 "어떤 서비스가 무엇을 책임지는가"를 즉시 알아야 한다.
그래서 서비스 카탈로그는 단순 목록이 아니라 **책임 경계의 인덱스**여야 한다.

좋은 카탈로그는 다음을 알려준다.

- 누가 소유하는가
- 어떤 도메인에 속하는가
- 어떤 SLA를 가지는가
- 어떤 의존성이 있는가
- 어디서 연락해야 하는가
- 어떤 문서와 ADR을 따라야 하는가

즉 카탈로그는 검색용 전화번호부가 아니라 **운영 책임의 지도**다.

---

## 깊이 들어가기

### 1. 소유권이 없으면 경계도 없다

서비스 분리는 코드가 아니라 책임의 분리다.

소유권이 모호하면 다음이 생긴다.

- 장애 때 책임 전가
- 배포 승인 지연
- 문서 미갱신
- 계약 테스트 누락

그래서 서비스마다 owner, backup owner, domain steward를 명시해야 한다.

### 2. 서비스 카탈로그는 기술 목록보다 운영 연결이 중요하다

좋은 카탈로그 항목:

- 서비스 이름
- 목적
- owner 팀
- on-call 채널
- 런북 링크
- ADR 링크
- 주요 의존 서비스
- 배포 방식

이 정보가 있어야 인시던트나 전환 작업에서 바로 연결된다.

### 3. 카탈로그는 경계의 단일 원본이 아니다

서비스 카탈로그가 문서의 최상위 진실이 되면 안 된다.
실제 진실은 코드, 배포 설정, runbook, ADR, 모니터링에 흩어져 있다.

카탈로그의 역할은 이를 묶어주는 것이다.

- 어디서 볼지 안내
- 무엇이 최신인지 안내
- 누가 갱신해야 하는지 안내

### 4. ownership boundary는 도메인 boundary와 맞춰야 한다

코드 모듈 경계와 팀 경계가 어긋나면 운영이 복잡해진다.

좋은 방향:

- 한 팀이 하나의 주요 도메인 경계를 소유
- BFF, ACL, schema policy도 같은 책임 단위로 묶기
- 의존성은 명시적으로 기록

이 주제는 [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)와 직접 연결된다.

### 5. catalog hygiene가 없으면 오래 못 간다

카탈로그가 실효성을 가지려면 다음이 필요하다.

- 갱신 책임자
- 변경 시 체크리스트
- stale entry 탐지
- 배포/온콜과의 동기화

문서가 최신이 아닐수록 운영은 구두 의존으로 돌아간다.

---

## 실전 시나리오

### 시나리오 1: 장애가 났는데 누가 소유자인지 모른다

카탈로그가 있으면:

- owner 팀 확인
- on-call 연락
- runbook 연결
- 관련 ADR 확인

### 시나리오 2: BFF가 여러 개인데 책임이 겹친다

BFF를 분리하면 좋아 보이지만, 소유 경계가 없으면 공통 정책이 중복된다.
카탈로그는 각 BFF가 어떤 클라이언트를 책임지는지 분명히 해야 한다.

### 시나리오 3: 신규 합류자가 서비스 지도를 못 읽는다

카탈로그가 없으면 신규 인원은 코드 검색부터 시작한다.
카탈로그가 있으면 의존성과 운영 책임을 빠르게 찾는다.

---

## 코드로 보기

```markdown
Service: order-bff
Owner: commerce-platform
Domain: ordering
On-call: #commerce-oncall
Runbook: ./runbooks/order-bff.md
ADR: ./adr/adr-014-bff-per-client.md
Dependencies: order-service, payment-service, shipping-service
```

이런 메타데이터가 실제 운영에서는 길을 만든다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단순 목록 | 유지가 쉽다 | 책임이 안 보인다 | 서비스가 적을 때 |
| 상세 카탈로그 | 운영 연결이 좋다 | 유지비가 든다 | 서비스가 많고 사고가 잦을 때 |
| 카탈로그 + ADR + runbook 링크 | 추적성이 좋다 | 관리가 더 필요하다 | 조직이 커질 때 |

서비스 카탈로그는 장식이 아니라, **책임을 찾는 시간을 줄이는 인프라**다.

---

## 꼬리질문

- 서비스마다 owner와 backup owner가 명시되어 있는가?
- 카탈로그가 runbook, ADR, on-call과 연결되어 있는가?
- stale 서비스가 자동으로 드러나는가?
- 도메인 경계와 팀 경계가 크게 어긋나지 않는가?

## 한 줄 정리

서비스 카탈로그는 서비스의 존재를 나열하는 문서가 아니라, 책임과 경계를 즉시 찾게 해 주는 운영 메타데이터 체계다.
