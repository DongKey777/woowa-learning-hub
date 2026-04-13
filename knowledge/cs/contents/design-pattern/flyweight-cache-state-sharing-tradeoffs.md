# Flyweight: 캐시와 상태 공유의 경계

> 한 줄 요약: Flyweight 패턴은 공유 가능한 내부 상태를 재사용해 메모리를 줄이지만, 외부 상태와 섞이면 캐시처럼 보이는 공유 버그가 생긴다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [Singleton (싱글톤)](./singleton.md)
> - [Registry Pattern](./registry-pattern.md)
> - [Prototype Pattern Caveats](./prototype-pattern-caveats.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Flyweight는 **많이 생성되는 객체의 공통 상태를 공유해 메모리 사용을 줄이는 패턴**이다.  
핵심은 내부 상태와 외부 상태를 분리하는 것이다.

backend에서는 이 패턴이 다음처럼 보인다.

- 대량의 코드 테이블 객체
- 문서 렌더링 토큰
- 반복되는 정책 객체
- 동일 타입의 많은 작은 값 객체

### Retrieval Anchors

- `flyweight pattern`
- `shared intrinsic state`
- `extrinsic state`
- `memory optimization`
- `object pooling tradeoff`

---

## 깊이 들어가기

### 1. 내부 상태는 공유하고 외부 상태는 넘긴다

Flyweight는 객체 안에 모든 걸 넣지 않는다.

- 내부 상태: 공유 가능하고 변하지 않는 값
- 외부 상태: 호출 시점마다 달라지는 값

이 분리가 없으면 공유가 곧 버그가 된다.

### 2. 캐시와 비슷하지만 목적이 다르다

Flyweight는 "같은 객체를 재사용"한다는 점에서 캐시처럼 보인다.  
하지만 목적은 속도보다 메모리 절약과 중복 제거에 가깝다.

### 3. 상태 공유는 테스트를 어렵게 만든다

공유 객체가 mutable하면 한 곳의 변경이 다른 곳에 영향을 준다.

- 동시성 위험
- 디버깅 난이도 상승
- 예측 불가능한 참조 공유

---

## 실전 시나리오

### 시나리오 1: 코드값/등급 객체

변하지 않는 코드값을 Flyweight로 공유할 수 있다.

### 시나리오 2: 대량 렌더링 토큰

같은 스타일 정보를 재사용하면서 외부 좌표만 바꾸는 식이 적합하다.

### 시나리오 3: 권한/정책 상수

공유 가능한 규칙 오브젝트는 메모리를 아낄 수 있다.

---

## 코드로 보기

### Flyweight Factory

```java
public class GradeFlyweightFactory {
    private final Map<String, Grade> cache = new HashMap<>();

    public Grade get(String code) {
        return cache.computeIfAbsent(code, Grade::new);
    }
}
```

### 외부 상태 분리

```java
public record RenderContext(int x, int y, String color) {}

public class TextToken {
    private final String text;

    public void render(RenderContext context) {
        // text는 공유, 위치는 외부 상태
    }
}
```

### 주의

```java
// mutable state를 공유하면 Flyweight가 아니라 shared mutable bug가 된다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 새 객체 생성 | 단순하다 | 메모리 사용이 늘어난다 | 객체 수가 적을 때 |
| Flyweight | 메모리를 아낀다 | 외부 상태 분리가 필요하다 | 객체가 대량 생성될 때 |
| 캐시 | 재사용이 쉽다 | eviction과 일관성 문제가 있다 | 조회 비용이 높을 때 |

판단 기준은 다음과 같다.

- 내부 상태가 정말 공유 가능하면 Flyweight
- 값이 자주 바뀌면 캐시나 새 객체가 더 낫다
- mutable 공유는 피한다

---

## 꼬리질문

> Q: Flyweight와 캐시는 같은가요?
> 의도: 재사용 목적과 메모리 절약 목적을 구분하는지 확인한다.
> 핵심: 겹치는 부분은 있지만 목적이 다르다.

> Q: 내부 상태와 외부 상태의 차이는 무엇인가요?
> 의도: 공유 가능성의 기준을 아는지 확인한다.
> 핵심: 내부 상태는 공유, 외부 상태는 호출 시점에 전달한다.

> Q: Flyweight가 위험한 이유는 무엇인가요?
> 의도: mutable shared state의 위험을 아는지 확인한다.
> 핵심: 공유 객체가 예기치 않게 오염될 수 있다.

## 한 줄 정리

Flyweight는 대량 객체의 공통 상태를 공유해 메모리를 아끼지만, 외부 상태 분리가 안 되면 공유 버그로 바뀐다.

