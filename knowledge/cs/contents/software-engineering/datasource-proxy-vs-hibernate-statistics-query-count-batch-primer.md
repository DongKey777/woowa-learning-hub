# Datasource Proxy vs Hibernate Statistics Query Count and Batch Primer

> 한 줄 요약: datasource-proxy/p6spy는 "JDBC로 실제 무엇이 나갔는가"를 잡는 바깥쪽 관찰기이고, Hibernate statistics는 "Hibernate가 내부적으로 몇 번 준비하고 몇 번 batch를 실행했는가"를 보여 주는 안쪽 계기판이다. 초심자는 둘 다 쿼리 확인 도구로 보지만, query-count와 batch 검증에서 답하는 질문이 다르다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 멘탈 모델](#먼저-잡을-멘탈-모델)
- [한 장 비교표](#한-장-비교표)
- [query-count 확인에서 무엇이 더 직접적인가](#query-count-확인에서-무엇이-더-직접적인가)
- [batch 확인에서 무엇이 더 직접적인가](#batch-확인에서-무엇이-더-직접적인가)
- [둘을 같이 쓸 때 가장 덜 헷갈리는 순서](#둘을-같이-쓸-때-가장-덜-헷갈리는-순서)
- [자주 하는 오해](#자주-하는-오해)
- [짧은 예시: N+1 테스트와 batch 테스트](#짧은-예시-n1-테스트와-batch-테스트)
- [practice loop](#practice-loop)
- [관련 문서](#관련-문서)

</details>

> 관련 문서:
> - [SQL Log vs Hibernate Statistics Verification Boundaries](./sql-log-vs-hibernate-statistics-verification-boundaries.md)
> - [BatchExecutionCount Assertion Boundaries Primer](./batch-execution-count-assertion-boundaries-primer.md)
> - [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
> - [IDENTITY vs SEQUENCE Batch Verification Example](./identity-vs-sequence-batch-verification-example.md)
> - [JPA Lazy Loading and N+1 Boundary Smells](./jpa-lazy-loading-n-plus-one-boundary-smells.md)
> - [N+1 Query Detection and Solutions](../database/n-plus-one-query-detection-solutions.md)
>
> retrieval-anchor-keywords: datasource proxy vs hibernate statistics, p6spy vs hibernate statistics, query count verification beginner, batch verification datasource proxy, batch verification hibernate statistics, datasource-proxy query count test, p6spy query count test, hibernate statistics batchExecutionCount primer, prepareStatementCount vs query count, jpa observability beginner, sql capture vs orm statistics, datasource proxy batch 확인, p6spy batch 확인, hibernate statistics 쿼리 수 확인, query-count and batch primer, jdbc capture vs hibernate internal counters, beginner persistence observability, datasource proxy n+1 detection, hibernate statistics limits beginner

## 먼저 잡을 멘탈 모델

초심자는 아래 두 줄만 먼저 잡으면 된다.

- datasource-proxy/p6spy는 **DB 쪽으로 나가는 SQL 현장 기록**에 가깝다.
- Hibernate statistics는 **ORM 내부 집계판**에 가깝다.

같은 "쿼리 확인"처럼 보여도 관찰 위치가 다르다.

| 도구 | 초심자용 비유 | 어디에서 본다고 생각하면 쉬운가 |
|---|---|---|
| datasource-proxy / p6spy | 출입문 CCTV | JDBC를 통해 밖으로 나가는 SQL |
| Hibernate statistics | 실내 계기판 | Hibernate 내부 실행 횟수와 요약 숫자 |

그래서 질문도 다르게 잡는 편이 안전하다.

- "실제로 어떤 SQL이 몇 번 나갔지?"면 datasource-proxy/p6spy 쪽이 더 직접적이다.
- "Hibernate가 batch를 아예 실행했나?"면 statistics가 더 직접적이다.

## 한 장 비교표

| 지금 알고 싶은 것 | datasource-proxy / p6spy | Hibernate statistics |
|---|---|---|
| 실제 SQL 문장 | 강함 | 약함 |
| 바인딩 파라미터 | 강함 | 거의 없음 |
| 전체 query count | 강함 | 보조 |
| `prepareStatement` 수 요약 | 보조 | 강함 |
| `batchExecutionCount` | 약함 | 강함 |
| Hibernate 밖에서 나간 JDBC 호출 포함 여부 | 포함 가능 | 보통 제외 |
| 어느 코드 경로에서 반복 `select`가 생겼는지 감 잡기 | 강함 | 약함 |

짧게 외우면 이렇다.

- proxy 계열은 **SQL 장면**에 강하다.
- statistics는 **Hibernate 숫자 요약**에 강하다.

## query-count 확인에서 무엇이 더 직접적인가

초심자 query-count 테스트의 질문은 보통 이것이다.

- "`findAll()` 한 번 돌렸는데 select가 총 몇 번 나갔지?"
- "N+1 때문에 1번이 아니라 21번 나간 것 아닌가?"

이 질문에는 datasource-proxy/p6spy가 더 직관적이다.
이유는 실제 JDBC 호출 수를 바깥에서 세기 때문이다.

| 질문 | 더 먼저 볼 도구 | 이유 |
|---|---|---|
| `select`가 총 몇 번 나갔나 | datasource-proxy / p6spy | 실제 나간 SQL 개수를 바로 세기 쉽다 |
| SQL 파라미터가 어떻게 달라졌나 | datasource-proxy / p6spy | 같은 쿼리가 다른 값으로 반복되는지 보기 쉽다 |
| Hibernate가 준비한 statement 수가 비정상적으로 많나 | Hibernate statistics | `prepareStatementCount` 같은 요약 숫자가 있다 |

여기서 초심자가 특히 헷갈리는 부분이 있다.

- `prepareStatementCount`는 "실제 select 개수"와 완전히 같은 말이 아니다.
- query count를 묻고 있는데 statistics 숫자만 보면 질문이 살짝 바뀔 수 있다.

즉 N+1처럼 "**몇 번 나갔는가**"가 핵심이면 proxy 계열이 더 정면에 있다.

## batch 확인에서 무엇이 더 직접적인가

batch 확인은 query count와 질문이 다르다.
보통은 아래 둘을 분리해야 한다.

- 실제 `insert` SQL은 나갔는가
- Hibernate가 JDBC batch를 아예 실행했는가

이때는 Hibernate statistics가 더 직접적인 첫 신호를 준다.

| 질문 | 더 먼저 볼 도구 | 이유 |
|---|---|---|
| batch가 완전히 0인가 | Hibernate statistics | `getBatchExecutionCount()`가 바로 이 질문에 답한다 |
| 실제로 어떤 `insert`/`update`가 섞여 나갔나 | datasource-proxy / p6spy | SQL 종류와 순서를 장면으로 볼 수 있다 |
| batch가 왜 깨졌는지 `select`가 중간에 끼었는지 보나 | datasource-proxy / p6spy | 중간 개입 SQL을 눈으로 확인하기 쉽다 |

초심자 기준 첫 해석은 이렇게 두면 충분하다.

| 관찰값 | 첫 해석 |
|---|---|
| `batchExecutionCount > 0` | Hibernate batch가 완전히 죽지는 않았다 |
| `batchExecutionCount == 0` | 저장은 됐어도 batch 최적화는 약했을 수 있다 |
| proxy 로그에 `insert`만 길게 반복 | 저장 장면은 보이지만 batch 실행 여부 판단은 아직 부족하다 |

즉 batch에서는 보통 statistics가 먼저, proxy가 설명 보조 역할을 한다.

## 둘을 같이 쓸 때 가장 덜 헷갈리는 순서

둘을 경쟁시키지 말고 아래 순서로 보면 가장 덜 섞인다.

1. datasource-proxy/p6spy로 실제 SQL 장면을 본다.
2. Hibernate statistics로 `prepareStatementCount`, `batchExecutionCount`를 요약한다.
3. 테스트 assertion은 너무 빡빡한 exact count보다, 질문에 맞는 최소 숫자만 남긴다.

초심자에게 이 순서가 좋은 이유는 간단하다.

- 장면 없이 숫자만 보면 맥락을 잃기 쉽다.
- 숫자 없이 로그만 보면 "그래서 총 몇 번이었지?"에서 다시 흔들린다.

## 자주 하는 오해

| 오해 | 더 안전한 판단 |
|---|---|
| p6spy가 있으니 Hibernate statistics는 필요 없다 | SQL 장면은 잘 보이지만 `batchExecutionCount` 같은 ORM 내부 신호는 statistics가 더 직접적이다 |
| statistics 숫자만 보면 query count도 충분히 안다 | `prepareStatementCount`와 실제 query count는 질문이 다를 수 있다 |
| proxy 로그에 `insert`가 많이 보이면 batch는 실패다 | SQL 문장 반복만으로 batch 실행 여부를 단정하면 이르다 |
| `batchExecutionCount > 0`이면 어떤 SQL이 나갔는지는 더 볼 필요 없다 | 중간 `select` 개입이나 flush 시점 문제는 proxy/log가 더 잘 보여 준다 |
| Hibernate statistics가 있으니 Hibernate 밖 JDBC 호출도 다 잡힌다 | 보통 그렇지 않다. proxy 계열이 더 넓게 잡을 수 있다 |

## 짧은 예시: N+1 테스트와 batch 테스트

같은 persistence 테스트라도 주 질문이 다르면 먼저 볼 도구가 달라진다.

| 테스트 장면 | 먼저 볼 것 | 이유 |
|---|---|---|
| 주문 목록 조회 후 회원 이름을 순회한다 | datasource-proxy / p6spy | 반복 `select` 개수와 파라미터를 직접 보기 쉽다 |
| 120건 저장 후 batch가 살아 있는지 본다 | Hibernate statistics | `batchExecutionCount`가 더 직접적이다 |
| batch가 0이라서 왜 그런지 추적한다 | datasource-proxy / p6spy + statistics | 숫자로 0을 확인하고, 장면으로 원인을 본다 |

before / after로 더 짧게 정리하면 아래와 같다.

| before: 흔한 질문 방식 | after: 더 안전한 질문 방식 |
|---|---|
| "statistics 숫자가 낮으니 쿼리도 적게 나갔겠지?" | "실제 query count는 proxy로, Hibernate 내부 집계는 statistics로 나눠 본다" |
| "p6spy 로그에 `insert`가 많으니 batch가 없네" | "`batchExecutionCount`로 batch 실행 여부를 먼저 확인한다" |

## practice loop

1. N+1이 의심되는 조회 테스트 하나를 고른다.
2. datasource-proxy/p6spy나 비슷한 SQL capture로 실제 `select` 개수를 센다.
3. 같은 테스트에서 Hibernate statistics의 `prepareStatementCount`를 같이 보고, 왜 숫자가 질문과 조금 다를 수 있는지 적어 본다.
4. 이번에는 batch insert 테스트를 만들고 `batchExecutionCount`를 본다.
5. 마지막으로 proxy 로그를 다시 열어, 어떤 SQL이 batch 설명에 도움이 되는지 비교한다.

이 루프를 한 번 돌면 초심자도 아래를 분리해서 읽기 시작한다.

- query count는 실제 SQL 관찰 질문
- batch 여부는 ORM 내부 실행 집계 질문

## 관련 문서

- SQL 로그와 statistics 차이를 먼저 잡고 싶다면: [SQL Log vs Hibernate Statistics Verification Boundaries](./sql-log-vs-hibernate-statistics-verification-boundaries.md)
- `batchExecutionCount`를 어디까지 assertion으로 잠가야 하는지 보려면: [BatchExecutionCount Assertion Boundaries Primer](./batch-execution-count-assertion-boundaries-primer.md)
- `IDENTITY`, `flush`, batch 설정이 왜 같이 흔들리는지 보려면: [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
- 같은 insert 테스트가 `IDENTITY`와 `SEQUENCE`에서 왜 다르게 보이는지 보려면: [IDENTITY vs SEQUENCE Batch Verification Example](./identity-vs-sequence-batch-verification-example.md)
- N+1 탐지 도구를 조금 더 넓게 비교하고 싶다면: [N+1 Query Detection and Solutions](../database/n-plus-one-query-detection-solutions.md)
