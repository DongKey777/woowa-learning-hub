---
schema_version: 3
title: "Spring Bean 생명주기 기초: 스프링이 객체를 어떻게 만들어주는지 큰 그림"
concept_id: "spring/bean-lifecycle-basics"
canonical: true
category: "spring"
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
review_feedback_tags:
- bean-lifecycle
- postconstruct
- predestroy
- spring
aliases:
  - bean lifecycle
  - Spring Bean lifecycle
  - PostConstruct
  - PreDestroy
  - 빈 생명주기
  - 빈 라이프사이클
  - 스프링 빈 생성
  - 스프링 빈 소멸
intents:
  - definition
  - design
prerequisites:
  - spring/bean-di-basics
next_docs:
  - spring/bean-lifecycle-scope-traps
linked_paths:
- contents/spring/spring-bean-lifecycle-scope-traps.md
- contents/network/http-state-session-cache.md
  - contents/spring/spring-bean-di-basics.md
  - contents/spring/ioc-di-container.md
forbidden_neighbors:
  - contents/spring/spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md
  - contents/spring/spring-bean-definition-registry-postprocessor-import-registrar.md
expected_queries:
  - Spring Bean은 언제 만들어져?
  - Bean 생명주기가 뭐야?
  - PostConstruct는 언제 실행돼?
  - prototype Bean도 PreDestroy가 호출돼?
  - 스프링이 객체를 어떻게 만들어?
contextual_chunk_prefix: |
  이 문서는 Spring DI를 학습한 입문자가 스프링이 객체를 어떻게 만들어주는지
  큰 그림을 잡을 때 — Bean이 언제 만들어지고 언제 사라지는지, 컨테이너가
  객체 라이프사이클을 어떻게 관리하는지 — 처음 보는 primer다. 스프링이
  객체를 어떻게 만들어주는지 큰 그림, 객체가 언제 생기고 사라지나, 컨테이너
  시작 시 Bean 생성, @PostConstruct 초기화, @PreDestroy 정리, 객체 생성
  ~소멸 큰 흐름 같은 자연어 paraphrase가 본 문서의 단계 흐름에 매핑된다.
---
# Spring Bean 생명주기 기초: 생성부터 소멸까지

> 한 줄 요약: Spring Bean은 컨테이너 시작 시 생성되고, `@PostConstruct`로 초기화 작업을 할 수 있으며, `@PreDestroy`로 소멸 전 정리 작업을 할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
- [Spring Bean과 DI 기초](./spring-bean-di-basics.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring bean lifecycle basics, spring bean 생명주기 입문, spring bean 생명주기 뭐예요, 스프링 빈 생명주기 큰 그림, bean lifecycle 처음 배우는데, @postconstruct @predestroy 기초, spring bean 초기화 콜백, spring bean 소멸 콜백, singleton prototype 차이 기초, request scope session scope 뭐예요, spring bean 언제 만들어지나, 왜 postconstruct 에서 transactional 안 먹어요, spring bean 생성 순서, 빈 생성 주입 초기화 차이, 스프링 빈 처음 배우는데 언제 쓰는지, 스프링이 객체를 어떻게 만들어주는지 큰 그림, 컨테이너가 객체를 언제 만들고 초기화하고 소멸시키는지

## 핵심 개념

Spring Bean을 처음 배울 때는 "그냥 Spring이 대신 만드는 객체" 정도로 들리기 쉽다. 그런데 실제로는 **언제 만들어지고, 주입이 언제 끝나고, 언제 정리되는지**가 정해져 있다. 이 큰 그림을 먼저 잡아야 `@PostConstruct`가 왜 필요한지, 왜 `@Transactional`이 거기서 기대대로 안 붙을 수 있는지, 왜 singleton/prototype 차이를 따로 봐야 하는지가 이어진다.

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

헷갈리기 쉬운 표현을 먼저 번역해 두면 더 쉽다.

| 자주 하는 말 | 실제로 구분해야 하는 시점 |
|---|---|
| "bean이 만들어졌다" | 생성자 호출까지 끝난 상태 |
| "이제 써도 된다" | 주입과 초기화까지 끝난 상태 |
| "`@Transactional`도 같이 붙겠지?" | 프록시 적용까지 끝났는지 별도로 봐야 한다 |

## 상세 분해

- **생성자 호출**: 의존성 주입이 아직 완료되지 않은 시점이다. 생성자에서 주입받은 필드 외의 다른 Bean에 접근하면 null이 될 수 있다.
- **`@PostConstruct`**: 의존성 주입이 모두 완료된 뒤 호출된다. 외부 시스템 연결 확인, 데이터 로딩, 상태 초기화에 적합하다.
- **`@PreDestroy`**: 컨테이너가 종료될 때 호출된다. DB 커넥션, 파일 핸들, 스레드풀 같은 리소스를 해제하는 코드를 둔다.
- **singleton scope**: 기본 scope. 컨테이너 하나에 Bean 인스턴스 하나가 만들어져 공유된다. 컨테이너 시작 시 생성, 종료 시 소멸.
- **prototype scope**: 요청할 때마다 새 인스턴스가 만들어진다. `@PreDestroy`가 호출되지 않으므로 리소스 정리를 직접 해야 한다.

초보자가 처음엔 아래 세 줄만 구분해도 충분하다.

- 생성은 "객체 껍데기가 생김"
- 초기화는 "주입이 끝나고 준비 작업까지 마침"
- 프록시는 "실제 객체 바깥에 호출용 래퍼가 붙음"

이 순서를 머리에 두면 "`@PostConstruct` 안에서 왜 프록시 기반 기능을 기대하면 안 되지?"가 자연스럽게 이어진다.

## 흔한 오해와 함정

**오해 1: `@PostConstruct`에서 프록시 기능을 기대할 수 있다**
`@PostConstruct`는 프록시 적용 전에 실행된다. 이 메서드 안에서 `@Transactional`이 붙은 다른 메서드를 self 호출하면 트랜잭션이 걸리지 않을 수 있다.

**오해 2: prototype scope Bean도 `@PreDestroy`가 호출된다**
호출되지 않는다. prototype Bean의 소멸 시점 관리는 사용하는 쪽이 책임진다.

**오해 3: singleton Bean에 요청별 상태를 저장해도 된다**
singleton은 모든 요청이 공유하는 하나의 인스턴스다. `currentUserId` 같은 가변 필드를 두면 요청 간 데이터가 섞일 수 있다.

**오해 4: 생성자와 `@PostConstruct`는 아무 때나 바꿔 써도 된다**
생성자는 "필수 의존성을 받아 객체를 성립시키는 자리"이고, `@PostConstruct`는 "주입이 끝난 뒤 준비 작업을 하는 자리"다. DB 연결 확인, 캐시 예열처럼 외부 협력이 필요한 작업은 보통 `@PostConstruct` 쪽이 더 자연스럽다.

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

아래처럼 쓰임새를 나누면 감이 더 빠르다.

| 코드 위치 | 넣기 좋은 일 | 피하는 편이 좋은 일 |
|---|---|---|
| 생성자 | 필수 의존성 저장, 불변 필드 세팅 | 외부 호출, 긴 준비 작업 |
| `@PostConstruct` | 캐시 예열, 설정 검증, 연결 확인 | self 호출로 프록시 기능 기대 |
| `@PreDestroy` | 스레드풀 종료, 연결 정리 | 새 작업 시작 |

## 더 깊이 가려면

- scope 종류(request, session, prototype)별 생명주기 함정은 [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)에서 더 자세히 다룬다.
- `BeanPostProcessor`, `SmartInitializingSingleton` 같은 확장 포인트는 고급 주제에 해당한다.
- Bean 등록 전체 흐름은 [IoC 컨테이너와 DI](./ioc-di-container.md)에서 이어서 볼 수 있다.
- session scope가 왜 HTTP 세션과 연결되는지는 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)에서 같이 보면 덜 헷갈린다.

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
