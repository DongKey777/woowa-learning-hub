# Spring SSE Buffering / Compression Checklist

> 한 줄 요약: `text/event-stream`은 "서버가 바이트를 썼다"보다 "브라우저가 blank line까지 즉시 받았다"가 더 중요하므로, Nginx/CDN buffering, gzip/brotli, body transform이 있으면 heartbeat cadence와 observability 해석이 쉽게 어긋난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
> - [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
> - [Spring Partial-Response Access Log Interpretation](./spring-partial-response-access-log-interpretation.md)
> - [Cache-Control 실전](../network/cache-control-practical.md)

retrieval-anchor-keywords: spring SSE buffering checklist, spring SSE compression checklist, text/event-stream buffering, event stream buffering, event stream compression, nginx proxy_buffering off, X-Accel-Buffering no, SSE gzip off, SSE brotli off, Content-Encoding gzip text/event-stream, Cache-Control no-transform SSE, CDN response buffering SSE, CDN auto compression SSE, CDN body transform SSE, EventSource burst delivery, SSE heartbeat burst, downstream buffering, event stream coalescing, client-visible flush, last_flush_age drift, SSE observability drift

## 핵심 개념

SSE 운영에서 진짜 계약은 "Spring이 `send()`를 호출했다"가 아니라, **브라우저 `EventSource`가 한 event block의 끝(`\n\n`)을 제때 봤는가**다.

따라서 아래 셋은 모두 "총 바이트는 결국 전달됐지만, SSE로서는 망가진 상태"를 만들 수 있다.

- response buffering: 여러 heartbeat/event를 모아서 한 번에 내려 보낸다
- compression: 바이트 자체는 보존해도 flush cadence를 뭉개거나 downstream delivery 시점을 늦춘다
- response transform: body filter/edge function이 comment line, blank line, body 조각을 건드려 framing 또는 timing을 깨뜨린다

핵심은 origin flush 성공과 browser receive 성공을 같은 사건으로 취급하지 않는 것이다.

## 무엇이 실제로 깨지는가

| 개입 | 어떤 식으로 깨지는가 | 흔한 표면 증상 | observability 왜곡 |
|---|---|---|---|
| Nginx/CDN buffering | 작은 chunk를 모아 더 큰 덩어리로 downstream에 전달 | 15초 heartbeat가 브라우저에서는 60초 burst처럼 보임 | origin `last_flush_age`는 정상인데 client inter-event gap은 큼 |
| gzip / brotli | encoder나 intermediary가 더 큰 block을 기다리거나 재조합 | `Content-Encoding: gzip` 또는 `br`가 붙은 SSE에서 callback이 늦게 몰림 | access log bytes는 꾸준히 늘지만 EventSource 수신 시각은 띄엄띄엄 |
| body transform / edge function | body rewrite, comment strip, newline normalization, body inspection이 stream을 늦추거나 frame을 손상 | comment heartbeat가 사라지거나 parse/reconnect noise가 증가 | app은 200 streaming 성공처럼 보이는데 client는 parse failure 또는 reconnect 반복 |

중요한 점은 compression이 항상 parsing 자체를 깨지 않더라도, **즉시 전달성과 heartbeat 관측**은 쉽게 망가뜨린다는 것이다.
그래서 SSE 경로에서는 "압축이 이득이냐"보다 "압축이 cadence를 바꾸지 않는다는 증거가 있느냐"를 먼저 묻는 편이 안전하다.

## 체크리스트

### 1. App response contract

애플리케이션은 SSE route가 일반 JSON 응답과 다르다는 사실을 header로 먼저 알려야 한다.

- `Content-Type: text/event-stream`
- `Cache-Control: no-cache, no-transform`
- Nginx를 거친다면 필요 시 `X-Accel-Buffering: no`

`no-transform`은 모든 intermediary를 강제로 제어하지는 못하지만, CDN/edge가 body를 임의 변형하지 말아야 한다는 의도를 가장 먼저 드러내는 신호다.

### 2. Nginx buffering

Nginx 앞에서 가장 먼저 볼 질문은 "`proxy_read_timeout`이 충분한가?"보다 "`proxy_buffering`이 꺼져 있는가?"다.

확인 포인트:

- SSE location에서 `proxy_buffering off;`
- upstream이 보낸 `X-Accel-Buffering: no`를 무시하지 않는지
- SSE route만 별도 location으로 분리되어 다른 API 압축/버퍼링 정책을 상속받지 않는지

이 경로가 틀리면 upstream은 15초마다 heartbeat를 읽고도, browser는 몇 개 event를 한꺼번에 받는다.

### 3. gzip / brotli / Content-Encoding

SSE route에서 `Content-Encoding: gzip` 또는 `br`가 보이면 우선 의심부터 하는 편이 낫다.

- origin이 압축하지 않아도 CDN이 자동 압축할 수 있다
- parsing이 살아 있어도 flush cadence는 달라질 수 있다
- comment heartbeat는 payload가 작아서 압축 효율 이득이 거의 없는데, 지연 비용은 크게 치를 수 있다

운영 기본값은 보통 이렇다.

- SSE route는 `gzip off;`
- brotli를 쓰는 환경이면 SSE route는 `brotli off;`
- edge 자동 압축 대상에서 `text/event-stream` 제외

압축을 정말 유지하고 싶다면 "origin flush 시각", "`curl -N` 수신 시각", "브라우저 `EventSource` callback 시각"이 모두 같은 cadence로 움직이는지 직접 증명해야 한다.

### 4. CDN / edge response transformation

CDN은 idle timeout만이 아니라 response mutation 계층이기도 하다.

특히 아래 기능은 SSE route에서 명시적으로 제외하는 편이 안전하다.

- auto compression
- response buffering / large-chunk coalescing
- body rewrite / normalization
- custom edge function이나 WAF body inspection처럼 전체 body 조각을 붙잡는 기능

SSE는 comment line(`:`)와 blank line이 의미를 가지므로, "콘텐츠는 같고 표현만 바꾼다"는 류의 transform도 안전하지 않을 수 있다.

### 5. Observability 기준

SSE 경로에 buffering/compression이 끼면 가장 먼저 망가지는 것은 해석의 기준점이다.

최소한 아래 둘은 같이 남겨야 한다.

- origin 관점: `first_flush_at`, `last_flush_at`, `last_flush_age_ms`
- client/edge 관점: event 수신 timestamp, `Content-Encoding`, `Via`/`X-Cache` 같은 intermediary 힌트

origin은 정상인데 client가 늦게 받는다면 app보다 intermediary가 의심 대상이다.

## 최소 안전 설정 예시

### Spring response header

```java
@GetMapping(path = "/events/orders", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter orderEvents(HttpServletResponse response) {
    response.setHeader(HttpHeaders.CACHE_CONTROL, "no-cache, no-transform");
    response.setHeader("X-Accel-Buffering", "no");

    return new SseEmitter(0L);
}
```

이 예시는 "Nginx가 있으면 buffering 우회 의도가 있다"는 신호를 주는 최소 예시다.
장기 연결 lifetime, heartbeat cadence, replay 복구는 별도 설계가 필요하다.

### Nginx location

```nginx
location /events/ {
    proxy_pass http://spring_upstream;
    proxy_http_version 1.1;

    proxy_buffering off;
    gzip off;

    # brotli module을 쓰는 환경이면 SSE route는 제외한다.
    # brotli off;
}
```

핵심은 모든 route에 같은 전역 최적화를 거는 것이 아니라, **SSE route를 일반 API/HTML과 분리해서 운영 정책을 다르게 주는 것**이다.

## 증상별 해석 매트릭스

| 관측 | 더 의심할 것 | 먼저 할 일 |
|---|---|---|
| origin 로그엔 15초 heartbeat flush가 있는데 브라우저는 45~60초마다 몰려 받음 | buffering 또는 compression | edge를 거친 `curl -N`과 origin 직결 `curl -N` 비교 |
| `disconnect_total`은 늘지만 origin `heartbeat_gap`은 안정적 | downstream transform / client-visible idle | CDN buffering/auto-compression, browser receive gap 확인 |
| SSE route response header에 `Content-Encoding: gzip` | compression path 활성화 | 해당 route 압축 해제 후 cadence 재측정 |
| comment heartbeat 기반 liveness는 깨졌는데 business event는 가끔 도착 | body transform이 comment line을 건드리거나 chunk를 뭉침 | edge function/WAF/body filter 제외 여부 확인 |
| app access log duration은 길고 bytes도 증가하는데 UI는 stale | intermediary가 bytes를 모아 전달 | client-side synthetic probe 추가 |

여기서 핵심 질문은 "서버가 썼는가?"가 아니라 **"누가 마지막 바이트를 실제로 봤는가?"**다.

## 빠른 진단 순서

1. 브라우저와 edge 응답 헤더에서 `Content-Type`, `Content-Encoding`, `Cache-Control`, `Via`, `X-Cache`를 확인한다.
2. origin 직결 `curl -N`과 edge 경유 `curl -N`으로 heartbeat cadence를 비교한다.
3. SSE route에서 `proxy_buffering`, gzip, brotli, body transform을 먼저 끈다.
4. `last_flush_age_ms`와 client inter-event gap이 어디서 갈라지는지 본다.
5. 그다음에야 heartbeat interval과 idle timeout을 다시 조정한다.

buffering/compression 문제가 남아 있는 상태에서 heartbeat만 더 짧게 만드는 것은 대개 write 비용만 늘리고 원인을 숨긴다.

## 꼬리질문

> Q: `send()`와 `flush()`가 성공했는데도 브라우저 이벤트가 늦게 보이는 이유는 무엇인가?
> 의도: origin flush와 client receive 분리 확인
> 핵심: intermediary가 `text/event-stream` bytes를 더 큰 chunk로 모아 downstream에 늦게 내보낼 수 있기 때문이다.

> Q: SSE route에서 `Content-Encoding: gzip`이 왜 즉시 의심 신호인가?
> 의도: compression과 cadence 관계 확인
> 핵심: parsing이 유지돼도 flush cadence와 heartbeat 관측이 쉽게 왜곡되기 때문이다.

> Q: `Cache-Control: no-transform`만 주면 충분한가?
> 의도: header와 실제 edge policy 구분 확인
> 핵심: 의도 표시는 되지만, 실제 buffering/auto-compression/body rewrite를 끄는 설정까지 별도로 맞춰야 한다.

## 한 줄 정리

SSE의 장애 포인트는 "바이트 손실"보다 "바이트가 제때 안 보임"인 경우가 많아서, `text/event-stream` 경로는 buffering, compression, response transform을 일반 응답과 별도 정책으로 다뤄야 한다.
