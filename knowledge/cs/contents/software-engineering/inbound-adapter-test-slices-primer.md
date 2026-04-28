# Inbound Adapter Test Slices Primer

> 한 줄 요약: Hexagonal Architecture에서 controller와 message handler test는 port 경계에서 멈춰 adapter 번역 책임만 볼 때는 slice test로, 실제 트랜잭션/브로커/보안 wiring까지 실패 모드가 이어질 때는 앱 통합 테스트(app integration test)로 나눈다.

**난이도: 🟡 Intermediate**

입력 채널 자체를 먼저 정리하고 싶다면 [Message-Driven Adapter Example](./message-driven-adapter-example.md), 전체 seam 전략을 먼저 보고 싶다면 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)부터 읽고 이 문서는 그다음에 "inbound adapter는 어디까지 slice로 자르고, 언제 앱 통합 테스트로 올릴까"만 좁혀 보면 된다.

<details>
<summary>Table of Contents</summary>

- [왜 이 follow-up이 필요한가](#왜-이-follow-up이-필요한가)
- [먼저 한 문장 기준부터 잡기](#먼저-한-문장-기준부터-잡기)
- [controller slice test는 어디까지 검증하나](#controller-slice-test는-어디까지-검증하나)
- [message handler slice test는 어디까지 검증하나](#message-handler-slice-test는-어디까지-검증하나)
- [앱 통합 테스트가 필요한 순간](#앱-통합-테스트가-필요한-순간)
- [결정 표로 빠르게 고르기](#결정-표로-빠르게-고르기)
- [hexagonal 최소 포트폴리오는 어떻게 잡나](#hexagonal-최소-포트폴리오는-어떻게-잡나)
- [자주 생기는 오해](#자주-생기는-오해)

</details>

관련 문서:

- [Software Engineering README: Inbound Adapter Test Slices Primer](./README.md#inbound-adapter-test-slices-primer)
- [테스트 전략 기초](./test-strategy-basics.md)
- [Servlet Filter vs MVC Interceptor Beginner Bridge](./servlet-filter-vs-mvc-interceptor-beginner-bridge.md)
- [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
- [Message-Driven Adapter Example](./message-driven-adapter-example.md)
- [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
- [API 설계와 예외 처리](./api-design-error-handling.md)
- [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](../spring/spring-mvc-filter-interceptor-controlleradvice-boundaries.md)

retrieval-anchor-keywords: inbound adapter test slice, inbound adapter test slices primer, controller slice test, message handler slice test, slice vs app integration test, springboottest inbound integration, hexagonal inbound adapter test, web adapter slice test, request binding validation test, webmvctest first test checklist, controller input validation first test, 처음 배우는데 filter interceptor 때문에 controller test 헷갈림, filter interceptor basics before controller test, filter vs interceptor before controller test, inbound adapter test slices primer basics

controller와 message handler 중심 설명에서 scheduled job까지 포함한 채널별 테스트 비율을 비교하고 싶다면 [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)를 이어서 보면 된다.

`테스트 전략 기초`의 30초 자가진단에서 `Controller 입력 검증/응답 포맷 변경`을 골랐다면, 이 문서는 그 다음 질문인 "`@WebMvcTest`로 어디까지 보고 어디서 멈출까?"를 바로 이어서 설명하는 역링크다.
처음 배우는데 `filter`와 `interceptor`부터 헷갈려 controller 테스트 초점이 흐린다면, 깊은 Spring 문서로 바로 내려가기 전에 [Servlet Filter vs MVC Interceptor Beginner Bridge](./servlet-filter-vs-mvc-interceptor-beginner-bridge.md)로 먼저 큰 그림을 고정하고 돌아오면 된다.

## 왜 이 follow-up이 필요한가

[Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)에서 outbound port 쪽 seam은 비교적 직관적이다.
유스케이스는 fake outbound port로 빠르게 검증하고, persistence/external API adapter는 integration test로 별도 검증하면 된다.

하지만 inbound adapter는 더 자주 헷갈린다.

- controller도 framework 코드가 많이 섞인다
- message handler도 payload, header, ack, retry 규칙이 붙는다
- 그렇다고 매번 전체 애플리케이션을 올리면 느리고 실패 원인이 흐려진다

즉 inbound adapter는 "unit test냐 integration test냐"보다 먼저 **port 경계에서 멈출 것인가, 실제 runtime wiring까지 통과시킬 것인가**를 구분해야 한다.

## 먼저 한 문장 기준부터 잡기

실무 기준은 이 한 문장으로 충분하다.

- **slice test**: inbound adapter가 요청/메시지를 **use case port 호출로 번역하는 책임**만 검증한다
- **앱 통합 테스트(app integration test)**: 실제 adapter entrypoint부터 **real use case와 주요 runtime wiring**까지 이어지는 실패 모드를 검증한다

여기서 핵심은 경계를 어디에 두느냐다.
이 문맥의 앱 통합 테스트는 브라우저부터 외부 시스템까지 전부 붙이는 E2E와는 다르고, 보통 **애플리케이션 entrypoint에서 real use case와 핵심 인프라 연결까지 확인하는 `@SpringBootTest` 계열 테스트**에 가깝다.

| 테스트 종류 | 어디서 멈추나 | 주로 보는 실패 |
|---|---|---|
| slice test | use case port 앞에서 멈춘다 | 바인딩, 검증, 직렬화, 예외 번역, header 해석 |
| 앱 통합 테스트 | real use case와 핵심 outbound adapter까지 통과한다 | 트랜잭션, 보안 체인, listener container, broker/DB wiring, commit-after-ack 같은 실제 runtime 결합 |

즉 slice test는 "adapter가 port를 올바르게 호출하는가"를 보고, 앱 통합 테스트는 "이 entrypoint가 실제 앱 안에서 끝까지 안전하게 동작하는가"를 본다.

## controller slice test는 어디까지 검증하나

controller는 hexagonal 구조에서 대표적인 inbound adapter다.
그래서 slice test의 기본 모양은 **web adapter + serializer/validator/exception mapper**까지만 올리고, use case port는 fake나 mock으로 대체하는 쪽이 맞다.

controller slice에서 잘 맞는 질문:

- path/query/body가 command로 올바르게 번역되는가
- 입력 검증 실패가 기대한 `400` 계열 응답으로 나가는가
- 도메인/애플리케이션 예외가 `409`, `404` 같은 HTTP 의미로 번역되는가
- controller가 use case port를 기대한 인자로 정확히 호출하는가

반대로 아래는 controller slice의 주제가 아니다.

- 실제 트랜잭션이 열리고 커밋되는가
- JPA 매핑이나 DB 제약이 맞는가
- 보안 필터 체인 전체가 production 설정과 동일하게 동작하는가

예를 들면 아래처럼 읽으면 된다.

```java
@RestController
class OrderController {
    private final PlaceOrderUseCase useCase;

    @PostMapping("/orders")
    ResponseEntity<OrderResponse> place(@Valid @RequestBody PlaceOrderRequest request) {
        OrderId orderId = useCase.place(request.toCommand());
        return ResponseEntity.status(201).body(new OrderResponse(orderId.value()));
    }
}
```

이 controller의 slice test는 "주문 생성 규칙이 맞는가"가 아니라 아래를 본다.

- JSON body가 `PlaceOrderCommand`로 잘 번역되는가
- validation 실패 시 use case를 호출하지 않는가
- `OrderAlreadyClosedException`이 `409`로 번역되는가

즉 controller slice는 **HTTP 의미를 port 호출로 바꾸는 adapter 책임**에 집중한다.

## message handler slice test는 어디까지 검증하나

message handler도 똑같이 inbound adapter다.
다만 HTTP 대신 payload, header, ack/nack 같은 채널 규칙이 붙는다.

message handler slice에서 잘 맞는 질문:

- payload와 header가 command로 올바르게 번역되는가
- 이벤트 타입/버전/tenant 정보 해석이 기대대로 되는가
- recoverable/non-recoverable 예외를 handler가 올바른 처리 경로로 분기하는가
- handler가 use case port를 한 번만 호출하는가

예시는 아래처럼 생각하면 된다.

```java
class PaymentAuthorizedHandler {
    private final SyncPaymentStatusUseCase useCase;

    void handle(PaymentAuthorizedMessage message) {
        useCase.sync(new SyncPaymentStatusCommand(
            message.paymentId(),
            SyncTrigger.MESSAGE_EVENT
        ));
    }
}
```

이 handler의 slice test는 "결제 동기화 규칙 전체"를 다시 검증하지 않는다.
대신 아래를 본다.

- 메시지 envelope가 command로 정확히 변환되는가
- 필수 header가 없을 때 즉시 실패/격리하는가
- business rule은 handler가 아니라 use case로 위임되는가

Spring처럼 전용 messaging slice가 약한 프레임워크에서는 "adapter-only context + fake use case port" 형태의 좁은 integration test가 사실상 slice 역할을 하기도 한다.
중요한 것은 어노테이션 이름이 아니라 **검증 경계가 port 앞에서 멈추는가**다.

## 앱 통합 테스트가 필요한 순간

inbound adapter라도 아래 위험이 핵심이면 앱 통합 테스트로 올리는 편이 맞다.

### 1. 실제 runtime wiring이 핵심일 때

- controller filter/interceptor/security chain이 결과를 바꾼다
- `@ControllerAdvice`, serializer module, custom argument resolver가 함께 동작해야 한다
- message listener container 설정, deserializer, concurrency 설정이 실제 동작을 좌우한다

이 경우 adapter만 잘 만들어도 실제 앱에서는 깨질 수 있다.

### 2. port 뒤쪽 실패 모드가 entrypoint 의미를 바꿀 때

- HTTP 요청 하나가 실제 transaction과 DB write까지 이어져야 한다
- 메시지 처리에서 DB commit과 ack 순서가 중요하다
- idempotency store, dedup table, outbox write가 handler 성공 의미를 결정한다

이때는 port 앞에서 멈추면 가장 위험한 실패를 놓친다.

### 3. framework/broker semantics를 직접 확인해야 할 때

- 실제 malformed JSON이 converter에서 어떻게 실패하는가
- broker redelivery, backoff, DLQ routing이 기대대로 동작하는가
- timeout, transaction rollback, retry policy가 production과 같은 체인으로 연결되는가

이건 fake port나 hand-written test harness만으로는 충분히 증명되지 않는다.

### 4. 팀이 자주 틀리는 wiring이 그 지점에 모일 때

기술적으로는 slice로도 충분해 보이더라도, 팀이 반복해서 아래를 놓친다면 앱 통합 테스트 몇 개가 가치가 있다.

- security annotation 누락
- message consumer factory 설정 드리프트
- validation group/serializer registration 누락
- transaction boundary 밖에서 ack해 버리는 실수

즉 "실제로 자주 깨지는 곳"이 port 뒤 runtime 결합이라면 거기까지 덮는 테스트를 남겨야 한다.

## 결정 표로 빠르게 고르기

| 질문 | slice test가 맞는가 | 앱 통합 테스트가 맞는가 |
|---|---|---|
| HTTP body/header를 command로 바꾸는 규칙을 보고 싶다 | 예 | 아니오 |
| invalid request가 `400`으로 번역되는지 보고 싶다 | 예 | 아니오 |
| handler가 특정 payload를 받고 use case를 호출하는지 보고 싶다 | 예 | 아니오 |
| controller 호출 후 실제 DB 상태와 transaction을 보고 싶다 | 아니오 | 예 |
| listener가 메시지 처리 후 ack/retry/DLQ까지 production wiring대로 움직이는지 보고 싶다 | 아니오 | 예 |
| 비즈니스 분기 자체가 맞는지 보고 싶다 | 아니오, use case test로 이동 | 경우에 따라 다르지만 보통 use case test가 먼저 |

짧게 정리하면:

- **adapter 번역 책임**이면 slice test
- **runtime 결합 책임**이면 앱 통합 테스트
- **비즈니스 규칙 책임**이면 use case test

## hexagonal 최소 포트폴리오는 어떻게 잡나

과하게 무거운 테스트 묶음을 만들 필요는 없다.
보통 아래 조합이면 충분하다.

1. use case unit test
   - fake outbound port로 비즈니스 규칙 검증
2. inbound adapter slice test
   - controller/message handler가 port를 어떻게 호출하는지 검증
3. 소수의 앱 통합 테스트
   - security, transaction, broker/DB wiring, idempotency 같은 실제 실패 모드 검증

예를 들어 주문 생성과 결제 이벤트 소비가 같이 있는 서비스라면:

- `PlaceOrderService`는 fake `OrderRepository`, fake `PaymentGateway`로 unit test
- `OrderController`는 request/response/exception mapping 위주로 slice test
- `PaymentAuthorizedHandler`는 payload/header -> command 번역 위주로 slice test
- 실제 `POST /orders`와 `payment-authorized` 소비 경로는 각각 1~2개의 앱 통합 테스트로 security/transaction/ack 결합만 확인

핵심은 **많은 slice + 적은 앱 통합 테스트**이지, 둘 중 하나만 선택하는 것이 아니다.

## 자주 생기는 오해

- controller나 handler test에서 use case 내부 분기까지 다 검증하려 한다. 그러면 adapter test가 비즈니스 테스트를 중복한다.
- `SpringBootTest` 하나로 다 덮으면 안심된다고 본다. 느리고 실패 원인이 섞여서 port 경계 감각이 사라진다.
- slice test에 `@Import`를 계속 얹어 결국 real repository와 real config까지 끌어온다. 그러면 이름만 slice인 애매한 준통합 테스트가 된다.
- 앱 통합 테스트를 하나도 두지 않는다. 그러면 ack/transaction/security/serializer wiring 같은 실제 런타임 실패를 늦게 발견한다.

## 한 줄 정리

Hexagonal inbound adapter 테스트의 기준은 단순하다. controller/message handler가 **entry signal을 use case port 호출로 번역하는 책임**만 보면 slice test를 쓰고, 그 entrypoint의 의미가 실제 transaction, broker, security, serializer wiring까지 걸려 있으면 앱 통합 테스트로 올린다.
