# Auth Ladder Alias Drift Lint

> 한 줄 요약: `login loop`와 `hidden session` 계열 beginner ladder에서 primer와 follow-up 문서의 retrieval alias가 어긋났는지 빠르게 잡는 repo-local QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [Cross-Domain Bridge Map](./cross-domain-bridge-map.md#spring--security)
> - [Query Playbook](./query-playbook.md)
> - [CS Root README: Auth / Session Beginner Shortcut](../README.md#auth--session-beginner-shortcut)
> - [Security README: Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path)
>
> retrieval-anchor-keywords: auth ladder alias drift lint, login loop alias lint, hidden session alias lint, beginner auth ladder qa, primer follow-up alias parity, login-loop canonical beginner entry route lint, savedrequest alias drift check, cookie exists but session missing alias parity, cookie 있는데 다시 로그인 alias parity, browser 401 302 bounce alias parity, primer bridge alias consistency, auth session beginner route lint

## 먼저 잡는 mental model

이 check는 문장 품질보다 먼저 **검색어 손잡이 parity**를 본다.

- primer는 "처음 진입"을 담당한다.
- follow-up은 "같은 표현으로 다음 문서"를 담당한다.
- 둘의 retrieval alias가 어긋나면, beginner 질문이 primer에서 follow-up으로 안전하게 안 넘어간다.

## 언제 돌리나

- 아래 ladder 문서 중 하나라도 `retrieval-anchor-keywords`나 beginner row 문구를 손본 뒤
- `login loop`, `SavedRequest`, `hidden session` 관련 route를 README/table에서 재배치한 뒤
- beginner shortcut이 deep-dive로 바로 뛰는지, primer -> follow-up 사다리가 유지되는지 확인하고 싶을 때

대상 ladder(기본값):

1. [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
2. [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md)
3. [Spring Security `RequestCache` / `SavedRequest` Boundaries](../contents/spring/spring-security-requestcache-savedrequest-boundaries.md)
4. [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)

## Core alias 세트

| alias bundle | 최소 공통 alias (권장) | 의미 |
|---|---|---|
| `login-loop` | `login loop`, `browser 401 302 /login bounce`, `SavedRequest`, `saved request bounce` | redirect/navigation memory 축 |
| `hidden-session` | `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login` | post-login persistence 축 |

beginner lane에서는 primer와 follow-up이 위 두 묶음을 **같이 공유**해야 안전하다.

## 실행

먼저 대상 문서의 retrieval line을 한 번에 본다.

```bash
rg -n "^retrieval-anchor-keywords:" \
  knowledge/cs/contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md \
  knowledge/cs/contents/security/browser-401-vs-302-login-redirect-guide.md \
  knowledge/cs/contents/spring/spring-security-requestcache-savedrequest-boundaries.md \
  knowledge/cs/contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
```

그다음 core alias 누락을 빠르게 확인한다.

```bash
rg -n "login loop|browser 401 302 /login bounce|SavedRequest|saved request bounce|hidden session|hidden JSESSIONID|cookie exists but session missing|cookie 있는데 다시 로그인|next request anonymous after login" \
  knowledge/cs/contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md \
  knowledge/cs/contents/security/browser-401-vs-302-login-redirect-guide.md
```

README/bridge entrypoint가 primer -> follow-up 순서를 유지하는지도 본다.

```bash
rg -n 'canonical beginner entry route: login-loop|Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문|Browser `401` vs `302` Login Redirect Guide' \
  knowledge/cs/README.md \
  knowledge/cs/rag/cross-domain-bridge-map.md \
  knowledge/cs/contents/security/README.md
```

## 통과 기준

1. primer + follow-up 두 문서의 `retrieval-anchor-keywords`에 `login-loop`/`hidden-session` core alias가 모두 남아 있다.
2. primer의 다음 단계가 follow-up으로 고정되어 있고, follow-up에서 deep-dive로 내려가기 전 `Browser / Session Troubleshooting Path` 복귀 문장이 남아 있다.
3. root/bridge README row가 beginner route를 `primer -> primer bridge -> deep dive` 순서로 안내한다.

## 실패 패턴과 수리 순서

| 실패 패턴 | 왜 위험한가 | 수리 순서 |
|---|---|---|
| primer에는 `hidden session` alias가 있는데 follow-up retrieval line에서 빠짐 | 같은 증상 검색이 primer까지만 걸리고 follow-up 회수가 약해진다 | follow-up `retrieval-anchor-keywords`에 동일 alias를 복구 |
| follow-up에서 `SavedRequest` alias가 사라지고 deep-dive 링크만 남음 | beginner가 redirect memory와 session persistence를 구분하기 전에 내려가 버린다 | follow-up beginner row에 `SavedRequest`/`saved request bounce`를 다시 넣고 primer 링크 복구 |
| README row가 primer를 건너뛰고 spring deep-dive를 첫 링크로 둠 | beginner safe next-step이 깨져 route 이탈이 늘어난다 | row를 `Login Redirect primer -> Browser 401 vs 302`로 되돌린 뒤 deep-dive는 3단계로 배치 |

## 흔한 혼동

- `SavedRequest`는 로그인 상태 저장이 아니라 로그인 전 URL 기억이다.
- `cookie stored`와 `cookie sent`는 다르다. `Application` 탭만 보고 session persistence를 단정하지 않는다.
- `hidden session` 계열 표현은 보통 server lookup 문제를 뭉뚱그린 말이므로, 먼저 alias를 같은 사다리로 정렬해야 한다.

## 한 줄 정리

auth beginner ladder를 손봤다면 primer/follow-up 문서가 `login-loop`와 `hidden-session` core alias를 함께 유지하는지 먼저 lint로 고정한다.
