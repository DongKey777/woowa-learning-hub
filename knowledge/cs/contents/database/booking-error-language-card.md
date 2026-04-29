# Booking Error Language Card

> 한 줄 요약: 예약 경로에서 `duplicate key`, `23P01`, `lock timeout`, `deadlock`이 보이면 "이미 같은 요청이 있다", "이미 겹치는 시간대가 있다", "지금 줄이 길다", "이번 시도만 다시 하면 된다"로 먼저 번역하면 제품 문장과 재시도 정책이 덜 흔들린다.

**난이도: 🟢 Beginner**

관련 문서:

- [PostgreSQL `23P01` vs `23505` Product Language Card](./postgresql-23p01-vs-23505-product-language-card.md)
- [Duplicate Key vs Busy Response Mapping](./duplicate-key-vs-busy-response-mapping.md)
- [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- [Constraint-First Booking Primer](./constraint-first-booking-primer.md)
- [database 카테고리 인덱스](./README.md)
- [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)

retrieval-anchor-keywords: booking error language card, booking duplicate key 23p01 lock timeout deadlock, 예약 오류 문구 처음, booking duplicate key 뭐예요, 23p01 already booked why, lock timeout 예약 바쁨, deadlock retry booking basics, beginner booking conflict primer, 예약 중복 락 타임아웃 차이, product wording duplicate overlap timeout deadlock, booking error message what is, booking sqlstate language intro

## 핵심 개념

예약에서 에러 이름을 그대로 사용자 문장으로 옮기면 초보자가 가장 먼저 헷갈린다.

- `duplicate key`: 같은 요청 키나 같은 slot key를 누가 먼저 차지했다
- `23P01`: 같은 room/day/time range를 다른 예약이 이미 겹치게 차지했다
- `lock timeout`: 누가 이겼는지 확인하기 전에 줄 서다 이번 시도가 끝났다
- `deadlock`: 줄을 서로 반대로 잡아서 이번 시도 하나만 희생됐다

이 문서는 "`예약 저장에서 duplicate key, 23P01, lock timeout, deadlock 차이가 뭐예요?`" 같은 질문에 바로 답하는 entrypoint다.

짧게 기억하면:

> duplicate key = 같은 열쇠가 이미 있음
> `23P01` = 같은 시간대가 이미 겹침
> lock timeout = 아직 줄이 안 빠짐
> deadlock = 이번 판만 다시

## 한눈에 보기

| DB 신호 | 예약에서 먼저 읽을 뜻 | 학습자/사용자에게 가까운 문장 | 기본 처리 방향 |
|---|---|---|---|
| `duplicate key`, PostgreSQL `23505`, MySQL `1062` | 같은 요청 키나 같은 slot key winner가 이미 있다 | `이미 같은 예약 요청이 처리되었습니다.` | winner read 후 replay 또는 `already exists` |
| PostgreSQL `23P01` | 겹치는 예약 시간이 이미 있다 | `선택한 시간대에 이미 예약이 있습니다.` | retry보다 `conflict`로 닫기 |
| `lock timeout`, PostgreSQL `55P03`, MySQL `1205` | 예약 결론을 보기 전에 오래 막혔다 | `지금 예약이 몰려 잠시 후 다시 시도해 주세요.` | `busy`로 분류, blocker/queue 확인 |
| `deadlock`, PostgreSQL `40P01`, MySQL `1213` | 순환 대기 때문에 이번 시도만 깨졌다 | 보통 사용자에겐 내부 재시도 후 결과만 보여 준다 | whole-transaction bounded retry |

핵심은 하나다.

`duplicate key`와 `23P01`은 둘 다 "이미 다른 누군가가 자리를 차지했다"에 가깝지만, `duplicate key`는 **같은 키 중복**, `23P01`은 **겹치는 시간 충돌**이라는 점이 다르다. 반대로 `lock timeout`과 `deadlock`은 아직 최종 상태를 사용자 문장으로 확정하기보다 `busy` 또는 `retryable`로 먼저 읽는 편이 안전하다.

## 상세 분해

### 1. `duplicate key`: 같은 예약 요청이 이미 있다

대표 장면:

- 같은 `idempotency_key`로 재전송했다
- slot table에서 같은 `(room_id, slot_start)`를 두 요청이 동시에 넣었다

예약 문장은 보통 이렇게 간다.

- `이미 처리된 예약 요청입니다.`
- `이미 같은 좌석/슬롯이 선점되었습니다.`

여기서 질문은 "겹치는 시간대인가?"보다 **"같은 key winner가 이미 있나?"** 다.

### 2. `23P01`: 같은 시간대가 이미 겹친다

대표 장면:

- 기존 예약: `10:00~11:00`
- 새 예약: `10:30~11:30`
- PostgreSQL exclusion constraint가 overlap을 막음

예약 문장은 보통 이렇게 간다.

- `선택한 시간대에 이미 예약이 있습니다.`
- `겹치는 예약이 있어 저장할 수 없습니다.`

여기서 중요한 점은 key가 달라도 에러가 날 수 있다는 것이다. 그래서 `23P01`을 `중복 키`로만 번역하면 예약 도메인에서는 거의 항상 오해를 만든다.

### 3. `lock timeout`: 이미 찼다는 뜻이 아니라 줄이 길다는 뜻

대표 장면:

- 앞선 요청이 guard row나 booking row를 오래 잡고 있다
- 후행 요청이 기다리다 timeout budget을 다 썼다

예약 문장은 보통 이렇게 간다.

- `현재 예약 요청이 몰려 잠시 후 다시 시도해 주세요.`
- `지금은 처리 지연이 있어 예약을 완료하지 못했습니다.`

즉 `lock timeout`은 "이미 예약이 있다"가 아니라 **"이번 시도에서는 확인을 못 끝냈다"** 에 가깝다.

### 4. `deadlock`: 이번 시도만 다시 하면 되는 경우가 많다

대표 장면:

- 예약 변경 경로가 old slot -> new slot 순서로 잠근다
- 다른 경로가 new slot -> old slot 순서로 잠근다
- DB가 순환 대기를 감지하고 한쪽을 victim으로 고른다

이 경우 사용자에게 바로 `이미 예약이 있습니다`라고 말하면 틀릴 수 있다. 실제로는 겹침이 아니라 **락 순서 충돌**일 수 있기 때문이다. 보통은 서버가 짧게 내부 재시도한 뒤 성공/실패 결과만 보여 주는 편이 낫다.

## 흔한 오해와 함정

- `23P01`도 class `23`이니까 `duplicate key`와 같은 문장으로 보내도 된다
  - 아니다. 예약 도메인에서는 key 중복이 아니라 시간대 겹침을 말해야 한다.
- `lock timeout`이면 누군가 이미 예약을 끝냈다고 봐도 된다
  - 아니다. winner를 확인하기 전에 기다리다 끝난 것일 수 있다.
- `deadlock`도 결국 실패했으니 `이미 예약이 있습니다`로 닫아도 된다
  - 아니다. 같은 재시도 한 번으로 성공할 수 있는 `retryable`일 수 있다.
- `duplicate key`가 보이면 무조건 사용자 잘못이다
  - 아니다. 같은 멱등 요청 재전송이면 기존 성공 replay가 더 자연스럽다.

## 실무에서 쓰는 모습

회의실 예약 API를 예로 들면 아래처럼 나누면 된다.

| 장면 | 내부 신호 | 제품/서비스 첫 문장 |
|---|---|---|
| 같은 `idempotency_key` 재전송 | `duplicate key` | `이미 처리된 예약 요청입니다.` |
| 다른 사람이 같은 시간대를 먼저 선점 | `23P01` | `선택한 시간대에 이미 예약이 있습니다.` |
| 퇴실 정리 배치가 row를 오래 잡아 후행 요청이 기다리다 종료 | `lock timeout` | `지금 예약이 몰려 잠시 후 다시 시도해 주세요.` |
| 예약 변경과 취소가 락 순서를 엇갈리게 잡음 | `deadlock` | 내부 재시도 후 성공이면 정상 응답, 실패면 일시 장애 문장 |

제품 문장만 먼저 고정하면 서비스 동작도 따라오기 쉽다.

- `duplicate key`: replay 가능한지 본다
- `23P01`: 다른 시간 제안을 하거나 conflict로 닫는다
- `lock timeout`: 혼잡 완화나 짧은 재시도 budget을 본다
- `deadlock`: whole-transaction retry와 canonical lock ordering을 본다

## 더 깊이 가려면

- `23P01`과 `23505`를 제품 문장 기준으로 더 정확히 나누려면 [PostgreSQL `23P01` vs `23505` Product Language Card](./postgresql-23p01-vs-23505-product-language-card.md)
- `lock timeout`을 왜 `already exists`가 아니라 `busy`로 읽는지 짧게 고정하려면 [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- 예약 모델을 slot/constraint/guard row 관점에서 먼저 고르려면 [Constraint-First Booking Primer](./constraint-first-booking-primer.md)
- 예약 흐름 전체를 시스템 설계 관점에서 보고 싶으면 [Inventory Reservation System Design](../system-design/inventory-reservation-system-design.md)

## 한 줄 정리

예약 경로에서 `duplicate key`, `23P01`, `lock timeout`, `deadlock`을 보면 "같은 요청 중복", "시간대 겹침", "혼잡으로 대기 종료", "이번 시도만 재시도"로 먼저 번역해야 제품 문장과 처리 전략이 함께 안정된다.
