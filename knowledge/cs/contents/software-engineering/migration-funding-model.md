# Migration Funding Model

> 한 줄 요약: migration funding model은 전환 작업을 "남는 일"로 취급하지 않고, 별도 예산과 책임으로 관리해 지속 가능한 전환을 가능하게 하는 재정 모델이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Brownfield Strangler Org Model](./brownfield-strangler-org-model.md)
> - [Brownfield Modularization Strategy](./brownfield-modularization-strategy.md)
> - [Migration Scorecards](./migration-scorecards.md)
> - [Architecture Runway and Refactoring Window](./architecture-runway-refactoring-window.md)
> - [Architectural Debt Interest Model](./architectural-debt-interest-model.md)

> retrieval-anchor-keywords:
> - migration funding
> - transformation budget
> - refactor funding
> - dual-run cost
> - modernization investment
> - cost allocation
> - migration ROI
> - budget ownership

## 핵심 개념

전환은 일이 많고 오래 걸린다.
그런데 대부분의 조직은 그 비용을 제품 개발 예산에 섞어 놓는다.

그러면 전환은 늘 뒤로 밀린다.

migration funding model은 이 문제를 풀기 위해:

- 전환 예산을 별도로 잡고
- 누가 내는지 정하고
- 무엇에 쓰는지 정의한다

즉 migration은 비용이 아니라 **투자 항목**으로 다뤄야 한다.

---

## 깊이 들어가기

### 1. migration cost는 숨겨지기 쉽다

전환 비용은 다음처럼 분산된다.

- 병행 운영
- shadow compare
- contract updates
- data backfill
- training and support

### 2. funding model이 없으면 전환이 길어진다

예산이 없으면 다들 "나중에"라고 한다.

그러면:

- legacy debt가 쌓이고
- 운영 비용이 늘고
- 장애 risk가 커진다

### 3. funding은 release와 연결될 수 있다

큰 전환은 release train 또는 정기 예산 사이클과 맞춰야 한다.

### 4. ROI를 단기 기능 가치로만 보면 안 된다

전환 ROI에는:

- 장애 감소
- 운영 단순화
- 배포 속도 향상
- 계약 호환성 개선
- 인력 온보딩 단축

이 포함된다.

### 5. funding ownership은 명확해야 한다

누가 예산을 들고 전환 우선순위를 정하는지가 중요하다.

---

## 실전 시나리오

### 시나리오 1: 레거시를 계속 쓰느라 비용이 커진다

전환 funding이 없으면 유지 비용이 더 커진다.

### 시나리오 2: migration squad가 있는데 예산이 없다

전담 조직만 있고 funding이 없으면 전환은 오래 못 간다.

### 시나리오 3: 기능 개발이 전환을 계속 밀어낸다

별도 budget line을 만들어야 한다.

---

## 코드로 보기

```yaml
migration_budget:
  owner: platform-lead
  line_item: modernization
  scope:
    - shadow_traffic
    - backfill
    - contract_adoption
```

전환은 "남는 시간"에 하는 일이 아니라, 예산으로 보장해야 하는 일이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| implicit funding | 쉽다 | 전환이 밀린다 | 거의 없음 |
| dedicated migration budget | 지속 가능하다 | 별도 관리가 필요하다 | 큰 전환 |
| portfolio funding | 전략적이다 | 조직 합의가 필요하다 | 여러 전환이 동시에 있을 때 |

migration funding model은 전환을 의지 문제가 아니라 **재정과 우선순위 문제**로 바꾸는 장치다.

---

## 꼬리질문

- 전환 예산은 누가 소유하는가?
- dual-run 비용을 어떤 기준으로 승인하는가?
- ROI는 기능 가치와 어떻게 비교할 것인가?
- funding이 없을 때 전환 우선순위는 어떻게 정하는가?

## 한 줄 정리

Migration funding model은 전환과 현대화 비용을 별도 예산과 책임으로 다뤄, 장기적인 시스템 진화를 가능하게 하는 재정 전략이다.
