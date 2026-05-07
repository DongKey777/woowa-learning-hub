---
schema_version: 3
title: Recommendation / Feed Ranking Architecture
concept_id: system-design/recommendation-feed-ranking-architecture
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- recommendation system
- feed ranking
- candidate generation
- feature store
aliases:
- recommendation system
- feed ranking
- candidate generation
- feature store
- model serving
- exploration exploitation
- freshness
- personalization
- ranking pipeline
- online inference
- A/B testing
- Recommendation / Feed Ranking Architecture
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/newsfeed-system-design.md
- contents/system-design/search-system-design.md
- contents/system-design/system-design-framework.md
- contents/system-design/back-of-envelope-estimation.md
- contents/system-design/distributed-cache-design.md
- contents/system-design/search-indexing-pipeline-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Recommendation / Feed Ranking Architecture 설계 핵심을 설명해줘
- recommendation system가 왜 필요한지 알려줘
- Recommendation / Feed Ranking Architecture 실무 트레이드오프는 뭐야?
- recommendation system 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Recommendation / Feed Ranking Architecture를 다루는 deep_dive 문서다. 추천과 피드 랭킹은 후보 생성, 특징 추출, 점수화, 실험, 서빙 캐시를 함께 설계하는 실시간 의사결정 시스템이다. 검색 질의가 recommendation system, feed ranking, candidate generation, feature store처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Recommendation / Feed Ranking Architecture

> 한 줄 요약: 추천과 피드 랭킹은 후보 생성, 특징 추출, 점수화, 실험, 서빙 캐시를 함께 설계하는 실시간 의사결정 시스템이다.

retrieval-anchor-keywords: recommendation system, feed ranking, candidate generation, feature store, model serving, exploration exploitation, freshness, personalization, ranking pipeline, online inference, A/B testing

**난이도: 🔴 Advanced**

> 관련 문서:
> - [뉴스피드 시스템 설계](./newsfeed-system-design.md)
> - [Search 시스템 설계](./search-system-design.md)
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)

## 핵심 개념

추천/랭킹 시스템은 "좋아 보이는 순서"를 만드는 기능이 아니다.  
실전에서는 아래를 동시에 맞춰야 한다.

- 후보를 빠르게 모으기
- 개인화 특징을 안전하게 붙이기
- 실시간성과 freshness를 유지하기
- 실험을 통해 성능을 검증하기
- 편향과 반복 노출을 완화하기

즉, 랭킹은 단순 정렬이 아니라 **검색, 피드, 추천, 실험을 묶은 서빙 파이프라인**이다.

## 깊이 들어가기

### 1. 전체 파이프라인

일반적인 구조:

```text
Candidate Generation
  -> Filtering
  -> Feature Fetch
  -> Scoring
  -> Re-ranking
  -> Cache / Serve
```

각 단계의 책임이 다르다.

- candidate generation: 가능한 후보를 넓게 모은다
- filtering: policy / block / eligibility를 적용한다
- feature fetch: 사용자와 아이템 정보를 가져온다
- scoring: 모델이나 규칙으로 점수를 계산한다
- re-ranking: 다양성, freshness, business rule을 반영한다

### 2. Capacity Estimation

예:

- 초당 20,000 feed request
- 요청당 후보 500개
- feature fetch 20개

이 정도면 online feature store와 cache가 핵심 병목이다.  
랭킹의 비용은 `request 수 * 후보 수 * feature 수`로 커진다.

봐야 할 숫자:

- p95 inference latency
- feature fetch latency
- cache hit ratio
- model fallback rate
- freshness lag

### 3. 후보 생성 전략

추천은 모든 아이템을 다 점수화하지 않는다.

후보 생성 방식:

- 팔로우/그래프 기반
- 최근 상호작용 기반
- 유사 아이템 기반
- 인기/트렌딩 기반
- 검색 결과 기반

후보 생성은 recall 중심, 랭킹은 precision 중심이다.

### 4. Feature store와 온라인 서빙

특징은 배치와 온라인이 다를 수 있다.

- offline feature: 학습용
- online feature: 서빙용 최신 상태

문제는 feature drift와 freshness다.  
특징이 늦게 반영되면 모델은 오래된 정보를 기반으로 판단한다.

그래서 보통:

- batch feature store
- online feature store
- fallback default feature

를 함께 둔다.

### 5. 실험과 버전 관리

랭킹은 운영하면서 계속 바뀐다.

필수 요소:

- model version
- feature version
- ranking config version
- A/B test bucket
- rollback plan

실험 없이 랭킹을 바꾸면 효과를 측정할 수 없다.

### 6. 다양성, 편향, 반복 노출

단순 점수 정렬은 같은 유형만 반복 노출시키기 쉽다.

re-ranking에서 자주 넣는 규칙:

- 동일 author 연속 노출 제한
- 카테고리 다양성
- 광고/추천 비율 제한
- 최신성과 popularity의 균형

이 단계는 순수 모델보다 제품 정책이 더 강하게 개입한다.

### 7. Cache와 freshness

랭킹 결과는 자주 캐시되지만, 캐시만 믿으면 늦어진다.

전략:

- candidate cache
- score cache
- short-lived result cache
- personalized cache segment

이 부분은 [뉴스피드 시스템 설계](./newsfeed-system-design.md)와 [분산 캐시 설계](./distributed-cache-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: 홈 피드 랭킹

문제:

- 사용자가 앱을 열 때마다 다른 순서가 필요하다

해결:

- candidate generation은 inbox + trending으로 넓게 잡는다
- feature store에서 개인화 신호를 가져온다
- re-ranking에서 다양성과 최신성을 넣는다

### 시나리오 2: 추천 품질이 떨어짐

문제:

- 사용자가 비슷한 콘텐츠만 계속 본다

해결:

- exploration 비중을 조금 늘린다
- 동일 계열 반복 노출을 제한한다
- 실험 bucket으로 회귀를 확인한다

### 시나리오 3: feature store가 느려짐

문제:

- feature fetch가 p95를 끌어올린다

해결:

- hot feature는 cache에 올린다
- fallback feature를 둔다
- candidate 수를 줄인다

## 코드로 보기

```pseudo
function rankFeed(userId):
  candidates = candidateService.get(userId)
  features = featureStore.bulkGet(userId, candidates)
  scores = model.score(userId, candidates, features)
  return rerank(scores, businessRules)
```

```java
public List<Item> rank(long userId, List<Item> candidates) {
    Map<Long, FeatureVector> features = featureStore.bulkGet(userId, candidates);
    return scorer.score(userId, candidates, features);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Rule-based ranking | 단순하고 설명 가능 | 정교함이 부족하다 | 초기 제품 |
| ML ranking | 품질이 좋다 | feature/model 운영이 어렵다 | 대규모 추천 |
| Candidate cache | latency가 낮다 | freshness가 늦을 수 있다 | 조회가 많은 서비스 |
| Real-time inference | 반응성이 좋다 | 비용이 크다 | 개인화가 강한 경우 |
| Re-ranking layer | business rule 반영 쉽다 | 시스템이 복잡해진다 | 실서비스 대부분 |

핵심은 "모델이 똑똑한가"가 아니라 **후보, 특징, 실험, 정책이 각자 분리돼 운영 가능한가**다.

## 꼬리질문

> Q: 후보 생성과 랭킹은 왜 분리하나요?
> 의도: recall과 precision의 차이 이해 확인
> 핵심: 모든 아이템을 점수화하면 비용이 너무 커지기 때문이다.

> Q: feature store는 왜 필요한가요?
> 의도: 온라인/오프라인 특징 관리 이해 확인
> 핵심: 학습과 서빙의 특징을 일관되게 관리하기 위해서다.

> Q: A/B 테스트 없이 랭킹을 바꾸면 왜 위험한가요?
> 의도: 실험과 롤백 감각 확인
> 핵심: 품질 저하를 객관적으로 판단하기 어렵다.

> Q: freshness와 personalization 중 무엇이 더 중요한가요?
> 의도: 제품/시스템 trade-off 이해 확인
> 핵심: 도메인마다 다르며, 보통은 둘을 섞어야 한다.

## 한 줄 정리

추천과 feed ranking은 후보 생성부터 feature fetch, scoring, re-ranking, 실험까지 이어지는 실시간 개인화 파이프라인이다.

