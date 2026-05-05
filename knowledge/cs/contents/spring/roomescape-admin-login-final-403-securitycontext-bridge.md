---
schema_version: 3
title: roomescape 관리자 로그인 후 예약 페이지 403 ↔ SecurityContext 복원과 SavedRequest 브릿지
concept_id: spring/roomescape-admin-login-final-403-securitycontext-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- admin-auth-flow
- securitycontext-restoration
- savedrequest-final-403
aliases:
- roomescape 관리자 로그인 403
- roomescape 예약 페이지 권한 없음
- roomescape SavedRequest 복귀
- roomescape SecurityContext 복원
- roomescape admin session cookie
symptoms:
- 로그인 성공 후 roomescape 관리자 예약 페이지로 돌아왔는데 마지막에 403이 떠요
- roomescape admin 로그인은 됐는데 다음 요청에서 다시 anonymous처럼 보여요
- 리뷰어가 filter chain에서 먼저 끊긴다고 했는데 controller 코드를 봐도 이유를 모르겠어요
intents:
- mission_bridge
- troubleshooting
- comparison
prerequisites:
- spring/admin-302-login-vs-403-beginner-bridge
- spring/spring-admin-session-cookie-flow-primer
next_docs:
- spring/spring-admin-session-cookie-flow-primer
- spring/admin-login-success-final-403-savedrequest-role-mapping-primer
- spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge
linked_paths:
- contents/spring/spring-admin-302-login-vs-403-beginner-bridge.md
- contents/spring/spring-admin-session-cookie-flow-primer.md
- contents/spring/spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md
- contents/spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md
- contents/spring/spring-security-filter-chain.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
confusable_with:
- spring/admin-302-login-vs-403-beginner-bridge
- spring/spring-admin-session-cookie-flow-primer
- spring/admin-login-success-final-403-savedrequest-role-mapping-primer
forbidden_neighbors:
- contents/spring/spring-security-requestcache-savedrequest-boundaries.md
- contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
expected_queries:
- roomescape 관리자 로그인 뒤 원래 예약 페이지로 돌아왔는데 왜 마지막에 403이 나?
- 룸이스케이프 admin 페이지는 로그인 성공인데 다음 요청에서 왜 다시 비로그인처럼 보여?
- roomescape 미션에서 SavedRequest랑 SecurityContext를 같이 봐야 하는 장면이 언제야?
- 리뷰어가 roomescape admin 인증 문제는 controller 말고 filter chain부터 보라고 한 이유가 뭐야?
- 관리자 예약 페이지 접근이 /login 복귀 뒤 막히면 role mapping이랑 session 중 뭘 먼저 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 관리자 로그인 뒤 예약 페이지 접근이
  `/login` 복귀 후에도 403으로 끝나거나 다음 요청에서 다시 anonymous처럼 보이는
  장면을 SecurityContext 복원, 세션 쿠키, SavedRequest, filter chain 분기와
  연결하는 mission_bridge다. roomescape 관리자 로그인 403, admin session cookie,
  복귀는 됐는데 권한 없음 같은 자연어 질문이 이 문서의 검색 표면이다.
---

# roomescape 관리자 로그인 후 예약 페이지 403 ↔ SecurityContext 복원과 SavedRequest 브릿지

## 한 줄 요약

roomescape 관리자 인증 문제는 컨트롤러 메소드 한 줄보다 먼저 `filter chain`에서 갈린다. 로그인 뒤 원래 `/admin/reservations`로 돌아오는 것은 `SavedRequest` 문제이고, 그 뒤에도 `403`이 남거나 다시 anonymous처럼 보이는 것은 `SecurityContext` 복원과 권한 매핑 문제로 읽는 편이 빠르다.

## 미션 시나리오

roomescape 미션에서 관리자 예약 목록이나 예약 추가 화면을 만들면 보통 `/admin/reservations` 같은 보호 URL을 먼저 열게 된다. 학습자는 로그인 폼까지는 잘 갔다가, 로그인 성공 후 원래 화면으로 돌아오면 끝난 줄 알기 쉽다.

하지만 실제로는 두 갈래가 남는다. 하나는 브라우저가 세션 쿠키를 다시 보내고 서버가 `SecurityContext`를 복원하는 갈래이고, 다른 하나는 복원된 사용자가 정말 `ADMIN` 권한인지 확인하는 갈래다. 그래서 PR에서 "controller보다 filter chain 로그를 먼저 보세요", "`SavedRequest` 복귀와 final `403`을 분리하세요" 같은 코멘트가 붙는다.

## CS concept 매핑

roomescape 관리자 예약 페이지 접근은 CS 관점에서 "로그인 성공" 한 사건이 아니라, 요청마다 인증 상태를 복원하고 다시 검사하는 파이프라인이다.

| roomescape 장면 | 더 가까운 Spring Security 개념 | 왜 그 개념으로 읽나 |
| --- | --- | --- |
| 비로그인으로 `/admin/reservations`를 눌렀다가 로그인 화면으로 이동 | `AuthenticationEntryPoint`, `SavedRequest` | 보호 URL 접근 실패를 로그인 유도와 원래 URL 메모로 나눠 처리한다 |
| 로그인 뒤 원래 예약 페이지로 다시 돌아옴 | `RequestCache`, `SavedRequest` 재생 | 복귀 성공은 주소 메모가 동작했다는 뜻이지 권한 통과까지 보장하진 않는다 |
| 다음 요청에서 다시 anonymous처럼 보임 | 세션 쿠키, `SecurityContext` 복원 | 브라우저 쿠키와 서버 세션 연결이 끊기면 매 요청이 새 비로그인처럼 보인다 |
| 복귀 직후 final `403`이 남음 | `hasRole`, authority 매핑 | 로그인은 됐지만 `ROLE_ADMIN` 같은 권한 이름이 안 맞을 수 있다 |

짧게 외우면 "`복귀는 SavedRequest`, `다음 요청 로그인 유지`는 SecurityContext 복원, `마지막 403`은 권한 매핑"이다. roomescape에서 이 셋을 한 덩어리로 보면 디버깅 순서가 자주 꼬인다.

## 미션 PR 코멘트 패턴

- "컨트롤러 전에 Security filter chain에서 이미 막힙니다."라는 코멘트는 비즈니스 로직보다 인증 파이프라인 로그를 먼저 보라는 뜻이다.
- "로그인 복귀와 최종 403은 다른 단계예요."라는 코멘트는 `SavedRequest`가 성공해도 `ROLE_ADMIN` 검사는 별개라는 뜻이다.
- "쿠키가 있어도 다음 요청에서 anonymous면 세션 복원을 먼저 확인하세요."라는 코멘트는 브라우저 저장과 서버 세션 연결을 같이 보라는 뜻이다.
- "roomescape admin 권한 문자열을 security 설정과 사용자 authority에서 같이 확인해 보세요."라는 코멘트는 final `403`을 권한 이름 불일치로 의심하라는 뜻이다.

## 다음 학습

- `/admin`이 왜 `302 /login`인지와 final `403`을 먼저 갈라 보고 싶다면 `Spring 관리자 요청이 302 /login이 될 때와 403이 될 때: 초급 브리지`를 본다.
- 로그인 유지가 다음 요청에서 왜 끊기는지 더 자세히 보려면 `Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer`를 읽는다.
- 원래 URL로 복귀한 뒤 마지막 `403`이 남는 장면만 깊게 보고 싶다면 `Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 403이 나는 이유: SavedRequest와 역할 매핑 초급 primer`로 이어간다.
- filter와 Spring Security filter chain, interceptor의 경계를 roomescape 인증 예시로 다시 묶고 싶다면 `Spring Filter vs Spring Security Filter Chain vs HandlerInterceptor: 관리자 인증 입문 브리지`를 본다.
