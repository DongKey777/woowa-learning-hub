# 요청 객체는 왜 DI 컨테이너가 아니라 생성자/정적 팩토리/빌더로 만들까

> 한 줄 요약: DI 컨테이너는 오래 사는 협력자를 연결하고, 요청 DTO·command·value object는 이번 호출의 데이터와 규칙을 담아 호출부에서 생성하는 편이 더 자연스럽다.

**난이도: 🟢 Beginner**

관련 문서:

- [Request Scope vs Plain Request Objects: Spring Bean 생명주기와 요청 데이터 분리하기](./request-scope-vs-plain-request-objects.md)
- [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)
- [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
- [빌더 패턴 기초](./builder-pattern-basics.md)
- [Invariant-Preserving Command Model](./invariant-preserving-command-model.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](../spring/spring-bean-di-basics.md)
- [Record and Value Object Equality](../language/java/record-value-object-equality-basics.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: request dto vs di container, command object creation, value object creation beginner, builder vs spring bean, request object constructor or builder, static factory for dto, request scope vs request object, spring request scoped bean vs dto, binder created dto not bean, caller built command not bean, request body dto not bean, 요청 객체를 빈으로 만들면 안 되나요, 스프링 빈으로 dto 만들면 안 되나, what is container managed object, beginner request object creation

---

## 핵심 개념

먼저 아주 단순하게 나누면 된다.

- **DI 컨테이너가 관리하는 것**: 앱이 살아 있는 동안 여러 곳에서 함께 쓰는 협력자
- **호출부가 직접 만드는 것**: 이번 요청 한 번을 위해 필요한 데이터 묶음

예를 들면 `OrderService`, `PaymentClient`, `OrderRepository`는 오래 사는 협력자라서 컨테이너가 연결해 두기 좋다.
반면 `CreateOrderRequest`, `PlaceOrderCommand`, `EmailAddress`, `Money`는 이번 호출에서 들어온 값으로 바로 만들어지는 객체라서 생성자, 정적 팩토리, 빌더가 더 자연스럽다.

짧게 외우면 이렇다.

**"협력자는 컨테이너, 데이터는 호출부 생성"**

---

## 한눈에 보기

```text
HTTP/메서드 입력
-> request DTO / command / value object 생성
-> service(bean) 호출
-> repository / client(bean) 협력
```

| 대상 | 누가 값을 채우나 | 생명주기 | 기본 선택 | 이유 |
|---|---|---|---|---|
| `OrderService` | 컨테이너 | 앱 전역/긴 생명주기 | DI 컨테이너 | 여러 협력자를 안정적으로 wiring한다 |
| `CreateOrderRequest` | HTTP body, 메서드 인자 | 요청 1회 | 생성자/바인딩 | 이번 입력을 담는 데이터다 |
| `PlaceOrderCommand` | controller/service가 조립 | 요청 1회 | 생성자/정적 팩토리/빌더 | 의도와 전제조건을 담는다 |
| `EmailAddress`, `Money` | raw input | 매우 짧음 | 생성자/정적 팩토리 | 검증과 정규화를 잠근다 |

헷갈릴 때는 "이 객체가 다른 객체를 **협력자**로 들고 있나, 아니면 이번 호출의 **값**을 들고 있나"를 먼저 보면 된다.

---

## 상세 분해

### 1. 컨테이너는 협력자를 연결한다

컨테이너는 보통 이런 객체를 관리한다.

- service
- repository
- 외부 API client
- 정책 구현체 모음

공통점은 호출마다 값이 바뀌는 데이터가 아니라, 다른 객체와 **오래 협력**한다는 점이다.

### 2. 요청 DTO는 입력을 옮기는 얇은 객체다

요청 DTO는 HTTP body, form, 메서드 파라미터를 담는 역할에 가깝다.
핵심은 "이 요청에 뭐가 들어왔는가"이지 "어떤 빈과 연결될 것인가"가 아니다.

그래서 request DTO에 서비스 주입을 붙이기보다, 바인딩 후 필요한 서비스가 그 DTO를 받아 해석하는 편이 경계가 선명하다.

### 3. command와 value object는 생성 시점에 규칙을 잠글 수 있다

command는 의도를 담고, value object는 값 규칙을 담는다.
둘 다 호출 시점 입력으로부터 만들어지므로 생성자나 정적 팩토리가 잘 맞는다.

- `RegisterMemberCommand.of(...)`
- `EmailAddress.of(rawEmail)`
- `Money.of("KRW", amount)`

이 지점에서 검증, 정규화, 기본값 적용이 함께 일어나면 이후 코드가 더 단순해진다.

### 4. builder는 필드가 많을 때 조립 가독성을 올린다

필수값과 선택값이 많으면 builder가 읽기 쉽다.
중요한 점은 builder도 여전히 **호출부가 가진 데이터**를 조립한다는 것이다.

즉 builder는 DI의 대체물이 아니라, request object를 더 읽기 좋게 만드는 생성 방식이다.

---

## 흔한 오해와 함정

- **"`@RequestScope`면 request 객체도 bean으로 만들면 되지 않나요?"**
  scope는 생명주기 설정일 뿐이다. 누가 값을 채우는지, 어디서 검증을 잠그는지는 여전히 별도 문제다. 이 혼동만 따로 자르려면 [Request Scope vs Plain Request Objects](./request-scope-vs-plain-request-objects.md)를 보면 된다.
- **"`@RequestBody`로 만들어지면 bean 아닌가요?"**
  보통은 바인딩 결과일 뿐, 서비스 간 협력을 위한 container-managed bean과는 다르다.
- **"builder를 쓰면 DI 없이도 다 해결되나요?"**
  아니다. builder는 데이터 조립용이다. `Clock`, `Policy`, `Repository` 같은 협력자는 여전히 service 쪽에 주입하는 편이 낫다.
- **"작은 DTO도 전부 builder로 만들어야 하나요?"**
  아니다. 필드가 적으면 생성자나 record가 더 간단하다. builder는 옵션이 많을 때만 꺼내면 된다. 이 판단 기준은 [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)에서 더 짧게 볼 수 있다.

---

## 실무에서 쓰는 모습

회원 가입 요청을 받는 흐름을 보자.

```java
public record RegisterMemberRequest(String email, String nickname) {
}

@PostMapping("/members")
public void register(@RequestBody RegisterMemberRequest body) {
    EmailAddress email = EmailAddress.of(body.email());
    RegisterMemberCommand command =
        new RegisterMemberCommand(email, body.nickname());
    registerMemberService.handle(command);
}
```

여기서 `registerMemberService`는 bean이지만, `RegisterMemberRequest`, `RegisterMemberCommand`, `EmailAddress`는 이번 호출에서 바로 만들어진다.

옵션이 많은 command라면 builder가 더 읽기 쉽다.

```java
SendCouponCommand command = SendCouponCommand.builder()
    .memberId(memberId)
    .couponCode(couponCode)
    .expiresAt(expiresAt)
    .requestedBy(adminId)
    .dryRun(true)
    .build();
```

이때 `CouponPolicy`나 `Clock`이 필요하면 command에 주입하지 말고, `couponService`가 주입받아 command를 해석하는 편이 자연스럽다.

---

## 더 깊이 가려면

- [Request Scope vs Plain Request Objects](./request-scope-vs-plain-request-objects.md) — Spring request-scoped bean과 binder DTO/caller-built command를 생명주기와 데이터 생성 책임으로 분리한다
- [Factory와 DI 컨테이너 Wiring](./factory-vs-di-container-wiring.md) — 앱 wiring과 호출 시점 생성의 경계를 한 장 더 넓게 본다
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md) — 작은 request/query model이 언제 `record`, static factory, builder로 갈리는지 바로 자른다
- [Invariant-Preserving Command Model](./invariant-preserving-command-model.md) — command를 patch DTO가 아니라 의도 중심 입력으로 보는 이유를 이어서 본다
- [Spring Bean과 DI 기초](../spring/spring-bean-di-basics.md) — bean 등록, 주입, scope가 무엇을 해결하는지 분리해서 본다

---

## 면접/시니어 질문 미리보기

> Q: request-scoped bean이면 command도 bean으로 둬도 되나요?
> 의도: 생명주기와 생성 책임을 구분하는지 본다.
> 핵심: 아니다. request scope는 짧게 살게 할 뿐이고, command의 값 조립과 규칙 잠금은 여전히 호출부 생성이 더 선명하다.

> Q: value object는 생성자와 정적 팩토리 중 무엇이 더 좋은가요?
> 의도: 이름, 검증, 정규화 필요를 보는지 확인한다.
> 핵심: 단순하면 생성자, 의미 있는 이름이나 canonicalization이 필요하면 정적 팩토리가 더 낫다.

> Q: builder를 쓰면 DTO와 command를 한 번에 해결할 수 있나요?
> 의도: builder를 만능 해결책으로 보는지 확인한다.
> 핵심: builder는 조립 가독성 도구일 뿐이다. 객체의 책임 경계와 bean 여부를 대신 결정하지는 못한다.

---

## 한 줄 정리

DI 컨테이너는 오래 사는 협력자를 연결하고, 요청 DTO·command·value object는 이번 호출의 값과 규칙을 담아 생성자·정적 팩토리·빌더로 직접 만드는 편이 보통 더 낫다.
