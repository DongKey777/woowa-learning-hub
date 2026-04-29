# PostgreSQL `EXPLAIN ANALYZE`에서 `actual rows`, `buffers`, `heap fetches`를 같이 읽는 법

> 한 줄 요약: `actual rows`는 "몇 row가 이 단계를 통과했는지", `buffers`는 "그 row를 위해 몇 page를 만졌는지", `heap fetches`는 "`Index Only Scan`인데도 heap 확인이 몇 번 남았는지"를 보여 주므로, 셋을 같이 보면 plan 출력이 한 장의 이야기로 이어진다.

**난이도: 🟢 Beginner**

관련 문서:

- [인덱스와 실행 계획](./index-and-explain.md)
- [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
- [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- [PostgreSQL `visibility map`과 `all-visible`은 뭐예요?](./postgresql-visibility-map-all-visible-beginner-card.md)
- [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)
- [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: postgresql explain analyze actual rows buffers heap fetches, explain analyze terms beginner, actual rows vs buffers, buffers 뭐예요, heap fetches 뭐예요, explain analyze 처음 헷갈려요, why heap fetches remain, actual rows why different, postgresql plan reading basics, explain analyze what is, index only scan heap fetches, buffers and heap fetches together

## 핵심 개념

이 문서는 `"EXPLAIN ANALYZE에서 actual rows, Buffers, Heap Fetches가 같이 나오는데 서로 무슨 관계예요?"` 같은 첫 질문을 풀기 위한 mini bridge다.

초보자는 보통 이 셋을 따로 외우다가 더 헷갈린다.
안전한 순서는 "몇 개를 통과시켰나 -> 그 과정에서 몇 page를 만졌나 -> 그중 heap 재확인이 몇 번 남았나"로 읽는 것이다.

- `actual rows`: 이 plan node가 실제 실행에서 몇 row를 내보냈는가
- `buffers`: 그 row를 만들기 위해 shared buffer page를 얼마나 만졌는가
- `heap fetches`: `Index Only Scan`이 heap 확인을 완전히 생략하지 못해 다시 내려간 횟수

즉 row 개수와 page 접근량과 heap 재확인을 한 줄로 붙여 보는 연습이 핵심이다.

## 한눈에 보기

| 용어 | 초보자용 질문 | 안전한 첫 해석 |
| --- | --- | --- |
| `actual rows` | "실제로 몇 row가 여기까지 왔지?" | 예상치가 아니라 실행 결과다 |
| `Buffers: shared hit/read` | "그 row를 위해 page를 얼마나 만졌지?" | row 수가 아니라 page touch 신호다 |
| `Heap Fetches` | "`Index Only Scan`인데 왜 heap도 봤지?" | visibility 확인이 남았을 수 있다 |

```text
actual rows = 통과한 row 수
buffers = 만진 page 양
heap fetches = index-only 경로에서 남은 heap 재확인
```

## 세 용어를 같이 읽는 30초 순서

처음에는 아래 3문장만 붙잡으면 된다.

1. `actual rows`로 "실제로 많이 읽었는가"를 본다.
2. `buffers`로 "row 수에 비해 page touch가 과한가"를 본다.
3. `Heap Fetches`가 있으면 "index-only인데 heap 재확인이 남았나"를 본다.

| 같이 보인 패턴 | 초보자용 첫 판단 | 다음 문서 |
| --- | --- | --- |
| `actual rows` 큼 + `buffers`도 큼 | 정말 많이 읽는 쿼리일 가능성이 크다 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) |
| `actual rows`는 작음 + `buffers`는 큼 | row 수보다 page 접근이 비싸다. 산재된 heap 접근, 정렬, 재확인을 의심한다 | [인덱스와 실행 계획](./index-and-explain.md), [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md) |
| `Index Only Scan` + `Heap Fetches` 큼 | 커버링처럼 보여도 visibility 때문에 heap을 다시 본다 | [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md) |
| estimate rows는 작았는데 `actual rows`만 큼 | 통계나 데이터 분포 추정이 빗나갔을 수 있다 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) |

## 작은 예시로 연결하기

예를 들어 plan 일부가 아래처럼 보였다고 하자.

```text
Index Only Scan using idx_orders_status_created_at on orders
  (actual rows=120 loops=1)
  Heap Fetches: 80
  Buffers: shared hit=210 read=12
```

이때 초보자용 해석은 이렇게 붙이면 된다.

| 관찰 | 첫 해석 | 왜 같이 봐야 하나 |
| --- | --- | --- |
| `actual rows=120` | 120 row를 실제로 내보냈다 | row 규모가 먼저 보인다 |
| `Buffers: shared hit=210 read=12` | 120 row를 위해 page touch가 꽤 많았다 | row 수보다 page 접근 비용이 크다는 신호다 |
| `Heap Fetches: 80` | 그중 많은 row/page는 heap visibility 재확인이 필요했다 | buffers가 큰 이유를 설명해 준다 |

즉 이 plan은 "120 row밖에 없으니 가볍다"로 끝내면 안 된다.
row 수는 작아 보여도, heap 재확인 때문에 page touch가 커질 수 있다는 연결이 중요하다.

## 흔한 오해와 함정

- `actual rows`가 작으면 항상 빠르다 -> 아니다. `buffers`가 크면 row는 적어도 page를 많이 만진다.
- `buffers`는 row 수다 -> 아니다. page cache나 disk에서 만진 블록 수에 가깝다.
- `Heap Fetches`가 보이면 index가 실패했다 -> 아니다. `Index Only Scan` 경로에서도 visibility 확인 때문에 남을 수 있다.
- `Heap Fetches`만 보면 충분하다 -> 아니다. `actual rows`, `buffers`를 같이 봐야 "왜 느린지"가 이어진다.
- `buffers read`만 위험하고 `shared hit`는 무시해도 된다 -> 아니다. hit도 CPU와 memory touch 비용을 뜻하므로 row 수 대비 과하면 단서가 된다.

## 다음으로 어디로 가야 하나

질문이 어디서 막혔는지에 따라 follow-up이 달라진다.

- "`actual rows`가 estimate와 왜 다르죠?"가 먼저면 [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md)
- "`Heap Fetches`가 왜 남죠?"가 먼저면 [PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?](./postgresql-index-only-scan-heap-fetches-beginner-card.md)
- `visibility map`, `all-visible`이 아직 추상적이면 [PostgreSQL `visibility map`과 `all-visible`은 뭐예요?](./postgresql-visibility-map-all-visible-beginner-card.md)
- plan 전체를 어디서부터 읽을지 다시 잡고 싶으면 [인덱스와 실행 계획](./index-and-explain.md)

## 면접/시니어 질문 미리보기

| 질문 | 의도 | 핵심 답변 |
| --- | --- | --- |
| `actual rows`와 `rows` estimate를 왜 같이 보나요? | 추정치와 실제 실행을 구분하는지 확인 | plan drift와 statistics 문제를 분리하기 위해서다 |
| `Buffers`는 많은데 `actual rows`는 적으면 무엇을 의심하나요? | row 수와 page touch를 분리하는지 확인 | 산재된 접근, 정렬, heap 재확인처럼 page 비용이 큰 상황을 먼저 본다 |
| `Heap Fetches`는 언제 특히 의미가 크나요? | PostgreSQL index-only scan 이해 여부 확인 | `Index Only Scan`인데도 heap visibility 재확인이 남았는지 읽을 때 중요하다 |

## 한 줄 정리

`actual rows`는 "몇 row가 지나갔나", `buffers`는 "그 row를 위해 몇 page를 만졌나", `heap fetches`는 "`Index Only Scan`인데도 왜 heap 재확인이 남았나"를 보여 주므로 셋을 한 문장으로 묶어 읽어야 plan이 덜 끊겨 보인다.
