# Striped Guard Row Rebalance Basics

> 한 줄 요약: striped guard row에서 refill/rebalance는 "빠른 승인 경로"가 아니라 "가끔 예산을 옮기는 느린 경로"로 분리해야 하고, 초보자는 `hot path는 local budget만 본다`, `rebalance는 budget만 옮긴다`, `이동은 작은 범위와 고정 순서로 잠근다` 이 세 규칙부터 지키면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Striped Guard Row Budgeting Primer](./striped-guard-row-budgeting-primer.md)
- [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md)
- [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: striped guard row rebalance basics, striped guard row refill basics, bucket budget refill beginner, bucket rebalance beginner, low frequency refill path, low frequency rebalance path, avoid global lock hot path, local budget only, refill worker primer, rebalance worker primer, striped guard slow path, budget transfer beginner, bucket headroom refill, guard row rebalance rules, striped guard no global lock, striped budget transfer order, hot path local budget, background refill concurrency

## 핵심 개념

먼저 striped guard row를 "창구 여러 개"로 생각하면 쉽다.

- hot path는 각 창구가 자기 잔액만 보고 손님을 받는다
- refill/rebalance는 관리자가 가끔 창구 사이 예산을 옮긴다

문제가 되는 순간은 관리자가 창구를 돕겠다고 **매 손님마다 중앙 금고를 다시 열어 보는 경우**다.

- 승인마다 전체 bucket 합을 다시 계산
- 빈 bucket을 찾으려고 여러 bucket을 순회
- 부족하면 즉석에서 전 bucket을 잠그고 재배분

이렇게 하면 striping을 넣었어도 결국 **전역 잠금이 다른 이름으로 돌아온다**.

초보자용 핵심 기준은 단순하다.

> refill/rebalance는 "자주 오는 요청을 통과시키는 메인 문"이 아니라, "가끔 예산을 정리하는 옆문"이어야 한다.

## 왜 refill/rebalance가 필요한가

local budget으로만 승인하면 장점이 크다.

- 승인 SQL이 bucket 1개만 보면 된다
- lock wait가 여러 bucket으로 분산된다
- 패배 이유를 bucket-local 부족으로 설명할 수 있다

대신 시간이 지나면 이런 현상이 생길 수 있다.

- bucket `0`은 꽉 찼는데 bucket `3`은 남아 있다
- 특정 hash key가 한 bucket으로 더 자주 몰린다
- 총 capacity는 남았지만 일부 bucket은 stranded headroom이 된다

이때 필요한 것이 refill/rebalance다.
하지만 이 작업은 **낮은 빈도로**, **작은 범위만**, **hot path 밖에서** 해야 한다.

## 먼저 기억할 세 규칙

| 규칙 | 초보자용 뜻 | 왜 중요한가 |
|---|---|---|
| hot path는 local budget만 본다 | 승인 요청은 자기 bucket `budget_qty`와 `reserved_qty`만 본다 | 매 요청마다 중앙 합산을 하면 striping 이점이 사라진다 |
| rebalance는 reservation이 아니라 budget을 옮긴다 | 보통 `reserved_qty`를 억지로 옮기지 말고 `budget_qty`를 조정한다 | 이미 어떤 bucket에 기록된 점유의 소유권을 흔들지 않게 된다 |
| 이동은 작은 범위를 고정 순서로 잠근다 | source/destination bucket 몇 개만 정해진 순서로 잠근다 | refill path가 새 deadlock과 전역 대기를 만들지 않게 된다 |

이 세 줄만 지켜도 "hot-path global locking 재도입" 위험을 크게 줄일 수 있다.

## mental model: 승인 경로와 정리 경로를 분리한다

| 경로 | 언제 실행되나 | 만지는 범위 | 초보자 기본값 |
|---|---|---|---|
| acquire hot path | 거의 모든 요청 | bucket 1개 | local budget만 본다 |
| release path | 취소, 만료, 확정 취소 | 원래 bucket 1개 | 저장된 `bucket_id`만 만진다 |
| refill/rebalance slow path | 가끔, 운영/worker 기준 | bucket 2개 또는 작은 상수 | 작은 이동만 하고 끝낸다 |

핵심은 `slow path`가 `fast path`를 대신하지 않는다는 점이다.

- 승인 실패를 만날 때마다 즉석 rebalance를 호출하지 않는다
- 재시도 요청이 refill worker 역할을 대신하지 않는다
- 사용자 트랜잭션 안에서 전 bucket 조정까지 끝내려 하지 않는다

## beginner-safe refill 규칙

### 1. refill 트리거는 "매 실패"가 아니라 "관측된 쏠림"이어야 한다

안전한 시작점:

- 주기 worker가 10초, 30초, 1분 단위로 본다
- 또는 특정 bucket의 부족 비율이 한동안 반복될 때만 본다

피해야 할 시작점:

- acquire가 한 번 실패할 때마다 즉시 global refill
- p99가 조금 오를 때마다 요청 스레드가 직접 rebalance
- "비어 보이는 bucket 탐색"을 모든 요청에서 수행

처음에는 약간의 stranded headroom을 받아들이는 편이 더 안전하다.
초보자 단계에서는 "모든 빈 자리를 즉시 활용"보다 "hot path를 단순하게 유지"가 더 중요하다.

### 2. refill은 budget만 옮기고 active claim은 옮기지 않는다

예를 들어 bucket 상태가 아래와 같다고 하자.

| bucket_id | budget_qty | reserved_qty | 남은 자리 |
|---|---:|---:|---:|
| `0` | `3` | `3` | `0` |
| `1` | `3` | `1` | `2` |
| `2` | `2` | `1` | `1` |
| `3` | `2` | `0` | `2` |

이때 beginner 기본값은:

- bucket `1`이나 `3`에서 남는 `budget_qty` 일부를 bucket `0` 쪽으로 옮긴다
- 이미 bucket `1`에 기록된 claim의 `bucket_id`는 바꾸지 않는다

왜냐하면 active claim을 다른 bucket으로 재배치하기 시작하면:

- release가 어느 bucket에서 일어나야 하는지 흔들리고
- 중복 release, 누락 release 위험이 커지고
- detail row/ledger와 summary의 소유권 모델이 복잡해진다

즉 refill의 1차 목표는 **점유 재배치**가 아니라 **미래 승인 여지 조정**이다.

### 3. refill 한 번에 bucket 2개 또는 작은 상수만 만진다

초보자용 기본형은 보통 이렇다.

1. donor bucket 하나를 고른다
2. receiver bucket 하나를 고른다
3. 둘만 잠그고 소량 budget을 이동한다
4. 끝낸다

이 방식이 좋은 이유:

- 락 범위가 작다
- deadlock 설명이 쉽다
- 실패해도 영향 범위를 좁게 유지할 수 있다

반대로 한 번에 전 bucket을 모두 잠그는 방식은 "가끔만 하니까 괜찮다"라고 생각하기 쉽지만, 실제로는 인기 key에서 긴 정지 구간을 만들 수 있다.

## hot-path global lock을 다시 들이지 않는 규칙

| 위험한 접근 | 왜 다시 중앙 잠금이 되는가 | beginner-safe 대안 |
|---|---|---|
| acquire 실패 시 전 bucket `SUM` 후 재시도 | 모든 실패 요청이 같은 중앙 계산으로 몰린다 | 실패는 그냥 reject하고 refill은 별도 worker가 본다 |
| 가장 여유 있는 bucket을 찾으려고 매 요청마다 전 bucket 탐색 | read fan-in이 다시 hot path로 들어온다 | stable home bucket 1개만 먼저 본다 |
| refill 때 전 bucket을 한 트랜잭션으로 잠금 | 느린 경로가 전체 key를 멈춘다 | donor/receiver 소수 bucket만 잠근다 |
| rebalance를 release/acquire 요청 스레드가 직접 수행 | 사용자 요청 지연이 운영 정리 작업과 섞인다 | 백그라운드 worker 또는 운영 루틴으로 분리한다 |

한 문장으로 줄이면:

> "지금 이 요청을 통과시키려고 중앙 판단을 다시 붙이는 순간" striping의 이점이 약해진다.

## 가장 단순한 refill 예시

아래 예시는 개념 설명용이다.

```sql
SELECT campaign_id, bucket_id, budget_qty, reserved_qty
FROM campaign_guard_bucket
WHERE campaign_id = :campaign_id
  AND bucket_id IN (:donor_bucket_id, :receiver_bucket_id)
FOR UPDATE;

UPDATE campaign_guard_bucket
SET budget_qty = CASE
  WHEN bucket_id = :donor_bucket_id THEN budget_qty - :move_qty
  WHEN bucket_id = :receiver_bucket_id THEN budget_qty + :move_qty
END
WHERE campaign_id = :campaign_id
  AND bucket_id IN (:donor_bucket_id, :receiver_bucket_id);
```

초보자용 주의점:

- `donor_bucket_id`, `receiver_bucket_id`는 항상 같은 정렬 규칙으로 잠근다
- `move_qty`는 작게 시작한다
- donor의 `budget_qty - reserved_qty`보다 많이 옮기지 않는다
- 이 SQL을 acquire 실패 경로 안에 넣지 않는다

## refill과 rebalance를 다르게 본다

초보자에게는 두 용어를 이렇게 구분해 두면 편하다.

| 용어 | 쉬운 뜻 | beginner 기본 해석 |
|---|---|---|
| refill | 비어 있는 bucket에 headroom을 조금 채워 주는 작업 | 당장 부족한 bucket을 살짝 도와주는 수준 |
| rebalance | bucket 전체 배분을 다시 맞추는 작업 | refill보다 드물고 더 운영성 있는 작업 |

실무에서는 두 단어가 섞여 쓰이기도 하지만, beginner 관점에서는:

- refill은 더 작고 자주
- rebalance는 더 크고 드물게

로 기억하면 설계가 덜 흔들린다.

## 자주 헷갈리는 질문

| 질문 | 짧은 답 |
|---|---|
| "총 capacity가 남았는데 왜 바로 승인하지 않죠?" | striped guard의 목표는 총합 활용 최대화보다 hot path 분산이다. 약간의 stranded headroom은 의도된 trade-off다 |
| "refill을 acquire 안에 넣으면 reject가 줄지 않나요?" | 줄 수는 있지만, 그 대신 모든 실패가 중앙 조정으로 몰려 다시 hotspot을 만든다 |
| "`reserved_qty`를 bucket 간에 옮기면 더 깔끔하지 않나요?" | release 소유권과 detail row 정합성이 어려워져 초보자 단계에서 위험하다 |
| "모든 bucket을 읽기만 하는 것은 괜찮지 않나요?" | 읽기 fan-in도 충분히 뜨거우면 병목이 된다. 특히 실패가 많은 순간 더 그렇다 |

## 시작 규칙 5개

1. acquire는 home bucket 1개만 먼저 본다.
2. local budget으로 승인하고 global sum을 hot path에서 계산하지 않는다.
3. refill/rebalance는 background worker나 운영 루틴으로 분리한다.
4. budget 이동은 donor/receiver 작은 집합만 같은 순서로 잠근다.
5. active claim의 `bucket_id`는 바꾸지 않고 release는 원래 bucket에서만 한다.

이 다섯 줄이면 beginner가 striped guard row를 유지보수 가능한 수준으로 시작하는 데 충분하다.

## 다음에 이어서 볼 문서

- striped guard row의 기본 bookkeeping부터 다시 보고 싶으면 → [Striped Guard Row Budgeting Primer](./striped-guard-row-budgeting-primer.md)
- 단일 guard row가 언제 hot row로 뒤집히는지 먼저 보려면 → [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md)
- refill/rebalance보다 더 근본적으로 다른 mitigation을 비교하려면 → [Guard-Row Hot-Row Contention Mitigation](./hot-row-contention-counter-sharding.md)
- retry/재시도 경계와 함께 보고 싶다면 → [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)

## 한 줄 정리

striped guard row에서 refill/rebalance는 "모든 실패를 그때그때 구해 주는 중앙 구조"가 아니라 "가끔 bucket 예산을 옮겨 주는 느린 정리 경로"여야 한다. hot path는 local budget만 보고, slow path는 budget만 소량 이동시키는 것이 beginner-safe 기본값이다.
