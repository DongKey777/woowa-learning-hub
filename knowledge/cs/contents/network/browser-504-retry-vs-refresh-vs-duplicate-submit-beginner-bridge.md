---
schema_version: 3
title: Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge
concept_id: network/browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge
canonical: false
category: network
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 85
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- duplicate-submit-guard
- idempotency-boundary
- prg-vs-retry
aliases:
- browser retry after 504
- 504 duplicate submit
- gateway timeout refresh duplicate post
- safe automatic retry basics
- browser refresh after 504
- duplicate form submit after timeout
- post retry confusion
- idempotent vs duplicate submit
- why same order created twice
- 새로고침하면 중복 제출
- 504 뒤 다시 눌러도 되나요
- 처음 보는 gateway timeout
- 504 retry basics
- what is duplicate submit
- browser auto retry vs user refresh
symptoms:
- 504 보고 다시 눌러도 되는지 모르겠어
- 주문이 두 번 생성됐는지 헷갈려
- 새로고침했더니 같은 요청이 또 간 것 같아
intents:
- comparison
prerequisites:
- network/http-methods-rest-idempotency-basics
- network/http-status-codes-basics
next_docs:
- network/edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge
- system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
linked_paths:
- contents/network/browser-devtools-502-504-app-500-decision-card.md
- contents/network/edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge.md
- contents/network/post-redirect-get-prg-beginner-primer.md
- contents/network/http-methods-rest-idempotency-basics.md
- contents/network/timeout-retry-backoff-practical.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
confusable_with:
- network/edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge
- network/post-redirect-get-prg-beginner-primer
forbidden_neighbors:
expected_queries:
- 504를 본 뒤 다시 보내도 안전한지 어떻게 구분하나요?
- 새로고침과 자동 재시도, 중복 제출 위험은 무엇이 다른가요?
- gateway timeout 뒤 주문 요청을 다시 눌러도 되는지 처음 판단하는 법이 궁금해요
- POST timeout 뒤 재클릭하면 중복 요청이 생기나요?
- PRG가 없으면 504 뒤 재전송 위험이 커지나요?
contextual_chunk_prefix: |
  이 문서는 초급 학습자가 504 뒤에 다시 보인 요청을 자동 복구, 사용자
  새로고침, 비멱등 POST 중복 처리 위험으로 나눠 이해하도록 연결하는
  bridge다. 실패 뒤 다시 눌러도 되는지 판단, 같은 URL이 연달아 찍힘,
  조회 재호출과 주문 두 번 생성 구분, 첫 시도가 이미 끝났는지 확인하기
  같은 자연어 paraphrase가 본 문서의 분기 기준에 매핑된다.
---
# Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge

> 한 줄 요약: 브라우저에서 `504 Gateway Timeout`을 본 뒤 같은 URL이 다시 보일 때는 transport 복구, 사용자의 새로고침, 비멱등 `POST` 중복 제출을 서로 다른 질문으로 나눠야 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- [Edge는 `504`인데 App은 `200`? Timeout Budget Mismatch Beginner Bridge](./edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge.md)
- [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md)
- [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: browser retry after 504, 504 duplicate submit, gateway timeout refresh duplicate post, safe automatic retry basics, browser refresh after 504, duplicate form submit after timeout, post retry confusion, idempotent vs duplicate submit, why same order created twice, 새로고침하면 중복 제출, 504 뒤 다시 눌러도 되나요, 처음 보는 gateway timeout, 504 retry basics, what is duplicate submit, browser auto retry vs user refresh

## 핵심 개념

초급자가 먼저 분리해야 할 질문은 세 개다. 특히 `504`를 본 직후에는 "브라우저가 알아서 다시 보내 주겠지"와 "한 번 실패했으니 다시 눌러도 안전하겠지"를 같은 말처럼 취급하지 않는 것이 중요하다.

- **자동 재시도인가?** 브라우저나 client가 transport 복구 차원에서 다시 보냈는가
- **사용자 새로고침인가?** 사용자가 `F5`나 새로고침 버튼으로 같은 URL을 다시 요청했는가
- **중복 제출인가?** 같은 `POST`가 비즈니스 부작용을 한 번 더 만들었는가

이 셋은 모두 "같은 URL이 두 번 보인다"로 보일 수 있지만 뜻이 다르다.

- 자동 재시도는 보통 **전달 경로 복구** 질문이다.
- 새로고침은 **사용자 행동** 질문이다.
- 중복 제출은 **서버 상태가 두 번 바뀌었는가** 질문이다.

짧게 외우면 이렇다.

```text
504는 "기다리던 앞단 창구가 timeout을 선언했다"는 뜻이다.
그 뒤 같은 URL이 다시 보여도
1) 브라우저가 복구한 건지
2) 사용자가 다시 누른 건지
3) POST가 두 번 처리된 건지는 따로 확인해야 한다.
```

초급자용 첫 원칙도 하나 붙여 두면 덜 헷갈린다.

- **브라우저 자동 재시도는 기본값이라고 가정하지 않는다.** 자동 복구가 보이더라도 주로 조회성 `GET`에서 먼저 의심하고, 비멱등 `POST`는 "자동으로 다시 보내도 안전하다"라고 먼저 놓고 보면 안 된다.

## 한눈에 보기

| 장면 | 먼저 붙일 이름 | 초급자 첫 해석 | 바로 다음 확인 |
|---|---|---|---|
| `GET /products`가 짧은 간격으로 두 번 보이고 첫 줄이 `504` | 자동 재시도 후보 | 조회 요청 복구일 수 있다 | method, timing, connection 변화 |
| 사용자가 `504` 화면 뒤 새로고침했고 `GET`이 다시 감 | 사용자 새로고침 | 같은 조회를 다시 시도했다 | DevTools initiator, user action 시점 |
| `POST /orders` 뒤 `504`가 보이고 사용자가 다시 버튼을 눌렀다 | 중복 제출 위험 | 주문이 두 번 생성될 수 있다 | PRG 사용 여부, idempotency key, DB 결과 |
| `POST /orders` 뒤 `303 -> GET /orders/42`가 보인다 | PRG 흐름 | 마지막 화면은 `GET`이라 새로고침이 덜 위험하다 | redirect 응답과 결과 페이지 URL |

가장 안전한 첫 문장은 아래 한 줄이다.

- `GET` 재시도 흔적과 `POST` 중복 제출 위험은 같은 "retry"로 뭉개면 안 된다.

같은 장면을 "누가 다시 보냈나?"로 보면 더 빨리 갈린다.

| 누가 다시 보냈나 | 보통 어떤 요청인가 | 초급자 첫 판단 |
|---|---|---|
| 브라우저/클라이언트가 transport 복구로 다시 보냄 | 조회성 `GET` 후보가 먼저 보임 | duplicate business action보다 전달 복구부터 본다 |
| 사용자가 새로고침이나 버튼 재클릭을 함 | `GET`도 `POST`도 가능 | 마지막 method와 initiator를 본다 |
| 서버가 첫 `POST`를 이미 끝냈는데 사용자가 다시 보냄 | 비멱등 `POST` | 중복 제출 위험으로 본다 |

## 어디서 갈라지나

### 1. 자동 재시도는 transport 복구에 가깝다

초급자 mental model에서는 자동 재시도를 "길이 꼬여서 같은 편지를 다른 길로 다시 보내는 일"로 보면 된다.

이때 중심 질문은 보통 아래다.

- 원래 요청이 `GET`처럼 조회성인가
- connection이나 hop을 바꿔 다시 시도한 흔적인가
- 사용자가 직접 누르지 않았는데도 짧은 간격으로 같은 URL이 다시 보였는가

여기서는 핵심이 **비즈니스 중복 생성**보다 **전달 복구**다. 그래서 beginner는 "`504` 뒤 같은 URL이 또 보였다"만으로 `POST` 중복을 먼저 상상하기보다, 먼저 `Method`와 initiator를 보고 "조회 요청 복구인가?"를 가르는 편이 안전하다.

### 2. 새로고침은 사용자가 새 요청을 만든다

사용자가 `504`를 본 뒤 새로고침하면 브라우저는 새 HTTP 요청을 시작한다. 이건 앞선 실패를 "취소선으로 덮는 행위"가 아니라, **같은 URL에 대한 새 시도**다.

- 마지막 요청이 `GET`이면 보통 조회를 다시 하는 감각이다.
- 마지막 요청이 `POST`였다면 브라우저는 재전송 경고나 중복 제출 위험과 연결될 수 있다.

그래서 새로고침 질문은 "브라우저가 자동으로 복구했나"보다 먼저 **마지막 요청 method가 무엇이었나**를 봐야 한다. `GET` 새로고침은 같은 조회를 다시 시도하는 감각이지만, `POST` 새로고침이나 버튼 재클릭은 곧바로 duplicate submit 질문으로 이어진다.

### 3. 중복 제출은 서버 상태가 두 번 바뀌었는지 본다

중복 제출은 같은 `POST`가 두 번 **처리**되어 주문, 결제, 댓글 같은 side effect가 두 번 생긴 장면을 말한다.

여기서 `504`는 오해를 키운다.

- 사용자는 실패를 봤으니 "아예 안 됐겠지"라고 생각한다.
- 하지만 app은 timeout 뒤늦게 첫 `POST`를 끝냈을 수도 있다.
- 그 상태에서 사용자가 다시 누르면 두 번째 `POST`가 정말로 새 주문을 만들 수 있다.

즉 `504` 뒤 duplicate risk는 retry 버튼 자체보다 **첫 시도가 이미 어디까지 갔는가**와 연결된다. 브라우저 화면에서 실패를 봤다는 사실과 서버가 아무 일도 하지 않았다는 사실은 같은 뜻이 아니다.

## 흔한 오해와 함정

- `504`를 봤으니 서버는 아무 일도 안 했다고 단정한다. 실제로는 [Edge는 `504`인데 App은 `200`? Timeout Budget Mismatch Beginner Bridge](./edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge.md)처럼 app이 뒤늦게 성공했을 수 있다.
- 브라우저는 `POST`도 자동으로 안전하게 재시도해 줄 거라고 생각한다. 비멱등 `POST`는 그런 가정부터 위험하고, 실제로는 사용자 재클릭과 서버 dedup 여부가 더 중요하다.
- 같은 URL이 두 줄 보이면 무조건 브라우저 버그라고 생각한다. method와 timing을 보면 자동 복구, 새로고침, redirect가 갈린다.
- `POST`도 `GET`처럼 다시 보내면 된다고 생각한다. 주문/결제/댓글 생성은 같은 요청 두 번이 곧 두 번 처리일 수 있다.
- PRG를 쓰면 서버 중복 방지가 끝난다고 생각한다. PRG는 새로고침 대상을 `GET`으로 바꾸는 패턴이지, 첫 `POST`와 두 번째 `POST`를 dedup하는 장치는 아니다.
- retry와 refresh를 같은 말로 쓴다. retry는 client 복구 전략일 수 있고, refresh는 사용자가 만든 새 요청이다.

## 실무에서 쓰는 모습

가장 흔한 beginner confusion은 주문 생성 폼이다. 이 예시는 "`504`를 봤는데 다시 눌러도 되나요?"라는 질문에 가장 직접적으로 답한다.

```text
1) POST /orders 전송
2) gateway가 1초에서 timeout -> 브라우저는 504 표시
3) app은 1.3초에 첫 주문 생성 완료
4) 사용자는 실패로 보고 제출 버튼을 다시 누름
5) POST /orders가 한 번 더 감
6) dedup 장치가 없으면 주문이 두 건 생길 수 있음
```

이 장면에서 초급자가 바로 써먹을 분기표는 아래다.

| 관찰 | 뜻 | 안전한 다음 행동 |
|---|---|---|
| `GET` 두 번, 짧은 간격, user click 흔적 없음 | 자동 재시도/복구 후보 | connection, waterfall, status 변화 확인 |
| `POST` 뒤 `303 -> GET` | PRG 흐름 | 새로고침 대상이 `GET`인지 확인 |
| `POST` 뒤 `504`, 다시 `POST` | 중복 제출 위험 | 서버 dedup, idempotency key, 실제 생성 건수 확인 |
| 첫 `504`, app 로그에는 성공 | timeout mismatch 가능성 | 첫 시도 결과를 사용자에게 어떻게 복구할지 설계 확인 |

DevTools에서 초급자가 먼저 볼 최소 칸은 4개면 충분하다.

1. `Method`가 `GET`인지 `POST`인지
2. 첫 줄 `Status`가 `504`인지
3. 두 번째 요청의 간격과 initiator
4. `303` redirect나 결과 `GET`이 있었는지

질문을 더 짧게 줄이면 아래 3단계로 끝난다.

1. 마지막 요청이 `GET`인가 `POST`인가
2. 두 번째 요청을 누가 만들었나: 자동 복구인가, 새로고침인가, 재클릭인가
3. 첫 `POST`가 실제로 처리됐는가: app 로그, 주문 번호, DB 결과가 남았는가

## 안전한 다음 한 걸음

- 브라우저 `504`의 owner를 먼저 가르려면 [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- `504`인데 app은 성공했을 수 있다는 감각을 먼저 잡으려면 [Edge는 `504`인데 App은 `200`? Timeout Budget Mismatch Beginner Bridge](./edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge.md)
- 새로고침을 `POST`가 아닌 `GET`으로 바꾸는 브라우저 패턴은 [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- 어떤 method가 replay 부담이 작은지부터 다시 잡으려면 [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md)
- 서버가 같은 logical operation을 한 번으로 접는 쪽은 [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)

## 한 줄 정리

`504` 뒤 같은 URL이 다시 보여도 그것이 자동 복구인지, 사용자 새로고침인지, 비멱등 `POST` 중복 제출인지는 서로 다른 문제라서 `Method`, `303` 유무, 첫 시도 실제 처리 여부를 따로 갈라 봐야 한다.
