---
schema_version: 3
title: Spring Cache Key Generation Pitfalls
concept_id: spring/cache-key-generation-pitfalls
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 80
review_feedback_tags:
- cache-key-generation
- pitfalls
- keygenerator
- cache-key-collision
aliases:
- Spring cache key generation
- KeyGenerator
- cache key collision
- cache poisoning
- tenant-aware cache key
- locale-aware cache key
- cache invalidation
intents:
- troubleshooting
- design
symptoms:
- cache hit은 되는데 사용자, 권한, tenant, locale이 다른 응답이 섞인다.
- @Cacheable key가 id만 포함해서 page, sort, filter, version 차이를 구분하지 못한다.
- self-invocation이나 잘못된 invalidation 때문에 cache가 갱신되지 않은 값처럼 보인다.
linked_paths:
- contents/spring/spring-cache-abstraction-traps.md
- contents/spring/aop-proxy-mechanism.md
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-open-session-in-view-tradeoffs.md
- contents/spring/spring-test-slices-context-caching.md
expected_queries:
- Spring Cache key에는 어떤 값을 반드시 포함해야 해?
- tenant나 locale을 cache key에서 빼면 왜 데이터 오염이 생겨?
- @Cacheable key collision과 cache poisoning을 어떻게 구분해?
- Spring Cache에서 custom KeyGenerator는 언제 필요해?
contextual_chunk_prefix: |
  이 문서는 Spring Cache의 @Cacheable key 설계, KeyGenerator, tenant/locale/auth
  role/page/sort/filter/version 누락, cache poisoning, key collision,
  self-invocation과 invalidation 함정을 다룬다. 저장소 장애보다 key identity
  계약이 먼저 깨지는 문제를 진단하는 playbook이다.
---
# Spring Cache Key Generation Pitfalls

> 한 줄 요약: 캐시의 실패는 저장소보다 key 설계에서 먼저 시작되며, key가 불완전하면 캐시 히트가 아니라 데이터 오염이 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)

retrieval-anchor-keywords: cache key generation, key generator, cache poisoning, key collision, tenant-aware key, locale-aware key, cache invalidation, self invocation

## 핵심 개념

Spring Cache에서 key는 단순 문자열이 아니다.

그 key가 무엇을 식별하는지 명확해야 한다.

- 사용자별인지
- 테넌트별인지
- locale별인지
- 권한별인지
- 필터 조건별인지

key가 이 정보를 빠뜨리면 캐시는 빨라지는 대신 틀린 응답을 줄 수 있다.

## 깊이 들어가기

### 1. key는 응답의 정체성을 표현한다

```java
@Cacheable(cacheNames = "product", key = "#id")
public ProductDto find(Long id) {
    ...
}
```

이 key는 단순해 보이지만, 실제로는 "id만 같으면 같은 응답"이라는 계약이다.

그 계약이 맞는지 먼저 봐야 한다.

### 2. key에 빠지기 쉬운 요소들이 있다

- tenant id
- locale
- auth role
- page/sort/filter
- version

예를 들어 같은 product id라도 사용자 권한에 따라 내려가는 필드가 다르면 key가 같으면 안 된다.

### 3. collisions보다 더 무서운 것은 silent misuse다

key collision은 드러나기 쉽지만, 더 위험한 건 "틀린 key인데도 cache hit처럼 보이는 경우"다.

이 경우 장애가 아니라 정합성 문제로 남는다.

### 4. key generator는 규칙을 강제하는 도구다

```java
@Bean
public KeyGenerator tenantLocaleKeyGenerator() {
    return (target, method, params) -> {
        return method.getName() + ":" + TenantContext.currentTenant()
            + ":" + LocaleContextHolder.getLocale()
            + ":" + Arrays.deepToString(params);
    };
}
```

이런 식으로 공통 규칙을 두면 key 실수를 줄일 수 있다.

### 5. invalidation은 key 설계와 같이 봐야 한다

무효화가 잘 안 되는 경우는 key가 너무 넓거나 너무 좁을 때다.

- 너무 넓다: 서로 다른 응답이 같은 key로 묶인다
- 너무 좁다: 캐시 히트율이 너무 낮아진다

## 실전 시나리오

### 시나리오 1: 사용자 A 응답이 사용자 B에게 간다

원인 후보:

- locale이 key에 빠졌다
- tenant가 key에 빠졌다
- role별 응답 차이를 무시했다

### 시나리오 2: key는 맞는데 히트율이 낮다

대개 key가 너무 세분화되어 있다.

- timestamp를 넣었다
- page size와 sort가 불필요하게 다양하다
- request header를 전부 key에 넣었다

### 시나리오 3: 캐시를 지웠는데도 값이 계속 보인다

다른 key를 지우고 있었거나, 조회 path와 invalidation path가 다른 규칙을 쓰고 있을 수 있다.

### 시나리오 4: `@Cacheable`은 맞는데 self-invocation으로 안 탄다

이 문제는 [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)과 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)에서 보는 전형적 함정이다.

## 코드로 보기

### 잘못된 key

```java
@Cacheable(cacheNames = "product", key = "#id")
public ProductDto findForViewer(Long id) {
    ...
}
```

### tenant-aware key generator

```java
@Bean
public KeyGenerator productKeyGenerator() {
    return (target, method, params) ->
        TenantContext.currentTenant() + ":" + Arrays.deepToString(params);
}
```

### cacheable with compound key

```java
@Cacheable(cacheNames = "feed", key = "#userId + ':' + #locale")
public FeedDto findFeed(Long userId, String locale) {
    ...
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단순 key | 쉽다 | 오염 위험이 있다 | 정말 식별자가 하나일 때 |
| compound key | 안전하다 | 길어질 수 있다 | locale/tenant/role 반영 |
| custom KeyGenerator | 규칙을 강제할 수 있다 | 코드가 늘어난다 | 여러 캐시에서 공통 규칙 |
| raw method args | 구현이 빠르다 | 의도를 숨기기 쉽다 | 아주 단순한 경우 |

핵심은 key를 "캐시 주소"로 보고, **응답 정체성이 무엇인지 먼저 정의하는 것**이다.

## 꼬리질문

> Q: 캐시 key 설계에서 가장 먼저 봐야 하는 것은 무엇인가?
> 의도: 응답 정체성 이해 확인
> 핵심: 어떤 조건이 결과를 바꾸는지다.

> Q: key collision보다 더 위험한 것은 무엇인가?
> 의도: 조용한 데이터 오염 이해 확인
> 핵심: 틀린 key로 캐시 히트가 나는 경우다.

> Q: tenant/locale/role이 key에 빠지면 어떤 문제가 생기는가?
> 의도: 멀티테넌트/권한 캐시 인식 확인
> 핵심: 다른 사용자에게 잘못된 응답이 갈 수 있다.

> Q: custom KeyGenerator를 쓰는 이유는 무엇인가?
> 의도: 규칙 강제 이해 확인
> 핵심: 캐시 key 규칙을 한곳에서 통일하기 위해서다.

## 한 줄 정리

캐시 key는 성능 최적화의 부품이 아니라 응답 정체성을 표현하는 계약이므로, 빠뜨린 축이 있으면 캐시가 데이터를 오염시킨다.
