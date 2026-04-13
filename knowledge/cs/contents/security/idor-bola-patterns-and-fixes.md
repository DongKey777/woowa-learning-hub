# IDOR / BOLA Patterns and Fixes

> 한 줄 요약: IDOR/BOLA는 "ID를 안다고 다른 사람 데이터까지 접근되는" broken access control이다. 인증이 아니라 객체 수준 인가와 소유권 검증이 핵심이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [BFF Boundaries and Client-Specific Aggregation](../software-engineering/bff-boundaries-client-specific-aggregation.md)
> - [Multi-tenant SaaS Isolation Design](../system-design/multi-tenant-saas-isolation-design.md)

retrieval-anchor-keywords: IDOR, BOLA, broken object level authorization, broken access control, object ownership, resource id, path parameter, tenant isolation, horizontal privilege escalation

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
