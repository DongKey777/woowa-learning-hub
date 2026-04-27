# Authorization Graph Cache / Relationship Cache Primer

> 한 줄 요약: `authorization graph cache`와 `relationship cache`는 "권한 결정 계산을 빨리하려는 캐시"라는 한 묶음이며, 먼저 "어느 계층이 stale인지"를 나눠야 deep dive를 덜 헤맨다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Authorization Graph Caching](./authorization-graph-caching.md)
> - [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)
> - [Security README: 기본 primer](./README.md#기본-primer)

retrieval-anchor-keywords: authorization graph cache primer, relationship cache primer, graph cache primer, authz graph cache primer, relationship edge cache primer, path cache primer, graph snapshot primer, graph cache beginner route, relationship cache beginner route, graph cache first step, relationship cache first step, graph cache next step, relationship cache next step, graph cache return path, authz tenant catalog return, stale deny graph cache primer, tenant-specific 403 graph cache primer, 권한 바꾼 후에도 403

---

## 먼저 잡는 mental model

권한 판단을 3칸으로 나누면 헷갈림이 줄어든다.

1. source of truth 변경: role/relationship/policy가 실제로 바뀌었는가
2. propagation: claim/session/cache가 새 버전으로 갱신됐는가
3. request decision: 지금 요청이 새 기준으로 평가됐는가

`graph cache`와 `relationship cache`는 2-3번 칸에 걸쳐 있다.
그래서 "grant를 했는데 403"이면 cache 자체보다 먼저 "어느 칸이 stale인지"부터 본다.

## 용어를 짧게 정리

| 용어 | 초보자용 한 줄 뜻 | 먼저 확인할 포인트 |
|---|---|---|
| `relationship cache` | user-group, group-role 같은 edge 조회를 저장 | edge 변경 이벤트가 cache key/version에 반영됐는가 |
| `graph cache` | 관계 그래프 계산 결과(path/decision)를 저장 | tenant + snapshot version이 key에 들어가는가 |
| `path cache` | "이 사용자 -> 이 리소스 허용" 계산 결과 캐시 | stale allow/deny가 남는 TTL/무효화 경로가 있는가 |
| `graph snapshot version` | 어떤 그래프 버전 기준으로 판정했는지 식별자 | decision log에 version이 남는가 |

## 60초 분기: deep dive 전에 어디로 갈지

| 지금 증상 | 먼저 갈 문서 | 그다음 |
|---|---|---|
| `grant했는데 still 403`, `stale deny` | [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) | [Authorization Caching / Staleness](./authorization-caching-staleness.md) |
| `authorization graph cache`, `relationship cache` 구조 자체를 이해하고 싶음 | 이 문서(현재 위치) | [Authorization Graph Caching](./authorization-graph-caching.md) |
| tenant마다 allow/deny가 갈림 (`tenant-specific 403`) | [Authorization Caching / Staleness](./authorization-caching-staleness.md) | [Authorization Graph Caching](./authorization-graph-caching.md) |

## 간단 예시

`user A`에게 `project.read`를 방금 부여했는데 `tenant T1`에서는 성공, `T2`에서는 계속 `403`이 난다.

- source of truth: grant row는 두 tenant 모두 반영됨
- propagation: `T2`의 relationship cache key에 old `graph_snapshot_version`이 남음
- request decision: `T2`의 path cache가 old deny를 재사용

이 상황은 "권한 모델이 틀림"이 아니라 "version/tenant key 포함이 누락된 cache 경로" 문제일 가능성이 높다.

## 자주 헷갈리는 지점

- `relationship cache`와 `graph cache`는 경쟁 개념이 아니다. 보통 함께 쓴다.
- `TTL 짧게`만으로 해결되지 않는다. revoke/ownership move는 event invalidation이 필요하다.
- `401/403/404`가 흔들리면 response concealment와 authz stale이 같이 있을 수 있다. 먼저 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)에서 응답 의미를 고정한다.

## 다음 단계와 복귀 경로

- graph cache 설계 deep dive로 바로 가기:
  - [Authorization Graph Caching](./authorization-graph-caching.md)
- stale cache 운영/디버깅으로 가기:
  - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
- 카테고리에서 다른 authz 증상 갈래 고르기:
  - [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)
  - [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)

## 한 줄 정리

`authorization graph cache`와 `relationship cache`는 "권한 계산 가속층"이라는 같은 문제군이며, deep dive 전에 stale 위치(변경/전파/판정)를 먼저 분리하면 원인 탐색이 빨라진다.
