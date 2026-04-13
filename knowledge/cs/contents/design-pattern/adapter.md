# Adapter (어댑터) 패턴 🟢 Basic

> 호환되지 않는 인터페이스를 가진 객체들이 함께 동작할 수 있게 중간 번역기를 끼워 넣는 패턴

## 핵심 개념

어댑터 패턴은 **기존 코드를 수정하지 않고**, 서로 다른 인터페이스를 가진 클래스를 연결하는 구조 패턴이다. 해외여행에서 돼지코(전원 어댑터)를 꽂듯이, 이미 존재하는 코드의 인터페이스를 클라이언트가 기대하는 형태로 변환한다.

**문제를 먼저 보자**: 외부 라이브러리를 도입했는데 우리 시스템의 인터페이스와 메서드 시그니처가 다르다. 외부 코드를 수정할 수 없고, 우리 코드도 수십 곳에서 기존 인터페이스를 쓰고 있다. 이때 자연스럽게 나오는 구조가 어댑터다.

## 깊이 들어가기

### 두 가지 구현 방식

| 구분 | 객체 어댑터 (Composition) | 클래스 어댑터 (Inheritance) |
|---|---|---|
| 관계 | Adaptee를 멤버 변수로 보유 | Adaptee를 상속 |
| 유연성 | Adaptee의 하위 클래스도 적응 가능 | 특정 Adaptee에 고정 |
| 언어 제약 | 모든 언어에서 가능 | 다중 상속이 필요 (Java에서는 제한적) |
| GoF 권장 | **권장** | 제한적 사용 |

Java는 다중 상속을 지원하지 않으므로 **객체 어댑터(위임)**가 사실상 표준이다.

### 구조

```
[Client] → [Target Interface] ← [Adapter] → [Adaptee]
                                    │
                           target 메서드 호출을
                           adaptee 메서드로 위임
```

## 실전 시나리오

레거시 결제 시스템(XML 기반)을 새로운 결제 게이트웨이(JSON 기반)로 교체해야 하는 상황. 기존 코드 수십 곳에서 `LegacyPayment.processXml()`을 호출하고 있다.

## 코드로 보기

### Before: 어댑터 없이 직접 수정

```java
// 기존 인터페이스
public interface PaymentProcessor {
    void pay(String xmlData);
}

// 새로운 외부 라이브러리 - 수정 불가
public class ModernPaymentGateway {
    public void submitPayment(String jsonData) {
        System.out.println("Processing JSON payment: " + jsonData);
    }
}

// 문제: 기존 코드를 전부 수정해야 한다
public class OrderService {
    public void checkout(String xmlData) {
        // 기존: paymentProcessor.pay(xmlData);
        // 변경: XML→JSON 변환 로직을 여기에? 모든 호출부에?
        String json = convertXmlToJson(xmlData); // 호출부마다 반복
        modernGateway.submitPayment(json);
    }
}
```

### After: 어댑터 적용

```java
// 어댑터: 기존 인터페이스를 구현하면서, 내부에서 새 라이브러리로 위임
public class PaymentGatewayAdapter implements PaymentProcessor {

    private final ModernPaymentGateway gateway; // 위임 (객체 어댑터)

    public PaymentGatewayAdapter(ModernPaymentGateway gateway) {
        this.gateway = gateway;
    }

    @Override
    public void pay(String xmlData) {
        String jsonData = convertXmlToJson(xmlData); // 변환은 어댑터 안에서 한 번만
        gateway.submitPayment(jsonData);
    }

    private String convertXmlToJson(String xml) {
        // 변환 로직
        return "{converted: true}";
    }
}

// 호출부는 그대로
public class OrderService {
    private final PaymentProcessor processor;

    public OrderService(PaymentProcessor processor) {
        this.processor = processor;
    }

    public void checkout(String xmlData) {
        processor.pay(xmlData); // 변경 없음
    }
}
```

## Spring/JDK에서 실제로 쓰이는 곳

| 위치 | 설명 |
|---|---|
| `java.util.Arrays#asList()` | 배열을 List 인터페이스에 적응 |
| `java.io.InputStreamReader` | InputStream(바이트)을 Reader(문자) 인터페이스에 적응 |
| `java.io.OutputStreamWriter` | OutputStream을 Writer 인터페이스에 적응 |
| Spring `HandlerAdapter` | 다양한 핸들러 타입(Controller, HttpRequestHandler 등)을 DispatcherServlet이 동일하게 처리할 수 있게 적응 |
| Spring `JpaVendorAdapter` | Hibernate, EclipseLink 등 다른 JPA 구현체를 Spring이 동일하게 다루도록 적응 |

## 트레이드오프

### 장점
- **OCP(개방-폐쇄 원칙) 준수**: 기존 코드 수정 없이 새 기능 통합
- **SRP(단일 책임 원칙)**: 변환 로직을 어댑터 한 곳에 격리
- **테스트 용이**: 어댑터를 mock으로 교체해 단위 테스트 가능

### 단점
- 어댑터 클래스가 늘어나면 코드 복잡도 증가
- 변환 과정에서 성능 오버헤드 발생 가능

### 이 패턴을 쓰면 안 되는 상황
- **인터페이스가 근본적으로 호환 불가능할 때**: 메서드 시그니처 변환이 아니라 비즈니스 로직 자체가 다르면 어댑터가 아니라 새로운 설계가 필요하다.
- **어댑터 안에 비즈니스 로직이 커질 때**: 어댑터는 "번역"만 해야 한다. 변환 로직이 복잡해지면 별도 서비스로 분리해야 한다.
- **처음부터 설계할 수 있는 상황**: 레거시 통합이 아니라면 처음부터 통일된 인터페이스를 설계하는 게 낫다.

## 꼬리질문

1. **어댑터와 퍼사드의 차이는?** 어댑터는 인터페이스를 "변환"하고, 퍼사드는 여러 인터페이스를 "단순화"한다. 어댑터는 1:1 변환, 퍼사드는 N:1 단순화.
2. **어댑터와 데코레이터의 차이는?** 어댑터는 인터페이스를 바꾸고, 데코레이터는 같은 인터페이스를 유지하면서 기능을 추가한다.
3. **Spring의 HandlerAdapter는 왜 필요한가?** DispatcherServlet이 `@Controller`, `HttpRequestHandler`, `Servlet` 등 서로 다른 타입의 핸들러를 동일한 방식으로 호출하기 위해 어댑터 패턴을 적용한 것이다.

## 한 줄 정리

**어댑터는 "이미 존재하는 것"을 "기대하는 형태"로 바꾸는 번역기다. 새로 만드는 코드에서는 필요 없고, 레거시 통합이나 외부 라이브러리 연동에서 빛난다.**
