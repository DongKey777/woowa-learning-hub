# 421 Non-Idempotent Retry Guardrail Primer

> 한 줄 요약: `421 Misdirected Request`는 "다른 connection으로 다시 보내 볼 수 있음"을 뜻할 뿐, `POST`나 side-effect 요청을 공짜로 재실행해도 된다는 뜻은 아니다.

**난이도: 🟢 Beginner**

관련 문서:

- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md)
- [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
- [Idempotency Keys and Safe HTTP Retries](../language/java/httpclient-idempotency-keys-safe-http-retries.md)

retrieval-anchor-keywords: 421 non idempotent retry, 421 POST retry, 421 free replay 아님, 421 side effect request, 421 misdirected request idempotency, 421 retry guardrail, 421 unsafe replay, 421 post duplicate order, 421 payment retry, 421 idempotency key, 421 beginner primer, wrong connection retry vs business retry, 421 should not replay POST, 421 멱등성, 421 재시도 가드레일

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [421과 free replay를 한 표로 보면](#421과-free-replay를-한-표로-보면)
- [초보자용 예시: 무엇은 다시 보내도 되고 무엇은 조심해야 하나](#초보자용-예시-무엇은-다시-보내도-되고-무엇은-조심해야-하나)
- [POST라도 다시 보낼 수 있는 경우](#post라도-다시-보낼-수-있는-경우)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

`421` 문서를 읽고 나면 초보자가 자주 이렇게 묻는다.

- "`421`이면 어차피 잘못된 connection이었으니 그냥 다시 보내면 되나요?"
- "`POST /orders`도 `GET`처럼 그냥 replay해도 되나요?"
- "브라우저가 같은 URL을 다시 보냈다면, 우리 API client도 `POST`를 자동 재시도해도 되나요?"

여기서 가장 먼저 끊어야 할 오해는 하나다.

**`421`은 connection 복구 힌트이지, 비멱등 요청을 멱등하게 바꿔 주는 마법이 아니다.**

---

## 먼저 잡는 mental model

아주 짧게는 이렇게 기억하면 된다.

- `421`: "이 요청은 이 connection으로 처리하지 않겠다"
- retry: "그러면 다른 connection으로 다시 보내 볼 수 있다"
- guardrail: "하지만 같은 요청을 한 번 더 보내도 비즈니스 결과가 하나로 수렴하는지는 별도 문제다"

비유하면:

- `421`은 "문을 잘못 들어왔으니 옆문으로 가세요"
- 멱등성은 "옆문으로 다시 들어가도 주문이 한 건만 생기나요?"를 묻는 문제다

즉 질문이 두 개다.

1. connection이 잘못됐나?
2. 다시 보내도 결과가 한 번으로 수렴하나?

`421`은 1번에 답하고, 멱등성은 2번에 답한다.

---

## 421과 free replay를 한 표로 보면

| 질문 | `421`이 답해 주는 것 | `421`이 답해 주지 않는 것 |
|---|---|---|
| 왜 실패했나 | 이 connection 문맥이 틀렸을 수 있음 | 서버가 이미 business side effect를 만들었는지 |
| 무엇을 바꿔야 하나 | 다른 connection, 다른 authority 경로 | 중복 주문, 중복 결제, 중복 메일 방지 규칙 |
| 다시 보내도 되나 | 같은 요청을 **다른 connection**에서 시도할 근거가 될 수 있음 | 그 재전송이 **중복 효과 없이** 끝난다는 보장 |
| 초보자 결론 | transport 복구 신호 | business 안전 보장 아님 |

가장 짧은 규칙은 아래 두 줄이다.

- `GET`/`HEAD`처럼 원래 replay 부담이 작은 요청은 `421` 후 새 connection 재시도가 비교적 자연스럽다.
- `POST`/side-effect 요청은 `421`이 떠도 **dedup 계약 없이 공짜 replay로 취급하면 안 된다.**

---

## 초보자용 예시: 무엇은 다시 보내도 되고 무엇은 조심해야 하나

| 요청 | 보통의 감각 | 이유 |
|---|---|---|
| `GET /products/42` | 대체로 다시 보내도 됨 | 조회라서 같은 요청을 다시 보내도 상태 변화가 없다 |
| `PUT /users/42/profile`로 같은 전체 본문 재전송 | 비교적 안전 | 같은 표현으로 덮어쓰면 보통 같은 최종 상태로 수렴한다 |
| `DELETE /cart/items/7` | 비교적 안전 | 두 번 보내도 보통 "그 항목이 없다" 상태로 수렴한다 |
| `POST /orders` | 조심 | 두 번 보내면 주문이 두 건 생길 수 있다 |
| `POST /payments/approve` | 매우 조심 | 두 번 보내면 승인/청구가 중복될 수 있다 |
| `POST /emails/send` | 조심 | 사용자는 메일을 두 통 받았는데 서버 trace만 보면 복구처럼 보일 수 있다 |

이 표의 핵심은 method 이름만 외우는 것이 아니다.

- `GET`은 주로 조회라서 replay 부담이 작다.
- `POST`는 "새 일 하나를 시작"하는 경우가 많아서 duplicate side effect 위험이 크다.

그래서 `421 -> retry`를 볼 때 초보자는 먼저 이렇게 묻는 편이 안전하다.

```text
이 요청은 조회 재시도인가?
아니면 주문/결제/발송처럼 같은 요청이 두 번 실행되면 곤란한 작업인가?
```

---

## POST라도 다시 보낼 수 있는 경우

`POST`라고 해서 무조건 재시도 금지는 아니다. 다만 아래 같은 장치가 있어야 한다.

| 장치 | 왜 필요한가 | beginner 감각 |
|---|---|---|
| `Idempotency-Key` | 같은 logical operation을 한 번으로 접어 준다 | "같은 결제 시도"라는 표식을 붙인다 |
| 클라이언트가 만든 고정 주문 ID | 서버가 중복 생성 대신 같은 리소스를 찾게 해 준다 | "주문번호가 이미 있으면 새 주문을 만들지 않는다" |
| 서버 dedup 저장소 | 첫 성공 결과를 재사용하거나 중복 실행을 막는다 | "같은 키면 기존 결과를 돌려준다" |
| 명시적 API 계약 | 이 `POST`가 조회성/재생산성 요청인지 문서화한다 | "`POST`지만 보고서 생성 조회처럼 한 번으로 수렴한다" |

예를 들어:

- `POST /payments` + `Idempotency-Key: pay-20260427-001`
- 첫 시도는 `421`
- 클라이언트는 **같은 key, 같은 body**로 다른 connection에서 다시 시도

이 경우 핵심은 "`421`이라서 안전"이 아니라 아래다.

- 같은 logical operation 경계가 보존됐다
- 서버가 duplicate를 새 결제로 만들지 않도록 약속했다

즉 안전성의 주인공은 `421`이 아니라 **멱등 계약**이다.

---

## 자주 헷갈리는 포인트

- "`421`을 받았으니 서버는 아무 일도 안 했겠죠?"
  보통은 wrong-connection 거절 신호로 읽지만, 초보자에게 더 안전한 규칙은 "`POST`는 duplicate 방지 장치가 있을 때만 재전송한다"다.

- "브라우저가 같은 URL을 다시 보냈으니 우리 백엔드 client도 `POST`를 자동 재시도해도 되겠네요?"
  아니다. 브라우저의 connection recovery와 서버 API의 business replay safety는 같은 문제가 아니다.

- "`PUT`, `DELETE`는 무조건 안전하죠?"
  보통 멱등하게 설계하지만, 부수 효과가 섞인 구현이라면 문서와 실제 동작을 확인해야 한다.

- "`POST`면 무조건 재시도 금지인가요?"
  아니다. `Idempotency-Key`, 고정 resource id, dedup 저장소 같은 계약이 있으면 안전하게 재시도할 수 있다.

---

## 한 줄 정리

`421 Misdirected Request`는 "다른 connection에서 다시 시도할 수 있다"는 transport 신호일 뿐이고, `POST`나 side-effect 요청을 공짜로 replay해도 된다는 business 보장은 멱등 계약이 따로 있어야 나온다.
