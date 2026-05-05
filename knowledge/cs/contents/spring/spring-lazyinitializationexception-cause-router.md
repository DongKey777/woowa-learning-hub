---
schema_version: 3
title: LazyInitializationException이 나요 원인 라우터
concept_id: spring/lazyinitializationexception-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- entity-response-leakage
- dto-mapping-boundary
- osiv-hides-boundary-bug
aliases:
- lazy initialization exception 원인
- LazyInitializationException 해결 방향
- 지연 로딩 예외가 왜 나지
- jackson 직렬화 중 lazy loading
- service 밖에서 연관 접근
- osiv 끄니 lazy 예외
symptoms:
- 응답 JSON을 만들 때 LazyInitializationException이 터져요
- 서비스에서 조회는 했는데 controller에서 연관 필드 읽다가 지연 로딩 예외가 나요
- OSIV를 끄니까 갑자기 lazy initialization exception이 보여요
- 엔티티를 그대로 반환했더니 Jackson 근처 stack trace에서 예외가 나요
intents:
- symptom
- troubleshooting
prerequisites:
- spring/transactional-basics
- spring/bean-di-basics
next_docs:
- spring/controller-entity-return-vs-dto-return-primer
- spring/request-pipeline-bean-container
- spring/transactional-basics
linked_paths:
- contents/spring/spring-lazyinitializationexception-debug-sequence.md
- contents/spring/spring-controller-entity-return-vs-dto-return-primer.md
- contents/spring/spring-open-session-in-view-tradeoffs.md
- contents/spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md
- contents/spring/spring-persistence-transaction-web-service-repository-primer.md
confusable_with:
- spring/controller-entity-return-vs-dto-return-primer
- spring/transactional-basics
- spring/request-pipeline-bean-container
forbidden_neighbors: []
expected_queries:
- Spring에서 LazyInitializationException이 나면 어디서부터 원인을 나눠 봐야 해?
- 조회는 됐는데 응답 만들 때 lazy loading 예외가 터질 때 첫 분기가 뭐야?
- OSIV를 false로 바꿨더니 갑자기 LazyInitializationException이 보일 때 무엇을 의심해?
- 엔티티를 그대로 반환한 뒤 Jackson stack trace에서 예외가 나면 어떤 문서를 봐야 해?
- service 안에서 DTO를 만든 줄 알았는데 지연 로딩 예외가 계속 나면 fetch plan도 같이 봐야 해?
contextual_chunk_prefix: |
  이 문서는 LazyInitializationException이 왜 드러났는지 감이 안 잡히는
  학습자가 controller 밖 접근, 엔티티 직렬화, transaction 경계 바깥 접근,
  fetch plan 부족을 증상에서 원인으로 이어지게 돕는 symptom_router다.
  응답 만들 때 연관 필드에서 터짐, OSIV 끄고 나서 숨은 문제 노출, 서비스는
  끝났는데 getter가 더 호출됨, 조회는 됐는데 직렬화 단계에서 막힘 같은
  자연어 paraphrase가 본 문서의 원인 분기에 매핑된다.
---

# LazyInitializationException이 나요 원인 라우터

## 한 줄 요약

> `LazyInitializationException`은 대개 JPA 자체 고장보다 "연관을 읽은 위치가 transaction 경계 안이었는가"를 못 나눈 상태라서, 예외가 난 지점부터 controller 밖 접근인지 조회 계획 부족인지 먼저 자르는 편이 빠르다.

## 가능한 원인

1. **DTO 변환이 service 밖으로 밀렸다.** service에서 엔티티만 넘기고 controller나 presenter에서 DTO를 만들면, 이미 닫힌 경계 밖에서 lazy getter를 건드리기 쉽다. 이 경우는 [Controller Entity Return vs DTO Return Primer](./spring-controller-entity-return-vs-dto-return-primer.md)와 [LazyInitializationException Debug Sequence](./spring-lazyinitializationexception-debug-sequence.md)로 가서 DTO 생성 위치를 먼저 본다.
2. **엔티티를 그대로 반환해 Jackson 직렬화가 연관을 읽고 있다.** controller 메서드는 끝났는데 JSON을 만드는 단계에서 getter가 더 호출되면 예외 위치가 serializer 근처로 보일 수 있다. stack trace에 Jackson, `HttpMessageConverter`, serializer가 보이면 [Controller Entity Return vs DTO Return Primer](./spring-controller-entity-return-vs-dto-return-primer.md) 경로가 더 가깝다.
3. **transaction 경계 안에서 필요한 연관을 준비하지 못했다.** service 안에서 DTO를 만드는 줄 알았더라도 필요한 연관을 fetch join이나 `@EntityGraph` 없이 두면 같은 transaction 안에서 추가 조회가 꼬이거나, 경계를 벗어난 순간 예외로 드러날 수 있다. 이 갈래는 [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](./spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)로 내려가 조회 시점 준비 여부를 다시 본다.
4. **OSIV가 문제를 숨기다가 off에서 드러났다.** `spring.jpa.open-in-view=false`로 바꾼 뒤 갑자기 예외가 보이면 새 버그가 생겼다기보다 원래 있던 경계 위반이 빨리 드러난 경우가 많다. 이때는 [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)와 [Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기](./spring-persistence-transaction-web-service-repository-primer.md)로 가서 웹 요청 경계와 영속성 컨텍스트를 함께 본다.

## 빠른 자기 진단

1. stack trace 끝부분이 controller, DTO 변환 메서드, serializer 근처면 "누가 getter를 불렀는가"부터 본다. service 밖 코드가 보이면 [LazyInitializationException Debug Sequence](./spring-lazyinitializationexception-debug-sequence.md)로 이동한다.
2. controller 반환 타입이 엔티티이거나 service가 엔티티를 그대로 넘기고 있으면 [Controller Entity Return vs DTO Return Primer](./spring-controller-entity-return-vs-dto-return-primer.md) 경로가 맞다. 이때 OSIV on이라도 안전하다고 결론 내리면 안 된다.
3. service 안에서 DTO를 만들고 있는데도 필요한 연관 값에서 막히면 repository 조회 메서드가 연관을 미리 읽는지 확인한다. 조회 계획이 흐리면 [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](./spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)로 간다.
4. 설정 변경 뒤에만 예외가 눈에 띄면 `open-in-view` 값을 확인한다. off에서만 보이는 경우는 원인 제거보다 노출 시점 변화일 수 있으니 [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)로 분기한다.

## 다음 학습

- 예외를 가장 짧은 순서로 추적하고 싶으면 [LazyInitializationException Debug Sequence](./spring-lazyinitializationexception-debug-sequence.md)를 먼저 본다.
- controller가 엔티티를 그대로 반환하는 구조가 왜 위험한지 다시 묶고 싶으면 [Controller Entity Return vs DTO Return Primer](./spring-controller-entity-return-vs-dto-return-primer.md)로 이어 간다.
- 예외를 없애는 과정에서 조회 시점 연관 준비가 부족했다면 [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](./spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)를 다음 문서로 고른다.
