# Single Counter vs Ledger vs Slot Inventory Oversell Decision Card

> 한 줄 요약: `마지막 재고가 두 번 팔려요`가 보이면 먼저 single counter, append-only claim row, slot inventory 중 어느 모델인지 나눠야 guard row와 retry 문서를 덜 헷갈리고 읽을 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Lost Update vs Oversell vs Duplicate Insert Beginner Bridge](./lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge.md)
- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)
- [database 카테고리 인덱스](./README.md)
- [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)

retrieval-anchor-keywords: single counter vs ledger vs slot inventory, oversell decision card, inventory model beginner, 마지막 재고가 두 번 팔려요, 재고 모델 뭐로 나눠요, guard row 전에 뭐 봐요, append-only claim row basics, ledger inventory beginner, slot inventory beginner, counter row oversell, reservation ledger what is, slot claim what is, 처음 inventory locking, 헷갈리는 oversell 모델

## 핵심 개념

oversell은 "재고가 부족한데도 성공했다"는 결과 증상이고, 그 안의 저장 모델은 서로 다를 수 있다.

- **single counter**: `stock = 3` 같은 숫자 row를 직접 줄인다
- **append-only claim row**: 예약/hold/claim row를 계속 쌓고 합계를 계산한다
- **slot inventory**: 하루나 30분 slot처럼 잘게 쪼갠 key별로 점유 row를 만든다

초보자에게 중요한 질문은 "`어떤 SQL을 쓰나`"보다 "`재고 truth가 한 row 숫자인가, 여러 claim 합계인가, slot 집합인가`"다. 이걸 먼저 나누면 guard row가 필요한 이유도 훨씬 직관적으로 보인다.

## 한눈에 보기

| 모델 | 재고 truth가 있는 곳 | oversell이 보이는 전형적 장면 | 첫 대응 |
|---|---|---|---|
| single counter | `inventory.stock` 같은 한 row | 둘 다 `stock > 0`를 보고 차감해서 `-1` 또는 덜 차감 | 조건부 `UPDATE`, version CAS, row lock |
| append-only claim row | `SUM(qty)` 또는 active claim count | 각 row는 멀쩡한데 총합이 capacity를 넘김 | guard row, serializable retry, reconciliation |
| slot inventory | `resource_id + day/slot`별 claim row | 특정 날짜/시간 slot이 중복 점유됨 | slot `UNIQUE`, slot guard, union lock |

짧은 기억법:

- 숫자 하나를 직접 깎으면 single counter
- 이벤트/claim을 쌓아 합치면 ledger
- 시간을 칸으로 쪼개 점유하면 slot inventory

## 먼저 이렇게 고른다

| 먼저 던질 질문 | `yes`면 | `no`면 |
|---|---|---|
| 재고 truth가 `stock=9` 같은 **한 row 숫자**인가 | single counter부터 본다 | 다음 질문으로 |
| 성공한 주문/hold/claim row를 **합쳐서** 재고를 계산하나 | ledger inventory부터 본다 | 다음 질문으로 |
| 예약 범위를 day/slot 같은 **칸 집합**으로 펼치나 | slot inventory부터 본다 | guard row나 범위 invariant 문서로 간다 |

여기서 중요한 건 이름보다 shape다. `reservation`, `booking`, `inventory`라는 테이블 이름은 달라도, 실제 truth가 어디 있느냐가 같으면 같은 종류 문제로 읽는다.

## single counter를 먼저 보는 경우

single counter는 가장 익숙한 모델이다.

```sql
UPDATE inventory
SET stock = stock - 1
WHERE item_id = :id
  AND stock > 0;
```

이 모델에서 oversell이 나는 흔한 이유는:

- `SELECT stock` 후 애플리케이션에서 빼고 저장해서 same-row race가 남음
- 차감은 했지만 `stock > 0` 같은 조건이 write 시점에 다시 확인되지 않음

초보자 첫 대응은 단순하다. 숫자 row 하나를 **한 번의 조건부 write**로 닫을 수 있는지부터 본다. 이게 되면 guard row까지 갈 필요가 없는 경우가 많다.

## append-only claim row를 먼저 보는 경우

ledger inventory는 `stock`을 직접 깎기보다 `hold`, `reserve`, `confirm`, `cancel` row를 쌓고 active 합계를 truth로 본다.

예:

- 쿠폰 발급 수량을 claim row 개수로 센다
- room-type inventory를 stay-day claim 합계로 센다
- 주문당 `qty_delta` 이벤트를 더해 남은 수량을 계산한다

이 모델은 개별 row가 정상이어도 **합계 invariant**가 샐 수 있다. 그래서 `SELECT COUNT(*)`나 `SUM(qty)` 뒤 insert하는 경로만 있으면 oversell이 잘 난다.

이때 beginner safe next step은 "`합계를 누가 직렬화하나`"를 보는 것이다. 대표 row 하나로 줄 세우면 guard row, 쿼리 기반 충돌을 DB가 밀어내게 하면 serializable retry 쪽으로 내려간다.

## slot inventory를 먼저 보는 경우

slot inventory는 애매한 시간 범위를 작은 exact key 집합으로 바꾼다.

예:

- 회의실 `10:00~11:00`를 `10:00`, `10:30` slot claim으로 펼침
- 숙박 `2박`을 `stay_day` 2개로 펼침
- 좌석 재고를 `seat_id + show_slot`으로 고정

장점은 conflict를 `duplicate key`나 slot-level lock으로 더 명확하게 볼 수 있다는 점이다. 대신 move, extend, cancel에서는 `old slots ∪ new slots`를 함께 다뤄야 하므로 slot 수가 늘수록 모델이 복잡해진다.

즉 slot inventory는 single counter의 확장판이 아니라, **범위를 discrete key 집합으로 바꾼 별도 모델**이다.

## 흔한 오해와 함정

- "`재고` 테이블이 있으니 무조건 single counter죠?"
  - 아니다. 실제 승인 기준이 claim 합계면 ledger inventory다.
- "append-only ledger면 무조건 안전하죠?"
  - 아니다. append-only는 기록 방식일 뿐이고, admission을 누가 막는지는 별도다.
- "slot inventory는 row만 많아진 single counter 아닌가요?"
  - 아니다. slot의 핵심은 각 칸이 별도 truth가 되고 reschedule이 union problem으로 바뀐다는 점이다.
- "guard row는 언제나 필요한 상위 해법이죠?"
  - 아니다. single counter는 조건부 update만으로 닫힐 수 있고, slot inventory는 slot `UNIQUE`만으로 충분할 수도 있다.

## 실무에서 쓰는 모습

| 장면 | 더 가까운 모델 | 왜 그렇게 보나 |
|---|---|---|
| 상품 재고 한 줄 `stock=1` 차감 | single counter | 숫자 하나가 truth다 |
| 쿠폰 100장 한도를 active issue row 합계로 계산 | append-only claim row | row를 쌓은 뒤 count가 truth다 |
| 숙박 3박 예약을 날짜별 availability로 점유 | slot inventory | 각 `stay_day`가 점유 truth다 |

이 표를 먼저 잡고 나면 다음 문서도 자연스럽다.

- single counter면 locking read보다 조건부 update 문서를 먼저 본다
- ledger inventory면 guard row와 reconciliation 문서로 간다
- slot inventory면 slot claim, guard scope, reschedule 문서로 간다

## 더 깊이 가려면

- oversell이 lost update인지부터 헷갈리면 [Lost Update vs Oversell vs Duplicate Insert Beginner Bridge](./lost-update-vs-oversell-vs-duplicate-insert-beginner-bridge.md)
- exact key, slot row, guard row 중 충돌 surface를 고르려면 [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- multi-day booking에서 guard row key를 어떻게 잡는지 보려면 [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- pooled inventory + ledger + later assignment를 함께 보려면 [Shared-Pool Guard Design for Room-Type Inventory](./shared-pool-guard-design-room-type-inventory.md)
- 시스템 설계 관점에서 예약 inventory 흐름을 넓게 보려면 [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)

## 면접/시니어 질문 미리보기

> Q: oversell 문서를 읽기 전에 왜 inventory model부터 나누나요?
> 의도: anomaly 이름보다 storage truth를 먼저 잡는지 확인
> 핵심: 같은 oversell이라도 counter, claim sum, slot set은 충돌 surface와 해법이 다르기 때문이다.

> Q: append-only claim row와 slot inventory의 차이는 뭔가요?
> 의도: "row를 많이 쌓는다"를 같은 말로 뭉개지 않는지 확인
> 핵심: claim row는 보통 aggregate count/sum이 truth이고, slot inventory는 각 discrete slot key 자체가 truth다.

> Q: guard row는 언제 읽기 시작하면 좋나요?
> 의도: 해법을 너무 일찍 고르지 않는지 확인
> 핵심: 단일 숫자 row인지 아닌지를 먼저 분리한 뒤, ledger나 slot에서 합계/범위 arbitration이 남을 때 들어가는 편이 안전하다.

## 한 줄 정리

`마지막 재고가 두 번 팔려요`를 보면 먼저 재고 truth가 숫자 한 줄인지, claim 합계인지, slot 집합인지 나누고 그다음에야 guard row, slot claim, retry 문서로 내려가야 덜 헷갈린다.
