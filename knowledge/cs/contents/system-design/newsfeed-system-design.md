# Newsfeed 시스템 설계

> 한 줄 요약: 뉴스피드는 팔로우 그래프, fan-out, 캐시, 정렬, hot key를 동시에 다루는 읽기 중심 분산 시스템이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [분산 캐시 설계](./distributed-cache-design.md)
> - [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)
> - [채팅 시스템 설계](./chat-system-design.md)
> - [MVCC, Replication, Sharding](../database/mvcc-replication-sharding.md)

---

## 핵심 개념

뉴스피드는 "글 목록을 보여주는 화면"처럼 보이지만, 실제로는 다음 문제를 같이 풀어야 한다.

- 팔로우 관계가 많아도 응답이 빨라야 한다.
- 최신 글이 위에 와야 한다.
- 큰 계정이 생겨도 시스템이 죽지 않아야 한다.
- 피드 생성 시점과 피드 조회 시점의 비용을 나눠야 한다.
- 무한 스크롤, 좋아요 수, 댓글 수, 광고 노출 같은 부가 요구를 함께 만족해야 한다.

핵심 의사결정은 하나다.

- `fan-out on write`: 글이 올라올 때 팔로워 inbox에 미리 써 넣는다.
- `fan-out on read`: 조회할 때 팔로워/피드 소스를 계산한다.

대부분의 서비스는 이 둘을 섞는다.  
작은 계정은 write fan-out, 큰 계정은 read fan-out이나 별도 경로를 둔다.

---

## 깊이 들어가기

### 1. 요구사항 정리

먼저 확인해야 할 질문:

- 피드는 전역 타임라인인가, 팔로우 기반인가
- 광고/추천이 포함되는가
- 사진/동영상 비중이 큰가
- 실시간성이 중요한가
- 읽기와 쓰기 중 무엇이 더 많은가

뉴스피드는 대개 읽기 비중이 높지만, 새 글이 올라오는 순간에는 burst write가 생긴다.  
그래서 평균 QPS보다 "대형 계정이 글 하나 올렸을 때 무엇이 터지는가"를 먼저 봐야 한다.

### 2. Capacity Estimation

간단한 가정:

- DAU 500만
- 사용자당 하루 피드 진입 20회
- 평균 피드 응답 20 KB
- 하루 글쓰기 50만 건
- 팔로워 수 상위 1%가 전체 노출의 대부분을 차지

이때 읽기 트래픽은 안정적으로 보이지만, 대형 계정의 write fan-out이 병목이 된다.  
즉, "피드는 읽기 시스템"처럼 보여도 실제 설계는 **쓰기와 캐시 무효화**가 중심이 된다.

### 3. 아키텍처

기본 구성:

- API Server
- Follow graph store
- Post store
- Feed cache / inbox store
- Queue / stream
- Ranking service
- Media storage

전형적인 흐름:

1. 사용자가 글을 쓴다.
2. 글은 post store에 저장된다.
3. 팔로워 inbox를 갱신하거나 이벤트를 큐에 넣는다.
4. 조회 시 inbox 또는 피드 소스를 읽는다.
5. ranking service가 정렬/추천을 추가한다.

### 4. 저장 전략

피드 저장은 보통 세 층으로 나눈다.

| 계층 | 역할 | 예시 |
|------|------|------|
| Source of truth | 원본 저장 | post table |
| Inbox cache | 개인화 피드 | user_feed |
| Ranking material | 정렬/추천 특징값 | score, recency |

원본은 정합성 중심, inbox는 속도 중심, ranking은 실험 중심이다.

### 5. 병목 지점

대표적인 병목:

- 유명 계정의 fan-out 폭증
- 팔로우 그래프 조회 비용
- 무한 스크롤에서 중복/누락
- cache invalidation
- 랭킹 계산 비용

특히 hot key는 특정 게시물 하나가 과도하게 조회될 때 발생한다.  
이때는 consistent hashing, local cache, request coalescing이 함께 필요하다.

### 6. 일관성과 사용자 경험

피드에서 강한 일관성은 비용이 크다.  
대개 사용자 경험은 "몇 초 안에 보이면 된다" 수준이면 충분하다.

선택지:

- 강한 일관성: 즉시 반영, 비용 큼
- 최종 일관성: 빠르고 확장성 좋음
- 부분 일관성: 본인 글은 즉시 반영, 타인 글은 지연 허용

실제 서비스는 보통 부분 일관성을 택한다.

---

## 실전 시나리오

### 시나리오 1: 일반 사용자 피드

작은 팔로워 집합에서는 write fan-out이 효율적이다.

- 게시 시 팔로워 inbox에 미리 저장
- 조회는 inbox를 그대로 읽음
- 새 글 정렬은 created_at 기준

이 방식은 조회가 빠르지만, 팔로워가 늘수록 쓰기 비용이 커진다.

### 시나리오 2: 대형 계정

팔로워가 수백만이면 write fan-out이 터진다.

대응:

- 대형 계정은 read fan-out으로 분기
- recent posts를 별도 저장
- 인기 계정 전용 캐시
- batch / async fan-out

### 시나리오 3: 무한 스크롤 중복

사용자가 같은 글을 여러 번 보는 버그는 흔하다.

원인:

- cursor 설계가 불안정함
- 정렬 키가 중복됨
- 페이지 경계에 같은 timestamp가 몰림

해결:

- `created_at + id` 복합 커서 사용
- last-seen offset 저장
- dedup 처리

---

## 코드로 보기

```pseudo
function getFeed(userId, cursor):
    if cache.exists("feed:" + userId + ":" + cursor):
        return cache.get(...)

    items = feedStore.readInbox(userId, cursor, limit=20)
    ranked = rankingService.rank(items)
    cache.set(..., ranked, ttl=30s)
    return ranked
```

```java
public FeedPage buildFeed(long userId, FeedCursor cursor) {
    List<Post> inbox = feedRepository.readInbox(userId, cursor, 20);
    List<FeedItem> ranked = rankingService.rank(inbox);
    cache.put(cacheKey(userId, cursor), ranked, Duration.ofSeconds(30));
    return new FeedPage(ranked, cursor.next());
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|-------------|
| Fan-out on write | 조회가 빠르다 | 쓰기 비용이 크다 | 일반 사용자 비중이 높을 때 |
| Fan-out on read | 쓰기 단순 | 조회가 무겁다 | 초대형 계정이 많을 때 |
| 캐시 중심 | 빠르고 유연하다 | 무효화가 어렵다 | 조회 비중이 매우 높을 때 |
| DB 중심 | 단순하다 | 확장 한계가 빠르다 | 초기 MVP |

피드는 보통 "하나의 정답"이 아니라, 사용자 규모별로 다른 경로를 섞는 문제다.

## 꼬리질문

> Q: 피드에서 전역 순서 보장을 꼭 해야 하나요?
> 의도: 과도한 일관성 요구를 거를 수 있는지 확인
> 핵심: 대부분 사용자 체감 기준의 부분 순서면 충분하다

> Q: 대형 계정이 생기면 왜 write fan-out이 터지나요?
> 의도: fan-out 비용과 hot path 이해 여부 확인
> 핵심: 팔로워 수에 비례해 쓰기 비용이 선형 이상으로 커진다

## 한 줄 정리

뉴스피드는 팔로우 그래프와 fan-out 전략을 어떻게 섞느냐가 설계의 핵심이다.
