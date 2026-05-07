---
schema_version: 3
title: Email Delivery Platform 설계
concept_id: system-design/email-delivery-platform-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- email delivery platform
- smtp
- esp
- bounce
aliases:
- email delivery platform
- smtp
- esp
- bounce
- complaint
- suppression list
- retry
- queue
- domain reputation
- warmup
- unsubscribe
- Email Delivery Platform 설계
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/notification-system-design.md
- contents/system-design/job-queue-design.md
- contents/network/timeout-retry-backoff-practical.md
- contents/system-design/webhook-delivery-platform-design.md
- contents/system-design/rate-limiter-design.md
- contents/system-design/audit-log-pipeline-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Email Delivery Platform 설계 설계 핵심을 설명해줘
- email delivery platform가 왜 필요한지 알려줘
- Email Delivery Platform 설계 실무 트레이드오프는 뭐야?
- email delivery platform 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Email Delivery Platform 설계를 다루는 deep_dive 문서다. 이메일 전송 플랫폼은 SMTP/ESP 연동, 큐 기반 재시도, 평판 관리, 발송 최적화를 함께 다루는 대규모 메시지 배달 시스템이다. 검색 질의가 email delivery platform, smtp, esp, bounce처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Email Delivery Platform 설계

> 한 줄 요약: 이메일 전송 플랫폼은 SMTP/ESP 연동, 큐 기반 재시도, 평판 관리, 발송 최적화를 함께 다루는 대규모 메시지 배달 시스템이다.

retrieval-anchor-keywords: email delivery platform, smtp, esp, bounce, complaint, suppression list, retry, queue, domain reputation, warmup, unsubscribe

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Notification 시스템 설계](./notification-system-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
> - [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)

## 핵심 개념

Email delivery는 단순 SMTP 호출이 아니다. 실전에서는 아래를 함께 관리해야 한다.

- 발송 큐와 worker pool
- 도메인 평판과 warm-up
- bounce, complaint, unsubscribe 처리
- 템플릿 렌더링과 개인화
- 중복 발송 방지
- retry와 backoff

즉, 이메일 플랫폼은 비동기 메시징과 reputation management의 결합이다.

## 깊이 들어가기

### 1. 어떤 메일을 보내는가

보통 다음으로 나눈다.

- transactional email
- notification email
- marketing email
- system alert email

각 유형은 SLA와 우선순위가 다르다.  
주문 확인 메일과 마케팅 메일을 같은 큐에 넣으면 안 된다.

### 2. Capacity Estimation

예:

- 일 5,000만 통
- 피크 2,000 msg/sec
- 재시도율 5%

이때 발송량보다 더 중요한 것은 provider 제한과 domain throughput이다.  
특히 Gmail, Outlook 같은 수신 도메인별 처리율을 고려해야 한다.

봐야 할 숫자:

- send rate
- bounce rate
- complaint rate
- queue depth
- provider error rate

### 3. 아키텍처

```text
App Event
  -> Email Queue
  -> Template Renderer
  -> Policy / Suppression Check
  -> ESP Adapter
  -> Delivery Tracking
  -> Bounce / Complaint Processor
```

### 4. 발송 평판

이메일은 보내기만 하면 끝이 아니다.

- domain warming
- SPF/DKIM/DMARC
- complaint suppression
- bounce suppression
- list hygiene

평판이 무너지면 같은 메일도 스팸함으로 간다.

### 5. 재시도와 실패 분류

모든 실패를 동일하게 다루면 안 된다.

- transient SMTP error -> retry
- hard bounce -> suppression
- soft bounce -> limited retry
- complaint -> unsubscribe or stop

실패는 분류해야 운영이 가능하다.

### 6. 템플릿과 개인화

메일 내용은 흔히 템플릿으로 생성된다.

- subject template
- body template
- locale-specific rendering
- personalization token

렌더링 실패도 별도 실패로 다뤄야 한다.

### 7. Tracking

메일은 수신 여부와 행동이 중요하다.

- delivered
- opened
- clicked
- bounced
- complained

다만 open tracking은 privacy와 신뢰성 한계가 있다.

## 실전 시나리오

### 시나리오 1: 주문 확인 메일

문제:

- 즉시 도달해야 한다

해결:

- transactional queue 우선
- retry는 짧게
- bounce는 별도 기록

### 시나리오 2: 대량 캠페인 발송

문제:

- 수백만 명에게 보내면 burst가 생긴다

해결:

- domain별 rate limit
- warm-up 단계
- throttling

### 시나리오 3: 스팸 신고 증가

문제:

- 특정 캠페인에서 complaint가 늘었다

해결:

- suppression list 반영
- 세그먼트별 발송 중단
- 평판 지표 점검

## 코드로 보기

```pseudo
function sendEmail(job):
  if suppression.exists(job.recipient):
    return
  rendered = template.render(job.template, job.variables)
  result = esp.send(rendered)
  track(result)
```

```java
public void handle(EmailJob job) {
    if (suppressionService.isSuppressed(job.recipient())) return;
    espClient.send(templateService.render(job));
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Sync SMTP | 단순하다 | 느리고 불안정하다 | 소규모 |
| Async queue | 탄력적이다 | 상태 추적이 필요하다 | 대부분의 서비스 |
| ESP managed | 운영이 쉽다 | vendor lock-in | 빠른 출시 |
| Self-hosted MTA | 제어가 강하다 | 평판 운영이 어렵다 | 대규모 메일 |
| Domain throttling | 안정적이다 | 발송 지연 | 대량 캠페인 |

핵심은 이메일이 단순 전송이 아니라 **수신 성공률과 평판을 지속적으로 관리하는 배달 시스템**이라는 점이다.

## 꼬리질문

> Q: bounce와 complaint는 왜 다르게 다뤄야 하나요?
> 의도: 실패 유형 분류 이해 확인
> 핵심: bounce는 주소/전달 실패, complaint는 사용자 거부 신호다.

> Q: transactional과 marketing을 왜 분리하나요?
> 의도: 우선순위와 평판 격리 이해 확인
> 핵심: 중요한 메일이 캠페인 폭주에 밀리면 안 된다.

> Q: 도메인 warm-up은 왜 필요한가요?
> 의도: reputation management 이해 확인
> 핵심: 새 발송 도메인은 바로 대량 발송하면 스팸 의심을 받는다.

> Q: open tracking은 완벽한가요?
> 의도: observability 한계 이해 확인
> 핵심: privacy와 차단 때문에 정확하지 않을 수 있다.

## 한 줄 정리

Email delivery platform은 큐 기반 발송과 bounce/complaint 처리, 도메인 평판 관리를 결합해 고신뢰 메시지 배달을 제공한다.

