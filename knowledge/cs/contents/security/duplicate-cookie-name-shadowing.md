# Duplicate Cookie Name Shadowing

> 한 줄 요약: cookie 이름이 같아도 `Domain`이나 `Path`가 다르면 브라우저는 둘 다 저장할 수 있다. 그러면 어떤 요청에는 stale session cookie가 앞에 오거나 둘 다 실려서, 서버가 엉뚱한 session을 복원하고 login loop가 생길 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
> - [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: duplicate cookie name shadowing, duplicate session cookie, cookie name collision, same cookie name different path, same cookie name different domain, duplicate JSESSIONID, duplicate SESSION cookie, cookie header duplicate name, browser sends two cookies same name, stale cookie shadows new cookie, cookie path shadowing, cookie domain shadowing, wrong session cookie sent, wrong session cookie selected, login loop duplicate cookie, re-login loop duplicate cookie, cookie overwrite myth, last Set-Cookie does not always win, delete cookie exact path domain, auth cookie shadowing, callback login loop duplicate cookie, session cookie duplicate domain path, cookie scope collision, duplicate auth cookie beginner

## 이 문서를 먼저 읽는 이유

초보자는 보통 이렇게 생각한다.

- `session`이라는 이름의 cookie는 하나만 있다
- 새 login이 성공하면 옛 cookie는 자동으로 덮어써진다
- 그러니 login loop는 서버 세션 저장소 문제겠지

하지만 브라우저는 cookie를 이름만으로 구분하지 않는다.

- 실제 식별자는 보통 `(이름, Domain, Path)` 조합이다
- 그래서 이름이 같아도 scope가 다르면 여러 개가 같이 남을 수 있다
- 요청마다 브라우저가 붙이는 cookie 집합도 달라진다

즉 이 문서의 핵심은 한 줄이다.

- `cookie name`이 같다고 `같은 cookie`는 아니다

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 보통 뜻하는 것 | 먼저 볼 것 |
|---|---|---|
| 방금 다시 로그인했는데 특정 route에서만 또 `/login` | 더 좁은 `Path`의 old cookie가 남았을 수 있다 | 실패한 요청의 raw `Cookie` header |
| `Application > Cookies`에 `session`이 두 줄 이상 보인다 | 같은 이름 cookie가 서로 다른 scope로 공존한다 | `Domain`, `Path` column |
| request header에 `session=...; session=...`처럼 같은 이름이 두 번 나온다 | duplicate cookie shadowing이 이미 발생 중이다 | 서버/framework가 어느 값을 쓰는지 |
| `logout`이나 cookie 삭제를 했는데도 loop가 계속 난다 | old cookie를 다른 `Path`/`Domain`에 남겨 뒀을 수 있다 | 삭제 응답의 `Set-Cookie` scope |
| `/dashboard`는 되는데 `/app/me`나 `/auth/callback`만 깨진다 | route별로 matching되는 cookie 세트가 다르다 | 요청 path/host마다 어떤 cookie가 붙는지 |

---

## 가장 중요한 mental model

cookie를 "이름표"가 붙은 출입증으로 생각하면 쉽다.

- 이름표는 둘 다 `session`일 수 있다
- 하지만 출입 가능한 건물(`Domain`)과 층(`Path`)이 다를 수 있다
- 브라우저는 요청 주소를 보고 "이번 문에는 어느 출입증을 보여 줄까?"를 결정한다

앱 관점에서 중요한 점은 이것이다.

- 브라우저는 "이게 네가 의도한 대표 session인지"는 모른다
- 그냥 scope 규칙에 맞는 cookie를 보낸다
- 그러다 보니 앱은 stale cookie를 먼저 읽거나, 같은 이름 cookie 두 개를 같이 받게 된다

| 속성 | 브라우저가 판단하는 질문 | 틀리면 보이는 증상 |
|---|---|---|
| `Name` | 어떤 종류의 cookie인가? | 이름만 같다고 하나라고 착각하기 쉽다 |
| `Domain` | 이 host에도 보내도 되나? | `auth`에서는 깨지고 `app`에서는 되는 식의 혼란 |
| `Path` | 이 URL path에도 보내도 되나? | 특정 route에서만 login loop |

핵심은 `Name`만 보면 안 되고, 항상 `Domain`과 `Path`를 같이 봐야 한다는 점이다.

---

## 한 장면으로 보는 shadowing login loop

가장 흔한 예시는 이렇다.

| 시점 | 브라우저에 저장된 cookie | 의미 |
|---|---|---|
| 예전 배포 | `session=old123; Path=/app` | `/app` 아래에서만 쓰던 옛 session |
| 새 login 후 | `session=new999; Path=/` | 이제 앱 전체에서 쓰려는 새 session |
| 현재 상태 | 이름은 둘 다 `session` | 두 cookie가 같이 남아 있다 |

이제 요청별로 달라진다.

| 요청 | 브라우저가 보낼 수 있는 cookie | 초보자 눈에 보이는 결과 |
|---|---|---|
| `GET /dashboard` | `session=new999` | 로그인 유지처럼 보일 수 있다 |
| `GET /app/me` | `session=old123; session=new999` | 서버가 old 값을 읽으면 다시 `/login` |

즉 "로그인은 분명 성공했는데 특정 화면만 다시 튄다"는 현상은,
종종 새 cookie가 없는 게 아니라 **old cookie가 같은 이름으로 섞여 들어온 상태**다.

---

## `Path` shadowing이 왜 제일 흔한가

초보자에게 가장 자주 보이는 장면은 `Path` migration 뒤 잔여 cookie다.

예를 들어 예전에는 `/app` 아래만 session을 썼고, 나중에 `/` 전체로 넓혔다고 하자.

```http
Set-Cookie: session=old123; Path=/app; HttpOnly; Secure
Set-Cookie: session=new999; Path=/; HttpOnly; Secure
```

브라우저는 둘 다 저장할 수 있다.

그 결과:

1. `/dashboard`에는 새 cookie만 간다
2. `/app/me`에는 old/new 둘 다 갈 수 있다
3. 서버나 proxy가 old 값을 먼저 해석하면 session lookup이 실패한다
4. 사용자는 "일부 화면에서만 다시 로그인하라네?"를 보게 된다

여기서 중요한 건 브라우저가 꼭 틀리게 동작한 게 아니라는 점이다.
브라우저는 scope 규칙대로 보냈고, 앱이 같은 이름을 재사용한 것이 문제다.

---

## `Domain` shadowing은 auth/app 분리 구조에서 자주 나온다

subdomain을 나눠 둔 구조에서는 `Domain` 차이 때문에 같은 이름 cookie가 공존할 수 있다.

예를 들어:

| cookie | 어디에 저장됐나 | 어느 요청에 붙을 수 있나 |
|---|---|---|
| `session=hostOnly1` | host-only on `auth.example.com` | `auth.example.com`에만 |
| `session=shared2` | `Domain=example.com` | `auth.example.com`, `app.example.com` 둘 다 가능 |

이 상태에서 `https://auth.example.com/callback` 같은 요청은 두 cookie를 모두 받을 수 있다.

그러면 이런 현상이 나온다.

- `app.example.com`에서는 로그인된 것처럼 보인다
- 그런데 `auth.example.com/callback`이나 `/logout`에서만 loop가 난다
- 사용자는 "분명 같은 session 이름인데 왜 host마다 다르게 보이지?"라고 느낀다

여기서도 핵심은 같다.

- 이름은 같아도 scope가 다르면 브라우저는 다른 cookie로 취급한다

---

## 왜 서버가 "잘못된 session"을 읽게 되나

브라우저가 duplicate cookie를 보낼 때, 서버 쪽 파서는 이를 한 가지 방식으로만 다루지 않는다.

- 어떤 framework는 첫 번째 값을 본다
- 어떤 proxy/library는 마지막 값을 남긴다
- 어떤 코드는 이름을 key로 하는 map에 넣으며 하나를 덮어쓴다

즉 앱이 기대하는 "대표 `session` 하나"라는 가정이 깨진다.

초보자 관점에서 안전한 이해는 이것이다.

- 브라우저가 같은 이름 cookie를 둘 이상 보낼 수 있다
- 서버는 그중 어느 값을 실제 session id로 사용할지 일관되지 않을 수 있다
- 그래서 stale cookie가 새 cookie를 shadowing한 것처럼 보인다

보통 `Path`가 더 구체적인 cookie가 먼저 오는 장면이 많지만, **순서에 기대면 안 된다.**

---

## DevTools에서 꼭 보는 세 칸

| 어디서 보나 | 확인할 질문 | 여기서 찾는 신호 |
|---|---|---|
| login 응답의 `Set-Cookie` | 새 cookie를 어떤 `Domain`/`Path`로 만들었나 | 같은 이름을 다른 scope로 또 만들었나 |
| `Application > Cookies` | 같은 이름이 두 줄 이상 있나 | `session`이 `Path=/app`, `Path=/`로 같이 있나 |
| 실패한 요청의 raw `Cookie` header | 실제로 무엇이 전송됐나 | `session=...; session=...` 중복 전송 |

여기서 초보자가 자주 놓치는 포인트는 두 가지다.

- `Name` column만 보면 중복을 놓친다
- framework가 파싱한 값만 보면 raw header의 중복을 못 본다

즉 `Domain`, `Path`, raw `Cookie` header를 같이 봐야 한다.

---

## 자주 하는 오해

### 1. "같은 이름이면 마지막 `Set-Cookie`가 무조건 이긴다"

아니다.

- `Domain`이나 `Path`가 다르면 둘 다 남을 수 있다
- overwrite는 "같은 이름 + 같은 scope"일 때 기대하는 편이 맞다

### 2. "cookie 하나 지우면 끝난다"

이것도 자주 틀린다.

`session; Path=/`를 지우는 응답은 `session; Path=/app`를 지우지 못한다.

즉 삭제도 보통 같은 `(이름, Domain, Path)`를 정확히 맞춰야 한다.

### 3. "서버 세션 저장소가 불안정해서 loop가 난다"

그럴 수도 있지만, 먼저 duplicate cookie를 배제해야 한다.

- 특정 route에서만 반복된다
- 같은 이름 cookie가 둘 이상 보인다
- raw `Cookie` header에 이름이 중복된다

이 세 가지가 보이면 shadowing이 더 직접적인 원인일 수 있다.

---

## 가장 작은 수정 방향

| 해야 할 일 | 이유 |
|---|---|
| session 주 cookie는 auth boundary 안에서 이름을 하나로 고정 | 같은 이름의 목적 다른 cookie를 줄인다 |
| scope를 바꿀 때는 old `Domain`/`Path` cookie를 명시적으로 만료 | 옛 cookie 잔존을 막는다 |
| 디버깅 때는 parsed cookie map 말고 raw `Cookie` header도 같이 확인 | 어떤 값이 실제로 들어왔는지 본다 |
| 임시 callback cookie와 주 session cookie는 가능하면 이름을 분리 | 같은 이름 collision을 줄인다 |

이 문서의 포인트는 "어떻게 구현할까"보다, **왜 일부 route만 로그인 루프가 나는지 설명할 수 있게 되는 것**이다.

---

## 다음 단계

- 우선 `cookie가 저장돼 있지만 요청에 안 붙는 문제` 전체를 먼저 정리하고 싶으면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 이어 간다.
- `302 -> /login`, `SavedRequest`, login HTML fallback까지 함께 보이면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)를 본다.
- cookie/session/JWT 역할 자체가 아직 섞여 보이면 [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)부터 다시 맞춘다.

## 한 줄 정리

duplicate cookie name shadowing은 "같은 이름 cookie가 서로 다른 `Domain`/`Path`로 함께 살아남아, 어떤 요청에서는 stale session이 같이 전송되거나 우선 해석되는 현상"이다. 그래서 login 자체는 성공했는데 특정 route나 host에서만 계속 다시 로그인 화면으로 튀는 혼란이 생긴다.
