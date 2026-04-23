# Covering Index Width, Leaf Fanout, and Write Amplification

> 한 줄 요약: 커버링 인덱스로 heap/table lookup을 줄일 수는 있지만, 인덱스 폭이 커질수록 leaf fanout이 줄고 write path의 split·cache miss·maintenance 비용은 빠르게 커진다.

**난이도: 🔴 Advanced**

관련 문서:

- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- [Secondary Index Change Propagation Path](./secondary-index-change-propagation-path.md)
- [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
- [Page Split, Merge, and Fill Factor](./page-split-merge-fill-factor.md)
- [Hot Updates, Secondary Index Churn, and Write-Path Contention](./hot-update-secondary-index-churn.md)

retrieval-anchor-keywords: covering index width, leaf fanout, secondary index size, write amplification, page split frequency, cache residency, index payload cost, backend index tradeoff, using index but still slow, wide covering index, covering index write penalty, covering index write amplification, index too wide, buffer pool miss after covering index, page split after adding columns, covering index p99 regression, covering index cache pressure, 커버링 인덱스 너무 넓음, using index인데도 느림

## 증상별 바로 가기

- `Using index`와 `Index Only Scan`의 차이, `Heap Fetches`가 왜 남는지, PostgreSQL visibility map이 왜 끼어드는지가 궁금하면 [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)으로 먼저 간다.
- `Using index`는 보이는데도 쿼리가 아주 빠르지 않거나, covering을 위해 컬럼을 늘린 뒤 write latency, buffer pool miss, page split이 늘었다면 이 문서가 맡는 범위다.
- `ORDER BY ... LIMIT` 때문에 어떤 복합 인덱스 순서가 필요한지, `Using filesort`를 어떻게 없앨지가 먼저면 [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)로 돌아간다.

## 핵심 개념

커버링 인덱스는 보통 읽기 최적화 문맥에서만 이야기된다.

- 테이블 본문 접근 감소
- 목록 조회 응답 시간 개선
- index-only execution 가능성 증가

하지만 storage-engine 관점에서는 반대편 비용도 분명하다.

- 인덱스 entry가 두꺼워진다
- page 하나에 담기는 key 수(fanout)가 줄어든다
- tree height, split 빈도, cache 압박이 커진다
- INSERT/UPDATE/DELETE마다 더 큰 payload를 유지해야 한다

즉 "컬럼 몇 개 더 넣어서 커버링시키자"는 결정은 단순 read optimization이 아니라, **leaf page density와 write amplification을 바꾸는 엔진 레벨 결정**이다.
이 문서는 `Using index`라는 신호의 의미를 해석하기보다, **lookup을 줄이려고 인덱스를 넓혔더니 왜 전체 비용이 더 커졌는가**를 설명하는 쪽에 초점을 둔다.

## 깊이 들어가기

### 1. 커버링 인덱스의 숨은 비용은 key width다

복합 인덱스에 조회용 컬럼을 더 넣으면 실행 계획은 좋아질 수 있다.  
하지만 leaf entry 하나가 커지면 같은 page에 담을 수 있는 entry 수가 줄어든다.

그 결과:

- 더 많은 page가 필요하다
- buffer pool이나 shared buffer에서 index residency가 떨어진다
- range scan 시 더 많은 leaf page를 건드린다
- split/merge 비용이 빨리 나타난다

즉 커버링 인덱스는 lookup을 줄이는 대신, **인덱스 자체를 더 자주 메모리와 디스크에 올리게 만든다**.

### 2. fanout이 줄면 tree depth와 split 빈도가 같이 변한다

B-Tree 계열 구조에서 fanout은 page 하나가 다음 레벨을 얼마나 넓게 가리킬 수 있는지와 연결된다.

- key가 좁을수록 fanout이 높다
- key가 넓을수록 fanout이 낮다

fanout이 줄면:

- 같은 row 수를 담기 위해 더 많은 leaf page가 필요하고
- 내부 page도 더 빨리 커지며
- 최종적으로 탐색과 maintenance에 필요한 pointer hop이 늘 수 있다

대부분의 OLTP에서는 tree height 1 증가만으로도 dramatic한 차이가 나지는 않을 수 있다.  
하지만 hot range에 대한 split 빈도와 cache miss가 함께 오르면 p99는 민감하게 흔들린다.

### 3. covering column이 자주 바뀌면 cost가 더 커진다

커버링 인덱스에 넣은 컬럼이 자주 update되는 값이면 비용은 더 직접적이다.

예:

- `status`
- `updated_at`
- `last_seen_at`
- `retry_count`

이런 컬럼이 secondary index key/payload 일부가 되면:

- UPDATE마다 secondary entry rewrite가 생기고
- old/new key 정리가 필요하며
- hot row나 hot range에서 latch 경합이 커질 수 있다

즉 커버링 인덱스에 "읽을 때 편한 컬럼"을 넣기 전에, 그 컬럼이 **얼마나 자주 변하는가**를 먼저 봐야 한다.

### 4. narrow index + bookmark lookup이 더 나은 경우도 많다

모든 조회를 커버링으로 만들 필요는 없다.

오히려 다음 경우엔 narrow index가 더 건강하다.

- 결과 row 수가 적다
- LIMIT이 작다
- lookup 대상 row가 clustered/localized 되어 있다
- 쓰기 TPS가 높다

이때는 "약간의 row lookup"보다 "항상 비대한 secondary index 유지"가 더 비쌀 수 있다.

### 5. 테넌트별/상태별 skew가 있으면 폭 넓은 인덱스의 비용이 더 빨리 온다

멀티테넌트나 상태값 편향이 큰 테이블에서는 hot range가 좁다.

- 특정 tenant의 최근 주문
- `PENDING` 상태만 몰린 큐 테이블
- 최신 `created_at` 기준 append-heavy 목록

여기에 폭 넓은 covering index를 얹으면:

- hot range의 page density가 더 낮아지고
- split 빈도가 빨라지며
- buffer pool에서 같은 hot set을 유지하는 데 더 큰 메모리가 든다

즉 skew가 큰 workload일수록 covering index의 "조금 더 큰 폭"이 실제 운영에서는 꽤 크게 작용할 수 있다.

### 6. 읽기 최적화는 index width 말고도 다른 방법이 있다

커버링 인덱스 대신 검토할 수 있는 선택지:

- 필요한 컬럼만 줄여 narrow index 유지
- 목록 전용 summary/read model
- cache나 projection으로 일부 컬럼 분리
- 자주 바뀌는 컬럼을 읽기 테이블로 분리

핵심은 "lookup을 없애는 것"만이 아니라, **lookup 제거에 드는 구조 비용이 얼마나 되는지**를 비교하는 것이다.

## 실전 시나리오

### 시나리오 1. 목록 API를 위해 인덱스에 컬럼을 계속 추가

처음엔 `(tenant_id, status, created_at)`이면 충분했는데 DTO가 커지며 `amount`, `currency`, `channel`까지 넣고 싶어진다.

문제:

- read query는 빨라질 수 있다
- index size가 급격히 커진다
- write path가 무거워진다

이 경우는 "정말 항상 필요한 컬럼인지", "일부는 lookup으로 남겨도 되는지"를 다시 잘라야 한다.

### 시나리오 2. `status`가 자주 바뀌는 작업 큐

큐 polling을 빠르게 하려고 `(status, available_at, payload_hint)` 같은 covering index를 만들었다.

하지만 `status` 전이가 매우 잦다면:

- claim/ack마다 index rewrite가 일어난다
- hot status range에서 leaf page churn이 커진다

이 경우는 payload를 줄이거나 queue read model을 따로 두는 편이 낫다.

### 시나리오 3. 읽기는 빨라졌는데 buffer pool miss가 증가

폭 넓은 covering index를 추가했더니 read latency는 일부 좋아졌지만 전체 메모리 압박이 커졌다.

이때는:

- 실제 index size 증가량
- hot set residency
- lookup 감소 효과와 비교한 p95/p99

를 함께 봐야 한다.

## 코드로 보기

```sql
-- narrow index
CREATE INDEX idx_orders_tenant_status_created
ON orders (tenant_id, status, created_at);
```

```sql
-- wider covering index
CREATE INDEX idx_orders_tenant_status_created_amount_channel
ON orders (tenant_id, status, created_at, amount, channel);
```

```sql
EXPLAIN
SELECT tenant_id, status, created_at, amount, channel
FROM orders
WHERE tenant_id = ?
  AND status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

위 두 인덱스 중 후자가 lookup을 줄여 줄 수는 있다.  
하지만 update-heavy 테이블이라면 그 차이는 곧 더 큰 leaf entry, 더 많은 page, 더 비싼 maintenance로 돌아온다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| narrow secondary index | fanout과 cache 효율이 좋다 | lookup이 남는다 | 쓰기가 많고 결과 row 수가 적을 때 |
| wide covering index | lookup을 크게 줄일 수 있다 | index size, split, maintenance 비용이 크다 | 반복 목록 조회가 매우 중요할 때 |
| summary/read model 분리 | OLTP index를 가볍게 유지한다 | 동기화 비용이 생긴다 | DTO가 크고 조회 패턴이 고정적일 때 |
| 자주 바뀌는 컬럼 제외 | update churn을 줄인다 | 완전한 covering이 안 된다 | status/heartbeat 계열 컬럼이 자주 변할 때 |

## 꼬리질문

> Q: 커버링 인덱스는 왜 쓰기 비용을 늘리나요?
> 의도: lookup 감소와 key width 비용을 연결하는지 확인
> 핵심: 더 큰 leaf entry를 INSERT/UPDATE/DELETE마다 유지해야 하기 때문이다

> Q: fanout이 줄면 무엇이 문제인가요?
> 의도: storage-engine 관점 이해 확인
> 핵심: 같은 row 수를 담기 위해 더 많은 page와 더 큰 tree/메모리 압박이 필요해진다

> Q: 모든 목록 조회를 커버링 인덱스로 만들면 좋은가요?
> 의도: read-only 최적화를 경계하는지 확인
> 핵심: narrow index + lookup이나 summary model이 전체 비용면에서 더 나을 수 있다

## 한 줄 정리

커버링 인덱스의 진짜 가격표는 추가 컬럼 수가 아니라 key width가 줄이는 leaf fanout과 그로 인해 커지는 write amplification·cache pressure·split 빈도다.
