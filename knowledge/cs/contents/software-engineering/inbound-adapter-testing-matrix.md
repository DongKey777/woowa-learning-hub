# Inbound Adapter Testing Matrix

> 한 줄 요약: controller, message consumer, scheduled job는 모두 같은 inbound adapter지만, hexagonal 테스트 포트폴리오는 채널별 실패 모드에 맞춰 `slice-heavy`, `integration-heavy`, `clock/lock-heavy`로 다르게 가져가야 한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: inbound adapter testing matrix basics, inbound adapter testing matrix beginner, inbound adapter testing matrix intro, software engineering basics, beginner software engineering, 처음 배우는데 inbound adapter testing matrix, inbound adapter testing matrix 입문, inbound adapter testing matrix 기초, what is inbound adapter testing matrix, how to inbound adapter testing matrix
채널 자체를 먼저 정리하고 싶다면 [Message-Driven Adapter Example](./message-driven-adapter-example.md), slice와 full integration 경계부터 잡고 싶다면 [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md), 전체 seam 전략을 먼저 보고 싶다면 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)부터 읽고 이 문서는 그다음에 "같은 유스케이스를 여는 세 가지 inbound adapter를 테스트 포트폴리오에서는 어떻게 다르게 가져가야 하나"만 좁혀 보면 된다.

<details>
<summary>Table of Contents</summary>

- [왜 이 matrix가 필요한가](#왜-이-matrix가-필요한가)
- [먼저 공통 원칙부터 잡기](#먼저-공통-원칙부터-잡기)
- [controller adapter는 어떤 테스트 비율이 맞나](#controller-adapter는-어떤-테스트-비율이-맞나)
- [message consumer adapter는 어떤 테스트 비율이 맞나](#message-consumer-adapter는-어떤-테스트-비율이-맞나)
- [scheduled job adapter는 어떤 테스트 비율이 맞나](#scheduled-job-adapter는-어떤-테스트-비율이-맞나)
- [한 표로 보는 adapter별 testing matrix](#한-표로-보는-adapter별-testing-matrix)
- [최소 포트폴리오 예시](#최소-포트폴리오-예시)
- [자주 생기는 오해](#자주-생기는-오해)

</details>

> 관련 문서:
> - [Software Engineering README: Inbound Adapter Testing Matrix](./README.md#inbound-adapter-testing-matrix)
> - [Message-Driven Adapter Example](./message-driven-adapter-example.md)
> - [Webhook and Broker Boundary Primer](./webhook-and-broker-boundary-primer.md)
> - [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
> - [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
> - [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md)
> - [API 설계와 예외 처리](./api-design-error-handling.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [System Design: 분산 스케줄러 설계](../system-design/distributed-scheduler-design.md)
>
> retrieval-anchor-keywords:
> - inbound adapter testing matrix
> - controller consumer scheduler test matrix
> - controller vs consumer vs scheduler testing
> - hexagonal inbound adapter test portfolio
> - controller slice security integration test
> - message consumer ack retry dlq test
> - webhook vs broker consumer test boundary
> - webhook acknowledgment semantics test
> - event consumer contract test
> - scheduled job lock misfire test
> - scheduled job adapter testing
> - cron job integration test hexagonal
> - scheduler overlap prevention test
> - clock-driven adapter test
> - channel-specific adapter test
> - primary adapter testing matrix
> - inbound adapter test ratio

webhook receiver와 broker consumer를 둘 다 외부 이벤트 ingress로 읽되, 왜 test emphasis가 달라지는지 먼저 잡고 싶다면 [Webhook and Broker Boundary Primer](./webhook-and-broker-boundary-primer.md)를 보고 이 문서로 내려오면 된다.

## 왜 이 matrix가 필요한가

[Message-Driven Adapter Example](./message-driven-adapter-example.md)는 controller, consumer, scheduler가 모두 같은 inbound adapter 축에 있다는 점을 설명한다.
[Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)는 controller와 message handler를 slice test와 full integration test로 어떻게 나눌지 설명한다.

실무에서 남는 질문은 그다음이다.

- controller처럼 slice test를 많이 두면 consumer와 scheduler도 같은 비율로 가야 하는가
- consumer의 contract test와 scheduler의 lock test는 같은 종류의 integration risk인가
- 같은 유스케이스를 열더라도 채널별로 어떤 실패 모드를 우선 덮어야 하는가

핵심은 "세 어댑터가 모두 inbound adapter"라는 사실과 "세 어댑터의 테스트 비율이 같다"는 결론은 다르다는 점이다.
비즈니스 규칙은 같은 유스케이스 test가 덮고, adapter test는 각 채널이 실제로 깨지는 방식에 맞춰 달라져야 한다.

## 먼저 공통 원칙부터 잡기

먼저 공유 원칙은 하나다.

- **유스케이스 test**: 세 채널이 공통으로 쓰는 비즈니스 규칙을 검증한다
- **adapter test**: 각 채널이 command를 만들고 runtime과 결합하는 방식을 검증한다

즉 질문은 "어느 adapter가 더 중요하냐"가 아니라 아래에 가깝다.

- controller는 무엇이 유스케이스를 건드리지 않고도 깨질 수 있는가
- consumer는 무엇이 브로커/offset/retry 때문에 추가로 깨질 수 있는가
- scheduler는 무엇이 clock/lock/misfire 때문에 추가로 깨질 수 있는가

짧게 정리하면:

- controller는 **HTTP 번역과 web wiring**
- consumer는 **메시지 번역과 delivery semantics**
- scheduler는 **시간 계산과 중복 실행 제어**

를 더 많이 본다.

## controller adapter는 어떤 테스트 비율이 맞나

세 채널 중 controller는 보통 **slice test 비율이 가장 높다**.
이 채널의 핵심 실패는 request/response 번역, validation, exception mapping, security wiring에 몰리기 때문이다.

### controller에서 많이 가져갈 테스트

- path/query/body가 command로 정확히 번역되는가
- validation 실패가 `400` 계열 응답으로 바뀌는가
- 애플리케이션 예외가 `404`, `409` 같은 HTTP 의미로 번역되는가
- 인증 주체나 request metadata가 use case 인자로 올바르게 전달되는가

이건 대체로 web slice test가 가장 잘 맞는다.
controller는 request/response surface가 넓어서 slice만으로도 높은 신호를 얻는다.

### controller에서 소수만 남길 integration test

- 실제 security filter chain이 응답 의미를 바꾸는가
- serializer module, `@ControllerAdvice`, custom argument resolver가 production 설정과 같은가
- "응답 성공"의 의미가 실제 transaction/DB commit과 강하게 연결되는가

즉 controller는 **많은 slice + 적은 app integration**이 기본형이다.

### controller에서 contract gate가 필요한 순간

HTTP API를 외부 팀이나 외부 클라이언트가 소비한다면 request/response schema를 계약으로 고정하는 test가 추가될 수 있다.
다만 이는 controller의 기본 포트폴리오라기보다 public API 성격이 강할 때 붙는 확장 레이어다.

## message consumer adapter는 어떤 테스트 비율이 맞나

message consumer는 controller보다 **integration test와 contract test 비중이 더 크다**.
이 채널은 payload 번역만 맞아도 충분하지 않고, ack/retry/DLQ/중복 처리 같은 delivery semantics가 실제 장애를 만든다.

### consumer에서 많이 가져갈 테스트

- payload와 header가 command로 정확히 번역되는가
- 지원하지 않는 event version이나 malformed payload를 use case 진입 전에 차단하는가
- correlation id, causation id, tenant, delivery attempt를 올바르게 해석하는가

이 부분은 adapter-only slice test나 좁은 component test로 빠르게 검증할 수 있다.

### consumer에서 반드시 남길 integration test

- use case 성공 이후에만 ack가 나가고 실패 시 retry/DLQ가 production wiring대로 동작하는가
- dedup store나 inbox 상태와 도메인 상태 변경이 같은 transaction으로 묶이는가
- deserializer, listener container, concurrency 설정, observability context가 실제 런타임과 같은가
- 같은 메시지 redelivery에서 side effect가 한 번만 남는가

consumer는 "코드가 맞는가"보다 "설정과 순서가 맞는가"에서 자주 깨진다.
그래서 controller보다 integration coverage를 더 남겨야 한다.

### consumer에서 contract gate가 중요한 이유

메시지 consumer는 다른 서비스의 event schema와 header 규약에 직접 의존한다.
그래서 consumer 포트폴리오는 보통 아래 세 층으로 읽는 편이 안전하다.

- slice/component: payload/header -> command 번역
- integration: ack/retry/transaction/dedup/runtime wiring
- contract: event field/header/version 호환성

즉 consumer는 세 채널 중 **가장 입체적인 테스트 포트폴리오**를 가진다.

## scheduled job adapter는 어떤 테스트 비율이 맞나

scheduled job은 controller처럼 request binding이 풍부하지도 않고, consumer처럼 브로커 contract가 항상 있지도 않다.
대신 **clock, batch window, no-overlap, misfire** 같은 운영 의미가 중요하다.

그래서 scheduler는 보통 **많은 clock-driven component test + 소수의 lock/misfire integration test**가 잘 맞는다.

### scheduler에서 많이 가져갈 테스트

- 현재 시각과 기간 규칙에 따라 어떤 대상을 선택해야 하는가
- 조회한 대상들을 어떤 batch size와 chunk로 잘라 command를 만들 것인가
- 처리할 대상이 없을 때 조용히 종료하는가
- backfill 모드와 정기 실행 모드가 같은 유스케이스를 다른 trigger로 호출하는가

이런 테스트는 실제 cron을 기다릴 필요가 없다.
`Clock` 주입, 직접 `run()` 호출, fake query port로 훨씬 더 빠르고 안정적으로 검증할 수 있다.

### scheduler에서 반드시 남길 integration test

- 두 인스턴스가 동시에 떠도 같은 job이 겹쳐 실행되지 않는가
- distributed lock, lease, shard 정책이 production 설정대로 동작하는가
- misfire 이후 catch-up/backfill 정책이 중복 side effect 없이 이어지는가
- batch 처리 중간 실패 시 checkpoint와 transaction 경계가 기대대로 남는가

scheduler는 controller와 달리 `@Scheduled` annotation 자체보다 **중복 실행 방지와 시간 경계 보존**이 더 큰 리스크다.

### scheduler에서 contract gate가 드문 이유

scheduler는 내부 시계 기반 트리거라면 외부 계약이 거의 없다.
다만 외부 control plane, Quartz payload, workflow engine trigger 같은 별도 orchestrator가 job 실행을 요청한다면 그때는 scheduler도 입력 contract를 가질 수 있다.

## 한 표로 보는 adapter별 testing matrix

| 검증 질문 | controller | message consumer | scheduled job |
|---|---|---|---|
| 입력을 command로 번역하는 규칙 | web slice test | handler slice/component test | job component test |
| 입력 검증, malformed input 차단 | web slice test | slice/component test | component test |
| security/tenant/request context 주입 | 소수 integration 또는 focused security test | integration test | 드물지만 privileged job이면 integration test |
| ack/nack/retry/DLQ | 해당 없음 | 핵심 integration test | 해당 없음 |
| 중복 실행 방지, lock, misfire | 해당 없음 | concurrency/ordering 일부 integration | 핵심 integration test |
| 외부 계약 호환성 | public API면 optional contract test | 보통 strong contract gate | 외부 scheduler가 있으면 optional |
| 기본 포트폴리오 성격 | 많은 slice + 적은 integration | slice + integration + contract | 많은 component + 적은 lock/misfire integration |

결국 세 채널 모두 같은 유스케이스를 호출할 수 있어도, adapter test의 중심 질문은 이렇게 다르다.

- controller: "HTTP 의미를 제대로 번역하는가"
- consumer: "메시지를 안전하게 소비하고 다시 받더라도 안전한가"
- scheduler: "시간 기반 실행이 겹치거나 밀려도 의미가 보존되는가"

## 최소 포트폴리오 예시

예를 들어 `SyncPaymentStatusUseCase`를 세 채널이 함께 연다고 하자.

1. **공통 use case unit test**
   - 결제 상태 전이 규칙
   - 외부 조회 실패 처리
   - 저장/이벤트 발행 여부
2. **controller adapter**
   - `3~5`개의 web slice test
   - `1`개의 security 또는 serialization integration smoke
3. **message consumer adapter**
   - `2~3`개의 payload/header slice test
   - `2`개의 integration test
   - 성공 후 ack / 실패 후 retry or DLQ
   - duplicate redelivery 시 side effect 한 번만 반영
   - `1`개의 event contract gate
4. **scheduled job adapter**
   - `2~4`개의 clock-driven component test
   - stale target selection
   - batch split
   - no-op path
   - `1~2`개의 integration test
   - no-overlap lock
   - misfire/backfill or checkpoint recovery

여기서 중요한 점은 "세 adapter마다 같은 수의 테스트를 두라"가 아니다.
**같은 유스케이스를 중복 검증하지 않으면서, 채널별로 실제로 자주 깨지는 실패 모드를 남기라**는 쪽이 핵심이다.

## 자주 생기는 오해

- controller에서 잘 쓰던 web slice 패턴을 scheduler에 그대로 복사한다. 그러면 시간 계산과 lock 문제가 빠진다.
- consumer도 controller처럼 slice만 많이 두면 충분하다고 본다. 그러면 ack-after-commit, redelivery, DLQ wiring이 늦게 깨진다.
- scheduler test를 실제 cron 시간을 기다리는 sleep 기반 test로 만든다. 느리고 flakiness만 늘어난다.
- 세 adapter가 같은 유스케이스를 호출하니 세 곳에서 비즈니스 분기를 모두 다시 검증한다. 그러면 포트폴리오가 비대해지고 실패 원인이 흐려진다.
- contract test는 controller에만 있다고 생각한다. 메시지 consumer 쪽이 오히려 schema/version contract 의존도가 더 클 수 있다.

## 한 줄 정리

Hexagonal에서 controller, message consumer, scheduled job는 모두 같은 inbound adapter지만, 테스트는 **공통 비즈니스 규칙은 use case에 모으고, 채널별 실패 모드는 controller는 web 번역, consumer는 delivery semantics, scheduler는 clock/lock semantics 중심으로 나눠서 가져가야 한다.**
