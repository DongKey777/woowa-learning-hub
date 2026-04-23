# I/O Scheduler, blk-mq Basics

> 한 줄 요약: modern Linux storage는 단순한 FIFO가 아니라 blk-mq와 I/O scheduler의 조합으로 동작하며, 장치 큐와 요청 특성이 성능을 좌우한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [blk-mq, cgroup IO, Writeback Timeline Debugging](./blk-mq-cgroup-io-writeback-timeline-debugging.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: blk-mq, mq-deadline, BFQ, none, io scheduler, request queue, hardware queue, queue depth, latency class, I/O completion

## 핵심 개념

Linux block layer는 요청을 디스크로 보내기 전에 여러 큐와 스케줄링 계층을 거친다. modern storage에서는 `blk-mq`가 중심이고, 그 위에서 I/O scheduler가 요청을 정렬하거나 공정성을 조정한다.

- `blk-mq`: 멀티 큐 block layer다
- `hardware queue`: 실제 장치에 붙는 큐다
- `software queue`: 커널 내부에서 요청을 정리하는 큐다
- `mq-deadline`: deadline 기반 정렬 스케줄러다
- `BFQ`: 공정성에 더 중점을 둔 스케줄러다

왜 중요한가:

- 같은 디스크라도 큐잉 정책에 따라 지연이 크게 달라질 수 있다
- 순차 대량 I/O와 짧은 랜덤 I/O는 같은 장치에서도 서로 다르게 취급되어야 한다
- page cache, writeback, reclaim과 결합하면 latency 폭주가 생긴다

이 문서는 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)와 [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)를 저장장치 스케줄링 관점으로 잇는다.

## 깊이 들어가기

### 1. blk-mq는 큐를 단순화하는 것이 아니라 분산한다

장치가 하나의 줄에 모두 서는 대신, 여러 hardware queue로 분산해 병렬성을 높인다.

- 큐 분산은 처리량에 유리하다
- 하지만 잘못 섞이면 작은 요청이 큰 요청에 밀릴 수 있다
- 장치 특성과 workload가 맞아야 한다

### 2. scheduler는 공정성과 순서를 조정한다

대체로 다음 질문에 답한다.

- 어떤 요청을 먼저 보낼까
- 어떤 요청을 잠시 미룰까
- latency-sensitive 요청을 보호할까

이 때문에 scheduler는 throughput만이 아니라 latency와 fairness를 같이 본다.

### 3. queue depth는 숫자 하나로 끝나지 않는다

queue depth가 높으면 디바이스를 잘 채울 수 있지만, 지나치면 기다림이 길어진다.

- 낮으면 장치를 충분히 활용하지 못한다
- 높으면 queueing delay가 쌓인다
- direct reclaim과 writeback이 섞이면 더 복잡해진다

### 4. "디스크가 느리다"는 말은 불충분하다

실제 병목은 다음 중 하나일 수 있다.

- scheduler가 작은 요청을 보호하지 못함
- hardware queue가 포화됨
- writeback burst가 몰림
- reclaim과 겹침

## 실전 시나리오

### 시나리오 1: I/O는 적어 보이는데 p99가 튄다

가능한 원인:

- 작은 요청이 queue depth 뒤에 밀린다
- scheduler가 순서를 잘못 잡는다
- hardware queue가 burst로 포화된다

진단:

```bash
iostat -x 1
cat /proc/diskstats
cat /sys/block/<dev>/queue/scheduler
```

### 시나리오 2: 순차 배치가 OLTP를 망친다

가능한 원인:

- 대량 sequential read/write가 queue를 점유한다
- 공정성보다 throughput에 치우친 설정이다
- page cache writeback이 같이 몰린다

### 시나리오 3: 디바이스 교체 후에 성능이 오히려 흔들린다

가능한 원인:

- 새 장치의 queue depth와 scheduler가 워크로드와 안 맞는다
- blk-mq 분산 전략이 이전 장치와 다르다
- I/O class 구분이 없다

이때는 [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)로 io pressure도 같이 본다.

## 코드로 보기

### 현재 scheduler 확인

```bash
cat /sys/block/<dev>/queue/scheduler
```

### device 큐 감각 보기

```bash
cat /sys/block/<dev>/queue/nr_requests
cat /sys/block/<dev>/queue/read_ahead_kb
```

### disk stats 확인

```bash
cat /proc/diskstats | grep <dev>
```

### scheduler 경로의 단순화

```text
app IO request
  -> block layer
  -> blk-mq software queue
  -> scheduler decision
  -> hardware queue
  -> device
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| mq-deadline | latency를 잘 다룬다 | 복잡한 mixed workload에서 한계 | 일반 SSD |
| BFQ | 공정성이 좋다 | throughput이 손해일 수 있다 | interactivity 중요 |
| none | 오버헤드가 적다 | 장치가 직접 모든 부담을 진다 | 자체 큐잉이 강한 장치 |
| queue depth 증가 | 장치 활용이 좋아진다 | wait time이 늘 수 있다 | throughput 우선 |

## 꼬리질문

> Q: blk-mq가 왜 필요한가요?
> 핵심: 현대 장치는 병렬 큐를 활용해 높은 처리량을 내기 때문이다.

> Q: I/O scheduler는 무엇을 결정하나요?
> 핵심: 요청 순서, 공정성, 지연 보호를 조정한다.

> Q: queue depth를 키우면 항상 좋은가요?
> 핵심: 아니다. 장치 활용과 지연 사이의 균형이 필요하다.

## 한 줄 정리

blk-mq와 I/O scheduler는 storage 요청의 순서와 병렬성을 조정하므로, 디스크 성능은 장치 자체보다 큐잉 정책과 workload 적합성에 크게 좌우된다.
