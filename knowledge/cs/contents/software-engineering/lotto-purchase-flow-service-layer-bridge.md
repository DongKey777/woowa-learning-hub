---
schema_version: 3
title: 'lotto 여러 장 구매 흐름 ↔ Service 계층 브릿지'
concept_id: software-engineering/lotto-purchase-flow-service-layer-bridge
canonical: false
category: software-engineering
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- controller-logic-leak
- service-orchestration
- collection-wrapping
aliases:
- lotto 여러 장 구매 흐름
- 로또 구매 service 책임
- 로또 컨트롤러 반복문
- 구매 금액으로 로또 몇 장
- lotto service layer
symptoms:
- 컨트롤러에서 로또를 여러 장 만들어도 되나
- 구매 금액으로 몇 장 살지 어디서 계산해
- service가 얇아 보여서 반복문을 domain에 넣어야 하나
intents:
- mission_bridge
- design
prerequisites:
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
next_docs:
- software-engineering/service-layer-basics
- software-engineering/lotto-domain-invariant-bridge
- design-pattern/lotto-static-factory-bridge
linked_paths:
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/layered-architecture-basics.md
- contents/software-engineering/lotto-domain-invariant-bridge.md
- contents/design-pattern/lotto-static-factory-bridge.md
confusable_with:
- software-engineering/service-layer-basics
- software-engineering/lotto-domain-invariant-bridge
forbidden_neighbors:
- contents/software-engineering/roomescape-dao-vs-repository-bridge.md
expected_queries:
- 로또 구매 금액을 받아 여러 장 만드는 책임은 어디에 둬야 해?
- controller에서 반복문으로 로또 여러 장 생성하면 왜 지적받아?
- 로또 미션에서 service가 해야 하는 일은 정확히 뭐야?
- 일급 컬렉션 Lottos를 만들었는데 구매 흐름도 그 안에 넣어야 해?
- 구매 금액을 장수로 바꾸는 계산은 domain 규칙이야 service 흐름이야?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션에서 구매 금액을 장수로 바꾸고 여러 Lotto를
  생성해 묶는 흐름을 Service 계층과 잇는 mission_bridge다. 구매 금액으로 몇
  장 살지, controller 반복문이 티켓을 직접 만듦, service가 얇아 보여
  불안함, Lottos가 단순 List wrapper처럼 보임, 구매 유스케이스 순서를 어디에
  둘지, 한 장 규칙과 여러 장 흐름을 어떻게 나눌지 같은 학습자 표현을 service
  orchestration 감각으로 연결한다.
---

# lotto 여러 장 구매 흐름 ↔ Service 계층 브릿지

> 한 줄 요약: `구매 금액 -> 장수 계산 -> 번호 생성기 호출 -> 여러 Lotto 묶기`는 한 번의 유스케이스 흐름이라 Service가 조립하는 편이 자연스럽다. `Lotto`는 한 장의 유효성, `Lottos`는 여러 장을 다루는 도메인 의미를 맡고, Controller는 입력/출력만 남긴다.

## 미션 시나리오

lotto 미션에서 가장 자주 섞이는 지점은 "한 장 로또 규칙"과 "여러 장 구매 흐름"이다. 학습자는 보통 구매 금액을 입력받은 뒤 `money / 1000`으로 장수를 계산하고, 반복문으로 번호를 생성해 `List<Lotto>`를 만든다. 이 코드를 Controller에 두면 리뷰에서 "웹/입력 계층이 도메인 생성 흐름까지 안다"는 말을 듣기 쉽다.

반대로 이 반복문을 `Lotto` 생성자 안에 넣어도 책임이 섞인다. `Lotto`는 한 장의 번호 6개, 중복 없음, 범위 1-45 같은 불변식을 지키는 객체인데, 구매 장수 계산과 생성기 호출까지 알기 시작하면 "한 장의 규칙"보다 "구매 유스케이스"를 품게 된다.

## CS concept 매핑

Service 계층은 "입력을 받아 한 유스케이스를 끝까지 조립"하는 자리다. lotto 구매에서는 아래 흐름이 그 유스케이스다.

```java
int count = money / 1000;
List<Lotto> tickets = generator.generate(count);
return Lottos.from(tickets);
```

여기서 `count` 계산과 `generator` 호출 순서는 Service 책임이다. 반면 `Lotto.from(numbers)`는 각 티켓이 유효한지만 본다. `Lottos.from(tickets)`는 여러 장을 감싸며 총 장수, 수익률 계산 준비 같은 컬렉션 의미를 붙일 수 있다. 정리하면 Service는 "몇 장을 어떤 순서로 만들지", Domain은 "만들어진 한 장과 묶음이 유효한지"를 맡는다.

이 구분이 잡히면 "Service가 너무 얇은 것 아닌가?"라는 불안도 줄어든다. Service가 얇아 보이는 건 괜찮다. 중요한 건 Controller에 있던 흐름이 Service로 모이고, Domain이 자기 규칙만 정확히 지키는지다.

## 미션 PR 코멘트 패턴

- "Controller가 `Lotto`를 직접 여러 개 만들고 있네요. 입력 해석까지만 남기고 구매 흐름은 Service로 모아 보세요."
- "`Lotto`가 한 장 규칙보다 구매 금액 계산까지 품으면 책임이 커집니다. 구매 유스케이스와 티켓 규칙을 분리해 보세요."
- "`Lottos`가 단순 `List` wrapper라면 왜 필요한지 약합니다. 여러 장의 의미를 붙이거나, 아니면 Service에서 조립 책임만 두는지 기준을 분명히 하세요."

## 다음 학습

- Service 책임을 일반화해서 보려면 `service-layer-basics`
- 한 장 로또의 규칙 보장을 다시 보려면 `software-engineering/lotto-domain-invariant-bridge`
- 생성 경로 이름과 팩토리 의도를 정리하려면 `design-pattern/lotto-static-factory-bridge`
