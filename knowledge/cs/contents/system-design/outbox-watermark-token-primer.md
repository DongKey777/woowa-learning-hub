# Outbox Watermark Token Primer

> 한 줄 요약: outbox row에 붙는 commit metadata는 "downstream read model이 최소 여기까지 따라와야 한다"는 단순한 기준선으로 재사용할 수 있고, 이 숫자를 token처럼 넘기면 stale read를 비교 한 번으로 설명하기 쉬워진다.

**난이도: 🟢 Beginner**

관련 문서:

- [Projection Applied Watermark Basics](./projection-applied-watermark-basics.md)
- [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)
- [Shard-Aware Watermark Scope Primer](./shard-aware-watermark-scope-primer.md)
- [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Database: Incremental Summary Table Refresh and Watermark Discipline](../database/incremental-summary-table-refresh-watermark.md)
- [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)
- [system design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: outbox watermark token primer, outbox commit metadata token, commit lsn consistency token, outbox required watermark, downstream read watermark, what is outbox watermark, beginner consistency token, cdc outbox downstream read, read model watermark basics, outbox commit sequence token, shard aware watermark scope, outbox id across shards, outbox watermark cache metadata, refill metadata persistence, cache applied watermark bridge

---

## 핵심 개념

먼저 가장 단순한 mental model부터 보자.

> outbox row에 붙은 commit 번호를 "이 downstream은 최소 여기까지 처리했는가?"를 묻는 기준선으로 재사용할 수 있다.

주문 `#123` 결제가 끝난 트랜잭션 안에서 `orders` row와 `outbox` row가 같이 commit되었다고 하자.
이때 outbox row의 `id=9001`이나 `commit_lsn=9:001` 같은 metadata는 relay가 나중에 읽을 행 번호로만 쓰일 필요가 없다.

같은 값을 downstream read 쪽에서는 이렇게 읽을 수 있다.

- `required_watermark=9001`: 이 요청이 기대하는 최소 기준선
- `projection.applied_watermark=8998`: 이 read model이 현재 따라온 위치

그러면 질문은 복잡한 이론이 아니라 아래 한 줄이 된다.

- `8998 < 9001`이면 아직 너무 오래됐다
- `9001 <= applied_watermark`면 이 read model은 최소 그 commit까지는 반영했다

핵심은 token이 원본 주문 전체를 담는 게 아니라, downstream이 **최소 어디까지 따라와야 하는지**를 담는다는 점이다.

## 한눈에 보기

| 단계 | source 쪽에서 생기는 값 | read 쪽에서 비교하는 값 | 읽는 사람이 물어볼 질문 |
|---|---|---|---|
| 1. 주문/결제 commit | `outbox.id=9001` | 아직 없음 | "무슨 변경이 확정됐나?" |
| 2. relay publish | event에 `required_watermark=9001` 추가 | 아직 없음 | "downstream이 어디까지 따라와야 하나?" |
| 3. projection apply | read model이 `applied_watermark=8998 -> 9001`로 전진 | `projection.applied_watermark` | "이 read model은 그 commit을 봤나?" |
| 4. 사용자 조회 | request가 `required_watermark=9001` 전달 | `applied_watermark >= 9001` 검사 | "지금 이 화면은 그 변경 이후 상태인가?" |

```text
primary tx(order row + outbox row#9001)
  -> relay publishes event(required_watermark=9001)
  -> projection catches up(applied_watermark=8998, then 9001)
  -> read request compares 9001 vs applied_watermark
```

초보자는 여기서 "token 생성"보다 read model이 자기 watermark를 같이 들고 있는가를 먼저 보면 된다.
그 read-side 기준선을 따로 정리한 문서는 [Projection Applied Watermark Basics](./projection-applied-watermark-basics.md)다.
그리고 그 값을 cache refill 때 entry metadata로 남겨 다음 hit에서도 다시 검사하는 연결 고리는 [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)에서 이어서 설명한다.

## 왜 outbox commit metadata가 token이 되나

이게 성립하는 이유는 outbox row가 business row와 같은 commit 경계 안에서 만들어지기 때문이다.

1. source transaction이 business row와 outbox row를 함께 commit한다
2. 따라서 outbox row의 commit metadata는 "그 business change가 확정된 순간"과 붙어 있다
3. relay는 이 metadata를 event에 실어 보낼 수 있다
4. downstream projection은 자기 `applied_watermark`를 저장해 둔다
5. read 요청은 둘을 비교해 stale 여부를 판단한다

즉, token의 핵심은 "message broker가 언제 publish했나"가 아니라 source commit이 어디까지 확정됐나이다.

여기서 ordering scope만 기억하면 된다.

- 같은 aggregate 또는 같은 partition 안에서 비교 가능한가
- projection의 `applied_watermark`도 같은 순서 체계를 따르는가

beginner 단계에서는 이 두 조건만 맞으면 충분하다.
전역 글로벌 순서를 만들겠다는 순간 문서가 훨씬 어려워진다.
특히 shard가 나뉘면 outbox id나 commit position은 범위 없이 직접 비교하면 안 되는데, 이 지점을 따로 정리한 문서는 [Shard-Aware Watermark Scope Primer](./shard-aware-watermark-scope-primer.md)다.

## 주문 결제 예시로 따라가기

주문 `#123`을 결제했다고 하자.

```text
tx commit
- orders[123].status = PAID
- outbox row id = 9001
```

relay가 이 outbox row를 읽어 이벤트를 발행한다.

```json
{
  "event_type": "order_paid",
  "order_id": "123",
  "required_watermark": 9001
}
```

그런데 주문 상세 read model은 아직 `applied_watermark=8998` 상태일 수 있다.
이때 사용자가 결제 완료 알림을 누르거나, 결제 직후 주문 상세를 열면 읽기 경로는 이렇게 판단한다.

```pseudo
if projection.appliedWatermark < requiredWatermark:
  return fallback_to_primary_or_wait()
return projection.read(orderId)
```

중요한 점은 downstream row 자체를 일일이 diff하지 않아도 된다는 것이다.
`9001` 하나만 비교해도 "이 read model이 그 commit 이전인가 이후인가"를 빠르게 나눌 수 있다.

이 패턴은 주문 상세뿐 아니라 아래에도 그대로 적용된다.

- notification click 후 원본 상세 조회
- dashboard card가 최신 승인 상태를 보여야 하는 경우
- search/document read model이 방금 반영된 상태를 봐야 하는 경우

## 어떤 값을 token으로 쓰면 쉬운가

| 후보 값 | 초보자에게 왜 쉬운가 | 주의할 점 |
|---|---|---|
| outbox auto-increment id | 구현이 단순하고 눈으로 보기 쉽다 | shard가 여러 개면 table id 하나로 전역 비교는 어렵다 |
| commit lsn / binlog position | source commit 순서를 더 직접적으로 반영한다 | DB 엔진별 표현이 달라질 수 있다 |
| per-aggregate sequence | aggregate 단위 비교가 명확하다 | 다른 aggregate끼리는 직접 비교하면 안 된다 |
| app timestamp | 이해는 쉽다 | clock skew와 동률 때문에 watermark로는 약하다 |

beginner 설계에서는 보통 아래 둘 중 하나로 시작한다.

- 같은 DB/table 범위면 `outbox.id`
- CDC/log 기반이면 `commit_lsn` 또는 equivalent position

반대로 relay가 publish한 시각이나 앱 서버 시계 timestamp를 기준선으로 쓰면, source commit과 느슨하게 연결돼서 설명력이 떨어진다.

## 흔한 오해와 함정

- `outbox event id만 있으면 무조건 consistency token이다`라고 보면 안 된다. read model이 같은 순서 체계의 `applied_watermark`를 저장하고 있어야 비교가 된다.
- `token이 있으니 exactly-once가 보장된다`는 뜻이 아니다. token은 freshness 기준선이지 delivery semantics 자체가 아니다.
- `모든 downstream read가 항상 이 token을 받아야 한다`고 볼 필요는 없다. 결제 확인, 승인 완료, 알림 진입처럼 틀리면 안 되는 read부터 붙이면 된다.
- `relay publish 완료 시간`을 token으로 쓰면 source commit과 어긋날 수 있다. 비교 기준은 publish 시각보다 source commit metadata가 더 안전하다.
- `watermark가 같으면 화면 값이 100% 완벽하다`는 과장도 피해야 한다. 이 token은 최소한 "그 commit 이전 상태는 아니다"를 보여 주는 단순한 하한선이다.

## 실무에서 쓰는 모습

| 제품 흐름 | source에서 token 만드는 곳 | read에서 하는 가장 단순한 대응 |
|---|---|---|
| 결제 완료 -> 주문 상세 | 주문 row + outbox row commit | projection watermark 미달이면 primary fallback |
| 승인 완료 알림 -> 권한 화면 | approval row + outbox row commit | 미달이면 "처리 중" 또는 fresh source read |
| 검색 index -> 상세 화면 | indexing event에 `required_watermark` 전달 | stale index hit을 바로 채택하지 않고 overlay/fallback |
| 백오피스 대시보드 | aggregate update + outbox | widget별 applied watermark를 보고 restatement/placeholder 결정 |

관측 신호도 단순하게 시작할 수 있다.

- `required_watermark`
- `applied_watermark`
- `fallback_reason=watermark`
- `projection_lag_by_watermark`

이 정도만 있어도 "이상하게 stale하다"를 숫자로 설명하기 쉬워진다.

## 더 깊이 가려면

- [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Database: Incremental Summary Table Refresh and Watermark Discipline](../database/incremental-summary-table-refresh-watermark.md)
- [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)

## 면접/시니어 질문 미리보기

> Q: outbox row의 metadata가 왜 downstream consistency token으로 쓸 만한가요?
> 의도: source commit 경계와 read-side 비교 기준을 연결할 수 있는지 확인
> 핵심: business row와 outbox row가 같은 transaction에서 commit되므로, outbox metadata는 "그 변경이 최소 언제 확정됐는가"를 downstream에 전달하는 하한선이 된다.

> Q: token은 event payload 전체와 어떻게 다른가요?
> 의도: payload 내용과 ordering/freshness 기준을 구분하는지 확인
> 핵심: payload는 무엇이 바뀌었는지 설명하고, token은 read model이 최소 어디까지 따라와야 하는지 비교하는 숫자다.

> Q: beginner 단계에서 가장 단순한 구현은 무엇인가요?
> 의도: 과한 글로벌 ordering 없이 시작점을 설명하는지 확인
> 핵심: outbox row의 monotonic id나 commit_lsn을 event의 `required_watermark`로 싣고, projection은 `applied_watermark`를 저장한 뒤 read에서 둘을 비교한다.

## 한 줄 정리

outbox commit metadata는 "이 downstream read는 최소 여기까지 반영해야 한다"는 simple consistency token으로 재사용할 수 있고, read model의 applied watermark와 비교하면 downstream stale 여부를 훨씬 단순하게 설명할 수 있다.
