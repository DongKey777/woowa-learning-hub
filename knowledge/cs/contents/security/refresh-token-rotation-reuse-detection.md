# Refresh Token Rotation / Reuse Detection

> 한 줄 요약: refresh token은 긴 수명의 bearer credential이므로, 회전만이 아니라 재사용 탐지와 가족 단위 폐기까지 같이 설계해야 안전하게 운영할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)

retrieval-anchor-keywords: refresh token, rotation, reuse detection, token family, jti, revocation, sliding session, replay, bearer credential, refresh compromise

---

## 핵심 개념

access token과 refresh token은 역할이 다르다.

- `access token`: 짧게 살아서 API 호출에 쓰는 토큰
- `refresh token`: 길게 살아서 새 access token을 발급받는 토큰
- `rotation`: refresh token을 사용할 때마다 새 토큰으로 교체하는 것
- `reuse detection`: 이미 교체된 옛 토큰이 다시 쓰이면 탈취로 보고 가족 전체를 폐기하는 것

핵심은 refresh token이 단순한 "재발급 키"가 아니라는 점이다.  
실무에서는 사실상 장기 세션을 대표하는 bearer credential에 가깝다. 그래서 유출되면 만료 전까지 악용될 수 있고, 로그아웃이나 권한 회수 이후에도 살아남기 쉽다.

rotation은 이 문제를 줄이지만, rotation만으로는 부족하다.

- 회전 직전의 토큰이 재사용되면 어떻게 할지 정해야 한다
- 동시 refresh 요청이 두 번 들어오면 어떤 요청을 살릴지 정해야 한다
- 가족 전체를 revoke 할지, 단일 토큰만 끊을지 정해야 한다

즉 refresh token 설계는 발급 문제가 아니라 세션 상태 관리 문제다.

---

## 깊이 들어가기

### 1. 왜 rotation이 필요한가

refresh token은 보통 access token보다 더 중요하다.

- access token은 짧게 끊을 수 있다
- refresh token은 길게 유지되므로 탈취 피해가 더 크다
- 브라우저 cookie, 디바이스 저장소, 모바일 Keychain 등 여러 위치에 남는다

rotation을 쓰면 다음 이점을 얻는다.

- 토큰이 한 번 노출돼도 오래 재사용되기 어렵다
- 세션이 살아 있는 동안에도 탈취 징후를 더 빨리 잡을 수 있다
- 발급 이력을 추적하기 쉽다

하지만 rotation은 "매번 새 값을 주는 것" 이상의 의미를 가져야 한다.

### 2. token family 모델

가장 흔한 구현은 token family 모델이다.

- 하나의 로그인 세션마다 `family_id`를 둔다
- 각 refresh token은 `token_id`와 `parent_id`를 가진다
- 사용된 토큰은 `used` 또는 `rotated` 상태로 바뀐다
- 새 토큰은 같은 family 안의 자식으로 발급된다

이 구조의 장점은 재사용을 단순한 실패가 아니라 사고 신호로 볼 수 있다는 점이다.

예를 들어:

1. 사용자가 `RT1`로 refresh 한다
2. 서버는 `RT1`을 `rotated`로 바꾸고 `RT2`를 발급한다
3. 이후 `RT1`이 다시 오면 replay로 판단한다
4. 같은 family의 모든 토큰을 revoke 한다

이때 옛 토큰의 재등장은 "사용자 실수"보다 "탈취"에 더 가깝다.

### 3. 동시 refresh가 제일 까다롭다

모바일 앱이나 탭이 여러 개인 브라우저에서는 같은 refresh token이 동시에 두 번 올 수 있다.

- 요청 A와 요청 B가 거의 동시에 도착한다
- 둘 다 같은 토큰이 아직 유효하다고 본다
- 둘 다 새 토큰을 만들면 family가 분기된다

그래서 refresh는 원자적으로 처리해야 한다.

- token row를 잠근다
- 한 번만 `consume` 된다
- 새 토큰 발급은 트랜잭션 안에서 수행한다
- 중복 요청은 stale token reuse로 판정할 수 있게 만든다

실무에서는 "중복 1회 허용 grace window"를 두는 경우도 있지만, 그만큼 replay 탐지가 늦어진다.

### 4. 저장은 raw token이 아니라 hash로 한다

refresh token은 원문 그대로 저장하지 않는 편이 안전하다.

- DB 유출 시 즉시 재사용되는 것을 막는다
- 로그나 덤프에서 노출되는 위험을 줄인다
- 검색은 token hash로 한다

보통 저장하는 필드는 이런 식이다.

- `family_id`
- `token_id`
- `parent_id`
- `token_hash`
- `status`
- `issued_at`
- `used_at`
- `expires_at`
- `revoked_at`

### 5. reuse detection의 의미

reuse detection은 단순한 "다시 쓰면 실패"가 아니다.

- 이미 교체된 옛 토큰이 다시 등장하면 인증이 깨졌다고 본다
- 세션 하나가 아니라 같은 family 전체를 끊는 경우가 많다
- 필요하면 해당 계정의 모든 refresh session을 revoke 한다

이 판단은 엄격해야 한다.  
옛 refresh token의 재등장은 정상 사용자 흐름보다 공격 시그널인 경우가 훨씬 많기 때문이다.

---

## 실전 시나리오

### 시나리오 1: 탈취된 예전 refresh token이 다시 들어옴

상황:

- 사용자는 정상적으로 `RT1 -> RT2 -> RT3`로 갱신했다
- 공격자는 예전에 훔친 `RT1`을 가지고 있다
- 공격자가 `RT1`을 재사용한다

문제:

- rotation만 있으면 `RT1`이 이미 무효인지, 탈취인지 구분이 애매하다

대응:

- `RT1`의 reuse를 사고로 본다
- 같은 family의 `RT2`, `RT3`도 모두 revoke 한다
- 필요하면 사용자에게 재로그인을 요구한다

### 시나리오 2: 모바일 앱이 네트워크 재시도로 refresh를 두 번 보냄

상황:

- 첫 번째 refresh는 성공했는데 응답이 유실됐다
- 클라이언트가 같은 토큰으로 재시도한다

문제:

- 서버는 이미 사용된 token을 reuse로 볼 수 있다

대응:

- refresh endpoint를 원자적으로 설계한다
- 짧은 grace window를 둘지 결정한다
- 클라이언트에는 "최신 토큰만 보관"하는 규칙을 강제한다

### 시나리오 3: 로그아웃했는데 다른 디바이스에서 세션이 계속 살아 있음

상황:

- 웹에서 로그아웃했지만 모바일 앱은 여전히 refresh를 시도한다

문제:

- access token만 지우고 refresh session을 남겼다

대응:

- logout 시 refresh family를 revoke 한다
- 디바이스별 session 목록을 제공한다
- 계정 설정에서 "모든 기기에서 로그아웃"을 지원한다

---

## 코드로 보기

### 1. rotate and reuse detection 개념

```java
public TokenPair refresh(String presentedToken) {
    String tokenHash = hash(presentedToken);

    RefreshToken current = refreshTokenRepository.findActiveByHash(tokenHash)
        .orElseThrow(() -> new InvalidTokenException("refresh token not found"));

    if (current.isUsed()) {
        refreshTokenRepository.revokeFamily(current.familyId());
        throw new ReuseDetectedException("refresh token reused");
    }

    current.markUsed();
    RefreshToken next = RefreshToken.createChild(current);

    refreshTokenRepository.save(current);
    refreshTokenRepository.save(next);

    return new TokenPair(
        jwtIssuer.issueAccessToken(current.userId()),
        next.rawValue()
    );
}
```

### 2. family revoke 예시

```java
public void revokeFamily(String familyId) {
    List<RefreshToken> tokens = refreshTokenRepository.findByFamilyId(familyId);
    for (RefreshToken token : tokens) {
        token.revoke();
    }
    refreshTokenRepository.saveAll(tokens);
}
```

### 3. 클라이언트 저장 규칙

```text
1. refresh 응답을 받으면 이전 refresh token을 즉시 폐기한다
2. 저장소에는 최신 값만 둔다
3. 동시 refresh를 줄이기 위해 한 번에 하나의 refresh 요청만 보낸다
4. 인증 실패가 반복되면 재로그인을 유도한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 매 요청 rotation | 재사용 탐지가 강하다 | 구현과 동시성 처리가 어렵다 | 민감한 서비스, 장기 세션 |
| 고정 refresh token | 구현이 쉽다 | 탈취 후 장기 악용이 쉽다 | 거의 권장되지 않음 |
| rotation + grace window | 네트워크 재시도에 관대하다 | replay 탐지가 늦어진다 | 모바일, 불안정한 네트워크 |
| family-wide revoke | 침해 대응이 강하다 | 정상 세션도 같이 끊길 수 있다 | 높은 보안 요구사항 |

판단 기준은 단순하다.

- refresh token이 탈취되면 어떤 피해가 나는가
- 재로그인 UX를 얼마나 허용할 수 있는가
- 디바이스별 세션 관리가 필요한가
- 동시 refresh와 재시도 오류를 얼마나 자주 겪는가

---

## 꼬리질문

> Q: refresh token을 왜 access token보다 더 엄격하게 다뤄야 하나요?
> 의도: 장기 bearer credential의 위험을 이해하는지 확인
> 핵심: refresh token은 세션 연장 키라서 탈취 피해가 더 길다.

> Q: rotation만으로 replay attack이 완전히 막히나요?
> 의도: 회전과 재사용 탐지를 분리해서 이해하는지 확인
> 핵심: 아니요. 예전 토큰 재사용은 별도 탐지가 필요하다.

> Q: 왜 raw token을 DB에 저장하지 않나요?
> 의도: 저장소 유출 리스크를 이해하는지 확인
> 핵심: hash로 저장해야 유출 시 즉시 재사용되는 것을 줄일 수 있다.

> Q: 동시 refresh 요청은 어떻게 처리해야 하나요?
> 의도: 원자성과 race condition 대응을 아는지 확인
> 핵심: 하나만 consume 되도록 트랜잭션과 잠금을 사용해야 한다.

## 한 줄 정리

refresh token은 "길게 살아도 되는 토큰"이 아니라 "재사용되면 즉시 사고로 봐야 하는 세션 연장 키"다.
