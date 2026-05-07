---
schema_version: 3
title: '리소스 단위 인가 판단 연습: Role / Scope / Ownership / Tenant'
concept_id: security/resource-level-authz-decision-practice
canonical: false
category: security
difficulty: intermediate
doc_role: deep_dive
level: intermediate
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- resource-level authz practice
- role scope ownership tenant decision
- object-level authorization exercise
- ownership tenant check order
aliases:
- resource-level authz practice
- role scope ownership tenant decision
- object-level authorization exercise
- ownership tenant check order
- same user different tenant
- scope 있는데 왜 403
- role 있는데 왜 거부
- why 403 after login
- 처음 resource authz decision
- authz decision table
- what is resource-level authorization
- resource authorization practice
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/role-vs-scope-vs-ownership-primer.md
- contents/security/permission-checks-rest-flows-primer.md
- contents/security/tenant-membership-change-session-scope-basics.md
- contents/security/idor-bola-patterns-and-fixes.md
- contents/security/tenant-isolation-authz-testing.md
- contents/spring/spring-security-architecture.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- '리소스 단위 인가 판단 연습: Role / Scope / Ownership / Tenant 핵심 개념을 설명해줘'
- resource-level authz practice가 왜 필요한지 알려줘
- '리소스 단위 인가 판단 연습: Role / Scope / Ownership / Tenant 실무 설계 포인트는 뭐야?'
- resource-level authz practice에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: '이 문서는 security 카테고리에서 리소스 단위 인가 판단 연습: Role / Scope / Ownership / Tenant를 다루는 deep_dive 문서다. `role`, `scope`, `ownership`, `tenant`를 용어로만 외우지 않고, 실제 요청 하나를 `어느 체크가 action gate이고 어느 체크가 resource gate인지`로 잘라 보는 intermediate bridge다. 검색 질의가 resource-level authz practice, role scope ownership tenant decision, object-level authorization exercise, ownership tenant check order처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.'
---
# 리소스 단위 인가 판단 연습: Role / Scope / Ownership / Tenant

> 한 줄 요약: `role`, `scope`, `ownership`, `tenant`를 용어로만 외우지 않고, 실제 요청 하나를 `어느 체크가 action gate이고 어느 체크가 resource gate인지`로 잘라 보는 intermediate bridge다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
- [Permission Checks In REST Flows](./permission-checks-rest-flows-primer.md)
- [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
- [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
- [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
- [Spring Security 아키텍처](../spring/spring-security-architecture.md)

retrieval-anchor-keywords: resource-level authz practice, role scope ownership tenant decision, object-level authorization exercise, ownership tenant check order, same user different tenant, scope 있는데 왜 403, role 있는데 왜 거부, why 403 after login, 처음 resource authz decision, authz decision table, what is resource-level authorization, resource authorization practice

## 핵심 개념

beginner primer가 `role`, `scope`, `ownership`의 뜻을 갈라 줬다면, 그다음에는 `어느 요청에서 무엇을 먼저 묻는가`를 연습해야 한다.

이 문서의 핵심 질문은 하나다.

`이 요청은 action이 막힌 건가, resource가 막힌 건가?`

짧게 고정하면 아래처럼 읽으면 된다.

- role: `이 종류의 기능을 시도할 자격이 있나`
- scope: `이 토큰이 이 API action을 위임받았나`
- ownership: `이 특정 객체가 내 범위 안인가`
- tenant: `그 객체가 지금 선택한 tenant/workspace 문맥 안인가`

여기서 중요한 점은 `ownership`과 `tenant`가 보통 resource-level decision의 한 묶음으로 움직인다는 것이다. owner여도 tenant가 다르면 막힐 수 있고, tenant가 같아도 owner가 아니면 막힐 수 있다.

## 한눈에 보기

| 먼저 보이는 증상 | 실제로 먼저 의심할 축 | action gate인가 | resource gate인가 |
|---|---|---|---|
| `admin 메뉴가 403` | role / permission | 예 | 아니오 |
| `token은 valid한데 API가 403` | scope 또는 role | 예 | 아직 모름 |
| `같은 token인데 어떤 id만 안 됨` | ownership | 아니오 | 예 |
| `같은 사용자인데 workspace A는 되고 B는 안 됨` | tenant / context | 아니오 | 예 |
| `내 주문인데 지금 tenant 화면에서는 안 열림` | ownership + tenant 함께 확인 | 아니오 | 예 |

한 줄로 줄이면 이렇다.

- action gate는 `이 종류의 요청을 해도 되나`
- resource gate는 `이 id를 지금 이 문맥에서 다뤄도 되나`

비유로는 `건물 출입증`과 `서랍 열쇠`가 가깝다. 다만 실제 시스템에서는 한 요청 안에서 두 체크가 함께 일어나므로, 출입증 하나로 모든 서랍이 열리는 모델은 아니라는 점에서 비유가 멈춘다.

## 리소스 판단 순서

초보자가 실전에서 가장 덜 헷갈리는 순서는 아래다.

1. `이 action 자체를 시도할 자격이 있나`
2. `delegated token이라면 이 action scope가 맞나`
3. `이 resource id가 내 관계 범위 안인가`
4. `그 resource가 지금 active tenant와도 맞나`

이를 표로 다시 쓰면 이렇다.

| 질문 | 대표 체크 | 빠지면 생기는 실수 |
|---|---|---|
| `이 기능 종류를 해도 되나?` | role / permission | 일반 사용자가 관리자 action 호출 |
| `이 토큰이 그 action을 위임받았나?` | scope | read token으로 write 시도 |
| `이 객체가 내 범위 안인가?` | ownership / relationship | 남의 주문 상세 조회 |
| `지금 tenant 문맥과도 맞나?` | tenant / workspace context | same-user cross-tenant 조회 |

특히 `ownership`과 `tenant`를 분리해서 보는 이유는, single-tenant 감각으로 작성한 코드는 `owner 맞음`만 보고 통과시키기 쉽기 때문이다. multi-tenant에서는 `owner 맞음 AND activeTenant 일치`가 더 안전한 기본값이다.

## 연습 카드 4개

### 1. `GET /orders/123`에서 `scope=orders.read`인데 403

먼저 결론부터 말하면, 이 증상만으로 scope 부족이라고 단정하면 이르다.

가능한 해석:

- role/permission은 통과했고 ownership에서 막혔다
- scope는 맞지만 tenant 문맥이 달랐다
- support token이라 delegated 범위 밖 order였다

가장 먼저 던질 질문:

- `다른 order id는 되는가`
- `같은 사용자라도 다른 tenant 화면인가`
- `이 token이 read는 가능하지만 support case 범위를 넘었는가`

즉 `같은 token인데 어떤 id만 안 된다`면 resource gate 쪽 신호가 더 강하다.

### 2. `GET /orders`는 되는데 `GET /orders/123`만 안 됨

이 경우 beginner가 자주 놓치는 것은 list와 detail의 판단 단위가 다르다는 점이다.

| endpoint | 주된 판단 단위 |
|---|---|
| `GET /orders` | 어떤 row들을 필터링해서 보여 줄까 |
| `GET /orders/123` | 이 특정 id 하나를 열어도 되나 |

list는 필터 누락이 핵심이고, detail은 object rule 누락이 핵심이다. 둘 다 `조회`지만 같은 체크가 아니다.

### 3. 같은 사용자 A가 tenant A와 B에 모두 속해 있고, tenant A 화면에서 tenant B 주문을 조회

이 케이스는 `owner가 나인데 왜 안 되지` 질문을 가장 잘 고쳐 준다.

- ownership만 보면 허용될 수 있다
- tenant까지 같이 보면 거부돼야 한다

즉 `내 주문`이라는 말은 multi-tenant에서는 보통 `내 주문 AND 현재 tenant 주문`까지 포함해야 안전하다.

### 4. support operator가 `tickets.read`는 있는데 `refund.approve`는 안 됨

여기서는 ownership보다 action gate가 먼저다.

- ticket 조회는 `read action + delegated scope` 문제
- refund 승인는 `민감 action permission` 문제

owner나 같은 tenant라는 이유만으로 `approve` 같은 더 강한 action까지 열리면 안 된다. ownership은 자주 마지막 gate지만 만능 gate는 아니다.

## 흔한 오해와 함정

### 1. `scope가 있으면 resource 허용도 끝난다`

아니다. scope는 보통 API 범위다. 객체별 허용은 ownership, relationship, tenant rule이 이어서 본다.

### 2. `owner면 tenant는 안 봐도 된다`

아니다. multi-tenant에서는 owner와 tenant가 같은 질문이 아니다.

### 3. `read가 되면 update도 비슷하다`

아니다. `read action 허용`과 `state를 바꾸는 action 허용`은 보통 분리한다. 특히 approve, refund, invite 같은 action은 더 강한 조건이 붙는다.

### 4. `403이면 항상 role 문제다`

아니다. `403`은 role, scope, ownership, tenant 어느 축에서도 나올 수 있다. 그래서 `어떤 id에서만 막히는가`와 `tenant를 바꾸면 달라지는가`를 같이 봐야 한다.

## 실무에서 쓰는 모습

리뷰나 테스트에서는 아래 결정표 하나만 있어도 품질이 많이 올라간다.

| 요청 | 최소 허용 조건 |
|---|---|
| `GET /orders/{id}` | `order.read` action 허용 + same tenant + owner 또는 허용된 support 관계 |
| `PATCH /orders/{id}` | `order.update` action 허용 + same tenant + 수정 가능한 관계 |
| `POST /tenant-users/invite` | `tenant.user.invite` action 허용 + active tenant admin 문맥 |
| `POST /refunds/{id}/approve` | `refund.approve` action 허용 + same tenant + step-up이나 별도 승인 규칙 |

이 표의 목적은 정책을 모두 외우는 것이 아니라, `action gate`와 `resource gate`를 한 줄에 같이 적는 습관을 만드는 데 있다.

가장 작은 연습은 테스트 이름도 둘로 나누는 것이다.

- `rejectsMissingActionPermission`
- `rejectsTenantMismatch`
- `rejectsOwnerMismatch`

이렇게 이름을 나누면 `왜 거부돼야 하는지`가 테스트에서 바로 보인다.

## 더 깊이 가려면

- same-user cross-tenant가 왜 바로 취약점 감각으로 이어지는지 보려면 [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)를 보면 된다.
- session이나 membership 변경 뒤 `원래 되던 게 갑자기 403`이라면 resource rule보다 freshness 문제일 수 있으니 [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)로 먼저 간다.
- negative test를 더 체계화하려면 [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)으로 이어 가면 된다.
- Spring에서 filter, method security, service 계층이 어디서 이 판단을 나눠 갖는지 보려면 [Spring Security 아키텍처](../spring/spring-security-architecture.md)가 좋은 bridge다.

## 한 줄 정리

resource-level authz에서는 `role/scope`가 action gate를, `ownership/tenant`가 resource gate를 맡는다고 나눠 읽어야 `왜 403인지`를 실제 요청 단위로 안전하게 설명할 수 있다.
