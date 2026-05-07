---
schema_version: 3
title: Webhook Sender Hardening
concept_id: security/webhook-sender-hardening
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- webhook sender
- outbound webhook
- retry policy
- delivery id
aliases:
- webhook sender
- outbound webhook
- retry policy
- delivery id
- signing secret
- timeout
- backoff
- dead letter
- endpoint validation
- delivery ordering
- circuit breaker
- Webhook Sender Hardening
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/webhook-signature-verification-replay-defense.md
- contents/security/api-key-hmac-signature-replay-protection.md
- contents/security/secret-management-rotation-leak-patterns.md
- contents/security/ssrf-egress-control.md
- contents/security/rate-limiting-vs-brute-force-defense.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Webhook Sender Hardening 핵심 개념을 설명해줘
- webhook sender가 왜 필요한지 알려줘
- Webhook Sender Hardening 실무 설계 포인트는 뭐야?
- webhook sender에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Webhook Sender Hardening를 다루는 deep_dive 문서다. webhook sender는 "보내면 끝"이 아니라, 재시도, 서명, 타임아웃, 대상 검증, 순서 보장을 포함한 outbound 보안 경계를 운영해야 한다. 검색 질의가 webhook sender, outbound webhook, retry policy, delivery id처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Webhook Sender Hardening

> 한 줄 요약: webhook sender는 "보내면 끝"이 아니라, 재시도, 서명, 타임아웃, 대상 검증, 순서 보장을 포함한 outbound 보안 경계를 운영해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Webhook Signature Verification / Replay Defense](./webhook-signature-verification-replay-defense.md)
> - [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md)
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [SSRF / Egress Control](./ssrf-egress-control.md)
> - [Rate Limiting vs Brute Force Defense](./rate-limiting-vs-brute-force-defense.md)

retrieval-anchor-keywords: webhook sender, outbound webhook, retry policy, delivery id, signing secret, timeout, backoff, dead letter, endpoint validation, delivery ordering, circuit breaker

---

## 핵심 개념

webhook sender는 외부 시스템으로 이벤트를 전달하는 outbound 컴포넌트다.  
받는 쪽만 안전하게 해서는 부족하고, 보내는 쪽도 오작동이나 악용에 강해야 한다.

핵심 책임:

- 대상 endpoint 검증
- signing
- 타임아웃과 retry 정책
- 순서와 중복 처리 전략
- dead letter 처리
- secret 보호

즉 sender hardening은 "외부로 나가는 메시지의 품질과 안전성"을 통제하는 일이다.

---

## 깊이 들어가기

### 1. sender는 retry storm을 만들 수 있다

send 실패에 대해 무작정 재시도하면 문제가 커진다.

- 대상 시스템이 이미 죽어 있다
- 지연이 누적된다
- 큐가 쌓인다
- 같은 이벤트가 반복 전송된다

그래서 exponential backoff와 max retry, dead letter queue가 필요하다.

### 2. 대상 endpoint는 입력값이다

사용자나 설정 화면이 webhook destination을 정하면, 그 URL 자체가 위험하다.

- internal 주소를 넣을 수 있다
- 비정상 redirect가 섞일 수 있다
- 잘못된 프로토콜을 넣을 수 있다

즉 sender는 outbound SSRF 방어와 비슷한 검증을 가져야 한다.

### 3. signed delivery가 중요하다

받는 쪽이 우리를 신뢰하려면:

- event id
- timestamp
- signature
- delivery id

가 필요하다. sender는 이 값들을 일관되게 생성해야 한다.

### 4. ordering과 dedup은 sender 책임이기도 하다

event가 순서 민감하면 sender가 더 신경 써야 한다.

- 어떤 이벤트는 순서대로 보내야 한다
- 어떤 이벤트는 최신 상태만 중요하다
- duplicate delivery가 발생해도 receiver가 감당 가능해야 한다

### 5. secret rotation이 쉬워야 한다

sender secret이 길게 유지되면 전체 outbound가 위험해진다.

- versioned secret을 둔다
- old/new를 짧게 중복 허용한다
- endpoint별로 서명 버전을 기록한다

---

## 실전 시나리오

### 시나리오 1: 실패한 webhook을 무한 재시도함

대응:

- max retry를 둔다
- backoff를 적용한다
- 일정 횟수 후 DLQ로 보낸다

### 시나리오 2: 사용자 설정에 악성 destination이 들어감

대응:

- scheme과 host allowlist를 검사한다
- private IP와 localhost를 차단한다
- redirect chain을 다시 검증한다

### 시나리오 3: outbound 서명 secret이 오래 유지됨

대응:

- secret version을 관리한다
- 회전 중 dual signing/dual verify 기간을 둔다
- 실패한 delivery를 다시 보내기 전에 version을 확인한다

---

## 코드로 보기

### 1. sender retry 개념

```java
public void deliver(WebhookMessage message) {
    for (int attempt = 1; attempt <= 5; attempt++) {
        try {
            httpClient.post(message.targetUrl(), sign(message)).send();
            return;
        } catch (Exception ex) {
            sleep(backoff(attempt));
        }
    }
    deadLetterQueue.publish(message);
}
```

### 2. 대상 검증 개념

```java
public void validateTarget(URI uri) {
    if (!Set.of("https").contains(uri.getScheme())) {
        throw new IllegalArgumentException("invalid webhook target");
    }
    if (isPrivateAddress(resolve(uri.getHost()))) {
        throw new SecurityException("blocked webhook destination");
    }
}
```

### 3. delivery metadata

```text
1. delivery_id를 발급한다
2. timestamp와 signature를 붙인다
3. retries는 동일 delivery_id를 유지한다
4. receiver가 dedup할 수 있게 한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| fire-and-forget | 단순하다 | 실패 추적이 어렵다 | 낮은 중요도 알림 |
| retry with backoff | 안정적이다 | 중복 전송이 생긴다 | 일반 webhook |
| DLQ + alert | 운영이 강하다 | 처리 체계가 필요하다 | 중요한 integration |
| per-target signing | 보안이 좋다 | secret 관리가 늘어난다 | 파트너 연동 |

판단 기준은 이렇다.

- delivery 실패를 어디까지 자동 재시도할 것인가
- 대상 URL을 누가 설정하는가
- duplicate delivery를 수용할 수 있는가
- secret versioning과 rotation을 할 수 있는가

---

## 꼬리질문

> Q: webhook sender도 왜 hardening이 필요한가요?
> 의도: outbound도 공격면이라는 점을 아는지 확인
> 핵심: 잘못된 대상 전송과 retry storm이 위험하기 때문이다.

> Q: dead letter queue가 왜 필요한가요?
> 의도: 무한 재시도와 운영 안정성을 이해하는지 확인
> 핵심: 실패한 delivery를 분리해 운영자가 다룰 수 있게 하기 위해서다.

> Q: 대상 URL 검증이 왜 중요한가요?
> 의도: outbound SSRF 경계를 아는지 확인
> 핵심: 내부 주소나 악성 프로토콜로 보내는 사고를 막기 위해서다.

> Q: delivery_id와 signature는 왜 함께 써야 하나요?
> 의도: 재전송과 위조 방어를 구분하는지 확인
> 핵심: 하나는 중복 추적, 다른 하나는 무결성 보장이다.

## 한 줄 정리

webhook sender hardening은 외부 시스템에 메시지를 보낼 때도 대상 검증, 재시도, 서명, 비밀 관리까지 포함해야 한다는 뜻이다.
