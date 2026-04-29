# Spring Framework (스프링 프레임워크)

> 한 줄 요약: Spring을 처음 읽을 때는 MVC, DI, 트랜잭션, 요청 파이프라인 primer 4장만 먼저 보고, `context cache`, `REQUIRES_NEW`, `deadlock`, `observability` 같은 follow-up 키워드는 관련 문서 링크 뒤로 미뤄 두는 편이 안전하다.

**난이도: 🟢 Beginner**

> 작성자 : [이동훈](https://github.com/idonghun)

관련 문서:
- [Spring 처음 10분 라우트: primer 4장으로 시작하기](#처음-10분-라우트)
- [Spring primer 되돌아가기: 질문 축 다시 고르기](#spring-primer-되돌아가기)
- [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트: `@RequestBody 400`부터 validation/error response까지](#validation-400-problemdetail-route)
- [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](./spring-ioc-di-basics.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [@Transactional 기초: 트랜잭션 어노테이션이 하는 일](./spring-transactional-basics.md)
- [Spring 테스트 기초: @SpringBootTest부터 슬라이스 테스트까지](./spring-testing-basics.md)
- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Network 카테고리 README: HTTP, 캐시, 세션에서 Spring으로 넘어오는 handoff](../network/README.md#network---spring-handoff)
- [Database First-Step Bridge: Spring 다음 DB 입구를 한 장으로 잡기](../database/database-first-step-bridge.md)
- [Network: HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [CS 루트 README: 카테고리 전체 네비게이터](../../README.md#quick-routes)

retrieval-anchor-keywords: spring beginner route, spring primer route, spring 뭐부터 읽지, spring 처음 헷갈려요, spring mvc primer, spring di primer, spring bean primer, spring transaction primer, spring request pipeline guide, dispatcherservlet basics, transactional beginner, 왜 new 대신 주입, bean missing spring basics, 404 400 spring first split, validation 400 problemdetail route

<details>
<summary>Table of Contents</summary>

- beginner first: `처음 4장 루트`부터 읽고 아래 인덱스는 막힌 증상이 생겼을 때만 펼친다.
- deep dive 힌트: `전파`, `deadlock`, `timeout`, `observability`, `streaming`, `security session` 같은 단어가 보이면 지금은 링크만 저장해 두고 primer부터 끝낸다.
- safe return: primer를 읽다 길을 잃으면 [`Spring primer 되돌아가기`](#spring-primer-되돌아가기)에서 다시 질문 축을 고른다.

</details>

---

## 빠른 탐색

이 `README`는 Spring navigator다. beginner는 아래 4장부터 보면 된다.

- beginner first: MVC, DI, `@Transactional`, 요청 파이프라인 primer 4장을 먼저 본다. DI 축은 "`왜 new 대신 주입해요?`"면 [`IoC와 DI 기초`](./spring-ioc-di-basics.md), "`bean`/`component scan`/`누가 연결해요?`"면 [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md)부터 시작한다.
- 증상 anchor: `404`는 MVC, `400`은 바인딩, `bean missing`은 DI/component scan, "`@Transactional`이 안 먹어요"는 프록시 경계부터 본다.
- bridge anchor: "`service bean not found`와 `@Transactional` 안 먹음이 같은 문제 같아요"라면 "`무엇을 띄웠나`"는 [`Spring 테스트 기초`](./spring-testing-basics.md), "`어떻게 호출했나`"는 [`@Transactional 기초`](./spring-transactional-basics.md)로 나눈다.
- safe next step: "`HTTP 다음에 Spring은 뭐부터 봐요?`"라면 [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md)부터 읽고, 한 장 요약은 [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md)로 간다.
- beginner handoff: `request -> controller -> database`가 처음이면 [`Network -> Spring handoff`](../network/README.md#network---spring-handoff) -> [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) -> [`Database First-Step Bridge`](../database/database-first-step-bridge.md) 순서로만 간다.

## 처음 막힐 때 30초 선택표

처음에는 용어 뜻을 다 외우기보다 "`지금 어디가 막혔는지`"만 고르면 된다.

| 지금 바로 나온 말 | 먼저 읽을 1장 | 바로 이어 읽을 1장 | 왜 이 순서가 beginner-safe 한가 |
|---|---|---|---|
| "`DispatcherServlet`이 뭐예요?", "`404`예요" | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | 요청 입구와 전체 그림을 같은 요청 예시로 다시 붙여 준다 |
| "`왜 new 대신 주입해요?`" | [`IoC와 DI 기초`](./spring-ioc-di-basics.md) | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | 먼저 이유를 잡고, 그다음 scan과 Bean 등록으로 내려간다 |
| "`bean missing`이에요", "`controller`랑 `service`는 누가 연결해요?`" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | 객체 조립과 요청 처리 장면을 같은 문제로 섞지 않게 해 준다 |
| "`@Transactional`이 안 먹어요", "`this.method()`가 보여요`" | [`@Transactional 기초`](./spring-transactional-basics.md) | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | 옵션보다 service 경계와 프록시 위치를 먼저 고정하게 해 준다 |

## 빠른 복귀 규칙

- deep dive 신호: `propagation`, `deadlock`, `timeout`, `observability`, `streaming`, `REQUIRES_NEW` 같은 단어가 보이면 primer 뒤에만 내려간다.
- safe return path: `302 /login`, `cookie`, `304`가 먼저면 [`Network primer 되돌아가기`](../network/README.md#network-primer-되돌아가기)로 물러나고, 전체 카테고리는 [`CS 루트 Quick Routes`](../../README.md#quick-routes)로 간다.
- mental model: "`요청은 MVC`, `연결은 DI`, `DB 작업 묶음은 @Transactional`, `셋을 다시 한 장으로 붙이는 문서가 요청 파이프라인 primer`" 순서만 먼저 기억하면 된다.

## 처음 20분 루트

처음 읽는 사람은 "전부 다 연결돼 보인다"는 느낌부터 줄여야 한다. 아래처럼 질문 하나당 primer 하나만 고르면 충분하고, 나머지 deep dive는 나중에 눌러도 된다.

| 지금 머릿속 첫 질문 | 먼저 읽을 primer | 여기서 멈춰도 되는 이유 |
|---|---|---|
| "`스프링이 요청을 어떻게 처리해요?`", "`DispatcherServlet`이 뭐예요?" | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | 요청 입구, 길찾기, 바인딩, 예외 번역을 한 장으로 끊어 준다 |
| "`왜 new 대신 주입해요?`", "`service`는 누가 넣어 줘요?" | [`IoC와 DI 기초`](./spring-ioc-di-basics.md) | DI를 "객체 조립 책임 이동"으로 먼저 이해하게 해 준다 |
| "`bean`이 뭐예요?", "`component scan`은 언제 나와요?" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | 등록, 주입, 프록시를 같은 시점으로 착각하지 않게 해 준다 |
| "`controller`는 있는데 `service`는 누가 준비했죠?`", "`요청이 올 때마다 Bean을 새로 만들어요?`" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | 요청 길찾기와 객체 조립을 분리하는 concrete example이 바로 붙어 있다 |
| "`@Transactional`이 왜 안 먹어요?`", "`commit/rollback`은 누가 해요?" | [`@Transactional 기초`](./spring-transactional-basics.md) | 옵션보다 먼저 프록시 경계를 보게 만든다 |
| "`처음`인데 controller/DB/전체 중 어디까지 테스트해야 해요?" | [`Spring 테스트 기초`](./spring-testing-basics.md) | 테스트 실패를 slice 경계 문제와 트랜잭션 문제로 섞지 않게 해 준다 |

처음엔 primer 하나만 읽고 다시 이 README로 돌아오는 편이 더 안전하다. 첫 질문이 풀렸으면 다음 한 칸만 고르고, `self-invocation`, `condition report`, `deadlock` 같은 단어는 여기서 멈춘다.

## 처음 20분 증상표

| 지금 바로 보이는 증상 | 먼저 고를 primer | 왜 이 문서가 출발점인가 |
|---|---|---|
| `404`, `400`, "`요청이 어디서 끊겼죠?`" | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | 요청이 어디까지 왔는지부터 잘라 준다 |
| "`bean missing`", "`왜 new 대신 주입해요?`" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | 객체 등록과 주입 책임을 먼저 분리해 준다 |
| "`@Transactional`이 안 먹어요`", "`this.method()`가 보여요`" | [`@Transactional 기초`](./spring-transactional-basics.md) | 옵션보다 프록시 경계를 먼저 고정해 준다 |
| "`@WebMvcTest`인데 service bean not found예요`", "`어느 테스트부터 써요?`" | [`Spring 테스트 기초`](./spring-testing-basics.md) | test slice와 프록시 문제를 다른 축으로 분리해 준다 |

## 초급자 정지선

처음 읽는 단계에서는 아래 범위까지만 이해해도 충분하다. 이 선을 넘는 키워드는 "지금 당장 해결할 1순위"가 아니라 "나중에 follow-up 링크로 내려갈 2순위"라고 보면 된다.

| 지금 보이는 단어 | 지금 판단 | 먼저 둘 곳 |
|---|---|---|
| `404`, `400`, `bean missing`, "`@Transactional`이 안 먹어요" | primer 4장 안에서 먼저 풀 수 있는 질문이다 | [`첫 판단 4축`](#첫-판단-4축) |
| `self-invocation`, `rollback-only`, `REQUIRES_NEW` | 트랜잭션 심화 신호다 | [`첫 4장 뒤에만 여는 입문 확장`](#첫-4장-뒤에만-여는-입문-확장) |
| `deadlock`, `lock wait`, `timeout`, `observability`, `streaming` | primer 범위를 넘는 운영/incident형 신호다 | README 아래쪽 deep dive cluster |
| `cookie`, `302 /login`, `304`, `cache` | Spring 내부보다 browser/network 질문일 수 있다 | [`Network -> Spring handoff`](../network/README.md#network---spring-handoff) |

## 되돌아가기와 다음 한 걸음

| 지금 막힌 beginner 문장 | 여기서 바로 갈 곳 | 왜 이 링크가 안전한가 |
|---|---|---|
| "`302`, `304`, `cookie`가 먼저 헷갈려요" | [`Network -> Spring handoff`](../network/README.md#network---spring-handoff) | Spring 용어를 더 쌓기 전에 browser/network 축으로 한 칸 되돌아가게 해 준다 |
| "network primer까지 보고 왔는데 Spring은 어디서 다시 시작해요?" | [`처음 10분 라우트`](#처음-10분-라우트) | Network에서 건너온 뒤 Spring primer 4장 중 지금 질문에 맞는 한 장만 다시 고르게 해 준다 |
| "`controller -> service -> repository` 흐름은 보이는데 DB가 아직 추상적이에요" | [`Database First-Step Bridge`](../database/database-first-step-bridge.md) | Spring 내부 용어를 더 늘리지 않고 다음 카테고리의 safe next step 한 장만 연결한다 |
| "문서가 많아서 다시 어디서 고를지 모르겠어요" | [`첫 판단 4축`](#첫-판단-4축), [`CS 루트 Quick Routes`](../../README.md#quick-routes) | Spring 내부 축으로 다시 자르거나 카테고리 네비게이터로 안전하게 복귀할 수 있다 |
| "primer 한 장은 읽었는데 다음에 뭘 눌러야 할지 모르겠어요" | [`처음 10분 라우트`](#처음-10분-라우트), [`Spring primer 되돌아가기`](#spring-primer-되돌아가기) | 방금 읽은 문서를 버리지 않고 같은 beginner 질문 축에서 다음 한 칸만 고르게 해 준다 |

## 한 요청 4칸 지도

처음에는 Spring 용어를 전부 외우기보다, 같은 요청을 아래 4칸으로 자르는 편이 훨씬 덜 헷갈린다.

> mental model: 요청은 MVC가 받고, 객체는 DI가 연결하고, DB 묶음은 `@Transactional`이 정하고, 요청 파이프라인 primer는 이 셋을 한 장면으로 다시 붙여 준다.

| 같은 `POST /orders` 장면에서 먼저 든 말 | 지금 섞지 말아야 할 것 | 먼저 읽을 문서 |
|---|---|---|
| "`/orders`가 왜 저 컨트롤러로 안 가지?" | URL 길찾기와 Bean 등록 문제 | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) |
| "`OrderService`는 누가 넣어 줬지?" | 객체 조립과 트랜잭션 옵션 문제 | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) |
| "`@Transactional`이 왜 안 먹죠?" | 프록시 경계와 MVC 매핑 문제 | [`@Transactional 기초`](./spring-transactional-basics.md) |
| "`404`, `400`, DI 예외가 한 요청에서 다 섞여 보여요" | 증상을 한 층위로 보는 습관 | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) |

이 표는 "한 요청 안에 여러 층이 동시에 보인다"는 beginner 혼동을 끊는 용도다. `404`는 길찾기, `bean missing`은 객체 조립, `@Transactional`은 작업 묶기라는 말만 먼저 남기고 다음 문서를 고르면 glossary처럼 덜 읽힌다.

## 첫 판단 4축

Spring 입문자가 가장 많이 꼬이는 지점은 "한 요청에서 일어난 문제"를 전부 같은 층위로 보는 것이다. 먼저 아래 4축으로 잘라 두면 glossary처럼 읽지 않고, 문서를 고르는 속도가 빨라진다.

| 지금 머릿속 질문 | 보는 축 | 첫 문서 |
|---|---|---|
| "이 URL이 왜 저 컨트롤러로 가지?" | MVC 길찾기 | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) |
| "컨트롤러 안 `service`는 누가 넣었지?" | Bean 등록 / DI | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) |
| "DB 저장을 어디까지 한 묶음으로 보지?" | 트랜잭션 경계 | [`@Transactional 기초`](./spring-transactional-basics.md) |
| "이 셋이 한 요청에서 어떻게 만나는 거지?" | 요청 파이프라인 연결 | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) |

짧게 외우면 이렇다.

- MVC는 요청 길찾기다.
- DI는 객체 조립이다.
- 트랜잭션은 DB 작업 묶기다.
- 요청 파이프라인 primer는 위 세 축을 한 장면으로 다시 묶는 문서다.

## 테스트는 5번째 레이어가 아니라 확인용 창이다

처음엔 `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest`가 Spring 안의 또 다른 레이어처럼 보여서 더 헷갈린다. 테스트 문서는 **새 구조를 추가하는 문서가 아니라, 위 4축 중 어디를 확대해서 볼지 고르는 문서**라고 보면 된다.

| 지금 확인하고 싶은 질문 | 실제 runtime 축 | 먼저 볼 테스트 primer |
|---|---|---|
| "`이 URL`, `JSON`, `400/404`가 맞게 보이나?" | MVC 길찾기 / 바인딩 | [`Spring 테스트 기초`](./spring-testing-basics.md) |
| "`service bean not found`가 왜 뜨지?" | DI/Bean 경계 | [`Spring 테스트 기초`](./spring-testing-basics.md), [`Spring Test Slice Scan Boundary 오해`](./spring-test-slice-scan-boundaries.md) |
| "`rollback`, `commit`이 왜 기대와 다르지?" | 트랜잭션 경계 | [`Spring 테스트 기초`](./spring-testing-basics.md), [`@Transactional 기초`](./spring-transactional-basics.md) |

짧게 외우면 이렇다. 테스트는 "무엇을 띄울까"를 고르는 문서이고, 실제로 관찰하는 대상은 여전히 MVC, DI, 트랜잭션, 요청 파이프라인 4축이다.

## DI/Bean 2단계 분리

DI 축에서 같은 beginner가 두 문서를 연달아 열어도 질문이 다르면 중복 클릭이 아니다. 먼저 아래처럼 자르면 된다.

| 지금 먼저 든 질문 | 먼저 읽을 문서 | 바로 이어 읽을 문서 | 이유 |
|---|---|---|---|
| "`왜` 직접 `new`하지 않고 주입받아요?" | [`IoC와 DI 기초`](./spring-ioc-di-basics.md) | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | 먼저 제어권과 결합도 이유를 잡고, 그다음 Spring이 실제로 Bean을 등록하고 연결하는 방법으로 내려간다 |
| "`bean`이 뭐예요?", "`component scan`이 뭐예요?" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | 이미 "왜 DI를 쓰나"는 넘기고, Bean 등록과 wiring 감각부터 잡는 편이 빠르다 |
| "`controller` 안 `service`는 누가 넣어요?" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | [`IoC와 DI 기초`](./spring-ioc-di-basics.md) | 실전 질문은 wiring에서 시작하지만, 읽고 나서도 "`왜`"가 남으면 IoC/DI primer로 한 칸만 되돌아가면 된다 |
| "`요청이 오면 controller/service/repository가 그때 만들어지나요?`" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | Bean 준비 시점과 요청 처리 시점을 같은 말로 보는 오해를 먼저 끊는다 |

<a id="처음-10분-라우트"></a>
## 처음 10분 라우트

처음에는 아래 4장만 읽어도 된다. 이 순서가 request pipeline, DI, transaction을 beginner 질문 기준으로만 묶어 준다.

> mental model: 요청은 MVC가 받고, 객체는 DI가 연결하고, DB 묶음은 `@Transactional`이 정한다.

| 지금 막힌 말 | 먼저 읽을 1장 | 바로 이어 읽을 1장 | 왜 이 순서가 안전한가 |
|---|---|---|---|
| "`DispatcherServlet`이 뭐예요?" | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | 요청 길찾기와 객체 조립을 같은 문제로 섞지 않게 해 준다 |
| "`왜 new 대신 주입해요?`" | [`IoC와 DI 기초`](./spring-ioc-di-basics.md) | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | DI의 이유를 먼저 잡고, Bean 등록과 wiring으로 내려가면 같은 말을 두 번 읽는 느낌이 줄어든다 |
| "`controller`랑 `service`는 누가 연결해요?" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | Bean 등록과 주입을 먼저 보고, 그다음 요청 장면 속 연결까지 다시 묶는다 |
| "`@Transactional`이 왜 안 먹죠?" | [`@Transactional 기초`](./spring-transactional-basics.md) | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | 옵션과 예외 케이스보다 먼저 service 경계가 요청 흐름 안에서 어디 붙는지 고정한다 |
| "`404`, `400`, DI 예외가 한 요청에서 다 섞여 보여요" | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | [`Spring \`404\`/\`405\` vs Bean Wiring Error Confusion Card`](./spring-404-405-vs-bean-wiring-confusion-card.md) | 같은 주문 요청도 "길찾기 / 값 채우기 / 객체 조립 / 트랜잭션 경계"로 먼저 자르게 돕는다 |

## 처음 10분 라우트 메모

`controller`도 Bean이고 `@Transactional`도 Spring이라 헷갈리면, [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md)나 [`IoC와 DI 기초`](./spring-ioc-di-basics.md)의 비교 표에서 질문 축부터 다시 자른다. 브라우저 상태가 먼저 걸리면 [`HTTP의 무상태성과 쿠키, 세션, 캐시`](../network/http-state-session-cache.md)로 잠깐 내려간다. primer를 읽고도 다음 한 걸음이 안 보이면 [`Spring primer 되돌아가기`](#spring-primer-되돌아가기)로 복귀하고, 카테고리 단위로 다시 고르고 싶으면 [`CS 루트 Quick Routes`](../../README.md#quick-routes)로 돌아간다.

<a id="spring-primer-되돌아가기"></a>
## Spring primer 되돌아가기

primer나 증상 카드에서 너무 빨리 deep dive로 내려간 느낌이 들면, 여기서 다시 "지금 질문이 어느 축인가"만 고른다.

| 지금 다시 막힌 말 | README에서 되돌아갈 곳 | 왜 이 복귀점이 안전한가 |
|---|---|---|
| "`404`, `400`, bean missing이 한 요청에서 다 섞여 보여요" | [`첫 판단 4축`](#첫-판단-4축) | MVC 길찾기, 바인딩, DI, 트랜잭션을 다시 분리해서 같은 오류처럼 읽지 않게 해 준다 |
| "`HTTP`, `302`, `304`, `cookie`가 먼저 헷갈려서 Spring 용어가 안 들어와요" | [`Network -> Spring handoff`](../network/README.md#network---spring-handoff) | Spring 내부 deep dive 대신 browser/network 축으로 한 칸 되돌아가게 해 준다 |
| "`controller -> service -> repository` 다음에 `save()`와 SQL은 어디서 봐요?" | [`Database First-Step Bridge`](../database/database-first-step-bridge.md) | Spring 안에서 더 파기보다 DB 첫 bridge로 넘겨 다음 카테고리 입구만 고정한다 |
| "문서가 많아서 다시 카테고리 단위로 고르고 싶어요" | [`처음 10분 라우트`](#처음-10분-라우트), [`CS 루트 Quick Routes`](../../README.md#quick-routes) | Spring primer 입구와 전체 네비게이터를 같이 보여 줘서 안전하게 복귀할 수 있다 |

## 첫 10분에서 넘기기

처음 4장을 다 보고도 막힐 때만 follow-up으로 내려간다. `self-invocation`, `rollback-only`, `REQUIRES_NEW`, `condition report`, `deadlock`, `timeout`, `observability` 같은 단어는 "첫 10분" 범위가 아니라는 신호다. 처음에는 deep dive 여러 장을 연달아 열지 말고, primer 1장과 증상 카드 1장만 묶는 정도로만 이동하면 된다.

1. [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md)
2. [`IoC와 DI 기초`](./spring-ioc-di-basics.md) 또는 [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md)
3. [`@Transactional 기초`](./spring-transactional-basics.md)
4. [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md)

DI 2번 칸은 질문 모양으로만 고른다.

- "`왜 DI를 써요?`, `왜 new 대신 주입해요?`"면 [`IoC와 DI 기초`](./spring-ioc-di-basics.md)
- "`bean`, `component scan`, `누가 연결해요?`"면 [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md)

## Beginner 입문 5편

- **Spring 5단계 시작점**
  - [`IoC와 DI 기초`](./spring-ioc-di-basics.md) — 제어 역전과 의존성 주입이 왜 필요한지
  - [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) — Bean 등록, component scan, configuration, proxy 감각을 "왜 DI 다음에 이 문서를 읽는지"까지 포함해 연결
  - [`Spring MVC 컨트롤러 기초`](./spring-mvc-controller-basics.md) — `DispatcherServlet` 흐름, `@RestController`, `@RequestMapping`
  - [`@Transactional 기초`](./spring-transactional-basics.md) — "요청 하나"와 "트랜잭션 하나"를 분리하고, 프록시를 타는 `public` service 진입점 감각을 먼저 잡는 primer
  - [`Spring Security 기초`](./spring-security-basics.md) — 인증 vs 인가, 401 vs 403, `HttpSecurity` 설정

`Spring Bean 생명주기 기초`는 이 5편 다음에 여는 편이 안전하다. beginner 첫 라우트에서 먼저 필요한 것은 lifecycle보다 "`왜` DI를 쓰고 Spring이 `어떻게` Bean을 연결하나"이기 때문이다.

## 첫 4장 뒤에만 여는 입문 확장

- **AOP·부트 자동구성·JPA·테스트**
  - [`AOP 기초`](./spring-aop-basics.md) — 처음에는 "annotation이 붙는 문은 프록시"라는 감각과 `this.method()`/`private`/직접 `new` 3문항만 잡고, 자세한 프록시 메커니즘은 관련 문서로 넘기는 입문 primer
  - [`Spring Boot 자동 구성 기초`](./spring-boot-autoconfiguration-basics.md) — starter, `@ConditionalOnMissingBean`, 자동 Bean 오버라이드, `ObjectMapper` customizer vs top-level bean 비교, `proxyBeanMethods` 30초 연결
  - [`Spring Data JPA 기초`](./spring-data-jpa-basics.md) — `JpaRepository`, 쿼리 메서드, Dirty Checking 입문
  - [`Spring Data Repository vs Domain Repository Bridge`](./spring-data-vs-domain-repository-bridge.md) — 처음 배우는데 `Repository`가 두 번 보여도 "`업무 계약` vs `프레임워크 도구`"로 먼저 분리
  - [`Spring 테스트 기초`](./spring-testing-basics.md) — 처음에는 `@SpringBootTest` / `@WebMvcTest` / `@DataJpaTest` 셋만 먼저 고르고, `@JsonTest` / `@RestClientTest` 같은 세부 slice는 관련 문서로 넘기는 primer
  - [`Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer`](./spring-custom-error-dto-to-problemdetail-handoff-primer.md) — "`팀 DTO로 충분한 시점`과 `Spring 표준 오류 바디가 의미를 갖기 시작하는 시점`"을 한 장으로 잇는 beginner bridge

예외 응답 입문은 아래 [`예외 응답 primer`](#예외-응답-primer)에서 `400`/`404`/`409`, `BindingResult`, `ProblemDetail` 흐름을 한 묶음으로 본다.

## 테스트와 트랜잭션 프록시 브리지

- 컨트롤러 응답만 빨리 보거나 "`@WebMvcTest` / `@DataJpaTest` / `@SpringBootTest` 중 뭐가 맞죠?"라면 [`Spring 테스트 기초`](./spring-testing-basics.md)부터 본다.
- "`처음`인데 `service bean not found`가 나요"라면 [`Spring Test Slice Scan Boundary 오해`](./spring-test-slice-scan-boundaries.md)로 가서 scan 고장보다 slice 경계를 먼저 의심한다.
- "`같은 OrderService인데 어떤 테스트에서는 가짜고, 어떤 테스트에서는 아예 없고, 어떤 테스트에서는 진짜로 떠요`"가 헷갈리면 [`Spring 테스트 기초`](./spring-testing-basics.md)의 비교표부터 보고 "`무엇을 띄웠나`"를 먼저 고정한다.
- 같은 주문 기능이라도 "`JSON + 상태 코드`"만 보면 `@WebMvcTest`, "`repository 쿼리`"면 `@DataJpaTest`, "`controller-service-repository 연결`"이면 `@SpringBootTest`라는 1장 예시는 [`Spring Test Slice Scan Boundary 오해`](./spring-test-slice-scan-boundaries.md)에서 바로 볼 수 있다.
- "`assertSame`은 맞는데 `@Transactional`이 왜 안 먹죠?"라면 [`Spring `@Transactional` Self-invocation 검증 테스트 브리지`](./spring-transactional-self-invocation-test-bridge-primer.md)로 가서 identity 테스트와 behavior 테스트를 먼저 분리한다.
- "`갑자기 테스트가 너무 느려졌어요`"가 먼저 보이면 [`Spring Test Slices와 Context Caching`](./spring-test-slices-context-caching.md)으로 가서 "무엇을 띄웠나"와 "왜 다시 띄우나"를 분리한다.
- beginner-safe 메모: 테스트 문서에서 `context cache`, `boundary leak`, `flush/clear`, `rollback visibility` 같은 단어가 먼저 보여도, 처음에는 해당 deep dive를 바로 읽지 말고 [`Spring 테스트 기초`](./spring-testing-basics.md) 또는 [`Spring Test Slice Scan Boundary 오해`](./spring-test-slice-scan-boundaries.md)로 돌아와 질문 축을 다시 고른다.

## 주문 테스트 3칸 분리

같은 주문 예제를 읽을 때도 먼저 아래 3칸으로만 자르면 길을 덜 잃는다.

| 지금 막힌 문장 | 먼저 붙일 질문 | 첫 문서 | 그다음 한 걸음 |
|---|---|---|---|
| "`@WebMvcTest`인데 service bean not found예요" | "웹 slice가 원래 service를 올리는 테스트인가?" | [`Spring 테스트 기초`](./spring-testing-basics.md) | [`Spring Test Slice Scan Boundary 오해`](./spring-test-slice-scan-boundaries.md) |
| "`service`는 있는데 `@Transactional`이 안 먹어요" | "테스트 종류가 아니라 프록시를 우회했나?" | [`@Transactional 기초`](./spring-transactional-basics.md) | [`Spring `@Transactional` Self-invocation 검증 테스트 브리지`](./spring-transactional-self-invocation-test-bridge-primer.md) |
| "`어제보다 테스트가 3배 느려졌어요`" | "비즈니스 로직보다 컨텍스트를 다시 띄우는 비용이 커졌나?" | [`Spring Test Slices와 Context Caching`](./spring-test-slices-context-caching.md) | [`Spring Test Property Override Boundaries`](./spring-test-property-override-boundaries-primer.md) |

## 테스트/트랜잭션 증상별 빠른 라우팅

| 지금 먼저 든 말 | 먼저 읽을 문서 | 왜 이 순서가 beginner-safe 한가 |
|---|---|---|
| "`controller` 응답 코드만 빨리 확인하고 싶어요" | [`Spring 테스트 기초`](./spring-testing-basics.md) | HTTP 요청 계약과 Bean/트랜잭션 문제를 섞지 않게 해 준다 |
| "`service bean not found`가 먼저 보여요" | [`Spring Test Slice Scan Boundary 오해`](./spring-test-slice-scan-boundaries.md) | 같은 package라도 slice가 service/repository를 일부러 빼는 경우를 먼저 잡게 해 준다 |
| "`@Transactional`이 안 먹는지, 테스트가 잘못된 건지 모르겠어요" | [`@Transactional 기초`](./spring-transactional-basics.md) | 프록시 경계 문제를 먼저 고정한 뒤 테스트 방식으로 내려가게 해 준다 |
| "`assertSame`은 통과했는데 rollback/commit 결과가 이상해요" | [`Spring `@Transactional` Self-invocation 검증 테스트 브리지`](./spring-transactional-self-invocation-test-bridge-primer.md) | identity 확인과 transaction behavior 확인을 바로 분리해 준다 |
| "`JSON` 필드명/날짜 포맷만 깨졌어요" | [`Spring `@JsonTest` and `@RestClientTest` Slice Boundaries`](./spring-jsontest-restclienttest-slice-boundaries.md) | controller 전체를 띄우지 않고 payload 계약만 따로 본다 |
| "`어제보다 테스트가 3배 느려졌어요`" | [`Spring Test Slices와 Context Caching`](./spring-test-slices-context-caching.md) | 비즈니스 로직보다 컨텍스트 재사용이 깨졌는지 먼저 보게 해 준다 |

## 초반 연결용 primer

- 요청 처리와 Bean 조립을 한 장으로 먼저 묶고 싶다면:
  - [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) — `DispatcherServlet`, controller/service/repository, component scan, DI, `application.yml` 읽기를 한 흐름으로 연결

## 트랜잭션 연결 primer

- transaction과 JPA 영속성 컨텍스트를 web/service/repository 한 장으로 먼저 묶고 싶다면:
  - [`Spring Persistence / Transaction Mental Model Primer`](./spring-persistence-transaction-web-service-repository-primer.md) — `@Transactional`, persistence context, `flush`, lazy loading, service 경계, controller DTO 반환 원칙을 초급자용 한 흐름으로 정리

## 요청 흐름 primer

- `DispatcherServlet`, `HandlerInterceptor`가 처음부터 같이 나와서 헷갈린다면:
  - [`Spring DispatcherServlet / HandlerInterceptor 입문 브리지`](./spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md) — "요청 진입 관문"과 "컨트롤러 전후 훅"만 먼저 구분한 뒤 MVC 기초로 연결

## 바인딩 primer

- 요청 한 번이 어디서 들어와 어디서 실패 응답으로 바뀌는지 한 장으로 잡고 싶다면:
  - [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) — 요청 진입부터 binding, 컨트롤러, 예외 응답까지 한 장으로 묶는 입문 문서
  - [`Spring Filter vs Spring Security Filter Chain vs HandlerInterceptor: 관리자 인증 입문 브리지`](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md) — `/admin/**`에서 `302 /login`/`401`/`403`과 그다음 `@RequestBody 400`을 먼저 가르는 bridge
  - [`Spring @ModelAttribute vs @RequestBody 초급 비교 카드`](./spring-modelattribute-vs-requestbody-binding-primer.md) — 0단계: 지금 질문이 query/form 바인딩인지 JSON body 바인딩인지 먼저 자르는 primer
  - [`Spring @RequestBody가 컨트롤러 전에 400 나는 이유`](./spring-requestbody-400-before-controller-primer.md) — 1단계: "`컨트롤러 로그 안 찍힘`", "`@RequestBody`인데 컨트롤러 전에 `400`이 나요", "`JSON parse error`가 보여요"처럼 body 파싱/DTO 변환 실패를 먼저 의심하는 first-hit 카드
  - [`Spring @RequestBody 415 Unsupported Media Type 초급 primer`](./spring-requestbody-415-unsupported-media-type-primer.md) — 1.5단계: "`json`인데 `415 Unsupported Media Type`가 떠요", "`Content-Type: application/json` 안 붙였는데 `415`예요", "`Content-Type` 때문에 막힌 것 같아요"처럼 검색어가 직접 `415`/헤더를 말할 때 바로 꽂히는 entrypoint

## 바인딩 첫 증상표

| 지금 보이는 첫 증상 | 첫 문서 | 왜 여기서 시작하나 |
|---|---|---|
| "`POST`인데 `/login`으로 가요", "`401`/`403`이 먼저 보여요" | [`Spring Filter vs Spring Security Filter Chain vs HandlerInterceptor: 관리자 인증 입문 브리지`](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md) | body 바인딩 전에 security/filter 경계부터 잘라야 한다 |
| "`query`/form인지 JSON body인지부터 헷갈려요" | [`Spring @ModelAttribute vs @RequestBody 초급 비교 카드`](./spring-modelattribute-vs-requestbody-binding-primer.md) | 같은 `400`이어도 값이 들어오는 자리부터 달라진다 |
| "`컨트롤러 로그 안 찍힘`", "`@RequestBody`인데 컨트롤러 전에 `400`이 나요", "`JSON parse error`가 보여요" | [`Spring @RequestBody가 컨트롤러 전에 400 나는 이유`](./spring-requestbody-400-before-controller-primer.md) | `Content-Type`이 아니라 body 값 해석/DTO 변환 실패 쪽을 먼저 보게 한다 |
| "`json`인데 `415 Unsupported Media Type`가 떠요", "`Content-Type: application/json` 안 붙였는데 `415`예요" | [`Spring @RequestBody 415 Unsupported Media Type 초급 primer`](./spring-requestbody-415-unsupported-media-type-primer.md) | `Content-Type` 계약 문제를 가장 짧게 찾게 한다 |

## 바인딩 primer follow-up

  - [`Spring @Valid는 언제 타고 언제 못 타는가: 400 첫 분기 primer`](./spring-valid-400-vs-message-conversion-400-primer.md) — 2단계: 변환 실패와 validation 실패를 가른다
  - [`Spring BindingResult가 있으면 400 흐름이 어떻게 달라지나`](./spring-bindingresult-local-validation-400-primer.md) — 3단계: 전역 예외와 컨트롤러 로컬 분기를 나눈다
  - [`Spring MethodArgumentNotValidException vs HandlerMethodValidationException 초급 브리지`](./spring-methodargumentnotvalidexception-vs-handlermethodvalidationexception-beginner-bridge.md) — 3.5단계: 같은 validation `400` 안에서 "`request body DTO 하나 검증`"과 "`method parameter validation`"을 한 표로 가른다
  - [`Spring LocalDate/LocalTime JSON 파싱 400 자주 나는 형식 모음`](./spring-localdate-localtime-json-400-cheatsheet.md) — 4단계: `date`/`time` 형식 오류를 빠르게 찾는다
  - [`Spring @RequestParam vs @PathVariable 초급 비교 카드`](./spring-requestparam-vs-pathvariable-beginner-card.md) — path 값과 query 조건이 헷갈릴 때만 본다

## 바인딩 follow-up 증상표

| `400` 이후 다시 나온 증상 | 첫 문서 | 바로 이어 읽을 문서 |
|---|---|---|
| "`왜 `@Valid` 안 타요?`", "`같은 `400`인데 뭐가 다른가요?`", "`@NotBlank`가 왜 안 먹어요?`" | [`Spring @Valid는 언제 타고 언제 못 타는가: 400 첫 분기 primer`](./spring-valid-400-vs-message-conversion-400-primer.md) | [`Spring @RequestBody가 컨트롤러 전에 400 나는 이유`](./spring-requestbody-400-before-controller-primer.md) |
| "`BindingResult` 있으면 뭐가 달라져요?`", "`왜 `MethodArgumentNotValidException` 안 나요?`", "`@Valid` 실패인데 컨트롤러 안으로 왜 들어와요?`", "`BindingResult` 붙였는데 왜 어떤 `400`은 여전히 컨트롤러 전에 끝나요?`" | [`Spring BindingResult가 있으면 400 흐름이 어떻게 달라지나`](./spring-bindingresult-local-validation-400-primer.md) | [`Spring 예외 처리 기초`](./spring-exception-handling-basics.md) |
| "`HandlerMethodValidationException`이 왜 나와요?", "`같은 validation 400인데 exception 이름이 달라요`" | [`Spring MethodArgumentNotValidException vs HandlerMethodValidationException 초급 브리지`](./spring-methodargumentnotvalidexception-vs-handlermethodvalidationexception-beginner-bridge.md) | [`Spring 예외 처리 기초`](./spring-exception-handling-basics.md) |
| "`2026/05/01` 보냈는데 `400`이 나요`", "`18시`, `오후 6시`, `6pm` 보내면 왜 안 되죠?`" | [`Spring LocalDate/LocalTime JSON 파싱 400 자주 나는 형식 모음`](./spring-localdate-localtime-json-400-cheatsheet.md) | [`Spring @RequestBody가 컨트롤러 전에 400 나는 이유`](./spring-requestbody-400-before-controller-primer.md) |
| "`그 validation 400 응답 바디를 어떤 계약으로 보여 줄까?`" | [`Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer`](./spring-custom-error-dto-to-problemdetail-handoff-primer.md) | [`Spring 예외 처리 기초`](./spring-exception-handling-basics.md) |

## 예외 응답 primer

- `400`과 `409`가 왜 다른지, 에러 바디를 어디서 맞출지 먼저 보고 싶다면:
  - [`Spring RoomEscape validation 400 vs business conflict 409 분리 primer`](./spring-roomescape-validation-400-vs-business-conflict-409-primer.md) — Bean Validation `400`과 서비스 충돌 `409`를 한 표로 가른다
  - [`Spring 예외 처리 기초`](./spring-exception-handling-basics.md) — `400`/`404`/`409`를 전역 정책과 함께 정리하는 primer
  - [`Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer`](./spring-custom-error-dto-to-problemdetail-handoff-primer.md) — 작은 API의 빠른 통일과 Spring 표준화 시점을 연결한다

## 필터와 인터셉터 primer

- `필터 vs 인터셉터`가 처음부터 헷갈린다면:
  - [`Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries`](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md) — "`필터는 서블릿 입구`, `인터셉터는 컨트롤러 앞뒤`, `ControllerAdvice`는 예외 응답" 큰 그림부터 잡는다

## 처음이면 여기까지만 읽는다

처음 읽는 단계에서는 deep dive 제목이 보여도 바로 내려가지 않는 편이 안전하다. 아래 네 축만 먼저 잡고, 막힌 증상이 생길 때만 follow-up 링크로 이동한다.

| 먼저 잡을 축 | primer | 여기서 멈춰도 되는 이유 | 더 깊게 갈 때 |
|---|---|---|---|
| 요청이 어디로 들어오나 | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | `Filter -> DispatcherServlet -> binding -> controller` 흐름만 알아도 `400/404`를 덜 섞는다 | [`Spring MVC 요청 생명주기`](./spring-mvc-request-lifecycle.md) |
| 객체를 누가 연결하나 | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | component scan, 생성자 주입, 프록시 감각만 먼저 잡으면 된다 | [`Spring Component Scan 실패 패턴`](./spring-component-scan-failure-patterns.md) |
| DB 작업을 어디까지 묶나 | [`@Transactional 기초`](./spring-transactional-basics.md) | 옵션보다 "프록시를 탔는가"를 먼저 보는 습관이 중요하다 | [`Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only`](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md) |
| 요청 처리와 객체 연결이 왜 같이 보이나 | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | MVC, DI, 트랜잭션을 한 장면에서 분리해 본다 | [`Spring MVC -> JDBC/트랜잭션 -> DI/AOP 전환 오해 체크리스트`](./spring-mvc-jdbc-transaction-di-aop-transition-checklist.md) |

## 같은 요청에서 고르기

같은 `POST /orders` 장면도 어디가 막혔는지에 따라 출발 문서가 달라진다.

| 지금 먼저 든 생각 | 먼저 읽을 primer | 한 줄 기준 |
|---|---|---|
| "`/orders`가 왜 이 컨트롤러로 안 가지?" | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | URL 길찾기면 MVC부터 본다 |
| "`OrderService`는 누가 넣어 줬지?" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | 객체 연결이면 Bean/DI부터 본다 |
| "`@Transactional`이 왜 여기선 안 먹지?" | [`@Transactional 기초`](./spring-transactional-basics.md) | 작업 묶기면 프록시 경계부터 본다 |
| "셋이 한꺼번에 섞여 보여요" | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | 한 요청 장면에서 MVC, DI, 트랜잭션을 다시 분리한다 |

## 증상별 첫 문서

| 지금 막힌 말 | 먼저 읽을 문서 | 바로 이어 읽을 문서 | 왜 이 순서가 안전한가 |
|---|---|---|---|
| "`DispatcherServlet`이 뭐예요?" | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | 요청 길찾기와 객체 준비 흐름을 먼저 분리한다 |
| "`controller`랑 `service`는 누가 연결해요?" | [`Spring Bean과 DI 기초`](./spring-bean-di-basics.md) | [`Spring Component Scan 실패 패턴`](./spring-component-scan-failure-patterns.md) | component scan, 생성자 주입, 빈 누락 증상을 한 축으로 묶는다 |
| "`@Transactional`이 왜 안 먹죠?" | [`@Transactional 기초`](./spring-transactional-basics.md) | [`Spring Self-Invocation 공통 오해 1페이지 카드`](./spring-self-invocation-transactional-only-misconception-primer.md) | 옵션보다 먼저 `this.method()`/`private`/직접 `new`를 걸러 낸다 |
| "`400`이 컨트롤러 전에 나요" | [`Spring MVC 요청 생명주기 기초`](./spring-mvc-request-lifecycle-basics.md) | [`Spring @RequestBody가 컨트롤러 전에 400 나는 이유`](./spring-requestbody-400-before-controller-primer.md) | 바인딩 실패와 비즈니스 실패를 먼저 자른다 |
| "`404`, DI 예외, `400`, 트랜잭션 문제가 한꺼번에 섞여요" | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md#7-1-같은-orders-요청인데도-먼저-보는-곳이-다르다) | [`Spring MVC -> JDBC/트랜잭션 -> DI/AOP 전환 오해 체크리스트`](./spring-mvc-jdbc-transaction-di-aop-transition-checklist.md) | 같은 요청 장면에서도 "길찾기 / 객체 조립 / 값 채우기 / 트랜잭션 경계"를 먼저 분리하게 돕는다 |

## 입문 라우트

- HTTP에서 Spring wiring으로 처음 넘어오는 입문 루트:
  - [`HTTP 메서드와 REST 멱등성 입문`](../network/http-methods-rest-idempotency-basics.md) -> [`Spring MVC 컨트롤러 기초`](./spring-mvc-controller-basics.md) -> [`IoC와 DI 기초`](./spring-ioc-di-basics.md) -> [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md)
  - 목적: "요청 의도(HTTP)"와 "요청 진입(MVC)"과 "객체 연결(DI)"을 한 번에 연결해 초반 문맥 전환 비용을 줄인다.

- MVC -> JDBC/트랜잭션 -> DI/AOP 사다리에서 자꾸 섞인다면:
  - [`Spring MVC -> JDBC/트랜잭션 -> DI/AOP 전환 오해 체크리스트`](./spring-mvc-jdbc-transaction-di-aop-transition-checklist.md) — "요청 처리 / DB 호출 / 트랜잭션 경계 / 프록시 적용" 4칸으로 먼저 쪼개서 초급자가 deep dive 오진입 전에 안전한 다음 문서를 고르게 돕는다.

## 전환 구간 빠른 질문표

| 전환 구간 | 먼저 붙잡을 질문 | primer | follow-up |
|---|---|---|---|
| HTTP -> MVC | "이 HTTP 요청이 Spring 코드에서 어디서 처음 handler/controller로 넘어가나?" | [`HTTP 메서드와 REST 멱등성 입문`](../network/http-methods-rest-idempotency-basics.md) -> [`Spring MVC 컨트롤러 기초`](./spring-mvc-controller-basics.md) | [`Spring 요청 파이프라인과 Bean Container 기초`](./spring-request-pipeline-bean-container-foundations-primer.md) |
| MVC -> JDBC/transactions -> DI/AOP | "내가 지금 헷갈리는 게 요청 처리, DB 호출, 트랜잭션 경계, 프록시 중 무엇인가?" | [`Spring MVC -> JDBC/트랜잭션 -> DI/AOP 전환 오해 체크리스트`](./spring-mvc-jdbc-transaction-di-aop-transition-checklist.md) | [`JDBC / JPA / MyBatis 기초`](../database/jdbc-jpa-mybatis-basics.md) -> [`@Transactional 기초`](./spring-transactional-basics.md) -> [`AOP 기초`](./spring-aop-basics.md) |
| JDBC -> DI/AOP | "이 JDBC 호출이 왜 service/bean/proxy 문맥으로 감싸져 보이나?" | [`JDBC / JPA / MyBatis 기초`](../database/jdbc-jpa-mybatis-basics.md) -> [`IoC와 DI 기초`](./spring-ioc-di-basics.md) | [`Spring @Transactional 기초`](./spring-transactional-basics.md) -> [`AOP 기초`](./spring-aop-basics.md) |

## 기본 primer 묶음

- 기본 primer부터 읽고 싶다면:
  - `Spring Bean과 DI 기초`
  - `Spring @Primary vs @Qualifier vs 컬렉션 주입 결정 가이드`
  - `Spring @ConditionalOnMissingBean vs @Primary 오해 분리`
  - `Spring @ConditionalOnBean activation vs DI 후보 선택`
  - `Spring Bean 이름 규칙과 rename 함정 입문`
  - `커스텀 @Qualifier 입문`
  - `Spring Full vs Lite Configuration 예제`
  - `Spring Legacy Self-invocation(내부 호출) 탐지 카드`
  - `Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드`
  - `Spring @Transactional Self-invocation 검증 테스트 브리지`
  - `Spring Self-Invocation 공통 오해 1페이지 카드`
  - `Spring 런타임 전략 선택과 @Qualifier 경계`
  - `Spring Configuration vs Auto-configuration 입문`

## 기본 primer 묶음 확장

- 기본 primer를 더 넓히고 싶다면:
  - `Spring Boot Customizer vs Bean 교체 입문` — `ObjectMapper`/`WebClient.Builder` before-after 코드쌍으로 "옵션 추가"와 "owner 교체"를 첫 읽기에서 바로 구분
  - `Spring Starter Dependency Map 입문`
  - `Spring Property Source 우선순위 빠른 판별`
  - `Spring External Config File Precedence`
  - `Spring Relaxed Binding Env Var Cheatsheet`
  - `Spring @ConditionalOnClass classpath 함정`
  - `Spring @ConditionalOnProperty 기본값 함정`
  - `Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ` — starter 추가 뒤 `existing bean`, customizer, 직접 bean 등록을 `@ConditionalOnMissingBean` back-off 관점에서 먼저 가르는 beginner FAQ
  - `Spring Component Scan 실패 패턴`
  - `Spring scanBasePackages vs @Import 선택 기준`
  - `Spring JPA Scan Boundary 함정`
  - `DI 예외 빠른 판별`
  - `IoC 컨테이너와 DI`
  - `AOP 기초`
  - `AOP와 프록시 메커니즘`
  - `Spring MVC 요청 생명주기`
  - `Spring Boot 자동 구성`
  - `Spring Boot Condition Evaluation Report 첫 디버그 체크리스트`
  - `Spring Security 아키텍처`
  - `cookie`, `session`, `JWT` 개념에서 올라오는 beginner route라면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md) -> `Spring Security 아키텍처` 순으로 먼저 맞춘다.

## 트랜잭션과 persistence 라우트

- 트랜잭션 / persistence cluster로 바로 들어가려면:
  - `@Transactional 기초`를 먼저 끝낸 뒤에만 [`Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only`](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)로 내려간다
  - `DB Lock Wait / Deadlock vs Spring Proxy / Rollback`
  - `[playbook] Spring Transaction Debugging Playbook`
  - 초급자가 `REQUIRES_NEW`, `rollbackFor`, `readOnly`부터 먼저 열고 있으면 [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)로 내려가 `this.method()`/`private`/직접 `new` 30초 체크를 먼저 끝낸다.
  - `Spring Persistence Context Flush / Clear / Detach`
  - `dirty read`, `write skew`, `phantom`, `왜 @Transactional이 안 먹지`, `왜 안 롤백되지`가 같이 섞이면 처음부터 `REQUIRES_NEW`, rollback-only, readOnly, routing-datasource까지 한 번에 열지 말고 core ladder를 `트랜잭션 격리수준과 락` -> [`@Transactional 기초`](./spring-transactional-basics.md) -> [`Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only`](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md) -> [`Spring Service-Layer Transaction Boundary Patterns`](./spring-service-layer-transaction-boundary-patterns.md) 순으로 먼저 맞춘다.

## 트랜잭션 증상별 follow-up

- core ladder 뒤 follow-up beginner branch는 증상별로 고른다.
  - `audit는 남고 본 작업은 롤백`, `REQUIRES_NEW`, `partial commit`이면 `Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies` -> `Spring TransactionSynchronization Ordering / Suspend / Resume`
  - `UnexpectedRollbackException`, `transaction marked rollback-only`, `catch 했는데 마지막에 터짐`이면 `Spring UnexpectedRollback / Rollback-Only` -> `[playbook] Spring Transaction Debugging Playbook`
  - `readOnly면 안전한가`, `dirty checking`, `flush mode`가 헷갈리면 `Spring Transaction Isolation / ReadOnly Pitfalls`
  - `inner readOnly인데 writer pool`, `reader route가 안 탄다`, `read/write split`이면 `Spring Routing DataSource와 JDBC Exception Translation`
- `lock wait`, `deadlock`, `UnexpectedRollbackException`, `self invocation`이 한 문장에 같이 섞이면 `DB Lock Wait / Deadlock vs Spring Proxy / Rollback`부터 보고 DB branch와 Spring branch를 먼저 가른다

## 요청 처리와 운영 라우트

- 요청 처리 / 운영 cluster로 바로 들어가려면:
  - `Spring MVC 요청 생명주기`
  - `Spring MVC Async Dispatch`
  - `Spring ProblemDetail Before-After Commit Matrix`
  - `Spring HttpMessageNotWritableException Failure Taxonomy`
  - `Spring ProblemDetail vs /error Handoff Matrix`
  - `Spring Request Lifecycle Timeout / Disconnect Bridge`
  - `Spring Async Timeout vs Disconnect Decision Tree`
  - `Spring Servlet Container Disconnect Exception Mapping`
  - `Spring Partial-Response Access Log Interpretation`
  - `Spring HTTP/2 Reset Attribution`
  - `Spring StreamingResponseBody / SSE Commit Lifecycle`
  - `Spring ResponseBodyAdvice on Streaming Types`

## 요청 처리와 운영 follow-up

- 운영형 follow-up을 더 내려가려면:
  - `[playbook] Spring Async MVC Streaming Observability Playbook`
  - `Spring SSE Disconnect Observability Patterns`
  - `Spring ResponseBodyEmitter Media-Type Boundaries`
  - `Spring MVC Flux JSON vs NDJSON and SSE Adaptation`
  - `Spring Streaming Client Parsing Matrix`
  - `Spring SSE Proxy Idle-Timeout Matrix`
  - `Spring MVC SseEmitter vs WebFlux SSE Timeout Behavior`
  - `Spring SseEmitter Timeout Callback Race Matrix`
  - `Spring SSE Buffering / Compression Checklist`
  - `Spring SSE Replay Buffer / Last-Event-ID Recovery`
  - `Spring Observability, Micrometer, Tracing`
  - `499`, `broken pipe`, `client disconnect`, `connection reset`, `proxy timeout`처럼 disconnect symptom이 먼저 보이면 [Spring Request Lifecycle Timeout / Disconnect Bridge](#spring-bridge-request-lifecycle-timeout-disconnect) -> [Spring Async Timeout vs Disconnect Decision Tree](#spring-async-timeout-vs-disconnect-decision-tree) -> [Spring Servlet Container Disconnect Exception Mapping](#spring-servlet-container-disconnect-exception-mapping) -> [Network: Request Lifecycle Upload Disconnect](../network/README.md#network-bridge-request-lifecycle-upload-disconnect)

## Cross-domain 라우트

- [Spring + Network](../../rag/cross-domain-bridge-map.md#spring--network) route로 바로 들어가려면:
  - [Spring Request Lifecycle Timeout / Disconnect Bridge](#spring-bridge-request-lifecycle-timeout-disconnect)
  - [Spring Async Timeout vs Disconnect Decision Tree](#spring-async-timeout-vs-disconnect-decision-tree)
  - [Spring Partial-Response Access Log Interpretation](#spring-partial-response-access-log-interpretation)
  - [Network: Request Lifecycle Upload Disconnect](../network/README.md#network-bridge-request-lifecycle-upload-disconnect)
  - [Network: Edge Status Timeout Control Plane](../network/README.md#network-bridge-edge-status-timeout-control-plane)

## Cross-domain Security 라우트

<a id="spring-security-ladder"></a>
- [Spring + Security](../../rag/cross-domain-bridge-map.md#spring--security) route로 바로 들어가려면:
  - `cookie`, `session`, `JWT`는 아는데 `SecurityContextRepository`, `SavedRequest`, `hidden JSESSIONID`가 갑자기 등장하면 [Cross-Domain Bridge Map: HTTP Stateless / Cookie / Session / Spring Security](../../rag/cross-domain-bridge-map.md#bridge-http-session-security-cluster) route를 먼저 탄다.
  - 먼저 아래 2문답 카드로 `redirect / navigation memory`와 `server persistence / session mapping`을 갈라 놓고 시작하면 beginner가 Spring deep dive 입구를 더 빨리 고른다.

    | 2문답 | 예라면 | 바로 갈 문서 | 읽고 나서 돌아올 곳 |
    |---|---|---|---|
    | 로그인 전 URL로 다시 보내 주는 동작이 이상한가? `302 /login`, `saved request bounce`, `원래 URL 복귀 실패`, `복귀는 됐는데 403`가 먼저 보이나? | `redirect / navigation memory`부터 보고, 복귀 직후 `403`이면 `SavedRequest`와 역할 매핑을 두 단계로 자른다 | [Spring RequestCache / SavedRequest](#spring-bridge-requestcache-savedrequest) -> [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md) | [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) |
    | cookie는 브라우저에 있거나 request에 실리는데, 다음 요청에서 계속 anonymous인가? `hidden JSESSIONID`, `cookie exists but session missing`, `next request anonymous after login`이 먼저 보이나? | `server persistence / session mapping` | [Spring Security 예외 번역과 세션 경계](#spring-bridge-security-session-boundary) | [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) |

## Cross-domain Security follow-up

  - 한 줄 mental model: `SavedRequest`는 "어디로 다시 보낼까"를 기억하는 쪽이고, `SecurityContextRepository`/session mapping은 "다음 요청에서 누구였지"를 복원하는 쪽이다.
  - `SavedRequest`, `saved request bounce`, `browser 401 -> 302 /login bounce`, `원래 URL 복귀`, `복귀는 됐는데 403`가 먼저 보이면 고정 label은 `redirect / navigation memory`다. [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)에서 primer ladder를 한 번 탄 뒤 [Spring RequestCache / SavedRequest](#spring-bridge-requestcache-savedrequest) anchor로 들어가고, 복귀 직후 final `403`이면 바로 [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)로 이어 간다.
  - `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login`이 먼저 보이면 고정 label은 `server persistence / session mapping`이다. [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)에서 primer ladder를 한 번 탄 뒤 [Spring Security 예외 번역과 세션 경계](#spring-bridge-security-session-boundary) anchor로 들어간다.
  - [Spring Security 예외 번역과 세션 경계](#spring-bridge-security-session-boundary)
  - [Spring RequestCache / SavedRequest](#spring-bridge-requestcache-savedrequest)
  - [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
  - [Security: Session / Boundary / Replay](../security/README.md#session--boundary--replay)

## 디버깅과 문서 역할

- 운영 디버깅 절차가 먼저 필요하면:
  - `[playbook] Spring Transaction Debugging Playbook`
  - `[playbook] Spring Async MVC Streaming Observability Playbook`
  - `[playbook] Spring Startup Bean Graph Debugging Playbook`
- 문서 역할이 헷갈리면:
  - [Navigation Taxonomy](../../rag/navigation-taxonomy.md)
  - [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)

## Spring 요청 파이프라인과 Bean Container 기초

> `DispatcherServlet`, controller/service/repository 역할, component scan, DI, `application.yml` 설정 읽기를 "요청은 MVC가 받고 객체는 컨테이너가 준비한다"는 한 장의 그림으로 묶는 beginner bridge primer

- beginner-safe handoff: "`처음` 백엔드 요청 흐름을 잡는 중인데 `브라우저 -> controller -> database`가 한 장면으로 안 그려진다"면 [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) -> [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md) -> [Database First-Step Bridge](../database/database-first-step-bridge.md) 순서로만 내려간다.
- symptom phrase anchors: `request -> controller -> database flow`, `처음 Spring 다음 DB`, `save()는 보이는데 그 전에 뭐가 와요`, `왜 SQL 전에 controller/service가 보여요`
- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)

## Spring MVC -> JDBC/트랜잭션 -> DI/AOP 전환 오해 체크리스트

> MVC에서 JDBC/트랜잭션, 다시 DI/AOP로 넘어갈 때 "request 처리", "DB 호출", "transaction boundary", "proxy 적용"을 한 칸씩 분리해 초반 deep dive 오진입을 줄이는 1페이지 bridge다.

- [Spring MVC -> JDBC/트랜잭션 -> DI/AOP 전환 오해 체크리스트](./spring-mvc-jdbc-transaction-di-aop-transition-checklist.md)
- beginner-safe ladder: [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md) -> [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md) -> [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) -> [@Transactional 기초](./spring-transactional-basics.md)
- [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md)
- [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)
- [트랜잭션 격리 수준 기초](../database/transaction-isolation-basics.md)
- [IoC와 DI 기초](./spring-ioc-di-basics.md)
- [AOP 기초](./spring-aop-basics.md)
- [@Transactional 기초](./spring-transactional-basics.md)

## Spring Bean과 DI 기초

> Bean 등록, 생성자 주입, component scan, `@Bean`, 프록시 감각, `@Primary`/`@Qualifier` 후보 선택까지 한 번에 잡는 입문용 primer

- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다](./spring-primary-vs-bean-override-primer.md)
- [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)

## Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드

> `@Primary`/`@Qualifier`/collection과 runtime router를 먼저 갈라서, `found 2`인지 "요청마다 선택"인지에 따라 첫 문서를 바로 고르게 돕는 entrypoint다

| 지금 보이는 신호 | 먼저 열 문서 | 선택 기준 한 줄 |
|---|---|---|
| 후보 0개 | [Spring Bean과 DI 기초](./spring-bean-di-basics.md) | 선택 전 문제보다 bean 등록/scan 누락을 먼저 본다 |
| 후보 2개 | [`@Primary` vs `@Qualifier` vs 컬렉션 주입](./spring-primary-qualifier-collection-injection-decision-guide.md) | 같은 타입 bean이 둘 이상이면 주입 규칙부터 정한다 |
| 요청마다 선택 | [런타임 전략 선택과 `@Qualifier` 경계](./spring-runtime-strategy-router-vs-qualifier-boundaries.md) | 요청 값이 바뀌면 고정 wiring이 아니라 runtime router 쪽이다 |

- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)

## Spring `@Primary` vs Bean Override 입문

> 같은 타입 후보가 여러 개라서 기본 주입 대상을 고르는 문제와, 같은 bean 이름이 겹쳐 등록 단계에서 충돌하는 문제를 beginner 기준으로 먼저 분리한다

- [Spring `@Primary` vs Bean Override Primer: 주입 우선순위와 bean 이름 충돌은 다른 문제다](./spring-primary-vs-bean-override-primer.md)
- [Spring `spring.main.allow-bean-definition-overriding` Boundaries Primer: 테스트에서는 언제 괜찮고, 운영 기본값으로는 왜 위험한가](./spring-allow-bean-definition-overriding-test-boundaries-primer.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)
- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)

## Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리

> auto-configuration이 기본 bean 생성을 물러서는 문제와, 이미 등록된 후보 중 기본 주입 대상을 고르는 문제를 짧은 비교표와 예제로 분리한다

- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring `@ConditionalOnBean` 경계 노트: activation과 DI 후보 선택은 다르다](./spring-conditionalonbean-activation-vs-di-candidate-selection-primer.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md) - 재시작 가능하면 `--debug`, 떠 있는 앱을 유지해야 하면 `conditions`부터 고르는 beginner 분기표
- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)

ConditionEvaluationReport를 읽다가 `existing bean found`를 보면 `@Primary`로 해결하려 하기 전에 "지금 보는 게 등록 단계인지, 주입 단계인지"부터 먼저 가른다.

## Spring `@ConditionalOnBean` activation vs DI 후보 선택

> `@ConditionalOnBean`이 bean 존재 여부로 등록 경로를 여는 일과, 실제 생성자/`@Bean` 파라미터에 어떤 bean을 주입할지 고르는 일을 beginner 기준으로 분리한다

- [Spring `@ConditionalOnBean` 경계 노트: activation과 DI 후보 선택은 다르다](./spring-conditionalonbean-activation-vs-di-candidate-selection-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md) - `--debug`와 `conditions`의 첫 진입 타이밍을 초급자 기준으로 나눠 본다
- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)

`name`/`type`/`annotation` 속성이 모두 bean lookup 기준이라는 점, 그리고 그 match가 주입 대상 자동 선택과 다르다는 점을 짧은 표와 예제로 분리해 둔 entrypoint다.

## Spring Bean 이름 규칙과 rename 함정 입문

> 이름 없는 `@Component`/`@Bean`의 기본 이름 규칙, alias, 문자열 `@Qualifier`가 bean 이름과 엮이는 방식, rename 때 깨지는 지점을 beginner 기준으로 정리한다. 특히 Kotlin `@Bean` 함수명 rename이 기본 bean name과 문자열 주입을 같이 흔드는 함정을 짧은 비교표와 예제로 바로 설명한다.

- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)

## 커스텀 `@Qualifier` 입문

> `NoUniqueBeanDefinitionException` 대응이나 bean rename 이후 문자열 `@Qualifier` 흔들림을 겪을 때, 이름 계약에서 역할 annotation 계약으로 넘어가는 기준을 작은 예제로 정리한다.
> `@Qualifier`가 반복될수록 "같은 문제를 더 파는 중인지, runtime router 경계로 넘어가야 하는지"를 초급 기준으로 먼저 가르는 entrypoint다.
> 문서 상단의 "1분 비교 카드", "실패 증상 한눈표", "역방향 안내" 블록에서 bean naming primer, DI 예외 판별 문서, runtime router 문서로 바로 점프할 수 있게 정리했다.

- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
- [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)

## Spring 런타임 전략 선택과 `@Qualifier` 경계

> 처음 배우는데 `@Qualifier`와 `Map<String, Bean>` 중 언제 쓰는지 헷갈릴 때, 고정 wiring과 요청별 전략 선택을 한 번에 가르는 beginner boundary primer
> 큰 그림은 단순하다. `@Qualifier`는 "앱이 뜰 때 어떤 bean을 꽂을지" 고르는 쪽이고, runtime router는 "요청마다 어떤 구현체를 실행할지" 고르는 쪽이다. 문서 앞쪽의 주의 미니 박스에서 `channel -> bean name` 직접 매핑 같은 초급자 실수를 먼저 끊고, 그 다음 domain key registry / selector primer로 이어지게 정리했다.

- [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
- [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](../design-pattern/bean-name-vs-domain-key-lookup.md)
- [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](../design-pattern/factory-selector-resolver-beginner-entrypoint.md)

## Spring Configuration vs Auto-configuration 입문

> "`service`/`repository` 같은 우리 코드면 scan, 외부 객체 조립이면 `@Bean`, Boot 기본값이면 auto-configuration"이라는 초급자용 선택표를 먼저 세운 뒤, `@Configuration`, `@Bean`, `proxyBeanMethods`를 Boot 문서로 넘어가기 전 한 칸 작은 브리지로 연결한다

- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md) - Java/Kotlin 나란히, Kotlin expression body vs 파라미터 주입 차이, `assertSame` / `assertNotSame`를 한 표로 바로 연결해 읽는다
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)
- [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)

## Spring Legacy Self-invocation(내부 호출) 탐지 카드

> `@Configuration` 클래스의 legacy `@Bean` self-invocation(내부 호출)을 `rg` 기반 2단계 후보 탐지와 리뷰 체크 5개로 빠르게 걸러내고, `self-call`을 같은 뜻의 옛 표기로 묶어 첫 읽기 혼선을 줄인 beginner QA 카드

처음 보면 `self-call`과 `self-invocation(내부 호출)`을 같은 뜻으로 묶고 시작하면 된다.
초급자 추천 흐름은 "문제 후보를 찾기 -> 테스트로 고정하기 -> 구조를 이해하기" 순서다.

### self-call 3단계 묶음 표

처음 드는 질문 하나만 고르고 바로 옆 문서로 들어가면 된다.

| 단계 | 지금 드는 첫 질문 | 바로 갈 문서 | 읽고 나면 |
|---|---|---|---|
| 1. 탐지 | 리뷰에서 `self-call`, `self invocation`, `@Bean 직접 호출`이 보이는데 뭐가 문제인지 아직 모르겠다 | [Spring Legacy Self-invocation(내부 호출) 탐지 카드](./spring-legacy-configuration-bean-self-call-detection-card.md) | 위험 패턴을 `rg` 기준으로 먼저 추려 "지금 진짜 같은 클래스 내부 호출 문제인가"를 빠르게 가른다 |
| 2. 검증 | 후보는 찾았지만 수정 전후 차이를 테스트로 어떻게 고정할지 모르겠다 | [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드](./spring-self-call-verification-test-mini-guide.md) | `assertNotSame` / `assertSame`으로 문제 상태와 수정 완료 상태를 눈에 보이게 확인한다 |
| 3. 이해 | 왜 full/lite 설정과 `proxyBeanMethods`가 엮이는지 구조까지 같이 이해하고 싶다 | [Spring Full vs Lite Configuration 예제](./spring-full-vs-lite-configuration-examples.md) | self-call이 왜 생기고 파라미터 주입이 왜 안전한지 설정 방식 차이까지 한 번에 묶는다 |

## self-call 관련 문서 묶음

- [Spring Legacy Self-invocation(내부 호출) 탐지 카드: `@Configuration`의 위험한 `@Bean` 직접 호출 빠른 점검](./spring-legacy-configuration-bean-self-call-detection-card.md)
- [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드: `assertSame` / `assertNotSame`로 수정 전후를 바로 확인하기](./spring-self-call-verification-test-mini-guide.md)
- [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md) - full/lite와 테스트 기대값을 검증 뒤 다시 묶어 보는 entrypoint
- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)

## Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드

> legacy `@Bean` self-invocation(내부 호출)을 발견한 뒤 "수정 전엔 왜 위험했고, 수정 후엔 뭐가 달라졌는지"를 `assertNotSame` / `assertSame` 한 쌍으로 바로 눈에 보이게 만드는 beginner test primer. Java 중심 설명에 Kotlin `@Bean` 설정 전후 예제와 self-check 오답 포인트 1줄 해설까지 붙여 초급자가 복붙 뒤 바로 이해를 닫을 수 있게 다듬었다.

바로 앞 단계가 비어 있으면 이 순서로 되돌아가면 된다: 탐지 카드 -> full/lite 예제 -> 검증 테스트 가이드.

- [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드: `assertSame` / `assertNotSame`로 수정 전후를 바로 확인하기](./spring-self-call-verification-test-mini-guide.md)
- [Spring Legacy Self-invocation(내부 호출) 탐지 카드: `@Configuration`의 위험한 `@Bean` 직접 호출 빠른 점검](./spring-legacy-configuration-bean-self-call-detection-card.md)
- [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)
- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가](./spring-transactional-self-invocation-test-bridge-primer.md)

## Spring `@Transactional` Self-invocation 검증 테스트 브리지

> `@Bean` self-call에서 쓰는 identity 테스트와 `@Transactional` self-invocation에서 필요한 behavior 테스트를 초급자 기준으로 먼저 분리해, `assertSame`을 잘못 들고 들어오는 혼선을 줄이는 beginner bridge primer

- [Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가](./spring-transactional-self-invocation-test-bridge-primer.md)
- [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드: `assertSame` / `assertNotSame`로 수정 전후를 바로 확인하기](./spring-self-call-verification-test-mini-guide.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
- [@Transactional 기초: 요청 하나와 트랜잭션 하나를 분리하고, `this.method()`/`private`/직접 `new`를 먼저 거르는 프록시 우선 입문](./spring-transactional-basics.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)

## Spring Self-Invocation 공통 오해 1페이지 카드

> "`@Transactional`만 문제"라는 초급자 오해를 먼저 끊고, self-invocation을 프록시 기반 annotation 공통 규칙으로 다시 잡아 고급 매트릭스 진입 전에 1분 프라이머로 연결한다. `@Async`는 같은 스레드 실행 로그 전/후 예제로 프록시 우회 여부를 바로 확인하게 보강했고, 문서 후반 `수리 패턴 미니 카드`에서 `bean split` / `facade-worker` / `self-injection`을 한 표로 비교해 첫 수리 선택을 돕는다.

- [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
- [Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가](./spring-transactional-self-invocation-test-bridge-primer.md)
- [Spring `@Async` 내부 호출 증상 카드: 같은 스레드 로그를 async 설정 버그로 오해할 때](./spring-async-self-invocation-same-thread-symptom-card.md)
- [AOP 기초: 관점 지향 프로그래밍이 왜 필요한가](./spring-aop-basics.md)
- [@Transactional 기초: 요청 하나와 트랜잭션 하나를 분리하고, `this.method()`/`private`/직접 `new`를 먼저 거르는 프록시 우선 입문](./spring-transactional-basics.md)
- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)

## Spring `@Async` 내부 호출 증상 카드

> `@Async` 자체 규칙은 들어왔지만, 같은 스레드 로그를 볼 때마다 `@EnableAsync`나 executor 설정 버그로 바로 오진하는 초급자를 위해 만든 follow-up card다. "로그가 같으면 설정 문제"가 아니라 "먼저 프록시 정문을 탔는가"를 확인하게 짧은 전후 코드와 증상 표로 고정한다.

- [Spring `@Async` 내부 호출 증상 카드: 같은 스레드 로그를 async 설정 버그로 오해할 때](./spring-async-self-invocation-same-thread-symptom-card.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
- [AOP 기초: 관점 지향 프로그래밍이 왜 필요한가](./spring-aop-basics.md)
- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
- [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)

## Spring Boot Customizer vs Bean 교체 입문

> `ObjectMapper`, `RestClient.Builder`, `WebClient.Builder` 같은 Boot 상위 bean을 건드릴 때 "기본 조립 위에 옵션을 얹는가, 생성 책임 전체를 가져가는가"를 beginner 기준으로 먼저 가르고, `ObjectMapper`/`WebClient.Builder` before-after 코드쌍으로 왜 customizer가 더 안전한지 바로 체감하게 한다

- [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `RestClient.Builder`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)
- [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)
- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring RestClient vs WebClient Lifecycle Boundaries](./spring-restclient-vs-webclient-lifecycle-boundaries.md)

## Spring Property Source 우선순위 빠른 판별

> 같은 key가 `application.yml`, profile 파일, env var, command-line, test property에 동시에 있을 때 "가장 높은 source 하나가 최종 값"이라는 beginner mental model과 표로 빠르게 판별한다

- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring External Config File Precedence Primer: packaged `application.yml`, external file, `spring.config.location`, `spring.config.import`](./spring-external-config-file-precedence-primer.md)
- [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
- [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)

## Kotlin `@ConfigurationProperties` 탐지 보조 노트

> Kotlin `data class`와 Boot 3 생성자 바인딩 문법 때문에 "`@ConfigurationProperties` 타입은 보이는데 등록 포인트는 안 보이는" 초급자 혼동을 줄이는 짧은 탐지 primer

- [Kotlin `@ConfigurationProperties` 탐지 보조 노트: data class와 등록 포인트를 같이 찾는 법](./spring-kotlin-configurationproperties-detection-primer.md)
- [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)
- [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)

## Spring External Config File Precedence

> jar 안 `application.yml`, jar 밖 `application.yml`, `spring.config.location`, `spring.config.import`가 서로 같은 층위라고 착각하기 쉬운 지점을 beginner 기준으로 먼저 분리한다

- [Spring External Config File Precedence Primer: packaged `application.yml`, external file, `spring.config.location`, `spring.config.import`](./spring-external-config-file-precedence-primer.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
- [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)

## Spring Relaxed Binding Env Var Cheatsheet

> dotted, dashed, list, map key를 "점은 경계, dash는 철자, index는 `_0_`, 단순 map key는 한 segment"라는 beginner mental model과 짧은 비교표로 바꿔 보는 치트시트다

- [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
- [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)

## Spring `@ConditionalOnProperty` 기본값 함정

> `havingValue`, `matchIfMissing`, env var key 차이를 "missing인지, 값 불일치인지, 환경 입력 차이인지"로 먼저 가르는 beginner primer

- [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
- [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)

## Spring Component Scan 실패 패턴

> `bean이 안 뜬다`를 바로 scan 문제로 단정하지 않도록, `@SpringBootApplication` package 위치와 stereotype annotation 누락은 이 문서로, `@Profile`/conditional 탈락은 condition 문서로 먼저 역분기하게 정리했다

- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- `[playbook]` [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)

## Spring `scanBasePackages` vs `@Import` 선택 기준

> shared module을 붙일 때 scan 범위를 넓혀도 되는지, 아니면 명시적 `@Import`나 Boot auto-configuration으로 계약을 세워야 하는지 가른다

- [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)
- [BeanDefinitionOverrideException Quick Triage: 같은 이름 충돌인지, back-off인지, 후보 선택 문제인지 먼저 가르기](./spring-beandefinitionoverrideexception-quick-triage.md)

## Spring JPA Scan Boundary 함정

> `@SpringBootApplication(scanBasePackages = ...)`를 건드렸다고 entity/repository discovery까지 같이 바뀐다고 착각하기 쉬운 지점을 beginner 기준으로 분리한다

- [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)

## DI 예외 빠른 판별

> 초보자 기준으로 `NoSuchBeanDefinitionException`를 "bean을 못 찾음", `NoUniqueBeanDefinitionException`를 "bean이 여러 개라 못 고름"으로 먼저 번역한 뒤, scan 누락 vs `@Profile`/conditional 탈락 vs 후보 중복으로 이어서 분기하는 beginner troubleshooting note. `found 2`와 `expected at least 1 bean` 실제 로그 2개를 30초 안에 갈라 읽는 예시까지 붙여 초급 판독 진입점을 더 분명하게 정리했다.

- [Spring DI 예외 빠른 판별: bean을 못 찾음 vs 여러 개라 못 고름](./spring-di-exception-quick-triage.md)
- [BeanDefinitionOverrideException Quick Triage: 같은 이름 충돌인지, back-off인지, 후보 선택 문제인지 먼저 가르기](./spring-beandefinitionoverrideexception-quick-triage.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)

## IoC 컨테이너와 DI

> Bean 생명주기, 스코프, singleton 함정까지 — Spring이 객체를 관리하는 진짜 방식

- [IoC 컨테이너와 DI](./ioc-di-container.md)

## Bean 생명주기와 스코프 함정

> singleton/prototype/request/session 스코프와 프록시 타이밍, `ObjectProvider` vs scoped proxy 조회 시점 차이까지 이어서 본다

- [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
- [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)

## AOP와 프록시 메커니즘

> JDK Dynamic Proxy vs CGLIB, self-invocation 문제의 근본 원인

- [AOP 기초: 관점 지향 프로그래밍이 왜 필요한가 (`질문별 바로가기`에서 `this.method()`/`private`/직접 `new` anchor로 바로 점프 + 문제/개선 코드 예시 옆에서 같은 anchor로 바로 왕복 + 초반 표와 3줄 경고로 `self-invocation`과 `self-injection` 차이를 먼저 분리 + `@Transactional/@Cacheable/@Async` 공통 프록시 규칙을 한 표로 다시 묶는 입문 primer)](./spring-aop-basics.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
- [AOP와 프록시 메커니즘 (primer 검색어 `this.method transactional 안됨`, `JDK proxy`, `CGLIB`, `proxyTargetClass`, `final method proxy`를 deep-dive 용어와 바로 연결하는 검색어 브리지 + JDK proxy/CGLIB 초급 비교표)](./aop-proxy-mechanism.md)

## Spring Self-Invocation / Proxy Annotation Matrix

> `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`가 왜 같은 self-invocation 구조 함정을 공유하는지 한 번에 본다. 문서 중간에서 초급자용 Caller/Worker, Facade-Worker 패턴으로 바로 복귀하는 역링크도 함께 둔다.
> 고급 매트릭스에 들어가기 전 1분 프라이머가 필요하면 [`Spring Self-Invocation 공통 오해 1페이지 카드`](./spring-self-invocation-transactional-only-misconception-primer.md)부터 본다.
> 초급 복귀가 필요하면 [`@Transactional 기초`](./spring-transactional-basics.md)부터 보고 다시 올라온다.
> 문서 상단의 동일 3문항 빠른 진단(`this.method()`/`private`/직접 `new`)이 이제 질문별 anchor로 분리되어, 매트릭스에서 바로 해당 설명으로 점프할 수 있다.
> `private 메서드`, `this` 내부 호출, `self-injection`을 "메서드 경계 / 호출 경로 / 우회책"으로 나눠 FAQ 3문항과 30초 결정표로 초급 혼동을 줄였다.
> 이번 보강으로 `private` vs `this.method()`를 먼저 분리하는 한눈 비교표가 추가되어, "`public`으로 바꿨는데 왜 아직 안 되지?" 같은 초급 질문을 더 빨리 정리할 수 있다.

- [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)

## Spring Early Bean Reference와 Circular Proxy Traps

> 순환 의존성과 early reference가 raw target 누출, 프록시 누락, 애매한 startup 오류로 이어지는 경로를 본다

- [Spring Early Bean References and Circular Proxy Traps](./spring-early-bean-reference-circular-proxy-traps.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)

## Spring FactoryBean / SmartInitializingSingleton

> 제품 객체 생성과 singleton 전체 초기화 후 훅을 각각 어디에 써야 하는지 본다

- [Spring `FactoryBean` and `SmartInitializingSingleton` Extension Points](./spring-factorybean-smartinitializingsingleton-extension-points.md)
- [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)

## Spring Template 클래스 입문

> 처음 배우는데 `JdbcTemplate`, `RestTemplate`, `TransactionTemplate` 이름이 왜 비슷한지, 언제 쓰는지 한 장 큰 그림으로 먼저 묶는다

- [Spring Template 클래스 입문: `JdbcTemplate`, `RestTemplate`, `TransactionTemplate` 큰 그림](./spring-template-classes-beginner-primer.md)
- [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md)
- [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
- [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)

## Spring Data Repository vs Domain Repository Bridge

> 처음 배우는데 `JpaRepository`와 domain repository가 둘 다 `Repository`라서 섞이면, "업무 계약"과 "Spring Data 구현 도구"를 먼저 갈라서 본다

- [Spring Data Repository vs Domain Repository Bridge](./spring-data-vs-domain-repository-bridge.md)
- [Spring Data JPA 기초](./spring-data-jpa-basics.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)

## Spring Persistence / Transaction Mental Model Primer

> `@Transactional`, persistence context, `flush`, lazy loading, web/service/repository 역할을 초급자 눈높이 한 장으로 먼저 묶는 엔트리 프라이머

- [Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기](./spring-persistence-transaction-web-service-repository-primer.md)
- [@Transactional 기초: 요청 하나와 트랜잭션 하나를 분리하고, `this.method()`/`private`/직접 `new`를 먼저 거르는 프록시 우선 입문](./spring-transactional-basics.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

## @Transactional follow-up

> 전파 수준, 롤백 규칙, readOnly의 진짜 의미까지

- [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- [Database to Spring Transaction Master Note](../../master-notes/database-to-spring-transaction-master-note.md)
- [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)

## Spring TransactionTemplate과 Programmatic Transaction

> 메서드 경계보다 더 잘게 트랜잭션을 자를 때 `TransactionTemplate`을 어떻게 쓰는지 정리한다

- [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)
- [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)

## Spring UnexpectedRollback / Rollback-Only

> 이미 rollback-only가 찍힌 트랜잭션을 왜 바깥에서 뒤늦게 커밋하려다 실패하는지 정리한다

- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
- `[playbook]` [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

## DB Lock Wait / Deadlock vs Spring Proxy / Rollback

> `lock wait`, `deadlock`, `왜 안 롤백되지`, `왜 @Transactional이 안 먹지`가 섞였을 때 DB wait 증거와 Spring proxy/rollback 착시를 먼저 가른다

- [DB Lock Wait / Deadlock vs Spring Proxy / Rollback 빠른 분기표](./spring-db-lock-deadlock-vs-proxy-rollback-decision-matrix.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../database/lock-wait-deadlock-latch-triage-playbook.md)
- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)

## Spring TransactionSynchronization Ordering / Suspend / Resume

> `TransactionSynchronization`를 afterCommit 편의 기능이 아니라 resource binding, ordering, suspend/resume lifecycle로 본다

- [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](./spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)
- [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)

## Spring Propagation Edge Cases: MANDATORY / SUPPORTS / NOT_SUPPORTED

> 드물어 보이지만 transaction ownership, request lifecycle, non-tx intent를 함께 읽어야 하는 전파 수준을 정리한다

- [Spring Transaction Propagation: `MANDATORY` / `SUPPORTS` / `NOT_SUPPORTED` Boundaries](./spring-transaction-propagation-mandatory-supports-not-supported-boundaries.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

## Spring Service-Layer Transaction Boundary Patterns

> `@Transactional`을 application service 유스케이스 경계에 두는 기준 + 문서 상단 30초 진단 카드로 "프록시 우회 증상 -> 원인 -> 2패턴 선택"을 먼저 자른 뒤, `@Transactional` 기초와 같은 질문으로 읽히는 초급 2패턴(빈 분리, Facade-Worker)

- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)

## Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지

> 처음 배우는데 `DispatcherServlet`, `HandlerInterceptor`가 한꺼번에 나와도 lifecycle deep dive로 바로 내려가지 않도록, MVC 큰 그림과 쉬운 다음 문서를 먼저 연결한다

- [Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지: 큰 그림부터 잡기](./spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)

## Spring MVC 요청 생명주기

> DispatcherServlet부터 응답까지 전체 파이프라인. `filter vs interceptor`를 처음 배우는 질문은 아래 비교 문서부터 보고, async/security deep dive는 그다음으로 넘긴다.
> validation `400` 입문 라우트는 `@RequestBody 400` -> `@Valid` 분기 -> `BindingResult` 로컬 처리 -> `LocalDate/LocalTime` 형식 follow-up 순서로 읽으면 가장 덜 헷갈린다.

- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
- [Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지: 큰 그림부터 잡기](./spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)

<a id="validation-400-problemdetail-route"></a>
## Spring MVC 바인딩/400 라우트

> validation `400`은 "JSON body를 어디서 받는가" -> "`@RequestBody`가 왜 컨트롤러 전에 끊기나" -> "`@Valid`를 탔나" -> "`BindingResult`로 로컬 처리하나" 순서로 읽으면 가장 덜 헷갈린다.

- [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드: 폼/query 바인딩과 JSON body를 한 장으로 분리하기](./spring-modelattribute-vs-requestbody-binding-primer.md)
- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md)
- [Spring `MethodArgumentNotValidException` vs `HandlerMethodValidationException` 초급 브리지: `@Valid` request body와 method validation `400`를 한 표로 잇기](./spring-methodargumentnotvalidexception-vs-handlermethodvalidationexception-beginner-bridge.md)
- [Spring `LocalDate`/`LocalTime` JSON 파싱 `400` 자주 나는 형식 모음](./spring-localdate-localtime-json-400-cheatsheet.md)
- [Spring `@RequestParam` vs `@PathVariable` 초급 비교 카드: query 값과 path 값을 한 장으로 분리하기](./spring-requestparam-vs-pathvariable-beginner-card.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

## Spring MVC 바인딩/400 증상표

| symptom query | first hit | second hit |
|---|---|---|
| "`requestbody 400 왜 바로 나요`", "`컨트롤러 로그 안 찍힘`", "`@RequestBody`인데 컨트롤러 전에 `400`이 나요", "`JSON parse error`가 보여요" | [`@RequestBody` 400 첫 분리 primer](./spring-requestbody-400-before-controller-primer.md) | [`@Valid` 400 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md) |
| "`json인데 415 unsupported media type`", "`content-type: application/json 안 붙였는데 415`" | [`@RequestBody 415` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md) | [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md) |
| "`왜 @valid 안 타요`", "`같은 400인데 뭐가 다른가요`" | [`@Valid` 400 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md) | [`BindingResult` 로컬 처리 카드](./spring-bindingresult-local-validation-400-primer.md) |

## Spring MVC 바인딩/400 follow-up

| symptom query | first hit | second hit |
|---|---|---|
| "`bindingresult 있으면 뭐가 달라져요`", "`왜 methodargumentnotvalidexception 안 나요`", "`@valid 실패인데 컨트롤러 안으로 왜 들어와요`", "`bindingresult 붙였는데 왜 어떤 400은 여전히 컨트롤러 전에 끝나요`" | [`BindingResult` 로컬 처리 카드](./spring-bindingresult-local-validation-400-primer.md) | [Spring 예외 처리 기초](./spring-exception-handling-basics.md) |
| "`localdate json parse 400`", "`time 형식 때문에 400`" | [`LocalDate`/`LocalTime` JSON `400` 형식 모음](./spring-localdate-localtime-json-400-cheatsheet.md) | [`@RequestBody` 400 첫 분리 primer](./spring-requestbody-400-before-controller-primer.md) |
| "`validation 400 response를 problemdetail로 바꾸고 싶어요`" | [`ProblemDetail` handoff primer](./spring-custom-error-dto-to-problemdetail-handoff-primer.md) | [Spring 예외 처리 기초](./spring-exception-handling-basics.md) |

## Spring HandlerMethodReturnValueHandler Chain

> 컨트롤러 반환값이 view name, body, `ResponseEntity`, async/streaming 응답으로 어떻게 해석되고, body write에서 response commit과 disconnect가 어디서 갈리는지 정리한다

- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
- [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
- [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

## Spring ResponseBodyAdvice on Streaming Types

> global JSON envelope를 `ResponseBodyAdvice`로 통일하려 할 때 `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`가 왜 별도 handler ownership과 wire contract 때문에 같은 규칙을 따를 수 없는지 정리한다

- [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
- [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)

## Spring ProblemDetail Before-After Commit Matrix

> 어떤 MVC 실패가 아직 `ProblemDetail`로 번역될 수 있고, 어떤 실패가 response commit 이후 socket/write 오류로 접히는지를 commit 경계 기준으로 정리한다

- [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
- [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
- [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
- [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

## Spring HttpMessageNotWritableException Failure Taxonomy

> `HttpMessageNotWritableException`를 converter-selection, serialization, first-flush, partial-write로 나눠 pre-commit 문제와 post-commit partial response 문제를 빠르게 구분한다

- [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
- [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
- [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
- [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)

## Spring ProblemDetail vs /error Handoff Matrix

> unresolved MVC exception이 언제 Boot `/error` fallback으로 handoff되고, 언제 committed response 때문에 그 handoff가 끊기는지 ownership 관점에서 정리한다

- [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
- [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
- [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
- [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)

## Spring MVC vs WebFlux

> thread-per-request 모델과 event-loop + backpressure 모델의 차이, 그리고 언제 reactive가 득이 되는지

- [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)
- [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)

## Spring MVC Async Dispatch

> `Callable`, `DeferredResult`, `WebAsyncTask`가 Servlet async와 redispatch 위에서 어떻게 동작하는지, filter/interceptor/thread-local이 왜 흔들리는지 본다

- [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
- `OncePerRequestFilter`가 처음이라면 아래 entry split에서 filter/interceptor 큰 그림을 먼저 보고, async redispatch 함정이 맞을 때만 [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](./spring-onceperrequestfilter-async-error-dispatch-traps.md)로 내려간다
- [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)
- [gRPC Deadlines, Cancellation Propagation](../network/grpc-deadlines-cancellation-propagation.md)

## Spring OncePerRequestFilter Entry Split

> 처음 배우는데 `OncePerRequestFilter`가 보이면 먼저 "filter가 interceptor와 어떻게 다른가, 언제 쓰는가" 큰 그림부터 잡고, async/error dispatch 함정은 그다음으로 내려간다

- [Spring `OncePerRequestFilter` vs 일반 `Filter` 입문: 언제 상속부터 시작할까](./spring-onceperrequestfilter-vs-filter-beginner-primer.md)
- [Spring JWT 필터에서 `filterChain.doFilter(...)` 전후에 무슨 일이 일어날까](./spring-jwt-filter-securitycontext-before-after-dofilter-beginner-card.md)
- [Spring `FilterRegistrationBean` vs `@Component` 필터 입문: "bean 등록"과 "서블릿 필터 등록"을 언제 나눌까](./spring-filterregistrationbean-vs-component-filter-beginner-primer.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
- [템플릿 메소드 패턴 기초](../design-pattern/template-method-basics.md)
- [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](../design-pattern/template-method-framework-lifecycle-examples.md)
- [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](../design-pattern/template-method-vs-filter-interceptor-chain.md)
- [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](./spring-onceperrequestfilter-async-error-dispatch-traps.md)
- "`addFilterBefore` / `addFilterAfter` / `UsernamePasswordAuthenticationFilter` 앞뒤가 먼저 보이면" [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)에서 기준 필터 앞뒤 감각을 먼저 잡고, 순서 자체가 질문이면 다음 문서로 내려간다
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)

## Spring BasicErrorController / ErrorAttributes

> MVC advice 밖 실패가 `/error`, `BasicErrorController`, `ErrorAttributes` 경로로 어떻게 fallback되는지 본다

- [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)
- [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)

## Spring Reactive-Blocking Bridge

> WebFlux/WebClient를 쓰면서 어디서 `block()`하고 어디를 `boundedElastic`로 격리할지 경계를 명시한다

- [Spring Reactive-Blocking Bridge: `block()`, `boundedElastic`, and Boundary Traps](./spring-reactive-blocking-bridge-boundedelastic-block-traps.md)
- [Spring WebFlux vs MVC](./spring-webflux-vs-mvc.md)

<a id="spring-bridge-request-lifecycle-timeout-disconnect"></a>
## Spring Request Lifecycle Timeout / Disconnect Bridge

> Spring MVC lifecycle과 timeout budget, `499`, `client disconnect`, `broken pipe`, `connection reset`, `proxy timeout`, cancellation을 함께 본다

- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../network/network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)

## Spring Async Timeout vs Disconnect Decision Tree

> `AsyncRequestTimeoutException`, `AsyncRequestNotUsableException`, disconnected-client 신호가 `DeferredResult`, `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`에서 어느 순간 resolver path와 transport path로 갈라지는지 decision tree로 정리한다

- [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
- [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)

## Spring Servlet Container Disconnect Exception Mapping

> Tomcat/Jetty/Undertow가 `broken pipe`, `connection reset`, disconnected-client style abort를 어떤 예외 shape로 surface하는지와, 이를 로그/알림에서 어떻게 정규화할지 정리한다

- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

## Spring Partial-Response Access Log Interpretation

> download와 streaming response가 중간에 잘렸을 때 access log의 status/bytes/duration과 app log disconnect 예외를 한 타임라인으로 묶어 읽는 기준을 정리한다

- [Spring Partial-Response Access Log Interpretation](./spring-partial-response-access-log-interpretation.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

## Spring HTTP/2 Reset Attribution

> HTTP/2 `RST_STREAM`, `GOAWAY`, browser cancel이 Tomcat/Jetty/Undertow에서 classic broken pipe와 어떻게 다르게 surface되는지와, Spring MVC에서 어떤 bucket으로 태깅해야 하는지 정리한다

- [Spring HTTP/2 Reset Attribution in Spring MVC](./spring-http2-reset-attribution-spring-mvc.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

## Spring StreamingResponseBody / SSE Commit Lifecycle

> `StreamingResponseBody`, `ResponseBodyEmitter`, `SseEmitter`의 first-byte commit, flush cadence, async timeout, disconnect surface를 타입별로 분리해 본다

- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)

## Spring Async MVC Streaming Observability

> first-byte latency, 마지막 성공 flush, completion cause, `AsyncRequestNotUsableException` attribution을 분리해 streaming endpoint를 운영형 메트릭과 로그로 읽는 기준을 정리한다

- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring Observability, Micrometer, Tracing](./spring-observability-micrometer-tracing.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)

## Spring SSE Disconnect Observability Patterns

> heartbeat cadence, reconnect pressure, container 예외 shape, proxy idle timeout을 한 타임라인으로 묶어 SSE alert noise와 실제 incident를 분리하는 운영 기준을 정리한다

- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring HTTP/2 Reset Attribution in Spring MVC](./spring-http2-reset-attribution-spring-mvc.md)

## Spring ResponseBodyEmitter Media-Type Boundaries

> `ResponseBodyEmitter`의 flush cadence와 `application/x-ndjson`, `text/plain`, `application/json` 계약 경계를 분리해, client가 flush를 곧바로 메시지 경계로 착각하지 않게 한다

- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
- [Spring MVC `Flux` Adaptation: `application/json` vs NDJSON and SSE](./spring-mvc-flux-json-vs-ndjson-sse-adaptation.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)

## Spring MVC Flux JSON vs NDJSON and SSE Adaptation

> 같은 `Flux<?>`라도 Spring MVC는 media type이 item framing을 제공하는지에 따라 `application/json`은 `DeferredResult<List<?>>`로 모으고, NDJSON/SSE는 emitter로 흘려 보낸다

- [Spring MVC `Flux` Adaptation: `application/json` vs NDJSON and SSE](./spring-mvc-flux-json-vs-ndjson-sse-adaptation.md)
- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
- [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
- [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)

## Spring Streaming Client Parsing Matrix

> browser `fetch`, `EventSource`, CLI line reader가 각각 bytes, SSE event block, newline line을 어떻게 parse하는지 기준으로 NDJSON, plain text, SSE endpoint 계약을 맞춘다

- [Spring Streaming Client Parsing Matrix: `fetch`, `EventSource`, CLI Line Readers](./spring-streaming-client-parsing-matrix.md)
- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
- [Spring MVC `Flux` Adaptation: `application/json` vs NDJSON and SSE](./spring-mvc-flux-json-vs-ndjson-sse-adaptation.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)

## Spring SSE Proxy Idle-Timeout Matrix

> ALB, Nginx, CDN, 브라우저 reconnect가 서로 다른 타이머를 갖는 체인에서 `SseEmitter` heartbeat와 `Last-Event-ID` recovery를 어떻게 맞출지 정리한다

- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)
- [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)

## Spring MVC SseEmitter vs WebFlux SSE Timeout Behavior

> 같은 SSE라도 MVC `SseEmitter`는 async request lifetime 중심, WebFlux SSE는 publisher lifetime과 cancellation 중심으로 읽어야 하며, heartbeat와 reconnect는 두 스택 모두 별도 계약으로 분리해야 한다

- [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
- [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)

## Spring SseEmitter Timeout Callback Race Matrix

> `onTimeout`, `onError`, `onCompletion`, `completeWithError(...)`를 proxy idle timeout, reconnect replacement, scheduler cleanup ownership과 함께 읽어 old emitter cleanup이 new emitter를 지우는 race를 피한다

- [Spring `SseEmitter` Timeout Callback Race Matrix](./spring-sseemitter-timeout-callback-race-matrix.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)

## Spring SSE Buffering / Compression Checklist

> Nginx/CDN buffering, gzip/brotli, body transform이 `text/event-stream`의 즉시 전달과 heartbeat 관측을 어떻게 망가뜨리는지 점검 순서로 정리한다

- [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Cache-Control 실전](../network/cache-control-practical.md)

## Spring SSE Replay Buffer / Last-Event-ID Recovery

> `Last-Event-ID`를 reconnect header로만 보지 않고, replay window 크기, event ordering fence, stale cursor reset, multi-instance failover 복구 계약까지 함께 정리한다

- [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)

## Spring Boot 자동 구성

> @Conditional의 동작 원리와 커스텀 스타터 만들기

- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)
- [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)
- [Spring Starter Dependency Map 입문: starter, auto-configuration module, SDK/driver는 누가 소유하나](./spring-starter-dependency-map-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)

## Spring Starter Dependency Map 입문

> starter, auto-configuration module, implementation SDK/driver가 build 파일에서 각각 어떤 역할을 맡는지와 direct dependency 책임을 Gradle/Maven mini example로 분리한다

- [Spring Starter Dependency Map 입문: starter, auto-configuration module, SDK/driver는 누가 소유하나](./spring-starter-dependency-map-primer.md)
- [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)
- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)

## Spring `@ConditionalOnClass` classpath 함정

> starter가 build 파일에 있어도 실행 classpath와 test 경계가 다르면 auto-configuration 결과가 달라진다는 점을 scope, optional dependency, test slice 기준으로 가르고, `found required class` / `did not find required class` 같은 condition report 문구를 실제 로그에 매핑해 읽게 돕는다

- [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)

## Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ

> starter를 추가했는데 기대한 bean이 안 보일 때 classpath 조건, property, existing bean back-off와 `found 2` 같은 ambiguous 주입 증상을 먼저 가른 뒤 `DataSourceAutoConfiguration`/`JacksonAutoConfiguration` 로그 한 토막까지 표에 연결해 읽게 한다

- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)
- [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)

## Spring Startup Hooks와 Readiness Warmup

> startup code를 `@PostConstruct`, runner, `SmartLifecycle`, `ApplicationReadyEvent` 중 어디에 둘지와 readiness/liveness 기준을 같이 본다

- [Spring Startup Hooks: `CommandLineRunner`, `ApplicationRunner`, `SmartLifecycle`, and Readiness Warmup](./spring-startup-runner-smartlifecycle-readiness-warmup.md)
- [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)
- [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)

## Spring Startup / Bean Graph Debugging

> Bean 생성 실패, 조건부 자동 구성 누락, 순환 참조, 설정 바인딩 실패를 어디서부터 좁힐지 정리한다

- `[playbook]` [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)
- [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
- [Spring Early Bean References and Circular Proxy Traps](./spring-early-bean-reference-circular-proxy-traps.md)

## Spring + Security

> 오래된 reverse-link와 beginner handoff가 다시 착지하는 호환 anchor다. "`302 /login`", "`SavedRequest`", "`cookie 있는데 다시 로그인`"처럼 browser auth 증상이 보일 때는 deep dive보다 아래 primer 사다리부터 다시 고른다.

- beginner-safe route:
  [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md) -> [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md) -> [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- cross-category bridge:
  cookie, session, redirect memory가 먼저 헷갈리면 [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md) -> [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) 순서로 내려갔다가 다시 올라온다.
- return path:
  Spring 축 자체가 다시 섞이면 [첫 판단 4축](#첫-판단-4축)으로 즉시 돌아가 MVC, DI, 트랜잭션, 요청 파이프라인 중 어디가 먼저 문제인지 다시 고른다.

## Spring Security 아키텍처

> 필터 체인, 인증 아키텍처, OAuth2/JWT 통합

- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)
- [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)
- [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)
- [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md)
- [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md)
- [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)
- [Spring Security 아키텍처](./spring-security-architecture.md)

<a id="spring-bridge-security-session-boundary"></a>
## Spring Security 예외 번역과 세션 경계

> 401/403이 어디서 결정되는지, stateless와 session 기반 인증이 어떤 저장 경계를 가지는지 정리한다

- beginner-safe handoff는 먼저 [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 branch를 고정하는 것이다.
- `redirect / navigation memory`면 [Spring RequestCache / SavedRequest](#spring-bridge-requestcache-savedrequest), `server persistence / session mapping`이면 바로 아래 문서 묶음으로 내려간다.

## Spring Security 세션 저장 경계

- [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md)
- [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
- [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md)
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)
- [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
- [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)
- [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

## Spring Logout Handler / Success Flow

> logout handler가 local cleanup을 어디까지 담당하고, logout success가 언제 redirect/IdP hop만 끝낸 채 full revoke와 분리되는지 정리한다

- [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](./spring-security-logout-handler-success-boundaries.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
- [Security: OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)
- [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)

<a id="spring-bridge-requestcache-savedrequest"></a>
## Spring RequestCache / SavedRequest

> 로그인 전 요청 저장과 로그인 후 원래 URL 복귀 흐름이 API/stateless 경계와 어떻게 충돌하는지, 그리고 왜 이 정보가 OIDC revoke lookup과는 다른지 정리한다

- 이 anchor의 고정 역할은 `redirect / navigation memory` deep dive다.
- `cookie 있는데 다시 로그인`, `next request anonymous after login`처럼 다음 요청 복원이 먼저 문제면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 바로 갈아탄다.
- route가 흐려지면 [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)나 [Spring + Security](../../rag/cross-domain-bridge-map.md#spring--security)로 돌아가 다시 분기한다.

## Spring RequestCache / SavedRequest 관련 문서

- [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)
- [Network: HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Security: OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)
- [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
- [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)
- [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

## Spring OAuth2 + JWT 통합

> OAuth2 로그인 결과를 애플리케이션 JWT로 안전하게 바꾸면서 `SavedRequest`, post-login persistence, OIDC back-channel logout mapping을 어디서 분리할지 정리한다

- [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](./spring-security-logout-handler-success-boundaries.md)
- [Security: OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)

## Spring Test Slices와 Context Caching

> beginner first: 테스트 종류를 아직 못 골랐다면 `Spring 테스트 기초` -> `Test Slice Scan Boundary`를 먼저 보고, "`왜 느려졌지?`" 단계에서만 context cache 문서로 내려간다

> symptom route: "`service bean not found`"는 slice 경계, "`assertSame`은 맞는데 `@Transactional`이 안 먹어요`"는 프록시 behavior, "`어제보다 테스트가 느려졌어요`"는 context cache 재사용 문제로 먼저 자른다

- [Spring 테스트 기초: @SpringBootTest부터 슬라이스 테스트까지](./spring-testing-basics.md)
- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
- [Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가](./spring-transactional-self-invocation-test-bridge-primer.md)
- [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
- [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)
- [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md)

## Spring Test Property Override Boundaries

> `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`를 "고정 상수 / 테스트 설정 묶음 / 런타임 값"으로 나누고 context cache 영향까지 beginner 기준으로 정리한다

- [Spring Test Property Override Boundaries: `@SpringBootTest(properties)`, `@TestPropertySource`, `@DynamicPropertySource`, context cache](./spring-test-property-override-boundaries-primer.md)
- [Spring `spring.main.allow-bean-definition-overriding` Boundaries Primer: 테스트에서는 언제 괜찮고, 운영 기본값으로는 왜 위험한가](./spring-allow-bean-definition-overriding-test-boundaries-primer.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
- [Spring Testcontainers Boundary Strategy](./spring-testcontainers-boundary-strategy.md)

## Spring Test Slice Scan Boundary 오해

> `@WebMvcTest`, `@DataJpaTest`, custom test config가 full `@SpringBootTest`와 다른 탐색 경계를 어떻게 만드는지 beginner 기준으로 정리한다

- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
- [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)

## Spring Test Slice Boundary Leaks

> `@Import`, `@TestConfiguration`, custom security/filter 설정이 slice 경계를 어떻게 조용히 넓히는지 정리한다

- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)
- [Spring Testcontainers Boundary Strategy](./spring-testcontainers-boundary-strategy.md)

## Spring JsonTest / RestClientTest Slice Boundaries

> "`controller까지 올리기엔 과한데 JSON 모양이나 외부 API client 계약만 보고 싶다`"는 초급자 질문을 `@JsonTest` / `@RestClientTest`로 분리해 준다

- [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md)
- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)

## Spring Cache 추상화 함정

> `@Cacheable`이 숨기는 key, invalidation, self-invocation 함정까지

- [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)

## Spring Transaction Debugging Playbook

> `@Transactional`이 왜 안 먹는지, 어디서부터 추적할지 정리한 실전 디버깅 절차. 초급자는 propagation 전에 `this.method()`/`private`/직접 `new` 30초 진단 카드로 먼저 내려가면 오진입을 줄일 수 있다.

- `[playbook]` [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
- [30초 진단 카드: Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)
- [Database to Spring Transaction Master Note](../../master-notes/database-to-spring-transaction-master-note.md)

## Spring Persistence Context Flush / Clear / Detach

> dirty checking, bulk update, batch 처리에서 영속성 컨텍스트를 언제 비우고 동기화할지 다룬다

- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions](./spring-data-jpa-save-persist-merge-state-transitions.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

## Spring Routing DataSource와 JDBC Exception Translation

> read/write 분리에서 커넥션 획득 시점과 replica consistency를 어떻게 볼지, JDBC 예외를 어떻게 의미 기반으로 번역할지 함께 본다

- [Spring Routing DataSource Read/Write Transaction Boundaries](./spring-routing-datasource-read-write-transaction-boundaries.md)
- [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
- [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md)
- [Spring Transaction Isolation / ReadOnly Pitfalls](./spring-transaction-isolation-readonly-pitfalls.md)

## Spring Scheduler와 Async 경계

- [Spring Scheduler와 Async 경계](./spring-scheduler-async-boundaries.md)

## Spring TaskExecutor / TaskScheduler Overload Semantics

> executor queue, rejection policy, fixedRate/fixedDelay, scheduler overlap이 실제 운영 장애 모델을 어떻게 바꾸는지 본다

- [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](./spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)
- [Spring Scheduler와 Async 경계](./spring-scheduler-async-boundaries.md)

## Spring Distributed Scheduling / Cron Drift / Leader Election

> 멀티 인스턴스에서 `@Scheduled`를 어떻게 바라봐야 하는지, duplicate execution, leader handoff, checkpoint, catch-up policy까지 포함해 정리한다

- [Spring Distributed Scheduling, Cron Drift, and Leader-Election Patterns](./spring-distributed-scheduling-cron-drift-leader-election-patterns.md)
- [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](./spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)
- [Spring Batch Chunk / Retry / Skip](./spring-batch-chunk-retry-skip.md)

## Spring RequestContextHolder / ThreadLocal Leakage

> request context가 async pool에서 단순히 사라지는 것이 아니라 다른 요청에 섞여 남을 수 있는 문제를 본다

- [Spring `RequestContextHolder`, `ThreadLocal`, and Request Context Leakage Across Async Pools](./spring-requestcontextholder-threadlocal-leakage-async-pools.md)
- [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)

## Spring `@Transactional`과 `@Async` 조합 함정

> caller transaction과 worker thread가 언제 갈라지고, 커밋 이후 비동기 후속 처리를 어떻게 분리할지 정리한다

- [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
- [Spring EventListener, TransactionalEventListener, Outbox](./spring-eventlistener-transaction-phase-outbox.md)

## Spring Batch chunk, retry, skip

- [Spring Batch chunk, retry, skip](./spring-batch-chunk-retry-skip.md)

## Spring Observability, Micrometer, Tracing

- [Spring Observability, Micrometer, Tracing](./spring-observability-micrometer-tracing.md)

## Spring Resilience4j: Retry, CircuitBreaker, Bulkhead

> retry storm, timeout, circuit breaker, bulkhead, fallback를 Spring Boot 운영 관점에서 함께 본다

- [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](./spring-resilience4j-retry-circuit-breaker-bulkhead.md)

## Spring EventListener, TransactionalEventListener, Outbox

> `@EventListener`, `@TransactionalEventListener`, Outbox를 트랜잭션 phase와 정합성 경계 기준으로 비교한다

- [Spring EventListener, TransactionalEventListener, Outbox](./spring-eventlistener-transaction-phase-outbox.md)
- [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)
- [Spring ApplicationEventMulticaster Internals](./spring-applicationeventmulticaster-internals.md)
- [Spring `@TransactionalEventListener` Outside Transactions and `fallbackExecution`](./spring-transactionaleventlistener-fallbackexecution-no-transaction-boundaries.md)

## Spring WebClient vs RestTemplate

> `resttemplate` 다음에 바로 reactive deep dive로 가지 않도록, 먼저 `restclient` primer를 거쳐 동기 vs reactive 분기를 잡는다

- [Spring `RestClient.Builder` 입문 브리지: `RestClientCustomizer`, 전용 `RestClient` bean, builder 교체는 언제 고르나](./spring-restclient-builder-customizer-vs-dedicated-client-vs-builder-replacement-primer.md)
- [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
- [Spring RestClient vs WebClient Lifecycle Boundaries](./spring-restclient-vs-webclient-lifecycle-boundaries.md)
- [Spring WebClient Connection Pool and Timeout Tuning](./spring-webclient-connection-pool-timeout-tuning.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)

---

## 질의응답

_질문에 대한 답을 말해보며 공부한 내용을 점검할 수 있으며, 클릭하면 답변 내용을 확인할 수 있습니다._

<details>
<summary>Spring의 IoC 컨테이너가 Bean을 관리하는 방식과, 개발자가 직접 new로 객체를 생성하는 것의 차이를 설명해주세요.</summary>
<p>

IoC 컨테이너는 BeanDefinition을 기반으로 객체의 생성, 의존성 주입, 초기화, 소멸까지 전체 생명주기를 관리합니다.
개발자가 new로 직접 생성하면 의존 객체를 직접 조립해야 하고, AOP 프록시가 적용되지 않으며, 생명주기 콜백(@PostConstruct 등)도 호출되지 않습니다.
핵심 차이는 "제어의 주체"가 개발자에서 컨테이너로 역전된다는 점입니다.

</p>
</details>

<details>
<summary>@Transactional이 같은 클래스 내부 메서드 호출 시 동작하지 않는 이유를 프록시 관점에서 설명해주세요.</summary>
<p>

Spring AOP는 프록시 기반으로 동작합니다. 외부에서 호출할 때는 프록시 객체를 통해 메서드가 호출되므로 @Transactional 어드바이스가 적용됩니다.
하지만 같은 클래스 내부에서 this.method()로 호출하면, 프록시를 거치지 않고 실제 타깃 객체의 메서드를 직접 호출하게 됩니다.
따라서 트랜잭션 인터셉터가 끼어들 기회가 없어 @Transactional이 무시됩니다.
해결 방법으로는 AopContext.currentProxy(), 별도 빈으로 분리, AspectJ 위빙 등이 있습니다.

</p>
</details>

## 질의응답 확장

<details>
<summary>Spring Boot의 자동 구성(Auto-configuration)이 동작하는 원리를 설명해주세요.</summary>
<p>

@SpringBootApplication 안에 포함된 @EnableAutoConfiguration이 핵심입니다.
이 어노테이션은 AutoConfigurationImportSelector를 통해 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports 파일에 나열된 모든 자동 구성 클래스를 후보로 로딩합니다.
각 클래스에는 @ConditionalOnClass, @ConditionalOnMissingBean 등의 조건이 붙어 있어, 조건을 만족하는 것만 실제로 빈으로 등록됩니다.
개발자가 직접 같은 타입의 빈을 등록하면 @ConditionalOnMissingBean에 의해 자동 구성이 비활성화되어 커스터마이징이 가능합니다.

</p>
</details>

<details>
<summary>Spring Security의 필터 체인이 요청을 처리하는 흐름을 설명해주세요.</summary>
<p>

HTTP 요청이 들어오면 DelegatingFilterProxy가 Spring 컨텍스트의 FilterChainProxy에게 위임합니다.
FilterChainProxy는 요청 URL 패턴에 맞는 SecurityFilterChain을 선택하고, 그 안에 등록된 필터들(UsernamePasswordAuthenticationFilter, BearerTokenAuthenticationFilter 등)을 순서대로 실행합니다.
인증 필터는 Authentication 객체를 생성해 AuthenticationManager에게 인증을 위임하고, 성공 시 SecurityContextHolder에 저장합니다.
이후 AuthorizationFilter에서 권한 검사를 수행하고, 통과하면 DispatcherServlet으로 요청이 전달됩니다.

</p>
</details>

## 한 줄 정리

처음엔 증상과 질문에 맞는 primer 하나만 고르고, 막히면 [`첫 판단 4축`](#첫-판단-4축)이나 [`빠른 탐색`](#빠른-탐색)으로 돌아와 다음 단계만 이어서 읽으면 된다. HTTP, 쿠키, 세션이 먼저 헷갈릴 때는 [`Network 카테고리 README`](../network/README.md)로 잠깐 내려가고 다시 Spring으로 복귀하면 된다.
