# Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림

> 한 줄 요약: 이름을 붙이기 전에 먼저 질문을 고정한다. **"지금 새로 만들고 있나?"**면 `Factory`, 아니면 선택/해석 책임을 먼저 본다.

**난이도: 🟢 Beginner**

> Beginner Route: `[entrypoint]` 이 문서 -> `[beginner bridge]` [Strategy vs Policy Selector Naming](./strategy-policy-selector-naming.md) -> `[checklist]` [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md) -> `[deep dive]` [팩토리 (Factory)](./factory.md)

관련 문서:

- [팩토리 패턴 기초](./factory-basics.md)
- [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
- [Factory Misnaming Checklist: create 없는 `*Factory`를 리뷰에서 빨리 가르기](./factory-misnaming-checklist.md)
- [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
- [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: factory selector resolver beginner, factory vs selector vs resolver, factory selector resolver 차이, selector naming entrypoint, selector naming first hit, selector 이름 뭐로 지어야 해, creation vs selection naming, 생성 vs 선택 네이밍, 생성 책임 vs 선택 책임, 생성이 아니면 factory 아님, 처음 배우는데 factory selector resolver, 처음 배우는데 selector naming, factory 이름 언제 쓰는지, selector 이름 언제 쓰는지

---

## 먼저 10초 질문

처음 배우는데 이름이 헷갈리면, 패턴 용어보다 이 질문 하나를 먼저 본다.

**"이 클래스가 호출 시점에 새 객체를 만들고 조립하나?"**

- 예: provider별 client를 credentials/timeout과 함께 새로 조립한다 -> `Factory`
- 아니면 대부분 `Selector`/`Resolver` 쪽 질문이다

## `selector`로 검색했다면 여기서 먼저 자르기

처음 배우는데 `selector`라는 단어만 떠올라도, 바로 strategy deep dive로 내려가기보다 아래 큰 그림부터 잡는 편이 안전하다.

- raw 입력을 뜻으로 바꾸는 중이면 `Resolver`
- 이미 뜻이 정해진 후보 중 하나를 고르는 중이면 `Selector`
- 새 객체를 조립하는 중이면 `Factory`

`selector naming`, `selector 이름 언제 쓰는지`, `factory selector 차이` 같은 검색은 이 문서에서 먼저 끊고, 그다음 [Strategy vs Policy Selector Naming](./strategy-policy-selector-naming.md)으로 내려가면 된다.

---

## 30초 비교표

| 지금 코드가 답하는 질문 | 더 맞는 이름 | 왜 `Factory`가 아닌가 |
|---|---|---|
| "이 raw 입력 코드를 어떤 도메인 값으로 풀까?" | `Resolver` | 입력 해석이 중심이다 |
| "조건을 보고 후보 중 무엇을 쓸까?" | `Selector` | 후보 선택이 중심이다 |
| "이 key에 등록된 객체는 무엇이지?" | `Registry` | 등록 lookup이 중심이다 |
| "지금 새 객체를 만들어 반환할까?" | `Factory` | 생성/조립이 중심이므로 factory가 맞다 |

짧게 외우면 이 한 줄이면 충분하다.

**해석은 `Resolver`, 선택은 `Selector`, 생성은 `Factory`다.**

---

## 1분 예시: 결제 흐름 네이밍 쪼개기

```java
PaymentMethod method = paymentMethodResolver.resolve(request.getMethodCode());
PaymentPolicy policy = paymentPolicySelector.select(order, method);
PaymentClient client = paymentClientFactory.create(method.getProvider());
```

- `paymentMethodResolver`: raw code를 도메인 의미로 해석
- `paymentPolicySelector`: 조건을 보고 후보 정책 선택
- `paymentClientFactory`: 선택된 provider 기준으로 새 client 생성

이렇게 쪼개면 "생성 문제"와 "선택/해석 문제"가 섞이지 않는다.

---

## 자주 헷갈리는 포인트

- "런타임에 고르니까 factory 아닌가요?"
  - 아니다. 런타임 선택은 `Selector`/`Resolver`에서도 일어난다. factory 여부는 생성 책임으로 본다.
- "`Map.get(...)`을 쓰면 다 registry 아닌가요?"
  - 아니다. raw 입력을 정규화하면 `Resolver`, 조건 분기면 `Selector`, 등록 lookup이면 `Registry`다.
- "`create()` 메서드가 있으면 factory인가요?"
  - 이름보다 실제 책임을 본다. 기존 객체를 고르기만 하면 factory가 아니다.

---

## 다음 읽기 (언제 쓰는지 빠르게 이어가기)

- `Factory`를 언제 쓰는지 기초부터: [팩토리 패턴 기초](./factory-basics.md)
- `Factory` 남용을 리뷰에서 자르는 방법: [Factory Misnaming Checklist](./factory-misnaming-checklist.md)
- `Selector`/`Resolver`/`Registry`를 더 촘촘히 가르는 표: [Map-backed 클래스 네이밍 체크리스트](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
- 정적 팩토리와 패턴 factory까지 함께 정리: [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)

## 한 줄 정리

큰 그림은 단순하다. 생성 책임이면 `Factory`, 그 전 단계의 해석/선택 책임이면 `Resolver`/`Selector`를 먼저 붙인다.
