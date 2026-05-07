---
schema_version: 3
title: "Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload"
concept_id: network/browser-devtools-reload-hard-reload-disable-cache-primer
canonical: true
category: network
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 87
mission_ids: []
review_feedback_tags:
- browser-reload-cache-mode
- hard-reload-vs-disable-cache
- service-worker-cache-storage-separation
aliases:
- normal reload hard reload
- empty cache and hard reload
- disable cache reload effect
- browser refresh vs hard refresh
- chrome hard reload cache
- reload cache experiment
symptoms:
- hard reload 결과를 평소 사용자 normal reload cache 동작으로 설명한다
- empty cache and hard reload가 cookie나 server session까지 지운다고 오해한다
- Disable cache ON과 Service Worker 등록 상태나 Cache Storage 삭제를 같은 효과로 묶는다
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- network/browser-devtools-cache-trace-primer
- network/http-caching-conditional-request-basics
next_docs:
- network/browser-devtools-disable-cache-on-off-experiment-card
- network/browser-cache-toggles-vs-alt-svc-dns-cache-primer
- network/service-worker-vs-http-cache-devtools-primer
- network/browser-devtools-application-storage-1minute-card
- network/http-state-session-cache
linked_paths:
- contents/network/browser-devtools-cache-trace-primer.md
- contents/network/browser-devtools-disable-cache-on-off-experiment-card.md
- contents/network/http-caching-conditional-request-basics.md
- contents/network/http-state-session-cache.md
- contents/network/service-worker-vs-http-cache-devtools-primer.md
- contents/network/browser-devtools-application-storage-1minute-card.md
- contents/security/session-cookie-jwt-basics.md
confusable_with:
- network/browser-devtools-disable-cache-on-off-experiment-card
- network/browser-cache-toggles-vs-alt-svc-dns-cache-primer
- network/service-worker-vs-http-cache-devtools-primer
- network/http-state-session-cache
- network/browser-devtools-application-storage-1minute-card
forbidden_neighbors: []
expected_queries:
- "normal reload hard reload empty cache and hard reload 차이를 cache 관찰 기준으로 설명해줘"
- "Hard reload에서 200이 보이면 평소 사용자도 항상 새 body를 받는다는 뜻이야?"
- "Disable cache ON이 Service Worker나 Cache Storage까지 지우는지 구분해줘"
- "empty cache and hard reload가 로그인 cookie와 server session을 지우는지 알려줘"
- "새로고침 모드와 Cache-Control ETag 304 판독을 어떤 순서로 연결해?"
contextual_chunk_prefix: |
  이 문서는 normal reload, hard reload, empty cache and hard reload,
  DevTools Disable cache ON을 HTTP cache 관찰 조건으로 분리하고 cookie,
  session, Service Worker, Cache Storage와 섞지 않게 하는 beginner primer다.
---
# Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload

> 한 줄 요약: 같은 URL도 `normal reload`, `hard reload`, `empty cache and hard reload`, `Disable cache` ON 여부에 따라 cache 신호가 달라지므로, 먼저 "사용자 기본선인지 실험 스위치 영향인지"를 분리해서 본다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
- [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)
- [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md)
- [Security: Session / Cookie / JWT basics](../security/session-cookie-jwt-basics.md)
- [카테고리 README](./README.md#브라우저--쿠키--캐시에서-막히면-여기서-시작)

retrieval-anchor-keywords: normal reload, hard reload, empty cache and hard reload, disable cache reload effect, disable cache service worker state, disable cache cache storage, devtools reload cache, chrome hard reload, browser refresh vs hard refresh, empty cache hard reload meaning, disable cache checkbox meaning, disable cache clears service worker, disable cache 뭐예요, 처음 배우는데 disable cache service worker, 왜 disable cache인데 from serviceworker

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 멘탈 모델](#먼저-잡는-멘탈-모델)
- [`Disable cache`가 지우지 않는 것](#disable-cache가-지우지-않는-것)
- [이 문서가 일부러 미루는 질문](#이-문서가-일부러-미루는-질문)
- [같은 URL 1분 분기표](#같은-url-1분-분기표)
- [reload 모드와 진짜 cache 정책을 분리하는 1표](#reload-모드와-진짜-cache-정책을-분리하는-1표)
- [같은 `app.js`로 보는 작은 예시](#같은-appjs로-보는-작은-예시)
- [자주 하는 오해](#자주-하는-오해)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 잡는 멘탈 모델

새로고침 3개를 **같은 URL에 다시 들어가는 세 가지 태도**로 보면 덜 헷갈린다.

- `normal reload`는 "평소처럼 다시 열어 본다"
- `hard reload`는 "이미 가진 사본이 있어도 더 강하게 다시 확인하거나 다시 받는다"
- `empty cache and hard reload`는 "브라우저 cache를 먼저 비우고, 그 상태로 강하게 다시 받는다"

핵심은 이것이다.

- `normal reload`는 평소 사용자 흐름에 가장 가깝다
- `hard reload`는 강한 재요청 실험에 가깝다
- `empty cache and hard reload`는 "기존 사본이 없는 상태"까지 일부러 만든다

그래서 cache trace를 읽기 전 첫 질문은 "`이 줄이 어떻게 만들어졌나`"다.
같은 URL이라도 새로고침 방식이 다르면 `200`, `304`, `from memory cache`, `from disk cache`가 다르게 보일 수 있다.

## reload가 바꾸는 것과 안 바꾸는 것

초급자가 특히 자주 섞는 질문은 "`hard reload` 했더니 로그인도 풀린 거예요?`"다. 대부분의 경우 reload는 **HTTP cache 관찰 조건**을 더 크게 흔들고, cookie/session 자체를 없애는 동작은 아니다.

| 지금 누른 것 | 먼저 바뀌는 축 | 보통 그대로인 것 | 헷갈리면 다음 문서 |
|---|---|---|---|
| `normal reload` | 같은 URL 재요청 방식 | cookie 저장, 서버 session 유무 | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) |
| `hard reload` | cache hit 감소, 재검증/재다운로드 증가 가능성 | login cookie 자체, 서버 session 자체 | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |
| `empty cache and hard reload` | browser HTTP cache 비움 + 강한 재요청 | cookie 저장소, 서버가 기억하는 로그인 상태 | [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md) |
| `Disable cache` ON | DevTools 열린 동안 cache 재사용 실험 | response 헤더의 원래 cache 정책 의미 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |

짧게 자르면 아래처럼 기억하면 된다.

- reload는 주로 `body를 다시 받았나` 질문을 흔든다.
- cookie/session은 `누가 로그인했나` 질문이다.
- 둘이 동시에 보여도 같은 버튼 효과로 묶지 않는다.

## `Disable cache`가 지우지 않는 것

여기서 초급자가 특히 많이 오해하는 문장은 "`Disable cache` 켰으니 Service Worker도 지워졌죠? Cache Storage도 비워졌죠?"다. 보통 아니다.

`Disable cache`는 **DevTools가 열린 동안 HTTP cache 재사용을 덜 보게 만드는 실험 스위치**에 가깝고, Service Worker 등록 상태나 Application 탭의 Cache Storage entry를 자동으로 비우는 버튼으로 읽으면 빠르다.

| 내가 헷갈린 대상 | `Disable cache` ON이 보통 하는 일 | 보통 하지 않는 일 | 어디서 따로 확인하나 |
|---|---|---|---|
| HTTP cache | 같은 URL의 cache hit 관찰을 흔든다 | 서버 cache 정책 자체를 바꾸지 않는다 | Network row, `Cache-Control`, `ETag`, `304` |
| Service Worker 등록/개입 | SW가 있어도 HTTP cache 실험과 별도로 남아 있을 수 있다 | 등록 해제, scope 삭제, fetch handler 제거 | Application > Service Workers, `from ServiceWorker` row |
| Cache Storage | entry가 보여도 그대로 남아 있을 수 있다 | Cache Storage key 자동 삭제 | Application > Cache Storage |

짧게 외우면 아래 3줄이면 된다.

- `Disable cache` = HTTP cache 실험 스위치
- Service Worker 등록 상태 = 별도 축
- Cache Storage entry 존재 여부 = 또 다른 별도 축

그래서 `Disable cache` ON인데도 `from ServiceWorker`가 보이거나, Application 탭에 Cache Storage key가 그대로 남아 있어도 모순이 아니다. 이 장면은 "`Disable cache`가 안 먹었다"보다 "`HTTP cache 실험`과 `SW/Cache Storage 상태`를 같은 상자로 읽었다" 쪽에 더 가깝다.

## 이 문서가 일부러 미루는 질문

이 primer는 `reload`와 HTTP cache 관찰 조건까지만 다룬다. 아래 질문은 여기서 끝까지 파지 않고 관련 문서로 넘긴다.

- "`Disable cache`를 켰는데 왜 아직 `h2`예요?`"는 cache보다 protocol/discovery 질문이므로 [Browser Cache Toggles vs Alt-Svc DNS Cache Primer](./browser-cache-toggles-vs-alt-svc-dns-cache-primer.md)로 간다.
- "`from ServiceWorker`도 같은 cache예요?`"는 응답 주체가 다른 질문이므로 [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)로 분리한다.
- "`304`가 왜 나왔는지 validator까지 보고 싶어요`"는 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)로 내려간다.
- "쿠키, 세션, 로그인 유지까지 같이 흔들린 것 같아요"는 [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)로 넘긴다.

## 처음 헷갈릴 때 30초 체크

초급자가 실제로 자주 묻는 말은 "`hard reload`하니 `200`인데 평소엔 `304`예요. 뭐가 진짜예요?"에 가깝다. 이때는 `정답 찾기`보다 `어떤 조건에서 본 결과인가`를 먼저 분리한다.

| 지금 본 장면 | 먼저 내릴 결론 | 바로 이어서 볼 것 |
|---|---|---|
| `normal reload`에서 `304` | 평소 반복 방문에서 재검증이 일어났을 수 있다 | response의 `Cache-Control`, `ETag` |
| `hard reload`에서 `200` | 강제 재요청 실험 영향이 섞였을 수 있다 | 같은 URL을 `normal reload`로 다시 비교 |
| `empty cache and hard reload`에서 `200` | 기존 cache를 비운 뒤 다시 받은 것이다 | 이 결과를 평소 사용자 흐름처럼 말하지 않기 |
| `Disable cache` ON에서 항상 `200` | checkbox가 cache 재사용을 흔들고 있을 수 있다 | `Disable cache` OFF로 되돌려 기준선 다시 보기 |

짧게 외우면 아래 한 줄이면 충분하다.

- `normal reload`는 기준선
- `hard reload`는 실험
- `empty cache and hard reload`는 cache를 비운 실험
- `Disable cache` ON은 별도 실험 스위치

## 같은 URL 1분 분기표

| 내가 한 행동 | 같은 URL에서 먼저 보는 질문 | 초급자 첫 결론 | 자연 사용자 흐름으로 바로 말해도 되나 |
|---|---|---|---|
| `normal reload` | 평소 반복 방문처럼 cache hit나 `304`가 보이나 | 기본 관찰 출발점 | 대체로 예 |
| `hard reload` | 기존 hit가 사라지고 재검증/재다운로드가 늘어났나 | 강제 확인 실험일 수 있음 | 바로 단정하면 안 됨 |
| `empty cache and hard reload` | 이전 cache 흔적 없이 거의 처음 방문처럼 보이나 | cache를 비운 실험 결과일 수 있음 | 아니오 |

아주 짧은 규칙:

1. 평소 동작을 보려면 `normal reload`부터 본다.
2. 차이를 강하게 보고 싶으면 그다음 `hard reload`를 본다.
3. cache 자체를 비운 실험은 마지막에 따로 본다.

초급자용 한 줄 구분:

- `normal reload` = 기본선
- `hard reload` = 강제 확인
- `empty cache and hard reload` = 기존 사본 제거 후 새로 받기

그리고 `Disable cache`는 reload 버튼 이름이 아니라, **DevTools가 열린 동안 HTTP cache 재사용을 흔드는 별도 실험 스위치**다.
즉 "어떤 reload를 눌렀는가"와 "checkbox가 켜져 있었는가"는 다른 축이다.

## reload 모드와 진짜 cache 정책을 분리하는 1표

이 표는 초급자가 가장 많이 섞는 두 질문을 분리하려고 만든다.

- 질문 A: 내가 누른 reload 모드나 `Disable cache`가 관찰 결과를 흔들었나
- 질문 B: 서버가 보낸 `Cache-Control`, `ETag`, `Last-Modified` 같은 **진짜 cache 정책**이 무엇이었나

| 구분 축 | `normal reload` | `hard reload` | `empty cache and hard reload` | `Disable cache` ON |
|---|---|---|---|---|
| 무엇을 바꾸나 | 평소 사용자 reload에 가깝다 | 같은 URL을 더 강하게 다시 요청해 본다 | 브라우저 cache를 비우고 강하게 다시 요청한다 | DevTools가 열린 동안 HTTP cache 재사용을 실험적으로 줄인다 |
| 먼저 읽을 결론 | 기본선 | 강제 재요청 실험 | cache 비우기 실험 | checkbox 영향이 섞인 실험 |
| 이 결과만으로 진짜 cache 정책을 단정해도 되나 | 비교적 안전하다 | 아니오 | 아니오 | 아니오 |
| 진짜 cache 정책은 어디서 보나 | `Cache-Control`, `ETag`, `Last-Modified`, `304` | 같음 | 같음 | 같음 |
| 초급자 메모 | 실사용자와 가장 비슷하다 | hit가 줄어도 정책 자체가 바뀐 건 아닐 수 있다 | 첫 방문처럼 보여도 정책이 사라진 건 아니다 | `no-store`와 checkbox 효과를 같은 뜻으로 읽지 않는다 |

한 줄로 압축하면 이렇다.

- reload 모드와 `Disable cache`는 **관찰 조건**
- `Cache-Control`, `ETag`, `Last-Modified`, `304`는 **캐시 정책과 재검증 단서**

그래서 `hard reload`에서 `200`만 봤다고 "원래 캐시가 없다"고 말하면 빠르고, `Disable cache` ON에서 `from disk cache`가 안 보였다고 "`Cache-Control: no-store`였다"고 말해도 빠르다.
정책 결론은 항상 헤더와 validator 쪽에서 다시 확인해야 한다.

## 같은 `app.js`로 보는 작은 예시

같은 정적 파일 `app.js`를 본다고 하자.

| 순서 | 내가 한 행동 | DevTools에서 먼저 보일 수 있는 것 | 첫 해석 |
|---|---|---|---|
| 1 | 첫 방문 | `200 OK` | 원본을 처음 받음 |
| 2 | `normal reload` | `from memory cache` / `from disk cache` / validator + `304` | 평소 cache 동작 관찰 |
| 3 | `hard reload` | 다시 `200`, 또는 이전보다 강한 재요청 흔적 | 강제 확인 영향이 섞였을 수 있음 |
| 4 | `empty cache and hard reload` | 다시 `200`, 이전 hit 흔적 사라짐 | 기존 cache를 비우고 새로 받음 |

이 표에서 초급자가 먼저 기억할 문장은 하나면 충분하다.

`2`번은 "평소 브라우저가 어떻게 행동하는가"를 보는 단계이고, `3`번과 `4`번은 "그 평소 행동을 일부러 흔들어 본 단계"다.

같은 URL 실험표로 다시 압축하면 아래처럼 읽으면 된다.

| 질문 | `normal reload` | `hard reload` | `empty cache and hard reload` |
|---|---|---|---|
| 기존 cache hit가 남아 보이나 | 남을 수 있다 | 줄어들 수 있다 | 거의 사라진다 |
| `304` 같은 재검증이 보일 수 있나 | 예 | 보일 수 있지만 해석이 더 조심스럽다 | 기준 cache가 비워져 비교값이 약하다 |
| "실사용자와 비슷한가" | 가장 가깝다 | 덜 가깝다 | 가장 덜 가깝다 |
| 언제 쓰나 | 기본선 확인 | 강제 재요청 차이 확인 | cache 비운 뒤 첫 상태 재현 |

## 자주 하는 오해

### `hard reload`와 `empty cache and hard reload`를 같은 뜻으로 말한다

둘 다 cache 관찰을 흔들 수 있지만 같은 버튼은 아니다.

- `hard reload`는 한 번의 강한 재요청에 가깝다
- `empty cache and hard reload`는 cache를 먼저 비우는 단계가 추가된다

### `empty cache and hard reload` 결과를 실사용자 흐름처럼 말한다

가장 흔한 오해다.

- 이 동작은 실험용이다
- 먼저 `normal reload` 결과를 기준선으로 봐야 한다

### `Disable cache` ON 결과를 서버 cache 정책으로 말한다

이것도 자주 섞인다.

- `Disable cache`는 DevTools 실험 스위치다
- 서버가 `no-store`, `no-cache`, `max-age` 중 무엇을 보냈는지는 response header로 다시 봐야 한다

### `normal reload`에서 `304`가 나오면 cache가 안 된다고 생각한다

아니다.

- `304`는 서버에 다시 물어봤다는 뜻이다
- body는 기존 cache 사본을 계속 쓸 수 있다

### `Protocol` 열부터 보고 H2/H3 문제로 점프한다

초급 단계에서는 아직 빠르다.

- 먼저 reload 방식과 cache 신호를 분리한다
- `h2`/`h3` 같은 전송 경로 질문은 그 다음 단계다
- 버전 선택이 궁금하면 cache 결론을 먼저 적고, 프로토콜 follow-up 문서로 따로 내려간다

### `from ServiceWorker` 장면도 같은 표로 읽는다

그 경우는 HTTP cache만의 질문이 아닐 수 있다.
응답 주체부터 분리하려면 [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)를 먼저 본다.

## 다음 한 걸음

- `304`, `ETag`, `Cache-Control` 자체가 아직 헷갈리면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- `memory cache`, `disk cache`, `revalidation` 문구를 DevTools row에서 읽고 싶으면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- 저장소/쿠키/세션 질문이 섞이면 [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
- 로그인 유지와 브라우저 저장소 위치가 같이 헷갈리면 [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md)

## 한 줄 정리

같은 URL이라도 `normal reload`는 기본선, `hard reload`는 강제 확인, `empty cache and hard reload`는 cache를 비운 실험이므로 세 결과를 같은 뜻으로 묶으면 안 된다.
