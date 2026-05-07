---
schema_version: 3
title: Template Method Hook Explosion Mini Smell Card
concept_id: language/template-method-hook-explosion-mini-smell-card
canonical: true
category: language
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 90
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- template-method
- strategy
- oop-design
aliases:
- Template Method Hook Mini Smell Card
- hook explosion Java
- beforeX afterX shouldX smell
- template method hooks keep growing
- hook vs strategy beginner
- 템플릿 메소드 hook smell
symptoms:
- beforeX afterX shouldX 같은 hook 이름이 계속 늘어나는데 상속 확장 성공으로만 보고 규칙이 갈라지는 초기 smell을 놓쳐
- hook override 순서, super 호출 여부, cleanup 짝을 하위 클래스가 외워야 하는 구조가 되어도 template method를 계속 밀어붙여
- 선택적 덧붙임이 아니라 결제 정책이나 알림 정책처럼 핵심 규칙 자체가 달라졌는데 strategy나 composition 분리를 검토하지 않아
intents:
- troubleshooting
- design
- comparison
prerequisites:
- language/template-method-vs-strategy-quick-check-card
- language/java-abstract-class-vs-interface-basics
- language/object-oriented-core-principles
next_docs:
- design-pattern/template-method-basics
- design-pattern/template-hook-smells
- design-pattern/composition-over-inheritance-basics
linked_paths:
- contents/language/java/template-method-vs-strategy-quick-check-card.md
- contents/language/java/java-abstract-class-vs-interface-basics.md
- contents/language/java/object-oriented-core-principles.md
- contents/design-pattern/template-method-basics.md
- contents/design-pattern/template-hook-smells.md
- contents/design-pattern/composition-over-inheritance-basics.md
confusable_with:
- language/template-method-vs-strategy-quick-check-card
- design-pattern/template-method-basics
- design-pattern/template-hook-smells
forbidden_neighbors: []
expected_queries:
- Template Method에서 beforeX afterX shouldX hook이 계속 늘어나면 왜 hook explosion smell로 봐야 해?
- hook가 작은 선택적 확장인지 규칙 자체가 갈라지는 신호인지 어떻게 구분해?
- 템플릿 메소드 hook을 더 추가하지 말고 strategy나 composition으로 빼야 하는 기준은 뭐야?
- 하위 클래스가 override 순서와 super 호출 cleanup을 외워야 하면 왜 위험한 설계야?
- hook explosion beginner smell을 PaymentTemplate 예제로 설명해줘
contextual_chunk_prefix: |
  이 문서는 Template Method에서 beforeX/afterX/shouldX hook이 계속 늘어나는 hook explosion smell을 strategy/composition 분리 신호로 라우팅하는 beginner symptom router다.
  template method hook, hook explosion, beforeX afterX shouldX, strategy, composition 질문이 본 문서에 매핑된다.
---
# `beforeX`/`afterX`/`shouldX`가 늘어날 때: Template Method Hook Mini Smell Card

> 한 줄 요약: 템플릿 메소드를 처음 배우는 사람이 `beforeX`, `afterX`, `shouldX` 같은 hook 이름이 계속 늘어나는 장면을 보면, "상속 확장 성공"보다 "규칙이 갈라지기 시작했다"는 초기 설계 냄새로 먼저 읽게 만드는 tiny beginner bridge다.

**난이도: 🟢 Beginner**

관련 문서:

- [Template Method vs Strategy Quick Check Card](./template-method-vs-strategy-quick-check-card.md) - 부모가 흐름을 쥐는지, 밖에서 구현을 갈아끼우는지 먼저 15초로 자를 때
- [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) - 상속/계약 큰 그림이 아직 먼저 필요할 때
- [객체지향 핵심 원리](./object-oriented-core-principles.md) - 상속이 왜 결합을 키우는지 큰 그림으로 다시 보고 싶을 때
- [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md) - `hook`와 `abstract step` 기본 구조를 먼저 다시 고정할 때
- [Template Hook Smells](../../design-pattern/template-hook-smells.md) - 이 카드 다음에 실제 분해 신호와 리팩터링 방향을 더 길게 볼 때
- [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md) - `hook`를 더 추가하는 대신 정책 객체나 helper로 빼는 감각을 익힐 때
- [language 카테고리 인덱스 - Java primer](../README.md#java-primer) - Java beginner 흐름으로 다시 돌아갈 때

retrieval-anchor-keywords: template method hook smell beginner, beforex afterx shouldx smell, hook explosion java, template method hooks keep growing, when hook is too much, hook vs strategy beginner, 템플릿 메소드 hook 많아질 때, beforex afterx shouldx 왜 불안한가, 처음 배우는데 hook 늘어나요, 헷갈려요 hook 더 추가해도 되나, 언제 strategy 로 빼나요, 상속 말고 조합으로 빼야 하나, what is hook explosion, basics template hook smell

## 한눈에 보기

작은 `hook` 1~2개는 흔하다.
예를 들어 "실행 전 로그 한 줄", "끝난 뒤 선택 알림" 정도는 템플릿 메소드와 잘 맞는다.

하지만 `beforeX`, `afterX`, `shouldX`가 계속 생기면 보통은 "확장 포인트가 많다"보다 **흐름 하나 안에 서로 다른 규칙을 억지로 우겨 넣고 있다**는 신호에 가깝다.

비유하면 템플릿 메소드는 고정된 체크리스트에 작은 메모 칸을 몇 개 여는 구조다.
메모 칸이 체크리스트 자체를 바꾸기 시작하면 이 비유는 더 이상 맞지 않고, 그때는 별도 정책 객체나 전략이 더 자연스럽다.

## 30초 체크표

| 보이는 장면 | 아직 괜찮은 편 | 냄새에 가깝다 |
|---|---|---|
| `hook` 개수 | `before()`나 `after()`처럼 1~2개 | `beforeValidate()`, `afterPersist()`, `shouldSkipNotify()`처럼 계속 늘어남 |
| 기본 구현 | 비워 둬도 전체 흐름 의미가 유지됨 | override하지 않으면 무슨 일이 일어나는지 읽기 어려움 |
| 하위 클래스 지식 | slot 이름만 알면 됨 | 호출 순서, `super` 호출 여부, 짝 맞는 cleanup까지 외워야 함 |
| 바뀌는 이유 | 작은 부가 동작 | 정책, 분기, 예외 규칙 자체가 달라짐 |
| 다음 선택 | hook 유지 가능 | 전략/조합/helper 분리 재검토 |

## 코드로 보는 신호

```java
abstract class PaymentTemplate {
    public final void pay() {
        beforeValidate();
        validate();
        beforeAuthorize();
        authorize();
        afterAuthorize();
        if (shouldSendReceipt()) {
            sendReceipt();
        }
        afterReceipt();
    }

    protected void beforeValidate() {}
    protected void beforeAuthorize() {}
    protected void afterAuthorize() {}
    protected boolean shouldSendReceipt() { return true; }
    protected void afterReceipt() {}

    protected abstract void validate();
    protected abstract void authorize();
}
```

처음엔 `afterAuthorize()` 하나였는데, 나중에 `beforeValidate()`, `shouldSendReceipt()`, `afterReceipt()`가 붙기 시작하면 "선택 빈칸 몇 개"를 넘어서 **결제 정책 여러 개를 상속 구조에 매달기 시작한 상태**로 읽는 편이 안전하다.

이 단계에서는 `ReceiptPolicy`, `AuthorizationPolicy` 같은 별도 객체로 분리할 여지가 있는지 먼저 의심해 본다.

## 왜 초기에 냄새라고 부르나

- 템플릿 메소드의 장점은 부모가 흐름을 단순하게 고정하는 데 있다.
- `hook`가 많아질수록 하위 클래스는 "빈칸 채우기"보다 "숨은 분기 해석"을 하게 된다.
- 그 결과 "이 클래스는 어디를 override해야 안전한가?"가 바로 읽히지 않는다.
- 특히 `shouldX`가 늘어나면 선택 규칙이 부모 안의 `if`로 모이기 쉬워서, 나중에는 전략 객체로 빼는 편이 테스트와 변경에 더 낫다.

여기서 핵심은 "`hook`가 3개면 무조건 나쁘다"가 아니다.
보통은 **작고 선택적인 확장인지**, 아니면 **규칙 세트를 갈아끼우고 싶은지**를 구분하는 early warning으로 쓰면 된다.

## 흔한 오해

- `beforeX`나 `afterX` 이름이 보인다고 항상 smell은 아니다. 프레임워크 lifecycle처럼 제한된 확장 포인트는 흔하다.
- 추상 클래스가 복잡해졌다고 무조건 전략으로 끝나는 것도 아니다. 때로는 helper object 하나로도 충분하다.
- `hook`가 많아 보여도 실제로는 임시 과도기일 수 있다. 다만 그 경우에도 "왜 아직 상속에 두는지" 설명이 바로 되어야 한다.
- 냄새는 버그 확정이 아니라 재검토 신호다. 이 카드는 리팩터링 규칙 전부를 설명하는 문서가 아니다.

## 다음 한 칸

- `hook`와 전략을 15초로 다시 자르고 싶다면 [Template Method vs Strategy Quick Check Card](./template-method-vs-strategy-quick-check-card.md)
- 템플릿 메소드 구조 자체를 다시 고정하고 싶다면 [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md)
- 왜 조합이 기본값처럼 자주 권장되는지 보고 싶다면 [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)
- 이 냄새 이후의 더 깊은 분해 기준을 보고 싶다면 [Template Hook Smells](../../design-pattern/template-hook-smells.md)

## 한 줄 정리

`beforeX`/`afterX`/`shouldX`가 계속 늘어난다면, "hook를 더 열까?"보다 "이미 다른 규칙을 상속에 묶고 있나?"를 먼저 묻는 것이 beginner에게 더 안전한 첫 판단이다.
