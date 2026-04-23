# Dirty Throttling, balance_dirty_pages, Writeback Stalls

> 한 줄 요약: 쓰기 지연이 항상 storage 자체의 느림에서 오는 것은 아니며, dirty page debt가 커지면 `balance_dirty_pages()`가 writer를 직접 늦추고 writeback stall을 애플리케이션 p99로 되돌려 준다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Fsync Tail Latency, Dirty Writeback, Backend Debugging](./fsync-tail-latency-dirty-writeback-debugging.md)
> - [vmstat Counters, Runtime Pressure](./vmstat-counters-runtime-pressure.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)

> retrieval-anchor-keywords: dirty throttling, balance_dirty_pages, writeback stall, dirty page debt, writer throttling, background flusher, dirty_bytes, dirty_ratio, writeback congestion, stalled writes

## 핵심 개념

백엔드가 `write()`에서 느려질 때 많은 팀이 곧바로 "디스크가 느리다"고 생각한다. 하지만 buffered write 경로에서는 실제로 커널이 dirty page debt를 관리하기 위해 writer 자체를 늦추는 경우가 많다. 이때 핵심 메커니즘이 `balance_dirty_pages()`다.

- `dirty page`: 아직 backing storage로 내려가지 않은 page cache 쓰기 데이터다
- `writeback`: dirty page를 실제 저장장치로 밀어내는 경로다
- `balance_dirty_pages()`: dirty memory가 과도할 때 writer를 지연시키는 메커니즘이다
- `dirty page debt`: 지금까지 쌓인 미정산 쓰기 부채라는 운영 감각이다

왜 중요한가:

- 느린 syscall이 `fsync()`가 아니라 `write()`일 수도 있다
- 디스크 utilization보다 dirty memory 정책이 먼저 병목이 될 수 있다
- batch writer가 쌓아 둔 debt가 API 서버 write path를 느리게 만들 수 있다

## 깊이 들어가기

### 1. dirty throttling은 "나중에 쓸 거니까 지금은 빨리"의 반작용이다

buffered I/O는 처음에는 아주 빠르다.

- `write()`는 page cache만 더럽힌다
- storage queue는 나중에 flush한다
- 초반 throughput은 좋아 보인다

하지만 이 debt가 너무 커지면 커널은 더 이상 "나중에"로 미루지 못하고 현재 writer를 늦춘다. 이 순간이 dirty throttling이다.

### 2. `balance_dirty_pages()`는 writer를 직접 멈춰 세운다

중요한 점은 throttling이 flush thread 안에서만 일어나는 것이 아니라는 점이다.

- API thread가 `write()`나 `pwrite()`에서 느려진다
- CPU는 한가해 보여도 task는 sleep 상태로 기다릴 수 있다
- 앱은 storage wait처럼 체감하지만 실제로는 dirty control 경로다

그래서 "write syscall이 느리다"는 현상은 storage device보다 writeback control plane 문제일 수 있다.

### 3. background writeback이 따라가지 못하면 stall이 전염된다

writeback이 debt를 충분히 빨리 청산하지 못하면 다음이 생긴다.

- 새 writer가 더 자주 throttling 된다
- storage queue가 flush burst로 흔들린다
- 같은 노드 다른 서비스도 writeback pressure를 간접적으로 맞는다

즉 dirty throttling은 개별 프로세스 문제가 아니라 node-level writeback ecology 문제다.

### 4. memory와 I/O pressure가 함께 올라가는 이유

dirty throttling은 memory policy와 block I/O 경계에 걸쳐 있다.

- dirty memory가 너무 많다
- flusher가 디스크로 내린다
- storage가 밀리면 debt가 더 오래 남는다
- writer throttling과 io pressure가 함께 커진다

그래서 이 현상은 memory pressure처럼도, I/O pressure처럼도 보인다.

## 실전 시나리오

### 시나리오 1: `fsync()`를 안 하는데도 write-heavy API가 갑자기 느려진다

가능한 원인:

- dirty page가 임계치를 넘었다
- `balance_dirty_pages()`가 writer를 늦춘다
- batch/export/log flush가 같은 노드에서 debt를 쌓았다

진단:

```bash
grep -E 'Dirty|Writeback|WritebackTmp' /proc/meminfo
grep -E 'nr_dirty|nr_writeback|nr_dirtied|nr_written|dirty_(background_)?threshold' /proc/vmstat
cat /proc/pressure/io
vmstat 1
```

판단 포인트:

- `nr_dirtied` 증가 속도가 `nr_written`보다 빠른가
- `Dirty`가 높고 `Writeback`도 같이 높아지는가
- write path latency와 io PSI가 같이 오르는가

### 시나리오 2: 배치가 끝난 뒤에도 한동안 다른 서비스 p99가 흔들린다

가능한 원인:

- batch가 쌓은 dirty debt가 아직 청산 중이다
- flusher와 storage queue가 계속 바쁘다
- foreground writer가 throttling을 같이 맞는다

이 경우는 "배치는 끝났다"가 아니라 "writeback ecology는 아직 안 끝났다"로 읽어야 한다.

### 시나리오 3: dirty ratio를 낮췄더니 spike는 줄었지만 throughput이 빠진다

가능한 원인:

- throttling이 더 자주, 더 빨리 작동한다
- flush burst는 줄었지만 steady-state writer delay가 늘었다
- latency와 throughput의 trade-off가 더 앞당겨졌다

## 코드로 보기

### dirty debt 관찰

```bash
watch -n 1 "grep -E 'Dirty|Writeback' /proc/meminfo; echo; grep -E 'nr_dirty|nr_writeback|nr_dirtied|nr_written' /proc/vmstat"
```

### 해석 감각

```text
write() fast at first
  -> dirty debt accumulates
  -> background flusher works
  -> debt exceeds comfort zone
  -> balance_dirty_pages() slows writer
  -> app sees writeback stall
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 큰 dirty allowance | burst 흡수에 유리하다 | flush burst와 tail spike가 커질 수 있다 | throughput-heavy writes |
| 작은 dirty allowance | debt가 덜 쌓인다 | writer가 더 자주 throttling된다 | latency-sensitive nodes |
| foreground/background 분리 | writeback 전염을 줄인다 | 운영 복잡도가 오른다 | mixed workload nodes |
| explicit batching 재설계 | debt 패턴을 예측하기 쉬워진다 | 앱 설계 비용이 든다 | WAL/log/queue 경로 |

## 꼬리질문

> Q: `write()`가 느리면 무조건 디스크가 느린 건가요?
> 핵심: 아니다. dirty debt가 크면 `balance_dirty_pages()`가 writer를 직접 늦출 수 있다.

> Q: dirty throttling은 메모리 문제인가요 I/O 문제인가요?
> 핵심: 둘 다다. dirty memory 정책과 writeback I/O가 맞물린 경계 문제다.

> Q: dirty ratio를 낮추면 항상 좋아지나요?
> 핵심: 아니다. flush burst는 줄 수 있지만 steady-state writer throttling은 더 자주 생길 수 있다.

## 한 줄 정리

dirty throttling은 "디스크가 느리다"를 넘어서 "커널이 쌓인 write debt를 writer에게 되돌려 주는 순간"으로 읽어야 한다.
