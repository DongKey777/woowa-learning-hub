# cgroup CPU Throttling, Quota, Runtime Debugging

> 한 줄 요약: CPU가 남아 보여도 cgroup quota가 막히면 프로세스는 실제로는 "뛰고 싶어도 못 뛰는" 상태가 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: cpu.max, cpu.stat, throttling, nr_throttled, throttled_usec, cgroup quota, cfs quota, period, cpu.pressure, load average triage, cpu saturation vs throttling

## 핵심 개념

cgroup CPU quota는 프로세스 그룹이 특정 주기 동안 사용할 수 있는 CPU 시간을 제한한다. 이 제한에 걸리면 커널은 runnable 태스크가 있어도 더 이상 실행하지 않고, 다음 period까지 기다리게 만든다.

- `cpu.max`: cgroup v2에서 quota와 period를 표현한다
- `cpu.stat`: throttling 횟수와 시간을 보여준다
- `quota`: 한 주기 동안 쓸 수 있는 CPU 시간이다
- `period`: quota를 재충전하는 시간 단위다

왜 중요한가:

- 노드 전체 CPU 사용률이 낮아도 컨테이너는 느릴 수 있다
- nice를 바꿔도 quota가 막으면 못 뛴다
- throttling은 CPU 병목처럼 보이지만 실제로는 정책 병목이다

이 문서는 [container, cgroup, namespace](./container-cgroup-namespace.md)와 [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)를 운영 진단으로 연결한다.

## 깊이 들어가기

### 1. throttling은 CPU 부족이 아니라 시간 배분 제한이다

quota는 물리 CPU가 부족해서 생기는 게 아니다. 같은 CPU가 있어도 cgroup에 할당된 시간 예산이 떨어지면 멈춘다.

- 노드는 여유가 있어도 그룹은 멈춘다
- burst가 길면 period 끝까지 대기한다
- 짧은 지연이 아니라 주기적인 굶주림처럼 보일 수 있다

### 2. CFS 공정성과 quota는 다른 층이다

CFS는 runnable 태스크들 사이의 공정성을 맞춘다. quota는 그 위에서 아예 전체 파이를 잘라낸다.

- CFS: 누가 먼저/얼마나 공정하게 뛸지 결정한다
- cgroup quota: 그룹이 총 얼마를 뛸 수 있는지 제한한다

그래서 nice가 좋아도 throttling이 있으면 응답이 밀린다.

### 3. throttling은 load average를 왜곡한다

throttled 태스크는 runnable이지만 실행 기회를 못 받는다. 이 상태는 load average나 run queue만 보면 충분히 설명되지 않는다.

- load average는 밀려 있는 압력을 보여준다
- throttling은 정책으로 잘린 시간을 보여준다
- PSI는 그 결과로 생긴 stall을 보여준다

즉 `load average`가 높다고 바로 scheduler contention으로 결론내리면 안 된다. 초보자용 1차 분기는 [Load Average Triage: CPU Saturation vs cgroup Throttling vs I/O Wait](./load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md)처럼 saturation, throttling, I/O wait를 먼저 가르는 것이다.

### 4. bursty workload가 특히 취약하다

burst가 짧고 강할수록 quota는 더 빨리 소진된다.

- 요청 초반에 CPU를 몰아 쓰는 경로
- GC, serialization, decompression 같이 spike가 있는 작업
- 배치와 API가 같은 quota를 공유하는 경우

## 실전 시나리오

### 시나리오 1: 노드 CPU는 한가한데 컨테이너 p99만 튄다

가능한 원인:

- quota가 낮다
- period가 너무 길거나 burst 패턴과 안 맞는다
- 같은 cgroup에 배치와 API가 섞여 있다

진단:

```bash
cat /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/cpu.stat
cat /sys/fs/cgroup/cpu.pressure
```

판단 포인트:

- `nr_throttled`가 빠르게 증가하는가
- `throttled_usec`가 지속적으로 쌓이는가
- PSI의 `cpu some`이 같이 높아지는가

### 시나리오 2: 배치 돌리면 API가 같이 느려진다

가능한 원인:

- 같은 cgroup quota를 공유한다
- 배치가 period 시작 직후 CPU를 선점한다
- API가 배치 throttling 뒤에 굶는다

대응:

- API와 배치를 다른 cgroup으로 분리한다
- 배치에 더 낮은 quota를 준다
- burst 허용이 필요하면 period와 quota를 다시 설계한다

### 시나리오 3: 스레드를 늘렸는데 처리량이 안 오른다

가능한 원인:

- runnable 수만 늘고 quota는 그대로다
- context switch만 많아진다
- throttling 때문에 더 자주 멈춘다

이 경우는 [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)와 함께 보아야 한다.

## 코드로 보기

### cgroup v2 CPU 상태 확인

```bash
cat /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/cpu.stat
```

### throttling 감시

```bash
watch -n 1 'cat /sys/fs/cgroup/cpu.stat; echo; cat /sys/fs/cgroup/cpu.pressure'
```

### 제한 예시

```bash
echo "200000 100000" > /sys/fs/cgroup/cpu.max
```

의미:

- 100ms period마다 20ms만 사용 가능
- 총 20% CPU quota

### 진단용 샘플

```bash
perf stat -p <pid> -e cpu-clock,task-clock,context-switches -- sleep 30
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| quota 엄격화 | 노드 공정성이 좋아진다 | burst latency가 악화될 수 있다 | 멀티테넌트 환경 |
| quota 완화 | spike를 흡수한다 | noisy neighbor가 심해질 수 있다 | API burst 허용 |
| cgroup 분리 | 병목을 분명히 나눈다 | 운영 복잡도가 증가한다 | API/배치 혼재 |
| bigger period | burst 흡수가 쉬워진다 | 긴 독점이 생길 수 있다 | 특정 워크로드 조정 |

## 꼬리질문

> Q: CPU throttling은 CPU saturation과 같은가요?
> 핵심: 아니다. saturation은 실제 경쟁이고, throttling은 정책으로 잘린 시간이다.

> Q: nice를 조정하면 throttling이 없어지나요?
> 핵심: 아니다. quota가 먼저면 nice는 우선순위만 바꾼다.

> Q: `cpu.stat`에서 무엇을 봐야 하나요?
> 핵심: `nr_throttled`와 `throttled_usec`가 가장 직접적이다.

> Q: quota가 낮아도 노드가 멀쩡한 이유는?
> 핵심: cgroup은 그룹 단위 제한이므로 다른 그룹은 여유가 있을 수 있다.

## 한 줄 정리

cgroup CPU throttling은 커널이 태스크를 느리게 하는 것이 아니라, 미리 정한 시간 예산을 초과한 그룹의 실행을 멈추는 정책이다.
