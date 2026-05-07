---
schema_version: 3
title: 'roomescape 미션에서 DI/Bean 주입이 보이는 모양'
concept_id: spring/roomescape-di-bean-injection-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
- missions/spring-roomescape
review_feedback_tags:
- DI-vs-locator
- field-injection-vs-constructor
aliases:
- roomescape DI
- ReservationController 생성자 주입
- ReservationService 주입
- 룸이스케이프 의존성 주입
- 룸이스케이프 생성자 주입
- roomescape @Autowired 안 보임
- ReservationController final service
- 룸이스케이프 Bean 주입
intents:
- mission_bridge
- definition
prerequisites:
- spring/bean-di-basics
linked_paths:
- contents/spring/spring-bean-di-basics.md
- contents/spring/spring-bean-lifecycle-basics.md
- contents/design-pattern/service-locator-antipattern.md
forbidden_neighbors:
- contents/design-pattern/service-locator-antipattern.md
confusable_with:
- spring/bean-di-basics
- spring/bean-lifecycle-basics
- design-pattern/service-locator-antipattern
expected_queries:
- 룸이스케이프 미션에서 ReservationService를 어떻게 주입해?
- roomescape에서 DI가 어디에 적용되는 거야?
- ReservationController는 왜 생성자 주입을 써?
- 미션 코드에서 @Autowired가 안 보이는데 어떻게 주입되는 거야?
contextual_chunk_prefix: |
  이 문서는 roomescape 미션에서 ReservationController, ReservationService,
  constructor injection, final field, @Autowired 없는 단일 생성자 자동 주입, Bean container를 연결하는 mission_bridge다.
  new ReservationService로 직접 만들지 않고 Spring이 생성자에 넣어 주는 DI 모양과 service locator 안티패턴을 구분한다.
---

# roomescape 미션에서 DI/Bean 주입이 보이는 모양

> 한 줄 요약: roomescape 미션의 `ReservationController`가 `ReservationService`를 생성자로 받는 한 줄이 곧 *Spring DI*다. `new ReservationService(...)`로 직접 만들지 않고 *컨테이너가 만들어 넣어주는 것*이 핵심이다.

**난이도: 🟢 Beginner**

**미션 컨텍스트**: spring-roomescape-admin (Woowa Spring 트랙)

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "`ReservationController`는 `ReservationService`를 어떻게 받는 거예요?" | controller 생성자 주입을 처음 읽는 단계 | `new`가 없더라도 Spring container가 Bean을 생성자에 넣어 준다는 점을 본다 |
| "`@Autowired`가 안 보이는데도 주입되는 이유가 궁금해요" | 단일 생성자 자동 주입 | 생성자 파라미터가 곧 필요한 Bean 선언임을 확인한다 |
| "왜 필드 주입보다 생성자 주입을 쓰라고 하나요?" | roomescape PR에서 DI 스타일 피드백 | 의존성이 숨지 않고, `final`과 테스트 대체가 쉬운 구조로 읽는다 |

관련 문서:

- [Spring Bean과 DI 기초](./spring-bean-di-basics.md) — 미션을 떠나 일반 개념으로 익히고 싶을 때 먼저 본다
- [Spring Bean 라이프사이클](./spring-bean-lifecycle-basics.md) — Bean이 *언제* 만들어지는지 알고 싶을 때

## 미션의 어디에 DI가 보이는가

`ReservationController`의 한 줄이 입문자가 가장 자주 보는 DI 모양이다:

```java
@RestController
public class ReservationController {
    private final ReservationService reservationService;

    public ReservationController(ReservationService reservationService) {
        this.reservationService = reservationService;
    }
    // ...
}
```

여기서 `new ReservationService(...)`라는 코드가 **어디에도 없다**. 그런데 `reservationService.create(request)`는 동작한다. 그 이유는 *Spring Container가 미션 시작 시점에 한 번 `ReservationService` 인스턴스를 만들고, `ReservationController`를 만들 때 그 인스턴스를 생성자에 넣어주기 때문*이다.

## 왜 `new`로 직접 만들지 않는가

세 가지 이유가 한꺼번에 작동한다:

1. **테스트하기 쉽다** — `LayerTest`처럼 `MockMvc`나 가짜 Repository를 주입해서 컨트롤러만 따로 검증할 수 있다. `new`로 만들었다면 컨트롤러 코드를 바꾸지 않고는 의존성을 갈아끼울 수 없다.
2. **싱글톤 보장** — 같은 `ReservationService`가 모든 컨트롤러/서비스에 주입된다. `new`로 만들면 매 요청마다 새로 만들어져 캐시·상태가 깨진다.
3. **관심사 분리** — 컨트롤러는 *"어떤 Service가 필요하다"*만 선언하고, *"그 Service를 어떻게 만드나"*는 Spring이 책임진다.

## roomescape 미션에서 자주 보는 두 가지 함정

### 함정 1 — 필드 주입 (`@Autowired` private)

미션 PR에서 가끔 다음과 같은 코드가 보인다:

```java
public class ReservationController {
    @Autowired
    private ReservationService reservationService;  // 필드 주입
}
```

생성자 주입과 동작은 비슷해 보이지만, 멘토가 *"생성자로 바꾸세요"*라고 지적하는 이유는 다음과 같다:

- `final`을 붙일 수 없어 *불변 보장*이 깨진다
- 테스트에서 가짜 Service를 주입하려면 reflection이 필요하다
- 의존성이 *숨어버린다* — 클래스 시그니처만 봐서는 무엇이 필요한지 알 수 없다

### 함정 2 — `ApplicationContext.getBean(...)`

```java
ReservationService service =
    applicationContext.getBean(ReservationService.class);  // ❌
```

이건 DI가 아니라 *Service Locator 안티패턴*이다. 컨테이너에 직접 *조회*하면 그 클래스가 *Spring 없이는* 동작하지 못하게 묶여버린다. 자세한 비교는 [디자인 패턴: Service Locator 안티패턴](../design-pattern/service-locator-antipattern.md) 참고.

## 자가 점검

- [ ] `ReservationController`의 의존성을 클래스 시그니처만 봐도 다 셀 수 있나?
- [ ] `private final` 필드로 선언했나?
- [ ] `@Autowired`가 *어디에도* 안 보여도 동작하는 이유를 한 문장으로 설명할 수 있나? (Spring 4.3+ 단일 생성자는 자동 주입)
- [ ] 테스트에서 `new ReservationController(mockService)`로 인스턴스를 만들 수 있나?

## 다음 문서

- 더 큰 그림: [Spring Bean과 DI 기초](./spring-bean-di-basics.md)
- DI가 컨테이너에 등록되는 시점: [Spring Bean 라이프사이클](./spring-bean-lifecycle-basics.md)
- 단계 4 (계층 분리)로 넘어가면서 DAO/Repository 분리 고민이 시작되면 *roomescape DAO vs Repository 브리지* (별도 문서, Wave A 후속) 참고
