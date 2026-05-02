# Design Pattern (디자인 패턴)

> 한 줄 요약: 처음 배우는 입구에서는 `전략 / 팩토리 / 레지스트리 / repository`를 한꺼번에 외우지 말고, **행동 교체 / 생성 / 등록 lookup / 저장-조회 경계** 네 질문으로 먼저 자르면 된다.

**난이도: 🟢 Beginner**

이 README는 design-pattern 카테고리의 **입문용 길찾기 표지판**이다. 처음에는 패턴 이름을 넓게 수집하기보다, 지금 코드가 어떤 질문에 답하는지만 먼저 잡는 편이 안전하다.

관련 문서:

- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- [상속보다 조합 기초](./composition-over-inheritance-basics.md)
- [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)
- [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md)
- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
- [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md)

retrieval-anchor-keywords: design pattern readme, design pattern beginner route, pattern basics, strategy vs factory vs registry, repository boundary basics, 처음 design pattern, 처음 배우는데 pattern, 헷갈리는 pattern naming, factory selector registry, strategy map registry, repository read model, what is design pattern basics

## 빠른 시작

처음 읽을 때는 아래 순서만 잡으면 된다.

1. [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)로 캡슐화, 다형성, 역할 분리를 먼저 맞춘다.
2. [상속보다 조합 기초](./composition-over-inheritance-basics.md)로 "부모 클래스부터 만들까, 조합을 기본값으로 둘까"를 정리한다.
3. [객체지향 디자인 패턴 기초](./object-oriented-design-pattern-basics.md)에서 전략, 템플릿 메소드, 팩토리의 큰 그림만 본다.

이 단계에서는 deep dive보다 "지금 코드가 생성 문제인지, 행동 교체 문제인지"만 분리해도 충분하다.

## 4갈래 판단표

| 지금 코드가 답하는 질문 | 먼저 붙일 이름 | 첫 문서 |
|---|---|---|
| 어떻게 처리할지 규칙을 바꿔 끼우나 | strategy | [전략 패턴 기초](./strategy-pattern-basics.md) |
| 지금 새 객체를 만들고 조립하나 | factory | [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md) |
| 이미 등록된 것을 key로 찾기만 하나 | registry | [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md) |
| aggregate를 저장/복원하나, 화면 조회를 조합하나 | repository / read model | [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md) |

짧게 외우면 **행동 교체는 strategy, 생성은 factory, 등록 lookup은 registry, 저장-조회 분리는 repository/read model**이다.

## 네이밍이 헷갈릴 때

`Factory`, `Selector`, `Resolver`, `Registry`가 섞여 보이면 이름보다 책임을 먼저 본다.

- 새 객체를 조립하면 `Factory`
- raw 입력을 뜻으로 풀면 `Resolver`
- 이미 준비된 후보 중 하나를 고르면 `Selector`
- 등록된 객체나 정보를 key로 찾으면 `Registry`

`Map<Key, Strategy>`처럼 겉모양이 비슷해도, 꺼낸 뒤 같은 행동을 실행하면 strategy selection 쪽 질문이 더 중심일 수 있다. 이 경계는 [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)에서 짧게 정리하고, service locator 냄새까지 보고 싶을 때만 [Injected Registry vs Service Locator Checklist](./injected-registry-vs-service-locator-checklist.md)로 내려가면 된다.

## Repository 경계가 헷갈릴 때

처음에는 repository를 "DB 관련 코드를 다 넣는 곳"으로 이해하기 쉽지만, beginner 기준으로는 아래 두 줄만 먼저 잡으면 된다.

- aggregate를 저장하고 다시 꺼내는 책임이면 repository
- 화면 목록, 검색, 조합이 중심이면 read model 또는 query service

즉 `orderRepository.save(order)`와 `orderQueryService.search(condition)`는 같은 저장소 기술을 써도 질문이 다르다. 더 깊은 CQRS, freshness, projection 운영 이야기는 이 README의 중심이 아니고, 필요할 때만 [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)과 [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)로 이어가면 된다.

## 더 깊게 갈 때

입문에서 막히는 지점을 넘겼다면 그다음에는 문서를 역할별로 내려가면 된다.

- 템플릿 메소드 vs 전략 경계: [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- 팩토리 이름 남용 점검: [Factory Misnaming Checklist: create 없는 `*Factory`를 리뷰에서 빨리 가르기](./factory-misnaming-checklist.md)
- factory/selector/resolver 첫 분기: [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md)
- registry/lookup/service locator 첫 분기: [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
- strategy map과 registry 경계: [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)
- registry와 wiring 분리: [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
- repository/read model follow-up: [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
- read model freshness 운영: [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md) -> [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
- backend/DDD 쪽 확장: [Design Pattern / Read Model + Database + System Design](../../rag/cross-domain-bridge-map.md#design-pattern--read-model--database--system-design)

운영, cutover, incident 대응 성격의 문서는 여기서 바로 읽기보다 위 entrypoint를 통과한 뒤 필요한 주제만 따라가는 편이 beginner-first 동선에 맞다.

## 자주 헷갈리는 한 문장

- "런타임에 고르니까 다 factory 아닌가요?"
  아니다. 런타임 선택은 selector나 strategy selection에서도 일어난다. 새로 만들 때만 factory를 먼저 붙인다.
- "`Map<Key, Strategy>`면 그냥 registry 아닌가요?"
  lookup 도구는 registry처럼 보여도, 핵심이 행동 교체면 strategy selection이 중심일 수 있다.
- "repository가 조회도 다 하면 편하지 않나요?"
  처음엔 편해 보여도 저장과 화면 조합 질문이 섞인다. beginner 단계에서는 저장/조회 경계가 다르다는 것만 먼저 기억하면 된다.

## 한 줄 정리

입문 단계에서는 패턴 이름을 넓게 외우기보다, **행동 교체 / 생성 / 등록 lookup / 저장-조회 경계** 네 질문으로 먼저 자르는 것이 가장 안전하다.
