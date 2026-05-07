---
schema_version: 3
title: HTTP Keep-Alive와 커넥션 재사용 기초
concept_id: network/keepalive-connection-reuse-basics
canonical: true
category: network
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- http-keepalive-basics
- connection-reuse-handshake-cost
- stale-idle-connection-handoff
aliases:
- keepalive connection reuse basics
- HTTP keep-alive basics
- connection reuse
- persistent connection
- keep-alive 뭐예요
- tcp 연결 재사용
- HTTP 연결 유지
- keepalive와 로그인 유지 차이
- keepalive랑 tcp keepalive 헷갈려요
symptoms:
- HTTP Keep-Alive를 로그인 세션 유지나 TCP keepalive probe와 같은 개념으로 섞어 이해한다
- 연결 재사용이 동시에 여러 요청을 처리한다는 뜻으로 오해해 HTTP/2 multiplexing과 구분하지 못한다
- idle 뒤 첫 요청 실패를 Keep-Alive가 꺼진 문제로만 보고 stale idle connection 재사용을 확인하지 않는다
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- network/tcp-three-way-handshake-basics
- network/http-https-basics
next_docs:
- network/http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer
- network/keepalive-reuse-stale-idle-connection-primer
- network/connection-keepalive-loadbalancing-circuit-breaker
- network/devtools-waterfall-primer
linked_paths:
- contents/network/keepalive-reuse-stale-idle-connection-primer.md
- contents/network/http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md
- contents/network/tcp-three-way-handshake-basics.md
- contents/network/http-https-basics.md
- contents/network/browser-devtools-waterfall-primer.md
- contents/database/connection-pool-basics.md
confusable_with:
- network/http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer
- network/keepalive-reuse-stale-idle-connection-primer
- network/tcp-three-way-handshake-basics
- database/connection-pool
forbidden_neighbors: []
expected_queries:
- HTTP Keep-Alive는 TCP 연결을 어떻게 재사용해서 handshake 비용을 줄여?
- keepalive는 로그인 유지가 아니라 connection reuse라는 뜻이야?
- HTTP Keep-Alive와 TCP keepalive는 왜 다른 개념이야?
- 한참 쉬었다가 첫 요청만 connection reset이 나면 stale idle connection을 의심해야 해?
- 브라우저 DevTools에서 두 번째 요청의 dns connect ssl 시간이 사라지는 이유가 연결 재사용 때문일 수 있어?
contextual_chunk_prefix: |
  이 문서는 HTTP Keep-Alive beginner primer로, 요청마다 TCP/TLS handshake를
  새로 만들지 않고 같은 connection을 재사용하는 persistent connection
  개념을 설명한다. TCP keepalive, idle timeout, heartbeat, stale idle
  connection과 혼동되는 질문을 다음 문서로 라우팅한다.
---
# HTTP Keep-Alive와 커넥션 재사용 기초

> 한 줄 요약: Keep-Alive는 TCP 연결을 요청마다 끊지 않고 여러 요청에 걸쳐 재사용하는 기능이고, 이를 통해 매 요청마다 발생하는 핸드셰이크 비용을 아낄 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Keep-Alive 켰는데 왜 idle 뒤 첫 요청만 실패할까? (Stale Idle Connection Primer)](./keepalive-reuse-stale-idle-connection-primer.md)
- [HTTP keep-alive vs TCP keepalive vs idle timeout vs heartbeat](./http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md)
- [TCP 3-way handshake 기초](./tcp-three-way-handshake-basics.md)
- [HTTP와 HTTPS 기초](./http-https-basics.md)
- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- [network 카테고리 인덱스](./README.md)
- [커넥션 풀 기초](../database/connection-pool-basics.md)

retrieval-anchor-keywords: keep-alive basics, http 커넥션 재사용, tcp 연결 재사용, keep-alive 뭐예요, keepalive 큰 그림, connection reuse 입문, http 연결 유지, 왜 연결을 끊지 않아요, keepalive는 왜 쓰나요, keepalive 처음 배우는데, http/1.1 persistent connection, beginner keep-alive, 처음 배우는 커넥션 재사용, keepalive와 로그인 유지 차이, keepalive랑 tcp keepalive 헷갈려요

## 핵심 개념

HTTP/1.0까지는 요청 하나를 보내고 응답을 받으면 TCP 연결을 바로 끊었다. 다음 요청이 오면 새로 연결을 맺었다. 웹페이지 하나에 이미지·CSS·JS가 수십 개라면, 파일마다 TCP 핸드셰이크(3-way handshake)와 TLS 핸드셰이크가 반복된다. 이 비용은 꽤 크다.

**Keep-Alive**는 TCP 연결을 열어두고 여러 HTTP 요청/응답을 같은 연결로 처리하는 방식이다. HTTP/1.1부터 기본값이 됐다. 입문자가 헷갈리는 점은 Keep-Alive가 요청을 동시에 처리하는 게 아니라, 연결을 재사용해 순차 요청의 오버헤드를 줄이는 것이라는 점이다.

이 문서는 "`keepalive가 뭐예요?`", "`왜 매번 새 연결을 안 만들어요?`", "`keepalive가 로그인 유지예요?`" 같은 첫 질문에서 읽는 entry primer다. `timeout mismatch`, `stale connection`, `HTTP/2` 운영 튜닝은 다음 단계로 넘기고, 여기서는 "같은 TCP 연결을 다시 쓴다"는 그림만 먼저 고정한다.

## 한눈에 보기

| 방식 | 동작 | 비용 |
|---|---|---|
| Connection: close (HTTP/1.0 기본) | 요청마다 연결 생성 + 해제 | 매 요청에 핸드셰이크 발생 |
| Connection: keep-alive (HTTP/1.1 기본) | 연결 유지 후 재사용 | 첫 연결 시 1회만 핸드셰이크 |

## 상세 분해

### 어떻게 동작하는가

1. 클라이언트가 첫 요청을 보낼 때 TCP 연결을 맺는다(3-way handshake).
2. 서버는 응답 후 연결을 바로 닫지 않고 열어둔다.
3. 클라이언트가 같은 서버에 다음 요청을 보낼 때 기존 연결을 재사용한다.
4. 일정 시간 요청이 없으면(idle timeout) 서버 또는 클라이언트가 연결을 닫는다.

### keep-alive 헤더

HTTP/1.1 응답에는 `Keep-Alive: timeout=60, max=100` 같은 헤더가 올 수 있다. timeout은 유휴 상태에서 연결을 유지하는 초(秒), max는 연결 하나로 처리할 최대 요청 수다.

### HTTP/2에서의 변화

HTTP/2는 멀티플렉싱으로 한 연결에서 여러 요청을 동시에 처리할 수 있다. 연결 재사용 자체가 아예 설계 핵심이라 Keep-Alive 헤더 없이도 연결이 유지된다.

## 흔한 오해와 함정

- Keep-Alive가 연결을 무한정 유지한다고 오해하기 쉽다. idle timeout 설정에 따라 연결은 닫힌다. Nginx 기본값은 75초, Spring Boot 기본 Tomcat은 60초다.
- Keep-Alive가 항상 좋은 건 아니다. 연결 수가 너무 많으면 서버 소켓 리소스가 부족해진다. 짧은 일회성 요청이 많은 상황에서는 오히려 빠른 종료가 낫다.
- "TCP keep-alive"와 "HTTP keep-alive"는 다르다. TCP keep-alive는 연결이 살아있는지 확인하는 탐침 패킷이고, HTTP keep-alive는 커넥션 재사용을 의미한다.
- "keepalive timeout", "heartbeat", "session 유지"를 한 말로 섞고 있다면 먼저 [HTTP keep-alive vs TCP keepalive vs idle timeout vs heartbeat](./http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md)에서 용어부터 분리하는 편이 빠르다.
- keep-alive를 켰는데도 `한참 쉬었다가 첫 요청만 실패`할 수 있다. 이건 keep-alive가 꺼진 것이 아니라 idle 동안 먼저 닫힌 연결을 재사용한 패턴일 수 있으니 [Stale Idle Connection Primer](./keepalive-reuse-stale-idle-connection-primer.md)로 이어서 보는 편이 좋다.

## 실무에서 쓰는 모습

Spring Boot에서 외부 API를 호출할 때 `RestTemplate`이나 `WebClient`를 사용한다. 이때 연결 풀(connection pool)을 설정하면 미리 맺어둔 TCP 연결을 재사용해 호출마다 핸드셰이크 비용이 없다. 풀 없이 매번 새 연결을 만들면 응답 속도가 훨씬 느려진다.

브라우저 DevTools에서도 같은 현상을 볼 수 있다. 첫 요청에는 `dns`, `connect`, `ssl`이 보이는데, 같은 origin의 다음 요청에서는 그 칸들이 짧아지거나 사라질 수 있다. 이때는 "계측이 빠졌다"보다 "이미 열린 keep-alive 연결을 다시 썼다"를 먼저 떠올리는 편이 정확하다.

## 더 깊이 가려면

- "`keepalive`, `TCP keepalive`, `idle timeout`, `heartbeat`가 한꺼번에 헷갈리면 [HTTP keep-alive vs TCP keepalive vs idle timeout vs heartbeat](./http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md)부터 용어를 먼저 자른다.
- [TCP 3-way handshake](./tcp-three-way-handshake-basics.md) — 핸드셰이크 비용이 왜 발생하는지 이해
- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md) — 재사용 연결에서 `dns/connect/ssl`이 왜 안 보일 수 있는지 waterfall으로 읽기
- [Keep-Alive 켰는데 왜 idle 뒤 첫 요청만 실패할까? (Stale Idle Connection Primer)](./keepalive-reuse-stale-idle-connection-primer.md) — keep-alive 재사용과 idle timeout mismatch가 만나 `connection reset`으로 보이는 beginner 증상 정리
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md) — Keep-Alive 운영 상세

## 면접/시니어 질문 미리보기

**Q. HTTP Keep-Alive가 무엇이고 왜 필요한가요?**
TCP 연결을 요청마다 끊지 않고 재사용하는 기능이다. 매 요청마다 3-way handshake와 TLS handshake를 새로 하는 비용을 아낄 수 있다. HTTP/1.1부터 기본값이다.

**Q. Keep-Alive timeout이 맞지 않으면 어떤 문제가 생기나요?**
서버가 먼저 연결을 닫았는데 클라이언트가 그 연결에 요청을 보내면 오류(예: Connection reset)가 발생한다. 서버 idle timeout보다 클라이언트 연결 풀의 max-idle-time을 짧게 설정해야 한다.

**Q. HTTP/2를 쓰면 Keep-Alive를 따로 신경 안 써도 되나요?**
HTTP/2는 연결 재사용이 설계 기본이므로 HTTP/1.1의 Keep-Alive 헤더 설정이 덜 중요하다. 그러나 연결 수명(idle timeout, max connection age) 관리는 여전히 필요하다.

## 한 줄 정리

Keep-Alive는 TCP 연결을 재사용해 매 요청마다 핸드셰이크 비용이 발생하는 낭비를 막는다.
