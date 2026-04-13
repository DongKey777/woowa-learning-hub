# 컨텍스트 스위칭, 데드락, Lock-free

> 한 줄 요약: 동시성 제어의 비용과 위험을 모르면 스레드를 늘릴수록 서버가 느려지는 역설을 설명할 수 없다

## 핵심 개념 (정의 + 존재 이유)

### 컨텍스트 스위칭

컨텍스트 스위칭은 **CPU가 현재 실행 중인 태스크의 상태를 저장하고, 다음 태스크의 상태를 복원하여 실행을 넘기는 과정**이다.

왜 필요한가: 하나의 CPU 코어는 한 번에 하나의 실행 흐름만 처리할 수 있다. 멀티태스킹을 구현하려면 태스크 간 전환이 불가피하다.

왜 비용이 드는가:
- **레지스터 저장/복원**: PC, SP, 범용 레지스터, FPU/SIMD 레지스터 등을 PCB(또는 TCB)에 저장하고 복원
- **TLB flush**: 프로세스 전환 시 TLB(Translation Lookaside Buffer) 무효화 발생. 스레드 전환은 같은 주소 공간이므로 TLB flush가 없다는 점이 핵심 차이
- **캐시 오염(cache pollution)**: 새 태스크의 데이터가 캐시에 없으므로 cold miss 발생. L1/L2 캐시가 warming up 되기까지 수백~수천 사이클 소요
- **커널 진입 비용**: 스케줄러는 커널 모드에서 동작하므로 user→kernel→user 전환 필요
- **파이프라인 flush**: CPU의 명령어 파이프라인이 비워지고 다시 채워져야 함

프로세스 vs 스레드 컨텍스트 스위칭 비용 차이:

| 항목 | 프로세스 전환 | 스레드 전환 (같은 프로세스) |
|------|-------------|--------------------------|
| 레지스터 저장/복원 | O | O |
| TLB flush | O (PCID 없으면) | X |
| 페이지 테이블 전환 | O | X |
| 캐시 오염 | 심함 | 상대적으로 적음 |
| 커널 진입 | O | O |

### 데드락 (Deadlock)

데드락은 **두 개 이상의 태스크가 서로의 자원 해제를 기다리며 영원히 진행하지 못하는 상태**다.

발생 조건 (Coffman 조건, 네 가지 모두 충족 시 발생):
1. **상호 배제 (Mutual Exclusion)**: 자원은 한 번에 하나만 사용
2. **점유 대기 (Hold and Wait)**: 자원을 보유한 채 다른 자원 요청
3. **비선점 (No Preemption)**: 강제로 자원을 빼앗을 수 없음
4. **순환 대기 (Circular Wait)**: 자원 대기 관계가 순환 형태

### Starvation vs Livelock

- **Starvation**: 특정 태스크가 자원을 계속 획득하지 못해 무한히 대기. 시스템은 돌아가지만 특정 작업만 굶는다
- **Livelock**: 서로 양보만 반복하면서 실제 진행이 없는 상태. 데드락과 달리 상태가 변하지만 유용한 작업은 없다

### Lock-free / Wait-free

- **Lock-free**: 최소 하나의 스레드는 유한 시간 내에 작업을 완료한다. 다른 스레드가 블로킹되거나 실패해도 전체 시스템은 진행한다
- **Wait-free**: 모든 스레드가 유한 시간 내에 작업을 완료한다. Lock-free보다 강한 보장
- **Obstruction-free**: 다른 스레드가 모두 멈추면 유한 시간 내 완료. 가장 약한 보장

핵심 도구: **CAS (Compare-And-Swap)** 원자적 연산. "현재 값이 기대값과 같으면 새 값으로 교체, 아니면 실패" 패턴으로 락 없이 동시 갱신을 처리한다.

---

## 깊이 들어가기 (내부 동작 원리)

### 컨텍스트 스위칭의 실제 흐름 (Linux 기준)

```
1. 타이머 인터럽트 또는 syscall로 커널 진입
2. 현재 태스크의 레지스터를 task_struct→thread에 저장
3. 스케줄러 호출 → pick_next_task()로 다음 태스크 선택
4. context_switch() 호출
   ├─ switch_mm(): 메모리 디스크립터 전환 (프로세스 전환 시)
   │   └─ CR3 레지스터 변경 → TLB flush (또는 PCID 활용)
   └─ switch_to(): 스택 포인터, IP 전환
5. 새 태스크의 레지스터 복원
6. 유저 모드 복귀
```

### CAS 루프의 내부 동작

```c
// 의사 코드: lock-free counter increment
do {
    old = counter;           // 현재 값 읽기
    new = old + 1;           // 새 값 계산
} while (!CAS(&counter, old, new));  // 기대값이 맞으면 교체, 아니면 재시도
```

CAS는 CPU 레벨에서 `CMPXCHG` (x86) 또는 `LL/SC` (ARM) 명령으로 구현된다. 캐시 라인 단위로 배타적 소유권을 확보하므로 경쟁이 심하면 캐시 라인 바운싱이 발생한다.

### ABA 문제

CAS의 고전적 함정이다:
1. 스레드 A가 값 `A`를 읽음
2. 스레드 B가 `A→B→A`로 변경
3. 스레드 A의 CAS가 성공 (값이 여전히 `A`이므로)

해결: 버전 카운터(tagged pointer), hazard pointer, epoch-based reclamation 등

---

## 실전 시나리오 (장애 사례, 버그 패턴)

### 시나리오 1: 스레드 풀 과다 설정으로 인한 성능 저하 🟡 Intermediate

Tomcat 스레드 풀을 200→800으로 늘렸더니 오히려 p99 latency가 3배 증가.

**원인**: 컨텍스트 스위칭 오버헤드 + L1/L2 캐시 thrashing. CPU 코어 수(8)보다 훨씬 많은 runnable 스레드가 경쟁하면서 실제 작업 시간보다 전환 비용이 더 커짐.

**진단**:
```bash
# 초당 컨텍스트 스위칭 횟수 확인
vmstat 1
# cs 컬럼이 수만~수십만이면 과도한 전환

# 프로세스별 voluntary/involuntary context switch
cat /proc/<pid>/status | grep ctxt
# voluntary_ctxt_switches: I/O 대기 등 자발적 전환
# nonvoluntary_ctxt_switches: 타임슬라이스 소진으로 강제 전환

# perf로 스케줄링 이벤트 추적
perf stat -e context-switches,cpu-migrations -p <pid> -- sleep 10
```

### 시나리오 2: 데드락으로 인한 서비스 행 🟡 Intermediate

두 개의 서비스가 각각 `계좌A→계좌B`, `계좌B→계좌A` 순서로 락을 잡으면서 교착.

**진단 (Java)**:
```bash
# 스레드 덤프로 데드락 확인
jstack <pid> | grep -A 20 "Found one Java-level deadlock"

# 또는 JMX로
jcmd <pid> Thread.print
```

**진단 (Linux)**:
```bash
# futex 대기 상태 확인
cat /proc/<pid>/status | grep State
# S (sleeping) 이 대부분이면 대기 상태

# strace로 futex 대기 확인
strace -e futex -p <tid>
# FUTEX_WAIT가 반복되면 락 경쟁 또는 데드락
```

### 시나리오 3: CAS 스핀으로 인한 CPU 100% 🔴 Advanced

Lock-free 큐를 도입했는데 높은 경쟁 상황에서 CAS retry가 폭주하여 CPU가 100%에 도달. throughput은 오히려 lock 기반보다 낮아짐.

**원인**: 스레드 수 > 코어 수 상황에서 CAS 실패 후 재시도하는 스레드가 다른 스레드의 타임슬라이스까지 소비.

---

## 코드로 보기 (동작하는 예시)

### Java에서 CAS 기반 AtomicInteger vs synchronized

```java
// Lock-free: AtomicInteger 내부는 CAS 루프
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();  // CAS 기반, 경쟁 낮으면 빠름

// Lock 기반: synchronized
synchronized(lock) {
    counter++;  // 모니터 진입/탈출 비용
}
```

### 데드락 재현과 해결

```java
// 데드락 발생 코드
Thread t1 = new Thread(() -> {
    synchronized(lockA) {
        Thread.sleep(100);
        synchronized(lockB) { /* work */ }
    }
});
Thread t2 = new Thread(() -> {
    synchronized(lockB) {
        Thread.sleep(100);
        synchronized(lockA) { /* work */ }
    }
});

// 해결: 락 순서 통일
// 항상 lockA → lockB 순서로 획득
```

### 컨텍스트 스위칭 측정

```bash
# perf로 컨텍스트 스위칭 비용 측정
perf bench sched messaging -g 20 -t -l 10000

# 결과 예시: Total time: 1.234 [sec]
# 스레드 수를 바꿔가며 비교하면 전환 비용 체감 가능

# /proc에서 프로세스별 전환 횟수 확인
grep ctxt /proc/self/status
```

---

## 트레이드오프 (대안 비교표)

### 동시성 제어 전략 비교

| 전략 | 장점 | 단점 | 적합한 상황 |
|------|------|------|-----------|
| Mutex/synchronized | 구현 단순, 이해 쉬움 | 데드락 위험, 대기 비용 | 경쟁 낮고 임계 구간 짧을 때 |
| ReadWriteLock | 읽기 병렬성 확보 | 쓰기 기아 가능, 복잡도 증가 | 읽기 >> 쓰기 비율 |
| Lock-free (CAS) | 데드락 불가, 낮은 경쟁에서 빠름 | ABA 문제, 높은 경쟁에서 CPU 낭비 | 짧은 연산, 낮은~중간 경쟁 |
| Wait-free | 모든 스레드 진행 보장 | 구현 극도로 복잡 | 실시간 시스템 |
| 스레드 격리 (ThreadLocal 등) | 동기화 불필요 | 메모리 사용 증가, 집계 비용 | 스레드별 독립 상태 |

### 컨텍스트 스위칭 회피 전략 비교

| 전략 | 설명 | 트레이드오프 |
|------|------|------------|
| 코루틴/가상 스레드 | 유저 스페이스 전환, 커널 개입 없음 | 선점 불가 (협력적), 블로킹 콜 주의 |
| 이벤트 루프 | 단일 스레드로 다중 I/O | CPU 바운드 작업 시 전체 블로킹 |
| 스레드 풀 크기 최적화 | 코어 수 기반 조절 | CPU 바운드 vs I/O 바운드에 따라 다름 |
| CPU affinity | 특정 코어에 고정 | 유연성 감소, NUMA 고려 필요 |

---

## 꼬리질문 (면접 질문 + 의도 + 핵심)

### 🟢 Basic

**Q. 컨텍스트 스위칭이 왜 비싼가요?**
- 의도: 단순 암기가 아니라 하드웨어 수준의 비용을 이해하는지
- 핵심: 레지스터 저장/복원, TLB flush, 캐시 cold miss, 파이프라인 flush. "캐시 오염"까지 언급하면 좋다

**Q. 데드락과 스타베이션의 차이는?**
- 의도: 두 개념을 혼동하지 않는지
- 핵심: 데드락은 모든 관련 태스크가 막힘 (시스템 수준), 스타베이션은 특정 태스크만 굶음 (개별 수준)

### 🟡 Intermediate

**Q. 프로세스 컨텍스트 스위칭과 스레드 컨텍스트 스위칭의 차이는?**
- 의도: 프로세스와 스레드의 메모리 구조 이해
- 핵심: 스레드 전환은 TLB flush와 페이지 테이블 전환이 없다. 같은 주소 공간을 공유하기 때문

**Q. 데드락을 예방하려면?**
- 의도: Coffman 조건을 알고 실무에서 어떻게 적용하는지
- 핵심: 락 순서 통일 (순환 대기 제거), tryLock + timeout (비선점 조건 완화), 락 범위 최소화

**Q. CAS가 항상 lock보다 빠른가요?**
- 의도: Lock-free의 한계를 아는지
- 핵심: 경쟁이 심하면 CAS retry 폭주로 CPU 낭비. 스레드 수 > 코어 수 + 높은 경쟁에서는 lock이 나을 수 있다

### 🔴 Advanced

**Q. Java의 Virtual Thread가 컨텍스트 스위칭 비용을 어떻게 줄이나요?**
- 의도: OS 스레드와 유저 레벨 스레드의 차이 이해
- 핵심: 커널 개입 없이 유저 스페이스에서 continuation을 전환. TLB flush 없음, 스택 크기도 작음

**Q. ABA 문제란 무엇이고 어떻게 해결하나요?**
- 의도: Lock-free 자료구조의 실제 구현 난이도 이해
- 핵심: CAS가 값만 비교하므로 중간에 변경되었다 돌아온 경우를 감지 못함. tagged pointer, hazard pointer로 해결

---

## 한 줄 정리

컨텍스트 스위칭은 멀티태스킹의 필수 비용이고, 데드락은 동시성의 구조적 위험이며, lock-free는 만능이 아니라 경쟁 수준에 따라 전략을 골라야 한다.
