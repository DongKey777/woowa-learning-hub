---
schema_version: 3
title: "Chrome NetLog H3 421 Drilldown: DevTools로 부족할 때 Coalescing Rejection과 Retry Decision 읽기"
concept_id: network/chrome-netlog-h3-421-drilldown
canonical: true
category: network
difficulty: intermediate
doc_role: deep_dive
level: intermediate
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- chrome-netlog-h3
- http421-coalescing-retry
- devtools-netlog-drilldown
aliases:
- chrome netlog h3 421
- netlog coalescing rejection
- netlog retry decision
- h3 421 drilldown
- chrome net-export 421
- quic connection retry netlog
symptoms:
- DevTools에 421 -> 200 두 줄이 보이지만 connection reuse recovery인지 프론트 중복 호출인지 확신이 없다
- Connection ID 열이 없어 H3 retry가 새 connection인지 DevTools만으로 판단하기 어렵다
- 421 뒤 403이나 200이 섞여 coalescing rejection과 app-level response를 한 원인으로 묶는다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/http3-421-observability-primer
- network/browser-devtools-protocol-column-labels-primer
next_docs:
- network/browser-netlog-h3-alt-svc-https-rr-appendix
- network/http2-http3-421-retry-after-wrong-coalescing
- network/http3-cross-origin-reuse-guardrails-primer
- network/h3-stale-alt-svc-421-recovery-primer
linked_paths:
- contents/network/http3-421-observability-primer.md
- contents/network/http2-http3-421-retry-after-wrong-coalescing.md
- contents/network/http3-cross-origin-reuse-guardrails-primer.md
- contents/network/browser-netlog-h3-alt-svc-https-rr-appendix.md
- contents/network/h3-stale-alt-svc-421-recovery-primer.md
- contents/network/browser-devtools-protocol-column-labels-primer.md
confusable_with:
- network/http3-421-observability-primer
- network/browser-netlog-h3-alt-svc-https-rr-appendix
- network/http3-cross-origin-reuse-guardrails-primer
- network/h3-stale-alt-svc-421-recovery-primer
forbidden_neighbors: []
expected_queries:
- "Chrome NetLog로 H3 421 뒤 retry decision을 어떻게 확인해?"
- "DevTools 421 -> 200만으로 coalescing rejection인지 확신이 없을 때 무엇을 봐?"
- "NetLog에서 QUIC session과 retry job 흔적을 beginner도 읽는 순서를 알려줘"
- "421 뒤 403이 보이면 transport recovery와 app response를 어떻게 나눠?"
- "Connection ID가 없는 브라우저에서 H3 새 연결 retry 근거를 어떻게 보강해?"
contextual_chunk_prefix: |
  이 문서는 Chrome NetLog로 HTTP/3 421 Misdirected Request, connection
  coalescing rejection, QUIC session, retry decision을 DevTools trace와
  함께 읽는 intermediate H3 observability deep dive다.
---
# Chrome NetLog H3 421 Drilldown: DevTools로 부족할 때 Coalescing Rejection과 Retry Decision 읽기


> 한 줄 요약: Chrome NetLog H3 421 Drilldown: DevTools로 부족할 때 Coalescing Rejection과 Retry Decision 읽기는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
> DevTools에서 같은 URL 두 줄만으로는 확신이 서지 않을 때, Chrome NetLog를 이용해 "`첫 H3 시도가 어떤 connection 문맥에서 거절됐는지`, `브라우저가 왜 새 connection retry로 넘어갔는지`"를 beginner 관점에서 짧게 확인하는 follow-up primer

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../security/session-cookie-jwt-basics.md)

> 관련 문서:
> - [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
> - [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
> - [Browser NetLog H3 Appendix: Alt-Svc Cache와 HTTPS RR 흔적 확인](./browser-netlog-h3-alt-svc-https-rr-appendix.md)
> - [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
> - [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md)

retrieval-anchor-keywords: chrome netlog h3 421, chrome net-export 421 misdirected request, netlog coalescing rejection, netlog retry decision, h3 421 netlog primer, devtools insufficient 421, same url two rows not enough, quic connection retry netlog, h3 coalescing rejection evidence, browser retry decision trace, net-export wrong connection reuse, chrome h3 retry proof, 421 after wrong coalescing netlog, beginner chrome netlog primer, chrome netlog h3 421 drilldown basics

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [언제 DevTools만으로 부족한가](#언제-devtools만으로-부족한가)
- [Chrome NetLog가 추가로 보여 주는 것](#chrome-netlog가-추가로-보여-주는-것)
- [가장 짧은 capture 순서](#가장-짧은-capture-순서)
- [NetLog에서 어디를 찾나](#netlog에서-어디를-찾나)
- [3단계 판독 순서](#3단계-판독-순서)
- [작은 예시: `421 -> 200`](#작은-예시-421---200)
- [DevTools와 NetLog를 어떻게 연결해 쓰나](#devtools와-netlog를-어떻게-연결해-쓰나)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 잡는 mental model

DevTools는 "`무슨 결과가 보였는가`"를 빨리 보여 준다.
Chrome NetLog는 그 한 단계 뒤에서 "`브라우저가 어떤 내부 연결 판단을 했는가`"를 더 잘 보여 준다.

초급자는 아래 두 문장만 먼저 잡으면 된다.

- DevTools는 `421`과 retry **결과 화면**을 본다.
- NetLog는 그 사이의 **브라우저 결정 흔적**을 본다.

아주 짧게 그리면 이렇다.

```text
기존 shared H3 connection에 요청을 올림
-> 421 Misdirected Request를 읽음
-> 이 origin은 이 connection으로 계속 못 간다고 판단
-> 새 connection 또는 다른 경로로 retry
```

이 문서의 목적은 "`421`이 보였다"를 넘어서 "`왜 브라우저가 retry로 넘어갔는지`"를 NetLog에서 beginner도 안전하게 읽게 만드는 것이다.

---

## 언제 DevTools만으로 부족한가

DevTools만으로 충분한 장면도 많다.
하지만 아래처럼 **같은 URL 두 줄만으로는 설명 책임이 약한 순간**이 있다.

| DevTools에서 본 장면 | 왜 부족한가 | NetLog로 보강할 질문 |
|---|---|---|
| `421 -> 200` 두 줄은 보이는데 `Remote Address`가 같다 | 같은 edge 안에서 새 connection인지 화면만으로 애매하다 | 첫 시도와 retry가 서로 다른 연결 문맥이었는가 |
| `421 -> 403`가 붙어 나온다 | recovery와 app-level 거절을 한 원인으로 섞기 쉽다 | 첫 `421`가 실제로 wrong-connection 거절이었는가 |
| `Connection ID` 열이 없거나 약하다 | 새 연결 근거가 약해진다 | NetLog에 다른 QUIC session/stream 흐름이 남았는가 |
| 같은 URL이 한 줄만 남고 첫 `421`가 사라졌다 | `Preserve log`를 놓쳤으면 브라우저 recovery 순서를 잃는다 | NetLog capture 안에는 첫 실패와 retry가 모두 남았는가 |
| "프런트엔드 중복 호출"과 "브라우저 recovery"가 헷갈린다 | Network 탭 두 줄만으로는 initiator와 transport 판단이 섞인다 | 브라우저가 `421` 이후 transport 레벨에서 retry 결정을 했는가 |

짧게 말하면 이렇다.

- DevTools는 "보인 결과"를 잘 보여 준다.
- NetLog는 "브라우저가 왜 다시 갔는지"를 더 잘 보여 준다.

---

## Chrome NetLog가 추가로 보여 주는 것

Chrome NetLog는 버전마다 정확한 이벤트 이름이 조금 달라질 수 있다.
그래서 초급자는 **정확한 이벤트 이름 암기**보다 아래 세 묶음으로 찾는 편이 안전하다.

| NetLog에서 찾는 묶음 | 초급자 해석 |
|---|---|
| URL request / stream job / transaction 묶음 | 이 요청이 언제 시작됐고 언제 `421` 응답을 읽었는지 |
| QUIC session / socket / connection 묶음 | 첫 시도가 어느 H3 connection 문맥으로 갔는지 |
| retry 뒤 새 job / 새 session / 재연결 묶음 | 브라우저가 다른 연결로 다시 보냈는지 |

즉 NetLog는 아래 두 질문에 답하기 좋다.

1. 첫 `421`가 정말 **기존 shared H3 connection에서 난 거절**이었는가
2. 그 뒤 브라우저가 정말 **새 connection retry 결정을 내렸는가**

이 문서에서는 이것을 각각 `coalescing rejection`과 `retry decision`이라고 부른다.

---

## 가장 짧은 capture 순서

Chrome 계열에서는 보통 `chrome://net-export/`에서 capture를 만든다.

1. 가능하면 새 창이나 실험 조건이 단순한 탭을 준비한다.
2. NetLog recording을 먼저 시작한다.
3. 문제 URL을 한 번 재현한다.
4. recording을 멈추고 export를 저장한다.

핵심은 재현 전에 recording을 켜는 것이다.
그래야 첫 `421`와 그 직후 retry 결정을 한 capture 안에서 함께 볼 수 있다.

작은 습관:

- DevTools에서도 같은 재현을 함께 찍어 둔다.
- 캡처 메모에는 문제 URL, 대략 시각, 기대 패턴(`421 -> 200` 또는 `421 -> 403`)만 적는다.

---

## NetLog에서 어디를 찾나

NetLog viewer나 export 검색에서는 아래처럼 **짧은 검색 축**으로 접근하면 된다.

| 먼저 찾을 것 | 왜 찾나 |
|---|---|
| 문제 URL 또는 host | 관련 request 묶음을 좁히기 위해 |
| `421` | 첫 거절 시점을 찾기 위해 |
| `quic` 또는 `h3` | 첫 시도가 HTTP/3 connection이었는지 보기 위해 |
| `retry`, `restart`, `stream`, `session` 계열 흔적 | 브라우저가 같은 요청을 다른 연결 문맥으로 이어 갔는지 보기 위해 |

정확한 필드명은 버전에 따라 달라도, 초급자는 아래 정도만 읽으면 충분하다.

| 보고 싶은 사실 | 흔히 기대하는 NetLog 감각 |
|---|---|
| 첫 요청이 H3였다 | URL request 묶음 안에 `h3`/QUIC 관련 연결 흔적이 있다 |
| 첫 응답이 `421`였다 | response headers 또는 status 관련 구간에 `421`가 보인다 |
| 첫 시도와 retry가 연결 문맥이 달랐다 | 다른 session/socket/connection 식별 흔적이 이어진다 |
| 브라우저가 재시도했다 | 첫 request 뒤 새 job 또는 restart/retry 흐름이 이어진다 |

여기서 중요한 것은 exact string보다 **순서**다.

```text
첫 request 시작
-> H3/QUIC 연결 문맥
-> 421 응답
-> 새 job 또는 새 연결 문맥
-> 같은 URL retry
```

이 순서가 잡히면 beginner 설명으로는 충분하다.

---

## 3단계 판독 순서

### 1. `421` 이전에 어떤 H3 connection이었는지 본다

먼저 문제 URL request가 어떤 QUIC session이나 connection 문맥에 걸려 있었는지 찾는다.

초급자용 결론:

- 첫 요청이 기존 shared H3 connection 위에 있었으면 coalescing 후보였다.
- 여기서 핵심은 "`h3`였다"보다 "`이미 있던 connection 문맥에 실렸나`"다.

### 2. `421`를 응답으로 읽는 지점을 찾는다

그다음 같은 request 흐름 안에서 `421` 응답을 찾는다.

초급자용 결론:

- 이 지점은 "URL이 틀렸다"보다 "이 connection 문맥은 틀렸다"에 가깝다.
- DevTools의 첫 줄 `421`를 NetLog 안에서도 다시 고정하는 단계다.

### 3. 그 직후 새 연결 또는 새 job으로 이어지는지 본다

마지막으로 `421` 직후 새 request job, 새 QUIC session, 새 socket 같은 연결 전환 흔적이 이어지는지 본다.

초급자용 결론:

- 이 흐름이 보이면 브라우저 retry decision 근거가 강해진다.
- 같은 URL 두 줄이 프런트 중복 호출이 아니라 browser recovery였다는 설명이 쉬워진다.

짧은 판단표:

| NetLog에서 보인 흐름 | 안전한 beginner 결론 |
|---|---|
| 첫 request의 H3 문맥 -> `421` -> 새 connection 문맥 -> 같은 URL 재시도 | wrong-connection recovery 근거가 강하다 |
| `421`는 보이지만 뒤의 새 connection 흔적이 약하다 | recovery 추정은 가능하지만 캡처 범위 부족 가능성을 같이 적는다 |
| `421`보다 app-level `403`/`404`만 강하게 보인다 | 이 문서보다 app-level trace 쪽 문서를 먼저 본다 |

---

## 작은 예시: `421 -> 200`

아래처럼 DevTools에서 보였다고 하자.

| row | Status | Protocol | Remote Address |
|---|---:|---|---|
| 첫 줄 | `421` | `h3` | `198.51.100.30:443` |
| 둘째 줄 | `200` | `h3` | `198.51.100.30:443` |

주소가 같으니 초급자는 여기서 흔들린다.

- "같은 서버면 같은 연결 아닌가?"
- "그럼 retry가 아니라 프런트 중복 호출인가?"

NetLog에서는 아래 순서를 찾는다.

```text
request A -> QUIC session 42 -> response 421
request B -> QUIC session 57 -> response 200
```

이 순서가 보이면 주소가 같아도 설명은 달라진다.

- 같은 edge 주소 안에서 **다른 connection**으로 recovery했을 수 있다.
- 따라서 `Remote Address`만 같다고 retry를 부정하면 안 된다.

---

## DevTools와 NetLog를 어떻게 연결해 쓰나

둘을 경쟁 도구처럼 보지 않는 편이 좋다.

| 도구 | 먼저 답하는 질문 |
|---|---|
| DevTools | 같은 URL이 두 줄이었나, 첫 줄이 `421`였나, 둘째 줄이 `200/403/404`였나 |
| NetLog | 첫 줄이 어떤 H3 connection 문맥이었나, `421` 뒤 실제로 새 연결 retry가 있었나 |

실무적으로는 아래 순서가 가장 안전하다.

1. DevTools에서 `421 -> ...` 패턴을 먼저 잡는다.
2. 화면만으로 애매하면 NetLog에서 `421` 전후의 connection 문맥 변화를 찾는다.
3. 둘째 줄이 `403/404`면 recovery 뒤 app-level 결과라는 설명을 분리한다.

이 순서면 beginner도 "`421` 자체"와 "`그 다음 app 결과`"를 덜 섞게 된다.

---

## 자주 헷갈리는 포인트

### NetLog가 있으면 DevTools는 안 봐도 된다고 생각한다

아니다.

- DevTools는 사용자 눈에 보인 결과 순서를 가장 빨리 보여 준다.
- NetLog는 그 결과를 설명하는 내부 연결 결정을 보강한다.

### 정확한 이벤트 이름 하나만 찾으려 한다

Chrome 버전에 따라 세부 이름은 달라질 수 있다.
초급자는 `URL request -> QUIC/H3 문맥 -> 421 -> 새 연결/재시도` 순서를 찾는 편이 더 안전하다.

### `Remote Address`가 같으면 retry가 아니라고 단정한다

같은 edge 주소 안에서도 새 connection은 열릴 수 있다.
이때는 NetLog의 다른 session/connection 흔적이 더 직접적인 근거다.

### `421 -> 403`를 보면 처음부터 auth 문제였다고 말한다

첫 줄 `421`는 connection 문맥 거절일 수 있고, 둘째 줄 `403`은 recovery 뒤 app/auth 거절일 수 있다.
둘은 분리해서 읽는다.

---

## 한 줄 정리

DevTools가 `421`와 retry의 **겉모습**을 보여 준다면, Chrome NetLog는 그 사이에서 "`첫 H3 connection이 왜 거절됐고`, `브라우저가 왜 새 connection retry로 넘어갔는지`"를 beginner도 따라갈 수 있게 해 주는 후속 증빙 도구다.
