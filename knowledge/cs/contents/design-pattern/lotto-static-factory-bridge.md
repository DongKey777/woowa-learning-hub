---
schema_version: 3
title: 'lotto 미션 Lotto.from / Lotto.auto 정적 팩토리 메소드의 의도'
concept_id: design-pattern/lotto-static-factory-bridge
canonical: false
category: design-pattern
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- static-factory-naming
- constructor-vs-from
- intention-revealing
aliases:
- lotto 정적 팩토리
- Lotto.from
- Lotto.auto
- 로또 정적 팩토리 메소드
- Lotto 생성자 대신
intents:
- mission_bridge
- design
prerequisites:
- design-pattern/constructor-vs-static-factory-vs-factory-pattern
linked_paths:
- contents/design-pattern/constructor-vs-static-factory-vs-factory-pattern.md
- contents/language/java/java-instance-static-factory-methods-primer.md
forbidden_neighbors:
- contents/design-pattern/factory-misnaming-checklist.md
expected_queries:
- 로또에서 Lotto.from(numbers)랑 new Lotto(numbers) 차이가 뭐야?
- 정적 팩토리 메소드 이름은 어떻게 짓는 거야?
- Lotto.auto()는 왜 생성자 대신 정적 메소드로 만들어?
- 미션에서 자동 생성과 수동 입력을 분리할 때 어떻게 표현해?
---

# lotto 미션 Lotto.from / Lotto.auto 정적 팩토리 메소드의 의도

> 한 줄 요약: 정적 팩토리 메소드는 *생성자가 표현하지 못하는 의도*를 메소드 이름으로 표현한다. `Lotto.from(List<Integer>)`은 "주어진 번호로 만든다", `Lotto.auto()`는 "랜덤으로 6개 뽑는다" — `new Lotto(...)` 한 가지 시그니처로는 둘을 구별할 수 없다.

**난이도: 🟢 Beginner**

**미션 컨텍스트**: lotto (Woowa Java 트랙) — 도메인 객체 생성 시점

관련 문서:

- [생성자 vs 정적 팩토리 vs 팩토리 패턴](./constructor-vs-static-factory-vs-factory-pattern.md) — 일반 비교
- [Java 인스턴스/정적 팩토리 메소드 Primer](../language/java/java-instance-static-factory-methods-primer.md) — 자바 관용구

## 미션의 어디에 정적 팩토리가 등장하는가

lotto 미션은 *6개의 1-45 숫자*를 가진 `Lotto` 도메인 객체를 만들어야 한다. 두 가지 생성 경로가 있다:

```java
// 1) 사용자가 당첨 번호를 직접 입력
Lotto winning = Lotto.from(List.of(1, 2, 3, 4, 5, 6));

// 2) 자동 생성기가 1-45 중 6개를 랜덤으로
Lotto auto = Lotto.auto();
```

같은 의미를 생성자만으로 쓰면 어색해진다:

```java
Lotto winning = new Lotto(List.of(1, 2, 3, 4, 5, 6));  // 의도가 가려짐
Lotto auto = new Lotto();                              // 어떤 6개?? 비어있음??
```

생성자는 *시그니처(파라미터 타입)*만으로 구분되므로, 같은 타입을 받는 두 의도가 있으면 *이름으로 구별할 수 없다*. 정적 팩토리 메소드는 *이름*으로 의도를 드러낸다.

## 정적 팩토리가 주는 네 가지 이득

### 1. 이름이 의도를 표현한다

`Lotto.from(numbers)`는 *주어진 번호 그대로*임을 명시한다. `Lotto.auto()`는 *자동 생성*임을 명시한다. *읽는 사람*이 생성 경로를 즉시 안다.

### 2. 같은 시그니처에 다른 의도 OK

`Lotto.of(1,2,3,4,5,6)`처럼 *가변인자* 버전을 추가해도 이름이 다르면 OK. 생성자는 동일 타입 시그니처가 충돌한다.

### 3. 캐싱/재사용이 가능하다

`Lotto.auto()`를 여러 번 호출해도 *내부 풀에서 재사용*하거나 *Random 인스턴스를 재활용*할 수 있다. 생성자는 매 호출마다 *반드시 새 인스턴스*를 만든다 (자바 언어 규칙).

### 4. 검증 책임이 한 곳에 모인다

```java
public static Lotto from(List<Integer> numbers) {
    validate(numbers);  // 6개·중복없음·1-45 검사
    return new Lotto(new HashSet<>(numbers));
}

private Lotto(Set<Integer> numbers) {  // private 생성자
    this.numbers = numbers;
}
```

private 생성자 + 정적 팩토리만 *외부에 노출*하면 *모든 생성 경로가 검증*을 거친다. 이 패턴이 *도메인 불변식 보장*의 1단계다.

## lotto 미션의 자주 보이는 안티패턴

### 안티 1 — 정적 팩토리 이름이 모호함

```java
public static Lotto get(List<Integer> nums) { ... }    // ❌ get은 조회 의미
public static Lotto build(List<Integer> nums) { ... }  // ❌ Builder 패턴 연상
```

자바 관용구는 다음과 같다:

- `from(input)` — 단일 입력 변환 (가장 흔함)
- `of(args...)` — 가변인자 (예: `List.of(1,2,3)`)
- `valueOf(input)` — 입력값으로부터 동등한 값 객체 (예: `Integer.valueOf("42")`)
- `getInstance()` — 싱글톤
- `newInstance()` — 매번 새 인스턴스 보장

미션 PR에서 멘토가 *"이름이 의도를 안 드러내요"* 라고 지적하는 게 이 패턴이다.

### 안티 2 — 정적 팩토리 + public 생성자

```java
public Lotto(List<Integer> numbers) { ... }   // public
public static Lotto from(List<Integer> numbers) { return new Lotto(numbers); }
```

public 생성자가 살아있으면 *팩토리 우회*가 가능하다. 검증을 바이패스할 수 있어 *불변식 보장*이 깨진다. private 생성자가 필수.

### 안티 3 — 자동 생성 로직을 정적 팩토리 안에 박음

```java
public static Lotto auto() {
    List<Integer> pool = IntStream.rangeClosed(1, 45)...;  // 책임 누적
    Collections.shuffle(pool);
    return new Lotto(new HashSet<>(pool.subList(0, 6)));
}
```

`auto()`가 *생성 알고리즘*까지 가지면 *테스트하기 어렵다* (Random 주입 불가). 생성 전략은 별도 컴포넌트 (`LottoNumberGenerator`)로 빼고 `Lotto.from(generator.generate())`로 호출하는 게 깔끔.

## 자가 점검

- [ ] `Lotto`의 public 생성자가 없고, *모든 생성 경로*가 정적 팩토리를 거치는가?
- [ ] 정적 팩토리 이름이 *의도*를 드러내는가? (`from`, `of`, `auto` 등 관용구 사용)
- [ ] 검증 로직이 *생성자*가 아니라 *정적 팩토리*에 있는가?
- [ ] 자동 생성 알고리즘은 별도 객체로 분리됐는가? (테스트 가능성)
- [ ] 동일 시그니처의 다른 의도가 *이름으로 구별*되는가?

## 다음 문서

- 더 큰 그림: [생성자 vs 정적 팩토리 vs 팩토리 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
- Java 관용구로서의 정적 팩토리: [Java 인스턴스/정적 팩토리 메소드 Primer](../language/java/java-instance-static-factory-methods-primer.md)
- Factory 이름 체크: [Factory Misnaming Checklist](./factory-misnaming-checklist.md)
