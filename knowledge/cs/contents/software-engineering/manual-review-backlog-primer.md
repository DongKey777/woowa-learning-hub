# Manual Review Backlog Primer

> 한 줄 요약: 분류가 끝난 뒤 `manual-review` bucket은 "실패를 쌓아 두는 통"이 아니라, 사람이 다음 판단을 이어 가기 위해 최소 필드와 owner를 분명히 남기는 작업 backlog다.

**난이도: 🟢 Beginner**

관련 문서:

- [Primer On Retry Reason Taxonomy](./retry-reason-taxonomy-primer.md)
- [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)
- [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)
- [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
- [System Design: Job Queue 설계](../system-design/job-queue-design.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: manual review backlog primer, manual-review bucket beginner, manual review ownership rules, batch manual review fields, manual review 뭐부터 봐야 하나, manual review backlog 기초, classification after manual review, beginner operator backlog, who owns manual review item, manual review item fields, retryable vs manual-review backlog, manual review queue basics

## 핵심 개념

초심자는 `manual-review`를 "자동 재시도를 못 한 실패 모음"으로만 이해하기 쉽다.
하지만 실제로 더 안전한 이해는 이것이다.

- `retryable`은 시스템이 나중에 다시 해볼 수 있는 일
- `manual-review`는 사람이 먼저 판단해야 하는 일
- backlog item은 그 판단을 이어 가기 위한 작은 작업 카드

즉 `manual-review` bucket의 핵심은 실패 개수보다 **다음 사람에게 넘길 문맥이 충분한가**다.
`reasonCode`만 있고 누가 봐야 하는지 모르면 backlog는 금방 방치된다.

## 한눈에 보기

| 질문 | `retry queue` | `manual-review backlog` |
|---|---|---|
| 다음 행동을 누가 하나 | 시스템 | 사람 |
| 최소로 남길 것 | 재시도에 필요한 item 식별자와 retry 정보 | item 식별자, 왜 멈췄는지, 누가 판단할지, 언제 다시 볼지 |
| 잘못 섞이면 생기는 문제 | 불필요한 재시도 폭주 | owner 없는 backlog, 중복 대응, 영구 방치 |
| 초심자 첫 체크 | "같은 입력으로 다시 해도 되나?" | "사람이 무엇을 보고 어떤 결정을 내려야 하나?" |

짧은 멘탈 모델로 보면 `manual-review` item은 장애 로그가 아니라 **작업 티켓의 가장 작은 형태**다.

## 상세 분해

### 1. beginner-safe 필드는 많지 않아도 된다

처음부터 큰 스키마를 만들기보다 아래 필드만 먼저 안정적으로 남기면 된다.

| 필드 | 왜 필요한가 | beginner-safe 예시 |
|---|---|---|
| `itemId` | 무엇을 다시 봐야 하는지 잃지 않기 위해 | `order-102` |
| `reasonCode` | 왜 자동 경로에서 빠졌는지 분류를 유지하기 위해 | `missing-required-field` |
| `summary` | 운영자나 개발자가 한 줄로 상황을 이해하기 위해 | `배송지 우편번호 누락` |
| `sourceRef` | 원본 입력이나 실패 증거를 다시 열기 위해 | `upload-2026-04-28.csv:19` |
| `ownerTeam` 또는 `ownerRole` | 누가 첫 판단을 해야 하는지 정하기 위해 | `ops-billing`, `partner-ops` |
| `nextReviewAt` 또는 `dueAt` | "언젠가 보자" 상태를 막기 위해 | `2026-04-29 10:00` |

이 정도면 초심자 문맥에서 "무엇이 문제인지", "누가 볼지", "언제 다시 볼지"가 드러난다.

### 2. 분류 결과와 backlog 필드는 같은 질문에 답해야 한다

분류기에서 `manual-review`로 보냈다면 backlog 필드도 그 결정을 설명해야 한다.

예를 들어 아래 두 케이스는 둘 다 실패지만, backlog 질문이 다르다.

| reason code | backlog에서 바로 보여야 하는 질문 |
|---|---|
| `missing-required-field` | 어떤 값이 비었고 원본을 어디서 고치나? |
| `policy-violation` | 예외 승인 대상인지, 아니면 종료해야 하나? |
| `invalid-account` | 고객/파트너 쪽 확인이 필요한가, 내부 데이터 정정이 필요한가? |

`summary`가 `failed`처럼 너무 넓으면 사람이 다시 코드를 열어야 한다.
반대로 `summary`가 너무 길어도 검색과 triage가 느려진다.
초심자 기준으로는 "왜 멈췄는지 + 다음에 볼 단서 1개" 정도면 충분하다.

## ownership을 나누는 기준

### 1. owner는 사람 이름보다 책임 경계가 먼저다

가장 흔한 실수는 `owner=alice`처럼 개인 이름만 남기는 것이다.
휴가, 교대, 팀 이동이 생기면 backlog가 바로 흔들린다.

beginner-safe 규칙은 아래처럼 단순하게 잡을 수 있다.

| 먼저 정할 것 | 권장 예시 | 피할 예시 |
|---|---|---|
| 책임 경계 | `billing-ops`, `catalog-admin`, `partner-support` | `alice`, `bob` |
| 첫 판단 역할 | `operator`, `service-owner`, `partner-manager` | `누군가 확인` |
| escalation 경로 | `24h 내 미처리면 service-owner review` | 비어 있음 |

개인 담당자는 별도 할당 필드로 둘 수 있지만, backlog의 기본 owner는 **팀 또는 역할 경계**가 더 안전하다.

### 2. ownership rule은 "한 item, 한 다음 결정권자"에서 시작한다

한 item에 owner가 여러 명이면 실제로는 아무도 움직이지 않는 경우가 많다.
초심자 단계에서는 아래 네 규칙만 고정해도 품질이 많이 좋아진다.

1. 한 backlog item에는 기본 owner가 하나만 있다.
2. 자동 retry와 manual-review owner를 동시에 두지 않는다.
3. owner 변경이 필요하면 handoff 이유를 한 줄 남긴다.
4. `closed`로 끝낼 때는 "수정 후 재처리", "정책상 종료", "중복으로 병합" 중 하나를 함께 남긴다.

이 규칙의 목적은 정교한 워크플로 엔진을 만드는 것이 아니라, "지금 누구 차례인가"를 흐리지 않게 하는 데 있다.

## 흔한 오해와 함정

| 오해 | 더 안전한 이해 |
|---|---|
| manual review는 실패를 다 모아 두는 보관함이다 | manual review는 사람이 다음 결정을 내리기 위한 작업 backlog다 |
| `reasonCode`만 있으면 운영자가 알아서 본다 | owner와 sourceRef가 없으면 backlog는 오래 남기 쉽다 |
| owner를 여러 팀으로 걸어 두면 안전하다 | 기본 owner가 흐리면 모두가 구경꾼이 되기 쉽다 |
| due time은 나중에 붙여도 된다 | 처음부터 review 시점을 두어야 방치 신호를 빨리 본다 |

특히 "`manual-review`면 일단 운영팀"으로 뭉개면 안 된다.
데이터 보정이 필요한지, 도메인 정책 판단이 필요한지에 따라 첫 owner가 달라질 수 있다.

## 실무에서 쓰는 모습

주문 업로드 batch에서 세 건이 분류됐다고 가정하자.

| item | 분류 | backlog에 남길 핵심 |
|---|---|---|
| `order-101` | `retryable` | retry queue로 보냄. manual-review item 생성 안 함 |
| `order-102` | `manual-review / missing-required-field` | `summary=배송지 우편번호 누락`, `sourceRef=orders.csv:19`, `ownerTeam=ops-order`, `dueAt=오늘 15:00` |
| `order-103` | `manual-review / policy-violation` | `summary=차단 국가 주문`, `ownerTeam=service-owner`, `dueAt=내일 10:00`, `decisionHint=예외 승인 또는 종료` |

여기서 중요한 점은 `order-102`와 `order-103`이 같은 `manual-review`라도 **같은 사람이 같은 방식으로 처리하지 않는다**는 점이다.
그래서 backlog item은 "manual-review" 한 단어보다, 그 안의 ownership과 다음 질문을 같이 보여 줘야 한다.

## 더 깊이 가려면

- 실패를 왜 `retryable`, `manual-review`, `permanent`로 나누는지부터 다시 보고 싶다면 [Primer On Retry Reason Taxonomy](./retry-reason-taxonomy-primer.md)를 먼저 읽는다.
- 테스트에서 manual-review bucket 분리를 어떻게 잠글지 보려면 [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)를 이어서 본다.
- 사람이 보는 backlog를 실제 operator 절차와 rerun 기준으로 연결하려면 [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)를 읽는다.
- owner 변경과 handoff를 더 엄격하게 다루려면 [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)로 내려간다.

## 면접/시니어 질문 미리보기

| 질문 | 왜 묻는가 | 짧은 핵심 |
|---|---|---|
| manual-review item에 왜 `ownerTeam`이 필요한가 | backlog가 기술 로그인지 운영 작업인지 구분하는지 보기 위해 | 다음 결정권자를 명확히 해야 방치와 중복 대응을 줄일 수 있다 |
| `manual-review`와 `permanent`는 어떻게 다르나 | 종료와 사람 판단 대상을 섞지 않는지 보기 위해 | manual-review는 아직 사람 결정이 남았고, permanent는 현재 정책상 종료다 |
| owner를 개인이 아니라 역할/팀으로 두는 이유는 무엇인가 | 운영 지속성과 handoff 감각을 보는 질문 | 교대, 휴가, 팀 이동이 있어도 backlog 책임 경계가 유지된다 |

## 한 줄 정리

`manual-review` bucket은 실패 저장소가 아니라, `itemId + 이유 + 원본 단서 + owner + review 시점`을 남겨 사람이 다음 결정을 이어 가게 만드는 beginner-safe backlog다.
