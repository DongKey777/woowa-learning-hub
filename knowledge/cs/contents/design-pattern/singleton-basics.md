# 싱글톤 패턴 기초 (Singleton Basics)

> 한 줄 요약: 싱글톤은 인스턴스를 하나만 만들어 어디서든 같은 객체를 쓰게 하는 패턴인데, 숨은 전역 상태와 테스트 어려움을 함께 가져온다는 점을 알고 써야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [싱글톤 Java 구현 방법](./singleton-java.md)
- [싱글톤 vs DI 컨테이너 스코프](./singleton-vs-di-container-scope.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [IoC 컨테이너와 DI](../spring/ioc-di-container.md)

retrieval-anchor-keywords: singleton pattern, singleton basics, 싱글톤 패턴, 인스턴스 하나, 전역 객체 패턴, when to use singleton, singleton problem, singleton test difficulty, singleton hidden state, global state smell, 싱글톤이 뭔가요, 싱글톤 단점, beginner singleton

---

## 핵심 개념

싱글톤은 클래스의 인스턴스가 **딱 하나만** 존재하도록 강제하는 패턴이다. 앱 전체에서 같은 설정 객체, 공유 캐시, 커넥션 풀 등 "하나여야 의미 있는" 자원을 공유할 때 쓴다.

입문자가 자주 오해하는 부분은 "전역 변수와 다른 것"이라는 점이다. 싱글톤도 전역 상태를 만들며, 어떻게 쓰느냐에 따라 단순한 전역 변수보다 오히려 더 숨기기 쉬운 의존성이 생긴다.

## 한눈에 보기

```
AppConfig.getInstance()  ─→  (항상 같은 인스턴스)
    ↑ 어디서든 호출 가능
```

| 항목 | 설명 |
|------|------|
| 목적 | 인스턴스를 하나로 제한해 공유 |
| 대표 예 | 설정 객체, 로거, 커넥션 풀 |
| 핵심 메서드 | `getInstance()` 또는 정적 팩토리 |
| 주의점 | 숨은 의존성, 테스트 격리 어려움 |

## 상세 분해

싱글톤은 보통 세 가지 장치로 구성된다.

- **생성자를 `private`으로 막는다** — 외부에서 `new`로 만들지 못하게 한다.
- **정적 필드에 인스턴스를 저장한다** — 클래스가 살아있는 동안 하나의 참조를 유지한다.
- **`getInstance()` 같은 정적 메서드로 꺼내준다** — 어디서든 같은 객체를 반환한다.

Java에서 가장 간단한 형태:

```java
public class AppConfig {
    private static final AppConfig INSTANCE = new AppConfig();
    private AppConfig() {}
    public static AppConfig getInstance() { return INSTANCE; }
}
```

멀티스레드 안전성 등 구현 디테일은 [싱글톤 Java 구현 방법](./singleton-java.md)에서 다룬다.

## 흔한 오해와 함정

- **"싱글톤은 전역 변수보다 좋다"** — 접근 제어는 다르지만, 숨은 전역 상태라는 본질은 같다. 클래스 어디서든 호출할 수 있어서 의존성이 보이지 않게 된다.
- **"Spring Bean도 싱글톤이니까 같다"** — Spring Bean의 기본 스코프가 싱글톤이지만, Spring은 DI 컨테이너가 수명을 관리한다. 코드에 `getInstance()`를 직접 호출하는 GoF 싱글톤과는 다른 구조다.
- **"테스트할 때 그냥 쓰면 된다"** — 싱글톤은 테스트 간 상태를 공유해서 테스트 순서에 따라 결과가 달라질 수 있다.

## 실무에서 쓰는 모습

**쓰기 적당한 경우**: 스레드 안전하게 만든 설정 로더, 앱 수명 동안 변하지 않는 캐시 레지스트리.

**쓰기 부적당한 경우**: 상태가 자주 바뀌는 서비스 객체, 테스트에서 가짜(mock)로 교체해야 하는 외부 연동 객체. 이런 경우는 Spring DI 컨테이너에 Bean으로 등록하고 생성자 주입으로 받는 방식이 더 낫다.

## 더 깊이 가려면

- [싱글톤 Java 구현 방법](./singleton-java.md) — Eager / Lazy / DCL / Enum 등 구현 변형과 멀티스레드 안전성 비교
- [싱글톤 vs DI 컨테이너 스코프](./singleton-vs-di-container-scope.md) — Spring Bean 스코프와의 차이 및 언제 어느 쪽을 쓸지

## 면접/시니어 질문 미리보기

> Q: 싱글톤의 가장 큰 단점은 무엇인가?
> 의도: 패턴의 트레이드오프를 이해하는지 확인한다.
> 핵심: 숨은 전역 상태와 테스트 격리 어려움이다.

> Q: Spring Bean의 기본 스코프가 싱글톤인데, GoF 싱글톤과 어떻게 다른가?
> 의도: DI 컨테이너와 직접 구현 싱글톤을 구분하는지 확인한다.
> 핵심: Spring은 DI 컨테이너가 수명을 관리하므로 테스트에서 교체가 쉽다.

> Q: 멀티스레드 환경에서 싱글톤을 안전하게 만들려면 어떻게 하는가?
> 의도: 동시성 기본 감각이 있는지 확인한다.
> 핵심: Enum 싱글톤 또는 정적 홀더 패턴이 가장 간단하다.

## 한 줄 정리

싱글톤은 인스턴스를 하나로 공유하지만, 숨은 전역 상태와 테스트 어려움을 함께 가져오므로 Spring DI 컨테이너로 대체할 수 있는지 먼저 검토하는 것이 좋다.
