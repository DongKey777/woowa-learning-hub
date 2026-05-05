# Notification Preferences Graph 설계

> 한 줄 요약: notification preferences graph는 사용자 설정, tenant 정책, quiet hours, 필수 알림 예외를 "어느 규칙이 최종 승리하는가"라는 precedence graph로 모델링하는 설계다.

retrieval-anchor-keywords: notification preferences graph, notification preference precedence, quiet hours precedence, mandatory notification override, channel preference graph, tenant policy user override, notification opt in opt out, notification suppression graph, 알림 설정 그래프 뭐예요, quiet hours 왜 무시돼요, 왜 결제 알림은 밤에도 와요, channel override 언제 이기나요, preference policy graph design, notification policy explanation

**난이도: 🔴 Advanced**

관련 문서:

- [Notification 시스템 설계](./notification-system-design.md)
- [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
- [Config Distribution System 설계](./config-distribution-system-design.md)
- [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
- [Permission Model Drift / AuthZ Graph 설계](../security/permission-model-drift-authz-graph-design.md)
- [Feature Flags Rollout / Dependency Management](../software-engineering/feature-flags-rollout-dependency-management.md)

## 이 문서가 먼저 풀어주는 질문

이 문서는 "알림 설정 테이블을 넘어서 어떤 정책 충돌을 설명해야 하는가"가 막힐 때 읽는 graph 설계 문서다.

| learner query shape | 이 문서에서 먼저 고정하는 것 | 다음 문서 |
|---|---|---|
| `알림 설정 그래프가 뭐예요?` | preference를 key-value가 아니라 precedence graph로 본다 | [Notification 시스템 설계](./notification-system-design.md) |
| `왜 결제 알림은 quiet hours인데도 와요?` | mandatory override와 quiet hours의 우선순위를 분리한다 | [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md) |
| `tenant 기본 정책과 사용자 설정이 충돌하면 누가 이겨요?` | policy layer 순서를 먼저 고정한다 | [Config Distribution System 설계](./config-distribution-system-design.md) |
| `사용자에게 왜 이 알림이 갔는지 설명해야 해요` | explainability와 audit trail을 같이 설계해야 함을 묶어 준다 | [Audit Log Pipeline 설계](./audit-log-pipeline-design.md) |

## 추천 학습 경로

처음부터 모든 edge type을 늘리기보다, 먼저 "누가 승리하는가"와 "변경이 얼마나 빨리 반영되는가"를 나눠 보면 덜 헤맨다.

1. precedence 순서가 아직 모호하다면 이 문서에서 `mandatory > tenant > user > channel > quiet hours` 같은 골격을 먼저 잡는다.
2. 전달 지연이나 stale decision이 문제라면 [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)로 내려가 반영 지연을 본다.
3. 정책 배포/버전 관리가 핵심이면 [Config Distribution System 설계](./config-distribution-system-design.md)로 이동한다.
4. 권한 그래프와 비슷한 문제인지 비교하고 싶다면 [Permission Model Drift / AuthZ Graph 설계](../security/permission-model-drift-authz-graph-design.md)로 cross-category 비교를 한다.

## 핵심 개념

알림 선호도는 단순한 설정 테이블이 아니다.  
실전에서는 다음 충돌을 풀어야 한다.

- 채널별 opt-in/opt-out
- 이벤트 타입별 우선순위
- quiet hours
- tenant 정책과 사용자 개인 설정
- 법적/보안 필수 알림
- 중복 suppression

즉, preference system은 사용자 의도를 그래프로 모델링하는 정책 엔진이다.

## 깊이 들어가기

### 1. 왜 그래프인가

설정이 단순 key-value면 쉬워 보이지만, 실제 정책은 계층적이다.

- global default
- tenant policy
- user preference
- channel override
- event-specific exception

이 관계를 그래프로 두면 precedence를 명확히 할 수 있다.

### 2. Capacity Estimation

예:

- 1,000만 사용자
- 사용자당 20개 preference edge
- 알림 평가 초당 10만 회

그럼 읽기 경로가 핵심이다.  
preference lookup은 매우 자주 일어나므로 cacheable해야 한다.

봐야 할 숫자:

- preference lookup QPS
- cache hit ratio
- policy evaluation latency
- override write rate
- invalidation lag

### 3. 정책 우선순위

권장 우선순위 예:

1. legal / security mandatory
2. tenant policy
3. user preference
4. channel availability
5. quiet hours

우선순위를 명시하지 않으면 어떤 설정이 이기는지 모호해진다.

### 4. Quiet hours

조용한 시간은 단순 시간대 설정이 아니다.

- timezone aware
- weekend rule
- emergency exception
- per channel exception

예를 들어 마케팅은 조용한 시간에 막고, 결제/보안은 허용할 수 있다.

### 5. Channel capability

채널마다 지원하는 정책이 다르다.

- email: quiet hours 적용 가능
- push: OS 제한 고려
- sms: 엄격한 opt-in 필요
- in-app: 대부분 허용

### 6. Change propagation

preference 변경은 즉시 반영되어야 한다.

- cache invalidation
- event-driven sync
- versioned snapshot

이것은 [Config Distribution System 설계](./config-distribution-system-design.md)와 닮아 있다.

### 7. Audit and explainability

사용자는 왜 알림을 받았는지 알아야 한다.

- 어떤 rule이 적용됐는지
- 어떤 override가 승리했는지
- quiet hours가 왜 무시/적용됐는지

이력은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)로 남겨야 한다.

## 실전 시나리오

### 시나리오 1: 마케팅 알림 차단

문제:

- 사용자가 광고성 알림을 끄고 싶다

해결:

- channel opt-out
- event type suppression
- tenant default override

### 시나리오 2: 결제 알림은 항상 받아야 함

문제:

- 조용한 시간이어도 보안/결제 알림은 중요하다

해결:

- mandatory policy를 상위로 둔다
- quiet hours보다 우선 적용

### 시나리오 3: tenant별 기본 정책

문제:

- 어떤 고객사는 SMS를 금지한다

해결:

- tenant policy layer
- user override는 tenant 범위 내에서만 허용

## 코드로 보기

```pseudo
function shouldDeliver(user, event, channel, now):
  policy = loadPolicyGraph(user.tenantId)
  decision = evaluatePrecedence(policy, user, event, channel, now)
  return decision.allow
```

```java
public boolean canSend(NotificationContext ctx) {
    return policyEngine.evaluate(ctx).isAllowed();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Flat settings table | 단순하다 | 우선순위 표현이 약하다 | 작은 앱 |
| Graph-based policy | 유연하다 | 해석이 어렵다 | 복잡한 선호도 |
| Cache-first evaluation | 빠르다 | stale risk | high-QPS notification |
| Strong real-time sync | 반영이 빠르다 | fan-out cost | 중요한 변경 |
| Mandatory override layer | 안전하다 | 사용자 통제 약화 | 법/보안 알림 |

핵심은 선호도 시스템이 단순 설정이 아니라 **사용자 의도와 정책 예외를 함께 표현하는 그래프**라는 점이다.

## 꼬리질문

> Q: preferences를 그래프로 모델링하는 이유는 무엇인가요?
> 의도: 정책 우선순위와 예외 처리 이해 확인
> 핵심: global default, tenant policy, user override를 명확히 합성할 수 있다.

> Q: quiet hours보다 중요한 알림은 어떻게 처리하나요?
> 의도: mandatory policy 이해 확인
> 핵심: 보안/결제 같은 필수 알림은 예외로 둔다.

> Q: preference 변경은 얼마나 빨리 반영돼야 하나요?
> 의도: consistency와 UX 균형 이해 확인
> 핵심: 대부분 즉시 또는 매우 짧은 지연이 바람직하다.

> Q: 사용자가 왜 알림을 받았는지 설명할 수 있나요?
> 의도: explainability와 auditability 확인
> 핵심: 정책 경로와 우선순위를 기록해야 한다.

## 한 줄 정리

Notification preferences graph는 채널, 이벤트, 시간대, tenant 정책을 우선순위 그래프로 합성해 알림 전달 여부를 결정하는 시스템이다.
