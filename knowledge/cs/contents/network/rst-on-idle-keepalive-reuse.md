---
schema_version: 3
title: "RST on Idle Keep-Alive Reuse"
concept_id: network/rst-on-idle-keepalive-reuse
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- stale-socket
- keep-alive
- tcp-rst
aliases:
- RST on idle keep-alive reuse
- idle reuse RST
- stale socket
- ECONNRESET after idle
- broken pipe after idle
- first request after idle
- connection pool stale
symptoms:
- idle 뒤 첫 요청만 RST나 broken pipe로 실패하고 retry는 성공한다
- client pool은 살아 있다고 믿지만 LB/proxy/origin이 먼저 idle close한 상황을 놓친다
- 배포 후 reset 증가를 draining이나 timeout hierarchy와 연결하지 못한다
- RST를 항상 app crash나 server bug로 본다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/keepalive-reuse-stale-idle-connection-primer
- network/idle-timeout-mismatch-lb-proxy-app
next_docs:
- network/tcp-reset-storms-idle-reuse-stale-sockets
- network/http-keepalive-timeout-mismatch-deeper-cases
- network/fin-rst-half-close-eof-semantics
- network/lb-connection-draining-deployment-safe-close
linked_paths:
- contents/network/tcp-reset-storms-idle-reuse-stale-sockets.md
- contents/network/idle-timeout-mismatch-lb-proxy-app.md
- contents/network/http-keepalive-timeout-mismatch-deeper-cases.md
- contents/network/fin-rst-half-close-eof-semantics.md
- contents/network/lb-connection-draining-deployment-safe-close.md
confusable_with:
- network/keepalive-reuse-stale-idle-connection-primer
- network/tcp-reset-storms-idle-reuse-stale-sockets
- network/http-keepalive-timeout-mismatch-deeper-cases
- network/idle-timeout-mismatch-lb-proxy-app
forbidden_neighbors: []
expected_queries:
- "idle 후 keep-alive 재사용 시 RST가 나는 이유는?"
- "첫 요청은 ECONNRESET인데 retry는 성공하는 stale socket 패턴을 설명해줘"
- "client pool idle lifetime과 LB proxy timeout을 어떻게 맞춰?"
- "배포 후 reset 증가가 connection draining과 관련 있는 이유는?"
- "RST on idle reuse와 FIN/RST half-close 의미를 어떻게 구분해?"
contextual_chunk_prefix: |
  이 문서는 network 카테고리에서 RST on Idle Keep-Alive Reuse를 다루는 playbook 문서다. RST on idle keep-alive reuse, idle reuse RST, stale socket, ECONNRESET after idle, broken pipe after idle 같은 lexical 표현과 idle í keep-alive ì¬ì¬ì© ì RSTê° ëë ì´ì ë?, ì²« ìì²­ì ECONNRESETì¸ë° retryë ì±ê³µíë stale socket í¨í´ì ì¤ëª
  í´ì¤ 같은 자연어 질문을 같은 개념으로 묶어, 학습자가 증상, 비교, 설계 판단, 코드리뷰 맥락 중 어디에서 들어오더라도 본문의 핵심 분기와 다음 문서로 안정적으로 이어지게 한다.
---
# RST on Idle Keep-Alive Reuse

> 한 줄 요약: idle 후 keep-alive 재사용 시 RST가 나는 것은 대개 중간 장비가 소켓을 먼저 닫았는데 클라이언트 풀만 아직 믿고 있기 때문이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TCP Reset Storms, Idle Reuse, Stale Sockets](./tcp-reset-storms-idle-reuse-stale-sockets.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [HTTP Keep-Alive Timeout Mismatch, Deeper Cases](./http-keepalive-timeout-mismatch-deeper-cases.md)
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [LB Connection Draining, Deployment Safe Close](./lb-connection-draining-deployment-safe-close.md)

retrieval-anchor-keywords: RST, idle reuse, keep-alive, stale socket, broken pipe, ECONNRESET, proxy close, connection pool, first request after idle

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

idle 후 keep-alive 재사용 시 RST가 나는 건 아주 흔한 패턴이다.

- client pool은 연결이 살아 있다고 본다
- LB/proxy/origin은 이미 idle timeout으로 닫았다
- 첫 재사용에서 바로 RST가 난다

### Retrieval Anchors

- `RST`
- `idle reuse`
- `keep-alive`
- `stale socket`
- `broken pipe`
- `ECONNRESET`
- `proxy close`
- `connection pool`
- `first request after idle`

## 깊이 들어가기

### 1. 왜 첫 요청만 터지나

idle 구간 동안 중간 장비가 연결을 정리했을 수 있다.

- pool은 아직 객체를 가지고 있다
- OS는 파일 디스크립터가 열려 있다
- 실제 peer는 이미 사라졌다

### 2. 왜 RST로 보이나

정상 종료가 아니라 강제 종료나 상태 불일치일 때 흔하다.

- peer가 소켓 상태를 버렸다
- timeout mismatch가 있었다
- 드물게 proxy가 세션을 정리했다

### 3. 왜 디버깅이 어렵나

재사용하기 전까지 아무 문제가 없기 때문이다.

- 새 연결은 잘 된다
- idle 뒤 첫 재사용만 실패한다
- 이후 retry는 성공할 수 있다

### 4. 무엇을 먼저 보나

- pool idle lifetime
- LB/proxy timeout
- connection validation
- retry behavior

### 5. 예방책

- borrow 시 validation
- idle eviction
- timeout hierarchy 정렬
- draining과 함께 배포

## 실전 시나리오

### 시나리오 1: 가끔만 broken pipe가 난다

idle reuse와 RST를 의심한다.

### 시나리오 2: 배포 후에만 reset이 늘어난다

draining이 충분하지 않거나 timeout이 바뀌었을 수 있다.

### 시나리오 3: 특정 프록시 뒤에서만 실패한다

중간 장비가 먼저 닫았는데 app pool이 오래 믿고 있을 수 있다.

## 코드로 보기

### 관찰

```bash
ss -tan state established
tcpdump -i eth0 'tcp[tcpflags] & tcp-rst != 0'
```

### 정책 감각

```text
validate on borrow
evict idle before proxy timeout
align client pool with upstream lifetime
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 오래 재사용 | handshake 비용이 적다 | idle reuse RST 위험이 있다 | 안정적인 peer |
| 자주 재연결 | stale risk가 줄어든다 | 비용이 늘어난다 | 변동성 큰 경로 |
| 검증 후 재사용 | 안정성이 높다 | 약간 느리다 | 운영 안정성이 중요할 때 |

핵심은 재사용 자체가 아니라 **재사용 직전에 실제 살아 있는지**다.

## 꼬리질문

> Q: idle reuse에서 RST가 왜 나나요?
> 핵심: 중간 장비가 이미 닫은 연결을 client pool이 다시 쓰기 때문이다.

> Q: broken pipe와 다른가요?
> 핵심: 둘 다 닫힌 소켓에 write할 때 보이지만 원인은 동일 계열이다.

> Q: 어떻게 줄이나요?
> 핵심: validation, eviction, timeout 정렬, draining을 같이 쓴다.

## 한 줄 정리

idle keep-alive reuse에서 RST가 나면 소켓은 살아 보여도 peer는 이미 닫힌 상태이므로 pool 검증과 timeout 정렬이 필요하다.
