---
schema_version: 3
title: 'lotto 번호 생성기 교체 ↔ Spring Bean 주입 브릿지'
concept_id: spring/lotto-number-generator-bean-injection-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- constructor-injection
- generator-bean-wiring
- test-double-injection
aliases:
- lotto 번호 생성기 빈 주입
- 로또 NumberGenerator 스프링 등록
- lotto 자동 번호 생성기 DI
- 로또 생성기 구현체 주입
- lotto 랜덤 생성기 bean 연결
symptoms:
- lotto 자동 번호 생성기를 테스트용 구현으로 바꿔 끼우고 싶은데 어디를 열어야 할지 모르겠어요
- NumberGenerator 인터페이스를 만들었는데 Spring에서 어떤 구현체가 들어가는지 감이 안 와요
- controller나 service에서 new RandomNumberGenerator()를 직접 만들지 말라는 리뷰를 받았어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/bean-di-basics
- design-pattern/lotto-manual-auto-number-generator-strategy-bridge
next_docs:
- spring/bean-di-basics
- spring/primary-qualifier-collection-injection
- design-pattern/lotto-manual-auto-number-generator-strategy-bridge
linked_paths:
- contents/spring/spring-bean-di-basics.md
- contents/spring/spring-primary-qualifier-collection-injection-decision-guide.md
- contents/spring/spring-bean-registration-path-decision-guide.md
- contents/design-pattern/lotto-manual-auto-number-generator-strategy-bridge.md
- contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
confusable_with:
- design-pattern/lotto-manual-auto-number-generator-strategy-bridge
- spring/primary-qualifier-collection-injection
- spring/bean-registration-path-decision-guide
forbidden_neighbors: []
expected_queries:
- 로또 미션 코드를 스프링으로 옮기면 번호 생성기는 service에서 직접 만들지 말고 어떻게 연결해?
- 테스트에서 고정 번호 생성기를 넣으려면 Spring DI 구조를 어디서 잡아야 해?
- NumberGenerator 인터페이스를 bean으로 등록했을 때 실제 구현체 선택은 누가 해?
- 로또 구매 서비스가 RandomNumberGenerator를 new 하는 구조가 왜 Spring스럽지 않다고 하나?
- 수동 생성기와 자동 생성기를 둘 다 두면 주입 충돌을 어떤 기준으로 풀어야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션에서 자동 번호 생성 seam을 Spring으로 옮길 때
  NumberGenerator 인터페이스, Random 기반 구현체, 테스트용 고정 구현체를
  Bean 주입으로 어떻게 연결하는지 설명하는 mission_bridge다. 로또 생성기를
  service에서 직접 new 하지 말라는 리뷰, 테스트 더블 생성기 교체, 같은 타입
  구현체가 둘일 때 주입 충돌, 생성 책임과 Bean wiring 분리 같은 학습자
  표현을 Spring DI와 constructor injection 관점으로 매핑한다.
---

# lotto 번호 생성기 교체 ↔ Spring Bean 주입 브릿지

## 한 줄 요약

> lotto에서 `NumberGenerator`를 분리했다면, Spring에서는 구매 서비스가 구현체를 직접 만들기보다 생성자 주입으로 받아서 "생성 규칙 교체"와 "구매 흐름 조립"을 나누는 편이 자연스럽다.

## 미션 시나리오

lotto 미션에서 자동 번호 생성을 분리하고 나면 보통 `NumberGenerator` 인터페이스와 `RandomNumberGenerator` 구현체가 생긴다. 콘솔 과제 단계에서는 `new RandomNumberGenerator()`를 서비스나 애플리케이션 진입점에서 직접 만들어도 크게 이상해 보이지 않는다. 그런데 이 구조를 Spring 애플리케이션으로 옮기면 리뷰 포인트가 달라진다.

멘토가 자주 보는 냄새는 `LottoService`가 구매 흐름을 조립하면서 동시에 생성기 선택까지 직접 하는 모습이다. 이러면 테스트에서 고정 번호 생성기를 넣고 싶을 때 서비스 코드를 건드려야 하고, "왜 지금은 랜덤이고 테스트에서는 고정인가" 같은 정책 차이도 클래스 내부 분기로 숨어 버린다. 학습자 입장에서는 전략 분리를 했는데도 교체 지점이 체감되지 않는 순간이다.

## CS concept 매핑

Spring으로 읽으면 `NumberGenerator`는 "서비스가 필요로 하는 협력 객체의 계약"이고, Bean 등록은 "그 계약에 어떤 구현을 꽂을지 애플리케이션이 결정하는 자리"다. 그래서 `LottoService`는 "`몇 장을 살지 계산하고 생성기를 호출한다"까지만 알고, `RandomNumberGenerator`를 어떻게 만들지는 컨테이너에 맡기는 편이 맞다.

짧게 쓰면 구조는 이렇다. `@Service`인 구매 서비스가 `NumberGenerator`를 생성자로 받고, 운영에서는 랜덤 구현을 Bean으로 등록하고, 테스트에서는 고정 구현을 넣는다. 구현이 하나면 생성자 주입만으로 충분하고, 자동/수동 생성기처럼 같은 타입 Bean이 둘이면 `@Qualifier`나 별도 router가 필요한지 다음 단계에서 판단한다. 여기서 핵심은 "전략 분리"와 "Bean wiring"이 같은 일이 아니라는 점이다. 전자는 책임 분리이고, 후자는 그 책임을 런타임에 어떻게 연결할지의 문제다.

## 미션 PR 코멘트 패턴

- "`LottoService`가 `new RandomNumberGenerator()`를 직접 호출하면 테스트 seam이 다시 닫힙니다. 생성기 선택은 주입으로 빼 보세요."
- "전략 인터페이스를 만든 이유가 구현 교체라면, 교체 지점은 서비스 내부 `if`보다 Bean wiring 쪽에 있어야 합니다."
- "운영 구현과 테스트 구현이 둘 다 생길 수 있으니, 지금은 단일 Bean인지 같은 타입 후보가 여러 개인지도 같이 설명해 주세요."
- "구매 흐름을 조립하는 책임과 생성기 인스턴스를 만드는 책임이 섞이면 Spring DI를 도입한 이점이 약해집니다."

## 다음 학습

- Bean 등록과 생성자 주입의 큰 그림을 다시 잡으려면 `spring-bean-di-basics`
- 같은 타입 생성기 Bean이 둘일 때 `@Primary`와 `@Qualifier`를 어떻게 나눌지 보려면 `spring/primary-qualifier-collection-injection`
- lotto에서 왜 생성기를 전략 객체로 먼저 분리하는지 복습하려면 `design-pattern/lotto-manual-auto-number-generator-strategy-bridge`
- 구매 서비스가 생성기를 호출하는 책임 자체를 다시 보려면 `software-engineering/lotto-purchase-flow-service-layer-bridge`
