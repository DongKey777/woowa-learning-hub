# OIDC, ID Token, UserInfo

> 한 줄 요약: OIDC는 OAuth2 위에 "누구인지"를 표준화한 계층이다. ID Token과 UserInfo는 같은 사용자 정보를 다루지만 신뢰 경계가 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)

retrieval-anchor-keywords: OIDC, OpenID Connect, ID token, UserInfo endpoint, id token vs access token, id token vs userinfo, nonce validation, claim normalization, external identity mapping, issuer audience nonce, authentication vs authorization boundary, external IdP trust boundary

---

## 핵심 개념

OIDC(OpenID Connect)는 OAuth2 위에서 동작하는 인증 계층이다.

- OAuth2: 리소스 접근 위임
- OIDC: 사용자가 누구인지 인증

OIDC에서 자주 보는 세 가지는 다음과 같다.

- `ID Token`: 인증 결과를 담은 토큰
- `Access Token`: API 호출 권한을 담은 토큰
- `UserInfo Endpoint`: 추가 사용자 정보를 얻는 표준 엔드포인트

이 셋을 섞으면 흔히 이런 오해가 생긴다.

- Access token만 있으면 로그인 정보도 다 안다고 착각
- ID token만 믿고 내부 권한까지 부여
- UserInfo 응답을 무조건 진실로 받아들임

---

## 깊이 들어가기

### 1. ID Token은 인증용이다

ID token은 "이 사용자가 인증되었다"는 사실을 전한다.

보통 확인할 것:

- `iss`: 발급자
- `aud`: 이 토큰이 우리 앱용인지
- `sub`: 사용자 고유 식별자
- `exp`: 만료
- `nonce`: 재사용 방지

중요한 점은 ID token의 payload가 서명되었다고 해서, 그 값이 내부 권한 모델과 자동 일치하는 것은 아니라는 점이다.

### 2. Access Token은 API 호출용이다

Access token은 resource server가 API 호출 허용 여부를 판단할 때 쓴다.

- scope가 들어간다
- 만료가 짧다
- 우리 서비스의 내부 사용자 권한과는 별개일 수 있다

### 3. UserInfo는 추가 조회용이다

UserInfo endpoint는 인증 서버에서 사용자 프로필을 추가로 가져오는 표준 방식이다.

사용 시점:

- ID token만으로 부족한 프로필이 필요할 때
- provider별 claim 차이를 표준화하고 싶을 때
- email, name, picture 같은 부가 정보가 필요할 때

주의할 점:

- UserInfo도 "외부 IdP가 준 정보"다
- 내부 role/permission의 원천은 아니다
- 필요한 claim만 최소로 쓴다

### 4. trust boundary를 잘못 잡으면 사고가 난다

실수 패턴:

- `email_verified=true`만 보고 관리자 계정 생성
- `id_token`에 있는 `email`을 내부 키로 고정
- OIDC provider가 바뀌면 사용자 매핑이 깨짐

올바른 경계:

- 외부 IdP는 신원 확인
- 내부 서비스는 계정 매핑과 권한 부여
- 내부 role은 별도 DB/정책으로 관리

---

## 실전 시나리오

### 시나리오 1: ID token만 보고 내부 권한을 부여함

원인:

- 인증 성공과 내부 authorization을 동일시함

해결:

- OIDC principal은 외부 식별자까지만 신뢰
- 내부 `UserAccount`와 매핑 후 권한 부여

### 시나리오 2: UserInfo를 믿었는데 claim이 변함

원인:

- provider별 claim schema를 고정한다고 가정함

해결:

- claim normalization 계층을 둔다
- provider별 어댑터를 만든다

### 시나리오 3: nonce 검증을 빼먹음

원인:

- 인증 응답 재사용 공격을 막지 못함

해결:

- 로그인 시 nonce 생성
- callback 시 nonce 대조

### 시나리오 4: OIDC 로그인 후 내부 JWT 발급이 꼬임

원인:

- 외부 토큰과 내부 토큰의 목적이 섞임

해결:

- OIDC는 외부 인증
- 우리 서비스는 내부 세션/JWT 발급

---

## 코드로 보기

### OIDC principal 매핑 예시

```java
public class OidcAccountMapper {
    public UserAccount map(OidcUser oidcUser) {
        String provider = oidcUser.getIssuer().toString();
        String subject = oidcUser.getSubject();
        String email = oidcUser.getEmail();

        return userAccountRepository.findOrCreate(provider, subject, email);
    }
}
```

### ID token 검증 관점

```java
public void validateOidcToken(OidcIdToken idToken, String expectedIssuer, String expectedAudience) {
    if (!expectedIssuer.equals(idToken.getIssuer().toString())) {
        throw new IllegalArgumentException("bad issuer");
    }
    if (!idToken.getAudience().contains(expectedAudience)) {
        throw new IllegalArgumentException("bad audience");
    }
    if (idToken.getExpiresAt().before(new Date())) {
        throw new IllegalArgumentException("expired");
    }
}
```

### 내부 토큰 발급 경계

```java
public InternalSession issueInternalSession(OidcUser oidcUser) {
    UserAccount account = oidcAccountMapper.map(oidcUser);
    return internalSessionService.issue(account.getId(), account.getRoles());
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| ID Token만 사용 | 단순하다 | claim 변화와 내부 권한 분리가 약하다 | 아주 단순한 앱 |
| ID Token + UserInfo | 표준적이고 프로필 확장이 쉽다 | 네트워크 호출이 추가된다 | 일반적인 OIDC 로그인 |
| ID Token + 내부 세션/JWT | 내부 권한을 명확히 분리한다 | 구현이 한 단계 더 필요하다 | 대부분의 서비스 |

핵심 판단 기준은 **외부 인증과 내부 권한을 분리할 것인가**다.

---

## 꼬리질문

> Q: ID token과 access token의 차이를 한 문장으로 설명할 수 있나요?
> 의도: OIDC와 OAuth2의 역할 분리를 아는지 본다.
> 핵심: ID token은 인증 결과, access token은 API 접근 권한이다.

> Q: UserInfo를 매번 호출하면 왜 비효율적인가요?
> 의도: 네트워크 비용과 claim 정규화 비용을 이해하는지 본다.
> 핵심: 캐시 가능하지만, 외부 IdP 의존성과 지연이 늘어난다.

> Q: 내부 관리자 권한을 OIDC claim에 넣으면 왜 위험한가요?
> 의도: 외부 신원과 내부 권한을 분리하는 감각을 본다.
> 핵심: provider 변경, claim 누락, 과신 문제가 생긴다.

## 한 줄 정리

OIDC는 "누구인지"를 다루고, ID token은 인증 결과, UserInfo는 추가 프로필 조회, 내부 권한은 우리 서비스가 따로 관리해야 한다.
