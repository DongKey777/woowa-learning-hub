# PENDING Row Recovery Primer

> 한 줄 요약: 기존 `PENDING` idempotency row는 "아직 누군가 정상 처리 중인가?"를 먼저 보고, **살아 있음 신호가 남아 있으면 저장소 상태는 `PENDING`으로 두고, 호출자에게는 `PROCESSING`/`in-progress`로 설명**하며, **명시적인 lease/heartbeat 만료와 compare-and-swap takeover 조건이 있을 때만 recovery**해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [UNIQUE Claim + Existing-Row Reuse Primer](./unique-claim-existing-row-reuse-primer.md)
- [Idempotency Key Status Contract Examples](./idempotency-key-status-contract-examples.md)
- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- [Transaction Heartbeat와 Long-Running Job Locking](./transaction-heartbeat-long-running-job-locking.md)
- [DB Lease와 Fencing Token](./db-lease-fencing-coordination.md)
- [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: pending row recovery primer, pending idempotency row takeover, stale processing row recovery, in progress versus takeover idempotency, lease heartbeat expiry recovery, pending row safe recovery beginner, pending row should stay processing, idempotency pending row liveness, processing row stale detection beginner, compare and swap takeover row, retry after pending row, pending row recovery checklist, pending row heartbeat primer, pending row lease primer, pending row takeover safety

## 먼저 멘탈모델

초보자는 이 장면을 "계산대에 놓인 작업 바구니"로 보면 쉽다.

- `PENDING`: 바구니가 계산대에 올라와 있다
- heartbeat/lease: 점원이 아직 이 바구니를 **잡고 있는지 보여 주는 표지판**
- recovery/takeover: 점원이 정말 사라졌다고 확인된 뒤, 다른 점원이 **같은 바구니를 이어받는 절차**

핵심 한 줄:

> `PENDING`이라고 해서 바로 abandoned row는 아니다. **살아 있음 신호가 남아 있으면 기다리고, 살아 있음 신호가 명시적으로 끊겼을 때만 takeover**를 검토한다.

## 이름이 비슷해서 헷갈릴 때

이 문서에서는 `PENDING`과 `PROCESSING`을 같은 말로 쓰지 않는다.

| 이름 | 붙는 위치 | 초보자 해석 |
|---|---|---|
| `PENDING` | idempotency row 저장 상태 | winner가 row를 잡았지만 아직 최종 성공으로 닫지 못했다 |
| `PROCESSING` | 중복 요청에 돌려주는 응답 표현 | "기존 `PENDING` row가 아직 살아 있으니 기다려라" |
| `SUCCEEDED` | idempotency row 저장 상태 | 같은 key의 성공 결과가 이미 굳었다 |

짧게 외우면:

- row를 읽을 때는 `PENDING`인지 `SUCCEEDED`인지 본다
- 클라이언트에 설명할 때는 `PROCESSING` 응답을 줄 수 있다

## 이 문서가 답하는 질문

같은 `idempotency_key` 재시도에서 기존 row가 `PENDING`일 때 가장 흔한 질문은 둘이다.

1. 이 row를 계속 `in-progress`로 봐야 하나?
2. 아니면 내가 takeover해서 recovery를 시작해도 되나?

beginner 기본값은 단순하다.

- **기본값 1:** ownership 신호가 살아 있으면 takeover하지 않는다
- **기본값 2:** ownership 신호가 없으면 그래도 바로 덮어쓰지 말고, 명시적 recovery 규칙이 있을 때만 takeover한다

## 30초 결정표

| 기존 `PENDING` row 상태 | 초보자 해석 | 기본 행동 |
|---|---|---|
| 최근 heartbeat가 있고 lease도 안 지났음 | 원래 worker가 아직 처리 중일 가능성이 높다 | `in-progress` 유지 |
| heartbeat/lease 개념이 아예 없음 | 누가 살아 있는지 판단할 증거가 부족하다 | 무리한 takeover 금지, 짧은 대기/조회 우선 |
| lease 만료 + heartbeat stale + owner/version 검증 가능 | 원래 worker가 ownership을 잃었을 가능성이 높다 | compare-and-swap takeover 후보 |
| 외부 side effect 결과를 조회할 수 없음 | commit 직전/직후 상태를 모른다 | blind retry 금지, 결과 조회 경로 먼저 |
| 새 요청 payload hash가 다름 | recovery 문제가 아니라 key misuse다 | `409 conflict` |

## 왜 `PENDING`을 함부로 takeover하면 위험한가

`PENDING` row는 보통 "아직 안 끝났다"와 "어디까지 끝났는지 모른다"를 동시에 뜻한다.

특히 아래 경우가 위험하다.

- 원래 worker가 외부 결제를 이미 보냈지만 DB final update만 못 했을 수 있다
- commit outcome이 불명확해서 실제 결과는 성공인데 row만 `PENDING`일 수 있다
- 느린 처리일 뿐인데 뒤 요청이 너무 빨리 takeover하면 중복 side effect가 난다

그래서 초보자 규칙은 이것이다.

> "오래 걸려 보인다"와 "안전하게 버려졌다"는 같은 뜻이 아니다.

## `in-progress`로 남겨야 하는 경우

아래 중 하나라도 맞으면 기존 row를 계속 `in-progress`로 보는 쪽이 기본값이다.

### 1. 최근 heartbeat가 있다

예:

- `last_heartbeat_at`이 최근 5초 전
- 허용 idle budget이 30초

이 경우 timeout이 아니라 **정상 처리 중**으로 보는 것이 맞다.

### 2. lease가 아직 안 끝났다

예:

- `lease_expires_at = 10:00:30`
- 현재 시각 `10:00:12`

이 경우 ownership은 아직 원래 worker에게 있다.

### 3. owner/fencing token이 아직 현재 값이다

예:

- row에 `owner_id = worker-a`, `fencing_token = 18`
- worker-a가 여전히 lease holder다

이때 다른 worker가 `PENDING`만 보고 바로 상태를 뒤집으면 stale writer 사고가 난다.

### 4. commit outcome이 불명확한데 결과 조회가 아직 안 됐다

예:

- 앱은 timeout을 봤다
- 하지만 외부 결제사나 downstream ledger는 성공했을 수 있다

이때 recovery보다 먼저 할 일은 **결과 조회**다.

## takeover/recovery가 비교적 안전한 경우

초보자에게 가장 중요한 조건은 "느려 보임"이 아니라 **명시적 소유권 만료**다.

아래 조건이 함께 있을 때만 takeover를 검토한다.

### 1. liveness 기준이 문서화돼 있다

예:

- `lease_expires_at`
- `last_heartbeat_at`
- `attempt_owner`
- `version` 또는 `fencing_token`

이 중 최소 하나는 있어야 "정말 abandoned인지"를 판단할 수 있다.

### 2. stale 판단 기준이 숫자로 있다

예:

- heartbeat 3회 miss
- `lease_expires_at < now()`
- `updated_at`만 보지 않고, owner heartbeat 기준으로 stale 판단

`updated_at` 하나만 보고 "오래됐네"라고 takeover하는 것은 beginner 금지에 가깝다.

### 3. takeover가 compare-and-swap로 이뤄진다

안전한 recovery는 "읽고 감으로 덮어쓰기"가 아니라 조건부 update다.

예:

```sql
UPDATE api_idempotency
SET owner_id = :new_owner,
    lease_expires_at = :new_lease,
    recovery_count = recovery_count + 1
WHERE idempotency_key = :key
  AND status = 'PENDING'
  AND owner_id = :old_owner
  AND lease_expires_at < NOW();
```

핵심은 이것이다.

- 내가 본 오래된 owner가 아직 그대로인지 다시 확인한다
- 중간에 원래 worker가 살아났으면 takeover update가 실패해야 한다

### 4. external side effect 재진입 규칙이 있다

recovery가 안전하려면 아래 중 하나가 필요하다.

- 외부 호출 자체가 멱등적이다
- 외부 결과 조회 API가 있다
- outbox/inbox처럼 이미 보낸 효과를 다시 확인할 수 있다

없다면 `PENDING` recovery는 DB row 갱신이 아니라 **중복 side effect 위험**이 된다.

## beginner용 안전/위험 비교표

| 판단 기준 | 안전한 편 | 위험한 편 |
|---|---|---|
| stale 판정 | `lease_expires_at`, `last_heartbeat_at` 같은 명시 필드 | 그냥 `updated_at`이 오래됨 |
| ownership 교체 | compare-and-swap update | 읽은 뒤 무조건 overwrite |
| side effect 재진입 | 조회 가능, 멱등 key 있음 | 결과 조회 없이 재호출 |
| 응답 계약 | 당장은 `in-progress`, 나중에 recovery worker가 정리 | 사용자 재시도마다 즉시 takeover |

## 간단한 상태 흐름 예시

```text
1. 요청 A가 row를 만들고 status='PENDING'으로 claim
2. worker-a가 owner가 되고 lease_expires_at=10:00:30 설정
3. 요청 B가 같은 key로 들어옴
4. B는 row를 읽음
5. 현재 시각이 10:00:12면 -> 아직 lease 유효 -> in-progress 응답
6. 현재 시각이 10:01:10이고 owner heartbeat도 stale면 -> recovery 후보
7. B 또는 recovery worker는 compare-and-swap takeover 시도
8. takeover 성공 후에만 결과 조회 또는 재처리 진행
```

포인트는 두 가지다.

- `PENDING`만 보고 바로 6번으로 가면 안 된다
- takeover 성공 전에는 "내가 새 owner다"라고 가정하면 안 된다

## 추천 응답 계약

기존 `PENDING` row를 보고도 recovery가 아직 안전하지 않다면, API 응답은 보통 보수적으로 간다.

| 상황 | 추천 기본 응답 |
|---|---|
| lease 유효 / heartbeat 최근 | `202 Accepted` 또는 `409 in-progress` |
| stale 의심이지만 takeover 규칙 없음 | 여전히 `in-progress`, 내부 복구 큐/운영 경보 후보 |
| safe takeover 성공 후 최종 결과 확인됨 | replay 또는 새 final result |
| same key, different hash | `409 Conflict` |

초보자 기준에서는 사용자 요청 handler가 직접 복잡한 recovery를 다 하기보다, **일단 `in-progress`로 닫고 별도 recovery worker가 정리**하는 편이 더 안전한 경우가 많다.

## 자주 하는 오해

- "`PENDING`이 오래됐으니 무조건 죽은 row다"
  - 아니다. 느린 외부 호출일 수도 있다.
- "`updated_at`만 오래되면 takeover해도 된다"
  - 아니다. heartbeat/lease 같은 ownership 신호가 더 중요하다.
- "takeover는 `status='PENDING'`만 확인하면 된다"
  - 아니다. owner/version/lease를 함께 비교해야 한다.
- "복구니까 그냥 다시 실행해도 된다"
  - 아니다. 외부 side effect가 이미 나갔을 수 있다.
- "`PENDING` recovery는 API 응답 계약과 무관하다"
  - 아니다. recovery가 불확실하면 사용자에게는 `in-progress`를 주는 것이 더 정확할 수 있다.

## 이 문서를 떠올릴 순간

- "같은 idempotency key 재시도에서 기존 row가 계속 `PENDING`이다"
- "언제까지는 `PROCESSING`으로 돌려주고, 언제 `PENDING` row takeover를 할지 헷갈린다"
- "stale row recovery를 만들고 싶은데 `updated_at`만으로 충분한지 모르겠다"
- "retry handler가 직접 재처리해야 하는지, recovery worker로 넘겨야 하는지 헷갈린다"

## 한 줄 정리

기존 `PENDING` idempotency row는 **살아 있는 owner 신호가 남아 있으면 `in-progress`로 유지**하고, **lease/heartbeat 만료 + compare-and-swap ownership 교체 + side effect 재진입 안전성**이 있을 때만 recovery/takeover를 허용하는 것이 beginner 기본값이다.
