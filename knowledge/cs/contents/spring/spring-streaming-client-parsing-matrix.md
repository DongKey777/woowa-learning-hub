---
schema_version: 3
title: Spring Streaming Client Parsing Matrix
concept_id: spring/streaming-client-parsing-matrix
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- streaming-client-parsing
- fetch-byte-stream
- eventsource-sse
- cli-line-reader
aliases:
- streaming client parsing matrix
- fetch byte stream EventSource SSE
- CLI line reader NDJSON
- streaming flush vs parser framing
- NDJSON plain text SSE parsing
intents:
- comparison
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/spring-responsebodyemitter-media-type-boundaries.md
- contents/spring/spring-mvc-flux-json-vs-ndjson-sse-adaptation.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-sse-buffering-compression-checklist.md
- contents/spring/spring-sse-replay-buffer-last-event-id-recovery-patterns.md
- contents/network/http-response-compression-buffering-streaming-tradeoffs.md
expected_queries:
- Spring streaming endpoint에서 fetch EventSource CLI line reader는 각각 어떤 framing을 기대해?
- 서버 flush 횟수와 클라이언트 parser가 읽는 메시지 경계는 왜 달라?
- NDJSON plain text SSE는 서로 대체 가능한 streaming format이야?
- 브라우저 fetch와 EventSource가 같은 스트리밍 응답을 다르게 읽는 이유는?
contextual_chunk_prefix: |
  이 문서는 Spring streaming endpoint contract를 서버 flush 횟수가 아니라 client parser framing에
  맞춰 설계해야 한다는 점을 설명한다. fetch byte stream, EventSource SSE event block,
  CLI line reader newline-delimited protocol을 matrix로 비교한다.
---
# Spring Streaming Client Parsing Matrix: `fetch`, `EventSource`, CLI Line Readers

> 한 줄 요약: Spring streaming endpoint 계약은 서버의 `flush()` 횟수보다 클라이언트 parser가 이해하는 framing에 맞춰야 하며, browser `fetch`는 byte stream, `EventSource`는 SSE event block, CLI line reader는 newline-delimited line을 전제로 하므로 NDJSON, plain text, SSE를 서로 대체 가능하다고 보면 바로 어긋난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
> - [Spring MVC `Flux` Adaptation: `application/json` vs NDJSON and SSE](./spring-mvc-flux-json-vs-ndjson-sse-adaptation.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)
> - [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
> - [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)

retrieval-anchor-keywords: spring streaming client parsing matrix, fetch stream parser, browser fetch ndjson, fetch readable stream parser, TextDecoderStream ndjson, response.body getReader, response.json not streaming, EventSource text/event-stream, EventSource parser contract, EventSource Last-Event-ID, SSE browser parser, CLI line reader NDJSON, curl -N line reader, readline NDJSON, newline-delimited JSON parser, text/plain streaming parser, SSE blank line framing, fetch SSE parser, SSE line reader mismatch, spring streaming client contract

---

## 핵심 개념

이 문서는 `application/json` 집계 응답이 아니라 **이미 streaming으로 열어 둔 endpoint**를 클라이언트가 어떻게 읽는지에 초점을 둔다.

핵심은 "서버가 언제 `flush()`했는가?"보다 "`이 클라이언트는 어떤 문법을 message 경계로 인정하는가?`"다.

- browser `fetch`: body를 generic byte stream으로 준다. parser는 애플리케이션이 직접 만든다.
- `EventSource`: `text/event-stream` grammar와 reconnect 규칙을 브라우저가 내장해서 처리한다.
- CLI line reader: 한 줄(`\n`)을 record 경계로 보는 경우가 많다.

즉 같은 Spring endpoint라도 intended client parser가 다르면 계약이 달라진다.

## 먼저 보는 매트릭스

| 클라이언트 parser | NDJSON endpoint (`application/x-ndjson`) | plain text endpoint (`text/plain`) | SSE endpoint (`text/event-stream`) | 결론 |
|---|---|---|---|---|
| browser `fetch(response.body)` | 잘 맞는다. line buffer를 두고 줄마다 `JSON.parse`하면 된다 | 잘 맞는다. 부분 텍스트를 그대로 보여 주거나 line policy를 앱이 정하면 된다 | 가능은 하지만 native는 아니다. SSE parser와 reconnect 정책을 직접 구현해야 한다 | `fetch`는 bytes만 주므로 framing ownership이 전부 client에 있다 |
| browser `EventSource` | 맞지 않는다. NDJSON를 SSE로 해석해 주지 않는다 | 맞지 않는다. plain text를 event로 바꿔 주지 않는다 | 가장 잘 맞는다. browser가 event block, `id`, `event`, `retry`, reconnect를 처리한다 | `EventSource`는 SSE 전용 parser라고 보는 편이 정확하다 |
| CLI line reader (`readline`, `while read`, `bufio.Scanner`) | 잘 맞는다. newline이 record 경계다 | 잘 맞는다. line-oriented progress/log에 자연스럽다 | 조건부다. raw line reader는 `data:` line과 blank line을 따로 보므로 SSE-aware adapter가 필요하다 | line reader는 newline grammar에는 강하지만 SSE grammar는 모른다 |

이 표가 말하는 핵심은 단순하다.

- **browser fetch + structured incremental JSON**이면 NDJSON가 제일 자연스럽다
- **browser EventSource widget**이면 SSE가 제일 자연스럽다
- **CLI line reader**면 NDJSON 또는 line-oriented plain text가 제일 자연스럽다

## 먼저 구분할 것: transport chunk와 parse boundary는 다르다

`fetch`든 `curl -N`이든 네트워크 chunk는 record 경계와 일치하지 않을 수 있다.

- NDJSON record 하나가 두 chunk로 나뉠 수 있다
- plain text line 하나가 여러 번 나뉘어 보일 수 있다
- SSE event block 전체가 한 번에 오지 않을 수 있다

그래서 안전한 parser는 항상 buffer를 두고 **media type grammar가 완성될 때까지** 기다린다.

- NDJSON: `\n`
- plain text line mode: `\n`
- SSE: 빈 줄(`\n\n`)로 끝나는 event block

Spring 쪽 `send()`/`flush()` cadence를 그대로 client message 경계로 착각하면 여기서 깨진다.

## 1. Browser `fetch` stream은 bytes first, messages later다

브라우저 `fetch`에서 incremental 처리를 하려면 `response.body`를 읽어야 한다.

- `response.json()`은 body 전체가 끝날 때까지 기다리는 aggregate 경로다
- `response.body`는 `ReadableStream`이므로 chunk를 직접 읽거나 async iteration을 해야 한다
- chunk 경계는 NDJSON line이나 SSE event 경계와 자동으로 맞지 않는다

### NDJSON와 가장 잘 맞는 이유

NDJSON endpoint는 각 record가 독립 JSON value이고 줄바꿈으로 끝난다.
그래서 browser `fetch`에서는 다음 방식이 가장 단순하다.

1. bytes를 text로 decode한다
2. buffer에 붙인다
3. `\n`이 나올 때마다 line을 잘라 `JSON.parse`한다

```js
const response = await fetch("/orders.ndjson");
const reader = response.body
  .pipeThrough(new TextDecoderStream())
  .getReader();

let buffer = "";

for (;;) {
  const { value, done } = await reader.read();
  if (done) break;

  buffer += value;

  let newline;
  while ((newline = buffer.indexOf("\n")) !== -1) {
    const line = buffer.slice(0, newline).trimEnd();
    buffer = buffer.slice(newline + 1);

    if (!line) continue;
    render(JSON.parse(line));
  }
}
```

즉 browser `fetch`가 NDJSON와 잘 맞는 이유는 `fetch`가 똑똑해서가 아니라, **NDJSON가 line parser로 충분한 framing을 제공하기 때문**이다.

### Plain text도 잘 맞지만 record semantics는 앱이 정해야 한다

`text/plain` streaming은 fetch에서 읽기 쉽다.

- token-by-token UI
- progress text
- log tail

다만 plain text는 "부분 텍스트" 자체가 유효할 수 있으므로, line이 꼭 message 단위가 아닐 수도 있다.

- line UX가 필요하면 서버가 `\n` 정책을 명시한다
- token UX가 필요하면 client는 chunk를 그대로 이어 붙여도 된다

즉 plain text는 incremental visibility에는 강하지만, NDJSON처럼 구조화된 record 경계는 약하다.

### SSE도 fetch로 읽을 수는 있지만 parser를 직접 가져와야 한다

`fetch`는 `text/event-stream`을 받아도 EventSource처럼 event를 만들어 주지 않는다.

직접 해야 하는 일은 적지 않다.

- blank line 기준으로 event block을 자르기
- 여러 `data:` line을 하나의 event payload로 합치기
- `id:`, `event:`, `retry:`를 해석하기
- reconnect와 `Last-Event-ID` 재전송을 정책으로 소유하기

그래서 fetch + SSE는 "안 된다"가 아니라 **custom parser가 필요하다**가 정확하다.

이 경로가 맞는 경우는 보통 다음과 같다.

- `EventSource` API surface로 표현하기 어려운 인증/요청 제약이 있다
- 같은 `fetch` 취소/trace 흐름으로 묶고 싶다
- browser가 아니라 service worker, edge runtime, native wrapper 같은 다른 consumer도 같은 parser를 재사용한다

반대로 브라우저 페이지가 단순 SSE consumer라면 `EventSource`가 더 자연스럽다.

## 2. `EventSource`는 SSE parser와 reconnect 정책이 함께 들어 있다

`EventSource`는 generic streaming client가 아니라 **SSE 전용 브라우저 parser**다.

- `text/event-stream` 형식을 기대한다
- event block을 파싱해서 `message` 또는 named event로 넘긴다
- `id:`를 기억해서 reconnect 시 `Last-Event-ID`에 반영한다
- 재연결 간격(`retry:`)과 네트워크 오류 후 reconnect를 브라우저가 관리한다

```js
const source = new EventSource("/orders.sse");

source.addEventListener("order", (event) => {
  render(JSON.parse(event.data));
});

source.onerror = () => {
  console.warn("stream failed or reconnecting");
};
```

### NDJSON/plain text endpoint에 붙이면 안 되는 이유

`EventSource`가 필요한 것은 "바이트가 조금씩 온다"가 아니라 **SSE grammar**다.

NDJSON와 plain text는 이 grammar를 제공하지 않는다.

- NDJSON는 JSON line이지 `data:` field + blank line event block이 아니다
- plain text는 event name, `id`, `retry` 같은 SSE field가 없다

그래서 `EventSource`를 쓸 계획이면 서버 계약도 애초에 `text/event-stream`으로 정하는 편이 맞다.

### `EventSource`를 택할 때 받아들여야 하는 제약

`EventSource` constructor surface는 단순하다.

- URL
- cross-origin credentials 여부

즉 custom method, request body, arbitrary header를 세밀하게 조정하는 generic request API가 아니다.
그런 제약이 문제라면 아래 둘 중 하나를 고른다.

- 인증/세션 모델을 `EventSource`에 맞게 바꾼다
- `fetch` + SSE parser 조합으로 내려간다

## 3. CLI line reader는 newline-delimited contract에 가장 강하다

CLI 쪽 stream consumer는 대개 "한 줄 읽기" primitives를 쓴다.

- shell `while IFS= read -r line`
- Node `readline`
- Go `bufio.Scanner`

이 parser들은 newline이 record 경계일 때 가장 단순하다.

### NDJSON는 CLI 친화적인 structured stream이다

NDJSON 한 줄은 독립 JSON record라서 line reader와 잘 맞는다.

```bash
curl -N http://localhost:8080/orders.ndjson |
while IFS= read -r line; do
  [ -z "$line" ] && continue
  printf '%s\n' "$line"
done
```

이 경로의 장점은 분명하다.

- 줄 하나를 받은 즉시 처리 가능
- JSON object 경계가 명확하다
- 운영자가 사람이 읽거나 후처리 도구로 넘기기 쉽다

### Plain text는 progress/log stream에 잘 맞는다

CLI에서 사람이 즉시 보는 목적이면 plain text가 더 낫다.

- 진행률
- 상태 전이
- tail-like log

다만 structured automation까지 염두에 두면 NDJSON가 더 낫다.
plain text는 사람이 읽기 쉬운 대신 machine parser 계약은 약하다.

### Raw SSE는 line reader로는 반쯤만 보인다

SSE event 하나는 line 하나가 아니라 **여러 field line + 마지막 blank line**이다.

```text
id: 42
event: order
data: {"id":1}

```

raw line reader가 보는 것은 다음이다.

- `id: 42`
- `event: order`
- `data: {"id":1}`
- 빈 줄

즉 line reader는 "event 하나"를 바로 만들지 못한다.
게다가 SSE는 `data:`가 여러 줄일 수도 있어서, blank line까지 모아서 다시 합치는 parser가 필요하다.

따라서 primary consumer가 CLI line reader라면 SSE 하나로 우겨 넣기보다:

- NDJSON endpoint를 따로 두거나
- plain text progress endpoint를 두거나
- 정말 필요할 때만 SSE-aware CLI parser를 둔다

가 더 깔끔하다.

## 서버 계약 선택 가이드

| 주된 consumer | 권장 계약 | 이유 | 피해야 할 오해 |
|---|---|---|---|
| browser fetch로 구조화된 incremental JSON을 읽는다 | NDJSON | line buffer + `JSON.parse`로 충분하다 | `response.json()`도 streaming일 거라고 생각 |
| browser fetch로 진행률/토큰 텍스트를 바로 보여 준다 | plain text | partial text 자체가 의미가 있다 | chunk 1개가 항상 line 1개라고 생각 |
| browser UI가 native SSE parser와 reconnect를 원한다 | SSE | `EventSource`가 event block, `id`, reconnect를 처리한다 | NDJSON를 `EventSource`에 붙여도 비슷할 거라고 생각 |
| browser fetch와 CLI line reader가 같은 endpoint를 공유한다 | NDJSON 또는 line-oriented plain text | 둘 다 newline grammar를 쉽게 공유한다 | SSE 하나로 browser와 CLI를 동시에 만족시킬 수 있다고 생각 |
| SSE semantics는 필요한데 auth/request 제약 때문에 `EventSource`가 안 맞는다 | `fetch` + SSE parser 또는 별도 auth model | parser ownership을 명시적으로 가져가야 한다 | `fetch`가 SSE event를 자동으로 만들어 준다고 생각 |

실무에선 "하나의 endpoint로 모든 client를 만족시키겠다"가 오히려 계약을 흐리게 만드는 경우가 많다.

- browser `EventSource` consumer가 주류면 SSE endpoint를 따로 둔다
- browser fetch + CLI가 함께 쓰면 NDJSON endpoint를 따로 둔다
- 사람이 읽는 진행률이면 plain text endpoint를 따로 둔다

즉 **wire grammar를 client parser 기준으로 분기**하는 편이 운영도 단순하다.

## 실전 시나리오

### 시나리오 1: 프런트엔드가 `EventSource`로 NDJSON endpoint를 붙이려 한다

계약이 틀렸다.

원하는 것이 browser-native reconnect와 event dispatch라면 서버를 SSE로 바꾸고, 원하는 것이 structured incremental JSON이라면 client를 fetch line parser로 바꾸는 편이 맞다.

### 시나리오 2: 같은 stream을 브라우저 dashboard와 운영용 CLI가 같이 본다

SSE metadata가 꼭 필요하지 않다면 NDJSON가 보통 가장 덜 아프다.

- 브라우저 fetch가 line buffer로 읽기 쉽다
- CLI line reader도 그대로 읽기 쉽다
- `event:`/`id:` field를 해석하는 별도 parser가 필요 없다

### 시나리오 3: 인증 때문에 `EventSource`를 쓰기 애매하지만 SSE의 `id`/replay semantics는 필요하다

이 경우는 fetch + SSE parser가 가능하다.
단, 브라우저가 대신 해 주던 reconnect/`Last-Event-ID`/blank-line parsing 책임을 모두 client application이 가져간다는 점을 잊으면 안 된다.

## 꼬리질문

> Q: browser `fetch`는 SSE endpoint를 전혀 못 읽는가?
> 의도: transport 수신 가능성과 parser 지원 구분
> 핵심: 읽을 수는 있지만 SSE parser와 reconnect 정책을 직접 구현해야 한다. native SSE client는 아니다.

> Q: 왜 browser fetch + CLI 조합에선 NDJSON가 자주 더 낫나?
> 의도: newline grammar 공유 이해 확인
> 핵심: 둘 다 newline-delimited record를 다루기 쉬워서 parser를 가장 적게 만든다.

> Q: 언제 plain text가 NDJSON보다 더 낫나?
> 의도: 구조화보다 가시성이 우선인 경우 구분
> 핵심: 사람이 보는 진행률, 토큰, 로그처럼 partial text 자체가 의미일 때다.

## 한 줄 정리

`fetch`는 bytes를, `EventSource`는 SSE를, CLI line reader는 line을 읽는다. Spring streaming endpoint는 서버 구현 타입보다 **클라이언트 parser가 native로 이해하는 framing**에 맞춰 고르는 편이 계약이 덜 꼬인다.
