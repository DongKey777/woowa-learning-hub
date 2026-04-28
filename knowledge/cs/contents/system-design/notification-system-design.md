# Notification 시스템 설계

> 한 줄 요약: 알림 시스템은 이벤트를 여러 채널로 전달하면서 중복, 순서, 우선순위, 재시도를 함께 다루는 분산 메시징 설계다.

retrieval-anchor-keywords: notification system design, notification architecture, 알림 시스템 설계, 알림 시스템 뭐예요, notification system basics, 처음 배우는데 알림 시스템, 알림 큰 그림, push email sms in-app 차이, 알림 채널 언제 나누나요, notification queue, notification retry backoff, 알림 중복 왜 생기나요, idempotency dedup, user notification preference, delivery status read status, notification routing

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [메시지 큐 기초](./message-queue-basics.md)
> - [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
> - [Email Delivery Platform 설계](./email-delivery-platform-design.md)
> - [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
> - [Duplicate Suppression Windows](../database/duplicate-suppression-windows.md)
> - [Domain Events vs Integration Events](../design-pattern/domain-events-vs-integration-events.md)

---

## 핵심 개념

알림 시스템은 "이벤트를 보여주는 UI"가 아니라, **사용자에게 전달 가능한 상태로 바꾸는 파이프라인**이다.
처음 배우는데 헷갈리면 "알림함 화면"보다 "이벤트를 큐에 넣고 채널별로 배달하는 흐름"으로 먼저 잡는 편이 이해가 빠르다.

여기서 다뤄야 하는 문제:

- in-app, email, push, SMS를 어떻게 나눌 것인가
- 실패한 전달을 어떻게 재시도할 것인가
- 중복 알림을 어떻게 막을 것인가
- 사용자 선호도와 채널 우선순위를 어떻게 반영할 것인가
- 대규모 burst를 어떻게 흡수할 것인가

알림 시스템은 보통 push와 pull을 같이 쓴다.

- push: 즉시 보내기
- pull: 앱 열었을 때 재확인

---

## 깊이 들어가기

### 1. 요구사항 분리

먼저 확인해야 할 질문:

- 실시간성이 중요한가
- 유실이 허용되는가
- 읽음/확인 상태가 필요한가
- 사용자별 채널 설정이 있는가
- 마케팅 알림과 시스템 알림을 분리해야 하는가

알림은 대부분 "즉시성"보다 "신뢰성"이 중요하다.  
따라서 순서와 재시도 정책을 먼저 정해야 한다.

### 2. 채널 분리

채널별로 실패 양상이 다르다.

| 채널 | 장점 | 단점 | 특징 |
|------|------|------|------|
| In-app | 즉시 표시 | 앱이 떠 있어야 함 | 상태 관리가 쉽다 |
| Push | 모바일 친화적 | 토큰 만료/OS 제약 | 운영 복잡도가 높다 |
| Email | 범용적 | 지연이 크다 | 비동기 처리에 적합 |
| SMS | 전달률이 높다 | 비용이 크다 | 중요 알림에 사용 |

알림은 채널별 어댑터를 따로 두는 편이 안전하다.

### 3. 이벤트와 중복 제거

알림은 같은 이벤트가 여러 번 들어올 수 있다.  
그래서 idempotency key가 필요하다.

흐름:

1. 도메인 이벤트 생성
2. notification job에 적재
3. idempotency key로 중복 제거
4. 채널별 전송
5. 성공/실패 상태 기록

### 4. 우선순위와 라우팅

모든 알림이 같은 급은 아니다.

- 보안/로그인: 높은 우선순위
- 주문/결제: 높은 우선순위
- 마케팅: 낮은 우선순위

우선순위가 있는 경우 queue를 분리해야 한다.  
하나의 큐에 섞으면 중요한 알림이 밀린다.

### 5. 재시도와 백오프

외부 전송은 실패가 기본이다.

필요한 정책:

- timeout
- retry
- exponential backoff
- dead-letter queue
- circuit breaker

이 부분은 [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)과 강하게 연결된다.

### 6. 상태 모델

알림 상태는 보통 이렇게 간다.

```text
created -> queued -> sent -> delivered -> read
                    \-> failed -> retrying
```

상태가 많아질수록 운영은 쉬워지지만, 제품과 분석 복잡도도 같이 올라간다.

### 7. 데이터 모델

핵심 테이블 예시:

- notification_event
- user_notification_setting
- notification_delivery
- notification_template

조회 패턴은 보통 "내 알림함 최신순"이므로 정렬 인덱스와 pagination cursor가 중요하다.

---

## 실전 시나리오

### 시나리오 1: 주문 완료 알림

주문 완료는 시스템 핵심 알림이다.

설계:

- 이벤트 발행
- in-app + push 동시 처리
- 중복 제거
- 실패 시 재시도

### 시나리오 2: 마케팅 대량 발송

수백만 사용자에게 동시에 보내면 burst가 생긴다.

대응:

- rate limit
- queue 분리
- 발송 창 분산
- 사용자별 opt-out 확인

### 시나리오 3: 모바일 토큰 만료

푸시 토큰이 만료되면 실패가 연속 발생한다.

대응:

- 실패 토큰 격리
- 토큰 refresh job
- 실패율 메트릭

---

## 코드로 보기

```pseudo
function publishNotification(event):
    if dedup.exists(event.id):
        return

    dedup.save(event.id, ttl=24h)
    queue.publish(event)
```

```java
public void handle(NotificationEvent event) {
    if (dedupRepository.exists(event.id())) {
        return;
    }

    dedupRepository.save(event.id(), Duration.ofHours(24));
    notificationQueue.publish(event);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|-------------|
| Sync send | 구현이 단순 | 지연과 실패가 사용자에게 직접 전파 | 아주 작은 서비스 |
| Async queue | 탄력적이다 | 상태 추적이 복잡하다 | 대부분의 실서비스 |
| Push 우선 | 즉시성 좋다 | OS/토큰 관리가 필요 | 모바일 중심 |
| Pull 우선 | 단순하고 안정적 | 즉시성이 떨어진다 | 조회형 알림 |

알림은 빠르게 보내는 것보다, **중복 없이 적절한 채널로 보내는 것**이 더 중요하다.

## 꼬리질문

> Q: 같은 알림을 여러 번 보내지 않으려면 어떻게 하나요?
> 의도: idempotency와 dedup 설계 이해 여부 확인
> 핵심: 이벤트 id 기반 중복 제거가 필요하다

> Q: 마케팅과 시스템 알림을 같은 큐에 넣으면 왜 안 되나요?
> 의도: 우선순위와 장애 격리 이해 여부 확인
> 핵심: 중요한 알림이 밀리고 운영상 격리가 안 된다

## 한 줄 정리

알림 시스템은 채널 전송이 아니라 중복, 우선순위, 재시도를 다루는 이벤트 파이프라인이다.
