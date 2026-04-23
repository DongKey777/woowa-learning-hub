# State Pattern vs State Machine Library vs Workflow Engine

> 한 줄 요약: State Pattern은 한 객체나 aggregate의 전이를 코드로 응집시키고, State Machine Library는 한 프로세스 안의 복잡한 전이 표를 관리하며, Workflow Engine은 장기·분산 흐름의 durable 실행을 맡는다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Human Approval and Manual Review Workflow Pattern](./human-approval-manual-review-workflow-pattern.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

세 선택지는 모두 상태 전이를 다루지만, 복잡도의 축이 다르다.

- State Pattern: 한 객체나 aggregate의 **도메인 규칙**을 코드 구조로 드러낸다
- State Machine Library: 한 서비스나 프로세스 안에서 **전이 표, 이벤트, 가드, 액션**을 선언형으로 관리한다
- Workflow Engine: 서비스 경계를 넘거나 오래 걸리는 흐름의 **durable 실행, 타이머, 재시도, 감사 추적**을 맡는다

핵심 질문은 "상태가 몇 개냐"가 아니라, **누가 실행을 소유하고 중단 후 어떻게 재개하며 시간이 어디서 흐르느냐**다.

### Retrieval Anchors

- `state pattern enough`
- `state machine library when`
- `workflow engine when`
- `state machine library vs workflow engine`
- `in process state machine`
- `durable workflow orchestration`
- `long running workflow`
- `transition table guard action`
- `human approval timeout workflow`
- `compensation retry timer`
- `local aggregate state`
- `payment lifecycle state pattern`

---

## 먼저 경계를 자르기

### 1. 상태 패턴은 한 도메인 객체 안에서 끝나는 전이에 맞는다

다음 조건이면 State Pattern을 먼저 본다.

- 상태 owner가 분명하다. 보통 하나의 aggregate나 entity다.
- 전이가 같은 request나 transaction 안에서 끝난다.
- 잘못된 호출 순서를 막는 것이 핵심이다.
- 운영 복잡도보다 도메인 의미를 코드에 드러내는 것이 더 중요하다.

예를 들어 `Payment` aggregate가 `PENDING -> AUTHORIZED -> CAPTURED -> CANCELED`를 가진다면, 이건 대개 상태 패턴으로 충분하다.
문제는 "이 결제가 지금 무엇을 할 수 있느냐"지, 장기 workflow runtime이 아니다.

### 2. 상태 머신 라이브러리는 같은 서비스 안의 전이 행렬이 복잡할 때 맞는다

다음 신호가 보이면 라이브러리를 검토한다.

- 상태, 이벤트, 가드, 액션 조합이 많다.
- transition table을 코드보다 선언적으로 읽는 편이 낫다.
- 테스트가 "어떤 이벤트가 어떤 상태에서 허용되는가"라는 matrix 중심으로 바뀐다.
- 시각화나 전이 그래프가 있으면 운영과 개발 커뮤니케이션이 좋아진다.
- 그래도 실행 ownership은 여전히 한 서비스 안에 있다.

여기서 중요한 점은, state machine library는 보통 **in-process 도구**라는 것이다.
노드가 죽었을 때 타이머 재개, activity retry, human task inbox 같은 durable workflow 기능까지 자동으로 해결해 주진 않는다.

### 3. workflow engine은 상태 모델보다 실행 런타임이 필요한 순간에 들어온다

다음 요구가 생기면 workflow engine 영역이다.

- 흐름이 분, 시간, 일 단위로 이어진다.
- 외부 API 호출 뒤 결과를 기다리거나, crash 이후 재개해야 한다.
- retry, backoff, deadline, timeout, reminder가 중요하다.
- human approval이나 manual review가 정식 step이다.
- 여러 서비스나 participant를 orchestration해야 한다.
- audit trail, replay, execution history가 운영의 핵심이다.

이 경우 문제는 단순한 상태 전이가 아니다.
**실패한 실행을 어떻게 이어 가고, timer와 side effect를 어떻게 durable하게 관리하느냐**가 핵심이다.

---

## 한눈에 결정

| 질문 | State Pattern | State Machine Library | Workflow Engine |
|---|---|---|---|
| 주된 scope | 객체나 aggregate 하나 | 서비스나 프로세스 하나 | 서비스 경계를 넘는 비즈니스 프로세스 |
| 주된 복잡도 | 상태별 허용 행동 | 전이 표와 가드 조합 | 장기 실행, 타이머, 재시도, 사람 개입 |
| 실행 시간 | 같은 요청이나 트랜잭션 | 보통 짧은 흐름, 앱이 제어 | 분에서 일 단위 long-running flow |
| persistence | aggregate 필드면 충분한 경우가 많다 | 앱이 직접 저장한다 | engine의 durable state와 history가 중요하다 |
| 장애 복구 | 앱 재시도로 충분하다 | 앱이 직접 설계한다 | engine이 재개와 재시도 semantics를 제공한다 |
| 운영 가시성 | 로그와 도메인 이벤트면 충분하다 | 전이 그래프가 있으면 유리하다 | execution history와 audit UI가 사실상 필수다 |
| 대표 시그널 | invalid transition 방지 | guard/action explosion | timeout, compensation, human step, cross-service orchestration |

짧게 외우면 이렇다.

- 상태 패턴은 도메인 규칙 응집
- 상태 머신 라이브러리는 전이 표 관리
- 워크플로 엔진은 durable 실행 관리

---

## 무엇이 escalation 신호인가

### State Pattern에서 멈춰도 되는 신호

- 상태 수가 적고 의미가 선명하다
- 전이 규칙이 aggregate 메서드 안에서 읽힌다
- side effect는 이벤트 발행 정도로 분리하면 충분하다
- 운영자가 execution graph까지 볼 필요는 없다

### State Machine Library로 올릴 신호

- 상태, 이벤트, 가드 조합이 늘어 `if`나 `switch`, 상태 객체 클래스가 과하게 비대해진다
- 같은 guard나 action이 여러 전이에 반복된다
- 테스트가 "허용/금지 전이 matrix" 중심으로 바뀐다
- hierarchical state, parallel region, entry/exit action 같은 표현력이 필요하다

### Workflow Engine으로 올릴 신호

- `sleep`, `retry later`, `wait for callback`, `review queue`가 flow의 핵심이다
- node restart 뒤에도 같은 execution을 이어 가야 한다
- participant 호출 실패를 durable하게 재시도해야 한다
- 보상, reconciliation, timeout ownership을 중앙에서 추적해야 한다
- "현재 status"보다 "실행 이력과 대기 중인 timer"가 더 중요하다

---

## 실전 시나리오

### 시나리오 1: 결제 lifecycle

`PENDING -> AUTHORIZED -> CAPTURED -> CANCELED` 같은 결제 lifecycle은 보통 State Pattern으로 충분하다.
한 aggregate의 허용 행동을 막는 게 핵심이고, 실행 자체가 며칠씩 이어지진 않는다.

### 시나리오 2: 구독 결제 재시도 정책

같은 billing service 안에서 `FAILED`, `RETRY_SCHEDULED`, `GRACE_PERIOD`, `SUSPENDED` 같은 상태가 있고,
이벤트, 가드, 액션 조합이 복잡하다면 state machine library가 잘 맞는다.

다만 재시도 스케줄과 timer persistence를 앱이 직접 책임져야 한다는 점은 그대로다.

### 시나리오 3: 대출 심사, 수동 승인, 외부 검증

서류 수집, 신용 조회, 사람 승인, 추가 자료 요청, 24시간 SLA, 재알림, 재개가 붙는 순간 workflow engine 쪽이다.
여기서는 상태 이름보다 deadline, inbox, resume, audit log가 더 중요하다.

### 시나리오 4: 주문, 결제, 재고, 배송 orchestration

짧고 명확한 보상 흐름이면 saga나 process manager로 충분할 수 있다.
하지만 participant가 많고 timeout, human step, recovery가 길게 이어지면 workflow engine이 낫다.

즉 "분산" 자체가 engine 도입 이유는 아니고, **durable orchestration 복잡도**가 기준이다.

---

## 코드로 보기

### State Pattern 감각

```java
public interface PaymentState {
    PaymentState authorize(Payment payment);
    PaymentState capture(Payment payment);
    PaymentState cancel(Payment payment);
}
```

핵심은 상태별 허용 행동이 aggregate 코드에 응집된다는 점이다.

### State Machine Library 감각

```java
machine
    .from(PENDING).on(AUTHORIZE).to(AUTHORIZED).when(canAuthorize)
    .from(AUTHORIZED).on(CAPTURE).to(CAPTURED).when(canCapture)
    .from(AUTHORIZED).on(CANCEL).to(CANCELED).perform(refundAction);
```

핵심은 전이 table, guard, action을 선언형으로 다룬다는 점이다.

### Workflow Engine 감각

```java
workflow PaymentReviewFlow(orderId) {
    authorizePayment();
    await fraudCheckResult();
    if (needsManualReview()) {
        await reviewerDecision().withTimeout(24h);
    }
    capturePayment();
}
```

핵심은 코드 모양이 아니라, 이 실행이 **durable history와 timer**를 가진다는 점이다.

---

## 자주 생기는 오판

### 1. 큰 `switch`를 봤다고 바로 workflow engine으로 가면 과하다

문제가 단순히 코드 구조라면 state pattern이나 state machine library가 먼저다.
workflow engine은 구조 패턴이 아니라 운영 런타임 도입이다.

### 2. state machine library가 workflow engine을 대체하진 않는다

라이브러리가 전이를 잘 표현해도, 다음 문제는 별도로 남는다.

- 재시도 스케줄 저장
- 프로세스 재기동 후 resume
- human task queue
- execution audit/history
- activity idempotency

이것까지 필요하면 library만으로는 부족하다.

### 3. workflow engine이 모든 상태 모델링을 대신하진 않는다

workflow engine을 써도 각 participant 내부의 로컬 전이는 여전히 State Pattern이나 aggregate 규칙으로 남는다.
engine은 전체 orchestration을 맡고, participant는 자기 도메인 전이를 맡는다.

---

## 선택 체크리스트

다음 질문에 먼저 답하면 된다.

1. 상태 owner가 aggregate 하나인가, 아니면 프로세스 전체인가?
2. 이 흐름은 같은 요청 안에서 끝나는가, 아니면 나중에 재개되는가?
3. timer, retry, human approval이 first-class requirement인가?
4. crash 이후에도 execution history를 보존해야 하는가?
5. 문제의 중심이 "도메인 규칙 응집"인가, "전이 matrix 관리"인가, "durable orchestration"인가?

보통 선택은 이렇게 정리된다.

- 1번까지가 전부라면 State Pattern
- 1번은 아니지만 2번이 짧고 5번이 matrix 관리라면 State Machine Library
- 3번과 4번이 강하게 yes면 Workflow Engine

---

## 꼬리질문

> Q: 상태가 10개가 넘으면 무조건 workflow engine인가요?
> 의도: 상태 수와 실행 복잡도를 구분하는지 본다.
> 핵심: 아니다. 상태 수보다 timer, recovery, human step, cross-boundary orchestration 여부가 더 중요하다.

> Q: 상태 머신 라이브러리와 process manager는 같은 건가요?
> 의도: 표현 도구와 도메인 역할을 구분하는지 본다.
> 핵심: 아니다. process manager는 역할이고, state machine library는 그 역할을 구현할 때 쓸 수 있는 도구 중 하나다.

> Q: workflow engine을 쓰면 aggregate 내부 상태 패턴은 필요 없나요?
> 의도: 글로벌 orchestration과 로컬 도메인 모델을 분리하는지 본다.
> 핵심: 필요할 수 있다. engine은 전체 실행을, aggregate는 로컬 invariant와 허용 행동을 책임진다.

## 한 줄 정리

State Pattern은 로컬 도메인 전이를 코드로 응집시키고, State Machine Library는 같은 서비스 안의 복잡한 전이 표를 관리하며, Workflow Engine은 장기·분산 흐름의 durable 실행을 맡는다.
