# Mobile Push Notification Pipeline 설계

> 한 줄 요약: mobile push pipeline은 APNs/FCM을 통해 모바일 기기로 알림을 전달하고, 토큰 수명, collapse, 우선순위, 사용자 선호를 함께 관리하는 시스템이다.

retrieval-anchor-keywords: mobile push, APNs, FCM, device token, collapse key, priority, silent push, token refresh, delivery receipt, notification routing

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Notification 시스템 설계](./notification-system-design.md)
> - [Notification Preferences Graph 설계](./notification-preferences-graph-design.md)
> - [Email Delivery Platform 설계](./email-delivery-platform-design.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)

## 핵심 개념

모바일 push는 단순 알림 전송이 아니다.  
실전에서는 아래를 함께 관리한다.

- device token lifecycle
- APNs/FCM provider integration
- priority and collapse
- quiet hours와 preferences
- silent push
- delivery telemetry

즉, 모바일 push는 OS 제약을 고려한 고신뢰 알림 배달 파이프라인이다.

## 깊이 들어가기

### 1. push 채널의 특성

push는 앱이 종료되어 있어도 도달할 수 있지만, 제약이 많다.

- 토큰이 만료된다
- OS가 메시지를 drop할 수 있다
- 백그라운드 제한이 있다
- 너무 많은 알림은 suppression된다

### 2. Capacity Estimation

예:

- 일 1억 푸시 시도
- 성공률 98%
- 재시도율 3%

실제 병목은 전송량보다 provider rate limit과 device token quality다.

봐야 할 숫자:

- send QPS
- delivery success rate
- token invalidation rate
- collapse rate
- provider response latency

### 3. 파이프라인

```text
Event
  -> Preference Check
  -> Template / Localization
  -> Token Lookup
  -> Provider Adapter
  -> Delivery Tracking
  -> Token Cleanup
```

### 4. token lifecycle

모바일 토큰은 영구적이지 않다.

- app reinstall
- device reset
- OS update
- user opt-out

그래서 invalid token을 빠르게 정리해야 한다.

### 5. collapse와 priority

같은 채널에 알림이 많이 오면 합칠 필요가 있다.

- collapse key
- latest-only semantics
- high priority vs normal priority
- silent push vs visible push

### 6. user preference와 quiet hours

모바일 push도 선호도 그래프와 연결된다.

- marketing push off
- security push on
- quiet hours override

이 부분은 [Notification Preferences Graph 설계](./notification-preferences-graph-design.md)와 함께 보면 좋다.

### 7. telemetry and feedback

push는 delivered 여부를 완전히 알기 어렵다.

- sent
- accepted by provider
- device invalid
- open/click when available

메트릭이 중요하다.  
이 부분은 [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: 결제 보안 푸시

문제:

- 즉시 도착해야 한다

해결:

- high priority push
- user preference override
- fallback in-app notification

### 시나리오 2: 마케팅 푸시 대량 발송

문제:

- burst가 생기고 사용자 반응이 떨어진다

해결:

- rate limit
- collapse
- send window 분산

### 시나리오 3: invalid token 폭증

문제:

- provider 응답에 invalid token이 늘었다

해결:

- token cleanup job
- provider-specific quarantine

## 코드로 보기

```pseudo
function sendPush(event):
  if !preference.allows(event.userId, event.type):
    return
  token = tokenStore.get(event.deviceId)
  result = provider.send(token, buildPayload(event))
  if result.invalidToken:
    tokenStore.delete(token)
```

```java
public void send(NotificationEvent event) {
    pushAdapter.send(event, tokenRepository.lookup(event.deviceId()));
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| direct push | 빠르다 | provider 제약이 크다 | 모바일 핵심 |
| queue-based push | 탄력적이다 | 상태 추적이 필요하다 | 실서비스 |
| collapse-first | 알림 피로를 줄인다 | 일부 메시지 손실 | 빈번한 알림 |
| high-priority only | 도달성이 좋다 | 비용/정책 제한 | 보안/결제 |
| silent push | UX 제어가 좋다 | OS 제약이 많다 | 동기화/백그라운드 |

핵심은 모바일 push가 이메일보다 더 제약이 많고, **OS/provider/token lifecycle을 함께 운영해야 하는 채널**이라는 점이다.

## 꼬리질문

> Q: push token은 왜 자주 바뀌나요?
> 의도: 토큰 lifecycle 이해 확인
> 핵심: 앱 재설치, OS 정책, device 변경으로 바뀔 수 있다.

> Q: collapse key는 왜 필요한가요?
> 의도: 알림 폭주 제어 이해 확인
> 핵심: 같은 종류 알림을 합쳐 사용자를 덜 피로하게 한다.

> Q: silent push는 왜 어려운가요?
> 의도: OS background 제약 이해 확인
> 핵심: 백그라운드 제한과 전달 보장이 약하다.

> Q: 모바일 push와 email은 무엇이 다른가요?
> 의도: 채널별 제약 차이 이해 확인
> 핵심: push는 즉시성과 OS 제약, email은 도달성과 평판이 중심이다.

## 한 줄 정리

Mobile push notification pipeline은 APNs/FCM 제약과 토큰 생명주기, collapse, 선호도를 함께 다루는 모바일 알림 배달 시스템이다.

