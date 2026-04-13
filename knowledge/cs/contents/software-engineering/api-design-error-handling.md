# API 설계와 예외 처리 🟡 Intermediate

> 좋은 API는 호출자가 소스코드를 읽지 않아도 실패 이유를 알 수 있는 API다.

## 핵심 개념

API 설계와 예외 처리는 결국 세 가지 질문으로 수렴한다.

- **무엇을 공개할 것인가**: 메서드 시그니처, URL, 파라미터
- **실패를 어떻게 표현할 것인가**: 예외, 결과 객체, HTTP 상태 코드
- **예외를 어디서 잡을 것인가**: 도메인, 서비스, 컨트롤러

이 세 질문에 일관된 답이 없으면 코드가 커질수록 예외 처리가 흩어지고, 호출자가 방어 코드를 중복 작성하게 된다.

## 깊이 들어가기

### 좋은 API의 조건

| 조건 | 설명 | 위반 시 증상 |
|------|------|-------------|
| 이름만으로 의도가 읽힌다 | `findById`는 명확, `process`는 모호 | 호출자가 구현을 읽게 됨 |
| 호출자가 알아야 할 것만 드러난다 | 내부 캐시 여부, DB 종류는 감춤 | 변경 시 호출자까지 수정 |
| 실패 경로가 명시적이다 | 어떤 상황에서 어떤 예외가 나는지 예측 가능 | catch-all 남발, 로그 지옥 |
| 멱등성이 보장되거나 명시된다 | GET은 당연히, PUT/DELETE도 설계에 따라 | 재시도 시 부작용 발생 |

### 예외를 어디서 던질 것인가

**원칙: 도메인 규칙 위반은 도메인이 스스로 막아야 한다.**

```java
// 도메인 내부에서 규칙 위반을 감지하고 던진다
public class Order {
    public void cancel() {
        if (this.status == OrderStatus.SHIPPED) {
            throw new OrderAlreadyShippedException(this.id);
        }
        this.status = OrderStatus.CANCELLED;
    }
}
```

서비스 계층이 상태를 꺼내서 `if`로 검증하는 방식은 도메인 규칙이 서비스로 새는 것이다.

```java
// 나쁜 예: 도메인 규칙이 서비스로 유출
public class OrderService {
    public void cancel(Long orderId) {
        Order order = orderRepository.findById(orderId);
        if (order.getStatus() == OrderStatus.SHIPPED) {  // 규칙이 여기 있으면 안 된다
            throw new IllegalStateException("이미 배송됨");
        }
        order.setStatus(OrderStatus.CANCELLED);
    }
}
```

### 예외를 잡는 위치

계층별 책임이 분명해야 한다.

```
도메인       → 규칙 위반 예외 발생 (OrderAlreadyShippedException)
서비스       → 유스케이스 흐름 조율, 필요시 인프라 예외 변환
컨트롤러     → 예외를 HTTP 응답으로 변환
글로벌 핸들러 → 예상치 못한 예외를 안전한 응답으로 변환
```

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    // 도메인 예외 → 클라이언트가 이해할 수 있는 응답
    @ExceptionHandler(OrderAlreadyShippedException.class)
    public ResponseEntity<ErrorResponse> handle(OrderAlreadyShippedException e) {
        return ResponseEntity.status(409)
            .body(new ErrorResponse("ORDER_ALREADY_SHIPPED", e.getMessage()));
    }

    // 인프라 예외 → 내부 디테일을 감추고 안전한 메시지
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception e) {
        log.error("Unexpected error", e);  // 내부 로그에는 상세히
        return ResponseEntity.status(500)
            .body(new ErrorResponse("INTERNAL_ERROR", "서버 오류가 발생했습니다."));
    }
}
```

### 도메인 예외 vs 인프라 예외

| 구분 | 도메인 예외 | 인프라 예외 |
|------|-----------|-----------|
| 원인 | 비즈니스 규칙 위반 | 기술적 실패 |
| 예시 | 잔액 부족, 중복 주문, 권한 없음 | DB 연결 실패, 타임아웃, 파일 I/O |
| 처리 방향 | 사용자에게 의미 있는 메시지 | 재시도 또는 서킷브레이커 |
| 노출 수준 | 클라이언트에 전달 가능 | 내부 로그만, 클라이언트엔 일반 메시지 |

### 예외 vs 결과 객체

예외만이 실패를 표현하는 유일한 방법은 아니다.

```java
// 결과 객체 방식
public sealed interface OrderResult {
    record Success(Order order) implements OrderResult {}
    record AlreadyShipped(Long orderId) implements OrderResult {}
    record NotFound(Long orderId) implements OrderResult {}
}

public OrderResult cancel(Long orderId) {
    Order order = orderRepository.findById(orderId);
    if (order == null) return new OrderResult.NotFound(orderId);
    if (order.isShipped()) return new OrderResult.AlreadyShipped(orderId);
    order.cancel();
    return new OrderResult.Success(order);
}
```

**예외가 더 적합한 경우**: 호출자가 반드시 처리해야 하는 심각한 실패, 깊은 호출 스택에서의 비정상 종료
**결과 객체가 더 적합한 경우**: 실패가 정상적인 비즈니스 흐름의 일부, 컴파일 타임에 모든 경우를 강제하고 싶을 때

## 실전 시나리오

### 시나리오: 주문 취소 API

```
POST /orders/{id}/cancel

성공: 200 + { "orderId": 123, "status": "CANCELLED" }
이미 배송됨: 409 + { "code": "ORDER_ALREADY_SHIPPED", "message": "..." }
주문 없음: 404 + { "code": "ORDER_NOT_FOUND", "message": "..." }
서버 오류: 500 + { "code": "INTERNAL_ERROR", "message": "서버 오류가 발생했습니다." }
```

핵심은 **클라이언트가 `code` 필드를 보고 분기할 수 있어야 한다**는 것이다.
`message`는 사람이 읽는 용도이고, `code`는 프로그램이 분기하는 용도다.

### 안티패턴: 모든 것이 200

```json
// 이러면 클라이언트가 HTTP 상태 코드를 믿을 수 없다
{ "success": false, "errorCode": "NOT_FOUND" }  // HTTP 200으로 내려옴
```

HTTP 상태 코드는 표준이다. 의미에 맞게 쓰는 것이 클라이언트 개발자의 인지 부하를 줄인다.

## 코드로 보기

### 예외 계층 구조 설계

```java
// 비즈니스 예외의 공통 부모
public abstract class BusinessException extends RuntimeException {
    private final String errorCode;

    protected BusinessException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public String getErrorCode() { return errorCode; }
}

// 구체적인 도메인 예외
public class OrderAlreadyShippedException extends BusinessException {
    public OrderAlreadyShippedException(Long orderId) {
        super("ORDER_ALREADY_SHIPPED",
              "주문 " + orderId + "은 이미 배송되어 취소할 수 없습니다.");
    }
}

public class InsufficientBalanceException extends BusinessException {
    public InsufficientBalanceException(Long userId, long required, long actual) {
        super("INSUFFICIENT_BALANCE",
              String.format("잔액 부족: 필요 %d, 현재 %d", required, actual));
    }
}
```

### Checked vs Unchecked

```java
// Checked: 호출자가 반드시 처리 (컴파일러가 강제)
// → 복구 가능한 상황에 적합하지만, 실무에서는 대부분 RuntimeException 선호
public Order findById(Long id) throws OrderNotFoundException;  // 호출 코드가 지저분해짐

// Unchecked: 런타임에 터짐
// → Spring 생태계의 관례, 글로벌 핸들러에서 일괄 처리
public Order findById(Long id);  // 깔끔하지만 어떤 예외가 나는지 문서화 필요
```

실무에서 Checked Exception이 줄어든 이유:
1. `throws` 선언이 인터페이스를 오염시킨다
2. 대부분의 예외는 호출자가 복구할 수 없다
3. Spring의 `@ExceptionHandler`가 Unchecked 기반으로 설계되어 있다

## 트레이드오프

| 선택 | 장점 | 단점 |
|------|------|------|
| 예외 기반 | 깊은 스택에서도 전파 쉬움, 기존 Java 관례 | 흐름 제어에 쓰이면 성능/가독성 저하 |
| 결과 객체 | 컴파일 타임 안전성, 모든 경우 강제 | 보일러플레이트 증가, 중첩 시 복잡 |
| Checked Exception | 컴파일러가 처리 강제 | 인터페이스 오염, throws 전파 |
| Unchecked Exception | 깔끔한 시그니처 | 어떤 예외가 나는지 문서 의존 |
| 에러 코드 문자열 | 클라이언트 분기 쉬움 | 오타 위험, 타입 안전성 없음 |
| 에러 코드 enum | 타입 안전 | 클라이언트-서버 간 동기화 필요 |

## 꼬리질문

- `@ControllerAdvice`에서 모든 예외를 잡으면 편리하지만, 예외 흐름이 보이지 않게 되는 문제는 어떻게 해결하는가?
- 외부 API 호출 실패를 도메인 예외로 감싸야 하는가, 인프라 예외 그대로 두어야 하는가?
- 멱등하지 않은 API에서 타임아웃이 발생하면 클라이언트는 재시도해야 하는가?
- 사용자에게 보여줄 메시지와 개발자가 볼 로그 메시지를 분리하는 기준은 무엇인가?
- 예외 메시지에 민감 정보(userId, 금액 등)를 넣어도 되는가?

## 한 줄 정리

API 설계는 "어떻게 성공하는가"보다 **"어떻게 실패하는가"를 먼저 설계하는 것**이 핵심이다.
