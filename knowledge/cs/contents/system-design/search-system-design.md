# Search 시스템 설계

> 한 줄 요약: 검색 시스템은 단순 조회가 아니라, 인덱싱 파이프라인과 랭킹, freshness, hot query를 함께 관리하는 분산 정보 검색 시스템이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [인덱스와 실행 계획](../database/index-and-explain.md)
> - [Slow Query Analysis Playbook](../database/slow-query-analysis-playbook.md)
> - [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)
> - [RAG Topic Map](../../rag/topic-map.md)

---

## 핵심 개념

검색 시스템은 DB `LIKE` 검색을 예쁘게 감싼 것이 아니다.  
문서 수집, 정규화, 토큰화, 역인덱스, 랭킹, 캐시, freshness를 동시에 다룬다.

가장 먼저 구분해야 할 것은 검색의 종류다.

- 키워드 검색
- 필터 검색
- 자동완성/제안 검색
- 로그/이벤트 검색
- 의미 기반 검색

실무에서는 "검색"이라고 해도 위가 서로 다른 시스템이다.

---

## 깊이 들어가기

### 1. 검색 파이프라인

기본 구성은 다음과 같다.

- source of truth
- ingest pipeline
- parser/tokenizer
- inverted index
- ranking service
- query cache

흐름은 보통 이렇다.

1. 원본 데이터가 들어온다.
2. 인덱싱 파이프라인이 문서를 정규화한다.
3. 토큰과 필드가 역인덱스에 저장된다.
4. 질의 시 후보 문서를 빠르게 찾는다.
5. 랭킹으로 정렬한다.

### 2. 역인덱스

검색의 핵심은 "단어 -> 문서 목록" 구조다.

```text
"redis" -> [doc1, doc7, doc18]
"spring" -> [doc2, doc7, doc11]
```

여기에 다음이 붙는다.

- term frequency
- document frequency
- field boost
- recency boost
- personalization

### 3. 인덱싱과 freshness

검색은 읽기만 빠르면 안 된다.  
새 글이 검색에 반영되는 시간도 중요하다.

선택지:

| 방식 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| near real-time indexing | 반영이 빠르다 | 시스템이 복잡하다 | 뉴스/커뮤니티 |
| batch indexing | 단순하다 | 지연이 크다 | 로그/오프라인 분석 |
| hybrid | 균형이 좋다 | 구현이 어렵다 | 대부분의 서비스 |

### 4. 랭킹

검색은 결과 수가 아니라 순서가 중요하다.

랭킹에 쓰는 신호:

- 키워드 일치도
- 최신성
- 클릭률
- 인기도
- 개인화 신호

랭킹이 들어가면 검색은 단순 인덱스 조회가 아니라 실험 시스템이 된다.

### 5. 샤딩과 hot query

자주 검색되는 질의는 특정 shard를 망가뜨릴 수 있다.

대표 대응:

- query cache
- shard replication
- hot query 분리
- consistent hashing
- precomputed suggestion

### 6. DB와의 관계

검색 시스템은 DB를 대체하지 않는다.  
원본 무결성은 DB가, 검색은 검색 엔진이 담당한다.

DB 관점으로는:

- 정합성 있는 원본 저장
- 검색용 비정규화
- 인덱스 설계 분리

이 부분은 [인덱스와 실행 계획](../database/index-and-explain.md)과 [정규화 vs 반정규화 Trade-off](../database/normalization-denormalization-tradeoffs.md)와 연결된다.

---

## 실전 시나리오

### 시나리오 1: 게시글 검색

요구사항:

- 제목, 본문, 태그 검색
- 최신순/정확도순 정렬
- 삭제/비공개 반영

설계:

- 문서 저장소와 검색 인덱스 분리
- 태그/제목/본문 field boost
- soft delete 반영

### 시나리오 2: 자동완성

자동완성은 full-text search보다 더 민감하다.

필요한 것:

- prefix index
- popular suggestion cache
- 짧은 latency

### 시나리오 3: 운영 로그 검색

로그 검색은 freshness보다 throughput이 중요하다.

따라서:

- batch ingest 허용
- time partitioning
- retention policy
- 필터 우선 최적화

---

## 코드로 보기

```pseudo
function indexDocument(doc):
    tokens = tokenize(normalize(doc.text))
    for token in tokens:
        invertedIndex.add(token, doc.id, doc.boost)

function search(query):
    tokens = tokenize(normalize(query))
    candidates = intersect(invertedIndex.lookup(tokens))
    ranked = rank(candidates, query)
    return ranked
```

```java
public List<SearchResult> search(String query, int limit) {
    List<String> tokens = tokenizer.tokenize(query);
    Set<Long> candidates = index.lookup(tokens);
    return rankingService.rank(candidates, query).stream()
        .limit(limit)
        .toList();
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DB LIKE 검색 | 단순하다 | 느리고 확장성이 낮다 | 매우 작은 규모 |
| 검색 엔진 도입 | 강력하다 | 운영 복잡도가 높다 | 대부분의 검색 시스템 |
| Near real-time indexing | 반영이 빠르다 | 파이프라인이 복잡하다 | 커뮤니티/뉴스 |
| Batch indexing | 안정적이다 | 최신성이 떨어진다 | 로그/리포트 |

핵심은 "검색을 DB에서 할 수 있나"가 아니라 **사용자가 기대하는 relevance와 freshness를 어떤 비용으로 만족할 것인가**다.

---

## 꼬리질문

> Q: DB 인덱스로 검색 시스템을 대체할 수 있나요?
> 의도: 검색과 OLTP를 구분하는지 확인
> 핵심: 단순 필터는 가능해도 ranking/freshness/hot query는 별도 설계가 필요하다.

> Q: 검색 결과 순서는 왜 자꾸 바뀌나요?
> 의도: ranking과 freshness 이해 여부 확인
> 핵심: 최신성, 클릭 신호, personal signal이 함께 들어가면 순서가 동적이다.

## 한 줄 정리

검색 시스템은 역인덱스와 랭킹, freshness, hot query를 함께 다루는 분산 검색 파이프라인이다.
