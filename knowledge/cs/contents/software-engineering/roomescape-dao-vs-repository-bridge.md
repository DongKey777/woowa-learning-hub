---
schema_version: 3
title: 'roomescape 4단계 계층 분리에서 DAO와 Repository 어떻게 나누나'
concept_id: software-engineering/roomescape-dao-vs-repository-bridge
canonical: false
category: software-engineering
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- DAO-vs-repository
- layer-separation-step4
- jdbc-template-leak
aliases:
- roomescape DAO
- roomescape Repository 분리
- 룸이스케이프 4단계 계층 분리
- ReservationDao
- JdbcReservationRepository 의도
intents:
- mission_bridge
- comparison
prerequisites:
- software-engineering/repository-dao-entity
linked_paths:
- contents/software-engineering/repository-dao-entity.md
- contents/software-engineering/dao-vs-query-model-entrypoint-primer.md
- contents/software-engineering/repository-interface-contract-primer.md
forbidden_neighbors:
- contents/software-engineering/repository-naming-smells-primer.md
confusable_with:
- software-engineering/repository-dao-entity
- software-engineering/dao-vs-query-model
- software-engineering/repository-interface-contract
expected_queries:
- 룸이스케이프 4단계에서 DAO랑 Repository 둘 다 만들어야 해?
- ReservationDao를 ReservationRepository로 바꿔도 돼?
- 미션에서 JdbcTemplate 코드를 어디 클래스에 두는 게 맞아?
- 계층 분리할 때 DAO와 Repository 차이가 뭐야?
contextual_chunk_prefix: |
  이 문서는 roomescape 4단계 계층 분리에서 DAO와 Repository 이름, 인터페이스,
  JDBC 구현 경계를 어떻게 나눌지 설명하는 mission_bridge다. ReservationDao,
  JdbcReservationRepository, Service가 보는 영속화 인터페이스, JdbcTemplate
  위치 같은 질의를 레이어링과 의존성 방향 판단으로 연결한다.
---

# roomescape 4단계 계층 분리에서 DAO와 Repository 어떻게 나누나

> 한 줄 요약: roomescape 4단계는 *Service → Repository → JDBC* 흐름을 만든다. DAO는 "JDBC 호출 한 줄"의 이름이고, Repository는 "도메인이 보는 영속화 인터페이스"의 이름 — 둘 다 만들 필요 없이 *Repository 인터페이스 + JDBC 구현*으로 합쳐도 된다.

**난이도: 🟢 Beginner**

**미션 컨텍스트**: spring-roomescape-admin (Woowa Spring 트랙) — 4단계 계층 분리

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "룸이스케이프 4단계에서 DAO랑 Repository 둘 다 만들어야 하나요?" | `ReservationDao`, `ReservationRepository`, JDBC 구현 이름 선택 | Service가 보는 영속화 계약과 JDBC 실행 구현을 나눈다 |
| "`ReservationDao`를 `ReservationRepository`로 바꿔도 되나요?" | DAO 이름을 Repository 인터페이스/구현으로 재정리하는 단계 | DB 중심 이름과 도메인 저장 창구 이름의 차이를 본다 |
| "`JdbcTemplate` 코드를 어디 클래스에 두는 게 맞나요?" | Controller/Service에 JDBC 세부가 새는 코드 | `JdbcReservationRepository` 같은 persistence adapter에 숨긴다 |

관련 문서:

- [Repository, DAO, Entity 정리](./repository-dao-entity.md) — 일반 개념
- [DAO vs Query Model Entrypoint Primer](./dao-vs-query-model-entrypoint-primer.md) — DAO 단일 진입점 관점

## 미션의 어디에 DAO/Repository 분기가 보이는가

3단계까지는 컨트롤러가 `JdbcTemplate`을 직접 들고 있었거나, `ReservationDao`라는 이름의 클래스가 SQL 실행을 담당했다. 4단계에 진입하면 다음 두 가지 결정을 동시에 해야 한다:

1. **인터페이스를 추출할 것인가** — `ReservationRepository` interface + `JdbcReservationRepository` impl
2. **DAO라는 이름을 유지할 것인가** — `ReservationDao` 그대로 vs `ReservationRepository`로 개명

미션의 실제 코드는 인터페이스 추출 + Repository 명명을 택하고 있다:

```java
// repository/ReservationRepository.java
public interface ReservationRepository {
    Reservation save(Reservation reservation);
    List<Reservation> findAll();
    void deleteById(Long id);
}

// repository/JdbcReservationRepository.java
@Repository
public class JdbcReservationRepository implements ReservationRepository {
    private final JdbcTemplate jdbcTemplate;
    // save / findAll / deleteById JDBC 구현
}
```

여기서 핵심은 *Service는 `ReservationRepository` 인터페이스만 본다*는 점이다. JDBC인지 JPA인지 in-memory Mock인지 Service는 모른다.

## 왜 DAO와 Repository를 *둘 다* 만들지 않는가

### 책임이 같은 두 이름

DAO와 Repository는 *다른 모델에서 비슷한 일*을 한다:

- **DAO (Data Access Object)** — 테이블 1:1 매핑, "이 행을 가져와/저장해". DB 중심.
- **Repository** — 도메인 객체 collection처럼 보이는 인터페이스. "이 도메인 모델을 저장해/찾아". 도메인 중심.

roomescape처럼 도메인이 작고(Reservation, ReservationTime 두 엔티티) JDBC만 쓰는 미션에서는 *둘이 거의 같은 모양*이 된다. 그래서 굳이 `ReservationDao` + `ReservationRepository` 두 개를 만들면 *얇은 위임 한 층이 추가될 뿐* 책임은 안 늘어난다.

### Repository로 합치는 이유

미션 코드가 Repository 이름을 택한 이유는 셋이다:

1. **Service가 "도메인 collection"으로 보고 싶다** — `reservations.findAll()`은 *컬렉션을 다루는* 자연어와 가깝다. `reservationDao.selectAll()`은 *SQL을 다루는* 자연어다.
2. **Spring Data 마이그레이션 길** — 5단계에서 JPA로 바꿀 때 `extends JpaRepository`로 자연스럽게 넘어간다.
3. **테스트 더블이 쉽다** — `FakeReservationRepository implements ReservationRepository`로 in-memory 구현을 끼워서 Service만 단위 테스트할 수 있다.

## 미션 PR에서 자주 보이는 두 가지 잘못된 분기

### 잘못 1 — DAO + Repository 둘 다 만들고 위임만

```java
public class ReservationRepository {
    private final ReservationDao dao;
    public List<Reservation> findAll() { return dao.findAll(); }  // 단순 위임
    public Reservation save(Reservation r) { return dao.save(r); }  // 단순 위임
}
```

이건 *얇은 wrapping*이다. Repository가 도메인 합성/변환 같은 추가 책임을 지지 않으면 DAO를 그대로 쓰는 게 낫다. 멘토의 *"한 층이 의미 없다"*가 이 패턴을 가리킨다.

### 잘못 2 — Service가 JdbcTemplate을 직접 import

```java
@Service
public class ReservationService {
    private final JdbcTemplate jdbcTemplate;  // ❌ 4단계 계층 분리 실패
}
```

4단계의 핵심은 *Service가 JDBC를 모르는 것*. 위 코드는 3단계 머무름이고, *Repository 추상화의 의의가 사라진다*. 멘토의 *"계층이 분리 안 됐어요"*는 이 신호다.

## 자가 점검

- [ ] `ReservationService`가 `JdbcTemplate`이나 `DataSource`를 import하지 않는가?
- [ ] `ReservationRepository`는 *interface*이고, `JdbcReservationRepository`는 그 구현 한 종류인가?
- [ ] 테스트에서 `FakeReservationRepository`를 만들어 Service만 단위 테스트할 수 있나?
- [ ] DAO와 Repository를 둘 다 두지 않았는가? (둘 중 한 이름만)
- [ ] Repository 메소드 이름이 도메인 언어인가? (`findAllByTimeId` vs `selectByTimeIdSql`)

## 다음 문서

- 더 큰 그림: [Repository, DAO, Entity 정리](./repository-dao-entity.md)
- Repository 인터페이스 계약을 어떻게 적나: [Repository Interface Contract Primer](./repository-interface-contract-primer.md)
- 5단계로 넘어가 JPA Repository로 옮길 때: *Spring Data Repository 브리지* (별도 문서, 후속 Wave)
