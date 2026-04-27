# Design Pattern (디자인 패턴)

> 한 줄 요약: 처음 배우는데는 `객체지향 핵심 원리 -> 상속보다 조합 -> 패턴 primer -> bridge -> deep dive` 순서로 들어오고, 템플릿 메소드는 primer에서 큰 그림을 먼저 잡은 뒤 framework/deep 문서로 내려간다.

**난이도: 🔴 Advanced**

디자인 패턴(Design Pattern)은 **소프트웨어 설계의 효율성을 높이는 최선의 해결책** 중 하나다. 소프트웨어 최적화에 대한 관심이 높아지면서 소프트웨어 아키텍트는 객체 생성과 코드 구조, 객체 간의 상호작용 등을 반드시 설계 단계부터 생각해야 한다. 디자인 패턴을 잘 활용하면 소프트웨어 **유지보수 비용이 줄어들고 코드 재사용성이 증가하며** 쉽게 확장할 수 있는 구조가 될 것이다. 재사용할 수 있는 모듈간 독립적인 프레임워크를 제공하는 일이 현대 소프트웨어 개발의 핵심이다.

> retrieval-anchor-keywords: design pattern readme, ddd pattern catalog, design pattern playbook, template method primer route, template method primer first, template method primer to deep dive, template method beginner order, template method framework example, servlet lifecycle template method, HttpServlet service doGet doPost, OncePerRequestFilter doFilterInternal, onceperrequestfilter template method, spring filter vs handlerinterceptor, template method vs chain of responsibility spring, xUnit setUp tearDown, junit 5 callback model, junit5 beforeeach aftereach, junit extension not template method, BeforeEachCallback AfterEachCallback, ParameterResolver InvocationInterceptor, template hook smell, hook method explosion, before after hook explosion, fragile base class, shouldNotFilter smell, OncePerRequestFilter shouldNotFilter overuse, setup teardown override smell, base test fixture smell, unsafe extension point, projection playbook, rollout playbook, cutover playbook, read model, projection, design pattern / read model + database + system design route, projection readiness checklist, projection rebuild evidence packet, rebuild readiness packet, cutover approval packet, rollback proof packet, strict read fallback contract, strict screen fallback, strict pagination fallback contract, strict list fallback, strict list canary metrics, strict list rollback trigger, strict list canary dashboard, list endpoint fallback boundaries, first page only fallback, first page fallback boundary, later page rejection contract, next page continuation contract, legacy cursor rejection contract, legacy cursor reissue api surface, reissue response shape, reject response shape, pagination restart envelope, page1 restart response, clear cursor and restart, cursor invalidation fallback, mixed cursor prevention, single cursor world chain, fallback ownership, fallback routing, fallback rate contract, fallback capacity contract, fallback headroom contract, fallback circuit breaker, fallback burst budget, strict fallback degraded ux contract, degraded response contract, processing state contract, pending state contract, retry-after contract, strict fallback user visible guarantees, pinned legacy chain risk budget, accept pinned chain ttl, pinned chain capacity reserve, pinned chain rollback expiry, session pinning strict read, expected version strict read, watermark gated strict read, cross screen read your writes, strict screen routing window, tail catch-up, parity signoff, cutover approval, projection error budget, repository boundary, cqrs, saga coordinator, outbox relay, freshness slo, projection lag, old data after write, budget burn, backfill cutover, cutover guardrail, canary promotion threshold, canary dwell time, rollback trigger threshold, page depth rollback trigger, reissue restart success rate, rollback window exit criteria, old projection decommission, rollback command verification, latent bug audit cadence, projection canary cohort selection, low risk cohort, representative cohort, strict path cohort, query fingerprint bucket selection, poison event quarantine, replay retry matrix, partial replay failure, projection replay signoff, replay observability dashboard, replay gap count, quarantine growth alert, verified watermark drift, retry budget burn, normalized query fingerprint, pagination parity sampling, pagination parity packet schema, fingerprint bucket, cursor verdict pair, continuity outcome, cursor version parity, cursor compatibility sampling, legacy cursor reuse canary, requested emitted cursor version, cursor reuse allowlist, two page continuity canary, read model migration pagination parity, next page continuity, stable sort parity, normalization version rollout, cache namespace bump, reason code compatibility, cursor rollback packet, rollback cursor ttl, rollback reject reason code, rollback restart reason code, client restart after rollback, paginated cutover canary threshold, first-page parity floor, second-page continuity floor, cursor-verdict sample floor, pagination stage gate, pattern bridge, anti corruption layer, provider sandbox, contract test, hexagonal architecture, ports and adapters architecture, boundary architecture route, hexagonal acl route, anti corruption adapter layering, port adapter boundary, state pattern enough, state machine library vs workflow engine, state pattern vs workflow engine, in process state machine, durable workflow orchestration, bridge strategy factory runtime selection, behavior axis vs creation axis, runtime policy selection not factory, policy selector vs factory, strategy vs factory beginner, bridge vs strategy vs factory, strategy vs policy selector naming, selector resolver registry strategy vs factory, factory naming smell, resolver vs factory beginner, chooses not creates, lookup not creation, bean name vs domain key lookup, spring bean name handler map, domain key registry, bean name leak, container naming leak, channel to bean name confusion, channel -> bean name, channel bean mapping spring, notification channel handler registry, channel key leak, 처음 배우는데 채널 분기 큰 그림, 채널 분기 기초, channel registry 언제 쓰는지, injected registry vs service locator checklist, explicit constructor injection registry, hidden dependency lookup checklist, service locator drift, strategy registry service locator drift, strategy lookup helper smell, strategy selector service locator smell, global strategy lookup smell, ApplicationContext getBean handler smell, factory vs registry in di collection injection, spring list injection vs map injection, injected list and map patterns, wiring lookup creation separation, di collection injection beginner, request model chooser, request dto record vs builder, query object record vs builder, static factory for request dto, small dto stay record

관련 문서:

- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- [상속보다 조합 기초](./composition-over-inheritance-basics.md)
- [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)
> retrieval-anchor-keywords: template method basics route, template basics primer route, template method primer route, template method basics first, hook method beginner route, abstract step beginner route, hook method primer, abstract step primer, hook method vs abstract step beginner, 처음 배우는데 hook method, 처음 배우는데 훅 메서드, 처음 배우는데 abstract step, 처음 배우는데 추상 단계, 훅 메서드 기초, 추상 단계 기초, hook은 선택 빈칸, abstract step은 필수 빈칸, 필수 슬롯 선택 슬롯, 템플릿 메소드 3질문 체크리스트, 템플릿 메소드 1분 판별 카드, 템플릿 메소드 기초 먼저, 부모가 흐름을 쥔다 큰 그림, hook 하나 추가할까 전략으로 뺄까, hook 추가 vs 전략 분리, 처음 배우는데 hook vs strategy, 추상 클래스냐 인터페이스냐, 추상 클래스냐 인터페이스+주입이냐, abstract class or interface with DI, abstract class vs injected strategy, 결제 전략, payment strategy, 리포트 템플릿, report template method, report export template, 검증 규칙 교체, validation rule replacement, validation policy swap, beginner primer template, quick check skeleton, confusion box skeleton, 초보자 프라이머 템플릿, quick-check 템플릿, confusion box 템플릿, 자주 헷갈리는 포인트 박스
> retrieval-anchor-keywords: plugin registry boundary, plugin registry vs service locator, plugin lookup narrow registry, injected plugin registry, plugin locator smell, plugin manager hidden dependency, plugin extension point registry, plugin registry beginner
> retrieval-anchor-keywords: router vs selector naming, dispatcher vs selector naming, handler mapping vs factory, request dispatch naming, router dispatcher handlermapping beginner, spring dispatcher servlet handler mapping naming
> retrieval-anchor-keywords: factory selector resolver beginner, factory vs selector vs resolver, factory selector resolver 차이, 생성 vs 선택 네이밍, 생성 책임 vs 선택 책임, factory 이름 언제 쓰는지, selector 이름 언제 쓰는지, resolver 이름 언제 쓰는지, 처음 배우는데 factory selector resolver, factory selector resolver 큰 그림, factory selector resolver 기초, create 없는 factory
> retrieval-anchor-keywords: beginner entrypoint, beginner bridge, beginner deep dive, beginner route labels, pattern entrypoint, pattern bridge, pattern deep dive, design pattern beginner route, design pattern 첫 진입, 초보자 entrypoint 패턴, 초보자 브리지 문서, 초보자 심화 문서, entrypoint primer, beginner navigation labels, 객체지향 핵심 원리 다음 디자인 패턴, 디자인 패턴 처음 배우는데 순서, 디자인 패턴 큰 그림 기초 순서, 객체지향 핵심 원리 -> 상속보다 조합 -> 패턴 기초, 객체지향 핵심 원리 상속보다 조합 패턴 기초, object oriented core principles composition over inheritance pattern basics, oop beginner route design pattern, beginner oop route to design patterns, 처음 배우는데 객체지향 다음 패턴 뭐 읽지, 상속보다 조합 다음 패턴 기초, design README beginner route

## 빠른 탐색

이 `README`는 고전 GoF primer와 backend/DDD pattern catalog가 함께 있는 **navigator 문서**다.
mixed catalog에서 `[playbook]` 라벨은 rollout / cutover 절차를 먼저 읽어야 하는 step-oriented 문서라는 뜻이고, 라벨이 없는 항목은 패턴/경계 중심 `deep dive`다.
beginner 3단계 묶음의 순서 라벨은 `1단계: ...`, `2단계: ...`, `3단계: ...`처럼 `숫자 + 단계 + 콜론 + 짧은 행동 문구` 형식으로 통일한다.
처음 배우는데 큰 그림이 필요하면 README 수준의 기본 진입 경로는 **객체지향 핵심 원리 -> 상속보다 조합 -> 패턴 기초**다.

## 고전 패턴 빠른 진입

- 고전 패턴 primer부터 읽고 싶다면:
  - `1단계: 객체지향 핵심 원리`  ← [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)에서 클래스/객체/캡슐화/상속/다형성 큰 그림을 먼저 맞춘다
  - `2단계: 상속보다 조합`  ← [상속보다 조합 기초](composition-over-inheritance-basics.md)에서 부모 클래스부터 만들지, 조합을 기본값으로 둘지 먼저 자른다
  - `3단계: 패턴 기초`  ← [객체지향 디자인 패턴 기초](object-oriented-design-pattern-basics.md)에서 `조합 -> 템플릿 메소드 -> 전략 -> 어댑터` 순서로 내려간다
  - `상속보다 조합 기초` -> `추상 클래스냐 인터페이스+주입이냐 브리지` -> `템플릿 메소드 패턴 기초` -> `템플릿 메소드 vs 전략` -> `템플릿 메소드`  ← "처음 배우는데 `abstract class`면 다 템플릿 메소드인가?" 오해를 30초 3문장 반례 카드로 먼저 끊고, `hook method`/`abstract step`은 1분 3질문 카드로, `hook 추가 vs 전략 분리`는 3문항 미니 체크로, `리포트 템플릿`/`검증 규칙 교체` 같은 생활 검색어는 비교 카드로 바로 번역해 이어가는 beginner route
  - `객체지향 디자인 패턴 기초` -> `상속보다 조합 기초` -> `템플릿 메소드 패턴 기초` -> `전략 패턴 기초` -> `어댑터 패턴 기초`  ← pattern 이름을 넓게 아는 것보다 "조합을 기본값으로 두고, 흐름 고정/규칙 교체/외부 번역을 차례로 자르는" beginner route map이며, `결제 전략` 같은 검색어도 여기서 바로 strategy 쪽으로 연결된다
  - `Beginner Primer 작성 템플릿`  ← 새 입문 문서를 만들 때 "큰 그림 -> 비교표 -> Quick-Check -> Confusion Box -> 다음 읽기" 순서를 재사용하는 스켈레톤

## 네이밍 / 레지스트리 초입

- 처음 배우는데 `factory`, `selector`, `registry`가 섞이면:
  - `전략`
  - `Factory vs Selector vs Resolver (처음 배우는 큰 그림)`  ← creation-vs-selection 질문에서 `Factory`/`Selector`/`Resolver`를 먼저 가르고, naming/factory primer로 안전하게 넘기는 beginner entrypoint
  - `Strategy vs Policy Selector Naming`
  - `Policy Object Naming Primer`  ← rule object가 실행 방식인지, 판정 규칙인지, 조건 명세인지 먼저 나눠서 `Policy` / `Strategy` / `Specification` / `Factory`를 헷갈리지 않게 잡는 beginner bridge
  - `Map-backed 클래스 네이밍 체크리스트`  ← 같은 `Map<Key, ...>`라도 입력 해석 / 후보 선택 / 등록 조회 / 새 객체 생성을 `Resolver` / `Selector` / `Registry` / `Factory`로 바로 자르는 beginner guide
  - `Strategy vs Function`
  - `Registry Primer`  ← `lookup table`/`resolver`/`router`/`service locator`를 처음 배우는 검색어에서 registry와 anti-pattern 경로를 먼저 가르는 bridge

## Registry / Service Locator 초입

- registry, handler map, locator drift를 자르고 싶다면:
  - `Request Dispatch Naming`  ← request dispatch boundary에서는 `Router` / `HandlerMapping` / `Dispatcher`가 `Selector` / `Factory`보다 왜 더 정확한지 짧게 자르는 bridge
  - `Strategy Registry vs Service Locator Drift Note`  ← 전략 lookup helper가 좁은 selector인지, 전역 service locator 냄새인지 빠르게 확인하는 bridge
  - `Policy Object vs Strategy Map`  ← 커지는 `Map<Key, Strategy>`가 behavior selector로 남아도 되는지, rule 자체를 policy object shape로 올려야 하는지 가르는 beginner bridge
  - `주입된 Handler Map에서 Registry vs Factory`  ← `List<Handler>`/`Map<String, Handler>`를 wiring, lookup, creation으로 나누고 registry bootstrap의 duplicate/missing key fail-fast까지 묶어 보는 Spring-style beginner bridge
  - `Handler Registry Test Shape`  ← `supports()` 기반 registry를 Spring 없이 unit test로 자르고, fake registry consumer test와 Spring context locator test를 어떻게 분리할지 바로 잡는 beginner primer
  - `Bean Name vs Domain Key Lookup`
  - `Injected Registry vs Service Locator Checklist`
  - `Plugin Registry Boundary Primer`  ← plugin lookup이 host-owned registry에 머무는지, app-wide `PluginManager`/locator drift로 커지는지 가르는 beginner bridge
  - `Factory와 DI 컨테이너 Wiring`
  - `Request Scope vs Plain Request Objects`  ← Spring `@RequestScope` bean과 `@RequestBody` DTO / caller-built command를 생명주기와 데이터 생성 책임으로 분리

## 기타 고전 패턴 / 후속 문서

- 고전 패턴 이름별 deep dive나 후속 bridge를 찾는다면:
  - `싱글톤`
  - `팩토리`
  - `빌더`
  - `옵저버`
  - `Observer Lifecycle Hygiene`
  - `프레임워크 안의 템플릿 메소드`  ← 학습 순서 라벨: `basics -> framework examples -> deep dive`에서 `framework examples` 단계
  - `템플릿 메소드`  ← 같은 묶음의 `deep dive` 본문. `프레임워크 안의 템플릿 메소드`로 skeleton 감을 잡은 뒤, 본문에서 `abstract step`/`hook method`와 확장 맥락까지 바로 이어서 본다
  - `JUnit 5 Callback Model vs Classic xUnit Template Skeleton`  ← `@BeforeEach`/`@AfterEach`를 classic `setUp`/`tearDown`처럼 어디까지 볼 수 있는지, `@ExtendWith`가 끼면 왜 순서 추론이 더 어려워지는지도 1개 비교표로 이어 주는 beginner bridge
  - `Template Hook Smells`  ← 학습 순서 라벨 `basics -> framework examples -> deep dive` 다음의 심화 smell 점검용 문서다. `hook` 1~2개 설명을 넘어서 `beforeX/afterX/cleanup` 같은 슬롯 이름이 계속 늘 때만 들어간다

## Backend / DDD 빠른 진입

- backend / DDD catalog로 바로 들어가려면:
  - `Aggregate Boundary vs Transaction Boundary`
  - `Repository Boundary: Aggregate Persistence vs Read Model`
  - `Saga / Coordinator`
  - `Outbox Relay and Idempotent Publisher`
  - `Bounded Context Relationship Patterns`

## Read Model / Projection 빠른 진입

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

## Strict Read / Cutover 빠른 진입

- strict read, fallback, cutover 기준을 바로 보고 싶다면:
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

## Projection 운영 / 전환 묶음

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

## Projection rebuild / observability

- rebuild, lag, canary, replay 관점으로 내려가려면:
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

## Workflow / Ownership 빠른 진입

- workflow/operator ownership 묶음을 보고 싶다면:
  - `State Pattern vs State Machine Library vs Workflow Engine`
  - `Human Approval and Manual Review Workflow`
  - `Escalation, Reassignment, and Queue Ownership`
  - `Workflow Owner vs Participant Context`
  - `Process Manager Deadlines and Timeouts`

## Hexagonal / ACL 빠른 진입

- hexagonal / ACL boundary architecture route를 먼저 잡고 싶다면:
  - `Ports and Adapters vs GoF 패턴`
  - `Hexagonal Ports`
  - `Anti-Corruption Adapter Layering`
  - `Facade as Anti-Corruption Seam`
  - `Anti-Corruption Layer Operational Pattern`
  - `Adapter`, `퍼사드 vs 어댑터 vs 프록시`는 wrapper-level 비교가 필요할 때만 뒤에 붙인다

## Provider 경계 / ACL 운영

- 외부 provider 경계/ACL 운영을 묶어서 보고 싶다면:
  - `Anti-Corruption Contract Test`
  - `Anti-Corruption Rollout and Provider Sandbox`
  - `Anti-Corruption Layer Operational Pattern`
  - `Facade as Anti-Corruption Seam`
  - `Tolerant Reader for Event Contracts`

## Provider 추상화 / 인터페이스 번역

- provider abstraction / interface translation / boundary seam 혼동을 바로 가르려면:
  - `Bridge Pattern: 저장소와 제공자를 분리하는 추상화`
  - `Adapter (어댑터)`
  - `Facade as Anti-Corruption Seam`
  - `퍼사드 vs 어댑터 vs 프록시`
  - `Ports and Adapters vs GoF 패턴`
  - `Adapter Chaining Smells`

## 선택 기준부터 보는 진입

- 패턴 이름보다 선택 기준이 먼저 필요하면:
  - `실전 패턴 선택 가이드`
  - `Composition over Inheritance`
  - `Command Pattern, Undo, Queue`

## 문서 역할 가이드

- 문서 역할이 헷갈리면:
  - [Navigation Taxonomy](../../rag/navigation-taxonomy.md)
  - [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)

## 🟢 Beginner 진입 문서 (새로 추가)

로드맵 4단계에서 처음 디자인 패턴을 공부하는 분이라면 아래 beginner 문서를 먼저 읽는다.

## Beginner 시작 순서

| 단계 | 큰 그림 | 먼저 볼 문서 | 왜 이 순서가 안전한가 |
|---|---|---|---|
| 1단계 | 객체지향 핵심 원리 | [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) | 패턴 이름보다 먼저 클래스/객체/캡슐화/상속/다형성 큰 그림을 맞춘다 |
| 2단계 | 상속보다 조합 | [상속보다 조합 기초](composition-over-inheritance-basics.md) | 패턴에 들어가기 전에 "부모 클래스가 기본값이 아니다"를 먼저 고정한다 |
| 3단계 | 패턴 기초 | [객체지향 디자인 패턴 기초](object-oriented-design-pattern-basics.md) | 이제 `조합 -> 템플릿 메소드 -> 전략 -> 어댑터` 순서로 패턴 기초를 읽어도 덜 섞인다 |

짧게 외우면 **객체지향 핵심 원리 -> 상속보다 조합 -> 패턴 기초**다. 처음 배우는데 검색어가 막연할수록 이 3단계 route부터 타는 편이 안전하다.

라벨 읽는 법:

| 단계 라벨 | 언제 읽나 | 문서에서 기대할 것 |
|---|---|---|
| `[entrypoint]` | 첫 5~10분 진입일 때 | 큰 그림, 10초 질문, 30초 비교표부터 잡는다 |
| `[bridge]` | 두 패턴이나 두 용어가 헷갈릴 때 | 비교, 갈림길, 다음 문서 연결이 중심이다 |
| `[deep dive]` | 기초를 잡은 뒤 더 깊게 읽을 때 | 첫 진입보다 예외와 확장 맥락이 더 많다 |

짧게 보면 beginner route는 항상 `[entrypoint] -> [bridge] -> [deep dive]` 순서다.

## Template Method beginner route

템플릿 메소드는 초입 탐색도 같은 규칙으로 읽으면 덜 섞인다.
처음 배우는데 `hook method`, `abstract step`, `OncePerRequestFilter`가 한꺼번에 떠도 아래 순서로 고정한다.

| 단계 | 먼저 볼 문서 | 언제 쓰는지 |
|---|---|---|
| primer | [템플릿 메소드 첫 질문 라우터: `hook method`, `abstract step`, `template method vs strategy`](template-method-query-router-beginner.md) | 큰 그림, 기초, 어디서 시작할지 먼저 정하고 싶을 때 |
| basics | [템플릿 메소드 패턴 기초](template-method-basics.md) | 부모가 흐름을 쥔다, `abstract step`/`hook` 차이를 기초로 잡을 때 |
| bridge | [템플릿 메소드 vs 전략](template-method-vs-strategy.md) | 상속으로 풀지, 전략 객체로 뺄지 갈림길을 자를 때 |
| framework examples | [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](template-method-framework-lifecycle-examples.md) | `HttpServlet`, `OncePerRequestFilter`처럼 프레임워크 예시가 먼저 보일 때 |
| deep dive | [템플릿 메소드 (Template Method)](template-method.md) | 기초를 잡은 뒤 예외와 확장 맥락까지 더 깊게 읽을 때 |

## Beginner primer 모음

- [싱글톤 패턴 기초](singleton-basics.md) — `[entrypoint]` `10초 질문 -> 30초 비교표 -> 1분 예시` Quick-Check 다음 `자주 헷갈리는 포인트 3개`와 `3문항 미니 오해 점검`으로 Singleton/Static Utility/Spring Bean scope 혼동을 바로 정리하는 beginner primer
- [전략 패턴 기초](strategy-pattern-basics.md) — `[entrypoint]` `10초 질문 -> 30초 비교표 -> 1분 예시` Quick-Check에 더해 `Strategy vs if-else / Policy Object / Template Method` Confusion Box, `객체지향 핵심 원리 -> 상속보다 조합 -> 전략 -> 템플릿 메소드` beginner route까지 붙여 처음 읽는 사람의 헷갈림을 줄이는 primer
- [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](factory-selector-resolver-beginner-entrypoint.md) — `[entrypoint]` "처음 배우는데 이름이 헷갈릴 때"를 대상으로 생성 책임과 선택/해석 책임을 먼저 가르고, `Factory`/`Selector`/`Resolver` primer로 연결하는 entrypoint

## Beginner naming primer / bridge

- [Strategy vs Policy Selector Naming](strategy-policy-selector-naming.md) — `[bridge]` `*Factory`를 붙이기 전에 `*Selector`, `*Resolver`, `*Registry`, `*Strategy`가 선택/해석/조회/행동 의도를 더 잘 말하는지 확인하는 naming primer
- [Factory Misnaming Checklist: create 없는 `*Factory`를 리뷰에서 빨리 가르기](factory-misnaming-checklist.md) — `[bridge]` code review와 refactoring discussion에서 create-free factory 이름을 "만드나 / 고르나 / 찾나 / 푸나" 질문으로 빠르게 자르는 compact beginner checklist
- [Policy Object Naming Primer: `Policy`, `Strategy`, `Specification`을 언제 붙일까](policy-object-naming-primer.md) — `[bridge]` rule object가 실행 방식인지, 판정 규칙인지, 조건 명세인지 먼저 나눠 `Policy` / `Strategy` / `Specification` / `Factory`를 한 장에서 가르는 beginner naming bridge
- [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](map-backed-selector-resolver-registry-factory-naming-checklist.md) — `[bridge]` `Map<Key, ...>`를 감싼 클래스에서 raw input 해석, 후보 선택, 등록 lookup, creator 기반 생성 중 무엇이 public 책임인지 30초 안에 가르는 beginner checklist
- [Strategy Map vs Registry Primer](strategy-map-vs-registry-primer.md) — `[bridge]` 같은 `Map<Key, ...>`라도 행동 교체용 전략 컬렉션인지, 단순 keyed lookup용 registry인지 빠르게 자르는 비교 노트
- [Strategy Registry vs Service Locator Drift Note](strategy-registry-vs-service-locator-drift.md) — `[bridge]` 전략 lookup helper가 한 역할의 selector에 머무는지, 전역 service locator로 미끄러지는지 확인하는 beginner bridge
- [Policy Object vs Strategy Map: 커지는 전략 맵을 규칙 객체로 올릴 때](policy-object-vs-strategy-map-beginner-bridge.md) — `[bridge]` selector는 남기고, rule만 `Decision` 중심 policy object shape로 올려야 하는 순간을 가르는 beginner bridge

## Beginner registry / handler bridge

- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](registry-primer-lookup-table-resolver-router-service-locator.md) — `[entrypoint]` `lookup table`, `resolver`, `router`, `service locator`를 한 장에서 구분하고 registry-pattern / service-locator anti-pattern으로 안내하는 beginner entrypoint
- [Request Dispatch Naming: `Router`, `Dispatcher`, `HandlerMapping`이 `Selector`나 `Factory`보다 맞을 때](router-dispatcher-handlermapping-vs-selector-factory.md) — `[bridge]` request dispatch 경계에서 큰 길 분기, 구체 handler match, 전체 handoff 조율을 `Router` / `HandlerMapping` / `Dispatcher`로 나누고, handler 안쪽 정책 선택과 객체 생성에만 `Selector` / `Factory`를 남기는 beginner bridge
- [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](registry-vs-factory-injected-handler-maps.md) — `[bridge]` `List<Handler>`/`Map<String, Handler>`를 wiring, registry lookup, factory creation으로 자르고, registry bootstrap의 duplicate/missing key 검사를 fail-fast로 읽게 돕는 Spring-style beginner primer
- [Handler Registry Test Shape: `supports()` 기반 registry를 Spring 없이 단위 테스트하기](handler-registry-test-shape-supports-without-spring.md) — `[deep dive]` `supports()` 기반 handler registry를 fake/stub 입력과 복사형 test skeleton으로 시작하고, fake registry consumer test와 Spring context locator test의 차이까지 beginner 눈높이에서 자르는 primer

## Beginner domain-key / locator bridge

- [Bean Name vs Domain Key Lookup](bean-name-vs-domain-key-lookup.md) — `[bridge]` Spring이 주입한 `Map<String, Handler>`에서 `channel -> bean name`으로 새는 혼동을 끊고, 결제 수단/상태/채널/이벤트 타입 같은 domain key registry로 감싸는 beginner bridge
- [Injected Registry vs Service Locator Checklist](injected-registry-vs-service-locator-checklist.md) — `[bridge]` 생성자 노출 여부, domain key 사용, 본문 `getBean` 유무를 10초 순서로 점검하고, "새 결제 수단 추가 diff" 1분 예시로 drift를 빠르게 가르는 beginner 체크리스트
- [Plugin Registry Boundary Primer: 좁은 injected registry와 application-wide locator drift 구분하기](plugin-registry-boundary-primer.md) — `[bridge]` plugin extension point host가 자기 plugin registry를 생성자로 받는 정상 경계와, app-wide `PluginManager`/locator로 커지며 숨은 의존성을 만드는 drift를 초보자 눈높이에서 자르는 primer

## Beginner 패턴 / 이벤트 primer

- [데코레이터와 프록시 기초](decorator-proxy-basics.md) — `[entrypoint]` `10초 질문 -> 30초 비교표 -> 1분 예시` Quick-Check 다음 `자주 헷갈리는 포인트 3개`와 `3문항 미니 오해 점검`으로 wrapper 패턴 혼동과 Spring AOP 해석을 바로 정리하는 beginner primer
- [어댑터 패턴 기초](adapter-basics.md) — `[entrypoint]` `10초 질문 -> 30초 비교표: Adapter / Facade / Decorator -> 1분 예시: 외부 PG 응답을 우리 표준으로 번역하기` 리듬에 공통 `Quick-Check + Confusion Box`를 더해 Adapter/Facade/Decorator와 단순 mapper를 구분하고 "번역 책임" 경계를 먼저 고정하는 beginner primer
- [상속보다 조합 기초](composition-over-inheritance-basics.md) — `[entrypoint]` 처음 배우는데 `부모 클래스냐 전략 객체냐`를 30초 카드로 먼저 자르고, 문서 끝 `10초 exit card`에서 템플릿 메소드/전략 다음 읽기를 바로 고르게 만든 beginner bridge primer
- [추상 클래스냐 인터페이스+주입이냐: 템플릿 메소드·전략·조합 브리지](abstract-class-vs-interface-injection-bridge.md) — `[bridge]` 처음 배우는데 `추상 클래스냐 인터페이스+주입이냐`가 막힐 때, 고정 흐름(템플릿) vs 교체 규칙(전략/조합)으로 30초에 먼저 자르고, "추상 클래스면 다 템플릿 메소드인가?"를 비-템플릿 반례 1개로 바로 끊는 연결 문서
- [템플릿 메소드 첫 질문 라우터: `hook method`, `abstract step`, `template method vs strategy`](template-method-query-router-beginner.md) — `[entrypoint]` `hook method가 뭐예요`, `abstract step이 뭐예요`, `template method vs strategy가 뭐가 달라요`, `추상 클래스면 다 템플릿 메소드인가요` 같은 첫 질문을 큰 그림과 짧은 반례 카드로 먼저 자르고, primer -> framework/smell 순서로 보내는 compact beginner entrypoint

## Beginner 생성 / 요청 모델 primer

- [팩토리 패턴 기초](factory-basics.md) — `[entrypoint]` `10초 질문 -> 30초 비교표 -> 1분 예시`에 공통 `Quick-Check + Confusion Box`를 더해 `Factory / Static Factory / Selector / DI Container` 경계를 첫 읽기에서 고정하는 beginner primer
- [빌더 패턴 기초](builder-pattern-basics.md) — `[entrypoint]` `10초 질문 -> 30초 비교표 -> 1분 예시` Quick-Check 다음 `자주 헷갈리는 포인트 3개`와 `3문항 미니 오해 점검`으로 Constructor/Static Factory/Builder 선택 혼동을 먼저 자르는 beginner primer
- [요청 객체 생성 vs DI 컨테이너](request-object-creation-vs-di-container.md) — `[bridge]` request DTO, command, value object를 bean wiring이 아니라 constructor/static factory/builder 경계로 읽는 입문 브리지
- [Request Scope vs Plain Request Objects](request-scope-vs-plain-request-objects.md) — `[bridge]` Spring `@RequestScope` bean과 binder-created DTO, caller-built command를 섞지 않게 생명주기와 데이터 생성 책임을 먼저 분리하는 beginner bridge
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](record-vs-builder-request-model-chooser.md) — `[bridge]` 작은 request/query object를 기본 `record`로 두고, 정규화는 static factory, 옵션 조합 증가는 builder로 자르는 beginner chooser

## Beginner observer / command primer

- [옵저버 패턴 기초](observer-basics.md) — `[entrypoint]` `10초 질문 -> 30초 비교표 -> 1분 예시` Quick-Check 다음 `자주 헷갈리는 포인트 3개`, `3문항 미니 오해 점검`, 그리고 "중복 listener면 lifecycle hygiene, Spring commit timing이면 event listener timing" 상황별 다음 문서 연결까지 붙여 direct call/command/Pub-Sub 경계를 먼저 자르는 beginner primer
- [옵저버 vs 커맨드: 처음 선택을 줄이는 1페이지 브리지](observer-vs-command-beginner-bridge.md) — `[bridge]` `무슨 일이 일어났나` vs `무엇을 실행하나` 두 문장으로 먼저 자르고, 알림 fan-out과 작업 큐를 짧은 표와 예시로 구분하는 beginner bridge
- [옵저버 vs Pub-Sub: 처음 읽을 때 바로 잡는 짧은 다리](observer-vs-pubsub-quick-bridge.md) — `[bridge]` 같은 프로세스의 즉시 알림과 브로커/topic 기반 비동기 전파를 30초 비교표와 주문 완료 예시로 먼저 나눠 beginner 혼동을 줄이는 quick bridge
- [Event vs Command Naming Primer](event-vs-command-naming-primer.md) — `[bridge]` `OrderCompletedEvent` vs `CancelOrderCommand`처럼 과거 사실 vs 미래 요청을 1분 안에 가르고, `CancelOrderEvent` 같은 애매한 이름을 더 선명한 event/command 이름으로 바로 고치는 beginner naming primer
- [템플릿 메소드 패턴 기초](template-method-basics.md) — `[entrypoint]` 학습 순서 라벨: `basics -> framework examples -> deep dive`에서 `basics` 단계. `객체지향 핵심 원리 -> 상속보다 조합 -> 템플릿 메소드 -> 전략` beginner route에 더해 `리포트 템플릿`/`보고서 내보내기 템플릿` 검색어도 바로 받도록 공통 `Confusion Box`와 quick-check 예시를 정렬한 primer
- [커맨드 패턴 기초](command-pattern-basics.md) — `[entrypoint]` `10초 질문 -> 30초 비교표 -> 1분 예시` Quick-Check 다음 `자주 헷갈리는 포인트 3개`와 `3문항 미니 오해 점검`으로 direct call/strategy/DTO 경계를 먼저 고정하는 beginner primer
- [Command vs Strategy: `execute()`가 비슷해 보여도 먼저 자르는 짧은 다리](command-vs-strategy-quick-bridge.md) — `[bridge]` `실행 요청 저장` vs `알고리즘 교체` 두 질문으로 먼저 자르고, 작업 큐와 수수료 계산 예시로 `execute()` 겉모양 혼동을 빠르게 줄이는 beginner bridge

---

## 고전 패턴 primer

## GoF 디자인 패턴
- [Beginner Primer 작성 템플릿: 30초 비교표 + 1분 예시 박스 스켈레톤](beginner-primer-template.md) - 새 beginner primer를 쓸 때 "큰 그림 -> 30초 비교표: A / B -> Quick-Check -> Confusion Box -> 1분 예시: 도메인 상황 -> 다음 읽기" 리듬과 제목 톤을 함께 재사용할 수 있게 정리한 작성 가이드
- [Primer Scope Manifest: beginner primer와 bridge/checklist를 이름 대신 분류로 가르기](primer-scope-manifest.md) - `true-beginner-primer / beginner-bridge / beginner-checklist` 분류를 한 장에 고정해 beginner lint가 파일명 휴리스틱 없이 진짜 primer만 잡게 돕는 QA manifest
- `python3 beginner_primer_anchor_lint.py` - beginner primer 계열 문서가 `quick check / 10초 / 30초 비교표 / 1분 예시` 최소 앵커 세트를 갖췄는지 자동 점검하는 QA 스크립트. `--all-beginner`를 붙이면 전체 beginner 문서까지 넓혀 본다.

## 초보자 primer 작성 workflow

retrieval-anchor-keywords: beginner primer workflow, primer lint pass criteria, beginner authoring workflow, primer template and lint, beginner primer qa workflow, beginner_primer_anchor_lint usage, primer pass criteria, 초보자 프라이머 작성 순서, 프라이머 린트 통과 기준, 초보자 문서 qa 워크플로우

처음 쓰는 작성자라면 아래 3단계만 먼저 맞추면 된다.

| 단계 | 먼저 할 일 | 통과 기준 |
|---|---|---|
| 1. 뼈대 복사 | [Beginner Primer 작성 템플릿](beginner-primer-template.md)에서 `큰 그림 -> 30초 비교표 -> Quick-Check -> Confusion Box -> 1분 예시 -> 다음 읽기` 순서를 가져온다. | 첫 화면에서 문제 그림, 비교표, 작은 예시 위치가 바로 보인다. |
| 2. primer 표시 | [Primer Scope Manifest](primer-scope-manifest.md)를 보고 문서 상단에 `> Primer Scope: \`true-beginner-primer\`` 같은 marker를 붙인다. | lint 대상인지, bridge/checklist인지 분류가 제목이 아니라 marker로 드러난다. |
| 3. lint 확인 | 문서를 저장한 뒤 `python3 beginner_primer_anchor_lint.py <문서경로>`를 실행한다. lane 전체 beginner 문서를 다시 볼 때만 `--all-beginner`를 붙인다. | 종료 코드 `0`과 함께 `All ... include quick check / 10초 / 30초 비교표 / 1분 예시 anchors.`가 나오면 통과다. |

헷갈리면 이 한 줄만 기억하면 된다.
**템플릿으로 뼈대를 맞추고, scope marker를 붙이고, lint가 네 앵커를 모두 찾으면 beginner primer 1차 QA는 통과다.**

## 고전 패턴 entrypoint / naming

- [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](object-oriented-design-pattern-basics.md) - `[entrypoint]` 다섯 기본 패턴 큰 그림과 함께 `조합 -> 템플릿 메소드 -> 전략 -> 어댑터` route map, 공통 `Quick-Check + Confusion Box`, `direct call vs observer vs pub-sub` 빠른 연결 블록으로 읽는 순서와 첫 갈림길을 함께 잡는 입문 가이드
- [전략 (Strategy)](strategy-pattern.md) - `[deep dive]` runtime에 구현을 고르는 주체가 호출자/설정인지, `Context`는 실행만 맡는지, 부모 클래스 상속보다 전략 객체 주입이 자연스러운 순간과 작은 함수·단순 분기·전략 폭발 경계를 어디서 그을지 정리한 primer
- [템플릿 메소드 첫 질문 라우터: `hook method`, `abstract step`, `template method vs strategy`](template-method-query-router-beginner.md) - `[entrypoint]` `hook method`, `abstract step`, `template method vs strategy`, `추상 클래스면 다 템플릿 메소드인가` beginner query를 한 장에서 받아서 "부모가 흐름을 쥔다 vs 호출자가 전략을 고른다" 큰 그림과 짧은 오해 컷으로 먼저 자르고, basics/vs/framework/smell 순서로 넘기는 compact entrypoint
- [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](factory-selector-resolver-beginner-entrypoint.md) - `[entrypoint]` creation-vs-selection 관점에서 `Factory`/`Selector`/`Resolver`를 먼저 자르고, naming checklist와 factory primer로 이어 주는 beginner entrypoint

## 고전 패턴 naming / selector bridge

- [Strategy vs Policy Selector Naming](strategy-policy-selector-naming.md) - `*Factory`가 생성 책임을 암시해 오해를 만들 때 `*Selector`, `*Resolver`, `*Registry`, `*Strategy`로 의도를 나누는 beginner naming bridge
- [Factory Misnaming Checklist: create 없는 `*Factory`를 리뷰에서 빨리 가르기](factory-misnaming-checklist.md) - code review와 refactoring discussion에서 "만드나 / 고르나 / 찾나 / 푸나" 네 질문으로 create-free factory 이름을 빠르게 가르는 compact checklist
- [Policy Object Naming Primer: `Policy`, `Strategy`, `Specification`을 언제 붙일까](policy-object-naming-primer.md) - rule object가 실행 방식인지, 판정 규칙인지, 조건 명세인지 먼저 나눠 `Policy` / `Strategy` / `Specification` / `Factory`를 한 장에서 가르는 beginner naming bridge
- [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](map-backed-selector-resolver-registry-factory-naming-checklist.md) - 같은 `Map<Key, ...>`라도 raw input을 푸는지, 조건으로 고르는지, 등록된 값을 찾는지, creator로 새로 만드는지에 따라 이름을 바로 자르는 beginner naming checklist
- [Strategy vs Function](strategy-vs-function-chooser.md) - lambda/작은 함수 vs full Strategy type chooser, 짧고 stateless한 계산식이면 함수, 이름 있는 규칙·협력 객체·독립 테스트 경계가 필요하면 Strategy

## 고전 패턴 registry naming / drift

- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](registry-primer-lookup-table-resolver-router-service-locator.md) - `lookup table`은 registry로, `service locator`는 anti-pattern으로 보내고 resolver/router 주변 용어를 먼저 자르는 beginner entrypoint
- [Request Dispatch Naming: `Router`, `Dispatcher`, `HandlerMapping`이 `Selector`나 `Factory`보다 맞을 때](router-dispatcher-handlermapping-vs-selector-factory.md) - request dispatch 코드를 읽을 때 route 분기, concrete handler matching, central handoff orchestration을 `Router` / `HandlerMapping` / `Dispatcher`로 나누고, handler 내부 정책 선택만 `Selector`로 남기는 beginner naming bridge
- [Strategy Map vs Registry Primer](strategy-map-vs-registry-primer.md) - 같은 `Map<Key, ...>` 모양이더라도 "행동 교체"가 핵심이면 strategy, "이름표 lookup"이 핵심이면 registry라고 30초 안에 자르는 beginner comparison note
- [Strategy Registry vs Service Locator Drift Note](strategy-registry-vs-service-locator-drift.md) - `Map<Key, Strategy>` lookup helper가 좁은 selector에서 전역 service locator로 변하는 신호를 자르는 beginner smell note
- [Policy Object vs Strategy Map: 커지는 전략 맵을 규칙 객체로 올릴 때](policy-object-vs-strategy-map-beginner-bridge.md) - behavior selector로 남겨둘 전략 map과, reason code/allowed/decision이 필요해져 policy object shape로 올려야 하는 규칙을 가르는 beginner bridge

## 고전 패턴 strategy / template bridge

- [Strategy vs State vs Policy Object](strategy-vs-state-vs-policy-object.md) - payment method / payment status / refund rule처럼 헷갈리는 축을 한 장에서 구분하는 비교 문서
- [추상 클래스냐 인터페이스+주입이냐: 템플릿 메소드·전략·조합 브리지](abstract-class-vs-interface-injection-bridge.md) - "추상 클래스냐 인터페이스+주입이냐" 질문을 고정 흐름(템플릿)과 교체 규칙(전략/조합)으로 먼저 나누고, 비-템플릿 추상 클래스 반례로 오해를 빠르게 끊는 beginner bridge
- [템플릿 메소드 vs 전략](template-method-vs-strategy.md) - `[bridge]` "상속 vs 객체 주입", "부모 클래스냐 전략 객체냐", "`hook 하나 추가할까, 전략으로 뺄까`", "`오버라이드로 풀까 객체로 뺄까`", "`추상 클래스냐 인터페이스+주입이냐`" 같은 첫 질문을 "부모가 흐름을 쥔다 vs 호출자가 전략을 고른다"로 바로 번역하고, 추상 클래스 오해를 끊는 3문장 반례 카드, `hook 추가 vs 전략 분리` 3문항 미니 체크, 표현 변형 묶음표, 결제/리포트/검증 3줄 초미니 상황 카드와 `결제 전략`/`리포트 템플릿`/`검증 규칙 교체` 검색어 번역 표로 entrypoint 메시지를 맞춘 beginner chooser

## 고전 패턴 구조 / 생성

- [데코레이터 vs 프록시 (Decorator vs Proxy)](decorator-vs-proxy.md)
- [Adapter (어댑터)](adapter.md) - legacy SDK / 외부 인터페이스를 기존 포트에 맞추는 번역기 primer
- [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](bridge-storage-provider-abstractions.md) - storage/provider처럼 독립적으로 변하는 두 축을 분리해 조합 폭발을 막는 구조
- [런타임 선택에서 Bridge vs Strategy vs Factory](bridge-strategy-vs-factory-runtime-selection.md) - policy selection을 `*Factory`로 부르기 쉬운 지점을 행동 선택 / 객체 생성 / 두 축 분리로 잘라 주는 beginner bridge note
- [퍼사드 vs 어댑터 vs 프록시](facade-vs-adapter-vs-proxy.md) - wrapper 비교: 단순화 vs 인터페이스 번역 vs 호출 제어
- [Adapter Chaining Smells](adapter-chaining-smells.md) - adapter stack이 translation pipeline smell로 변하는 지점을 정리한 경고 문서

## 고전 패턴 생성 / 빌더

- [싱글톤 (Singleton)](singleton.md)
  - [싱글톤 Java 구현 방법](singleton-java.md)
- [팩토리 (Factory)](factory.md) - `[deep dive]` 언제 생성 책임을 숨기고 언제 그냥 `new`/정적 팩토리/빌더/레지스트리를 택해야 하는지 정리
- [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](constructor-vs-static-factory-vs-factory-pattern.md) - Java `of`/`from`/`valueOf`/`parse`/`getInstance` naming guide와 같은 타입 생성 vs 구현 선택 factory 구분용 companion
- [요청 객체 생성 vs DI 컨테이너](request-object-creation-vs-di-container.md) - request DTO, command, value object를 constructor/static factory/builder로 두고 service/client/repository만 bean wiring에 남기는 beginner bridge
- [Request Scope vs Plain Request Objects](request-scope-vs-plain-request-objects.md) - Spring `@RequestScope` bean과 `@RequestBody` DTO / caller-built command를 생명주기와 데이터 생성 책임으로 분리하는 beginner bridge
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](record-vs-builder-request-model-chooser.md) - small request/query model은 `record`, 이름 있는 정규화는 static factory, 옵션 조합 폭발은 builder로 자르는 beginner chooser
- [빌더 (Builder)](builder-pattern.md) - `[deep dive]` "초안 작성 -> build로 완성" 멘탈 모델, 15초 선택 루틴, `build()` 검증 예시, builder 오해(`체이닝=빌더`, `검증 자동`)를 함께 정리한 beginner-friendly deep dive
- [Factory vs Abstract Factory vs Builder](factory-vs-abstract-factory-vs-builder.md)
- [Factory Switch Registry Smell](factory-switch-registry-smell.md) - switch-heavy factory를 registry-backed factory로 옮길 때 selector / registry / factory 경계를 다시 나누고 service locator drift를 피하는 smell guide

## 고전 패턴 registry / service locator

- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](registry-primer-lookup-table-resolver-router-service-locator.md) - `lookup table`, `resolver`, `router`, `service locator`를 한 장에서 나누고 registry-pattern과 service-locator anti-pattern으로 라우팅하는 beginner bridge
- [Request Dispatch Naming: `Router`, `Dispatcher`, `HandlerMapping`이 `Selector`나 `Factory`보다 맞을 때](router-dispatcher-handlermapping-vs-selector-factory.md) - request dispatch code에서 "어느 길로 보낼까 / 어떤 handler가 맞나 / handoff 전체를 누가 조율하나"를 `Router` / `HandlerMapping` / `Dispatcher`로 자르고, `Selector` / `Factory`는 handler 안쪽 역할에 남기는 beginner bridge
- [Registry Pattern: 객체를 찾는 이름표와 저장소](registry-pattern.md) - lookup table의 역할, factory와의 차이, switch factory refactor 이후에도 registry를 좁은 lookup으로 유지하는 기준
- [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](registry-vs-factory-injected-handler-maps.md) - `Map<String, Handler>`/`List<Handler>` 주입을 factory로 오해할 때 wiring, lookup, creation을 세 단계로 끊고 registry bootstrap의 duplicate/missing key 검사를 fail-fast로 읽는 beginner primer
- [Handler Registry Test Shape: `supports()` 기반 registry를 Spring 없이 단위 테스트하기](handler-registry-test-shape-supports-without-spring.md) - fake/stub handler, helper method, duplicate/missing/bootstrap lookup에 더해 fake registry consumer test와 Spring context locator test를 분리해서 읽는 beginner test primer

## 고전 패턴 domain-key / locator

- [Bean Name vs Domain Key Lookup](bean-name-vs-domain-key-lookup.md) - Spring이 주입한 `Map<String, Handler>`에서 `channel -> bean name` 문자열 조합을 public 분기로 쓰지 않도록 막고 domain-key registry로 감싸는 beginner bridge
- [Injected Registry vs Service Locator Checklist](injected-registry-vs-service-locator-checklist.md) - 생성자/본문 조회 위치/키 타입 세 질문과 "새 결제 수단 추가 diff" 비교표로 injected registry와 hidden lookup drift를 가르는 beginner checklist
- [Plugin Registry Boundary Primer: 좁은 injected registry와 application-wide locator drift 구분하기](plugin-registry-boundary-primer.md) - plugin extension point host의 좁은 registry와 앱 전체가 쓰는 `PluginManager`/locator drift를 분리해서, plugin lookup이 lookup 경계인지 숨은 의존성 조회인지 빠르게 자르는 beginner bridge
- [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](service-locator-antipattern.md) - `hidden dependency`, `global lookup`, `ApplicationContext.getBean` 초심자 검색에서 숨은 의존성 냄새를 먼저 자르고 checklist/primer로 연결하는 companion anti-pattern

## 고전 패턴 observer / template method

- [옵저버 (Observer)](observer.md) - `[deep dive]` observer vs direct call vs Pub/Sub decision table, ordering/failure boundary caveats
- [옵저버, Pub/Sub, ApplicationEvent](observer-pubsub-application-events.md)
- [Mediator vs Observer vs Pub/Sub](mediator-vs-observer-vs-pubsub.md) - 같은 프로세스에서 coordination / notification / brokered messaging을 가르는 비교 문서
- [Observer Lifecycle Hygiene](observer-lifecycle-hygiene.md) - unsubscribe, duplicate-registration 방지, UI/plugin/long-lived process의 listener ownership과 teardown discipline
- [옵저버 vs 커맨드: 처음 선택을 줄이는 1페이지 브리지](observer-vs-command-beginner-bridge.md) - `[bridge]` `무슨 일이 일어났는지 알리는가`와 `무엇을 실행하라고 요청하는가`를 먼저 잘라, beginner가 observer/event와 command/queue를 섞지 않게 돕는 entrypoint bridge
- [옵저버 vs Pub-Sub: 처음 읽을 때 바로 잡는 짧은 다리](observer-vs-pubsub-quick-bridge.md) - `[bridge]` 같은 프로세스 fan-out과 broker/topic 기반 비동기 전파를 짧게 나눠 첫 읽기 혼동을 줄이는 beginner bridge
- [Spring `@EventListener` vs `@TransactionalEventListener`: Timing, Ordering, Rollback](spring-eventlistener-vs-transactionaleventlistener-timing.md) - Spring 내부 옵저버에서 commit/rollback timing, `@Order`, `fallbackExecution`이 어떻게 의미를 바꾸는지 정리한 bridge 문서

## 고전 패턴 template method / chain / smell

- [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](template-method-framework-lifecycle-examples.md) - `[bridge]` 학습 순서 라벨: `basics -> framework examples -> deep dive`에서 `framework examples` 단계. basics를 다시 풀지 않고 `HttpServlet`, `OncePerRequestFilter`, classic xUnit fixture에서 skeleton이 어디 있는지 짚고, callback을 `abstract step` vs `hook`으로 분류하는 초심자용 매핑 표를 통해 base class 상속 vs 분리된 policy/component 경계까지 이어 주는 companion 문서
- [템플릿 메소드 (Template Method)](template-method.md) - `[deep dive]` 학습 순서 라벨: `basics -> framework examples -> deep dive`에서 `deep dive` 단계. "고정 순서 + 빈칸 채우기" 60초 멘탈 모델, 템플릿 vs 전략 30초 선택표, 입문 3질문 판정으로 시작해 abstract step vs hook method 경계를 잡는다
- [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](chain-of-responsibility-filters-interceptors.md) - Servlet `Filter`, Spring MVC `HandlerInterceptor`, short-circuit 흐름을 request chain 관점에서 읽는 primer
- [JUnit 5 Callback Model vs Classic xUnit Template Skeleton](junit5-callback-model-vs-classic-xunit-template-skeleton.md) - `setUp`/`tearDown`(hook)와 test 본문(핵심 슬롯) 미니 매핑표로 시작해, 같은 클래스 다중 `@BeforeEach`/`@AfterEach`를 초보자가 바로 읽을 수 있는 5줄 순서 카드와 짧은 로그 예시로 풀어낸 뒤, "여러 lifecycle method는 기본적으로 1쌍으로 줄인다"는 30초 규칙 카드와 전/후 비교 예시로 fixture 정리 방향을 먼저 고정하고, `@ExtendWith`가 개입하면 왜 순서 추론이 더 어려워지는지 1개 비교표로 연결하는 beginner 보조 문서
- [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](template-method-vs-filter-interceptor-chain.md) - 학습 순서 라벨 `basics -> framework examples -> deep dive`를 따라 `framework examples -> deep dive` 사이에서 읽는 bridge로, 같은 요청 경로의 chain participant와 template wrapper를 30초 안에 분리하는 comparison note

## 고전 패턴 smell / decision guide

- [Template Hook Smells](template-hook-smells.md) - `hook` 1~2개 설명을 넘어서 `beforeX`/`afterX`/`cleanup`이 늘고 내부 순서를 외워야 할 때만 들어가는 advanced smell guide로, `OncePerRequestFilter#shouldNotFilter`와 classic xUnit `setUp`/`tearDown`까지 unsafe extension point 기준으로 묶는다
- [Composition over Inheritance](composition-over-inheritance-practical.md) - 상속이 아니라 변경 축 기준으로 조합을 고르는 primer
- [Command Pattern, Undo, Queue](command-pattern-undo-queue.md) - undo/history/job queue까지 이어지는 command 객체 primer
- [실전 패턴 선택 가이드](pattern-selection.md) - survey / decision guide, change-axis confusion을 adapter/composition/command primer까지 직접 연결

## 아키텍처 패턴
- [MVC (Model-View-Controller)](mvc-python.md)

## 백엔드 / DDD catalog

아래 mixed catalog에서는 `[playbook]` 라벨로 step-oriented rollout 문서를 deep dive 패턴과 구분했다.

## DDD / Backend 설계 패턴 언어
- [Aggregate Boundary vs Transaction Boundary](aggregate-boundary-vs-transaction-boundary.md)
- [Aggregate Root vs Unit of Work](aggregate-root-vs-unit-of-work.md)
- [Aggregate Version and Optimistic Concurrency Pattern](aggregate-version-optimistic-concurrency-pattern.md)
- [Unit of Work Pattern: 트랜잭션 경계 안에서 변경을 모으기](unit-of-work-pattern.md)
- [Repository Boundary: Aggregate Persistence vs Read Model](repository-boundary-aggregate-vs-read-model.md)
- [Transaction Script vs Rich Domain Model](transaction-script-vs-rich-domain-model.md)
- [Aggregate Invariant Guard Pattern](aggregate-invariant-guard-pattern.md)
- [Invariant-Preserving Command Model](invariant-preserving-command-model.md)
- [Reference Other Aggregates by ID](aggregate-reference-by-id.md)

## Strict Read / Projection 운영 패턴
- [Read Model Staleness and Read-Your-Writes](read-model-staleness-read-your-writes.md)
- [Session Pinning vs Version-Gated Strict Reads](session-pinning-vs-version-gated-strict-reads.md)
- [Strict Read Fallback Contracts](strict-read-fallback-contracts.md)
- [Strict Pagination Fallback Contracts](strict-pagination-fallback-contracts.md) - list endpoint fallback boundary split: first page, later-page reject/reissue, mixed-cursor prevention
- [Strict List Canary Metrics and Rollback Triggers](strict-list-canary-metrics-rollback-triggers.md) - page-depth metric family, cursor verdict drift, freeze vs hard rollback packet
- [Pinned Legacy Chain Risk Budget](pinned-legacy-chain-risk-budget.md) - `ACCEPT` / pinned-chain fallback justification, short TTL, dedicated reserve, rollback zero-ttl
- [Fallback Capacity and Headroom Contracts](fallback-capacity-and-headroom-contracts.md) - strict fallback reserve, burst, breaker, degraded UX 계약
- [Strict Fallback Degraded UX Contracts](strict-fallback-degraded-ux-contracts.md) - processing/pending state split, retry-after policy, user-visible guarantees when fallback is constrained

## Projection rebuild / cutover 패턴
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

## 상태 / 정책 / 이벤트 패턴
- [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](state-pattern-workflow-payment.md) - payment lifecycle, workflow transition guard, invalid transition 방지
- [State Pattern vs State Machine Library vs Workflow Engine](state-machine-library-vs-state-pattern.md) - local aggregate transition, in-process transition table, durable workflow runtime를 가르는 decision guide
- [Policy Object Naming Primer: `Policy`, `Strategy`, `Specification`을 언제 붙일까](policy-object-naming-primer.md) - rule object naming에서 "방법 / 판정 / 조건 / 생성" 질문을 먼저 분리해 `Factory` 과용을 줄이는 beginner bridge
- [Policy Object Pattern: 도메인 결정을 객체로 만든다](policy-object-pattern.md) - refund/fee/approval decision을 reason code, fee, 후속 액션까지 담는 규칙 객체
- [Specification Pattern: 조건식을 조합 가능한 도메인 규칙으로 만들기](specification-pattern.md) - boolean 명세 조합과 policy object로 넘어가는 rich decision 경계를 함께 정리
- [Layered Validation Pattern: 입력, 도메인, 정책을 층별로 검증하기](layered-validation-pattern.md) - beginner-friendly 30초 멘탈 모델로 실패 의미를 먼저 나누고, 검증 흐름 고정 vs 규칙 교체는 `템플릿 메소드 vs 전략` 카드로 이어 주는 bridge
- [Semantic Lock and Pending State Pattern](semantic-lock-pending-state-pattern.md)

## 이벤트 / ACL / 전달 패턴
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

## Query / Pagination / Read Model Migration
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

## Workflow / Coordination / Boundary 패턴
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

## 한 줄 정리

> 아직 없습니다.
