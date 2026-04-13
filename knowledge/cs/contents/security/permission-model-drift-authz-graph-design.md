# Permission Model Drift / AuthZ Graph Design

> 한 줄 요약: permission model drift는 코드, DB, 캐시, 정책 엔진, UI가 서로 다른 권한 진실을 갖게 될 때 생긴다. 이를 막으려면 권한 그래프와 정책 버전을 명시적으로 관리해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
> - [Multi-tenant SaaS Isolation Design](../system-design/multi-tenant-saas-isolation-design.md)

retrieval-anchor-keywords: permission drift, authz graph, policy version, entitlement, role explosion, relationship-based access control, RBAC, ABAC, decision graph, policy engine, source of truth

---

## 핵심 개념

permission model drift는 권한 모델이 시간이 지나며 서로 다른 시스템에서 조금씩 달라지는 현상이다.

- DB에는 role A가 있다
- 코드에는 role B가 하드코딩돼 있다
- 캐시에는 예전 권한이 남아 있다
- UI는 권한을 숨기지만 API는 열려 있다

이런 상태가 되면 누구도 "정답 권한"을 말할 수 없다.  
그래서 권한은 단일 source of truth와 명시적인 graph로 다뤄야 한다.

---

## 깊이 들어가기

### 1. drift가 생기는 전형적인 이유

- 기능 추가 때 role을 임시로 늘린다
- UI 조건문과 API 조건문이 분리된다
- tenant나 조직 구조가 바뀐다
- 캐시 무효화가 느리다
- 마이그레이션 후 옛 권한 코드가 남는다

### 2. RBAC만으로는 점점 부족해진다

단순 role 기반 모델은 이해하기 쉽지만, 커질수록 role explosion이 생긴다.

- `ADMIN`, `MANAGER`, `SUPPORT`, `SUPPORT_READONLY`, ...
- 예외 역할이 계속 추가된다

그래서 자주 다음으로 이동한다.

- RBAC + ownership
- ABAC
- relationship-based access control
- policy graph / decision graph

### 3. authz graph는 권한을 관계로 본다

graph 관점에서 보면:

- user는 team에 속한다
- team은 tenant에 속한다
- tenant는 resource를 소유한다
- role은 edge로 표현된다

장점:

- 권한의 출처를 추적하기 쉽다
- drift를 비교하기 쉽다
- 감사 로그와 설명 가능성이 좋아진다

### 4. policy version이 없으면 비교가 어렵다

정책이 바뀌면 이전 결정과 새 결정을 비교해야 한다.

- version이 없으면 언제부터 바뀌었는지 모른다
- 캐시가 언제 stale해졌는지 알기 어렵다
- incident 후 원인 분석이 느려진다

그래서 policy version 또는 entitlement snapshot이 필요하다.

### 5. UI hiding은 보안이 아니다

권한 없는 메뉴를 화면에서 숨기는 것은 좋지만, 그것만으로는 부족하다.

- API가 그대로 열려 있을 수 있다
- 모바일 앱이 예전 정책을 들고 있을 수 있다
- BFF가 다른 policy를 적용할 수 있다

즉 UI는 표현이고, 정책은 서버의 책임이다.

---

## 실전 시나리오

### 시나리오 1: 관리자 페이지는 숨겼는데 API는 열려 있음

대응:

- API와 UI가 같은 policy source를 읽게 만든다
- endpoint별 authorization test를 추가한다
- policy version을 배포 단위로 맞춘다

### 시나리오 2: role이 너무 많아져 관리가 안 됨

대응:

- 역할을 그룹과 관계로 재설계한다
- 중요한 권한은 graph-based policy로 옮긴다
- 예외 role을 남발하지 않는다

### 시나리오 3: 권한 회수 후에도 일부 캐시가 오래 살아 있음

대응:

- permission version을 올린다
- decision cache key에 version을 넣는다
- drift detector로 UI/API/DB 정책을 비교한다

---

## 코드로 보기

### 1. policy version 기반 결정

```java
public AuthorizationDecision decide(UserPrincipal user, String resourceId, String action) {
    String cacheKey = user.id() + ":" + user.policyVersion() + ":" + resourceId + ":" + action;
    return decisionCache.computeIfAbsent(cacheKey, ignored -> policyEngine.evaluate(user, resourceId, action));
}
```

### 2. authz graph 개념

```java
public boolean canAccess(User user, Resource resource) {
    return authzGraph.hasPath(user.id(), resource.ownerTenantId(), "CAN_READ");
}
```

### 3. drift detector 아이디어

```text
1. DB role 정의를 읽는다
2. policy engine 규칙을 읽는다
3. UI hidden state와 API permission을 비교한다
4. 차이가 나면 alert를 보낸다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| plain RBAC | 이해가 쉽다 | role explosion이 생긴다 | 단순 조직 |
| RBAC + ownership | 현실적이다 | 구현이 늘어난다 | 대부분의 서비스 |
| graph-based authz | 설명 가능성이 좋다 | 모델링이 복잡하다 | 복잡한 SaaS |
| policy engine | 중앙화할 수 있다 | 운영과 성능 고려가 필요하다 | 대규모 플랫폼 |

판단 기준은 이렇다.

- 권한이 role로 표현 가능한가
- 관계와 맥락이 더 중요한가
- 정책 변경이 자주 일어나는가
- drift를 자동으로 감지해야 하는가

---

## 꼬리질문

> Q: permission model drift는 왜 위험한가요?
> 의도: 여러 진실이 생기는 문제를 아는지 확인
> 핵심: 코드, DB, 캐시, UI가 서로 다른 권한을 믿게 되기 때문이다.

> Q: role explosion은 왜 생기나요?
> 의도: 단순 역할 모델의 한계를 아는지 확인
> 핵심: 예외와 조합이 계속 늘어나기 때문이다.

> Q: authz graph의 장점은 무엇인가요?
> 의도: 관계 기반 권한의 설명 가능성을 이해하는지 확인
> 핵심: 권한의 출처와 경로를 추적하기 쉽다.

> Q: UI에서 숨겼으면 안전한가요?
> 의도: 표현과 정책을 구분하는지 확인
> 핵심: 아니다. 서버 policy가 최종 기준이다.

## 한 줄 정리

permission model drift는 권한 진실이 여러 개로 갈라지는 문제이고, authz graph와 policy version은 그 분열을 줄이는 도구다.
