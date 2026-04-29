# PostgreSQL `visibility map`과 `all-visible`은 뭐예요?

> 한 줄 요약: `visibility map`은 PostgreSQL이 "이 heap page는 지금 heap 본문을 다시 안 봐도 될 가능성이 높다"라고 빠르게 표시해 두는 메모이고, `all-visible`은 그 page의 tuple들이 현재 모든 스냅샷에서 보일 수 있다고 정리된 상태를 뜻한다.

**난이도: 🟢 Beginner**

관련 문서:

- [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)
- [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: postgresql visibility map basics, all-visible meaning, visibility map what is, why heap fetches remain, mvcc visibility beginner, vacuum all visible basics, postgresql page visibility, index only scan follow up, visibility map 처음, all visible 뭐예요, why postgres still reads heap, beginner visibility map, autovacuum visibility map beginner, vacuum why index only scan improved

## 핵심 개념

`Heap Fetches` 설명을 읽고도 막히는 지점은 보통 여기다.
"그래서 visibility map이 정확히 뭐고, all-visible은 무슨 체크인가?"

초급에서는 아주 단순하게 잡으면 된다.

- heap page: row 본문이 들어 있는 페이지
- `visibility map`: "이 페이지는 지금 다시 열어보지 않아도 될 가능성이 큰가?"를 빠르게 적어 둔 메모
- `all-visible`: 그 페이지의 tuple들이 현재 visibility 규칙상 모두 보여도 된다고 정리된 상태

즉 `all-visible`은 "영원히 안 바뀐다"가 아니라, **지금 시점에는 heap 재확인 없이 지나갈 가능성이 크다**는 뜻에 가깝다.

## 한눈에 보기

| 용어 | 초보자용 멘탈모델 | 실행 계획에서 체감되는 변화 |
| --- | --- | --- |
| `visibility map` | heap 옆의 체크 메모 | heap 재확인이 줄 수 있다 |
| page가 `all-visible` | "이 page는 다시 안 열어봐도 될 가능성이 높다" | `Heap Fetches`가 줄기 쉽다 |
| page가 `all-visible` 아님 | "혹시 안 보이는 row가 있을 수 있으니 다시 확인" | heap 방문이 다시 붙기 쉽다 |

```text
안전한 순서
1. index가 후보 row를 찾는다
2. postgres가 visibility map으로 page 상태를 본다
3. all-visible이 아니면 heap에서 실제 visibility를 다시 확인한다
```

## 상세 분해

`visibility map`은 row마다 붙는 메모가 아니라 **page 단위 메모**다.
그래서 어떤 row 하나만 보고 "이 row는 보여요"라고 적는 게 아니라,
"이 page 전체는 지금 all-visible로 취급할 수 있나?"를 본다.

여기서 `all-visible`은 "누구에게나 영원히 보인다"가 아니다.
최근 `UPDATE`나 `DELETE`가 생기면 그 page는 다시 조심해야 하므로,
이 표식이 깨지고 heap 재확인이 다시 필요해질 수 있다.

초급자가 붙잡아야 할 핵심은 하나다.

> index가 필요한 컬럼을 갖고 있어도, page가 all-visible이 아니면 PostgreSQL은 heap 확인을 다시 붙일 수 있다.

## 흔한 오해와 함정

- "`all-visible`이면 row가 아예 고정됐다" -> 아니다. 나중에 쓰기가 생기면 상태가 다시 바뀔 수 있다.
- "`visibility map`은 row 하나하나의 visible 여부를 적어 둔다" -> 아니다. page 단위 메모다.
- "`all-visible`이면 MVCC를 안 쓴다" -> 아니다. MVCC 규칙은 그대로고, 재확인을 줄이는 힌트가 생긴 것뿐이다.
- "`Heap Fetches`가 있으면 visibility map이 고장 났다" -> 꼭 그렇지 않다. 최근 쓰기나 vacuum 타이밍 때문에 자연스럽게 생길 수 있다.

## 실무에서 쓰는 모습

예를 들어 `EXPLAIN ANALYZE`에서 아래처럼 보였다고 하자.

```text
Index Only Scan using idx_orders_status_created_at on orders
Heap Fetches: 37
```

이때 첫 해석은 "인덱스가 틀렸다"가 아니라 아래 쪽이 더 안전하다.

| 관찰 | 초급 해석 | 바로 이어질 질문 |
| --- | --- | --- |
| `Index Only Scan` | 인덱스만으로 끝내는 경로를 우선 탔다 | 필요한 컬럼은 인덱스에 다 있었나? |
| `Heap Fetches: 37` | 일부 page는 all-visible이 아니라 heap 재확인이 붙었다 | 최근 쓰기 churn이나 vacuum 지연이 있었나? |

그래서 follow-up은 보통 "인덱스를 다시 만들까?"보다
"이 테이블이 최근에 많이 바뀌었나, vacuum이 따라오고 있나?"를 먼저 보는 쪽이 맞다.

## autovacuum와 왜 연결되나요?

visibility map은 시간이 지나도 자동으로 항상 완벽하게 유지되는 메모가 아니다.
`UPDATE`나 `DELETE`가 생기면 어떤 page는 다시 조심해야 해서 `all-visible` 표식이 깨질 수 있고,
그 뒤 autovacuum나 `VACUUM`이 지나가며 정리해야 다시 heap 재확인을 덜 하게 된다.

초급에서는 아래 흐름만 기억하면 충분하다.

| 상황 | visibility map 쪽 변화 | `Index Only Scan`에 보이는 변화 |
| --- | --- | --- |
| 쓰기가 잦아짐 | `all-visible` page가 줄 수 있다 | `Heap Fetches`가 다시 늘 수 있다 |
| autovacuum가 제때 따라옴 | 정리된 page가 다시 늘 수 있다 | heap 재확인이 줄어 더 빨라질 수 있다 |
| autovacuum가 밀림 | 오래 `all-visible`로 못 돌아온 page가 남는다 | 같은 쿼리도 시간이 지나며 느려진 것처럼 보일 수 있다 |

즉 autovacuum는 "백그라운드 청소"라는 운영 용어로만 외우기보다,
**visibility map을 회복시켜 index-only scan이 다시 index 쪽에서 끝나게 도와주는 작업**으로 연결해서 보는 편이 이해가 빠르다.

## 더 깊이 가려면

- `Heap Fetches` 숫자를 plan에서 읽는 연습은 [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- MySQL `Using index`와 PostgreSQL `Index Only Scan`을 헷갈린다면 [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- dead tuple, autovacuum, heap fetch 회귀까지 같이 보고 싶다면 [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)

## 한 줄 정리

`visibility map`은 PostgreSQL이 heap page를 다시 열어볼 필요가 적은지 빠르게 판단하려고 쓰는 메모이고, `all-visible`은 그 page가 지금은 heap 재확인 없이 지나갈 가능성이 큰 상태라고 이해하면 된다.
