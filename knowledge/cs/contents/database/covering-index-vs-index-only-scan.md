# Covering Index vs Index-Only Scan

> 한 줄 요약: MySQL `Using index`는 보통 "이 조회가 인덱스 값만으로 답이 되나"를 읽는 신호이고, PostgreSQL `Index Only Scan`은 "이번 실행에서 heap 재방문을 얼마나 줄였나"를 읽는 plan node라서 같은 칸에 놓고 바로 번역하면 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)
- [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- [인덱스 기초 (Index Basics)](./index-basics.md)
- [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: covering index vs index only scan, using index meaning, mysql using index vs postgresql index only scan, explain checklist beginner, plan reading checklist, heap fetches basics, index only scan 뭐예요, using index 헷갈림, 왜 using index인데도 느려요, why heap fetches remain, covering index beginner, beginner explain reading, what is index only scan

## 핵심 개념

초보자가 가장 많이 섞는 질문은 이것이다.

- "`Using index`면 PostgreSQL `Index Only Scan`이랑 같은 말 아닌가요?"
- "둘 다 인덱스만 읽는다는 뜻 아닌가요?"

안전한 첫 답은 "비슷한 방향의 좋은 신호일 수는 있지만, 같은 층의 용어는 아니다"이다.

- covering index: 쿼리에 필요한 컬럼이 인덱스 안에 다 들어 있는 설계
- MySQL `Using index`: MySQL `EXPLAIN`의 `Extra`에서 보는 신호
- PostgreSQL `Index Only Scan`: PostgreSQL 실행 계획 node 이름

즉 먼저 "컬럼 설계"와 "실행 계획"을 분리해서 읽어야 한다.
비유하자면 covering index는 "재료를 가방에 다 챙겼나"이고, index-only scan은 "이번 이동에서 창고를 다시 안 갔나"에 가깝다. 다만 실제 엔진 동작은 가방과 창고 같은 단순 비유보다 더 복잡하므로, 비유는 설계와 실행을 분리하는 시작점까지만 유효하다.

## 한눈에 보기

| plan-reading 질문 | MySQL에서 먼저 보는 말 | PostgreSQL에서 먼저 보는 말 | 바로 따라붙는 체크 |
| --- | --- | --- | --- |
| 필요한 컬럼이 인덱스에 다 있나 | `Extra: Using index` 가능성 | `Index Only Scan` 후보 여부 | `SELECT *`인지, 필요한 컬럼이 늘었는지 |
| 이번 실행에서 테이블 본문 접근을 줄였나 | secondary lookup이 줄었는지 | `Heap Fetches`가 남았는지 | 실행 시간, rows, buffers/heap 재확인 |
| 이 신호를 무조건 좋은 결과로 봐도 되나 | 아니다. row 수와 정렬 비용은 남을 수 있다 | 아니다. visibility 확인 때문에 heap을 다시 볼 수 있다 | 다른 병목이 같이 남는지 |

짧게 외우면 아래 두 줄이면 된다.

```text
MySQL `Using index` = 인덱스 값만으로 답을 만들 가능성이 큰가
PostgreSQL `Index Only Scan` = 이번 실행에서 heap 재방문을 줄이는 경로를 탔는가
```

## 표준 읽기 순서 카드

실행 계획에서 둘을 만나면 아래 순서로 읽으면 된다.

1. 엔진부터 분리한다.
   MySQL `EXPLAIN Extra`인지, PostgreSQL plan node인지 먼저 확인한다.
2. 필요한 컬럼이 인덱스에 다 있는지 본다.
   `SELECT *`, 계산식, 추가 DTO 컬럼 때문에 covering이 깨졌는지 본다.
3. "실제로 본문 재방문이 줄었나"를 따로 본다.
   MySQL은 lookup 수와 row 수를, PostgreSQL은 `Heap Fetches`와 heap 관련 buffer 접근을 같이 본다.
4. 신호를 절대화하지 않는다.
   `Using index`가 있어도 row를 너무 많이 읽으면 느릴 수 있고, PostgreSQL `Index Only Scan`이어도 visibility 확인 때문에 heap 접근이 남을 수 있다.
5. 다음 행동을 결정한다.
   컬럼 구성이 문제면 인덱스/조회 컬럼을 다시 보고, PostgreSQL에서 `Heap Fetches`가 크면 vacuum/visibility 문맥까지 이어 본다.

이 카드의 핵심은 "`Using index`를 보면 컬럼 구성을 먼저", "`Index Only Scan`을 보면 `Heap Fetches`를 같이" 보는 습관이다.

## 상세 분해

### 1. MySQL `Using index`를 읽는 기본선

MySQL, 특히 InnoDB 문맥에서는 `Using index`를 보면 "이 조회가 인덱스 리프에 있는 값만으로 답을 만들 수 있나"를 먼저 떠올리면 된다.

예를 들어 아래처럼 필요한 컬럼이 인덱스에 모두 있으면 커버링 쪽 신호가 될 수 있다.

```sql
EXPLAIN
SELECT user_id, status, created_at
FROM orders
WHERE user_id = 10
ORDER BY created_at DESC
LIMIT 20;
```

하지만 `Using index`가 보여도 아래는 별개다.

- 읽는 row 수가 너무 많은가
- `ORDER BY`가 여전히 비싼가
- 인덱스 폭이 커져 write 비용이 늘었는가

즉 MySQL에서는 `Using index`를 "좋은 출발 신호"로 읽되, "무조건 가장 빠른 상태"라고 단정하면 안 된다.

### 2. PostgreSQL `Index Only Scan`을 읽는 기본선

PostgreSQL에서는 `Index Only Scan`이라는 node 이름이 직접 보인다.
이때 초보자가 바로 놓치는 숫자가 `Heap Fetches`다.

이 node는 "가능하면 인덱스만으로 끝내려는 경로"를 뜻하지만, PostgreSQL의 MVCC visibility 확인 때문에 heap 재확인이 남을 수 있다. 특히 page가 all-visible로 충분히 표시되지 않았으면 heap을 다시 볼 수 있다.

그래서 PostgreSQL에서는 아래처럼 묶어 읽는 편이 안전하다.

- `Index Only Scan`이 보였나
- `Heap Fetches`가 0에 가까운가
- `BUFFERS`나 실행 시간상 heap 재확인이 체감 병목인가

즉 PostgreSQL에서는 node 이름 하나보다 "heap을 정말 덜 읽었나"를 끝까지 확인해야 한다.

### 3. 둘을 같은 말로 번역하면 생기는 오해

| 자주 하는 말 | 왜 틀어지나 | 더 안전한 표현 |
| --- | --- | --- |
| "`Using index` = `Index Only Scan`이죠?" | MySQL의 `Extra` 신호와 PostgreSQL node 이름을 같은 층으로 묶는다 | 둘 다 본문 접근을 줄이는 쪽 신호일 수 있지만, 읽는 위치와 조건이 다르다 |
| "covering index를 만들었으니 PostgreSQL도 heap을 안 보겠죠?" | 설계와 실행을 섞는다 | covering은 후보 조건이고, 실제 heap 생략은 visibility와 실행 결과를 같이 본다 |
| "`Index Only Scan`이면 무조건 빠르죠?" | heap fetch와 row 수를 놓친다 | `Heap Fetches`, rows, buffers를 같이 봐야 한다 |

## 흔한 오해와 함정

- "`Using index`가 보이면 튜닝 끝이다"
  아니다. row 수가 크거나 정렬/범위 스캔이 크면 여전히 느릴 수 있다.
- "`Index Only Scan`이면 heap을 절대 안 읽는다"
  아니다. PostgreSQL에서는 visibility 확인 때문에 heap 재확인이 남을 수 있다.
- "covering index와 index-only scan은 같은 단어의 영어/영어 차이일 뿐이다"
  아니다. covering은 설계 관점, index-only scan은 실행 경로 관점이다.
- "`SELECT *`여도 인덱스만 잘 만들면 커버링이 된다"
  보통은 아니다. 필요한 컬럼이 많아지면 커버링이 쉽게 깨진다.

## 실무에서 쓰는 모습

목록 API를 본다고 하자.

```sql
SELECT user_id, status, created_at
FROM orders
WHERE user_id = 10
ORDER BY created_at DESC
LIMIT 20;
```

이 쿼리를 볼 때 초보자는 아래처럼 읽으면 된다.

- MySQL `EXPLAIN`에서 `Using index`가 보이면 "인덱스 컬럼만으로 답이 되나"를 먼저 본다.
- PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)`에서 `Index Only Scan`이 보이면 "`Heap Fetches`가 얼마나 남았나"를 바로 같이 본다.
- 둘 다 plan이 좋아 보여도 실제 row 수가 크면 latency가 기대만큼 줄지 않을 수 있다.

follow-up이 아래처럼 갈리면 다음 문서가 안전하다.

- "`Using index`인데도 왜 느려요?" -> [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- "`Index Only Scan`인데 `Heap Fetches`가 왜 남아요?" -> [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- "MySQL 감각이 PostgreSQL에서 왜 안 맞죠?" -> [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)

## 더 깊이 가려면

- MySQL의 커버링 설계와 복합 인덱스 순서를 더 보려면 [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- PostgreSQL에서 `Heap Fetches`가 남는 이유를 더 보려면 [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- 실행 계획을 처음부터 읽는 순서를 넓게 잡고 싶으면 [인덱스 기초 (Index Basics)](./index-basics.md)
- B+Tree 리프와 상단 인덱스 모양을 그림 감각으로 다시 보고 싶으면 [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)

## 면접/시니어 질문 미리보기

| 질문 | 의도 | 핵심 답 |
| --- | --- | --- |
| "`Using index`와 `Index Only Scan`의 차이를 한 문장으로 설명해 보세요." | 설계와 실행을 분리하는지 본다 | MySQL 신호와 PostgreSQL 실행 노드를 분리해서 설명한다 |
| "PostgreSQL에서 `Index Only Scan`인데도 왜 느릴 수 있나요?" | visibility와 heap 재확인을 연결하는지 본다 | `Heap Fetches`와 heap buffer 재방문이 남을 수 있다고 답한다 |
| "covering index를 넓히면 항상 좋은가요?" | 읽기 최적화와 쓰기 비용 균형을 보는지 본다 | 읽기는 좋아질 수 있지만 인덱스 폭과 유지 비용이 늘 수 있다고 답한다 |

## 한 줄 정리

`Using index`는 "인덱스 컬럼만으로 답이 되는가"를 읽는 MySQL 쪽 신호이고, `Index Only Scan`은 "이번 실행에서 heap을 얼마나 생략했는가"를 읽는 PostgreSQL 쪽 실행 경로다.
