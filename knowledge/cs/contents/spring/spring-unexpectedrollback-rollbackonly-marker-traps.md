# Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps

> 한 줄 요약: `UnexpectedRollbackException`은 예외를 "갑자기" 던지는 것이 아니라, 이미 rollback-only가 찍힌 트랜잭션을 바깥에서 커밋하려 했다는 사실을 뒤늦게 알려 주는 신호다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Mini Debugging Card for `UnexpectedRollbackException`](./spring-unexpectedrollbackexception-mini-debugging-card.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)
> - [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)

retrieval-anchor-keywords: UnexpectedRollbackException, rollback-only, transaction marked rollback-only, swallowed exception transaction, inner exception outer commit, rollback marker, participation failure

## 핵심 개념

`UnexpectedRollbackException`은 이름 때문에 "예상 못 한 롤백"처럼 느껴진다.

초급자가 먼저 짧은 symptom-to-cause 카드가 필요하면 [Mini Debugging Card for `UnexpectedRollbackException`](./spring-unexpectedrollbackexception-mini-debugging-card.md)부터 보고 이 문서로 내려오면 된다.

하지만 Spring 관점에서 보면 대개 전혀 갑작스럽지 않다.

실제 의미는 보통 이렇다.

- 안쪽 어딘가에서 현재 트랜잭션이 rollback-only로 마킹됐다
- 바깥 코드는 그 사실을 모른 채 계속 진행했다
- 마지막에 커밋하려는 순간 Spring이 "이건 이미 커밋될 수 없는 트랜잭션"이라고 알려 준다

즉 이 예외의 핵심은 rollback 그 자체보다, **이미 실패한 트랜잭션을 성공처럼 계속 끌고 간 호출 구조**다.

## 깊이 들어가기

### 1. rollback-only는 "실패 예정" 표시다

트랜잭션 안쪽에서 예외가 나면 Spring은 현재 트랜잭션을 rollback-only로 마킹할 수 있다.

중요한 점은 그 순간 바로 예외가 바깥까지 그대로 전달되지 않을 수도 있다는 것이다.

- 내부에서 catch 했다
- 다른 계층에서 예외를 감쌌다
- 조건부로 계속 진행했다

이 경우 개발자는 "문제를 처리했으니 괜찮겠지"라고 생각하기 쉽다.

하지만 트랜잭션 입장에서는 이미 **커밋 불가 상태**일 수 있다.

### 2. 예외를 삼켰다고 트랜잭션 실패가 취소되는 것은 아니다

가장 흔한 형태는 이 패턴이다.

```java
@Transactional
public void placeOrder() {
    try {
        paymentService.charge();
    } catch (Exception ex) {
        log.warn("ignore and continue", ex);
    }
    auditRepository.save(new AuditLog("done"));
}
```

겉보기엔 "실패는 무시하고 로그는 남긴다"처럼 보일 수 있다.

하지만 `paymentService.charge()`가 같은 트랜잭션에 참여해 rollback-only를 찍었다면, 바깥 메서드는 결국 커밋 시점에 `UnexpectedRollbackException`을 맞을 수 있다.

즉 catch는 예외 전달만 막을 뿐, **트랜잭션 운명을 되돌려 주지 않는다**.

### 3. inner `REQUIRED` 참여가 특히 자주 만든다

안쪽 메서드가 기본 전파인 `REQUIRED`면 바깥 트랜잭션에 함께 탄다.

이때 안쪽이 실패하면 다음이 흔하다.

- 바깥은 같은 트랜잭션 계속 사용
- 안쪽 실패를 catch
- 바깥은 정상 흐름처럼 마무리 시도
- 마지막 커밋에서 `UnexpectedRollbackException`

즉 이 예외는 전파 설정과 직접 연결된다.

### 4. 해결은 예외를 숨기지 말거나, 경계를 진짜로 분리하는 것이다

흔한 해결 방향은 아래 셋 중 하나다.

- 실패를 실제로 바깥까지 던져 트랜잭션 실패를 명확히 만든다
- 실패를 독립 경계로 분리한다 (`REQUIRES_NEW`, 별도 후속 처리, 이벤트/아웃박스)
- 애초에 함께 실패해야 하는지/독립 커밋이어야 하는지 유스케이스 경계를 다시 잡는다

핵심은 "예외를 덜 보이게"가 아니라, **트랜잭션 fate를 코드 구조와 맞추는 것**이다.

### 5. `TransactionTemplate`에서도 같은 실수는 가능하다

programmatic transaction을 쓴다고 이 문제가 사라지는 것은 아니다.

`setRollbackOnly()`를 찍어 놓고 바깥 코드가 성공처럼 해석하면, 역시 같은 종류의 혼란이 생긴다.

즉 문제는 선언형/프로그램형 방식이 아니라, **rollback-only 상태를 호출자 의미에 제대로 반영했는가**다.

### 6. 운영 디버깅은 "누가 처음 rollback-only를 찍었는가"를 찾는 게 핵심이다

이 예외가 떴을 때 마지막 커밋 지점만 보면 늦다.

오히려 더 중요한 질문은 아래다.

- 최초 예외는 어디서 났는가
- 누가 그 예외를 catch 했는가
- 그 메서드가 같은 tx에 참여했는가

즉 `UnexpectedRollbackException`은 원인이라기보다 **뒤늦게 표면화된 결과**다.

## 실전 시나리오

### 시나리오 1: 결제 실패는 무시하고 주문 상태만 저장하려 했는데 전체가 실패한다

결제와 주문 상태 갱신이 같은 트랜잭션에 있었고, 결제 실패가 rollback-only를 찍었을 수 있다.

### 시나리오 2: 내부 검증 실패를 catch 했는데 마지막에 갑자기 예외가 난다

검증이 같은 트랜잭션 참여자였다면 이미 rollback-only 상태일 수 있다.

### 시나리오 3: audit 로그는 남길 줄 알았는데 그것도 안 남는다

같은 트랜잭션에서 저장했다면 rollback-only에 함께 묶였을 수 있다.

정말 독립적으로 남겨야 하면 별도 경계가 필요하다.

### 시나리오 4: 문제는 inner service인데 stack trace는 outer service 커밋에서 보인다

바로 이게 `UnexpectedRollbackException`을 헷갈리게 만드는 이유다.

표면화 지점과 최초 실패 지점이 다를 수 있다.

## 코드로 보기

### 같은 트랜잭션 참여자가 rollback-only를 찍는 예

```java
@Service
public class PaymentService {

    @Transactional
    public void charge() {
        throw new IllegalStateException("payment failed");
    }
}
```

```java
@Service
public class OrderService {

    @Transactional
    public void placeOrder() {
        try {
            paymentService.charge();
        } catch (Exception ex) {
            log.warn("continue", ex);
        }
        orderRepository.save(new Order());
    }
}
```

### 독립 경계로 분리하는 예

```java
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void writeAudit(String message) {
    auditRepository.save(new AuditLog(message));
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 예외를 그대로 전파 | 트랜잭션 fate가 명확하다 | 호출자가 실패를 직접 처리해야 한다 | 함께 실패해야 하는 작업 |
| 내부에서 예외 catch 후 계속 진행 | 일부 흐름은 단순해 보인다 | rollback-only와 의미가 쉽게 어긋난다 | 매우 신중해야 함 |
| 독립 트랜잭션 분리 | 보조 기록/후속 처리를 남길 수 있다 | 부분 커밋 추적이 복잡해진다 | 감사 로그, 별도 기록 |
| 이벤트/아웃박스 분리 | 정합성 경계가 더 분명하다 | 즉시성은 떨어질 수 있다 | 외부 부작용, 느슨한 결합 |

핵심은 `UnexpectedRollbackException`을 "Spring이 갑자기 던진 예외"로 보지 않고, **이미 실패한 트랜잭션을 성공처럼 다룬 구조의 증상**으로 보는 것이다.

## 꼬리질문

> Q: `UnexpectedRollbackException`은 언제 주로 발생하는가?
> 의도: 표면화 시점 이해 확인
> 핵심: 이미 rollback-only인 트랜잭션을 바깥에서 커밋하려 할 때다.

> Q: 내부에서 예외를 catch 했는데도 왜 마지막에 실패할 수 있는가?
> 의도: catch와 rollback-only 차이 이해 확인
> 핵심: 예외 전달은 막아도 트랜잭션 운명은 되돌리지 못할 수 있기 때문이다.

> Q: audit 로그를 꼭 남기고 싶을 때 왜 같은 트랜잭션에 두면 안 될 수 있는가?
> 의도: 독립 경계 필요성 확인
> 핵심: rollback-only가 찍히면 함께 되돌아갈 수 있기 때문이다.

> Q: 디버깅에서 가장 먼저 찾아야 할 것은 무엇인가?
> 의도: 원인 추적 순서 확인
> 핵심: 마지막 커밋 지점이 아니라 최초로 rollback-only를 유발한 예외다.

## 한 줄 정리

`UnexpectedRollbackException`은 "예상 못 한 롤백"이 아니라, 이미 실패한 트랜잭션을 뒤늦게 커밋하려 했다는 경고다.
