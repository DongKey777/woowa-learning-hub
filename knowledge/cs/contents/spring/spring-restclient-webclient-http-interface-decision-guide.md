---
schema_version: 3
title: Spring `RestClient` vs `WebClient` vs HTTP Interface 결정 가이드
concept_id: spring/restclient-webclient-http-interface-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags: []
aliases:
  - spring http client choice
  - restclient webclient http interface 차이
  - 동기 http 클라이언트냐 reactive 클라이언트냐
  - 선언형 http client
  - resttemplate 다음 뭐 써요
  - outbound client 선택
  - http exchange client
  - spring 외부 api 클라이언트 고르기
symptoms:
  - 외부 API를 붙여야 하는데 RestClient로 끝낼지 WebClient로 갈지 감이 안 와요
  - RestClient랑 HTTP interface가 같은 건지 다른 건지 모르겠어요
  - WebClient를 써야 하는지 그냥 동기 호출로 가도 되는지 결정 기준이 없어요
intents:
  - comparison
  - design
  - troubleshooting
prerequisites:
  - spring/boot-autoconfiguration-basics
next_docs:
  - spring/restclient-builder-customizer-vs-dedicated-client-vs-builder-replacement-primer
  - spring/restclient-vs-webclient-lifecycle-boundaries
  - spring/async-context-propagation-restclient-http-interface-clients
linked_paths:
  - contents/spring/spring-restclient-builder-customizer-vs-dedicated-client-vs-builder-replacement-primer.md
  - contents/spring/spring-restclient-vs-webclient-lifecycle-boundaries.md
  - contents/spring/spring-async-context-propagation-restclient-http-interface-clients.md
  - contents/spring/spring-webclient-vs-resttemplate.md
  - contents/spring/spring-webflux-vs-mvc.md
confusable_with:
  - spring/restclient-builder-customizer-vs-dedicated-client-vs-builder-replacement-primer
  - spring/restclient-vs-webclient-lifecycle-boundaries
  - spring/async-context-propagation-restclient-http-interface-clients
forbidden_neighbors: []
expected_queries:
  - Spring에서 외부 API 호출할 때 RestClient, WebClient, HTTP interface 중 무엇부터 고르면 돼?
  - RestClient랑 HTTP interface client는 어떤 관계고 언제 분리해서 생각해야 해?
  - WebClient를 써야 하는 상황과 그냥 RestClient로 끝내도 되는 상황을 어떻게 나눠?
  - resttemplate 다음에 동기 클라이언트로 갈지 reactive 클라이언트로 갈지 결정 기준이 뭐야?
  - 외부 API client를 만들 때 선언형 인터페이스가 맞는지 직접 client를 다루는 게 맞는지 헷갈려
contextual_chunk_prefix: |
  이 문서는 Spring 학습자가 외부 API 호출 클라이언트를 고를 때
  `RestClient`, `WebClient`, HTTP interface client를 먼저 어떤 축으로
  분리해야 하는지 안내하는 chooser다. resttemplate 다음에 뭘 써야 하나,
  reactive까지 필요한가, 선언형 인터페이스는 언제 얹는가 같은 질문을
  실행 모델, 호출 수, 선언 방식 세 갈래 결정으로 연결한다.
---

# Spring `RestClient` vs `WebClient` vs HTTP Interface 결정 가이드

## 한 줄 요약

> blocking 호출이면 `RestClient`, reactive fan-out이면 `WebClient`, 그리고 HTTP interface는 그 위에 얹는 선언 방식이라고 먼저 나누면 된다.

## 결정 매트릭스

| 지금 질문 | 먼저 고를 것 | 이유 |
| --- | --- | --- |
| MVC 서비스에서 외부 API 한두 개를 동기적으로 호출한다 | `RestClient` | 호출 스레드 모델이 단순하고 `RestTemplate` 다음 단계로 읽기 쉽다 |
| 여러 외부 API를 fan-out하거나 reactive 체인 안에서 호출한다 | `WebClient` | non-blocking 체인, timeout, backpressure를 같은 모델에서 다룰 수 있다 |
| 호출 방식은 이미 정했는데 메서드 시그니처를 인터페이스로 선언하고 싶다 | HTTP interface client | `RestClient`나 `WebClient` 위에 얹는 선언형 프록시라 구현 반복을 줄인다 |
| `RestClient`와 HTTP interface 중 하나만 골라야 한다고 느껴진다 | `RestClient` 먼저, 필요하면 HTTP interface 추가 | 둘은 대체 관계보다 "실행 엔진"과 "선언 방식" 관계에 가깝다 |
| WebClient를 쓰지만 내부에서 결국 `block()`할 예정이다 | `RestClient` 재검토 | reactive 장점을 버릴 거면 운영 복잡도만 늘기 쉽다 |

짧게 말하면 결정 축은 세 개다. 첫째는 blocking이냐 reactive냐, 둘째는 fan-out과 스트리밍이 실제로 필요한가, 셋째는 client 코드를 인터페이스 선언형으로 감쌀 가치가 있는가다.

## 흔한 오선택

`RestClient`와 HTTP interface를 경쟁 기술처럼 고르면 구조가 흐려진다. HTTP interface는 보통 "`어떤 메서드 계약으로 호출할까`"의 문제라서, 아래에서 실제 요청을 보내는 엔진은 여전히 `RestClient`나 `WebClient`가 맡는다.

"비동기 같아 보여서 무조건 WebClient"로 가는 것도 흔한 오선택이다. 학습자가 "`외부 API 호출이니까 일단 WebClient가 최신 아닌가요?`"라고 느껴도, 실제로 MVC 요청 스레드에서 한두 번 부르고 `block()`할 거면 `RestClient`가 더 정직한 선택일 수 있다.

"선언형이 좋아 보여서 HTTP interface부터" 시작하면 timeout, retry, context propagation 책임이 가려질 수 있다. "`인터페이스로 만들었는데 왜 인증 헤더와 MDC 전파가 그대로 어렵죠?`"라는 표현이 나오면 선언 방식보다 실행 모델과 경계 설계를 먼저 점검해야 한다.

## 다음 학습

- 공용 baseline, 전용 client bean, builder owner 교체를 나누려면 [Spring `RestClient.Builder` 입문 브리지: `RestClientCustomizer`, 전용 `RestClient` bean, builder 교체는 언제 고르나](./spring-restclient-builder-customizer-vs-dedicated-client-vs-builder-replacement-primer.md)
- blocking과 reactive lifecycle 차이를 더 깊게 보려면 [Spring RestClient vs WebClient Lifecycle Boundaries](./spring-restclient-vs-webclient-lifecycle-boundaries.md)
- `@Async`, SecurityContext, HTTP interface까지 섞인 경계를 보려면 [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
