# Lost Update vs Oversell vs Duplicate Insert Beginner Bridge

> 한 줄 요약: `마지막 재고가 두 번 팔렸다`는 말 하나만으로는 lost update, oversell, duplicate insert를 구분할 수 없고, beginner는 먼저 "같은 row가 덮였나 / 합계 규칙이 깨졌나 / 같은 key row가 두 번 생기려 했나"를 나눠야 다음 락 문서를 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [락 기초](./lock-basics.md)
- [Single Counter vs Ledger vs Slot Inventory Oversell Decision Card](./single-counter-vs-ledger-vs-slot-inventory-oversell-decision-card.md)
- [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
- [Spring @Transactional 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: lost update vs oversell vs duplicate insert, oversell beginner, duplicate insert beginner, 마지막 재고 두 번 팔렸어요, 재고가 왜 음수가 돼요, 같은 insert가 두 번 들어가요, what is lost update, beginner locking primer, 처음 락 문서 보기 전에, 헷갈리는 동시성 증상, same row overwrite, count invariant break, unique key duplicate, basics concurrency symptom map

## 핵심 개념

초보자는 에러 이름보다 **겉으로 보이는 증상**부터 먼저 본다. 그런데 `재고가 이상하다`는 증상 하나 안에 서로 다른 문제가 섞여 있다.

- **lost update**: 같은 row를 둘 다 읽고, 둘 다 저장해서 앞선 변경이 덮여 사라진다
- **oversell**: 남은 수량, 좌석 수, capacity 같은 합계 규칙이 깨져서 결과가 0 아래로 가거나 허용치를 넘는다
- **duplicate insert**: "없으면 만든다" 경로에서 같은 key row를 두 요청이 동시에 만들려 한다

한 줄 기억법:

- 같은 row가 조용히 덮였으면 lost update
- 총량 규칙이 깨졌으면 oversell
- 같은 key row를 두 번 만들려다 `duplicate key`가 났으면 duplicate insert

## 한눈에 보기

| 지금 보이는 장면 | 먼저 의심할 것 | 왜 다른가 | 첫 대응 |
|---|---|---|---|
| 최종 stock이 `9`인데 실제로는 두 번 팔려 `8`이어야 한다 | lost update | 같은 row 최종 write가 서로를 덮었다 | atomic `update`, version CAS, row lock |
| stock이 `-1`이 되거나 capacity 10인데 11건이 성공했다 | oversell | 합계/수량 규칙이 저장 시점에 닫히지 않았다 | 조건부 update, guard row, slot/ledger |
| `(user_id, coupon_id)` 같은 key insert가 동시에 들어오고 하나가 `duplicate key`로 끝난다 | duplicate insert | exact key 승자를 DB가 마지막에 가른다 | `UNIQUE`, upsert, winner read |

입문자는 이 표에서 `같은 row / 총량 규칙 / exact key` 세 칸만 분리해도 절반은 끝난다.

## 30초 분류 순서

이 문서를 처음 찾은 학습자는 보통 anomaly 이름이 아니라 증상 문장부터 들고 온다. 그럴 때는 아래 순서로 자르면 된다.

| 먼저 던질 질문 | `yes`면 어디로 가나 | `no`면 다음 질문 |
|---|---|---|
| 마지막에 저장된 **같은 row 값**이 서로를 덮어쓴 것 같나 | lost update 쪽으로 본다 | 총량 규칙 질문으로 간다 |
| 여러 row를 합친 **count/sum/capacity**가 한도를 넘었나 | oversell 쪽으로 본다 | exact key 질문으로 간다 |
| "없으면 만든다" 경로에서 **같은 key insert**가 경쟁했나 | duplicate insert 쪽으로 본다 | write skew/phantom이나 다른 증상 지도로 간다 |

짧은 기억법:

- row 하나가 조용히 사라졌으면 lost update
- 개별 row는 멀쩡한데 총량이 틀어졌으면 oversell
- `duplicate key`나 same-key insert 경쟁이 보이면 duplicate insert

## 가장 작은 예시 3개

### 1. Lost update

`inventory(stock=10)` row 하나를 두 요청이 동시에 읽고 각각 `9`로 저장한다.

| 시점 | 요청 A | 요청 B |
|---|---|---|
| t1 | `stock=10` 읽음 |  |
| t2 |  | `stock=10` 읽음 |
| t3 | `stock=9` 저장 |  |
| t4 |  | `stock=9` 저장 |

결과는 `9`다. 두 번 팔렸다면 `8`이어야 하므로 앞선 변경이 사라졌다. 이건 **같은 row overwrite** 문제다.

### 2. Oversell

`concert_inventory(stock=1)`에서 두 요청이 둘 다 "재고 있음"이라고 판단하고 각각 주문 row를 만든다.

| 시점 | 요청 A | 요청 B |
|---|---|---|
| t1 | `stock > 0` 확인 |  |
| t2 |  | `stock > 0` 확인 |
| t3 | 주문 생성, 차감 시도 |  |
| t4 |  | 주문 생성, 차감 시도 |

겉으로는 "마지막 재고가 두 번 팔림"이지만, 본질은 **수량 invariant가 닫히지 않은 것**이다. 같은 inventory row를 덮어쓴 경우도 있고, 예약/claim row를 쌓다가 합계가 초과된 경우도 있다.

### 3. Duplicate insert

`coupon_issue(user_id, coupon_id)`가 비어 있는지 보고 `INSERT`한다.

| 시점 | 요청 A | 요청 B |
|---|---|---|
| t1 | 없음 확인 |  |
| t2 |  | 없음 확인 |
| t3 | `INSERT` 성공 |  |
| t4 |  | 같은 key `INSERT` 시도 |

`UNIQUE`가 있으면 B는 보통 `duplicate key`를 받고 끝난다. 여기서는 "두 번 팔렸다"보다 **같은 key를 두 번 만들려 한 insert 경쟁**이 핵심이다.

## 왜 oversell이 특히 헷갈리나

oversell은 anomaly 이름이 아니라 **비즈니스 증상**에 가깝다. 그래서 아래 둘이 모두 oversell처럼 보일 수 있다.

| oversell이 난 방식 | 실제 더 가까운 분류 | 설명 |
|---|---|---|
| 단일 stock row를 둘 다 읽고 덮어씀 | lost update | 같은 row overwrite 때문에 재고 계산이 틀어진다 |
| 예약 row/claim row를 여러 개 append해서 합계가 한도를 넘김 | write skew 또는 phantom 쪽 | 개별 row는 멀쩡하지만 전체 수량 규칙이 깨진다 |

즉 `oversell = 항상 lost update`가 아니다. oversell은 "결과 증상", lost update는 "충돌 모양"이다.

초보자에게는 아래 순서가 안전하다.

1. oversell이 **단일 카운터 row** 문제인지 본다
2. 아니면 **여러 row 합계** 문제인지 본다
3. 그다음에야 row lock, guard row, slot row, serializable 같은 해법을 고른다

## 증상별 로그 힌트

디버깅 초반에는 SQL 이론보다 "패배 요청이 무슨 신호를 봤는지"가 더 빠른 힌트가 된다.

| 로그/결과에서 먼저 보인 것 | 초보자 첫 해석 | 더 자주 연결되는 증상 |
|---|---|---|
| 둘 다 성공했고 최종 counter만 덜 줄었다 | overwrite 가능성이 크다 | lost update |
| 둘 다 성공했고 row 수나 합계가 limit를 넘었다 | 저장은 됐지만 invariant가 안 닫혔다 | oversell |
| 한쪽이 `duplicate key`로 끝났다 | DB가 same-key 승자를 정했다 | duplicate insert |
| `lock timeout`, `deadlock`, `40001`이 먼저 보인다 | 이름보다 경쟁 surface가 먼저 문제다 | oversell follow-up 또는 고급 locking/retry |

즉 `duplicate key`는 duplicate insert 쪽의 강한 단서이고, "둘 다 성공했는데 결과가 틀림"은 lost update나 oversell 쪽 단서다.

## 흔한 오해와 함정

- "`@Transactional`이면 oversell도 자동으로 막히죠?"
  - 아니다. 트랜잭션은 같이 commit/rollback할 범위를 정하고, 경쟁 제어는 별도 장치가 필요하다.
- "`duplicate key`가 났으니 시스템이 망가진 건가요?"
  - beginner 문맥에서는 보통 정상적인 승자 결정 신호다.
- "`마지막 재고 두 번 팔림`이면 무조건 락부터 걸면 되나요?"
  - 단일 row면 그럴 수 있지만, 여러 row 합계 문제라면 guard row나 slotization이 더 맞을 수 있다.
- "oversell과 duplicate insert는 같은 말 아닌가요?"
  - 아니다. duplicate insert는 exact key 경쟁이고, oversell은 capacity 규칙이 깨진 결과다.

## 처음 디버깅할 때 묻는 4문장

아래 네 문장만 물어도 다음 문서가 빨리 정해진다.

1. 두 요청이 **같은 row**를 둘 다 최종 저장했나?
2. 아니면 **여러 row의 count/sum**이 한도를 넘었나?
3. 아니면 `없으면 insert` 경로에서 **같은 key**를 두 번 만들려 했나?
4. 패배 요청이 본 신호가 `duplicate key`인가, `lock timeout`인가, 그냥 둘 다 성공인가?

이 질문의 답에 따라 다음 이동이 달라진다.

| 답 | 다음 문서 |
|---|---|
| 같은 row overwrite 같다 | [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md) |
| 여러 row 합계/capacity 문제 같다 | [Single Counter vs Ledger vs Slot Inventory Oversell Decision Card](./single-counter-vs-ledger-vs-slot-inventory-oversell-decision-card.md) |
| exact key duplicate insert 같다 | [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md) |
| 아직 락이 뭔지부터 헷갈린다 | [락 기초](./lock-basics.md) |

## 흔한 질문 한 장 답변

| 학습자 질문 | 먼저 짧게 답하면 좋은 문장 |
|---|---|
| "`마지막 재고가 두 번 팔렸어요`면 lost update예요?" | 그럴 수도 있지만 oversell이라는 결과 증상일 수도 있다. 먼저 same-row overwrite인지 본다. |
| "`duplicate key`가 떴는데 oversell인가요?" | 보통은 아니다. 우선 same-key duplicate insert 경쟁으로 읽는다. |
| "둘 다 성공했는데 재고가 음수예요. duplicate insert죠?" | 아니다. duplicate insert는 loser가 `duplicate key`로 끝나는 쪽에 더 가깝다. 이 경우는 oversell이나 lost update를 먼저 본다. |

## 더 깊이 가려면

- lost update, write skew, phantom을 `same row / different row / new row`로 더 세밀하게 나누려면 [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md)
- oversell이 single counter, claim 합계, slot inventory 중 어디서 나는지 먼저 고르려면 [Single Counter vs Ledger vs Slot Inventory Oversell Decision Card](./single-counter-vs-ledger-vs-slot-inventory-oversell-decision-card.md)
- exact duplicate와 `duplicate key` 처리 흐름을 보려면 [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- 단일 row 차감, guard row, retry를 어떤 기준으로 고를지 보려면 [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
- `@Transactional`과 동시성 제어를 먼저 분리하려면 [Spring @Transactional 기초](../spring/spring-transactional-basics.md)

## 면접/시니어 질문 미리보기

> Q: oversell과 lost update는 같은 말인가요?
> 의도: 증상과 anomaly 이름을 구분하는지 확인
> 핵심: 아니다. oversell은 결과 증상이고, lost update는 같은 row overwrite라는 충돌 모양이다.

> Q: duplicate insert는 락 문제인가요, 제약 조건 문제인가요?
> 의도: read-before-write와 write-time arbitration을 구분하는지 확인
> 핵심: beginner 기본값은 제약 조건 문제다. `UNIQUE`가 승자를 정하고, 락은 보조 queue 역할일 수 있다.

> Q: "마지막 재고가 두 번 팔렸다"를 들었을 때 첫 질문은 무엇인가요?
> 의도: 바로 기술 해법으로 점프하지 않는지 확인
> 핵심: 같은 row overwrite인지, 여러 row 합계 규칙인지, duplicate insert인지부터 나눈다.

## 한 줄 정리

`마지막 재고가 두 번 팔렸다`는 증상을 보면 먼저 `같은 row overwrite`, `총량 invariant 붕괴`, `exact key duplicate insert` 중 어디인지 가른 뒤 그에 맞는 락·제약·재시도 문서로 내려가야 한다.
