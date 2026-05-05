---
schema_version: 3
title: Failover 뒤 옛값/새값 번갈아 보임 원인 라우터
concept_id: database/failover-after-old-new-flip-symptom-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- failover-mixed-read-path
- stale-topology-cache
- write-fencing-after-promotion
aliases:
- failover 뒤 값이 왔다 갔다 함
- old new flip after failover
- 승격 후 일부 요청만 옛값
- failover 후 새로고침마다 값 바뀜
- promotion 뒤 데이터가 번갈아 보임
symptoms:
- failover 직후 새로고침할 때마다 어떤 요청은 새 값이고 어떤 요청은 옛 값이다
- 같은 API를 연속 호출했는데 pod나 요청마다 결과가 달라진다
- 승격은 끝났다는데 관리자 화면에서는 상태가 보였다가 사라진다
- 재시도하면 성공과 옛 결과가 번갈아 나와서 실제 저장 여부를 헷갈린다
intents:
- symptom
- troubleshooting
prerequisites:
- database/replica-lag-read-after-write-strategies
- database/read-your-writes-session-pinning
next_docs:
- database/failover-promotion-read-divergence
- database/replica-read-routing-anomalies
- database/commit-horizon-after-failover-verification
- database/primary-switch-write-fencing
linked_paths:
- contents/database/failover-promotion-read-divergence.md
- contents/database/replica-read-routing-anomalies.md
- contents/database/failover-visibility-window-topology-cache-playbook.md
- contents/database/commit-horizon-after-failover-verification.md
- contents/database/primary-switch-write-fencing.md
- contents/database/ghost-reads-mixed-routing-write-fence-tokens.md
confusable_with:
- database/replica-lag-read-after-write-strategies
- database/replica-read-routing-anomalies
- database/cache-replica-split-read-inconsistency
forbidden_neighbors:
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/read-your-writes-session-pinning.md
expected_queries:
- failover 뒤에 왜 어떤 요청은 새 값이고 어떤 요청은 옛 값이야?
- 승격 후 새로고침할 때마다 데이터가 번갈아 보이면 어디부터 봐야 해?
- failover는 끝났는데 pod마다 읽는 값이 다를 때 원인 분기가 뭐야?
- promotion 이후 재시도할 때 결과가 달라지면 topology 문제야 commit 유실 문제야?
- old primary가 아직 읽히는지 어떻게 빨리 가려?
contextual_chunk_prefix: |
  이 문서는 failover나 promotion 직후 같은 데이터를 새로고침할 때 옛값과
  새값이 번갈아 보이는 학습자 증상을 topology cache stale, old primary나
  replica mixed routing, commit horizon gap, write fencing 부재로 이어 주는
  symptom_router다. 승격 뒤 값이 왔다 갔다 함, pod마다 결과 다름, 어떤
  요청은 새값 어떤 요청은 옛값, 재시도하면 상태가 바뀜 같은 자연어 표현이
  이 문서의 분기와 매핑된다.
---

# Failover 뒤 옛값/새값 번갈아 보임 원인 라우터

## 한 줄 요약

> failover 뒤 값이 번갈아 보이면 단순 replica lag 하나로 닫지 말고, 읽기 경로가 아직 두 갈래인지, 새 primary가 어디까지 commit을 들고 있는지, 옛 writer가 아직 쓰는지부터 갈라야 한다.

## 가능한 원인

1. 일부 요청이 아직 old primary나 예전 replica를 읽는다. topology cache, DNS TTL, 커넥션 풀 재연결이 늦으면 같은 API도 경로가 갈린다. 이때는 [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md)와 [Failover Visibility Window, Topology Cache, and Freshness Playbook](./failover-visibility-window-topology-cache-playbook.md)로 간다.
2. write 후 retry가 서로 다른 replica를 타서 관측이 흔들린다. failover가 아니어도 생기지만, 전환 직후 더 심해진다. 이 분기는 [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md)으로 이어진다.
3. 새 primary가 최신 commit 전부를 포함하지 못했다. 보였다가 사라지는 것처럼 느껴져도 실제로는 uncertain gap일 수 있다. 이때는 [Commit Horizon After Failover, Loss Boundaries, and Verification](./commit-horizon-after-failover-verification.md)을 먼저 본다.
4. old primary나 오래된 worker의 늦은 write가 최신 상태를 덮는다. 읽기 문제처럼 보여도 실제 root cause는 write fencing 부재다. 이 분기는 [Primary Switch와 Write Fencing](./primary-switch-write-fencing.md)와 [Ghost Reads와 Mixed Routing Write Fence Tokens](./ghost-reads-mixed-routing-write-fence-tokens.md)로 간다.

## 빠른 자기 진단

1. 값이 갈린 순간 요청별 대상 노드를 먼저 본다. pod A/B, replica host, DNS 캐시, topology cache가 다르면 mixed routing 분기다.
2. 새 primary에서 직접 읽었을 때도 값이 비면 commit horizon을 의심한다. old primary와 새 primary의 "누가 authoritative인가"를 먼저 확정한다.
3. 읽기는 같아 보이는데 상태가 다시 뒤집히면 늦은 write 흔적을 찾는다. failover 직후 epoch, fencing, read-only 전환 로그가 없으면 write fencing 분기다.
4. recent write 사용자만 흔들리면 replica selection과 session 보장을 본다. 전 사용자 공통이면 topology 전환이나 horizon 검증 쪽이 더 가깝다.

## 다음 학습

- 승격 뒤 읽기 경로가 둘로 갈리는 모양 자체를 이해하려면 [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md)를 본다.
- retry, replica 선택, 세션 일관성 문제를 분리하려면 [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md)으로 간다.
- 진짜 유실 가능 구간인지 확인하려면 [Commit Horizon After Failover, Loss Boundaries, and Verification](./commit-horizon-after-failover-verification.md)을 본다.
- 옛 주체의 늦은 write 차단이 핵심이면 [Primary Switch와 Write Fencing](./primary-switch-write-fencing.md)와 [Ghost Reads와 Mixed Routing Write Fence Tokens](./ghost-reads-mixed-routing-write-fence-tokens.md)을 이어 읽는다.
