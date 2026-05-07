---
schema_version: 3
title: SSE 이벤트가 한꺼번에 와요 원인 라우터
concept_id: spring/sse-events-arrive-in-bursts-cause-router
canonical: false
category: spring
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- sse-buffering-drift
- sse-heartbeat-timeout
- sse-replay-gap
aliases:
- sse 알림이 몰아서 옴
- spring sse burst delivery
- sse heartbeat 보냈는데 늦게 옴
- eventsource 실시간이 아니라 한꺼번에 옴
- sse 브라우저에서만 늦게 보임
- text event stream buffering symptom
symptoms:
- SSE 알림이 끊긴 것처럼 보이다가 몇 개가 한꺼번에 도착해요
- 서버 로그에는 heartbeat를 보냈는데 브라우저 화면은 30초쯤 멈췄다가 몰아서 갱신돼요
- origin에 직접 붙으면 실시간인데 ALB나 Nginx 뒤에서는 EventSource callback이 늦게 와요
- 새로고침 뒤에는 최신 이벤트를 놓치거나 중복으로 다시 받아서 더 헷갈려요
intents:
- symptom
- troubleshooting
prerequisites:
- spring/streamingresponsebody-responsebodyemitter-sse-commit-lifecycle
next_docs:
- spring/sse-buffering-compression-checklist
- spring/sse-proxy-idle-timeout-matrix
- spring/mvc-sseemitter-vs-webflux-sse-timeout-behavior
- spring/sse-replay-buffer-last-event-id-recovery-patterns
linked_paths:
- contents/spring/spring-sse-buffering-compression-checklist.md
- contents/spring/spring-sse-proxy-idle-timeout-matrix.md
- contents/spring/spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md
- contents/spring/spring-sse-replay-buffer-last-event-id-recovery-patterns.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-sse-disconnect-observability-patterns.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
confusable_with:
- spring/sse-buffering-compression-checklist
- spring/sse-proxy-idle-timeout-matrix
- spring/sse-replay-buffer-last-event-id-recovery-patterns
- spring/streamingresponsebody-responsebodyemitter-sse-commit-lifecycle
forbidden_neighbors: []
expected_queries:
- Spring SSE가 실시간으로 안 오고 몇 초 뒤에 한꺼번에 몰려오면 어디부터 의심해야 해?
- heartbeat는 보내는데 브라우저 EventSource callback이 늦게 찍히는 이유를 빠르게 나누고 싶어
- origin curl에서는 정상인데 ALB나 Nginx 뒤에서만 SSE가 burst처럼 보일 때 첫 분기는 뭐야?
- SseEmitter timeout 문제인지 proxy buffering 문제인지 어떤 질문으로 갈라야 해?
- SSE 재연결 뒤 이벤트를 놓치거나 중복으로 받는 증상까지 같이 보이면 무엇을 이어서 읽어야 해?
contextual_chunk_prefix: |
  이 문서는 학습자가 Spring SSE에서 "실시간 알림이 안 오고 한꺼번에
  몰려와요", "heartbeat는 보냈는데 브라우저는 멈춘 것 같아요", "origin은
  정상인데 ALB나 Nginx 뒤에서만 늦어요", "재연결 뒤 이벤트가 비거나 중복돼요"
  같은 자연어 증상을 buffering/compression, proxy idle timeout, app timeout
  과 실행 모델, replay/Last-Event-ID 설계 네 갈래로 나누는 symptom_router다.
  SSE burst delivery, EventSource callback 지연, text/event-stream buffering
  증상을 원인 문서로 보내는 입구로 사용한다.
---

# SSE 이벤트가 한꺼번에 와요 원인 라우터

## 한 줄 요약

> SSE가 몰려오면 먼저 "서버가 못 보냈다"보다 "중간 hop이 즉시 안 흘려보냈다"를 의심하고, 그다음에 timeout과 replay 설계를 분리해서 본다.

## 가능한 원인

1. **buffering이나 compression이 heartbeat cadence를 뭉갰다.** 서버는 15초마다 `send()`를 해도 Nginx, CDN, gzip, body transform이 여러 event를 모아 브라우저에 늦게 내릴 수 있다. 이 갈래는 [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)로 바로 이어진다.
2. **proxy idle timeout과 heartbeat 간격이 어긋났다.** app은 살아 있는데 ALB, Nginx, CDN의 가장 짧은 idle timeout이 먼저 닫히면 다음 write 때까지 조용하다가 reconnect 뒤에야 움직이는 것처럼 보인다. 이때는 [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)에서 hop별 타이머를 분리한다.
3. **`SseEmitter`와 WebFlux SSE의 lifetime 해석을 섞었다.** MVC async timeout, `Flux.timeout()`, blocking write 관측을 한 문제로 뭉치면 "실시간이 늦다"는 표면 증상만 같고 실제 수정 지점은 달라진다. 이 분기는 [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)와 [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)로 내려간다.
4. **reconnect는 되지만 replay 계약이 약하다.** 연결이 다시 붙은 뒤 `Last-Event-ID`, replay window, ordering fence가 없으면 끊긴 동안의 이벤트를 놓치거나 중복으로 받아 "몰아서 온다"는 체감이 더 심해진다. 이 경우는 [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)를 먼저 본다.

## 빠른 자기 진단

1. origin 직결 `curl -N`은 실시간인데 브라우저나 edge 경유에서만 늦다면 app 로직보다 buffering/compression 갈래가 우선이다.
2. 일정한 간격으로 조용히 끊기고 다음 heartbeat나 business event에서야 예외가 보이면 heartbeat와 proxy idle timeout 숫자부터 비교한다.
3. MVC `SseEmitter`인지 WebFlux `Flux<ServerSentEvent<?>>`인지 말이 섞여 있으면 같은 symptom이라도 timeout 소유권이 다르니 실행 모델 문서로 먼저 분기한다.
4. reconnect 뒤 `Last-Event-ID`가 비어 있거나, 같은 event id가 다시 오거나, 일부 구간이 비면 전달 지연 하나만의 문제가 아니라 replay 계약 문제까지 같이 본다.

## 다음 학습

- 브라우저에 늦게 도착하는 이유를 가장 빨리 자르려면 [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)와 [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)를 한 쌍으로 본다.
- MVC `SseEmitter`와 WebFlux SSE의 timeout 소유권이 헷갈리면 [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md), commit 시점이 헷갈리면 [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)로 이어간다.
- 끊김 관측과 재연결 품질까지 같이 보려면 [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md), [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md), [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md) 순으로 내려간다.
