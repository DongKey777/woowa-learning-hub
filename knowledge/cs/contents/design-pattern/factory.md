# 팩토리 (Factory) 디자인 패턴

> 작성자 : [서그림](https://github.com/Seogeurim)

> 한 줄 요약: Factory는 객체 생성 책임을 호출부에서 분리해 생성 규칙, 선택 규칙, 외부 연동을 한 곳에 모으는 패턴이다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [싱글톤 (Singleton) Java 구현 방법](./singleton-java.md)
> - [Registry Pattern](./registry-pattern.md)
> - [Builder vs Fluent Mutation Smell](./builder-vs-fluent-mutation-smell.md)
> - [Service Locator Antipattern](./service-locator-antipattern.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

---

## 핵심 개념

팩토리는 객체를 `new`로 직접 만들지 않고, **생성 책임을 별도 객체나 메서드로 숨기는 구조**다.  
핵심은 "객체를 만드는 방법"이 바뀌어도 호출부가 흔들리지 않게 하는 것이다.

Factory가 해결하는 문제는 세 가지다.

- 생성 규칙이 복잡하다
- 어떤 구현을 쓸지 런타임에 결정해야 한다
- 생성 코드가 여기저기 흩어지면 유지보수가 어렵다

### Retrieval Anchors

- `factory pattern`
- `object creation boundary`
- `runtime implementation selection`
- `switch factory smell`
- `factory vs registry`

---

## 깊이 들어가기

### 1. Factory는 생성과 사용을 분리한다

호출부가 `new Pencil()`를 직접 하게 두면, 생성 방식 변경이 곧 호출부 변경이 된다.  
팩토리를 두면 생성과 사용 사이에 경계가 생긴다.

### 2. 팩토리의 종류를 구분해야 한다

| 종류 | 핵심 | 예시 |
|---|---|---|
| Simple Factory | 입력에 따라 적절한 객체를 돌려준다 | `create("Pencil")` |
| Factory Method | 서브클래스가 생성 대상을 결정한다 | 템플릿/상속 기반 생성 |
| Abstract Factory | 관련된 객체군을 함께 만든다 | UI theme, DB family |
| Static Factory | 생성 메서드 이름을 가진 정적 진입점 | `of()`, `from()`, `valueOf()` |

실무에서 "팩토리"라고 부르는 것의 절반은 사실 단순 생성 헬퍼다.  
반드시 어떤 패턴인지부터 확인해야 한다.

### 3. Factory는 Registry와 닮지만 다르다

Factory는 "만든다"가 핵심이고, Registry는 "찾는다"가 핵심이다.  
팩토리가 계속 커지면 사실상 Registry나 Strategy 선택기가 되는 경우가 많다.

### 4. 팩토리는 anti-pattern이 되기도 한다

다음 신호를 주의해야 한다.

- `switch`가 길어진다
- 문자열 키가 하드코딩된다
- `null`을 반환한다
- 생성 규칙 안에 비즈니스 로직이 들어간다
- 사실상 Service Locator처럼 사용된다

---

## 실전 시나리오

### 시나리오 1: 외부 provider 생성

결제 SDK, 저장소 클라이언트, 메시지 발행자를 만들 때 적합하다.

### 시나리오 2: 테스트 픽스처 생성

테스트에서 다양한 객체 조합을 간단히 만들 수 있다.

### 시나리오 3: 구현 선택

환경에 따라 S3, GCS, local storage 중 하나를 고르는 경우에 유용하다.

---

## 코드로 보기

### Before: 직접 생성

```java
Product pencil = new Pencil();
```

직접 생성은 단순하지만, 구현이 바뀌면 호출부 전체를 손봐야 한다.

### Simple Factory

```java
public class ProductFactory {
    public static Product create(String type) {
        return switch (type) {
            case "PENCIL" -> new Pencil();
            case "NOTE" -> new Note();
            default -> throw new IllegalArgumentException("unknown product: " + type);
        };
    }
}
```

### Factory with Map

```java
public class ProductFactory {
    private final Map<String, Supplier<Product>> suppliers;

    public ProductFactory(Map<String, Supplier<Product>> suppliers) {
        this.suppliers = suppliers;
    }

    public Product create(String type) {
        Supplier<Product> supplier = suppliers.get(type);
        if (supplier == null) {
            throw new IllegalArgumentException("unknown product: " + type);
        }
        return supplier.get();
    }
}
```

### Abstract Factory 감각

```java
public interface StorageClientFactory {
    UploadClient uploadClient();
    DownloadClient downloadClient();
}
```

Factory는 생성 책임을 한 곳에 모으고, 변경의 충격을 줄여준다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 `new` | 가장 단순하다 | 변경이 퍼진다 | 아주 작은 코드 |
| Factory | 생성 규칙이 집중된다 | 클래스가 하나 더 생긴다 | 생성 규칙이 변할 때 |
| Registry + Factory | 선택과 생성이 분리된다 | 구조가 복잡해질 수 있다 | 구현이 많을 때 |
| DI 컨테이너 | 생성/조립이 자동화된다 | 학습 비용이 있다 | backend 애플리케이션 |

판단 기준은 다음과 같다.

- 생성 규칙이 자주 바뀌면 Factory
- 객체 종류가 많으면 Registry와 같이 본다
- 단순한 생성이면 굳이 Factory를 만들지 않는다

---

## 꼬리질문

> Q: Factory와 Registry는 어떻게 다르나요?
> 의도: 생성과 조회를 구분하는지 확인한다.
> 핵심: Factory는 만들고 Registry는 찾는다.

> Q: factory가 너무 커지면 어떤가요?
> 의도: switch explosion을 아는지 확인한다.
> 핵심: 선택 로직을 registry나 strategy로 분리한다.

> Q: factory가 service locator처럼 변하는 이유는 무엇인가요?
> 의도: 숨은 의존성과 생성 책임 혼선을 아는지 확인한다.
> 핵심: 객체 생성과 조회가 뒤섞이기 때문이다.

> Q: static factory는 언제 좋나요?
> 의도: 정적 진입점의 장단점을 아는지 확인한다.
> 핵심: 단순 생성, 이름 있는 생성, 불변 객체에 좋다.

## 한 줄 정리

Factory는 객체 생성 책임을 분리해 변경을 한곳에 모으는 패턴이지만, switch가 커지면 Registry나 DI 쪽으로 다시 설계를 봐야 한다.
