---
schema_version: 3
title: "Browser DevTools `traceparent` vs `tracestate` 초급 미니 카드"
concept_id: network/browser-devtools-traceparent-vs-tracestate-mini-card
canonical: true
category: network
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- traceparent-tracestate
- tracing-header-first-pass
- devtools-observability-header
aliases:
- traceparent vs tracestate
- devtools traceparent tracestate
- beginner tracing headers
- traceparent first check
- tracestate vendor memo
- distributed tracing header basics
symptoms:
- traceparent와 tracestate가 같이 보이면 둘 다 즉시 완전히 해석해야 한다고 생각한다
- tracestate 값이 길어 보여서 traceparent보다 더 중요한 추적 키로 착각한다
- traceparent가 있으면 app이 직접 응답을 만든 증거라고 오해한다
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- network/http-request-response-headers-basics
next_docs:
- network/browser-devtools-traceid-vs-spanid-mini-card
- network/x-request-id-gateway-app-log-trace-beginner-bridge
- network/browser-devtools-gateway-error-header-clue-card
- spring/observability-micrometer-tracing
linked_paths:
- contents/network/x-request-id-gateway-app-log-trace-beginner-bridge.md
- contents/network/browser-devtools-gateway-error-header-clue-card.md
- contents/network/http-request-response-headers-basics.md
- contents/spring/spring-observability-micrometer-tracing.md
confusable_with:
- network/browser-devtools-traceid-vs-spanid-mini-card
- network/x-request-id-gateway-app-log-trace-beginner-bridge
- network/browser-devtools-gateway-error-header-clue-card
- spring/observability-micrometer-tracing
forbidden_neighbors: []
expected_queries:
- "traceparent와 tracestate가 DevTools에 같이 보이면 무엇부터 봐야 해?"
- "tracestate는 vendor별 메모라서 초급자는 나중에 봐도 되는 이유를 설명해줘"
- "traceparent가 있으면 request ID 대신 traceId 중심 추적이라고 봐도 돼?"
- "502 응답에 traceparent가 있어도 app이 직접 만든 에러라고 단정하면 안 되는 이유가 뭐야?"
- "브라우저 tracing header first pass 규칙을 알려줘"
contextual_chunk_prefix: |
  이 문서는 DevTools request/response headers의 traceparent를 표준 tracing
  propagation key로 먼저 읽고, tracestate는 vendor-specific 메모로 우선순위를
  낮추는 beginner observability header primer다.
---
# Browser DevTools `traceparent` vs `tracestate` 초급 미니 카드

> 한 줄 요약: DevTools에서 `traceparent`와 `tracestate`가 같이 보여도 초급자는 먼저 `traceparent`를 "같은 요청을 다시 찾는 공용 표식"으로 읽고, `tracestate` 값 해석은 보통 뒤로 미뤄도 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)
- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- [network 카테고리 인덱스](./README.md)
- [Spring Observability, Micrometer, Tracing](../spring/spring-observability-micrometer-tracing.md)

retrieval-anchor-keywords: traceparent vs tracestate, devtools traceparent tracestate, tracestate 뭐예요, traceparent 뭐예요, beginner tracing headers, devtools tracing header first pass, what is traceparent, what is tracestate, trace headers 처음, 둘 다 보일 때 뭐 봐요, 왜 tracestate까지 보여요, beginner distributed tracing header, traceparent first check, tracestate ignore first, standards header confusion

## 핵심 개념

처음에는 이렇게만 나누면 된다.

- `traceparent`: 여러 시스템이 **같은 요청 흐름**을 이어 붙일 때 공통으로 보는 표준 표식
- `tracestate`: 그 흐름에 붙는 **vendor별 추가 메모**가 들어갈 수 있는 보조 칸

초급자가 자주 헷갈리는 이유는 둘 다 tracing 헤더라서 "둘 다 해석해야 하나?"라고 느끼기 때문이다.
하지만 DevTools first pass에서는 둘의 우선순위가 다르다.

- 먼저 보는 것: `traceparent`가 있는가
- 보통 나중에 미루는 것: `tracestate` 안의 상세 값

비유로 말하면 `traceparent`는 송장 번호에 가깝고, `tracestate`는 택배사 내부 메모에 가깝다. 다만 실제 tracing 시스템은 더 복잡하므로, `tracestate`를 사람이 항상 직접 읽는다고 일반화하면 안 된다.

## 한눈에 보기

| DevTools에서 보인 장면 | 초급자 첫 해석 | 지금 바로 해도 되는 것 | 보통 지금은 미뤄도 되는 것 |
|---|---|---|---|
| `traceparent`만 있다 | trace 중심 추적이 켜졌을 가능성이 크다 | traceId 검색 흐름을 연다 | `tracestate`가 왜 없는지 깊게 분석 |
| `traceparent`와 `tracestate`가 같이 있다 | 표준 trace + vendor 메타데이터가 같이 전달됐을 수 있다 | `traceparent` 기준으로 같은 요청을 찾는다 | `tracestate` key/value를 줄줄이 해석 |
| `tracestate`만 눈에 띈다 | 헤더 체인 표기가 어색하거나 일부 도구가 일부만 보여 준 장면일 수 있다 | raw headers, tracing UI, gateway/app 로그를 더 본다 | `tracestate`만으로 trace를 확정 |

짧게 외우면 이렇다.

```text
traceparent = 먼저 본다
tracestate = 보조 메모로 둔다
```

## 초급자 first pass 규칙

처음 보는 사람은 `traceparent` 전체 스펙을 외우기보다 아래 3가지만 보면 충분하다.

1. 요청 헤더에 `traceparent`가 있는가
2. 로그나 tracing UI에서 `traceId`로 이어 찾을 수 있는가
3. status, URL, 시간과 함께 같은 요청을 묶을 수 있는가

아래 같은 장면이면 초급자 메모는 이것이면 충분하다.

```http
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: acme=edge-us,rojo=sample
```

- "`traceparent`가 있으니 trace 중심 추적 구성이 보인다"
- "`tracestate`는 vendor 메모일 수 있으니 지금은 해석 우선순위를 낮춘다"

여기서 중요한 점은 `traceparent` 전체 문자열을 외우는 것이 아니라, 많은 팀이 그 안의 `traceId` 또는 연결된 tracing 필드를 검색 키로 쓴다는 흐름을 아는 것이다.

## 흔한 오해와 함정

- `tracestate`가 더 길어 보여서 더 중요한 헤더라고 생각한다. 초급자 first pass에서는 보통 아니다.
- `traceparent`와 `tracestate`가 같이 보이면 둘 다 의미를 완전히 해석해야 한다고 느낀다. 대부분의 초급 장애 판독에서는 `traceparent`부터면 충분하다.
- `tracestate` 값이 이해되지 않으면 tracing이 깨졌다고 단정한다. vendor별 형식이 달라 사람이 바로 읽기 어려울 수 있다.
- `traceparent`가 있으면 app이 반드시 직접 에러를 만들었다고 생각한다. gateway, proxy, app 어디서든 trace 헤더를 전달할 수 있다.
- `tracestate`만 보인다고 바로 표준 위반이라고 단정한다. DevTools 표시 방식, 중간 hop, 로그 가공 방식에 따라 관찰이 불완전할 수 있으니 raw header나 tracing UI를 먼저 대조한다.

## 실무에서 쓰는 모습

| 지금 DevTools에서 본 것 | 초급자 첫 문장 | 다음 한 걸음 |
|---|---|---|
| `500` + `traceparent`만 있음 | "request ID 대신 traceId 중심 추적일 수 있다" | tracing UI 또는 app/gateway 로그의 `traceId` 필드를 찾기 |
| `500` + `traceparent` + `tracestate` | "표준 trace 헤더와 vendor 메타데이터가 같이 있다" | `traceparent` 기준으로 같은 요청을 찾고, `tracestate` 해석은 필요할 때만 팀 문서 확인 |
| `502` + `Server`/`Via` + `traceparent` | "proxy/gateway 문맥에서도 trace가 이어졌을 수 있다" | owner 판독은 `Server`/`Via`, 추적 키는 `traceparent`로 분리해서 본다 |

안전한 30초 순서는 이렇다.

1. `Status`, URL, 시간대를 먼저 적는다.
2. tracing 헤더가 있으면 `traceparent`부터 본다.
3. 로그나 tracing UI 검색 키가 `traceId`인지 확인한다.
4. `tracestate`는 팀이 vendor-specific 디버깅을 요구할 때만 더 깊게 본다.

## 더 깊이 가려면

- `traceparent`가 `X-Request-Id`와 어떤 관계인지 먼저 붙여 보고 싶으면 [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)
- DevTools 첫 헤더 분기에서 `Server`/`Via`와 같이 읽고 싶으면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- tracing 헤더보다 header 자체가 낯설면 [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- Spring 기준으로 log, metric, trace 연결이 어떻게 보이는지 보려면 [Spring Observability, Micrometer, Tracing](../spring/spring-observability-micrometer-tracing.md)

## 한 줄 정리

DevTools에서 `traceparent`와 `tracestate`가 같이 보여도 초급자는 먼저 `traceparent`로 같은 요청을 다시 찾고, `tracestate` 상세 해석은 보통 나중으로 미루는 편이 가장 안전하다.
