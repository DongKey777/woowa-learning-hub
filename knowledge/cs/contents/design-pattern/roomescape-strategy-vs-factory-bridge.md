---
schema_version: 3
title: 'roomescape에서 예약 검증/시간 슬롯 결정에 Strategy vs Factory 어떤 게 맞나'
concept_id: design-pattern/roomescape-strategy-vs-factory-bridge
canonical: false
category: design-pattern
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- strategy-vs-factory
- validation-rule-set
- runtime-behavior-vs-creation
aliases:
- roomescape Strategy
- roomescape Factory
- 룸이스케이프 검증 전략
- 예약 검증 Strategy
- ReservationTime 슬롯 Factory
intents:
- mission_bridge
- comparison
prerequisites:
- design-pattern/strategy-pattern-basics
linked_paths:
- contents/design-pattern/strategy-pattern-basics.md
- contents/design-pattern/bridge-strategy-vs-factory-runtime-selection.md
forbidden_neighbors:
- contents/design-pattern/factory-misnaming-checklist.md
expected_queries:
- 룸이스케이프 검증 로직에 Strategy 패턴이 어울려?
- 예약 검증 규칙을 분기할 때 Factory를 써?
- Strategy랑 Factory 중에 미션에서 뭐가 맞아?
- 시간 슬롯 결정에 어떤 패턴이 자연스러워?
---

# roomescape에서 예약 검증/시간 슬롯 결정에 Strategy vs Factory 어떤 게 맞나

> 한 줄 요약: *런타임 동작*을 바꾸려면 Strategy(예약 검증 규칙 set), *객체 생성*을 추상화하려면 Factory(시간 슬롯 인스턴스). roomescape 단계 4~5에서 자주 만나는 분기 — 둘은 다른 축이다.

**난이도: 🟢 Beginner**

**미션 컨텍스트**: spring-roomescape-admin (Woowa Spring 트랙)

관련 문서:

- [Strategy 패턴 기초](./strategy-pattern-basics.md) — 일반 개념
- [Strategy vs Factory Runtime Selection Bridge](./bridge-strategy-vs-factory-runtime-selection.md) — 두 패턴 분기

## 미션의 어디에 둘이 동시에 등장하는가

roomescape에서 패턴 도입을 고민하게 되는 두 지점:

1. **예약 검증 규칙** — "과거 시간 예약 금지", "동일 시간 중복 금지", "관리자 권한 확인" 같은 규칙이 늘어난다
2. **시간 슬롯 객체 생성** — 30분/60분/120분 타입에 따라 ReservationTime 인스턴스가 달라진다 (5단계 이후)

학습자가 흔히 "두 군데 다 Factory를 쓸까? 아니면 Strategy?"라고 질문한다. 답은 *서로 다른 패턴이 두 곳에 각각 맞다*.

## 두 패턴은 다른 *축*에 있다

### Strategy — *행동*을 바꾼다

검증 로직 예시:

```java
public interface ReservationValidator {
    void validate(ReservationRequest request);
}

class PastTimeValidator implements ReservationValidator { ... }
class DuplicateValidator implements ReservationValidator { ... }

@Service
public class ReservationService {
    private final List<ReservationValidator> validators;  // 주입된 set

    public Reservation create(ReservationRequest request) {
        validators.forEach(v -> v.validate(request));  // 동일 입력 → 다른 행동
        return reservationRepository.save(...);
    }
}
```

핵심은 *같은 인터페이스*에 *행동이 다른 구현체*가 여러 개라는 것. *어떤 검증기를 적용할지*는 외부 설정/조건에 따라 결정된다.

### Factory — *생성*을 추상화한다

```java
public class ReservationTimeFactory {
    public static ReservationTime create(LocalTime time, int durationMinutes) {
        if (durationMinutes == 30) return new ShortSlot(time);
        if (durationMinutes == 60) return new StandardSlot(time);
        return new LongSlot(time);
    }
}
```

핵심은 *호출자가 어떤 구체 타입을 쓸지 모르게* 한다는 것. 같은 메소드 호출이 *입력에 따라 다른 인스턴스*를 돌려준다.

## roomescape의 두 결정 포인트에 매핑하기

### 결정 1 — 예약 검증 → Strategy

이유:

- 검증 *행동*이 다양하다 (시간 검증, 중복 검증, 권한 검증)
- *모두 적용하거나 일부만 적용*하는 합성이 자연스럽다 (`List<ReservationValidator>`)
- 새 규칙 추가 시 *기존 코드 수정 없이* 새 구현체만 추가 (OCP)

미션 PR에서 자주 보이는 잘못된 모양:

```java
public Reservation create(ReservationRequest request) {
    if (request.date().isBefore(LocalDate.now())) throw ...;        // ❌ 분기 누적
    if (existsBy(request)) throw ...;                                // ❌
    if (!isAdmin(request.user())) throw ...;                         // ❌
    return reservationRepository.save(...);
}
```

이 if-덩어리는 *Strategy로 분리*하면 testable + extensible.

### 결정 2 — 시간 슬롯 인스턴스 결정 → Factory (또는 정적 팩토리)

이유:

- 호출자는 *"30분 슬롯이 필요"*라는 의도만 표현
- *어떤 클래스로 만들지*는 변경 가능 (예: ShortSlot이 record로 바뀌거나)
- 검증과 달리 *행동이 아니라 생성*만 다르다

다만 roomescape 4단계까지는 ReservationTime이 단일 클래스라서 *Factory를 도입할 만한 분기가 아직 없을 수도* 있다. *분기가 1개일 때 Factory를 미리 만드는 것은 over-engineering*.

## "둘 다 써야 하나?"라는 질문의 함정

### 함정 1 — Validator를 Factory가 만들도록 강요

```java
public class ValidatorFactory {
    public static List<ReservationValidator> create(ReservationType type) { ... }
}
```

Spring DI 컨테이너가 이미 Validator들을 빈으로 모아 *List<ReservationValidator>*로 주입해준다. *Factory는 DI 컨테이너의 일을 빼앗는 패턴*이다. 자세한 비교는 [Factory vs DI 컨테이너 와이어링](./factory-vs-di-container-wiring.md).

### 함정 2 — Strategy 하나만 있는데 추상 인터페이스 도입

```java
public interface ReservationValidator { void validate(...); }
public class TheOnlyValidator implements ReservationValidator { ... }
```

구현체가 *하나*뿐이면 인터페이스는 *나중에* 도입한다. YAGNI.

## 자가 점검

- [ ] *행동이 분기*되는가, *생성이 분기*되는가? (Strategy vs Factory의 갈림길)
- [ ] 구현체가 *둘 이상* 있는가? (있어야 추상화 가치)
- [ ] DI 컨테이너로 충분한 합성을 *Factory가 다시 짜고* 있지 않은가?
- [ ] Validator 추가 시 Service 코드를 *수정하지 않고* 새 빈만 추가하면 되는가?
- [ ] Factory의 분기 조건이 *런타임 입력*에 의존하는가? (정적이면 그냥 Bean 분리)

## 다음 문서

- 더 큰 그림: [Strategy 패턴 기초](./strategy-pattern-basics.md)
- 두 패턴 정확한 분기: [Strategy vs Factory Runtime Selection Bridge](./bridge-strategy-vs-factory-runtime-selection.md)
- 잘못된 Factory 명명을 찾는 체크: [Factory Misnaming Checklist](./factory-misnaming-checklist.md)
