# Java 스레드와 동기화 기초

> 한 줄 요약: 스레드는 프로세스 안에서 독립적으로 실행되는 흐름이고, 여러 스레드가 같은 데이터를 동시에 쓸 때 synchronized로 한 번에 하나씩만 접근하도록 보호해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
- [Java 동시성 유틸리티](./java-concurrency-utilities.md)
- [language 카테고리 인덱스](../README.md)
- [컨텍스트 스위칭, 데드락, lock-free](../../operating-system/context-switching-deadlock-lockfree.md)

retrieval-anchor-keywords: java thread basics, 스레드 입문, thread runnable beginner, synchronized 기초, 멀티스레드 입문, java 동기화 기초, race condition beginner, thread start run 차이, 스레드 만드는 법, java volatile 입문, synchronized method beginner, 공유 자원 보호 방법

## 핵심 개념

프로세스(Process)는 실행 중인 프로그램 전체이고, 스레드(Thread)는 그 안에서 독립적으로 실행되는 작은 흐름이다. Java 프로그램은 `main` 스레드 하나에서 시작하고, `new Thread()`로 추가 스레드를 만들 수 있다.

입문자가 헷갈리는 지점은 두 스레드가 같은 변수를 동시에 읽고 쓸 때 발생하는 문제다. 이를 **경쟁 조건(race condition)**이라 부르며, `synchronized` 키워드로 한 번에 하나의 스레드만 접근하도록 막아야 한다.

## 한눈에 보기

```
Thread 생성 방법
┌── Thread 상속      class MyThread extends Thread { run() }
└── Runnable 구현   class Task implements Runnable { run() }
    └── 람다         new Thread(() -> doWork())

실행 순서
thread.start()  → JVM이 새 스레드 생성 → run() 호출
thread.run()    → 현재 스레드에서 run() 직접 호출 (새 스레드 없음)
```

## 상세 분해

### 스레드 생성과 시작

```java
// Runnable 방식 (권장)
Thread t = new Thread(() -> {
    System.out.println("새 스레드 실행: " + Thread.currentThread().getName());
});
t.start(); // 반드시 start()를 써야 새 스레드가 생성됨
```

`start()`는 JVM에 새 스레드를 만들어달라고 요청한다. `run()`을 직접 호출하면 현재 스레드에서 순차 실행되므로 병렬성이 없다.

### 경쟁 조건과 synchronized

```java
// 문제 있는 코드: 두 스레드가 동시에 count를 변경
int count = 0;
// 스레드 A: count++ → count 읽기 → 1 더하기 → 저장
// 스레드 B: count++ → (동시에) count 읽기 → 1 더하기 → 저장
// 결과가 2여야 하는데 1이 나올 수 있음

// synchronized로 보호
synchronized (this) {
    count++;
}
```

`synchronized` 블록 안에는 한 번에 하나의 스레드만 들어갈 수 있다. 나머지 스레드는 대기한다.

### volatile — 가시성 보장

```java
private volatile boolean running = true;

// 스레드 A: running = false 설정
// 스레드 B: while (running) { ... } — volatile 없으면 변경을 못 볼 수 있음
```

`volatile`은 한 스레드의 변경이 다른 스레드에게 즉시 보이도록 보장한다. 단, 복합 연산(`count++` 같은)의 원자성은 보장하지 않는다.

## 흔한 오해와 함정

**오해 1: `thread.run()`을 호출하면 병렬로 실행된다**
아니다. `run()`은 일반 메서드 호출이고 현재 스레드에서 실행된다. 새 스레드를 만들려면 반드시 `start()`를 써야 한다.

**오해 2: synchronized를 쓰면 성능이 너무 느려진다**
현대 JVM은 경쟁이 없는 경우 `synchronized`를 거의 비용 없이 처리한다. 처음에는 정확성이 먼저고, 성능 문제는 실측 후 최적화하는 편이 낫다.

**오해 3: volatile이 synchronized를 대체할 수 있다**
`volatile`은 가시성만 보장한다. `count++`처럼 읽기-수정-쓰기가 연속된 연산의 원자성은 보장하지 않는다. 원자성이 필요하면 `synchronized` 또는 `AtomicInteger`를 써야 한다.

## 실무에서 쓰는 모습

1. 백그라운드 작업을 별도 스레드로 분리할 때 `new Thread(task).start()`
2. 서버 환경에서는 직접 스레드를 만들지 않고 `ExecutorService`(스레드 풀)를 쓴다
3. Spring 서비스에서 `@Async`를 쓰면 Spring이 내부적으로 스레드 풀을 관리한다
4. 공유 카운터·플래그가 필요하면 `AtomicInteger`, `AtomicBoolean`을 먼저 고려한다

## 더 깊이 가려면

- JVM 메모리 모델과 happens-before: [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
- ExecutorService, Future, CompletableFuture: [Java 동시성 유틸리티](./java-concurrency-utilities.md)

## 면접/시니어 질문 미리보기

**Q. `start()`와 `run()`의 차이는?**
`start()`는 JVM에 새 스레드를 생성하고 그 스레드에서 `run()`을 호출한다. `run()`을 직접 호출하면 현재 스레드에서 실행되므로 병렬성이 없다.

**Q. synchronized 메서드와 synchronized 블록의 차이는?**
`synchronized` 메서드는 메서드 전체를 잠근다. `synchronized(lock)` 블록은 지정한 범위만 잠가서 잠금 범위를 최소화할 수 있다. 블록 방식이 더 세밀한 제어가 가능하다.

**Q. 데드락(Deadlock)이란?**
두 스레드가 각자 락을 잡고 서로 상대방의 락을 기다리는 상태다. 스레드 A는 락 1을 갖고 락 2를 기다리고, 스레드 B는 락 2를 갖고 락 1을 기다린다. 무한 대기가 된다.

## 한 줄 정리

스레드는 `start()`로 만들고, 공유 자원은 `synchronized`로 보호하며, 단순 플래그 가시성만 필요하면 `volatile`을 쓴다.
