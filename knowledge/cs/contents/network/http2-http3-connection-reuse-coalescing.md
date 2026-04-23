# HTTP/2와 HTTP/3 Connection Coalescing 입문

> 이미 열린 H2/H3 연결을 언제 다른 origin까지 같이 쓸 수 있는지, 브라우저와 서버가 각각 무엇을 만족해야 하는지부터 잡는 beginner primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/3와 QUIC 실전 트레이드오프](./http3-quic-practical-tradeoffs.md)
> - [SNI Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)
> - [Connection Reuse vs Service Discovery Churn](./connection-reuse-vs-service-discovery-churn.md)

retrieval-anchor-keywords: HTTP/2 connection coalescing, HTTP/3 connection coalescing, origin coalescing, connection reuse across origins, multiple origins same connection, certificate SAN reuse, subjectAltName, wildcard certificate, 421 misdirected request, Alt-Svc connection reuse, same IP edge, authority, authoritative server, browser coalescing rules, shared H2 connection, shared H3 connection

<details>
<summary>Table of Contents</summary>

- [왜 헷갈리나](#왜-헷갈리나)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [용어를 짧게 정리하면](#용어를-짧게-정리하면)
- [언제 한 connection을 여러 origin이 같이 쓸 수 있나](#언제-한-connection을-여러-origin이-같이-쓸-수-있나)
- [HTTP/2와 HTTP/3는 무엇이 다르나](#http2와-http3는-무엇이-다르나)
- [브라우저 체크리스트](#브라우저-체크리스트)
- [서버운영자 체크리스트](#서버운영자-체크리스트)
- [작은 예시로 보기](#작은-예시로-보기)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 헷갈리나

입문자가 가장 자주 섞는 개념은 아래 두 쌍이다.

- 같은 origin인가?
- 같은 connection을 써도 되나?

이 둘은 같은 질문이 아니다.

- **같은 origin**이면 보통 같은 connection을 재사용하기 쉽다
- **다른 origin**이어도 조건이 맞으면 같은 connection을 공유할 수 있다

그래서 브라우저에서는 이런 장면이 나온다.

- `https://www.example.com`을 보다가
- `https://static.example.com` 요청이 나갔는데
- 새 연결을 열지 않고 기존 H2/H3 연결에 같이 실릴 수 있다

이때 브라우저가 하는 판단이 바로 **connection coalescing**이다.

### Retrieval Anchors

- `HTTP/2 connection coalescing`
- `HTTP/3 connection coalescing`
- `origin coalescing`
- `multiple origins same connection`
- `421 misdirected request`
- `authority`
- `certificate SAN`
- `Alt-Svc connection reuse`

---

## 먼저 잡는 mental model

간단히 이렇게 생각하면 된다.

- connection reuse: 이미 연 문을 같은 가게가 다시 쓴다
- coalescing: 간판은 다른데 같은 프런트 데스크가 안전하게 둘 다 처리할 수 있으면 문 하나를 같이 쓴다

중요한 점은 "같은 건물"처럼 보여도 정말 같은 프런트 데스크가 맞아야 한다는 것이다.

- 인증서가 두 이름을 모두 커버해야 하고
- 브라우저가 그 연결이 새 origin에도 안전하다고 믿어야 하고
- 서버도 그 connection에서 그 origin 요청을 제대로 처리할 수 있어야 한다

즉 coalescing은 "연결을 아끼는 최적화"이지만, 더 근본적으로는 **이 연결이 그 origin에 대해 authoritative한가**를 확인하는 문제다.

---

## 용어를 짧게 정리하면

| 용어 | 뜻 | 입문 감각 |
|---|---|---|
| origin | `scheme + host + port` 조합 | `https://api.example.com:443` 같은 요청 대상 |
| connection reuse | 이미 열린 연결을 다시 사용 | 같은 origin 요청을 기존 H2/H3 연결에 다시 실음 |
| connection coalescing | 서로 다른 origin이 한 연결을 공유 | `www`와 `static`이 같은 연결을 나눠 씀 |
| authoritative | 그 서버가 그 origin을 진짜로 처리해도 됨 | "이 간판 요청을 이 프런트 데스크가 받아도 맞다" |
| `421 Misdirected Request` | 잘못 공유된 연결이라고 서버가 거절 | "이 origin은 이 연결로 보내지 마" |

짧게 요약하면:

- reuse는 "같은 대상의 재사용"
- coalescing은 "다른 대상까지 공유"

---

## 언제 한 connection을 여러 origin이 같이 쓸 수 있나

실제 브라우저 구현은 조금씩 다르지만, beginner 관점에서는 아래 4가지를 같이 보면 된다.

| 조건 | 왜 필요한가 | 실무 감각 |
|---|---|---|
| 이미 건강한 H2/H3 연결이 있다 | 공유할 대상 connection이 있어야 한다 | idle timeout으로 닫혔으면 새 연결 필요 |
| 인증서가 새 origin도 커버한다 | 그 서버가 새 hostname에 대해 authoritative해야 한다 | SAN / wildcard가 자주 등장 |
| 브라우저가 같은 edge/endpoint라고 본다 | 전혀 다른 서버에 잘못 보내면 안 된다 | H2는 같은 IP/edge로 보이는지, H3는 같은 QUIC endpoint/Alt-Svc인지가 중요 |
| 서버 라우팅이 그 연결에서 새 origin도 올바르게 처리한다 | 인증서만 맞고 라우팅이 틀리면 오동작한다 | CDN/LB/TLS terminator가 실제로 둘 다 받아야 한다 |

여기에 마지막 안전장치가 하나 더 있다.

- 서버가 "이 origin은 이 연결로 받지 않겠다"면 `421 Misdirected Request`를 보낼 수 있다
- 브라우저는 그 신호를 보면 그 origin용 새 연결을 따로 연다

즉 한 줄로 줄이면:

**브라우저가 보기에 안전하고, 서버도 실제로 처리 가능해야 여러 origin을 한 connection에 묶을 수 있다.**

---

## HTTP/2와 HTTP/3는 무엇이 다르나

둘 다 큰 원리는 비슷하지만, 브라우저가 connection을 바라보는 방식은 조금 다르다.

| 항목 | HTTP/2 | HTTP/3 |
|---|---|---|
| 공유하는 것 | TCP + TLS 연결 | QUIC 연결 |
| 브라우저가 주로 보는 것 | 인증서, 이미 열린 TLS 연결, 같은 edge/IP인지 여부 | 인증서, 이미 열린 QUIC 연결, `Alt-Svc`나 H3 endpoint 정보 |
| 흔한 blocker | cert는 맞지만 실제 backend가 다름, SNI/Host 라우팅 불일치 | UDP/H3 endpoint가 다름, `Alt-Svc`가 일부 origin에만 맞음 |
| 거절 신호 | `421 Misdirected Request` | `421 Misdirected Request` |

### HTTP/2 감각

HTTP/2에서는 브라우저가 이미 가진 **하나의 TLS 연결**을 다른 origin에도 써도 되는지 본다.

- 인증서가 두 host를 모두 커버해야 하고
- 브라우저는 보통 같은 edge에 도착하는지 보수적으로 확인한다
- 서버는 `:authority`가 달라져도 올바른 사이트로 라우팅해야 한다

### HTTP/3 감각

HTTP/3에서도 생각 자체는 같다.

- 이미 열린 QUIC 연결이 있고
- 그 연결의 인증서가 새 origin에도 맞고
- H3 endpoint가 실제로 그 origin도 처리할 수 있으면
- 브라우저가 같은 connection을 재사용할 수 있다

다만 H3는 브라우저가 그 endpoint를 보통 `Alt-Svc` 같은 신호로 배우기 때문에, "H3를 어디로 시도했는가"가 같이 중요해진다.

---

## 브라우저 체크리스트

브라우저 쪽 판단을 초보자용으로 줄이면 아래 순서다.

1. 이미 열린 H2/H3 connection이 있는가?
2. 그 연결에서 받은 인증서가 새 origin hostname에도 유효한가?
3. 이 connection이 새 origin을 처리하는 같은 edge/endpoint라고 믿을 근거가 있는가?
4. 이전에 `421` 같은 거절 신호를 받은 적은 없는가?
5. 새로 연결하는 편이 더 안전하다고 판단할 이유는 없는가?

핵심은 브라우저가 **"같은 certificate이니 무조건 공유"** 하지 않는다는 점이다.

브라우저는 보통 꽤 보수적으로 행동한다.

- cert만 맞고 endpoint가 다르게 보이면 안 묶을 수 있다
- H3는 `Alt-Svc` cache나 endpoint 정보가 없으면 처음부터 새 QUIC 경로를 못 쓸 수 있다
- connection 상태가 나쁘거나 닫힐 시점이면 새 연결을 열 수 있다

즉 coalescing은 브라우저가 "할 수 있으면 한다"에 가깝지, "항상 해야 한다"는 규칙이 아니다.

---

## 서버운영자 체크리스트

서버/CDN/LB 입장에서 "브라우저가 coalescing해도 안전한 상태"를 만들려면 아래를 확인하면 된다.

1. 여러 origin이 정말 같은 edge에서 처리되는가?
2. 인증서 SAN 또는 wildcard가 그 origin들을 모두 커버하는가?
3. TLS termination 뒤 라우팅이 `Host`/`:authority` 기준으로 올바르게 분기되는가?
4. H3를 광고한다면 `Alt-Svc` endpoint가 그 origin에도 실제로 authoritative한가?
5. 잘못 공유된 요청이 들어오면 `421 Misdirected Request`로 거절할 수 있는가?
6. 로그와 메트릭이 connection 단위뿐 아니라 origin/authority 단위로도 보이는가?

특히 아래 상황은 주의해야 한다.

- wildcard cert 하나로 여러 host를 덮었지만 backend는 완전히 분리된 경우
- TLS terminator가 첫 SNI 기준으로 upstream을 고정해 버리는 경우
- CDN 설정상 `www`와 `static`은 같은 edge인데 `api`는 다른 정책을 써야 하는 경우

즉 서버 쪽 핵심은 "같이 받아도 된다"는 사실을 **인증서뿐 아니라 라우팅과 운영 설정으로도 보장**하는 것이다.

---

## 작은 예시로 보기

### 예시 1: coalescing이 잘 되는 경우

- `https://www.example.com`
- `https://static.example.com`

조건:

- 둘 다 같은 CDN edge로 간다
- 인증서 SAN이 두 hostname을 모두 포함한다
- edge가 `Host`/`:authority`를 보고 올바른 서비스로 보낸다

결과:

- 브라우저는 기존 H2 또는 H3 연결을 새로 열지 않고 공유할 수 있다

### 예시 2: 인증서는 맞지만 공유하면 안 되는 경우

- `https://api.example.com`
- `https://admin.example.com`

조건:

- wildcard cert `*.example.com`은 둘 다 커버한다
- 하지만 `admin`은 별도 보안 영역이고 다른 LB/정책이 필요하다

결과:

- 인증서만 보고 묶으면 위험하다
- 서버는 coalescing이 일어나지 않게 보수적으로 설정하거나, 잘못 온 요청에 `421`을 보내야 한다

### 예시 3: H3에서 특히 자주 보는 경우

- `www.example.com`이 `Alt-Svc: h3="edge.example.net:443"`를 광고한다
- 그 H3 endpoint의 인증서가 `www.example.com`과 `static.example.com` 모두에 유효하다
- `static`도 실제로 같은 H3 edge에서 처리된다

결과:

- 브라우저는 두 origin을 같은 H3 connection으로 묶을 수 있다

반대로 `static`은 다른 edge 정책을 써야 한다면, 같은 `Alt-Svc` endpoint를 함부로 공유하면 안 된다.

---

## 자주 헷갈리는 포인트

### 같은 origin이어야만 같은 connection을 쓰는가

아니다.

- 같은 origin이면 reuse가 쉽다
- 다른 origin이어도 조건이 맞으면 coalescing 가능하다

### 같은 IP면 무조건 coalescing되는가

아니다.

- 같은 IP는 힌트일 뿐이다
- 인증서와 라우팅이 같이 맞아야 한다

### 인증서 SAN만 맞으면 충분한가

아니다.

- SAN은 필요 조건에 가깝다
- backend routing과 authority 처리가 틀리면 잘못된 서버로 갈 수 있다

### 서버가 원하면 브라우저에게 coalescing을 강제할 수 있는가

아니다.

- 최종적으로 연결을 재사용할지 결정하는 쪽은 브라우저다
- 서버는 "가능하게 만들기" 또는 "`421`로 거절하기"를 할 수 있다

### coalescing과 multiplexing은 같은 말인가

아니다.

- multiplexing: 한 connection에서 여러 stream을 동시에 보냄
- coalescing: 서로 다른 origin이 그 같은 connection을 공유할 수 있는지 판단

### HTTP/3면 이 문제가 거의 사라지는가

아니다.

HTTP/3는 TCP HOL 문제를 줄이는 데 강점이 있지만,

- 어떤 origin을 같은 QUIC connection에 실어도 되는지
- `Alt-Svc` endpoint가 실제로 authoritative한지

같은 질문은 그대로 남는다.

---

## 한 줄 정리

HTTP/2와 HTTP/3의 connection coalescing은 "여러 origin이 정말 같은 authoritative edge를 공유하느냐"를 확인한 뒤 연결을 아끼는 최적화다. 인증서, endpoint, 라우팅, `421` 처리까지 함께 맞아야 안전하다.
