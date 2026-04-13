# CFS Bandwidth, Burst Behavior

> 한 줄 요약: CFS bandwidth controller는 평균 quota만 보지 말고 period 안에서의 burst 소모와 throttling 회복 패턴을 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [cgroup CPU Throttling, Quota, Runtime Debugging](./cgroup-cpu-throttling-quota-runtime-debugging.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [Scheduler Classes, nice, RT Trade-offs](./scheduler-classes-nice-rt-tradeoffs.md)

> retrieval-anchor-keywords: CFS bandwidth, quota period, throttling recovery, burst behavior, nr_periods, nr_throttled, cpu.max, cpu.stat, quota refill

## 핵심 개념

CFS bandwidth controller는 cgroup에 CPU 시간을 period 단위로 나눠준다. 버스트가 짧고 강하면 quota를 빨리 소진하고, 이후 같은 period 내에서 runnable 태스크가 있어도 실행이 멈출 수 있다.

- `period`: quota가 재충전되는 시간 구간이다
- `quota`: 한 period에서 쓸 수 있는 시간 예산이다
- `nr_periods`: 주기 수다
- `nr_throttled`: throttling이 걸린 횟수다

왜 중요한가:

- 평균 CPU 사용률만 보면 burst 패턴을 놓치기 쉽다
- period 시작 직후 CPU를 몰아 쓰는 워크로드는 불리할 수 있다
- API와 배치가 같은 cgroup에 있으면 회복 패턴이 서로 간섭한다

이 문서는 [cgroup CPU Throttling, Quota, Runtime Debugging](./cgroup-cpu-throttling-quota-runtime-debugging.md)보다 더 세밀하게 period 안의 소모와 회복을 본다.

## 깊이 들어가기

### 1. bandwidth는 "총량"과 "타이밍"이 둘 다 중요하다

같은 quota라도 분포에 따라 체감이 다르다.

- 초반 burst에 몰리면 빨리 throttling된다
- 고르게 쓰면 period를 더 안정적으로 활용한다
- 짧은 response path는 순간 spike에 취약하다

### 2. recovery는 다음 period까지 기다리는 구조다

quota를 다 쓰면 같은 period 안에서는 더 못 뛴다.

- runnable이어도 멈춘다
- 다음 period까지 대기한다
- burst 주기와 period가 안 맞으면 지연이 반복된다

### 3. `nr_periods`와 `nr_throttled`를 같이 봐야 한다

- period가 많아도 throttled가 거의 없으면 괜찮을 수 있다
- throttled가 자주 늘면 burst pattern이 quota를 자주 넘는 것이다
- `throttled_usec`까지 봐야 실제 피해를 알 수 있다

### 4. 같은 quota라도 workload에 따라 다르게 망가진다

- CPU 초기화가 큰 API
- decompression/serialization이 큰 경로
- batch vs online 혼재

## 실전 시나리오

### 시나리오 1: p95보다 p99가 유독 튄다

가능한 원인:

- burst 초반에 quota가 소모된다
- period 끝까지 throttling된다
- tail 요청이 굶는다

진단:

```bash
cat /sys/fs/cgroup/cpu.stat
cat /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/cpu.pressure
```

### 시나리오 2: batch job이 짧게는 빠른데 전체적으로는 불안정하다

가능한 원인:

- 초반 burst가 period를 잡아먹는다
- 회복 구간이 짧다
- 다른 워크로드가 같은 cgroup에 있다

### 시나리오 3: quota를 늘렸는데도 지연 패턴이 비슷하다

가능한 원인:

- period와 burst 분포가 여전히 안 맞는다
- load는 줄었지만 smoothing이 없다
- run queue/pressure가 다른 곳에 있다

이 경우는 [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)와 같이 본다.

## 코드로 보기

### bandwidth 상태 보기

```bash
cat /sys/fs/cgroup/cpu.stat
watch -n 1 'cat /sys/fs/cgroup/cpu.stat'
```

### quota/period 예시

```bash
echo "50000 100000" > /sys/fs/cgroup/cpu.max
```

의미:

- 100ms period에 50ms 사용 가능
- 평균 50% CPU

### burst 감각 모델

```text
period starts
  -> burst consumes quota quickly
  -> throttling occurs
  -> next period restores budget
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 짧은 period | burst 회복이 빠르다 | 관리 오버헤드가 있다 | 지연 민감 |
| 긴 period | 스파이크 흡수에 유리 | 독점 시간이 길어질 수 있다 | throughput 우선 |
| 높은 quota | throttling이 줄어든다 | noisy neighbor 위험 | 핵심 서비스 |
| workload 분리 | 패턴 간섭을 줄인다 | 운영 비용 증가 | batch/API 혼재 |

## 꼬리질문

> Q: CFS bandwidth에서 burst가 왜 문제인가요?
> 핵심: quota를 초반에 빨리 써서 period 내 나머지 시간이 throttling될 수 있기 때문이다.

> Q: `nr_periods`와 `nr_throttled`는 왜 같이 보나요?
> 핵심: 주기 대비 throttling 빈도를 봐야 burst 패턴을 알 수 있기 때문이다.

> Q: quota만 늘리면 해결되나요?
> 핵심: 아니다. period와 workload 분포도 같이 봐야 한다.

## 한 줄 정리

CFS bandwidth는 평균 quota보다 period 안의 burst 소모와 throttling 회복 패턴이 더 중요하며, 분포가 안 맞으면 tail latency가 흔들린다.
