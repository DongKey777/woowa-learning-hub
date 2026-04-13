# Cpuset Isolation, Noisy Neighbors

> 한 줄 요약: cpuset은 CPU를 "얼마나" 쓸지보다 "어느 코어 집합에서" 쓸지를 정해서, noisy neighbor를 공간적으로 분리하는 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [cgroup CPU Throttling, Quota, Runtime Debugging](./cgroup-cpu-throttling-quota-runtime-debugging.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [Scheduler Classes, nice, RT Trade-offs](./scheduler-classes-nice-rt-tradeoffs.md)
> - [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)

> retrieval-anchor-keywords: cpuset, cpuset.cpus, cpuset.mems, noisy neighbor, CPU isolation, core pinning, NUMA node placement, cgroup cpuset

## 핵심 개념

cpuset은 cgroup의 한 종류로, 프로세스가 실행할 수 있는 CPU와 메모리 노드의 범위를 제한한다. 이는 단순한 quota와 다르게, **자원을 얼마나 쓰는지**보다 **어디에서 실행되는지**를 제어한다.

- `cpuset.cpus`: 프로세스가 사용할 CPU 집합이다
- `cpuset.mems`: 프로세스가 사용할 NUMA 메모리 노드 집합이다
- `noisy neighbor`: 같은 호스트의 다른 워크로드가 locality나 캐시를 흔드는 상황이다

왜 중요한가:

- 같은 quota라도 다른 코어와 섞이면 cache locality가 무너질 수 있다
- noisy neighbor를 CPU 집합 단위로 분리하면 tail latency가 좋아질 수 있다
- NUMA와 함께 보면 메모리 locality까지 같이 잡을 수 있다

이 문서는 [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)와 [NUMA Auto Balancing, Runtime Debugging](./numa-autobalancing-runtime-debugging.md)을 cgroup 관점에서 묶는다.

## 깊이 들어가기

### 1. cpuset은 quota가 아니라 배치다

quota는 시간 예산을 제한한다. cpuset은 실행 위치를 제한한다.

- quota만 있으면 다른 코어와 섞일 수 있다
- cpuset만 있으면 한정된 코어에서만 돌아간다
- 둘을 함께 써야 격리와 예측 가능성을 높일 수 있다

### 2. noisy neighbor는 CPU만의 문제가 아니다

같은 CPU 집합에서 다른 워크로드가 돌면 다음이 흔들린다.

- cache locality
- branch predictor 상태
- IRQ/softirq 분산
- NUMA 메모리 접근

### 3. cpuset은 안정성을 높이지만 유연성을 잃는다

- 코어를 고정하면 예측 가능성이 높아진다
- 하지만 특정 코어가 포화되면 대체 경로가 줄어든다
- 장애 시 자동 흡수가 어렵다

### 4. mems와 cpus를 같이 봐야 한다

CPU 집합만 고정하면 메모리가 다른 NUMA 노드에서 올 수 있다.

- `cpuset.cpus`와 `cpuset.mems`를 같이 잡아야 한다
- local memory를 유지하려면 두 축이 모두 중요하다

## 실전 시나리오

### 시나리오 1: CPU는 여유 있는데 특정 서비스 p99만 튄다

가능한 원인:

- 다른 서비스와 같은 CPU 집합을 공유한다
- cache locality가 깨진다
- IRQ가 섞여 들어온다

진단:

```bash
cat /sys/fs/cgroup/cpuset.cpus
cat /sys/fs/cgroup/cpuset.mems
taskset -cp <pid>
```

### 시나리오 2: 한 노드에서만 latency가 안정적이다

가능한 원인:

- cpuset 배치가 잘 됐다
- noisy neighbor 영향이 적다
- NUMA locality도 맞았다

### 시나리오 3: cpuset을 썼더니 오히려 코어 하나가 뜨거워졌다

가능한 원인:

- CPU 집합이 너무 좁다
- load balance가 깨진다
- worker와 interrupt가 한정된 코어에 쏠린다

## 코드로 보기

### CPU 집합 확인

```bash
cat /sys/fs/cgroup/cpuset.cpus
cat /sys/fs/cgroup/cpuset.mems
```

### affinity와 같이 보는 감각

```bash
taskset -cp <pid>
ps -eo pid,psr,comm | head
```

### 단순 모델

```text
shared cores
  -> noisy neighbor interference
  -> cache and scheduler locality degrade
  -> tail latency increases
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| cpuset 격리 | noisy neighbor를 줄인다 | 유연성이 떨어진다 | 핵심 서비스 |
| 넓은 CPU 집합 | 부하 흡수가 쉽다 | 간섭이 늘 수 있다 | 일반 워크로드 |
| cpuset + NUMA 고정 | locality가 좋다 | 운영 복잡도 증가 | 대형 JVM/DB |
| 동적 배치 | 자원 활용이 좋다 | 예측성이 떨어진다 | 탄력적 클러스터 |

## 꼬리질문

> Q: cpuset은 quota와 무엇이 다른가요?
> 핵심: quota는 시간, cpuset은 위치를 제한한다.

> Q: noisy neighbor는 왜 cpuset으로 줄이나요?
> 핵심: 같은 코어와 NUMA 경계를 분리하면 간섭이 줄 수 있기 때문이다.

> Q: cpuset만 쓰면 충분한가요?
> 핵심: 아니다. quota와 NUMA, IRQ 배치까지 같이 봐야 한다.

## 한 줄 정리

cpuset은 CPU를 얼마나 쓰느냐보다 어디에서 쓰느냐를 통제해 noisy neighbor를 줄이는 데 유용하지만, 너무 좁히면 hot core를 만든다.
