# Spring Bean 생명주기 기초: 생성부터 소멸까지

> 한 줄 요약: Spring Bean은 컨테이너 시작 시 생성되고, `@PostConstruct`로 초기화 작업을 할 수 있으며, `@PreDestroy`로 소멸 전 정리 작업을 할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
- [Spring Bean과 DI 기초](./spring-bean-di-basics.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring bean lifecycle basics, spring bean 생명주기 입문, @postconstruct @predestroy 기초, spring bean 초기화 콜백, spring bean 소멸 콜백, singleton scope basics, bean scope beginner, prototype bean basics, spring bean 언제 만들어지나, spring bean created when, spring initialization callback, spring destroy callback, spring bean 생성 순서, spring bean lifecycle basics basics, spring bean lifecycle basics beginner

## 핵심 개념

Spring Bean은 단순히 "컨테이너에 등록된 객체"가 아니라, 생성부터 소멸까지 명확한 생명주기를 가진 객체다. 이 흐름을 모르면 `@PostConstruct`가 생각대로 동작하지 않거나, 리소스 정리 코드가 소멸 시점에 호출되지 않는 문제를 만나게 된다.

입문자가 자주 놓치는 포인트는 Bean 생성 직후와 의존성 주입 완료 후의 차이, 그리고 scope에 따라 생성 시점이 달라진다는 점이다.

## 한눈에 보기

```text
BeanDefinition 등록
  -> 생성자 호출 (객체 생성)
  -> 의존성 주입 완료
  -> @PostConstruct 메서드 실행 (초기화 콜백)
  -> 프록시 적용 (AOP 등)
  -> 사용
  -> 컨테이너 종료 시 @PreDestroy 메서드 실행
  -> 소멸
```

| 시점 | 콜백 | 역할 |
|---|---|---|
| 의존성 주입 완료 직후 | `@PostConstruct` | 초기화, 연결 검증, 캐시 예열 |
| 컨테이너 종료 직전 | `@PreDestroy` | 리소스 해제, 연결 종료 |

## 상세 분해

- **생성자 호출**: 의존성 주입이 아직 완료되지 않은 시점이다. 생성자에서 주입받은 필드 외의 다른 Bean에 접근하면 null이 될 수 있다.
- **`@PostConstruct`**: 의존성 주입이 모두 완료된 뒤 호출된다. 외부 시스템 연결 확인, 데이터 로딩, 상태 초기화에 적합하다.
- **`@PreDestroy`**: 컨테이너가 종료될 때 호출된다. DB 커넥션, 파일 핸들, 스레드풀 같은 리소스를 해제하는 코드를 둔다.
- **singleton scope**: 기본 scope. 컨테이너 하나에 Bean 인스턴스 하나가 만들어져 공유된다. 컨테이너 시작 시 생성, 종료 시 소멸.
- **prototype scope**: 요청할 때마다 새 인스턴스가 만들어진다. `@PreDestroy`가 호출되지 않으므로 리소스 정리를 직접 해야 한다.

## 흔한 오해와 함정

**오해 1: `@PostConstruct`에서 프록시 기능을 기대할 수 있다**
`@PostConstruct`는 프록시 적용 전에 실행된다. 이 메서드 안에서 `@Transactional`이 붙은 다른 메서드를 self 호출하면 트랜잭션이 걸리지 않을 수 있다.

**오해 2: prototype scope Bean도 `@PreDestroy`가 호출된다**
호출되지 않는다. prototype Bean의 소멸 시점 관리는 사용하는 쪽이 책임진다.

**오해 3: singleton Bean에 요청별 상태를 저장해도 된다**
singleton은 모든 요청이 공유하는 하나의 인스턴스다. `currentUserId` 같은 가변 필드를 두면 요청 간 데이터가 섞일 수 있다.

## 실무에서 쓰는 모습

초기화와 소멸 콜백의 전형적인 활용 예다.

```java
@Component
public class CacheWarmup {

    private final DataLoader dataLoader;

    public CacheWarmup(DataLoader dataLoader) {
        this.dataLoader = dataLoader;
    }

    @PostConstruct
    public void init() {
        // 의존성 주입이 완료된 뒤 실행 - dataLoader 사용 가능
        dataLoader.loadInitialData();
    }

    @PreDestroy
    public void cleanup() {
        // 컨테이너 종료 직전 실행 - 리소스 정리
        dataLoader.close();
    }
}
```

`@PostConstruct` 안에서는 주입받은 `dataLoader`를 안전하게 사용할 수 있다.

## 더 깊이 가려면

- scope 종류(request, session, prototype)별 생명주기 함정은 [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)에서 더 자세히 다룬다.
- `BeanPostProcessor`, `SmartInitializingSingleton` 같은 확장 포인트는 고급 주제에 해당한다.
- Bean 등록 전체 흐름은 [IoC 컨테이너와 DI](./ioc-di-container.md)에서 이어서 볼 수 있다.

## 면접/시니어 질문 미리보기

> Q: `@PostConstruct`와 생성자 중 어느 시점이 더 늦은가?
> 의도: 생명주기 순서 이해 확인
> 핵심: `@PostConstruct`는 생성자 호출과 의존성 주입이 모두 끝난 뒤에 실행된다.

> Q: singleton Bean에 mutable 상태를 두면 왜 위험한가?
> 의도: scope와 공유 상태 이해 확인
> 핵심: singleton은 하나의 인스턴스를 모든 요청이 공유하므로 요청별 상태를 필드에 저장하면 충돌한다.

> Q: prototype scope Bean의 소멸 관리는 누가 해야 하는가?
> 의도: prototype 생명주기 이해 확인
> 핵심: 컨테이너가 `@PreDestroy`를 호출하지 않으므로 사용하는 쪽이 직접 정리해야 한다.

## 한 줄 정리

Spring Bean 생명주기는 생성 → 주입 → `@PostConstruct` → 사용 → `@PreDestroy` → 소멸이고, singleton의 공유 특성과 prototype의 `@PreDestroy` 미호출을 입문 단계에서 반드시 알아야 한다.
