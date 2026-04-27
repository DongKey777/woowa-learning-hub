# Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only

> 한 줄 요약: 초급자는 전파 옵션을 "새 트랜잭션 기술"로 외우기보다, "같이 망하게 둘지, 따로 남길지, 이미 실패 예정인지"를 서비스 메서드 이야기로 먼저 잡는 편이 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Spring Mini Card: rollback-only 실패 vs checked exception인데 commit된 것처럼 보이는 놀람](./spring-rollbackonly-vs-checked-exception-commit-surprise-card.md)
- [Mini Debugging Card for `UnexpectedRollbackException`](./spring-unexpectedrollbackexception-mini-debugging-card.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](./spring-service-layer-external-io-after-commit-outbox-primer.md)
- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
- [Spring Mini Card: `JpaTransactionManager`에서 `NESTED` 기대가 자주 깨지는 이유](./spring-jpatransactionmanager-savepoint-expectations-mini-card.md)
- [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](./spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)
- [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md)
- [spring 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: required requires_new primer, propagation beginner, rollback-only beginner, transactional propagation 입문, required vs requires_new 차이, nested vs requires_new beginner, savepoint beginner bridge, 왜 unexpectedrollbackexception 나요, transaction marked rollback-only beginner, audit log requires new, 주문 저장 감사 로그 분리, 같은 트랜잭션 참여, 독립 트랜잭션, partial commit beginner, catch 했는데 마지막에 터짐

## 먼저 mental model 한 줄

전파(propagation)는 "안쪽 메서드를 부를 때 트랜잭션을 **합칠지**, **새로 딸지**, 아니면 **이미 실패 예정 상태를 그대로 이어받을지**"를 정하는 규칙이다.

초급자는 용어보다 아래 세 문장부터 잡으면 된다.

- `REQUIRED`: 지금 트랜잭션이 있으면 같이 탄다.
- `REQUIRES_NEW`: 바깥 것을 잠깐 멈추고 새 트랜잭션을 하나 더 연다.
- rollback-only: 지금 트랜잭션은 이미 커밋 불가라고 표시된 상태다.

`catch 했는데 마지막에 터짐` 패턴을 먼저 짧게 분리하고 싶다면 [Mini Debugging Card for `UnexpectedRollbackException`](./spring-unexpectedrollbackexception-mini-debugging-card.md)를 먼저 보고 돌아와도 된다.

## 30초 비교표

| 항목 | `REQUIRED` | `REQUIRES_NEW` | rollback-only |
|---|---|---|---|
| 초급자용 감각 | 한 배를 같이 탄다 | 작은 보조 배를 따로 띄운다 | 배 바닥에 이미 "이 배는 항구에 못 들어감" 표시가 붙었다 |
| 바깥 tx가 있으면 | 합류한다 | 잠깐 멈추고 새 tx를 연다 | 그 상태를 그대로 공유할 수 있다 |
| 안쪽 실패가 바깥에 주는 영향 | 보통 전체에 영향 | 분리 가능 | 마지막 커밋 때 실패로 드러날 수 있다 |
| 대표 용도 | 주문 저장, 재고 차감처럼 같이 성공/실패할 작업 | 감사 로그, 별도 기록 | 예외를 catch 했는데도 마지막에 실패하는 현상 이해 |

핵심은 옵션 이름이 아니라, **무엇을 같이 성공시키고 무엇을 따로 남길지**다.

## 가장 먼저 보는 서비스 레이어 이야기 3개

### 이야기 1. 주문 저장과 재고 차감은 같이 망해야 한다 -> `REQUIRED`

주문을 저장했는데 재고 차감이 실패하면, 초급자 감각으로도 "둘 다 취소"가 자연스럽다.

```java
@Service
public class CheckoutService {

    @Transactional
    public void checkout() {
        orderService.createOrder();      // REQUIRED
        inventoryService.decreaseStock(); // REQUIRED
    }
}
```

이때 안쪽 서비스들이 기본 전파(`REQUIRED`)면 보통 바깥 트랜잭션에 같이 참여한다.

```text
checkout tx 시작
  -> 주문 저장
  -> 재고 차감 실패
checkout 전체 rollback
```

초급자 기준 한 줄:

- 같이 성공하거나 같이 실패해야 하면 먼저 `REQUIRED` 쪽이 기본값이다.

### 이야기 2. 주문은 실패해도 감사 로그는 남기고 싶다 -> `REQUIRES_NEW`

이번에는 주문 저장은 실패했지만, "실패했다"는 감사 로그는 꼭 남기고 싶다고 해 보자.

```java
@Service
public class AuditService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void writeFailureLog(String message) {
        auditRepository.save(new AuditLog(message));
    }
}
```

```java
@Service
public class CheckoutService {

    @Transactional
    public void checkout() {
        try {
            orderService.createOrder();
            inventoryService.decreaseStock();
        } catch (RuntimeException ex) {
            auditService.writeFailureLog("checkout failed");
            throw ex;
        }
    }
}
```

흐름은 이렇게 읽으면 된다.

```text
바깥 checkout tx 시작
  -> 주문/재고 작업 실패
  -> 바깥 tx는 실패 방향
  -> audit는 REQUIRES_NEW로 새 tx 시작
  -> audit commit
바깥 checkout rollback
```

초급자 기준 한 줄:

- 본 작업과 운명을 분리해서 "이 기록만은 남기고 싶다"면 `REQUIRES_NEW`를 검토한다.

주의도 같이 기억해야 한다.

## 가장 먼저 보는 서비스 레이어 이야기 3개 (계속 2)

- `REQUIRES_NEW`는 "새 커밋"이면서 보통 "새 트랜잭션 자원"도 뜻한다.
- 그래서 남발하면 흐름 추적이 어려워지고 커넥션 풀 부담도 생긴다.

### 이야기 3. 예외를 catch 했는데 왜 마지막에 또 터지지? -> rollback-only

초급자가 가장 당황하는 장면이다.

```java
@Service
public class CheckoutService {

    @Transactional
    public void checkout() {
        try {
            paymentService.charge(); // 같은 tx에 REQUIRED로 참여
        } catch (Exception ex) {
            log.warn("결제 실패는 일단 무시", ex);
        }

        orderRepository.save(new Order());
    }
}
```

겉으로는 "예외를 처리했으니 계속 가도 되겠지"처럼 보인다.

하지만 `paymentService.charge()`가 같은 트랜잭션 안에서 실패하면서 rollback-only를 찍었다면 의미가 달라진다.

```text
checkout tx 시작
  -> payment 실패
  -> 현재 tx가 rollback-only 표시됨
  -> 예외는 catch 해서 화면에서 사라짐
  -> 바깥은 계속 진행
  -> 마지막 commit 시도
  -> "이미 rollback-only라 커밋 불가" 예외 발생
```

초급자 기준 한 줄:

- catch는 예외 전달을 숨길 수 있어도, rollback-only가 찍힌 트랜잭션을 정상으로 되돌리지는 못한다.

## 세 가지를 한 장으로 연결하기

| 질문 | 먼저 떠올릴 답 |
|---|---|
| "안쪽 실패가 바깥도 같이 실패하게 해야 하나?" | `REQUIRED` 쪽부터 본다 |
| "이 작업만 따로 커밋해서 남겨야 하나?" | `REQUIRES_NEW`를 검토한다 |
| "분명 catch 했는데 마지막에 왜 실패하지?" | rollback-only 가능성을 먼저 본다 |

## 여기서 `NESTED`는 어떻게 다르게 봐야 하나

초급자는 `NESTED`를 "`REQUIRES_NEW`의 약한 버전"으로 외우면 거의 항상 헷갈린다.
둘 다 "안쪽 작업을 분리해 보인다"는 공통점은 있지만, 분리 방식이 다르다.

- `NESTED`: 같은 큰 트랜잭션 안에 savepoint를 찍고, 안쪽 일부만 되감는다.
- `REQUIRES_NEW`: 안쪽 작업을 아예 별도 트랜잭션으로 떼서 따로 커밋하거나 롤백한다.

짧게 비유하면:

- `NESTED`는 같은 문서에서 "여기까지 되돌리기" 체크포인트를 찍는 느낌이다.
- `REQUIRES_NEW`는 새 문서를 하나 더 열어 따로 저장하는 느낌이다.

### 초급자용 20초 비교

| 질문 | `NESTED` | `REQUIRES_NEW` |
|---|---|---|
| 안쪽 작업은 바깥과 같은 큰 일인가? | 보통 그렇다 | 꼭 그렇지 않다 |
| 안쪽 성공을 바깥 실패와 분리해 남길 수 있나? | 아니다 | 가능하다 |
| 안쪽 실패 후 바깥 흐름을 계속 갈 수 있나? | savepoint 기준으로는 가능하다 | 가능하다 |
| 마지막에 바깥이 전체 롤백되면? | 안쪽도 함께 사라진다 | 안쪽에서 이미 커밋한 것은 남을 수 있다 |

핵심 한 줄:

- `NESTED`는 **부분 되돌리기**에 가깝다.
- `REQUIRES_NEW`는 **별도 결과 남기기**에 가깝다.

### savepoint 한계도 초급자 감각으로만 먼저 기억하자

`NESTED`를 이해할 때 초급자가 꼭 먼저 기억할 한계는 복잡한 플랫폼 차이보다 이것이다.

- savepoint는 "같은 트랜잭션 안에서 잠깐 되감기"다.
- 그래서 바깥 트랜잭션이 최종 실패하면 안쪽에서 했던 일도 같이 사라진다.
- 즉 "안쪽 작업만 영구적으로 남기고 싶다"는 요구에는 `NESTED`가 아니라 `REQUIRES_NEW` 쪽 감각이 맞다.

예를 들면:

- 배치 100건 중 1건 실패를 되감고 99건 흐름은 계속 보고 싶다 -> `NESTED` 감각
- 주문은 실패해도 실패 로그만큼은 꼭 DB에 남기고 싶다 -> `REQUIRES_NEW` 감각

즉 `NESTED`는 "같은 이야기 안의 부분 수정", `REQUIRES_NEW`는 "이 기록은 본 이야기와 별개로 저장"이라고 잡으면 된다.

### 왜 Spring/JPA에서는 `NESTED`가 기대처럼 안 보일 때가 있나

여기서 초급자가 하나만 더 기억하면 된다.

- `NESTED`의 핵심은 JPA 마법이 아니라 **JDBC savepoint**다.
- 그래서 Spring/JPA라고 해서 항상 "안쪽 트랜잭션이 하나 더 생긴다"처럼 동작하지는 않는다.
- 특히 JPA 중심 코드에서는 "`NESTED`를 줬는데 왜 그냥 같은 트랜잭션처럼 보이지?"라는 느낌이 자주 나온다.

초급자용 판단표:

## 여기서 `NESTED`는 어떻게 다르게 봐야 하나 (계속 2)

| 상황 | 먼저 가져갈 감각 |
|---|---|
| "안쪽 실패만 잠깐 되감고 싶다" | savepoint가 실제로 가능한 환경인지 먼저 의심한다 |
| "안쪽 성공은 바깥 실패와 무관하게 꼭 남겨야 한다" | `NESTED`보다 `REQUIRES_NEW` 쪽 요구다 |
| "JPA에서 `NESTED`를 붙였는데 차이가 잘 안 보인다" | JPA 자체 중첩 트랜잭션이 아니라 savepoint 지원 문제일 수 있다 |

한 줄로 정리하면:

- `NESTED`는 "새 트랜잭션 추가"가 아니라 "같은 트랜잭션 안의 savepoint"라고 기억해야 오해가 줄어든다.

플랫폼 차이까지 깊게 들어가고 싶다면 [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)를 보고, JPA 쪽에서 왜 이 기대가 더 자주 깨지는지 먼저 짧게 잡고 싶다면 [Spring Mini Card: `JpaTransactionManager`에서 `NESTED` 기대가 자주 깨지는 이유](./spring-jpatransactionmanager-savepoint-expectations-mini-card.md), savepoint 자체 감각이 먼저 필요하면 [Savepoint와 Partial Rollback](../database/savepoint-partial-rollback.md)을 같이 보면 된다.

## 아주 짧은 코드 감각

### `REQUIRED`는 대부분 "기본 참여"다

```java
@Transactional
public void placeOrder() {
    couponService.useCoupon(); // 기본값 REQUIRED
    orderService.saveOrder();  // 기본값 REQUIRED
}
```

별도 설정이 없으면 보통 같은 트랜잭션으로 이해하면 된다.

### `REQUIRES_NEW`는 "이 메서드만 독립 경계"다

```java
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void writeAudit() {
    auditRepository.save(...);
}
```

이 코드는 바깥 실패와 분리해 audit를 남길 수 있다는 의미에 가깝다.

### rollback-only는 옵션이 아니라 "상태"다

`REQUIRED`나 예외 처리 흐름 속에서 현재 트랜잭션이 이미 실패 예정으로 표시된 상태를 말한다.

즉 rollback-only는 "`REQUIRES_NEW`의 반대 옵션"이 아니라, **현재 tx가 커밋될 수 없다는 결과 상태**다.

## 자주 하는 혼동 5개

- `REQUIRES_NEW`는 "실패를 무시하는 마법"이 아니다. 독립 커밋을 만드는 선택이다.
- `REQUIRES_NEW`는 self-invocation 문제를 고치는 수단이 아니다. 프록시 우회 문제는 호출 구조를 먼저 고쳐야 한다.
- catch 했다고 rollback-only가 자동으로 풀리지 않는다.
- `REQUIRED`는 촌스러운 기본값이 아니라, 같은 유스케이스를 같이 묶을 때 가장 자연스러운 기본값이다.
- "조금이라도 중요하면 전부 `REQUIRES_NEW`"는 위험하다. 부분 커밋이 늘수록 설명과 복구가 어려워진다.

## 초급자용 빠른 결정표

| 상황 | 먼저 고를 기본값 | 이유 |
|---|---|---|
| 주문 저장 + 재고 차감 + 쿠폰 사용이 한 유스케이스다 | `REQUIRED` | 같이 성공/실패해야 한다 |
| 본 작업은 실패해도 감사 로그는 꼭 남겨야 한다 | `REQUIRES_NEW` | 보조 기록을 독립 커밋으로 남긴다 |
| 외부 결제 API/브로커 발행이 같이 섞여 있다 | 전파 옵션보다 경계 분리 먼저 | 외부 부작용은 `REQUIRES_NEW`보다 tx 밖/`AFTER_COMMIT`/outbox가 더 정확하다 |
| 예외를 잡고 계속 갔는데 마지막에 `UnexpectedRollbackException`이 난다 | rollback-only 조사 | 이미 같은 tx가 실패 예정일 수 있다 |

## 여기서 어디로 가면 되나

| 지금 필요한 것 | 다음 문서 |
|---|---|
| `@Transactional` 기본 그림부터 다시 보고 싶다 | [@Transactional 기초](./spring-transactional-basics.md) |
| 서비스 경계를 어디에 둬야 할지 헷갈린다 | [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md) |
| rollback-only와 `UnexpectedRollbackException`을 더 정확히 보고 싶다 | [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md) |
| savepoint가 정확히 무엇인지 먼저 짧게 잡고 싶다 | [Savepoint와 Partial Rollback](../database/savepoint-partial-rollback.md) |
| `REQUIRES_NEW`와 `NESTED`를 더 깊게 비교하고 싶다 | [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md) |
| `REQUIRES_NEW`의 suspend/resume, 자원 바인딩까지 보고 싶다 | [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](./spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md) |
| 감사 로그를 장기적으로 더 안전하게 분리하고 싶다 | [Spring EventListener / TransactionalEventListener / Outbox](./spring-eventlistener-transaction-phase-outbox.md) |
| 외부 API를 메인 tx 밖으로 빼는 예시가 필요하다 | [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](./spring-service-layer-external-io-after-commit-outbox-primer.md) |

## 한 줄 정리

초급자 기준으로 전파 선택은 "`REQUIRED`는 같이 간다, `REQUIRES_NEW`는 따로 남긴다, rollback-only는 이미 같이 망한 상태를 뒤늦게 알리는 표시다"로 먼저 잡으면 된다.
