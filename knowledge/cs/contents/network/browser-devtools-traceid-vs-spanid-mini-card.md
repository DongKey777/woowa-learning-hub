# Browser DevTools `traceId` vs `spanId` 초급 미니 카드

> 한 줄 요약: DevTools 옆에서 로그나 tracing 화면을 같이 볼 때 `traceId`는 "같은 요청 흐름 전체를 다시 찾는 키"이고, `spanId`는 "그 흐름 안의 한 작업 조각"이라서 초급자는 보통 `traceId`부터 검색하는 편이 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `traceparent` vs `tracestate` 초급 미니 카드](./browser-devtools-traceparent-vs-tracestate-mini-card.md)
- [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)
- [Browser DevTools Waterfall 기초](./browser-devtools-waterfall-primer.md)
- [Spring Observability, Micrometer, Tracing](../spring/spring-observability-micrometer-tracing.md)
- [Distributed Tracing Pipeline Design](../system-design/distributed-tracing-pipeline-design.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: traceid vs spanid, devtools traceid spanid, spanid 뭐예요, traceid 뭐예요, tracing screen first search, log trace id first, trace id span id difference, distributed tracing basics, traceparent traceid spanid, 처음 tracing 화면, 왜 spanid로 안 찾아져요, what is span id, what is trace id, beginner observability ids, devtools adjacent tracing

## 핵심 개념

처음에는 이렇게만 나누면 된다.

- `traceId`: 요청이 여러 서비스와 여러 span을 지나도 **전체 흐름을 묶는 공통 번호**
- `spanId`: 그 흐름 안에서 **지금 보고 있는 한 작업 조각의 번호**

초급자가 자주 막히는 장면은 이렇다.

- DevTools에서는 `traceparent`만 보였다
- 로그나 tracing UI에서는 `traceId`, `spanId`가 같이 보였다
- 그래서 `spanId`를 먼저 복붙했는데 원하는 요청이 잘 안 모였다

비유로 말하면 `traceId`는 드라마 시즌 이름이고 `spanId`는 한 에피소드 번호에 가깝다. 다만 실제 tracing은 fan-out, async 작업, 재시도 때문에 더 복잡하므로 "span 하나 = 요청 전체"로 일반화하면 안 된다.

## 한눈에 보기

| 지금 보이는 필드 | 초급자 첫 해석 | 먼저 찾을 곳 | 지금 바로 단정하면 안 되는 것 |
|---|---|---|---|
| `traceId=4bf9...` | 같은 요청 흐름 전체를 다시 모을 키일 가능성이 크다 | tracing UI 전체 검색, app/gateway 로그 | 이 값이 반드시 브라우저 헤더에 그대로 보였을 것 |
| `spanId=00f0...` | 한 hop 또는 한 작업 조각을 가리킬 가능성이 크다 | 이미 찾은 trace 안에서 세부 span 확인 | 이 값만으로 요청 전체가 다 모일 것 |
| `traceparent: 00-4bf9...-00f0...-01` | 앞 32hex는 trace 흐름, 그다음 16hex는 현재 span 조각일 수 있다 | 보통 `traceId=4bf9...`부터 찾기 | `spanId`만 먼저 검색 |

짧게 외우면 이렇다.

```text
traceId = 요청 묶음 전체
spanId = 그 안의 한 조각
먼저 검색 = traceId
```

## DevTools 옆에서 읽는 순서

브라우저 DevTools는 보통 `traceId`와 `spanId`를 각각 친절한 컬럼으로 보여 주기보다, `traceparent` 같은 헤더를 보여 주거나 아예 tracing 필드를 직접 안 보여 줄 수 있다. 이 부분은 브라우저 도구와 tracing 제품 구성에 따라 다르다.

초급자 first pass는 아래 순서면 충분하다.

1. DevTools에서 URL, status, 시간을 적는다.
2. `traceparent`가 보이면 앞쪽 `traceId` 후보를 먼저 본다.
3. 로그나 tracing UI에서 `traceId`로 전체 요청 흐름을 찾는다.
4. 그 다음에 필요한 span 하나를 열 때 `spanId`를 본다.

즉 `spanId`는 "처음 찾는 키"보다 "찾은 뒤에 확대하는 키"에 가깝다.

## 흔한 오해와 함정

- `spanId`가 더 짧아서 검색하기 쉬워 보이니 먼저 써야 한다고 생각한다. 보통은 너무 좁아서 요청 전체를 놓치기 쉽다.
- `traceId`와 `spanId`가 항상 DevTools에 둘 다 그대로 나온다고 기대한다. 실제로는 `traceparent`만 보이거나, vendor UI에서만 분리 표시될 수 있다.
- 로그 한 줄에 `spanId`가 찍혔으니 그 값으로 모든 서비스 로그를 찾을 수 있다고 생각한다. 다른 서비스 hop은 다른 `spanId`를 가질 수 있다.
- `traceId` 하나면 언제나 모든 로그가 다 연결된다고 생각한다. 샘플링, 로그 포맷 누락, 비동기 컨텍스트 전파 누락이 있으면 일부만 보일 수 있다.
- `spanId`를 찾지 못하면 tracing이 깨졌다고 단정한다. 제품 UI가 span 세부 식별자를 숨기거나 다른 이름으로 보여 줄 수도 있다.

## 실무에서 쓰는 모습

아래 장면이면 초급자는 `traceId`부터 시작하면 된다.

```http
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

| 필드 | 이 장면에서 읽는 법 | 초급자 다음 행동 |
|---|---|---|
| `4bf92f3577b34da6a3ce929d0e0e4736` | trace 전체 묶음 후보 | tracing UI나 로그에서 `traceId` 검색 |
| `00f067aa0ba902b7` | 현재 request hop의 span 후보 | trace를 찾은 뒤 해당 span 세부 확인 |

로그 화면에서는 보통 이렇게 만난다.

| 관측 위치 | 보이는 값 | 먼저 할 말 |
|---|---|---|
| gateway log | `traceId=4bf9... spanId=00aa...` | "gateway도 같은 trace 안에 있다" |
| app log | `traceId=4bf9... spanId=91cd...` | "app hop은 같은 trace지만 span은 다를 수 있다" |
| tracing UI | `traceId=4bf9...` 아래 여러 span | "먼저 trace를 열고, 느린 span 또는 에러 span을 고른다" |

핵심은 "`왜 spanId로 먼저 안 찾지?`"에 대한 답이 간단하다는 점이다. 같은 요청 안에서도 hop마다 span이 갈라지기 쉬워서, 초급자 첫 검색 키로는 `traceId`가 더 안정적이다.

## 더 깊이 가려면

- DevTools에서 `traceparent` 자체를 먼저 읽는 법이 필요하면 [Browser DevTools `traceparent` vs `tracestate` 초급 미니 카드](./browser-devtools-traceparent-vs-tracestate-mini-card.md)
- `X-Request-Id`, `traceparent`, `traceId`의 역할 차이를 한 번에 붙여 보려면 [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)
- waterfall 시간선과 tracing 시간을 같이 보는 감각을 붙이려면 [Browser DevTools Waterfall 기초](./browser-devtools-waterfall-primer.md)
- Spring 기준 로그, 메트릭, trace 연결을 보려면 [Spring Observability, Micrometer, Tracing](../spring/spring-observability-micrometer-tracing.md)
- span tree와 parent span 관계까지 들어가려면 [Distributed Tracing Pipeline Design](../system-design/distributed-tracing-pipeline-design.md)

## 한 줄 정리

DevTools 옆에서 `traceId`와 `spanId`가 같이 보이면 초급자는 보통 `traceId`로 같은 요청 흐름 전체를 먼저 찾고, `spanId`는 그다음 세부 hop을 확대할 때 쓰는 편이 가장 덜 헷갈린다.
