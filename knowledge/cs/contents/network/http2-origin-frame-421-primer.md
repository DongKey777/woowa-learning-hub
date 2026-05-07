---
schema_version: 3
title: "HTTP/2 ORIGIN Frame and 421 Primer"
concept_id: network/http2-origin-frame-421-primer
canonical: true
category: network
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- http2-origin-frame
- http-421
- connection-coalescing
aliases:
- HTTP/2 ORIGIN frame
- Origin Set
- 421 Misdirected Request
- cross-origin connection reuse
- wrong connection retry
- coalescing beginner
- h3 no origin frame
symptoms:
- 421을 403/404 같은 권한/존재 문제로만 해석한다
- ORIGIN frame이 certificate 검증을 대신한다고 오해한다
- cross-origin coalescing에서 미리 좁히는 ORIGIN과 사후 거절 421을 구분하지 못한다
- HTTP/3에도 같은 ORIGIN frame guardrail이 있다고 생각한다
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- network/http2-http3-connection-reuse-coalescing
- network/http1-http2-http3-beginner-comparison
next_docs:
- network/wildcard-cert-routing-boundary-primer
- network/http-421-troubleshooting-trace-examples
- network/http3-cross-origin-reuse-guardrails-primer
- network/http2-http3-421-retry-after-wrong-coalescing
linked_paths:
- contents/network/http2-http3-connection-reuse-coalescing.md
- contents/network/wildcard-cert-routing-boundary-primer.md
- contents/network/http-421-troubleshooting-trace-examples.md
- contents/network/http3-cross-origin-reuse-guardrails-primer.md
- contents/network/http2-http3-421-retry-after-wrong-coalescing.md
- contents/network/browser-http-version-selection-alpn-alt-svc-fallback.md
- contents/network/http1-http2-http3-beginner-comparison.md
- contents/network/sni-routing-mismatch-hostname-failure.md
confusable_with:
- network/http2-http3-connection-reuse-coalescing
- network/http3-cross-origin-reuse-guardrails-primer
- network/http-421-troubleshooting-trace-examples
- network/http-421-non-idempotent-retry-guardrail-primer
forbidden_neighbors: []
expected_queries:
- "HTTP/2 ORIGIN frame과 421 Misdirected Request를 초보자에게 설명해줘"
- "ORIGIN frame은 connection coalescing 범위를 어떻게 좁혀?"
- "421은 서버 고장이나 권한 문제가 아니라 wrong connection 신호일 수 있는 이유는?"
- "HTTP/2 ORIGIN frame과 HTTP/3 reuse guardrail 차이는?"
- "잘못 coalescing된 요청을 브라우저가 다른 connection으로 retry하는 흐름은?"
contextual_chunk_prefix: |
  이 문서는 HTTP/2 ORIGIN frame, Origin Set, 421 Misdirected Request,
  cross-origin connection coalescing의 미리 좁히기와 사후 recovery를 설명하는
  beginner primer다.
---
# HTTP/2 ORIGIN Frame와 421 입문

> 한 줄 요약: `ORIGIN`은 "이 HTTP/2 connection을 어디까지 같이 써도 되는지"를 미리 좁히고, `421`은 잘못 탄 요청을 다른 connection으로 돌려보내는 신호다.
>
> 문서 역할: 이 문서는 network 카테고리 안에서 ORIGIN frame과 `421 Misdirected Request`를 초보자가 "연결 재사용 범위 제한" 관점으로 먼저 이해하게 돕는 **beginner follow-up primer**다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../security/session-cookie-jwt-basics.md)

> 이 문서는 ORIGIN/`421` 주제의 **beginner-safe follow-up entry**다. `421`을 상태 코드 암기 문제로 보지 말고, 먼저 "잘못된 connection을 바로잡는 문서"로 읽으면 안전하다.
>
> | 지금 상태 | 먼저 읽을 문서 | 이 문서로 돌아오는 타이밍 |
> |---|---|---|
> | `connection coalescing` 자체가 아직 낯설다 | [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md) | "`같이 쓸 수는 있다`는 건 알겠는데 어디까지 허용하지?"가 궁금해졌을 때 |
> | HTTP 버전 큰 그림부터 다시 잡아야 한다 | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) | H2/H3 차이 감각을 다시 잡은 뒤 |
> | "`421`이 403/404와 왜 다른지"가 궁금하다 | 이 문서 | connection 문맥과 retry 흐름을 같이 보려는 지금 |

> 관련 문서:
> - [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
> - [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
> - [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
> - [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) (selection follow-up primer)
> - [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) (main comparison primer)
> - [SNI Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)

retrieval-anchor-keywords: http2 origin frame, 421 misdirected request, origin set basics, cross origin connection reuse, wrong connection retry, coalescing beginner, h2 connection reuse why, 421 what is, origin frame what is, 언제 421, 왜 421, 처음 coalescing, 헷갈리는 421, h3 no origin frame

<details>
<summary>Table of Contents</summary>

- [먼저 보는 20초 입장권](#먼저-보는-20초-입장권)
- [왜 이 follow-up이 필요한가](#왜-이-follow-up이-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [ORIGIN과 421를 한 표로 보면](#origin과-421를-한-표로-보면)
- [ORIGIN frame은 무엇을 하냐](#origin-frame은-무엇을-하냐)
- [421은 언제 쓰냐](#421은-언제-쓰냐)
- [함께 보는 타임라인](#함께-보는-타임라인)
- [작은 예시](#작은-예시)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 보는 20초 입장권

이 문서는 아래 두 문장을 먼저 잡고 읽으면 된다.

- `ORIGIN`은 "이 H2 connection을 어디까지 같이 써도 되는지 미리 좁히는 힌트"
- `421`은 "그 선을 넘은 요청은 다른 connection으로 다시 와라"라는 거절 신호

| 지금 질문 | 먼저 떠올릴 한 줄 | 다음 이동 |
|---|---|---|
| "`421`이 나오면 서버가 고장난 건가?" | 아니다. 보통은 wrong connection 신호다 | 상세 복구는 [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) |
| "`ORIGIN`은 인증서를 대신하나?" | 아니다. cert를 대체하지 않고 재사용 범위를 좁힌다 | 본문 `ORIGIN frame은 무엇을 하냐`로 이어 읽기 |
| "H3에도 ORIGIN frame이 있나?" | 없다. H3는 다른 guardrail을 본다 | [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) |

## 왜 이 follow-up이 필요한가

[HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)은 "여러 origin이 왜 한 connection을 같이 쓸 수 있나"를 설명한다.

그다음 단계에서 초보자가 자주 막히는 질문은 이것이다.

- 브라우저가 공유 후보라고 판단한 뒤에도, 서버는 어디까지 허용할 수 있나?
- 인증서는 넓게 잡혀 있는데 일부 origin만 같은 connection으로 받고 싶으면 어떻게 하나?
- 잘못 공유된 요청이 실제로 들어오면 무엇으로 거절하나?

이때 같이 보면 좋은 조합이 아래 둘이다.

- `ORIGIN` frame: "이 H2 connection은 이 origin들까지만 같이 써도 된다"
- `421 Misdirected Request`: "방금 온 이 요청은 이 connection으로 받지 않겠다"

### Retrieval Anchors

- `HTTP/2 ORIGIN frame`
- `Origin Set`
- `421 Misdirected Request`
- `cross-origin connection reuse`
- `misdirected request retry`
- `connection context mismatch`

---

## 먼저 잡는 mental model

간단히 이렇게 생각하면 된다.

- 브라우저의 coalescing 판단은 "이 문을 같이 써도 될 것 같나?"를 보는 단계다
- `ORIGIN` frame은 서버가 "그래도 이 문은 `www`와 `static`까지만 써라"라고 미리 선을 긋는 단계다
- `421`은 그 선을 넘은 요청이 왔을 때 "그 요청은 다른 문으로 다시 와라"라고 돌려보내는 단계다

짧게 말하면:

- `ORIGIN`은 **미리 좁히기**
- `421`은 **들어온 뒤 거절하기**

즉 둘 다 cross-origin connection reuse를 막연히 넓히기보다, **안전한 범위로 제한하는 장치**다.

---

## ORIGIN과 421를 한 표로 보면

| 항목 | `ORIGIN` frame | `421 Misdirected Request` |
|---|---|---|
| 형태 | HTTP/2 frame | HTTP 응답 status code |
| 타이밍 | 요청이 잘못 가기 전에 미리 | 잘못 간 요청이 들어온 뒤 |
| 역할 | 이 connection의 origin set을 명시해 재사용 범위를 제한 | 이 요청은 이 connection 문맥에서 처리하지 않겠다고 거절 |
| 감각 | "이 문은 A, B만 받아" | "C 요청은 다른 문으로 다시 와" |
| 결과 | 브라우저가 coalescing 범위를 더 보수적으로 잡을 수 있음 | 브라우저가 다른 connection으로 retry할 근거를 얻음 |

둘 중 하나만 있어도 도움이 되지만, 같이 있으면 더 깔끔하다.

- `ORIGIN`이 있으면 잘못된 재사용을 줄일 수 있다
- 그래도 잘못 온 요청이 있으면 `421`이 마지막 안전장치가 된다

---

## ORIGIN frame은 무엇을 하냐

`ORIGIN` frame은 **HTTP/2 connection 단위의 힌트**다.

초보자 감각으로는 **connection 전용 allow-list**라고 생각하면 된다.

### 왜 필요하나

아래처럼 "인증서는 넓은데, connection 공유는 더 좁게 하고 싶다"는 장면에서 쓴다.

- 인증서가 여러 hostname을 함께 커버한다
- 브라우저는 "같은 connection을 같이 써도 되나?"를 검토한다
- 서버는 일부 origin만 같은 connection으로 받고 싶다

이때 `ORIGIN` frame이 있으면 서버는 "cert 범위와 별개로, 이 connection 재사용은 여기까지만"이라고 알려 줄 수 있다.

### 작은 예로 보면

인증서가 `www`, `static`, `admin`을 모두 커버해도, 실제로는 `www`와 `static`만 같이 받고 싶을 수 있다.

이때 서버는 `ORIGIN` frame으로 `www`, `static`만 광고해서 브라우저가 그 connection을 `admin`까지 확장하지 않도록 유도할 수 있다.

### 꼭 같이 기억할 점

- `ORIGIN`은 **HTTP/2 전용** frame이다
- frame을 이해하지 못하는 클라이언트는 그냥 무시할 수 있다
- 인증서 검증을 대체하지는 않는다
- wildcard certificate를 쓰더라도 `ORIGIN`은 실제 origin 목록을 적는 쪽으로 이해하면 된다

더 깊은 vendor별 동작이나 예외 패턴은 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)와 [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)로 넘겨서 보는 편이 안전하다.

---

## 421은 언제 쓰냐

`421 Misdirected Request`는 "리소스가 없다"가 아니라 **이 요청이 잘못된 connection으로 왔다**에 가깝다.

초급자 기준으로는 "`421`을 보면 앱 로직보다 connection 문맥부터 다시 본다" 정도로 잡으면 된다.

서버가 "이 요청은 지금 connection 문맥으로 처리하면 안 된다"고 판단할 때 쓴다.

즉 초보자 감각으로는:

- `404`: 맞는 서버에 갔는데 그 리소스가 없다
- `403`: 맞는 서버에 갔는데 app 권한/정책으로 거절당했다
- `421`: 아예 **이 connection으로 오면 안 되는 요청**이었다

| status | 뜻 | 다음 동작 감각 |
|---|---|---|
| `404` | 리소스를 못 찾음 | 다른 connection보다 URL/자원 확인 |
| `403` | 권한/정책으로 거절 | 인증/인가 확인 |
| `421` | connection 또는 authority 문맥이 잘못됨 | 다른 connection으로 다시 시도 |

특히 coalescing 맥락에서는 아래처럼 자주 보인다.

- 브라우저가 `admin.example.com` 요청도 기존 H2 connection에 태움
- 서버는 "이 connection은 `admin`용이 아니다"라고 판단함
- 서버가 `421`을 돌려줌
- 클라이언트는 `admin` 전용 새 connection을 열어 다시 보냄

이 점이 중요하다.

- `421`은 **wrong connection** 신호다
- 그래서 클라이언트는 다른 connection으로 retry할 수 있다
- 초보자 1차 판단에서는 서버 장애보다 "connection을 잘못 공유했나?"를 먼저 떠올리는 편이 안전하다

---

## 함께 보는 타임라인

### 타임라인 1: 서버가 미리 범위를 좁힌다

1. 브라우저가 `https://www.example.com`으로 H2 connection을 연다.
2. 인증서는 `www`, `static`, `admin`을 모두 커버한다.
3. 서버는 초반에 `ORIGIN` frame으로 `https://www.example.com`, `https://static.example.com`만 광고한다.
4. 브라우저는 이 connection을 `www`와 `static`에는 재사용할 수 있다고 본다.
5. `admin`은 같은 cert라도 이 connection reuse 후보에서 빠진다.

핵심:

- `ORIGIN`은 coalescing을 "무조건 넓혀라"가 아니라
- **어디까지 허용할지 연결별로 다시 그리게 하는 힌트**다

### 타임라인 2: 그래도 잘못 온 요청은 `421`로 막는다

1. 어떤 이유로 `https://admin.example.com` 요청이 같은 connection으로 들어온다.
2. 요청의 `:authority`는 `admin.example.com`이다.
3. 서버는 이 authority가 현재 connection 범위와 맞지 않는다고 본다.
4. 서버는 `421 Misdirected Request`를 보낸다.
5. 클라이언트는 "이 origin은 이 connection에 싣지 말아야겠다"라고 배우고, 별도 connection으로 다시 시도한다.

즉 실제 운영에서는:

- `ORIGIN`이 **사전 가드레일**
- `421`이 **사후 복구 신호**

라고 보면 된다.

---

## 작은 예시

### 예시 1: `www`와 `static`만 같이 쓰고 싶다

- 인증서: `www`, `static`, `admin` 모두 포함
- edge/LB routing: `www`, `static`은 같은 front door
- `admin`은 다른 보안 영역

좋은 설정:

- H2 connection에는 `ORIGIN` frame으로 `www`, `static`만 광고
- `admin` 요청이 잘못 오면 `421`

결과:

- 브라우저는 재사용 가능한 범위를 더 빨리 좁힌다
- 잘못 공유된 요청도 안전하게 분리된다

### 예시 2: ORIGIN이 없는 경우

- 브라우저는 cert, endpoint, 기존 규칙만 보고 coalescing 여부를 판단한다
- 이 판단이 보수적이면 새 connection을 열고, 공격적이면 잘못 공유할 수도 있다

결과:

- `421`이 더 자주 마지막 복구 장치 역할을 하게 된다

H3까지 바로 넓히면 초보자 기준으로는 축이 늘어난다. 이 문서에서는 "`ORIGIN`은 H2, `421`은 wrong connection 거절"까지만 먼저 잡고, H3 분기는 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)로 넘기는 편이 안전하다.

---

## 자주 헷갈리는 포인트

### 같은 certificate면 ORIGIN이 필요 없나

아니다.

- certificate는 "이 이름으로 인증할 수 있나"에 가깝다
- `ORIGIN`은 "그래서 이 connection을 어디까지 공유할래?"를 더 좁히는 장치다

### ORIGIN이 있으면 브라우저가 반드시 connection을 공유하나

아니다.

- 최종적으로 reuse/coalescing을 할지 결정하는 것은 여전히 client다
- `ORIGIN`은 허용 범위를 알려 주는 힌트이지 강제 스위치가 아니다

### 421은 그냥 일시적인 서버 에러인가

아니다.

- `500`류처럼 "서버가 망가졌다"보다
- "이 요청은 다른 connection으로 보내라"에 더 가깝다
- 그래서 beginner triage에서는 app 권한/리소스 오류보다 connection 문맥을 먼저 보는 편이 안전하다

### ORIGIN은 일반 HTTP header인가

아니다.

- HTTP/2 frame이다
- hop-by-hop 성격이라 intermediary가 그대로 전달하는 일반 앱 header처럼 생각하면 안 된다

### H3에도 ORIGIN frame이 똑같이 있나

이 beginner 문서 기준으로는 아니라고 잡는 편이 좋다.

- H2에서는 `ORIGIN` frame을 같이 볼 수 있다
- H3 세부 guardrail은 별도 문서로 넘긴다
- H3에서 무엇을 기준으로 판단하는지는 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)로 이어서 본다

## 다음에 어디로 가면 좋나

- "`421`이 `403`/`404`와 로그에서 어떻게 다르게 보이죠?"가 궁금하면 [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- "`여러 origin이 왜 같은 connection을 탈 수 있죠?`"가 아직 헷갈리면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- "H3에서는 무엇으로 guardrail을 거나요?"가 다음 질문이면 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)

---

## 한 줄 정리

HTTP/2에서 `ORIGIN` frame은 "이 connection을 어디까지 같이 써도 되는지"를 미리 좁히는 힌트이고, `421 Misdirected Request`는 그 선을 넘은 cross-origin reuse를 다른 connection으로 되돌리는 거절 신호다.
