---
schema_version: 3
title: 업로드는 끝났는데 마지막에 거절됨 원인 라우터
concept_id: network/upload-finishes-then-rejected-symptom-router
canonical: false
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- upload-owner-before-blame
- late-reject-vs-late-cleanup
- body-bytes-vs-auth-latency
aliases:
- 업로드는 다 됐는데 마지막에 실패해요
- 파일 전송 끝나고 401이 떠요
- 업로드 100퍼센트 뒤에 403이 나와요
- 큰 파일 올리면 끝나고 413이 보여요
- 업로드 거의 끝날 때 499가 떠요
- 파일은 다 보낸 것 같은데 마지막에 거절돼요
symptoms:
- 큰 파일 업로드에서 progress는 거의 다 찼는데 마지막에 `401`, `403`, `413`, `499` 같은 거절 응답이 떠서 인증 문제인지 업로드 경로 문제인지 헷갈린다
- 컨트롤러는 거의 안 탔다고 들었는데 사용자는 파일을 오래 올린 뒤에야 실패를 봐서 왜 늦게 거절됐는지 감이 안 잡힌다
- 같은 업로드 API가 어떤 환경에서는 빨리 막히고 어떤 환경에서는 다 보낸 뒤 실패해서 gateway buffering인지 multipart parsing인지 구분이 안 된다
intents:
- symptom
- troubleshooting
prerequisites:
- network/http-request-response-headers-basics
next_docs:
- network/request-timing-decomposition
- network/request-pending-forever-symptom-router
- network/browser-devtools-blocked-canceled-failed-symptom-router
linked_paths:
- contents/network/gateway-buffering-vs-spring-early-reject.md
- contents/network/http-request-body-drain-early-reject-keepalive-reuse.md
- contents/network/proxy-to-container-upload-cleanup-matrix.md
- contents/network/multipart-parsing-vs-auth-reject-boundary.md
- contents/network/spring-multipart-exception-translation-matrix.md
- contents/network/http2-upload-early-reject-rst-stream-flow-control-cleanup.md
- contents/network/expect-100-continue-proxy-request-buffering.md
- contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md
- contents/network/browser-devtools-blocked-canceled-failed-symptom-router.md
confusable_with:
- network/request-pending-forever-symptom-router
- network/browser-devtools-blocked-canceled-failed-symptom-router
- network/browser-504-app-200-symptom-router
forbidden_neighbors: []
expected_queries:
- 파일 업로드는 거의 다 끝났는데 마지막에 401이나 403이 뜨면 어디부터 봐야 해?
- 큰 파일 전송 뒤에 413이 나오는 건 용량 제한이야 아니면 게이트웨이 문제야?
- 업로드 progress는 100퍼센트인데 마지막에 실패하면 왜 늦게 거절된 거야?
- controller는 안 탔다는데 사용자는 오래 업로드한 뒤 실패를 보는 이유가 뭐야?
- 업로드 끝무렵 499나 연결 종료가 보이면 auth 실패와 어떻게 나눠 읽어?
contextual_chunk_prefix: |
  이 문서는 학습자가 큰 파일 업로드에서 progress는 거의 다 찼는데 마지막에
  `401`, `403`, `413`, `499` 같은 거절 응답을 보는 증상을 원인별로 가르는
  network symptom_router다. 업로드는 다 됐는데 마지막에 실패해요, 파일 전송
  끝나고 401이 떠요, 큰 파일 올리면 끝나고 413이 보여요, 업로드 100퍼센트
  뒤에 거절돼요 같은 자연어 표현이 gateway buffering, multipart parsing,
  unread body cleanup, client disconnect 분기와 다음 문서 추천으로 매핑된다.
---

# 업로드는 끝났는데 마지막에 거절됨 원인 라우터

## 한 줄 요약

> 이 장면은 "인증이 틀렸다" 하나로 끝나지 않는다. 먼저 누가 request body를 어디까지 읽은 뒤 거절했는지와, 사용자가 본 실패가 reject 자체인지 cleanup tail인지부터 갈라야 한다.

## 가능한 원인

1. gateway나 proxy가 body를 먼저 거의 다 받은 뒤 upstream reject를 전달한 경우다. Spring 쪽 판단은 빨랐어도 wire에서는 이미 긴 upload가 끝나 버려 사용자는 "마지막에야 막혔다"고 느낀다. 다음 문서: [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md), [Expect `100-continue`, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
2. multipart parsing이나 size limit가 body를 읽기 시작한 뒤 발동한 경우다. controller에 깊이 들어가지 않았더라도 `MultipartFilter`, `request.getParts()`, container size guard가 먼저 움직이면 `401/403` 또는 `413`이 늦게 보일 수 있다. 다음 문서: [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md), [Spring Multipart Exception Translation Matrix](./spring-multipart-exception-translation-matrix.md)
3. reject는 이미 났지만 unread body cleanup이나 연결 정리 tail이 길게 남은 경우다. proxy나 container가 남은 body를 drain하거나 close하는 동안 사용자는 업로드가 끝나고도 한참 뒤 `499`나 reset 계열 실패를 볼 수 있다. 다음 문서: [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md), [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
4. HTTP/2나 client 쪽 전송 제어 때문에 "거절"보다 transport 종료가 먼저 눈에 들어온 경우다. stream reset, flow-control cleanup, client disconnect가 섞이면 auth 실패와 네트워크 종료가 같은 사건의 다른 표면일 수 있다. 다음 문서: [HTTP/2 Upload Early Reject, `RST_STREAM`, Flow-Control Cleanup](./http2-upload-early-reject-rst-stream-flow-control-cleanup.md), [Browser DevTools `(blocked)` / `canceled` / `(failed)` 원인 라우터](./browser-devtools-blocked-canceled-failed-symptom-router.md)

## 빠른 자기 진단

1. 먼저 최종 상태가 `401/403`, `413`, `499`, `(failed)` 중 무엇인지 적는다. 숫자 상태인지 브라우저 메모인지가 갈리면 다음 확인 문서도 달라진다.
2. waterfall에서 upload가 길었는지, `Waiting`이 길었는지, response가 거의 없는지 본다. upload tail이 길면 body ownership, `Waiting` tail이 길면 upstream reject 전달이나 cleanup 쪽이 더 강하다.
3. edge access log의 request body bytes와 app 쪽 auth 또는 multipart 로그를 함께 본다. edge는 많이 받았는데 app은 거의 안 읽었다면 buffering 분기, app에서 multipart 예외가 났다면 parsing 분기다.
4. `Expect: 100-continue`, `Content-Length`, multipart 여부, route별 buffering 설정 차이가 있는지 본다. 환경마다 "빨리 막힘"과 "다 보낸 뒤 막힘"이 갈리면 대개 여기서 힌트가 나온다.
5. 실패 직전이나 직후에 `499`, broken pipe, stream reset이 붙는지 확인한다. 붙는다면 business reject 한 줄로 끝내지 말고 unread body cleanup 또는 client disconnect 사건으로 같이 읽는다.

## 다음 학습

- timing 칸부터 다시 읽으려면 [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- 오래 걸리는 업로드가 실제로는 pending/queue 문제인지부터 가르려면 [요청이 Pending에서 안 끝남 원인 라우터](./request-pending-forever-symptom-router.md)
- 숫자 상태보다 `(failed)`나 `canceled`가 더 강하게 보이면 [Browser DevTools `(blocked)` / `canceled` / `(failed)` 원인 라우터](./browser-devtools-blocked-canceled-failed-symptom-router.md)
- upload cleanup 번역표로 바로 내려가려면 [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
