# Thundering Herd, Accept, Wakeup

> 한 줄 요약: 여러 스레드나 프로세스가 같은 이벤트에 동시에 깨어나는 구조는 간단해 보여도, accept와 wakeup 비용을 폭증시켜 서버를 쉽게 흔든다.

## 핵심 개념

`thundering herd`는 하나의 이벤트에 너무 많은 대기자가 동시에 반응하는 현상이다. 서버에서는 주로 `accept()` 대기, `epoll` 대기, 락 경쟁, 조건 변수 wakeup에서 나타난다.

- `accept`: 리스닝 소켓에서 새 연결을 받아오는 동작이다.
- `wakeup`: 커널이 잠자던 스레드를 runnable 상태로 깨우는 일이다.
- `thundering herd`: 여러 워커가 한 번에 깨어나서 결국 하나만 유효한 일을 하고 나머지는 낭비되는 상황이다.

왜 중요한가:

- 트래픽이 몰릴 때 CPU가 실제 처리보다 wakeup과 경쟁에 쓰일 수 있다.
- accept 경합은 tail latency를 크게 흔든다.
- 멀티프로세스/멀티스레드 서버에서 "스케일 업"이 오히려 비효율이 될 수 있다.

## 깊이 들어가기

### 1. herd가 왜 문제인가

이벤트 기반 서버는 기다리는 주체가 많을수록 겉보기에 탄탄해 보인다. 하지만 같은 이벤트에 너무 많은 워커가 동시에 깨면 다음 비용이 생긴다.

- 캐시라인 경쟁
- mutex 또는 accept lock 경쟁
- wakeup 후 다시 sleep하는 낭비
- context switch 증가

결국 "일을 많이 하는 구조"가 아니라, **일이 생겼는지 확인하는 비용이 더 커지는 구조**가 된다.

### 2. `accept()`에서 herd가 생기는 이유

여러 프로세스나 스레드가 같은 리스닝 소켓에서 `accept()`를 기다릴 수 있다.

문제는 새 연결이 도착할 때다.

- 모두가 깨어난다
- 하나만 실제 연결을 가져간다
- 나머지는 실패하거나 다시 대기한다

이 구조는 연결이 적을 때는 별 문제 없어 보이지만, burst traffic에서 비효율이 급격히 커진다.

### 3. Linux에서의 전형적인 완화 방식

현대 Linux는 `accept` 경쟁을 완화하기 위한 여러 장치를 제공한다.

- `SO_REUSEPORT`: 여러 소켓이 포트를 나눠 받게 해 분산한다.
- `epoll` + 적절한 edge-triggered 처리: 불필요한 반복 wakeup을 줄인다.
- listen backlog 조정: 연결 폭주 시 손실을 줄인다.

핵심은 하나다. **모든 워커가 같은 큐를 함께 보는 구조를 피하는 것**이다.

### 4. wakeup은 왜 비싼가

wakeup은 단순히 flag를 바꾸는 것이 아니다.

- runnable queue에 넣어야 한다
- 스케줄러가 적절한 CPU를 고른다
- 캐시가 차갑기 때문에 다시 워밍업해야 한다

즉 자고 있던 스레드를 깨우는 건 공짜가 아니다. 특히 짧은 작업에서는 "깨어나는 비용"이 "일하는 비용"보다 커질 수 있다.

### 5. 운영에서 자주 놓치는 포인트

- 스레드 수를 늘리면 accept 처리량이 자동으로 늘어난다고 생각한다
- 부하 테스트가 균등 트래픽이라 herd 현상이 잘 안 보인다
- 프로덕션 burst는 특정 시간대에 몰리는데, 그때만 tail latency가 튄다

그래서 herd 문제는 평균보다 **분산과 꼬리 지연**을 봐야 드러난다.

## 실전 시나리오

### 시나리오 1: 배포 직후 짧은 시간 동안 5xx와 latency가 동시에 튄다

가능한 원인:

- 워커 다수가 동시에 떠서 같은 리스닝 소켓을 경합한다
- cold start로 캐시가 비어 있는데 accept와 초기 요청이 몰린다
- readiness가 너무 빨리 올라가 트래픽을 한꺼번에 받는다

대응:

- `SO_REUSEPORT` 또는 accept 분산 전략을 검토한다
- warm-up 이후에 트래픽을 받도록 readiness를 조정한다
- 배포 직후 트래픽 ramp-up을 둔다

### 시나리오 2: CPU는 충분한데 커넥션 수가 늘면 처리량이 오히려 출렁인다

가능한 원인:

- 여러 워커가 같은 이벤트에 wakeup된다
- accept lock이나 epoll ready queue 경쟁이 발생한다
- 불필요한 context switch가 늘어난다

대응:

- per-core accept 분산 구조를 검토한다
- shared listener를 줄인다
- lock contention과 scheduler run queue를 함께 본다

### 시나리오 3: 특정 피크 시간대에만 지연이 길어진다

가능한 원인:

- burst connection이 backlog를 압박한다
- 일부 워커에 wakeup이 집중된다
- TLS handshake나 초기 인증이 herd와 겹친다

대응:

- backlog와 worker 분산을 점검한다
- handshake 단계와 accept 이후 처리를 분리한다
- 부하 테스트를 burst 패턴으로 다시 만든다

## 코드로 보기

### 나쁜 예: 모든 워커가 같은 listen fd를 공유하고 경쟁하는 구조

```c
int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
bind(listen_fd, ...);
listen(listen_fd, 1024);

while (1) {
    int client_fd = accept(listen_fd, NULL, NULL);
    if (client_fd >= 0) {
        handle_client(client_fd);
    }
}
```

이 코드 자체가 틀렸다는 뜻은 아니다. 다만 여러 워커가 동일한 `listen_fd`를 두고 경쟁하면 herd가 생길 수 있다.

### 개선 방향 1: `SO_REUSEPORT`로 분산

```c
int fd = socket(AF_INET, SOCK_STREAM, 0);
int on = 1;
setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &on, sizeof(on));
bind(fd, ...);
listen(fd, 1024);
```

각 워커가 자신의 소켓을 가지면 accept 경쟁을 줄이기 쉽다.

### 개선 방향 2: 이벤트 루프에서 불필요한 wakeup 줄이기

```c
int epfd = epoll_create1(0);
struct epoll_event ev = {.events = EPOLLIN, .data.fd = listen_fd};
epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

for (;;) {
    struct epoll_event events[64];
    int n = epoll_wait(epfd, events, 64, -1);
    for (int i = 0; i < n; i++) {
        if (events[i].data.fd == listen_fd) {
            while (1) {
                int client_fd = accept4(listen_fd, NULL, NULL, SOCK_NONBLOCK);
                if (client_fd < 0) {
                    break;
                }
                // client_fd를 바로 등록
            }
        }
    }
}
```

핵심은 이벤트를 받았을 때 한 번에 충분히 처리하고, 불필요한 재깨움을 줄이는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 적합한 상황 |
|------|------|------|-------------|
| 공유 listen fd + 여러 워커 | 단순하다 | herd가 생기기 쉽다 | 작은 규모, 단순 구현 |
| `SO_REUSEPORT` | accept 분산에 유리하다 | 배치/운영 설계가 필요하다 | 고트래픽 서버 |
| 단일 acceptor + worker pool | 경합을 줄이기 쉽다 | acceptor가 병목이 될 수 있다 | 연결 패턴이 예측 가능할 때 |
| event loop 기반 수용 | wakeup을 줄이기 좋다 | 구현 난도가 있다 | 고동시성 네트워크 서버 |

실무에서는 "더 많은 워커"보다 "워커가 같은 이벤트를 얼마나 공유하는가"를 먼저 본다.

## 꼬리질문

> Q: thundering herd는 왜 accept에서 자주 언급되나요?
> 의도: listen socket 경쟁 구조를 이해하는지 확인
> 핵심: 새 연결 하나에 대기자들이 동시에 반응하면서 비효율이 생기기 쉽다.

> Q: wakeup 비용은 왜 체감되나요?
> 의도: 스케줄링과 캐시 재가열을 아는지 확인
> 핵심: runnable queue 진입, 스케줄러 선택, 캐시 미스가 누적된다.

> Q: `SO_REUSEPORT`는 herd를 완전히 없애나요?
> 의도: 완화와 해결을 구분하는지 확인
> 핵심: 경쟁을 분산해 줄 뿐, 전체 시스템 설계와 부하 패턴은 여전히 중요하다.

> Q: 왜 burst 트래픽에서 더 심해지나요?
> 의도: 평균과 꼬리 지연을 구분하는지 확인
> 핵심: 순간적으로 많은 워커가 같은 이벤트를 보게 되어 경쟁이 집중된다.

## 한 줄 정리

accept와 wakeup은 단순한 대기 해제가 아니라, 많은 워커를 동시에 흔들어 CPU와 지연을 낭비하게 만들 수 있는 병목 지점이다.
