# 템플릿 메소드 패턴

> 한 줄 요약: 공통 알고리즘의 순서는 상위 클래스가 고정하고, 바뀌는 단계만 하위 클래스가 구현하는 패턴이다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)
> - [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
> - [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](./template-method-vs-filter-interceptor-chain.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [전략 패턴](./strategy-pattern.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

retrieval-anchor-keywords: template method pattern, template method beginner, algorithm skeleton, fixed workflow inheritance, hook method, hook method vs abstract method, final template method, template method vs strategy, framework callback skeleton, framework native template method, servlet doGet doPost, OncePerRequestFilter doFilterInternal, onceperrequestfilter template method, filter chain vs template method, handlerinterceptor not template method, junit setUp tearDown, xUnit fixture template method, when not to use template method, inheritance explosion, composition over inheritance

---

## 핵심 개념

템플릿 메소드 패턴은 **공통 흐름을 한곳에 고정**하려고 쓴다.  
초보자가 이 패턴을 처음 볼 때 놓치기 쉬운 핵심은 "상속으로 재사용"보다 **순서를 통제**하는 데 있다.

- 상위 클래스: 알고리즘의 전체 순서를 가진다
- 하위 클래스: 바뀌는 단계만 구현한다
- hook method: 꼭 바꾸지 않아도 되는 선택적 확장 지점이다

즉 이 패턴은 "공통 로직 묶기"가 아니라  
**"순서를 실수로 바꾸지 못하게 하면서, 단계별 차이만 열어두기"**에 가깝다.

### 템플릿 메소드가 잘 맞는 경우

- 검증 -> 변환 -> 저장처럼 순서가 중요한 흐름이 있을 때
- 구현체가 여러 개지만 단계 이름과 책임은 안정적일 때
- 공통 예외 처리, 로깅, 리소스 정리 같은 뼈대를 한곳에 두고 싶을 때

### 템플릿 메소드가 덜 맞는 경우

- 구현을 런타임에 교체해야 할 때
- 단계 조합이 너무 많아서 하위 클래스가 폭증할 때
- 상위 클래스가 모든 하위 클래스의 세부 요구를 계속 끌어안게 될 때

한 문장 규칙:  
**"흐름은 고정, 단계만 다름"이면 템플릿 메소드를 먼저 본다.**

---

## 깊이 들어가기

### 1. 템플릿은 뼈대이고, 하위 클래스는 빈칸을 채운다

예를 들어 파일 내보내기 기능이 있다고 하자.

1. 데이터 읽기
2. 형식 변환
3. 파일 쓰기
4. 후처리

이 순서가 모든 구현에서 같다면 상위 클래스가 이 순서를 잡아야 한다.  
하위 클래스가 제멋대로 `write -> load -> transform`처럼 바꾸면 안 되기 때문이다.

그래서 보통 템플릿 메소드는 `final`로 두는 편이 많다.  
흐름 자체는 상속받는 쪽에서 바꾸지 못하게 막고, 단계 메서드만 재정의하게 만드는 것이다.

### 2. 추상 단계와 hook method는 다르다

이 문서에서 가장 중요한 구분이다.

| 구분 | 의미 | 하위 클래스 구현 여부 | 언제 쓰는가 |
|---|---|---|---|
| 추상 메서드 | 없으면 알고리즘이 완성되지 않는 필수 단계 | 반드시 구현 | 구현체마다 핵심 동작이 달라질 때 |
| hook method | 기본값이 있는 선택적 확장 지점 | 필요하면 구현 | 특정 구현에서만 추가 동작이 필요할 때 |

예를 들어:

- `convert()`는 보고서를 어떤 형식으로 바꿀지 결정하므로 필수 단계일 수 있다
- `afterExport()`는 알림 전송이나 메트릭 기록처럼 선택적일 수 있다

이 차이를 흐리면 모든 단계를 hook으로 열어버리게 된다.  
그러면 상위 클래스가 흐름을 통제한다는 템플릿 메소드의 장점이 약해진다.

### 3. hook method는 "선택적 확장"만 허용해야 한다

좋은 hook은 기본 구현이 안전하다.

```java
protected void afterExport(Path path) {
    // 기본은 아무 일도 하지 않는다.
}
```

또는:

```java
protected boolean shouldCompress() {
    return false;
}
```

반대로 아래 같은 hook은 위험하다.

- `protected int stepOrder()`처럼 전체 순서를 바꾸게 하는 hook
- `protected void onEverything(...)`처럼 너무 많은 책임을 몰아주는 hook
- hook 안에서 상위 클래스의 내부 상태를 광범위하게 바꿔야 하는 구조

hook은 "여기서 조금 덧붙일 수 있다" 수준이어야 한다.  
**알고리즘의 불변식을 깨뜨릴 수 있는 hook은 거의 항상 과하다.**

### 4. 프레임워크에서도 비슷한 느낌을 자주 본다

템플릿 메소드는 오래된 패턴이지만 지금도 프레임워크 안에서 자주 보인다.

- 서블릿에서 `service()` 흐름 안에 `doGet()`, `doPost()`를 재정의하는 방식
- Spring `OncePerRequestFilter`가 `doFilter()` 골격을 잡고 `doFilterInternal()`만 열어두는 방식
- 테스트 프레임워크에서 공통 실행 흐름 안에 setup/teardown 포인트를 두는 방식
- 배치/파이프라인 코드에서 공통 실행 골격을 상위 클래스가 잡는 방식

이때 핵심은 같다.  
프레임워크가 먼저 흐름을 결정하고, 애플리케이션은 정해진 지점만 구현한다.  
이 점이 흔히 말하는 Hollywood Principle과도 이어진다.

실제 API 이름 기준 예시는 [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)에 따로 묶어 두었다.
Spring `Filter` / `HandlerInterceptor` / `OncePerRequestFilter`를 한 요청 경로에서 어떻게 갈라 읽는지 빠르게 확인하려면 [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](./template-method-vs-filter-interceptor-chain.md)를 같이 보면 된다.

---

## 실전 시나리오

### 시나리오 1: 보고서 내보내기

CSV와 JSON 보고서를 둘 다 내보내야 한다고 하자.

- 공통: 데이터 조회, 파일 생성, 예외 처리, 임시 파일 정리
- 차이: 포맷 변환 방식

이 경우 상위 클래스가 `load -> convert -> write -> cleanup` 순서를 고정하고,  
하위 클래스는 `convert()`만 다르게 구현하면 된다.

### 시나리오 2: 인증 이후 채널별 후처리

로그인 후 공통적으로 토큰 검증과 사용자 조회는 항상 필요하지만,

- 웹은 쿠키를 설정하고
- 앱은 디바이스 메타데이터를 기록하고
- 관리자 콘솔은 감사 로그를 남긴다

이처럼 순서는 같고 마지막 처리만 달라지면 템플릿 메소드가 잘 맞는다.

### 시나리오 3: "안 맞는" 예시도 같이 보기

배송비 계산 정책이 `일반`, `퀵`, `새벽`, `프로모션`처럼 계속 늘어난다고 해보자.  
이 문제는 "공통 순서"보다 **계산 규칙을 바꿔 끼우는 일**이 핵심이다.

이때 템플릿 메소드를 쓰면 `StandardShippingCalculator`, `QuickShippingCalculator` 같은 하위 클래스만 늘어난다.  
게다가 런타임에 정책 교체가 필요하면 결국 템플릿보다 [전략 패턴](./strategy-pattern.md)이 더 자연스럽다.

즉 "단계 일부가 다른 파이프라인"이 아니라 "정책 자체를 교체하는 문제"라면 템플릿 메소드는 좋은 선택이 아니다.

---

## 코드로 보기

### 1. 템플릿 메소드 없이 중복이 생기는 코드

```java
public class CsvReportExporter {
    public void export(List<Order> orders, Path path) {
        validate(orders);
        String body = convertToCsv(orders);
        writeFile(path, body);
        recordMetric(path);
    }

    private void validate(List<Order> orders) {
        if (orders.isEmpty()) {
            throw new IllegalArgumentException("orders must not be empty");
        }
    }

    private void writeFile(Path path, String body) {
        // 파일 저장
    }

    private void recordMetric(Path path) {
        // 내보내기 메트릭 기록
    }
}

public class JsonReportExporter {
    public void export(List<Order> orders, Path path) {
        validate(orders);
        String body = convertToJson(orders);
        writeFile(path, body);
        recordMetric(path);
    }

    private void validate(List<Order> orders) {
        if (orders.isEmpty()) {
            throw new IllegalArgumentException("orders must not be empty");
        }
    }

    private void writeFile(Path path, String body) {
        // 파일 저장
    }

    private void recordMetric(Path path) {
        // 내보내기 메트릭 기록
    }
}
```

검증, 파일 쓰기, 알림 흐름은 같은데 형식 변환만 다르다.  
이럴 때 상위 클래스가 뼈대를 들고 있는 편이 낫다.

### 2. 템플릿 메소드 적용

```java
public abstract class ReportExporter {
    public final void export(List<Order> orders, Path path) {
        validate(orders);
        String body = convert(orders);
        writeFile(path, body);
        afterExport(path);
    }

    private void validate(List<Order> orders) {
        if (orders.isEmpty()) {
            throw new IllegalArgumentException("orders must not be empty");
        }
    }

    protected abstract String convert(List<Order> orders);

    protected void afterExport(Path path) {
        // optional hook
    }

    private void writeFile(Path path, String body) {
        // 공통 파일 쓰기 로직
    }
}
```

### 3. 하위 클래스는 필수 단계만 구현하고, hook은 필요할 때만 건드린다

```java
public class CsvReportExporter extends ReportExporter {
    @Override
    protected String convert(List<Order> orders) {
        return "csv-body";
    }
}

public class JsonReportExporter extends ReportExporter {
    @Override
    protected String convert(List<Order> orders) {
        return "json-body";
    }

    @Override
    protected void afterExport(Path path) {
        System.out.println("json export metric recorded");
    }
}
```

여기서 `convert()`는 필수 단계다.  
반면 `afterExport()`는 선택적 확장 지점이다.  
이 차이를 명확히 두면 하위 클래스 책임이 훨씬 읽기 쉬워진다.

---

## hook method 설계 가이드

### 1. hook은 적게 두는 편이 좋다

hook이 많아질수록 상위 클래스가 사실상 "거대한 설정 파일"처럼 변한다.  
hook 1~2개는 유용하지만, 거의 모든 단계에 hook이 달리기 시작하면 설계가 흔들리는 신호다.

### 2. hook 이름은 의도를 드러내야 한다

- 좋은 예: `afterExport()`, `shouldCompress()`
- 나쁜 예: `customize()`, `handleExtra()`

이름만 보고도 "언제, 무엇을 바꿀 수 있는지" 드러나야 한다.

### 3. hook으로 핵심 순서를 바꾸게 하지 말라

예를 들어 `beforeValidate()`, `skipWrite()`, `replaceAllSteps()` 같은 확장은  
처음에는 유연해 보여도 결국 상위 클래스 계약을 무너뜨린다.

이런 요구가 많아지면 두 가지를 의심해야 한다.

- 템플릿 메소드보다 [전략 패턴](./strategy-pattern.md)이 더 맞는지
- 상속보다 [Composition over Inheritance](./composition-over-inheritance-practical.md)가 더 안전한지

### 4. hook이 외부 협력 객체를 너무 많이 요구하면 재검토하라

hook 하나 때문에 캐시, 메시지 발행기, 감사 로거, 알림 서비스까지 전부 하위 클래스가 알아야 한다면  
그 시점부터는 "선택적 한 단계"가 아니라 별도 역할 객체가 필요하다는 뜻일 수 있다.

그런 경우에는 hook 대신 전략 객체, 리스너, 후처리 컴포넌트로 분리하는 편이 낫다.

---

## 언제 쓰지 말아야 하나

### 1. 런타임 교체가 중요한 정책 문제

할인 정책, 배송 정책, 정렬 기준처럼 실행 중에 구현을 바꿔야 한다면  
템플릿 메소드보다 [전략 패턴](./strategy-pattern.md)이 더 자연스럽다.

템플릿 메소드는 상속 구조가 먼저 고정되기 때문에  
"지금은 A, 다음 요청은 B"처럼 유연하게 바꾸는 문제에 약하다.

### 2. 조합 축이 두세 개 이상 겹치는 문제

예를 들어 보고서 형식은 `CSV/JSON`, 저장 위치는 `로컬/S3`, 후처리는 `없음/압축/알림`이라고 해보자.  
이걸 템플릿 메소드 하위 클래스만으로 풀면 이런 식으로 번지기 쉽다.

- `CsvToLocalExporter`
- `CsvToS3Exporter`
- `JsonToLocalCompressedExporter`
- `JsonToS3WithNotificationExporter`

이건 템플릿 메소드가 아니라 **상속 조합 폭발**에 가깝다.  
이 경우에는 상속 하나로 다 풀려 하지 말고 형식 변환, 저장 전략, 후처리 정책을 분리해야 한다.

### 3. 하위 클래스가 거의 모든 단계를 덮어쓰는 경우

상위 클래스는 뼈대만 남고, 하위 클래스마다 `validate`, `convert`, `write`, `afterExport`를 전부 갈아엎는다면  
사실 공통 골격이 안정적이지 않다는 뜻이다.

그런 구조에서는 상위 클래스가 재사용 기반이 아니라 **억지 공통 부모**가 된다.  
이때는 공통 함수로만 묶거나, 아예 별도 협력 객체 조합으로 다시 나누는 편이 낫다.

### 4. 공통 로직이 너무 작을 때

공통인 부분이 "로그 한 줄" 정도뿐이라면 템플릿 메소드까지 갈 필요가 없다.  
작은 헬퍼 함수, 데코레이터, 인터셉터가 더 단순하고 읽기 쉽다.

패턴은 중복을 없애기 위해 쓰지만,  
**사소한 중복 하나 없애려다가 상속 계층 전체를 만드는 것은 더 큰 비용**일 수 있다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 템플릿 메소드 | 순서를 강하게 보장한다 | 상속 계층이 굳기 쉽다 | 공통 파이프라인이 안정적일 때 |
| 전략 | 구현 교체가 쉽다 | 흐름 보장은 약하다 | 정책을 런타임에 바꿔야 할 때 |
| 조합 + 작은 헬퍼 | 구조가 가볍다 | 공통 흐름이 퍼질 수 있다 | 공통 로직이 작고 단순할 때 |

판단 기준은 단순하다.

- **흐름이 더 중요하면** 템플릿 메소드
- **교체 가능성이 더 중요하면** 전략
- **공통점이 작고 얕으면** 그냥 작은 함수나 조합

---

## 꼬리질문

> Q: 추상 메서드와 hook method의 차이는 무엇인가요?
> 의도: 템플릿 메소드의 필수 단계와 선택 단계의 경계를 아는지 확인한다.
> 핵심: 추상 메서드는 반드시 구현해야 하고, hook은 기본 구현이 있는 선택적 확장 지점이다.

> Q: 템플릿 메소드의 템플릿 메서드 자체를 왜 `final`로 두기도 하나요?
> 의도: 패턴의 목적이 재사용이 아니라 흐름 통제라는 점을 이해하는지 본다.
> 핵심: 하위 클래스가 알고리즘 순서를 깨지 못하게 하기 위해서다.

> Q: 보고서 형식, 저장 위치, 후처리 조합이 계속 늘어나면 왜 템플릿 메소드가 불편해지나요?
> 의도: 상속 기반 설계의 조합 폭발 위험을 이해하는지 확인한다.
> 핵심: 하위 클래스 수가 곱셈처럼 늘어나서 조합 분리가 더 자연스러워진다.

> Q: 배송비 정책은 왜 템플릿 메소드보다 전략 패턴이 더 맞나요?
> 의도: "흐름 고정"과 "정책 교체"를 구분하는지 확인한다.
> 핵심: 문제의 본질이 단계 일부 변경이 아니라 규칙 교체이기 때문이다.

---

## 한 줄 정리

템플릿 메소드는 공통 순서를 상위 클래스가 고정하고 일부 단계만 하위 클래스에 맡기는 패턴이며, hook method는 그 뼈대를 깨지 않는 범위에서만 선택적으로 열어둬야 한다.
