# 세션 cache fallback

## 개념

Redis는 빠르지만 영속 저장소가 아니다.

## 사주다방 방식

1. Redis에서 먼저 조회
2. miss면 DB `auth_sessions`
3. 찾으면 Redis 복원

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/auth/application/AuthSessionQueryService.java`

## 실제 코드 스니펫

```java
Optional<StoredSession> cached = redisSessionStore.get(sessionToken);
if (cached.isPresent()) {
  return cached;
}

String tokenHash = sessionTokenHasher.hash(sessionToken);
return authSessionJdbcRepository.findValidSessionByTokenHash(tokenHash)
  .map(session -> {
    long ttlSeconds = Math.max(
      1L,
      Math.min(
        SessionKeys.SESSION_TTL_SECONDS,
        Duration.between(Instant.now(), session.expiresAt()).getSeconds()
      )
    );
    StoredSession restored = new StoredSession(session.userId(), session.userKey());
    redisSessionStore.persist(sessionToken, restored, ttlSeconds);
    return restored;
  });
```

읽는 포인트:

1. Redis가 우선
2. miss면 DB 조회
3. DB에서 찾으면 Redis 재구성

즉 “캐시가 날아가도 로그인 경험은 유지”가 목표다.

## CS 포인트

- cache-aside 비슷한 패턴
- durable store + cache 조합

## 면접 포인트

“캐시 miss가 나도 로그인이 풀리지 않도록 DB fallback을 두었다.”

## 꼬리질문

### Q. Redis만 쓰면 더 빠르지 않나요?

A. 빠르지만 안전하지 않다. Redis는 flush, 만료, 장애가 발생할 수 있다. 세션을 거기만 두면 로그인 상태가 예기치 않게 사라질 수 있다.

### Q. DB만 쓰면 안 되나요?

A. 가능은 하지만 매 요청마다 DB 조회 비용이 크다. 그래서 빠른 Redis와 durable DB를 함께 두는 게 실용적이다.

### Q. 왜 token hash를 쓰나요?

A. 세션 토큰 원문을 그대로 DB 조회 키로 남기기보다, 해시를 사용하면 유출 위험을 줄일 수 있다. 조회 가능성과 보안 사이의 절충이다.
