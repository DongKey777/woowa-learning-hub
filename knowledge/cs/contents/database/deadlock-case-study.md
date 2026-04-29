# Deadlock Case Study

**난이도: 🔴 Advanced**

> 데드락을 개념 정의가 아니라 실제 발생 원인과 대응 전략으로 보는 문서

관련 문서: [Deadlock vs Lock Wait Timeout 입문 프라이머](./deadlock-vs-lock-wait-timeout-primer.md), [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md), [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Transaction Timeout vs Lock Timeout](./transaction-timeout-vs-lock-timeout.md), [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
retrieval-anchor-keywords: deadlock case study, deadlock lock timeout difference, deadlock beginner bridge, deadlock 처음 읽기, deadlock case study 어디서부터, lock ordering, mysql deadlock log 보고 lock ordering 어떻게 고쳐, mysql deadlock log lock ordering 고치는 법, mysql deadlock log, mysql deadlock log lock ordering fix, deadlock log 보고 lock ordering 고치는 법, mysql deadlock 고치는 법, deadlock retry, lock wait, wait graph, backend db incident, transaction deadlock, circular wait, innodb deadlock log, retryable database error, booking deadlock, multi-day booking deadlock, guard row canonical order

<details>
<summary>Table of Contents</summary>

- [먼저 이 문서를 어떻게 읽으면 좋은가](#먼저-이-문서를-어떻게-읽으면-좋은가)
- [왜 중요한가](#왜-중요한가)
- [데드락이 생기는 이유](#데드락이-생기는-이유)
- [대표 사례](#대표-사례)
- [탐지와 해소](#탐지와-해소)
- [예방 전략](#예방-전략)
- [실무 체크리스트](#실무-체크리스트)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

## 먼저 이 문서를 어떻게 읽으면 좋은가

이 문서는 Advanced 문서지만, 데드락을 처음 incident 관점으로 읽는 학습자도 진입할 수 있게 짧은 브리지를 둔다.

- 먼저 `deadlock`을 "서로가 서로의 락을 기다리는 원형 대기"로만 잡는다.
- 다음으로 "`lock wait timeout`과 같은 말인가?"를 분리한다.
- 그 다음에야 아래 사례에서 **어떤 순서로 락을 잡았는지** 본다.

즉 이 문서의 초반 목표는 "왜 실패했나"를 완벽히 증명하는 것이 아니라, **deadlock인지 timeout인지 먼저 말로 구분할 수 있게 만드는 것**이다.

비유하자면 `lock wait timeout`은 줄이 길어서 이번 차례를 놓친 상황에 가깝고, `deadlock`은 두 줄이 서로 교차해서 아무도 앞으로 못 가는 상황에 가깝다. 다만 실제 DB는 단순 줄서기보다 복잡해서, 최종 판단은 DB 로그와 락 순서까지 봐야 한다.

## 왜 중요한가

데드락은 “락을 썼으니 안전하다”에서 끝나지 않는다.

- 특정 요청이 오래 멈춘다
- DB가 트랜잭션 하나를 희생시킨다
- 재시도 설계가 없으면 사용자 장애로 이어진다

따라서 데드락은 락의 부작용이 아니라 **락을 쓸 때 반드시 다뤄야 하는 운영 이슈**다.

---

## 데드락이 생기는 이유

데드락은 서로가 가진 자원을 상대가 풀어주기만 기다리는 상태다.

전형적인 조건은 이렇다.

- 트랜잭션 A가 `row 1`을 잡고 `row 2`를 기다림
- 트랜잭션 B가 `row 2`를 잡고 `row 1`을 기다림

둘 다 계속 기다리면 진행이 멈춘다.

핵심은 **락 자체가 나쁜 게 아니라, 락 획득 순서가 일관되지 않을 때** 문제가 커진다는 점이다.

---

## 대표 사례

### 사례 1. 계좌 이체

송금과 입금이 같은 테이블의 서로 다른 row를 건드릴 수 있다.

예:

1. A 계좌 차감
2. B 계좌 증가

다른 요청은 반대 순서로 접근하면 데드락이 발생할 수 있다.

### 사례 2. 주문과 재고 갱신

주문 상태와 재고 row를 같이 업데이트하는 흐름에서,

- 요청 1은 주문 먼저, 재고 나중
- 요청 2는 재고 먼저, 주문 나중

처럼 경로가 갈리면 데드락 가능성이 높아진다.

### 사례 3. 배치 작업과 실시간 요청 충돌

배치가 대량 row를 잠그는 동안 실시간 API가 같은 row를 잡으려 하면 대기가 늘어난다.

이건 순환 대기까지 가지 않더라도 체감 장애를 만든다.

---

## 탐지와 해소

DB는 보통 데드락을 자동 탐지하고, 한쪽 트랜잭션을 희생시켜 풀어낸다.

즉 운영에서 보이는 현상은 보통 다음 중 하나다.

- 한 요청이 deadlock error로 실패
- 오래 기다리다가 timeout

중요한 건 “에러가 났다”보다 **재시도 가능한 실패인지**를 판단하는 것이다.

### deadlock과 lock timeout 경계 빠르게 나누기

| 질문 | deadlock | lock wait timeout |
|---|---|---|
| 핵심 장면 | 서로가 서로의 락을 기다리는 cycle이 생김 | 한쪽이 락을 오래 쥐고 있어 기다리다 limit를 넘김 |
| DB의 즉시 반응 | 보통 희생자 하나를 골라 transaction을 abort함 | 보통 기다리던 쪽이 timeout으로 끝남 |
| beginner가 처음 붙일 말 | "순서가 엇갈려 서로 물렸다" | "막혀서 오래 기다렸는데 안 풀렸다" |
| 첫 대응 포인트 | lock ordering, whole-transaction retry | blocker, 긴 트랜잭션, timeout budget |
| 같은 대응으로 묶어도 되나 | 보통 아니다. retry 후보로 자주 본다 | 상황 의존적이다. 원인 없이 retry만 늘리면 반복될 수 있다 |

이 표는 **첫 분류용 브리지**다. MySQL/InnoDB처럼 deadlock detector가 있는 엔진에서는 위 구분이 잘 맞지만, 실제 예외 이름과 timeout 정책은 DB 제품과 설정에 따라 달라질 수 있다.

### 애플리케이션 관점

- deadlock error는 보통 재시도 후보다
- 재시도는 즉시 무한 반복이 아니라 backoff를 둬야 한다
- 외부 API와 함께 묶인 경우 중복 실행 가능성도 같이 점검해야 한다

---

## 예방 전략

### 1. 락 획득 순서를 통일한다

가장 효과적인 방법은 항상 같은 순서로 row를 잡는 것이다.

예:

- 항상 `user_id` 오름차순
- 항상 `order -> stock` 순서

순서가 흔들리면 데드락 가능성이 급격히 올라간다.

### 2. 트랜잭션을 짧게 유지한다

트랜잭션이 길수록 락 점유 시간이 늘어난다.

특히 다음은 피해야 한다.

- 트랜잭션 안에서 외부 API 호출
- 불필요한 대기
- 큰 범위의 scan 후 update

### 3. 잠금 범위를 줄인다

불필요하게 넓은 범위를 잠그면 충돌 면적이 커진다.

예:

- 전체 테이블 잠금 대신 row-level lock 사용
- 범위 조건이 큰 쿼리를 최소화

### 4. 재시도 정책을 둔다

완벽한 예방은 어렵다.

그래서 실제 운영에서는

- 재시도 횟수 제한
- 지수 백오프
- 멱등 처리

가 같이 가야 한다.

---

## 실무 체크리스트

- 락을 잡는 SQL 순서가 서비스 전반에서 일관적인가
- 트랜잭션 안에 외부 호출이 들어가 있지 않은가
- deadlock/timeout 에러가 재시도 가능한 유형으로 처리되는가
- 배치와 실시간 요청의 충돌 구간이 분리되어 있는가
- 같은 요청이 재시도돼도 결과가 안전한가

---

## 시니어 관점 질문

- 데드락이 발생했을 때 시스템은 자동 재시도할 것인가, 사용자에게 실패를 노출할 것인가?
- 락 순서를 통일하는 설계가 가능한가, 아니면 구조적으로 충돌을 받아들여야 하는가?
- deadlock과 lock timeout을 같은 실패로 취급해도 되는가?
- 트랜잭션을 짧게 만들기 위해 비동기로 빼야 하는 경계는 어디인가?
