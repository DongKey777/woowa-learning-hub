# Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`

> 한 줄 요약: self-invocation 문제는 `@Transactional` 하나의 예외가 아니라, 프록시 기반 애노테이션 전반에서 같은 원리로 반복되는 함정이므로 "어떤 애노테이션이 왜 내부 호출에서 빠지는지"를 한 번에 묶어 보는 편이 실전적이다.

**난이도: 🔴 Advanced**

## 3문항 빠른 진단 링크 (`@Transactional`/`@Async`/`@Cacheable` 공통)

아래 3문항 중 하나라도 `Yes`면, 이 문서를 끝까지 읽기 전에 해당 질문 anchor로 바로 왕복하는 편이 빠르다.

| 빠른 진단 질문 | 바로 이동 |
|---|---|
| 같은 클래스 안에서 `this.method()`로 호출했나? | [`AOP 기초`의 `this.method()` 체크로 이동](./spring-aop-basics.md#checklist-this-method) |
| annotation을 `private` 메서드에 붙였나? | [`AOP 기초`의 `private` 메서드 체크로 이동](./spring-aop-basics.md#checklist-private-method) |
| 객체를 `new`로 직접 생성했나? | [`AOP 기초`의 직접 `new` 체크로 이동](./spring-aop-basics.md#checklist-direct-new) |

> 🧭 Beginner 진입 배너 (`@Transactional`부터 다시 잡기)
>
> 이 문서는 고급 매트릭스다. `self-invocation`이 아직 낯설면 먼저 아래 문서로 돌아간 뒤 다시 오면 이해가 훨씬 빠르다.
>
> - [`Self-Invocation 공통 오해 1페이지 카드`](./spring-self-invocation-transactional-only-misconception-primer.md) — "`@Transactional`만 문제"라는 오해를 먼저 끊고, 프록시 기반 annotation 공통 규칙으로 다시 잡는 가장 짧은 프라이머
> - [`@Transactional 기초`](./spring-transactional-basics.md) — 프록시 트랜잭션, rollback 규칙, 내부 호출/프록시 우회의 첫 증상부터 설명
> - [`AOP 기초`](./spring-aop-basics.md) — 왜 `this.method()` 호출에서 프록시가 빠지는지 가장 짧게 확인
>
> 빠른 선택표:
>
> | 지금 상태 | 먼저 볼 문서 |
> |---|---|
> | "`@Transactional`이 왜 안 먹는지"부터 막힌다 | [`@Transactional 기초`](./spring-transactional-basics.md) |
> | "프록시/내부 호출" 개념이 아직 헷갈린다 | [`AOP 기초`](./spring-aop-basics.md) |
> | 증상이 `@Async`/`@Cacheable`/보안까지 번진다 | 이 문서를 계속 읽기 |

> 관련 문서:
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [Spring Self-Invocation 공통 오해 1페이지 카드: "`@Transactional`만 문제"가 아니다](./spring-self-invocation-transactional-only-misconception-primer.md)
> - [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
> - [Spring Method Validation Proxy Pitfalls](./spring-method-validation-proxy-pitfalls.md)
> - [Spring Security Method Security Deep Dive](./spring-security-method-security-deep-dive.md)
> - [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)

retrieval-anchor-keywords: self invocation, proxy trap, internal call bypass proxy, transactional self invocation, async self invocation, cacheable self invocation, validated self invocation, preauthorize self invocation, AopContext, self injection, self-injection, private transactional, this method call proxy bypass, transactional basics, beginner routing, primer bridge, aop 3문항 진단, this.method private new 체크, self invocation quick triage, private vs this call, self injection vs self invocation, private method transactional faq, this call transactional faq, self injection beginner faq, 프라이빗 메서드 트랜잭션, this 내부 호출 트랜잭션, self injection 우회, aop 내부 호출 함정, aop 30초 진단, transactional cacheable async 비교표, bean public external call proxy, spring aop public method only, aop primer to self invocation matrix, caller worker pattern, facade worker pattern, transactional internal call 2 patterns, beginner reverse link, matrix to primer bridge, private vs this 한눈표, private this self invocation 차이, 프록시 우회 비교표, private vs self invocation faq

## 먼저 붙여두는 한 줄 규칙

이 문서는 고급 매트릭스지만, 아래 한 줄은 `AOP 기초`와 동일하게 가져가면 된다.

`Bean + public + external call(proxy)`가 안 맞으면, `@Transactional`, `@Async`, `@Cacheable` 같은 프록시 기반 annotation은 같은 뿌리에서 실패한다.

| 빠르게 보는 항목 | 초급자용 해석 | 이 문서에서 이어서 볼 것 |
|---|---|---|
| Bean이 아닌 객체를 `new`로 만들었다 | 프록시를 붙일 Spring 관리 경계가 없다 | `new` 생성 vs DI 주입 |
| `private` 메서드에 붙였다 | 프록시가 서야 할 메서드 경계가 닫혀 있다 | `private`와 `public` 경계 |
| 같은 클래스에서 `this.method()`로 불렀다 | 프록시 정문을 안 지났다 | self-invocation과 Bean 분리 |

## 핵심 개념

Spring에서 self-invocation 문제를 처음 배울 때 보통 `@Transactional` 예제로 접한다.

하지만 실제로는 같은 원리가 여러 애노테이션에 반복된다.

- `@Transactional`
- `@Async`
- `@Cacheable`
- `@Validated`
- `@PreAuthorize`

공통 원리는 단순하다.

- 외부에서 프록시를 통해 들어오면 interception이 된다
- 같은 객체 내부에서 `this.method()`로 부르면 프록시를 우회한다

즉 self-invocation은 특정 애노테이션 버그가 아니라, **프록시 기반 기능 전체에 공통인 구조적 함정**이다.

### 자주 헷갈리는 포인트 (초급 복귀 체크)

- "`@Transactional`만 예외적으로 까다롭다"가 아니다. `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`도 같은 구조 함정을 공유한다.
- "애노테이션을 더 붙이면 해결된다"가 아니다. 핵심은 애노테이션 개수보다 **호출 경로가 프록시를 타는지**다.
- 용어가 먼저 버거우면 이 문서를 붙잡기보다 [`@Transactional 기초`](./spring-transactional-basics.md)로 돌아가 한 번 정리하고 다시 오는 편이 빠르다.

## 공통 오해 FAQ (3문항)

먼저 아주 짧은 mental model부터 잡는다.

- `private`은 "메서드 문 앞에 경비가 설 수 있나?" 문제다.
- `this` 호출은 "그 문을 통과하나, 그냥 옆문으로 들어가나?" 문제다.
- `self-injection`은 "같은 집 안에서도 정문으로 다시 들어오게 만드는 우회"다.

즉 셋은 비슷해 보여도 서로 다른 질문이다.

| 항목 | 지금 묻는 핵심 | 초급자용 한 줄 해석 | 기본 권장 |
|---|---|---|---|
| `private` 메서드 | 프록시가 메서드 경계에 끼어들 수 있나 | 문이 닫혀 있어서 프록시가 못 선다 | `public` 경계 메서드로 올린다 |
| `this.save()` 호출 | 호출이 프록시를 거치나 | 같은 집 안에서 바로 들어가서 정문을 안 지난다 | 다른 Bean으로 경계를 나눈다 |
| `self-injection` | 프록시를 일부러 다시 타게 할까 | 자기 자신 대신 프록시 버전을 주입받아 정문으로 돌린다 | 가능하지만 기본 해법은 아님 |

### `private` vs `this` 한눈 비교표

초급자는 이 둘을 자주 같은 문제로 묶지만, 실제로는 질문이 다르다.

| 비교 항목 | `private` 메서드 문제 | `this.method()` 내부 호출 문제 |
|---|---|---|
| 먼저 보는 질문 | "이 메서드 경계에 프록시가 설 수 있나?" | "호출이 프록시 정문을 통과했나?" |
| 핵심 오해 | "`private`만 `public`으로 바꾸면 끝난다" | "`public`이면 자동으로 된다" |
| `public`으로 바꾸면 | 메서드 경계는 열릴 수 있다 | 그래도 같은 클래스 내부 호출이면 여전히 우회할 수 있다 |
| 다른 Bean으로 분리하면 | 보통 같이 정리된다 | 가장 기본적인 해결 방향이다 |
| 한 줄 기억법 | 문이 닫혀 있으면 프록시가 못 선다 | 문이 열려 있어도 안 지나가면 소용없다 |

바로 판별하는 질문도 같이 외우면 빠르다.

- 애노테이션이 붙은 메서드가 `private`인가? 그러면 먼저 메서드 경계를 본다.
- 메서드가 `public`인데도 안 먹는가? 그러면 거의 항상 호출 경로가 `this`인지부터 본다.

### 한눈에 구분하는 30초 결정표

| 내가 지금 본 코드/질문 | 먼저 판단할 포인트 | 첫 답변 |
|---|---|---|
| "`private`에 `@Transactional` 붙였어요" | 메서드 경계 자체가 프록시에 열려 있는가 | 우선 `public` 경계로 올리고, 호출 경로를 다시 본다 |
| "`public`인데도 내부 호출에서 안 먹어요" | `this`로 직접 불렀는가 | `public` 여부보다 프록시 경유 여부가 먼저다 |
| "`self-injection` 하면 해결되죠?" | 우회책을 기본 해법으로 착각했는가 | 가능은 하지만 보통은 Bean 분리가 더 낫다 |

초급자가 많이 섞는 문장을 먼저 분해하면 더 빨라진다.

- "`private`이라서 안 된다"는 절반만 맞다. `private` 문제와 `this` 내부 호출 문제는 별개다.
- "`public`으로 바꿨는데도 안 된다"면 대부분 호출 경로가 여전히 `this`다.
- "`self-injection`을 썼다"는 말은 문제 원인이 아니라 우회 방식이다.

### Q1. `private` 메서드에 `@Transactional`을 붙였는데 왜 안 되나요?

짧게 말하면, Spring AOP 프록시는 보통 이런 `private` 메서드 경계에 끼어들지 못한다.

```java
@Service
public class OrderService {

    public void place() {
        save(); // 같은 클래스 내부 호출
    }

    @Transactional
    private void save() {
    }
}
```

이 코드에서 초급자가 흔히 하는 오해는 "`private`을 `public`으로만 바꾸면 끝"이라고 생각하는 것이다. 하지만 실제 핵심은 두 가지다.

- `private`이면 프록시가 메서드 경계에 개입하기 어렵다.
- 게다가 같은 클래스 내부 호출이면 `this` 경로로 프록시까지 우회한다.

즉 `private`은 "메서드 경계 문제"이고, self-invocation은 "호출 경로 문제"다. 둘이 한 코드에서 같이 나타날 수는 있지만 같은 원인은 아니다.

바로 연결해서 보면:

- 접근 제한자 감각이 먼저 필요하면 [`AOP 기초`의 `private` 메서드 체크](./spring-aop-basics.md#checklist-private-method)
- `@Transactional` 입문 설명으로 다시 잡으려면 [`@Transactional 기초`](./spring-transactional-basics.md#증상-라우팅-카드-내부-호출프록시-우회)

### Q2. `this.save()`는 왜 문제인가요? `public`이어도 안 되나요?

네. `public`이어도 `this.save()`면 문제일 수 있다.

```java
@Service
public class OrderService {

    public void place() {
        this.save(); // public이어도 self-invocation
    }

    @Transactional
    public void save() {
    }
}
```

초급자 눈높이로 보면 이렇게 기억하면 된다.

- `public`은 "정문을 만들었다"에 가깝다.
- `this.save()`는 "정문이 있어도 집 안에서 바로 들어갔다"에 가깝다.

즉 문이 `public`이어도, 호출이 프록시 정문을 안 지나면 `@Transactional`, `@Async`, `@Cacheable` 같은 기능이 붙지 않는다.

짧은 비교:

| 호출 방식 | 프록시 경유 여부 | 기대 결과 |
|---|---|---|
| `this.save()` | 우회 | 애노테이션 기능 미적용 가능 |
| 다른 Bean의 `orderTxService.save()` | 경유 | 애노테이션 기능 적용 기대 가능 |

그래서 초급 단계의 기본 답은 "`public`으로 바꿀까?"보다 "호출을 다른 Bean 경계로 빼야 하나?"다.

### Q3. `self-injection`은 정답인가요?

정답이라기보다 "제한적으로 쓸 수 있는 우회책"에 가깝다.

```java
@Service
public class OrderService {

    private final OrderService self;

    public OrderService(OrderService self) {
        this.self = self;
    }

    public void place() {
        self.save(); // 프록시를 다시 타도록 기대
    }

    @Transactional
    public void save() {
    }
}
```

이 코드는 "같은 클래스 내부 호출" 문제를 없앤 것이 아니라, **프록시 버전의 자기 자신을 통해 다시 호출하도록 우회한 것**이다.

왜 초급자에게 기본 해법으로 권하지 않냐면, 읽는 사람이 바로 이해하기 어렵기 때문이다.

- "`왜 자기 자신을 다시 주입받지?`"라는 구조적 의문이 생긴다.
- 테스트나 리팩터링 때 의도를 놓치기 쉽다.
- "내부 호출 문제"를 코드 구조로 숨기고 넘어갈 위험이 있다.

그래서 우선순위는 보통 아래 순서다.

1. 가장 기본: `@Transactional` 같은 프록시 기능이 필요한 메서드를 다른 Bean으로 분리한다.
2. 차선책: 정말 구조를 못 나누는 상황에서만 `self-injection`이나 `AopContext` 같은 우회를 검토한다.

한 줄로 묶으면:

- `private`은 "메서드 경계가 프록시에 열려 있나?"
- `this` 호출은 "호출이 프록시를 지나가나?"
- `self-injection`은 "프록시를 다시 지나가게 만드는 우회가 필요한가?"

이 셋을 분리해서 보면 self-invocation FAQ가 glossary처럼 보이지 않고, 어디를 고쳐야 하는지 바로 잡힌다.

### 자주 나오는 오해 문장 바로잡기

| 흔한 말 | 왜 헷갈리나 | 초급자용 교정 |
|---|---|---|
| "`private`만 `public`으로 바꾸면 해결된다" | 메서드 경계와 호출 경로를 한 문제로 섞는다 | `public`은 필요 조건일 수 있지만, `this` 호출이면 여전히 우회한다 |
| "`self-injection`도 self-invocation이니까 같은 말이다" | 둘 다 `self`가 들어가서 같은 개념처럼 보인다 | `self-invocation`은 문제 상황, `self-injection`은 그 문제를 우회하려는 방법이다 |
| "`this.save()`와 그냥 `save()`는 다르다" | 문법 차이만 본다 | 같은 클래스 내부라면 둘 다 사실상 self-invocation 맥락으로 봐야 한다 |

## 깊이 들어가기

### 1. 문제의 본질은 애노테이션이 아니라 호출 경로다

같은 코드를 봐도 중요한 질문은 "무슨 애노테이션이 붙었나?"보다 "누가 누구를 어떻게 호출하나?"다.

```java
public void outer() {
    this.inner(); // proxy bypass
}
```

여기서 `inner()`에 어떤 프록시 기반 애노테이션이 붙든, 원칙적으로는 비슷한 위험이 생긴다.

즉 self-invocation은 기능별 예외 목록이 아니라, **호출 경로 모델**로 이해해야 한다.

### 2. annotation별로 깨지는 증상은 다르게 보인다

같은 구조지만 현상은 다르게 체감된다.

| 애노테이션 | self-invocation 시 흔한 증상 |
|---|---|
| `@Transactional` | 트랜잭션이 안 열리거나 전파/롤백 기대가 깨짐 |
| `@Async` | 비동기 실행이 안 되고 같은 스레드에서 바로 실행됨 |
| `@Cacheable` | 캐시를 안 타고 매번 실제 메서드 실행 |
| `@Validated` | 메서드 파라미터/리턴값 검증이 조용히 빠짐 |
| `@PreAuthorize` | 메서드 보안 검사가 안 걸림 |

즉 "작동 안 함"은 같지만, **무엇이 빠졌는지는 기능마다 다르게 보인다**.

### 3. 복합 애노테이션일수록 더 헷갈린다

한 메서드에 여러 프록시 기반 기능이 같이 붙으면 self-invocation은 더 위험하다.

예:

- `@Transactional` + `@CacheEvict`
- `@Async` + `@Transactional`
- `@PreAuthorize` + `@Validated`

이 경우 일부만 빠지고 일부는 다른 경로에서 살아 있는 것처럼 보여, 디버깅이 더 어려워진다.

즉 self-invocation 문제는 단일 기능보다, **애노테이션 조합이 많을수록 더 운영적으로 헷갈린다**.

### 4. 해결은 프록시를 억지로 끌어오는 것보다 경계를 나누는 편이 낫다

보통 더 좋은 방향은 아래다.

- 메서드를 다른 빈으로 분리
- orchestration service와 worker service 분리
- 내부 helper는 프록시 기대 없이 순수 로직으로 유지

`AopContext.currentProxy()`나 self injection은 가능할 수 있다.

하지만 이런 우회는 대개 다음 대가가 있다.

- 구조가 프록시 구현에 묶인다
- 테스트가 지저분해진다
- 팀원이 읽기 어렵다

즉 해결의 기본은 마법이 아니라, **호출 경계를 프록시가 탈 수 있는 방향으로 다시 그리는 것**이다.

### 초급자 복귀 링크: 결국 어디 문서로 돌아가면 되나

여기서부터는 "원리는 알겠는데 코드를 어디까지 나눠야 하지?"가 더 중요해진다.

이 문서는 annotation 공통 원리를 보는 고급 매트릭스이고, 실제 수정 출발점은 아래 2패턴 문서로 돌아가는 편이 빠르다.

| 지금 머릿속 질문 | 먼저 돌아갈 링크 | 왜 그 문서가 더 빠른가 |
|---|---|---|
| "`this.write()` 한 군데만 프록시 정문으로 돌리면 된다" | [`빈 분리(Caller/Worker)`로 바로 이동](./spring-service-layer-transaction-boundary-patterns.md#pattern-caller-worker) | 가장 작은 구조 변경으로 self-invocation을 끊는 예시가 바로 나온다 |
| "주문 생성 + 재고 차감처럼 여러 작업의 커밋 주인을 정해야 한다" | [`Facade-Worker`로 바로 이동](./spring-service-layer-transaction-boundary-patterns.md#pattern-facade-worker) | 유스케이스 대표 메서드 1개가 경계를 소유하는 그림을 먼저 잡아 준다 |
| "`@Transactional`부터 다시 천천히 보고 싶다" | [`Self-Invocation 공통 오해 1페이지 카드`](./spring-self-invocation-transactional-only-misconception-primer.md) | 프록시 우회 원인을 jargon 없이 1분짜리 mental model로 다시 묶어 준다 |

짧게 외우면:

- Caller/Worker = "문제 메서드만 다른 Bean으로 옮겨 정문 호출 복구"
- Facade-Worker = "유스케이스 대표 메서드 1개가 커밋 주인"
- 아직도 헷갈리면 = 매트릭스보다 프라이머로 먼저 복귀

### 5. "같은 클래스에 있으니 자연스럽다"는 감각이 오히려 위험하다

서비스 메서드를 잘게 나누다 보면 내부 호출이 자연스러워 보인다.

하지만 프록시 기반 기능이 붙는 순간, 같은 클래스 배치는 단순한 리팩터링 취향이 아니라 실행 의미를 바꾼다.

즉 메서드 위치는 코드 스타일이 아니라, **interception 가능 여부를 결정하는 구조 요소**가 된다.

### 6. 디버깅은 기능별 현상보다 공통 원리를 먼저 보는 것이 빠르다

문제가 보이면 먼저 묻는다.

- 이 메서드는 외부 빈에서 프록시를 통해 불렸는가
- 아니면 같은 객체 내부에서 직접 호출됐는가

이 질문 하나로 트랜잭션, 캐시, 보안, 검증, 비동기 문제 상당수가 동시에 좁혀진다.

## 실전 시나리오

### 시나리오 1: `@Async`가 붙었는데 로그가 같은 스레드에서 찍힌다

내부 호출로 프록시를 우회했을 수 있다.

### 시나리오 2: 캐시가 붙은 조회 메서드가 내부 호출에서는 매번 DB를 친다

`@Cacheable`도 같은 프록시 구조를 쓰므로 self-invocation 영향을 받는다.

### 시나리오 3: `@PreAuthorize`가 서비스 내부 호출에서는 무력화된다

보안 문제처럼 보여도 본질은 method-security proxy bypass일 수 있다.

### 시나리오 4: `@Validated`가 붙었는데 내부 helper 경로에선 검증이 안 된다

validation도 interception 기반이면 같은 구조 문제를 가진다.

## 코드로 보기

### 위험한 구조

```java
@Service
public class OrderService {

    public void place() {
        save(); // self-invocation
    }

    @Transactional
    public void save() {
    }
}
```

### 더 나은 분리

```java
@Service
public class OrderFacade {

    private final OrderWriter orderWriter;

    public void place() {
        orderWriter.save();
    }
}
```

이 예시를 보고 "이건 Caller/Worker인가, Facade-Worker인가?"가 헷갈리면 아래처럼 자르면 된다.

| 코드 모양 | 더 가까운 패턴 | 바로 볼 링크 |
|---|---|---|
| `OrderFacade -> OrderWriter.save()`처럼 문제 메서드 1개만 밖으로 뺐다 | Caller/Worker | [패턴 1 다시 보기](./spring-service-layer-transaction-boundary-patterns.md#pattern-caller-worker) |
| `CheckoutFacade -> OrderWorker + InventoryWorker`처럼 유스케이스 orchestration을 Facade가 맡는다 | Facade-Worker | [패턴 2 다시 보기](./spring-service-layer-transaction-boundary-patterns.md#pattern-facade-worker) |

### 최후 수단

```java
((OrderService) AopContext.currentProxy()).save();
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 내부 호출 유지 | 코드가 한 곳에 모인다 | 프록시 기반 기능이 조용히 빠질 수 있다 | 프록시 기능이 없는 순수 로직 |
| 별도 빈 분리 | 실행 의미가 명확하다 | 클래스 수가 늘어난다 | 트랜잭션/보안/캐시/비동기 경계 |
| self injection / `AopContext` | 빠른 우회가 가능하다 | 구조가 불투명해진다 | 정말 제한적으로 |
| AspectJ 등 다른 접근 | self-invocation 제약을 줄일 수 있다 | 복잡도와 운영 부담이 있다 | 매우 특수한 경우 |

핵심은 self-invocation을 `@Transactional` 특수 사례로 보지 않고, **프록시 기반 annotation 전체의 공통 위험 모델**로 보는 것이다.

## 꼬리질문

> Q: self-invocation 문제가 여러 애노테이션에서 반복되는 이유는 무엇인가?
> 의도: 공통 구조 원리 이해 확인
> 핵심: 모두 프록시를 통한 interception에 의존하기 때문이다.

> Q: `@Async` self-invocation은 어떤 식으로 보일 수 있는가?
> 의도: 현상 차이 이해 확인
> 핵심: 비동기화가 안 되고 같은 스레드에서 즉시 실행될 수 있다.

> Q: 가장 기본적인 해결은 무엇인가?
> 의도: 구조적 해결 우선순위 확인
> 핵심: 프록시를 탈 수 있도록 메서드를 다른 빈/경계로 분리하는 것이다.

> Q: 왜 `AopContext.currentProxy()`는 최후 수단인가?
> 의도: 우회책의 비용 인식 확인
> 핵심: 코드 구조가 프록시 구현 세부사항에 강하게 묶이기 때문이다.

## 한 줄 정리

self-invocation은 `@Transactional`만의 함정이 아니라, 프록시 기반 annotation 전체에서 반복되는 공통 구조 문제다.
