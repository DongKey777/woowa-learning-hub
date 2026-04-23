# Template Hook Smells: 템플릿 메소드가 과해졌다는 신호

> 한 줄 요약: Template Hook는 흐름 고정에 유용하지만, 훅이 많아지면 상속 구조보다 조건 분기와 전략 조합이 더 낫다는 신호일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [템플릿 메소드](./template-method.md)
> - [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
> - [JUnit 5 Callback Model vs Classic xUnit Template Skeleton](./junit5-callback-model-vs-classic-xunit-template-skeleton.md)
> - [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](./template-method-vs-filter-interceptor-chain.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [전략 패턴](./strategy-pattern.md)
> - [안티 패턴](./anti-pattern.md)
> - [God Object / Spaghetti / Golden Hammer](./god-object-spaghetti-golden-hammer.md)
> - [전략 폭발 냄새](./strategy-explosion-smell.md)

retrieval-anchor-keywords: template hook smell, template hook smells, template method overuse, 훅 메서드 과다, hook method explosion, too many hooks, before after hook explosion, inheritance rigidity, fragile base class, subclass override risk, hook ladder smell, brittle base class, OncePerRequestFilter shouldNotFilter smell, shouldNotFilter overuse, doFilterInternal shouldNotFilter boundary, xUnit setUp tearDown smell, setup teardown override smell, base test fixture smell, unsafe extension point, framework hook overuse

---

## 핵심 개념

Template Method는 알고리즘의 골격을 상위 클래스가 고정하고, 일부 단계를 hook으로 열어두는 패턴이다.  
문제는 hook이 계속 늘어나는 순간이다.

- `beforeX`, `afterX`
- `validate`, `doExecute`, `cleanup`
- `onStart`, `onFinish`, `onError`

hook이 많아지면 상속 계층이 아니라 **분기와 우회로**가 된다.

## 냄새-first 분기

- 상위 클래스 하나가 검증, 실행, 로깅, 복구까지 모두 빨아들이면 [God Object / Spaghetti / Golden Hammer](./god-object-spaghetti-golden-hammer.md)도 같이 본다.
- 훅을 줄이겠다며 단계별 구현을 전략 클래스로 옮겼는데 조합 수가 다시 늘어나면 [전략 폭발 냄새](./strategy-explosion-smell.md)로 이어진다.
- `beforeX`, `afterX`, `onError`, `cleanup`이 계속 늘어나고 서브클래스가 내부 순서를 외워야 하면 이 문서가 기준점이다.

---

## 깊이 들어가기

### 1. hook은 유연성처럼 보이지만 결합을 만든다

hook은 "조금만 바꿀 수 있다"는 장점이 있다.
하지만 실제로는 서브클래스가 상위 클래스의 내부 순서에 의존하게 된다.

이 구조는 다음 위험을 만든다.

- 순서 변경이 어렵다
- 일부 hook만 override되면 의도가 흐려진다
- 상위 클래스 수정이 하위 클래스 전체에 파급된다

### 2. 훅이 많으면 패턴이 아니라 정책이 된다

hook이 많다는 건 결국 여러 변화 지점이 있다는 뜻이다.

- 전처리
- 검증
- 후처리
- 에러 복구

이때는 template method를 유지하기보다 전략, 상태, 책임 연쇄로 분해하는 편이 더 자연스럽다.

### 3. backend에서 흔한 냄새

- 배치 프레임워크의 abstract job class가 너무 커진다
- 인증/인가/검증/로깅 hook이 한 클래스에 몰린다
- 서브클래스가 템플릿 내부 순서를 가정한다

### 4. 프레임워크 hook이 안전 구간을 넘는 순간

[프레임워크 안의 템플릿 메소드](./template-method-framework-lifecycle-examples.md)를 읽고 오면 감이 더 빨라진다.
핵심은 같다. 프레임워크 hook은 "정해진 slot에 조금 덧붙이는 용도"일 때만 안전하다.

#### `OncePerRequestFilter#shouldNotFilter()`: skip predicate면 안전, 요청 정책 엔진이 되면 냄새

`shouldNotFilter()`는 원래 "이 요청은 아예 이 필터를 건너뛸까?"를 묻는 작은 hook이다.

- 안전한 경우: `/health`, `/favicon.ico`처럼 값싼 제외 조건만 둔다
- 냄새가 시작되는 경우: tenant, role, feature flag, async/error dispatch, 헤더 기반 분기를 한꺼번에 여기로 몰아넣는다
- 더 위험한 경우: `shouldNotFilter()`와 `doFilterInternal()`이 같은 인증/추적 조건을 중복으로 가진다

```java
@Override
protected boolean shouldNotFilter(HttpServletRequest request) {
    return isHealth(request)
        || isSwagger(request)
        || isAsyncResume(request)
        || tenantTracingDisabled(request)
        || hasSkipHeader(request)
        || alreadyAuthenticated(request);
}
```

이쯤 되면 hook이 "간단한 skip"이 아니라 **요청 라우팅 정책**이 된다.
서브클래스는 base class의 dispatch 순서와 `shouldNotFilterAsyncDispatch()` 같은 주변 hook까지 함께 알아야 하므로, 안전한 확장 지점을 벗어난다.

이럴 때는 다음으로 옮기는 편이 낫다.

- `RequestMatcher`나 predicate 객체로 skip 기준 분리
- 필터 등록 단계에서 path/dispatcher 범위를 나누기
- 인증/추적 판단을 별도 policy component로 빼고 filter는 orchestration만 맡기기

#### classic xUnit `setUp()` / `tearDown()`: fixture 준비는 안전, 테스트 오케스트레이션이 되면 냄새

`setUp()` / `tearDown()`도 원래는 fixture를 만들고 정리하는 작은 lifecycle slot이다.

- 안전한 경우: 테스트 객체 생성, fake 초기화, 리소스 해제
- 냄새가 시작되는 경우: DB seed, clock reset, 트랜잭션 열기, event listener 등록, 외부 stub wiring이 한 base test class에 몰린다
- 더 위험한 경우: 서브클래스가 `super.setUp()` 호출 순서와 숨은 부작용을 외워야 한다

```java
public abstract class BaseIntegrationTest extends TestCase {
    @Override
    protected void setUp() {
        openTransaction();
        seedDatabase();
        resetClock();
        stubPaymentGateway();
        registerDomainEventSpy();
    }

    @Override
    protected void tearDown() {
        clearThreadLocal();
        rollbackTransaction();
        resetClock();
    }
}
```

이 구조는 테스트마다 필요한 fixture를 여는 게 아니라,
base class가 **테스트 환경 오케스트레이터**가 되는 모습이다.
그 순간 `setUp()` / `tearDown()`은 hook이라기보다 숨은 실행 파이프라인이 되고, fixture 대칭도 쉽게 깨진다.

이럴 때는 다음이 더 낫다.

- fixture builder / helper object로 준비 책임 분리
- JUnit 5 extension이나 rule-style component로 lifecycle 합성
- 테스트마다 필요한 의존성을 명시적으로 주입해 hidden setup 축소

### 5. 프레임워크 hook smell을 빨리 판별하는 질문

| 질문 | 아직 안전한 hook | 이미 smell 쪽 |
|---|---|---|
| hook이 하는 일은 작은가 | skip 여부, fixture 준비/정리 한두 개 | 정책 조합, dispatch 분기, 복수 인프라 orchestration |
| 기본 구현이 안전한가 | override 안 해도 일관된 기본값 | override 없이는 의미가 불분명하거나 side effect가 숨는다 |
| 서브클래스가 내부 순서를 몰라도 되는가 | slot 이름만 알면 된다 | `super` 호출 순서, paired hook symmetry, base class 상태까지 외워야 한다 |
| 더 나은 분해 지점이 있는가 | 아직 없음 | matcher, strategy, extension, helper object로 바로 분리 가능 |

---

## 실전 시나리오

### 시나리오 1: 배치 작업

입력 읽기, 정제, 저장, 알림 발송 같은 단계는 템플릿 메소드와 잘 맞는다.  
하지만 훅이 복잡해지면 각 단계가 별도 전략이나 체인으로 나뉘어야 한다.

### 시나리오 2: 외부 연동 작업

공통 흐름은 같지만 인증, 변환, 전송, 재시도가 모두 다르면 hook이 폭발하기 쉽다.

### 시나리오 3: 도메인 룰 처리

비즈니스 규칙이 자꾸 달라진다면 상속보다 정책 객체가 더 안전하다.

---

## 코드로 보기

### Template Method

```java
public abstract class AbstractJob {
    public final void run() {
        before();
        execute();
        after();
    }

    protected void before() {}
    protected abstract void execute();
    protected void after() {}
}
```

### Hook가 많아지는 냄새

```java
public abstract class AbstractJob {
    public final void run() {
        beforeValidate();
        beforeExecute();
        execute();
        afterExecute();
        afterCleanup();
    }

    protected void beforeValidate() {}
    protected void beforeExecute() {}
    protected abstract void execute();
    protected void afterExecute() {}
    protected void afterCleanup() {}
}
```

이쯤 되면 상위 클래스가 흐름을 고정하는 이점보다, 하위 클래스가 알아야 할 내부 규칙이 더 많아진다.

### 대안

```java
public class JobPipeline {
    private final List<JobStep> steps;

    public void run() {
        for (JobStep step : steps) {
            step.execute();
        }
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Template Method | 흐름을 강하게 보장한다 | 훅이 많아지면 단단해진다 | 순서가 거의 고정일 때 |
| Strategy | 교체가 쉽다 | 클래스가 늘어날 수 있다 | 단계별 동작이 바뀔 때 |
| Chain/Pipeline | 단계 분리가 명확하다 | 순서 추적이 필요하다 | 전/후처리 조합이 많을 때 |

판단 기준은 다음과 같다.

- 훅이 2~3개면 템플릿이 자연스럽다
- 훅이 계속 늘어나면 냄새다
- 서브클래스가 상위 내부를 알아야 하면 구조를 다시 본다

---

## 꼬리질문

> Q: Template Method와 전략 패턴을 함께 써도 되나요?
> 의도: 패턴 조합을 이론적으로만 보지 않는지 확인한다.
> 핵심: 가능하지만, 먼저 훅이 정말 필요한지 봐야 한다.

> Q: hook이 많아지면 왜 문제가 되나요?
> 의도: 상속 기반 유연성이 오히려 약점이 되는 이유를 아는지 확인한다.
> 핵심: 내부 순서 의존성이 커지고 하위 클래스가 불안정해진다.

> Q: 템플릿 메소드가 과해졌다는 신호는 무엇인가요?
> 의도: 냄새를 조기에 감지할 수 있는지 확인한다.
> 핵심: before/after hook이 계속 늘어나면 분해를 고려해야 한다.

## 한 줄 정리

Template Hook가 많아지면 상속으로 흐름을 고정하는 장점보다, 구조가 단단해지는 비용이 더 커질 수 있다.
