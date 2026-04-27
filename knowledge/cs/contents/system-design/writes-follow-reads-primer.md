# Writes-Follow-Reads Primer

> 한 줄 요약: writes-follow-reads는 "내가 보고 판단한 상태가 아직 유효할 때만 write를 받는다"는 규칙이고, version/etag/precondition check로 stale save를 막는 입문용 설계다.

**난이도: 🟢 Beginner**

관련 문서:

- [Conditional Write Status Code Bridge](./conditional-write-status-code-bridge.md)
- [Write Order vs Precondition Primer](./write-order-vs-precondition-primer.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Inventory Reservation System Design](./inventory-reservation-system-design.md)
- [Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md)
- [Version Column Retry Walkthrough](../database/version-column-retry-walkthrough.md)
- [Strong vs Weak ETag: validator 정밀도와 cache correctness](../network/strong-vs-weak-etag-validator-precision-cache-correctness.md)
- [Aggregate Version and Optimistic Concurrency Pattern](../design-pattern/aggregate-version-optimistic-concurrency-pattern.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: writes-follow-reads primer, writes-follow-reads beginner, what is writes-follow-reads, stale write after read, version check after read, precondition check after read, write precondition primer, expected version write, if-match beginner, etag precondition basics, optimistic precondition write, optimistic concurrency beginner, lost update beginner, edit form stale save, cart version mismatch

---

## 핵심 개념

가장 쉬운 mental model은 이렇다.

- read할 때는 "판단 근거가 되는 번호표"를 같이 받는다
- write할 때는 "아직 그 번호표가 유효할 때만 저장해 달라"고 요청한다

예를 들어 사용자가 장바구니를 열었을 때 `cart_version=12`를 봤다면, 쿠폰 적용이나 수량 변경 write는 "`version 12`를 기준으로 계산했다"는 사실을 함께 보내야 한다.
서버는 현재 version이 여전히 `12`일 때만 write를 반영한다.

즉, writes-follow-reads는 "방금 쓴 값이 다시 보이느냐"보다 **내가 보고 판단한 상태를 믿고 써도 되느냐**를 다룬다.
핵심 질문은 이것이다.

> 내가 읽은 상태가 이미 낡았는데도 저장을 받아 버리면, 앞선 변경을 덮거나 잘못된 결정을 굳혀 버리지 않을까?

---

## 먼저 흐름으로 보기

가장 흔한 beginner 버전은 아래 한 줄 계약으로 이해하면 된다.

```text
read 응답: 값 + version(또는 ETag)
write 요청: 새 값 + "나는 version 12를 보고 계산했다"는 precondition
서버 판단: 현재도 12면 저장, 아니면 거절
```

예를 들어 장바구니 화면을 이렇게 열었다고 해 보자.

```http
GET /carts/123
ETag: "cart-v12"

{
  "items": [
    {"sku": "A", "qty": 1}
  ],
  "totalPrice": 12000
}
```

이후 쿠폰 적용은 새 쿠폰 코드만 보내는 게 아니라, **내 계산 근거가 된 상태 토큰**도 같이 보내야 한다.

```http
PATCH /carts/123/coupon
If-Match: "cart-v12"

{
  "couponCode": "SPRING10"
}
```

이 계약이 바로 writes-follow-reads의 beginner entry다.
버전 번호를 쓰든, `ETag`를 쓰든, `expected_version` 필드를 쓰든 뜻은 같다.

---

## 한눈에 보기

| 상황 | 보호 장치 없음 | writes-follow-reads 적용 |
|---|---|---|
| 프로필 수정 화면을 오래 열어 둠 | 나중에 저장한 사용자가 예전 값 기준으로 덮어쓸 수 있음 | `profile_version` mismatch면 저장 거절 후 새로고침/merge 유도 |
| 장바구니를 보고 쿠폰 적용 | 다른 탭에서 수량이 바뀌었어도 예전 총액 기준 계산이 들어갈 수 있음 | `If-Match: cart_version` 또는 expected version 검사 |
| 관리자 화면에서 권한 설정 변경 | 이미 다른 관리자가 바꾼 정책을 모르고 다시 저장할 수 있음 | 마지막으로 본 policy version을 precondition으로 보냄 |

짧게 구분하면:

| 용어 | 막는 문제 | 질문 |
|---|---|---|
| Read-after-write | write 뒤 stale read | "내가 방금 쓴 값이 보이나?" |
| Writes-follow-reads | stale read 기반 write | "내가 본 상태를 믿고 저장해도 되나?" |
| Monotonic writes | write 순서 뒤집힘 | "내 write 두 개가 순서대로 적용되나?" |

## version check와 precondition check를 한 문장으로 구분하기

초보자가 가장 자주 헷갈리는 단어가 이 둘이다.

- `version`, `revision`, `ETag`는 read에서 받은 **상태 토큰**이다
- `precondition`은 "그 토큰이 아직 유효할 때만 write를 받는다"는 **서버 규칙**이다
- `version check`는 가장 흔한 precondition 형태다

즉, "`expected_version=12`를 보냈다"는 것은 결국 "`현재도 version 12일 때만 저장해 달라`"는 precondition을 건 것이다.

| 표현 방식 | read에서 받는 것 | write에서 보내는 것 | 서버가 실제로 확인하는 것 |
|---|---|---|---|
| API body 필드 | `version=7` | `expected_version=7` | current version이 아직 `7`인가 |
| HTTP 조건부 write | `ETag: "profile-v7"` | `If-Match: "profile-v7"` | current ETag가 strong match인가 |
| DB SQL | row의 `version=7` | `WHERE version = 7` | update row count가 `1`인가 |

transport와 이름은 달라도 핵심 의미는 하나다.

> "내가 읽은 상태 토큰과 현재 상태 토큰이 같을 때만 이 write를 받아라."

---

## 상세 분해

### 1. read에서 기준선을 같이 받는다

사용자가 화면에서 보는 값만 전달하면 부족하다.
그 값이 **언제 기준이 된 상태인지**도 같이 알아야 한다.

대표 예:

- DB row의 `version`
- HTTP resource의 `ETag`
- 이벤트/문서/장바구니의 `revision`
- 권한 정책의 `policy_version`

중요한 점은 이름이 아니라 의미다.
"내가 본 상태의 식별자"를 read 응답이 실어 줘야 한다.

### 2. write에서 precondition을 같이 보낸다

그다음 write 요청은 새 값만 보내면 안 되고, **내가 무엇을 보고 계산했는지**를 같이 보내야 한다.

흔한 형태:

- `If-Match: "etag-12"`
- `expected_version=12`
- `UPDATE ... WHERE id = ? AND version = 12`

이 패턴의 뜻은 모두 같다.

> "현재 상태가 내가 읽은 상태와 같을 때만 이 write를 받아 달라."

### 3. mismatch는 실패가 아니라 보호 신호다

precondition mismatch는 서버가 고장 났다는 뜻이 아니다.
오히려 stale write를 조용히 받아 버리지 않았다는 뜻이다.

이때 흔한 다음 동작은:

- 최신 상태를 다시 읽고 UI를 갱신
- 사용자가 본 변경과 현재 변경을 비교
- 자동 merge가 안전하면 merge
- 금전/재고/권한처럼 민감하면 명시적으로 다시 확인

초보자는 `409`나 `412` 숫자보다 **"왜 저장을 막았는가"**를 먼저 이해하는 편이 좋다.

conditional write API에서 상태 코드까지 같이 정리하려면:

- 조건이 아예 없으면 `428 Precondition Required`
- 조건은 있었지만 stale하면 `412 Precondition Failed`
- 최신 상태 기준으로도 도메인 충돌이 남으면 `409 Conflict`

이 구분은 [Conditional Write Status Code Bridge](./conditional-write-status-code-bridge.md)에서 초보자용 표로 다시 본다.

---

## 왜 version check가 필요한가

문제는 대부분 read-modify-write 흐름에서 생긴다.

```text
1. 사용자 A가 장바구니 version 12를 읽는다
2. 사용자 B가 다른 탭에서 수량을 바꿔 version 13이 된다
3. 사용자 A가 예전 총액을 기준으로 쿠폰 적용을 저장한다
```

여기서 precondition이 없으면 서버는 A의 write를 그냥 받아 버릴 수 있다.
그러면 시스템은 "최신 장바구니"에 대해 계산한 것이 아니라 **예전 판단을 현재 상태에 덮어쓴 것**이 된다.

그래서 writes-follow-reads는 lock을 오래 잡기보다, 저장 순간에 이렇게 묻는 설계다.

> "이 write가 의존한 read는 아직도 유효한가?"

이 질문 하나가 lost update, 잘못된 할인 계산, 낡은 권한 정책 저장 같은 사고를 많이 줄여 준다.

---

## 언제 version/precondition check를 먼저 붙일까

모든 write에 무조건 붙이는 규칙은 아니다.
가장 쉬운 판단 기준은 이 write가 **read한 상태를 근거로 계산됐는가**다.

| write 종류 | 필요도 | 이유 | 시작 설계 |
|---|---|---|---|
| 프로필/문서 편집 저장 | 높음 | 오래 열린 화면이 다른 변경을 덮어쓸 수 있음 | `expected_version` |
| 장바구니 확인 후 쿠폰/결제 | 매우 높음 | 총액, 재고, 할인 판단이 stale state 기준일 수 있음 | `If-Match`, cart version |
| 관리자 정책/권한 저장 | 매우 높음 | 예전 정책 화면으로 현재 권한을 잘못 덮을 수 있음 | policy version precondition |
| append-only 메시지 전송 | 낮음 | 기존 state를 덮는 저장이 아니라 새 항목 추가인 경우가 많음 | 보통 idempotency가 더 우선 |
| 원자적 증가 SQL (`count = count + 1`) | 낮음 | 서버가 read 없이 직접 갱신 가능할 수 있음 | atomic update, idempotency 검토 |

요약하면:

- **read-modify-write**면 우선 후보
- 금전/재고/권한/오래 열린 편집 화면이면 거의 기본값
- append-only나 서버 원자 연산이면 다른 guard가 더 먼저일 수 있다

---

## 실무에서 쓰는 모습

### 문서/프로필 편집

- `GET /profile` 응답에 `version=7`
- 편집 후 `PATCH /profile`에 `expected_version=7`
- 서버의 현재 version이 `8`이면 저장을 막고 최신 값 다시 보여 줌

이 흐름은 "마지막 저장이 무조건 이긴다"보다 안전하다.

### HTTP API의 `ETag` / `If-Match`

- read 응답이 `ETag: "cart-v12"`를 준다
- write 요청이 `If-Match: "cart-v12"`를 보낸다
- 서버는 현재 ETag가 다르면 `412 Precondition Failed`로 거절한다

즉, HTTP의 조건부 write도 결국 writes-follow-reads를 wire protocol에 올린 형태다.

### 장바구니, 재고, 권한 설정

이 경로들은 읽은 뒤 판단해서 다음 write를 만드는 경우가 많다.
그래서 단순 CRUD보다 precondition check 가치가 더 크다.

| 흐름 | 왜 위험한가 | 시작 설계 |
|---|---|---|
| 장바구니 수량 -> 쿠폰 적용 | 총액/재고 계산이 예전 상태 기준일 수 있음 | cart version + `If-Match` |
| 문서 편집 -> 저장 | 다른 사용자의 변경을 덮을 수 있음 | document revision check |
| 관리자 정책 변경 | 이미 바뀐 권한 규칙을 예전 화면으로 다시 저장할 수 있음 | policy version precondition |

---

## precondition mismatch 뒤에 무엇을 해야 하나

write가 거절됐을 때 가장 위험한 실수는 **같은 payload를 그대로 다시 보내는 것**이다.
그 payload 자체가 이미 예전 read를 근거로 만들어졌을 수 있기 때문이다.

| 상황 | 바로 재시도하면 왜 위험한가 | 더 안전한 다음 단계 |
|---|---|---|
| 프로필 저장 충돌 | 예전 폼 값으로 최신 변경을 다시 덮을 수 있음 | 최신 값을 다시 읽고 diff/merge 보여 주기 |
| 장바구니 쿠폰 적용 충돌 | 오래된 총액 기준 할인 계산을 반복함 | 최신 cart를 다시 읽고 할인 재계산 |
| 관리자 정책 저장 충돌 | 이미 바뀐 권한을 무심코 원복할 수 있음 | 누가 무엇을 바꿨는지 보여 주고 재확인 |

HTTP API에서는 많은 팀이 아래처럼 구분한다.

| 응답 | 흔한 의미 | 초보자용 해석 |
|---|---|---|
| `412 Precondition Failed` | 명시한 `If-Match`/`expected_version`가 깨짐 | "네가 본 기준선이 더 이상 최신이 아니다" |
| `409 Conflict` | 최신 상태 기준으로도 도메인 충돌이 남음 | "지금 상태로는 이 동작 자체가 충돌한다" |

그리고 이 API가 conditional write를 강제하는데 요청이 precondition 없이 왔다면 `428 Precondition Required`로 계약을 더 선명하게 표현할 수 있다.

정확한 status code 선택보다 더 중요한 것은 contract다.
클라이언트와 서버가 "**기준선 mismatch면 다시 읽고 다시 판단한다**"는 흐름을 공유해야 한다.

---

## 흔한 오해와 함정

- `writes-follow-reads = optimistic lock`이라고만 외우면 제품 의미를 놓치기 쉽다. 핵심은 락 이름보다 "내 판단 근거가 아직 유효한가"다.
- read-after-write와 같은 말이 아니다. 전자는 write 뒤 read freshness, 후자는 read 뒤 write precondition이다.
- precondition mismatch를 무조건 자동 재시도하면 안 된다. 예전 판단으로 만든 명령이라면 다시 읽고 다시 판단해야 한다.
- version check가 있으면 모든 동시성 문제가 끝나는 것도 아니다. 여러 row/집합 규칙 문제는 더 강한 guard가 필요할 수 있다.
- `ETag`는 cache용이라고만 생각하기 쉽지만, `If-Match`와 함께 쓰면 write precondition 도구가 된다.

---

## 더 깊이 가려면

- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Conditional Write Status Code Bridge](./conditional-write-status-code-bridge.md)
- [Inventory Reservation System Design](./inventory-reservation-system-design.md)
- [Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md)
- [Version Column Retry Walkthrough](../database/version-column-retry-walkthrough.md)
- [Strong vs Weak ETag: validator 정밀도와 cache correctness](../network/strong-vs-weak-etag-validator-precision-cache-correctness.md)
- [Aggregate Version and Optimistic Concurrency Pattern](../design-pattern/aggregate-version-optimistic-concurrency-pattern.md)

## 면접/시니어 질문 미리보기

> Q: writes-follow-reads와 read-after-write 차이는 무엇인가요?
> 핵심: 하나는 read 뒤 write를 안전하게 받는 조건이고, 다른 하나는 write 뒤 read freshness 보장이다.

> Q: precondition mismatch가 나면 왜 같은 payload를 바로 재시도하면 안 되나요?
> 핵심: 그 payload 자체가 이미 stale read를 근거로 만들어졌을 수 있기 때문이다.

> Q: `If-Match`와 DB version column은 어떤 관계인가요?
> 핵심: 표현 계층은 다르지만 "내가 읽은 버전일 때만 저장"이라는 의미는 같다.

## 한 줄 정리

writes-follow-reads는 사용자가 **읽고 나서 내린 판단**을 안전하게 write로 바꾸기 위한 규칙이고, 핵심 도구는 "read에서 받은 version/etag를 write의 precondition으로 다시 보내는 것"이다.
