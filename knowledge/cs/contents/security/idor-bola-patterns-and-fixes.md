---
schema_version: 3
title: IDOR / BOLA Patterns and Fixes
concept_id: security/idor-bola-patterns-and-fixes
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- idor basics
- bola basics
- broken object level authorization
- object ownership check
aliases:
- idor basics
- bola basics
- broken object level authorization
- object ownership check
- tenant isolation authz
- same user different tenant
- 같은 사용자 다른 tenant
- 왜 403 이 아니라 404
- 없는 줄 알았는데 남의 리소스
- scope is not ownership
- own resource wrong tenant
- concealment 404
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/authentication-vs-authorization.md
- contents/security/auth-failure-response-401-403-404.md
- contents/security/concealment-404-entry-cues.md
- contents/security/permission-model-bridge-authn-to-role-scope-ownership.md
- contents/security/role-vs-scope-vs-ownership-primer.md
- contents/security/tenant-membership-change-session-scope-basics.md
- contents/system-design/multi-tenant-saas-isolation-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- IDOR / BOLA Patterns and Fixes 핵심 개념을 설명해줘
- idor basics가 왜 필요한지 알려줘
- IDOR / BOLA Patterns and Fixes 실무 설계 포인트는 뭐야?
- idor basics에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 IDOR / BOLA Patterns and Fixes를 다루는 deep_dive 문서다. IDOR/BOLA는 "ID를 안다고 다른 사람 데이터까지 접근되는" broken access control이다. 인증이 아니라 객체 수준 인가와 소유권 검증이 핵심이다. 검색 질의가 idor basics, bola basics, broken object level authorization, object ownership check처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# IDOR / BOLA Patterns and Fixes

> 한 줄 요약: IDOR/BOLA는 "ID를 안다고 다른 사람 데이터까지 접근되는" broken access control이다. 인증이 아니라 객체 수준 인가와 소유권 검증이 핵심이다.

**난이도: 🔴 Advanced**

관련 문서:

- [인증과 인가의 차이](./authentication-vs-authorization.md)
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
- [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)
- [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)
- [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
- [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
- [Multi-tenant SaaS Isolation Design](../system-design/multi-tenant-saas-isolation-design.md)

retrieval-anchor-keywords: idor basics, bola basics, broken object level authorization, object ownership check, tenant isolation authz, same user different tenant, 같은 사용자 다른 tenant, 왜 403 이 아니라 404, 없는 줄 알았는데 남의 리소스, scope is not ownership, own resource wrong tenant, concealment 404

---

## 1분 브리지: Ownership 누락이 왜 바로 취약점인가

먼저 이렇게 생각하면 쉽다.

- `role`은 "무슨 종류의 사용자냐"
- `scope`는 "토큰에 어떤 API 작업 권한이 있냐"
- `ownership`은 "지금 이 객체가 정말 네 것이냐"

IDOR/BOLA는 보통 앞의 두 칸은 통과했는데, 마지막 ownership 확인이 빠져서 터진다.

| 체크 항목 | 통과해도 남는 빈칸 |
|--------|----------------|
| role 확인 (`USER`, `ADMIN`) | `USER`끼리 서로 남의 주문을 볼 수 있는지 못 막음 |
| scope 확인 (`orders.read`) | "주문 읽기 가능"일 뿐 "아무 주문이나 가능"은 아님 |
| ownership 확인 (`order.owner_id == me`) | 이 검사가 있어야 객체 단위 접근이 닫힘 |

짧은 예시:

- `/orders/1001`은 내 주문, `/orders/1002`는 남의 주문
- 내 토큰에 `orders.read`가 있어도 `1002.owner_id != myUserId`면 거부해야 한다
- 이 한 줄 검증이 빠지면 "ID만 바꿔 남의 데이터 조회"가 바로 IDOR다

같은 사용자라도 tenant가 다르면 같은 실수가 난다. 예를 들어 사용자 A가 tenant A와 tenant B 둘 다 속해 있을 때, tenant A 화면에서 tenant B의 자기 주문 ID를 넣으면 `owner_id == me`만으로는 통과시키면 안 된다. beginner 관점에서 이 감각이 아직 약하면 먼저 [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)의 `같은 사용자, 다른 tenant` 미니 케이스로 ownership과 tenant를 같이 묶어 보고, 다시 이 문서의 `30초 분기표`로 돌아와 `403`과 concealment `404`를 고정하면 된다.

헷갈리기 쉬운 포인트:

- "로그인됨"은 신원 확인이지 객체 소유 증명이 아니다
- "scope 있음"은 기능 권한이지 리소스 소유권 증명이 아니다
- 따라서 ownership 누락은 부가 위험이 아니라 직접 취약점이다

## 초보자 출발 문장: `없는 줄 알았는데 남의 리소스였다`

이 문서로 들어오는 초보자 표현은 보통 전문 용어보다 먼저 이렇게 나온다.

- `404라서 없는 줄 알았는데 다른 사람 계정으로는 열려요`
- `내 계정에서는 없는데 owner는 보인대요`
- `없는 줄 알았는데 사실 남의 주문이었어요`

이 문장을 IDOR/BOLA 관점으로 바꾸면 뜻은 단순하다.

| 초보자 표현 | 실제로 의심해야 하는 것 |
|---|---|
| `없는 줄 알았는데 owner는 연다` | 객체는 존재하고, 내 요청만 ownership/tenant 정책에서 막혔을 수 있다 |
| `없다고 나오는데 관리자/운영 문맥에서는 보인다` | 외부에는 concealment `404`, 내부 판단은 ownership mismatch일 수 있다 |
| `scope도 있고 로그인도 됐다` | authn/scope를 통과해도 ownership 누락 또는 ownership deny는 별개다 |

즉 `없는 줄 알았는데 남의 리소스였다`는 보통 "정말 없는 객체"가 아니라 "객체는 있는데 내 문맥에서는 숨겨졌거나 거부됐다"는 쪽 단서다.

- 아직 `진짜 없음 / 숨김 404 / stale deny` 세 갈래를 못 가르겠다면 이 문서로 바로 깊게 내려가기 전에 `[primer bridge]` [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)에서 먼저 beginner용 분기를 고정하는 편이 안전하다.

---

## 30초 분기표: IDOR에서 `403` vs 의도적 `404`

먼저 mental model을 아주 짧게 고정한다.

- `검사는 항상 ownership/tenant 정책으로 한다`
- `응답코드 선택은 정보 노출 정책으로 한다`

즉 `404`를 고른다고 ownership 검사가 사라지는 것이 아니다. 내부적으로는 "남의 리소스라 deny"를 이미 알아낸 뒤, 바깥에 그 존재를 숨길지 결정하는 것이다.

| 질문 | `예`면 더 가까운 기본값 | 이유 |
|---|---|---|
| 사용자가 그 리소스의 존재를 알아도 되는가 | `403` | 이미 존재를 아는 협업/관리 화면이면 "권한은 없지만 대상은 존재"를 알려도 정책상 문제가 적다 |
| 리소스 존재 자체가 민감한가 | 의도적 `404` | `내 주문`, `내 메시지`, `내 파일`처럼 user-owned/private 리소스는 존재 노출이 곧 정보 누출이 될 수 있다 |
| 클라이언트가 "존재함 vs 권한없음"을 구분해야 다음 행동이 가능한가 | `403` | 권한 요청, 관리자 문의, 승인 흐름으로 이어져야 하면 `403`이 더 실용적이다 |
| 외부에는 숨기되 내부 운영자는 정확한 deny 이유를 알아야 하는가 | 의도적 `404` + 내부 로그는 실제 deny reason 기록 | 외부 응답과 내부 감사/디버깅 정보는 분리할 수 있다 |

초보자용 한 줄 결정:

- `협업/관리/공유 자원`이면 기본 `403`
- `내 것만 보여야 하는 private 자원`이면 기본 `404`

짧은 예시:

| 요청 상황 | 내부 판단 | 외부 응답 권장 |
|---|---|---|
| 내가 속한 팀 문서인데 `edit` 권한만 없음 | 대상 존재를 이미 알아도 됨 | `403` |
| `/orders/1002`가 남의 개인 주문 | 존재 자체를 숨기는 편이 안전 | 의도적 `404` |
| tenant A 사용자가 tenant B invoice를 조회 | cross-tenant 존재 노출을 막고 싶음 | 의도적 `404` |

헷갈리기 쉬운 포인트:

- `404`는 "정말 없음"과 "있지만 숨김"이 외부에서 같게 보이도록 만드는 선택일 수 있다.
- `403`을 쓴다고 IDOR가 해결되는 것은 아니다. 핵심은 먼저 ownership/tenant 검사를 실제로 하는 것이다.
- `404` concealment를 쓰더라도 내부 로그에는 `ownership_mismatch`, `tenant_mismatch` 같은 실제 deny reason을 남겨야 운영이 가능하다.

---

## 핵심 개념

IDOR(Insecure Direct Object Reference)와 BOLA(Broken Object Level Authorization)는 거의 같은 문제를 다른 관점에서 부른다.

- 사용자가 객체 ID를 조작한다
- 서버가 그 객체에 대한 권한을 충분히 확인하지 않는다
- 다른 사람의 데이터가 노출되거나 변경된다

이 취약점은 인증이 성공했다고 해서 안전하지 않다는 사실을 보여준다.

- 로그인 여부는 확인했다
- 그러나 그 객체에 접근할 권한은 확인하지 않았다

즉 IDOR/BOLA의 해결책은 더 강한 인증이 아니라, 더 정확한 객체 수준 인가다.

---

## 깊이 들어가기

### 1. 흔한 패턴

대표적인 취약한 형태:

- `/users/1234`
- `/orders/9999`
- `/files/abc`
- `/tenants/42/invoices/7`

문제는 ID가 추측 가능하거나 순차적일 때 더 쉽게 드러난다.

### 2. 인증과 객체 권한은 다르다

좋지 않은 생각:

- 로그인했으니 내 데이터라고 가정
- role만 확인하고 소유권은 안 봄
- "관리자 화면이 아니니 괜찮겠지"라고 넘김

좋은 생각:

- user id와 resource owner를 비교한다
- tenant id를 함께 검증한다
- 객체별 policy를 적용한다

### 3. BOLA는 API 설계와 직결된다

모바일이나 SPA에서는 resource id가 요청에 직접 드러난다.

- client가 id를 바꿀 수 있다
- BFF가 있어도 내부 API가 취약하면 끝이다
- list API와 detail API의 권한 기준이 다를 수 있다

### 4. multi-tenant에서는 더 위험하다

tenant 경계를 잘못 잡으면 horizontal privilege escalation이 된다.

- 같은 user라도 tenant가 다르면 권한이 달라진다
- cache key에 tenant가 빠지면 권한이 섞인다
- soft-delete된 tenant나 이전 멤버십도 고려해야 한다

### 5. indirect reference가 안전하다는 오해

난수 같은 opaque ID를 쓰면 안전해 보이지만, 완전한 방어는 아니다.

- 추측은 어려워지지만 권한 확인이 사라지면 여전히 취약하다
- 결국 서버에서 "이 사용자가 이 객체를 볼 수 있는가"를 확인해야 한다

---

## 실전 시나리오

### 시나리오 1: 남의 주문 상세를 조회함

문제:

- `/orders/{orderId}`만 보고 조회한다
- 주문 소유자 검증이 없다

대응:

- order owner와 principal을 비교한다
- tenant 경계까지 확인한다
- 관리자와 owner의 정책을 분리한다

### 시나리오 2: 파일 다운로드 URL을 바꿔서 남의 파일을 봄

문제:

- storage key만 알면 다운로드 가능하다

대응:

- signed URL 또는 authorization check를 추가한다
- public/private object를 분리한다
- object metadata에 owner를 둔다

### 시나리오 3: 관리자 기능이 아니라고 방심함

문제:

- 일반 사용자용 API에도 소유권 검사가 빠졌다

대응:

- 모든 object endpoint에 ownership policy를 둔다
- list와 detail, update, delete의 기준을 분리한다
- 단위 테스트와 security test를 같이 둔다

---

## 코드로 보기

### 1. 객체 수준 인가

```java
public Order getOrder(UserPrincipal user, Long orderId) {
    Order order = orderRepository.findById(orderId)
        .orElseThrow(() -> new NotFoundException("order not found"));

    if (!order.ownerId().equals(user.id()) && !user.roles().contains("ADMIN")) {
        throw new AccessDeniedException("forbidden");
    }

    return order;
}
```

### 2. tenant 검증

```java
public Invoice getInvoice(UserPrincipal user, Long tenantId, Long invoiceId) {
    if (!user.tenantIds().contains(tenantId)) {
        throw new AccessDeniedException("tenant mismatch");
    }
    return invoiceRepository.findByTenantIdAndId(tenantId, invoiceId)
        .orElseThrow(() -> new NotFoundException("invoice not found"));
}
```

### 3. path parameter만 믿지 않는 규칙

```text
1. path id는 입력값일 뿐 신원 증명이 아니다
2. 객체 조회 후 owner/tenant/policy를 검증한다
3. 권한 없으면 403 또는 의도적 404를 선택한다
4. 모든 변경 요청에 동일한 객체 수준 규칙을 적용한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| role-only check | 쉽다 | IDOR를 막지 못할 수 있다 | 단순 admin 화면 |
| ownership check | 정확하다 | 코드가 더 필요하다 | 대부분의 객체 API |
| tenant-aware policy | multi-tenant에 맞다 | 경계 정의가 복잡하다 | SaaS |
| opaque ID | 추측을 어렵게 한다 | 권한 검증 대체가 아니다 | 보조 수단 |

판단 기준은 이렇다.

- 객체 ID를 사용자가 바꿀 수 있는가
- owner와 requester가 항상 같은가
- tenant가 여러 개인가
- 404로 숨겨야 할지 403으로 드러내야 할지 정책이 있는가

---

## 꼬리질문

> Q: IDOR과 BOLA의 차이는 무엇인가요?
> 의도: 같은 문제를 다른 관점으로 설명할 수 있는지 확인
> 핵심: 둘 다 객체 수준 인가 실패를 뜻한다.

> Q: 로그인했는데도 왜 취약할 수 있나요?
> 의도: 인증과 객체 인가를 구분하는지 확인
> 핵심: 로그인은 신원을 확인할 뿐 객체 권한은 별도다.

> Q: opaque ID만 쓰면 안전한가요?
> 의도: 추측 불가능성과 인가 검증의 차이를 아는지 확인
> 핵심: 아니다. 서버 검증이 여전히 필요하다.

> Q: multi-tenant에서 더 위험한 이유는 무엇인가요?
> 의도: tenant 경계 이해를 확인
> 핵심: 같은 사용자라도 tenant별 권한이 달라지기 때문이다.

## 한 줄 정리

IDOR/BOLA는 path ID를 신분증처럼 취급한 순간 생기는 객체 수준 인가 실패다.
