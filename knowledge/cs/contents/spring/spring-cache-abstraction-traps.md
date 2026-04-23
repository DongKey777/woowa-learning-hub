# Spring Cache 추상화 함정

> 한 줄 요약: `@Cacheable`은 캐시를 쉽게 붙여주지만, 정책과 경계까지 자동으로 해결해주지는 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Cache-Control 실전](../network/cache-control-practical.md)
> - [분산 캐시 설계](../system-design/distributed-cache-design.md)

retrieval-anchor-keywords: Spring Cache abstraction, @Cacheable trap, cache key design, self invocation cacheable, cache invalidation, cache stale data, @CacheEvict, @CachePut, CacheManager boundary, transaction boundary with cache

---

## 핵심 개념

Spring Cache 추상화는 `@Cacheable`, `@CachePut`, `@CacheEvict` 같은 어노테이션으로 캐시 접근을 가려준다.

장점은 분명하다.

- 비즈니스 코드가 단순해진다
- 캐시 구현체를 바꾸기 쉽다
- 캐시 정책을 선언적으로 표현할 수 있다

하지만 함정도 분명하다.

- 캐시가 어디서 타는지 감이 사라진다
- self-invocation 때문에 어노테이션이 무시될 수 있다
- key 설계를 잘못하면 오염이 난다
- TTL, invalidation, transaction boundary가 분리되면 stale data가 생긴다

이 문서의 목적은 캐시를 “붙이는 법”이 아니라, **캐시를 붙였을 때 어디가 틀어지는지**를 보는 것이다.

---

## 깊이 들어가기

### 1. `@Cacheable`은 프록시 기반이다

Spring Cache는 AOP와 같은 방식으로 동작한다.  
즉, 메서드 호출이 프록시를 거쳐야 캐시가 적용된다.

```java
@Service
public class ProductService {

    @Cacheable(cacheNames = "product", key = "#id")
    public ProductDto findProduct(Long id) {
        return loadFromDb(id);
    }
}
```

같은 클래스 내부에서 `this.findProduct(id)`로 호출하면 캐시가 안 탈 수 있다.  
이건 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)과 같은 문제다.

### 2. key는 단순 문자열이 아니다

캐시 문제의 절반은 key 설계다.

잘못된 예:

```java
@Cacheable(cacheNames = "product", key = "#root.methodName")
public ProductDto findProduct(Long id) { }
```

이렇게 하면 id가 달라도 같은 key가 된다.

좋은 key는 보통 다음을 반영한다.

- 식별자
- 언어/지역/권한
- 필터 조건
- 조회 기준 버전

### 3. invalidation은 TTL만으로 끝나지 않는다

TTL은 편하다. 하지만 TTL만 믿으면 stale data를 어느 정도 감수하게 된다.

문제는 아래 상황이다.

- DB는 바뀌었는데 캐시는 아직 남아 있다
- 사용자별 응답인데 공용 캐시에 올라갔다
- write 후 read가 같은 트랜잭션 경계 밖에서 발생한다

즉, 캐시 만료 시간과 데이터 정합성 요구는 별개다.

### 4. Cache abstraction과 실제 캐시 시스템은 다르다

Spring Cache는 추상화고, 실제 저장소는 Redis, Caffeine, Ehcache 등일 수 있다.

| 계층 | 역할 | 대표 함정 |
|---|---|---|
| Spring Cache | 선언적 캐시 API | 어노테이션이 어디서 타는지 보이지 않는다 |
| CacheManager | 캐시 구현체 연결 | 환경별 설정이 흩어진다 |
| 실제 캐시 저장소 | 데이터 저장/만료 | TTL, eviction, replication 정책이 다르다 |

`@Cacheable`은 정책을 숨겨주지 않는다.  
정책은 결국 운영자가 책임져야 한다.

---

## 실전 시나리오

### 시나리오 1: 캐시를 붙였는데도 지연이 줄지 않는다

원인 후보:

1. cache hit ratio가 낮다
2. key가 너무 세분화되어 있다
3. self-invocation으로 캐시가 안 탄다
4. 로컬 캐시와 Redis 사이 레이어가 너무 많다

### 시나리오 2: 캐시는 맞는데 값이 가끔 오래된다

원인 후보:

- `@CacheEvict`가 write path와 분리됐다
- DB 커밋 전에 캐시를 지웠다
- 이벤트 기반 무효화가 지연된다
- TTL이 길다

이 문제는 `@Transactional`과 함께 봐야 한다.  
트랜잭션 커밋 전에 캐시를 지우면 실패 시 캐시만 날아갈 수 있다.

### 시나리오 3: 사용자별 데이터가 섞였다

`public` 성격의 key를 잘못 쓰면 사용자 A의 응답이 사용자 B에게 갈 수 있다.  
특히 인증 정보, locale, role, tenant가 key에 빠지면 위험하다.

이건 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)와도 맞닿아 있다.

---

## 코드로 보기

### 기본 cacheable

```java
@Cacheable(cacheNames = "product", key = "#id")
public ProductDto findProduct(Long id) {
    return productRepository.findDtoById(id);
}
```

### 캐시 무효화

```java
@Transactional
@CacheEvict(cacheNames = "product", key = "#id")
public void updateProduct(Long id, ProductCommand command) {
    productRepository.update(id, command);
}
```

### 조건과 unless

```java
@Cacheable(
    cacheNames = "product",
    key = "#id",
    condition = "#id > 0",
    unless = "#result == null"
)
public ProductDto findProduct(Long id) {
    return load(id);
}
```

### 커스텀 key generator

```java
@Bean
public KeyGenerator tenantAwareKeyGenerator() {
    return (target, method, params) ->
        method.getName() + ":" + params[0] + ":" + TenantContext.currentTenant();
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| `@Cacheable` | 구현이 간단하다 | 정책이 숨겨진다 | 단순 조회 캐시 |
| 수동 캐시 코드 | 흐름이 명확하다 | 중복 코드가 생긴다 | 정교한 invalidation |
| 로컬 캐시 | 빠르다 | 분산 정합성이 어렵다 | 단일 인스턴스/핫 데이터 |
| Redis 같은 외부 캐시 | 공유가 쉽다 | 네트워크/운영 비용이 있다 | 다중 인스턴스 |

핵심은 캐시를 넣는 게 아니라, **캐시가 깨지는 시점까지 설계하는 것**이다.

---

## 꼬리질문

> Q: `@Cacheable`이 self-invocation에서 안 먹는 이유는 무엇인가?
> 의도: 프록시 기반 동작 이해 확인
> 핵심: 메서드 호출이 프록시를 거쳐야 한다

> Q: key 설계를 잘못하면 어떤 사고가 생기는가?
> 의도: 캐시 오염/혼합 이해 확인
> 핵심: 다른 사용자나 다른 조건의 응답이 섞인다

> Q: TTL이 있는데도 왜 stale data가 문제인가?
> 의도: 정합성과 만료 정책 분리 이해 확인
> 핵심: TTL은 상한선일 뿐 즉시 무효화가 아니다

> Q: `@CacheEvict`와 `@Transactional`을 같이 쓸 때 왜 주의해야 하는가?
> 의도: 트랜잭션 경계와 캐시 경계 이해 확인
> 핵심: 커밋 실패와 캐시 무효화 순서를 봐야 한다

---

## 한 줄 정리

Spring Cache는 붙이기 쉽지만, key, invalidation, transaction boundary를 설계하지 않으면 더 빨리 stale data를 만든다.
