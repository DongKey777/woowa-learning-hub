# 싱글톤 (Singleton) Java 구현 방법

> 작성자 : [서그림](https://github.com/Seogeurim)

> 한 줄 요약: Java에서 싱글톤은 private 생성자, static 인스턴스, public accessor로 구현하지만, 실제 backend에서는 classloader, serialization, 테스트, DI 컨테이너까지 함께 봐야 한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)


retrieval-anchor-keywords: singleton java basics, singleton java beginner, singleton java intro, design pattern basics, beginner design pattern, 처음 배우는데 singleton java, singleton java 입문, singleton java 기초, what is singleton java, how to singleton java
> 관련 문서:
> - [싱글톤 (Singleton)](./singleton.md)
> - [싱글톤 vs DI 컨테이너 스코프](./singleton-vs-di-container-scope.md)
> - [Registry Pattern](./registry-pattern.md)
> - [Service Locator Antipattern](./service-locator-antipattern.md)
> - [팩토리 (Factory)](./factory.md)

---

## 핵심 개념

싱글톤 구현의 핵심은 단순하다.

- 생성자는 감춘다
- 인스턴스는 하나만 둔다
- 접근은 static 메서드로 제공한다

하지만 Java에서는 "하나"라는 말이 생각보다 단순하지 않다.

- JVM 전체가 아니라 classloader마다 하나일 수 있다
- serialization이 복제본을 만들 수 있다
- reflection이 private 생성자를 뚫을 수 있다
- 테스트가 전역 상태에 오염될 수 있다

그래서 싱글톤은 "코드를 줄이는 패턴"이 아니라 **전역 상태를 통제하는 방식**으로 봐야 한다.

### Retrieval Anchors

- `singleton java implementation`
- `double checked locking`
- `holder idiom`
- `serialization reflection classloader`
- `spring singleton scope`

---

## 깊이 들어가기

### 1. Java 싱글톤의 기본 형태

싱글톤은 private 생성자와 static 인스턴스가 기본이다.

```java
public final class AppConfig {
    private static final AppConfig INSTANCE = new AppConfig();

    private AppConfig() {}

    public static AppConfig getInstance() {
        return INSTANCE;
    }
}
```

이 방식은 가장 단순하고 thread-safe하다. 대신 eager initialization이라 클래스 로딩 시점에 바로 생성된다.

### 2. lazy initialization은 조심해서 써야 한다

지연 생성은 비용을 늦출 수 있지만 thread safety가 중요하다.

```java
public final class LazyConfig {
    private static LazyConfig instance;

    private LazyConfig() {}

    public static synchronized LazyConfig getInstance() {
        if (instance == null) {
            instance = new LazyConfig();
        }
        return instance;
    }
}
```

`synchronized`는 안전하지만 호출 빈도가 높은 곳에서는 불필요한 비용이 될 수 있다.

### 3. Holder idiom이 실전에서 가장 많이 추천된다

```java
public final class HolderConfig {
    private HolderConfig() {}

    private static class Holder {
        private static final HolderConfig INSTANCE = new HolderConfig();
    }

    public static HolderConfig getInstance() {
        return Holder.INSTANCE;
    }
}
```

클래스 로딩은 JVM이 보장하므로, lazy하면서도 thread-safe하다.

### 4. double-checked locking은 volatile이 핵심이다

## 깊이 들어가기 (계속 2)

```java
public final class DclConfig {
    private static volatile DclConfig instance;

    private DclConfig() {}

    public static DclConfig getInstance() {
        if (instance == null) {
            synchronized (DclConfig.class) {
                if (instance == null) {
                    instance = new DclConfig();
                }
            }
        }
        return instance;
    }
}
```

`volatile`이 없으면 메모리 가시성 문제로 반쯤 만들어진 객체를 볼 수 있다.

### 5. enum singleton은 가장 안전한 편이다

```java
public enum EnumConfig {
    INSTANCE;

    public String value() {
        return "config";
    }
}
```

enum singleton은 serialization과 reflection에 상대적으로 안전하다.
다만 타입이 enum이어야 하므로 유연성은 떨어질 수 있다.

---

## 실전 시나리오

### 시나리오 1: 설정/레지스트리

환경 설정, feature flag, 정적 참조 데이터처럼 애플리케이션 전반에서 하나만 필요한 객체에 적합하다.

### 시나리오 2: 로깅/메트릭 클라이언트

공통 클라이언트를 하나 두고 재사용할 수 있다. 다만 실제 운영에서는 DI 컨테이너가 관리하는 빈이 더 자연스럽다.

### 시나리오 3: 잘못된 사용

도메인 서비스나 상태가 자주 바뀌는 객체를 싱글톤으로 두면 테스트와 유지보수가 악화된다.

---

## 코드로 보기

### private 생성자

```java
public final class ClassName {
    private ClassName() {}
}
```

### lazy getInstance

```java
public final class ClassName {
    private static ClassName instance;

    private ClassName() {}

    public static ClassName getInstance() {
        if (instance == null) {
            instance = new ClassName();
        }
        return instance;
    }
}
```

### serialization 방어

```java
private Object readResolve() {
    return getInstance();
}
```

### reflection 방어

```java
private ClassName() {
    if (instance != null) {
        throw new IllegalStateException("already initialized");
    }
}
```

이런 방어는 완벽한 보안책은 아니지만, 의도치 않은 복제를 줄여준다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| eager static final | 단순하고 thread-safe하다 | 시작 시 바로 생성된다 | 항상 필요한 객체 |
| synchronized lazy | 구현이 쉽다 | 호출 비용이 있다 | 빈도가 낮을 때 |
| holder idiom | lazy + thread-safe | 개념을 알아야 한다 | 실전 추천 |
| enum singleton | serialization/reflection에 강하다 | 유연성이 낮다 | 설정/상수성 객체 |

판단 기준은 다음과 같다.

- 상태가 없고 전역적으로 하나면 singleton 후보다
- 테스트가 어려워지면 DI 컨테이너로 넘기는 편이 낫다
- reflection, serialization, classloader를 반드시 염두에 둔다

---

## 꼬리질문

> Q: 싱글톤은 classloader마다 하나가 될 수 있나요?
> 의도: JVM 스코프를 정확히 이해하는지 확인한다.
> 핵심: 그렇다. classloader 경계가 다르면 인스턴스도 달라질 수 있다.

> Q: enum singleton이 왜 안전하다고 하나요?
> 의도: Java 언어 차원의 특성을 아는지 확인한다.
> 핵심: serialization과 reflection에 상대적으로 강하다.

> Q: 싱글톤을 왜 테스트하기 어렵다고 하나요?
> 의도: 전역 상태와 테스트 격리를 구분하는지 확인한다.
> 핵심: 상태가 공유되어 케이스 간 오염이 생길 수 있다.

> Q: Spring bean singleton과 디자인 패턴 singleton은 같은가요?
> 의도: 프레임워크 scope와 패턴을 분리하는지 확인한다.
> 핵심: 비슷해 보이지만 관리 주체와 의미가 다르다.

## 한 줄 정리

Java 싱글톤은 private 생성자와 static 접근자로 구현하지만, 실제로는 thread safety와 JVM 경계, serialization, 테스트까지 함께 고려해야 한다.
