---
schema_version: 3
title: Instant LocalDateTime OffsetDateTime ZonedDateTime Boundary Design
concept_id: language/java-time-instant-localdatetime-boundaries
canonical: true
category: language
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 90
mission_ids:
- missions/payment
- missions/racingcar
review_feedback_tags:
- time-boundary
- serialization
- scheduling
aliases:
- Java time boundary design
- Instant vs LocalDateTime vs OffsetDateTime vs ZonedDateTime
- LocalDateTime audit timestamp pitfall
- OffsetDateTime ZonedDateTime DST schedule
- monotonic clock timeout deadline Java
- 자바 시간 타입 선택 경계 설계
symptoms:
- createdAt 같은 절대 발생 시각을 LocalDateTime으로 저장해 timezone, DB session, multi-region ordering 문제를 만든다
- 반복 스케줄을 Instant 하나로만 저장해 사용자의 ZoneId와 DST gap/overlap 정책을 잃어버려
- timeout이나 elapsed time을 wall clock 기준으로만 계산해 NTP 보정이나 시각 변경에 흔들리는 문제를 놓쳐
intents:
- comparison
- design
- troubleshooting
prerequisites:
- operating-system/monotonic-clock-wall-clock-timeout-deadline
- language/io-nio-serialization
- system-design/distributed-scheduler-design
next_docs:
- language/record-serialization-evolution
- language/json-null-missing-unknown-field-schema-evolution
- system-design/distributed-scheduler-design
linked_paths:
- contents/language/java/io-nio-serialization.md
- contents/language/java/record-serialization-evolution.md
- contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md
- contents/operating-system/monotonic-clock-wall-clock-timeout-deadline.md
- contents/system-design/distributed-scheduler-design.md
- contents/language/java/json-null-missing-unknown-field-schema-evolution.md
confusable_with:
- operating-system/monotonic-clock-wall-clock-timeout-deadline
- system-design/distributed-scheduler-design
- language/io-nio-serialization
forbidden_neighbors: []
expected_queries:
- Instant LocalDateTime OffsetDateTime ZonedDateTime 차이를 API와 DB 경계 기준으로 비교해줘
- createdAt은 왜 LocalDateTime보다 Instant가 더 안전한 경우가 많아?
- 반복 스케줄에서 ZoneId와 ZonedDateTime이 DST 때문에 필요한 이유를 설명해줘
- API 요청 시간은 OffsetDateTime으로 받고 저장은 Instant로 바꾸는 기준을 알려줘
- timeout과 deadline 계산에는 왜 wall clock보다 monotonic clock을 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Java time API 타입을 absolute time, wall clock, offset, zone rule, monotonic elapsed time 경계로 비교하는 advanced chooser다.
  Instant vs LocalDateTime, OffsetDateTime, ZonedDateTime, DST schedule, timeout deadline 질문이 본 문서에 매핑된다.
---
# `Instant`, `LocalDateTime`, `OffsetDateTime`, `ZonedDateTime` Boundary Design

> 한 줄 요약: Java time API 타입은 "시간"을 하나로 표현하지 않는다. 절대 시각, 지역 벽시계 시간, 고정 offset, 지역 시간대 규칙을 다른 타입으로 나누며, 이 구분을 API/DB/스케줄링 경계에서 흐리면 DST, 정렬, 재처리 버그가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)
> - [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
> - [Monotonic Clock, Wall Clock, Timeout, Deadline](../../operating-system/monotonic-clock-wall-clock-timeout-deadline.md)
> - [Distributed Scheduler Design](../../system-design/distributed-scheduler-design.md)

> retrieval-anchor-keywords: Instant, LocalDateTime, OffsetDateTime, ZonedDateTime, ZoneId, ZoneOffset, UTC, DST gap, DST overlap, timestamp boundary, wall clock, absolute time, recurring schedule, API contract, database timestamp, timeout deadline

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

각 타입은 서로 다른 질문에 답한다.

- `Instant`: 세계 어디서나 같은 절대 시각인가
- `LocalDateTime`: 사용자가 본 벽시계 시간이 무엇인가
- `OffsetDateTime`: 그 시각이 어떤 UTC offset과 함께 기록됐는가
- `ZonedDateTime`: 어떤 지역 시간대 규칙까지 포함해야 하는가

즉 "언제"를 다루는 게 아니라 "어떤 의미의 시간인가"를 먼저 정해야 한다.

백엔드에서 흔한 실수는 이렇다.

- 생성 시각을 `LocalDateTime`으로 저장한다
- 반복 스케줄을 `Instant` 하나로만 저장한다
- timeout 계산을 `Instant.now()` 차이로만 잰다
- JSON/DB 경계에서 offset을 잃어버린다

## 깊이 들어가기

### 1. `Instant`는 ordering과 audit에 강하다

`Instant`는 절대 시각이다.  
로그 정렬, 이벤트 발생 시각, 만료 시각, idempotency window처럼 "전 세계에서 같은 점"을 표현할 때 가장 안전하다.

장점:

- 비교와 정렬이 명확하다
- timezone에 덜 흔들린다
- 저장과 전송 규칙을 단순화하기 쉽다

하지만 사용자에게 보여줄 wall clock 정보는 없다.

### 2. `LocalDateTime`은 벽시계이지 절대 시각이 아니다

`LocalDateTime`에는 zone도 offset도 없다.  
그래서 `2026-10-25T01:30`이 정확히 어느 순간인지는 모른다.

이 타입은 다음에 잘 맞는다.

- 사용자가 입력한 예약 시간
- 영업 시작/종료 시간
- 날짜 기반 비즈니스 규칙

즉 사람의 지역적 시간 개념에는 맞지만, audit timestamp 기본형으로 쓰기엔 위험하다.

### 3. `OffsetDateTime`은 기록 시점 offset을 보존한다

외부 API 계약에서는 `OffsetDateTime`이 유용할 수 있다.

- `"2026-04-14T10:15:30+09:00"`처럼 self-describing하다
- 송신자가 보낸 offset을 그대로 남길 수 있다
- `LocalDateTime`보다 의미가 덜 모호하다

하지만 offset만으로는 "지역 시간대 규칙"을 재현하지 못한다.  
미래 반복 스케줄에서는 `ZoneId`가 더 중요하다.

### 4. `ZonedDateTime`은 규칙까지 들고 간다

`ZonedDateTime`은 `Asia/Seoul`, `Europe/Berlin` 같은 지역 시간대를 안다.  
이 값은 DST gap/overlap을 해석할 수 있어 "매일 오전 9시" 같은 recurring schedule에 잘 맞는다.

중요한 차이:

- `OffsetDateTime`: 그 순간의 offset만 안다
- `ZonedDateTime`: 그 지역의 과거/미래 규칙을 안다

즉 미래 스케줄, 사용자 locale time preference, calendar 기능에는 `ZoneId`를 잃으면 안 된다.

### 5. timeout과 elapsed time은 wall clock과 다른 문제다

request deadline, retry backoff, circuit breaker timeout은 "얼마나 지났나"가 중요하다.  
이 문제는 `Instant.now()`보다 monotonic clock이 더 안전하다.

wall clock은 다음 때문에 흔들릴 수 있다.

- NTP 보정
- 수동 시각 변경
- leap second 처리 방식 차이

그래서 API 만료 시각 저장은 `Instant`,  
프로세스 내부 경과 시간 측정은 `System.nanoTime()` 계열이 더 적합하다.

## 실전 시나리오

### 시나리오 1: createdAt을 `LocalDateTime`으로 저장했다

서울과 도쿄에선 얼핏 괜찮아 보여도, 다중 리전에 들어가면 ordering과 해석이 흐려진다.  
DB session timezone, JVM default timezone, JSON serializer 설정에 따라 같은 값이 다르게 읽힌다.

이벤트 발생 시각이라면 `Instant`가 기본값에 가깝다.

### 시나리오 2: 매일 02:30 실행 스케줄이 DST 날 깨진다

어떤 날은 02:30이 존재하지 않고, 어떤 날은 두 번 존재한다.  
이 문제는 `LocalDateTime` 문자열 하나로는 해결되지 않는다.

필요한 것:

- `ZoneId`
- gap/overlap 정책
- UI와 운영 문서에서의 명시

### 시나리오 3: API는 offset을 보냈는데 서비스가 버린다

클라이언트가 `2026-04-14T10:15:30+09:00`를 보냈는데 서버가 `LocalDateTime`으로 받으면,  
보낸 의미 중 절반이 사라진다.

그 뒤 다시 UTC로 바꿀 때 서버 default timezone이 끼어들면 버그가 생긴다.

### 시나리오 4: timeout 계산이 시계 보정에 흔들린다

`Instant.now()` 두 번 찍어 차이를 구하면 대부분은 동작한다.  
하지만 clock step이 있는 환경에선 SLA 경계에서 흔들릴 수 있다.

운영성 높은 timeout 로직은 monotonic clock을 같이 생각해야 한다.

## 코드로 보기

### 1. 절대 시각 저장

```java
import java.time.Instant;

public record AuditEvent(String type, Instant occurredAt) {}
```

### 2. 사용자 입력 시간과 지역 규칙 보존

```java
import java.time.LocalDateTime;
import java.time.ZoneId;

public record ScheduledRun(LocalDateTime localTime, ZoneId zoneId) {}
```

### 3. API 경계에서 offset 유지

```java
import java.time.OffsetDateTime;

public record ApiRequest(OffsetDateTime requestedAt) {}
```

### 4. 경과 시간 측정은 monotonic 기준

```java
long start = System.nanoTime();
doWork();
long elapsedNanos = System.nanoTime() - start;
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `Instant` | 정렬과 저장이 단순하다 | 사용자 wall clock 의미는 잃는다 |
| `LocalDateTime` | 입력 폼과 비즈니스 규칙 표현이 자연스럽다 | 절대 시각으로는 모호하다 |
| `OffsetDateTime` | API 경계에서 의미를 많이 보존한다 | 지역 시간대 규칙은 담지 못한다 |
| `ZonedDateTime` | recurring schedule과 DST 해석에 강하다 | 저장/비교 모델이 더 복잡하다 |

핵심은 "시간 타입 선택"이 아니라 "경계에서 어떤 시간 의미를 보존할 것인가"다.

## 꼬리질문

> Q: 이벤트 발생 시각은 보통 어떤 타입이 좋나요?
> 핵심: 절대 ordering과 audit이 중요하면 `Instant`가 기본값에 가깝다.

> Q: `LocalDateTime`은 언제 쓰나요?
> 핵심: 사용자 입력 wall clock이나 날짜 규칙처럼 zone 없는 지역 시간 개념이 중요할 때다.

> Q: `OffsetDateTime`과 `ZonedDateTime` 차이는 무엇인가요?
> 핵심: 전자는 offset만, 후자는 지역 시간대 규칙까지 가진다.

> Q: timeout 계산도 `Instant`로 하면 안 되나요?
> 핵심: 가능은 하지만 경과 시간 측정에는 monotonic clock이 더 안정적이다.

## 한 줄 정리

Java time API는 시간의 의미를 분리해 놓았으므로, absolute time, wall clock, offset, zone rule을 섞지 않는 것이 API와 스케줄링 설계의 핵심이다.
