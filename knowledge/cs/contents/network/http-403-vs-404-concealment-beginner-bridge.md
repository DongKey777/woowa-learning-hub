---
schema_version: 3
title: "403 vs 404 Concealment Beginner Bridge"
concept_id: network/http-403-vs-404-concealment-beginner-bridge
canonical: true
category: network
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- status-code-semantics
- authz-concealment
- beginner-http
aliases:
- 403 vs 404 concealment
- intentional 404
- hidden 404 basics
- forbidden vs not found auth
- resource concealment intro
- 남의 주문인데 왜 404
symptoms:
- 권한 실패는 무조건 403이고 404는 URL 오타라고만 해석한다
- user-owned resource나 tenant 자원에서 존재 노출 위험을 놓친다
- concealment 404와 진짜 missing 404를 같은 내부 의미로 뭉갠다
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- network/http-status-codes-basics
- network/http-request-response-basics-url-dns-tcp-tls-keepalive
next_docs:
- security/auth-failure-response-401-403-404
- security/concealment-404-entry-cues
- network/http-request-response-headers-basics
linked_paths:
- contents/network/http-status-codes-basics.md
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
- contents/network/http-request-response-headers-basics.md
- contents/security/auth-failure-response-401-403-404.md
- contents/security/concealment-404-entry-cues.md
confusable_with:
- network/http-status-codes-basics
- security/auth-failure-response-401-403-404
- security/concealment-404-entry-cues
forbidden_neighbors: []
expected_queries:
- "권한이 없는데 왜 403 대신 404를 줄 수 있어?"
- "남의 주문 상세를 요청했을 때 404 concealment를 쓰는 이유는?"
- "403과 의도적 404는 HTTP 계약상 어떻게 달라?"
- "404가 URL 오타인지 존재 숨김인지 초보자는 어떻게 구분해?"
- "tenant 자원에서 resource concealment를 어떻게 설명해야 해?"
contextual_chunk_prefix: |
  이 문서는 HTTP 403 Forbidden, 404 Not Found, intentional concealment 404,
  user-owned/tenant resource의 존재 노출 정책을 beginner 관점에서 연결하는
  bridge 문서다.
---
# `403` vs `404` Concealment: 존재를 숨길 때 초보자가 읽는 법

> 한 줄 요약: `403`은 "리소스는 맞지만 너에게 허용되지 않음"을 드러내는 응답이고, 의도적 `404`는 같은 인가 실패라도 리소스 존재를 숨기기 위해 바깥 계약을 더 보수적으로 고른 경우다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md)
- [Concealment `404` Entry Cues](../security/concealment-404-entry-cues.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: 403 vs 404 concealment, intentional 404 beginner, hidden 404 basics, 404 대신 403 아닌가요, 남의 주문인데 왜 404, 없는 것도 아닌데 404, forbidden vs not found auth, resource concealment intro, authz concealment beginner, status code semantics beginner

## 핵심 개념

초보자가 가장 많이 헷갈리는 문장은 이것이다.

- `403`이면 권한 문제
- `404`면 없는 것

입문 단계에서는 이 규칙이 대체로 맞다. 다만 보안이 섞이면 한 가지 예외가 생긴다.  
앱이 "있지만 있다고 말해 주면 안 되는 리소스"라고 판단하면, 내부적으로는 인가 실패여도 바깥에는 `404`를 줄 수 있다.

여기서 중요한 점은 **의미를 섞지 않는 것**이다.

- `403`의 기본 의미는 여전히 "허용되지 않음"이다.
- `404`의 기본 의미는 여전히 "찾지 못함"이다.
- concealment `404`는 "`404`가 진짜 없음이라는 뜻을 잃었다"가 아니라, **존재 여부를 노출하지 않기 위해 바깥 응답을 `404`로 고른 경우도 있다**는 뜻이다.

즉 초보자에게는 "`404`를 보면 URL 오타와 삭제를 먼저 떠올리되, user-owned resource나 tenant 경계 자원이면 숨김 `404`도 열어 둔다"라고 설명하는 편이 안전하다.

## 한눈에 보기

| 장면 | 바깥 응답 기본값 | 초보자용 해석 |
|---|---|---|
| 로그인도 안 했고 인증이 안 됨 | `401` 또는 브라우저에선 `302 /login` | 아직 `누구인지`를 못 믿는다 |
| 로그인은 됐고, 리소스 존재를 알려도 되는 화면인데 권한이 부족함 | `403` | "있긴 있는데 너는 안 됨"을 드러낸다 |
| 로그인은 됐지만, 남의 주문/다른 tenant 자원처럼 존재 자체가 민감함 | `404` 가능 | "없다"와 "있지만 말하지 않음"을 외부에서 구분하기 어렵게 만든다 |
| 실제로 리소스가 없음 | `404` | 진짜 없음이다 |

짧은 mental model:

- `403`은 **거절 사실을 드러내는 응답**
- concealment `404`는 **거절 이유를 숨기는 응답**

둘 다 내부에서는 인가 판단이 있었을 수 있지만, 바깥 계약은 다르다.

## 상세 분해

### 1. 언제 `403`이 더 자연스러운가

`403`은 "이 대상이 있다는 사실은 알려 줘도 괜찮고, 지금은 권한 부족을 분명히 말하는 편이 더 낫다"는 장면에 잘 맞는다.

예시:

- 관리자 메뉴는 존재를 다들 아는데 내 계정에 관리자 권한이 없다
- 팀 문서는 존재를 알고 있지만 수정 권한이 없다
- API scope가 부족해서 같은 리소스에 `read`는 되지만 `delete`는 안 된다

이때는 초보자에게 "`403`은 다시 로그인보다 역할, 권한, scope를 보라는 신호"라고 설명하면 된다.

### 2. 언제 의도적 `404`가 더 자연스러운가

`404` concealment는 "그 리소스가 존재한다는 사실 자체가 정보"인 장면에서 많이 쓴다.

예시:

- 다른 사람 주문 상세
- 다른 tenant의 invoice 상세
- private 파일, 개인 메시지, 계정 복구 토큰처럼 존재 노출이 민감한 객체

이때 외부 사용자는 아래 둘을 구분하기 어렵다.

- 진짜로 없는 ID
- 있지만 네 문맥에서는 보여 주지 않기로 한 ID

바로 그 구분을 어렵게 만드는 것이 concealment의 목적이다.

### 3. 초보자에게 어떻게 설명하면 덜 섞이나

아래 문장을 그대로 쓰면 흔한 오해를 줄이기 쉽다.

- `403`은 "있다는 사실을 보여 준 채 거절하는 응답"이다.
- 의도적 `404`는 "거절 자체보다 존재 여부를 숨기는 응답"이다.
- 그래서 concealment `404`를 쓴다고 해서 `403`의 의미가 사라지는 것은 아니다. 앱이 바깥 계약을 더 보수적으로 고른 것이다.

피해야 할 설명도 있다.

- `404도 그냥 권한 없음이다`  
  이 말은 진짜 missing과 숨김 `404`를 뭉개 버린다.
- `403 대신 404를 쓰면 의미가 완전히 같다`  
  외부 클라이언트가 받는 계약은 분명히 다르다.

### 4. 어떤 자원에서 무엇을 먼저 떠올리나

| 자원 종류 | 초보자 첫 가설 |
|---|---|
| 관리자 페이지, 협업 보드, 공유 메뉴 | `403` 쪽이 더 자연스럽다 |
| 내 주문, 내 파일, 다른 tenant 자원 | concealment `404` 가능성을 같이 연다 |
| 아무 계정에서도 안 열리고 목록에서도 안 보임 | 진짜 `404` 가능성이 더 크다 |

## 흔한 오해와 함정

- `404`가 뜨면 무조건 URL 오타라고 단정한다.  
  user-owned resource나 tenant 경계 자원이면 숨김 `404`도 같이 봐야 한다.
- `403`과 concealment `404`를 같은 말이라고 설명한다.  
  내부 인가 맥락은 비슷할 수 있어도 외부 HTTP 계약은 다르다.
- 모든 인가 실패를 `404`로 돌리고 싶어 한다.  
  공유 자원이나 관리자 UI까지 전부 숨기면 클라이언트 계약이 흐려지고 디버깅도 어려워진다.
- 반대로 모든 ownership 실패를 `403`으로만 고정한다.  
  다른 사람 리소스 존재를 불필요하게 알려 주는 설계가 될 수 있다.

초보자용 안전 규칙은 이것이다.

- `404` concealment는 **리소스 클래스 단위 정책**으로 정한다.
- 예를 들어 "개인 주문 상세는 `404`, 관리자 메뉴 권한 부족은 `403`"처럼 문서화하는 편이 낫다.

## 실무에서 쓰는 모습

브라우저나 API 클라이언트 입장에서 보면 같은 `404`라도 두 장면이 섞여 있을 수 있다.

| 요청 | 내부 상황 | 바깥 응답 |
|---|---|---|
| `GET /orders/123` | 주문이 아예 없음 | `404` |
| `GET /orders/123` | 주문은 있지만 다른 사용자 소유, concealment 정책 적용 | `404` |
| `GET /admin/users` | 로그인은 됐지만 `ADMIN` 역할 없음 | `403` |

그래서 초보자 설명은 이렇게 가져가면 된다.

1. 먼저 `401`인지 `403`인지 `404`인지 숫자부터 본다.
2. `404`면 URL/ID 실수부터 확인한다.
3. 그런데 그 자원이 개인 주문, 개인 파일, tenant 자원이라면 "숨김 `404`일 수도 있다"를 같이 연다.
4. 관리자 화면이나 공유 자원에서 권한 부족이면 보통 `403` 쪽이 더 자연스럽다.

한 줄로 압축하면, **`404` concealment는 `403`을 부정하는 게 아니라 존재 노출 정책을 앞세운 응답 선택**이다.

## 더 깊이 가려면

- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md) — 인증 실패 전체 큰 그림
- [Concealment `404` Entry Cues](../security/concealment-404-entry-cues.md) — `진짜 없음 / 숨김 / stale` 세 갈래로 더 자세히 분리
- [HTTP 상태 코드 기초](./http-status-codes-basics.md) — 상태 코드 전체 mental model 복습

## 면접/시니어 질문 미리보기

**Q. 왜 어떤 앱은 권한 부족인데도 `403` 대신 `404`를 주나요?**  
리소스 존재 여부 자체가 민감한 경우, "있지만 너에게는 보여 주지 않음"을 "없는 것처럼 보이게" 만들어 정보 노출을 줄이기 위해서다.

**Q. 그러면 `404`는 더 이상 not found가 아닌가요?**  
아니다. 여전히 기본 의미는 not found다. 다만 보안 정책상 외부에서 존재 여부를 구분하지 못하게 하려고 같은 `404`를 쓸 수 있다.

**Q. 모든 권한 실패를 `404`로 숨기면 더 안전한가요?**  
항상 그렇지는 않다. 공유 자원이나 관리자 기능까지 전부 `404`로 숨기면 클라이언트 계약과 운영 디버깅이 흐려질 수 있어서, 어떤 리소스 클래스에 concealment를 적용할지 명확한 기준이 필요하다.

## 한 줄 정리

`403`은 거절 사실을 드러내는 응답이고, 의도적 `404`는 같은 인가 맥락이라도 리소스 존재를 숨기기 위해 바깥 계약을 더 보수적으로 고른 응답이다.
