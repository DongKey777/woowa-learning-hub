# DDL Metadata Version Visibility

> 한 줄 요약: DDL은 메타데이터를 바꾸는 순간에 끝나는 게 아니라, 세션마다 다른 버전의 테이블 정의가 언제 보이느냐까지 관리해야 안전하다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: metadata version visibility, DDL metadata, table definition cache, metadata lock, instant ddl, schema version, session visibility

## 핵심 개념

- 관련 문서:
  - [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md)
  - [Instant ADD COLUMN Metadata Semantics](./instant-add-column-metadata-semantics.md)
  - [Instant DDL vs Inplace vs Copy Algorithms](./instant-ddl-vs-copy-inplace-algorithms.md)

DDL은 테이블 구조를 바꾸지만, 그 새 구조가 모든 세션에 동시에 보이는 것은 아니다.  
세션과 시점에 따라 보이는 metadata version이 달라질 수 있다.

핵심은 다음이다.

- DDL은 metadata lock과 함께 진행된다
- 세션은 자기 시점의 테이블 정의를 잠시 유지할 수 있다
- cutover 순간에 old/new metadata visibility를 잘 관리해야 한다

## 깊이 들어가기

### 1. metadata version이 왜 필요한가

테이블 정의가 바뀌는 동안에도 다른 세션은 쿼리를 수행한다.  
그럼 어떤 세션은 old definition, 어떤 세션은 new definition을 봐야 할 수 있다.

이때 엔진은 metadata version과 lock을 이용해 일관성을 유지한다.

### 2. visibility가 꼬이면 무슨 일이 생기나

- DDL 직후 일부 세션이 옛 구조를 잠깐 본다
- 신규 세션은 새 구조를 본다
- 잘못된 cutover는 애플리케이션 오류를 만든다

이건 row visibility와는 다른 층위의 문제다.

### 3. instant DDL과 visibility

instant DDL은 빨리 끝나지만, 그래도 metadata visibility 규칙은 필요하다.  
새 컬럼이 보이는 시점과 기존 세션이 보던 구조의 전환점을 잘 다뤄야 한다.

### 4. 복제/배포와는 다른 관점

이 문서는 복제 지연이 아니라, **같은 primary 안에서 metadata version이 어떻게 보이느냐**에 집중한다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `metadata version visibility`
- `DDL metadata`
- `table definition cache`
- `schema version`
- `session visibility`
- `metadata lock`

## 실전 시나리오

### 시나리오 1. DDL 직후 잠깐 이상한 쿼리가 보인다

일부 세션이 옛 metadata를 유지하고 있거나 cutover가 완전히 안정화되지 않은 상황일 수 있다.  
이때는 세션별 정의 visibility를 봐야 한다.

### 시나리오 2. 새 컬럼을 추가했는데 일부 요청만 실패한다

애플리케이션이 새/옛 schema를 섞어 쓰면 metadata version 전환 구간에서 오류가 날 수 있다.  
그래서 DDL 배포는 코드 배포와 맞물려야 한다.

### 시나리오 3. DDL은 끝났는데 세션은 이상하게 오래 산다

긴 세션은 옛 metadata를 오래 붙잡을 수 있다.  
이 때문에 DDL 이후에도 세션 종료와 재연결 전략이 필요할 수 있다.

## 코드로 보기

### DDL 전환 예시

```sql
ALTER TABLE orders
ADD COLUMN campaign_id BIGINT NULL,
ALGORITHM=INSTANT;
```

### 락과 상태 확인

```sql
SHOW PROCESSLIST;
SELECT OBJECT_SCHEMA, OBJECT_NAME, LOCK_TYPE, LOCK_STATUS
FROM performance_schema.metadata_locks
WHERE OBJECT_NAME = 'orders';
```

### 세션 관찰

```sql
SHOW ENGINE INNODB STATUS\G
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| metadata version 전환 엄격 관리 | schema 안정성이 높다 | 배포 절차가 복잡하다 | 운영 DDL |
| 세션 재연결 유도 | 새 schema 반영이 빠르다 | 애플리케이션 영향이 있다 | cutover 직후 |

핵심은 DDL을 테이블 변경만이 아니라 **metadata version visibility 전환**까지 포함하는 문제로 보는 것이다.

## 꼬리질문

> Q: DDL이 끝났는데도 옛 schema가 보일 수 있나요?
> 의도: metadata visibility 차이를 아는지 확인
> 핵심: 세션이 잠시 옛 metadata를 유지할 수 있다

> Q: metadata lock과 version visibility의 차이는 무엇인가요?
> 의도: 락과 보이는 시점을 구분하는지 확인
> 핵심: 락은 변경 보호, visibility는 실제 보이는 정의다

> Q: DDL 배포에서 무엇을 조심해야 하나요?
> 의도: schema 전환과 세션 관리 감각 확인
> 핵심: cutover, 세션 오래 유지, 앱 호환성이다

## 한 줄 정리

DDL metadata version visibility는 테이블 정의 변경이 세션마다 언제 보이는지 관리하는 문제이고, cutover와 장기 세션이 핵심 위험이다.
