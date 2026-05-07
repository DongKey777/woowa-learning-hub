---
schema_version: 3
title: vm.max_map_count mmap-heavy Apps
concept_id: operating-system/vm-max-map-count-mmap-heavy-apps
canonical: true
category: operating-system
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 83
review_feedback_tags:
- vm-max-map
- count-mmap-heavy
- apps
- count
aliases:
- vm.max_map_count
- mmap-heavy apps
- VMA count limit
- too many mappings
- mmap allocation failure
- virtual memory areas
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/page-table-overhead-memory-footprint.md
- contents/operating-system/mmap-vs-read-page-cache-behavior.md
- contents/operating-system/major-minor-page-faults-runtime-diagnostics.md
- contents/operating-system/memory-overcommit-semantics.md
- contents/operating-system/tlb-page-table-walk-bridge.md
symptoms:
- mmap-heavy application이 memory가 남아 있는데도 VMA count limit 때문에 mapping 실패를 겪는다.
- vm.max_map_count를 올렸지만 page table overhead와 fault cost도 함께 증가한다.
- 많은 작은 mappings 때문에 address space metadata 비용이 커진다.
expected_queries:
- vm.max_map_count는 mmap 기반 app의 VMA 수 상한이야?
- memory가 남아도 너무 많은 mapping 때문에 mmap이 실패할 수 있어?
- vm.max_map_count를 올릴 때 page table overhead와 fault cost도 봐야 해?
- mmap-heavy workload에서 VMA count와 memory footprint를 어떻게 진단해?
contextual_chunk_prefix: |
  이 문서는 vm.max_map_count를 mmap-heavy application이 가질 수 있는 virtual memory area count
  상한으로 설명한다. limit이 낮으면 large mapping workload가 먼저 실패하고, 높이면 metadata와
  page table overhead도 함께 고려해야 한다.
---
# vm.max_map_count, mmap-heavy Apps

> 한 줄 요약: `vm.max_map_count`는 mmap 기반 앱이 가질 수 있는 VMA 수의 상한이며, 너무 낮으면 대규모 매핑이 먼저 실패한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [Page Table Overhead, Memory Footprint](./page-table-overhead-memory-footprint.md)
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)

> retrieval-anchor-keywords: vm.max_map_count, VMA, mmap-heavy, map count, /proc/pid/maps, mmap failure, Elasticsearch, virtual memory area

## 핵심 개념

Linux는 프로세스가 매핑하는 메모리 구간을 VMA(virtual memory area) 단위로 관리한다. `vm.max_map_count`는 프로세스가 가질 수 있는 VMA 개수의 상한이다.

- `VMA`: 연속된 가상 메모리 구간을 나타내는 커널 자료구조다
- `vm.max_map_count`: 프로세스당 VMA 최대 개수 제한이다
- `mmap-heavy app`: 작은 매핑을 많이 만들어 쓰는 앱이다

왜 중요한가:

- search engine, JVM, DB, memory-mapped index처럼 많은 매핑을 쓰는 앱은 이 한도에 걸릴 수 있다
- 한도 초과는 느려지는 문제가 아니라 실패로 이어질 수 있다
- VMA 수는 page fault, page table overhead와도 연결된다

이 문서는 [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)와 [Page Table Overhead, Memory Footprint](./page-table-overhead-memory-footprint.md)를 매핑 관리 관점에서 잇는다.

## 깊이 들어가기

### 1. VMA는 많을수록 좋은 것이 아니다

VMA가 많아지면 커널은 더 많은 구간을 추적해야 한다.

- 개별 매핑 관리 비용이 늘어난다
- lookup과 fault handling이 복잡해진다
- 작은 매핑이 폭증하면 성능과 안정성이 흔들릴 수 있다

### 2. mmap-heavy 앱은 상한에 민감하다

다음 류의 앱은 주의해야 한다.

- 검색 인덱스 엔진
- 큰 파일을 shard 단위로 나눠 매핑하는 시스템
- 많은 plugin/module을 개별 mmap하는 앱
- memory-mapped cache를 자주 열고 닫는 앱

### 3. map count 초과는 곧바로 장애가 된다

한도를 넘으면 새 매핑이 실패할 수 있다.

- startup이 실패할 수 있다
- shard load가 깨질 수 있다
- 일부 기능만 비정상적으로 동작할 수 있다

### 4. `vm.max_map_count`는 단독 튜닝이 아니다

상한만 올린다고 끝나지 않는다.

- page table overhead가 늘 수 있다
- fault 처리 비용이 커질 수 있다
- 메모리 압박이 더 빨리 올 수 있다

## 실전 시나리오

### 시나리오 1: 큰 mmap 앱이 기동 중 실패한다

가능한 원인:

- `vm.max_map_count`가 낮다
- shard/segment 수가 너무 많다
- 매핑이 잘게 쪼개져 있다

진단:

```bash
cat /proc/sys/vm/max_map_count
wc -l /proc/<pid>/maps
cat /proc/<pid>/maps | head
```

### 시나리오 2: 데이터 양이 늘수록 startup이 더 느려진다

가능한 원인:

- map 수가 증가한다
- fault와 page table work가 늘어난다
- VMA lookup 비용이 커진다

### 시나리오 3: 일부 노드에서만 mmap 실패가 발생한다

가능한 원인:

- sysctl 값이 노드마다 다르다
- container runtime이 같은 설정을 안 쓴다
- workload density가 달라 VMA 사용량이 다르다

## 코드로 보기

### map count와 설정 확인

```bash
cat /proc/sys/vm/max_map_count
wc -l /proc/<pid>/maps
```

### `mmap()` 실패 감지 의사 코드

```c
void *p = mmap(NULL, len, PROT_READ, MAP_PRIVATE, fd, 0);
if (p == MAP_FAILED) {
    // handle ENOMEM or map-related failure
}
```

### map 폭증 감각

```text
many small mmap segments
  -> VMA count increases
  -> kernel bookkeeping increases
  -> map_count limit or overhead becomes visible
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `vm.max_map_count` 상향 | mmap-heavy 앱이 버틴다 | VMA overhead가 늘 수 있다 | search/index 서버 |
| 매핑 수 절감 | 커널 부담이 준다 | 앱 설계 수정이 필요하다 | 장기 최적화 |
| 큰 chunk로 매핑 | 관리가 단순해진다 | 접근 패턴이 안 맞을 수 있다 | large segment data |
| read 기반 전환 | 예측성이 좋다 | copy 비용이 늘 수 있다 | 단순 파일 I/O |

## 꼬리질문

> Q: `vm.max_map_count`는 무엇을 제한하나요?
> 핵심: 프로세스가 가질 수 있는 VMA 수를 제한한다.

> Q: `mmap()`을 많이 쓰면 왜 문제인가요?
> 핵심: VMA 관리와 page fault, page table 비용이 늘 수 있기 때문이다.

> Q: map count만 올리면 안전한가요?
> 핵심: 아니다. 오버헤드와 메모리 압박을 같이 봐야 한다.

## 한 줄 정리

`vm.max_map_count`는 mmap-heavy 앱의 실질적 상한이며, 너무 낮으면 startup 실패와 매핑 장애로 바로 이어질 수 있다.
