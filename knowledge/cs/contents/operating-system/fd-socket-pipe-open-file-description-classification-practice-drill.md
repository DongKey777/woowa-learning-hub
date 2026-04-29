# FD, Socket, Pipe, Open File Description 분류 연습

> 한 줄 요약: backend 예시를 볼 때 `fd는 번호`, `socket/pipe는 자원 종류`, `open file description은 커널이 들고 있는 열린 상태`라는 세 축으로 다시 분류해 보는 practice drill이다.
>
> 문서 역할: 이 문서는 [파일 디스크립터 기초](./file-descriptor-basics.md) 바로 다음에 붙는 sibling practice drill로, `socket도 fd인가요?`, `pipe도 fd인가요?`, `dup()` 뒤에 뭐가 공유되나요?` 같은 beginner/junior 혼동을 짧은 장면 분류로 정리한다.

**난이도: 🟡 Intermediate**

관련 문서:

- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
- [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [operating-system 카테고리 인덱스](./README.md)
- [TCP/UDP Basics](../network/tcp-udp-basics.md)

retrieval-anchor-keywords: fd socket pipe open file description practice, fd vs socket practice, socket vs pipe 헷갈림, open file description 뭐예요, fd 분류 연습, backend fd socket pipe basics, dup fork shared offset practice, 처음 fd socket 구분, what is open file description, file descriptor socket pipe classification, pipe 도 fd인가요, socket 도 fd인가요

## 핵심 개념

이 주제가 꼬이는 이유는 서로 다른 층의 말을 한 문장에 같이 쓰기 때문이다.

- `fd`는 프로세스가 들고 있는 **번호**
- `socket`, `pipe`는 fd가 가리킬 수 있는 **자원 종류**
- `open file description`은 커널 쪽에 있는 **열린 상태 묶음**이다

예를 들어 "`fd 4`가 소켓이다"라는 말은 완전히 틀린 문장이 아니라, `4`는 번호이고 그 번호가 가리키는 자원이 socket이라는 뜻으로 풀어 읽어야 한다.

번호표 비유는 입문에는 도움이 되지만 끝까지 같지는 않다. `open file description`은 단순 번호표 뒤의 "실제 파일"이 아니라, offset과 상태 플래그까지 포함한 커널의 열린 상태라는 점에서 비유보다 더 넓다.

## 한눈에 보기

| 용어 | 먼저 답하는 질문 | 초보자용 한 줄 감각 | 자주 같이 나오는 말 |
| --- | --- | --- | --- |
| file descriptor | "프로세스가 지금 무엇으로 접근하나?" | 자원을 가리키는 정수 번호 | `fd 3`, `stdin`, `dup2` |
| socket | "네트워크/유닉스 소켓 자원인가?" | 연결과 송수신을 위한 끝점 | `listen`, `accept`, `connect` |
| pipe | "프로세스 사이 바이트 통로인가?" | 한쪽이 쓰고 다른 쪽이 읽는 연결선 | `stdout pipe`, `EOF`, `broken pipe` |
| open file description | "여러 fd가 무엇을 함께 공유하나?" | 커널의 열린 상태 묶음 | `shared offset`, `O_NONBLOCK`, `fork`, `dup` |

짧게 외우면 이렇다.

- 숫자를 말하면 먼저 `fd`
- 자원 종류를 말하면 `socket` 또는 `pipe`
- `dup()` 뒤 공유, offset, 상태 플래그를 말하면 `open file description`

## 분류 순서

헷갈릴 때는 아래 세 질문을 순서대로 던지면 된다.

1. 지금 말하는 것이 **정수 번호**인가?
   - 그렇다면 우선 `fd` 축이다.
2. 지금 말하는 것이 **열린 자원 종류**인가?
   - 네트워크 연결이면 보통 `socket`, 프로세스 사이 스트림이면 보통 `pipe`다.
3. 지금 말하는 것이 **여러 fd가 공유하는 커널 상태**인가?
   - 그렇다면 `open file description` 축이다.

한 장면 안에 답이 두 개 이상 나오는 것은 이상한 일이 아니다. 예를 들어 "부모가 child stdout을 읽기 위해 pipe를 만들고 read end를 fd 5로 받았다"는 문장은 `pipe`와 `fd`가 같이 들어 있다.

## 분류 연습

먼저 직접 분류해 보고, 오른쪽 해설을 확인해 보자.

| 예시 | 먼저 분류해 보기 | 해설 |
| --- | --- | --- |
| 서버 로그에 `fd 7`이 `write()` 실패로 보인다 | `fd` | 지금 중심은 "몇 번 번호로 접근했는가"다. 자원 종류는 아직 모른다. |
| `accept()` 결과로 새 연결 하나를 받았다 | `socket` + `fd` | 받은 것은 네트워크 socket 자원이고, 프로세스는 그 자원에 fd 번호를 붙여 다룬다. |
| `cmd1 | cmd2`에서 두 프로세스 사이 stdout이 이어진다 | `pipe` + `fd` | 연결선의 종류는 pipe이고, 각 프로세스는 read end / write end를 fd로 들고 있다. |
| `dup(stdout_fd)` 뒤 stdout과 같은 파일 위치가 같이 움직인다 | `open file description` | 핵심은 "새 번호를 만들었는데 왜 offset이 공유되나"이므로 커널의 열린 상태 축을 봐야 한다. |
| `socketpair()`로 parent-child control 채널을 만든다 | `socket` + `fd` | local IPC라도 primitive 자체는 socket이다. 각 끝점은 fd로 들고 다닌다. |
| `fork()` 뒤 parent가 `O_NONBLOCK`를 바꾸자 child도 영향을 받는다 | `open file description` | 번호 복사 자체보다 공유된 열린 상태가 핵심이다. |
| `lsof`에서 `FIFO`가 보이고 child가 종료돼도 EOF가 안 온다 | `pipe` | 여기서는 pipe end를 누가 아직 들고 있나가 먼저다. fd 번호보다 lifecycle 해석이 중요하다. |
| `lsof`에서 `IPv4` `*:8080 (LISTEN)`이 보인다 | `socket` | listener socket을 열고 있다는 뜻이다. 실제 접근은 fd로 하지만, 첫 분류는 socket이 맞다. |

### 미니 체크: 같은 장면을 두 축으로 말하기

- "`fd 3`은 socket이다"를 더 정확히 풀면: `fd 3`이라는 번호가 `socket` 자원을 가리킨다.
- "`pipe가 안 닫혀서 EOF가 안 온다"를 운영체제 말로 풀면: 어떤 프로세스가 그 `pipe`의 write end `fd`를 아직 닫지 않았다.
- "`dup()` 후 같이 움직인다"를 더 정확히 풀면: 서로 다른 `fd`가 같은 `open file description`을 공유한다.

## 흔한 오해와 함정

- "`socket`과 `fd`는 경쟁 개념이다"는 오해가 가장 흔하다. 보통은 경쟁이 아니라 서로 다른 축이다.
- "`pipe`는 fd가 아니다"도 틀리다. pipe endpoint 역시 fd로 접근한다.
- "`open file description`은 파일일 때만 있다"처럼 외우면 좁다. 열린 상태와 공유 semantics를 설명하는 커널 층 개념으로 이해하는 편이 안전하다.
- "`dup()`은 새로 open한 것이다"도 틀리다. 보통은 새 번호를 만들 뿐, 같은 열린 상태를 계속 본다.
- "`socketpair()`는 pipe와 완전히 같은 것`"도 과하다. 둘 다 fd로 다루지만, 보통 pipe는 단방향 스트림 감각, socketpair는 양방향 채널 감각이 더 자연스럽다.

## 실무에서 쓰는 모습

Spring Boot 서버 하나를 떠올리면 구분이 빨라진다.

- 클라이언트 연결을 받는 `8080` listener는 `socket`
- JVM은 그 listener를 어떤 `fd` 번호로 들고 있다
- 요청 처리 중 다른 프로세스의 stdout을 붙이면 그 연결은 `pipe`
- 로깅 리다이렉션에서 `dup2()`를 쓰면 어떤 fd들이 같은 `open file description`을 공유하는지가 중요해진다

즉 backend 장면을 읽을 때 "`무슨 자원인가`"와 "`프로세스가 무슨 번호로 잡고 있나`"와 "`공유된 커널 상태가 있나`"를 따로 보면 디버깅 문장이 훨씬 덜 섞인다.

## 더 깊이 가려면

- [파일 디스크립터 기초](./file-descriptor-basics.md) — `fd는 번호표`라는 첫 축을 다시 고정
- [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md) — `pipe`, `socketpair`, shared memory 같은 IPC 선택 감각을 넓힘
- [Open File Description, dup, fork, Shared Offsets](./open-file-description-dup-fork-shared-offsets.md) — 오늘 연습에서 가장 헷갈리는 공유 semantics를 정확히 파고듦
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md) — child에 어떤 fd만 남겨야 하는지 실전 패턴으로 연결
- [TCP/UDP Basics](../network/tcp-udp-basics.md) — socket이 네트워크 계층에서 어떤 역할을 하는지 다른 카테고리에서 이어서 확인

## Self-check (자가 점검 4문항)

시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다.

1. "`fd 9가 pipe다`"라는 문장을 두 축으로 나눠 다시 설명할 수 있는가?
힌트: `9`는 번호, `pipe`는 자원 종류다.
2. `dup()` 뒤 파일 위치가 같이 움직이는 이유를 `socket`이나 `pipe`가 아니라 다른 축의 말로 설명할 수 있는가?
힌트: 공유되는 것은 보통 커널의 열린 상태다.
3. subprocess hang에서 "EOF가 안 온다"는 말을 들었을 때 지금 먼저 봐야 할 것이 `fd 개수`인지 `pipe end lifecycle`인지 구분할 수 있는가?
힌트: 이 경우는 resource type과 누가 아직 write end를 들고 있는지가 더 중요하다.
4. listener `socket`과 accepted client `socket`이 모두 fd로 보인다고 해서 같은 장면을 같은 층으로만 설명하면 왜 부족한가?
힌트: 둘 다 fd로 접근하지만, 자원 종류와 역할은 `listen`과 `connected socket`으로 다르다.

## 한 줄 정리

backend 예시를 읽을 때 `fd는 번호`, `socket/pipe는 자원 종류`, `open file description은 공유되는 커널 상태`라고 축을 나누면 용어가 훨씬 덜 섞인다.
