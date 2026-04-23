# 파일 디스크립터 기초

> 한 줄 요약: 파일 디스크립터는 OS가 열린 파일·소켓·파이프에 붙여주는 정수 번호이며, 유닉스 계열에서는 거의 모든 I/O 자원이 이 번호 하나로 다뤄진다.

**난이도: 🟢 Beginner**

관련 문서:

- [파일 디스크립터, 소켓, 시스템 콜 비용과 서버 영향](./file-descriptor-socket-syscall-cost-server-impact.md)
- [FD 고갈과 ulimit 진단](./fd-exhaustion-ulimit-diagnostics.md)
- [operating-system 카테고리 인덱스](./README.md)
- [TCP/UDP Basics](../network/tcp-udp-basics.md)

retrieval-anchor-keywords: 파일 디스크립터란, file descriptor basics, fd 뭐예요, 파일 디스크립터 기초, fd 번호, stdin stdout stderr 번호, open file table beginner, 파일 열기 흐름, fd leak 기초, file descriptor intro

## 핵심 개념

프로그램이 파일을 열거나 소켓을 만들면 OS는 그 자원을 **파일 디스크립터(file descriptor, fd)**라는 작은 정수로 돌려준다. 이후 `read()`, `write()`, `close()` 같은 시스템 콜을 할 때 이 숫자를 넘기면 OS가 실제 자원을 찾아 처리한다.

유닉스 철학 "모든 것은 파일이다"가 여기서 나온다. 일반 파일, 소켓, 파이프, 터미널이 모두 fd로 추상화된다.

## 한눈에 보기

프로세스가 시작할 때 자동으로 3개의 fd가 열린다.

| fd 번호 | 이름 | 역할 |
|---------|------|------|
| 0 | stdin | 표준 입력 (키보드 등) |
| 1 | stdout | 표준 출력 (터미널 등) |
| 2 | stderr | 표준 에러 출력 |

`open("data.txt")` 호출 → OS가 3번 fd 반환 → 이후 `read(3, ...)`, `close(3)`.

## 상세 분해

- **프로세스 fd 테이블**: 각 프로세스는 자신이 열어둔 fd 목록을 fd 테이블로 관리한다. fd 번호는 프로세스 안에서만 의미가 있다.
- **시스템 오픈 파일 테이블**: OS 전체가 공유하는 열린 파일 항목 테이블. 파일 오프셋과 접근 모드가 여기 저장된다.
- **아이노드(inode)**: 실제 파일 메타데이터(크기, 위치 등). 여러 fd가 같은 inode를 가리킬 수 있다.
- **fd 상속**: `fork()`로 자식 프로세스를 만들면 부모의 fd 테이블이 복사된다. 부모가 연 파일을 자식도 읽을 수 있다.
- **`close-on-exec`**: `exec()` 후 fd를 자동으로 닫는 플래그. 자식 프로세스가 부모의 fd를 불필요하게 물려받지 않도록 할 때 쓴다.

## 흔한 오해와 함정

- "파일을 닫지 않아도 프로그램이 끝나면 자동으로 닫힌다"는 사실이지만 위험한 습관이다. 서버처럼 오래 실행되는 프로세스에서 fd를 계속 열고 안 닫으면 **fd 고갈**이 발생해 새 파일이나 소켓을 못 연다.
- "소켓과 파일 fd는 다른 종류다"는 오해다. OS 레벨에서 소켓도 fd이다. `read(socketFd, ...)`, `write(socketFd, ...)` 가 동작하는 이유가 이것이다.
- "fd 번호가 크면 무언가 문제다"는 틀렸다. 낮은 번호가 먼저 채워지므로 fd 번호가 크다는 것은 많은 fd가 열려 있다는 신호일 수 있다. 모니터링 시 `/proc/<pid>/fd` 디렉터리에서 확인한다.

## 실무에서 쓰는 모습

Java에서 `new FileInputStream("file.txt")`를 호출하면 JVM 내부에서 `open()` 시스템 콜이 발생하고 fd가 하나 생긴다. `try-with-resources`가 중요한 이유는 `close()`를 자동으로 호출해 fd를 반환하기 때문이다.

서버에서 HTTP 요청 하나당 소켓 fd가 하나 만들어진다. 동시 연결이 많을수록 열린 fd가 많아진다. ulimit 설정이 낮으면 `Too many open files` 에러가 발생한다.

## 더 깊이 가려면

- [파일 디스크립터, 소켓, 시스템 콜 비용과 서버 영향](./file-descriptor-socket-syscall-cost-server-impact.md) — 시스템 콜 비용과 fd 최적화
- [FD 고갈과 ulimit 진단](./fd-exhaustion-ulimit-diagnostics.md) — 운영 환경 fd 고갈 대응
- [fork-exec와 copy-on-write](./fork-exec-copy-on-write-behavior.md) — fd 상속과 자식 프로세스

## 면접/시니어 질문 미리보기

1. "파일 디스크립터란 무엇이고 왜 중요한가요?"
   - 핵심 답: OS가 열린 I/O 자원에 붙이는 정수 번호. 프로세스가 I/O를 할 때 항상 fd를 통하기 때문에 fd 관리가 자원 관리의 핵심이다.
2. "fd leak이 무엇이고 어떻게 생기나요?"
   - 핵심 답: 파일이나 소켓을 열고 닫지 않아 fd가 계속 쌓이는 현상. 오래 실행되는 서버에서 `Too many open files` 오류를 유발한다.
3. "stdin, stdout, stderr의 fd 번호는 각각 몇 번인가요?"
   - 핵심 답: 0, 1, 2. 유닉스 관례로 고정되어 있다.

## 한 줄 정리

파일 디스크립터는 "파일·소켓·파이프 모두를 하나의 숫자로 다루는 유닉스의 통합 I/O 추상화"이며, fd를 제때 닫지 않으면 서버가 새 연결을 거부하게 된다.
