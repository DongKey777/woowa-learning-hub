# Logout Scope Primer

> 한 줄 요약: logout은 버튼 하나가 아니라 여러 층의 출입증을 어디까지 끊을지 정하는 범위 문제다. 초보자는 먼저 `현재 세션`, `이 기기`, `모든 기기`, `refresh token revoke`, `BFF 서버 정리`를 분리해서 보면 덜 헷갈린다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 문서 역할: `primer bridge`
>
> 이 문서는 "로그아웃했는데 왜 다른 탭은 살아 있지?", "모든 기기 로그아웃과 refresh revoke가 같은 말 아닌가?", "BFF인데 cookie만 지우면 끝 아닌가?" 같은 질문을 처음 분리하는 entrypoint다.

> 관련 문서:
> - `[primer]` [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
> - `[primer]` [Subdomain Logout Cookie Cleanup Primer](./subdomain-logout-cookie-cleanup-primer.md)
> - `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - `[follow-up]` [Session Revocation at Scale](./session-revocation-at-scale.md)
> - `[follow-up]` [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - `[follow-up]` [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)
> - `[follow-up]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - `[advanced]` [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
> - `[catalog]` [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: logout scope primer, single-device logout, logout all devices, current session logout, current device logout, session invalidation basics, refresh token revocation basics, logout scope difference, bff logout cleanup, server-side logout cleanup, cookie delete not enough, logout still works after logout, beginner logout revocation, logout current browser vs all devices, refresh revoke vs session revoke

## 먼저 잡는 mental model

로그아웃을 출입증 회수로 보면 쉽다.

- 브라우저 cookie는 브라우저가 들고 있는 출입증이다.
- 서버 session row는 서버 창구에 있는 출입 기록이다.
- refresh token은 새 access token을 다시 발급받는 장기 출입권이다.
- access token은 짧게 쓰는 현장 출입권이다.

핵심은 이것이다.

- logout은 보통 **한 층만 지우는 작업이 아니다**
- 어떤 버튼은 현재 세션만 끊고
- 어떤 버튼은 이 기기의 세션 묶음을 끊고
- 어떤 버튼은 모든 기기와 refresh 계열까지 끊는다

즉 "로그아웃"이라는 한국어 한 단어보다 **무엇을 어디까지 못 쓰게 만드는가**가 더 중요하다.

---

## 30초 구분표

| 지금 들리는 말 | 보통 먼저 의심할 범위 | 아직 자동으로 뜻하지 않는 것 |
|---|---|---|
| `이 탭만 다시 로그인하래요` | 현재 세션 종료 | 같은 기기의 다른 브라우저 프로필 종료 |
| `휴대폰만 끊고 싶어요` | single-device logout | 노트북, 태블릿까지 전부 종료 |
| `비밀번호 바꿨으니 전부 끊어야 해요` | logout all devices | 이미 발급된 짧은 access token의 즉시 소멸 |
| `refresh token을 revoke했어요` | 재발급 경로 차단 | 현재 살아 있는 access token 즉시 차단 |
| `BFF에서 logout했어요` | cookie + 서버 session/token cache 정리 | 외부 IdP 세션이나 다른 앱 세션까지 자동 종료 |

---

## 용어를 정확히 나누기

### 1. 현재 세션 logout

가장 좁은 범위다.

- 현재 브라우저 세션 하나
- 현재 앱 인스턴스 하나
- 현재 탭/프로필에서 쓰는 session cookie 하나

보통 하는 일:

- 현재 cookie 삭제
- 현재 session id 무효화

보통 아직 남는 것:

- 같은 계정의 다른 기기
- 같은 계정의 다른 브라우저 프로필
- 같은 사용자의 다른 refresh family

초보자 오해:

- "노트북에서 로그아웃했으니 같은 노트북의 크롬/사파리도 다 끊기겠지"

실제로는 제품이 session을 어떻게 묶었는지에 따라 다르다.

### 2. single-device logout

이 문서에서는 `이 기기에서 발급된 세션 묶음`을 끊는다는 뜻으로 쓴다.

예를 들면:

- 같은 휴대폰 앱의 현재/백그라운드 세션
- 같은 브라우저 프로필에서 이어진 여러 session
- 같은 device record 아래 매달린 refresh family

보통 하는 일:

- device id 또는 device session group 기준 revoke
- 이 기기에서 다시 refresh 못 하게 차단

보통 아직 남는 것:

- 다른 휴대폰
- 다른 노트북
- 계정 전체 세션

중요:

- `현재 세션`보다 넓고 `모든 기기 로그아웃`보다는 좁다.
- 같은 물리 기기라도 브라우저 프로필이 따로면 구현상 다른 device/session으로 볼 수 있다.

### 3. logout all devices

가장 넓은 사용자-facing 범위다.

보통 뜻하는 것:

- 계정에 연결된 모든 브라우저 session 종료
- 모든 앱 install 또는 device session 종료
- 모든 refresh 경로 차단

보통 같이 하는 일:

- user-wide session version 증가
- refresh token family 전체 revoke
- 세션 목록의 모든 row를 revoked 상태로 전환

하지만 아직 남을 수 있는 것:

- 짧은 TTL access token의 tail
- 분산 cache 전파 지연
- 외부 IdP 자체 로그인 세션

그래서 `모든 기기 로그아웃`은 강한 범위지만, "지금 이 순간 지구 전체에서 0초 지연으로 완전 차단"과 같은 말은 아니다.

### 4. session invalidation

이건 버튼 이름이라기보다 **서버 판단**이다.

뜻:

- 서버가 어떤 session/token을 더 이상 인정하지 않기로 결정함

방법 예시:

- session row 삭제
- `revoked=true`
- `session_version` mismatch
- server-side deny list

즉 `현재 세션 logout`, `single-device logout`, `모든 기기 로그아웃`은 모두 session invalidation을 일으킬 수 있다.
반대로 브라우저 cookie만 지우고 서버가 invalidation을 안 하면 반쪽 logout이 된다.

## 용어를 정확히 나누기 (계속 2)

### 5. refresh token revocation

이건 **재발급 경로 차단**에 가깝다.

뜻:

- refresh token 또는 refresh family를 더 이상 받아 주지 않음

효과:

- 다음 access token 재발급이 막힘
- 장기 세션 복원이 끊김

하지만 보통 즉시 해결하지 못하는 것:

- 이미 발급된 access token 한두 개
- 이미 만들어진 BFF downstream token cache

그래서 refresh revoke는 중요하지만, 단독으로 "완전 로그아웃"과 같다고 보면 안 된다.

### 6. BFF / server-side cleanup

BFF 구조에서는 브라우저보다 서버가 더 많은 출입증을 들고 있다.

서버 쪽에 남을 수 있는 것:

- session store row
- provider refresh/access token
- downstream API token cache
- handoff source session

그래서 BFF logout은 최소 두 층으로 봐야 한다.

1. 브라우저 cookie 삭제
2. 서버 session/token mapping 정리

필요하면 여기에:

3. provider refresh revoke
4. federated logout

브라우저에서 cookie만 지웠는데 서버 token cache가 살아 있으면, "브라우저는 로그아웃처럼 보이지만 서버 자산은 아직 남아 있는 상태"가 된다.

---

## 한눈에 비교

| 범위 | 주로 끊는 것 | 초보자가 자주 놓치는 것 | 대표 질문 |
|---|---|---|---|
| 현재 세션 logout | 현재 cookie, 현재 session id | 같은 기기의 다른 세션은 안 끊길 수 있음 | `왜 다른 탭은 살아 있지?` |
| single-device logout | 그 기기 아래 session/refresh 묶음 | device 정의가 UI 직감과 다를 수 있음 | `휴대폰만 끊고 싶어요` |
| logout all devices | 계정 전체 session + refresh 경로 | access token tail, 전파 지연 | `비번 바꿨는데 바로 다 끊겼나요?` |
| session invalidation | 서버의 불인정 결정 자체 | 브라우저 cleanup과 같은 말이 아님 | `cookie 지웠는데 왜 아직 되죠?` |
| refresh token revocation | 재발급 경로 | 이미 발급된 access token은 잠깐 남을 수 있음 | `revoke했는데 왜 몇 요청은 통과하죠?` |
| BFF/server cleanup | server session, token cache, handoff | cookie 삭제만으로 끝나지 않음 | `BFF인데 왜 서버도 치워야 하죠?` |

---

## 예시로 붙여 보기

### 예시 1. 웹 브라우저에서 "로그아웃"

구조:

- 브라우저는 `session` cookie를 보낸다
- BFF는 서버 session row와 provider refresh token을 들고 있다

안전한 logout:

1. 브라우저 cookie를 tombstone으로 지운다
2. 서버 session row를 invalid 처리한다
3. 필요하면 refresh token도 revoke한다

위험한 반쪽 logout:

- 1번만 하고 2, 3번을 안 함

### 예시 2. "이 휴대폰만 로그아웃"

구조:

- 같은 계정이 노트북 웹, 회사 폰 앱, 개인 폰 앱에 로그인돼 있다

의도:

- 회사 폰 앱만 끊고 싶다

보통 필요한 것:

- 회사 폰 device session group revoke
- 그 폰과 연결된 refresh family revoke

보통 필요 없는 것:

- 노트북 웹 세션 전부 종료

### 예시 3. "모든 기기에서 로그아웃"

의도:

- 계정 탈취가 의심돼 전체를 끊고 싶다

보통 필요한 것:

- user-wide session invalidation
- 모든 refresh family revoke
- 분산 캐시 전파

그래도 설명해야 하는 것:

- 이미 받은 access token은 짧은 TTL 동안 tail이 남을 수 있다

---

## 흔한 오해 5개

- `cookie를 지웠다 = 완전 로그아웃이다`는 틀릴 수 있다. 서버 session이나 refresh token이 남을 수 있다.
- `refresh token revoke = 지금 모든 API 호출이 즉시 100% 멈춘다`도 틀릴 수 있다. 이미 발급된 access token tail이 남는다.
- `모든 기기 로그아웃 = 외부 OAuth 제공자 세션도 끝났다`도 자동이 아니다. federated logout은 별도 설계다.
- `single-device logout = 물리 기기 하나만 정확히 끊는다`도 항상 아니다. 제품이 브라우저 프로필, app install, device fingerprint를 어떻게 모델링했는지 봐야 한다.
- `BFF면 브라우저에 토큰이 없으니 logout가 쉬워진다`도 절반만 맞다. 브라우저 cleanup은 쉬워질 수 있지만 서버 token cache 정리가 더 중요해진다.

---

## 다음 문서로 넘기는 기준

- "용어는 알겠는데 분산 환경에서 어떻게 전파하죠?"가 궁금하면 [Session Revocation at Scale](./session-revocation-at-scale.md)로 간다.
- "세션 목록 UI에서 현재 세션/이 기기/모든 기기를 어떻게 이름 붙이죠?"가 궁금하면 [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)로 간다.
- "refresh token family를 왜 따로 보죠?"가 궁금하면 [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)로 간다.
- "BFF에서 왜 cookie 삭제만으로 안 끝나죠?"가 궁금하면 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 간다.
- "subdomain logout migration 중 old cookie cleanup이 왜 남죠?"가 궁금하면 [Subdomain Logout Cookie Cleanup Primer](./subdomain-logout-cookie-cleanup-primer.md)로 간다.

## 한 줄 정리

logout을 이해하는 가장 쉬운 방법은 "어떤 출입증을 어느 범위까지 회수하는가"로 보는 것이다. 현재 세션, 이 기기, 모든 기기, refresh revoke, BFF 서버 정리를 같은 말로 뭉개면 설계와 디버깅이 둘 다 꼬인다.
