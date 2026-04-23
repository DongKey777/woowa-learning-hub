# Consumer Exception Registry Quality and Automation

> 한 줄 요약: consumer exception registry가 신뢰를 얻으려면 단순 입력 폼을 넘어서 stale owner, missing expiry, broken support link, invalid state transition 같은 품질 문제를 자동으로 검출하고 review queue로 보내는 자동화가 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Consumer Exception Registry Templates](./consumer-exception-registry-templates.md)
> - [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md)
> - [Ownership Metadata Quality](./ownership-metadata-quality.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)

> retrieval-anchor-keywords:
> - exception registry quality
> - registry automation
> - stale exception owner
> - invalid state transition
> - missing expiry
> - broken support link
> - registry lint
> - exception data quality

## 핵심 개념

registry는 있어도 품질이 낮으면 다시 안 쓰이게 된다.
특히 예외 registry는 시간이 지나며 빨리 낡는다.

대표 품질 문제:

- owner 없음
- expires_at 없음
- support contact 죽음
- state와 actual usage 불일치
- close됐는데 old path traffic 남음

그래서 registry는 입력받는 시스템이 아니라 **검증하고 경고하는 시스템**이어야 한다.

---

## 깊이 들어가기

### 1. core field validation이 먼저다

자동 체크 기본 예:

- required field missing
- invalid date
- unknown owner/team
- support channel not found
- contract/api id mismatch

이런 기본 검사가 없으면 고급 governance는 의미가 약하다.

### 2. temporal quality가 중요하다

예외 데이터는 시간과 함께 품질이 떨어진다.

봐야 할 것:

- expires_at approaching
- no update for long period
- owner changed in org metadata
- support model changed but registry not updated

즉 registry quality는 static correctness보다 **time-decay 관리**가 더 중요하다.

### 3. state validation은 external signal과 연결돼야 한다

예:

- closed인데 old path still active
- expiring인데 no escalation owner
- blocked인데 no next review date
- active인데 replacement path missing

registry alone이 아니라 telemetry와 ownership metadata와 연결돼야 한다.

### 4. quality automation은 review queue를 만들어야 한다

단순 경고보다 유용한 형태:

- daily stale exception report
- expiring exception queue
- invalid state transition queue
- broken support contract queue

즉 automation은 "문제 있음"을 넘어서 **누가 무엇을 고칠지 보이는 queue**를 만들어야 한다.

### 5. quality metric도 portfolio level로 봐야 한다

예:

- missing expiry ratio
- stale owner ratio
- closed-with-traffic count
- blocked-without-review count

이 지표는 registry 신뢰도를 보여 준다.

---

## 실전 시나리오

### 시나리오 1: closed exception이 많은데 support 문의는 계속 온다

state quality가 무너진 상태일 수 있다.

### 시나리오 2: team rename 뒤 registry owner가 모두 stale해진다

ownership metadata sync가 없으면 registry quality가 급락한다.

### 시나리오 3: allowlist exception이 expiry는 있는데 review가 없다

temporal quality rule과 review queue가 필요하다.

---

## 코드로 보기

```yaml
exception_registry_checks:
  - missing_expiry
  - stale_owner
  - closed_but_traffic_present
  - broken_support_link
```

좋은 registry automation은 누락을 줄이는 동시에 신뢰를 올린다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 수동 품질 관리 | 단순하다 | 금방 낡는다 | 작은 규모 |
| field validation | 기본 신뢰를 준다 | 시간 경과 문제는 약하다 | 초기 registry |
| signal-linked automation | 현실적이다 | 연결 작업이 필요하다 | 성숙한 governance 운영 |

consumer exception registry quality and automation의 목적은 데이터를 예쁘게 만드는 것이 아니라, **예외 registry를 실제 의사결정에 다시 쓸 수 있을 만큼 신뢰 가능한 운영 자산으로 유지하는 것**이다.

---

## 꼬리질문

- registry에서 가장 자주 깨지는 필드는 무엇인가?
- stale owner와 broken support link를 자동으로 잡고 있는가?
- closed state가 실제 usage와 검증되는가?
- registry quality queue가 burn-down review와 연결되는가?

## 한 줄 정리

Consumer exception registry quality and automation은 예외 registry를 time-decay와 telemetry mismatch까지 포함해 검증해, governance가 신뢰할 수 있는 운영 데이터로 유지하게 만드는 방식이다.
