---
schema_version: 3
title: '역할 변경 직후 403 — token TTL / cache / role mapping 어디에 원인이 있나'
concept_id: security/forbidden-after-role-change-symptom-router
canonical: false
category: security
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- stale-authority-after-role-change
- role-prefix-mapping
- securitycontext-cache-invalidation
aliases:
- 역할 변경 후 403
- role change 403
- 권한 부여 후에도 권한 없음
- JWT 권한 안 바뀜
- 새 역할 반영 안 됨
intents:
- symptom
- troubleshooting
symptoms:
- '관리자 권한 부여 직후에도 사용자가 403 Forbidden을 받는다'
- '역할 변경했는데 로그아웃 후 다시 로그인해야 반영된다'
- '백엔드 DB의 user_roles는 바뀌었는데 API 호출 시 권한이 그대로다'
prerequisites:
- security/auth-failure-response-401-403-404
- security/role-change-session-freshness-basics
next_docs:
- security/claim-freshness-after-permission-changes
- security/grant-path-freshness-stale-deny-basics
- security/authz-session-versioning-patterns
linked_paths:
- contents/security/auth-failure-response-401-403-404.md
- contents/security/role-change-session-freshness-basics.md
- contents/security/claim-freshness-after-permission-changes.md
- contents/security/grant-path-freshness-stale-deny-basics.md
- contents/security/authz-session-versioning-patterns.md
- contents/security/authorization-caching-staleness.md
- contents/spring/spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md
confusable_with:
- security/auth-failure-response-401-403-404
- spring/admin-login-success-final-403-savedrequest-role-mapping-primer
forbidden_neighbors:
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/security/session-cookie-jwt-basics.md
expected_queries:
- 권한 변경 직후에 403이 뜨는 이유가 뭐야?
- JWT를 바꾸지 않고도 새 역할이 반영되게 하려면?
- DB는 admin인데 API는 USER로 보는 이유는?
- 로그인은 유지되는데 역할만 바뀐 뒤 왜 forbidden이 남아?
- role grant 이후에도 재로그인 전까지 403이면 어디부터 봐?
contextual_chunk_prefix: |
  이 문서는 role grant나 role change 뒤에도 403이 남을 때 원인을 token
  claim, SecurityContext/권한 캐시, DB role mapping 세 갈래로 자르는
  symptom_router다. DB는 admin인데 API는 USER로 보임, 재로그인 전까지만
  403, 역할 변경 후 forbidden이 계속됨 같은 learner phrasing을 원인별 다음
  문서로 연결한다.
---

# 역할 변경 직후 403 — token TTL / cache / role mapping 어디에 원인이 있나

> 한 줄 요약: "DB에 admin이라고 적혀있는데 API는 403"이라는 증상은 *세 곳* 중 하나에서 *오래된 권한 정보*가 남은 것이다 — (1) JWT/세션 토큰 안에 박힌 role claim, (2) 권한 캐시 (Spring Security context, Redis), (3) DB 조회 매핑 자체가 잘못됨. 분기 진단으로 좁힌다.

**난이도: 🟡 Intermediate**

**증상 분기**: authn/authz (인증/인가 시스템)

관련 문서:

- [Auth Failure Response 401 vs 403 vs 404](./auth-failure-response-401-403-404.md) — 일반 분류
- [Admin Login 성공 후 최종 403 (savedRequest, role mapping)](../spring/spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md) — 비슷한 디버깅

## 어떤 증상에서 이 문서를 펴는가

학습자가 다음 중 하나를 보고한다:

- *"관리자 페이지에 들어갔더니 403. DB에는 ROLE_ADMIN이라고 돼있어요."*
- *"권한 부여 후 사용자가 *재로그인하면* 정상 작동, 안 하면 403."*
- *"`@PreAuthorize("hasRole('ADMIN')")`이 막는데, JPA로 조회해보면 역할이 ADMIN."*

증상은 동일 — *DB의 truth*와 *런타임이 보는 view*가 어긋난다. 원인은 *세 층* 중 하나다.

## 원인 분기

### 분기 1 — 토큰 안에 박힌 role claim (가장 흔함)

JWT 또는 세션 토큰을 *처음 발급할 때* role을 claim에 박는 패턴:

```json
{
  "sub": "user-123",
  "roles": ["USER"],          // 이 시점 역할
  "exp": 1735689600
}
```

이후 DB의 role이 ADMIN으로 바뀌어도 *토큰 안의 claim은 그대로*. 토큰이 만료되거나 *재발급*되어야 새 role이 들어간다.

**진단법**:

- 클라이언트가 들고 있는 JWT를 디코딩 (jwt.io)
- `roles` claim이 *DB와 다른가* 확인

**해결**:

- 단기 수정 — 사용자 *재로그인 안내* (UX는 거칠지만 작동)
- 장기 수정 — *토큰 TTL을 짧게 (예: 5~15분)* + refresh 토큰 사용
- 또는 *토큰에 role을 박지 않고* 매 요청마다 DB/캐시 조회

### 분기 2 — Spring Security context / 권한 캐시

세션 기반이라면 Spring이 *로그인 시점*에 `UserDetails`를 만들고 그 안에 `authorities`를 박는다. 이후 같은 세션에서 권한이 바뀌어도 *세션 안의 authorities가 갱신되지 않는다*.

```java
@AuthenticationPrincipal UserDetails user
// user.getAuthorities() → 로그인 시점 권한 (구버전)
```

또는 Redis/Caffeine 같은 *권한 캐시*가 있고 invalidation이 빠진 경우.

**진단법**:

- 사용자가 *로그아웃 후 재로그인*하면 정상인지 확인. *그렇다면* 이 분기.
- Redis에 `permissions:user:123` 같은 키가 있는지 + TTL 확인

**해결**:

- 권한 변경 시 *해당 사용자의 SecurityContext 무효화* (`SessionRegistry.expireNow()`)
- Redis 캐시면 *publish/subscribe로 즉시 invalidation*
- 또는 *짧은 TTL*로 자동 갱신

### 분기 3 — DB 조회 매핑 (가장 드물지만 가장 헷갈림)

```java
@Query("SELECT r FROM Role r WHERE r.id = :userId")  // ❌ 잘못된 SQL
List<Role> findRolesByUserId(Long userId);
```

또는 *복수 역할* 사용자가 있는데 `findFirst()`만 호출하는 경우:

```java
Role role = userRoleRepository.findByUserId(userId).orElseThrow();  // ❌ 첫 번째만
// 사용자가 [USER, ADMIN]을 가지면 USER만 나올 수 있음
```

**진단법**:

- DB에 *직접 쿼리* (`SELECT * FROM user_roles WHERE user_id = ?`)
- *Spring Security가 받아간 GrantedAuthority 목록*을 로깅
- 둘이 다르면 이 분기

**해결**:

- N:M 관계는 *Set/List로 받기* + 중복 제거
- `findAllByUserId` 같은 *복수형 메소드* 사용
- Lazy loading이라면 fetch join 또는 `@Transactional`로 세션 유지

## 분기 체크리스트

- [ ] 클라이언트가 들고 있는 JWT를 디코딩해 *role claim*을 확인했는가?
- [ ] 사용자 *재로그인 시 정상*이면 분기 2 (세션/캐시).
- [ ] *재로그인해도 여전히 403*이면 분기 3 (DB 매핑) 또는 토큰 발급 시점 매핑 자체가 틀린 경우.
- [ ] DB에 직접 쿼리한 *권한 목록*과 Spring Security가 보는 *GrantedAuthority*가 일치하는가?
- [ ] 권한 캐시 (Redis, Caffeine)가 있으면 *invalidation 트리거*가 권한 변경 시 발화되는가?

## 흔한 함정

### 함정 — `ROLE_` 접두사 누락

```java
@PreAuthorize("hasRole('ADMIN')")          // hasRole은 자동으로 ROLE_ADMIN 비교
SimpleGrantedAuthority("ADMIN")            // ❌ ROLE_ 접두사 없음
SimpleGrantedAuthority("ROLE_ADMIN")       // OK
```

`hasRole('ADMIN')`은 *내부적으로 `ROLE_ADMIN`*을 찾는다. authorities에 `ROLE_` 없이 넣으면 매핑 실패. 자주 보이는 *DB는 ADMIN, Spring은 USER*의 원인 중 하나.

### 함정 — Refresh 토큰의 role을 갱신 안 함

refresh 토큰으로 access 토큰을 재발급할 때 *원래 토큰의 claim을 그대로 복사*하면 *DB 갱신을 반영 못 한다*. refresh 시점에 *DB 재조회*가 필수.

## 다음 문서

- 401 vs 403 vs 404의 의미: [Auth Failure Response 401 vs 403 vs 404](./auth-failure-response-401-403-404.md)
- 비슷한 디버깅 패턴: [Admin Login 성공 후 최종 403 Primer](../spring/spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)
- 인증 vs 권한 모델: [Permission Model Bridge](./permission-model-bridge-authn-to-role-scope-ownership.md)
