---
schema_version: 3
title: "Keep-Alive Reuse, Stale Idle Connection Primer"
concept_id: network/keepalive-reuse-stale-idle-connection-primer
canonical: true
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- keep-alive
- stale-idle-connection
- first-request-after-idle
aliases:
- keep-alive first request after idle
- stale idle connection
- keepalive reuse failure
- idle 뒤 첫 요청 실패
- broken pipe after idle
- connection reset after idle
- stale socket beginner
symptoms:
- 한참 쉬었다가 보낸 첫 요청만 connection reset이나 broken pipe로 실패한다
- 바로 재시도하면 새 연결로 성공해서 서버가 잠깐 이상했다고 오해한다
- keep-alive를 켰으니 idle 뒤에도 연결이 반드시 살아 있다고 믿는다
- TCP keepalive와 HTTP keep-alive를 같은 기능으로 본다
intents:
- symptom
- troubleshooting
- definition
prerequisites:
- network/keepalive-connection-reuse-basics
- network/browser-devtools-first-fail-second-success-keepalive-card
next_docs:
- network/http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer
- network/idle-timeout-mismatch-lb-proxy-app
- network/http-keepalive-timeout-mismatch-deeper-cases
- spring/webclient-connection-pool-timeout-tuning
linked_paths:
- contents/network/keepalive-connection-reuse-basics.md
- contents/network/browser-devtools-first-fail-second-success-keepalive-card.md
- contents/network/http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md
- contents/network/idle-timeout-mismatch-lb-proxy-app.md
- contents/network/rst-on-idle-keepalive-reuse.md
- contents/spring/spring-webclient-connection-pool-timeout-tuning.md
confusable_with:
- network/keepalive-connection-reuse-basics
- network/http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer
- network/idle-timeout-mismatch-lb-proxy-app
- network/rst-on-idle-keepalive-reuse
forbidden_neighbors: []
expected_queries:
- "keep-alive를 켰는데 idle 뒤 첫 요청만 실패하는 이유가 뭐야?"
- "stale idle connection과 connection reset after idle을 초보자에게 설명해줘"
- "왜 첫 요청은 깨지고 바로 재시도하면 성공해?"
- "HTTP keep-alive와 TCP keepalive가 이 문제에서 어떻게 달라?"
- "idle timeout mismatch 때문에 stale socket을 재사용하는 패턴을 알려줘"
contextual_chunk_prefix: |
  이 문서는 HTTP keep-alive connection reuse에서 idle timeout으로 죽은
  stale idle connection을 첫 요청에 재사용해 reset/broken pipe가 나는
  beginner symptom router다.
---
# Keep-Alive 켰는데 왜 idle 뒤 첫 요청만 실패할까? (Stale Idle Connection Primer)

> 한 줄 요약: keep-alive는 연결 재사용 기능이지만, idle 동안 중간 장비가 먼저 연결을 닫으면 클라이언트는 "살아 있다고 믿은 연결"을 다시 써서 첫 요청만 실패할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md)
- [Browser DevTools 첫 실패 후 두 번째 성공 trace 카드](./browser-devtools-first-fail-second-success-keepalive-card.md)
- [HTTP keep-alive vs TCP keepalive vs idle timeout vs heartbeat](./http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md)
- [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
- [RST on Idle Keep-Alive Reuse](./rst-on-idle-keepalive-reuse.md)
- [Spring WebClient Connection Pool / Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: keep-alive first request after idle, stale idle connection primer, keepalive reuse why first request fails, idle timeout mismatch basics, connection reset after idle, broken pipe after idle, keep-alive 켰는데 왜 실패, 한참 후 첫 요청 실패, stale socket 뭐예요, why keep-alive fails after idle, beginner keepalive reset, 처음 idle 뒤 요청 왜 터져요

## 핵심 개념

keep-alive를 켰다는 말은 "다음 요청에도 같은 연결을 재사용할 수 있다"는 뜻이지, 그 연결이 영원히 살아 있다는 뜻은 아니다. 문제는 클라이언트, LB, proxy, app server가 각자 idle timeout을 따로 가진다는 점이다.

그래서 한쪽은 "아직 재사용 가능"이라고 믿는데, 다른 한쪽은 이미 그 연결을 정리했을 수 있다. 이때 가장 흔한 증상이 `한참 쉬었다가 보낸 첫 요청만 connection reset/broken pipe로 실패하고, 바로 재시도하면 성공`하는 패턴이다.

## 한눈에 보기

| 시점 | 클라이언트가 믿는 것 | 실제 반대편 상태 | 보이는 증상 |
|---|---|---|---|
| 방금 요청 직후 | keep-alive 연결이 살아 있다 | 실제로도 살아 있다 | 정상 |
| idle 구간이 길어짐 | 아직 재사용 가능하다고 본다 | LB/proxy/server가 먼저 닫을 수 있다 | 겉으로는 조용함 |
| idle 뒤 첫 요청 | 기존 연결에 다시 쓴다 | 이미 죽은 연결일 수 있다 | `connection reset`, `broken pipe`, 간헐적 502 |
| 바로 재시도 | 새 연결을 만든다 | 새 연결은 정상 | 두 번째는 성공 가능 |

초급자용 기억법은 간단하다.

- keep-alive는 "재사용"
- idle timeout은 "조용하면 정리"
- stale idle connection은 "재사용 후보처럼 보이지만 실제론 이미 죽은 연결"

## 상세 분해

### 1. 왜 첫 요청만 자주 터질까

idle 동안에는 아무 요청도 안 보내므로 문제를 드러낼 기회가 없다. 클라이언트 풀은 연결 객체를 들고 있지만, 반대편은 이미 timeout으로 닫았을 수 있다. 그래서 "재사용하려는 순간"에만 실패가 드러난다.

### 2. 왜 재시도하면 바로 성공할까

첫 시도는 죽은 연결을 재사용하려다 실패한 것이다. 실패 뒤에는 보통 그 연결을 버리고 새 TCP 연결을 만든다. 그래서 두 번째 시도는 정상 경로로 지나가며, 초급자 입장에서는 "서버가 잠깐 이상했나?"처럼 오해하기 쉽다.

### 3. 누가 먼저 닫았는지가 핵심이다

원인은 keep-alive 자체보다 timeout 관계에 있다. 예를 들어 client pool은 60초까지 믿는데 proxy는 30초에 닫으면, 31초 뒤 첫 재사용에서 stale socket 문제가 생길 수 있다. 즉 숫자 하나보다 "어느 홉이 먼저 포기하느냐"가 더 중요하다.

## 흔한 오해와 함정

- keep-alive를 켰으니 idle 뒤에도 항상 안전하게 재사용된다고 생각하면 틀린다.
- TCP keepalive를 켰다고 이 문제가 자동 해결되진 않는다. LB나 proxy의 idle timeout이 더 먼저 끝날 수 있다.
- 첫 요청 실패를 바로 애플리케이션 버그로 단정하면 놓친다. `idle 뒤 첫 요청만` 실패하는지 먼저 본다.
- retry가 성공한다고 문제가 사라진 것은 아니다. 사용자는 첫 요청 지연이나 간헐 실패를 이미 겪는다.
- 로그인 세션 만료와 헷갈리기 쉽지만, 여기서는 인증보다 "연결 수명"이 핵심이다.

## 실무에서 쓰는 모습

가장 흔한 예시는 외부 API 호출이나 DB 앞단 proxy 뒤의 HTTP 클라이언트 풀이다. 평소에는 빠르다가 한동안 트래픽이 없다가 다시 호출하면 첫 요청만 `ECONNRESET`이나 `broken pipe`가 난다. 이후 retry는 성공한다.

초급자라면 아래 순서로 읽으면 된다.

1. keep-alive 재사용 자체는 정상 기능이다.
2. 하지만 idle timeout은 각 홉마다 다르다.
3. 그래서 재사용 후보 중 일부가 stale idle connection이 될 수 있다.
4. 첫 요청 실패 뒤 새 연결을 만들면 다시 성공한다.

이 패턴을 보면 "왜 keep-alive인데 실패하지?"보다 "누가 먼저 idle close 했지?"를 먼저 떠올리는 편이 맞다.

## 더 깊이 가려면

- 재사용 자체를 먼저 잡으려면 [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md)
- DevTools 두 줄 trace에서 이 패턴을 빠르게 읽으려면 [Browser DevTools 첫 실패 후 두 번째 성공 trace 카드](./browser-devtools-first-fail-second-success-keepalive-card.md)
- keepalive, timeout, heartbeat 용어를 분리하려면 [HTTP keep-alive vs TCP keepalive vs idle timeout vs heartbeat](./http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md)
- hop별 timeout 불일치를 더 깊게 보려면 [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
- reset 관찰을 운영 관점에서 보려면 [RST on Idle Keep-Alive Reuse](./rst-on-idle-keepalive-reuse.md)
- Spring 클라이언트 풀 설정으로 이어 보려면 [Spring WebClient Connection Pool / Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)

## 면접/시니어 질문 미리보기

**Q. keep-alive를 켰는데 왜 첫 요청이 실패할 수 있나요?**  
keep-alive는 재사용 기능일 뿐이다. idle 동안 중간 장비가 먼저 연결을 닫으면, 클라이언트가 stale connection을 재사용하려다 실패할 수 있다.

**Q. 왜 첫 요청만 실패하고 두 번째는 성공하나요?**  
첫 요청은 죽은 연결을 건드렸고, 실패 후에는 새 연결을 만들기 때문이다.

**Q. 무엇을 먼저 맞춰야 하나요?**  
client pool, proxy, LB, server의 idle timeout 관계를 보고 재사용하는 쪽이 너무 오래 믿지 않게 조정하는 것이 출발점이다.

## 한 줄 정리

idle 뒤 첫 요청만 실패한다면 keep-alive 자체를 의심하기보다, 먼저 닫힌 연결을 클라이언트가 다시 쓰는 stale idle reuse 패턴을 떠올려야 한다.
