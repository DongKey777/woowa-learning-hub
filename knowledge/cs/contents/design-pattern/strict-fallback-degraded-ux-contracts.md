---
schema_version: 3
title: Strict Fallback Degraded UX Contracts
concept_id: design-pattern/strict-fallback-degraded-ux-contracts
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- degraded-ux-contract
- processing-pending-response
- retry-after-contract
aliases:
- strict fallback degraded ux contract
- degraded response contract
- processing state contract
- pending state response contract
- retry-after contract
- strict fallback user visible guarantees
- fallback breaker response
- honest eventual consistency ux
- stale success prevention
- bounded retry poll contract
symptoms:
- primary read와 fallback source가 모두 즉시 정답을 못 줄 때 stale 200 success처럼 보여 false completion을 만든다
- PROCESSING, PENDING, manual review, breaker-open을 같은 회색 상태로 보여 retry-after와 사용자 다음 행동이 모순된다
- retry-after를 보호용 backoff가 아니라 장식 숫자로 내려 polling amplification과 중복 제출을 유도한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/strict-read-fallback-contracts
- design-pattern/fallback-capacity-and-headroom-contracts
- design-pattern/semantic-lock-pending-state-pattern
next_docs:
- design-pattern/session-pinning-vs-version-gated-strict-reads
- design-pattern/strict-pagination-fallback-contracts
- design-pattern/process-manager-deadlines-timeouts
linked_paths:
- contents/design-pattern/strict-read-fallback-contracts.md
- contents/design-pattern/fallback-capacity-and-headroom-contracts.md
- contents/design-pattern/session-pinning-vs-version-gated-strict-reads.md
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/design-pattern/semantic-lock-pending-state-pattern.md
- contents/design-pattern/process-manager-deadlines-timeouts.md
- contents/design-pattern/projection-freshness-slo-pattern.md
- contents/design-pattern/strict-pagination-fallback-contracts.md
confusable_with:
- design-pattern/strict-read-fallback-contracts
- design-pattern/fallback-capacity-and-headroom-contracts
- design-pattern/semantic-lock-pending-state-pattern
- design-pattern/session-pinning-vs-version-gated-strict-reads
forbidden_neighbors: []
expected_queries:
- Strict fallback degraded UX는 fallback도 정답을 못 줄 때 PROCESSING/PENDING/retry-after를 response contract로 고정하는 패턴이야?
- PROCESSING은 시스템 catch-up이고 PENDING은 사람 승인이나 외부 provider 대기라는 차이를 사용자에게 왜 분리해야 해?
- retry-after는 UX 힌트가 아니라 breaker와 poll amplification을 보호하는 backoff contract인 이유가 뭐야?
- degraded response에는 operation_id, reason_code, retry_after, user_guarantees, next_actor가 왜 필요해?
- stale success를 보여주는 것보다 processing/pending contract로 truthful eventual consistency를 드러내는 게 더 안전한 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Strict Fallback Degraded UX Contracts playbook으로, primary read와 fallback
  source가 즉시 canonical truth를 줄 수 없을 때 PROCESSING/PENDING, reason_code, operation_id,
  retry-after, safe_to_resubmit, next_actor, user guarantee를 response contract로 내려 stale success와
  poll amplification을 막는 방법을 설명한다.
---
# Strict Fallback Degraded UX Contracts

> 한 줄 요약: primary read도 fallback source도 즉시 정답을 못 줄 때는 `processing`/`pending`/`retry-after`를 임시 스피너가 아니라 response-side contract로 고정해, 사용자가 무엇을 다시 시도해야 하고 무엇은 이미 안전하게 접수됐는지 일관되게 알 수 있어야 한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)
> - [Session Pinning vs Version-Gated Strict Reads](./session-pinning-vs-version-gated-strict-reads.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Semantic Lock and Pending State Pattern](./semantic-lock-pending-state-pattern.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)

retrieval-anchor-keywords: strict fallback degraded ux contract, degraded response contract, processing state contract, pending state response contract, retry-after contract, strict fallback user visible guarantees, fallback breaker response, honest eventual consistency ux, stale success prevention, bounded retry poll contract, pending versus processing contract, strict read degrade envelope

---

## 핵심 개념

[Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)가 "언제 canonical read를 포기하고 다른 경로로 우회할지"를 정한다면, Strict Fallback Degraded UX Contracts는 **그 우회마저 제한될 때 응답을 어떻게 보일지**를 정한다.

이 문서가 답하려는 질문은 네 가지다.

- 지금 보이는 `processing`은 시스템이 자동으로 끝낼 일인가, 아니면 사람/외부 의존성 때문에 `pending`인가
- 사용자가 새로 제출하면 중복이 나는가, 아니면 그냥 기다리면 되는가
- `retry-after`는 실제 보호용 backoff인가, 장식용 숫자인가
- 같은 작업을 새로고침했을 때 상태 문구와 약속이 왜 달라지지 않아야 하는가

degraded UX가 계약이 아니면 보통 다음이 벌어진다.

- primary는 stale해서 못 보여 주고, fallback은 포화돼서 못 읽는데 응답은 `200 success`처럼 보인다
- 어떤 화면은 `processing`, 다른 화면은 `not found`, 또 다른 화면은 옛 데이터를 보여 준다
- `retry-after: 1`을 계속 주며 polling amplification을 만든다
- 시스템이 실제로는 수동 검토 대기인데 사용자는 몇 초 뒤 자동 완료될 거라고 오해한다

즉 degraded UX의 목적은 "예쁘게 기다리게 하기"가 아니라, **truthful response contract로 correctness와 overload를 동시에 관리하는 것**이다.

### Retrieval Anchors

- `strict fallback degraded ux contract`
- `degraded response contract`
- `processing state contract`
- `pending state response contract`
- `retry-after contract`
- `strict fallback user visible guarantees`
- `fallback breaker response`
- `honest eventual consistency ux`
- `stale success prevention`
- `bounded retry poll contract`
- `pending versus processing contract`

---

## 깊이 들어가기

### 1. degraded UX는 fallback 실패 메시지가 아니라 마지막 안전한 계약이다

많은 팀이 degraded UX를 "fallback도 안 되면 spinner 띄우기" 정도로 본다.  
하지만 사용자가 체감하는 것은 spinner가 아니라 **무엇이 보장되는지**다.

그래서 response contract에는 최소한 다음이 들어가야 한다.

| 축 | 꼭 답해야 하는 질문 | 왜 필요한가 |
|---|---|---|
| Acceptance | 사용자의 직전 write/요청이 안전하게 접수됐는가 | 재시도/중복 제출 판단 기준이 된다 |
| Visibility | 결과가 아직 안 보이는 이유가 projection lag인지, manual hold인지, breaker-open인지 | 같은 `processing`이라도 다음 행동이 달라진다 |
| Retry policy | 언제 다시 poll/refresh해도 되는가 | poll amplification과 불필요한 클릭을 막는다 |
| User guarantee | 지금 절대 말하면 안 되는 것은 무엇인가 | stale success, false completion을 막는다 |
| Next actor | 시스템이 자동으로 끝낼 일인지, 사람/외부 응답을 기다리는지 | `processing`과 `pending`을 가르는 핵심이다 |

핵심은 degraded UX가 fallback의 그림자가 아니라 **정식 응답 모드**라는 점이다.

### 2. `PROCESSING`과 `PENDING`은 같은 회색 상태가 아니다

둘을 모두 "아직 안 끝남"으로 뭉개면 사용자는 시스템을 잘못 이해한다.

| 상태 | 시스템 의미 | 사용자에게 해도 되는 약속 | 기본 retry policy | 말하면 안 되는 것 |
|---|---|---|---|---|
| `PROCESSING` | 시스템이 이미 요청을 접수했고, 자동 처리 또는 catch-up이 진행 중이다 | 다시 제출하지 않아도 되고, 같은 `operation_id`로 수렴 경과를 추적할 수 있다 | 짧고 명시적인 `retry-after` 허용 | "이미 완료됐다" |
| `PENDING` | 사람 승인, 외부 provider, 별도 workflow gate처럼 자동 완료를 장담할 수 없는 대기다 | 요청/상태는 유지되지만 완료 시점은 외부 의존성에 달려 있음을 솔직히 말할 수 있다 | 짧은 poll보다 긴 revisit hint 또는 이벤트 알림이 더 적합 | "곧 끝난다" |

실무에서 구분이 흔들리는 순간은 보통 다음과 같다.

- fallback breaker가 열렸는데 무조건 `PENDING`으로 내려서, 사실은 시스템 포화인데 manual hold처럼 보이게 함
- manual review 대기인데 `PROCESSING`이라고 적어, 몇 초 뒤 자동 완료를 기대하게 함
- projection lag와 human approval을 한 UI state로 섞어, 지원팀도 원인을 해석하지 못함

따라서 degraded contract는 상태 이름보다도 **다음 actor와 completion ownership**을 더 선명하게 적어야 한다.

### 3. `retry-after`는 UX 힌트가 아니라 보호용 backoff 계약이다

`retry-after`를 그냥 "2초쯤 넣어 두자"로 다루면 poll 폭증과 사용자 오해를 동시에 만든다.

안전한 기본값은 다음과 같다.

| 상황 | `retry-after` 처리 | 이유 |
|---|---|---|
| projection catch-up, 짧은 fallback 포화, bounded processing | 짧은 `retry-after`를 **반드시** 명시 | 시스템이 자동으로 진전 중이고 재시도 시점이 비교적 예측 가능하다 |
| breaker-open으로 fallback reserve를 보호 중 | `retry-after`를 고정값이 아니라 보호 정책에 맞춰 점진적으로 키움 | 같은 1초 polling을 허용하면 breaker를 연 의미가 없다 |
| manual review, provider callback, long-running approval | 짧은 `retry-after`를 기본값으로 두지 않음 | poll해도 상태가 거의 안 바뀌므로 사용자와 시스템 모두 손해다 |
| 상태를 확인할 수단이 전혀 없을 때 | 가짜 `retry-after`를 주지 않고, 다음 확인 채널을 분리 | "언제든 다시 눌러 보세요"는 계약이 아니라 회피다 |

`retry-after`를 설계할 때 지켜야 할 규칙은 단순하다.

- `retry-after=0` 같은 사실상 즉시 재시도 유도값은 두지 않는다
- 짧은 값이면 왜 짧은지 설명 가능한 bounded processing이어야 한다
- `PENDING`인데 1~2초 poll을 계속 시키지 않는다
- UI auto-refresh와 API `retry-after`를 서로 모순되게 두지 않는다

### 4. 사용자에게 보여 주는 보장은 "무엇이 아직 아니다"까지 포함해야 한다

degraded UX의 핵심은 optimistic phrasing이 아니라 **보장 경계의 명시**다.

| 보장 축 | `PROCESSING`에서 기본 보장 | `PENDING`에서 기본 보장 |
|---|---|---|
| 접수 여부 | 직전 작업은 접수됐고 중복 제출 없이 추적 가능 | 현재 상태/요청은 시스템에 기록돼 있음 |
| 결과 확정성 | 아직 최종 가시성/완료를 말하지 않음 | 더더욱 완료 시점/성공을 말하지 않음 |
| 재시도 안전성 | refresh/poll은 안전하지만 submit 재실행은 보통 금지 | refresh는 가능하되, 사용자가 해야 할 다음 행동이 따로 있을 수 있음 |
| 오류 해석 | primary/fallback 제약 때문에 확인 지연 중 | 외부/수동 gate 때문에 보류 중 |
| 종료 조건 | canonical read 회복, projector catch-up, breaker close | 승인 완료, callback 도착, timeout/거절 |

그래서 문구도 다음처럼 달라져야 한다.

- `PROCESSING`: "요청은 접수되었고 반영을 확인 중입니다. 다시 제출하지 말고 {retry_after}s 후 새로고침하세요."
- `PENDING`: "현재 수동 검토/외부 응답을 기다리고 있습니다. 지금 새로고침해도 바로 완료되지 않을 수 있습니다."

둘 다 공통으로 금지해야 하는 것은 다음이다.

- 확인되지 않은 데이터를 완료된 것처럼 보여 주기
- 재제출이 위험한데 CTA를 `다시 시도` 하나로만 두기
- 동일 작업에 대해 detail/list/banner가 서로 다른 완료 약속을 말하기

### 5. degraded contract는 화면마다 새로 만들지 말고 operation 단위로 붙여야 한다

같은 작업에 대해 어떤 화면은 `processing`, 어떤 화면은 옛 데이터, 어떤 화면은 `not found`를 보여 주는 순간 사용자는 "시스템이 거짓말한다"고 느낀다.

그래서 최소한 아래 식별자는 같은 recent-write window 동안 공유하는 편이 안전하다.

- `operation_id` 또는 `mutation_id`
- `degraded_contract_id`
- `reason_code`
- `next_poll_not_before`
- `guarantee_level`

이렇게 해야 list/detail/badge가 서로 다른 read path를 보더라도, **이번 작업은 아직 canonical visibility를 확인하지 못했다**는 사실을 같은 문장으로 유지할 수 있다.

[Session Pinning vs Version-Gated Strict Reads](./session-pinning-vs-version-gated-strict-reads.md)가 route non-regression을 다룬다면, 이 문서는 **narrative non-regression**을 다룬다.  
즉 route가 같아도 응답 설명이 흔들리면 사용자는 일관성을 잃는다.

### 6. 최소 response packet을 고정하면 API와 UI가 덜 흔들린다

| 필드 | 꼭 담아야 하는 질문 | 예시 |
|---|---|---|
| `degraded_state` | 지금이 `PROCESSING`인가 `PENDING`인가 | `PROCESSING` |
| `reason_code` | 왜 canonical result를 못 보여 주는가 | `PRIMARY_LAG_AND_FALLBACK_BREAKER_OPEN` |
| `operation_id` | 사용자가 방금 한 작업을 어떻게 추적하는가 | `order-create-9f1a...` |
| `retry_after_seconds` | 언제 다시 확인해도 되는가 | `3` |
| `next_poll_not_before` | client auto-refresh가 지켜야 할 하한은 무엇인가 | `2026-04-14T10:03:12Z` |
| `user_guarantees` | 무엇이 접수/미보장 상태인가 | `accepted=true`, `final_visible=false`, `safe_to_resubmit=false` |
| `next_actor` | 시스템, 사람, 외부 provider 중 누가 공을 쥐고 있는가 | `SYSTEM` |
| `expires_at` | 이 degraded contract를 언제 다시 평가해야 하는가 | strict window 종료 시각 |
| `status_url` 또는 `refresh_token` | 후속 확인 경로가 있는가 | `/operations/{id}` |

HTTP status는 transport 문맥일 뿐이고, **도메인 상태는 위 packet이 설명해야 한다**.  
어떤 팀은 `200`으로, 어떤 팀은 `202`로 표현할 수 있지만, body contract가 비어 있으면 사용자 약속은 여전히 흐릿하다.

### 7. breaker-open 상태에서는 "작동 중"보다 "보호 중"을 더 정확히 말해야 한다

[Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)에서 breaker-open은 2차 장애 차단 장치다.  
이때 응답도 그 사실을 숨기지 말아야 한다.

- `processing`은 유지하되, 단순 지연이 아니라 보호 정책 때문에 확인을 늦추고 있음을 드러낸다
- `retry-after`는 reserve 보호 정책에 맞춰 늘어난다
- 사용자가 새로 제출하면 중복/추가 부하가 날 수 있음을 명시한다
- 기존에 확인된 마지막 snapshot이 있다면 "마지막 확인 기준"임을 분리해서 보여 준다

즉 breaker-open은 단지 internal metric이 아니라 **response contract reason family**여야 한다.

### 8. pagination/list에도 같은 contract가 필요하다

목록 endpoint에서 `page1-only fallback`을 두더라도, later-page나 badge는 여전히 제약될 수 있다.  
이때 화면별로 제각각 다른 degraded 문구를 내면 오히려 더 혼란스럽다.

안전한 기본값은 다음과 같다.

- page 1 strict fallback이 실패하거나 breaker-open이면 `processing` shortcut으로 내려간다
- `retry-after`와 함께 "새 항목 반영을 확인 중"이라고 말하되, page 2 continuity를 암시하지 않는다
- list/detail/badge가 같은 `operation_id`를 공유해 이번 write window의 설명을 맞춘다

즉 [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)가 cursor world를 다룬다면, 이 문서는 **그 실패를 사용자에게 어떤 문장으로 번역할지**를 다룬다.

### 9. 하지 말아야 할 것

- stale row를 그대로 보여 주면서 상단에만 "반영 중" 배지를 붙이지 말 것
- `PENDING`과 `PROCESSING`을 하나의 회색 라벨로 합치지 말 것
- breaker-open인데 `retry-after=1`로 polling amplification을 유도하지 말 것
- manual review 대기에 short poll을 기본값으로 두지 말 것
- 같은 작업에 대해 API는 `processing`, 웹은 `not found`, 푸시는 `completed`처럼 서술을 갈라 버리지 말 것

---

## 실전 시나리오

### 시나리오 1: 주문 생성 직후, primary lag + write fallback breaker-open

- command는 성공했고 `operation_id`가 있다
- detail projection은 `expectedVersion` 미달
- write query port는 saturation으로 breaker-open

이때 응답 계약은 다음처럼 잡는 편이 안전하다.

- state: `PROCESSING`
- reason: `PRIMARY_LAG_AND_FALLBACK_BREAKER_OPEN`
- guarantee: 접수는 완료, 최종 가시성은 미보장, 재제출 금지
- retry-after: 3초, 이후 보호 정책에 따라 증가 가능

핵심은 "주문이 사라졌다"가 아니라 **주문은 접수됐지만 확인 경로를 잠시 늦추고 있다**를 정확히 말하는 것이다.

### 시나리오 2: 결제 후 manual review hold

- 결제 요청은 기록됐다
- fraud/manual review가 걸려 자동 완료를 보장할 수 없다
- projection lag는 부차적 문제다

이 경우는 `PROCESSING`보다 `PENDING`이 맞다.

- state: `PENDING`
- next actor: `MANUAL_REVIEW`
- retry-after: 짧은 poll 생략 또는 긴 revisit hint
- guarantee: 요청은 유지되지만 완료 시점은 미보장

이 문맥에서 `retry-after: 2`를 주면 사용자는 자동 완료를 기대하게 된다.

### 시나리오 3: 내 주문 page 1 strict fallback도 막힌 경우

- page 1 strict shortcut이 필요하다
- old projection fallback reserve가 포화됐다
- detail 화면도 동일 write window 안에 있다

이때 list/detail 둘 다 같은 degraded contract를 공유해야 한다.

- same `operation_id`
- same `reason_code` family
- same `next_poll_not_before`
- list는 "첫 화면 반영을 확인 중"이라고 말하되 page 2 continuity는 약속하지 않음

이렇게 해야 사용자는 화면마다 다른 시스템을 보는 느낌을 덜 받는다.

---

## 코드로 보기

### degraded response packet

```java
public enum DegradedState {
    PROCESSING,
    PENDING
}

public enum NextActor {
    SYSTEM,
    MANUAL_REVIEW,
    EXTERNAL_PROVIDER
}

public record UserGuarantees(
    boolean accepted,
    boolean finalVisible,
    boolean safeToResubmit
) {}

public record DegradedResponseContract(
    String contractId,
    String operationId,
    DegradedState state,
    String reasonCode,
    Duration retryAfter,
    Instant nextPollNotBefore,
    NextActor nextActor,
    UserGuarantees guarantees
) {}
```

### contract selection

```java
public final class StrictFallbackDegradePolicy {
    public DegradedResponseContract decide(
        boolean accepted,
        boolean fallbackBreakerOpen,
        boolean awaitingManualReview,
        String operationId,
        Instant now
    ) {
        if (awaitingManualReview) {
            return new DegradedResponseContract(
                "payments.manual-review",
                operationId,
                DegradedState.PENDING,
                "MANUAL_REVIEW_WAIT",
                Duration.ofMinutes(10),
                now.plus(Duration.ofMinutes(10)),
                NextActor.MANUAL_REVIEW,
                new UserGuarantees(accepted, false, false)
            );
        }

        if (fallbackBreakerOpen) {
            return new DegradedResponseContract(
                "orders.strict-fallback",
                operationId,
                DegradedState.PROCESSING,
                "PRIMARY_LAG_AND_FALLBACK_BREAKER_OPEN",
                Duration.ofSeconds(3),
                now.plusSeconds(3),
                NextActor.SYSTEM,
                new UserGuarantees(accepted, false, false)
            );
        }

        throw new IllegalStateException("degraded contract not required");
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| spinner만 두고 상태 의미를 비워 둠 | 구현이 빠르다 | 사용자/운영 모두 오해한다 | 학습용 프로토타입 외에는 비추천 |
| `PROCESSING`/`PENDING` + `retry-after`를 response contract로 고정 | truthful UX와 overload 보호를 같이 챙긴다 | API/클라이언트 계약을 더 엄격히 관리해야 한다 | strict read / fallback / breaker가 얽힌 서비스 |
| manual review도 short poll로 통일 | 구현은 단순해 보인다 | poll amplification과 false expectation이 커진다 | 거의 비추천 |

판단 기준은 다음과 같다.

- `processing`은 시스템이 completion ownership을 가질 때만 쓴다
- `pending`은 외부/사람 gate를 숨기지 않을 때만 쓴다
- `retry-after`는 보호 정책과 같은 방향으로 움직여야 한다
- 동일 작업의 여러 화면은 같은 degraded contract narrative를 공유한다

---

## 꼬리질문

> Q: degraded UX면 그냥 상단 배너 하나로 충분하지 않나요?
> 의도: 문구와 계약을 구분하는지 보는 질문이다.
> 핵심: 아니다. 배너보다 중요한 것은 재제출 가능 여부, retry timing, next actor 같은 response-side 보장이다.

> Q: `PROCESSING`과 `PENDING`을 둘 다 "대기 중"으로 번역해도 되나요?
> 의도: 자동 완료와 외부 의존 대기를 구분하는지 보는 질문이다.
> 핵심: 비추천이다. 둘은 completion ownership과 retry policy가 다르다.

> Q: `retry-after`만 주면 user-visible guarantee는 생긴 것 아닌가요?
> 의도: backoff와 correctness 약속을 같은 것으로 보는지 확인한다.
> 핵심: 아니다. 언제 다시 보라는 것과 무엇이 이미 접수됐는지는 다른 질문이다.

## 한 줄 정리

Strict Fallback Degraded UX Contracts는 primary/fallback이 모두 제약될 때 `processing`/`pending`/`retry-after`를 정식 response contract로 만들어, 사용자에게는 거짓 완료를 숨기지 않고 시스템에는 polling과 overload를 억제하게 해 주는 패턴이다.
