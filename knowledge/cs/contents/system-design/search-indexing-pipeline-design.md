# Search Indexing Pipeline 설계

> 한 줄 요약: 검색 인덱싱 파이프라인은 원본 데이터를 정규화하고 토큰화해 검색 엔진에 반영하는 지속적 데이터 처리 시스템이다.

retrieval-anchor-keywords: search indexing pipeline, ingest, normalization, tokenization, inverted index, refresh latency, reindex, schema evolution, backfill, dead letter queue, freshness

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Search 시스템 설계](./search-system-design.md)
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)

## 핵심 개념

검색 인덱싱 파이프라인은 "DB 변경을 검색 엔진에 복제하는 ETL"보다 더 넓다.  
실전에서는 다음까지 포함한다.

- 소스 데이터 수집
- 정규화와 스키마 변환
- 토큰화와 필드 추출
- 역인덱스 반영
- freshness 관리
- reindex와 backfill
- 장애 복구와 DLQ

즉, 검색 품질은 query 시점보다 ingest 시점에서 이미 결정된다.

## 깊이 들어가기

### 1. Source of truth와 index는 다르다

원본 DB는 정합성 중심이고, 검색 인덱스는 조회 최적화 중심이다.  
둘을 같은 저장소로 취급하면 다음 문제가 생긴다.

- 검색 쿼리가 원본 DB를 압박한다
- schema 변경이 검색을 망친다
- freshness와 query latency가 서로 충돌한다

### 2. Capacity Estimation

예:

- 초당 신규/변경 문서 5,000건
- 평균 문서 크기 2 KB
- reindex window 24시간

인덱싱 파이프라인은 단순 쓰기량뿐 아니라, reprocess와 backfill을 감당해야 한다.  
그래서 평상시 처리량보다 장애 후 재처리 속도를 같이 봐야 한다.

보는 숫자:

- ingest lag
- indexing throughput
- reindex duration
- segment merge cost
- DLQ 적재량

### 3. 파이프라인 단계

```text
CDC / Event Stream
  -> Normalize
  -> Enrich
  -> Tokenize
  -> Build Document
  -> Write Index
  -> Refresh / Commit
```

실무에서 각 단계는 독립적으로 실패할 수 있다.  
그래서 단계별 retry와 DLQ가 필요하다.

### 4. 스키마와 버전 관리

검색 인덱스는 schema evolution에 민감하다.

- 필드 추가
- analyzer 변경
- ranking feature 추가
- 정규화 규칙 변경

권장 전략:

- index versioning
- alias cutover
- backward compatible document schema
- reindex job 분리

이런 구조가 없으면 운영 중 schema change가 곧 서비스 장애가 된다.

### 5. Freshness와 consistency

검색은 "반영 속도"가 중요하다.

선택지:

- near real-time indexing
- micro-batch indexing
- batch reindex

보통은 신규 데이터는 빠르게, 대량 재처리는 배치로 섞는다.  
즉, `hot path`와 `cold path`를 분리하는 것이 핵심이다.

### 6. Reindex와 backfill

인덱스가 잘못되면 다시 만들어야 한다.

그러려면:

- source of truth에서 재수집 가능해야 한다
- reindex를 idempotent하게 만들어야 한다
- alias를 통해 무중단 전환해야 한다
- backfill이 live indexing을 방해하지 않아야 한다

### 7. 장애와 DLQ

인덱싱은 실패가 흔하다.

- malformed document
- analyzer 오류
- external enrichment timeout
- partial shard failure

대응:

- dead-letter queue
- bad record quarantine
- retry with bounded backoff
- poison pill detection

이 부분은 [Job Queue 설계](./job-queue-design.md)와 묶어서 봐야 한다.

## 실전 시나리오

### 시나리오 1: 게시글 검색 인덱싱

문제:

- 제목, 본문, 태그를 검색해야 한다
- 삭제/비공개 상태가 즉시 반영돼야 한다

해결:

- event stream으로 변경 이벤트를 받는다
- soft delete는 delete tombstone으로 반영한다
- alias cutover로 reindex를 무중단 처리한다

### 시나리오 2: 검색 analyzer 변경

문제:

- 토큰화 규칙을 바꿔야 한다

해결:

- 새 index version을 만든다
- backfill 후 alias를 전환한다
- 구 버전은 점진적으로 retire한다

### 시나리오 3: 대규모 backfill

문제:

- 수억 건 문서를 다시 색인해야 한다

해결:

- partition 단위로 병렬화한다
- backfill rate limit을 둔다
- live traffic과 worker pool을 분리한다

## 코드로 보기

```pseudo
function processChange(change):
  doc = normalize(change)
  doc = enrich(doc)
  tokens = tokenize(doc)
  index.write(doc.id, tokens)

function reindex(snapshot):
  for record in snapshot:
    queue.publish(record)
```

```java
public IndexedDocument build(ChangeEvent event) {
    NormalizedDocument doc = normalizer.normalize(event);
    return indexer.index(doc);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Sync indexing | 단순하다 | write latency 증가 | 아주 작은 시스템 |
| Async indexing | 서비스 경로가 가볍다 | freshness 지연 | 대부분의 실서비스 |
| NRT indexing | 반영이 빠르다 | 운영 복잡도 높음 | 검색 중심 서비스 |
| Batch indexing | 안정적이다 | 지연이 길다 | 로그/아카이브 |
| Alias cutover | 무중단 전환이 쉽다 | 운영 절차 필요 | schema migration |

핵심은 "색인만 만든다"가 아니라 **변경, 반영 지연, 재처리, 스키마 진화까지 운영 가능한가**다.

## 꼬리질문

> Q: 검색 인덱스를 DB 대체로 쓰면 안 되나요?
> 의도: source of truth와 search index 구분 확인
> 핵심: 검색 인덱스는 조회 최적화용이라 정합성의 원천이 되기 어렵다.

> Q: reindex는 왜 어려운가요?
> 의도: 대량 재처리와 무중단 전환 이해 확인
> 핵심: 데이터량, freshness, live traffic, schema change가 동시에 걸리기 때문이다.

> Q: DLQ에 들어간 문서는 어떻게 하나요?
> 의도: 운영 복구 감각 확인
> 핵심: 원인 분석 후 수정 재처리하거나 quarantine 한다.

> Q: freshness를 높이면 무엇을 희생하나요?
> 의도: latency와 consistency trade-off 이해 확인
> 핵심: write 비용과 운영 복잡도가 올라간다.

## 한 줄 정리

Search indexing pipeline은 원본 변경을 검색 가능한 형태로 지속 반영하고, freshness와 재처리, 스키마 진화를 함께 다루는 시스템이다.

