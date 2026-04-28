# MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지

> 한 줄 요약: InnoDB에서는 primary key 순서가 row 저장 위치 감각과 거의 붙어 있지만, PostgreSQL은 heap row와 index가 기본적으로 분리돼 있어서 `CLUSTER`를 한 번 실행해도 "PK를 타면 본문도 항상 같이 정렬돼 있다"는 기본 저장 모델이 되지는 않는다.

**난이도: 🟢 Beginner**

관련 문서:

- [인덱스 기초 (Index Basics)](./index-basics.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [Clustered Index Locality](./clustered-index-locality.md)
- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [database 카테고리 인덱스](./README.md)
- [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)

retrieval-anchor-keywords: mysql vs postgresql index storage, innodb clustered index beginner, postgresql heap index basics, why mysql intuition fails in postgres, postgres cluster one time reorder, postgres primary key도 clustered인가요, postgresql cluster 뭐예요, heap table 뭐예요, index only scan basics, using index vs index only scan, mysql using index postgres index only scan, 처음 배우는 mysql postgresql index, why pk lookup feels different, clustered vs heap storage, 헷갈리는 저장 구조

## 핵심 개념

MySQL InnoDB를 먼저 배우면 "primary key를 따라가면 row 본문이 바로 붙어 있다"는 감각이 생긴다.  
이 감각은 InnoDB 안에서는 유용하지만, PostgreSQL까지 그대로 들고 가면 자주 헷갈린다.

핵심 차이는 저장 구조다.

- InnoDB: primary key leaf 쪽에 row 본문이 같이 붙어 있는 clustered 구조
- PostgreSQL: table heap과 index가 기본적으로 분리된 구조

그래서 같은 "index를 탄다"라는 말이어도, 두 엔진이 실제로 row를 찾는 방식은 다르게 생각해야 한다.

## 한눈에 보기

| 질문 | MySQL InnoDB | PostgreSQL |
| --- | --- | --- |
| 테이블 본문은 어디에 가까운가 | primary key clustered leaf 쪽 감각으로 이해하기 쉽다 | heap page에 row가 있고 index는 그 위치를 가리킨다 |
| primary key index = 테이블 저장 순서인가 | 거의 그렇다고 배워도 큰 틀에서 맞다 | 기본값으로는 아니다 |
| `CLUSTER`를 한 번 실행하면 그 뒤도 계속 정렬되나 | clustered 구조 자체라 PK 기준 locality가 기본 모델에 가깝다 | 아니다. 그 시점에 heap을 다시 써 주는 작업이지 기본 저장 모델 변경은 아니다 |
| secondary index를 타면 | 필요 시 primary key로 한 번 더 본문을 찾는다 | 필요 시 heap으로 가서 row visibility까지 확인한다 |
| 입문자가 자주 하는 착각 | "PK면 물리 정렬이 자동으로 다 해결된다" | "PK index가 있으니 InnoDB처럼 clustered겠지" |

```text
안전한 첫 문장
- InnoDB: PK가 테이블 저장 축에 가깝다
- PostgreSQL: index와 heap이 기본적으로 분리돼 있다
```

## 짧은 용어 브리지

초보자라면 먼저 이렇게 번역해서 읽으면 된다.

| plan에서 보인 말 | 초보자용 첫 해석 | 바로 붙이면 안 되는 말 |
| --- | --- | --- |
| MySQL `Using index` | "이 조회는 인덱스에 있는 값만으로 답을 만들 가능성이 크다" | "PostgreSQL `Index Only Scan`과 완전히 같은 뜻이다" |
| PostgreSQL `Index Only Scan` | "실행 계획상 heap 본문을 안 읽고 끝내려는 경로다" | "MySQL `Using index`와 같은 wording이니까 같은 내부 동작이다" |

핵심은 둘 다 "인덱스를 잘 쓴다"는 방향의 신호일 수는 있어도, **같은 용어 번역본은 아니라는 점**이다.

- `Using index`: MySQL `EXPLAIN`의 `Extra`에 보이는 표현
- `Index Only Scan`: PostgreSQL plan node 이름

짧게 외우면 아래 한 줄이면 충분하다.

```text
MySQL `Using index` = 커버링 쪽 신호
PostgreSQL `Index Only Scan` = heap 생략 실행 경로 이름
```

## 상세 분해

### 1. InnoDB에서 clustered index 직관이 생기는 이유

InnoDB는 primary key leaf에 row 본문이 같이 들어 있는 쪽으로 이해하면 된다.  
그래서 `id BETWEEN ...` 같은 범위 조회를 볼 때 "PK 순서 근처 데이터가 같이 모여 있겠구나"라는 locality 감각이 자연스럽다.

이 직관 덕분에 입문자는 아래를 쉽게 연결한다.

- primary key 설계가 쓰기 패턴에 영향을 준다
- secondary index lookup 뒤 primary key 재탐색 비용이 남을 수 있다
- PK 범위 조회가 물리적으로도 비교적 자연스럽다

### 2. PostgreSQL은 왜 같은 설명이 바로 안 맞나

PostgreSQL은 기본적으로 table heap과 index가 분리돼 있다.  
index는 "이 key에 해당하는 row가 heap의 어디쯤 있다"는 길잡이 역할을 하고, 실제 row 본문은 heap에서 읽는다.

그래서 PostgreSQL에서 primary key index가 있다고 해서 곧바로 "테이블 자체가 PK 순서로 저장된다"라고 말하면 과장이다.  
입문 단계에서는 "PostgreSQL의 PK도 인덱스이지만, InnoDB clustered index와 같은 저장 구조는 아니다"라고 끊어 말하는 편이 안전하다.

### 3. 왜 PostgreSQL에서 heap 확인 이야기가 자주 나오나

PostgreSQL은 MVCC visibility 확인까지 생각해야 한다.  
그래서 index에 필요한 컬럼이 다 있어 보여도, 실제 실행에서는 heap fetch가 남을 수 있다.

이때 입문자가 기억할 최소 문장은 아래 정도면 충분하다.

- InnoDB의 covering 감각과 PostgreSQL의 index-only scan은 같은 말이 아니다
- PostgreSQL은 visibility map 상태에 따라 heap 방문이 다시 생길 수 있다

즉 PostgreSQL에서 "인덱스만 읽는다"는 말은 저장 구조와 MVCC 조건을 함께 봐야 한다.

## PostgreSQL `CLUSTER` 오해 끊기

### 1. 왜 보조 작업으로 봐야 하나

`CLUSTER table_name USING some_index;`는 "지금 이 순간 heap row를 그 index 순서에 맞춰 다시 써 보자"에 가깝다.  
즉 **한 번 재정렬해 주는 maintenance 작업**이지, InnoDB처럼 "앞으로 들어오는 row도 계속 그 구조로 저장된다"는 기본 모델 전환이 아니다.

초보자는 아래 표만 기억해도 충분하다.

| 질문 | 안전한 첫 답 |
| --- | --- |
| PostgreSQL에도 `CLUSTER`가 있는데 clustered index 아닌가요? | 이름은 비슷하지만 기본 저장 모델은 여전히 heap + index다 |
| `CLUSTER` 한 번 했으면 계속 PK 순서인가요? | 아니다. 이후 INSERT/UPDATE가 쌓이면 다시 흐트러질 수 있다 |
| 그럼 `CLUSTER`는 언제 떠올리나요? | 기본 개념이라기보다 "한 번 정리"가 필요한 운영/성능 작업으로 본다 |

즉 입문 단계에서는 "`CLUSTER`가 있으니 PostgreSQL도 InnoDB clustered index와 같다"가 아니라,  
"PostgreSQL은 heap 기반이고 `CLUSTER`는 그 heap을 한 번 재배치하는 도구"라고 끊어 이해하면 된다.

## 그래서 처음엔 무엇을 같은 선에 놓고 보면 되나

입문 단계에서는 아래처럼 짝을 맞추면 덜 헷갈린다.

| 비교하려는 것 | MySQL에서 먼저 볼 말 | PostgreSQL에서 먼저 볼 말 |
| --- | --- | --- |
| "이 조회가 인덱스 컬럼만으로 답이 되나?" | `Using index` | 필요한 컬럼이 인덱스에 다 있는지 + `Index Only Scan` 후보인지 |
| "실제로 테이블/heap 본문을 덜 읽었나?" | 실행 시간, rows, 추가 lookup 여부 | `Index Only Scan` + `Heap Fetches` |

즉 `Using index`와 `Index Only Scan`을 1:1 사전 번역처럼 붙이기보다,  
"둘 다 본문 접근을 줄이는 쪽 신호인데 보는 층이 다르다"라고 이해하는 편이 안전하다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀어지나 | 더 안전한 표현 |
| --- | --- | --- |
| "PostgreSQL primary key도 clustered index죠?" | PK 인덱스 존재와 테이블 저장 구조를 섞는다 | "PK 인덱스는 있지만 기본 저장은 heap + index 구조다" |
| "PostgreSQL도 `CLUSTER` 있으니 InnoDB clustered index랑 같은 거죠?" | 재정렬 명령과 기본 저장 모델을 섞는다 | "`CLUSTER`는 한 번 heap 순서를 다시 맞추는 도구지 기본 구조 자체는 아니다" |
| "MySQL에서 빠른 PK range scan이면 PostgreSQL도 같은 이유로 빠르겠죠?" | 같은 성능 결과가 나와도 저장 구조 설명은 다를 수 있다 | 실행 계획과 heap 접근 여부를 따로 본다 |
| "`Using index`와 `Index Only Scan`은 같은 말이죠?" | 커버링 설계와 실제 heap 생략 실행을 섞는다 | MySQL 신호와 PostgreSQL 실행 노드를 분리해서 읽는다 |
| "primary key를 타면 본문은 항상 바로 옆에 있죠?" | InnoDB 직관을 모든 엔진에 일반화한다 | 엔진별 row 저장 위치부터 먼저 확인한다 |

초급에서 중요한 건 모든 내부 구현을 외우는 게 아니라, **엔진이 다르면 저장 구조 설명도 달라진다**는 경계선을 먼저 세우는 것이다.

## 실무에서 쓰는 모습

예를 들어 주문 목록 API를 본다고 하자.

```sql
SELECT id, member_id, created_at
FROM orders
WHERE id BETWEEN 1000 AND 1100;
```

InnoDB에서는 "PK 범위와 row 배치 locality가 어느 정도 붙어 있겠다"는 직관으로 접근하기 쉽다.  
반면 PostgreSQL에서는 같은 SQL을 보더라도 "어떤 index path를 탔고, heap을 얼마나 다시 읽는가"까지 한 단계 더 분리해 생각한다.

만약 운영 중에 PostgreSQL에서 `CLUSTER orders USING orders_pkey;`를 한 번 실행했다 해도,  
그건 "지금 row 배치를 다시 정리했다"는 뜻에 가깝다. 이후 쓰기가 계속 들어오면 InnoDB PK clustered처럼 자동 유지된다고 기대하면 안 된다.

또 다른 예시는 목록 API의 covering/index-only scan 혼동이다.

- MySQL에서 `Using index`를 보면 "secondary index만으로 답을 만들었나?"를 먼저 본다
- PostgreSQL에서 `Index Only Scan`을 보면 "heap fetch가 정말 줄었나?"를 같이 본다

그래서 엔진을 옮겨 갈 때는 SQL 문법보다 먼저 **저장 구조 mental model**을 다시 맞추는 편이 덜 헷갈린다.

## 더 깊이 가려면

- InnoDB에서 PK locality가 왜 중요한지 더 보려면 [Clustered Index Locality](./clustered-index-locality.md)
- MySQL `Using index`와 PostgreSQL `Index Only Scan` 차이를 plan 관점에서 더 보려면 [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- PostgreSQL에서 heap 방문과 재정렬 이후 write churn을 함께 보려면 [HOT UPDATE와 Secondary Index Churn](./hot-update-secondary-index-churn.md)
- 인덱스, secondary lookup, `EXPLAIN`의 기본 감각부터 다시 잡으려면 [인덱스 기초 (Index Basics)](./index-basics.md)
- leaf/page locality를 자료구조 관점에서 더 넓게 보려면 [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)

## 면접/시니어 질문 미리보기

> Q: 왜 InnoDB clustered index 직관을 PostgreSQL에 그대로 옮기면 안 되나요?  
> 의도: index 존재와 row 저장 구조를 구분하는지 확인  
> 핵심: PostgreSQL은 기본적으로 heap과 index가 분리돼 있어서 PK index가 곧 테이블 저장 순서를 뜻하지 않는다.

> Q: PostgreSQL에서 index-only scan을 볼 때 heap fetch를 같이 보는 이유는 무엇인가요?  
> 의도: MVCC visibility 조건을 알고 있는지 확인  
> 핵심: 인덱스만으로 컬럼이 충분해 보여도 visibility 확인 때문에 heap 접근이 남을 수 있다.

> Q: MySQL에서 secondary index가 빨라 보여도 왜 PK 재탐색 얘기가 나오나요?  
> 의도: clustered/secondary 차이를 설명할 수 있는지 확인  
> 핵심: secondary index leaf만으로 부족하면 primary key 쪽 본문으로 한 번 더 내려가야 하기 때문이다.

> Q: PostgreSQL `CLUSTER`와 InnoDB clustered index를 왜 같은 말로 보면 안 되나요?  
> 의도: one-time reorder와 default storage model을 구분하는지 확인  
> 핵심: PostgreSQL `CLUSTER`는 heap을 한 번 다시 쓰는 작업이고, InnoDB clustered index처럼 기본 row 저장 구조가 계속 유지되는 모델은 아니다.

## 한 줄 정리

InnoDB는 "PK가 테이블 저장 축"에 가깝고 PostgreSQL은 "heap과 index가 분리된 구조"에 가깝기 때문에, PostgreSQL의 `CLUSTER`까지 봐도 그것을 InnoDB clustered index와 같은 기본 저장 모델로 이해하면 안 된다.
