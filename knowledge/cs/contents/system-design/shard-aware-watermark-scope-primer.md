# Shard-Aware Watermark Scope Primer

> 한 줄 요약: shard가 나뉘면 outbox id나 commit position은 더 이상 "전체 시스템 공용 번호표"가 아니므로, beginner 단계에서는 **같은 shard 안에서만 비교되는 watermark scope**를 먼저 고르고 그 scope를 event와 projection 양쪽에 같이 적는 편이 가장 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
- [Projection Applied Watermark Basics](./projection-applied-watermark-basics.md)
- [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
- [Tenant Partition Strategy / Reassignment 설계](./tenant-partition-strategy-reassignment-design.md)
- [system design 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: shard aware watermark scope primer, outbox id not comparable across shards, commit lsn not globally comparable, per shard watermark beginner, watermark scope beginner, shard watermark ordering scope, outbox id across shards, cdc position across shards, safe watermark scope choice, projection checkpoint per shard, shard local ordering, watermark scope vs global order, beginner sharding consistency primer, system-design-00077, shard aware watermark scope primer basics

---

## 먼저 잡을 mental model

초보자에게 가장 쉬운 비유는 "지점마다 따로 뽑는 대기표"다.

- 강남점 대기표 `101`
- 종로점 대기표 `101`

둘 다 `101`이어도 어느 쪽이 더 먼저인지 알 수는 없다.
번호가 같아도 **같은 창구에서 뽑힌 표가 아니기 때문**이다.

shard 환경의 outbox id나 commit position도 비슷하다.

> 숫자 자체보다 먼저 봐야 하는 것은 "이 숫자가 어느 shard의 번호인가?"다.

그래서 beginner 단계에서는 이렇게 생각하면 된다.

- `watermark`는 숫자만으로 완성되지 않는다
- `scope`까지 붙어야 비교가 된다
- 가장 안전한 scope는 보통 `same shard` 또는 `same partition`

## 왜 shard가 생기면 직접 비교가 깨지나

단일 DB일 때는 아래 가정이 자주 성립한다.

- outbox table이 하나다
- auto-increment id가 하나다
- commit log도 한 줄로 흐른다

그래서 `9002 > 9001`이면 대체로 "뒤에 일어난 변경"처럼 설명할 수 있다.

하지만 shard가 나뉘면 상황이 달라진다.

| 환경 | 값 예시 | 왜 쉬웠나 / 왜 깨지나 |
|---|---|---|
| 단일 DB | `outbox.id=9001 -> 9002` | 같은 카운터라서 비교가 단순하다 |
| shard A | `outbox.id=9001` | shard A 안에서는 의미가 있다 |
| shard B | `outbox.id=9001` | shard B 안에서는 의미가 있지만 shard A와는 직접 비교 불가 |
| shard A LSN | `16/B374` | A 안에서는 commit 순서를 설명할 수 있다 |
| shard B LSN | `16/B400` | 숫자가 커 보여도 A보다 "나중"이라고 단정 불가 |

핵심은 이것이다.

- auto-increment는 보통 shard마다 따로 돈다
- commit position도 보통 shard마다 따로 생긴다
- shard마다 clock, failover, relay 진행 속도도 다르다

즉 `id=9001`이나 `lsn=16/B374`만 들고 와서
"그러면 다른 shard의 `8999`보다 최신이네요?"라고 말하면 위험하다.

## 가장 흔한 오해

초보자는 다음 문장을 자주 섞는다.

- "숫자가 더 크면 더 최신이다"
- "commit position이니까 전역 순서다"
- "outbox id는 결국 순번이니 전체 비교 가능하다"

하지만 shard가 둘 이상이면 보통 아래처럼 바뀐다.

| 문장 | 실제로 안전한 해석 |
|---|---|
| 숫자가 더 크면 더 최신이다 | **같은 shard 안에서만** 대체로 맞다 |
| commit position이면 전역 순서다 | 보통은 **해당 DB 로그 안에서만** 순서다 |
| outbox id는 전체 비교 가능하다 | 보통은 **같은 outbox table 범위에서만** 비교 가능하다 |
| watermark 하나만 들고 다니면 된다 | 보통은 `scope + value`가 같이 필요하다 |

짧게 줄이면:

> shard가 생기면 `9001`은 숫자가 아니라 `(scope, 9001)`로 읽어야 한다.

## beginner에게 가장 안전한 ordering scope

처음부터 글로벌 총순서를 만들려 하지 않는 편이 낫다.
beginner 단계에서는 아래 우선순위가 안전하다.

1. **같은 aggregate**
2. **같은 shard 또는 같은 partition**
3. 정말 필요할 때만 더 넓은 scope

이유는 간단하다.

- 실제 사용자 질문은 대부분 "이 주문", "이 계정", "이 tenant" 단위다
- 그 단위는 대개 한 shard에 라우팅된다
- 그러면 같은 shard 안의 monotonic sequence로도 설명이 충분하다

가장 쉬운 기본 규칙은 이것이다.

> "이 read가 참조하는 source row들이 같은 shard에 모여 있다면, watermark scope도 그 shard로 잡는다."

## 어떤 scope를 고르면 쉬운가

| scope 후보 | beginner 적합도 | 언제 안전한가 | 주의할 점 |
|---|---|---|---|
| per-aggregate sequence | 높음 | 한 aggregate의 write 순서만 보면 될 때 | aggregate끼리 직접 비교 불가 |
| per-shard outbox id | 높음 | 한 shard가 단일 monotonic counter를 가질 때 | shard id를 같이 들고 다녀야 한다 |
| per-partition commit position | 중간 | CDC/stream partition 기준 처리일 때 | partition 이동 시 scope metadata 보강 필요 |
| global timestamp | 낮음 | 로그 참고용으로만 쓸 때 | ordering 기준으로는 약하다 |
| synthetic global sequencer | 낮음 | 정말 전역 순서가 제품 요구일 때 | beginner 단계에는 과하다 |

보통 beginner-friendly 선택은 둘 중 하나다.

- `required_watermark = { shard_id, outbox_id }`
- `required_watermark = { partition_key, commit_position }`

즉 숫자 하나가 아니라 **작은 튜플**로 들고 가는 쪽이 안전하다.

## 주문 예시로 보기

주문 시스템이 shard A, shard B로 나뉘어 있다고 하자.

```text
shard A
- order 101
- outbox.id = 9001

shard B
- order 202
- outbox.id = 9001
```

둘 다 `9001`이 나올 수 있다.
하지만 아래 질문에는 답할 수 없다.

- "A의 9001이 B의 9001보다 먼저인가?"

대신 아래 질문은 답할 수 있다.

- "주문 101의 read model이 shard A의 9001까지 따라왔는가?"
- "주문 202의 read model이 shard B의 9001까지 따라왔는가?"

그래서 event도 이렇게 적는 편이 낫다.

```json
{
  "order_id": "101",
  "watermark_scope": "orders-shard-A",
  "required_watermark": 9001
}
```

projection도 같은 scope로 checkpoint를 남긴다.

```text
projection checkpoint
- scope=orders-shard-A, applied_watermark=8998
- scope=orders-shard-B, applied_watermark=9010
```

그러면 read path는 이렇게 본다.

```pseudo
if projection.scope != event.watermarkScope:
  return fallback("scope mismatch")

if projection.appliedWatermark < event.requiredWatermark:
  return fallback("not caught up")

return serveProjection()
```

여기서 중요한 점은 `8998 < 9010` 같은 cross-shard 비교가 아니다.
항상 **같은 scope 안에서만** 비교한다는 점이다.

## projection 쪽 checkpoint도 scope를 따라가야 한다

source event만 scope-aware라고 끝나지 않는다.
projection이 저장하는 `applied_watermark`도 같은 scope 규칙을 따라야 한다.

나쁜 예:

- event는 `orders-shard-A:9001`
- projection checkpoint는 그냥 `9005`

이러면 `9005`가 어느 shard 기준인지 몰라서 비교가 무너진다.

좋은 예:

- event는 `scope=orders-shard-A, required=9001`
- projection checkpoint도 `scope=orders-shard-A, applied=9005`

beginner 체크 문장으로 줄이면 이렇다.

- event가 scope를 말하면
- projection도 같은 scope를 말해야 하고
- read path는 scope가 같을 때만 숫자를 비교한다

## "글로벌 순서가 꼭 필요해 보이는" 상황은 어떻게 보나

초보자는 종종 이렇게 묻는다.

- "전체 주문 목록이면 shard 여러 개를 한 화면에 섞는데요?"
- "그러면 결국 전역 순서가 필요한 것 아닌가요?"

항상 그런 것은 아니다.

먼저 나눠 보면 된다.

| 질문 | beginner 기본 답 |
|---|---|
| 단건 상세가 최신이어야 하나 | per-shard scope로 충분한 경우가 많다 |
| 한 사용자가 방금 본 같은 주문이 뒤로 가면 안 되나 | 그 주문 key 기준 scope면 충분할 때가 많다 |
| 여러 shard 데이터를 정확한 전역 사건 순서로 정렬해야 하나 | 이때는 별도 설계가 필요할 수 있다 |

즉, 제품 요구가 "전역 총순서"인지,
아니면 "같은 엔티티에 대한 안전한 최신선"인지를 먼저 나눠야 한다.

대부분의 beginner 문제는 두 번째다.

## 안전한 기본 선택 규칙

아래 규칙이면 처음 설계에서 크게 틀리지 않는다.

1. 사용자가 실제로 확인하려는 최신성이 어느 엔티티 범위인지 적는다
2. 그 엔티티가 항상 같은 shard/partition으로 가는지 확인한다
3. 그렇다면 그 shard/partition을 watermark scope로 잡는다
4. event와 projection 양쪽에 같은 scope를 저장한다
5. read에서는 scope가 같을 때만 watermark 숫자를 비교한다

짧은 결정표로 보면:

| 상황 | safe default scope |
|---|---|
| 주문 상세 | `order shard` 또는 `order aggregate` |
| 계정 프로필 | `account shard` |
| tenant별 대시보드 | `tenant shard` 또는 `tenant partition` |
| 여러 tenant를 한 번에 합친 운영 보고서 | beginner 범위를 넘을 수 있으므로 별도 설계 검토 |

## 자주 나오는 실수

- shard id 없이 outbox id만 event에 넣는다
  - 나중에 같은 숫자가 다른 shard에도 나와 비교가 흐려진다.
- projection checkpoint를 전역 숫자 하나로 저장한다
  - 실제로는 shard별 따라온 정도가 다른데 한 숫자로 뭉개진다.
- partition relocation 후에도 예전 scope 이름을 그대로 믿는다
  - scope 정의가 "논리 shard"인지 "물리 DB"인지 구분해야 한다.
- timestamp를 global order 대용으로 쓴다
  - clock skew와 동시 commit 때문에 beginner 설명이 오히려 더 어려워진다.
- cross-shard compare 결과를 제품 로직에 바로 쓴다
  - "더 큰 숫자니까 더 최신"이라는 잘못된 가정이 들어간다.

## 운영에서 최소한 보고 싶은 신호

운영도 복잡하게 시작할 필요는 없다.
아래 다섯 개면 초반 진단이 쉬워진다.

- `watermark_scope`
- `required_watermark`
- `applied_watermark`
- `fallback_reason=scope_mismatch|watermark_lag`
- `source_shard` 또는 `partition_key`

이렇게 남기면 "왜 fresh read로 우회했나"를 숫자와 scope로 같이 설명할 수 있다.

## common confusion

- `commit_lsn`이면 무조건 전역적으로 비교된다
  - 보통은 아니다. 같은 로그 스트림 안에서만 안전하다.
- shard가 있어도 outbox id는 계속 증가하니 전체 정렬 가능하다
  - shard별 카운터면 안 된다.
- scope가 붙으면 복잡해 보인다
  - 반대로 scope를 빼면 나중에 숫자의 의미를 설명할 수 없다.
- 전역 화면이 하나라도 있으면 처음부터 global sequencer가 필요하다
  - 단건 최신성 문제와 전역 정렬 문제를 먼저 분리해야 한다.

## 30초 체크리스트

- 이 watermark가 어느 shard/partition 범위의 숫자인지 이름이 붙어 있는가
- event와 projection이 같은 scope를 쓰는가
- read path가 scope mismatch를 따로 처리하는가
- 숫자 비교를 cross-shard로 하지 않는가
- 정말 전역 총순서가 필요한 요구인지 먼저 확인했는가

## 한 줄 정리

shard가 나뉘면 outbox id나 commit position은 숫자 alone으로는 의미가 약해지고, beginner 단계에서는 `same shard / same partition`처럼 비교 가능한 ordering scope를 먼저 고른 뒤 `scope + watermark`를 event와 projection 양쪽에 같이 저장하는 쪽이 가장 안전하다.
