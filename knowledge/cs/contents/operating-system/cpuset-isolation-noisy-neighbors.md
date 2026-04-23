# Cpuset Isolation, Noisy Neighbors

> 한 줄 요약: cpuset은 noisy neighbor를 시간으로 제한하는 도구가 아니라, CPU와 NUMA node 경계를 잘라 hot path가 섞일 수 있는 공간 자체를 줄이는 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [AutoNUMA vs Manual Locality Trade-offs](./autonuma-vs-manual-locality-tradeoffs.md)
> - [NUMA First-Touch, Remote Memory, Locality Debugging](./numa-first-touch-remote-memory-locality-debugging.md)
> - [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md)
> - [cgroup CPU Throttling, Quota, Runtime Debugging](./cgroup-cpu-throttling-quota-runtime-debugging.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)

> retrieval-anchor-keywords: cpuset, cpuset placement, cpuset.cpus, cpuset.mems, cpuset.cpus.effective, cpuset.mems.effective, noisy neighbor, noisy neighbor mitigation, CPU isolation, NUMA node placement, remote memory drift, hot core, cgroup cpuset

## 핵심 개념

cpuset은 cgroup의 cpuset controller를 통해 태스크가 사용할 수 있는 CPU와 NUMA memory node의 범위를 제한한다. quota가 "얼마나 오래" CPU를 쓰는지 제한한다면, cpuset은 **어디에서 실행되고 어디서 메모리를 받는지**를 제한한다.

- `cpuset.cpus`: 허용 CPU 집합이다
- `cpuset.mems`: 허용 NUMA memory node 집합이다
- `*.effective`: 상위 cgroup 제약까지 반영된 실제 유효 범위다
- `noisy neighbor`: 같은 host의 다른 workload가 cache, IRQ, memory bandwidth, scheduler locality를 흔드는 상황이다

왜 중요한가:

- 같은 quota라도 shared core에 섞이면 cache locality와 tail latency가 쉽게 무너진다
- CPU 집합만 분리하면 compute placement는 좋아져도 remote memory는 남을 수 있다
- cpuset은 AutoNUMA, first-touch, IRQ affinity가 의미 있게 동작할 경계를 먼저 만든다

## 깊이 들어가기

### 1. cpuset은 quota의 대체제가 아니라 placement envelope다

cpuset의 핵심은 "얼마나"보다 "어디서"다.

- quota만 있으면 다른 workload와 같은 코어에서 시간 단위로 번갈아 돌 수 있다
- cpuset만 있으면 실행 위치는 고정되지만 과부하를 막지는 못한다
- low-latency 서비스는 보통 quota, cpuset, affinity를 함께 본다

즉 cpuset은 isolation의 출발점이지, 단독 완성품이 아니다.

### 2. 좋은 cpuset placement는 `cpus`, `mems`, warm-up이 같은 의도를 가져야 한다

cpuset을 걸었는데 효과가 약한 이유는 대부분 배치 의도가 반쯤만 반영됐기 때문이다.

- `cpuset.cpus`만 좁히고 `cpuset.mems`를 넓게 두면 worker는 고정돼도 memory는 remote로 남을 수 있다
- `cpuset.mems`를 좁혀도 bootstrap thread가 엉뚱한 node에서 first-touch 했다면 이미 heap 배치가 왜곡됐을 수 있다
- serving worker 수보다 cpuset이 너무 좁으면 hot core와 run queue가 생긴다

실전 체크리스트:

- serving worker 수와 `cpuset.cpus` 폭이 맞는가
- `cpuset.mems`가 실제로 그 CPU 집합이 붙은 node와 일치하는가
- warm-up, cache fill, 대형 allocation이 같은 node에서 일어났는가

### 3. noisy neighbor는 CPU 경합만이 아니라 locality 경합이다

같은 CPU 집합을 공유하면 단순히 CPU time만 나눠 갖는 것이 아니다.

- LLC와 branch predictor를 공유한다
- IRQ/softirq가 같은 코어로 들어와 worker를 깨운다
- 같은 NUMA node의 memory bandwidth와 page cache pressure를 같이 쓴다
- background reclaim, flush, batch thread가 hot path의 latency budget을 갉아먹는다

그래서 noisy neighbor mitigation은 "CPU 사용률 낮추기"보다 **shared locality domain 줄이기**에 가깝다.

### 4. AutoNUMA와 cpuset은 함께 보면 더 정확하다

cpuset 안에서도 locality 문제는 남을 수 있다.

- `cpuset.mems`가 여러 node를 포함하면 AutoNUMA가 그 안에서 계속 page migration을 시도할 수 있다
- `cpuset.mems`가 좁아도 first-touch가 잘못됐거나 worker/IRQ가 다른 경계에 있으면 기대한 locality가 안 나온다
- cpuset을 적용한 뒤 `numa_hint_faults`, `numa_pages_migrated`가 계속 많다면 "격리가 부족한지"와 "자동 재배치 비용이 큰지"를 같이 봐야 한다

즉 cpuset은 noisy neighbor를 줄이는 틀이고, AutoNUMA 여부는 그 틀 안에서 얼마나 동적으로 재배치할지 정하는 선택이다.

## 실전 시나리오

### 시나리오 1: dedicated cpuset을 준 뒤 API p99가 안정된다

가능한 해석:

- scheduler migration이 줄었다
- cache와 branch predictor가 덜 오염된다
- 같은 node 안에서 worker와 memory locality가 더 잘 맞는다

### 시나리오 2: cpuset을 줬는데도 효과가 거의 없다

가능한 해석:

- `cpuset.cpus`만 바뀌고 `cpuset.mems`는 그대로다
- first-touch가 이미 다른 node에 대형 heap을 만들어 놓았다
- 실제 유효 범위는 `*.effective` 기준으로 다르게 적용되고 있다

진단:

```bash
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus.effective
cat /sys/fs/cgroup/<cgroup>/cpuset.mems
cat /sys/fs/cgroup/<cgroup>/cpuset.mems.effective
numastat -p <pid>
```

### 시나리오 3: noisy neighbor는 줄었는데 특정 코어만 100%가 된다

가능한 해석:

- cpuset 폭이 burst를 감당하기엔 너무 좁다
- IRQ나 kworker가 같은 코어에 붙어 있다
- isolation은 성공했지만 queueing 비용이 더 커졌다

### 시나리오 4: batch와 API를 분리했는데 batch만 느려진다

가능한 해석:

- foreground를 보호하면서 background의 placement 유연성을 일부 희생했다
- host 전체 throughput보다 tail predictability를 우선한 결과다
- batch는 더 넓은 cpuset 또는 다른 node로 재배치해야 할 수 있다

## 코드로 보기

### cpuset과 locality를 같이 확인

```bash
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus.effective
cat /sys/fs/cgroup/<cgroup>/cpuset.mems
cat /sys/fs/cgroup/<cgroup>/cpuset.mems.effective
taskset -cp <pid>
numastat -p <pid>
cat /proc/<pid>/numa_maps | head -n 20
```

### IRQ와 hot core도 같이 본다

```bash
ps -eo pid,psr,comm | head
cat /proc/interrupts | head -n 20
```

### 단순 모델

```text
shared socket and shared cores
  -> noisy neighbor interference
  -> cache and NUMA locality degrade
  -> tail latency increases

node-aligned cpuset
  -> smaller interference domain
  -> better predictability
  -> but less burst absorption
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| dedicated cpuset | noisy neighbor를 강하게 줄인다 | burst 흡수력이 떨어진다 | 핵심 API, low-latency path |
| node-aligned cpuset + mems | CPU와 memory locality를 같이 잡는다 | warm-up과 운영 설계가 필요하다 | JVM, DB, RPC worker |
| 넓은 shared cpuset | 자원 활용과 흡수가 쉽다 | 간섭과 지터가 늘 수 있다 | 일반 배치, 탄력적 워크로드 |
| cpuset만 적용하고 나머지 방치 | 빠르게 시도 가능하다 | first-touch, IRQ, remote memory 문제를 놓친다 | 1차 실험, 원인 분리 |

## 꼬리질문

> Q: cpuset은 quota와 무엇이 다른가요?
> 핵심: quota는 시간 예산을 제한하고, cpuset은 실행과 메모리 배치의 공간 경계를 제한한다.

> Q: noisy neighbor는 왜 cpuset으로 줄이나요?
> 핵심: 같은 코어와 같은 NUMA domain을 공유하는 범위를 줄이면 locality 오염이 줄기 때문이다.

> Q: cpuset만 쓰면 충분한가요?
> 핵심: 아니다. `cpuset.mems`, first-touch, IRQ 배치, worker 수까지 같이 맞춰야 high-value isolation이 된다.

## 한 줄 정리

cpuset은 noisy neighbor를 줄이는 가장 강한 1차 경계지만, 진짜 효과는 `cpuset.cpus`, `cpuset.mems`, first-touch, IRQ 경계가 같은 locality 의도를 공유할 때 나온다.
