# Conditional Write Status Code Bridge

> 한 줄 요약: conditional write에서 `428`은 "조건을 꼭 보내라", `412`는 "보낸 조건이 깨졌다", `409`는 "최신 상태로 다시 봐도 이 동작 자체가 충돌한다"로 나누면 초보자 혼동이 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- [Write Order vs Precondition Primer](./write-order-vs-precondition-primer.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md)
- [Strong vs Weak ETag: validator 정밀도와 cache correctness](../network/strong-vs-weak-etag-validator-precision-cache-correctness.md)
- [409 vs 422 선택 기준 짧은 가이드](../software-engineering/http-409-vs-422-selection-guide.md)

retrieval-anchor-keywords: conditional write status code bridge, 409 vs 412 vs 428, conditional write beginner, if-match status code, precondition required vs precondition failed, optimistic concurrency status code, stale save status code, etag mismatch 412, missing if-match 428, conflict after latest read 409, 처음 409 412 헷갈림, 왜 428 나와요, conditional patch api guide, write precondition response code, optimistic lock 409 412 428

---

## 먼저 잡는 멘탈 모델

conditional write에서 서버는 세 단계로 생각하면 된다.

1. "이 API는 조건부 저장이 필수인가?"
2. "그 조건을 요청이 실제로 보냈는가?"
3. "보낸 조건이 현재 상태와 아직 맞는가?"

여기서 상태 코드는 보통 이렇게 갈린다.

- `428 Precondition Required`: 이 API는 조건부 저장이 필수인데, 아예 `If-Match`나 `expected_version`을 안 보냈다.
- `412 Precondition Failed`: 조건은 보냈지만, 내가 읽고 온 기준선이 이미 낡았다.
- `409 Conflict`: 최신 상태를 다시 읽고 와도 이 동작 자체가 현재 상태와 충돌한다.

짧게 외우면:

- `428` = 조건을 안 가져왔다
- `412` = 조건이 깨졌다
- `409` = 조건이 맞아도 동작이 충돌한다

비유로 보면:

- `428`은 "안전벨트 없이 출발하려 한다"
- `412`는 "표를 들고 왔지만 이미 지난 열차 표다"
- `409`는 "최신 표로 와도 이 칸은 이미 만석이다"

이 비유는 입문용이다. 실제 구현에서는 HTTP 헤더 대신 `expected_version` 필드를 쓰거나, 팀 정책상 `428` 대신 `400`/`409`를 택할 수도 있다. 중요한 것은 숫자 자체보다 "누락", "stale", "도메인 충돌"을 분리해 주는 계약이다.

## 한눈에 비교

| 코드 | 서버가 먼저 본 질문 | 초보자용 해석 | 호출자 다음 행동 |
|---|---|---|---|
| `428 Precondition Required` | "이 API는 조건부 write인데, 조건이 아예 없나?" | 안전벨트 없는 저장 요청 | 먼저 최신 version/ETag를 읽고 조건을 붙여 다시 보냄 |
| `412 Precondition Failed` | "보낸 `If-Match`/`expected_version`이 아직 유효한가?" | 예전 화면 기준 저장 시도 | 최신 상태 재조회 후 다시 판단 |
| `409 Conflict` | "최신 상태 기준으로 봐도 이 명령이 현재 상태와 충돌하나?" | stale 문제를 넘어서 도메인 충돌 | payload나 사용자 행동 자체를 바꿔야 할 수 있음 |

표를 한 문장으로 줄이면 이렇다.

> `428`은 "조건부터 가져와", `412`는 "그 조건은 이미 늦었어", `409`는 "최신 기준으로도 지금은 안 돼"다.

## 같은 흐름으로 보기

### 장면 1. 조건 없이 저장을 시도함

```http
PATCH /profiles/42
Content-Type: application/json

{
  "nickname": "neo"
}
```

이 API가 "오래 열린 편집 화면 overwrite 방지"를 위해 conditional write를 강제한다면, 서버는 이렇게 답할 수 있다.

```http
HTTP/1.1 428 Precondition Required
```

이때 핵심은 "값이 틀렸다"가 아니라 "조건 없는 저장 자체를 받지 않는다"는 계약이다.

### 장면 2. 조건은 보냈지만 기준선이 낡음

```http
PATCH /profiles/42
If-Match: "profile-v7"
Content-Type: application/json

{
  "nickname": "neo"
}
```

하지만 현재 서버 상태가 이미 `profile-v8`이라면:

```http
HTTP/1.1 412 Precondition Failed
```

여기서는 "조건부 write라는 방식"은 맞았다.
문제는 그 조건이 stale하다는 점이다.

### 장면 3. 최신 상태를 읽고 와도 도메인 충돌이 남음

최신 cart를 다시 읽어 보니 쿠폰이 이미 소진됐거나, 주문이 이미 `SHIPPED`라서 취소 자체가 불가능할 수 있다.
이때는 precondition 문제가 아니라 현재 비즈니스 상태 충돌이다.

```http
HTTP/1.1 409 Conflict
```

즉 `409`는 "다시 읽고 와도 같은 명령으로는 안 풀리는 충돌"에 더 가깝다.

## 초보자용 결정 순서

아래 순서로 물으면 대부분 갈라진다.

1. 이 API가 lost update 방지를 위해 conditional write를 강제하나?
2. 그런데 이번 요청이 `If-Match`/`expected_version` 없이 왔나?
3. 그렇다면 `428`
4. 조건은 보냈는데 현재 version/ETag와 안 맞나?
5. 그렇다면 `412`
6. 최신 상태 기준으로도 쿠폰 소진, 이미 배송됨, 이미 취소됨 같은 충돌이 남나?
7. 그렇다면 `409`

처음이라 "`왜 409랑 412가 둘 다 충돌처럼 들리죠?`"가 헷갈리면 이렇게 다시 물으면 된다.

- 최신 상태를 다시 읽으면 같은 요청이 풀릴까?
- 풀리면 `412` 쪽
- 안 풀리고 요청 의미나 사용자 선택을 바꿔야 하면 `409` 쪽

## 장바구니 예시로 한 번에 보기

| 상황 | 추천 | 이유 |
|---|---|---|
| `PATCH /carts/123`에 `If-Match` 없이 수량 변경 요청 | `428` | cart 변경 API가 conditional write 강제 정책인데 조건이 없음 |
| `If-Match: "cart-v12"`를 보냈지만 현재는 `cart-v13` | `412` | 예전 장바구니 기준 저장 시도 |
| 최신 cart를 다시 읽었더니 쿠폰이 이미 만료됨 | `409` | stale mismatch가 아니라 최신 상태에서도 충돌 |

초보자가 자주 섞는 지점은 이것이다.

- 쿠폰 만료는 보통 `412`가 아니라 `409` 쪽에 가깝다.
- `If-Match` 누락은 `409`로 뭉개지기 쉽지만, API 계약을 선명하게 하려면 `428`이 더 설명적일 수 있다.
- `412`는 "네가 본 기준선이 낡았다"는 신호이지, "요청 내용이 나쁘다"는 뜻이 아니다.

## 관리자 정책 편집 예시

| 상황 | 추천 | 이유 |
|---|---|---|
| 정책 저장 API가 `If-Match`를 필수로 정했는데 헤더 없이 저장 | `428` | 오래 열린 화면 overwrite 방지 계약을 아예 지키지 않음 |
| `If-Match: "policy-v7"`로 저장했지만 현재는 `policy-v8` | `412` | 다른 관리자가 먼저 바꿔서 기준선이 깨짐 |
| 최신 `policy-v8`을 다시 읽고도 "이미 비활성화된 플래그를 또 비활성화" 같은 비즈니스 충돌 | `409` | 최신 상태에서도 명령 의미가 충돌 |

여기서 beginner 포인트는:

- "편집 화면 stale save"는 먼저 `412`를 떠올린다.
- "조건 없는 저장 금지 정책"이 있다면 그 앞단에 `428`이 있다.
- "최신 상태에서도 허용 불가"는 `409`다.

## 흔한 혼동

- `412`와 `409`를 둘 다 "충돌"이라고만 이해하면 클라이언트 다음 행동이 흐려진다.
  - `412` 뒤에는 보통 재조회와 재판단이 먼저다.
  - `409` 뒤에는 비즈니스 규칙 설명이나 다른 사용자 선택지가 먼저다.
- `428`을 생략하고 모든 조건 누락을 `400`이나 `409`로 보내는 팀도 있다.
  - 가능은 하지만 "이 API는 조건부 저장이 필수"라는 계약 신호는 약해진다.
  - 즉 `428`은 자주 쓰이는 선택지이지, 모든 제품과 프레임워크가 반드시 그렇게 해야 하는 규칙은 아니다.
- `412`가 나오면 자동 재시도하면 된다고 생각하기 쉽다.
  - 위험하다. payload 자체가 stale read 기반 판단일 수 있다.
- `409`를 보면 항상 optimistic lock이라고 생각하기 쉽다.
  - 아니다. `409`는 최신 상태 기준으로도 남는 비즈니스 충돌을 표현할 때 더 자주 유용하다.

## 최소 응답 계약 예시

```json
{
  "error": {
    "code": "PRECONDITION_FAILED",
    "message": "cart version is stale",
    "currentVersion": 13
  }
}
```

초보자 관점에서 더 중요한 것은 숫자만 던지지 않는 것이다.
특히 conditional write API는 아래 힌트를 같이 주면 재시도 방향이 선명해진다.

| 코드 | 같이 주면 좋은 힌트 |
|---|---|
| `428` | `If-Match required`, `expected_version required` |
| `412` | `currentVersion`, 최신 재조회 링크 또는 merge 필요 신호 |
| `409` | 어떤 규칙과 충돌했는지 설명하는 안정적인 `error.code` |

## 어디와 이어 보나

- "read 뒤 write precondition 자체"를 먼저 이해하려면 [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- "write 순서 보호와 precondition을 구분"하려면 [Write Order vs Precondition Primer](./write-order-vs-precondition-primer.md)
- "DB row version / compare-and-set 구현"으로 내려가려면 [Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md)

처음 읽는 단계의 안전한 다음 질문은 이것이다.

- "`왜 stale save를 막으려면 read 뒤 write가 한 묶음처럼 보이나요?`" -> [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
- "`409 말고 422를 쓰는 장면은 언제예요?`" -> [409 vs 422 선택 기준 짧은 가이드](../software-engineering/http-409-vs-422-selection-guide.md)
- "`ETag랑 DB version column은 어떻게 이어지나요?`" -> [Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md)

## 한 줄 정리

conditional write API에서 `428`은 조건 누락, `412`는 조건 불일치, `409`는 최신 상태 기준으로도 남는 도메인 충돌로 보면 된다.
