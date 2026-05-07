---
schema_version: 3
title: Saturating Arithmetic Clamping and Domain Contracts
concept_id: language/saturating-arithmetic-clamping-domain-contracts
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/lotto
- missions/payment
review_feedback_tags:
- numeric-boundary
- overflow
- domain-contract
aliases:
- Saturating Arithmetic Clamping and Domain Contracts
- saturating arithmetic clamp fail-fast policy
- numeric overflow domain contract
- retry backoff clamp quota invariant
- clamped value vs fail fast arithmetic
- 자바 saturating arithmetic clamp 정책
symptoms:
- overflow를 피하려고 무조건 min max clamp를 적용해 재고, 잔액, quota 같은 core invariant 위반을 조용히 숨겨
- UI progress나 retry backoff처럼 clamp가 자연스러운 곳과 정산 금액이나 권한 카운터처럼 fail-fast가 필요한 곳을 구분하지 못해
- saturating arithmetic을 overflow workaround로만 적용하고 어디서 saturate하고 어디서 exception을 낼지 domain contract로 문서화하지 않아
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- language/integer-overflow-exact-arithmetic-unit-conversion-pitfalls
- language/biginteger-unsigned-parsing-boundaries
- language/value-object-invariants-canonicalization-boundary-design
next_docs:
- language/parser-overflow-boundaries-parseint-parselong-tointexact
- language/executor-sizing-queue-rejection-policy
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
linked_paths:
- contents/language/java/integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md
- contents/language/java/biginteger-unsigned-parsing-boundaries.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
- contents/language/java/executor-sizing-queue-rejection-policy.md
confusable_with:
- language/integer-overflow-exact-arithmetic-unit-conversion-pitfalls
- language/parser-overflow-boundaries-parseint-parselong-tointexact
- language/biginteger-unsigned-parsing-boundaries
forbidden_neighbors: []
expected_queries:
- saturating arithmetic와 clamp는 fail-fast arithmetic과 어떤 domain contract 차이가 있어?
- retry backoff는 max cap으로 clamp해도 자연스럽지만 재고나 잔액 clamp는 왜 bug를 숨길 수 있어?
- overflow 방지로 min max clamp를 적용하기 전에 어디서 saturate하고 어디서 예외를 낼지 어떻게 정해?
- quota counter metrics bucket UI progress와 core business invariant에서 clamp 정책이 왜 달라질 수 있어?
- numeric overflow policy를 value object invariant와 validation boundary에 어떻게 문서화해?
contextual_chunk_prefix: |
  이 문서는 saturating arithmetic과 clamping을 retry backoff, metrics, quota, inventory, balance domain contract 관점에서 fail-fast와 비교하는 advanced playbook이다.
  saturating arithmetic, clamp, numeric overflow, fail-fast, domain contract 질문이 본 문서에 매핑된다.
---
# Saturating Arithmetic, Clamping, and Domain Contracts

> 한 줄 요약: overflow를 막기 위해 값을 min/max로 clamp하는 saturating arithmetic는 편리해 보이지만, 많은 backend 도메인에선 bug를 숨길 수 있다. 어디서 saturate할지와 어디서 fail-fast할지를 안 나누면 재고, quota, retry, backoff, metrics가 조용히 틀어진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)
> - [BigInteger, Unsigned Parsing, and Numeric Boundary Semantics](./biginteger-unsigned-parsing-boundaries.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)

> retrieval-anchor-keywords: saturating arithmetic, clamp, clamped value, fail fast arithmetic, numeric overflow policy, retry backoff clamp, quota max cap, counter saturation, domain contract, arithmetic policy

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

saturating arithmetic는 범위를 넘는 값을 예외 대신 경계값으로 눌러 버린다.

예:

- 너무 크면 `MAX_VALUE`
- 너무 작으면 `MIN_VALUE`
- quota는 0 미만으로 안 내려가게 clamp

문제는 이 정책이 domain contract와 맞지 않으면  
오류를 복구하는 게 아니라 숨기게 된다는 점이다.

## 깊이 들어가기

### 1. fail-fast와 saturate는 다른 철학이다

- fail-fast: 계약 위반을 즉시 드러낸다
- saturate: 값 범위를 강제로 안전 영역에 눌러 담는다

어느 쪽이 맞는지는 수학보다 도메인 의미가 결정한다.

### 2. UI/telemetry와 core business logic는 정책이 다를 수 있다

clamp가 잘 맞는 경우:

- progress bar 표시
- retry delay upper cap
- metrics bucket boundary

clamp가 위험한 경우:

- 재고 수량
- 정산 금액
- quota 청구 기준
- 권한/제한 카운터

즉 saturating arithmetic는 표현 계층엔 맞고 core invariant엔 위험할 수 있다.

### 3. backoff는 saturation이 합리적일 수 있다

retry backoff는 보통 upper bound를 두는 것이 자연스럽다.

- 100ms
- 200ms
- 400ms
- ...
- max 30s

이 경우는 saturate가 의도된 정책이다.  
하지만 왜 clamp하는지 문서화되지 않으면 그냥 overflow workaround처럼 보일 수 있다.

### 4. 재고/잔액/청구는 saturation이 bug를 숨길 수 있다

예를 들어 잔액이 음수가 되면 안 된다고 해서 0으로 clamp하면,  
실제로는 중복 차감이나 순서 역전 버그를 숨기는 결과가 된다.

이런 곳은 보통:

- atomic SQL
- exact arithmetic
- invariant validation

이 먼저다.

### 5. saturating policy도 값 객체로 잠그는 편이 좋다

clamp가 맞는 도메인이라면 helper util보다 value object나 명시적 policy 이름이 낫다.

- `BackoffMillis.nextCapped()`
- `TokenBucketLevel.saturatedAdd()`

이렇게 해야 "이 clamp가 의도된 것인지 임시 땜질인지"가 드러난다.

## 실전 시나리오

### 시나리오 1: retry delay가 overflow 대신 max delay에 붙는다

backoff upper cap은 합리적이다.  
다만 cap 도달이 정상인지 이상 징후인지 metric으로 남기는 편이 좋다.

### 시나리오 2: quota 잔량이 0으로 clamp되어 초과 사용이 숨는다

고객은 더 썼는데 시스템은 그냥 0으로만 보인다.  
청구나 제한 enforcement 버그가 숨겨질 수 있다.

### 시나리오 3: UI용 표시 clamp를 domain 계산에도 재사용한다

표시 로직은 괜찮았지만 business logic까지 같은 util을 써서 correctness가 흔들린다.

## 코드로 보기

### 1. 명시적 saturation helper 감각

```java
long capped = Math.min(candidate, MAX_DELAY_MILLIS);
```

### 2. fail-fast가 더 맞는 경우

```java
long exact = Math.addExact(current, delta);
if (exact < 0) {
    throw new IllegalStateException("negative inventory");
}
```

### 3. policy 이름으로 드러내기

```java
public record BackoffMillis(long value) {
    public BackoffMillis nextCapped(long max) {
        long doubled = value > max / 2 ? max : value * 2;
        return new BackoffMillis(Math.min(doubled, max));
    }
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| fail-fast arithmetic | invariant 위반을 빨리 드러낸다 | 예외 처리와 복구 설계가 필요하다 |
| saturating arithmetic | 상한/하한 정책을 부드럽게 적용할 수 있다 | 잘못 쓰면 버그를 조용히 숨긴다 |
| value object로 정책 고정 | clamp 의도를 명확히 드러낸다 | 타입과 메서드 설계가 늘어난다 |

핵심은 saturation을 overflow workaround가 아니라 domain policy로 다루는 것이다.

## 꼬리질문

> Q: saturating arithmetic는 언제 맞나요?
> 핵심: backoff cap, UI display bound, telemetry bucket처럼 clamp가 의도된 경우에 더 맞다.

> Q: 언제 위험한가요?
> 핵심: 재고, 잔액, 청구처럼 invariant 위반을 숨기면 안 되는 core business logic에서 위험하다.

> Q: `Math.*Exact`와 어떻게 다르나요?
> 핵심: exact는 위반을 드러내고, saturate는 경계값으로 눌러 담는다.

## 한 줄 정리

saturating arithmetic는 계산 실수 방지책이 아니라 clamp policy이므로, fail-fast가 맞는 곳과 의도적으로 saturate할 곳을 명확히 나눠야 한다.
