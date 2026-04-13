# Kworker Saturation, Runtime Diagnostics

> 한 줄 요약: kworker saturation은 커널의 deferred work가 밀리는 상태라서, 유저 CPU가 아니라 커널 worker backlog와 softirq 후속 처리를 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Workqueues, Kthreads, Debugging](./workqueues-kthreads-debugging.md)
> - [Softirq, Hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: kworker saturation, workqueue backlog, worker threads, kworker, deferred work, /proc/workqueue, kernel backlog, saturation

## 핵심 개념

kworker는 커널 workqueue의 실제 실행자다. 이들이 포화되면 deferred work가 밀려서 I/O completion, reclaim, filesystem maintenance 같은 작업이 늦어진다.

- `kworker`: workqueue를 처리하는 커널 worker다
- `backlog`: 아직 실행되지 못한 work item이다
- `deferred work`: 즉시 처리하지 않고 뒤로 넘긴 커널 작업이다

왜 중요한가:

- user-space CPU가 낮아도 시스템이 느릴 수 있다
- kworker가 밀리면 커널 내부 후속 작업이 전부 늦어진다
- 특정 호스트에서만 latency가 흔들리는 원인이 될 수 있다

이 문서는 [Workqueues, Kthreads, Debugging](./workqueues-kthreads-debugging.md)을 saturation 관점으로 좁힌다.

## 깊이 들어가기

### 1. kworker는 커널의 뒤처리 담당이다

커널은 오래 걸리는 작업을 workqueue에 넘긴다.

- flush
- reclaim 보조
- filesystem deferred work
- device-related follow-up

### 2. saturation은 backlog와 idle worker 부재로 드러난다

- work item이 쌓인다
- worker가 따라잡지 못한다
- 유저 경로의 completion이 밀린다

### 3. CPU affinity와도 연결된다

worker가 특정 코어에 몰리면 hot core가 생길 수 있다.

### 4. kworker 포화는 증상이 더 늦게 보일 수 있다

유저 스레드는 멀쩡해 보여도 커널 후속 작업이 밀리면 전체 tail latency가 나빠진다.

## 실전 시나리오

### 시나리오 1: I/O 후속 처리가 늦는다

가능한 원인:

- kworker backlog가 쌓였다
- deferred flush가 밀린다
- workqueue가 포화됐다

진단:

```bash
ps -eLo pid,tid,psr,comm | grep kworker | head
cat /proc/workqueue/* 2>/dev/null | head
```

### 시나리오 2: 배치/리클레임 이후 시스템이 굼뜨다

가능한 원인:

- reclaim 관련 work가 폭주
- kworker가 CPU를 확보하지 못함
- softirq 이후 작업이 밀림

### 시나리오 3: 특정 코어만 busy하다

가능한 원인:

- worker affinity가 나쁘다
- IRQ와 worker가 같은 코어에 몰린다
- cache locality는 좋아도 load balance가 깨진다

## 코드로 보기

### kworker 관찰

```bash
ps -eLo pid,tid,psr,comm | grep kworker | head
```

### workqueue 감각

```text
kernel event
  -> queued as deferred work
  -> kworker executes later
  -> if backlog grows, completion latency increases
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| workqueue 사용 | 즉시 경로를 짧게 한다 | backlog가 생길 수 있다 | 일반 kernel deferred work |
| worker 분산 | 포화를 줄일 수 있다 | locality가 깨질 수 있다 | 고트래픽 host |
| affinity 고정 | 예측성이 좋아진다 | hot core 위험 | latency tuning |

## 꼬리질문

> Q: kworker saturation은 왜 문제인가요?
> 핵심: 커널이 뒤에서 해야 할 일이 밀려 전체 latency가 늘기 때문이다.

> Q: user-space CPU가 낮은데도 왜 느릴 수 있나요?
> 핵심: 커널 deferred work가 병목일 수 있다.

> Q: 어디를 먼저 보나요?
> 핵심: `kworker` 개수와 backlog, 그리고 IRQ/softirq 분포를 본다.

## 한 줄 정리

kworker saturation은 커널 후속 작업이 밀려 생기는 숨은 병목이므로, 유저 CPU보다 workqueue backlog와 worker 배치를 봐야 한다.
