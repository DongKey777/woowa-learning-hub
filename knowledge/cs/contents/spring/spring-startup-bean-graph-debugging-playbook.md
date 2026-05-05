---
schema_version: 3
title: Spring Startup Bean Graph Debugging Playbook
concept_id: spring/startup-bean-graph-debugging-playbook
canonical: false
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 78
mission_ids: []
review_feedback_tags:
- startup-root-cause-triage
- condition-report-first
- bean-graph-vs-config-binding
aliases:
- startup debugging
- BeanCreationException
- UnsatisfiedDependencyException
- condition evaluation report
- config properties binding
- bean graph
symptoms:
- 애플리케이션이 부팅하다가 죽는데 Bean 그래프 문제인지 설정 바인딩 문제인지 구분이 안 돼요
- startup 로그에 BeanCreationException만 길게 보여서 어디서부터 읽어야 할지 모르겠어요
- 스타터는 넣었는데 어떤 자동 구성이 빠졌는지 몰라서 앱이 안 떠요
- 순환 참조인지 조건 탈락인지 헷갈려서 startup 장애를 계속 잘못 짚고 있어요
intents:
- troubleshooting
- design
prerequisites:
- spring/ioc-container-internals
- spring/boot-autoconfiguration-internals
- spring/application-context-refresh-phases
next_docs:
- spring/boot-autoconfiguration-internals
- spring/ioc-container-internals
- spring/component-scan-failure-patterns
linked_paths:
- contents/spring/spring-boot-condition-evaluation-report-debugging.md
- contents/spring/spring-application-context-refresh-phases.md
- contents/spring/ioc-di-container.md
- contents/spring/spring-early-bean-reference-circular-proxy-traps.md
- contents/spring/spring-configurationproperties-binding-internals.md
- contents/spring/spring-configuration-proxybeanmethods-beanpostprocessor-chain.md
- contents/database/slow-query-analysis-playbook.md
confusable_with:
- spring/bean-not-found-cause-router
- spring/component-scan-failure-patterns
- spring/boot-autoconfiguration-internals
forbidden_neighbors: []
expected_queries:
- Spring startup failure가 났을 때 Bean 그래프, condition, config binding 중 어디부터 분기해야 해?
- BeanCreationException만 보이는 부팅 실패를 root cause까지 어떻게 추적해?
- 스타터를 넣었는데 앱이 안 뜰 때 condition report를 먼저 봐야 하는 이유가 뭐야?
- 순환 참조와 설정 바인딩 실패가 섞여 보일 때 startup 장애를 어떻게 분류해?
- Spring 애플리케이션이 시작 중 죽으면 로그를 어떤 순서로 읽어야 해?
contextual_chunk_prefix: |
  이 문서는 Spring 애플리케이션이 startup 중 죽을 때 Bean graph, 조건부 자동 구성,
  프록시와 후처리 순서, configuration properties binding 실패를 먼저 어떤 질문으로
  분기해야 하는지 정리한 playbook이다. BeanCreationException만 길게 보이는 부팅
  실패, ConditionEvaluationReport를 어디서 읽어야 하는지, 순환 참조인지 설정
  바인딩 실패인지 헷갈리는 상황 같은 자연어 증상을 startup root-cause triage
  순서로 연결한다.
---

# Spring Startup Bean Graph Debugging Playbook

> 한 줄 요약: Spring startup 장애는 대개 Bean 그래프, 조건부 자동 구성, 프록시/후처리 순서, 설정 바인딩 중 어디서 깨졌는지 분류하면 풀리며, 로그를 끝까지 읽지 않으면 원인보다 증상만 좇게 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring Early Bean References and Circular Proxy Traps](./spring-early-bean-reference-circular-proxy-traps.md)
> - [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)

retrieval-anchor-keywords: startup debugging, BeanCreationException, UnsatisfiedDependencyException, NoSuchBeanDefinitionException, BeanCurrentlyInCreationException, condition evaluation report, config properties binding, not eligible for processing, bean graph

## 핵심 개념

Spring startup 실패는 처음 보면 전부 비슷해 보인다.

- Bean 생성 실패
- 의존성 주입 실패
- 자동 구성 누락
- 순환 참조
- 설정 바인딩 실패

하지만 디버깅은 이들을 한 덩어리로 보면 오래 걸린다.

실무에서 startup 장애는 보통 아래 다섯 갈래 중 하나로 분류하면 빨라진다.

1. Bean 정의가 아예 없다
2. Bean은 있는데 조건/프로필/설정 때문에 선택되지 않았다
3. Bean 생성 중 다른 Bean 그래프와 순환/초기화 순서가 꼬였다
4. 프록시/후처리/팩토리 단계에서 기대한 객체가 아니게 되었다
5. `@ConfigurationProperties`나 외부 설정 바인딩이 실패했다

즉 startup 디버깅의 핵심은 "에러를 읽는다"보다, **실패 지점을 bean graph / condition / lifecycle / config binding으로 먼저 분류하는 것**이다.

## 깊이 들어가기

### 1. 예외는 항상 맨 아래 root cause까지 본다

Spring startup 로그는 wrapper exception이 많다.

- `BeanCreationException`
- `UnsatisfiedDependencyException`
- `BeanInstantiationException`

하지만 실제 원인은 더 안쪽에 있을 때가 많다.

- `NoSuchBeanDefinitionException`
- `BeanCurrentlyInCreationException`
- `BindException`
- classpath 관련 `ClassNotFoundException`

그래서 첫 단계는 단순하다.

- 위쪽 요약 메시지에 반응하지 않는다
- cause chain의 가장 안쪽까지 읽는다
- "어느 bean이 누구를 만들다 실패했는가"를 적는다

### 2. missing bean과 wrong bean은 다르게 본다

대표적인 startup 실패는 "의존성을 찾을 수 없다"지만, 실제 의미는 둘로 갈린다.

- 정말 Bean이 없다
- Bean은 있는데 qualifier/type/조건이 안 맞는다

예를 들면:

- component scan 범위 밖이다
- profile이 달라 활성화되지 않았다
- `@ConditionalOnMissingBean`에 가로막혔다
- 같은 타입이 여러 개라 모호하다

즉 `NoSuchBeanDefinitionException` 하나만 봐도, **정의 부재인지 선택 실패인지**를 나눠야 한다.

### 3. 순환/초기화 순서는 "누가 너무 일찍 누구를 찾는가"의 문제다

다음 증상은 lifecycle 문제를 의심하기 좋다.

- `BeanCurrentlyInCreationException`
- early reference 관련 경고
- "not eligible for getting processed by all BeanPostProcessors"

이런 경우는 보통 Bean 그래프만 보는 것으로 부족하다.

함께 봐야 하는 것:

- constructor cycle인지
- `@Lazy` / `ObjectProvider`가 끼었는지
- 어떤 post processor가 proxy를 만들고 있는지
- final적으로 주입된 것이 raw target인지 proxy인지

즉 startup 장애가 wiring 문제가 아니라, **생성 시점과 후처리 순서 문제**일 수 있다.

### 4. 자동 구성 문제는 추측보다 ConditionEvaluationReport가 빠르다

특히 Boot에서 "분명 스타터를 넣었는데 Bean이 없다"는 문제는 감으로 고치기 쉽다.

하지만 대개 더 빠른 길은 다음이다.

- `--debug`
- `debug=true`
- `logging.level.org.springframework.boot.autoconfigure.condition=TRACE`

그리고 [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md) 문맥으로 바로 들어가는 것이다.

핵심은 startup 문제의 일부가 "Bean 생성 실패"가 아니라, **애초에 자동 구성 후보가 조건에서 탈락한 결과**라는 점이다.

### 5. 설정 바인딩 실패는 Bean 그래프보다 먼저 터질 수도 있다

`@ConfigurationProperties` 오류는 의외로 wiring 오류처럼 보이기도 한다.

대표 신호:

- 숫자/Duration/URI 타입 변환 실패
- validation 실패
- prefix 오타
- 환경 변수 이름 매핑 오해

이런 경우는 Bean 그래프를 오래 보지 말고, **property source와 binding 메시지**로 바로 내려가는 편이 낫다.

### 6. startup 디버깅은 "한 Bean 고치기"보다 실패 패턴을 표준화하는 게 효율적이다

운영 팀이나 팀 내 공통 플레이북 관점에서는 아래 분류가 특히 유용하다.

- missing definition
- ambiguous candidate
- conditional skip
- circular / early reference
- binding / validation failure
- factory method exception

이렇게 분류하면 매번 로그를 처음부터 해석하지 않아도 된다.

## 실전 시나리오

### 시나리오 1: `UnsatisfiedDependencyException`이 터졌다

가장 먼저 볼 것:

- 안쪽 cause가 `NoSuchBeanDefinitionException`인지
- 같은 타입 Bean이 여러 개인지
- profile/conditional bean인지

겉으로는 주입 실패지만 실제론 정의 부재가 아닐 수도 있다.

### 시나리오 2: 스타터를 넣었는데 Bean이 안 생긴다

이건 Bean graph보다 먼저 condition report를 보는 편이 빠르다.

특히 클래스패스, property, 사용자 정의 Bean 충돌을 먼저 확인한다.

### 시나리오 3: startup은 되다 말다 하고, 어떤 로그에는 "not eligible for processing"가 보인다

이건 단순 wiring이 아니라 BeanPostProcessor/early reference 문제일 가능성이 있다.

프록시 기반 기능이 조용히 빠질 수도 있으니 주의해서 봐야 한다.

### 시나리오 4: `@ConfigurationProperties`가 틀렸는데 controller/service Bean 생성 실패처럼 보인다

실제 root cause는 binding/validation일 수 있다.

startup 장애는 최종 실패 Bean만 보고 추적하면 방향을 잃기 쉽다.

## 코드로 보기

### auto-configuration debug

```properties
debug=true
logging.level.org.springframework.boot.autoconfigure.condition=TRACE
```

### beans/support debug

```properties
logging.level.org.springframework.beans.factory.support=DEBUG
logging.level.org.springframework.beans.factory.annotation=DEBUG
```

### config binding debug

```properties
logging.level.org.springframework.boot.context.properties=DEBUG
```

### 간단한 점검 질문

```text
1. 실패한 최종 bean 이름은 무엇인가?
2. root cause는 missing bean / condition skip / circular reference / binding failure 중 무엇인가?
3. proxy가 붙어야 하는 bean이 early reference로 새고 있지는 않은가?
4. 테스트/로컬/CI에서 profile/property/classpath 차이가 있는가?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| root cause 중심 추적 | 가장 정확하다 | 로그를 끝까지 읽어야 한다 | 모든 startup 장애 |
| condition report 우선 확인 | 자동 구성 문제를 빨리 좁힌다 | wiring/순환 문제엔 직접 답이 아닐 수 있다 | Boot autoconfig 의심 시 |
| 로그 레벨 상승 | 증거가 많아진다 | 로그가 시끄러워진다 | 로컬/CI 재현 시 |
| 추측성 수정 반복 | 즉흥적으로 빠르다 | 원인 학습과 재발 방지에 약하다 | 권장하지 않음 |

핵심은 startup 실패를 "빈 하나가 안 떴다"가 아니라, **Bean 그래프가 어느 단계에서 어떤 이유로 끊겼는지 찾는 작업**으로 보는 것이다.

## 꼬리질문

> Q: startup 장애에서 가장 먼저 할 일은 무엇인가?
> 의도: 디버깅 순서 확인
> 핵심: wrapper 예외가 아니라 가장 안쪽 root cause까지 읽는 것이다.

> Q: `NoSuchBeanDefinitionException`이 곧바로 component scan 누락만 뜻하지 않는 이유는 무엇인가?
> 의도: missing vs selection failure 구분 확인
> 핵심: profile, conditional skip, qualifier mismatch 등도 같은 증상으로 보일 수 있다.

> Q: condition report는 언제 먼저 보는 것이 좋은가?
> 의도: 자동 구성 디버깅 분기 확인
> 핵심: 스타터/자동 구성/프로퍼티 조건 문제를 의심할 때다.

> Q: "not eligible for getting processed by all BeanPostProcessors" 로그가 왜 중요한가?
> 의도: lifecycle/proxy 문제 감지 확인
> 핵심: 일부 bean이 후처리나 프록시 적용을 완전히 받지 못했을 가능성을 시사하기 때문이다.

## 한 줄 정리

Spring startup 장애는 root cause를 bean graph, condition, lifecycle, binding 중 어디로 분류하느냐에 따라 절반 이상이 풀린다.
