---
schema_version: 3
title: 브라우저는 504인데 앱 로그는 200 원인 라우터
concept_id: network/browser-504-app-200-symptom-router
canonical: false
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- edge-timeout-vs-app-success
- request-owner-before-retry
- request-id-correlation
aliases:
- 브라우저 504 앱 200
- 504인데 서버 로그는 200
- gateway timeout인데 서버는 성공
- edge 504 app 200
- 사용자 504 서버 200
- 사용자는 timeout인데 서버는 성공
- 504 후 재시도해도 되나
symptoms:
- "브라우저나 DevTools에서는 `504 Gateway Timeout`인데 서버 로그에는 같은 요청이 `200`으로 끝난 흔적이 보인다"
- 사용자는 실패 화면을 봤는데 백엔드 팀은 성공 로그가 있다며 서로 같은 요청을 다르게 설명한다
- "`504` 뒤에 재시도하려는데 첫 요청이 이미 처리됐는지 확신이 서지 않는다"
- "주문·결제·예약 같은 쓰기 요청이 `504`로 끝나 재시도 전에 중복 처리 여부가 걱정된다"
- gateway access log와 app trace를 맞춰 보는데 어느 홉이 사용자에게 실패를 선언했는지 헷갈린다
intents:
- symptom
- troubleshooting
prerequisites:
- network/http-status-codes-basics
- network/devtools-waterfall-primer
- network/request-timing-decomposition
next_docs:
- network/request-timing-decomposition
- network/devtools-waterfall-primer
- network/latency-bandwidth-throughput-basics
linked_paths:
- contents/network/edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge.md
- contents/network/browser-devtools-502-504-app-500-decision-card.md
- contents/network/browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
- contents/network/browser-devtools-gateway-error-header-clue-card.md
- contents/database/idempotency-key-status-contract-examples.md
- contents/network/timeout-retry-backoff-practical.md
confusable_with:
- network/browser-devtools-blocked-canceled-failed-symptom-router
- network/json-expected-but-html-response-symptom-router
forbidden_neighbors:
- contents/network/browser-devtools-502-504-app-500-decision-card.md
expected_queries:
- 브라우저에서는 Gateway Timeout인데 서버 로그에는 성공이 찍히는 이유가 뭐야?
- 504를 봤는데 백엔드는 200 완료라면 어디서 시간이 갈린 거야?
- 사용자 화면은 실패인데 앱 로그는 정상일 때 무엇부터 확인해야 해?
- edge가 timeout 냈는데 서버는 나중에 끝난 상황을 어떻게 해석해?
- 504 뒤 재시도 전에 첫 요청이 이미 처리됐는지 어떻게 판단해?
contextual_chunk_prefix: |
  이 문서는 학습자가 실패 화면과 성공 로그가 함께 보일 때 어느 홉이 먼저
  timeout을 선언했는지, 뒤쪽 처리가 늦게 끝난 건지 증상에서 원인으로
  이어지는 symptom_router다. 사용자 화면은 timeout인데 서버 일은 끝남,
  edge가 먼저 끊고 app은 나중에 완료, 실패 응답 뒤 성공 trace, 재시도 전에
  첫 요청 처리 여부 확인 같은 자연어 paraphrase가 본 문서의 분기에 매핑된다.
---

# 브라우저는 504인데 앱 로그는 200 원인 라우터

> 한 줄 요약: 브라우저의 `504`와 앱 로그의 `200`은 서로 모순이라기보다 다른 홉이 다른 시계로 같은 요청을 끝낸 흔적일 때가 많다. 먼저 누가 사용자에게 실패를 선언했는지, 앱은 그 뒤에 무엇을 끝냈는지 분리해서 본다.

**난이도: 🟢 Beginner**

관련 문서:

- [Edge는 `504`인데 App은 `200`? Timeout Budget Mismatch Beginner Bridge](./edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge.md) - hop별 timeout budget이 어긋나는 기본 구조
- [Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge](./browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md) - 첫 요청과 두 번째 요청이 섞였는지 확인하는 다음 단계
- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md) - 실제 응답 owner가 gateway인지 app인지 좁히는 문서
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md) - 브라우저 timeline과 서버 종료 시점을 같은 축으로 읽는 기본기
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md) - 쓰기 요청 재시도 안전성과 중복 방지를 이어서 보는 교차 카테고리 문서

## 어떤 장면에서 이 문서를 펴는가

- 브라우저에서는 `504 Gateway Timeout`인데 백엔드 팀 로그에는 같은 요청이 `200`으로 끝난 흔적이 있어 서로 다른 말을 할 때
- 주문, 결제, 예약 같은 쓰기 요청이 `504`로 보인 뒤 재시도해도 되는지 결정해야 할 때
- gateway access log와 app trace를 맞춰 보는데 어느 홉이 사용자에게 실패를 선언했는지부터 헷갈릴 때

이 장면의 핵심은 "같은 요청이 두 결과를 냈다"는 표현을 곧바로 믿지 않는 것이다. 실제로는 앞단 gateway가 먼저 실패를 응답했고 app은 뒤늦게 일을 마친 경우, 혹은 아예 두 번째 요청이 섞인 경우가 많다.

## 가능한 원인

1. edge나 gateway의 timeout budget이 앱 처리 시간보다 짧았을 수 있다. 사용자는 앞단이 만든 `504`를 봤지만 app은 그 뒤에 작업을 끝내며 `200`을 남긴다. 다음 문서: [Edge는 `504`인데 App은 `200`? Timeout Budget Mismatch Beginner Bridge](./edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge.md)
2. proxy가 upstream 응답을 기다리다 local reply를 만들었을 수 있다. 이 경우 앱 로그의 `200`은 "요청을 받았고 끝냈다"는 뜻이지만, 사용자가 받은 실제 응답 owner는 app이 아니라 proxy다. 다음 문서: [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md), [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
3. 같은 요청이라고 생각했지만 실제로는 재시도나 새로고침으로 두 번째 요청이 섞였을 수 있다. 첫 줄은 `504`인데 직후 다른 row가 `200`으로 끝나면 "하나의 요청이 두 결과를 냈다"보다 "두 번 요청됐다" 가능성도 같이 본다. 다음 문서: [Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge](./browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md)
4. app 로그와 브라우저 timeline의 시계를 같은 축에 놓지 않아 오해했을 수 있다. `504` 시점보다 앱 `200` 로그가 늦다면 모순이 아니라 종료 시점 차이다. 다음 문서: [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md), [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)

## 빠른 자기 진단

1. DevTools에서 `504` row 하나만 보지 말고 같은 URL의 직전·직후 row를 함께 본다. 같은 trace처럼 보이는 `200`이 사실 두 번째 요청이면 질문이 완전히 바뀐다.
2. `Status`, `Server`, `Via`, `X-Request-Id`, preview 첫 줄을 묶는다. `504` 응답의 owner가 gateway인지 app인지 먼저 가르면 app `200` 로그와 충돌하는 이유가 보인다.
3. waterfall에서 `Waiting`이 timeout 직전까지 길었는지 확인한다. 길다면 app exception보다 hop 간 timeout budget 차이를 먼저 의심한다.
4. 앱 로그 timestamp를 브라우저 실패 시점과 나란히 놓는다. 브라우저가 이미 실패를 본 뒤에 앱 `200`이 찍혔다면 "뒤늦은 성공" 갈래다.
5. 재시도 전에는 첫 요청이 실제로 side effect를 만들었는지 확인한다. 조회면 중복 부담이 작지만 생성·결제·주문 같은 요청은 이미 처리됐을 수 있다.

## 자주 하는 오해

- 브라우저가 `504`를 봤으니 서버는 아무 일도 못 했다고 단정하면 안 된다. app은 timeout 뒤에도 계속 실행되어 `200`을 남길 수 있다.
- app 로그에 `200`이 있으니 사용자가 성공을 본 것이라고 단정하면 안 된다. 사용자에게 실패를 선언한 주체가 앞단 proxy일 수 있다.
- 같은 URL의 `504`와 `200`이 보인다고 자동으로 "한 요청의 두 결과"라고 읽으면 안 된다. 새로고침, 자동 재시도, 버튼 재클릭이 섞였을 수 있다.

## 한 줄 정리

`504`와 app `200`이 같이 보이면 모순부터 찾지 말고 `누가 실패를 응답했는가`, `app은 그 뒤에 끝났는가`, `두 번째 요청이 섞였는가`를 순서대로 분리해서 본다.
