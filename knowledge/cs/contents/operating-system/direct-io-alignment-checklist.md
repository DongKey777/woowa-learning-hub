---
schema_version: 3
title: Direct IO Alignment Checklist
concept_id: operating-system/direct-io-alignment-checklist
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- direct-io-alignment
- o-direct-buffer
- alignment
- direct-io-offset
aliases:
- Direct IO alignment checklist
- O_DIRECT buffer alignment
- direct IO offset length alignment
- direct IO EINVAL
- page cache bypass contract
- storage alignment
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/buffered-vs-direct-io-mixing-coherency-pitfalls.md
- contents/operating-system/page-cache-thrash-vs-direct-io.md
- contents/operating-system/page-cache-dirty-writeback-fsync.md
- contents/operating-system/dirty-throttling-balance-dirty-pages-writeback-stalls.md
- contents/operating-system/blk-mq-cgroup-io-writeback-timeline-debugging.md
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
- contents/operating-system/io-scheduler-blk-mq-basics.md
symptoms:
- O_DIRECT를 켰지만 buffer address, length, offset alignment가 맞지 않아 EINVAL이나 fallback이 난다.
- direct I/O로 page cache를 우회하려 했지만 alignment와 storage path 때문에 더 느려진다.
- 같은 파일에서 buffered/direct mixing까지 겹쳐 장애 분석이 어려워진다.
expected_queries:
- Direct I/O는 buffer address length offset alignment를 왜 맞춰야 해?
- O_DIRECT가 켜졌는데 EINVAL이나 성능 저하가 나는 체크리스트를 알려줘
- direct I/O를 켜기만 하면 page cache 우회 최적화가 자동으로 되는 거야?
- direct I/O alignment와 blk-mq, dirty writeback timeline은 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 direct I/O가 켜기만 하는 최적화가 아니라 buffer, address, length, offset,
  filesystem/block device alignment 계약을 만족해야 의미가 있다는 점을 checklist로 설명한다.
---
# Direct I/O Alignment Checklist

> 한 줄 요약: direct I/O는 켜기만 하면 되는 최적화가 아니라, buffer/address/length/offset/alignment 계약을 만족해야 의미가 있고, 이 계약이 흐리면 성능은 안 좋아지고 장애 분석만 어려워진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Buffered vs Direct I/O Mixing, Coherency Pitfalls](./buffered-vs-direct-io-mixing-coherency-pitfalls.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Dirty Throttling, balance_dirty_pages, Writeback Stalls](./dirty-throttling-balance-dirty-pages-writeback-stalls.md)
> - [blk-mq, cgroup IO, Writeback Timeline Debugging](./blk-mq-cgroup-io-writeback-timeline-debugging.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [I/O Scheduler, blk-mq Basics](./io-scheduler-blk-mq-basics.md)
> - [posix_fadvise, madvise, Page Cache Hints](./posix-fadvise-madvise-page-cache-hints.md)

> retrieval-anchor-keywords: direct I/O alignment, O_DIRECT checklist, aligned buffer, aligned offset, aligned length, block size alignment, direct I/O debugging, alignment pitfalls, O_DIRECT errors, O_DIRECT EINVAL, logical block size, minimum_io_size, statx dioalign, fallback to buffered, direct vs buffered timeline

## 핵심 개념

`O_DIRECT`의 첫 번째 문제는 coherency가 아니라 alignment다. 즉 direct I/O는 "캐시를 우회한다"보다 먼저 "이 버퍼 주소, 길이, 오프셋이 이 파일시스템/디바이스의 제약과 맞는가"를 확인해야 한다.

- `buffer alignment`: user buffer 주소 정렬 조건이다
- `length alignment`: I/O 길이 정렬 조건이다
- `offset alignment`: file offset 정렬 조건이다
- `block size`: backing device/filesystem이 의미 있게 요구하는 정렬 단위다
- `failure semantics`: mismatch 시 즉시 실패할지, 우회 경로를 탈지에 대한 계약이다

왜 중요한가:

- direct I/O 실패는 성능 이슈가 아니라 correctness/error handling 이슈로 먼저 드러날 수 있다
- alignment가 안 맞으면 fallback, retry, hidden copy가 섞여 더 헷갈릴 수 있다
- "직접 I/O로 바꿨는데 왜 안 빨라지지?"의 시작점이 대부분 정렬 계약이다
- direct I/O는 dirty throttling을 우회할 수 있지만, blk-mq queueing과 cgroup I/O 경쟁까지 사라지지는 않는다

## 깊이 들어가기

### 1. direct I/O는 "정렬된 경로"를 요구한다

운영 감각으로 가장 먼저 볼 체크리스트는 이 셋이다.

- 버퍼 주소가 충분히 정렬됐는가
- I/O 길이가 정렬 단위를 만족하는가
- 파일 오프셋이 정렬됐는가

이 중 하나라도 어긋나면 direct I/O는 기대처럼 동작하지 않거나, 구현/환경에 따라 실패 또는 비싼 우회 경로가 생길 수 있다.

### 2. alignment 단위는 코드 상수로 단순화하면 위험하다

많은 코드가 4096 같은 상수를 박아 넣지만, 운영에서는 다음이 다를 수 있다.

- logical block size
- physical block size
- minimum I/O size / optimal I/O size
- filesystem 제약
- device path 차이
- deployment 환경 차이

즉 "로컬에서 됐다"가 곧 "프로덕션에서도 안전하다"는 뜻은 아니다.

운영 감각으로는 "정렬 단위가 하나 있다"보다 "이 경로에 겹치는 제약이 여러 층에 있다"가 더 정확하다.

- page size 정렬만 맞아도 파일시스템 direct-I/O 제약은 더 엄격할 수 있다
- device queue geometry가 바뀌면 같은 길이/오프셋도 비효율적일 수 있다
- 가능하면 path별 direct-I/O alignment를 조회하고, 안 되면 filesystem + block device 정보를 함께 본다

즉 `4KiB면 끝`이 아니라 `이 파일 경로의 direct path가 무엇을 요구하는가`를 먼저 확인해야 한다.

### 3. performance tuning 전에 failure mode를 먼저 고정해야 한다

direct I/O를 도입할 때는 보통 throughput/latency만 본다. 하지만 먼저 고정해야 하는 것은 실패 시 계약이다.

- alignment mismatch면 명시적으로 실패할 것인가
- buffered fallback을 허용할 것인가
- mixed path coherency를 어떻게 문서화할 것인가

이 계약이 없으면 운영자가 관측하는 현상은 "가끔만 느리다/가끔만 틀린다"가 된다.

특히 direct I/O 경로를 기대했는데도 다음이 보이면 fallback 또는 mixed path를 먼저 의심하는 편이 좋다.

- `write()`는 빨랐는데 나중에 `Dirty`/`Writeback`이 오른다
- 겉보기엔 direct writer인데 page cache debt가 계속 쌓인다
- 일부 환경에서만 `EINVAL`이 나거나, 반대로 일부 환경에서만 조용히 지나간다

즉 alignment mismatch를 명시적으로 실패시키는 편이, 조용한 우회보다 운영 관측을 훨씬 단순하게 만든다.

### 4. direct I/O는 dirty throttling은 건너뛰어도 blk-mq/cgroup 타임라인은 공유한다

정렬이 맞는 direct I/O는 buffered write와 다르게 page cache debt를 먼저 쌓지 않는다.

- aligned direct write/read는 submit 직후 block layer로 내려간다
- 그래서 지연은 dirty writeback보다 blk-mq queueing, device backlog, cgroup I/O contention에서 먼저 보인다
- 반대로 buffered write는 초반엔 빠르게 보이다가 나중에 dirty throttling과 writeback stall로 되돌아온다

이 차이를 구분하지 않으면 "direct I/O인데 왜 느리지?"와 "buffered writeback debt가 왜 여기서 터지지?"를 같은 문제로 오해하게 된다.

운영에서는 이렇게 읽는 편이 좋다.

- `Dirty`가 거의 안 늘고 submit/completion latency가 바로 튄다: direct path 또는 queue contention 가능성이 크다
- `Dirty`가 먼저 늘고 한참 뒤에 stall이 온다: buffered writeback timeline일 가능성이 크다
- direct workload만 느린 줄 알았는데 같은 디바이스의 background flush와 시점이 겹친다: blk-mq/hardware queue는 공유된다는 뜻이다

### 5. alignment가 맞아도 direct I/O가 정답은 아니다

정렬을 모두 맞췄다고 direct I/O가 항상 유리한 것은 아니다.

- 요청이 너무 작다
- readahead/fadvise로도 충분하다
- completion/queue depth 경로가 더 큰 병목이다

즉 alignment는 출발선이지 승리 조건이 아니다.

## 실전 시나리오

### 시나리오 1: 일부 환경에서만 direct I/O가 실패하거나 이상하게 느리다

가능한 원인:

- offset/length/buffer 정렬이 환경별 제약과 안 맞는다
- device/filesystem 차이를 상수 하나로 뭉갰다
- fallback 경로가 숨어 있다

대응 감각:

- alignment 단위를 코드와 운영 문서에서 명시한다
- filesystem 정보와 block device geometry를 함께 기록한다
- failure/fallback semantics를 먼저 결정한다

### 시나리오 2: direct I/O로 바꿨는데 작은 요청에서 오히려 느려진다

가능한 원인:

- alignment를 맞추기 위한 버퍼 관리 비용이 커진다
- 요청 크기 자체가 direct path에 안 맞는다
- cache pollution보다 submit/completion overhead가 더 크다

### 시나리오 3: direct writer와 buffered reader가 섞여 문제를 만든다

가능한 원인:

- alignment는 맞았지만 coherency contract는 없다
- region ownership이 모호하다
- 운영자는 direct I/O가 cache 문제를 "다 해결했다"고 믿는다

### 시나리오 4: direct I/O라고 믿었는데 node `Dirty`가 계속 오른다

가능한 원인:

- 라이브러리나 래퍼가 misalignment 시 buffered fallback을 탔다
- 일부 요청만 정렬이 깨져 mixed path가 생겼다
- direct reader는 맞지만 writer 쪽이 여전히 buffered다

대응 감각:

- "direct enabled" 여부만 보지 말고 실제 syscall 길이/오프셋과 `Dirty` 증가를 같이 본다
- 같은 시점의 blk-mq queue depth와 cgroup `io.stat`도 같이 본다
- direct path와 buffered path의 range ownership을 분리한다

## 코드로 보기

### alignment 단서 수집

```bash
stat -fc 'fs=%T block=%s fundamental=%S' <path>
blockdev --getss /dev/<dev>
blockdev --getpbsz /dev/<dev>
blockdev --getiomin /dev/<dev>
blockdev --getioopt /dev/<dev>
```

해석 감각:

- filesystem block size와 device geometry는 direct-I/O alignment의 힌트다
- 이것만으로 충분하지 않을 수 있으므로, path별 direct-I/O 제약을 알 수 있다면 그 값을 우선한다
- 코드에 상수를 박아 두기보다 runtime/environment별 계약을 노출하는 편이 안전하다

### 운영 체크리스트

```text
1. What is the required alignment unit in this environment?
2. Are buffer address, length, and offset all aligned?
3. What happens on mismatch: fail, retry, or fallback?
4. Is this file/range ever touched by buffered or mmap paths too?
5. If this is supposed to be O_DIRECT, does Dirty stay flat while latency appears in blk-mq/cgroup signals?
```

### mental model

```text
direct I/O
  -> first pass: alignment contract
  -> second pass: ownership/coherency contract
  -> third pass: blk-mq/cgroup queue contention
  -> fourth pass: actual performance value
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| strict fail on mismatch | behavior가 분명하다 | 운영 유연성이 줄 수 있다 | DB-like engines |
| silent fallback | 초기 도입이 쉬워 보인다 | 관측과 디버깅이 흐려진다 | 피하는 편이 좋다 |
| large aligned I/O | direct path 이점을 살리기 쉽다 | 버퍼 관리가 복잡해진다 | sequential/DB workloads |
| buffered path 유지 | contract가 단순하다 | cache pollution 가능성은 남는다 | mixed workloads |

## 꼬리질문

> Q: direct I/O는 왜 alignment 이야기가 먼저 나오나요?
> 핵심: coherency나 성능 이전에, 이 경로가 성립하려면 주소/길이/오프셋 정렬 계약을 먼저 만족해야 하기 때문이다.

> Q: 4KB 정렬이면 어디서나 충분한가요?
> 핵심: 그렇게 단순화하면 위험하다. 환경별 block/filesystem 제약을 같이 확인해야 한다.

> Q: alignment가 맞으면 direct I/O가 항상 빠른가요?
> 핵심: 아니다. alignment는 출발선일 뿐이고, 실제 이득은 workload와 mixed-path 계약까지 봐야 판단할 수 있다.

## 한 줄 정리

direct I/O를 운영에서 안전하게 쓰려면 "캐시를 우회한다"보다 먼저 "정렬 계약과 fallback 계약이 분명한가"를 확인해야 한다.
