# PostgreSQL `Index Only Scan`인데 왜 `Heap Fetches`가 남아요?

> 한 줄 요약: PostgreSQL에서 `Index Only Scan`인데도 `Heap Fetches`가 남는 건 이상 동작이 아니라, visibility map이 "이 page는 모두 보여도 된다"를 아직 보증하지 못하면 heap에서 MVCC visibility를 다시 확인하기 때문이다.

**난이도: 🟢 Beginner**

관련 문서:

- [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)
- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)
- [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)
- [Hybrid Top-Index / Leaf Layouts](../data-structure/hybrid-top-index-leaf-layouts.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: postgresql index only scan heap fetches, why heap fetches remain, heap fetches beginner, index only scan basics, mvcc visibility basics, visibility map what is, visibility map beginner, postgresql heap table basics, why index only scan still reads heap, 처음 보는 heap fetches, heap fetches 뭐예요, covering index but still heap fetches, explain analyze heap fetches why, index only scan 왜 heap read

## 핵심 개념

초보자는 `Index Only Scan`을 보면 "이제 heap은 절대 안 읽겠네"라고 받아들이기 쉽다.
하지만 PostgreSQL에서 이 이름은 **인덱스만으로 끝낼 수 있으면 그렇게 하겠다**는 경로에 가깝다.
실행 중에는 "이 row가 지금 내 스냅샷에서 보여도 되나?"를 다시 확인해야 해서, 그 확인이 남아 있으면 heap 방문이 붙는다.

먼저 한 줄만 고정하면 된다.

- index: 값을 빨리 찾는 안내판
- heap: row 본문이 있는 테이블 페이지
- `visibility map`: "이 heap page는 지금 모든 tuple이 모두에게 보여도 된다"에 가까운 빠른 메모
- `Heap Fetches`: 안내판만으로 끝내지 못해 row 본문 쪽을 다시 확인한 횟수

즉 `Heap Fetches`가 보인다는 건 "플랜이 틀렸다"보다 **visibility map만으로 확신할 수 없어 heap까지 내려갔다**에 가깝다.

## 한눈에 보기

| plan에서 보인 것 | 초보자용 첫 해석 | 바로 결론 내리면 안 되는 말 |
| --- | --- | --- |
| `Index Only Scan` | "가능하면 인덱스만 읽고 끝내려는 경로를 탔다" | "heap을 100% 안 읽었다" |
| `Heap Fetches: 0` | "이번에는 heap 확인이 거의 필요 없었다" | "항상 이렇게 나온다" |
| `Heap Fetches: 42` | "몇 row/page는 heap 확인이 다시 필요했다" | "index가 아예 소용없다" |
| visibility map이 잘 유지됨 | "page 단위로 '대체로 안전' 표식이 붙어 있다" | "MVCC를 완전히 안 본다" |

```text
안전한 멘탈모델
1. index가 후보 row를 찾는다
2. visibility map이 heap 확인을 생략할 수 있는지 먼저 본다
3. 확신이 서지 않으면 postgres가 heap에서 visibility를 다시 확인한다
```

## visibility map을 어떻게 이해하면 되나요?

visibility map은 초급에서는 "heap page 옆에 붙어 있는 체크 스티커" 정도로 이해하면 충분하다.
"이 페이지는 지금 있는 tuple들이 다 visible하니, index만 보고 지나가도 될 가능성이 높다"는 빠른 힌트를 주는 장치다.

중요한 건 이 메모가 **row별 메모가 아니라 page 단위 메모**라는 점이다.
그래서 index에 필요한 컬럼이 다 있어도, 해당 page가 all-visible로 보증되지 않으면 PostgreSQL은 heap을 다시 본다.

| visibility map 관점 | 초보자용 해석 | `Heap Fetches`에 주는 영향 |
| --- | --- | --- |
| page가 `all-visible` | "이 page는 heap 재확인 없이 지나갈 가능성이 크다" | 줄기 쉽다 |
| page가 아직 `all-visible` 아님 | "누가 지금 보이는지 heap에서 다시 확인해야 한다" | 남기 쉽다 |

초급에서는 내부 비트 구조를 외울 필요는 없다.
`Heap Fetches`를 볼 때는 아래 한 문장만 붙잡으면 된다.

> "index가 row를 찾는 일"과 "이 page를 heap까지 안 내려가도 되는지 확인하는 일"은 다른 단계다.

## 왜 all-visible이 깨지나요?

`Heap Fetches`가 남는 흔한 이유를 초급용으로 줄이면 둘이다.

- 최근 `UPDATE`/`DELETE`가 많아서 page의 visible 보증이 다시 흔들렸다
- `VACUUM`/autovacuum가 아직 그 변화를 정리해 visibility map을 갱신하지 못했다

여기서 포인트는 "인덱스가 나빠서"보다 **쓰기 흔적과 정리 상태 때문에 heap 재확인이 남을 수 있다**는 것이다.
그래서 `Index Only Scan` follow-up에서는 인덱스 컬럼만 보지 말고 visibility map과 vacuum 문맥을 같이 봐야 한다.

## 작은 예시로 읽기

예를 들어 아래처럼 plan이 나왔다고 하자.

```text
Index Only Scan using idx_orders_status_created_at on orders
Heap Fetches: 37
```

초보자용 해석은 이렇게 끊는 편이 안전하다.

| 보인 숫자 | 첫 해석 | 다음 질문 |
| --- | --- | --- |
| `Index Only Scan` | 인덱스만으로 끝내는 경로를 우선 시도했다 | 필요한 컬럼은 인덱스에 다 있었나? |
| `Heap Fetches: 37` | 37번은 heap 확인이 다시 필요했다 | 왜 visibility map만으로 못 끝냈지? 최근 쓰기나 vacuum 상태가 어떤가? |

즉 이 plan은 "이름은 index only였는데 실패"가 아니라,
"대부분 인덱스로 가되, visibility map이 확신하지 못한 일부 page는 heap 검증이 붙었다"로 읽는 편이 맞다.

## 흔한 오해와 함정

- "`Index Only Scan`이면 heap fetch가 0이어야 정상이다" -> 아니다. 이름과 실제 heap 재확인 횟수는 분리해서 본다.
- "`Heap Fetches`가 있으면 인덱스를 새로 만들어야 한다" -> 꼭 그렇지 않다. storage layout과 MVCC visibility 문제가 먼저일 수 있다.
- "heap이니까 자바 heap 메모리 얘기다" -> 아니다. 여기서 heap은 PostgreSQL table body 쪽을 가리킨다.
- "커버링 인덱스를 만들었는데 왜 또 읽지?" -> PostgreSQL에서는 커버링 설계와 visibility 확인이 같은 층이 아니다.
- "visibility map이 있으면 heap을 영원히 안 본다" -> 아니다. 최근 쓰기나 vacuum 상태에 따라 다시 heap 확인이 생긴다.
- "`Heap Fetches`가 조금이라도 있으면 plan이 완전히 나쁘다" -> 아니다. 0이 아니어도 여전히 index path가 유리할 수 있다.

## 다음에 무엇을 보면 되나요?

처음엔 원인을 너무 많이 열지 말고 아래 순서로 보면 된다.

1. 정말 `Index Only Scan`인지와 `Heap Fetches` 숫자를 같이 본다.
2. 최근 쓰기 churn이 많았는지, vacuum/autovacuum가 따라오고 있는지 확인한다.
3. "인덱스 shape 문제"인지 "visibility 문제"인지 분리한다.

문서 연결은 이렇게 가져가면 안전하다.

- 저장 구조 감각이 약하면 [MySQL clustered index와 PostgreSQL heap + index 저장 구조 브리지](./mysql-postgresql-index-storage-bridge.md)
- 커버링 인덱스와 `Index Only Scan`을 같은 말로 읽고 있었다면 [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- `vacuum`, dead tuple, cleanup debt가 같이 보여서 운영 신호까지 이어지면 [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)

## 한 줄 정리

PostgreSQL에서 `Index Only Scan`인데도 `Heap Fetches`가 남는 이유는 index가 row를 찾는 일과 MVCC visibility를 확인하는 일이 분리돼 있어서, 일부 row는 heap에서 다시 검증해야 하기 때문이다.
