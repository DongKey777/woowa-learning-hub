# AOP 기초: 관점 지향 프로그래밍이 왜 필요한가

> 한 줄 요약: AOP는 로깅·트랜잭션·보안처럼 여러 곳에 반복되는 "횡단 관심사"를 비즈니스 로직과 분리해 한 곳에서 관리하는 프로그래밍 기법이다.

**난이도: 🟢 Beginner**

관련 문서:

- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- [IoC와 DI 기초](./spring-ioc-di-basics.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)
- [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)
- [Spring @Transactional 기초](./spring-transactional-basics.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴)
- [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)
- [software-engineering API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: aop basics, 스프링 aop 처음, 횡단 관심사 입문, spring aop 왜 써요, proxy aop beginner, self invocation internal call, aop 내부 호출 함정, this method self invocation, private method aop, new service proxy bypass, bean public external call proxy, self invocation vs self injection, spring aop basics basics, spring aop basics beginner, spring aop basics intro

초급자용 공통 라우팅 한 줄:

`this.method()`, `private`, `new Foo()`가 보이면 옵션보다 먼저 `Bean + public + external call(proxy)`가 깨졌는지 본다.

이 문서에서 `self-invocation`은 어려운 새 용어가 아니라, **같은 클래스 안에서 `this.method()`로 다시 부르는 내부 호출**이라고 읽으면 된다.

## 초급자용 3단계 왕복 라우트

AOP 입문에서 `@Transactional`로 넘어갈 때는 용어보다 아래 순서가 덜 헷갈린다.

| 지금 궁금한 것 | 먼저 볼 문서 | 다음 한 칸 |
|---|---|---|
| "AOP가 왜 필요한가?" | 이 문서 | [`@Transactional 기초`](./spring-transactional-basics.md) |
| "`@Transactional`이 왜 AOP 이야기와 같이 나오지?" | [`@Transactional 기초`](./spring-transactional-basics.md) | [`Service-Layer 2패턴`](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) |
| "`this.method()`를 구조적으로 어떻게 고치지?" | [`Service-Layer 2패턴`](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) | 이 문서의 `Bean + public + external call(proxy)` 체크로 다시 복귀 |

짧게 기억하면:

- AOP 기초는 "왜 프록시가 필요한지"를 잡는 문서다.
- `@Transactional` 기초는 "그 프록시가 트랜잭션에서 어떻게 보이는지"를 연결하는 문서다.
- Service-Layer 2패턴은 "그래서 코드를 어디서 끊어야 하는지"를 보여 주는 문서다.

## 30초 진단 체크리스트 (증상 나오면 먼저 확인)

`@Transactional`, `@Cacheable`, `@Async`가 "붙어 있는데도 안 동작"하면 먼저 아래 3가지를 본다.

두 primer에서 공통으로 쓰는 라우팅 문구는 이 한 줄이다.

`this.method()`, `private`, `new Foo()`가 보이면 옵션보다 먼저 `Bean + public + external call(proxy)`가 깨졌는지 본다.

| 체크 질문 | Yes면 무슨 뜻인가 | 첫 조치 |
|---|---|---|
| 같은 클래스 안에서 `this.method()`로 호출했나? | 프록시를 우회해서 Advice가 적용되지 않는다 | 호출 경로를 다른 Spring Bean 경유로 바꾼다 |
| annotation을 `private` 메서드에 붙였나? | Spring AOP 기본 프록시 범위에서 제외된다 | `public` 경계 메서드로 올려 적용한다 |
| 객체를 `new`로 직접 생성했나? | Spring Bean이 아니라 프록시가 붙지 않는다 | DI로 주입받는 Bean 호출로 바꾼다 |

## 용어 브리지: `self-invocation` = 내부 호출

먼저 용어부터 짧게 갈라두면 덜 헷갈린다.

| 말 | 지금 가리키는 것 | 초급자용 한 줄 |
|---|---|---|
| `self-invocation` | 같은 클래스 내부 호출이라는 문제 상황 | 문서마다 보이면 그냥 "내부 호출"로 읽으면 된다 |
| `self-injection` | 자기 자신의 프록시를 다시 주입받는 우회 방식 | 당장 우회는 가능하지만 기본 해법은 아님 |

짧은 예시:

```java
// 문제: 같은 클래스 내부 호출 + private + 직접 new
public void placeOrder() {
    this.saveOrder();                  // self-invocation
    new AuditService().writeLog();     // not a Spring Bean
}

@Transactional
private void saveOrder() {}
```

```java
// 개선: 프록시가 적용될 public Bean 경계를 통해 호출
@Service
public class OrderService {
    private final OrderTxService orderTxService;
    private final AuditService auditService;

    public void placeOrder() {
        orderTxService.saveOrder();    // Bean -> Proxy -> Advice
        auditService.writeLog();       // Bean 주입 사용
    }
}
```

## 질문별 바로가기

아래 3문항은 이제 각각 바로 점프할 수 있다.

| 질문별 바로가기 | 언제 누르면 좋은가 |
|---|---|
| [`this.method()` 내부 호출 체크](#checklist-this-method) | "`public`인데도 안 먹어요"가 먼저 보일 때 |
| [`private` 메서드 체크](#checklist-private-method) | "annotation을 붙였는데 조용히 무시돼요"가 먼저 보일 때 |
| [`new` 직접 생성 체크](#checklist-direct-new) | "분명 서비스 객체인데 왜 적용이 안 되죠?"가 먼저 보일 때 |

<a id="checklist-this-method"></a>

## 1. 같은 클래스 안에서 `this.method()`로 호출했나?

먼저 이렇게 기억하면 된다.

- `public`은 "정문이 있다"는 뜻이다.
- `this.method()`는 "정문이 있어도 집 안에서 바로 들어간다"는 뜻이다.

즉 메서드가 `public`이어도, 호출이 프록시를 안 지나면 `@Transactional`, `@Cacheable`, `@Async`는 붙지 않을 수 있다.

| 호출 방식 | 프록시를 지나나 | 초급자가 보는 결과 |
|---|---|---|
| `this.saveOrder()` | 아니오 | annotation이 붙어도 안 먹는 것처럼 보임 |
| `orderTxService.saveOrder()` | 예 | annotation 동작을 기대할 수 있음 |

첫 조치:

- 프록시 기능이 필요한 메서드를 다른 Spring Bean으로 분리한다.
- "`public`으로만 바꾸면 되나?"보다 "호출 경로가 Bean 밖으로 나가나?"를 먼저 본다.

자주 헷갈리는 분리:

| 말 | 뜻 | 초급자용 판단 |
|---|---|---|
| `self-invocation` | 같은 클래스 내부 호출 때문에 프록시를 못 탐 | 문제 원인 |
| `self-injection` | 자기 자신의 프록시를 다시 주입받아 우회 호출함 | 가능하지만 기본 해법 아님 |

`self-injection`을 초급 문서에서 기본 답으로 밀지 않는 이유는 짧게 3줄이면 충분하다.

- `self-invocation`은 "왜 안 되나"를 설명하는 원인이고, `self-injection`은 "억지로 다시 프록시를 타게 하자"는 우회라 둘을 같은 답처럼 외우면 구조를 놓친다.
- 코드만 보면 "왜 자기 자신을 주입하지?"가 먼저 보여 읽는 사람에게 Bean 경계보다 특수 트릭이 먼저 학습된다.
- 초급 단계에서는 메서드를 다른 Bean으로 분리하는 편이 호출 경로, 책임 분리, 리팩터링 의도가 함께 드러난다.

<a id="checklist-private-method"></a>

## 2. annotation을 `private` 메서드에 붙였나?

이 질문은 "호출 경로"보다 먼저 "메서드 경계 자체가 프록시에 열려 있나?"를 보는 체크다.

- `private` 메서드는 Spring AOP 기본 프록시 경계에서 빠지기 쉽다.
- 그래서 같은 코드에 `this.method()`가 없어도, 우선 `public` 경계로 끌어올려 다시 보는 편이 안전하다.

짧은 대비:

| 코드 위치 | 프록시 적용 기대 |
|---|---|
| `@Transactional private void save()` | 낮음 |
| `@Transactional public void save()` | 높음 |

첫 조치:

- annotation을 `public` 경계 메서드로 올린다.
- 그다음 실제 호출이 프록시를 지나는지도 함께 확인한다.

<a id="checklist-direct-new"></a>

## 3. 객체를 `new`로 직접 생성했나?

이 질문은 "메서드 접근 제한자"보다 더 앞단, 즉 "그 객체가 Spring이 관리하는 Bean인가?"를 확인하는 체크다.

- `new AuditService()`로 만든 객체는 Spring Bean이 아니다.
- Bean이 아니면 프록시도 붙지 않는다.

짧게 비교하면:

| 생성 방식 | Spring Bean인가 | 프록시 적용 기대 |
|---|---|---|
| `new AuditService()` | 아니오 | 낮음 |
| 생성자 주입받은 `auditService` | 예 | 높음 |

첫 조치:

- 직접 생성 대신 생성자 주입으로 Bean을 받는다.
- "객체는 있는데 왜 annotation이 안 먹지?"가 보이면 `new` 생성 흔적부터 찾는다.

## 1페이지 비교표: `@Transactional` / `@Cacheable` / `@Async` 프록시 전제

초급자 관점에서 먼저 이렇게 기억하면 된다.

- 셋 다 "메서드에 annotation만 붙이면 끝"이 아니라, **프록시를 타는 호출 경로**가 전제다.
- 아래 3칸(Bean / public / external call) 중 하나라도 깨지면 "붙었는데 안 동작" 증상이 나온다.

| annotation | Spring Bean이어야 하나 | `public` 메서드 전제가 필요한가 | 외부 호출(프록시 경유)이어야 하나 | 전제가 깨졌을 때 초보가 보는 증상 |
|---|---|---|---|---|
| `@Transactional` | 필요 | 보통 필요 | 필요 | 트랜잭션 시작/전파/롤백 기대가 깨짐 |
| `@Cacheable` | 필요 | 보통 필요 | 필요 | 캐시 적중 없이 매번 원본 메서드 실행 |
| `@Async` | 필요 | 보통 필요 | 필요 | 비동기가 아니라 호출 스레드에서 즉시 실행 |

### 3문항 미니 진단 카드

아래 3칸을 Yes/No로만 보면 초급자도 바로 가지를 탈 수 있다.

```text
1. 이 객체는 Spring Bean인가?  No -> `new` 흔적부터 지우고 DI 주입으로 바꾼다.
2. annotation 붙은 메서드가 `public`인가?  No -> `public` 경계 메서드로 올린다.
3. 호출이 다른 Bean에서 들어오나?  No -> `this.method()` 자기 호출이라 프록시를 우회한다.
4. 1~3이 모두 Yes인가?  Yes -> 프록시 전제는 맞다. 이제 annotation 옵션/실행 환경을 본다.
5. `@Transactional`이면 전파/rollback 조건으로 이동한다.
6. `@Cacheable`이면 key/condition/cacheManager 설정으로 이동한다.
7. `@Async`이면 executor/@EnableAsync/반환 타입을 확인한다.
```

더 자세한 분기는 [`Spring Self-Invocation Proxy Trap Matrix`](./spring-self-invocation-proxy-annotation-matrix.md)와 [`AOP와 프록시 메커니즘`](./aop-proxy-mechanism.md)에서 이어서 보면 된다.

한 줄 규칙:

`Bean + public + external call(proxy)`가 안 맞으면, 세 annotation 모두 같은 뿌리(프록시 우회)에서 실패한다.

초급자용으로 다시 한 번만 줄이면 아래 표다.

| 눈에 먼저 들어온 단서 | 먼저 고정할 질문 |
|---|---|
| `this.method()` | "다른 Bean을 거쳤나?" |
| `private` | "프록시가 설 `public` 경계인가?" |
| `new Foo()` | "애초에 Spring Bean인가?" |

## `@Cacheable`인데 DB를 매번 다시 읽는다면? 1분 확인 절차

초급자용 mental model부터 잡으면 쉽다.

- `@Cacheable`은 메서드 앞 정문에 붙은 "캐시 확인원"에 가깝다.
- 같은 클래스 안에서 `this.method()`로 들어가면 정문을 안 지나므로, 확인원도 못 만나고 DB 쪽으로 바로 간다.

짧은 예시:

```java
@Service
public class ProductService {

    public ProductDto renderProduct(Long id) {
        return this.findProduct(id); // 내부 호출 -> 캐시 프록시 우회
    }

    @Cacheable(cacheNames = "products", key = "#id")
    public ProductDto findProduct(Long id) {
        return productRepository.findDtoById(id); // DB 조회
    }
}
```

같은 `id`로 두 번 호출했는데도 DB 조회 로그가 두 번 보이면, 초급자는 먼저 "캐시 설정이 다 틀렸나?"보다 "호출이 프록시를 탔나?"를 의심하는 편이 빠르다.

| 확인 단계 | 무엇을 보면 되나 | 해석 |
|---|---|---|
| 1. 같은 파라미터로 두 번 호출 | 예: `id=1`로 연속 요청/테스트 | 캐시 hit가 나면 두 번째는 원본 메서드 실행이 줄어야 한다 |
| 2. SQL 로그나 repository 호출 횟수 확인 | `select ...`가 두 번 찍히는지 본다 | 두 번 찍히면 "캐시 miss가 계속 난다"는 관찰을 확보한 것 |
| 3. 호출 경로 확인 | `this.findProduct(id)` / 같은 클래스 내부 호출인지 본다 | 맞다면 설정 실수보다 프록시 우회 가능성이 크다 |

다음 이동:

- 내부 호출 여부를 더 짧게 가르려면 [`Spring Self-Invocation Proxy Trap Matrix`](./spring-self-invocation-proxy-annotation-matrix.md)
- 캐시 key, `condition`, `cacheManager`까지 이어서 보려면 [`Spring Cache 추상화 함정`](./spring-cache-abstraction-traps.md)

짧은 대비 예시:

```java
@Service
public class BillingService {

    @Async
    public void sendReceipt() {}

    public void issueBill() {
        this.sendReceipt(); // 내부 호출 -> 프록시 우회 -> @Async 미적용
    }
}
```

## `@Cacheable`인데 DB를 매번 다시 읽는다면? 1분 확인 절차 (계속 2)

```java
@Service
public class BillingFacade {
    private final BillingWorker billingWorker;

    public void issueBill() {
        billingWorker.sendReceipt(); // 외부 Bean 호출 -> 프록시 경유 -> @Async 적용
    }
}
```

## 증상별 다음 문서 한 칸 라우팅

검색어가 아래 쪽에 더 가깝다면, 시작 문서를 이렇게 고르면 왕복이 줄어든다.

| 지금 검색한 말/증상 | 여기서 먼저 잡을 것 | 다음 문서 |
|---|---|---|
| `aop 뭐예요`, `횡단 관심사`, `aspect advice pointcut` | AOP의 목적과 가장 짧은 mental model | 이 문서 계속 읽기 |
| `@transactional 왜 aop예요`, `transactional 프록시`, `트랜잭션이 왜 내부 호출에서 빠지지` | AOP 프록시가 begin/commit/rollback을 감싼다는 연결 | [Spring @Transactional 기초](./spring-transactional-basics.md) |
| `this.method transactional 구조 수정`, `service 레이어 나누는 법`, `caller worker`, `facade worker` | 프록시 우회 원인을 코드 구조 수정으로 바꾸는 2패턴 | [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴) |
| `this.method transactional 안됨`, `private method transactional`, `직접 new 해서 annotation 안 먹음` | 프록시 우회 3문항 체크 | [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md) |
| `private`와 `this`와 `self-injection` 차이가 헷갈림 | 메서드 경계 / 호출 경로 / 우회책 분리 | [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md) |
| `JDK dynamic proxy`, `CGLIB`, `proxy target class` | 프록시 생성 방식과 한계 | [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md) |

## 먼저 mental model 한 장

AOP를 처음 볼 때는 용어보다 아래 한 문장으로 시작하면 된다.

`AOP = 비즈니스 메서드 주변(before/after)에 공통 코드를 자동으로 두르는 프록시 규칙`

예를 들어 서비스 3곳에 공통 실행 로그를 넣는다고 가정하자.

| 방식 | 코드 모양 | 변경 비용 |
|---|---|---|
| 직접 삽입 | 각 서비스 메서드마다 시작/종료 로그를 복붙 | 로그 포맷 변경 시 N개 메서드 수정 |
| AOP 적용 | Aspect 1곳에 로그 규칙 정의 | 로그 포맷 변경 시 Aspect 1곳 수정 |

`OrderService`에 트랜잭션 로그를 추가하고 싶다고 해보자. `OrderService`, `PaymentService`, `MemberService`마다 같은 로그 코드를 복붙하면 형식 변경 때 50개 클래스를 전부 건드려야 한다.

AOP(Aspect-Oriented Programming, 관점 지향 프로그래밍)는 이 반복 코드를 "관점(Aspect)"으로 분리해 **한 곳에서 정의하고, 여러 곳에 자동으로 적용**한다. Spring은 이를 프록시 객체를 통해 런타임에 끼워 넣는다.

## 한눈에 보기

```text
[호출자]
   ↓
[프록시(Aspect 적용)]  ← 로깅, 트랜잭션 등 횡단 관심사
   ↓
[실제 서비스 메서드]   ← 순수 비즈니스 로직
```

| 용어 | 의미 |
|---|---|
| Aspect | 횡단 관심사를 담은 모듈 (예: 로깅 Aspect) |
| Advice | 언제 어떤 코드를 실행할지 (Before / After / Around) |
| Pointcut | 어떤 메서드에 Advice를 적용할지 선택 표현식 |
| JoinPoint | Advice가 실제로 끼어드는 실행 지점 (메서드 호출 시점) |

## 언제 AOP로 풀고, 언제 그냥 코드로 둘까

| 상황 | 권장 선택 | 이유 |
|---|---|---|
| 로깅/권한/트랜잭션처럼 여러 클래스에 반복된다 | AOP | 중복 제거와 정책 일관성이 크다 |
| 한 메서드만 특별 처리한다 | 메서드 내부 코드 | AOP 설정 비용이 더 클 수 있다 |
| 요청/응답 단위 공통 처리다 (웹 계층) | Filter/Interceptor 우선 검토 | AOP보다 HTTP 경계 의미가 직접적이다 |
| 런타임 데이터에 따라 동적으로 분기한다 | 명시적 서비스 코드 | pointcut보다 코드 분기가 읽기 쉽다 |

## 상세 분해

- **Before Advice**: 메서드 실행 전에 동작. 예: 입력값 로깅, 권한 확인.
- **After Advice**: 메서드 실행 후에 동작(예외 여부 무관). 예: 실행 완료 기록.
- **Around Advice**: 메서드 실행 전후를 감쌈. `proceed()`를 직접 호출해야 원래 메서드가 실행됨. 가장 강력하지만 실수하면 메서드가 아예 안 불린다.
- **Pointcut 표현식**: `execution(* com.example.service.*.*(..))` 같은 형태로 패키지·클래스·메서드 이름 패턴을 지정한다.
- **@Transactional도 AOP**: Spring의 `@Transactional`은 Around Advice로 트랜잭션을 열고 닫는다. AOP 없이는 선언적 트랜잭션이 불가능하다.

## 흔한 오해와 함정

**오해 1: AOP는 복잡하니 쓸 일이 없다**
로그, 트랜잭션, 보안 검사 등 이미 매일 쓰는 Spring 기능이 AOP 위에 구현돼 있다. 원리를 모르면 `@Transactional`이 왜 내부 호출에서 안 먹히는지 이해하기 어렵다.

**오해 2: Around Advice에서 `proceed()`를 안 불러도 된다**
`proceed()`를 빠뜨리면 원래 메서드가 실행되지 않고 Advice만 실행된다. 항상 `return joinPoint.proceed()`를 반환해야 한다.

**오해 3: AOP는 어떤 메서드에도 다 적용된다**
Spring AOP는 **Spring Bean의 public 메서드**에만 적용된다. 같은 클래스 내부 메서드 호출(self-invocation)에는 프록시가 끼어들지 못한다. 이것이 `@Transactional` 내부 호출 함정과 동일한 원인이다.

**오해 4: `@Transactional` 문제는 트랜잭션 문서만 보면 된다**
`@Transactional` 자체가 AOP 프록시 위에서 동작하므로, 내부 호출/직접 `new` 생성/`private` 메서드 같은 프록시 우회가 있으면 트랜잭션 규칙이 적용되지 않는다. 이때는 트랜잭션 옵션보다 호출 경로를 먼저 확인한다.

**오해 5: `@Cacheable`, `@Async`는 `@Transactional`과 다르게 내부 호출에서도 된다**
세 annotation 모두 기본적으로 프록시 interception에 기대기 때문에, 내부 호출(`this.method()`), 직접 `new`, 프록시를 타지 않는 경계에서는 같은 이유로 빠질 수 있다.

## 실무에서 쓰는 모습

실행 시간을 측정하는 간단한 Aspect 예시:

```java
@Aspect
@Component
public class TimingAspect {

    @Around("execution(* com.example.service.*.*(..))")
    public Object measureTime(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed(); // 원래 메서드 실행
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(joinPoint.getSignature() + " took " + elapsed + "ms");
        return result;
    }
}
```

`@Aspect` + `@Component`를 붙이고, `@Around`에 Pointcut 표현식을 지정하면 된다.

## 다음 읽기 라우팅

- "왜 내부 호출에서 `@Transactional`이 안 먹지?"가 먼저면 [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)로 바로 이동한다.
- "프록시가 실제로 어떻게 만들어지지?"가 궁금하면 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)으로 이어간다.
- "AOP와 선언적 트랜잭션 연결"을 먼저 잡고 싶으면 [Spring @Transactional 기초](./spring-transactional-basics.md)를 바로 본다.
- "구조를 어떻게 나눠야 self-invocation을 끊지?"가 먼저면 [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md#초급-빠른-수정-내부-호출-프록시-우회-2패턴)로 바로 이동한다.
- "`@Async`, `@Cacheable`까지 같이 헷갈린다"면 [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)의 annotation별 증상 표를 이어서 본다.

## 더 깊이 가려면

- 프록시 생성 방식(JDK 동적 프록시 vs CGLIB), self-invocation 한계, `@EnableAspectJAutoProxy` 동작은 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)에서 이어서 본다.
- `@Transactional`이 AOP로 어떻게 구현되는지는 [Spring @Transactional 기초](./spring-transactional-basics.md)와 함께 보면 연결이 명확해진다.

## 면접/시니어 질문 미리보기

> Q: AOP의 횡단 관심사를 예로 들어 설명하면?
> 의도: AOP 필요성 이해 확인
> 핵심: 로깅, 트랜잭션, 보안 검사 등 여러 모듈에 동일하게 적용되는 기능이 횡단 관심사다.

> Q: Spring AOP에서 self-invocation이 문제가 되는 이유는?
> 의도: 프록시 동작 원리 이해 확인
> 핵심: Spring AOP는 외부 호출 시 프록시를 거치지만, 같은 빈 내부 메서드 호출은 프록시를 우회해 Advice가 적용되지 않는다.

> Q: Around Advice와 Before/After Advice의 차이는?
> 의도: Advice 종류 구분 확인
> 핵심: Around는 메서드 호출을 직접 제어할 수 있고 `proceed()`로 원래 메서드를 실행한다. Before/After는 실행 전/후 시점만 가로챈다.

## 한 줄 정리

AOP는 로깅·트랜잭션처럼 여러 곳에 반복되는 횡단 관심사를 Aspect로 분리해 비즈니스 로직과 섞이지 않게 하는 기법이고, Spring은 프록시를 통해 이를 투명하게 적용한다.
