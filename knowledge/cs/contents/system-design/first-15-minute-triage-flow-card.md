---
schema_version: 3
title: First 15-Minute Triage Flow Card
concept_id: system-design/first-15-minute-triage-flow-card
canonical: false
category: system-design
difficulty: beginner
doc_role: deep_dive
level: beginner
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- first 15 minute triage flow card
- first 15-minute triage flow card
- starter matrix to dashboard panel
- fallback reason first dashboard panel
aliases:
- first 15 minute triage flow card
- first 15-minute triage flow card
- starter matrix to dashboard panel
- fallback reason first dashboard panel
- first response dashboard opener
- rejected hit starter matrix bridge
- stale dashboard first panel
- symptom path capacity triage card
- recent_write first panel
- min_version first panel
- replica_lag first panel
- watermark first panel
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/rejected-hit-observability-primer.md
- contents/system-design/post-write-stale-dashboard-primer.md
- contents/system-design/read-after-write-routing-primer.md
- contents/system-design/mixed-cache-replica-freshness-bridge.md
- contents/system-design/mixed-cache-replica-read-path-pitfalls.md
- contents/system-design/dashboard-restatement-ux-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- First 15-Minute Triage Flow Card 설계 핵심을 설명해줘
- first 15 minute triage flow card가 왜 필요한지 알려줘
- First 15-Minute Triage Flow Card 실무 트레이드오프는 뭐야?
- first 15 minute triage flow card 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 First 15-Minute Triage Flow Card를 다루는 deep_dive 문서다. `fallback_reason`를 봤을 때 바로 어느 dashboard panel부터 열지와 첫 15분 안에 어떤 한 문장으로 상황을 정리할지를 한 화면으로 묶어 둔 초보자용 연결 카드다. 검색 질의가 first 15 minute triage flow card, first 15-minute triage flow card, starter matrix to dashboard panel, fallback reason first dashboard panel처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# First 15-Minute Triage Flow Card

> 한 줄 요약: `fallback_reason`를 봤을 때 바로 어느 dashboard panel부터 열지와 첫 15분 안에 어떤 한 문장으로 상황을 정리할지를 한 화면으로 묶어 둔 초보자용 연결 카드다.

retrieval-anchor-keywords: first 15 minute triage flow card, first 15-minute triage flow card, starter matrix to dashboard panel, fallback reason first dashboard panel, first response dashboard opener, rejected hit starter matrix bridge, stale dashboard first panel, symptom path capacity triage card, recent_write first panel, min_version first panel, replica_lag first panel, watermark first panel, replica_error first panel, beginner first response triage, first 15 minute triage flow card basics

**난이도: 🟢 Beginner**

관련 문서:

- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Dashboard Restatement UX 설계](./dashboard-restatement-ux-design.md)
- [system-design 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

---

## 먼저 잡을 mental model

처음 15분은 원인을 완전히 증명하는 시간이 아니라, **어느 panel부터 열어야 첫 대응이 안 빗나가는지**를 정하는 시간이다.

짧게 외우면 이 순서다.

- `reason`은 출발 버튼이다
- `panel`은 첫 확인 화면이다
- `첫 문장`은 팀에 바로 공유할 임시 판정이다

즉, 초보자용 첫 대응은 "로그 reason을 봤다 -> 맞는 panel 1개를 먼저 연다 -> 증상/경로/용량 중 무엇이 먼저 흔들렸는지 한 문장으로 말한다"로 끝내면 된다.

---

## 한 화면 flow card

```text
alert / log / trace에서 fallback_reason 또는 rejected_hit_reason를 봄
            |
            v
   1. 먼저 어느 종류인지 고른다
      - 사용자 체감 stale를 바로 의심? -> Symptom panel
      - 경로 선택이 이상해 보임?      -> Path panel
      - primary 버틸지 걱정됨?        -> Capacity panel
            |
            v
   2. reason별 첫 panel 하나만 연다

      recent_write -----------------> fallback headroom
           |                         (정상 보호인지, primary 여유가 남는지)
           |
           +-> stale도 같이 왔나? ----> post-write stale rate

      min_version -----------------> read source distribution
           |                         (어느 route에서 version floor를 못 맞추는지)
           |
           +-> stale 체감 확인 ------> post-write stale rate

      replica_lag ----------------> read source distribution
           |                         (replica 쏠림인지, primary fallback 증가인지)
           |
           +-> lag가 길게 가나? -----> fallback headroom

      watermark ------------------> post-write stale rate
           |                         (token 전달 누락이 실제 stale로 보였는지)
           |
           +-> source 왜곡 확인 -----> read source distribution

      replica_error --------------> fallback headroom
                                     (장애 회피가 primary 병목으로 번지는지)
            |
            v
   3. 첫 응답 문장을 고른다
      - Symptom 먼저 흔들림  -> "사용자 visible stale이 먼저 커졌습니다."
      - Path 먼저 흔들림     -> "특정 source/routing 경로 쏠림이 먼저 보입니다."
      - Capacity 먼저 흔들림 -> "보호 동작은 있지만 primary headroom이 먼저 위험합니다."
            |
            v

## 한 화면 flow card (계속 2)

4. 아직 열지 않을 것
      - 사용자-facing correction 설명이 필요할 때만 Dashboard Restatement UX로 간다
      - 첫 15분에는 deep dive보다 첫 panel 선택을 먼저 끝낸다
```

---

## Reason -> First Panel 빠른 매핑표

| 로그에서 먼저 본 값 | starter-matrix의 첫 행동 | 제일 먼저 열 panel | 첫 문장 예시 |
|---|---|---|---|
| `recent_write` | write 직후 경로와 `primary_fallback_total`를 같이 본다 | `fallback headroom` | "write 피크 보호 동작인지 먼저 보겠습니다. 지금은 primary 여유가 남는지가 1순위입니다." |
| `min_version` | version gap 큰 route를 상위 몇 개로 좁힌다 | `read source distribution` | "version floor를 못 맞추는 route가 어디로 몰리는지부터 보겠습니다." |
| `replica_lag` | replica lag가 route budget을 넘는지 대조한다 | `read source distribution` | "replica 쏠림인지, 이미 primary fallback으로 넘긴 상태인지 먼저 가르겠습니다." |
| `watermark` | required watermark 전달 누락을 trace 1개로 확인한다 | `post-write stale rate` | "전달 누락이 실제 stale 증상으로 보였는지부터 확인하겠습니다." |
| `replica_error` | timeout/connection 급증인지 분리한다 | `fallback headroom` | "replica 장애 회피가 primary headroom을 얼마나 먹는지 먼저 보겠습니다." |

헷갈리면 이렇게 외우면 된다.

| 먼저 떠오르는 질문 | 먼저 열 panel |
|---|---|
| 사용자에게 옛값이 실제로 보였나 | `post-write stale rate` |
| cache/replica/primary 중 어디로 쏠렸나 | `read source distribution` |
| primary로 더 보내도 버티나 | `fallback headroom` |

---

## 15분 안에 쓰는 작은 비교표

| panel | 이 panel이 답하는 질문 | 초보자 첫 행동 |
|---|---|---|
| `post-write stale rate` | 사용자가 틀린 값을 실제로 봤나 | "증상이 진짜인지"를 먼저 확인한다 |
| `read source distribution` | 어느 source가 먼저 흔들렸나 | cache/replica/primary 경로를 좁힌다 |
| `fallback headroom` | 보호 동작을 더 써도 버티나 | primary 보호가 급한지 먼저 가른다 |

핵심은 panel 세 개를 다 보는 것이 아니라, **reason에 맞는 첫 panel 1개부터 여는 것**이다.

---

## 주문 상세 예시

주문 결제 직후 `GET /orders/{id}`에서 아래 로그가 먼저 보였다고 하자.

```text
event=replica_primary_fallback
fallback_reason=min_version
min_required_version=42
replica_visible_version=41
selected_source=primary
```

초보자 첫 대응은 이렇게 읽는다.

1. `min_version`이므로 "version 기준선을 못 맞춘 route를 좁히는 단계"라고 판단한다.
2. 첫 panel은 `read source distribution`을 연다.
3. 여기서 replica 비중이 갑자기 커졌는지, primary fallback이 이미 커졌는지 먼저 본다.
4. 그다음에 `post-write stale rate`를 열어 실제 사용자 증상이 같이 커졌는지 확인한다.

첫 문장 예시는 이 정도면 충분하다.

> "`min_version` 로그가 먼저 보여서 source 분포부터 확인 중입니다. 지금은 어떤 route가 기준선을 못 맞추는지 좁히는 단계입니다."

---

## 자주 헷갈리는 점

- `recent_write`를 봤다고 바로 `post-write stale rate`부터 여는 건 아니다. 먼저 `fallback headroom`을 봐야 정상 보호인지 capacity 위험인지 가를 수 있다.
- `replica_lag`를 봤다고 바로 infra 문제로 단정하면 안 된다. `read source distribution`을 봐야 routing 누락과 lag 급증을 분리할 수 있다.
- `watermark`는 trace에서 보인다고 끝이 아니다. 사용자 체감 stale로 이어졌는지 `post-write stale rate`에서 같이 확인해야 한다.
- `Dashboard Restatement UX`는 사용자-facing correction 설명 문서다. runtime first response에서 여는 첫 panel은 아니다.

---

## 다음으로 어디를 읽나

- starter-matrix 자체를 먼저 익히려면 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- 세 panel의 뜻과 정상 범위를 익히려면 [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- 왜 `recent_write`와 `min_version`이 같은 stale라도 다른 대응으로 이어지는지 보려면 [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- 용어가 `recent-write`인지 `recent_write`인지 헷갈리면 [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- 사용자 공지나 corrected badge까지 설계해야 하면 [Dashboard Restatement UX 설계](./dashboard-restatement-ux-design.md)

## 한 줄 정리

`fallback_reason`를 봤을 때 바로 어느 dashboard panel부터 열지와 첫 15분 안에 어떤 한 문장으로 상황을 정리할지를 한 화면으로 묶어 둔 초보자용 연결 카드다.
