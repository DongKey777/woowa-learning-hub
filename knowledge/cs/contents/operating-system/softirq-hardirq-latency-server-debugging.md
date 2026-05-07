---
schema_version: 3
title: Softirq Hardirq Latency Server Debugging
concept_id: operating-system/softirq-hardirq-latency-server-debugging
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- softirq-hardirq-latency
- server
- interrupt-latency-server
- ksoftirqd-network-latency
aliases:
- softirq hardirq latency
- interrupt latency server debugging
- ksoftirqd network latency
- IRQ CPU time
- network storage interrupt bottleneck
- irq affinity latency
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/operating-system/epoll-kqueue-io-uring.md
- contents/operating-system/interrupt-basics.md
- contents/operating-system/cpu-affinity-irq-affinity-core-locality.md
- contents/operating-system/kworker-saturation-runtime-diagnostics.md
- contents/operating-system/ebpf-perf-strace-production-tracing.md
- contents/operating-system/socket-buffer-autotuning-backpressure.md
symptoms:
- network나 storage가 느려 보이지만 실제 병목은 hardirq/softirq CPU time에 숨어 있다.
- ksoftirqd가 밀리며 packet processing latency가 application p99로 보인다.
- IRQ affinity가 특정 core에 몰려 hot core와 latency spike를 만든다.
expected_queries:
- hardirq와 softirq가 CPU를 언제 얼마나 쓰는지가 server latency에 왜 중요해?
- ksoftirqd saturation과 network packet processing latency를 어떻게 디버깅해?
- IRQ affinity와 softirq backlog가 p99를 키울 수 있어?
- storage/network latency가 실제로는 interrupt processing bottleneck인지 확인하려면?
contextual_chunk_prefix: |
  이 문서는 network와 storage가 느려 보일 때 실제 bottleneck이 hardirq와 softirq가 어느 CPU에서
  얼마나 오래 실행되는가에 숨어 있을 수 있다는 server debugging playbook이다.
---
# Softirq, Hardirq, Latency Server Debugging

> 한 줄 요약: 네트워크와 저장장치가 느려 보일 때, 실제 병목은 hardirq와 softirq가 CPU를 언제, 얼마나 오래 쓰느냐에 숨어 있는 경우가 많다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: softirq, hardirq, ksoftirqd, /proc/interrupts, /proc/softirqs, irqbalance, NAPI, NET_RX, NET_TX, interrupt latency

## 핵심 개념

인터럽트는 장치가 CPU의 현재 일을 잠깐 끊고 긴급 신호를 전달하는 메커니즘이다. Linux에서는 그 처리를 크게 hardirq와 softirq로 나누어 생각한다.

- `hardirq`: 즉시 처리해야 하는 매우 짧은 인터럽트 핸들러다
- `softirq`: 조금 더 여유 있게 처리할 수 있는 후속 작업이다
- `ksoftirqd`: softirq를 커널 스레드 컨텍스트에서 처리하는 경로다

왜 중요한가:

- NIC interrupt가 몰리면 패킷 처리가 밀린다
- storage interrupt가 몰리면 I/O completion이 늦어진다
- softirq가 CPU를 오래 쓰면 애플리케이션 스레드가 굶는다

이 문서는 [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)에서 본 이벤트 루프를, 커널의 interrupt path 관점에서 다시 본다.

## 깊이 들어가기

### 1. hardirq는 짧아야 한다

hardirq는 가능한 빨리 끝나야 한다.

- 너무 오래 붙잡으면 다른 인터럽트를 지연시킨다
- 장치 응답과 실제 처리 분리를 해친다
- 긴 작업은 softirq나 worker로 넘겨야 한다

즉 hardirq는 "즉시성"이 장점이지, 많은 일을 하는 곳이 아니다.

### 2. softirq는 네트워크와 블록 I/O의 핵심 경로다

네트워크 수신은 보통 NAPI와 softirq를 통해 처리된다.

- 패킷이 들어오면 인터럽트가 발생한다
- 커널은 일부만 즉시 처리하고 나머지는 softirq로 넘긴다
- softirq가 밀리면 `ksoftirqd`가 바빠진다

이 구조 때문에 CPU가 바빠 보이지 않아도 실제 packet processing이 막힐 수 있다.

### 3. interrupt latency는 애플리케이션 latency로 이어진다

인터럽트가 늦게 처리되면 다음이 발생한다.

- 패킷 도착 후 소켓 큐 반영이 늦는다
- ACK/응답 전송이 늦는다
- disk completion이 늦어 syscall이 오래 block된다

즉 interrupt latency는 커널 내부 문제가 아니라, 앱 p99와 직접 연결된다.

### 4. `irqbalance`는 만능이 아니다

IRQ를 여러 CPU에 분산하면 도움이 될 수 있지만, 무작정 분산이 답은 아니다.

- affinity가 흩어지면 cache locality가 깨진다
- 너무 많이 분산하면 context switch와 cache miss가 늘 수 있다
- 한 코어에 집중되면 반대로 hot spot이 생긴다

운영에서는 장치 특성, CPU topology, NUMA를 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 네트워크 트래픽은 많은데 유저 스페이스는 한가해 보인다

가능한 원인:

- NET_RX softirq가 밀린다
- `ksoftirqd`가 바빠서 앱 스레드가 CPU를 못 받는다
- IRQ affinity가 한 코어에 쏠렸다

진단:

```bash
cat /proc/interrupts
cat /proc/softirqs
mpstat -I ALL 1
top -H
```

판단 포인트:

- 특정 CPU에 IRQ가 몰리는가
- `NET_RX`, `NET_TX` softirq가 상승하는가
- `ksoftirqd/*`가 상위에 보이는가

### 시나리오 2: 디스크 I/O 지연이 갑자기 늘었다

가능한 원인:

- block layer completion이 밀린다
- hardirq 처리 이후 softirq 후속 작업이 늦는다
- 다른 CPU에서 interrupt storm이 발생한다

진단:

```bash
cat /proc/interrupts
iostat -x 1
pidstat -d 1
```

### 시나리오 3: accept나 read는 빠른데 간헐적으로 응답이 늦다

가능한 원인:

- softirq가 몰리면서 소켓 wakeup이 늦는다
- 네트워크 receive path가 포화된다
- backlog와 interrupt latency가 서로 증폭된다

이 경우는 [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)과 함께 보아야 한다. wakeup이 느린 이유가 user space가 아니라 kernel interrupt path일 수 있다.

## 코드로 보기

### IRQ와 softirq를 먼저 보는 기본 점검

```bash
watch -n 1 'cat /proc/interrupts; echo; cat /proc/softirqs'
```

### CPU별 인터럽트 분포 확인

```bash
mpstat -I ALL 1
```

### 특정 장치와 IRQ affinity 확인

```bash
for i in /proc/irq/*/smp_affinity_list; do echo "$i"; cat "$i"; done | head
```

### bpftrace로 interrupt 핸들러 힌트 보기

```bash
bpftrace -e 'tracepoint:irq:irq_handler_entry { @[comm] = count(); }'
```

### perf로 softirq hot path 확인

```bash
perf top -g -a
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| IRQ 분산 | hot spot을 줄인다 | locality가 깨질 수 있다 | NIC/스토리지 집중 부하 |
| IRQ 고정 | 캐시 locality가 좋다 | 한 코어가 포화될 수 있다 | 저지연 워크로드 |
| `irqbalance` 기본 사용 | 운영이 쉽다 | 세밀한 제어가 약하다 | 일반 서버 |
| RPS/RFS 튜닝 | 수신 분산에 유리하다 | 복잡도가 증가한다 | 고트래픽 네트워크 서버 |

인터럽트 튜닝은 "더 분산"과 "더 고정" 사이의 균형 문제다. 워크로드와 하드웨어가 답을 바꾼다.

## 꼬리질문

> Q: hardirq와 softirq의 차이는 무엇인가요?
> 핵심: hardirq는 즉시 짧게 처리하고, softirq는 후속 작업을 담당한다.

> Q: `ksoftirqd`가 보이면 항상 문제인가요?
> 핵심: 아니다. 다만 softirq가 충분히 처리되지 못해 커널 스레드로 밀렸다는 신호다.

> Q: 왜 interrupt latency가 p99에 영향을 주나요?
> 핵심: 패킷 수신과 completion이 늦어지면 앱이 기다리는 시간이 길어지기 때문이다.

> Q: IRQ affinity는 무조건 분산이 좋은가요?
> 핵심: 아니다. 캐시 locality와 포화 상태를 같이 봐야 한다.

## 한 줄 정리

softirq와 hardirq는 커널의 "숨은 실행 시간"이므로, 네트워크와 저장장치 latency를 볼 때는 /proc/interrupts와 softirq 분포를 반드시 같이 봐야 한다.
