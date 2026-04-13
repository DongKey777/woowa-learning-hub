# Instant ADD COLUMN Metadata Semantics

> 한 줄 요약: instant ADD COLUMN은 기존 row를 다시 쓰지 않고 메타데이터로 새 컬럼을 설명하는 방식이라, 읽을 때 값이 합성되는 의미를 이해해야 한다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: instant add column, metadata semantics, default synthesis, row format, ALGORITHM=INSTANT, metadata only, column append, instant ddl

## 핵심 개념

- 관련 문서:
  - [Instant DDL vs Inplace vs Copy Algorithms](./instant-ddl-vs-copy-inplace-algorithms.md)
  - [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md)
  - [Clustered Index Locality](./clustered-index-locality.md)

instant ADD COLUMN은 기존 row 데이터를 물리적으로 다시 쓰지 않고, 테이블 메타데이터만 바꿔 새 컬럼을 "있는 것처럼" 보이게 하는 방식이다.  
이때 가장 중요한 것은 **기존 row가 새 컬럼 값을 실제로 저장하고 있지 않다**는 점이다.

핵심은 다음이다.

- 새 컬럼 정보가 메타데이터에 추가된다
- 기존 row는 여전히 옛 layout을 유지할 수 있다
- 읽을 때는 default/NULL 같은 값이 합성될 수 있다
- 일부 변경은 instant가 아니라 inplace/copy로 떨어진다

## 깊이 들어가기

### 1. metadata-only라는 말의 의미

instant ADD COLUMN은 "행을 다 고치지 않는다"는 뜻이다.  
즉 기존 데이터 페이지를 재작성하지 않고, 테이블 정의와 버전 정보를 갱신하는 쪽에 가깝다.

이게 의미하는 바:

- 대형 테이블에서도 빠를 수 있다
- row storage 비용이 즉시 들지 않는다
- 대신 읽기 시점에 새 컬럼을 해석하는 규칙이 필요하다

### 2. 기존 row에는 새 컬럼이 실제로 없을 수 있다

새 컬럼을 instant로 추가해도, 과거에 쓰인 row page에 그 값이 물리적으로 들어가 있는 것은 아니다.  
그래서 읽을 때는 엔진이 metadata와 default 규칙으로 값을 해석한다.

이것이 "metadata semantics"다.

### 3. 왜 컬럼 위치가 중요한가

instant ADD COLUMN은 보통 append 쪽에 가장 자연스럽다.  
중간 삽입이나 복잡한 layout 변경은 instant가 아니라 다른 알고리즘을 유도할 수 있다.

즉 "컬럼 추가"와 "테이블 구조 재배치"는 다르다.

### 4. default와 NULL의 의미

기존 row에 새 컬럼이 없으면, 엔진은 그 컬럼을 어떻게 해석할지 알아야 한다.

- nullable이면 NULL로 해석될 수 있다
- 기본값이 있으면 그 값처럼 보일 수 있다
- 실제 저장 여부와 읽기 결과는 다를 수 있다

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `instant add column`
- `metadata semantics`
- `default synthesis`
- `metadata only`
- `column append`
- `ALGORITHM=INSTANT`

## 실전 시나리오

### 시나리오 1. 컬럼을 추가했는데 기존 row는 backfill이 없었다

instant DDL이면 기존 row를 다시 쓰지 않으므로, 데이터를 즉시 채워 넣지 않아도 된다.  
대신 애플리케이션은 새 컬럼이 물리적으로 아직 비어 있을 수 있다는 점을 알아야 한다.

### 시나리오 2. instant가 아니라는 이유로 배포가 느려진다

컬럼 위치나 속성 때문에 instant가 불가능하면 inplace/copy로 내려갈 수 있다.  
이때는 DDL 알고리즘 문서와 같이 봐야 한다.

### 시나리오 3. 읽기 결과가 default처럼 보인다

metadata-only 추가는 읽기 시점 합성 결과를 만든다.  
이 동작을 모르고 있으면 "실제 저장된 값"과 "보이는 값"을 혼동하기 쉽다.

## 코드로 보기

### instant 가능한 형태 점검

```sql
ALTER TABLE orders
ADD COLUMN campaign_id BIGINT NULL DEFAULT NULL,
ALGORITHM=INSTANT;
```

### 읽기 결과 확인

```sql
SELECT campaign_id
FROM orders
WHERE id = 1;
```

### 메타데이터 확인

```sql
SHOW CREATE TABLE orders;
```

### DDL 경로 확인

```sql
SHOW PROCESSLIST;
SHOW ENGINE INNODB STATUS\G
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| instant add column | 매우 빠르다 | 가능한 형태가 제한적이다 | 메타데이터만 바뀌는 경우 |
| inplace/copy | 더 많은 변경을 처리한다 | 더 느리고 무겁다 | layout 변경이 필요할 때 |

핵심은 instant ADD COLUMN을 "컬럼을 실제로 다 채우는 작업"으로 오해하지 않는 것이고, **메타데이터가 row 의미를 대신 설명한다**는 점이다.

## 꼬리질문

> Q: instant ADD COLUMN에서 기존 row는 어떻게 보이나요?
> 의도: 물리 저장과 논리 해석을 구분하는지 확인
> 핵심: 실제 값이 없어도 metadata로 합성되어 보일 수 있다

> Q: 왜 항상 instant가 되지 않나요?
> 의도: 컬럼 위치와 layout 변경의 제약을 아는지 확인
> 핵심: 모든 변경이 metadata-only는 아니기 때문이다

> Q: default와 instant semantics는 어떤 관계가 있나요?
> 의도: 읽기 시점 값 합성 이해 여부 확인
> 핵심: 기존 row에 없는 값을 해석하는 규칙이 필요하다

## 한 줄 정리

instant ADD COLUMN은 row를 다시 쓰지 않고 메타데이터로 새 컬럼 의미를 합성하는 방식이라, 물리 저장과 논리 읽기를 분리해서 이해해야 한다.
