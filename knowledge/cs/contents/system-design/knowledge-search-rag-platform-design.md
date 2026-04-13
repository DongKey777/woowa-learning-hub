# Knowledge Search / RAG Platform 설계

> 한 줄 요약: knowledge search / RAG platform은 문서 수집, 검색, 재랭킹, 컨텍스트 조립, 출처 추적을 결합해 지식 기반 응답을 만드는 시스템이다.

retrieval-anchor-keywords: knowledge search, RAG, retrieval augmented generation, embeddings, vector search, reranking, citation, chunking, context assembly, grounding, source ranking

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Search 시스템 설계](./search-system-design.md)
> - [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)
> - [Recommendation / Feed Ranking Architecture](./recommendation-feed-ranking-architecture.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Experimentation / A/B Testing Platform 설계](./experimentation-ab-testing-platform-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)

## 핵심 개념

RAG 플랫폼은 LLM에 문서를 붙이는 기능이 아니다.  
실전에서는 아래를 함께 설계해야 한다.

- document ingestion
- chunking and metadata
- sparse + vector retrieval
- reranking
- context assembly
- citation and grounding
- freshness and eval

즉, RAG는 검색과 생성의 결합된 지식 서빙 시스템이다.

## 깊이 들어가기

### 1. Retrieval 문제를 먼저 푼다

LLM이 똑똑해도 잘못된 컨텍스트를 주면 틀린 답을 만든다.

따라서 핵심은:

- 어떤 문서를 넣을지
- 어떤 chunk를 뽑을지
- 어떤 순서로 넣을지

### 2. Capacity Estimation

예:

- 1,000만 문서
- chunk 1억 개
- query 초당 2,000

이때 가장 중요한 병목은 vector retrieval latency와 context window 비용이다.

봐야 할 숫자:

- retrieval latency
- top-k recall
- rerank latency
- token budget
- citation coverage

### 3. Ingestion pipeline

```text
Source Docs
  -> Normalize
  -> Chunk
  -> Embed
  -> Index (sparse + vector)
  -> Metadata Store
  -> Evaluation / Reindex
```

### 4. Chunking and metadata

문서 쪼개기는 품질을 좌우한다.

- section-aware chunking
- overlap window
- title/path metadata
- freshness timestamp
- access control tags

### 5. Hybrid retrieval

RAG는 보통 sparse와 vector를 섞는다.

- keyword precision
- semantic recall
- reranking

이 부분은 [Search 시스템 설계](./search-system-design.md)와 [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)와 연결된다.

### 6. Context assembly

검색 결과를 그대로 넣으면 안 된다.

- token budget
- diversity
- dedup
- source ranking
- citation formatting

context assembly는 prompt 품질의 핵심이다.

### 7. Evaluation and freshness

RAG 품질은 계속 변한다.

- retrieval recall
- answer faithfulness
- citation accuracy
- latency
- hallucination rate

실험과 지표는 [Experimentation / A/B Testing Platform 설계](./experimentation-ab-testing-platform-design.md)와 [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: 사내 문서 검색 + 답변

문제:

- 정책 문서와 runbook을 정확히 찾아야 한다

해결:

- permission-aware retrieval
- source citation
- recency-aware ranking

### 시나리오 2: 제품 Q&A

문제:

- 오래된 문서가 답변을 오염시킨다

해결:

- freshness scoring
- reindex pipeline
- versioned sources

### 시나리오 3: 답변 근거 부족

문제:

- LLM이 근거 없는 답을 만든다

해결:

- citation coverage metric
- low-confidence fallback
- answer with abstain

## 코드로 보기

```pseudo
function answer(query, user):
  chunks = retrieve(query, user.permissions)
  ranked = rerank(chunks, query)
  context = assemble(ranked, tokenBudget=8000)
  return generate(context)
```

```java
public RagResponse answer(RagRequest req) {
    List<Chunk> chunks = retriever.retrieve(req.query(), req.user());
    return generator.generate(contextAssembler.build(chunks));
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| sparse search only | 단순하고 정확하다 | 의미 검색 약함 | 키워드 중심 |
| vector search only | 의미 recall이 좋다 | precision과 explainability 약함 | semantic search |
| hybrid retrieval | 균형이 좋다 | 운영 복잡도 증가 | 대부분의 RAG |
| long context only | 구현이 쉽다 | 비용이 크고 noisy | 소규모 |
| citation-first RAG | 신뢰성이 높다 | 조립 복잡도 증가 | enterprise knowledge |

핵심은 RAG가 LLM 기능이 아니라 **검색, 재랭킹, 컨텍스트 조립, 출처 검증을 통합한 지식 서빙 플랫폼**이라는 점이다.

## 꼬리질문

> Q: RAG에서 검색이 왜 중요한가요?
> 의도: retrieval quality와 generation 품질의 관계 이해 확인
> 핵심: 잘못된 컨텍스트는 좋은 모델도 망친다.

> Q: chunking이 왜 어려운가요?
> 의도: 문서 구조와 token budget 이해 확인
> 핵심: 너무 작으면 맥락이 깨지고, 너무 크면 비용이 올라간다.

> Q: sparse와 vector를 왜 같이 쓰나요?
> 의도: precision/recall 균형 이해 확인
> 핵심: 키워드 정확도와 의미 유사도를 함께 잡기 위해서다.

> Q: citation이 왜 필요한가요?
> 의도: grounding과 신뢰성 이해 확인
> 핵심: 답변 출처를 추적할 수 있어야 신뢰성이 생긴다.

## 한 줄 정리

Knowledge search / RAG platform은 문서 수집과 하이브리드 검색, 재랭킹, 컨텍스트 조립, 출처 추적을 통합해 신뢰 가능한 지식 응답을 만드는 시스템이다.

