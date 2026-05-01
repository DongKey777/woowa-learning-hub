---
schema_version: 2
title: "트랜잭션 실전 시나리오"
concept_id: "database/transaction-case-studies"
difficulty: advanced
doc_role: playbook
level: advanced
aliases:
  - transaction boundary
  - idempotency key
  - inventory race
  - duplicate payment
  - 정합성 시나리오
expected_queries:
  - 중복 결제는 트랜잭션만으로 막을 수 있어?
  - 재고 차감은 어떤 트랜잭션 경계로 묶어야 해?
  - idempotency key랑 transaction은 어떻게 같이 봐?
  - 주문 생성 정합성은 어디까지 같은 트랜잭션이야?
forbidden_neighbors:
  - contents/database/transaction-basics.md
  - contents/database/transaction-isolation-basics.md
---

# 트랜잭션 실전 시나리오

**난이도: 🔴 Advanced**

> 트랜잭션을 정의로만 외우지 않고 실제 정합성 문제에 연결하기 위한 문서
>
> 문서 역할: 이 문서는 anomaly catalog라기보다, "어떤 작업을 같은 트랜잭션 경계에 묶어야 하나"를 빠르게 익히는 **survey 문서**다.

<details>
<summary>Table of Contents</summary>

- [이 문서 다음에 볼 focused 문서](#이-문서-다음에-볼-focused-문서)
- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [시나리오 1. 중복 결제](#시나리오-1-중복-결제)
- [시나리오 2. 재고 차감](#시나리오-2-재고-차감)
- [시나리오 3. 포인트 차감과 주문 생성](#시나리오-3-포인트-차감과-주문-생성)
- [시나리오 4. 장기 게임 저장](#시나리오-4-장기-게임-저장)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

retrieval-anchor-keywords: transaction case study, transaction boundary, idempotency key with transaction, inventory deduction race, optimistic lock vs pessimistic lock, atomic update, duplicate payment prevention, order creation consistency, consistency unit, transaction scenario interview

## 이 문서 다음에 볼 focused 문서

- write skew, phantom read 같은 anomaly 자체를 보려면 [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)를 본다.
- 락 경합과 데드락 triage는 [Deadlock Case Study](./deadlock-case-study.md), [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)로 내려간다.
- 멱등성과 중복 요청 경계는 [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)에서 더 명확히 본다.
- 부분 롤백과 저장 지점은 [Savepoint와 Partial Rollback](./savepoint-partial-rollback.md)으로 이어진다.

## 왜 이 문서가 필요한가

트랜잭션은 보통 ACID로 외우기 쉽다.  
하지만 실무에서는 “이걸 왜 트랜잭션으로 묶어야 하지?”가 더 중요하다.

이 문서는 실제 서비스에서 자주 나오는 정합성 시나리오를 통해,

- 어떤 작업을 한 트랜잭션으로 묶어야 하는지
- 어디서 실패하면 안 되는지
- 어떤 대안을 고려해야 하는지

를 익히기 위해 만든다.

---

## 시나리오 1. 중복 결제

### 문제

클라이언트가 결제 요청을 보냈는데 응답이 늦어져 같은 요청을 다시 보낼 수 있다.

이때 서버가 요청을 단순히 두 번 처리하면

- 주문 1건에 대해 결제가 2번 일어나거나
- 외부 PG 호출이 2번 일어나거나
- 내부 결제 기록이 중복 저장될 수 있다

### 핵심 포인트

- 트랜잭션만으로는 완전히 해결되지 않는다
- **idempotency key** 또는 **중복 요청 식별자**가 필요할 수 있다

즉 이 문제는

- DB 트랜잭션
- API 멱등성

둘을 같이 봐야 한다.

---

## 시나리오 2. 재고 차감

### 문제

재고가 1개 남아 있는데, 두 요청이 동시에 “재고 확인 -> 차감”을 하면
둘 다 성공해버릴 수 있다.

### 잘못된 흐름

1. 재고 조회
2. 애플리케이션에서 `if (stock > 0)` 확인
3. update

이 사이에 다른 요청이 끼어들면 정합성이 깨질 수 있다.

### 해결 방향

- 트랜잭션 + 락
- 원자적 update
- 버전 기반 낙관적 락

즉 “읽고 판단하고 다시 쓰는” 흐름이 안전한지 항상 의심해야 한다.

---

## 시나리오 3. 포인트 차감과 주문 생성

### 문제

한 요청 안에서

- 포인트 차감
- 주문 생성

두 작업이 같이 일어난다고 하자.

만약 포인트는 차감됐는데 주문 생성이 실패하면 데이터가 꼬인다.

### 핵심

이건 전형적인 **한 트랜잭션으로 묶여야 하는 작업**이다.

즉 다음 둘은 같이 성공하거나 같이 실패해야 한다.

- `UPDATE points ...`
- `INSERT orders ...`

---

## 시나리오 4. 장기 게임 저장

장기 게임에서 한 수를 둘 때 DB에 반영해야 하는 변화는 보통 이렇다.

- 현재 턴 변경
- 게임 상태 변경
- 이동한 말 위치 변경
- 잡힌 말 삭제

이 네 작업 중 하나라도 빠지면 게임 상태가 깨진다.

예:

- `pieces`는 이동했는데
- `games.turn`은 안 바뀜

이런 상태는 곧바로 복원 문제로 이어진다.

즉 **매 수 저장은 하나의 트랜잭션으로 묶여야 한다.**

---

## 시니어 관점 질문

- 이 작업이 정말 한 트랜잭션이어야 하는가, 아니면 결국 분리 가능한가?
- 트랜잭션 범위를 넓히면 어떤 성능 비용이 생기는가?
- 멱등성과 트랜잭션 중 무엇이 더 핵심인 문제인가?
- DB 트랜잭션만으로 해결 안 되는 문제는 무엇인가?
