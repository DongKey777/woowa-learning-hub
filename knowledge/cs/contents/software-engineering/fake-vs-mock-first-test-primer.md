---
schema_version: 3
title: Fake vs Mock 첫 테스트 프라이머
concept_id: software-engineering/fake-vs-mock-first-test-primer
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 89
mission_ids:
- missions/roomescape
- missions/baseball
- missions/shopping-cart
review_feedback_tags:
- first-failing-test-choice
- fake-vs-mock-boundary
- repository-vs-notifier-test-double
aliases:
- fake vs mock first test
- first failing test fake mock
- 처음 mock fake 뭐부터
- service refactor first test
- mock vs fake beginner
- fake repository first refactor
- 왜 fake 먼저
- when to use mock
- 처음 테스트 더블 헷갈려
- what is fake vs mock
- small service refactor test
- test double basics
symptoms:
- 첫 failing test를 짜려는데 fake로 시작할지 mock으로 시작할지 기준이 없어요
- repository는 fake를 쓰라는데 notifier는 mock을 쓰라 해서 왜 다른지 헷갈려요
- 결과를 검증하는 테스트와 호출을 검증하는 테스트를 자꾸 섞어서 읽게 돼요
intents:
- definition
- comparison
- design
- troubleshooting
prerequisites:
- software-engineering/dummy-vs-stub-beginner-mini-card
- software-engineering/test-strategy-basics
next_docs:
- software-engineering/stub-vs-spy-first-test-primer
- software-engineering/repository-fake-design-guide
- software-engineering/outbound-notifier-mock-boundary-primer
- software-engineering/refactoring-first-failing-test-bridge
linked_paths:
- contents/software-engineering/dummy-vs-stub-beginner-mini-card.md
- contents/software-engineering/service-refactor-first-test-examples-pack.md
- contents/software-engineering/test-strategy-basics.md
- contents/software-engineering/stub-vs-spy-first-test-primer.md
- contents/software-engineering/refactoring-first-failing-test-bridge.md
- contents/software-engineering/outbound-notifier-mock-boundary-primer.md
- contents/software-engineering/repository-fake-design-guide.md
- contents/software-engineering/testing-strategy-and-test-doubles.md
- contents/spring/spring-testing-basics.md
confusable_with:
- software-engineering/stub-vs-spy-first-test-primer
- software-engineering/outbound-notifier-mock-boundary-primer
- software-engineering/repository-fake-design-guide
- software-engineering/testing-strategy-and-test-doubles
forbidden_neighbors:
- contents/software-engineering/stub-vs-spy-first-test-primer.md
- contents/software-engineering/outbound-notifier-mock-boundary-primer.md
expected_queries:
- 첫 failing test에서 fake를 먼저 잡아도 되는지 mock부터 검증해야 하는지 기준을 알려줘
- service 리팩토링 시작할 때 결과 중심 테스트와 호출 중심 테스트를 어떻게 구분해?
- repository는 fake가 자연스럽고 notifier는 mock이 자연스럽다는 말을 한 번에 이해하고 싶어
- 중복 저장 실패 같은 규칙은 fake로 보고 알림 전송은 mock으로 보는 이유가 뭐야?
- 테스트 더블을 처음 고를 때 fake와 mock을 선택하는 빠른 질문표가 필요해
contextual_chunk_prefix: |
  이 문서는 작은 service 리팩토링의 첫 failing test에서 fake와 mock 중
  무엇으로 시작할지 감을 잡는 beginner primer다. repository는 왜 fake가
  읽히고 notifier는 왜 mock이 읽히는지, 결과를 검증하는 질문과 호출을
  검증하는 질문을 어떻게 나누는지, 첫 테스트가 구현 순서 검증으로 새지
  않게 어떤 test double을 골라야 하는지 같은 학습자 질문을 입문 기준으로
  정리한다.
---

# Fake vs Mock 첫 테스트 프라이머

> 한 줄 요약: 작은 service 리팩토링에서 첫 failing test를 고를 때는 보통 `결과를 읽는 fake`로 시작하고, `호출 자체가 답`일 때만 mock으로 좁히면 초심자도 구현 순서에 덜 묶인다.

**난이도: 🟢 Beginner**

관련 문서:

- [Dummy vs Stub 초심자 미니 카드](./dummy-vs-stub-beginner-mini-card.md)
- [Service Refactor First-Test Examples Pack](./service-refactor-first-test-examples-pack.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [Stub vs Spy 첫 테스트 프라이머](./stub-vs-spy-first-test-primer.md)
- [리팩토링과 첫 failing test 연결 브리지](./refactoring-first-failing-test-bridge.md)
- [Outbound Notifier Mock Boundary Primer](./outbound-notifier-mock-boundary-primer.md)
- [Repository Fake Design Guide](./repository-fake-design-guide.md)
- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: fake vs mock first test, first failing test fake mock, 처음 mock fake 뭐부터, service refactor first test, mock vs fake beginner, fake repository first refactor, 왜 fake 먼저, when to use mock, 처음 테스트 더블 헷갈려, what is fake vs mock, small service refactor test, test double basics

## 핵심 개념

이 문서의 질문은 "`작은 service 리팩토링인데 첫 failing test를 fake로 시작할까, mock으로 시작할까?`"다. 초심자는 `mock`을 더 많이 들어서 먼저 집어 드는 경우가 많지만, 첫 테스트의 목적이 `호출 순서 확인`이 아니라 `규칙이 아직 같은 결과를 내는지`라면 fake가 더 읽기 쉽다.

만약 아직 "`고정값을 넣은 더블`도 전부 mock 아닌가요?" 단계라면 [Dummy vs Stub 초심자 미니 카드](./dummy-vs-stub-beginner-mini-card.md)부터 먼저 보고 오는 편이 더 안전하다. 이 문서는 그 다음 단계인 `결과를 읽는가, 호출을 읽는가`를 다룬다.

짧게 기준을 잡으면 이렇다. `저장 후 다시 읽었을 때 어떤 결과가 나와야 하나`를 묻는다면 fake가 먼저고, `이 알림을 정말 보냈나`, `이 포트를 호출했나`처럼 호출 자체가 비즈니스 결과라면 mock이 먼저다.

## 한눈에 보기

| 지금 확인하려는 질문 | 첫 선택 | 이유 |
|---|---|---|
| "`중복 주문번호면 생성이 실패하나?`" | fake repository | 상태와 결과를 한 흐름으로 읽을 수 있다 |
| "`재고 부족이면 상태가 바뀌지 않나?`" | fake repository | 저장 전후 결과를 구현 순서보다 먼저 본다 |
| "`알림을 정확히 1번 보냈나?`" | mock/spy | 호출 자체가 답이다 |
| "`결제 승인 포트를 실패 시 호출하지 않았나?`" | mock | 상호작용 유무가 핵심이다 |

- 처음이라 헷갈리면 `결과를 읽는가, 호출을 읽는가` 두 칸만 먼저 고르면 된다.
- 작은 service 리팩토링의 starter에서는 보통 결과 질문이 먼저라서 fake가 더 자주 등장한다.

## 작은 service 리팩토링에서 고르는 순서

| 순서 | 먼저 보는 것 | 여기서 멈추는 기준 |
|---|---|---|
| 1 | 이번 변경이 규칙 1개를 건드렸는지 적는다 | 예: `중복이면 실패`, `재고 부족이면 예외` |
| 2 | 그 규칙을 결과 문장으로 다시 쓴다 | "`무엇을 호출했나`"보다 "`어떤 결과가 나와야 하나`"가 먼저 말해진다 |
| 3 | 결과를 읽기 쉬우면 fake로 시작한다 | 저장/조회/중복 같은 계약을 한 테스트에서 재현할 수 있다 |
| 4 | 결과보다 호출 자체가 핵심이면 mock으로 바꾼다 | 알림, 이벤트 발행, 외부 승인 요청처럼 호출이 곧 일이다 |

이 순서를 쓰는 이유는 간단하다. 첫 failing test는 리팩토링을 안전하게 시작하려는 장치인데, mock을 너무 일찍 쓰면 테스트가 "`save()`를 먼저 불렀나`" 같은 구현 상세에 묶이기 쉽다. 반대로 fake는 "`이미 있으면 실패한다`" 같은 문장을 그대로 읽게 도와준다.

## 흔한 오해와 함정

- "`mock`이 더 진짜 테스트 아닌가요?"  
  아니다. mock은 더 강한 도구가 아니라, `호출을 검증하는 도구`에 가깝다. 질문이 결과 중심이면 오히려 과하다.
- "repository면 무조건 fake인가요?"  
  아니다. repository라도 `저장하지 않았는지` 자체가 중요한 장면이면 mock이 맞을 수 있다. 다만 beginner의 첫 리팩토링 테스트는 보통 중복, 저장 결과, 상태 전이처럼 결과 질문이 먼저다.
- "fake를 쓰면 DB처럼 완벽히 흉내 내야 하나요?"  
  아니다. fake는 JPA 복제품이 아니라, service가 기대하는 계약만 메모리에서 재현하면 충분하다.

## 실무에서 쓰는 모습

주문 service에서 "`중복 주문번호면 생성이 실패해야 한다`" 규칙을 분리한다고 해 보자. 이때 첫 failing test는 보통 fake repository 쪽이 읽기 쉽다.

```java
FakeOrderRepository repository = new FakeOrderRepository();
repository.save(existingOrder("ORDER-001"));

PlaceOrderService service = new PlaceOrderService(repository, notifier);

assertThatThrownBy(() -> service.place(command("ORDER-001")))
        .isInstanceOf(DuplicateOrderNumberException.class);
```

이 테스트가 먼저 설명하는 것은 "`중복이면 실패한다`"다. 반면 mock repository로 시작하면 "`existsByOrderNumber()`를 호출했고 `save()`는 안 불렀다`"가 먼저 눈에 들어온다.

반대로 "`주문이 성공하면 알림을 1번 보냈나`"를 확인하는 순간에는 mock/spy가 자연스럽다. 여기서는 결과 객체보다 `알림 전송 호출`이 바로 확인 대상이기 때문이다. 즉 같은 service 안에서도 repository 질문은 fake, notifier 질문은 mock으로 갈라질 수 있다. 이 notifier 쪽 경계를 한 단계 더 짧게 보면 [Outbound Notifier Mock Boundary Primer](./outbound-notifier-mock-boundary-primer.md)가 바로 이어진다.

## 더 깊이 가려면

- [테스트 전략 기초](./test-strategy-basics.md): 첫 failing test를 unit, slice, integration 중 어디에 둘지 먼저 고를 때
- [Stub vs Spy 첫 테스트 프라이머](./stub-vs-spy-first-test-primer.md): 고정 반환 더블과 호출 기록 더블을 첫 테스트에서 어떻게 가를지 더 짧게 보고 싶을 때
- [리팩토링과 첫 failing test 연결 브리지](./refactoring-first-failing-test-bridge.md): 리뷰 문장을 `질문 1개`로 줄이는 흐름이 먼저 필요할 때
- [Repository Fake Design Guide](./repository-fake-design-guide.md): fake repository를 JPA clone이 아니라 port 계약으로 설계하는 법까지 이어 볼 때
- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md): fake, stub, mock, spy 차이를 한 단계 더 정리하고 싶을 때

## 면접/시니어 질문 미리보기

| 질문 | 왜 묻나 | 핵심 답변 |
|---|---|---|
| "왜 첫 리팩토링 테스트에서 fake를 더 자주 권하나요?" | 결과 중심 테스트 감각을 본다 | 초심자에게는 구현 순서보다 규칙 결과를 먼저 읽게 해 주기 때문이다 |
| "mock이 더 좋은 경우는 언제인가요?" | 상호작용 검증 감각을 본다 | 호출 자체가 비즈니스 의미일 때다 |
| "fake가 너무 복잡해지면 무슨 신호인가요?" | 경계 설계 감각을 본다 | fake가 JPA나 프레임워크 세부까지 흉내 내기 시작하면 port 계약이 새고 있을 가능성이 크다 |

## 한 줄 정리

작은 service 리팩토링의 첫 failing test는 보통 `결과를 읽는 fake`, 호출 자체가 답인 장면에서만 `mock`으로 좁힌다고 기억하면 출발이 훨씬 단순해진다.
