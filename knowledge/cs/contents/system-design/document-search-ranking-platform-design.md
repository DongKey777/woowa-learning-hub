# Document Search / Ranking Platform 설계

> 한 줄 요약: document search and ranking platform은 키워드, 의미 검색, 권한 필터, 랭킹 신호, 설명 가능한 결과를 결합한 엔터프라이즈 문서 검색 시스템이다.

retrieval-anchor-keywords: document search ranking, enterprise search, ACL filter, BM25, reranking, snippets, freshness, hybrid search, query understanding, relevance

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Search 시스템 설계](./search-system-design.md)
> - [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)
> - [Search Hit Overlay Pattern](./search-hit-overlay-pattern.md)
> - [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md)
> - [Knowledge Search / RAG Platform 설계](./knowledge-search-rag-platform-design.md)
> - [Experimentation / A/B Testing Platform 설계](./experimentation-ab-testing-platform-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)

## 핵심 개념

문서 검색은 단순한 full-text query가 아니다.
실전에서는 아래를 함께 설계해야 한다.

- 권한 필터와 문서 가시성
- keyword + semantic hybrid retrieval
- reranking과 snippet 생성
- freshness와 reindex
- personalized ranking
- explainability와 citation

즉, 문서 검색 플랫폼은 조직 지식에 대한 검색 품질 시스템이다.

## 깊이 들어가기

### 1. 검색 대상이 다르다

엔터프라이즈 문서는 다양한 형태로 존재한다.

- PDF
- DOCX
- wiki
- ticket
- slide
- comment

검색 품질은 문서 포맷보다도 chunking과 metadata에 크게 좌우된다.

### 2. Capacity Estimation

예:

- 1억 chunk
- 초당 2,000 search query
- refresh lag 1분 이하

문서 검색은 retrieval latency와 index freshness 둘 다 중요하다.
단순 DB 검색으로는 사용자 기대치를 만족하기 어렵다.

봐야 할 숫자:

- query latency
- recall@k
- nDCG
- freshness lag
- ACL filter cost

### 3. Retrieval pipeline

```text
Query
  -> Normalize
  -> Keyword Retrieve
  -> Semantic Retrieve
  -> ACL Filter
  -> Rerank
  -> Snippet / Highlight
```

### 4. ACL 필터

문서 검색의 핵심은 "찾았다"가 아니라 "볼 수 있는가"다.

- 문서 소유자
- team membership
- tenant scope
- confidentiality label

권한 필터는 retrieval 후처리가 아니라 초기에 넣는 것이 좋다.

### 5. ranking signals

랭킹 신호는 보통 섞인다.

- BM25 score
- recency
- popularity
- document quality
- user/team affinity

실험 없이 랭킹을 바꾸면 정답이 없는 싸움이 된다.

### 6. snippets and highlights

검색은 제목만 보여주지 않는다.

- matched snippet
- highlight
- result preview
- source path

이 단계가 좋아야 사용자가 클릭한다.

### 7. freshness and reindex

문서 수정은 검색에 바로 반영돼야 한다.

- incremental indexing
- alias cutover
- soft delete tombstone
- backfill job

이 부분은 [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: 정책 문서 검색

문제:

- 오래된 정책이 상단에 떠 있으면 안 된다

해결:

- recency boost
- versioned document
- policy tag ranking

### 시나리오 2: 권한 없는 문서 노출

문제:

- 검색 결과에는 떠도 실제로 보면 안 되는 문서가 있다

해결:

- ACL filter
- doc-level security
- tenant-aware routing

### 시나리오 3: 문서 제목이 모호함

문제:

- 유사한 제목이 너무 많다

해결:

- semantic rerank
- snippet quality
- team affinity

## 코드로 보기

```pseudo
function search(query, user):
  candidates = keywordIndex.lookup(query) + vectorIndex.lookup(query)
  visible = aclFilter(candidates, user)
  ranked = rerank(visible, query, user)
  return buildSnippets(ranked)
```

```java
public List<SearchResult> search(SearchRequest req) {
    return rankingService.rank(retriever.retrieve(req), req.user());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Keyword only | 단순하고 정확하다 | 의미 검색 약함 | 작은 문서 집합 |
| Hybrid search | recall과 precision 균형 | 운영 복잡 | 대부분의 기업 검색 |
| ACL at query time | 유연하다 | latency 증가 | 권한이 복잡할 때 |
| ACL at index time | 빠르다 | 재색인이 필요 | 강한 격리 |
| Personalized ranking | 만족도가 높다 | 설명이 어려움 | 사내 검색/포털 |

핵심은 문서 검색 플랫폼이 단순 검색 엔진이 아니라 **권한, 랭킹, freshness, 설명 가능성을 함께 만족하는 정보 검색 시스템**이라는 점이다.

## 꼬리질문

> Q: document search와 generic search는 무엇이 다른가요?
> 의도: 권한과 문서 구조 차이 이해 확인
> 핵심: 문서 검색은 ACL, snippet, freshness가 더 중요하다.

> Q: reranking은 왜 필요한가요?
> 의도: 후보 검색과 순위의 차이 이해 확인
> 핵심: 검색 후보를 더 의미 있게 정렬해야 한다.

> Q: ACL 필터는 어디에 두나요?
> 의도: 보안 경계와 성능 trade-off 이해 확인
> 핵심: 검색 초기에 넣는 것이 안전하고 효율적이다.

> Q: freshness를 높이면 무엇이 어려워지나요?
> 의도: 실시간 반영의 비용 이해 확인
> 핵심: index update와 reindex 운영이 복잡해진다.

## 한 줄 정리

Document search/ranking platform은 권한 필터, 하이브리드 검색, reranking, snippet, freshness를 결합한 엔터프라이즈 문서 검색 시스템이다.
