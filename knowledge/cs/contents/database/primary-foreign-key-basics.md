# 기본 키와 외래 키 기초 (Primary Key & Foreign Key Basics)

> 한 줄 요약: 기본 키는 테이블 안에서 행을 유일하게 식별하는 컬럼이고, 외래 키는 다른 테이블의 기본 키를 참조해 두 테이블 사이의 관계와 무결성을 보장한다.

**난이도: 🟢 Beginner**

관련 문서:

- [조인 테이블과 복합 키 기초](./join-table-composite-key-basics.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [정규화 기초](./normalization-basics.md)
- [database 카테고리 인덱스](./README.md)
- [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)

retrieval-anchor-keywords: primary key basics, foreign key basics, pk fk 입문, 기본키 외래키 처음 배우는데, pk fk 차이, 기본키가 뭐예요, 외래키 제약 설명, surrogate key natural key, 참조 무결성 기초, db 관계 키 입문, primary foreign key basics basics, primary foreign key basics beginner, primary foreign key basics intro, database basics, beginner database

## 핵심 개념

관계형 데이터베이스에서 **기본 키(Primary Key, PK)** 는 테이블의 각 행(row)을 유일하게 식별하는 컬럼(또는 컬럼 조합)이다. 같은 값이 중복될 수 없고(`UNIQUE`), `NULL`이 허용되지 않는다.

**외래 키(Foreign Key, FK)** 는 한 테이블의 컬럼이 다른 테이블의 기본 키를 참조한다는 선언이다. 이 선언 덕분에 DB는 참조 무결성(referential integrity)을 자동으로 지킨다 — 없는 부모 행을 자식이 참조하거나, 자식이 남아 있는 부모 행을 삭제하려 할 때 오류를 낸다.

입문자가 자주 헷갈리는 지점:

- 기본 키는 자동으로 클러스터드 인덱스(MySQL InnoDB 기준)로 만들어진다 — 별도 `CREATE INDEX` 없이 조회가 빠른 이유다
- 외래 키 제약은 선언적 보장이지 성능 최적화가 아니다 — 오히려 INSERT/DELETE 시 참조 테이블 체크로 비용이 발생한다
- 애플리케이션 레벨에서 관계를 관리하고 외래 키를 생략하는 팀도 있다 — 이는 의도적 선택이지 기본 상태가 아니다

## 한눈에 보기

- `orders` 테이블의 `order_id`는 기본 키(PK) — 각 주문을 고유하게 식별한다
- `orders.customer_id`는 외래 키(FK) — `customers.customer_id`를 참조한다
- 존재하지 않는 `customer_id`(예: `999`)를 `orders`에 넣으면 DB가 거부한다

```
orders(order_id PK, customer_id FK→customers)
customers(customer_id PK, name)
```

## 상세 분해

**기본 키 종류**:

- **자연 키(natural key)**: 실세계 의미를 가진 값 — 주민등록번호, 이메일 등. 변경 가능성이 있거나 길면 PK로 쓰기 어렵다.
- **대리 키(surrogate key)**: 의미 없이 DB가 생성한 식별자 — `AUTO_INCREMENT` 정수, UUID 등. 실무에서 더 흔히 쓴다.
- **복합 기본 키(composite PK)**: 두 컬럼 조합이 유일성을 보장할 때 — 연결 테이블(`order_item`)에서 `(order_id, item_id)` 조합.

**외래 키 옵션 (`ON DELETE`)**:

- `RESTRICT` / `NO ACTION`: 자식이 존재하면 부모 삭제 거부 (기본값)
- `CASCADE`: 부모 삭제 시 자식도 함께 삭제
- `SET NULL`: 부모 삭제 시 FK 컬럼을 NULL로 변경

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "UUID를 PK로 쓰면 느리다" | 무작위 UUID는 클러스터드 인덱스 삽입 시 페이지 분할이 잦아 느릴 수 있다 | 순서가 보장되는 UUID v7 또는 ULID를 고려하거나, 인덱스 분기 비용을 측정한 뒤 결정한다 |
| "FK는 항상 걸어야 한다" | 대규모 서비스에서는 마이그레이션·배포 시 FK 제약이 병목이 되어 의도적으로 생략하기도 한다 | 무결성 보장 주체(DB vs 애플리케이션)를 팀이 명시적으로 결정한다 |
| "PK가 없어도 된다" | PK가 없으면 각 행의 고유 식별이 불가능하고, InnoDB는 내부적으로 숨겨진 row_id를 만든다 | 거의 모든 테이블에 명시적 PK를 정의하는 것이 원칙이다 |

## 실무에서 쓰는 모습

**(1) 일반 도메인 테이블** — `id BIGINT AUTO_INCREMENT PRIMARY KEY` 패턴이 가장 흔하다. 작은 서비스에서는 FK 제약도 함께 선언해 DB가 무결성을 보장하게 한다.

**(2) 연결 테이블(join table)** — 다대다(N:M) 관계를 표현할 때 두 테이블의 PK를 FK로 가지고 두 FK의 조합을 복합 PK로 사용한다. 예: `user_role(user_id, role_id)`.

## 더 깊이 가려면

- 연결 테이블, 복합 PK, surrogate key 선택 기준을 초급자 관점에서 다시 보려면 → [조인 테이블과 복합 키 기초](./join-table-composite-key-basics.md)
- 인덱스와 PK의 관계, 클러스터드 vs 논클러스터드 → [인덱스와 실행 계획](./index-and-explain.md)
- 테이블 설계 시 PK 선택이 정규화와 어떻게 연결되는지 → [정규화 기초](./normalization-basics.md)

cross-category bridge:

- JPA `@Entity`에서 PK와 FK가 `@Id`, `@ManyToOne` 어노테이션으로 어떻게 표현되는지 → [Repository, DAO, Entity](../software-engineering/repository-dao-entity.md)

## 면접/시니어 질문 미리보기

> Q: 기본 키로 자연 키와 대리 키 중 무엇을 선택하시겠어요?
> 의도: PK 선택의 트레이드오프를 이해하는지 확인
> 핵심: 자연 키는 의미가 명확하지만 변경 가능성이 있다. 대리 키는 안정적이지만 의미가 없다. 실무에서는 변경 안전성을 위해 대리 키를 선호하는 경향이 있다.

> Q: 외래 키 제약이 없으면 어떤 문제가 생기나요?
> 의도: 참조 무결성의 실질적 의미를 아는지 확인
> 핵심: 고아 데이터(orphaned row)가 생길 수 있다. 부모가 삭제되었는데 자식 데이터가 남아 있으면 조인 시 빈 결과나 예외가 발생하고, 비즈니스 로직에서 처리가 복잡해진다.

## 한 줄 정리

기본 키는 행의 고유 식별자이고, 외래 키는 다른 테이블 PK를 참조해 두 테이블 간 관계와 참조 무결성을 DB 수준에서 보장한다.
