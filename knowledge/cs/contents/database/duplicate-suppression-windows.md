# Duplicate Suppression Windows

> 한 줄 요약: duplicate suppression window는 같은 이벤트를 무한히 기억하지 않고, 일정 시간 동안만 중복을 막는 현실적인 dedup 전략이다.

관련 문서: [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md), [Transactional Inbox와 Dedup Design](./transactional-inbox-dedup-design.md), [Exactly-Once 신화와 DB + Queue 경계](./exactly-once-myths-db-queue.md)
Retrieval anchors: `duplicate suppression window`, `dedup window`, `ttl dedup`, `time bucket`, `duplicate suppression`

## 핵심 개념

모든 중복을 영원히 저장할 수는 없다.  
그래서 실무에서는 중복을 막는 기간을 정해 suppression window를 둔다.

왜 중요한가:

- 웹훅, 재시도, 배치 재실행은 보통 짧은 시간 안에 몰린다
- 무한 dedup은 저장 공간과 조회 비용이 커진다
- window는 현실적인 메모리와 정확성의 균형점이다

window 전략은 “완벽한 중복 방지”가 아니라, **운영 가능한 중복 억제**다.

## 깊이 들어가기

### 1. window가 필요한 이유

같은 요청이 연달아 두세 번 들어오는 경우는 많지만, 수개월 뒤 같은 요청이 다시 들어오는 건 다른 문제일 수 있다.

- 재시도 폭주
- 모바일 네트워크 재전송
- 큐의 일시적 중복 전달

이런 케이스는 짧은 window로 충분히 잡을 수 있다.

### 2. 어떻게 구현하나

- request hash + time bucket
- event_id + TTL
- Redis set with expiry
- DB unique key on `(key, bucket)`

핵심은 “같은 의미의 중복이 들어올 확률이 높은 시간대”를 커버하는 것이다.

### 3. window가 너무 짧으면

- 느린 retry를 못 막는다
- duplicate가 새 window로 넘어갈 수 있다
- 운영자가 재처리했다고 오판할 수 있다

window는 너무 짧아도, 너무 길어도 문제다.

### 4. window와 영구 dedup의 조합

중요한 결제/주문은 영구 dedup, 덜 중요한 알림/캐시는 window dedup처럼 섞어 쓸 수 있다.

## 실전 시나리오

### 시나리오 1: 웹훅이 3번 연속 도착

짧은 suppression window로 한 번만 처리하고 나머지는 무시한다.

### 시나리오 2: 배치가 같은 chunk를 재실행

chunk id와 window를 같이 쓰면 중복 작업을 줄일 수 있다.

### 시나리오 3: 오래 지난 재전송은 다른 이벤트일 수 있음

window가 만료된 뒤 다시 온 이벤트는 새로운 업무 요청인지 판단해야 한다.

## 코드로 보기

```sql
CREATE TABLE dedup_window (
  dedup_key VARCHAR(100) NOT NULL,
  bucket_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (dedup_key, bucket_id)
);
```

```java
long bucketId = System.currentTimeMillis() / TimeUnit.MINUTES.toMillis(5);
boolean firstSeen = dedupRepository.insertIfAbsent(key, bucketId);
if (!firstSeen) return;
```

duplicate suppression window는 영구 기록이 아니라, **중복이 집중되는 시간대를 현실적으로 막는 장치**다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 영구 dedup | 가장 강하다 | 비용이 크다 | 핵심 거래 |
| suppression window | 비용이 낮다 | window 밖 중복은 못 막는다 | 알림/재시도 |
| bucketed dedup | 운영이 쉽다 | bucket 경계가 애매하다 | 대량 이벤트 |
| no dedup | 단순하다 | 중복에 취약하다 | 거의 없음 |

## 꼬리질문

> Q: duplicate suppression window와 idempotency key는 같은 건가요?
> 의도: 영구 멱등성과 시간 제한 중복 억제를 구분하는지 확인
> 핵심: window는 시간 제한이 있고, idempotency key는 보통 더 강한 계약이다

> Q: window가 짧으면 어떤 문제가 생기나요?
> 의도: 중복 억제의 시간 경계를 아는지 확인
> 핵심: 늦은 retry를 못 막는다

> Q: window를 어디에 두는 게 좋나요?
> 의도: storage 선택과 TTL 전략을 아는지 확인
> 핵심: Redis나 DB bucket 키처럼 빠르게 조회 가능한 곳이 좋다

## 한 줄 정리

Duplicate suppression window는 모든 중복을 영구 저장하지 않고, 중복이 몰리는 시간대만 현실적으로 억제하는 dedup 전략이다.
