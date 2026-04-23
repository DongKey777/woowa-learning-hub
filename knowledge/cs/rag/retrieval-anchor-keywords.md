# Retrieval Anchor Keywords

> 한 줄 요약: 사용자가 문서 제목이 아니라 증상, 에러 문자열, 약어, 운영 용어로 질문할 때 검색을 붙잡아 주는 보조 키워드 규칙이다.

## 왜 필요한가

실제 질문은 문서 제목 그대로 들어오지 않는다.

예를 들면:

- `heap은 괜찮은데 RSS만 올라요`
- `nf_conntrack table full 떠요`
- `retry storm 같아요`
- `mTLS랑 SPIFFE 차이가 뭐예요`

이런 질문은 문서 제목보다 **증상, 에러 문자열, 약어, 도구 이름**으로 들어온다.
그래서 deep dive 문서에는 제목 외에 retrieval anchor를 남겨 두는 편이 RAG 회수율에 유리하다.

## 추천 형식

문서 상단 메타데이터 근처에 한 줄로 남긴다.

```markdown
> retrieval-anchor-keywords: direct buffer, off-heap, native memory, RSS, NMT
```

## 템플릿 삽입 포인트

- deep dive 템플릿: `한 줄 요약` / `난이도` / `관련 문서` 다음, 첫 `##` 제목 바로 전에 둔다.
- `<details>` TOC 템플릿: `</details>` 바로 아래에 두고, 첫 본문 섹션 시작 전에 고정한다.
- `README` / navigator 템플릿: 소개 문단이나 배지 블록 다음, `## 빠른 탐색` 같은 첫 안내 섹션 전에 둔다.
- 새 문서 템플릿에는 placeholder 한 줄을 미리 넣어 두고, 작성 시 comma-separated 값만 채우는 방식으로 유지한다.

### 루트 엔트리포인트 문서 고정 위치

- roadmap 템플릿: 제목 바로 아래 `한 줄 설명` 다음에 두고, `## 목표` 전에 고정한다.
- question bank 템플릿: 제목/요약 다음에 두고, `## 이 문서를 어떻게 써야 하나` 전에 고정한다.
- checklist 템플릿: 제목/요약 다음에 두고, `## 무엇을 먼저 읽나` 또는 첫 체크 섹션 전에 고정한다.
- 배지나 대표 이미지가 있는 루트 `README`는 배지 블록 직후, 첫 `##` 섹션 전에 anchor를 둬서 catalog/navigator alias를 먼저 노출한다.

## 무엇을 넣는가

### 1. 한글 개념 + 영어 원어

- `서비스 간 인증, service-to-service auth`
- `멀티 테넌트, multi-tenant`

### 2. 약어 + 풀네임

- `mTLS, mutual TLS`
- `NMT, Native Memory Tracking`
- `WAL, write-ahead logging`

### 3. 증상과 에러 문자열

- `EADDRNOTAVAIL`
- `Direct buffer memory`
- `table full, dropping packet`
- `client closed request`
- `unable to find JWK`
- `old data after write`

### 4. 운영 도구 이름

- `ss`
- `conntrack`
- `perf`
- `strace`
- `bpftrace`

### 5. 제품/구현체 이름

- `SPIFFE`
- `SPIRE`
- `Resilience4j`
- `HikariCP`

## 좋은 anchor의 특징

- 문서 제목을 그대로 반복하지 않는다.
- 사용자가 실제로 검색할 법한 표현을 넣는다.
- 같은 뜻의 표현을 4~8개 정도로 압축한다.
- 증상, 원인, 도구를 섞되 너무 길게 늘리지 않는다.

## 문서 역할 alias도 anchor에 넣는다

증상형 deep dive만 anchor가 필요한 것은 아니다. `README`나 navigator 문서도 사용자가 `survey`, `primer`, `catalog`, `deep dive` 같은 역할 이름으로 찾을 수 있으므로 alias를 같이 두는 편이 안전하다.

- `survey`: `roadmap`, `learning path`, `study order`, `big picture`
- `primer`: `basics`, `intro`, `foundation`, `first principles`
- `catalog / navigator`: `readme`, `index`, `guide`, `entrypoint`
- `deep dive / playbook`: `troubleshooting`, `failure mode`, `trade-off`, `runbook`, `recovery`, `outage`, `incident recovery`
- `question bank`: `interview questions`, `self-check`, `drill`

문서 역할 구분 기준 자체는 [Navigation Taxonomy](./navigation-taxonomy.md)와 함께 맞춰 둔다.

## 패턴 혼동 alias도 anchor에 넣는다

알고리즘 문서는 풀이 이름보다 문제 모양이 헷갈린 채 들어오는 검색이 많다.
`subsequence`, `subarray`, `substring`, `window`, `subwindow`, `contiguous`, `LIS`처럼 서로 섞여 쓰이는 표현은 metadata와 표 라벨 둘 다에 남기는 편이 회수율이 높다.

- subsequence cluster: `LIS`, `longest increasing subsequence`, `증가 부분 수열`, `subsequence`, `skip allowed`, `order preserving`
- contiguous cluster: `subarray`, `substring`, `window`, `subwindow`, `sliding window`, `contiguous only`, `recent k`
- boundary-search cluster: `binary search`, `lower_bound`, `upper_bound`, `first true`, `answer space`, `monotonic predicate`
- confusion bridge: `subsequence vs subarray`, `LIS vs sliding window`, `LIS lower_bound`, `window feasibility + binary search`, `contiguous vs skip allowed`

이 규칙은 [Query Playbook](./query-playbook.md)과 알고리즘 카테고리 navigator를 같이 손볼 때 가장 효과가 크다.

## Topic Map / Bridge 라벨에도 symptom alias와 pattern alias를 드러낸다

metadata anchor만 보강하고 표 라벨이나 섹션 제목은 추상적으로 남겨 두면, symptom query나 pattern query가 category cluster까지 닿는 속도가 느려진다.
특히 topic map, query playbook, cross-domain bridge 같은 routing helper는 표 라벨 자체에도 alias를 함께 적는 편이 좋다.
mixed cross-category bridge라면 symptom alias만이 아니라 `[playbook]`, `[deep dive]`, `[system design]` 같은 role cue도 bullet 앞이나 표 라벨에 드러내서 route shift를 숨기지 않는다.
security README처럼 `incident -> deep dive -> system design -> deep dive`가 한 bullet에 같이 나오면 later link가 앞 badge를 상속한다고 가정하지 말고, 역할이 바뀌는 첫 링크마다 cue를 다시 적어 둔다.

- freshness cluster: `freshness`, `stale read`, `read-after-write`, `projection lag`, `old data after write`, `saved but still old data`
- disconnect cluster: `client disconnect`, `client closed request`, `499`, `broken pipe`, `connection reset`
- edge 502/504 cluster: `502`, `504`, `bad gateway`, `gateway timeout`, `local reply`, `upstream reset`, `upstream prematurely closed`
- timeout mismatch cluster: `timeout mismatch`, `async timeout mismatch`, `idle timeout mismatch`, `deadline budget mismatch`, `gateway는 504인데 app은 200`, `first byte timeout`
- auth incident cluster: `JWKS outage`, `kid miss`, `unable to find jwk`, `unable to find JWK`, `auth verification outage`
- revoke lag cluster: `revoke lag`, `revocation tail`, `logout but still works`, `allowed after revoke`, `revoked admin still has access`, `role removed but still allowed`
- session-tail handoff cluster: `session-store route`, `session store handoff`, `hidden session mismatch handoff`, `session tail handoff`, `revoke-tail route`, `revocation-tail route`, `claim-version cleanup tail`, `regional revoke lag handoff`
- authz cache symptom cluster: `stale authz cache`, `stale deny`, `grant but still denied`, `tenant-specific 403`, `only one tenant 403`, `403 after revoke`, `403 after role change`, `inconsistent 401 404`, `401 404 flip`, `concealment drift`, `cached 404 after grant`
- bridge role cluster: `playbook`, `deep dive`, `system design`, `incident ladder`, `control-plane handoff`, `cutover handoff`
- authority transfer cluster: `authority transfer`, `SCIM deprovision`, `SCIM disable but still access`, `backfill is green but access tail remains`, `backfill green access tail`, `decision parity`, `data parity vs decision parity`, `shadow read green but auth decision diverges`, `auth shadow divergence`, `deprovision tail`
- cross-readme authority route aliases: security README의 `Identity / Delegation / Lifecycle`, database README의 `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`, system-design README의 `Database / Security Authority Bridge` / `Verification / Shadowing / Authority Bridge`처럼 sibling label이 갈리면 각 README metadata anchor에 서로의 route name도 같이 남긴다
- algorithm boundary cluster: `LIS`, `subsequence`, `subarray`, `subwindow`, `sliding window`, `binary search`, `lower_bound`, `first true`, `contiguous only`, `skip allowed`

이 규칙은 [Topic Map](./topic-map.md), [Query Playbook](./query-playbook.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)를 같이 맞춰 줄 때 가장 효과가 크다.

## 예시

| 문서 | anchor 예시 |
|---|---|
| `nat-conntrack-ephemeral-port-exhaustion.md` | `NAT gateway`, `conntrack`, `TIME_WAIT`, `EADDRNOTAVAIL` |
| `direct-buffer-offheap-memory-troubleshooting.md` | `off-heap`, `RSS`, `Direct buffer memory`, `NMT` |
| `service-to-service-auth-mtls-jwt-spiffe.md` | `mTLS`, `SPIFFE`, `SPIRE`, `workload identity` |
| `strangler-fig-migration-contract-cutover.md` | `shadow traffic`, `dual write`, `cutover`, `rollback` |
| `api-key-hmac-signature-replay-protection.md` | `HMAC`, `nonce`, `timestamp`, `replay attack`, `canonical string` |
| `forwarded-x-forwarded-for-x-real-ip-trust-boundary.md` | `X-Forwarded-For`, `Forwarded`, `X-Real-IP`, `trusted proxy` |
| `monotonic-clock-wall-clock-timeout-deadline.md` | `CLOCK_MONOTONIC`, `wall clock`, `deadline propagation`, `NTP jump` |
| `payment-system-ledger-idempotency-reconciliation-design.md` | `ledger`, `reconciliation`, `auth capture refund`, `double-entry` |

## 관리 규칙

- 새 운영형 문서를 만들면 anchor를 같이 넣는다.
- anchor는 metadata로 올려 query expansion에 쓴다.
- README의 역할 라벨을 바꿨다면 anchor도 함께 맞춰 `roadmap`, `index`, `self-check` 같은 alias가 남아 있는지 본다.
- symptom-first navigator를 고쳤다면 metadata anchor뿐 아니라 table row, section label, related-doc link에도 같은 alias cluster가 드러나는지 본다.
- edge/network routing을 손봤다면 `499`, `502`, `504`, `bad gateway`, `gateway timeout`, `timeout mismatch`가 separate shortcut으로 남아 있는지 본다.
- revoke/authz routing을 손봤다면 `revoke lag`, `allowed after revoke`, `stale authz cache`, `403 after revoke`가 separate shortcut으로 남아 있는지 본다.
- authz cache/debugging 문서를 손봤다면 `stale deny`, `tenant-specific 403`, `401 404 flip` 같은 alias가 deep dive metadata와 security README symptom row에 같이 남는지 본다.
- cross-category bridge를 손봤다면 `playbook`, `deep dive`, `system design` cue가 metadata anchor, section label, related-doc bullet에 같이 남는지 본다.
- authority-transfer bridge를 손봤다면 security `Identity / Delegation / Lifecycle`, database `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`, system-design `Database / Security Authority Bridge` / `Verification / Shadowing / Authority Bridge`가 서로의 README metadata anchor와 entrypoint 설명에 같이 남아 route-name mismatch를 흡수하는지 본다.
- security mixed bridge를 손봤다면 `cross-category bridge`, `deep dive`, `system design` cue가 같은 bullet 안의 role-switch 지점마다 다시 붙는지 본다.
- mixed incident catalog를 손봤다면 `[playbook]` / `[runbook]` / `[drill]` / `[incident matrix]` / `[recovery]` 옆의 개념 본문에도 `[deep dive]` cue가 붙었는지, `deep dive`, `failure mode`, affected component alias가 같은 섹션 anchor와 링크 문구에 같이 남는지 본다.
- 알고리즘 topic map을 손봤다면 `skip allowed`, `contiguous only`, `lower_bound`, `first true` 같은 경계 alias가 topic map과 query playbook에 같이 남아 있는지 본다.
- mixed incident catalog에 `[recovery]` 라벨을 붙였다면 `outage`, `degradation`, `recovery`, affected store/component alias도 anchor와 표 라벨에 같이 남긴다.
- anchor가 늘어나면 `query-playbook.md`와 `topic-map.md`도 함께 점검한다.

## 한 줄 정리

Retrieval anchor keyword는 제목 밖 검색어를 붙잡는 장치라서, 운영/장애형 문서일수록 꼭 챙기는 편이 좋다.
