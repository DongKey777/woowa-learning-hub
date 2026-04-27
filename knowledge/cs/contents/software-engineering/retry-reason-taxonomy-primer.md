# Primer On Retry Reason Taxonomy

> 한 줄 요약: 초심자용 retry reason taxonomy는 "지금 다시 해볼까", "사람이 먼저 볼까", "이번 정책에서는 종료할까" 세 갈래만 먼저 고정하면 충분하다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: retry reason taxonomy primer basics, retry reason taxonomy primer beginner, retry reason taxonomy primer intro, software engineering basics, beginner software engineering, 처음 배우는데 retry reason taxonomy primer, retry reason taxonomy primer 입문, retry reason taxonomy primer 기초, what is retry reason taxonomy primer, how to retry reason taxonomy primer
retry 정책을 처음 잡을 때 가장 흔한 실수는 reason code 이름을 많이 만드는 것이다.
초심자에게 더 중요한 일은 이름 개수보다 **다음 행동이 섞이지 않게 묶는 것**이다.
이 문서는 beginner-safe 기준으로 `retryable`, `manual-review`, `permanent` 세 그룹만 먼저 설명한다.
[Retry Queue Assertions Primer](./retry-queue-assertions-primer.md)에서 테스트 관점을 보고 있다면, 여기서는 그 테스트가 기대하는 분류표를 먼저 단순하게 만드는 데 집중한다.
run 결과 타입을 먼저 보고 싶다면 [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md), 운영 복구 흐름까지 연결하고 싶다면 [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)를 이어서 보면 된다.

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 한 장면](#먼저-잡을-한-장면)
- [세 그룹만 먼저 나누면 되는 이유](#세-그룹만-먼저-나누면-되는-이유)
- [초심자용 작은 reason-code 묶음](#초심자용-작은-reason-code-묶음)
- [작게 시작하는 naming 규칙](#작게-시작하는-naming-규칙)
- [짧은 분류 예시](#짧은-분류-예시)
- [테스트와 runbook에서 어떻게 쓰나](#테스트와-runbook에서-어떻게-쓰나)
- [practice loop](#practice-loop)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

> 관련 문서:
> - [Retry Queue Assertions Primer](./retry-queue-assertions-primer.md)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
> - [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
> - [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)
> - [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md)
>
> retrieval-anchor-keywords:
> - retry reason taxonomy primer
> - beginner retry reason code grouping
> - retryable permanent manual review primer
> - batch reason code grouping beginner
> - retry reason classification starter set
> - retryable vs permanent vs manual review
> - batch failure reason taxonomy
> - small reason code grouping
> - reason code next action mapping
> - permanent failure reason code beginner
> - manual review reason code example
> - retryable reason code example
> - retry policy reason taxonomy
> - batch retry classification primer
> - failure reason grouping for tests
> - retry queue reason code grouping
> - operator manual review reason mapping
> - reason code naming beginner
> - batch failure next action taxonomy
> - retry classification practice loop

## 먼저 잡을 한 장면

초심자는 reason code를 "오류 이름"보다 "다음 행동 표지판"으로 기억하는 편이 안전하다.

- `retryable`: 잠깐 뒤 같은 입력으로 다시 해볼 가치가 있다
- `manual-review`: 사람이 먼저 확인하거나 값을 고쳐야 한다
- `permanent`: 이번 정책에서는 더 진행하지 않고 종료한다

핵심은 원인 분석의 깊이가 아니라 **자동화가 다음에 무엇을 해도 되는가**다.
예를 들어 timeout과 validation 오류를 둘 다 "실패"라고만 적으면, retry queue와 운영 backlog가 섞여 버린다.

## 세 그룹만 먼저 나누면 되는 이유

초심자 taxonomy에서 reason code는 많아도 되지만, 그룹은 먼저 작아야 한다.
세 그룹만 있어도 아래 세 질문에 바로 답할 수 있기 때문이다.

| 먼저 답할 질문 | 그룹 |
|---|---|
| 지금 자동으로 다시 시도해도 되는가 | `retryable` |
| 사람 판단이나 데이터 수정이 먼저 필요한가 | `manual-review` |
| 지금 같은 입력으로는 결과가 바뀌지 않는가 | `permanent` |

이 세 질문이 잠기면 테스트, backlog, runbook이 같이 단순해진다.

- 테스트는 `nextAction`과 bucket 분리만 먼저 검증하면 된다
- 운영자는 retry queue와 manual-review backlog를 섞어 보지 않게 된다
- 개발자는 reason code를 추가해도 어느 그룹인지 먼저 고정할 수 있다

## 초심자용 작은 reason-code 묶음

beginner-safe starter set은 아래 정도면 충분하다.
도메인마다 이름은 달라질 수 있지만, 다음 행동이 흔들리지 않는지가 더 중요하다.

| 그룹 | 공통 성격 | starter reason code 예시 | 기본 next action |
|---|---|---|---|
| `retryable` | 외부 상태나 짧은 시간 경과로 결과가 바뀔 수 있다 | `partner-timeout`, `temporary-network-error`, `rate-limit-hit` | 같은 item key로 나중에 재시도 |
| `manual-review` | 사람 확인, 보정, 정책 판단이 먼저 필요하다 | `missing-required-field`, `invalid-account`, `policy-violation` | backlog에 남기고 자동 retry 금지 |
| `permanent` | 같은 입력으로 다시 돌려도 바뀌지 않는다 | `unsupported-country`, `deleted-user`, `duplicate-closed-order` | 종료로 기록하고 다음 item 진행 |

이 표에서 중요한 점은 "원인을 아주 정확히 설명했는가"보다 "경로를 안전하게 나눴는가"다.
예를 들어 `invalid-phone-format`을 `manual-review`로 둘지 `permanent`로 둘지는 팀 정책 차이가 있을 수 있다.
하지만 한 번 정했다면 자동 retry와 섞이지 않게 유지해야 한다.

## 작게 시작하는 naming 규칙

reason code 이름이 길어지기 전에 아래 네 규칙부터 지키면 taxonomy가 덜 흐려진다.

1. reason code는 원인 단서를 주고, 그룹은 다음 행동을 결정하게 둔다.
2. 같은 이유를 뜻하는 이름을 둘 이상 만들지 않는다.
3. 기술 에러 이름과 운영 행동 이름을 한 문자열에 섞지 않는다.
4. 새 code를 추가할 때는 "어느 bucket인가"를 먼저 정한다.

짧은 비교:

| 덜 안전한 이름 | 더 안전한 첫 이름 | 이유 |
|---|---|---|
| `retry-later-invalid-account` | `invalid-account` | reason과 action을 분리해야 정책 변경이 쉽다 |
| `fatal-error-7` | `unsupported-country` | 초심자도 종료 이유를 읽을 수 있어야 한다 |
| `bad-data` | `missing-required-field` | manual review backlog가 무엇을 고쳐야 하는지 보이게 한다 |

## 짧은 분류 예시

주문 동기화 batch에서 아래 실패가 나왔다고 하자.

| item | reason code | 초심자 분류 | 이유 |
|---|---|---|---|
| `order-101` | `partner-timeout` | `retryable` | 파트너 상태가 회복되면 성공 가능성이 있다 |
| `order-102` | `missing-required-field` | `manual-review` | 값 보정이나 원천 데이터 확인이 먼저다 |
| `order-103` | `unsupported-country` | `permanent` | 같은 입력으로는 정책상 계속 거절된다 |

이때 결과는 아래처럼 읽히면 된다.

```text
retry queue:
- order-101 / partner-timeout

manual review backlog:
- order-102 / missing-required-field

permanent failures:
- order-103 / unsupported-country
```

초심자에게 이 예시가 중요한 이유는 count보다 **경로가 분리되어 보인다**는 점이다.
세 item 모두 실패했지만, 다음 행동은 셋 다 다르다.

## 테스트와 runbook에서 어떻게 쓰나

taxonomy는 문서로만 끝나면 금방 흐려진다.
초심자 기준으로는 아래 두 군데에 바로 연결하면 효과가 크다.

| 쓰는 곳 | 먼저 잠글 것 |
|---|---|
| 테스트 | reason code가 기대 bucket과 `nextAction`으로 번역되는가 |
| runbook | operator가 retry, manual review, 종료를 다른 절차로 읽을 수 있는가 |

예를 들어 테스트에서는 아래 질문이면 충분하다.

- `partner-timeout`은 retry queue로 가는가
- `missing-required-field`는 manual review bucket에만 남는가
- `unsupported-country`는 retry queue와 manual review에 섞이지 않는가

운영 문서에서는 아래처럼 짧게 연결하면 된다.

- `retryable`: 같은 item key로 backlog 재시도
- `manual-review`: 사람 확인 후 수정 또는 재처리 결정
- `permanent`: 종료로 기록하고 재시도 금지

이 연결이 더 필요하면 [Retry Queue Assertions Primer](./retry-queue-assertions-primer.md)와 [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)를 함께 보면 된다.

## practice loop

처음 taxonomy를 붙일 때는 큰 표를 만들기보다 아래 연습 한 바퀴면 충분하다.

1. 현재 batch에서 자주 나오는 실패 3개만 고른다.
2. 각 실패에 대해 `retryable`, `manual-review`, `permanent` 중 하나만 붙인다.
3. 각 그룹에 맞는 `nextAction` 한 줄을 적는다.
4. 테스트 1개씩으로 bucket 분리를 고정한다.
5. 한 주 뒤 새 실패가 나오면 기존 code 재사용이 가능한지 먼저 본다.

이 루프의 목표는 taxonomy를 크게 만드는 것이 아니라, 새 reason code가 생겨도 기존 분류가 쉽게 흔들리지 않게 만드는 것이다.

## 자주 하는 오해

| 오해 | 더 안전한 이해 |
|---|---|
| `permanent`는 무조건 심각 장애다 | 여기서는 "이번 정책상 종료"라는 뜻에 가깝다 |
| retryable이 아니면 전부 manual review다 | 사람이 볼 필요가 없으면 `permanent`로 닫는 편이 더 명확하다 |
| reason code가 많을수록 정교하다 | 초심자 단계에서는 next action이 분명한 작은 starter set이 더 안전하다 |
| manual review는 운영 문서 일이라 코드와 무관하다 | 코드에서 bucket이 섞이면 backlog와 runbook도 같이 흔들린다 |

## 한 줄 정리

beginner retry reason taxonomy는 많은 이름보다 `retryable`, `manual-review`, `permanent` 세 갈래를 먼저 고정해 자동 재시도, 사람 확인, 종료 경로를 섞지 않게 만드는 것이 핵심이다.
