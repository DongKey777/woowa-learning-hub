# XSS와 CSRF 기초

> 한 줄 요약: XSS는 "내 사이트에서 공격자 스크립트가 실행되는 문제"이고, CSRF는 "사용자의 인증 상태를 몰래 이용해 요청을 보내는 문제"다. 원인도 방어 방향도 다르다.

**난이도: 🟢 Beginner**

관련 문서:

- [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [OAuth2 기초](./oauth2-basics.md)
- [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)

retrieval-anchor-keywords: xss csrf basics, xss가 뭔가요, csrf란 무엇인가, cross-site scripting beginner, cross-site request forgery beginner, 스크립트 삽입 공격, xss csrf 차이, csrf token 왜 써요, xss 방어 방법, input sanitization, 반사형 xss, 저장형 xss, 쿠키 hijacking, samesite cookie, social login first post 403, first post 403 after login, callback 이후 csrf, post-login csrf token rotation, csrf boundary after oauth callback, oauth callback success first post forbidden, BFF login completion csrf, security symptom shortcut, category return path

## 이 문서 다음에 보면 좋은 문서

- 증상표에서 `social login callback은 성공했는데 첫 POST가 403`으로 들어왔다면, 여기서 CSRF mental model을 먼저 잡고 [OAuth2 기초](./oauth2-basics.md) -> [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)로 callback/login completion 흐름을 확인한 뒤 [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)로 내려가면 된다.
- 다른 security 증상 row를 다시 고르고 싶으면 [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)로 돌아간다.
- Spring Security 필터와 header 설정까지 이어 보려면 [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)를 보면 된다.

## 핵심 개념

### XSS (Cross-Site Scripting)

XSS는 공격자가 웹 페이지에 **악의적인 스크립트를 삽입**하고, 다른 사용자의 브라우저에서 그 스크립트가 실행되도록 하는 공격이다.

핵심 문제: 서버가 사용자 입력을 그대로 HTML에 출력하면, 입력 안에 `<script>` 태그가 있을 때 브라우저가 그것을 코드로 실행한다.

### CSRF (Cross-Site Request Forgery)

CSRF는 로그인된 사용자가 악의적인 사이트를 방문했을 때, 그 사이트가 **사용자 모르게 사용자의 인증 쿠키를 이용해 API를 호출**하는 공격이다.

핵심 문제: 브라우저는 동일 도메인 쿠키를 요청마다 자동으로 첨부한다. 공격자 사이트가 `bank.com/transfer`로 요청을 보내도 쿠키가 따라간다.

## 한눈에 보기

| 구분 | XSS | CSRF |
|---|---|---|
| 무엇이 문제인가 | 공격 스크립트가 브라우저에서 실행됨 | 인증 쿠키를 몰래 사용해 요청이 전송됨 |
| 공격자가 원하는 것 | 세션 탈취, 키로깅, 피싱 | 사용자 대신 상태 변경 (송금, 삭제 등) |
| 피해 발생 위치 | 피해자의 브라우저 | 피해자의 계정/데이터 |
| 핵심 방어 | 출력 이스케이프, CSP | CSRF 토큰, SameSite 쿠키 |

## 상세 분해

### XSS의 두 가지 주요 유형

**저장형(Stored) XSS**: 공격자가 게시판 댓글 등에 `<script>악성코드</script>`를 저장하면, 다른 사용자가 그 페이지를 볼 때 스크립트가 실행된다.

**반사형(Reflected) XSS**: URL 파라미터의 값을 페이지에 그대로 출력할 때 발생한다. 공격 링크를 클릭한 사람만 피해를 입는다.

XSS로 탈취 가능한 것: HttpOnly가 없는 쿠키, localStorage 토큰, 화면에 보이는 민감 정보

### CSRF 공격 흐름

1. 사용자가 `bank.com`에 로그인한 상태다.
2. 공격자가 만든 `evil.com` 페이지를 방문한다.
3. `evil.com` 페이지가 브라우저에서 `bank.com/transfer?to=attacker&amount=100`을 자동 요청한다.
4. 브라우저가 `bank.com` 쿠키를 자동으로 첨부해 요청이 완성된다.

## 흔한 오해와 함정

### "HTTPS를 쓰면 XSS/CSRF가 막힌다"

HTTPS는 전송 암호화다. 브라우저 내에서 스크립트가 실행되거나 쿠키가 요청에 첨부되는 것은 HTTPS와 무관하다.

### "XSS는 입력할 때 막으면 된다"

입력 검증도 필요하지만 더 중요한 것은 **출력 시 이스케이프**다. HTML을 출력할 때 `<`를 `&lt;`로 변환하면 스크립트가 실행되지 않는다. 타임리프, JSP EL 등은 기본 이스케이프를 제공한다.

### "CSRF는 JSON API에서는 안 일어난다"

`Content-Type: application/json`은 단순 요청(simple request)이 아니므로 CORS preflight를 거치지만, `Content-Type: application/x-www-form-urlencoded`로 보내는 폼 요청은 CORS를 타지 않아 여전히 위험할 수 있다.

## 실무에서 쓰는 모습

Spring Security는 기본적으로 CSRF 방어가 활성화돼 있다. `POST` 요청에 CSRF 토큰이 없으면 거부한다.

- 브라우저 세션 방식: Thymeleaf 폼에 `_csrf` hidden 필드 자동 삽입
- REST API + JWT 방식: CSRF 방어를 끄는 경우가 많지만, 쿠키로 JWT를 전달한다면 `SameSite=Strict` 또는 `SameSite=Lax`와 함께 사용하는 것이 좋다.

XSS 방어는 템플릿 엔진의 기본 이스케이프를 신뢰하되, 직접 HTML을 concat 하는 코드는 피한다.

## 더 깊이 가려면

- Spring Security CSRF 필터와 XSS 헤더 심화: [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
- 세션과 쿠키가 왜 CSRF의 표적인지: [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)

## 면접/시니어 질문 미리보기

> Q: XSS와 CSRF의 차이를 설명해 보세요.
> 의도: 두 공격의 원리를 구분하는지 확인
> 핵심: XSS는 스크립트 실행, CSRF는 인증 상태 도용 요청. 방어 방향도 다르다.

> Q: Spring Security의 CSRF 방어는 어떻게 동작하나요?
> 의도: 토큰 기반 방어 원리를 이해하는지 확인
> 핵심: 서버가 발급한 토큰을 폼 또는 헤더로 함께 보내야 한다. 공격자는 이 토큰을 미리 알 수 없다.

## 한 줄 정리

XSS는 출력 이스케이프로, CSRF는 토큰·SameSite 쿠키로 막는다. 둘은 원인이 다르므로 방어 방향도 따로 챙겨야 한다.
