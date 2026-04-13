# Scheduler Classes, nice, RT Trade-offs

> 한 줄 요약: Linux 스케줄러는 하나가 아니라 여러 클래스의 합이며, nice는 CFS 안에서만 의미가 크고 RT는 완전히 다른 우선순위 세계를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [cgroup CPU Throttling, Quota, Runtime Debugging](./cgroup-cpu-throttling-quota-runtime-debugging.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)

> retrieval-anchor-keywords: scheduler class, CFS, SCHED_FIFO, SCHED_RR, SCHED_DEADLINE, nice, rtprio, realtime priority, fairness, latency trade-off

## 핵심 개념

Linux는 모든 태스크를 같은 방식으로 스케줄하지 않는다. 스케줄러 클래스가 다르면 우선순위 철학도 다르다.

- `CFS`: 일반적인 공정성 중심 스케줄러다
- `SCHED_FIFO`: RT 우선순위 기반 선점형 정책이다
- `SCHED_RR`: RT이면서 time slice를 나눠 쓴다
- `SCHED_DEADLINE`: deadline 기반 스케줄링이다

왜 중요한가:

- nice만 조정해도 해결되지 않는 지연이 있다
- RT 태스크가 많으면 일반 태스크가 굶을 수 있다
- scheduler class는 "빠르게"와 "안정적으로" 사이의 선택이다

이 문서는 [CFS Scheduler, nice, CPU Fairness](./cfs-scheduler-nice-cpu-fairness.md)를 확장해, RT 계열과 운영 트레이드오프를 다룬다.

## 깊이 들어가기

### 1. CFS와 RT는 같은 층이 아니다

CFS 안에서는 `vruntime`과 weight가 중요하다. RT는 더 강한 우선순위 규칙을 적용한다.

- CFS 태스크는 RT 태스크보다 아래에 있다
- RT가 과하면 일반 프로세스가 실행 기회를 잃는다
- deadline 정책은 또 다른 제약을 가진다

즉 nice를 조정하는 것으로 RT 성격의 문제를 고칠 수 없다.

### 2. RT는 지연을 줄이지만 시스템을 위험하게 만들 수 있다

RT는 특정 작업의 deadline을 지키는 데 유리하다.

- 오디오, 제어 루프, 산업 제어처럼 지터가 중요한 경우 유용하다
- 하지만 너무 강한 RT 태스크는 다른 작업을 굶길 수 있다
- 시스템 관리용 daemon까지 밀리면 전체 운영이 위험해진다

### 3. nice는 "부드러운 조정", RT는 "강한 보장"이다

nice는 같은 CFS 그룹 내 배분을 바꾸는 힌트다. RT는 우선순위 체계를 바꾼다.

- nice: 배치와 API의 공정성 조정
- RT: 특정 루프의 지연을 줄이는 용도

그래서 서버 일반 워크로드에는 보통 nice나 cgroup이 더 현실적이다.

### 4. scheduler class는 tail latency를 바꾼다

평균 CPU 사용률이 같아도 scheduler class가 다르면 응답성은 다르게 보인다.

- RT 태스크가 있으면 짧은 경로는 빨라질 수 있다
- CFS 태스크가 밀리면 일반 요청 p99는 나빠질 수 있다
- 잘못된 RT 사용은 시스템 전체를 불안정하게 만든다

## 실전 시나리오

### 시나리오 1: 특정 프로세스가 계속 CPU를 선점한다

가능한 원인:

- RT policy로 실행 중이다
- 우선순위가 너무 높다
- 긴 루프가 yield 없이 돈다

진단:

```bash
ps -eo pid,cls,pri,rtprio,ni,comm | head
chrt -p <pid>
```

### 시나리오 2: nice를 낮췄는데 기대처럼 빨라지지 않는다

가능한 원인:

- 병목이 CPU가 아니다
- cgroup quota가 먼저 막는다
- RT 또는 다른 고우선순위 태스크가 이미 있다

진단:

```bash
top -H -p <pid>
cat /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/cpu.stat
```

### 시나리오 3: 실시간 작업을 넣었더니 다른 서비스가 굶는다

가능한 원인:

- RT 우선순위가 너무 높다
- 방어적인 CPU cap이 없다
- run queue에서 CFS 태스크가 계속 밀린다

대응:

- RT 사용 범위를 최소화한다
- rate limit이나 watchdog를 둔다
- 일반 서비스와 노드를 분리한다

### 시나리오 4: deadline이 중요한 잡인데 jitter가 크다

가능한 원인:

- CFS로 돌리고 있다
- scheduler class가 문제 요구사항과 안 맞는다
- IRQ/softirq가 CPU를 흔든다

이 경우는 [softirq, hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)도 같이 봐야 한다.

## 코드로 보기

### 현재 스케줄 정책 확인

```bash
ps -eo pid,cls,pri,rtprio,ni,comm | head
chrt -p <pid>
```

### RT 정책 예시

```bash
chrt -f -p 80 <pid>
```

주의점:

- RT는 강력한 만큼 위험하다
- 잘못 쓰면 시스템이 멈춘 것처럼 보일 수 있다

### nice 조정 예시

```bash
renice -n 10 -p <pid>
```

### scheduler 관련 상태 보기

```bash
cat /proc/<pid>/sched
cat /proc/<pid>/status | grep -E 'Cpus_allowed|Threads'
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| CFS 기본 | 일반 서버에 안정적이다 | 지터 보장이 약하다 | 대부분의 백엔드 |
| nice 조정 | 간단하다 | 강한 보장이 없다 | 배치/보조 태스크 |
| RT policy | 지연을 강하게 줄인다 | 다른 태스크를 굶길 수 있다 | 엄격한 실시간 루프 |
| 작업 분리 | 운영이 예측 가능하다 | 자원 비용이 든다 | 중요 서비스 보호 |

## 꼬리질문

> Q: nice와 RT priority의 차이는 무엇인가요?
> 핵심: nice는 CFS 내부 배분이고, RT priority는 다른 클래스 위에 서는 우선순위다.

> Q: RT를 쓰면 무조건 더 빠른가요?
> 핵심: 아니다. 지터를 줄일 수 있지만 시스템 전체 위험이 커질 수 있다.

> Q: scheduler class 문제를 의심해야 하는 신호는?
> 핵심: 특정 태스크가 지나치게 잘 실행되거나, 반대로 일반 태스크가 굶는 경우다.

> Q: 서버에서 RT는 흔한가요?
> 핵심: 보통은 아니다. 특별한 지연 요구가 있을 때만 제한적으로 쓴다.

## 한 줄 정리

Linux scheduler는 CFS, RT, deadline 같은 서로 다른 규칙의 조합이며, nice는 그중 CFS의 공정성을 다듬는 도구일 뿐이다.
