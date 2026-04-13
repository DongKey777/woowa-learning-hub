# Cgroup IO Controller, Basics

> 한 줄 요약: cgroup I/O controller는 디스크와 블록 큐를 워크로드별로 나누어 쓰기/읽기 속도와 우선순위를 조정하는 격리 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [I/O Scheduler, blk-mq Basics](./io-scheduler-blk-mq-basics.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)

> retrieval-anchor-keywords: cgroup io controller, io.max, io.weight, io.stat, io.pressure, cgroup v2 io, blkio, io throttling, io isolation

## 핵심 개념

cgroup v2의 I/O controller는 워크로드별로 디스크 사용량과 우선순위를 조정한다. CPU quota처럼 I/O도 격리와 fairness가 필요하다.

- `io.max`: throughput 상한을 제한한다
- `io.weight`: 상대적 우선순위를 준다
- `io.stat`: 실제 I/O 사용량을 보여준다
- `io.pressure`: I/O 대기로 인한 stall을 보여준다

왜 중요한가:

- 배치가 디스크를 독점하는 것을 막을 수 있다
- API와 background job을 분리할 수 있다
- writeback과 page cache pressure를 제어하는 데 도움이 된다

이 문서는 [I/O Scheduler, blk-mq Basics](./io-scheduler-blk-mq-basics.md)와 [Dirty Page Ratios, Writeback Tuning](./dirty-page-ratios-writeback-tuning.md)를 cgroup 격리 관점에서 묶는다.

## 깊이 들어가기

### 1. io controller는 디스크 fairness 도구다

CPU와 달리 storage는 큐와 배치가 중요하다.

- 워크로드별로 우선순위를 나눌 수 있다
- 한 cgroup이 장치를 다 먹는 것을 막을 수 있다
- latency-sensitive 경로를 보호할 수 있다

### 2. `io.max`와 `io.weight`는 역할이 다르다

- `io.max`: 절대 제한
- `io.weight`: 상대적 우선순위

### 3. io pressure와 함께 봐야 한다

흐름을 제한해도 wait이 길면 latency는 여전히 문제다.

### 4. page cache와 writeback은 I/O controller와 맞물린다

dirty page가 내려갈 때 특정 워크로드가 너무 많은 디스크를 쓰지 않도록 조정할 수 있다.

## 실전 시나리오

### 시나리오 1: batch job이 API latency를 망친다

가능한 원인:

- 같은 디스크를 독점한다
- writeback burst가 몰린다
- io.weight가 없다

진단:

```bash
cat /sys/fs/cgroup/io.stat
cat /sys/fs/cgroup/io.pressure
```

### 시나리오 2: 디스크는 바쁜데 어떤 워크로드가 문제인지 모른다

가능한 원인:

- per-cgroup 관측이 없다
- queue depth와 controller가 분리되어 있지 않다
- io.stat를 안 본다

### 시나리오 3: 제한을 걸었는데도 체감이 완전히 안 좋아지지 않는다

가능한 원인:

- page cache pressure가 남아 있다
- blk-mq scheduler와 정책이 안 맞는다
- 다른 cgroup이 여전히 과다 사용 중이다

## 코드로 보기

### I/O controller 상태 확인

```bash
cat /sys/fs/cgroup/io.stat
cat /sys/fs/cgroup/io.pressure
```

### 개념적 제한 예시

```bash
echo "8:0 rbps=10485760 wbps=10485760" > /sys/fs/cgroup/io.max
```

### 상대적 우선순위 예시

```bash
echo 100 > /sys/fs/cgroup/io.weight
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| io.weight 조정 | 공정성을 높인다 | 절대 제한은 아니다 | mixed workloads |
| io.max 제한 | 과다 사용을 막는다 | throughput이 줄 수 있다 | noisy batch |
| 기본값 유지 | 단순하다 | 간섭이 심할 수 있다 | 소규모 호스트 |

## 꼬리질문

> Q: cgroup I/O controller는 무엇을 조절하나요?
> 핵심: 워크로드별 디스크 throughput과 우선순위를 조절한다.

> Q: io.weight와 io.max 차이는?
> 핵심: weight는 상대 우선순위, max는 절대 상한이다.

> Q: io.pressure는 왜 보나요?
> 핵심: 디스크 사용량보다 실제 stall 시간을 보기 위해서다.

## 한 줄 정리

cgroup I/O controller는 디스크를 워크로드별로 격리하고 공정성을 조절하는 도구이며, io.stat와 io.pressure를 같이 봐야 효과를 해석할 수 있다.
