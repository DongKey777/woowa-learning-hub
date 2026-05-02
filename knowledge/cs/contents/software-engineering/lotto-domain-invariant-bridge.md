---
schema_version: 3
title: 'lotto 번호 6개·중복없음·1-45 도메인 불변식을 어디에서 보장하나'
concept_id: software-engineering/lotto-domain-invariant-bridge
canonical: false
category: software-engineering
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- domain-invariant
- input-vs-domain-validation
- private-constructor
aliases:
- lotto 도메인 불변식
- 로또 번호 검증 위치
- Lotto 클래스 불변식
- 입력 검증 vs 도메인 검증
- 로또 6개 중복 1-45 보장
intents:
- mission_bridge
- design
prerequisites:
- software-engineering/domain-invariants-as-contracts
linked_paths:
- contents/software-engineering/domain-invariants-as-contracts.md
- contents/software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md
forbidden_neighbors:
- contents/software-engineering/order-validation-annotation-vs-domain-rule-card.md
expected_queries:
- 로또 번호 6개 중복없음을 컨트롤러에서 검사할까 도메인에서 검사할까?
- Lotto 생성자에서 던지는 게 맞아 정적 팩토리에서 던지는 게 맞아?
- 입력 파싱 검증이랑 도메인 불변식이 어떻게 달라?
- 1-45 범위는 어디에서 보장해야 해?
---

# lotto 번호 6개·중복없음·1-45 도메인 불변식을 어디에서 보장하나

> 한 줄 요약: 도메인 불변식 (6개·중복없음·1-45)은 *반드시 도메인 객체 안*에서 보장한다. 입력 파싱/형식 검증은 컨트롤러/DTO에서 해도 되지만, *Lotto가 한 번이라도 잘못된 상태로 존재하지 않게* 하는 책임은 도메인이 진다.

**난이도: 🟢 Beginner**

**미션 컨텍스트**: lotto (Woowa Java 트랙)

관련 문서:

- [Domain Invariants as Contracts](./domain-invariants-as-contracts.md) — 일반 개념
- [Validation Boundary: Input vs Domain Invariant](./validation-boundary-input-vs-domain-invariant-mini-bridge.md) — 두 검증의 분기

## 미션의 어디에 불변식이 보이는가

`Lotto` 객체는 다음 세 가지를 *항상 동시에 만족*해야 한다:

1. 번호 *정확히 6개*
2. *중복 없음*
3. 각 번호가 *1-45 범위*

이 세 조건을 *불변식 (invariant)*이라 부른다. *Lotto 인스턴스가 존재하는 한* 이들은 깨지지 않아야 한다.

학습자가 자주 작성하는 코드:

```java
public class LottoController {
    public Result purchase(LottoRequest req) {
        if (req.numbers().size() != 6) throw ...;             // 1) 컨트롤러에서 검증
        if (new HashSet<>(req.numbers()).size() != 6) throw ...;
        for (int n : req.numbers()) if (n < 1 || n > 45) throw ...;
        Lotto lotto = new Lotto(req.numbers());                // 2) 검증 끝났으니 그대로
    }
}
```

이 모양은 *이번 호출은 안전*하지만 *Lotto 생성 경로가 컨트롤러뿐일 때*만 작동한다. 자동 생성기, 테스트 코드, 다른 컨트롤러가 `new Lotto(...)`를 직접 부르면 *검증이 누락*된다.

## 왜 도메인이 책임지는가

### 불변식은 *클래스의 계약*

`Lotto` 타입을 보는 모든 코드는 *"이 객체는 6개·중복없음·1-45 보장"*을 전제로 한다. 그 전제가 *생성자/팩토리 메소드*에서만 보장되면 모든 호출자가 *수동으로 검증할 필요가 사라진다*.

```java
public class Lotto {
    private final Set<Integer> numbers;

    private Lotto(Set<Integer> numbers) {
        this.numbers = numbers;
    }

    public static Lotto from(List<Integer> input) {
        validate(input);
        return new Lotto(new HashSet<>(input));
    }

    private static void validate(List<Integer> numbers) {
        if (numbers.size() != 6) throw new IllegalArgumentException("6개여야 합니다");
        if (new HashSet<>(numbers).size() != numbers.size())
            throw new IllegalArgumentException("중복은 안 됩니다");
        for (int n : numbers)
            if (n < 1 || n > 45)
                throw new IllegalArgumentException("1-45 범위여야 합니다");
    }
}
```

private 생성자 + 정적 팩토리 + private validate. *외부 진입로*가 `from(...)` 하나뿐이므로 *모든 Lotto 인스턴스*가 검증을 거친다.

### 입력 검증은 별개의 층

컨트롤러에서 `Bean Validation` (`@Valid`)으로 *형식*을 검사하는 건 OK — 음수/문자열/비어있음 같은 *입력 형식*을 일찍 거른다. 하지만 *도메인 불변식*까지 컨트롤러에서 모두 짜면 *도메인이 자기 계약을 책임지지 않는 빈 껍질*이 된다.

| 위치 | 책임 |
| ---- | ---- |
| 컨트롤러/DTO | 입력 형식 (null, 타입, 길이) |
| 도메인 객체 | 도메인 불변식 (6개·중복없음·1-45) |

## lotto에서 자주 보는 잘못된 분기

### 잘못 1 — Setter로 깨뜨릴 수 있는 객체

```java
public class Lotto {
    private List<Integer> numbers;
    public void setNumbers(List<Integer> numbers) { this.numbers = numbers; }  // ❌
}
```

setter 한 줄로 *언제든 불변식이 깨진다*. `private final` 필드 + setter 없음이 기본.

### 잘못 2 — 검증을 utility에 두기

```java
public class LottoValidator {
    public static void validate(List<Integer> numbers) { ... }
}

// 호출자가 까먹으면 검증 누락
LottoValidator.validate(numbers);
Lotto lotto = new Lotto(numbers);
```

검증과 생성이 *분리*되면 *호출자가 책임*지게 된다. 도메인이 *자기 검증을 잊은 채로 생성될 수 있다*. 검증은 생성 경로 안에 있어야 한다.

### 잘못 3 — 컨트롤러에서 한 번 검증했으니 도메인은 생략

```java
@PostMapping
public Result buy(@Valid LottoRequest req) {  // 컨트롤러에서 검증
    return service.buy(req.numbers());        // Lotto 생성자는 검증 생략 가정
}
```

다른 진입점 (배치 잡, 테스트, 자동 생성기)이 *같은 도메인 객체*를 *같은 가정 없이* 만들 수 있다. 도메인 불변식은 *진입점에 의존하지 않아야* 한다.

### 잘못 4 — Lotto가 컬렉션을 그대로 노출

```java
public List<Integer> getNumbers() {
    return numbers;  // ❌ 외부에서 add/remove 가능
}
```

내부 컬렉션을 노출하면 *외부 변형*으로 불변식이 깨진다. `Collections.unmodifiableList(...)` 또는 `List.copyOf(...)`로 방어.

## 자가 점검

- [ ] `Lotto`의 모든 생성 경로가 *정적 팩토리 한 곳*을 거치는가?
- [ ] 검증 로직이 *그 정적 팩토리 안*에 있는가? (utility 호출 의존 X)
- [ ] 필드가 `private final`이고 setter가 없는가?
- [ ] 외부에 노출되는 컬렉션이 *방어적 복사 또는 unmodifiable*인가?
- [ ] 입력 형식 (`@Valid`)과 도메인 불변식의 *책임이 분리*돼 있는가?

## 다음 문서

- 더 큰 그림: [Domain Invariants as Contracts](./domain-invariants-as-contracts.md)
- 두 검증의 분기: [Validation Boundary: Input vs Domain Invariant](./validation-boundary-input-vs-domain-invariant-mini-bridge.md)
- 정적 팩토리 패턴: *lotto 정적 팩토리 브리지* (별도 문서, 같은 Wave)
