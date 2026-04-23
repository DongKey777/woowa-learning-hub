# 데코레이터와 프록시 기초 (Decorator and Proxy Basics)

> 한 줄 요약: 데코레이터는 원본 객체에 기능을 덧씌우는 래퍼이고, 프록시는 접근 자체를 제어하는 대리자인데, 겉모양이 비슷해서 헷갈리기 쉽다.

**난이도: 🟢 Beginner**

관련 문서:

- [데코레이터 vs 프록시 — 심화](./decorator-vs-proxy.md)
- [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [AOP와 프록시 메커니즘](../spring/aop-proxy-mechanism.md)

retrieval-anchor-keywords: decorator pattern basics, proxy pattern basics, 데코레이터 패턴, 프록시 패턴, decorator vs proxy beginner, wrapper pattern, 기능 추가 래퍼, 접근 제어 대리자, spring aop proxy, 데코레이터가 뭔가요, 프록시가 뭔가요, decorator proxy difference, beginner wrapper patterns, 로깅 데코레이터

---

## 핵심 개념

두 패턴 모두 "원본 객체를 감싸는 래퍼"라는 점에서 구조가 비슷하다. 입문자가 헷갈리는 이유가 여기에 있다.

- **데코레이터** — 원본 객체의 기능에 **새 기능을 추가(장식)**하는 것이 목적이다. 원본과 같은 인터페이스를 구현하고, 내부에서 원본을 호출한 뒤 앞뒤에 로직을 얹는다.
- **프록시** — 원본 객체로의 **접근을 제어**하는 것이 목적이다. 캐싱, 지연 로딩, 권한 확인, 로깅처럼 "원본을 직접 쓰지 않고 걸러서 쓰고 싶은" 경우에 쓴다.

## 한눈에 보기

| 항목 | 데코레이터 | 프록시 |
|------|-----------|--------|
| 주 목적 | 기능 추가/확장 | 접근 제어 |
| 원본 교체 가능? | 쉽게 교체 가능 | 클라이언트는 원본인지 몰라도 됨 |
| 실무 예 | 로깅 래퍼, 압축 스트림, 필터 체인 | Spring AOP, lazy 로딩, 캐시 프록시 |
| 생성 시점 | 기능 조합이 필요한 시점 | 접근 제어가 필요한 시점 |

## 상세 분해

### 데코레이터 구조

원본과 같은 인터페이스를 구현하면서 원본을 내부에 감싼다. 기능을 여러 겹으로 쌓을 수 있다.

```java
public class LoggingOrderService implements OrderService {
    private final OrderService delegate;
    public LoggingOrderService(OrderService delegate) {
        this.delegate = delegate;
    }
    public void complete(Order order) {
        log("before complete");
        delegate.complete(order);
        log("after complete");
    }
}
```

### 프록시 구조

접근 제어 로직이 들어간다. 예를 들어 권한 확인, 캐시 반환, 지연 초기화 같은 로직이다.

```java
public class CachedProductRepository implements ProductRepository {
    private final ProductRepository real;
    private final Map<Long, Product> cache = new HashMap<>();
    public Product findById(Long id) {
        return cache.computeIfAbsent(id, real::findById);
    }
}
```

## 흔한 오해와 함정

- **"두 패턴은 그냥 같다"** — 구조는 비슷하지만 의도가 다르다. "기능을 추가하나 vs 접근을 제어하나"를 보면 구분된다.
- **"Spring AOP가 데코레이터다"** — Spring AOP는 접근 제어(트랜잭션, 보안)가 주 목적이므로 프록시 패턴에 더 가깝다.
- **"래퍼 클래스를 만들면 항상 데코레이터다"** — 인터페이스를 같이 구현하고 원본을 위임 호출하는지, 기능 추가인지 접근 제어인지가 핵심이다.

## 실무에서 쓰는 모습

**데코레이터 실무**: Java `InputStream` 계열이 대표 예시다. `BufferedInputStream(new FileInputStream(...))` 처럼 여러 기능을 겹쳐 쌓는다. 또는 서비스 앞에 로깅·메트릭·재시도 래퍼를 붙일 때 쓴다.

**프록시 실무**: Spring `@Transactional`이 붙은 메서드는 Spring이 프록시 객체를 만들어 트랜잭션 경계를 제어한다. 캐시 라이브러리도 원본 메서드 앞에 캐시 확인 프록시를 끼운다.

## 더 깊이 가려면

- [데코레이터 vs 프록시 — 심화](./decorator-vs-proxy.md) — 동적 프록시, 투명성 원칙, 언제 어느 패턴이 맞는지 세부 기준
- [Retry Policy vs Decorator Chain](./retry-policy-vs-decorator-chain.md) — 재시도 정책을 데코레이터 체인으로 구성하는 패턴

## 면접/시니어 질문 미리보기

> Q: 데코레이터와 프록시의 의도 차이를 한 문장으로 설명할 수 있는가?
> 의도: 패턴의 의도를 구조와 분리해 이해하는지 확인한다.
> 핵심: 데코레이터는 기능 추가, 프록시는 접근 제어다.

> Q: Spring AOP는 두 패턴 중 어느 쪽에 가까운가?
> 의도: Spring 동작 원리를 패턴 관점에서 보는지 확인한다.
> 핵심: 트랜잭션·보안 같은 접근 제어가 목적이므로 프록시에 가깝다.

> Q: 같은 인터페이스를 여러 겹으로 쌓아야 할 때 데코레이터 체인의 단점은 무엇인가?
> 의도: 패턴의 한계를 아는지 확인한다.
> 핵심: 호출 체인이 깊어지면 디버깅이 어렵고, 상태 공유가 필요하면 구조가 복잡해진다.

## 한 줄 정리

데코레이터는 원본에 기능을 쌓는 래퍼이고 프록시는 접근을 제어하는 대리자인데, 둘 다 원본과 같은 인터페이스를 구현한다는 점에서 구조는 닮았다.
