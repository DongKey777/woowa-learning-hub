---
schema_version: 3
title: '전략 폭발 냄새: 전략 패턴이 많아질수록 의심해야 하는 것'
concept_id: design-pattern/strategy-explosion-smell
canonical: false
category: design-pattern
difficulty: advanced
doc_role: symptom_router
level: advanced
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
  - strategy-overuse
  - policy-object-vs-strategy
  - template-vs-strategy
aliases:
  - strategy explosion
  - strategy explosion smell
  - 전략 폭발
  - 전략 클래스 폭발
  - strategy overuse
  - too many strategy classes
  - one class per case smell
  - combinatorial class explosion
  - enum to class smell
  - if else moved into classes
  - policy matrix
  - golden hammer strategy
  - strategy collapse checklist
  - when not to use strategy
  - config table vs strategy
  - lambda vs strategy
  - simple branching vs strategy
  - decision table refactoring
  - rule table
  - strategy to policy object
symptoms:
  - 전략 클래스를 계속 추가하는데 코드가 더 단순해지지 않아
  - if 문을 없앴는데 클래스만 늘고 분기 기준은 그대로 남아 있어
  - 할인이나 결제 규칙마다 구현체를 만들다 보니 이름이 조합 설명서가 됐어
intents:
  - symptom
  - design
  - troubleshooting
prerequisites:
  - design-pattern/strategy-pattern-basics
  - design-pattern/composition-over-inheritance-basics
next_docs:
  - design-pattern/policy-object-pattern
  - design-pattern/strategy-vs-state-vs-policy-object
  - design-pattern/template-hook-smells
linked_paths:
  - contents/design-pattern/strategy-pattern-basics.md
  - contents/design-pattern/strategy-vs-function-chooser.md
  - contents/design-pattern/strategy-vs-state-vs-policy-object.md
  - contents/design-pattern/policy-object-pattern.md
  - contents/design-pattern/specification-pattern.md
  - contents/design-pattern/template-hook-smells.md
  - contents/design-pattern/composition-over-inheritance-practical.md
  - contents/design-pattern/god-object-spaghetti-golden-hammer.md
confusable_with:
  - design-pattern/strategy-pattern-basics
  - design-pattern/strategy-vs-function-chooser
  - design-pattern/strategy-vs-state-vs-policy-object
forbidden_neighbors:
  - contents/design-pattern/strategy-pattern.md
expected_queries:
  - 전략 패턴을 적용할수록 클래스만 늘어나는데 이게 정상인지 판단하고 싶어
  - 구현체마다 경우의 수 이름이 붙기 시작했을 때 전략 대신 뭘 봐야 해?
  - if-else를 전략으로 옮겼는데 조합 수가 폭발하는 구조를 어떻게 줄여?
  - 결제 정책마다 전략 클래스를 만들고 있는데 policy object나 specification으로 바꿔야 할 신호가 뭐야?
  - lambda나 설정 테이블로 내려야 하는데 계속 전략으로 풀고 있는지 점검하는 기준이 필요해
contextual_chunk_prefix: |
  이 문서는 전략 패턴을 도입했는데 구현체 수만 늘고 분기 기준은 그대로 남아
  있어서 설계가 더 어려워졌다고 느끼는 학습자를 위한 symptom_router다. 할인,
  결제, 알림 규칙처럼 경우의 수마다 전략 클래스를 만들다가 이름이 조합 설명이
  되고, if else가 클래스 파일로 흩어졌을 뿐이라는 느낌, policy object나
  specification, config table로 다시 축을 나눠야 하는지 묻는 검색에 매핑된다.
---
# 전략 폭발 냄새: 전략 패턴이 많아질수록 의심해야 하는 것

> 한 줄 요약: 전략 패턴이 너무 많이 늘어날 때는 "유연해졌다"가 아니라 "변화 축을 잘못 쪼갰다"는 신호일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [전략 패턴](./strategy-pattern.md)
> - [Strategy vs Function: lambda로 충분한가, 전략 타입이 필요한가](./strategy-vs-function-chooser.md)
> - [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
> - [Policy Object Pattern: 도메인 결정을 객체로 만든다](./policy-object-pattern.md)
> - [Specification Pattern: 조건식을 조합 가능한 도메인 규칙으로 만들기](./specification-pattern.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [안티 패턴](./anti-pattern.md)
> - [God Object / Spaghetti / Golden Hammer](./god-object-spaghetti-golden-hammer.md)
> - [Template Hook Smells](./template-hook-smells.md)

retrieval-anchor-keywords: strategy explosion, strategy explosion smell, 전략 폭발, 전략 클래스 폭발, strategy overuse, too many strategy classes, one class per case smell, combinatorial class explosion, enum to class smell, if else moved into classes, policy matrix, golden hammer strategy, strategy collapse checklist, when not to use strategy, config table vs strategy, lambda vs strategy, simple branching vs strategy, decision table refactoring, rule table, strategy to policy object

---

## 핵심 개념

전략 폭발(Strategy Explosion)은 **전략 클래스를 늘려서 문제를 해결하려다 오히려 클래스 수와 조합 수가 폭증하는 현상**이다.  
전략 패턴 자체는 좋은 도구지만, 변화 축이 여러 개일 때는 클래스 하나가 1:1로 대응되지 않는다.

backend에서 자주 보이는 냄새는 이런 형태다.

- `PaymentStrategy`, `PaymentStrategyV2`, `PaymentStrategyForMobile`
- `DiscountStrategy`, `DiscountStrategyForVip`, `DiscountStrategyForCoupon`
- 팩토리가 전략을 너무 많이 조립한다
- 조건문을 클래스 폭발로 옮겨 놓았다

## 냄새-first 분기

- 거대한 서비스 하나가 조건과 외부 호출까지 모두 끌어안고 있다면 [God Object / Spaghetti / Golden Hammer](./god-object-spaghetti-golden-hammer.md)를 먼저 본다.
- 전략으로 쪼갰지만 추상 상위 클래스와 `before/after` hook가 다시 늘어나면 [Template Hook Smells](./template-hook-smells.md)를 같이 본다.
- `VipMobileWeekendDiscountStrategy`처럼 이름이 조건 조합 자체를 설명하기 시작하면 이 문서가 기준점이다.

---

## 깊이 들어가기

### 1. 전략이 늘어나는 이유는 보통 축이 여러 개이기 때문이다

문제가 한 축으로만 바뀌면 전략 패턴이 잘 맞는다.
하지만 현실의 backend는 대개 두세 개 축이 동시에 바뀐다.

- 결제 수단
- 채널
- 사용자 등급
- 지역
- 프로모션 여부

이때 축을 분리하지 않고 전략 하나씩 늘리면 조합이 폭발한다.

### 2. 전략 폭발의 신호

- 전략 클래스가 enum 값보다 많다
- 전략 이름에 조건이 붙는다
- 팩토리에서 `if` 문이 다시 커진다
- 테스트가 전략 개수만큼 늘어난다
- 새 요구사항이 오면 전략 생성부터 고민한다

이 상태는 "객체지향화"가 아니라 **분기 이동**일 가능성이 크다.

### 3. 대안은 전략이 아니라 분해다

전략 폭발의 해법은 전략을 더 만드는 것이 아니라, 변화 축을 다시 나누는 것이다.

- 공통 규칙은 Specification으로 뽑는다
- 상태 전이는 State로 바꾼다
- 공통 파이프라인은 Template Method나 Chain으로 둔다
- 독립 축은 작은 value object로 분리한다

### 4. 전략을 접고 더 단순한 구조로 내려야 하는 순간

전략 패턴을 없애는 기준은 "객체지향을 포기한다"가 아니라, **문제 크기에 맞는 표현으로 다시 축소한다**는 데 있다.

#### Compact checklist

- 새 구현체를 추가할 때 클래스보다 설정값 한 줄만 늘어난다면 `config table`이 먼저다.
- 구현 차이가 메서드 본문 2~3줄짜리 계산식이나 매핑이라면 `lambda`/함수 맵이 먼저다.
- 선택지가 2~3개뿐이고 호출 지점도 하나라면 단순 `if`/`switch`가 더 읽기 쉽다.
- 호출자가 전략 타입을 몰라도 되고, 키 기반 lookup만 있으면 `registry + data row`로 충분할 수 있다.
- 테스트가 "각 전략 클래스"보다 "입력 조합과 기대값 표"에 가까워지면 decision table 쪽이 맞다.
- 전략 이름보다 `grade`, `channel`, `weekend` 같은 축 이름이 더 중요해지면 Policy/Specification 조합을 검토한다.

#### 무엇으로 접을지 빠르게 고르기

| 축소 후보 | 이런 신호가 보이면 | 예시 |
|---|---|---|
| Config table | 차이가 상수, 비율, 임계값뿐이다 | 등급별 할인율, 채널별 수수료 |
| Lambda / 함수 맵 | 계산식은 짧지만 런타임 선택은 필요하다 | 배송 타입별 fee 계산, 포맷터 선택 |
| Simple branching | 분기가 작고 지역적이며 거의 안 바뀐다 | `isTestUser` 예외, 2가지 화면 분기 |
| Policy / Specification | 조합 규칙과 판정 이유가 중요하다 | 환불 가능 여부, 승인 규정, 프로모션 eligibility |

작게 외우면 다음 순서로 본다.

1. 값 차이만 있나? 그러면 config table.
2. 짧은 동작 차이만 있나? 그러면 lambda.
3. 분기가 매우 적고 지역적인가? 그러면 simple branching.
4. 판정 이유와 조합 규칙이 중요한가? 그러면 Policy/Specification.
5. 그래도 알고리즘 자체가 독립적으로 길고 교체 가능한가? 그때 Strategy.

---

## 실전 시나리오

### 시나리오 1: 할인 정책

처음에는 `VipDiscountStrategy`, `NewbieDiscountStrategy` 정도로 끝난다.  
그런데 어느 순간 `VipMobileWeekendDiscountStrategy`가 생기면 이미 구조가 위험하다.

### 시나리오 2: 알림 발송

이메일, SMS, 푸시를 전략으로 만들 수 있지만, 채널과 템플릿과 재시도 정책까지 분기되면 전략만으로는 과하다.

### 시나리오 3: 결제 라우팅

PG, 간편결제, 포인트, 지역 규정이 섞이면 전략 조합이 아니라 정책 모델이 필요하다.

---

## 코드로 보기

### Before: 전략 클래스가 축마다 늘어난다

```java
public interface DiscountStrategy {
    int discount(int amount);
}

public class VipMobileWeekendDiscountStrategy implements DiscountStrategy {
    @Override
    public int discount(int amount) {
        return (int) (amount * 0.7);
    }
}
```

전략 이름만 봐도 "무엇이 바뀌는지"가 아닌 "모든 경우의 수"가 드러난다.

### After: 축을 분리한다

```java
public record DiscountContext(MemberGrade grade, Channel channel, boolean weekend) {}

public interface DiscountRule {
    boolean matches(DiscountContext context);
    int discount(int amount, DiscountContext context);
}

public class VipRule implements DiscountRule {
    @Override
    public boolean matches(DiscountContext context) {
        return context.grade() == MemberGrade.VIP;
    }

    @Override
    public int discount(int amount, DiscountContext context) {
        return (int) (amount * 0.8);
    }
}
```

### 조합 접근

```java
public class DiscountPolicy {
    private final List<DiscountRule> rules;

    public int calculate(int amount, DiscountContext context) {
        return rules.stream()
            .filter(rule -> rule.matches(context))
            .findFirst()
            .map(rule -> rule.discount(amount, context))
            .orElse(amount);
    }
}
```

이 구조는 "전략 수를 줄였다"가 아니라 **변화 축을 정책과 규칙으로 다시 모델링했다**는 점이 중요하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 전략 클래스 다수 | 교체는 쉽다 | 클래스가 급증한다 | 진짜로 독립적인 알고리즘일 때 |
| Config table | 변경을 데이터처럼 다룬다 | 행 의미가 흐려지면 문맥이 약해진다 | 차이가 상수/매핑일 때 |
| Lambda / 함수 맵 | 구현 수를 줄이고 선택은 유지한다 | 공통 생명주기와 상태가 커지면 약하다 | 계산식이 짧고 stateless일 때 |
| 단순 분기 | 가장 직접적이고 읽기 쉽다 | 축이 늘면 금방 다시 비대해진다 | 분기가 적고 지역적일 때 |
| 전략 + 팩토리 | 생성은 통제된다 | 팩토리가 비대해질 수 있다 | 전략 수가 적당할 때 |
| 규칙/명세 조합 | 축을 다시 나눌 수 있다 | 설계가 조금 더 추상적이다 | 조건이 합성될 때 |
| State/Chain/Template 전환 | 구조가 더 명확해진다 | 개념 전환이 필요하다 | 전략이 아니라 흐름 문제일 때 |

판단 기준은 다음과 같다.

- 전략이 "선택지"라면 유지한다
- 전략이 "경우의 수"가 되면 의심한다
- 이름에 조건이 붙기 시작하면 축 분해를 다시 한다
- 전략을 제거해도 데이터 표와 짧은 함수로 읽힌다면 과한 추상화였을 가능성이 높다

---

## 꼬리질문

> Q: 전략 클래스가 많아지면 왜 문제가 되나요?
> 의도: 클래스 수 자체보다 변화 축의 설계가 중요하다는 점을 아는지 확인한다.
> 핵심: 조합 수가 늘어 유지보수와 테스트 비용이 커진다.

> Q: 전략 폭발과 if-else 스파게티는 같은 문제인가요?
> 의도: 구조만 바뀌고 본질은 안 바뀌는 경우를 구분하는지 확인한다.
> 핵심: 형태만 다를 뿐, 둘 다 변화 축을 잘못 잡았을 가능성이 높다.

> Q: 전략을 언제 포기해야 하나요?
> 의도: 패턴 과사용을 경계하는지 확인한다.
> 핵심: 조건 조합이 중심이면 Specification이나 다른 분해가 더 낫다.

## 한 줄 정리

전략 폭발은 전략 패턴이 실패했다는 뜻이 아니라, 문제의 변화 축이 여러 개인데도 전략 하나로 억지로 풀고 있다는 경고다.
