# 조인 테이블과 복합 키 기초 (Join Table & Composite Key Basics)

> 한 줄 요약: N:M 관계는 두 테이블 사이에 연결 테이블을 하나 더 두어 풀고, 이때 두 FK 조합을 복합 기본 키로 잡으면 "같은 연결이 두 번 저장되는 문제"를 가장 직접적으로 막을 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [기본 키와 외래 키 기초](./primary-foreign-key-basics.md)
- [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md)
- [인덱스 기초](./index-basics.md)
- [database 카테고리 인덱스](./README.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

retrieval-anchor-keywords: join table basics, composite primary key beginner, many to many table design, n:m modeling intro, 연결 테이블이 뭐예요, 복합 기본 키 처음, surrogate key vs composite key, 다대다 모델링 기초, link table duplicate prevention, user role mapping beginner, enrollment table basics, 조인 테이블 왜 필요해요, join table composite key basics basics, join table composite key basics beginner, join table composite key basics intro

## 핵심 개념

초급자에게 가장 쉬운 mental model은 이것이다. **N:M은 한 줄에 담으려 하지 말고, "관계 자체를 행으로 만든다."**

예를 들어 학생 한 명은 여러 강의를 들을 수 있고, 강의 하나에도 여러 학생이 들어온다. 이 관계를 `student.course_ids = '1,3,7'` 같은 문자열로 넣기 시작하면 검색, 중복 방지, 삭제 규칙이 모두 어려워진다. 대신 `enrollment` 같은 연결 테이블을 만들고, "학생 10번이 강의 3번을 수강한다"를 **연결 행 1개**로 저장한다.

입문자가 자주 헷갈리는 지점:

- JOIN은 조회 문법이고, join table은 저장 모델이다. 이름이 비슷하지만 역할이 다르다.
- 복합 기본 키는 "컬럼이 2개라서 복잡한 PK"가 아니라 "두 값의 조합이 이 행의 정체"라는 뜻이다.
- surrogate key를 추가했다고 중복 연결 방지가 자동으로 되지 않는다. `id`만 PK로 두면 `(student_id, course_id)` 중복을 따로 막아야 한다.

## 한눈에 보기

```text
student(id PK)        course(id PK)
       \                /
        \              /
         enrollment(student_id, course_id, enrolled_at)
```

| 저장 방식 | 무엇을 의미하나 | 초급자 기준 첫 판단 |
|---|---|---|
| `student.course_ids = '1,3,7'` | 여러 관계를 문자열 한 칸에 욱여넣음 | 피한다 |
| `enrollment(student_id, course_id)` | 관계 하나를 row 하나로 저장 | 기본 선택 |
| `PRIMARY KEY (student_id, course_id)` | 같은 학생-강의 연결 중복 금지 | 기본 선택 |
| `id PK + UNIQUE(student_id, course_id)` | 별도 식별자가 필요할 때 | 이유가 있을 때만 |

## 상세 분해

**1. 왜 중간 테이블이 필요한가**

- `student`에도 `course`에도 상대 id를 여러 개 직접 넣을 수 없기 때문이다.
- N:M을 1:N + N:1 두 개로 풀어야 관계형 테이블이 깔끔해진다.
- 연결 테이블은 "누가 누구와 연결됐는가"를 저장하는 전용 공간이다.

**2. 왜 복합 기본 키가 잘 맞는가**

- `student_id + course_id` 조합 자체가 연결의 의미다.
- 같은 학생이 같은 강의를 두 번 수강 등록할 수 없다면, 그 조합이 곧 유일성 규칙이다.
- 그래서 `PRIMARY KEY (student_id, course_id)`는 식별과 중복 방지를 한 번에 해결한다.

**3. surrogate key가 도움이 되는 경우**

- 연결 행 자체를 다른 테이블이 참조해야 할 때
- 연결 행에 별도 lifecycle이 커져 "등록 요청", "승인", "취소" 같은 상태 흐름을 독립적으로 다룰 때
- ORM이나 API 계약에서 단일 id가 다루기 훨씬 단순한 상황일 때

이 경우에도 보통 `(student_id, course_id)` 유니크 제약은 함께 둔다. 그래야 "같은 연결 중복 저장"을 계속 막을 수 있다.

**4. surrogate key가 오히려 해가 되는 경우**

- 이유 없이 `id`만 추가하고 `(student_id, course_id)` 유니크 제약을 빼는 경우
- 그러면 `student_id=10, course_id=3` 행이 두 번 들어가도 DB가 허용할 수 있다.
- 결국 연결 테이블의 핵심 규칙을 애플리케이션 코드가 대신 막아야 해서 더 불안해진다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "다대다는 테이블 두 개만 있으면 되지 않나요?" | 두 테이블만으로는 "누가 누구와 연결됐는지"를 여러 건 저장하기 어렵다 | N:M은 연결 테이블로 푼다 |
| "복합 PK는 무조건 안티패턴이다" | 복합 PK가 딱 맞는 테이블도 있다. 대표가 link table이다 | 연결의 정체가 두 FK 조합이면 자연스럽다 |
| "surrogate key를 넣으면 설계가 더 좋아진다" | 중복 방지 규칙이 사라지면 오히려 나빠질 수 있다 | surrogate key가 필요하면 쓰되, 원래 유일성도 같이 남긴다 |
| "join table이면 컬럼이 두 개만 있어야 한다" | 실제로는 `created_at`, `role`, `status` 같은 부가 정보가 자주 붙는다 | 핵심은 컬럼 수가 아니라 연결 1건을 row 1개로 표현하는 것이다 |

## 실무에서 쓰는 모습

가장 흔한 예시는 `user`와 `role` 사이의 권한 매핑이다.

```sql
CREATE TABLE user_role (
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  granted_at TIMESTAMP NOT NULL,
  PRIMARY KEY (user_id, role_id)
);
```

- 사용자 1명이 여러 역할을 가질 수 있다.
- 역할 1개도 여러 사용자에게 붙을 수 있다.
- 같은 사용자에게 같은 역할이 두 번 들어가면 안 되므로 `(user_id, role_id)`를 PK로 둔다.

한편 `enrollment`가 결제, 승인, 출석 같은 별도 흐름을 크게 가지면 `enrollment_id`를 두고 다른 테이블이 그 id를 참조하게 만들 수 있다. 대신 그때도 `(student_id, course_id)` 유니크 제약을 빼면 안 된다.

## 더 깊이 가려면

- PK/FK와 대리 키, 복합 키 용어를 먼저 다시 정리하려면 → [기본 키와 외래 키 기초](./primary-foreign-key-basics.md)
- N:M이 SQL 조회에서 어떻게 JOIN으로 나타나는지 보려면 → [SQL 읽기와 관계형 모델링 기초](./sql-reading-relational-modeling-primer.md), [SQL 조인 기초](./sql-join-basics.md)
- 복합 키가 인덱스 순서와 어떤 관련이 있는지 보려면 → [인덱스 기초](./index-basics.md)

cross-category bridge:

- JPA에서 연결 테이블을 `@ManyToMany` 또는 명시적 엔티티로 어떻게 다루는지 보려면 → [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)

## 면접/시니어 질문 미리보기

> Q: 다대다 관계를 왜 직접 컬럼 하나에 저장하지 않고 연결 테이블로 푸나요?
> 의도: 관계형 모델의 기본 제약을 이해하는지 확인
> 핵심: 관계 하나를 row 하나로 저장해야 검색, 중복 방지, FK 무결성, 삭제 규칙을 DB가 자연스럽게 다룰 수 있기 때문이다.

> Q: join table에서 composite PK와 surrogate key 중 무엇을 먼저 고려하시겠어요?
> 의도: 기본 선택과 예외 조건을 구분하는지 확인
> 핵심: 연결 자체가 두 FK 조합으로 식별되면 composite PK를 먼저 본다. 연결 행이 독립적으로 참조되거나 lifecycle이 커질 때 surrogate key를 추가하되, 원래 조합의 유일성은 유지한다.

> Q: `id` PK만 있는 연결 테이블에서 자주 빠지는 제약은 무엇인가요?
> 의도: surrogate key 도입 시 놓치기 쉬운 무결성 규칙을 아는지 확인
> 핵심: `(fk1, fk2)` 유니크 제약이 빠져 같은 연결 중복 저장이 허용될 수 있다.

## 한 줄 정리

N:M 관계는 연결 자체를 별도 row로 저장하는 join table로 풀고, 연결의 정체가 두 FK 조합이라면 composite PK를 기본값으로 보며, surrogate key는 정말 필요한 경우에만 유일성 제약과 함께 추가하는 것이 안전하다.
