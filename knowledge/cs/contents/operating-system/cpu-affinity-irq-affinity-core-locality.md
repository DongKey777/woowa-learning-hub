# CPU Affinity, IRQ Affinity, Core Locality

> 한 줄 요약: affinity는 특정 코어에 작업과 인터럽트를 붙여 locality를 살리는 도구지만, 잘못 고정하면 한 코어만 뜨거워지고 나머지는 놀게 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Softirq, Hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md)
> - [AutoNUMA vs Manual Locality Trade-offs](./autonuma-vs-manual-locality-tradeoffs.md)
> - [Scheduler Classes, nice, RT Trade-offs](./scheduler-classes-nice-rt-tradeoffs.md)
> - [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)

> retrieval-anchor-keywords: cpu affinity, irq affinity, taskset, sched_setaffinity, smp_affinity, core locality, cache locality, RSS, NUMA node, hot core

## 핵심 개념

CPU affinity는 특정 프로세스나 스레드를 특정 CPU에 가깝게 묶는 설정이다. IRQ affinity는 장치 인터럽트를 특정 CPU에 배정하는 설정이다. 둘 다 locality를 높이기 위한 수단이지만, 과하면 균형이 깨진다.

- `sched_setaffinity`: 태스크의 CPU 집합을 제한한다
- `smp_affinity`: IRQ가 어느 CPU에서 처리될지 정한다
- `core locality`: 자주 쓰는 캐시와 데이터가 같은 코어 근처에 남는 성질이다
- `hot core`: 한 코어에 일과 인터럽트가 몰린 상태다

왜 중요한가:

- locality는 좋아질 수 있지만 부하 분산은 나빠질 수 있다
- IRQ와 worker가 같은 코어에 붙으면 경합이 커질 수 있다
- NUMA와 함께 보면 더 복잡해진다

이 문서는 [Softirq, Hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)와 [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)를 CPU 배치 관점으로 연결한다.

## 깊이 들어가기

### 1. affinity는 캐시 locality를 돕는다

작업을 같은 코어 근처에서 돌리면 캐시가 재사용될 가능성이 높다.

- hot data가 같은 코어에 남는다
- TLB와 cache miss를 줄일 수 있다
- 하지만 분산이 부족하면 병목이 생긴다

### 2. IRQ affinity는 네트워크와 저장장치 latency에 직접 영향이 있다

인터럽트를 어느 CPU가 처리하느냐는 실제 packet completion과 wakeup latency에 연결된다.

- 너무 흩어지면 cache locality가 깨진다
- 너무 모이면 한 코어가 포화된다
- worker affinity와 맞춰야 한다

### 3. affinity는 고정이 아니라 설계다

- CPU pinning
- IRQ pinning
- NUMA node alignment
- worker placement

이걸 같이 설계해야 한다. 한 가지만 고정하면 다른 축이 흔들릴 수 있다.

### 4. affinity는 throughput과 tail latency 사이 선택이다

일반적으로 locality가 좋아지면 평균은 좋아질 수 있지만, hot core가 생기면 꼬리 지연이 나빠질 수 있다.

## 실전 시나리오

### 시나리오 1: 특정 CPU만 100%에 가깝다

가능한 원인:

- task affinity가 지나치게 좁다
- IRQ가 한 코어에 몰린다
- worker와 interrupt가 같은 코어에서 싸운다

진단:

```bash
top -H
taskset -cp <pid>
cat /proc/interrupts
```

### 시나리오 2: affinity를 주고 나서 성능이 좋아졌다가 다시 흔들린다

가능한 원인:

- hot core가 생겼다
- batch/interrupt와 API가 섞인다
- NUMA locality는 좋아졌지만 load balance가 깨졌다

### 시나리오 3: 네트워크 latency만 이상하게 튄다

가능한 원인:

- IRQ affinity가 network worker와 안 맞는다
- softirq가 특정 CPU를 잡아먹는다
- cache locality보다 load imbalance가 더 크다

이 경우는 [Softirq, Hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)도 함께 본다.

## 코드로 보기

### 프로세스 affinity 보기

```bash
taskset -cp <pid>
```

### IRQ affinity 보기

```bash
for i in /proc/irq/*/smp_affinity_list; do echo "$i"; cat "$i"; done | head
```

### affinity 변경 예시

```bash
taskset -cp 0,1 <pid>
```

### 단순 모델

```text
affinity improves locality
  -> cache hits rise
  -> but load balance can collapse
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| pinning 강화 | locality가 좋아진다 | hot core가 생길 수 있다 | low-latency path |
| pinning 완화 | load balance가 좋아진다 | cache miss가 늘 수 있다 | 일반 서버 |
| IRQ 분산 | 특정 코어 포화를 줄인다 | locality가 깨질 수 있다 | NIC/스토리지 집약 |
| worker/IRQ alignment | completion latency를 줄인다 | 운영 설계가 복잡하다 | latency-sensitive service |

## 꼬리질문

> Q: CPU affinity와 IRQ affinity는 왜 같이 보나요?
> 핵심: 인터럽트와 워커가 같은 데이터와 캐시를 공유하기 때문이다.

> Q: affinity를 주면 무조건 빨라지나요?
> 핵심: 아니다. locality는 좋아져도 load balance가 깨질 수 있다.

> Q: hot core가 왜 문제가 되나요?
> 핵심: 한 코어만 포화되고 tail latency가 튀기 때문이다.

## 한 줄 정리

CPU affinity와 IRQ affinity는 locality를 살리지만, 균형을 잃으면 한 코어 포화와 latency 악화를 만들 수 있다.
