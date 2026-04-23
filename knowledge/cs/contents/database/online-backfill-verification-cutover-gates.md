# Online Backfill Verification, Drift Checks, and Cutover Gates

> 한 줄 요약: online backfill의 진짜 마지막 단계는 copy 완료가 아니라, row count·checksum·sample diff·late write 검증을 통과하고도 cutover해도 된다는 증거를 모으는 것이다.

**난이도: 🔴 Advanced**

관련 문서:

- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)
- [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)
- [Destructive Schema Cleanup, Column Retirement, and Contract-Phase Safety](./destructive-schema-cleanup-column-retirement.md)
- [Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md)
- [Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
- [SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md)

retrieval-anchor-keywords: backfill verification, cutover gate, checksum validation, sample diff, late write verification, shadow read compare, migration acceptance criteria, backend data cutover, authority transfer, identity cutover, auth shadow evaluation, deprovision tail, online backfill shadow compare

## 핵심 개념

online backfill이 위험한 이유는 복사 자체보다, "이제 source와 target이 충분히 같다고 믿어도 되는가"를 잘못 판단하기 쉽기 때문이다.

필요한 질문:

- row count가 같은가
- 중요한 컬럼 값도 같은가
- 늦게 들어온 write가 target에도 반영됐는가
- 읽기 경로를 잠깐 바꿔도 결과가 같은가

즉 verification은 모니터링 부록이 아니라, **cutover 승인 절차**다.

## 깊이 들어가기

### 1. row count는 시작점일 뿐 종료 조건이 아니다

count가 같아도 다음이 틀릴 수 있다.

- 일부 컬럼만 오래된 값
- tombstone/delete 누락
- 중복 row가 다른 row를 가려서 count는 같음
- target의 파생 컬럼 계산 오류

그래서 count는 "아주 크게 망가졌는지" 확인하는 첫 문턱일 뿐이다.

### 2. checksum은 범위를 잘라서 봐야 실용적이다

테이블 전체 checksum 하나만 보면:

- mismatch는 알 수 있지만
- 어디가 틀렸는지 찾기 어렵다

더 현실적인 방식:

- PK range별 checksum
- 날짜/tenant bucket별 checksum
- 핵심 컬럼 subset checksum

이렇게 해야 mismatch가 나도 repair scope를 좁힐 수 있다.

### 3. sample diff는 "현실적인 거짓 양성/음성"을 줄여 준다

checksum은 강력하지만 다음 상황엔 sample diff가 필요하다.

- 계산 컬럼이 포함됨
- serialization/format 차이 있음
- 일부 nullable/default semantics 차이 확인 필요

즉 sample diff는 정합성의 증거라기보다, **checksum mismatch의 원인을 해석하는 도구**다.

### 4. late write verification이 빠지면 cutover 직전에 틀어진다

많은 backfill이 마지막에 실패하는 이유:

- snapshot copy는 맞았음
- catch-up도 한 번 돌았음
- 하지만 cutover 직전 몇 초의 write가 target에 늦게 반영됨

그래서 필요한 gate:

- 마지막 watermark 이후 delta 적용 완료
- source와 target latest write horizon 비교
- 필요 시 짧은 write freeze/fence

verification은 과거 데이터뿐 아니라 **가장 최근 변화까지 포함**해야 한다.

### 5. shadow read compare가 가장 설득력 있는 cutover gate일 때가 많다

실제 API/read path로 source와 target을 동시에 조회해 비교하면:

- 앱이 실제로 읽는 projection 기준으로 검증할 수 있고
- schema/type/default 차이도 함께 볼 수 있다

보통은:

- read-only mirror query
- 일부 tenant/traffic 샘플 shadow compare
- mismatch logging

를 통해 점진적으로 confidence를 올린다.

### 6. data shadow compare와 auth shadow evaluation은 서로 대체하지 않는다

source와 target row가 같아 보여도 access decision은 아직 다를 수 있다.

- tenant membership row는 맞지만 authz cache가 stale하다
- SCIM deprovision이 local DB에는 반영됐지만 session/refresh revoke가 늦다
- new claim/policy version이 같은 row를 보고도 다른 allow/deny를 낸다

즉 `shadow read mismatch = 0`은 **data parity** 증거이고,
`auth shadow divergence = 0`은 **decision parity** 증거다.

identity/session/authz authority transfer가 함께 움직이는 cutover라면
[Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md),
[SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md),
[Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md)를 같이 봐야 한다.

### 7. cutover gate는 pass/fail 기준이 숫자로 있어야 한다

예시:

- row count mismatch = 0
- bucket checksum mismatch < 0.01%
- shadow read mismatch = 0 for 24h
- late write lag < 5s

숫자가 없으면 cutover는 감으로 결정되고, 실패 후 책임도 흐려진다.

## 실전 시나리오

### 시나리오 1. count는 같은데 관리자 화면만 다름

원인:

- 일부 파생 컬럼/최근 상태만 target이 뒤처짐

교훈:

- count만으로 cutover하면 안 된다
- shadow read와 recent-write verification이 필요하다

### 시나리오 2. 특정 tenant만 mismatch가 남음

bucket checksum이 `tenant_id=42` 범위에서만 틀리면 전체 rebuild보다 그 범위만 repair하는 편이 낫다.

즉 verification 설계는 repair unit 설계와 같이 가야 한다.

### 시나리오 3. cutover 직후 source rollback을 고민함

검증 gate가 약하면 cutover 뒤에 뒤늦게 mismatch를 발견하게 된다.

이 경우는 rollback보다 bounded repair가 더 현실적일 수 있다.

## 코드로 보기

```sql
CREATE TABLE backfill_verification_run (
  run_id BIGINT PRIMARY KEY,
  target_name VARCHAR(100) NOT NULL,
  scope_key VARCHAR(255) NOT NULL,
  row_count_match BOOLEAN NOT NULL,
  checksum_match BOOLEAN NOT NULL,
  sample_diff_count BIGINT NOT NULL,
  latest_watermark VARCHAR(255) NOT NULL,
  verified_at TIMESTAMP NOT NULL
);
```

```text
cutover gates
1. count gate
2. checksum gate
3. sample diff gate
4. late write gate
5. shadow read gate
6. authority transfer gate (if auth/session plane also moves)
7. rollback/repair plan prepared
```

```java
if (!verification.allGatesPassed()) {
    throw new CutoverBlockedException();
}
```

핵심은 검증 코드보다, 어느 mismatch까지 허용하고 어디서 cutover를 멈출지를 미리 합의하는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| row count only | 가장 단순하다 | false confidence가 크다 | 초기 smoke check |
| bucket checksum | 범위별 검증이 가능하다 | 구현과 해석이 필요하다 | 대부분의 backfill |
| shadow read compare | 앱 관점 검증이 강하다 | 운영 로깅/비용이 든다 | 중요한 read path cutover |
| write freeze gate | 마지막 정합성 확보에 강하다 | 짧아도 쓰기 중단이 생긴다 | 강한 정합성 cutover |

## 꼬리질문

> Q: row count가 같으면 cutover해도 되나요?
> 의도: count와 data correctness를 구분하는지 확인
> 핵심: 아니다. checksum, sample diff, recent-write verification이 추가로 필요하다

> Q: checksum은 왜 bucket별로 보는 게 좋나요?
> 의도: 검증과 repair scope를 연결하는지 확인
> 핵심: mismatch가 났을 때 범위를 좁혀 원인 분석과 재처리를 쉽게 하기 위해서다

> Q: cutover 직전 가장 놓치기 쉬운 검증은 무엇인가요?
> 의도: late write 문제를 인식하는지 확인
> 핵심: 마지막 watermark 이후 들어온 recent write가 target에도 반영됐는지 보는 것이다

## 한 줄 정리

backfill verification의 목적은 "복사가 끝났다"가 아니라, shadow read와 recent-write gate까지 포함해 cutover를 승인할 만큼 source와 target이 충분히 같다는 증거를 만드는 것이다.
