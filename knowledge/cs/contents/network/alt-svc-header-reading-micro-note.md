# Alt-Svc Header Reading Micro-Note

> `Alt-Svc: h3=":443"; ma=86400` 같은 값을 처음 봤을 때, "이건 H3를 다음 새 연결에서 시도해도 된다는 짧은 메모"라고 읽게 만드는 beginner bridge

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
> - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)

retrieval-anchor-keywords: Alt-Svc header reading, Alt-Svc value reading, how to read Alt-Svc h3 443, Alt-Svc h3=":443" meaning, Alt-Svc ma meaning beginner, alt-svc header cheat sheet, alt-svc micro note, alt-svc first read, alternative service header beginner, h3 :443 same host meaning, alt-svc clear meaning beginner

## 먼저 잡는 mental model

`Alt-Svc` 값은 복잡한 설정문처럼 보여도, 초급자 첫 읽기는 아래 한 줄이면 충분하다.

> "이 사이트는 다음 새 연결에서 H3라는 다른 길도 시도해 볼 수 있고, 그 힌트를 잠시 기억해 둔다."

즉 처음에는 아래 2개만 읽으면 된다.

- `h3="..."`
  H3를 후보로 준다
- `ma=...`
  그 후보를 얼마나 기억할지 적는다

## 가장 자주 보는 모양 2개

| 값 | 초급자 1차 해석 |
|---|---|
| `Alt-Svc: h3=":443"; ma=86400` | "같은 host의 443 포트로 H3도 시도 가능, 이 힌트를 하루 정도 기억" |
| `Alt-Svc: h3="edge.example.net:443"; ma=3600` | "다음 새 연결에서 `edge.example.net:443` 쪽 H3도 후보, 이 힌트를 1시간 정도 기억" |

여기서 중요한 차이는 host를 생략했는지, 다른 host를 적었는지다.

## 조각별로 읽기

```http
Alt-Svc: h3=":443"; ma=86400
```

| 조각 | 첫 읽기 |
|---|---|
| `Alt-Svc` | "대체 서비스 힌트"라는 헤더 이름 |
| `h3` | HTTP/3 후보를 뜻함 |
| `":443"` | 같은 host에서 443 포트로 시도한다는 뜻으로 읽으면 됨 |
| `ma=86400` | 이 힌트를 최대 86400초 기억한다는 뜻 |

초급자에게는 이렇게 번역해 주면 된다.

```text
지금 응답을 준 이 사이트는,
다음 새 연결에서 같은 host의 443 포트 H3도 시도해 볼 수 있다.
이 힌트는 하루(86400초) 정도 기억할 수 있다.
```

## `:443`가 특히 헷갈리는 이유

`:443`를 처음 보면 "`host가 빠졌는데 잘못된 값인가?`"라고 생각하기 쉽다.
여기서는 복잡하게 들어가지 말고 이렇게 읽으면 충분하다.

- host가 없으면 보통 "지금 보고 있는 같은 host" 쪽으로 읽는다
- `443`은 HTTPS에서 익숙한 기본 포트라서 자주 보인다
- 그래서 `h3=":443"`는 "다른 서버 이름"보다 "같은 사이트의 H3 경로" 느낌으로 먼저 잡으면 된다

반대로 아래처럼 host가 보이면:

```http
Alt-Svc: h3="edge.example.net:443"; ma=3600
```

초급자 첫 해석은:

- "아, H3 후보가 같은 host가 아니라 `edge.example.net`이구나"
- "그래도 이건 아직 시도 후보일 뿐이구나"

정도면 충분하다.

## 흔한 오해 4개

| 오해 | 더 안전한 해석 |
|---|---|
| `h3=":443"`면 지금 이 응답도 이미 H3다 | 아니다. 보통은 다음 새 연결용 힌트다 |
| `ma=86400`이면 connection을 하루 유지한다 | 아니다. 초급자 첫 읽기에서는 "힌트 기억 시간" 정도로만 잡으면 된다 |
| `:443`는 값이 비어 있으니 이상한 헤더다 | 보통 같은 host의 443 포트를 뜻하는 축약형처럼 읽으면 된다 |
| 다른 host가 보이면 그 host로 모든 요청을 자동 전환한다 | 아니다. 우선은 "H3 후보를 알려 준다" 정도로만 본다 |

## 너무 깊게 들어가지 말고 여기서 멈춰도 되는 기준

이 문서는 값 모양을 읽는 브리지다. 아래까지 이해했으면 1차 목적은 달성이다.

- `h3`는 HTTP/3 후보다
- `":443"`는 같은 host의 443 포트처럼 읽는다
- `edge.example.net:443`처럼 보이면 다른 host 후보가 있다는 뜻이다
- `ma`는 그 힌트를 기억하는 시간이다

`cache scope`, `421`, cross-origin reuse 같은 말이 나오기 시작하면 이 문서에서 더 파지 말고 다음 문서로 넘기는 편이 안전하다.

## 다음에 이어서 볼 문서

- `Alt-Svc`를 배운 뒤 왜 첫 요청은 `h2`, 다음 새 연결은 `h3`처럼 보이는지 보려면 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- `ma`를 조금 더 정확히 보되 초급자 범위를 유지하려면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- `ma`, cache scope, `421`이 한꺼번에 섞이면 [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- H3 endpoint를 HTTP 응답과 DNS 중 어디서 배웠는지까지 보고 싶으면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)

## 한 줄 정리

`Alt-Svc: h3=":443"; ma=86400`는 초급자 기준으로 "`이 사이트는 다음 새 연결에서 H3도 시도해 볼 수 있고, 그 힌트를 하루 정도 기억한다`"라고 읽으면 된다.
