# EXPLAIN 첫 판독 미니카드

> 한 줄 요약: timeout 앞에서 `EXPLAIN`을 처음 열었다면, 초보자는 먼저 `type`, `key`, `rows`, `Using filesort`, `Using temporary` 다섯 신호만으로 "락 대기보다 느린 실행 쪽인가"를 빠르게 줄이면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)
- [타임아웃 튜닝 순서 체크리스트 카드](./timeout-tuning-order-checklist-card.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
- [Spring 트랜잭션 기본](../spring/spring-transactional-basics.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: explain first read timeout, explain beginner timeout card, explain type key rows extra, using filesort using temporary, statement timeout explain first check, mysql explain slow query beginner, rows key type mini card, explain query plan first read, timeout plan reading primer, 실행계획 첫 판독, rows key type filesort temporary, timeout explain 입문, explain first read timeout mini card basics, explain first read timeout mini card beginner, explain first read timeout mini card intro

## 먼저 멘탈모델

`EXPLAIN`은 "정답표"가 아니라 **DB가 이 SQL을 얼마나 넓게 읽고, 중간에 따로 정렬하나**를 보여 주는 첫 지도다.

timeout 앞에서 초보자가 바로 모든 컬럼을 읽을 필요는 없다. 먼저 아래 다섯 개만 본다.

- `type`: 좁게 찾는가, 넓게 훑는가
- `key`: 어떤 인덱스를 실제로 탔는가
- `rows`: 몇 row를 읽을 것으로 보는가
- `Using filesort`: 인덱스 순서로 못 끝내고 따로 정렬하나
- `Using temporary`: 중간 결과를 임시 테이블에 담나

짧게 기억하면 이렇다.

> `rows`가 크거나 `filesort`/`temporary`가 붙으면, 초보자 1차 가설은 "락 대기 전에도 SQL 자체가 무겁다" 쪽이다.

## 30초 판독표

| 보이는 신호 | 초보자 첫 해석 | timeout 원인 후보 |
| --- | --- | --- |
| `type = ALL` | 거의 전체를 훑을 수 있다 | 느린 scan 쪽 |
| `key = NULL` | 타는 인덱스가 없다 | 느린 scan 쪽 |
| `rows`가 크다 | 읽는 양이 많다 | 느린 실행 쪽 |
| `Using filesort` | 따로 정렬한다 | 정렬 비용 쪽 |
| `Using temporary` | 중간 결과를 다시 담는다 | 집계/정렬 비용 쪽 |

이 표의 목적은 정밀 튜닝이 아니다.
초보자가 "`statement timeout`인데도 blocker부터 찾을까, 아니면 plan부터 볼까"를 빨리 가르는 용도다.

## 다섯 신호를 이렇게 읽는다

| 항목 | good에 가까운 모습 | suspicious에 가까운 모습 |
| --- | --- | --- |
| `type` | `const`, `ref`, 좁은 `range` | `ALL`, 너무 넓은 `range` |
| `key` | 의도한 인덱스 이름이 보임 | `NULL`, 엉뚱한 인덱스 |
| `rows` | 한 자리수~작은 범위 | 생각보다 큰 수 |
| `Using filesort` | 없음 | 있음 |
| `Using temporary` | 없음 | 있음 |

읽는 순서는 항상 같게 두면 덜 흔들린다.

1. `type`으로 "full scan 후보인가"를 본다.
2. `key`로 "인덱스를 실제로 탔나"를 본다.
3. `rows`로 "읽는 양이 이미 큰가"를 본다.
4. `filesort`/`temporary`로 "읽은 뒤에 한 번 더 무거운 일을 하나"를 본다.

## 작은 예시

```sql
EXPLAIN
SELECT id, created_at
FROM orders
WHERE status = 'PAID'
ORDER BY created_at DESC
LIMIT 20;
```

| 항목 | 예시 값 | 초보자 해석 |
| --- | --- | --- |
| `type` | `ALL` | 넓게 훑는다 |
| `key` | `NULL` | 맞는 인덱스를 못 탔다 |
| `rows` | `850000` | 읽는 양이 이미 크다 |
| `Extra` | `Using filesort` | 읽고 나서 또 정렬한다 |

이 장면에서는 초보자 결론을 이렇게만 적어도 충분하다.

- 같은 SQL이 혼자 실행돼도 느릴 가능성이 높다
- timeout이 나면 먼저 lock보다 plan을 의심할 근거가 있다
- 다음 액션은 blocker 조회보다 인덱스/정렬 축 확인이다

반대로 `type=ref`, `key=idx_orders_status_created_at`, `rows=20` 근처면 plan 자체보다는 lock 대기나 다른 축도 같이 의심할 수 있다.

## 바로 다음 행동

| 지금 보인 조합 | 초보자 다음 행동 |
| --- | --- |
| `type = ALL` + `key = NULL` | [인덱스와 실행 계획](./index-and-explain.md)으로 가서 인덱스 축부터 다시 본다 |
| `rows` 큼 + `Using filesort` | 정렬 컬럼과 복합 인덱스 순서를 본다 |
| `rows` 큼 + `Using temporary` | `GROUP BY`/`DISTINCT`/중간 결과 재배열을 의심한다 |
| `rows` 작고 정렬 신호도 약함 | lock wait, hot key, 긴 트랜잭션 쪽 로그도 같이 본다 |

timeout 문서와 같이 붙여 기억하면 더 쉽다.

- `statement timeout`이고 이 카드에서 suspicious 신호가 많다: 느린 SQL 쪽부터 본다
- `statement timeout`인데 이 카드에서 suspicious 신호가 약하다: lock 대기 로그를 같이 본다

## 자주 헷갈리는 포인트

- "`rows`는 추정치라 초보자는 볼 필요 없다" -> 추정치여도 "이미 넓다/좁다"를 가르는 1차 신호로는 충분하다.
- "`Using filesort`면 무조건 디스크 정렬이다" -> 아니다. 핵심은 "인덱스 순서로 끝나지 못했다"는 뜻이다.
- "`Using temporary`면 바로 장애다" -> 아니다. 다만 timeout 앞에서는 중간 작업 비용 후보로 먼저 적어 둔다.
- "`key`만 잡히면 느린 쿼리가 아니다" -> 아니다. `key`가 보여도 `rows`, `filesort`, `temporary` 때문에 느릴 수 있다.
- "`type = range`면 항상 좋다" -> 아니다. 너무 넓은 `range`면 timeout 후보가 될 수 있다.

## 한 줄 정리

timeout 앞의 첫 `EXPLAIN`에서는 **`type -> key -> rows -> filesort/temporary`** 순서만 고정해도, 초보자가 락 대기와 느린 실행 후보를 훨씬 빨리 분리할 수 있다.
