# Index Skip Scan Behavior

> 한 줄 요약: index skip scan은 복합 인덱스의 선행 컬럼이 없어도, 낮은 카디널리티라면 그 값을 건너뛰며 뒤쪽 컬럼을 활용하는 우회로다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: skip scan, index skip scan, Using index for skip scan, composite index, low cardinality, optimizer_switch, loose prefix, range access

## 핵심 개념

- 관련 문서:
  - [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
  - [Optimizer Switch Knobs and Plan Stability](./optimizer-switch-plan-stability-invisible-indexes.md)
  - [인덱스와 실행 계획](./index-and-explain.md)
  - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)

skip scan은 복합 인덱스의 앞 컬럼이 조건에 없을 때도 인덱스를 일부 활용하려는 전략이다.  
예를 들어 `(gender, birth_date)` 인덱스에서 `birth_date`만 조건에 있어도, gender의 가능한 값을 건너뛰며 찾을 수 있다.

이 문서의 핵심은 다음이다.

- 복합 인덱스의 왼쪽 접두어 규칙을 완전히 무시하는 게 아니다
- 선행 컬럼의 distinct 값이 적을 때만 유리하다
- `Using index for skip scan`이 보이면 비용 모델이 우회 탐색을 선택한 것이다

## 깊이 들어가기

### 1. skip scan이 풀려는 문제

복합 인덱스가 `(a, b)`일 때 `b`만 조건으로 걸면 보통 인덱스 활용이 어렵다.  
하지만 `a`의 distinct 값이 적다면, a의 각 값마다 b 범위를 훑어보는 편이 전체 풀스캔보다 나을 수 있다.

### 2. 왜 저카디널리티에서만 잘 맞는가

skip scan은 선행 컬럼의 가능한 값을 순회하는 비용이 들어간다.

- 선행 컬럼 값이 적으면 시도할 만하다
- 선행 컬럼 값이 많으면 반복 탐색 비용이 커진다

그래서 성별, 상태값, 작은 분류 코드처럼 값이 적은 컬럼에서 의미가 있다.

### 3. skip scan은 왼쪽 접두어 규칙의 예외가 아니다

이 전략은 규칙을 깨는 것이 아니라, 규칙이 완벽히 맞지 않을 때의 우회 경로다.  
즉 "복합 인덱스 순서가 중요하지 않다"는 뜻이 아니다.

### 4. 통계와 함께 봐야 하는 이유

옵티마이저는 선행 컬럼의 distinct 수와 뒤쪽 컬럼의 선택도를 보고 판단한다.  
통계가 틀리면 skip scan이 유리할 때 놓치거나, 불리할 때 선택할 수 있다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `skip scan`
- `index skip scan`
- `Using index for skip scan`
- `low cardinality`
- `composite index`
- `loose prefix`

## 실전 시나리오

### 시나리오 1. birth_date 조건만 있는데 인덱스가 있다

`(gender, birth_date)` 인덱스에서 gender 조건이 없어도, gender 값이 몇 개 안 된다면 skip scan이 가능할 수 있다.  
이때는 새 인덱스를 바로 추가하기보다 skip scan 가능성을 먼저 확인할 수 있다.

### 시나리오 2. 조건은 맞는데 실행 계획이 풀스캔이다

선행 컬럼 distinct가 크거나 통계가 오래되면 skip scan이 선택되지 않을 수 있다.  
이 경우 인덱스 순서 재설계가 더 나을 수 있다.

### 시나리오 3. skip scan이 갑자기 안 좋아졌다

데이터 분포가 바뀌어 선행 컬럼 카디널리티가 높아지면, 우회 탐색이 오히려 비싸질 수 있다.  
통계와 분포를 같이 봐야 한다.

## 코드로 보기

### 예시 인덱스

```sql
CREATE INDEX idx_users_gender_birthdate
ON users (gender, birth_date);
```

### skip scan 관찰

```sql
EXPLAIN
SELECT id, gender, birth_date
FROM users
WHERE birth_date >= '1990-01-01';
```

확인 포인트:

- `Using index for skip scan`
- `type`이 range인지
- rows 추정이 과도하게 크지 않은지

### 스위치 비교

```sql
SET SESSION optimizer_switch='skip_scan=on';
SET SESSION optimizer_switch='skip_scan=off';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| skip scan 활용 | 인덱스를 우회적으로 쓸 수 있다 | 선행 컬럼 distinct가 많으면 비싸다 | low cardinality prefix |
| 새 인덱스 추가 | 명확하고 예측 가능하다 | 쓰기 비용이 늘어난다 | skip scan이 불안정할 때 |
| 기존 복합 인덱스 재설계 | 구조를 바로잡을 수 있다 | DDL 비용이 든다 | 조회 패턴이 안정적일 때 |

핵심은 skip scan을 "인덱스가 없어도 되는 기술"로 착각하지 않고, **선행 컬럼이 적을 때만 유효한 우회로**로 보는 것이다.

## 꼬리질문

> Q: skip scan은 언제 유리한가요?
> 의도: low cardinality prefix의 의미를 아는지 확인
> 핵심: 선행 컬럼 distinct 값이 적을 때다

> Q: skip scan이 왼쪽 접두어 규칙을 깨는 건가요?
> 의도: 규칙과 우회 경로를 구분하는지 확인
> 핵심: 규칙을 완전히 무시하는 게 아니라 우회하는 것이다

> Q: `Using index for skip scan`이 보이면 무조건 좋은가요?
> 의도: 실행 계획 신호를 절대화하지 않는지 확인
> 핵심: 통계와 rows 추정이 맞아야 한다

## 한 줄 정리

index skip scan은 선행 컬럼이 없는 복합 인덱스를 low-cardinality prefix로 우회 활용하는 전략이고, 통계가 맞을 때만 이득이 있다.
