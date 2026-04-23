# AutoNUMA vs Manual Locality Trade-offs

> 한 줄 요약: autoNUMA는 이미 발생한 remote access를 뒤늦게 고치려는 반응형 메커니즘이고, manual locality는 first-touch, cpuset, worker placement로 애초에 remote access를 덜 만들려는 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)
> - [NUMA First-Touch, Remote Memory, Locality Debugging](./numa-first-touch-remote-memory-locality-debugging.md)
> - [NUMA Production Debugging](./numa-production-debugging.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md)
> - [Cpuset Isolation, Noisy Neighbors](./cpuset-isolation-noisy-neighbors.md)

> retrieval-anchor-keywords: autoNUMA vs manual locality, NUMA tradeoff, first touch vs autonuma, manual placement, cpuset placement, cpuset.cpus.effective, cpuset.mems.effective, noisy neighbor mitigation, hint fault jitter, page migration, remote memory, tail latency locality

## 핵심 개념

NUMA locality를 운영할 때 실제 선택지는 세 축이다.

- `autoNUMA`: 커널이 접근 패턴을 관찰한 뒤 page migration으로 locality를 개선하려는 방식이다
- `manual locality`: first-touch, affinity, cpuset, warm-up 순서를 직접 설계하는 방식이다
- `cpuset placement`: 프로세스가 어느 CPU와 NUMA memory node 집합 안에서만 살 수 있는지 정하는 경계다

핵심은 "자동 vs 수동" 자체보다 **locality를 사후 보정할지, 사전 설계할지**다.

왜 중요한가:

- autoNUMA는 remote memory를 줄일 수 있지만 hint fault와 migration 지터를 동반한다
- manual locality는 p99를 더 안정적으로 만들 수 있지만 배치 유연성이 줄어든다
- noisy neighbor는 per-process affinity가 맞아도 같은 socket, LLC, IRQ 경로를 공유하면 다시 locality를 흔든다

## 깊이 들어가기

### 1. autoNUMA는 locality를 "치유"하지만 관찰 비용을 먼저 낸다

autoNUMA는 현재 접근 패턴을 본 뒤 hot page를 더 가까운 node로 옮기려 한다.

- remote access가 충분히 오래 지속되면 migration 투자비를 회수할 수 있다
- working set이 길게 유지되는 batch나 large heap에서는 이득이 날 수 있다
- 하지만 짧은 request path, lock-heavy hot structure, event loop에서는 hint fault와 cache/TLB 교란이 바로 p99로 보인다

즉 autoNUMA는 "알아서 맞춰 준다"기보다, **runtime motion을 허용하고 그 대가로 적응성**을 얻는 전략이다.

### 2. manual locality는 CPU pinning이 아니라 초기화와 메모리 배치까지 포함한다

manual locality를 제대로 한다는 것은 단순히 `taskset`을 거는 일이 아니다.

- bootstrap 또는 warm-up을 serving worker와 같은 node에서 수행한다
- worker CPU 집합을 좁혀 scheduler migration을 줄인다
- `cpuset.mems` 또는 NUMA policy로 새 메모리가 엉뚱한 node에 생기지 않게 한다
- background thread, GC, flush worker가 hot path CPU를 다시 오염시키지 않게 분리한다

즉 manual locality의 실체는 `CPU placement + memory placement + initialization order`의 결합이다.

### 3. cpuset placement는 locality 전략의 경계 조건이다

cpuset은 locality를 직접 "보장"하지는 않지만, locality가 틀어질 수 있는 범위를 크게 줄인다.

- `cpuset.cpus`를 좁히면 worker가 오갈 수 있는 코어 범위를 제한한다
- `cpuset.mems`를 좁히면 새 할당이 기대하는 NUMA node 집합을 제한한다
- 하지만 CPU만 좁히고 mems를 넓게 두면 worker는 고정돼도 메모리는 여전히 remote일 수 있다
- 반대로 cpuset을 나중에 바꿔도, 이미 first-touch가 끝난 heap과 cache history가 자동으로 "원하는 모양"으로 정리되지는 않는다

실전에서는 다음 정렬이 중요하다.

- `cpuset.cpus`
- `cpuset.mems`
- warm-up thread가 도는 node
- 실제 worker 개수와 burst 시 queue depth

이 네 가지가 안 맞으면 manual locality라고 해도 half-measure가 된다.

### 4. noisy-neighbor mitigation은 "간섭 영역"을 분리하는 일이다

noisy neighbor는 단순히 같은 호스트에 다른 프로세스가 있다는 뜻이 아니다. 같은 locality domain을 공유할 때 문제가 커진다.

- 같은 socket의 LLC를 공유한다
- IRQ와 softirq가 같은 CPU 집합으로 들어온다
- background batch가 같은 NUMA node의 memory bandwidth를 먹는다
- page migration이나 reclaim이 request path와 같은 시간축에서 발생한다

그래서 mitigation의 핵심은 **hot path와 background path의 적응 범위를 분리하는 것**이다.

- hot request path는 node-aligned cpuset으로 좁게 유지한다
- batch나 백그라운드 작업은 더 넓은 CPU 집합에서 돌리거나 다른 node로 밀어낸다
- shared host라면 먼저 request path를 안정화하고, 남는 유연성을 background 쪽에 준다

### 5. 어떤 workload가 autoNUMA에 맞고, 어떤 workload가 manual locality에 맞는가

상대적으로 autoNUMA에 맞는 경우:

- working set이 오래 살아남는다
- throughput 중심이라 약간의 runtime motion을 감수할 수 있다
- memory footprint가 커서 remote access 감소 이득이 migration 비용보다 크다
- 프로세스나 런타임이 first-touch를 직접 통제하기 어렵다

상대적으로 manual locality가 나은 경우:

- 짧고 latency-sensitive한 RPC/API path다
- lock-heavy shared structure나 event loop처럼 작은 흔들림도 tail에 반영된다
- worker 수와 warm-up 순서를 운영자가 제어할 수 있다
- noisy neighbor를 socket/node 단위로 잘라야 한다

## 실전 시나리오

### 시나리오 1: cpuset으로 코어를 분리했는데 remote memory가 그대로다

가능한 해석:

- `cpuset.cpus`만 바뀌고 `cpuset.mems`는 넓게 남아 있다
- 초기화 스레드가 이미 다른 node에 heap을 first-touch 했다
- CPU placement만 고쳤지 memory placement history는 그대로다

확인 포인트:

```bash
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus.effective
cat /sys/fs/cgroup/<cgroup>/cpuset.mems.effective
numastat -p <pid>
cat /proc/<pid>/numa_maps | head -n 40
```

### 시나리오 2: autoNUMA를 켜면 batch throughput은 좋아지는데 API p99는 흔들린다

가능한 해석:

- batch는 locality 재학습 이득을 얻고 있다
- foreground는 hint fault와 migration 지터를 비용으로 내고 있다
- shared host에서 두 workload의 locality 철학이 충돌한다

이때는 "전체 host에 하나의 정답"보다, foreground를 더 좁은 placement로 보호할지 먼저 본다.

### 시나리오 3: dedicated cpuset을 만들었더니 평균은 비슷한데 tail만 안정된다

가능한 해석:

- CPU migration과 remote touch의 확률이 줄었다
- cache/TLB working set이 덜 흔들린다
- manual locality의 이득이 평균보다 p99에서 더 크게 나타난다

### 시나리오 4: cpuset을 너무 좁혔더니 hot core가 생긴다

가능한 해석:

- worker 수에 비해 허용 코어가 부족하다
- IRQ 또는 background kernel work가 같은 코어에 붙는다
- locality는 좋아졌지만 queueing이 더 비싸졌다

즉 "manual locality = 더 좁게"가 아니라, **충분히 넓지만 경계는 명확한 배치**가 목표다.

## 코드로 보기

### 배치 확인 체크리스트

```bash
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus.effective
cat /sys/fs/cgroup/<cgroup>/cpuset.mems
cat /sys/fs/cgroup/<cgroup>/cpuset.mems.effective
taskset -cp <pid>
numastat -p <pid>
cat /proc/<pid>/numa_maps | head -n 40
grep -E 'numa_(hint_faults|pages_migrated)' /proc/vmstat
ps -eo pid,psr,comm | head
```

### placement timeline mental model

```text
bootstrap on node 0
  -> large heap first-touched on node 0

workers later pinned to CPUs on node 1
  -> steady-state remote memory tax appears

autoNUMA reacts
  -> hint faults + page migration
  -> average may recover, tail may shake
```

### 선택 질문

```text
Is p99 stability more important than average throughput?
Can we control warm-up and first-touch directly?
Do cpuset.cpus and cpuset.mems describe the same NUMA intent?
Is the real problem remote memory, or a noisy neighbor sharing the same socket?
Will migration have time to pay back before the request is gone?
```

## 트레이드오프

| 전략 | 장점 | 위험 | 잘 맞는 경우 |
|------|------|------|-------------|
| 넓은 placement + autoNUMA | 적응성이 높다 | noisy neighbor와 migration 지터가 남는다 | shared batch, long-lived memory workload |
| node-aligned cpuset + autoNUMA | 적응 범위를 제한하면서 locality를 개선할 수 있다 | 같은 경계 안에서도 hint fault는 남는다 | mixed workload host |
| node-aligned cpuset + manual first-touch | tail predictability가 높다 | 운영과 warm-up 설계 부담이 크다 | API, RPC, DB hot path |
| CPU pinning만 수행 | 빠르게 시도할 수 있다 | remote memory와 잘못된 first-touch를 못 고친다 | 1차 진단, 임시 완화 |

## 꼬리질문

> Q: `cpuset.cpus`만 맞추면 manual locality가 된 건가요?
> 핵심: 아니다. `cpuset.mems`, first-touch, warm-up, background worker까지 같은 locality 의도로 맞아야 한다.

> Q: autoNUMA를 끄면 noisy neighbor도 해결되나요?
> 핵심: 아니다. 같은 socket, cache, IRQ 경로를 공유하면 autoNUMA 없이도 간섭은 남는다.

> Q: 가장 먼저 확인할 것은 무엇인가요?
> 핵심: 정책 토론 전에 `cpuset.*.effective`, `numa_maps`, `numastat -p`로 실제 배치를 본다.

## 한 줄 정리

autoNUMA는 이미 생긴 remote access를 줄이려는 반응형 전략이고, manual locality는 cpuset과 first-touch로 애초에 remote access와 noisy-neighbor 간섭이 생길 경계를 설계하는 전략이다.
