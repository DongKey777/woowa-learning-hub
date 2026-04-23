# Pinned Legacy Chain Risk Budget

> 한 줄 요약: `ACCEPT` / pinned legacy chain은 "decode 가능한 cursor를 잠깐 받아 준다"가 아니라 old/legacy cursor world의 page `2+` continuity를 짧게 운영하는 예외 계약이므로, justify gate, seconds-scale TTL, 전용 capacity reserve, rollback 시 즉시 종료 규칙을 함께 가진 risk budget으로만 허용해야 한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)
> - [Cursor Rollback Packet](./cursor-rollback-packet.md)
> - [Cursor Compatibility Sampling for Cutover](./cursor-compatibility-sampling-cutover.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Legacy Cursor Reissue API Surface](./legacy-cursor-reissue-api-surface.md)
> - [Session Pinning vs Version-Gated Strict Reads](./session-pinning-vs-version-gated-strict-reads.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)

retrieval-anchor-keywords: pinned legacy chain risk budget, accept pinned chain ttl, pinned chain capacity reserve, pinned chain rollback expiry, legacy cursor accept allowlist, pinned chain accept justification, page2 continuity budget, fallback continuity reserve, accept as costly exception, strict pagination accept criteria, legacy chain rollback zero ttl, accept pinned chain rollback constraints, active pinned chain cap, pinned fallback reserve sizing

---

## 핵심 개념

`ACCEPT` / pinned legacy chain은 page `1`만 old path에서 살리는 shortcut이 아니다.  
의미는 **legacy/fallback source가 발급한 cursor world를 page `2+`에서도 한동안 계속 정답처럼 다루겠다**는 약속이다.

그래서 이 선택은 세 비용을 동시에 만든다.

- 시간 비용: non-canonical world를 몇 초 더 유지한다
- 용량 비용: same-source continuation을 위해 reserve를 따로 잡아야 한다
- 복구 비용: rollback이 오면 chain을 어떻게 끊을지 미리 정해야 한다

즉 `ACCEPT`는 "cursor가 decode된다"가 아니라, **continuity 자체에 예산을 쓴다**는 결정이다.

### Retrieval Anchors

- `pinned legacy chain risk budget`
- `accept pinned chain ttl`
- `pinned chain capacity reserve`
- `pinned chain rollback expiry`
- `legacy cursor accept allowlist`
- `page2 continuity budget`
- `accept as costly exception`
- `active pinned chain cap`

---

## 깊이 들어가기

### 1. `ACCEPT`는 continuity가 product promise일 때만 정당화된다

다음 중 하나라도 아니면 기본값은 `REISSUE` 또는 `REJECT`가 더 안전하다.

| justify gate | 반드시 참이어야 하는 것 | 하나라도 비면 어떻게 볼까 |
|---|---|---|
| UX reason | page `1` restart가 아니라 page `2+` continuity 자체가 사용자 약속이다 | continuity보다 visibility가 중요하면 `page1-only + REISSUE/REJECT` |
| Scope | actor-owned 또는 매우 좁은 allowlist endpoint/query/sort/page-size 조합이다 | 넓은 search/list면 사실상 dual-stack serving |
| Semantic parity | sort/filter/null ordering/collation/cursor schema가 실질적으로 같다 | semantic drift 가능성이 있으면 `ACCEPT` 금지 |
| Evidence | fingerprint bucket별 `page1 -> page2` `PASS` sample과 allowlist 밖 `ACCEPT=0`이 증명됐다 | page `1` green만으로는 부족 |
| Ownership | fallback source owner와 on-call이 reserve, breaker, rollback을 승인했다 | "편해서 남겨 둔 ACCEPT"로 간주 |

특히 다음 상황은 `ACCEPT`를 정당화하기 어렵다.

- 일반 검색이나 공개 목록처럼 restart가 받아들여질 수 있는 경우
- normalization version, tie-breaker, collation, page-size bucket drift가 있는 경우
- old projection을 오래 남겨 두려는 운영 편의가 주 이유인 경우
- chain을 끊었을 때의 UX 문구보다 `ACCEPT` 경로 구현이 더 쉬운 경우

한 줄로 줄이면 이렇다.  
**continuity가 명시적 제품 약속이고, 그 continuity가 좁은 scope에서만 증명될 때만 `ACCEPT`를 검토한다.**

### 2. `ACCEPT` proof는 decode proof가 아니라 same-world proof여야 한다

legacy cursor를 읽을 수 있다는 사실만으로는 부족하다.  
`ACCEPT` 전에 아래 네 가지가 같이 증명돼야 한다.

1. requested cursor world와 served cursor world가 같은 normalized query fingerprint를 가진다.
2. sort/filter/null ordering/collation/tie-breaker가 page `2+`에서도 같은 boundary row를 만든다.
3. allowlist bucket별 `page1 -> page2` continuity sample이 충분하고 duplicate/gap이 없다.
4. allowlist 밖 `ACCEPT` sample은 `0`건이다.

즉 `ACCEPT` verdict는 "legacy cursor를 이해했다"가 아니라 **same world를 계속 유지해도 된다고 증명했다**는 뜻이어야 한다.

### 3. risk budget은 `TTL + reserve + rollback` 세 축이 함께 있어야 한다

| 축 | 질문 | 안전한 기본값 |
|---|---|---|
| TTL | old/legacy world continuity를 얼마나 오래 살릴 것인가 | 초 단위의 짧은 absolute TTL |
| Capacity reserve | 그 TTL 동안 몇 개의 active chain과 몇 RPS를 버틸 것인가 | dedicated reserve와 breaker를 별도 확보 |
| Rollback | canonical world가 바뀌면 chain을 어떻게 끊을 것인가 | 기본 `pinned_chain_ttl_after_rollback=0` |

이 셋 중 하나라도 비어 있으면 `ACCEPT`는 계약이 아니라 낙관적 희망이 된다.

### 4. TTL은 "짧고, 절대적이고, 연장되지 않는" 형태여야 한다

`ACCEPT` TTL은 cursor가 살아 있는 전체 수명이 아니라 **legacy continuity를 허용하는 짧은 strict window**다.  
안전한 규칙은 아래처럼 두는 편이 좋다.

| TTL rule | 기본 추천 | 이유 |
|---|---|---|
| 시작 시점 | page `1` 응답 발급 시각 | chain 시작점이 같아야 budget 해석이 쉽다 |
| 형태 | absolute TTL, non-sliding | page `2`를 눌렀다고 clock를 다시 늘리지 않는다 |
| 일반 기본값 | `5~10초` | strict window 수준의 continuity만 허용 |
| 일반 상한 | `30초` 이내 | 그 이상이면 reserve와 rollback 해석이 급격히 무거워진다 |
| 예외 상한 | `<=60초`, 명시적 승인 필요 | rollback exception bridge 수준의 마지막 상한 |
| `60초` 초과 | fallback이 아니라 dual-pagination 운영으로 간주 | budget이 아니라 별도 아키텍처 문제 |

TTL과 함께 page-depth cap도 같이 두는 편이 안전하다.

- 보통 `max_page_depth=2` 또는 `3`
- TTL 만료 또는 page-depth 초과 시 `ACCEPT`를 연장하지 않음
- 만료 뒤에는 `REISSUE` 또는 `REJECT`로 page `1` restart boundary를 명시

핵심은 `ACCEPT`가 "스크롤하는 동안 계속 편하게 유지"가 아니라, **짧게 continuity를 버티게 해 주는 비싼 예외**라는 점이다.

### 5. capacity reserve는 요청 수가 아니라 active chain 기준으로도 잡아야 한다

`page1-only fallback` reserve를 그대로 재사용하면 `ACCEPT` 비용을 과소평가하게 된다.  
`ACCEPT`는 later-page 요청과 chain registry 비용이 추가되기 때문이다.

최소 산정은 아래 네 값이 필요하다.

```text
required_chain_start_rps = peak_page1_strict_rps x accept_activation_ratio x burst_multiplier
required_pinned_request_rps = required_chain_start_rps x avg_requests_per_chain
required_concurrency = required_pinned_request_rps x p99_fallback_latency_seconds
active_pinned_chains = required_chain_start_rps x pinned_chain_ttl_seconds
```

여기서 중요한 해석은 다음과 같다.

- `accept_activation_ratio`: strict traffic 중 실제 `ACCEPT` chain으로 들어갈 비율
- `avg_requests_per_chain`: page `1` 이후 평균적으로 몇 번 더 same-source를 탈지
- `active_pinned_chains`: session pin store, cursor registry, connection pressure를 함께 설명

운영 계약은 보통 아래 항목을 함께 남긴다.

| reserve field | 꼭 적어야 하는 것 | 기본 해석 |
|---|---|---|
| `reserved_rps` | baseline 제외 후 `ACCEPT` chain 전용 RPS | page1-only reserve와 분리 |
| `reserved_concurrency` | same-source continuation을 감당할 in-flight 상한 | DB/search thread pool 보호 |
| `max_active_pinned_chains` | 동시에 유지할 chain 수 상한 | TTL이 길수록 빠르게 커짐 |
| `admission policy` | reserve 부족 시 새 chain을 어떻게 다룰지 | 새 `ACCEPT` admission 중지, `REISSUE/REJECT` downgrade |
| `breaker threshold` | 언제 open할지 | util 90% 또는 command/read p99 악화 |

실무 기본값은 이렇다.

- `ACCEPT` reserve는 general fallback spare capacity에 기대지 않는다
- reserve를 태우기 시작하면 먼저 **새 pinned chain admission**을 닫는다
- reserve가 빠르게 줄면 `ACCEPT` cohort를 `page1-only + REISSUE/REJECT`로 downgrade한다
- residual headroom이 `20%` 미만으로 떨어지면 canary/promotion을 멈춘다

즉 `ACCEPT`는 "page `2`도 되겠지"가 아니라 **active chain 숫자까지 돈다**는 전제로만 허용한다.

### 6. rollback 제약은 기본적으로 `zero-ttl after rollback`이어야 한다

rollback이 오면 `ACCEPT` chain은 더 이상 정답 world가 아니다.  
그래서 기본 규칙은 단순해야 한다.

| rollback question | 기본값 | 이유 |
|---|---|---|
| rollback 뒤 기존 pinned legacy chain을 계속 받을까 | 아니오 | split-brain 시간을 늘리지 않기 위해 |
| `pinned_chain_ttl_after_rollback_seconds` | `0` | canonical world를 빨리 하나로 줄인다 |
| rollback 뒤 허용되는 recovery | `REISSUE` 또는 `REJECT` 기반 page `1` restart만 | page depth를 보존하지 않는다 |
| mixed old/new/reissued cursor | 항상 `REJECT` | boundary row 계산 기준이 모호 |
| 예외 bridge | `<=60초`, incident commander 수준 승인 | 기본값이 되면 rollback 의미가 사라진다 |

rollback 이후 invariant는 아래처럼 고정하는 편이 안전하다.

1. page `N` continuity보다 page `1` restart를 우선한다.
2. `rollback_epoch`가 바뀌면 기존 pinned chain은 canonical하지 않다.
3. rollback 뒤 `ACCEPT`는 restored canonical cursor family에만 남길 수 있다.
4. retired legacy chain을 다시 살리고 싶다면 일반 packet이 아니라 예외 packet으로 승인한다.

즉 `ACCEPT`를 허용하더라도 **rollback에서는 미련 없이 끊을 수 있어야** 한다.

### 7. 최소 risk budget packet은 숫자와 종료 조건을 같이 가져야 한다

| 필드 | 꼭 적어야 하는 질문 | 예시 |
|---|---|---|
| `contract_id` | 어느 endpoint/query 조합의 budget인가 | `cases.my-queue/default-sort` |
| `continuity_reason` | 왜 restart보다 continuity가 중요한가 | 상담사가 검토 중인 queue 위치를 잃으면 안 됨 |
| `allowlist` | 어떤 fingerprint/page-size/sort bucket만 허용되는가 | default sort, `page_size<=50` |
| `pin_ttl_seconds` | 얼마나 오래 same-source chain을 살릴까 | `10` |
| `max_page_depth` | 몇 페이지까지 허용할까 | `2` |
| `reserved_rps` | 전용 reserve는 얼마인가 | `45` |
| `reserved_concurrency` | in-flight 상한은 얼마인가 | `18` |
| `max_active_pinned_chains` | 동시 chain 상한은 얼마인가 | `120` |
| `admission_on_reserve_exhaustion` | reserve가 차면 무엇을 할까 | new `ACCEPT` 차단, `REISSUE` downgrade |
| `pinned_chain_ttl_after_rollback_seconds` | rollback 뒤 chain을 얼마나 살릴까 | `0` |
| `rollback_reason_code` | chain 종료를 무엇으로 설명할까 | `ROLLBACK_CHAIN_PIN_EXPIRED` |

이 packet이 있어야 "왜 `ACCEPT`를 남겼는지"와 "언제 끊을지"가 같은 문장으로 남는다.

### 8. 빠른 의사결정 규칙

다음 네 질문에 모두 `예`라고 답하지 못하면 `ACCEPT`를 기본값으로 두지 않는 편이 맞다.

1. continuity가 page `1` visibility보다 더 중요한가
2. allowlist bucket별 same-world parity가 page `2+`까지 증명됐는가
3. page1-only fallback과 별도인 pinned-chain reserve를 잡았는가
4. rollback 시 `0초` 또는 아주 짧은 예외 bridge로 끊을 수 있는가

하나라도 `아니오`면 안전한 기본값은 보통 다음 둘 중 하나다.

- `PAGE1_STRICT_REISSUE`
- `PAGE1_STRICT_REJECT`

---

## 실전 시나리오

### 시나리오 1: 상담사 전용 내 큐 목록

- actor scope: 상담사 본인
- query scope: default sort, filter 고정
- continuity reason: 검토 중인 queue 위치를 page `2`에서 잃으면 업무 흐름이 끊김
- `pin_ttl_seconds`: `10`
- `max_page_depth`: `2`
- rollback after pin: `0초`

이 경우는 `ACCEPT`를 검토할 수 있다.  
다만 allowlist sample, dedicated reserve, rollback zero-ttl이 모두 있어야 한다.

### 시나리오 2: 일반 검색 결과

- anonymous/public traffic
- 다양한 filter와 page-size
- restart가 제품적으로 허용 가능
- sort/normalization drift 가능성이 큼

이 경우는 `ACCEPT`보다 `REISSUE` 또는 `REJECT`가 맞다.  
continuity보다 semantic safety가 중요하기 때문이다.

---

## 정리

`ACCEPT` / pinned legacy chain은 compatibility convenience가 아니라 **continuity에 쓰는 제한된 risk budget**이다.  
따라서 justify gate, 짧은 absolute TTL, dedicated reserve, rollback zero-ttl이 함께 없으면 남겨 두지 않는 편이 안전하다.

실무 기본값은 여전히 `page1-only + REISSUE/REJECT`다.  
`ACCEPT`는 그 기본값을 뒤집을 만큼 continuity 가치가 크고, 그 비용을 숫자로 감당할 수 있을 때만 허용한다.
