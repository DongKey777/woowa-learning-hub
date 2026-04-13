# Plugin Architecture: 기능을 꽂아 넣는 패턴 언어

> 한 줄 요약: Plugin Architecture는 핵심 엔진과 확장 기능을 분리해, 새로운 기능을 코드 변경 최소화로 꽂아 넣는 구조다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Registry Pattern](./registry-pattern.md)
> - [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Plugin Architecture는 **핵심 시스템이 확장 지점을 정의하고 외부 모듈이 그 지점에 붙는 구조**다.  
backend에서는 전략/핸들러/필터/리포터/수집기 같은 확장 지점이 많다.

핵심은 다음이다.

- extension point를 먼저 정의한다
- plugin 계약을 안정적으로 유지한다
- 로딩/활성화/비활성화 정책을 분리한다

### Retrieval Anchors

- `plugin architecture`
- `extension point`
- `plugin contract`
- `dynamic module loading`
- `host plugin model`

---

## 깊이 들어가기

### 1. 플러그인은 단순한 인터페이스가 아니다

인터페이스만 있다고 plugin이 되는 건 아니다.

- 호스트가 플러그인을 찾고
- 계약을 검사하고
- 활성화 순서를 관리하고
- 실패를 격리해야 한다

### 2. Registry와 자주 함께 쓴다

Plugin은 보통 Registry에 등록된다.  
이름, 버전, capability로 조회해 실행한다.

### 3. 과하면 확장 지옥이 된다

플러그인을 너무 쉽게 열면 다음 문제가 생긴다.

- 호환성 관리가 어려워진다
- 버전 충돌이 생긴다
- host가 불안정해진다

---

## 실전 시나리오

### 시나리오 1: 결제 수단 확장

새로운 결제 provider를 기존 엔진에 끼워 넣을 때 좋다.

### 시나리오 2: 리포트 포맷 확장

CSV, JSON, XLSX 출력기를 플러그인으로 분리할 수 있다.

### 시나리오 3: 비즈니스 룰 확장

할인, 점검, 검증 규칙을 외부 모듈로 교체할 수 있다.

---

## 코드로 보기

### Plugin contract

```java
public interface ReportPlugin {
    String name();
    boolean supports(ReportContext context);
    ReportResult generate(ReportContext context);
}
```

### Host

```java
public class ReportEngine {
    private final List<ReportPlugin> plugins;

    public ReportResult run(ReportContext context) {
        return plugins.stream()
            .filter(plugin -> plugin.supports(context))
            .findFirst()
            .orElseThrow()
            .generate(context);
    }
}
```

### Registry와 결합

```java
registry.register(plugin.name(), plugin);
```

플러그인은 확장성의 대가로 계약 관리 비용을 요구한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 코드 수정 | 단순하다 | 배포마다 코어를 바꿔야 한다 | 확장이 거의 없을 때 |
| Plugin Architecture | 확장을 분리한다 | 계약/버전 관리가 필요하다 | extension point가 중요할 때 |
| Registry + Strategy | 가볍게 확장한다 | host가 비대해질 수 있다 | 플러그인보다 가벼운 확장 |

판단 기준은 다음과 같다.

- 확장 지점이 장기적으로 살아남으면 plugin을 본다
- 한두 개 구현만 바뀌면 registry/strategy로 충분할 수 있다
- 계약 안정성이 없으면 plugin을 만들지 않는다

---

## 꼬리질문

> Q: Plugin Architecture와 Registry는 같은 건가요?
> 의도: 조회 구조와 확장 구조를 구분하는지 확인한다.
> 핵심: Registry는 찾는 방식이고, Plugin Architecture는 호스트-확장 관계다.

> Q: 플러그인 계약이 왜 중요한가요?
> 의도: 호환성과 버전 관리를 아는지 확인한다.
> 핵심: 계약이 깨지면 확장성이 아니라 장애가 된다.

> Q: 플러그인 시스템을 언제 피해야 하나요?
> 의도: 복잡한 구조를 남용하지 않는지 확인한다.
> 핵심: 확장 요구가 약하면 오히려 과하다.

## 한 줄 정리

Plugin Architecture는 호스트와 확장 모듈의 계약을 분리해, 기능을 안전하게 꽂아 넣는 패턴 언어다.

