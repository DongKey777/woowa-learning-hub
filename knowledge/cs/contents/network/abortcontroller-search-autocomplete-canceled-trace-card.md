# AbortController 검색 자동완성 `canceled` trace 카드

> 한 줄 요약: 검색 자동완성에서 이전 요청을 `AbortController`로 끊고 마지막 요청만 남기는 trace는 DevTools `canceled`를 백엔드 장애가 아니라 프론트의 의도된 정리 동작으로 읽게 도와주는 대표 패턴이다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)
- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [Browser XHR/fetch vs page navigation DevTools 1분 비교 카드](./browser-fetch-vs-page-navigation-redirect-trace-card.md)
- [Trie (Prefix Search / Autocomplete)](../data-structure/trie-prefix-search-autocomplete.md)
- [Browser E2E Cost vs Signal Checklist](../software-engineering/browser-e2e-cost-vs-signal-checklist.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: abortcontroller autocomplete canceled, search autocomplete canceled trace, devtools canceled not backend bug, xhr canceled on typing, fetch canceled by abortcontroller, search as you type trace, autocomplete request aborted, 왜 canceled가 떠요, 검색창 입력할 때 canceled, frontend intentional cancel, browser network canceled basics, stale request abort trace, what is abortcontroller cancel, canceled before latest 200, autocomplete backend bug 아님

## 핵심 개념

이 카드는 "검색창에 글자를 빨리 입력하면 왜 `canceled`가 여러 줄 보이냐"는 질문에 답하는 **trace 해석 카드**다.

검색 자동완성 UI는 보통 마지막 입력값만 의미가 있다. 그래서 `a`를 치고 바로 `ab`, `abc`를 치면 프론트는 예전 요청 결과가 늦게 도착해 화면을 덮지 않도록 이전 요청을 취소할 수 있다. 이때 DevTools에는 앞 요청들이 `canceled`, 마지막 요청만 `200`으로 남는다.

다만 `canceled`가 보인다고 항상 서버가 아무 일도 안 했다는 뜻은 아니다. 브라우저가 취소를 표시하는 시점은 브라우저/버전과 네트워크 타이밍에 따라 달라질 수 있고, 백엔드가 이미 요청을 받기 시작했을 수도 있다. 이 카드의 핵심은 **"이 trace만으로 백엔드 버그부터 신고하지 말자"**는 1차 판독 기준이다.

## 한눈에 보기

| DevTools에서 보이는 묶음 | 먼저 붙일 해석 | backend 버그로 바로 가면 안 되는 이유 |
|---|---|---|
| `GET /search?q=a -> canceled`<br>`GET /search?q=ab -> canceled`<br>`GET /search?q=abc -> 200` | 마지막 입력만 남기려는 프론트 abort 패턴 후보 | 앞 요청이 낡은 결과라서 의도적으로 정리됐을 수 있다 |
| 같은 path인데 query가 점점 길어짐 | 검색창 입력 흐름 후보 | 중복 호출보다 "이전 키 입력 취소" 설명력이 크다 |
| `Initiator`가 같은 입력 핸들러/컴포넌트 | 같은 UI 이벤트 체인 후보 | 백엔드 재시도보다 프론트 상태 관리 후보가 더 가깝다 |
| 마지막 요청만 response preview에 실제 추천 목록이 있음 | 실제로 사용자에게 필요한 요청은 마지막 1개 | 앞 요청의 `canceled` 자체는 실패라기보다 정리 흔적일 수 있다 |

짧게 외우면 이렇다.

```text
autocomplete는 최신 입력만 중요
이전 요청 canceled + 마지막 200
= 의도된 abort 패턴 후보
```

## trace를 어떻게 읽나

### 1. query가 "입력 순서대로" 길어지는지 본다

가장 먼저 `q=a`, `q=ab`, `q=abc`처럼 query가 입력 순서대로 자라는지 본다. 이 패턴이면 같은 URL 반복 호출이 아니라 **사용자 타이핑 흐름**일 가능성이 높다.

반대로 query가 완전히 같다면 이 카드보다 중복 클릭, effect 두 번 실행, retry 같은 후보를 먼저 봐야 한다.

### 2. 마지막 요청만 성공하는지 본다

자동완성에서는 보통 마지막 요청만 `200`으로 끝나고, 앞 요청은 `canceled`로 남는다. 이건 "앞 요청이 실패해서"가 아니라 **더 최신 입력이 나와서 앞 결과가 쓸모없어졌기 때문**일 수 있다.

특히 응답 속도가 들쭉날쭉한 환경에서는 이전 요청을 안 끊으면 `abc`보다 늦게 도착한 `a` 결과가 화면을 덮는 race condition이 생길 수 있다. `AbortController`는 그 오염을 막는 대표 도구다.

### 3. initiator와 timing을 같이 본다

`Initiator`가 같은 검색 컴포넌트이고, 요청 간격이 수십~수백 ms 수준이면 사람 타이핑 cadence와 잘 맞는다. 이런 장면은 proxy retry나 backend 재시도보다 **프론트 입력 처리** 문맥으로 읽는 편이 안전하다.

브라우저 UI 열 이름은 버전에 따라 조금 다를 수 있지만, beginner가 보는 단서는 대체로 같다.

- query가 점점 길어지는가
- 각 row 간격이 매우 짧은가
- 마지막 row만 결과 body가 있는가
- page navigation 없이 같은 화면에서 계속 발생하는가

## 흔한 오해와 함정

- `canceled`가 여러 줄이니 서버가 에러를 냈다고 단정한다. 자동완성에서는 오히려 정상 UX 후보가 더 흔하다.
- `canceled`면 서버 로그가 절대 없다고 생각한다. 취소 시점에 따라 서버가 요청 시작을 봤을 수도 있다.
- 같은 path 반복 호출을 전부 "중복 버그"로 묶는다. query가 자라는지부터 봐야 한다.
- 마지막 `200`만 보고 앞 `canceled`를 무시한다. 앞줄은 race condition을 막기 위한 프론트 의도를 설명하는 중요한 단서다.
- 이 패턴을 모든 `canceled`에 적용한다. 페이지 이동, 새로고침, 탭 종료로 생긴 `canceled`는 또 다른 문맥이다.

## 실무에서 쓰는 모습

DevTools row가 아래처럼 보이면, 초급자가 팀 채널에 남길 첫 문장은 "백엔드 장애"보다 "프론트가 이전 검색을 의도적으로 정리한 trace 후보"가 된다.

| 순서 | Request | Status | 먼저 적을 메모 |
|---|---|---|---|
| 1 | `GET /api/search?q=a` | `canceled` | 첫 글자 요청은 더 긴 입력이 나와 stale 후보 |
| 2 | `GET /api/search?q=ab` | `canceled` | 두 번째 요청도 최신 입력에게 자리 양보 |
| 3 | `GET /api/search?q=abc` | `200` | 최종 입력 기준 결과만 살아남음 |

프론트 코드는 보통 이런 식으로 보인다.

```javascript
let controller;

async function search(query) {
  controller?.abort();
  controller = new AbortController();

  const response = await fetch(`/api/search?q=${query}`, {
    signal: controller.signal,
  });
  return response.json();
}
```

이 예시는 입문용 단순화다. 실제 구현은 debounce, 로딩 상태, abort 에러 무시 처리까지 함께 들어갈 수 있다. 중요한 건 "이전 요청을 끊는 이유"가 **오래된 결과가 최신 화면을 덮지 못하게 하려는 것**이라는 점이다.

## 더 깊이 가려면

- `canceled` 자체를 브라우저 메모로 먼저 읽는 감각이 아직 약하면 [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)
- DevTools 첫 1분 판독 순서를 다시 고정하려면 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- page 이동 때문에 끊긴 요청과 XHR/fetch 취소를 구분하려면 [Browser XHR/fetch vs page navigation DevTools 1분 비교 카드](./browser-fetch-vs-page-navigation-redirect-trace-card.md)
- 자동완성 자체의 자료구조 배경을 보려면 [Trie (Prefix Search / Autocomplete)](../data-structure/trie-prefix-search-autocomplete.md)
- 이 장면을 꼭 브라우저 E2E로만 잡아야 하는지 테스트 비용을 비교하려면 [Browser E2E Cost vs Signal Checklist](../software-engineering/browser-e2e-cost-vs-signal-checklist.md)

## 한 줄 정리

검색 자동완성에서 query가 길어지며 앞 요청이 `canceled`, 마지막 요청만 `200`으로 끝나는 trace는 백엔드 장애보다 `AbortController` 기반의 의도된 프론트 정리 동작으로 먼저 읽는 것이 맞다.
