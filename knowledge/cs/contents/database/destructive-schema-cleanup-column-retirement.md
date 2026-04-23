# Destructive Schema Cleanup, Column Retirement, and Contract-Phase Safety

> 한 줄 요약: 컬럼 추가보다 더 위험한 순간은 old field를 실제로 제거하는 contract phase이며, 이때는 "아무도 더 이상 읽지 않는다"는 사실을 증명하는 절차가 필요하다.

**난이도: 🔴 Advanced**

관련 문서:

- [CDC Schema Evolution, Event Compatibility, and Expand-Contract Playbook](./cdc-schema-evolution-compatibility-playbook.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Instant DDL vs Inplace vs Copy Algorithms](./instant-ddl-vs-copy-inplace-algorithms.md)
- [Instant ADD COLUMN Metadata Semantics](./instant-add-column-metadata-semantics.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [Index Maintenance Window, Rollout, and Fallback Playbook](./index-maintenance-window-rollout-playbook.md)

retrieval-anchor-keywords: column retirement, destructive migration, contract phase, drop column safety, schema cleanup, expand contract, backward compatibility window, field removal runbook

## 핵심 개념

expand-contract migration에서 expand 단계는 보통 눈에 잘 띈다.

- 새 컬럼 추가
- dual write
- backfill
- read path 전환

하지만 실제 사고는 contract 단계에서 자주 난다.

- old code가 아직 old field를 읽고 있다
- replay/DLQ가 과거 schema를 다시 보낸다
- 운영 스크립트가 퇴역 컬럼을 계속 쓴다
- analytics/export 경로가 늦게 따라온다

즉 destructive cleanup은 DDL 실행보다, **의존성 제거를 증명하는 운영 절차**다.

## 깊이 들어가기

### 1. "코드에서 안 쓴다"와 "시스템에서 안 쓴다"는 다르다

애플리케이션 main path에서 old field를 제거해도 다음이 남아 있을 수 있다.

- 배치/운영 스크립트
- BI/데이터 추출 쿼리
- CDC consumer와 replay tool
- DLQ 재처리 코드
- 관리자 화면

그래서 contract phase 전 체크리스트는 코드 grep보다 넓어야 한다.

### 2. column retirement의 실제 순서는 read-off -> write-off -> drop이다

안전한 흐름:

1. new field read path 전환
2. old field shadow read 제거
3. old field write 중단
4. old field 접근 로그/메트릭 관찰
5. retention/replay window 경과 확인
6. 그 뒤에 drop/cleanup

특히 replay window가 긴 시스템은 "배포 끝남"보다 "과거 이벤트가 다시 안 들어옴"이 더 중요하다.

### 3. observability 없이는 contract phase를 자신 있게 못 한다

권장 신호:

- old column access query count
- old field 포함 이벤트/쿼리 로그
- shadow read fallback hit rate
- old field null/non-null ratio
- rollout version coverage

이런 계측이 없으면 contract phase는 감으로 하는 정리 작업이 된다.

### 4. rename migration에서는 old field drop이 마지막 cutover다

rename을 add/copy/switch/remove로 처리했다면, 마지막 remove가 사실상 최종 cutover다.

위험 신호:

- 일부 인스턴스만 아직 old field 기준 write
- 외부 파트너/consumer가 old payload에 의존
- rollback 문서가 old field 복구를 전제

이 상태에서 drop을 하면 rollback 옵션도 같이 사라질 수 있다.

### 5. DDL 자체의 비용도 contract phase에서 다시 봐야 한다

old column을 drop하는 순간은 논리 의존성만의 문제가 아니다.

- 실제 DDL 알고리즘이 instant인지
- metadata lock risk가 있는지
- replica/app compatibility가 맞는지

도 같이 본다.

즉 "이제 안 쓰니 지우자"가 아니라, **지우는 DDL 경로도 운영 변경**으로 다뤄야 한다.

### 6. cleanup은 삭제보다 tombstone 기간이 유용할 때가 있다

일부 시스템에서는 즉시 제거보다:

- old field deprecated 표시
- 접근 시 경고 로그
- 일정 기간 shadow value 유지

같은 tombstone 기간이 더 안전하다.

특히 외부 consumer가 많은 CDC 환경에서는 "deprecated but present" 기간이 사고를 줄인다.

## 실전 시나리오

### 시나리오 1. API는 새 필드를 읽는데 배치가 옛 컬럼을 계속 사용

main path는 정상이지만 야간 배치 실패가 난다.

교훈:

- contract phase 대상은 application code만이 아니다
- 운영/분석 경로까지 전수 확인이 필요하다

### 시나리오 2. old field를 drop했더니 DLQ replay 실패

현재 코드는 새 schema만 알지만, 장애 복구 중 과거 payload가 다시 들어온다.

이 경우:

- replay window 종료 전 old compatibility 유지
- adapter layer 또는 replay 전용 변환기

가 필요하다.

### 시나리오 3. 컬럼 제거 DDL이 예상보다 오래 걸림

논리적으로는 cleanup이지만 물리적으로는 non-instant 경로일 수 있다.

그래서 contract phase도 여전히 online DDL 판단과 MDL 점검이 필요하다.

## 코드로 보기

```sql
-- drop 직전 사용 여부 점검 예시
SELECT COUNT(*)
FROM information_schema.columns
WHERE table_schema = 'mydb'
  AND table_name = 'orders'
  AND column_name = 'legacy_status';
```

```text
contract phase checklist
1. app read path old-field off
2. app write path old-field off
3. background jobs updated
4. CDC/replay compatibility window cleared
5. old-field access metrics flat
6. DDL algorithm + MDL risk checked
```

```sql
ALTER TABLE orders
DROP COLUMN legacy_status;
```

핵심은 마지막 SQL이 아니라, 그 SQL을 눌러도 되는지에 대한 증거를 먼저 모으는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 빠른 drop | 정리가 빨리 끝난다 | 숨어 있던 의존성이 터질 수 있다 | 거의 신중해야 한다 |
| deprecate 기간 유지 | 안전하다 | 레거시가 오래 남는다 | replay/외부 consumer가 많을 때 |
| access metric 기반 계약 종료 | 근거가 명확하다 | 관측 설계가 필요하다 | 중요한 schema retirement |
| adapter layer 유지 | 복구에 강하다 | 코드 복잡도가 남는다 | 긴 호환성 창이 필요할 때 |

## 꼬리질문

> Q: contract phase가 왜 expand phase보다 위험할 수 있나요?
> 의도: add보다 remove가 더 파괴적임을 아는지 확인
> 핵심: 숨어 있는 old-field 의존성을 제거해야 하고 rollback 옵션도 줄어들기 때문이다

> Q: old column을 drop하기 전에 무엇을 증명해야 하나요?
> 의도: 사용 중단의 증거 기반 운영을 이해하는지 확인
> 핵심: main path뿐 아니라 배치, CDC, replay, 운영 도구가 더 이상 그 필드를 쓰지 않음을 보여야 한다

> Q: cleanup인데도 왜 online DDL 판단이 필요한가요?
> 의도: 논리 cleanup과 물리 변경을 구분하는지 확인
> 핵심: column drop도 실제로는 metadata lock과 알고리즘 차이를 갖는 DDL이기 때문이다

## 한 줄 정리

schema cleanup의 안전성은 `DROP COLUMN` 자체보다, old-field 의존성이 truly zero인지와 replay/DDL window까지 포함한 contract-phase 증거를 갖췄는지에 달려 있다.
