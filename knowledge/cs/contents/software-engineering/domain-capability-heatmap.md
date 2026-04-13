# Domain Capability Heatmap

> 한 줄 요약: domain capability heatmap은 도메인과 서비스의 중요도, 병목, 위험, 성숙도를 시각화해 어디에 먼저 투자할지 보여 주는 전략 맵이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Capability-Based Roadmap Planning](./capability-based-roadmap-planning.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Organizational Coupling and Conway Effects](./organizational-coupling-conway-effects.md)
> - [Migration Scorecards](./migration-scorecards.md)
> - [Service Maturity Model](./service-maturity-model.md)

> retrieval-anchor-keywords:
> - capability heatmap
> - domain capability
> - business value map
> - bottleneck visualization
> - maturity visualization
> - risk heatmap
> - capability prioritization
> - investment map

## 핵심 개념

capability heatmap은 도메인 기능을 색으로만 보는 게 아니라, 어디가 중요한지, 어디가 막혔는지, 어디가 위험한지를 함께 보는 시각화다.

보통 축은 다음을 포함한다.

- business value
- operational risk
- maturity
- dependency bottleneck
- change frequency

즉 heatmap은 **전략적 투자 지도를 만드는 도구**다.

---

## 깊이 들어가기

### 1. heatmap은 우선순위가 아니라 패턴을 보여 준다

어떤 capability가 붉다는 것은 단순히 나쁘다는 뜻이 아니다.

병목인지, 위험인지, 고가치인지 구분해야 한다.

### 2. capability는 서비스 경계를 넘어선다

하나의 capability가 여러 서비스에 분산될 수 있다.
그래서 heatmap은 서비스 목록이 아니라 능력 구조를 봐야 한다.

### 3. 색만 보면 안 된다

색상은 요약이고, 뒤에 지표가 있어야 한다.

예:

- red: 높은 risk, 낮은 maturity
- yellow: 변화 잦음, 개선 중
- green: 안정적

### 4. heatmap은 roadmap과 연결된다

heatmap에서 붉은 영역부터 runway, migration, review를 잡는다.

### 5. heatmap은 org coupling도 보여 준다

어떤 capability가 특정 팀에만 묶여 있으면 병목이 드러난다.

---

## 실전 시나리오

### 시나리오 1: 어디부터 리팩터링할지 모르겠다

heatmap에서 변경 빈도와 리스크가 높은 capability를 먼저 본다.

### 시나리오 2: 플랫폼 투자를 어디에 할지 모르겠다

관측성, 계약 안정성, rollout capability가 붉은지 본다.

### 시나리오 3: 조직 간 책임이 꼬여 있다

capability를 기준으로 소유 경계를 다시 그린다.

---

## 코드로 보기

```yaml
capability_heatmap:
  checkout:
    value: high
    risk: high
    maturity: medium
  reporting:
    value: medium
    risk: low
    maturity: high
```

heatmap은 시각 자료이지만, 의사결정 자료여야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 목록만 보기 | 쉽다 | 우선순위가 흐리다 | 작은 시스템 |
| heatmap | 한눈에 보인다 | 해석이 필요하다 | 여러 capability가 있을 때 |
| heatmap + scorecard | 전략과 실행이 연결된다 | 관리가 필요하다 | 성장하는 조직 |

domain capability heatmap은 도메인 전체를 색으로 요약해 **투자와 전환 우선순위**를 보이게 하는 지도다.

---

## 꼬리질문

- 어떤 축으로 heatmap을 만들 것인가?
- 색을 만든 근거 데이터는 무엇인가?
- heatmap 결과가 roadmap에 실제 반영되는가?
- capability와 서비스 경계는 얼마나 일치하는가?

## 한 줄 정리

Domain capability heatmap은 도메인 capability의 가치, 위험, 성숙도, 병목을 시각화해 투자 우선순위와 구조 개선 방향을 보여 주는 전략 맵이다.
