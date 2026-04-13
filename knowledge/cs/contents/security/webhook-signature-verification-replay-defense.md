# Webhook Signature Verification / Replay Defense

> 한 줄 요약: webhook은 inbound callback이므로 transport만 믿지 말고, raw body 기준 서명 검증과 idempotent 처리로 재전송까지 막아야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md)
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [API Gateway, Reverse Proxy 운영 포인트](../network/api-gateway-reverse-proxy-operational-points.md)

retrieval-anchor-keywords: webhook signature, raw body, event id, idempotency, replay defense, provider secret, HMAC, timestamp window, delivery retry, constant-time compare

---

## 핵심 개념

webhook은 다른 시스템이 우리 서버로 보내는 서버-투-서버 알림이다.  
이때 중요한 건 "누가 보냈는가"와 "내용이 바뀌지 않았는가"다.

- `signature verification`: provider가 가진 secret 또는 private key로 진짜 메시지인지 확인
- `raw body`: 파싱 전 원본 바이트
- `event id`: 같은 이벤트가 중복 전달됐는지 판별하는 식별자
- `idempotency`: 같은 알림이 여러 번 와도 결과가 한 번만 반영되게 하는 성질
- `replay defense`: 예전 webhook을 다시 보내는 공격을 막는 것

많은 구현이 실패하는 이유는 webhook을 "그냥 POST 요청"처럼 다루기 때문이다.  
그러면 다음을 놓치기 쉽다.

- provider는 retry를 여러 번 보낸다
- 네트워크는 중복 전달할 수 있다
- body parser가 원문을 바꿀 수 있다
- signature만 맞아도 같은 이벤트를 여러 번 처리할 수 있다

즉 webhook 보안은 인증보다 더 넓게, 수신 검증과 중복 처리까지 포함해야 한다.

---

## 깊이 들어가기

### 1. webhook은 왜 특별한가

일반 API는 우리 클라이언트가 호출한다.  
webhook은 외부 provider가 우리에게 호출한다.

그래서 신뢰 모델이 다르다.

- 우리 쪽이 요청을 시작하지 않는다
- provider가 재시도 정책을 가진다
- 같은 이벤트를 여러 번 보낼 수 있다
- 우리 서버는 실패 응답에 따라 retry storm을 맞을 수 있다

이 때문에 webhook handler는 "받자마자 DB 변경"이 아니라 "검증 후 비동기 처리"가 좋다.

### 2. raw body가 중요한 이유

signature는 보통 exact bytes에 대해 계산된다.

- JSON 파싱 후 다시 직렬화하면 공백과 key order가 바뀔 수 있다
- UTF-8 정규화나 escaping이 달라질 수 있다
- 프레임워크가 body를 한 번 읽으면 원문을 잃을 수 있다

따라서 검증은 항상 raw body로 해야 한다.

### 3. event id와 idempotency

provider가 "같은 이벤트"를 여러 번 보내는 일은 정상이다.

- timeout이 나면 다시 보낸다
- 500 응답이 나면 다시 보낸다
- 네트워크 단절 후 다시 시도한다

그래서 handler는 중복을 전제로 해야 한다.

- `event_id`를 저장한다
- 이미 처리한 이벤트면 200을 준다
- side effect는 딱 한 번만 적용한다

여기서 중요한 건 "중복 이벤트가 잘못"이 아니라는 점이다.  
중복 이벤트를 잘 처리하지 못하는 쪽이 문제다.

### 4. timestamp window와 replay

signature가 맞아도 예전 메시지를 그대로 재전송할 수 있다.

그래서 provider가 timestamp를 함께 보내는 경우가 많다.

- 현재 시각과 너무 차이가 나면 거부한다
- 허용 창은 짧게 둔다
- clock skew를 고려한다

timestamp만 믿는 건 부족하고, event id dedup과 같이 써야 한다.

### 5. secret rotation

webhook secret은 유출되면 바로 재사용될 수 있다.

- secret을 DB와 로그에 남기지 않는다
- 새 secret을 배포한 뒤 old/new를 잠깐 중복 허용한다
- provider와 receiver의 전환 시점을 맞춘다

회전 시에는 "어느 버전의 secret으로 서명됐는지"를 구분할 수 있으면 좋다.

---

## 실전 시나리오

### 시나리오 1: body를 파싱한 뒤 검증해서 서명이 항상 실패함

문제:

- framework가 JSON body를 객체로 바꿨다
- 다시 문자열화한 값으로 signature를 비교했다

대응:

- raw bytes를 먼저 저장한다
- 그 바이트로 signature를 검증한다
- 검증이 끝난 뒤에만 JSON parse를 한다

### 시나리오 2: 같은 결제 webhook이 여러 번 들어옴

문제:

- 결제 완료 이벤트가 중복 전달된다
- handler가 매번 포인트 적립과 주문 상태 변경을 수행한다

대응:

- `event_id`를 unique key로 저장한다
- 이미 처리된 이벤트는 no-op으로 처리한다
- side effect를 큐나 outbox로 한번만 흘린다

### 시나리오 3: webhook secret이 유출됨

문제:

- 테스트 로그에 secret이 남았다
- 공격자가 임의 webhook을 우리 서비스로 보낸다

대응:

- secret을 즉시 rotate 한다
- 이전 secret은 짧게만 허용한다
- webhook source와 payload를 감사 로그에 남긴다

---

## 코드로 보기

### 1. raw body 검증 흐름

```java
public ResponseEntity<Void> handleWebhook(
        @RequestHeader("X-Webhook-Signature") String signature,
        @RequestHeader("X-Webhook-Timestamp") long timestamp,
        @RequestHeader("X-Webhook-Event-Id") String eventId,
        @RequestBody byte[] rawBody) {

    webhookVerifier.verify(signature, timestamp, rawBody);

    if (processedEventRepository.existsByEventId(eventId)) {
        return ResponseEntity.ok().build();
    }

    WebhookEvent event = objectMapper.readValue(rawBody, WebhookEvent.class);
    webhookProcessor.process(event);
    processedEventRepository.save(new ProcessedEvent(eventId));

    return ResponseEntity.ok().build();
}
```

### 2. HMAC 검증 개념

```java
public void verify(String signature, long timestamp, byte[] rawBody) {
    if (Math.abs(Instant.now().getEpochSecond() - timestamp) > 300) {
        throw new SecurityException("webhook timestamp expired");
    }

    String expected = sign(rawBody, timestamp);
    if (!MessageDigest.isEqual(
            expected.getBytes(StandardCharsets.UTF_8),
            signature.getBytes(StandardCharsets.UTF_8))) {
        throw new SecurityException("invalid webhook signature");
    }
}
```

### 3. 비동기 처리 패턴

```text
1. 수신 즉시 signature와 timestamp를 검증한다
2. event_id 중복 여부를 확인한다
3. 큐에 넣는다
4. worker가 side effect를 적용한다
5. 실패 시에도 동일 event_id는 다시 처리하지 않도록 기록한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| HMAC + shared secret | 구현이 단순하다 | secret 유출 시 위험하다 | 대부분의 webhook |
| public-key signature | sender secret 보관 부담이 적다 | 검증과 키 관리가 더 복잡하다 | 고신뢰 파트너 연동 |
| IP allowlist only | 운영이 쉬워 보인다 | IP 변동, 프록시, 위조에 약하다 | 보조 신호로만 |
| sync processing | 단순하다 | retry와 timeout에 취약하다 | 아주 가벼운 알림 |
| async + idempotency | 안정적이다 | 구현이 더 복잡하다 | 결제, 주문, 정산 |

판단 기준은 이렇다.

- 같은 이벤트가 여러 번 올 수 있는가
- side effect가 되돌리기 어려운가
- provider secret이 안전하게 관리되는가
- 검증 전에 아무 DB 변경도 하지 않을 수 있는가

---

## 꼬리질문

> Q: webhook을 왜 raw body로 검증해야 하나요?
> 의도: 파싱과 서명 검증의 순서를 이해하는지 확인
> 핵심: 파싱하면 원문 바이트가 달라질 수 있기 때문이다.

> Q: event id가 있는데도 signature 검증이 필요한가요?
> 의도: 인증과 중복 방지의 역할을 분리하는지 확인
> 핵심: event id는 중복 확인용이고, signature는 위조 방지용이다.

> Q: IP allowlist만으로 webhook을 믿을 수 있나요?
> 의도: 네트워크 신뢰와 메시지 신뢰를 구분하는지 확인
> 핵심: 아니다. IP는 보조 신호일 뿐이고 서명 검증이 핵심이다.

> Q: provider가 retry할 때 우리 시스템은 어떻게 해야 하나요?
> 의도: idempotency와 재시도 설계 이해 확인
> 핵심: 같은 event_id는 한 번만 side effect를 적용해야 한다.

## 한 줄 정리

webhook은 "외부가 보내는 내부 이벤트"가 아니라 "외부가 보낸 요청을 우리가 증명하고 중복 없이 반영해야 하는 입력"이다.
