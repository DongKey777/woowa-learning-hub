# CFS Scheduler, nice, CPU Fairness

> 한 줄 요약: CFS는 CPU 시간을 "같이 나누는 것"이 아니라, `vruntime` 기준으로 상대적 공정성을 맞춰서 여러 워크로드의 체감 편차를 줄인다.

**난이도: 🔴 Advanced**

> retrieval-anchor-keywords: CFS, nice, vruntime, schedstat, scheduler fairness, run queue, weight, CPU fairness, wakeup latency, scheduling delay

## 핵심 개념

리눅스의 `CFS(Completely Fair Scheduler)`는 각 태스크가 CPU를 얼마나 썼는지를 단순 누적 시간으로 보지 않고, `weight`를 반영한 가상 실행 시간(`vruntime`)으로 비교한다.

- `nice`: 프로세스의 우선순위 힌트를 준다.
- `weight`: nice 값에 따라 CPU 배분 비중이 달라진다.
- `vruntime`: "이 태스크가 공정하게 받은 시간"을 누적한 값처럼 다룬다.
- `run queue`: 실행 가능한 태스크들이 대기하는 곳이다.

실무에서 중요한 이유는 간단하다.

- 같은 서버에서 API, 배치, 백그라운드 작업이 섞이면 CPU 경합이 생긴다.
- nice 값을 잘못 두면 중요한 요청이 밀리거나, 반대로 배치가 굶는다.
- CPU 사용률이 높지 않아도 latency가 튈 수 있다.

관련 문서:

- [Scheduler Fairness, Page Cache, File System Basics](./scheduler-fairness-page-cache.md)
- [컨테이너, cgroup, namespace](./container-cgroup-namespace.md)
- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
- [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md)

## 깊이 들어가기

### 1. CFS가 공정성을 보는 방식

CFS는 "먼저 온 순서"나 "무조건 라운드 로빈"으로 돌지 않는다. 대신 `vruntime`이 가장 작은 태스크를 우선 실행한다.

핵심 감각은 이렇다.

- CPU를 많이 쓴 태스크는 `vruntime`이 빨리 증가한다.
- `nice`가 낮아 `weight`가 큰 태스크는 같은 실제 CPU 시간을 써도 `vruntime` 증가가 느리다.
- 결국 스케줄러는 "덜 받은 태스크"를 우선한다.

즉, 공정성은 절대 시간의 평등이 아니라 **가중치가 반영된 상대적 균형**이다.

### 2. nice는 절대 우선순위가 아니다

`nice`는 이름 때문에 "중요도"처럼 보이지만, 실제로는 CPU 배분 비율을 조정하는 힌트에 가깝다.

- `nice -20`에 가까울수록 더 많은 CPU 비중을 받는다.
- `nice 19`에 가까울수록 덜 받는다.
- root 권한 없이 낮은 nice 값으로 내리기 어렵다.

운영에서 자주 하는 실수는 다음이다.

- "이 프로세스는 덜 중요하니 nice만 올리면 끝"이라고 생각한다.
- 하지만 메모리 압박, I/O 대기, 락 경합은 nice만으로 해결되지 않는다.

### 3. CFS에서 중요한 건 평균보다 tail latency다

서버에서 체감 문제는 보통 평균 CPU가 아니라 tail latency로 드러난다.

- 워커 수가 많아져도 한 요청이 오래 밀릴 수 있다.
- 짧은 인터랙티브 요청과 긴 배치 작업이 섞이면 응답 편차가 커진다.
- container/cgroup의 CPU quota까지 얹히면 더 헷갈린다.

이 때문에 CFS는 단순히 "공평하게 나눠준다"가 아니라, **실제 서비스 품질을 망치지 않는 범위에서 균형을 맞추는 장치**로 봐야 한다.

### 4. cgroup과 같이 봐야 한다

컨테이너 환경에서는 CFS만으로 설명이 끝나지 않는다. `cgroup`이 CPU 사용 상한을 걸면, 프로세스가 `throttling`될 수 있다.

- 노드 전체 CPU는 남아도 컨테이너는 멈춘 것처럼 보일 수 있다.
- nice가 좋아도 quota가 부족하면 못 뛴다.
- scheduler 문제처럼 보여도 실제로는 cgroup 제한인 경우가 많다.

이 지점은 [컨테이너, cgroup, namespace](./container-cgroup-namespace.md)와 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 배치 작업 후 API p95가 튄다

원인 후보:

- 배치가 CPU를 많이 써서 run queue가 길어졌다.
- 배치와 API가 같은 노드, 같은 cgroup 자원을 공유한다.
- 배치의 nice 조정이 없어서 인터랙티브 요청이 밀린다.

진단:

```bash
uptime
vmstat 1
top -H
pidstat -u 1
cat /proc/schedstat
```

판단 포인트:

- CPU 사용률보다 run queue 길이를 본다.
- 특정 프로세스가 계속 CPU를 점유하는지 본다.
- 컨테이너라면 `cpu.max`, `cpu.stat`도 같이 본다.

### 시나리오 2: nice를 올렸는데도 별 차이가 없다

원인 후보:

- CPU가 아니라 I/O 대기나 락 경합이 병목이다.
- 태스크의 CPU 사용 자체가 작아서 체감 차이가 없다.
- cgroup quota가 먼저 병목이다.

즉 nice는 만능이 아니다. CPU 스케줄 비중을 조정할 뿐, 전체 응답시간의 모든 병목을 해결하지는 않는다.

### 시나리오 3: 한 노드에서 여러 워커를 돌리면 오히려 느려진다

원인 후보:

- context switch 비용이 증가한다.
- 캐시 locality가 깨진다.
- run queue 경쟁이 심해진다.

이 경우는 "CPU를 더 써서 빨라진다"가 아니라, **작업이 쪼개진 만큼 스케줄링 비용도 같이 늘어난다**는 문제다.

## 코드로 보기

### nice 값에 따른 우선순위 조정 감각

```bash
nice -n 10 ./batch-job
renice -n -5 -p <pid>
```

### CPU 압박을 볼 때의 기본 점검

```bash
ps -eo pid,ni,pri,pcpu,comm --sort=-pcpu | head
pidstat -p <pid> -u 1
cat /proc/<pid>/sched
```

### CFS 개념을 단순화한 의사 코드

```c
while (true) {
    task = pick_task_with_smallest_vruntime(runqueue);
    run(task, slice);
    task->vruntime += actual_runtime * weight_factor(task->nice);
    reinsert(runqueue, task);
}
```

실제 커널은 더 복잡하지만, 운영 감각은 이 정도로 이해하면 충분하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| CFS 기본값 | 일반 워크로드에 무난하다 | 특정 작업을 의도적으로 보호하지 않는다 | 대부분의 서버 |
| nice 조정 | 간단하고 빠르다 | CPU 외 병목은 못 잡는다 | 배치/보조 작업 완화 |
| cgroup CPU 제한 | 노드 안정성이 좋아진다 | 잘못 잡으면 throttling 발생 | 멀티테넌트 환경 |
| 전용 노드 분리 | 예측 가능성이 높다 | 비용이 든다 | 중요한 API, 대형 배치 |

운영에서는 "공정"과 "중요"를 같은 말로 쓰면 안 된다. 중요한 요청을 우대하려면 scheduler 힌트, cgroup, 배치 분리까지 같이 설계해야 한다.

## 꼬리질문

> Q: CFS는 정말 공정한가요?
> 핵심: 절대 평등이 아니라 가중치를 반영한 상대 공정성이다.

> Q: nice 값만 바꾸면 성능 문제가 해결되나요?
> 핵심: CPU 병목에는 도움 되지만, I/O, 락, 메모리 압박은 별도다.

> Q: 컨테이너에서 CPU가 느릴 때 nice와 cgroup 중 무엇을 먼저 봐야 하나요?
> 핵심: 먼저 `cpu.max`, `cpu.stat` 같은 quota/throttling을 보고, 그다음 nice와 run queue를 본다.

## 한 줄 정리

CFS는 `vruntime`과 weight로 CPU를 상대적으로 공정하게 나누고, nice는 그 비중을 조절하는 힌트다. 운영에서는 CPU 평균보다 run queue, throttling, tail latency를 함께 봐야 한다.
