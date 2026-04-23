# Payment System Ledger, Idempotency, Reconciliation

> 한 줄 요약: 결제 시스템은 외부 PG 상태와 내부 원장을 동시에 맞춰야 하므로, auth/capture/refund 흐름, 멱등성, 원장, 재조정(reconciliation)을 한 덩어리로 설계해야 한다.

retrieval-anchor-keywords: payment auth capture refund, ledger, transaction log, reconciliation, idempotency key, duplicate charge, partial refund, settlement, PG callback, chargeback, provider timeout recovery, replay-safe retry, reconciliation window, correction cutoff

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md)
> - [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
> - [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
> - [트랜잭션 실전 시나리오](../database/transaction-case-studies.md)
> - [Outbox, Saga, Eventual Consistency](../software-engineering/outbox-inbox-domain-events.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](../security/service-to-service-auth-mtls-jwt-spiffe.md)
> - [Retry, Circuit Breaker, Bulkhead](../spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)
> - [Redo Log, Undo Log, Checkpoint, Crash Recovery](../database/redo-log-undo-log-checkpoint-crash-recovery.md)
> - [Reconciliation Window / Cutoff Control 설계](./reconciliation-window-cutoff-control-design.md)

## 핵심 개념

결제 시스템은 단순히 `POST /payments`를 성공시키는 문제가 아니다.
실전에서는 최소 네 가지를 동시에 맞춰야 한다.

- **외부 PG 상태**: 승인(auth), 매입(capture), 환불(refund), 취소(cancel)
- **내부 원장(ledger)**: 어떤 금액이 언제, 왜, 어떤 상태로 움직였는지의 회계적 기록
- **요청 멱등성(idempotency)**: 같은 요청이 재시도되어도 한 번만 반영되는 성질
- **정합성 재조정(reconciliation)**: 내부 기록과 PG/정산 결과가 어긋났을 때 다시 맞추는 작업

여기서 가장 많이 헷갈리는 개념이 `ledger`와 `transaction log`다.

- **ledger**는 비즈니스 관점의 장부다. "승인됨", "매입됨", "환불됨", "수수료 발생" 같은 의미가 남는다.
- **transaction log**는 시스템 관점의 작업 흔적이다. DB에 무엇이 쓰였고, 어떤 순서로 커밋됐는지를 남긴다.

둘은 비슷해 보이지만 목적이 다르다.

- ledger는 회계/정산/감사에 맞춘다
- transaction log는 장애 복구/재시작/재처리에 맞춘다

따라서 결제 시스템을 설계할 때는 "DB에 저장만 되면 끝"이 아니라, "나중에 재처리해도 다시 같은 결과가 나오는가"까지 봐야 한다.

## 깊이 들어가기

### 1. auth, capture, refund는 같은 결제가 아니다

결제를 하나의 버튼으로 보지만, 실제로는 단계가 다르다.

- **auth**: 카드 한도나 결제 가능 여부를 확인하고 금액을 묶어 두는 단계
- **capture**: 실제 매입을 확정하는 단계
- **refund**: 이미 확정된 금액을 되돌리는 단계

이 셋을 한 문장으로 합치면 쉽게 설계가 망가진다.

- auth 성공 후 capture 실패
- capture 성공 후 환불 필요
- 부분 환불만 허용되는 상품
- 승인과 매입 사이에 주문 취소가 들어오는 경우

즉 결제 상태는 보통 다음처럼 더 세밀해야 한다.

```text
CREATED -> AUTHORIZED -> CAPTURED -> PARTIALLY_REFUNDED -> REFUNDED
                 \-> AUTH_FAILED
                 \-> CANCELED
```

### 2. 내부 원장은 PG 응답과 별개로 남아야 한다

외부 PG 응답만 믿으면 나중에 추적이 어렵다.

원장에는 최소한 다음이 있어야 한다.

- payment_id
- order_id
- action (`AUTH`, `CAPTURE`, `REFUND`, `CANCEL`)
- amount
- currency
- provider
- provider_transaction_id
- idempotency_key
- status
- occurred_at
- reversed_entry_id 또는 reference_id

이렇게 해야 다음 질문에 답할 수 있다.

- "이 결제는 언제 승인됐나?"
- "부분 환불은 몇 번 있었나?"
- "환불이 실패했는데 내부에서는 성공으로 기록됐나?"
- "어떤 재시도 요청이 같은 결제를 두 번 만들었나?"

### 3. transaction log는 복구용, ledger는 설명용

둘의 차이는 장애 때 선명해진다.

- transaction log는 "무엇이 커밋됐는가"를 복구한다
- ledger는 "무슨 돈이 왜 움직였는가"를 설명한다

예를 들어 PG 콜백이 왔는데 우리 서버가 응답 직후 죽었다고 하자.

- transaction log 관점: DB에는 commit이 남았는지, 아니면 중간에 죽었는지 확인해야 한다
- ledger 관점: 승인 기록이 이미 생성됐는지, 승인 이후 캡처로 넘어갔는지 봐야 한다

이 차이를 모르면 "DB에 들어갔으니 끝"이라고 착각하고, 정산 단계에서 크게 틀어진다.

### 4. reconciliation은 예외처리가 아니라 운영 루프다

reconciliation은 가끔 하는 보정 작업이 아니라, 결제 시스템의 상시 운영 루프다.

대표적인 불일치:

- 우리 DB는 `CAPTURED`인데 PG는 `AUTHORIZED`에 멈춤
- 우리 DB는 `REFUNDED`인데 PG에는 부분 환불만 반영됨
- settlement 금액과 우리 원장 합계가 안 맞음
- 콜백 유실로 외부 상태만 바뀌고 내부 상태가 남음

보통은 다음 순서로 재조정한다.

1. provider의 정산/거래 조회 API를 기준으로 truth를 가져온다
2. 우리 원장과 비교한다
3. 차이를 발견하면 보정 이벤트를 만든다
4. 보정도 ledger에 남긴다

즉 reconciliation은 "원장 수정"이 아니라 **정정 원장 추가**에 가깝다.
또한 어떤 시점의 숫자를 확정할지, late arrival를 언제 correction으로 넘길지는 reconciliation window 정책으로 별도 관리하는 편이 안전하다.

### 5. 멱등성은 결제 시스템의 생명선이다

결제는 재시도가 매우 흔하다.

- 네트워크 timeout
- 서버 응답 지연
- PG callback 중복
- 사용자의 새로고침

이때 같은 요청이 두 번 들어와도 한 번만 처리되어야 한다.

멱등성 키 설계 예:

```text
POST /payments/auth
Idempotency-Key: 8f7d2f6c-3d0b-4d8b-9b85-5ef0d7a0d9ae
```

동작 규칙:

1. 같은 key + 같은 request hash면 이전 결과를 반환한다
2. 같은 key + 다른 payload면 거부한다
3. 처리 중이면 `PROCESSING`을 반환하거나 잠시 대기시킨다
4. 성공 결과는 response cache처럼 재사용한다

이 문맥은 [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)와 반드시 같이 봐야 한다.

### 6. PG 호출은 언제든 깨질 수 있다

결제 시스템에서 가장 위험한 순간은 "PG는 성공했는데 우리 서버가 못 받는 경우"다.

예:

1. 우리 서버가 `auth` 요청을 PG로 보낸다
2. PG는 승인한다
3. 응답이 오기 전에 우리 서버가 timeout 또는 crash
4. 클라이언트는 실패로 보고 재시도
5. 우리 서버는 다시 결제를 시도

이 시나리오를 막으려면:

- idempotency key를 저장한다
- provider transaction id를 기록한다
- auth/capture/refund 각각의 상태 전이를 분리한다
- 외부 호출 이후에는 반드시 조회 재확인을 할 수 있어야 한다

### 7. auth/capture/refund는 API를 분리하는 편이 안전하다

한 API로 뭉치면 운영이 어려워진다.

권장 예시:

- `POST /payments/auth`
- `POST /payments/{paymentId}/capture`
- `POST /payments/{paymentId}/refund`
- `GET /payments/{paymentId}`
- `GET /payments/{paymentId}/ledger`
- `GET /payments/reconciliation-runs/{runId}`

이렇게 나누면

- auth 재시도
- capture 지연
- refund 부분 처리
- reconciliation 확인

을 각각 추적할 수 있다.

## 실전 시나리오

### 시나리오 1. auth 성공 후 응답 유실

문제:

- PG는 승인했지만 서버는 timeout을 받았다
- 사용자는 다시 눌렀다

위험:

- 동일한 결제가 두 번 승인될 수 있다

해결:

- auth 요청에 idempotency key를 넣는다
- 같은 key면 이전 상태를 조회한다
- provider transaction id를 기준으로 재조회한다

### 시나리오 2. capture는 성공했는데 내부 저장이 실패

문제:

- PG 매입은 성공
- 우리 DB 저장은 실패

위험:

- 돈은 나갔는데 우리 시스템에는 미반영

해결:

- PG 결과를 원장에 먼저 기록하는 것이 아니라, 저장/외부 호출/상태 갱신의 경계를 설계한다
- outbox나 재처리 큐로 보정한다
- reconciliation job이 PG 상태를 재조회한다

### 시나리오 3. 부분 환불이 여러 번 일어남

문제:

- 주문 전체가 아니라 일부만 환불된다
- 여러 차례 나눠서 환불된다

위험:

- 합계 계산이 틀어진다
- 원장 잔액과 PG 금액이 어긋난다

해결:

- refund entry를 누적 기록한다
- original payment와 refund의 reference 관계를 남긴다
- 부분 환불 가능 금액을 DB에서 계산한다

### 시나리오 4. 정산일에 금액이 안 맞음

문제:

- 내부 원장은 정상처럼 보인다
- 정산 파일과 합계가 맞지 않는다

위험:

- 미수금, 과다 정산, 회계 오류

해결:

- reconciliation batch를 돌린다
- settlement report와 원장을 대사한다
- 보정 분개를 남긴다

### 시나리오 5. 환불 API가 중복 호출됨

문제:

- 사용자가 환불 버튼을 두 번 누른다
- 운영자가 재시도한다

위험:

- 환불이 두 번 나가면 재무 사고다

해결:

- refund도 auth와 동일한 멱등성 키를 쓴다
- 상태 전이로 중복 환불을 막는다

## 코드로 보기

### 1. 상태 전이와 원장 기록

```java
public class PaymentService {

    private final PaymentRepository paymentRepository;
    private final PaymentLedgerRepository ledgerRepository;
    private final IdempotencyStore idempotencyStore;

    public PaymentResult auth(AuthRequest request) {
        IdempotencyRecord record = idempotencyStore.findOrCreate(
            request.idempotencyKey(),
            request.payloadHash()
        );

        if (record.isCompleted()) {
            return record.toResult();
        }

        Payment payment = paymentRepository.createAuthorized(
            request.orderId(),
            request.amount(),
            request.provider(),
            request.providerTransactionId()
        );

        ledgerRepository.append(PaymentLedgerEntry.auth(payment.getId(), request.amount()));
        idempotencyStore.markCompleted(request.idempotencyKey(), PaymentResult.of(payment));

        return PaymentResult.of(payment);
    }

    public PaymentResult capture(CaptureRequest request) {
        Payment payment = paymentRepository.findById(request.paymentId());
        payment.capture(request.amount());

        ledgerRepository.append(PaymentLedgerEntry.capture(payment.getId(), request.amount()));
        paymentRepository.save(payment);
        return PaymentResult.of(payment);
    }
}
```

핵심은 외부 호출 결과를 단순히 덮어쓰는 것이 아니라, **멱등성 기록 + 원장 기록 + 상태 전이**를 같이 남기는 것이다.

### 2. 원장 테이블 예시

```sql
CREATE TABLE payment_ledger_entries (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    payment_id BIGINT NOT NULL,
    entry_type VARCHAR(30) NOT NULL,
    amount DECIMAL(19,2) NOT NULL,
    currency CHAR(3) NOT NULL,
    provider VARCHAR(50) NULL,
    provider_transaction_id VARCHAR(100) NULL,
    idempotency_key VARCHAR(100) NULL,
    reference_entry_id BIGINT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_payment_id_created_at (payment_id, created_at)
);
```

이 테이블은 잔액과 상태를 설명하는 장부 역할을 한다.

### 3. reconciliation job 예시

```java
@Scheduled(cron = "0 0 * * * *")
public void reconcile() {
    List<Payment> candidates = paymentRepository.findNeedsReconciliation();

    for (Payment payment : candidates) {
        ProviderPaymentInfo info = providerClient.lookup(payment.getProviderTransactionId());

        if (!payment.matches(info)) {
            paymentRepository.applyReconciliation(payment.getId(), info);
            ledgerRepository.append(PaymentLedgerEntry.reconcile(payment.getId(), info));
        }
    }
}
```

여기서 중요한 것은 reconciliation 결과를 "수정"만 하지 말고, **보정 entry로 남겨야 한다**는 점이다.

### 4. API 예시

```bash
curl -X POST /payments/auth \
  -H 'Idempotency-Key: 8f7d2f6c-3d0b-4d8b-9b85-5ef0d7a0d9ae' \
  -H 'Content-Type: application/json' \
  -d '{
    "orderId": 1001,
    "amount": 15000,
    "currency": "KRW",
    "provider": "toss",
    "cardToken": "tok_abc"
  }'
```

```bash
curl -X POST /payments/123/capture \
  -H 'Idempotency-Key: 2e5c4b6f-8ed1-4a03-bf5b-7e45f6e7e3df' \
  -H 'Content-Type: application/json' \
  -d '{
    "amount": 15000
  }'
```

```bash
curl -X POST /payments/123/refund \
  -H 'Idempotency-Key: 5ef0e9f0-9c0f-4c4e-9f8e-0e7cb8af9cc9' \
  -H 'Content-Type: application/json' \
  -d '{
    "amount": 5000,
    "reason": "customer_cancel"
  }'
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| auth/capture/refund API 분리 | 상태 전이가 명확하다 | 엔드포인트가 늘어난다 | PG 연동과 정산을 분리해서 추적해야 할 때 |
| 하나의 `POST /payments` API | 사용이 단순하다 | 상태 복잡도가 숨겨진다 | 정말 단순한 결제만 있을 때 |
| ledger를 별도 테이블로 둠 | 감사/정산/복구가 쉽다 | 저장이 늘고 설계가 무거워진다 | 금전 사고가 중요한 서비스 |
| transaction log만 믿음 | 구현이 쉽다 | 비즈니스 의미가 부족하다 | 감사/정산이 거의 필요 없는 경우 |
| reconciliation을 배치로 둠 | 운영이 안정적이다 | 지연이 생긴다 | 정산 파일/PG 조회가 주기적으로 가능할 때 |
| 실시간 reconciliation | 불일치 탐지가 빠르다 | 외부 호출 비용이 크다 | 고가 결제, 강한 정합성이 필요한 경우 |
| idempotency key만 사용 | 중복 방지가 쉽다 | 상태 분기와 보상은 약하다 | 단순 생성 API |
| idempotency + ledger + reconciliation | 가장 안전하다 | 가장 복잡하다 | 결제, 환불, 정산 시스템 |

핵심 판단 기준은 이렇다.

- 사용자가 돈을 내는 순간인가
- PG와 우리 DB가 분리되는가
- 나중에 감사/정산/소명 자료가 필요한가
- 재시도와 중복 호출이 빈번한가

하나라도 그렇다면 ledger와 reconciliation을 설계에 넣는 편이 맞다.

## 꼬리질문

> Q: auth와 capture를 굳이 분리해야 하나요?  
> 의도: 결제 단계의 의미 차이를 이해하는지 확인  
> 핵심: 분리하면 승인 보류와 실제 매입을 나눌 수 있고, 취소/환불 정책이 명확해진다.

> Q: ledger와 transaction log는 어떻게 다르죠?  
> 의도: 저장 로그와 비즈니스 장부를 혼동하는지 확인  
> 핵심: transaction log는 복구용, ledger는 정산/감사용이다.

> Q: reconciliation은 왜 필요한가요?  
> 의도: 외부 PG와 내부 DB가 항상 일치하지 않는다는 현실 이해 여부 확인  
> 핵심: 콜백 유실, 재시도, 부분 환불, 정산 차이가 반드시 생기기 때문이다.

> Q: 멱등성 키만 있으면 중복 결제는 다 막히나요?  
> 의도: 멱등성의 한계를 이해하는지 확인  
> 핵심: 요청 중복은 막아도, 외부 PG 상태와 내부 상태가 어긋나는 문제는 reconciliation이 필요하다.

> Q: 환불이 부분 환불일 때 원장은 어떻게 설계하나요?  
> 의도: 이벤트 누적과 잔액 계산을 이해하는지 확인  
> 핵심: refund entry를 누적하고, reference 관계를 남기며, 남은 가능 금액을 계산해야 한다.

## 한 줄 정리

결제 시스템은 "돈이 오갔다"는 사실을 한 번만 처리하는 문제가 아니라, 외부 PG 상태와 내부 원장을 멱등하게 맞추고, 어긋난 부분을 재조정까지 할 수 있게 설계하는 문제다.
