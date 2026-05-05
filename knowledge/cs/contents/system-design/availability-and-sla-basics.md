---
schema_version: 3
title: 가용성과 SLA/SLO/SLI 기초 (Availability and SLA Basics)
concept_id: system-design/availability-and-sla-basics
canonical: true
category: system-design
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- sli-slo-sla-boundary
- availability-vs-latency
- error-budget-policy-threshold
aliases:
- availability basics
- sla 뭐예요
- slo 입문
- sli 기초
- 가용성 계산
- nines availability
- 99.9 percent uptime
- 장애 허용 시간
- 서비스 수준 목표
- sla slo sli 차이
- 고가용성 입문
- downtime 계산
- beginner availability
- error budget 기초
- 처음 availability 뭐예요
symptoms:
- 99.9% 가용성이 실제로 얼마나 자주 깨지는지 감이 안 와
- SLI, SLO, SLA가 맨날 섞여서 뭐가 목표고 뭐가 계약인지 헷갈려
- 에러 버짓을 왜 배포 중단 기준으로 쓰는지 모르겠어
intents:
- definition
prerequisites:
- system-design/system-design-foundations
next_docs:
- system-design/load-balancer-basics
- system-design/request-deadline-timeout-budget-primer
- system-design/backpressure-and-load-shedding-design
linked_paths:
- contents/system-design/backpressure-and-load-shedding-design.md
- contents/system-design/load-balancer-basics.md
- contents/system-design/rate-limiting-basics.md
- contents/system-design/request-deadline-timeout-budget-primer.md
- contents/network/http-methods-rest-idempotency.md
confusable_with:
- system-design/load-balancer-basics
- system-design/backpressure-and-load-shedding-design
forbidden_neighbors: []
expected_queries:
- 가용성 99.9랑 99.99 차이가 실제 다운타임으로 얼마야?
- SLI SLO SLA를 한 번에 구분해서 설명해줘
- 에러 버짓이 왜 배포 중단 기준이 되는지 감이 안 와
- 직렬로 연결된 두 서비스 가용성은 왜 곱해서 계산해?
- 서비스 수준 목표를 잡을 때 nines를 어떻게 해석해야 해?
contextual_chunk_prefix: |
  이 문서는 시스템 설계를 처음 배우는 학습자가 가용성 숫자를 어떻게 읽고,
  SLI, SLO, SLA를 왜 구분하는지, 에러 버짓이 운영 판단과 어떻게 이어지는지
  기초를 잡는 primer다. 업타임 퍼센트 감각, 목표 수치와 계약 차이, 허용 장애
  시간 계산, 직렬 의존성 때문에 전체 신뢰도가 낮아짐, 배포 멈춤 기준 같은
  자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다.
---
# 가용성과 SLA/SLO/SLI 기초 (Availability and SLA Basics)

> 한 줄 요약: SLI는 측정 지표, SLO는 목표 수치, SLA는 계약 조건이며, 가용성은 "시스템이 요청을 정상 처리할 수 있는 시간 비율"이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
- [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: availability basics, sla 뭐예요, slo 입문, sli 기초, 가용성 계산, nines availability, 99.9 percent uptime, 장애 허용 시간, 서비스 수준 목표, sla slo sli 차이, 고가용성 입문, downtime 계산, beginner availability, error budget 기초, availability and sla basics basics

---

## 핵심 개념

가용성(Availability)은 "서비스가 정상적으로 동작하는 시간의 비율"이다.

입문자가 자주 헷갈리는 지점은 **SLI, SLO, SLA가 각각 무엇인가**이다.

- **SLI (Service Level Indicator)**: 실제로 측정하는 지표다. 예: 지난 5분간 성공한 요청 비율.
- **SLO (Service Level Objective)**: 목표 수치다. 예: 성공률을 99.9% 이상으로 유지한다.
- **SLA (Service Level Agreement)**: 계약이다. SLO를 위반하면 페널티(환불, 크레딧)가 생긴다.

쉽게 기억하면: SLI로 측정하고, SLO로 목표를 잡고, SLA로 약속한다.

---

## 한눈에 보기

가용성 "nines" 표:

| 표기 | 가용성 | 연간 허용 다운타임 |
|---|---|---|
| 99% (two nines) | 99% | 약 3.65일 |
| 99.9% (three nines) | 99.9% | 약 8.77시간 |
| 99.99% (four nines) | 99.99% | 약 52분 |
| 99.999% (five nines) | 99.999% | 약 5.26분 |

숫자가 9 하나 늘어날 때마다 허용 장애 시간이 약 10분의 1로 줄어든다.

---

## 상세 분해

### 가용성 계산 기본 공식

```text
가용성 = 정상 동작 시간 / (정상 동작 시간 + 다운 시간)
```

예: 한 달(720시간) 중 7.2시간 장애 → 가용성 = (720 - 7.2) / 720 ≈ 99%.

### 직렬 연결 시 가용성

두 컴포넌트가 직렬로 연결(A → B)되면 전체 가용성은 둘의 곱이다.

- A 가용성 99.9%, B 가용성 99.9%이면, 전체 = 99.9% × 99.9% ≈ 99.8%.

컴포넌트가 늘어날수록 전체 가용성이 낮아진다. 그래서 설계에서 컴포넌트 수를 줄이거나 각 컴포넌트의 가용성을 높이는 노력이 필요하다.

### Error Budget

SLO를 100%에서 빼면 허용 오류 예산이 나온다.

- SLO가 99.9%이면 Error Budget = 0.1%, 한 달 약 43분이다.
- 이 시간 안에서 배포 장애, 점검, 버그를 해결해야 한다.
- Error Budget이 소진되면 신기능 배포를 멈추고 안정성에 집중하는 정책을 쓰기도 한다.

---

## 흔한 오해와 함정

- **"99.9%면 충분하다"**: 결제나 의료 시스템처럼 장애 비용이 높은 서비스는 99.99%가 필요할 수 있다. "충분함"은 도메인과 비용을 함께 봐야 한다.
- **"가용성이 높으면 성능도 좋다"**: 가용성은 "살아있는가"이고, 성능은 "얼마나 빠른가"다. p99 지연이 10초여도 서비스는 살아있을 수 있다.
- **"SLA = SLO"**: SLA는 외부 계약이고 SLO는 내부 목표다. SLO는 SLA보다 엄격하게 잡는 게 일반적이다. 내부 목표를 먼저 위반해야 외부 계약 위반을 막을 수 있다.

---

## 실무에서 쓰는 모습

팀에서 가장 흔하게 쓰는 모습은 SLO 대시보드를 두고 Error Budget을 추적하는 것이다.

1. SLI를 정의한다: "HTTP 5xx가 아닌 응답 비율"
2. SLO를 설정한다: "30일 기준 99.9% 이상"
3. Error Budget을 모니터링한다: "남은 허용 장애 시간: 23분"
4. Error Budget이 빠르게 소진되면 배포를 중단하고 원인을 파악한다.

이 흐름은 SRE(Site Reliability Engineering) 실천의 기반이 된다.

---

## 더 깊이 가려면

- [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md) — 가용성을 지키기 위해 부하를 제어하는 고급 기법
- [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md) — 장애 상황에서 재시도 안전성과 멱등성의 관계

---

## 면접/시니어 질문 미리보기

> Q: SLI, SLO, SLA의 차이를 설명해 주세요.
> 의도: 세 개념을 혼동하지 않고 구분하는지 확인
> 핵심: SLI는 측정 지표, SLO는 목표 수치, SLA는 위반 시 페널티가 있는 계약이다.

> Q: "네 개의 9" 가용성을 달성하려면 어느 정도의 다운타임이 허용되나요?
> 의도: 가용성 nines 감각 확인
> 핵심: 연간 약 52분, 한 달 기준 약 4.38분이다.

> Q: 두 서비스를 직렬로 연결하면 가용성은 어떻게 되나요?
> 의도: 직렬 시스템의 가용성 계산 이해 확인
> 핵심: 두 가용성을 곱한다. 각각 99.9%여도 합치면 약 99.8%로 낮아진다.

---

## 한 줄 정리

가용성은 SLI로 측정하고 SLO로 목표를 잡으며, Error Budget은 SLO에서 남은 허용 오류 시간으로 배포와 안정성 간 균형을 맞추는 기준이 된다.
