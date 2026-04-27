# 421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough


> 한 줄 요약: 421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
> wildcard certificate 때문에 host 이름은 맞아 보여도 routing boundary가 다르면 왜 `421 Misdirected Request`가 나는지, Browser DevTools, `curl`, proxy log에서 초보자가 바로 잡아야 할 신호만 따라가는 mini-lab

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../security/session-cookie-jwt-basics.md)

> 관련 문서:
> - [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
> - [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
> - [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
> - [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
> - [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
> - [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md)

retrieval-anchor-keywords: 421 trace mini lab, wildcard cert 421, wildcard certificate 421 walkthrough, coalescing rejected 421, same cert different backend 421, devtools curl proxy log 421, beginner 421 walkthrough, wildcard cert connection reuse rejected, misdirected request mini lab, wrong connection wildcard cert, 421 trace mini lab wildcard cert coalescing basics, 421 trace mini lab wildcard cert coalescing beginner, 421 trace mini lab wildcard cert coalescing intro, network basics, beginner network

<details>
<summary>Table of Contents</summary>

- [왜 이 mini-lab가 필요한가](#왜-이-mini-lab가-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [lab 상황](#lab-상황)
- [신호를 한 표로 먼저 보기](#신호를-한-표로-먼저-보기)
- [Step 1. DevTools에서 오탑승 흔적 잡기](#step-1-devtools에서-오탑승-흔적-잡기)
- [Step 2. `curl`로 status와 host target 고정하기](#step-2-curl로-status와-host-target-고정하기)
- [Step 3. proxy log에서 누가 421을 냈는지 확인하기](#step-3-proxy-log에서-누가-421을-냈는지-확인하기)
- [세 신호를 합쳐 한 줄로 쓰기](#세-신호를-합쳐-한-줄로-쓰기)
- [초보자가 자주 헷갈리는 포인트](#초보자가-자주-헷갈리는-포인트)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 mini-lab가 필요한가

초보자는 여기서 자주 섞는다.

- wildcard cert가 있으니 `www`와 `admin`은 같은 connection을 써도 되나?
- Browser Network 탭에서 `421`이 보이면 auth 문제인가?
- `curl`은 `421`을 보여 주는데 proxy log는 왜 upstream이 비어 있나?

이 문서는 **같은 incident를 세 화면에서 어떻게 읽는지**만 짧게 훈련한다.

## 먼저 잡는 mental model

한 줄로 줄이면 이렇다.

```text
wildcard cert는 이름이 맞는지 보여 주고,
421은 "이 이름을 이 connection으로 받지는 않겠다"를 보여 준다.
```

즉 `421`은 보통 certificate 실패보다 **connection reuse 거절**에 가깝다.

## lab 상황

아래처럼 가정한다.

```text
www.example.test   -> public edge
admin.example.test -> admin edge
certificate        -> *.example.test
```

- certificate는 두 host를 모두 덮는다.
- 하지만 `admin`은 별도 edge, 별도 routing policy를 쓴다.
- 브라우저가 기존 `www` connection을 `admin`에도 재사용하려 하면 edge가 `421`로 거절할 수 있다.

초보자용 해석:

- cert는 같아도
- front door가 다르면
- 같은 connection 공유는 거절될 수 있다

## 신호를 한 표로 먼저 보기

| 보는 곳 | 초보자 첫 신호 | 이 신호가 뜻하는 것 |
|---|---|---|
| DevTools | 같은 `admin` URL에서 `421`이 먼저 보이고 `Protocol`/`Connection ID`/`Remote Address`가 `www` 쪽과 겹친다 | 브라우저가 기존 shared connection에 `admin`을 실으려 했다 |
| `curl -v` | `Host` target은 `admin.example.test`인데 응답이 `< HTTP/2 421` 또는 `< HTTP/3 421`이다 | 서버가 "URL 자체"보다 "이 connection 문맥"을 거절했다 |
| proxy log | `authority=admin.example.test`, `status=421`, `upstream`이 비었거나 local reply 흔적이 있다 | 앱까지 보내기 전에 edge/front door가 잘못된 reuse를 끊었다 |

이 표의 핵심은 `421`을 auth/app 결과로 읽지 않는 것이다.

## Step 1. DevTools에서 오탑승 흔적 잡기

브라우저에서 먼저 `www.example.test`를 열고, 이어서 `admin.example.test/api/me`를 친다.

DevTools Network 탭에서 아래 4필드를 먼저 본다.

- `Status`
- `Protocol`
- `Connection ID`
- `Remote Address`

예시:

| URL | Status | Protocol | Connection ID | Remote Address | 읽는 법 |
|---|---:|---|---:|---|---|
| `https://www.example.test/` | `200` | `h2` | `17` | `203.0.113.10:443` | `www`용 기존 connection |
| `https://admin.example.test/api/me` | `421` | `h2` | `17` | `203.0.113.10:443` | `admin`이 `www` connection에 잘못 실림 |
| `https://admin.example.test/api/me` | `200` | `h2` | `24` | `203.0.113.20:443` | 새 admin connection으로 recovery |

여기서 초보자가 붙잡아야 할 한 줄은 이것이다.

- 같은 wildcard cert라도 `admin`은 `www` connection을 그대로 받지 않을 수 있다.

## Step 2. `curl`로 status와 host target 고정하기

`curl`은 브라우저의 coalescing 전체 맥락을 완전히 복제하는 도구라기보다, **status와 host target을 고정해서 보여 주는 확대경**에 가깝다.

예시:

```bash
curl --http2 -v https://admin.example.test/api/me
```

읽는 위치:

- `> GET /api/me HTTP/2`
- `> Host: admin.example.test`
- `< HTTP/2 421`

판독:

- `Host`는 `admin`으로 맞게 보냈다.
- 그런데 응답이 `421`이면 "URL path가 틀렸다"보다 "이 connection/authority 문맥이 틀렸다"를 먼저 본다.

H3 확인이 필요하면:

```bash
curl --http3-only -v https://admin.example.test/api/me
```

여기서도 초보자 첫 신호는 같다.

- `< HTTP/3 421`이면 H3에서도 wrong-connection/reuse 거절을 먼저 의심한다.

## Step 3. proxy log에서 누가 421을 냈는지 확인하기

proxy log에서는 app body보다 **front door가 먼저 끊었는지**를 본다.

예시:

```text
ts=10:15:02 route=public-edge authority=admin.example.test tls_sni=www.example.test status=421 response_code_details=misdirected_request upstream_cluster=-
ts=10:15:02 route=admin-edge  authority=admin.example.test tls_sni=admin.example.test status=200 upstream_cluster=admin-api
```

초보자용 읽는 법:

- 첫 줄: `admin` authority가 `public-edge`로 들어와 edge가 바로 `421`
- 둘째 줄: 새 admin 경로에서는 정상 처리

proxy log에서 자주 보는 신호를 압축하면 아래와 같다.

| 필드 | `421` 쪽에서 눈여겨볼 값 | 뜻 |
|---|---|---|
| `authority` 또는 `host` | `admin.example.test` | 요청 target 자체는 admin이다 |
| route / vhost / listener | `public-edge`처럼 엉뚱한 front door | wrong connection 또는 wrong routing boundary |
| `status` | `421` | edge가 misdirected request로 거절 |
| upstream | 비어 있음, `-`, local reply 흔적 | 앱까지 안 갔을 수 있음 |

## 세 신호를 합쳐 한 줄로 쓰기

초보자 메모는 길 필요가 없다. 아래 한 줄이면 충분하다.

```text
wildcard cert는 같았지만 DevTools에서 admin 요청이 www connection ID로 421을 받았고, curl도 admin Host에 421을 보여 주며, proxy log는 public-edge local 421이라 coalescing rejection으로 읽힌다.
```

## 초보자가 자주 헷갈리는 포인트

- wildcard cert가 같으면 connection 공유도 자동이라고 생각하면 안 된다.
- `421`을 보면 `403/404`처럼 auth나 path부터 파지 말고 connection 문맥을 먼저 본다.
- `curl`이 브라우저 coalescing 전체를 그대로 재현하지 못해도, `Host` target과 `421` status를 분리해서 확인하는 데는 충분히 유용하다.
- proxy log에서 upstream이 비어 있으면 "로그가 부족하다"보다 "edge가 앱까지 보내기 전에 끊었나?"를 먼저 본다.

## 한 줄 정리

wildcard cert `421` incident는 "인증서는 맞았지만 이 host를 이 shared connection으로 받지 않겠다"는 신호로 읽고, DevTools의 connection 흔적, `curl`의 host target, proxy log의 local `421`를 한 세트로 붙여 보면 초보자도 빠르게 방향을 잡을 수 있다.
