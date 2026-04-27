# 세마포어와 모니터 기초

> 한 줄 요약: 세마포어는 카운터로 여러 스레드의 공유 자원 접근을 제어하고, 모니터는 그 복잡함을 숨겨 객체 단위로 안전한 동기화를 제공하는 고수준 추상화다.

**난이도: 🟢 Beginner**

관련 문서:

- [futex, mutex, semaphore, spinlock](./futex-mutex-semaphore-spinlock.md)
- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [operating-system 카테고리 인덱스](./README.md)
- [Java Thread Basics](../language/java/java-thread-basics.md)

retrieval-anchor-keywords: 세마포어란, 모니터란, semaphore basics, monitor basics, 세마포어 뮤텍스 차이, 세마포어 뭐예요, 모니터 뭐예요, wait notify 기초, counting semaphore beginner, java synchronized 기초, semaphore monitor basics basics, semaphore monitor basics beginner, semaphore monitor basics intro, operating system basics, beginner operating system

## 먼저 잡는 멘탈 모델

뮤텍스는 "딱 1명만 들어올 수 있는 화장실"이다. 세마포어는 "N명까지 들어올 수 있는 주차장"이다. 모니터는 "자바의 `synchronized` 블록처럼 언어가 제공하는 안전한 방"이다.

- **세마포어(Semaphore)**: 정수 카운터와 두 연산 `wait()`(카운터 감소, 0이면 블록)·`signal()`(카운터 증가, 대기 스레드 깨움)으로 동작한다. 카운터가 1이면 이진 세마포어(binary semaphore)로 뮤텍스처럼 쓸 수 있다.
- **모니터(Monitor)**: 공유 자원과 그것을 조작하는 메서드를 하나의 객체에 묶고, 한 번에 하나의 스레드만 메서드를 실행하도록 보장하는 동기화 구조. Java의 `synchronized`가 모니터를 기반으로 동작한다.

## 한눈에 보기

세마포어는 카운터로 동시 진입 수를 제어하고, 모니터는 조건 변수(`wait/notify`)로 스레드 간 협력을 구현한다.

세마포어(카운터 = 3)에서 4개 스레드가 경쟁하는 흐름:

```
세마포어 (카운터 = 3):
  스레드 A → wait() → 카운터: 2 → 진입
  스레드 B → wait() → 카운터: 1 → 진입
  스레드 C → wait() → 카운터: 0 → 진입
  스레드 D → wait() → 카운터: -1 → 블록(대기)
  스레드 A 종료 → signal() → 카운터: 0 → D 깨움
```

모니터는 Java `synchronized` 키워드가 대표적이다. 락 획득과 조건 대기를 하나의 객체로 묶는다.

```
모니터 (Java synchronized):
  synchronized void transfer() {
      // 한 번에 하나의 스레드만 실행
      wait()   // 조건 불만족 시 대기
      notify() // 조건 충족 시 대기 스레드 깨움
  }
```

두 개념의 핵심 차이:

| 구분 | 세마포어 | 모니터 |
|------|----------|--------|
| 접근 제어 | 카운터 기반 | 락 기반 |
| 조건 대기 | 별도 구현 필요 | wait/notify 내장 |
| 소유권 | 없음 | 락 보유 스레드가 소유 |

## 상세 분해

- **이진 세마포어 vs 뮤텍스**: 이진 세마포어는 아무 스레드나 `signal()` 호출 가능. 뮤텍스는 락을 건 스레드만 해제 가능. 소유권 개념의 유무가 차이다.
- **카운팅 세마포어**: DB 커넥션 풀(최대 10개 연결)처럼 자원 개수를 제한할 때 쓴다. 카운터를 10으로 초기화하면 최대 10개 스레드가 동시 접근 가능.
- **모니터의 조건 변수**: `wait()`는 락을 풀고 특정 조건이 될 때까지 대기. `notify()`/`notifyAll()`은 대기 중인 스레드를 깨운다. Java에서 `Object.wait()`, `Object.notify()`가 이 역할을 한다.
- **`notify` vs `notifyAll`**: `notify()`는 대기 중인 스레드 중 하나만 깨운다. `notifyAll()`은 전부 깨운다. 어느 스레드가 깨어나야 하는지 모를 때 `notifyAll()`이 더 안전하다.

## 흔한 오해와 함정

- "세마포어가 뮤텍스보다 항상 좋다"는 틀렸다. 소유권이 없는 세마포어는 한 스레드가 signal을 빠뜨려도 오류가 나지 않아 버그를 추적하기 어렵다.
- "`synchronized` 메서드 안에서 `wait()`를 호출하면 락이 유지된다"는 오해다. `wait()`는 호출 즉시 락을 반납하고 대기 상태에 들어간다. 깨어날 때 다시 락을 획득한다.
- "`notify()` 후 깨어난 스레드가 즉시 실행된다"는 틀렸다. 깨어난 스레드는 락을 다시 얻어야 하므로 다른 스레드가 먼저 실행될 수 있다.

## 실무에서 쓰는 모습

Java의 `BlockingQueue` 구현(예: `LinkedBlockingQueue`)은 내부에 `ReentrantLock` + 두 개의 `Condition`(notEmpty, notFull)을 사용해 모니터 패턴을 구현한다. 큐가 꽉 차면 `put()`이 `notFull.await()`로 대기하고, 빠지면 `notFull.signal()`로 깨운다.

DB 커넥션 풀도 카운팅 세마포어 패턴이다. 최대 연결 수를 초과하는 요청은 세마포어 `wait()`에서 블록된다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "동기화 원시 도구를 한 표로 비교"하려면: [futex, mutex, semaphore, spinlock](./futex-mutex-semaphore-spinlock.md)
> - "실서비스에서 락 대기 시간을 추적"하려면: [lock contention, futex wait, off-CPU 디버깅](./lock-contention-futex-offcpu-debugging.md)
> - "`wait/notify` 설계가 깨질 때 패턴"을 보려면: [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)

## 더 깊이 가려면

- [futex, mutex, semaphore, spinlock](./futex-mutex-semaphore-spinlock.md) — 커널 수준 동기화 원시 연산
- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md) — 데드락과 lock-free 설계
- [lock contention, futex wait, off-CPU 디버깅](./lock-contention-futex-offcpu-debugging.md) — 운영 환경 락 경합 진단

## 면접/시니어 질문 미리보기

1. "뮤텍스와 세마포어의 차이를 설명하세요."
   - 핵심 답: 뮤텍스는 소유권이 있어 락을 건 스레드만 해제 가능. 세마포어는 카운터 기반으로 소유권이 없고 여러 스레드의 동시 접근 수를 제한한다.
2. "Java `synchronized`와 모니터의 관계는 무엇인가요?"
   - 핵심 답: Java의 모든 객체는 모니터를 내장하고 있다. `synchronized` 블록/메서드는 그 모니터의 락을 획득·해제하는 문법적 설탕이다.
3. "`wait()`와 `sleep()`의 차이는 무엇인가요?"
   - 핵심 답: `sleep()`은 락을 유지한 채 잠든다. `wait()`는 락을 반납하고 잠든다. 모니터 안에서 다른 스레드가 자원을 쓰게 하려면 `wait()`가 필요하다.

## 한 줄 정리

세마포어는 숫자로 동시 접근 수를 제어하고, 모니터는 그 복잡한 카운터 조작을 객체 안에 숨겨 `wait/notify`만으로 안전한 동기화를 가능하게 한다.
