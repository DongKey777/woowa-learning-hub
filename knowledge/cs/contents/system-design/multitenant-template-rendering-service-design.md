# Multi-tenant Template Rendering Service 설계

> 한 줄 요약: multi-tenant template rendering service는 여러 고객의 브랜드, 언어, 정책을 분리하면서 같은 렌더링 엔진으로 콘텐츠를 생성하는 서비스다.

retrieval-anchor-keywords: multitenant template rendering, brand theme, locale rendering, template version, sandboxed renderer, personalization, preview, partials, cache, tenant isolation

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Document Generation / Rendering Service 설계](./document-generation-rendering-service-design.md)
> - [File Storage Presigned URL + CDN 설계](./file-storage-presigned-url-cdn-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)
> - [Email Delivery Platform 설계](./email-delivery-platform-design.md)
> - [Object Metadata Service 설계](./object-metadata-service-design.md)

## 핵심 개념

템플릿 렌더링은 문자열 치환이 아니다.  
멀티 테넌트 환경에서는 다음을 함께 다뤄야 한다.

- tenant별 theme
- locale / timezone
- template version
- partial reuse
- preview and approval
- sandbox and escaping

즉, 렌더링 서비스는 브랜드별 표현을 안전하게 분리하는 텍스트/HTML 생성 인프라다.

## 깊이 들어가기

### 1. 왜 multi-tenant인가

하나의 렌더링 엔진으로 여러 고객을 서비스하면 효율이 좋다.  
하지만 경계가 없으면 브랜드가 섞인다.

- tenant A logo가 tenant B 이메일에 들어감
- locale fallback이 잘못됨
- private variable이 노출됨

### 2. Capacity Estimation

예:

- tenant 1,000개
- 하루 1,000만 render
- 재렌더/preview 포함

렌더링은 CPU와 템플릿 캐시가 핵심이다.  
특히 프리뷰와 대량 발송이 동시에 오면 backend가 흔들릴 수 있다.

봐야 할 숫자:

- render latency
- template cache hit ratio
- preview rate
- tenant isolation breach count
- queue depth

### 3. 렌더링 파이프라인

```text
Template Registry
  -> Tenant Theme
  -> Personalization Variables
  -> Escape / Sanitize
  -> Render
  -> Preview / Store / Deliver
```

### 4. isolation

멀티 테넌트 렌더링에서 중요한 것은 경계다.

- template namespace per tenant
- theme asset namespace
- cache key tenant prefix
- secrets and tokens tenant scoped

이 부분은 [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)와 연결된다.

### 5. sandbox and escaping

템플릿은 공격면이기도 하다.

- HTML escaping
- helper whitelist
- arbitrary code execution 금지
- preview mode permission

### 6. versioning and approvals

브랜드 문서는 한번에 바꾸면 안 된다.

- draft
- review
- approved
- published
- rollback

이 부분은 [Config Distribution System 설계](./config-distribution-system-design.md)와 닮아 있다.

### 7. delivery integration

렌더링 결과는 여러 곳으로 간다.

- email
- pdf export
- in-app preview
- CDN asset bundle

이 부분은 [Email Delivery Platform 설계](./email-delivery-platform-design.md)와 [Document Generation / Rendering Service 설계](./document-generation-rendering-service-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: 브랜드별 이메일

문제:

- 고객사마다 로고와 색상이 다르다

해결:

- tenant theme
- versioned template
- locale fallback

### 시나리오 2: 템플릿 미리보기

문제:

- 운영자가 발송 전에 확인해야 한다

해결:

- preview mode
- data fixture
- approval workflow

### 시나리오 3: 잘못된 템플릿 배포

문제:

- 발송된 메일의 링크가 깨졌다

해결:

- rollback
- version pin
- audit trace

## 코드로 보기

```pseudo
function render(tenantId, templateId, data):
  template = registry.load(tenantId, templateId)
  context = mergeThemeAndLocale(tenantId, data)
  return renderer.render(template, context)
```

```java
public String preview(TemplateRequest req) {
    return renderer.render(templateService.load(req), req.variables());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Single-tenant renderer | 단순하다 | 비용이 크다 | 고가치 고객 |
| Multi-tenant renderer | 효율이 좋다 | isolation이 어렵다 | 대부분의 SaaS |
| Preview sandbox | 안전하다 | 복잡하다 | 운영 템플릿 |
| Versioned templates | 롤백이 쉽다 | 관리가 늘어난다 | 브랜드 자산 |
| Cached render fragments | 빠르다 | invalidation 필요 | 고QPS rendering |

핵심은 멀티 테넌트 렌더링이 단순 템플릿 엔진이 아니라 **브랜드 격리, 승인, 안전한 출력 생성**을 함께 제공하는 서비스라는 점이다.

## 꼬리질문

> Q: 왜 tenant namespace가 필요한가요?
> 의도: 격리와 cache safety 이해 확인
> 핵심: 템플릿과 asset이 섞이면 사고가 난다.

> Q: preview와 publish를 왜 분리하나요?
> 의도: 승인과 안전 배포 이해 확인
> 핵심: 미리보기는 안전하게 검토하고, 발송은 승인 후 해야 한다.

> Q: 템플릿에서 code execution을 막으려면?
> 의도: sandbox와 escaping 이해 확인
> 핵심: helper whitelist와 escaping, sandbox가 필요하다.

> Q: versioned templates가 왜 중요한가요?
> 의도: 재현성과 롤백 이해 확인
> 핵심: 같은 출력물을 다시 만들 수 있어야 한다.

## 한 줄 정리

Multi-tenant template rendering service는 고객별 브랜드와 locale, 승인, 캐시를 분리하면서 안전하게 문자를 렌더링하는 서비스다.

