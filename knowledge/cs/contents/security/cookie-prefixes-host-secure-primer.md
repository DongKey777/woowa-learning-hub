# Cookie Prefixes Primer: `__Host-` vs `__Secure-`

> 한 줄 요약: `__Secure-`와 `__Host-`는 "멋있어 보이는 이름"이 아니라 브라우저가 추가 규칙을 검사하는 cookie 이름 prefix다. 그래서 prefix 에러를 보면 value보다 먼저 `Secure`, `Domain`, `Path` 조합이 규칙을 만족하는지 보면 된다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 문서 역할: `primer bridge`
>
> DevTools나 브라우저 경고에서 "`__Host-` cookie rejected", "`__Secure-` prefix error" 같은 문구를 봤을 때 여는 첫 문서다. prefix 규칙을 이해한 뒤에도 cookie가 저장되지 않으면 [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)로, `Secure` 축이 proxy/HTTPS 경계에서 흔들리면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)로 바로 내려간다.

> 관련 문서:
> - `[primer]` [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)
> - `[primer]` [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)
> - `[follow-up primer]` [__Host- Cookie Migration Primer](./host-cookie-migration-primer.md)
> - `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
> - `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - `[intermediate]` [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](../network/cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: cookie prefix primer, __host __secure cookie primer, __host cookie rejected beginner, __secure cookie rejected beginner, cookie prefix error secure domain path, __host prefix no domain path=/ secure, __secure prefix requires secure, browser cookie prefix error primer, cookie prefix rules beginner, devtools __host __secure blocked, cookie prefixes host secure guide, prefix cookie rule interaction, cookie prefixes host secure primer basics, cookie prefixes host secure primer beginner, cookie prefixes host secure primer intro
retrieval-anchor-keywords: __Host cookie Domain forbidden, __Host cookie Path slash required, __Host cookie Secure required, __Secure cookie Secure required, prefix cookie behind proxy, prefix cookie scope mismatch, prefix cookie devtools checklist, cookie prefix vs cookie attribute beginner

## 먼저 잡을 mental model

prefix는 cookie attribute를 대신하는 magic 옵션이 아니다.

- `__Secure-`는 "`Secure`가 꼭 있어야 한다"는 이름 규칙이다
- `__Host-`는 "`Secure`가 있어야 하고, `Domain`은 없어야 하고, `Path=/`여야 한다"는 더 강한 이름 규칙이다

초보자용 기억 문장:

- `__Secure-`는 "HTTPS 전용 표시가 꼭 붙어야 하는 쿠키"
- `__Host-`는 "현재 host 루트 전용 쿠키"

즉 prefix 에러는 보통 "이름은 prefix인데 실제 속성 조합은 그 약속을 안 지켰다"는 뜻이다.

---

## 15초 비교표

| 이름 prefix | 꼭 필요한 것 | 금지되거나 고정되는 것 | 감각적으로 보면 |
|---|---|---|---|
| `__Secure-` | `Secure` | 없음 | "HTTPS 전용 badge가 붙은 cookie" |
| `__Host-` | `Secure` | `Domain` 금지, `Path=/` 고정 | "이 host 루트에만 묶인 cookie" |

바로 기억할 규칙:

- `__Secure-foo`인데 `Secure`가 없으면 reject될 수 있다
- `__Host-foo`인데 `Domain=example.com`이 있으면 reject될 수 있다
- `__Host-foo`인데 `Path=/app`처럼 루트가 아니면 reject될 수 있다

---

## 왜 브라우저가 prefix를 따로 보나

보안 의도와 실제 cookie scope가 어긋나는 실수를 줄이기 위해서다.

예를 들어 이름이 `__Host-session`이면 브라우저는 이런 기대를 한다.

- 이 cookie는 현재 응답 host에만 묶여 있어야 한다
- subdomain 공유용 `Domain=example.com` cookie면 안 된다
- 특정 하위 경로 전용이 아니라 루트 기준이어야 한다

그래서 prefix는 "보안 naming convention"이 아니라 **브라우저가 검증하는 scope contract**에 가깝다.

---

## 가장 흔한 성공/실패 예시

### `__Secure-`는 이 정도로 보면 된다

성공 예시:

```http
Set-Cookie: __Secure-session=abc123; Secure; Path=/; HttpOnly; SameSite=Lax
```

실패하기 쉬운 예시:

```http
Set-Cookie: __Secure-session=abc123; Path=/; HttpOnly; SameSite=Lax
```

여기서 문제는 간단하다.

- 이름은 `__Secure-...`
- 그런데 `Secure`가 없다

### `__Host-`는 조건이 더 많다

성공 예시:

```http
Set-Cookie: __Host-session=abc123; Secure; Path=/; HttpOnly; SameSite=Lax
```

실패하기 쉬운 예시 1:

```http
Set-Cookie: __Host-session=abc123; Secure; Domain=example.com; Path=/; HttpOnly; SameSite=Lax
```

문제:

- `__Host-`인데 `Domain`이 있다
- 그래서 host-only가 아니라 shared-domain cookie가 되려 한다

실패하기 쉬운 예시 2:

```http
Set-Cookie: __Host-session=abc123; Secure; Path=/app; HttpOnly; SameSite=Lax
```

문제:

- `__Host-`인데 `Path=/`가 아니다
- 브라우저가 기대한 "host 루트 전용" 조건을 안 맞춘다

---

## `Secure`, `Domain`, `Path`가 prefix와 어떻게 엮이나

| 속성 | `__Secure-`와 관계 | `__Host-`와 관계 | 초보자용 해석 |
|---|---|---|---|
| `Secure` | 필수 | 필수 | HTTPS 전용이어야 prefix 약속을 지킨다 |
| `Domain` | 써도 prefix 자체는 가능 | 쓰면 안 됨 | `__Host-`는 shared-domain cookie가 될 수 없다 |
| `Path` | 아무 path나 가능 | 반드시 `/` | `__Host-`는 특정 하위 경로 전용으로 쪼개지지 않는다 |

이 표에서 beginner가 가장 자주 놓치는 한 줄:

- **`__Host-`는 "`__Secure-`보다 더 엄격한 host-only 규칙"이다**

즉 이런 식으로 생각하면 헷갈림이 줄어든다.

1. `__Secure-`인지 먼저 본다
2. 그러면 최소 `Secure`는 있어야 한다
3. `__Host-`라면 거기에 `Domain` 없음, `Path=/`를 추가로 검사한다

---

## common confusion

### 1. "`__Secure-`면 `Domain`도 못 쓰나요?"

아니다.

- `__Secure-`의 핵심 조건은 `Secure`
- `Domain`과 `Path`는 일반 cookie처럼 별도 설계 문제다

예를 들어 이건 가능하다.

```http
Set-Cookie: __Secure-shared=abc123; Secure; Domain=example.com; Path=/; HttpOnly; SameSite=Lax
```

다만 "가능하다"와 "권장된다"는 다른 말이다.
shared-domain 범위가 정말 필요한지는 따로 판단해야 한다.

### 2. "`__Host-`가 더 안전하니까 subdomain 공유 cookie에도 붙이면 좋지 않나요?"

안 된다.

- `__Host-`는 `Domain`을 금지한다
- 그래서 `auth.example.com`에서 만든 `__Host-session`을 `app.example.com`과 공유하는 용도로 쓸 수 없다

subdomain 공유가 필요하면 shared-domain cookie나 handoff 구조를 따로 봐야 한다.
이때는 [__Host- Cookie Migration Primer](./host-cookie-migration-primer.md)로 내려간다.

### 3. "prefix 규칙은 맞췄는데도 cookie가 안 남아요"

그럼 prefix 다음 갈래를 보면 된다.

| 지금 보이는 증거 | 다음 문서 |
|---|---|
| DevTools blocked reason이 `SameSite`나 invalid `Domain`을 더 말한다 | [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) |
| `Secure` cookie인데 proxy/LB 뒤에서만 안 된다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| `Application`에는 보이는데 다음 요청에 안 붙는다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |

### 4. "`__Host-`면 XSS나 CSRF도 자동으로 막히나요?"

아니다.

- prefix는 cookie scope 규칙을 더 엄격하게 만드는 도구다
- `HttpOnly`, `SameSite`, CSRF token, XSS 방어를 대신하지 않는다

즉 prefix는 "좋은 기본 shape"를 강제하는 장치이지, 모든 웹 보안 문제의 만능 해법이 아니다.

---

## DevTools에서 바로 볼 것

| 어디서 보나 | 확인할 질문 |
|---|---|
| `Response Headers > Set-Cookie` | cookie 이름이 `__Secure-` / `__Host-`인데 속성이 규칙과 맞나 |
| `Issues` 또는 blocked reason | prefix 관련 문구가 있는가 |
| `Application > Cookies` | reject되지 않고 row가 실제로 생겼는가 |
| 실패한 요청의 `Request URL` | `Secure` cookie가 붙을 만큼 HTTPS인가 |

실전 quick check:

- `__Secure-...`인데 `Secure`가 빠졌나
- `__Host-...`인데 `Domain`이 있나
- `__Host-...`인데 `Path=/`가 아니나
- prefix는 맞는데 HTTPS/proxy 흐름이 흔들리나

---

## 바로 써먹는 decision shortcut

| 내가 하려는 것 | prefix 선택 |
|---|---|
| "이 cookie는 HTTPS 전용이어야 한다" | `__Secure-` 검토 |
| "이 cookie는 현재 host 루트에만 묶고 싶다" | `__Host-` 검토 |
| "여러 subdomain이 같은 cookie를 읽어야 한다" | `__Host-`는 아님. shared-domain 또는 handoff 설계를 본다 |

초보자용 한 줄 결론:

- **shared cookie면 보통 `__Host-`가 아니다**
- **host-only root cookie면 `__Host-`를 검토할 수 있다**
- **HTTPS 전용 표시만 강제하고 싶으면 `__Secure-`가 더 가깝다**

---

## 다음 한 걸음과 복귀 경로

| 지금 보이는 증거 | 다음 한 장 | 읽고 나서 돌아올 자리 |
|---|---|---|
| prefix 에러 문구를 broader cookie reject 문맥에서 읽고 싶다 | [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |
| `__Host-` 전환 설계와 stale shared session cleanup까지 같이 봐야 한다 | [__Host- Cookie Migration Primer](./host-cookie-migration-primer.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| prefix는 맞는데 특정 환경에서만 `Secure` cookie가 깨진다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

초보자용 복귀 규칙:

- follow-up 한 장만 읽고도 증상이 섞여 보이면 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)에서 같은 cookie branch를 다시 고른다.
- proxy, shared-domain migration, blocked reason이 동시에 보이면 바로 deep dive를 늘리지 말고 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 첫 갈래를 다시 자른다.

## 한 줄 정리

`__Secure-`와 `__Host-`는 "멋있어 보이는 이름"이 아니라 브라우저가 추가 규칙을 검사하는 cookie 이름 prefix다. 그래서 prefix 에러를 보면 value보다 먼저 `Secure`, `Domain`, `Path` 조합이 규칙을 만족하는지 보면 된다.
