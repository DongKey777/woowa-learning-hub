# Incremental Summary Table Refresh and Watermark Discipline

> 한 줄 요약: summary table은 조회를 빠르게 만드는 대신, 원본 변경을 어떤 watermark와 dedup 규칙으로 따라잡을지 계속 관리해야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [정규화와 반정규화 트레이드오프](./normalization-denormalization-tradeoffs.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)
- [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)
- [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md)
- [Idempotency Key and Deduplication](./idempotency-key-and-deduplication.md)

retrieval-anchor-keywords: summary table refresh, materialized view refresh, incremental aggregation, watermark discipline, late arriving event, replay safe refresh, aggregation dedup, summary drift, bounded rebuild

## 핵심 개념

요약 테이블(summary table), read model, materialized view 대체 구조는 보통 조회 비용을 줄이기 위해 만든다.

예:

- 주문 일별 합계
- 사용자별 최근 활동 수
- 상품 재고/판매 대시보드
- 관리자 화면용 precomputed stats

문제는 원본 데이터가 계속 바뀐다는 점이다.  
summary table은 한 번 계산해 넣고 끝나는 캐시가 아니라, **원본 변경을 지속적으로 따라가는 파생 상태**다.

그래서 핵심 질문은 다음이다.

- 어느 시점까지 반영됐는가
- 늦게 도착한 변경은 어떻게 다시 반영하는가
- 중복 처리와 재실행은 안전한가
- 조회자가 이 summary의 freshness를 알고 있는가

## 깊이 들어가기

### 1. full rebuild보다 중요한 것은 incremental boundary다

초기에는 `TRUNCATE + INSERT ... SELECT` 전체 재계산으로 시작할 수 있다.  
하지만 데이터가 커질수록 문제는 금방 드러난다.

- 계산 시간이 길어진다
- lock 또는 resource spike가 커진다
- rebuild 중간에 들어온 변경을 놓칠 수 있다
- freshness가 rebuild 주기에 묶인다

그래서 운영 단계에서는 "무엇을 다시 계산할지"보다 **"어디까지 반영됐는지"를 기억하는 watermark**가 더 중요해진다.

### 2. watermark는 시간보다 로그 위치가 더 안전할 때가 많다

증분 반영 기준으로 자주 쓰는 것:

- `updated_at`
- 단조 증가 ID
- binlog/WAL position
- event sequence

`updated_at`는 단순하지만 함정이 있다.

- 시계 오차
- 같은 row의 반복 수정
- 늦게 도착한 이벤트

반면 로그 위치나 sequence는 재처리 경계가 더 분명하다.  
가능하면 "어느 변경까지 반영했는지"를 total order에 가까운 값으로 기록하는 편이 안전하다.

### 3. 집계는 덮어쓰기보다 merge 규칙이 중요하다

summary refresh는 단순 overwrite가 아닐 때가 많다.

- 카운트는 누적
- 최댓값/최솟값은 비교
- 최근 상태는 최신 sequence가 이김
- 취소/환불은 역보정이 필요하다

따라서 summary table은 보통 다음 중 하나의 규칙을 가진다.

- upsert with additive update
- window recompute for affected bucket
- append-only delta 후 주기적 compaction

핵심은 "원본 한 건이 summary에 어떤 diff를 남기는가"를 명시하는 것이다.

### 4. late arrival와 replay를 기본값으로 둬야 한다

실무에서는 항상 다음이 생긴다.

- CDC connector 지연
- 브로커 재전송
- 재처리 배치
- 과거 데이터 보정

이때 summary refresh가 안전하려면:

- event id 기준 dedup
- bucket 단위 재계산
- watermark rewind 허용
- 영향 범위 재처리 도구

가 있어야 한다.

즉 summary pipeline은 "정상 흐름"보다 **이상 흐름을 재현 가능하게 만드는 것**이 더 중요하다.

### 5. freshness를 모르면 summary는 조용히 거짓말한다

summary table이 최신이 아닐 수 있다는 사실을 시스템이 모르면 문제가 커진다.

- 운영자는 dashboard 수치를 믿다가 잘못 판단한다
- 사용자에게 stale한 잔액/통계를 보여준다
- 장애가 나도 어느 구간이 누락됐는지 모른다

그래서 다음 메타데이터를 함께 남기는 편이 좋다.

- last processed watermark
- last successful refresh time
- lag metric
- backfill/replay in-progress 여부

summary는 데이터와 함께 **자신의 freshness 상태도 제공**해야 한다.
그리고 freshness와 별개로, source와 summary가 실제로 맞는지 검증하는 drift detection 루프도 필요하다.

### 6. "materialized view"라는 이름보다 운영 통제가 중요하다

엔진이 materialized view를 직접 지원하든, 애플리케이션이 summary table을 만들든 핵심은 같다.

- refresh boundary가 명확한가
- 재실행이 안전한가
- late correction을 흡수할 수 있는가
- 읽는 쪽이 freshness를 이해하는가

기능 이름에 기대기보다, 파이프라인의 replay safety와 observability를 먼저 보아야 한다.

## 실전 시나리오

### 시나리오 1. 주문 일별 매출 집계

`orders`에서 `paid_at` 기준 일별 매출 summary를 만든다.

필요한 설계:

- bucket은 일 단위
- 취소/환불 이벤트는 역보정
- late arrival가 있으면 해당 일 bucket 재계산 또는 보정 update
- dashboard에는 "마지막 반영 시각" 노출

### 시나리오 2. 사용자 활동 카운터

실시간에 가까운 카운트가 필요해 event마다 summary table에 `count = count + 1`을 한다.

이때:

- 중복 이벤트 dedup key 필요
- hot user는 contention이 심해질 수 있음
- 장기적으로 shard counter 또는 append-only delta가 더 나을 수 있음

### 시나리오 3. CDC 지연으로 관리 지표가 틀림

원본 트랜잭션은 성공했지만 summary refresh가 20분 늦었다.

이 경우는 단순 캐시 miss가 아니라 **freshness SLO 위반**이다.

- lag metric 경보
- fallback read 또는 "데이터 갱신 중" 표시
- watermark 기준 replay 도구

가 필요하다.

## 코드로 보기

```sql
CREATE TABLE summary_refresh_checkpoint (
  pipeline_name VARCHAR(100) PRIMARY KEY,
  last_watermark VARCHAR(255) NOT NULL,
  last_refreshed_at TIMESTAMP NOT NULL
);
```

```sql
CREATE TABLE daily_order_summary (
  order_date DATE PRIMARY KEY,
  paid_count BIGINT NOT NULL,
  paid_amount BIGINT NOT NULL,
  last_aggregated_at TIMESTAMP NOT NULL
);
```

```sql
INSERT INTO daily_order_summary (
  order_date,
  paid_count,
  paid_amount,
  last_aggregated_at
) VALUES (?, ?, ?, NOW())
ON DUPLICATE KEY UPDATE
  paid_count = daily_order_summary.paid_count + VALUES(paid_count),
  paid_amount = daily_order_summary.paid_amount + VALUES(paid_amount),
  last_aggregated_at = NOW();
```

```sql
-- replay-safe consumer 쪽에서 event dedup 테이블과 함께 사용
INSERT INTO processed_summary_event (event_id, processed_at)
VALUES (?, NOW());
```

위 예시는 additive counter에는 맞지만, 환불/정정처럼 역연산이 있는 경우에는 bucket 재계산이 더 안전할 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| full rebuild | 구현이 단순하다 | 느리고 freshness가 낮다 | 작은 데이터, 초기 단계 |
| incremental upsert | 지연이 짧다 | dedup과 late arrival 처리가 필요하다 | 운영 대시보드, near real-time read model |
| bucket recompute | 정정에 강하다 | 재계산 비용이 든다 | 일/시간 단위 집계 |
| append-only delta + compaction | replay가 쉽다 | 읽기 모델이 복잡하다 | 고트래픽 집계, audit가 중요한 경우 |

## 꼬리질문

> Q: summary table에서 watermark가 왜 중요한가요?
> 의도: 파생 상태의 반영 경계를 이해하는지 확인
> 핵심: 어느 변경까지 반영됐는지 알아야 누락, 재처리, freshness를 설명할 수 있다

> Q: late arriving event는 어떻게 처리하나요?
> 의도: 정상 흐름 밖의 정합성 감각 확인
> 핵심: dedup과 affected bucket 재계산 또는 보정 update 전략이 필요하다

> Q: summary table은 캐시와 무엇이 다른가요?
> 의도: 파생 상태의 운영 책임을 이해하는지 확인
> 핵심: 단순 재조회가 아니라, 원본 변경을 추적하는 증분 반영과 checkpoint 관리가 필요하다

## 한 줄 정리

summary table의 성패는 조회 속도보다, watermark·dedup·replay·freshness 메타데이터를 갖춘 증분 갱신 절차를 만들었는지에 달려 있다.
