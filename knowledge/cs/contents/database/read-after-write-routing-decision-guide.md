---
schema_version: 3
title: Read-After-Write 라우팅 결정 가이드
concept_id: database/read-after-write-routing-decision-guide
canonical: false
category: database
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 88
mission_ids:
- missions/shopping-cart
- missions/roomescape
review_feedback_tags:
- read-after-write-routing
- primary-fallback-vs-session-pinning
- strict-read-window
aliases:
- read-after-write routing chooser
- primary fallback vs session pinning vs consistency token
- recent write read path 선택
- 저장 직후 조회 라우팅 가이드
- strict read window 설계
- replica lag 대응 읽기 전략 선택
- post-write freshness routing
- roomescape 예약 직후 조회 stale
- 저장은 됐는데 첫 조회만 옛값
symptoms:
- 저장은 성공했는데 직후 조회만 가끔 옛값이라 어떤 읽기 전략을 먼저 써야 할지 헷갈린다
- 모든 read를 primary로 보낼지, 세션만 묶을지, token으로 판정할지 결정 축이 섞인다
- 결제 직후 상세는 최신인데 목록이나 다른 화면은 흔들려 strict read 범위를 어디까지 잡아야 할지 모르겠다
- roomescape에서 예약 생성은 성공했는데 목록이나 가능 시간 첫 조회만 이전 상태처럼 보여 read path를 어떻게 나눌지 모르겠다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/replica-lag-read-after-write-strategies
- database/read-your-writes-vs-monotonic-reads-vs-causal-consistency-decision-guide
next_docs:
- database/read-your-writes-session-pinning
- database/replica-lag-read-after-write-strategies
- design-pattern/session-pinning-vs-version-gated-strict-reads
linked_paths:
- contents/database/roomescape-reservation-create-read-after-write-bridge.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/read-your-writes-vs-monotonic-reads-vs-causal-consistency-decision-guide.md
- contents/design-pattern/session-pinning-vs-version-gated-strict-reads.md
- contents/database/cache-replica-split-read-inconsistency.md
confusable_with:
- database/roomescape-reservation-create-read-after-write-bridge
- database/read-your-writes-session-pinning
- database/replica-lag-read-after-write-strategies
- database/read-your-writes-vs-monotonic-reads-vs-causal-consistency-decision-guide
- database/cache-replica-split-read-inconsistency
forbidden_neighbors:
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-lag-read-after-write-strategies.md
expected_queries:
- write 직후 첫 조회만 안전하게 만들려면 primary fallback, session pinning, token 방식 중 무엇부터 고르면 돼?
- 저장 후 상세 화면은 바로 보여야 하지만 전체 세션을 오래 primary에 묶고 싶지 않을 때 어떤 전략이 맞아?
- replica lag가 있을 때 짧은 strict read window를 primary fallback으로 둘지 session pinning으로 둘지 판단 기준이 뭐야?
- 주문 생성 뒤 상세와 목록이 서로 다른 freshness를 보이면 consistency token 같은 판정을 언제 도입해야 해?
- read-after-write 문제를 해결하려고 모든 조회를 primary로 보내기 전에 어떤 분기부터 생각해야 해?
- roomescape에서 예약 생성 직후 목록이나 가능 시간이 한 번만 늦을 때 primary fallback부터 볼지 session pinning부터 볼지 어떻게 정해?
contextual_chunk_prefix: |
  이 문서는 학습자가 write 직후 stale read를 막으려 할 때 primary fallback,
  session pinning, consistency token이나 version gate를 모두 같은 라우팅
  버튼으로 이해하는 혼선을 풀기 위한 chooser다. 첫 조회만 primary로
  보내야 하나, 사용자 세션 몇 초를 묶어야 하나, 상세와 목록이 서로 다른
  projection일 때 token 판정이 필요한가, recent write window를 어디까지
  strict 하게 잡아야 하나 같은 자연어 질문이 이 문서의 결정 매트릭스와
  오선택 패턴에 연결되도록 작성됐다.
---

# Read-After-Write 라우팅 결정 가이드

> 한 줄 요약: 직후 한두 번의 조회만 안전하면 `primary fallback`, 같은 사용자 여정의 여러 화면이 함께 뒤로 가지 않게 해야 하면 `session pinning`, 화면별로 "이 버전 이상을 봤는가"를 판정해야 하면 `consistency token` 또는 version gate를 먼저 본다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Roomescape Reservation Create Read-After-Write Bridge](./roomescape-reservation-create-read-after-write-bridge.md)
- [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
- [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)
- [Read-Your-Writes vs Monotonic Reads vs Causal Consistency](./read-your-writes-vs-monotonic-reads-vs-causal-consistency-decision-guide.md)
- [Cache/Replica Split Read Inconsistency](./cache-replica-split-read-inconsistency.md)
- [Session Pinning vs Version-Gated Strict Reads](../design-pattern/session-pinning-vs-version-gated-strict-reads.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: read after write routing, primary fallback vs session pinning, consistency token basics, strict read window chooser, replica lag read path, stale first read why, write 직후 조회 라우팅, 저장 직후 옛값 왜, 언제 primary fallback, 언제 session pinning, version gate 뭐예요, recent write flow basics

## 먼저 잡는 멘탈 모델

이 문서는 "저장은 됐는데 다음 화면만 가끔 옛값"일 때 어떤 read path를 먼저 골라야 하는지 정하는 chooser다.

먼저 질문을 세 갈래로 나누면 덜 헷갈린다.

- 한 번의 조회만 안전하면 되는가
- 같은 사용자 여정의 여러 화면이 함께 안 뒤로 가야 하는가
- 화면이 "최소 이 버전 이상"을 직접 증명해야 하는가

짧게 기억하면 `primary fallback`은 "짧은 우회", `session pinning`은 "짧은 여정 고정", `consistency token`은 "화면별 freshness 증명"에 가깝다.

## 한눈에 고르는 표

| 지금 먼저 해결할 질문 | 1차 선택 | 왜 이 전략이 맞나 |
|---|---|---|
| 저장 직후 다음 조회 한 번만 stale이면 안 됨 | `primary fallback` | strict window가 아주 짧고 범위가 좁아서 가장 단순하게 freshness를 보장한다 |
| 상세, 목록, 배지처럼 여러 화면이 같은 recent-write 여정 안에서 함께 안 뒤로 가야 함 | `session pinning` | 화면마다 read route가 흔들리면 사용자가 모순을 느끼므로 actor 단위로 짧게 묶는 편이 낫다 |
| 단건 상세나 projection이 "이 version 이상을 반영했는가"를 스스로 판정할 수 있음 | `consistency token` / version gate | 세션 전체를 묶지 않고도 필요한 화면만 정확히 strict 하게 만들 수 있다 |
| cache와 replica가 섞여 stale source 자체가 갈라질 수 있음 | source split부터 분리 | 라우팅 전략보다 먼저 어떤 경로가 옛값을 주는지 확인해야 헛핀닝을 피한다 |
| 관리자 화면처럼 여러 번 읽지만 write actor는 제한적임 | hybrid | 첫 조회는 fallback, 이후 strict screen만 pinning 또는 token으로 줄이는 편이 비용 대비 안정적이다 |

## `primary fallback`이 먼저인 경우

가장 단순한 장면은 "쓰기 직후 상세 한 번만 최신이면 된다"다. 예를 들어 주문 생성 뒤 상세 화면 한 번만 정확하면 되고, 그 다음 목록은 조금 늦어도 괜찮다면 `primary fallback`이 보통 첫 선택이다.

예시:

| 화면 | 요구 freshness | 첫 선택 |
|---|---|---|
| 주문 생성 직후 상세 | 바로 최신 | primary로 한 번 우회 |
| 주문 목록 | 몇 초 뒤 반영 가능 | 기존 replica 또는 projection 유지 |

이 방식이 좋은 이유는 strict read 범위를 가장 짧게 잡기 때문이다. "전체 세션을 묶을 필요는 없고, 한 번만 안 틀리면 된다"라는 질문에 잘 맞는다.

## `session pinning`이 먼저인 경우

같은 사용자 여정에서 상세, 목록, 배지, 가능 시간처럼 여러 화면이 함께 안 뒤로 가야 하면 `session pinning`이 더 자연스럽다. 한 화면은 최신이고 다음 화면은 옛값이면 사용자는 "저장이 안 됐나?"라고 느끼기 쉽기 때문이다.

roomescape 예시로 보면 예약 생성 직후에:

- 상세는 새 예약이 보이는데
- 가능 시간 목록은 예전 slot처럼 보이고
- 관리자 목록은 한 박자 늦게 따라오면

각 화면마다 fallback을 따로 붙이기보다 recent-write window 동안 같은 actor의 read route를 짧게 고정하는 편이 설명하기 쉽다.

## `consistency token` 또는 version gate가 먼저인 경우

화면이 "최소 이 version 이상을 읽어야 한다"를 스스로 판단할 수 있으면 token 방식이 강해진다. 이때는 세션 전체를 primary에 묶지 않고도 필요한 projection만 엄격하게 볼 수 있다.

대표 장면:

- 상세 화면이 write 결과의 version이나 watermark를 알고 있다
- projection이 applied version을 노출한다
- 여러 화면 중 일부만 strict read가 필요하다

주의할 점도 있다. token은 가장 정교하지만 구현 복잡도도 가장 빨리 커진다. "상세 한 번만 최신이면 끝"인 문제를 token으로 시작하면 오히려 과설계가 되기 쉽다.

## 흔한 혼동과 오선택

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "그럼 그냥 전부 primary로 읽으면 끝 아닌가?" | 문제 범위가 한두 화면인지 세션 전체인지 안 나눠 primary 부하만 키우기 쉽다 | strict read window를 먼저 짧게 정의한다 |
| "`session pinning` 하나면 다 해결된다" | pinned route여도 projection 자체가 아직 필요한 version을 못 봤을 수 있다 | 화면별 freshness 증명이 필요한지 따로 본다 |
| "token이 제일 정교하니 무조건 정답이다" | 상세 한 화면만 막으면 되는 장면에서도 구현 복잡도만 커질 수 있다 | token은 version 판단이 실제로 필요한 화면에만 쓴다 |
| "pinning을 했는데도 stale이 보이니 DB 설정이 틀렸다" | cache와 replica 등 stale source가 여러 곳이면 라우팅만 바꿔도 안 잡힌다 | source split부터 분리한다 |

## 다음 문서 고르기

| 지금 더 궁금한 것 | 다음 문서 |
|---|---|
| 세션 단위 recent-write window를 어떻게 잡는지 | [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md) |
| replica lag, primary fallback, stale source 분리 전체 | [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md) |
| version gate와 strict screen 비교 | [Session Pinning vs Version-Gated Strict Reads](../design-pattern/session-pinning-vs-version-gated-strict-reads.md) |
| roomescape 예약 직후 stale read를 미션 맥락으로 보기 | [Roomescape Reservation Create Read-After-Write Bridge](./roomescape-reservation-create-read-after-write-bridge.md) |

## 한 줄 정리

read-after-write 라우팅은 "전부 primary냐 아니냐" 문제가 아니라, 한 번의 조회를 보호할지, 짧은 사용자 여정을 고정할지, 화면별 freshness를 증명할지부터 나누는 문제다.
