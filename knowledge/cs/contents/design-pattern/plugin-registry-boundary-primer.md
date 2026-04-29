# Plugin Registry Boundary Primer: 좁은 injected registry와 application-wide locator drift 구분하기

> 한 줄 요약: plugin lookup은 host가 자기 extension point를 위해 주입받은 좁은 registry일 때는 괜찮지만, 앱 어디서나 아무 plugin이나 service를 꺼내는 통로가 되면 service locator 쪽으로 미끄러진다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)

> 관련 문서:
> - [Plugin Architecture: 기능을 꽂아 넣는 패턴 언어](./plugin-architecture-pattern-language.md)
> - [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
> - [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
> - [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
> - [Strategy Registry vs Service Locator Drift Note](./strategy-registry-vs-service-locator-drift.md)
> - [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)

retrieval-anchor-keywords: plugin registry boundary primer, plugin registry vs service locator, injected plugin registry, plugin registry beginner, plugin registry 큰 그림, plugin registry 언제 쓰는지, 처음 배우는데 plugin registry 뭐예요, service locator랑 뭐가 달라요, 처음 배우는데 service locator 차이, 왜 applicationcontext getbean이 문제예요, plugin manager가 왜 냄새예요, 플러그인 매니저가 왜 service locator 같아요, 플러그인 구조 큰 그림, dependency injection registry beginner, 주입받은 registry와 전역 locator 차이

---

## 먼저 머릿속 그림

이 문서는 `"plugin registry가 뭐예요?"`, `"처음 배우는데 service locator랑 뭐가 달라요?"`, `"왜 ApplicationContext getBean이 냄새라는 거예요?"` 같은 첫 질문이 들어왔을 때 먼저 착지해야 하는 primer다.

plugin registry를 처음 보면 "어차피 뭔가를 찾아오는 거니까 service locator 아닌가?"라는 질문이 자주 나온다.
초보자에게는 아래 그림으로 잡는 편이 가장 쉽다.

- **좁은 plugin registry**: host가 자기 plugin 선반 하나를 생성자로 받는다.
- **application-wide locator**: 건물 안내데스크처럼 앱 어디서나 필요한 것을 이것저것 꺼내 간다.

예를 들어 `ReportEngine`이 `ReportPluginRegistry`를 받아서 `PluginId.PDF`에 맞는 plugin을 찾는 것은 자연스럽다.
하지만 `BillingService`, `NotificationService`, `AdminJob`가 모두 같은 `PluginManager`에서 plugin, repository, client를 이름으로 꺼내기 시작하면 경계가 달라진다.

짧게 외우면 된다.

**"host가 자기 extension point용 plugin 선반을 주입받아 쓰면 registry, 앱 전체가 공용 조회소처럼 쓰면 locator."**

---

## 30초 비교표

| 질문 | 좁은 injected plugin registry | application-wide locator drift |
|---|---|---|
| 의존성이 어디에 보이나 | `ReportEngine(ReportPluginRegistry plugins)`처럼 생성자에 보인다 | `ApplicationContext`, `PluginManager`, `Locator`만 보이거나 본문에서 lookup한다 |
| 무엇을 돌려주나 | `ReportPlugin` 한 종류나 그 descriptor만 돌려준다 | plugin, repository, client, service 등 여러 타입을 돌려준다 |
| 누가 주로 쓰나 | extension point를 가진 host나 coordinator가 쓴다 | 앱 여기저기 서비스가 공용으로 쓴다 |
| key가 무엇인가 | `PluginId`, `Capability` 같은 plugin 계약 key | bean name, class name, 임의 문자열 |
| 테스트는 어떤가 | fake registry나 fake plugin으로 바로 테스트한다 | 전역 locator나 container 설정이 필요하다 |
| 경계가 어디서 무너지나 | plugin 후보 집합이 한 extension point에 머문다 | `get(Class<T>)`, `get(String)`처럼 아무거나 찾는 통로가 된다 |

핵심은 plugin이라는 단어가 아니다.
**반환 타입과 사용 범위가 좁은가**가 경계의 핵심이다.

---

## 좋은 예: host가 자기 plugin registry를 주입받는다

```java
public enum PluginId {
    PDF,
    CSV
}

public interface ReportPlugin {
    PluginId id();
    ReportResult generate(ReportRequest request);
}

public final class ReportEngine {
    private final ReportPluginRegistry plugins;
    private final AuditPort auditPort;

    public ReportEngine(ReportPluginRegistry plugins, AuditPort auditPort) {
        this.plugins = plugins;
        this.auditPort = auditPort;
    }

    public ReportResult run(PluginId pluginId, ReportRequest request) {
        ReportPlugin plugin = plugins.get(pluginId);
        auditPort.record(pluginId);
        return plugin.generate(request);
    }
}
```

```java
public final class ReportPluginRegistry {
    private final Map<PluginId, ReportPlugin> plugins;

    public ReportPluginRegistry(List<ReportPlugin> plugins) {
        this.plugins = plugins.stream()
            .collect(Collectors.toUnmodifiableMap(
                ReportPlugin::id,
                plugin -> plugin
            ));
    }

    public ReportPlugin get(PluginId pluginId) {
        ReportPlugin plugin = plugins.get(pluginId);
        if (plugin == null) {
            throw new IllegalArgumentException("unsupported plugin: " + pluginId);
        }
        return plugin;
    }
}
```

이 코드는 lookup을 하지만 아직 service locator는 아니다.

- `ReportEngine`이 plugin lookup 의존성을 생성자에서 드러낸다.
- registry는 `ReportPlugin` 한 종류만 다룬다.
- `AuditPort` 같은 다른 협력자는 registry에서 꺼내지 않고 별도로 주입받는다.
- key는 Spring bean name이 아니라 host-plugin 계약인 `PluginId`다.

## 좋은 예: host가 자기 plugin registry를 주입받는다 (계속 2)

초보자 기준으로는 이것만 보면 된다.

**"plugin을 고르는 책임은 registry에 있지만, 나머지 의존성은 여전히 생성자 주입에 남아 있다."**

---

## 나쁜 예: plugin registry라는 이름의 앱 전체 조회소

```java
public final class PluginLocator {
    private final ApplicationContext context;

    public PluginLocator(ApplicationContext context) {
        this.context = context;
    }

    public <T> T get(Class<T> type, String name) {
        return context.getBean(name, type);
    }
}

public final class ReportEngine {
    private final PluginLocator locator;

    public ReportEngine(PluginLocator locator) {
        this.locator = locator;
    }

    public ReportResult run(String pluginName, ReportRequest request) {
        ReportPlugin plugin = locator.get(ReportPlugin.class, pluginName);
        AuditPort auditPort = locator.get(AuditPort.class, "auditPort");
        return plugin.generate(request);
    }
}
```

겉으로는 "plugin을 찾는 helper"처럼 보이지만, 실제로는 경계가 크게 무너진다.

- `ReportEngine` 생성자만 봐서는 `AuditPort`가 필요한지 알 수 없다.
- `pluginName`이 plugin 계약 key가 아니라 container bean name 규칙으로 흐르기 쉽다.
- `PluginLocator`는 plugin뿐 아니라 아무 타입이나 꺼낼 수 있다.
- 다른 서비스도 같은 locator를 쓰기 시작하면 app-wide service locator가 된다.

즉 이름이 `PluginRegistry`, `PluginManager`라고 붙어 있어도 public API가 `get(Class<T>)`, `get(String)`이면 좁은 registry보다 locator에 더 가깝다.

---

## 아직 좁은 registry라고 볼 수 있는 신호

- host나 coordinator가 `ReportPluginRegistry`, `PaymentPluginRegistry`처럼 **extension point별 registry**를 생성자로 받는다.
- registry가 돌려주는 값이 `ReportPlugin`처럼 **한 인터페이스 계열로 고정**되어 있다.
- key가 bean name이 아니라 `PluginId`, `Capability`, `FormatType` 같은 **계약상 domain key**다.
- registry는 부트스트랩 시점에 조립되고, 요청 처리 중에는 **읽기 전용 lookup**에 가깝다.
- plugin이 필요한 다른 협력자(`Repository`, `Port`, `Client`)는 registry에서 꺼내지 않고 **명시적으로 주입**한다.
- 테스트에서 Spring context 없이 fake plugin 리스트나 fake registry로 시작할 수 있다.

---

## locator drift 신호

- 여러 서비스가 하나의 `PluginManager`나 `ApplicationContext`를 공용 조회소처럼 쓴다.
- public API가 `get(String)`, `get(Class<T>)`, `findAny(...)`처럼 넓다.
- plugin lookup과 함께 repository, notifier, external client까지 같은 통로에서 꺼낸다.
- plugin id보다 bean name 문자열 규칙이 더 중요해진다.
- plugin 구현체도 다시 locator를 호출해 자기 의존성을 찾는다.
- 클래스 생성자만 보고 실제 협력자를 말하기 어려워진다.

코드 리뷰에서 빠르게 묻는 질문은 이것이다.

**"이 클래스가 plugin 선반 하나를 받는가, 아니면 건물 안내데스크 하나만 받는가?"**

후자라면 locator drift를 먼저 의심한다.

---

## 흔한 오해

- **"plugin을 런타임에 찾으면 전부 service locator인가요?"**
  아니다. runtime lookup 자체는 문제 아니다. host가 자기 extension point용 registry를 명시적으로 주입받아 쓰면 정상적인 registry다.
- **"plugin registry도 문자열 key를 쓰면 무조건 나쁜가요?"**
  꼭 그렇지는 않다. 다만 문자열이 bean name인지, host-plugin 계약의 안정적인 plugin id인지 구분해야 한다. 입문 단계에서는 `PluginId` 같은 타입을 두는 편이 더 안전하다.
- **"`ApplicationContext`로 plugin bean을 모으는 것 자체가 문제인가요?"**
  아니다. composition root나 bootstrap 단계에서 plugin 목록을 모아 registry를 만드는 것은 괜찮다. 문제는 use case 본문에서 요청마다 `getBean(...)`을 하는 것이다.
- **"`PluginManager`라는 이름이면 다 locator인가요?"**
  아니다. 이름보다 범위를 본다. load/enable/disable/검증을 한 extension system 안에서만 관리하면 manager일 수 있다. 하지만 앱 어디서나 의존성을 꺼내게 하면 locator 쪽이다.

플러그인 lifecycle, 버전 호환성, 활성화 정책까지 같이 보고 싶다면 [Plugin Architecture](./plugin-architecture-pattern-language.md)를 이어서 읽으면 된다.

## 한 줄 정리

Plugin lookup은 **host가 자기 extension point용으로 좁게 주입받은 registry**에 머무는 동안에는 괜찮다.
하지만 **앱 전체가 쓰는 범용 `PluginManager`/`Locator`가 되어 숨은 의존성을 해소하기 시작하면 service locator drift**로 보는 편이 맞다.
