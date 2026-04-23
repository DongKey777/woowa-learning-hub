# Design Pattern (디자인 패턴)

**난이도: 🔴 Advanced**

디자인 패턴(Design Pattern)은 **소프트웨어 설계의 효율성을 높이는 최선의 해결책** 중 하나다. 소프트웨어 최적화에 대한 관심이 높아지면서 소프트웨어 아키텍트는 객체 생성과 코드 구조, 객체 간의 상호작용 등을 반드시 설계 단계부터 생각해야 한다. 디자인 패턴을 잘 활용하면 소프트웨어 **유지보수 비용이 줄어들고 코드 재사용성이 증가하며** 쉽게 확장할 수 있는 구조가 될 것이다. 재사용할 수 있는 모듈간 독립적인 프레임워크를 제공하는 일이 현대 소프트웨어 개발의 핵심이다.

> retrieval-anchor-keywords: design pattern readme, ddd pattern catalog, design pattern playbook, template method framework example, servlet lifecycle template method, HttpServlet service doGet doPost, OncePerRequestFilter doFilterInternal, onceperrequestfilter template method, spring filter vs handlerinterceptor, template method vs chain of responsibility spring, xUnit setUp tearDown, junit 5 callback model, junit5 beforeeach aftereach, junit extension not template method, BeforeEachCallback AfterEachCallback, ParameterResolver InvocationInterceptor, template hook smell, hook method explosion, before after hook explosion, fragile base class, shouldNotFilter smell, OncePerRequestFilter shouldNotFilter overuse, setup teardown override smell, base test fixture smell, unsafe extension point, projection playbook, rollout playbook, cutover playbook, read model, projection, design pattern / read model + database + system design route, projection readiness checklist, projection rebuild evidence packet, rebuild readiness packet, cutover approval packet, rollback proof packet, strict read fallback contract, strict screen fallback, strict pagination fallback contract, strict list fallback, strict list canary metrics, strict list rollback trigger, strict list canary dashboard, list endpoint fallback boundaries, first page only fallback, first page fallback boundary, later page rejection contract, next page continuation contract, legacy cursor rejection contract, legacy cursor reissue api surface, reissue response shape, reject response shape, pagination restart envelope, page1 restart response, clear cursor and restart, cursor invalidation fallback, mixed cursor prevention, single cursor world chain, fallback ownership, fallback routing, fallback rate contract, fallback capacity contract, fallback headroom contract, fallback circuit breaker, fallback burst budget, strict fallback degraded ux contract, degraded response contract, processing state contract, pending state contract, retry-after contract, strict fallback user visible guarantees, pinned legacy chain risk budget, accept pinned chain ttl, pinned chain capacity reserve, pinned chain rollback expiry, session pinning strict read, expected version strict read, watermark gated strict read, cross screen read your writes, strict screen routing window, tail catch-up, parity signoff, cutover approval, projection error budget, repository boundary, cqrs, saga coordinator, outbox relay, freshness slo, projection lag, old data after write, budget burn, backfill cutover, cutover guardrail, canary promotion threshold, canary dwell time, rollback trigger threshold, page depth rollback trigger, reissue restart success rate, rollback window exit criteria, old projection decommission, rollback command verification, latent bug audit cadence, projection canary cohort selection, low risk cohort, representative cohort, strict path cohort, query fingerprint bucket selection, poison event quarantine, replay retry matrix, partial replay failure, projection replay signoff, replay observability dashboard, replay gap count, quarantine growth alert, verified watermark drift, retry budget burn, normalized query fingerprint, pagination parity sampling, pagination parity packet schema, fingerprint bucket, cursor verdict pair, continuity outcome, cursor version parity, cursor compatibility sampling, legacy cursor reuse canary, requested emitted cursor version, cursor reuse allowlist, two page continuity canary, read model migration pagination parity, next page continuity, stable sort parity, normalization version rollout, cache namespace bump, reason code compatibility, cursor rollback packet, rollback cursor ttl, rollback reject reason code, rollback restart reason code, client restart after rollback, paginated cutover canary threshold, first-page parity floor, second-page continuity floor, cursor-verdict sample floor, pagination stage gate, pattern bridge, anti corruption layer, provider sandbox, contract test, hexagonal architecture, ports and adapters architecture, boundary architecture route, hexagonal acl route, anti corruption adapter layering, port adapter boundary, state pattern enough, state machine library vs workflow engine, state pattern vs workflow engine, in process state machine, durable workflow orchestration, bridge strategy factory runtime selection, behavior axis vs creation axis, runtime policy selection not factory, policy selector vs factory, strategy vs factory beginner, bridge vs strategy vs factory, strategy vs policy selector naming, selector resolver registry strategy vs factory, factory naming smell, resolver vs factory beginner, chooses not creates, lookup not creation, bean name vs domain key lookup, spring bean name handler map, domain key registry, bean name leak, container naming leak, injected registry vs service locator checklist, explicit constructor injection registry, hidden dependency lookup checklist, service locator drift, strategy registry service locator drift, strategy lookup helper smell, strategy selector service locator smell, global strategy lookup smell, ApplicationContext getBean handler smell, factory vs registry in di collection injection, spring list injection vs map injection, injected list and map patterns, wiring lookup creation separation, di collection injection beginner, request model chooser, request dto record vs builder, query object record vs builder, static factory for request dto, small dto stay record
> retrieval-anchor-keywords: template method basics route, template method basics first, hook method beginner route, abstract step beginner route, hook method vs abstract step beginner, 처음 배우는데 hook method, 처음 배우는데 훅 메서드, 처음 배우는데 abstract step, 처음 배우는데 추상 단계, 훅 메서드 기초, 추상 단계 기초, hook은 선택 빈칸, abstract step은 필수 빈칸, 템플릿 메소드 기초 먼저, 부모가 흐름을 쥔다 큰 그림

## 빠른 탐색

이 `README`는 고전 GoF primer와 backend/DDD pattern catalog가 함께 있는 **navigator 문서**다.
mixed catalog에서 `[playbook]` 라벨은 rollout / cutover 절차를 먼저 읽어야 하는 step-oriented 문서라는 뜻이고, 라벨이 없는 항목은 패턴/경계 중심 `deep dive`다.

- 고전 패턴 primer부터 읽고 싶다면:
  - `객체지향 디자인 패턴 기초`
  - `상속보다 조합 기초` -> `템플릿 메소드 패턴 기초` -> `템플릿 메소드 vs 전략` -> `템플릿 메소드`  ← "부모가 흐름을 쥔다", `hook method`, `abstract step`을 처음 배우는 질문을 basics로 먼저 보내는 beginner route
  - `전략`
  - `Strategy vs Policy Selector Naming`
  - `Strategy vs Function`
  - `Registry Primer`  ← `lookup table`/`resolver`/`router`/`service locator`를 처음 배우는 검색어에서 registry와 anti-pattern 경로를 먼저 가르는 bridge
  - `Strategy Registry vs Service Locator Drift Note`  ← 전략 lookup helper가 좁은 selector인지, 전역 service locator 냄새인지 빠르게 확인하는 bridge
  - `주입된 Handler Map에서 Registry vs Factory`  ← `List<Handler>`/`Map<String, Handler>`를 wiring, lookup, creation으로 바로 분리하는 Spring-style beginner bridge
  - `Bean Name vs Domain Key Lookup`
  - `Injected Registry vs Service Locator Checklist`
  - `Factory와 DI 컨테이너 Wiring`
  - `Request Scope vs Plain Request Objects`  ← Spring `@RequestScope` bean과 `@RequestBody` DTO / caller-built command를 생명주기와 데이터 생성 책임으로 분리
  - `싱글톤`
  - `팩토리`
  - `빌더`
  - `옵저버`
  - `Observer Lifecycle Hygiene`
  - `프레임워크 안의 템플릿 메소드`
  - `JUnit 5 Callback Model vs Classic xUnit Template Skeleton`  ← `@BeforeEach`/`@AfterEach`를 classic `setUp`/`tearDown`처럼 어디까지 볼 수 있는지 정리
  - `Template Hook Smells`  ← `beforeX`/`afterX`/`onError`뿐 아니라 `shouldNotFilter`, classic `setUp`/`tearDown`가 안전 구간을 넘는 순간까지 바로 연결한다
- backend / DDD catalog로 바로 들어가려면:
  - `Aggregate Boundary vs Transaction Boundary`
  - `Repository Boundary: Aggregate Persistence vs Read Model`
  - `Saga / Coordinator`
  - `Outbox Relay and Idempotent Publisher`
  - `Bounded Context Relationship Patterns`
- [Design Pattern / Read Model + Database + System Design](../../rag/cross-domain-bridge-map.md#design-pattern--read-model--database--system-design) route로 바로 들어가려면:
  - `old data after write`, `저장했는데 옛값` 같은 freshness phrase는 `Read Model Staleness and Read-Your-Writes`부터 본다
  - `Query Object and Search Criteria`
  - `Search Normalization and Query`  ← normalized input parity / sample key
  - `[playbook] Normalization Version Rollout Playbook`  ← cache namespace bump / cursor invalidation / reason-code parity
  - `Cursor Pagination and Sort Stability`  ← 2-page continuity / cursor-version parity
  - `Cursor and Pagination Parity During Read-Model Migration`  ← stable sort audit / legacy cursor verdict / next-page parity
  - `Cursor Compatibility Sampling for Cutover`  ← legacy cursor reuse allowlist / requested-emitted version matrix / 2-page canary sample floor
  - `Legacy Cursor Reissue API Surface`  ← `REISSUE`/`REJECT` response envelope / served-page reset / client page1 restart contract
  - `Cursor Rollback Packet`  ← rollback-time cursor TTL / reason code / client page1 restart contract
  - `Dual-Read Pagination Parity Sample Packet Schema`  ← canonical fingerprint bucket / cursor verdict pair / continuity outcome
  - `Read Model Staleness and Read-Your-Writes`
  - `Session Pinning vs Version-Gated Strict Reads`  ← cross-screen strict window / actor-scoped pinning / expectedVersion vs watermark choice
  - `Strict Read Fallback Contracts`
  - `Strict Pagination Fallback Contracts`  ← list endpoint fallback boundaries / first-page fallback / later-page reject-reissue / mixed-cursor prevention
  - `Strict List Canary Metrics and Rollback Triggers`  ← page-depth split dashboard / freeze vs hard rollback / fallback source saturation
  - `Pinned Legacy Chain Risk Budget`  ← `ACCEPT` / pinned-chain fallback justify gate, TTL, reserve, rollback zero-ttl
  - `Fallback Capacity and Headroom Contracts`  ← write-side / old projection reserve, burst, breaker
  - `Strict Fallback Degraded UX Contracts`  ← processing vs pending / retry-after / user-visible guarantees
  - `Read Model Cutover Guardrails`
  - `Canary Promotion Thresholds for Projection Cutover`  ← generic promotion ladder + paginated list stage gates for first-page parity / second-page continuity / cursor verdict floors
  - `Rollback Window Exit Criteria`  ← old projection decommission / audit cadence / rollback-command verification
  - `Projection Freshness SLO Pattern`
- projection 운영 SLO/전환 묶음을 보고 싶다면:
  - `Search Normalization and Query`  ← cutover input parity / fingerprint bucket
  - `[playbook] Normalization Version Rollout Playbook`  ← normalization version bump / cache namespace / client-visible reason code compatibility
  - `Cursor Pagination and Sort Stability`  ← pagination continuity / legacy cursor verdict
  - `Cursor and Pagination Parity During Read-Model Migration`  ← projection replacement list-endpoint cutover packet
  - `Cursor Compatibility Sampling for Cutover`  ← pagination-specific canary checks for legacy reuse / version matrix / page-chain quotas
  - `Legacy Cursor Reissue API Surface`  ← restart-based compatibility에서 response-shape와 clear-cursor contract를 고정
  - `Cursor Rollback Packet`  ← rollback bridge TTL / cursor cutoff / restart-based recovery packet
  - `Dual-Read Pagination Parity Sample Packet Schema`  ← canonical compare packet for bucket/verdict/outcome rollups
  - `Strict Read Fallback Contracts`
  - `Strict Pagination Fallback Contracts`  ← strict list boundary matrix / page1-only vs later-page rejection / mixed-cursor prevention
  - `Strict List Canary Metrics and Rollback Triggers`  ← page-depth metric family / cursor verdict drift / freeze vs hard rollback
  - `Pinned Legacy Chain Risk Budget`  ← `ACCEPT` pinned chain을 남겨도 되는 조건과 TTL / reserve / rollback 제약
  - `Fallback Capacity and Headroom Contracts`  ← strict fallback reserve / breaker-open / 2차 장애 방지
  - `Strict Fallback Degraded UX Contracts`  ← degraded response envelope / processing-pending split / retry-after backoff
  - `Projection Freshness SLO Pattern`
  - `Projection Lag Budgeting Pattern`
  - `Read Model Cutover Guardrails`
  - `Projection Canary Cohort Selection`  ← low-risk / representative / strict-path stage routing, fingerprint bucket ladder
  - `Canary Promotion Thresholds for Projection Cutover`  ← stage별 sample/dwell/rollback criteria + paginated list first-page parity / second-page continuity / cursor-verdict floor
  - `Rollback Window Exit Criteria`  ← primary 이후 old projection decommission, audit cadence, latent-bug / rollback-command exit gate
  - `Projection Rebuild, Backfill, and Cutover Pattern`  ← tail catch-up / parity / error-budget readiness checklist 포함
  - `Projection Rebuild Evidence Packet`  ← rebuild readiness / cutover approval / rollback proof를 한 packet으로 묶는 canonical artifact
  - `Poison Event and Replay Failure Handling in Projection Rebuilds`  ← quarantine / retry / verified-watermark sign-off packet
  - `Event Contract Drift Triage for Rebuilds`  ← legacy schema drift / upcaster gap / semantic incompatibility를 갈라 replay resume gate를 고정
  - `Projection Replay Observability and Alerting Pattern`  ← replay gap dashboard / quarantine growth / verified watermark drift / retry burn alert
- workflow/operator ownership 묶음을 보고 싶다면:
  - `State Pattern vs State Machine Library vs Workflow Engine`
  - `Human Approval and Manual Review Workflow`
  - `Escalation, Reassignment, and Queue Ownership`
  - `Workflow Owner vs Participant Context`
  - `Process Manager Deadlines and Timeouts`
- hexagonal / ACL boundary architecture route를 먼저 잡고 싶다면:
  - `Ports and Adapters vs GoF 패턴`
  - `Hexagonal Ports`
  - `Anti-Corruption Adapter Layering`
  - `Facade as Anti-Corruption Seam`
  - `Anti-Corruption Layer Operational Pattern`
  - `Adapter`, `퍼사드 vs 어댑터 vs 프록시`는 wrapper-level 비교가 필요할 때만 뒤에 붙인다
- 외부 provider 경계/ACL 운영을 묶어서 보고 싶다면:
  - `Anti-Corruption Contract Test`
  - `Anti-Corruption Rollout and Provider Sandbox`
  - `Anti-Corruption Layer Operational Pattern`
  - `Facade as Anti-Corruption Seam`
  - `Tolerant Reader for Event Contracts`
- provider abstraction / interface translation / boundary seam 혼동을 바로 가르려면:
  - `Bridge Pattern: 저장소와 제공자를 분리하는 추상화`
  - `Adapter (어댑터)`
  - `Facade as Anti-Corruption Seam`
  - `퍼사드 vs 어댑터 vs 프록시`
  - `Ports and Adapters vs GoF 패턴`
  - `Adapter Chaining Smells`
- 패턴 이름보다 선택 기준이 먼저 필요하면:
  - `실전 패턴 선택 가이드`
  - `Composition over Inheritance`
  - `Command Pattern, Undo, Queue`
- 문서 역할이 헷갈리면:
  - [Navigation Taxonomy](../../rag/navigation-taxonomy.md)
  - [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)

## 🟢 Beginner 진입 문서 (새로 추가)

로드맵 4단계에서 처음 디자인 패턴을 공부하는 분이라면 아래 beginner 문서를 먼저 읽는다.

- [싱글톤 패턴 기초](singleton-basics.md) — 인스턴스 하나 공유의 이점과 함정, Spring DI와의 차이
- [전략 패턴 기초](strategy-pattern-basics.md) — if-else 대신 구현을 교체하는 구조, 호출자가 전략 객체를 고르는 큰 그림, 부모 클래스 상속 vs 객체 주입 첫 갈림길
- [Strategy vs Policy Selector Naming](strategy-policy-selector-naming.md) — `*Factory`를 붙이기 전에 `*Selector`, `*Resolver`, `*Registry`, `*Strategy`가 선택/해석/조회/행동 의도를 더 잘 말하는지 확인하는 naming primer
- [Strategy Map vs Registry Primer](strategy-map-vs-registry-primer.md) — 같은 `Map<Key, ...>`라도 행동 교체용 전략 컬렉션인지, 단순 keyed lookup용 registry인지 빠르게 자르는 비교 노트
- [Strategy Registry vs Service Locator Drift Note](strategy-registry-vs-service-locator-drift.md) — 전략 lookup helper가 한 역할의 selector에 머무는지, 전역 service locator로 미끄러지는지 확인하는 beginner bridge
- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](registry-primer-lookup-table-resolver-router-service-locator.md) — `lookup table`, `resolver`, `router`, `service locator`를 한 장에서 구분하고 registry-pattern / service-locator anti-pattern으로 안내하는 beginner bridge
- [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](registry-vs-factory-injected-handler-maps.md) — `List<Handler>`/`Map<String, Handler>`를 봤을 때 wiring, registry lookup, factory creation을 먼저 분리하게 돕는 Spring-style beginner primer
- [Bean Name vs Domain Key Lookup](bean-name-vs-domain-key-lookup.md) — Spring이 주입한 `Map<String, Handler>`의 bean name key를 결제 수단/상태/이벤트 타입 같은 domain key registry로 감싸야 하는 순간
- [Injected Registry vs Service Locator Checklist](injected-registry-vs-service-locator-checklist.md) — 생성자에 보이는 좁은 registry와 메서드 안의 숨은 전역 lookup을 코드 리뷰에서 바로 가르는 beginner 체크리스트
- [데코레이터와 프록시 기초](decorator-proxy-basics.md) — 기능 추가 래퍼 vs 접근 제어 대리자, Spring AOP 연결
- [어댑터 패턴 기초](adapter-basics.md) — 인터페이스 불일치 번역기, 외부 SDK·레거시 연결 실무
- [상속보다 조합 기초](composition-over-inheritance-basics.md) — is-a vs has-a, 상속을 좁게 허용하고 조합/전략으로 넘어가는 첫 갈림길
- [팩토리 패턴 기초](factory-basics.md) — 생성 책임 분리, 정적 팩토리 메서드, 호출자와 구현 클래스 디커플링
- [빌더 패턴 기초](builder-pattern-basics.md) — 인자 많은 객체 조립, 메서드 체이닝, Lombok @Builder 연결
- [요청 객체 생성 vs DI 컨테이너](request-object-creation-vs-di-container.md) — request DTO, command, value object를 bean wiring이 아니라 constructor/static factory/builder 경계로 읽는 입문 브리지
- [Request Scope vs Plain Request Objects](request-scope-vs-plain-request-objects.md) — Spring `@RequestScope` bean과 binder-created DTO, caller-built command를 섞지 않게 생명주기와 데이터 생성 책임을 먼저 분리하는 beginner bridge
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](record-vs-builder-request-model-chooser.md) — 작은 request/query object를 기본 `record`로 두고, 정규화는 static factory, 옵션 조합 증가는 builder로 자르는 beginner chooser
- [옵저버 패턴 기초](observer-basics.md) — 상태 변화 알림, Subject/Observer 역할 분리, Spring EventListener 연결
- [템플릿 메소드 패턴 기초](template-method-basics.md) — 부모가 흐름을 쥐는 큰 그림, 알고리즘 뼈대 고정, `abstract step`은 필수 빈칸이고 `hook method`는 선택 빈칸이라는 첫 분기
- [커맨드 패턴 기초](command-pattern-basics.md) — 요청 객체화, 지연 실행·큐·undo/redo 입문

---

## 고전 패턴 primer

### GoF 디자인 패턴
- [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](object-oriented-design-pattern-basics.md) - beginner route, 다섯 기본 패턴을 먼저 잡고 adapter/composition/command primer로 이어지는 입문 가이드
- [전략 (Strategy)](strategy-pattern.md) - runtime에 구현을 고르는 주체가 호출자/설정인지, `Context`는 실행만 맡는지, 부모 클래스 상속보다 전략 객체 주입이 자연스러운 순간과 작은 함수·단순 분기·전략 폭발 경계를 어디서 그을지 정리한 primer
- [Strategy vs Policy Selector Naming](strategy-policy-selector-naming.md) - `*Factory`가 생성 책임을 암시해 오해를 만들 때 `*Selector`, `*Resolver`, `*Registry`, `*Strategy`로 의도를 나누는 beginner naming bridge
- [Strategy vs Function](strategy-vs-function-chooser.md) - lambda/작은 함수 vs full Strategy type chooser, 짧고 stateless한 계산식이면 함수, 이름 있는 규칙·협력 객체·독립 테스트 경계가 필요하면 Strategy
- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](registry-primer-lookup-table-resolver-router-service-locator.md) - `lookup table`은 registry로, `service locator`는 anti-pattern으로 보내고 resolver/router 주변 용어를 먼저 자르는 beginner entrypoint
- [Strategy Map vs Registry Primer](strategy-map-vs-registry-primer.md) - 같은 `Map<Key, ...>` 모양이더라도 "행동 교체"가 핵심이면 strategy, "이름표 lookup"이 핵심이면 registry라고 30초 안에 자르는 beginner comparison note
- [Strategy Registry vs Service Locator Drift Note](strategy-registry-vs-service-locator-drift.md) - `Map<Key, Strategy>` lookup helper가 좁은 selector에서 전역 service locator로 변하는 신호를 자르는 beginner smell note
- [Strategy vs State vs Policy Object](strategy-vs-state-vs-policy-object.md) - payment method / payment status / refund rule처럼 헷갈리는 축을 한 장에서 구분하는 비교 문서
- [템플릿 메소드 vs 전략](template-method-vs-strategy.md) - "상속 vs 객체 주입", "부모 클래스냐 전략 객체냐" 같은 첫 질문을 "부모가 흐름을 쥔다 vs 호출자가 전략을 고른다"로 바로 번역해 주는 beginner chooser
- [데코레이터 vs 프록시 (Decorator vs Proxy)](decorator-vs-proxy.md)
- [Adapter (어댑터)](adapter.md) - legacy SDK / 외부 인터페이스를 기존 포트에 맞추는 번역기 primer
- [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](bridge-storage-provider-abstractions.md) - storage/provider처럼 독립적으로 변하는 두 축을 분리해 조합 폭발을 막는 구조
- [런타임 선택에서 Bridge vs Strategy vs Factory](bridge-strategy-vs-factory-runtime-selection.md) - policy selection을 `*Factory`로 부르기 쉬운 지점을 행동 선택 / 객체 생성 / 두 축 분리로 잘라 주는 beginner bridge note
- [퍼사드 vs 어댑터 vs 프록시](facade-vs-adapter-vs-proxy.md) - wrapper 비교: 단순화 vs 인터페이스 번역 vs 호출 제어
- [Adapter Chaining Smells](adapter-chaining-smells.md) - adapter stack이 translation pipeline smell로 변하는 지점을 정리한 경고 문서
- [싱글톤 (Singleton)](singleton.md)
  - [싱글톤 Java 구현 방법](singleton-java.md)
- [팩토리 (Factory)](factory.md) - beginner deep dive, 언제 생성 책임을 숨기고 언제 그냥 `new`/정적 팩토리/빌더/레지스트리를 택해야 하는지 정리
- [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](constructor-vs-static-factory-vs-factory-pattern.md) - Java `of`/`from`/`valueOf`/`parse`/`getInstance` naming guide와 같은 타입 생성 vs 구현 선택 factory 구분용 companion
- [요청 객체 생성 vs DI 컨테이너](request-object-creation-vs-di-container.md) - request DTO, command, value object를 constructor/static factory/builder로 두고 service/client/repository만 bean wiring에 남기는 beginner bridge
- [Request Scope vs Plain Request Objects](request-scope-vs-plain-request-objects.md) - Spring `@RequestScope` bean과 `@RequestBody` DTO / caller-built command를 생명주기와 데이터 생성 책임으로 분리하는 beginner bridge
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](record-vs-builder-request-model-chooser.md) - small request/query model은 `record`, 이름 있는 정규화는 static factory, 옵션 조합 폭발은 builder로 자르는 beginner chooser
- [빌더 (Builder)](builder-pattern.md)
- [Factory vs Abstract Factory vs Builder](factory-vs-abstract-factory-vs-builder.md)
- [Factory Switch Registry Smell](factory-switch-registry-smell.md) - switch-heavy factory를 registry-backed factory로 옮길 때 selector / registry / factory 경계를 다시 나누고 service locator drift를 피하는 smell guide
- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](registry-primer-lookup-table-resolver-router-service-locator.md) - `lookup table`, `resolver`, `router`, `service locator`를 한 장에서 나누고 registry-pattern과 service-locator anti-pattern으로 라우팅하는 beginner bridge
- [Registry Pattern: 객체를 찾는 이름표와 저장소](registry-pattern.md) - lookup table의 역할, factory와의 차이, switch factory refactor 이후에도 registry를 좁은 lookup으로 유지하는 기준
- [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](registry-vs-factory-injected-handler-maps.md) - `Map<String, Handler>`/`List<Handler>` 주입을 factory로 오해할 때 wiring, lookup, creation을 세 단계로 끊어 보는 beginner primer
- [Bean Name vs Domain Key Lookup](bean-name-vs-domain-key-lookup.md) - Spring이 주입한 `Map<String, Handler>`의 bean name key를 서비스 분기 기준으로 흘리지 않고 domain-key registry로 감싸는 beginner bridge
- [Injected Registry vs Service Locator Checklist](injected-registry-vs-service-locator-checklist.md) - handler registry가 명시적 constructor injection에 머무는지, `ApplicationContext.getBean` 같은 hidden dependency lookup으로 미끄러졌는지 확인하는 beginner checklist
- [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](service-locator-antipattern.md) - registry refactor가 전역 lookup으로 미끄러질 때 무엇이 깨지는지 확인하는 companion anti-pattern
- [옵저버 (Observer)](observer.md) - beginner deep dive, observer vs direct call vs Pub/Sub decision table, ordering/failure boundary caveats
- [옵저버, Pub/Sub, ApplicationEvent](observer-pubsub-application-events.md)
- [Mediator vs Observer vs Pub/Sub](mediator-vs-observer-vs-pubsub.md) - 같은 프로세스에서 coordination / notification / brokered messaging을 가르는 비교 문서
- [Observer Lifecycle Hygiene](observer-lifecycle-hygiene.md) - unsubscribe, duplicate-registration 방지, UI/plugin/long-lived process의 listener ownership과 teardown discipline
- [Spring `@EventListener` vs `@TransactionalEventListener`: Timing, Ordering, Rollback](spring-eventlistener-vs-transactionaleventlistener-timing.md) - Spring 내부 옵저버에서 commit/rollback timing, `@Order`, `fallbackExecution`이 어떻게 의미를 바꾸는지 정리한 bridge 문서
- [템플릿 메소드 (Template Method)](template-method.md) - [템플릿 메소드 패턴 기초](template-method-basics.md) 다음에 보는 deep dive, abstract step vs hook method, 상속을 써도 되는 좁은 경우와 언제 쓰지 말아야 하는지 포함
- [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](chain-of-responsibility-filters-interceptors.md) - Servlet `Filter`, Spring MVC `HandlerInterceptor`, short-circuit 흐름을 request chain 관점에서 읽는 primer
- [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](template-method-framework-lifecycle-examples.md) - basics를 다시 풀지 않고 `HttpServlet`, `OncePerRequestFilter`, classic xUnit fixture에서 skeleton이 어디 있는지 짚고, base class 상속 vs 분리된 policy/component 경계까지 이어 주는 companion 문서
- [JUnit 5 Callback Model vs Classic xUnit Template Skeleton](junit5-callback-model-vs-classic-xunit-template-skeleton.md) - `@BeforeEach`/`@AfterEach`, `BeforeEachCallback`, `InvocationInterceptor`가 왜 classic xUnit의 단일 template skeleton과 같지 않은지 정리한 짧은 보조 문서
- [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](template-method-vs-filter-interceptor-chain.md) - 같은 요청 경로에서 chain participant와 template wrapper를 30초 안에 구분하는 focused comparison note
- [Template Hook Smells](template-hook-smells.md) - `beforeX`/`afterX`/`cleanup` hook explosion뿐 아니라 `OncePerRequestFilter#shouldNotFilter`, classic xUnit `setUp`/`tearDown`가 unsafe extension point로 커지는 순간을 점검하는 advanced smell guide
- [Composition over Inheritance](composition-over-inheritance-practical.md) - 상속이 아니라 변경 축 기준으로 조합을 고르는 primer
- [Command Pattern, Undo, Queue](command-pattern-undo-queue.md) - undo/history/job queue까지 이어지는 command 객체 primer
- [실전 패턴 선택 가이드](pattern-selection.md) - survey / decision guide, change-axis confusion을 adapter/composition/command primer까지 직접 연결

### 아키텍처 패턴
- [MVC (Model-View-Controller)](mvc-python.md)

## 백엔드 / DDD catalog

아래 mixed catalog에서는 `[playbook]` 라벨로 step-oriented rollout 문서를 deep dive 패턴과 구분했다.

### DDD / Backend 설계 패턴 언어
- [Aggregate Boundary vs Transaction Boundary](aggregate-boundary-vs-transaction-boundary.md)
- [Aggregate Root vs Unit of Work](aggregate-root-vs-unit-of-work.md)
- [Aggregate Version and Optimistic Concurrency Pattern](aggregate-version-optimistic-concurrency-pattern.md)
- [Unit of Work Pattern: 트랜잭션 경계 안에서 변경을 모으기](unit-of-work-pattern.md)
- [Repository Boundary: Aggregate Persistence vs Read Model](repository-boundary-aggregate-vs-read-model.md)
- [Read Model Staleness and Read-Your-Writes](read-model-staleness-read-your-writes.md)
- [Session Pinning vs Version-Gated Strict Reads](session-pinning-vs-version-gated-strict-reads.md)
- [Strict Read Fallback Contracts](strict-read-fallback-contracts.md)
- [Strict Pagination Fallback Contracts](strict-pagination-fallback-contracts.md) - list endpoint fallback boundary split: first page, later-page reject/reissue, mixed-cursor prevention
- [Strict List Canary Metrics and Rollback Triggers](strict-list-canary-metrics-rollback-triggers.md) - page-depth metric family, cursor verdict drift, freeze vs hard rollback packet
- [Pinned Legacy Chain Risk Budget](pinned-legacy-chain-risk-budget.md) - `ACCEPT` / pinned-chain fallback justification, short TTL, dedicated reserve, rollback zero-ttl
- [Fallback Capacity and Headroom Contracts](fallback-capacity-and-headroom-contracts.md) - strict fallback reserve, burst, breaker, degraded UX 계약
- [Strict Fallback Degraded UX Contracts](strict-fallback-degraded-ux-contracts.md) - processing/pending state split, retry-after policy, user-visible guarantees when fallback is constrained
- [Projection Freshness SLO Pattern](projection-freshness-slo-pattern.md)
- [Projection Lag Budgeting Pattern](projection-lag-budgeting-pattern.md)
- [Projection Rebuild, Backfill, and Cutover Pattern](projection-rebuild-backfill-cutover-pattern.md) - cutover approval용 readiness checklist 포함
- [Projection Rebuild Evidence Packet](projection-rebuild-evidence-packet.md) - rebuild readiness, parity artifacts, rollback proof를 묶는 canonical approval packet
- [Poison Event and Replay Failure Handling in Projection Rebuilds](projection-rebuild-poison-event-replay-failure-handling.md) - poison event quarantine, partial replay gap closure, sign-off rules
- [Projection Replay Observability and Alerting Pattern](projection-replay-observability-alerting-pattern.md) - replay gap dashboard, quarantine growth, verified watermark drift, retry burn alert contract
- [Read Model Cutover Guardrails](read-model-cutover-guardrails.md)
- [Projection Canary Cohort Selection](projection-canary-cohort-selection.md) - low-risk, representative, strict-path stage cohort 선택과 fingerprint bucket ladder
- [Canary Promotion Thresholds for Projection Cutover](canary-promotion-thresholds-projection-cutover.md) - readiness 이후 stage별 sample/dwell/rollback 승격 기준과 paginated list parity/verdict stage gate
- [Rollback Window Exit Criteria](projection-rollback-window-exit-criteria.md) - primary 이후 old projection decommission, audit cadence, latent-bug sweep, rollback-command verification
- [Transaction Script vs Rich Domain Model](transaction-script-vs-rich-domain-model.md)
- [Aggregate Invariant Guard Pattern](aggregate-invariant-guard-pattern.md)
- [Invariant-Preserving Command Model](invariant-preserving-command-model.md)
- [Reference Other Aggregates by ID](aggregate-reference-by-id.md)
- [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](state-pattern-workflow-payment.md) - payment lifecycle, workflow transition guard, invalid transition 방지
- [State Pattern vs State Machine Library vs Workflow Engine](state-machine-library-vs-state-pattern.md) - local aggregate transition, in-process transition table, durable workflow runtime를 가르는 decision guide
- [Policy Object Pattern: 도메인 결정을 객체로 만든다](policy-object-pattern.md) - refund/fee/approval decision을 reason code, fee, 후속 액션까지 담는 규칙 객체
- [Specification Pattern: 조건식을 조합 가능한 도메인 규칙으로 만들기](specification-pattern.md) - boolean 명세 조합과 policy object로 넘어가는 rich decision 경계를 함께 정리
- [Semantic Lock and Pending State Pattern](semantic-lock-pending-state-pattern.md)
- [Domain Events vs Integration Events](domain-events-vs-integration-events.md)
- [Domain Event Translation Pipeline](domain-event-translation-pipeline.md)
- [Event Upcaster Compatibility Patterns](event-upcaster-compatibility-patterns.md)
- [Event Contract Drift Triage for Rebuilds](event-contract-drift-triage-rebuilds.md) - legacy schema drift, upcaster coverage gap, semantic incompatibility를 분리해 replay 재개 조건을 고정
- [Snapshot Versioning and Compatibility Pattern](snapshot-versioning-compatibility-pattern.md)
- [Tolerant Reader for Event Contracts](tolerant-reader-event-contract-pattern.md)
- [Anti-Corruption Contract Test Pattern](anti-corruption-contract-test-pattern.md)
- [Anti-Corruption Rollout and Provider Sandbox Pattern](anti-corruption-rollout-provider-sandbox-pattern.md)
- [Outbox Relay and Idempotent Publisher](outbox-relay-idempotent-publisher.md)
- [Idempotent Consumer and Projection Dedup Pattern](idempotent-consumer-projection-dedup-pattern.md)
- [Anti-Corruption Layer Operational Pattern](anti-corruption-layer-operational-pattern.md)
- [Specification vs Query Service Boundary](specification-vs-query-service-boundary.md)
- [Query Object and Search Criteria Pattern](query-object-search-criteria-pattern.md)
- [Search Normalization and Query Pattern](search-normalization-query-pattern.md)
- `[playbook]` [Normalization Version Rollout Playbook](normalization-version-rollout-playbook.md) - cache namespace bump, cursor invalidation, public reason-code compatibility during cutover
- [Cursor Pagination and Sort Stability Pattern](cursor-pagination-sort-stability-pattern.md)
- [Cursor and Pagination Parity During Read-Model Migration](cursor-pagination-parity-read-model-migration.md)
- [Cursor Compatibility Sampling for Cutover](cursor-compatibility-sampling-cutover.md) - legacy cursor reuse allowlist, requested/emitted version matrix, two-page continuity sample floor
- [Legacy Cursor Reissue API Surface](legacy-cursor-reissue-api-surface.md) - `REISSUE`/`REJECT` response envelope, served-page reset, client page1 restart contract
- [Cursor Rollback Packet](cursor-rollback-packet.md) - rollback-time cursor version TTL, reject/reissue reason code, client page1 restart contract
- [Dual-Read Pagination Parity Sample Packet Schema](dual-read-pagination-parity-sample-packet-schema.md) - canonical packet for fingerprint bucket, cursor verdict pair, continuity outcome
- [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](saga-coordinator-pattern-language.md)
- [Orchestration vs Choreography Failure Handling](orchestration-vs-choreography-failure-handling.md)
- [Process Manager vs Saga Coordinator](process-manager-vs-saga-coordinator.md)
- [Process Manager Deadlines and Timeouts](process-manager-deadlines-timeouts.md)
- [Process Manager State Store and Recovery Pattern](process-manager-state-store-recovery.md)
- [Human Approval and Manual Review Workflow Pattern](human-approval-manual-review-workflow-pattern.md)
- [Escalation, Reassignment, and Queue Ownership Pattern](escalation-reassignment-queue-ownership-pattern.md)
- [Workflow Owner vs Participant Context](workflow-owner-vs-participant-context.md)
- [Reservation, Hold, and Expiry as a Consistency Seam](reservation-hold-expiry-consistency-seam.md)
- [Compensation vs Reconciliation Pattern](compensation-vs-reconciliation-pattern.md)
- [Bounded Context Relationship Patterns](bounded-context-relationship-patterns.md)
- [Ports and Adapters vs GoF 패턴: 경계에서 책임을 자르는 법](ports-and-adapters-vs-classic-patterns.md) - hexagonal boundary architecture와 classic adapter를 분리해 읽는 비교 문서
- [Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](hexagonal-ports-pattern-language.md) - inbound/outbound contract naming과 포트 역할에 집중하는 보조 문서
- [Facade as Anti-Corruption Seam](facade-anti-corruption-seam.md) - facade가 단순 진입점을 넘어 boundary translation seam이 되는 경우
- [Anti-Corruption Adapter Layering](anti-corruption-adapter-layering.md) - port, adapter, facade, translator 역할을 분리하는 layered ACL guide

## 카테고리 브리지

### 가까운 카테고리 브리지
- 트랜잭션 경계와 락 해석은 [Database: Transaction Boundary, Isolation, and Locking Decision Framework](../database/transaction-boundary-isolation-locking-decision-framework.md), [Database: 트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)로 이어 보면 좋다.
- repository/read model/projection 군은 [Database: Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md), [System Design: Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md), [System Design: Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)과 붙여서 보면 더 실전적이다.
- read model freshness를 감으로 운영하지 않으려면 [Database: Incremental Summary Table Refresh and Watermark Discipline](../database/incremental-summary-table-refresh-watermark.md), [Database: Summary Drift Detection, Invalidation, and Bounded Rebuild](../database/summary-drift-detection-bounded-rebuild.md), [System Design: Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)을 같이 보면 좋다.
- outbox/idempotency/event 계약 진화는 [Database: CDC, Debezium, Outbox, Binlog](../database/cdc-debezium-outbox-binlog.md), [Database: 멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md), [Language: JSON `null`, Missing Field, Unknown Property, and Schema Evolution](../language/java/json-null-missing-unknown-field-schema-evolution.md)을 같이 보면 연결이 빨라진다.

## 안티패턴 보조 문서

#### [부록] 피해야 하는 개발 습관
- [안티 패턴](anti-pattern.md)
- [God Object / Spaghetti / Golden Hammer](god-object-spaghetti-golden-hammer.md) - 큰 서비스/매니저 객체, 스파게티 흐름, 황금 망치를 한 묶음으로 읽는 smell entrypoint
- [전략 폭발 냄새](strategy-explosion-smell.md) - if/else를 지웠는데 전략 클래스와 팩토리 조합이 폭증할 때, config table / lambda / simple branching으로 다시 줄이는 체크리스트
- [Template Hook Smells](template-hook-smells.md) - abstract base class의 `before/after` hook, `shouldNotFilter`, `setUp`/`tearDown`가 커지며 상속 구조가 단단해지는 경우

---

## 질의응답

> 아직 없습니다.
