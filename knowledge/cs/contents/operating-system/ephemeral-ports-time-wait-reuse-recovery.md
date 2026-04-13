# Ephemeral Ports, TIME_WAIT, Reuse Recovery

> 한 줄 요약: outbound 연결이 많으면 ephemeral port와 TIME_WAIT가 병목이 될 수 있고, port reuse는 편하지만 잘못 다루면 충돌과 유실 위험이 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [Socket Buffer Autotuning, Backpressure](./socket-buffer-autotuning-backpressure.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: ephemeral ports, TIME_WAIT, port exhaustion, ip_local_port_range, tcp_tw_reuse, SO_REUSEADDR, outbound connections, 4-tuple, reuse recovery

## 핵심 개념

클라이언트 역할이 많은 서버는 outbound connection을 많이 열 수 있다. 이때 각 연결은 4-tuple로 구분되며, 로컬 ephemeral port가 고갈되면 새 연결이 안 열린다.

- `ephemeral port`: 임시로 할당되는 로컬 포트다
- `TIME_WAIT`: 연결 종료 후 한동안 상태를 유지하는 구간이다
- `port exhaustion`: 사용 가능한 로컬 포트가 부족해지는 상태다
- `SO_REUSEADDR`: 동일 주소 재사용을 돕는 옵션이다

왜 중요한가:

- connection burst가 많으면 새 outbound 연결이 실패할 수 있다
- TIME_WAIT가 많으면 transient하게 포트 풀이 줄어든다
- 잘못된 reuse는 충돌과 잘못된 연결 재사용을 유발할 수 있다

이 문서는 [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)와 [Socket Buffer Autotuning, Backpressure](./socket-buffer-autotuning-backpressure.md)를 연결해, 연결 수명주기 전체를 본다.

## 깊이 들어가기

### 1. ephemeral port는 무한하지 않다

클라이언트는 outbound 연결마다 로컬 포트를 소비한다.

- 동시에 많은 연결을 열면 포트 풀이 줄어든다
- 연결 종료 후 TIME_WAIT 동안 바로 재사용되지 않을 수 있다
- 짧은 connection churn이 심하면 고갈이 빨라진다

### 2. TIME_WAIT는 버그가 아니라 안전장치다

TIME_WAIT는 늦게 도착하는 세그먼트가 새 연결을 망치지 않게 하려는 장치다.

- 종료 직후 바로 같은 4-tuple을 쓰지 않게 한다
- 포트 재사용을 신중하게 한다
- 안정성을 위해 일정 시간 기다린다

### 3. reuse는 편하지만 함부로 쓰면 안 된다

`SO_REUSEADDR`나 관련 옵션은 유용하지만, 단순히 "포트가 안 열릴 때 켜는 버튼"은 아니다.

- 서버 바인딩 안정성에 도움
- 운영환경에 따라 안전한 의미가 다르다
- 잘못 쓰면 의도치 않은 재사용 문제가 생긴다

### 4. ephemeral port 문제는 outbound가 많은 서버에서 잘 드러난다

- 프록시
- API gateway
- fan-out이 큰 백엔드
- health check나 metric exporter가 많은 서버

이런 경우는 CPU보다 연결 수명주기 자체가 병목일 수 있다.

## 실전 시나리오

### 시나리오 1: 외부 API 호출이 갑자기 실패한다

가능한 원인:

- ephemeral port가 부족하다
- TIME_WAIT가 많다
- NAT나 방화벽 상태와 충돌한다

진단:

```bash
cat /proc/sys/net/ipv4/ip_local_port_range
ss -ant state time-wait | wc -l
ss -ant | head
```

### 시나리오 2: 연결은 열리는데 간헐적으로 실패한다

가능한 원인:

- 포트 풀이 좁다
- connection churn이 높다
- 재시도 폭주가 겹친다

### 시나리오 3: 서버를 재시작했는데 이전 연결 흔적이 걸린다

가능한 원인:

- TIME_WAIT가 아직 남아 있다
- reuse 정책이 환경과 맞지 않는다
- 포트 재사용 시점이 너무 빠르다

## 코드로 보기

### ephemeral port 범위 확인

```bash
cat /proc/sys/net/ipv4/ip_local_port_range
```

### TIME_WAIT 관찰

```bash
ss -ant state time-wait | head
```

### 재사용 힌트 예시

```c
int on = 1;
setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on));
```

### 단순 모델

```text
many outbound connections
  -> local ports consumed
  -> TIME_WAIT holds ports
  -> new connects fail or stall
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 연결 재사용 | port pressure를 줄인다 | keep-alive 관리가 필요하다 | HTTP client, proxy |
| port range 확장 | 더 많은 포트를 수용한다 | 근본 churn 문제는 남는다 | fan-out 서버 |
| TIME_WAIT 관리 조정 | 포트 회복을 돕는다 | 안전성/호환성 이슈 | 특수 운영환경 |
| connection cap | 폭주를 막는다 | 유연성이 줄어든다 | 대형 outbound 서비스 |

## 꼬리질문

> Q: ephemeral port는 왜 고갈되나요?
> 핵심: outbound connection이 너무 많고 TIME_WAIT가 포트를 묶기 때문이다.

> Q: TIME_WAIT는 제거해도 되나요?
> 핵심: 아니다. 안전성을 위한 상태다.

> Q: 재사용 옵션은 항상 좋은가요?
> 핵심: 아니다. 환경과 트래픽 패턴을 같이 봐야 한다.

## 한 줄 정리

ephemeral port와 TIME_WAIT는 outbound 연결이 많은 서버의 숨은 병목이며, 연결 재사용과 포트 범위 조정은 안전장치와 함께 다뤄야 한다.
