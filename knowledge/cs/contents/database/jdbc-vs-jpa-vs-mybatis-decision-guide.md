---
schema_version: 3
title: JDBC vs JPA vs MyBatis 결정 가이드
concept_id: database/jdbc-vs-jpa-vs-mybatis-decision-guide
canonical: false
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- where-is-sql
- orm-vs-sql-mapper-choice
- persistence-tech-mixing
aliases:
- jdbc vs jpa vs mybatis
- sql mapper vs orm vs jdbc
- repository save mapper insert jdbc template
- sql control vs productivity chooser
- orm chooser
- mybatis chooser
- jdbc template or jpa
- persistence tech chooser
symptoms:
- save는 보이는데 SQL 위치와 수정 지점을 같이 헷갈린다
- CRUD 위주 서비스인데 JDBC부터 직접 짜야 하는지 고민한다
- 복잡한 조회가 많은데 JPA와 MyBatis 중 어디에 두어야 할지 막힌다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/database-first-step-bridge
- database/sql-relational-modeling-basics
- database/transaction-basics
next_docs:
- database/transaction-basics
- database/database-first-step-bridge
- database/sql-relational-modeling-basics
linked_paths:
- contents/database/jdbc-jpa-mybatis-basics.md
- contents/database/jdbc-jpa-mybatis.md
- contents/database/jdbc-code-patterns.md
- contents/database/transaction-basics.md
- contents/database/connection-pool-transaction-propagation-bulk-write.md
- contents/database/query-tuning-checklist.md
- contents/spring/spring-data-jpa-basics.md
- contents/software-engineering/repository-dao-entity.md
confusable_with:
- database/jdbc
- database/jpa
- database/mybatis
forbidden_neighbors:
- contents/database/database-first-step-bridge.md
expected_queries:
- 지금 서비스는 CRUD가 대부분인데 JDBC, JPA, MyBatis 중 무엇부터 고르는 게 좋아?
- save 호출만 보이는 코드와 mapper xml이 보이는 코드는 어떤 차이로 읽어야 해?
- SQL 튜닝을 자주 해야 하면 JPA보다 MyBatis가 더 맞는 이유가 뭐야?
- 쿼리가 단순한데도 MyBatis를 쓰는 팀과 JPA를 쓰는 팀의 판단 기준이 궁금해
- raw SQL 제어가 필요하지만 보일러플레이트는 줄이고 싶을 때 어떤 선택지가 자연스러워?
- 미션 코드에서 JdbcTemplate, JpaRepository, Mapper가 섞여 보이면 무엇을 기준으로 분리해 읽어?
contextual_chunk_prefix: |
  이 문서는 학습자가 JDBC, JPA, MyBatis 중 무엇을 선택해야 하는지,
  혹은 미션 코드에서 save, mapper.xml, JdbcTemplate이 섞여 보일 때 어떤
  축으로 읽어야 하는지 정리하는 beginner chooser다. SQL 위치, 객체 중심
  CRUD, 복잡한 조회 튜닝, 보일러플레이트 감수 여부 같은 질문이 결정
  매트릭스와 흔한 오선택 섹션으로 바로 연결되도록 설계됐다.
---

# JDBC vs JPA vs MyBatis 결정 가이드

## 한 줄 요약

> SQL을 어디서 직접 통제할지와 반복 코드를 어느 정도 감수할지 먼저 정하면, `JDBC`, `JPA`, `MyBatis` 선택이 훨씬 덜 헷갈린다.

## 결정 매트릭스

| 지금 더 중요한 기준 | JDBC | JPA | MyBatis |
|---|---|---|---|
| SQL을 한 줄씩 눈으로 보고 바로 고치고 싶다 | 가장 직접적이다 | SQL이 뒤로 숨을 수 있다 | SQL은 직접 보되 매핑은 덜 반복한다 |
| CRUD 생산성을 먼저 끌어올리고 싶다 | 반복 코드가 가장 많다 | 가장 유리하다 | 중간 정도다 |
| 복잡한 조회와 튜닝 포인트가 자주 나온다 | 가능하지만 코드량이 늘 수 있다 | 조회가 복잡해질수록 설계 주의가 필요하다 | 가장 자연스럽게 버틴다 |
| 팀이 객체 중심으로 읽고 싶다 | SQL 중심 사고가 필요하다 | 가장 잘 맞는다 | 객체와 SQL을 분리해 절충한다 |
| 미션 코드에서 첫 독해를 빨리 끝내고 싶다 | `JdbcTemplate` 호출을 따라간다 | `Repository`와 `@Entity`를 먼저 본다 | `Mapper` 인터페이스와 XML을 같이 본다 |

짧게 정리하면, SQL을 직접 들고 가면 `JDBC`, CRUD 중심이면 `JPA`, SQL 통제와 생산성 사이 절충이 필요하면 `MyBatis`가 1차 후보가 된다.

## 흔한 오선택

`JPA`를 쓰면 SQL을 몰라도 된다고 생각하는 경우가 많다. 하지만 flush 시점, N+1, 느린 조회가 나오면 결국 SQL과 인덱스를 읽어야 해서, "SQL을 숨기고 싶다"가 아니라 "기본 CRUD를 더 짧게 쓰고 싶다"일 때 선택하는 편이 맞다.

`MyBatis`를 단순히 레거시 전용이라고 보는 것도 흔한 오선택이다. 실제로는 조회 shape가 자주 바뀌고 SQL을 명시적으로 관리해야 하는 팀에서 지금도 충분히 자연스럽다. 다만 mapper와 XML 분리가 익숙하지 않으면 처음 독해 비용이 올라간다.

`JDBC`를 배웠으니 실무도 무조건 JDBC부터 시작해야 한다고 밀어붙이는 경우도 있다. 원리 학습에는 좋지만, 단순 CRUD가 많은 서비스라면 반복 매핑과 자원 관리 코드가 빠르게 부담이 된다. 학습 순서와 실무 기본 선택은 같은 질문이 아니다.

## 다음 학습

코드에서 `save()`만 보이고 SQL 위치가 먼저 헷갈리면 [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)와 [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)부터 짧게 읽는 편이 안전하다.

이미 기술 이름은 구분했는데 flush, 영속성 컨텍스트, OSIV처럼 런타임 동작이 막히면 [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)로 내려가고, raw SQL 코드 패턴이 필요하면 [JDBC 실전 코드 패턴](./jdbc-code-patterns.md)으로 이어 가면 된다.

트랜잭션 경계나 커넥션 점유 시간까지 같이 흔들리면 [트랜잭션 기초](./transaction-basics.md)와 [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)를 함께 보는 편이 다음 판단에 도움이 된다.
