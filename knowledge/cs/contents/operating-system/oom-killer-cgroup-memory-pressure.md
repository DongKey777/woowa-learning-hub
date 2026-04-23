# OOM Killer, cgroup Memory Pressure

> 한 줄 요약: 메모리가 부족해지면 Linux는 단순히 "느려지는" 게 아니라, cgroup 경계와 시스템 전체 상태를 보고 어떤 프로세스를 죽일지 결정한다.

**난이도: 🔴 Advanced**

## 핵심 개념

`OOM(Out Of Memory)`은 메모리가 정말 부족해 더 이상 할당을 못 하는 상태다. 이때 Linux는 커널이 멈추지 않도록 `OOM killer`를 동작시켜 일부 프로세스를 종료한다.

- `memory limit`: cgroup이 프로세스에 허용하는 메모리 상한이다.
- `memory pressure`: 메모리 회수가 자주 일어나는 상태다.
- `OOM killer`: 메모리를 많이 쓰거나 점수가 높은 희생자를 고른다.
- `swap`: 상황을 완화할 수 있지만, 잘못 쓰면 지연이 커진다.

실무에서 중요한 이유는 다음과 같다.

- "호스트는 멀쩡한데 컨테이너만 죽었다"가 흔하다.
- 메모리 누수와 순간 스파이크는 증상이 비슷하다.
- page cache, anonymous memory, JVM heap, native allocation이 같이 얽힌다.

관련 문서:

- [컨테이너, cgroup, namespace](./container-cgroup-namespace.md)
- [Page Replacement, Clock vs LRU](./page-replacement-clock-vs-lru.md)
- [Scheduler Fairness, Page Cache, File System Basics](./scheduler-fairness-page-cache.md)

## 깊이 들어가기

### 1. OOM은 "메모리 부족"의 마지막 단계다

메모리 압박은 보통 다음 순서로 악화된다.

- free memory 감소
- page reclaim 증가
- swap 사용 증가
- alloc 실패
- OOM 발생

즉 OOM은 시작이 아니라 끝이다. 운영에서는 OOM이 떠야 대응하는 게 아니라, 그 전에 pressure를 감지해야 한다.

### 2. cgroup OOM과 global OOM은 다르다

컨테이너 환경에서 흔한 건 cgroup 단위 OOM이다.

- cgroup memory limit을 넘으면 해당 그룹에서 희생자가 나온다.
- 호스트 전체 메모리가 남아도 컨테이너는 죽을 수 있다.
- 반대로 노드 전체가 메모리 압박이면 global OOM으로 번질 수 있다.

이 차이를 모르고 보면 "왜 아무 문제 없는 프로세스가 죽었지?"처럼 보인다.

### 3. OOM killer는 랜덤이 아니다

커널은 아무 프로세스나 죽이지 않는다. 일반적으로 다음 요소가 반영된다.

- 메모리 사용량이 큰지
- `oom_score_adj`로 보호받거나 불이익을 받는지
- 해당 프로세스를 죽였을 때 회복 가능성이 어떤지

운영적으로는 "중요한 프로세스가 살아남도록 조정했는가"가 핵심이다.

### 4. memory pressure는 느린 장애를 만든다

OOM 전에 이미 서비스 품질이 망가질 수 있다.

- reclaim이 길어져 latency가 늘어난다.
- swap이 많아지면 CPU보다 메모리 대기 시간이 커진다.
- page cache가 밀리면 디스크 I/O가 늘어난다.

즉 "아직 안 죽었으니 괜찮다"가 아니다. pressure 상태 자체가 장애다.

## 실전 시나리오

### 시나리오 1: 컨테이너가 갑자기 재시작된다

증상:

- 애플리케이션 로그에 `Killed`가 남는다.
- Kubernetes에서는 `OOMKilled`로 보인다.
- 호스트는 특별히 죽지 않았다.

진단:

```bash
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.events
dmesg | tail -n 50
```

판단 포인트:

- `memory.events`의 `oom`과 `oom_kill`을 본다.
- limit 근처에서 반복적으로 튀는지 본다.
- JVM, native, cache, buffer allocation을 나눠 본다.

### 시나리오 2: 트래픽 급증 뒤 p99가 급격히 튄다

원인 후보:

- 메모리 reclaim이 늘었다.
- swap이 활성화되면서 page fault 비용이 커졌다.
- cache miss가 증가했다.

체크:

```bash
vmstat 1
sar -B 1
grep -E 'pgfault|pgmajfault|pswpin|pswpout' /proc/vmstat
free -h
```

### 시나리오 3: 같은 JVM인데 특정 환경에서만 OOM

원인 후보:

- heap 외 native memory가 커졌다.
- thread stack, direct buffer, mmap이 늘었다.
- cgroup limit이 낮아서 host 기준으론 괜찮아 보여도 컨테이너는 넘친다.

여기서는 heap size만 보지 말고 process 전체 RSS와 cgroup current를 같이 봐야 한다.

## 코드로 보기

### cgroup 메모리 상태 확인

```bash
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.high
cat /sys/fs/cgroup/memory.events
```

### 프로세스별 메모리 점검

```bash
ps -eo pid,rss,vsz,comm --sort=-rss | head
cat /proc/<pid>/status | grep -E 'VmRSS|VmSize|Threads'
cat /proc/<pid>/oom_score
cat /proc/<pid>/oom_score_adj
```

### OOM 보호 의사 설정

```bash
echo -1000 > /proc/<pid>/oom_score_adj
```

실무에서는 무조건 보호하기보다, 재시작 가능 여부와 서비스 중요도를 같이 보고 조정한다.

### 메모리 압박을 단순화한 흐름

```text
alloc 실패 or reclaim 과다
  -> pressure 증가
  -> 커널이 희생자 선정
  -> 프로세스 종료
  -> 서비스 일부 복구 또는 장애 전파
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 메모리 limit 엄격 적용 | 노드 안정성이 높다 | 버스트에 취약하다 | 멀티테넌트 컨테이너 |
| `oom_score_adj` 조정 | 중요한 프로세스를 보호한다 | 잘못하면 희생자 선택이 왜곡된다 | system daemon, 핵심 워커 |
| swap 허용 | 순간 압박을 완충한다 | 지연이 커질 수 있다 | 덜 민감한 워크로드 |
| limit 여유 확보 | OOM 위험이 줄어든다 | 자원 효율이 떨어진다 | 핵심 API, JVM 서버 |

운영에서 OOM 대응은 "죽지 않게 만들기"와 "죽더라도 덜 중요한 것부터 죽기"를 동시에 만족시켜야 한다.

## 꼬리질문

> Q: OOM killer는 왜 필요한가요?
> 핵심: 커널이 더 이상 메모리를 확보할 수 없을 때 시스템 전체 정지를 막기 위해서다.

> Q: cgroup OOM과 호스트 OOM의 차이는?
> 핵심: 전자는 제한된 그룹 안에서 죽고, 후자는 노드 전체 압박에서 희생자를 고른다.

> Q: 메모리 pressure가 있는데 아직 OOM이 안 났으면 괜찮은가요?
> 핵심: 아니다. reclaim과 swap 때문에 이미 latency 장애가 시작됐을 수 있다.

> Q: `oom_score_adj`만 조정하면 충분한가요?
> 핵심: 아니다. limit 설계, 워크로드 분리, 메모리 추적이 같이 가야 한다.

## 한 줄 정리

OOM은 메모리 부족의 끝단이고, 실무에서는 cgroup limit, pressure, swap, `oom_score_adj`를 함께 봐야 정확히 원인과 희생자를 판단할 수 있다.
