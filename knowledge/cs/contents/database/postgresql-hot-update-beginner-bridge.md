# PostgreSQL `HOT update`는 뭐예요?

> 한 줄 요약: PostgreSQL의 `HOT update`는 `UPDATE`가 생겨도 새 row 버전을 같은 heap page 안에 붙여 두고 index 재작업을 줄이려는 경로라서, 초급에서는 "heap page 여유 공간이 있으면 write churn이 index까지 덜 번질 수 있다"는 뜻으로 이해하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)
- [PostgreSQL `visibility map`과 `all-visible`은 뭐예요?](./postgresql-visibility-map-all-visible-beginner-card.md)
- [HOT UPDATE와 Secondary Index Churn](./hot-update-secondary-index-churn.md)
- [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: postgresql hot update basics, hot update what is, hot update beginner, heap only tuple intro, why fillfactor and hot update, heap page free space basics, write churn postgres, why update touches index, hot update 처음, hot update 뭐예요, why postgres update got expensive, indexed column hot update

## 핵심 개념

PostgreSQL 저장 구조를 처음 보면 이런 질문이 자주 나온다.

- "왜 PostgreSQL에서는 `fillfactor`와 `HOT update`를 같이 말해요?"
- "`UPDATE` 한 번인데 왜 index churn 이야기까지 나오죠?"

초급에서는 먼저 아래 한 줄만 고정하면 된다.

> `HOT update`는 가능하면 **같은 heap page 안에서 새 row 버전을 이어 붙여 index 재작업을 덜 하려는 경로**다.

여기서 `HOT`는 `Heap-Only Tuple`의 줄임말이다.
다만 이름 때문에 "heap만 바꾸고 나머지는 완전히 공짜다"라고 이해하면 안 된다.
핵심은 "항상 되는 마법"이 아니라, **같은 page에 여유 공간이 있고 index 쪽을 다시 건드리지 않아도 되는 조건일 때** write churn을 줄일 수 있는 선택지라는 점이다.

## 한눈에 보기

| 상황 | 초보자용 첫 해석 | write churn 쪽 의미 |
| --- | --- | --- |
| 같은 heap page에 자리 있음 + 바뀌는 컬럼이 index key에 안 걸림 | `HOT update`가 될 가능성이 있다 | index 재작업이 줄 수 있다 |
| 같은 page가 너무 빡빡함 | 새 버전이 page 밖으로 밀릴 수 있다 | page 이동과 추가 작업이 늘 수 있다 |
| 바뀌는 컬럼이 index에 걸려 있음 | 보통 `HOT update`가 어렵다 | index도 다시 고쳐야 한다 |

```text
안전한 멘탈모델
1. postgres는 update 때 새 tuple 버전을 만든다
2. 같은 heap page에 남길 수 있으면 더 싸게 끝날 수 있다
3. 그 경로를 막는 대표 원인은 page 여유 부족과 indexed column 변경이다
```

## heap page 여유 공간과 왜 붙어 나오나요?

`HOT update`는 "새 row 버전을 어디에 둘 수 있나"와 직결된다.
PostgreSQL은 `UPDATE`를 하면 기존 row를 덮어쓰기보다 새 버전을 만드는 쪽으로 이해하는 편이 초급자에게 안전하다.

이때 같은 heap page 안에 빈자리가 있으면 새 버전을 근처에 둘 여지가 생긴다.
그래서 `fillfactor`가 같이 등장한다.

- `fillfactor`: page를 처음부터 너무 꽉 채우지 말고, 나중 `UPDATE`를 위한 여유를 조금 남기는 설정
- page 여유 공간이 있으면: 같은 page 안에 새 버전을 둘 가능성이 커진다
- page 여유 공간이 없으면: page 밖으로 밀리거나 index 재작업이 더 쉽게 붙는다

비유로는 "책장 같은 칸에 수정 메모를 옆에 끼워 넣을 자리" 정도로 생각하면 된다.
다만 이 비유는 page 안 공간 감각까지만 맞고, 실제로는 MVCC row version과 index 조건이 같이 걸리므로 "빈칸만 있으면 무조건 HOT"이라고 일반화하면 안 된다.

## write churn과 왜 연결되나요?

초보자가 `write churn`을 읽을 때는 "같은 row나 page를 자주 바꿔서 저장 구조가 계속 흔들리는 상태" 정도로 잡으면 충분하다.

`HOT update`가 반가운 이유는, update-heavy workload에서 churn이 바로 index까지 번지는 일을 줄여 줄 수 있기 때문이다.

| 질문 | `HOT update` 관점에서 보는 첫 답 |
| --- | --- |
| `UPDATE`가 잦으면 왜 느려지죠? | 새 row 버전이 계속 생기고, 경우에 따라 index도 같이 다시 고쳐야 해서다 |
| 왜 어떤 테이블은 update가 특히 비싸죠? | page 여유 공간이 부족하거나, 자주 바뀌는 컬럼이 index에 걸려 있을 수 있다 |
| 왜 queue/heartbeat 테이블에서 이 말을 자주 보죠? | status, timestamp 같은 값이 자주 바뀌어 write churn이 크기 쉽기 때문이다 |

즉 PostgreSQL 쪽 첫 감각은 "PK가 row를 어디에 붙여 놓나"보다,
"이 update가 같은 heap page 근처에 남을 수 있나, 아니면 index churn까지 번지나"에 더 가깝다.

## 작은 예시로 보면

예를 들어 이런 테이블이 있다고 하자.

```sql
CREATE TABLE session_heartbeat (
  id BIGINT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  last_seen_at TIMESTAMP NOT NULL,
  note TEXT
);
```

그리고 `last_seen_at`을 계속 갱신한다.

```sql
UPDATE session_heartbeat
SET last_seen_at = NOW()
WHERE id = 10;
```

초급에서는 아래처럼 질문을 자르면 된다.

| 먼저 볼 것 | 왜 보나 |
| --- | --- |
| `last_seen_at`이 index key에 포함돼 있나 | 포함돼 있으면 `HOT update`가 어려워질 수 있다 |
| heap page에 update 여유 공간이 남아 있나 | 같은 page 안에 새 버전을 둘 가능성과 연결된다 |
| 이 테이블이 write-heavy인가 | churn이 큰 테이블일수록 `HOT update` 여부 체감이 커진다 |

반대로 `note`처럼 index에 안 걸린 컬럼을 가끔 바꾸는 경우는
같은 page 여유만 있다면 더 유리한 경로가 열릴 수 있다.

핵심은 "`UPDATE`는 다 똑같이 비싸다"가 아니라,
"어떤 컬럼을 얼마나 자주 바꾸고, 그 컬럼이 index와 page 여유 공간에 어떻게 걸리나"를 같이 본다는 점이다.

## 흔한 오해와 함정

- "`HOT update`면 index를 절대 안 건드린다" -> 보통 그 방향의 최적화지만, 조건이 안 맞으면 그냥 일반 update 경로로 간다.
- "빈 공간만 있으면 무조건 `HOT update`다" -> 아니다. 바뀌는 컬럼이 index key에 걸리면 막힐 수 있다.
- "`fillfactor`만 낮추면 다 해결된다" -> 아니다. 읽기 밀도와 공간 효율 trade-off가 있고, indexed column 변경이 많으면 한계가 있다.
- "`HOT update`는 PostgreSQL이면 항상 자동으로 잘 된다" -> 아니다. 테이블 구조와 update 패턴에 따라 체감이 크게 달라진다.
- "`HOT update`면 vacuum이나 visibility는 상관없다" -> 아니다. row version이 계속 생기는 MVCC 문맥은 그대로 남는다.

## 다음에 무엇을 보면 되나요?

처음에는 운영 지표를 다 외우지 말고, 아래 순서면 충분하다.

1. PostgreSQL 저장 구조 감각이 아직 흐리면 [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)부터 다시 본다.
2. `HOT update`가 막히면 왜 secondary index churn으로 번지는지 보고 싶다면 [HOT UPDATE와 Secondary Index Churn](./hot-update-secondary-index-churn.md)로 넘어간다.
3. 같은 PostgreSQL storage follow-up에서 `visibility map`, `Heap Fetches`가 같이 헷갈리면 [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)를 잇는다.

주니어 단계의 안전한 다음 한 줄은 이것이다.

> write-heavy PostgreSQL 테이블을 볼 때는 "index가 있나?" 다음으로 "같은 heap page에 새 버전을 남길 여유가 있나?"를 같이 본다.

## 한 줄 정리

PostgreSQL의 `HOT update`는 같은 heap page 안에 새 row 버전을 남겨 index churn을 줄이려는 경로라서, 초급에서는 `fillfactor`, page 여유 공간, indexed column 변경 여부를 함께 보는 개념으로 이해하면 된다.
