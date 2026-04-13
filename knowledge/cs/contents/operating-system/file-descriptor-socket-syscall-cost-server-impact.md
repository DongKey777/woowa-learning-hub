# File Descriptor, Socket, Syscall Cost, and Server Impact

서버 성능을 볼 때 네트워크나 디스크만 보아서는 부족하다. 실제로는 file descriptor, socket, syscall 경계, 그리고 커널이 사용자 공간과 오가는 비용이 함께 작동한다. 이 문서는 fd와 socket의 개념부터, syscall 비용이 서버 지연과 처리량에 어떤 영향을 주는지까지 연결해서 정리한다.

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 중요한가](#왜-이-주제가-중요한가)
- [File descriptor란 무엇인가](#file-descriptor란-무엇인가)
- [Socket은 왜 특별한가](#socket은-왜-특별한가)
- [Syscall 비용이 생기는 이유](#syscall-비용이-생기는-이유)
- [서버에 미치는 영향](#서버에-미치는-영향)
- [실무에서 보는 병목 패턴](#실무에서-보는-병목-패턴)
- [시니어 질문](#시니어-질문)

</details>

## 왜 이 주제가 중요한가

서버는 결국 파일과 네트워크를 다룬다. 이 둘은 모두 커널 자원을 통해 접근되고, 대부분의 작업은 syscall을 통과한다.

문제는 syscall 자체가 단순 함수 호출이 아니라는 점이다. 요청 수가 많아질수록 syscall 횟수, 커널 진입 비용, 사용자 공간과 커널 공간 사이의 데이터 복사, 잠금 경쟁이 누적된다.

그래서 서버 성능을 볼 때는 "네트워크가 느리다"보다 먼저 다음을 물어야 한다.

- 요청당 syscall이 몇 번 발생하는가
- fd 수가 얼마나 늘어나는가
- blocking 지점이 어디인가
- 커널 경계에서 얼마나 오래 머무는가

## File descriptor란 무엇인가

File descriptor는 프로세스가 열린 자원을 가리키는 정수 핸들이다.

핵심은 fd가 단순히 파일만 의미하지 않는다는 점이다.

- 일반 파일
- socket
- pipe
- device

모두 fd로 다룰 수 있다. 즉 `open()`의 결과는 디스크 파일을 가리키는 숫자일 뿐 아니라, 커널이 관리하는 열린 객체에 대한 참조다.

### 왜 정수인가

- 프로세스별로 관리하기 쉽다
- 인자 전달이 단순하다
- 커널 내부 객체를 간접 참조할 수 있다

### fd에서 자주 놓치는 점

- `close()`를 하지 않으면 자원이 누수된다
- fd는 프로세스가 fork되면 복제될 수 있다
- 숫자가 같아도 다른 프로세스의 fd는 다른 객체를 가리킬 수 있다

## Socket은 왜 특별한가

Socket은 네트워크 통신을 위한 커널 객체다. 파일처럼 fd로 다루지만, 실제로는 네트워크 스택과 연결되어 있다.

서버에서 중요한 이유는 다음과 같다.

- 연결 하나마다 상태가 생긴다
- recv/send가 버퍼 상태에 따라 blocking될 수 있다
- accept backlog, send buffer, receive buffer 같은 커널 버퍼가 병목이 될 수 있다

즉 socket은 "연결"을 추상화하지만, 뒤에서는 메모리와 커널 큐를 소비한다.

### 서버에서 socket이 늘어날 때

- fd table이 커진다
- 연결 상태를 위한 메모리가 증가한다
- 스케줄링과 wakeup 비용이 누적된다
- epoll 같은 메커니즘이 없으면 polling 비용이 커진다

## Syscall 비용이 생기는 이유

syscall은 user mode에서 kernel mode로 넘어가는 작업이다. 이때 다음 비용이 발생한다.

- 권한 전환 비용
- 인자 검증 비용
- 커널 자료구조 탐색 비용
- 사용자 버퍼와 커널 버퍼 사이의 복사 비용
- blocking 시 스케줄링 비용

모든 syscall이 context switch를 유발하는 것은 아니지만, blocking syscall은 다른 runnable task로 넘겨야 하므로 간접적으로 context switch를 만들 수 있다.

### 같은 일을 하더라도 왜 차이가 나는가

- 작은 `read()`를 여러 번 호출하면 syscall 횟수가 늘어난다
- 큰 버퍼로 한 번에 읽으면 syscall 횟수를 줄일 수 있다
- `write()`도 마찬가지로 batching이 중요하다

즉 syscalls는 "기능 호출"이 아니라 "커널 경계 통과"이므로 횟수 자체가 비용이다.

## 서버에 미치는 영향

syscall 비용은 요청 처리량과 tail latency에 직접 영향을 준다.

### 처리량 측면

- 요청당 syscall이 많으면 초당 처리 가능한 요청 수가 줄어든다
- 작은 I/O를 자주 하면 CPU가 실제 비즈니스 로직보다 커널 작업에 더 많이 쓰인다
- 연결 수가 많을수록 accept, epoll, recv, send의 관리 비용이 커진다

### 지연 시간 측면

- blocking syscall이 길어지면 워커 스레드가 묶인다
- 같은 워커 수에서 동시 처리 가능한 요청 수가 줄어든다
- 커널 버퍼가 꽉 차면 backpressure가 발생한다

서버가 느려지는 이유를 네트워크 대역폭만으로 설명하면 부족하다. 실제 병목은 syscall 빈도, buffer copy, sleep/wakeup, fd 관리 비용에서 나올 수 있다.

## 실무에서 보는 병목 패턴

### 1. 작은 요청을 너무 자주 보낸다

- 로그를 한 줄씩 write 한다
- 네트워크 패킷을 너무 잘게 쪼갠다
- DB나 외부 API를 반복적으로 호출한다

이 경우 batching이 필요하다.

### 2. fd를 많이 열어 둔다

- 연결 관리가 부실하다
- close 누락이 있다
- keep-alive가 지나치게 길다

fd가 많아지면 단순 메모리뿐 아니라 poll/epoll 관리 비용도 늘어난다.

### 3. blocking I/O에 워커를 묶는다

- thread-per-request 구조에서 느린 I/O가 스레드를 오래 잡는다
- CPU는 놀고 있는데 응답은 밀린다

이때는 non-blocking I/O, event loop, backpressure 제어가 필요하다.

### 4. 커널 복사가 병목이 된다

- 큰 payload를 자주 주고받는다
- user-space와 kernel-space 사이 copy가 누적된다

이 경우 zero-copy 계열 접근이나 데이터 흐름 재설계가 필요할 수 있다.

## 시니어 질문

- file descriptor는 왜 정수로 표현하는가?
- socket과 일반 파일 fd의 공통점과 차이는 무엇인가?
- syscall이 왜 비싼가?
- 모든 syscall이 context switch를 유발하는가?
- fd가 많아질수록 서버는 왜 느려질 수 있는가?
- blocking I/O와 event loop 모델은 syscall 비용을 어떻게 다르게 다루는가?
- batching은 왜 서버 성능을 바꾸는가?
