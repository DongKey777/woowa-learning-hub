# 데코레이터 vs 프록시

> 한 줄 요약: 둘 다 객체를 감싸지만, 데코레이터는 기능을 "쌓는" 구조이고 프록시는 호출을 "가로채는" 구조다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [전략 (Strategy)](./strategy-pattern.md)
> - [팩토리 (Factory)](./factory.md)
> - [템플릿 메소드 (Template Method)](./template-method.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

데코레이터와 프록시는 둘 다 "같은 인터페이스를 유지한 채 객체를 감싸는 패턴"처럼 보인다. 하지만 목적이 다르다.

- 데코레이터는 기능을 동적으로 조합한다.
- 프록시는 접근 제어, 지연 로딩, 로깅, 트랜잭션처럼 "호출 전후에 끼어드는 역할"을 한다.

둘을 헷갈리면 Spring AOP를 데코레이터라고 오해하거나, 단순 기능 확장에 프록시를 과하게 얹는 실수를 한다.

### 한 줄 구분

- 데코레이터: "이 객체에 기능을 하나 더 얹자"
- 프록시: "이 객체 호출을 대신 받자"

---

## 깊이 들어가기

### 1. 구조는 비슷하지만 책임은 다르다

두 패턴 모두 보통 같은 인터페이스를 구현한다.

```text
Client -> Wrapper -> Real Object
```

하지만 의미가 다르다.

| 구분 | 데코레이터 | 프록시 |
|------|------------|--------|
| 중심 질문 | 기능을 추가할 것인가 | 호출을 제어할 것인가 |
| 대표 용도 | 압축, 암호화, 재시도, 캐싱 조합 | 접근 제어, 트랜잭션, 지연 로딩, 로깅 |
| 조합 방식 | 여러 개를 연속으로 붙임 | 보통 한 단계에서 가로챔 |
| 팀이 기대하는 것 | 기능 확장 | 투명한 대리 수행 |

### 2. Spring에서의 프록시

Spring AOP, `@Transactional`, `@Cacheable`은 대부분 프록시 기반이다.  
즉 기능 자체보다 "호출 경계"를 잡는 것이 중요하다.

이런 경우 프록시는 데코레이터와 비슷해 보이지만, 목적은 기능 조합이 아니라 **호출 제어**다.

### 3. JDK와 코드 관점

Java의 `java.io` 계열에는 데코레이터 스타일 API가 많다.

- `InputStream`
- `BufferedInputStream`
- `DataInputStream`
- `GZIPInputStream`

반면 Spring은 프록시를 통해 메서드 호출 전후를 제어한다.

### 4. 언제 헷갈리면 안 되는가

- 기능이 누적되는가: 데코레이터
- 호출 권한을 판단하는가: 프록시
- 같은 인터페이스로 여러 기능을 조합하는가: 데코레이터
- 내부 호출, self-invocation, 트랜잭션 경계 같은 문제가 중요한가: 프록시

---

## 실전 시나리오

### 시나리오 1: 로그 + 압축 + 암호화

파일 전송이나 응답 가공처럼 기능을 단계적으로 더하고 싶다면 데코레이터가 자연스럽다.

### 시나리오 2: `@Transactional`이 동작하는 이유

Spring은 메서드 호출을 프록시가 대신 받는다.  
이건 데코레이터처럼 보일 수 있지만 핵심은 기능 추가가 아니라 호출 통제다.

### 시나리오 3: 잘못된 적용

아주 단순한 객체에 데코레이터를 여러 겹 쌓으면, 기능은 좋아 보여도 디버깅 난이도만 올라간다.  
프록시도 마찬가지로, 호출 흐름이 숨겨지면 읽기 비용이 커진다.

---

## 코드로 보기

### 데코레이터 예시

```java
interface MessageSender {
    void send(String message);
}

class PlainSender implements MessageSender {
    @Override
    public void send(String message) {
        System.out.println(message);
    }
}

class LoggingSender implements MessageSender {
    private final MessageSender delegate;

    LoggingSender(MessageSender delegate) {
        this.delegate = delegate;
    }

    @Override
    public void send(String message) {
        System.out.println("[log] sending message");
        delegate.send(message);
    }
}

class CompressingSender implements MessageSender {
    private final MessageSender delegate;

    CompressingSender(MessageSender delegate) {
        this.delegate = delegate;
    }

    @Override
    public void send(String message) {
        delegate.send("compressed:" + message);
    }
}

MessageSender sender = new CompressingSender(new LoggingSender(new PlainSender()));
sender.send("hello");
```

### 프록시 예시

```java
interface OrderService {
    void placeOrder();
}

class RealOrderService implements OrderService {
    @Override
    public void placeOrder() {
        System.out.println("place order");
    }
}

class SecurityProxy implements OrderService {
    private final OrderService target;

    SecurityProxy(OrderService target) {
        this.target = target;
    }

    @Override
    public void placeOrder() {
        if (!hasPermission()) {
            throw new IllegalStateException("forbidden");
        }
        target.placeOrder();
    }

    private boolean hasPermission() {
        return true;
    }
}
```

### Spring AOP와 연결

```java
@Transactional
public void pay() {
    repository.save(order);
}
```

이 코드는 "데코레이터를 쓴 것"이라기보다, 프록시가 트랜잭션 경계를 잡는 예시로 보는 편이 정확하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| 데코레이터 | 기능 조합이 유연하다 | 객체 수가 늘어난다 | 기능을 쌓아가며 확장할 때 |
| 프록시 | 호출 제어를 일관되게 처리한다 | 흐름이 숨겨진다 | 인증, 권한, 트랜잭션, 캐시 |
| 직접 호출 | 단순하다 | 중복 코드가 늘어난다 | 변경이 거의 없을 때 |

데코레이터는 "기능의 조합"을, 프록시는 "경계의 제어"를 해결한다.  
이 차이를 보면 어떤 상황에서 Spring AOP가 적합한지도 같이 보인다.

---

## 꼬리질문

> Q: 데코레이터와 프록시의 가장 큰 차이는 무엇인가?
> 의도: 같은 wrapper 구조를 목적까지 구분해서 아는지 확인
> 핵심: 기능 확장인지, 호출 제어인지

> Q: Spring AOP는 데코레이터에 더 가까운가, 프록시에 더 가까운가?
> 의도: 프록시 기반 AOP 이해 여부 확인
> 핵심: 프록시가 더 정확하다

> Q: 객체를 여러 겹 감싸면 왜 디버깅이 어려워지는가?
> 의도: wrapper 패턴의 장단점을 실제로 이해하는지 확인
> 핵심: 호출 경로와 책임이 분산된다

---

## 한 줄 정리

데코레이터는 기능을 누적하는 구조, 프록시는 호출을 통제하는 구조다. Spring AOP와 `@Transactional`은 후자에 가깝다.
