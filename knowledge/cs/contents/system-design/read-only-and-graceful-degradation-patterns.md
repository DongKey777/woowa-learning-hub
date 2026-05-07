---
schema_version: 3
title: Read-Only and Graceful Degradation Patterns
concept_id: system-design/read-only-and-graceful-degradation-patterns
canonical: false
category: system-design
difficulty: intermediate
doc_role: playbook
level: intermediate
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- read-only mode
- graceful degradation patterns
- stale read fallback
- stale-if-error
aliases:
- read-only mode
- graceful degradation patterns
- stale read fallback
- stale-if-error
- cache outage degradation
- database incident read-only
- partial feature disablement
- brownout pattern
- degraded mode matrix
- bounded stale fallback
- write freeze during incident
- replica lag downgrade
symptoms:
- Read-Only and Graceful Degradation Patterns 관련 장애나 마이그레이션 리스크가 발생해 단계별 대응이 필요하다
intents:
- troubleshooting
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/request-path-failure-modes-primer.md
- contents/system-design/request-deadline-timeout-budget-primer.md
- contents/system-design/caching-vs-read-replica-primer.md
- contents/system-design/database-scaling-primer.md
- contents/system-design/distributed-cache-design.md
- contents/system-design/backpressure-and-load-shedding-design.md
- contents/system-design/read-write-quorum-staleness-budget-design.md
- contents/system-design/policy-snapshot-cache-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Read-Only and Graceful Degradation Patterns 장애 대응 순서를 알려줘
- read-only mode 복구 설계 체크리스트가 뭐야?
- Read-Only and Graceful Degradation Patterns에서 blast radius를 어떻게 제한해?
- read-only mode 운영 리스크를 줄이는 방법은?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Read-Only and Graceful Degradation Patterns를 다루는 playbook 문서다. cache 또는 database incident 때 stale read, read-only mode, partial feature disablement 중 어디까지 내려갈지 freshness budget, write safety, dependency headroom으로 가르는 문서이며, "읽기는 살리고 쓰기만 잠글 수 있나?"라는 질문의 첫 판단표를 준다. 검색 질의가 read-only mode, graceful degradation patterns, stale read fallback, stale-if-error처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Read-Only and Graceful Degradation Patterns

> 한 줄 요약: cache 또는 database incident 때 stale read, read-only mode, partial feature disablement 중 어디까지 내려갈지 freshness budget, write safety, dependency headroom으로 가르는 문서이며, "읽기는 살리고 쓰기만 잠글 수 있나?"라는 질문의 첫 판단표를 준다.

retrieval-anchor-keywords: read-only mode, graceful degradation patterns, stale read fallback, stale-if-error, cache outage degradation, database incident read-only, partial feature disablement, brownout pattern, degraded mode matrix, bounded stale fallback, write freeze during incident, replica lag downgrade, 읽기는 살리고 쓰기만 막아도 되나요, 왜 바로 maintenance mode로 안 가요, stale read랑 read-only 차이 뭐예요

**난이도: 🟡 Intermediate**

관련 문서:

- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [분산 캐시 설계](./distributed-cache-design.md)
- [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Policy Snapshot Cache 설계](./policy-snapshot-cache-design.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

---

## 핵심 개념

장애가 났다고 해서 바로 maintenance mode로 내리는 것은 보통 과하다.
처음 읽을 때는 `지금은 읽기만 살릴까, 아예 일부 기능을 꺼야 할까`를 먼저 물으면 된다.
실전에서는 먼저 아래 세 가지를 분리해서 본다.

1. **지금 읽는 데이터가 조금 오래돼도 되는가**
2. **지금 쓰기를 받아도 안전하게 commit할 수 있는가**
3. **핵심 경로를 살리기 위해 꺼도 되는 부가 기능은 무엇인가**

이 질문에 따라 선택지가 갈린다.

| 모드 | 무엇을 유지하나 | 언제 켜나 | 주의할 점 |
|---|---|---|---|
| stale read | 조회 자체는 유지 | source of truth가 느리거나 cache miss가 위험하지만 마지막 안전한 값은 있음 | 허용 stale budget이 없는 데이터에는 쓰면 안 된다 |
| partial feature disablement | 핵심 경로만 유지 | 특정 기능이 dependency fan-out, DB load, queue backlog를 키움 | "메인 기능"과 "부가 기능" 구분이 평소에 정의돼 있어야 한다 |
| read-only mode | 안전한 read만 유지 | write commit 성공률이 떨어지거나 failover 중 write safety가 불명확 | 나중에 replay/reconciliation 경계까지 같이 설계해야 한다 |

핵심은 이 셋이 **서로 대체재가 아니라 조합 가능한 손잡이**라는 점이다.

- stale read + partial disablement: cache incident 때 카탈로그는 오래된 값으로 유지하고 추천 위젯은 끈다
- read-only + partial disablement: DB primary failover 중 browse/history는 살리고 checkout/export는 막는다
- read-only + fail-closed: 권한, 잔액, 재고처럼 stale 자체가 위험한 경로는 조회도 막는다

---

## 깊이 들어가기

### 1. degradation ladder를 먼저 정의한다

많은 팀이 장애 때 "무엇을 끌까"를 그때그때 정한다.
하지만 실제로는 아래 순서를 미리 정해 두는 편이 안전하다.

```text
fresh service
  -> bounded stale read
  -> stale read + brownout(partial disablement)
  -> read-only mode
  -> fail-closed / maintenance
```

중요한 점:

- stale read는 **freshness를 희생해 availability를 산다**
- partial disablement는 **제품 면적을 줄여 capacity를 산다**
- read-only mode는 **write safety를 지키기 위해 mutability를 포기한다**

즉 같은 "degraded mode"라도 보호하려는 대상이 다르다.

### 2. cache incident에서는 stale read와 brownout을 먼저 본다

cache 장애에서 가장 흔한 실수는 cache timeout 뒤 DB fallback을 무제한으로 열어 두는 것이다.
이러면 cache incident가 곧바로 DB incident로 번진다.

cache 쪽 판단 순서는 대체로 이렇다.

| 관찰 신호 | 우선 선택 | 이유 |
|---|---|---|
| cache latency만 상승, DB headroom 충분 | quick miss 또는 cache bypass | 굳이 stale mode까지 올리지 않아도 된다 |
| cache miss 급증, DB read headroom 부족 | stale-if-error + hot read brownout | DB read amplification을 줄여야 한다 |
| cache invalidation이 꼬여 correctness가 의심됨 | stale read 금지, 민감 경로 disable | 오래된 값이 아니라 **틀린 값**일 수 있다 |
| cache cluster 일부 shard만 불안정 | hot key 보호, request coalescing, 부분 stale | 전체 read-only로 내릴 이유는 없다 |

실전 감각은 이것이다.

- stale read는 "cache가 느리다"가 아니라 **DB를 더 치면 안 되는 순간**에 가장 가치가 크다
- cache incident에서 read-only는 1차 반응이 아니라 **DB까지 흔들릴 때** 고려한다
- 추천, 정렬, facet count, 대시보드 부가 위젯처럼 fan-out이 큰 기능은 brownout 후보 1순위다

### 3. database incident에서는 write safety가 read freshness보다 먼저다

DB가 흔들릴 때는 read latency보다 **write commit의 신뢰성**을 먼저 본다.
아래 중 하나라도 보이면 read-only 전환을 진지하게 검토한다.

## 깊이 들어가기 (계속 2)

- primary commit error가 의미 있게 증가
- lock wait / pool wait이 app deadline을 잠식
- failover 중 leader가 바뀌는 중이라 fencing이 불확실
- replication topology가 흔들려 "어디가 진짜 primary인가" 판단이 늦음

이때의 선택지는 보통 아래와 같다.

| 상태 | 선택 | 이유 |
|---|---|---|
| primary write 불안정, replica read는 가능 | read-only mode | 잘못된 write를 받는 것보다 안전한 read만 유지하는 편이 낫다 |
| replica lag가 stale budget 안 | browse/history만 stale read | 읽기 UX는 살리되 최근 write 보장은 포기한다 |
| replica lag가 budget 밖 | stale read 금지, 핵심 화면 fail-fast | "보여 주는 것" 자체가 사고가 될 수 있다 |
| split-brain, restore 직후 correctness 불명확 | fail-closed for critical paths | read-only만으로 충분하지 않다 |

실전에서 read-only는 단순한 503 페이지가 아니다.
보통은 아래처럼 세분화한다.

- 주문 생성, 결제 확정, 재고 차감, 권한 변경: 즉시 차단
- 조회, 내역 열람, 카탈로그 탐색: 유지 가능하면 유지
- 관리자 대량 수정, export, backfill trigger: 우선 차단

### 4. 데이터 종류별 허용 downgrade를 미리 나눈다

incident 때 가장 위험한 질문은 "이 데이터 stale해도 되나요?"를 실시간으로 묻는 것이다.
제품별로 미리 class를 나눠 두는 편이 낫다.

| 데이터/기능 | stale read 허용 | read-only 시 유지 | partial disable 후보 | 메모 |
|---|---|---|---|---|
| 상품 카탈로그, 정적 콘텐츠 | 보통 허용 가능 | 유지 | 추천/정렬/연관상품 | `stale-if-error`에 잘 맞는다 |
| 프로필, 알림 목록, 주문 이력 | 제한적 허용 | 유지 가능 | unread count, 보조 배지 | recent-write 직후는 primary pinning이 필요할 수 있다 |
| 장바구니, draft 문서 | 짧은 stale만 제한적으로 | 서비스마다 다름 | cross-sell, preview | merge/conflict UX까지 같이 봐야 한다 |
| 재고, 잔액, quota, 권한 판단 | 대체로 비권장 | read-only만으로도 불충분할 수 있음 | 주변 보조 UI | 잘못 보여 주는 순간 사고가 난다 |
| analytics 대시보드, export, admin report | 허용 범위가 넓다 | 유지 가능 | 실시간 보조 패널 | 아예 snapshot이나 last-known-good로 내리는 편이 낫다 |

## 깊이 들어가기 (계속 3)

즉, stale read 가능 여부는 기술 레이어보다 **도메인 의미**가 더 크게 좌우한다.

### 5. 전환 신호는 latency 하나로 정하지 않는다

mode switch를 p99 latency 하나로 걸면 false positive가 많다.
보통은 세 축을 같이 본다.

1. **correctness risk**
2. **capacity risk**
3. **recovery confidence**

예시 guardrail:

| 질문 | stale read로 가는 신호 | read-only로 가는 신호 | disable로 가는 신호 |
|---|---|---|---|
| freshness가 예산 안인가 | yes | 상관없음 | 상관없음 |
| write commit이 안전한가 | yes | no | 보통 yes 또는 unknown |
| 특정 기능이 부하를 키우는가 | 보통 no | 일부 yes | yes |
| 마지막 안전한 snapshot이 있는가 | yes | optional | optional |
| 사용자 약속을 어기지 않는가 | yes | read는 지킴 | 핵심 기능만 지킴 |

따라서 운영 룰은 보통 이렇게 된다.

- freshness 예산 안 + snapshot 존재 + writes healthy -> stale read
- writes unsafe + reads reproducible -> read-only
- optional feature가 dependency fan-out를 키움 -> partial disablement
- correctness unknown -> fail-closed

### 6. 구현은 per-endpoint policy와 kill switch가 핵심이다

이 패턴은 보통 runtime config 또는 feature flag로 제어한다.

필요한 손잡이 예시:

- endpoint별 freshness class: `strict`, `bounded-stale`, `snapshot-ok`
- global write fence: `READ_ONLY=true`
- feature brownout flags: `disable_recommendations`, `disable_export`, `disable_live_counts`
- dependency-aware routing: `primary_only`, `replica_ok`, `cache_stale_ok`
- 사용자 메시지 분리: "일시적으로 수정 기능이 제한됩니다" vs "일부 보조 기능이 지연됩니다"

간단히 쓰면 아래 흐름이다.

## 깊이 들어가기 (계속 4)

```pseudo
function chooseMode(route, signal):
  if route.correctnessCritical and signal.correctnessUnknown:
    return FAIL_CLOSED
  if signal.writeSafetyBroken:
    return READ_ONLY
  if route.optional and signal.featureAmplifiesLoad:
    return DISABLE_FEATURE
  if route.maxStaleness >= signal.estimatedStaleness and signal.lastKnownGoodExists:
    return STALE_READ
  return FAIL_FAST
```

```java
public Response handle(Request request, IncidentSignal signal) {
    RoutePolicy policy = routePolicyRegistry.lookup(request.route());
    DegradationMode mode = degradationPlanner.choose(policy, signal);
    return mode.execute(request);
}
```

### 7. exit도 단계적으로 해야 한다

degraded mode를 켜는 것만큼 끄는 것도 중요하다.
특히 read-only를 너무 빨리 풀면 복구 직후 write storm가 다시 primary를 누른다.

보통은 아래 순서가 안전하다.

1. primary/failover 안정화 확인
2. replica lag, queue backlog, cache warm-up 상태 확인
3. read-only 해제 전에 brownout 기능은 일부 유지
4. stale read를 점진적으로 줄이고 fresh path 복원
5. disabled feature를 순차적으로 재개

즉, **복구 순서는 장애 중 내린 순서를 거꾸로 따라간다**고 생각하면 된다.

---

## 실전 시나리오

### 시나리오 1: cache cluster outage + DB read headroom 부족

문제:

- cache hit ratio가 92%에서 15%로 급락
- DB read CPU가 80%를 넘기기 시작
- 상품 상세, 홈 추천, facet count가 모두 DB fan-out를 일으킨다

해결:

- 상품 상세는 `stale-if-error`로 last-known-good를 허용
- 홈 추천, facet count, 실시간 배지는 brownout으로 비활성화
- write path는 아직 건강하므로 read-only는 켜지 않는다

핵심:

- stale read는 핵심 browse path를 살리고
- partial disablement는 DB 증폭 경로를 잘라 낸다

### 시나리오 2: primary failover 중 주문/결제 시스템 보호

문제:

- primary 승격이 진행 중이라 write fencing이 불안정
- replica는 주문 이력 조회 정도는 가능
- checkout write를 계속 받으면 중복 결제/유실 위험이 있다

해결:

- 주문 생성, 결제 확정, 취소 요청은 read-only 모드에서 차단
- 주문 이력, 영수증 조회는 replica read로 유지
- 추천/프로모션 banner는 함께 꺼서 DB 여유를 확보

핵심:

- DB incident의 1차 목표는 UX 최대화보다 **잘못된 write 방지**다

### 시나리오 3: replica lag가 길어 권한/잔액 판단이 흔들림

문제:

- failover 직후 replica lag가 8초 이상
- 계정 잔액, quota, 권한 revoke는 1초 stale도 위험

해결:

- 권한 판단과 잔액 조회는 stale read를 쓰지 않고 fail-closed
- 비핵심 analytics 위젯은 snapshot으로 유지
- lag가 budget 아래로 내려올 때까지 selective brownout 유지

핵심:

- "조금 오래된 값"이 아니라 "잘못된 권한/잔액"이 될 수 있는 경로는 가용성보다 correctness를 우선한다

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| stale read | 사용자 조회 흐름을 많이 살린다 | 오래된 값이 보인다 | bounded stale가 명시된 read path |
| partial feature disablement | 핵심 기능을 지키면서 부하를 빠르게 줄인다 | 제품 면적이 줄어 UX가 어색해질 수 있다 | 부가 기능이 dependency fan-out를 키울 때 |
| read-only mode | write corruption과 중복 처리를 막는다 | 사용자가 수정/생성을 못 한다 | primary/fencing/commit safety가 불안할 때 |
| full maintenance | 가장 단순하고 보수적이다 | 가용성 손실이 크다 | correctness가 불명확하고 안전한 read도 남기기 어려울 때 |

핵심은 "무조건 더 많이 살린다"가 아니라 **무엇을 희생해서 무엇을 보호할지 미리 합의하는 것**이다.

## 꼬리질문

> Q: cache incident면 항상 stale read를 켜야 하나요?
> 핵심: 아니다. DB headroom이 충분하면 quick miss나 bypass로 끝낼 수 있고, invalidation이 꼬였으면 stale 자체가 위험할 수 있다.

> Q: read-only mode와 partial disablement는 어떻게 다르나요?
> 핵심: read-only는 write safety를 지키는 모드이고, partial disablement는 부가 기능을 줄여 capacity를 지키는 모드다. 둘은 자주 함께 켠다.

> Q: 어떤 경로는 왜 stale read보다 fail-closed가 더 낫나요?
> 핵심: 권한, 재고, 잔액처럼 오래된 값이 사고로 이어지는 경로는 availability보다 correctness가 우선이기 때문이다.

> Q: degraded mode는 누가 결정해야 하나요?
> 핵심: runtime automation이 1차 신호를 감지하더라도, endpoint별 freshness class와 kill switch는 평소 설계 단계에서 정의돼 있어야 한다.

## 한 줄 정리

Read-only와 graceful degradation 패턴의 핵심은 cache/DB incident 때 stale read, feature brownout, write freeze를 섞어 쓰되, 데이터 freshness와 write safety를 같은 축으로 보지 않는 것이다.
