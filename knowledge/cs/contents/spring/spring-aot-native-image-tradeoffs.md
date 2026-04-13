# Spring AOT and Native Image Trade-offs

> 한 줄 요약: Spring AOT와 native image는 시작 속도와 메모리 이점을 주지만, reflection과 dynamic proxy에 의존한 설계를 바꾸지 않으면 빌드와 런타임이 더 까다로워진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Spring BeanFactoryPostProcessor vs BeanPostProcessor Lifecycle](./spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Security Method Security Deep Dive](./spring-security-method-security-deep-dive.md)

retrieval-anchor-keywords: AOT, native image, GraalVM, reflection hints, runtime hints, build-time initialization, dynamic proxy, closed world, native compatibility

## 핵심 개념

Spring AOT는 애플리케이션이 시작하기 전에 reflection, proxy, resource access 같은 동적 요소를 미리 분석해 준비하는 접근이다.

native image는 그 결과를 기반으로 더 빨리 시작하고 더 적은 메모리를 쓰도록 만든다.

하지만 이건 단순 배포 포맷 변화가 아니다.

- 런타임 동작이 빌드 시점으로 이동한다
- reflection과 proxy 사용을 명시적으로 관리해야 한다
- 동적 코드가 많은 설계는 호환성 비용이 커진다

## 깊이 들어가기

### 1. AOT는 build-time analysis다

Spring은 애플리케이션 컨텍스트를 미리 분석해 실행에 필요한 힌트를 만든다.

- 어떤 bean이 필요할지
- 어떤 reflection이 필요한지
- 어떤 proxy가 필요할지

### 2. native image는 closed-world 가정이 강하다

GraalVM native image는 런타임에 "새 클래스가 갑자기 필요할 것"이라는 가정을 약하게 가져간다.

그래서 다음이 중요하다.

- reflection hints
- runtime hints
- proxy hints
- resource hints

### 3. 동적 프록시와 리플렉션이 많은 코드가 민감하다

`@Configuration`, AOP, validation, serialization, MVC binding, security method proxy는 모두 힌트와 관련된다.

이 문맥은 [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)과 같이 봐야 한다.

### 4. 시작 속도와 디버깅 난이도는 다른 문제다

native image는 빠르게 뜨지만, 스택트레이스, reflection error, unsupported feature 처리가 까다로울 수 있다.

### 5. 모든 서비스가 native image 후보는 아니다

좋은 후보:

- CLI
- 짧게 실행되는 worker
- cold start가 중요한 API

조심할 후보:

- reflection-heavy framework extension
- dynamic plugin style
- 런타임 코드 생성이 많은 서비스

## 실전 시나리오

### 시나리오 1: 로컬에서는 되는데 native build에서 깨진다

대개 reflection hint가 빠졌거나 dynamic proxy가 누락됐다.

### 시나리오 2: 시작 속도는 빨라졌는데 특정 기능이 안 된다

런타임에만 만들어지던 타입이 빌드 시점에 드러나지 않았을 수 있다.

### 시나리오 3: Spring Security나 MVC가 native에서 까다롭다

프록시와 바인딩 힌트가 많기 때문이다.

### 시나리오 4: Boot auto-config를 많이 쓰는데 native 호환성이 애매하다

조건부 구성이 많을수록 힌트와 검증이 중요하다.

## 코드로 보기

### runtime hints registrar

```java
@ImportRuntimeHints(AppRuntimeHints.class)
public class NativeConfig {
}
```

```java
public class AppRuntimeHints implements RuntimeHintsRegistrar {

    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // reflection/proxy/resource hints
    }
}
```

### AOT-friendly configuration

```java
@Configuration(proxyBeanMethods = false)
public class AotFriendlyConfig {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| JVM mode | 유연하고 디버깅이 쉽다 | 시작이 느릴 수 있다 | 일반적인 서버 |
| AOT + JVM | 일부 최적화 이득 | 빌드 복잡도 증가 | Boot 최적화 |
| native image | 빠른 start, 낮은 memory | 호환성 제약이 크다 | cold start 민감 워크로드 |

핵심은 native image가 "더 좋은 자바"가 아니라, **동적 기능을 줄이고 빌드 시점에 계약을 확정하는 배포 전략**이라는 점이다.

## 꼬리질문

> Q: Spring AOT가 해결하려는 문제는 무엇인가?
> 의도: 빌드 시점 분석 이해 확인
> 핵심: 런타임 동적 비용을 줄이기 위해서다.

> Q: native image에서 reflection이 까다로운 이유는 무엇인가?
> 의도: closed-world 가정 이해 확인
> 핵심: 런타임에 임의 타입을 찾기 어렵기 때문이다.

> Q: `proxyBeanMethods`와 native image는 왜 연관이 있는가?
> 의도: proxy/hint 비용 이해 확인
> 핵심: 프록시와 동적 호출이 많을수록 힌트 관리가 복잡해진다.

> Q: native image가 모든 서비스에 맞지 않는 이유는 무엇인가?
> 의도: 배포 전략 판단 확인
> 핵심: 동적 기능과 디버깅 비용이 크기 때문이다.

## 한 줄 정리

Spring AOT/native image는 시작 속도와 메모리를 개선하지만, reflection과 dynamic proxy 의존도를 줄이지 않으면 호환성과 유지보수 비용이 커진다.
