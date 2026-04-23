# Cursor Compatibility Sampling for Cutover

> 한 줄 요약: projection migration canary에서 paginated endpoint는 legacy cursor reuse, requested/emitted cursor version, `page1 -> page2` continuity를 한 sampling contract로 묶어야 restart-only 전환과 진짜 compatibility를 구분할 수 있다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Projection Canary Cohort Selection](./projection-canary-cohort-selection.md)
> - [Cursor Pagination and Sort Stability Pattern](./cursor-pagination-sort-stability-pattern.md)
> - [Normalization Version Rollout Playbook](./normalization-version-rollout-playbook.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Dual-Read Comparison / Verification Platform 설계](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: cursor compatibility sampling, projection cutover pagination canary, legacy cursor reuse canary, legacy cursor reuse allowlist, cursor version canary matrix, requested emitted cursor version, cursor reissue canary sampling, cursor reject restart expected, two page continuity sampling, page1 page2 continuity canary, pagination-specific canary checks, projection migration pagination sampling, cursor cutover sample floor, legacy cursor acceptance drift, cursor verdict pair, continuity outcome, fingerprint bucket, page size bucket, cutover rollback cursor evidence

---

## 핵심 개념

paginated endpoint cutover canary는 단순히 "새 projection도 첫 페이지가 비슷하게 나온다"를 보는 실험이 아니다.

- legacy cursor를 계속 받아도 되는가
- 안 된다면 어떤 version으로 재발급하거나 거절하는가
- 그 판단 뒤에 page 2까지 연속성이 실제로 유지되는가

이 세 질문을 따로 샘플링하면 흔히 false green이 나온다.

- fresh query sample은 녹색인데 legacy reuse traffic은 한 번도 안 탔음
- `REISSUE`와 `REJECT`가 같은 restart bucket으로 뭉개짐
- `ACCEPT`는 표면상 성공인데 page 2에서 duplicate/gap이 터짐

이 문서는 [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)의 cutover 계약을 canary sampling 관점으로 더 좁혀, **legacy cursor reuse, cursor versioning, two-page continuity**를 어떻게 같이 증명할지 설명한다.

### Retrieval Anchors

- `cursor compatibility sampling`
- `legacy cursor reuse canary`
- `cursor version canary matrix`
- `requested emitted cursor version`
- `two page continuity sampling`
- `page1 page2 continuity canary`
- `cursor cutover sample floor`
- `legacy cursor acceptance drift`

---

## 깊이 들어가기

### 1. sample unit은 `fingerprint bucket x requested cursor version x page-size bucket`이다

cursor compatibility canary에서 최소 샘플 단위는 "한 요청"보다 더 좁고 더 구체적이어야 한다.

| 축 | 예시 | 왜 필요한가 |
|---|---|---|
| `endpoint_id` | `orders.search` | 다른 목록 contract와 섞이지 않게 한다 |
| `fingerprint_bucket` | `norm:v2->v2|fp:a->a|sort:createdAt:DESC:id|size:20` | 같은 query/sort 세계인지 고정한다 |
| `requested_cursor_version` | `0`, `1`, `2` | fresh world와 legacy world를 분리해 본다 |
| `cursor_path_class` | `FRESH`, `LEGACY_ACCEPT_PROBE`, `LEGACY_REISSUE_PROBE`, `LEGACY_REJECT_PROBE` | policy별 성공/실패 의미가 다르다 |
| `page_depth` | `page1-only`, `page1-to-page2` | continuity를 실제로 증명했는지 구분한다 |

fresh query sample이 많다고 legacy cursor compatibility가 증명되지는 않는다.  
반대로 legacy cursor sample만 보고 fresh world의 stable sort를 생략해도 안 된다.  
canary는 최소한 **fresh path와 legacy reuse path를 다른 bucket으로 분리해 샘플링**해야 한다.

### 2. legacy cursor reuse는 allowlist 기반으로 샘플링해야 한다

legacy cursor reuse는 "decode되면 일단 받아 준다"가 아니라, endpoint/sort/fingerprint family별 allowlist 정책이어야 한다.

| 정책 | canary에서 묻는 질문 | green 의미 | 즉시 중지 신호 |
|---|---|---|---|
| `ACCEPT` | legacy cursor가 같은 semantic page chain을 계속 유지하는가 | allowlist bucket에서만 나오고 `page1 -> page2`가 `PASS`다 | allowlist 밖 `ACCEPT`, 또는 `ACCEPT`인데 continuity break |
| `REISSUE` | legacy request를 새 cursor world로 안정적으로 넘기는가 | `requested -> emitted` version과 reason code가 고정되고, 재발급 cursor로 page 2가 녹색이다 | bucket별 emitted version 혼합, silent `ACCEPT`, restart 후 page 2 drift |
| `REJECT` | cutoff 경계가 명시적이고 restart가 회복 가능한가 | reject reason과 재시작 경로가 일관된다 | reject reason drift, 일부 노드만 `ACCEPT` 또는 `REISSUE` |

특히 `ACCEPT`는 가장 보수적으로 남겨야 한다.  
projection, sort, null ordering, collation, normalization contract가 완전히 같다고 증명된 좁은 bucket만 allowlist에 올리고, 그 외는 기본 `REISSUE` 또는 `REJECT`로 두는 편이 안전하다.

### 3. requested/emitted cursor version matrix를 별도 증거로 남겨야 한다

cursor versioning canary는 단순히 "legacy traffic이 있었다"가 아니라, **무슨 version을 요청했고 무슨 version을 응답으로 보냈는지**를 분리해서 기록해야 한다.

| requested cursor version | verdict | emitted cursor version | canary 해석 |
|---|---|---|---|
| `v2` | `ACCEPT` | `v2` | current world normal path |
| `v1` | `REISSUE` | `v2` | 점진 전환이 의도대로 동작함 |
| `v1` | `REJECT` | 없음 | hard cutoff가 의도대로 동작함 |
| `v1` | `ACCEPT` | `v1` 또는 `v2` | 가장 위험한 bucket. stable sort parity와 page 2 continuity가 함께 증명돼야만 green |

여기서 꼭 남겨야 하는 필드는 다음과 같다.

- `requested_cursor_version`
- `candidate_cursor.verdict`
- `candidate_cursor.emitted_version`
- `candidate_cursor.reason_code`
- canonical `cursor_verdict_pair`

이 matrix가 없으면 `REISSUE`가 의도된 restart인지, 일부 노드의 split-brain인지, 또는 잘못된 downgrade/upgrade인지 구분할 수 없다.

### 4. `compatible`이라고 부르는 경로는 반드시 2-page chain까지 따라가야 한다

page 1만 비교하면 legacy reuse의 가장 위험한 failure를 놓친다.

1. 같은 bucket으로 page 1을 요청한다
2. verdict, emitted cursor version, reason code를 기록한다
3. `ACCEPT`면 그대로, `REISSUE`면 재발급된 cursor로 page 2를 요청한다
4. `page1 ∪ page2`의 key/order/duplicate/gap을 비교한다

이때 outcome 해석은 보통 아래처럼 가져간다.

| outcome | 의미 | 승격 해석 |
|---|---|---|
| `PASS` | page 1, page 2, verdict가 정책과 일치 | green |
| `RESTART_EXPECTED` | `REISSUE` 또는 `REJECT`가 의도된 정책이고 restart가 정상 | cursor-policy green, full continuity green과는 별도 |
| `VERDICT_DRIFT` | 예상 allowlist나 version matrix와 다른 verdict | freeze 또는 rollback 검토 |
| `DUPLICATE_OR_GAP` | union에서 duplicate 또는 gap 발생 | hard stop |
| `UNKNOWN` | page 2 follow-up 또는 packet 필드가 빠져 판정 불가 | observability stop |

특히 `legacy accepted but second-page mismatch`는 비율이 낮아도 보통 hard rollback 성격으로 본다.  
page 1 parity가 좋아 보여도 사용자가 실제로 보는 pagination contract는 이미 깨졌기 때문이다.

### 5. stage gate는 총 요청 수가 아니라 pagination-specific floor를 가져야 한다

[Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)가 traffic/sample/dwell 네 축을 설명했다면, paginated endpoint는 그 sample floor를 아래처럼 더 좁혀 적는 편이 좋다.

| Stage | 최소 pagination 증거 | 다음 단계로 올려도 되는 의미 |
|---|---|---|
| `SHADOW SMOKE` | top default bucket + 실제 live legacy version family가 모두 관측됨. allowlist 밖 `ACCEPT` 0건 | serve 이전 blind spot이 없다 |
| `CANARY 1%` | 각 `ACCEPT` allowlist bucket에 `page1 -> page2` `PASS` sample이 있고, 각 `REISSUE` bucket은 `requested -> emitted` matrix가 고정됨 | low-risk serving에서 compatibility 의미가 선명하다 |
| `CANARY 10%` | representative `fingerprint_bucket`, 주요 `page_size_bucket`, 주요 legacy version family가 모두 녹색 | 대표 사용자 분포에서도 cursor contract가 흔들리지 않는다 |
| `CANARY 25~50%` | strict bucket, non-default sort, large-page bucket, historical hotspot bucket까지 재확인 | full traffic 직전의 tail risk가 줄었다 |
| `PRIMARY + ROLLBACK WINDOW` | historically bad bucket과 restart-heavy bucket을 계속 샘플링하고 reason-code 분포도 안정적 | old projection 제거 전까지 latent compatibility bug를 추적한다 |

운영적으로는 total request floor와 별도로 아래 바닥을 둔다.

- `ACCEPT` allowlist bucket별 2-page chain floor
- `REISSUE` bucket별 `requested -> emitted` version floor
- 주요 `page_size_bucket`별 continuity floor
- historical hotspot bucket 재관측 floor

즉 "총 5천 건 봤다"보다 **어느 cursor family와 어느 page-size family를 실제로 봤는가**가 더 중요하다.

### 6. pagination compatibility는 일반 mismatch rate보다 더 빠르게 중지해야 한다

다음 신호는 보통 generic compare mismatch보다 강한 우선순위를 갖는다.

| 신호 | 기본 대응 | 이유 |
|---|---|---|
| allowlist 밖 `ACCEPT` | 즉시 freeze | 선언되지 않은 compatibility drift다 |
| `ACCEPT` bucket의 `DUPLICATE_OR_GAP` | hard rollback 검토 | 사용자가 보는 pagination bug다 |
| 같은 bucket에서 emitted version 혼합 | freeze | node/version skew 가능성이 높다 |
| `REJECT` reason drift 또는 restart failure 증가 | freeze | client-visible contract가 흔들린다 |
| `UNKNOWN` chain 비율 증가 | observability stop | blind spot을 녹색으로 세면 안 된다 |

핵심은 `REISSUE`나 `REJECT`가 많다는 사실 자체가 실패가 아니라는 점이다.  
실패는 **정해 둔 policy와 다른 verdict가 나오거나, compatibility라고 선언한 bucket이 page 2에서 깨지는 것**이다.

### 7. sign-off packet은 "호환성 verdict"를 바로 읽을 수 있어야 한다

cutover sign-off에서는 최소한 아래 질문이 yes/no로 답돼야 한다.

1. live traffic에 남아 있는 `requested_cursor_version` family가 모두 파악됐는가
2. family별 정책이 `ACCEPT` / `REISSUE` / `REJECT` 중 하나로 고정됐는가
3. `ACCEPT` family는 `fingerprint_bucket x page_size_bucket` 기준 2-page `PASS`가 충분한가
4. `REISSUE` family는 requested/emitted version matrix와 restart 후 page 2가 안정적인가
5. `REJECT` family는 reason code와 fresh restart 경로가 클라이언트 계약상 안정적인가
6. rollback 시 다시 canonical로 볼 cursor version 집합이 문서화됐는가

이 질문이 한 packet으로 정리되지 않으면 팀은 "page 1은 맞다"와 "legacy cursor compatibility가 증명됐다"를 자꾸 혼동한다.

---

## 실전 시나리오

### 시나리오 1: mobile `v1` cursor를 `v2`로 재발급하는 점진 전환

mobile release가 느려 `v1` cursor traffic이 당분간 남는다고 해 보자.

- `requested_cursor_version=v1`
- verdict는 항상 `REISSUE`
- emitted version은 항상 `v2`
- `v2` cursor로 이어진 page 2는 `PASS`

이 경우 canary의 녹색 의미는 "legacy reuse가 안전하다"가 아니라 **restart-based compatibility가 안전하다**다.

### 시나리오 2: tie-breaker를 추가했는데 일부 버킷이 여전히 `ACCEPT`하는 경우

`createdAt DESC`에서 `createdAt DESC, id DESC`로 계약을 강화했는데 일부 노드가 예전 allowlist를 그대로 둔다고 해 보자.

- page 1 key 집합은 거의 같음
- `requested=v1` bucket 일부에서 `ACCEPT`
- page 2 union에서 duplicate/gap 발생

이건 low-rate mismatch가 아니라 **허용되지 않은 compatibility drift**다.  
`ACCEPT` sample 한 건만으로도 freeze 또는 rollback 검토가 정당하다.

### 시나리오 3: `size=20`만 봐서 false green이 나는 경우

top traffic가 대부분 `size=20`이라 그 bucket만 녹색이라고 승격했다고 해 보자.

- `size=20`은 `PASS`
- `size=100` bucket은 canary 표본이 거의 없음
- full traffic 이후 `size=100`에서 second-page mismatch 발생

그래서 page-size family를 packet의 first-class bucket으로 두지 않으면, canary는 steady-state pagination risk를 과소평가하기 쉽다.

---

## 코드로 보기

### compatibility sample verdict

```java
public record CursorCompatibilitySample(
    String fingerprintBucket,
    String pageSizeBucket,
    int requestedCursorVersion,
    CursorVerdict verdict,
    Integer emittedCursorVersion,
    ContinuityOutcome continuityOutcome,
    boolean duplicateDetected,
    boolean gapDetected,
    String reasonCode
) {
    public boolean blocksPromotion(boolean acceptAllowlisted) {
        if (verdict == CursorVerdict.ACCEPT && !acceptAllowlisted) {
            return true;
        }
        if (verdict == CursorVerdict.ACCEPT
            && continuityOutcome != ContinuityOutcome.PASS) {
            return true;
        }
        return duplicateDetected || gapDetected;
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| fresh-query 중심 canary | 계측 비용이 낮다 | legacy cursor blind spot이 남는다 | legacy traffic이 사실상 없을 때만 |
| allowlist `ACCEPT` + 2-page chain 샘플링 | 진짜 compatibility를 증명할 수 있다 | page 2 follow-up 비용이 든다 | continuity를 유지해야 하는 목록 |
| 기본 `REISSUE` / `REJECT` 전략 | 해석이 선명하다 | restart UX가 필요하다 | sort/normalization semantics가 달라졌을 때 |
| total request floor만 보는 승격 | 운영 규칙이 단순하다 | version family와 size family blind spot이 남는다 | 내부 smoke 수준에서만 제한적으로 |

판단 기준은 다음과 같다.

- `ACCEPT`를 늘리기 전에 2-page `PASS` 증거를 먼저 모은다
- `REISSUE`는 page 1 응답만이 아니라 reissued cursor의 page 2까지 본다
- page-size bucket과 hotspot bucket을 total count에 묻지 않는다
- `UNKNOWN` sample을 조용히 버리지 않는다

---

## 꼬리질문

> Q: legacy cursor가 decode되고 page 1도 같으면 `ACCEPT`로 봐도 되나요?
> 의도: decode 가능성과 semantic compatibility를 구분하는지 본다.
> 핵심: 아니다. page 2 continuity와 allowlist 정책까지 녹색이어야 한다.

> Q: `REISSUE`는 page 1만 안정적이면 충분하지 않나요?
> 의도: restart-based compatibility를 continuity와 연결해 보는지 본다.
> 핵심: 아니다. 재발급된 새 cursor로 이어지는 page 2도 확인해야 한다.

> Q: `REJECT` sample이 많으면 canary 실패인가요?
> 의도: verdict 양과 policy drift를 구분하는지 본다.
> 핵심: 아니다. 의도된 `REJECT`면 green일 수 있다. 대신 reason code와 restart 경로가 안정적이어야 한다.

> Q: 왜 page-size bucket을 따로 봐야 하나요?
> 의도: boundary drift가 size family에 숨는다는 점을 아는지 본다.
> 핵심: page boundary와 second-page mismatch는 `20`, `50`, `100+` bucket별로 다르게 나타날 수 있다.

## 한 줄 정리

paginated endpoint cutover canary는 legacy cursor family, emitted cursor version, `page1 -> page2` continuity를 같은 sample language로 묶어야만 "호환된다"와 "그냥 첫 페이지가 비슷했다"를 구분할 수 있다.
