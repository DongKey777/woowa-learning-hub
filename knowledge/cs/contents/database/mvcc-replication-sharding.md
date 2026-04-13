# MVCC, Replication, Sharding

> 데이터베이스 확장성과 동시성 관점에서 자주 나오는 개념 정리

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [MVCC](#mvcc)
- [Replication](#replication)
- [Sharding](#sharding)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 중요한가

백엔드 면접에서는 단순 CRUD를 넘어

- 동시성에서 읽기/쓰기가 어떻게 공존하는지
- DB를 어떻게 확장하는지

를 묻는 경우가 많다.

---

## MVCC

MVCC(Multi-Version Concurrency Control)는 **동시에 접근하는 트랜잭션들이 서로 덜 막히도록 여러 버전의 데이터를 관리하는 방식**이다.

핵심 감각:

- 읽는 쪽은 특정 시점의 snapshot을 본다
- 쓰는 쪽은 새 버전을 만든다

장점:

- 읽기와 쓰기 충돌을 줄일 수 있다
- 동시성 성능이 좋아질 수 있다

단점:

- 내부 동작을 이해하지 못하면 “왜 최신 값이 바로 안 보이는지” 헷갈릴 수 있다
- undo/version 관리 비용이 있다

---

## Replication

Replication은 **같은 데이터를 여러 DB 서버에 복제하는 것**이다.

대표 목적:

- 읽기 부하 분산
- 장애 대비

예:

- Primary / Replica

주의:

- 복제 지연(replication lag)이 생길 수 있다
- 방금 쓴 데이터가 replica에는 아직 안 보일 수 있다

즉 읽기 확장은 쉬워지지만, 읽기 일관성은 별도로 고민해야 한다.

---

## Sharding

Sharding은 **데이터를 여러 DB에 나눠 저장하는 것**이다.

예:

- 사용자 ID 범위별 분리
- 지역별 분리

Replication이 “같은 데이터 복제”라면,
Sharding은 “데이터 분산 저장”이다.

장점:

- 데이터 크기를 수평으로 확장할 수 있다
- 특정 샤드 단위로 부하를 나눌 수 있다

단점:

- 샤드 키 설계가 어렵다
- 조인, 집계, 재샤딩이 복잡하다

---

## 추천 공식 자료

- PostgreSQL MVCC:
  - https://www.postgresql.org/docs/current/mvcc-intro.html
- PostgreSQL Replication:
  - https://www.postgresql.org/docs/current/high-availability.html

---

## 면접에서 자주 나오는 질문

### Q. MVCC란 무엇인가요?

- 동시에 실행되는 트랜잭션들이 서로 덜 막히도록 여러 버전의 데이터를 관리하는 방식이다.

### Q. Replication과 Sharding 차이는 무엇인가요?

- Replication은 같은 데이터를 복제하는 것이고,
- Sharding은 데이터를 분산 저장하는 것이다.

### Q. Replica를 쓰면 항상 읽기 성능이 좋아지나요?

- 읽기 분산은 가능하지만 복제 지연과 일관성 문제를 함께 고려해야 한다.
