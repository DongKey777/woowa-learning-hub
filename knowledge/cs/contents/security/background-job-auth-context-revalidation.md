---
schema_version: 3
title: Background Job Auth Context / Revalidation
concept_id: security/background-job-auth-context-revalidation
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- background job authorization
- async auth context
- permission revalidation
- snapshot authorization
aliases:
- background job authorization
- async auth context
- permission revalidation
- snapshot authorization
- tenant context in jobs
- stale claims
- delayed job security
- queued authorization
- delegated authority
- export job auth
- Background Job Auth Context / Revalidation
- background job auth context revalidation
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/tenant-isolation-authz-testing.md
- contents/security/token-exchange-impersonation-risks.md
- contents/security/session-revocation-at-scale.md
- contents/security/authorization-caching-staleness.md
- contents/spring/spring-securitycontext-propagation-async-reactive-boundaries.md
- contents/spring/spring-async-context-propagation-restclient-http-interface-clients.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Background Job Auth Context / Revalidation 핵심 개념을 설명해줘
- background job authorization가 왜 필요한지 알려줘
- Background Job Auth Context / Revalidation 실무 설계 포인트는 뭐야?
- background job authorization에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Background Job Auth Context / Revalidation를 다루는 deep_dive 문서다. 비동기 job은 요청 시점의 인증 결과를 몇 초 뒤, 몇 분 뒤, 심지어 몇 시간 뒤에 재사용하는 경계이므로, 사용자 권한을 그대로 들고 가기보다 snapshot과 re-check 정책을 명시적으로 선택해야 한다. 검색 질의가 background job authorization, async auth context, permission revalidation, snapshot authorization처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Background Job Auth Context / Revalidation

> 한 줄 요약: 비동기 job은 요청 시점의 인증 결과를 몇 초 뒤, 몇 분 뒤, 심지어 몇 시간 뒤에 재사용하는 경계이므로, 사용자 권한을 그대로 들고 가기보다 snapshot과 re-check 정책을 명시적으로 선택해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
> - [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Spring `SecurityContext` Propagation: Async / Reactive Boundaries](../spring/spring-securitycontext-propagation-async-reactive-boundaries.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](../spring/spring-async-context-propagation-restclient-http-interface-clients.md)

retrieval-anchor-keywords: background job authorization, async auth context, permission revalidation, snapshot authorization, tenant context in jobs, stale claims, delayed job security, queued authorization, delegated authority, export job auth

---

## 핵심 개념

사용자 요청이 비동기 작업을 생성하는 순간, authorization은 시간 경계를 만난다.

- 지금은 관리자지만 10분 뒤에는 아닐 수 있다
- 지금 tenant member지만 재시도 시점에는 탈퇴됐을 수 있다
- 지금 허용된 export 범위가 나중에는 정책 변경으로 금지될 수 있다

그래서 background job 보안의 핵심은 "`SecurityContext`를 전파하느냐"보다  
"어떤 권한 판단을 어떤 시점까지 유효하게 볼 것인가"를 정하는 일이다.

---

## 깊이 들어가기

### 1. queue에 raw access token을 싣는 것은 거의 항상 나쁜 기본값이다

표면적으로는 편해 보인다.

- worker가 받은 token을 그대로 검증하면 된다
- 요청과 같은 principal로 실행되는 것처럼 보인다

하지만 문제는 많다.

- delayed retry 시 token이 만료된다
- 로그, dead letter queue, tracing에 token이 남을 수 있다
- 권한 회수 후에도 오래된 token이 남는다
- worker가 원래 필요하지 않은 사용자 자격을 과도하게 가진다

즉 raw token 전파는 convenience는 주지만, least privilege와 revocation을 무너뜨린다.

### 2. 보통 선택지는 세 가지다

#### A. authorization snapshot

요청 시점의 결정 근거를 snapshot으로 남긴다.

- actor id
- tenant id
- 허용된 resource filter
- policy version
- approval id
- 만료 시각

이 방식은 "그 시점에 승인된 작업"을 재현하기 좋다.  
예를 들어 감사 가능한 export, 결재 기반 배치에 맞는다.

#### B. execution-time re-check

job 실행 시 현재 권한을 다시 확인한다.

- actor가 아직 tenant member인가
- role이 유지되는가
- resource scope가 여전히 허용되는가

이 방식은 revoke 반영에 강하지만, 요청 당시 성공한 작업이 나중에 실패할 수 있다.

#### C. service-owned job

사용자 대신 서비스가 최소 권한의 service identity로 job를 수행한다.

이때 사용자 정보는 audit와 scope 입력으로만 쓰고, 실제 권한은 별도 정책으로 제한한다.

예:

- "사용자가 export를 요청했다"는 사실만 기록
- 실제 export worker는 `reports.export` service role로 동작
- tenant, report template, row limit는 명시적 입력으로 제한

### 3. 어떤 모델인지 문서화하지 않으면 stale authorization가 우연히 결정된다

흔한 나쁜 패턴:

- 처음엔 `@Async`로 바로 실행해서 문제없었다
- 나중에 queue + retry가 붙었다
- 예전과 똑같이 principal object를 직렬화해서 쓰기 시작했다

이렇게 되면 사실상 "snapshot인지 re-check인지"를 아무도 결정하지 않았는데 코드가 답을 정해 버린다.

### 4. job payload에는 권한 입력만 싣고, 권한 판단은 재구성하는 편이 안전하다

보통 payload에 필요한 것은 이 정도다.

- requested by user id
- tenant id
- explicit resource scope
- requested at
- approval id or policy version
- correlation id

반대로 조심할 것:

- raw bearer token
- 거대한 role list
- UI 전용 filter state 전체
- gateway trusted header dump

job는 request replay가 아니라 controlled execution input이어야 한다.

### 5. revoke 민감한 작업은 pre-flight revalidation이 필요하다

특히 아래 작업은 실행 직전에 재검증하는 편이 낫다.

- 대량 export
- tenant-wide data delete
- admin bulk mutation
- payment/refund batch

이유:

- 권한 회수 직후에도 job가 계속 돌면 피해가 크다
- queue delay와 retry가 길수록 stale authorization 위험이 커진다

### 6. long-running job는 중간 재확인 지점도 필요할 수 있다

몇 시간 걸리는 작업은 시작 시점에만 확인해서는 부족할 수 있다.

예:

- 5만 건 export
- tenant 전체 재색인
- 장시간 걸리는 migration assistant

이 경우:

- chunk boundary마다 tenant validity 확인
- 취소 플래그 확인
- user disable / account lockout 이벤트 반영

같은 checkpoint가 필요하다.

### 7. 감사 로그는 "누가 요청했고, 누구 권한으로 실행됐는가"를 둘 다 남겨야 한다

비동기 경계에서는 actor와 executor가 달라질 수 있다.

- requested_by: 원래 요청한 사용자
- approved_by: 별도 승인자
- executed_as: service identity 또는 delegated actor
- policy_version: 어떤 기준으로 허용됐는가

이 네 가지가 없으면 사고 후 포렌식이 어렵다.

### 8. tenant isolation은 async path에서 자주 깨진다

동기 API는 tenant filter가 잘 붙어도, background worker는 별도 repository path를 타면서 누락되기 쉽다.

특히 위험한 경우:

- tenant id를 payload에 안 넣고 user id만 넣음
- worker가 "관리자 내부 작업"이라며 tenant predicate를 생략
- export temp file path에 tenant partition이 없음

즉 async path는 기능 로직이 아니라 별도 보안 경계로 테스트해야 한다.

---

## 실전 시나리오

### 시나리오 1: 직원이 퇴사했는데 예약된 export job가 밤새 계속 돈다

문제:

- 요청 당시 권한만 믿고 실행 시점 재검증이 없다

대응:

- revoke 민감 작업은 execution-time re-check를 붙인다
- user disable 이벤트와 job cancellation을 연결한다
- long-running job는 chunk 단위 checkpoint를 둔다

### 시나리오 2: support admin이 tenant A에서 예약한 job가 tenant B 데이터까지 읽는다

문제:

- payload에 tenant scope가 없거나 worker query에 tenant predicate가 빠졌다

대응:

- payload에 tenant id와 explicit scope를 필수화한다
- worker path를 tenant isolation 테스트에 포함한다
- 내부 관리자 job라도 tenant boundary를 생략하지 않는다

### 시나리오 3: retry된 job가 예전 permission snapshot으로 side effect를 다시 만든다

문제:

- snapshot 만료나 policy version drift를 고려하지 않았다

대응:

- snapshot에는 expiration과 approval id를 둔다
- retry 전에 snapshot validity를 다시 본다
- 재검증이 필요한 job class와 아닌 job class를 나눈다

---

## 코드로 보기

### 1. raw token 대신 명시적 job grant를 담는 예시

```java
public record ExportJobRequest(
        String requestedByUserId,
        String tenantId,
        String reportId,
        String policyVersion,
        Instant requestedAt,
        Instant grantExpiresAt
) {
}
```

### 2. 실행 직전 권한 재검증 개념

```java
public void execute(ExportJobRequest job) {
    if (Instant.now().isAfter(job.grantExpiresAt())) {
        throw new SecurityException("authorization snapshot expired");
    }

    authorizationService.verifyExportPermission(
            job.requestedByUserId(),
            job.tenantId(),
            job.reportId(),
            job.policyVersion()
    );

    exportService.run(job);
}
```

### 3. 운영 체크리스트

```text
1. job가 snapshot authorization인지 execution-time re-check인지 명시되어 있는가
2. payload에 raw access token 대신 actor/tenant/scope/policy version이 담기는가
3. revoke 민감 작업은 시작 전 또는 chunk 단위 재확인을 하는가
4. audit log에 requested_by, executed_as, policy_version이 모두 남는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| raw user token on queue | 구현이 쉽다 | 만료, 유출, stale permission 위험이 크다 | 가능하면 피한다 |
| authorization snapshot | 요청 당시 승인 의미를 보존하기 좋다 | revoke 반영이 느릴 수 있다 | 결재 기반 export, 승인형 배치 |
| execution-time re-check | 최신 권한을 반영한다 | 요청 당시 성공한 작업이 나중에 실패할 수 있다 | admin, 민감 작업, 장시간 지연 job |
| service-owned job identity | least privilege 설계가 쉽다 | 사용자 대리 실행 semantics를 따로 설계해야 한다 | internal worker, scheduled batch, platform jobs |

판단 기준은 이렇다.

- 권한 회수가 즉시 반영돼야 하는가
- job delay와 retry window가 얼마나 긴가
- 작업 결과가 감사 가능해야 하는가
- worker가 꼭 사용자 자격으로 실행돼야 하는가

---

## 꼬리질문

> Q: queue에 access token을 그대로 넣으면 왜 위험한가요?
> 의도: 시간 경계와 credential 노출 문제를 아는지 확인
> 핵심: 만료, 유출, stale authorization, 과도한 권한 전달이 동시에 생길 수 있다.

> Q: snapshot authorization과 re-check 중 무엇이 더 안전한가요?
> 의도: 절대 정답보다 작업 성격별 선택을 이해하는지 확인
> 핵심: revoke 민감도와 감사 의미에 따라 다르다. 민감 작업은 re-check가 더 안전한 경우가 많다.

> Q: service-owned job는 왜 유용한가요?
> 의도: user identity와 executor identity를 분리하는지 확인
> 핵심: worker에 최소 권한을 부여하고, 사용자 요청 사실은 audit와 scope 입력으로만 남길 수 있다.

> Q: async path를 별도 보안 경계로 테스트해야 하는 이유는 무엇인가요?
> 의도: worker가 동기 API와 다른 코드 경로를 타는 점을 이해하는지 확인
> 핵심: tenant predicate, policy re-check, file partition 같은 보호 장치가 async 경로에서 빠지기 쉽기 때문이다.

## 한 줄 정리

Background job 보안의 핵심은 사용자 컨텍스트를 그대로 운반하는 것이 아니라, 어떤 권한 판단을 snapshot으로 고정하고 어떤 작업은 실행 시 다시 확인할지 명시적으로 선택하는 것이다.
