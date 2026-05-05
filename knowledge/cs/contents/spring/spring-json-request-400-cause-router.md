---
schema_version: 3
title: JSON 요청 400 원인 라우터
concept_id: spring/json-request-400-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids:
- missions/roomescape
- missions/baseball
- missions/blackjack
review_feedback_tags:
- requestbody-pre-controller-400
- valid-vs-message-conversion
- content-type-contract
aliases:
- json 요청 400 왜 나요
- spring json 400 cause router
- requestbody 400 어디서 갈라요
- controller 전에 400 나요
- '@valid 안 탄 것 같아요'
- localdate json 400 spring
- fetch 는 400 postman 은 됨
- body 안 보냈는데 400
- required request body is missing spring
- 415 랑 400 차이 처음
- json parse error basics
- what is spring requestbody 400
symptoms:
- POST JSON을 보내면 컨트롤러 첫 줄 로그도 없이 바로 400이 나와요
- Postman에서는 되는데 브라우저 fetch나 테스트에서는 JSON 요청이 400으로 끝나요
- 날짜나 시간 필드가 들어간 요청만 보내면 `@Valid` 전에 실패하는 것 같아요
- 같은 400인데 어떤 건 body 형식 문제 같고 어떤 건 validation 같아서 첫 분기가 안 돼요
intents:
- symptom
- troubleshooting
prerequisites:
- spring/controller-not-hit-cause-router
next_docs:
- spring/requestbody-400-before-controller-primer
- spring/requestbody-415-unsupported-media-type-primer
- spring/valid-400-vs-message-conversion-400-primer
- spring/controller-not-hit-cause-router
linked_paths:
- contents/spring/spring-requestbody-400-before-controller-primer.md
- contents/spring/spring-requestbody-415-unsupported-media-type-primer.md
- contents/spring/spring-valid-400-vs-message-conversion-400-primer.md
- contents/spring/spring-bindingresult-local-validation-400-primer.md
- contents/spring/spring-controller-not-hit-cause-router.md
- contents/spring/spring-localdate-localtime-json-400-cheatsheet.md
- contents/network/browser-devtools-waterfall-primer.md
confusable_with:
- spring/requestbody-400-before-controller-primer
- spring/requestbody-415-unsupported-media-type-primer
- spring/valid-400-vs-message-conversion-400-primer
- spring/controller-not-hit-cause-router
forbidden_neighbors: []
expected_queries:
- JSON API가 스프링 컨트롤러에 닿기 전에 400으로 끝날 때 어디부터 나눠서 봐야 해?
- `415`랑 `400`이 번갈아 보여서 헷갈릴 때 첫 분기 기준을 알려줘
- 날짜 필드 때문에 요청이 깨지는지 validation 전에 죽는지 빠르게 구분하고 싶어
- fetch에서는 실패하고 Postman에서는 되는 JSON 요청이면 무엇을 먼저 비교해야 해?
- body를 안 보낸 건지 JSON 파싱이 깨진 건지 스프링에서 어떻게 가려?
- `@Valid`가 안 탄 것처럼 보이는 JSON 400을 어떤 순서로 진단해?
contextual_chunk_prefix: |
  이 문서는 스프링 학습자가 JSON 요청 400을 만났을 때 media type 계약,
  body 누락, DTO 변환 실패, 날짜 형식, validation 진입 여부를 먼저 나누는
  symptom_router다. POST body를 보냈는데 컨트롤러 전에 끝난다, 브라우저에서만
  요청이 깨진다, 본문이 비었다고 나온다, 날짜 필드 넣으면 바로 실패한다,
  검증 전에 변환에서 멈춘 것 같다 같은 자연어 증상을 분기 기준에 매핑한다.
---
# JSON 요청 400 원인 라우터

> 한 줄 요약: JSON 요청 `400`은 한 가지 버그 이름이 아니라, 헤더 계약이 틀렸는지, body를 DTO로 못 바꿨는지, 날짜·시간 형식이 어긋났는지, validation까지 갔는지를 먼저 나눠야 빨라진다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)
- [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)
- [2단계 `@Valid`는 언제 타고 언제 못 타는가](./spring-valid-400-vs-message-conversion-400-primer.md)
- [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나](./spring-bindingresult-local-validation-400-primer.md)
- [컨트롤러 미진입 원인 라우터](./spring-controller-not-hit-cause-router.md)
- [Browser DevTools Waterfall Primer](../network/browser-devtools-waterfall-primer.md)

retrieval-anchor-keywords: json 요청 400 왜 나요, spring json 400 cause router, requestbody 400 어디서 갈라요, controller 전에 400 나요, @valid 안 탄 것 같아요, localdate json 400 spring, fetch 는 400 postman 은 됨, body 안 보냈는데 400, required request body is missing spring, 415 랑 400 차이 처음, json parse error basics, what is spring requestbody 400

## 어떤 증상에서 이 문서를 펴는가

- POST JSON 요청을 보내면 컨트롤러 첫 줄도 안 찍히고 바로 `400`이 뜬다.
- 날짜나 시간이 들어간 JSON만 보내면 `400`이 나고 `@Valid` 메시지는 안 보인다.
- 같은 `400`인데 어떤 요청은 validation 같고 어떤 요청은 JSON parse error처럼 보여 처음에 분기가 헷갈린다.
- Postman에서는 되는데 브라우저 fetch나 테스트 코드에서는 JSON 요청이 `400`으로 끝난다.

## 가능한 원인

- `415` 또는 `Unsupported Media Type`이 함께 보이면 body 값보다 `Content-Type`과 `consumes` 계약이 먼저 어긋난 경우다. [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)로 간다.
- `JSON parse error`, `HttpMessageNotReadableException`, `Cannot deserialize`가 보이면 DTO를 만들기 전에 message conversion에서 멈춘 장면이다. [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)로 간다.
- `Required request body is missing`, body가 비어 있음, 브라우저 fetch만 실패 같은 문장이 보이면 JSON 문법보다 **body 자체가 비었는지 / 전송 방식이 달라졌는지** 먼저 본다. 같은 primer 안에서도 empty body 분기부터 확인하는 편이 빠르다.
- `LocalDate`, `LocalTime`, enum, 숫자 타입처럼 특정 필드에서만 자주 깨지면 문법보다 형식 계약이 흔들린 경우가 많다. [Spring `LocalDate`/`LocalTime` JSON 파싱 `400` 자주 나는 형식 모음](./spring-localdate-localtime-json-400-cheatsheet.md)으로 간다.
- `@Valid`를 붙였는데도 field error보다 앞단 `400`처럼 끝나면 validation 전에 body 변환에서 멈췄을 가능성이 높다. [2단계 `@Valid`는 언제 타고 언제 못 타는가](./spring-valid-400-vs-message-conversion-400-primer.md)로 간다.
- 어떤 요청은 컨트롤러 안으로 들어와 `BindingResult`를 보고, 어떤 요청은 아예 못 들어오면 같은 `400`이라도 단계가 다르다. [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나](./spring-bindingresult-local-validation-400-primer.md)로 이어서 본다.

## 한눈에 보기

| 지금 보이는 단서 | 먼저 갈 문서 | 이유 |
| --- | --- | --- |
| `415 Unsupported Media Type` | [415 primer](./spring-requestbody-415-unsupported-media-type-primer.md) | body 값보다 `Content-Type` 계약을 먼저 본다 |
| `JSON parse error`, `Cannot deserialize` | [RequestBody 400 primer](./spring-requestbody-400-before-controller-primer.md) | DTO 생성 전 message conversion 실패다 |
| `Required request body is missing`, body를 안 보낸 것 같음 | [RequestBody 400 primer](./spring-requestbody-400-before-controller-primer.md) | JSON 문법보다 body 유무와 전송 방식 차이를 먼저 확인해야 한다 |
| 날짜·시간 필드에서만 반복 재현 | [LocalDate/LocalTime cheatsheet](./spring-localdate-localtime-json-400-cheatsheet.md) | 형식 계약이 흔들린 장면일 가능성이 높다 |
| `@Valid`가 안 탄 것처럼 보임 | [2단계 `@Valid` primer](./spring-valid-400-vs-message-conversion-400-primer.md) | validation 전에 끊겼는지 확인해야 한다 |
| `BindingResult`까지 들어옴 | [BindingResult primer](./spring-bindingresult-local-validation-400-primer.md) | 이미 DTO 생성 이후 단계다 |

## 헷갈리는 짝 빠른 분기

이 문서는 "JSON 요청인데 `400`이 났다"는 **넓은 입구**다. 아래 다섯 장은 서로 가까워 보여 자주 섞이므로, 검색어 모양에 따라 먼저 집을 문서를 고정하면 retrieval도 덜 흔들린다.

| 헷갈리는 문서 짝 | 이 문서를 먼저 볼 때 | 바로 옆 문서를 먼저 볼 때 |
| --- | --- | --- |
| JSON 요청 `400` 원인 라우터 vs `@RequestBody 400` primer | 아직 `400`이 body 누락인지, parse 실패인지, validation인지 모르겠다 | 이미 `JSON parse error`, `Cannot deserialize`, `Required request body is missing`가 보인다 |
| JSON 요청 `400` 원인 라우터 vs `415` primer | `400`과 `415`가 섞여 보여 first split이 필요하다 | 검색어에 `415`, `Unsupported Media Type`, `Content-Type`이 직접 나온다 |
| JSON 요청 `400` 원인 라우터 vs `@Valid` primer | `@Valid`가 안 탔는지조차 아직 확신이 없다 | DTO는 읽힌 것 같고 "`왜 @Valid 안 타요?`"가 핵심 질문이다 |
| JSON 요청 `400` 원인 라우터 vs `BindingResult` primer | 어떤 요청은 컨트롤러 전에 끝나고 어떤 요청은 메서드 안으로 들어오는지 아직 안 갈랐다 | 이미 `BindingResult`, `MethodArgumentNotValidException`, 로컬 처리 여부가 핵심 단서다 |
| JSON 요청 `400` 원인 라우터 vs 컨트롤러 미진입 라우터 | 문제를 JSON body 축으로 좁혀도 괜찮다 | `302`, `403`, `/login`, filter/security 선차단과도 구분이 안 된다 |

## 빠른 자기 진단

1. 상태 코드가 진짜 `400`인지 `415`인지부터 다시 본다. `415`면 이 문서보다 media type 계약 문서가 더 가깝다.
2. 에러 로그에 `JSON parse`, `Cannot deserialize`, `HttpMessageNotReadableException`이 있으면 validation보다 변환 실패 축으로 바로 분기한다.
3. `Required request body is missing`, body length `0`, fetch 요청만 실패 같은 단서가 있으면 JSON 문법보다 body가 실제로 실렸는지부터 본다.
4. 문제 필드가 날짜, 시간, enum, 숫자처럼 형식 민감한 값인지 본다. 특정 필드만 바꾸면 재현되면 형식 계약 가능성이 높다.
5. 컨트롤러 메서드 안에서 `BindingResult`나 validation 메시지를 실제로 본 적이 있으면 DTO 생성 이후 단계다. 전혀 못 봤다면 앞단에서 끝난 것이다.
6. Postman은 되는데 브라우저나 테스트만 실패하면 body 내용보다 `Content-Type`, 직렬화 방식, 테스트 fixture 차이를 먼저 비교한다.

## 자주 하는 오해

- `400`이면 모두 `@Valid` 실패라고 생각하면 안 된다. DTO를 아예 못 만든 `400`과 validation `400`은 수정 위치가 다르다.
- body가 비어 있거나 전송 방식이 달라 생긴 `400`을 JSON 문법 오류로만 보면 오래 헤맨다. 특히 fetch, 테스트 fixture, `Content-Length: 0` 차이를 같이 봐야 한다.
- body JSON이 눈으로는 멀쩡해 보여도 날짜 형식, enum 문자열, 숫자 타입 하나만 어긋나도 컨트롤러 전에 끝날 수 있다.
- Postman에서 된다고 해서 서버 코드가 항상 맞는 것은 아니다. 브라우저 fetch나 테스트 fixture의 헤더와 직렬화 방식이 다를 수 있다.

## 다음 학습

- 전체 first split을 다시 잡으려면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)를 먼저 본다.
- `415`와 `400`을 자주 헷갈리면 [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)를 바로 잇는다.
- `@Valid`가 왜 어떤 때는 타고 어떤 때는 못 타는지 보려면 [2단계 `@Valid`는 언제 타고 언제 못 타는가](./spring-valid-400-vs-message-conversion-400-primer.md)로 간다.
- 날짜·시간 값이 반복해서 깨지면 [Spring `LocalDate`/`LocalTime` JSON 파싱 `400` 자주 나는 형식 모음](./spring-localdate-localtime-json-400-cheatsheet.md)을 같이 본다.
- body를 안 보낸 것 같은 증상이나 fetch/Postman 차이가 핵심이면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)에서 empty body 분기를 먼저 다시 본다.
- 더 넓은 분기에서 `302`, `403`, `415`, `400`을 함께 자르고 싶으면 [컨트롤러 미진입 원인 라우터](./spring-controller-not-hit-cause-router.md)로 올라간다.

## 한 줄 정리

Spring JSON 요청 `400`은 "body가 틀렸다" 하나로 뭉개지 말고 `415 계약`, `DTO 변환`, `날짜·시간 형식`, `validation 진입 여부` 네 갈래로 먼저 잘라야 빠르게 해결된다.
