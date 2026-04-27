# HTTP Coalescing Failure Mapping

> 한 줄 요약: HTTP adapter가 여러 item 요청을 한 번의 bulk 호출로 묶더라도, 결과는 `batch receipt`, `per-item receipt`, `retry decision`으로 다시 펼쳐야 부분 실패를 안전하게 설명할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Software Engineering README: HTTP Coalescing Failure Mapping](./README.md#http-coalescing-failure-mapping)
- [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
- [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)
- [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
- [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
- [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)
- [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md)
- [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
- [HTTP 상태 코드 기초](../network/http-status-codes-basics.md)
- [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md)
- [Job Queue 설계](../system-design/job-queue-design.md)

retrieval-anchor-keywords: http coalescing failure mapping, bulk http partial result mapping, batch receipt to item receipt, per-item receipt mapping, http partial success retry decision, bulk endpoint item correlation key, http bulk response index mapping, adapter coalescing beginner, array position mapping smell, missing item means unknown, bulk result to retry queue, http receipt mapping what is, partial success 처음, retry decision basics, vendor response index to item id

## 핵심 개념

먼저 그림부터 잡으면 쉽다.
한 번의 bulk HTTP 호출은 "트럭 한 대 영수증"이고, 실제 운영 판단은 "상자마다 붙는 영수증"에 가깝다.

- `batch receipt`는 "이번 묶음 요청을 파트너가 받았는가"를 말한다.
- `per-item receipt`는 "37번 item은 접수됐는가, 거절됐는가, 결과가 비었는가"를 말한다.
- `retry decision`은 "이 item을 같은 key로 다시 보낼지, 수동 확인으로 넘길지"를 말한다.

초심자가 가장 많이 하는 실수는 HTTP 응답이 한 번 왔다는 사실만 보고 전체 item이 처리됐다고 생각하는 것이다.
하지만 bulk endpoint는 `200 OK`여도 일부 item만 성공할 수 있고, 일부는 validation reject나 timeout 재시도 후보일 수 있다.

## 한눈에 보기

| 층위 | 답하는 질문 | 예시 필드 | 여기서 놓치면 생기는 문제 |
|---|---|---|---|
| 요청 대응표 | "이 결과가 어느 item의 것인가?" | `clientRef`, `itemId`, `idempotencyKey` | 결과를 item에 다시 붙이지 못한다 |
| batch receipt | "묶음 호출 자체는 접수됐는가?" | `batchReceiptId`, `acceptedCount` | 운영자는 묶음 추적을 못 한다 |
| per-item receipt | "각 item은 어떻게 끝났는가?" | `partnerItemReceipt`, `status`, `reasonCode` | 부분 실패를 설명하거나 재시도 대상을 고르지 못한다 |
| retry decision | "다음 행동은 무엇인가?" | `retry-same-key`, `manual-review`, `done` | timeout과 validation 오류를 같은 방식으로 다뤄 버린다 |

핵심은 count가 아니라 대응표다.
`successCount=97, failureCount=3`만 남기면 나중에 어떤 3건을 다시 볼지 결정할 수 없다.

## 상세 분해

### 1. 보내기 전에 item 대응표를 고정한다

결과를 받은 뒤에 "아마 배열 순서가 같겠지"라고 맞추면 늦다.
adapter는 보내기 전에 각 item에 안정적인 대응 키를 붙여야 한다.

- 가장 안전한 키는 `clientRef`, `itemId`, `idempotencyKey`처럼 응답에서 다시 찾을 수 있는 값이다.
- 가능하면 배열 index보다 business-safe reference를 쓴다.
- 외부가 index만 돌려줘도, 내부에서는 `index -> item` 표를 먼저 만들어 둔다.

즉 매핑은 응답 단계의 추측이 아니라 요청 단계의 준비물이다.

### 2. HTTP 상태와 item 결과를 분리해서 읽는다

bulk HTTP 응답은 보통 두 층으로 읽어야 한다.

- HTTP status / batch receipt: 요청 전체가 transport 차원에서 도달했는가
- item results: 각 item이 실제로 accepted, rejected, retryable, unknown 중 어디에 있는가

`200 OK`는 "응답을 잘 받았다"에 가깝지, "모든 item이 business success다"를 보장하지 않는다.
반대로 `207`이나 파트너 고유 응답도 결국 adapter 안에서는 per-item 상태로 번역돼야 한다.

### 3. transport 결과를 per-item 영수증으로 번역한다

adapter는 vendor 응답을 그대로 안쪽으로 들여보내기보다, 애플리케이션이 읽을 receipt로 다시 펴는 편이 안전하다.

| transport 결과 | per-item receipt 해석 | retry decision |
|---|---|---|
| accepted + partner receipt 있음 | `done` | 재시도 없음 |
| validation reject | `rejected(reasonCode)` | 수동 확인 |
| timeout / temporary failure | `retryable` | 같은 idempotency key로 재시도 |
| 응답에서 item 누락 | `unknown` | 성공 처리하지 말고 reconcile 후 재시도 여부 결정 |

여기서 중요한 것은 `unknown`을 성공으로 합치지 않는 것이다.
bulk 응답이 일부 item을 빼먹으면 "실패일 수도, 이미 접수됐을 수도" 있으므로 먼저 미확정 상태로 남겨야 한다.

### 4. 재시도는 묶음이 아니라 item 영수증에서 결정한다

coalescing은 요청을 묶는 기술이고, retry decision은 item별로 갈라지는 운영 판단이다.

## 상세 분해 (계속 2)

- `timeout` item만 같은 key로 retry queue에 넣는다.
- `validation` item은 자동 재시도하지 않는다.
- `unknown` item은 receipt 조회나 reconciliation 없이는 함부로 재전송하지 않는다.
- batch receipt는 추적과 감사에 쓰고, 실제 후속 동작은 per-item receipt를 기준으로 정한다.

그래서 adapter의 출력은 "한 번의 bulk 응답"이 아니라 "item별 영수증 모음"에 가까워야 한다.

### 5. vendor index를 stable item id로 다시 고정해 retry drift를 막는다

여기서 초심자가 특히 많이 미끄러지는 지점이 있다.
vendor가 `result[2] failed`처럼 index만 돌려주면, 그 index를 item identity처럼 저장해 버리는 것이다.

하지만 vendor index는 "이번 한 번의 배열 자리번호"일 뿐이다.
retry에서 실패 item만 다시 묶으면 배열이 다시 압축되므로 같은 item도 새 요청에서는 다른 index를 받을 수 있다.

먼저 세 이름을 분리해서 기억하면 쉽다.

| 이름 | 무엇을 뜻하나 | retry 뒤에도 그대로여야 하나 |
|---|---|---|
| vendor index | 이번 outbound payload 안의 자리번호 | 아니다. retry 때 바뀔 수 있다 |
| domain item id | 우리 시스템이 추적하는 안정 식별자 | 그렇다 |
| item idempotency key | 같은 부작용 재시도 여부를 가르는 키 | 그렇다 |

그래서 adapter는 요청을 보내기 전에 아래 대응표를 같이 고정해 두는 편이 안전하다.

```text
request slot ledger
- slot 0 -> msg-101 / notify-101
- slot 1 -> msg-102 / notify-102
- slot 2 -> msg-103 / notify-103
- slot 3 -> msg-104 / notify-104
```

응답이 `{ failedIndexes: [2, 3] }`로 오면 내부에서는 즉시 아래처럼 번역한다.

```text
translated failures
- msg-103 / notify-103 / retryable
- msg-104 / notify-104 / retryable
```

retry queue에 넣을 때도 `2, 3`을 저장하지 않고 `msg-103`, `msg-104`와 같은 stable id를 저장한다.
그래야 다음 retry payload가 아래처럼 다시 압축돼도 drift가 나지 않는다.

```text
retry payload
- slot 0 -> msg-103 / notify-103
- slot 1 -> msg-104 / notify-104
```

## 상세 분해 (계속 3)

같은 item이 첫 요청에서는 index `2`였고 retry에서는 index `0`이 되어도, domain 쪽에서는 여전히 `msg-103` 한 건으로 설명된다.
반대로 retry backlog에 index만 남기면 "예전 2번"이 "이번 2번"과 같은 item이라고 착각해 잘못된 재전송이나 잘못된 성공 표시가 생긴다.

초심자 기준으로는 아래 세 줄만 기억해도 충분하다.

- vendor index는 response parsing용 임시 좌표다.
- retry queue와 domain result에는 stable item id를 남긴다.
- 같은 item 재시도 여부는 index가 아니라 item idempotency key로 판단한다.

### 짧은 테스트 예시: index-only vendor response

아래 두 테스트를 나란히 보면 차이가 더 빨리 보인다.

| 비교 장면 | 무엇을 저장하나 | retry 재정렬 뒤에 안전한가 |
|---|---|---|
| 실패하는 예시 | `sourceIndex`만 저장 | 아니다 |
| 고친 예시 | `itemId`와 `idempotencyKey`를 저장 | 그렇다 |

#### 실패하는 예시: retry drift를 놓치는 테스트

```java
@Test
void index_only_mapping_breaks_after_retry_payload_is_compacted() {
    VendorResponse firstResponse = VendorResponse.failedIndexes(2);

    RetryBacklog backlog = mapper.toRetryBacklog(
            outboundRequest(
                    slot(0, "msg-101", "notify-101"),
                    slot(1, "msg-102", "notify-102"),
                    slot(2, "msg-103", "notify-103")
            ),
            firstResponse
    );

    VendorResponse retryResponse = VendorResponse.failedIndexes(0);

    RetryBacklog retried = mapper.toRetryBacklog(
            outboundRequest(
                    slot(0, "msg-103", "notify-103")
            ),
            retryResponse
    );

    assertThat(backlog.failedIndexes()).containsExactly(2);
    assertThat(retried.failedIndexes()).containsExactly(0);
    assertThat(retried.failedIndexes()).doesNotContain(2);
}
```

## 상세 분해 (계속 4)

이 테스트는 초심자에게 오히려 잘못된 안심을 줄 수 있다.
첫 요청의 실패 item과 retry 요청의 실패 item이 **같은 domain item인지**는 확인하지 않고, index가 바뀌었다는 사실만 지나가 버리기 때문이다.

#### 고친 예시: stable item id로 같은 실패를 끝까지 추적하는 테스트

```java
@Test
void stable_item_id_mapping_survives_retry_payload_reordering() {
    VendorResponse firstResponse = VendorResponse.failedIndexes(2);

    RetryCandidate firstRetry = mapper.toRetryCandidates(
            outboundRequest(
                    slot(0, "msg-101", "notify-101"),
                    slot(1, "msg-102", "notify-102"),
                    slot(2, "msg-103", "notify-103")
            ),
            firstResponse
    ).get(0);

    VendorResponse retryResponse = VendorResponse.failedIndexes(0);

    RetryCandidate secondRetry = mapper.toRetryCandidates(
            outboundRequest(
                    slot(0, "msg-103", "notify-103")
            ),
            retryResponse
    ).get(0);

    assertThat(firstRetry.itemId()).isEqualTo("msg-103");
    assertThat(firstRetry.idempotencyKey()).isEqualTo("notify-103");
    assertThat(secondRetry.itemId()).isEqualTo("msg-103");
    assertThat(secondRetry.idempotencyKey()).isEqualTo("notify-103");
}
```

이 버전의 핵심은 "`2`가 `0`으로 바뀌었다"가 아니라 "`msg-103 / notify-103`은 그대로다"를 검증하는 것이다.
retry payload가 압축되거나 재정렬돼도, domain 쪽 설명은 계속 같은 item 하나를 가리켜야 한다.

## 흔한 오해와 함정

| 오해 | 더 안전한 첫 판단 |
|---|---|
| HTTP `200`이면 전부 성공이다 | transport 성공과 item 성공을 분리해서 본다 |
| 응답 배열 순서대로 붙이면 된다 | `clientRef` 같은 안정 키로 매핑하고, index는 마지막 수단으로만 쓴다 |
| `successCount`와 `failureCount`만 저장하면 충분하다 | 어떤 item이 왜 실패했는지 남겨야 retry가 가능하다 |
| 응답에서 빠진 item은 대충 성공으로 본다 | `unknown`으로 두고 receipt 조회나 reconcile을 먼저 한다 |
| timeout이면 묶음 전체를 다시 보낸다 | retryable item만 같은 key로 다시 보낸다 |
| vendor가 index를 줬으니 retry queue도 index만 저장하면 된다 | index는 매 요청마다 달라질 수 있으니 `itemId`와 `idempotencyKey`로 번역해 남긴다 |
| 여기서 coalescing은 HTTP/2 connection coalescing 이야기다 | 이 문서의 coalescing은 adapter가 여러 item 요청을 bulk HTTP 한 번으로 묶는다는 뜻이다 |

## 실무에서 쓰는 모습

알림 adapter가 4건을 `/bulk-send`로 묶는다고 하자.

```text
sent items
- msg-101 / clientRef=a1 / idempotencyKey=notify-101
- msg-102 / clientRef=a2 / idempotencyKey=notify-102
- msg-103 / clientRef=a3 / idempotencyKey=notify-103
- msg-104 / clientRef=a4 / idempotencyKey=notify-104

response
- batchReceiptId=bulk-33
- results:
  - a1 accepted, partnerReceipt=p-901
  - a2 rejected, reason=invalid-phone
  - a3 temporary-failure, reason=provider-timeout
```

이때 adapter 출력은 이렇게 읽는 편이 안전하다.

| item | mapped per-item receipt | next action |
|---|---|---|
| `msg-101` | `done(partnerReceipt=p-901)` | 종료 |
| `msg-102` | `rejected(invalid-phone)` | 수동 수정 후 재시도 |
| `msg-103` | `retryable(provider-timeout)` | 같은 key로 retry queue 이동 |
| `msg-104` | `unknown(missing-from-response)` | receipt 조회 또는 reconcile 후 결정 |

중요한 점은 `msg-104`다.
응답에 안 보인다고 해서 성공도 실패도 확정하지 않는다.
이 한 줄이 없으면 bulk partial failure가 조용한 데이터 누락으로 바뀐다.

## 더 깊이 가려면

- HTTP bulk endpoint를 adapter 세부로 숨기되 per-item 계약을 유지하는 큰 경계는 [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)에서 본다.
- run/chunk/file과 partial failure result 타입 자체를 이름 붙이는 문제는 [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)로 이어진다.
- retry queue, checkpoint, manual-review 분리는 [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)에서 더 넓게 다룬다.
- 같은 item을 다시 보낼 때 어떤 key를 재사용해야 하는지는 [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)를 같이 보면 선명해진다.
- `sourceIndex`를 stable `itemId`로 어떻게 검증할지는 [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)에서 이어 볼 수 있다.
- run/file/chunk/item 계약마다 어떤 key를 유지해야 하는지는 [Bulk Idempotency Keys For Named Contracts](./bulk-idempotency-keys-for-named-contracts.md)로 이어 읽으면 좋다.
- HTTP status와 멱등성 용어가 먼저 헷갈리면 [HTTP 상태 코드 기초](../network/http-status-codes-basics.md), [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md)을 먼저 정리하면 된다.

## 한 줄 정리

HTTP bulk coalescing의 핵심은 "응답 한 장"을 믿는 것이 아니라, 안정적인 item 대응 키로 `batch receipt`를 `per-item receipt + retry decision`으로 다시 펼치는 데 있다.
