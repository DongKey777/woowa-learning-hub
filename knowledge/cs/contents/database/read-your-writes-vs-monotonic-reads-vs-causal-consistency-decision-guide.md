---
schema_version: 3
title: Read-Your-Writes vs Monotonic Reads vs Causal Consistency 결정 가이드
concept_id: database/read-your-writes-vs-monotonic-reads-vs-causal-consistency-decision-guide
canonical: false
category: database
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 88
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- read-your-writes-vs-monotonic
- causal-vs-freshness-ordering
- session-guarantee-token-scope
aliases:
- read your writes vs monotonic reads vs causal consistency
- session consistency guarantees chooser
- read after write monotonic causal difference
- 세션 일관성 보장 선택 가이드
- 방금 쓴 값 보기 vs 뒤로 가지 않기 vs 원인 결과 순서
- session guarantee 차이 한 번에 정리
- read-your-writes monotonic causal 차이
- replica 읽기 보장 뭐부터 봐야 해
symptoms:
- 저장 직후 안 보이는 문제와 새로고침할수록 옛값이 나오는 문제와 원인보다 결과가 먼저 보이는 문제를 한 가지 일관성 이슈로 뭉뚱그린다
- read-after-write만 고치면 세션 일관성 문제가 다 끝난다고 생각한다
- monotonic reads와 causal consistency를 둘 다 그냥 최신성 보장으로 기억하고 있다
intents:
- comparison
- troubleshooting
- design
prerequisites:
- database/replica-lag-read-after-write-strategies
next_docs:
- database/read-your-writes-session-pinning
- database/replica-lag-read-after-write-strategies
- database/client-consistency-tokens
linked_paths:
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/monotonic-reads-session-guarantees.md
- contents/database/causal-consistency-intuition.md
- contents/database/client-consistency-tokens.md
confusable_with:
- database/read-your-writes-session-pinning
- database/monotonic-reads-session-guarantees
- database/causal-consistency-intuition
forbidden_neighbors:
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-lag-read-after-write-strategies.md
expected_queries:
- write는 성공했는데 바로 안 보이는 것과 새로고침 후 더 옛값을 보는 것은 어떤 보장 차이로 이해해야 해?
- 같은 세션에서 시간이 뒤로 가지 않게 하는 것과 내가 쓴 값을 바로 보는 것은 뭐가 달라?
- 댓글이 본문보다 먼저 보이는 문제는 read-your-writes로 설명하면 왜 부족해?
- replica 라우팅 설계할 때 read-your-writes, monotonic reads, causal consistency 중 어디까지 필요할지 어떻게 고르지?
- 세션 일관성 질문이 나왔을 때 최신성 문제인지 관측 순서 문제인지 어떻게 먼저 가르면 돼?
contextual_chunk_prefix: |
  이 문서는 데이터베이스 학습자가 read-your-writes, monotonic reads,
  causal consistency를 모두 "replica 읽기에서 최신값 보장"으로만 묶을 때
  저장 직후 내 write를 다시 봐야 하는지, 한 번 본 최신선보다 뒤로
  가지 않게 해야 하는지, 원인과 결과의 관측 순서까지 지켜야 하는지를
  빠르게 갈라 주는 chooser다. write 성공 후 옛값이 보임, 새로고침할수록
  더 옛값을 봄, 댓글이 본문보다 먼저 보임, 멀티 탭과 멀티 디바이스에서
  session guarantee를 어디까지 강하게 해야 하나 같은 질문이 이 문서의
  결정 매트릭스와 오선택 패턴에 연결되도록 작성됐다.
---

# Read-Your-Writes vs Monotonic Reads vs Causal Consistency 결정 가이드

## 한 줄 요약

> 내 write가 바로 다시 보여야 하면 `Read-Your-Writes`, 한 번 본 최신선보다 뒤로 가지 않게 해야 하면 `Monotonic Reads`, 원인과 결과의 관측 순서까지 보장해야 하면 `Causal Consistency`를 먼저 본다.

## 결정 매트릭스

| 지금 먼저 막고 싶은 문제 | 1차 선택 | 왜 이 보장이 맞나 |
|---|---|---|
| `POST`는 성공했는데 직후 `GET`에서 내가 방금 바꾼 값이 안 보임 | `Read-Your-Writes` | "내가 쓴 것"이 최소 보장 단위라서 write 이후 read 경로를 최신선 위로 올리는 게 핵심이다 |
| 같은 세션에서 한 번 `PAID`를 봤다가 새로고침 후 `PENDING`으로 되돌아감 | `Monotonic Reads` | 이미 본 최신선보다 뒤로 가지 않는 관측 순서가 필요하다 |
| 댓글은 보이는데 본문은 아직 없거나 결제 완료가 보이는데 주문 생성은 안 보임 | `Causal Consistency` | 단순 최신성보다 원인과 결과의 dependency 순서를 함께 지켜야 한다 |
| 여러 탭과 여러 디바이스에서 "내가 마지막으로 본 시점"을 운반해야 함 | `Monotonic Reads` 또는 `Causal Consistency` + token 전달 | 서버 세션만으로는 기준선을 공유하기 어렵다 |

짧게 기억하면 `Read-Your-Writes`는 "내 write 확인", `Monotonic Reads`는 "내가 본 미래에서 후퇴 금지", `Causal Consistency`는 "원인 없는 결과 금지"에 가깝다.

## 흔한 오선택

가장 흔한 오선택은 저장 직후 옛값이 보였다는 이유만으로 바로 causal consistency를 꺼내는 것이다. 학습자 표현으로는 "최신값이 안 보이니까 제일 강한 일관성이 필요하네?"에 가깝다. 하지만 이 장면은 대부분 원인과 결과의 순서보다 먼저, 내 write를 다시 볼 최소 보장이 빠진 문제다.

반대로 `Read-Your-Writes`만 있으면 충분하다고 생각하는 것도 자주 틀린다. "한 번은 최신값을 봤으니 끝난 것 아닌가?"처럼 들리지만, 이후 요청이 더 늦은 replica를 타면 같은 세션 안에서도 시간이 뒤로 갈 수 있다. 이건 write visibility가 아니라 monotonic read 실패다.

`Monotonic Reads`와 `Causal Consistency`를 같은 말로 취급하는 것도 위험하다. 새로고침 후 옛값을 다시 보는 문제는 "내 관측선 후퇴"가 핵심이고, 댓글이 본문보다 먼저 보이는 문제는 "의존 관계 역전"이 핵심이다. 둘 다 순서 문제지만 지켜야 하는 기준선이 다르다.

## 다음 학습

저장 직후 내 값이 왜 안 보이는지부터 붙잡고 싶으면 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)과 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)로 내려가면 된다.

같은 세션에서 시간이 뒤로 가는 문제를 더 구체적으로 보고 싶으면 [Monotonic Reads와 Session Guarantees](./monotonic-reads-session-guarantees.md)를 이어 보면 된다.

원인과 결과의 의미 순서를 왜 별도 보장으로 봐야 하는지 확인하려면 [Causal Consistency 입문](./causal-consistency-intuition.md)과 [Client Consistency Tokens](./client-consistency-tokens.md)을 다음 문서로 잡으면 된다.
