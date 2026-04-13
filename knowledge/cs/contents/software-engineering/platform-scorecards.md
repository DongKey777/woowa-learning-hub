# Platform Scorecards

> 한 줄 요약: platform scorecards는 플랫폼이 얼마나 잘 쓰이고 있는지가 아니라, 개발자 경험, 채택률, 안정성, 예외 사용량을 함께 보여 주는 운영 지표 체계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)
> - [Service Template Trade-offs](./service-template-tradeoffs.md)
> - [Service Bootstrap Governance](./service-bootstrap-governance.md)
> - [Service Maturity Model](./service-maturity-model.md)
> - [Ownership Metadata Quality](./ownership-metadata-quality.md)

> retrieval-anchor-keywords:
> - platform scorecard
> - platform adoption
> - developer experience
> - exception usage
> - paved road adoption
> - platform reliability
> - platform health
> - self-service metrics

## 핵심 개념

플랫폼은 만들어 놓는 것보다 잘 쓰이게 하는 것이 더 어렵다.

scorecard는 플랫폼의 성공을 한 가지 숫자로 재지 않는다.

- 채택률
- 만족도
- 우회 경로 비율
- provisioning time
- incident rate
- exception count

을 함께 본다.

즉 platform scorecard는 **플랫폼 제품의 운영 성과표**다.

---

## 깊이 들어가기

### 1. 채택률만 보면 안 된다

많이 쓰인다고 좋은 플랫폼은 아니다.

우회 사용이 많으면:

- 정책이 너무 강하거나
- 기능이 부족하거나
- 문서가 부족할 수 있다

### 2. reliability와 DX를 같이 본다

플랫폼이 안정적이어도 쓰기 어렵다면 실패다.
반대로 쓰기 쉬워도 자주 깨지면 실패다.

### 3. exception ratio는 중요한 신호다

예외 경로가 많아지면 paved road가 맞지 않는다는 뜻일 수 있다.

### 4. platform scorecard는 개선 우선순위를 준다

지표가 있으면:

- 어떤 기본 경로를 개선할지
- 어디서 우회가 생기는지
- 어떤 팀이 플랫폼 가치를 못 느끼는지

를 볼 수 있다.

### 5. scorecard는 platform maturity와 연결된다

이 문맥은 [Service Maturity Model](./service-maturity-model.md)과 연결된다.

---

## 실전 시나리오

### 시나리오 1: 플랫폼 도입률이 낮다

문서, onboarding, defaults를 다시 봐야 한다.

### 시나리오 2: 예외가 많이 발생한다

golden path나 bootstrap policy가 너무 딱딱한지 확인한다.

### 시나리오 3: 플랫폼은 안정적인데 만족도가 낮다

DX, 속도, self-service 흐름을 개선해야 한다.

---

## 코드로 보기

```yaml
platform_scorecard:
  adoption_rate: 78
  exception_ratio: 12
  provision_time_minutes: 9
  incident_rate: low
```

scorecard는 숫자를 위한 숫자가 아니라, 플랫폼 개선 결정을 돕는 장치다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 KPI | 보기 쉽다 | 왜곡된다 | 초기 |
| 멀티 metric scorecard | 균형이 좋다 | 해석이 필요하다 | 플랫폼이 커질 때 |
| scorecard + action loop | 개선까지 연결된다 | 운영이 필요하다 | 성숙한 플랫폼 |

platform scorecards는 플랫폼을 "있다/없다"가 아니라 **잘 작동하는 제품**으로 보기 위한 도구다.

---

## 꼬리질문

- 채택률 외에 무엇을 봐야 하는가?
- 예외 비율이 높다는 건 무엇을 의미하는가?
- scorecard 결과를 누가 행동으로 옮기는가?
- 플랫폼 만족도를 어떻게 정량화할 것인가?

## 한 줄 정리

Platform scorecards는 플랫폼의 채택, 안정성, 예외 사용량, DX를 함께 보여 주는 운영 지표 체계다.
