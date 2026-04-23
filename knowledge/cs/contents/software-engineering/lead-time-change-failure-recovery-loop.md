# Lead Time, Change Failure, and Recovery Loop

> 한 줄 요약: lead time, change failure rate, recovery 같은 엔지니어링 지표는 팀 랭킹표가 아니라 배치 크기와 승인 병목, 사고 복구 체계가 어디서 흐름을 막는지 보여 주는 피드백 루프다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Trunk-Based Development vs Feature Branch Trade-offs](./trunk-based-development-vs-feature-branch-tradeoffs.md)
> - [Pair Programming and Code Review Trade-offs](./pair-programming-code-review-tradeoffs.md)
> - [Release Policy, Change Freeze, and Error Budget Coupling](./release-policy-change-freeze-error-budget-coupling.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)

> retrieval-anchor-keywords:
> - lead time
> - change failure rate
> - deployment frequency
> - recovery time
> - DORA metrics
> - engineering metrics
> - delivery flow
> - MTTR

## 핵심 개념

많은 조직이 lead time, deployment frequency, change failure rate, recovery time을 수집한다.
하지만 숫자만 보고 "더 빨라져라"라고 하면 쉽게 왜곡된다.

이 지표는 함께 봐야 의미가 있다.

예:

- deployment frequency가 높아도 change failure rate가 높으면 흐름이 불안정하다
- lead time이 길면 승인 구조나 배치 크기가 문제일 수 있다
- recovery가 느리면 관측성이나 kill switch가 약한 것일 수 있다

즉 엔지니어링 지표의 목적은 점수화가 아니라 **개선 루프를 만드는 것**이다.

---

## 깊이 들어가기

### 1. 지표는 서로 연결된 시스템이다

개별 숫자만 좋아 보여도 전체 흐름은 나빠질 수 있다.

예:

- 배포 횟수를 늘렸지만 hotfix도 같이 늘어남
- lead time을 줄였지만 review 품질이 급락함
- 실패율을 낮추려다 너무 큰 freeze가 생김

그래서 지표는 trade-off를 같이 읽어야 한다.

### 2. 조직 평균보다 서비스와 변경 유형별 분해가 중요하다

전사 평균은 보통 현실을 가린다.

구분 예:

- 핵심 결제 vs 내부 백오피스
- schema change vs UI text change
- 신규 서비스 vs 성숙 서비스

같은 목표치를 모든 변경에 적용하면 잘못된 압박이 생긴다.

### 3. lead time 문제는 승인 병목과 배치 크기에서 자주 생긴다

느린 팀이 꼭 코딩이 느린 것은 아니다.
실제 병목은 다음인 경우가 많다.

- 오래 쌓인 feature branch
- 다단계 승인
- 환경 대기
- 불안정한 테스트
- 수동 배포 체크리스트

따라서 지표를 보면 "더 열심히"가 아니라 **어디서 대기 시간이 쌓이는지**를 봐야 한다.

### 4. change failure rate와 recovery는 운영 설계의 결과다

실패율과 복구 시간은 개발자 조심성만으로 좋아지지 않는다.

영향을 주는 요소:

- rollout granularity
- rollback path
- kill switch
- observability
- incident drill
- runbook quality

즉 recovery metric은 운영 체계가 얼마나 준비됐는지 보여준다.

### 5. metric gaming을 막으려면 해석 문맥이 필요하다

지표가 평가 도구가 되면 왜곡이 생긴다.

예:

- 작은 의미 없는 배포만 늘림
- 위험한 변경을 여러 PR로 쪼개 의미를 잃음
- 실패를 incident로 안 올려 통계를 좋게 만듦

그래서 지표는 보상 체계보다 **리뷰와 학습의 입력**으로 써야 한다.

---

## 실전 시나리오

### 시나리오 1: 배포 빈도는 높지만 장애도 늘어난다

이 경우 목표는 더 많이 배포하는 것이 아니라, batch size와 rollout safety를 줄이는 것이다.

### 시나리오 2: lead time이 길다

코드 작성보다 승인 대기와 QA 대기가 길다면, 문제는 개발 속도가 아니라 흐름 설계다.

### 시나리오 3: 장애는 적지만 복구가 너무 느리다

보수적 배포로 실패율은 낮아도, 사고 시 rollback과 runbook이 약하면 recovery metric이 나빠진다.

---

## 코드로 보기

```yaml
engineering_flow:
  service: checkout
  lead_time_hours: 18
  deployment_frequency_per_week: 12
  change_failure_rate: 0.17
  median_recovery_minutes: 42
  top_bottleneck: manual_approval_queue
```

좋은 지표 대시보드는 숫자보다 다음 행동이 보이게 만들어야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 전사 평균 추적 | 쉽다 | 원인이 안 보인다 | 초기 측정 |
| 서비스별 지표 | 개선 포인트가 보인다 | 관리가 늘어난다 | 여러 팀/서비스가 있을 때 |
| 지표 + 리뷰 루프 | 학습이 된다 | 해석 역량이 필요하다 | 성숙 조직 |

lead time과 change failure, recovery 지표는 경쟁표가 아니라, **흐름을 막는 병목과 운영 취약점을 드러내는 계기판**이어야 한다.

---

## 꼬리질문

- 평균 lead time 뒤에 숨어 있는 대기 시간은 어디인가?
- 실패율을 높이는 변경 유형은 무엇인가?
- recovery time을 줄이기 위해 어떤 운영 장치를 더해야 하는가?
- 지표가 평가 수단으로 변질돼 왜곡되고 있지 않은가?

## 한 줄 정리

Lead time, change failure, and recovery loop는 개발 속도와 운영 안정성을 함께 읽어, 승인 병목과 배포 위험과 복구 약점을 개선 루프로 연결하는 관점이다.
