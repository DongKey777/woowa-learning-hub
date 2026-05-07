---
schema_version: 3
title: Money Equality Policy Mini Drill
concept_id: language/money-equality-policy-mini-drill
canonical: true
category: language
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 91
mission_ids:
- missions/lotto
- missions/payment
review_feedback_tags:
- value-object
- bigdecimal
- equality
aliases:
- Money Equality Policy Mini Drill
- Money value object equality policy
- currency amount canonicalization
- BigDecimal Money HashSet HashMap key
- stripTrailingZeros money equality
- 자바 Money 값 객체 동등성
symptoms:
- BigDecimal을 raw key로 쓰며 10.0과 10.00의 scale 차이가 HashSet이나 HashMap key 동작에 영향을 주는 점을 놓쳐
- 금액만 같으면 같은 돈이라고 생각해 currency까지 포함한 Money equality policy를 설계하지 못해
- value object 안에서 canonicalization을 하지 않아 같은 도메인 금액이 Set과 Map에서 서로 다른 key처럼 흩어져
intents:
- drill
- design
- comparison
prerequisites:
- language/money-value-object-basics
- language/bigdecimal-1-0-vs-1-00-collections-mini-drill
- language/record-value-object-equality-basics
next_docs:
- language/value-object-invariants-canonicalization-boundary-design
- language/bigdecimal-hashmap-treemap-lookup-mini-drill
- language/record-bigdecimal-component-faq
linked_paths:
- contents/language/java/money-value-object-basics.md
- contents/language/java/bigdecimal-1-0-vs-1-00-collections-mini-drill.md
- contents/language/java/bigdecimal-hashmap-treemap-lookup-mini-drill.md
- contents/language/java/record-value-object-equality-basics.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
confusable_with:
- language/bigdecimal-1-0-vs-1-00-collections-mini-drill
- language/bigdecimal-hashmap-treemap-lookup-mini-drill
- language/record-value-object-equality-basics
forbidden_neighbors: []
expected_queries:
- Money value object에서 currency와 amount equality policy를 어떻게 잡아야 해?
- BigDecimal 10.0과 10.00을 Money로 감싸면 HashSet과 HashMap key가 어떻게 달라져?
- stripTrailingZeros를 Money 생성자에서 쓰는 이유와 scale 함정을 설명해줘
- USD 10과 KRW 10은 금액 숫자가 같아도 왜 다른 Money로 봐야 해?
- raw BigDecimal key 대신 Money value object를 쓰는 장점을 드릴로 연습하고 싶어
contextual_chunk_prefix: |
  이 문서는 Money value object의 equality policy를 currency와 normalized BigDecimal amount로 잡는 beginner drill이다.
  Money equality, BigDecimal scale, currency amount, HashSet HashMap key, canonicalization 질문이 본 문서에 매핑된다.
---
# Money Equality Policy Mini Drill

> 한 줄 요약: raw `BigDecimal` key는 scale 차이 때문에 `10.0`과 `10.00`을 다르게 볼 수 있지만, `Money` value object는 "통화 + 정규화된 금액" 정책으로 set/map 동작을 더 도메인답게 고정할 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: money equality policy mini drill basics, money equality policy mini drill beginner, money equality policy mini drill intro, java basics, beginner java, 처음 배우는데 money equality policy mini drill, money equality policy mini drill 입문, money equality policy mini drill 기초, what is money equality policy mini drill, how to money equality policy mini drill
> 관련 문서:
> - [Money Value Object Basics](./money-value-object-basics.md)
> - [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
> - [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)

> retrieval-anchor-keywords: money equality policy mini drill, money value object set map key beginner, currency plus amount equality, bigdecimal money equality difference, money hashset hashmap key, money canonicalization beginner, stripTrailingZeros money equality, java money value object equals hashcode, 자바 money 동등성 정책, 통화 금액 값 객체, bigdecimal money set map 차이

## 먼저 잡을 멘탈 모델

처음엔 이 2줄만 기억하면 된다.

- raw `BigDecimal`은 "숫자 표현"까지 equality에 끌고 들어온다
- `Money`는 "우리 도메인에서 같은 돈이 무엇인가"를 타입 안에 적어 둘 수 있다

즉 `BigDecimal("10.0")`와 `BigDecimal("10.00")`는 숫자로는 같아 보여도, 그대로 key로 쓰면 다른 key가 될 수 있다.

## 10초 비교표

| 비교 대상 | 같은 값으로 보는 기준 | `10.0` vs `10.00` |
|---|---|---|
| raw `BigDecimal` | `equals()` + scale | 다를 수 있다 |
| `Money("USD", ...)` | 통화 + 정규화된 금액 | 같게 만들 수 있다 |
| `Money("USD", ...)` vs `Money("KRW", ...)` | 통화까지 포함 | 항상 다르다 |

## 드릴 코드

```java
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

record Money(String currency, BigDecimal amount) {
    Money {
        currency = Objects.requireNonNull(currency).toUpperCase(Locale.ROOT);
        amount = Objects.requireNonNull(amount).stripTrailingZeros();
    }

    static Money of(String currency, String amountText) {
        return new Money(currency, new BigDecimal(amountText));
    }
}

Set<BigDecimal> raw = new HashSet<>();
raw.add(new BigDecimal("10.0"));
raw.add(new BigDecimal("10.00"));

Set<Money> moneySet = new HashSet<>();
moneySet.add(Money.of("usd", "10.0"));
moneySet.add(Money.of("USD", "10.00"));
moneySet.add(Money.of("KRW", "10.00"));

Map<Money, String> prices = new HashMap<>();
String prev1 = prices.put(Money.of("USD", "10.0"), "coffee");
String prev2 = prices.put(Money.of("USD", "10.00"), "coffee-updated");
String prev3 = prices.put(Money.of("KRW", "10.00"), "snack");

System.out.println(raw.size());
System.out.println(moneySet.size());
System.out.println(prev1);
System.out.println(prev2);
System.out.println(prev3);
System.out.println(prices.get(Money.of("USD", "10")));
System.out.println(prices.get(Money.of("KRW", "10")));
```

## 실행 전 워크시트

| 질문 | 내 답(실행 전) |
|---|---|
| `raw.size()` |  |
| `moneySet.size()` |  |
| `prev1` |  |
| `prev2` |  |
| `prev3` |  |
| `prices.get(Money.of("USD", "10"))` |  |
| `prices.get(Money.of("KRW", "10"))` |  |

## 정답

- `raw.size()` -> `2`
- `moneySet.size()` -> `2`
- `prev1` -> `null`
- `prev2` -> `"coffee"`
- `prev3` -> `null`
- `prices.get(Money.of("USD", "10"))` -> `"coffee-updated"`
- `prices.get(Money.of("KRW", "10"))` -> `"snack"`

## 왜 이렇게 되나

| 케이스 | 이유 |
|---|---|
| raw `BigDecimal` set | `10.0`과 `10.00`은 `equals()`가 `false`라 둘 다 남는다 |
| `Money.of("usd", "10.0")` vs `Money.of("USD", "10.00")` | 통화를 대문자로 맞추고 금액을 정규화해서 같은 key가 된다 |
| `Money.of("USD", "10.00")` vs `Money.of("KRW", "10.00")` | 금액이 같아도 통화가 다르니 다른 돈이다 |
| `HashMap<Money, ...>` 두 번째 `put` | 같은 `Money` key로 판단해서 기존 값을 덮어쓴다 |

핵심은 한 줄이다.

> raw `BigDecimal` equality는 도메인 정책이 아니라 라이브러리 규칙이고, `Money` equality는 우리 팀이 정한 "같은 돈" 규칙이다.

## 초보자 혼동 포인트

- `BigDecimal`이 정확한 숫자 타입이니 equality도 돈 의미에 맞을 거라고 생각하기 쉽다
- `Money`에 통화 필드만 추가하면 자동으로 정책이 생긴다고 오해하기 쉽다
- `Set` size와 `Map.put` 반환값을 같이 보지 않아 overwrite 순간을 놓치기 쉽다

안전한 습관:

- money key를 만들 때 "통화를 equality에 넣을지"를 먼저 적는다
- 금액 표현 차이를 같은 값으로 볼 거면 생성 시 정규화 위치를 한곳에 모은다
- `HashSet`과 `HashMap`에서 `size()`와 `put` 반환값을 같이 테스트한다

## 다음 읽기

- 입문 맥락: [Money Value Object Basics](./money-value-object-basics.md)
- raw `BigDecimal` 비교부터 다시: [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
- 조회 관점 확장: [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- 설계 관점 확장: [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)

## 한 줄 정리

raw `BigDecimal` key는 scale 차이 때문에 `10.0`과 `10.00`을 다르게 볼 수 있지만, `Money` value object는 "통화 + 정규화된 금액" 정책으로 set/map 동작을 더 도메인답게 고정할 수 있다.
