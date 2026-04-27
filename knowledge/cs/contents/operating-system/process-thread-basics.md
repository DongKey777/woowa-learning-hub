# 프로세스와 스레드 기초

> 한 줄 요약: 프로세스는 독립된 메모리 공간과 자원을 가진 실행 단위이고, 스레드는 같은 프로세스 안에서 메모리를 공유하며 동시에 실행되는 더 가벼운 흐름이다.

**난이도: 🟢 Beginner**

관련 문서:

- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [Linux Process State, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
- [operating-system 카테고리 인덱스](./README.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)

retrieval-anchor-keywords: 프로세스 스레드 차이, process thread difference, 프로세스란 뭐예요, 스레드란 뭐예요, process beginner, thread beginner, 멀티스레드 기초, 프로세스 메모리 공간, 스레드 공유 메모리, process vs thread intro, process thread self check, 프로세스 스레드 자가 점검, 프로세스 스레드 다음 문서 추천, process thread branch question, 프로세스 스레드 분기 질문

## 먼저 잡는 멘탈 모델

- 프로세스는 "격리된 집", 스레드는 "같은 집 안의 작업자"로 보면 대부분의 차이가 한 번에 정리된다.
- 격리(프로세스)를 택하면 안전성이 올라가고, 공유(스레드)를 택하면 협업 속도는 올라가지만 동기화 부담이 생긴다.
- "무엇이 더 빠른가"보다 **무엇을 공유하고 어디까지 격리할지**가 먼저 결정돼야 한다.

## 핵심 개념

백엔드 코드를 짜다 보면 "스레드를 더 쓰면 빠를까?" 같은 질문이 생긴다. 그 전에 프로세스와 스레드가 무엇인지 정확히 알아야 한다.

- **프로세스(Process)**: 운영체제가 실행 중인 프로그램에 부여하는 독립 단위. 코드·힙·스택·파일 디스크립터 등 자원을 각자 갖는다. 두 프로세스는 메모리를 기본적으로 공유하지 않는다.
- **스레드(Thread)**: 프로세스 안에서 CPU 시간을 받는 실행 흐름. 같은 프로세스 안의 스레드끼리는 힙과 전역 변수를 공유하되, 스택과 레지스터는 따로 가진다.

혼동 포인트: "프로세스가 무거운 이유"는 자원 격리 때문이다. 자원 격리가 있어서 한 프로세스가 죽어도 다른 프로세스는 살아 있다.

## 한눈에 보기

| 항목 | 프로세스 | 스레드 |
|------|----------|--------|
| 메모리 공간 | 독립 | 프로세스 내 공유 |
| 생성 비용 | 높음 | 낮음 |
| 충돌 격리 | 강함 | 약함 (한 스레드 오류가 전체에 영향) |
| 통신 방법 | IPC (파이프, 소켓 등) | 공유 변수 직접 접근 |
| 컨텍스트 스위치 비용 | 상대적으로 큼 | 작음 |

## 아주 작은 예시: 주문 서버를 1프로세스 4스레드로 띄운다면

- 프로세스는 1개라서 힙(캐시, 커넥션 풀 등)을 스레드가 함께 쓴다.
- 요청 4개가 들어오면 스레드 4개가 병렬로 처리할 수 있다(코어 여유가 있다면).
- 대신 공유 객체를 동시에 바꾸면 race condition이 발생할 수 있어 락/동기화가 필요하다.

포인트: 스레드는 "빠른 협업"을 주고, 프로세스 분리는 "장애 격리"를 준다.

## 상세 분해

- **프로세스 주소 공간**: 코드(text), 데이터(전역 변수), 힙(동적 할당), 스택(함수 호출), OS가 관리하는 커널 영역으로 나뉜다.
- **스레드 스택**: 각 스레드는 자신만의 스택을 갖는다. 함수 호출 깊이가 깊으면 스택 오버플로가 나는 이유가 이것이다.
- **공유 힙의 위험**: 스레드가 힙을 공유하면 속도는 빠르지만, 여러 스레드가 같은 객체를 동시에 수정할 때 경쟁 조건(race condition)이 생긴다.
- **Java에서의 모습**: `new Thread(runnable).start()`는 JVM 내부에서 OS 스레드를 하나 만든다. 같은 JVM 프로세스 안의 스레드들은 힙을 공유한다.

## 흔한 오해와 함정

- "프로세스가 여러 개면 항상 더 빠르다"는 틀렸다. 프로세스 간 통신(IPC) 비용이 크다. CPU 코어 수, 작업 특성에 따라 달라진다.
- "스레드는 메모리를 전혀 안 쓴다"도 틀렸다. 스레드 스택은 기본 수백 KB를 차지한다. 스레드를 수천 개 만들면 메모리 압박이 생긴다.
- "멀티스레드면 무조건 동시에 실행된다"는 오해다. 코어가 1개라면 실제 동시 실행은 없고, 운영체제가 빠르게 번갈아 실행할 뿐이다.
- "프로세스 = 프로그램 파일"도 틀렸다. 프로그램은 디스크의 정적 파일이고, 프로세스는 실행 중인 인스턴스다.

## 다음으로 어디를 읽을까? (초심자 라우팅)

- 프로세스 상태 전이(`running`, `sleeping`, `zombie`)가 헷갈린다면: [Linux Process State, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
- 스레드가 왜 느려지는지(락 대기, 전환 비용)를 먼저 보고 싶다면: [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- 스레드 대신 이벤트 루프로 동시성을 다루는 길을 보고 싶다면: [I/O Models and Event Loop](./io-models-and-event-loop.md)

## 실무에서 쓰는 모습

가장 흔한 시나리오는 **웹 서버의 요청 처리**다. Tomcat 같은 서블릿 컨테이너는 하나의 JVM 프로세스 안에서 요청마다 스레드를 하나씩 배정한다. 스레드가 힙의 서비스 빈을 공유하기 때문에 빠르게 응답할 수 있지만, 스레드 안전성을 보장하지 않으면 공유 데이터가 꼬인다.

또 다른 시나리오는 **멀티프로세스 격리**다. Nginx는 마스터 프로세스가 워커 프로세스를 여러 개 띄운다. 워커 하나가 죽어도 다른 워커와 마스터는 살아 있다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "상태 전이(zombie/orphan)가 헷갈리면": [Linux Process State, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - "`fork/exec` 경계와 메모리 복사 감각"이 필요하면: [Fork, Exec, Copy-on-Write Behavior](./fork-exec-copy-on-write-behavior.md)
> - "실제 서버 프로세스 흐름을 한 번에" 보려면: [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)

## 더 깊이 가려면

- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md) — 스레드 전환 비용과 데드락
- [Linux Process State, Zombie, Orphan](./linux-process-state-zombie-orphan.md) — 프로세스 상태 전이
- [I/O Models and Event Loop](./io-models-and-event-loop.md) — 스레드 없이 동시성을 다루는 방식

## 면접/시니어 질문 미리보기

1. "프로세스와 스레드의 차이를 메모리 관점에서 설명하세요."
   - 핵심 답: 프로세스는 독립 주소 공간, 스레드는 프로세스 힙을 공유하되 스택과 레지스터는 독립.
2. "멀티스레드 프로그램에서 발생하는 공유 메모리 문제는 무엇인가요?"
   - 핵심 답: race condition. 여러 스레드가 동기화 없이 같은 변수를 읽고 쓰면 결과가 예측 불가능해진다.
3. "스레드를 늘리면 항상 처리량이 올라가나요?"
   - 핵심 답: 아니다. 코어 수 이상의 스레드는 컨텍스트 스위치 오버헤드를 증가시키고, I/O 대기가 병목이면 스레드 추가가 효과 없을 수 있다.

## Self-check (자가 점검 5문항)

아래 질문은 시험이 아니라, 지금 이해한 축을 말로 꺼내 보고 다음 문서를 고르기 위한 점검이다. 먼저 짧게 답해 보고, 막히면 바로 아래 `힌트`만 확인해 보자.

1. 프로세스와 스레드 중 누가 주소 공간을 독립적으로 갖는가?
   힌트: 주소 공간은 격리 단위인 프로세스 기준으로 나뉘고, 스레드는 그 안에서 실행 흐름만 여러 개다.
2. 같은 프로세스 안에서 스레드들이 공유하는 것과 공유하지 않는 것을 각각 말할 수 있는가?
   힌트: heap, code, fd는 주로 공유하고, stack과 레지스터 문맥은 스레드마다 따로 가진다고 떠올리면 된다.
3. "스레드를 늘리면 항상 빨라진다"가 왜 틀렸는지 한 문장으로 설명할 수 있는가?
   힌트: CPU 경쟁, 락 경합, 컨텍스트 스위치 비용이 늘면 스레드 수 증가는 오히려 손해가 될 수 있다.
4. 지금 내 고민이 "상태 전이", "락/전환", "이벤트 루프" 중 어디에 가까운지 구분하고 다음 문서를 고를 수 있는가?
   힌트: "느린 이유가 상태 변화인지, 경쟁인지, I/O 대기인지" 먼저 분류하면 다음 문서 선택이 쉬워진다.
5. "새 프로세스를 만든다"와 "같은 프로세스 안에서 실행 흐름을 늘린다"를 들었을 때, 어느 쪽이 프로세스 branch이고 어느 쪽이 스레드 branch인지 바로 나눌 수 있는가?
   힌트: 주소 공간을 새로 나누면 프로세스 쪽이고, 같은 힙을 공유한 채 실행 주체만 늘리면 스레드 쪽이다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`프로세스 상태`는 실제로 어떻게 바뀌지?`"가 궁금하면: [Linux Process State, Zombie, Orphan](./linux-process-state-zombie-orphan.md)
> - "`스레드를 늘렸는데 왜 오히려 느려지지?`"가 궁금하면: [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
> - "`스레드 대신 event loop로 가는 길은 뭐지?`"가 궁금하면: [I/O Models and Event Loop](./io-models-and-event-loop.md)
> - "`fork()`, `exec()`, `waitpid()`는 한 흐름에서 어떻게 이어지지?`"가 궁금하면: [Process Lifecycle and IPC Basics](./process-lifecycle-and-ipc-basics.md)
> - "`다른 operating-system primer는 어디서 다시 고르지?`"가 궁금하면: [Operating System README - 입문 primer](./README.md#입문-primer)

## 한 줄 정리

프로세스는 격리된 자원 경계이고, 스레드는 그 안에서 자원을 공유하며 CPU를 받는 실행 단위라는 것을 기억하면 모든 멀티스레딩 논의의 출발점이 된다.
