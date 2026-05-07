---
schema_version: 3
title: blk-mq cgroup IO Writeback Timeline Debugging
concept_id: operating-system/blk-mq-cgroup-io-writeback-timeline-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- blk-mq-cgroup
- io-writeback-timeline
- page-cache-writeback
- dirty-flush-storage
aliases:
- blk-mq cgroup IO writeback timeline
- page cache writeback debugging
- dirty flush storage latency
- cgroup IO controller debugging
- disk busy timeline
- submit to flush storage path
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/io-scheduler-blk-mq-basics.md
- contents/operating-system/cgroup-io-controller-basics.md
- contents/operating-system/direct-io-alignment-checklist.md
- contents/operating-system/buffered-vs-direct-io-mixing-coherency-pitfalls.md
- contents/operating-system/dirty-throttling-balance-dirty-pages-writeback-stalls.md
- contents/operating-system/page-cache-dirty-writeback-fsync.md
- contents/operating-system/fsync-tail-latency-dirty-writeback-debugging.md
symptoms:
- 디스크가 바쁘다는 지표만 보이고 submit, queue, writeback 중 병목 위치가 안 갈린다.
- cgroup IO limit과 page cache dirty writeback이 서로 다른 시점에 latency를 만든다.
- fsync tail latency가 blk-mq queue와 dirty flush timeline 중 어디서 생겼는지 모른다.
expected_queries:
- blk-mq cgroup IO writeback을 submit부터 dirty flush까지 timeline으로 디버깅해줘
- 디스크가 바쁠 때 block queue, cgroup IO, page cache writeback 중 어디를 봐야 해?
- dirty throttling과 fsync tail latency가 storage path에서 어떻게 연결돼?
- cgroup IO controller가 page cache writeback latency에 어떤 영향을 줘?
contextual_chunk_prefix: |
  이 문서는 storage 장애를 디스크가 바쁘다는 한 지표로 보지 않고 blk-mq submit/dispatch,
  cgroup I/O control, page cache dirty writeback, fsync tail latency가 서로 다른 시점에
  영향을 주는 timeline으로 디버깅한다.
---
# blk-mq, cgroup IO, Writeback Timeline Debugging

> 한 줄 요약: storage 장애는 블록 계층, cgroup IO 제어, page cache writeback이 서로 다른 시점에 영향을 주기 때문에, "디스크가 바쁘다"보다 submit부터 dirty flush까지의 타임라인으로 읽는 편이 정확하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [I/O Scheduler, blk-mq Basics](./io-scheduler-blk-mq-basics.md)
> - [Cgroup IO Controller, Basics](./cgroup-io-controller-basics.md)
> - [Direct I/O Alignment Checklist](./direct-io-alignment-checklist.md)
> - [Buffered vs Direct I/O Mixing, Coherency Pitfalls](./buffered-vs-direct-io-mixing-coherency-pitfalls.md)
> - [Dirty Throttling, balance_dirty_pages, Writeback Stalls](./dirty-throttling-balance-dirty-pages-writeback-stalls.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Fsync Tail Latency, Dirty Writeback, Backend Debugging](./fsync-tail-latency-dirty-writeback-debugging.md)

> retrieval-anchor-keywords: blk-mq timeline, cgroup io timeline, writeback timeline, io.stat, io.pressure, dirty flush path, hardware queue backlog, storage timeline debugging, writeback ecology, direct vs buffered timeline, O_DIRECT fallback, balance_dirty_pages timeline, io.max, io.weight, dirty page debt, submit to completion latency

## 핵심 개념

운영에서 storage tail latency를 볼 때 `iostat` 한 장면만 보면 자주 틀린다. 이유는 앱 쓰기, dirty page 누적, flusher writeback, blk-mq queueing, cgroup I/O controller, hardware queue 포화가 모두 서로 다른 시점에 드러나기 때문이다. 그래서 "누가 언제 debt를 쌓고, 누가 언제 장치를 점유하는가"의 timeline으로 읽어야 한다.

- 앱 submit 시점: userspace가 write/read를 시작하는 순간
- dirty accumulation 시점: page cache에 debt가 쌓이는 단계
- writeback 시점: flusher가 storage로 내리는 단계
- blk-mq queueing 시점: block layer/hardware queue에 실제 요청이 밀리는 단계
- cgroup IO accounting 시점: 어느 workload가 queue와 stall을 소비했는지 드러나는 단계
- completion 시점: syscall 또는 async completion이 실제로 지연을 체감하는 순간

왜 중요한가:

- foreground API와 background batch의 blame 시점이 다를 수 있다
- 현재 느린 프로세스가 debt를 만든 주체가 아닐 수도 있다
- io.max/io.weight를 조정해도 이미 쌓인 dirty debt는 늦게 터질 수 있다
- direct I/O와 buffered I/O는 같은 장치를 두고도 latency가 드러나는 순간이 다르다

## 깊이 들어가기

### 1. 앱 submit과 storage busy는 같은 순간이 아니다

buffered write 경로에서는 특히 그렇다.

- 앱은 `write()`를 호출한다
- dirty page만 늘고 당장은 storage가 한가할 수 있다
- 나중에 flusher가 장치를 바쁘게 만든다

그래서 "지금 디스크가 바쁘니 지금 API가 원인"이라고 단정하면 자주 틀린다.

direct I/O는 반대로 debt를 먼저 숨기지 않는다.

- aligned direct read/write는 submit 직후 block layer로 내려간다
- 앱 latency와 device queueing이 더 가깝게 붙어 보인다
- 그래서 direct workload는 dirty debt보다 blk-mq/cgroup 경쟁이 먼저 보이는 경우가 많다

즉 같은 "쓰기 지연"도 buffered path와 direct path의 타임라인이 다르다.

### 2. cgroup IO controller는 queueing blame을 분리해 주지만, 늦게 보이는 debt까지 지우지는 못한다

`io.stat`, `io.pressure`, `io.max`, `io.weight`는 매우 유용하다. 하지만 writeback ecology를 해석할 때는 한계도 있다.

- 어떤 cgroup이 현재 I/O를 많이 쓰는지는 보인다
- 하지만 dirty debt를 누가 earlier phase에 쌓았는지는 더 넓은 타임라인이 필요하다
- foreground cgroup이 지금 stall을 맞지만 root cause는 earlier batch일 수 있다

즉 controller는 accounting/isolating 도구지, causality를 자동으로 설명해 주는 도구는 아니다.

실전에서는 root cgroup만 보면 자주 놓친다.

- affected workload의 `io.stat`/`io.pressure`를 per-cgroup으로 본다
- `io.weight`는 future competition을 바꾸지, 이미 디바이스에 올라간 backlog를 지우지 않는다
- `io.max`는 noisy neighbor를 제어하지만, node-global dirty debt가 청산되는 동안 체감 latency는 남을 수 있다

### 3. blk-mq queueing은 최종 병목 표면이다

storage path가 실제로 보이는 지점은 blk-mq/hardware queue다.

- 작은 latency-sensitive write가 긴 background flush 뒤에 밀린다
- queue depth가 커지며 `await`, `aqu-sz`가 오른다
- userspace는 `fsync()`나 writeback stall로 체감한다

그래서 최종 표면은 blk-mq지만, 시작점은 dirty debt 또는 cgroup policy일 수 있다.

직접 I/O도 여기서는 예외가 아니다.

- page cache를 안 거쳐도 hardware queue는 공유된다
- background writeback burst가 있으면 aligned direct I/O도 뒤에서 기다린다
- 따라서 `Dirty`가 flat하다고 해서 storage contention이 없는 것은 아니다

즉 "direct니까 writeback 문제와 무관하다"가 아니라 "dirty debt는 남이 만들고, queue delay는 내가 맞을 수 있다"가 더 정확하다.

### 4. direct I/O alignment/fallback이 타임라인 해석을 바꾼다

운영에서 가장 위험한 상태는 "우리는 direct I/O를 쓰고 있다"고 믿는데 실제로는 일부 요청이 그렇지 않은 경우다.

- misaligned offset/length/buffer 때문에 direct path가 실패한다
- 라이브러리/엔진이 일부 요청만 buffered fallback 한다
- 그러면 같은 workload 안에서도 어떤 요청은 submit latency로, 어떤 요청은 dirty/writeback latency로 드러난다

이 상태가 되면 timeline이 두 갈래로 갈라진다.

- direct path 요청: blk-mq/cgroup queueing이 먼저 보인다
- buffered fallback 요청: dirty debt와 writeback stall이 늦게 보인다

그래서 `O_DIRECT enabled` 같은 설정값만 보지 말고, 실제 alignment 계약과 node `Dirty` 증감을 같이 확인해야 한다.

### 5. timeline이 맞아야 blame이 맞는다

운영 triage는 보통 이렇게 맞추는 편이 좋다.

- 앱 latency spike 시점
- `Dirty`/`Writeback` 증가 시점
- `io.stat`/`io.pressure` 상승 시점
- `iostat -x` queue depth 상승 시점

이 타임라인이 어긋나면 "누가 원인인가" 해석도 어긋난다.

다만 I/O mode에 따라 먼저 보는 신호는 달라진다.

| 단계 | buffered write path | aligned direct I/O path | 먼저 볼 신호 |
|------|----------------------|-------------------------|--------------|
| submit 직후 | syscall은 짧을 수 있다 | syscall latency가 바로 늘 수 있다 | `strace`, 앱 p99 |
| memory debt | `Dirty`, `nr_dirtied`가 오른다 | 대체로 flat해야 한다 | `/proc/meminfo`, `/proc/vmstat` |
| throttling | `balance_dirty_pages()`가 writer를 늦춘다 | dirty throttling 영향은 작다 | `Dirty`, `io.pressure` |
| queueing | 나중에 flusher가 blk-mq queue를 채운다 | foreground request가 곧바로 queue로 간다 | `iostat -x`, scheduler, `nr_requests` |
| cgroup accounting | writeback consumer가 보일 수 있다 | current direct issuer가 더 직접 보인다 | per-cgroup `io.stat`, `io.pressure` |

이 표를 기억해 두면 "왜 direct workload latency와 Dirty spike가 같이 안 보이지?" 같은 혼란을 줄일 수 있다.

## 실전 시나리오

### 시나리오 1: 배치는 끝났는데 API fsync p99가 그 뒤에 튄다

가능한 원인:

- batch가 dirty debt를 남겼다
- flusher가 나중에 storage queue를 점유한다
- foreground API는 늦게 도착한 victim일 뿐이다

진단:

```bash
grep -E 'Dirty|Writeback' /proc/meminfo
cat /sys/fs/cgroup/<cg>/io.stat
cat /sys/fs/cgroup/<cg>/io.pressure
iostat -x 1
```

### 시나리오 2: io.weight를 줬는데도 체감 latency는 여전히 나쁘다

가능한 원인:

- policy는 바뀌었지만 earlier dirty debt가 아직 남아 있다
- foreground stall은 writeback ecology 전체의 결과다
- blk-mq queue 자체가 이미 길다
- 이미 queue에 올라간 background writeback은 즉시 사라지지 않는다

### 시나리오 3: 디스크는 바쁜데 어느 워크로드를 blame해야 할지 모르겠다

가능한 원인:

- 현재 queue consumer와 earlier dirty producer가 다르다
- buffered write path와 direct I/O path가 섞여 있다
- cgroup boundary와 node-global writeback이 겹친다

### 시나리오 4: direct I/O로 바꿨는데도 node `Dirty`가 오르고 latency도 흔들린다

가능한 원인:

- 일부 요청이 misalignment로 buffered fallback 했다
- direct reader와 buffered writer가 같은 파일/장치를 공유한다
- direct path 자체는 맞지만 background writeback이 blk-mq queue를 점유한다

판단 포인트:

- 앱 syscall latency spike와 `Dirty` 증가가 같은 시점인가
- `Dirty`가 오르는 동안 affected cgroup의 `io.stat`는 누구를 가리키는가
- `iostat -x`의 `await`, `aqu-sz` 상승이 direct path와 writeback path를 모두 압박하는가

## 코드로 보기

### 운영 타임라인 체크

```bash
watch -n 1 'grep -E "Dirty|Writeback" /proc/meminfo; echo; cat /sys/fs/cgroup/<cg>/io.stat; echo; cat /sys/fs/cgroup/<cg>/io.pressure'
```

```bash
iostat -x 1
```

### direct-vs-buffered 분류부터 한다

```bash
strace -ff -ttT -p <pid> -e trace=openat,read,pread64,write,pwrite64,fsync,fdatasync
```

```bash
stat -fc 'fs=%T block=%s fundamental=%S' <path>
blockdev --getss /dev/<dev>
blockdev --getiomin /dev/<dev>
```

해석 감각:

- direct path를 기대한다면 syscall 길이/오프셋과 alignment 단서를 먼저 본다
- direct path인데 `Dirty`가 같이 오른다면 fallback 또는 mixed path를 의심한다
- buffered path라면 dirty debt와 writeback을 먼저 timeline 위에 올린다

### mental model

```text
buffered write
  -> dirty debt accumulates
  -> balance_dirty_pages may slow writer
  -> writeback starts later
  -> cgroup IO accounting shows current pressure
  -> blk-mq/hardware queue becomes visibly busy
  -> foreground latency spikes may arrive last

aligned direct I/O
  -> syscall submits to block layer now
  -> cgroup IO accounting reflects current issuer
  -> blk-mq/hardware queue backlog is felt earlier
  -> latency shows up near submit/completion time
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| blk-mq만 보기 | 최종 병목 표면을 본다 | earlier dirty causality는 놓칠 수 있다 | device saturation 확인 |
| cgroup IO만 보기 | workload blame에 유리하다 | debt의 시간차는 놓칠 수 있다 | multi-tenant hosts |
| dirty/writeback 같이 보기 | causality 해석이 좋아진다 | 메모리와 I/O를 같이 읽어야 한다 | buffered write-heavy nodes |
| direct-vs-buffered 분리해서 보기 | 타임라인 해석이 선명해진다 | alignment/fallback 확인이 필요하다 | mixed storage paths |
| 통합 timeline 보기 | 가장 정확하다 | 운영 관측 체계가 필요하다 | complex mixed workloads |

## 꼬리질문

> Q: 지금 디스크가 바쁜 cgroup이 항상 root cause인가요?
> 핵심: 아니다. 현재 stall consumer와 earlier dirty producer가 다를 수 있다.

> Q: io.weight를 줬는데도 latency가 나쁜 이유는?
> 핵심: policy는 바뀌어도 이미 쌓인 dirty debt와 blk-mq backlog는 늦게 해소될 수 있기 때문이다.

> Q: direct I/O인데 왜 writeback timeline도 같이 봐야 하나요?
> 핵심: direct path 자체는 dirty debt를 덜 만들지만, 같은 장치의 background writeback이 blk-mq queue를 점유하면 direct request도 같이 느려질 수 있기 때문이다.

> Q: 왜 blk-mq, cgroup IO, writeback을 함께 봐야 하나요?
> 핵심: storage tail latency는 이 세 층이 다른 시점에 표면화된 합성 결과이기 때문이다.

## 한 줄 정리

storage 장애를 제대로 읽으려면 "이 요청이 direct인가 buffered인가", "지금 누가 장치를 쓰나", "누가 earlier phase에 dirty debt를 쌓았나"를 같은 timeline 위에 올려 봐야 한다.
