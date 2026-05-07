---
schema_version: 3
title: OAuth2 기초
concept_id: security/oauth2-basics
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- oauth-delegation-not-password-sharing
- oauth-vs-oidc-login-boundary
- external-token-internal-session-translation
aliases:
- oauth2 basics
- OAuth2 기초
- oauth2가 뭔가요
- oauth2 입문
- 소셜 로그인 원리
- 구글 로그인 어떻게 되나
- access token 이란
- authorization server beginner
- resource owner client authorization server resource server
- oauth2 흐름 쉽게
- 위임 인증 개념
- third party access
- oauth2 scope refresh token
symptoms:
- 구글로 로그인 버튼 뒤에서 OAuth2와 우리 서비스 세션이 어떻게 이어지는지 모르겠어
- OAuth2가 로그인인지 권한 위임인지 헷갈려
- access token, refresh token, scope, authorization server 역할이 섞여 보여
intents:
- definition
- comparison
prerequisites:
- security/authentication-authorization-session-foundations
next_docs:
- security/oauth2-oidc-social-login-primer
- security/oauth2-authorization-code-grant
- security/api-key-vs-oauth-vs-client-credentials-primer
- security/session-cookie-jwt-basics
- security/oauth-scope-vs-api-audience-vs-application-permission
linked_paths:
- contents/security/api-key-vs-oauth-vs-client-credentials-primer.md
- contents/security/oauth2-oidc-social-login-primer.md
- contents/security/oauth2-authorization-code-grant.md
- contents/security/session-cookie-jwt-basics.md
- contents/security/oauth-scope-vs-api-audience-vs-application-permission.md
- contents/spring/spring-security-basics.md
confusable_with:
- security/oauth2-oidc-social-login-primer
- security/oauth2-authorization-code-grant
- security/api-key-vs-oauth-vs-client-credentials-primer
- security/session-cookie-jwt-basics
forbidden_neighbors: []
expected_queries:
- OAuth2는 로그인 기능인지 권한 위임인지 beginner 기준으로 설명해줘
- 구글 소셜 로그인에서 외부 access token과 우리 서비스 session cookie는 어떻게 달라?
- Resource Owner, Client, Authorization Server, Resource Server 역할을 예시로 정리해줘
- scope와 access token과 refresh token은 각각 무엇을 제한하거나 이어 주는 값이야?
- API key와 OAuth와 client credentials를 언제 구분해서 써야 해?
contextual_chunk_prefix: |
  이 문서는 OAuth2를 사용자가 비밀번호를 제3자 앱에 넘기지 않고 특정 scope로 자원 접근을 위임하는 protocol로 설명하는 beginner primer다.
  구글 로그인, consent screen, access token, refresh token, scope, authorization server, resource server, external token과 internal session translation, OAuth2와 OIDC 차이를 묻는 자연어 질문이 본 문서에 매핑된다.
---
# OAuth2 기초: 내 앱이 왜 다른 서비스의 API를 쓸 수 있나

> 한 줄 요약: OAuth2는 사용자가 비밀번호를 공유하지 않고도 제3자 앱이 특정 권한으로 내 자원에 접근할 수 있도록 허가하는 표준 위임 프로토콜이다.

**난이도: 🟢 Beginner**

관련 문서:

- [API 키 vs OAuth vs Client Credentials 한 장 비교](./api-key-vs-oauth-vs-client-credentials-primer.md)
- [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
- [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [Spring Security 기초](../spring/spring-security-basics.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)

retrieval-anchor-keywords: oauth2 basics, oauth2가 뭔가요, oauth2 입문, 소셜 로그인 원리, 구글 로그인 어떻게 되나, access token 이란, authorization server beginner, resource owner, client credentials beginner, oauth2 흐름 쉽게, 위임 인증 개념, third party access, oauth basics route, auth basics route, auth beginner route

## 핵심 개념

"구글로 로그인" 버튼을 눌렀을 때 일어나는 일이 OAuth2다. 사용자가 앱에 구글 비밀번호를 알려주는 대신, 구글이 직접 "이 앱이 이 권한을 써도 되나요?"라고 사용자에게 물어보고 짧은 수명의 토큰을 발급한다.

OAuth2의 핵심 아이디어는 **비밀번호 위임 없는 권한 위임**이다. 앱은 비밀번호를 모르면서도 사용자를 대신해 특정 작업을 할 수 있다.

입문자가 헷갈리는 점: OAuth2는 "로그인"이 아니라 "권한 위임"이다. 로그인(신원 확인)은 그 위에 올라타는 OIDC(OpenID Connect)가 추가로 처리한다.
소셜 로그인 질문인데 `access token`, `id token`, 내부 session이 한 문장처럼 섞이면 [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)로 먼저 역할을 나눈 뒤 Authorization Code Grant로 내려가는 편이 빠르다.

## 2문장 결정 예시: OAuth로 가는 경우

API 키와 OAuth가 헷갈리면 "이 요청이 특정 사용자 동의와 데이터 범위를 필요로 하는가"를 먼저 본다.

| 실제 상황 | 2문장 결정 예시 |
|---|---|
| 사용자가 우리 서비스에서 자신의 구글 캘린더 일정을 읽어 오게 한다 | 이 호출은 우리 서버 자체 작업이 아니라, 특정 사용자의 캘린더를 그 사용자의 동의 범위 안에서 읽는 장면이다. 그래서 서버 고정 API 키보다 OAuth access token과 scope가 맞다. |
| 사용자가 우리 서비스에서 자신의 구글 드라이브 파일 목록을 조회한다 | 어떤 데이터를 읽을지 기준이 "우리 앱"이 아니라 "로그인한 그 사용자"이므로 사용자 위임이 필요하다. 이때는 API 키로 공용 접근을 열기보다 OAuth 동의 화면과 토큰 만료/재발급 흐름을 설계해야 한다. |

## 한눈에 보기

| 역할 | 설명 | 예시 |
|---|---|---|
| Resource Owner | 자원의 주인 (사용자) | 구글 계정 소유자 |
| Client | 자원에 접근하려는 앱 | 나의 Spring Boot 앱 |
| Authorization Server | 토큰을 발급하는 서버 | 구글 OAuth 서버 |
| Resource Server | 보호된 자원을 가진 서버 | 구글 Calendar API |

## consent screen 다음에 무슨 일이 이어지나

초보자는 여기서 가장 많이 헷갈린다. `구글 동의 화면이 끝났다`와 `우리 서비스 로그인도 끝났다`는 같은 말이 아닐 수 있다.

간단한 mental model은 이렇다.

- 외부 토큰은 `구글이 우리 앱에 준 증표`
- 내부 세션은 `우리 서비스가 브라우저에 준 로그인 상태`

| 단계 | 누가 만든 값인가 | 어디에 쓰나 |
|---|---|---|
| consent screen 완료 후 `code` 또는 `access token` | 구글 같은 외부 Authorization Server | 외부 provider와 통신하거나, 외부 로그인 결과를 확인할 때 쓴다 |
| 우리 서비스의 session cookie | 우리 서비스 | 이후 우리 서비스 요청에서 "이미 로그인한 사용자"를 복원할 때 쓴다 |

짧은 예시는 아래처럼 읽으면 된다.

1. 사용자가 `구글로 로그인`을 누른다.
2. 구글 consent screen에서 동의한다.
3. 우리 서버가 구글에서 `code`를 받아 `access token`이나 필요한 사용자 정보를 확인한다.
4. 우리 서버가 "이 외부 사용자를 우리 서비스의 어떤 회원으로 볼지" 내부 계정에 매핑한다.
5. 그다음에야 우리 서비스가 `SESSION=...` 같은 session cookie를 만들어 브라우저에 내려준다.

```text
browser -> google consent screen -> 우리 서버 callback
우리 서버 -> google token/user info 확인
우리 서버 -> internal user 조회/생성
우리 서버 -> session cookie 발급
browser -> 이후 요청부터 우리 서비스 session으로 로그인 상태 유지
```

핵심은 갈라지는 지점이 4단계다. 외부 provider가 우리 서비스의 session을 직접 만들어 주는 게 아니라, **우리 서버가 외부 결과를 받아 내부 로그인 상태로 번역**한다.

## 상세 분해

### Access Token이란

Authorization Server가 Client에게 발급하는 짧은 수명의 증표다. 이 토큰을 들고 Resource Server에 요청하면 사용자 대신 행동할 수 있다. 비밀번호와 달리 토큰은 범위(scope)와 만료 시간이 제한돼 있다.

### Scope란

토큰이 허용하는 권한의 범위다. `scope=calendar.read`면 캘린더 읽기만 할 수 있고, 이메일 삭제는 불가능하다. 사용자는 앱이 요청한 scope 목록을 보고 허가 여부를 결정한다.

### Grant Type이란

Client가 토큰을 얻는 방법이다. 가장 흔한 패턴은 다음 두 가지다.

- **Authorization Code Grant**: 브라우저 기반 앱. 사용자가 직접 Authorization Server에서 로그인하고 Code를 받아 토큰으로 교환한다. 가장 안전한 패턴.
- **Client Credentials Grant**: 서버-서버 통신. 사용자 없이 앱 자체의 자격증명으로 토큰을 얻는다.

### Refresh Token이란

Access Token이 만료됐을 때 재발급 받는 데 쓰는 수명이 긴 토큰이다. 사용자에게 다시 로그인 요청하지 않아도 된다.

## 흔한 오해와 함정

### "OAuth2를 쓰면 로그인 기능이 완성된다"

OAuth2는 권한 위임 프레임워크다. 신원 확인(로그인, "이 사람이 누구인가")은 OIDC가 담당한다. 순수 OAuth2만으로는 "이 토큰이 누구 것인가"를 신뢰할 수 없다.

### "Access Token을 localStorage에 넣으면 된다"

XSS 공격으로 JavaScript가 실행되면 localStorage의 토큰이 탈취된다. Access Token은 `HttpOnly` 쿠키 또는 메모리에만 두는 것이 더 안전하다.

### "Refresh Token은 아무 데나 저장해도 된다"

Refresh Token은 수명이 길어서 탈취되면 장기 피해가 생긴다. 서버 쪽 세션에 저장하거나, 사용 후 폐기(rotation)하는 패턴을 써야 한다.

## 실무에서 쓰는 모습

Spring Boot에서 "구글로 로그인"을 구현할 때 `spring-boot-starter-oauth2-client` 의존성을 추가하고 `application.yml`에 client-id와 client-secret을 설정한다. Spring Security가 Authorization Code Grant 흐름을 자동으로 처리하므로, 개발자가 직접 토큰 교환 코드를 짤 필요가 없다.

사용자가 "구글로 로그인" 버튼을 누르면 앱이 구글 Authorization Server로 리다이렉트하고, 구글이 인증 후 code를 앱에 돌려준다. 앱은 그 code를 access token으로 교환하고 사용자 세션을 만든다.

### 가장 흔한 오해를 한 번 더 자르면

| 헷갈리는 말 | 실제 의미 |
|---|---|
| `구글 로그인이 끝났으니 우리 서비스도 이미 로그인됐다` | 아직 아니다. 우리 서버가 외부 결과를 내부 계정과 연결하고 session을 발급해야 한다. |
| `access token이 있으니 브라우저는 그걸로 우리 서비스에 계속 요청하면 된다` | 보통 소셜 로그인 웹앱에서는 우리 서비스 session cookie를 따로 쓴다. access token은 외부 API 호출이나 외부 인증 결과 확인에 더 가깝다. |
| `consent screen`에서 받은 권한이 우리 서비스 관리자 권한까지 결정한다 | 아니다. 우리 서비스 role과 permission은 내부 정책이 정한다. |

## 더 깊이 가려면

- 보안 입문 문서 묶음으로 돌아가기: [Security README 기본 primer 묶음](./README.md#기본-primer)
- 소셜 로그인에서 OAuth2, OIDC, `access token`, `id token`, 내부 session 경계가 아직 섞이면: [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
- Authorization Code Grant 상세 흐름과 callback hardening follow-up: [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- JWT로 Access Token을 표현하는 방법: [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)

## 면접/시니어 질문 미리보기

> Q: OAuth2에서 Access Token과 Refresh Token의 차이는 무엇인가요?
> 의도: 토큰 역할 분리를 이해하는지 확인
> 핵심: Access Token은 짧은 수명으로 Resource Server 접근에 쓰고, Refresh Token은 만료된 Access Token을 재발급 받는 데 쓴다. 역할이 다르므로 보관 위치와 보안 수준도 달라야 한다.

> Q: OAuth2의 scope는 무엇이고 왜 필요한가요?
> 의도: 최소 권한 원칙과의 연결을 이해하는지 확인
> 핵심: scope는 토큰이 허용하는 권한 범위다. 앱이 필요한 것만 요청해야 토큰 탈취 시 피해 범위를 줄일 수 있다.

## 한 줄 정리

OAuth2는 비밀번호 공유 없이 제한된 권한을 위임하는 프로토콜이고, Access Token의 scope와 만료 시간이 피해 범위를 제어한다.
