---
schema_version: 3
title: URL 단축기 설계
concept_id: system-design/url-shortener-design
canonical: false
category: system-design
difficulty: intermediate
doc_role: deep_dive
level: intermediate
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- url shortener design basics
- url shortener design beginner
- url shortener design intro
- system design basics
aliases:
- url shortener design basics
- url shortener design beginner
- url shortener design intro
- system design basics
- beginner system design
- 처음 배우는데 url shortener design
- url shortener design 입문
- url shortener design 기초
- what is url shortener design
- how to url shortener design
- URL 단축기 설계
- url shortener design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/database/transaction-basics.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/database/mvcc-replication-sharding.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- URL 단축기 설계 설계 핵심을 설명해줘
- url shortener design basics가 왜 필요한지 알려줘
- URL 단축기 설계 실무 트레이드오프는 뭐야?
- url shortener design basics 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 URL 단축기 설계를 다루는 deep_dive 문서다. 긴 URL을 짧고 안전하게 저장하고, 빠르게 리다이렉트하며, 트래픽과 분석 요구를 함께 감당하는 설계다. 검색 질의가 url shortener design basics, url shortener design beginner, url shortener design intro, system design basics처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# URL 단축기 설계

> 한 줄 요약: 긴 URL을 짧고 안전하게 저장하고, 빠르게 리다이렉트하며, 트래픽과 분석 요구를 함께 감당하는 설계다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)


retrieval-anchor-keywords: url shortener design basics, url shortener design beginner, url shortener design intro, system design basics, beginner system design, 처음 배우는데 url shortener design, url shortener design 입문, url shortener design 기초, what is url shortener design, how to url shortener design
---

## 핵심 개념

URL 단축기는 단순히 `long URL -> short code` 매핑만 저장하는 시스템이 아니다. 실제 설계에서는 아래 질문에 답해야 한다.

- 사용자는 어떤 요청을 보내고, 어떤 응답을 받아야 하는가?
- 단축 코드는 어떻게 생성할 것인가?
- 중복과 충돌을 어떻게 처리할 것인가?
- 단축 URL을 열 때 얼마나 빨라야 하는가?
- 클릭 수, 지역, 기기 같은 분석 데이터를 어디까지 모을 것인가?
- 악성 링크, 스팸, 폭주 트래픽을 어떻게 막을 것인가?

설계할 때는 먼저 범위를 나누는 게 중요하다. 자세한 설계 방법은 같은 카테고리의 [README](./README.md)와, 아래의 용량 감각 정리와 함께 보면 좋다.

### 요구사항 분리

#### 기능 요구사항

- 긴 URL을 짧은 코드로 변환한다.
- 짧은 코드를 입력하면 원래 URL로 리다이렉트한다.
- 사용자는 만료 기간, 커스텀 alias, 공개 여부를 지정할 수 있다.
- 클릭 수 정도의 기본 분석은 제공한다.

#### 비기능 요구사항

- 리다이렉트는 매우 빨라야 한다.
- 쓰기보다 읽기가 훨씬 많다.
- 한 번 생성된 링크는 오랫동안 유지되어야 한다.
- 악성 링크와 중복 생성 요청을 견뎌야 한다.

### 기본 API

```http
POST /v1/urls
Content-Type: application/json

{
  "longUrl": "https://example.com/very/long/path",
  "customAlias": "spring",
  "expireAt": "2026-12-31T23:59:59Z"
}
```

응답 예시:

```json
{
  "shortUrl": "https://sho.rt/spring",
  "code": "spring",
  "longUrl": "https://example.com/very/long/path"
}
```

리다이렉트:

```http
GET /spring
```

---

## 깊이 들어가기

### 1. 단축 코드 생성 방식

대표적인 방법은 다음과 같다.

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| Auto Increment + Base62 | 구현이 단순하고 충돌이 거의 없다 | 코드가 예측 가능하다 | 내부 서비스, 빠른 MVP |
| Random String | 분산이 좋고 추측이 어렵다 | 충돌 검사가 필요하다 | 외부 공개 서비스 |
| Hash 기반 | 같은 URL이면 같은 코드가 되기 쉽다 | 해시 충돌과 길이 조정이 어렵다 | 중복 생성을 줄이고 싶을 때 |
| Snowflake류 ID + Base62 | 분산 생성에 강하다 | 시간/노드 의존성이 생긴다 | 대규모 분산 시스템 |

실무에서는 `ID 생성 -> Base62 인코딩 -> 저장` 조합이 가장 흔하다. 예측 가능성이 문제라면 앞뒤에 salt를 섞거나, 별도 토큰을 섞는다.

### 2. 충돌 처리

랜덤 코드나 해시 기반은 충돌 가능성이 있다. 처리 전략은 세 가지다.

1. 저장소에 `unique(code)` 제약을 둔다.
2. 충돌이 나면 재시도한다.
3. 커스텀 alias는 사용자 입력이므로 선점 여부를 명확히 한다.

커스텀 alias는 특히 정책이 중요하다. `spring`, `admin`, `api` 같은 값은 예약어로 막아야 한다.

### 3. 리다이렉트 경로

읽기 경로는 최대한 짧아야 한다.

1. 엣지 캐시 또는 CDN에서 먼저 조회한다.
2. 애플리케이션 캐시에서 `code -> longUrl`을 찾는다.
3. 캐시에 없으면 DB에서 조회한다.
4. 만료 여부와 접근 정책을 확인한다.
5. `301` 또는 `302`로 응답한다.

대부분의 단축 서비스는 추적과 정책 변경을 고려해 `302 Found`를 많이 쓴다. `301 Moved Permanently`는 브라우저 캐시가 강하게 남아 분석과 제어가 어려워질 수 있다.

### 4. 캐시 전략

읽기 비중이 높기 때문에 캐시는 사실상 필수다.

- `code -> longUrl`은 Redis 같은 외부 캐시에 올린다.
- 자주 조회되는 코드만 메모리 캐시로 한 번 더 둔다.
- 만료된 코드, 없는 코드는 negative cache로 짧게 저장한다.

캐시 무효화는 간단해 보이지만 까다롭다. 링크 삭제, 만료 변경, 차단 처리 같은 이벤트가 생기면 캐시를 즉시 지워야 한다.

### 5. 분석 데이터 수집

단축 URL의 진짜 가치는 클릭 분석에서 나온다.

- 총 클릭 수
- 일자별 클릭 수
- 리퍼러
- 디바이스/브라우저
- 국가/IP 대역

하지만 분석을 리다이렉트 요청과 같은 트랜잭션으로 처리하면 느려진다. 보통은 아래처럼 분리한다.

1. 리다이렉트는 바로 응답한다.
2. 클릭 이벤트는 비동기 큐로 보낸다.
3. 소비자가 집계 테이블을 갱신한다.

## 깊이 들어가기 (계속 2)

이 구조는 [outbox/inbox와 이벤트 기반 설계](../software-engineering/outbox-inbox-domain-events.md)와도 연결된다.

### 6. 남용과 보안

URL 단축기는 악성 사용을 매우 쉽게 만든다.

- 피싱 링크 위장
- 대량 생성 스팸
- 리다이렉트 오픈 리다이렉트 악용
- 봇 트래픽 폭주

완화 전략:

- 사용자/토큰/IP 단위 rate limit
- 악성 도메인 블랙리스트
- URL 정규화와 스킴 검증
- 미리보기 페이지 제공
- 관리자 차단 기능

보안과 인증은 별도 보안 카테고리로 더 깊게 확장할 수 있지만, 현재 저장소에는 해당 디렉토리가 없으므로 여기서는 설계 수준까지만 다룬다.

### 7. 저장 모델 예시

```sql
CREATE TABLE short_url (
  id BIGINT PRIMARY KEY,
  code VARCHAR(16) NOT NULL,
  long_url TEXT NOT NULL,
  user_id BIGINT NULL,
  expire_at TIMESTAMP NULL,
  is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  UNIQUE KEY uq_short_url_code (code)
);

CREATE TABLE short_url_click (
  id BIGINT PRIMARY KEY,
  short_url_id BIGINT NOT NULL,
  clicked_at TIMESTAMP NOT NULL,
  referrer VARCHAR(255),
  user_agent VARCHAR(255),
  country_code VARCHAR(8)
);
```

### 8. 병목 지점

자주 터지는 병목은 아래와 같다.

- 단일 DB에 쓰기와 읽기를 모두 몰아넣는 구조
- 클릭 집계를 동기 처리하는 구조
- random code 충돌을 재시도 없이 처리하는 구조
- 캐시 미스가 많아 DB로 쏠리는 구조
- 분석 이벤트를 같은 테이블에 계속 누적하는 구조

확장 시에는 읽기 경로를 먼저 분리하고, 이후에 분석 파이프라인과 샤딩 여부를 본다. DB 확장은 [Database 카테고리](../database/README.md)와 [MVCC / Replication / Sharding](../database/mvcc-replication-sharding.md)를 같이 보는 게 좋다.

---

## 실전 시나리오

### 시나리오 1: 트래픽이 급증한 단축 링크

대형 캠페인 링크 하나가 SNS에 퍼지면 읽기 트래픽이 갑자기 폭증한다. 이때 DB를 바로 때리면 지연이 급격히 늘어난다.

대응 순서:

1. 캐시 적중률을 높인다.
2. CDN 또는 엣지 캐시를 적용한다.
3. 읽기 전용 replica를 붙인다.
4. 필요하면 단축 코드별로 핫키를 분산한다.

### 시나리오 2: 악성 링크 대량 생성

봇이 짧은 시간에 수십만 개의 링크를 만들면 저장소와 분석 파이프라인이 같이 흔들린다.

대응 순서:

1. 생성 API에 rate limit을 건다.
2. 인증된 사용자만 생성 가능하게 한다.
3. 의심 도메인은 차단한다.
4. 생성 후 검사 작업을 비동기로 돌린다.

### 시나리오 3: 분석 집계가 느려짐

클릭마다 동기 집계를 하면 리다이렉트가 느려지고 사용자 체감이 나빠진다.

해결책은 리다이렉트와 집계를 분리하는 것이다. 즉, 사용자 응답과 데이터 수집의 SLA를 분리해야 한다.

---

## 코드로 보기

### 코드 1: Base62 인코딩

```java
public final class Base62 {
    private static final char[] ALPHABET =
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ".toCharArray();

    public static String encode(long value) {
        if (value == 0) {
            return "0";
        }

        StringBuilder builder = new StringBuilder();
        long current = value;
        while (current > 0) {
            int index = (int) (current % 62);
            builder.append(ALPHABET[index]);
            current /= 62;
        }
        return builder.reverse().toString();
    }
}
```

### 코드 2: 단축 URL 생성 서비스의 핵심 흐름

```java
@Service
public class UrlShortenService {
    private final UrlRepository urlRepository;
    private final CodeGenerator codeGenerator;

    public UrlShortenService(UrlRepository urlRepository, CodeGenerator codeGenerator) {
        this.urlRepository = urlRepository;
        this.codeGenerator = codeGenerator;
    }

    @Transactional
    public ShortUrlResponse create(String longUrl, String customAlias) {
        String code = customAlias != null ? customAlias : codeGenerator.nextCode();

        if (urlRepository.existsByCode(code)) {
            throw new IllegalStateException("이미 사용 중인 코드입니다.");
        }

        UrlEntity entity = new UrlEntity(code, longUrl);
        urlRepository.save(entity);
        return new ShortUrlResponse(code, longUrl);
    }
}
```

### 코드 3: 리다이렉트 경로의 기본 형태

## 코드로 보기 (계속 2)

```java
@RestController
public class RedirectController {
    private final UrlLookupService urlLookupService;
    private final ClickEventPublisher clickEventPublisher;

    public RedirectController(UrlLookupService urlLookupService,
                              ClickEventPublisher clickEventPublisher) {
        this.urlLookupService = urlLookupService;
        this.clickEventPublisher = clickEventPublisher;
    }

    @GetMapping("/{code}")
    public ResponseEntity<Void> redirect(@PathVariable String code) {
        String longUrl = urlLookupService.findLongUrl(code);
        clickEventPublisher.publish(code);

        return ResponseEntity.status(302)
                .location(URI.create(longUrl))
                .build();
    }
}
```

### 코드 4: 캐시 조회 우선순위

```java
public String findLongUrl(String code) {
    String cached = cache.get(code);
    if (cached != null) {
        return cached;
    }

    String fromDb = repository.findByCode(code)
            .orElseThrow(() -> new IllegalArgumentException("없는 코드입니다."));

    cache.put(code, fromDb);
    return fromDb;
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| 301 redirect | 브라우저 캐시가 강하다 | 분석과 정책 변경이 어렵다 | 거의 변경되지 않는 정적 링크 |
| 302 redirect | 제어가 쉽다 | 캐시 이점이 상대적으로 약하다 | 분석과 차단이 중요한 서비스 |
| DB 중심 | 단순하다 | 읽기 폭주에 약하다 | 초기 MVP |
| Cache + DB | 빠르고 확장성이 좋다 | 캐시 일관성 관리가 필요하다 | 대부분의 운영 환경 |
| 랜덤 코드 | 추측이 어렵다 | 충돌 검사가 필요하다 | 공개 서비스 |
| 순차 ID + Base62 | 구현이 쉽고 안정적이다 | 코드가 예측 가능하다 | 내부 시스템, 초기 버전 |

---

## 꼬리질문

> Q: 커스텀 alias가 있으면 왜 별도 정책이 필요한가?
> 의도: 예약어 충돌과 권한 문제를 구분하는지 확인한다.
> 핵심: 사용자 입력은 식별자이면서 동시에 공격면이 된다.

> Q: 클릭 분석을 왜 리다이렉트와 분리해야 하는가?
> 의도: 사용자 응답 경로와 비즈니스 집계 경로를 분리할 수 있는지 본다.
> 핵심: 느린 분석은 전체 리다이렉트를 느리게 만들 수 있다.

> Q: 301보다 302를 더 자주 쓰는 이유는 무엇인가?
> 의도: 브라우저 캐시와 운영 제어의 차이를 이해하는지 본다.
> 핵심: 단축 링크는 수정, 차단, 집계가 중요해서 제어 가능한 응답이 유리하다.

> Q: 단축 URL 서비스의 첫 번째 병목은 보통 어디에서 생기는가?
> 의도: 읽기 중심 서비스의 병목을 추론할 수 있는지 확인한다.
> 핵심: 캐시 미스가 DB로 몰리는 지점이 가장 먼저 흔들린다.

---

## 한 줄 정리

URL 단축기는 짧은 코드를 만드는 문제가 아니라, 읽기 폭주·분석·보안·캐시 일관성을 함께 다루는 작은 분산 시스템이다.
