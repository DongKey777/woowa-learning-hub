# NAT, Conntrack, Ephemeral Port Exhaustion

> 한 줄 요약: NAT 뒤에서 outbound 연결이 폭발하면 공인 IP의 포트와 conntrack entry가 먼저 바닥나고, 그 증상이 `timeout`, `EADDRNOTAVAIL`, `tail latency`로 드러난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](../operating-system/file-descriptor-socket-syscall-cost-server-impact.md)
> - [run queue, load average, CPU saturation](../operating-system/run-queue-load-average-cpu-saturation.md)
> - [Rate Limiter 설계](../system-design/rate-limiter-design.md)

retrieval-anchor-keywords: NAT gateway, SNAT, conntrack table, ephemeral port exhaustion, TIME_WAIT, file descriptor, tail latency, netfilter, source port reuse

## 핵심 개념

NAT(Network Address Translation)은 내부 주소를 외부 주소로 바꾸는 장치나 커널 기능이다. 실무에서는 대부분 **SNAT(Source NAT)** 를 뜻하고, outbound 트래픽의 source IP와 source port를 바꿔서 여러 내부 호스트가 하나의 공인 IP를 공유하게 만든다.

여기서 자주 같이 따라오는 자원이 있다.

- **ephemeral port**: 클라이언트가 outbound 연결에 임시로 쓰는 로컬 포트
- **conntrack entry**: 커널이 흐름 상태를 기억하기 위해 저장하는 연결 추적 정보
- **TIME_WAIT**: 연결 종료 뒤에도 일정 시간 포트를 붙잡아 두는 TCP 상태
- **file descriptor**: 애플리케이션이 socket을 다루는 프로세스 내부 핸들

이 문서는 [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)에서 말한 연결 재사용을 NAT/포트 관점으로 다시 보는 문서다. 또한 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)에서 말한 retry 폭주가 왜 포트 고갈을 더 빨리 만들고, [File Descriptor, Socket, Syscall Cost, and Server Impact](../operating-system/file-descriptor-socket-syscall-cost-server-impact.md)에서 말한 fd와 syscall 비용이 왜 같이 커지는지 연결해서 봐야 한다.

핵심은 간단하다.

- 연결 하나는 socket 1개, fd 1개, conntrack entry 1개 이상을 만든다.
- outbound 연결이 짧고 많아질수록 ephemeral port와 conntrack table이 빨리 소진된다.
- NAT gateway 뒤에서는 여러 서버가 같은 공인 IP의 포트 공간을 공유하므로 포트 충돌 가능성이 훨씬 커진다.
- 장애가 시작되면 retry가 트래픽을 더 키우고, blocked thread가 늘면서 [run queue, load average, CPU saturation](../operating-system/run-queue-load-average-cpu-saturation.md) 같은 현상으로도 번진다.

## 깊이 들어가기

### 1. NAT가 실제로 바꾸는 것

내부 서버가 `10.0.1.23:43124 -> 198.51.100.10:443` 으로 나간다고 하자. NAT 장치는 이를 바깥에서 보이는 주소로 바꾼다.

```text
before: 10.0.1.23:43124 -> 198.51.100.10:443
after : 203.0.113.8:52001 -> 198.51.100.10:443
```

이때 중요한 것은 NAT가 단순 치환이 아니라 **매핑 상태를 저장**한다는 점이다. 그래서 NAT 장치나 커널은 다음을 기억해야 한다.

- 내부 source IP/port
- 외부 destination IP/port
- 변환된 public IP/port
- TCP 상태와 timeout

즉, 포트는 숫자 하나가 아니라 **상태를 가진 자원**이 된다.

### 2. conntrack table은 왜 채워지는가

리눅스의 netfilter conntrack은 흐름별 상태를 저장한다. TCP 연결은 SYN, ESTABLISHED, FIN, TIME_WAIT 같은 상태 전이를 거치며, 각 흐름은 테이블 엔트리를 잡아 둔다.

문제가 되는 패턴은 대개 이렇다.

- 짧은 HTTP 요청마다 새 연결을 만든다.
- keep-alive가 꺼져 있거나 idle timeout이 너무 짧다.
- retry가 많아서 동일한 upstream으로 새 연결을 계속 시도한다.
- NAT 뒤에 여러 워커가 몰려 같은 공인 IP를 공유한다.

테이블이 한계에 도달하면 새 흐름이 등록되지 못하고, 증상은 다음처럼 보인다.

- SYN이 계속 재전송된다.
- `connect()`가 느려진다.
- `EADDRNOTAVAIL` 또는 `ETIMEDOUT` 이 난다.
- 커널 로그에 `nf_conntrack: table full, dropping packet` 류 메시지가 보인다.

### 3. ephemeral port exhaustion은 왜 생기는가

클라이언트는 outbound 연결을 만들 때 로컬 포트를 임시로 할당받는다. Linux에서는 보통 `ip_local_port_range` 로 범위를 정한다.

```text
예시 범위: 32768-60999
가용 포트 수: 대략 2만 후반개
```

이 숫자는 생각보다 작다. 특히 아래 조건이 겹치면 금방 부족해진다.

- 동일한 destination으로 대량 연결을 만든다.
- 짧은-lived connection을 반복한다.
- TIME_WAIT가 많이 쌓인다.
- NAT gateway 뒤에서 여러 호스트가 같은 공인 IP를 공유한다.

여기서 혼동하면 안 되는 점이 있다.

- "연결 수"가 많다고 해서 항상 포트가 고갈되는 것은 아니다.
- 하지만 **동시에 살아 있는 연결 수**와 **짧은 시간에 재사용하려는 포트 수**가 많아지면 고갈된다.
- 특히 같은 외부 대상으로 붙는 연결은 NAT 뒤에서 더 쉽게 충돌한다.

### 4. TIME_WAIT이 왜 포트를 잡아먹는가

TCP는 연결을 닫은 직후에도 잠시 상태를 유지한다. 이유는 늦게 도착한 패킷이 새 연결로 잘못 들어가는 것을 막기 위해서다.

즉, TIME_WAIT은 버그가 아니라 안전장치다.

하지만 운영 관점에서는 문제가 된다.

- 요청이 끝날 때마다 새 연결을 열면 TIME_WAIT이 많이 쌓인다.
- TIME_WAIT이 많으면 같은 포트를 바로 재사용하기 어렵다.
- 결과적으로 outbound 커넥션 churn이 심한 서비스는 tail latency가 급격히 나빠진다.

이 지점에서 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)의 retry 정책과 [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)의 연결 재사용 전략이 직접 연결된다.

### 5. 왜 tail latency가 먼저 망가지는가

포트나 conntrack이 100% 다 찬 순간에만 문제가 생기는 것은 아니다. 실제로는 일부 요청만 먼저 실패하고, 그 실패가 재시도와 대기열을 늘리면서 P95, P99가 먼저 무너진다.

흐름은 보통 이렇게 간다.

1. 새 연결 생성이 느려진다.
2. `connect()` 대기가 늘어난다.
3. retry가 추가 연결을 더 만든다.
4. worker thread가 대기 상태로 묶인다.
5. runnable task가 늘고, load average와 tail latency가 함께 오른다.

이 패턴은 네트워크 문제처럼 시작하지만, 결국은 자원 고갈과 스케줄링 문제로 번진다.

## 실전 시나리오

### 시나리오 1: NAT gateway 뒤에서 외부 API를 대량 호출한다

배치 작업이나 트래픽 피크가 오는 순간, 내부 여러 인스턴스가 같은 외부 API로 짧은 요청을 쏟아낸다. 각 요청이 새 연결을 만들면 NAT gateway는 공인 IP의 포트 공간과 conntrack 엔트리를 빠르게 소모한다.

이때 보이는 증상은 다음과 같다.

- 간헐적으로 `connect timed out`
- 일부 요청만 비정상적으로 느려짐
- `ss` 에 `TIME-WAIT` 가 급증
- `conntrack -S` 에 `insert_failed`, `drop` 류 카운터 증가

### 시나리오 2: Kubernetes 노드 SNAT가 병목이 된다

여러 Pod가 노드 IP로 SNAT되어 나가면, 실질적으로는 노드가 하나의 큰 출구가 된다. Pod 수가 늘고 각 Pod가 외부 연결을 많이 만들수록 노드의 ephemeral port와 conntrack 한계가 먼저 온다.

여기서는 네트워크만 보는 게 아니라 fd와 syscall 비용도 같이 봐야 한다. [File Descriptor, Socket, Syscall Cost, and Server Impact](../operating-system/file-descriptor-socket-syscall-cost-server-impact.md)에서 설명한 것처럼, 연결 수가 늘면 fd table과 커널 경계 통과 비용도 같이 커진다.

### 시나리오 3: retry storm이 장애를 증폭시킨다

상대 서비스가 느려졌는데 timeout이 길고 retry가 공격적이면, 실패한 요청이 같은 upstream으로 새 연결을 또 만든다. 이 순간부터는 단순 실패가 아니라 **자원 경쟁 장애**가 된다.

이 경우는 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)과 [Rate Limiter 설계](../system-design/rate-limiter-design.md)를 함께 봐야 한다. 요청 수를 제한하지 않으면 retry가 limiter를 우회하고, 결국 NAT와 conntrack까지 밀어 넣는다.

### 시나리오 4: 증상이 CPU 문제처럼 보인다

연결 대기가 길어지면 thread가 block되고, 재시도와 타임아웃 대기로 runnable queue가 길어진다. 그 결과 `top` 이나 `uptime` 에서 load average가 올라가고, 겉보기에는 CPU가 바쁜 것처럼 보일 수 있다.

하지만 실제 원인은 CPU 계산이 아니라 네트워크 자원 대기인 경우가 많다. 이럴 때는 [run queue, load average, CPU saturation](../operating-system/run-queue-load-average-cpu-saturation.md)와 함께 해석해야 한다.

## 코드로 보기

### 1. 현재 상태를 보는 명령

```bash
# 로컬 ephemeral port 범위
sysctl net.ipv4.ip_local_port_range

# conntrack 한도와 현재 사용량
sysctl net.netfilter.nf_conntrack_max
sysctl net.netfilter.nf_conntrack_count
sudo conntrack -S

# TIME_WAIT 개수와 전체 TCP 상태
ss -tan state time-wait | wc -l
ss -s

# netstat은 구식이지만 빠른 확인용으로 아직 유용하다
netstat -ant | awk '$6 == "TIME_WAIT" { c++ } END { print c + 0 }'

# conntrack 엔트리 일부 확인
sudo conntrack -L | head
```

### 2. 포트 고갈을 재현하는 간단한 예시

아래 예시는 같은 대상에 계속 새 TCP 연결을 열어 포트 소모를 관찰하는 실험용 코드다. 서버가 연결을 닫지 않고 유지해야 포트와 conntrack 상태가 누적되므로, 로컬에서 홀드용 서버를 먼저 띄운다.

```python
# terminal 1: connection holder
import socket

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", 18080))
srv.listen()

connections = []
while True:
    conn, _ = srv.accept()
    connections.append(conn)
    print(f"accepted: {len(connections)}")
```

```python
# terminal 2: client that keeps opening sockets
import socket
import time

HOST = "127.0.0.1"
PORT = 18080
sockets = []

for i in range(50000):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        sockets.append(s)
    except OSError as e:
        print(f"stopped at {i}: {e}")
        break

print(f"open sockets: {len(sockets)}")
time.sleep(60)
```

이 코드는 포트를 계속 점유하기 때문에 `connect()` 실패가 나거나 `TIME_WAIT` 가 쌓이는 과정을 보기 좋다. 운영 서버에서 돌리는 코드는 아니고, 포트와 연결 상태를 눈으로 확인하기 위한 실험용이다.

### 3. 모니터링을 한 번에 보는 루프

```bash
watch -n 1 '
  echo "TIME_WAIT: $(ss -tan state time-wait | wc -l)"
  echo "conntrack: $(sysctl -n net.netfilter.nf_conntrack_count 2>/dev/null || echo N/A)"
  echo "port_range: $(sysctl -n net.ipv4.ip_local_port_range)"
'
```

이렇게 보면 port range, TIME_WAIT, conntrack 사용량이 같이 움직이는지 빠르게 확인할 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| Keep-alive / connection pool 사용 | 연결 churn과 TIME_WAIT를 줄인다 | idle connection 관리가 필요하고 stale connection이 남을 수 있다 | 외부 API, DB, 내부 RPC처럼 재사용 가능한 경로 |
| ephemeral port range 확대 | 당장 버틸 수 있는 연결 수가 늘어난다 | 근본 원인을 못 고치면 결국 conntrack나 다른 자원으로 막힌다 | 단기 완화, 튜닝 여지 확인용 |
| egress IP를 더 늘린다 | 공인 IP당 포트 공간을 분산할 수 있다 | 비용과 운영 복잡도가 올라간다 | 대규모 outbound, NAT gateway 병목 |
| conntrack 한도와 timeout을 조정한다 | 테이블 포화와 엔트리 과잉을 완화한다 | 잘못 조정하면 메모리 사용량과 진단 난도가 올라간다 | 커널 튜닝이 가능한 운영 환경 |
| TIME_WAIT 축소나 공격적 port reuse를 시도한다 | 단기적으로 포트 회전율이 좋아 보인다 | TCP 안전성을 해치고 재전송/충돌 리스크를 키울 수 있다 | 실험 환경이나 매우 신중한 제한적 상황 |

정리하면, **재사용을 늘리고 churn을 줄이는 것**이 우선이고, 그 다음이 포트와 conntrack의 용량 확장이다. 숫자만 키우는 방식은 대부분 임시방편이다.

## 꼬리질문

> Q: conntrack table이 가득 찬 것과 ephemeral port exhaustion은 같은 문제인가요?
> 의도: 커널 상태 추적과 포트 자원 고갈을 구분하는지 확인한다.
> 핵심: 다르다. conntrack은 흐름 상태 저장소이고, ephemeral port exhaustion은 로컬 또는 NAT 변환 포트 공간 고갈이다. 다만 둘은 같이 터지는 경우가 많다.

> Q: TIME_WAIT이 왜 필요하고, 그냥 줄이면 안 되나요?
> 의도: TCP 종료 안정성과 재사용 위험을 이해하는지 본다.
> 핵심: TIME_WAIT은 늦게 도착한 패킷이 새 연결을 오염시키는 것을 막는다. 줄이면 포트는 빨리 돌지만 안전성과 예측 가능성이 떨어진다.

> Q: keep-alive를 쓰면 왜 port exhaustion이 줄어드나요?
> 의도: 연결 재사용이 포트 churn을 어떻게 낮추는지 보는 질문이다.
> 핵심: 새 TCP 연결 수가 줄어들면 ephemeral port와 conntrack entry 생성 속도가 함께 줄어든다.

> Q: retry가 왜 이 문제를 더 악화시키나요?
> 의도: 장애 증폭 메커니즘을 아는지 확인한다.
> 핵심: 실패한 요청이 새 연결을 다시 만들면서 포트와 conntrack 소비가 더 빨라진다. 그래서 timeout, backoff, jitter가 같이 필요하다.

> Q: 현장에서 무엇부터 확인하겠나요?
> 의도: 진단 순서와 도구 감각을 본다.
> 핵심: `ss -tan state time-wait`, `sysctl net.ipv4.ip_local_port_range`, `sysctl net.netfilter.nf_conntrack_count`, `sudo conntrack -S`, `dmesg | grep -i conntrack` 순으로 본다.

## 한 줄 정리

NAT 뒤에서 짧은 outbound 연결을 많이 만들면 ephemeral port와 conntrack가 먼저 병목이 되고, 그 결과는 보통 `timeout` 과 tail latency 상승으로 나타난다.
