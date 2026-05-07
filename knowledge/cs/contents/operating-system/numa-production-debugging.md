---
schema_version: 3
title: NUMA Production Debugging
concept_id: operating-system/numa-production-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- numa-production
- remote-memory-latency
- cpu-available-memory
- remote
aliases:
- NUMA production debugging
- remote memory latency
- CPU available memory remote
- numastat production
- memory locality p99
- NUMA backend latency
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/cpu-cache-coherence-memory-barrier.md
- contents/operating-system/context-switching-deadlock-lockfree.md
- contents/operating-system/numa-first-touch-remote-memory-locality-debugging.md
- contents/operating-system/numa-autobalancing-runtime-debugging.md
- contents/operating-system/cpu-affinity-irq-affinity-core-locality.md
- contents/operating-system/autonuma-vs-manual-locality-tradeoffs.md
symptoms:
- CPU 사용률은 낮아 보이는데 remote memory access 때문에 backend p99가 흔들린다.
- NUMA node별 memory placement와 worker CPU placement가 맞지 않는다.
- AutoNUMA migration cost와 manual locality tuning 중 어느 쪽을 볼지 판단해야 한다.
expected_queries:
- NUMA production debugging에서 CPU가 남아도 서버가 느린 이유는 remote memory 때문일 수 있어?
- numastat과 CPU affinity로 memory locality 문제를 어떻게 좁혀?
- remote memory latency와 backend p99를 연결해 설명해줘
- NUMA first-touch, AutoNUMA, cpuset을 운영에서 어떤 순서로 봐야 해?
contextual_chunk_prefix: |
  이 문서는 NUMA 환경에서 CPU가 남아 보여도 memory가 remote node에 있거나 migration/locality가
  맞지 않아 backend p99가 느려질 수 있다는 production debugging playbook이다.
---
# NUMA Production Debugging

> 한 줄 요약: NUMA 환경에서는 CPU가 남아 보여도 메모리 원격 접근 때문에 서버가 느려질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CPU 캐시, 코히어런시, 메모리 배리어](./cpu-cache-coherence-memory-barrier.md)
> - [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
> - [NUMA First-Touch, Remote Memory, Locality Debugging](./numa-first-touch-remote-memory-locality-debugging.md)
> - [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)

> retrieval-anchor-keywords: NUMA, production debugging, local memory, remote memory, first touch, numa_maps, numastat, locality, remote access, memory placement

## 핵심 개념

`NUMA`는 Non-Uniform Memory Access의 약자다.  
즉, CPU 코어가 있는 노드마다 메모리 접근 비용이 다르다.

왜 중요한가:

- 같은 머신인데도 어느 소켓의 메모리에 붙었는지에 따라 지연이 달라진다.
- 스레드가 메모리를 "가까운 곳"에서 보지 못하면 원격 접근 비용이 늘어난다.
- 대규모 JVM/DB 서버에서 이런 차이는 p99에 직접 나타난다.

## 깊이 들어가기

### 1. NUMA의 기본

멀티소켓 서버는 보통 각 소켓이 자기 메모리 컨트롤러를 가진다.  
그 결과:

- local memory access는 빠르다
- remote memory access는 느리다

즉 "메모리"가 하나처럼 보이지만 실제로는 노드별 비용이 다르다.

### 2. 왜 프로덕션에서 문제가 되는가

NUMA 문제는 보통 다음 상황에서 커진다.

- JVM heap이 한쪽 노드에 치우침
- thread가 다른 노드에서 돌면서 메모리를 계속 읽음
- DB buffer pool이나 page cache가 특정 소켓에 몰림

이 경우 CPU 사용률은 괜찮아 보여도 실제 메모리 지연이 성능을 깎는다.

### 3. first touch와 affinity

메모리는 첫 접근한 스레드/프로세스의 NUMA 노드에 배치되는 경우가 많다.  
그래서 부팅 직후 초기화 패턴이 중요하다.

- 초기화 스레드가 한 소켓에 몰리면 메모리도 몰림
- 워커가 다른 소켓에서 접근하면 remote access 증가

CPU affinity를 적절히 주는 이유가 여기 있다.

## 실전 시나리오

### 시나리오 1: CPU는 여유 있는데 latency가 높다

단일 서버에서 JVM CPU는 넉넉한데 p99만 높으면 NUMA를 의심할 수 있다.

진단:

```bash
numactl --hardware
numastat -p <pid>
cat /proc/<pid>/numa_maps | head
```

체크 포인트:

- 특정 노드에 메모리 편중이 있는가
- remote hit이 높은가
- 스레드가 한 소켓에 몰려 있는가

### 시나리오 2: Redis-like cache가 특정 노드에서만 느리다

메모리만 많이 쓰는 프로세스는 쉽게 한 노드에 치우친다.  
그 상태에서 다른 소켓의 코어가 접근하면 지연이 늘어난다.

### 시나리오 3: DB와 앱 서버를 같은 머신에 넣었더니 모두 느려진다

서로 메모리를 경쟁하면서 node locality가 깨질 수 있다.  
프로세스 하나의 문제가 아니라 host 전체의 placement 문제가 된다.

## 코드로 보기

### 관찰 커맨드

```bash
numastat -p <pid>
numactl --show
perf stat -e node-load-misses,node-loads -p <pid> -- sleep 10
```

### 간단한 배치 감각

```text
local access < remote access

같은 CPU 사용률이라도 remote access가 많으면 더 느릴 수 있다.
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| NUMA-aware 배치 | locality 개선 | 운영 복잡도 증가 | 대형 JVM/DB 서버 |
| 기본 OS 스케줄링 | 단순 | 편중 가능성 | 작은 서버/낮은 메모리 압력 |
| CPU affinity | 예측 가능성 높음 | 유연성 감소 | 고정된 워커/지연 민감 |
| 메모리 인터리빙 | 편중 완화 | local access 이점 감소 | 균형이 더 중요할 때 |

## 꼬리질문

> Q: NUMA에서 local memory와 remote memory는 왜 다르게 느린가?
> 의도: 메모리 컨트롤러와 소켓 구조 이해 여부 확인
> 핵심: 같은 RAM이라도 물리 경로가 다르다.

> Q: CPU 사용률이 낮은데도 서버가 느리면 NUMA를 의심해야 하는 이유는?
> 의도: 메모리 지연이 CPU 지표에 가려지는 문제 이해 여부 확인
> 핵심: 병목은 계산이 아니라 접근 경로일 수 있다.

> Q: CPU affinity를 무작정 걸면 왜 위험한가?
> 의도: locality와 스케줄링 유연성 trade-off 이해 여부 확인
> 핵심: locality를 얻는 대신 부하 분산을 잃을 수 있다.

## 한 줄 정리

NUMA는 CPU가 아니라 메모리의 거리 문제이므로, 프로덕션에서 느린 서버를 볼 때는 스케줄링보다 locality를 먼저 의심해야 한다.
