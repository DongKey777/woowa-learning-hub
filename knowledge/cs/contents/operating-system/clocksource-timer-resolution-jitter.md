# Clocksource, Timer Resolution, Jitter

> 한 줄 요약: timer resolution은 "얼마나 자주 깨울 수 있나"의 문제이고, clocksource 품질과 timer jitter는 지연 측정과 주기 작업의 정확도를 흔든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [monotonic clock, wall clock, timeout, deadline](./monotonic-clock-wall-clock-timeout-deadline.md)
> - [Scheduler Classes, nice, RT Trade-offs](./scheduler-classes-nice-rt-tradeoffs.md)
> - [softirq, hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)

> retrieval-anchor-keywords: clocksource, hrtimer, jiffy, timer resolution, jitter, CLOCK_MONOTONIC, timerfd, nohz, timekeeping

## 핵심 개념

Linux는 시간을 하나의 숫자로만 다루지 않는다. clocksource는 현재 시간을 계산하는 기준이고, timer resolution은 커널이 얼마나 세밀하게 타이머를 잡을 수 있는지와 관련된다. jitter는 이 타이밍이 흔들리는 정도다.

- `clocksource`: 시간을 읽는 기반 소스다
- `hrtimer`: 고해상도 타이머다
- `jiffy`: 커널 tick 기반 시간 단위다
- `jitter`: 실제 wakeup이 예정 시각에서 벗어나는 정도다

왜 중요한가:

- timeout과 deadline이 흔들리면 retry와 backoff가 망가진다
- periodic job이 밀리면 batch window가 길어진다
- latency 측정도 clock 품질에 영향을 받는다

이 문서는 [monotonic clock, wall clock, timeout, deadline](./monotonic-clock-wall-clock-timeout-deadline.md)을 커널 타이머 관점으로 좁혀서 본다.

## 깊이 들어가기

### 1. clocksource는 시간의 "근거"다

커널은 여러 방식으로 시간을 읽을 수 있고, 그중 무엇을 쓰느냐가 정확성과 비용에 영향을 준다.

- 더 정확한 소스는 더 비쌀 수 있다
- 덜 정확한 소스는 jitter를 키울 수 있다
- 시스템 전원 상태나 가상화 환경도 영향을 줄 수 있다

### 2. hrtimer는 세밀하지만 완전무결하지 않다

고해상도 타이머는 jiffy보다 더 정밀하게 동작할 수 있지만, 실제 wakeup은 scheduler와 interrupt path에 영향을 받는다.

- 타이머가 울려도 즉시 실행은 아니다
- run queue와 IRQ pressure가 있으면 늦어진다
- periodic 작업은 drift가 누적될 수 있다

### 3. jitter는 측정과 제어를 모두 망친다

- timeout이 짧은 RPC
- 주기적 heartbeat
- 배치 간격 제어
- exponential backoff

이런 곳에서 jitter가 커지면 시스템은 불안정해진다.

### 4. clocksource 문제는 성능 문제처럼 보일 수 있다

실제 병목이 아니라도 시간이 흔들리면 다음이 나타난다.

- timeout 오판
- retry 폭주
- heartbeat miss
- latency 측정 노이즈

## 실전 시나리오

### 시나리오 1: heartbeat가 가끔 늦게 도착한다

가능한 원인:

- timer wakeup jitter
- CPU affinity/IRQ pressure
- scheduler contention

진단:

```bash
cat /sys/devices/system/clocksource/clocksource0/current_clocksource
cat /proc/timer_list | head
```

### 시나리오 2: timeout이 들쭉날쭉하다

가능한 원인:

- wall clock을 잘못 쓴다
- timer resolution이 충분하지 않다
- wakeup이 run queue에서 밀린다

### 시나리오 3: 주기 작업이 누적해서 늦어진다

가능한 원인:

- jitter가 drift로 누적된다
- periodic task가 CPU pressure를 만난다
- interrupt path가 바쁘다

이 경우는 [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)와 같이 본다.

## 코드로 보기

### clocksource 확인

```bash
cat /sys/devices/system/clocksource/clocksource0/current_clocksource
cat /sys/devices/system/clocksource/clocksource0/available_clocksource
```

### timerfd 사용 감각

```c
int tfd = timerfd_create(CLOCK_MONOTONIC, 0);
```

### jitter 측정의 간단한 생각

```text
expected wakeup time
  vs
actual wakeup time
  -> difference = jitter
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| hrtimer 사용 | 정밀하다 | 시스템 부하 영향을 받는다 | 짧은 timeout |
| jiffy 기반 | 단순하고 싸다 | 정밀도가 낮다 | 거친 주기 작업 |
| CLOCK_MONOTONIC | 시간 역행 걱정이 적다 | wall clock과 다르다 | timeout/deadline |
| wall clock | 사람에게 친숙하다 | NTP/조정에 영향받는다 | 표시/로그 |

## 꼬리질문

> Q: clocksource와 timer resolution은 같은가요?
> 핵심: 아니다. clocksource는 시간을 읽는 기준이고, resolution은 타이머 정밀도다.

> Q: jitter가 왜 문제인가요?
> 핵심: timeout, retry, heartbeat, 주기 작업이 다 흔들리기 때문이다.

> Q: timeout은 왜 monotonic clock을 많이 쓰나요?
> 핵심: wall clock 조정에 덜 흔들리기 때문이다.

## 한 줄 정리

clocksource와 timer resolution은 시간 측정과 wakeup의 기반이며, jitter가 크면 timeout과 주기 작업의 신뢰성이 흔들린다.
