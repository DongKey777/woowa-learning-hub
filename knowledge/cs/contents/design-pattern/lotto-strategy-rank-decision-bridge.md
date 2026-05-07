---
schema_version: 3
title: 'lotto 당첨 등수 결정 로직에서 Strategy 패턴이 어울리는 이유'
concept_id: design-pattern/lotto-strategy-rank-decision-bridge
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
- enum-vs-strategy
- rank-decision
- if-cascade-smell
aliases:
- lotto 등수 결정
- Rank enum
- 로또 당첨 Strategy
- 로또 등수 분기 if
- LottoRank 결정 로직
intents:
- mission_bridge
- comparison
prerequisites:
- design-pattern/strategy-pattern-basics
linked_paths:
- contents/design-pattern/strategy-pattern-basics.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
- contents/design-pattern/strategy-explosion-smell.md
forbidden_neighbors:
- contents/design-pattern/strategy-explosion-smell.md
confusable_with:
- design-pattern/strategy-pattern-basics
- design-pattern/strategy-vs-state-vs-policy-object
- design-pattern/strategy-explosion-smell
expected_queries:
- 로또 등수 결정에 if 6개를 쓰는 게 맞아 enum이 맞아?
- LottoRank를 enum으로 둘지 Strategy로 둘지 어떻게 골라?
- 일치 개수랑 보너스 매칭 분기를 깔끔하게 하려면 어떻게?
- 로또 당첨 결정 로직이 길어지는데 패턴이 필요해?
contextual_chunk_prefix: |
  이 문서는 lotto 미션의 당첨 등수 결정 로직에서 enum, Strategy, 단순 분기
  중 무엇이 자연스러운지 판단하는 mission_bridge다. LottoRank, 일치 개수와
  보너스 매칭, if-else 분기 냄새, Strategy 패턴 도입 여부 같은 질의를
  과한 패턴 도입 방지와 도메인 규칙 모델링 관점으로 연결한다.
---

# lotto 당첨 등수 결정 로직에서 Strategy 패턴이 어울리는 이유

> 한 줄 요약: 로또 등수 결정은 *(일치 개수, 보너스 매칭) → 등수* 매핑이고 *분기가 6개*다. enum이 *데이터*를 표현하고 Strategy가 *분기 알고리즘*을 표현 — lotto는 enum + 정적 매칭 메소드 조합이 가장 자연스럽고, *Strategy를 도입할 만큼 행동이 다양하지는 않다*. Strategy는 *수익률 계산 정책 같은 변동 큰 분기*에 더 어울린다.

**난이도: 🟢 Beginner**

**미션 컨텍스트**: lotto (Woowa Java 트랙) — 결과 산출 단계

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "등수 결정 if문이 길어지는데 Strategy를 써야 하나요?" | `matchCount`, `bonusMatched`로 1등~미당첨을 분기하는 lotto 결과 코드 | 행동 알고리즘 교체인지, 닫힌 등수표 매핑인지 먼저 구분한다 |
| "`Rank` enum이랑 Strategy 중 뭐가 맞는지 모르겠어요" | 등수/상금/보너스 여부가 닫힌 규칙인데 패턴 이름부터 고르는 상황 | lotto 등수는 enum 데이터와 정적 매칭 메소드가 보통 더 자연스럽다 |
| "패턴을 넣으면 if문이 줄어드니까 좋은 거 아닌가요?" | 작은 닫힌 분기를 전략 클래스로 과하게 쪼개려는 설계 | 분기 제거보다 변경 축과 확장 가능성이 실제로 있는지 먼저 본다 |

관련 문서:

- [Strategy 패턴 기초](./strategy-pattern-basics.md) — 일반 개념
- [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md) — 비슷한 패턴 비교

## 미션의 어디에 등수 결정 분기가 등장하는가

당첨 결정에는 두 입력이 있다:

- *일치한 번호 개수* (0~6)
- *보너스 번호 일치 여부* (true/false)

규칙은 다음과 같다:

| 일치 | 보너스 | 등수 |
| ---- | ------ | ---- |
| 6    | -      | 1등  |
| 5    | true   | 2등  |
| 5    | false  | 3등  |
| 4    | -      | 4등  |
| 3    | -      | 5등  |
| ≤ 2  | -      | 미당첨 |

학습자가 흔히 *if-else*로 작성한다:

```java
public Rank decide(int matchCount, boolean bonus) {
    if (matchCount == 6) return Rank.FIRST;
    if (matchCount == 5 && bonus) return Rank.SECOND;
    if (matchCount == 5) return Rank.THIRD;
    if (matchCount == 4) return Rank.FOURTH;
    if (matchCount == 3) return Rank.FIFTH;
    return Rank.NONE;
}
```

이때 멘토 코멘트는 *"분기가 늘어나면 어떻게 할 거예요?"* — 여기서 학습자는 Strategy를 떠올린다. 하지만 이 분기에 Strategy는 *과한 도구*다.

## 왜 enum + 정적 매칭이 더 맞는가

### enum이 데이터로 표현하면 분기가 사라진다

```java
public enum Rank {
    FIRST(6, false, 2_000_000_000),
    SECOND(5, true,    30_000_000),
    THIRD (5, false,    1_500_000),
    FOURTH(4, false,       50_000),
    FIFTH (3, false,        5_000),
    NONE  (0, false,            0);

    private final int matchCount;
    private final boolean bonusRequired;
    private final long prize;

    Rank(int matchCount, boolean bonusRequired, long prize) { ... }

    public static Rank of(int matchCount, boolean bonus) {
        return Arrays.stream(values())
            .filter(r -> r.matches(matchCount, bonus))
            .findFirst()
            .orElse(NONE);
    }

    private boolean matches(int matchCount, boolean bonus) {
        if (this.matchCount != matchCount) return false;
        if (this.matchCount == 5) return this.bonusRequired == bonus;  // 2등 vs 3등
        return true;
    }
}
```

각 등수가 *자기 매칭 규칙*을 안다. *추가 등수*는 enum 상수 하나 추가로 끝.

### Strategy는 행동이 진짜 다양할 때

Strategy는 *같은 인터페이스에 다른 알고리즘*이 여럿일 때 빛난다. 로또 등수 결정은 *모두 같은 알고리즘 (matchCount + bonus 비교)*이고 *데이터만 다르다*. 같은 알고리즘에 데이터만 다르면 *enum이 표현하기에 충분하다*.

```java
// 과한 Strategy
public interface RankDecider { Optional<Rank> decide(int m, boolean b); }
class FirstRankDecider implements RankDecider { ... }
class SecondRankDecider implements RankDecider { ... }
// ... 6개 클래스
class CompositeRankDecider {
    private final List<RankDecider> deciders;
}
```

이 구조는 *6개의 클래스 + 1개의 Composite + 인터페이스 하나*가 되어 *enum 한 개*보다 비싸다. *분기 6개가 변할 가능성이 작은데* 추상화 비용이 6배다.

## Strategy가 진짜 어울리는 lotto 분기

### 분기 후보 — 수익률 계산 정책

```java
public interface ProfitPolicy {
    double calculate(long totalPrize, long spent);
}

class RatioProfitPolicy implements ProfitPolicy { ... }      // 수익률 = 당첨금 / 구입금
class NetProfitPolicy implements ProfitPolicy { ... }        // 수익 = 당첨금 - 구입금
class TaxAdjustedProfitPolicy implements ProfitPolicy { ... } // 세금 차감
```

여기는 *알고리즘 자체*가 다르다. 수익률 vs 절대값 vs 세후. 새 정책이 *언제 추가될지 모르고*, *런타임에 정책을 갈아끼울* 수도 있다. Strategy의 가정과 정확히 맞다.

### 분기 후보 — 자동/수동 번호 생성

```java
public interface LottoNumberGenerator {
    Lotto generate();
}

class RandomLottoGenerator implements LottoNumberGenerator { ... }
class ManualLottoGenerator implements LottoNumberGenerator {
    private final List<Integer> numbers;
}
class TestFixedLottoGenerator implements LottoNumberGenerator { ... }  // 테스트
```

여기도 *알고리즘이 다르고*, *테스트 더블이 자연스럽다*. Strategy의 가치가 분명하다.

## 자가 점검

- [ ] 분기가 *데이터 매핑*인가, *알고리즘 분기*인가?
- [ ] 분기 가짓수가 *변할 가능성*이 있는가? 적으면 enum, 많으면 Strategy.
- [ ] Strategy를 도입했다면 *런타임 교체*나 *테스트 더블*이 진짜 필요한가?
- [ ] enum의 정적 매칭 메소드가 *분기 6개를 한 줄씩*으로 줄여줬는가?
- [ ] 등수에 *액션*이 붙었나, *데이터*만 있나? 액션이면 Strategy 검토.

## 다음 문서

- 더 큰 그림: [Strategy 패턴 기초](./strategy-pattern-basics.md)
- 비슷한 패턴 분기: [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
- Strategy 남용 신호: [Strategy Explosion Smell](./strategy-explosion-smell.md)
