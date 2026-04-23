# Repository, DAO, Entity

**난이도: 🟡 Intermediate**

> 신입 백엔드 개발자가 저장 계층을 설계할 때 자주 헷갈리는 개념 정리

<details>
<summary>Table of Contents</summary>

- [왜 헷갈리는가](#왜-헷갈리는가)
- [Repository](#repository)
- [DAO](#dao)
- [Entity](#entity)
- [Mapper와 RowMapper](#mapper와-rowmapper)
- [언제 무엇을 둘까](#언제-무엇을-둘까)
- [작은 프로젝트에서의 추천 구조](#작은-프로젝트에서의-추천-구조)
- [추천 참고 자료](#추천-참고-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

> 관련 문서:
> - [Software Engineering README: Repository, DAO, Entity](./README.md#repository-dao-entity)
> - [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
> - [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
>
> retrieval-anchor-keywords: repository vs dao, repository boundary, persistence boundary, domain repository, dao table access, entity vs domain model, mapper rowmapper, aggregate persistence, repository abstraction, database access layer, persistence adapter mapping checklist, domain object to jpa entity, jpa entity mapper checklist

## 왜 헷갈리는가

저장 계층을 처음 설계할 때는 보통 이런 이름이 한꺼번에 등장한다.

- Repository
- DAO
- Entity
- Mapper

문제는 이름은 익숙한데, **무슨 기준으로 나누는지**가 헷갈린다는 점이다.

핵심은 다음처럼 구분하면 된다.

- **Repository**: 도메인 객체 관점
- **DAO**: 테이블/SQL 관점
- **Entity**: DB 저장 형태 관점
- **Mapper**: DB row ↔ 객체 변환 관점

---

## Repository

Repository는 **도메인 객체를 저장하고 조회하는 창구**다.

예를 들어 장기 게임이면 이렇게 말하는 쪽에 가깝다.

```java
gameRepository.save(game);
JanggiGame game = gameRepository.findById(id);
```

즉 Repository는

- “게임을 저장한다”
- “게임을 불러온다”

처럼 **도메인 언어로 말하는 계층**이다.

### 특징

- 도메인 중심
- 저장소 구현 세부사항을 감춘다
- DB가 바뀌어도 바깥 사용 코드는 덜 흔들린다

---

## DAO

DAO(Data Access Object)는 **DB 테이블에 직접 접근하는 객체**다.

예:

- `GameDao`
- `PieceDao`

이 객체들은 보통

- SQL 실행
- insert / update / delete / select
- `ResultSet` 읽기

를 담당한다.

즉 DAO는 **테이블 중심**이다.

### Repository와의 차이

- Repository는 “게임 저장/조회”
- DAO는 “games 테이블 insert/update”

즉 DAO가 더 세부적이다.

---

## Entity

Entity는 여기서 **DB에 저장하기 쉬운 데이터 모양**이라고 보면 된다.

예를 들어 도메인 객체가

- `JanggiGame`
- `Board`
- `Piece`
- `Position`

처럼 연결되어 있어도, DB는 row 형태를 좋아한다.

그래서 이런 식의 객체를 둘 수 있다.

```java
public record PieceEntity(
        long gameId,
        int x,
        int y,
        String name,
        String team
) {
}
```

즉 Entity는 **도메인 그 자체라기보다 DB 저장용 형태**에 가깝다.

### 주의

프레임워크에 따라 `Entity`라는 말이 다르게 쓰일 수 있다.

- JPA에서는 `@Entity`가 붙은 ORM 엔티티를 말함
- JDBC 문맥에서는 그냥 DB row용 객체를 뜻할 수도 있음

---

## Mapper와 RowMapper

Mapper는 **DB row를 객체로 바꾸거나, 객체를 DB 저장 형태로 바꾸는 역할**을 한다.

JPA adapter 안에서 domain object와 `@Entity`를 어디서 끊어야 할지 헷갈린다면 [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)를 같이 보면 좋다.

예:

- `GameEntityMapper`
- `PieceEntityMapper`
- `RowMapper`

### 왜 필요하나

저장 계층에서 자주 하는 일은 결국 이거다.

- `ResultSet` -> Entity
- Entity -> Domain
- Domain -> Entity

이 변환 책임을 별도 클래스로 두면 역할이 선명해진다.

---

## 언제 무엇을 둘까

### Repository만으로 충분한 경우

- 프로젝트가 작다
- 저장 대상이 많지 않다
- SQL이 단순하다

이 경우에는 Repository 하나에서

- SQL 작성
- 매핑
- 저장/조회

를 같이 해도 된다.

### DAO까지 나누는 게 좋은 경우

- 테이블이 여러 개다
- 저장/조회 SQL이 길다
- 저장소 코드가 커진다
- 테이블별 책임을 분리하고 싶다

### Entity/Mapper가 필요한 경우

- 도메인 객체와 DB 저장 형태가 많이 다르다
- 변환 코드가 길어진다
- DB 변경이 도메인으로 새는 걸 줄이고 싶다

---

## 작은 프로젝트에서의 추천 구조

신입 수준의 작은 프로젝트에서는 보통 이 정도면 충분하다.

### 1단계

- `Repository`

하나만 둔다.

### 2단계

필요하면

- `Repository + DAO`

로 나눈다.

### 3단계

더 복잡해지면

- `Repository + DAO + Entity + Mapper`

까지 간다.

즉 처음부터 모든 계층을 다 만들 필요는 없다.

---

## 추천 참고 자료

- Martin Fowler - Repository: https://martinfowler.com/eaaCatalog/repository.html
- Martin Fowler - Data Mapper: https://martinfowler.com/eaaCatalog/dataMapper.html
- Martin Fowler - Gateway: https://martinfowler.com/eaaCatalog/gateway.html

## 면접에서 자주 나오는 질문

### Q. Repository와 DAO의 차이는 무엇인가요?

- Repository는 도메인 객체를 저장/조회하는 관점의 계층이다.
- DAO는 DB 테이블과 SQL 중심의 저수준 접근 계층이다.
- DAO가 더 세부적이라고 볼 수 있다.

### Q. Entity는 왜 필요한가요?

- 도메인 객체와 DB row의 모양이 다를 수 있기 때문이다.
- DB 저장용 형태를 따로 두면 도메인 변경을 줄이고 매핑 책임도 분리할 수 있다.

### Q. 항상 DAO와 Entity를 모두 둬야 하나요?

- 아니다.
- 규모가 작고 SQL이 단순하면 Repository 하나로도 충분하다.
- 구조가 커질 때 점진적으로 나누는 것이 더 자연스럽다.
