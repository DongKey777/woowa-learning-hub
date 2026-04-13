# 온라인 스키마 변경 전략

> 한 줄 요약: 운영 중인 큰 테이블의 구조를 바꿀 때는 `ALTER TABLE` 한 줄보다, 락과 복제 지연을 통제하는 절차가 더 중요하다.

**난이도: 🔴 Advanced**

관련 문서:

- [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [인덱스와 실행 계획](./index-and-explain.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
- [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)

---

## 핵심 개념

온라인 스키마 변경은 서비스 중단 없이 테이블 구조를 바꾸는 작업이다.  
문제는 단순히 `ALTER TABLE`을 실행하는 것이 아니라, 그 과정에서 다음을 함께 관리해야 한다는 점이다.

- 메타데이터 락
- 장시간 실행되는 DDL
- 쓰기 트래픽과의 충돌
- replication lag
- cutover 순간의 정합성

테이블이 작으면 단순 `ALTER TABLE`로 끝날 수 있다. 하지만 대용량 OLTP 테이블에서는 구조 변경 자체가 장애가 될 수 있으므로, 보통 shadow table + copy + sync + cutover 방식으로 접근한다.

### 언제 온라인 변경이 필요한가

- 수억 건 테이블에 컬럼 추가/타입 변경이 필요할 때
- 인덱스를 추가하거나 재구성해야 할 때
- nullable/기본값/길이 변경이 서비스 영향 없이 되어야 할 때
- 배포 창이 짧고 다운타임을 허용하기 어려울 때

---

## 깊이 들어가기

### 1. 왜 `ALTER TABLE`이 위험한가

DBMS에 따라 다르지만, 큰 테이블의 DDL은 다음 문제를 만들 수 있다.

- 테이블이 잠긴다
- 쓰기 트래픽이 밀린다
- 복제본이 뒤처진다
- 롤백 비용이 커진다

예를 들어 다음처럼 단순해 보이는 작업도 위험할 수 있다.

```sql
ALTER TABLE orders ADD COLUMN campaign_id BIGINT NULL;
```

작은 테이블에서는 빠르지만, 큰 테이블에서는 전체 스캔과 재작성, 락 점유가 발생할 수 있다.  
DB 버전과 엔진에 따라 online DDL 지원 범위가 다르므로, “된다”와 “안전하다”는 별개의 문제다.

### 2. shadow table 기반 전략

가장 흔한 패턴은 아래와 같다.

1. 새 구조의 shadow table을 만든다.
2. 기존 테이블 데이터를 chunk 단위로 복사한다.
3. 복사 중 발생한 쓰기 변경을 shadow table에 동기화한다.
4. 검증 후 cutover 한다.

이 방식은 쓰기 이중화가 필요하고, validation 절차가 핵심이다.

### 3. pt-online-schema-change와 gh-ost

둘 다 “온라인 변경”을 도와주는 도구지만 접근이 다르다.

| 도구 | 핵심 아이디어 | 장점 | 주의점 |
|------|------|------|------|
| `pt-online-schema-change` | 트리거로 원본 테이블 변경을 shadow table에 반영 | 직관적이고 널리 알려짐 | 트리거 오버헤드, FK 제약, 대형 쓰기 부하 |
| `gh-ost` | binlog 기반으로 변경을 추적 | 원본 테이블 트리거 부담이 적음 | replication/binlog 환경 의존, cutover 제어 필요 |

운영 관점에서 중요한 차이는 “복사 중 쓰기 변경을 어디서 잡는가”다.

- `pt-osc`는 트리거가 직접 잡는다
- `gh-ost`는 binlog를 이용해 변경을 추적한다

### 4. chunk copy와 backfill

대용량 테이블 복사는 한 번에 하면 안 된다. chunk 단위로 나눠야 한다.

```sql
-- 예시: PK 기준으로 chunk를 나눠 복사한다고 가정
INSERT INTO orders_new (id, user_id, status, created_at)
SELECT id, user_id, status, created_at
FROM orders
WHERE id BETWEEN 100000 AND 110000;
```

chunk 크기가 너무 크면 락과 IO가 커지고, 너무 작으면 전체 작업 시간이 늘어난다.  
그래서 작업 중에는 복사 속도, replication lag, CPU, disk IO를 계속 관찰해야 한다.

### 5. cutover는 가장 위험한 순간이다

마지막 순간에는 원본과 shadow를 교체해야 한다.

여기서 흔한 문제는 다음과 같다.

- 마지막 write 유실
- metadata lock 대기
- 애플리케이션이 잠시 구버전 스키마를 본다
- 복제본과 primary의 시점이 어긋난다

cutover는 가능한 짧아야 하고, 사전에 롤백 플랜이 있어야 한다.

---

## 실전 시나리오

### 시나리오 1: 대형 테이블에 컬럼 추가

`orders`가 수억 건이고, 새 컬럼이 필요하다. 단순 `ALTER TABLE`은 배포 시간을 넘어설 수 있다.

대응:

1. shadow table 생성
2. chunk copy
3. 애플리케이션을 새 컬럼 nullable 기준으로 배포
4. validation 후 cutover
5. 새 컬럼을 점진적으로 채운다

### 시나리오 2: 인덱스 추가가 오히려 장애를 만든다

운영 중 인덱스를 추가했더니 쓰기 지연이 급증할 수 있다.

원인:

- 인덱스 생성 자체가 무겁다
- secondary index가 많아지면 write amplification이 늘어난다
- replication lag가 커질 수 있다

### 시나리오 3: replication lag 때문에 읽기 오류가 난다

schema change 중 replica가 뒤처지면 새 구조를 기대하는 애플리케이션과 충돌할 수 있다.

대응:

- primary 기준으로 cutover를 관리한다
- lag 모니터링을 넣는다
- 릴리즈 순서를 schema-first/app-second 또는 app-first/schema-second 중 상황에 맞게 고른다

---

## 코드로 보기

### pt-online-schema-change 감각

```bash
pt-online-schema-change \
  --alter "ADD COLUMN campaign_id BIGINT NULL" \
  D=mydb,t=orders \
  --execute
```

### gh-ost 감각

```bash
gh-ost \
  --host=primary.db.local \
  --database=mydb \
  --table=orders \
  --alter="ADD COLUMN campaign_id BIGINT NULL" \
  --execute
```

### 직접 점검하는 DDL 예시

```sql
-- 복사 전 확인
SHOW CREATE TABLE orders;
SHOW VARIABLES LIKE 'innodb_online_alter_log_max_size';

-- 복사 후 검증
SELECT COUNT(*) FROM orders;
SELECT COUNT(*) FROM orders_new;
```

운영 자동화에서는 이 작업 전후로 row count, checksum, sample query를 함께 확인하는 편이 안전하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|-------------|
| 직접 `ALTER TABLE` | 가장 단순하다 | 큰 테이블에서 위험하다 | 작은 테이블, 짧은 락 허용 |
| `pt-online-schema-change` | 절차가 명확하다 | 트리거 오버헤드가 있다 | 트리거 비용을 감당할 수 있을 때 |
| `gh-ost` | 원본 트리거 부담이 적다 | 환경 의존성이 있다 | binlog/replication 체계가 안정적일 때 |
| 애플리케이션 병행 배포 | 배포 순서를 유연하게 잡을 수 있다 | 코드/스키마 호환성을 맞춰야 한다 | 마이그레이션이 여러 단계일 때 |

핵심은 “어떤 도구가 좋냐”보다, **내 테이블 크기와 운영 제약에서 실패 확률이 낮은가**다.

---

## 꼬리질문

> Q: 대형 테이블에 `ALTER TABLE`을 그냥 하면 왜 위험한가?
> 의도: 메타데이터 락, 재작성, 복제 지연의 이해 여부 확인
> 핵심: 테이블 크기와 엔진 특성에 따라 다운타임이 발생할 수 있다

> Q: `pt-online-schema-change`와 `gh-ost`의 차이는 무엇인가?
> 의도: 트리거 기반과 binlog 기반 변경 추적의 차이 이해 여부 확인
> 핵심: 원본 테이블 부담과 복제 체계 의존성이 다르다

> Q: cutover 단계에서 가장 먼저 확인할 것은 무엇인가?
> 의도: 운영 절차와 롤백 플랜 감각 확인
> 핵심: 마지막 write 반영, replication lag, 앱 호환성

---

## 한 줄 정리

온라인 스키마 변경은 DDL 실행이 아니라, shadow table, sync, validation, cutover, rollback까지 포함한 운영 절차다.
