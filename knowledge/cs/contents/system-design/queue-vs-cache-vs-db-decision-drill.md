---
schema_version: 3
title: Queue vs Cache vs DB Decision Drill
concept_id: system-design/queue-vs-cache-vs-db-decision-drill
canonical: false
category: system-design
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- sync-vs-async-boundary
- cache-is-not-source-of-truth
- queue-vs-persistence-role
aliases:
- queue vs cache vs db decision drill
- cache vs queue vs database beginner
- 언제 cache를 쓰고 언제 queue를 쓰나요
- cache queue db 차이
- db cache queue 뭐예요
- db만 있으면 안 되나요
- 처음 system design cache queue 헷갈려요
- source of truth vs copy vs handoff
- 왜 queue를 db 대신 쓰면 안 되나요
- 왜 cache는 정답 저장소가 아니에요
- what is cache vs queue vs db
- backend basics cache queue database
symptoms:
- 응답이 느린데 cache를 붙여야 할지 queue로 빼야 할지 모르겠어
- DB가 있는데 cache나 queue를 왜 더 두는지 감이 안 와
- 후처리 작업도 그냥 DB에만 넣으면 되는지 헷갈려
intents:
- comparison
- design
prerequisites:
- database/transaction-basics
- system-design/stateless-backend-cache-database-queue-starter-pack
next_docs:
- system-design/caching-basics
- system-design/message-queue-basics
- system-design/per-key-queue-vs-direct-api-primer
linked_paths:
- contents/system-design/stateless-backend-cache-database-queue-starter-pack.md
- contents/system-design/caching-basics.md
- contents/system-design/message-queue-basics.md
- contents/system-design/consistency-idempotency-async-workflow-foundations.md
- contents/system-design/per-key-queue-vs-direct-api-primer.md
- contents/database/transaction-basics.md
confusable_with:
- system-design/caching-basics
- system-design/message-queue-basics
- system-design/per-key-queue-vs-direct-api-primer
forbidden_neighbors:
- contents/system-design/job-queue-design.md
- contents/system-design/distributed-cache-design.md
expected_queries:
- 저장은 해야 하고 메일은 나중에 보내고 싶은데 DB랑 queue를 어떻게 나눠?
- 조회 속도 문제인지 비동기 처리 문제인지 구분하는 가장 쉬운 기준이 뭐야?
- 주문 시스템에서 cache, queue, database를 각각 어디에 써야 하는지 감이 안 와
- cache가 정답 저장소가 아니라고 할 때 실제로 무슨 뜻이야?
- 이미지 리사이즈나 알림 발송은 왜 DB 대신 queue로 보내는 거야?
- 같은 데이터를 빨리 보여주고 싶은 상황과 나중 처리하고 싶은 상황을 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 system design 입문자가 database, cache, queue를 대체재가
  아니라 정답 저장, 빠른 재사용, 비동기 handoff로 나눠 고르게 돕는
  intermediate chooser다. DB가 있는데 왜 cache나 queue가 더 필요한지,
  응답 속도 문제와 후처리 분리 문제를 어떻게 가르는지, 주문 저장과
  이메일 발송을 왜 다른 컴포넌트에 맡기는지, cache가 왜 source of
  truth가 아닌지 같은 자연어 질문이 본 문서의 선택 기준에 매핑된다.
---
# Queue vs Cache vs DB Decision Drill

> 한 줄 요약: `cache`는 "같은 답을 더 빨리 다시 꺼내기", `queue`는 "지금 안 끝내도 되는 일을 뒤로 넘기기", `database`는 "핵심 상태의 정답을 남기기"로 잡으면 beginner가 가장 자주 헷갈리는 선택이 빨리 정리된다.

retrieval-anchor-keywords: queue vs cache vs db decision drill, cache vs queue vs database beginner, 언제 cache를 쓰고 언제 queue를 쓰나요, cache queue db 차이, db cache queue 뭐예요, db만 있으면 안 되나요, 처음 system design cache queue 헷갈려요, source of truth vs copy vs handoff, 왜 queue를 db 대신 쓰면 안 되나요, 왜 cache는 정답 저장소가 아니에요, what is cache vs queue vs db, backend basics cache queue database

**난이도: 🟡 Intermediate**

관련 문서:

- [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- [캐시 기초](./caching-basics.md)
- [메시지 큐 기초](./message-queue-basics.md)
- [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- [Per-Key Queue vs Direct API Primer](./per-key-queue-vs-direct-api-primer.md)
- [트랜잭션 기초](../database/transaction-basics.md)
- [system-design 카테고리 인덱스](./README.md)

---

## 언제 이 드릴을 먼저 보나

아래 질문이 한 번이라도 나오면 이 문서부터 보면 된다.

- `언제 cache를 쓰고 언제 queue를 써요?`
- `DB가 있는데 cache나 queue를 왜 또 붙여요?`
- `응답을 빠르게 만들고 싶은데 cache인지 queue인지 헷갈려요`

이 드릴의 목표는 제품별 세부 기능 비교가 아니다.
**요청 하나를 볼 때 "정답 저장", "빠른 재사용", "나중 처리" 중 무엇이 필요한지 먼저 가르는 것**이다.

---

## 먼저 잡는 3칸 정신 모델

| 구성 요소 | 먼저 떠올릴 질문 | 기본 역할 | 보통 기대하는 것 |
|---|---|---|---|
| `database` | 이 상태의 정답을 어디에 남길까? | 핵심 비즈니스 상태의 기준 저장소 | durability, 조회/수정 기준점 |
| `cache` | 같은 읽기를 더 빨리 반복할 수 있을까? | 정답의 복사본 | 더 빠른 읽기, DB 부하 감소 |
| `queue` | 지금 다 안 끝내도 되는 일을 분리할 수 있을까? | 작업 전달과 비동기 handoff | 응답 시간 단축, 피크 흡수, 재시도 |

택배 비유로 시작하면 쉽다.

- `database`: 주문 원장을 적는 장부
- `cache`: 자주 보는 요약 메모
- `queue`: 나중에 처리할 작업 바구니

하지만 비유는 여기까지만 맞다.
실제 시스템에서는 cache도 오래 남을 수 있고 queue도 일시 저장을 하지만, **장부 역할까지 자동으로 대신해 주지는 않는다.**

---

## 30초 결정표

| 지금 필요한 것 | 먼저 고를 후보 | 이유 |
|---|---|---|
| 주문 상태의 정답 저장 | `database` | 나중에 다시 읽고 수정할 기준점이 필요하다 |
| 인기 상품 조회를 더 빠르게 응답 | `cache` | 같은 읽기를 복사본으로 짧게 처리할 수 있다 |
| 주문 완료 후 이메일 발송 | `queue` | 사용자 응답 뒤에 처리해도 되는 느린 작업이다 |
| 결제 성공 직후 영수증 화면에 최신 상태 보이기 | `database`를 기준으로 응답, 필요 시 `cache`는 보조 | 최신성이 우선이라 복사본만 믿으면 위험하다 |
| 이미지 리사이즈, 검색 인덱싱처럼 오래 걸리는 후처리 | `queue` + 결과 저장소 | 작업은 뒤로 넘기고, 완료 결과는 별도 저장한다 |
| 조회가 폭증하는 공개 프로필 화면 | `cache`, 단 원본은 `database` | 빠른 읽기가 목표지만 정답 저장소는 따로 있어야 한다 |

빠른 기억법:

- `정답을 남긴다` -> `database`
- `같은 답을 빨리 꺼낸다` -> `cache`
- `지금 안 끝내도 되는 일을 넘긴다` -> `queue`

## 셋은 경쟁 관계보다 역할 분담에 가깝다

초심자가 가장 자주 막히는 질문은 "`셋 중 하나만 골라야 하나요?`"다.
대부분의 실제 시스템은 하나만 고르지 않고, **정답 저장 / 빠른 재사용 / 느린 후처리**를 나눠 맡긴다.

| 상황 | `database` 역할 | `cache` 역할 | `queue` 역할 |
|---|---|---|---|
| 주문 생성 + 주문 조회 많음 | 주문 상태 원본 저장 | 주문 상세/목록 조회 가속 | 메일, 적립금, 알림 후처리 전달 |
| 상품 상세 조회 폭증 | 상품 원본과 재고 기준 저장 | 인기 조회 응답 가속 | 캐시 재계산이나 색인 갱신 작업 전달 |
| 결제 완료 직후 영수증 화면 | 결제 결과와 영수증 기준 저장 | 최신성 허용 범위 안에서 반복 조회 가속 | 영수증 메일, 정산 이벤트 전달 |

즉 `database`가 있더라도 읽기 비용이 크면 `cache`를 붙이고, 응답 뒤로 미뤄도 되는 일이 있으면 `queue`를 붙인다.
반대로 `cache`나 `queue`를 붙였다고 해서 원본 저장소 역할이 자동으로 사라지지는 않는다.

---

## 미니 상황 4개로 바로 구분하기

### 1. 주문 생성

사용자가 주문 버튼을 눌렀다.
주문 번호와 상태는 나중에 다시 조회되고 결제 흐름의 기준이 된다.

먼저 필요한 것은 `database`다.
이메일 발송이나 추천 갱신은 늦어도 되므로 뒤에 `queue`로 뺄 수 있다.

### 2. 상품 상세 조회

같은 상품 상세를 수천 명이 반복 조회한다.
원본은 자주 바뀌지 않는다.

이때 먼저 보는 카드는 `cache`다.
다만 가격이나 재고처럼 stale이 위험한 필드는 TTL만 믿지 말고 원본 조회 경로와 무효화 전략을 같이 봐야 한다.

### 3. 회원가입 직후 환영 메일

회원가입 성공 여부는 지금 바로 알려야 한다.
하지만 메일 전송은 외부 시스템 상태에 따라 느려질 수 있다.

회원 정보 저장은 `database`, 메일 전송 요청은 `queue`가 자연스럽다.
`queue`는 가입 자체의 정답 저장소가 아니라 후처리 분리 장치다.

### 4. "방금 결제한 잔액" 조회

사용자가 방금 바꾼 값이 바로 보여야 한다.
여기서 `cache`만 먼저 보면 stale read가 날 수 있다.

이 경우 출발점은 `database` 또는 최신성 보장을 가진 읽기 경로다.
그 뒤에 cache를 붙이더라도 `delete-on-write`, bypass, session consistency 같은 보조 장치를 함께 검토한다.

---

## beginner가 자주 하는 오해

- `응답이 느리면 일단 queue를 붙이면 된다`
  - 아니다. 사용자가 지금 결과를 알아야 하는 핵심 쓰기라면 sync 경로와 DB 저장을 먼저 설계해야 한다.
- `cache가 있으니 DB를 덜 믿어도 된다`
  - 아니다. cache는 보통 복사본이다. 정답 기준점은 대개 DB나 별도 원본 저장소에 있다.
- `queue에 메시지가 남아 있으니 그게 곧 영속 저장이다`
  - broker 보존 기간과 소비 실패 정책은 제품 설정에 따라 다르다. 보통 핵심 상태 원장과 같은 뜻으로 쓰면 안 된다.
- `DB, cache, queue 중 하나만 고르면 된다`
  - 실제로는 함께 쓴다. 예를 들면 `DB에 주문 저장 -> queue로 메일 발송 -> 조회는 cache 가속` 조합이 흔하다.
- `DB가 있으니 cache나 queue는 나중에 붙여도 된다`
  - 늦게 붙여도 되지만, 조회 폭증이나 느린 후처리가 이미 보이면 처음부터 `원본 저장`, `읽기 가속`, `비동기 handoff`를 분리해서 보는 편이 설계 대화가 훨씬 빨라진다.

---

## 헷갈릴 때 3문장 체크리스트

1. 이 데이터의 정답을 나중에도 다시 읽고 수정해야 하나?
2. 사용자가 지금 바로 결과를 알아야 하나, 아니면 뒤에 처리해도 되나?
3. 지금 문제는 "느린 읽기"인가, "느린 후처리"인가?

이 세 문장에 답하면 출발점이 꽤 선명해진다.

- `정답 저장`이 먼저면 `database`
- `느린 읽기`가 먼저면 `cache`
- `느린 후처리`가 먼저면 `queue`

---

## 다음으로 어디를 이어 읽나

- `cache는 알겠는데 stale이 무섭다`면 [캐시 기초](./caching-basics.md)
- `queue는 알겠는데 중복 재시도와 eventually consistent가 걱정된다`면 [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- `사용자가 지금 결과를 알아야 하는데 순서도 중요하다`면 [Per-Key Queue vs Direct API Primer](./per-key-queue-vs-direct-api-primer.md)
- `정답 저장소에서 commit이 왜 기준점이 되는지`를 먼저 잡고 싶다면 [트랜잭션 기초](../database/transaction-basics.md)

---

## 한 줄 정리

`database`는 정답을 남기는 곳, `cache`는 같은 읽기를 빠르게 다시 꺼내는 복사본, `queue`는 지금 안 끝내도 되는 일을 넘기는 handoff라고 잡으면 "언제 cache를 쓰고 언제 queue를 쓰는지"가 가장 빠르게 풀린다.
