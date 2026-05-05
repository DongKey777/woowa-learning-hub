---
schema_version: 3
title: 같은 URL 요청이 두 번 보임 원인 라우터
concept_id: network/same-url-request-twice-symptom-router
canonical: false
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- duplicate-call-vs-retry
- same-url-trace-owner
- idempotent-retry-check
aliases:
- 같은 url이 두 번 떠요
- devtools에 같은 요청 두 줄
- 같은 api가 두 번 찍혀요
- 중복 호출인지 retry인지 모르겠어요
- 같은 요청이 다시 나가요
- 똑같은 path가 연속으로 보여요
- 421 뒤 같은 요청 재시도
symptoms:
- DevTools Network 탭에서 같은 URL이 연속으로 두 줄 보여서 프론트가 중복 호출한 건지 브라우저나 프록시가 다시 보낸 건지 헷갈린다
- 한 번만 클릭했는데 같은 API가 두 번 찍히고 첫 줄과 둘째 줄의 status가 달라 원인을 어디서 잘라야 할지 모르겠다
- "`421`, `302`, `304`, `504` 같은 status가 섞이며 같은 path가 반복돼서 같은 요청의 복구인지 다른 요청인지 판단이 안 된다"
- 주문·예약 같은 쓰기 요청에서 같은 endpoint가 두 번 보여 재시도 전에 첫 요청이 이미 처리됐는지 걱정된다
intents:
- symptom
- troubleshooting
prerequisites:
- network/http-status-codes-basics
- network/http-request-response-headers-basics
next_docs:
- network/idle-first-fail-second-success-symptom-router
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
- network/browser-devtools-blocked-canceled-failed-symptom-router
- network/proxy-retry-budget-discipline
linked_paths:
- contents/network/http2-http3-421-retry-after-wrong-coalescing.md
- contents/network/browser-devtools-cache-trace-primer.md
- contents/network/browser-fetch-vs-page-navigation-redirect-trace-card.md
- contents/network/browser-devtools-first-checklist-1minute-card.md
- contents/network/browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md
- contents/network/abortcontroller-search-autocomplete-canceled-trace-card.md
- contents/network/421-retry-path-mini-guide-fresh-h3-vs-h2-fallback.md
confusable_with:
- network/idle-first-fail-second-success-symptom-router
- network/browser-devtools-blocked-canceled-failed-symptom-router
- network/fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser
forbidden_neighbors: []
expected_queries:
- 브라우저 네트워크 탭에서 동일한 요청이 연속으로 두 번 보이면 어디부터 구분해?
- 하나의 클릭인데 요청이 두 번 간 것처럼 보일 때 중복 버그와 자동 재시도를 어떻게 나눠?
- 같은 엔드포인트가 421 다음에 다시 성공하면 프론트가 두 번 호출한 게 아닌가?
- redirect나 304 때문에 두 줄이 생긴 건지 확인하는 빠른 기준이 뭐야?
- gateway나 proxy retry 때문에 같은 요청이 반복된 흔적은 어떻게 읽어?
contextual_chunk_prefix: |
  이 문서는 학습자가 한 번 눌렀는데 동일 경로 요청이 연달아 보일 때 그것이
  진짜 중복 호출인지, 연결 복구나 redirect, cache 재검증, timeout 뒤
  재전송인지 증상에서 원인으로 잇는 network symptom_router다. 한 번 클릭했는데
  두 줄이 생김, 첫 줄 실패 뒤 다시 감, 같은 endpoint가 연속으로 찍힘,
  새로고침 없이 반복 흔적이 남음 같은 자연어 표현이 retry trace, 421 교정,
  redirect/cache follow 분기와 다음 문서 추천에 매핑된다.
---

# 같은 URL 요청이 두 번 보임 원인 라우터

## 한 줄 요약

> 같은 URL 두 줄은 곧바로 중복 버그를 뜻하지 않는다. 먼저 둘째 줄이 connection 복구인지, redirect나 cache follow인지, 진짜 두 번째 비즈니스 요청인지부터 가른다.

## 가능한 원인

1. 브라우저가 잘못된 connection을 교정하며 다시 보낸 경우다. `421` 뒤 같은 URL이 새 connection에서 다시 보이거나 idle 뒤 첫 줄만 실패하고 둘째 줄이 성공하면, 프론트 중복 호출보다 recovery trace일 가능성이 크다. 다음 문서: [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md), [idle 뒤 첫 요청만 실패하고 바로 다음은 성공 원인 라우터](./idle-first-fail-second-success-symptom-router.md)
2. redirect나 cache revalidation 때문에 비슷한 두 줄이 생긴 경우다. 첫 줄이 `302`이고 다음 줄이 `/login`이나 다른 URL이면 redirect chain이고, validator와 `304`가 보이면 같은 body를 다시 쓰는 cache 확인 흐름이다. 다음 문서: [Browser XHR/fetch vs page navigation DevTools 1분 비교 카드](./browser-fetch-vs-page-navigation-redirect-trace-card.md), [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
3. 실제로 프론트나 사용자 동작이 두 번째 요청을 만든 경우다. 중복 클릭, 검색어 변경, page navigation, abort 후 새 요청이 섞이면 URL이 같아 보여도 다른 initiator와 다른 시점의 요청일 수 있다. 다음 문서: [AbortController 검색 자동완성 `canceled` trace 카드](./abortcontroller-search-autocomplete-canceled-trace-card.md), [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
4. timeout이나 transport failure 뒤 client, gateway, proxy가 retry한 경우다. 첫 줄이 `504`, `(failed)`, reset 계열이고 둘째 줄이 늦게 성공하면 같은 endpoint 두 줄이 "실패 후 재전송"의 흔적일 수 있다. 쓰기 요청이라면 중복 side effect를 먼저 확인해야 한다. 다음 문서: [Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge](./browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md), [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)

## 빠른 자기 진단

1. 첫 줄 status와 response headers부터 본다. `421`이면 connection 교정 후보, `302`면 redirect 후보, `304`면 cache 재검증 후보, `(failed)`나 `504`면 retry 후보가 먼저 올라온다.
2. 두 줄의 method, query string, initiator, 시간 간격을 비교한다. 값이 다르거나 사용자 동작 직후면 같은 요청의 복구보다 별도 요청 가능성이 크다.
3. `Connection ID`, `Protocol`, `Remote Address`가 바뀌는지 본다. 둘째 줄에서 연결 정보가 바뀌면 browser recovery나 새 경로 선택 해석이 강해진다.
4. 첫 줄에 body가 있었는지 확인한다. login HTML, `Bad Gateway`, vendor HTML이 보이면 body owner 해석으로 내려가고, body 없이 빨간 줄이면 transport나 retry 쪽으로 간다.
5. 쓰기 요청이면 재시도 전에 side effect를 먼저 확인한다. 주문, 예약, 결제처럼 한 번만 처리돼야 하는 요청은 같은 URL 두 줄만 보고 안전하다고 판단하면 안 된다.

## 다음 학습

- `421 -> 200` 같은 recovery trace를 먼저 익히려면 [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- 첫 실패 뒤 둘째 줄 성공 패턴이 idle reuse인지 보려면 [idle 뒤 첫 요청만 실패하고 바로 다음은 성공 원인 라우터](./idle-first-fail-second-success-symptom-router.md)
- login redirect나 hidden HTML이 섞였는지 다시 가르려면 [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md)
- retry budget과 중복 부작용 경계를 운영 관점에서 보려면 [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)
