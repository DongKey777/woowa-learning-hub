# Outbox and Message Adapter Test Matrix

> 한 줄 요약: outbox/inbox와 message-driven adapter는 같은 메시징 흐름 안에 있지만, unit test는 결정 로직, integration test는 트랜잭션·브로커·중복 제어 wiring, contract test는 이벤트 schema 약속을 검증하도록 분리해야 한다.

**난이도: 🔴 Advanced**

메시징 구조를 먼저 정리하고 싶다면 [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md), [Message-Driven Adapter Example](./message-driven-adapter-example.md), [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)부터 읽고, 이 문서는 그다음에 "그러면 테스트를 어디에 배치해야 하나?"만 좁혀서 보면 된다.

<details>
<summary>Table of Contents</summary>

- [왜 이 matrix가 필요한가](#왜-이-matrix가-필요한가)
- [먼저 세 가지 테스트 경계부터 구분하기](#먼저-세-가지-테스트-경계부터-구분하기)
- [Outbox producer는 무엇을 어디서 검증하나](#outbox-producer는-무엇을-어디서-검증하나)
- [Inbox consumer는 무엇을 어디서 검증하나](#inbox-consumer는-무엇을-어디서-검증하나)
- [Message-driven adapter는 무엇을 어디서 검증하나](#message-driven-adapter는-무엇을-어디서-검증하나)
- [한 표로 보는 test matrix](#한-표로-보는-test-matrix)
- [최소 포트폴리오는 어떻게 잡나](#최소-포트폴리오는-어떻게-잡나)
- [자주 생기는 오해](#자주-생기는-오해)

</details>

> 관련 문서:
> - [Software Engineering README: Outbox and Message Adapter Test Matrix](./README.md#outbox-and-message-adapter-test-matrix)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Message-Driven Adapter Example](./message-driven-adapter-example.md)
> - [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
> - [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)
> - [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [Event Schema Versioning and Compatibility](./event-schema-versioning-compatibility.md)
> - [Backward Compatibility Test Gates](./backward-compatibility-test-gates.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [System Design: Change Data Capture / Outbox Relay 설계](../system-design/change-data-capture-outbox-relay-design.md)

> retrieval-anchor-keywords:
> - outbox test matrix
> - inbox test matrix
> - message adapter test matrix
> - outbox unit integration contract test
> - inbox dedup integration test
> - message-driven adapter contract test
> - event consumer contract test
> - outbox relay integration test
> - transaction commit before publish test
> - message ack retry dlq test
> - contract vs integration messaging
> - idempotent consumer test boundary
> - event schema compatibility test
> - broker adapter test split
> - message testing portfolio

controller, message consumer, scheduled job를 채널별로 어떤 테스트 포트폴리오로 가져갈지 먼저 비교하고 싶다면 [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)를 먼저 읽고 이 문서를 consumer 쪽 심화편으로 이어 보면 된다.

## 왜 이 matrix가 필요한가

메시징 기반 서비스에서 테스트가 섞이기 쉬운 이유는 실패 원인이 서로 다른데도 전부 "Kafka test"나 "integration test"라는 한 이름으로 묶여 버리기 때문이다.

- outbox 쪽에서는 "도메인 상태는 저장됐는데 publish할 row가 안 남는가"가 핵심이고
- inbox 쪽에서는 "같은 메시지가 다시 와도 side effect가 한 번만 적용되는가"가 핵심이며
- adapter 쪽에서는 "payload/header를 유스케이스 호출로 올바르게 번역하는가"가 핵심이다

여기에 서비스 간 약속까지 붙으면 또 다른 질문이 생긴다.

- 새 이벤트 필드가 기존 consumer parser를 깨지 않는가
- header, topic, key, schema version을 다른 팀도 같은 의미로 해석하는가
- 과거 이벤트 replay가 현재 consumer에서도 여전히 읽히는가

즉 하나의 메시징 흐름 안에도 최소 세 가지 검증 경계가 있다.

- **unit test**: 내부 결정 로직
- **integration test**: 이 서비스 안의 runtime wiring
- **contract test**: 서비스 사이의 약속

이 셋을 섞어 두면 테스트는 많은데도 가장 위험한 실패를 놓치기 쉽다.

## 먼저 세 가지 테스트 경계부터 구분하기

| 테스트 종류 | 주된 질문 | 어디까지 올리나 | 대표 실패 |
|---|---|---|---|
| unit test | "이 상황에서 이벤트를 내보내거나 처리해야 하나?" | 유스케이스, mapper, 정책 객체 | 조건 분기, 상태 전이, 중복 판단 로직 |
| integration test | "트랜잭션, DB, 브로커, listener wiring이 실제 순서대로 안전한가?" | DB, transaction manager, serializer, broker/container, dedup store | commit-before-ack, outbox 상태 꼬임, redelivery 중복 반영 |
| contract test | "다른 서비스가 이 메시지를 계속 읽고 해석할 수 있는가?" | producer/consumer schema와 sample payload | 필수 필드 삭제, enum 의미 변경, header 계약 누락 |

짧게 정리하면:

- unit test는 **결정**을 본다
- integration test는 **실행 순서와 기술 결합**을 본다
- contract test는 **경계 약속**을 본다

따라서 "메시지 publish가 됐다"는 이유만으로 contract가 검증된 것도 아니고, "계약 테스트가 통과했다"는 이유만으로 outbox transaction이 안전한 것도 아니다.

## Outbox producer는 무엇을 어디서 검증하나

outbox producer 쪽에서는 "언제 이벤트를 만든다"와 "그 이벤트가 실제로 같은 트랜잭션에 기록된다"를 분리해서 봐야 한다.

### unit test로 볼 것

- 특정 도메인 상태 전이에서 integration event를 만들어야 하는가
- domain event를 외부 전송용 payload로 매핑할 때 필수 값이 빠지지 않는가
- relay 정책 객체가 retryable/non-retryable failure를 어떻게 분류하는가

이 단계는 메모리 안에서 충분하다.
여기서 broker round-trip이나 실제 DB flush를 붙이면 느려질 뿐 아니라 실패 원인도 흐려진다.

### integration test로 볼 것

- aggregate 저장과 outbox row 기록이 **같은 트랜잭션**으로 묶이는가
- relay가 publish 성공 전에는 row를 `SENT`로 바꾸지 않는가
- publish 실패 시 retry count, next attempt, poison 상태 전이가 기대대로 남는가
- 실제 serializer, header enricher, topic routing 설정이 runtime과 같은가

outbox의 핵심 리스크는 원자성과 상태 전이다.
이건 mock repository나 mock broker로는 충분히 증명되지 않는다.

### contract test로 볼 것

- outbox payload가 consumer가 기대하는 field, header, version을 만족하는가
- additive change가 기존 consumer를 깨지 않는가
- topic, event type, schema subject 같은 외부 식별자가 release gate에서 고정되는가

즉 outbox table이 생겼다는 사실 자체는 producer contract를 증명하지 않는다.
DB 안에 잘 썼더라도, 외부로 나가는 메시지 schema가 깨지면 소비자 입장에서는 장애다.

## Inbox consumer는 무엇을 어디서 검증하나

inbox나 dedup store를 쓰는 consumer는 "중복 감지 정책"과 "중복 감지 + side effect + ack 순서"를 분리해서 봐야 한다.

### unit test로 볼 것

- 이미 처리한 메시지일 때 어떤 경로로 빠져야 하는가
- recoverable/non-recoverable exception을 어떻게 나눌 것인가
- payload/header에서 command를 만드는 규칙과 기본값 해석이 맞는가

이 부분은 handler나 policy object 단위로 빨리 검증하는 편이 낫다.

### integration test로 볼 것

- dedup record 저장과 도메인 상태 변경이 같은 트랜잭션으로 묶이는가
- 같은 메시지가 redelivery되어도 side effect가 한 번만 남는가
- rollback 시 inbox 상태가 어중간하게 남지 않는가
- listener container의 ack/nack, retry, DLQ routing이 production wiring과 같은가

inbox가 필요한 이유 자체가 "중복과 재전송이 현실"이기 때문이다.
따라서 duplicate delivery 경로는 happy path만큼 중요하다.

### contract test로 볼 것

- consumer가 지원하는 event version과 optional field 기본값 해석이 명시돼 있는가
- 새 enum 값, 새 header, 필수 필드 제거가 현재 parser를 깨지 않는가
- 과거에 저장된 이벤트 샘플을 replay해도 현재 consumer가 계속 읽을 수 있는가

inbox는 중복 처리 장치이지 schema 호환성 장치가 아니다.
중복에 안전해도 payload 의미가 바뀌면 여전히 잘못 처리할 수 있다.

## Message-driven adapter는 무엇을 어디서 검증하나

[Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)가 slice와 full integration 경계를 설명했다면, 여기서는 그 adapter를 outbox/inbox 흐름과 연결해서 읽으면 된다.

### unit test 또는 slice test로 볼 것

- 메시지 envelope와 header가 use case command로 정확히 번역되는가
- tenant, correlation id, causation id, delivery attempt 정보를 올바르게 해석하는가
- malformed payload나 지원하지 않는 version을 use case 진입 전에 차단하는가

이 경계의 핵심은 "adapter 번역 책임"이다.
비즈니스 규칙 전체나 브로커 재시도 자체를 여기서 다 증명하려고 하면 테스트가 비대해진다.

### integration test로 볼 것

- 실제 deserializer, listener container, transaction boundary가 함께 동작하는가
- observability context나 security/tenant context가 runtime과 같은 방식으로 주입되는가
- use case 성공 이후에만 ack가 나가고, 실패 시 retry/DLQ가 기대대로 이어지는가

message-driven adapter에서 가장 자주 깨지는 건 코드 한 줄보다 설정 드리프트다.
그래서 production과 같은 wiring을 확인하는 소수의 integration test가 필요하다.

### contract test로 볼 것

- upstream producer가 보내는 event envelope와 header 규약을 이 consumer가 계속 만족할 수 있는가
- topic/key/version 계약이 문서가 아니라 자동 검증으로 고정돼 있는가
- consumer가 의존하는 의미 규칙이 provider와 같은가

즉 message-driven adapter의 contract test는 HTTP API의 response contract와 비슷하지만, 대상이 response body가 아니라 **이벤트 메시지 경계**라는 점만 다르다.

## 한 표로 보는 test matrix

| 검증 대상 | unit test | integration test | contract test |
|---|---|---|---|
| 유스케이스가 이벤트를 발행해야 하는 조건 | 예 | 아니오 | 아니오 |
| domain event -> integration event 매핑 함수 | 예 | 경우에 따라 | 아니오 |
| aggregate 저장 + outbox row 기록 원자성 | 아니오 | 예 | 아니오 |
| relay publish 후 상태 전이와 재시도 | 일부 정책만 | 예 | 아니오 |
| payload/header -> command 번역 | 예 | 예, 실제 converter 검증 시 | 아니오 |
| dedup 판단과 duplicate skip 정책 | 예 | 예, 실제 redelivery 확인 시 | 아니오 |
| ack, retry, DLQ, transaction ordering | 아니오 | 예 | 아니오 |
| event field, header, version 호환성 | 아니오 | 일부 serialization smoke만 | 예 |
| historical payload replay 호환성 | 아니오 | 아니오 | 예 |

이 표를 실무 식으로 바꾸면 아래 질문이 된다.

- "도메인 로직이 맞는가?" -> unit test
- "지금 이 서비스의 runtime wiring이 안전한가?" -> integration test
- "배포 후에도 다른 팀 서비스가 이 메시지를 계속 읽는가?" -> contract test

## 최소 포트폴리오는 어떻게 잡나

모든 consumer마다 거대한 E2E를 붙일 필요는 없다.
보통은 아래 조합이 작고 강하다.

1. **유스케이스 unit test**
   - emit / no-emit
   - duplicate / first-delivery
   - retryable / non-retryable 분기
2. **adapter slice test**
   - payload/header -> command 번역
   - malformed event 차단
3. **outbox integration test**
   - aggregate write와 outbox write 원자성
   - relay 상태 전이
4. **consumer integration test**
   - first delivery
   - duplicate redelivery
   - poison message -> retry or DLQ
5. **producer/consumer contract gate**
   - field/header/version compatibility
   - replay sample verification

핵심은 "많은 unit/slice + 적은 integration + release에 걸리는 contract gate"다.
세 종류를 한 테스트 스위트에 우겨 넣는 것이 아니다.

## 자주 생기는 오해

- Testcontainers로 broker를 띄운 integration test 하나면 메시징 품질이 다 증명된다고 본다. 이 테스트는 runtime wiring은 보여 주지만 schema 호환성까지 대신하지 못한다.
- contract test만 있으면 안전하다고 본다. contract는 소비자 약속을 검증할 뿐, outbox 원자성이나 ack-after-commit 순서는 검증하지 않는다.
- outbox를 mock repository로 테스트했으니 atomicity도 증명됐다고 본다. atomicity는 실제 transaction과 persistence layer를 올려 봐야 한다.
- inbox dedup은 repository 테스트만 있으면 충분하다고 본다. 실제 redelivery와 rollback 순서는 listener/container를 포함한 integration test에서 드러난다.
- 모든 handler마다 end-to-end broker round-trip을 잔뜩 만든다. 그러면 느리고 취약한 테스트만 늘고, 진짜 중요한 compatibility gate 운영이 빠질 수 있다.

## 한 줄 정리

Outbox/inbox와 message-driven adapter의 테스트는 한 종류로 뭉치지 말고, **결정은 unit, 실행 순서는 integration, 서비스 사이 약속은 contract**로 분리해야 가장 적은 수의 테스트로 가장 큰 메시징 리스크를 잡을 수 있다.
