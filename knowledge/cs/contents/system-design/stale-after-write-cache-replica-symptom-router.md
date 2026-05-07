---
schema_version: 3
title: '방금 쓴 값이 다시 옛값으로 보임 — Cache / Replica / Projection freshness 분기'
concept_id: system-design/stale-after-write-cache-replica-symptom-router
canonical: false
category: system-design
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: mixed
source_priority: 86
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- read-after-write-staleness
- cache-replica-freshness
- projection-lag
- min-version-token
aliases:
- 방금 쓴 값이 옛값
- stale after write
- cache replica stale read
- read after write 깨짐
- projection lag after update
- min version freshness
symptoms:
- 수정 직후 상세 화면이나 목록에서 이전 값이 다시 보인다
- 캐시를 지웠는데도 replica나 projection에서 오래된 값이 돌아온다
- 새로고침을 여러 번 하면 최신값과 옛값이 번갈아 보인다
intents:
- symptom
- troubleshooting
prerequisites:
- system-design/read-after-write-consistency-basics
- system-design/caching-vs-read-replica-primer
next_docs:
- system-design/mixed-cache-replica-freshness-bridge
- system-design/cache-acceptance-rules-for-causal-reads
- database/replica-lag-read-after-write-strategies
linked_paths:
- contents/system-design/read-after-write-consistency-basics.md
- contents/system-design/caching-vs-read-replica-primer.md
- contents/system-design/mixed-cache-replica-freshness-bridge.md
- contents/system-design/cache-hit-miss-session-policy-bridge.md
- contents/system-design/cache-acceptance-rules-for-causal-reads.md
- contents/system-design/trace-attribute-freshness-read-source-bridge.md
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/causal-consistency-intuition.md
confusable_with:
- system-design/mixed-cache-replica-freshness-bridge
- system-design/cache-hit-miss-session-policy-bridge
- database/replica-lag-read-after-write-strategies
forbidden_neighbors:
- contents/system-design/caching-basics.md
expected_queries:
- 방금 수정한 값이 다시 예전 값으로 보이면 cache랑 replica 중 어디부터 봐?
- 캐시를 지웠는데도 stale read가 남는 이유를 분기해줘
- read-after-write가 깨질 때 min-version이나 causal token을 어디에 붙여?
- 목록은 최신인데 상세는 옛값이거나 반대면 어떤 freshness 문제야?
contextual_chunk_prefix: |
  이 문서는 쓰기 직후 옛값이 다시 보이는 증상을 cache hit, replica fallback,
  projection lag, freshness token 누락으로 나누는 system-design symptom_router다.
  방금 수정했는데 옛값, 캐시 지웠는데도 stale, 목록/상세 불일치, replica lag,
  min-version과 causal token 같은 질의를 read-after-write consistency 진단으로 연결한다.
---
# 방금 쓴 값이 다시 옛값으로 보임 — Cache / Replica / Projection freshness 분기

> 한 줄 요약: stale-after-write는 "캐시가 문제" 한 마디로 끝나지 않는다. 캐시 히트 허용 조건, 캐시 미스 뒤 replica 선택, projection 적용 지연, 클라이언트 freshness token 전달을 순서대로 봐야 한다.

**난이도: 🟡 Intermediate**

## 증상을 네 갈래로 자르기

### 1. 캐시 히트가 너무 쉽게 허용된다

장면:

- 방금 업데이트했는데 cache hit가 그대로 반환된다.
- 캐시 TTL은 짧지만 그 TTL 안에서는 옛값이 보인다.

확인:

- 최근 write를 한 세션인지 알 수 있는가
- `min-version`이나 `updated_at` 기준으로 hit를 거절할 수 있는가
- stale hit를 거절했을 때 어디로 fallback하는가

### 2. 캐시 미스 뒤 replica가 더 오래됐다

장면:

- 캐시를 삭제했는데도 옛값이 나온다.
- primary를 보면 최신이고 replica를 보면 이전 값이다.

확인:

- 최근 write 이후 read를 replica로 보내도 되는 정책인가
- session stickiness, causal token, primary fallback 기준이 있는가
- lag metric을 응답 trace에 남기는가

### 3. projection이나 read model이 아직 적용되지 않았다

장면:

- 원장 테이블은 최신인데 목록/검색/알림 read model은 이전 상태다.
- 이벤트 consumer lag가 있거나 outbox relay가 지연된다.

확인:

- read model의 applied watermark를 알 수 있는가
- 화면이 요구하는 최소 version보다 projection이 뒤처졌는가
- 지연 시 pending/processing 상태를 보여줄 수 있는가

### 4. 클라이언트가 freshness context를 잃어버린다

장면:

- 저장 직후 첫 화면은 최신인데 다음 탭이나 새 요청에서 옛값이 보인다.
- API gateway, BFF, frontend store 중 어딘가에서 version token이 빠진다.

확인:

- write 응답에 version이나 causal token을 돌려주는가
- 후속 read 요청이 그 token을 전달하는가
- cache, replica, projection이 같은 token을 해석하는가

## 먼저 남길 관측값

```text
read_source=cache|replica|primary|projection
hit_accept_reason=ttl_ok|min_version_ok|unchecked
required_version=<client_min_version>
served_version=<response_version>
replica_lag_ms=<observed_lag>
projection_watermark=<applied_event_id>
```

이 값이 없으면 "가끔 옛값"이라는 말만 남고 원인을 재현하기 어렵다.

## 꼬리질문

> Q: 캐시를 지우면 read-after-write 문제가 끝나나요?
> 핵심: 아니다. 캐시 미스 뒤 replica나 projection으로 내려가면 여전히 stale일 수 있다.

> Q: stale read를 완전히 없애려면 항상 primary만 읽어야 하나요?
> 핵심: 비용이 크다. 최근 write가 있는 세션이나 중요한 화면에만 freshness token 기반 primary/fresh source를 요구하는 식으로 좁힌다.

## 한 줄 정리

방금 쓴 값이 옛값으로 보이면 캐시만 보지 말고 `cache hit 허용 -> replica fallback -> projection watermark -> client freshness token` 순서로 자른다.
