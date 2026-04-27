# Request Scope vs Plain Request Objects: Spring Bean 생명주기와 요청 데이터 분리하기

> 한 줄 요약: `@RequestScope`는 Spring이 관리하는 협력자를 요청마다 새로 만드는 설정이고, request DTO와 command는 이번 요청의 값을 담아 binder나 호출부가 만드는 평범한 데이터 객체다.

**난이도: 🟢 Beginner**

관련 문서:

- [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md)
- [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
- [Singleton vs DI Container Scope](./singleton-vs-di-container-scope.md)
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](../spring/spring-bean-di-basics.md)
- [Invariant-Preserving Command Model](./invariant-preserving-command-model.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: request scope vs request object, spring request scoped bean vs dto, requestscope bean vs requestbody dto, request scoped bean command object, binder created dto not bean, caller built command not bean, request dto plain object, spring di lifetime vs request data creation, request scope beginner, request object bean confusion, dto should not be request scoped bean, command object creation spring, request scoped context holder, method local request state, request scope vs plain request objects basics

---

## 먼저 그림부터 잡기

Spring 요청 코드에서 "request"라는 말이 두 번 나온다.
이 둘을 같은 뜻으로 섞으면 DI 생명주기와 데이터 생성 책임이 꼬인다.

- **request-scoped bean**: Spring 컨테이너가 요청마다 새로 만들어 주는 관리 객체
- **plain request object**: HTTP body나 메서드 인자로부터 이번 호출의 값을 담는 일반 객체

짧게 외우면 이렇다.

**"scope는 누가 얼마나 오래 관리하나, DTO/command는 이번 값이 무엇인가"**

`@RequestScope`는 생명주기 이야기다.
`@RequestBody RegisterRequest`, `PlaceOrderCommand`는 데이터 생성 이야기다.

---

## 한눈에 비교

| 구분 | Spring request-scoped bean | request DTO | command |
|---|---|---|---|
| 누가 만드는가 | Spring 컨테이너 | Spring MVC binder, 테스트 코드, 호출자 | controller/service 같은 호출부 |
| 무엇을 담는가 | 요청 동안 공유할 협력자나 context | 외부에서 들어온 raw input | 유스케이스 의도와 정리된 입력 |
| 생명주기 | HTTP 요청 하나 | 객체를 만든 호출 흐름 안 | 객체를 만든 호출 흐름 안 |
| DI 대상인가 | 예, bean이다 | 보통 아니다 | 보통 아니다 |
| 대표 예 | `RequestTrace`, `CurrentUserContext` | `RegisterMemberRequest` | `RegisterMemberCommand` |

핵심은 "짧게 산다"가 곧 "bean이어야 한다"는 뜻이 아니라는 점이다.
DTO와 command도 짧게 살지만, 대부분 컨테이너가 관리할 협력자가 아니라 이번 호출의 값 묶음이다.

---

## 왜 헷갈리나

### 1. 둘 다 요청마다 달라진다

request-scoped bean도 요청마다 달라지고, request DTO도 요청마다 달라진다.
그래서 초보자는 "요청마다 다르면 `@RequestScope`인가?"라고 생각하기 쉽다.

하지만 질문이 다르다.

- "요청마다 새 bean 인스턴스가 필요하다"면 scope 질문이다.
- "이번 요청 body를 객체에 담고 싶다"면 binding/생성 질문이다.

### 2. `@RequestBody`가 Spring을 거쳐 만들어진다

`@RequestBody` 객체는 Spring MVC가 만들어 주므로 bean처럼 느껴질 수 있다.
하지만 보통은 컨테이너에 등록된 bean이 아니라 **binder가 만든 메서드 인자**다.

```java
public record RegisterMemberRequest(String email, String nickname) {
}

@PostMapping("/members")
public void register(@RequestBody RegisterMemberRequest request) {
    RegisterMemberCommand command = RegisterMemberCommand.of(
        request.email(),
        request.nickname()
    );

    registerMemberService.register(command);
}
```

여기서 bean은 `registerMemberService`다.
`RegisterMemberRequest`와 `RegisterMemberCommand`는 이번 호출에서 만들어진 plain object다.

### 3. command 이름 때문에 "처리자"처럼 보인다

`PlaceOrderCommand`는 유스케이스 입력을 담는 객체다.
`PlaceOrderCommandHandler`나 `OrderService`가 실제 처리를 담당한다.

따라서 command에 repository, client, policy를 주입하기보다 handler/service가 그런 협력자를 주입받고 command를 해석하는 편이 경계가 선명하다.

---

## request-scoped bean이 어울리는 경우

request-scoped bean은 "요청마다 값이 다르다"보다 더 좁게 써야 한다.
다음 조건이 붙을 때 검토한다.

- 같은 요청 안의 여러 bean이 공통 context를 읽어야 한다
- 그 context가 framework lifecycle에 묶여 있다
- method parameter로 넘기는 것보다 명시적 request context bean이 더 단순하다
- 테스트에서 request lifecycle을 준비할 수 있을 만큼 이득이 있다

예시는 이런 쪽이다.

```java
@RequestScope
@Component
public class RequestTrace {
    private final String traceId;

    public RequestTrace(HttpServletRequest request) {
        this.traceId = request.getHeader("X-Trace-Id");
    }

    public String traceId() {
        return traceId;
    }
}
```

이 객체는 "회원 가입 요청 body"가 아니다.
요청 동안 여러 협력자가 참조할 수 있는 framework-side context에 가깝다.

---

## plain request object가 어울리는 경우

request DTO, command, value object는 대부분 plain object로 충분하다.

```java
public record PlaceOrderRequest(
    Long memberId,
    List<Long> itemIds,
    String couponCode
) {
}

public record PlaceOrderCommand(
    Long memberId,
    List<Long> itemIds,
    Optional<String> couponCode
) {
    public static PlaceOrderCommand from(PlaceOrderRequest request) {
        return new PlaceOrderCommand(
            request.memberId(),
            List.copyOf(request.itemIds()),
            Optional.ofNullable(request.couponCode()).filter(code -> !code.isBlank())
        );
    }
}
```

이런 객체는 다음 성격을 가진다.

- 필드 값이 호출마다 다르다
- HTTP binding이나 controller 조립 결과다
- 생성 시점에 검증, 정규화, 기본값을 잠글 수 있다
- repository/client 같은 긴 생명주기 협력자를 들고 있을 필요가 없다

그래서 `@Component`, `@RequestScope`, `@Autowired`를 붙이지 않고도 정상적인 설계다.

---

## 코드 리뷰에서 바로 보는 기준

| 질문 | `예`라면 | `아니오`라면 |
|---|---|---|
| 이 객체가 다른 bean들을 협력자로 주입받아 일하나? | bean 후보 | plain object 후보 |
| 이 객체의 필드 대부분이 HTTP body, path variable, method argument인가? | plain object 후보 | bean 후보일 수 있음 |
| 같은 요청 안의 여러 service가 이 context를 공통으로 읽어야 하나? | request-scoped bean 검토 | method parameter 전달 우선 |
| 생성 시점에 값 검증/정규화를 잠그는 게 핵심인가? | DTO/command/value object | service/context bean과 분리 |
| 테스트에서 `new`로 바로 만들 수 있어야 읽기 쉬운가? | plain object 유지 | DI fixture 검토 |

초보자에게는 이 순서가 실용적이다.

1. 먼저 request DTO와 command를 `record`나 생성자로 둔다.
2. 정규화 이름이 필요하면 정적 팩토리를 붙인다.
3. 선택값이 많아 호출부가 흐려지면 builder를 검토한다.
4. 여러 bean이 공유해야 하는 요청 context일 때만 request scope를 따로 검토한다.

---

## 흔한 혼동

- **"`@RequestScope`면 DTO에 서비스를 주입해도 되나요?"**
  보통은 아니다. DTO는 입력을 담고, service가 DTO나 command를 받아 처리한다.

- **"요청마다 새로 만들어지면 전부 request-scoped bean 아닌가요?"**
  아니다. `new`, binder, static factory로 만들어지는 짧은 생명주기 객체도 많다.

- **"`@RequestBody` 객체는 Spring이 만들었으니 bean인가요?"**
  일반적으로는 controller method argument다. container-managed collaborator와 구분해야 한다.

- **"command가 비즈니스 행동 이름을 가지니 bean이어야 하지 않나요?"**
  command는 대개 행동 자체가 아니라 행동에 필요한 입력이다. 행동은 handler/service bean이 맡는다.

- **"request-scoped bean을 쓰면 parameter 전달을 줄일 수 있으니 좋은가요?"**
  숨은 입력이 늘면 테스트와 추적이 어려워진다. 단순한 값은 method parameter나 command에 남기는 편이 더 읽기 쉽다.

---

## 잘못 섞인 예와 분리한 예

아래 코드는 DTO가 입력, 검증, 협력자 호출을 모두 떠안는다.

```java
@RequestScope
@Component
public class RegisterMemberRequest {
    @Autowired
    private MemberRepository memberRepository;

    private String email;
    private String nickname;

    public void register() {
        memberRepository.save(new Member(email, nickname));
    }
}
```

문제는 DTO가 더 이상 단순한 요청 데이터가 아니라 숨은 service처럼 변한다는 점이다.

분리하면 각 객체의 이유가 선명해진다.

```java
public record RegisterMemberRequest(String email, String nickname) {
}

public record RegisterMemberCommand(EmailAddress email, String nickname) {
    public static RegisterMemberCommand from(RegisterMemberRequest request) {
        return new RegisterMemberCommand(
            EmailAddress.of(request.email()),
            request.nickname()
        );
    }
}

@Service
public class RegisterMemberService {
    private final MemberRepository memberRepository;

    public RegisterMemberService(MemberRepository memberRepository) {
        this.memberRepository = memberRepository;
    }

    public void register(RegisterMemberCommand command) {
        memberRepository.save(Member.register(command.email(), command.nickname()));
    }
}
```

이 구조에서는 생성 책임과 DI 책임이 나뉜다.

- binder가 `RegisterMemberRequest`를 만든다
- controller가 `RegisterMemberCommand`를 만든다
- Spring이 `RegisterMemberService`와 `MemberRepository`를 연결한다

---

## 어디로 이어서 읽을까

- request DTO, command, value object를 직접 만드는 기준은 [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md)를 본다.
- 작은 request object가 `record`, static factory, builder 중 어디서 멈춰야 하는지는 [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)를 본다.
- Spring bean scope와 singleton scope의 차이는 [Singleton vs DI Container Scope](./singleton-vs-di-container-scope.md)를 본다.
- DI container가 어떤 객체 graph를 연결하는지 더 넓게 보려면 [Factory와 DI 컨테이너 Wiring](./factory-vs-di-container-wiring.md)을 본다.

---

## 한 줄 정리

`@RequestScope`는 Spring이 관리하는 협력자의 요청 단위 생명주기이고, request DTO와 command는 binder나 호출부가 이번 요청의 값을 담아 만드는 plain object다.
