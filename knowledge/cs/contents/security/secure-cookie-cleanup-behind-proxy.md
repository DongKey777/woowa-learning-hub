# Secure Cookie Cleanup Behind Proxy

> 한 줄 요약: logout이나 cookie migration cleanup이 안 먹는다고 해서 곧바로 `bad tombstone`으로 단정하면 안 된다. proxy 뒤에서 다음 요청이 `http://...`로 꺾이면 `Secure` tombstone 자체가 전달되지 않거나, old cookie가 안 지워진 것처럼 보일 수 있다.

**난이도: 🟢 Beginner**

> 문서 역할: `primer bridge`
>
> 이미 `cookie cleanup이 안 먹는다`, `logout 후에도 old cookie가 남는다`, `migration tombstone을 보냈는데 DevTools에서 그대로 보인다` 같은 증거가 잡혔을 때, 이것이 **정말 tombstone scope 불일치인지** 아니면 **proxy / HTTPS 전달 불일치인지** 먼저 가르는 bridge다.

> 관련 문서:
> - `[primer]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)
> - `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
> - `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md)
> - `[primer bridge]` [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)
> - `[primer]` [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: secure cookie cleanup behind proxy, cookie cleanup behind proxy, secure tombstone behind proxy, cookie tombstone secure delivery, bad tombstone vs secure delivery, logout cookie cleanup behind proxy, secure cookie delete not working proxy, max-age 0 secure cookie proxy, expires delete cookie https proxy, cookie cleanup seems ignored behind alb, cookie tombstone not applied behind nginx, stale secure cookie after logout proxy, secure logout cookie remains proxy, cookie migration cleanup proxy mismatch, X-Forwarded-Proto tombstone, secure cookie delete looks broken, secure cookie cleanup http redirect, old cookie not deleted behind load balancer, tombstone delivered over http, beginner cookie cleanup proxy guide
retrieval-anchor-keywords: cookie deleted locally but still visible, logout clears cookie locally not in prod, secure cookie logout works local fails prod, bad tombstone vs wrong scheme redirect, host-only cookie tombstone vs secure redirect mismatch, tombstone exact domain path vs secure delivery issue

## 왜 이 문서를 먼저 읽나

초보자가 자주 보는 장면은 이렇다.

- logout 응답에서 `Set-Cookie: session=; Max-Age=0`를 보냈다
- 또는 migration cleanup tombstone도 같이 보냈다
- 그런데 prod에서만 old cookie가 계속 남아 보인다
- 그래서 "delete cookie header가 잘못됐나?"라고 생각한다

여기서 실제 원인은 둘 중 하나인 경우가 많다.

| 갈래 | 실제로 깨지는 지점 | 먼저 잡을 증거 |
|---|---|---|
| bad tombstone | old cookie의 `Domain` / host-only / `Path`와 delete header가 안 맞는다 | 같은 host에서 봐도 old cookie row가 그대로 남고, redirect URL은 계속 HTTPS다 |
| `Secure` delivery problem behind proxy | logout/cleanup 뒤 다음 이동이 `http://...`로 꺾이거나, cleanup 응답이 HTTPS 문맥으로 전달되지 않는다 | prod proxy 뒤에서만 재현되고, redirect URL 또는 request scheme이 틀어진다 |

핵심 mental model은 짧다.

- tombstone은 "어느 cookie를 지울지"를 맞추는 문제다
- `Secure` delivery는 "그 지우기 지시가 브라우저까지 HTTPS 문맥으로 갔는가"의 문제다

즉 **삭제 지시 자체가 틀린 것**과 **삭제 지시가 전달되는 환경이 틀린 것**은 다른 문제다.

## 막히면 돌아갈 자리

이 bridge에서 헷갈리면 더 깊게 내려가기 전에 category navigator로 먼저 복귀한다.

- cleanup이 `bad tombstone`인지 proxy 문제인지 아직도 애매하면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 symptom을 다시 고른다.
- scope 판단이 먼저 선명해지면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md) 한 장만 읽고 다시 README로 복귀한다.
- proxy/HTTPS 전달 문제로 굳어지면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) 한 장만 읽고, 다음 branch 선택은 다시 README에서 한다.

---

## 가장 중요한 mental model

cookie cleanup은 아래 두 단계를 모두 통과해야 끝난다.

1. 서버가 old cookie와 정확히 맞는 tombstone을 만든다
2. 브라우저가 그 tombstone을 올바른 HTTPS 문맥에서 받는다

둘 중 하나라도 틀리면 초보자 눈에는 둘 다 "cookie가 안 지워진다"로 보인다.

| 단계 | 질문 | 틀리면 보이는 현상 |
|---|---|---|
| tombstone identity | `name` / `Domain` / host-only / `Path`가 old cookie와 맞나 | old cookie row가 그대로 남는다 |
| tombstone delivery | response와 다음 redirect가 HTTPS 기준으로 유지되나 | `Secure` cleanup이 적용되지 않거나, 지워진 뒤 다시 다른 old flow가 살아난 것처럼 보인다 |

짧게 말하면:

- **bad tombstone**은 "주소를 잘못 적은 회수 지시"
- **proxy mismatch**는 "회수 지시를 HTTPS 문맥으로 전달하지 못한 상태"

---

## 먼저 20초 분기표

| 지금 가장 먼저 보이는 증거 | 이쪽이 더 가깝다 | 다음 문서 |
|---|---|---|
| old cookie의 `Domain`/`Path`를 바꾼 직후부터 cleanup이 안 먹고, redirect는 계속 `https://...`다 | bad tombstone | [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md) |
| 로컬은 되는데 ALB/Nginx/ingress 뒤 prod에서만 cleanup이 안 먹고, redirect가 한 번이라도 `http://...`로 꺾인다 | `Secure` delivery problem behind proxy | 이 문서 계속 읽기 후 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| `Application > Cookies`에는 old row가 남는데 실패 요청 raw `Cookie` header에 같은 이름이 두 번 보인다 | cleanup 실패가 duplicate로 번진 상태 | [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md) -> [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md) |
| cleanup redirect는 HTTPS인데 특정 host/path에서만 old cookie가 남는다 | scope mismatch | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |

---

## 한 장면으로 보는 두 실패

### A. tombstone이 잘못된 경우

old cookie가 host-only `auth.example.com`, `Path=/`였다고 하자.

```http
Set-Cookie: session=old123; Path=/; HttpOnly; Secure
```

그런데 cleanup을 이렇게 보냈다.

```http
Set-Cookie: session=; Domain=example.com; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT
```

이건 shared-domain cookie 삭제일 뿐이다.
host-only old cookie를 정확히 가리키지 못하므로 브라우저는 old row를 남길 수 있다.

이 경우의 핵심은:

- redirect가 HTTPS인지 아닌지보다
- **old cookie scope와 tombstone scope가 정확히 맞는지**다

즉 이 갈래는 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)이 먼저다.

### B. tombstone은 맞는데 proxy 뒤에서만 안 되는 경우

logout 응답이 이렇게 내려왔다고 하자.

```http
Set-Cookie: session=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; Secure
Location: http://app.example.com/login
```

여기서 tombstone header 모양은 얼핏 맞아 보인다.
하지만 앱이 proxy 뒤에서 요청을 HTTP로 착각해 redirect를 `http://...`로 만들면,
cleanup 직후의 브라우저 이동과 이후 `Secure` cookie 판단이 어긋난다.

초보자 눈에는 이 장면도 그냥 "`Max-Age=0`가 안 먹었다"처럼 보이지만,
실제 핵심은:

- proxy가 original HTTPS를 앱에 제대로 전달했는가
- 앱이 `X-Forwarded-Proto`를 믿고 `https://...` redirect를 만들었는가

즉 이 갈래는 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)이 먼저다.

---

## 왜 `Secure` tombstone 전달 문제가 헷갈리나

초보자는 보통 이렇게 생각한다.

- "삭제 cookie는 빈 값이니까 덜 까다롭겠지"
- "new cookie 발급과 delete cookie는 완전히 같은 방식으로 적용되겠지"

하지만 브라우저가 보는 것은 둘 다 `Set-Cookie`다.
즉 cleanup tombstone도 cookie response 정책의 일부다.

특히 beginner가 헷갈리는 포인트는 다음 두 가지다.

| 오해 | 실제로는 |
|---|---|
| `Max-Age=0`만 있으면 언제나 old cookie가 사라진다 | old scope가 맞아야 하고, cleanup 응답이 브라우저에 기대한 문맥으로 도달해야 한다 |
| `Secure`는 새 cookie 발급에만 중요하다 | cleanup tombstone도 `Secure` cookie lifecycle의 일부라 HTTPS/proxy mismatch 영향을 같이 받는다 |

---

## 초보자용 체크 순서

1. old cookie row의 `Name` / `Domain` / `Path` / host-only 여부를 적는다.
2. cleanup 응답 `Set-Cookie`가 그 old scope와 정확히 맞는지 본다.
3. 같은 응답의 `Location`이나 다음 요청 URL이 `https://...`인지 본다.
4. prod proxy 뒤에서만 `http://...`로 꺾이면 tombstone 모양만 보지 말고 proxy branch를 먼저 연다.

가장 작은 판단 규칙:

- **scope가 다르면 bad tombstone**
- **scope는 맞아 보이는데 proxy 뒤에서만 깨지면 `Secure` delivery problem**

---

## beginner가 자주 놓치는 비교표

| 비교 대상 | bad tombstone 쪽 신호 | proxy / HTTPS 전달 문제 쪽 신호 |
|---|---|---|
| 재현 환경 | 로컬/운영 모두 같은 scope에서 재현 가능 | 로컬은 되는데 proxy/LB 뒤에서만 잘 재현 |
| redirect URL | 계속 `https://...` | cleanup 직후 `http://...`로 꺾이거나 public origin 재구성이 틀림 |
| old cookie row | 특정 `Domain`/`Path` row만 계속 남음 | redirect chain, logout finish URL, callback URL까지 같이 이상해지는 경우가 많음 |
| 다음 문서 | [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md) | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |

---

## 예시: "bad tombstone처럼 보였는데 사실 proxy 문제"

아래 장면은 beginner가 가장 많이 헷갈리는 예시다.

1. prod logout 후 old cookie가 남아 보인다
2. 팀이 `Path` / `Domain` tombstone을 여러 번 바꿔 본다
3. 그래도 prod에서만 증상이 남는다
4. 나중에 보니 logout 응답 `Location`이 `http://...`였다

이 경우에는 tombstone을 더 바꾸기보다,
먼저 proxy/app이 original scheme을 복원하는지 봐야 한다.

즉 "`delete cookie 모양`을 고치는 일"과
"`https` redirect를 유지하는 일"을 분리해야 한다.

---

## 어디서 확인하면 되나

| 어디서 보나 | 확인 질문 |
|---|---|
| `Application > Cookies` old row | 정말 어떤 `Domain` / `Path` old cookie가 남아 있나 |
| cleanup 응답 `Set-Cookie` | old scope와 exact match인가 |
| cleanup 응답 `Location` | `https://...`인가, `http://...`로 꺾였나 |
| logout 뒤 첫 요청 URL | 브라우저가 실제로 어디로 이동했나 |

정확한 DevTools 칸이 헷갈리면 [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)로 돌아가면 된다.

---

## 다음 단계

- old cookie scope inventory와 tombstone 설계가 먼저면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)으로 간 뒤, 갈래를 다시 고를 때는 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 복귀한다.
- redirect나 next request URL이 `http://...`로 꺾이면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)로 간 뒤, follow-up이 끝나면 다시 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 다음 symptom을 고른다.
- 처음 분기 자체를 다시 잡아야 하면 [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)로 돌아간 뒤, 그다음 entrypoint는 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 맞춘다.
- 질문이 cookie scope, duplicate cookie, proxy redirect를 한꺼번에 섞으면 [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md)로 잠깐 복귀하고, 추가 deep dive를 더 열기 전에 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 한 번 되돌아온다.

## 한 줄 정리

cookie cleanup 실패는 항상 `bad tombstone`이 아니다. old cookie를 정확히 가리키는 `Domain`/host-only/`Path` tombstone 문제와, proxy 뒤에서 `Secure` cleanup이 HTTPS 문맥으로 전달되지 않는 문제를 먼저 분리해야 beginner가 헛수고 없이 원인을 좁힐 수 있다.
