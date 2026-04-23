# Instant DDL vs Inplace vs Copy Algorithms

> 한 줄 요약: DDL은 한 줄처럼 보이지만, 실제로는 메타데이터만 바꾸는지, 테이블을 다시 쓰는지에 따라 락과 비용이 완전히 달라진다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: instant ddl, inplace algorithm, copy algorithm, alter table algorithm, metadata lock, online ddl, rebuild table, ddl blocking

## 핵심 개념

- 관련 문서:
  - [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md)
  - [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
  - [Destructive Schema Cleanup, Column Retirement, and Contract-Phase Safety](./destructive-schema-cleanup-column-retirement.md)
  - [Index Maintenance Window, Rollout, and Fallback Playbook](./index-maintenance-window-rollout-playbook.md)
  - [Clustered Index Locality](./clustered-index-locality.md)
  - [Page Split, Merge, and Fill Factor](./page-split-merge-fill-factor.md)

DDL은 항상 같은 방식으로 동작하지 않는다.  
같은 `ALTER TABLE`이라도 DB와 버전에 따라 다음 셋 중 하나로 흘러갈 수 있다.

- Instant: 메타데이터만 바꾸고 끝나는 방식
- Inplace: 테이블 재작성 없이 내부적으로 수정하는 방식
- Copy: 새 테이블을 만들어 복사하는 방식

운영에서 중요한 건 "문법이 같다"가 아니라 **어떤 알고리즘이 실제로 선택되느냐**다.

## 깊이 들어가기

### 1. Instant DDL은 왜 매력적인가

Instant DDL은 매우 빠르게 끝날 수 있다.

- 테이블 전체를 다시 쓰지 않는다
- 대형 테이블에서도 짧게 끝날 수 있다
- 배포 창을 크게 줄일 수 있다

하지만 모든 변경이 instant인 것은 아니다.

- 일부 컬럼 추가/메타데이터 변경에 한정된다
- 실제 row layout 변경은 불가능하거나 제한적일 수 있다

### 2. Inplace는 무엇을 의미하는가

Inplace는 복사보다 덜 무겁지만, 그렇다고 공짜는 아니다.  
테이블을 통째로 복사하지 않고 내부적으로 작업할 수 있지만, 여전히 쓰기와 락, redo, progress 비용이 있을 수 있다.

### 3. Copy는 왜 가장 위험한가

Copy는 보통 새 테이블에 다 복사한 뒤 바꾸는 방식이다.

- 공간을 더 쓴다
- 시간이 오래 걸릴 수 있다
- metadata lock과 cutover가 위험하다

대형 OLTP 테이블에서는 가장 보수적으로 본다.

### 4. 버전과 엔진에 따라 결과가 달라진다

같은 SQL이라도:

- MySQL 버전
- 컬럼 타입
- 인덱스 변경 여부
- 테이블 크기

에 따라 알고리즘이 달라질 수 있다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `instant ddl`
- `inplace algorithm`
- `copy algorithm`
- `online ddl`
- `rebuild table`
- `metadata lock`

## 실전 시나리오

### 시나리오 1. 컬럼 추가가 instant일 거라 생각했는데 아니었다

배포가 빨리 끝날 거라 예상했지만 실제로는 테이블 재작성 경로를 탔다.  
이 경우는 버전과 컬럼 속성을 먼저 봐야 한다.

### 시나리오 2. 인덱스 추가가 느리게 끝난다

인덱스 생성은 instant가 아니라 inplace나 copy에 가까울 수 있다.  
특히 대형 테이블에서는 작업 시간과 replication lag를 같이 봐야 한다.

### 시나리오 3. DDL 자체보다 cutover가 문제다

copy/inplace가 오래 걸리거나 마지막 전환에서 MDL이 막히면 배포가 실패한 것처럼 보인다.  
실제로는 알고리즘과 락 경로를 분리해서 봐야 한다.

## 코드로 보기

### 어떤 알고리즘이 쓰일지 점검

```sql
ALTER TABLE orders ADD COLUMN campaign_id BIGINT NULL;
```

### 진행 상태 확인

```sql
SHOW PROCESSLIST;
SHOW ENGINE INNODB STATUS\G
```

### DDL 관련 변수 점검

```sql
SHOW VARIABLES LIKE 'innodb_online_alter_log_max_size';
SHOW VARIABLES LIKE 'lock_wait_timeout';
```

### 큰 테이블 작업 전후 비교

```sql
SHOW CREATE TABLE orders;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| Instant | 매우 빠르다 | 가능한 변경이 제한적이다 | 메타데이터 변경 중심 |
| Inplace | 복사보다 덜 무겁다 | 여전히 비용과 락이 있다 | 중간 수준 구조 변경 |
| Copy | 가장 보수적이다 | 공간과 시간이 많이 든다 | 호환성 우선, 일부 변경 |

핵심은 DDL을 "한 번 실행하면 끝"으로 보지 말고, **어떤 알고리즘 경로를 타는지**부터 확인하는 것이다.

## 꼬리질문

> Q: instant DDL은 왜 빠른가요?
> 의도: 메타데이터만 바꾸는 경로를 이해하는지 확인
> 핵심: 테이블 전체를 다시 쓰지 않기 때문이다

> Q: inplace와 copy의 차이는 무엇인가요?
> 의도: 테이블 재작성 여부를 구분하는지 확인
> 핵심: inplace는 더 가볍고, copy는 새 테이블로 복사한다

> Q: DDL이 느릴 때 무엇을 먼저 봐야 하나요?
> 의도: 알고리즘과 MDL을 분리해서 보는지 확인
> 핵심: 실제 경로와 metadata lock 대기 상태다

## 한 줄 정리

DDL은 모두 같은 `ALTER TABLE`이 아니라 instant, inplace, copy 중 어떤 경로를 타는지에 따라 락과 비용이 크게 달라진다.
