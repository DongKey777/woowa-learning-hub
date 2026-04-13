# State Machine Library vs State Pattern

> 한 줄 요약: State Pattern은 도메인 규칙을 코드로 직접 담는 방식이고, State Machine Library는 전이/이벤트/가드/액션을 외부 엔진으로 관리한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [Saga / Coordinator](./saga-coordinator-pattern-language.md)
> - [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

상태 패턴과 상태 머신 라이브러리는 둘 다 상태 전이를 다룬다.  
하지만 하나는 코드 구조, 다른 하나는 실행 엔진에 가깝다.

- State Pattern: 상태별 행위를 객체로 분리한다
- State Machine Library: 전이 테이블, guard, action, event를 엔진이 처리한다

backend에서는 워크플로가 단순하면 상태 패턴이, 복잡하면 상태 머신 라이브러리가 더 적합할 수 있다.

### Retrieval Anchors

- `state machine library`
- `state pattern`
- `transition table`
- `guard action event`
- `workflow engine`

---

## 깊이 들어가기

### 1. 상태 패턴은 코드 중심이다

상태 객체를 직접 만들면 도메인 규칙이 코드에 응집된다.

- 이해하기 쉽다
- 디버깅이 단순하다
- 작은 워크플로에 적합하다

### 2. 상태 머신 라이브러리는 선언형이다

라이브러리는 보통 다음 개념을 제공한다.

- 상태
- 이벤트
- 전이
- 가드
- 액션

이 구조는 복잡한 승인/보상/재시도 흐름에 잘 맞는다.

### 3. 너무 빨리 라이브러리를 쓰면 과하다

상태가 3~5개뿐이면 오히려 라이브러리가 무겁다.
반대로 전이가 많고 운영 가시성이 필요하면 라이브러리가 낫다.

---

## 실전 시나리오

### 시나리오 1: 결제 워크플로

단순 결제 승인/캡처/취소는 상태 패턴으로 충분할 수 있다.

### 시나리오 2: 복잡한 승인 흐름

여러 단계 승인, 재시도, 타임아웃, 보상이 있으면 상태 머신 엔진이 더 유리하다.

### 시나리오 3: 운영 화면과 추적

상태 머신 라이브러리는 전이 로그와 시각화가 쉬운 경우가 많다.

---

## 코드로 보기

### State Pattern

```java
public interface PaymentState {
    PaymentState approve();
    PaymentState capture();
    PaymentState cancel();
}
```

### State Machine 스타일

```java
public class PaymentStateMachine {
    public void send(PaymentEvent event) {
        // 전이 테이블, guard, action 처리
    }
}
```

### 상태 머신 개념 요소

```java
public record Transition(State from, Event event, State to) {}
public interface Guard { boolean allow(Context context); }
public interface Action { void execute(Context context); }
```

상태 머신 라이브러리는 상태 패턴보다 선언이 많지만, 복잡도가 올라갈수록 관리가 쉬워진다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| State Pattern | 코드가 단순하다 | 복잡한 흐름엔 한계가 있다 | 작은 상태 전이 |
| State Machine Library | 선언형이고 강력하다 | 학습 비용이 있다 | 전이가 많고 추적이 필요할 때 |
| Saga + Workflow Engine | 분산 흐름까지 다룬다 | 운영 복잡도가 크다 | 서비스 간 보상과 재시도 |

판단 기준은 다음과 같다.

- 상태 수가 적고 도메인 규칙이 직접적이면 State Pattern
- guard, action, transition이 많으면 State Machine Library
- 서비스 경계를 넘으면 Saga나 workflow engine을 본다

---

## 꼬리질문

> Q: 상태 패턴과 상태 머신 라이브러리를 어떻게 고르나요?
> 의도: 흐름 복잡도와 운영 요구를 구분하는지 확인한다.
> 핵심: 단순하면 상태 패턴, 복잡하면 상태 머신 엔진이다.

> Q: 상태 머신 라이브러리는 왜 선언형이 유리한가요?
> 의도: 전이 테이블 기반 사고를 이해하는지 확인한다.
> 핵심: 전이, 가드, 액션을 분리해 관리할 수 있기 때문이다.

> Q: 상태 패턴이 더 나은 경우는 언제인가요?
> 의도: 과한 엔진 도입을 경계하는지 확인한다.
> 핵심: 상태가 적고 도메인 규칙이 코드에 직접 드러나야 할 때다.

## 한 줄 정리

State Pattern은 도메인 코드에 상태 전이를 직접 담고, State Machine Library는 더 복잡한 전이와 가드를 선언형으로 관리한다.

