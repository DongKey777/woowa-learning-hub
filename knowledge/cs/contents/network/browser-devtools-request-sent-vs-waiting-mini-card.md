---
schema_version: 3
title: "Browser DevTools `Request Sent` vs `Waiting` 미니 카드"
concept_id: network/browser-devtools-request-sent-vs-waiting-mini-card
canonical: false
category: network
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 75
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- upload-vs-ttfb-separation
- waiting-is-not-upload
- waterfall-phase-ownership
aliases:
- devtools request sent vs waiting
- request sent confusion
- waiting confusion
- slow upload vs slow response
- request body send time
- upload timing beginner
- waterfall request sent waiting
- why request sent is long
- request sent 뭐예요
- waiting 뭐예요
- 처음 devtools upload
- browser network tab upload delay
- what is request sent
- what is waiting in devtools
symptoms:
- "waterfall에서 `Request Sent`가 길게 보이는데 서버가 느린 건지 업로드가 느린 건지 구분이 안 된다"
- 파일 업로드 API가 오래 걸릴 때 `Waiting`이 문제인지 request body를 보내는 중인지 헷갈린다
- "`POST` 요청이 느린데 DevTools timing 칸을 어떻게 읽어야 upload 지연과 응답 시작 지연을 나눌 수 있는지 막힌다"
intents:
- drill
prerequisites:
- network/devtools-waterfall-primer
- network/request-timing-decomposition
next_docs:
- network/browser-devtools-waiting-vs-content-download-mini-card
- network/request-pending-forever-symptom-router
- network/browser-devtools-waterfall-server-log-timing-bridge
linked_paths:
- contents/network/browser-devtools-waterfall-primer.md
- contents/network/browser-devtools-waterfall-server-log-timing-bridge.md
- contents/network/browser-devtools-waiting-vs-content-download-mini-card.md
- contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md
- contents/spring/spring-multipart-upload-request-pipeline.md
confusable_with:
- network/browser-devtools-waiting-vs-content-download-mini-card
- network/request-pending-forever-symptom-router
- network/devtools-waterfall-primer
forbidden_neighbors:
- contents/network/browser-devtools-waterfall-primer.md
expected_queries:
- "`Request Sent`가 길면 서버가 느린 거야 업로드가 느린 거야?"
- "waterfall에서 `Waiting`이 길다는 건 정확히 어느 구간이야?"
- "파일 업로드 API가 느릴 때 `Request Sent`와 `Waiting`을 어떻게 나눠 읽어?"
- "DevTools timing에서 보내는 시간과 첫 바이트 대기를 구분하는 법을 알려줘"
- "`POST` 요청이 오래 걸릴 때 TTFB 문제인지 upload 문제인지 어떻게 판단해?"
contextual_chunk_prefix: |
  이 문서는 학습자가 DevTools waterfall의 `Request Sent`와 `Waiting`을
  구분해 업로드 지연과 첫 응답 바이트 대기를 섞지 않도록 돕는 network
  drill이다. request sent가 길어요, waiting이 오래 걸려요, upload가
  느린지 서버 응답이 느린지 모르겠어요 같은 자연어 표현이 timing 칸의
  의미와 다음 관찰 포인트로 바로 연결되도록 설계했다.
---
# Browser DevTools `Request Sent` vs `Waiting` 미니 카드

> 한 줄 요약: DevTools waterfall에서 `Request Sent`는 브라우저가 request header/body를 밀어 넣는 시간이고 `Waiting`은 그 뒤 첫 응답 바이트를 기다리는 시간이므로, upload가 느린 장면을 server response 지연으로 읽으면 첫 분기부터 틀어진다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- [Browser DevTools Waterfall -> Server Log Timing 브리지](./browser-devtools-waterfall-server-log-timing-bridge.md)
- [Browser DevTools `Waiting` vs `Content Download` 미니 카드](./browser-devtools-waiting-vs-content-download-mini-card.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- [Spring Multipart Upload Request Pipeline](../spring/spring-multipart-upload-request-pipeline.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: devtools request sent vs waiting, request sent confusion, waiting confusion, slow upload vs slow response, request body send time, upload timing beginner, waterfall request sent waiting, why request sent is long, request sent 뭐예요, waiting 뭐예요, 처음 devtools upload, browser network tab upload delay, what is request sent, what is waiting in devtools

## 핵심 개념

초급자는 `Request Sent`와 `Waiting`을 둘 다 "서버 기다린 시간"처럼 읽기 쉽다. 하지만 질문이 다르다.

- `Request Sent`: 브라우저가 요청을 서버 쪽으로 보내는 시간
- `Waiting`: 요청을 보낸 뒤 첫 응답 바이트가 오기 전까지 기다리는 시간

즉 큰 파일 업로드, 느린 상행선, 큰 request body 때문에 `Request Sent`가 길어질 수 있다. 이때 서버가 느린 게 아니라 **아직 브라우저가 보내는 중**일 수도 있다.

## 한눈에 보기

| 길어진 구간 | 브라우저가 실제로 하는 일 | 초급자 첫 질문 | 먼저 붙일 해석 |
|---|---|---|---|
| `Request Sent` | request header/body 업로드 | 왜 보내는 데 오래 걸리지 | 큰 body, 느린 upload, form-data/multipart 후보 |
| `Waiting` | 첫 응답 바이트 대기 | 왜 응답 시작이 늦지 | app 계산, queue, proxy/upstream wait 후보 |

짧게 외우면 아래 한 줄이다.

```text
request sent = 보내는 시간
waiting = 보내고 난 뒤 첫 바이트를 기다리는 시간
```

## 상세 분해

### `Request Sent`가 길게 보일 때

이 구간은 브라우저가 아직 request를 밀어 넣는 중이다.

- `GET`처럼 body가 거의 없으면 보통 매우 짧다
- `POST`/`PUT` upload, multipart form-data, 큰 JSON body면 길어질 수 있다
- 사용자의 uplink가 느리면 app이 빨리 답할 준비가 돼 있어도 먼저 send 시간이 길어진다

초급자 첫 메모는 "`서버가 아직 느리다`"보다 "`브라우저가 request body를 보내는 중인가?`"가 더 안전하다.

### `Waiting`이 길게 보일 때

이 구간은 request를 보낸 뒤 응답 시작을 기다리는 시간이다.

- 서버가 첫 바이트를 늦게 만들 수 있다
- proxy queue, upstream 호출, DB 대기처럼 app 바깥/안쪽 원인이 섞일 수 있다
- `504`나 slow API처럼 "응답 시작이 늦다"는 질문은 보통 여기서 시작한다

초급자 첫 메모는 "`업로드가 느리다`"가 아니라 "`응답 시작이 늦다`"다.

### 이 비유가 맞는 범위

입문용으로는 `Request Sent = 택배 보내는 시간`, `Waiting = 상대가 문 열기 전까지 기다리는 시간` 정도로 생각해도 된다. 다만 이 비유는 request body가 거의 없는 `GET`과 큰 upload `POST`의 차이를 설명할 때까지만 유용하다. 실제 네트워크에서는 proxy buffering, early reject, HTTP 버전 차이 때문에 서버가 body를 다 받기 전에 판단할 수도 있으니, 비유를 그대로 내부 구현에까지 밀어 붙이면 안 된다.

## 흔한 오해와 함정

- `Request Sent`가 길면 서버 처리 시간이 길다고 단정한다. 먼저 upload/body 크기와 uplink를 본다.
- `Waiting`이 길면 무조건 컨트롤러 실행 시간이라고 생각한다. proxy queue, upstream wait도 섞일 수 있다.
- `POST` upload가 느린데 `Waiting`만 본다. 큰 body 요청은 `Request Sent`부터 확인해야 한다.
- 모든 브라우저가 항상 같은 이름과 같은 정밀도로 보여 준다고 생각한다. DevTools UI는 브라우저/버전에 따라 묶음 표현이 조금 다를 수 있지만, beginner 해석의 큰 축은 같다.

## 실무에서 쓰는 모습

같은 `POST /files`라도 읽는 법이 달라진다.

| 장면 | `Request Sent` | `Waiting` | 초급자 첫 판독 |
|---|---:|---:|---|
| A | `920ms` | `35ms` | upload/body send가 대부분이다. 서버 응답 시작은 오히려 빠른 편일 수 있다 |
| B | `18ms` | `780ms` | 보내는 건 빨랐다. 응답 시작 전 대기가 대부분이다 |

```text
A: [request sent.................][.. waiting ..][download]
B: [request sent][........ waiting ........][download]
```

특히 multipart upload API에서는 A 같은 장면이 흔하다. 이때 "서버 응답이 920ms 느리다"보다 "request body를 보내는 데 920ms가 들었다"가 더 정확하다.

## 더 깊이 가려면

- waterfall 전체 칸을 처음부터 다시 읽고 싶다면 [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- DevTools timing을 proxy/access log 필드와 이어 보고 싶다면 [Browser DevTools Waterfall -> Server Log Timing 브리지](./browser-devtools-waterfall-server-log-timing-bridge.md)
- `Waiting`과 `Content Download`를 또 한 번 분리하고 싶다면 [Browser DevTools `Waiting` vs `Content Download` 미니 카드](./browser-devtools-waiting-vs-content-download-mini-card.md)
- curl의 `TTFB`/`TTLB`와 연결해 더 깊게 보고 싶다면 [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- upload가 Spring 안에서 multipart parsing으로 어떻게 이어지는지 보려면 [Spring Multipart Upload Request Pipeline](../spring/spring-multipart-upload-request-pipeline.md)

## 한 줄 정리

DevTools에서 `Request Sent`는 request body를 보내는 시간이고 `Waiting`은 그 뒤 첫 응답 바이트를 기다리는 시간이므로, upload가 느린 장면을 server response 지연으로 바로 번역하면 안 된다.
