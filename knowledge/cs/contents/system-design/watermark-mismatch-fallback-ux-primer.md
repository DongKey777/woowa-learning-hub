# Watermark Mismatch Fallback UX Primer

> 한 줄 요약: `required_watermark > applied_watermark`라는 mismatch는 "틀린 값을 자신 있게 보여 주지 말라"는 신호이고, 초보자용 첫 대응은 `stale hit reject`, `processing placeholder`, `primary fallback` 세 가지 UX 중 하나로 단순하게 고르는 것이다.

retrieval-anchor-keywords: watermark mismatch fallback ux primer, watermark mismatch ux, required watermark applied watermark fallback, stale hit rejection watermark, stale cache hit reject watermark, processing placeholder watermark mismatch, primary fallback watermark mismatch, watermark mismatch decision table, stale read placeholder beginner, read model lag user visible behavior, downstream read stale reject, required greater than applied, watermark mismatch user experience, watermark mismatch bridge beginner, consistency fallback ui primer, projection lag placeholder, watermark reject placeholder fallback, system-design-00078

**난이도: 🟢 Beginner**

관련 문서:

- [Projection Applied Watermark Basics](./projection-applied-watermark-basics.md)
- [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Notification Read to Min-Version Bridge](./notification-read-to-min-version-bridge.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)

---

## 먼저 잡을 mental model

watermark mismatch를 처음 보면 초보자는 보통 "데이터가 없나?" 또는 "에러인가?"부터 떠올린다.
하지만 사용자 화면에서 더 먼저 맞는 해석은 아래에 가깝다.

> "값이 아예 없는 것"보다 "지금 가진 값이 아직 믿을 만큼 따라오지 못했다"는 뜻이다.

예를 들어 주문 결제 직후를 보자.

- source write는 `required_watermark=9001`을 만들었다
- read model row나 cache entry는 아직 `applied_watermark=8998`이다

이때 시스템이 해야 할 첫 판단은 "어떻게든 이 row를 보여 줄까?"가 아니다.
먼저 아래를 정해야 한다.

- 오래된 hit를 그대로 버릴까
- 잠깐 처리 중 placeholder를 보여 줄까
- 더 신선한 source로 fallback할까

즉 watermark mismatch는 **비교 로직의 끝**이 아니라,
**사용자에게 무엇을 보여 줄지 고르는 시작점**이다.

---

## 세 가지 UX 선택지만 먼저 외우기

| 선택지 | 사용자에게 보이는 것 | 언제 먼저 고르기 쉬운가 | 핵심 위험 |
|---|---|---|---|
| `stale hit reject` | 오래된 row를 그대로 채택하지 않음 | 후보가 cache/search/list hit일 때 | reject만 하고 대체 경로가 없으면 빈 화면처럼 느껴질 수 있다 |
| `processing placeholder` | `처리 중`, `갱신 중`, skeleton, badge 표시 | projection이 곧 따라올 가능성이 높고 잠깐 기다릴 수 있을 때 | placeholder가 오래 지속되면 진짜 장애처럼 느껴진다 |
| `primary fallback` | 더 느려도 최신성이 높은 결과를 바로 보여 줌 | 결제/권한/재고처럼 틀리면 안 되는 read일 때 | fallback 범위가 넓어지면 primary가 버티지 못할 수 있다 |

짧게 기억하면 이렇다.

- stale 후보면 **그대로 채택하지 않는다**
- 곧 따라올 값이면 **placeholder**
- 지금 정확해야 하면 **primary fallback**

---

## 왜 "mismatch = stale 화면 그대로 노출"이 아니어야 하나

초보자가 가장 자주 하는 실수는 mismatch를 "조금 늦었네" 정도로 보고 기존 값을 그냥 렌더링하는 것이다.
하지만 사용자 입장에서는 아래처럼 읽힌다.

| 시스템 내부 상태 | 사용자가 느끼는 화면 |
|---|---|
| `required=9001`, `applied=8998`, 그래도 `PENDING` 렌더링 | "결제가 안 됐나?" |
| `required=9001`, `applied=8998`, 그래도 재고 `available` 렌더링 | "지금도 살 수 있나?" |
| `required=9001`, `applied=8998`, 그래도 권한 `admin` 렌더링 | "권한이 아직 남아 있나?" |

그래서 mismatch는 보통 "보여 줄 값이 있음"보다 "그 값을 그대로 믿으면 안 됨"에 더 가깝다.

---

## 가장 단순한 흐름

```text
request comes with required_watermark=9001
        |
        v
candidate row/cache/search hit has applied_watermark=8998
        |
        v
8998 < 9001 => mismatch
        |
        +-> reject stale hit
        |
        +-> choose next UX
              - primary fallback
              - processing placeholder
              - suppress + retry/poll
```

핵심은 한 줄이다.

> watermark compare는 "accept?"를 묻고, fallback UX는 "accept가 아니면 무엇을 보여 줄까?"를 정한다.

---

## 주문 결제 예시로 보면 더 쉽다

### 상황

```text
POST /orders/123/pay
- commit success
- required_watermark=9001

GET /orders/123
- cache row status=PENDING
- cache applied_watermark=8998
```

### 잘못된 처리

- cache hit이 있으니 그냥 `PENDING`을 보여 준다

사용자는 "결제가 실패했나?"라고 오해할 수 있다.

### 더 나은 처리

| 판단 | 결과 |
|---|---|
| `8998 < 9001` | stale cache hit reject |
| 주문 상세는 정확도가 중요함 | primary fallback 시도 |
| primary가 `PAID`, `observed_watermark=9001` 반환 | 그 결과를 렌더링하고 cache metadata도 올림 |

즉 여기서는 placeholder보다 primary fallback이 더 자연스럽다.
결제 확인 화면은 "잠깐 후 새로고침"보다 "바로 정확한 상태"가 더 중요하기 때문이다.

---

## 반대로 placeholder가 더 맞는 경우도 있다

대시보드 카드, 통계 위젯, 검색 색인 결과처럼 projection이 잠깐 늦을 수 있는 화면에서는
"오래된 값 강행"보다 "갱신 중 표시"가 더 정직한 UX일 수 있다.

예:

```text
required_watermark=5100
widget applied_watermark=5096
```

이때 beginner 단계의 쉬운 선택은 아래다.

| 화면 종류 | mismatch 시 기본 선택 | 이유 |
|---|---|---|
| 결제 확인, 권한 검사, 재고 확정 | `primary fallback` | 틀린 값을 보여 주는 비용이 큼 |
| 분석 위젯, 배지 수치, 검색 요약 | `processing placeholder` | 잠깐 늦는 것이 치명적이지 않음 |
| 목록 row, cache hit, search hit | `stale hit reject` + 다른 source/overlay 선택 | 오래된 hit를 그대로 채택하는 것이 가장 눈에 띄는 UX 사고를 만든다 |

---

## downstream read에서 특히 중요한 규칙

watermark mismatch는 "지금 이 한 번의 read"로 끝나지 않는 경우가 많다.
특히 목록, 검색, 알림 진입 뒤 후속 화면에서 stale hit를 다시 집어 들기 쉽다.

그래서 downstream read는 아래 순서로 보는 편이 안전하다.

1. 후보 hit의 `applied_watermark`를 먼저 본다
2. `required_watermark`보다 낮으면 그 hit를 채택하지 않는다
3. 더 신선한 source가 있으면 fallback한다
4. 없으면 placeholder, suppress, overlay 중 하나를 고른다
5. mismatch였던 값을 cache에 다시 refill하지 않는다

이 다섯 번째가 자주 빠진다.
stale 후보를 reject해 놓고도 그 값을 다시 cache에 넣으면 다음 요청도 같은 mismatch를 반복하게 된다.

---

## 작은 의사코드로 보면

```pseudo
candidate = readFastPath(key)

if candidate.appliedWatermark < requiredWatermark:
  reject(candidate)

  if endpoint.requiresFreshNow():
    return readPrimary()

  if endpoint.canShowProcessingState():
    return processingPlaceholder()

  return suppressOrOverlay()

return candidate
```

초보자에게 중요한 점은 `fallback`이 "무조건 primary"가 아니라는 것이다.
먼저 stale hit를 reject하고, 그다음 endpoint 성격에 맞는 UX를 고른다.

---

## 선택 기준을 한 표로 고정하기

| 질문 | `yes`면 먼저 보기 | 이유 |
|---|---|---|
| 틀린 값을 보여 주면 금전/권한/재고 사고로 이어지나 | `primary fallback` | 정확도가 지연보다 중요하다 |
| 몇 초 안에 projection이 따라오고, 사용자도 잠깐 기다릴 수 있나 | `processing placeholder` | 거짓 최신값보다 정직한 대기 화면이 낫다 |
| 지금 후보가 cache/list/search의 오래된 hit인가 | `stale hit reject` | 오래된 hit를 그대로 채택하는 버그를 먼저 막아야 한다 |

이 표는 "정답이 하나"라기보다 초보자용 기본 우선순위다.

- 위험한 read는 primary fallback 쪽으로 기운다
- 덜 위험한 read는 placeholder 쪽으로 기운다
- 어떤 경우에도 stale hit는 무심코 accept하지 않는다

---

## observability도 UX 언어로 남겨야 한다

운영에서 mismatch를 이해하려면 숫자만이 아니라 "무슨 UX 선택이 실행됐는가"도 같이 남겨야 한다.

최소 필드는 아래 정도면 충분하다.

- `required_watermark`
- `applied_watermark`
- `mismatch=true`
- `rejected_hit_reason=watermark`
- `fallback_reason=watermark` 또는 `ux_action=processing_placeholder`
- `selected_source=cache|replica|primary|placeholder`

예를 들면:

```text
event=read_freshness_gate
required_watermark=9001
applied_watermark=8998
rejected_hit_reason=watermark
ux_action=primary_fallback
selected_source=primary
```

이렇게 남겨야 "왜 사용자가 placeholder를 봤는지", "왜 primary 비율이 갑자기 늘었는지"를 같이 설명할 수 있다.

---

## 자주 나오는 오해

- `watermark mismatch면 무조건 에러 화면이다`
  - 아니다. 많은 경우 에러보다 `placeholder`나 `fallback`이 맞다.
- `candidate 값이 있으면 일단 보여 주고 background에서 고치면 된다`
  - mismatch에서는 그 "일단"이 가장 큰 UX 사고가 된다.
- `primary fallback`이 제일 안전하니 항상 쓰면 된다
  - 안전하지만 비싸다. endpoint 중요도와 primary headroom을 같이 봐야 한다.
- `placeholder`는 최신성 문제를 숨기는 꼼수다
  - 틀린 확정값을 보여 주는 것보다 "아직 반영 중"을 정직하게 알리는 편이 나을 수 있다.
- `stale hit reject`는 cache miss와 같은 뜻이다
  - 다르다. hit는 있었지만 freshness contract를 못 맞춰서 의도적으로 버린 것이다.

---

## 30초 체크리스트

- `required_watermark > applied_watermark`일 때 stale 후보를 그대로 렌더링하지 않는가
- endpoint별 기본 UX가 정해져 있는가
- 중요 read는 `primary fallback`, 덜 중요한 read는 `placeholder` 같은 기본 축이 있는가
- reject된 stale 값을 cache에 다시 refill하지 않는가
- 로그/메트릭에 `watermark mismatch`와 실제 `ux_action`이 같이 남는가

---

## 한 줄 정리

watermark mismatch는 "비교 실패"가 아니라 "사용자에게 어떤 정직한 다음 행동을 보여 줄지 고르는 신호"이고, beginner 단계에서는 `stale hit reject`, `processing placeholder`, `primary fallback` 세 선택지를 endpoint 위험도에 맞춰 일관되게 고르는 것부터 시작하면 된다.
